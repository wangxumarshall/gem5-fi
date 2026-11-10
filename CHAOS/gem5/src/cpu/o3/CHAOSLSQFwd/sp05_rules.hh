#ifndef __CPU_O3_SP05_RULES_HH__
#define __CPU_O3_SP05_RULES_HH__

#include <cstdint>
#include <cstdlib>
#include <string>

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

// The completion hook cannot reach size-0 instant completions or data
// prefetches (writebackStores handles them before the SP05 check), so the
// ordinal must count only reachable stores.
inline bool
isSelectable(uint32_t size, bool is_prefetch)
{
    return size > 0 && !is_prefetch;
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

// ---- v3.2.12 propagation closure (task 13): stage vs. visibility ----------
// SP05 completes the selected store inside writebackStores BEFORE its cache
// write is sent; the send is skipped, so the store's bytes never reach the
// cache (drain_tick stays 0 — the honest record of a lost write; frozen
// SP05_Source_Audit_v3.2.9 §5: "A store whose write was dropped may make a
// later load read the old value (potential SDC) or may be unobservable
// (MASKED)"). The three stages are separated (task-13 brief step 1):
//   execution complete  completion_tick (the premature completeStore)
//   commit              commit_tick     (the store's architectural commit)
//   data visible        drain_tick      (the cache write; for SP05 the
//                       observable visibility event is instead a RELOAD
//                       reading what the skipped write left behind)
// Commit != visibility; both ticks are recorded. The record's data_correct
// field is the pure tri-state mapping dataCorrect() below (the exact
// semantics the emitChainRecord sp05_stage node prints): "1" the reload
// read exactly the store's intended bytes, "0" it read something else,
// "null" unknown (no reload observed, or a hash absent — §3).

// Absent-sentinel rule shared with chaos_fw02 / chaos_sq01 / chaos_sq03
// (standard v3.2.12 §3): empty / "null" / "None" / "0" are ABSENT hashes.
inline uint64_t
hashValue(const std::string &h)
{
    if (h.empty() || h == "null" || h == "None" || h == "0")
        return 0;
    return std::strtoull(h.c_str(), nullptr, 16);
}

enum class StageOutcome
{
    MASKED_DATA_WRITTEN_CORRECTLY, // reload read exactly the store's bytes
    CHAIN_VISIBILITY_LOST,         // reload read bytes != the store's data
    NO_RELOAD_OBSERVED,            // skipped write, no load read the lane
    RELOAD_UNVERIFIABLE            // reload bound but a hash is absent —
                                   // data_correct stays unknown, never a
                                   // claimed chain
};

struct Sp05Stage
{
    uint64_t completion_tick = 0; // 0 = not observed
    uint64_t commit_tick = 0;     // 0 = store never committed
    uint64_t writeback_tick = 0;  // writebackStores processed the entry
    uint64_t drain_tick = 0;      // 0 = the cache write never happened
    uint64_t reload_seq = 0;      // 0 = no reload bound to the chain
    std::string store_data_hash;  // the store's intended bytes
    std::string reload_data_hash; // what the reload actually read
};

inline StageOutcome
stageVerdict(const Sp05Stage &s)
{
    if (s.reload_seq == 0)
        return StageOutcome::NO_RELOAD_OBSERVED;
    if (hashValue(s.store_data_hash) == 0
            || hashValue(s.reload_data_hash) == 0)
        return StageOutcome::RELOAD_UNVERIFIABLE;
    if (hashValue(s.reload_data_hash) == hashValue(s.store_data_hash))
        return StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY;
    return StageOutcome::CHAIN_VISIBILITY_LOST;
}

inline const char *
maskingMechanism(StageOutcome o)
{
    return o == StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY
        ? "DATA_WRITTEN_CORRECTLY" : "NOT_APPLICABLE";
}

inline const char *
stageOutcomeName(StageOutcome o)
{
    switch (o) {
      case StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY:
          return "MASKED";
      case StageOutcome::CHAIN_VISIBILITY_LOST:
          return "CHAIN_VISIBILITY_LOST";
      case StageOutcome::NO_RELOAD_OBSERVED:
          return "NO_RELOAD_OBSERVED";
      case StageOutcome::RELOAD_UNVERIFIABLE:
          return "RELOAD_UNVERIFIABLE";
    }
    return "NO_RELOAD_OBSERVED";
}

// data_correct (task-13 brief interface): tri-state, honestly unknown when
// the verdict cannot see the bytes. Identical to the mapping the
// emitChainRecord sp05_stage node prints, so the record can never drift
// from the host-tested rule:
//   "1"    the reload read exactly the store's intended bytes
//          (MASKED_DATA_WRITTEN_CORRECTLY)
//   "0"    the reload read different bytes (CHAIN_VISIBILITY_LOST)
//   "null" no reload observed, or a bound hop's hash is absent (§3) —
//          unknown is reported as unknown, never as correct
inline const char *
dataCorrect(const Sp05Stage &s)
{
    switch (stageVerdict(s)) {
      case StageOutcome::MASKED_DATA_WRITTEN_CORRECTLY:
          return "1";
      case StageOutcome::CHAIN_VISIBILITY_LOST:
          return "0";
      default:
          return "null";
    }
}

// The definitive SP05 fact: completed without a drain — the write is lost.
// (Stage order note: the SP05 target is selected at commitStores — the
// store's architectural commit — and the premature completion happens later
// in writebackStores, so completion normally FOLLOWS commit. The stage
// separation that matters is completion/drain: a normal store completes
// only after its cache write; an SP05 store completes with no drain at all.
// Commit != visibility; the record carries both ticks for the audit.)
inline bool
writeSkipped(const Sp05Stage &s)
{
    return s.completion_tick != 0 && s.drain_tick == 0;
}

} // namespace chaos_sp05
} // namespace gem5

#endif
