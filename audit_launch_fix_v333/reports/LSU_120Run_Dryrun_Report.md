# LSU v3.3.3 — 120-Run Dry-Run Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Binary:** `build/ARM/gem5.opt` SHA256 `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Config:** `configs/se/lsu_proxy.py` SHA256 `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`

## 1. Command and exact output

```console
$ python3 tools/lsu_v332_matrix.py --dry-run --out-base /tmp/lsu_v333_dryrun_t6 > /tmp/lsu_v333_dryrun_t6.log 2>&1
EXIT=0
$ tail -1 /tmp/lsu_v333_dryrun_t6.log
dry-run: 120 commands; no run dirs written
$ test -e /tmp/lsu_v333_dryrun_t6 && echo OUTBASE_EXISTS || echo OUTBASE_ABSENT
OUTBASE_ABSENT
```

No run directory, summary, CSV, or campaign identity file is written by `--dry-run`.

## 2. Task-set invariants (derived from the dry-run text)

```console
tasks 120
unique_tasks 120 duplicates 0
unique_outdirs 120 none 0 collision 0
pairs 60 paired_same_seed 60
unpaired []
models 12 contexts 5
```

- 120 scheduled tasks = 12 models × 5 contexts × 2 roles.
- Every `(model, context, role)` is unique; no task is launched twice.
- Every `--outdir` is unique (no output collision).
- 60 fault/control pairs share the frozen seed; 0 unpaired.
- The per-task map (outdir, SampleRunID, seed, exact command) is
  `audit_launch_fix_v333/artifacts/LSU_120Run_Task_Map.csv` (120 rows,
  60 unique SampleRunIDs, 60 unique seeds, 120 unique outdirs).

## 3. Resource check

```console
$ nproc
126
$ free -g | head -2
               total        used        free      shared  buff/cache   available
Mem:              29           4           0           1          26          25
$ stat -c '%s bytes' build/ARM/gem5.opt
1149173888 bytes
```

- Host memory is 29 GB; the documented hard cap is ≤ 4 concurrent gem5
  processes. The runner executes tasks serially under `matrix_lock`, so the
  formal campaign uses one gem5 process at a time.
- Measured pre-formal wall time (120 runs, `summary.json.elapsed`):
  total 429.1 s, mean 3.6 s, max 21.3 s → ≈ 7.2 min serial.
- Worst-case bound if every task hit its external timeout:
  A03/RP01 direct runs 180 s / 400 s; run_pilot runs 400 s. A pathological
  all-timeout campaign is bounded by those per-task limits, not unbounded.

## 4. Verdict

`120/120 tasks generated; 0 duplicate; 0 output collision; 60/60 pairs share
the frozen seed; resource check PASS.`
