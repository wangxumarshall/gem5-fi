#ifndef __ARCH_ARM_CHAOS_ARM_TLB_HH__
#define __ARCH_ARM_CHAOS_ARM_TLB_HH__

#include <random>
#include <bitset>
#include <memory>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSArmTLB.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace ArmISA { class TLB; struct TlbEntry; }

// CHAOSArmTLB — ARM TLB-entry fault injector (Phase 3 §六.4 item 3).
//
// Hooks TLB::lookup (arch/arm/tlb.cc): on a TLB HIT, with probability
// `probability` per lookup (capped by maxFaults, within [firstClock,
// lastClock]), corrupts the hit entry's `pfn` (physical frame number) by
// a bit-flip mask. The next translation that reuses this entry resolves
// to a WRONG physical address -> potential SDC (wrong page read/written)
// or Crash (wrong page unmapped -> a fault). Models a defective TLB cell
// or translation-structure fault — the address-translation path, which is
// invisible to register-only or cache-only injectors. FS mode only.
class CHAOSArmTLB : public SimObject
{
  public:
    CHAOSArmTLB(const CHAOSArmTLBParams &p);
    ~CHAOSArmTLB();

    // Called from TLB::lookup AFTER a hit is found (retval != nullptr),
    // BEFORE the entry is returned to the MMU. If the RNG fires (and under
    // the clock window + maxFaults cap), corrupts retval->pfn by the mask
    // (bit_flip / stuck_at_zero / stuck_at_one). Hot-path: when
    // probability==0 or outside the window, returns immediately.
    void maybeCorrupt(ArmISA::TlbEntry *entry, Addr va);

    // D1 fix: the TLB is not a ClockedObject, so firstClock/lastClock are
    // interpreted as sim TICKS (curTick domain, NOT CPU cycles — avoids the
    // 1GHz assumption of D4). startup() snapshots them into first_tick/
    // last_tick once the global tick domain is fixed.
    void startup() override;

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    ArmISA::TLB *tlb;
    float probability;
    FaultType fault_type_enum;
    uint64_t fault_mask;
    int num_bits_to_change;
    Cycles first_clock, last_clock;
    Tick first_tick = 0, last_tick = 0;  // D1: advisory tick window (curTick)
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;

    std::mt19937 rng;
    std::random_device rd;
    std::discrete_distribution<int> random_fault_distribution;
    OutputStream *log_stream;

    uint64_t generateRandomMask(int bits_to_change);

    struct CHAOSArmTLBStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        CHAOSArmTLBStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSArmTLBStats> stats;
};

} // namespace gem5
#endif // __ARCH_ARM_CHAOS_ARM_TLB_HH__
