#!/bin/bash
# W8.1 M2 gate — Wave B (formal) driver.
# Runs the 14 FORMAL campaigns SEQUENTIALLY, each with --jobs 8. These are
# the backfill sources (campaign_id ooo_w81_gate_*; NEVER pass the
# ooo_w81_gatecheck_* dirs to backfill_expanded_matrix.py).
# LAUNCH CONDITION: Wave A gate-check pilots all SDC=0 (M2 gate stop rule).
# Plan: docs/superpowers/plans/2026-09-25-ooo-w8-experiments.md §1
cd /home/sdc/gem5-fi || exit 1
export PYTHONHASHSEED=0

# /tmp sweeper (same as Wave A): man-* gem5 outdirs older than 20 min are
# finished runs; keep /tmp from filling over the multi-hour formal burn.
(
  while true; do
    find /tmp -maxdepth 1 -name 'man-*' -mmin +20 -exec rm -rf {} + 2>/dev/null
    sleep 300
  done
) &
SWEEPER=$!

echo "[driver] Wave B formal start: $(date -Is)  driver_pid=$$  sweeper=$SWEEPER  jobs=8"
echo "[driver] free before start: $(free -g | awk '/^Mem:/{print "used="$3" available="$7}')"
for y in \
  campaigns/ooo-w81-gate-e074.yaml \
  campaigns/ooo-w81-gate-e075_crc32.yaml \
  campaigns/ooo-w81-gate-e075_matmult-int.yaml \
  campaigns/ooo-w81-gate-e075_md5sum.yaml \
  campaigns/ooo-w81-gate-e075_minver.yaml \
  campaigns/ooo-w81-gate-e075_nbody.yaml \
  campaigns/ooo-w81-gate-e075_wikisort.yaml \
  campaigns/ooo-w81-gate-e082.yaml \
  campaigns/ooo-w81-gate-e083_crc32.yaml \
  campaigns/ooo-w81-gate-e083_matmult-int.yaml \
  campaigns/ooo-w81-gate-e083_md5sum.yaml \
  campaigns/ooo-w81-gate-e083_minver.yaml \
  campaigns/ooo-w81-gate-e083_nbody.yaml \
  campaigns/ooo-w81-gate-e083_wikisort.yaml \
; do
  echo "[driver] === $(date -Is) START $y ==="
  python3 tools/campaign.py "$y" --jobs 8
  rc=$?
  echo "[driver] === $(date -Is) END   $y rc=$rc ==="
  if [ $rc -ne 0 ]; then
    echo "[driver] CAMPAIGN FAILED rc=$rc: $y — continuing to next (recorded honestly)"
  fi
done
kill $SWEEPER 2>/dev/null
echo "[driver] Wave B formal DONE: $(date -Is)"
