// Host unit test: FR01 / FR02 transient Vec physical-cell bit flips.
//
// Build/run (no gem5, no workload):
//   g++ -O0 -std=c++17 -Wall -Wextra -Werror
//       -I CHAOS/gem5/src/cpu/o3/CHAOSPhysReg
//       tests/unit/chaos_vec_transient_test.cc -o /tmp/x && /tmp/x
//
// Exit code 0 = all checks pass.
//
// What this pins (workbook tables 3/7/9 FR01 + FR02):
//   * FR01 flips exactly one bit in the 128-bit Vec value;
//   * FR02 flips exactly two DIFFERENT bits, never a collapsed one-bit fault;
//   * a two-bit mask with only one set bit is rejected (fail closed);
//   * a geometry whose domain cannot hold the requested bits is rejected;
//   * cross-lane / cross-field / adjacent / non-adjacent geometry is in-range;
//   * every non-target lane/bit/byte is unchanged;
//   * the fault is one-shot: a real write overwrites it and reads afterwards
//     never re-apply it (no permanent/stuck behaviour).

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <random>
#include <set>
#include <vector>

#include "chaos_vec_transient.hh"

using namespace gem5::chaos_vec_transient;

static int failures = 0;

static void
check(const char *name, bool ok)
{
    if (ok) {
        std::printf("  PASS %s\n", name);
    } else {
        std::printf("  FAIL %s\n", name);
        ++failures;
    }
}

static void
fillPattern(uint8_t *v, size_t n, uint8_t seed)
{
    for (size_t i = 0; i < n; ++i)
        v[i] = (uint8_t)(seed + 37u * i);
}

static uint64_t
bytesToU64(const uint8_t *v, int lane_width, int lane)
{
    const int lane_bytes = lane_width / 8;
    const int base = lane * lane_bytes;
    uint64_t x = 0;
    for (int b = 0; b < lane_bytes; ++b)
        x |= (uint64_t)v[base + b] << (8 * b);
    return x;
}

static int
diffBits(const uint8_t *a, const uint8_t *b)
{
    int n = 0;
    for (int i = 0; i < kVecBytes; ++i)
        n += __builtin_popcount((unsigned)(a[i] ^ b[i]));
    return n;
}

int
main()
{
    const uint8_t initial_pattern[16] = {
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
        0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff,
    };

    // ------------------------------------------------------------------
    // FR01: one bit in one directed 32-bit lane.
    // ------------------------------------------------------------------
    {
        const Selection s = selectionFromMask(
            32, 0, 1, Geometry::SameLane, 1ULL << 5, 0);
        check("FR01 selection ok (lane 0, bit 5)", s.ok &&
              s.bits.size() == 1 && s.bits[0].flat == 5 &&
              s.bits[0].lane == 0 && s.bits[0].bit_in_lane == 5 &&
              s.bits[0].field == 0 && popcount128(s.mask_lo, s.mask_hi) == 1);

        uint8_t before[16];
        uint8_t after[16];
        std::memcpy(before, initial_pattern, sizeof(before));
        std::memcpy(after, before, sizeof(after));
        check("FR01 apply succeeds",
              applyToVec(after, sizeof(after), s));
        check("FR01 single-bit: only target bit changes",
              onlySelectedBitsDiffer(before, after, sizeof(after), s) &&
              diffBits(before, after) == 1);
        check("FR01 non-target lanes/bytes unchanged",
              std::memcmp(before + 1, after + 1, 15) == 0 &&
              bytesToU64(after, 32, 0) == (bytesToU64(before, 32, 0) ^ 0x20ULL));

        // Negative control: a different lane/bit is untouched.
        uint8_t lane3_before[16], lane3_after[16];
        std::memcpy(lane3_before, initial_pattern, 16);
        std::memcpy(lane3_after, lane3_before, 16);
        (void)applyToVec(lane3_after, 16, s);
        check("FR01 negative: lane 3 byte-identical",
              std::memcmp(lane3_before + 12, lane3_after + 12, 4) == 0);
        check("FR01 negative: only the selected lane differs",
              std::memcmp(lane3_before + 4, lane3_after + 4, 12) == 0);
    }

    // ------------------------------------------------------------------
    // FR01: transient overwrite. No permanent re-apply is possible.
    // ------------------------------------------------------------------
    {
        const Selection s = selectionFromMask(
            64, 0, 1, Geometry::SameLane, 1ULL << 40, 0);
        TransientCell cell(16);
        cell.reset(initial_pattern, 16);
        check("FR01 cell install succeeds", cell.install(s, 7));
        check("FR01 cell is active after install", cell.active() &&
              !cell.overwritten() && cell.installs() == 1 &&
              cell.maskedBits() == 1 && cell.generation() == 7);

        uint8_t read1[16];
        cell.read(read1, 16);
        check("FR01 read observes the injected value",
              read1[5] == (uint8_t)(initial_pattern[5] ^ (1u << 0)));

        uint8_t replacement[16];
        fillPattern(replacement, 16, 0x80);
        check("FR01 real write accepted", cell.write(replacement, 16));
        check("FR01 overwrite terminates the transient",
              !cell.active() && cell.overwritten() && cell.writes() == 1);

        uint8_t read2[16], read3[16];
        cell.read(read2, 16);
        cell.read(read3, 16);
        check("FR01 overwrite: reads return the written value, not the flip",
              std::memcmp(read2, replacement, 16) == 0 &&
              std::memcmp(read3, replacement, 16) == 0 &&
              std::memcmp(read2, read3, 16) == 0);
        check("FR01 no permanent/stuck re-apply on later reads",
              !cell.active() && cell.overwritten() &&
              cell.bytes() == std::vector<uint8_t>(replacement,
                                                   replacement + 16));
    }

    // ------------------------------------------------------------------
    // FR02: two bits are always distinct over many random selections.
    // ------------------------------------------------------------------
    {
        std::mt19937 rng(0x5eed1234u);
        bool all_ok = true;
        bool saw_same_lane = false;
        bool saw_cross_lane = false;
        for (int i = 0; i < 2000; ++i) {
            const Selection s = select(rng, 32, -1, 2, Geometry::Any);
            const int bits = popcount128(s.mask_lo, s.mask_hi);
            if (!s.ok || s.bits.size() != 2 || bits != 2 ||
                s.bits[0].flat == s.bits[1].flat ||
                s.bits[0].flat < 0 || s.bits[1].flat >= kVecBits)
                all_ok = false;
            if (s.ok) {
                if (s.bits[0].lane == s.bits[1].lane)
                    saw_same_lane = true;
                else
                    saw_cross_lane = true;
            }
        }
        check("FR02 two bits are always distinct", all_ok);
        check("FR02 128-bit domain reaches same-lane and cross-lane pairs",
              saw_same_lane && saw_cross_lane);
    }

    // ------------------------------------------------------------------
    // FR02: collision / insufficient domain fail closed.
    // ------------------------------------------------------------------
    {
        // One-bit mask requested as a two-bit fault: MUST be rejected.
        const Selection collapsed = selectionFromMask(
            32, 0, 2, Geometry::SameLane, 1ULL << 5, 0);
        check("FR02 collision in explicit mask rejected (fail closed)",
              !collapsed.ok &&
              collapsed.reason == "mask_popcount_mismatch");

        // A one-value pool cannot supply two distinct values.
        std::mt19937 rng(7);
        std::vector<int> out;
        check("FR02 chooseDistinct rejects an undersized domain",
              !chooseDistinct(rng, 1, 2, out));

        const Selection narrow = select(rng, 8, 0, 9, Geometry::SameLane);
        check("FR02 insufficient lane width rejected (fail closed)",
              !narrow.ok &&
              (narrow.reason == "insufficient_lane_width" ||
               narrow.reason == "bit_count_out_of_range"));

        const Selection bad_lane = selectionFromMask(
            64, 2, 1, Geometry::SameLane, 1ULL << 5, 0);
        check("FR02 out-of-range lane rejected (fail closed)",
              !bad_lane.ok && bad_lane.reason == "lane_offset_out_of_range");

        const Selection bad_width = selectionFromMask(
            0, 0, 1, Geometry::Any, 1ULL << 5, 0);
        check("FR02 invalid lane width rejected (fail closed)",
              !bad_width.ok && bad_width.reason == "invalid_lane_width");

        // Explicit two-bit mask outside the directed lane: reject.
        const Selection wrong_lane = selectionFromMask(
            32, 1, 2, Geometry::SameLane, 0x21ULL, 0);
        check("FR02 directed-lane mismatch rejected (fail closed)",
              !wrong_lane.ok && wrong_lane.reason == "written_lane_mismatch");
    }

    // ------------------------------------------------------------------
    // FR02: explicit two-bit identities (cross-lane low-64 mask).
    // bits 5 and 37 => lane 0 bit 5, lane 1 bit 5 (32-bit lanes).
    // ------------------------------------------------------------------
    {
        const Selection s = selectionFromMask(
            32, -1, 2, Geometry::CrossLane, 0x2000000020ULL, 0);
        check("FR02 explicit two-bit mask has two distinct identities",
              s.ok && s.bits.size() == 2 &&
              s.bits[0].flat == 5 && s.bits[1].flat == 37 &&
              s.bits[0].lane == 0 && s.bits[1].lane == 1 &&
              s.bits[0].bit_in_lane == 5 &&
              s.bits[1].bit_in_lane == 5 &&
              popcount128(s.mask_lo, s.mask_hi) == 2);

        uint8_t before[16], after[16];
        std::memcpy(before, initial_pattern, 16);
        std::memcpy(after, before, 16);
        check("FR02 explicit mask applies exactly two bits",
              applyToVec(after, 16, s) &&
              onlySelectedBitsDiffer(before, after, 16, s) &&
              diffBits(before, after) == 2);
    }

    // ------------------------------------------------------------------
    // FR02: cross-lane geometry, only target bits change.
    // ------------------------------------------------------------------
    {
        std::mt19937 rng(12345);
        bool ok = true;
        for (int i = 0; i < 500; ++i) {
            const Selection s = select(rng, 32, -1, 2, Geometry::CrossLane);
            if (!s.ok || s.bits.size() != 2 ||
                s.bits[0].lane == s.bits[1].lane ||
                popcount128(s.mask_lo, s.mask_hi) != 2)
                ok = false;
            if (s.ok) {
                uint8_t before[16], after[16];
                std::memcpy(before, initial_pattern, 16);
                std::memcpy(after, before, 16);
                if (!applyToVec(after, 16, s) ||
                    !onlySelectedBitsDiffer(before, after, 16, s) ||
                    diffBits(before, after) != 2)
                    ok = false;
            }
        }
        check("FR02 cross-lane geometry is in-range and only target bits change",
              ok);

        // Directed cross-lane: lane 2 must be one of the two lanes.
        std::mt19937 rng2(999);
        const Selection directed = select(rng2, 32, 2, 2, Geometry::CrossLane);
        check("FR02 directed cross-lane keeps the requested lane",
              directed.ok && directed.bits.size() == 2 &&
              (directed.bits[0].lane == 2 || directed.bits[1].lane == 2) &&
              directed.bits[0].lane != directed.bits[1].lane);

        // Directed cross-lane mask that omits the requested lane is rejected.
        const Selection missing = selectionFromMask(
            32, 2, 2, Geometry::CrossLane, 0x2000000020ULL, 0);
        check("FR02 cross-lane mask missing the directed lane rejected",
              !missing.ok &&
              missing.reason == "written_lane_not_in_mask");
    }

    // ------------------------------------------------------------------
    // FR02-d: cross-field (different 32-bit fields).
    // ------------------------------------------------------------------
    {
        std::mt19937 rng(42);
        bool ok = true;
        for (int i = 0; i < 300; ++i) {
            const Selection s = select(rng, 32, -1, 2, Geometry::CrossField);
            if (!s.ok || s.bits.size() != 2 ||
                s.bits[0].field == s.bits[1].field)
                ok = false;
        }
        check("FR02 cross-field geometry uses two 32-bit fields", ok);

        // Directed FP64 lane: exp+mant stay inside the 64-bit lane (fields
        // 0/1 for lane 0, 2/3 for lane 1).
        std::mt19937 rng2(77);
        const Selection fp64 = select(rng2, 64, 1, 2, Geometry::CrossField);
        check("FR02 cross-field inside a directed 64-bit lane",
              fp64.ok && fp64.bits.size() == 2 &&
              fp64.bits[0].lane == 1 && fp64.bits[1].lane == 1 &&
              fp64.bits[0].field != fp64.bits[1].field &&
              fp64.bits[0].flat >= 64 && fp64.bits[1].flat < 128);

        // Directed 32-bit lane: that lane's field is one of the two fields.
        const Selection fp32 = select(rng2, 32, 2, 2, Geometry::CrossField);
        check("FR02 cross-field anchored on a directed 32-bit lane",
              fp32.ok && fp32.bits.size() == 2 &&
              (fp32.bits[0].field == 2 || fp32.bits[1].field == 2) &&
              fp32.bits[0].field != fp32.bits[1].field);
    }

    // ------------------------------------------------------------------
    // FR02-a/b: adjacent / non-adjacent within one lane.
    // ------------------------------------------------------------------
    {
        std::mt19937 rng(2026);
        bool adj_ok = true;
        bool non_ok = true;
        for (int i = 0; i < 300; ++i) {
            const Selection a = select(rng, 32, -1, 2,
                                       Geometry::SameLaneAdjacent);
            if (!a.ok || a.bits.size() != 2 ||
                a.bits[1].flat != a.bits[0].flat + 1 ||
                a.bits[0].lane != a.bits[1].lane)
                adj_ok = false;
            const Selection b = select(rng, 32, -1, 2,
                                       Geometry::SameLaneNonAdjacent);
            if (!b.ok || b.bits.size() != 2 ||
                b.bits[1].flat - b.bits[0].flat < 2 ||
                b.bits[0].lane != b.bits[1].lane)
                non_ok = false;
        }
        check("FR02 adjacent geometry: distance exactly 1 in one lane",
              adj_ok);
        check("FR02 non-adjacent geometry: distance >= 2 in one lane",
              non_ok);

        // FR02-a needs 2 bits in an 8-bit lane: valid; 9 bits: fail closed.
        const Selection lane8 = select(rng, 8, 3, 2,
                                       Geometry::SameLaneAdjacent);
        check("FR02 adjacent geometry accepts an 8-bit lane",
              lane8.ok && lane8.bits.size() == 2 &&
              lane8.bits[0].lane == 3);
    }

    // ------------------------------------------------------------------
    // 128-bit boundary / field identity.
    // ------------------------------------------------------------------
    {
        const Selection top = selectionFromMask(
            32, 3, 1, Geometry::SameLane, 0, 1ULL << 63);
        check("128-bit boundary bit 127 is addressable",
              top.ok && top.bits.size() == 1 && top.bits[0].flat == 127 &&
              top.bits[0].lane == 3 && top.bits[0].field == 3);

        uint8_t before[16], after[16];
        std::memcpy(before, initial_pattern, 16);
        std::memcpy(after, before, 16);
        check("128-bit boundary: byte 15 bit 7 flips, nothing else",
              applyToVec(after, 16, top) &&
              onlySelectedBitsDiffer(before, after, 16, top) &&
              (after[15] ^ before[15]) == 0x80 &&
              std::memcmp(before, after, 15) == 0);
    }

    // ------------------------------------------------------------------
    // The lane-relative mask helper is the evidence identity.
    // ------------------------------------------------------------------
    {
        const Selection s = selectionFromMask(
            32, 1, 2, Geometry::SameLane, 0x1800000000ULL, 0);
        check("lane mask helper reports exact bit identities",
              s.ok && laneMask(s, 1) == 0x18ULL &&
              laneMask(s, 0) == 0 && s.bits[0].bit_in_lane == 3 &&
              s.bits[1].bit_in_lane == 4);
    }

    if (failures == 0)
        std::printf("ALL TRANSIENT CHECKS PASSED\n");
    else
        std::printf("%d TRANSIENT CHECK(S) FAILED\n", failures);
    return failures == 0 ? 0 : 1;
}
