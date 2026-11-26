#ifndef __CPU_O3_CHAOS_PROPAGATION_TLB_CHAIN_HH__
#define __CPU_O3_CHAOS_PROPAGATION_TLB_CHAIN_HH__

// [MDSPEC][R6-FIXCPP/A] TLB-fault chain admission + containment revocation.
//
// Dependency-free on purpose (same pattern as arch/arm/CHAOSArmTLB/
// chaos_tlb_pfn.hh): CHAOSPropagation.cc (inside the gem5 build) and the
// standalone unit test (tests/chaos_tlb_chain_containment_test.cc, compiled
// with plain g++) share THIS ONE definition, so the rule under test is the
// rule that runs — no drift between the regression suite and the tracer.
//
// Root cause this encodes the fix for (measured T01-F0-W4/seed1, contract
// pin tests/test_lsu_r6_contained_chain_contract.py):
//   * the injection flips pfn bit 56; `pfn << 12` wraps out of the 64-bit
//     Addr, so the EFFECTIVE PA is unchanged (0x81d75fa8 == 0x81d75fa8) and
//     the injection site itself reports pa_changed = 0;
//   * but CHAOSPropagation::registerTlbFault registered the SEQ-PRIMARY arm
//     for every req_seq != 0 unconditionally, so the SAME request's later
//     CLEAN events (sq_execute / sq_writeback / resp / taint_reg) joined the
//     fault chain by seq — one chain simultaneously claimed "L2 contained"
//     and "propagated to L4", and the checker (correctly) rejected it with
//     time_reversed_edge.
// The fix: a fault whose corrupted pfn does NOT redirect the PA has no
// downstream effect, so it opens NO correlation arm at all (the chain
// honestly stops at the TLB layer), and a translation that completes
// CONTAINED additionally revokes any arm the chain did open (no residual
// mapping left behind for later events to join).

#include <cstdint>
#include <map>

namespace gem5
{
namespace chaos_chain
{

// Which correlation arms a TLB-entry fault registration may open.
//   seq_primary   — the addr-registry arm bound to the faulting request's
//                   dyn_seq (its later seq-keyed events join by seq);
//   addr_fallback — the labeled, address-only arm on the WRONG physical page
//                   (only reachable when req_seq == 0 — a table-walker or
//                   functional lookup with no Request identity).
struct Arms
{
    bool seq_primary = false;
    bool addr_fallback = false;

    bool
    any() const
    {
        return seq_primary || addr_fallback;
    }
};

// The registration decision. `pa_changed` is the REAL physical-redirect
// verdict computed at the injection site (old_page != new_page on gem5's own
// pAddr arithmetic, which includes the 64-bit wrap). An unchanged effective
// PA means the translation the MMU performs is the CLEAN one — there is
// nothing downstream to attribute, so no arm opens (pre-fix defect: the
// seq arm ignored this and captured clean traffic).
inline Arms
tlbRegistrationArms(uint64_t req_seq, bool pa_changed)
{
    Arms a;
    if (!pa_changed)
        return a;                    // effective PA unchanged: no downstream surface
    // [R6-FIXARMS 2026-10-24] The two arms are INDEPENDENT, not either/or.
    // A real physical redirect makes the whole forged PA page reachable, so
    // the address-fallback arm must open in BOTH cases; the seq arm
    // additionally binds the faulting request itself. (Pre-fix defect: an
    // `else` made them mutually exclusive, so with pa_changed=1 & req_seq!=0
    // the same-page victim requests lost attribution, `errant_commit`
    // disappeared, and the chain was misjudged as a fake L4 containment.)
    a.addr_fallback = true;          // forged PA page is shared -> always open
    if (req_seq != 0)
        a.seq_primary = true;        // ... plus the faulting request (seq-bound)
    return a;
}

// The translation-completion verdict, mirroring noteTlbTranslationResult:
// a translation is CONTAINED when it was blocked (permission/alignment/
// injected fault) or when its effective PA equals the clean baseline. A
// walk-family fault has no clean-PA baseline, so it can never claim
// containment on the strength of an unknown baseline.
inline bool
translationContained(bool translation_blocked, bool walk_fault, bool has_pa,
                     bool pa_equals_clean)
{
    if (translation_blocked)
        return true;
    if (walk_fault)
        return false;                // unknown baseline is not a containment proof
    return has_pa && pa_equals_clean;
}

// Does a contained completion revoke the chain's registry arms? Yes: the
// chain's terminal state is "absorbed at this layer", so a residual mapping
// would let a LATER event join a chain that is already closed — exactly the
// "one chain asserts contained AND propagated" contradiction, relocated.
// Revocation is unconditional on containment (idempotent: revoking no arms
// is a no-op).
inline bool
containmentRevokesArms(bool contained)
{
    return contained;
}

// ---------------------------------------------------------------------------
// [R6-FIXCPP/A] The registration/revocation BEHAVIOUR, as a plain-data model.
//
// The tracer's real registries are std::map<Addr, AddrEntry> /
// std::map<Addr, BlkEntry> keyed exactly like this model's (addr arm keyed by
// the registration VA, fallback arm keyed by the wrong PA page base) with the
// ptag as the value. The model exists so the unit test can drive the REAL
// decision functions above through a real register/complete sequence and
// assert the observable outcome (does a later clean event still join this
// chain?) instead of only asserting the decision table.
class ChainArmModel
{
  public:
    // registerTlbFault's registration decision, applied.
    void
    registerFault(uint64_t ptag, uint64_t req_seq, uint64_t va_lo,
                  uint64_t new_page, uint64_t pa_span, bool pa_changed)
    {
        const Arms a = tlbRegistrationArms(req_seq, pa_changed);
        if (a.seq_primary)
            addr[va_lo] = ptag;
        if (a.addr_fallback) {
            blk_begin = new_page;
            blk_end = new_page + pa_span;
            blk_ptag = ptag;
        }
    }

    // noteTlbTranslationResult's containment path, applied.
    void
    complete(uint64_t ptag, bool translation_blocked, bool walk_fault,
             bool has_pa, bool pa_equals_clean)
    {
        const bool contained =
            translationContained(translation_blocked, walk_fault, has_pa,
                                 pa_equals_clean);
        if (containmentRevokesArms(contained))
            revoke(ptag);
    }

    // revoke: drop every arm of this ptag from both registries.
    void
    revoke(uint64_t ptag)
    {
        for (auto it = addr.begin(); it != addr.end(); ) {
            if (it->second == ptag)
                it = addr.erase(it);
            else
                ++it;
        }
        if (blk_ptag == ptag)
            blk_ptag = 0;
    }

    // A later event's join attempt: the seq-bound addr arm.
    uint64_t
    lookupSeq(uint64_t va_lo) const
    {
        const auto it = addr.find(va_lo);
        return it == addr.end() ? 0 : it->second;
    }

    // A later event's join attempt: the address-only fallback arm.
    uint64_t
    lookupBlock(uint64_t a) const
    {
        if (blk_ptag && a >= blk_begin && a < blk_end)
            return blk_ptag;
        return 0;
    }

    bool
    empty() const
    {
        return addr.empty() && blk_ptag == 0;
    }

  private:
    std::map<uint64_t, uint64_t> addr;   // registration VA -> ptag
    uint64_t blk_ptag = 0;
    uint64_t blk_begin = 0;
    uint64_t blk_end = 0;
};

} // namespace chaos_chain
} // namespace gem5

#endif // __CPU_O3_CHAOS_PROPAGATION_TLB_CHAIN_HH__
