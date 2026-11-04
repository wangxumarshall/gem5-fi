// Host unit test: §2.5 FQ08-b / FQ08-c CHAOSIQ lifecycle model.
//
// Build/run (no gem5, no workload):
//   g++ -O0 -std=c++17 -Wall -Wextra -Werror
//       -I CHAOS/gem5/src/cpu/o3/CHAOSIQ
//       tests/unit/chaos_iq_lifecycle_test.cc -o /tmp/chaos_iq_lifecycle
//       && /tmp/chaos_iq_lifecycle
//
// Exit code 0 = all checks pass.
//
// What this pins:
//
// FQ08-b (no victim yet counted as an injection):
//   * the gate hit only records an ATTEMPT — eligible / attempted / applied /
//     activated are separate counters;
//   * an attempt whose wake produced no dependent, or no eligible victim, is
//     dropped as no_victim WITHOUT touching applied/activated and WITHOUT
//     consuming the max_faults budget;
//   * a real victim gets exactly one wrong-source ready write; activated is a
//     strict subset of applied (the write alone completed the ready count).
//   The "REPRO" sections below model the OLD gate behaviour (count at gate
//   time) side by side, so the over-count is visible in the same run.
//
// FQ08-c (delayed wake vs squash / slot reuse):
//   * a normal delayed wake re-issues (Fire);
//   * a producer squashed inside the delay window is ignored;
//   * a destination physical register freed/reallocated (generation bump) is
//     ignored — the event never touches the new occupant's dependents;
//   * identity mismatch / missing instruction is ignored;
//   * every ignored event increments exactly one observable counter, and the
//     simulated wakeDependents() call count stays 0.

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "chaos_iq_lifecycle.hh"

using namespace gem5::chaos_iq_lifecycle;

static int failures = 0;

#define CHECK(cond)                                                          \
    do {                                                                     \
        if (!(cond)) {                                                       \
            std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__,     \
                         #cond);                                             \
            ++failures;                                                      \
        }                                                                    \
    } while (0)

static void
check(const char *name, bool ok)
{
    std::printf("  %s %s\n", ok ? "PASS" : "FAIL", name);
    if (!ok)
        ++failures;
}

// ---------------------------------------------------------------------------
// FQ08-b
// ---------------------------------------------------------------------------

static void
test_no_victim_does_not_apply()
{
    Counters c;
    Attempt a;

    // One producer wake reaches the gate (eligible + probability hit).
    ++c.eligible;
    beginAttempt(a, /*producer_sn=*/100, /*tid=*/0, /*tick=*/500);
    ++c.attempted;

    // REPRO of the old behaviour: faults_injected_count++ happened HERE, in
    // the gate, so the run reported an injection even though the wake had no
    // dependent and nothing was modified.
    const uint64_t old_faults_injected = 1;
    check("REPRO old gate counts 1 injection with no victim",
          old_faults_injected == 1);

    // The wake ends with no dependent: the attempt is dropped.
    const bool dropped = abortPendingAttempt(a, c);
    check("attempt dropped", dropped);
    check("no applied", c.applied == 0);
    check("no activated", c.activated == 0);
    check("no_victim counted", c.no_victim == 1);
    // The fixed model's injection count is the applied count: 0, not 1.
    const uint64_t new_faults_injected = c.applied;
    check("REPRO fixed model counts 0 injections", new_faults_injected == 0);
}

static void
test_only_the_woken_chain_is_not_a_victim()
{
    Counters c;
    Attempt a;
    beginAttempt(a, 101, 0, 600);
    ++c.attempted;

    // One target-class unready source, and it IS the chain being woken: this
    // wake is not "wrong" for this dependent -> no victim.
    VictimView v;
    v.ready_regs = 1;
    v.num_src_regs = 2;
    v.slot = {0};
    v.flat = {7};
    v.unready = {1};

    check("chain slot rejected as victim", chooseWrongSlot(v, 7) == -1);
    CHECK(abortPendingAttempt(a, c));
    check("no victim => no applied", c.applied == 0);
}

static void
test_positive_victim_applies_and_activates()
{
    Counters c;
    Attempt a;
    beginAttempt(a, 102, 0, 700);
    ++c.attempted;

    // Two unready target-class sources: slot 0 waits on the woken chain
    // (flat 100), slot 1 is a different source (flat 200). The wrong-source
    // wake must pick slot 1, not the legitimate chain slot.
    VictimView v;
    v.ready_regs = 0;
    v.num_src_regs = 2;
    v.slot = {0, 1};
    v.flat = {100, 200};
    v.unready = {1, 1};

    const int slot = chooseWrongSlot(v, 100);
    check("wrong source slot chosen", slot == 1);
    check("legitimate chain slot not chosen", slot != 0);

    // Simulate the write: ready count 0 -> 1 (of 2) is not issueable.
    bool issueable_before = false;
    bool issueable_after = (v.ready_regs + 1 == v.num_src_regs);
    check("one wake short is not issueable", !issueable_after);
    ApplyOutcome o = noteApplied(c, issueable_before, issueable_after);
    check("applied", o.applied && c.applied == 1);
    check("not activated (still one wake short)", !o.activated &&
                                                 c.activated == 0);
}

static void
test_victim_with_last_unready_slot_activates()
{
    Counters c;
    Attempt a;
    beginAttempt(a, 103, 0, 800);
    ++c.attempted;

    // Two sources, exactly one already ready; the only unready target-class
    // slot is wrong relative to the chain -> our write completes it.
    VictimView v;
    v.ready_regs = 1;
    v.num_src_regs = 2;
    v.slot = {0};
    v.flat = {200};
    v.unready = {1};

    const int slot = chooseWrongSlot(v, 100);
    check("wrong slot chosen when chain differs", slot == 0);

    bool issueable_before = false;
    bool issueable_after = (v.ready_regs + 1 == v.num_src_regs);
    check("wrong write makes victim issueable", issueable_after);
    ApplyOutcome o = noteApplied(c, issueable_before, issueable_after);
    check("applied", o.applied && c.applied == 1);
    check("activated", o.activated && c.activated == 1);
}

static void
test_squashed_and_fully_ready_victims_rejected()
{
    VictimView squashed;
    squashed.squashed = true;
    squashed.ready_regs = 0;
    squashed.num_src_regs = 2;
    squashed.slot = {0};
    squashed.flat = {200};
    squashed.unready = {1};
    check("squashed victim rejected", chooseWrongSlot(squashed, 100) == -1);

    VictimView ready;
    ready.ready_regs = 2;
    ready.num_src_regs = 2;
    ready.slot = {0};
    ready.flat = {200};
    ready.unready = {0};
    check("fully-ready victim rejected", chooseWrongSlot(ready, 100) == -1);

    VictimView issued;
    issued.issued = true;
    issued.ready_regs = 1;
    issued.num_src_regs = 2;
    issued.slot = {0};
    issued.flat = {200};
    issued.unready = {1};
    check("already-issued victim rejected", chooseWrongSlot(issued, 100) == -1);
}

static void
test_budget_only_consumed_on_apply()
{
    // Three gate hits with no victim must leave the fault budget at 0; the
    // fourth attempt with a victim consumes exactly one unit.
    Counters c;
    Attempt a;
    uint64_t budget = 0;

    for (int i = 0; i < 3; ++i) {
        ++c.attempted;
        beginAttempt(a, 200 + i, 0, 900 + i);
        VictimView empty;   // no target-class unready source
        empty.ready_regs = empty.num_src_regs = 1;
        if (chooseWrongSlot(empty, 0) < 0) {
            abortPendingAttempt(a, c);
        } else {
            ++budget;
        }
    }
    check("three no-victim attempts consumed no budget", budget == 0);
    check("three no_victim", c.no_victim == 3);
    check("still no applied", c.applied == 0);

    VictimView v;
    v.ready_regs = 1;
    v.num_src_regs = 2;
    v.slot = {0};
    v.flat = {300};
    v.unready = {1};
    ++c.attempted;
    beginAttempt(a, 300, 0, 1000);
    if (chooseWrongSlot(v, 100) >= 0) {
        ApplyOutcome o = noteApplied(c, false, true);
        if (o.applied)
            ++budget;
    }
    check("victim attempt consumed exactly one budget unit", budget == 1);
    check("attempted=4 applied=1", c.attempted == 4 && c.applied == 1);
}

// ---------------------------------------------------------------------------
// FQ08-c
// ---------------------------------------------------------------------------

static WakeStamp
make_stamp()
{
    WakeStamp s;
    s.seq_num = 4242;
    s.tid = 0;
    s.dests = {{/*flat=*/96, /*generation=*/3}, {/*flat=*/97, /*generation=*/5}};
    return s;
}

static WakeObserved
make_now(const WakeStamp &s)
{
    WakeObserved n;
    n.has_inst = true;
    n.seq_num = s.seq_num;
    n.tid = s.tid;
    n.squashed = false;
    n.dests = s.dests;
    return n;
}

static void
test_normal_delayed_wake_fires()
{
    const WakeStamp s = make_stamp();
    const WakeObserved n = make_now(s);
    const WakeDecision d = classifyWake(s, n);
    check("normal delayed wake fires", d == WakeDecision::Fire);
    check("decision name", std::string(wakeDecisionName(d)) == "fire");

    DelayedWakeCounters dw;
    noteWakeDecision(dw, d);
    check("fired counter", dw.fired == 1);
    check("no ignored counter moved",
          dw.ignored_squashed == 0 && dw.ignored_generation == 0 &&
          dw.ignored_identity == 0 && dw.ignored_no_inst == 0);

    // Simulate process(): only Fire may call wakeDependents.
    int wake_calls = (d == WakeDecision::Fire) ? 1 : 0;
    check("wakeDependents called exactly once", wake_calls == 1);
}

static void
test_squashed_producer_is_ignored()
{
    const WakeStamp s = make_stamp();
    WakeObserved n = make_now(s);
    n.squashed = true;

    const WakeDecision d = classifyWake(s, n);
    check("squashed producer ignored", d == WakeDecision::IgnoreSquashed);

    DelayedWakeCounters dw;
    noteWakeDecision(dw, d);
    check("ignored_squashed counter", dw.ignored_squashed == 1);
    int wake_calls = (d == WakeDecision::Fire) ? 1 : 0;
    check("squash => wakeDependents NOT called", wake_calls == 0);
}

static void
test_freed_slot_generation_is_ignored()
{
    const WakeStamp s = make_stamp();
    WakeObserved n = make_now(s);
    // The producer's destination physical register was freed (or freed and
    // reallocated): allocation generation moved on.
    n.dests[0].generation = s.dests[0].generation + 1;

    const WakeDecision d = classifyWake(s, n);
    check("freed/reused slot ignored", d == WakeDecision::IgnoreGeneration);

    DelayedWakeCounters dw;
    noteWakeDecision(dw, d);
    check("ignored_generation counter", dw.ignored_generation == 1);
    int wake_calls = (d == WakeDecision::Fire) ? 1 : 0;
    check("reused slot => new owner is NOT woken", wake_calls == 0);
}

static void
test_second_dest_generation_mismatch_is_ignored()
{
    const WakeStamp s = make_stamp();
    WakeObserved n = make_now(s);
    n.dests[1].generation = 6;   // only the second destination moved

    check("all destinations must match",
          classifyWake(s, n) == WakeDecision::IgnoreGeneration);
}

static void
test_identity_mismatch_is_ignored()
{
    const WakeStamp s = make_stamp();
    WakeObserved n = make_now(s);
    n.seq_num = s.seq_num + 1;
    check("sequence mismatch ignored",
          classifyWake(s, n) == WakeDecision::IgnoreIdentity);

    WakeObserved t = make_now(s);
    t.tid = 1;
    check("thread mismatch ignored",
          classifyWake(s, t) == WakeDecision::IgnoreIdentity);

    WakeObserved u = make_now(s);
    u.dests.pop_back();
    check("dest-count mismatch ignored",
          classifyWake(s, u) == WakeDecision::IgnoreIdentity);
}

static void
test_missing_instruction_is_ignored()
{
    const WakeStamp s = make_stamp();
    WakeObserved n;
    n.has_inst = false;
    check("missing instruction ignored",
          classifyWake(s, n) == WakeDecision::IgnoreNoInst);

    DelayedWakeCounters dw;
    noteWakeDecision(dw, WakeDecision::IgnoreNoInst);
    check("ignored_no_inst counter", dw.ignored_no_inst == 1);
}

static void
test_squash_then_reuse_sequence()
{
    // End-to-end lifecycle of ONE delayed event:
    //   schedule -> producer squash (ignore) -> later slot reuse by a new
    //   producer (a NEW event, not this one) -> normal event still fires.
    const WakeStamp s = make_stamp();
    DelayedWakeCounters dw;

    WakeObserved squashed = make_now(s);
    squashed.squashed = true;
    noteWakeDecision(dw, classifyWake(s, squashed));

    WakeObserved reused = make_now(s);
    reused.dests[0].generation += 1;
    noteWakeDecision(dw, classifyWake(s, reused));

    WakeObserved normal = make_now(s);
    noteWakeDecision(dw, classifyWake(s, normal));

    check("old event never fired after squash/reuse",
          dw.ignored_squashed == 1 && dw.ignored_generation == 1);
    check("normal event still fires", dw.fired == 1);
}

static void
test_duplicate_genuine_wake_is_suppressed_once()
{
    // The injection marked source slot B (flat 200) ready but could not pop
    // the victim from B's dependency chain. When B's producer completes, the
    // genuine wake must not mark B a second time (and must not re-push the
    // victim after issue).
    DuplicateWake d;
    recordDuplicateWake(d, /*victim_sn=*/777, /*victim_tid=*/0,
                        /*corrupt_flat=*/200);

    check("different instruction not suppressed",
          !suppressDuplicateWake(d, 778, 0, 200));
    check("different thread not suppressed",
          !suppressDuplicateWake(d, 777, 1, 200));
    check("different chain not suppressed",
          !suppressDuplicateWake(d, 777, 0, 300));
    check("tracking survives non-matching wakes", d.tracked);
    check("genuine wake of the corrupted source suppressed",
          suppressDuplicateWake(d, 777, 0, 200));
    check("suppression is one-shot", !d.tracked);
    check("second genuine wake is not suppressed again",
          !suppressDuplicateWake(d, 777, 0, 200));
}

int
main()
{
    std::printf("CHAOSIQ FQ08 lifecycle host test\n");

    std::printf("[FQ08-b] no victim => no applied count\n");
    test_no_victim_does_not_apply();
    test_only_the_woken_chain_is_not_a_victim();

    std::printf("[FQ08-b] victim => real wrong-source write + identity\n");
    test_positive_victim_applies_and_activates();
    test_victim_with_last_unready_slot_activates();
    test_squashed_and_fully_ready_victims_rejected();
    test_budget_only_consumed_on_apply();
    test_duplicate_genuine_wake_is_suppressed_once();

    std::printf("[FQ08-c] delayed wake lifecycle\n");
    test_normal_delayed_wake_fires();
    test_squashed_producer_is_ignored();
    test_freed_slot_generation_is_ignored();
    test_second_dest_generation_mismatch_is_ignored();
    test_identity_mismatch_is_ignored();
    test_missing_instruction_is_ignored();
    test_squash_then_reuse_sequence();

    if (failures == 0) {
        std::printf("ALL CHAOS IQ LIFECYCLE CHECKS PASSED\n");
        return 0;
    }
    std::printf("%d CHECK(S) FAILED\n", failures);
    return 1;
}
