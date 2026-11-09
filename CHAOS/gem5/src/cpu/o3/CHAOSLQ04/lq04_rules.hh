#ifndef __CPU_O3_LQ04_RULES_HH__
#define __CPU_O3_LQ04_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_lq04
{

// v3.2.10 LQ04: an eligible Load is one whose LQ entry is valid, still owns
// its request, is not squashed, and has not already completed an execution
// round. `LSQUnit::executeLoad` early-returns on `inst->isExecuted()`, so the
// executed flag keeps a repeated call from being counted as a new ordinal.
// The fault is applied only at the end of executeLoad, i.e. on a live entry
// whose request has just been issued.
inline bool
isEligible(bool valid, bool has_request, bool squashed, bool executed)
{
    return valid && has_request && !squashed && !executed;
}

// EventOrdinal is the 1-based ordinal of the eligible Load stream. Ordinal 0
// disables selection; only the N-th eligible Load is selected.
inline bool
shouldSelect(uint64_t eligible_count, uint64_t ordinal)
{
    return ordinal != 0 && eligible_count == ordinal;
}

// The target is identified by its LQ entry identity (index + generation), not
// by "the next executeLoad call"; a replayed Load must not be injected twice.
inline bool
identityMatches(uint64_t idx, uint64_t gen, uint64_t target_idx,
                uint64_t target_gen)
{
    return idx == target_idx && gen == target_gen;
}

// maxFaults == 0 is clamped to one injection.
inline bool
shouldInject(uint64_t injected, uint64_t max_faults)
{
    const uint64_t cap = (max_faults == 0) ? 1 : max_faults;
    return injected < cap;
}

} // namespace chaos_lq04
} // namespace gem5

#endif // __CPU_O3_LQ04_RULES_HH__
