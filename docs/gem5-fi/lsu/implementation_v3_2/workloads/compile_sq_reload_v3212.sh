#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o sq_reload_v3212 sq_reload_v3212.c
sha256sum sq_reload_v3212
