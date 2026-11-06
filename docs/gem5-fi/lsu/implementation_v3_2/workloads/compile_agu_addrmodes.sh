#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o agu_addrmodes agu_addrmodes.c
sha256sum agu_addrmodes
