/*
 * chaos_l0.hh — L0 injection-item lifecycle interface (OoO north star
 * docs/gem5-fi/ooo/01-observation-points.md L0; normative contract in
 * docs/gem5-fi/ooo/07-l0-lifecycle-interface.md; implementation plan W2.5).
 *
 * Header-only like chaos_trigger.hh / chaos_event_sample.hh (no SConscript
 * entry; include path cpu/o3 is on CPPPATH for all o3 sources and the CHAOS
 * injector subdirs — same pattern CHAOSFPU.cc uses for
 * chaos_event_sample.hh).
 *
 * THE L0 QUESTION (01-observation-points.md, verbatim intent): was the
 * injected item/field ever REALLY READ by later logic before it was
 * overwritten or the run ended? A miss (reads==0) is an INVALID injection:
 * it must NOT enter the SDC denominator (a statistical-口径 issue, not a
 * fault effect). This header is the single shared contract every injector
 * wires so that judgement is made uniformly.
 *
 * THREE FIELDS (per injected item; one tracked item per injector instance —
 * the campaign maxFaults=1 discipline; re-registration overwrites, last
 * injection wins):
 *   reads_before_overwrite  uint64   real reads of the injected item after
 *                                    injection and before overwrite/sim-end
 *   overwritten             bool     was the injected item overwritten
 *   overwritten_at_cycle    uint64   cycle at which the overwrite was
 *                                    DETECTED; 0 = never overwritten
 *
 * HOOK TEMPLATE — three inline functions (the injector-side contract):
 *   chaosL0Register(st, key)            inject time: shared registration
 *                                       entry; key = the target id in the
 *                                       container's own numbering (phys reg
 *                                       idx, RAT entry arch id, ROB/IQ slot
 *                                       key, ...)
 *   chaosL0CountRead(st, key)           read-side hook: call on EVERY real
 *                                       read in the container; counts only
 *                                       the matching key and stops once
 *                                       overwritten (reads after overwrite
 *                                       are of the NEW value — not ours)
 *   chaosL0Overwrite(st, key, cycle)    write-side hook: call on every
 *                                       container write; the first
 *                                       matching-key write marks the item
 *                                       overwritten and stamps the cycle
 * exactly. This is the W4-W7 pattern for injectors that OWN their hooks
 * (their corrupted value lives in a structure they control).
 *
 * CONTAINER-OWNED HOOKS (the CHAOSPhysReg pattern — first instance of this
 * interface): when the corrupted value lives in shared gem5 state (here
 * PhysRegFile), the read/write-side hooks are IN the container
 * (regfile.hh getReg/setReg count reads / detect overwrite against the
 * registered key) and the injector cannot call chaosL0CountRead itself.
 * For that pattern use chaosL0Sync(st, reads, overwritten, cycle) at each
 * observation point (poll / exit): it mirrors the container counters into
 * the L0 state with once-only overwrite stamping. at= is then
 * observation-granular (poll or exit cycle), NOT the exact write cycle —
 * documented honestly in 07 §3.3.
 *
 * OUTPUT (pinned, end of sim; goes to the injector log file, NOT stdout —
 * stdout must stay byte-stable for FINAL/golden compares, W2.1 discipline):
 *   CHAOS_L0: <injector>: target=<id> reads=<n> overwritten=<0/1> at=<cycle> hit=<0/1>
 * hit = reads_before_overwrite > 0 (the valid-injection verdict). The line
 * is printed exactly once per run from a registerExitCallback (a poll
 * scheduled beyond the workload's halt cycle never fires — observed on
 * smoke; CHAOSProbe/CHAOSMicroSnap exit-callback precedent). Crash/abort
 * paths do not run exit callbacks: no CHAOS_L0 line on Crash runs (same
 * family as the W2.3 truncated-gzip discovery).
 */
#ifndef __CPU_O3_CHAOS_L0_HH__
#define __CPU_O3_CHAOS_L0_HH__

#include <cstdint>
#include <string>

namespace gem5
{

/** Per-injector L0 lifecycle state (one tracked item; see header comment). */
struct ChaOSL0State
{
    bool active = false;              // an item is registered (injected)
    uint64_t target_key = 0;          // container-side id of the item
    uint64_t reads_before_overwrite = 0;
    bool overwritten = false;
    uint64_t overwritten_at_cycle = 0;    // 0 = not overwritten
};

/** Hook 1 — inject-time registration (shared registration entry).
 *  Resets the lifecycle bookkeeping for a newly injected item. */
inline void
chaosL0Register(ChaOSL0State &st, uint64_t key)
{
    st.active = true;
    st.target_key = key;
    st.reads_before_overwrite = 0;
    st.overwritten = false;
    st.overwritten_at_cycle = 0;
}

/** Hook 2 — read-side hook: count one real read of the injected item.
 *  Non-matching keys are ignored; reads after overwrite are of the new
 *  value and do not count. */
inline void
chaosL0CountRead(ChaOSL0State &st, uint64_t key)
{
    if (st.active && !st.overwritten && key == st.target_key)
        ++st.reads_before_overwrite;
}

/** Hook 3 — write-side hook: detect the overwrite of the injected item.
 *  First matching-key write flips `overwritten` and stamps the cycle
 *  exactly (injectors that own their write hook get exact at=). */
inline void
chaosL0Overwrite(ChaOSL0State &st, uint64_t key, uint64_t cycle)
{
    if (st.active && !st.overwritten && key == st.target_key) {
        st.overwritten = true;
        st.overwritten_at_cycle = cycle;
    }
}

/** Container-owned-hook sync (CHAOSPhysReg pattern): mirror the container's
 *  counters (counted inside the container's own read/write paths) into the
 *  L0 state, stamping the overwrite cycle once at observation granularity. */
inline void
chaosL0Sync(ChaOSL0State &st, uint64_t container_reads, bool container_overwritten,
            uint64_t now_cycle)
{
    if (!st.active)
        return;
    st.reads_before_overwrite = container_reads;
    if (container_overwritten && !st.overwritten) {
        st.overwritten = true;
        st.overwritten_at_cycle = now_cycle;
    }
}

/** Valid-injection verdict: hit = the injected item was really read at
 *  least once before overwrite/sim-end. Misses (hit=0) are excluded from
 *  the SDC denominator (01-observation-points.md L0). */
inline bool
chaosL0Hit(const ChaOSL0State &st)
{
    return st.reads_before_overwrite > 0;
}

/** The pinned end-of-sim output line (see header comment for format). */
inline std::string
chaosL0Line(const char *injector, const ChaOSL0State &st)
{
    std::string line = "CHAOS_L0: ";
    line += injector;
    line += ": target=";
    line += std::to_string(st.target_key);
    line += " reads=";
    line += std::to_string(st.reads_before_overwrite);
    line += " overwritten=";
    line += st.overwritten ? "1" : "0";
    line += " at=";
    line += std::to_string(st.overwritten_at_cycle);
    line += " hit=";
    line += chaosL0Hit(st) ? "1" : "0";
    return line;
}

} // namespace gem5

#endif // __CPU_O3_CHAOS_L0_HH__
