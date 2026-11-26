#!/usr/bin/env bash
# Run the 75 formal Fault conditions from a timing plan.
# usage: run_faults.sh [PLAN]
# PLAN defaults to $RUNS/timing_plan.tsv (produced by compute_timing_plan.py).
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_require_gem5
plan=${1:-$TIMING_PLAN}
if [ ! -f "$plan" ]; then
    echo "ERROR: timing plan not found: $plan" >&2
    echo "Run scripts/prescan/run_prescan.sh then scripts/prescan/compute_timing_plan.py" >&2
    exit 2
fi

rfwb_clean_samples 'RFWB-*'
rfwb_index_init

runs=0
failed=0
while IFS=$'\t' read -r model ctx n t1 t2 t3 s1 s2 s3 status id1 id2 id3 scan; do
    [ "$model" = "model" ] && continue
    [ -n "$model" ] || continue
    if [ "$status" != "PASS" ]; then
        echo "SKIP $model $ctx status=$status" >&2
        failed=$((failed+1))
        continue
    fi
    for pair in "T01:$t1:$s1:$id1" "T02:$t2:$s2:$id2" "T03:$t3:$s3:$id3"; do
        tim=${pair%%:*}; rest=${pair#*:}
        ord=${rest%%:*}; rest=${rest#*:}
        tseq=${rest%%:*}; sid=${rest##*:}
        tseq_arg=0
        [ "$model" = "M005" ] && tseq_arg=$tseq
        echo "FAULT $sid (${model} ${ctx} ${tim}) ordinal=$ord target_seq=$tseq_arg"
        if ! "$RFWB_ROOT/scripts/experiment/run_one.sh" \
             "$model" "$ctx" fault "$ord" "$sid" "$tseq_arg"; then
            failed=$((failed+1))
        fi
        runs=$((runs+1))
    done
done < <(tail -n +2 "$plan")

echo "fault runs: $runs/75; failed: $failed"
if [ "$runs" -ne 75 ] || [ "$failed" -ne 0 ]; then
    exit 1
fi
