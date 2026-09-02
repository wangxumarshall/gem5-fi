#!/bin/bash
# LSQ fault-mode matrix on fp_fwd_kernel (T4 final scope).
# 5 modes x N reps; per-rep fails parsed from stderr (fail_count oracle
# semantics: fails>0 = SDC). The 7-geometry axis was DROPPED honestly:
# fwd_7case's volatile-but-no-asm-barrier C pattern does not reach the
# store->load forwarding path under -O2 (verified: injection log 0 bytes,
# output==golden across all cases; fp_fwd_kernel with asm back-to-back
# does reach it, fails=1 anchor).
#
# Usage: bash tools/fp_fwd_matrix_batch.sh [MODES|all] [N] [JOBS]
#   MODES: comma/space list subset of {bitflip,structural,fwdsrc,stale,phase},
#          or "all" (default). Resume-safe: reps already present in a cell's
#          csv are skipped (append-only; header written only for new files).
set -u
G5="${G5:?export G5=}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/artifacts/lsq-matrix"; mkdir -p "$OUT"
MODES="${1:-all}"; N="${2:-64}"; JOBS="${3:-8}"
if [ "$MODES" = "all" ]; then MODES="bitflip structural fwdsrc stale phase"; fi
declare -A MODE_ARGS=(
  [bitflip]="--fault_type=bit_flip"
  [structural]="--lsq_structural_fault=byte_lane_skew --lsq_skew_bytes=1"
  [fwdsrc]="--lsq_source_fault=fwd_source_sub"
  [stale]="--lsq_source_fault=stale_line_replay"
  [phase]="--lsq_source_fault=phase_offset --lsq_phase_offset=2"
)
for mode in $MODES; do
  out="$OUT/fpfwd_${mode}.csv"
  if [ ! -f "$out" ]; then echo "rep,seed,fails,class" > "$out"; fi
  # resume: reps already recorded in the csv are skipped
  done_reps=$(tail -n +2 "$out" | awk -F, '{print $1}' | sort -n | tr '\n' ' ')
  echo "[$mode] resuming; already-done reps: ${done_reps:-none}"
  for ((i=0;i<N;i++)); do
    case " $done_reps " in *" $i "*) continue;; esac
    (
      seed=$((20260825 + i))
      fl=$("$G5" --quiet --outdir="$OUT/r_fp_${mode}_$i" \
        "$REPO/configs/se/arm_chaos.py" \
        --cmd "$REPO/workloads/directed/fp_fwd_kernel" --cpu=O3 \
        --chaos_lsqfwd ${MODE_ARGS[$mode]} \
        --probability=1.0 --first_clock=1000000 --max_faults=1 \
        --rng_seed=$seed 2>&1 | grep -oE "fails=[0-9]+" | head -1 | cut -d= -f2)
      if [ -z "$fl" ]; then cls=Hang; fl=-1
      elif [ "$fl" -gt 0 ]; then cls=SDC
      else cls=Masked; fi
      echo "$i,$seed,$fl,$cls" >> "$out"
    ) &
    while (( $(jobs -r | wc -l) >= JOBS )); do wait -n; done
  done
  wait
done
echo done
