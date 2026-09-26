#!/bin/bash
# W8.1 Wave B driver #3 — DUAL-LANE 24 jobs each (2026-09-26 second
# acceleration).
#
# Lane 1: e082 (2000 formal, deterministic re-run of the ~408 reps the
#          killed 8-job campaign had finished — same seeds, same results).
# Lane 2: e083 x6 (crc32 matmult-int md5sum minver nbody wikisort).
# Both lanes at --jobs 24 (measured ~96MB/gem5: 48 concurrent ≈ 5GB on a
# host with 21G available; D28-stall throughput = jobs/600s exactly, so
# 24 jobs = 2.4 runs/min per lane).
#   Lane 1 ETA: 2020/2.4 ≈ 14h -> ~2026-09-27 00:30
#   Lane 2 ETA: 6x(20+334)/2.4 ≈ 14.75h -> ~2026-09-27 01:15
# Wave B ETA ≈ 2026-09-27 ~01:30 (was 9/29 21:45 sequential; 9/27 19:30
# after the first acceleration).
#
# DONE marker: printed ONLY after BOTH lanes exit AND all seven
# results.jsonl files are row-complete (e082>=2000, each e083>=334).
# Appends to the same driver_waveB.log the periodic cron greps.
set -u
cd /home/sdc/gem5-fi || exit 1
export PYTHONHASHSEED=0
LOG=runs/ooo_w81_gate/driver_waveB.log
say() { echo "[driverB3] $*" >> "$LOG"; }

(
  while true; do
    find /tmp -maxdepth 1 -name 'man-*' -mmin +20 -exec rm -rf {} + 2>/dev/null
    sleep 300
  done
) &
SWEEPER=$!

say "=== Wave B3 (dual-lane, 24 jobs each) start: $(date -Is) pid=$$ sweeper=$SWEEPER ==="
say "free before start: $(free -g | awk '/^Mem:/{print "used="$3" available="$7}')"

(
  python3 tools/campaign.py campaigns/ooo-w81-gate-e082.yaml --jobs 24
  say "LANE1 e082 rc=$? (results rows=$(wc -l < runs/ooo_w81_gate_e082/c0000/results.jsonl 2>/dev/null || echo 0))"
) &
LANE1=$!

(
  FAILED=0
  for y in \
    campaigns/ooo-w81-gate-e083_crc32.yaml \
    campaigns/ooo-w81-gate-e083_matmult-int.yaml \
    campaigns/ooo-w81-gate-e083_md5sum.yaml \
    campaigns/ooo-w81-gate-e083_minver.yaml \
    campaigns/ooo-w81-gate-e083_nbody.yaml \
    campaigns/ooo-w81-gate-e083_wikisort.yaml \
  ; do
    say "LANE2 === $(date -Is) START $y (jobs=24) ==="
    python3 tools/campaign.py "$y" --jobs 24
    rc=$?
    [ $rc -ne 0 ] && FAILED=$((FAILED+1))
    say "LANE2 === $(date -Is) END   $y rc=$rc ==="
  done
  say "LANE2 all six done, failed=$FAILED"
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
  say "Wave B formal DONE: $(date -Is) (dual-lane 24 jobs; e082 rows=$rows82; e083x6 verified)"
else
  say "Wave B3 lanes exited but results INCOMPLETE — orchestrator attention needed; NO DONE marker."
  exit 2
fi
