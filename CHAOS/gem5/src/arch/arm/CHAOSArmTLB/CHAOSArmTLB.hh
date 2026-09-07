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
    std::string target_field;   // pfn/ap/xn/attridx/ng/asid (§5.7B)
    uint64_t pfn_offset;        // F5 directed pfn substitute (0=legacy bitflip)
    // §5.7B pfn_to_mapped_page: "mapped_page" substitutes the hit entry's
    // pfn with the pfn of ANOTHER VALID entry in the same TLB (a live
    // mapped page — the most dangerous silent-SDC path: the substituted
    // translation always resolves to mapped memory, so no DUE guard fires).
    std::string pfn_select_mode;  // bit_flip (legacy) | mapped_page
    // §2.3 N1 TRM proxy: none (L1 — raw escape) | parity_interleaved
    // (L2 — 1-bit detected: entry invalidated + rewalk; same-parity >=2-bit
    // silent escape). Applied POST-injection on the pfn bit count.
    enum class ProtectionModel { None, ParityInterleaved };
    ProtectionModel protection_model;
    std::string log_name;
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

    // §5.7B pfn_to_mapped_page: collect the pfns of all OTHER valid
    // entries in the target TLB (excluding `self`). Returns false if no
    // candidate exists (single-entry TLB — the caller then declines the
    // injection, an honest Inactive).
    bool pickMappedPagePfn(const ArmISA::TlbEntry *self, Addr &out_pfn,
                           Addr &out_size);

    // §2.3: apply the parity_interleaved model post-injection (see .cc).
    // Returns true if the corrupted pfn survived (escape), false if the
    // entry was invalidated (parity detected, refetch).
    bool applyProtectionModel(ArmISA::TlbEntry *entry,
                              Addr old_pfn, Addr new_pfn);

    struct CHAOSArmTLBStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        // §2.3 protection outcomes (parity_interleaved model).
        statistics::Scalar numParityDetectedInvalidated;  // 1-bit: refetch
        statistics::Scalar numParitySilentEscape;         // >=2-bit: escape
        CHAOSArmTLBStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSArmTLBStats> stats;
};

} // namespace gem5
#endif // __ARCH_ARM_CHAOS_ARM_TLB_HH__
