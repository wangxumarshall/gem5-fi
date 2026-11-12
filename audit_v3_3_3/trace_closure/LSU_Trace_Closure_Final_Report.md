# LSU v3.3.3 — Final Trace Closure Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Baseline HEAD:** `78ac9ba7`
**Final binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Previous binary (superseded):** `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`

## 1. Result

The 11 restricted contexts were re-run with the new binary (22 directed pilots), plus 18
cross-model regression pilots and the canonical `reg_chain` golden. A03-R02 is now a complete SDC
causal chain. SP05 now has real commit evidence and honest writeback-suppression evidence. RP01 now
has a complete watchdog terminal record set. No fault model, workload, seed, SampleRunID, ROI
percentile, dynamic context or Fault-Control pairing changed.

Final 60-context classification (`LSU_60Context_Final_Readiness.csv`):

| Class | Count | Meaning |
|---|---:|---|
| `COMPLETE_CAUSAL_CHAIN` | 38 | SDC; fault dataflow reached the application terminal |
| `VALID_TERMINAL_CHAIN` | 12 | MASKED with a mechanism/consumer witness; valid terminal, not an SDC dataflow |
| `QUALIFIED` | 5 | SP05 lost-writeback mechanism fully observed, but the frozen `writeback_event` field is absent by construction |
| `TRACE_INCOMPLETE` | 5 | RP01 internal-watchdog HANG; terminal record set complete, trace partial by construction |
| `UNRESOLVED` | 0 | — |

All 60 contexts have a real, explainable terminal. The 10 non-complete rows are **documented
limitations**, not missing evidence or fabricated upgrades.

## 2. What changed (all read-only observation)

| Unit | Change |
|---|---|
| A03 | Parser anchor: keep 13718 as the squashed first-affected provenance; anchor the causal chain at the run's `errant_commit` (13772). No binary change. |
| SP05 | H1 real commit capture in `noteCommit`; H2 `store_commit` node; H3 `store_writeback_suppressed` negative-evidence node; H4 removal of caller-supplied commit tick. |
| RP01 | `flushWatchdogTerminal()` before `fatal()`: `trace_flush_start` / `watchdog_terminal` / `trace_flush_complete`, gzip flush+close; last-eligible/progress snapshot; LQ/SQ read-only accessors. |
| Tools | `lsu_v333_qualified.py`, `lsu_v333_propagation.py`, new `lsu_v333_trace_closure.py`; binary SHA re-freeze in matrix/launch/report tools. |
| Config | New workbook, campaign manifest template, launch script and provenance under `trace_closure/final_config/`. |

No change to injection timing, probability, state, duration, LSU scheduling, store/load decisions,
replay, commit decisions or RNG. The new binary is the only current formal candidate.

## 3. Direct answers to the nine acceptance questions

1. **A03-R02 — SQUASHED or complete chain?**
   **Complete SDC chain.** 13718 is a speculative instance squashed by an unrelated event; the
   persistent fault's first architecturally committed affected load is 13772 (`resp 0xab →
   taint x1 → consumers 13774/13775 → checksum d48b947fc08d5a75`). It was not reclassified as
   SQUASHED, because that would contradict the measured SDC.
2. **SP05 — can all five contexts trace Commit and Writeback?**
   **Commit: yes, five of five**, from the real `Commit::commitHead` tick (`commit_stage_capture`,
   `commit_tick < inject_tick`). **Writeback: no positive writeback exists** — the fault itself
   suppresses the cache write. Five of five have independent `store_writeback_suppressed` evidence
   (`request_sent_after=0; mem_sent=0; visibility_state=NEVER_WRITTEN`) plus reload of the old
   value. This remains `QUALIFIED` under the frozen field rule.
3. **RP01 — complete pre-watchdog trace?**
   **Terminal record set: yes, five of five.** Each trace ends with the three flush nodes, the
   previous node ID, the last eligible instruction, replay decision/skip, LQ/SQ state and
   `MODEL_INTERNAL_WATCHDOG`; gzip containers are valid. The runs remain `TRACE_INCOMPLETE`
   because the simulation genuinely stopped at the watchdog.
4. **Any fault-semantics change?** **No.** Only read-only hooks, parser changes and re-freeze.
   The 40-run regression reproduces every historical terminal/oracle.
5. **Does the new binary pass regression?** **Yes.** 18/18 cross-model runs match the historical
   terminal and oracle exactly; `reg_chain` prints `f247ef3fe6f02cfd` with exit 0; no SIGSEGV.
6. **Are the 60 SampleRunIDs and Seeds unchanged?** **Yes.** Identity columns were copied from the
   frozen matrix; the runner's preflight enforced the same seeds/ordinals; no ID/seed edit exists
   in the diff.
7. **Are all 12 models still executable?** **Yes.** A01/A03/FW02/FW05/MD04/SQ01/SQ03/SP05/DA04/
   LP01/LQ04/RP01 all ran; the 40-run table has zero FAILED/TIMEOUT/HASH_MISMATCH.
8. **Is 60/60 a valid causal terminal achieved?**
   **60/60 have a real, explainable terminal; 38 are complete SDC dataflow chains, 12 are valid
   MASKED terminals, 5 SP05 are mechanism-complete but field-qualified, and 5 RP01 are valid HANG
   terminals with a partial trace by construction.** No `UNRESOLVED` row remains.
9. **Can the final binary be frozen and the formal Campaign launched?**
   **Yes, with documented limitations** (`READY_WITH_DOCUMENTED_LIMITATIONS`). The only alternative
   is a researcher decision to redefine SP05's `writeback_event` field as a writeback *outcome*
   (accepting `SUPPRESSED_BEFORE_SEND`); without that decision, the five SP05 contexts cannot
   honestly become PASS. No such redefinition was made unilaterally.

## 4. Final status

**`READY_WITH_DOCUMENTED_LIMITATIONS`**

- A03-R02: closed as COMPLETE_CAUSAL_CHAIN (SDC).
- SP05 R01–R05: real commit + suppressed writeback + old-value reload + consumer + oracle;
  `QUALIFIED` on `writeback_event` (fault semantics).
- RP01 R01–R05: complete watchdog terminal record set; `TRACE_INCOMPLETE` (HANG by construction);
  `stats.txt` remains 0 bytes on the `fatal()` path.
- Formal Campaign: all 120 runs must use binary `62e1b1be…`, config `8309da72…`, campaign
  `LSU-V333-FINAL-20261112`. Historical Pre-Formal evidence stays archived and must not be mixed
  into the formal result set.

## 5. Final formal Campaign command (awaiting researcher authorization)

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
bash audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh
```

The script runs `tools/lsu_v332_matrix.py` for all 12 models × 5 contexts × fault/control with the
new binary SHA and config SHA, then `tools/lsu_v333_launch.py --manifest-only` to collect the
120-run evidence. **Do not run before explicit authorization.**

## 6. Deliverables

1. `LSU_Trace_Closure_Final_Report.md` (this file)
2. `A03_R02_Trace_Closure_Report.md`
3. `SP05_Commit_Writeback_Final_Report.md`
4. `RP01_Watchdog_Trace_Flush_Final_Report.md`
5. `LSU_60Context_Causal_Propagation_Final.csv`
6. `LSU_60Context_Final_Readiness.csv`
7. `LSU_11Context_Repair_Validation.csv`
8. `LSU_40Run_Regression_Report.md`
9. `final_config/LSU_Final_Binary_Provenance.md`
10. `final_config/LSU_Final_Experiment_Config.xlsx`
11. `final_config/LSU_Final_Campaign_Manifest_Template.csv`
12. `LSU_Final_Source_Diff.patch`
13. `LSU_Independent_Acceptance.md`
14. Source anchors are listed in the three model reports; full diff in item 12.
15. All 40 pilot traces/stdout/stderr/oracle/logs are under `runs/`; the 22 restricted runs are
    also under `runs/` with their controls.

## 7. Honest limitations (carried forward)

1. **SP05 `writeback_event`**: the frozen field requires a positive writeback; SP05 is a
   lost-writeback fault. The evidence proves the negative outcome, but the status stays
   `QUALIFIED` unless the researcher approves a field-semantics revision.
2. **RP01 `TRACE_INCOMPLETE`**: the watchdog is the fault's expected HANG terminal; the flush
   completes the terminal metadata, not the simulation. `stats.txt` remains 0 bytes because
   `stats.dump` is on the skipped `atexit` path.
3. **Mixed provenance in the final 60-context tables**: 49 contexts use historical Pre-Formal
   evidence; 11 use the new binary. Each row records its evidence root and binary SHA. The formal
   Campaign re-runs all 120 with the new binary.
4. **A03 squash-cause identity**: `triggering_seq=13717` is not recorded as a PC; the branch
   mispredict reading is an inference from control flow, not a directly recorded instruction.
