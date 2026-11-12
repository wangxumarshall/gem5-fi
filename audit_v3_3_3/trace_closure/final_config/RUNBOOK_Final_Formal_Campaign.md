# LSU v3.3.3 — Final Formal Campaign Runbook

**Status:** `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES`
**DO NOT RUN until the researcher explicitly authorizes the campaign.**

- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- Binary: `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
- Config: `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
- Campaign ID: `LSU-V333-FINAL-20261112`
- Unique output root: `runs/lsu/formal_v333_final_20261112`
- Scope: 12 models × 5 contexts × 2 roles = **120 runs**

## Stage 0 — preflight (read-only)

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
sha256sum build/ARM/gem5.opt configs/se/lsu_proxy.py
# expected: 62e1b1be... and 8309da72...
test ! -e runs/lsu/formal_v333_final_20261112 || echo "DIR EXISTS — investigate"
```

## Stage 1 — Campaign execution (120 runs)

```bash
bash audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh
```

The script refuses a non-empty output dir. It does **not** use `--force`, so it cannot overwrite
historical evidence. It writes `runs/lsu/formal_v333_final_20261112/<Model>-Rxx-{fault,control}/`
and `LSU_Fault_Control_Pair_RAW.csv`.

## Stage 2 — Manifest-only collection

```bash
bash audit_v3_3_3/trace_closure/final_config/02_manifest_only.sh
```

Writes `collector_manifest/LSU_120Run_Campaign_Manifest.csv`,
`LSU_60Fault_60Control_Pair_Map.csv`, `LSU_Control_Zero_Proof_Final.csv` and `per_run/`.
No XLSX/readiness export at this stage.

## Stage 3 — Full Collector

```bash
bash audit_v3_3_3/trace_closure/final_config/03_full_collector.sh
```

Writes the same artifacts plus `LSU_Formal_Experiment_Config_Final.xlsx` and
`LSU_60Context_Final_Readiness.csv` under `collector_full/`. This is the collector's own final
Excel; it is distinct from the 8-sheet analysis workbook in Stage 4.

## Stage 4 — Final propagation chain, classification and Excel

```bash
bash audit_v3_3_3/trace_closure/final_config/04_final_reports.sh
```

Produces under the campaign root:

- `LSU_60Context_Causal_Propagation_Final.csv`
- `LSU_60Context_Final_Readiness.csv`
- `LSU_11Context_Repair_Validation.csv`
- `LSU_Final_Experiment_Config.xlsx` (8-sheet analysis workbook)

## Stage 5 — post-campaign gates

```bash
python3 - <<'PY'
import csv
from pathlib import Path
r = Path("runs/lsu/formal_v333_final_20261112")
m = list(csv.DictReader(open(r/"LSU_120Run_Campaign_Manifest.csv")))
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
- `LSU_Control_Zero_Proof_Final.csv` has 60 zero-injection controls.

## Distinction of collection stages

| Stage | Command | Output |
|---|---|---|
| Campaign execution | `01_launch_campaign.sh` | 120 run dirs + raw pair CSV |
| Manifest-only | `02_manifest_only.sh` | manifest/pair/control-proof/per-run only |
| Full Collector | `03_full_collector.sh` | the above + collector XLSX + readiness |
| Final reports | `04_final_reports.sh` | propagation CSV, classification, 11-context validation, 8-sheet XLSX |

## Frozen limitations (must be carried into the formal report)

- SP05 R01–R05 remain `QUALIFIED` (frozen `writeback_event` unsatisfiable; real suppressed-writeback
  evidence retained).
- RP01 R01–R05 remain `TRACE_INCOMPLETE` (internal-watchdog HANG; terminal metadata complete).
- A03-R02 is `COMPLETE_CAUSAL_CHAIN`.
- Historical Pre-Formal evidence is archived under `audit_v3_3_3/runs/` and must not be mixed into
  the formal result set.
