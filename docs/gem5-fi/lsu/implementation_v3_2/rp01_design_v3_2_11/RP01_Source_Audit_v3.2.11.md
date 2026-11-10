# RP01 Source Audit — v3.2.11

**Model:** RP01 (Replay trigger loss)  **SubUnit:** Replay Logic  **Mode:** F6
**Audited source:** `CHAOS/gem5/src/cpu/o3/` at branch `lsu-platform-v3.2.11` (source unchanged since v3.2.10 except `CHAOSLQ04.cc`/`configs/se/lsu_proxy.py`).
**No C++ hook was implemented in this round.**

## 1. Exact source map (re-verified with `grep -n`/`sed -n`)

| Component | File | Class / function | Lines |
|---|---|---|---|
| Load issue + forwarding loop | `lsq_unit.cc` | `LSQUnit::read` | **1641-2075** |
| Request installed on the LQ entry | `lsq_unit.cc` | `load_entry.setRequest(request)` | 1647 |
| Strictly-ordered replay branch | `lsq_unit.cc` | `read()` | **1657-1680** |
| Strict-order `rescheduleMemInst` call | `lsq_unit.cc` | `read()` | **1665** |
| Partial-coverage branch | `lsq_unit.cc` | `read()` | **1990-2030** |
| Stall record (`stalled`, `stallingStoreIsn`, `stallingLoadIdx`) | `lsq_unit.cc` | `read()` | **2001-2008** |
| `++replayGeneration` | `lsq_unit.cc` | `read()` | 2012 |
| **Partial-forward `rescheduleMemInst` call** | `lsq_unit.cc` | `read()` | **2016** |
| Issued/effective-address reset | `lsq_unit.cc` | `read()` | 2017-2018 |
| Request discard + null | `lsq_unit.cc` | `read()` | 2028-2029 |
| IEW reschedule entry | `iew.cc` | `IEW::rescheduleMemInst` | **562-566** |
| IQ reschedule | `inst_queue.cc` | `InstructionQueue::rescheduleMemInst` | **1322-1333** |
| MemDep queue push | `mem_dep_unit.cc` | `MemDepUnit::reschedule` | **380-384** |
| MemDep replay drain | `mem_dep_unit.cc` | `MemDepUnit::replay` | **386-** |
| Store-completion replay (storePostSend) | `lsq_unit.cc` | `LSQUnit::storePostSend` | **1347-1357** (call 1357) |
| Store-completion replay (completeStore) | `lsq_unit.cc` | `LSQUnit::completeStore` | **1489-1496** (call 1496) |
| Replay identity | `dyn_inst.hh` | `DynInst::executionAttemptId`, `replayGeneration` | **353-355** |
| Stalling load index | `lsq_unit.hh` | `LSQUnit::stallingLoadIdx` | **565** |
| LQ entry generation | `lsq_unit.hh` | `LSQEntry` / `lqEntryGeneration` | around 95-147 |

## 2. Normal replay path (Question A)

1. A Load executes `LSQUnit::read()` and scans older Stores for forwarding.
2. `AddrRangeCoverage` is computed for each candidate Store. A **partial** overlap (`PartialAddrRangeCoverage`, `lsq_unit.cc:1990`) means the Store covers only some of the Load's bytes; the remaining bytes must come from memory after the Store is written.
3. The Load is recorded as the stalling load (`stalled=true`, `stallingStoreIsn`, `stallingLoadIdx`, lines 2001-2008), its `replayGeneration` is incremented (2012), and `iewStage->rescheduleMemInst(load_inst)` (2016) pushes it into `InstructionQueue` → `MemDepUnit::reschedule` → `instsToReplay`.
4. The Load's request is discarded and the LQ entry's request pointer is cleared (2028-2029); no writeback event is generated. `read()` returns `NoFault`.
5. When the stalling Store completes, `storePostSend()`/`completeStore()` call `iewStage->replayMemInst(loadQueue[stallingLoadIdx].instruction())` (1357/1496), which calls `MemDepUnit::replay()` to move `instsToReplay` entries to the ready list. The Load re-issues, re-executes, and now assembles the full data (forwarded bytes + memory bytes), writes back, and commits.

**State that decides re-execution:** `stalled`, `stallingLoadIdx`, `stallingStoreIsn`, membership in `instsToReplay`, `canIssue` (cleared by `clearIssued()`), `effAddrValid`, `executionAttemptId`, and `replayGeneration`.

## 3. What happens if one `rescheduleMemInst` call is skipped (Question B)

The proposed fault removes **only** the call at `lsq_unit.cc:2016` for one ordinal-selected partial-forward event; everything else (stall record, `++replayGeneration`, `clearIssued()`, `effAddrValid(false)`, `request->discard()`, `setRequest(nullptr)`, `return NoFault`) is unchanged.

1. **Does the Load stay in the Issue Queue?** Yes. `clearIssued()` clears `canIssue`; the instruction remains in the IQ's issued list.
2. **Is the wait state preserved?** Yes. `stalled`, `stallingStoreIsn`, `stallingLoadIdx` remain set; the LQ entry remains allocated with `request()==nullptr`.
3. **Can it become permanently unreschedulable?** Yes, in the normal case. `MemDepUnit::replay()` (386-) drains `instsToReplay`; the skipped Load was never pushed because `MemDepUnit::reschedule` (380-384) is called only from the skipped path. The store-completion `replayMemInst` therefore has nothing to wake for this Load. No other path re-issues this specific dynamic Load.
4. **Can it use incomplete data?** No. The partial branch generates no writeback event and returns before data assembly; the Load is not executed.
5. **Can it write wrong data to the PRF?** No direct path — there is no writeback for this attempt.
6. **Can another replay mechanism recover it?** `replayMemInst` only drains `instsToReplay`; `wakeDependents` does not re-issue an unexecuted memory instruction. A branch misprediction squash can clear the entry, but that is a different mechanism and not guaranteed.
7. **Can it be squashed?** Yes, if an older instruction squashes. The squash loop clears `stalled` and pops the LQ entry; the dynamic Load then disappears without committing. That is a recovery-ish outcome, not a propagation of the fault.
8. **Can it hang?** Yes — and this is the predicted deterministic outcome. The Load never completes; the ROB head (or a dependent instruction) waits indefinitely; the pipeline drains and the simulation deadlocks. The expected terminal is **HANG/TIMEOUT**, not SDC. This is the central safety finding.

## 4. Normal vs fault execution

| Phase | Normal | Fault (skip one call) |
|---|---|---|
| Partial overlap detected | stall record + replayGeneration | same |
| IQ/MemDep reschedule | `instsToReplay` push | **missing** |
| Request | discarded, entry null | same |
| Store completion | `replayMemInst` wakes the Load | nothing to wake |
| Load re-execution | full data assembly | never happens |
| Writeback / commit | correct value, commit | none; ROB stalls |
| Terminal | MASKED or SDC depending on data | **HANG** (unless squashed) |

## 5. Safety analysis (Question D)

| Risk | Assessment |
|---|---|
| Permanent wait | **High** — the most likely outcome |
| LQ entry never released | **High** — the entry cannot commit; one-shot fault bounds the leak to one entry |
| IQ resource exhaustion | Low — one-shot, one entry |
| Duplicate scheduling | None — the call is skipped, not duplicated |
| Duplicate writeback | None — no writeback for the skipped attempt |
| Wrong commit | None via this mechanism |
| Simulator state corruption | Low — the request was already discarded and the entry nulled consistently; the stall record is stale but bounded |

**Watchdog/timeout design:** an in-simulator `EventFunctionWrapper` armed at injection (or at the first eligible partial event), logging `CHAOS_RP01_WATCHDOG_EXPIRED` and exiting through gem5's registered `m5_fail instruction encountered` event with code 1 (the v3.2.11 LQ04 precedent). The external `run_pilot.py` timeout preserves the partial trace and must classify the result as `TIMEOUT`/`HANG`, never `MASKED`. The last valid trace event must be retained (gzip closed by the exit callback).

## 6. Question C — RP01 vs MD04

| Dimension | MD04 | RP01 candidate A |
|---|---|---|
| Injection site | `LSQUnit::checkViolations` return (`lsq_unit.cc:550-636`) | `LSQUnit::read` partial branch (`2016`) |
| Trigger | a real Store→Younger-Load ordering violation | a partial-coverage forwarding mismatch |
| Modified state | the violation report/fault return | the replay trigger/`instsToReplay` membership |
| Downstream behavior | Load still executes; data path unchanged | Load is never re-issued; ROB stalls |
| Typical terminal | MASKED (or SDC if the stale data is consumed) | HANG/TIMEOUT |
| Diagnostic signature | `violation_report_suppressed=1`, correct data | skipped `rescheduleMemInst`, no writeback, stall |
| Safety profile | bounded, often MASKED | deadlock risk; requires watchdog |

RP01 is not a re-labelled MD04: it modifies a different control state, at a different site, with a different downstream signature.
