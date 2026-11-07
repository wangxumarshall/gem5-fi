#ifndef __CPU_O3_CHAOS_L1D_FORWARD_HH__
#define __CPU_O3_CHAOS_L1D_FORWARD_HH__

#include <random>
#include <string>
#include <vector>

#include "params/CHAOSL1DForward.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "mem/packet.hh"

namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

class CHAOSL1DForward : public SimObject
{
  public:
    CHAOSL1DForward(const CHAOSL1DForwardParams &p);
    ~CHAOSL1DForward();

    void startup() override;  // self-attach to CPU.chaosL1DFwd

    // Called from LSQUnit::completeDataAccess BEFORE writeback(inst, pkt).
    // Corrupts byte lane 0 of the response payload (post-L1D-read,
    // post-ECC-check) — the post-check escape path. `is_load` is true only
    // for a data load (SC/atomic/I-fetch are rejected). When `before_out`
    // is non-null and a fault is injected, it receives a copy of the
    // pre-fault payload taken BEFORE the XOR. Returns true iff injected.
    bool maybeCorrupt(PacketPtr pkt, bool is_load,
                      std::vector<uint8_t> *before_out = nullptr,
                      uint64_t *mask_out = nullptr);
    uint64_t lastEligibleOrdinal() const { return last_eligible_ordinal; }

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2): number of eligible load
    // events to skip before the first injection — geometric(p=0.1) sampled
    // from the seed, so maxFaults=1 lands on a seed-dependent load instead
    // of always the first eligible one (which is the same squashed
    // wrong-path load every rep on a deterministic stream).
    uint64_t events_to_skip = 0;
    // v3.2.5 LP01: the driver-supplied skip at startup, used to report the
    // 1-based eligible-event ordinal that was actually injected.
    uint64_t events_to_skip_initial = 0;
    uint64_t last_eligible_ordinal = 0;
    // v1.1 Phase 8.2 uniform sampling (chaos_event_sample.hh): FIXED skip
    // from the driver overrides the legacy geometric(0.1) draw.
    bool count_only = false;         // consume + count, never corrupt
    uint64_t eligible_count = 0;     // CHAOS_ELIGIBLE_COUNT=<n> at teardown

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_L1D_FORWARD_HH__
