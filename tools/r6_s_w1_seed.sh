#!/usr/bin/env bash
# R6-S W1 single-seed launcher (serial, one W1 gem5 at a time).
#
# [R6-S-W1-CONTINUATION 2026-11-01] Fixed two metadata-finalization defects
# observed on the 2026-10-30/31 W1 queue:
#   1. An earlier revision had an unterminated quote in the finish block:
#      bash aborted AFTER the campaign completed, so .exit_code/.done were
#      never written (S13-F1-W1 seed3).
#   2. RC/END were shell-local and never exported, so the heredoc's
#      os.environ["END"] raised KeyError and the manifest stayed RUNNING
#      (S13-F2-W1 seed2/s3, S13-F0-W1 seed3).
# The finish block now passes values as argv with a quoted heredoc, and
# refuses to write .done if the manifest cannot be finalized.
# R6-S REPAIR2 W1 single-seed launcher (serial, one W1 at a time).
# Usage: r6s_w1_seed.sh <RUN_ID> <SEED> [timeout_seconds]
set -u
RUN_ID="${1:?run id}"; SEED="${2:?seed}"; TIMEOUT="${3:-43200}"
WT="${WT_OVERRIDE:-/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029}"
BIN="${BIN_OVERRIDE:-$WT/CHAOS/gem5/build/ARM/gem5.opt}"
OUTROOT="${OUTROOT_OVERRIDE:-/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2/w1}"
DIR="$OUTROOT/${RUN_ID}_s${SEED}"
LOG=/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1-${RUN_ID}-s${SEED}.log
LOCK=/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1-serial.lock

mkdir -p "$OUTROOT"
exec 9>"$LOCK"
flock -n 9 || { echo "REFUSED: another W1 launcher holds $LOCK" >&2; exit 3; }

if [ -e "$DIR/.done" ]; then echo "ALREADY DONE: $DIR"; exit 0; fi
if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
  echo "REFUSED: non-fresh output dir $DIR" >&2; exit 4
fi
mkdir -p "$DIR"

SHA=$(sha256sum "$BIN" | awk '{print $1}')
SRCHEAD=$(git -C "$WT" rev-parse HEAD)
TOOLHEAD=$(git -C "$WT" rev-parse HEAD)
START=$(date -Iseconds)
CMD="LSU_GEM5_BIN=$BIN python3 $WT/tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir $DIR --cells $RUN_ID --phase trial --seed-start $SEED --max-seeds-per-cell 1 --max-parallel 1 --timeout $TIMEOUT"
export RUN_ID SEED TIMEOUT BIN SHA SRCHEAD TOOLHEAD START CMD DIR LOG

python3 - "$DIR/manifest.json" <<PY
import json, os, sys
p=sys.argv[1]
json.dump({
 "run_id": os.environ["RUN_ID"], "seed": int(os.environ["SEED"]),
 "wall_budget_seconds": int(os.environ["TIMEOUT"]),
 "binary_path": os.environ["BIN"], "binary_sha256": os.environ["SHA"],
 "binary_source_head": os.environ["SRCHEAD"],
 "analysis_tool_head": os.environ["TOOLHEAD"],
 "start_time": os.environ["START"], "launcher_pid": os.getpid(),
 "pgid": os.getpgid(0), "command": os.environ["CMD"],
 "status": "RUNNING", "output_dir": os.environ["DIR"],
 "log": os.environ["LOG"],
 "span_extra_env": os.environ.get("LSU_LSQFWD_F0_SPAN_EXTRA", ""),
}, open(p,"w"), indent=1)
PY

echo "START $RUN_ID seed$SEED at $START pid=$$ pgid=$(ps -o pgid= -p $$ | tr -d ' ') sha=$SHA dir=$DIR"
cd "$WT" || exit 5
LSU_GEM5_BIN="$BIN" timeout --signal=INT --kill-after=120 "$((TIMEOUT + 900))" \
  python3 "$WT/tools/lsu_campaign.py" \
  --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir "$DIR" --cells "$RUN_ID" --phase trial --seed-start "$SEED" \
  --max-seeds-per-cell 1 --max-parallel 1 --timeout "$TIMEOUT" >>"$LOG" 2>&1
RC=$?
END=$(date -Iseconds)
echo "$RC" > "$DIR/.exit_code"
# Pass values as argv (not env): END/RC are shell-local and were never exported,
# which caused the historical `KeyError: 'END'` and left manifest at RUNNING.
python3 - "$DIR/manifest.json" "$END" "$RC" <<'PY'
import json, sys
p, end, rc = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = json.load(open(p))
d.update({"end_time": end, "exit_code": rc,
          "status": "FINISHED" if rc == 0 else "FAILED"})
json.dump(d, open(p, "w"), indent=1)
PY
if [ $? -ne 0 ]; then
  echo "ERROR: manifest finalize failed for $DIR (see stderr); .done NOT written" >&2
  exit 6
fi
touch "$DIR/.done"
echo "END $RUN_ID seed$SEED at $END rc=$RC"
