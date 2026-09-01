#ifndef __CPU_O3_CHAOS_ROB_HH__
#define __CPU_O3_CHAOS_ROB_HH__

#include <random>
#include <memory>
#include <string>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "cpu/reg_class.hh"  // PhysRegIdPtr (S6-4 spec_leak)
#include "params/CHAOSROB.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"  // Cycles, EventFunctionWrapper

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSROB — ROB fault injector (plan §5.3, S1-4).
//
// method1 ROB dimension: "投机流状态泄漏 + 异常位静默":
//   exc_suppress   : clear a faulting DynInst's fault -> DUE turns into SDC
//   entry_bitflip  : flip a bit of a ROB-entry DynInst's seqNum (re-ordering
//                    corruption)
//   spec_leak      : retain wrong-path μop's PRF write on squash (deferred —
//                    needs lsq_unit/squash hook plumbing)
//
// Self-driven attackEvent (ROB is not a SimObject), holds cpu pointer,
// reaches cpu->rob like CHAOSPhysReg reaches physRegFile.
class CHAOSROB : public SimObject
{
  public:
    CHAOSROB(const CHAOSROBParams &p);
    ~CHAOSROB();

    void startup() override;

    // S6-4 spec_leak: called from Rename::doSquash before returning a
    // squashed inst's dest physReg to the free list. Returns true to SKIP
    // the return (retain the wrong-path PRF write — method1's state-leak
    // signature). Honors probability/window/maxFaults; only active when
    // fi_mode == SpecLeak.
    bool maybeDelayFree(const PhysRegIdPtr &reg);

  private:
    enum class Mode { EntryBitFlip, ExcSuppress, SpecLeak };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    o3::CPU *cpu;
    float probability;
    Mode fi_mode;
    int distance_from_head;
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

    void writeLog(const std::string &type, ThreadID tid,
                  uint64_t seq, uint64_t old_seq, uint64_t new_seq,
                  bool had_fault, bool cleared_fault);

    struct CHAOSROBStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numEntryBitFlips;
        statistics::Scalar numExcSuppress;       // faults cleared
        statistics::Scalar numSpecLeak;          // (deferred, 0 for now)
        statistics::Scalar numLegalityRejects;    // head null / no faulting inst
        CHAOSROBStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSROBStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_ROB_HH__
