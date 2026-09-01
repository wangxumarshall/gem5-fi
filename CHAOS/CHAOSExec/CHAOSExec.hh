#ifndef __CPU_O3_CHAOS_EXEC_HH__
#define __CPU_O3_CHAOS_EXEC_HH__

#include <random>
#include <memory>
#include <string>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSExec.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{
namespace o3 { class CPU; }

// CHAOSExec — integer ALU writeback-path injector (plan §5.10, S8-3).
// Negative control: P_SDC(Int) << P_SDC(FSU/forward). Reaches the ROB-head
// DynInst via cpu->robAccess() (same as CHAOSROB/CHAOSIQ), filters isInteger,
// and XORs a mask into the front instResult (DynInst::corruptResultRegVal)
// before PhysReg writeback.
class CHAOSExec : public SimObject
{
  public:
    CHAOSExec(const CHAOSExecParams &p);
    ~CHAOSExec();
    void startup() override;
  private:
    enum class BitSeg { All, Low, Mid, High };
    static BitSeg stringToBitSeg(const std::string &s);

    o3::CPU *cpu;
    float probability;
    uint64_t fault_mask;
    int num_bits_to_change;
    BitSeg bit_seg;
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
    uint64_t genMask();
    void writeLog(ThreadID tid, uint64_t mask, int bit_seg_lo, int bit_seg_hi);
    struct Stats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numIntResultCorrupted;
        statistics::Scalar numSkippedNonInt;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
};
} // namespace gem5
#endif
