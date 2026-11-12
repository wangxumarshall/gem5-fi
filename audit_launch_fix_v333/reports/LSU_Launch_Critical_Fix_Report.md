# LSU v3.3.3 — Launch-Critical Fix Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Baseline HEAD:** `58d77b34`; C++ source `b5031bf7`; binary `1126e0fd`; config `8309da72`.

## 1. Scope

This round fixed the two formal-campaign launch blockers and produced the
launch package. It did **not** change any fault model, SampleRunID, seed, ROI
percentile, approved workload, C++ source, or the gem5 binary, and it did not
re-run the 120 pre-formal runs.

## 2. Blocker 1 — runner exit/timeout semantics

The runner now:

- rejects missing binary/config/ELF/seed/SampleRunID and SHA mismatches at
  preflight, before any gem5 process;
- kills the whole process group on timeout and records PID, start/end time,
  timeout, stdout, stderr and the real exit code;
- distinguishes `PYTHON_TIMEOUT` / `EXTERNAL_TIMEOUT` /
  `MODEL_INTERNAL_WATCHDOG` / `NORMAL`;
- assigns one of `COMPLETED, FAILED, TIMEOUT, OUTPUT_INCOMPLETE,
  HASH_MISMATCH, ORACLE_FAIL` per task;
- returns campaign exit 0 only when every scheduled task is `COMPLETED` or
  `ORACLE_FAIL`; any unresolved failure is nonzero and is never silently
  skipped;
- persists `parse_error` into both `summary.json` and the RAW CSV;
- writes `campaign_identity.json` before the first task;
- passes the frozen seed to RP01 controls as well as faults.

Verification: `tests/test_lsu_v333_runner_errors.py` — **40 passed**.

## 3. Blocker 2 — formal manifest evidence isolation

`tools/lsu_v333_launch.py` was rewritten. It no longer references
`audit_v3_3_3/**` (`grep -c audit_v3_3` → 0) and derives every evidence value
from `--runs <CampaignRoot>`:

- `campaign.json` must match `--campaign-id` and the design identity;
- binary/config/ELF SHAs are checked against the frozen values and the
  campaign identity record;
- missing summary/trace/oracle/model log, identity mismatch, SHA mismatch and
  timeouts produce non-PASS statuses (`OUTPUT_INCOMPLETE`, `HASH_MISMATCH`,
  `TIMEOUT`);
- `EvidenceKind=FORMAL` only for a run under the campaign root with a matching
  campaign id; historical PRE_FORMAL roots yield zero FORMAL records;
- controls are graded by `classify_control_run` on the current run dir;
- A03/SP05/RP01 additionally carry `qualified_evidence`, never upgraded;
- `COMPLETED/ORACLE_FAIL/QUALIFIED/TRACE_INCOMPLETE` are the only statuses
  that can coexist with exit 0.

Verification: `tests/test_lsu_v333_manifest_isolation.py` (6) +
`tests/test_lsu_v333_synthetic.py` (36) — **42 passed, 0 skipped**.

## 4. Test totals

```console
$ python3 -m pytest tests/test_lsu_v333_runner_errors.py \
    tests/test_lsu_v333_control_proof.py tests/test_lsu_v333_qualified.py \
    tests/test_lsu_v333_manifest_isolation.py tests/test_lsu_v333_synthetic.py \
    -q -p no:cacheprovider
123 passed in 16.63s
```

## 5. 120-task dry-run

`120` commands, `120` unique tasks, `0` duplicates, `120` unique outdirs,
`0` collisions, `60/60` fault/control pairs with identical frozen seeds.
See `LSU_120Run_Dryrun_Report.md` and
`artifacts/LSU_120Run_Task_Map.csv`.

## 6. Commits this round

```
179082bd harden runner exit, timeout and per-task status
521c1f7f classify control zero-injection proof from run evidence
cce03ca4 enforce A03/SP05/RP01 qualified evidence rules
702de38c add synthetic fixtures and runner integration checks
1ecdb54a isolate formal manifest collection to the campaign root
e6220c43 record parse errors, campaign identity and paired RP01 seed
```

## 7. Known limitations (not hidden)

- A03: the pre-formal context `A03-R01` satisfies all required causal fields
  (`QUALIFIED` status probe → `PASS`). If a formal run lacks a field, the
  collector records `QUALIFIED`, never `PASS`.
- SP05: commit/writeback events are still absent from current evidence
  (`QUALIFIED`), even though `store_data_fnv` is present. This is recorded,
  not fabricated.
- RP01: the internal watchdog cuts the trace (`TRACE_INCOMPLETE`); HANG is a
  valid terminal, but the propagation chain is not complete.
- No formal campaign has been executed yet. All collector evidence is
  synthetic; the launch package proves the *tools and gates*, not new run
  results.

## 8. Verdict

`READY_TO_LAUNCH_FORMAL_CAMPAIGN` — the formal campaign itself awaits the
researcher's authorization.
