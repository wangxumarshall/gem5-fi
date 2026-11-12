#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — verified command block (authorization copy).
# DO NOT RUN until the researcher explicitly authorizes the campaign.
set -euo pipefail
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12

BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
OUT=runs/lsu/formal_v333_final_20261112
CAMPAIGN=LSU-V333-FINAL-20261112

# 0) frozen artifact preflight
echo "$BIN  build/ARM/gem5.opt" | sha256sum -c -
echo "$CFG  configs/se/lsu_proxy.py" | sha256sum -c -

# 1) 120-task dry-run (no dirs, no gem5)
python3 tools/lsu_v332_matrix.py \
  --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base "$OUT" \
  --campaign-id "$CAMPAIGN" \
  --expected-binary-sha "$BIN" \
  --expected-config-sha "$CFG" \
  --dry-run

# 2) 120 formal runs (60 fault + 60 control)
python3 tools/lsu_v332_matrix.py \
  --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base "$OUT" \
  --out-csv "$OUT/LSU_Fault_Control_Pair_RAW.csv" \
  --campaign-id "$CAMPAIGN" \
  --expected-binary-sha "$BIN" \
  --expected-config-sha "$CFG"
runner_exit=$?
echo "runner_exit=$runner_exit"

# 2b) after an interruption: resume only unfinished/failed attempts
# python3 tools/lsu_v332_matrix.py \
#   --models all --roles fault,control --contexts 1,2,3,4,5 \
#   --out-base "$OUT" --out-csv "$OUT/LSU_Fault_Control_Pair_RAW.csv" \
#   --campaign-id "$CAMPAIGN" \
#   --expected-binary-sha "$BIN" --expected-config-sha "$CFG" \
#   --resume

# 3) collect the formal manifest from THIS campaign root only
python3 tools/lsu_v333_launch.py \
  --runs "$OUT" \
  --campaign-id "$CAMPAIGN" \
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --out "$OUT/collector_manifest" \
  --manifest-only \
  --expected-binary-sha "$BIN" \
  --expected-config-sha "$CFG"
collector_exit=$?
echo "collector_exit=$collector_exit"

exit $(( runner_exit != 0 || collector_exit != 0 ))
