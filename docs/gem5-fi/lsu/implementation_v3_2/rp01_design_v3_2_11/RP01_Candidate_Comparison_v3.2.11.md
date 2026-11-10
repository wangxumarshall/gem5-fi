# RP01 Candidate Comparison — v3.2.11

**Decision status: NEEDS_USER_DECISION (unchanged). No candidate is approved.**

## 1. Candidates

- **A — Partial-forward replay loss.** In the `PartialAddrRangeCoverage` branch of `LSQUnit::read()` (`lsq_unit.cc:1990-2030`), suppress one target Load's `iewStage->rescheduleMemInst(load_inst)` call at **line 2016**. All other state transitions remain (stall record, `++replayGeneration`, `clearIssued`, `effAddrValid(false)`, `request->discard()`, `setRequest(nullptr)`, `return NoFault`).
- **B — Strict-order replay loss.** Suppress the `rescheduleMemInst` call in the strictly-ordered-load branch at **line 1665** (`read()` 1657-1680). The load is not at the LQ head / commit head; it is normally rescheduled until it can execute in order.
- **C — Violation/Snoop replay loss.** Suppress a `replayMemInst` drain at the store-completion/snoop sites (`lsq_unit.cc:1357` in `storePostSend`, `1496` in `completeStore`), or the violation-driven replay path (`checkViolations`, 550-636).

## 2. Comparison

| Criterion | A (partial forward) | B (strict order) | C (violation/snoop) |
|---|---|---|---|
| Real source hook | Yes, `lsq_unit.cc:2016` | Yes, `lsq_unit.cc:1665` | Yes, 1357/1496 |
| Independent fault semantics | Removes one replay trigger after a partial-forward mismatch | Removes one strict-order retry | Removes a replay drain after store completion/snoop |
| Data safety | No writeback is generated; no wrong PRF value; the load is simply not re-issued | The load remains strictly ordered and is re-checked when it reaches commit; likely recovered → MASKED | The load may be delayed until another drain event; no direct wrong value |
| Observable propagation | Strong: stall record + no writeback + no commit; the fault is visible in the IQ/MemDep state | Weak: the later commit-time retry masks the skipped call; little observable effect | Medium: delay/stall; overlaps the violation path of MD04 |
| Distinct from MD04 | Yes (replay trigger, not violation report) | Yes | **No** — C touches the same violation/replay area as MD04 |
| Workload fit | `replay_dependency` produces real partial-forward replays (5 observed) | The workload has no dedicated strictly-ordered load; a new workload is needed | Needs a violation/snoop-triggering workload (MD04 territory) |
| Unrecoverable HANG risk | **High** — the load is never pushed to `instsToReplay`; the store-completion `replayMemInst` has nothing to wake; ROB stalls | Low — commit-time re-check recovers it | Medium-high — depends on another drain event |
| Diagnostic value | High: a clean "missing replay trigger" signature | Low: likely indistinguishable from normal timing | Low: confounded with MD04 |

## 3. Recommendation

**Recommend A**, because it is the only candidate that (a) has a real, unambiguous source hook; (b) is semantically distinct from MD04; (c) produces a strong, diagnosable signature (stall/no writeback/missing `instsToReplay` membership); and (d) fits the existing `replay_dependency` workload, which has already produced five real `partial_forward_mismatch` replays.

The recommendation is **conditional** because A's predicted terminal is HANG, not SDC. The design must not claim a data-corruption result it cannot produce; it must be sold as a **replay-mechanism availability** fault whose expected terminal is TIMEOUT/HANG unless a squash intervenes.

## 4. Conditions (all required before implementation)

1. Researcher approval of definition A (this document does not change `DecisionStatus`).
2. Hook only the call at `lsq_unit.cc:2016` for one ordinal-selected eligible event; do not alter the stall record, the request discard, or the return value.
3. Prove by a unit/host test and a smoke run that no other path re-issues the skipped load (the store-completion `replayMemInst` must not recover it). If it does, the design must be revised (the fault would be MASKED).
4. In-simulator watchdog + external timeout; on expiry log `CHAOS_RP01_WATCHDOG_EXPIRED`, save the partial trace, exit non-zero through the registered `m5_fail instruction encountered` event; classify TIMEOUT/HANG, never MASKED.
5. Count-only preflight with the five frozen seeds/ordinals proves five distinct eligible partial-forward events. If the workload cannot supply five, report and propose a workload adjustment; do not fabricate contexts.
6. Record identity (`seq`, `pc`, `lq_entry`, `lq_gen`, `executionAttemptId`, `replayGeneration`), the pre/post `instsToReplay` state, and the skipped-call marker in the trace.
7. Preserve all SampleRunIDs/Seeds; no formal run this round; no overwrite of historical pilots.
8. One-shot semantics only (no stuck-at replay removal), to bound the leak to one LQ entry.

## 5. Why not B or C

- **B** is likely self-healing at commit (the strict-order load is re-checked when it reaches the head), so a skipped reschedule may be unobservable — a weak fault with little diagnostic value.
- **C** overlaps MD04's violation mechanism and needs a violation/snoop workload; it does not add an independent model.

## 6. Gate

**IMPLEMENTABLE_WITH_CONDITIONS** (conditions above). Pending researcher approval; `DecisionStatus` remains `NEEDS_USER_DECISION`.
