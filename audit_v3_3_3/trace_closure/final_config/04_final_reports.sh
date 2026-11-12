#!/usr/bin/env bash
# STEP 4: final propagation chain + classification + Excel from the formal run.
set -euo pipefail
ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

RUNS=runs/lsu/formal_v333_final_20261112
COLL=runs/lsu/formal_v333_final_20261112/collector_full
CTL="$RUNS/LSU_Control_Audit_Formal.csv"

# 4a. 60-context causal propagation table
python3 tools/lsu_v333_propagation.py \
  --runs "$RUNS" \
  --out "$RUNS/LSU_60Context_Causal_Propagation_Final.csv"

# 4b. final classification/readiness + 11-context repair validation
python3 tools/lsu_v333_trace_closure.py \
  --runs "$RUNS" \
  --propagation "$RUNS/LSU_60Context_Causal_Propagation_Final.csv" \
  --out-readiness "$RUNS/LSU_60Context_Final_Readiness.csv" \
  --out-validation "$RUNS/LSU_11Context_Repair_Validation.csv"

# 4c. derive the control-audit CSV expected by the 8-sheet workbook
python3 - "$COLL/LSU_Control_Zero_Proof_Final.csv" "$CTL" <<'PY'
import csv, sys
src, dst = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, newline="")))
with open(dst, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["ModelID", "ContextID",
                                       "ControlInjected", "ControlZeroProof"])
    w.writeheader()
    for r in rows:
        injected = "NO" if str(r.get("InjectionCount", "")).strip() in ("0", "") else "YES"
        w.writerow({"ModelID": r["ModelID"], "ContextID": r["ContextID"],
                    "ControlInjected": injected,
                    "ControlZeroProof": r["ControlZeroProof"]})
PY

# 4d. 8-sheet final experiment workbook (collector_full already has its own XLSX)
python3 tools/lsu_v333_workbook.py \
  --runs "$RUNS" \
  --mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --controls "$CTL" \
  --causal "$RUNS/LSU_60Context_Causal_Propagation_Final.csv" \
  --out "$RUNS/LSU_Final_Experiment_Config.xlsx"

echo "wrote:"
echo "  $RUNS/LSU_60Context_Causal_Propagation_Final.csv"
echo "  $RUNS/LSU_60Context_Final_Readiness.csv"
echo "  $RUNS/LSU_11Context_Repair_Validation.csv"
echo "  $RUNS/LSU_Final_Experiment_Config.xlsx"
echo "  $COLL/LSU_Formal_Experiment_Config_Final.xlsx"
