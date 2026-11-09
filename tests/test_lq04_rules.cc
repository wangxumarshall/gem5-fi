#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSLQ04/lq04_rules.hh"

using namespace gem5::chaos_lq04;

int
main()
{
    // v3.2.10 LQ04 assert set (verbatim from the plan). The predicate is
    // valid && has_request && !squashed && !executed; `executeLoad`
    // early-returns for an instruction that is already executed, so the
    // executed flag guards against counting a repeated call as a new ordinal.
    assert(isEligible(true, true, false, false));          // valid, request, not squashed, not executed
    assert(!isEligible(false, true, false, false));        // no valid entry
    assert(!isEligible(true, false, false, false));        // no request
    assert(!isEligible(true, true, false, true));          // executed flag set
    assert(!isEligible(true, true, true, false));          // squashed
    assert(!isEligible(true, true, true, true));           // squashed and executed

    // EventOrdinal is the 1-based ordinal of the eligible Load stream;
    // ordinal 0 never selects.
    assert(shouldSelect(3, 3));
    assert(!shouldSelect(3, 0));
    assert(!shouldSelect(2, 3));

    // Target identity is (LQ index, entry generation).
    assert(identityMatches(7, 11, 7, 11));
    assert(!identityMatches(7, 12, 7, 11));                // generation mismatch
    assert(!identityMatches(8, 11, 7, 11));                // index mismatch

    // maxFaults == 0 clamps to one injection.
    assert(shouldInject(0, 0));
    assert(!shouldInject(1, 1));                           // one-shot spent
    assert(!shouldInject(1, 0));

    std::printf("LQ04 ordinal/identity rules: PASS\n");
    return 0;
}
