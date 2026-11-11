#!/bin/bash
# Build the LSU v3.3.2 W4 SQ-Forward candidate (P0-1 / FW02).
# Host is native aarch64 — plain host gcc, no cross toolchain.
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o sq_forward_w4v2 sq_forward_w4v2.c
sha256sum sq_forward_w4v2 sq_forward_w4v2.c
