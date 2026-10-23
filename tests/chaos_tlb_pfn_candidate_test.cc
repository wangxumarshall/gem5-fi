/*
 * chaos_tlb_pfn_candidate_test.cc — standalone unit test for
 * CHAOSArmTLB/chaos_tlb_pfn.hh (the T04 pfn_to_mapped_page candidate
 * predicate). NOT part of the gem5 build; compiled directly:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_tlb_pfn_candidate_test.cc -o /tmp/tlb_pfn_test \
 *       && /tmp/tlb_pfn_test
 *
 * Root cause under test (measured on the frozen binary, 3/3 seeds):
 * CHAOSArmTLB.cc:427 collected candidates with only
 *   `&(*it) != entry && it->pfn != entry->pfn`
 * — missing `it->valid`. The TLB is full of stale/invalid slots whose
 * pfn == 0; they dominated the candidate set (真机 candidates: 31) and the
 * rng draw landed on pfn == 0 -> new_pfn == 0x0 -> PA 0xfa8 -> guest level-0
 * translation fault -> kernel Oops. That is a "wrong page + crash" fault,
 * NOT the spec §2.10 F5 "silently read a wrong LIVE page".
 *
 * The predicate must: (1) require valid (mapping state); (2) never pick the
 * invalid frame 0; (3) require the candidate's page-size exponent N to match
 * the hit entry's (pAddr(va) == (pfn << N) | (va & size) — a different N
 * shifts the PA by a different amount); (4) require a DIFFERENT physical
 * frame; (5) never substitute the hit entry with itself.
 */
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>

#include "arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh"

using gem5::chaos_tlb::PfnCandidateView;
using gem5::chaos_tlb::isSelectablePfnTarget;
using gem5::chaos_tlb::selectPfnCandidateIndex;

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

/* A plain 4 KiB live mapping (N == 12, the kernel page size in the pilot). */
static PfnCandidateView
view(bool valid, uint64_t pfn, uint8_t n = 12, bool is_hit = false)
{
    PfnCandidateView v;
    v.valid = valid;
    v.pfn = pfn;
    v.page_size_bits = n;
    v.is_hit_entry = is_hit;
    return v;
}

int
main()
{
    const PfnCandidateView hit = view(/*valid=*/true, /*pfn=*/0x81d75);

    std::printf("[1] invalid / stale / zero-frame candidates are EXCLUDED\n");
    // The exact stale slot that caused the crash: an invalid entry with pfn 0.
    check("invalid slot (valid=0, pfn=0) rejected",
          !isSelectablePfnTarget(hit, view(false, 0)),
          "stale zero-frame slot must never be a substitute");
    check("invalid slot (valid=0, pfn!=0) rejected (mapping state)",
          !isSelectablePfnTarget(hit, view(false, 0x1234)),
          "only live mappings are legal substitutes");
    check("valid but pfn==0 rejected (never select frame 0)",
          !isSelectablePfnTarget(hit, view(true, 0)),
          "pfn 0 is the invalid-frame sentinel");

    std::printf("[2] a legal LIVE mapping is SELECTED\n");
    check("live, non-zero, same-size, different-frame accepted",
          isSelectablePfnTarget(hit, view(true, 0x81d76)),
          "the spec's silent wrong-live-page target");

    std::printf("[3] page-size consistency (address relation)\n");
    check("page-size mismatch rejected (N differs)",
          !isSelectablePfnTarget(hit, view(true, 0x40000, /*n=*/21)),
          "different N shifts the PA differently");
    check("page-size match accepted",
          isSelectablePfnTarget(hit, view(true, 0x40000, /*n=*/12)));

    std::printf("[4] identity / same-frame relations\n");
    check("the hit entry itself rejected",
          !isSelectablePfnTarget(hit, view(true, 0x81d75, 12, /*is_hit=*/true)));
    check("same physical frame as hit rejected (no-op substitution)",
          !isSelectablePfnTarget(hit, view(true, 0x81d75)));

    std::printf("[5] deterministic, reproducible selection\n");
    check("index is in range", selectPfnCandidateIndex(31, 12345) < 31);
    check("same draw -> same index (reproducible)",
          selectPfnCandidateIndex(31, 777) == selectPfnCandidateIndex(31, 777));
    check("empty candidate set -> 0 (caller must no-op)",
          selectPfnCandidateIndex(0, 777) == 0);
    check("distinct draws over a set span every slot",
          selectPfnCandidateIndex(3, 0) == 0 &&
          selectPfnCandidateIndex(3, 1) == 1 &&
          selectPfnCandidateIndex(3, 2) == 2);

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
