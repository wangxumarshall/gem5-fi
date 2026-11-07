#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSPropagation/store_chain_rules.hh"

using namespace gem5::chaos_store_chain;

int
main()
{
    // A younger load after the actual write, not overwritten: consumes.
    assert(mayConsumeFaultByte(300, 250, false, 1000, 1100));
    // Older load (pre-store program order): never consumes.
    assert(!mayConsumeFaultByte(200, 250, false, 1000, 1100));
    // Load equal to the store itself: not a consumer.
    assert(!mayConsumeFaultByte(250, 250, false, 1000, 1100));
    // The store has not reached the cache yet: the load cannot see it.
    assert(!mayConsumeFaultByte(300, 250, false, 0, 1100));
    // Response before the write tick: cannot see it.
    assert(!mayConsumeFaultByte(300, 250, false, 1200, 1100));
    // A later store overwrote the byte: attribution stops.
    assert(!mayConsumeFaultByte(300, 250, true, 1000, 1100));

    std::printf("store-chain attribution unit test: PASS\n");
    return 0;
}
