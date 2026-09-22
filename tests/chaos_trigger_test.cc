/*
 * chaos_trigger_test.cc — standalone unit test for chaos_trigger.hh
 * (docs/superpowers/plans/2026-09-22-ooo-w0-foundation.md Task 2 / W0.2,
 * F0-F5 unified trigger semantics per the OoO north star).
 *
 * NOT part of the gem5 build. Compiled directly (plan Task 2 Step 3):
 *   g++ -std=c++17 -Wall -Wextra -Werror \
 *       -I CHAOS/gem5/src -I CHAOS/gem5/src/cpu/o3 \
 *       tests/chaos_trigger_test.cc -o /tmp/chaos_trigger_test
 *
 * The -I CHAOS/gem5/src flag mirrors gem5's own CPPPATH: chaos_trigger.hh
 * includes "cpu/o3/chaos_event_sample.hh" repo-style (the same include path
 * CHAOSFPU.cc:11 uses inside gem5), which resolves against src/, not
 * against src/cpu/o3/ — the bare -I CHAOS/gem5/src/cpu/o3 alone cannot
 * find it (src/cpu/o3/cpu/o3/ does not exist).
 *
 * Assertions (plan Task 2 Step 2):
 *   1. F1: per-cycle polling, 1000 adjacent fire intervals, every one in
 *      [1300000, 3900000) (2.6M mean ±50%).
 *   2. F0: exactly one fire over window [1000, 2000) (and none after);
 *      same-seed rebuild lands on the identical cycle (determinism).
 *   3. F5: fire() true at 100 arbitrary cycles (permanent defect).
 *   4. F1 determinism: two same-seed instances, 100 fires each, identical.
 *   5. F2/F3 interval magnitude spot check: every F2 interval in
 *      [130000, 390000), every F3 interval in [13000, 39000) (±50% of
 *      260K / 26K).
 */

#include <cinttypes>
#include <cstddef>
#include <cstdio>

#include "chaos_trigger.hh"

using gem5::ChaOSTier;
using gem5::ChaOSTrigger;

// Compile-time check of the Produces interface (plan Task 2 Interfaces).
static_assert(ChaOSTrigger::intervalCycles(ChaOSTier::F0) == 0,
              "F0 is not interval-based");
static_assert(ChaOSTrigger::intervalCycles(ChaOSTier::F1) == 2600000,
              "F1 = 1ms @ 2.6GHz = 2.6M cycles");
static_assert(ChaOSTrigger::intervalCycles(ChaOSTier::F2) == 260000,
              "F2 = 100us @ 2.6GHz = 260K cycles");
static_assert(ChaOSTrigger::intervalCycles(ChaOSTier::F3) == 26000,
              "F3 = 10us @ 2.6GHz = 26K cycles");
static_assert(ChaOSTrigger::intervalCycles(ChaOSTier::F5) == 0,
              "F5 is not interval-based");

/*
 * Poll fire(now) once per CPU cycle starting at `first` until `n` fires
 * have been observed; record the fire cycles in `out`. Interval tiers
 * (F1/F2/F3) only. Returns false if the generous cycle cap is hit before
 * n fires — itself a failure, since interval fires must keep coming.
 */
static bool
pollFireCycles(ChaOSTier tier, uint64_t seed, uint64_t first, uint64_t last,
               size_t n, uint64_t *out)
{
    ChaOSTrigger t(tier, seed, first, last);
    const uint64_t iv = ChaOSTrigger::intervalCycles(tier);
    // worst case is 1.5*iv per fire; 2*iv per fire plus slack is a safe cap
    const uint64_t cap = first + (uint64_t)n * 2 * iv + 2 * iv + 16;
    size_t got = 0;
    for (uint64_t now = first; now < cap && got < n; now++) {
        if (t.fire(now))
            out[got++] = now;
    }
    return got == n;
}

int
main()
{
    // ---- 1. F1: 1000 adjacent intervals, each in [1.3M, 3.9M) -----------
    {
        static constexpr size_t kFires = 1001;  // -> 1000 intervals
        uint64_t fires[kFires];
        if (!pollFireCycles(ChaOSTier::F1, 12345, 0, 0, kFires, fires)) {
            std::printf("FAIL(1): F1 hit the cycle cap before %zu fires\n",
                        kFires);
            return 1;
        }
        for (size_t i = 1; i < kFires; i++) {
            const uint64_t iv = fires[i] - fires[i - 1];
            if (iv < 1300000 || iv >= 3900000) {
                std::printf("FAIL(1): F1 interval #%zu = %" PRIu64
                            " outside [1300000, 3900000)\n", i - 1, iv);
                return 1;
            }
        }
        std::printf("PASS(1): F1 1000 intervals all in [1300000,3900000), "
                    "mean = %" PRIu64 "\n",
                    (fires[kFires - 1] - fires[0]) / (kFires - 1));
    }

    // ---- 2. F0: single uniform fire over [1000, 2000), deterministic ----
    {
        const uint64_t lo = 1000, hi = 2000;
        uint64_t landing = 0;
        int fires = 0;
        ChaOSTrigger t(ChaOSTier::F0, 0xC0FFEE, lo, hi);
        for (uint64_t now = lo; now < hi; now++) {
            if (t.fire(now)) {
                fires++;
                landing = now;
            }
        }
        if (fires != 1) {
            std::printf("FAIL(2): F0 fired %d times in [1000,2000), "
                        "expected exactly 1\n", fires);
            return 1;
        }
        if (landing < lo || landing >= hi) {
            std::printf("FAIL(2): F0 landing cycle %" PRIu64
                        " outside [1000,2000)\n", landing);
            return 1;
        }
        for (uint64_t now = hi; now < hi + 3000; now++) {
            if (t.fire(now)) {
                std::printf("FAIL(2): F0 re-fired at cycle %" PRIu64
                            " after the window (spent violated)\n", now);
                return 1;
            }
        }
        // same seed, fresh instance -> identical landing cycle
        ChaOSTrigger t2(ChaOSTier::F0, 0xC0FFEE, lo, hi);
        uint64_t landing2 = 0;
        int fires2 = 0;
        for (uint64_t now = lo; now < hi; now++) {
            if (t2.fire(now)) {
                fires2++;
                landing2 = now;
            }
        }
        if (fires2 != 1 || landing2 != landing) {
            std::printf("FAIL(2): F0 determinism: rebuild fired %d times, "
                        "landing %" PRIu64 " vs original %" PRIu64 "\n",
                        fires2, landing2, landing);
            return 1;
        }
        std::printf("PASS(2): F0 fired exactly once in [1000,2000) at cycle "
                    "%" PRIu64 "; same-seed rebuild reproduces it\n", landing);
    }

    // ---- 3. F5: permanent defect — fire() true at any cycle -------------
    {
        ChaOSTrigger t(ChaOSTier::F5, 42, 0, 0);
        for (int i = 0; i < 100; i++) {
            const uint64_t now = (uint64_t)i * 7919 + 3;  // arbitrary points
            if (!t.fire(now)) {
                std::printf("FAIL(3): F5 fire(%" PRIu64 ") returned false\n",
                            now);
                return 1;
            }
        }
        std::printf("PASS(3): F5 fire() true at all 100 probed cycles\n");
    }

    // ---- 4. F1 determinism: same seed -> identical fire sequence --------
    {
        static constexpr size_t kFires = 100;
        uint64_t a[kFires], b[kFires];
        if (!pollFireCycles(ChaOSTier::F1, 777, 0, 0, kFires, a) ||
            !pollFireCycles(ChaOSTier::F1, 777, 0, 0, kFires, b)) {
            std::printf("FAIL(4): F1 determinism run hit the cycle cap\n");
            return 1;
        }
        for (size_t i = 0; i < kFires; i++) {
            if (a[i] != b[i]) {
                std::printf("FAIL(4): F1 same-seed sequences differ at fire "
                            "#%zu: %" PRIu64 " vs %" PRIu64 "\n",
                            i, a[i], b[i]);
                return 1;
            }
        }
        std::printf("PASS(4): F1 same-seed sequences identical (100 fires)\n");
    }

    // ---- 5. F2/F3 interval magnitude spot check -------------------------
    {
        static constexpr size_t kFires = 101;  // -> 100 intervals each
        uint64_t fires[kFires];

        if (!pollFireCycles(ChaOSTier::F2, 424242, 0, 0, kFires, fires)) {
            std::printf("FAIL(5): F2 hit the cycle cap before %zu fires\n",
                        kFires);
            return 1;
        }
        for (size_t i = 1; i < kFires; i++) {
            const uint64_t iv = fires[i] - fires[i - 1];
            if (iv < 130000 || iv >= 390000) {
                std::printf("FAIL(5): F2 interval #%zu = %" PRIu64
                            " outside [130000, 390000)\n", i - 1, iv);
                return 1;
            }
        }
        const uint64_t mean2 = (fires[kFires - 1] - fires[0]) / (kFires - 1);

        if (!pollFireCycles(ChaOSTier::F3, 999983, 0, 0, kFires, fires)) {
            std::printf("FAIL(5): F3 hit the cycle cap before %zu fires\n",
                        kFires);
            return 1;
        }
        for (size_t i = 1; i < kFires; i++) {
            const uint64_t iv = fires[i] - fires[i - 1];
            if (iv < 13000 || iv >= 39000) {
                std::printf("FAIL(5): F3 interval #%zu = %" PRIu64
                            " outside [13000, 39000)\n", i - 1, iv);
                return 1;
            }
        }
        const uint64_t mean3 = (fires[kFires - 1] - fires[0]) / (kFires - 1);

        std::printf("PASS(5): F2 100 intervals all in [130000,390000), "
                    "mean = %" PRIu64 "; F3 100 intervals all in "
                    "[13000,39000), mean = %" PRIu64 "\n", mean2, mean3);
    }

    std::printf("CHAOS_TRIGGER_TEST PASS\n");
    return 0;
}
