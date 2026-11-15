#!/bin/bash
# Read-only preflight for the frozen MMU experiment.
# Checks the clone, authority, workload payloads and all 40 describe plans.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

fail=0
ok()   { echo "PASS  $*"; }
bad()  { echo "FAIL  $*"; fail=1; }

echo "== repository =="
[ -f "$MMU_REPO_ROOT/CLAUDE.md" ] && ok "repository root $MMU_REPO_ROOT" || bad "not a repository root"
[ -f "$MMU_REPO_ROOT/CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc" ] \
    && ok "CHAOSPropagation source present" || bad "CHAOSPropagation source missing"

echo "== python dependencies =="
python3 - <<'EOF' && ok "python: yaml + openpyxl available" || { echo "  pip install -r reproduction/requirements.txt"; exit 1; }
import yaml, openpyxl
EOF

echo "== frozen authority =="
for f in phase3/freeze/authority/MMU_40_Sample_Matrix.csv \
         phase3/freeze/authority/MMU_Formal_Config.json; do
    [ -f "$MMU_REPO_ROOT/$f" ] && ok "$f" || bad "missing $f"
done

echo "== workloads =="
for w in W9 W10 W10S W11 W12 W13 W14; do
    if ls "$MMU_REPO_ROOT"/workloads/mmu*/${w}* >/dev/null 2>&1; then ok "workload $w"; else bad "workload $w"; fi
done

echo "== runtime assets =="
[ -x "$MMU_GEM5" ] && ok "gem5 $(sha256sum "$MMU_GEM5" | cut -d' ' -f1)" || bad "gem5 binary (run reproduction/build_mmu.sh)"
[ -f "$MMU_KERNEL" ] && ok "kernel" || bad "kernel (run reproduction/prepare_runtime_assets.sh)"
[ -d "$MMU_CHECKPOINT" ] && ok "checkpoint" || bad "checkpoint"
[ -f "$MMU_DISK_TEMPLATE" ] && ok "disk template" || bad "disk template"

echo "== archived results =="
python3 "$MMU_REPRO_DIR/verify_archive.py" --quiet && ok "results archive hashes" || bad "results archive hashes"

echo "== 40 describe plans =="
if [ -x "$MMU_GEM5" ] && [ -f "$MMU_KERNEL" ] && [ -d "$MMU_CHECKPOINT" ]; then
    MATRIX="$MMU_RESULTS_DIR/formal/campaign_package/40_Sample_Matrix_Completed.csv"
    export MMU_REPO_ROOT
    RESULT=/tmp/mmu_describe_results.txt
    tail -n +2 "$MATRIX" | cut -d, -f2 | \
        xargs -P "${MMU_PREFLIGHT_JOBS:-8}" -n1 "$MMU_REPRO_DIR/_describe_one.sh" > "$RESULT"
    p=$(grep -c '^OK ' "$RESULT" || true)
    if [ "$p" = 40 ]; then
        ok "describe plans: 40/40"
    else
        bad "describe plans: $p/40"
        grep '^FAIL ' "$RESULT" | sed 's/^/        /' || true
    fi
else
    echo "SKIP  describe plans (runtime assets absent)"
fi

[ "$fail" = 0 ] && echo "MMU_PREFLIGHT=PASS" || { echo "MMU_PREFLIGHT=FAIL"; exit 1; }
