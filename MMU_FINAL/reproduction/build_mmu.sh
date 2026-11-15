#!/bin/bash
# Build the frozen gem5 binary from the vendored source tree.
# Clean build: -j16 (the 0202 host OOM-kills at -j126).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

cd "$MMU_REPO_ROOT/CHAOS/gem5"
JOBS="${MMU_BUILD_JOBS:-16}"
mmu_info "building build/ARM/gem5.opt with -j$JOBS in $PWD"
scons -j"$JOBS" build/ARM/gem5.opt

BIN="$MMU_REPO_ROOT/CHAOS/gem5/build/ARM/gem5.opt"
[ -x "$BIN" ] || mmu_die "build finished but $BIN is missing"
ACTUAL="$(sha256sum "$BIN" | cut -d' ' -f1)"
mmu_info "built binary: $BIN"
mmu_info "sha256:       $ACTUAL"
mmu_info "frozen:       $MMU_EXPECTED_GEM5_SHA256"
if [ "$ACTUAL" = "$MMU_EXPECTED_GEM5_SHA256" ]; then
    mmu_info "binary matches the frozen experiment binary byte-for-byte"
else
    mmu_info "binary differs from the frozen artifact; this is reported, not hidden."
    mmu_info "Check compiler version, build flags, timestamps and embedded paths"
    mmu_info "before claiming semantic equivalence (MMU_REPRODUCTION_GUIDE.md section 4)."
fi

# The eight model hooks must be present in the built source closure.
missing=0
for m in M01 M02 M03 M04 M05 M06 M07 M08; do
    if git -C "$MMU_REPO_ROOT" grep -q "\"$m\"" -- CHAOS/gem5/src 2>/dev/null; then
        mmu_info "hook present: $m"
    else
        mmu_info "hook MISSING: $m"; missing=1
    fi
done
[ "$missing" = 0 ] || mmu_die "one or more MMU model hooks are absent from the source tree"
