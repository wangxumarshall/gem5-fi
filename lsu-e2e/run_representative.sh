#!/bin/bash
# Run one representative A01-C03-T01 fault or its paired control.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CLONE=$(cd "$HERE/.." && pwd)
GEM5="${LSU_GEM5_ROOT:-$CLONE/CHAOS/gem5}/build/ARM/gem5.opt"
CFG="$HERE/code/configs/lsu_proxy_e2e.py"
BIN="$HERE/code/workloads/bin/agu_C03"
MODE="${1:-fault}"

if [ ! -x "$GEM5" ]; then
    echo "gem5 binary not found: $GEM5" >&2
    echo "Build it with: cd $CLONE/CHAOS/gem5 && scons build/ARM/gem5.opt -j\$(nproc)" >&2
    exit 2
fi

COMMON=(--cmd="$BIN" --cpu O3 --variant B0 --probability 1.0
        --chaos_propagation --prop_replay_all --prop_trace_file prop_trace.csv.gz
        --chaos_ctrace --ctrace_file commit_trace.csv.gz
        --chaos_msnap --msnap_every 200 --msnap_file micro_snap.csv.gz
        --chaos_addrpath --agu_pre_mode a01_bit3_load --addrpath_lsu_tier F0
        --addrpath_max_faults 1 --addrpath_warmup_events 0
        --addrpath_span_events 10)

case "$MODE" in
  fault)
    OUT="$HERE/code/results/smoke/A01-C03-T01-FAULT"
    EXTRA=(--addrpath_rng_seed 771015199 --addrpath_event_ordinal 20)
    ;;
  control)
    OUT="$HERE/code/results/smoke/A01-C03-CTRL"
    EXTRA=(--addrpath_count_only)
    ;;
  *)
    echo "usage: $0 {fault|control}" >&2; exit 2;;
esac

mkdir -p "$OUT"
echo "gem5: $GEM5"
echo "out : $OUT"
"$GEM5" --outdir="$OUT" "$CFG" "${COMMON[@]}" "${EXTRA[@]}"

for f in prop_trace.csv.gz commit_trace.csv.gz micro_snap.csv.gz stdout.log; do
    if [ -e "$OUT/$f" ]; then echo "OK $OUT/$f"; else echo "MISSING $OUT/$f"; fi
done
