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
        Tick now = curTick();
        Tick f = first_clock * 1000;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * 1000) return false;
        return true;
    }

    bool
    CHAOSExMon::maybeCorrupt(const RequestPtr &req, bool would_succeed)
    {
        if (probability <= 0.0f) return would_succeed;
        if (max_faults != 0 && faults_injected_count >= max_faults) return would_succeed;
        if (!inWindow()) return would_succeed;
        if (!req) return would_succeed;

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
