#include "cpu/o3/CHAOSIQ/CHAOSIQ.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/inst_queue.hh"   // InstructionQueue
#include "cpu/o3/dyn_inst.hh"     // DynInst
#include "debug/CHAOSIQ.hh"
#include "params/CHAOSIQ.hh"

namespace gem5
{

    CHAOSIQ::CHAOSIQ(const CHAOSIQParams &p)
        : SimObject(p),
          cpu(p.cpu),
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
        }
    }

    CHAOSIQ::~CHAOSIQ() {}

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
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
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

    // src_ready_bitflip / tag_sub (F5): needs dependency-graph traversal
    // (find a not-ready dependent, mark its source ready / swap src tag).
    // DEFERRED — §2.5 patch 2 (complex; wake_omit is the F6 subset here).

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
    }

} // namespace gem5
