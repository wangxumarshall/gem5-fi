#ifndef __CPU_O3_RP01_RULES_HH__
#define __CPU_O3_RP01_RULES_HH__

#include <cstdint>

namespace gem5
{
namespace chaos_rp01
{

// RP01 (LSU v3.2.12, design frozen in
// docs/gem5-fi/lsu/implementation_v3_2/rp01_design_v3_2_11/
// RP01_Final_Design_Gate_v3.2.11.md): skip exactly ONE
// iewStage->rescheduleMemInst(load_inst) call in the
// PartialAddrRangeCoverage branch of LSQUnit::read()
// (lsq_unit.cc:2016 at HEAD 8835d951). Everything else in the branch
// (stall record 2001-2008, ++replayGeneration 2012, clearIssued 2017,
// effAddrValid(false) 2018, request->discard() 2028,
// load_entry.setRequest(nullptr) 2029, return NoFault 2030) stays.
//
// Wake-up audit (task-14, this round): the call is the ONLY way this load
// attempt enters MemDepUnit::instsToReplay (IEW::rescheduleMemInst ->
// InstructionQueue::rescheduleMemInst -> MemDepUnit::reschedule,
// inst_queue.cc:1332 is its sole caller, and lsq_unit.cc:2016/1665 are the
// only two iewStage->rescheduleMemInst call sites repo-wide). The
// store-completion unstall paths (LSQUnit::completeStore lsq_unit.cc:1496,
// LSQUnit::storePostSend lsq_unit.cc:1357) call replayMemInst, which only
// DRAINS instsToReplay (MemDepUnit::replay, mem_dep_unit.cc:387-404) — a
// skipped load is absent, so it is never re-issued. Expected terminals:
// HANG/TIMEOUT (no older squash) or SQUASHED (older squash discards it).
// Never MASKED-with-normal-completion of the load; no SDC mechanism exists.

// Identity tuple recorded per eligible event. dyn_inst_seq + lq_idx +
// lq_gen identify the LQ entry attempt; store_seq identifies the partial
// stalling store; replay_gen is the POST-increment replayGeneration the
// caller observes at the call site (lsq_unit.cc:2012 runs before 2016, so
// the pre value is replay_gen - 1).
struct EventIdentity {
    uint64_t dyn_inst_seq;
    uint64_t lq_idx;
    uint64_t lq_gen;
    uint64_t store_seq;
    uint64_t replay_gen;

    bool operator==(const EventIdentity &o) const {
        return dyn_inst_seq == o.dyn_inst_seq && lq_idx == o.lq_idx &&
               lq_gen == o.lq_gen && store_seq == o.store_seq &&
               replay_gen == o.replay_gen;
    }
};

// Site-level eligibility beyond what the call site already guarantees
// (coverage == PartialAddrRangeCoverage, store not completed — the branch
// panics on a completed store at lsq_unit.cc:1994-1996). A squashed load
// must never consume an ordinal: its replay would be discarded anyway and
// would silently shift the ordinal space.
inline bool
isEligible(bool load_squashed)
{
    return !load_squashed;
}

// Ordinal rule (1-based, same convention as FW05/SP05 event ordinals):
// ordinal N selects exactly the Nth eligible event. eligible_count is the
// 1-based count of the event being judged (the caller increments BEFORE
// consulting). ordinal 0 = disabled, selects none. ordinal 999 (or any
// ordinal greater than the stream's eligible-event count) selects none —
// the preflight/pilot "select none" control inside fault mode.
inline bool
shouldSelect(uint64_t eligible_count, uint64_t ordinal)
{
    return ordinal != 0 && eligible_count == ordinal;
}

// Full skip decision for CHAOSLSQFwd::maybeSkipPartialReplay.
//  - count_only: never skip (the count-only preflight observes and records
//    every eligible event but changes nothing).
//  - already_skipped: one-shot guard; RP01 must fire at most once per run.
inline bool
shouldSkip(uint64_t eligible_count, uint64_t ordinal, bool count_only,
           bool already_skipped)
{
    if (count_only || already_skipped)
        return false;
    return shouldSelect(eligible_count, ordinal);
}

} // namespace chaos_rp01
} // namespace gem5

#endif // __CPU_O3_RP01_RULES_HH__
