#ifndef __CPU_O3_SP05_RULES_HH__
#define __CPU_O3_SP05_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_sp05
{

// v3.2.9: ordinal target selection. The fault is applied to the Nth store
// that earns canWB (a live, committed store), not to "the next call".
inline bool
shouldSelect(uint64_t eligible_count, uint64_t ordinal)
{
    return ordinal != 0 && eligible_count == ordinal;
}

// SP05-CFG01: one live store completion is premature. The target is
// identified by its SQ entry identity (index + generation), not by "the next
// completeStore call" (instant-complete paths defeat a next-call flag).
// max_faults==0 is clamped to one completion.
inline bool
shouldComplete(uint64_t sq_idx, uint64_t sq_gen, uint64_t target_idx,
               uint64_t target_gen, uint64_t injected, uint64_t max_faults)
{
    if (target_idx == 0 && target_gen == 0)
        return false;
    if (sq_idx != target_idx || sq_gen != target_gen)
        return false;
    const uint64_t cap = (max_faults == 0) ? 1 : max_faults;
    return injected < cap;
}

} // namespace chaos_sp05
} // namespace gem5

#endif
