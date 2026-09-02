#!/bin/bash
# LSQ forwarding geometry x fault-mode matrix (plan §5.4E, method3, T4).
# 3 geometries x 5 modes x N reps; per-rep checksum vs the geometry's
# no-injection gem5 golden (goldens.txt must exist first).
set -u
G5="${G5:?export G5=.../CHAOS/gem5/build/ARM/gem5.opt}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/artifacts/lsq-matrix"; mkdir -p "$OUT"
N="${1:-64}"; JOBS="${2:-8}"
declare -A MODE_ARGS=(
  [bitflip]="--chaos_lsqfwd --fault_type=bit_flip"
  [structural]="--chaos_lsqfwd --lsq_structural_fault=byte_lane_skew --lsq_skew_bytes=1"
  [fwdsrc]="--chaos_lsqfwd --lsq_source_fault=fwd_source_sub"
  [stale]="--chaos_lsqfwd --lsq_source_fault=stale_line_replay"
  [phase]="--chaos_lsqfwd --lsq_source_fault=phase_offset --lsq_phase_offset=2"
)
for geom in same twocand ldxr; do
  golden=$(grep "^$geom " "$OUT/goldens.txt" 2>/dev/null | awk '{print $2}')
  if [ -z "$golden" ]; then echo "MISSING golden for $geom — run goldens first" >&2; exit 1; fi
  for mode in bitflip structural fwdsrc stale phase; do
    out="$OUT/${geom}_${mode}.csv"
    echo "rep,seed,checksum,class" > "$out"
    for ((i=0;i<N;i++)); do
      (
        seed=$((20260825 + i))
        ck=$("$G5" --quiet --outdir="$OUT/run_${geom}_${mode}_$i" \
          "$REPO/configs/se/arm_chaos.py" \
          --cmd "$REPO/workloads/directed/fwd_7case_$geom" --cpu=O3 \
          ${MODE_ARGS[$mode]} \
          --probability=1.0 --first_clock=1000000 --max_faults=1 \
          --rng_seed=$seed 2>/dev/null | grep -E "^[0-9a-f]{16}$" | tail -1)
        if [ -z "$ck" ]; then cls=Hang
        elif [ "$ck" = "$golden" ]; then cls=Masked
        else cls=SDC; fi
        echo "$i,$seed,${ck:-NONE},$cls" >> "$out"
      ) &
      while (( $(jobs -r | wc -l) >= JOBS )); do wait -n; done
    done
    wait
  done
done
echo done
