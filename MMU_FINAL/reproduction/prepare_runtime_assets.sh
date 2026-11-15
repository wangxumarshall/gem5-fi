#!/bin/bash
# Populate the runtime assets required by the full-system samples.
#
#   ./prepare_runtime_assets.sh <ASSET_SOURCE_ROOT>
#
# <ASSET_SOURCE_ROOT> must contain:
#   gem5-fs/vmlinux
#   gem5-fs/boot.arm64
#   runs/disks/mmu_template.img
#   runs/mmu_bootF1/cpt.244799013609/
#
# Files are COPIED into this clone (never symlinked) so the clone has no
# hidden dependency on a historical workspace.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

SRC="${1:-}"
[ -n "$SRC" ] || mmu_die "usage: $0 <ASSET_SOURCE_ROOT>"
[ -d "$SRC" ] || mmu_die "asset source not found: $SRC"

copy_checked() {
    local rel="$1"
    [ -e "$SRC/$rel" ] || mmu_die "missing asset: $SRC/$rel"
    mkdir -p "$(dirname "$MMU_REPO_ROOT/$rel")"
    if [ -f "$SRC/$rel" ]; then
        cp -a "$SRC/$rel" "$MMU_REPO_ROOT/$rel"
    else
        rsync -a "$SRC/$rel/" "$MMU_REPO_ROOT/$rel/"
    fi
    mmu_info "staged $rel"
}

copy_checked gem5-fs/vmlinux
copy_checked gem5-fs/boot.arm64
copy_checked runs/disks/mmu_template.img
copy_checked runs/mmu_bootF1/cpt.244799013609

DISK_SHA="$(sha256sum "$MMU_DISK_TEMPLATE" | cut -d' ' -f1)"
[ "$DISK_SHA" = "$MMU_EXPECTED_DISK_SHA256" ] \
    && mmu_info "disk template hash matches: $DISK_SHA" \
    || mmu_die "disk template hash $DISK_SHA != $MMU_EXPECTED_DISK_SHA256"

mmu_info "runtime assets ready"
