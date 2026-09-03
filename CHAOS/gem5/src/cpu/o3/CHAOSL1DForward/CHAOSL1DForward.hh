#ifndef __CPU_O3_CHAOS_L1D_FORWARD_HH__
#define __CPU_O3_CHAOS_L1D_FORWARD_HH__

#include <random>
#include <string>

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
    // XORs the response packet's data (post-L1D-read, post-ECC-check) —
    // the post-check escape path. Returns true if an injection happened.
    bool maybeCorrupt(PacketPtr pkt);

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

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_L1D_FORWARD_HH__
