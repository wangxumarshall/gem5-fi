#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="sq_drain.host.out"
./sq_drain | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < sq_drain.golden)" "$out"
