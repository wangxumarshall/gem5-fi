#ifndef __CPU_O3_CHAOS_RAS_HH__
#define __CPU_O3_CHAOS_RAS_HH__

#include <random>
#include <memory>
#include <string>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "cpu/o3/dyn_inst_ptr.hh"  // DynInstPtr
#include "params/CHAOSRAS.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSRAS — RAS-mechanism-escape injector (plan §5.11/S5-2, P1).
//
// Models the escape mechanism where a faulting instruction's exception is
// silently committed: the ERR* record that should log the error to the RAS
// subsystem is SUPPRESSED — a hardware-reportable DUE becomes an
// unreported SDC (the meta-analysis arm of §8.1 escape decomposition).
//
// Distinct from CHAOSROB::exc_suppress (ROB-entry fault-bit model):
// CHAOSRAS drives from the commit-path perspective and logs every
// suppression as a "RAS record miss" — the observable used by the escape
// analysis is that the SDC event leaves NO RAS record behind.
//
// O3-only: dynamic_cast to O3CPU to reach cpu->robAccess(). Self-driven
// attackEvent (same pattern as CHAOSROB/CHAOSPhysReg).
class CHAOSRAS : public SimObject
{
  public:
    CHAOSRAS(const CHAOSRASParams &p);
    ~CHAOSRAS();

    void startup() override;

  private:
    o3::CPU *cpu;
    float probability;
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

    struct CHAOSRASStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;      // suppressions applied
        statistics::Scalar numRasRecordMisses;     // DUE turned unreported
        statistics::Scalar numSkippedNoFault;      // head not faulting
        CHAOSRASStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSRASStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_RAS_HH__
