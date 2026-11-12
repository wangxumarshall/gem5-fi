#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — verified command block.
# DO NOT RUN until the researcher explicitly authorizes the campaign.
set -u
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12 || exit 2

python3 tools/lsu_v332_matrix.py \
  --models all --roles fault,control --contexts 1,2,3,4,5 \
  --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv \
  --campaign-id LSU-V333-FINAL-20261112 \
  --expected-binary-sha 62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd \
  --expected-config-sha 8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
runner_exit=$?
echo "runner_exit=$runner_exit"

python3 tools/lsu_v333_launch.py \
  --runs runs/lsu/formal_v333 \
  --campaign-id LSU-V333-FINAL-20261112 \
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --out runs/lsu/formal_v333/collector \
  --manifest-only
collector_exit=$?
echo "collector_exit=$collector_exit"

exit $(( runner_exit != 0 || collector_exit != 0 ))
