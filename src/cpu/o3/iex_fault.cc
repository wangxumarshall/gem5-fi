/*
 * IEX paper-experiment fault injection controller and read-only propagation
 * tracer.
 *
 * Fault semantics are injected at the audited ISA semantic points.  The
 * controller is configured entirely from the environment so the same
 * gem5.opt binary runs every Fault and Control sample; Control differs only
 * in IEX_FAULT_ENABLED=0 while selection and observation stay enabled.
 *
 * Trace is JSONL, one event per line, flushed after every line so aborted
 * runs keep all completed evidence.
 */

#include "cpu/o3/iex_fault.hh"

#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>

#include "base/logging.hh"
#include "base/types.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "cpu/reg_class.hh"
#include "sim/core.hh"
#include "sim/faults.hh"

namespace gem5
{
namespace iex
{

namespace
{

struct RegRec
{
    uint64_t producer_seq = 0;
    uint64_t generation = 0;
    uint64_t value = 0;
    Tick tick = 0;
};

struct InstRec
{
    uint64_t pc = 0;
    Tick begin_tick = 0;
    Tick end_tick = 0;
    Tick commit_tick = 0;
    bool executed = false;
    bool ended = false;
    bool committed = false;
    bool squashed = false;
};

struct State
{
    bool initialized = false;
    bool observing = false;
    bool fault_enabled = false;
    std::string model;
    std::string run_id;
    std::string sample_id;
    std::string pair_id;
    std::string context;
    std::string workload;
    std::string fault_config;
    std::string oracle_id;
    std::string seed;
    std::string gem5_commit;
    uint64_t target_pc = ~0ULL;
    uint64_t consumer_pc = ~0ULL;
    uint64_t roi_start = 0;
    uint64_t roi_end = ~0ULL;
    FILE *out = nullptr;
    bool roi_open = false;
    uint64_t eligible_count = 0;
    uint64_t applied_count = 0;
    uint64_t target_seq = 0;
    bool target_seen = false;
    bool injection_applied = false;
    uint64_t generation = 0;
    uint64_t last_event_tick = 0;
    o3::DynInst *current = nullptr;
    std::unordered_map<uint64_t, InstRec> observed;
    std::unordered_map<uint64_t, RegRec> regs;
    uint64_t next_event_id = 1;
    std::unordered_map<uint64_t, uint64_t> begin_event;
    std::unordered_map<uint64_t, uint64_t> last_event;
    uint64_t observed_count = 0;
    uint64_t committed_count = 0;
    uint64_t squashed_count = 0;
    uint64_t unknown_count = 0;
    uint64_t last_squash_branch = ~0ULL;
    uint64_t last_squash_seq = ~0ULL;
    Tick last_squash_tick = 0;
    std::string last_squash_reason;
};

State &state();

static void
initState(State &s)
{
    {
        const char *v;

        s.model = getenv("IEX_MODEL") ? getenv("IEX_MODEL") : "";
        s.run_id = getenv("IEX_RUN_ID") ? getenv("IEX_RUN_ID") : "";
        s.sample_id = getenv("IEX_SAMPLE_ID") ? getenv("IEX_SAMPLE_ID") : "";
        s.pair_id = getenv("IEX_PAIR_ID") ? getenv("IEX_PAIR_ID") : "";
        s.context = getenv("IEX_CONTEXT") ? getenv("IEX_CONTEXT") : "";
        s.workload = getenv("IEX_WORKLOAD") ? getenv("IEX_WORKLOAD") : "";
        s.fault_config =
            getenv("IEX_FAULT_CONFIG") ? getenv("IEX_FAULT_CONFIG") : "";
        s.oracle_id = getenv("IEX_ORACLE_ID") ? getenv("IEX_ORACLE_ID") : "";
        s.seed = getenv("IEX_SEED") ? getenv("IEX_SEED") : "";
        s.gem5_commit =
            getenv("IEX_GEM5_COMMIT") ? getenv("IEX_GEM5_COMMIT") : "";

        v = getenv("IEX_FAULT_ENABLED");
        s.fault_enabled = v && (std::strcmp(v, "1") == 0 ||
                                std::strcmp(v, "yes") == 0 ||
                                std::strcmp(v, "true") == 0);

        v = getenv("IEX_TARGET_PC");
        if (v && *v)
            s.target_pc = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_CONSUMER_PC");
        if (v && *v)
            s.consumer_pc = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_ROI_START");
        if (v && *v)
            s.roi_start = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_ROI_END");
        if (v && *v)
            s.roi_end = std::strtoull(v, nullptr, 0);

        const char *path = getenv("IEX_TRACE_FILE");
        if (path && *path) {
            s.out = std::fopen(path, "w");
            if (!s.out)
                panic("IEX: cannot open trace file '%s'\n", path);
            std::setvbuf(s.out, nullptr, _IOLBF, 0);
            s.observing = true;
            std::atexit([] {
                State &s = state();
                if (!s.out)
                    return;
                for (auto &kv : s.observed) {
                    if (!kv.second.committed && !kv.second.squashed)
                        ++s.unknown_count;
                }
                std::fprintf(
                    s.out,
                    "{\"schema\":\"iex-trace-v1\",\"event\":\"run_end\","
                    "\"tick\":%" PRIu64 ",\"event_id\":%" PRIu64 ","
                    "\"parent_event_ids\":[],\"fault_id\":\"%s\","
                    "\"dynamic_instruction_id\":0,\"run_id\":\"%s\","
                    "\"sample_id\":\"%s\",\"pair_id\":\"%s\","
                    "\"model\":\"%s\",\"context\":\"%s\","
                    "\"fault_enabled\":%d,\"observed_insts\":%" PRIu64 ","
                    "\"committed_observed\":%" PRIu64 ","
                    "\"squashed_observed\":%" PRIu64 ","
                    "\"unknown_observed\":%" PRIu64 ","
                    "\"eligible_events\":%" PRIu64 ","
                    "\"applied_events\":%" PRIu64 ","
                    "\"injection_applied\":%d,\"target_seq\":%" PRIu64 ","
                    "\"target_seen\":%d,\"trace_complete\":1}\n",
                    static_cast<uint64_t>(curTick()), s.next_event_id++,
                    s.fault_config.c_str(), s.run_id.c_str(),
                    s.sample_id.c_str(), s.pair_id.c_str(),
                    s.model.c_str(), s.context.c_str(),
                    s.fault_enabled ? 1 : 0, s.observed_count,
                    s.committed_count, s.squashed_count, s.unknown_count,
                    s.eligible_count, s.applied_count,
                    s.injection_applied ? 1 : 0, s.target_seq,
                    s.target_seen ? 1 : 0);
                std::fflush(s.out);
                std::fclose(s.out);
                s.out = nullptr;
            });
        }

        s.initialized = true;

        if (s.observing) {
            std::fprintf(
                s.out,
                "{\"schema\":\"iex-trace-v1\",\"event\":\"run_start\","
                "\"tick\":%" PRIu64 ",\"event_id\":0,"
                "\"parent_event_ids\":[],\"fault_id\":\"%s\","
                "\"dynamic_instruction_id\":0,\"run_id\":\"%s\","
                "\"sample_id\":\"%s\",\"pair_id\":\"%s\","
                "\"model\":\"%s\",\"context\":\"%s\","
                "\"workload\":\"%s\",\"fault_config\":\"%s\","
                "\"oracle_id\":\"%s\",\"seed\":\"%s\","
                "\"gem5_commit\":\"%s\",\"fault_enabled\":%d,"
                "\"target_pc\":\"0x%016" PRIx64 "\","
                "\"consumer_pc\":\"0x%016" PRIx64 "\","
                "\"roi_start\":\"0x%016" PRIx64 "\","
                "\"roi_end\":\"0x%016" PRIx64 "\","
                "\"trace_schema\":\"iex-trace-v1\"}\n",
                static_cast<uint64_t>(curTick()), s.fault_config.c_str(),
                s.run_id.c_str(), s.sample_id.c_str(), s.pair_id.c_str(),
                s.model.c_str(), s.context.c_str(), s.workload.c_str(),
                s.fault_config.c_str(), s.oracle_id.c_str(),
                s.seed.c_str(), s.gem5_commit.c_str(),
                s.fault_enabled ? 1 : 0, s.target_pc, s.consumer_pc,
                s.roi_start, s.roi_end);
            std::fflush(s.out);
        }
    }
}

State &
state()
{
    // Single simulation thread: plain lazy initialisation avoids a
    // recursive std::call_once (initState registers an exit handler that
    // calls state() again).
    static State *s = nullptr;
    if (!s) {
        s = new State();
        initState(*s);
    }
    return *s;
}

static inline std::string
jstr(const std::string &s)
{
    // Identifiers in this experiment are simple; still guard the two
    // JSON-significant characters if a caller supplies something else.
    std::string tmp;
    tmp.reserve(s.size() + 8);
    for (char c : s) {
        if (c == '"' || c == '\\')
            tmp.push_back('\\');
        tmp.push_back(c);
    }
    return tmp;
}

static inline uint64_t
regKey(const PhysRegIdPtr &r)
{
    return (static_cast<uint64_t>(r->classValue()) << 32) |
           static_cast<uint32_t>(r->index());
}

static inline bool
inRoi(const State &s, uint64_t pc)
{
    return pc >= s.roi_start && pc < s.roi_end;
}

static std::string
parentList(const std::vector<uint64_t> &ids)
{
    std::string out = "[";
    bool first = true;
    uint64_t prev = ~0ULL;
    for (uint64_t id : ids) {
        if (id == 0 || id == prev)
            continue;
        char b[32];
        std::snprintf(b, sizeof(b), "%s%" PRIu64, first ? "" : ",", id);
        out += b;
        first = false;
        prev = id;
    }
    out += "]";
    return out;
}

static void
emitFull(State &s, const char *event, const std::string &body,
         uint64_t seq = 0, const std::vector<uint64_t> &extra = {})
{
    if (!s.observing || !s.out)
        return;
    std::vector<uint64_t> parents = extra;
    if (seq) {
        auto b = s.begin_event.find(seq);
        if (b != s.begin_event.end())
            parents.push_back(b->second);
        auto l = s.last_event.find(seq);
        if (l != s.last_event.end())
            parents.push_back(l->second);
    }
    const uint64_t eid = s.next_event_id++;
    char head[1024];
    std::snprintf(head, sizeof(head),
                  "{\"schema\":\"iex-trace-v1\",\"event\":\"%s\","
                  "\"tick\":%" PRIu64 ",\"event_id\":%" PRIu64 ","
                  "\"parent_event_ids\":%s,\"fault_id\":\"%s\","
                  "\"dynamic_instruction_id\":%" PRIu64 ","
                  "\"run_id\":\"%s\",\"sample_id\":\"%s\","
                  "\"pair_id\":\"%s\",\"model\":\"%s\","
                  "\"context\":\"%s\",\"fault_enabled\":%d",
                  event, static_cast<uint64_t>(curTick()), eid,
                  parentList(parents).c_str(),
                  jstr(s.fault_config).c_str(), seq,
                  jstr(s.run_id).c_str(), jstr(s.sample_id).c_str(),
                  jstr(s.pair_id).c_str(), jstr(s.model).c_str(),
                  jstr(s.context).c_str(), s.fault_enabled ? 1 : 0);
    std::string line(head);
    line += ",";
    line += body;
    line += "}\n";
    std::fwrite(line.data(), 1, line.size(), s.out);
    std::fflush(s.out);
    if (seq) {
        if (std::strcmp(event, "inst_exec_begin") == 0)
            s.begin_event[seq] = eid;
        s.last_event[seq] = eid;
    }
    s.last_event_tick = curTick();
}

static std::string
regArray(State &s, o3::DynInst *d, bool dest)
{
    std::string out = "[";
    int n = dest ? d->numDestRegs() : d->numSrcRegs();
    bool first = true;
    for (int i = 0; i < n; ++i) {
        const PhysRegIdPtr &r =
            dest ? d->renamedDestIdx(i) : d->renamedSrcIdx(i);
        if (!r || r->is(InvalidRegClass))
            continue;
        const RegId &arch =
            dest ? d->destRegIdx(i) : d->srcRegIdx(i);
        uint64_t v = 0;
        if (d->cpu)
            v = d->cpu->getReg(r, d->threadNumber);
        auto it = s.regs.find(regKey(r));
        uint64_t prod = it == s.regs.end() ? 0 : it->second.producer_seq;
        uint64_t gen = it == s.regs.end() ? 0 : it->second.generation;
        char b[512];
        std::snprintf(
            b, sizeof(b),
            "%s{\"cls\":\"%s\",\"class_value\":%d,\"phys\":%u,"
            "\"flat\":%u,\"arch\":%u,\"arch_cls\":%d,"
            "\"value\":\"0x%016" PRIx64 "\",\"producer_seq\":%" PRIu64 ","
            "\"gen\":%" PRIu64 "}",
            first ? "" : ",", jstr(r->className()).c_str(),
            static_cast<int>(r->classValue()),
            static_cast<unsigned>(r->index()),
            static_cast<unsigned>(r->flatIndex()),
            static_cast<unsigned>(arch.index()),
            static_cast<int>(arch.classValue()), v, prod, gen);
        out += b;
        first = false;
    }
    out += "]";
    return out;
}

static uint64_t
resolvedNpc(o3::DynInst *d)
{
    std::unique_ptr<PCStateBase> next(d->pcState().clone());
    d->staticInst->advancePC(*next);
    return next->instAddr();
}

static bool
hasFault(const o3::DynInst *d)
{
    return d->getFault() != NoFault;
}

/* Called by every model site once the target PC matched.  Records the
 * dynamic-instruction identity and returns whether this is the first
 * eligible event. */
static bool
select(State &s, uint64_t pc)
{
    if (s.current) {
        s.target_seen = true;
        if (!s.target_seq)
            s.target_seq = s.current->seqNum;
    }
    ++s.eligible_count;
    (void)pc;
    return s.eligible_count == 1;
}

static void
logIneligible(State &s, uint64_t pc, const char *reason, uint64_t a,
              uint64_t b)
{
    char bdy[512];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"tid\":%d,\"reason\":\"%s\",\"a\":\"0x%016" PRIx64 "\","
                  "\"b\":\"0x%016" PRIx64 "\"",
                  s.current ? s.current->seqNum : 0ULL, pc,
                  s.current ? s.current->threadNumber : 0, reason, a, b);
    emitFull(s, "ineligible", bdy, s.current ? s.current->seqNum : 0);
}

} // anonymous namespace

static void
beginObserved(State &s, o3::DynInst *d, const char *path)
{
    if (!s.observing || !d)
        return;
    if (s.observed.find(d->seqNum) != s.observed.end())
        return;
    uint64_t pc = d->pcState().instAddr();
    if (!inRoi(s, pc))
        return;

    if (!s.roi_open) {
        s.roi_open = true;
        char bdy[256];
        std::snprintf(bdy, sizeof(bdy),
                      "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                      "\"tid\":%d,\"roi_start\":\"0x%016" PRIx64 "\","
                      "\"roi_end\":\"0x%016" PRIx64 "\"",
                      d->seqNum, pc, d->threadNumber, s.roi_start,
                      s.roi_end);
        emitFull(s, "roi_open", bdy, 0);
    }

    InstRec rec;
    rec.pc = pc;
    rec.begin_tick = curTick();
    s.observed[d->seqNum] = rec;
    ++s.observed_count;

    std::vector<uint64_t> src_parents;
    for (int i = 0; i < d->numSrcRegs(); ++i) {
        const PhysRegIdPtr &r = d->renamedSrcIdx(i);
        if (!r || r->is(InvalidRegClass))
            continue;
        auto it = s.regs.find(regKey(r));
        if (it == s.regs.end())
            continue;
        auto le = s.last_event.find(it->second.producer_seq);
        if (le != s.last_event.end())
            src_parents.push_back(le->second);
    }
    char bdy[4096];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"tid\":%d,\"opcode\":\"%s\",\"op_class\":%d,"
        "\"path\":\"%s\",\"is_control\":%d,\"is_load\":%d,"
        "\"is_store\":%d,\"is_integer\":%d,\"predicted_taken\":%d,"
        "\"predicted_npc\":\"0x%016" PRIx64 "\",\"srcs\":%s",
        d->seqNum, pc, d->threadNumber,
        jstr(d->staticInst->getName()).c_str(),
        static_cast<int>(d->opClass()), path, d->isControl() ? 1 : 0,
        d->isLoad() ? 1 : 0, d->isStore() ? 1 : 0,
        d->isInteger() ? 1 : 0, d->readPredTaken() ? 1 : 0,
        d->readPredTarg().instAddr(), regArray(s, d, false).c_str());
    emitFull(s, "inst_exec_begin", bdy, d->seqNum, src_parents);
}

static void
endObserved(State &s, o3::DynInst *d)
{
    if (!s.observing || !d)
        return;
    auto it = s.observed.find(d->seqNum);
    if (it == s.observed.end())
        return;
    InstRec &rec = it->second;
    if (rec.ended)
        return;
    rec.ended = true;
    rec.executed = true;
    rec.end_tick = curTick();

    uint64_t resolved = 0;
    bool mispred = false;
    if (d->isControl()) {
        resolved = resolvedNpc(d);
        mispred = d->mispredicted();
    }

    char addr[96] = "";
    if ((d->isLoad() || d->isStore()) && d->effAddrValid()) {
        std::snprintf(addr, sizeof(addr),
                      ",\"eff_addr\":\"0x%016" PRIx64 "\","
                      "\"phys_eff_addr\":\"0x%016" PRIx64 "\","
                      "\"mem_size\":%u",
                      static_cast<uint64_t>(d->effAddr),
                      static_cast<uint64_t>(d->physEffAddr),
                      d->staticInst->size());
    }

    char bdy[4096];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"tid\":%d,\"opcode\":\"%s\",\"op_class\":%d,"
        "\"fault\":%d,\"executed\":1,\"is_control\":%d,"
        "\"predicted_taken\":%d,\"predicted_npc\":\"0x%016" PRIx64 "\","
        "\"resolved_npc\":\"0x%016" PRIx64 "\",\"mispredicted\":%d,"
        "\"dests\":%s%s",
        d->seqNum, rec.pc, d->threadNumber,
        jstr(d->staticInst->getName()).c_str(),
        static_cast<int>(d->opClass()), hasFault(d) ? 1 : 0,
        d->isControl() ? 1 : 0, d->readPredTaken() ? 1 : 0,
        d->readPredTarg().instAddr(), resolved, mispred ? 1 : 0,
        regArray(s, d, true).c_str(), addr);
    emitFull(s, "inst_exec_end", bdy, d->seqNum);

    if (d->isControl()) {
        char bb[512];
        std::snprintf(bb, sizeof(bb),
                      "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                      "\"predicted_npc\":\"0x%016" PRIx64 "\","
                      "\"resolved_npc\":\"0x%016" PRIx64 "\","
                      "\"predicted_taken\":%d,\"mispredicted\":%d,"
                      "\"redirect_required\":%d",
                      d->seqNum, rec.pc, d->readPredTarg().instAddr(),
                      resolved, d->readPredTaken() ? 1 : 0,
                      mispred ? 1 : 0, mispred ? 1 : 0);
        emitFull(s, "branch_resolve", bb, d->seqNum);
    }
    if (s.current == d)
        s.current = nullptr;
}

void
noteExecuteBegin(o3::DynInst *d)
{
    State &s = state();
    s.current = d;
    beginObserved(s, d, "execute");
}

void
noteExecuteEnd(o3::DynInst *d)
{
    State &s = state();
    endObserved(s, d);
    if (s.current == d)
        s.current = nullptr;
}

void
noteInitiateAcc(o3::DynInst *d)
{
    State &s = state();
    s.current = d;
    beginObserved(s, d, "mem_initiate");
    if (!s.observing || !d)
        return;
    auto it = s.observed.find(d->seqNum);
    if (it == s.observed.end())
        return;
    char bdy[1024];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"tid\":%d,\"is_load\":%d,\"is_store\":%d,"
        "\"eff_addr\":\"0x%016" PRIx64 "\","
        "\"phys_eff_addr\":\"0x%016" PRIx64 "\",\"srcs\":%s",
        d->seqNum, it->second.pc, d->threadNumber, d->isLoad() ? 1 : 0,
        d->isStore() ? 1 : 0, static_cast<uint64_t>(d->effAddr),
        static_cast<uint64_t>(d->physEffAddr),
        regArray(s, d, false).c_str());
    emitFull(s, "mem_access", bdy, d->seqNum);
}

void
noteCompleteAcc(o3::DynInst *d)
{
    State &s = state();
    endObserved(s, d);
    if (s.current == d)
        s.current = nullptr;
}

void
noteRegWrite(o3::DynInst *d, int idx, uint64_t val, uint64_t old)
{
    State &s = state();
    if (!s.observing || !d)
        return;
    auto it = s.observed.find(d->seqNum);
    if (it == s.observed.end())
        return;
    const PhysRegIdPtr &r = d->renamedDestIdx(idx);
    if (!r || r->is(InvalidRegClass))
        return;
    const RegId &arch = d->destRegIdx(idx);
    ++s.generation;
    RegRec &rr = s.regs[regKey(r)];
    rr.producer_seq = d->seqNum;
    rr.generation = s.generation;
    rr.value = val;
    rr.tick = curTick();

    char bdy[1024];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"tid\":%d,\"cls\":\"%s\",\"class_value\":%d,\"phys\":%u,"
        "\"flat\":%u,\"arch\":%u,\"arch_cls\":%d,\"old\":\"0x%016" PRIx64
        "\",\"new\":\"0x%016" PRIx64 "\",\"gen\":%" PRIu64,
        d->seqNum, it->second.pc, d->threadNumber, jstr(r->className()).c_str(),
        static_cast<int>(r->classValue()),
        static_cast<unsigned>(r->index()),
        static_cast<unsigned>(r->flatIndex()),
        static_cast<unsigned>(arch.index()),
        static_cast<int>(arch.classValue()), old, val, s.generation);
    emitFull(s, "reg_write", bdy, d->seqNum);
}

void
noteWriteback(o3::DynInst *d, int dependents)
{
    State &s = state();
    if (!s.observing || !d)
        return;
    auto it = s.observed.find(d->seqNum);
    if (it == s.observed.end())
        return;
    endObserved(s, d);
    char bdy[2048];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"tid\":%d,\"dependents_woken\":%d,\"executed\":%d,"
                  "\"squashed\":%d,\"fault\":%d,\"dests\":%s",
                  d->seqNum, it->second.pc, d->threadNumber, dependents,
                  d->isExecuted() ? 1 : 0, d->isSquashed() ? 1 : 0,
                  hasFault(d) ? 1 : 0, regArray(s, d, true).c_str());
    emitFull(s, "writeback", bdy, d->seqNum);
}

void
noteCommit(o3::DynInst *d, unsigned rob_entries)
{
    State &s = state();
    if (!s.observing || !d)
        return;
    auto it = s.observed.find(d->seqNum);
    if (it == s.observed.end())
        return;
    InstRec &rec = it->second;
    rec.committed = true;
    rec.commit_tick = curTick();
    ++s.committed_count;

    char bdy[2048];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"tid\":%d,\"opcode\":\"%s\",\"rob_entries\":%u,"
                  "\"dests\":%s",
                  d->seqNum, rec.pc, d->threadNumber,
                  jstr(d->staticInst->getName()).c_str(), rob_entries,
                  regArray(s, d, true).c_str());
    emitFull(s, "commit", bdy, d->seqNum);
}

void
noteSquash(ThreadID tid, uint64_t branch_seq, uint64_t squashed_seq,
           const char *reason, unsigned rob_entries)
{
    State &s = state();
    if (!s.observing || !s.roi_open)
        return;
    uint64_t first = 0, last = 0, count = 0;
    for (auto &kv : s.observed) {
        if (kv.first > squashed_seq && !kv.second.committed) {
            if (!count)
                first = kv.first;
            last = kv.first;
            kv.second.squashed = true;
            ++count;
        }
    }
    s.squashed_count += count;
    /* Squashes entirely outside the observed chain (e.g. libc exit-path
     * branch training after the ROI) are not part of this sample's
     * propagation evidence. Keep the event when the branch itself or any
     * observed younger instruction is affected. */
    if (count == 0 && s.observed.find(branch_seq) == s.observed.end())
        return;
    /* IEW::squash() is polled every cycle during ROB squashing; fold the
     * repeated notifications of one squash episode into one event. */
    if (branch_seq == s.last_squash_branch &&
        squashed_seq == s.last_squash_seq &&
        reason == s.last_squash_reason &&
        curTick() - s.last_squash_tick < 1000)
        return;
    s.last_squash_branch = branch_seq;
    s.last_squash_seq = squashed_seq;
    s.last_squash_reason = reason;
    s.last_squash_tick = curTick();
    char bdy[1024];
    std::snprintf(bdy, sizeof(bdy),
                  "\"tid\":%d,\"branch_seq\":%" PRIu64 ","
                  "\"squashed_seq\":%" PRIu64 ",\"reason\":\"%s\","
                  "\"observed_squashed\":%" PRIu64 ",\"seq_first\":%" PRIu64
                  ",\"seq_last\":%" PRIu64 ",\"rob_entries\":%u",
                  tid, branch_seq, squashed_seq, reason, count, first, last,
                  rob_entries);
    emitFull(s, "squash", bdy, branch_seq);
}

void
noteSquashInfo(ThreadID tid, uint64_t squashed_seq, const char *reason,
               unsigned rob_entries)
{
    noteSquash(tid, 0, squashed_seq, reason, rob_entries);
}

void
noteBranchResolve(o3::DynInst *d, uint64_t pred_npc, uint64_t resolved_npc,
                  bool predicted_taken, bool mispredicted)
{
    State &s = state();
    if (!s.observing || !d)
        return;
    auto it = s.observed.find(d->seqNum);
    if (it == s.observed.end())
        return;
    char bdy[512];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"predicted_npc\":\"0x%016" PRIx64 "\","
                  "\"resolved_npc\":\"0x%016" PRIx64 "\","
                  "\"predicted_taken\":%d,\"mispredicted\":%d",
                  d->seqNum, it->second.pc, pred_npc, resolved_npc,
                  predicted_taken ? 1 : 0, mispredicted ? 1 : 0);
    emitFull(s, "branch_resolve_iew", bdy, d->seqNum);
}

/* ------------------------------------------------------------------ */
/* Model hooks                                                         */
/* ------------------------------------------------------------------ */

uint64_t
m001_add(uint64_t pc, uint64_t a, uint64_t b, uint64_t normal)
{
    State &s = state();
    if (s.model != "IEX-M001" || pc != s.target_pc)
        return normal;
    uint64_t c32 = ((a & 0xffffffffULL) + (b & 0xffffffffULL)) >> 32;
    if (c32 != 1) {
        logIneligible(s, pc, "no_carry32", a, b);
        return normal;
    }
    bool first = select(s, pc);
    uint64_t faulty = normal - 0x100000000ULL;
    bool apply = first && s.fault_enabled && !s.injection_applied;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    if (s.observing) {
        char bdy[1024];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"AddXSReg::execute\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"a\":\"0x%016" PRIx64 "\",\"b\":\"0x%016" PRIx64 "\","
            "\"carry32\":%" PRIu64 ",\"low32_sum\":\"0x%016" PRIx64 "\","
            "\"normal\":\"0x%016" PRIx64 "\","
            "\"faulty\":\"0x%016" PRIx64 "\","
            "\"low32_unchanged\":%d,\"delta\":\"0x%016" PRIx64 "\"",
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0, a, b, c32,
            (a & 0xffffffffULL) + (b & 0xffffffffULL), normal, faulty,
            ((normal & 0xffffffffULL) == (faulty & 0xffffffffULL)) ? 1 : 0,
            normal - faulty);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return apply ? faulty : normal;
}

uint64_t
m002_lslv_amt(uint64_t pc, uint64_t a, uint64_t b, uint64_t width)
{
    State &s = state();
    if (s.model != "IEX-M002" || pc != s.target_pc)
        return b;
    uint64_t mask = width - 1;
    uint64_t eff = b & mask;
    uint64_t alt = eff ^ 1ULL;
    uint64_t rn = width == 64 ? (a << eff) : ((a << eff) & 0xffffffffULL);
    uint64_t rf = width == 64 ? (a << alt) : ((a << alt) & 0xffffffffULL);
    if (a == 0 || rn == rf) {
        logIneligible(s, pc, a == 0 ? "a_zero_guard" : "indistinguishable",
                      a, b);
        return b;
    }
    bool first = select(s, pc);
    bool apply = first && s.fault_enabled && !s.injection_applied;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    if (s.observing) {
        char bdy[1024];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"Lslv64::execute\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"a\":\"0x%016" PRIx64 "\",\"b_raw\":\"0x%016" PRIx64 "\","
            "\"width\":%" PRIu64 ",\"effective_shift_old\":%" PRIu64 ","
            "\"effective_shift_new\":%" PRIu64 ","
            "\"result_normal\":\"0x%016" PRIx64 "\","
            "\"result_faulty\":\"0x%016" PRIx64 "\"",
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0, a, b, width, eff, alt, rn,
            rf);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return apply ? alt : b;
}

uint64_t
m003_l214(uint64_t pc, uint64_t op1h, uint64_t op1l, uint64_t op2h,
          uint64_t op2l, uint64_t mid1, uint64_t mid2, uint64_t result)
{
    State &s = state();
    if (s.model != "IEX-M003" || pc != s.target_pc)
        return result;
    if (result != 1) {
        logIneligible(s, pc, "c214_not_one", mid1, mid2);
        return result;
    }
    bool first = select(s, pc);
    bool apply = first && s.fault_enabled && !s.injection_applied;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    uint64_t low_product_hi = ((uint32_t)mid1 + (uint32_t)mid2) >> 32;
    if (s.observing) {
        char bdy[2048];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"Umulh64::execute:L214\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"op1l\":\"0x%016" PRIx64 "\",\"op1h\":\"0x%016" PRIx64 "\","
            "\"op2l\":\"0x%016" PRIx64 "\",\"op2h\":\"0x%016" PRIx64 "\","
            "\"mid1\":\"0x%016" PRIx64 "\",\"mid2\":\"0x%016" PRIx64 "\","
            "\"low_product_hi\":\"0x%016" PRIx64 "\","
            "\"result_l214_before\":%" PRIu64 ","
            "\"result_l214_after\":%" PRIu64,
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0, op1l, op1h, op2l, op2h, mid1,
            mid2, low_product_hi, result, apply ? 0ULL : result);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return apply ? 0 : result;
}

void
m003_after215(uint64_t pc, uint64_t result)
{
    State &s = state();
    if (s.model != "IEX-M003" || pc != s.target_pc || !s.observing)
        return;
    char bdy[256];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"result_after_l215\":\"0x%016" PRIx64 "\"",
                  s.current ? s.current->seqNum : 0ULL, pc, result);
    emitFull(s, "model_witness_l215", bdy, s.current ? s.current->seqNum : 0);
}

void
m003_after216(uint64_t pc, uint64_t result)
{
    State &s = state();
    if (s.model != "IEX-M003" || pc != s.target_pc || !s.observing)
        return;
    char bdy[256];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"result_after_l216\":\"0x%016" PRIx64 "\"",
                  s.current ? s.current->seqNum : 0ULL, pc, result);
    emitFull(s, "model_witness_l216", bdy, s.current ? s.current->seqNum : 0);
}

void
m003_final(uint64_t pc, uint64_t op1h, uint64_t op2h,
           uint64_t result_before_hh, uint64_t xd)
{
    State &s = state();
    if (s.model != "IEX-M003" || pc != s.target_pc || !s.observing)
        return;
    char bdy[512];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"hi_mid1_plus_mid2\":\"0x%016" PRIx64 "\","
        "\"op1h_x_op2h\":\"0x%016" PRIx64 "\","
        "\"result_before_l217\":\"0x%016" PRIx64 "\","
        "\"xd\":\"0x%016" PRIx64 "\"",
        s.current ? s.current->seqNum : 0ULL, pc, result_before_hh,
        op1h * op2h, result_before_hh, xd);
    emitFull(s, "model_witness_l217", bdy, s.current ? s.current->seqNum : 0);
}

bool
m004_force_zero(uint64_t pc, uint64_t a, uint64_t b)
{
    State &s = state();
    if (s.model != "IEX-M004" || pc != s.target_pc)
        return false;
    if (b == 0 || a < b) {
        logIneligible(s, pc, b == 0 ? "divisor_zero_guard" : "a_lt_b_guard",
                      a, b);
        return false;
    }
    bool first = select(s, pc);
    bool apply = first && s.fault_enabled && !s.injection_applied;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    if (s.observing) {
        char bdy[768];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"Udiv64::execute\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"a\":\"0x%016" PRIx64 "\",\"b\":\"0x%016" PRIx64 "\","
            "\"divisor_nonzero\":1,\"a_ge_b\":1,\"forced_zero\":%d",
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0, a, b, apply ? 1 : 0);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return apply;
}

void
m004_result(uint64_t pc, uint64_t a, uint64_t b, uint64_t result)
{
    State &s = state();
    if (s.model != "IEX-M004" || pc != s.target_pc || !s.observing)
        return;
    char bdy[512];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"a\":\"0x%016" PRIx64 "\",\"b\":\"0x%016" PRIx64
                  "\",\"quotient\":\"0x%016" PRIx64 "\","
                  "\"result_is_zero\":%d",
                  s.current ? s.current->seqNum : 0ULL, pc, a, b, result,
                  result == 0 ? 1 : 0);
    emitFull(s, "model_witness_quotient", bdy, s.current ? s.current->seqNum : 0);
}

bool
m005_bcond(uint64_t pc, bool taken, uint64_t nz, uint64_t c, uint64_t v,
           int cond, uint64_t target_npc, uint64_t fallthrough_npc)
{
    State &s = state();
    if (s.model != "IEX-M005" || pc != s.target_pc)
        return taken;
    bool first = select(s, pc);
    bool apply = first && s.fault_enabled && !s.injection_applied;
    bool actual = apply ? !taken : taken;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    uint64_t nzcv = (((nz >> 1) & 1) << 3) | ((nz & 1) << 2) |
                    ((c & 1) << 1) | (v & 1);
    uint64_t pred = s.current ? s.current->readPredTarg().instAddr() : 0;
    if (s.observing) {
        char bdy[1024];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"BCond64::execute\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"nzcv\":\"0x%x\",\"nz_bits\":%" PRIu64 ",\"c\":%" PRIu64
            ",\"v\":%" PRIu64 ",\"cond\":%d,"
            "\"taken_golden\":%d,\"taken_actual\":%d,"
            "\"predicted_npc\":\"0x%016" PRIx64 "\","
            "\"target_npc\":\"0x%016" PRIx64 "\","
            "\"fallthrough_npc\":\"0x%016" PRIx64 "\","
            "\"golden_npc\":\"0x%016" PRIx64 "\","
            "\"fault_npc\":\"0x%016" PRIx64 "\","
            "\"predicted_matches_golden\":%d,"
            "\"predicted_matches_fault\":%d",
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0,
            static_cast<unsigned>(nzcv), nz, c, v, cond, taken ? 1 : 0,
            actual ? 1 : 0, pred, target_npc, fallthrough_npc,
            taken ? target_npc : fallthrough_npc,
            actual ? target_npc : fallthrough_npc,
            pred == (taken ? target_npc : fallthrough_npc) ? 1 : 0,
            pred == (actual ? target_npc : fallthrough_npc) ? 1 : 0);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return actual;
}

uint64_t
m006_iz(uint64_t pc, uint64_t res_temp, uint64_t iz, uint64_t in)
{
    State &s = state();
    if (s.model != "IEX-M006" || pc != s.target_pc)
        return iz;
    bool first = select(s, pc);
    bool apply = first && s.fault_enabled && !s.injection_applied;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    if (s.observing) {
        char bdy[768];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"SubXSRegCc::execute:_iz\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"subs_result\":\"0x%016" PRIx64 "\",\"in_n\":%" PRIu64 ","
            "\"iz_before\":%" PRIu64 ",\"iz_after\":%" PRIu64,
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0, res_temp, in, iz,
            apply ? (iz ^ 1) : iz);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return apply ? (iz ^ 1) : iz;
}

void
m006_flags(uint64_t pc, uint64_t res_temp, uint64_t nz, uint64_t c,
           uint64_t v)
{
    State &s = state();
    if (s.model != "IEX-M006" || pc != s.target_pc || !s.observing)
        return;
    uint64_t nzcv = (((nz >> 1) & 1) << 3) | ((nz & 1) << 2) |
                    ((c & 1) << 1) | (v & 1);
    char bdy[512];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"subs_result\":\"0x%016" PRIx64 "\","
                  "\"nz\":%" PRIu64 ",\"z\":%" PRIu64 ",\"n\":%" PRIu64
                  ",\"c\":%" PRIu64 ",\"v\":%" PRIu64
                  ",\"nzcv\":\"0x%x\",\"fault_applied\":%d",
                  s.current ? s.current->seqNum : 0ULL, pc, res_temp, nz,
                  nz & 1, (nz >> 1) & 1, c, v,
                  static_cast<unsigned>(nzcv),
                  s.injection_applied ? 1 : 0);
    emitFull(s, "model_witness_flags", bdy, s.current ? s.current->seqNum : 0);
}

void
m006_csel(uint64_t pc, bool eq, uint64_t op1, uint64_t op2, uint64_t selected,
          uint64_t result)
{
    State &s = state();
    if (s.model != "IEX-M006" || pc != s.consumer_pc || !s.observing)
        return;

    uint64_t cc_phys = ~0ULL, cc_gen = 0, cc_prod = 0;
    std::string cc_cls = "";
    if (s.current) {
        for (int i = 0; i < s.current->numSrcRegs(); ++i) {
            const PhysRegIdPtr &r = s.current->renamedSrcIdx(i);
            if (!r || r->is(InvalidRegClass))
                continue;
            if (r->classValue() == CCRegClass) {
                cc_phys = r->index();
                cc_cls = r->className();
                auto it = s.regs.find(regKey(r));
                if (it != s.regs.end()) {
                    cc_gen = it->second.generation;
                    cc_prod = it->second.producer_seq;
                }
                break;
            }
        }
    }

    char bdy[1024];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"tid\":%d,\"site\":\"CSEL::execute\","
        "\"actual_eq\":%d,\"op1\":\"0x%016" PRIx64 "\","
        "\"op2\":\"0x%016" PRIx64 "\",\"selected\":\"0x%016" PRIx64 "\","
        "\"result\":\"0x%016" PRIx64 "\",\"cc_phys\":\"%s:%" PRIu64 "\","
        "\"cc_gen\":%" PRIu64 ",\"cc_producer_seq\":%" PRIu64,
        s.current ? s.current->seqNum : 0ULL, pc,
        s.current ? s.current->threadNumber : 0, eq ? 1 : 0, op1, op2,
        selected, result, cc_cls.c_str(), cc_phys, cc_gen, cc_prod);
    emitFull(s, "model_witness_csel", bdy, s.current ? s.current->seqNum : 0);
}

uint64_t
m007_clz(uint64_t pc, uint64_t a, uint64_t width)
{
    State &s = state();
    if (s.model != "IEX-M007" || pc != s.target_pc)
        return a == 0 ? width : (width - 1 - ((width == 64)
                     ? (63 - __builtin_clzll(a))
                     : (31 - __builtin_clz((uint32_t)a))));
    if (a == 0) {
        logIneligible(s, pc, "a_zero_guard", a, 0);
        return width;
    }
    uint64_t msb = (width == 64) ? (63 - __builtin_clzll(a))
                                 : (31 - __builtin_clz((uint32_t)a));
    uint64_t golden = width - 1 - msb;
    uint64_t faulty = golden + 1;
    bool first = select(s, pc);
    bool apply = first && s.fault_enabled && !s.injection_applied;
    if (apply) {
        s.injection_applied = true;
        ++s.applied_count;
    }
    if (s.observing) {
        char bdy[768];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"site\":\"Clz64::execute\","
            "\"eligible_ordinal\":%" PRIu64 ",\"applied\":%d,"
            "\"a\":\"0x%016" PRIx64 "\",\"width\":%" PRIu64 ","
            "\"msb_index\":%" PRIu64 ",\"clz_golden\":%" PRIu64 ","
            "\"clz_faulty\":%" PRIu64,
            s.current ? s.current->seqNum : 0ULL, pc,
            s.current ? s.current->threadNumber : 0,
            s.eligible_count, apply ? 1 : 0, a, width, msb, golden, faulty);
        emitFull(s, apply ? "inject" : "eligible_control", bdy,
                 s.current ? s.current->seqNum : 0);
    }
    return apply ? faulty : golden;
}

void
note_site(uint64_t pc, const char *site)
{
    State &s = state();
    if (!s.observing)
        return;
    char bdy[256];
    std::snprintf(bdy, sizeof(bdy),
                  "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                  "\"site\":\"%s\"",
                  s.current ? s.current->seqNum : 0ULL, pc, site);
    emitFull(s, "site_witness", bdy, s.current ? s.current->seqNum : 0);
}

} // namespace iex
} // namespace gem5
