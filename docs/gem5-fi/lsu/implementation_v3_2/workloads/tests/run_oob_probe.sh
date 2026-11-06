#!/usr/bin/env bash
# Rebuild and run the W6/W8 guard-page probe against original and fixed offsets.
set -uo pipefail
cd "$(dirname "$0")"
gcc -O0 -g -o oob_probe oob_probe.c || exit 2
LOG=../../logs
mkdir -p "$LOG"
for mode in store_path alignment store_path_fixed alignment_fixed; do
  ./oob_probe "$mode" > "$LOG/probe_${mode}.log" 2>&1
  rc=$?
  echo "mode=$mode exit=$rc" | tee -a "$LOG/probe_${mode}.log" >> "$LOG/probe_results.txt"
done
