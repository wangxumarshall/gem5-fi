#include "arch/arm/CHAOSExMon/CHAOSExMon.hh"

#include "arch/arm/isa.hh"  // ArmISA::ISA (full def for setChaosExMon)
#include "mem/request.hh"
#include "debug/CHAOSExMon.hh"
#include "params/CHAOSExMon.hh"

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

} // namespace gem5
