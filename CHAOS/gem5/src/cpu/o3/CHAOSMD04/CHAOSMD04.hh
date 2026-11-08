#ifndef __CPU_O3_CHAOS_MD04_HH__
#define __CPU_O3_CHAOS_MD04_HH__

#include <random>
#include <string>

#include "params/CHAOSMD04.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

namespace gem5 { namespace o3 { class CPU; class DynInst; } }

namespace gem5
{

// MD04 — memory-dependency violation miss (F6). Hooks
// LSQUnit::checkViolations at the store->younger-load alias check: one real
// same-address 8-byte alias is reported as no violation, so the younger load
// keeps its stale data and may commit it.
class CHAOSMD04 : public SimObject
{
  public:
    CHAOSMD04(const CHAOSMD04Params &p);
    ~CHAOSMD04();
    void startup() override;  // self-attach to CPU.chaosMD04

    // Returns true iff the caller must suppress the violation report for this
    // store->load pair. `load_complete` is the response state at this point.
    bool maybeSkipViolation(o3::DynInst *ld_inst, o3::DynInst *store_inst,
                            bool load_complete);
    uint64_t lastEligibleOrdinal() const { return last_eligible_ordinal; }

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t rng_seed;
    uint64_t event_ordinal;
    bool count_only;
    bool write_log;
    uint64_t eligible_count = 0;
    uint64_t last_eligible_ordinal = 0;
    uint64_t faults_injected_count = 0;
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;
};

} // namespace gem5

#endif
