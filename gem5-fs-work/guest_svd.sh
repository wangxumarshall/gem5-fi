#!/bin/sh
# FS-mode eigen_svd multi-thread verification (guest side)
# Host loader scheme: run the host-built sdcshield against the host glibc
# set bundled on /mnt/libs (avoids polluting guest tools with host libc).
mount -t ext2 /dev/vdb /mnt 2>/dev/null || mount /dev/vdb /mnt
echo "=== guest: disk mounted ==="
LD=/mnt/libs/ld-linux-aarch64.so.1
export LD_LIBRARY_PATH=/mnt/libs
echo "=== nproc (guest) ==="
nproc
echo "=== sdcshield --list-tests (head) ==="
$LD --library-path /mnt/libs /mnt/bin/sdcshield --list-tests 2>&1 | head -4
echo "=== eigen_svd_double -n 2 -t 30 mdim=64 ==="
$LD --library-path /mnt/libs /mnt/bin/sdcshield -e eigen_svd_double -t 30 -n 2 -O eigen_svd_double.mdim=64 -v 2>&1 | grep -E "test-plans|fullsocket|core_groups|test:|result|threads:|exit:" | head -20
echo "=== GUEST DONE ==="
unset LD_LIBRARY_PATH
/sbin/m5 exit
