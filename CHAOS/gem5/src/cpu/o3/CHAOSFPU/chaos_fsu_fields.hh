#ifndef __CPU_O3_CHAOS_FSU_FIELDS_HH__
#define __CPU_O3_CHAOS_FSU_FIELDS_HH__

// Pure FP field/lane model for the FSU result-side injector.
//
// This header deliberately depends only on the C++ standard library so it can
// be unit-tested with the host compiler (tests/test_chaos_fsu_fields_cpp.py),
// independent of a gem5 build.
//
// Semantics
// ---------
//  - `precision_bits` is 64 (FP64) or 32 (FP32). Field bit coordinates are
//    relative to the start of the FP value, inside a lane.
//  - `lane_width` is the storage lane width in bits: 8/16/32/64.
//  - `lane_offset` is the lane index inside the 128-bit vector register;
//    valid range is [0, 128/lane_width).
//  - A field must fit inside the lane: field.hi < lane_width. FP64 fields
//    therefore require lane_width=64; FP32 fields require lane_width>=32.
//  - `lane_mask` is relative to the lane; `abs_*` locate the same bit in the
//    full 128-bit register (lane_offset*lane_width + bit_in_lane).
//
// All validation is fail-closed: callers get false + an error string and must
// reject the configuration (CHAOSFPU panics) instead of silently injecting.

#include <cstdint>
#include <string>

namespace gem5
{
namespace chaos_fsu
{

struct FieldRange
{
    int lo = 0;
    int hi = -1;
    bool valid = false;
};

struct MaskInfo
{
    uint64_t lane_mask = 0;   // bit mask relative to the lane
    int bit_in_lane = 0;      // bit index relative to the lane
    int abs_bit = 0;          // bit index in the full 128-bit register
    uint64_t abs_lo = 0;      // 128-bit absolute mask, low 64 bits
    uint64_t abs_hi = 0;      // 128-bit absolute mask, high 64 bits
};

// "fp64" -> 64, "fp32" -> 32; anything else is rejected.
inline bool
parsePrecision(const std::string &precision, int &bits)
{
    if (precision == "fp64") {
        bits = 64;
        return true;
    }
    if (precision == "fp32") {
        bits = 32;
        return true;
    }
    return false;
}

// IEEE754 field bit ranges. FP64: sign=63, exp=62..52
// (exp_hi=62..58, exp_lo=57..52), mant=51..0
// (mant_hi=51..35, mant_mid=34..18, mant_lo=17..0).
// FP32: sign=31, exp=30..23 (exp_hi=30..27, exp_lo=26..23),
// mant=22..0 (mant_hi=22..15, mant_mid=14..8, mant_lo=7..0).
inline FieldRange
fieldRange(const std::string &seg, int precision_bits)
{
    if (precision_bits == 64) {
        if (seg == "sign")     return {63, 63, true};
        if (seg == "exp_hi")   return {58, 62, true};
        if (seg == "exp_lo")   return {52, 57, true};
        if (seg == "mant_hi")  return {35, 51, true};
        if (seg == "mant_mid") return {18, 34, true};
        if (seg == "mant_lo")  return {0, 17, true};
    } else if (precision_bits == 32) {
        if (seg == "sign")     return {31, 31, true};
        if (seg == "exp_hi")   return {27, 30, true};
        if (seg == "exp_lo")   return {23, 26, true};
        if (seg == "mant_hi")  return {15, 22, true};
        if (seg == "mant_mid") return {8, 14, true};
        if (seg == "mant_lo")  return {0, 7, true};
    }
    return {0, -1, false};
}

inline bool
laneGeometryValid(int lane_width, int lane_offset, std::string &err)
{
    if (lane_width != 8 && lane_width != 16 && lane_width != 32 &&
        lane_width != 64) {
        err = "lane_width must be 8/16/32/64, got " +
              std::to_string(lane_width);
        return false;
    }
    const int lanes = 128 / lane_width;
    if (lane_offset < 0 || lane_offset >= lanes) {
        err = "lane_offset " + std::to_string(lane_offset) +
              " out of [0," + std::to_string(lanes) + ") for lane_width " +
              std::to_string(lane_width);
        return false;
    }
    return true;
}

inline void
splitAbsMask(unsigned __int128 mask, uint64_t &lo, uint64_t &hi)
{
    lo = (uint64_t)mask;
    hi = (uint64_t)(mask >> 64);
}

inline bool
buildSingleBitMask(int lane_width, int lane_offset, int bit_in_lane,
                   MaskInfo &out, std::string &err)
{
    if (!laneGeometryValid(lane_width, lane_offset, err))
        return false;
    if (bit_in_lane < 0 || bit_in_lane >= lane_width) {
        err = "bit_in_lane " + std::to_string(bit_in_lane) +
              " outside lane width " + std::to_string(lane_width);
        return false;
    }
    out = MaskInfo();
    out.bit_in_lane = bit_in_lane;
    out.lane_mask = (uint64_t)1 << bit_in_lane;
    out.abs_bit = lane_offset * lane_width + bit_in_lane;
    const unsigned __int128 abs =
        ((unsigned __int128)1) << out.abs_bit;
    splitAbsMask(abs, out.abs_lo, out.abs_hi);
    return true;
}

// Mask for one bit of a named IEEE754 field. Fails closed on unknown
// field/precision, a field wider than the lane, or a bit outside the field.
inline bool
buildFieldMask(const std::string &seg, int precision_bits, int lane_width,
               int lane_offset, int bit_in_field, MaskInfo &out,
               std::string &err)
{
    const FieldRange r = fieldRange(seg, precision_bits);
    if (!r.valid) {
        err = "unknown field '" + seg + "' for precision_bits " +
              std::to_string(precision_bits);
        return false;
    }
    if (r.hi >= lane_width) {
        err = "field '" + seg + "' bit range [" + std::to_string(r.lo) +
              "," + std::to_string(r.hi) + "] does not fit lane_width " +
              std::to_string(lane_width);
        return false;
    }
    if (bit_in_field < r.lo || bit_in_field > r.hi) {
        err = "bit " + std::to_string(bit_in_field) + " outside field '" +
              seg + "' range [" + std::to_string(r.lo) + "," +
              std::to_string(r.hi) + "]";
        return false;
    }
    return buildSingleBitMask(lane_width, lane_offset, bit_in_field, out, err);
}

// Explicit fault_mask is lane-relative and may contain multiple bits.
inline bool
validateExplicitMask(uint64_t mask, int lane_width, int lane_offset,
                     std::string &err)
{
    if (!laneGeometryValid(lane_width, lane_offset, err))
        return false;
    if (mask == 0) {
        err = "explicit fault_mask must be non-zero";
        return false;
    }
    if (lane_width < 64 && (mask >> lane_width) != 0) {
        err = "fault_mask 0x" + std::to_string(mask) +
              " does not fit lane_width " + std::to_string(lane_width);
        return false;
    }
    return true;
}

inline bool
buildExplicitMask(uint64_t mask, int lane_width, int lane_offset,
                  MaskInfo &out, std::string &err)
{
    if (!validateExplicitMask(mask, lane_width, lane_offset, err))
        return false;
    out = MaskInfo();
    out.lane_mask = mask;
    out.bit_in_lane = __builtin_ctzll(mask);
    out.abs_bit = lane_offset * lane_width + out.bit_in_lane;
    const unsigned __int128 abs =
        ((unsigned __int128)mask) << (lane_offset * lane_width);
    splitAbsMask(abs, out.abs_lo, out.abs_hi);
    return true;
}

// Only the mask bits may differ. This is the core "target field only"
// invariant checked by the unit tests and by the seed audit.
inline bool
onlyTargetBitsChanged(uint64_t before, uint64_t after, uint64_t mask)
{
    return ((before ^ after) & ~mask) == 0 && (before ^ after) != 0;
}

// Keep the upper bits of a narrow lane value; only lane_width bits are live.
inline uint64_t
laneMaskForWidth(int lane_width)
{
    if (lane_width >= 64)
        return ~(uint64_t)0;
    return (((uint64_t)1) << lane_width) - 1;
}

// [FSU][F5] Permanent stuck-at polarity. 0 = SA0 (force target bits to 0),
// 1 = SA1 (force target bits to 1). Any other value is invalid and callers
// must reject the configuration (fail closed).
inline bool
stuckPolarityValid(int polarity)
{
    return polarity == 0 || polarity == 1;
}

// Apply a permanent stuck-at fault to one lane value. This is NOT XOR:
//   SA0: value & ~mask   (every target bit forced to 0)
//   SA1: value |  mask   (every target bit forced to 1)
// Bits outside `mask` are never touched, so the "non-target bits unchanged"
// invariant holds by construction. The operation is idempotent:
// applyStuck(applyStuck(v)) == applyStuck(v).
inline uint64_t
applyStuck(uint64_t value, uint64_t mask, int polarity)
{
    return polarity ? (value | mask) : (value & ~mask);
}

// Was this exposure activated? A stuck-at exposure is activated exactly when
// the pre-application (correct) value differs from the forced polarity on at
// least one target bit:
//   SA0: any target bit is 1 in the correct value -> (correct & mask) != 0
//   SA1: any target bit is 0 in the correct value -> (~correct & mask) != 0
// Multi-bit masks activate when ANY target bit differs (not all): a single
// already-stuck bit does not mask the other forced bits. An empty mask is
// never activated.
inline bool
stuckActivated(uint64_t correct, uint64_t mask, int polarity)
{
    if (mask == 0)
        return false;
    return polarity ? ((~correct & mask) != 0) : ((correct & mask) != 0);
}

// ---------------------------------------------------------------------------
// [FSU][F5] Bounded sample budget + eligible/warm-up accounting.
//
// These are pure functions so the exact arithmetic used by CHAOSFPU's
// constructor and chain_end emitter can be unit-tested on the host, without a
// gem5 build:
//
//   budget  = f5SampleLimit
//   N > 0:  keep_first = min(N, budget)
//           keep_last  = min(N, budget - keep_first)
//   N == 0: keep_first = budget, keep_last = 0
//
// The mandatory events (install, carrier, first exposure, first activated
// exposure, its L2-L5 chain, chain_end) are extra. `F5_MANDATORY_EVENTS` is a
// conservative count of those; the auditable budget (190000) plus them must
// stay strictly below the PROP-EVT cap (200000), so a run can never be
// silently truncated. A configuration over the cap must PANIC (the injector
// does), never silently clamp.
// ---------------------------------------------------------------------------
struct F5SampleBudget
{
    uint64_t keep_first = 0;
    uint64_t keep_last = 0;
    uint64_t total_with_mandatory = 0;
    bool within_cap = false;
};

static constexpr uint64_t F5_MANDATORY_EVENTS = 8;
static constexpr uint64_t F5_AUDITABLE_BUDGET = 190000;
static constexpr uint64_t F5_EVENT_CAP = 200000;

inline F5SampleBudget
f5ResolveSampleBudget(uint64_t sample_limit, uint64_t keep_first_last_n)
{
    F5SampleBudget b;
    if (keep_first_last_n == 0) {
        b.keep_first = sample_limit;
    } else {
        b.keep_first = keep_first_last_n < sample_limit
                       ? keep_first_last_n : sample_limit;
        const uint64_t rest = sample_limit - b.keep_first;
        b.keep_last = keep_first_last_n < rest
                      ? keep_first_last_n : rest;
    }
    if (b.keep_first > UINT64_MAX - b.keep_last) {
        b.total_with_mandatory = UINT64_MAX;
    } else {
        const uint64_t sum = b.keep_first + b.keep_last;
        b.total_with_mandatory = sum > UINT64_MAX - F5_MANDATORY_EVENTS
                                 ? UINT64_MAX
                                 : sum + F5_MANDATORY_EVENTS;
    }
    b.within_cap = b.total_with_mandatory <= F5_AUDITABLE_BUDGET
                   && b.total_with_mandatory < F5_EVENT_CAP;
    return b;
}

// Warm-up counts MATCHED eligible events. If the fault was installed, exactly
// `warmup_configured` eligible events were skipped; if the run ended before
// installation, every eligible event seen was a warm-up skip. Never reports
// more skips than events actually seen.
inline uint64_t
f5WarmupEligibleSkipped(uint64_t warmup_configured,
                        uint64_t eligible_seen_total, bool installed)
{
    if (!installed)
        return eligible_seen_total;
    return warmup_configured < eligible_seen_total
           ? warmup_configured : eligible_seen_total;
}

// Eligible events from the installation window onward. The installation event
// itself is exposure #1, so this includes it.
inline uint64_t
f5PostInstallEligible(uint64_t eligible_seen_total,
                      uint64_t warmup_eligible_skipped)
{
    return eligible_seen_total >= warmup_eligible_skipped
           ? eligible_seen_total - warmup_eligible_skipped : 0;
}

inline uint64_t
f5InstallEligibleOrdinal(uint64_t warmup_eligible_skipped)
{
    return warmup_eligible_skipped + 1;
}

// The three identities emitted on fault_installed / chain_end:
//   eligible_seen_total = warmup_eligible_skipped + post_install_eligible
//   post_install_eligible = exposures_total + eligible_without_writable_dest
//   install_eligible_ordinal = warmup_eligible_skipped + 1
// A fault-run eligible total different from the pre-registered census is NOT
// an error; only this internal arithmetic is required to hold.
inline bool
f5EligibleAccountingValid(uint64_t eligible_seen_total,
                          uint64_t warmup_eligible_skipped,
                          uint64_t post_install_eligible,
                          uint64_t exposures_total,
                          uint64_t eligible_without_writable_dest,
                          uint64_t install_eligible_ordinal)
{
    return eligible_seen_total ==
               warmup_eligible_skipped + post_install_eligible
        && post_install_eligible ==
               exposures_total + eligible_without_writable_dest
        && install_eligible_ordinal == warmup_eligible_skipped + 1;
}

// A consumer that reads a physical cell touched by several activated
// exposures gets ONE expanded source (the first activated exposure's recorded
// chain) plus a bounded summary of the rest. It never expands every source.
struct F5SourceSummary
{
    uint64_t expanded = 0;
    uint64_t unexpanded = 0;
};

inline F5SourceSummary
f5SourceSummary(uint64_t merged_activated_exposures)
{
    F5SourceSummary s;
    if (merged_activated_exposures == 0)
        return s;
    s.expanded = 1;
    s.unexpanded = merged_activated_exposures - 1;
    return s;
}

} // namespace chaos_fsu
} // namespace gem5

#endif // __CPU_O3_CHAOS_FSU_FIELDS_HH__
