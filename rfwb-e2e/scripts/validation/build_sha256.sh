#!/usr/bin/env bash
# Build RF_WB_SHA256SUMS.txt over every file and symlink in this project,
# excluding runs/ and the manifest itself.  Verifies the 25 context symlinks
# resolve to their five base ELFs first.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_locate
cd "$RFWB_ROOT"

ok=0
for i in 1 2 3 4 5; do
    base="workloads/build/rfwb_0${i}"
    bh=$(sha256sum "$base" | cut -d' ' -f1)
    for c in 1 2 3 4 5; do
        p="workloads/build/rfwb_0${i}_C0${c}"
        [ -e "$p" ] || { echo "MISSING $p" >&2; exit 1; }
        ph=$(sha256sum "$p" | cut -d' ' -f1)
        [ "$ph" = "$bh" ] || { echo "HASH MISMATCH $p != $base" >&2; exit 1; }
        ok=$((ok+1))
    done
done
echo "context ELF hashes OK: $ok/25"

find . \( -type f -o -type l \) \
    ! -path './runs/*' \
    ! -name 'RF_WB_SHA256SUMS.txt' -print0 \
    | sort -z | xargs -0 sha256sum > RF_WB_SHA256SUMS.txt
sha256sum -c RF_WB_SHA256SUMS.txt >/dev/null
echo "listed entries: $(wc -l < RF_WB_SHA256SUMS.txt)"
echo "manifest sha256: $(sha256sum RF_WB_SHA256SUMS.txt | cut -d' ' -f1)"
