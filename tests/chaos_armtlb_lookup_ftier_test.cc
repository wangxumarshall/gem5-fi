/*
 * chaos_armtlb_lookup_ftier_test.cc — standalone unit test for the
 * [R6-FIXCPP/B] armtlb LOOKUP-path F-tier polling. NOT part of the gem5
 * build; compiled directly:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_armtlb_lookup_ftier_test.cc -o /tmp/tlb_ftier \
 *       && /tmp/tlb_ftier
 *
 * Defect under test (the R6-FTIER contract, tests/test_lsu_ftier_armtlb_lookup.py):
 * the TLB lookup-HIT path (TLB::lookup -> CHAOSArmTLB::maybeCorrupt /
 * maybeCorruptLookup) NEVER polled lsuTrigger, so F1-F6 had no landed knob
 * there and every tier silently degraded to F0 (the six first-wave armtlb
 * RunIDs collapsed to three experimental conditions).
 *
 * This test drives the SAME trigger object the injector now polls
 * (ChaOSLsuTrigger, chaos_lsu_trigger.hh — the event-normalized tier source
 * shared with the walk path) over a synthetic eligible stream that mirrors
 * the lookup path (one eligible event per TLB-hit lookup) and pins:
 *   [1] F0 (legacy chain) fires ONCE, at the seed-varied skip position;
 *   [2] F2 fires MULTIPLE times, first fire inside the spec's ±50% window of
 *       the 100,000-eligible-event mean, and every interval inside it;
 *   [3] F6 (first-event tier) fires EXACTLY ONCE, executed AT the first
 *       eligible event (the TlbHit) — i.e. at index 0;
 *   [4] the three tiers fire at DIFFERENT positions;
 *   [5] all three are REPRODUCIBLE for a fixed seed (and the F0 legacy chain
 *       is reproducible through the injector's own seeded geometric skip).
 */
#include <cstdint>
#include <cstdio>
#include <random>
#include <string>
#include <vector>

#include "cpu/o3/chaos_lsu_trigger.hh"

// [LSU][OBS-3] standalone link fix (same as tests/chaos_lsu_trigger_test.cc):
// chaos_lsu_trigger.hh calls curTick(), which dereferences the gem5 TLS
// pointer the event queue maintains. Outside the gem5 build nothing defines
// it — define it here, pointed at a static tick, so the documented one-line
// build works.
namespace gem5 { namespace Gem5Internal {
__thread Tick *_curTickPtr;   // the definition a standalone TU lacks
} }
static gem5::Tick standalone_tick = 0;

using gem5::ChaOSLsuEvent;
using gem5::ChaOSLsuTier;
using gem5::ChaOSLsuTrigger;

static int failed = 0;

static void
check(const std::string &name, bool cond, const std::string &detail = "")
{
    if (cond) {
        std::printf("PASS %s\n", name.c_str());
    } else {
        std::printf("FAIL %s%s\n", name.c_str(),
                    detail.empty() ? "" : ("  [" + detail + "]").c_str());
        ++failed;
    }
}

// The injector's own legacy F0 chain (CHAOSArmTLB ctor): a seed-dependent
// geometric skip of eligible events before the single injection.
static uint64_t
legacyF0Skip(uint64_t seed)
{
    std::mt19937 rng;
    rng.seed(seed != 0 ? seed : 1);
    std::geometric_distribution<uint64_t> skip_dist(0.1);
    return skip_dist(rng);
}

// Fire positions (eligible-event indices) of `tier` over `n` eligible
// lookups, for one seed. The injector's lookup hook shape:
//   tiered run : onAttempt(); return onEligible()  [or onF6Event() for F6]
//   legacy F0  : the geometric skip budget then a single shot
static std::vector<uint64_t>
firePositions(ChaOSLsuTier tier, uint64_t seed, uint64_t warmup, uint64_t span,
              uint64_t n)
{
    std::vector<uint64_t> pos;
    if (tier == ChaOSLsuTier::F0) {
        const uint64_t skip = legacyF0Skip(seed);
        // one eligible lookup = one attempt; probability 1.0 in the
        // campaign, so the legacy chain injects once, after the skip budget.
        for (uint64_t i = 0; i < n; ++i) {
            if (i == skip) { pos.push_back(i); break; }
        }
        return pos;
    }
    ChaOSLsuTrigger tr(tier, seed, warmup, span);
    for (uint64_t i = 0; i < n; ++i) {
        tr.onAttempt();
        const bool fire = (tier == ChaOSLsuTier::F6)
            ? tr.onF6Event(false)   // the lookup hit IS the F6 event here
            : tr.onEligible();
        if (fire) pos.push_back(i);
    }
    return pos;
}

static std::string
join(const std::vector<uint64_t> &v)
{
    std::string s;
    for (size_t i = 0; i < v.size(); ++i)
        s += (i ? "," : "") + std::to_string(v[i]);
    return s;
}

int
main()
{
    // point the gem5 tick TLS at our static tick (see the definition above)
    gem5::Gem5Internal::_curTickPtr = &standalone_tick;

    const uint64_t N = 600000;      // >5 F2 intervals at 1e5 eligible events
    const uint64_t seed = 7;

    std::printf("[1] F0 (legacy chain): single transient, skip-gated\n");
    const auto f0 = firePositions(ChaOSLsuTier::F0, seed, 0, 1000, N);
    check("F0 injects exactly once", f0.size() == 1, join(f0));
    check("F0 lands at the injector's seeded geometric-skip position",
          !f0.empty() && f0[0] == legacyF0Skip(seed), join(f0));
    check("F0 position is not the first eligible event (skip > 0)",
          !f0.empty() && f0[0] > 0, join(f0));

    std::printf("[2] F2: mean 100,000 eligible events, +-50%% jitter\n");
    const auto f2 = firePositions(ChaOSLsuTier::F2, seed, 0, 0, N);
    check("F2 repeats (>1 injection over 600k eligible events)",
          f2.size() > 1, join(f2));
    check("F2's first fire is the mean-(skewed) draw, not the first event",
          !f2.empty() && f2[0] > 0, join(f2));
    {
        bool in_window = !f2.empty();
        for (size_t k = 0; k < f2.size(); ++k) {
            const uint64_t prev = k ? f2[k - 1] : 0;
            const uint64_t gap = f2[k] - prev;
            // mean 1e5, interval U[iv/2, 3*iv/2) = [50000, 150000)
            if (gap < 50000 || gap >= 150000) in_window = false;
        }
        check("every F2 interval is inside [50k,150k) (spec jitter)",
              in_window, join(f2));
    }
    {
        // warm-up is an eligible-event count: with warmup=100000 the first
        // fire cannot precede index 100000 + iv/2 = 150000.
        const auto warmed = firePositions(ChaOSLsuTier::F2, seed, 100000, 0, N);
        check("F2 respects warm-up (first fire >= warmup + iv/2)",
              !warmed.empty() && warmed[0] >= 150000, join(warmed));
    }

    std::printf("[3] F6: exactly once, AT the first eligible event\n");
    const auto f6 = firePositions(ChaOSLsuTier::F6, seed, 0, 0, N);
    check("F6 injects exactly once", f6.size() == 1, join(f6));
    check("F6 lands at eligible index 0 (the first TlbHit)",
          !f6.empty() && f6[0] == 0, join(f6));

    std::printf("[4] the three tiers fire at DIFFERENT positions\n");
    check("F0 != F2 (first fire)", f0 != f2, join(f0) + " vs " + join(f2));
    check("F0 != F6", f0 != f6, join(f0) + " vs " + join(f6));
    check("F2 != F6", f2 != f6, join(f2) + " vs " + join(f6));

    std::printf("[5] fixed seed -> reproducible positions\n");
    check("F0 reproducible", firePositions(ChaOSLsuTier::F0, seed, 0, 1000, N)
          == f0);
    check("F2 reproducible", firePositions(ChaOSLsuTier::F2, seed, 0, 0, N)
          == f2);
    check("F6 reproducible", firePositions(ChaOSLsuTier::F6, seed, 0, 0, N)
          == f6);
    check("a different seed moves F2 (the draw is really seeded)",
          firePositions(ChaOSLsuTier::F2, seed + 1, 0, 0, N) != f2);

    std::printf("[6] funnel accounting is consistent (04 L0)\n");
    {
        ChaOSLsuTrigger tr(ChaOSLsuTier::F2, seed, 0, 0);
        const auto pos = firePositions(ChaOSLsuTier::F2, seed, 0, 0, N);
        for (uint64_t i = 0; i < N; ++i) {
            tr.onAttempt();
            tr.onEligible();
        }
        check("attempted == eligible == the stream length",
              tr.attempted == N && tr.eligible == N,
              std::to_string(tr.attempted) + "/" + std::to_string(tr.eligible));
        check("injected == the number of fire positions",
              tr.injected == pos.size(),
              std::to_string(tr.injected) + " vs " + std::to_string(pos.size()));
    }
    {
        ChaOSLsuTrigger tr(ChaOSLsuTier::F6, seed, 0, 0);
        tr.onAttempt();
        const bool fired = tr.onF6Event(false);
        for (uint64_t i = 1; i < 1000; ++i) {
            tr.onAttempt();
            tr.onF6Event(false);
        }
        // Every lookup books one attempt (the injector's hook shape); the F6
        // firing must NOT book a second one (book_attempt=false), and it
        // counts exactly one eligible event / one injection.
        check("F6: 1000 attempts, 1 eligible event, 1 injection "
              "(no double-counted attempt)",
              fired && tr.attempted == 1000 && tr.eligible == 1
              && tr.injected == 1,
              std::to_string(tr.attempted) + "/" + std::to_string(tr.eligible)
              + "/" + std::to_string(tr.injected));
    }

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
