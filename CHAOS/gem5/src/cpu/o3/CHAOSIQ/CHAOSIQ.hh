#ifndef __CPU_O3_CHAOS_IQ_HH__
#define __CPU_O3_CHAOS_IQ_HH__

#include <random>
#include <memory>
#include <string>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSIQ.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSIQ — issue-queue fault injector (plan §5.5, S8-1).
// Reaches the ROB-head DynInst via cpu->robAccess() (the public IQ list is
// not iterable). Operates on src-ready bits / src tags as the observable
// IQ-state proxy. Self-driven attackEvent (IQ not a SimObject).
class CHAOSIQ : public SimObject
{
  public:
    CHAOSIQ(const CHAOSIQParams &p);
    ~CHAOSIQ();

    void startup() override;

  private:
    enum class Mode { SrcReadyBitFlip, TagSub, WakePhase, WakeOmit };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    o3::CPU *cpu;
    float probability;
    Mode fi_mode;
    int target_src_idx;
    uint64_t fault_mask;
    int num_bits_to_change;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::string semantic_role;

    std::mt19937 rng;
    std::random_device rd;
    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    OutputStream *log_stream;

    EventFunctionWrapper attackEvent;
    void scheduleAttackEvent(Cycles delay);
    void attackCheck();
    void processFault(ThreadID tid);
    void writeLog(const std::string &type, ThreadID tid, int src_idx,
                  bool old_ready, bool new_ready, uint64_t mask);

    struct CHAOSIQStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numSrcReadyBitFlips;
        statistics::Scalar numTagSub;
        statistics::Scalar numLegalityRejects;
        CHAOSIQStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSIQStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_IQ_HH__
