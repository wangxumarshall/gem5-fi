#!/bin/bash
# Shared environment for the MMU final reproduction entry points.
# All paths are derived from this repository clone; nothing points at a
# historical development workspace.
set -euo pipefail

export MMU_REPO_ROOT="${MMU_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export MMU_FINAL_DIR="$MMU_REPO_ROOT/MMU_FINAL"
export MMU_RESULTS_DIR="$MMU_FINAL_DIR/results"
export MMU_REPRO_DIR="$MMU_FINAL_DIR/reproduction"

# The frozen binary is the one built from source commit 60f1a876.
export MMU_GEM5="${MMU_GEM5:-$MMU_REPO_ROOT/CHAOS/gem5/build/ARM/gem5.opt}"
export MMU_EXPECTED_GEM5_SHA256="b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185"
export MMU_SOURCE_COMMIT="60f1a8760410288128061d85582e5395b24c0106"
export MMU_EXPECTED_CHECKPOINT_SHA256="4aa1ba38b5288fe1c7e58dde73a1f27166e67f846f77f241fcd1fb2cd89e6417"
export MMU_CHECKPOINT="$MMU_REPO_ROOT/runs/mmu_bootF1/cpt.244799013609"
export MMU_DISK_TEMPLATE="$MMU_REPO_ROOT/runs/disks/mmu_template.img"
export MMU_EXPECTED_DISK_SHA256="bb872707d6bae3885688556908536d4f92e07da68aae0401d27ff03216425759"
export MMU_KERNEL="$MMU_REPO_ROOT/gem5-fs/vmlinux"
export MMU_BOOTLOADER="$MMU_REPO_ROOT/gem5-fs/boot.arm64"

mmu_die() { echo "MMU-ERROR: $*" >&2; exit 1; }
mmu_info() { echo "[mmu] $*"; }

mmu_check_runtime_assets() {
    [ -x "$MMU_GEM5" ] || mmu_die "gem5 binary missing: $MMU_GEM5 (run reproduction/build_mmu.sh)"
    [ -f "$MMU_KERNEL" ] || mmu_die "kernel missing: $MMU_KERNEL (run reproduction/prepare_runtime_assets.sh)"
    [ -f "$MMU_BOOTLOADER" ] || mmu_die "bootloader missing: $MMU_BOOTLOADER"
    [ -d "$MMU_CHECKPOINT" ] || mmu_die "checkpoint missing: $MMU_CHECKPOINT (run reproduction/prepare_runtime_assets.sh)"
    [ -f "$MMU_DISK_TEMPLATE" ] || mmu_die "disk template missing: $MMU_DISK_TEMPLATE (run reproduction/prepare_runtime_assets.sh)"
}

mmu_check_frozen_binary() {
    local out
    out="$(sha256sum "$MMU_GEM5" | cut -d' ' -f1)"
    if [ "$out" != "$MMU_EXPECTED_GEM5_SHA256" ]; then
        mmu_info "WARNING: gem5 SHA256 $out != frozen $MMU_EXPECTED_GEM5_SHA256"
        mmu_info "A different hash is not automatically a failure; see MMU_REPRODUCTION_GUIDE.md section 4."
    fi
}
