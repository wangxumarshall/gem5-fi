#!/bin/sh
# Run one FW05 pilot from the archive binary. Usage:
#   ./run_pilot.sh <outdir> [seed] [event_ordinal]
# Defaults: seed 1025137124 (R01), ordinal 1.
set -e
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
OUT="${1:?outdir}"
SEED="${2:-1025137124}"
ORD="${3:-1}"
mkdir -p "$OUT"
"$ROOT/build/ARM/gem5.opt" --outdir="$OUT" \
  "$ROOT/configs/se/lsu_proxy.py" \
  --cmd="$ROOT/docs/gem5-fi/lsu/implementation_v3_2/workloads/fw05_forward" \
  --cpu O3 --variant B0 --probability=1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_lsqfwd \
  --lsq_struct_mode fw05_older_src --max_faults 1 \
  --rng_seed "$SEED" --lsqfwd_event_ordinal "$ORD"
