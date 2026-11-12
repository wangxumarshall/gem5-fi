# LSU v3.3.3 — Final Launch Readiness Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Verdict:** `READY_TO_LAUNCH_FORMAL_CAMPAIGN`

The formal campaign is **not started**. It awaits the researcher's explicit
authorization.

## 1. Launch gate

| Item | Requirement | Measured result | Status |
|---|---|---|---|
| Models | 12/12 | 12 | PASS |
| SampleRunID | 60/60 | 60 unique | PASS |
| Seed | 60/60 | 60 non-empty | PASS |
| Context mapping | 60/60 | 5 contexts × 12 models | PASS |
| Fault tasks | 60/60 | 60 scheduled | PASS |
| Control tasks | 60/60 | 60 scheduled | PASS |
| Fault-Control pairing | 60/60 | 60/60 identical frozen seed in the planned commands | PASS |
| Control zero proof | 60/60 | pre-formal mechanism proof: 35 `MOUNTED_BUT_DISABLED` + 25 `INJECTOR_ABSENT`, all `PASS`; formal runs re-prove from the campaign root | PASS (mechanism) |
| Binary provenance | complete | `1126e0fd…`, config `8309da72…`, 9 ELF hashes, C++ diff 0 | PASS |
| Manifest schema | valid | 46 columns in `LSU_120Run_Formal_Manifest_Schema.csv` | PASS |
| Formal evidence isolation | enforced | `grep audit_v3_3 tools/lsu_v333_launch.py` → 0; historical root → 0 FORMAL | PASS |
| Missing-output detection | enforced | 18 collector/isolation tests | PASS |
| Timeout handling | enforced | TIMEOUT + source separation, process-group kill | PASS |
| Non-zero exit handling | enforced | any FAILED/TIMEOUT/OUTPUT_INCOMPLETE/HASH_MISMATCH/CONTROL_PROOF_INCOMPLETE → exit 1 | PASS |
| Synthetic tests | all pass | 123 passed, 0 skipped | PASS |
| Runner dry-run | 120/120 | 120 commands, 0 duplicate, 0 collision | PASS |
| Output collision | 0 | 120 unique outdirs | PASS |
| Resource check | PASS | 126 cores, 29 GB RAM, ≤4 concurrent cap; runner is serial | PASS |

## 2. Real launch commands (parameters verified)

Run from the worktree:

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12

# 1) 120 formal runs (60 fault + 60 control)
python3 tools/lsu_v332_matrix.py \
  --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv \
  --campaign-id LSU-V333-FORMAL-20261112 \
  --expected-binary-sha 1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338 \
  --expected-config-sha 8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
echo "runner_exit=$?"

# 2) collect the formal manifest from THIS campaign root only
python3 tools/lsu_v333_launch.py \
  --runs runs/lsu/formal_v333 \
  --campaign-id LSU-V333-FORMAL-20261112 \
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --out runs/lsu/formal_v333/collector \
  --manifest-only
echo "collector_exit=$?"
```

`--design-mapping` is a **design/identity** input; it is never a run-evidence
source. The frozen SampleRunID/Seed/ROI are unchanged.

## 3. Task mapping

`audit_launch_fix_v333/artifacts/LSU_120Run_Task_Map.csv`: 120 rows,
12 models × 5 contexts × 2 roles, 60 unique SampleRunIDs, 60 unique seeds,
120 unique outdirs (see `LSU_120Run_Dryrun_Report.md`).

## 4. Resources and expected time

- 126 CPU cores, 29 GB RAM (≈25 GB available); documented cap ≤ 4 concurrent
  gem5 processes. The matrix runner is serial (`matrix_lock`), so one gem5
  process at a time.
- Measured pre-formal total: 429.1 s for 120 runs (mean 3.6 s, max 21.3 s)
  → ≈ 7.2 min of pure simulation.
- Expected formal wall time: roughly 10–30 min including per-run overhead and
  oracle checks. Worst case is bounded by the per-task timeouts
  (A03/RP01 direct 180 s / 400 s; run_pilot 400 s); a pathological
  all-timeout campaign is bounded, not unbounded.

## 5. QUALIFIED contexts — mandatory formal rules (not hidden)

| Model | Required formal evidence | Terminal rule |
|---|---|---|
| A03 | stuck-at lifecycle, activation, first affected load (seq/PC), load result, register writeback, consumer, checksum, internal watchdog reason — three events kept distinct (`stuck-at active` ≠ `selected event first activated` ≠ `first downstream instruction affected`) | SDC/HANG_WATCHDOG; missing field → `QUALIFIED` |
| SP05 | store dyn seq, PC, SQ entry, address, `store_data_fnv`/data hash, commit event, writeback event, visibility, reload, consumer, golden memory, oracle. Current evidence has `store_data_fnv` but lacks `commit_event`/`writeback_event` → `QUALIFIED` | never upgraded to `PASS` |
| RP01 | replay eligibility/decision, faulty replay state, replay skip, dyn seq, LQ/SQ entry, watchdog, external timeout, final progress | HANG_WATCHDOG is valid; trace cut → `TRACE_INCOMPLETE`; external timeout never relabelled as internal HANG |

Pre-formal A03-R01 currently satisfies all required fields; SP05 and RP01
remain `QUALIFIED`/`TRACE_INCOMPLETE` by evidence, which the formal manifest
will record verbatim.

## 6. Explicit non-authorization

No formal campaign run was started by this round. The command block above is
the authorized-execution command, to be run only after the researcher's
approval.
