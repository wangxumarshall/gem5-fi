#ifndef __ARCH_ARM_CHAOS_ARM_TLB_HH__
#define __ARCH_ARM_CHAOS_ARM_TLB_HH__

#include <random>
#include <bitset>
#include <memory>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "cpu/o3/chaos_lsu_trigger.hh"   // [R4-5.9] walk_pairing trigger tier
#include "params/CHAOSArmTLB.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace ArmISA {
class TLB;
struct TlbEntry;
// [R4-5.9] T08 walk/fill pairing — the real class lives in
// gem5::ArmISA (arch/arm/table_walker.hh), so the forward declaration
// must sit in the SAME namespace (a gem5-level `class TableWalker;`
// would be a DIFFERENT type and made `TableWalker::…` ambiguous).
class TableWalker;
}

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
    // [MDSPEC][R4-4] req_seq/req_size carry the Request identity of the
    // translation in flight at this lookup (published by MMU::getTE via
    // the TLB's chaosLookupReq* side-channel; 0 = no Request identity —
    // table-walker/functional lookups). The fault chain registers
    // SEQ-PRIMARY on that request; address-only correlation survives only
    // as the labeled fallback (user ruling 2026-10-20).
    void maybeCorrupt(ArmISA::TlbEntry *entry, Addr va,
                      uint64_t req_seq, uint64_t req_size);
    // [MDSPEC][R4-4] propagation-trace registration (see .cc ruling).
    // old_pa/new_pa are the entry's pAddr(va) before/after the mutation
    // (gem5's own arithmetic — includes the 64-bit wrap that makes pfn
    // bits at/above the PA width architecturally inert); pa_span is the
    // entry's page size (entry->size + 1).
    void registerTrace(Addr va, Addr old_pfn, Addr new_pfn,
                       Addr old_pa, Addr new_pa, Addr pa_span,
                       const char *mode, uint64_t req_seq, uint64_t req_size);

    // [MDSPEC][R4-5.9] T08 walk/fill pairing (FS-only). Called from
    // TableWalker::walk() once per page-table walk, right AFTER the
    // WalkerState is constructed (walk_id + issue tick assigned) and just
    // BEFORE the walk is handed to a walk unit. This is the one point that
    // (a) has a real Request (dyn-inst seq / transaction identity — the
    // spec's "DTLB miss并启动walk" trigger) and (b) can withhold the walk.
    // Returns true => this walk is DROPPED (T08-a, "walk/fill丢失"): the
    // caller must NOT issue it, so the requesting translation never
    // completes (the spec's Timeout channel). The walk/fill node pair is
    // emitted at the fire point (registerTlbWalkPair, fill_lost=true).
    // Consults lsuTrigger (F0/F4/F6, event-normalized on the walk-issue
    // stream). Inert (returns false, emits nothing) when faultType is not
    // "walk_pairing" or no lsuTier is mounted — byte-equivalent to the
    // pre-R4-5.9 tree.
    bool maybeDropWalkFill(uint64_t walk_id, Addr va, uint64_t req_seq,
                           uint64_t walk_start_tick, unsigned level);

  private:
    // PfnToMappedPage = §2.10 F5 (Phase 4.4, FS-only): substitute the hit
    // entry's pfn with another MAPPED entry's pfn (legal domain -> silent
    // wrong-page access, method2's silent-SDC pathway).
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random,
                           PfnToMappedPage,
                           // [R4-5.9] T08: FS page-table walk/fill pairing
                           // (walk_pairing) — see maybeDropWalkFill.
                           WalkPairing };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    ArmISA::TLB *tlb;
    // [R4-5.9] T08 target walker (optional; nullptr unless the FS config
    // passes walker= to the CHAOSArmTLB object). Also the host of the
    // event-normalized walk_pairing trigger.
    ArmISA::TableWalker *walker = nullptr;
    std::unique_ptr<ChaOSLsuTrigger> lsuTrigger;
    float probability;
    FaultType fault_type_enum;
    uint64_t fault_mask;
    int num_bits_to_change;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    // Sampling-bias fix (the 9th member of the geometric-skip family —
    // the sister track fixed 8 SE injectors in Phase 3.0; this FS-only
    // injector was deferred to the FS pipeline round, which is now).
    // Without it, maxFaults=1 lands on the DETERMINISTIC first eligible
    // lookup after the window opens — the T01 anchor trial showed all 5
    // seeds hitting the same kernel VA (0xffffffc009483eb0), varying only
    // the bit. Drawn geometric(0.1) from rngSeed in the ctor; consumed
    // on eligible events (post probability-gate) before the first fault.
    uint64_t events_to_skip = 0;
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
