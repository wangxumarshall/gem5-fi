/*
 * chaos_event_trigger.hh — OoO-track event-normalized F0-F6 trigger
 * (implementation-plan.md Task WS4.1; docs/gem5-fi/ooo/05-frequency-and-
 * statistics.md). The OoO book's 05 table specifies the same eligible-event
 * normalized semantics as the LSU book's (F0 uniform-after-warm-up / F1-F3
 * mean intervals 1M/100K/10K eligible events, ±50% jitter / F4 burst 2-4
 * consecutive per 100K / F5 permanent from warm-up / F6 first occurrence of
 * the specified event injects once), so this header ALIASES the LSU
 * implementation instead of reimplementing it — plan WS4 ruling: "不允许出现
 * 第三种语义" (no third semantics). Aliasing is the enforcement: a semantic
 * fix on the LSU side propagates here for free, and the standalone tests
 * pin the alias with static_assert.
 *
 * OoO additions on top of the alias:
 *   ChaOSOooEvent   — the OoO F6 event sources (d-bridge D14/D18 semantics;
 *                     risk R1 initial set: BranchMispredict=D14 anchor,
 *                     RenameSquash=D18 anchor; CommitSquash is declared for
 *                     the WB1 audit to extend — no call site until each new
 *                     source carries no-injection event-count evidence).
 *   chaosOooF6Notify — single-consumer notification hook, same discipline as
 *                     chaosLsuF6Notify (one OoO consumer per run; the
 *                     310-cell grid runs one injector per run by
 *                     construction).
 *   chaosEventTriggerSummary — the OoO end-of-run summary line prints the
 *                     CHAOS_EVENT_TRIGGER: prefix (the LSU track's
 *                     CHAOS_LSU_TRIGGER: line stays byte-identical; the
 *                     runner/lsu_l5_classify regexes widen to accept both —
 *                     plan WS4).
 *
 * Header-only, no SConscript entry — same precedent as chaos_lsu_trigger.hh.
 */
#ifndef __CPU_O3_CHAOS_EVENT_TRIGGER_HH__
#define __CPU_O3_CHAOS_EVENT_TRIGGER_HH__

#include <cstdint>
#include <cstdio>

#include "cpu/o3/chaos_lsu_trigger.hh"

namespace gem5
{

// The tier enum and trigger machinery are the LSU track's, aliased verbatim.
using ChaOSEventTier = ChaOSLsuTier;
using ChaOSEventTrigger = ChaOSLsuTrigger;

// OoO F6 event sources (WS4 Interfaces; d-bridge D14/D18).
enum class ChaOSOooEvent : uint8_t { BranchMispredict, RenameSquash,
                                     CommitSquash };

// Single-consumer F6 notification hook. The O3 CPU event sources call this
// when the configured consumer registered a callback; the consumer compares
// the event against its configured ChaOSOooEvent and feeds the match into
// ChaOSEventTrigger::onF6Event().
inline void (*chaosOooF6Notify)(ChaOSOooEvent) = nullptr;

// OoO end-of-run summary (the injector's exit callback prints this). Reads
// the public funnel counters of the aliased trigger; the LSU summary method
// is untouched.
inline void
chaosEventTriggerSummary(const ChaOSLsuTrigger &t, const char *injector)
{
    printf("CHAOS_EVENT_TRIGGER: injector=%s tier=F%d attempted=%lu "
           "eligible=%lu injected=%lu\n",
           injector, static_cast<int>(t.tier),
           (unsigned long)t.attempted, (unsigned long)t.eligible,
           (unsigned long)t.injected);
}

} // namespace gem5

#endif // __CPU_O3_CHAOS_EVENT_TRIGGER_HH__
