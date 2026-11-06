#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="load_response.host.out"
./load_response | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < load_response.golden)" "$out"
