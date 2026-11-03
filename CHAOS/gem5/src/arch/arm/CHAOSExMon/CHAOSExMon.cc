#include "arch/arm/CHAOSExMon/CHAOSExMon.hh"

#include "arch/arm/isa.hh"  // ArmISA::ISA (full def for setChaosExMon)
#include "arch/generic/pcstate.hh"  // PCStateBase::instAddr (ROI filter)
#include "cpu/exec_context.hh"      // ExecContext (ROI PC + dest regs)
#include "mem/request.hh"
#include "debug/CHAOSExMon.hh"
#include "params/CHAOSExMon.hh"
// [MDSPEC][H6] exmon faults register with the propagation tracer through
// the static instance (CHAOSCache precedent — the ISA has no tracer ptr).
#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"
#include <sstream>

namespace gem5
{

    CHAOSExMon::CHAOSExMon(const CHAOSExMonParams &p)
        : SimObject(p),
          isa(dynamic_cast<ArmISA::ISA *>(p.isa)),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          pc_lo(p.pcLo),
          pc_hi(p.pcHi),
          lsu_tier(p.lsuTier),
          lsu_span(p.lsuSpanEvents),
          lsu_warmup(p.lsuWarmupEvents)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("exmon_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSExMon: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            if (lsu_tier == "F0") {
                // [R6-O-ROI 2026-11-03] Matrix F0: uniform draw over the
                // eligible stream after warm-up. The legacy pre-drawn
                // geometric(0.1) skip can exceed a short FS stream (the
                // litmus loop has 39 LDXRs; seed 1 draws 55) and inject
                // nothing at all. A span-based uniform draw is exact.
                if (lsu_span == 0)
                    panic("CHAOSExMon: lsuTier=F0 requires lsuSpanEvents>0");
                events_to_skip = rng() % lsu_span;
                warmup_remaining = lsu_warmup;
                span_mode = true;
                inform("CHAOSExMon: tier=F0 span=%llu warmup=%llu "
                       "uniform_skip=%llu pc=[%#llx,%#llx)\n",
                       (unsigned long long)lsu_span,
                       (unsigned long long)lsu_warmup,
                       (unsigned long long)events_to_skip,
                       (unsigned long long)pc_lo,
                       (unsigned long long)pc_hi);
            } else if (lsu_tier == "F5") {
                // Permanent: every eligible event (maxFaults must be 0).
                span_mode = true;
                events_to_skip = 0;
                warmup_remaining = lsu_warmup;
                if (max_faults != 0)
                    panic("CHAOSExMon: lsuTier=F5 requires maxFaults=0");
                inform("CHAOSExMon: tier=F5 (every eligible event) "
                       "pc=[%#llx,%#llx)\n",
                       (unsigned long long)pc_lo,
                       (unsigned long long)pc_hi);
            } else {
                // Sampling-bias fix (findings.md Phase 2.2/3.0): legacy
                // geometric first-fire skip (SE default, unchanged).
                std::geometric_distribution<uint64_t> skip_dist(0.1);
                events_to_skip = skip_dist(rng);
            }
        }
        // SELF-ATTACH to the target ISA (same pattern as CHAOSArmSysReg).
        // ISA's `chaosExMon` field is public; set it so handleLockedWrite
        // can reach this injector. `isa` was passed as a Param.
        if (isa) {
            isa->setChaosExMon(this);
            inform("CHAOSExMon: SELF-ATTACH to ISA %s (mode=%s)\n",
                   isa->name(), p.mode.c_str());
        } else {
            warn("CHAOSExMon: isa is NULL; injector disabled.\n");
        }
    }

    CHAOSExMon::~CHAOSExMon() {}

    CHAOSExMon::Mode
    CHAOSExMon::stringToMode(const std::string &s) {
        if (s == "stxr_force_fail") return Mode::StxrForceFail;
        // W8 O-series (03-design-matrix O01/O02) — monitor-side faults on
        // the handleLockedRead path; the STXR verdict path passes through.
        if (s == "o01_monitor_addr_bitflip") return Mode::O01MonitorAddrBitflip;
        if (s == "o02_monitor_state_corrupt") return Mode::O02MonitorStateCorrupt;
        return Mode::StxrForceSuccess;
    }

    bool
    CHAOSExMon::inWindow() {
        // Frequency-correct: use the CPU's actual clock period for the
        // cycles->ticks conversion (C0 2GHz=500t/cyc, C2-KP 2.6GHz~385t/cyc).
        // The old *1000 assumed 1GHz — wrong on every config family we run
        // (pilot was C0, where the window opened at 2x the requested cycle).
        // NULL cpu falls back to the 1GHz nominal (documented approximation).
        Tick now = curTick();
        Tick period = cpu ? cpu->clockPeriod() : 1000;
        Tick f = first_clock * period;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * period) return false;
        return true;
    }

    bool
    CHAOSExMon::inRoi(ExecContext *xc) const
    {
        // No window configured: legacy whole-run eligibility (SE default).
        if (pc_hi == 0)
            return true;
        if (!xc)
            return false;
        const Addr pc = xc->pcState().instAddr();
        return pc >= pc_lo && pc < pc_hi;
    }

    bool
    CHAOSExMon::maybeCorrupt(const RequestPtr &req, bool would_succeed,
                             ExecContext *xc)
    {
        // [MDSPEC][H6] STXR consumption of an active monitor-side fault:
        // observe the (corrupted-monitor-driven) verdict as the terminal
        // consumption of the LDXR→STXR chain. The verdict is NOT mutated
        // here (O01/O02 only corrupt the monitor). Attaches to
        // active_monitor_ptag (LL-SC pairing key — the shared key the spec
        // names for O01). nullptr/no-active = no-op.
        //
        // Two distinct nodes, as the spec separates them:
        //   exmon_rmw  (L2) — the reservation compare that DECIDES
        //                     match/mismatch (cache/coherence compare point).
        //   exmon_stxr (L3) — the status/old-value consumption by the STXR,
        //                     carrying the 1-based retry attempt number.
        // state_before/state_after genuinely differ (reserved → outcome),
        // unlike the earlier form that printed the same value twice.
        //
        // [R6-O-ACT 2026-11-03] The corrupted monitor is authoritative for
        // this SC. On the O3 path the architectural LOCKADDR/LOCKFLAG write
        // is deferred to the LDXR's commit (DynInst::setMiscReg ->
        // updateMiscRegs), while this hook runs at STXR issue — so the
        // monitor a plain `would_succeed` reflects can be the PREVIOUS
        // reservation. That made the six 2026-10-23 monitor pilots inert
        // (97/97 exmon_stxr nodes said match_success). Evaluate the SC
        // comparison against the reservation the fault actually placed.
        if ((fi_mode == Mode::O01MonitorAddrBitflip ||
             fi_mode == Mode::O02MonitorStateCorrupt) &&
            active_monitor_ptag != 0 && req &&
            inRoi(xc)) {
            const uint64_t ptag = active_monitor_ptag;
            const Addr block_mask = ~Addr(0x3f);
            const bool match =
                active_monitor_flag &&
                ((req->getPaddr() & block_mask) ==
                 (active_monitor_addr & block_mask));
            if (CHAOSPropagation *h6s = CHAOSPropagation::instance()) {
                const uint64_t seq = req->hasInstSeqNum()
                    ? req->getReqInstSeqNum() : 0;
                // request_id names the CHAIN's owner request (the faulted
                // LDXR); dyn_inst_seq names the consuming STXR. Stamping the
                // STXR id here would open a SIBLING sub-chain (the emitPropEvt
                // request-scoped cursor), orphaning L2/L3 from the L0/L1
                // witnesses and defeating containment prefix proof.
                const uint64_t owner_seq = active_monitor_seq;
                ++active_monitor_attempts;
                std::ostringstream h6s_pa;
                h6s_pa << std::hex << req->getPaddr();
                h6s->notePropEvt("exmon_rmw", {
                    {"fault_id", std::to_string(ptag)},
                    {"dyn_inst_seq", std::to_string(seq)},
                    {"request_id", std::to_string(owner_seq)},
                    {"pa", h6s_pa.str()},
                    {"field", "reservation_compare"},
                    {"state_before", "reserved"},
                    {"state_after", match ? "match_success"
                                          : "mismatch_fail"},
                });
                if (match) {
                    h6s->notePropEvt("exmon_stxr", {
                        {"fault_id", std::to_string(ptag)},
                        {"dyn_inst_seq", std::to_string(seq)},
                        {"request_id", std::to_string(owner_seq)},
                        {"pa", h6s_pa.str()},
                        {"entry_index",
                         std::to_string(active_monitor_attempts)},
                        {"field", "stxr_consume"},
                        {"state_before", "reserved"},
                        {"state_after", "success"},
                    });
                } else {
                    // The corrupted reservation blocks the SC: the store is
                    // not performed and the status writeback reports failure,
                    // which the LL/SC retry loop consumes. That is a real
                    // containment witness at the unit's L3 consumption layer
                    // (no deeper observation follows on this chain).
                    h6s->notePropEvt("exmon_stxr", {
                        {"fault_id", std::to_string(ptag)},
                        {"dyn_inst_seq", std::to_string(seq)},
                        {"request_id", std::to_string(owner_seq)},
                        {"pa", h6s_pa.str()},
                        {"entry_index",
                         std::to_string(active_monitor_attempts)},
                        {"field", "stxr_consume"},
                        {"state_before", "reserved"},
                        {"state_after", "fail_retry"},
                        {"detection_layer", "L3"},
                        {"contained", "1"},
                        {"outcome", "corrupted_monitor_blocks_sc"},
                        {"corr", "addr_fallback"},
                        {"containment_layer", "L3"},
                        {"containment_reason",
                         "sc_mismatch_against_corrupted_monitor"},
                    });
                }
            }
            // The forced failure must also set VALID_EXTRA_DATA: the LSQ
            // insta-completes a failed SC without sending it, so the memory
            // system never sets extraData, and STXRW64::completeAcc asserts
            // on getExtraData() (src/mem/request.hh:912) — the same crash as
            // O03. The normal ISA failure path does this at isa.cc:1942.
            if (!match)
                req->setExtraData(0);
            // Retire the fault after the paired SC. Without this the ptag
            // stayed live for the rest of the run and every later STXR was
            // appended to it (measured: 97 pairs on one injected monitor).
            active_monitor_ptag = 0;
            active_monitor_block = 0;
            active_monitor_addr = 0;
            active_monitor_flag = true;
            return match;
        }
        // W8 O01/O02 on the read side only; no active monitor = no-op.
        if (fi_mode == Mode::O01MonitorAddrBitflip ||
            fi_mode == Mode::O02MonitorStateCorrupt)
            return would_succeed;
        if (probability <= 0.0f) return would_succeed;
        if (max_faults != 0 && faults_injected_count >= max_faults) return would_succeed;
        if (!inWindow()) return would_succeed;
        if (!req) return would_succeed;
        if (!inRoi(xc)) return would_succeed;

        // Eligible = in the mode's direction (force_success needs a
        // would-fail STXR; force_fail needs a would-succeed one). Only
        // consume skip budget on eligible events, not on every STXR.
        const bool eligible =
            (fi_mode == Mode::StxrForceSuccess) ? !would_succeed
                                                : would_succeed;
        if (!eligible) return would_succeed;

        // [R6-O-ROI] Warm-up (seed-independent prefix) then the tier draw:
        // F0 = uniform over lsuSpanEvents (drawn in the ctor), legacy =
        // geometric first-fire skip.
        if (warmup_remaining > 0) {
            --warmup_remaining;
            return would_succeed;
        }
        if (events_to_skip > 0) {
            --events_to_skip;
            return would_succeed;
        }

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return would_succeed;

        bool result = would_succeed;
        if (fi_mode == Mode::StxrForceSuccess) {
            // §2.4: force a STXR that would FAIL to SUCCEED (the monitor's
            // 'open↔exclusive' state is corrupted -> isolation violation).
            if (!would_succeed) {
                result = true;
                // must also clear the lock flag so the mem system proceeds
                // (the caller checks the return value; setting extraData=1
                // signals success).
                req->setExtraData(1);
                faults_injected_count++;
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: isa_handleLockedWrite, mode=stxr_force_success"
                        << ", addr=0x" << std::hex << req->getPaddr() << std::dec
                        << ", would_succeed=false -> forced=true"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
            }
        } else {  // StxrForceFail
            if (would_succeed) {
                result = false;
                // [R6-O03-FIX 2026-11-03] A forced failure completes the
                // store unconditionally in the LSQ (`if (!success)` path,
                // src/cpu/o3/lsq_unit.cc:1116-1124) and never reaches the
                // memory system, so nothing sets VALID_EXTRA_DATA. The
                // retrying STXRW64::completeAcc asserts on
                // req->getExtraData() (src/mem/request.hh:912). The normal
                // failure path sets 0 at src/arch/arm/isa.cc:1942; mirror it.
                req->setExtraData(0);
                faults_injected_count++;
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: isa_handleLockedWrite, mode=stxr_force_fail"
                        << ", addr=0x" << std::hex << req->getPaddr() << std::dec
                        << ", would_succeed=true -> forced=false"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
                // [R6-O03-CHAIN 2026-11-03] Register the status-flip fault so
                // the sample carries a real L0..L3 chain instead of an empty
                // stream. The STXR comparison itself matched; the fabricated
                // failure blocks this store and the LL/SC retry loop absorbs
                // it — the containment witness is at L3 (the unit's own
                // status-consumption layer). HONEST BOUNDARY: the store is
                // not sent on this attempt (the model's documented
                // approximation; the retry performs the update).
                if (CHAOSPropagation *h6f = CHAOSPropagation::instance()) {
                    const uint64_t seq = req->hasInstSeqNum()
                        ? req->getReqInstSeqNum() : 0;
                    std::ostringstream h6f_pa;
                    h6f_pa << std::hex << req->getPaddr();
                    const uint64_t ptag = h6f->registerInjection(
                        "stxr_force_fail", seq, req->getPaddr(),
                        req->getPaddr(), false, 8, 0);
                    if (ptag) {
                        h6f->notePropEvt("exmon_rmw", {
                            {"fault_id", std::to_string(ptag)},
                            {"dyn_inst_seq", std::to_string(seq)},
                            {"request_id", std::to_string(seq)},
                            {"pa", h6f_pa.str()},
                            {"field", "reservation_compare"},
                            {"state_before", "reserved"},
                            {"state_after", "match_success"},
                        });
                        h6f->notePropEvt("exmon_stxr", {
                            {"fault_id", std::to_string(ptag)},
                            {"dyn_inst_seq", std::to_string(seq)},
                            {"request_id", std::to_string(seq)},
                            {"pa", h6f_pa.str()},
                            {"entry_index", "1"},
                            {"field", "stxr_status_flip"},
                            {"state_before", "success"},
                            {"state_after", "fail_forced"},
                            {"detection_layer", "L3"},
                            {"contained", "1"},
                            {"outcome", "stxr_status_forced_fail"},
                            {"corr", "addr_fallback"},
                            {"containment_layer", "L3"},
                            {"containment_reason",
                             "retry_loop_absorbs_forced_status_flip"},
                        });
                    }
                }
            }
        }
        return result;
    }

    std::optional<CHAOSExMon::MonitorVal>
    CHAOSExMon::maybeCorruptMonitor(const RequestPtr &req, ExecContext *xc)
    {
        // W8 O-series: only the monitor-side modes act here; the stxr
        // modes leave the read side alone.
        if (fi_mode != Mode::O01MonitorAddrBitflip &&
            fi_mode != Mode::O02MonitorStateCorrupt)
            return std::nullopt;
        if (!req) return std::nullopt;
        if (!inRoi(xc)) return std::nullopt;
        if (probability <= 0.0f) return std::nullopt;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return std::nullopt;
        if (!inWindow()) return std::nullopt;

        // Every LDXR that placed a monitor is eligible. [R6-O-ROI] Warm-up
        // prefix, then the tier draw (F0 uniform span / legacy geometric).
        if (warmup_remaining > 0) {
            --warmup_remaining;
            return std::nullopt;
        }
        if (events_to_skip > 0) {
            --events_to_skip;
            return std::nullopt;
        }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return std::nullopt;

        const Addr paddr = req->getPaddr();
        MonitorVal mv{paddr, true};
        const char *site = "";
        if (fi_mode == Mode::O01MonitorAddrBitflip) {
            // O01: one architecturally-visible monitor-address bit XORed.
            // Bits [6,47] only — lockedWriteHandler masks both sides with
            // cacheBlockMask (64B lines), so bits <6 are don't-care and are
            // excluded from sampling (injected == activated semantics).
            const unsigned bit = 6 + rng() % 42;
            mv.addr = paddr ^ (Addr(1) << bit);
            site = "o01_monitor_addr_bitflip";
        } else {
            // O02: 50% clear the flag (valid清零), 50% repoint the
            // reservation at the neighboring 64B block (伪造/version-旧值
            // proxy — gem5 monitor = flag+addr only, documented in .hh).
            if (rng() % 2) {
                mv.flag = false;
                site = "o02_monitor_state_clear";
            } else {
                mv.addr = paddr ^ Addr(0x40);
                site = "o02_monitor_state_fake";
            }
        }
        ++faults_injected_count;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: isa_handleLockedRead, mode=" << site
                << ", addr=0x" << std::hex << paddr << std::dec
                << " -> monitor addr=0x" << std::hex << mv.addr << std::dec
                << ", flag=" << (mv.flag ? 1 : 0)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }

        // [MDSPEC][H6] register the monitor-side fault with the tracer and
        // emit the exmon_monitor event (L1): the LDXR placed a corrupted
        // monitor. before/after = original vs corrupted monitor address,
        // state_* = monitor flag. The ptag is kept so the paired STXR's
        // consumption event attaches to the same chain (LL-SC pairing =
        // the shared key). nullptr tracer = no-op.
        if (CHAOSPropagation *h6 = CHAOSPropagation::instance()) {
            const uint64_t seq = req->hasInstSeqNum()
                ? req->getReqInstSeqNum() : 0;
            // [R6-O-ACT 2026-11-03] size=0: the monitor fault has no data
            // payload, and registering a live range here made later resp /
            // lq_complete / taint_reg / consumer / errant_commit nodes attach
            // to the LDXR's (correct) data — a FALSE data-taint that also
            // placed the errant_commit BEFORE the STXR consumption nodes.
            // registerInjection's size==0 marker never range-matches, so the
            // chain stays monitor-only (L0 → L1 → L2 → L3).
            const uint64_t ptag = h6->registerInjection(
                site, seq, paddr, mv.addr, true, 8, 0);
            if (ptag) {
                active_monitor_ptag = ptag;
                active_monitor_attempts = 0;   // new monitor → new retry count
                active_monitor_block = paddr & ~Addr(0x3f);
                active_monitor_addr = mv.addr;
                active_monitor_flag = mv.flag;
                active_monitor_seq = seq;
                std::ostringstream h6_before, h6_after;
                h6_before << std::hex << paddr;
                h6_after << std::hex << mv.addr;
                h6->notePropEvt("exmon_monitor", {
                    {"fault_id", std::to_string(ptag)},
                    {"dyn_inst_seq", std::to_string(seq)},
                    {"request_id", std::to_string(seq)},
                    {"va", h6_before.str()},
                    {"pa", h6_before.str()},
                    {"before", h6_before.str()},
                    {"after", h6_after.str()},
                    {"field", site},
                    {"state_before", "1"},
                    {"state_after", mv.flag ? "1" : "0"},
                });
            }
        }
        return mv;
    }

} // namespace gem5
