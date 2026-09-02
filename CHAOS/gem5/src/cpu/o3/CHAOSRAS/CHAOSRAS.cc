#include "cpu/o3/CHAOSRAS/CHAOSRAS.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst, getFault
#include "debug/CHAOSRAS.hh"
#include "params/CHAOSRAS.hh"

namespace gem5
{

    CHAOSRAS::CHAOSRAS(const CHAOSRASParams &p)
        : SimObject(p),
          cpu(p.cpu),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
        if (probability > 0.0f) {
            log_stream = simout.create("ras_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSRAS: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        }
    }

    CHAOSRAS::~CHAOSRAS() {}

    bool
    CHAOSRAS::inWindow() {
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
    CHAOSRAS::maybeCorrupt(ThreadID tid, o3::DynInst *head_inst)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        if (!head_inst) return false;

        // Only inject if the head has a pending fault (exc_suppress = clear it).
        Fault &fref = head_inst->getFault();
        if (fref == NoFault) return false;  // no fault to suppress

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.18 exc_suppress: clear the fault -> the DUE/SError is silently
        // swallowed at commit (no trap, no RAS record). Quantifies the
        // 'DUE-to-SDC conversion at commit' (§2.18's exc_suppress mode).
        Fault old = fref;
        fref = NoFault;
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: commit_commitHead, mode=exc_suppress, tid=" << (int)tid
                << ", head_sn=" << head_inst->seqNum
                << ", cleared_fault=" << (old ? "yes" : "none")
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSRAS::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSRAS: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->o3Commit().setChaosRAS(this);
    }

} // namespace gem5
