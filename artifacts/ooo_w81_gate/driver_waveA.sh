#!/bin/bash
# W8.1 M2 gate — Wave A (gate-check) driver.
# Runs the 14 gate-check campaigns SEQUENTIALLY, each with --jobs 8.
# Purpose: complete ALL pilot batches (14 cells x F0 x 20) BEFORE any formal
# burn, so the M2 gate stop rule (any pilot SDC>0 -> kill everything) can be
# applied before Wave B starts. Wave A formal_n=1 probes are audit-only and
# are NEVER passed to tools/backfill_expanded_matrix.py.
# Plan: docs/superpowers/plans/2026-09-25-ooo-w8-experiments.md §1
cd /home/sdc/gem5-fi || exit 1
export PYTHONHASHSEED=0

# /tmp sweeper: each run leaves a /tmp/man-* gem5 outdir (~0.6MB); ~9000 runs
# would add ~5GB to /tmp (8.1GB free). A finished run's outdir is dead weight
# (runner parses faults during the run). One run lives <=630s (hang_timeout
# 600 + 30), so man-* older than 20 min is definitely complete -> safe to
# delete; active runs (incl. the parallel ctrace agent's) are never touched.
(
  while true; do
    find /tmp -maxdepth 1 -name 'man-*' -mmin +20 -exec rm -rf {} + 2>/dev/null
    sleep 300
  done
) &
SWEEPER=$!

echo "[driver] Wave A gate-check start: $(date -Is)  driver_pid=$$  sweeper=$SWEEPER  jobs=8"
echo "[driver] free before start: $(free -g | awk '/^Mem:/{print "used="$3" available="$7}')"
# Order: the 4 gate cells (E074/E075/E082/E083) each get one representative
# campaign first, then the remaining 10 program strata.
for y in \
  campaigns/ooo-w81-gatecheck-e074.yaml \
  campaigns/ooo-w81-gatecheck-e075_crc32.yaml \
  campaigns/ooo-w81-gatecheck-e082.yaml \
  campaigns/ooo-w81-gatecheck-e083_crc32.yaml \
  campaigns/ooo-w81-gatecheck-e075_matmult-int.yaml \
  campaigns/ooo-w81-gatecheck-e075_md5sum.yaml \
  campaigns/ooo-w81-gatecheck-e075_minver.yaml \
  campaigns/ooo-w81-gatecheck-e075_nbody.yaml \
  campaigns/ooo-w81-gatecheck-e075_wikisort.yaml \
  campaigns/ooo-w81-gatecheck-e083_matmult-int.yaml \
  campaigns/ooo-w81-gatecheck-e083_md5sum.yaml \
  campaigns/ooo-w81-gatecheck-e083_minver.yaml \
  campaigns/ooo-w81-gatecheck-e083_nbody.yaml \
  campaigns/ooo-w81-gatecheck-e083_wikisort.yaml \
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
echo "[driver] Wave A gate-check DONE: $(date -Is)"
