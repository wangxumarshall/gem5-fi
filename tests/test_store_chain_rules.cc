#include <cassert>
#include <cstdint>
#include <cstdio>

#include "cpu/o3/CHAOSPropagation/store_chain_rules.hh"

using namespace gem5::chaos_store_chain;

int
main()
{
    // Request issued after the actual write: consumes.
    assert(mayConsumeFaultByte(300, 250, false, 1000, 1100));
    // Request issued BEFORE the write, even if the response arrives after:
    // NOT causal (the v3.2.4 response-time rule admitted this case).
    assert(!mayConsumeFaultByte(300, 250, false, 1000, 900));
    // Older load (pre-store program order): never consumes.
    assert(!mayConsumeFaultByte(200, 250, false, 1000, 1100));
    // Load equal to the store itself: not a consumer.
    assert(!mayConsumeFaultByte(250, 250, false, 1000, 1100));
    // The store has not reached the cache yet: the load cannot see it.
    assert(!mayConsumeFaultByte(300, 250, false, 0, 1100));
    // A later store overwrote the byte: attribution stops.
    assert(!mayConsumeFaultByte(300, 250, true, 1000, 1100));

    std::printf("store-chain attribution (request-time) unit test: PASS\n");
    return 0;
}
