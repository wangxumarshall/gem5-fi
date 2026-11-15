#!/bin/bash
# Generate (and optionally execute) the 40 frozen formal samples.
#
#   ./run_mmu_formal_40.sh --dry-run          # default: print commands only
#   ./run_mmu_formal_40.sh --execute [OUTROOT]
#
# Re-running the 40 formal samples is NOT required to reproduce the original
# campaign; it is an independent replication.  Output goes to a fresh root and
# can never overwrite MMU_FORMAL_CAMPAIGN_20261113.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

MODE=dry
OUT_ROOT="$MMU_REPO_ROOT/runs/MMU_FINAL_FORMAL_40_REPLICA"
if [ "${1:-}" = "--execute" ]; then MODE=execute; OUT_ROOT="${2:-$OUT_ROOT}"; fi
[ "${1:-}" = "--dry-run" ] && MODE=dry

MATRIX="$MMU_RESULTS_DIR/formal/campaign_package/40_Sample_Matrix_Completed.csv"
[ -f "$MATRIX" ] || mmu_die "missing matrix: $MATRIX"

mmu_info "mode: $MODE"
mmu_info "output root: $OUT_ROOT"
mmu_info "matrix: $MATRIX"

n=0
while IFS= read -r sid; do
    n=$((n + 1))
    if [ "$MODE" = dry ]; then
        printf 'python3 tools/mmu_formal_runner.py --repo-root %q --out-root %q --excel %q --csv %q --param-authority %q --sample %q\n' \
            "$MMU_REPO_ROOT" "$OUT_ROOT" \
            "$MMU_REPO_ROOT/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx" \
            "$MMU_REPO_ROOT/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/MMU_40_Sample_Matrix.csv" \
            "$MMU_REPO_ROOT/phase3/final/MMU_Final_Formal_Readiness_Package_v3.0.2/MMU_Parameter_Authority_v3.0.2.json" \
            "$sid"
    else
        mmu_info "[$n/40] $sid"
        "$MMU_REPRO_DIR/run_mmu_sample.sh" "$sid" "$OUT_ROOT"
    fi
done < <(tail -n +2 "$MATRIX" | cut -d, -f2)

mmu_info "samples enumerated: $n"
[ "$n" = 40 ] || mmu_die "expected 40 samples, found $n"
[ "$MODE" = dry ] && mmu_info "dry run complete; nothing executed"
