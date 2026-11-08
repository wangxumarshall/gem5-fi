#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSMD04/md04_rules.hh"

using namespace gem5::chaos_md04;

int
main()
{
    // MD04-ELIG-v1: 8-byte store + younger load with real byte overlap and
    // the same shifted-range predicate used by checkViolations.
    assert(isEligibleViolationPair(0x1000, 8, 0x1000, 8, 3));
    assert(isEligibleViolationPair(0x1000, 16, 0x1000, 8, 3));  // LDP covers
    assert(isEligibleViolationPair(0x1004, 16, 0x1000, 8, 3));  // LDP starts +4
    assert(isEligibleViolationPair(0x0ffc, 16, 0x1000, 8, 3));  // LDP starts -4
    assert(!isEligibleViolationPair(0x1008, 8, 0x1000, 8, 3));  // disjoint
    assert(!isEligibleViolationPair(0x1000, 4, 0x1000, 8, 3));  // 4B load
    assert(!isEligibleViolationPair(0x1000, 8, 0x1000, 4, 3));  // 4B store
    assert(!isEligibleViolationPair(0x1000, 8, 0x1008, 8, 3));  // 4B offset
    // Same shifted chunk but no real byte overlap: rejected as a different
    // address.
    assert(!isEligibleViolationPair(0x1009, 8, 0x1000, 8, 3));

    // First eligible event.
    assert(shouldInject(1, 0, 0, 1));
    // Selected ordinal only.
    assert(!shouldInject(1, 3, 0, 1));
    assert(shouldInject(3, 3, 0, 1));
    // maxFaults bounds.
    assert(!shouldInject(3, 3, 1, 1));

    std::printf("MD04 same-address-8B violation-suppression rules: PASS\n");
    return 0;
}
