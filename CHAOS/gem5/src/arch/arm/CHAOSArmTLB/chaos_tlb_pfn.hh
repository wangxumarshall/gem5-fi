#ifndef __ARCH_ARM_CHAOS_ARM_TLB_PFN_HH__
#define __ARCH_ARM_CHAOS_ARM_TLB_PFN_HH__

// [MDSPEC][R6-FIXC] T04 `pfn_to_mapped_page` candidate predicate.
//
// Dependency-free on purpose: CHAOSArmTLB.cc (inside the gem5 build) and the
// standalone unit test (tests/chaos_tlb_pfn_candidate_test.cc, compiled with
// plain g++) share THIS ONE definition, so the rule under test is the rule
// that runs — no drift between the regression suite and the injector.
//
// Root cause this encodes the fix for (measured on the frozen binary, 3/3
// seeds): the pre-R6 candidate filter was
//     `&(*it) != entry && it->pfn != entry->pfn`
// — it never required `it->valid`. The TLB holds many stale/invalid slots
// whose pfn == 0; those dominated the candidate set (真机 `candidates: 31`)
// and the rng draw landed on pfn == 0 -> new_pfn == 0x0 -> PA 0xfa8 -> guest
// level-0 translation fault -> kernel Oops. Spec §2.10 F5 wants a SILENT read
// of a WRONG *LIVE* page, so the substitute must be a different live frame of
// the SAME page size (pAddr(va) == (pfn << N) | (va & size) — a different N
// shifts the physical address by a different amount).

#include <cstddef>  // size_t (selectPfnCandidateIndex)
#include <cstdint>

namespace gem5
{
namespace chaos_tlb
{

// The ArmISA::TlbEntry fields the candidate rule depends on, as plain values.
struct PfnCandidateView
{
    // entry->valid — mapping state: is this a live translation?
    bool valid = false;
    // entry->pfn — the physical frame number.
    uint64_t pfn = 0;
    // entry->N — page-size exponent (pAddr shifts by N).
    uint8_t page_size_bits = 0;
    // &entry == the entry being faulted (never substitute with itself).
    bool is_hit_entry = false;
};

// True iff `cand` is a legal target for the T04 pfn substitution of `hit`:
//   (1) not the hit entry itself;
//   (2) a LIVE mapping (`valid`) — excludes stale/invalid slots;
//   (3) never the invalid frame pfn == 0;
//   (4) the same page size as the hit entry (address relation);
//   (5) a DIFFERENT physical frame than the hit entry (else it is a no-op).
inline bool
isSelectablePfnTarget(const PfnCandidateView &hit, const PfnCandidateView &cand)
{
    if (cand.is_hit_entry) return false;
    if (!cand.valid) return false;
    if (cand.pfn == 0) return false;
    if (cand.page_size_bits != hit.page_size_bits) return false;
    if (cand.pfn == hit.pfn) return false;
    return true;
}

// Deterministic, reproducible selection: index into the collected candidate
// list for a given rng draw. Same seed -> same draw sequence -> same index;
// an empty set returns 0, which the caller MUST treat as an honest no-op.
inline size_t
selectPfnCandidateIndex(size_t count, uint64_t draw)
{
    return count ? static_cast<size_t>(draw % count) : 0;
}

// [R6-F6APP] Model-applicability is part of ELIGIBILITY.
//
// Root cause this encodes the fix for (measured 2026-10-25, T04-F6-W4 seed1,
// binary a9b2c236): the substitution hook polled the tier BEFORE it looked
// for a legal substitute, so the F6 one-shot was consumed by the very FIRST
// TLB hit — a hit with no other live same-page-size frame. F6 recorded
// spent/eligible=1/injected=1 while the model applied nothing
// (numFaultsInjected=0, no injection log, no prop_evt): exactly the
// count_contradiction the campaign raised. F1-F4 had the same shape — a
// fired interval slot on a candidate-less lookup advanced next_fire and
// counted an injection that was never written.
//
// The rule: one TLB-hit lookup on this model books the funnel ATTEMPT (it
// reached the hook) unconditionally; it is ELIGIBLE only when the read-only
// candidate scan found at least one legal substitute; the tier fires — and
// therefore consumes RNG/state — only for an eligible lookup, and the
// mutation is applied iff the tier fired.
enum class PfnHookAction
{
    // No legal substitute: book `attempted`, then stop. No onEligible /
    // onF6Event call, no eligible/injected increment, no F6 `spent`.
    AttemptOnly,
    // A legal substitute exists: the lookup is eligible; poll the tier and
    // apply the substitution iff it fires.
    PollTier,
};

inline PfnHookAction
pfnHookAction(std::size_t candidate_count)
{
    return candidate_count ? PfnHookAction::PollTier
                           : PfnHookAction::AttemptOnly;
}

} // namespace chaos_tlb
} // namespace gem5

#endif // __ARCH_ARM_CHAOS_ARM_TLB_PFN_HH__
