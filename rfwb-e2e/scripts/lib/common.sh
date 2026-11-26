#!/usr/bin/env bash
# Shared path resolution for the RF/WB reproduction scripts.
# All paths are derived from this file's location; nothing is absolute.
set -euo pipefail

rfwb_locate() {
    local here
    here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    RFWB_ROOT=${RFWB_ROOT:-$(cd "$here/../.." && pwd)}
    RUNS=${RUNS:-$RFWB_ROOT/runs}
    GOLDEN_DIR=${GOLDEN_DIR:-$RFWB_ROOT/golden}
    TARGETS=${TARGETS:-$RFWB_ROOT/configs/targets.tsv}
    TIMING_PLAN=${TIMING_PLAN:-$RUNS/timing_plan.tsv}
    RFWB_TIMEOUT=${RFWB_TIMEOUT:-120}

    if [ -n "${GEM5_ROOT:-}" ]; then
        :
    elif [ -f "$RFWB_ROOT/../CHAOS/gem5/src/cpu/o3/rfwb.cc" ]; then
        # Release-branch layout: the project is a subdirectory of gem5-fi.
        GEM5_ROOT=$(cd "$RFWB_ROOT/.." && pwd)
    elif [ -f "$RFWB_ROOT/../gem5-fi/CHAOS/gem5/src/cpu/o3/rfwb.cc" ]; then
        # Standalone layout: gem5-fi checked out next to this project.
        GEM5_ROOT=$(cd "$RFWB_ROOT/../gem5-fi" && pwd)
    else
        GEM5_ROOT=""
    fi

    if [ -n "$GEM5_ROOT" ]; then
        if [ -d "$GEM5_ROOT/CHAOS/gem5/src" ]; then
            GEM5_SRC="$GEM5_ROOT/CHAOS/gem5"
        elif [ -d "$GEM5_ROOT/src/cpu/o3" ]; then
            GEM5_SRC="$GEM5_ROOT"
        else
            GEM5_SRC="$GEM5_ROOT"
        fi
        GEM5_CONFIG=${GEM5_CONFIG:-$GEM5_ROOT/configs/se/ooo_proxy.py}
        GEM5_BIN=${GEM5_BIN:-$GEM5_SRC/build/ARM/gem5.opt}
    fi
}

rfwb_require_gem5() {
    rfwb_locate
    if [ -z "${GEM5_ROOT:-}" ]; then
        cat >&2 <<'EOF'
ERROR: gem5-fi source tree not found.
Set GEM5_ROOT to the root of the gem5-fi checkout (the branch contains CHAOS/gem5):
  export GEM5_ROOT=/path/to/gem5-fi
Or place it next to this project as ../gem5-fi.
EOF
        exit 2
    fi
    if [ ! -f "$GEM5_SRC/src/cpu/o3/rfwb.cc" ]; then
        echo "ERROR: $GEM5_SRC/src/cpu/o3/rfwb.cc missing; apply src/RF_WB_Source_Injection_Final.patch to baseline 2f4e00b4." >&2
        exit 2
    fi
    if [ ! -f "$GEM5_CONFIG" ]; then
        echo "ERROR: gem5 config not found: $GEM5_CONFIG" >&2
        exit 2
    fi
    if [ ! -x "$GEM5_BIN" ]; then
        echo "ERROR: gem5 binary not found/executable: $GEM5_BIN" >&2
        echo "Build it first: scripts/build/build_gem5.sh" >&2
        exit 2
    fi
}

rfwb_require_tools() {
    local t
    for t in awk sha256sum timeout python3; do
        command -v "$t" >/dev/null 2>&1 || { echo "ERROR: required tool missing: $t" >&2; exit 2; }
    done
}

rfwb_index_init() {
    mkdir -p "$RUNS" "$RUNS/traces"
    if [ ! -f "$RUNS/index.tsv" ]; then
        printf 'sample\tmodel\tcontext\tmode\tordinal\ttarget_seq\trc\tduration_s\n' > "$RUNS/index.tsv"
    fi
}

rfwb_clean_samples() {
    local pattern=$1
    mkdir -p "$RUNS/samples" "$RUNS/traces"
    if compgen -G "$RUNS/samples/$pattern" >/dev/null 2>&1; then
        if [ "${RFWB_FORCE:-0}" != "1" ]; then
            echo "ERROR: existing samples match $RUNS/samples/$pattern; set RFWB_FORCE=1 to replace them." >&2
            exit 2
        fi
        find "$RUNS/samples" -maxdepth 1 -name "$pattern" -exec rm -rf {} +
    fi
    rm -f "$RUNS/traces"/$pattern.csv
}
