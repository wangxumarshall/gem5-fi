// Host-side unit test for the [FSU][F5] permanent stuck-at pure functions in
// cpu/o3/CHAOSFPU/chaos_fsu_fields.hh.
//
// Compiled and run by tests/test_chaos_fsu_f5_cpp.py (no gem5 build):
//   g++ -O0 -std=c++17 -I CHAOS/gem5/src
//       tests/unit/chaos_fsu_f5_test.cc -o /tmp/fsu_f5_test
//
// The test pins the semantics the injector relies on:
//   - SA0 forces target bits to 0, SA1 forces them to 1 (NOT XOR);
//   - application is idempotent and leaves every non-target bit unchanged;
//   - a multi-bit exposure is activated when ANY target bit differs from
//     the forced polarity (not only when all bits differ);
//   - an exposure where the correct value already carries the polarity is
//     exposed-but-not-activated.

#include <cstdio>
#include <cstdint>

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
test_polarity_validity()
{
    CHECK(stuckPolarityValid(0));
    CHECK(stuckPolarityValid(1));
    CHECK(!stuckPolarityValid(-1));
    CHECK(!stuckPolarityValid(2));
}

static void
test_sa0_sa1_are_forced_not_xor()
{
    const uint64_t mask = (1ULL << 13) | (1ULL << 40);
    const uint64_t v = 0x123456789abcdef0ULL;

    // SA0: every target bit is cleared. XOR would FLIP a set bit; a forced
    // zero always clears it.
    const uint64_t sa0 = applyStuck(v, mask, 0);
    CHECK((sa0 & mask) == 0);
    CHECK((sa0 & ~mask) == (v & ~mask));

    // SA1: every target bit is set, regardless of its previous value.
    const uint64_t sa1 = applyStuck(v, mask, 1);
    CHECK((sa1 & mask) == mask);
    CHECK((sa1 & ~mask) == (v & ~mask));

    // Already-stuck values stay byte-identical (XOR would flip them back).
    CHECK(applyStuck(sa0, mask, 0) == sa0);
    CHECK(applyStuck(sa1, mask, 1) == sa1);

    // The two polarities differ on the target bits and agree elsewhere.
    CHECK(((sa0 ^ sa1) & ~mask) == 0);
    CHECK(((sa0 ^ sa1) & mask) == mask);
}

static void
test_idempotence()
{
    const uint64_t masks[] = {
        1ULL, 1ULL << 31, 1ULL << 63, 0x5ULL, 0xff00ff00ff00ff00ULL,
    };
    for (uint64_t m : masks) {
        for (uint64_t v : {0ULL, ~0ULL, 0x0123456789abcdefULL,
                           0xfedcba9876543210ULL}) {
            for (int p = 0; p <= 1; ++p) {
                const uint64_t once = applyStuck(v, m, p);
                CHECK(applyStuck(once, m, p) == once);
            }
        }
    }
}

static void
test_non_target_bits_unchanged()
{
    const uint64_t mask = 0x0000000f00000000ULL;
    const uint64_t v = 0x89abcdef01234567ULL;
    for (int p = 0; p <= 1; ++p) {
        const uint64_t out = applyStuck(v, mask, p);
        CHECK((out & ~mask) == (v & ~mask));
        // onlyTargetBitsChanged is true only if the value actually moved.
        if (out != v)
            CHECK(onlyTargetBitsChanged(v, out, mask));
    }
}

static void
test_activation_single_bit()
{
    const uint64_t bit = 1ULL << 7;
    // SA0 activates when the correct bit is 1.
    CHECK(stuckActivated(bit, bit, 0));
    CHECK(!stuckActivated(0, bit, 0));
    // SA1 activates when the correct bit is 0.
    CHECK(stuckActivated(0, bit, 1));
    CHECK(!stuckActivated(bit, bit, 1));
}

static void
test_activation_multibit_any()
{
    const uint64_t mask = 0x3ULL;   // bits 0 and 1
    // SA0: 0b01 has one set target bit -> activated (ANY, not ALL).
    CHECK(stuckActivated(0x1ULL, mask, 0));
    CHECK(stuckActivated(0x2ULL, mask, 0));
    CHECK(!stuckActivated(0x0ULL, mask, 0));
    CHECK(stuckActivated(0x3ULL, mask, 0));
    // SA1: 0b10 has one clear target bit -> activated.
    CHECK(stuckActivated(0x2ULL, mask, 1));
    CHECK(stuckActivated(0x1ULL, mask, 1));
    CHECK(!stuckActivated(0x3ULL, mask, 1));
    CHECK(stuckActivated(0x0ULL, mask, 1));
    // Empty mask never activates.
    CHECK(!stuckActivated(0xffffffffffffffffULL, 0, 0));
    CHECK(!stuckActivated(0xffffffffffffffffULL, 0, 1));
}

static void
test_exposed_but_not_activated()
{
    // Correct value already carries the SA1 polarity on every target bit:
    // the exposure is real (it happens on every eligible event) but it does
    // not change the value.
    const uint64_t mask = 0x0f0f0f0f0f0f0f0fULL;
    const uint64_t correct = mask;   // all target bits already 1
    CHECK(!stuckActivated(correct, mask, 1));
    CHECK(applyStuck(correct, mask, 1) == correct);

    // Same for SA0 with all target bits already 0.
    CHECK(!stuckActivated(0, mask, 0));
    CHECK(applyStuck(0, mask, 0) == 0);

    // And the complementary case is activated.
    CHECK(stuckActivated(0, mask, 1));
    CHECK(stuckActivated(correct, mask, 0));
}

static void
test_narrow_lane()
{
    // FP32 lane-relative mask: only the low 32 bits are ever touched.
    const uint64_t mask = 1ULL << 31;   // FP32 sign inside a 32-bit lane
    // correct sign bit is already 1: SA1 is exposed-but-not-activated
    // (the forced value equals the correct value), SA0 is activated.
    const uint64_t correct = 0x0000000080000000ULL;
    CHECK(!stuckActivated(correct, mask, 1));
    CHECK(stuckActivated(correct, mask, 0));
    const uint64_t sa1 = applyStuck(correct, mask, 1);
    CHECK(sa1 == 0x0000000080000000ULL);
    const uint64_t sa0 = applyStuck(0x00000000c0000000ULL, mask, 0);
    CHECK(sa0 == 0x0000000040000000ULL);
}

static void
test_full_stuck_run_sequence()
{
    // Simulate four exposures of ONE fixed fault (SA1 on bit 5). Only the
    // exposures whose correct value has bit5=0 are activated; the count is
    // 2 and the applied value is always forced, never XORed.
    const uint64_t mask = 1ULL << 5;
    const uint64_t correct[] = {0x00, 0x20, 0x00, 0x20};
    int activated = 0;
    for (uint64_t c : correct) {
        const bool act = stuckActivated(c, mask, 1);
        if (act)
            ++activated;
        const uint64_t after = applyStuck(c, mask, 1);
        CHECK((after & mask) == mask);         // forced to 1 every time
        CHECK((after & ~mask) == (c & ~mask)); // other bits untouched
    }
    CHECK(activated == 2);
}

static void
test_multibit_accounting_across_exposures()
{
    // FP06-c style fixed mantissa mask (FP32 bits 15..22). The SAME fault
    // is exposed many times; activation is recomputed from the correct
    // pre-forced value every time, and the forced write never XORs.
    const uint64_t mask = 0x007f8000ULL;
    const uint64_t correct[] = {
        0x00000000ULL,  // SA0: no target bit set -> not activated
        0x00008000ULL,  // SA0: bit15 set -> activated
        0x00000000ULL,  // not activated
        0x007f8000ULL,  // activated (all set)
    };
    int activated = 0;
    for (uint64_t c : correct) {
        const bool act = stuckActivated(c, mask, 0);
        if (act)
            ++activated;
        const uint64_t after = applyStuck(c, mask, 0);
        CHECK((after & mask) == 0);
        CHECK((after & ~mask) == (c & ~mask));
        if (act)
            CHECK(onlyTargetBitsChanged(c, after, mask));
        else
            CHECK(after == c);
    }
    CHECK(activated == 2);

    // SA1 is the complement: the zero target bits are the activated ones.
    activated = 0;
    for (uint64_t c : correct) {
        if (stuckActivated(c, mask, 1))
            ++activated;
        const uint64_t after = applyStuck(c, mask, 1);
        CHECK((after & mask) == mask);
        CHECK((after & ~mask) == (c & ~mask));
    }
    // SA1 activates on any CLEAR target bit: 0, 0x8000 and 0 activate;
    // only the fully-set 0x007f8000 is exposed-but-not-activated.
    CHECK(activated == 3);
}

static void
test_activation_formula_matches_every_sampled_exposure()
{
    // The seed/gate auditor re-derives `activated` from correct_before and
    // the fixed polarity. Pin the two branches it relies on.
    const uint64_t mask = 0x80000000ULL;   // FP32 sign inside a 32-bit lane
    CHECK(stuckActivated(0x0000000000000000ULL, mask, 0) == false);
    CHECK(stuckActivated(0x0000000080000000ULL, mask, 0) == true);
    CHECK(stuckActivated(0x0000000000000000ULL, mask, 1) == true);
    CHECK(stuckActivated(0x0000000080000000ULL, mask, 1) == false);
}

int
main()
{
    test_polarity_validity();
    test_sa0_sa1_are_forced_not_xor();
    test_idempotence();
    test_non_target_bits_unchanged();
    test_activation_single_bit();
    test_activation_multibit_any();
    test_exposed_but_not_activated();
    test_narrow_lane();
    test_full_stuck_run_sequence();
    test_multibit_accounting_across_exposures();
    test_activation_formula_matches_every_sampled_exposure();
    if (failures) {
        std::fprintf(stderr, "%d failure(s)\n", failures);
        return 1;
    }
    std::printf("chaos_fsu_f5: all checks passed\n");
    return 0;
}
