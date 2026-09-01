#!/bin/bash
# H7: PTW ECC vs spurious rate
# {ptwEcc on/off} x measure spurious-fault count (numSpuriousFaults stat)
# Falsifiable: ECC-on -> spurious~0; ECC-off -> spurious>0
#
# HONEST REPRODUCIBILITY NOTE (REVIEW_v1 finding): this script runs the SE-mode
# config (o3_chaos_smoke.py). In SE mode the D3 hook never fires (translateMmuOff
# bypasses the page-table walker), so EVERY arm reports numFaultsInjected=0.
# This script therefore reproduces the SE-mode NULL (§5.4), NOT the FS-mode
# 5-seed ECC-on/off contrast table in the paper. The FS contrast table was
# produced by hand-running o3_chaos_fs.py (FS mode) across 5 seeds x 2 arms;
# there is no automated FS script for it (FS single-boot to bash is 1-2h, 5 seeds
# x 2 arms is not feasible in one shot). To reproduce the FS table, run
# o3_chaos_fs.py with --ptw-prob <p> --conditional-valid-bit --ptw-ecc (on/off)
# across seeds 0..4; see paper §5.4 and FI_DESIGN_SUPPLEMENT §7.
#
# Reproducibility note (adversarial-review fix): resolves paths relative to
# itself and sources ~/gem5-deps/env.sh for LD_LIBRARY_PATH (gem5.opt has no
# rpath, so libprotobuf/libabsl must be on the link path to run).
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
GEM5="$REPO/CHAOS/gem5/build/ARM/gem5.opt"
PROBE="$HERE/ptrskew_kernel"
CFG="$HERE/o3_chaos_smoke.py"
[ -f "$HOME/gem5-deps/env.sh" ] && source "$HOME/gem5-deps/env.sh"
CPUS="$(cat /tmp/cpus.txt 2>/dev/null || nproc)"
mkdir -p /tmp/h7
run() {
  local tag=$1; shift
  local out=/tmp/h7/$tag
  timeout 200 taskset -c "$CPUS" "$GEM5" -d "$out" "$CFG" \
    --binary "$PROBE" --iters 1000 --no-fi --seed 7 --max-faults 200 \
    --first-clock 2000 "$@" 2>&1 | grep -E 'fails|Page table fault|Exiting|panic' | head -3
  echo "  [stats] $(grep -E 'numFaultsInjected|numSpuriousFaults|numBenignFlips|numHooksCalled' $out/stats.txt 2>/dev/null | tr '\n' ' ')"
}
echo "=== H7: PTW ECC vs spurious rate ==="
echo "[1/3] ECC-off, 1-bit flip:"
run ecc_off_1bit --ptw-prob 0.02 --ptw-bits 1
echo "[2/3] ECC-off, 2-bit flip (uncorrectable):"
run ecc_off_2bit --ptw-prob 0.02 --ptw-bits 2
echo "[3/3] ECC-on, 1-bit flip (should be corrected):"
run ecc_on_1bit --ptw-prob 0.02 --ptw-bits 1 --ptw-ecc
