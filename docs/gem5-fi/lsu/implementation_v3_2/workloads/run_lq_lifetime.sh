#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out="lq_lifetime.host.out"
./lq_lifetime | tee "$out"
python3 oracle_check.py "$(tr -d '[:space:]' < lq_lifetime.golden)" "$out"
