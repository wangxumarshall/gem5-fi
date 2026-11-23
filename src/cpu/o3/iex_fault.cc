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
#include <vector>

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
    /* (seqNum << 8 | dest_index) -> allocation generation at ROB insert. */
    std::unordered_map<uint64_t, uint64_t> dest_gen;
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

    /* --- When-v2 timing selection / state observation --- */
    std::string timing_id;
    std::string selector_mode = "FIRST";
    uint64_t select_ordinal = 0;
    uint64_t calibrated_n = 0;
    bool timing_selected_once = false;
    bool timing_satisfied = false;
    bool selected_event = false;
    uint64_t timing_selected_ordinal = 0;
    uint64_t timing_selected_seq = 0;
    std::string selection_reason;
    std::string timing_state_json;
    uint64_t iter_pc = 0;
    uint64_t iter_init = 0;
    uint64_t iter_last_value = 0;
    bool iter_have_last = false;
    uint64_t older_branch_pc_filter = 0;
    uint64_t head_pc_filter = 0;
    /* v3 C05 context predicate: only target executions with the designed
     * older conditional branch still unresolved at the hook are eligible. */
    std::string core_id;
    uint64_t encounter_count = 0;
    uint64_t context_reject_count = 0;
    uint64_t log_candidate_ordinal = 0;
    bool timing_eligible = false;
    struct BranchRec
    {
        uint64_t pc = 0;
        uint64_t pred_npc = 0;
        bool pred_taken = false;
        bool unresolved = true;
        Tick entered = 0;
        Tick resolved_tick = 0;
    };
    std::unordered_map<uint64_t, BranchRec> branches;
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
        s.timing_id = getenv("IEX_TIMING_ID") ? getenv("IEX_TIMING_ID") : "";
        v = getenv("IEX_SELECTOR_MODE");
        if (v && *v)
            s.selector_mode = v;
        v = getenv("IEX_SELECT_ORDINAL");
        if (v && *v)
            s.select_ordinal = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_CALIBRATED_N");
        if (v && *v)
            s.calibrated_n = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_ITER_PC");
        if (v && *v)
            s.iter_pc = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_ITER_INIT");
        if (v && *v)
            s.iter_init = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_OLDER_BRANCH_PC");
        if (v && *v)
            s.older_branch_pc_filter = std::strtoull(v, nullptr, 0);
        v = getenv("IEX_HEAD_PC");
        if (v && *v)
            s.head_pc_filter = std::strtoull(v, nullptr, 0);
        s.core_id = getenv("IEX_CORE") ? getenv("IEX_CORE") : "0";

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
                    "\"target_seen\":%d,"
                    "\"timing_id\":\"%s\",\"selector_mode\":\"%s\","
                    "\"calibrated_n\":%" PRIu64 ","
                    "\"select_ordinal\":%" PRIu64 ","
                    "\"timing_satisfied\":%d,"
                    "\"timing_selected_ordinal\":%" PRIu64 ","
                    "\"timing_selected_seq\":%" PRIu64 ","
                    "\"timing_selection_reason\":\"%s\","
                    "\"timing_condition_status\":\"%s\","
                    "\"target_encounters\":%" PRIu64 ","
                    "\"context_eligible_events\":%" PRIu64 ","
                    "\"context_reject_events\":%" PRIu64 ","
                    "\"core\":\"%s\","
                    "\"trace_complete\":1}\n",
                    static_cast<uint64_t>(curTick()), s.next_event_id++,
                    s.fault_config.c_str(), s.run_id.c_str(),
                    s.sample_id.c_str(), s.pair_id.c_str(),
                    s.model.c_str(), s.context.c_str(),
                    s.fault_enabled ? 1 : 0, s.observed_count,
                    s.committed_count, s.squashed_count, s.unknown_count,
                    s.eligible_count, s.applied_count,
                    s.injection_applied ? 1 : 0, s.target_seq,
                    s.target_seen ? 1 : 0,
                    s.timing_id.c_str(), s.selector_mode.c_str(),
                    s.calibrated_n, s.select_ordinal,
                    s.timing_satisfied ? 1 : 0,
                    s.timing_selected_ordinal, s.timing_selected_seq,
                    s.selection_reason.c_str(),
                    s.selector_mode == "CENSUS" ? "CENSUS" :
                    (s.timing_satisfied ? "SATISFIED" : "CONDITION_UNMET"),
                    s.encounter_count, s.eligible_count,
                    s.context_reject_count, s.core_id.c_str());
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
                "\"timing_id\":\"%s\",\"selector_mode\":\"%s\","
                "\"select_ordinal\":%" PRIu64 ","
                "\"calibrated_n\":%" PRIu64 ","
                "\"iter_pc\":\"0x%016" PRIx64 "\","
                "\"iter_init\":%" PRIu64 ",\"core\":\"%s\","
                "\"trace_schema\":\"iex-trace-v1\"}\n",
                static_cast<uint64_t>(curTick()), s.fault_config.c_str(),
                s.run_id.c_str(), s.sample_id.c_str(), s.pair_id.c_str(),
                s.model.c_str(), s.context.c_str(), s.workload.c_str(),
                s.fault_config.c_str(), s.oracle_id.c_str(),
                s.seed.c_str(), s.gem5_commit.c_str(),
                s.fault_enabled ? 1 : 0, s.target_pc, s.consumer_pc,
                s.roi_start, s.roi_end, s.timing_id.c_str(),
                s.selector_mode.c_str(), s.select_ordinal, s.calibrated_n,
                s.iter_pc, s.iter_init, s.core_id.c_str());
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
                  "\"context\":\"%s\",\"fault_enabled\":%d,"
                  "\"timing_id\":\"%s\",\"selector_mode\":\"%s\","
                  "\"select_ordinal\":%" PRIu64 ","
                  "\"calibrated_n\":%" PRIu64 ",\"core\":\"%s\"",
                  event, static_cast<uint64_t>(curTick()), eid,
                  parentList(parents).c_str(),
                  jstr(s.fault_config).c_str(), seq,
                  jstr(s.run_id).c_str(), jstr(s.sample_id).c_str(),
                  jstr(s.pair_id).c_str(), jstr(s.model).c_str(),
                  jstr(s.context).c_str(), s.fault_enabled ? 1 : 0,
                  jstr(s.timing_id).c_str(), jstr(s.selector_mode).c_str(),
                  s.select_ordinal, s.calibrated_n, jstr(s.core_id).c_str());
    std::string line(head);
    line += ",";
    std::string full_body = body;
    if (std::strcmp(event, "candidate") == 0 ||
        std::strcmp(event, "inject") == 0 ||
        std::strcmp(event, "eligible_control") == 0)
        full_body += s.timing_state_json;
    line += full_body;
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

struct TimingSnapshot
{
    uint64_t rob_entries = 0;
    uint64_t head_seq = 0;
    uint64_t head_pc = 0;
    std::string head_opcode;
    bool head_present = false;
    bool head_executed = false;
    bool head_completed = false;
    bool head_ready = false;
    bool head_mem = false;
    bool head_load = false;
    bool head_store = false;
    bool head_blocked = false;
    std::string head_block_reason = "head_absent";
    uint64_t iq_count = 0;
    bool target_ready = false;
    bool target_issued = false;
    unsigned op_class = 0;
    uint64_t older_branch_count = 0;
    uint64_t older_branch_seq = 0;
    uint64_t older_branch_pc = 0;
    uint64_t older_branch_pred_npc = 0;
    bool older_branch_pred_taken = false;
    Tick older_branch_entered = 0;
    Tick older_branch_resolved = 0;
    uint64_t iteration = 0;
    std::string iteration_basis = "eligible_ordinal";
};

static TimingSnapshot
takeSnapshot(State &s, o3::DynInst *d)
{
    TimingSnapshot t;
    if (!d)
        return t;
    t.target_ready = d->readyToIssue();
    t.target_issued = d->isIssued();
    t.op_class = static_cast<unsigned>(d->opClass());

    if (s.iter_have_last && s.iter_init >= s.iter_last_value)
        t.iteration = s.iter_init - s.iter_last_value + 1;
    else
        t.iteration = s.eligible_count;
    if (s.iter_have_last)
        t.iteration_basis = "loop_counter";

    o3::CPU *o3cpu = dynamic_cast<o3::CPU *>(d->cpu);
    if (o3cpu) {
        o3::ROB &rob = o3cpu->o3ROB();
        t.rob_entries = rob.getThreadEntries(d->threadNumber);
        if (!rob.isEmpty(d->threadNumber)) {
            const o3::DynInstPtr &head = rob.readHeadInst(d->threadNumber);
            if (head) {
                t.head_present = true;
                t.head_seq = head->seqNum;
                t.head_pc = head->pcState().instAddr();
                t.head_opcode = head->staticInst->getName();
                t.head_executed = head->isExecuted();
                t.head_completed = head->isCompleted();
                t.head_ready = head->readyToCommit();
                t.head_mem = head->isMemRef();
                t.head_load = head->isLoad();
                t.head_store = head->isStore();
                if (head->isSquashed())
                    t.head_block_reason = "head_squashed";
                else if (!head->isExecuted())
                    t.head_block_reason = "head_not_executed";
                else if (!head->isCompleted())
                    t.head_block_reason = head->isLoad() ?
                        "long_latency_load_pending" : "head_not_completed";
                else if (!head->readyToCommit())
                    t.head_block_reason = "head_not_ready";
                else
                    t.head_block_reason = "head_ready";
            }
        }
        t.iq_count = o3cpu->o3IEW().instQueue.getCount(d->threadNumber);
    }

    for (const auto &kv : s.branches) {
        if (s.older_branch_pc_filter &&
            kv.second.pc != s.older_branch_pc_filter)
            continue;
        if (kv.first < d->seqNum && kv.second.unresolved) {
            ++t.older_branch_count;
            if (!t.older_branch_seq || kv.first < t.older_branch_seq) {
                t.older_branch_seq = kv.first;
                t.older_branch_pc = kv.second.pc;
                t.older_branch_pred_npc = kv.second.pred_npc;
                t.older_branch_pred_taken = kv.second.pred_taken;
                t.older_branch_entered = kv.second.entered;
                t.older_branch_resolved = kv.second.resolved_tick;
            }
        }
    }
    t.head_blocked = t.head_present && t.head_seq < d->seqNum &&
                     !t.head_ready;
    return t;
}

static std::string
timingStateJson(State &s, const TimingSnapshot &t, bool selected, bool cond,
                const std::string &reason)
{
    char b[4096];
    std::snprintf(
        b, sizeof(b),
        ",\"candidate_ordinal\":%" PRIu64 ",\"iteration\":%" PRIu64 ","
        "\"iteration_basis\":\"%s\",\"selected\":%d,"
        "\"condition_true\":%d,\"selection_reason\":\"%s\","
        "\"timing_satisfied_so_far\":%d,"
        "\"rob_entries\":%" PRIu64 ",\"rob_head_present\":%d,"
        "\"rob_head_seq\":%" PRIu64 ",\"rob_head_pc\":\"0x%016" PRIx64 "\","
        "\"rob_head_opcode\":\"%s\",\"rob_head_executed\":%d,"
        "\"rob_head_completed\":%d,\"rob_head_ready\":%d,"
        "\"rob_head_mem\":%d,\"rob_head_load\":%d,"
        "\"rob_head_store\":%d,\"head_blocked\":%d,"
        "\"head_block_reason\":\"%s\",\"iq_count\":%" PRIu64 ","
        "\"target_ready\":%d,\"target_issued\":%d,"
        "\"fu_class\":\"opClass\",\"op_class\":%u,"
        "\"older_unresolved_branch_count\":%" PRIu64 ","
        "\"older_unresolved_branch_seq\":%" PRIu64 ","
        "\"older_unresolved_branch_pc\":\"0x%016" PRIx64 "\","
        "\"older_unresolved_predicted_npc\":\"0x%016" PRIx64 "\","
        "\"older_unresolved_predicted_taken\":%d,"
        "\"older_unresolved_entered_tick\":%" PRIu64 ","
        "\"older_unresolved_resolved_tick\":%" PRIu64 ","
        "\"timing_eligible\":%d,\"target_encounters\":%" PRIu64 ","
        "\"speculative\":%d",
        s.log_candidate_ordinal, t.iteration, t.iteration_basis.c_str(),
        selected ? 1 : 0, cond ? 1 : 0, reason.c_str(),
        s.timing_satisfied ? 1 : 0,
        t.rob_entries, t.head_present ? 1 : 0, t.head_seq, t.head_pc,
        jstr(t.head_opcode).c_str(), t.head_executed ? 1 : 0,
        t.head_completed ? 1 : 0, t.head_ready ? 1 : 0,
        t.head_mem ? 1 : 0, t.head_load ? 1 : 0, t.head_store ? 1 : 0,
        t.head_blocked ? 1 : 0, t.head_block_reason.c_str(), t.iq_count,
        t.target_ready ? 1 : 0, t.target_issued ? 1 : 0, t.op_class,
        t.older_branch_count, t.older_branch_seq, t.older_branch_pc,
        t.older_branch_pred_npc, t.older_branch_pred_taken ? 1 : 0,
        static_cast<uint64_t>(t.older_branch_entered),
        static_cast<uint64_t>(t.older_branch_resolved),
        s.timing_eligible ? 1 : 0, s.encounter_count,
        t.older_branch_count ? 1 : 0);
    return std::string(b);
}

/* Called by every model site once the target PC matched.  The v1 model
 * guard has already passed; this function selects the When-v2 timing
 * instance and returns true only for the selected event.  Fault vs
 * Control is still the only functional difference (apply = selected &&
 * fault_enabled). */
static bool
select(State &s, uint64_t pc)
{
    if (s.current) {
        s.target_seen = true;
        if (!s.target_seq)
            s.target_seq = s.current->seqNum;
    }
    ++s.encounter_count;

    TimingSnapshot snap = takeSnapshot(s, s.current);

    bool context_ok = true;
    if (s.selector_mode == "C05_ORDINAL") {
        /* v3 C05 frozen context predicate: the designed older conditional
         * branch (PC-filtered) must be unresolved and older than target. */
        context_ok = snap.older_branch_count > 0 &&
                     snap.older_branch_seq < (s.current ? s.current->seqNum
                                                        : 0);
        if (!context_ok)
            ++s.context_reject_count;
    }

    if (context_ok)
        ++s.eligible_count;
    s.log_candidate_ordinal = context_ok ? s.eligible_count : 0;
    s.timing_eligible = context_ok;

    bool cond = false;
    bool selected = false;
    std::string reason;

    if (s.selector_mode == "CENSUS") {
        reason = "census";
    } else if (s.selector_mode == "ORDINAL") {
        cond = s.select_ordinal != 0 && s.eligible_count == s.select_ordinal;
        selected = cond;
        reason = cond ? "ordinal_match" : "ordinal_not_match";
    } else if (s.selector_mode == "C05_ORDINAL") {
        cond = context_ok && s.select_ordinal != 0 &&
               s.eligible_count == s.select_ordinal;
        selected = cond;
        reason = !context_ok ? "c05_context_unmet" :
                 (cond ? "c05_ordinal_match" : "c05_ordinal_not_match");
    } else if (s.selector_mode == "STATE_BRANCH") {
        cond = snap.older_branch_count > 0;
        selected = cond && !s.timing_selected_once;
        reason = selected ? "older_branch_unresolved" :
            (cond ? "already_selected" : "no_older_unresolved_branch");
    } else if (s.selector_mode == "STATE_ROB") {
        cond = snap.head_blocked && snap.head_mem && !snap.head_completed &&
               (!s.head_pc_filter || snap.head_pc == s.head_pc_filter);
        selected = cond && !s.timing_selected_once;
        reason = selected ? "older_head_blocked" :
            (cond ? "already_selected" : "no_older_head_block");
    } else { // FIRST (v1-compatible)
        cond = true;
        selected = !s.timing_selected_once;
        reason = selected ? "first_eligible" : "already_selected";
    }

    s.selected_event = selected;
    s.selection_reason = reason;
    s.timing_state_json = timingStateJson(s, snap, selected, cond, reason);
    if (selected) {
        s.timing_selected_once = true;
        s.timing_satisfied = true;
        s.timing_selected_ordinal = s.eligible_count;
        s.timing_selected_seq = s.current ? s.current->seqNum : 0;
    }
    (void)pc;
    return selected;
}

static const char *
eventName(const State &s, bool apply)
{
    if (apply)
        return "inject";
    return s.selected_event ? "eligible_control" : "candidate";
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
noteIssue(o3::DynInst *d)
{
    State &s = state();
    if (!s.observing || !d)
        return;
    const uint64_t pc = d->pcState().instAddr();
    if (!inRoi(s, pc))
        return;
    char bdy[512];
    std::snprintf(
        bdy, sizeof(bdy),
        "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
        "\"tid\":%d,\"opcode\":\"%s\",\"op_class\":%d,"
        "\"is_control\":%d,\"is_load\":%d,\"is_store\":%d,"
        "\"predicted_taken\":%d,\"predicted_npc\":\"0x%016" PRIx64 "\"",
        d->seqNum, pc, d->threadNumber,
        jstr(d->staticInst->getName()).c_str(),
        static_cast<int>(d->opClass()), d->isControl() ? 1 : 0,
        d->isLoad() ? 1 : 0, d->isStore() ? 1 : 0,
        d->readPredTaken() ? 1 : 0, d->readPredTarg().instAddr());
    emitFull(s, "inst_issue", bdy, d->seqNum);
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
    if (d && d->isCondCtrl()) {
        auto it = s.branches.find(d->seqNum);
        if (it != s.branches.end()) {
            it->second.unresolved = false;
            it->second.resolved_tick = curTick();
        }
    }
    endObserved(s, d);
    if (s.current == d)
        s.current = nullptr;
}

void
noteRobInsert(o3::DynInst *d)
{
    State &s = state();
    if (!d)
        return;

    /* Bind every renamed destination physical register to its producing
     * dynamic instruction at ROB insertion, before writeback.  Without
     * this, a consumer that issues before an in-flight producer writes
     * back would see the previous allocation's producer and fabricate a
     * cross-iteration dependency. */
    for (int i = 0; i < d->numDestRegs(); ++i) {
        const PhysRegIdPtr &r = d->renamedDestIdx(i);
        if (!r || r->is(InvalidRegClass))
            continue;
        const RegId &arch = d->destRegIdx(i);
        ++s.generation;
        s.dest_gen[(d->seqNum << 8) | static_cast<uint64_t>(i)] =
            s.generation;
        RegRec &rr = s.regs[regKey(r)];
        rr.producer_seq = d->seqNum;
        rr.generation = s.generation;
        rr.value = 0;
        rr.tick = curTick();
        if (s.observing) {
            char bdy[512];
            std::snprintf(
                bdy, sizeof(bdy),
                "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
                "\"tid\":%d,\"cls\":\"%s\",\"class_value\":%d,"
                "\"phys\":%u,\"flat\":%u,\"arch\":%u,\"arch_cls\":%d,"
                "\"gen\":%" PRIu64 ",\"dest_index\":%d",
                d->seqNum, d->pcState().instAddr(), d->threadNumber,
                jstr(r->className()).c_str(),
                static_cast<int>(r->classValue()),
                static_cast<unsigned>(r->index()),
                static_cast<unsigned>(r->flatIndex()),
                static_cast<unsigned>(arch.index()),
                static_cast<int>(arch.classValue()), s.generation, i);
            emitFull(s, "reg_alloc", bdy, d->seqNum);
        }
    }

    if (!d->isCondCtrl())
        return;
    State::BranchRec &b = s.branches[d->seqNum];
    b.pc = d->pcState().instAddr();
    b.pred_npc = d->readPredTarg().instAddr();
    b.pred_taken = d->readPredTaken();
    b.unresolved = true;
    b.entered = curTick();
    if (s.observing) {
        char bdy[512];
        std::snprintf(
            bdy, sizeof(bdy),
            "\"seq\":%" PRIu64 ",\"pc\":\"0x%016" PRIx64 "\","
            "\"tid\":%d,\"predicted_npc\":\"0x%016" PRIx64 "\","
            "\"predicted_taken\":%d,\"unresolved\":1",
            d->seqNum, b.pc, d->threadNumber, b.pred_npc,
            b.pred_taken ? 1 : 0);
        emitFull(s, "branch_enter_rob", bdy, d->seqNum);
    }
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
    RegRec &rr = s.regs[regKey(r)];
    auto git = s.dest_gen.find((d->seqNum << 8) |
                               static_cast<uint64_t>(idx));
    uint64_t alloc_gen =
        git == s.dest_gen.end() ? rr.generation : git->second;
    /* The allocation generation was assigned at ROB insertion.  A later
     * writeback of an older instruction must not overwrite a physical
     * register that has since been renamed to a younger producer. */
    if (rr.producer_seq == d->seqNum) {
        rr.value = val;
        rr.tick = curTick();
        rr.generation = alloc_gen;
    }
    if (s.iter_pc && it->second.pc == s.iter_pc && idx == 0 &&
        r->classValue() == IntRegClass) {
        s.iter_last_value = val;
        s.iter_have_last = true;
    }

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
        static_cast<int>(arch.classValue()), old, val, alloc_gen);
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
    for (auto it = s.branches.begin(); it != s.branches.end();) {
        if (it->first > squashed_seq && it->second.unresolved)
            it = s.branches.erase(it);
        else
            ++it;
    }
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
    bool selected = select(s, pc);
    uint64_t faulty = normal - 0x100000000ULL;
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0, a, b, c32,
            (a & 0xffffffffULL) + (b & 0xffffffffULL), normal, faulty,
            ((normal & 0xffffffffULL) == (faulty & 0xffffffffULL)) ? 1 : 0,
            normal - faulty);
        emitFull(s, eventName(s, apply), bdy,
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
    bool selected = select(s, pc);
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0, a, b, width, eff, alt, rn,
            rf);
        emitFull(s, eventName(s, apply), bdy,
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
    bool selected = select(s, pc);
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0, op1l, op1h, op2l, op2h, mid1,
            mid2, low_product_hi, result, apply ? 0ULL : result);
        emitFull(s, eventName(s, apply), bdy,
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
    bool selected = select(s, pc);
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0, a, b, apply ? 1 : 0);
        emitFull(s, eventName(s, apply), bdy,
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
    bool selected = select(s, pc);
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0,
            static_cast<unsigned>(nzcv), nz, c, v, cond, taken ? 1 : 0,
            actual ? 1 : 0, pred, target_npc, fallthrough_npc,
            taken ? target_npc : fallthrough_npc,
            actual ? target_npc : fallthrough_npc,
            pred == (taken ? target_npc : fallthrough_npc) ? 1 : 0,
            pred == (actual ? target_npc : fallthrough_npc) ? 1 : 0);
        emitFull(s, eventName(s, apply), bdy,
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
    bool selected = select(s, pc);
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0, res_temp, in, iz,
            apply ? (iz ^ 1) : iz);
        emitFull(s, eventName(s, apply), bdy,
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
    bool selected = select(s, pc);
    bool apply = selected && s.fault_enabled && !s.injection_applied;
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
            s.log_candidate_ordinal, apply ? 1 : 0, a, width, msb, golden, faulty);
        emitFull(s, eventName(s, apply), bdy,
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
