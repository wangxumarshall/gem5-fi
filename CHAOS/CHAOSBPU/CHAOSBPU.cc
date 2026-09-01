#include "cpu/o3/CHAOSBPU/CHAOSBPU.hh"
#include "params/CHAOSBPU.hh"
#include "cpu/o3/cpu.hh"
#include "arch/generic/pcstate.hh"
#include "base/trace.hh"
#include "debug/CHAOSBPU.hh"
#include <iostream>
#include <fstream>

namespace gem5
{
    CHAOSBPU::CHAOSBPU(const CHAOSBPUParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fi_mode(stringToMode(p.mode)),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          semantic_role(p.semanticRole),
          rng([this]() {
              std::random_device local_rd;
              return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
          }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (!cpu) throw std::runtime_error(
            "CHAOSBPU: cpu not O3CPU. O3-only (hooks BAC::predict).");
        if (probability > 0.0f) {
            log_stream = simout.create("bpu_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSBPU: Could not open log file");
            stats = std::make_unique<Stats>(this);
        }
    }

    CHAOSBPU::~CHAOSBPU() {}

    CHAOSBPU::Mode CHAOSBPU::stringToMode(const std::string &s) {
        if (s == "direction_flip") return Mode::DirectionFlip;
        return Mode::TargetSub;  // default + "target_sub"
    }

    bool
    CHAOSBPU::maybeSubstituteTarget(PCStateWithNext &pc, bool taken)
    {
        if (probability <= 0.0f) return taken;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return taken;
        if (last_clock != Cycles(0) && cur > last_clock) return taken;
        if (max_faults != 0 && faults_injected_count >= max_faults) return taken;
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return taken;

        if (fi_mode == Mode::TargetSub) {
            // F5 legal-domain substitute: predicted target -> fall-through.
            // Both are legal PCs; the wrong one forces mispredict -> squash.
            Addr fetch_pc = pc.pc();
            Addr old_target = pc.npc();
            pc.npc(fetch_pc + 4);  // AArch64 fall-through (fixed 4B inst)
            stats->numTargetSub++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << ", Site: bac_predict_target"
                    << ", Mode: target_sub"
                    << ", FetchPC: 0x" << std::hex << fetch_pc
                    << ", OldTarget: 0x" << old_target
                    << ", NewTarget: 0x" << (fetch_pc + 4) << std::dec
                    << std::endl;
            }
        } else {
            taken = !taken;  // direction_flip (F1)
            stats->numDirectionFlip++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << ", Site: bac_predict_direction"
                    << ", Mode: direction_flip"
                    << std::endl;
            }
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;
        return taken;
    }

    CHAOSBPU::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total BPU faults injected"),
          ADD_STAT(numTargetSub, statistics::units::Count::get(),
                   "target_sub faults (F5 fall-through substitute)"),
          ADD_STAT(numDirectionFlip, statistics::units::Count::get(),
                   "direction_flip faults (F1 taken inversion)")
    {}
} // namespace gem5
