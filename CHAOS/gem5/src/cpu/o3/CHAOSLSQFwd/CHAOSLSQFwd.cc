#include "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSLSQFwd.hh"

#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>   // [MDSPEC][R4-5.7] std::find (S10 candidate dedup)

#include "base/output.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"   // [MDSPEC][R4-5.3] full DynInst (resp-pair)
#include "debug/LSQUnit.hh"
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [MDSPEC][H3-FWD]

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
        }
        if (lsuTrigger) {
            // W5: funnel lines at exit (chaos_l0 discipline: log file, not
            // stdout). activated = same near-tautological approximation as
            // CHAOSAddrPath (the forwarded data is consumed by the load's
            // writeback immediately after this hook).
            registerExitCallback([this]() {
                if (lsuTrigger)
                    lsuTrigger->summary("CHAOSLSQFwd");
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

    void
    CHAOSLSQFwd::writeLog(const char *type, unsigned size, Addr vaddr,
                          int byte_off, int mask, const FwdCorrelKeys &keys)
    {
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
        if (CHAOSPropagation *tr = CHAOSPropagation::instance()) {
            const uint64_t ptag = tr->registerLSQForwardFault(
                keys.store_dyn_inst_seq, keys.sq_idx, keys.store_request_id,
                keys.load_dyn_inst_seq, keys.lq_idx, keys.load_request_id,
                vaddr, size ? size : 1, "lsqfwd_forward");
            if (ptag) {
                std::ostringstream a;
                a << std::hex << vaddr;
                tr->notePropEvt("lsq_fwd", {
                    {"fault_id", std::to_string(ptag)},
                    {"dyn_inst_seq", std::to_string(keys.load_dyn_inst_seq)},
                    {"store_dyn_inst_seq",
                     std::to_string(keys.store_dyn_inst_seq)},
                    {"sq_idx", std::to_string(keys.sq_idx)},
                    {"lq_idx", std::to_string(keys.lq_idx)},
                    {"request_id", std::to_string(keys.load_request_id)},
                    {"va", a.str()},
                    {"pa", a.str()},
                    {"field", type},
                    {"before", "store_data"},
                    {"after", std::string("fwd_corrupt:") + type},
                    {"corr", keys.store_dyn_inst_seq ? "seq_primary"
                                                     : "addr_fallback"},
                });
            }
        }
        if (!write_log) return;
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
    }

    void
    CHAOSLSQFwd::corrupt(uint8_t *data, unsigned size, Addr vaddr,
                         const FwdCorrelKeys &keys)
    {
        // Hot-path short-circuit: no injection configured.
        if (probability <= 0.0f) return;
        // fwd_source_sub injects at the DECISION point (maybeSubstituteSource,
        // called before the memcpy); this post-forward corrupt hook must NOT
        // also fire in that mode (double-injection bug found in Phase 4.2
        // verification: an unlimited-faults run showed bit_flip lines while
        // in fwd_source_sub mode — the old hook was still active).
        // phase_offset likewise acts at the WRITEBACK-SCHEDULE point
        // (maybeDelayForward) — no data mutation there either.
        if (struct_mode == StructMode::FwdSourceSub) return;
        if (struct_mode == StructMode::PhaseOffset) return;
        // [LSU][SEM-B] L03 hook split: with --lsqfwd_l03 the SQ-forward
        // data path is NOT L03's event source — the trigger stream must be
        // violation checks only (checkViolations site), not the mixed stream.
        if (l03_mode) return;
        // [MDSPEC][R4-5.3] L04 hook split, same discipline: with
        // --lsqfwd_l04 the SQ-forward data path is NOT L04's event source —
        // the trigger stream is the response-pairing point only
        // (LSQUnit::completeDataAccess, maybeSwapResponseTarget).
        if (l04_mode) return;
        // [MDSPEC][R4-5.7] S10 hook split, same discipline: with
        // --lsqfwd_s10 the SQ-forward data path is NOT S10's event source —
        // the trigger stream is the StoreSet SSIT-training point only
        // (StoreSet::violation, chaosS10* hooks).
        if (s10_mode) return;
        if (lsuTrigger) {
            // LSU W2/W5 path (05 r2-r8): the event-normalized trigger owns
            // warm-up/repetition semantics; the legacy cycle window,
            // events_to_skip and the Bernoulli roll do NOT apply here.
            lsuTrigger->onAttempt();
            if (!lsuTrigger->onEligible()) return;
        } else {
            Cycles cur = cpu->curCycle();
            if (cur < first_clock) return;
            if (last_clock != Cycles(0) && cur > last_clock) return;
            if (max_faults != 0 && faults_injected_count >= max_faults) return;

            // Sampling-bias fix (findings.md Phase 2.2): skip the first N
            // eligible forwarding events (N ~ geometric(0.1) from the seed)
            // so the single fault lands on a seed-dependent event.
            if (count_only) { ++eligible_count; return; }
            if (events_to_skip > 0) {
                --events_to_skip;
                return;
            }

            // Bernoulli: does this forwarding event get corrupted?
            std::uniform_real_distribution<float> dist(0.0f, 1.0f);
            if (dist(rng) >= probability) return;
        }
        if (size == 0) return;

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
            writeLog("byte_lane_skew", size, vaddr, lane_skew_k, 0, keys);
            DPRINTF(LSQUnit, "CHAOSLSQFwd: byte_lane_skew rol %d (vaddr=%#x)\n",
                    lane_skew_k, vaddr);
            return;
        }
        if (struct_mode == StructMode::AllZero) {
            for (unsigned i = 0; i < size; i++) data[i] = 0;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            writeLog("all_zero", size, vaddr, 0, 0, keys);
            DPRINTF(LSQUnit, "CHAOSLSQFwd: all_zero (vaddr=%#x size=%u)\n",
                    vaddr, size);
            return;
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
        writeLog(faultTypeToString(chosen), size, vaddr, off, mask, keys);
        DPRINTF(LSQUnit, "CHAOSLSQFwd: corrupted forwarded byte %d (vaddr=%#x "
                "mask=%#x type=%s)\n", off, vaddr, mask,
                faultTypeToString(chosen));
    }

    bool
    CHAOSLSQFwd::maybeSubstituteSource(uint8_t *load_data,
                                       const uint8_t *true_src,
                                       unsigned copy_size,
                                       const uint8_t *alt_src,
                                       unsigned alt_size, Addr vaddr)
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
        if (it != s10_active->s10_entries.end()) {
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
        if (cands.empty())
            return false;   // no other live store set — not eligible

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
        s10_active->s10_entries[load_pc] =
            S10Entry{ptag, true_ssid, false};

        ++s10_active->faults_injected_count;
        if (s10_active->stats)
            s10_active->stats->numFaultsInjected++;
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
        DPRINTF(LSQUnit, "CHAOSLSQFwd: S10 SSIT ssid subst load_pc=%#x "
                "true=%llu -> %llu (candidates=%zu)\n", load_pc,
                (unsigned long long)true_ssid, (unsigned long long)target,
                cands.size());
        *out_ssid = target;
        return true;
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
            });
        }
        DPRINTF(LSQUnit, "CHAOSLSQFwd: S10 consult load_pc=%#x ssid=%llu "
                "dep=%llu (counterfactual %llu)\n", pc,
                (unsigned long long)actual_ssid,
                (unsigned long long)actual_dep,
                (unsigned long long)counterfactual_dep);
    }

} // namespace gem5
