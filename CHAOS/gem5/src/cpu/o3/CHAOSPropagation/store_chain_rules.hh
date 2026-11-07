#ifndef __CPU_O3_STORE_CHAIN_RULES_HH__
#define __CPU_O3_STORE_CHAIN_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_store_chain
{

// LSU v3.2.4 review fix. A load may join a faulted store's chain only when:
//   - it is younger than the store in program order (a pre-store load cannot
//     read the store's value),
//   - the store's actual cache write has already happened,
//   - the response is observed at/after that write tick, and
//   - no different store has overwritten the byte.
// This prevents address-overlap-only attribution (a later load reading an
// overwriting store, or an in-flight older load) from being counted as a
// fault propagation.
inline bool
mayConsumeFaultByte(uint64_t load_seq, uint64_t store_seq, bool overwritten,
                    uint64_t written_tick, uint64_t now)
{
    if (overwritten)
        return false;
    if (written_tick == 0)
        return false;
    if (load_seq <= store_seq)
        return false;
    if (now < written_tick)
        return false;
    return true;
}

} // namespace chaos_store_chain
} // namespace gem5

#endif // __CPU_O3_STORE_CHAIN_RULES_HH__
