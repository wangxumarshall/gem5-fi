#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSMD04/md04_rules.hh"

using namespace gem5::chaos_md04;

int
main()
{
    // Option A: same address, both 8 bytes.
    assert(isSameAddress8B(0x1000, 8, 0x1000, 8));
    assert(isSameAddress8B(0x1000, 16, 0x1000, 8));   // LDP covers the store
    assert(!isSameAddress8B(0x1000, 8, 0x1008, 8));
    assert(!isSameAddress8B(0x1000, 4, 0x1000, 8));
    assert(!isSameAddress8B(0x1000, 8, 0x1000, 4));

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
