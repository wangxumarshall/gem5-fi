#!/usr/bin/env bash
# sve_sme_fi_diversity.sh — Task 8 diversity campaign (J3').
#
# Question: does the PR #237 seed-randomized input (random mode) widen the
# DETECTION SURFACE over the fixed-formula input (fixed mode) under the
# same injector family?
#
# Design (confound-controlled vs the Task 7 pilot):
#   - ALIGNED TRIGGER WINDOW: first_clock = 50% of each (kernel, mode)
#     baseline's total cycles, measured at runtime from the baseline run's
#     stats (Task 7 showed fixed 932k vs random 2146k cycles for
#     fpu_special — a shared absolute window lands in different code
#     sections, which confounds the fixed-vs-random comparison).
#   - Per-seed baselines (random data differs per seed).
#   - n seeds per cell; rng_seed varies the injection site each run.
# J3' (preregistered): exists an injector config C with fixed = Masked/
#   Escape but random (>=5-seed union) = Detected. Not met => report
#   honestly (input pattern does not change the detection surface in this
#   injection space).
# Usage: bash tools/sve_sme_fi_diversity.sh [N_SEEDS]
set -u
cd "$(dirname "$0")/.."
source ~/gem5-deps/env.sh
G5=CHAOS/gem5/build/ARM/gem5.opt
CFG=configs/se/arm_chaos.py
N=${1:-10}
OUTCSV=fi_research/sve_sme_diversity_results.csv
mkdir -p fi_research /tmp/sve_sme_div
echo "kernel,injector,mode,seed,classification,faults_injected,first_clock,total_cycles" > "$OUTCSV"

total_cycles() { # outdir -> cycles
    grep -oE "numCycles +[0-9]+" "$1/stats.txt" 2>/dev/null | grep -oE "[0-9]+$"
}

run_case() { # kernel injector mode seed firstclock
    local kernel=$1 injector=$2 mode=$3 seed=$4 fc=$5
    local od="/tmp/sve_sme_div/${kernel}_${injector}_${mode}_${seed}"
    local base out cs cls finj fails tc
    base=$(timeout 900 "$G5" --quiet --outdir="$od-base" "$CFG" --cpu O3 \
           --cmd "workloads/sdcshield/$kernel" --sve_vl 4 --sme_vl 4 \
           --workload_args "$mode $seed" 2>/dev/null | \
           grep -E '^[0-9a-f]{16}$' | tail -1)
    tc=$(total_cycles "$od-base")
    if [ -z "$base" ] || [ -z "$tc" ]; then
        echo "$kernel,$injector,$mode,$seed,BASELINE_HANG,0,$fc," >> "$OUTCSV"
        return
    fi
    out=$(timeout 900 "$G5" --quiet --outdir="$od-inj" "$CFG" --cpu O3 \
          --cmd "workloads/sdcshield/$kernel" --sve_vl 4 --sme_vl 4 \
          --workload_args "$mode $seed" \
          --chaos_fpu --fpu_bit_segment mantissa \
          --rng_seed $((seed * 7919 + 41)) --first_clock "$fc" 2>/dev/null)
    cs=$(echo "$out" | grep -E '^[0-9a-f]{16}$' | tail -1)
    finj=$(grep -oE 'numFaultsInjected +[0-9]+' "$od-inj/stats.txt" 2>/dev/null \
           | grep -oE '[0-9]+$'); finj=${finj:-0}
    fails=$(echo "$out" | grep -oE 'SDCSHIELD_FAILS=[0-9]+' | cut -d= -f2)
    if [ -z "$cs" ]; then cls=Hang
    elif [ "${fails:-0}" != "0" ]; then cls=Detected
    elif [ "$cs" != "$base" ]; then cls=Detected
    elif [ "$finj" -eq 0 ]; then cls=Inactive
    else cls=Masked
    fi
    echo "$kernel,$injector,$mode,$seed,$cls,$finj,$fc,$tc" >> "$OUTCSV"
    echo "  $kernel/$injector/$mode/$seed -> $cls (faults=$finj fc=$fc tc=$tc)"
}

# Focus cells: the two compute-dense kernels with the injector that showed
# detections in Task 7 (fpumant). physvec is kept as an all-Masked control.
for kernel in fpu_special_sve_dual stencil_axis_dual; do
    for mode in fixed random; do
        # measure this cell's cycle count once (seed 1 baseline), then
        # align every seed's window to 50% of it
        probe=/tmp/sve_sme_div/${kernel}_probe_${mode}
        timeout 900 "$G5" --quiet --outdir="$probe" "$CFG" --cpu O3 \
            --cmd "workloads/sdcshield/$kernel" --sve_vl 4 --sme_vl 4 \
            --workload_args "$mode 1" >/dev/null 2>&1
        tc=$(total_cycles "$probe")
        fc=$((tc / 2))
        echo "$kernel/$mode: total=$tc cycles, aligned window=$fc"
        for seed in $(seq 1 "$N"); do
            run_case "$kernel" fpumant "$mode" "$seed" "$fc"
        done
    done
done

echo "=== summary (Detected / total per cell) ==="
awk -F, 'NR>1 && $5!="BASELINE_HANG" {d[$1"/"$2"/"$3"/"$5]++} END {
    for (x in d) print x, d[x]}' "$OUTCSV" | sort
echo "CSV: $OUTCSV"
