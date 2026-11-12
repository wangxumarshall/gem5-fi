// CHAOSPropagation.cc — [LSU][OBS-L3] real L3 propagation-chain tracer
// (central correction directive 2026-10-13). Four-piece SimObject family
// pattern (template: CHAOSMicroSnap/; setter-attach: CHAOSCommitTrace/).
// See CHAOSPropagation.hh for the pinned CSV contract and the v1
// registry/taint rules. Nothing here mutates CPU state: the only writes are
// to the trace file and the tracer's own registries/taint set.
//
// COMPILE-DEFERRED (source-level commit, 2026-10-13 directive): the AGU
// formal production batch is running and the guard gate forbids building;
// every C++ change in this series is verified against the
// CHAOSMicroSnap/CHAOSCommitTrace patterns item by item (see the commit
// message checklist) and compiled after the batch reaches terminal state
// (checklist in docs/gem5-fi/lsu/evidence/P4/obs_l3_propagation_design.md).

#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
#include "cpu/o3/CHAOSPropagation/chaos_tlb_chain.hh"

#include <cstdio>
#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "cpu/o3/cpu.hh"          // o3::CPU: setChaosPropagation, o3Commit()
#include "cpu/o3/dyn_inst.hh"     // DynInst: seqNum/renamedSrcIdx/destRegIdx
#include "cpu/reg_class.hh"       // RegClassType values
#include "mem/packet.hh"          // Packet: getAddr/getSize/getPtr/req
#include "params/CHAOSPropagation.hh"
#include "sim/cur_tick.hh"        // curTick()
#include "sim/sim_exit.hh"        // registerExitCallback

namespace gem5
{

    CHAOSPropagation *CHAOSPropagation::chaos_instance = nullptr;

    CHAOSPropagation::CHAOSPropagation(const CHAOSPropagationParams &p)
        : SimObject(p),
          cpu(p.cpu),
          trace_file(p.traceFile),
          write_log(p.writeLog),
          mmu_trace(p.mmuTrace),
          mmu_trace_va_lo(p.mmuTraceVaLo),
          mmu_trace_va_hi(p.mmuTraceVaHi),
          mmu_fault_enable(p.mmuFaultEnable),
          mmu_fault_model(p.mmuFaultModel),
          mmu_m01_va(p.mmuM01Va),
          mmu_m01_asid(p.mmuM01Asid),
          mmu_m01_vmid(p.mmuM01Vmid),
          mmu_m01_regime(p.mmuM01Regime),
          mmu_m01_ss(p.mmuM01SecurityState),
          mmu_m01_n(p.mmuM01N),
          mmu_m02_va(p.mmuM02Va),
          mmu_m02_old_pfn(p.mmuM02OldPfn),
          mmu_m02_xor_mask(p.mmuM02XorMask),
          mmu_m02_dram_lo(p.mmuM02DramLo),
          mmu_m02_dram_hi(p.mmuM02DramHi),
          mmu_target_va(p.mmuTargetVa),
          mmu_target_asid(p.mmuTargetAsid),
          mmu_target_vmid(p.mmuTargetVmid),
          mmu_target_n(p.mmuTargetN),
          mmu_target_regime(p.mmuTargetRegime),
          mmu_target_ss(p.mmuTargetSecurityState),
          mmu_target_instance(p.mmuTargetInstance),
          mmu_target_walk_level(p.mmuTargetWalkLevel),
          mmu_target_seq(p.mmuTargetSeq),
          mmu_target_mode(p.mmuTargetMode),
          mmu_eligible_index(p.mmuEligibleEventIndex),
          mmu_fault_persistence(p.mmuFaultPersistence),
          mmu_m03_candidate_asid(p.mmuM03CandidateAsid),
          mmu_m04_decoy_pfn(p.mmuM04DecoyPfn),
          mmu_m05_decoy_va(p.mmuM05DecoyVa),
          mmu_m05_decoy_table_base(p.mmuM05DecoyTableBase),
          mmu_m08_pa_xor_mask(p.mmuM08PaXorMask),
          addr_expiry_ticks(p.addrExpiryTicks),
          evt_trace_file(p.evtTraceFile),
          run_id(p.runId),
          sample_run_id(p.sampleRunId)
    {
        // CHAOSCache (no CPU pointer) reaches the tracer through the static
        // instance (single-core campaign; BaseCache::chaosVictimHook static
        // precedent). Last instance wins — one instance per run here.
        chaos_instance = this;

        // [MMU-TRACE v2] One-shot model state. A configured model starts
        // Idle (configured but no eligible event seen yet); no model = Off.
        // [Phase 2.2] The explicit enable switch is authoritative: a model
        // string with mmuFaultEnable=false is configured-but-disabled and
        // stays Off (no latch, no mutation).
        if (mmu_fault_enable && !mmu_fault_model.empty()) {
            mmu_fault_state = MmuFaultState::Idle;
            printf("[CHAOSPropagation] MMU fault model %s armed: "
                   "M01(va=%#llx asid=%d vmid=%d n=%u) "
                   "M02(va=%#llx old_pfn=%#llx xor=%#llx) "
                   "target(va=%#llx asid=%d vmid=%d n=%d mode=%s "
                   "instance=%s level=%d seq=%llu ordinal=%llu)\n",
                   mmu_fault_model.c_str(),
                   (unsigned long long)mmu_m01_va, mmu_m01_asid,
                   mmu_m01_vmid, mmu_m01_n,
                   (unsigned long long)mmu_m02_va,
                   (unsigned long long)mmu_m02_old_pfn,
                   (unsigned long long)mmu_m02_xor_mask,
                   (unsigned long long)mmu_target_va, mmu_target_asid,
                   mmu_target_vmid, mmu_target_n, mmu_target_mode.c_str(),
                   mmu_target_instance.c_str(), mmu_target_walk_level,
                   (unsigned long long)mmu_target_seq,
                   (unsigned long long)mmu_eligible_index);
            fflush(stdout);
        }

        if (write_log) {
            // Raw zlib gzFile at simout.resolve(trace_file) — NOT
            // simout.create's gz streambuf (that path only gzwrite()s and
            // zlib holds data until gzclose, so an aborted run loses the
            // file; CHAOSMicroSnap measured 0 bytes there). Every node
            // below is followed by gzflush(Z_SYNC_FLUSH) — the per-node
            // cost is irrelevant here (a handful of nodes per run).
            const std::string path = simout.resolve(trace_file);
            gz_file = gzopen(path.c_str(), "wb");
            if (!gz_file)
                panic("CHAOSPropagation: Could not open trace file %s",
                      path.c_str());
            const char *header =
                "# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,"
                "request_id,addr,phys_reg,arch_reg,detail\n";
            const int hlen = (int)strlen(header);
            if (gzwrite(gz_file, header, hlen) != hlen)
                panic("CHAOSPropagation: header write failed on %s",
                      path.c_str());
            gzflush(gz_file, Z_SYNC_FLUSH);

            // PROP-EVT unified stream (H0): same crash-durability contract
            // (raw gzFile + per-node Z_SYNC_FLUSH). The '#' header line
            // carries the registry; the Python parser rejects it as a
            // non-PROP-EVT line.
            const std::string epath = simout.resolve(evt_trace_file);
            evt_gz_file = gzopen(epath.c_str(), "wb");
            if (!evt_gz_file)
                panic("CHAOSPropagation: Could not open PROP-EVT file %s",
                      epath.c_str());
            std::ostringstream eh;
            eh << "# prop-evt v1:";
            for (int i = 0; i < N_PROP_EVT_FIELDS; ++i)
                eh << " " << PROP_EVT_FIELDS[i];
            // [R6] the family-extension columns are part of the row contract
            // too, so the header must list them (else the row would carry
            // keys the documented schema does not name).
            for (int i = 0; i < N_PROP_EVT_EXT_FIELDS; ++i)
                eh << " " << PROP_EVT_EXT_FIELDS[i];
            eh << "\n";
            const std::string ehs = eh.str();
            if (gzwrite(evt_gz_file, ehs.data(), (unsigned)ehs.size())
                    != (int)ehs.size())
                panic("CHAOSPropagation: PROP-EVT header write failed on %s",
                      epath.c_str());
            gzflush(evt_gz_file, Z_SYNC_FLUSH);

            // Normal-exit trailer: gzclose writes the gzip trailer. MUST be
            // an exit callback, not the destructor — gem5's exit path does
            // not reliably run SimObject destructors (CHAOSMicroSnap
            // measurement; CHAOSProbe exit-callback precedent). Aborted runs
            // never get here: they keep the Z_SYNC_FLUSH-ed truncated
            // stream, which tools/lsu_l3_propagation.py salvages.
            registerExitCallback([this]() {
                // [MDSPEC][L5] chain_end events: one per fault chain at
                // exit. The observable state (errant_commit seen or not,
                // outcome) is what gem5 alone knows; the FINAL checksum /
                // exit-code classification is the offline reclass join
                // (spec sheet 9: L5 = 检测与最终结局, joined offline).
                // outcome=unknown means "pending offline join" — the honest
                // default, never guessed (spec: 不得推断).
                if (evt_gz_file && write_log) {
                    // [MDSPEC][R6-FIXCPP/T3] Flush the consumer_summary
                    // accounting to the stream BEFORE the chain_end
                    // terminators: a real terminal / chain_end must precede
                    // the accounting, and a summary never stands in for a
                    // terminal (rules ②/⑦). Each row is written raw and
                    // Z_SYNC_FLUSH-ed like every other node.
                    for (const std::string &sl :
                             consumer_agg.flush(run_id, sample_run_id)) {
                        const std::string row = sl + "\n";
                        if (gzwrite(evt_gz_file, row.data(),
                                    (unsigned)row.size())
                                != (int)row.size())
                            panic("CHAOSPropagation: CONSUMER-SUMMARY write "
                                  "failed");
                        gzflush(evt_gz_file, Z_SYNC_FLUSH);
                    }
                    // Resource bound hit: LOUD on stdout AND in the stream,
                    // never silent. The abort path emitted every further
                    // consumer (suppressed=0), so no evidence was dropped and
                    // the run must not be read as complete (rules ⑦).
                    if (consumer_agg.resourceAborted()) {
                        const std::string ab =
                            chaos_consumer::Aggregator::resourceAbortLine(
                                consumer_agg.groupCount());
                        printf("%s\n", ab.c_str());
                        const std::string row = ab + "\n";
                        if (gzwrite(evt_gz_file, row.data(),
                                    (unsigned)row.size())
                                != (int)row.size())
                            panic("CHAOSPropagation: resource-abort marker "
                                  "write failed");
                        gzflush(evt_gz_file, Z_SYNC_FLUSH);
                    }
                    // [MDSPEC][R6-EMIT2/A7] Store chains whose fault-carrying
                    // store NEVER retired. A store taints itself at its
                    // response (noteMemResponse) and the taint is erased by
                    // its own commit (noteCommit); an entry still present at
                    // exit therefore means that store instance was squashed/
                    // discarded and never reached architectural state — a
                    // same-PC replay retires instead. That is containment by
                    // squash/replay (measured S04-F0-W5: the injected store
                    // sn:4001 never commits while a same-PC replay does, and
                    // the cell's oracle is clean). Record it explicitly so
                    // the chain closes as detected_contained instead of an
                    // Unknown terminal.
                    for (const auto &st : store_taint) {
                        const uint64_t p = st.second.ptag;
                        if (errant_ptags.count(p)
                                || containment_ptags.count(p))
                            continue;
                        containment_ptags[p] = {"L4",
                                                "store_discarded_not_retired"};
                        // [R6-A2/TERMINAL] A REAL lifecycle event, not a
                        // chain_end claim: this store's response was observed
                        // (noteMemResponse inserted the taint) and the store's
                        // own commit was NEVER observed (noteCommit erases
                        // it). That is the containment evidence the gate
                        // requires. We deliberately do NOT claim same-PC
                        // replay here (that would need per-PC commit proof).
                        notePropEvt("store_not_retired", {
                            {"fault_id", std::to_string(p)},
                            {"request_id", std::to_string(st.first)},
                            {"dyn_inst_seq",
                                std::to_string(st.second.taintor_seq)},
                            {"outcome", "contained"},
                            {"detection_layer", "L4"},
                            {"contained", "1"},
                            {"containment_layer", "L4"},
                            {"containment_reason",
                                "store_discarded_not_retired"},
                            {"state_before", "response_seen_commit_absent"},
                            {"corr", "taint_prop"},
                        });
                        emitDetectSignal("Hardware RAS", true, p,
                                         "store_discarded_not_retired");
                    }
                    for (const auto &kv : ptag_last_event) {
                        const uint64_t ptag = kv.first;
                        // [MDSPEC][R6] Per-chain evidence, not a run-global
                        // guess: the errant_commit node carries the faulting
                        // chain's own ptag, so this chain's L5 can say
                        // "the wrong value reached the architectural state"
                        // instead of falling back to the bare lifecycle
                        // marker (outcome=run_end) that the chain checker
                        // rejects as L5 evidence. Chains that did not commit
                        // errantly keep run_end — still honest.
                        const bool seen_errant = errant_ptags.count(ptag) > 0;
                        const auto cit = containment_ptags.find(ptag);
                        const bool contained = cit != containment_ptags.end();
                        // [R6] This node is a LIFECYCLE terminus, not L5
                        // evidence on its own: it never invents a detection
                        // layer. It REPORTS what the chain's own events
                        // proved — the errant commit (real L5 detection, the
                        // chain's `errant_commit` node) or the explicit
                        // containment recorded at L2 (Masked / refused /
                        // lost walk). A chain with neither stays honestly
                        // empty (no layer, outcome=run_end): a bare
                        // lifecycle marker must never be read as L5.
                        const char *outcome = seen_errant ? "errant_commit_seen"
                            : contained ? "detected_contained" : "run_end";
                        const char *layer = seen_errant ? "L5"
                            : contained ? cit->second.first.c_str() : "";
                        // [MDSPEC][R6-EMIT2/oracle] L18 contract item 3: the
                        // L5 outcome join needs the detection point. When the
                        // chain reached an errant commit we have it (pc /
                        // DynInst seq / commit ordinal / tick); a chain that
                        // never detected keeps them empty (honest — no
                        // invented values).
                        const auto dit = errant_detect.find(ptag);
                        std::string ce_pc, ce_seq, ce_commit;
                        if (dit != errant_detect.end()) {
                            std::ostringstream p;
                            p << std::hex << dit->second.pc;
                            ce_pc = p.str();
                            ce_seq = std::to_string(dit->second.dyn_seq);
                            ce_commit = std::to_string(dit->second.commit_seq);
                        }
                        notePropEvt("chain_end", {
                            {"fault_id", std::to_string(ptag)},
                            {"commit_seq", ce_commit},
                            {"pc", ce_pc},
                            {"dyn_inst_seq", ce_seq},
                            {"outcome", outcome},
                            {"detection_layer", layer},
                            {"contained", (seen_errant || contained)
                                ? "1" : "0"},
                            {"containment_layer",
                                contained ? cit->second.first : ""},
                            {"containment_reason",
                                contained ? cit->second.second : ""},
                            // [R4-4-review-I1] explicit non-join marker:
                            // the exit summary correlates nothing (the
                            // per-event corr fields carry provenance).
                            {"corr", CORR_NONE},
                        });
                    }
                }
                // [MMU-TRACE v2] Honest M01/M02 lifecycle terminus: an
                // armed-but-unconsumed M01 latch or a never-eligible M02 is
                // recorded explicitly (never silently reported as success).
                if (evt_gz_file)
                    mmuFaultExitReport();
                // [FSU][F5] Injector terminal events (e.g. the permanent
                // fault's chain_end with exposure totals) must be written
                // while the stream is still open. They run after the
                // tracer's own chain_end markers and before gzclose.
                for (auto &hook : exit_flush_hooks) {
                    if (hook)
                        hook();
                }
                if (gz_file) {
                    gzclose(gz_file);
                    gz_file = nullptr;
                }
                if (evt_gz_file) {
                    gzclose(evt_gz_file);
                    evt_gz_file = nullptr;
                }
            });
        }
    }

    CHAOSPropagation::~CHAOSPropagation()
    {
        // Backstop only (exit callback above is the primary closer).
        if (gz_file) {
            gzclose(gz_file);
            gz_file = nullptr;
        }
        if (evt_gz_file) {
            gzclose(evt_gz_file);
            evt_gz_file = nullptr;
        }
        if (chaos_instance == this)
            chaos_instance = nullptr;
    }

    void
    CHAOSPropagation::startup()
    {
        SimObject::startup();
        auto *o3 = dynamic_cast<o3::CPU *>(cpu);
        if (!o3) {
            warn("CHAOSPropagation: cpu is not an O3CPU; tracer disabled.\n");
            return;
        }
        o3cpu = o3;
        // PROP-EVT cycle field: tick / clockPeriod (integer division).
        clock_period = o3cpu->clockPeriod();
        // CHAOSCommitTrace/CHAOSMicroSnap setter pattern, both consumers:
        // (a) the CPU pointer the LSQ-side hooks (lsq.cc / lsq_unit.cc)
        //     read via cpu->chaosPropagation;
        // (b) the commit-stage pointer the commit.cc hook tests
        //     (cpu->o3Commit().setChaosPropagation — W2.1 anchor).
        o3cpu->setChaosPropagation(this);
        o3cpu->o3Commit().setChaosPropagation(this);
    }

    // ------------------------------------------------------------------ util

    uint64_t
    CHAOSPropagation::fnv1a64(const void *blob, size_t n) const
    {
        const uint8_t *p = static_cast<const uint8_t *>(blob);
        uint64_t h = 14695981039346656037ULL;  // FNV-1a 64-bit offset basis
        for (size_t i = 0; i < n; ++i) {
            h ^= p[i];
            h *= 1099511628211ULL;             // FNV-1a 64-bit prime
        }
        return h;
    }

    const char *
    CHAOSPropagation::regClassName(int class_value) const
    {
        // CHAOSCommitTrace.cc switch precedent (RegClassType values).
        switch ((RegClassType)class_value) {
          case IntRegClass:    return "int";
          case FloatRegClass:  return "float";
          case VecRegClass:    return "vec";
          case VecElemClass:   return "vecelem";
          case CCRegClass:     return "cc";
          case MatRegClass:    return "mat";
          default:             return "misc";
        }
    }

    void
    CHAOSPropagation::sweepExpired()
    {
        if (addr_expiry_ticks == 0)
            return;
        const Tick now = curTick();
        for (auto it = addr_registry.begin(); it != addr_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = addr_registry.erase(it);
            else
                ++it;
        }
        for (auto it = blk_registry.begin(); it != blk_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = blk_registry.erase(it);
            else
                ++it;
        }
        // [R6-S-FWD 2026-10-30] forwarded-load seq entries share the same
        // lifetime policy (a stale seq must never capture a recycled seq).
        for (auto it = load_fwd_registry.begin();
             it != load_fwd_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = load_fwd_registry.erase(it);
            else
                ++it;
        }
        // [MDSPEC][H5] prefetch requests share the same lifetime policy as
        // the other address registries (no expiry when addr_expiry_ticks=0).
        for (auto it = pf_registry.begin(); it != pf_registry.end(); ) {
            if (now > it->second.registered &&
                now - it->second.registered > (Tick)addr_expiry_ticks)
                it = pf_registry.erase(it);
            else
                ++it;
        }
    }

    // ------------------------------------------------------ PROP-EVT (H0)

    void
    CHAOSPropagation::parseDetail(const std::string &detail,
                                  std::map<std::string, std::string> &out)
    {
        // v1 detail contract: "k=v;k=v", no commas. Keys that match a
        // unified field name (pc/field) land directly; others are lifted by
        // the caller where the schema has a home.
        size_t pos = 0;
        while (pos < detail.size()) {
            const size_t semi = detail.find(';', pos);
            const std::string tok = detail.substr(
                pos, semi == std::string::npos ? std::string::npos : semi - pos);
            const size_t eq = tok.find('=');
            if (eq != std::string::npos)
                out[tok.substr(0, eq)] = tok.substr(eq + 1);
            if (semi == std::string::npos)
                break;
            pos = semi + 1;
        }
    }

    void
    CHAOSPropagation::emitPropEvt(const std::string &kind, uint64_t ptag,
                                  uint64_t event_id,
                                  std::map<std::string, std::string> fields,
                                  int tid)
    {
        if (!write_log || !evt_gz_file)
            return;
        // Auto fields: caller-supplied non-empty values win.
        const Tick now = curTick();
        if (fields["tick"].empty())
            fields["tick"] = std::to_string(now);
        if (fields["cycle"].empty())
            fields["cycle"] = clock_period
                ? std::to_string(now / clock_period) : std::string("0");
        if (fields["core_id"].empty())
            fields["core_id"] = std::to_string(cpu ? cpu->cpuId() : 0);
        if (tid >= 0 && fields["thread_id"].empty())
            fields["thread_id"] = std::to_string(tid);
        fields["fault_id"] = std::to_string(ptag);
        fields["event_id"] = std::to_string(event_id);
        // [MDSPEC][R6-FIXA] Request-scoped chain cursor (see .hh).  The event's
        // branch key is its own stamped request_id; an un-stamped (lifecycle)
        // event rides the chain's OWNER request (= the first stamped request of
        // this ptag, i.e. the faulting request).  A later, different request is
        // therefore a SIBLING sub-chain, never a cross-request parent edge.
        uint64_t branch_key = 0;
        {
            const std::string &reqs = fields["request_id"];
            const bool stamped = !reqs.empty() && reqs != "0";
            if (stamped) {
                branch_key = strtoull(reqs.c_str(), nullptr, 10);
                if (ptag != 0 && ptag_owner_request.find(ptag)
                        == ptag_owner_request.end()) {
                    ptag_owner_request[ptag] = branch_key;
                    // Carry the pre-owner un-stamped cursor (e.g. an un-stamped
                    // L0 inj) onto the owner's branch so the owner's first
                    // stamped event still descends from it (byte-identical to
                    // the old single cursor for a single-request chain).
                    const auto pit = ptag_branch_last.find({ptag, 0});
                    if (pit != ptag_branch_last.end())
                        ptag_branch_last[{ptag, branch_key}] = pit->second;
                }
            } else if (ptag != 0) {
                const auto oit = ptag_owner_request.find(ptag);
                branch_key = (oit == ptag_owner_request.end()) ? 0
                                                              : oit->second;
            }
        }
        // [MDSPEC][R6-FIXA2] Explicit lineage bridge.  The request-scoped
        // cursor below would leave a NEW request's first event with NO parent
        // at all — which drops the real cross-request pollution propagation
        // out of the causal graph (user ruling 2026-10-23).  Instead the new
        // request's first event is joined to the pollution source by exactly
        // one explicit `request_fork` bridge; when no real source event /
        // shared object is verifiable, NO bridge is fabricated and the event
        // keeps no parent (the chain stays honestly per-request).
        uint64_t bridge_id = 0;
        {
            const std::string &reqs0 = fields["request_id"];
            const bool stamped0 = !reqs0.empty() && reqs0 != "0"
                                  && reqs0 != "0x0";
            const auto oit = ptag_owner_request.find(ptag);
            const bool is_owner = (oit != ptag_owner_request.end()
                                   && oit->second == branch_key);
            const bool first_of_branch =
                ptag_branch_last.find({ptag, branch_key})
                    == ptag_branch_last.end();
            if (ptag != 0 && stamped0 && !is_owner && first_of_branch)
                bridge_id = emitLineageBridge(kind, ptag, branch_key,
                                              event_id, fields);
        }
        if (fields["parent_event_id"].empty()) {
            if (bridge_id) {
                fields["parent_event_id"] = std::to_string(bridge_id);
            } else {
                const auto it = ptag_branch_last.find({ptag, branch_key});
                if (it != ptag_branch_last.end() && it->second != event_id)
                    fields["parent_event_id"] = std::to_string(it->second);
            }
        }
        if (!run_id.empty() && fields["run_id"].empty())
            fields["run_id"] = run_id;
        if (!sample_run_id.empty() && fields["sample_run_id"].empty())
            fields["sample_run_id"] = sample_run_id;
        if (fields["evidence_status"].empty())
            fields["evidence_status"] = "observed";   // spec sheet 11 default
        // kind is forced — the caller cannot retype an event.
        fields["kind"] = kind;

        writePropEvtRow(fields);
        if (ptag != 0) {
            ptag_last_event[ptag] = event_id;
            // Advance the request-scoped cursor for this event's branch, so
            // the NEXT event of the same (ptag, request) descends from it.
            ptag_branch_last[{ptag, branch_key}] = event_id;
            // [R6-FIXA2] Remember the last STAMPED event of this branch with
            // the addresses it carried — the only admissible, verifiable
            // pollution source for a later lineage bridge (an un-stamped
            // lifecycle event carries no request identity and is never used).
            const std::string &rq = fields["request_id"];
            if (!rq.empty() && rq != "0") {
                auto hex = [&](const char *k) -> uint64_t {
                    const auto it = fields.find(k);
                    return (it == fields.end() || it->second.empty())
                        ? 0 : strtoull(it->second.c_str(), nullptr, 16);
                };
                ptag_branch_src[{ptag, branch_key}] =
                    LineageSrc{event_id, hex("va"), hex("pa"),
                               hex("cache_line")};
            }
        }
    }

    // [MDSPEC][R6-FIXA2] Serialize + flush one PROP-EVT row.  Shared by the
    // normal emitter and the explicit lineage-bridge emitter so the bridge is
    // byte-shaped exactly like every other event (registry order + family
    // extension columns).
    void
    CHAOSPropagation::writePropEvtRow(std::map<std::string, std::string> &fields)
    {
        std::ostringstream row;
        row << "PROP-EVT:";
        for (int i = 0; i < N_PROP_EVT_FIELDS; ++i) {
            const auto it = fields.find(PROP_EVT_FIELDS[i]);
            row << ' ' << PROP_EVT_FIELDS[i] << '='
                << (it == fields.end() ? "" : it->second);
        }
        // [R6] family-extension columns follow the shared registry (same
        // key=value shape; parser keeps them for the family that owns them).
        for (int i = 0; i < N_PROP_EVT_EXT_FIELDS; ++i) {
            const char *k = PROP_EVT_EXT_FIELDS[i];
            const auto it = fields.find(k);
            row << ' ' << k << '=' << (it == fields.end() ? "" : it->second);
        }
        row << '\n';
        const std::string s = row.str();
        if (gzwrite(evt_gz_file, s.data(), (unsigned)s.size()) != (int)s.size())
            panic("CHAOSPropagation: PROP-EVT write failed");
        gzflush(evt_gz_file, Z_SYNC_FLUSH);
    }

    // [MDSPEC][R6-FIXA2] Observation layer of a kind for the chain's unit
    // family, mirroring tools/lsu_prop_fields.KIND_LAYER (generic) and the
    // checker's T-series table.  Deliberately NOT a general table: a kind the
    // fork actually lands on must be listed, and the chain checker re-derives
    // the layer and REJECTS a bridge whose declared layer disagrees — so any
    // drift between this map and the checker is loud, never silent.
    static const char *
    bridgeLayerOf(const std::string &kind, char family)
    {
        if (family == 'T') {
            if (kind == "tlb_lookup") return "L1";
            if (kind == "tlb_pfn" || kind == "tlb_state"
                    || kind == "tlb_walk" || kind == "tlb_refill"
                    || kind == "tlb_translate" || kind == "tlb_translate_result"
                    || kind == "tlb_fault")
                return "L2";
            if (kind == "taint_reg" || kind == "consumer"
                    || kind == "errant_commit")
                return "L4";
            return "L3";            // lookup/request/cache/memory side
        }
        if (kind == "inj") return "L0";
        if (kind == "addr_form" || kind == "lsq_push"
                || kind == "cache_access")
            return "L1";
        if (kind == "mem_req" || kind == "lsq_sendfrag"
                || kind == "tlb_translate" || kind == "cache_return"
                || kind == "mshr_alloc" || kind == "mshr_merge"
                || kind == "mshr_fill" || kind == "mshr_free")
            return "L2";
        if (kind == "resp" || kind == "lq_complete" || kind == "sq_execute"
                || kind == "sq_writeback" || kind == "sq_complete"
                || kind == "cache_fill" || kind == "cache_evict"
                || kind == "cache_writeback")
            return "L3";
        if (kind == "taint_reg" || kind == "consumer"
                || kind == "errant_commit")
            return "L4";
        return "";                  // unmapped -> checker rejects it loudly
    }

    uint64_t
    CHAOSPropagation::emitLineageBridge(
        const std::string &kind, uint64_t ptag, uint64_t dest_request,
        uint64_t dest_event_id,
        const std::map<std::string, std::string> &fields)
    {
        if (!write_log || !evt_gz_file || ptag == 0)
            return 0;
        const auto oit = ptag_owner_request.find(ptag);
        if (oit == ptag_owner_request.end() || oit->second == dest_request)
            return 0;
        const uint64_t src_request = oit->second;
        // A REAL, VERIFIABLE source event is mandatory: the last request-
        // stamped event of the owner request (an un-stamped lifecycle event
        // carries no identity and is never used as a pollution source).  With
        // no such source there is NO bridge (never fabricated).
        const auto sit = ptag_branch_src.find({ptag, src_request});
        if (sit == ptag_branch_src.end() || sit->second.event_id == 0)
            return 0;               // no source -> no bridge

        // The SHARED propagation object: the registered corrupted byte range
        // that BOTH requests really address.  Requiring both sides here (not
        // only the destination) is what makes the bridge source-verifiable —
        // and it is exactly what the chain checker re-checks offline.
        auto addr_of = [&](const char *k) -> uint64_t {
            const auto it = fields.find(k);
            if (it == fields.end() || it->second.empty())
                return 0;
            return strtoull(it->second.c_str(), nullptr, 16);
        };
        LineageSrc dstsrc;
        dstsrc.va = addr_of("va");
        dstsrc.pa = addr_of("pa");
        dstsrc.line = addr_of("cache_line");
        const LineageSrc &src = sit->second;
        Addr base = 0, size = 0;
        const char *reason = nullptr;
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (e.byte_end > e.byte_begin
                    && dstsrc.touches(e.byte_begin, e.byte_end)
                    && src.touches(e.byte_begin, e.byte_end)) {
                base = e.byte_begin; size = e.byte_end - e.byte_begin;
                reason = "addr_fallback_broadcast";
                break;
            }
        }
        if (!reason) {
            for (const auto &kv : addr_registry) {
                const AddrEntry &e = kv.second;
                if (e.size && dstsrc.touches(e.base, e.base + e.size)
                        && src.touches(e.base, e.base + e.size)) {
                    base = e.base; size = e.size;
                    reason = "request_handoff";
                    break;
                }
            }
        }
        if (!reason)
            return 0;               // no verifiable object -> no bridge

        const uint64_t bridge_id = next_bridge_id++;
        const std::string layer =
            bridgeLayerOf(kind, run_id.empty() ? '\0' : run_id[0]);
        std::map<std::string, std::string> b;
        b["kind"] = "request_fork";
        b["fault_id"] = std::to_string(ptag);
        b["event_id"] = std::to_string(bridge_id);
        b["parent_event_id"] = std::to_string(src.event_id);
        b["tick"] = std::to_string(curTick());
        b["cycle"] = clock_period ? std::to_string(curTick() / clock_period)
                                  : std::string("0");
        b["core_id"] = std::to_string(cpu ? cpu->cpuId() : 0);
        if (!run_id.empty())
            b["run_id"] = run_id;
        if (!sample_run_id.empty())
            b["sample_run_id"] = sample_run_id;
        b["evidence_status"] = "observed";
        // request_id follows the registry convention: the SOURCE (old)
        // request — the bridge is the transition carrier, so the parent edge
        // (source -> bridge) stays request-consistent while (bridge -> dest)
        // is the single whitelisted transition.
        b["request_id"] = std::to_string(src_request);
        b["old_request_id"] = std::to_string(src_request);
        b["new_request_id"] = std::to_string(dest_request);
        b["source_event_id"] = std::to_string(src.event_id);
        b["dest_event_id"] = std::to_string(dest_event_id);
        const auto cit = fields.find("corr");
        b["corr"] = cit == fields.end() ? "" : cit->second;
        b["bridge_layer"] = layer;
        b["bridge_reason"] = reason;
        {
            std::ostringstream sa, ss;
            sa << std::hex << base;
            ss << std::hex << size;
            b["shared_addr"] = sa.str();
            b["shared_size"] = ss.str();
        }
        writePropEvtRow(b);
        ptag_bridge_event[{ptag, dest_request}] = bridge_id;
        return bridge_id;
    }

    uint64_t
    CHAOSPropagation::notePropEvt(
        const std::string &kind,
        const std::vector<std::pair<std::string, std::string>> &kv)
    {
        if (!write_log || !evt_gz_file)
            return 0;
        std::map<std::string, std::string> fields;
        uint64_t ptag = 0;
        for (const auto &pair : kv) {
            bool known = false;
            for (int i = 0; i < N_PROP_EVT_FIELDS; ++i) {
                if (pair.first == PROP_EVT_FIELDS[i]) {
                    known = true;
                    break;
                }
            }
            // [R6] family-extension keys (containment_layer/_reason) are
            // legitimately emitted but live outside the shared registry.
            for (int i = 0; !known && i < N_PROP_EVT_EXT_FIELDS; ++i) {
                if (pair.first == PROP_EVT_EXT_FIELDS[i])
                    known = true;
            }
            if (!known) {
                if (!evt_unknown_key_warned) {
                    warn("CHAOSPropagation: PROP-EVT unknown field '%s' "
                         "(dropped; further drops are silent)\n",
                         pair.first.c_str());
                    evt_unknown_key_warned = true;
                }
                continue;
            }
            fields[pair.first] = pair.second;
        }
        const auto fp = fields.find("fault_id");
        if (fp != fields.end() && !fp->second.empty())
            ptag = strtoull(fp->second.c_str(), nullptr, 10);
        const uint64_t eid = next_node_id++;
        emitPropEvt(kind, ptag, eid, std::move(fields), -1);
        return eid;
    }

    // ------------------------------------------------------------------ util

    // [MDSPEC][R6-EMIT2/oracle] Hardware-detector stdout signal (see .hh).
    void
    CHAOSPropagation::emitDetectSignal(const char *layer, bool contained,
                                       uint64_t ptag, const char *reason)
    {
        if (!write_log)
            return;
        // The four-value detection-layer vocabulary is
        // Hardware RAS | OS | Application | None; "None" = nothing detected
        // (an escape). Contained faults are detected by the hardware
        // (Hardware RAS). stdout, not the gz stream: a crash/abort sample
        // never reaches the exit callback, so the gz chain_end is absent —
        // this line is the oracle's only detection input in that case.
        std::cout << "CHAOS_DETECT: layer="
                  << (layer && *layer ? layer : "None")
                  << " contained=" << (contained ? 1 : 0)
                  << " tick=" << curTick()
                  << " ptag=" << ptag
                  << " reason=" << (reason && *reason ? reason : "unknown")
                  << std::endl;
    }

    void
    CHAOSPropagation::writeNode(uint64_t ptag, const char *kind,
                                uint64_t dyn_seq, bool has_seq,
                                uint64_t request_id, bool has_req_id,
                                Addr addr, bool has_addr,
                                uint64_t phys_reg, bool has_phys,
                                uint64_t arch_reg, bool has_arch,
                                const std::string &detail, const char *corr,
                                int tid)
    {
        if (!write_log || !gz_file)
            return;
        // Numeric fields without a value are EMPTY strings (pinned contract).
        std::ostringstream row;
        row << next_node_id << ',' << curTick() << ',' << ptag << ','
            << kind << ',';
        if (has_seq) row << dyn_seq;
        row << ',';
        if (has_req_id) row << request_id;
        row << ',';
        if (has_addr) row << std::hex << addr << std::dec;
        row << ',';
        if (has_phys) row << phys_reg;
        row << ',';
        if (has_arch) row << arch_reg;
        row << ',' << detail << '\n';
        const std::string s = row.str();
        if (gzwrite(gz_file, s.data(), (unsigned)s.size())
                != (int)s.size())
            panic("CHAOSPropagation: node write failed (node %llu kind %s)",
                  (unsigned long long)next_node_id, kind);
        // Crash durability (W2.1 contract): one flush per node — an aborted
        // run keeps every completed node readable (trailer-less prefix).
        gzflush(gz_file, Z_SYNC_FLUSH);

        // PROP-EVT dual-emit (H0): same event in the unified sheet-11
        // schema; event_id == this node_id (1:1 join with the v1 CSV row).
        // Funnel rows are not propagation events — no dual-emit.
        if (strcmp(kind, "funnel") != 0) {
            std::map<std::string, std::string> f;
            parseDetail(detail, f);
            // [R4-4-review-I1] every dual-emitted event carries an explicit
            // corr provenance marker (join arm, or a non-join marker saying
            // HOW it belongs to the chain). nullptr = the caller forgot —
            // warn once and emit corr= so the gap is visible, never silent.
            if (!corr && !evt_corr_missing_warned) {
                warn("CHAOSPropagation: writeNode kind '%s' dual-emitted "
                     "without a corr label (corr= written; further "
                     "occurrences are silent)\n", kind);
                evt_corr_missing_warned = true;
            }
            f["corr"] = corr ? corr : "";
            if (has_seq)
                f["dyn_inst_seq"] = std::to_string(dyn_seq);
            if (has_req_id)
                f["request_id"] = std::to_string(request_id);
            if (has_addr) {
                std::ostringstream a;
                a << std::hex << addr;
                f["va"] = a.str();
            }
            if (has_phys)
                f["phys_reg"] = std::to_string(phys_reg);
            if (has_arch)
                f["arch_reg"] = std::to_string(arch_reg);
            // detail lifts: old_addr/new_addr → before/after; block_addr →
            // cache_line; pc=/field= already land on their unified names.
            const auto oa = f.find("old_addr");
            if (oa != f.end())
                f["before"] = oa->second;
            const auto na = f.find("new_addr");
            if (na != f.end())
                f["after"] = na->second;
            const auto ba = f.find("block_addr");
            if (ba != f.end())
                f["cache_line"] = ba->second;
            emitPropEvt(kind, ptag, next_node_id, std::move(f), tid);
        }
        ++next_node_id;
    }

    // ------------------------------------------------------- registration

    uint64_t
    CHAOSPropagation::registerInjection(const char *site, uint64_t dyn_seq,
                                        Addr old_addr, Addr new_addr,
                                        bool is_load, unsigned old_size,
                                        unsigned new_size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node: the injection event (addr column = the ORIGINAL addr).
        {
            std::ostringstream d;
            d << "site=" << site << ";family=addrpath;is_load="
              << (is_load ? 1 : 0)
              << ";old_size=" << old_size << ";new_size=" << new_size
              << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr << std::dec;
            writeNode(ptag, "inj", dyn_seq, true, 0, false,
                      old_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // addr_form node: the erroneous address (addr column = NEW addr).
        {
            std::ostringstream d;
            d << "site=" << site << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr << std::dec;
            writeNode(ptag, "addr_form", dyn_seq, true, 0, false,
                      new_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // Addr registry: [new_addr, new_addr+size). size==0 (s11 lost-store
        // substitution) registers an address-only marker that never
        // range-matches — the chain then honestly stops at addr_form.
        sweepExpired();
        AddrEntry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.base = new_addr;
        e.size = new_size;
        e.registered = curTick();
        addr_registry[new_addr] = e;
        return ptag;
    }

    uint64_t
    CHAOSPropagation::registerCacheFault(Addr block_addr, int byte_offset,
                                         Addr block_size, const char *field)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the faulted block address).
        {
            std::ostringstream d;
            d << "family=cache;field=" << field
              << ";byte_offset=" << byte_offset
              << ";block_addr=" << std::hex << block_addr << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      block_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        if (byte_offset >= 0) {
            // Single faulted byte (data faults).
            sweepExpired();
            BlkEntry e;
            e.ptag = ptag;
            e.byte_begin = block_addr + (Addr)byte_offset;
            e.byte_end = e.byte_begin + 1;
            e.registered = curTick();
            blk_registry[e.byte_begin] = e;
        } else if (byte_offset == -1) {
            // Whole-block fault (data_shift rotate corrupts every byte).
            sweepExpired();
            BlkEntry e;
            e.ptag = ptag;
            e.byte_begin = block_addr;
            e.byte_end = block_addr + block_size;
            e.registered = curTick();
            blk_registry[block_addr] = e;
        }
        // byte_offset == -2 (metadata field / victim path): NO registry —
        // the chain honestly stops at the inj node (see .hh).
        return ptag;
    }

    // [MDSPEC][R4-5.1] C11 MSHR merge corruption (see .hh for the full
    // contract). Address-only registration (the labeled addr_fallback arm):
    // this site has no Request seq binding for the MSHR entry itself — the
    // seq of the merging load belongs to the response side, which joins by
    // packet-address overlap instead.
    uint64_t
    CHAOSPropagation::registerMshrMergeFault(Addr line, Addr old_addr,
                                             Addr new_addr, unsigned size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the corrupted target address; detail
        // keys old_addr/new_addr/block_addr are lifted by the writeNode
        // dual-emit into before/after/cache_line).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_merge"
              << ";old_addr=" << std::hex << old_addr
              << ";new_addr=" << new_addr
              << ";size=" << std::dec << size
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      new_addr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // faulted-byte (blk) registry: the CORRUPTED target range. The
        // fill's readout serves the block at the corrupted offset and the
        // response returns on the corrupted address, so noteMemResponse's
        // cache arm (pkt->getAddr()) fires there; the H4 mshr_merge event
        // (correlateBlock on the corrupted address, same line) and the
        // line-level mshr_fill/cache_fill/mshr_free events join by overlap.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = new_addr;
            b.byte_end = new_addr + (size ? (Addr)size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.2] C12 fill-timing offset (see .hh for the full
    // contract). Address-only registration (the labeled addr_fallback arm):
    // the fill-response site has no Request seq binding — the delayed
    // fill's consumers join by line overlap instead.
    uint64_t
    CHAOSPropagation::registerFillTimingFault(Addr line, Addr block_size,
                                              Tick arrival_tick,
                                              Tick deferred_tick,
                                              uint64_t delay_cycles)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the deferred fill's line). before/after
        // carry the faulted VALUE for this model — the fill's delivery
        // tick before/after the offset (registered fields, so the pair is
        // stream-visible on the dual-emit; delay_cycles stays in the
        // detail for the v1 CSV node and is derivable as after-before).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_fill_timing"
              << ";before=" << arrival_tick
              << ";after=" << deferred_tick
              << ";delay_cycles=" << delay_cycles
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // faulted-byte (blk) registry: the WHOLE fill line. The delayed
        // mshr_fill/cache_fill/mshr_free events (correlateBlock on the
        // line), cache_access on later lookups, and noteMemResponse's
        // cache arm (the response delivery on this very line) all join by
        // overlap — at the shifted tick, so the trace itself witnesses the
        // offset (mshr_fill.tick - inj.tick = the delay + the normal fill
        // pipeline latency).
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1 (see .hh for the
    // full contract). Address-only registration (the labeled addr_fallback
    // arm): the release-point site has no Request seq binding — later
    // events on the leaked entry's line join by overlap instead.
    uint64_t
    CHAOSPropagation::registerMshrBusyFault(Addr line, Addr block_size,
                                            uint64_t occ_before,
                                            uint64_t occ_after, bool was_full)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the leaked entry's line). before/after =
        // the occupancy pair — this model's faulted VALUE: the in-service
        // occupancy that the correct release would have left (before) vs.
        // the occupancy with the release SKIPPED (after).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_busy_leak"
              << ";before=" << occ_before
              << ";after=" << occ_after
              << ";was_full=" << (was_full ? 1 : 0)
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // model-specific mshr_busy node (the stuck occupied state itself).
        // mshr_id: the propagator's line-keyed MSHR registry id for this
        // entry — looked up, and minted when it did not exist yet (the
        // fault is registered at the release point, which may precede any
        // H4 mshr_alloc observation of this line). Deliberately NOT
        // released here (no noteMshrFree): the leak is the point.
        {
            uint64_t mid = noteMshrLookup(line);
            if (!mid)
                mid = noteMshrAlloc(line);
            std::ostringstream h;
            h << std::hex << line;
            notePropEvt("mshr_busy", {
                {"fault_id", std::to_string(ptag)},
                {"corr", CORR_ORIGIN},
                {"mshr_id", std::to_string(mid)},
                {"entry_index", std::to_string(mid)},
                {"cache_line", h.str()},
                {"field", "busy"},
                {"state_before", "should_release"},
                {"state_after", "stuck_busy"},
            });
        }
        // faulted-byte (blk) registry: the WHOLE leaked line. Later events
        // on that line (a re-miss' mshr_alloc/mshr_merge, cache_access, a
        // response delivery) join by overlap — corr=addr_fallback.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.6] C15-b MSHR capacity-arbitration fake-free (see .hh
    // for the full contract). Address-only registration (the labeled
    // addr_fallback arm): the arbitration site has no Request seq binding —
    // later events on the over-committed request's line join by overlap.
    uint64_t
    CHAOSPropagation::registerMshrArbFault(Addr line, Addr block_size,
                                           uint64_t occ_before,
                                           uint64_t occ_after,
                                           bool materialized)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the over-committed request's line).
        // before/after = the occupancy pair — this model's faulted VALUE:
        // the in-service occupancy at the fire (before) vs. at the
        // over-capacity allocation (after).
        {
            std::ostringstream d;
            d << "family=cache;field=mshr_occupancy"
              << ";before=" << occ_before
              << ";after=" << occ_after
              << ";materialized=" << (materialized ? 1 : 0)
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // model-specific mshr_arb node (the arbitration observation: the
        // arbitration genuinely ALLOWED an allocation beyond capacity).
        {
            std::ostringstream h;
            h << std::hex << line;
            notePropEvt("mshr_arb", {
                {"fault_id", std::to_string(ptag)},
                {"corr", CORR_ORIGIN},
                {"mshr_id", std::to_string(noteMshrAlloc(line))},
                {"entry_index", std::to_string(occ_after)},
                {"cache_line", h.str()},
                {"field", "capacity"},
                {"state_before", "full_blocked"},
                {"state_after", "over_commit_alloc"},
            });
        }
        // faulted-byte (blk) registry: the over-committed request's line.
        // Later events on that line (cache_access, mshr_merge/fill/free,
        // the response delivery) join by overlap — corr=addr_fallback.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill classification fault
    // (see .hh for the full contract). Address-only registration (the
    // labeled addr_fallback arm): the fill-classification site has no
    // Request seq binding — the marked line's later consumers join by
    // line overlap instead.
    uint64_t
    CHAOSPropagation::registerPfFillClassFault(Addr line, Addr block_size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (addr column = the marked line). before/after carry
        // the faulted VALUE for this model — the fill's demand/prefetch
        // classification before/after the marking (registered fields, so
        // the pair is stream-visible on the dual-emit; the string values
        // are the third per-model value type after C12's tick pair and
        // L04's seq pair — read them together with field=pf_fill_class).
        {
            std::ostringstream d;
            d << "family=prefetch;field=pf_fill_class"
              << ";before=prefetch"
              << ";after=demand"
              << ";block_addr=" << std::hex << line << std::dec;
            writeNode(ptag, "inj", 0, false, 0, false,
                      line, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // faulted-byte (blk) registry: the WHOLE marked line. cache_access
        // on later lookups, cache_fill/mshr_fill/mshr_free on refetches,
        // cache_evict on eviction, and noteMemResponse's cache arm (a
        // demand load served on this line -> resp/lq_complete/taint_reg)
        // all join by overlap, each carrying corr=addr_fallback (the
        // labeled over-approximation: a correct response on the same
        // line also joins — C11 §5.1.6 precedent; the oracle adjudicates).
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = line;
            b.byte_end = line + (block_size ? block_size : 1);
            b.registered = curTick();
            blk_registry[b.byte_begin] = b;
        }
        return ptag;
    }


    // [MDSPEC][R4-5.8] A07-b AGU-ready delay (see .hh for the full
    // contract — the late-binding design and why NO registry entry is
    // made here). inj node only; the address binding arrives with the
    // delayed instruction's EA at LSQ::pushRequest (bindAguFaultAddr).
    uint64_t
    CHAOSPropagation::registerAguReadyFault(uint64_t dyn_seq,
                                            long long lq_idx,
                                            long long sq_idx,
                                            Tick ready_tick,
                                            Tick delayed_tick,
                                            uint64_t delay_cycles,
                                            bool is_load, Addr pc,
                                            uint64_t request_id)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (dyn_seq = the delayed instruction — the fault IS its
        // ready timing). before/after carry the faulted VALUE for this
        // model: the ready tick before/after the bounded delay (the C12
        // delivery-tick precedent; value type is per-model, documented at
        // the registration point and lifted by the writeNode dual-emit).
        // delay_cycles / lq_idx / sq_idx / pc stay in the v1 detail.
        {
            std::ostringstream d;
            d << "family=addrpath;field=agu_ready_delay"
              << ";before=" << ready_tick
              << ";after=" << delayed_tick
              << ";delay_cycles=" << delay_cycles
              << ";is_load=" << (is_load ? 1 : 0)
              << ";lq_idx=" << lq_idx
              << ";sq_idx=" << sq_idx
              << ";pc=0x" << std::hex << pc << std::dec;
            // [MDSPEC][R6-A4/A07-b] A07-b (request_id != 0) additionally
            // declares the model's before/after READY STATE; the ready/
            // delayed ticks themselves ride before/after, delay_cycles is a
            // family-extension column (PROP_EVT_EXT_FIELDS). A07-a/A07-c
            // (request_id == 0) keep the detail string byte-identical.
            if (request_id)
                d << ";state_before=ready;state_after=delayed"
                  << ";ready_tick=" << ready_tick
                  << ";delayed_tick=" << delayed_tick;
            writeNode(ptag, "inj", dyn_seq, true,
                      request_id, request_id != 0,
                      0, false, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // NO registry entry: the EA does not exist at the ready point.
        // bindAguFaultAddr (called from the pushRequest PRE hook at the
        // delayed tick) binds the chain to the real address range.
        return ptag;
    }

    // [MDSPEC][R4-5.8] A07 late address binding: attach the ptag from
    // registerAguReadyFault to [addr, addr+size) bound to dyn_seq (the
    // seq-primary arm — same entry shape as registerLSQForwardFault's
    // PRIMARY, but the range is the DELAYED instruction's own access:
    // only its requests/events match, never another instruction's).
    void
    CHAOSPropagation::bindAguFaultAddr(uint64_t ptag, uint64_t dyn_seq,
                                       Addr addr, unsigned size)
    {
        if (!write_log || ptag == 0 || dyn_seq == 0)
            return;
        sweepExpired();
        AddrEntry e;
        e.ptag = ptag;
        e.dyn_seq = dyn_seq;
        e.base = addr;
        e.size = size ? size : 1;
        e.registered = curTick();
        addr_registry[addr] = e;
    }

    // [MDSPEC][R4-1] SQ store->load forwarding fault (seq-primary).
    uint64_t
    CHAOSPropagation::registerLSQForwardFault(
        uint64_t store_seq, long long sq_idx, uint64_t store_req_id,
        uint64_t load_seq, long long lq_idx, uint64_t load_req_id,
        Addr vaddr, Addr size, const char *field)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        const Addr span = size ? size : 1;

        // inj node: the consuming load's seq (the instruction whose
        // architectural state receives the corrupted data) + both sides'
        // keys in the detail for the v1 CSV.
        {
            std::ostringstream d;
            d << "family=lsqfwd;field=" << field
              << ";store_dyn_inst_seq=" << store_seq
              << ";sq_idx=" << sq_idx
              << ";store_request_id=" << store_req_id
              << ";load_dyn_inst_seq=" << load_seq
              << ";lq_idx=" << lq_idx
              << ";load_request_id=" << load_req_id
              << ";fwd_addr=" << std::hex << vaddr << std::dec;
            writeNode(ptag, "inj", load_seq, true,
                      load_req_id, load_req_id != 0,
                      vaddr, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }

        // PRIMARY: addr-registry entry bound to the producer store's
        // dyn_inst_seq. The store is definitionally still in the SQ at
        // forward time (the scan window ends at storeWBIt), so its
        // sq_writeback / sq_complete fire AFTER this registration and join
        // the chain by seq (correlateRequestBySeq).
        if (store_seq) {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = store_seq;
            e.base = vaddr;
            e.size = span;
            e.registered = curTick();
            addr_registry[vaddr] = e;
        }

        // FALLBACK (labeled, address-only): the forwarded byte range in
        // the faulted-byte registry for seq-less sites (correlateBlock /
        // noteMemResponse's cache branch). Same registration the pre-R4
        // registerCacheFault path made — now explicitly secondary.
        {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = vaddr;
            b.byte_end = vaddr + span;
            b.registered = curTick();
            blk_registry[vaddr] = b;
        }
        return ptag;
    }

    // [MDSPEC][R4-5.3] L04-b response-pairing target exchange (see .hh for
    // the ruling and the exchanged-pairing-table correlation design).
    uint64_t
    CHAOSPropagation::registerRespPairFault(
        uint64_t src_seq, long long src_lq_idx, uint64_t src_req_id,
        Addr src_va, unsigned src_size,
        uint64_t tgt_seq, long long tgt_lq_idx, uint64_t tgt_req_id,
        Addr tgt_va, unsigned tgt_size)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        const Addr src_span = src_size ? src_size : 1;
        const Addr tgt_span = tgt_size ? tgt_size : 1;

        // inj node (v1 CSV + dual-emit): dyn_inst_seq = the TARGET load (the
        // wrong consumer whose writeback materializes the fault — its
        // resp/lq_complete/taint_reg share this seq, so the L0->L1 edge
        // witness keys fault_id+dyn_inst_seq match); addr = the response's
        // own vaddr; before/after = the pairing mapping (source seq ->
        // target seq — the faulted VALUE of this model; value type is
        // per-model, interpreted with `field`, C12 tick-pair precedent).
        {
            std::ostringstream d;
            d << "family=lsqfwd;field=resp_pairing"
              << ";source_dyn_inst_seq=" << src_seq
              << ";source_lq_idx=" << src_lq_idx
              << ";source_request_id=" << src_req_id
              << ";source_va=" << std::hex << src_va
              << ";target_dyn_inst_seq=" << tgt_seq
              << ";target_lq_idx=" << tgt_lq_idx
              << ";target_request_id=" << tgt_req_id
              << ";target_va=" << tgt_va << std::dec
              << ";old_addr=" << src_seq      // lifted -> before
              << ";new_addr=" << tgt_seq;     // lifted -> after
            writeNode(ptag, "inj", tgt_seq, true,
                      tgt_req_id, tgt_req_id != 0,
                      src_va, true, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }

        // PRIMARY (seq-bound), the exchanged pairing table. Entry 1:
        // [src_va, +src_span) -> tgt_seq — half 1 joins here (the packet
        // IS src's response, noteMemResponse's inst is the target).
        {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = tgt_seq;
            e.base = src_va;
            e.size = src_span;
            e.registered = curTick();
            addr_registry[src_va] = e;
        }
        // Entry 2: [tgt_va, +tgt_span) -> src_seq — half 2 joins here (the
        // packet is tgt's response, inst is the source). Skipped on
        // address collision (one map key; the half-1 binding wins and half
        // 2 keeps no seq-bound surface — honest gap, see .hh).
        if (tgt_va != src_va) {
            sweepExpired();
            AddrEntry e2;
            e2.ptag = ptag;
            e2.dyn_seq = src_seq;
            e2.base = tgt_va;
            e2.size = tgt_span;
            e2.registered = curTick();
            addr_registry[tgt_va] = e2;
        }
        // NO blk-registry (address-only) fallback by design — L04's joins
        // are seq-bound only (the 09 sheet forbids address single-key
        // chains; stricter than the labeled-fallback minimum).
        return ptag;
    }

    // [MDSPEC][R4-5.7] S10-a StoreSet SSIT-ID 换值 (see .hh for the ruling:
    // inj node only, no correlate surface — PC-keyed predictor state).
    uint64_t
    CHAOSPropagation::registerStoreSetFault(Addr store_pc, Addr load_pc,
                                            uint64_t true_ssid,
                                            uint64_t new_ssid,
                                            size_t candidate_count)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;

        // inj node (v1 CSV + dual-emit): no seq, no addr — the faulted
        // structure is the PC-indexed SSIT mapping. pc lifts to the
        // unified pc field (the corrupted LOAD's PC — the chain's key);
        // before/after = the faulted VALUE of this model, the SSID
        // assignment (true -> substituted; both legal live store-set IDs,
        // workbook 07 实施细则). store_pc and the candidate-set size stay
        // in the detail (the workbook's "保存 source/target 及候选集合").
        {
            std::ostringstream d;
            d << "family=lsqfwd;field=ssid"
              << ";pc=" << std::hex << load_pc << std::dec
              << ";store_pc=" << std::hex << store_pc << std::dec
              << ";ssid_candidates=" << candidate_count
              << ";old_addr=" << true_ssid      // lifted -> before
              << ";new_addr=" << new_ssid;      // lifted -> after
            writeNode(ptag, "inj", 0, false, 0, false,
                      0, false, 0, false, 0, false, d.str(),
                      CORR_ORIGIN);
        }
        // NO addr/seq registry registration by design (see .hh): the
        // downstream chain members (ssit_consult / ssit_violation) are the
        // injector's own PC-keyed emissions, pf_train precedent.
        return ptag;
    }

    // [MDSPEC][R4-4] ArmTLB pfn fault (seq-primary; see .hh for the ruling
    // and the measured pre-R4-4 mis-association this replaces).
    uint64_t
    CHAOSPropagation::registerTlbFault(uint64_t req_seq, Addr va, Addr size,
                                       Addr old_pfn, Addr new_pfn,
                                       Addr old_pa, Addr new_pa,
                                       Addr pa_span, const char *mode,
                                       int entry_way, int candidate_way,
                                       uint64_t walk_id,
                                       const std::string &entry_before,
                                       const std::string &entry_after)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        const Addr span = size ? size : 1;
        // pa_span = the entry's page size (entry->size + 1 at the site);
        // pa_mask = its page mask. Fall back to 4 KiB when 0 (defensive —
        // the site always passes entry->size + 1, which is >= 0x1000).
        const Addr pa_span_eff = pa_span ? pa_span : (Addr)0x1000;
        const Addr pa_mask = pa_span_eff - 1;
        const Addr old_page = old_pa & ~pa_mask;
        const Addr new_page = new_pa & ~pa_mask;
        const bool pa_changed = new_page != old_page;

        // inj node (v1 CSV): the L0 injection. addr column = the VA whose
        // translation consumed the corrupted entry; seq columns carry the
        // in-flight request's identity ("" when unstamped).
        {
            std::ostringstream d;
            // [R6-C/GAP-1] The L0 node must say WHAT the injection changed,
            // not only name it. The faulted VALUE of the pfn model is the
            // pfn pair, and the unified emitter's documented lift is
            // old_addr/new_addr -> before/after (registerStoreSetFault /
            // registerInjection convention). Measured before this fix:
            //   kind=inj ... field=pfn_to_mapped_page before= after=
            // — an L0 that cannot say before/after is not evidence that an
            // injection happened. The pfn hex pair now rides BOTH the native
            // old_pfn/new_pfn keys and the lifted old_addr/new_addr keys.
            d << "family=tlb;field=" << mode
              << ";req_seq=" << req_seq
              << ";old_pfn=" << std::hex << old_pfn
              << ";new_pfn=" << new_pfn
              << ";old_addr=" << old_pfn
              << ";new_addr=" << new_pfn
              << ";old_pa=" << old_pa
              << ";new_pa=" << new_pa
              << ";pa_span=" << pa_span_eff
              << ";pa_changed=" << (pa_changed ? 1 : 0) << std::dec;
            writeNode(ptag, "inj", req_seq, req_seq != 0,
                      req_seq, req_seq != 0, va, true, 0, false, 0, false,
                      d.str(), CORR_ORIGIN);
        }

        // [MDSPEC][R6-FIXCPP/A] Admission is gated by the REAL physical
        // redirect verdict (chaos_chain::tlbRegistrationArms — the single
        // source of truth shared with tests/chaos_tlb_chain_containment_test.cc).
        // Pre-fix defect (measured T01-F0-W4/seed1): the seq arm opened for
        // EVERY req_seq != 0, so a fault whose corrupted pfn never redirected
        // the PA — pfn bit 56 wraps out of the 64-bit Addr, effective PA
        // unchanged, pa_changed == 0 — still captured the SAME request's later
        // CLEAN events (sq_execute/sq_writeback/resp/taint_reg) and the chain
        // simultaneously asserted "L2 contained" and "propagated to L4" (the
        // checker correctly rejected that shape with time_reversed_edge).
        // A translation that is not redirected has nothing downstream to
        // attribute: NO arm opens and the chain stops at the TLB layer.
        const chaos_chain::Arms arms =
            chaos_chain::tlbRegistrationArms(req_seq, pa_changed);

        // PRIMARY (seq-bound): the request whose translation consumed the
        // corrupted entry — its later seq-keyed events join by seq.
        if (arms.seq_primary) {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = req_seq;
            e.base = va;
            e.size = span;
            e.registered = curTick();
            addr_registry[va] = e;
        }

        // FALLBACK (labeled, address-only): the WRONG physical page, only
        // when the corrupted pfn actually redirects the PA. No VA-page
        // registration anymore (that was the pre-R4-4 mis-association
        // source: every later same-VA request joined regardless of seq).
        if (arms.addr_fallback) {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = new_page;
            b.byte_end = new_page + pa_span_eff;
            b.registered = curTick();
            blk_registry[new_page] = b;
        }

        // corr label: which arm downstream events join this chain by.
        //   seq_primary  — the seq-bound primary arm is registered
        //   addr_fallback — only the PA-page fallback exists (req_seq==0)
        //   ""           — no correlation surface at all. Two honest cases:
        //                  (a) req_seq==0 AND the PA page unchanged (the
        //                  pre-R6 contract); (b) [R6-FIXCPP/A] a Request
        //                  identity exists but the effective PA did NOT
        //                  change — the translation the MMU performs is the
        //                  CLEAN one, so there is no downstream event of THIS
        //                  fault to attribute. L1/L2 carry an empty corr
        //                  instead of a fabricated seq_primary, and the chain
        //                  honestly stops at the TLB layer (containment).
        const char *corr = arms.seq_primary ? CORR_SEQ_PRIMARY
                        : arms.addr_fallback ? CORR_ADDR_FALLBACK
                        : nullptr;

        // T-series L1: the faulted request has completed TLB lookup. The
        // snapshot preserves the selected entry's identity and every field
        // needed to explain why the translation did (or did not) change.
        // notePropEvt links parent_event_id through this ptag.
        std::ostringstream h_va, h_pfn_old, h_pfn_new, h_pa_old, h_pa_new;
        h_va << std::hex << va;
        h_pfn_old << std::hex << old_pfn;
        h_pfn_new << std::hex << new_pfn;
        h_pa_old << std::hex << old_pa;
        h_pa_new << std::hex << new_pa;
        notePropEvt("tlb_lookup", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr ? corr : ""},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"entry_index", std::to_string(entry_way)},
            {"way", std::to_string(candidate_way)},
            {"field", "post_lookup"},
            {"before", h_pfn_old.str()},
            {"after", h_pfn_new.str()},
            {"state_before", entry_before},
            {"state_after", entry_after},
        });

        // Do not guess the post-translation outcome here: permission and
        // alignment checks run later in MMU::translateMmuOn. Keep the lookup
        // evidence until that completion point reports the actual PA/Fault.
        tlb_pending[{req_seq, va}] = TlbPending{
            ptag, corr ? corr : "", walk_id, entry_way, candidate_way,
            old_pa, new_pa, entry_before, entry_after};

        // Unified L2 event (tlb_pfn): full pfn/pa old-new state. Address
        // fields are bare lowercase hex (registry convention); pfn values
        // hex; dyn_inst_seq/request_id "0" = unstamped (lsq_sendfrag
        // convention).
        notePropEvt("tlb_pfn", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr ? corr : ""},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"va", h_va.str()},
            {"pa", h_pa_new.str()},
            {"before", h_pfn_old.str()},
            {"after", h_pfn_new.str()},
            {"field", mode},
            {"state_before", h_pa_old.str()},
            {"state_after", h_pa_new.str()},
        });
        return ptag;
    }

    // [MDSPEC][R6-FIXCPP/A] Drop every correlation arm of `ptag` from both
    // registries. Called when a chain's translation completes CONTAINED
    // (effective PA unchanged / refused / lost walk) so the chain has no
    // residual mapping a later, unrelated event could join — the chain's
    // terminal state is "absorbed at the TLB layer", and a chain that is
    // closed must not also be reachable from live traffic (the exact
    // contradiction R6-FIXCPP/A removes at registration time, here closed
    // for the in-flight case). Idempotent: revoking no arms is a no-op.
    void
    CHAOSPropagation::revokeChainArms(uint64_t ptag)
    {
        if (ptag == 0)
            return;
        for (auto it = addr_registry.begin(); it != addr_registry.end(); ) {
            if (it->second.ptag == ptag)
                it = addr_registry.erase(it);
            else
                ++it;
        }
        for (auto it = blk_registry.begin(); it != blk_registry.end(); ) {
            if (it->second.ptag == ptag)
                it = blk_registry.erase(it);
            else
                ++it;
        }
    }

    void
    CHAOSPropagation::noteTlbTranslationResult(uint64_t req_seq, Addr va,
                                               bool has_pa, Addr pa,
                                               const char *fault)
    {
        if (!write_log)
            return;
        auto it = tlb_pending.find({req_seq, va});
        if (it == tlb_pending.end())
            return;
        const TlbPending pending = it->second;
        tlb_pending.erase(it); // exactly one completion per injected lookup

        const std::string fault_name = fault ? fault : "NoFault";
        const bool translation_blocked = fault_name != "NoFault";
        // A walk-family fault corrupts the walk handshake, not the entry's
        // pfn, so there is no clean-PA baseline to compare against. Report
        // the real PA/fault honestly, but never claim containment for a
        // completed walk on the strength of an unknown baseline.
        const bool pa_unchanged = has_pa && pa == pending.clean_pa;
        // [MDSPEC][R6-FIXCPP/A] the verdict itself is the shared decision
        // function (chaos_chain::translationContained), so the containment
        // rule the unit test pins is the rule that runs here.
        const bool contained = chaos_chain::translationContained(
            translation_blocked, pending.walk_fault, has_pa, pa_unchanged);
        std::ostringstream h_va, h_before, h_after;
        h_va << std::hex << va;
        // The walk family has no clean-PA baseline (the corrupted object is
        // the walk handshake, not an entry pfn). Leave the baseline EMPTY
        // rather than printing a fabricated 0 that would read as a real PA.
        if (!pending.walk_fault)
            h_before << std::hex << pending.clean_pa;
        if (has_pa)
            h_after << std::hex << pa;

        // [R6-A] The fault name rides `outcome` (the tlb_fault convention)
        // and the outcome reason rides `field`. Both are registry fields;
        // notePropEvt DROPS any key outside the emittable registry, so a
        // bespoke `fault=`/`detail=` key would be silently lost from the
        // stream (measured: the L2 Fault and the reason were invisible to
        // the pilot's chain checker before this fix).
        const char *field_reason = translation_blocked
            ? "translation_blocked"
            : pending.walk_fault ? "walk_result_reported"
            : pa_unchanged ? "effective_pa_unchanged"
                           : "effective_pa_changed";

        // [R6] A contained translation is the Masked case: the injected
        // fault was absorbed (effective PA unchanged), refused
        // (permission/alignment fault) or its walk never arrived. Record
        // WHERE (L2) and WHY explicitly, and remember it per chain so the
        // terminus can justify every later layer as N/A(contained) instead
        // of leaving the chain at an unresolvable terminal state.
        const char *reason = contained ? field_reason : "";
        if (contained) {
            containment_ptags[pending.ptag] = {"L2", reason};
            // [MDSPEC][R6-FIXCPP/A] Containment REVOCATION. Whatever
            // correlation arm this chain opened at registration is dropped
            // now: its terminal state is "absorbed at L2", so a residual
            // mapping would let a LATER event join a chain that is already
            // closed — the same "contained AND propagated" contradiction the
            // registration gate closes, merely relocated in time. This is
            // unconditional (idempotent: revoking no arm is a no-op) and it
            // covers the blocked-translation case (permission/alignment
            // fault) as well as the unchanged-PA case, including the labeled
            // addr_fallback page arm a seq-less lookup may have opened.
            revokeChainArms(pending.ptag);
            // [MDSPEC][R6-EMIT2/oracle] the translation absorbed the fault
            // (effective PA unchanged / refused / lost walk): hardware
            // detection + containment → stdout signal.
            emitDetectSignal("Hardware RAS", true, pending.ptag,
                             reason && *reason ? reason : field_reason);
        }

        // [R6-FIXCORR 2026-10-25] A CONTAINED translation is the chain's real
        // terminus. When the effective PA did not change, registerTlbFault
        // deliberately opens no correlation arm (comment block above: "the
        // chain honestly stops at the TLB layer (containment)"), so
        // pending.corr is empty — and the terminus inherited that emptiness.
        // The chain checker accepts explicit containment only from a REAL
        // detection event (chaos::chain::_explicit_l5: non-lifecycle kind +
        // detection_layer + outcome + a chain-correlation `corr`), so a
        // legitimate L2 containment could never be certified.
        //
        // The event already belongs to the original injection through its
        // real parent_event_id ancestry (notePropEvt links it through ptag);
        // labelling it `origin` states exactly that and invents nothing:
        //  * no registry arm is re-opened (revokeChainArms above already
        //    dropped every arm for this ptag);
        //  * no later L3/L4/L5 event can join (there is no open arm to join);
        //  * chain_end keeps corr=none and still cannot serve as the terminus.
        // Non-contained events keep whatever corr they had (empty stays
        // empty) — only the containment terminus is labelled.
        const char *evt_corr = (contained && pending.corr.empty())
            ? CORR_ORIGIN : pending.corr.c_str();

        notePropEvt("tlb_translate_result", {
            {"fault_id", std::to_string(pending.ptag)},
            {"corr", evt_corr},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"walk_id", std::to_string(pending.walk_id)},
            {"va", h_va.str()},
            {"pa", h_after.str()},
            {"entry_index", std::to_string(pending.entry_way)},
            {"way", std::to_string(pending.candidate_way)},
            {"field", field_reason},
            {"before", h_before.str()},
            {"after", h_after.str()},
            {"state_before", pending.entry_before},
            {"state_after", pending.entry_after},
            {"outcome", fault_name},
            {"detection_layer", contained ? "L2" : ""},
            {"contained", contained ? "1" : "0"},
            {"containment_layer", contained ? "L2" : ""},
            {"containment_reason", reason},
        });
    }

    // [MDSPEC][R4-5.9] T08 walk/fill pairing. Two PROP-EVT nodes for ONE
    // [MDSPEC][R4-10-T05/T06/T07] TLB entry-state / attribute fault. One L0
    // `inj` anchor + one L2 `tlb_state` node. The pfn/PA are not the fault
    // surface here (the mutated field is valid/global/asid/ap/mtype/page-size),
    // so the node carries field + state_before/state_after text instead of the
    // tlb_pfn before/after-pfn payload. corr = seq_primary when the in-flight
    // request is published (the request's later seq-keyed events join by seq);
    // else "" — no correlation surface, the chain honestly stops here (mirrors
    // registerTlbFault's no-surface arm; NO PA-page fallback is invented
    // because this fault does not change the PA).
    uint64_t
    CHAOSPropagation::registerTlbStateFault(uint64_t req_seq, Addr va, Addr size,
                                            const char *field,
                                            const std::string &before,
                                            const std::string &after,
                                            Addr old_pa, Addr new_pa,
                                            int entry_way, int candidate_way,
                                            uint64_t walk_id,
                                            const std::string &entry_before,
                                            const std::string &entry_after,
                                            Addr pa_span)
    {
        if (!write_log)
            return 0;
        (void)size;
        const uint64_t ptag = ++next_ptag;

        // [R6-V4-T07CHAIN] A state/CAM fault that REDIRECTS the effective PA
        // (false_hit fabrizing a hit on a miss: no clean baseline ⇒ forged
        // PA) must open the same correlation arms as the pfn model; otherwise
        // no L3+ event can ever join and the chain is unopenable BY
        // CONSTRUCTION. Measured (T07-F0-W4 seed1, frozen 20fda699…): 5
        // events, open at L2, no lsq_sendfrag/mem_req/resp ever correlated.
        // A PA-neutral state fault (T05/T06 valid_clear / perm_subst) has
        // pa_changed=false ⇒ tlbRegistrationArms opens NOTHING, exactly as
        // before — its honest L2 containment is unchanged.
        const Addr pa_span_eff = pa_span ? pa_span : (Addr)0x1000;
        const Addr pa_mask = pa_span_eff - 1;
        const Addr old_page = old_pa & ~pa_mask;
        const Addr new_page = new_pa & ~pa_mask;
        const bool pa_changed = new_page != old_page;

        std::ostringstream d_inj;
        d_inj << "family=tlb;field=" << field << ";req_seq=" << req_seq
              << ";state_before=" << before << ";state_after=" << after
              << ";pa_span=" << pa_span_eff
              << ";pa_changed=" << (pa_changed ? 1 : 0);
        notePropEvt("inj", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"field", field},
            // [R6-C/GAP-1] L0 must record WHAT changed, not only what was
            // injected. The faulted VALUE of the T05/T06/T07 state model is
            // the mutated entry field: `before`/`after` are that field's
            // text before/after the mutation (the injector computed them at
            // the site). Measured before this fix: before= after=.
            {"before", before},
            {"after", after},
            {"evidence_status", "observed"},
            {"detail", d_inj.str()},
        });

        std::ostringstream h_va;
        h_va << std::hex << va;
        const char *corr = req_seq ? CORR_SEQ_PRIMARY : "";
        notePropEvt("tlb_lookup", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"entry_index", std::to_string(entry_way)},
            {"way", std::to_string(candidate_way)},
            {"field", "post_lookup"},
            {"before", before},
            {"after", after},
            {"state_before", entry_before},
            {"state_after", entry_after},
        });
        notePropEvt("tlb_state", {
            {"fault_id", std::to_string(ptag)},
            {"corr", corr},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"va", h_va.str()},
            {"field", field},
            {"state_before", before},
            {"state_after", after},
        });
        tlb_pending[{req_seq, va}] = TlbPending{
            ptag, corr, walk_id, entry_way, candidate_way,
            old_pa, new_pa, entry_before, entry_after};

        // [R6-V4-T07CHAIN] Open the correlation arm(s) IFF the effective PA
        // actually redirects. PA-neutral state faults (T05/T06) fall through
        // with no arm — unchanged behaviour. A fabricated hit (T07) redirects
        // 0 (or another page) → forged page, so the in-flight request's own
        // L3 events (lsq_sendfrag/mem_req/resp, correlated by seq) and any
        // access to the forged page can join, making the chain observable and
        // the oracle verdict attributable.
        const chaos_chain::Arms arms =
            chaos_chain::tlbRegistrationArms(req_seq, pa_changed);
        if (arms.seq_primary) {
            sweepExpired();
            AddrEntry e;
            e.ptag = ptag;
            e.dyn_seq = req_seq;
            e.base = va;
            e.size = size ? size : 1;
            e.registered = curTick();
            addr_registry[va] = e;
        }
        if (arms.addr_fallback) {
            sweepExpired();
            BlkEntry b;
            b.ptag = ptag;
            b.byte_begin = new_page;
            b.byte_end = new_page + pa_span_eff;
            b.registered = curTick();
            blk_registry[new_page] = b;
        }
        return ptag;
    }

    // walk, sharing walk_id (the pairing key) and ptag (the chain binding):
    //   tlb_walk   — tick = the walk's ISSUE tick (walker entry)
    //   tlb_refill — tick = the refill completion tick; field=lost and
    //                outcome=lost when the refill never arrived (T08-a)
    // The walk_id equality + the two distinct ticks are the pairing
    // evidence; a lost refill is recorded explicitly, never fabricated.
    uint64_t
    CHAOSPropagation::registerTlbWalkPair(uint64_t walk_id, Addr va,
                                          uint64_t req_seq,
                                          uint64_t walk_start_tick,
                                          uint64_t refill_tick,
                                          unsigned level, bool fill_lost,
                                          const char *mode)
    {
        if (!write_log)
            return 0;
        const uint64_t ptag = ++next_ptag;
        std::ostringstream h_va;
        h_va << std::hex << va;

        // [R4-6-T08] L0 anchor for the walk-issue model. The T08 drop IS an
        // injection performed at the page-table walk-issue decision point, so
        // the stream must carry its L0 node. Without it the local chain has no
        // L0 event at all and the chain checker can only report
        // no_l0_fault_applied even though tlb_walk/tlb_refill are in the
        // stream (measured on the R4-6 T08-F0-W9 pilot). Emitted first so the
        // event order is inj -> tlb_walk -> tlb_refill; part of the same
        // fault_id/ptag, so existing joins are unaffected.
        std::ostringstream d_inj;
        d_inj << "family=tlb;site=arm_tlb_walk_issue_drop;field=" << mode
              << ";walk_id=" << walk_id << ";level=L" << level
              << ";req_seq=" << req_seq;
        notePropEvt("inj", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"field", mode},
            // [R6-C/GAP-1] L0 before/after for the walk-issue model: the
            // faulted VALUE is the walk handshake itself — the correct
            // machine issues the walk (before=walk_issued), the corrupted
            // handshake is named by the injector's own mode (after=<mode>,
            // e.g. walk_fill_dup / walk_done_early / walk_stale_result).
            // Measured before this fix: before= after=.
            {"before", "walk_issued"},
            {"after", mode},
            {"evidence_status", "observed"},
            {"detail", d_inj.str()},
        });

        // The walk family starts from a real post-lookup miss. There is no
        // selected entry/way yet, so preserve that absence explicitly.
        notePropEvt("tlb_lookup", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"entry_index", "-1"},
            {"way", "-1"},
            {"field", "post_lookup"},
            {"state_before", "entry=miss"},
            {"state_after", "entry=miss"},
            {"outcome", "miss"},
        });

        std::ostringstream d_walk;
        d_walk << "family=tlb;site=tlb_walk;walk_id=" << walk_id
               << ";level=L" << level << ";start_tick=" << walk_start_tick
               << ";req_seq=" << req_seq;
        notePropEvt("tlb_walk", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"dyn_inst_seq", std::to_string(req_seq)},
            {"request_id", std::to_string(req_seq)},
            {"tick", std::to_string(walk_start_tick)},
            {"field", mode},
        });

        // The refill node. field=lost marks the T08-a lost-refill outcome
        // (the refill that never arrived) so downstream joins can prove the
        // walk was unpaired rather than silently absent. [R4-10] the T08-b/c/d
        // sub-models label their outcome explicitly (duplicated / early_done /
        // stale) instead of a bare "refilled", so the pairing is self-describing.
        const std::string mode_s(mode);
        const char *refill_outcome =
            fill_lost ? "lost"
                      : (mode_s == "walk_fill_dup" ? "duplicated"
                         : mode_s == "walk_done_early" ? "early_done"
                         : mode_s == "walk_stale_result" ? "stale"
                                                         : "refilled");
        const char *refill_field = fill_lost ? "lost" : mode;
        std::ostringstream d_refill;
        d_refill << "family=tlb;site=tlb_refill;walk_id=" << walk_id
                 << ";level=L" << level
                 << ";outcome=" << refill_outcome
                 << ";refill_tick=" << refill_tick
                 << ";req_seq=" << req_seq;
        notePropEvt("tlb_refill", {
            {"fault_id", std::to_string(ptag)},
            {"corr", CORR_ORIGIN},
            {"walk_id", std::to_string(walk_id)},
            {"va", h_va.str()},
            {"field", refill_field},
            {"outcome", refill_outcome},
            {"tick", std::to_string(refill_tick)},
        });
        if (fill_lost) {
            // No MMU completion callback can occur after the walk is dropped;
            // close the DAG here with an observed translation block. The
            // reason rides `field` and the outcome rides `outcome` (both
            // registry fields) — a bespoke detail=/fault= key would be
            // dropped by notePropEvt before it ever reached the stream.
            notePropEvt("tlb_translate_result", {
                {"fault_id", std::to_string(ptag)},
                {"corr", CORR_ORIGIN},
                {"walk_id", std::to_string(walk_id)},
                {"va", h_va.str()},
                {"dyn_inst_seq", std::to_string(req_seq)},
                {"request_id", std::to_string(req_seq)},
                {"entry_index", "-1"},
                {"way", "-1"},
                {"field", "walk_refill_lost"},
                {"pa", ""},
                // No entry was ever selected and no PA was materialised: the
                // payload carries the honest empty baseline (same shape as
                // the MMU-completion L2 node) instead of omitting the keys.
                {"before", ""},
                {"after", ""},
                {"state_before", "entry=miss"},
                {"state_after", "entry=miss"},
                {"outcome", "translation_blocked"},
                {"detection_layer", "L2"},
                {"contained", "1"},
            });
        } else {
            // [R6-B/T08-bcd] The walk completed (duplicated / done-early /
            // stale result): the requesting translation still completes in
            // the MMU, so register the pending lookup exactly like the
            // pfn/state faults. The real L2 node (effective PA + Fault) is
            // then emitted by noteTlbTranslationResult at that completion.
            // Without this, the T08-b/c/d chain had no real-PA L2 node.
            tlb_pending[{req_seq, va}] = TlbPending{
                ptag, CORR_ORIGIN, walk_id, -1, -1, 0, 0,
                "entry=miss", "entry=miss", /*walk_fault=*/true};
        }
        return ptag;
    }

    void
    CHAOSPropagation::noteFunnel(const char *site, uint64_t attempted,
                                 uint64_t eligible, uint64_t injected)
    {
        if (!write_log)
            return;
        std::ostringstream d;
        d << "site=" << site << ";attempted=" << attempted
          << ";eligible=" << eligible << ";injected=" << injected;
        // ptag=0: funnel rows are not bound to one chain.
        writeNode(0, "funnel", 0, false, 0, false, 0, false,
                  0, false, 0, false, d.str());
    }

    // ------------------------------------------------------------ pipeline

    uint64_t
    CHAOSPropagation::correlateRequest(uint64_t dyn_seq, Addr addr,
                                       Addr size, const char **corr_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + size;
        // addrpath registry: range overlap + dyn-inst binding (same
        // semantics as noteMemRequest's stamped path). Seq-bound arm.
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.size == 0)
                continue;
            if (addr < e.base + e.size && e.base < a_end
                    && e.dyn_seq == dyn_seq) {
                if (corr_out)
                    *corr_out = CORR_SEQ_PRIMARY;
                return e.ptag;
            }
        }
        // cache faulted-byte registry: range overlap (SE vaddr==paddr).
        // Address-only arm: the labeled fallback ([R4-1-review-I1]).
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (addr < e.byte_end && e.byte_begin < a_end) {
                if (corr_out)
                    *corr_out = CORR_ADDR_FALLBACK;
                return e.ptag;
            }
        }
        return 0;
    }

    void
    CHAOSPropagation::noteStoreRequestSuppressed(uint64_t dyn_seq, Addr addr,
                                                 unsigned old_size)
    {
        if (!write_log)
            return;
        Addr base = addr;
        const char *corr = nullptr;
        const uint64_t ptag = correlateRequestBySeq(dyn_seq, &base, &corr);
        if (!ptag)
            return;
        std::ostringstream h;
        h << std::hex << base;
        notePropEvt("request_suppressed", {
            {"fault_id", std::to_string(ptag)},
            {"dyn_inst_seq", std::to_string(dyn_seq)},
            {"va", h.str()},
            {"field", "request_suppressed:empty_byte_enable"},
            {"before", std::to_string(old_size)},
            {"after", "0"},
            {"state_before", "byte_enable_empty"},
            {"corr", corr ? corr : CORR_SEQ_PRIMARY},
        });
    }

    void
    CHAOSPropagation::noteStoreLostContained(uint64_t dyn_seq, Addr addr)
    {
        if (!write_log)
            return;
        if (store_lost_contained.count(dyn_seq))
            return;
        Addr base = addr;
        const char *corr = nullptr;
        const uint64_t ptag = correlateRequestBySeq(dyn_seq, &base, &corr);
        if (!ptag)
            return;
        store_lost_contained.insert(dyn_seq);
        std::ostringstream h;
        h << std::hex << base;
        notePropEvt("store_lost_contained", {
            {"fault_id", std::to_string(ptag)},
            {"dyn_inst_seq", std::to_string(dyn_seq)},
            {"va", h.str()},
            {"field", "store_completed_without_mem_request"},
            {"state_after", "completed_no_request"},
            {"detection_layer", "L3"},
            {"contained", "1"},
            {"outcome", "contained"},
            {"containment_layer", "L3"},
            {"containment_reason", "store_lost_before_request_formation"},
            {"corr", corr ? corr : CORR_SEQ_PRIMARY},
        });
    }

    void
    CHAOSPropagation::noteArchTranslationFault(Addr va, bool delivered)
    {
        if (!write_log)
            return;
        uint64_t ptag = 0;
        const char *corr = nullptr;
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.size != 0 && va >= e.base && va < e.base + e.size) {
                ptag = e.ptag;
                corr = CORR_SEQ_PRIMARY;
                break;
            }
        }
        if (!ptag) {
            for (const auto &kv : blk_registry) {
                const BlkEntry &e = kv.second;
                if (va >= e.byte_begin && va < e.byte_end) {
                    ptag = e.ptag;
                    corr = CORR_ADDR_FALLBACK;
                    break;
                }
            }
        }
        if (!ptag)
            return;   // no injected chain owns this address: stay honest
        std::ostringstream h_va;
        h_va << std::hex << va;
        notePropEvt("arch_translation_fault", {
            {"fault_id", std::to_string(ptag)},
            {"va", h_va.str()},
            {"exc_type", "page_table"},
            {"delivered", delivered ? "1" : "0"},
            {"outcome", "arch_exception"},
            {"detection_layer", "L2"},
            {"contained", delivered ? "1" : "0"},
            {"containment_layer", delivered ? "L2" : ""},
            {"containment_reason", delivered
                ? "arch_translation_fault_delivered" : ""},
            {"corr", corr ? corr : ""},
        });
    }

    void
    CHAOSPropagation::noteSquashDiscarded(o3::DynInst *inst, bool is_load,
                                          const char *state_before)
    {
        if (!write_log || !inst)
            return;
        Addr base = 0;
        const char *corr = nullptr;
        const uint64_t ptag = correlateRequestBySeq(inst->seqNum, &base, &corr);
        if (!ptag)
            return;   // instruction carries no injected fault
        notePropEvt("squash_discarded", {
            {"fault_id", std::to_string(ptag)},
            {"dyn_inst_seq", std::to_string(inst->seqNum)},
            {"request_id", std::to_string(inst->seqNum)},
            {"field", is_load ? "load" : "store"},
            {"state_before", state_before ? state_before : ""},
            {"outcome", "contained"},
            {"detection_layer", "L4"},
            {"contained", "1"},
            {"containment_layer", "L4"},
            {"containment_reason", "squash_discarded"},
            {"corr", corr ? corr : ""},
        });
        // [R6-S-FWD 2026-10-30] A FORWARDED load's squashed result is
        // discarded and replayed: drop the taint it established and its seq
        // registration so the replay can never inherit a stale chain. Gated
        // strictly on the forwarded-load registry so addrpath/cache semantics
        // stay byte-identical (their taint handling is untouched).
        if (load_fwd_registry.find(inst->seqNum)
                != load_fwd_registry.end()) {
            for (auto it = taint_set.begin(); it != taint_set.end(); ) {
                if (it->second.ptag == ptag &&
                    it->second.taintor_seq == inst->seqNum)
                    it = taint_set.erase(it);
                else
                    ++it;
            }
            load_fwd_registry.erase(inst->seqNum);
        }
    }

    uint64_t
    CHAOSPropagation::correlateRequestBySeq(uint64_t dyn_seq,
                                            Addr *base_out,
                                            const char **corr_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.dyn_seq == dyn_seq) {
                if (base_out)
                    *base_out = e.base;
                if (corr_out)
                    *corr_out = CORR_SEQ_PRIMARY;
                return e.ptag;
            }
        }
        // [R6-S-FWD 2026-10-30] A forwarded load has no memory response; its
        // only seq-bound surface is the dedicated forwarded-load registry
        // written at the forward site. Join by the LOAD's own seq.
        const auto fit = load_fwd_registry.find(dyn_seq);
        if (fit != load_fwd_registry.end()) {
            if (base_out)
                *base_out = fit->second.base;
            if (corr_out)
                *corr_out = CORR_SEQ_PRIMARY;
            return fit->second.ptag;
        }
        return 0;
    }

    uint64_t
    CHAOSPropagation::correlateBlock(Addr addr, Addr size, Addr *base_out,
                                     const char **corr_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + size;
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (addr < e.byte_end && e.byte_begin < a_end) {
                if (base_out)
                    *base_out = e.byte_begin;
                if (corr_out)
                    *corr_out = CORR_ADDR_FALLBACK;
                return e.ptag;
            }
        }
        return 0;
    }

    // ------------------------------------------------ prefetch request id (H5)
    uint64_t
    CHAOSPropagation::notePrefetchRequest(Addr addr, Addr size)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr base = addr & ~(Addr)(size ? size - 1 : 0);
        const uint64_t pfid = PF_ID_BASE + (++next_pf_request_id);
        PfEntry e;
        e.pf_request_id = pfid;
        e.base = base;
        e.size = size;
        e.registered = curTick();
        pf_registry[base] = e;
        return pfid;
    }

    void
    CHAOSPropagation::registerPtagPrefetch(uint64_t pfid, Addr addr, Addr size)
    {
        if (!write_log || pfid < PF_ID_BASE || size == 0)
            return;
        sweepExpired();
        const Addr base = addr & ~(Addr)(size - 1);
        PfEntry e;
        e.pf_request_id = pfid;
        e.base = base;
        e.size = size;
        e.registered = curTick();
        pf_registry[base] = e;
    }

    uint64_t
    CHAOSPropagation::prefetchRequestId(Addr addr, Addr size, Addr *base_out)
    {
        if (!write_log)
            return 0;
        sweepExpired();
        const Addr a_end = addr + (size ? size : 1);
        for (const auto &kv : pf_registry) {
            const PfEntry &e = kv.second;
            const Addr e_end = e.base + (e.size ? e.size : 1);
            if (addr < e_end && e.base < a_end) {
                if (base_out)
                    *base_out = e.base;
                return e.pf_request_id;
            }
        }
        return 0;
    }

    // ------------------------------------------------- MSHR lifecycle (H4)
    uint64_t
    CHAOSPropagation::noteMshrAlloc(Addr line)
    {
        if (!write_log)
            return 0;
        const uint64_t id = ++next_mshr_id;
        mshr_registry[line] = id;
        return id;
    }

    uint64_t
    CHAOSPropagation::noteMshrLookup(Addr line)
    {
        if (!write_log)
            return 0;
        const auto it = mshr_registry.find(line);
        return it == mshr_registry.end() ? 0 : it->second;
    }

    uint64_t
    CHAOSPropagation::noteMshrFree(Addr line)
    {
        if (!write_log)
            return 0;
        const auto it = mshr_registry.find(line);
        if (it == mshr_registry.end())
            return 0;
        const uint64_t id = it->second;
        mshr_registry.erase(it);
        return id;
    }

    uint64_t
    CHAOSPropagation::noteFill(Addr line)
    {
        (void)line;                    // reserved for per-line fill accounting
        if (!write_log)
            return 0;
        return ++next_fill_id;
    }

    void
    CHAOSPropagation::registerPtagBlock(uint64_t ptag, Addr byte_begin,
                                        Addr byte_end)
    {
        if (!write_log || ptag == 0 || byte_end <= byte_begin)
            return;
        sweepExpired();
        BlkEntry e;
        e.ptag = ptag;
        e.byte_begin = byte_begin;
        e.byte_end = byte_end;
        e.registered = curTick();
        blk_registry[byte_begin] = e;
    }

    uint64_t
    CHAOSPropagation::noteMemRequest(const char *site, uint64_t dyn_seq,
                                     const RequestPtr &req,
                                     const char **corr_out)
    {
        if (!write_log || !req || !req->hasVaddr())
            return 0;
        sweepExpired();
        const Addr v = req->getVaddr();
        const Addr v_end = v + (Addr)req->getSize();

        // addrpath registry: range overlap + dyn-inst binding. The request
        // seq must be stamped (getReqInstSeqNum asserts otherwise — gem5
        // v25 request.hh); an unstamped request falls back to overlap-only
        // (documented: split _mainReq is not seq-stamped).
        const bool stamped = req->hasInstSeqNum();
        const uint64_t req_seq = stamped ? req->getReqInstSeqNum() : 0;
        uint64_t matched = 0;
        for (const auto &kv : addr_registry) {
            const AddrEntry &e = kv.second;
            if (e.size == 0)
                continue;                       // address-only marker
            const Addr e_end = e.base + e.size;
            if (v >= e_end || e.base >= v_end)
                continue;                       // no overlap
            if (stamped && req_seq != e.dyn_seq)
                continue;                       // not the faulting inst
            if (corr_out && !*corr_out)
                *corr_out = CORR_SEQ_PRIMARY;   // seq-bound arm
            std::ostringstream d;
            d << "site=" << site << ";family=addrpath;size="
              << req->getSize();
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      req_seq, stamped, v, true, 0, false, 0, false, d.str(),
                      CORR_SEQ_PRIMARY);
            if (!matched)
                matched = e.ptag;
        }

        // cache faulted-byte registry: range overlap (SE vaddr==paddr).
        // Address-only arm: the labeled fallback ([R4-1-review-I1]).
        for (const auto &kv : blk_registry) {
            const BlkEntry &e = kv.second;
            if (v >= e.byte_end || e.byte_begin >= v_end)
                continue;
            if (corr_out && !*corr_out)
                *corr_out = CORR_ADDR_FALLBACK;
            std::ostringstream d;
            d << "site=" << site << ";family=cache;size=" << req->getSize();
            writeNode(e.ptag, "mem_req", dyn_seq, true,
                      req_seq, stamped, v, true, 0, false, 0, false, d.str(),
                      CORR_ADDR_FALLBACK);
            if (!matched)
                matched = e.ptag;
        }
        // [MDSPEC][H1] first matched chain id for the unified lsq_sendfrag
        // event emitted by the caller (lsq.cc sendFragmentToTranslation).
        return matched;
    }

    void
    CHAOSPropagation::noteMemResponse(o3::DynInst *inst, Packet *pkt,
                                      bool wb_to_reg)
    {
        if (!write_log || !inst || !pkt)
            return;
        sweepExpired();

        uint64_t hit_ptag = 0;
        const char *hit_family = nullptr;
        const char *hit_corr = nullptr;   // [R4-1-review-I1] matched arm

        // addrpath: the response's own Request vaddr range vs the registry,
        // bound to this instruction (the faulting load itself).
        if (pkt->req && pkt->req->hasVaddr()) {
            const Addr v = pkt->req->getVaddr();
            const Addr v_end = v + (Addr)pkt->req->getSize();
            for (const auto &kv : addr_registry) {
                const AddrEntry &e = kv.second;
                if (e.size == 0)
                    continue;
                if (v < e.base + e.size && e.base < v_end
                        && e.dyn_seq == inst->seqNum) {
                    hit_ptag = e.ptag;
                    hit_family = "addrpath";
                    hit_corr = CORR_SEQ_PRIMARY;
                    break;
                }
            }
        }
        // cache: the delivered byte range vs the faulted-byte registry.
        if (!hit_ptag) {
            const Addr a = pkt->getAddr();
            const Addr a_end = a + (Addr)pkt->getSize();
            for (const auto &kv : blk_registry) {
                const BlkEntry &e = kv.second;
                if (a < e.byte_end && e.byte_begin < a_end) {
                    hit_ptag = e.ptag;
                    hit_family = "cache";
                    hit_corr = CORR_ADDR_FALLBACK;
                    break;
                }
            }
        }
        if (!hit_ptag)
            return;

        // [MDSPEC][R6/A10] A load that received the wrong response but is
        // then SQUASHED has its result discarded and the instruction
        // replayed: the corruption is contained by the squash/replay
        // mechanism. This case used to emit NOTHING at all (the old
        // `isSquashed()` early-return fired before any emission), so a
        // contain-by-squash outcome could never fire and the chain looked
        // like it silently vanished. Record the containment explicitly.
        if (inst->isSquashed()) {
            std::ostringstream h_va, h_pa;
            if (pkt->req && pkt->req->hasVaddr())
                h_va << std::hex << pkt->req->getVaddr();
            h_pa << std::hex << pkt->getAddr();
            notePropEvt("squash_masked", {
                {"fault_id", std::to_string(hit_ptag)},
                {"corr", hit_corr ? hit_corr : ""},
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"va", h_va.str()},
                {"pa", h_pa.str()},
                {"field", "squashed_load"},
                {"outcome", "masked"},
                {"detection_layer", "L4"},
                {"contained", "1"},
                {"containment_layer", "L4"},
                {"containment_reason", "squash_replay"},
            });
            containment_ptags[hit_ptag] = {"L4", "squash_replay"};
            // [MDSPEC][R6-EMIT2/oracle] the hardware squash/replay detected
            // and contained the fault: signal it on stdout too.
            emitDetectSignal("Hardware RAS", true, hit_ptag, "squash_replay");
            return;
        }

        // resp node: the memory response delivering the fault.
        const uint64_t req_seq =
            (pkt->req && pkt->req->hasInstSeqNum())
                ? pkt->req->getReqInstSeqNum() : 0;
        {
            std::ostringstream d;
            d << "family=" << hit_family << ";size=" << pkt->getSize();
            // [R6-A2/EVID-P0] A SplitDataRequest response can carry the
            // data flag without a readable contiguous buffer; the old
            // unconditional getPtr() crash inside fnv1a64 truncated the
            // whole evidence stream (A08-F0-W5 s3). Never hash a null
            // pointer — record the honest "unavailable" marker instead.
            if (pkt->hasData() && pkt->getPtr<uint8_t>() != nullptr) {
                d << ";data_fnv=" << std::hex
                  << fnv1a64(pkt->getPtr<uint8_t>(), pkt->getSize())
                  << std::dec;
            } else if (pkt->hasData()) {
                d << ";data_fnv=unavailable";
            }
            if (inst->getFault() != NoFault)
                d << ";fault=" << inst->getFault()->name();
            writeNode(hit_ptag, "resp", inst->seqNum, true,
                      req_seq, req_seq != 0, pkt->getAddr(), true,
                      0, false, 0, false, d.str(), hit_corr);
        }

        // [MDSPEC][H7] unified lq_complete event (spec sheet 9: LQ
        // lifecycle — the response returned for LQ entry lqIdx; L3).
        // Load-side discriminator = wb_to_reg (needWBToRegister — the SAME
        // condition gating taint_reg below). lqIdx alone is UNSOUND: stores
        // keep a stale lqIdx from DynInst-pool reuse (empirically hit on
        // sq_forward dyn133 store with residual lq_idx=3).
        if (wb_to_reg && inst->lqIdx >= 0) {
            std::ostringstream h7_va, h7_pa;
            if (pkt->req && pkt->req->hasVaddr())
                h7_va << std::hex << pkt->req->getVaddr();
            h7_pa << std::hex << pkt->getAddr();
            notePropEvt("lq_complete", {
                {"fault_id", std::to_string(hit_ptag)},
                {"dyn_inst_seq", std::to_string(inst->seqNum)},
                {"lq_idx", std::to_string((long long)inst->lqIdx)},
                {"va", h7_va.str()},
                {"pa", h7_pa.str()},
                {"request_id", req_seq ? std::to_string(req_seq)
                                       : std::string("0")},
                // [R4-1-review-I1] which correlate arm joined this event
                {"corr", hit_corr ? hit_corr : ""},
            });
        }

        // [MDSPEC][R6/A7] Store chains: a STORE's response carries the
        // wrong value/address to memory, but a store has no register
        // writeback (needWBToRegister() is false), so the load-only taint
        // path below returned before anything was tainted and the chain used
        // to stop at L3 (measured: S04-F0-W5, verdict
        // provable_to_L3_then_unknown, 11 events, no L4 node). A store's
        // architectural materialization IS its commit (the wrong memory side
        // effect), so taint the store BY DYN SEQ: the store's own later
        // commit (noteCommit) then fires the errant commit and the chain
        // closes at L4->L5. The taint_reg node is the L4 anchor the chain
        // checker needs (L3->L4 witness = this store's resp/sq_complete).
        if (!wb_to_reg && inst->isStore()) {
            std::ostringstream sd;
            sd << "class=store;dest_idx=0;old_addr=clean;new_addr=tainted";
            writeNode(hit_ptag, "taint_reg", inst->seqNum, true,
                      req_seq, req_seq != 0, pkt->getAddr(), true,
                      0, false, 0, false, sd.str(), hit_corr);
            TaintEntry ste;
            ste.ptag = hit_ptag;
            ste.taintor_seq = inst->seqNum;
            // [R6/A6] the event that established this taint = the node just
            // written (writeNode's dual-emit used event_id == next_node_id).
            ste.src_event = next_node_id - 1;
            store_taint[inst->seqNum] = ste;
            return;
        }

        // taint_reg: exactly the condition under which LSQUnit::writeback
        // performs completeAcc (needWBToRegister + NoFault) — the load's
        // dest phys regs receive the fault-delivered data.
        if (!wb_to_reg || inst->getFault() != NoFault)
            return;
        const int ndest = (int)inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = inst->renamedDestIdx(i);
            if (!phys)
                continue;
            const std::pair<int, uint32_t> key(phys->classValue(),
                                               phys->index());
            TaintEntry te;
            te.ptag = hit_ptag;
            te.taintor_seq = inst->seqNum;
            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";dest_idx=" << i
              // [MDSPEC][R6/A4] The faulted VALUE of this node is the
              // physical cell's taint state: the cell held a legitimate
              // (clean) value and now holds fault-delivered data. The pair
              // rides the documented old_addr/new_addr → before/after lift
              // so the T-series stream can show WHAT changed (C12 tick pair
              // / L04 seq pair precedent). Measured before this fix:
              // kind=taint_reg ... before= after=.
              << ";old_addr=clean;new_addr=tainted";
            writeNode(hit_ptag, "taint_reg", inst->seqNum, true,
                      req_seq, req_seq != 0, pkt->getAddr(), true,
                      phys->index(), true,
                      inst->destRegIdx(i).index(), true, d.str(), hit_corr);
            // [MDSPEC][R6/A6] Remember WHICH event established this taint:
            // writeNode's dual-emit used event_id == next_node_id (pre-
            // increment), so the node just written is next_node_id - 1.
            te.src_event = next_node_id - 1;
            taint_set[key] = te;
        }
    }

    // [R6-S-FWD 2026-10-30] Real SQ-forward lifecycle: L1 sq_entry -> L2
    // lsq_fwd -> L3 resp -> L4 taint_reg, plus the consuming load's seq
    // registration. A forwarded load has no memory response, so this is the
    // ONLY place its destination registers can enter the taint set; noteCommit
    // then observes a real L5 at the load's (or a consumer's) commit.
    uint64_t
    CHAOSPropagation::noteForwardedLoad(o3::DynInst *load_inst, Addr vaddr,
                                        unsigned size, uint64_t ptag,
                                        uint64_t store_seq, long long sq_idx,
                                        long long lq_idx,
                                        uint64_t load_req_id,
                                        uint64_t true_store_seq,
                                        const char *field, const void *data)
    {
        if (!write_log || !load_inst || ptag == 0)
            return 0;
        const uint64_t load_seq = load_inst->seqNum;
        const Addr span = size ? size : 1;
        sweepExpired();
        auto hex = [](Addr a) {
            std::ostringstream s;
            s << std::hex << a;
            return s.str();
        };
        const char *model = field ? field : "lsqfwd_forward";

        // L1: the producer store's SQ entry — the real forwarding source.
        notePropEvt("sq_entry", {
            {"fault_id", std::to_string(ptag)},
            {"dyn_inst_seq", std::to_string(load_seq)},
            {"store_dyn_inst_seq", std::to_string(store_seq)},
            {"sq_idx", std::to_string(sq_idx)},
            {"lq_idx", std::to_string(lq_idx)},
            {"request_id", std::to_string(load_req_id)},
            {"va", hex(vaddr)},
            {"field", "store_entry"},
            {"corr", CORR_SEQ_PRIMARY},
        });

        // L2: the forward decision/transfer itself.
        {
            std::vector<std::pair<std::string, std::string>> kv = {
                {"fault_id", std::to_string(ptag)},
                {"dyn_inst_seq", std::to_string(load_seq)},
                {"store_dyn_inst_seq", std::to_string(store_seq)},
                {"sq_idx", std::to_string(sq_idx)},
                {"lq_idx", std::to_string(lq_idx)},
                {"request_id", std::to_string(load_req_id)},
                {"va", hex(vaddr)},
                {"field", model},
                {"before", "store_data"},
                {"after", std::string("fwd_corrupt:") + model},
                {"shared_size", std::to_string(span)},
                {"corr", CORR_SEQ_PRIMARY},
            };
            if (true_store_seq != 0 && true_store_seq != store_seq)
                kv.push_back({"true_store_dyn_inst_seq",
                              std::to_string(true_store_seq)});
            notePropEvt("lsq_fwd", kv);
        }

        // L3: the forwarded value handed to the consuming load.
        {
            std::ostringstream d;
            d << "family=lsqfwd;size=" << span << ";field=" << model;
            if (data)
                d << ";data_fnv=" << std::hex
                  << fnv1a64(data, span) << std::dec;
            if (true_store_seq != 0 && true_store_seq != store_seq)
                d << ";true_store_dyn_inst_seq=" << true_store_seq;
            writeNode(ptag, "resp", load_seq, true, load_req_id,
                      load_req_id != 0, vaddr, true, 0, false, 0, false,
                      d.str(), CORR_SEQ_PRIMARY);
        }

        // L4: the load's destination physical register(s) receive the value.
        uint64_t last_evt = 0;
        const int ndest = (int)load_inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = load_inst->renamedDestIdx(i);
            if (!phys)
                continue;
            const std::pair<int, uint32_t> key(phys->classValue(),
                                               phys->index());
            std::ostringstream d;
            d << "class=" << regClassName(phys->classValue())
              << ";dest_idx=" << i
              << ";old_addr=clean;new_addr=tainted"
              << ";fwd_source=" << store_seq;
            writeNode(ptag, "taint_reg", load_seq, true, load_req_id,
                      load_req_id != 0, vaddr, true, phys->index(), true,
                      load_inst->destRegIdx(i).index(), true, d.str(),
                      CORR_SEQ_PRIMARY);
            TaintEntry te;
            te.ptag = ptag;
            te.taintor_seq = load_seq;
            te.src_event = next_node_id - 1;
            taint_set[key] = te;
            last_evt = next_node_id - 1;
        }

        // Seq-bound lifecycle surface: squash/commit join by the LOAD's seq.
        AddrEntry e;
        e.ptag = ptag;
        e.dyn_seq = load_seq;
        e.base = vaddr;
        e.size = span;
        e.registered = curTick();
        load_fwd_registry[load_seq] = e;
        return last_evt;
    }

    void
    CHAOSPropagation::noteCommit(ThreadID tid, o3::DynInst *head_inst)
    {
        if (!write_log || !head_inst)
            return;

        // [MDSPEC][R6-EMIT2/oracle] tracer commit ordinal (counts every
        // commit observed, CHAOSMicroSnap semantic). The L5 detection node
        // and chain_end carry it as commit_seq (L18 contract item 3).
        ++commit_seq_counter;

        const uint64_t pc = head_inst->pcState().instAddr();
        uint64_t first_consumed_ptag = 0;
        bool any_consumer = false;
        bool self_taint = false;
        uint64_t self_taint_ptag = 0;
        // [MDSPEC][R6/A7] A STORE whose own response carried the fault: its
        // commit is the architectural materialization (the wrong memory side
        // effect). Keyed by dyn seq (see store_taint / noteMemResponse).
        bool self_store_taint = false;
        uint64_t self_store_ptag = 0;
        {
            const auto stit = store_taint.find(head_inst->seqNum);
            if (stit != store_taint.end()) {
                self_store_taint = true;
                self_store_ptag = stit->second.ptag;
            }
        }
        // [MDSPEC][R6/A6] event_id of the last consumer node emitted above —
        // the taint source for the dests it re-taints (see below).
        uint64_t last_consumer_evt = 0;

        // Sources: a tainted source phys reg = this commit consumes a
        // fault-delivered value → consumer node.
        const int nsrc = (int)head_inst->numSrcRegs();
        for (int i = 0; i < nsrc; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedSrcIdx(i);
            if (!phys)
                continue;
            const auto it = taint_set.find(
                std::make_pair(phys->classValue(), phys->index()));
            if (it == taint_set.end())
                continue;
            any_consumer = true;
            if (!first_consumed_ptag)
                first_consumed_ptag = it->second.ptag;
            // [MDSPEC][R6-FIXCPP/T3] Route the consumer through the summary
            // aggregator. The group's FIRST member (and any member with a NEW
            // dyn_inst_seq = a new semantic state) is emitted as its own
            // PROP-EVT; an exact duplicate is folded into the group's
            // CONSUMER-SUMMARY accounting (see chaos_consumer_summary.hh).
            // The `consumer` kind is the ONLY aggregatable kind — L5 /
            // containment / terminal / every state-change event is emitted
            // unchanged below and elsewhere.
            const uint64_t cptag = it->second.ptag;
            const std::string csrc = chaos_consumer::sourceIdOf(phys->index());
            if (consumer_agg.observe("consumer", cptag, csrc,
                                     head_inst->seqNum, curTick())) {
                std::ostringstream d;
                d << "class=" << regClassName(phys->classValue())
                  << ";src_idx=" << i
                  // [MDSPEC][R6/A6] A consumer does NOT descend from the
                  // previous event of the chain: it descends from the event
                  // that established the taint it consumed. Naming that event
                  // is what turns the chain into a real DAG (one source → many
                  // consumers) instead of the degenerate linear list the
                  // single ptag_last_event cursor produced. parent_event_id is
                  // a registry field, so the dual-emit honours this override.
                  << ";parent_event_id=" << it->second.src_event
                  << ";pc=" << std::hex << pc << std::dec;
                writeNode(cptag, "consumer", head_inst->seqNum, true,
                          0, false, 0, false, phys->index(), true,
                          head_inst->srcRegIdx(i).index(), true, d.str(),
                          CORR_TAINT_PROP, (int)tid);
                // The just-emitted consumer node is the taint source for any
                // dest it re-taints below.
                last_consumer_evt = next_node_id - 1;
                consumer_agg.noteEmitted("consumer", cptag, csrc,
                                         last_consumer_evt);
            } else {
                // Suppressed duplicate: no event is fabricated. Keep the DAG
                // connected by naming the group's representative (the emitted
                // first member) as the taint source for the dests re-tained
                // below.
                const uint64_t rep = consumer_agg.representativeEvent(
                    "consumer", cptag, csrc);
                if (rep)
                    last_consumer_evt = rep;
            }
        }

        // Dests: is this the faulting load itself committing its tainted
        // dest (taintor_seq == own seqNum)? That commit is the first
        // architectural materialization of the fault.
        const int ndest = (int)head_inst->numDestRegs();
        for (int i = 0; i < ndest; ++i) {
            const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
            if (!phys)
                continue;
            const auto it = taint_set.find(
                std::make_pair(phys->classValue(), phys->index()));
            if (it != taint_set.end()
                    && it->second.taintor_seq == head_inst->seqNum) {
                self_taint = true;
                if (!self_taint_ptag)
                    self_taint_ptag = it->second.ptag;
            }
        }

        // errant_commit: once per run — the first commit on a fault path
        // (the faulting load itself, or the first consumer). Field-level
        // "first wrong architectural commit" stays L2 commit_diff's
        // first_errant_commit (authoritative); this node is the
        // propagation-view alignment point (same seqNum space).
        if (!errant_commit_seen
                && (any_consumer || self_taint || self_store_taint)) {
            const uint64_t ptag = any_consumer ? first_consumed_ptag
                : self_taint ? self_taint_ptag : self_store_ptag;
            std::ostringstream d;
            // [R6-C/GAP-2] This IS the observable L5 detection: the wrong
            // value reached architectural state (a committed instruction
            // consumed the tainted value, or the faulting load committed its
            // tainted dest). Measured before this fix:
            //   kind=errant_commit corr=taint_prop dyn_inst_seq=391
            //   detection_layer= outcome=
            // — the real detection event named neither its layer nor its
            // outcome, while the lifecycle chain_end node carried the only
            // (non-evidentiary) L5-ish fields. The ruling: L5 evidence must
            // be THIS event, so it must name its layer and outcome. Both keys
            // are registry fields, so the dual-emit lifts them verbatim.
            d << "trigger=" << (any_consumer ? "first_consumer"
                                 : self_taint ? "faulting_load_commit"
                                              : "faulting_store_commit")
              << ";detection_layer=L5"
              << ";outcome=errant_commit"
              // [MDSPEC][R6-EMIT2/oracle] the escape is NOT contained, and
              // the detection point is named (L18 contract items 1+3): a
              // crash/abort sample that never reaches the exit callback must
              // still carry contained=0 and the commit point.
              << ";contained=0"
              << ";commit_seq=" << commit_seq_counter
              << ";pc=" << std::hex << pc << std::dec;
            writeNode(ptag, "errant_commit", head_inst->seqNum, true,
                      0, false, 0, false, 0, false, 0, false, d.str(),
                      CORR_TAINT_PROP, (int)tid);
            // Remember the detection point for the chain's L5 chain_end.
            errant_detect[ptag] = DetectPoint{pc, head_inst->seqNum,
                                              commit_seq_counter, curTick()};
            // Hardware-detector stdout signal: the wrong value reached
            // architectural state and NOTHING contained it → layer None,
            // contained 0. This is the escape the oracle records as SDC.
            emitDetectSignal("None", false, ptag, "errant_commit");
            errant_commit_seen = true;
            // [MDSPEC][R6] Bind the observed errant commit to its own chain
            // so the L5 chain_end node can report it (see .hh).
            errant_ptags.insert(ptag);
        }
        // [MDSPEC][R6/A7] Bound the store taint: the store's commit has now
        // been observed (it either fired the errant commit above or the run
        // already had its first one) — drop the entry so a recycled dyn seq
        // cannot re-fire later.
        if (self_store_taint)
            store_taint.erase(head_inst->seqNum);

        // Propagation rules (see .hh):
        //  - consumer commits → its dests now carry the wrong value
        //    (re-taint under the consumed chain's ptag);
        //  - the tainting load's own commit → keep its dest taint;
        //  - an UNRELATED producer committing onto a tainted phys cell →
        //    clean overwrite, the stale taint dies (phys-recycling bound).
        if (any_consumer) {
            for (int i = 0; i < ndest; ++i) {
                const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
                if (!phys)
                    continue;
                TaintEntry te;
                te.ptag = first_consumed_ptag;
                te.taintor_seq = head_inst->seqNum;
                // [R6/A6] the re-taint is established by the consumer node.
                te.src_event = last_consumer_evt;
                taint_set[std::make_pair(phys->classValue(),
                                         phys->index())] = te;
            }
        } else if (!self_taint && !self_store_taint) {
            for (int i = 0; i < ndest; ++i) {
                const PhysRegIdPtr phys = head_inst->renamedDestIdx(i);
                if (!phys)
                    continue;
                taint_set.erase(std::make_pair(phys->classValue(),
                                               phys->index()));
            }
        }
        // [R6-S-FWD 2026-10-30] This instruction's commit was observed; drop
        // its forwarded-load registration so a recycled dyn seq cannot
        // re-join the chain. The architectural taint itself stays (the
        // phys-reg entry is cleared by the normal overwrite rules).
        load_fwd_registry.erase(head_inst->seqNum);
    }

    // ================= MMU unified trace (MMU-TRACE v1) ==================
    //
    // Every event is observation-only and goes through notePropEvt, i.e.
    // into the SAME prop_evt.txt.gz stream as the fault-propagation events.
    // Fault-free events carry fault_id=0. ParentEventID is set explicitly
    // from the per-translation / per-walk / per-TLBI cursor; it is never
    // inferred from tick order.
    //
    // Identity rules:
    //   * translation_id  — one MMU::getTE translation attempt.
    //   * unique_request_id — one MMU-allocated request identity; the legacy
    //     request_id stays Request::getReqInstSeqNum (documented alias).
    //   * walk_id — the existing WalkerState::chaosWalkId.
    //   * lookup_id / tlbi_id / response_id — MMU-allocated counters.
    //   * tlb_entry_id + entry_generation — stable slot identity, never a
    //     raw pointer.

    static std::string
    mmuHex(Addr a)
    {
        std::ostringstream s;
        s << std::hex << a;
        return s.str();
    }

    static void
    mmuSetParent(std::vector<std::pair<std::string, std::string>> &kv,
                 uint64_t parent)
    {
        if (parent)
            kv.push_back({"parent_event_id", std::to_string(parent)});
    }

    uint64_t
    CHAOSPropagation::mmuUniqueId(uint64_t translation_id) const
    {
        const auto it = mmu_txn.find(translation_id);
        return it == mmu_txn.end() ? 0 : it->second.unique_request_id;
    }

    uint64_t
    CHAOSPropagation::mmuTxnForSeqVa(uint64_t seq, Addr va) const
    {
        const auto it = mmu_txn_by_seq_va.find({seq, va});
        return it == mmu_txn_by_seq_va.end() ? 0 : it->second;
    }

    uint64_t
    CHAOSPropagation::mmuTxnForSeq(uint64_t seq) const
    {
        const auto it = mmu_seq_txn.find(seq);
        return it == mmu_seq_txn.end() ? 0 : it->second;
    }

    bool
    CHAOSPropagation::mmuSeqSquashed(uint64_t seq) const
    {
        if (!seq)
            return false;
        const uint64_t tid = mmuTxnForSeq(seq);
        if (!tid)
            return false;
        const auto it = mmu_txn.find(tid);
        return it != mmu_txn.end() && it->second.squash_event != 0;
    }

    uint64_t
    CHAOSPropagation::mmuTxnForVa(Addr va) const
    {
        const auto it = mmu_txn_by_va.find(va);
        return it == mmu_txn_by_va.end() ? 0 : it->second;
    }

    uint64_t
    CHAOSPropagation::mmuAdoptConsumerFault(uint64_t tid, uint64_t seq)
    {
        if (!tid)
            return 0;
        const auto pit = mmu_consumer_seq_ptag.find(seq);
        auto tit = mmu_txn.find(tid);
        if (pit != mmu_consumer_seq_ptag.end() &&
                tit != mmu_txn.end() && tit->second.fault_ptag == 0)
            tit->second.fault_ptag = pit->second;
        return tit == mmu_txn.end() ? 0 : tit->second.fault_ptag;
    }

    uint64_t
    CHAOSPropagation::mmuNewSyntheticSeq(Addr va)
    {
        // Observation-only: no trace, or VA outside the configured window,
        // means no synthetic identity is created and the caller keeps its
        // previous behaviour (seq == 0).
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        if (next_mmu_synthetic_seq == 0)
            next_mmu_synthetic_seq = mmuSyntheticSeqBase();
        if (next_mmu_synthetic_seq == UINT64_MAX)
            return 0;   // reserved namespace exhausted: drop the trace, never
                        // reuse an id
        const uint64_t seq = ++next_mmu_synthetic_seq;
        mmu_synthetic_seqs.insert(seq);
        return seq;
    }

    uint64_t
    CHAOSPropagation::mmuBeginTxn(uint64_t seq, Addr va, uint64_t pc,
                                  const char *mode, bool stage2, uint16_t asid,
                                  uint16_t vmid, unsigned regime,
                                  unsigned ss, uint64_t fault_ptag)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va) || seq == 0)
            return 0;       // no instruction identity: outside MMU trace scope
        // [MMU-TRACE v4] A reserved-namespace seq must have been minted by
        // mmuNewSyntheticSeq. A real DynInst::seqNum that ever reached this
        // range is refused, so synthetic and real identities can never
        // collide in the transaction map or in the trace.
        if (mmuIsSyntheticSeq(seq) && !mmu_synthetic_seqs.count(seq))
            return 0;

        // A retranslation of the same (instruction, VA) reuses the open
        // transaction so the walk/result events keep one causal chain; it
        // still gets a fresh execution_attempt_id.
        uint64_t tid = mmuTxnForSeqVa(seq, va);
        if (tid) {
            const auto &t = mmu_txn[tid];
            if (t.result_event != 0)
                tid = 0;    // previous attempt completed: new transaction
        }
        const uint32_t attempt = ++mmu_attempts[{seq, va}];
        if (!tid) {
            tid = ++next_mmu_translation_id;
            MmuTxnInfo t;
            t.translation_id = tid;
            t.unique_request_id = ++next_mmu_unique_request_id;
            t.dyn_seq = seq;
            t.va = va;
            t.attempt = attempt;
            t.asid = asid;
            t.vmid = vmid;
            t.regime = regime;
            t.ss = ss;
            // [Phase 2.2] A consumer transaction is BORN with the inherited
            // fault id: its translation_start is already fault-tagged.
            t.fault_ptag = fault_ptag;
            mmu_txn[tid] = t;
            mmu_txn_by_seq_va[{seq, va}] = tid;
            mmu_txn_by_va[va] = tid;
            mmu_seq_txn[seq] = tid;
            mmu_traced_seqs.insert(seq);
        } else {
            mmu_txn[tid].attempt = attempt;
            // Refresh the association key on a retranslation of the same
            // (seq, VA) — a regime/ASID switch must not inherit a stale key.
            mmu_txn[tid].asid = asid;
            mmu_txn[tid].vmid = vmid;
            mmu_txn[tid].regime = regime;
            mmu_txn[tid].ss = ss;
            if (fault_ptag)
                mmu_txn[tid].fault_ptag = fault_ptag;
        }

        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(mmu_txn[tid].fault_ptag)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id",
                std::to_string(mmu_txn[tid].unique_request_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"mode", mode ? mode : "Unknown"},
            {"stage", stage2 ? "2" : "1"},
            {"execution_attempt_id", std::to_string(attempt)},
            {"replay_generation", attempt > 1 ? "1" : "0"},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"corr", CORR_NONE},
        };
        // [MMU-TRACE v4] Explicit marker: this dyn_inst_seq is a synthetic
        // Execute-fetch identity, not a real DynInst::seqNum. Any reader can
        // also detect it from the 2^63 namespace bit.
        if (mmuIsSyntheticSeq(seq))
            kv.push_back(
                {"dyn_inst_seq_kind", "synthetic_execute_fetch"});
        if (pc)
            kv.push_back({"pc", mmuHex(pc)});
        // [MMU-TRACE v2] Explicit maintenance -> miss edge on the EXACT
        // association key (VA, ASID, VMID, regime, SS), never VA alone.
        const MmuAssocKey key{va, asid, vmid, (uint8_t)regime, (uint8_t)ss};
        uint64_t parent_ev = 0;
        const auto tlit = mmu_last_tlbi_key.find(key);
        if (tlit != mmu_last_tlbi_key.end())
            parent_ev = tlit->second;
        // While the M01 latch is still armed for this exact key, the
        // suppressed maintenance event (the retained stale entry's survival)
        // is the true cause of this miss — prefer it over a later unrelated
        // maintenance with the same key (e.g. a partial-entry range TLBI).
        if (mmu_fault_armed && va == mmu_fault_va && asid == mmu_fault_asid &&
                vmid == mmu_fault_vmid &&
                (uint8_t)regime == mmu_fault_regime &&
                (uint8_t)ss == mmu_fault_ss &&
                mmu_fault_last_suppressed_event)
            parent_ev = mmu_fault_last_suppressed_event;
        if (parent_ev)
            mmuSetParent(kv, parent_ev);
        const uint64_t eid = notePropEvt("translation_start", kv);
        mmu_txn[tid].last_event = eid;
        return tid;
    }

    uint64_t
    CHAOSPropagation::mmuBeginTranslation(const RequestPtr &req, Addr va,
                                          const char *mode, bool stage2)
    {
        const uint64_t seq =
            (req && req->hasInstSeqNum()) ? req->getReqInstSeqNum() : 0;
        return mmuBeginTxn(seq, va, (req ? req->getPC() : 0), mode, stage2,
                           0, 0, 0, 0);
    }

    uint64_t
    CHAOSPropagation::mmuBeginMissTranslation(uint64_t seq, Addr va,
                                              const char *mode, bool stage2,
                                              uint16_t asid, uint16_t vmid,
                                              unsigned regime, unsigned ss)
    {
        return mmuBeginTxn(seq, va, 0, mode, stage2, asid, vmid, regime, ss);
    }

    uint64_t
    CHAOSPropagation::mmuNoteLookup(const std::string &instance,
                                    uint64_t lookup_id,
                                    uint64_t translation_id,
                                    uint64_t unique_id, uint64_t seq, Addr va,
                                    uint16_t asid, uint16_t vmid, bool hit,
                                    bool partial, Addr pfn, unsigned n,
                                    uint64_t entry_id, uint32_t gen,
                                    unsigned level, unsigned regime,
                                    unsigned ss, uint64_t fault_ptag)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid && seq)
            tid = mmuTxnForSeqVa(seq, va);
        if (!tid && !seq)
            tid = mmuTxnForVa(va);
        if (!tid)
            return 0;
        uint64_t ftid = 0;
        {
            const auto it = mmu_txn.find(tid);
            if (it == mmu_txn.end())
                return 0;
            // A different dynamic instruction hitting the same warm VA must
            // NOT join this transaction (that was the warm-up amplification).
            if (seq && it->second.dyn_seq != seq)
                return 0;
            if (!seq)
                seq = it->second.dyn_seq;
            // [MMU-TRACE v2] The consuming lookup of a fault-chain
            // translation adopts (or already has) the chain id.
            if (fault_ptag)
                mmu_txn[tid].fault_ptag = fault_ptag;
            ftid = mmu_txn[tid].fault_ptag;
        }
        if (!unique_id && tid)
            unique_id = mmuUniqueId(tid);
        uint64_t parent = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end())
                parent = it->second.last_event;
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"lookup_id", std::to_string(lookup_id)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"tlb_instance", instance},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"walk_level", "L" + std::to_string(level)},
            {"mode", partial ? "partial" : "complete"},
            {"corr", CORR_NONE},
        };
        if (mmuIsSyntheticSeq(seq))
            kv.push_back(
                {"dyn_inst_seq_kind", "synthetic_execute_fetch"});
        if (hit) {
            kv.push_back({"pfn", mmuHex(pfn)});
            kv.push_back({"page_size_n", std::to_string(n)});
            kv.push_back({"pa", mmuHex(pfn << n)});
            kv.push_back({"tlb_entry_id", std::to_string(entry_id)});
            kv.push_back({"entry_generation", std::to_string(gen)});
            kv.push_back({"entry_valid", "1"});
            kv.push_back({"entry_partial", partial ? "1" : "0"});
        }
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt(hit ? "tlb_lookup_hit"
                                            : "tlb_lookup_miss", kv);
        if (tid) {
            mmu_txn[tid].last_event = eid;
            if (!hit) {
                // remember the miss as the walk's causal parent
                mmu_seq_txn[seq] = tid;
            }
        }
        if (ftid && ftid == mmu_fault_ptag && hit) {
            mmu_fault_entry_id = entry_id;
            mmu_fault_entry_generation = gen;
        }
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteWalkStart(uint64_t walk_id,
                                       uint64_t translation_id,
                                       uint64_t unique_id, uint64_t seq,
                                       Addr va, uint16_t asid, uint16_t vmid,
                                       unsigned level, const char *mode,
                                       bool stage2, unsigned regime,
                                       unsigned ss)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid && seq)
            tid = mmuTxnForSeqVa(seq, va);
        if (!tid && !seq)
            tid = mmuTxnForVa(va);
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it == mmu_txn.end() || (seq && it->second.dyn_seq != seq))
                tid = 0;
        }
        if (!unique_id && tid)
            unique_id = mmuUniqueId(tid);
        uint64_t parent = 0;
        uint64_t ftid = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end()) {
                parent = it->second.last_event;
                ftid = it->second.fault_ptag;
            }
            mmu_txn_by_walk[walk_id] = tid;
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"walk_level", "L" + std::to_string(level)},
            {"mode", mode ? mode : "Unknown"},
            {"stage", stage2 ? "2" : "1"},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("ptw_start", kv);
        mmu_walk_last[walk_id] = eid;
        if (tid)
            mmu_txn[tid].last_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNotePteRead(uint64_t walk_id,
                                     uint64_t translation_id,
                                     uint64_t unique_id, uint64_t seq,
                                     Addr va, Addr pte_addr, unsigned level,
                                     uint64_t ptw_request_id)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid)
            tid = mmuTxnForVa(va);
        if (!unique_id && tid)
            unique_id = mmuUniqueId(tid);
        uint64_t ftid = 0, regime = 0, s_state = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end()) {
                ftid = it->second.fault_ptag;
                regime = it->second.regime;
                s_state = it->second.ss;
            }
        }
        uint64_t parent = 0;
        const auto wit = mmu_walk_last.find(walk_id);
        if (wit != mmu_walk_last.end())
            parent = wit->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"pte_address", mmuHex(pte_addr)},
            {"walk_level", "L" + std::to_string(level)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(s_state)},
            {"corr", CORR_NONE},
        };
        if (ptw_request_id)
            kv.push_back({"ptw_request_id", std::to_string(ptw_request_id)});
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("pte_read", kv);
        mmu_walk_last[walk_id] = eid;
        if (tid)
            mmu_txn[tid].last_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNotePteDecode(uint64_t walk_id,
                                       uint64_t translation_id,
                                       uint64_t unique_id, uint64_t seq,
                                       Addr va, Addr pte_addr, uint64_t before,
                                       uint64_t after, unsigned level,
                                       const char *desc_type,
                                       uint64_t ptw_request_id)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid)
            tid = mmuTxnForVa(va);
        if (!unique_id && tid)
            unique_id = mmuUniqueId(tid);
        uint64_t ftid = 0, regime = 0, s_state = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end()) {
                ftid = it->second.fault_ptag;
                regime = it->second.regime;
                s_state = it->second.ss;
            }
        }
        uint64_t parent = 0;
        const auto wit = mmu_walk_last.find(walk_id);
        if (wit != mmu_walk_last.end())
            parent = wit->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"pte_address", mmuHex(pte_addr)},
            {"pte_value_before", mmuHex(before)},
            {"pte_value_after", mmuHex(after)},
            {"walk_level", "L" + std::to_string(level)},
            {"descriptor_type", desc_type ? desc_type : "Unknown"},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(s_state)},
            {"corr", CORR_NONE},
        };
        if (ptw_request_id)
            kv.push_back({"ptw_request_id", std::to_string(ptw_request_id)});
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("pte_decode", kv);
        mmu_walk_last[walk_id] = eid;
        if (tid)
            mmu_txn[tid].last_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNotePtwRequest(uint64_t ptw_request_id,
                                        uint64_t walk_id,
                                        uint64_t translation_id,
                                        uint64_t unique_id, uint64_t seq,
                                        Addr va, Addr pte_addr,
                                        unsigned level,
                                        uint64_t pte_read_event)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va) || !ptw_request_id)
            return 0;
        uint64_t tid = translation_id;
        if (!tid)
            tid = mmuTxnForVa(va);
        if (!unique_id && tid)
            unique_id = mmuUniqueId(tid);
        uint64_t ftid = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end())
                ftid = it->second.fault_ptag;
        }
        MmuPtwRequestInfo &info = mmu_ptw_info[ptw_request_id];
        info.walk_id = walk_id;
        info.translation_id = tid;
        info.unique_id = unique_id;
        info.seq = seq;
        info.va = va;
        info.pte_addr = pte_addr;
        info.level = level;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"ptw_request_id", std::to_string(ptw_request_id)},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"pte_address", mmuHex(pte_addr)},
            {"walk_level", "L" + std::to_string(level)},
            {"outcome", "request_sent"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, pte_read_event);
        const uint64_t eid = notePropEvt("ptw_request", kv);
        info.request_event = eid;
        if (tid)
            mmu_txn[tid].last_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNotePtwResponse(uint64_t ptw_request_id)
    {
        if (!mmuTraceEnabled() || !ptw_request_id)
            return 0;
        auto it = mmu_ptw_info.find(ptw_request_id);
        if (it == mmu_ptw_info.end())
            return 0;
        MmuPtwRequestInfo &info = it->second;
        if (info.response_event)
            return info.response_event;
        uint64_t ftid = 0;
        if (info.translation_id) {
            const auto t = mmu_txn.find(info.translation_id);
            if (t != mmu_txn.end())
                ftid = t->second.fault_ptag;
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"ptw_request_id", std::to_string(ptw_request_id)},
            {"ptw_response_id", std::to_string(ptw_request_id)},
            {"walk_id", std::to_string(info.walk_id)},
            {"translation_id", std::to_string(info.translation_id)},
            {"unique_request_id", std::to_string(info.unique_id)},
            {"dyn_inst_seq", std::to_string(info.seq)},
            {"va", mmuHex(info.va)},
            {"pte_address", mmuHex(info.pte_addr)},
            {"walk_level", "L" + std::to_string(info.level)},
            {"outcome", "response_received"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, info.request_event);
        info.response_event = notePropEvt("ptw_response", kv);
        if (info.translation_id)
            mmu_txn[info.translation_id].last_event = info.response_event;
        return info.response_event;
    }

    uint64_t
    CHAOSPropagation::mmuNoteCacheEvent(const char *kind,
                                        const std::string &cache,
                                        PacketPtr pkt, bool hit,
                                        uint64_t mshr_id)
    {
        if (!mmuTraceEnabled() || !pkt || !pkt->req)
            return 0;
        const uint64_t seq = pkt->req->hasInstSeqNum()
            ? pkt->req->getReqInstSeqNum() : 0;
        if (!seq)
            return 0;
        const Addr pa = pkt->getAddr();
        const Addr va = pkt->req->hasVaddr() ? pkt->req->getVaddr() : 0;
        // [Phase 2.2] Primary: the instruction's own transaction. A later
        // dynamic consumer that hit the corrupted entry through a warm hit
        // used to have NO transaction here, so its cache path was dropped;
        // the lineage-consumption record now names its consumer transaction
        // and, if it is missing, a real per-instruction transaction is
        // created for it. The fault id always comes from the entry-lineage
        // consumption, never from a VA/PA match.
        uint64_t tid = va ? mmuTxnForSeqVa(seq, va) : 0;
        if (!tid)
            tid = mmuTxnForSeq(seq);
        if (!tid) {
            const auto cit = mmu_consumer_seq_tid.find(seq);
            if (cit != mmu_consumer_seq_tid.end())
                tid = cit->second;
        }
        if (!tid) {
            const auto pit = mmu_consumer_seq_ptag.find(seq);
            if (pit != mmu_consumer_seq_ptag.end() && va != 0) {
                tid = mmuBeginTxn(seq, va, pkt->req->getPC(),
                                  pkt->isWrite() ? "Write" : "Read", false,
                                  0, 0, 0, 0, pit->second);
            }
        }
        if (!tid)
            return 0;
        const uint64_t inherited_fault = mmuAdoptConsumerFault(tid, seq);
        (void)inherited_fault;
        uint64_t ftid = 0;
        auto t = mmu_txn.find(tid);
        if (t != mmu_txn.end())
            ftid = t->second.fault_ptag;
        // Chain identity comes ONLY from the MMU transaction's own
        // fault_ptag. A VA/PA match is not enough: the same VA is reused by
        // later translations and must not be merged into this fault chain.
        const std::string key = cache + ":" + std::to_string(seq) + ":" +
            std::to_string(pa) + ":" + (pkt->req->isInstFetch() ? "i" : "d");
        auto it = mmu_cache_req_ids.find(key);
        if (it == mmu_cache_req_ids.end())
            it = mmu_cache_req_ids.emplace(key, ++next_mmu_cache_req_id).first;
        const uint64_t cache_req_id = it->second;
        uint64_t parent = 0;
        if (t != mmu_txn.end())
            parent = t->second.last_event;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(mmuUniqueId(tid))},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"cache_req_id", std::to_string(cache_req_id)},
            {"cache_name", cache},
            {"pa", mmuHex(pa)},
            {"cache_line", mmuHex(pa & ~(Addr)0x3F)},
            {"hit", hit ? "1" : "0"},
            {"mshr_id", std::to_string(mshr_id)},
            {"corr", CORR_NONE},
        };
        if (va)
            kv.push_back({"va", mmuHex(va)});
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt(kind, kv);
        if (t != mmu_txn.end())
            t->second.last_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteTlbFill(uint64_t walk_id,
                                     uint64_t translation_id,
                                     uint64_t unique_id, uint64_t seq,
                                     Addr va, Addr pfn, unsigned n,
                                     bool partial, unsigned level)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid)
            tid = mmuTxnForVa(va);
        if (!unique_id && tid)
            unique_id = mmuUniqueId(tid);
        uint64_t ftid = 0, regime = 0, s_state = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end()) {
                ftid = it->second.fault_ptag;
                regime = it->second.regime;
                s_state = it->second.ss;
            }
        }
        uint64_t parent = 0;
        const auto wit = mmu_walk_last.find(walk_id);
        if (wit != mmu_walk_last.end())
            parent = wit->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"pfn", mmuHex(pfn)},
            {"page_size_n", std::to_string(n)},
            {"walk_level", "L" + std::to_string(level)},
            {"mode", partial ? "partial" : "complete"},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(s_state)},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt(
            partial ? "partial_entry_insert" : "tlb_fill", kv);
        mmu_walk_last[walk_id] = eid;
        if (tid)
            mmu_txn[tid].last_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteEntryInsert(const std::string &instance,
                                         uint64_t entry_id, uint32_t gen,
                                         Addr va, uint16_t asid, uint16_t vmid,
                                         Addr pfn, unsigned n, bool partial,
                                         unsigned level, unsigned regime,
                                         unsigned ss, uint64_t translation_id,
                                         uint64_t unique_id, uint64_t walk_id,
                                         uint64_t prev_entry_id,
                                         uint32_t prev_generation)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        // [Phase 2.2] The victim slot's old lifetime ends here. Close it
        // BEFORE the new insert event so the stream never shows a live old
        // generation after its replacement.
        if (prev_entry_id)
            mmuEndEntryLineage(instance, prev_entry_id, prev_generation,
                               "replace");
        // The owning translation is supplied by the real call site (walker
        // insert context or the TLB's propagated lookup identity). Never
        // guess it from "the latest transaction for this VA": a reused VA
        // would be misattributed.
        uint64_t tid = translation_id;
        uint64_t parent = 0, ftid = 0;
        uint64_t seq = 0, uid = unique_id;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end()) {
                parent = it->second.last_event;
                seq = it->second.dyn_seq;
                if (!uid)
                    uid = it->second.unique_request_id;
                ftid = it->second.fault_ptag;
            } else {
                tid = 0;      // context id without a live transaction
            }
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"tlb_instance", instance},
            {"tlb_entry_id", std::to_string(entry_id)},
            {"entry_generation", std::to_string(gen)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(uid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"pfn", mmuHex(pfn)},
            {"page_size_n", std::to_string(n)},
            {"walk_level", "L" + std::to_string(level)},
            {"mode", partial ? "partial" : "complete"},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"entry_valid", "1"},
            {"entry_partial", partial ? "1" : "0"},
            {"corr", CORR_NONE},
        };
        if (mmuIsSyntheticSeq(seq))
            kv.push_back(
                {"dyn_inst_seq_kind", "synthetic_execute_fetch"});
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("tlb_entry_insert", kv);
        if (tid)
            mmu_txn[tid].last_event = eid;
        if (ftid && ftid == mmu_fault_ptag && mmu_fault_entry_id == 0) {
            // First corrupted-entry identity only; M01 keeps its armed id.
            mmu_fault_entry_id = entry_id;
            mmu_fault_entry_generation = gen;
        }

        // [Phase 2.2] Register the lineage for THIS entry lifetime when the
        // inserted payload is the pending corrupted M02 refill. The match is
        // exact on walk_id + VA + page size + new PFN; a later unrelated
        // walk/entry can never be captured by address equality.
        if (walk_id == 0)
            walk_id = mmu_insert_walk_id;
        if (mmu_m02_pending.active && entry_id != 0 && walk_id != 0 &&
                walk_id == mmu_m02_pending.walk_id &&
                va == mmu_m02_pending.va && n == mmu_m02_pending.n &&
                pfn == mmu_m02_pending.new_pfn) {
            MmuEntryLineage lin;
            lin.fault_id = mmu_m02_pending.ptag;
            lin.origin_event = mmu_m02_pending.activation_event;
            lin.origin_translation_id = mmu_m02_pending.translation_id;
            lin.origin_walk_id = mmu_m02_pending.walk_id;
            lin.origin_seq = mmu_m02_pending.seq;
            lin.insert_event = eid;
            lin.va = va;
            lin.asid = asid;
            lin.vmid = vmid;
            lin.n = n;
            lin.regime = regime;
            lin.ss = ss;
            lin.old_pfn = mmu_m02_pending.old_pfn;
            lin.new_pfn = mmu_m02_pending.new_pfn;
            lin.old_pa = mmu_m02_pending.old_pa;
            lin.new_pa = mmu_m02_pending.new_pa;
            lin.last_event = eid;
            mmu_entry_lineage[MmuEntryLineageKey{instance, entry_id, gen}] =
                lin;
        }

        // [Phase 2.2] A promotion insert (DTLB refill from an l2 hit) copies
        // an existing corrupted entry. Propagate the lineage by the SOURCE
        // entry identity recorded by TLB::multiLookup.
        if (mmu_promote_src_id) {
            mmuM02NotePromotion(instance, entry_id, gen,
                                mmu_promote_src_instance, mmu_promote_src_id,
                                mmu_promote_src_gen, eid);
            mmuClearPromotionSource();
        }
        return eid;
    }

    void
    CHAOSPropagation::mmuNotePermission(const RequestPtr &req, Addr va,
                                        bool grant, const char *mode,
                                        bool stage2)
    {
        const uint64_t seq =
            (req && req->hasInstSeqNum()) ? req->getReqInstSeqNum() : 0;
        uint64_t tid = mmuTxnForSeqVa(seq, va);
        // [MMU-TRACE v4] A fetch Request has no inst seq; join the open
        // synthetic Execute transaction for this VA. A completed synthetic
        // transaction is never reused (warm hits stay silent).
        if (!tid && !seq) {
            tid = mmuTxnForVa(va);
            const auto tit = mmu_txn.find(tid);
            if (!tid || tit == mmu_txn.end() ||
                    (mmuIsSyntheticSeq(tit->second.dyn_seq) &&
                     tit->second.result_event != 0))
                tid = 0;
        }
        if (!tid || !mmuTraceEnabled())
            return;
        const auto it = mmu_txn.find(tid);
        if (it == mmu_txn.end())
            return;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(it->second.fault_ptag)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(it->second.unique_request_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"permission_result", grant ? "grant" : "deny"},
            {"mode", mode ? mode : "Unknown"},
            {"stage", stage2 ? "2" : "1"},
            {"regime", mmuRegimeName(it->second.regime)},
            {"security_state", mmuSecurityStateName(it->second.ss)},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, it->second.last_event);
        const uint64_t eid = notePropEvt("permission_eval", kv);
        mmu_txn[tid].last_event = eid;
    }

    void
    CHAOSPropagation::mmuNoteTranslationResult(
        const RequestPtr &req, Addr va, Addr pa, bool has_pa, const char *fault,
        Addr pfn, unsigned n, uint8_t mtype, bool shareable, uint8_t inner,
        uint8_t outer, bool noncacheable, bool xn, uint8_t ap,
        uint64_t entry_id, uint32_t gen)
    {
        const uint64_t seq =
            (req && req->hasInstSeqNum()) ? req->getReqInstSeqNum() : 0;
        uint64_t tid = mmuTxnForSeqVa(seq, va);
        if (!tid && !seq) {
            tid = mmuTxnForVa(va);
            // [MMU-TRACE v4] Only the first result joins a synthetic
            // Execute transaction; a later warm fetch hit to the same VA
            // must not re-attribute an event to the completed translation.
            const auto tit = mmu_txn.find(tid);
            if (!tid || tit == mmu_txn.end() ||
                    (mmuIsSyntheticSeq(tit->second.dyn_seq) &&
                     tit->second.result_event != 0))
                tid = 0;
        }
        if (!tid || !mmuTraceEnabled())
            return;
        const auto it = mmu_txn.find(tid);
        if (it == mmu_txn.end() || (seq && it->second.dyn_seq != seq))
            return;
        std::ostringstream attr;
        attr << "mtype=" << (unsigned)mtype
             << ";shareable=" << (shareable ? 1 : 0)
             << ";inner=" << (unsigned)inner
             << ";outer=" << (unsigned)outer
             << ";noncacheable=" << (noncacheable ? 1 : 0)
             << ";xn=" << (xn ? 1 : 0)
             << ";ap=" << (unsigned)ap;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(it->second.fault_ptag)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(it->second.unique_request_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"fault_status", fault ? fault : "NoFault"},
            {"memory_attribute", attr.str()},
            {"pfn", mmuHex(pfn)},
            {"page_size_n", std::to_string(n)},
            {"tlb_entry_id", std::to_string(entry_id)},
            {"entry_generation", std::to_string(gen)},
            {"regime", mmuRegimeName(it->second.regime)},
            {"security_state", mmuSecurityStateName(it->second.ss)},
            {"corr", CORR_NONE},
        };
        if (req && req->getPC() != 0)
            kv.push_back({"pc", mmuHex(req->getPC())});
        if (has_pa)
            kv.push_back({"pa", mmuHex(pa)});
        mmuSetParent(kv, it->second.last_event);
        const uint64_t eid = notePropEvt("translation_result", kv);
        mmu_txn[tid].last_event = eid;
        mmu_txn[tid].result_event = eid;
        if (it->second.fault_ptag && it->second.fault_ptag == mmu_fault_ptag) {
            mmu_fault_result_event = eid;
            mmu_fault_result_pa = has_pa ? pa : 0;
        }
    }

    void
    CHAOSPropagation::mmuNoteLsuRequest(const RequestPtr &req, Addr va, Addr pa,
                                        const char *mode, bool is_fetch,
                                        bool has_pa)
    {
        const uint64_t seq =
            (req && req->hasInstSeqNum()) ? req->getReqInstSeqNum() : 0;
        uint64_t tid = mmuTxnForSeqVa(seq, va);
        // [MMU-TRACE v4] Join the open synthetic Execute transaction for a
        // fetch (no inst seq). One LSU request per synthetic translation.
        if (!tid && !seq) {
            tid = mmuTxnForVa(va);
            const auto tit = mmu_txn.find(tid);
            if (!tid || tit == mmu_txn.end() ||
                    (mmuIsSyntheticSeq(tit->second.dyn_seq) &&
                     tit->second.req_event != 0))
                tid = 0;
        }
        if (!tid || !mmuTraceEnabled())
            return;
        const auto it = mmu_txn.find(tid);
        if (it == mmu_txn.end())
            return;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(it->second.fault_ptag)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(it->second.unique_request_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"mode", is_fetch ? "Execute" : (mode ? mode : "Unknown")},
            {"regime", mmuRegimeName(it->second.regime)},
            {"security_state", mmuSecurityStateName(it->second.ss)},
            {"corr", CORR_NONE},
        };
        if (has_pa)
            kv.push_back({"pa", mmuHex(pa)});
        mmuSetParent(kv, it->second.last_event);
        const uint64_t eid = notePropEvt("lsu_request", kv);
        mmu_txn[tid].last_event = eid;
        mmu_txn[tid].req_event = eid;
    }

    void
    CHAOSPropagation::mmuNoteMemResponse(o3::DynInst *inst, Packet *pkt)
    {
        if (!mmuTraceEnabled() || !inst || !pkt)
            return;
        const uint64_t seq = inst->seqNum;
        if (!mmu_traced_seqs.count(seq))
            return;
        Addr va = 0;
        if (pkt->req && pkt->req->hasVaddr())
            va = pkt->req->getVaddr();
        uint64_t tid = mmuTxnForSeqVa(seq, va);
        if (!tid)
            tid = mmuTxnForSeq(seq);
        if (!tid)
            return;
        mmuAdoptConsumerFault(tid, seq);
        const auto it = mmu_txn.find(tid);
        if (it == mmu_txn.end())
            return;
        const uint64_t rid = ++next_mmu_response_id;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(it->second.fault_ptag)},
            {"response_id", std::to_string(rid)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(it->second.unique_request_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"pa", mmuHex(pkt->getAddr())},
            {"corr", CORR_NONE},
        };
        if (pkt->hasData() && pkt->getPtr<uint8_t>() != nullptr) {
            kv.push_back({"data_fnv", mmuHex(
                fnv1a64(pkt->getPtr<uint8_t>(), pkt->getSize()))});
        }
        const uint64_t parent = it->second.req_event
            ? it->second.req_event : it->second.last_event;
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("memory_response", kv);
        mmu_txn[tid].last_event = eid;
        mmu_txn[tid].resp_event = eid;
        if (it->second.fault_ptag && it->second.fault_ptag == mmu_fault_ptag)
            mmu_fault_response_event = eid;
    }

    void
    CHAOSPropagation::mmuNoteWriteback(o3::DynInst *inst)
    {
        if (!mmuTraceEnabled() || !inst)
            return;
        const uint64_t seq = inst->seqNum;
        const uint64_t tid = mmuTxnForSeq(seq);
        if (!tid || !mmu_traced_seqs.count(seq))
            return;
        mmuAdoptConsumerFault(tid, seq);
        const auto it = mmu_txn.find(tid);
        if (it == mmu_txn.end())
            return;
        std::ostringstream dests;
        std::set<std::pair<int, uint32_t>> own;
        for (int i = 0; i < (int)inst->numDestRegs(); ++i) {
            const PhysRegIdPtr phys = inst->renamedDestIdx(i);
            if (!phys)
                continue;
            const auto key = std::make_pair(phys->classValue(), phys->index());
            own.insert(key);
            mmu_dest_owner[key] = seq;
            if (i)
                dests << ',';
            dests << regClassName(phys->classValue()) << ':'
                  << phys->index();
        }
        mmu_traced_dests[seq] = own;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(it->second.fault_ptag)},
            {"translation_id", std::to_string(tid)},
            {"unique_request_id", std::to_string(it->second.unique_request_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"fault_status", "NoFault"},
            {"field", dests.str()},
            {"corr", CORR_NONE},
        };
        const uint64_t parent = it->second.resp_event
            ? it->second.resp_event : it->second.last_event;
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("rf_writeback", kv);
        mmu_txn[tid].last_event = eid;
        mmu_txn[tid].wb_event = eid;
        if (it->second.fault_ptag && it->second.fault_ptag == mmu_fault_ptag)
            mmu_fault_wb_event = eid;
    }

    void
    CHAOSPropagation::mmuNoteCommit(o3::DynInst *inst)
    {
        if (!mmuTraceEnabled() || !inst)
            return;
        const uint64_t seq = inst->seqNum;
        const bool is_traced = mmu_traced_seqs.count(seq) > 0;

        // A committed instruction that reads a register written by a traced
        // load is a real data consumer. Its parent is the producer's
        // writeback event, never a tick-order guess.
        uint64_t consumer_of = 0;
        uint64_t consumer_parent = 0;
        uint64_t consumer_ptag = 0;
        for (int i = 0; i < (int)inst->numSrcRegs(); ++i) {
            const PhysRegIdPtr phys = inst->renamedSrcIdx(i);
            if (!phys)
                continue;
            const auto it = mmu_dest_owner.find(
                std::make_pair(phys->classValue(), phys->index()));
            if (it == mmu_dest_owner.end())
                continue;
            consumer_of = it->second;
            const uint64_t ptid = mmuTxnForSeq(consumer_of);
            if (ptid) {
                const auto pit = mmu_txn.find(ptid);
                if (pit != mmu_txn.end()) {
                    consumer_parent = pit->second.wb_event
                        ? pit->second.wb_event : pit->second.last_event;
                    consumer_ptag = pit->second.fault_ptag;
                }
            }
            break;
        }
        if (!is_traced && !consumer_of)
            return;

        const uint64_t commit_seq = commit_seq_counter;
        if (consumer_of) {
            std::vector<std::pair<std::string, std::string>> kv = {
                {"fault_id", std::to_string(consumer_ptag)},
                {"dyn_inst_seq", std::to_string(seq)},
                {"request_id", std::to_string(seq)},
                {"commit_seq", std::to_string(commit_seq)},
                {"commit_status", "committed"},
                {"squash_status", "none"},
                {"field", "consumer_of=" + std::to_string(consumer_of)},
                {"corr", CORR_NONE},
            };
            if (inst->pcState().instAddr())
                kv.push_back({"pc", mmuHex(inst->pcState().instAddr())});
            mmuSetParent(kv, consumer_parent);
            const uint64_t ceid = notePropEvt("consumer", kv);
            if (consumer_ptag && consumer_ptag == mmu_fault_ptag)
                mmu_fault_consumer_event = ceid;
            mmu_consumer_seqs.insert(seq);
            // Bounded consumer observation: the first committed consumer of
            // a traced load's destination consumes the ownership entry, so a
            // recycled physical register cannot generate an unbounded
            // consumer fan-out on every later commit.
            for (auto it = mmu_dest_owner.begin();
                 it != mmu_dest_owner.end(); ) {
                if (it->second == consumer_of)
                    it = mmu_dest_owner.erase(it);
                else
                    ++it;
            }
        }

        uint64_t parent = consumer_parent;
        uint64_t tid = 0;
        uint64_t commit_ptag = consumer_ptag;
        if (is_traced) {
            tid = mmuTxnForSeq(seq);
            if (tid) {
                mmuAdoptConsumerFault(tid, seq);
                const auto it = mmu_txn.find(tid);
                if (it != mmu_txn.end()) {
                    parent = it->second.wb_event
                        ? it->second.wb_event : it->second.last_event;
                    commit_ptag = it->second.fault_ptag;
                }
            }
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(commit_ptag)},
            {"translation_id", std::to_string(tid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"commit_seq", std::to_string(commit_seq)},
            {"commit_status", "committed"},
            {"squash_status", "none"},
            {"corr", CORR_NONE},
        };
        if (inst->pcState().instAddr())
            kv.push_back({"pc", mmuHex(inst->pcState().instAddr())});
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("commit", kv);
        if (tid)
            mmu_txn[tid].last_event = eid;
        if (commit_ptag && commit_ptag == mmu_fault_ptag)
            mmu_fault_commit_event = eid;
    }

    void
    CHAOSPropagation::mmuNoteSquash(o3::DynInst *inst)
    {
        if (!mmuTraceEnabled() || !inst)
            return;
        const uint64_t seq = inst->seqNum;
        if (!mmu_traced_seqs.count(seq) && !mmu_consumer_seqs.count(seq))
            return;
        const uint64_t tid = mmuTxnForSeq(seq);
        uint64_t parent = 0;
        if (tid) {
            mmuAdoptConsumerFault(tid, seq);
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end())
                parent = it->second.last_event;
        }
        uint64_t ftid = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end())
                ftid = it->second.fault_ptag;
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"translation_id", std::to_string(tid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"commit_status", "not_committed"},
            {"squash_status", "squashed"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("squash", kv);
        // [Phase 2.2] Remember the real squash witness: the M02 lineage
        // reports whether the ORIGINAL refill instruction was squashed
        // before a later dynamic consumer arrived.
        if (tid)
            mmu_txn[tid].squash_event = eid;
        // [M06] Record the squash of the SPECIFIC faulting instruction (not
        // just any consumer of the same transaction). A fault result whose
        // instruction is squashed before commit is not architecturally
        // delivered; the summary reports both facts separately.
        if (ftid && ftid == mmu_fault_ptag && seq == mmu_fault_origin_seq) {
            mmu_fault_inst_squashed = true;
            if (!mmu_fault_inst_squash_event)
                mmu_fault_inst_squash_event = eid;
        }
    }

    uint64_t
    CHAOSPropagation::mmuNoteFaultStateConsumed(
        const char *model, uint64_t fault_id, uint64_t walk_id,
        uint64_t translation_id, uint64_t seq, Addr va,
        const char *descriptor_type, uint64_t pte_value_before,
        uint64_t pte_value_after, Addr pte_address, bool pte_memory_written,
        uint64_t pte_decode_event)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid)
            tid = mmuTxnForSeqVa(seq, va);
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(fault_id)},
            {"fault_model", model ? model : ""},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"pte_address", mmuHex(pte_address)},
            {"pte_value_before", mmuHex(pte_value_before)},
            {"pte_value_after", mmuHex(pte_value_after)},
            {"descriptor_type", descriptor_type ? descriptor_type : "Unknown"},
            // HONEST memory property: the fault only rewrites the host-order
            // decode copy; the implementation has no guest PTE write-back.
            {"pte_memory_written", pte_memory_written ? "1" : "0"},
            {"pte_decode_event_id", std::to_string(pte_decode_event)},
            {"state_consumed", "1"},
            {"outcome", "state_consumed"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, pte_decode_event);
        const uint64_t eid = notePropEvt("fault_state_consumed", kv);
        // Chain the walk cursor through the consume witness so the following
        // fault_result_propagated descends from it (activation -> decode ->
        // consume -> propagate -> delivery).
        if (walk_id)
            mmu_walk_last[walk_id] = eid;
        if (fault_id && fault_id == mmu_fault_ptag &&
                !mmu_fault_state_consumed_event)
            mmu_fault_state_consumed_event = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteFaultResultPropagated(
        const char *model, uint64_t fault_id, uint64_t walk_id,
        uint64_t translation_id, uint64_t seq, Addr va,
        const char *exception_class, const char *fault_source,
        unsigned fault_source_level, bool is_fetch, bool is_write,
        Addr fault_va, const char *delivery_target)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t tid = translation_id;
        if (!tid)
            tid = mmuTxnForSeqVa(seq, va);
        uint64_t parent = 0;
        const auto wit = mmu_walk_last.find(walk_id);
        if (wit != mmu_walk_last.end())
            parent = wit->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(fault_id)},
            {"fault_model", model ? model : ""},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(tid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"va", mmuHex(va)},
            {"fault_va", mmuHex(fault_va)},
            {"exception_class",
                exception_class ? exception_class : "Unknown"},
            {"fault_source", fault_source ? fault_source : "Unknown"},
            {"fault_source_level", std::to_string(fault_source_level)},
            {"fault_status", "Translation"},
            {"is_fetch", is_fetch ? "1" : "0"},
            {"is_write", is_write ? "1" : "0"},
            // ISV is architecturally 0 for faults on a translation-table
            // walk (ARM ARM DDI0487: ISV=0 for stage-1 table-walk aborts).
            {"isv", "0"},
            {"delivery_target", delivery_target ? delivery_target : "unknown"},
            {"result_propagated", "1"},
            {"outcome", "result_propagated"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("fault_result_propagated", kv);
        if (fault_id && fault_id == mmu_fault_ptag) {
            if (!mmu_fault_result_propagated_event)
                mmu_fault_result_propagated_event = eid;
            mmu_fault_exception_class = exception_class
                ? exception_class : "Unknown";
            mmu_fault_delivery_target = delivery_target
                ? delivery_target : "unknown";
        }
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteExceptionDelivery(uint64_t seq, const char *pc,
                                               const char *exception_class)
    {
        if (!mmuTraceEnabled() || !seq)
            return 0;
        uint64_t tid = mmuTxnForSeq(seq);
        uint64_t ftid = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end())
                ftid = it->second.fault_ptag;
        }
        // Only an injected fault chain has a ptag. A normal guest fault is
        // not part of this trace and stays silent.
        if (!ftid)
            return 0;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(ftid)},
            {"translation_id", std::to_string(tid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"exception_class",
                exception_class ? exception_class : "Unknown"},
            {"delivery_target", mmu_fault_delivery_target.empty()
                ? "unknown" : mmu_fault_delivery_target},
            {"exception_delivered", "1"},
            {"commit_status", "trapped"},
            {"squash_status", "not_committed"},
            {"corr", CORR_NONE},
        };
        if (pc && *pc)
            kv.push_back({"pc", pc});
        mmuSetParent(kv, mmu_fault_result_propagated_event
            ? mmu_fault_result_propagated_event
            : mmu_fault_activation_event);
        const uint64_t eid = notePropEvt("exception_delivery", kv);
        if (ftid == mmu_fault_ptag && !mmu_fault_exception_delivery_event)
            mmu_fault_exception_delivery_event = eid;
        return eid;
    }

    void
    CHAOSPropagation::mmuNoteUnactivated(
        const char *model, const char *reason, Addr va,
        const std::vector<std::pair<std::string, std::string>> &extra)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return;
        std::ostringstream key;
        key << (model ? model : "") << '|' << (reason ? reason : "") << '|'
            << std::hex << va;
        if (!mmu_unactivated_emitted.insert(key.str()).second)
            return;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", "0"},
            {"fault_model", model ? model : ""},
            {"fault_reason", reason ? reason : "unactivated"},
            {"va", mmuHex(va)},
            {"fault_activation_status", "not_activated"},
            {"outcome", "not_activated"},
            {"corr", CORR_NONE},
        };
        for (const auto &p : extra)
            kv.push_back(p);
        notePropEvt("mmu_fault_unactivated", kv);
    }

    uint64_t
    CHAOSPropagation::mmuNoteTlbiIssue(uint64_t tlbi_id, const char *op,
                                       bool stage1, bool stage2)
    {
        if (!mmuTraceEnabled())
            return 0;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", "0"},
            {"tlbi_id", std::to_string(tlbi_id)},
            {"field", op ? op : "TLBI"},
            {"stage", stage2 ? (stage1 ? "1+2" : "2") : "1"},
            {"corr", CORR_NONE},
        };
        const uint64_t eid = notePropEvt("tlbi_issue", kv);
        mmu_tlbi_last[tlbi_id] = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteTlbiMatch(uint64_t tlbi_id,
                                       const std::string &instance,
                                       const char *op, uint64_t entry_id,
                                       uint32_t gen, Addr va, uint16_t asid,
                                       uint16_t vmid, unsigned n,
                                       unsigned regime, unsigned ss,
                                       bool suppressed, uint64_t fault_ptag,
                                       const char *suppress_phase)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t parent = 0;
        const auto it = mmu_tlbi_last.find(tlbi_id);
        if (it != mmu_tlbi_last.end())
            parent = it->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(fault_ptag)},
            {"tlbi_id", std::to_string(tlbi_id)},
            {"tlb_instance", instance},
            {"tlb_entry_id", std::to_string(entry_id)},
            {"entry_generation", std::to_string(gen)},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"page_size_n", std::to_string(n)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"field", op ? op : "TLBI"},
            {"outcome", suppressed ? "matched_suppressed" : "matched"},
            {"state_before", "valid"},
            {"entry_valid", "1"},
            {"entry_partial", "0"},
            {"corr", CORR_NONE},
        };
        if (suppressed) {
            kv.push_back({"entry_generation_after", std::to_string(gen)});
            if (suppress_phase)
                kv.push_back({"fault_reason", suppress_phase});
        }
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("tlbi_match", kv);
        mmu_tlbi_last[tlbi_id] = eid;
        return eid;
    }

    uint64_t
    CHAOSPropagation::mmuNoteTlbiInvalidate(uint64_t tlbi_id,
                                            const std::string &instance,
                                            const char *op, uint64_t entry_id,
                                            uint32_t gen_before,
                                            uint32_t gen_after, Addr va,
                                            uint16_t asid, uint16_t vmid,
                                            unsigned regime, unsigned ss)
    {
        if (!mmuTraceEnabled() || !mmuTraceVa(va))
            return 0;
        uint64_t parent = 0;
        const auto it = mmu_tlbi_last.find(tlbi_id);
        if (it != mmu_tlbi_last.end())
            parent = it->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", "0"},
            {"tlbi_id", std::to_string(tlbi_id)},
            {"tlb_instance", instance},
            {"tlb_entry_id", std::to_string(entry_id)},
            {"entry_generation", std::to_string(gen_before)},
            {"entry_generation_after", std::to_string(gen_after)},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"field", op ? op : "TLBI"},
            {"outcome", "invalidated"},
            {"state_before", "valid"},
            {"state_after", "invalid"},
            {"entry_valid", "0"},
            {"entry_partial", "0"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, parent);
        const uint64_t eid = notePropEvt("tlbi_invalidate", kv);
        mmu_tlbi_last[tlbi_id] = eid;
        mmu_last_tlbi_key[MmuAssocKey{va, asid, vmid, (uint8_t)regime,
                                      (uint8_t)ss}] = eid;
        return eid;
    }

    // ================= MMU fault injection (Phase 2 smoke) =================

    bool
    CHAOSPropagation::mmuFaultModelIs(const char *model) const
    {
        // [Phase 2.2] Injection enablement is decided ONLY by the explicit
        // fault configuration. write_log (generic logging) and mmu_trace
        // (fault-free trace) are observation switches and must never change
        // fault semantics.
        return mmu_fault_enable && mmu_fault_model == model;
    }

    // ================= [MMU-PHASE3] M03-M08 shared API =====================

    bool
    CHAOSPropagation::mmuTargetKeyMatch(Addr va, uint16_t asid, uint16_t vmid,
                                        unsigned n, unsigned regime,
                                        unsigned ss, const char *instance,
                                        int walk_level, const char *mode) const
    {
        if (!mmu_target_instance.empty()) {
            if (!instance || mmu_target_instance != instance)
                return false;
        }
        if (mmu_target_walk_level >= 0 &&
                walk_level != mmu_target_walk_level)
            return false;
        if (!mmu_target_mode.empty()) {
            if (!mode || mmu_target_mode != mode)
                return false;
        }
        if (mmu_target_va != 0) {
            const unsigned shift =
                mmu_target_n >= 0 ? (unsigned)mmu_target_n : 12u;
            if ((va >> shift) != (mmu_target_va >> shift))
                return false;
        }
        if (mmu_target_asid >= 0 && asid != (uint16_t)mmu_target_asid)
            return false;
        if (mmu_target_vmid >= 0 && vmid != (uint16_t)mmu_target_vmid)
            return false;
        if (mmu_target_n >= 0 && (int)n != mmu_target_n)
            return false;
        if (mmu_target_regime >= 0 &&
                regime != (unsigned)mmu_target_regime)
            return false;
        if (mmu_target_ss >= 0 && ss != (unsigned)mmu_target_ss)
            return false;
        return true;
    }

    bool
    CHAOSPropagation::mmuTargetSeqMatch(uint64_t seq) const
    {
        return mmu_target_seq == 0 || seq == mmu_target_seq;
    }

    bool
    CHAOSPropagation::mmuEligibleEvent(unsigned channel)
    {
        if (mmu_eligible_index == 0)
            return true;
        uint64_t &count = mmu_eligible_counts[channel];
        ++count;
        return count == mmu_eligible_index;
    }

    uint64_t
    CHAOSPropagation::mmuBeginConsumerTranslation(uint64_t seq, Addr va,
                                                  const char *mode,
                                                  bool stage2, uint16_t asid,
                                                  uint16_t vmid,
                                                  unsigned regime,
                                                  unsigned ss,
                                                  uint64_t fault_ptag)
    {
        return mmuBeginTxn(seq, va, 0, mode, stage2, asid, vmid, regime, ss,
                           fault_ptag);
    }

    uint64_t
    CHAOSPropagation::mmuFaultActivate(
            const char *model, const char *site, uint64_t translation_id,
            uint64_t seq, Addr va,
            const std::vector<std::pair<std::string, std::string>> &extra)
    {
        if (!mmuFaultModelIs(model))
            return 0;
        // One-shot activation: the first eligible event owns the fault id.
        if (mmu_fault_state != MmuFaultState::Idle)
            return 0;

        uint64_t tid = translation_id;
        if (!tid && seq)
            tid = mmuTxnForSeqVa(seq, va);
        if (!tid && seq && mmuTraceEnabled() && mmuTraceVa(va))
            tid = mmuBeginConsumerTranslation(seq, va, nullptr, false, 0, 0,
                                              0, 0);
        mmu_fault_state = MmuFaultState::Activated;
        mmu_fault_activated = true;
        mmu_fault_ptag = ++next_ptag;
        mmu_fault_va = va;
        mmu_fault_origin_seq = seq;
        mmu_fault_activation_event = 0;
        // [M06] A new fault chain starts with no consumed/propagated/
        // delivered witness. The one-shot latch guarantees this runs once.
        mmu_fault_state_consumed_event = 0;
        mmu_fault_result_propagated_event = 0;
        mmu_fault_exception_delivery_event = 0;
        mmu_fault_exception_class.clear();
        mmu_fault_delivery_target.clear();
        mmu_fault_inst_squashed = false;
        mmu_fault_inst_squash_event = 0;

        uint64_t parent = 0;
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end()) {
                it->second.fault_ptag = mmu_fault_ptag;
                parent = it->second.last_event;
            }
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(mmu_fault_ptag)},
            {"fault_model", model},
            {"fault_site", site ? site : ""},
            {"fault_persistence", mmu_fault_persistence},
            {"va", mmuHex(va)},
            {"translation_id", std::to_string(tid)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"outcome", "activated"},
            {"corr", CORR_NONE},
        };
        for (const auto &p : extra)
            kv.push_back(p);
        mmuSetParent(kv, parent);
        mmu_fault_activation_event = notePropEvt("mmu_fault_activate", kv);
        if (tid) {
            const auto it = mmu_txn.find(tid);
            if (it != mmu_txn.end())
                it->second.last_event = mmu_fault_activation_event;
        }
        printf("[CHAOSPropagation] %s activation: fault_id=%llu site=%s "
               "va=%#llx seq=%llu tid=%llu event=%llu\n",
               model, (unsigned long long)mmu_fault_ptag,
               site ? site : "", (unsigned long long)va,
               (unsigned long long)seq, (unsigned long long)tid,
               (unsigned long long)mmu_fault_activation_event);
        fflush(stdout);
        return mmu_fault_ptag;
    }

    void
    CHAOSPropagation::mmuRegisterEntryFault(const std::string &instance,
                                            uint64_t entry_id,
                                            uint32_t generation,
                                            uint64_t fault_id,
                                            uint64_t source_event,
                                            uint64_t origin_seq, Addr va,
                                            const char *model)
    {
        if (!fault_id)
            return;
        MmuEntryLineageKey key{instance, entry_id, generation};
        MmuEntryFaultRecord rec;
        rec.fault_id = fault_id;
        rec.source_event = source_event;
        rec.origin_seq = origin_seq;
        rec.va = va;
        rec.model = model ? model : "";
        mmu_entry_faults[key] = rec;
    }

    uint64_t
    CHAOSPropagation::mmuEntryFaultPtag(const std::string &instance,
                                        uint64_t entry_id,
                                        uint32_t generation) const
    {
        const auto it = mmu_entry_faults.find(
            MmuEntryLineageKey{instance, entry_id, generation});
        return it == mmu_entry_faults.end() ? 0 : it->second.fault_id;
    }

    uint64_t
    CHAOSPropagation::mmuNoteEntryConsume(const char *kind,
                                          const std::string &instance,
                                          uint64_t entry_id,
                                          uint32_t generation, Addr va,
                                          uint16_t asid, uint16_t vmid,
                                          unsigned n, unsigned regime,
                                          unsigned ss, uint64_t seq,
                                          const char *mode,
                                          uint64_t lookup_event)
    {
        const MmuEntryLineageKey key{instance, entry_id, generation};
        const auto it = mmu_entry_faults.find(key);
        if (it == mmu_entry_faults.end())
            return 0;
        MmuEntryFaultRecord &rec = it->second;
        ++rec.reuse_count;
        ++mmu_entry_fault_consume_count;
        if (rec.fault_id == mmu_fault_ptag) {
            if (!mmu_fault_lineage_consume_event) {
                mmu_fault_lineage_consume_event = 0;   // filled below
                mmu_fault_lineage_consumer_seq = seq;
            }
            mmu_fault_consumed = true;
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(rec.fault_id)},
            {"fault_model", rec.model},
            {"fault_persistence", "entry_lifetime"},
            {"tlb_instance", instance},
            {"tlb_entry_id", std::to_string(entry_id)},
            {"entry_generation", std::to_string(generation)},
            {"retained_entry_id", std::to_string(entry_id)},
            {"retained_entry_generation", std::to_string(generation)},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"page_size_n", std::to_string(n)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"origin_dyn_inst_seq", std::to_string(rec.origin_seq)},
            {"mode", mode ? mode : ""},
            {"source_event_id", std::to_string(rec.source_event)},
            {"lookup_event_id", std::to_string(lookup_event)},
            {"lineage_state", "consumed"},
            {"reuse_ordinal", std::to_string(rec.reuse_count)},
            {"consumption_event_id", std::to_string(lookup_event)},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, lookup_event);
        const uint64_t eid = notePropEvt(kind ? kind : "fault_entry_consume",
                                         kv);
        if (rec.fault_id == mmu_fault_ptag) {
            if (!mmu_fault_lineage_consume_event)
                mmu_fault_lineage_consume_event = eid;
            if (mmu_fault_result_event == 0 && lookup_event)
                mmu_fault_result_event = lookup_event;
        }
        return eid;
    }

    CHAOSPropagation::MmuM01Decision
    CHAOSPropagation::mmuM01OnTlbiMatch(const std::string &instance, Addr va,
                                        uint16_t asid, uint16_t vmid,
                                        unsigned n, bool valid, bool partial,
                                        unsigned regime, unsigned ss,
                                        uint64_t tlbi_id, uint64_t entry_id,
                                        uint32_t generation, const char *op)
    {
        MmuM01Decision d;
        if (!mmuFaultModelIs("M01") || instance != "l2_shared")
            return d;
        if (mmu_fault_state == MmuFaultState::Consumed ||
                mmu_fault_state == MmuFaultState::Activated)
            return d;
        if (!valid || partial || n != mmu_m01_n || va != mmu_m01_va)
            return d;
        if (mmu_m01_asid >= 0 && asid != (uint16_t)mmu_m01_asid)
            return d;
        if (mmu_m01_vmid >= 0 && vmid != (uint16_t)mmu_m01_vmid)
            return d;
        // [MMU-TRACE v3] A match from a different translation regime or
        // security state must never arm this fault, even for the same
        // VA/ASID/VMID (aliasing regimes are architecturally distinct).
        if (mmu_m01_regime >= 0 && regime != (unsigned)mmu_m01_regime)
            return d;
        if (mmu_m01_ss >= 0 && ss != (unsigned)mmu_m01_ss)
            return d;

        if (mmu_fault_state == MmuFaultState::Idle) {
            // Entry identity is mandatory: without a stable non-zero
            // EntryID/Generation the retained lifetime cannot be proven.
            if (entry_id == 0)
                return d;
            mmu_fault_state = MmuFaultState::Armed;
            mmu_fault_armed = true;
            mmu_fault_ptag = ++next_ptag;
            mmu_fault_entry_id = entry_id;
            mmu_fault_entry_generation = generation;
            mmu_fault_va = va;
            mmu_fault_asid = asid;
            mmu_fault_vmid = vmid;
            mmu_fault_regime = (uint8_t)regime;
            mmu_fault_ss = (uint8_t)ss;
            mmu_fault_n = n;
            mmu_fault_first_tlbi_id = tlbi_id;
            mmu_fault_tlbi_op = op ? op : "TLBI";
            mmu_fault_suppress_count = 0;
            mmu_fault_suppressed_tlbi_ids.clear();

            // [MMU-TRACE v3] Do NOT emit mmu_fault_arm here. The caller has
            // not emitted tlbi_match yet; emitting now would (a) invert the
            // causal order and (b) make the match's parent the arm event.
            // The arm event is emitted by mmuM01EmitArm() after the match.
            d.suppress = true;
            d.first_arm = true;
            d.fault_id = mmu_fault_ptag;
            d.arm_event = 0;
            return d;
        }

        // Armed: suppress only the SAME retained lifetime. [Phase 2.2] The
        // armed branch must enforce the SAME complete identity as arming:
        //   TLBInstance + EntryID + Generation + VA + ASID + VMID +
        //   PageSizeN + Regime + SecurityState.
        // Phase 2.1 re-checked only the first six, so an aliasing page-size /
        // regime / security-state match could be suppressed by mistake.
        if (!mmu_fault_armed || entry_id != mmu_fault_entry_id ||
                generation != mmu_fault_entry_generation || va != mmu_fault_va ||
                asid != mmu_fault_asid || vmid != mmu_fault_vmid ||
                n != mmu_fault_n || regime != mmu_fault_regime ||
                ss != mmu_fault_ss)
            return d;
        d.suppress = true;
        d.fault_id = mmu_fault_ptag;
        d.arm_event = mmu_fault_arm_event;
        return d;
    }

    uint64_t
    CHAOSPropagation::mmuM01EmitArm(uint64_t match_event)
    {
        if (!mmuFaultModelIs("M01") || !mmu_fault_armed ||
                mmu_fault_arm_event != 0)
            return 0;
        // The match event is the real cause of this arm; never infer it
        // from tick order. With tracing disabled there is no match event,
        // so the lifecycle stays silent (state transitions are unchanged).
        if (match_event == 0)
            return 0;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(mmu_fault_ptag)},
            {"fault_model", "M01"},
            {"fault_field", "retain_l2_complete_invalidation"},
            {"fault_reason", "first_exact_key_tlbi_match"},
            {"field", mmu_fault_tlbi_op},
            {"tlbi_id", std::to_string(mmu_fault_first_tlbi_id)},
            {"first_tlbi_id", std::to_string(mmu_fault_first_tlbi_id)},
            {"tlb_instance", "l2_shared"},
            {"retained_entry_id", std::to_string(mmu_fault_entry_id)},
            {"retained_entry_generation",
                std::to_string(mmu_fault_entry_generation)},
            {"tlb_entry_id", std::to_string(mmu_fault_entry_id)},
            {"entry_generation", std::to_string(mmu_fault_entry_generation)},
            {"entry_generation_after",
                std::to_string(mmu_fault_entry_generation)},
            {"entry_valid", "1"},
            {"entry_partial", "0"},
            {"va", mmuHex(mmu_fault_va)},
            {"asid", std::to_string(mmu_fault_asid)},
            {"vmid", std::to_string(mmu_fault_vmid)},
            {"page_size_n", std::to_string(mmu_fault_n)},
            {"regime", mmuRegimeName(mmu_fault_regime)},
            {"security_state", mmuSecurityStateName(mmu_fault_ss)},
            {"outcome", "armed"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, match_event);
        mmu_fault_arm_event = notePropEvt("mmu_fault_arm", kv);
        if (mmu_fault_arm_event) {
            mmu_tlbi_last[mmu_fault_first_tlbi_id] = mmu_fault_arm_event;
            mmu_last_tlbi_key[MmuAssocKey{mmu_fault_va, mmu_fault_asid,
                    mmu_fault_vmid, mmu_fault_regime, mmu_fault_ss}] =
                mmu_fault_arm_event;
        }
        return mmu_fault_arm_event;
    }

    void
    CHAOSPropagation::mmuM01NoteSuppressed(const std::string &instance,
                                           Addr va, uint16_t asid,
                                           uint16_t vmid, unsigned n,
                                           unsigned regime, unsigned ss,
                                           uint64_t tlbi_id, uint64_t entry_id,
                                           uint32_t generation, const char *op,
                                           uint64_t match_event)
    {
        if (!mmuFaultModelIs("M01") || !mmu_fault_armed)
            return;
        ++mmu_fault_suppress_count;
        mmu_fault_suppressed_tlbi_ids.push_back(tlbi_id);
        std::ostringstream ids;
        for (size_t i = 0; i < mmu_fault_suppressed_tlbi_ids.size(); ++i) {
            if (i)
                ids << ',';
            ids << mmu_fault_suppressed_tlbi_ids[i];
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(mmu_fault_ptag)},
            {"fault_model", "M01"},
            {"fault_field", "tlbi_invalidation_suppressed"},
            {"fault_reason", "armed_maintenance_window"},
            {"field", op ? op : "TLBI"},
            {"tlbi_id", std::to_string(tlbi_id)},
            {"first_tlbi_id", std::to_string(mmu_fault_first_tlbi_id)},
            {"suppressed_tlbi_ids", ids.str()},
            {"suppress_count", std::to_string(mmu_fault_suppress_count)},
            {"fault_arm_event_id", std::to_string(mmu_fault_arm_event)},
            {"match_event_id", std::to_string(match_event)},
            {"tlb_instance", instance},
            {"retained_entry_id", std::to_string(mmu_fault_entry_id)},
            {"retained_entry_generation",
                std::to_string(mmu_fault_entry_generation)},
            {"tlb_entry_id", std::to_string(entry_id)},
            {"entry_generation", std::to_string(generation)},
            {"entry_generation_after", std::to_string(generation)},
            {"entry_valid", "1"},
            {"entry_partial", "0"},
            {"va", mmuHex(va)},
            {"asid", std::to_string(asid)},
            {"vmid", std::to_string(vmid)},
            {"page_size_n", std::to_string(n)},
            {"regime", mmuRegimeName(regime)},
            {"security_state", mmuSecurityStateName(ss)},
            {"state_before", "valid"},
            {"state_after", "valid_retained"},
            {"outcome", "suppressed"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, match_event);
        const uint64_t eid = notePropEvt("tlbi_suppressed", kv);
        mmu_tlbi_last[tlbi_id] = eid;
        mmu_fault_last_suppressed_event = eid;
        mmu_last_tlbi_key[MmuAssocKey{va, asid, vmid, (uint8_t)regime,
                                      (uint8_t)ss}] = eid;
    }

    bool
    CHAOSPropagation::mmuM01Consume(const std::string &instance, Addr va,
                                    uint16_t asid, uint16_t vmid, unsigned n,
                                    unsigned regime, unsigned ss,
                                    uint64_t entry_id, uint32_t generation,
                                    uint64_t translation_id,
                                    uint64_t *fault_ptag)
    {
        if (!mmuFaultModelIs("M01") || !mmu_fault_armed ||
                mmu_fault_state != MmuFaultState::Armed ||
                instance != "l2_shared")
            return false;
        if (va != mmu_fault_va || asid != mmu_fault_asid ||
                vmid != mmu_fault_vmid || n != mmu_fault_n ||
                regime != mmu_fault_regime || ss != mmu_fault_ss ||
                entry_id != mmu_fault_entry_id ||
                generation != mmu_fault_entry_generation)
            return false;

        mmu_fault_state = MmuFaultState::Consumed;
        mmu_fault_armed = false;
        mmu_fault_consumed = true;
        if (fault_ptag)
            *fault_ptag = mmu_fault_ptag;
        if (translation_id) {
            mmu_txn[translation_id].fault_ptag = mmu_fault_ptag;
            if (!mmu_fault_result_event)
                mmu_fault_result_event = 0;   // filled by translation_result
        }
        printf("[CHAOSPropagation] M01 retained l2_shared entry consumed: "
               "entry=%llu gen=%u va=%#llx asid=%u -> fault_id=%llu\n",
               (unsigned long long)entry_id, generation,
               (unsigned long long)va, (unsigned)asid,
               (unsigned long long)mmu_fault_ptag);
        fflush(stdout);
        return true;
    }

    void
    CHAOSPropagation::mmuM01EmitDisarm(uint64_t fault_ptag,
                                        uint64_t consume_event)
    {
        if (!mmuFaultModelIs("M01") || fault_ptag == 0 ||
                fault_ptag != mmu_fault_ptag || !mmu_fault_consumed)
            return;
        mmu_fault_consume_event = consume_event;
        std::ostringstream ids;
        for (size_t i = 0; i < mmu_fault_suppressed_tlbi_ids.size(); ++i) {
            if (i)
                ids << ',';
            ids << mmu_fault_suppressed_tlbi_ids[i];
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(mmu_fault_ptag)},
            {"fault_model", "M01"},
            {"fault_field", "stale_entry_consumed"},
            {"fault_reason", "first_post_maintenance_translation"},
            {"fault_arm_event_id", std::to_string(mmu_fault_arm_event)},
            {"first_tlbi_id", std::to_string(mmu_fault_first_tlbi_id)},
            {"suppressed_tlbi_ids", ids.str()},
            {"suppress_count", std::to_string(mmu_fault_suppress_count)},
            {"consumption_event_id", std::to_string(consume_event)},
            {"retained_entry_id", std::to_string(mmu_fault_entry_id)},
            {"retained_entry_generation",
                std::to_string(mmu_fault_entry_generation)},
            {"tlb_entry_id", std::to_string(mmu_fault_entry_id)},
            {"entry_generation", std::to_string(mmu_fault_entry_generation)},
            {"va", mmuHex(mmu_fault_va)},
            {"asid", std::to_string(mmu_fault_asid)},
            {"vmid", std::to_string(mmu_fault_vmid)},
            {"page_size_n", std::to_string(mmu_fault_n)},
            {"regime", mmuRegimeName(mmu_fault_regime)},
            {"security_state", mmuSecurityStateName(mmu_fault_ss)},
            {"consumed", "1"},
            {"outcome", "consumed"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, consume_event);
        mmu_fault_disarm_event = notePropEvt("mmu_fault_disarm", kv);
        printf("[CHAOSPropagation] M01 disarm: fault_id=%llu suppress_count=%llu "
               "consume_event=%llu\n",
               (unsigned long long)mmu_fault_ptag,
               (unsigned long long)mmu_fault_suppress_count,
               (unsigned long long)consume_event);
        fflush(stdout);
    }

    bool
    CHAOSPropagation::mmuM02ShouldCorrupt(Addr va, Addr pfn, unsigned n,
                                          bool stage2, bool is_data,
                                          bool is_page, bool long_desc)
    {
        if (!mmuFaultModelIs("M02") ||
                mmu_fault_state != MmuFaultState::Idle)
            return false;
        if (stage2 || !is_data || !is_page || !long_desc)
            return false;
        if (n != 12 || va != mmu_m02_va || pfn != mmu_m02_old_pfn)
            return false;
        const Addr old_pa = pfn << n;
        const Addr new_pa = (pfn ^ mmu_m02_xor_mask) << n;
        if (old_pa < mmu_m02_dram_lo || old_pa >= mmu_m02_dram_hi ||
                new_pa < mmu_m02_dram_lo || new_pa >= mmu_m02_dram_hi)
            return false;

        mmu_fault_state = MmuFaultState::Activated;
        mmu_fault_activated = true;
        mmu_fault_ptag = ++next_ptag;
        mmu_fault_va = va;
        mmu_fault_n = n;
        mmu_fault_entry_id = 0;
        mmu_fault_entry_generation = 0;
        mmu_fault_new_pfn = pfn ^ mmu_m02_xor_mask;
        mmu_fault_old_pa = old_pa;
        mmu_fault_new_pa = new_pa;
        return true;
    }

    void
    CHAOSPropagation::mmuM02NoteActivation(uint64_t walk_id,
                                           uint64_t translation_id,
                                           uint64_t unique_id, uint64_t seq,
                                           Addr va, Addr old_pfn, Addr new_pfn,
                                           unsigned n, uint64_t descriptor_raw,
                                           Addr pte_addr, uint64_t walk_event,
                                           const char *mode)
    {
        if (!mmuFaultModelIs("M02") ||
                mmu_fault_state != MmuFaultState::Activated)
            return;
        if (translation_id) {
            mmu_txn[translation_id].fault_ptag = mmu_fault_ptag;
            if (!unique_id)
                unique_id = mmu_txn[translation_id].unique_request_id;
        }
        const Addr old_pa = old_pfn << n;
        const Addr new_pa = new_pfn << n;
        // [Phase 2.2] The origin instruction's real squash witness (if it
        // was squashed before the walk completed). Read from its own
        // transaction; never inferred from tick order.
        uint64_t origin_squash = 0;
        if (translation_id) {
            const auto t = mmu_txn.find(translation_id);
            if (t != mmu_txn.end())
                origin_squash = t->second.squash_event;
        }
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(mmu_fault_ptag)},
            {"fault_model", "M02"},
            {"fault_field", "refill_pfn_xor_bit0"},
            {"fault_reason", "local_refill_payload_only"},
            {"walk_id", std::to_string(walk_id)},
            {"translation_id", std::to_string(translation_id)},
            {"unique_request_id", std::to_string(unique_id)},
            {"dyn_inst_seq", std::to_string(seq)},
            {"request_id", std::to_string(seq)},
            {"origin_dyn_inst_seq", std::to_string(seq)},
            {"origin_squashed", origin_squash ? "1" : "0"},
            {"origin_squash_event_id", std::to_string(origin_squash)},
            {"va", mmuHex(va)},
            {"old_pfn", mmuHex(old_pfn)},
            {"new_pfn", mmuHex(new_pfn)},
            {"old_pa", mmuHex(old_pa)},
            {"new_pa", mmuHex(new_pa)},
            {"before", mmuHex(old_pfn)},
            {"after", mmuHex(new_pfn)},
            {"page_size_n", std::to_string(n)},
            {"stage", "1"},
            {"mode", mode ? mode : "Read"},
            {"pte_address", mmuHex(pte_addr)},
            {"pte_value_before", mmuHex(descriptor_raw)},
            {"pte_value_after", mmuHex(descriptor_raw)},
            {"pte_recheck", "descriptor_unchanged"},
            {"descriptor_type", "Page"},
            {"outcome", "activated"},
            {"corr", CORR_NONE},
        };
        mmuSetParent(kv, walk_event);
        mmu_fault_activation_event = notePropEvt("refill_pfn_corrupt", kv);

        // [Phase 2.2] Publish the pending corrupted refill. TLB::insert
        // registers one lineage record per layer whose inserted payload
        // matches this walk/VA/N/new-PFN exactly.
        mmu_m02_pending.active = true;
        mmu_m02_pending.ptag = mmu_fault_ptag;
        mmu_m02_pending.activation_event = mmu_fault_activation_event;
        mmu_m02_pending.translation_id = translation_id;
        mmu_m02_pending.unique_id = unique_id;
        mmu_m02_pending.walk_id = walk_id;
        mmu_m02_pending.seq = seq;
        mmu_m02_pending.va = va;
        mmu_m02_pending.n = n;
        mmu_m02_pending.old_pfn = old_pfn;
        mmu_m02_pending.new_pfn = new_pfn;
        mmu_m02_pending.old_pa = old_pa;
        mmu_m02_pending.new_pa = new_pa;
        // The corrupted refill is now the causal parent of the entry that
        // mmu->insert writes next (same translation cursor).
        if (translation_id && mmu_fault_activation_event)
            mmu_txn[translation_id].last_event = mmu_fault_activation_event;
        printf("[CHAOSPropagation] M02 refill PFN corrupted: fault_id=%llu "
               "walk=%llu pfn %#llx -> %#llx (PA %#llx -> %#llx)\n",
               (unsigned long long)mmu_fault_ptag,
               (unsigned long long)walk_id,
               (unsigned long long)old_pfn, (unsigned long long)new_pfn,
               (unsigned long long)old_pa, (unsigned long long)new_pa);
        fflush(stdout);
    }

    // ================= [Phase 2.2] M02 entry lineage ======================
    //
    // The registry is keyed by the REAL inserted entry identity
    // (instance, entry_id, generation). It is deliberately INDEPENDENT of
    // DynamicInstSeqNum: the original walk/refill may be squashed, and a
    // later, different dynamic instruction may consume the exact same
    // corrupted entry. Neither VA/PA equality nor tick proximity is used to
    // join a consumer; the entry identity is the join key, and the emitted
    // witness carries both causal endpoints (origin insert/refill event and
    // the consumer's own lookup event).

    uint64_t
    CHAOSPropagation::mmuM02FindLineage(const std::string &instance,
                                        uint64_t entry_id, uint32_t gen,
                                        Addr va, uint16_t asid, uint16_t vmid,
                                        unsigned n, unsigned regime,
                                        unsigned ss, Addr pfn, uint64_t seq,
                                        const char *mode, bool functional,
                                        uint64_t *tid_out)
    {
        mmu_m02_consume_pending.active = false;
        if (tid_out)
            *tid_out = 0;
        if (!mmuTraceEnabled() || !mmuTraceVa(va) || functional || seq == 0)
            return 0;
        const MmuEntryLineageKey key{instance, entry_id, gen};
        auto it = mmu_entry_lineage.find(key);
        if (it == mmu_entry_lineage.end())
            return 0;
        const MmuEntryLineage &lin = it->second;
        // The FULL architectural key must match the recorded lifetime. An
        // entry-id reuse with a different VA/ASID/VMID/regime/security state/
        // page size is a different translation and must not inherit the
        // fault, even if the slot number coincides.
        if (lin.fault_id == 0 || pfn != lin.new_pfn || n != lin.n ||
                asid != lin.asid || vmid != lin.vmid ||
                regime != lin.regime || ss != lin.ss)
            return 0;
        if (n >= 64 || (va >> n) != (lin.va >> n))
            return 0;

        // The consuming dynamic instruction gets its OWN translation
        // transaction. A warm hit by a younger instruction has none (that
        // was exactly the Phase 2.1 drop); it is created here with the fault
        // stamped before translation_start is emitted.
        // Key the consumer transaction by (dyn_seq, VA): an instruction may
        // perform several accesses, and each VA keeps its own translation
        // attempt. Falling back to "the instruction's last transaction"
        // would merge two different VAs of one dynamic instruction.
        uint64_t tid = mmuTxnForSeqVa(seq, va);
        if (tid) {
            mmu_txn[tid].fault_ptag = lin.fault_id;
        } else {
            tid = mmuBeginTxn(seq, va, 0, mode, false, asid, vmid, regime, ss,
                              lin.fault_id);
        }
        if (!tid)
            return 0;   // outside the VA-gated trace: no consumer evidence

        MmuM02ConsumePending &p = mmu_m02_consume_pending;
        p.active = true;
        p.ptag = lin.fault_id;
        p.tid = tid;
        p.uid = mmuUniqueId(tid);
        p.seq = seq;
        p.attempt = mmu_txn[tid].attempt;
        p.instance = instance;
        p.entry_id = entry_id;
        p.generation = gen;
        p.va = va;
        p.pfn = pfn;
        p.pa = pfn << n;
        p.asid = asid;
        p.vmid = vmid;
        p.n = n;
        p.regime = regime;
        p.ss = ss;
        p.reuse_ordinal = lin.reuse_count + 1;

        // Cache/response hooks that only know the Request sequence inherit
        // the fault through this real TLB-consumption record.
        mmu_consumer_seq_ptag[seq] = lin.fault_id;
        mmu_consumer_seq_tid[seq] = tid;

        if (tid_out)
            *tid_out = tid;
        return lin.fault_id;
    }

    void
    CHAOSPropagation::mmuM02NoteConsume(uint64_t lookup_event)
    {
        MmuM02ConsumePending &p = mmu_m02_consume_pending;
        if (!p.active)
            return;
        p.active = false;
        if (!mmuTraceEnabled())
            return;
        const MmuEntryLineageKey key{p.instance, p.entry_id, p.generation};
        auto it = mmu_entry_lineage.find(key);
        if (it == mmu_entry_lineage.end())
            return;
        MmuEntryLineage &lin = it->second;
        // The origin instruction may be squashed; report its REAL witness.
        uint64_t origin_squash = 0;
        if (lin.origin_translation_id) {
            const auto t = mmu_txn.find(lin.origin_translation_id);
            if (t != mmu_txn.end())
                origin_squash = t->second.squash_event;
        }
        const bool reuse = p.reuse_ordinal > 1;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(p.ptag)},
            {"fault_model", "M02"},
            {"fault_field", "corrupted_entry_consumed"},
            {"fault_reason", reuse ? "same_entry_lifetime_reuse"
                                   : "same_entry_lifetime_first_consume"},
            {"lineage_state", "consumed"},
            {"reuse_ordinal", std::to_string(p.reuse_ordinal)},
            {"tlb_instance", p.instance},
            {"tlb_entry_id", std::to_string(p.entry_id)},
            {"entry_generation", std::to_string(p.generation)},
            {"entry_valid", "1"},
            {"entry_partial", "0"},
            {"va", mmuHex(p.va)},
            {"asid", std::to_string(p.asid)},
            {"vmid", std::to_string(p.vmid)},
            {"page_size_n", std::to_string(p.n)},
            {"regime", mmuRegimeName(p.regime)},
            {"security_state", mmuSecurityStateName(p.ss)},
            {"pfn", mmuHex(p.pfn)},
            {"pa", mmuHex(p.pa)},
            {"dyn_inst_seq", std::to_string(p.seq)},
            {"request_id", std::to_string(p.seq)},
            {"translation_id", std::to_string(p.tid)},
            {"unique_request_id", std::to_string(p.uid)},
            {"execution_attempt_id", std::to_string(p.attempt)},
            {"replay_generation", p.attempt > 1 ? "1" : "0"},
            {"lookup_event_id", std::to_string(lookup_event)},
            {"source_event_id", std::to_string(lin.insert_event)},
            {"entry_insert_event_id", std::to_string(lin.insert_event)},
            {"origin_event_id", std::to_string(lin.origin_event)},
            {"origin_translation_id",
                std::to_string(lin.origin_translation_id)},
            {"origin_walk_id", std::to_string(lin.origin_walk_id)},
            {"origin_dyn_inst_seq", std::to_string(lin.origin_seq)},
            {"origin_squashed", origin_squash ? "1" : "0"},
            {"origin_squash_event_id", std::to_string(origin_squash)},
            {"old_pfn", mmuHex(lin.old_pfn)},
            {"new_pfn", mmuHex(lin.new_pfn)},
            {"old_pa", mmuHex(lin.old_pa)},
            {"new_pa", mmuHex(lin.new_pa)},
            {"outcome", reuse ? "reused_by_later_dynamic_inst"
                              : "consumed_by_dynamic_inst"},
            {"corr", CORR_ENTRY_LINEAGE},
        };
        mmuSetParent(kv, lookup_event);
        const uint64_t eid = notePropEvt(
            reuse ? "fault_entry_reuse" : "fault_entry_consume", kv);
        lin.last_event = eid;
        lin.reuse_count = p.reuse_ordinal;
        if (mmu_fault_lineage_consume_event == 0) {
            mmu_fault_lineage_consume_event = eid;
            mmu_fault_lineage_consumer_seq = p.seq;
        }
        printf("[CHAOSPropagation] M02 fault entry %s: fault_id=%llu "
               "%s entry=%llu gen=%u va=%#llx pa=%#llx dyn_seq=%llu "
               "(origin seq=%llu squash_event=%llu)\n",
               reuse ? "reused" : "consumed",
               (unsigned long long)p.ptag, p.instance.c_str(),
               (unsigned long long)p.entry_id, p.generation,
               (unsigned long long)p.va, (unsigned long long)p.pa,
               (unsigned long long)p.seq,
               (unsigned long long)lin.origin_seq,
               (unsigned long long)origin_squash);
        fflush(stdout);
    }

    void
    CHAOSPropagation::mmuEndEntryLineage(const std::string &instance,
                                         uint64_t entry_id, uint32_t gen,
                                         const char *reason,
                                         uint64_t parent_event)
    {
        if (!mmuTraceEnabled() || entry_id == 0)
            return;
        MmuEntryLineageKey key{instance, entry_id, gen};
        auto it = mmu_entry_lineage.find(key);
        if (it == mmu_entry_lineage.end()) {
            // [Phase 2.2] A physical slot may be invalidated several times
            // before it is replaced, so the victim's CURRENT generation can
            // be newer than the corrupted lifetime's generation. The slot
            // identity (instance + entry_id) is unique; close that slot's
            // outstanding lineage. Lookups still match the EXACT
            // (entry_id, generation), so no newer entry inherits the fault.
            for (auto sit = mmu_entry_lineage.begin();
                    sit != mmu_entry_lineage.end(); ++sit) {
                if (sit->first.instance == instance &&
                        sit->first.entry_id == entry_id) {
                    it = sit;
                    key = sit->first;
                    break;
                }
            }
        }
        if (it == mmu_entry_lineage.end())
            return;
        const MmuEntryLineage lin = it->second;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(lin.fault_id)},
            {"fault_model", "M02"},
            {"fault_field", "corrupted_entry_lifetime_ended"},
            {"fault_reason", reason ? reason : "invalidated"},
            {"lineage_state", "ended"},
            {"tlb_instance", instance},
            {"tlb_entry_id", std::to_string(entry_id)},
            // The corrupted lifetime's generation (not the drifted slot gen).
            {"entry_generation", std::to_string(key.generation)},
            {"entry_generation_after", std::to_string(gen + 1)},
            {"entry_valid", "0"},
            {"va", mmuHex(lin.va)},
            {"asid", std::to_string(lin.asid)},
            {"vmid", std::to_string(lin.vmid)},
            {"page_size_n", std::to_string(lin.n)},
            {"regime", mmuRegimeName(lin.regime)},
            {"security_state", mmuSecurityStateName(lin.ss)},
            {"source_event_id", std::to_string(lin.insert_event)},
            {"entry_insert_event_id", std::to_string(lin.insert_event)},
            {"origin_event_id", std::to_string(lin.origin_event)},
            {"reuse_ordinal", std::to_string(lin.reuse_count)},
            {"outcome", "lineage_ended"},
            {"corr", CORR_ENTRY_LINEAGE},
        };
        mmuSetParent(kv, parent_event ? parent_event : lin.last_event);
        notePropEvt("fault_entry_end", kv);
        mmu_entry_lineage.erase(it);
    }

    void
    CHAOSPropagation::mmuM02NotePromotion(const std::string &new_instance,
                                          uint64_t new_entry_id,
                                          uint32_t new_gen,
                                          const std::string &src_instance,
                                          uint64_t src_entry_id,
                                          uint32_t src_gen,
                                          uint64_t insert_event)
    {
        if (!mmuTraceEnabled() || new_entry_id == 0)
            return;
        const MmuEntryLineageKey skey{src_instance, src_entry_id, src_gen};
        auto it = mmu_entry_lineage.find(skey);
        if (it == mmu_entry_lineage.end())
            return;
        MmuEntryLineage lin = it->second;
        lin.insert_event = insert_event;
        lin.last_event = insert_event;
        lin.reuse_count = 0;
        mmu_entry_lineage[MmuEntryLineageKey{new_instance, new_entry_id,
                                             new_gen}] = lin;
        std::vector<std::pair<std::string, std::string>> kv = {
            {"fault_id", std::to_string(lin.fault_id)},
            {"fault_model", "M02"},
            {"fault_field", "corrupted_entry_promoted"},
            {"fault_reason", "tlb_layer_promotion"},
            {"lineage_state", "inserted"},
            {"tlb_instance", new_instance},
            {"tlb_entry_id", std::to_string(new_entry_id)},
            {"entry_generation", std::to_string(new_gen)},
            {"va", mmuHex(lin.va)},
            {"asid", std::to_string(lin.asid)},
            {"vmid", std::to_string(lin.vmid)},
            {"page_size_n", std::to_string(lin.n)},
            {"regime", mmuRegimeName(lin.regime)},
            {"security_state", mmuSecurityStateName(lin.ss)},
            {"pfn", mmuHex(lin.new_pfn)},
            {"pa", mmuHex(lin.new_pa)},
            {"source_event_id", std::to_string(lin.insert_event)},
            {"entry_insert_event_id", std::to_string(insert_event)},
            {"origin_event_id", std::to_string(lin.origin_event)},
            {"origin_translation_id",
                std::to_string(lin.origin_translation_id)},
            {"origin_walk_id", std::to_string(lin.origin_walk_id)},
            {"outcome", "promoted_from_source_entry"},
            {"corr", CORR_ENTRY_LINEAGE},
        };
        mmuSetParent(kv, insert_event);
        const uint64_t eid = notePropEvt("fault_entry_promote", kv);
        mmu_entry_lineage[MmuEntryLineageKey{new_instance, new_entry_id,
                                             new_gen}].last_event = eid;
        if (lin.fault_id == mmu_fault_ptag && mmu_fault_entry_id == 0) {
            mmu_fault_entry_id = new_entry_id;
            mmu_fault_entry_generation = new_gen;
        }
    }

    void
    CHAOSPropagation::mmuFaultExitReport()
    {
        // [Phase 2.2] The honest exit report belongs to the fault
        // configuration, not to generic logging. notePropEvt still no-ops
        // when the stream itself is disabled, so a disabled logger can
        // never emit a partial row.
        if (!mmu_fault_enable || mmu_fault_model.empty())
            return;
        if (mmu_fault_model == "M01") {
            if (mmu_fault_state == MmuFaultState::Idle) {
                notePropEvt("mmu_fault_unactivated", {
                    {"fault_id", "0"},
                    {"fault_model", "M01"},
                    {"fault_reason", "no_eligible_tlbi_match"},
                    {"outcome", "not_activated"},
                    {"suppress_count", "0"},
                    {"corr", CORR_NONE},
                });
            } else if (!mmu_fault_consumed) {
                std::ostringstream ids;
                for (size_t i = 0; i < mmu_fault_suppressed_tlbi_ids.size();
                        ++i) {
                    if (i)
                        ids << ',';
                    ids << mmu_fault_suppressed_tlbi_ids[i];
                }
                notePropEvt("mmu_fault_unconsumed", {
                    {"fault_id", std::to_string(mmu_fault_ptag)},
                    {"fault_model", "M01"},
                    {"fault_reason", "retained_entry_not_consumed_in_roi"},
                    {"fault_arm_event_id",
                        std::to_string(mmu_fault_arm_event)},
                    {"first_tlbi_id",
                        std::to_string(mmu_fault_first_tlbi_id)},
                    {"suppressed_tlbi_ids", ids.str()},
                    {"suppress_count",
                        std::to_string(mmu_fault_suppress_count)},
                    {"retained_entry_id",
                        std::to_string(mmu_fault_entry_id)},
                    {"retained_entry_generation",
                        std::to_string(mmu_fault_entry_generation)},
                    {"va", mmuHex(mmu_fault_va)},
                    {"asid", std::to_string(mmu_fault_asid)},
                    {"vmid", std::to_string(mmu_fault_vmid)},
                    {"consumed", "0"},
                    {"outcome", "unconsumed"},
                    {"corr", CORR_NONE},
                });
            }
        }
        if (mmu_fault_model == "M02") {
            if (mmu_fault_state == MmuFaultState::Idle) {
                notePropEvt("mmu_fault_unactivated", {
                    {"fault_id", "0"},
                    {"fault_model", "M02"},
                    {"fault_reason", "no_eligible_refill"},
                    {"outcome", "not_activated"},
                    {"corr", CORR_NONE},
                });
                return;
            }
            const bool consumed = mmu_fault_result_event != 0 ||
                                  mmu_fault_lineage_consume_event != 0;
            // [Phase 2.2] Real per-layer lineage census (instance:id:gen).
            std::ostringstream lineage_entries;
            uint64_t consumer_count = 0;
            for (const auto &le : mmu_entry_lineage) {
                if (le.second.fault_id != mmu_fault_ptag)
                    continue;
                if (lineage_entries.tellp() > 0)
                    lineage_entries << ',';
                lineage_entries << le.first.instance << ':'
                                << le.first.entry_id << ':'
                                << le.first.generation;
                consumer_count += le.second.reuse_count;
            }
            notePropEvt("mmu_fault_summary", {
                {"fault_id", std::to_string(mmu_fault_ptag)},
                {"fault_model", "M02"},
                {"fault_reason", consumed ? "corrupted_entry_consumed"
                                          : "corrupted_entry_not_consumed"},
                {"activation_event_id",
                    std::to_string(mmu_fault_activation_event)},
                {"tlb_entry_id", std::to_string(mmu_fault_entry_id)},
                {"entry_generation",
                    std::to_string(mmu_fault_entry_generation)},
                {"lineage_fault_id", std::to_string(mmu_fault_ptag)},
                {"lineage_entry_count",
                    std::to_string(mmu_entry_lineage.size())},
                {"lineage_entries", lineage_entries.str()},
                {"consumer_count", std::to_string(consumer_count)},
                {"consumption_event_id",
                    std::to_string(mmu_fault_lineage_consume_event)},
                {"consumer_dyn_inst_seq",
                    std::to_string(mmu_fault_lineage_consumer_seq)},
                {"origin_dyn_inst_seq",
                    std::to_string(mmu_m02_pending.seq)},
                {"old_pfn", mmuHex(mmu_m02_old_pfn)},
                {"new_pfn", mmuHex(mmu_fault_new_pfn)},
                {"old_pa", mmuHex(mmu_fault_old_pa)},
                {"new_pa", mmuHex(mmu_fault_new_pa)},
                {"result_event_id",
                    std::to_string(mmu_fault_result_event)},
                {"result_pa", mmuHex(mmu_fault_result_pa)},
                {"response_event_id",
                    std::to_string(mmu_fault_response_event)},
                {"writeback_event_id",
                    std::to_string(mmu_fault_wb_event)},
                {"commit_event_id",
                    std::to_string(mmu_fault_commit_event)},
                {"consumed", consumed ? "1" : "0"},
                {"outcome", consumed ? "activated_consumed"
                                     : "activated_not_consumed"},
                {"corr", CORR_NONE},
            });
            return;
        }
        // [MMU-PHASE3] M03-M08: one honest summary row per configured model.
        // The terminal classification itself is done offline by the
        // validator (activation != propagation != SDC).
        if (mmu_fault_model == "M03" || mmu_fault_model == "M04" ||
                mmu_fault_model == "M05" || mmu_fault_model == "M06" ||
                mmu_fault_model == "M07" || mmu_fault_model == "M08") {
            if (mmu_fault_state == MmuFaultState::Idle) {
                notePropEvt("mmu_fault_unactivated", {
                    {"fault_id", "0"},
                    {"fault_model", mmu_fault_model},
                    {"fault_reason", "no_eligible_target_event"},
                    {"fault_activation_status", "not_activated"},
                    {"outcome", "not_activated"},
                    {"corr", CORR_NONE},
                });
                return;
            }
            // [M06] "Consumed" means the CORRUPTED STATE was consumed by the
            // decoder (or by a real entry-lineage lookup), never "a squash
            // was observed" and never "a translation result exists". The
            // propagation of the fault RESULT (Arm fault object + commit
            // trap) is reported separately so a SQUASHED instruction can
            // never be mislabelled as consumed.
            const bool mmu_state_consumed =
                mmu_fault_state_consumed_event != 0 ||
                mmu_entry_fault_consume_count != 0;
            const bool mmu_result_propagated =
                mmu_fault_result_propagated_event != 0;
            const bool mmu_exception_delivered =
                mmu_fault_exception_delivery_event != 0;
            notePropEvt("mmu_fault_summary", {
                {"fault_id", std::to_string(mmu_fault_ptag)},
                {"fault_model", mmu_fault_model},
                {"fault_persistence", mmu_fault_persistence},
                {"fault_activation_status", "activated"},
                {"activation_event_id",
                    std::to_string(mmu_fault_activation_event)},
                {"va", mmuHex(mmu_fault_va)},
                {"tlb_entry_id", std::to_string(mmu_fault_entry_id)},
                {"entry_generation",
                    std::to_string(mmu_fault_entry_generation)},
                {"fault_consume_count",
                    std::to_string(mmu_entry_fault_consume_count)},
                {"consumption_event_id",
                    std::to_string(mmu_fault_lineage_consume_event)},
                {"consumer_dyn_inst_seq",
                    std::to_string(mmu_fault_lineage_consumer_seq)},
                {"result_event_id",
                    std::to_string(mmu_fault_result_event)},
                {"result_pa", mmuHex(mmu_fault_result_pa)},
                {"response_event_id",
                    std::to_string(mmu_fault_response_event)},
                {"writeback_event_id",
                    std::to_string(mmu_fault_wb_event)},
                {"commit_event_id",
                    std::to_string(mmu_fault_commit_event)},
                {"consumer_count",
                    std::to_string(mmu_entry_fault_consume_count)},
                // [M06] Separate consumed-state / propagated-result /
                // delivered-exception evidence.
                {"state_consumed", mmu_state_consumed ? "1" : "0"},
                {"result_propagated", mmu_result_propagated ? "1" : "0"},
                {"exception_delivered",
                    mmu_exception_delivered ? "1" : "0"},
                {"fault_state_consumed_event_id",
                    std::to_string(mmu_fault_state_consumed_event)},
                {"fault_result_propagated_event_id",
                    std::to_string(mmu_fault_result_propagated_event)},
                {"exception_delivery_event_id",
                    std::to_string(mmu_fault_exception_delivery_event)},
                {"exception_class", mmu_fault_exception_class.empty()
                    ? "none" : mmu_fault_exception_class},
                {"delivery_target", mmu_fault_delivery_target.empty()
                    ? "none" : mmu_fault_delivery_target},
                {"faulting_inst_squashed",
                    mmu_fault_inst_squashed ? "1" : "0"},
                {"faulting_inst_squash_event_id",
                    std::to_string(mmu_fault_inst_squash_event)},
                {"consumed", mmu_state_consumed ? "1" : "0"},
                {"outcome", mmu_state_consumed ? "activated_consumed"
                                               : "activated_not_consumed"},
                {"corr", CORR_NONE},
            });
        }
    }

} // namespace gem5
