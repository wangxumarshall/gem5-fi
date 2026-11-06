#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o lq_lifetime lq_lifetime.c
sha256sum lq_lifetime
