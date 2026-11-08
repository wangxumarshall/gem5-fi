#!/bin/sh
# Run one FW05 pilot from the archive binary. Usage:
#   GEM5_ROOT=/path/to/repo ./run_pilot.sh <outdir> [seed] [event_ordinal]
# ROOT defaults to the git top-level containing this archive; set GEM5_ROOT
# when the archive is copied outside the repository.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT="${GEM5_ROOT:-$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || true)}"
if [ -z "$ROOT" ]; then
    echo "run_pilot.sh: cannot locate the repository; set GEM5_ROOT" >&2
    exit 2
fi
GEM5="$ROOT/build/ARM/gem5.opt"
CONFIG="$ROOT/configs/se/lsu_proxy.py"
BIN="$HERE/bin/fw05_forward"
OUT="${1:?outdir}"
SEED="${2:-1025137124}"
ORD="${3:-1}"
for f in "$GEM5" "$CONFIG" "$BIN"; do
    [ -e "$f" ] || { echo "run_pilot.sh: missing $f" >&2; exit 2; }
done
mkdir -p "$OUT"
"$GEM5" --outdir="$OUT" "$CONFIG" \
  --cmd="$BIN" \
  --cpu O3 --variant B0 --probability=1.0 --chaos_propagation \
  --prop_trace_file prop_trace.csv.gz --chaos_lsqfwd \
  --lsq_struct_mode fw05_older_src --max_faults 1 \
  --rng_seed "$SEED" --lsqfwd_event_ordinal "$ORD"
