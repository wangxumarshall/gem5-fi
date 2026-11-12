# LSU v3.3.3 — Final Formal Campaign Runbook

**Status:** `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES`
**DO NOT RUN until the researcher explicitly authorizes the campaign.**

- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- Binary: `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
- Config: `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
- Campaign ID: `LSU-V333-FINAL-20261112`
- Unique output root: `runs/lsu/formal_v333_final_20261112` (worktree-relative)
- Scope: 12 models × 5 contexts × 2 roles = **120 runs**

All five scripts live in `audit_v3_3_3/trace_closure/final_config/`. Every stage
fails closed with a nonzero exit code; none of them falls back to historical
pilot or Pre-Formal evidence.

## Ordered pipeline at a glance

| Stage | Command | Writes (disjoint) |
|---|---|---|
| 0 preflight | `launch_commands_final.sh preflight` | nothing (SHA check only) |
| 0b dry-run | `launch_commands_final.sh dry-run` | nothing; prints 120 commands |
| 1 launch | `01_launch_campaign.sh` | `runs/lsu/formal_v333_final_20261112/<Model>-Rxx-{fault,control}/` + `LSU_Fault_Control_Pair_RAW.csv` |
| 1 resume | `01_launch_campaign.sh --resume` | appends attempts under the same root |
| 2 manifest | `02_manifest_only.sh` | `collector_manifest/` only |
| 3 collector | `03_full_collector.sh` | `collector_full/` only |
| 4 reports | `04_final_reports.sh` | campaign-root `LSU_*.csv` + `LSU_Final_Experiment_Config.xlsx` |

`dispatch` shorthand: `bash launch_commands_final.sh <plan|preflight|dry-run|launch|resume|collect|report>`.
`collect` runs Stage 2 then Stage 3; `report` runs Stage 4.

## Stage 0 — preflight (read-only)

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
bash audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh preflight
# expected: both sha256 sums OK, then the campaign-root state line
```

The preflight checks the frozen binary (`build/ARM/gem5.opt`) and config
(`configs/se/lsu_proxy.py`) against the SHAs above and reports whether the
campaign root is still empty. If the root is non-empty, do not continue with a
fresh launch; use the resume stage.

## Stage 0b — dry run (validation only, writes nothing)

```bash
bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh --dry-run
# or: bash audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh dry-run
```

Must print `dry-run: 120 commands; no run dirs written` and exit 0. The dry run
verifies the 120-task matrix (12 models × 5 contexts × 2 roles), the frozen
binary/config hashes, the workload ELF hashes, the 60 SampleRunIDs/seeds and
fault/control pairing. The campaign root is **not** created.

## Stage 1 — Campaign execution (120 runs)

```bash
bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh
```

A fresh launch refuses a non-empty campaign root (`exit 2`) and never uses
`--force`, so it cannot overwrite historical evidence. It writes
`runs/lsu/formal_v333_final_20261112/<Model>-Rxx-{fault,control}/` and
`LSU_Fault_Control_Pair_RAW.csv`; the runner exit code is echoed as
`runner_exit=<n>` and propagated.

### Resume after an interruption

```bash
bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh --resume
# equivalent: RESUME=1 bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh
# or:         bash audit_v3_3_3/trace_closure/final_config/launch_commands_final.sh resume
```

`--resume` forwards `--resume` to `tools/lsu_v332_matrix.py`. Resume scans the
attempt records: COMPLETED tasks are skipped, failed/incomplete tasks get a new
attempt directory (older attempt bytes are preserved), HASH_MISMATCH stops with
a nonzero exit, ORACLE_FAIL is never retried or replaced. Without `--resume` a
non-empty root is always refused.

## Stage 2 — Manifest-only collection

```bash
bash audit_v3_3_3/trace_closure/final_config/02_manifest_only.sh
```

Guards: the campaign root must exist, `campaign_identity.json` must carry
`campaign_id=LSU-V333-FINAL-20261112`, and all 120 run directories must contain
`summary.json` + `campaign.json` (otherwise exit 3). Writes **only**
`collector_manifest/LSU_120Run_Campaign_Manifest.csv`,
`LSU_60Fault_60Control_Pair_Map.csv`, `LSU_Control_Zero_Proof_Final.csv` and
`per_run/`. No XLSX/readiness export at this stage; this directory is asserted
disjoint from `collector_full/`.

## Stage 3 — Full Collector

```bash
bash audit_v3_3_3/trace_closure/final_config/03_full_collector.sh
```

Guards: the same 120-run completeness check plus the Stage-2 artifacts
(`collector_manifest/LSU_120Run_Campaign_Manifest.csv`,
`LSU_60Fault_60Control_Pair_Map.csv`, `LSU_Control_Zero_Proof_Final.csv`) must
exist; otherwise exit 4. Writes **only** `collector_full/`: the same artifacts
plus `LSU_Formal_Experiment_Config_Final.xlsx` (the collector's own Excel) and
`LSU_60Context_Final_Readiness.csv`. This is distinct from the 8-sheet analysis
workbook produced in Stage 4.

## Stage 4 — Final propagation chain, classification and Excel

```bash
bash audit_v3_3_3/trace_closure/final_config/04_final_reports.sh
# explicit regeneration only:
FORCE=1 bash audit_v3_3_3/trace_closure/final_config/04_final_reports.sh
# or: bash audit_v3_3_3/trace_closure/final_config/04_final_reports.sh --force
```

Guards: all Stage-3 `collector_full/` outputs must exist (exit 3), and the
campaign-root identity must still match the frozen binary/config/campaign id.
Existing reports are never overwritten unless `FORCE=1` / `--force` is set
(exit 4).

Produces under the campaign root:

- `LSU_60Context_Causal_Propagation_Final.csv`
- `LSU_60Context_Final_Readiness.csv`
- `LSU_11Context_Repair_Validation.csv`
- `LSU_Control_Audit_Formal.csv`
- `LSU_Final_Experiment_Config.xlsx` (8-sheet analysis workbook)

The control audit is emitted by `tools/lsu_v333_control_proof.py
--emit-control-audit --proof collector_full/LSU_Control_Zero_Proof_Final.csv
--out <root>/LSU_Control_Audit_Formal.csv`. Any `UNKNOWN` or `INVALID`
`ControlInjected` state is a hard failure (exit 5); missing or illegal
injection counts never become a zero-injection PASS.

## Stage 5 — post-campaign gates

```bash
python3 - <<'PY'
import csv
from pathlib import Path
r = Path("runs/lsu/formal_v333_final_20261112")
m = list(csv.DictReader(open(r/"collector_full/LSU_120Run_Campaign_Manifest.csv")))
print("manifest rows", len(m))
print("formal", sum(1 for x in m if x["EvidenceKind"]=="FORMAL"))
readiness = list(csv.DictReader(open(r/"LSU_60Context_Final_Readiness.csv")))
print("readiness rows", len(readiness))
print("ready", sum(1 for x in readiness if x["ChainClass"] in
                  ("COMPLETE_CAUSAL_CHAIN","VALID_TERMINAL_CHAIN")))
PY
```

Also verify:

- all 120 `campaign.json` files carry `campaign_id=LSU-V333-FINAL-20261112`;
- all `Binary_SHA256 == 62e1b1be...`, all `Config_SHA256 == 8309da72...`;
- 60 fault + 60 control pairs, same seed per pair;
- no run used `audit_v3_3_3/runs/**` or `runs/lsu/formal_v333/**`;
- `LSU_Control_Audit_Formal.csv` has 60 rows, all `ControlInjected=NO` and no
  `UNKNOWN`/`INVALID` state.

## Failure and recovery

| Symptom | Action |
|---|---|
| `refusing to reuse a non-empty formal output dir` | A previous launch exists. Use `--resume` (never `--force`). |
| `campaign root is incomplete` (Stage 2/3, exit 3) | Run `01_launch_campaign.sh --resume`; retry the failed stage. |
| `STEP 2 output missing` (Stage 3, exit 4) | Run `02_manifest_only.sh` first; the pipeline is ordered. |
| `STEP 3 collector_full output missing` (exit 3) | Run `03_full_collector.sh`; do not run Stage 4 on partial evidence. |
| `control audit ... UNKNOWN/INVALID` (exit 5) | Do not publish. Investigate the control run; never hand-edit the audit CSV. |
| `refusing to overwrite an existing report` (exit 4) | Inspect the existing report; regenerate only with explicit `FORCE=1`. |
| `campaign identity mismatch` | The binary/config or campaign id drifted. Stop and re-run the preflight. |

## Frozen limitations (must be carried into the formal report)

- SP05 R01–R05 remain `QUALIFIED` (frozen `writeback_event` unsatisfiable; real suppressed-writeback
  evidence retained).
- RP01 R01–R05 remain `TRACE_INCOMPLETE` (internal-watchdog HANG; terminal metadata complete).
- A03-R02 is `COMPLETE_CAUSAL_CHAIN`.
- Historical Pre-Formal evidence is archived under `audit_v3_3_3/runs/` and must not be mixed into
  the formal result set. The pipeline scripts reject that root outright.
