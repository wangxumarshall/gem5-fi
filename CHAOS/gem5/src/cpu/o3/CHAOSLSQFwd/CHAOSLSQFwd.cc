#include "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSLSQFwd.hh"

#include <iostream>
#include <fstream>
#include <sstream>
#include <cstring>     // [R6-S-FWD] strcmp (model-field routing)
#include <cstdio>      // [MDSPEC][R4-5.7b] printf (CHAOS_LSU_S10_FORK line)
#include <algorithm>   // [MDSPEC][R4-5.7] std::find (S10 candidate dedup)

#include "base/output.hh"
#include "cpu/o3/chaos_barrier_hook.hh"  // [MDSPEC][R4-9-FSMC] O06/O07
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"   // [MDSPEC][R4-5.3] full DynInst (resp-pair)
#include "debug/LSQUnit.hh"
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [MDSPEC][H3-FWD]
#include "base/chaos_guest_fault.hh"  // [R6-S-REPAIR2] guest-SEGV teardown arm

namespace gem5
{

    CHAOSLSQFwd::CHAOSLSQFwd(const CHAOSLSQFwdParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fault_type_enum(stringToFaultType(p.faultType)),
          struct_mode(stringToStructMode(p.structMode)),
          fault_mask(std::bitset<64>(p.faultMask)),
          num_bits_to_change(p.bitsToChange),
          byte_offset(p.byteOffset),
          lane_skew_k(p.laneSkewK),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          l03_mode(p.l03Mode),   // [LSU][SEM-B]
          l04_mode(p.l04Mode),   // [MDSPEC][R4-5.3] W5 L04
          s10_mode(p.s10Mode),   // [MDSPEC][R4-5.7] W5 S10
          // [MDSPEC][R4-9-FSMC] O06/O07 barrier-completion / order-tag modes.
          o06_mode(p.o06Mode),
          o07_mode(p.o07Mode),
          o06_early(p.o06BarrierDone == "early"),
          rng(rng_seed != 0 ? rng_seed : rd()),
          log_stream(nullptr),
          stats(nullptr)
    {
        // LSU W2/W5: event-normalized trigger (05 r2-r8; off = legacy).
        if (p.lsuTier != "off") {
            auto tier = ChaOSLsuTier::F0;
            if (p.lsuTier == "F1") tier = ChaOSLsuTier::F1;
            else if (p.lsuTier == "F2") tier = ChaOSLsuTier::F2;
            else if (p.lsuTier == "F3") tier = ChaOSLsuTier::F3;
            else if (p.lsuTier == "F4") tier = ChaOSLsuTier::F4;
            else if (p.lsuTier == "F5") tier = ChaOSLsuTier::F5;
            else if (p.lsuTier == "F6") tier = ChaOSLsuTier::F6;
            lsuTrigger = new ChaOSLsuTrigger(tier, rng_seed ? rng_seed : 1,
                                             p.lsuWarmupEvents, p.lsuSpanEvents);
        }
        // [MDSPEC][R4-5.3] L04 is trigger-native (the response-pairing
        // stream is the model's event source) — the tier flags are not
        // optional. Loud refusal, C11/C12 convention (never silently inert).
        if (l04_mode && !lsuTrigger)
            panic("CHAOSLSQFwd: --lsqfwd_l04 (L04 response-pairing mode) "
                  "requires --lsqfwd_lsu_tier (the event-normalized trigger "
                  "owns the pairing-point stream); refusing to run with a "
                  "legacy Bernoulli fallback");
        // [MDSPEC][R4-5.7] S10 is trigger-native the same way (the
        // StoreSet SSIT-training stream is the model's event source) and
        // rides the standard mount (log stream + exit callbacks live in
        // the probability>0 branch — the campaign default 1.0). Loud
        // refusals, L04/C11/C12 convention.
        if (s10_mode && !lsuTrigger)
            panic("CHAOSLSQFwd: --lsqfwd_s10 (S10 StoreSet SSIT-ID 换值 "
                  "mode) requires --lsqfwd_lsu_tier (the event-normalized "
                  "trigger owns the StoreSet training stream); refusing to "
                  "run with a legacy Bernoulli fallback");
        if (s10_mode && probability <= 0.0f)
            panic("CHAOSLSQFwd: --lsqfwd_s10 requires the standard mount "
                  "(probability > 0; the campaign default is 1.0 — the "
                  "legacy probability knob is not the S10 trigger, but the "
                  "injection-log stream and exit callbacks live on the "
                  "standard mount path)");
        // [MDSPEC][R4-5.7] S10 hook registration: StoreSet (inside
        // MemDepUnit/InstQueue) reaches this injector through the
        // chaosS10* globals (single-consumer, BaseCache::chaosMergeHook
        // precedent). Cleared in the destructor.
        if (s10_mode) {
            s10_active = this;
            chaosS10Violation = &CHAOSLSQFwd::s10ViolationCb;
            chaosS10SsidSubst = &CHAOSLSQFwd::s10SsidSubstCb;
            chaosS10CorruptedPc = &CHAOSLSQFwd::s10CorruptedPcCb;
            chaosS10Consult = &CHAOSLSQFwd::s10ConsultCb;
            chaosS10Issued = &CHAOSLSQFwd::s10IssuedCb;
            chaosS10Clear = &CHAOSLSQFwd::s10ClearCb;
        }
        // [MDSPEC][R4-9-FSMC] O06/O07: trigger-native like L04/S10 (the
        // barrier-SN stream IS the model's event source). The MemDepUnit has
        // no injector pointer, so the armed instance self-registers into the
        // chaosBarrier* globals (S10/store_set.cc precedent).
        if (o06_mode || o07_mode) {
            if (!lsuTrigger)
                panic("CHAOSLSQFwd: --lsqfwd_o06/--lsqfwd_o07 require "
                      "--lsqfwd_lsu_tier (the event-normalized trigger owns "
                      "the barrier bookkeeping stream); refusing to run with "
                      "a legacy Bernoulli fallback");
            barrier_active = this;
            chaosBarrierInsertHook = &CHAOSLSQFwd::barrierInsertCb;
            chaosBarrierReleaseHook = &CHAOSLSQFwd::barrierReleaseCb;
        }
        if (lsuTrigger) {
            // W5: funnel lines at exit (chaos_l0 discipline: log file, not
            // stdout). activated = same near-tautological approximation as
            // CHAOSAddrPath (the forwarded data is consumed by the load's
            // writeback immediately after this hook).
            registerExitCallback([this]() {
                if (lsuTrigger)
                    lsuTrigger->summary("CHAOSLSQFwd");
                // [MDSPEC][R4-5.7b] S10 fork-point break-down, printed next
                // to CHAOS_LSU_TRIGGER so one census run settles the
                // attempted>0/eligible=0 triage (classes (a)/(b)/(c)/(d);
                // see the .hh member comment). Only in S10 mode; zero
                // effect on every other model's output. Reading:
                //   arm1_events==0            -> (c): the assignment arm is
                //                                never entered at all
                //   arm1_events>0 && cand_empty==arm1_events
                //                             -> the predicate never held:
                //                                (a) if max_live_ssids==0,
                //                                (d) if max_live_ssids==1
                //                                (single store-set in use)
                //   arm1_cand_ok>0            -> candidates existed: any
                //                                eligible==0 then is a
                //                                trigger-window artifact
                if (s10_mode) {
                    printf("CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd "
                           "attempted=%lu eligible=%lu arm1_events=%lu "
                           "arm1_cand_empty=%lu arm1_cand_ok=%lu "
                           "max_live_ssids=%lu max_cands=%lu "
                           "distinct_arm1_load_pcs=%zu\n",
                           (unsigned long)lsuTrigger->attempted,
                           (unsigned long)lsuTrigger->eligible,
                           (unsigned long)s10_arm1_events,
                           (unsigned long)s10_arm1_cand_empty,
                           (unsigned long)s10_arm1_cand_ok,
                           (unsigned long)s10_max_live_ssids,
                           (unsigned long)s10_max_cands,
                           s10_arm1_load_pcs.size());
                }
                // [MDSPEC][R4-9-FSMC] O06/O07 teardown read-back: the barrier
                // bookkeeping the injector saw + how many completions it
                // corrupted. barrier_live_sns.size() > 0 at exit is the O06-b
                // OBSERVABLE STALL (the SN was never released — every later
                // memory op waited on a barrier that never completed).
                if (o06_mode || o07_mode)
                    printf("CHAOS_BARRIER: injector=CHAOSLSQFwd mode=%s "
                           "inserts_seen=%lu releases_seen=%lu injections=%lu "
                           "live_sns_at_exit=%lu (R4-9-FSMC O06/O07 barrier "
                           "bookkeeping hook, mem_dep_unit.cc)\n",
                           o06_mode ? (o06_early ? "o06a_early_done"
                                                 : "o06b_done_stuck")
                                    : "o07_order_tag_swap",
                           (unsigned long)barrier_inserts_seen,
                           (unsigned long)barrier_releases_seen,
                           (unsigned long)barrier_injections,
                           (unsigned long)barrier_live_sns.size());
                l0_funnel.attempted = lsuTrigger->attempted;
                l0_funnel.eligible  = lsuTrigger->eligible;
                l0_funnel.injected  = faults_injected_count;
                // [MDSPEC][R4-5.7] S10 activated is NOT the near-tautology
                // the data-path models use: the fault lives in PC-keyed
                // predictor state, so "consumed downstream" = a consult or
                // violation actually read the corrupted entry (workbook
                // 激活口径: "故障值被下游实际读取、选择或消费"). An
                // injection whose PC is never consulted stays
                // Injected-not-activated — reported honestly as 0.
                l0_funnel.activated = s10_mode ? s10_activated_count
                                               : faults_injected_count;
                if (write_log && log_stream && log_stream->stream()) {
                    *(log_stream->stream()) << l0_funnel.line("CHAOSLSQFwd")
                                            << std::endl;
                }
            });
        }
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSLSQFwd: cpu is not an O3CPU. CHAOSLSQFwd only supports "
                "O3CPU (it hooks the O3 LSQ store->load forwarding path). "
                "Cast failed.");
        }
        if (probability > 0.0f) {
            log_stream = simout.create("lsq_fwd_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSLSQFwd: Could not open log file");
            }
            // Sampling-bias fix (findings.md Phase 2.2, same as
            // CHAOSL1DForward): skip a geometric(p=0.1) number of eligible
            // forwarding events before the first injection, so the single
            // fault (maxFaults=1) lands on a seed-dependent event instead
            // of always the first eligible one (same dynamic store->load
            // pair every rep on a deterministic stream).
            // v1.1 Phase 8.2: fixed uniform skip (driver-provided,
            // chaos_event_sample.hh) overrides the legacy geometric(0.1)
            // draw; UINT64_MAX sentinel keeps legacy behavior.
            if (p.eventsToSkip != ~0ULL)
                events_to_skip = p.eventsToSkip;
            else {
                std::geometric_distribution<uint64_t> skip_dist(0.1);
                events_to_skip = skip_dist(rng);
            }
            count_only = p.countOnly;
            // v1.1 Phase 8.2: print CHAOS_ELIGIBLE_COUNT at sim exit (the
            // destructor may not run before gem5's exit path; the exit
            // callback always fires). Registered here because CHAOSLSQFwd
            // self-attaches in the ctor (no startup() override).
            if (count_only) {
                registerExitCallback([this]() {
                    if (log_stream && log_stream->stream())
                        *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
                            << eligible_count << std::endl;
                });
            }
            stats = std::make_unique<CHAOSLSQFwdStats>(this);
            random_fault_distribution = std::discrete_distribution<int>(
                {0.9, 0.05, 0.05});  // bit_flip / stuck0 / stuck1
            // Register self with the CPU so lsq_unit.cc can reach this
            // injector via cpu->lsqFwd. cpu is guaranteed constructed first
            // (it was passed as a Param). Safe because lsq_unit only reads
            // lsqFwd during execute(), long after SimObject construction.
            cpu->lsqFwd = this;
        }
    }

    CHAOSLSQFwd::~CHAOSLSQFwd()
    {
        // [MDSPEC][R4-5.7] S10 hook deregistration (single consumer: only
        // clear what still points at THIS injector's statics).
        if (s10_active == this) {
            s10_active = nullptr;
            if (chaosS10Violation == &CHAOSLSQFwd::s10ViolationCb)
                chaosS10Violation = nullptr;
            if (chaosS10SsidSubst == &CHAOSLSQFwd::s10SsidSubstCb)
                chaosS10SsidSubst = nullptr;
            if (chaosS10CorruptedPc == &CHAOSLSQFwd::s10CorruptedPcCb)
                chaosS10CorruptedPc = nullptr;
            if (chaosS10Consult == &CHAOSLSQFwd::s10ConsultCb)
                chaosS10Consult = nullptr;
            if (chaosS10Issued == &CHAOSLSQFwd::s10IssuedCb)
                chaosS10Issued = nullptr;
            if (chaosS10Clear == &CHAOSLSQFwd::s10ClearCb)
                chaosS10Clear = nullptr;
        }
        // [MDSPEC][R4-9-FSMC] O06/O07 hook deregistration (same single-
        // consumer discipline).
        if (barrier_active == this) {
            barrier_active = nullptr;
            if (chaosBarrierInsertHook == &CHAOSLSQFwd::barrierInsertCb)
                chaosBarrierInsertHook = nullptr;
            if (chaosBarrierReleaseHook == &CHAOSLSQFwd::barrierReleaseCb)
                chaosBarrierReleaseHook = nullptr;
        }
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                << std::endl;
        }
    }

    CHAOSLSQFwd::FaultType
    CHAOSLSQFwd::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        else if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        else if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char*
    CHAOSLSQFwd::faultTypeToString(FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::Random: return "random";  // §2.4: clear -Wswitch
        }
        return "random";
    }

    // §2.4 structured fault mode (fi-h6-h7 branch, H5 closed).
    CHAOSLSQFwd::StructMode
    CHAOSLSQFwd::stringToStructMode(const std::string &s) {
        if (s == "byte_lane_skew") return StructMode::ByteLaneSkew;
        if (s == "all_zero") return StructMode::AllZero;
        if (s == "fwd_source_sub") return StructMode::FwdSourceSub;
        if (s == "phase_offset") return StructMode::PhaseOffset;
        return StructMode::ByteFlip;  // default / unknown
    }

    int
    CHAOSLSQFwd::generateRandomMask(int bits_to_change)
    {
        // 8-bit mask (applied to one byte of the forwarded buffer)
        int mask = 0;
        std::uniform_int_distribution<int> bitDist(0, 7);
        while (bits_to_change-- > 0) mask |= (1 << bitDist(rng));
        return mask;
    }

    uint64_t
    CHAOSLSQFwd::writeLog(const char *type, unsigned size, Addr vaddr,
                          int byte_off, int mask, const FwdCorrelKeys &keys,
                          const o3::DynInstPtr &load_inst, const void *data)
    {
        // [R6-S-REPAIR2 2026-10-30] A real LSQFwd injection can leave the
        // guest with a corrupted value that is later dereferenced as a wild
        // pointer. Arm the same controlled guest-SEGV teardown CHAOSAddrPath
        // uses; without it the SE page-table-fault path panics and truncates
        // stats/prop_evt (S09-F0-W5 seed2). Arm-only: no VA is registered.
        chaos::noteChaosInjection();
        // [MDSPEC][H3-FWD] register the forwarding fault with the propagation
        // tracer — writeLog is the single chokepoint every S01/S02/S03/S09
        // data-path injection passes through, so one hook covers them all.
        //
        // [MDSPEC][R4-1] seq-PRIMARY correlation (user ruling 2026-10-20,
        // superseding the H3-FWD address-scoped note): the producer store's
        // and consuming load's dyn_inst_seq / sq_idx / lq_idx / request_id
        // are passed in from lsq_unit.cc's forward site. Registration binds
        // the addr registry to the STORE's seq (sq_writeback/sq_complete
        // join by seq); the byte range stays in the blk registry as the
        // LABELED address-only fallback. store_dyn_inst_seq == 0 (seq
        // genuinely unavailable) degrades to corr=addr_fallback.
        uint64_t ptag = 0;
        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            ptag = tr->registerLSQForwardFault(
                keys.store_dyn_inst_seq, keys.sq_idx, keys.store_request_id,
                keys.load_dyn_inst_seq, keys.lq_idx, keys.load_request_id,
                vaddr, size ? size : 1,
                type && strcmp(type, "fwd_source_sub") == 0
                    ? "fwd_source_sub" : "lsqfwd_forward");
            // [R6-S-FWD 2026-10-30] The real forward lifecycle (L1 sq_entry ->
            // L2 lsq_fwd -> L3 resp -> L4 taint_reg) plus the consuming load's
            // seq registration. A forwarded load has no memory response, so
            // this is the only place its dest registers can be tainted.
            if (ptag)
                tr->noteForwardedLoad(
                    load_inst ? load_inst.get() : nullptr,
                    vaddr, size ? size : 1, ptag,
                    keys.store_dyn_inst_seq, keys.sq_idx, keys.lq_idx,
                    keys.load_request_id,
                    /*true_store_seq=*/0, type, data);
        }
        if (!write_log) return ptag;
        *(log_stream->stream())
            << "Cycle: " << cpu->curCycle()
            << ", CPU: " << cpu->name()
            << ", Site: store->load_forward"
            << ", FaultType: " << type
            << ", Vaddr: 0x" << std::hex << vaddr << std::dec
            << ", FwdSize: " << size
            << ", ByteOffset: " << byte_off
            << ", Mask: " << std::bitset<8>(mask)
            << ", StoreSeq: " << keys.store_dyn_inst_seq
            << ", SqIdx: " << keys.sq_idx
            << ", LoadSeq: " << keys.load_dyn_inst_seq
            << ", LqIdx: " << keys.lq_idx
            << std::endl;
        return ptag;
    }

    bool
    CHAOSLSQFwd::corrupt(uint8_t *data, unsigned size, Addr vaddr,
                         const FwdCorrelKeys &keys,
                         const o3::DynInstPtr &load_inst)
    {
        // Hot-path short-circuit: no injection configured.
        if (probability <= 0.0f) return false;
        // fwd_source_sub injects at the DECISION point (maybeSubstituteSource,
        // called before the memcpy); this post-forward corrupt hook must NOT
        // also fire in that mode (double-injection bug found in Phase 4.2
        // verification: an unlimited-faults run showed bit_flip lines while
        // in fwd_source_sub mode — the old hook was still active).
        // phase_offset likewise acts at the WRITEBACK-SCHEDULE point
        // (maybeDelayForward) — no data mutation there either.
        if (struct_mode == StructMode::FwdSourceSub) return false;
        if (struct_mode == StructMode::PhaseOffset) return false;
        // [LSU][SEM-B] L03 hook split: with --lsqfwd_l03 the SQ-forward
        // data path is NOT L03's event source — the trigger stream must be
        // violation checks only (checkViolations site), not the mixed stream.
        if (l03_mode) return false;
        // [MDSPEC][R4-5.3] L04 hook split, same discipline: with
        // --lsqfwd_l04 the SQ-forward data path is NOT L04's event source —
        // the trigger stream is the response-pairing point only
        // (LSQUnit::completeDataAccess, maybeSwapResponseTarget).
        if (l04_mode) return false;
        // [MDSPEC][R4-5.7] S10 hook split, same discipline: with
        // --lsqfwd_s10 the SQ-forward data path is NOT S10's event source —
        // the trigger stream is the StoreSet SSIT-training point only
        // (StoreSet::violation, chaosS10* hooks).
        if (s10_mode) return false;
        // [MDSPEC][R4-9-FSMC] O06/O07 hook split, same discipline: with
        // --lsqfwd_o06/--lsqfwd_o07 the SQ-forward data path is NOT the
        // model's event source — the trigger stream is the barrier-SN
        // bookkeeping in MemDepUnit (cpu/o3/chaos_barrier_hook.hh).
        if (o06_mode || o07_mode) return false;
        if (lsuTrigger) {
            // LSU W2/W5 path (05 r2-r8): the event-normalized trigger owns
            // warm-up/repetition semantics; the legacy cycle window,
            // events_to_skip and the Bernoulli roll do NOT apply here.
            lsuTrigger->onAttempt();
            if (!lsuTrigger->onEligible()) return false;
        } else {
            Cycles cur = cpu->curCycle();
            if (cur < first_clock) return false;
            if (last_clock != Cycles(0) && cur > last_clock) return false;
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return false;

            // Sampling-bias fix (findings.md Phase 2.2): skip the first N
            // eligible forwarding events (N ~ geometric(0.1) from the seed)
            // so the single fault lands on a seed-dependent event.
            if (count_only) { ++eligible_count; return false; }
            if (events_to_skip > 0) {
                --events_to_skip;
                return false;
            }

            // Bernoulli: does this forwarding event get corrupted?
            std::uniform_real_distribution<float> dist(0.0f, 1.0f);
            if (dist(rng) >= probability) return false;
        }
        if (size == 0) return false;

        // §2.4 structured fault modes (fi-h6-h7 branch, H5 closed):
        if (struct_mode == StructMode::ByteLaneSkew) {
            // Rotate the whole forwarded buffer by k bytes (rol_k) —
            // core179 D1 byte-lane phase signature (method2).
            int k = lane_skew_k % (int)size;
            if (k < 0) k += (int)size;
            if (k != 0) {
                uint8_t tmp[16];
                for (unsigned i = 0; i < size; i++) tmp[i] = data[i];
                for (unsigned i = 0; i < size; i++)
                    data[i] = tmp[(i + k) % size];
            }
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("byte_lane_skew", size, vaddr, lane_skew_k, 0, keys,
                     load_inst, data);
            if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F5)
                lsuTrigger->noteOutcome(true);
            DPRINTF(LSQUnit, "CHAOSLSQFwd: byte_lane_skew rol %d (vaddr=%#x)\n",
                    lane_skew_k, vaddr);
            return true;
        }
        if (struct_mode == StructMode::AllZero) {
            for (unsigned i = 0; i < size; i++) data[i] = 0;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("all_zero", size, vaddr, 0, 0, keys, load_inst, data);
            if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F5)
                lsuTrigger->noteOutcome(true);
            DPRINTF(LSQUnit, "CHAOSLSQFwd: all_zero (vaddr=%#x size=%u)\n",
                    vaddr, size);
            return true;
        }

        // Choose byte to corrupt.
        int off = byte_offset;
        if (off < 0) {
            std::uniform_int_distribution<int> bdist(0, (int)size - 1);
            off = bdist(rng);
        }
        if (off >= (int)size) off = (int)size - 1;

        int mask = fault_mask.any()
            ? (int)(fault_mask.to_ulong() & 0xff)
            : generateRandomMask(num_bits_to_change);

        FaultType chosen = fault_type_enum;
        if (fault_type_enum == FaultType::Random) {
            int idx = random_fault_distribution(rng);
            chosen = static_cast<FaultType>(idx);
        }

        switch (chosen) {
            case FaultType::StuckAtZero:
                data[off] &= ~(uint8_t)mask;
                stats->numStuckAtZero++;
                break;
            case FaultType::StuckAtOne:
                data[off] |= (uint8_t)mask;
                stats->numStuckAtOne++;
                break;
            case FaultType::BitFlip:
                data[off] ^= (uint8_t)mask;
                stats->numBitFlips++;
                break;
            default: break;
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;
        writeLog(faultTypeToString(chosen), size, vaddr, off, mask, keys,
                 load_inst, data);
        // [R6-A-F5COUNT discipline] F5 separates fire from outcome: report the
        // effective write so trigger.injected matches the log/stats.
        if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F5)
            lsuTrigger->noteOutcome(true);
        DPRINTF(LSQUnit, "CHAOSLSQFwd: corrupted forwarded byte %d (vaddr=%#x "
                "mask=%#x type=%s)\n", off, vaddr, mask,
                faultTypeToString(chosen));
        return true;
    }

    bool
    CHAOSLSQFwd::maybeSubstituteSource(uint8_t *load_data,
                                       const uint8_t *true_src,
                                       unsigned copy_size,
                                       const uint8_t *alt_src,
                                       unsigned alt_size, Addr vaddr,
                                       const FwdCorrelKeys &keys,
                                       const o3::DynInstPtr &load_inst,
                                       uint64_t alt_store_seq,
                                       long long alt_sq_idx,
                                       uint64_t alt_store_req_id)
    {
        // §2.4 fwd_source_sub (F5): wrong-source store->load forwarding.
        // Only active in FwdSourceSub mode; other modes return false and the
        // caller does its normal memcpy (zero regression).
        if (struct_mode != StructMode::FwdSourceSub) return false;
        if (probability <= 0.0f) return false;
        if (!load_data || !true_src || !alt_src) return false;
        if (copy_size == 0 || alt_size == 0) return false;

        // [MDSPEC][R4-1-review-I2] the event-normalized trigger owns this
        // site too: fwd_source_sub's eligible stream (wrong-source
        // opportunities — the call site's alt-scan already gated on an
        // older SQ entry carrying data) must ride the SAME F0-uniform /
        // F1-F4 interval semantics as the data-path corrupt() site. Before
        // this change a tier-mounted S08 run never consulted lsuTrigger
        // (attempted=0) and injected via the legacy Bernoulli path below —
        // the tier flags were silently inert for this mode.
        if (lsuTrigger) {
            lsuTrigger->onAttempt();
            if (!lsuTrigger->onEligible()) return false;
        } else {
            Cycles cur = cpu->curCycle();
            if (cur < first_clock) return false;
            if (last_clock != Cycles(0) && cur > last_clock) return false;
            if (max_faults != 0 && faults_injected_count >= max_faults)
                return false;

            // sampling-bias fix: consume skip only on eligible wrong-source
            // opportunities (an older SQ entry exists with data)
            if (count_only) { ++eligible_count; return false; }
            if (events_to_skip > 0) { --events_to_skip; return false; }

            std::uniform_real_distribution<float> dist(0.0f, 1.0f);
            if (dist(rng) >= probability) return false;
        }

        // Copy the WRONG store's data into the load buffer. If the wrong
        // source is smaller than the load, copy what it has (the tail keeps
        // whatever the caller's buffer held — the mismatch IS the fault).
        unsigned n = copy_size < alt_size ? copy_size : alt_size;
        memcpy(load_data, alt_src, n);
        stats->numFaultsInjected++;
        ++faults_injected_count;
        // [R6-S-REPAIR2 2026-10-30] real injection: arm controlled guest SEGV.
        chaos::noteChaosInjection();
        // [R6-S-FWD 2026-10-30] fwd_source_sub rides the SAME real
        // registration/emission path as the data-path corruption: the inj
        // node names the consuming load, and the real L1->L4 lifecycle is
        // emitted with the WRONG source store's identity (the store whose
        // data was actually delivered). true_store_dyn_inst_seq keeps the
        // scan's true source on the event. No lone/isolated inj is allowed.
        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            const uint64_t ptag = tr->registerLSQForwardFault(
                alt_store_seq, alt_sq_idx, alt_store_req_id,
                keys.load_dyn_inst_seq, keys.lq_idx, keys.load_request_id,
                vaddr, n, "fwd_source_sub");
            if (ptag)
                tr->noteForwardedLoad(
                    load_inst ? load_inst.get() : nullptr, vaddr, n, ptag,
                    alt_store_seq, alt_sq_idx, keys.lq_idx,
                    keys.load_request_id, keys.store_dyn_inst_seq,
                    "fwd_source_sub", load_data);
        }
        // [R6-A-F5COUNT discipline] report the effective F5 write.
        if (lsuTrigger && lsuTrigger->tier == ChaOSLsuTier::F5)
            lsuTrigger->noteOutcome(true);
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", Site: store->load_forward_decision"
                << ", FaultType: fwd_source_sub"
                << ", Vaddr: 0x" << std::hex << vaddr << std::dec
                << ", TrueSrcSize: " << copy_size
                << ", AltSrcSize: " << alt_size
                << ", Copied: " << n
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        DPRINTF(LSQUnit, "CHAOSLSQFwd: fwd_source_sub wrong-source forward "
                "(vaddr=%#x true=%uB alt=%uB)\n", vaddr, copy_size, alt_size);
        return true;
    }

    Cycles
    CHAOSLSQFwd::maybeDelayForward(Addr vaddr, unsigned size)
    {
        // §2.4 F6 phase_offset (Phase 4.7, the REAL method3 forward-path
        // phase proxy): delay ONE forward's WritebackEvent by phaseOffset
        // CPU cycles. The method3 field signature ('add a no-op ALU ->
        // trigger rate collapses') is a forward-path timing race — the
        // load's writeback landing LATER than the dependent instruction's
        // read window (or vice versa) changes what the consumer sees.
        // Only active in PhaseOffset mode; other modes return Cycles(0)
        // (zero regression — the caller schedules at curTick() as usual).
        if (struct_mode != StructMode::PhaseOffset) return Cycles(0);
        if (probability <= 0.0f) return Cycles(0);
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return Cycles(0);

        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return Cycles(0);
        if (last_clock != Cycles(0) && cur > last_clock) return Cycles(0);

        // sampling-bias fix: skip budget consumed on eligible forwards
        if (count_only) { ++eligible_count; return Cycles(0); }
        if (events_to_skip > 0) { --events_to_skip; return Cycles(0); }

        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return Cycles(0);

        faults_injected_count++;
        stats->numFaultsInjected++;
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", Site: store->load_forward_wb_schedule"
                << ", FaultType: phase_offset"
                << ", Vaddr: 0x" << std::hex << vaddr << std::dec
                << ", FwdSize: " << size
                << ", DelayCycles: +" << lane_skew_k
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        DPRINTF(LSQUnit, "CHAOSLSQFwd: phase_offset delay +%d cycles "
                "(vaddr=%#x)\n", lane_skew_k, vaddr);
        // reuse lane_skew_k as the offset knob (the --lsq_lane_skew_k CLI
        // arg; documented here as the phase offset in cycles)
        return Cycles(lane_skew_k > 0 ? lane_skew_k : 1);
    }

    CHAOSLSQFwd::CHAOSLSQFwdStats::CHAOSLSQFwdStats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total forwarded-data faults injected"),
          ADD_STAT(numBitFlips, statistics::units::Count::get(),
                   "Bit-flip faults on forwarded data"),
          ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
                   "Stuck-at-0 faults on forwarded data"),
          ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
                   "Stuck-at-1 faults on forwarded data")
    {}

    bool
    CHAOSLSQFwd::violationCorrupt(Addr& cmp_addr)
    {
        // [LSU][SEM-B] the violation site is L03's ONLY injection point;
        // non-L03 runs must not inject here (was: mixed into any lsqfwd run).
        if (!lsuTrigger || !l03_mode) return false;
        lsuTrigger->onAttempt();
        if (!lsuTrigger->onEligible()) return false;
        const uint64_t bit = rng() % 20;
        cmp_addr ^= (1ULL << bit);
        ++faults_injected_count;
        ++l0_funnel.injected;
        ++l0_funnel.activated;
        // [R6-S-REPAIR2 2026-10-30] real injection: arm controlled guest SEGV.
        chaos::noteChaosInjection();
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Cycle: " << cpu->curCycle()
                << ", Site: checkViolations_L03"
                << ", FaultType: violation_addr_bitflip"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // [MDSPEC][R4-5.3] LSU W5 L04-b: response-pairing target exchange.
    // Model (workbook 03/09, L04 row): when >=2 loads are in flight, the
    // response-pairing table's entries for two loads are EXCHANGED — each
    // load's returning response is delivered to the OTHER load ("两个响应
    // 数据各自合法但送错消费者": both responses keep their data, both go
    // to the wrong consumer). Realized here as a deferred exchange:
    //   half 1 — the source load A's response arrives; with the trigger's
    //            consent a candidate in-flight load B is chosen and THIS
    //            response is delivered to B (writeback(B, A's packet):
    //            B's dest reg receives A's data — the mispairing);
    //   half 2 — B's own response arrives later and is delivered to A
    //            (writeback(A, B's packet)). Both loads complete exactly
    //            once, each with the other's data; the program terminates
    //            and the oracle classifies normally.
    // The workbook's "同周期" (same-cycle) is relaxed to a pairing-window
    // exchange (responses may arrive in different cycles — gem5 delivers
    // one response per completeDataAccess call); the SEMANTICS — two
    // legal responses, each delivered to the wrong consumer — are exactly
    // the L04-b exchange. L04-a (one-shot transaction-ID replacement whose
    // victim load never completes — a hang/Timeout channel) is NOT landed
    // (pending in lsu_runid_map SPEC_IMPL_LANDED).
    o3::DynInstPtr
    CHAOSLSQFwd::maybeSwapResponseTarget(const o3::DynInstPtr &inst,
                                         const RespPairKeys &src,
                                         const RespPairScan &scan)
    {
        // Non-L04 runs: one branch, byte-identical behavior.
        if (!l04_mode || !lsuTrigger)
            return inst;

        // Half 2 — the pending exchange's partner response. Mechanical
        // completion of the already-injected fault: no trigger consult, no
        // attempt booking (booking it would double-count the injected
        // event's own footprint in the attempt stream), and deliberately
        // BEFORE the maxFaults cap (the cap gates NEW injections, not the
        // completion of an established exchange — capping here would hang
        // the source load).
        if (l04_pending && inst && inst->seqNum == l04_pending_tgt_seq) {
            l04_pending = false;
            return l04_pending_src;
        }

        // G5 single-fault cap BEFORE onAttempt (C11 convention: with the
        // campaign cap the counters freeze at fire time — exact).
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return inst;

        // The pairing point's attempt stream: EVERY response delivered via
        // completeDataAccess (loads, stores, atomics — C11's "the hook is
        // the attempt stream" convention).
        lsuTrigger->onAttempt();

        // Eligibility gate 1 (shape): a plain register-writeback load's
        // response (store/atomic/SC/squashed responses return here —
        // attempted, never the event).
        if (!src.eligible_shape || src.size == 0)
            return inst;

        // Eligibility gate 2 (the model's own trigger condition "同时存在
        // 至少两个在途load且发生cache response"): a live same-shape
        // candidate must exist. The scan is lazy — paid only past gate 1.
        std::vector<RespPairCand> cands;
        if (scan)
            scan(cands);
        if (cands.empty())
            return inst;

        // Trigger decision. F6 ([MDSPEC][R4-5.1-review-I1] accounting):
        // onAttempt above already booked this invocation — onF6Event(false)
        // must not re-book attempted. F6 = the FIRST response that passes
        // BOTH gates (the eligible-event first-occurrence, early_stress).
        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return inst;

        // Fire: choose the partner uniformly among the candidates (seeded
        // mt19937 — reproducible with --rng_seed; the spec does not pin a
        // choice rule, recorded here).
        const RespPairCand &b = cands[rng() % cands.size()];

        // Establish the exchange (half 2 completes it).
        l04_pending = true;
        l04_pending_src = inst;
        l04_pending_tgt_seq = b.seq;

        // Propagation registration: inj node (corr=origin; before/after =
        // the pairing mapping source-seq -> target-seq, the faulted VALUE
        // of this model, lifted to the unified stream via the writeNode
        // dual-emit old_addr/new_addr keys) + the EXCHANGED pairing table
        // as two seq-bound addr-registry entries: [src_va,+size) bound to
        // the TARGET seq (half 1's noteMemResponse hits: packet = A's
        // response, inst = B), [tgt_va,+size) bound to the SOURCE seq
        // (half 2 hits). Address collision (same-VA loads): one map key —
        // the half-1 binding wins and half 2 has no seq-bound surface
        // (recorded in the registration, never papered over with an
        // address-only join — the 09 sheet forbids address single-key
        // chains).
        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            tr->registerRespPairFault(
                src.seq, src.lq_idx, src.request_id, src.vaddr, src.size,
                b.seq, b.lq_idx, b.request_id, b.vaddr, b.size);
        }

        ++faults_injected_count;
        if (stats)
            stats->numFaultsInjected++;
        // [R6-S-REPAIR2 2026-10-30] real injection: arm controlled guest SEGV.
        chaos::noteChaosInjection();
        // Injection-log line (L0 parses the "Tick: …, Site: …, mode=…,
        // faults_injected:" contract — tools/lsu_obs_core._INJ_RE; the
        // source/target IDs are the L04 pairing keys the spec requires to
        // be saved: "保存 source/target ID").
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: completeDataAccess_response_pairing"
                << ", mode=resp_pairing (L04-b target exchange)"
                << ", source_dyn_inst_seq=" << src.seq
                << ", source_lq_idx=" << src.lq_idx
                << ", source_request_id=" << src.request_id
                << ", source_va=0x" << std::hex << src.vaddr << std::dec
                << ", target_dyn_inst_seq=" << b.seq
                << ", target_lq_idx=" << b.lq_idx
                << ", target_request_id=" << b.request_id
                << ", target_va=0x" << std::hex << b.vaddr << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        DPRINTF(LSQUnit, "CHAOSLSQFwd: L04 resp-pairing exchange "
                "src seq %llu -> tgt seq %llu\n",
                (unsigned long long)src.seq, (unsigned long long)b.seq);
        return b.inst;
    }

    // [MDSPEC][R4-5.7] S10 StoreSet SSIT-ID 换值 (S10-a). See CHAOSLSQFwd.hh
    // for the model ruling; the hooks below are the single consumer the
    // chaosS10* globals point at while an S10-armed injector is mounted.
    CHAOSLSQFwd *CHAOSLSQFwd::s10_active = nullptr;

    // [MDSPEC][R4-9-FSMC] O06/O07 single armed consumer (the static
    // callbacks registered into the chaosBarrier* globals act through it).
    CHAOSLSQFwd *CHAOSLSQFwd::barrier_active = nullptr;

    // ---- [MDSPEC][R4-9-FSMC] O06/O07 barrier bookkeeping hooks ------------
    // Called from MemDepUnit (mem_dep_unit.cc) via the chaosBarrier* globals;
    // this injector is the single consumer. `seq` is the barrier's
    // InstSeqNum (the platform's order tag — see chaos_barrier_hook.hh).

    bool
    CHAOSLSQFwd::barrierInsertCb(uint64_t seq, bool is_read, bool is_write)
    {
        // Defensive: the globals are cleared by the dtor, so a torn-down
        // injector is never reached. The armed instance is the single
        // registered consumer (chaos_barrier_active).
        CHAOSLSQFwd *self = barrier_active;
        if (!self || !self->lsuTrigger)
            return false;
        // Ledger first: the injector's view of the live barrier SNs must
        // mirror the MemDepUnit's own set (O07's substitute picker reads it).
        ++self->barrier_inserts_seen;
        self->barrier_live_sns.push_back(seq);
        const bool corrupt = self->maybeCorruptBarrierInsert(seq, is_read,
                                                             is_write);
        if (corrupt) {
            // O06-a: the SN will NOT be tracked by the MemDepUnit — drop it
            // from the ledger so both views stay identical.
            if (!self->barrier_live_sns.empty())
                self->barrier_live_sns.pop_back();
        }
        return corrupt;
    }

    int
    CHAOSLSQFwd::barrierReleaseCb(uint64_t seq, bool is_read, bool is_write,
                                  uint64_t *subst)
    {
        CHAOSLSQFwd *self = barrier_active;
        if (!self || !self->lsuTrigger)
            return 0;
        return self->maybeCorruptBarrierRelease(seq, is_read, is_write,
                                                subst);
    }

    // O06-a "early done": consent => the SN is NOT tracked. The insert event
    // itself is the attempt stream; only the F6 tier fires ON the insert,
    // every other tier samples the inserts through onEligible().
    bool
    // [R4-8-INT] 形参名必须写全：函数体第 858 行的注入日志要打印 barrier SN
    // （= seq）。原为无名形参 (uint64_t, bool, bool)，编译报
    // "'seq' was not declared in this scope"（编译未验证分支的漏网）。
    CHAOSLSQFwd::maybeCorruptBarrierInsert(uint64_t seq, bool, bool)
    {
        if (!o06_mode || !o06_early)
            return false;                     // stuck (b) acts at release
        if (max_faults != 0 && barrier_injections >= max_faults)
            return false;
        lsuTrigger->onAttempt();
        const bool go = (lsuTrigger->tier == ChaOSLsuTier::F6)
                            ? lsuTrigger->onF6Event(false)
                            : lsuTrigger->onEligible();
        if (!go)
            return false;
        ++barrier_injections;
        ++faults_injected_count;
        if (stats)
            stats->numFaultsInjected++;
        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            std::vector<std::pair<std::string, std::string>> kv = {
                {"field", "barrier_done"},
                {"state_before", "tracked"},
                {"state_after", "early_released"},
                {"corr", "origin"},
            };
            tr->notePropEvt("barrier_done", kv);
        }
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream())
                << "Tick: " << curTick() << ", Field: barrier_done "
                << "(O06-a early done, barrier SN " << seq
                << " NOT tracked), injections: " << barrier_injections
                << std::endl;
        }
        return true;
    }

    // O06-b "done stuck" / O07 order-tag exchange, both decided at the
    // release point. Returns the chaos_barrier_hook.hh code (0/1/2).
    int
    CHAOSLSQFwd::maybeCorruptBarrierRelease(uint64_t seq, bool is_read,
                                            bool is_write, uint64_t *subst)
    {
        ++barrier_releases_seen;
        // The release is also the ledger's removal point (both the normal
        // path and the injected ones) — the injector's view must stay in
        // sync with the MemDepUnit's.
        auto drop = [this](uint64_t sn) {
            for (auto it = barrier_live_sns.begin();
                 it != barrier_live_sns.end(); ++it) {
                if (*it == sn) { barrier_live_sns.erase(it); return; }
            }
        };

        if (o06_mode && !o06_early) {         // O06-b: stuck
            if (max_faults != 0 && barrier_injections >= max_faults)
                return 0;
            lsuTrigger->onAttempt();
            const bool go = (lsuTrigger->tier == ChaOSLsuTier::F6)
                                ? lsuTrigger->onF6Event(false)
                                : lsuTrigger->onEligible();
            if (!go)
                return 0;
            ++barrier_injections;
            ++faults_injected_count;
            if (stats)
                stats->numFaultsInjected++;
            // The SN stays in the ledger too (it was never released).
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::vector<std::pair<std::string, std::string>> kv = {
                    {"field", "barrier_done"},
                    {"state_before", "should_release"},
                    {"state_after", "stuck"},
                    {"corr", "origin"},
                };
                tr->notePropEvt("barrier_done", kv);
            }
            if (write_log && log_stream && log_stream->stream()) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Field: barrier_done "
                    << "(O06-b done lost: barrier SN " << seq
                    << " stays tracked), injections: " << barrier_injections
                    << std::endl;
            }
            return 1;
        }

        if (o07_mode) {                       // O07: order-tag exchange
            if (max_faults != 0 && barrier_injections >= max_faults) {
                drop(seq);
                return 0;
            }
            lsuTrigger->onAttempt();
            const bool go = (lsuTrigger->tier == ChaOSLsuTier::F6)
                                ? lsuTrigger->onF6Event(false)
                                : lsuTrigger->onEligible();
            if (!go) {
                drop(seq);
                return 0;
            }
            // [MDSPEC][R4-9-FSMC] the substitute must be ANOTHER LEGAL LIVE
            // tag (workbook 实施细则) — the ledger holds exactly those.
            // With none, the injection is honestly skipped (attempted,
            // never eligible: the spec's "至少2个相关事务" gate).
            const uint64_t other = orderTagSubstitute(seq);
            if (other == 0) {
                drop(seq);
                return 0;
            }
            drop(other);
            if (subst)
                *subst = other;
            ++barrier_injections;
            ++faults_injected_count;
            if (stats)
                stats->numFaultsInjected++;
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::vector<std::pair<std::string, std::string>> kv = {
                    {"field", "order_tag"},
                    {"state_before", std::to_string(seq)},
                    {"state_after", std::to_string(other)},
                    {"corr", "origin"},
                };
                tr->notePropEvt("order_tag", kv);
            }
            if (write_log && log_stream && log_stream->stream()) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Field: order_tag "
                    << "(O07 swap: released SN " << other << " instead of "
                    << seq << "), injections: " << barrier_injections
                    << std::endl;
            }
            return 2;
        }

        drop(seq);
        return 0;
    }

    // O07 substitute picker: another live barrier SN (never a fabricated
    // value). LIFO so a long-lived earlier barrier is the preferred swap
    // partner, matching the spec's "交换两个在飞事务" reading.
    uint64_t
    CHAOSLSQFwd::orderTagSubstitute(uint64_t seq)
    {
        for (auto it = barrier_live_sns.rbegin();
             it != barrier_live_sns.rend(); ++it) {
            if (*it != seq)
                return *it;
        }
        return 0;
    }

    void
    CHAOSLSQFwd::s10ViolationCb(Addr store_pc, Addr load_pc,
                                uint64_t load_ssid_now, bool load_ssid_valid)
    {
        if (!s10_active || !s10_active->lsuTrigger)
            return;

        // (a) ssit_violation (L2): a memory-ordering violation was detected
        // on a corrupted load PC — the missed-dependence manifestation.
        // Cap-INDEPENDENT (mechanical chain evidence of the already-injected
        // fault, L04 half-2 discipline: the cap gates NEW injections).
        // state_before = the SSID still mapped to that PC at violation time
        // (== the substituted SSID while the corruption is live; a healed
        // retrain shows the merged value — the stream stays honest either
        // way). Caveat recorded in the report: violations on that PC can
        // also occur naturally (the SSIT is a predictor, not a guarantee);
        // this event witnesses the co-occurrence, the causal reading rests
        // on the preceding ssit_consult's before/after divergence.
        auto it = s10_active->s10_entries.find(load_pc);
        // [R6-S-REPAIR2 2026-10-30] A violation on the corrupted PC only
        // belongs to this chain when the corruption actually changed the
        // predicted dependency. A no-effect consult's L2 containment is not
        // invalidated by an unrelated natural violation on the same PC.
        if (it != s10_active->s10_entries.end() &&
            it->second.wrong_prediction) {
            if (!it->second.consumed) {
                it->second.consumed = true;
                ++s10_active->s10_activated_count;
            }
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::ostringstream pc_hex;
                pc_hex << std::hex << load_pc;
                // kv pairs must be registry fields (unregistered keys are
                // warned + dropped by notePropEvt); the store PC stays in
                // the inj node's v1 detail (registerStoreSetFault) and the
                // injection-log line, not on this unified event.
                tr->notePropEvt("ssit_violation", {
                    {"fault_id", std::to_string(it->second.ptag)},
                    {"pc", pc_hex.str()},
                    {"field", "dep_miss_violation"},
                    {"state_before",
                     load_ssid_valid ? std::to_string(load_ssid_now)
                                     : "invalid"},
                    {"corr", "origin"},
                });
            }
            if (s10_active->write_log && s10_active->log_stream &&
                s10_active->log_stream->stream()) {
                *(s10_active->log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: StoreSet_violation_retrain"
                    << ", mode=ssit_violation (S10 dep-miss manifestation)"
                    << ", load_pc=0x" << std::hex << load_pc << std::dec
                    << ", load_ssid_now="
                    << (load_ssid_valid ? std::to_string(load_ssid_now)
                                        : std::string("invalid"))
                    << ", faults_injected: "
                    << s10_active->faults_injected_count
                    << std::endl;
            }
        }

        // (b) maxFaults cap BEFORE onAttempt (C11 convention: with the
        // campaign cap the funnel counters freeze at fire time — exact).
        if (s10_active->max_faults != 0 &&
            s10_active->faults_injected_count >= s10_active->max_faults)
            return;

        // (c) The attempt stream: EVERY StoreSet training event (the hook
        // is the top of StoreSet::violation). Eligibility (the new-SSID
        // assignment arm + a live candidate) is decided at the subst hook.
        s10_active->lsuTrigger->onAttempt();
    }

    bool
    CHAOSLSQFwd::s10SsidSubstCb(Addr store_pc, Addr load_pc,
                                uint64_t true_ssid, const S10SsidScan &scan,
                                uint64_t *out_ssid)
    {
        if (!s10_active || !s10_active->lsuTrigger || !out_ssid)
            return false;

        // [R6-S-S10 2026-10-30] maxFaults gates NEW injections at THIS site
        // too. The violation-top check only freezes the attempt stream; the
        // substitution hook still ran and injected (measured on S10-F5-W5:
        // maxFaults=1 but 3 real writes). Cap first, before any attempt or
        // eligibility accounting, so attempted/eligible/injected reconcile.
        if (s10_active->max_faults != 0 &&
            s10_active->faults_injected_count >= s10_active->max_faults)
            return false;

        // [MDSPEC][R4-5.7b] FUNNEL FORK-POINT INSTRUMENTATION (observation
        // only — no decision below depends on these counters). Reaching this
        // line at all means StoreSet::violation took its "brand-new store
        // set" arm with the S10 hook mounted; this call site is therefore
        // exactly the arm-1 entry point the R4-5.7b triage needs to count.
        ++s10_active->s10_arm1_events;
        if (std::find(s10_active->s10_arm1_load_pcs.begin(),
                      s10_active->s10_arm1_load_pcs.end(), load_pc) ==
            s10_active->s10_arm1_load_pcs.end())
            s10_active->s10_arm1_load_pcs.push_back(load_pc);

        // Workbook 07 实施细则: the substituted value must be ANOTHER
        // LEGAL live value from the current run — no random bit strings.
        // Candidate set = SSIDs of currently valid SSIT entries (live
        // store sets; free/idle SSIDs are excluded by construction — only
        // present entries scan), minus the true SSID. Lazy scan (L04
        // RespPairScan precedent): paid only here, in the assignment arm.
        std::vector<uint64_t> live;
        if (scan)
            scan(live);
        std::vector<uint64_t> cands;
        for (uint64_t s : live)
            if (s != true_ssid &&
                std::find(cands.begin(), cands.end(), s) == cands.end())
                cands.push_back(s);
        // [MDSPEC][R4-5.7b] Record the two observable quantities behind the
        // fork: how many DISTINCT live store-sets the SSIT held (== 1 means
        // "this run only ever uses one store-set" — triage class (d)) and
        // how wide the legal candidate set was.
        {
            std::vector<uint64_t> distinct_live;
            for (uint64_t s : live)
                if (std::find(distinct_live.begin(), distinct_live.end(), s)
                        == distinct_live.end())
                    distinct_live.push_back(s);
            if (distinct_live.size() > s10_active->s10_max_live_ssids)
                s10_active->s10_max_live_ssids = distinct_live.size();
            if (cands.size() > s10_active->s10_max_cands)
                s10_active->s10_max_cands = cands.size();
        }
        if (cands.empty()) {
            ++s10_active->s10_arm1_cand_empty;   // (a)/(b)/(d) predicate hit
            return false;   // no other live store set — not eligible
        }
        ++s10_active->s10_arm1_cand_ok;

        // Trigger decision. F6 ([MDSPEC][R4-5.1-review-I1] accounting):
        // the attempt was already booked by s10ViolationCb's onAttempt —
        // onF6Event(false) must not re-book it. F6 = the first eligible
        // assignment event (early_stress first-occurrence, A5 ruling).
        bool go;
        if (s10_active->lsuTrigger->tier == ChaOSLsuTier::F6) {
            go = s10_active->lsuTrigger->onF6Event(false);
        } else {
            go = s10_active->lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        // Fire: choose the target uniformly among the candidates (seeded
        // mt19937 — reproducible with --rng_seed; the spec does not pin a
        // choice rule, recorded here). The value is legal by construction
        // (it came from the live SSIT, so < LFSTSize holds).
        const uint64_t target = cands[s10_active->rng() % cands.size()];

        // Propagation registration: inj node only (corr=origin; the
        // before/after pair = the faulted VALUE of this model, the SSID
        // assignment). NO addr/seq registry entry — a PC-keyed predictor
        // state has no correlate surface; chain members are this
        // injector's own PC-keyed emissions (pf_train precedent).
        uint64_t ptag = 0;
        if (CHAOSPropagation *tr = CHAOSPropagation::instance())
            ptag = tr->registerStoreSetFault(store_pc, load_pc, true_ssid,
                                             target, cands.size());

        // Consumption table (single-slot-per-PC: re-corruption of the same
        // PC — only possible with maxFaults=0/unlimited — overwrites; the
        // previous chain then has no live consumption surface, recorded in
        // the .hh comment rather than papered over).
        // [R6-S-REPAIR2 2026-10-30] Overwrite-before-use: a previous
        // corruption of this PC is replaced by this new injection. If it
        // never changed a decision (no wrong prediction reached issue) and
        // was not contained yet, close its chain at the real overwrite point.
        auto prev = s10_active->s10_entries.find(load_pc);
        if (prev != s10_active->s10_entries.end() &&
            !prev->second.effective_emitted &&
            !prev->second.contained_emitted) {
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::ostringstream pc_hex;
                pc_hex << std::hex << load_pc;
                tr->notePropEvt("ssit_epoch_clear", {
                    {"fault_id", std::to_string(prev->second.ptag)},
                    {"pc", pc_hex.str()},
                    {"field", "ssid_overwritten"},
                    {"state_before",
                     std::to_string(prev->second.subst_ssid)},
                    {"detection_layer", "L1"},
                    {"contained", "1"},
                    {"outcome", "contained"},
                    {"containment_layer", "L1"},
                    {"containment_reason",
                     "overwritten_before_decision_change"},
                    {"corr", "origin"},
                });
            }
            prev->second.contained_emitted = true;
        }

        S10Entry entry;
        entry.ptag = ptag;
        entry.true_ssid = true_ssid;
        entry.subst_ssid = target;
        s10_active->s10_entries[load_pc] = entry;

        // [R6-S-REPAIR2 2026-10-30] L1 witness: the SSIT field now holds the
        // substituted SSID (the corrupted state exists). parent = inj.
        if (ptag) {
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::ostringstream pc_hex;
                pc_hex << std::hex << load_pc;
                tr->notePropEvt("ssit_corrupt", {
                    {"fault_id", std::to_string(ptag)},
                    {"pc", pc_hex.str()},
                    {"field", "ssid"},
                    {"before", std::to_string(true_ssid)},
                    {"after", std::to_string(target)},
                    {"entry_index", std::to_string(target)},
                    {"corr", "origin"},
                });
            }
        }

        ++s10_active->faults_injected_count;
        if (s10_active->stats)
            s10_active->stats->numFaultsInjected++;
        // [R6-S-REPAIR2 2026-10-30] real S10 injection: arm guest SEGV.
        chaos::noteChaosInjection();
        // [R6-S-S10 2026-10-30] F5 separates fire from outcome: report the
        // REAL write so trigger.injected == injection log == stats (pre-fix
        // fires=3 / outcomes_recorded=0 / injected=0 was a reporting bug).
        if (s10_active->lsuTrigger->tier == ChaOSLsuTier::F5)
            s10_active->lsuTrigger->noteOutcome(true);
        // Injection-log line (L0 parses the "Tick: …, Site: …, mode=…,
        // old_ssid/new_ssid, …, faults_injected:" contract —
        // tools/lsu_obs_core._INJ_RE; source/target + the candidate-set
        // size are the workbook's "保存 source/target 及候选集合").
        if (s10_active->write_log && s10_active->log_stream &&
            s10_active->log_stream->stream()) {
            *(s10_active->log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: StoreSet_violation_ssid_assign"
                << ", mode=ssid_subst (S10-a SSIT-ID 换值)"
                << ", old_ssid=" << true_ssid
                << ", new_ssid=" << target
                << ", store_pc=0x" << std::hex << store_pc << std::dec
                << ", load_pc=0x" << std::hex << load_pc << std::dec
                << ", ssid_candidates=" << cands.size()
                << ", faults_injected: "
                << s10_active->faults_injected_count
                << std::endl;
        }
        // [R4-5.7-integration] 这里原本有一行 DPRINTF/DPRINTFN 诊断输出，
        // 构建三次失败后移除：本函数是 **static 成员**（StoreSet 侧回调），
        // 无 this → `name()` 取不到宿主；而 gem5 v25 的 DPRINTF **与**
        // DPRINTFN（src/base/trace.hh:212/240）**都**调用 `name()`，故无一
        // 适用于无宿主静态回调。该行纯属诊断：本次替换的全部事实已由上方
        // 写入 `lsq_fwd_injections.log`（old_ssid/new_ssid/candidates/
        // faults_injected 契约）并计入 `faults_injected_count` 与
        // `numFaultsInjected` 统计——证据链完整，不因删除该行而缺失。
        (void)load_pc;
        *out_ssid = target;
        return true;
    }

    void
    CHAOSLSQFwd::s10IssuedCb(Addr pc)
    {
        if (!s10_active)
            return;
        auto it = s10_active->s10_entries.find(pc);
        if (it == s10_active->s10_entries.end())
            return;
        S10Entry &e = it->second;
        if (!e.wrong_prediction || e.effective_emitted)
            return;
        e.effective_emitted = true;
        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            std::ostringstream pc_hex;
            pc_hex << std::hex << pc;
            tr->notePropEvt("ssit_dep_effective", {
                {"fault_id", std::to_string(e.ptag)},
                {"pc", pc_hex.str()},
                {"field", "pred_dep_effective"},
                {"before", std::to_string(e.dep_before)},
                {"after", std::to_string(e.dep_after)},
                {"entry_index", std::to_string(e.subst_ssid)},
                {"corr", "origin"},
            });
        }
    }

    void
    CHAOSLSQFwd::s10ClearCb()
    {
        if (!s10_active)
            return;
        // [R6-S-REPAIR2 2026-10-30] Real epoch boundary. A corrupted entry
        // that never changed the predicted dependency is contained here:
        // it was discarded before it could affect a decision. Entries whose
        // wrong prediction already reached issue are NOT contained.
        for (auto &kv : s10_active->s10_entries) {
            S10Entry &e = kv.second;
            if (e.effective_emitted || e.contained_emitted ||
                e.wrong_prediction)
                continue;
            e.contained_emitted = true;
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::ostringstream pc_hex;
                pc_hex << std::hex << kv.first;
                tr->notePropEvt("ssit_epoch_clear", {
                    {"fault_id", std::to_string(e.ptag)},
                    {"pc", pc_hex.str()},
                    {"field", e.consulted ? "ssid_clear_after_no_effect"
                                          : "ssid_clear_before_use"},
                    {"state_before", std::to_string(e.subst_ssid)},
                    {"detection_layer", "L1"},
                    {"contained", "1"},
                    {"outcome", "contained"},
                    {"containment_layer", "L1"},
                    {"containment_reason", e.consulted
                        ? "epoch_clear_after_no_decision_change"
                        : "epoch_clear_before_use"},
                    {"corr", "origin"},
                });
            }
        }
        s10_active->s10_entries.clear();
    }

    bool
    CHAOSLSQFwd::s10CorruptedPcCb(Addr pc, uint64_t *true_ssid)
    {
        if (!s10_active || !true_ssid)
            return false;
        auto it = s10_active->s10_entries.find(pc);
        if (it == s10_active->s10_entries.end())
            return false;
        *true_ssid = it->second.true_ssid;
        return true;
    }

    void
    CHAOSLSQFwd::s10ConsultCb(Addr pc, uint64_t actual_ssid,
                              uint64_t actual_dep, uint64_t counterfactual_dep)
    {
        if (!s10_active)
            return;
        auto it = s10_active->s10_entries.find(pc);
        if (it == s10_active->s10_entries.end())
            return;

        // The corrupted SSIT entry was READ by the prediction path — the
        // workbook's 激活口径 ("故障值被下游实际读取、选择或消费"). Whether
        // the prediction actually CHANGED is readable on the stream
        // (before=counterfactual vs after=actual producing-store seq).
        if (!it->second.consumed) {
            it->second.consumed = true;
            ++s10_active->s10_activated_count;
        }
        it->second.consulted = true;
        it->second.dep_before = counterfactual_dep;
        it->second.dep_after = actual_dep;

        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            std::ostringstream pc_hex;
            pc_hex << std::hex << pc;
            tr->notePropEvt("ssit_consult", {
                {"fault_id", std::to_string(it->second.ptag)},
                {"pc", pc_hex.str()},
                {"field", "pred_dep"},
                {"before", std::to_string(counterfactual_dep)},
                {"after", std::to_string(actual_dep)},
                {"entry_index", std::to_string(actual_ssid)},
                {"corr", "origin"},
            });
        }

        // [R6-S-REPAIR2 2026-10-30] Real L2 detected containment: the
        // corrupted entry was read, but the predicted dependency equals the
        // counterfactual (the substituted SSID's LFST slot produced the same
        // answer). No decision changed at this read. A LATER consult with
        // before != after emits ssit_dep_effective at issue (L3), which
        // disqualifies this L2 containment in the chain checker.
        if (actual_dep == counterfactual_dep && !it->second.wrong_prediction &&
            !it->second.no_effect_emitted) {
            it->second.no_effect_emitted = true;
            if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
                std::ostringstream pc_hex;
                pc_hex << std::hex << pc;
                tr->notePropEvt("ssit_no_effect", {
                    {"fault_id", std::to_string(it->second.ptag)},
                    {"pc", pc_hex.str()},
                    {"field", "pred_dep_unchanged"},
                    {"before", std::to_string(counterfactual_dep)},
                    {"after", std::to_string(actual_dep)},
                    {"entry_index", std::to_string(actual_ssid)},
                    {"detection_layer", "L2"},
                    {"contained", "1"},
                    {"outcome", "contained"},
                    {"containment_layer", "L2"},
                    {"containment_reason",
                     "ssit_consult_prediction_unchanged"},
                    {"corr", "origin"},
                });
            }
        } else if (actual_dep != counterfactual_dep) {
            it->second.wrong_prediction = true;
        }
        // [R4-5.7-integration] 这里原本有一行 DPRINTF(LSQUnit, ...) 诊断输出，
        // 构建失败两次后移除：
        //   1) DPRINTF 需要 `name()`，而本处是 StoreSet 侧的**自由桥函数**
        //      （无 this、无 Named 宿主）→ "没有对象无法调用成员函数
        //      'gem5::Named::name'"；
        //   2) 换用无宿主变体 DPRINTFN 后仍报 `'LSQUnit' 在此作用域中尚未声明`
        //      （该 debug flag 声明于 gem5::debug，此作用域未引入）。
        // 该行纯属诊断：consult 已由上方 `notePropEvt("ssit_consult", …)`
        // **完整记录在统一传播流上**（pc/fault_id/before/after/entry_index 全字段），
        // 证据链不受影响——故不再为此引入调试作用域改动。
        (void)pc;
    }

} // namespace gem5
