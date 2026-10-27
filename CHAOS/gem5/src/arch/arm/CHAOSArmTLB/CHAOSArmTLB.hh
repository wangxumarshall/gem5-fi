#ifndef __ARCH_ARM_CHAOS_ARM_TLB_HH__
#define __ARCH_ARM_CHAOS_ARM_TLB_HH__

#include <random>
#include <bitset>
#include <memory>
#include <string>
#include <utility>   // [R6-F6APP] std::pair in collectPfnCandidates
#include <vector>    // [R6-F6APP] the read-only candidate scan output

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
                       const char *mode, uint64_t req_seq, uint64_t req_size,
                       int entry_way, int candidate_way, uint64_t walk_id,
                       const std::string &entry_before,
                       const std::string &entry_after);

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

    // [MDSPEC][R4-10-T07] CAM-compare / way-select hook (called from
    // TLB::lookup for BOTH outcomes). Returns the entry the MMU should use:
    //   * false_hit  — on a MISS (entry == nullptr) fabricate a hit by
    //     returning another VALID entry from the same TLB (a wrong
    //     translation the CAM would never have produced);
    //   * double_hit — on a HIT, record that a second entry also matches
    //     this VA/ASID (match-vector popcount 2) — no pointer change;
    //   * wrong_way  — on a HIT, return a DIFFERENT valid way's entry.
    // For every other fault type this is a strict no-op returning `entry`
    // unchanged AND consuming no budget, so the T01-T06/T08/T10 paths are
    // byte-equivalent. The lookup-HIT-only tlb_state/attr/pfn models stay in
    // maybeCorrupt; this hook exists because false_hit needs the MISS case
    // and the returned-pointer slot, neither of which maybeCorrupt owns.
    ArmISA::TlbEntry *maybeCorruptLookup(ArmISA::TlbEntry *entry, Addr va,
                                         uint64_t req_seq, uint64_t req_size);

    // [MDSPEC][R4-10-T08-b/c/d] walk/refill pairing sub-models (FS-only).
    // Called at the refill completion point (WalkUnit::insertTableEntry)
    // BEFORE mmu->insert, once per COMPLETED walk:
    //   * T08-b walk_fill_dup    — the same walk's result is written a SECOND
    //     time (the caller must insert `te` again): returns true.
    //   * T08-c walk_done_early  — the completion (done) signal is reported at
    //     the walk's ISSUE tick instead of the refill tick; the data payload
    //     stays correct (spec T08: timing-only fault).
    //   * T08-d walk_stale_result— the PREVIOUS completed walk's translation
    //     (pfn) is written into the current entry (a stale result).
    // Also maintains the last-completed-walk record consumed by T08-d. Returns
    // true only for the duplicated-refill arm. For a non-walk-family model or
    // no pending arm this is a strict no-op returning false (byte-equivalent
    // to the pre-R4-10 tree). The pairing node pair (tlb_walk/tlb_refill with
    // the sub-model's field/outcome) is emitted HERE, at the refill point.
    bool maybeCorruptWalkRefill(uint64_t walk_id, Addr va, uint64_t req_seq,
                                uint64_t walk_start_tick, unsigned level,
                                ArmISA::TlbEntry *te);

    // [MDSPEC][R6-FIXCPP/B] lookup-mode F-tier polling, the C++ half of the
    // R6-FTIER defect (the campaign's ARMTLB_LOOKUP_TIERS block names this
    // exact gap: "Making them runnable needs a C++ change to CHAOSArmTLB").
    //
    // Pre-fix: the lookup-HIT path (TLB::lookup -> maybeCorrupt /
    // maybeCorruptLookup) NEVER polled lsuTrigger — it appeared only in the
    // constructor and in maybeDropWalkFill — so F1-F6 had no landed knob
    // there and every tier silently degraded to F0. These two hooks give the
    // lookup path a REAL eligible-event stream (one eligible event per
    // TLB-hit lookup), consumed with the tier semantics of
    // src/cpu/o3/chaos_lsu_trigger.hh (the same event-normalized trigger the
    // walk path and every other LSU injector uses — no new frequency is
    // invented here):
    //   * F0 — NOT tiered: the legacy chain (--tlb_max_faults /
    //     --tlb_probability + the seed-varied eligible-event skip) is
    //     byte-equivalent to the pre-R6 tree. `lookupTierMounted()` returns
    //     false for it, so the legacy gates below run unchanged.
    //   * F1/F2/F3 — mean interval 1e6/1e5/1e4 eligible lookups, ±50% jitter
    //     (chaos_lsu_trigger.hh intervalEvents + scheduleNext).
    //   * F4 — burst: every 1e5 eligible lookups fire once, then 2-4
    //     consecutive lookups.
    //   * F5 — permanent: every eligible lookup from warm-up on.
    //   * F6 — once, at the first TlbHit event. TLB::lookup notifies the F6
    //     source BEFORE the injection hooks (see arch/arm/tlb.cc) so the
    //     injection happens AT that event, not one lookup later.
    // When a non-F0 tier is mounted it IS the frequency model for this path:
    // --tlb_max_faults is NOT consumed (the tier decides how many times),
    // and the mismatch is reported LOUDLY at the first eligible lookup
    // instead of silently capping the tier back to a single shot.
    bool lookupTierMounted() const;
    // [R6-F6APP] The tier poll is SPLIT so model applicability can sit
    // between its two halves: `lookupTierBookAttempt` runs for every TLB-hit
    // lookup (funnel: attempted) and is the only half the candidate-less case
    // may reach; `lookupTierFires` is the tier's inject-now decision for one
    // ELIGIBLE lookup and must only be called once a legal candidate is known
    // to exist (F6 spends its one shot here; F1-F4 advance their interval
    // slot here). See the ruling in chaos_tlb_pfn.hh.
    void lookupTierBookAttempt();
    bool lookupTierFires(bool is_hit);
    // [R6-F0FUNNEL] Exit-time authoritative funnel summary for the F0 legacy
    // path (the tier path prints its own via ChaOSLsuTrigger::summary). Same
    // line format the campaign / L5 / obs-core parsers already accept.
    void printLegacyFunnelSummary() const;

  private:
    // PfnToMappedPage = §2.10 F5 (Phase 4.4, FS-only): substitute the hit
    // entry's pfn with another MAPPED entry's pfn (legal domain -> silent
    // wrong-page access, method2's silent-SDC pathway).
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random,
                           PfnToMappedPage,
                           // [R4-5.9] T08: FS page-table walk/fill pairing
                           // (walk_pairing) — see maybeDropWalkFill.
                           WalkPairing,
                           // [R4-10-T08-b/c/d] walk/refill pairing sub-models
                           // — see maybeCorruptWalkRefill. All four are the
                           // walk family (isWalkFamily) and are armed at the
                           // issue point (maybeDropWalkFill) then applied at
                           // the refill completion point.
                           WalkDuplicate,   // T08-b duplicated refill
                           WalkEarlyDone,   // T08-c done reported too early
                           WalkStaleResult, // T08-d previous walk's result
                           // [R4-10-T05] entry identity / lifecycle STATE:
                           // valid清零/伪置位、global翻转、ASID替换为别的
                           // 活跃ASID（每次只改一种状态）。Lookup-HIT path.
                           ValidClear, ValidSet, GlobalFlip, AsidSubst,
                           // [R4-10-T06] access-attribute LEGAL substitution
                           // (PPN不变): AP权限、memory type、page size 各替换
                           // 为同 TLB 另一条 live 表项的合法编码。
                           PermSubst, MemTypeSubst, PageSizeSubst,
                           // [R4-10-T07] CAM compare / way select:
                           // false hit / double hit / wrong-way selection.
                           // Handled in maybeCorruptLookup (needs the miss
                           // case + the returned-pointer slot).
                           FalseHit, DoubleHit, WrongWay };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);
    // [R4-10] family predicates (single source of truth for which hook owns
    // which model — no drift between maybeCorrupt / maybeCorruptLookup /
    // maybeDropWalkFill).
    static bool isEntryStateFault(FaultType f)
    {
        return f == FaultType::ValidClear || f == FaultType::ValidSet ||
               f == FaultType::GlobalFlip || f == FaultType::AsidSubst;
    }
    static bool isAttrSubstFault(FaultType f)
    {
        return f == FaultType::PermSubst || f == FaultType::MemTypeSubst ||
               f == FaultType::PageSizeSubst;
    }
    static bool isCamFault(FaultType f)
    {
        return f == FaultType::FalseHit || f == FaultType::DoubleHit ||
               f == FaultType::WrongWay;
    }
    static bool isWalkFamily(FaultType f)
    {
        return f == FaultType::WalkPairing || f == FaultType::WalkDuplicate ||
               f == FaultType::WalkEarlyDone ||
               f == FaultType::WalkStaleResult;
    }
    // [R4-10-T05/T06] apply an entry-state or attribute-substitution fault to
    // `entry` and register the tlb_state node. Returns true if applied (a
    // legal substitute existed and the field changed), false = honest no-op
    // (no candidate — nothing registered, nothing counted).
    bool applyEntryFieldFault(ArmISA::TlbEntry *entry, FaultType ft, Addr va,
                              uint64_t req_seq, uint64_t req_size);

    // Stable lookup-slot identity plus the complete TLB entry state carried
    // by the T-series L1/L2 observation events. -1 means no applicable way.
    int entryIndex(const ArmISA::TlbEntry *entry) const;
    std::string snapshotEntry(const ArmISA::TlbEntry *entry, Addr pa) const;
    // [R6-F6APP] Read-only collection of the legal pfn-substitute candidates
    // for `entry`, in deterministic entryTable() order, paired with their
    // table index. Pure scan: no RNG draw, no TLB mutation, no member state
    // change — this IS the applicability test the tier gate must consult
    // BEFORE consuming a fire opportunity.
    void collectPfnCandidates(
        const ArmISA::TlbEntry *entry,
        std::vector<std::pair<const ArmISA::TlbEntry *, int>> &out) const;

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
    // [MDSPEC][R4-6-T08] one-shot diagnostics for faultType=walk_pairing.
    // (1) lookup_notice: TLB::lookup reached maybeCorrupt with the
    //     walk-issue-only model mounted — logged once and SKIPPED, so the
    //     fault budget is never consumed by the lookup-hit path (the
    //     R4-5.9 pilot's root cause: old_pfn == new_pfn at
    //     Site: arm_tlb_lookup_hit with the single maxFaults budget gone).
    // (2) probe_notice: TableWalker::walk reached maybeDropWalkFill — the
    //     wiring proof for the walk hook, printed once per run so it
    //     survives a timeout-killed sim (no exit callback needed).
    bool walk_pairing_lookup_notice = false;
    bool walk_pairing_probe_notice = false;
    // [MDSPEC][R4-10-T08-b/c/d] state for the refill-side sub-models.
    // pending_walk_id: the walk_id armed at the issue point (0 = none); the
    // refill hook applies the sub-model only to THAT walk. last_walk_pfn /
    // last_walk_vpn / have_last_walk: the PREVIOUS completed walk's result,
    // consumed by walk_stale_result (T08-d).
    uint64_t pending_walk_id = 0;
    Addr last_walk_pfn = 0;
    Addr last_walk_vpn = 0;
    bool have_last_walk = false;
    bool stale_no_previous_notice = false;
    // [R6-F0FUNNEL 2026-10-25] PASSIVE F0-legacy funnel observation.
    // F0 mounts no ChaOSLsuTrigger (the tier object exists only when
    // --tlb_lsu_tier != "off"), so the legacy lookup path had NO authority to
    // report attempted/eligible from — the campaign could only record None.
    // These counters OBSERVE ONLY: no injection decision, RNG draw,
    // events_to_skip decrement or fault-cap test reads them, so the F0
    // injection sequence is byte-identical with and without this fix.
    // `injected` is deliberately NOT mirrored here — the exit summary prints
    // the real faults_injected_count, the same counter the fault budget uses.
    uint64_t legacy_attempted = 0;
    uint64_t legacy_eligible = 0;
    uint64_t legacy_first_eligible_tick = 0;
    uint64_t legacy_last_eligible_tick = 0;

    // [R6-F5-NOEFFECT] F5 固定掩码 latch + lookup 侧 no_effect 聚合。
    // 规范 07:60 要求"warm-up 后固定一个物理 bit"且"每次读出施加同一掩码"，
    // 故掩码在本次运行内只抽一次；"正确值本来就等于卡死值"的那些读出只进
    // 聚合，不建 fault identity、不写日志、不发事件、不计 stats。
    uint64_t f5_stuck_mask = 0;                 // 0 = 尚未抽取
    uint64_t lookup_no_effect = 0;
    uint64_t lookup_effective = 0;
    uint64_t lookup_no_effect_first_tick = 0;
    uint64_t lookup_no_effect_last_tick = 0;
    // [R6-F5-NOEFFECT] The raw `--tlb_lsu_tier` spelling, kept so the exit-time
    // CHAOS_LSU_NOEFFECT summary derives requested/effective from the SAME
    // chaos_lsu_tier_cap::resolve(param, mounted_tier) the startup marker uses
    // — no second spelling convention invented at exit time.
    std::string lsu_tier_string;
    void printNoEffectSummary() const;

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
    uint64_t generateRandomMaskInFrame(int bits_to_change, uint64_t pfn);

    // [MDSPEC][R6-FIXCPP/B] one-shot lookup-tier reachability/budget notice.
    // Printed to armtlb_injections.log at the FIRST eligible lookup of a
    // tiered (non-F0) run: it records that the lookup path really polls the
    // event-normalized trigger, and — when --tlb_max_faults is also set — that
    // the legacy cap is NOT consumed by a tiered run (the tier is the
    // frequency model). Silent-zero discipline: a tiered lookup run whose
    // eligible stream never reaches the tier's first fire is visible in the
    // trigger summary (attempted/eligible/injected), never assumed.
    bool tier_lookup_notice = false;

    struct CHAOSArmTLBStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        // [R4-10-T05/T06/T07] entry-state / attribute / CAM faults applied.
        statistics::Scalar numStateFaults;
        CHAOSArmTLBStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSArmTLBStats> stats;
};

} // namespace gem5
#endif // __ARCH_ARM_CHAOS_ARM_TLB_HH__
