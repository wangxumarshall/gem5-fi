// Host unit test for the FR03 Vec permanent-stuck pure model.
//
// Build/run (no gem5, no workload):
//   g++ -O0 -std=c++17 -I CHAOS/gem5/src/cpu/o3/CHAOSPhysReg \
//       tests/unit/chaos_vec_stuck_test.cc -o /tmp/chaos_vec_stuck_test
//   /tmp/chaos_vec_stuck_test
//
// Exit code 0 = all checks pass.

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

#include "chaos_vec_stuck.hh"

using namespace gem5::chaos_vec_stuck;

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

int
main()
{
    // --- forceLane: SA0 / SA1 are force, never XOR -------------------------
    check("SA0 forces target bit to 0",
          forceLane(0xffffffffULL, 0x4ULL, 0) == 0xffffffffULL - 0x4ULL);
    check("SA1 forces target bit to 1",
          forceLane(0x0ULL, 0x4ULL, 1) == 0x4ULL);
    check("SA0 idempotent",
          forceLane(forceLane(0x0fffffffULL, 0x4ULL, 0), 0x4ULL, 0) ==
          0x0ffffffbULL);
    check("SA1 idempotent",
          forceLane(forceLane(0x0ULL, 0x4ULL, 1), 0x4ULL, 1) == 0x4ULL);
    check("SA0 does not use XOR",
          forceLane(0x4ULL, 0x4ULL, 0) == 0x0ULL);
    check("SA1 does not use XOR",
          forceLane(0x4ULL, 0x4ULL, 1) == 0x4ULL);

    // --- satisfied: exposed-but-not-activated ------------------------------
    check("satisfied SA0 when bit already 0", satisfied(0x0ULL, 0x4ULL, 0));
    check("satisfied SA0 false when bit 1", !satisfied(0x4ULL, 0x4ULL, 0));
    check("satisfied SA1 when bit already 1", satisfied(0x4ULL, 0x4ULL, 1));
    check("satisfied SA1 false when bit 0", !satisfied(0x0ULL, 0x4ULL, 1));
    check("multi-bit satisfied only if all target bits equal",
          satisfied(0x7ULL, 0x7ULL, 1) && !satisfied(0x5ULL, 0x7ULL, 1));

    // --- lane placement: only the target lane changes ----------------------
    uint8_t v[16];
    std::memset(v, 0xab, sizeof(v));   // lane2 LSB starts at 1
    uint64_t mask = 0x1ULL;
    check("build lane mask fp32 lane1 bit0", buildLaneMask(32, 0, mask) &&
          mask == 1);
    uint8_t before[16];
    std::memcpy(before, v, 16);
    check("apply SA0 lane2 bit0", applyToVec16(v, 32, 2, 1ULL, 0));
    check("only lane2 bit0 changed",
          onlyMaskedBitsDiffer(before, v, 32, 2, 1ULL));
    check("lane2 low byte cleared", v[8] == 0xaa);
    check("non-target lane0 intact", v[0] == 0xab && v[1] == 0xab &&
          v[2] == 0xab && v[3] == 0xab);
    check("non-target lane3 intact", v[12] == 0xab && v[15] == 0xab);

    std::memcpy(before, v, 16);
    check("apply SA1 lane2 bit0", applyToVec16(v, 32, 2, 1ULL, 1));
    check("only lane2 bit0 changed (SA1)",
          onlyMaskedBitsDiffer(before, v, 32, 2, 1ULL));
    check("lane2 low byte is 0xab", v[8] == 0xab);

    // --- repeated writes: persistence across consecutive writes ------------
    // A program write replaces the cell; the injector must re-force the bit.
    bool consecutive_ok = true;
    for (int i = 0; i < 8; ++i) {
        std::memset(v, (uint8_t)(0x10 + i), sizeof(v));
        applyToVec16(v, 32, 2, 1ULL, 0);
        const uint64_t lane = (uint64_t)v[8] | ((uint64_t)v[9] << 8) |
                              ((uint64_t)v[10] << 16) |
                              ((uint64_t)v[11] << 24);
        if ((lane & 1ULL) != 0)
            consecutive_ok = false;
    }
    check("consecutive writes stay SA0", consecutive_ok);

    // --- generation: freed/reallocated slot is a different generation ------
    Target t;
    t.valid = true;
    t.reg_class = 7;          // opaque class value in the pure model
    t.phys_index = 11;
    t.generation = 3;
    t.lane_width = 32;
    t.lane_offset = 2;
    t.lane_mask = 1;
    t.polarity = 0;
    check("applies in install generation", t.applies(7, 11, 3));
    check("does not apply after reallocation", !t.applies(7, 11, 4));
    check("does not apply to another phys index", !t.applies(7, 12, 3));
    check("does not apply to another class", !t.applies(8, 11, 3));
    t.valid = false;
    check("invalid target never applies", !t.applies(7, 11, 3));

    // --- invalid geometry is rejected (fail closed) ------------------------
    uint64_t dummy = 0;
    check("bad lane width rejected", !buildLaneMask(24, 0, dummy));
    check("bit outside lane rejected", !buildLaneMask(32, 32, dummy));
    check("lane offset outside register rejected",
          !applyToVec16(v, 32, 4, 1, 0));
    check("mask wider than lane rejected",
          !applyToVec16(v, 32, 0, 0x100000000ULL, 0));

    if (failures) {
        std::printf("FAILED: %d check(s)\n", failures);
        return 1;
    }
    std::printf("ALL CHECKS PASSED\n");
    return 0;
}
