#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="replay_dependency.host.out"
./replay_dependency | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < replay_dependency.golden)" "$out"
