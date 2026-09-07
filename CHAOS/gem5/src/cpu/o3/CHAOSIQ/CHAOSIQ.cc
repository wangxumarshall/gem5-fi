#include "cpu/o3/CHAOSIQ/CHAOSIQ.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/inst_queue.hh"   // InstructionQueue
#include "sim/core.hh"
#include "cpu/o3/dyn_inst.hh"     // DynInst
#include "debug/CHAOSIQ.hh"
#include "sim/sim_exit.hh"
#include "params/CHAOSIQ.hh"

namespace gem5
{

    CHAOSIQ::CHAOSIQ(const CHAOSIQParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          phase_offset(p.phaseOffset),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("iq_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSIQ: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
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
        }
    }

    CHAOSIQ::~CHAOSIQ()
    {
        // v1.1 Phase 8.2 countOnlyMode: the driver's dry-run learns
        // N_eligible from this line (campaign.py parses the log).
        if (count_only && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT=" << eligible_count
                << std::endl;
        }
    }

    CHAOSIQ::Mode
    CHAOSIQ::stringToMode(const std::string &s) {
        if (s == "src_ready_bitflip") return Mode::SrcReadyBitflip;
        if (s == "wake_phase") return Mode::WakePhase;
        return Mode::WakeOmit;  // default / unknown
    }

    bool
    CHAOSIQ::inWindow() {
        // Frequency-correct: use the CPU's actual clock period for the
        // cycles->ticks conversion (C0 2GHz=500t/cyc, C2-KP 2.6GHz~385t/cyc).
        // The old *1000 assumed 1GHz and never opened the window on C2.
        if (!cpu) return false;
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) return false;
        Tick now = curTick();
        Tick period = o3cpu->clockPeriod();
        Tick f = first_clock * period;
        if (now < f) return false;
        if (last_clock != 0 && now > last_clock * period) return false;
        return true;
    }

    bool
    CHAOSIQ::shouldOmitWake(ThreadID tid, const o3::DynInstPtr &completed_inst)
    {
        if (fi_mode != Mode::WakeOmit) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible wakeup events (N ~ geometric(0.1) from the seed).
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.5 wake_omit (F6): drop this wakeup broadcast. Dependents of the
        // completed inst stay not-ready (one missed wake) — models method3
        // timing-race phase shift / dropped-wake fault.
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=wake_omit, tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", phase_offset=" << phase_offset
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;  // caller skips the wakeup broadcast
    }

    bool
    CHAOSIQ::shouldWrongSourceWake(ThreadID tid,
                                   const o3::DynInstPtr &completed_inst)
    {
        // §2.5 F5 src_ready_bitflip: gate ONLY. The dependency-graph surgery
        // (pop a not-ready dependent from a different chain, markSrcRegReady,
        // addIfReady) lives in InstructionQueue::wakeDependents — it owns
        // dependGraph/addIfReady/scoreboard and we don't want to expose them.
        if (fi_mode != Mode::SrcReadyBitflip) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!completed_inst) return false;

        // sampling-bias fix: skip on eligible completed-inst events
        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=src_ready_bitflip"
                << ", tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    bool
    CHAOSIQ::shouldDelayWake(ThreadID tid, const o3::DynInstPtr &completed_inst)
    {
        // §2.5 F6 wake_phase: gate. The caller (InstructionQueue) skips this
        // broadcast now and re-issues it after |phase_offset| cycles via its
        // own scheduled event. phase_offset <= 0 is a config error for this
        // mode (advance = wake in the past = no-op; documented E3 limit).
        if (fi_mode != Mode::WakePhase) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (phase_offset <= 0) return false;  // delay only; advance not modeled
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!completed_inst) return false;

        if (count_only) { ++eligible_count; return false; }
        if (events_to_skip > 0) { --events_to_skip; return false; }
        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: iq_wakeDependents, mode=wake_phase"
                << ", tid=" << (int)tid
                << ", completed_sn=" << completed_inst->seqNum
                << ", phase_offset=+" << phase_offset
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSIQ::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSIQ: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        // SELF-ATTACH: IEW.instQueue.chaosIQ = this.
        o3cpu->o3IEW().instQueue.setChaosIQ(this);
        // v1.1 Phase 8.2: print CHAOS_ELIGIBLE_COUNT at sim exit (the
        // destructor may not run before gem5's exit path tears everything
        // down; the exit callback always fires).
        if (count_only) {
            registerExitCallback([this]() {
                if (log_stream && log_stream->stream())
                    *(log_stream->stream()) << "CHAOS_ELIGIBLE_COUNT="
                        << eligible_count << std::endl;
            });
        }
    }

} // namespace gem5
