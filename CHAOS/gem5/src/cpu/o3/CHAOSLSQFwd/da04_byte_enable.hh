#ifndef __CPU_O3_DA04_BYTE_ENABLE_HH__
#define __CPU_O3_DA04_BYTE_ENABLE_HH__

#include <cstdint>
#include <vector>

namespace gem5
{
namespace chaos_da04
{

// DA04 (LSU v3.2.4): the modelled mask is the 4-bit byte-enable of a 32-bit
// store. gem5 stores it as std::vector<bool>, one entry per byte:
//   index 0 = lowest-addressed byte (packet data[0], AArch64 LE bits [7:0])
//   index 3 = highest-addressed byte (bits [31:24])
// 0xF = {true,true,true,true}; clearing bit0 yields 0xE =
// {false,true,true,true}. No Load and no non-4-byte access is eligible.
static constexpr unsigned kMaskWidth = 4;

inline bool
eligible(unsigned size, const std::vector<bool> &be)
{
    if (size != kMaskWidth || be.size() != kMaskWidth)
        return false;
    for (bool b : be) {
        if (!b)
            return false;
    }
    return true;
}

inline uint64_t
maskOf(const std::vector<bool> &be)
{
    uint64_t m = 0;
    for (unsigned i = 0; i < be.size() && i < 64; ++i) {
        if (be[i])
            m |= (uint64_t)1 << i;
    }
    return m;
}

inline bool
clearLane0(std::vector<bool> &be)
{
    if (be.empty() || !be[0])
        return false;
    be[0] = false;
    return true;
}

} // namespace chaos_da04
} // namespace gem5

#endif // __CPU_O3_DA04_BYTE_ENABLE_HH__
