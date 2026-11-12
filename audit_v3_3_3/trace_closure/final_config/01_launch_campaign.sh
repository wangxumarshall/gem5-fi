#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — STEP 1: execute the 120 runs.
# DO NOT RUN until the researcher explicitly authorizes the campaign.
set -euo pipefail
ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
OUT=runs/lsu/formal_v333_final_20261112

if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null || true)" ]; then
  echo "refusing to reuse a non-empty formal output dir: $OUT" >&2
  exit 2
fi
mkdir -p "$OUT"

python3 tools/lsu_v332_matrix.py \
  --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base "$OUT" \
  --out-csv "$OUT/LSU_Fault_Control_Pair_RAW.csv" \
  --campaign-id LSU-V333-FINAL-20261112 \
  --expected-binary-sha "$BIN" \
  --expected-config-sha "$CFG"
