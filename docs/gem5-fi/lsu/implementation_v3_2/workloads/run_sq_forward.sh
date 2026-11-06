#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="sq_forward.host.out"
./sq_forward | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < sq_forward.golden)" "$out"
