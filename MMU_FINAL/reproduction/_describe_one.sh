#!/bin/bash
# Internal worker: generate one formal sample's describe plan.  Read-only.
set -uo pipefail
SID="$1"
REPO="${MMU_REPO_ROOT:?}"
AUTH_DIR="$REPO/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2"
if python3 "$REPO/tools/mmu_formal_runner.py" \
      --repo-root "$REPO" --out-root "$REPO/runs/MMU_FINAL_PREFLIGHT" \
      --describe --sample "$SID" \
      --excel "$AUTH_DIR/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx" \
      --csv "$AUTH_DIR/MMU_40_Sample_Matrix.csv" \
      --param-authority "$AUTH_DIR/MMU_Parameter_Authority_v3.0.2.json" \
      > "/tmp/mmu_describe_$SID.txt" 2>&1; then
    echo "OK $SID"
else
    echo "FAIL $SID"
fi
