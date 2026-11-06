#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o load_response load_response.c
sha256sum load_response
