#!/bin/bash
# Run one frozen formal sample by SampleRunID through the authoritative runner.
#
#   ./run_mmu_sample.sh M01-F0-W9-S01-R01 [OUTPUT_ROOT]
#
# The runner validates the Model/Workload/Context triple against the frozen
# authority, refuses to overwrite an existing non-empty output directory,
# checks binary/source/workload hashes, resolves the control oracle, and
# invokes the trace validator.  It never generates a seed.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

SID="${1:-}"
OUT_ROOT="${2:-$MMU_REPO_ROOT/runs/MMU_FINAL_VALIDATION}"
[ -n "$SID" ] || mmu_die "usage: $0 <SampleRunID> [OUTPUT_ROOT]"

mmu_check_runtime_assets

# M05/M07 parity evidence (M05 DecoyVA column, pilot decoy VA, M07 exact VA)
# lives in the v3.0.2 authority package.  Pass it explicitly: the base frozen
# workbook does not carry the parameter-authority JSON next to it.
AUTH_DIR="$MMU_REPO_ROOT/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2"
AUTH_EXCEL="$AUTH_DIR/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx"
AUTH_CSV="$AUTH_DIR/MMU_40_Sample_Matrix.csv"
AUTH_JSON="$AUTH_DIR/MMU_Parameter_Authority_v3.0.2.json"
for f in "$AUTH_EXCEL" "$AUTH_CSV" "$AUTH_JSON"; do
    [ -f "$f" ] || mmu_die "missing parity authority: $f"
done

case "$OUT_ROOT" in
  *MMU_FORMAL_CAMPAIGN_20261113*)
    mmu_die "refusing to write into the frozen formal campaign: $OUT_ROOT" ;;
esac

mmu_info "sample:       $SID"
mmu_info "output root:  $OUT_ROOT"
mmu_info "gem5:         $MMU_GEM5"
mmu_info "authority:    v3.0.2"
python3 "$MMU_REPO_ROOT/tools/mmu_formal_runner.py" \
    --repo-root "$MMU_REPO_ROOT" \
    --out-root "$OUT_ROOT" \
    --excel "$AUTH_EXCEL" \
    --csv "$AUTH_CSV" \
    --param-authority "$AUTH_JSON" \
    --sample "$SID"
