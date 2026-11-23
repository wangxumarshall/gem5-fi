#!/bin/bash
# Run the full 180 fault + 60 control matrix from a fresh clone.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CLONE=$(cd "$HERE/.." && pwd)

export LSU_E2E_ROOT="$HERE/code"
export LSU_WORKSPACE_ROOT="$HERE"
export LSU_GEM5_ROOT="${LSU_GEM5_ROOT:-$CLONE/CHAOS/gem5}"
export LSU_INPUT_XLSX="${LSU_INPUT_XLSX:-$HERE/inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx}"

if [ ! -x "$LSU_GEM5_ROOT/build/ARM/gem5.opt" ]; then
    echo "gem5 binary not found under $LSU_GEM5_ROOT" >&2
    echo "Build it with: cd $LSU_GEM5_ROOT && scons build/ARM/gem5.opt -j\$(nproc)" >&2
    exit 2
fi

exec python3 "$HERE/code/runner/e2e_experiment.py" "$@"
