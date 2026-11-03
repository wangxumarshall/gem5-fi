#ifndef __CPU_O3_CHAOS_VEC_STUCK_HH__
#define __CPU_O3_CHAOS_VEC_STUCK_HH__

// FR03 pure model: a permanent stuck-at defect on one Vec physical register.
//
// This header depends only on the C++ standard library so the semantics can be
// unit-tested with the host compiler (tests/unit/chaos_vec_stuck_test.cc),
// independent of the gem5 build. The container side (PhysRegFile) uses it to
// force the stuck bits on EVERY write to the target physical cell.
//
// Semantics
// ---------
//  * SA0 (polarity=0): target bits are forced to 0 (`value &= ~mask`).
//  * SA1 (polarity=1): target bits are forced to 1 (`value |= mask`).
//    XOR is NOT a stuck-at model and must never be used here.
//  * The target is keyed by reg_class + phys_index + generation + lane + bit +
//    polarity. A new generation (the slot was freed and reallocated) is a
//    different logical value: the old defect no longer applies unless the
//    workbook explicitly asks for a physical cell spanning generations.
//  * Only the selected lane's mask bits may change; every other bit of the
//    128-bit register stays byte-identical.

#include <cstdint>
#include <cstring>

namespace gem5
{
namespace chaos_vec_stuck
{

struct Target
{
    int reg_class = -1;        // RegClassType value (VecRegClass in FR03)
    int phys_index = -1;       // physical register index within the class
    uint32_t generation = 0;   // generation captured at install time
    int lane_width = 32;       // 8/16/32/64
    int lane_offset = 0;       // lane index inside the 128-bit register
    int bit_in_lane = 0;       // first set bit inside the lane
    uint64_t lane_mask = 0;    // mask relative to the lane
    uint8_t polarity = 0;      // 0 = stuck-at-zero, 1 = stuck-at-one
    bool valid = false;

    bool applies(int cls, int idx, uint32_t gen) const
    {
        return valid && cls == reg_class && idx == phys_index &&
               gen == generation;
    }
};

// Force one lane value. Idempotent: applying the same stuck target twice yields
// the same value.
inline uint64_t
forceLane(uint64_t value, uint64_t lane_mask, uint8_t polarity)
{
    return polarity ? (value | lane_mask) : (value & ~lane_mask);
}

// True iff the target bits already equal the stuck polarity. This is the
// "exposed but not activated" case: the correct value did not differ.
inline bool
satisfied(uint64_t value, uint64_t lane_mask, uint8_t polarity)
{
    return polarity ? ((value & lane_mask) == lane_mask)
                    : ((value & lane_mask) == 0);
}

// Build a lane mask from a bit index. Returns false for an invalid lane/bit.
inline bool
buildLaneMask(int lane_width, int bit_in_lane, uint64_t &lane_mask)
{
    if (lane_width != 8 && lane_width != 16 && lane_width != 32 &&
        lane_width != 64)
        return false;
    if (bit_in_lane < 0 || bit_in_lane >= lane_width)
        return false;
    lane_mask = (uint64_t)1 << bit_in_lane;
    return true;
}

// Apply a target to a 16-byte little-endian vector register image. Only the
// target lane is touched; `mask` must fit `lane_width`.
inline bool
applyToVec16(uint8_t *vec16, int lane_width, int lane_offset,
             uint64_t lane_mask, uint8_t polarity)
{
    if (vec16 == nullptr)
        return false;
    if (lane_width != 8 && lane_width != 16 && lane_width != 32 &&
        lane_width != 64)
        return false;
    const int lanes = 128 / lane_width;
    if (lane_offset < 0 || lane_offset >= lanes)
        return false;
    if (lane_width < 64 && (lane_mask >> lane_width) != 0)
        return false;
    const int lane_bytes = lane_width / 8;
    const int base = lane_offset * lane_bytes;
    uint64_t value = 0;
    for (int b = 0; b < lane_bytes; ++b)
        value |= (uint64_t)vec16[base + b] << (8 * b);
    value = forceLane(value, lane_mask, polarity);
    for (int b = 0; b < lane_bytes; ++b)
        vec16[base + b] = (uint8_t)((value >> (8 * b)) & 0xff);
    return true;
}

// True iff only the masked bits differ between two 16-byte images.
inline bool
onlyMaskedBitsDiffer(const uint8_t *before16, const uint8_t *after16,
                     int lane_width, int lane_offset, uint64_t lane_mask)
{
    if (before16 == nullptr || after16 == nullptr)
        return false;
    const int lane_bytes = lane_width / 8;
    const int base = lane_offset * lane_bytes;
    for (int i = 0; i < 16; ++i) {
        const uint8_t diff = before16[i] ^ after16[i];
        if (diff == 0)
            continue;
        if (i < base || i >= base + lane_bytes)
            return false;
        const int bit_base = (i - base) * 8;
        for (int b = 0; b < 8; ++b) {
            if ((diff >> b) & 1) {
                const int rel = bit_base + b;
                if (rel >= 64 || ((lane_mask >> rel) & 1) == 0)
                    return false;
            }
        }
    }
    return true;
}

} // namespace chaos_vec_stuck
} // namespace gem5

#endif // __CPU_O3_CHAOS_VEC_STUCK_HH__
