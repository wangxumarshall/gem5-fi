// [LSU][V3.2.12][A03] host unit test for cpu/o3/CHAOSAddrPath/a03_stream.hh
// (plan Task 8 Step 2). Pure-header test — no gem5 build, plain g++:
//   g++ -O2 -std=c++17 -I CHAOS/gem5/src tests/test_addrpath_a03_stream.cc
//       -o /tmp/test_a03 && /tmp/test_a03
// Expected output: A03_STREAM_OK
//
// Asserts the F5 eligibility-stream contract (task-8-brief.md Step 2,
// LSU_Propagation_Acceptance_Standard_v3.2.12.md):
//   - after activation, EVERY eligible load is recorded exactly once (the
//     recorder accepts a strictly advancing ordinal once; a duplicate or
//     regressed submission is rejected and counted, never silently kept);
//   - affected=1 iff the stuck bit changes the EA (the builder derives it
//     from the observed golden/actual pair, so the property holds by
//     construction — verified here over applied and masked pairs);
//   - an ALREADY_STUCK address yields affected=0, reason=ALREADY_STUCK and
//     is STILL recorded exactly once (the masking path is a recorded event,
//     not a missing event);
//   - one a03_activation per run (a second activate() is rejected);
//   - the frozen detail strings use the CHAOSPropagation k=v;k=v dialect
//     with NO commas (a comma would corrupt the CSV trace, whose detail
//     column is the last field), bare lowercase hex addresses, decimal
//     ordinals/counts, and the literal NOT_APPLICABLE for absent values.
//
// v3.3.2 P0-5 additions:
//   - a stream event built with a real PC (0x400558) prints that PC in the
//     frozen detail (the PC is threaded from the lsq.cc call site);
//   - the persistent stuck-at lifecycle counts applications (affected=1)
//     and already_stuck (affected=0) separately, and first_affected is the
//     FIRST affected row — not the first recorded row (an ALREADY_STUCK
//     activation is a no-op application, the fault stays active later).

#include <cstdio>
#include <cstring>
#include <string>

#include "cpu/o3/CHAOSAddrPath/a03_stream.hh"

using namespace gem5::chaos_a03;
using gem5::chaos_a01::kPcUnknown;

static int failures = 0;

static void
check(bool ok, const char *what)
{
    if (!ok) {
        std::printf("FAIL: %s\n", what);
        ++failures;
    }
}

static bool
contains(const std::string &s, const char *needle)
{
    return s.find(needle) != std::string::npos;
}

int
main()
{
    // ---- record builder: affected=1 iff the bit changes -------------------
    {
        // bit 3 SET in the golden EA: the stuck-at-0 application flips it.
        const uint64_t golden = 0x7ffffefda8ULL;   // bit3 = 1
        const uint64_t actual = applyStuckAt(golden, 3, 0);
        check(actual == 0x7ffffefda0ULL,
              "stuck0 math: EA & ~0x8 clears bit 3");
        check(actual == (golden & ~(1ULL << 3)),
              "stuck0 math mirrors the injector's mask");
        const StreamEvent e = streamEvent(1, 4242, kPcUnknown, golden,
                                          actual, 3);
        check(e.affected == 1, "applied: affected=1 iff the bit changes");
        check(e.reason == StreamReason::StuckApplied,
              "applied: reason STUCK_APPLIED");
        check(std::string(streamReasonName(e.reason)) == "STUCK_APPLIED",
              "applied: reason name is the frozen string");
        check(e.bit == 3, "applied: stuck bit carried");
        check(e.golden_ea == golden && e.actual_ea == actual,
              "applied: golden/actual pair carried");
        check(e.eligible == 1, "stream records only eligible loads");
        check(e.dyn_inst_seq == 4242 && e.pc == kPcUnknown,
              "applied: identity fields carried (pc never fabricated)");
    }
    {
        // bit 3 CLEAR in the golden EA: the condition is applied but the
        // address is ALREADY_STUCK — affected=0, and the event is still a
        // stream record (the masking path, not a missing event).
        const uint64_t golden = 0x7ffffefda0ULL;   // bit3 = 0
        const uint64_t actual = applyStuckAt(golden, 3, 0);
        check(actual == golden, "already-stuck: application is a no-op");
        check(applyStuckAt(applyStuckAt(golden, 3, 0), 3, 0) == actual,
              "stuck0 application is idempotent");
        const StreamEvent e = streamEvent(2, 4243, kPcUnknown, golden,
                                          actual, 3);
        check(e.affected == 0, "already-stuck: affected=0");
        check(e.reason == StreamReason::AlreadyStuck,
              "already-stuck: reason ALREADY_STUCK");
        check(std::string(streamReasonName(e.reason)) == "ALREADY_STUCK",
              "already-stuck: reason name is the frozen string");
        check(e.actual_ea == e.golden_ea,
              "already-stuck: actual == golden (nothing to propagate)");
    }
    {
        // stuck-at-1 mirror (the rng-selected path's other level): the pure
        // math must also model vaddr | mask.
        const uint64_t golden = 0x2000ULL;        // bit 12 clear (0x2000 = 1<<13)
        const uint64_t actual = applyStuckAt(golden, 12, 1);
        check(actual == (golden | (1ULL << 12)) && actual == 0x3000ULL,
              "stuck1 math: EA | mask sets the bit");
        const StreamEvent e = streamEvent(3, 7, kPcUnknown, golden, actual,
                                          12);
        check(e.affected == 1 && e.reason == StreamReason::StuckApplied,
              "stuck1: bit set by the application is affected");
        const StreamEvent m = streamEvent(4, 8, kPcUnknown, 0x1000ULL,
                                          applyStuckAt(0x1000ULL, 12, 1), 12);
        check(m.affected == 0 && m.reason == StreamReason::AlreadyStuck,
              "stuck1: bit already set (0x1000 = 1<<12) is ALREADY_STUCK");
    }

    // ---- exactly-once discipline: every eligible load, one record ---------
    {
        StreamRecorder rec;
        check(!rec.activated() && rec.recorded() == 0 && rec.rejected() == 0,
              "fresh recorder: nothing recorded, nothing rejected");

        // a stream record BEFORE activation is rejected (the stream starts
        // at the activation start position — R05's stream begins at
        // ordinal 5, and ordinals 1-4 produce no records).
        StreamEvent early = streamEvent(5, 100, kPcUnknown, 0x108ULL,
                                        applyStuckAt(0x108ULL, 3, 0), 3);
        check(!rec.record(early),
              "pre-activation record rejected");
        check(rec.recorded() == 0 && rec.rejected() == 1,
              "pre-activation rejection counted, no silent record");

        // activation: the first fired eligible load arms the stream.
        Activation act;
        act.tick = 555000;
        act.bit = 3;
        act.mode = "a03_bit3_stuck0_load";
        check(rec.activate(act), "first activation accepted");
        check(rec.activated(), "recorder is activated");
        check(rec.activation().tick == 555000 && rec.activation().bit == 3 &&
              rec.activation().mode == "a03_bit3_stuck0_load",
              "activation record carries {tick, bit, mode}");
        check(!rec.activate(act), "second activation rejected");
        check(rec.rejected() == 2, "second activation rejection counted");

        // R05 shape: activation AT ordinal 5 — the first stream row IS
        // ordinal 5, proving a start position, not a fresh count.
        StreamEvent first = streamEvent(5, 100, kPcUnknown, 0x108ULL,
                                        applyStuckAt(0x108ULL, 3, 0), 3);
        check(rec.record(first), "first post-activation event recorded");
        check(rec.recorded() == 1, "recorded count is 1");

        // every LATER eligible load records exactly once: the duplicate is
        // rejected, the regression is rejected, the next ordinal is kept.
        check(!rec.record(first),
              "duplicate ordinal rejected (exactly once)");
        StreamEvent regressed = streamEvent(4, 101, kPcUnknown, 0x100ULL,
                                            applyStuckAt(0x100ULL, 3, 0), 3);
        check(!rec.record(regressed), "ordinal regression rejected");
        check(rec.recorded() == 1 && rec.rejected() == 4,
              "rejections counted, the record stream unchanged");
        StreamEvent next = streamEvent(6, 101, kPcUnknown, 0x100ULL,
                                       applyStuckAt(0x100ULL, 3, 0), 3);
        check(rec.record(next), "next ordinal recorded");
        check(rec.recorded() == 2 && rec.rejected() == 4,
              "two distinct eligible events, exactly two records");
    }

    // ---- a continuous post-activation stream (the pilot shape) -------------
    {
        StreamRecorder rec;
        Activation act;
        act.tick = 1234;
        act.bit = 3;
        act.mode = "a03_bit3_stuck0_load";
        rec.activate(act);

        // R01 shape: activation at ordinal 1, then EVERY eligible load —
        // alternating applied / already-stuck — one record each, ordinals
        // contiguous 1..6.
        const uint64_t goldens[6] = {0x108ULL, 0x100ULL, 0x1a8ULL,
                                     0x1f0ULL, 0x400ULL, 0x408ULL};
        for (int i = 0; i < 6; ++i) {
            const uint64_t g = goldens[i];
            const uint64_t a = applyStuckAt(g, 3, 0);
            const StreamEvent e = streamEvent((uint64_t)(i + 1),
                                             (uint64_t)(900 + i), kPcUnknown,
                                             g, a, 3);
            check(rec.record(e), "continuous stream: each event accepted");
            check(e.affected == ((g & 0x8ULL) ? 1 : 0),
                  "affected=1 iff bit 3 changed (derived from the pair)");
            if (g & 0x8ULL)
                check(e.reason == StreamReason::StuckApplied,
                      "applied row reason");
            else
                check(e.reason == StreamReason::AlreadyStuck,
                      "already-stuck row reason (recorded, not dropped)");
        }
        check(rec.recorded() == 6, "six eligible loads, six records");
        check(rec.rejected() == 0, "no rejections in an honest stream");
        check(rec.appliedCount() == 3 && rec.alreadyStuckCount() == 3,
              "applied / already-stuck split follows the goldens' bit 3");
    }

    // ---- frozen detail format (single format, no drift) ---------------------
    {
        const StreamEvent e = streamEvent(5, 4242, kPcUnknown, 0x7ffffefda8ULL,
                                          0x7ffffefda0ULL, 3);
        const std::string d = streamDetail(e);
        check(contains(d, "event_ordinal=5;"), "detail: event_ordinal decimal");
        check(contains(d, ";dyn_inst_seq=4242;"), "detail: dyn_inst_seq");
        check(contains(d, ";pc=0;"), "detail: pc hex (kPcUnknown)");
        check(contains(d, ";eligible=1;"), "detail: eligible=1");
        check(contains(d, ";affected=1;"), "detail: affected decimal");
        check(contains(d, ";golden_ea=7ffffefda8;"),
              "detail: golden_ea bare hex");
        check(contains(d, ";actual_ea=7ffffefda0;"),
              "detail: actual_ea bare hex");
        check(contains(d, ";bit=3;"), "detail: bit decimal");
        check(contains(d, ";reason=STUCK_APPLIED"),
              "detail: reason name, last field");

        const StreamEvent m = streamEvent(6, 4243, kPcUnknown, 0x100ULL,
                                          0x100ULL, 3);
        const std::string dm = streamDetail(m);
        check(contains(dm, ";affected=0;"), "masked detail: affected=0");
        check(contains(dm, ";reason=ALREADY_STUCK"),
              "masked detail: reason=ALREADY_STUCK");
        check(contains(dm, ";golden_ea=100;") && contains(dm, ";actual_ea=100;"),
              "masked detail: identical pair carried");

        check(d.find(',') == std::string::npos &&
              dm.find(',') == std::string::npos,
              "detail: NO commas (CSV last column)");
        const size_t reason_pos = d.rfind(";reason=STUCK_APPLIED");
        check(reason_pos != std::string::npos &&
              reason_pos + std::strlen(";reason=STUCK_APPLIED") == d.size(),
              "detail: reason is the final field (frozen field order)");

        Activation act;
        act.tick = 555000;
        act.bit = 3;
        act.mode = "a03_bit3_stuck0_load";
        const std::string da = activationDetail(act);
        check(contains(da, "tick=555000;bit=3;mode=a03_bit3_stuck0_load"),
              "activation detail: {tick, bit, mode} frozen order");
        check(da.find(',') == std::string::npos,
              "activation detail: NO commas");
        Activation nobit;
        nobit.tick = 1;
        nobit.mode = "a03_stuck0";
        const std::string dn = activationDetail(nobit);
        check(contains(dn, ";bit=NOT_APPLICABLE;"),
              "activation detail: bit=NOT_APPLICABLE for kNoBit");
    }

    // ---- v3.3.2 P0-5: real faulting PC --------------------------------
    {
        const uint64_t golden = 0x7ffffefda8ULL;   // bit3 = 1
        const uint64_t actual = applyStuckAt(golden, 3, 0);
        const StreamEvent e = streamEvent(1, 4242, 0x400558ULL, golden,
                                          actual, 3);
        check(e.pc == 0x400558ULL, "PC: the real faulting PC is carried");
        const std::string d = streamDetail(e);
        check(contains(d, ";pc=400558;"),
              "detail: real PC prints as bare lowercase hex");
        check(d.find(";pc=0;") == std::string::npos,
              "detail: kPcUnknown sentinel not emitted when a PC exists");
    }

    // ---- v3.3.2 P0-5: persistent stuck-at lifecycle --------------------
    {
        StreamRecorder rec;
        Activation act;
        act.tick = 777;
        act.bit = 3;
        act.mode = "a03_bit3_stuck0_load";
        act.event_ordinal = 1;
        act.dyn_inst_seq = 900;
        act.pc = 0x400500ULL;
        act.golden_ea = 0x100ULL;      // bit3 = 0: activation is ALREADY_STUCK
        check(rec.activate(act), "lifecycle: activation accepted");
        check(rec.record(streamEvent(1, 900, 0x400500ULL, 0x100ULL,
                                     applyStuckAt(0x100ULL, 3, 0), 3)),
              "lifecycle: activation row recorded (no-op application)");
        check(rec.record(streamEvent(2, 901, 0x400560ULL, 0x108ULL,
                                     applyStuckAt(0x108ULL, 3, 0), 3)),
              "lifecycle: first affected row recorded");
        check(rec.record(streamEvent(3, 902, 0x400568ULL, 0x1a0ULL,
                                     applyStuckAt(0x1a0ULL, 3, 0), 3)),
              "lifecycle: later no-op row recorded");

        check(rec.eligibleEvents() == 3, "lifecycle: three eligible events");
        check(rec.appliedCount() == 1,
              "lifecycle: exactly one application changed the EA");
        check(rec.alreadyStuckCount() == 2,
              "lifecycle: two ALREADY_STUCK no-op applications");
        check(rec.hasFirstAffected(),
              "lifecycle: a first-affected row exists");

        const StuckLifecycle lc = rec.lifecycle(7, "a03_bit3_stuck0_load");
        check(lc.fault_id == 7 && lc.bit == 3 &&
              lc.mode == "a03_bit3_stuck0_load",
              "lifecycle: fault identity {fault_id, bit, mode} carried");
        check(lc.eligible_events == 3 && lc.applications == 1 &&
              lc.already_stuck == 2,
              "lifecycle: eligible/applications/already_stuck split");
        check(lc.has_activation && lc.activation_ordinal == 1 &&
              lc.activation_dyn_inst_seq == 900 &&
              lc.activation_pc == 0x400500ULL &&
              lc.activation_golden_ea == 0x100ULL,
              "lifecycle: activation identity carried");
        check(lc.has_first_affected && lc.first_affected_ordinal == 2 &&
              lc.first_affected_dyn_inst_seq == 901 &&
              lc.first_affected_pc == 0x400560ULL,
              "lifecycle: first_affected is the FIRST affected row, not "
              "the (already-stuck) activation row");

        const std::string d = lifecycleDetail(lc);
        check(contains(d, "fault_id=7;bit=3;mode=a03_bit3_stuck0_load;"),
              "lifecycle detail: fault identity first");
        check(contains(d, ";eligible_events=3;applications=1;already_stuck=2;"),
              "lifecycle detail: application split decimal");
        check(contains(d, ";activation_ordinal=1;activation_dyn_inst_seq=900;"
                         "activation_pc=400500;activation_golden_ea=100;"),
              "lifecycle detail: activation identity (bare hex PC/EA)");
        check(contains(d, ";first_affected_ordinal=2;"
                         "first_affected_dyn_inst_seq=901;"
                         "first_affected_pc=400560"),
              "lifecycle detail: first-affected identity, last fields");
        check(d.find(',') == std::string::npos,
              "lifecycle detail: NO commas (CSV last column)");

        // No affected row -> first_affected is honestly absent, never 0.
        StreamRecorder masked;
        Activation act2;
        act2.tick = 1;
        act2.bit = 3;
        act2.mode = "a03_bit3_stuck0_load";
        act2.event_ordinal = 1;
        act2.dyn_inst_seq = 5;
        masked.activate(act2);
        masked.record(streamEvent(1, 5, 0x400500ULL, 0x100ULL,
                                  applyStuckAt(0x100ULL, 3, 0), 3));
        const StuckLifecycle lc2 = masked.lifecycle(1, act2.mode);
        check(!lc2.has_first_affected &&
              contains(lifecycleDetail(lc2), ";first_affected_ordinal="
                                             "NOT_APPLICABLE;"),
              "lifecycle: no affected row -> NOT_APPLICABLE, no silent zero");
    }

    if (failures != 0) {
        std::printf("test_addrpath_a03_stream: %d failure(s)\n", failures);
        return 1;
    }
    std::printf("A03_STREAM_OK\n");
    return 0;
}
