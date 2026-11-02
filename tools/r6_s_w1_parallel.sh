#!/usr/bin/env bash
# R6-S W1 parallel queue (<=MAXJOBS gem5) for the remaining W1 RunIDs.
# Gated on: canary PASS on the new binary, no PAUSE flag, MemAvailable >=12 GiB,
# /home available >=30 GiB, unchanged binary SHA, no swap collapse.
#
# Usage: r6_s_w1_parallel.sh [--dry-run]
#
# 2026-11-02 fixes:
#   1. `declare -A RUNNING` + `set -u` made `${#RUNNING[@]}` abort on the empty
#      array under bash 5.2.15 ("RUNNING: 未绑定的变量") before any worker
#      started. The array is now initialised (`RUNNING=()`), and an explicit
#      RUNNING_N counter is used for the slot check.
#   2. Workers reaped while the queue was at MAXJOBS were unset without being
#      graded, so summary records were silently lost for every seed that did
#      not finish in the final wave. Reaping now grades immediately.
#   3. S01-F1-W1 seed1 is the canary run (same RunID/seed on the same binary);
#      it is graded from its canary directory and never re-run.
#
# All paths are overridable (R6S_W1_*) so the scheduling logic can be exercised
# against a fake launcher without touching the real experiment directories.
set -u
BIN=${R6S_W1_BIN:-/home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-6db026e7}
SHA_EXPECT=${R6S_W1_SHA:-6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4}
WT=${R6S_W1_WT:-/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-w1-continuation-20261101}
LAUNCH=${R6S_W1_LAUNCH:-$WT/tools/r6_s_w1_par_seed.sh}
OUTROOT=${R6S_W1_OUTROOT:-/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2/w1e}
CENSUS=${R6S_W1_CENSUS:-/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2/w1census}
CANARY=${R6S_W1_CANARY:-/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2/w1canary/S01-F1-W1_s1}
PRESEED=${R6S_W1_PRESEED-S01-F1-W1#1}
PAUSE=${R6S_W1_PAUSE:-/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_PAUSE}
STATE=${R6S_W1_STATE:-/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_PARALLEL_STATE.json}
SUMMARY=${R6S_W1_SUMMARY:-/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1-par-summary.jsonl}
QLOCK=${R6S_W1_QLOCK:-/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-w1-parallel.lock}
DONE_MARK=${R6S_W1_DONE_MARK:-/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_PARALLEL_DONE}
MAXJOBS=${MAXJOBS:-8}
MEM_MIN_KB=$((12*1024*1024))
HOME_MIN_KB=$((30*1024*1024))
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

TASKS=(
  "S01-F0-W1 1" "S01-F0-W1 2" "S01-F0-W1 3"
  "S01-F1-W1 1" "S01-F1-W1 2" "S01-F1-W1 3"
  "S01-F2-W1 1" "S01-F2-W1 2" "S01-F2-W1 3"
  "S02-F0-W1 1" "S02-F0-W1 2" "S02-F0-W1 3"
  "S02-F2-W1 1" "S02-F2-W1 2" "S02-F2-W1 3"
)
# Test hook: "RID:SEED,RID:SEED,..." replaces the production task list.
if [ -n "${R6S_W1_TASKS:-}" ]; then
  TASKS=()
  IFS=',' read -r -a _pairs <<<"$R6S_W1_TASKS"
  for _p in "${_pairs[@]}"; do TASKS+=("${_p/:/ }"); done
  unset _pairs _p
fi
TOTAL_EXPECTED=${R6S_W1_TOTAL_EXPECTED:-15}

state_write() {
  python3 - "$STATE" "$1" "$2" <<'PY'
import json, sys, datetime
p, phase, extra = sys.argv[1], sys.argv[2], sys.argv[3]
d = {
  "updated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
  "phase": phase,
  "extra": json.loads(extra),
}
tmp = p + ".tmp"
json.dump(d, open(tmp, "w"), indent=1, ensure_ascii=False)
import os; os.replace(tmp, p)
PY
}

# ---- dry-run: prove allocation has no duplicates / omissions ----
if [ "$DRY" = "1" ]; then
  echo "DRY-RUN allocation (${#TASKS[@]} tasks, preseed=${PRESEED:-none})"
  python3 - "${TASKS[@]}" <<'PY'
import sys
tasks = [tuple(x.split()) for x in sys.argv[1:]]
seen = {}
for rid, seed in tasks:
    seen.setdefault(rid, []).append(int(seed))
ok = True
for rid in sorted(seen):
    seeds = sorted(seen[rid])
    if seeds != [1,2,3]:
        ok = False
    print(f"{rid}: seeds={seeds}")
dups = [(rid,s) for rid,s in tasks if tasks.count((rid,s)) > 1]
print("total", len(tasks), "unique", len(set(tasks)), "dups", sorted(set(dups)))
print("ALLOCATION_OK" if ok and not dups and len(tasks)==15 else "ALLOCATION_BAD")
sys.exit(0 if ok and not dups and len(tasks)==15 else 1)
PY
  exit $?
fi

# ---- live preconditions ----
exec 8>"$QLOCK"
flock -n 8 || { echo "REFUSED: another parallel queue holds $QLOCK" >&2; exit 3; }

SHA_BEFORE=$(sha256sum "$BIN" | awk '{print $1}')
[ "$SHA_BEFORE" = "$SHA_EXPECT" ] || { echo "REFUSED: binary SHA $SHA_BEFORE" >&2; exit 4; }

canary_check() {
python3 - "$CANARY" "$SHA_EXPECT" <<'PY'
import json, os, sys
d, sha = sys.argv[1], sys.argv[2]
m = json.load(open(os.path.join(d, "manifest.json")))
c = m.get("checks") or {}
req = {
  "prop_evt_eof": c.get("prop_evt.txt.gz_eof") is True,
  "prop_trace_eof": c.get("prop_trace.csv.gz_eof") is True,
  "stats_nonzero": isinstance(c.get("stats_size"), int) and c.get("stats_size") > 0,
  "admission": c.get("admission_status") == "ADMITTED",
  "admitted": c.get("admitted") is True,
  "certified": c.get("certified") is True,
  "not_truncated": c.get("truncated") is False,
  "violations_empty": c.get("violations") == [],
  "binary": m.get("binary_sha256") == sha,
}
print(json.dumps({"pass": all(req.values()), "checks": req}, sort_keys=True))
sys.exit(0 if all(req.values()) else 1)
PY
}

# Canary must PASS on the new binary before any worker starts.
CANARY_VERDICT=$(canary_check) || { echo "REFUSED: canary has not passed: $CANARY_VERDICT" >&2; exit 10; }
echo "CANARY PASS $CANARY_VERDICT"

# SKIP_PAUSE=1 lets the supervisor start this queue while the PAUSE flag still
# blocks the LEGACY serial wrapper (we must not let it start seed3 on the old
# binary). The flag is removed only after legacy seed2 ends.
if [ "${SKIP_PAUSE:-0}" != "1" ]; then
  while [ -e "$PAUSE" ]; do sleep 30; done
fi

SPAN_JSON=$(python3 - "$CENSUS" <<'PY'
import json, os, sys
root = sys.argv[1]; out = {}
for key, model in (("S01:mibench/bin/w1_all","S01"), ("S02:mibench/bin/w1_all","S02")):
    m = json.load(open(os.path.join(root, f"{model}-w1", "manifest.json")))
    n = m.get("eligible_span")
    if not isinstance(n, int) or n <= 0:
        raise SystemExit(f"bad span {model} {n!r}")
    out[key] = n
print(json.dumps(out, separators=(",", ":")))
PY
) || { echo "ABORT: spans unavailable" >&2; exit 5; }
echo "SPAN_EXTRA=$SPAN_JSON"
export LSU_LSQFWD_F0_SPAN_EXTRA="$SPAN_JSON"

SWAP_BASE_KB=$(awk '/SwapFree/{print $2}' /proc/meminfo)
gate() {
  local mem home sha swap
  [ "${R6S_W1_SKIP_GATE:-0}" = "1" ] && return 0
  mem=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  home=$(df -Pk /home | awk 'NR==2{print $4}')
  sha=$(sha256sum "$BIN" | awk '{print $1}')
  swap=$(awk '/SwapFree/{print $2}' /proc/meminfo)
  if [ "$sha" != "$SHA_EXPECT" ]; then echo "GATE STOP: binary SHA drift $sha" >&2; return 2; fi
  if [ "$mem" -lt "$MEM_MIN_KB" ]; then echo "GATE WAIT: MemAvailable ${mem}KiB < 12GiB" >&2; return 1; fi
  if [ "$home" -lt "$HOME_MIN_KB" ]; then echo "GATE WAIT: /home avail ${home}KiB < 30GiB" >&2; return 1; fi
  if [ $((SWAP_BASE_KB - swap)) -gt $((2*1024*1024)) ]; then
    echo "GATE STOP: swap free dropped >2GiB (${SWAP_BASE_KB}->${swap})" >&2; return 2
  fi
  return 0
}

# grade <rid> <seed> <dir> <source> <worker_rc>
grade() {
  local rid="$1" seed="$2" dir="$3" source="$4" rc="${5:-}"
  python3 - "$dir" "$rid" "$seed" "$SUMMARY" "$source" "$rc" <<'PY'
import json, os, sys
d, rid, seed, summ, source, rc = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
rec = {"run_id": rid, "seed": int(seed), "dir": d, "source": source}
if rc != "":
    rec["worker_rc"] = int(rc)
try:
    m = json.load(open(os.path.join(d, "manifest.json")))
    rec.update({"status": m.get("status"), "exit_code": m.get("exit_code"),
                "binary_sha256": m.get("binary_sha256"),
                "analysis_tool_head": m.get("analysis_tool_head"),
                "kind": m.get("kind")})
    inner = os.path.join(d, rid)
    cr = json.load(open(os.path.join(inner, "cell_results.json")))
    rec.update({"admission_status": cr.get("admission_status"),
                "conservation": cr.get("conservation")})
    runs = cr.get("runs") or []
    if runs:
        ch = runs[0].get("chain") or {}
        rec.update({"oracle": ch.get("oracle_outcome"),
                    "terminal": ch.get("terminal"),
                    "provable_to": ch.get("provable_to"),
                    "admitted": ch.get("admitted"),
                    "certified": ch.get("certified"),
                    "truncated": ch.get("truncated")})
except Exception as e:
    rec["error"] = repr(e)
line = json.dumps(rec, ensure_ascii=False, sort_keys=True)
with open(summ, "a") as f:
    f.write(line + "\n")
print(line)
PY
}

rm -f "$DONE_MARK"
state_write "parallel-start" "{\"maxjobs\":$MAXJOBS,\"tasks\":${#TASKS[@]},\"preseed\":\"${PRESEED:-}\",\"span\":$SPAN_JSON}"
echo "PARALLEL START at $(date -Iseconds) maxjobs=$MAXJOBS preseed=${PRESEED:-none}"

declare -A RUNNING=()
RUNNING_N=0

reap_one() {
  local k="$1" pid="${RUNNING[$1]}" rc
  wait "$pid" 2>/dev/null; rc=$?
  local rid=${k%#*} seed=${k#*#}
  unset "RUNNING[$k]"
  RUNNING_N=$((RUNNING_N - 1))
  echo "DONE $rid s$seed rc=$rc at $(date -Iseconds)"
  grade "$rid" "$seed" "$OUTROOT/${rid}_s${seed}" worker "$rc" || true
}

handle_signal() {
  echo "PARALLEL INTERRUPTED $(date -Iseconds): not killing running workers" >&2
  state_write "interrupted" "{\"active\":$RUNNING_N}"
  exit 130
}
trap handle_signal INT TERM

for item in "${TASKS[@]}"; do
  set -- $item; rid="$1"; seed="$2"
  key="$rid#$seed"
  dir="$OUTROOT/${rid}_s${seed}"

  # S01-F1-W1 seed1 was produced by the canary on the same binary; never re-run.
  if [ -n "${PRESEED:-}" ] && [ "$key" = "$PRESEED" ]; then
    if [ -e "$CANARY/.done" ]; then
      echo "PRESEED $rid s$seed <- $CANARY (canary verified)"
      grade "$rid" "$seed" "$CANARY" preseed "" || true
      continue
    fi
    echo "ABORT: preseed $key has no completed canary at $CANARY" >&2
    state_write "stopped-preseed" "{}"; exit 11
  fi

  if [ -e "$dir/.done" ]; then
    echo "SKIP completed dir $dir"
    grade "$rid" "$seed" "$dir" existing "" || true
    continue
  fi

  while :; do
    # reap finished workers (grading happens at reap time, not only at the end)
    for k in "${!RUNNING[@]}"; do
      if ! kill -0 "${RUNNING[$k]}" 2>/dev/null; then
        reap_one "$k"
      fi
    done
    [ "$RUNNING_N" -lt "$MAXJOBS" ] && break
    sleep 20
  done

  while :; do
    gate; g=$?
    [ "$g" -eq 0 ] && break
    [ "$g" -eq 2 ] && { echo "PARALLEL STOP: gate hard-stop" >&2; state_write "stopped-gate" "{}"; exit 20; }
    sleep 300
  done

  BIN_OVERRIDE="$BIN" WT_OVERRIDE="$WT" LSU_LSQFWD_F0_SPAN_EXTRA="$SPAN_JSON" \
    "$LAUNCH" "$rid" "$seed" "$BIN" "$OUTROOT" 43200 &
  RUNNING["$key"]=$!
  RUNNING_N=$((RUNNING_N + 1))
  echo "LAUNCH $rid s$seed pid=${RUNNING[$key]} at $(date -Iseconds) active=$RUNNING_N"
  state_write "parallel-running" "{\"launched\":\"$key\",\"active\":$RUNNING_N}"
  sleep 2
done

for k in "${!RUNNING[@]}"; do
  reap_one "$k"
done

SHA_AFTER=$(sha256sum "$BIN" | awk '{print $1}')
[ "$SHA_AFTER" = "$SHA_EXPECT" ] || echo "ERROR: binary SHA drifted" >&2
state_write "parallel-done" "{\"sha_before\":\"$SHA_BEFORE\",\"sha_after\":\"$SHA_AFTER\"}"
touch "$DONE_MARK"
echo "PARALLEL DONE at $(date -Iseconds)"
