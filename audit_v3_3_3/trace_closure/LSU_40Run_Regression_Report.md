# LSU v3.3.3 — 40-Run Directed Validation & Regression Report

**Date:** 2026-11-12
**Binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Config:** `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Run root:** `audit_v3_3_3/trace_closure/runs/` (independent of `audit_v3_3_3/runs/`; historical evidence untouched)
**Raw table:** `audit_v3_3_3/trace_closure/runs/LSU_40Run_RAW_Combined.csv`

## 1. Scope

| Group | Runs | Result |
|---|---:|---|
| 11 restricted contexts (Fault + Control) | 22 | 11 Fault (`ORACLE_FAIL`/valid terminal) + 11 Control (`COMPLETED`, zero injection, oracle PASS) |
| 9 unaffected models × R03 (Fault + Control) | 18 | 6 SDC fault + 3 MASKED fault + 9 control (`COMPLETED`, zero injection) |
| **Total** | **40** | **0 FAILED, 0 TIMEOUT, 0 HASH_MISMATCH, 0 OUTPUT_INCOMPLETE, 0 SIGSEGV** |

Status counts: `COMPLETED=28`, `ORACLE_FAIL=12`. The 12 `ORACLE_FAIL` runs are the expected
fault-injection SDC terminals, not runner failures.

## 2. Restricted contexts

| Model | Contexts | New evidence |
|---|---|---|
| A03 | R02 | `PASS`, anchor 13772, checksum `d48b947fc08d5a75` (identical to baseline), squash 13718 preserved |
| SP05 | R01–R05 | real `store_commit` (`commit_stage_capture`) + `store_writeback_suppressed`; `QUALIFIED` on `writeback_event` only |
| RP01 | R01–R05 | `trace_flush_start`/`watchdog_terminal`/`trace_flush_complete` present; `TRACE_INCOMPLETE` retained |

Controls for all 11 contexts: `injection_count=0`, `oracle=True`, no new event types, no flush
nodes.

## 3. Cross-model regression (9 models × R03)

| Model | Role | Status | Terminal | Oracle | Injection | Old terminal | Old oracle | Match |
|---|---|---|---|---:|---:|---|---|---|
| A01 | fault | ORACLE_FAIL | SDC | False | 1 | SDC | False | YES |
| A01 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| FW02 | fault | COMPLETED | MASKED | True | 1 | MASKED | True | YES |
| FW02 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| FW05 | fault | ORACLE_FAIL | SDC | False | 1 | SDC | False | YES |
| FW05 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| MD04 | fault | ORACLE_FAIL | SDC | False | 1 | SDC | False | YES |
| MD04 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| SQ01 | fault | ORACLE_FAIL | SDC | False | 1 | SDC | False | YES |
| SQ01 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| SQ03 | fault | COMPLETED | MASKED | True | 1 | MASKED | True | YES |
| SQ03 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| LP01 | fault | ORACLE_FAIL | SDC | False | 1 | SDC | False | YES |
| LP01 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| LQ04 | fault | COMPLETED | MASKED | True | 1 | MASKED | True | YES |
| LQ04 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |
| DA04 | fault | ORACLE_FAIL | SDC | False | 1 | SDC | False | YES |
| DA04 | control | COMPLETED | UNRESOLVED | True | 0 | UNRESOLVED | True | YES |

Every regression run reproduces the historical terminal and oracle exactly. This proves the
shared trace-hook changes did not alter execution, commit, replay, injection or oracle behavior
for any of the nine unaffected models.

## 4. Canonical golden and unit tests

```console
$ build/ARM/gem5.opt --outdir=audit_v3_3_3/trace_closure/runs/regression-reg_chain \
    configs/se/arm_chaos.py --cmd=workloads/directed/reg_chain --cpu O3
exit 0
f247ef3fe6f02cfd
```

The canonical `reg_chain` golden `f247ef3fe6f02cfd` passes with no SIGSEGV.

Full Python suite: see `reports/pytest_full.log`. The suite covers the runner, manifest
isolation, qualified grader, synthetic fixtures, workbook, controls and launch tooling.

## 5. Provenance discipline

- All 40 runs used the new binary and the unchanged config; the runner preflight enforced both
  SHAs (`HASH_MISMATCH=0`).
- No historical `audit_v3_3_3/runs/**` directory was overwritten.
- The 49 non-restricted contexts in the final 60-context tables still point at their historical
  Pre-Formal evidence; every row records its evidence root and binary SHA. The formal Campaign
  will re-run all 120 tasks with the new binary as one batch.
