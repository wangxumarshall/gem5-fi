#ifndef __CPU_O3_CHAOS_VEC_STUCK_HH__
#define __CPU_O3_CHAOS_VEC_STUCK_HH__

// FR03 pure model: a permanent stuck-at defect on one Vec physical cell.
//
// This header depends only on the C++ standard library so the semantics can be
// unit-tested with the host compiler (tests/unit/chaos_vec_stuck_test.cc and
// tests/unit/chaos_physreg_generation_test.cc), independent of the gem5
// build. The container side (PhysRegFile) uses it to force the stuck bits on
// EVERY write to the target physical cell.
//
// Semantics (workbook table 3 FR03 + table 7/9 FR03)
// --------------------------------------------------
//  * SA0 (polarity=0): target bits are forced to 0 (`value &= ~mask`).
//  * SA1 (polarity=1): target bits are forced to 1 (`value |= mask`).
//    XOR is NOT a stuck-at model and must never be used here.
//  * The PERMANENT KEY is reg_class + phys_index + lane + bit/mask + polarity.
//    The defect lives on the physical cell: it survives free/realloc, rename
//    reuse, multiple writes and reads ("永久缺陷跨物理槽复用和多次读写暴露").
//  * `generation` is allocation/exposure IDENTITY ONLY. It is recorded on
//    events so each reallocation's application/read chain is explicit; it is
//    NOT a matching condition and NEVER clears the defect. Only an explicit
//    clear()/reset (end of run) removes it.
//  * A generation change restarts that generation's exposure chain
//    (exposure_id starts again at 1); producer/consumer edges from an older
//    generation must not be joined to the new generation.

#include <cstdint>
#include <cstring>
#include <vector>

namespace gem5
{
namespace chaos_vec_stuck
{

struct Target
{
    int reg_class = -1;        // RegClassType value (VecRegClass in FR03)
    int phys_index = -1;       // physical register index within the class
    uint32_t generation = 0;   // generation captured at install time
                               // (provenance only — NOT a match key)
    int lane_width = 32;       // 8/16/32/64
    int lane_offset = 0;       // lane index inside the 128-bit register
    int bit_in_lane = 0;       // first set bit inside the lane
    uint64_t lane_mask = 0;    // mask relative to the lane
    uint8_t polarity = 0;      // 0 = stuck-at-zero, 1 = stuck-at-one
    bool valid = false;

    // The permanent physical-cell key. `generation` is deliberately absent:
    // the workbook requires the defect to persist across physical-slot reuse.
    bool matches(int cls, int idx) const
    {
        return valid && cls == reg_class && idx == phys_index;
    }

    // Backwards-compatible spelling used by older call sites/tests. The
    // generation argument is accepted only for provenance call sites and is
    // NOT part of the match.
    bool applies(int cls, int idx, uint32_t /*gen*/) const
    {
        return matches(cls, idx);
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

// ---------------------------------------------------------------------------
// Per-physical-slot logical generation ledger (the host-testable mirror of
// PhysRegFile::flat_generation).
//
// Numeric source: PhysRegFile's constructor initialises every slot to 0
// (CHAOS/gem5/src/cpu/o3/regfile.cc:88). UnifiedFreeList::addReg() calls
// noteRegFreed() exactly when a slot is released (including the initial free
// list population), so the value increments at every free/release. It is
// descriptive identity only; it is never compared by the permanent key.
// ---------------------------------------------------------------------------
class GenerationLedger
{
  public:
    GenerationLedger() = default;
    explicit GenerationLedger(size_t slots) : generations_(slots, 0) {}

    void resize(size_t slots) { generations_.assign(slots, 0); }
    size_t size() const { return generations_.size(); }

    uint32_t generationOf(int flat) const
    {
        if (flat < 0 || (size_t)flat >= generations_.size())
            return 0;
        return generations_[(size_t)flat];
    }

    // A release starts a new logical generation for that physical slot.
    // Returns the new generation (0 for an out-of-range slot).
    uint32_t noteFreed(int flat)
    {
        if (flat < 0 || (size_t)flat >= generations_.size())
            return 0;
        return ++generations_[(size_t)flat];
    }

    // End-of-run reset: generations restart at 0. Never called on squash.
    void reset() { generations_.assign(generations_.size(), 0); }

  private:
    std::vector<uint32_t> generations_;
};

// ---------------------------------------------------------------------------
// PermanentCell: the permanent-defect state machine for one Vec physical cell.
//
// `write*()` is called for EVERY write to the target cell. The cell applies
// the stuck mask whenever reg_class+phys_index match — regardless of
// `generation`. A generation change only resets the per-generation exposure
// identity (exposure_id restarts at 1) and records a generation-change
// transition; it never disarms the defect nor joins the old generation's
// producer/consumer edges to the new one.
// ---------------------------------------------------------------------------
struct WriteResult
{
    bool matched = false;             // reg_class + phys_index matched
    bool applied = false;             // stuck mask was forced (always for a
                                      // matching permanent cell)
    bool activated = false;           // correct lane differed before forcing
    bool generation_changed = false;  // this write observed a new generation
    uint32_t generation = 0;          // generation of this write
    uint32_t old_generation = 0;      // previous generation (if changed)
    uint64_t generation_exposure_id = 0;  // 1-based, resets per generation
    uint64_t exposure_total = 0;      // all generations
    uint64_t activated_total = 0;
    uint64_t generation_changes = 0;
    uint64_t before = 0;              // lane value before forcing
    uint64_t after = 0;               // lane value after forcing
};

class PermanentCell
{
  public:
    // Install on reg_class + phys_index. Returns false for invalid
    // geometry/mask. `generation` is recorded as provenance only.
    bool install(int reg_class, int phys_index, int lane_width,
                 int lane_offset, uint64_t lane_mask, uint8_t polarity,
                 uint32_t generation)
    {
        target_ = Target();
        if (reg_class < 0 || phys_index < 0)
            return false;
        if (lane_width != 8 && lane_width != 16 && lane_width != 32 &&
            lane_width != 64)
            return false;
        const int lanes = 128 / lane_width;
        if (lane_offset < 0 || lane_offset >= lanes)
            return false;
        if (lane_mask == 0)
            return false;
        if (lane_width < 64 && (lane_mask >> lane_width) != 0)
            return false;
        target_.reg_class = reg_class;
        target_.phys_index = phys_index;
        target_.generation = generation;
        target_.lane_width = lane_width;
        target_.lane_offset = lane_offset;
        target_.bit_in_lane = __builtin_ctzll(lane_mask);
        target_.lane_mask = lane_mask;
        target_.polarity = polarity ? 1 : 0;
        target_.valid = true;
        generation_ = generation;
        have_generation_ = true;
        generation_exposures_ = 0;
        total_exposures_ = 0;
        activated_total_ = 0;
        generation_changes_ = 0;
        return true;
    }

    // End of run / explicit reset: remove the defect. Squash must NOT call
    // this (the defect survives squash/replay).
    void clear()
    {
        target_ = Target();
        generation_ = 0;
        have_generation_ = false;
        generation_exposures_ = 0;
        total_exposures_ = 0;
        activated_total_ = 0;
        generation_changes_ = 0;
    }

    bool active() const { return target_.valid; }
    const Target &target() const { return target_; }
    bool matches(int cls, int idx) const { return target_.matches(cls, idx); }
    uint32_t generation() const { return generation_; }
    uint64_t exposuresTotal() const { return total_exposures_; }
    uint64_t activatedTotal() const { return activated_total_; }
    uint64_t generationChanges() const { return generation_changes_; }

    // Observe a write whose lane value is supplied directly. `generation` is
    // the CURRENT allocation generation of the cell (from the container's
    // ledger), never a match key.
    WriteResult writeLaneValue(uint64_t correct, int cls, int idx,
                               uint32_t generation)
    {
        WriteResult r = beginWrite(cls, idx, generation);
        if (!r.matched)
            return r;
        const int lw = target_.lane_width;
        const uint64_t width_mask = lw == 64 ? ~0ULL
                                             : ((1ULL << lw) - 1ULL);
        r.before = correct & width_mask;
        r.after = forceLane(r.before, target_.lane_mask, target_.polarity);
        r.applied = true;
        r.activated = !satisfied(r.before, target_.lane_mask,
                                 target_.polarity);
        if (r.activated)
            ++activated_total_;
        return r;
    }

    // Observe a write to a 16-byte vector register image. Only the target
    // lane is touched; every other lane/bit stays byte-identical.
    WriteResult writeVec16(uint8_t *vec16, int cls, int idx,
                           uint32_t generation)
    {
        WriteResult r = beginWrite(cls, idx, generation);
        if (!r.matched)
            return r;
        if (vec16 == nullptr)
            return r;
        const int lane_bytes = target_.lane_width / 8;
        const int base = target_.lane_offset * lane_bytes;
        r.before = 0;
        for (int b = 0; b < lane_bytes; ++b)
            r.before |= (uint64_t)vec16[base + b] << (8 * b);
        r.applied = applyToVec16(vec16, target_.lane_width,
                                 target_.lane_offset, target_.lane_mask,
                                 target_.polarity);
        r.after = 0;
        for (int b = 0; b < lane_bytes; ++b)
            r.after |= (uint64_t)vec16[base + b] << (8 * b);
        r.activated = !satisfied(r.before, target_.lane_mask,
                                 target_.polarity);
        if (r.activated)
            ++activated_total_;
        return r;
    }

  private:
    WriteResult beginWrite(int cls, int idx, uint32_t generation)
    {
        WriteResult r;
        r.generation = generation;
        if (!target_.matches(cls, idx))
            return r;
        r.matched = true;
        if (!have_generation_) {
            generation_ = generation;
            have_generation_ = true;
        } else if (generation != generation_) {
            r.generation_changed = true;
            r.old_generation = generation_;
            generation_ = generation;
            generation_exposures_ = 0;  // chain restarts for the new gen
            ++generation_changes_;
        }
        r.generation_exposure_id = ++generation_exposures_;
        r.exposure_total = ++total_exposures_;
        r.activated_total = activated_total_;
        r.generation_changes = generation_changes_;
        return r;
    }

    Target target_;
    uint32_t generation_ = 0;
    bool have_generation_ = false;
    uint64_t generation_exposures_ = 0;
    uint64_t total_exposures_ = 0;
    uint64_t activated_total_ = 0;
    uint64_t generation_changes_ = 0;
};

} // namespace chaos_vec_stuck
} // namespace gem5

#endif // __CPU_O3_CHAOS_VEC_STUCK_HH__
