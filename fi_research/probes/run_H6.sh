#!/bin/bash
# H6: D1 vs D2 谱可分性 (single/multi-defect arbiter, sim-side proxy)
# 2x2 design: {D1 on/off} x {D2 on/off}, measure {crash, SDC, benign}
# Falsifiable: if D1-only and D2-only spectra indistinguishable -> single-defect
set -e
GEM5=/home/sdc/vmcore/gem5-fi/CHAOS/gem5/build/ARM/gem5.opt
PROBE=/home/sdc/vmcore/gem5-fi/fi_research/probes/ptrskew_kernel
CFG=/home/sdc/vmcore/gem5-fi/fi_research/probes/o3_chaos_smoke.py
CPUS=$(cat /tmp/cpus.txt)
mkdir -p /tmp/h6
run() {
  local tag=$1; shift
  local out=/tmp/h6/$tag
  timeout 200 taskset -c "$CPUS" "$GEM5" -d "$out" "$CFG" \
    --binary "$PROBE" --iters 500 --no-fi --seed 42 --max-faults 50 \
    --first-clock 2000 "$@" 2>&1 | grep -E 'fails|Page table fault|Exiting|panic' | head -3
  echo "  [stats] $(grep -E 'numStructuralByteLaneSkew|numAddrFaults|numFaultsInjected' $out/stats.txt 2>/dev/null | tr '\n' ' ')"
}
echo "=== H6: D1 vs D2 spectrum separability ==="
echo "[1/4] baseline (no FI):"
run baseline
echo "[2/4] D1-only (byte_lane_skew prob=0.05):"
run D1_only --lsq-fwd-prob 0.05 --lsq-structural byte_lane_skew --lsq-skew 1
echo "[3/4] D2-only (addr byte7-zero prob=0.05):"
run D2_only --addr-prob 0.05 --addr-byte 7
echo "[4/4] D1+D2 (both prob=0.05):"
run D1D2 --lsq-fwd-prob 0.05 --lsq-structural byte_lane_skew --lsq-skew 1 --addr-prob 0.05 --addr-byte 7
