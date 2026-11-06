#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
gcc -O2 -static -o replay_dependency replay_dependency.c
sha256sum replay_dependency
