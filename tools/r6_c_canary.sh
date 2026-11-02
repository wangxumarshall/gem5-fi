#!/usr/bin/env bash
# R6-C unit canary launcher: one RunID x one seed, authoritative binary.
set -u
RUN_ID="${1:?run id}"; SEED="${2:?seed}"; TIMEOUT="${3:-43200}"
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
BIN=/home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-6db026e7
OUTROOT="${OUTROOT_OVERRIDE:-/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary}"
DIR="$OUTROOT/${RUN_ID}_s${SEED}"
LOG=/home/sdc/gem5-fi-ding-cleanup-20261029/r6c-canary-${RUN_ID}-s${SEED}.log
WANT_SHA=6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4
mkdir -p "$OUTROOT"
[ -e "$DIR/.done" ] && { echo "ALREADY DONE: $DIR"; exit 0; }
if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
  echo "REFUSED: non-fresh output dir $DIR" >&2; exit 4
fi
mkdir -p "$DIR"
SHA=$(sha256sum "$BIN" | awk '{print $1}')
[ "$SHA" = "$WANT_SHA" ] || { echo "SHA DRIFT: $SHA" >&2; exit 7; }
START=$(date -Iseconds)
export WT RUN_ID SEED BIN SHA START DIR LOG TIMEOUT
python3 - "$DIR/manifest.json" <<'PY'
import json, os, sys
p=sys.argv[1]
json.dump({
 "run_id": os.environ["RUN_ID"], "seed": int(os.environ["SEED"]),
 "binary_path": os.environ["BIN"], "binary_sha256": os.environ["SHA"],
 "binary_source_head": "43d1bb08",
 "analysis_tool_head": os.popen("git -C %s rev-parse HEAD" % os.environ["WT"]).read().strip(),
 "start_time": os.environ["START"], "launcher_pid": os.getpid(),
 "output_dir": os.environ["DIR"], "log": os.environ["LOG"],
 "wall_budget_seconds": int(os.environ["TIMEOUT"]) if "TIMEOUT" in os.environ else None,
 "status": "RUNNING",
}, open(p,"w"), indent=1)
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
