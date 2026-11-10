#ifndef __CPU_O3_SQ03_RULES_HH__
#define __CPU_O3_SQ03_RULES_HH__

#include <cstdint>
#include <cstdlib>
#include <string>

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
    // SQ03 is one-shot by construction; max_faults==0 must not mean
    // "unlimited" here (that was the v3.2.7 HANG hazard).
    const uint64_t cap = (max_faults == 0) ? 1 : max_faults;
    if (injected >= cap)
        return false;
    return true;
}

// ---- v3.2.12 propagation closure (task 12): downstream-effect grading ------
// SQ03 sets _canWB early (executeStore instead of commitStores). The state
// change is real, but a field change alone is never propagation (task-12
// brief step 4). The downstream differences that ARE observable on the
// trace:
//   - the store drained (cache write) BEFORE its architectural commit
//     (visible_before_commit) with a reload consumer bound to the chain —
//     bytes architecturally not yet visible were read;
//   - the store drained but never committed (a squashed store whose bytes
//     reached memory — the SQ squash path stops at canWB-marked entries,
//     lsq_unit.cc squash(): "Instructions marked as can WB are already
//     committed", so the premature canWB defeats the squash guard).
// Anything else (correct data, drain after commit, no reload consumer) is
// LIFECYCLE_ONLY with reason NO_DOWNSTREAM_EFFECT.

// Absent-sentinel rule shared with chaos_fw02 / chaos_sq01 / chaos_sp05
// (standard v3.2.12 §3): empty / "null" / "None" / "0" are ABSENT hashes.
inline uint64_t
hashValue(const std::string &h)
{
    if (h.empty() || h == "null" || h == "None" || h == "0")
        return 0;
    return std::strtoull(h.c_str(), nullptr, 16);
}

enum class EffectOutcome
{
    LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT,
    CHAIN_VISIBILITY_MOVED,   // drain before commit + reload consumer
    CHAIN_PHANTOM_STORE       // drained, never committed
};

struct Sq03Effect
{
    bool canwb_before = false;
    bool canwb_after = false;
    uint64_t writeback_tick = 0;  // 0 = not observed (sq03_wb node)
    uint64_t drain_tick = 0;      // 0 = cache write not observed
    uint64_t commit_tick = 0;     // 0 = store never committed
    uint64_t reload_seq = 0;      // 0 = no reload bound to the chain
    std::string reload_data_hash; // reload response data hash
};

inline bool
stateChanged(const Sq03Effect &e)
{
    return !e.canwb_before && e.canwb_after;
}

inline bool
visibleBeforeCommit(const Sq03Effect &e)
{
    return e.drain_tick != 0 && e.commit_tick != 0
        && e.drain_tick < e.commit_tick;
}

inline bool
phantomDrain(const Sq03Effect &e)
{
    return e.drain_tick != 0 && e.commit_tick == 0;
}

inline EffectOutcome
effectVerdict(const Sq03Effect &e)
{
    if (!stateChanged(e))
        return EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT;
    if (phantomDrain(e))
        return EffectOutcome::CHAIN_PHANTOM_STORE;
    // The visibility-moved chain needs the reload consumer edge verifiable:
    // a reload with an absent response hash is an unverified edge (§3).
    if (visibleBeforeCommit(e) && e.reload_seq != 0
            && hashValue(e.reload_data_hash) != 0)
        return EffectOutcome::CHAIN_VISIBILITY_MOVED;
    return EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT;
}

inline const char *
effectReason(EffectOutcome o)
{
    switch (o) {
      case EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT:
          return "NO_DOWNSTREAM_EFFECT";
      case EffectOutcome::CHAIN_VISIBILITY_MOVED:
          return "DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER";
      case EffectOutcome::CHAIN_PHANTOM_STORE:
          return "DRAINED_WITHOUT_COMMIT";
    }
    return "NO_DOWNSTREAM_EFFECT";
}

inline const char *
effectOutcomeName(EffectOutcome o)
{
    switch (o) {
      case EffectOutcome::LIFECYCLE_ONLY_NO_DOWNSTREAM_EFFECT:
          return "LIFECYCLE_ONLY";
      case EffectOutcome::CHAIN_VISIBILITY_MOVED:
          return "CHAIN_VISIBILITY_MOVED";
      case EffectOutcome::CHAIN_PHANTOM_STORE:
          return "CHAIN_PHANTOM_STORE";
    }
    return "LIFECYCLE_ONLY";
}

} // namespace chaos_sq03
} // namespace gem5

#endif // __CPU_O3_SQ03_RULES_HH__
