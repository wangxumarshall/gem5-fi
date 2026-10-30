// chaos_lsu_s10_accounting_test.cc — standalone unit test for the F5
// fire/outcome separation used by the S10 SSIT-substitution site.
//
// Defect pinned (2026-10-30): onEligible() on F5 only increments `fires`;
// the injector MUST report each fire's outcome via noteOutcome(). The S10
// subst site never did, so trigger.injected stayed 0 while the injection
// log and stats both recorded 3 real writes.
//
// Build: g++ -std=c++17 -I CHAOS/gem5/src tests/chaos_lsu_s10_accounting_test.cc -o /tmp/s10_acct
// Run:   /tmp/s10_acct
#include <cstdio>
#include <vector>

#include "cpu/o3/chaos_lsu_trigger.hh"

namespace gem5 { namespace Gem5Internal {
__thread Tick *_curTickPtr;
} }
static gem5::Tick standalone_tick = 0;

using gem5::ChaOSLsuTier;
using gem5::ChaOSLsuTrigger;

static int failures = 0;
#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("FAIL: %s\n", msg); ++failures; } \
} while (0)

int
main()
{
    gem5::Gem5Internal::_curTickPtr = &standalone_tick;

    // 1) Reported path: every F5 fire reports a real write.
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F5, /*seed*/7, /*warmup*/0,
                          /*span*/0);
        uint64_t fires = 0;
        for (int i = 0; i < 3; ++i) {
            t.onAttempt();
            if (t.onEligible()) {
                ++fires;
                t.noteOutcome(true);       // the S10 fix's contract
            }
        }
        CHECK(fires == 3, "three F5 fires");
        CHECK(t.fires == 3, "trigger.fires == 3");
        CHECK(t.outcomes_recorded == 3, "outcomes_recorded == 3");
        CHECK(t.injected == 3, "injected == 3");
        CHECK(t.no_effect == 0, "no_effect == 0");
        CHECK(t.fires == t.injected + t.no_effect,
              "fires == injected + no_effect");
        printf("PASS fires==injected+no_effect\n");
    }

    // 2) Unreported path: the defect is structurally detectable.
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F5, /*seed*/7, /*warmup*/0,
                          /*span*/0);
        for (int i = 0; i < 3; ++i) {
            t.onAttempt();
            if (t.onEligible()) { /* BUG: no noteOutcome */ }
        }
        CHECK(t.fires == 3, "unreported: fires counted");
        CHECK(t.injected == 0, "unreported: injected stayed 0");
        CHECK(t.outcomes_recorded != t.fires,
              "unreported: accounting mismatch is visible");
        printf("PASS unreported-detected\n");
    }

    // 3) No-effect path: a refused write must not be counted as injected.
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F5, /*seed*/7, /*warmup*/0,
                          /*span*/0);
        t.onAttempt();
        if (t.onEligible()) t.noteOutcome(false);
        CHECK(t.fires == 1 && t.injected == 0 && t.no_effect == 1,
              "no-effect fire recorded as no_effect, not injected");
    }

    // 4) Non-F5 tiers keep fire-time injected accounting (no double count).
    {
        ChaOSLsuTrigger t(ChaOSLsuTier::F2, /*seed*/7, /*warmup*/0,
                          /*span*/0);
        uint64_t fires = 0;
        for (uint64_t i = 0; i < 500000 && fires < 3; ++i) {
            t.onAttempt();
            if (t.onEligible()) ++fires;
        }
        CHECK(fires > 0, "F2 fires within its interval");
        CHECK(t.injected > 0, "F2 injected counted at fire time");
        CHECK(t.outcomes_recorded == 0,
              "F2 does not use outcome reporting");
    }

    if (failures) { printf("FAILURES: %d\n", failures); return 1; }
    printf("ALL PASS\n");
    return 0;
}
