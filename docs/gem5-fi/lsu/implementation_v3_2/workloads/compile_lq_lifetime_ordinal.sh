#!/usr/bin/env bash
# Build lq_lifetime_ordinal: freestanding AArch64 ELF, no libc/crt0.
# _start (lq_lifetime_ordinal.S) is the entry point; the first five data
# loads of the process are the five anchor_tbl loads A1..A5.
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -nostdlib -fno-pic -no-pie -Wl,-e,_start \
    -o lq_lifetime_ordinal lq_lifetime_ordinal.S lq_lifetime_ordinal.c
sha256sum lq_lifetime_ordinal
