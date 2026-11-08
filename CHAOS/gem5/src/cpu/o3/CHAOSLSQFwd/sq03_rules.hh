#ifndef __CPU_O3_SQ03_RULES_HH__
#define __CPU_O3_SQ03_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_sq03
{

// SQ03-CFG01: exactly one selected real store gets _canWB set early in
// executeStore (normal stores set it at commitStores). The caller must make
// the paired storesToWB increment so writebackStores/completeStore stay
// balanced. target_seq == 0 means no target; max_faults == 0 means unlimited.
inline bool
shouldSetCanWB(uint64_t store_seq, uint64_t target_seq,
               uint64_t injected, uint64_t max_faults)
{
    if (target_seq == 0 || store_seq != target_seq)
        return false;
    if (max_faults != 0 && injected >= max_faults)
        return false;
    return true;
}

} // namespace chaos_sq03
} // namespace gem5

#endif // __CPU_O3_SQ03_RULES_HH__
