/*
 * [R6-A-SEGV 2026-10-28] Injected-VA registry shared by CHAOSAddrPath and the
 * SE page-table-fault path.
 *
 * Why: in SE there is no OS. When a CHAOS-injected effective address lands on
 * an unmapped page, GenericPageTableFault::invoke cannot be handled by the
 * process and gem5 panics/aborts — losing stats.txt and the gzip trailer of
 * prop_evt (the A01/A03 crash-evidence truncation class). On real hardware
 * that access delivers SIGSEGV to the user process and the app dies. This
 * registry lets the fault path recognise *injected* addresses and model that
 * faithful guest SEGV as a normal simulation exit (stats + trace flushed)
 * instead of a simulator panic. Baseline (non-injected) faults keep the
 * upstream panic behaviour.
 *
 * The set is bounded: F5 (stuck-at) re-registers the same VA on every event;
 * clearing on overflow is safe because the VA is re-added at the next
 * injection before the fault can occur.
 */

#ifndef __BASE_CHAOS_GUEST_FAULT_HH__
#define __BASE_CHAOS_GUEST_FAULT_HH__

#include <unordered_set>

#include "base/types.hh"

namespace gem5
{

namespace chaos
{

inline std::unordered_set<Addr> &
injectedGuestVas()
{
    static std::unordered_set<Addr> vas;
    return vas;
}

inline bool &
guestSegvArmed()
{
    static bool armed = false;
    return armed;
}

// Set once when CHAOSAddrPath is instantiated: from then on any *unhandled* SE
// page-table fault is an experiment outcome (the corrupted program can also
// dereference a wild pointer derived from the injected one), so it must be
// modelled as a guest SEGV instead of a gem5 panic. Baseline runs never arm
// this flag.
inline void
noteChaosAddrPathActive()
{
    guestSegvArmed() = true;
}

inline void
noteInjectedGuestVa(Addr va)
{
    guestSegvArmed() = true;
    auto &vas = injectedGuestVas();
    if (vas.size() >= 4096)
        vas.clear();
    vas.insert(va);
}

inline bool
consumeInjectedGuestVa(Addr va)
{
    auto &vas = injectedGuestVas();
    auto it = vas.find(va);
    if (it == vas.end())
        return false;
    vas.erase(it);
    return true;
}

} // namespace chaos

} // namespace gem5

#endif // __BASE_CHAOS_GUEST_FAULT_HH__
