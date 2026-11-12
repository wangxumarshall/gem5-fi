# LSU v3.3.3 — Finalization Runbook

**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Final source HEAD:** `b5031bf7` (A01 8-byte correction)
**Final binary:** `build/ARM/gem5.opt`, SHA256 `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Final run set:** `audit_v3_3_3/runs/` (120 dirs; every `summary.json` must carry the final SHA)
**Pre-correction history:** `audit_v3_3_3/runs_685d88f7/` (not mixed)

## 1. Generate the acceptance tables

```bash
python3 tools/lsu_v332_report.py \
  --runs audit_v3_3_3/runs --out audit_v3_3_3
```
Writes: `roi/LSU_60Context_ROI_Percentile_Mapping.csv`,
`roi/LSU_60Context_Distinctness_Audit.csv`,
`LSU_60Context_Final_Readiness_Matrix.csv`,
`controls/LSU_Fault_Control_Pair_FINAL.csv`,
`propagation/LSU_60Context_Causal_Propagation_Final.csv`.

```bash
python3 tools/lsu_v333_propagation.py \
  --runs audit_v3_3_3/runs \
  --out audit_v3_3_3/LSU_60Context_Causal_Propagation.csv
```

## 2. Build the final workbook

```bash
python3 tools/lsu_v333_workbook.py \
  --runs audit_v3_3_3/runs \
  --mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --controls audit_v3_3_3/controls/LSU_Fault_Control_Pair_FINAL.csv \
  --causal audit_v3_3_3/LSU_60Context_Causal_Propagation.csv \
  --out audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx
```

## 3. Required deliverable copies

```bash
cp audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv \
   audit_v3_3_3/LSU_60Context_Final_Readiness.csv
cp audit_v3_3_3/controls/LSU_Fault_Control_Pair_FINAL.csv \
   audit_v3_3_3/LSU_Fault_Control_Final_Audit.csv
# Workload/oracle audit from the workbook Workload_Oracle sheet or the
# authoritative matrix + measured control checksums; never invent a value.
```

## 4. Hard verification (real commands, real output)

```bash
python3 - <<'EOF'
import csv, glob, json
from collections import Counter
# 120 summaries, one SHA
shas = Counter()
rows = []
for p in glob.glob('audit_v3_3_3/runs/*/summary.json'):
    d = json.load(open(p)); shas[d.get('binary_sha')] += 1; rows.append((p, d))
assert len(rows) == 120, len(rows)
assert len(shas) == 1 and '1126e0fd' in next(iter(shas)), shas
fault = [d for p, d in rows if '-fault/' in p]
control = [d for p, d in rows if '-control/' in p]
assert len(fault) == 60 and len(control) == 60
assert all((d.get('injection_count') or 0) > 0 for d in fault)
assert all((d.get('injection_count') or 0) == 0 for d in control)
print('120 runs; one binary SHA; 60 fault inject >0; 60 control ==0')
print('terminals', Counter(d.get('terminal') for d in fault))
EOF
```

## 5. Regression

```bash
pytest tests/ -q
pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q
```

## 6. Ready-Gate cross-checks (all must hold)

- 12 models × 5 contexts = 60; no duplicate within a model.
- Every context has ROI start/end/N, percentile, absolute ordinal = `start + ceil(p*N) − 1`, dyn seq, PC, instruction type, LQ/SQ identity (where applicable), dynamic state.
- Every fault/control pair: same seed, ELF, binary, config, ROI, ordinal; control zero-injection proof is `MOUNTED_BUT_DISABLED` (35) or `INJECTOR_ABSENT` (25).
- Every causal row: injection → activation/first divergence → downstream/consumer → commit/squash/replay → oracle/terminal; `COMPLETE` requires all witnesses.
- MASKED rows carry a mechanism; SQUASHED carries no-arch-entry proof; HANG carries the internal watchdog/deadline; SDC carries an independent oracle FAIL.
- 60/60 authoritative SampleRunID/Seed preserved; 30 candidate contexts carry `OVERRIDE_APPROVED`.
- Final workbook has all 8 sheets and no blank critical field marked PASS.

## 7. Package

```bash
zip -r LSU_v3.3.3_Formal_Experiment_Ready_Package.zip \
  audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md \
  audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv \
  audit_v3_3_3/LSU_v3.3.3_Consolidated_Repair_Plan.md \
  audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md \
  audit_v3_3_3/decisions \
  audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx \
  audit_v3_3_3/LSU_60Context_Final_Readiness.csv \
  audit_v3_3_3/LSU_60Context_Causal_Propagation.csv \
  audit_v3_3_3/LSU_Fault_Control_Final_Audit.csv \
  audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv \
  audit_v3_3_3/LSU_Final_Binary_Provenance.md \
  audit_v3_3_3/build/LSU_Final_Source_Diff.patch \
  audit_v3_3_3/LSU_Independent_Acceptance.md \
  audit_v3_3_3/reports \
  audit_v3_3_3/roi \
  audit_v3_3_3/controls \
  audit_v3_3_3/propagation \
  audit_v3_3_3/census \
  audit_v3_3_3/gate_tests \
  audit_v3_3_3/build/PROVENANCE.md \
  audit_v3_3_3/build/RUNBOOK.md \
  audit_v3_3_3/build/v333_build2.log \
  audit_v3_3_3/runs
unzip -t LSU_v3.3.3_Formal_Experiment_Ready_Package.zip
sha256sum LSU_v3.3.3_Formal_Experiment_Ready_Package.zip \
  | tee LSU_v3.3.3_Formal_Experiment_Ready_Package.zip.sha256
```
