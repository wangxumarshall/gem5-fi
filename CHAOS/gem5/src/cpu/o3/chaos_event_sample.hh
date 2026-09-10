/*
 * chaos_event_sample.hh — v1.1 Phase 8.2 uniform event-sampling helper
 * (design doc §1.7 rule 4; task_plan Phase 8.2).
 *
 * PROBLEM (the geometric-skip bias): every CHAOS hook-on-event injector
 * (FPU/Exec/L1DForward/LSQFwd/IQ/...) draws
 *     events_to_skip ~ geometric(p=0.1)
 * from its RNG to land maxFaults=1 on a "seed-dependent" eligible event.
 * geometric(0.1) has MEAN 10 and a heavy forward skew: P(skip <= 30) ≈ 96%.
 * Under a long ROI with thousands of eligible events, the single fault
 * therefore lands in the FIRST ~30 events for almost every rep — the
 * sampled "distribution" is not the eligible-event distribution at all,
 * it is the head of it (findings.md Phase 3.0 family; the l1dfwd formal
 * measured one squashed wrong-path load until this was patched, and even
 * the patched version only spreads over the head).
 *
 * FIX (two-piece, per the design doc):
 *  1. countOnlyMode: the injector CONSUMES eligible events without
 *     corrupting and prints
 *         CHAOS_ELIGIBLE_COUNT=<n>
 *     to its log at end-of-sim (or when counting is stopped). A driver
 *     (campaign.py) dry-runs the cell once in count mode to learn
 *     N_eligible — the number of eligible events inside the ROI window.
 *  2. pickSkip(seed, nEligible): a seed-derived UNIFORM draw
 *         skip = lcg(seed) % nEligible
 *     so the single fault lands uniformly over [0, N_eligible). The
 *     driver passes the fixed skip back via the injector's
 *     eventsToSkip param (no per-injector RNG dependence for placement).
 *
 * The LCG is the same one the smoke kernels use (Knuth MMIX-ish
 * 6364136223846793005 / 1442695040888963407) — cheap, deterministic,
 * dependency-free, and identical across hosts (std::mt19937 is also
 * portable, but an explicit LCG keeps this header SimObject-free and
 * trivially auditable).
 *
 * Header-only: no SConscript entry needed (include path cpu/o3 is on
 * CPPPATH for all o3 sources and the CHAOS injector subdirs).
 */
#ifndef __CPU_O3_CHAOS_EVENT_SAMPLE_HH__
#define __CPU_O3_CHAOS_EVENT_SAMPLE_HH__

#include <cstdint>

namespace gem5
{

/** Seed-mixed LCG step — one round so the low bits are not the raw seed. */
inline uint64_t
chaosSampleLCG(uint64_t x)
{
    return x * 6364136223846793005ULL + 1442695040888963407ULL;
}

/**
 * Uniform skip over [0, nEligible). Returns 0 when nEligible == 0 (no
 * eligible events — inject on the first one, which will not exist
 * anyway). nEligible == 1 -> 0 (the only eligible event).
 */
inline uint64_t
chaosPickSkip(uint64_t seed, uint64_t n_eligible)
{
    if (n_eligible == 0) return 0;
    return chaosSampleLCG(seed ^ 0x9e3779b97f4a7c15ULL) % n_eligible;
}

} // namespace gem5

#endif // __CPU_O3_CHAOS_EVENT_SAMPLE_HH__
