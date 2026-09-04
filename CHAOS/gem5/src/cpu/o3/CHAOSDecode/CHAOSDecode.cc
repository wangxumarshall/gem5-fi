#include "cpu/o3/CHAOSDecode/CHAOSDecode.hh"

#include "cpu/o3/cpu.hh"          // o3::CPU
#include "cpu/o3/dyn_inst.hh"     // DynInst
#include "debug/CHAOSDecode.hh"
#include "params/CHAOSDecode.hh"

namespace gem5
{

    CHAOSDecode::CHAOSDecode(const CHAOSDecodeParams &p)
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
            log_stream = simout.create("decode_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSDecode: Could not open log file");
            rng.seed(rng_seed != 0 ? rng_seed : rd());
        // Sampling-bias fix (findings.md Phase 2.2/3.0): skip a
        // geometric(p=0.1) number of eligible events before the first
        // injection so maxFaults=1 lands on a seed-dependent event.
        std::geometric_distribution<uint64_t> skip_dist(0.1);
        events_to_skip = skip_dist(rng);
        }
    }

    CHAOSDecode::~CHAOSDecode() {}

    bool
    CHAOSDecode::inWindow() {
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
    CHAOSDecode::maybeCorrupt(int dest_idx, RegId &flat_dest_regid,
                              const o3::DynInst *inst)
    {
        if (!cpu || probability <= 0.0f) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!inWindow()) return false;
        // only integer class dest regs (aarch64 X0-X30 = index 0-30)
        if (flat_dest_regid.classValue() != IntRegClass) return false;

        // Sampling-bias fix (findings.md Phase 3.0): skip the first N
        // eligible events (N ~ geometric(0.1) from the seed) so the
        // single fault lands on a seed-dependent event.
        if (events_to_skip > 0) {
            --events_to_skip;
            return false;
        }


        std::uniform_real_distribution<float> pd(0.0f, 1.0f);
        if (pd(rng) > probability) return false;

        // §2.14 dest_reg_sub F5: replace the dest arch reg index with another
        // legal 0-30 integer reg (per-inst, safe — _flatDestIdx is per-DynInst,
        // not the shared staticInst). The commit path will write the result
        // to the WRONG arch reg (commit.cc:1264 reads flattenedDestIdx).
        RegIndex old_idx = flat_dest_regid.index();
        RegIndex new_idx;
        do { new_idx = rng() % 31; } while (new_idx == old_idx);  // 0..30, != old
        flat_dest_regid.setIndex(new_idx);  // mutate the by-ref reg id

        faults_injected_count++;
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: rename_flattenDest, mode=dest_reg_sub"
                << ", dest_idx=" << dest_idx
                << ", sn=" << inst->seqNum
                << ", old_dest_reg=" << old_idx
                << ", new_dest_reg=" << new_idx
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    void
    CHAOSDecode::startup() {
        SimObject::startup();
        auto *o3cpu = dynamic_cast<o3::CPU *>(cpu);
        if (!o3cpu) {
            warn("CHAOSDecode: cpu is not an O3CPU; injector disabled.\n");
            return;
        }
        o3cpu->setChaosDecode(this);
    }

} // namespace gem5
