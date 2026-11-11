#!/bin/bash
# Build the LSU v3.3.2 RP01 partial-overlap candidate (P0-2 / RP01).
# Host is native aarch64 -- plain host gcc, no cross toolchain.
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o replay_partial_v332 replay_partial_v332.c
./replay_partial_v332 | head -1 | cut -d= -f2 > replay_partial_v332.golden
sha256sum replay_partial_v332 replay_partial_v332.c
cat replay_partial_v332.golden
