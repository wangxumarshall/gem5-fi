#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o sq_forward sq_forward.c
sha256sum sq_forward
