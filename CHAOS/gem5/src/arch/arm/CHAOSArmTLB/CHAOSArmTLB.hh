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

  private:
    // PfnToMappedPage = §2.10 F5 (Phase 4.4, FS-only): substitute the hit
    // entry's pfn with another MAPPED entry's pfn (legal domain -> silent
    // wrong-page access, method2's silent-SDC pathway).
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random,
                           PfnToMappedPage };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    ArmISA::TLB *tlb;
    float probability;
    FaultType fault_type_enum;
    uint64_t fault_mask;
    int num_bits_to_change;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::string protection_model;  // §1.2 protection-aware layer

    std::mt19937 rng;
    std::random_device rd;
    std::discrete_distribution<int> random_fault_distribution;
    OutputStream *log_stream;

    // §1.2 protection outcome ladder.
    enum class ProtectionOutcome { Raw, Corrected, SilentEscape };
    static ProtectionOutcome stringToProtectionModel(const std::string &s);
    const char *protectionOutcomeToString(ProtectionOutcome o);
    // Post-injection protection (§1.2). Acts on `entry->pfn` (by ref) after the
    // bit mutation, BEFORE the entry is returned to the MMU. parity_interleaved
    // 1-bit -> undo (restore old_pfn = Corrected; re-entrancy-safe vs real-HW
    // entry-invalidate+re-walk, E3); >=2-bit -> SilentEscape. none -> Raw.
    ProtectionOutcome applyProtection(ArmISA::TlbEntry *entry, uint64_t mask,
                                      Addr old_pfn, FaultType ft);

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
