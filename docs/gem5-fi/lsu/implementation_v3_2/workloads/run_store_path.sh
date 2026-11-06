#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="store_path.host.out"
./store_path | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < store_path.golden)" "$out"
