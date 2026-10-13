#!/usr/bin/env bash
# sve_sme_fi_pilot.sh — Task 7 FI pilot (J2') for the four SVE/SME
# dual-channel kernels (plan 2026-10-13-sve-sme-fi-eval).
#
# For every (kernel x injector x mode x seed):
#   1. baseline run (no injection) — per-seed golden (random modes draw
#      different data per seed, so the baseline must be per-seed);
#   2. injected run — classify against the baseline:
#        Detected : SDCSHIELD_FAILS>0 or exit!=0 or checksum != baseline
#        Inactive : numFaultsInjected == 0 (never fired)
#        Masked   : fired (stats) but identical output
#        Hang     : gem5 timeout
# Injectors: physvec (CHAOSPhysReg, VecRegClass, 64-bit lanes) and
#            fpumant (CHAOSFPU, mantissa segment).
# NOTE: first_clock is in CYCLES (CHAOSPhysReg casts to Cycles), and the
#       kernels run ~1-3M cycles total; 300k lands inside the compute
#       section of all four.
# Usage: bash tools/sve_sme_fi_pilot.sh [N_SEEDS]
set -u
cd "$(dirname "$0")/.."
source ~/gem5-deps/env.sh
G5=CHAOS/gem5/build/ARM/gem5.opt
CFG=configs/se/arm_chaos.py
N=${1:-5}
# Per-kernel injection window (first_clock is in CYCLES; kernel totals:
# fpu_special ~932k, stencil ~207k, fmopa ~60k, za_tileview ~53k cycles —
# window at ~30-40% of each lands inside the compute section).
FIRSTCLOCK_fpu_special_sve_dual=300000
FIRSTCLOCK_stencil_axis_dual=80000
FIRSTCLOCK_sme_fmopa_dual=20000
FIRSTCLOCK_sme_za_tileview_dual=18000
OUTCSV=${OUTCSV:-fi_research/sve_sme_pilot_results.csv}
KERNELS_F=${KERNELS_F:-"fpu_special_sve_dual stencil_axis_dual sme_fmopa_dual sme_za_tileview_dual"}
mkdir -p fi_research /tmp/sve_sme_pilot
echo "kernel,injector,mode,seed,classification,faults_injected,checksum,base_checksum" > "$OUTCSV"

run_case() { # kernel injector mode seed inject_extra...
    local kernel=$1 injector=$2 mode=$3 seed=$4; shift 4
    local od="/tmp/sve_sme_pilot/${kernel}_${injector}_${mode}_${seed}"
    local base extra out bcs cs cls finj
    base=$(timeout 600 "$G5" --quiet --outdir="$od-base" "$CFG" --cpu O3 \
           --cmd "workloads/sdcshield/$kernel" --sve_vl 4 --sme_vl 4 \
           --workload_args "$mode $seed" 2>/dev/null | \
           grep -E '^[0-9a-f]{16}$' | tail -1)
    if [ -z "$base" ]; then
        echo "$kernel,$injector,$mode,$seed,BASELINE_HANG,0,," >> "$OUTCSV"
        return
    fi
    out=$(timeout 600 "$G5" --quiet --outdir="$od-inj" "$CFG" --cpu O3 \
          --cmd "workloads/sdcshield/$kernel" --sve_vl 4 --sme_vl 4 \
          --workload_args "$mode $seed" "$@" 2>/dev/null)
    cs=$(echo "$out" | grep -E '^[0-9a-f]{16}$' | tail -1)
    finj=$(grep -oE 'numFaultsInjected\s+[0-9]+' "$od-inj/stats.txt" 2>/dev/null \
           | awk '{print $2}')
    finj=${finj:-0}
    local fails=$(echo "$out" | grep -oE 'SDCSHIELD_FAILS=[0-9]+' | cut -d= -f2)
    if [ -z "$cs" ]; then cls=Hang
    elif [ "${fails:-0}" != "0" ]; then cls=Detected
    elif [ "$cs" != "$base" ]; then cls=Detected   # channel B differs => the
                                                   # corrupted state changed
                                                   # the hw output bits
    elif [ "$finj" -eq 0 ]; then cls=Inactive
    else cls=Masked
    fi
    echo "$kernel,$injector,$mode,$seed,$cls,$finj,$cs,$base" >> "$OUTCSV"
    echo "  $kernel/$injector/$mode/$seed -> $cls (faults=$finj)"
}

for kernel in $KERNELS_F; do
    fc=""
    eval fc=\$FIRSTCLOCK_${kernel}
    for mode in fixed random; do
        for seed in $(seq 1 "$N"); do
            run_case "$kernel" physvec "$mode" "$seed" \
                --chaos_phys --phys_reg_class vector --vec_lane_width 64 \
                --rng_seed $((seed * 1000 + 7)) --first_clock "$fc"
            run_case "$kernel" fpumant "$mode" "$seed" \
                --chaos_fpu --fpu_bit_segment mantissa \
                --rng_seed $((seed * 1000 + 13)) --first_clock "$fc"
        done
    done
done

echo "=== summary ==="
awk -F, 'NR>1 {k[$1"/"$2"/"$3"/"$5]++} END {for (x in k) print x, k[x]}' "$OUTCSV" | sort
echo "CSV: $OUTCSV"
