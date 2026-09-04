#ifndef __CPU_O3_CHAOS_BPU_HH__
#define __CPU_O3_CHAOS_BPU_HH__

#include <random>
#include <string>

#include "params/CHAOSBPU.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

class CHAOSBPU : public SimObject
{
  public:
    CHAOSBPU(const CHAOSBPUParams &p);
    ~CHAOSBPU();

    void startup() override;  // self-attach to BAC.chaosBPU

    // Called from BAC::predict AFTER bpu->predict(). dir_flip: reverse
    // `taken` (F5 direction). target_flip: flip a bit of the predicted PC
    // target (F5 target). Returns true if an injection happened.
    bool maybeCorrupt(ThreadID tid, bool &taken, PCStateBase &pc);

  private:
    enum class Mode { DirFlip, TargetFlip };
    static Mode stringToMode(const std::string &s);

    BaseCPU *cpu;
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2/3.0, same as CHAOSL1DForward
    // 7387649): skip a geometric(p=0.1) number of eligible events before
    // the first injection, so maxFaults=1 lands on a seed-dependent event
    // instead of always the first eligible one (same dynamic instruction
    // every rep on a deterministic stream).
    uint64_t events_to_skip = 0;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_BPU_HH__
