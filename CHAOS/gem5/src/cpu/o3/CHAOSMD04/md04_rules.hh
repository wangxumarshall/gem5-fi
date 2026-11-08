#ifndef __CPU_O3_MD04_RULES_HH__
#define __CPU_O3_MD04_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_md04
{

// MD04-CFG01 (Excel option A): a real same-address 8-byte store alias whose
// memory-dependency violation is reported exactly once. The store is 8 bytes
// at the load's start address; a wider load (e.g. a 16-byte LDP) that covers
// the store is a real same-address alias and is included. A 4-byte pair or a
// different address is not. Only the violation report is suppressed.
inline bool
isSameAddress8B(uint64_t load_addr, unsigned load_size,
                uint64_t store_addr, unsigned store_size)
{
    return store_size == 8 && load_size >= 8 && load_addr == store_addr;
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
