#!/usr/bin/env bash
# [LSU][MDSPEC][R6-SQPILOT] L24 pilot driver — real SE pilots for one store-family
# cell and one load-queue-family cell, each into its own outdir, via the
# OFFICIAL campaign entry point (tools/lsu_campaign.py), so propagation evidence
# (prop_evt.txt.gz) comes from the sanctioned path, not a hand-driven gem5 call.
#
# Cells (SE, non-FS — both run on the sq_forward directed carrier W5):
#   S04-F0-W5  Store Queue  (addrpath PRE hook, --agu_pre_mode s04_store_subst)
#   L01-F0-W5  Load Queue   (addrpath PRE hook, --agu_pre_mode l01_load_addr)
#
# Resource discipline (host runs ~5-6 gem5 already): --max-parallel 1, one cell
# at a time, never bulk output to /tmp.
set -u
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-sqpq
BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-tlb-hooks/CHAOS/gem5/build/ARM/gem5.opt
MATRIX=artifacts/lsu-trial/07-expanded-matrix-backfilled.csv
RUNS=/home/sdc/gem5-fi-ding/runs/lsu

run_cell () {   # $1 = cell RunID, $2 = outdir suffix
  local cell="$1" suffix="$2"
  local outroot="$RUNS/$suffix"
  echo "=== [$cell] -> $outroot @ $(date -Is) ==="
  cd "$WT" || exit 1
  LSU_GEM5_BIN="$BIN" python3 tools/lsu_campaign.py \
      --matrix "$MATRIX" \
      --outdir "$outroot" \
      --cells "$cell" \
      --phase trial --max-seeds-per-cell 1 --max-parallel 1 \
      --timeout 900 2>&1 | tee "$outroot.log"
  echo "=== [$cell] done @ $(date -Is) ==="
}

run_cell S04-F0-W5 r6_sq_S04-F0-W5
run_cell L01-F0-W5 r6_lq_L01-F0-W5
