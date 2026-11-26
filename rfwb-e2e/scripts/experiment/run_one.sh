#!/usr/bin/env bash
# Run exactly one RF/WB gem5 sample.
# usage: run_one.sh MODEL CONTEXT MODE ORDINAL SAMPLE [TARGET_SEQ]
#   MODE = off | count | fault
#   ORDINAL is 1-based eligible-event ordinal (0 for off/count)
#   TARGET_SEQ is used by M005 corrected timing; 0 means "use ORDINAL".
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_require_gem5

if [ "$#" -lt 5 ]; then
    echo "usage: $0 MODEL CONTEXT MODE ORDINAL SAMPLE [TARGET_SEQ]" >&2
    exit 2
fi

model=$1; ctx=$2; mode=$3; ordinal=${4:-0}; sample=$5; target_seq=${6:-0}

row=$(awk -v m="$model" -v c="$ctx" 'BEGIN{FS="\t"} $1==m && $2==c {print; exit}' "$TARGETS")
if [ -z "$row" ]; then
    echo "ERROR: no target row for $model $ctx in $TARGETS" >&2
    exit 2
fi

workload=$(printf '%s\n' "$row" | cut -f3)
prod=$(printf '%s\n' "$row" | cut -f4)
second=$(printf '%s\n' "$row" | cut -f5)
srcidx=$(printf '%s\n' "$row" | cut -f6)
byte=$(printf '%s\n' "$row" | cut -f7)

case "$sample" in
    SCAN-*) phase=scan ;;
    CTRL-*) phase=controls ;;
    RFWB-*) phase=faults ;;
    *) echo "ERROR: cannot infer phase from sample $sample" >&2; exit 2 ;;
esac

out="$RUNS/samples/$sample"
trace="$RUNS/traces/$sample.csv"

# The frozen runs used a 51-byte absolute workload path.  The guest stack
# layout (and therefore O3 timing) is sensitive to this path string, so an
# arbitrary checkout path can change M005's WB-before-Rename count.  Prefer
# the canonical project path when it already has the frozen length; otherwise
# expose the workload through a stable 51-byte symlink path under /tmp.
WL_PATH_LEN=${RFWB_WL_PATH_LEN:-51}
base_wl="$RFWB_ROOT/workloads/build/$workload"
wl_name="${workload}_${ctx}"
canonical_cmd="$RFWB_ROOT/workloads/build/$wl_name"
if [ -n "${WORKLOAD_DIR:-}" ]; then
    cmd="$WORKLOAD_DIR/$wl_name"
elif [ "$(printf '%s' "$canonical_cmd" | wc -c)" -eq "$WL_PATH_LEN" ]; then
    cmd="$canonical_cmd"
else
    wl_root=${RFWB_WL_ROOT:-/tmp}
    user_part="rfwb-wl-$(id -u)"
    dir_len=$((WL_PATH_LEN - ${#wl_root} - 2 - ${#wl_name}))
    if [ "$dir_len" -lt "${#user_part}" ]; then
        echo "ERROR: cannot build a $WL_PATH_LEN-byte workload path under $wl_root" >&2
        exit 2
    fi
    pad=$((dir_len - ${#user_part}))
    stable_dir="$wl_root/$user_part$(printf 'x%.0s' $(seq 1 "$pad"))"
    mkdir -p "$stable_dir"
    ln -sfn "$base_wl" "$stable_dir/$wl_name"
    cmd="$stable_dir/$wl_name"
    actual=$(printf '%s' "$cmd" | wc -c)
    if [ "$actual" -ne "$WL_PATH_LEN" ]; then
        echo "ERROR: stable workload path is $actual bytes, want $WL_PATH_LEN: $cmd" >&2
        exit 2
    fi
fi

if [ ! -x "$cmd" ]; then
    echo "ERROR: workload binary missing/not executable: $cmd" >&2
    exit 2
fi
if [ -e "$out" ]; then
    if [ "${RFWB_FORCE:-0}" != "1" ]; then
        echo "ERROR: output already exists: $out (set RFWB_FORCE=1 to replace)" >&2
        exit 2
    fi
    rm -rf "$out"
fi
if [ -e "$trace" ] && [ "${RFWB_FORCE:-0}" != "1" ]; then
    echo "ERROR: trace already exists: $trace (set RFWB_FORCE=1 to replace)" >&2
    exit 2
fi

rfwb_index_init
mkdir -p "$out" "$RUNS/traces"

# Reset every model knob so a caller's environment cannot leak into a sample.
export RFWB_MODEL="$model"
export RFWB_MODE="$mode"
export RFWB_ORDINAL="$ordinal"
export RFWB_TARGET_SEQ="$target_seq"
export RFWB_PRODUCER_PC="$prod"
export RFWB_MARKER_PC=0
export RFWB_CONSUMER_PC=0
export RFWB_SRC_IDX="$srcidx"
export RFWB_BIT=0
export RFWB_BYTE="$byte"
export RFWB_SAMPLE="$sample"
export RFWB_TRACE="$trace"

case "$model" in
    M001) export RFWB_MARKER_PC="$second" ;;
    M003|M005) export RFWB_CONSUMER_PC="$second" ;;
esac

start=$(date +%s)
timeout "$RFWB_TIMEOUT" "$GEM5_BIN" \
    --outdir="$out" "$GEM5_CONFIG" \
    --cmd="$cmd" --cpu O3 --maxinsts=1000000 --max_ticks=50000000 \
    >"$out/stdout.txt" 2>"$out/stderr.txt"
rc=$?
end=$(date +%s)
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$sample" "$model" "$ctx" "$mode" "$ordinal" "$target_seq" "$rc" "$((end-start))" \
    >> "$RUNS/index.tsv"
exit "$rc"
