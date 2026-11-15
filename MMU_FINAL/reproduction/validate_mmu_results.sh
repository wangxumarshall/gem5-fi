#!/bin/bash
# Validate the archived authority: hashes, 40/40 formal samples, 31/5/4
# terminal split, 28 control oracles, 10/10 repeat consistency.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

python3 "$MMU_REPRO_DIR/verify_archive.py" "$@"
python3 "$MMU_REPRO_DIR/validate_results.py"
