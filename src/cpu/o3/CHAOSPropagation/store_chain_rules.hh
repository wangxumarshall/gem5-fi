#ifndef __CPU_O3_STORE_CHAIN_RULES_HH__
#define __CPU_O3_STORE_CHAIN_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_store_chain
{

// LSU v3.2.5. A load may join a faulted store's chain only when:
//   - it is younger than the store in program order (a pre-store load cannot
//     read the store's value),
//   - the store's actual cache write has already happened,
//   - the load's own REQUEST was issued at/after that write (a request that
//     left the LSQ before the write can only have observed the old byte —
//     response time alone is not evidence of causality), and
//   - no different store has overwritten the byte.
// The v3.2.4 rule compared the RESPONSE tick, which admitted loads already in
// flight when the store wrote; the DA04 R04 chain is exactly that case
// (R04: request 2286900 < store write 17042410 < response 17889795).
inline bool
mayConsumeFaultByte(uint64_t load_seq, uint64_t store_seq, bool overwritten,
                    uint64_t written_tick, uint64_t load_request_tick)
{
    if (overwritten)
        return false;
    if (written_tick == 0)
        return false;
    if (load_seq <= store_seq)
        return false;
    if (load_request_tick < written_tick)
        return false;
    return true;
}

} // namespace chaos_store_chain
} // namespace gem5

#endif // __CPU_O3_STORE_CHAIN_RULES_HH__
