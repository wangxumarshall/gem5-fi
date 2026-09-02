#!/bin/bash
# L1D raw-vs-secded formal batch (plan §6.5 risk-reversal table, T2).
# 2 protection arms x 3 ECC-granularity (1/2/3-bit) x N reps.
# l1d_reduce Timing = 2.9s/run -> N=384, 6 cells = 2304 runs ~25min @ jobs=8.
set -u
G5="${G5:?set G5=.../CHAOS/gem5/build/ARM/gem5.opt}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/artifacts/l1d-ecc"; mkdir -p "$OUT"
N="${1:-384}"; JOBS="${2:-8}"; BLOCK="${3:-862656}"
export GEM5_OPT="$G5"

run_cell() {  # $1=protection $2=bits $3=tag
  local prot="$1"
  local bits="$2"
  local tag="$3"
  local out="$OUT/${tag}.csv"
  echo "tag,protection,bits,classification,faults" > "$out"
  # bit_indices for the granularity axis: 1-bit=[0], 2-bit=[0,1], 3-bit=[0,1,2]
  local idx="[0]"
  [ "$bits" -ge 2 ] && idx="[0,1]"
  [ "$bits" -ge 3 ] && idx="[0,1,2]"
  for ((i=0;i<N;i++)); do
    (
      manifest=$(mktemp --suffix=.yaml)
      sed -e "s/protection_model: secded/protection_model: $prot/" \
          -e "s/bit_indices: \[0\]/bit_indices: $idx/" \
          "$REPO/manifests/v2-cache-l1d-protection.yaml" > "$manifest"
      res=$(python3 "$REPO/tools/runner.py" "$manifest" \
        --binary "$REPO/workloads/directed/l1d_reduce" \
        --golden-checksum f44d2b9cd4a173cd \
        --cache-block-addr "$BLOCK" 2>&1 | grep "RESULT:" | head -1)
      cls=$(echo "$res" | grep -oE "classification=[A-Za-z]+" | cut -d= -f2)
      f=$(echo "$res" | grep -oE "faults_injected=[0-9]+" | cut -d= -f2)
      echo "$tag,$prot,$bits,${cls:-SimulatorError},${f:-0}" >> "$out"
      rm -f "$manifest"
    ) &
    while (( $(jobs -r | wc -l) >= JOBS )); do wait -n; done
  done
  wait
}

for bits in 1 2 3; do
  run_cell none    "$bits" "raw-b$bits"
  run_cell secded  "$bits" "secded-b$bits"
done
echo "batch done -> $OUT"
