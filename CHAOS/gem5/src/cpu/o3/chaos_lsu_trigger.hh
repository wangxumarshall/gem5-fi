/*
 * chaos_lsu_trigger.hh — LSU north-star F0-F6 trigger semantics
 * (docs/gem5-fi/lsu/05-frequency-and-sampling.md r2-r8), EVENT-normalized:
 * the denominator is the injector's eligible-event stream, NOT CPU cycles
 * (the ooo track's chaos_trigger.hh stays cycle-based — different tracks,
 * different denominators, no mixing; W2 R1 ruling 2026-09-25).
 *
 * Tiers (05 r2-r8):
 *   F0 single transient — uniform over eligible events after warm-up;
 *   F1/F2/F3 — mean interval 1,000,000 / 100,000 / 10,000 eligible events,
 *              each next interval = U[iv/2, 3*iv/2) (±50% jitter, 05 r3-r5);
 *   F4 short burst — every 100,000 eligible events fire once, then pollute
 *              2-4 consecutive eligible events (05 r6);
 *   F5 permanent — from the first eligible event after warm-up to end of run
 *              (one bit/field per run; target choice is the injector's);
 *   F6 deterministic event — inject ONCE at the first occurrence of the
 *              specified event type (05 r7; event sources per 09 §2.1 map:
 *              TlbHit[FS-only]/SqForward/DirtyEviction/CasSuccess).
 *
 * Funnel counts (04 L0): attempted (hook invocations) / eligible (passed the
 * injector's eligibility filter) / injected (fault written). The ACTIVATED
 * count (fault consumed downstream) is the L0 read-back layer's verdict —
 * deliberately NOT counted here (W3 delivers it; W2 R2 ruling). End-of-run
 * summary line: CHAOS_LSU_TRIGGER: injector= tier= attempted= eligible=
 * injected=.
 *
 * F6 event notification: the single-consumer function pointer below is
 * single-core-SE scoped (one LSU consumer per run — the 337-cell grid runs
 * one injector per run by construction). A multicore/FS generalization is
 * W8's business, recorded here honestly.
 */
#ifndef __CPU_O3_CHAOS_LSU_TRIGGER_HH__
#define __CPU_O3_CHAOS_LSU_TRIGGER_HH__

#include <cstdint>
#include <cstdio>

#include "cpu/o3/chaos_event_sample.hh"
#include "sim/cur_tick.hh"     // curTick() [LSU][OBS-3]

namespace gem5
{

enum class ChaOSLsuTier : uint8_t { F0, F1, F2, F3, F4, F5, F6 };

// F6 event sources (09 §2.1 W1 map). TlbHit is FS-only — SE never calls
// TLB::lookup (arm/mmu.cc:323-365 translateSe); the enum value exists so the
// config surface is uniform, and an SE run selecting it logs zero events.
//
// [MDSPEC][R4-5.1] FIFTH source, recorded ruling: the L1D MSHR merge
// (BaseCache::handleTimingReqMiss coalescing branch — CHAOSCache
// targetField=mshr_merge, model C11) is treated as an F6 event source: C11's
// specified event IS the merge, and the matrix F6 row reads "如…" (e.g., not
// an exhaustive enumeration). It does NOT ride chaosLsuF6Observe/Notify
// (typed to the W1 enum above) — the merge hook calls onF6Event(false)
// directly at the merge site (early_stress first-occurrence, A5 ruling).
//
// [MDSPEC][R4-5.2] SIXTH source, same ruling shape: the L1D miss fill
// (BaseCache::recvTimingResp read-fill arrival at the mounted cache —
// CHAOSCache targetField=mshr_fill_timing, model C12) is an F6 event
// source: C12's specified event IS the miss fill (the model's trigger
// column reads "miss fill或dirty writeback"; the landed mode defers the
// miss fill). Same non-ride: the fill-timing hook calls onF6Event(false)
// directly at the fill site (the fillResponse-arrival hook is the attempt
// stream, R4-5.1-review-I1 accounting).
//
// [MDSPEC][R4-5.3] SEVENTH source, same ruling shape: the LQ
// response-pairing point (LSQUnit::completeDataAccess — CHAOSLSQFwd
// --lsqfwd_l04, model L04) is an F6 event source: L04's specified event
// IS the load response arriving while another same-shape load is in
// flight (the model's trigger condition "同时存在至少两个在途load且发生
// cache response"). Same non-ride: the pairing hook calls onF6Event(false)
// directly at the eligible response (the completeDataAccess hook is the
// attempt stream; store/atomic/squashed responses and no-candidate
// arrivals return before the event — attempted, never the F6 event).
//
// [MDSPEC][R4-5.7] EIGHTH source, same ruling shape: the StoreSet
// SSID-assignment training event (StoreSet::violation's new-SSID arm —
// CHAOSLSQFwd --lsqfwd_s10, model S10; the workbook trigger "load/store
// alias训练后" IS the violation retrain that assigns a fresh SSID) is an
// F6 event source. Same non-ride: the S10 subst hook calls onF6Event(false)
// directly at the eligible assignment (the StoreSet::violation top is the
// attempt stream — s10ViolationCb; violations that retrain existing sets
// and assignment events with no other live store set return before the
// event — attempted, never the F6 event). NOTE: the S10 matrix rows carry
// no F6 cells (F0/F2/F5 only); this ruling records the event-source shape
// for completeness. HISTORICAL CONFLATION, kept deliberately: the W5
// commit 7af6eed4 also calls chaosLsuF6Observe(SqForward) at this site —
// SSIT-training events are counted into the SqForward supply counter (the
// true W1 SqForward source is the lsq_unit.cc forward branch). Removing
// it would change the event supply of already-landed F6 cells; recorded
// here and in the R4-5.7 report, not silently altered.
enum class ChaOSLsuEvent : uint8_t { TlbHit, SqForward, DirtyEviction,
                                     CasSuccess };

// F6 event-source notification hook. The four sources (lsq_unit.cc forward
// branch, cache.cc DirtyBit eviction, base.cc SwapReq commit, tlb.cc lookup
// hit) each call this when the configured consumer registered a callback.
// Inline global in a header-only TU included by exactly one .cc each —
// single consumer registers at startup, deregisters at exit.
inline void (*chaosLsuF6Notify)(ChaOSLsuEvent) = nullptr;

// [LSU][OBS-1] Per-type F6 event-source observation counters (F-047 C-class
// count-only gate): count at EVERY notify site regardless of consumer
// registration, so count-only runs quantify F6 event supply even when the
// mounted injector never registered a consumer (CHAOSLSQFwd pre-SEM-A:
// injected was structurally 0 under ANY workload). Observation only — the
// dispatch below is byte-for-byte the old null-checked call, so injection
// semantics are unchanged.
inline uint64_t chaosLsuF6EventsSeen[4] = {0, 0, 0, 0};

inline void
chaosLsuF6Observe(ChaOSLsuEvent e)
{
    ++chaosLsuF6EventsSeen[static_cast<unsigned>(e)];
    if (chaosLsuF6Notify)
        chaosLsuF6Notify(e);
}

// [LSU][OBS-1] End-of-run report line (called from the trigger summary so it
// prints whenever any injector+trigger is mounted — census and rerun cases).
inline void
chaosLsuF6EventsReport()
{
    printf("CHAOS_LSU_F6_EVENTS: TlbHit=%lu SqForward=%lu DirtyEviction=%lu "
           "CasSuccess=%lu\n",
           (unsigned long)chaosLsuF6EventsSeen[0],
           (unsigned long)chaosLsuF6EventsSeen[1],
           (unsigned long)chaosLsuF6EventsSeen[2],
           (unsigned long)chaosLsuF6EventsSeen[3]);
}

struct ChaOSLsuTrigger
{
    ChaOSLsuTier tier;
    ChaOSLsuEvent f6_event = ChaOSLsuEvent::SqForward;
    uint64_t rng;
    uint64_t warmup_events = 0;   // eligible events skipped before arming
    uint64_t span_events   = 0;   // F0: uniform window size (0 = fire at warmup)

    // funnel (04 L0; activated lands in W3 — R2)
    uint64_t attempted = 0;
    uint64_t eligible  = 0;
    uint64_t injected  = 0;

    // [LSU][OBS-3] eligible-event window diagnostics (B/E-class): tick of the
    // first / last eligible event — observation only, no semantic effect.
    uint64_t first_eligible_tick = 0;
    uint64_t last_eligible_tick  = 0;

  private:
    uint64_t next_fire = 0;       // eligible-count threshold (F1-F4)
    uint64_t burst_left = 0;      // F4: remaining burst shots (this shot incl.)
    uint64_t fired_at = 0;        // [R4-1-review-I2] F0: eligible count at fire
    bool spent  = false;          // F0/F6 fired once
    bool armed  = false;

    static constexpr uint64_t
    intervalEvents(ChaOSLsuTier t)
    {
        switch (t) {
          case ChaOSLsuTier::F1: return 1000000;
          case ChaOSLsuTier::F2: return  100000;
          case ChaOSLsuTier::F3: return   10000;
          case ChaOSLsuTier::F4: return  100000;   // burst trigger period
          default:               return       0;   // F0/F5/F6 not interval-based
        }
    }

    void
    scheduleNext(uint64_t from)
    {
        const uint64_t iv = intervalEvents(tier);
        rng = chaosSampleLCG(rng);
        next_fire = from + iv / 2 + rng % iv;      // mean ±50% (05 r3-r5)
    }

  public:
    ChaOSLsuTrigger(ChaOSLsuTier t, uint64_t seed, uint64_t warmup,
                    uint64_t span, ChaOSLsuEvent ev = ChaOSLsuEvent::SqForward)
        : tier(t), f6_event(ev), rng(seed ? seed : 1),
          warmup_events(warmup), span_events(span)
    {}

    // The injector calls this once per hook invocation (before any filter).
    void
    onAttempt()
    {
        ++attempted;
    }

    // The injector calls this when a candidate PASSED its eligibility filter
    // (target exists, window open, ...). Returns true => inject now.
    bool
    onEligible()
    {
        ++eligible;
        if (!first_eligible_tick) first_eligible_tick = curTick();
        last_eligible_tick = curTick();   // [LSU][OBS-3]
        switch (tier) {
          case ChaOSLsuTier::F5: {
              if (!armed && eligible > warmup_events) armed = true;
              if (!armed) return false;
              ++injected;                 // every eligible event from warm-up on
              return true;
          }
          case ChaOSLsuTier::F0: {
              if (spent) return false;
              if (!armed) {
                  armed = true;
                  const uint64_t span = span_events ? span_events : 1;
                  rng = chaosSampleLCG(rng);
                  next_fire = warmup_events + rng % span;
              }
              if (eligible >= next_fire) { spent = true; fired_at = eligible;
                                          ++injected; return true; }
              return false;
          }
          case ChaOSLsuTier::F1:
          case ChaOSLsuTier::F2:
          case ChaOSLsuTier::F3: {
              if (!armed) { armed = true; scheduleNext(warmup_events); }
              if (eligible < next_fire) return false;
              scheduleNext(next_fire);
              ++injected;
              return true;
          }
          case ChaOSLsuTier::F4: {
              if (burst_left) { --burst_left; ++injected; return true; }
              if (!armed) { armed = true; scheduleNext(warmup_events); }
              if (eligible < next_fire) return false;
              scheduleNext(next_fire);
              rng = chaosSampleLCG(rng);
              burst_left = 2 + rng % 3;   // 2-4 consecutive incl. this one
              --burst_left;               // this shot consumes one
              ++injected;
              return true;
          }
          case ChaOSLsuTier::F6:
              return false;               // F6 fires on the event, not here
        }
        return false;
    }

    // The F6 event source calls this when the configured event occurs.
    // Returns true => inject at this event, once ever.
    // book_attempt — two caller shapes, [MDSPEC][R4-5.1-review-I1]:
    //   true (default): the W1 thunk sites (CHAOSAddrPath/CHAOSPrefetch
    //     f6Thunk) have no attempt stream at the event-notification site —
    //     there the event occurrence IS the attempt, so it is booked here
    //     (pinned by tests/chaos_lsu_trigger_test.cc "100 stream + 1
    //     event"). The same-invocation double-count is impossible there:
    //     onF6Event() runs in the thunk, not inside a hook call that
    //     already did onAttempt().
    //   false: a hook-based caller that ALREADY counted this invocation via
    //     onAttempt() (CHAOSCache mshr_merge: the merge hook itself is the
    //     attempt stream). Booking attempted again here would count the
    //     firing hook invocation twice.
    bool
    onF6Event(bool book_attempt = true)
    {
        if (tier != ChaOSLsuTier::F6 || spent) return false;
        spent = true;
        if (book_attempt) ++attempted;
        ++eligible; ++injected;
        if (!first_eligible_tick) first_eligible_tick = curTick();
        last_eligible_tick = curTick();   // [LSU][OBS-3]
        return true;
    }

    // End-of-run summary (the injector's exit callback prints this).
    void
    summary(const char *injector) const
    {
        printf("CHAOS_LSU_TRIGGER: injector=%s tier=F%d attempted=%lu "
               "eligible=%lu injected=%lu first_eligible_tick=%lu "
               "last_eligible_tick=%lu (activated=W3-L0-layer)\n",
               injector, static_cast<int>(tier),
               (unsigned long)attempted, (unsigned long)eligible,
               (unsigned long)injected,
               (unsigned long)first_eligible_tick,
               (unsigned long)last_eligible_tick);
        chaosLsuF6EventsReport();   // [LSU][OBS-1] event-supply observation

        // [MDSPEC][R4-1-review-I2] LOUD F0 span diagnostics — the two
        // silent failure modes of a static span vs. the workload's real
        // eligible stream (the S01 root cause class). Printed right after
        // the summary line so it lands in the same stdout log the campaign
        // captures; NEVER buried:
        //   SPAN_UNREACHABLE — the hook fired (attempted>0) but the F0 draw
        //     landed beyond the observed eligible stream → injected=0
        //     (span larger than the stream, or the stream truncated).
        //   EARLY_BIAS — an injection happened AND the observed eligible
        //     stream ran past the draw window [warmup, warmup+span). Two
        //     readings, honestly both named: (a) span UNDER-COVERS the
        //     golden (uninjected) eligible stream — golden events beyond
        //     the window were unreachable, the "fires, looks healthy" bias
        //     mode; (b) span == the measured golden size and the injected
        //     FAULT ITSELF extended the stream (post-injection events) —
        //     not a sampling bias. fired_at (= eligible count at fire,
        //     always ≤ warmup+span-1) + the uninjected golden measurement
        //     adjudicate: excess events all post-date fired_at.
        if (tier == ChaOSLsuTier::F0) {
            const uint64_t eff_span = span_events ? span_events : 1;
            const uint64_t draw_end = warmup_events + eff_span;
            if (attempted > 0 && injected == 0)
                printf("CHAOS_LSU_TRIGGER_ALARM: injector=%s "
                       "mode=SPAN_UNREACHABLE attempted=%lu eligible=%lu "
                       "injected=%lu draw_next_fire=%lu span=%lu warmup=%lu "
                       "(F0 draw never landed inside the observed eligible "
                       "stream; no injection though the hook fired)\n",
                       injector, (unsigned long)attempted,
                       (unsigned long)eligible, (unsigned long)injected,
                       (unsigned long)next_fire,
                       (unsigned long)span_events,
                       (unsigned long)warmup_events);
            else if (injected > 0 && eligible >= draw_end)
                printf("CHAOS_LSU_TRIGGER_ALARM: injector=%s mode=EARLY_BIAS "
                       "attempted=%lu eligible=%lu injected=%lu fired_at=%lu "
                       "span=%lu warmup=%lu (observed eligible ran past the "
                       "F0 draw window [%lu,%lu): span under-covers the "
                       "golden stream = silent early bias, OR span == "
                       "measured golden and the fault extended the stream "
                       "past fired_at — adjudicate vs the uninjected golden "
                       "measurement)\n",
                       injector, (unsigned long)attempted,
                       (unsigned long)eligible, (unsigned long)injected,
                       (unsigned long)fired_at,
                       (unsigned long)span_events,
                       (unsigned long)warmup_events,
                       (unsigned long)warmup_events,
                       (unsigned long)(draw_end - 1));
        }
    }
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_LSU_TRIGGER_HH__
