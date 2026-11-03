// Host-side unit test for cpu/o3/CHAOSFPU/chaos_fsu_fields.hh.
// Compiled and run by tests/test_chaos_fsu_fields_cpp.py (no gem5 build).

#include <cstdio>
#include <cstdlib>
#include <string>

#include "cpu/o3/CHAOSFPU/chaos_fsu_fields.hh"

using namespace gem5::chaos_fsu;

static int failures = 0;

#define CHECK(cond) do {                                                   \
    if (!(cond)) {                                                         \
        std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        ++failures;                                                        \
    }                                                                      \
} while (0)

static void
test_precision()
{
    int bits = 0;
    CHECK(parsePrecision("fp64", bits) && bits == 64);
    CHECK(parsePrecision("fp32", bits) && bits == 32);
    CHECK(!parsePrecision("fp16", bits));
    CHECK(!parsePrecision("", bits));
}

static void
test_field_ranges()
{
    const struct { const char *seg; int lo64, hi64, lo32, hi32; } cases[] = {
        {"sign", 63, 63, 31, 31},
        {"exp_hi", 58, 62, 27, 30},
        {"exp_lo", 52, 57, 23, 26},
        {"mant_hi", 35, 51, 15, 22},
        {"mant_mid", 18, 34, 8, 14},
        {"mant_lo", 0, 17, 0, 7},
    };
    for (const auto &c : cases) {
        FieldRange r64 = fieldRange(c.seg, 64);
        CHECK(r64.valid && r64.lo == c.lo64 && r64.hi == c.hi64);
        FieldRange r32 = fieldRange(c.seg, 32);
        CHECK(r32.valid && r32.lo == c.lo32 && r32.hi == c.hi32);
    }
    CHECK(!fieldRange("bogus", 64).valid);
    CHECK(!fieldRange("sign", 16).valid);
}

static void
test_field_masks()
{
    MaskInfo m;
    std::string err;

    // FP64 sign bit63, lane 64 offset 0.
    CHECK(buildFieldMask("sign", 64, 64, 0, 63, m, err));
    CHECK(m.bit_in_lane == 63 && m.abs_bit == 63);
    CHECK(m.lane_mask == (1ULL << 63));
    CHECK(m.abs_lo == (1ULL << 63) && m.abs_hi == 0);

    // FP64 sign bit63, lane 64 offset 1 (upper 64-bit lane).
    CHECK(buildFieldMask("sign", 64, 64, 1, 63, m, err));
    CHECK(m.abs_bit == 127 && m.abs_lo == 0 && m.abs_hi == (1ULL << 63));

    // FP32 sign bit31, lane 32 offset 3 (last 32-bit lane).
    CHECK(buildFieldMask("sign", 32, 32, 3, 31, m, err));
    CHECK(m.abs_bit == 127 && m.abs_lo == 0 && m.abs_hi == (1ULL << 63));

    // FP32 mant_lo bit7, lane 32 offset 1.
    CHECK(buildFieldMask("mant_lo", 32, 32, 1, 7, m, err));
    CHECK(m.abs_bit == 39 && m.abs_lo == (1ULL << 39) && m.abs_hi == 0);

    // FP32 field inside a 64-bit lane (offset 0) is allowed.
    CHECK(buildFieldMask("exp_hi", 32, 64, 0, 30, m, err));
    CHECK(m.abs_bit == 30 && m.lane_mask == (1ULL << 30));

    // Fail closed: FP64 field cannot fit a 32-bit lane.
    CHECK(!buildFieldMask("sign", 64, 32, 0, 31, m, err));
    // Fail closed: bit outside the field.
    CHECK(!buildFieldMask("mant_lo", 64, 64, 0, 18, m, err));
    // Fail closed: unknown field.
    CHECK(!buildFieldMask("bogus", 64, 64, 0, 0, m, err));
    // Fail closed: lane offset out of range.
    CHECK(!buildFieldMask("mant_lo", 64, 64, 2, 0, m, err));
}

static void
test_explicit_masks()
{
    MaskInfo m;
    std::string err;

    CHECK(buildExplicitMask(0x5, 64, 1, m, err));
    CHECK(m.lane_mask == 0x5 && m.bit_in_lane == 0 && m.abs_bit == 64);
    CHECK(m.abs_lo == 0 && m.abs_hi == 0x5);

    CHECK(buildExplicitMask(0x1ULL << 32, 64, 0, m, err));
    CHECK(m.abs_bit == 32 && m.abs_lo == (1ULL << 32));

    CHECK(!buildExplicitMask(0, 64, 0, m, err));
    CHECK(!buildExplicitMask(1ULL << 32, 32, 0, m, err));
    CHECK(!buildExplicitMask(1, 64, 2, m, err));
}

static void
test_only_target_bits()
{
    const uint64_t mask = 1ULL << 13;
    const uint64_t before = 0x3ff0000000000000ULL;
    const uint64_t after = before ^ mask;
    CHECK(onlyTargetBitsChanged(before, after, mask));
    CHECK(!onlyTargetBitsChanged(before, before, mask));
    CHECK(!onlyTargetBitsChanged(before, after ^ (1ULL << 12), mask));
    CHECK(laneMaskForWidth(32) == 0xffffffffULL);
    CHECK(laneMaskForWidth(64) == ~0ULL);
}

int
main()
{
    test_precision();
    test_field_ranges();
    test_field_masks();
    test_explicit_masks();
    test_only_target_bits();
    if (failures) {
        std::fprintf(stderr, "%d failure(s)\n", failures);
        return 1;
    }
    std::printf("chaos_fsu_fields: all checks passed\n");
    return 0;
}
