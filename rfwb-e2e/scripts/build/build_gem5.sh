#!/usr/bin/env bash
# Build the patched gem5.opt for the RF/WB baseline.
#
# Expected layout: $GEM5_ROOT is a gem5-fi checkout of baseline 2f4e00b4 with
# src/RF_WB_Source_Injection_Final.patch applied (the RF_WB branch already has
# it applied).  The script refuses to build an unpatched tree.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_locate

if [ -z "${GEM5_ROOT:-}" ]; then
    echo "ERROR: GEM5_ROOT not set and gem5-fi not found next to this project." >&2
    echo "  git clone -b RF_WB https://github.com/wangxumarshall/gem5-fi.git gem5-fi" >&2
    echo "  export GEM5_ROOT=\$PWD/gem5-fi" >&2
    exit 2
fi
if [ ! -f "$GEM5_SRC/src/cpu/o3/rfwb.cc" ]; then
    echo "ERROR: RF/WB patch not applied: $GEM5_SRC/src/cpu/o3/rfwb.cc is missing." >&2
    exit 2
fi
if [ ! -f "$GEM5_CONFIG" ]; then
    echo "ERROR: patched config missing: $GEM5_CONFIG" >&2
    exit 2
fi
command -v scons >/dev/null || { echo "ERROR: scons not found" >&2; exit 2; }

jobs=${JOBS:-16}
echo "building: cd $GEM5_SRC && scons -j$jobs build/ARM/gem5.opt"
cd "$GEM5_SRC"
scons -j"$jobs" build/ARM/gem5.opt
bin="$GEM5_SRC/build/ARM/gem5.opt"
[ -x "$bin" ] || { echo "ERROR: build finished but $bin is missing" >&2; exit 2; }
echo "built: $bin"
sha256sum "$bin"
