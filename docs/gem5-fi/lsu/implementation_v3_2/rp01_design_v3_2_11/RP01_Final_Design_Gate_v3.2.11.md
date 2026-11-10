# RP01 Final Design Gate — v3.2.11

**DecisionStatus: NEEDS_USER_DECISION (unchanged). No C++ implementation in this round.**
**Gate verdict: IMPLEMENTABLE_WITH_CONDITIONS.**

## 1. Fault definition (proposed, pending approval)

Skip **one** ordinal-selected `iewStage->rescheduleMemInst(load_inst)` call in the `PartialAddrRangeCoverage` branch of `LSQUnit::read()` for the target Load. One-shot (F6/F0 semantics); no change to the address, size, data, or any other state transition. The fault removes a replay trigger, not a value.

## 2. Exact injection site

- File: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- Function: `LSQUnit::read(LSQRequest *request, ssize_t load_idx)` (1641-2075)
- Branch: `coverage == AddrRangeCoverage::PartialAddrRangeCoverage` (1990-2030)
- Call suppressed: **line 2016** `iewStage->rescheduleMemInst(load_inst);`
- Eligibility: the load is the ordinal-selected eligible partial-forward event; identity `(dyn_inst_seq, lq_entry_id, entry_generation)`.
- Everything else in the branch stays: stall record (2001-2008), `++replayGeneration` (2012), `clearIssued()` (2017), `effAddrValid(false)` (2018), `request->discard()` (2028), `load_entry.setRequest(nullptr)` (2029), `return NoFault` (2030).

## 3. Normal execution path

Partial store→load overlap → stall record + `++replayGeneration` → `rescheduleMemInst` → `MemDepUnit::instsToReplay` → store completion `replayMemInst` (1357/1496) → `MemDepUnit::replay` → load re-issues → full data assembly → writeback → commit.

## 4. Fault execution path

Partial overlap → stall record + `++replayGeneration` → **reschedule skipped** → request discarded/null → the load is never pushed to `instsToReplay` → store completion has nothing to wake → the load never writes back or commits → the ROB stalls → HANG/TIMEOUT unless an older squash clears the entry (then SQUASHED).

## 5. Safety analysis

| Risk | Level | Mitigation |
|---|---|---|
| Permanent wait | High (expected) | internal watchdog + external timeout |
| LQ entry never freed | High | one-shot bounds it to one entry; timeout ends the run |
| IQ resource exhaustion | Low | one-shot |
| Duplicate scheduling/writeback | None | the call is skipped, not duplicated; no writeback is generated |
| Wrong commit / PRF corruption | None via this mechanism | no data path is modified |
| Simulator state corruption | Low | request discard/null is already the normal partial-branch behavior |

## 6. HANG risk

**This is the defining risk, not an edge case.** The expected terminal is HANG/TIMEOUT. The model must be presented as a replay-availability fault, not a data-corruption fault. A run that ends MASKED or SDC would falsify the predicted mechanism and must be investigated, not celebrated.

## 7. Difference from MD04

| | MD04 | RP01-A |
|---|---|---|
| Site | `checkViolations` return (550-636) | `read()` partial branch, line 2016 |
| Trigger | ordering violation | partial-forward mismatch |
| State changed | violation report/fault return | replay trigger / `instsToReplay` membership |
| Downstream | load still executes | load never re-issues |
| Terminal | usually MASKED | usually HANG/TIMEOUT |
| Signature | `violation_report_suppressed=1`, data correct | skipped call, no writeback, stall |

## 8. Workload verification

`replay_dependency` exists, SHA256 matches `ca15390f…38f4`, oracle `59fc61c040618747` reproduced. A prior probe recorded five real `partial_forward_mismatch` replays, but under a different seed/fault; a clean count-only preflight under the five RP01 seeds is still required. The C-level same-address 8-byte store→load normally gives full coverage; the observed partial events come from the compiled dynamic stream and must be re-proven.

## 9. Five dynamic contexts

Identities R01–R05 preserved. A candidate mapping from the five observed replay events is in `RP01_Dynamic_Contexts_v3.2.11.md`; it is a hypothesis, not a verified context set. The count-only preflight must prove five distinct contexts under the five seeds.

## 10. Expected propagation chain

`injection (skip replay trigger)` → `stall record / no instsToReplay membership` → `no memory response for the attempt` → `no register writeback` → `no consumer` → `no commit` → `HANG/TIMEOUT` (or `SQUASHED` if an older squash clears the entry). **No SDC is expected.** If the design is approved, the audit classification target will be `COMPLETE_CAUSAL_CHAIN` only for a directly evidenced HANG/SQUASHED chain, never for a run that silently masks the fault.

## 11. Oracle design

- Normal completion (if the fault is recovered): application checksum must equal `59fc61c040618747`; a mismatch would indicate an unexpected data path and must be investigated as a design error, not claimed as RP01 SDC.
- HANG/TIMEOUT: no checksum; the platform must classify TIMEOUT/HANG, save the partial trace, and never report MASKED.
- The trace must record the skipped-call marker, the pre/post `instsToReplay` state, and the watchdog line.

## 12. Recommendation

Implement **candidate A** only under the conditions below.

## Conditions (all required)

1. Researcher approval of this definition; `DecisionStatus` remains `NEEDS_USER_DECISION` until then.
2. Hook only line 2016 for one ordinal-selected eligible event; do not alter the stall record, request discard, or return value.
3. Prove (host unit test + smoke) that no other path re-issues the skipped load; if the store-completion `replayMemInst` recovers it, revise the design.
4. Internal watchdog + external timeout; partial trace retained; non-zero exit through the registered `m5_fail instruction encountered` event; classification TIMEOUT/HANG, never MASKED.
5. Clean count-only preflight under the five frozen seeds proves five distinct eligible events; if not, propose a workload adjustment (preserve the original workload/SHA/golden).
6. Record identity (`seq`, PC, `lq_entry`, `gen`, `executionAttemptId`, `replayGeneration`), pre/post replay state, and the skipped-call marker.
7. Preserve SampleRunIDs/Seeds; no formal run this round; no historical overwrite.
8. One-shot semantics only.

## Gate verdict

**IMPLEMENTABLE_WITH_CONDITIONS** — the source hook is real and independent of MD04, but the expected terminal is HANG/TIMEOUT, the workload's five distinct contexts are not yet proven, and the fault must not be sold as SDC. The design is ready for researcher review; it is not approved for implementation.
