#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="alignment.host.out"
./alignment | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < alignment.golden)" "$out"
