#ifndef __CPU_O3_LP01_BYTEWISE_HH__
#define __CPU_O3_LP01_BYTEWISE_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_lp01
{

// LP01-CFG01 (Excel v3.2.1 Sheet 3/4/5): the modeled fault is byte lane 0,
// bit 3 of the load-response payload. The model is a single-bit data fault:
// for a response of size N >= 1 exactly data[0] is XORed with the low byte
// of `mask`; bytes 1..N-1 are untouched for every N, including 9/12/16.
// Mask bits 8..63 are outside the modeled lane and ignored. size == 0 and
// mask == 0 are no-ops. This is byte-wise and bounded: it never writes past
// `size` (the v3.2.4 uint64_t* defect).
inline bool
corruptByte0(uint8_t *data, unsigned size, uint64_t mask)
{
    if (!data || size == 0)
        return false;
    const uint8_t m = (uint8_t)(mask & 0xffu);
    if (m == 0)
        return false;
    data[0] ^= m;
    return true;
}

// 1-based ordinal of the eligible event that is being injected. The injector
// starts with `initial_skip` (ordinal - 1) and decrements `remaining_skip`
// for every earlier eligible event; when it injects, the ordinal is
// initial_skip - remaining_skip + 1.
inline uint64_t
eligibleOrdinal(uint64_t initial_skip, uint64_t remaining_skip)
{
    return initial_skip - remaining_skip + 1;
}

} // namespace chaos_lp01
} // namespace gem5

#endif // __CPU_O3_LP01_BYTEWISE_HH__
