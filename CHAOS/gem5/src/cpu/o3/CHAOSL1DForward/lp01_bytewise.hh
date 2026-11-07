#ifndef __CPU_O3_LP01_BYTEWISE_HH__
#define __CPU_O3_LP01_BYTEWISE_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_lp01
{

// LP01 (LSU v3.2.4): corrupt a load-response payload byte by byte. The old
// path cast the packet payload to uint64_t* and always XORed one 8-byte word,
// which wrote past the payload for size<8 (undefined behaviour / heap
// corruption). The mask bytes repeat every 8 bytes, so payloads >= 8 keep the
// previous two-word behaviour exactly and smaller payloads stay in bounds.
inline void
xorMask(uint8_t *data, unsigned size, uint64_t mask)
{
    for (unsigned i = 0; i < size; ++i) {
        data[i] ^= (uint8_t)(mask >> (8 * (i % 8)));
    }
}

} // namespace chaos_lp01
} // namespace gem5

#endif // __CPU_O3_LP01_BYTEWISE_HH__
