#!/usr/bin/env bash
# R6-C single-seed launcher (one RunID x one seed, independent dir + lock).
# Usage: r6_c_seed.sh <RUN_ID> <SEED> [timeout_seconds]
set -u
RUN_ID="${1:?run id}"; SEED="${2:?seed}"; TIMEOUT="${3:-43200}"
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
BIN="${R6C_BIN:-$WT/CHAOS/gem5/build/ARM/gem5.opt}"
OUTROOT="${R6C_OUTROOT:-/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/runs}"
LOCKROOT="${R6C_LOCKROOT:-/home/sdc/gem5-fi-ding-cleanup-20261029/r6c_locks}"
DIR="$OUTROOT/${RUN_ID}_s${SEED}"
LOG="${R6C_LOG:-/home/sdc/gem5-fi-ding-cleanup-20261029/r6c-${RUN_ID}-s${SEED}.log}"
LOCK="$LOCKROOT/${RUN_ID}_s${SEED}.lock"
mkdir -p "$OUTROOT" "$LOCKROOT"
exec 9>"$LOCK"
flock -n 9 || { echo "REFUSED: lock held $LOCK" >&2; exit 3; }
if [ -e "$DIR/.done" ]; then echo "ALREADY DONE: $DIR"; exit 0; fi
if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
  echo "REFUSED: non-fresh output dir $DIR" >&2; exit 4
fi
[ -x "$BIN" ] || { echo "MISSING BINARY: $BIN" >&2; exit 7; }
SHA=$(sha256sum "$BIN" | awk '{print $1}')
if [ -n "${R6C_WANT_SHA:-}" ] && [ "$SHA" != "$R6C_WANT_SHA" ]; then
  echo "SHA DRIFT: $SHA != $R6C_WANT_SHA" >&2; exit 7
fi
mkdir -p "$DIR"
START=$(date -Iseconds)
export WT RUN_ID SEED BIN SHA START DIR LOG TIMEOUT
python3 - "$DIR/manifest.json" <<'PY'
import json, os, sys
p = sys.argv[1]
json.dump({
 "run_id": os.environ["RUN_ID"], "seed": int(os.environ["SEED"]),
 "wall_budget_seconds": int(os.environ["TIMEOUT"]),
 "binary_path": os.environ["BIN"], "binary_sha256": os.environ["SHA"],
 "binary_source_head": os.popen("git -C %s rev-parse HEAD" % os.environ["WT"]).read().strip(),
 "analysis_tool_head": os.popen("git -C %s rev-parse HEAD" % os.environ["WT"]).read().strip(),
 "start_time": os.environ["START"], "launcher_pid": os.getpid(),
 "output_dir": os.environ["DIR"], "log": os.environ["LOG"],
 "status": "RUNNING",
}, open(p, "w"), indent=1)
PY
echo "START $RUN_ID seed$SEED at $START sha=$SHA dir=$DIR"
cd "$WT" || exit 5
LSU_GEM5_BIN="$BIN" timeout --signal=INT --kill-after=120 "$((TIMEOUT + 900))" \
  python3 "$WT/tools/lsu_campaign.py" \
  --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir "$DIR" --cells "$RUN_ID" --phase trial --seed-start "$SEED" \
  --max-seeds-per-cell 1 --max-parallel 1 --timeout "$TIMEOUT" >>"$LOG" 2>&1
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
touch "$DIR/.done"
echo "END $RUN_ID seed$SEED at $END rc=$RC"
