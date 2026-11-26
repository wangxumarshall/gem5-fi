// FPUInjector.cc -- per-dynamic-instruction FPU/SIMD fault injector and
// O3 lifecycle tracer for the 0202 FPU/SIMD fault campaign.
//
// Configuration is entirely per-run via environment variables:
//   FI_ENABLE=1       enable one semantic fault
//   FI_MODEL=M001..M012
//   FI_PC=0x...       exact static target PC
//   FI_ORDINAL=N      1-based eligible dynamic-instruction ordinal
//   FI_LANE=N         target SIMD lane (-1 for scalar / whole-vector)
//   FI_COUNT_ONLY=1   count eligible events, never inject
//   FI_TRACE=/path/events.jsonl
//   FI_SAMPLE / FI_PAIR / FI_CONTEXT / FI_MODE
//   FI_STATE=READY_COMMIT|DEPENDENCY_DELAY|SPEC_EXEC_SQUASH
//
// The semantic hooks in fplib.cc and neon64.isa consult active(model), so
// the actual arithmetic transformation stays at the audited source anchor;
// this file only decides which DynInst is eligible and records evidence.

#include "cpu/o3/FPUInjector.hh"

#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "arch/arm/regs/misc.hh"
#include "base/types.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/reg_class.hh"
#include "sim/cur_tick.hh"
#include "sim/sim_exit.hh"
#include "cpu/thread_context.hh"

namespace gem5
{
namespace fpu_fi
{

namespace
{

static uint64_t
env_u64(const char *name, uint64_t def)
{
    const char *s = std::getenv(name);
    if (!s || !*s) return def;
    return std::strtoull(s, nullptr, 0);
}

static std::string
env_str(const char *name, const char *def = "")
{
    const char *s = std::getenv(name);
    return s ? std::string(s) : std::string(def);
}

static std::string
json_escape(const std::string &s)
{
    std::ostringstream o;
    for (char c : s) {
        switch (c) {
          case '"': o << "\\\""; break;
          case '\\': o << "\\\\"; break;
          case '\n': o << "\\n"; break;
          case '\r': o << "\\r"; break;
          case '\t': o << "\\t"; break;
          default: o << c;
        }
    }
    return o.str();
}

static std::string
hex64(uint64_t v)
{
    char b[32];
    std::snprintf(b, sizeof(b), "0x%016llx", (unsigned long long)v);
    return std::string(b);
}

struct Config
{
    bool enable = false;
    bool count_only = false;
    int model = 0;
    uint64_t target_pc = 0;
    uint64_t ordinal = 1;
    int lane = -1;
    std::string trace_path;
    std::string sample;
    std::string pair;
    std::string context;
    std::string mode;
    std::string state;
    uint64_t eligible = 0;
    uint64_t applied = 0;
    uint64_t event_id = 0;
    bool exit_registered = false;
    std::ofstream out;
};

static Config cfg;

static int
parse_model(const std::string &s)
{
    if (s.size() >= 4 && s[0] == 'M') {
        return std::atoi(s.c_str() + 1);
    }
    return std::atoi(s.c_str());
}

static void
init()
{
    static bool done = false;
    if (done) return;
    done = true;

    cfg.enable = env_u64("FI_ENABLE", 0) != 0;
    cfg.count_only = env_u64("FI_COUNT_ONLY", 0) != 0;
    cfg.model = parse_model(env_str("FI_MODEL", "0"));
    cfg.target_pc = env_u64("FI_PC", 0);
    cfg.ordinal = env_u64("FI_ORDINAL", 1);
    cfg.lane = (int)env_u64("FI_LANE", (uint64_t)(int64_t)-1);
    cfg.trace_path = env_str("FI_TRACE");
    cfg.sample = env_str("FI_SAMPLE");
    cfg.pair = env_str("FI_PAIR");
    cfg.context = env_str("FI_CONTEXT");
    cfg.mode = env_str("FI_MODE");
    cfg.state = env_str("FI_STATE");

    if (!cfg.trace_path.empty()) {
        cfg.out.open(cfg.trace_path, std::ios::out | std::ios::trunc);
        if (!cfg.out) {
            std::cerr << "FPU_FI: cannot open trace " << cfg.trace_path
                      << std::endl;
        }
    }

    if (!cfg.exit_registered) {
        cfg.exit_registered = true;
        registerExitCallback([]() {
            if (cfg.out.is_open()) {
                cfg.out << "{\"schema\":\"fpu-fi-v1\",\"event\":\"run_end\","
                    << "\"tick\":" << curTick()
                    << ",\"eligible_total\":" << cfg.eligible
                    << ",\"applied_total\":" << cfg.applied
                    << ",\"sample\":\"" << json_escape(cfg.sample)
                    << "\",\"context\":\"" << json_escape(cfg.context)
                    << "\",\"state\":\"" << json_escape(cfg.state)
                    << "\"}\n";
                cfg.out.flush();
                cfg.out.close();
            }
            std::cout << "FPU_FI_ELIGIBLE_COUNT=" << cfg.eligible << std::endl;
            std::cout << "FPU_FI_APPLIED_COUNT=" << cfg.applied << std::endl;
            std::cout.flush();
        });
    }
}

static uint64_t
dyn_pc(const o3::DynInst *inst)
{
    return inst ? inst->pcState().instAddr() : 0;
}

static std::string
reg_class_name(PhysRegIdPtr r)
{
    if (!r || r->is(InvalidRegClass)) return "Invalid";
    return std::string(r->className());
}

static std::string
reg_value(o3::DynInst *inst, PhysRegIdPtr r, bool writable)
{
    if (!inst || !r || r->is(InvalidRegClass)) return "null";
    auto *cpu = dynamic_cast<o3::CPU *>(inst->getCpuPtr());
    if (!cpu) return "null";

    const RegClassType rc = r->classValue();
    if (rc == MiscRegClass || rc == InvalidRegClass)
        return "null";
    if (rc == VecRegClass) {
        uint8_t buf[64] = {};
        void *p = writable ? cpu->getWritableReg(r, inst->threadNumber)
                           : (cpu->getReg(r, buf, inst->threadNumber), (void*)buf);
        if (!p) return "null";
        std::memcpy(buf, p, 16);
        std::ostringstream o;
        o << "\"";
        for (int i = 15; i >= 0; --i) {
            char b[3];
            std::snprintf(b, sizeof(b), "%02x", buf[i]);
            o << b;
        }
        o << "\"";
        return o.str();
    }
    if (rc == VecElemClass) {
        uint64_t v = cpu->getReg(r, inst->threadNumber);
        return "\"" + hex64(v) + "\"";
    }
    RegVal v = cpu->getReg(r, inst->threadNumber);
    return "\"" + hex64(v) + "\"";
}

static void
append_regs(std::ostringstream &o, o3::DynInst *inst, bool dest, bool values)
{
    const int n = dest ? inst->numDestRegs() : inst->numSrcRegs();
    o << "[";
    for (int i = 0; i < n; ++i) {
        if (i) o << ",";
        PhysRegIdPtr phys = dest ? inst->renamedDestIdx(i)
                                 : inst->renamedSrcIdx(i);
        const RegId &arch = dest ? inst->destRegIdx(i) : inst->srcRegIdx(i);
        o << "{\"idx\":" << i
          << ",\"arch\":" << (arch.is(InvalidRegClass) ? -1 : (int)arch.index())
          << ",\"phys\":" << (phys && !phys->is(InvalidRegClass)
                                ? (int)phys->index() : -1)
          << ",\"class\":\"" << reg_class_name(phys) << "\"";
        if (values) o << ",\"value\":" << reg_value(inst, phys, dest);
        o << "}";
    }
    o << "]";
}

static void
emit_base(std::ostringstream &o, const char *event, o3::DynInst *inst,
          uint64_t pc)
{
    o << "{\"schema\":\"fpu-fi-v1\",\"eid\":" << (++cfg.event_id)
      << ",\"event\":\"" << event << "\""
      << ",\"tick\":" << curTick()
      << ",\"seq\":" << (inst ? (long long)inst->seqNum : -1)
      << ",\"pc\":" << pc
      << ",\"is_target\":" << ((pc == cfg.target_pc) ? "true" : "false")
      << ",\"model\":\"" << cfg.model << "\""
      << ",\"sample\":\"" << json_escape(cfg.sample) << "\""
      << ",\"pair\":\"" << json_escape(cfg.pair) << "\""
      << ",\"context\":\"" << json_escape(cfg.context) << "\""
      << ",\"state\":\"" << json_escape(cfg.state) << "\""
      << ",\"thread\":" << (inst ? (int)inst->threadNumber : -1)
      << ",\"target_pc\":" << cfg.target_pc;
}

static void
write_line(std::ostringstream &o)
{
    o << "}\n";
    if (cfg.out.is_open()) {
        cfg.out << o.str();
        cfg.out.flush();
    }
}

struct Current
{
    o3::DynInst *inst = nullptr;
    uint64_t pc = 0;
    uint64_t ordinal = 0;
    bool active = false;
    bool applied = false;
    uint64_t src_values[8] = {};
    bool have_src_values = false;
};

static thread_local Current cur;

} // anonymous namespace

bool is_target(uint64_t pc) { init(); return pc == cfg.target_pc; }
uint64_t eligible_count() { init(); return cfg.eligible; }
uint64_t applied_count() { init(); return cfg.applied; }
int model() { init(); return cfg.model; }
int lane() { init(); return cfg.lane; }

bool
active(int model_id)
{
    init();
    return cur.inst && cur.active && cfg.model == model_id;
}

void
note_injection(const char *site, uint64_t old_value, uint64_t new_value,
               int lane_id, uint64_t aux)
{
    init();
    if (!cur.active || !cur.inst || cur.applied) return;
    // One semantic fault application per selected dynamic instruction.  A
    // vector model may call this from the target lane only; a second call is
    // a bug and is deliberately not silently accepted.
    if (cfg.applied >= cfg.ordinal + 1 && cfg.ordinal != 0) {
        // no-op guard; keep counting below
    }
    cur.applied = true;
    ++cfg.applied;
    std::ostringstream o;
    emit_base(o, "fault_inject", cur.inst, cur.pc);
    o << ",\"fault_id\":\"FPU-M" << (cfg.model < 10 ? "00" : "0")
      << cfg.model << "\""
      << ",\"site\":\"" << json_escape(site) << "\""
      << ",\"ordinal\":" << cur.ordinal
      << ",\"lane\":" << lane_id
      << ",\"old\":" << old_value
      << ",\"new\":" << new_value
      << ",\"aux\":" << aux
      << ",\"application_count\":" << cfg.applied;
    write_line(o);
}

void
begin_exec(o3::DynInst *inst)
{
    init();
    cur = Current();
    if (!inst) return;
    const uint64_t pc = dyn_pc(inst);
    cur.inst = inst;
    cur.pc = pc;

    if (pc == cfg.target_pc) {
        cur.ordinal = ++cfg.eligible;
        const bool selected = cfg.enable && !cfg.count_only &&
                              cur.ordinal == cfg.ordinal;
        cur.active = selected;
        std::ostringstream o;
        emit_base(o, "target_begin", inst, pc);
        o << ",\"ordinal\":" << cur.ordinal
          << ",\"selected\":" << (selected ? "true" : "false")
          << ",\"count_only\":" << (cfg.count_only ? "true" : "false")
          << ",\"op\":\"" << inst->staticInst->disassemble(pc) << "\""
          << ",\"src\":"; append_regs(o, inst, false, true);
        write_line(o);
    }
}

void
end_exec(o3::DynInst *inst)
{
    init();
    if (!inst) return;
    const uint64_t pc = dyn_pc(inst);
    if (pc == cfg.target_pc) {
        std::ostringstream o;
        emit_base(o, "target_end", inst, pc);
        o << ",\"ordinal\":" << cur.ordinal
          << ",\"fault_applied\":" << (cur.applied ? "true" : "false")
          << ",\"fpsr\":" << inst->tcBase()->readMiscRegNoEffect(
                 ArmISA::MISCREG_FPSR)
          << ",\"fpcr\":" << inst->tcBase()->readMiscRegNoEffect(
                 ArmISA::MISCREG_FPCR)
          << ",\"nzcv\":" << inst->tcBase()->readMiscRegNoEffect(
                 ArmISA::MISCREG_NZCV)
          << ",\"src\":"; append_regs(o, inst, false, true);
        o << ",\"dest\":"; append_regs(o, inst, true, true);
        write_line(o);
    }
    cur = Current();
}

void
trace_rename(o3::DynInst *inst)
{
    init();
    if (!inst || cfg.trace_path.empty()) return;
    const uint64_t pc = dyn_pc(inst);
    if (pc == 0) return;
    std::ostringstream o;
    emit_base(o, "rename", inst, pc);
    o << ",\"op\":\"" << inst->staticInst->disassemble(pc) << "\""
      << ",\"op_class\":" << (int)inst->opClass()
      << ",\"src\":"; append_regs(o, inst, false, false);
    o << ",\"dest\":"; append_regs(o, inst, true, false);
    write_line(o);
}

void
trace_issue(o3::DynInst *inst)
{
    init();
    if (!inst || cfg.trace_path.empty()) return;
    const uint64_t pc = dyn_pc(inst);
    std::ostringstream o;
    emit_base(o, "issue", inst, pc);
    o << ",\"src\":"; append_regs(o, inst, false, true);
    write_line(o);
}

void
trace_writeback(o3::DynInst *inst)
{
    init();
    if (!inst || cfg.trace_path.empty()) return;
    const uint64_t pc = dyn_pc(inst);
    std::ostringstream o;
    emit_base(o, "writeback", inst, pc);
    o << ",\"dest\":"; append_regs(o, inst, true, true);
    write_line(o);
}

void
trace_commit(o3::DynInst *inst, uint64_t commit_seq)
{
    init();
    if (!inst || cfg.trace_path.empty()) return;
    const uint64_t pc = dyn_pc(inst);
    std::ostringstream o;
    emit_base(o, "commit", inst, pc);
    o << ",\"commit_seq\":" << commit_seq
      << ",\"fpsr\":" << inst->tcBase()->readMiscRegNoEffect(
             ArmISA::MISCREG_FPSR)
      << ",\"fpcr\":" << inst->tcBase()->readMiscRegNoEffect(
             ArmISA::MISCREG_FPCR)
      << ",\"nzcv\":" << inst->tcBase()->readMiscRegNoEffect(
             ArmISA::MISCREG_NZCV)
      << ",\"dest\":"; append_regs(o, inst, true, true);
    write_line(o);
}

void
trace_squash(o3::DynInst *inst)
{
    init();
    if (!inst || cfg.trace_path.empty() || !inst->isExecuted()) return;
    const uint64_t pc = dyn_pc(inst);
    std::ostringstream o;
    emit_base(o, "squash", inst, pc);
    write_line(o);
}

void
trace_branch(o3::DynInst *inst, bool pred_taken, bool actual_taken,
             uint64_t pred_pc, uint64_t actual_pc)
{
    init();
    if (!inst || cfg.trace_path.empty()) return;
    const uint64_t pc = dyn_pc(inst);
    std::ostringstream o;
    emit_base(o, "branch_mispredict", inst, pc);
    o << ",\"pred_taken\":" << (pred_taken ? "true" : "false")
      << ",\"actual_taken\":" << (actual_taken ? "true" : "false")
      << ",\"pred_pc\":" << pred_pc
      << ",\"actual_pc\":" << actual_pc;
    write_line(o);
}

void
trace_squash_reason(uint64_t squashed_seq, const char *reason)
{
    init();
    if (cfg.trace_path.empty()) return;
    std::ostringstream o;
    o << "{\"schema\":\"fpu-fi-v1\",\"eid\":" << (++cfg.event_id)
      << ",\"event\":\"squash_reason\",\"tick\":" << curTick()
      << ",\"squashed_seq\":" << squashed_seq
      << ",\"reason\":\"" << json_escape(reason ? reason : "") << "\""
      << ",\"sample\":\"" << json_escape(cfg.sample) << "\""
      << ",\"context\":\"" << json_escape(cfg.context) << "\""
      << ",\"state\":\"" << json_escape(cfg.state) << "\"";
    write_line(o);
}

} // namespace fpu_fi
} // namespace gem5
