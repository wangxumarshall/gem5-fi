#!/usr/bin/env bash
# 25 count-only eligible-event scans: 5 models x 5 contexts.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
rfwb_require_gem5
rfwb_clean_samples 'SCAN-*'
rfwb_index_init

n=0
for m in M001 M002 M003 M004 M005; do
    for c in C01 C02 C03 C04 C05; do
        s="SCAN-${m}-${c}-N"
        echo "SCAN $s"
        "$RFWB_ROOT/scripts/experiment/run_one.sh" "$m" "$c" count 0 "$s"
        n=$((n+1))
    done
done
echo "prescan complete: $n/25 scans; traces in $RUNS/traces"
