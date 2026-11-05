// [FSU][FP05] Host unit test for the pure burst-episode model.
// Compiled by tests/test_chaos_fsu_burst_cpp.py with -Wall -Wextra -Werror.
#include <cassert>
#include <cstdio>
#include <string>

#include "cpu/o3/CHAOSFPU/chaos_fsu_burst.hh"

using namespace gem5::chaos_fsu;

static void
test_mode_parse()
{
    BurstSubmodel m;
    assert(parseBurstMode("", m) && m == BurstSubmodel::None);
    assert(parseBurstMode("same_lane", m) && m == BurstSubmodel::SameLane);
    assert(parseBurstMode("adjacent_lane", m) &&
           m == BurstSubmodel::AdjacentLane);
    assert(parseBurstMode("cross_lane_mbu", m) &&
           m == BurstSubmodel::CrossLaneMbu);
    assert(parseBurstMode("lane_mask", m) && m == BurstSubmodel::LaneMask);
    // Unknown / misspelled modes fail closed.
    assert(!parseBurstMode("burst", m));
    assert(!parseBurstMode("SAME_LANE", m));
}

static void
test_length()
{
    assert(!burstLengthValid(0));
    assert(!burstLengthValid(1));   // one event is not a burst
    assert(burstLengthValid(2));
    assert(burstLengthValid(3));
    assert(burstLengthValid(4));
    assert(!burstLengthValid(5));
}

static void
test_lane_geometry()
{
    std::string err;
    // FP64 (2 lanes): same-lane and lane-mask fit everywhere.
    assert(burstLaneGeometryValid(BurstSubmodel::SameLane, 0, 4, 1, 64, err));
    assert(burstLaneGeometryValid(BurstSubmodel::SameLane, 1, 4, 1, 64, err));
    assert(burstLaneGeometryValid(BurstSubmodel::LaneMask, 1, 2, 1, 64, err));
    // adjacent lane2 burst needs lanes 0..1: valid; base 1 for N=2 needs
    // lane 2 -> fail closed (never clamp).
    assert(burstLaneGeometryValid(BurstSubmodel::AdjacentLane, 0, 2, 1, 64,
                                  err));
    assert(!burstLaneGeometryValid(BurstSubmodel::AdjacentLane, 1, 2, 1, 64,
                                   err));
    // N=4 with 64-bit lanes cannot fit in a 128-bit register.
    assert(!burstLaneGeometryValid(BurstSubmodel::AdjacentLane, 0, 4, 1, 64,
                                   err));
    // cross-lane MBU needs base+1 to exist.
    assert(burstLaneGeometryValid(BurstSubmodel::CrossLaneMbu, 0, 4, 1, 64,
                                  err));
    assert(!burstLaneGeometryValid(BurstSubmodel::CrossLaneMbu, 1, 2, 1, 64,
                                   err));
    // FP32 (4 lanes) supports adjacent N=4.
    assert(burstLaneGeometryValid(BurstSubmodel::AdjacentLane, 0, 4, 1, 32,
                                  err));
    assert(!burstLaneGeometryValid(BurstSubmodel::AdjacentLane, 3, 2, 1, 32,
                                   err));
    // Invalid base/length are rejected.
    assert(!burstLaneGeometryValid(BurstSubmodel::SameLane, 2, 2, 1, 64, err));
    assert(!burstLaneGeometryValid(BurstSubmodel::SameLane, 0, 1, 1, 64, err));
}

static void
test_lane_at()
{
    assert(burstLaneAt(BurstSubmodel::SameLane, 0, 3, 1) == 0);
    assert(burstLaneAt(BurstSubmodel::LaneMask, 1, 3, 1) == 1);
    assert(burstLaneAt(BurstSubmodel::AdjacentLane, 0, 0, 1) == 0);
    assert(burstLaneAt(BurstSubmodel::AdjacentLane, 0, 2, 1) == 2);
    assert(burstLaneAt(BurstSubmodel::AdjacentLane, 0, 2, 2) == 4);
    assert(burstLaneAt(BurstSubmodel::CrossLaneMbu, 1, 3, 1) == 1);
    assert(burstLaneAt(BurstSubmodel::None, 0, 0, 1) == -1);
}

static void
test_span()
{
    assert(burstLaneSpan(BurstSubmodel::SameLane, 4, 1) == 1);
    assert(burstLaneSpan(BurstSubmodel::LaneMask, 4, 1) == 1);
    assert(burstLaneSpan(BurstSubmodel::AdjacentLane, 3, 1) == 3);
    assert(burstLaneSpan(BurstSubmodel::AdjacentLane, 3, 2) == 5);
    assert(burstLaneSpan(BurstSubmodel::CrossLaneMbu, 4, 1) == 2);
}

static void
test_tracker_ordinals()
{
    BurstEpisodeTracker t;
    assert(t.arm(7, 3, 100));
    assert(t.active && !t.completed());
    assert(t.currentOrdinal() == 0);
    uint64_t o = 99;
    assert(t.applyOne(o) && o == 0);
    assert(t.applyOne(o) && o == 1);
    assert(!t.completed());          // 2 of 3
    assert(t.applyOne(o) && o == 2);
    assert(t.completed());
    // No fourth ordinal: the declared length is never exceeded.
    assert(!t.applyOne(o));
    assert(t.ordinal == 3);
    t.finish();
    assert(!t.active);
    assert(!t.applyOne(o));
}

static void
test_tracker_no_reuse_and_disabled()
{
    BurstEpisodeTracker t;
    assert(t.arm(5, 2, 10));
    uint64_t o;
    assert(t.applyOne(o));
    assert(!t.arm(6, 2, 11));        // an active episode cannot be re-armed
    assert(t.applyOne(o) && o == 1);
    t.finish();
    // The next episode gets a NEW id (monotonic, never reused).
    assert(t.arm(t.next_id, 2, 20));
    assert(t.id == 6);
    t.finish();

    BurstEpisodeTracker d;
    d.disabled = true;
    assert(!d.arm(1, 2, 0));
    assert(!d.active);
}

static void
test_tracker_rejects_bad_length()
{
    BurstEpisodeTracker t;
    assert(!t.arm(1, 1, 0));
    assert(!t.arm(1, 5, 0));
    assert(!t.arm(1, 0, 0));
    assert(!t.active);
}

static void
test_end_reasons()
{
    assert(std::string(burstEndReason(true, false)) == "completed");
    assert(std::string(burstEndReason(false, false)) == "run_exit");
    assert(std::string(burstEndReason(false, true)) == "lane_geometry");
    assert(std::string(burstEndReason(true, true)) == "lane_geometry");
}

static void
test_accounting()
{
    // A completed one-episode burst.
    assert(burstAccountingConserved(3, 3, 2, 0, 1, 1, 1, 0, 0));
    // An early-exit short episode.
    assert(burstAccountingConserved(2, 2, 0, 1, 1, 1, 0, 1, 0));
    // A lane-geometry rejection (never armed, no event).
    assert(burstAccountingConserved(0, 0, 0, 0, 1, 0, 0, 0, 1));
    // Conservation violations are rejected.
    assert(!burstAccountingConserved(1, 2, 0, 0, 1, 1, 1, 0, 0));
    assert(!burstAccountingConserved(2, 2, 3, 0, 1, 1, 1, 0, 0));
    assert(!burstAccountingConserved(2, 2, 0, 0, 1, 1, 1, 1, 0));
    assert(!burstAccountingConserved(2, 2, 0, 0, 2, 1, 1, 0, 0));
}

static void
test_noneligible_does_not_consume_ordinal()
{
    // Model the eligible stream: only eligible events call applyOne().
    //   E N E N E  -> ordinals 0,1,2 (the two N events consume nothing).
    const bool stream[] = {true, false, true, false, true};
    BurstEpisodeTracker t;
    uint64_t ordinals[3] = {99, 99, 99};
    int seen = 0;
    for (size_t i = 0; i < sizeof(stream) / sizeof(stream[0]); ++i) {
        if (!stream[i])
            continue;                 // non-eligible: no ordinal
        if (!t.active)
            assert(t.arm(1, 3, 1));
        uint64_t o;
        assert(t.applyOne(o));
        assert(seen < 3);
        ordinals[seen++] = o;
    }
    assert(seen == 3);
    assert(ordinals[0] == 0 && ordinals[1] == 1 && ordinals[2] == 2);
    assert(t.completed());
}

int
main()
{
    test_mode_parse();
    test_length();
    test_lane_geometry();
    test_lane_at();
    test_span();
    test_tracker_ordinals();
    test_tracker_no_reuse_and_disabled();
    test_tracker_rejects_bad_length();
    test_noneligible_does_not_consume_ordinal();
    test_end_reasons();
    test_accounting();
    std::printf("all checks passed\n");
    return 0;
}
