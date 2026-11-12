#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — exact ordered command block.
#
# DO NOT RUN until the researcher explicitly authorizes the campaign.
# One stage per invocation; the default prints the whole plan and runs nothing.
#
#   bash launch_commands_final.sh plan       # print this sequence (default)
#   bash launch_commands_final.sh preflight  # verify frozen SHAs, no run dir
#   bash launch_commands_final.sh dry-run    # validate 120 commands, write nothing
#   bash launch_commands_final.sh launch     # STEP 1: fresh campaign
#   bash launch_commands_final.sh resume     # STEP 1: continue interrupted run
#   bash launch_commands_final.sh collect    # STEP 2 + STEP 3
#   bash launch_commands_final.sh report     # STEP 4 (FORCE=1 to regenerate)
set -euo pipefail

ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

# Frozen identity — never edit.
BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
CAMPAIGN_ID=LSU-V333-FINAL-20261112
RUNS=runs/lsu/formal_v333_final_20261112
CFG_DIR=audit_v3_3_3/trace_closure/final_config

usage() {
  cat >&2 <<'EOF'
usage: launch_commands_final.sh <stage>
  plan | preflight | dry-run | launch | resume | collect | report
EOF
}

plan() {
  cat <<EOF
frozen binary : $BIN
frozen config : $CFG
campaign id   : $CAMPAIGN_ID
campaign root : $RUNS

  bash $CFG_DIR/launch_commands_final.sh preflight   # frozen SHAs, root state
  bash $CFG_DIR/launch_commands_final.sh dry-run     # 120-task validation only
  bash $CFG_DIR/launch_commands_final.sh launch      # STEP 1 fresh launch
  bash $CFG_DIR/launch_commands_final.sh resume      # STEP 1 after interruption
  bash $CFG_DIR/launch_commands_final.sh collect     # STEP 2 then STEP 3
  bash $CFG_DIR/launch_commands_final.sh report      # STEP 4 final reports
  FORCE=1 bash $CFG_DIR/launch_commands_final.sh report   # explicit regeneration
EOF
}

case "${1:-plan}" in
  plan)
    plan
    ;;
  preflight)
    printf '%s  %s\n' \
      "$BIN" build/ARM/gem5.opt \
      "$CFG" configs/se/lsu_proxy.py | sha256sum -c -
    if [ -e "$RUNS" ] && [ -n "$(ls -A "$RUNS" 2>/dev/null || true)" ]; then
      echo "campaign root already non-empty: $RUNS (use the resume stage)"
    else
      echo "campaign root is empty/absent: $RUNS"
    fi
    ;;
  dry-run)
    bash "$CFG_DIR/01_launch_campaign.sh" --dry-run
    ;;
  launch)
    bash "$CFG_DIR/01_launch_campaign.sh"
    ;;
  resume)
    RESUME=1 bash "$CFG_DIR/01_launch_campaign.sh" --resume
    ;;
  collect)
    bash "$CFG_DIR/02_manifest_only.sh"
    bash "$CFG_DIR/03_full_collector.sh"
    ;;
  report)
    bash "$CFG_DIR/04_final_reports.sh"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "error: unknown stage: $1" >&2
    usage
    exit 2
    ;;
esac
