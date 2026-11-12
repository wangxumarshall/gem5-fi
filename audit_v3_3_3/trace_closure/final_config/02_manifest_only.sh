#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — STEP 2/5: manifest-only collection.
#
# Requires STEP 1 to be complete: the campaign root must exist and hold all
# 120 run directories (12 models x 5 contexts x {fault,control}) with their
# summary.json / campaign.json records. Historical pilot and Pre-Formal
# evidence roots are rejected outright.
#
# Writes ONLY under $RUNS/collector_manifest (disjoint from the full
# collector's $RUNS/collector_full). No XLSX/readiness export at this stage.
set -euo pipefail

ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

# Frozen identity — never edit.
BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
CAMPAIGN_ID=LSU-V333-FINAL-20261112
RUNS=runs/lsu/formal_v333_final_20261112
OUT="$RUNS/collector_manifest"
FULL="$RUNS/collector_full"

MODELS="A01 A03 FW02 FW05 SQ01 SQ03 SP05 DA04 LP01 MD04 LQ04 RP01"
CONTEXTS="1 2 3 4 5"
ROLES="fault control"

case "$RUNS" in
  */audit_v3_3_3/runs|*/audit_v3_3_3/runs/*|*/formal_v333|*/formal_v333/*|*pilot*|*pre_formal*|*PreFormal*)
    echo "error: refusing historical pilot/pre-formal evidence root: $RUNS" >&2
    exit 2
    ;;
esac

if [ ! -d "$RUNS" ]; then
  echo "error: campaign root missing: $RUNS" >&2
  echo "run 01_launch_campaign.sh first" >&2
  exit 2
fi

# Stage-2 and stage-3 outputs must stay disjoint.
if [ "$OUT" = "$FULL" ]; then
  echo "error: manifest-only output collides with the full collector output" >&2
  exit 2
fi

python3 - "$RUNS/campaign_identity.json" "$CAMPAIGN_ID" <<'PY'
import json
import sys
from pathlib import Path

path, campaign = sys.argv[1], sys.argv[2]
p = Path(path)
if not p.is_file():
    raise SystemExit(f"error: campaign identity missing: {p}")
record = json.loads(p.read_text(encoding="utf-8"))
if record.get("campaign_id") != campaign:
    raise SystemExit("error: campaign identity mismatch: "
                     f"{record.get('campaign_id')!r} != {campaign!r}")
print(f"campaign identity OK: {campaign}")
PY

# Fail closed unless every one of the 120 scheduled runs is present.
missing=""
for model in $MODELS; do
  for ctx in $CONTEXTS; do
    ctx_id=$(printf '%02d' "$ctx")
    for role in $ROLES; do
      dir="$RUNS/${model}-R${ctx_id}-${role}"
      if [ ! -d "$dir" ] || [ ! -f "$dir/summary.json" ] \
         || [ ! -f "$dir/campaign.json" ]; then
        missing="$missing $dir"
      fi
    done
  done
done
if [ -n "$missing" ]; then
  echo "error: campaign root is incomplete; missing run dirs/records:" >&2
  echo "$missing" >&2
  echo "run 01_launch_campaign.sh --resume, then retry STEP 2" >&2
  exit 3
fi

mkdir -p "$OUT"
python3 tools/lsu_v333_launch.py \
  --runs "$RUNS" \
  --campaign-id "$CAMPAIGN_ID" \
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \
  --out "$OUT" \
  --manifest-only \
  --expected-binary-sha "$BIN" \
  --expected-config-sha "$CFG"

echo "manifest-only collection wrote:"
echo "  $OUT/LSU_120Run_Campaign_Manifest.csv"
echo "  $OUT/LSU_60Fault_60Control_Pair_Map.csv"
echo "  $OUT/LSU_Control_Zero_Proof_Final.csv"
echo "  $OUT/per_run/"
