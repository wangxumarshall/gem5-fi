#!/bin/sh
# build_all.sh — reproducible build of the W10S and W11-W14 guest workloads.
#
# Host is native aarch64; the guest is aarch64, so no cross toolchain is used.
# Flags match the verified W9/W10 binaries:
#   gcc -O2 -static -march=armv8-a+simd -o <bin> <src>
#
# Usage: ./build_all.sh [CC]
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CC=${1:-${CC:-gcc}}
CFLAGS="-O2 -static -march=armv8-a+simd"

for n in 10S 11 12 13 14; do
    l=$(printf '%s' "$n" | tr 'A-Z' 'a-z')
    echo "[build] W$n"
    $CC $CFLAGS -o "$HERE/W$n/mmu_w$l" "$HERE/W$n/mmu_w$l.c"
done

echo "[build] sha256"
sha256sum "$HERE"/W10S/mmu_w10s "$HERE"/W11/mmu_w11 \
           "$HERE"/W12/mmu_w12 "$HERE"/W13/mmu_w13 "$HERE"/W14/mmu_w14
