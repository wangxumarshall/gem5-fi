#!/bin/bash
# W8.1 Wave B driver #2 — PARALLEL e083 lane (2026-09-26 acceleration).
#
# CONTEXT: the original driver_waveB.sh (killed 2026-09-26 09:5x after its
# e074+e075x6+e082-pilot launches) had the six e083 campaigns QUEUED behind
# e082 — pure serialization costing ~44h. Measured RSS: ~96MB per gem5
# process (8 jobs = 0.7GB total on a 29GB host) — the 8-slot cap was a
# vast overestimate for SE workloads. This driver runs the six e083
# campaigns NOW, in parallel with the orphaned e082 campaign (PID at
# launch: 863035, --jobs 8), at --jobs 16.
#
# D28-stall throughput math: every destid_bitflip run is an infinite
# dependency stall killed at the 600s WALL timeout, so throughput is
# exactly jobs/600s regardless of CPU contention: 16 jobs = 1.6 runs/min
# -> each e083 campaign (20 pilot + 334 formal) ≈ 3.7h -> six ≈ 22h.
# e082 (2000 formal @ 8 jobs) ≈ 41.7h remains the critical path:
# Wave B ETA ≈ 2026-09-28 ~01:30 (was 9/29-30 sequential).
#
# COMPLETION GATE: this driver waits for the ORPHANED e082 campaign's
# results.jsonl to reach 2000 rows before printing the
# "Wave B formal DONE" marker (the periodic cron greps this log for it).
# If the orphan dies with incomplete results, exit 2 loudly instead.
# All output APPENDS to the same driver_waveB.log (O_APPEND, no clobber).
set -u
cd /home/sdc/gem5-fi || exit 1
export PYTHONHASHSEED=0
LOG=runs/ooo_w81_gate/driver_waveB.log
E082_PID=863035   # the orphaned campaign (recorded at this driver's birth)

say() { echo "[driverB2] $*" >> "$LOG"; }

avail=$(free -g | awk '/^Mem:/{print $7}')
if [ "${avail:-0}" -lt 8 ]; then
  say "ABORT: only ${avail}G available (< 8G) — not launching."
  exit 1
fi

# /tmp sweeper (same 20-min policy).
(
  while true; do
    find /tmp -maxdepth 1 -name 'man-*' -mmin +20 -exec rm -rf {} + 2>/dev/null
    sleep 300
  done
) &
SWEEPER=$!

say "=== Wave B2 (parallel e083 lane) start: $(date -Is) pid=$$ sweeper=$SWEEPER jobs=16 avail=${avail}G ==="
say "e082 orphan campaign PID=$E082_PID continues in parallel (--jobs 8)."

FAILED=0
for y in \
  campaigns/ooo-w81-gate-e083_crc32.yaml \
  campaigns/ooo-w81-gate-e083_matmult-int.yaml \
  campaigns/ooo-w81-gate-e083_md5sum.yaml \
  campaigns/ooo-w81-gate-e083_minver.yaml \
  campaigns/ooo-w81-gate-e083_nbody.yaml \
  campaigns/ooo-w81-gate-e083_wikisort.yaml \
; do
  say "=== $(date -Is) START $y (jobs=16) ==="
  python3 tools/campaign.py "$y" --jobs 16
  rc=$?
  say "=== $(date -Is) END   $y rc=$rc ==="
  if [ $rc -ne 0 ]; then
    FAILED=$((FAILED+1))
    say "CAMPAIGN FAILED rc=$rc: $y — continuing (recorded honestly)"
  fi
done

# ---- completion gate: wait for the orphaned e082 ----
say "e083 lane done (failed=$FAILED). Waiting for orphaned e082 (PID $E082_PID) to finish..."
while true; do
  rows=$(wc -l < runs/ooo_w81_gate_e082/c0000/results.jsonl 2>/dev/null || echo 0)
  if [ "$rows" -ge 2000 ]; then
    say "e082 results.jsonl rows=$rows — complete."
    break
  fi
  if ! kill -0 "$E082_PID" 2>/dev/null && ! pgrep -f "campaign.py campaigns/ooo-w81-gate-e082" >/dev/null; then
    say "ORPHAN e082 DIED with results.jsonl rows=$rows < 2000 — orchestrator restart needed. ABORT."
    kill $SWEEPER 2>/dev/null
    exit 2
  fi
  sleep 300
done

kill $SWEEPER 2>/dev/null
say "Wave B formal DONE: $(date -Is) (e083 lane failed_campaigns=$FAILED; e082 verified 2000 rows)"
