#!/bin/bash
# W8.1 Wave B driver #4 — 96-way (2026-09-26 third acceleration).
#
# Measured at 48 jobs: gem5 RSS 105MB uniform (4.93GB total), python stack
# 1.67GB → 96 jobs ≈ 13.5GB vs 19G available (5.5G margin), CPU 96/126.
# D28-stall throughput = jobs/600s exactly.
#   Lane 1: e082, ONE campaign @ 48 jobs — 2020 runs = 7.0h
#   Lane 2: six e083 campaigns as 3 sequential PAIRS, each campaign @ 24
#           jobs (2 concurrent) — 3 x 2.375h = 7.1h
# Wave B ETA ≈ tonight ~18:30 (was 9/27 01:30 at 48-way; 9/29 21:45
# original sequential).
#
# Restarts are deterministic (same seeds → same results); the ~35 min of
# progress in the killed 24-way campaigns is redone exactly.
#
# DONE gate identical to B3: both lanes exit AND e082 results >= 2000
# rows AND each e083 >= 334 rows → "Wave B formal DONE" appended to the
# same driver_waveB.log the periodic cron greps. Incomplete → exit 2,
# no marker.
set -u
cd /home/sdc/gem5-fi || exit 1
export PYTHONHASHSEED=0
LOG=runs/ooo_w81_gate/driver_waveB.log
say() { echo "[driverB4] $*" >> "$LOG"; }

avail=$(free -g | awk '/^Mem:/{print $7}')
if [ "${avail:-0}" -lt 14 ]; then
  say "ABORT: only ${avail}G available (< 14G for 96-way). Not launching."
  exit 1
fi

(
  while true; do
    find /tmp -maxdepth 1 -name 'man-*' -mmin +20 -exec rm -rf {} + 2>/dev/null
    sleep 300
  done
) &
SWEEPER=$!

say "=== Wave B4 (96-way: e082@48 + e083 pairs 2x24) start: $(date -Is) pid=$$ sweeper=$SWEEPER avail=${avail}G ==="

(
  python3 tools/campaign.py campaigns/ooo-w81-gate-e082.yaml --jobs 48
  say "LANE1 e082 rc=$? (rows=$(wc -l < runs/ooo_w81_gate_e082/c0000/results.jsonl 2>/dev/null || echo 0))"
) &
LANE1=$!

(
  run_pair() {
    say "LANE2 pair START: $1 + $2 ($(date -Is))"
    python3 tools/campaign.py "campaigns/ooo-w81-gate-$1.yaml" --jobs 24 &
    P1=$!
    python3 tools/campaign.py "campaigns/ooo-w81-gate-$2.yaml" --jobs 24 &
    P2=$!
    wait $P1; r1=$?
    wait $P2; r2=$?
    say "LANE2 pair END: $1 rc=$r1, $2 rc=$r2 ($(date -Is))"
    [ $r1 -ne 0 ] && say "CAMPAIGN FAILED rc=$r1: $1"
    [ $r2 -ne 0 ] && say "CAMPAIGN FAILED rc=$r2: $2"
  }
  run_pair e083_crc32       e083_matmult-int
  run_pair e083_md5sum      e083_minver
  run_pair e083_nbody       e083_wikisort
  say "LANE2 all six done."
) &
LANE2=$!

wait $LANE1 $LANE2
say "both lanes exited: $(date -Is). Verifying results completeness..."

OK=1
rows82=$(wc -l < runs/ooo_w81_gate_e082/c0000/results.jsonl 2>/dev/null || echo 0)
if [ "$rows82" -lt 2000 ]; then
  say "INCOMPLETE: e082 rows=$rows82 < 2000"
  OK=0
fi
for prog in crc32 matmult-int md5sum minver nbody wikisort; do
  r=$(wc -l < "runs/ooo_w81_gate_e083_${prog}/c0000/results.jsonl" 2>/dev/null || echo 0)
  if [ "$r" -lt 334 ]; then
    say "INCOMPLETE: e083_${prog} rows=$r < 334"
    OK=0
  fi
done

kill $SWEEPER 2>/dev/null
if [ "$OK" -eq 1 ]; then
  say "Wave B formal DONE: $(date -Is) (96-way; e082 rows=$rows82; e083x6 verified)"
else
  say "Wave B4 lanes exited but results INCOMPLETE — orchestrator attention needed; NO DONE marker."
  exit 2
fi
