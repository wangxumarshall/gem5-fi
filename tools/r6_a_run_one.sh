#!/usr/bin/env bash
# =============================================================================
# tools/r6_a_run_one.sh — R6 A 单元单 RunID + 单 seed 启动器（SE only）
#
# 每个 RunID+seed 一个独立目录、一把 flock、一份原子 manifest、一个 .done。
# 不覆盖已有证据：目录存在且无 .done 时拒绝启动（FORCE=1 才会继续，且必须
# 人工确认）。不删除任何旧证据。
#
# 用法：
#   tools/r6_a_run_one.sh <RUNID> <SEED>
# 例：
#   tools/r6_a_run_one.sh A01-F0-W3 1
#
# 记录（manifest.json，原子替换写入）：
#   run_id / seed / sample_run_id / output_dir / cmd / binary_path /
#   binary_sha256 / binary_source_head / analysis_tool_head / start_time /
#   end_time / campaign_pid / process_group_id / stdout_log / stderr_log /
#   exit_code / done_flag / matrix_sha256
# =============================================================================
set -uo pipefail

RUNID="${1:?usage: r6_a_run_one.sh <RUNID> <SEED>}"
SEED="${2:?usage: r6_a_run_one.sh <RUNID> <SEED>}"
FORCE="${FORCE:-0}"

MAIN=/home/sdc/gem5-fi-ding
REPO=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
BIN="$REPO/CHAOS/gem5/build/ARM/gem5.opt"
MATRIX="$MAIN/runs/lsu/r6_matrix_325.csv"
RUNS="$MAIN/runs/lsu"
OUT_TAG="${OUT_TAG:-}"
# [R6-A4] per-cell budget override: the F2 repeat census showed some
# filtered-eligible cells need a much longer run to reach the deterministic
# first-fire position.  Default stays the historic 300s; the batch sets a
# measured budget per cell (run time from the census × 2 margin).
TIMEOUT="${TIMEOUT:-300}"
OUT="$RUNS/r6_a${OUT_TAG}_${RUNID}_s${SEED}"
LOG="$OUT.log"
LOCK="$RUNS/.lock_r6_a${OUT_TAG}_${RUNID}_s${SEED}"
PY=python3

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
# [R6-A-PROVENANCE] record the exact source state the binary was built from:
# HEAD plus whether the src tree was dirty at run time.
BIN_HEAD="$TOOL_HEAD"
SRC_DIRTY=$(git -C "$REPO" status --porcelain --untracked-files=no -- CHAOS/gem5/src | wc -l)
START=$(date -Is)
SID=$(date +%s)

CMD="LSU_GEM5_BIN=$BIN $PY tools/lsu_campaign.py --matrix $MATRIX --outdir $OUT --cells $RUNID --phase trial --seed-start $SEED --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout $TIMEOUT"

write_manifest() {   # $1=status $2=exit_code $3=campaign_pid $4=pgid $5=end
    "$PY" - "$OUT/manifest.json" <<PYEOF
import json, os, sys, tempfile
path = sys.argv[1]
d = {
  "batch": "R6-A",
  "run_id": "$RUNID",
  "seed": int("$SEED"),
  "sample_run_id": "s$SEED",
  "output_dir": "$OUT",
  "cmd": "$CMD",
  "run_mode": "standalone-single-seed (no cumulative re-run)",
  "binary_path": "$BIN",
  "binary_sha256": "$BIN_SHA",
  "binary_source_head": "$BIN_HEAD",
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
    --max-parallel 1 --allow-blocked-models --timeout "$TIMEOUT" \
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
printf 'batch=R6-A\nrun_id=%s\nseed=%s\nexit_code=%s\nstart=%s\nend=%s\nbinary_sha256=%s\nbinary_source_head=%s\nanalysis_tool_head=%s\n' \
    "$RUNID" "$SEED" "$RC" "$START" "$END" "$BIN_SHA" "$BIN_HEAD" "$TOOL_HEAD" > "$OUT/.done"
echo "DONE run=$RUNID seed=$SEED exit=$RC end=$END"
exit "$RC"
