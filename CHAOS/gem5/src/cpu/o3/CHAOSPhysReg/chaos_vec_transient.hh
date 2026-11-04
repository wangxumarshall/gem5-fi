#ifndef __CPU_O3_CHAOS_VEC_TRANSIENT_HH__
#define __CPU_O3_CHAOS_VEC_TRANSIENT_HH__

// FR01 / FR02 pure model: a ONE-SHOT transient bit flip on a Vec physical
// cell. This header depends only on the C++ standard library so the semantics
// can be host-unit-tested with the host g++ (tests/unit/
// chaos_vec_transient_test.cc), independent of the gem5 build.
//
// Semantics (workbook tables 3/7/9 FR01 + FR02)
// ---------------------------------------------
//  * FR01 = flip exactly ONE bit inside the target 128-bit Vec value.
//  * FR02 = flip exactly TWO DIFFERENT bits. Collapsing the two draws into a
//    single bit is a hard error (fail closed), never a silent 1-bit fault.
//  * The fault is TRANSIENT: it is applied by one read-modify-write of the
//    physical cell and is never armed on the write path. Any later real write
//    to the cell replaces the value; the injected bits are gone and must not
//    be re-applied by a read.
//  * The fault domain is the architectural 128-bit Vec value (AArch64 NEON /
//    scalar FP lower 128 bits), NOT the 256-byte SVE backing store. Every bit
//    identity is reported as (flat bit, lane, bit-in-lane, 32-bit field).
//  * Non-target lanes/bits/bytes are byte-identical before and after.
//  * Geometry (FR02-a/b/c/d) is selected explicitly by the caller:
//      -a same-lane adjacent
//      -b same-lane non-adjacent
//      -c cross-lane
//      -d cross-field (different 32-bit fields)
//    A geometry whose domain cannot hold `count` distinct bits fails closed.

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <numeric>
#include <random>
#include <string>
#include <vector>

namespace gem5
{
namespace chaos_vec_transient
{

constexpr int kVecBits = 128;
constexpr int kVecBytes = kVecBits / 8;
constexpr int kFieldBits = 32;

enum class Geometry
{
    Any,                  // any distinct bits in the 128-bit value
    SameLane,             // all bits inside one lane
    SameLaneAdjacent,     // consecutive bits inside one lane (FR02-a)
    SameLaneNonAdjacent,  // same lane, no two adjacent (FR02-b)
    CrossLane,            // at least two different lanes (FR02-c)
    CrossField            // at least two different 32-bit fields (FR02-d)
};

struct BitId
{
    int flat = -1;         // absolute bit position in the 128-bit value
    int lane = -1;         // lane index under the selected lane width
    int bit_in_lane = -1;  // bit offset inside that lane
    int field = -1;        // flat / 32
};

struct Selection
{
    bool ok = false;
    std::string reason = "not_selected";
    Geometry geometry = Geometry::Any;
    int lane_width = 32;
    int lane_offset = -1;      // lane of the first (lowest flat) bit
    std::vector<BitId> bits;   // sorted by flat position, all distinct
    uint64_t mask_lo = 0;      // absolute bits 0..63
    uint64_t mask_hi = 0;      // absolute bits 64..127
};

inline bool
validLaneWidth(int lane_width)
{
    return lane_width == 8 || lane_width == 16 || lane_width == 32 ||
           lane_width == 64;
}

inline int
laneCount(int lane_width)
{
    return validLaneWidth(lane_width) ? kVecBits / lane_width : 0;
}

inline int
laneOf(int flat, int lane_width)
{
    return validLaneWidth(lane_width) ? flat / lane_width : -1;
}

inline int
bitInLane(int flat, int lane_width)
{
    return validLaneWidth(lane_width) ? flat % lane_width : -1;
}

inline int
fieldOf(int flat)
{
    return flat / kFieldBits;
}

inline int
popcount128(uint64_t lo, uint64_t hi)
{
    return __builtin_popcountll(lo) + __builtin_popcountll(hi);
}

// Recognise an FR02 submodel in a semantic role (e.g. "FR02-c",
// "cross_lane", "same_lane_adjacent"). Returns false for unrecognised roles,
// so the caller keeps its default geometry instead of guessing.
inline bool
parseGeometry(const std::string &role, int count, Geometry &out)
{
    if (count < 2)
        return false;
    std::string r;
    r.reserve(role.size());
    for (char c : role) {
        if (c >= 'A' && c <= 'Z')
            r.push_back((char)(c - 'A' + 'a'));
        else
            r.push_back(c);
    }
    auto has = [&r](const char *s) {
        return r.find(s) != std::string::npos;
    };
    if (has("cross_lane") || has("crosslane") || has("fr02-c") ||
        (has("-c") && has("fr02"))) {
        out = Geometry::CrossLane;
        return true;
    }
    if (has("cross_field") || has("crossfield") || has("exp_mant") ||
        has("exp+mant") || has("fr02-d") || (has("-d") && has("fr02"))) {
        out = Geometry::CrossField;
        return true;
    }
    if (has("non_adjacent") || has("nonadjacent") || has("non-adjacent") ||
        has("fr02-b") || (has("-b") && has("fr02"))) {
        out = Geometry::SameLaneNonAdjacent;
        return true;
    }
    if (has("adjacent") || has("fr02-a") || (has("-a") && has("fr02"))) {
        out = Geometry::SameLaneAdjacent;
        return true;
    }
    return false;
}

// Sample `count` DISTINCT integers from [0, domain_bits). Returns false
// (fail closed) if the domain cannot supply that many distinct values.
inline bool
chooseDistinct(std::mt19937 &rng, int domain_bits, int count,
               std::vector<int> &out)
{
    out.clear();
    if (count <= 0 || domain_bits <= 0 || count > domain_bits)
        return false;
    std::vector<int> pool((size_t)domain_bits);
    std::iota(pool.begin(), pool.end(), 0);
    for (int i = 0; i < count; ++i) {
        std::uniform_int_distribution<int> pick(i, domain_bits - 1);
        const int j = pick(rng);
        std::swap(pool[(size_t)i], pool[(size_t)j]);
        out.push_back(pool[(size_t)i]);
    }
    std::sort(out.begin(), out.end());
    return true;
}

inline Selection
fail(const char *reason)
{
    Selection s;
    s.ok = false;
    s.reason = reason;
    return s;
}

inline bool
bitsWithinLane(const std::vector<int> &flats, int lane_width, int lane)
{
    for (int f : flats)
        if (laneOf(f, lane_width) != lane)
            return false;
    return true;
}

inline bool
distinctLaneCount(const std::vector<int> &flats, int lane_width,
                  int &distinct)
{
    std::vector<int> lanes;
    for (int f : flats)
        lanes.push_back(laneOf(f, lane_width));
    std::sort(lanes.begin(), lanes.end());
    lanes.erase(std::unique(lanes.begin(), lanes.end()), lanes.end());
    distinct = (int)lanes.size();
    return true;
}

inline bool
distinctFieldCount(const std::vector<int> &flats, int &distinct)
{
    std::vector<int> fields;
    for (int f : flats)
        fields.push_back(fieldOf(f));
    std::sort(fields.begin(), fields.end());
    fields.erase(std::unique(fields.begin(), fields.end()), fields.end());
    distinct = (int)fields.size();
    return true;
}

inline bool
isAdjacentRun(const std::vector<int> &flats, int lane_width, int lane)
{
    if (flats.empty() || !bitsWithinLane(flats, lane_width, lane))
        return false;
    for (size_t i = 1; i < flats.size(); ++i)
        if (flats[i] != flats[i - 1] + 1)
            return false;
    return true;
}

inline bool
hasNoAdjacentPair(const std::vector<int> &flats, int lane_width, int lane)
{
    if (!bitsWithinLane(flats, lane_width, lane))
        return false;
    for (size_t i = 1; i < flats.size(); ++i)
        if (flats[i] - flats[i - 1] < 2)
            return false;
    return true;
}

// Build a Selection from explicit bit positions (already absolute in the
// 128-bit value). Returns false, with a reason, when the requested count or
// geometry does not match the mask. This is the "no random collision" guard:
// a two-bit FR02 whose mask has only one set bit is rejected here.
inline Selection
selectionFromMask(int lane_width, int lane_offset, int count,
                  Geometry geometry, uint64_t mask_lo, uint64_t mask_hi)
{
    if (!validLaneWidth(lane_width))
        return fail("invalid_lane_width");
    const int lanes = laneCount(lane_width);
    if (lane_offset < -1 || lane_offset >= lanes)
        return fail("lane_offset_out_of_range");
    const int requested = count;
    if (requested <= 0 || requested > kVecBits)
        return fail("bit_count_out_of_range");
    const int got = popcount128(mask_lo, mask_hi);
    if (got != requested)
        return fail("mask_popcount_mismatch");

    std::vector<int> flats;
    for (int b = 0; b < 64; ++b)
        if ((mask_lo >> b) & 1ULL)
            flats.push_back(b);
    for (int b = 0; b < 64; ++b)
        if ((mask_hi >> b) & 1ULL)
            flats.push_back(64 + b);
    // popcount already validated, but keep the identity invariant explicit.
    std::sort(flats.begin(), flats.end());
    for (size_t i = 1; i < flats.size(); ++i)
        if (flats[i] == flats[i - 1])
            return fail("duplicate_bit");

    const int first_lane = laneOf(flats.front(), lane_width);
    switch (geometry) {
      case Geometry::Any:
        break;
      case Geometry::SameLane:
        if (!bitsWithinLane(flats, lane_width, first_lane))
            return fail("bits_not_in_one_lane");
        if (lane_offset >= 0 && first_lane != lane_offset)
            return fail("written_lane_mismatch");
        break;
      case Geometry::SameLaneAdjacent:
        if (requested < 2)
            return fail("adjacent_needs_two_bits");
        if (!isAdjacentRun(flats, lane_width, first_lane))
            return fail("bits_not_adjacent_in_lane");
        if (lane_offset >= 0 && first_lane != lane_offset)
            return fail("written_lane_mismatch");
        break;
      case Geometry::SameLaneNonAdjacent:
        if (requested < 2)
            return fail("non_adjacent_needs_two_bits");
        if (!hasNoAdjacentPair(flats, lane_width, first_lane))
            return fail("bits_adjacent_or_out_of_lane");
        if (lane_offset >= 0 && first_lane != lane_offset)
            return fail("written_lane_mismatch");
        break;
      case Geometry::CrossLane: {
        if (requested < 2)
            return fail("cross_lane_needs_two_bits");
        int distinct_lanes = 0;
        distinctLaneCount(flats, lane_width, distinct_lanes);
        if (distinct_lanes < 2)
            return fail("mask_is_single_lane");
        int first = laneOf(flats.front(), lane_width);
        (void)first;
        if (lane_offset >= 0) {
            bool seen = false;
            for (int f : flats)
                if (laneOf(f, lane_width) == lane_offset)
                    seen = true;
            if (!seen)
                return fail("written_lane_not_in_mask");
        }
        break;
      }
      case Geometry::CrossField: {
        if (requested < 2)
            return fail("cross_field_needs_two_bits");
        int distinct_fields = 0;
        distinctFieldCount(flats, distinct_fields);
        if (distinct_fields < 2)
            return fail("mask_is_single_field");
        if (lane_offset >= 0) {
            if (lane_width >= 64) {
                // A 64-bit (or wider) directed lane contains both 32-bit
                // fields; exp+mant must stay inside that architectural lane.
                if (!bitsWithinLane(flats, lane_width, lane_offset))
                    return fail("bits_not_in_directed_lane");
            } else {
                // Narrow lanes live inside one 32-bit field; cross-field must
                // still involve the directed lane's field.
                const int want = fieldOf(lane_offset * lane_width);
                bool seen = false;
                for (int f : flats)
                    if (fieldOf(f) == want)
                        seen = true;
                if (!seen)
                    return fail("directed_field_not_in_mask");
            }
        }
        break;
      }
    }

    Selection s;
    s.ok = true;
    s.reason = "ok";
    s.geometry = geometry;
    s.lane_width = lane_width;
    s.lane_offset = first_lane;
    for (int f : flats) {
        BitId id;
        id.flat = f;
        id.lane = laneOf(f, lane_width);
        id.bit_in_lane = bitInLane(f, lane_width);
        id.field = fieldOf(f);
        s.bits.push_back(id);
        if (f < 64)
            s.mask_lo |= (1ULL << f);
        else
            s.mask_hi |= (1ULL << (f - 64));
    }
    return s;
}

// Randomly select `count` distinct bits honouring the requested geometry.
// `semantic_role` may name an FR02 submodel; otherwise the caller's geometry
// (normally Any, or SameLane when a lane is directed) is used.
inline Selection
select(std::mt19937 &rng, int lane_width, int lane_offset, int count,
       Geometry geometry, const std::string &semantic_role = "")
{
    if (!validLaneWidth(lane_width))
        return fail("invalid_lane_width");
    const int lanes = laneCount(lane_width);
    if (lane_offset < -1 || lane_offset >= lanes)
        return fail("lane_offset_out_of_range");
    if (count <= 0 || count > kVecBits)
        return fail("bit_count_out_of_range");

    Geometry geom = geometry;
    Geometry hinted;
    if (parseGeometry(semantic_role, count, hinted))
        geom = hinted;

    const bool directed = lane_offset >= 0;
    int lane = directed ? lane_offset : -1;

    // Geometry that needs a lane but has none: pick one.
    if (geom == Geometry::SameLane || geom == Geometry::SameLaneAdjacent ||
        geom == Geometry::SameLaneNonAdjacent) {
        if (count > lane_width)
            return fail("insufficient_lane_width");
        if (lane < 0)
            lane = std::uniform_int_distribution<int>(0, lanes - 1)(rng);
        if (geom == Geometry::SameLaneAdjacent && count > lane_width)
            return fail("insufficient_lane_width");
        if (geom == Geometry::SameLaneNonAdjacent && count > lane_width)
            return fail("insufficient_lane_width");
    }

    if (geom == Geometry::CrossLane) {
        if (lanes < 2 || count < 2)
            return fail("insufficient_lanes");
    }
    if (geom == Geometry::CrossField) {
        const int fields = kVecBits / kFieldBits;
        if (fields < 2 || count < 2)
            return fail("insufficient_fields");
    }

    std::vector<int> flats;
    const int base = (lane >= 0 && (geom == Geometry::SameLane ||
                                    geom == Geometry::SameLaneAdjacent ||
                                    geom == Geometry::SameLaneNonAdjacent))
                         ? lane * lane_width : 0;
    const int domain = (base > 0 || geom == Geometry::SameLane ||
                        geom == Geometry::SameLaneAdjacent ||
                        geom == Geometry::SameLaneNonAdjacent)
                           ? lane_width : kVecBits;

    switch (geom) {
      case Geometry::Any:
        if (!chooseDistinct(rng, kVecBits, count, flats))
            return fail("insufficient_vector_width");
        break;
      case Geometry::SameLane:
        if (!chooseDistinct(rng, domain, count, flats))
            return fail("insufficient_lane_width");
        for (int &f : flats)
            f += base;
        break;
      case Geometry::SameLaneAdjacent: {
        if (count > lane_width)
            return fail("insufficient_lane_width");
        const int start = std::uniform_int_distribution<int>(
            0, lane_width - count)(rng);
        for (int i = 0; i < count; ++i)
            flats.push_back(base + start + i);
        break;
      }
      case Geometry::SameLaneNonAdjacent: {
        // Re-sample until no two selected bits are adjacent. For count==2
        // this needs lane_width >= 3 (0 and 2 is the smallest valid pair).
        if (count > lane_width || lane_width < count + 1)
            return fail("insufficient_lane_width");
        bool ok = false;
        for (int attempt = 0; attempt < 128 && !ok; ++attempt) {
            if (!chooseDistinct(rng, lane_width, count, flats))
                return fail("insufficient_lane_width");
            ok = hasNoAdjacentPair(flats, lane_width, 0);
        }
        if (!ok)
            return fail("non_adjacent_selection_failed");
        for (int &f : flats)
            f += base;
        break;
      }
      case Geometry::CrossLane: {
        int l0 = directed ? lane
                          : std::uniform_int_distribution<int>(0, lanes - 1)(rng);
        int l1 = std::uniform_int_distribution<int>(0, lanes - 2)(rng);
        if (l1 >= l0)
            ++l1;
        if (l1 == l0 || l1 < 0 || l1 >= lanes)
            return fail("cross_lane_selection_failed");
        flats.push_back(l0 * lane_width +
                        std::uniform_int_distribution<int>(0, lane_width - 1)(rng));
        flats.push_back(l1 * lane_width +
                        std::uniform_int_distribution<int>(0, lane_width - 1)(rng));
        // Additional bits (FR02 is two, but keep the model general) are drawn
        // from the remaining positions in the 128-bit value.
        std::vector<int> used = flats;
        while ((int)flats.size() < count) {
            std::vector<int> rest;
            for (int f = 0; f < kVecBits; ++f)
                if (std::find(used.begin(), used.end(), f) == used.end())
                    rest.push_back(f);
            if ((int)rest.size() < count - (int)flats.size())
                return fail("insufficient_vector_width");
            const int pick = std::uniform_int_distribution<int>(
                0, (int)rest.size() - 1)(rng);
            flats.push_back(rest[(size_t)pick]);
            used.push_back(rest[(size_t)pick]);
        }
        break;
      }
      case Geometry::CrossField: {
        // Two 32-bit fields must be represented. A directed 64-bit lane keeps
        // both fields inside that lane (FR02-d exp+mant); narrower directed
        // lanes anchor one field and cross to another field.
        const int fields = kVecBits / kFieldBits;
        int f0 = -1, f1 = -1;
        if (directed && lane_width >= 64) {
            f0 = fieldOf(lane * lane_width);
            f1 = f0 + 1;
            if (f1 >= fields)
                return fail("insufficient_fields");
        } else if (directed) {
            f0 = fieldOf(lane * lane_width);
            f1 = std::uniform_int_distribution<int>(0, fields - 2)(rng);
            if (f1 >= f0)
                ++f1;
        } else {
            f0 = std::uniform_int_distribution<int>(0, fields - 1)(rng);
            f1 = std::uniform_int_distribution<int>(0, fields - 2)(rng);
            if (f1 >= f0)
                ++f1;
        }
        if (f0 < 0 || f1 < 0 || f0 == f1)
            return fail("cross_field_selection_failed");
        std::vector<int> used;
        auto addBitInField = [&](int field) {
            std::vector<int> cand;
            for (int b = 0; b < kFieldBits; ++b) {
                const int flat = field * kFieldBits + b;
                if (std::find(used.begin(), used.end(), flat) == used.end())
                    cand.push_back(flat);
            }
            if (cand.empty())
                return false;
            const int pick = std::uniform_int_distribution<int>(
                0, (int)cand.size() - 1)(rng);
            flats.push_back(cand[(size_t)pick]);
            used.push_back(cand[(size_t)pick]);
            return true;
        };
        if (!addBitInField(f0) || !addBitInField(f1))
            return fail("cross_field_selection_failed");
        while ((int)flats.size() < count) {
            std::vector<int> rest;
            for (int f = 0; f < kVecBits; ++f)
                if (std::find(used.begin(), used.end(), f) == used.end())
                    rest.push_back(f);
            if ((int)rest.size() < count - (int)flats.size())
                return fail("insufficient_vector_width");
            const int pick = std::uniform_int_distribution<int>(
                0, (int)rest.size() - 1)(rng);
            flats.push_back(rest[(size_t)pick]);
            used.push_back(rest[(size_t)pick]);
        }
        int distinct_fields = 0;
        distinctFieldCount(flats, distinct_fields);
        if (distinct_fields < 2)
            return fail("cross_field_selection_failed");
        break;
      }
    }

    std::sort(flats.begin(), flats.end());
    flats.erase(std::unique(flats.begin(), flats.end()), flats.end());
    if ((int)flats.size() != count)
        return fail("duplicate_bit");

    Selection s;
    s.ok = true;
    s.reason = "ok";
    s.geometry = geom;
    s.lane_width = lane_width;
    s.lane_offset = laneOf(flats.front(), lane_width);
    for (int f : flats) {
        BitId id;
        id.flat = f;
        id.lane = laneOf(f, lane_width);
        id.bit_in_lane = bitInLane(f, lane_width);
        id.field = fieldOf(f);
        s.bits.push_back(id);
        if (f < 64)
            s.mask_lo |= (1ULL << f);
        else
            s.mask_hi |= (1ULL << (f - 64));
    }
    return s;
}

// Relative-to-lane mask for the bits that live in `lane`.
inline uint64_t
laneMask(const Selection &s, int lane)
{
    uint64_t m = 0;
    for (const auto &b : s.bits)
        if (b.lane == lane && b.bit_in_lane >= 0 &&
            b.bit_in_lane < 64)
            m |= (1ULL << b.bit_in_lane);
    return m;
}

// XOR only the selected absolute bits into a vector image. Fails if a bit
// falls outside the 128-bit model or outside the supplied buffer. Every other
// bit/byte is left untouched.
inline bool
applyToVec(uint8_t *vec, size_t bytes, const Selection &s)
{
    if (vec == nullptr || !s.ok)
        return false;
    if (bytes < (size_t)kVecBytes)
        return false;
    for (const auto &b : s.bits) {
        if (b.flat < 0 || b.flat >= kVecBits)
            return false;
        const size_t byte = (size_t)(b.flat / 8);
        if (byte >= bytes)
            return false;
        vec[byte] ^= (uint8_t)(1u << (b.flat % 8));
    }
    return true;
}

// True iff the ONLY bit differences between two images are the selected
// bits, and every selected bit really differs. Used by the host tests to pin
// "non-target lane/bit/register unchanged".
inline bool
onlySelectedBitsDiffer(const uint8_t *before, const uint8_t *after,
                       size_t bytes, const Selection &s,
                       bool require_all_selected = true)
{
    if (before == nullptr || after == nullptr || !s.ok ||
        bytes < (size_t)kVecBytes)
        return false;
    uint64_t changed_lo = 0;
    uint64_t changed_hi = 0;
    for (size_t i = 0; i < bytes; ++i) {
        const uint8_t diff = before[i] ^ after[i];
        if (!diff)
            continue;
        for (int bit = 0; bit < 8; ++bit) {
            if (!((diff >> bit) & 1))
                continue;
            const int flat = (int)(i * 8 + bit);
            if (flat < 64)
                changed_lo |= (1ULL << flat);
            else
                changed_hi |= (1ULL << (flat - 64));
        }
    }
    if ((changed_lo & ~s.mask_lo) || (changed_hi & ~s.mask_hi))
        return false;
    if (require_all_selected &&
        (changed_lo != s.mask_lo || changed_hi != s.mask_hi))
        return false;
    return true;
}

// ---------------------------------------------------------------------------
// TransientCell: the host-testable one-shot cell.
//
// install() performs exactly one read-modify-write. It NEVER arms any
// write-path mask, so the cell cannot become permanently stuck. A later
// write() replaces the value and clears `active`; read() afterwards returns
// the written value, never the injected one.
// ---------------------------------------------------------------------------
class TransientCell
{
  public:
    explicit TransientCell(size_t bytes = (size_t)kVecBytes)
        : bytes_(bytes, 0)
    {
    }

    void reset(const uint8_t *data, size_t n)
    {
        std::fill(bytes_.begin(), bytes_.end(), 0);
        if (data && n)
            std::memcpy(bytes_.data(), data,
                        std::min(n, bytes_.size()));
        active_ = false;
        overwritten_ = false;
        generation_ = 0;
        bits_.clear();
        installs_ = 0;
        writes_ = 0;
        reads_ = 0;
        masked_bits_ = 0;
    }

    bool install(const Selection &s, uint32_t generation)
    {
        if (!s.ok || bytes_.size() < (size_t)kVecBytes)
            return false;
        if (!applyToVec(bytes_.data(), bytes_.size(), s))
            return false;
        active_ = true;
        overwritten_ = false;
        generation_ = generation;
        bits_ = s.bits;
        lane_width_ = s.lane_width;
        masked_bits_ = (uint64_t)popcount128(s.mask_lo, s.mask_hi);
        ++installs_;
        return true;
    }

    // A real program write to the cell. Even a write that happens to carry
    // the same bytes replaces the injected value; the transient fault is gone.
    bool write(const uint8_t *data, size_t n)
    {
        if (!data || n != bytes_.size())
            return false;
        std::memcpy(bytes_.data(), data, n);
        ++writes_;
        if (active_) {
            active_ = false;
            overwritten_ = true;
        }
        return true;
    }

    size_t read(uint8_t *out, size_t n) const
    {
        const size_t copy = std::min(n, bytes_.size());
        if (out && copy)
            std::memcpy(out, bytes_.data(), copy);
        ++reads_;
        return copy;
    }

    bool active() const { return active_; }
    bool overwritten() const { return overwritten_; }
    uint32_t generation() const { return generation_; }
    uint64_t maskedBits() const { return masked_bits_; }
    uint64_t installs() const { return installs_; }
    uint64_t writes() const { return writes_; }
    uint64_t reads() const { return reads_; }
    const std::vector<BitId> &bits() const { return bits_; }
    const std::vector<uint8_t> &bytes() const { return bytes_; }
    size_t size() const { return bytes_.size(); }
    int laneWidth() const { return lane_width_; }

  private:
    std::vector<uint8_t> bytes_;
    std::vector<BitId> bits_;
    bool active_ = false;
    bool overwritten_ = false;
    uint32_t generation_ = 0;
    int lane_width_ = 32;
    uint64_t masked_bits_ = 0;
    uint64_t installs_ = 0;
    uint64_t writes_ = 0;
    mutable uint64_t reads_ = 0;
};

} // namespace chaos_vec_transient
} // namespace gem5

#endif // __CPU_O3_CHAOS_VEC_TRANSIENT_HH__
