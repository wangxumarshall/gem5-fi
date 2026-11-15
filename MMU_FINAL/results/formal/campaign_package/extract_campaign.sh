#!/usr/bin/env bash
# Reproduce the MMU formal campaign dataset from the stable server paths.
# Read-only over run evidence. Adjust REPO if the workspace moves.
set -eu
REPO="${REPO:-/home/sdc/gem5-fi-mmu-impl-v2}"
CAMP="$REPO/runs/MMU_FORMAL_CAMPAIGN_20261113"
python3 "$CAMP/analysis/collect.py"
python3 "$CAMP/analysis/report.py"
python3 "$CAMP/analysis/validate_models.py"
python3 "$CAMP/analysis/package.py"
echo "Artifacts regenerated under $CAMP/analysis and"
echo "$CAMP/MMU_Final_Formal_Campaign_Results_Package"
