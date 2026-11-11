#!/bin/bash
# Build the LSU v3.3.2 P0-3 / MD04 context workload (md04_violations_v332).
# Host is native aarch64 — plain host gcc, no cross toolchain.
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o md04_violations_v332 md04_violations_v332.c
sha256sum md04_violations_v332 md04_violations_v332.c
