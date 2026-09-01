#ifndef __CPU_O3_CHAOS_L1D_FORWARD_HH__
#define __CPU_O3_CHAOS_L1D_FORWARD_HH__

#include <random>
#include <memory>
#include <string>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSL1DForward.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{
namespace o3 { class CPU; }

// CHAOSL1DForward — post-check escape (PCE) injector (plan §5.8, §3.1).
// Hooks DynInst::corruptResultRegVal on LOAD instructions — flips bits of
// the load result AFTER ECC has passed (the data path between cache return
// and PhysReg writeback). "Complete RAM protection pushes SDC to the
// post-check data path's inevitable exit."
class CHAOSL1DForward : public SimObject
{
  public:
    CHAOSL1DForward(const CHAOSL1DForwardParams &p);
    ~CHAOSL1DForward();
    void startup() override;
  private:
    o3::CPU *cpu;
    float probability;
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
    uint64_t genMask();
    void writeLog(ThreadID tid, uint64_t mask);
    struct Stats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numLoadResultCorrupted;
        statistics::Scalar numSkippedNonLoad;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
};
} // namespace gem5
#endif
