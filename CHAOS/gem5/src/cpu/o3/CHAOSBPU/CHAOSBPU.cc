#include "cpu/o3/CHAOSBPU/CHAOSBPU.hh"
#include "cpu/pred/bpred_unit.hh"  // v1.2 Phase 16: RAS registry

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "arch/generic/pcstate.hh"
#include "debug/CHAOSBPU.hh"
#include "params/CHAOSBPU.hh"

namespace gem5
{

    CHAOSBPU::CHAOSBPU(const CHAOSBPUParams &p)
        : SimObject(p),
          cpu(p.cpu),
          fi_mode(stringToMode(p.mode)),
          probability(p.probability),
          first_clock(p.firstClock),
          last_clock(p.lastClock),
          fault_mask(p.faultMask),
          max_faults(p.maxFaults),
          rng_seed(p.rngSeed),
          write_log(p.writeLog)
    {
    // v1.2 Phase 16: register the RAS hook (BPredUnit's return-predict
    // path consults it). Single global — one CHAOSBPU per run.
    if (fi_mode == Mode::RasFlip) {
        branch_prediction::BPredUnit::chaosRasHook = this;
    }

        if (probability > 0.0f) {
            log_stream = simout.create("bpu_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSBPU: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        // Sampling-bias fix (findings.md Phase 2.2/3.0): skip a
        // geometric(p=0.1) number of eligible events before the first
        // injection so maxFaults=1 lands on a seed-dependent event.
        std::geometric_distribution<uint64_t> skip_dist(0.1);
        events_to_skip = skip_dist(rng);
        }
    }

    CHAOSBPU::~CHAOSBPU() {}

    CHAOSBPU::Mode
    CHAOSBPU::stringToMode(const std::string &s) {
        if (s == "target_flip") return Mode::TargetFlip;
        if (s == "ras_flip") return Mode::RasFlip;  // v1.2 Phase 16
        return Mode::DirFlip;  // default / unknown
    }

    bool
    CHAOSBPU::inWindow() {
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
    CHAOSBPU::maybeCorrupt(ThreadID tid, bool &taken, PCStateBase &pc)
    {
        // v1.2 Phase 16: ras_flip mode lives on the BPredUnit return path
        // (maybeCorruptRas); the BAC post-predict hook must NOT fire it.
        if (fi_mode == Mode::RasFlip) return false;
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        if (fi_mode == Mode::DirFlip) {
        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed) so the
        // single fault lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }


            // §2.13 F5 direction: reverse taken/not-taken.
            taken = !taken;
        } else if (fi_mode == Mode::TargetFlip) {
            // §2.13 F5 target: flip a bit of the predicted PC target.
            Addr addr = pc.instAddr();
            uint64_t mask = fault_mask ? fault_mask : (1ULL << (rng() % 16));
            pc.set(addr ^ mask);
        }
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: bac_predict, tid=" << (int)tid
                << ", mode=" << (fi_mode == Mode::DirFlip ? "dir_flip" : "target_flip")
                << ", taken=" << taken
                << ", pc=0x" << std::hex << pc.instAddr() << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSBPU::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSBPU: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->o3BAC().setChaosBPU(this);
    }

    // v1.2 Phase 16 (item 1): RAS F5 — flip a bit of the predicted return
    // address. Gated on window/faults/probability like the other modes.
    void
    CHAOSBPU::maybeCorruptRas(ThreadID tid, PCStateBase &target)
    {
        if (fi_mode != Mode::RasFlip) return;
        if (!cpu || probability <= 0.0f) return;
        if (max_faults != 0 && faults_injected_count >= max_faults) return;
        if (!inWindow()) return;

        if (events_to_skip > 0) { --events_to_skip; return; }

        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return;

        // flip one bit of the return address (faultMask directs, else random)
        RegVal mask = fault_mask ? fault_mask : (1ULL << (rng() % 48));
        Addr ra = target.instAddr();
        target.set(ra ^ (Addr)mask);
        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: bpred_ras_return, mode=ras_flip, tid=" << (int)tid
                << ", old_ra=0x" << std::hex << ra
                << ", new_ra=0x" << (Addr)(ra ^ mask) << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
    }

} // namespace gem5
