#!/bin/bash
# fs_mk_sdcshield_disk.sh — 无 root 制第二磁盘: gem5-fs-work/diskroot → sdcshield.img
# 依 2026-09-22 sdcshield-fi-eval 计划 Task 3.1 设计 (mke2fs -d 目录打包)。
# guest 内: mount /dev/vdb /mnt; LD_LIBRARY_PATH=/mnt/libs /mnt/bin/sdcshield ...
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/gem5-fs-work/diskroot"
OUT="$ROOT/gem5-fs-work/sdcshield.img"
SZ=$(du -sm "$SRC" | awk '{print $1}')
IMG_MB=$(( (SZ * 3 / 2 + 8) / 8 * 8 ))   # 1.5x + 8MB, 8MB 取整
[ "$IMG_MB" -lt 32 ] && IMG_MB=32
echo "mkfs: $SRC (${SZ}MB) -> $OUT (${IMG_MB}MB ext2)"
rm -f "$OUT"
mke2fs -q -t ext2 -b 4096 -d "$SRC" -L sdcdisk "$OUT" "${IMG_MB}M"
e2fsck -fn "$OUT" | tail -2
echo "OK: $OUT"
