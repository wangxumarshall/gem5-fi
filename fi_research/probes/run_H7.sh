#!/bin/bash
# H7: PTW ECC vs spurious rate
# {ptwEcc on/off} x measure spurious-fault count (numSpuriousFaults stat)
# Falsifiable: ECC-on -> spurious~0; ECC-off -> spurious>0
set -e
GEM5=/home/sdc/vmcore/gem5-fi/CHAOS/gem5/build/ARM/gem5.opt
PROBE=/home/sdc/vmcore/gem5-fi/fi_research/probes/ptrskew_kernel
CFG=/home/sdc/vmcore/gem5-fi/fi_research/probes/o3_chaos_smoke.py
CPUS=$(cat /tmp/cpus.txt)
mkdir -p /tmp/h7
run() {
  local tag=$1; shift
  local out=/tmp/h7/$tag
  timeout 200 taskset -c "$CPUS" "$GEM5" -d "$out" "$CFG" \
    --binary "$PROBE" --iters 1000 --no-fi --seed 7 --max-faults 200 \
    --first-clock 2000 "$@" 2>&1 | grep -E 'fails|Page table fault|Exiting|panic' | head -3
  echo "  [stats] $(grep -E 'numFaultsInjected|numSpuriousFaults|numBenignFlips' $out/stats.txt 2>/dev/null | tr '\n' ' ')"
}
echo "=== H7: PTW ECC vs spurious rate ==="
echo "[1/3] ECC-off, 1-bit flip:"
run ecc_off_1bit --ptw-prob 0.02 --ptw-bits 1
echo "[2/3] ECC-off, 2-bit flip (uncorrectable):"
run ecc_off_2bit --ptw-prob 0.02 --ptw-bits 2
echo "[3/3] ECC-on, 1-bit flip (should be corrected):"
run ecc_on_1bit --ptw-prob 0.02 --ptw-bits 1 --ptw-ecc
