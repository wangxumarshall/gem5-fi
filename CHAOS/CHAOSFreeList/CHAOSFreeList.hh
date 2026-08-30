#ifndef __CPU_O3_CHAOS_FREE_LIST_HH__
#define __CPU_O3_CHAOS_FREE_LIST_HH__

#include <random>
#include <memory>
#include <string>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSFreeList.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"  // Cycles, EventFunctionWrapper

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSFreeList — freelist fault injector (plan §5.2, S1-3).
//
// method1 companion: a LIVE physReg (still mapped in the RAT) is wrongly
// added to the free list -> next rename allocates it to another arch reg
// (double-occupancy) -> old owner's in-flight reads return the NEW owner's
// value (history residue). Distinct from CHAOSRenameMap (swaps mapping):
// CHAOSFreeList corrupts the ALLOCATION state.
//
// Self-driven attackEvent (freelist not a SimObject), holds cpu pointer,
// reaches physFreeList() like CHAOSPhysReg.
class CHAOSFreeList : public SimObject
{
  public:
    CHAOSFreeList(const CHAOSFreeListParams &p);
    ~CHAOSFreeList();

    void startup() override;

  private:
    enum class Mode { MarkFree, PopWrong };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    enum class RegClassSel { Integer, FloatingPoint, Vector };
    static RegClassSel stringToRegClassSel(const std::string &s);

    o3::CPU *cpu;
    float probability;
    Mode fi_mode;
    RegClassSel reg_target_class;
    int target_phys_idx;
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
    void writeLog(const std::string &type, ThreadID tid, int phys_idx,
                  int donor_arch, const std::string &detail);

    struct CHAOSFreeListStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numMarkFree;
        statistics::Scalar numPopWrong;
        statistics::Scalar numLegalityRejects;  // target was free (not live) — skip
        CHAOSFreeListStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSFreeListStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_FREE_LIST_HH__
