#include "arch/arm/CHAOSExMon/CHAOSExMon.hh"

#include "arch/arm/isa.hh"  // ArmISA::ISA (full def for setChaosExMon)
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
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("exmon_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSExMon: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
            // Sampling-bias fix (findings.md Phase 2.2/3.0): skip a
            // geometric(p=0.1) number of eligible events before the first
            // injection so maxFaults=1 lands on a seed-dependent event.
            std::geometric_distribution<uint64_t> skip_dist(0.1);
            events_to_skip = skip_dist(rng);
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
    CHAOSExMon::maybeCorrupt(const RequestPtr &req, bool would_succeed)
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
        if ((fi_mode == Mode::O01MonitorAddrBitflip ||
             fi_mode == Mode::O02MonitorStateCorrupt) &&
            active_monitor_ptag != 0 && req) {
            if (CHAOSPropagation *h6s = CHAOSPropagation::instance()) {
                const uint64_t seq = req->hasInstSeqNum()
                    ? req->getReqInstSeqNum() : 0;
                ++active_monitor_attempts;
                std::ostringstream h6s_pa;
                h6s_pa << std::hex << req->getPaddr();
                h6s->notePropEvt("exmon_rmw", {
                    {"fault_id", std::to_string(active_monitor_ptag)},
                    {"dyn_inst_seq", std::to_string(seq)},
                    {"request_id", std::to_string(seq)},
                    {"pa", h6s_pa.str()},
                    {"field", "reservation_compare"},
                    {"state_before", "reserved"},
                    {"state_after", would_succeed ? "match_success"
                                                  : "mismatch_fail"},
                });
                h6s->notePropEvt("exmon_stxr", {
                    {"fault_id", std::to_string(active_monitor_ptag)},
                    {"dyn_inst_seq", std::to_string(seq)},
                    {"request_id", std::to_string(seq)},
                    {"pa", h6s_pa.str()},
                    {"entry_index", std::to_string(active_monitor_attempts)},
                    {"field", "stxr_consume"},
                    {"state_before", "reserved"},
                    {"state_after", would_succeed ? "success" : "fail_retry"},
                });
            }
        }
        // W8 O01/O02 are monitor-side (handleLockedRead) faults — the STXR
        // verdict must pass through untouched on these modes.
        if (fi_mode == Mode::O01MonitorAddrBitflip ||
            fi_mode == Mode::O02MonitorStateCorrupt)
            return would_succeed;
        if (probability <= 0.0f) return would_succeed;
        if (max_faults != 0 && faults_injected_count >= max_faults) return would_succeed;
        if (!inWindow()) return would_succeed;
        if (!req) return would_succeed;

        // Eligible = in the mode's direction (force_success needs a
        // would-fail STXR; force_fail needs a would-succeed one). Only
        // consume skip budget on eligible events, not on every STXR.
        const bool eligible =
            (fi_mode == Mode::StxrForceSuccess) ? !would_succeed
                                                : would_succeed;
        if (!eligible) return would_succeed;

        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed) so the single
        // fault lands on a seed-dependent event.
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
                faults_injected_count++;
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Site: isa_handleLockedWrite, mode=stxr_force_fail"
                        << ", addr=0x" << std::hex << req->getPaddr() << std::dec
                        << ", would_succeed=true -> forced=false"
                        << ", faults_injected: " << faults_injected_count
                        << std::endl;
                }
            }
        }
        return result;
    }

    std::optional<CHAOSExMon::MonitorVal>
    CHAOSExMon::maybeCorruptMonitor(const RequestPtr &req)
    {
        // W8 O-series: only the monitor-side modes act here; the stxr
        // modes leave the read side alone.
        if (fi_mode != Mode::O01MonitorAddrBitflip &&
            fi_mode != Mode::O02MonitorStateCorrupt)
            return std::nullopt;
        if (!req) return std::nullopt;
        if (probability <= 0.0f) return std::nullopt;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return std::nullopt;
        if (!inWindow()) return std::nullopt;

        // Every LDXR that placed a monitor is eligible. Sampling-bias fix
        // (same defense as the stxr modes): skip a geometric(0.1) number of
        // eligible events so maxFaults=1 lands on a seed-dependent event.
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
            const uint64_t ptag = h6->registerInjection(
                site, seq, paddr, mv.addr, true, 8, 8);
            if (ptag) {
                active_monitor_ptag = ptag;
                active_monitor_attempts = 0;   // new monitor → new retry count
                // The monitor is compared against the STXR block address
                // (masks are cache-block sized), so register the whole 64B
                // line the reservation covers: the cache-side nodes
                // (cache_access/cache_return/RMW) on that line then carry
                // this chain instead of dropping out. The chain's own key
                // stays the ptag (fault_id).
                h6->registerPtagBlock(ptag, paddr & ~Addr(0x3f),
                                      (paddr & ~Addr(0x3f)) + 64);
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
