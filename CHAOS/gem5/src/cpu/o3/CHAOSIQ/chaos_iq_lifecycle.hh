// §2.5 FQ08 lifecycle model (pure C++; host-unit-testable).
//
// This header holds the parts of the CHAOSIQ FQ08 fixes that are pure state
// machines, so they can be compiled and exercised with the host g++ without a
// gem5 build:
//
//   FQ08-b  src_ready_bitflip accounting
//     eligible / attempted / applied / activated are SEPARATE counters.  The
//     gate only records an ATTEMPT; a fault is APPLIED only when a live victim
//     instruction is actually modified.  An attempt that finds no victim is
//     dropped without touching applied/activated and without consuming the
//     max_faults budget.
//
//   FQ08-c  delayed-wake lifecycle
//     A delayed wake carries a value snapshot of the producer identity
//     (sequence number, thread) and of every destination physical register's
//     allocation generation.  At fire time the snapshot is compared against the
//     live DynInst/PhysRegFile; a squashed producer, a freed/reallocated
//     physical slot or an identity mismatch makes the event a safe no-op
//     instead of re-entering InstructionQueue::wakeDependents.
//
// The gem5-side code (CHAOSIQ.cc) calls these functions directly, so the
// behaviour tested here is the behaviour that runs in gem5.
//
// Build/run (no gem5):
//   g++ -O0 -std=c++17 -Wall -Wextra -Werror
//       -I CHAOS/gem5/src/cpu/o3/CHAOSIQ
//       tests/unit/chaos_iq_lifecycle_test.cc -o /tmp/chaos_iq_lifecycle
//       && /tmp/chaos_iq_lifecycle

#ifndef __CPU_O3_CHAOS_IQ_LIFECYCLE_HH__
#define __CPU_O3_CHAOS_IQ_LIFECYCLE_HH__

#include <cstddef>
#include <cstdint>
#include <vector>

namespace gem5
{
namespace chaos_iq_lifecycle
{

// ---------------------------------------------------------------------------
// FQ08-b: src_ready_bitflip accounting
// ---------------------------------------------------------------------------

struct Counters
{
    /** Events that reached the mode/window/class filters. */
    uint64_t eligible = 0;
    /** Gate hits (window + skip + probability draw). Never counts as a fault. */
    uint64_t attempted = 0;
    /** Attempts that modified a live victim (consumes the max_faults budget). */
    uint64_t applied = 0;
    /** Applied injections whose wrong-source ready write alone made the victim
     *  issue-able (ready count reached numSrcRegs at the write). */
    uint64_t activated = 0;
    /** Attempts that were dropped because no eligible victim was seen. */
    uint64_t no_victim = 0;
};

/** One gate hit waiting for a real victim inside the caller's dependent loop. */
struct Attempt
{
    bool pending = false;
    uint64_t producer_sn = 0;
    unsigned producer_tid = 0;
    uint64_t tick = 0;
};

inline void
beginAttempt(Attempt &a, uint64_t producer_sn, unsigned producer_tid,
             uint64_t tick)
{
    a.pending = true;
    a.producer_sn = producer_sn;
    a.producer_tid = producer_tid;
    a.tick = tick;
}

/** A new producer wake invalidates an attempt that never found a victim.
 *  Returns true when a pending attempt was dropped (counted in no_victim). */
inline bool
abortPendingAttempt(Attempt &a, Counters &c)
{
    if (!a.pending)
        return false;
    a.pending = false;
    ++c.no_victim;
    return true;
}

/**
 * Victim description, filled from DynInst by the gem5 hook.
 *
 * `slot`/`flat`/`unready` are parallel arrays over the source-register slots
 * of the configured target register class (IntRegClass for the W5 scope,
 * VecRegClass for the FP/SIMD scope).  `flat` is the physical register's
 * flatIndex, i.e. the dependency-chain id.
 */
struct VictimView
{
    bool squashed = false;
    bool issued = false;
    unsigned ready_regs = 0;
    unsigned num_src_regs = 0;
    std::vector<unsigned> slot;
    std::vector<uint64_t> flat;
    std::vector<uint8_t> unready;
};

inline bool
victimEligible(const VictimView &v)
{
    // A fully-ready instruction would issue anyway (no fault content), a
    // squashed one is dead, and an already-issued one must never be woken
    // again (it would be pushed onto the ready list a second time).
    return !v.squashed && !v.issued && v.ready_regs < v.num_src_regs;
}

/**
 * Choose the WRONG source slot of this dependent: an unready target-class slot
 * whose physical id is NOT the chain the normal wake is consuming.
 *
 * Returning -1 means "no victim on this dependent"; the caller must keep the
 * attempt pending (a later dependent of the same wake may still be eligible)
 * and must not count applied/activated.
 */
inline int
chooseWrongSlot(const VictimView &v, uint64_t chain_flat)
{
    if (!victimEligible(v))
        return -1;
    const std::size_t n = v.slot.size();
    for (std::size_t i = 0; i < n; ++i) {
        if (!v.unready[i])
            continue;
        if (i < v.flat.size() && v.flat[i] == chain_flat)
            continue;
        return static_cast<int>(v.slot[i]);
    }
    return -1;
}

struct ApplyOutcome
{
    bool applied = false;
    bool activated = false;
};

/**
 * Tracking of the injected victim so the GENUINE wake of the corrupted source
 * is suppressed exactly once.
 *
 * The injection marks an unready source slot ready without removing the
 * victim from that source's dependency chain (CHAOSIQ cannot reach
 * InstructionQueue::dependGraph). When that source's producer later completes
 * it will pop the victim and call markSrcRegReady()/addIfReady() again; without
 * suppression the source would be counted twice and the victim could be pushed
 * onto the ready list a second time after it has already issued. The old
 * in-caller surgery popped the chain it corrupted, which is the property this
 * one-shot suppression restores.
 */
struct DuplicateWake
{
    bool tracked = false;
    uint64_t victim_sn = 0;
    unsigned victim_tid = 0;
    uint64_t corrupt_flat = 0;
};

inline void
recordDuplicateWake(DuplicateWake &d, uint64_t victim_sn, unsigned victim_tid,
                    uint64_t corrupt_flat)
{
    d.tracked = true;
    d.victim_sn = victim_sn;
    d.victim_tid = victim_tid;
    d.corrupt_flat = corrupt_flat;
}

/** True exactly once: this popped dependent is our injected victim reaching
 *  the genuine wake of the source we already marked ready. */
inline bool
suppressDuplicateWake(DuplicateWake &d, uint64_t dep_sn, unsigned dep_tid,
                      uint64_t chain_flat)
{
    if (!d.tracked)
        return false;
    if (dep_sn != d.victim_sn || dep_tid != d.victim_tid ||
            chain_flat != d.corrupt_flat)
        return false;
    d.tracked = false;
    return true;
}

/** Accounting for a wrong-source ready write that really happened. */
inline ApplyOutcome
noteApplied(Counters &c, bool issueable_before, bool issueable_after)
{
    ApplyOutcome o;
    o.applied = true;
    ++c.applied;
    if (!issueable_before && issueable_after) {
        o.activated = true;
        ++c.activated;
    }
    return o;
}

// ---------------------------------------------------------------------------
// FQ08-c: delayed-wake identity + generation validation
// ---------------------------------------------------------------------------

/** Allocation-generation stamp of one destination physical register. */
struct DestStamp
{
    uint64_t flat = ~uint64_t(0);
    uint32_t generation = 0;
};

inline bool
operator==(const DestStamp &a, const DestStamp &b)
{
    return a.flat == b.flat && a.generation == b.generation;
}

inline bool
operator!=(const DestStamp &a, const DestStamp &b)
{
    return !(a == b);
}

/** Value snapshot taken when the delayed event is scheduled. */
struct WakeStamp
{
    uint64_t seq_num = 0;
    unsigned tid = 0;
    std::vector<DestStamp> dests;
};

/** Live observation taken when the delayed event fires. */
struct WakeObserved
{
    bool has_inst = false;
    uint64_t seq_num = 0;
    unsigned tid = 0;
    bool squashed = false;
    std::vector<DestStamp> dests;
};

enum class WakeDecision
{
    Fire,
    IgnoreNoInst,
    IgnoreIdentity,
    IgnoreSquashed,
    IgnoreGeneration,
};

inline const char *
wakeDecisionName(WakeDecision d)
{
    switch (d) {
      case WakeDecision::Fire: return "fire";
      case WakeDecision::IgnoreNoInst: return "ignore_no_inst";
      case WakeDecision::IgnoreIdentity: return "ignore_identity";
      case WakeDecision::IgnoreSquashed: return "ignore_squashed";
      case WakeDecision::IgnoreGeneration: return "ignore_generation";
    }
    return "unknown";
}

/**
 * Decide whether the delayed wake may re-enter wakeDependents.
 *
 * Order matters: identity first (the object must be the same instruction),
 * then squash (a dead producer must never be woken), then generation (a
 * freed/reallocated destination slot belongs to a new producer; waking it
 * would touch the new occupant's dependency chain and could trip the
 * dependGraph empty-assert).
 */
inline WakeDecision
classifyWake(const WakeStamp &stamp, const WakeObserved &now)
{
    if (!now.has_inst)
        return WakeDecision::IgnoreNoInst;
    if (now.seq_num != stamp.seq_num || now.tid != stamp.tid)
        return WakeDecision::IgnoreIdentity;
    if (now.squashed)
        return WakeDecision::IgnoreSquashed;
    if (now.dests.size() != stamp.dests.size())
        return WakeDecision::IgnoreIdentity;
    for (std::size_t i = 0; i < stamp.dests.size(); ++i) {
        if (stamp.dests[i] != now.dests[i])
            return WakeDecision::IgnoreGeneration;
    }
    return WakeDecision::Fire;
}

struct DelayedWakeCounters
{
    uint64_t scheduled = 0;
    uint64_t fired = 0;
    uint64_t ignored_no_inst = 0;
    uint64_t ignored_identity = 0;
    uint64_t ignored_squashed = 0;
    uint64_t ignored_generation = 0;
};

inline void
noteWakeDecision(DelayedWakeCounters &c, WakeDecision d)
{
    switch (d) {
      case WakeDecision::Fire: ++c.fired; break;
      case WakeDecision::IgnoreNoInst: ++c.ignored_no_inst; break;
      case WakeDecision::IgnoreIdentity: ++c.ignored_identity; break;
      case WakeDecision::IgnoreSquashed: ++c.ignored_squashed; break;
      case WakeDecision::IgnoreGeneration: ++c.ignored_generation; break;
    }
}

} // namespace chaos_iq_lifecycle
} // namespace gem5

#endif // __CPU_O3_CHAOS_IQ_LIFECYCLE_HH__
