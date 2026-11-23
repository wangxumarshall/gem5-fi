#!/bin/bash
# Safe resume entry point for the WHEN-5X3 MMU campaign.
#
# Every run is independent and its manifest.json is an idempotency marker:
# re-running this script re-runs only controls/faults that have no final
# manifest.  The command below never overwrites a completed run directory.
set -euo pipefail
cd "$(dirname "$0")"

BOOT_CKPT="${W5X3_CHECKPOINT:-$PWD/runs/mmu_bootF1/cpt.244799013609}"
if [ ! -d "$BOOT_CKPT" ]; then
    echo "missing runtime checkpoint: $BOOT_CKPT" >&2
    echo "place the frozen checkpoint at the path above" >&2
    exit 2
fi
export W5X3_CHECKPOINT="$BOOT_CKPT"
JOBS="${JOBS:-16}"

echo "[resume] checkpoint=$W5X3_CHECKPOINT jobs=$JOBS"
python3 campaign/when5x3_runner.py --all --jobs "$JOBS" "$@"
python3 campaign/finalize.py
