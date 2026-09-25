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

namespace gem5
{

enum class ChaOSLsuTier : uint8_t { F0, F1, F2, F3, F4, F5, F6 };

// F6 event sources (09 §2.1 W1 map). TlbHit is FS-only — SE never calls
// TLB::lookup (arm/mmu.cc:323-365 translateSe); the enum value exists so the
// config surface is uniform, and an SE run selecting it logs zero events.
enum class ChaOSLsuEvent : uint8_t { TlbHit, SqForward, DirtyEviction,
                                     CasSuccess };

// F6 event-source notification hook. The four sources (lsq_unit.cc forward
// branch, cache.cc DirtyBit eviction, base.cc SwapReq commit, tlb.cc lookup
// hit) each call this when the configured consumer registered a callback.
// Inline global in a header-only TU included by exactly one .cc each —
// single consumer registers at startup, deregisters at exit.
inline void (*chaosLsuF6Notify)(ChaOSLsuEvent) = nullptr;

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

  private:
    uint64_t next_fire = 0;       // eligible-count threshold (F1-F4)
    uint64_t burst_left = 0;      // F4: remaining burst shots (this shot incl.)
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
              if (eligible >= next_fire) { spent = true; ++injected; return true; }
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
    bool
    onF6Event()
    {
        if (tier != ChaOSLsuTier::F6 || spent) return false;
        spent = true;
        ++attempted; ++eligible; ++injected;
        return true;
    }

    // End-of-run summary (the injector's exit callback prints this).
    void
    summary(const char *injector) const
    {
        printf("CHAOS_LSU_TRIGGER: injector=%s tier=F%d attempted=%lu "
               "eligible=%lu injected=%lu (activated=W3-L0-layer)\n",
               injector, static_cast<int>(tier),
               (unsigned long)attempted, (unsigned long)eligible,
               (unsigned long)injected);
    }
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_LSU_TRIGGER_HH__
