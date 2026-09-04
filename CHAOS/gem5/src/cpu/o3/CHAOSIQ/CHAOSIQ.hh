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

    // §2.5 F5 src_ready_bitflip (Phase 4.3, method3 wrong-source wakeup):
    // GATE only — the dependency-graph surgery (pop a not-ready dependent
    // from a different reg's chain, markSrcRegReady, addIfReady) lives in
    // InstructionQueue::wakeDependents, which owns dependGraph/addIfReady/
    // scoreboard (no internals exposed). Returns true = inject this event.
    bool shouldWrongSourceWake(ThreadID tid,
                               const o3::DynInstPtr &completed_inst);

    // §2.5 F6 wake_phase (Phase 4.3, method3 phase collapse): GATE only —
    // the caller skips this broadcast now and re-issues it after
    // |phase_offset| cycles via its own scheduled event. Delay only
    // (advance = wake in the past = no-op; documented E3 proxy limit).
    bool shouldDelayWake(ThreadID tid, const o3::DynInstPtr &completed_inst);

    // F6: the configured delay in cycles (InstructionQueue reads it when
    // scheduling the DelayedWakeEvent).
    int phaseOffset() const { return phase_offset; }

  private:
    enum class Mode { WakeOmit, SrcReadyBitflip, WakePhase };
    static Mode stringToMode(const std::string &s);
    Mode fi_mode;
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
