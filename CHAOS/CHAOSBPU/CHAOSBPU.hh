#ifndef __CPU_O3_CHAOS_BPU_HH__
#define __CPU_O3_CHAOS_BPU_HH__

#include <random>
#include <memory>
#include <string>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSBPU.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{
namespace o3 { class CPU; }
namespace GenericISA { class PCStateWithNext; }
using GenericISA::PCStateWithNext;

// CHAOSBPU — branch-predictor fault injector (plan §5.9).
// BAC::predict calls maybeSubstituteTarget() after bpu->predict() —
// target_sub replaces the predicted target with fall-through (F5 legal-
// domain substitute), direction_flip inverts taken. Wrong speculative
// stream should squash (P(arch==golden after squash) ~= 1): BPU is a
// negative-control surface (§2.2 P3).
class CHAOSBPU : public SimObject
{
  public:
    CHAOSBPU(const CHAOSBPUParams &p);
    ~CHAOSBPU();

    // Called from BAC::predict AFTER bpu->predict(). `pc` is the
    // prediction PC state (PCStateWithNext — its npc() is the predicted
    // target); `taken` is bpu->predict's return. May rewrite pc.npc()
    // (target_sub) or return inverted taken (direction_flip). Returns
    // the (possibly flipped) taken value.
    bool maybeSubstituteTarget(PCStateWithNext &pc, bool taken);

  private:
    enum class Mode { TargetSub, DirectionFlip };
    static Mode stringToMode(const std::string &s);

    o3::CPU *cpu;
    float probability;
    Mode fi_mode;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::string semantic_role;
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream;

    struct Stats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numTargetSub;
        statistics::Scalar numDirectionFlip;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
};
} // namespace gem5
#endif
