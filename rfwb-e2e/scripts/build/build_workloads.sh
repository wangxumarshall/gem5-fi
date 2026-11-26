#!/usr/bin/env bash
# Rebuild the five AArch64 workloads from source.
#
# The frozen authoritative ELFs in workloads/build were built on the experiment
# host with gcc 12.3.1 (openEuler -109).  A different compiler patch level can
# change BuildID/.comment and therefore the file SHA256 even when code is
# equivalent.  This script never overwrites the authoritative ELFs; it builds
# into workloads/build_rebuilt by default and reports hash equality.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_locate

out=${1:-$RFWB_ROOT/workloads/build_rebuilt}
mkdir -p "$out"
command -v gcc >/dev/null || { echo "ERROR: gcc not found" >&2; exit 2; }

for i in 1 2 3 4 5; do
    src_c="$RFWB_ROOT/workloads/source/rfwb_0${i}.c"
    src_s="$RFWB_ROOT/workloads/source/rfwb_0${i}.S"
    [ -f "$src_c" ] && [ -f "$src_s" ] || { echo "ERROR: missing source for rfwb_0$i" >&2; exit 2; }
    gcc -O2 -static "$src_c" "$src_s" -o "$out/rfwb_0${i}"
    for c in 1 2 3 4 5; do
        ln -sfn "rfwb_0${i}" "$out/rfwb_0${i}_C0${c}"
    done
done

echo "built into $out"
echo "compiler: $(gcc --version | head -1)"
echo "authoritative vs rebuilt SHA256:"
ok=0
for i in 1 2 3 4 5; do
    a=$(sha256sum "$RFWB_ROOT/workloads/build/rfwb_0${i}" | cut -d' ' -f1)
    b=$(sha256sum "$out/rfwb_0${i}" | cut -d' ' -f1)
    if [ "$a" = "$b" ]; then
        echo "  rfwb_0${i}: IDENTICAL $a"
        ok=$((ok+1))
    else
        echo "  rfwb_0${i}: DIFFERENT authoritative=$a rebuilt=$b"
    fi
done
echo "byte-identical: $ok/5 (frozen ELFs remain authoritative for the published results)"
