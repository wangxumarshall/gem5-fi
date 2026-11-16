#ifndef __CPU_O3_MD04_RULES_HH__
#define __CPU_O3_MD04_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_md04
{

// MD04-ELIG-v1 (frozen 2026-11-08): a real 8-byte store -> younger-load
// violation whose report is suppressed exactly once. The pair must satisfy
// the same shifted-range predicate as LSQUnit::checkViolations AND have a
// real byte overlap (so "different address" pairs that happen to share an
// 8-byte chunk are excluded). A 16-byte LDP covering the store is included;
// a 4-byte access is not. Only the violation report is suppressed.
inline bool
isEligibleViolationPair(uint64_t load_addr, unsigned load_size,
                        uint64_t store_addr, unsigned store_size,
                        unsigned dep_check_shift)
{
    if (store_size != 8 || load_size < 8)
        return false;

    const uint64_t s_lo = store_addr;
    const uint64_t s_hi = store_addr + store_size - 1;
    const uint64_t l_lo = load_addr;
    const uint64_t l_hi = load_addr + load_size - 1;

    // Require a real byte overlap.
    if (s_hi < l_lo || l_hi < s_lo)
        return false;

    // Same shifted-range predicate as checkViolations.
    const uint64_t ss_lo = store_addr >> dep_check_shift;
    const uint64_t ss_hi = (store_addr + store_size - 1) >> dep_check_shift;
    const uint64_t ls_lo = load_addr >> dep_check_shift;
    const uint64_t ls_hi = (load_addr + load_size - 1) >> dep_check_shift;
    return ss_hi >= ls_lo && ss_lo <= ls_hi;
}

// 1-based eligible-event selection. target_ordinal == 0 means "the first
// eligible event"; max_faults == 0 means unlimited.
inline bool
shouldInject(uint64_t eligible_ordinal, uint64_t target_ordinal,
             uint64_t injected, uint64_t max_faults)
{
    if (max_faults != 0 && injected >= max_faults)
        return false;
    if (target_ordinal != 0 && eligible_ordinal != target_ordinal)
        return false;
    return true;
}

} // namespace chaos_md04
} // namespace gem5

#endif // __CPU_O3_MD04_RULES_HH__
