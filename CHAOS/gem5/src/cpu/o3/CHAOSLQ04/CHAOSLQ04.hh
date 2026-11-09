#ifndef __CPU_O3_CHAOS_LQ04_HH__
#define __CPU_O3_CHAOS_LQ04_HH__

#include <cstdint>

#include "base/output.hh"
#include "base/types.hh"
#include "params/CHAOSLQ04.hh"
#include "sim/eventq.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace o3 { class CPU; }
class BaseCPU;

// CHAOSLQ04 — Load-Queue entry lifetime fault injector (LSU v3.2.10 LQ04).
//
// Fault model: at the end of a successful LSQUnit::executeLoad (a live LQ
// entry whose request has just been issued), the entry's `valid` and
// `request` fields are moved into the Task-4 side channel
// (LSQEntry::corruptLifetime). The entry keeps its slot, its instruction
// and its queue position, but reads as invalid with no request until the
// boundary restore (commit/squash, LSQUnit::lq04Restore) puts the fields
// back before clear(). The fault is a structural lifetime fault — data,
// address and size are untouched, and the injection itself lives in
// lsq_unit.cc (Task 6); this SimObject only owns selection and logging.
//
// Selection is ordinal-driven and deterministic (F0, lq04_rules.hh): the
// eventOrdinal-th eligible Load is the target. A replayed load is never
// injected twice because the target is identified by its LQ entry identity
// (index + generation), not by "the next executeLoad call". The eligible
// stream (valid entry, owns its request, not squashed, not executed) is
// established by the call site; maybeSelect rejects prefetches so they do
// not consume an ordinal.
class CHAOSLQ04 : public SimObject
{
  public:
    CHAOSLQ04(const CHAOSLQ04Params &p);

    // Self-attach: reject non-O3 CPUs (std::runtime_error), set
    // cpu->chaosLQ04 = this, arm the watchdog, register exit callbacks.
    void startup() override;

    // Called at the end of LSQUnit::executeLoad (Task 6) for a live,
    // request-owning, un-squashed, un-executed load entry. Increments the
    // eligible-Load ordinal; logs up to probeFirstN
    // CHAOS_LQ04_ELIGIBLE_PROBE lines (count-only dry-run or probe mode);
    // returns true exactly once — on the eventOrdinal-th eligible load,
    // while the maxFaults budget lasts — meaning "this entry is the
    // target, corrupt its lifetime now". countOnly never returns true.
    bool maybeSelect(uint64_t seq, Addr pc, int64_t lq_idx, uint64_t lq_gen,
                     uint64_t attempt_id, Addr addr, unsigned size,
                     uint64_t request_id, bool is_prefetch);

    // Response-side probe (Task 6, completeDataAccess): is this dynamic
    // load the injected target? Matches the stored LQ entry identity via
    // chaos_lq04::identityMatches; seq is a defensive cross-check.
    bool isTarget(uint64_t seq, uint64_t lq_idx, uint64_t lq_gen) const;

    // Boundary restore observation (Task 6, LSQUnit::lq04Restore): the
    // target entry's corrupt window closed at a commit/squash boundary.
    // Non-target entries never had a window and are ignored.
    void noteRestore(uint64_t seq, uint64_t lq_idx, uint64_t lq_gen,
                     const char *reason);

    bool countOnly() const { return count_only; }
    uint64_t eligibleCount() const { return eligible_count; }
    uint64_t injectedCount() const { return injected_count; }
    uint64_t targetRequestId() const { return target_request_id; }
    uint64_t targetLqIdx() const { return target_lq_idx; }
    uint64_t targetLqGen() const { return target_lq_gen; }
    uint64_t targetSeq() const { return target_seq; }
    uint64_t eventOrdinal() const { return event_ordinal; }
    // Recorded for reproducibility; the ordinal-driven F0 model draws no
    // random numbers (unlike the probability-mode injectors).
    uint64_t rngSeed() const { return rng_seed; }

    // In-simulator watchdog: if the ordinal-selected injection has not
    // happened by watchdogCycles after startup() (and the run is still
    // going), log CHAOS_LQ04_WATCHDOG_EXPIRED and exit the simulation
    // with a non-zero code — a stuck run must not be classifiable as a
    // normal MASKED completion.
    void watchdog();

  private:
    BaseCPU *cpu;               // raw param; O3 check at startup()
    uint64_t event_ordinal;     // 1-based eligible ordinal; 0 = disabled
    uint64_t max_faults;        // 0 clamps to 1 (chaos_lq04::shouldInject)
    bool count_only;
    uint64_t probe_first_n;     // first-N eligible probe lines (0 = none)
    uint64_t watchdog_cycles;   // 0 = disabled
    uint64_t rng_seed;
    bool write_log;

    uint64_t eligible_count = 0;
    uint64_t injected_count = 0;
    uint64_t probe_logged = 0;

    bool target_selected = false;
    bool target_restored = false;
    uint64_t target_seq = 0;
    uint64_t target_lq_idx = 0;     // LQ index (non-negative once selected)
    uint64_t target_lq_gen = 0;
    uint64_t target_request_id = 0;
    uint64_t target_attempt_id = 0;

    EventFunctionWrapper *watchdog_event = nullptr;
    OutputStream *log_stream = nullptr;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_LQ04_HH__
