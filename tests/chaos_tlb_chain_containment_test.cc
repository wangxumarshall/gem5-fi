/*
 * chaos_tlb_chain_containment_test.cc — standalone unit test for
 * CHAOSPropagation/chaos_tlb_chain.hh (the [R6-FIXCPP/A] TLB-fault chain
 * admission + containment-revocation contract). NOT part of the gem5 build;
 * compiled directly:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_tlb_chain_containment_test.cc -o /tmp/tlb_chain_test \
 *       && /tmp/tlb_chain_test
 *
 * Root cause under test (measured T01-F0-W4/seed1; the offline contract pin
 * tests/test_lsu_r6_contained_chain_contract.py):
 *   the injection flips pfn bit 56. `pfn << 12` wraps out of the 64-bit Addr,
 *   so the EFFECTIVE PA is unchanged (0x81d75fa8 == 0x81d75fa8) and the site
 *   reports pa_changed = 0. Yet registerTlbFault registered the SEQ-PRIMARY
 *   arm for EVERY req_seq != 0, so the SAME request's later CLEAN events
 *   (sq_execute / sq_writeback / resp / taint_reg) joined the chain by seq:
 *   one chain asserted "L2 contained" AND "propagated to L4", which the chain
 *   checker (correctly, ruling D) rejects with time_reversed_edge.
 *
 * The rules pinned here are the ones the tracer runs — CHAOSPropagation.cc
 * includes THIS header and calls these functions (drift-guarded by the
 * python wrapper).
 */
#include <cstdint>
#include <cstdio>
#include <string>

#include "cpu/o3/CHAOSPropagation/chaos_tlb_chain.hh"

using gem5::chaos_chain::Arms;
using gem5::chaos_chain::ChainArmModel;
using gem5::chaos_chain::containmentRevokesArms;
using gem5::chaos_chain::tlbRegistrationArms;
using gem5::chaos_chain::translationContained;

static int failed = 0;

static void
check(const std::string &name, bool cond, const std::string &detail = "")
{
    if (cond) {
        std::printf("PASS %s\n", name.c_str());
    } else {
        std::printf("FAIL %s%s\n", name.c_str(),
                    detail.empty() ? "" : ("  [" + detail + "]").c_str());
        ++failed;
    }
}

int
main()
{
    // The measured T01-F0-W4/seed1 numbers.
    const uint64_t req_seq = 301;
    const uint64_t va_lo = 0xffffffc009483fa8ull;
    const uint64_t clean_pa = 0x81d75fa8ull;   // == the "new" PA: no redirect
    const uint64_t new_page = clean_pa & ~0xfffull;
    const uint64_t span = 0x1000;

    std::printf("[1] the T01 shape: effective PA unchanged -> NO arm opens\n");
    {
        Arms a = tlbRegistrationArms(req_seq, /*pa_changed=*/false);
        check("req_seq!=0 but pa_changed=0 opens no seq arm", !a.seq_primary);
        check("...and no addr_fallback arm either", !a.addr_fallback);
        check("...so the chain has no correlation surface at all", !a.any());
    }

    std::printf("[2] the same request's later CLEAN events cannot join\n");
    {
        ChainArmModel m;
        m.registerFault(/*ptag=*/1, req_seq, va_lo, new_page, span,
                        /*pa_changed=*/false);
        check("addr registry empty after the registration", m.empty());
        check("later sq_execute/resp by seq finds no chain (1 -> 0)",
              m.lookupSeq(va_lo) == 0);
        check("later cache event on the (unchanged) PA finds no chain",
              m.lookupBlock(clean_pa) == 0);
    }

    std::printf("[3] a REAL redirect keeps propagation (no over-fix)\n");
    {
        Arms a = tlbRegistrationArms(req_seq, /*pa_changed=*/true);
        // [R6-FIXARMS 2026-10-24] The two arms are INDEPENDENT: a real
        // physical redirect leaves the whole forged PA page reachable, so the
        // address-fallback arm must open alongside the seq arm.
        check("pa_changed=1 with a Request identity opens BOTH seq_primary and addr_fallback",
              a.seq_primary && a.addr_fallback);
        ChainArmModel m;
        m.registerFault(1, req_seq, va_lo, new_page, span, true);
        check("the faulting request's own later events still join by seq",
              m.lookupSeq(va_lo) == 1);
        // The forged PA page is SHARED: a same-page victim request must be
        // attributed too. (Pre-fix defect: an `else` made this 0, so the
        // victim lost attribution, `errant_commit` vanished and the chain was
        // misjudged as a fake L4 containment.)
        check("a same-(forged)-PA-page event DOES join via the addr arm",
              m.lookupBlock(new_page) == 1);
    }

    std::printf("[4] seq-less lookups keep the labeled addr_fallback\n");
    {
        Arms a = tlbRegistrationArms(/*req_seq=*/0, /*pa_changed=*/true);
        check("req_seq==0 + real redirect -> addr_fallback only",
              !a.seq_primary && a.addr_fallback);
        ChainArmModel m;
        m.registerFault(2, 0, va_lo, new_page, span, true);
        check("the wrong-page arm is registered", m.lookupBlock(new_page) == 2);
        check("no seq arm for a seq-less lookup", m.lookupSeq(va_lo) == 0);
        Arms b = tlbRegistrationArms(0, /*pa_changed=*/false);
        check("req_seq==0 + no redirect -> still no arm", !b.any());
    }

    std::printf("[5] CONTAINMENT revokes arms already opened\n");
    {
        ChainArmModel m;
        m.registerFault(3, req_seq, va_lo, new_page, span, /*pa_changed=*/true);
        check("pre-condition: the seq arm is live",
              m.lookupSeq(va_lo) == 3);
        // Translation completed with the SAME PA as the clean baseline.
        m.complete(3, /*translation_blocked=*/false, /*walk_fault=*/false,
                   /*has_pa=*/true, /*pa_equals_clean=*/true);
        check("post-containment: no residual seq mapping", m.empty());
        check("...so a later clean event cannot join a closed chain",
              m.lookupSeq(va_lo) == 0 && m.lookupBlock(new_page) == 0);
    }
    {
        // The blocked case (permission/alignment fault): the PA may well have
        // changed, yet the translation never happens -> revoke the page arm.
        ChainArmModel m;
        m.registerFault(4, 0, va_lo, new_page, span, /*pa_changed=*/true);
        check("pre-condition: the fallback page arm is live",
              m.lookupBlock(new_page) == 4);
        m.complete(4, /*translation_blocked=*/true, false, /*has_pa=*/false,
                   /*pa_equals_clean=*/false);
        check("blocked translation revokes the fallback arm", m.empty());
    }

    std::printf("[6] NON-contained completion keeps the chain open\n");
    {
        ChainArmModel m;
        m.registerFault(5, req_seq, va_lo, new_page, span, true);
        m.complete(5, /*translation_blocked=*/false, /*walk_fault=*/false,
                   /*has_pa=*/true, /*pa_equals_clean=*/false);
        check("a real redirect is NOT revoked (propagation continues)",
              m.lookupSeq(va_lo) == 5);
    }
    check("walk-family unknown baseline never claims containment",
          !containmentRevokesArms(
              translationContained(false, /*walk_fault=*/true, true, true)));
    check("walk result with no PA is not containment",
          !translationContained(false, true, /*has_pa=*/false, false));
    check("blocked is containment", translationContained(true, false, false,
                                                        false));
    check("unchanged effective PA is containment",
          translationContained(false, false, true, true));

    std::printf("[7] revocation is scoped and idempotent\n");
    {
        ChainArmModel m;
        m.registerFault(6, req_seq, va_lo, new_page, span, true);
        m.registerFault(7, req_seq + 1, va_lo + 0x800, new_page + 0x1000, span,
                        true);
        m.complete(6, false, false, true, true);     // revoke only ptag 6
        check("only the contained chain's arm is dropped",
              m.lookupSeq(va_lo) == 0 && m.lookupSeq(va_lo + 0x800) == 7);
        m.revoke(6);
        m.revoke(6);
        check("re-revoking an arm-less chain is a no-op",
              m.lookupSeq(va_lo) == 0 && m.lookupSeq(va_lo + 0x800) == 7);
        m.revoke(0);
        check("revoke(0) touches nothing",
              m.lookupSeq(va_lo + 0x800) == 7);
    }

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
