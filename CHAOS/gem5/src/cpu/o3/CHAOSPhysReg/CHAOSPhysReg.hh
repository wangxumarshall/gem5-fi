#ifndef __CPU_O3_CHAOS_PHYS_REG_HH__
#define __CPU_O3_CHAOS_PHYS_REG_HH__

#include <random>
#include <bitset>
#include <map>

#include "params/CHAOSPhysReg.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"
#include "cpu/base.hh"
#include "base/output.hh"

// o3::CPU (C++ class behind ArmO3CPU) is needed to reach regFile/renameMap.
// We forward-declare it here (full definition pulled into the .cc via
// cpu/o3/cpu.hh) to avoid dragging cpu.hh into the auto-generated params
// wrapper. CHAOSPhysReg only supports O3CPU; dynamic_cast fails at construct
// time otherwise.
namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

class CHAOSPhysReg : public SimObject
{
  public:
    CHAOSPhysReg(const CHAOSPhysRegParams &p);
    ~CHAOSPhysReg();

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    enum class Mode { Phys, ArchFrontend, ArchCommit };

    struct PermanentFault {
        FaultType fault_type;
        int mask;
        bool update;
    };

    o3::CPU *cpu;      // dynamic_cast<o3::CPU*> in the .cc
    Mode fi_mode;
    unsigned free_list_size_at_inject = 0;  // diagnostic: numFreeRegs at inject
    uint64_t reads_before_overwrite = 0;   // reads of the INJECTED VALUE (stops at overwrite)
    bool trace_overwritten = false;        // has the injected value been overwritten?
    uint64_t overwritten_at_cycle = 0;     // cycle at which the injected value was overwritten
    bool overwrite_recorded = false;       // have we recorded overwritten_at_cycle?
    int traced_phys_idx = -1;              // phys idx being traced, or -1

    // target selection
    int target_phys_idx;     // phys fi_mode; -1 = random
    int target_arch_idx;     // arch_frontend / arch_commit modes

    // fault model
    float probability;
    int num_bits_to_change;
    FaultType fault_type_enum;
    std::bitset<32> fault_mask;
    float bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob;

    // timing
    Cycles first_clock, last_clock;

    // campaign control
    uint64_t max_faults;
    uint64_t faults_injected_count;
    uint64_t rng_seed;

    bool write_log;

    EventFunctionWrapper attackEvent, periodicCheck;
    EventFunctionWrapper readTraceEvent;  // polls read_count after inject

    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    std::discrete_distribution<int> random_fault_distribution;
    std::mt19937 rng;
    std::random_device rd;

    // permanent faults (keyed by phys reg flatIdx for phys fi_mode, or arch idx
    // for arch modes). For stuck-at via write-path mask, this is used by the
    // periodic re-apply fallback; the preferred stuck mechanism is the
    // write-path mask hook in PhysRegFile::setReg (TODO).
    std::map<std::pair<ThreadID, int>, PermanentFault> permanent_faults;

    OutputStream *log_stream;

    // helpers
    int generateRandomMask(std::mt19937 &gen, int bits_to_change, int len);
    void processFault(ThreadID tid);
    void scheduleAttackEvent(Cycles delay);
    void unscheduleAttackEvent();
    void scheduleCheckPermanentFault(Cycles delay);
    void checkPermanent();
    void attackCheck();
    void readTraceCheck();          // poll read_count, reschedule until halt
    const char* faultTypeToString(FaultType f);
    static FaultType stringToFaultType(const std::string &s);
    static Mode stringToMode(const std::string &s);

    struct CHAOSPhysRegStats : public statistics::Group
    {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        statistics::Scalar numPermanentFaults;
        CHAOSPhysRegStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSPhysRegStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_PHYS_REG_HH__
