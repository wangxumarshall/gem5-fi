#!/usr/bin/env bash
# STEP 2: manifest-only collection (no XLSX/readiness export).
set -euo pipefail
ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225

python3 tools/lsu_v333_launch.py \
  --runs runs/lsu/formal_v333_final_20261112 \
  --campaign-id LSU-V333-FINAL-20261112 \
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --out runs/lsu/formal_v333_final_20261112/collector_manifest \
  --manifest-only \
  --expected-binary-sha "$BIN" \
  --expected-config-sha "$CFG"
