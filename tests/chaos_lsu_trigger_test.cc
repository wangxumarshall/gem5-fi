// chaos_lsu_trigger_test.cc — standalone unit test for the LSU event-
// normalized trigger tiers (docs/gem5-fi/lsu/05 r2-r8), OUTSIDE the gem5
// build (same pattern as tests/chaos_trigger_test.cc for the ooo trigger).
// Compiles chaos_lsu_trigger.hh standalone (its only deps are <cstdint>,
// <cstdio> and the header-only chaosSampleLCG in chaos_event_sample.hh).
//
// Build: g++ -std=c++17 -I CHAOS/gem5/src tests/chaos_lsu_trigger_test.cc -o /tmp/lsu_trig
// Run:   /tmp/lsu_trig   → prints one PASS line per assertion group.
#include <cstdio>
#include <cstdlib>
#include <vector>

#include "cpu/o3/chaos_lsu_trigger.hh"

using gem5::ChaOSLsuTier;
using gem5::ChaOSLsuEvent;
using gem5::ChaOSLsuTrigger;

static int failures = 0;
#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("FAIL: %s\n", msg); ++failures; } \
} while (0)

int
main()
{
    // ---- F0: single uniform shot after warm-up (05 r2) ----
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F0, /*seed*/42, /*warmup*/100,
                          /*span*/1000);
        int fires = 0;
        uint64_t last_eligible = 0;
        for (uint64_t i = 0; i < 5000; ++i) {
            t.onAttempt();
            if (t.onEligible()) { ++fires; last_eligible = i + 1; }
        }
        CHECK(fires == 1, "F0 fires exactly once");
        CHECK(last_eligible >= 101 && last_eligible <= 1100,
              "F0 lands in [warmup+1, warmup+span]");
    }

    // ---- F1/F2/F3: mean interval 1M/100K/10K eligible events (05 r3-r5) ----
    // ±50% jitter per interval; over many intervals the count must land in a
    // generous [0.4x, 2.5x] band around the mean (statistical sanity, not a
    // tight CI — the tier's law is per-interval, checked exactly below).
    {
        const struct { ChaOSLsuTier t; uint64_t iv; } cases[] = {
            {ChaOSLsuTier::F1, 1000000}, {ChaOSLsuTier::F2, 100000},
            {ChaOSLsuTier::F3, 10000}};
        for (auto &c : cases) {
            ChaOSLsuTrigger t(c.t, 7, 1000, 0);
            uint64_t n = 40 * c.iv;         // 40 mean intervals
            uint64_t fires = 0;
            for (uint64_t i = 0; i < n; ++i) { t.onAttempt(); t.onEligible(); }
            fires = t.injected;
            double rate = (double)fires / ((double)n / (double)c.iv);
            CHECK(rate > 0.4 && rate < 2.5, "F1/F2/F3 rate band");
            printf("  tier=F%d events=%lu injected=%lu (mean-intervals=%.1f)\n",
                   static_cast<int>(c.t), (unsigned long)n,
                   (unsigned long)fires, rate);
        }
    }

    // ---- F4: bursts of 2-4 consecutive eligible events (05 r6) ----
    // A burst = back-to-back injections with NO non-injected eligible event
    // in between; track the eligible index at each fire to reconstruct.
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F4, 99, 100, 0);
        const uint64_t n = 1000000;
        std::vector<uint64_t> fire_idx;
        for (uint64_t i = 0; i < n; ++i) {
            t.onAttempt();
            if (t.onEligible()) fire_idx.push_back(i);
        }
        std::vector<uint64_t> bursts;
        uint64_t cur = 1;
        for (size_t k = 1; k < fire_idx.size(); ++k) {
            if (fire_idx[k] == fire_idx[k - 1] + 1) ++cur;
            else { bursts.push_back(cur); cur = 1; }
        }
        if (!fire_idx.empty()) bursts.push_back(cur);
        bool all_24 = true;
        for (uint64_t b : bursts) if (b < 2 || b > 4) all_24 = false;
        CHECK(all_24, "F4 every burst length in [2,4]");
        CHECK(!bursts.empty() && bursts.size() >= 3, "F4 >=3 bursts in 1M events");
        printf("  F4 bursts(%lu):", (unsigned long)bursts.size());
        for (uint64_t b : bursts) printf(" %lu", (unsigned long)b);
        printf("\n");
    }

    // ---- F5: permanent from first post-warm-up eligible event (05 r7-note;
    //      05 r2-r8 F5) — every eligible event after warm-up injects ----
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F5, 5, 100, 0);
        uint64_t fires = 0;
        for (uint64_t i = 0; i < 1000; ++i) { t.onAttempt(); if (t.onEligible()) ++fires; }
        CHECK(fires == 900, "F5 injects on every eligible event after warm-up");
        CHECK(t.eligible == 1000 && t.attempted == 1000, "F5 funnel counts");
    }

    // ---- F6: first occurrence of the configured event, once ever (05 r7) ----
    // CONTRACT: onF6Event() means "the CONFIGURED event just occurred" — the
    // event-TYPE filtering is the consumer's thunk (CHAOSAddrPath::f6Thunk
    // checks f6_event == ev before calling; proven end-to-end in the gem5 F6
    // run: eligible stream + other event types never fired it).
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F6, 11, 0, 0,
                          gem5::ChaOSLsuEvent::SqForward);
        // eligible stream never fires F6
        for (int i = 0; i < 100; ++i) { t.onAttempt(); t.onEligible(); }
        CHECK(t.injected == 0, "F6 ignores the eligible stream");
        // configured event: fires once, then never again
        CHECK(t.onF6Event(), "F6 fires on the first configured event");
        CHECK(t.injected == 1, "F6 injected==1 after first event");
        CHECK(!t.onF6Event(), "F6 fires once ever");
        CHECK(t.injected == 1, "F6 still 1 after repeat");
        CHECK(t.attempted == 101 && t.eligible == 101,
              "F6 funnel: 100 stream + 1 event");
    }

    if (failures == 0) {
        printf("LSU TRIGGER TEST: ALL PASSED\n");
        return 0;
    }
    printf("LSU TRIGGER TEST: %d FAILURES\n", failures);
    return 1;
}
