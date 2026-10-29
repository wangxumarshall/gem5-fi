#!/usr/bin/env bash
# =============================================================================
# tools/r6_s_run_one.sh — R6 S 单元单 RunID + 单 seed 启动器（SE only）
#
# 每个 RunID+seed 一个独立目录、一把 flock、一份原子 manifest、一个 .done。
# 不覆盖已有证据：目录存在且无 .done 时拒绝启动（FORCE=1 才会继续）。
# 不删除任何旧证据。**不使用 --allow-blocked-models / --allow-stress-only**。
#
# 用法：tools/r6_s_run_one.sh <RUNID> <SEED>
# 记录：run_id/seed/output_dir/cmd/binary_path/binary_sha256/binary_source_head/
#       analysis_tool_head/start_time/end_time/campaign_pid/process_group_id/
#       stdout_log/exit_code/done_flag/matrix_sha256/src_tree_dirty_files
# =============================================================================
set -uo pipefail

RUNID="${1:?usage: r6_s_run_one.sh <RUNID> <SEED>}"
SEED="${2:?usage: r6_s_run_one.sh <RUNID> <SEED>}"
FORCE="${FORCE:-0}"

MAIN=/home/sdc/gem5-fi-ding
REPO=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029
BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt
MATRIX="$MAIN/runs/lsu/r6_matrix_325.csv"
RUNS="$MAIN/runs/lsu"
OUT="$RUNS/r6_s_unit/${RUNID}_s${SEED}"
LOG="$RUNS/r6_s_unit/${RUNID}_s${SEED}.log"
LOCK="$RUNS/r6_s_unit/.lock_${RUNID}_s${SEED}"
# Binary build source head is a FIXED provenance fact (verified: no C++ delta to
# HEAD). It must NOT be replaced by the analysis tool head.
BIN_SOURCE_HEAD="2498573fddaf67bdbca7b1461443ae9e926e650b"
TIMEOUT="${TIMEOUT:-300}"
PY=python3

mkdir -p "$RUNS/r6_s_unit"
[ -x "$BIN" ] || { echo "FATAL: missing binary $BIN" >&2; exit 2; }
[ -f "$MATRIX" ] || { echo "FATAL: missing matrix $MATRIX" >&2; exit 2; }

exec 9>"$LOCK"
if ! flock -n 9; then
    echo "REFUSED: another run holds $LOCK (duplicate start blocked)" >&2
    exit 3
fi

if [ -e "$OUT/.done" ] && [ "$FORCE" != "1" ]; then
    echo "REFUSED: $OUT/.done exists (evidence present; FORCE=1 to rerun)" >&2
    exit 4
fi
if [ -e "$OUT" ] && [ ! -e "$OUT/.done" ] && [ "$FORCE" != "1" ]; then
    if [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
        echo "REFUSED: $OUT exists without .done (incomplete evidence; inspect first)" >&2
        exit 5
    fi
fi
mkdir -p "$OUT"

BIN_SHA=$(sha256sum "$BIN" | awk '{print $1}')
MATRIX_SHA=$(sha256sum "$MATRIX" | awk '{print $1}')
TOOL_HEAD=$(git -C "$REPO" rev-parse HEAD)
SRC_DIRTY=$(git -C "$REPO" status --porcelain --untracked-files=no -- CHAOS/gem5/src | wc -l)
START=$(date -Is)

# NO --allow-blocked-models, NO --allow-stress-only.
CMD="LSU_GEM5_BIN=$BIN $PY tools/lsu_campaign.py --matrix $MATRIX --outdir $OUT --cells $RUNID --phase trial --seed-start $SEED --max-seeds-per-cell 1 --max-parallel 1 --timeout $TIMEOUT"

write_manifest() {   # $1=status $2=exit_code $3=campaign_pid $4=pgid $5=end
    "$PY" - "$OUT/manifest.json" <<PYEOF
import json, os, sys, tempfile
path = sys.argv[1]
d = {
  "batch": "R6-S",
  "run_id": "$RUNID",
  "seed": int("$SEED"),
  "sample_run_id": "s$SEED",
  "output_dir": "$OUT",
  "cmd": "$CMD",
  "run_mode": "standalone-single-seed (no cumulative re-run)",
  "binary_path": "$BIN",
  "binary_sha256": "$BIN_SHA",
  "binary_source_head": "$BIN_SOURCE_HEAD",
  "src_tree_dirty_files": $SRC_DIRTY,
  "analysis_tool_head": "$TOOL_HEAD",
  "matrix_sha256": "$MATRIX_SHA",
  "start_time": "$START",
  "end_time": "$5",
  "campaign_pid": $3,
  "process_group_id": $4,
  "stdout_log": "$LOG",
  "stderr_log": "$LOG",
  "status": "$1",
  "exit_code": $2,
  "done_flag": "$OUT/.done",
}
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
with os.fdopen(fd, "w") as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
os.replace(tmp, path)
PYEOF
}

write_manifest "RUNNING" "None" "None" "None" "None"

cd "$REPO" || exit 2
setsid env LSU_GEM5_BIN="$BIN" "$PY" tools/lsu_campaign.py \
    --matrix "$MATRIX" --outdir "$OUT" --cells "$RUNID" \
    --phase trial --seed-start "$SEED" --max-seeds-per-cell 1 \
    --max-parallel 1 --timeout "$TIMEOUT" \
    >>"$LOG" 2>&1 &
CPID=$!
PGID=$(ps -o pgid= -p "$CPID" 2>/dev/null | tr -d ' ')
write_manifest "RUNNING" "None" "$CPID" "${PGID:-None}" "None"
echo "STARTED run=$RUNID seed=$SEED pid=$CPID pgid=${PGID:-?} out=$OUT"

wait "$CPID"
RC=$?
END=$(date -Is)
write_manifest "FINISHED" "$RC" "$CPID" "${PGID:-None}" "$END"
printf '%s\n' "$RC" > "$OUT/.exit_code"
printf 'batch=R6-S\nrun_id=%s\nseed=%s\nexit_code=%s\nstart=%s\nend=%s\nbinary_sha256=%s\nbinary_source_head=%s\nanalysis_tool_head=%s\n' \
    "$RUNID" "$SEED" "$RC" "$START" "$END" "$BIN_SHA" "$BIN_SOURCE_HEAD" "$TOOL_HEAD" > "$OUT/.done"
echo "DONE run=$RUNID seed=$SEED exit=$RC end=$END"
exit "$RC"
