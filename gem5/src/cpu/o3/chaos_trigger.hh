/*
 * chaos_trigger.hh — OoO north-star F0-F5 unified trigger semantics
 * (docs/gem5-fi/ooo/02-frequency-and-sampling.md; 06-implementation-plan
 * W0.2). Header-only like chaos_event_sample.hh (no SConscript entry).
 *
 * Tiers: F0 single uniform over [first,last) — REQUIRES explicit last_cycle
 * (last_cycle==0 degenerates to firing at first_cycle); F1/F2/F3 fixed mean
 * interval with ±50% jitter (1ms/100µs/10µs @2.6GHz = 2.6M/260K/26K cycles);
 * F5 permanent defect (always true — the injector applies the stuck mask on
 * every write; timing is not its dimension). Poll fire() at the injector's
 * hook; intervals are in CPU cycles.
 */
#ifndef __CPU_O3_CHAOS_TRIGGER_HH__
#define __CPU_O3_CHAOS_TRIGGER_HH__

#include <cstdint>

#include "cpu/o3/chaos_event_sample.hh"

namespace gem5
{

enum class ChaOSTier : uint8_t
{
    F0, F1, F2, F3, F5
};

struct ChaOSTrigger
{
    ChaOSTier tier;
    uint64_t rng;
    uint64_t first_cycle;
    uint64_t last_cycle;   // 0 = unbounded (F0: see header comment)
    uint64_t next_fire = 0;
    bool spent = false;    // F0 fired once
    bool armed = false;

    ChaOSTrigger(ChaOSTier t, uint64_t seed, uint64_t first, uint64_t last)
        : tier(t), rng(seed ? seed : 1), first_cycle(first), last_cycle(last)
    {}

    static constexpr uint64_t
    intervalCycles(ChaOSTier t)
    {
        switch (t) {
          case ChaOSTier::F1: return 2600000;
          case ChaOSTier::F2: return   260000;
          case ChaOSTier::F3: return    26000;
          default:            return        0;   // F0/F5: not interval-based
        }
    }

    bool
    fire(uint64_t now)
    {
        switch (tier) {
          case ChaOSTier::F5:
            return true;
          case ChaOSTier::F0: {
            if (spent) return false;
            if (!armed) {
                armed = true;
                const uint64_t span = (last_cycle > first_cycle)
                                    ? last_cycle - first_cycle : 1;
                next_fire = first_cycle + chaosSampleLCG(rng) % span;
            }
            if (now >= next_fire) { spent = true; return true; }
            return false;
          }
          default: {              // F1/F2/F3
            if (!armed) { armed = true; scheduleNext(first_cycle); }
            if (now < next_fire) return false;
            scheduleNext(next_fire);
            return true;
          }
        }
    }

  private:
    void
    scheduleNext(uint64_t from)
    {
        // mean interval ±50%: from + U[iv/2, 3*iv/2)
        const uint64_t iv = intervalCycles(tier);
        rng = chaosSampleLCG(rng);
        next_fire = from + iv / 2 + rng % iv;
    }
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_TRIGGER_HH__
