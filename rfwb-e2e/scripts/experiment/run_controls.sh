#!/usr/bin/env bash
# 25 Controls: 5 models x 5 contexts, RFWB_MODE=off. No Trace is collected.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_require_gem5
rfwb_clean_samples 'CTRL-*'
rfwb_index_init

n=0
for m in M001 M002 M003 M004 M005; do
    for c in C01 C02 C03 C04 C05; do
        s="CTRL-RFWB-${m}-${c}-RUN"
        echo "CONTROL $s"
        "$RFWB_ROOT/scripts/experiment/run_one.sh" "$m" "$c" off 0 "$s"
        n=$((n+1))
    done
done
echo "controls complete: $n/25 runs"
