#!/usr/bin/env bash
# R6-S W1 parallel single-seed worker (one exclusive lock + dir per RunID/seed).
# Usage: r6_s_w1_par_seed.sh <RUN_ID> <SEED> <BIN> <OUTROOT> [timeout_seconds]
# The queue enforces the global concurrency/gate policy; this worker enforces
# per-seed exclusivity, fresh directories, binary SHA identity, and atomic
# manifest finalization.
set -u
RUN_ID="${1:?run id}"; SEED="${2:?seed}"; BIN="${3:?binary}"
OUTROOT="${4:?outroot}"; TIMEOUT="${5:-43200}"
WT="${WT_OVERRIDE:-/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-w1-continuation-20261101}"
MATRIX=/home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv
DIR="$OUTROOT/${RUN_ID}_s${SEED}"
LOG=/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1par-${RUN_ID}-s${SEED}.log
mkdir -p "$OUTROOT" "$DIR"

exec 9>"$DIR/.lock"
flock -n 9 || { echo "REFUSED: $DIR already locked" >&2; exit 3; }
if [ -e "$DIR/.done" ]; then echo "ALREADY DONE: $DIR"; exit 0; fi
if [ -n "$(ls -A "$DIR" 2>/dev/null | grep -v '^\.lock$' || true)" ]; then
  echo "REFUSED: non-fresh output dir $DIR" >&2; exit 4
fi

SHA=$(sha256sum "$BIN" | awk '{print $1}')
SRCHEAD=$(git -C "$WT" rev-parse HEAD)
START=$(date -Iseconds)
CMD="LSU_GEM5_BIN=$BIN python3 $WT/tools/lsu_campaign.py --matrix $MATRIX --outdir $DIR --cells $RUN_ID --phase trial --seed-start $SEED --max-seeds-per-cell 1 --max-parallel 1 --timeout $TIMEOUT"
export RUN_ID SEED TIMEOUT BIN SHA SRCHEAD START CMD DIR LOG

python3 - "$DIR/manifest.json" <<'PY'
import json, os, sys
json.dump({
 "run_id": os.environ["RUN_ID"], "seed": int(os.environ["SEED"]),
 "wall_budget_seconds": int(os.environ["TIMEOUT"]),
 "binary_path": os.environ["BIN"], "binary_sha256": os.environ["SHA"],
 "binary_source_head": os.environ["SRCHEAD"],
 "analysis_tool_head": os.environ["SRCHEAD"],
 "start_time": os.environ["START"], "launcher_pid": os.getpid(),
 "pgid": os.getpgid(0), "command": os.environ["CMD"],
 "status": "RUNNING", "output_dir": os.environ["DIR"],
 "log": os.environ["LOG"],
 "span_extra_env": os.environ.get("LSU_LSQFWD_F0_SPAN_EXTRA", ""),
}, open(sys.argv[1], "w"), indent=1)
PY

echo "START $RUN_ID seed$SEED at $START pid=$$ pgid=$(ps -o pgid= -p $$ | tr -d ' ') sha=$SHA dir=$DIR"
cd "$WT" || exit 5
LSU_GEM5_BIN="$BIN" timeout --signal=INT --kill-after=120 "$((TIMEOUT + 900))" \
  python3 "$WT/tools/lsu_campaign.py" \
  --matrix "$MATRIX" --outdir "$DIR" --cells "$RUN_ID" --phase trial \
  --seed-start "$SEED" --max-seeds-per-cell 1 --max-parallel 1 \
  --timeout "$TIMEOUT" >>"$LOG" 2>&1
RC=$?
END=$(date -Iseconds)
echo "$RC" > "$DIR/.exit_code"
python3 - "$DIR/manifest.json" "$END" "$RC" <<'PY'
import json, sys
p, end, rc = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = json.load(open(p))
d.update({"end_time": end, "exit_code": rc,
          "status": "FINISHED" if rc == 0 else "FAILED"})
json.dump(d, open(p, "w"), indent=1)
PY
if [ $? -ne 0 ]; then
  echo "ERROR: manifest finalize failed for $DIR; .done NOT written" >&2
  exit 6
fi
touch "$DIR/.done"
echo "END $RUN_ID seed$SEED at $END rc=$RC"
