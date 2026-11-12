#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — STEP 1/5: execute the 120 runs.
#
# DO NOT RUN until the researcher explicitly authorizes the campaign.
#
#   bash 01_launch_campaign.sh --dry-run   # validate 120 commands; write nothing
#   bash 01_launch_campaign.sh             # fresh launch; refuses a non-empty root
#   bash 01_launch_campaign.sh --resume    # continue an interrupted campaign
#   RESUME=1 bash 01_launch_campaign.sh    # same as --resume
#
# The campaign root is WORKTREE-relative. A fresh launch refuses any non-empty
# root; only an explicit --resume / RESUME=1 forwards --resume to the runner.
set -euo pipefail

ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

# Frozen identity — never edit.
BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
CAMPAIGN_ID=LSU-V333-FINAL-20261112
OUT=runs/lsu/formal_v333_final_20261112

usage() {
  cat >&2 <<'EOF'
usage: 01_launch_campaign.sh [--resume] [--dry-run]
  --dry-run  print the 120 planned commands and exit; nothing is written
  --resume   continue an interrupted campaign (forwards --resume); also RESUME=1
EOF
}

RESUME=${RESUME:-0}
DRY_RUN=${DRY_RUN:-0}
for arg in "$@"; do
  case "$arg" in
    --resume)  RESUME=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown argument: $arg" >&2; usage; exit 2 ;;
  esac
done

if [ "$RESUME" = "1" ]; then
  if [ ! -d "$OUT" ]; then
    echo "error: RESUME requested but the campaign root does not exist: $OUT" >&2
    exit 2
  fi
elif [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null || true)" ]; then
  # Fail closed: never reuse or overwrite campaign evidence implicitly.
  echo "refusing to reuse a non-empty formal output dir: $OUT" >&2
  echo "use --resume (or RESUME=1) to continue an interrupted campaign" >&2
  exit 2
fi

# A dry run validates the matrix and must never create the campaign root.
if [ "$DRY_RUN" != "1" ]; then
  mkdir -p "$OUT"
fi

runner_args=(
  tools/lsu_v332_matrix.py
  --models all --roles fault,control --contexts 1,2,3,4,5
  --out-base "$OUT"
  --out-csv "$OUT/LSU_Fault_Control_Pair_RAW.csv"
  --campaign-id "$CAMPAIGN_ID"
  --expected-binary-sha "$BIN"
  --expected-config-sha "$CFG"
)
if [ "$DRY_RUN" = "1" ]; then
  runner_args+=(--dry-run)
fi
if [ "$RESUME" = "1" ]; then
  runner_args+=(--resume)
fi

# set -e already aborts on failure; capture the code so callers see it explicitly.
set +e
python3 "${runner_args[@]}"
status=$?
set -e
echo "runner_exit=$status"
exit "$status"
