#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="agu_addrmodes.host.out"
./agu_addrmodes | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < agu_addrmodes.golden)" "$out"
