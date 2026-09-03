#ifndef __CPU_O3_CHAOS_IQ_HH__
#define __CPU_O3_CHAOS_IQ_HH__

#include <random>
#include <string>

#include "params/CHAOSIQ.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class InstructionQueue; } }

namespace gem5
{

class CHAOSIQ : public SimObject
{
  public:
    CHAOSIQ(const CHAOSIQParams &p);
    ~CHAOSIQ();

    void startup() override;  // self-attach to InstructionQueue.chaosIQ

    // Called from InstructionQueue::wakeDependents at the START. If
    // wake_omit and the RNG fires, returns true (the caller SKIPS the
    // wakeup broadcast — one dropped wake). Otherwise false (normal wake).
    bool shouldOmitWake(ThreadID tid, const o3::DynInstPtr &completed_inst);

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    int phase_offset;
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

#endif // __CPU_O3_CHAOS_IQ_HH__
