// RP01 selector host test (LSU v3.2.12, task-14 step 2).
//
// Build & run (host, outside the gem5 build), from the repo root:
//   g++ -O2 -std=c++17 -I CHAOS/gem5/src tests/test_rp01_selector.cc
//       -o /tmp/test_rp01_selector
//   /tmp/test_rp01_selector
//
// Verifies the pure rules in cpu/o3/CHAOSLSQFwd/rp01_rules.hh:
//   1. count-only never skips (the preflight observes, never acts);
//   2. ordinal N selects exactly the Nth eligible event (1-based);
//   3. ordinal 999 selects none in a bounded stream;
//   4. ordinal 0 selects none (disabled);
//   5. one-shot: an already-fired selector never skips again;
//   6. squashed loads do not consume the ordinal space;
//   7. the identity tuple (dyn_inst_seq, lq_idx, lq_gen, store_seq,
//      replay_gen) is recorded for the selected event.
#include <cassert>
#include <cstdio>
#include <vector>

#include "cpu/o3/CHAOSLSQFwd/rp01_rules.hh"

using namespace gem5::chaos_rp01;

// One visit of the lsq_unit.cc:2016 call site (PartialAddrRangeCoverage
// branch of LSQUnit::read()). replay_gen is the POST-increment value the
// caller observes (line 2012 runs before the call).
struct SiteEvent {
    uint64_t seq;
    uint64_t lq_idx;
    uint64_t lq_gen;
    uint64_t store_seq;
    uint64_t replay_gen;
    bool squashed;
};

// Mirror of the planned CHAOSLSQFwd::maybeSkipPartialReplay core: judge one
// site visit, maintain the eligible counter and the recorded identity.
struct Selector {
    uint64_t ordinal = 0;
    bool count_only = false;
    bool fired = false;
    uint64_t eligible = 0;
    EventIdentity last{};     // identity of the most recent judged event
    EventIdentity fired_id{}; // identity of the skipped (selected) event

    bool consult(const SiteEvent &e) {
        if (!isEligible(e.squashed))
            return false;
        ++eligible;
        last = EventIdentity{e.seq, e.lq_idx, e.lq_gen, e.store_seq,
                             e.replay_gen};
        if (shouldSkip(eligible, ordinal, count_only, fired)) {
            fired = true;
            fired_id = last;
            return true;
        }
        return false;
    }
};

static std::vector<SiteEvent>
make_stream(size_t n)
{
    std::vector<SiteEvent> v;
    for (size_t i = 0; i < n; ++i)
        v.push_back(SiteEvent{1000 + i,          // dyn_inst_seq
                              9000 + 10 * i,     // lq_idx
                              9500 + 10 * i,     // lq_gen
                              500 + i,           // stalling store_seq
                              1,                 // post-increment replay_gen
                              false});
    return v;
}

int
main()
{
    // --- rule-level assertions (SP05-style) -------------------------------
    assert(shouldSelect(2, 2));       // the 2nd event with ordinal 2
    assert(!shouldSelect(2, 0));      // ordinal 0 = disabled
    assert(!shouldSelect(1, 2));      // not yet at the 2nd event
    assert(!shouldSelect(2, 1));      // already past ordinal 1
    assert(!shouldSelect(5, 999));    // 999th never reached in 5 events
    assert(shouldSelect(999, 999));   // generic rule: would need 999 events
    assert(isEligible(false));
    assert(!isEligible(true));
    // count-only and one-shot dominate the ordinal match:
    assert(!shouldSkip(3, 3, true, false));
    assert(!shouldSkip(3, 3, false, true));
    assert(shouldSkip(3, 3, false, false));

    // --- 1. count-only never skips ----------------------------------------
    {
        Selector s;
        s.ordinal = 3;
        s.count_only = true;
        auto stream = make_stream(10);
        int skips = 0;
        for (const auto &e : stream)
            skips += s.consult(e) ? 1 : 0;
        assert(skips == 0);
        assert(s.eligible == 10);
        assert(!s.fired);
        // identity of the LAST judged event is still recorded (observation):
        assert(s.last == (EventIdentity{1009, 9090, 9590, 509, 1}));
    }

    // --- 2. ordinal N selects exactly the Nth eligible event --------------
    {
        Selector s;
        s.ordinal = 3;
        auto stream = make_stream(7);
        int skips = 0;
        int skip_at = -1;
        for (size_t i = 0; i < stream.size(); ++i)
            if (s.consult(stream[i])) { ++skips; skip_at = (int)i; }
        assert(skips == 1);
        assert(skip_at == 2);  // 0-based index 2 = 3rd eligible event
        assert(s.eligible == 7);
        // recorded identity is exactly the 3rd event's tuple:
        assert(s.fired_id ==
               (EventIdentity{1002, 9020, 9520, 502, 1}));
        // and it differs from the neighbors':
        assert(!(s.fired_id == (EventIdentity{1001, 9010, 9510, 501, 1})));
        assert(!(s.fired_id == (EventIdentity{1003, 9030, 9530, 503, 1})));
    }

    // --- 3. ordinal 999 selects none in a bounded stream ------------------
    {
        Selector s;
        s.ordinal = 999;  // the "select none" control inside fault mode
        auto stream = make_stream(7);
        int skips = 0;
        for (const auto &e : stream)
            skips += s.consult(e) ? 1 : 0;
        assert(skips == 0);
        assert(s.eligible == 7);
        assert(!s.fired);
    }

    // --- 4. ordinal 0 selects none (disabled) ------------------------------
    {
        Selector s;
        s.ordinal = 0;
        auto stream = make_stream(7);
        int skips = 0;
        for (const auto &e : stream)
            skips += s.consult(e) ? 1 : 0;
        assert(skips == 0);
        assert(s.eligible == 7);
    }

    // --- 5. one-shot: once fired, no further skip even on re-consult -------
    {
        Selector s;
        s.ordinal = 2;
        auto stream = make_stream(7);
        int skips = 0;
        for (const auto &e : stream)
            skips += s.consult(e) ? 1 : 0;
        assert(skips == 1 && s.fired);
        // A duplicate/later visit with a matching count must not re-fire:
        assert(!shouldSkip(2, 2, false, s.fired));
    }

    // --- 6. squashed loads do not consume the ordinal space ----------------
    {
        Selector s;
        s.ordinal = 3;
        auto stream = make_stream(6);
        stream[1].squashed = true;  // site visit 2 is a squashed load
        int skips = 0;
        int skip_seq = 0;
        for (const auto &e : stream)
            if (s.consult(e)) { ++skips; skip_seq = (int)e.seq; }
        // Eligible events are visits 1,3,4,5,6 (squashed visit excluded),
        // so the 3rd ELIGIBLE event is site visit 4 (seq 1003):
        assert(s.eligible == 5);
        assert(skips == 1);
        assert(skip_seq == 1003);
        assert(s.fired_id == (EventIdentity{1003, 9030, 9530, 503, 1}));
    }

    std::printf("RP01_SELECTOR_OK\n");
    return 0;
}
