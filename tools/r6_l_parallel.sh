#!
# R6-L parallel seed queue: 14 runnable non-F6 L RunIDs x seeds 1/2/3 = 42.
# Each seed is an independent process/dir/lock; resume skips `.done`.
#
# Usage:
#   bash tools/r6_c_parallel.sh [--dry-run]
# Env:
#   R6L_MAXJOBS=8 R6L_TIMEOUT=43200 R6L_WANT_SHA=<binary sha> R6L_BIN=<path>
set -u
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-l-unit-20261103
BIN="${R6L_BIN:-/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102/CHAOS/gem5/build/ARM/gem5.opt}"
OUTROOT="${R6L_OUTROOT:-/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs}"
MAXJOBS="${R6L_MAXJOBS:-2}"
TIMEOUT="${R6L_TIMEOUT:-43200}"
RUNIDS="${R6L_RUNIDS:-L01-F0-W5,L01-F0-W12,L01-F1-W5,L01-F1-W12,L01-F2-W5,L01-F2-W12,L02-F0-W5,L02-F0-W12,L02-F2-W5,L02-F2-W12,L03-F0-W5,L03-F0-W12,L03-F4-W5,L03-F4-W12}"
STATE_DIR="${R6L_STATE_DIR:-/home/sdc/gem5-fi-ding-cleanup-20261029}"
SUMMARY="$STATE_DIR/r6l-par-summary.jsonl"
QLOG="$STATE_DIR/r6l-parallel.log"
DONE_MARK="$STATE_DIR/R6L_PARALLEL_DONE"
STOP_MARK="$STATE_DIR/R6L_PARALLEL_STOP"
mkdir -p "$OUTROOT" "$STATE_DIR"

IFS=',' read -r -a IDS <<< "$RUNIDS"
TASKS=()
# [R6-L-UNIT] Explicit seed-level task list (RUNID:SEED,...) for the
# repeat reruns: the 25 NO_INJECTION seeds only. Without it, the historical
# 14-RunID x 3-seed allocation is used. Never let a qualified seed rerun.
if [ -n "${R6L_TASKS:-}" ]; then
  IFS=',' read -r -a SPECS <<< "$R6L_TASKS"
  for spec in "${SPECS[@]}"; do
    spec="$(echo "$spec" | tr -d '[:space:]')"
    [ -z "$spec" ] && continue
    TASKS+=("${spec/:/|}")
  done
else
  for rid in "${IDS[@]}"; do
    for s in 1 2 3; do TASKS+=("$rid|$s"); done
  done
fi

if [ "${1:-}" = "--dry-run" ]; then
  declare -A seen=()
  dup=0
  for t in "${TASKS[@]}"; do
    [ -n "${seen[$t]:-}" ] && dup=$((dup+1))
    seen[$t]=1
  done
  expected=42
  [ -n "${R6L_TASKS:-}" ] && expected=${#TASKS[@]}
  echo "tasks=${#TASKS[@]} unique=${#seen[@]} dup=$dup runids=${#IDS[@]}"
  if [ "${#TASKS[@]}" -eq "$expected" ] && [ "${#seen[@]}" -eq "$expected" ] && [ "$dup" -eq 0 ]; then
    echo "ALLOCATION_OK"
    exit 0
  fi
  echo "ALLOCATION_FAIL"
  exit 1
fi

log() { echo "[$(date -Iseconds)] $*" | tee -a "$QLOG"; }
gate_ok() {
  local mem avail
  mem=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
  avail=$(df -Pk /home | awk 'NR==2{print int($4/1024/1024)}')
  if [ "${mem:-0}" -lt 12 ]; then log "GATE: MemAvailable ${mem}G < 12G"; return 1; fi
  if [ "${avail:-0}" -lt 30 ]; then log "GATE: /home ${avail}G < 30G"; return 1; fi
  if [ ! -x "$BIN" ]; then log "GATE: missing binary $BIN"; return 1; fi
  if [ -n "${R6L_WANT_SHA:-}" ]; then
    local sha; sha=$(sha256sum "$BIN" | awk '{print $1}')
    if [ "$sha" != "$R6L_WANT_SHA" ]; then log "GATE: SHA drift $sha"; return 1; fi
  fi
  return 0
}

rm -f "$DONE_MARK" "$STOP_MARK"
log "QUEUE START tasks=${#TASKS[@]} maxjobs=$MAXJOBS bin=$BIN timeout=$TIMEOUT"

declare -A RUNNING=()
declare -A PIDTASK=()
RUNNING_N=0
launch() {
  local task="$1" rid seed
  rid="${task%%|*}"; seed="${task##*|}"
  R6L_BIN="$BIN" R6L_OUTROOT="$OUTROOT" R6L_WANT_SHA="${R6L_WANT_SHA:-}" \
    "$WT/tools/r6_l_seed.sh" "$rid" "$seed" "$TIMEOUT" &
  local pid=$!
  RUNNING[$pid]=1
  PIDTASK[$pid]="$task"
  RUNNING_N=$((RUNNING_N+1))
  log "LAUNCH $rid seed$seed pid=$pid running=$RUNNING_N"
}

reap_one() {
  local pid rc task rid seed
  wait -n -p pid
  rc=$?
  task="${PIDTASK[$pid]:-unknown}"
  unset "PIDTASK[$pid]" "RUNNING[$pid]"
  RUNNING_N=$((RUNNING_N-1))
  rid="${task%%|*}"; seed="${task##*|}"
  printf '{"time":"%s","task":"%s","run_id":"%s","seed":%s,"pid":%s,"rc":%s}\n' \
    "$(date -Iseconds)" "$task" "$rid" "$seed" "$pid" "$rc" >> "$SUMMARY"
  log "REAP $rid seed$seed pid=$pid rc=$rc running=$RUNNING_N"
}

while :; do
  if [ -e "$STOP_MARK" ]; then log "STOP marker present — halting"; exit 9; fi
  progressed=0
  for task in "${TASKS[@]}"; do
    rid="${task%%|*}"; seed="${task##*|}"
    if [ -e "$OUTROOT/${rid}_s${seed}/.done" ]; then continue; fi
    if [ "$RUNNING_N" -ge "$MAXJOBS" ]; then break; fi
    # skip tasks already running
    already=0
    for p in "${!PIDTASK[@]}"; do [ "${PIDTASK[$p]}" = "$task" ] && already=1; done
    [ "$already" -eq 1 ] && continue
    if ! gate_ok; then
      log "GATE blocked before $rid seed$seed; waiting 60s"
      sleep 60
      continue 2
    fi
    launch "$task"
    progressed=1
  done

  if [ "$RUNNING_N" -eq 0 ]; then
    remaining=0
    for task in "${TASKS[@]}"; do
      rid="${task%%|*}"; seed="${task##*|}"
      [ -e "$OUTROOT/${rid}_s${seed}/.done" ] || remaining=$((remaining+1))
    done
    if [ "$remaining" -eq 0 ]; then
      log "QUEUE DONE all ${#TASKS[@]} seeds have .done"
      date -Iseconds > "$DONE_MARK"
      exit 0
    fi
    log "QUEUE idle with $remaining remaining — retrying after 60s"
    sleep 60
    continue
  fi

  reap_one
done
