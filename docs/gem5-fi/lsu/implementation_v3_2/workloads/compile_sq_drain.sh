#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o sq_drain sq_drain.c
sha256sum sq_drain
