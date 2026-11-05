// Host test: FQ08-c delayed-wake TARGET-STATE checks (no gem5).
//
// The offline Python replica of chaos_iq_lifecycle.hh checks the decision
// function only.  This test additionally models the thing the decision is
// supposed to protect: a dependent's ready state.  It proves that
//
//   * Fire really changes the target state (dependent ready=false -> true,
//     wakeDependents called exactly once);
//   * squash, identity mismatch and generation change DO NOT change the
//     target state and DO NOT call wakeDependents;
//   * a stale event whose destination physical slot was freed and reallocated
//     cannot wake the dependent of the new owner (the old event is checked
//     before any state mutation);
//   * each processed event advances exactly one observable counter, and when
//     every scheduled event has been processed
//     scheduled == fired + ignored_* (the exit-summary conservation law).
//
// The header included here is the exact header the gem5-side CHAOSIQ.cc
// calls, so this is host evidence for the real model code, not a copy.
//
// Build/run:
//   g++ -O0 -std=c++17 -Wall -Wextra -Werror
//       -I CHAOS/gem5/src/cpu/o3/CHAOSIQ
//       tests/unit/fq08c_delayed_wake_target_state_test.cc
//       -o /tmp/fq08c_target_state && /tmp/fq08c_target_state
//
// Exit code 0 = all checks pass.

#include <cstdint>
#include <cstdio>
#include <utility>
#include <vector>

#include "chaos_iq_lifecycle.hh"

using namespace gem5::chaos_iq_lifecycle;

static int failures = 0;

static void
check(const char *name, bool ok)
{
    std::printf("  %s %s\n", ok ? "PASS" : "FAIL", name);
    if (!ok)
        ++failures;
}

// ---------------------------------------------------------------------------
// Minimal target machine
// ---------------------------------------------------------------------------

struct Dependent
{
    uint64_t sn = 0;
    bool ready = false;
};

struct Producer
{
    uint64_t seq_num = 0;
    unsigned tid = 0;
    bool squashed = false;
    std::vector<DestStamp> dests;
};

struct TargetIQ
{
    std::vector<Dependent> deps;
    int wake_calls = 0;

    void
    wakeDependents(const Producer &p)
    {
        ++wake_calls;
        // A real wake only touches the dependents of THIS producer; the
        // host model has exactly one such dependent, whose ready bit is the
        // observable target state.
        for (auto &d : deps)
            d.ready = true;
        (void)p;
    }
};

static WakeStamp
make_stamp(uint64_t sn, unsigned tid,
           std::vector<DestStamp> dests)
{
    WakeStamp s;
    s.seq_num = sn;
    s.tid = tid;
    s.dests = std::move(dests);
    return s;
}

// Mirrors CHAOSIQ::DelayedWake::process(): classify first, act only on Fire.
static WakeDecision
process_event(const WakeStamp &stamp, const Producer *inst, TargetIQ &iq,
              DelayedWakeCounters &c)
{
    WakeObserved now;
    now.has_inst = (inst != nullptr);
    if (inst) {
        now.seq_num = inst->seq_num;
        now.tid = inst->tid;
        now.squashed = inst->squashed;
        now.dests = inst->dests;
    }

    const WakeDecision d = classifyWake(stamp, now);
    noteWakeDecision(c, d);
    if (d == WakeDecision::Fire)
        iq.wakeDependents(*inst);
    return d;
}

// ---------------------------------------------------------------------------
// Checks
// ---------------------------------------------------------------------------

static void
test_fire_really_changes_target_state()
{
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}, {97, 5}});
    Producer p;
    p.seq_num = 4242;
    p.tid = 0;
    p.dests = s.dests;

    TargetIQ iq;
    iq.deps.push_back({311, false});
    DelayedWakeCounters c;

    const WakeDecision d = process_event(s, &p, iq, c);
    check("unsquashed producer fires", d == WakeDecision::Fire);
    check("fire calls wakeDependents exactly once", iq.wake_calls == 1);
    check("fire changes dependent ready state false -> true",
          iq.deps.size() == 1 && iq.deps[0].ready);
    check("fire increments fired counter", c.fired == 1);
    check("fire increments no ignored counter",
          c.ignored_no_inst == 0 && c.ignored_identity == 0 &&
          c.ignored_squashed == 0 && c.ignored_generation == 0);
}

static void
test_squash_leaves_target_state_unchanged()
{
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}});
    Producer p;
    p.seq_num = 4242;
    p.dests = s.dests;
    p.squashed = true;

    TargetIQ iq;
    iq.deps.push_back({311, false});
    DelayedWakeCounters c;

    const WakeDecision d = process_event(s, &p, iq, c);
    check("squashed producer ignored", d == WakeDecision::IgnoreSquashed);
    check("squash does not call wakeDependents", iq.wake_calls == 0);
    check("squash leaves dependent ready=false", !iq.deps[0].ready);
    check("squash increments only ignored_squashed",
          c.ignored_squashed == 1 && c.fired == 0);
}

static void
test_generation_realloc_cannot_wake_new_owner()
{
    // The SAME instruction object is still alive (DynInstPtr refcount), but
    // its destination physical cell was freed at commit and reallocated to a
    // new producer: the live generation is one older than the snapshot.
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}});
    Producer p;
    p.seq_num = 4242;
    p.tid = 0;
    p.dests = {{96, 4}};        // new allocation generation
    p.squashed = false;

    TargetIQ iq;
    iq.deps.push_back({311, false});      // dependent of the NEW owner
    DelayedWakeCounters c;

    const WakeDecision d = process_event(s, &p, iq, c);
    check("freed/reallocated dest ignored", d == WakeDecision::IgnoreGeneration);
    check("stale event does not wake the new owner", iq.wake_calls == 0);
    check("stale event leaves the new owner's dependent not ready",
          !iq.deps[0].ready);
    check("generation mismatch increments only ignored_generation",
          c.ignored_generation == 1 && c.fired == 0);
}

static void
test_identity_mismatch_cannot_wake_another_instruction()
{
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}});

    TargetIQ iq;
    iq.deps.push_back({999, false});
    DelayedWakeCounters c;

    Producer other;
    other.seq_num = 999;
    other.tid = 0;
    other.dests = {{96, 3}};       // same flat+generation, different producer
    check("different seqNum ignored",
          process_event(s, &other, iq, c) == WakeDecision::IgnoreIdentity);

    Producer other_tid = other;
    other_tid.seq_num = 4242;
    other_tid.tid = 1;
    check("different tid ignored",
          process_event(s, &other_tid, iq, c) == WakeDecision::IgnoreIdentity);

    Producer fewer_dests;
    fewer_dests.seq_num = 4242;
    fewer_dests.tid = 0;
    fewer_dests.dests = {{96, 3}, {97, 5}};
    const WakeStamp two = make_stamp(4242, 0, {{96, 3}, {97, 5}});
    fewer_dests.dests.pop_back();
    check("dest-count mismatch ignored",
          process_event(two, &fewer_dests, iq, c) ==
              WakeDecision::IgnoreIdentity);

    check("identity mismatches never touch target state",
          iq.wake_calls == 0 && !iq.deps[0].ready);
    check("identity counter moved for each mismatch",
          c.ignored_identity == 3 && c.fired == 0);
}

static void
test_every_destination_must_match()
{
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}, {97, 5}});
    Producer p;
    p.seq_num = 4242;
    p.dests = {{96, 3}, {97, 6}};      // only the second dest moved

    TargetIQ iq;
    iq.deps.push_back({311, false});
    DelayedWakeCounters c;

    check("one stale destination rejects the whole event",
          process_event(s, &p, iq, c) == WakeDecision::IgnoreGeneration);
    check("partial generation match does not wake", iq.wake_calls == 0 &&
          !iq.deps[0].ready);
}

static void
test_identity_is_checked_before_squash()
{
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}});
    Producer p;
    p.seq_num = 4243;               // different instruction
    p.squashed = true;              // and dead
    p.dests = {{96, 9}};            // and its slot was reused

    TargetIQ iq;
    DelayedWakeCounters c;
    check("identity wins over squash/generation",
          process_event(s, &p, iq, c) == WakeDecision::IgnoreIdentity);
    check("identity-first still never wakes", iq.wake_calls == 0);
    check("identity-first increments ignored_identity only",
          c.ignored_identity == 1 && c.ignored_squashed == 0 &&
          c.ignored_generation == 0);
}

static void
test_squash_then_reuse_then_new_event_fires()
{
    // One stale event sees squash; later the slot is reused (generation
    // bump). The stale event is still dead, but a DIFFERENT, current event
    // must still fire and change the target state.
    const WakeStamp stale = make_stamp(100, 0, {{96, 3}});
    DelayedWakeCounters c;
    TargetIQ iq;
    iq.deps.push_back({200, false});

    Producer squashed;
    squashed.seq_num = 100;
    squashed.dests = {{96, 3}};
    squashed.squashed = true;
    process_event(stale, &squashed, iq, c);

    Producer reused;
    reused.seq_num = 100;
    reused.dests = {{96, 4}};
    process_event(stale, &reused, iq, c);
    check("old event never wakes after squash/reuse", iq.wake_calls == 0 &&
          !iq.deps[0].ready);

    const WakeStamp fresh = make_stamp(101, 0, {{97, 1}});
    Producer live;
    live.seq_num = 101;
    live.dests = {{97, 1}};
    const WakeDecision d = process_event(fresh, &live, iq, c);
    check("separate current event still fires", d == WakeDecision::Fire);
    check("separate current event changes target state",
          iq.wake_calls == 1 && iq.deps[0].ready);
    check("counter accounting after squash+reuse+fire",
          c.fired == 1 && c.ignored_squashed == 1 &&
          c.ignored_generation == 1);
}

static void
test_one_counter_per_event_and_drained_conservation()
{
    const WakeStamp s = make_stamp(4242, 0, {{96, 3}});
    DelayedWakeCounters c;
    TargetIQ iq;
    iq.deps.push_back({311, false});
    uint64_t scheduled = 0;

    auto schedule = [&](const Producer *p) {
        ++scheduled;                       // CHAOSIQ::shouldOmitWake
        process_event(s, p, iq, c);        // DelayedWake::process
    };

    Producer live;
    live.seq_num = 4242;
    live.dests = {{96, 3}};
    schedule(&live);                       // Fire

    Producer squashed = live;
    squashed.squashed = true;
    schedule(&squashed);                   // Squashed

    Producer reused = live;
    reused.dests = {{96, 4}};
    schedule(&reused);                     // Generation

    Producer other = live;
    other.seq_num = 9;
    schedule(&other);                      // Identity

    schedule(nullptr);                     // NoInst

    const uint64_t processed = c.fired + c.ignored_no_inst +
                               c.ignored_identity + c.ignored_squashed +
                               c.ignored_generation;
    check("one decision per processed event", processed == 5);
    check("each reason counted exactly once",
          c.fired == 1 && c.ignored_no_inst == 1 &&
          c.ignored_identity == 1 && c.ignored_squashed == 1 &&
          c.ignored_generation == 1);
    check("drained run: scheduled == fired + ignored_*", scheduled == processed);
    check("drained run: one fire changed target state", iq.wake_calls == 1 &&
          iq.deps[0].ready);
}

int
main()
{
    std::printf("FQ08-c delayed-wake target-state host test\n");

    std::printf("[positive] unsquashed event fires and changes state\n");
    test_fire_really_changes_target_state();

    std::printf("[negative] squash / generation / identity are no-ops\n");
    test_squash_leaves_target_state_unchanged();
    test_generation_realloc_cannot_wake_new_owner();
    test_identity_mismatch_cannot_wake_another_instruction();
    test_every_destination_must_match();
    test_identity_is_checked_before_squash();

    std::printf("[lifecycle] stale event cannot resurrect; new event fires\n");
    test_squash_then_reuse_then_new_event_fires();
    test_one_counter_per_event_and_drained_conservation();

    if (failures == 0) {
        std::printf("ALL FQ08-C TARGET-STATE CHECKS PASSED\n");
        return 0;
    }
    std::printf("%d CHECK(S) FAILED\n", failures);
    return 1;
}
