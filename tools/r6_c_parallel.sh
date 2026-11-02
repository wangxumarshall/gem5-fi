#!/usr/bin/env bash
# R6-C parallel seed queue: 31 runnable non-F6 C RunIDs x seeds 1/2/3 = 93.
# Each seed is an independent process/dir/lock; resume skips `.done`.
#
# Usage:
#   bash tools/r6_c_parallel.sh [--dry-run]
# Env:
#   R6C_MAXJOBS=8 R6C_TIMEOUT=43200 R6C_WANT_SHA=<binary sha> R6C_BIN=<path>
set -u
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
BIN="${R6C_BIN:-$WT/CHAOS/gem5/build/ARM/gem5.opt}"
OUTROOT="${R6C_OUTROOT:-/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/runs}"
MAXJOBS="${R6C_MAXJOBS:-8}"
TIMEOUT="${R6C_TIMEOUT:-43200}"
RUNIDS="${R6C_RUNIDS:-C01-F0-W6,C01-F1-W6,C01-F2-W6,C02-F0-W6,C02-F2-W6,C03-F5-W6,C03-F5-W10,C04-F0-W6,C04-F1-W6,C04-F2-W6,C05-F0-W6,C05-F2-W6,C06-F0-W6,C06-F2-W6,C06-F5-W6,C07-F0-W6,C07-F2-W6,C07-F5-W6,C08-F0-W6,C08-F2-W6,C08-F5-W6,C09-F0-W6,C09-F0-W10,C09-F2-W6,C09-F2-W10,C10-F0-W6,C10-F0-W10,C10-F3-W6,C10-F3-W10,C10-F5-W6,C10-F5-W10}"
STATE_DIR="${R6C_STATE_DIR:-/home/sdc/gem5-fi-ding-cleanup-20261029}"
SUMMARY="$STATE_DIR/r6c-par-summary.jsonl"
QLOG="$STATE_DIR/r6c-parallel.log"
DONE_MARK="$STATE_DIR/R6C_PARALLEL_DONE"
STOP_MARK="$STATE_DIR/R6C_PARALLEL_STOP"
mkdir -p "$OUTROOT" "$STATE_DIR"

IFS=',' read -r -a IDS <<< "$RUNIDS"
TASKS=()
for rid in "${IDS[@]}"; do
  for s in 1 2 3; do TASKS+=("$rid|$s"); done
done

if [ "${1:-}" = "--dry-run" ]; then
  declare -A seen=()
  dup=0
  for t in "${TASKS[@]}"; do
    [ -n "${seen[$t]:-}" ] && dup=$((dup+1))
    seen[$t]=1
  done
  echo "tasks=${#TASKS[@]} unique=${#seen[@]} dup=$dup runids=${#IDS[@]}"
  if [ "${#TASKS[@]}" -eq 93 ] && [ "${#seen[@]}" -eq 93 ] && [ "$dup" -eq 0 ]; then
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
  if [ -n "${R6C_WANT_SHA:-}" ]; then
    local sha; sha=$(sha256sum "$BIN" | awk '{print $1}')
    if [ "$sha" != "$R6C_WANT_SHA" ]; then log "GATE: SHA drift $sha"; return 1; fi
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
  R6C_BIN="$BIN" R6C_OUTROOT="$OUTROOT" R6C_WANT_SHA="${R6C_WANT_SHA:-}" \
    "$WT/tools/r6_c_seed.sh" "$rid" "$seed" "$TIMEOUT" &
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
