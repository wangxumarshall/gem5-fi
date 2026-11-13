#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — STEP 4/5: final propagation chain,
# classification and the 8-sheet analysis workbook.
#
# Requires STEP 3 (collector_full) to be complete. Every control state is
# emitted by the strict tri-state emitter in tools/lsu_v333_control_proof.py;
# an UNKNOWN or INVALID control state is a hard failure.
#
# Existing reports are never overwritten implicitly. Pass --force (or set
# FORCE=1) only after a deliberate decision to regenerate.
#
#   bash 04_final_reports.sh           # write only if the outputs are absent
#   FORCE=1 bash 04_final_reports.sh   # explicit regeneration
set -euo pipefail

ROOT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
cd "$ROOT"

# Frozen identity — never edit.
BIN=62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd
CFG=8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225
CAMPAIGN_ID=LSU-V333-FINAL-20261112
RUNS=runs/lsu/formal_v333_final_20261112
COLL="$RUNS/collector_full"
MAP=audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv

PROP="$RUNS/LSU_60Context_Causal_Propagation_Final.csv"
READY="$RUNS/LSU_60Context_Final_Readiness.csv"
VALID="$RUNS/LSU_11Context_Repair_Validation.csv"
CTL="$RUNS/LSU_Control_Audit_Formal.csv"
BOOK="$RUNS/LSU_Final_Experiment_Config.xlsx"
AUDIT="$RUNS/LSU_Evidence_Completeness_Audit.csv"
A03CNT="$RUNS/LSU_A03_Injection_Count_Semantics.csv"

FORCE=${FORCE:-0}
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help)
      echo "usage: 04_final_reports.sh [--force]   (also FORCE=1)" >&2
      exit 0
      ;;
    *) echo "error: unknown argument: $arg" >&2; exit 2 ;;
  esac
done

case "$RUNS" in
  */audit_v3_3_3/runs|*/audit_v3_3_3/runs/*|*/formal_v333|*/formal_v333/*|*pilot*|*pre_formal*|*PreFormal*)
    echo "error: refusing historical pilot/pre-formal evidence root: $RUNS" >&2
    exit 2
    ;;
esac

# Ordered dependency: STEP 3 must have produced the full collector artifacts.
for needed in \
  "$COLL/LSU_120Run_Campaign_Manifest.csv" \
  "$COLL/LSU_60Fault_60Control_Pair_Map.csv" \
  "$COLL/LSU_Control_Zero_Proof_Final.csv" \
  "$COLL/LSU_Formal_Experiment_Config_Final.xlsx" \
  "$COLL/LSU_60Context_Final_Readiness.csv"; do
  if [ ! -f "$needed" ]; then
    echo "error: STEP 3 collector_full output missing: $needed" >&2
    echo "run 03_full_collector.sh before final reports" >&2
    exit 3
  fi
done

# The campaign-root identity must still carry the frozen binary/config.
python3 - "$RUNS/campaign_identity.json" "$BIN" "$CFG" "$CAMPAIGN_ID" <<'PY'
import json
import sys
from pathlib import Path

path, binary, config, campaign = sys.argv[1:5]
p = Path(path)
if not p.is_file():
    raise SystemExit(f"error: campaign identity missing: {p}")
record = json.loads(p.read_text(encoding="utf-8"))
problems = []
if record.get("campaign_id") != campaign:
    problems.append(f"campaign_id={record.get('campaign_id')!r}")
if record.get("binary_sha") != binary:
    problems.append(f"binary_sha={record.get('binary_sha')!r}")
if record.get("config_sha") != config:
    problems.append(f"config_sha={record.get('config_sha')!r}")
if problems:
    raise SystemExit("error: campaign identity mismatch: " + ", ".join(problems))
print(f"campaign identity OK: {campaign}")
PY

refuse_overwrite() {
  local path="$1"
  if [ -e "$path" ] && [ "$FORCE" != "1" ]; then
    echo "error: refusing to overwrite an existing report: $path" >&2
    echo "set FORCE=1 (or pass --force) to regenerate explicitly" >&2
    exit 4
  fi
}

refuse_overwrite "$PROP"
refuse_overwrite "$READY"
refuse_overwrite "$VALID"
refuse_overwrite "$CTL"
refuse_overwrite "$BOOK"
refuse_overwrite "$AUDIT"
refuse_overwrite "$A03CNT"

# 4a. 60-context causal propagation table
python3 tools/lsu_v333_propagation.py \
  --runs "$RUNS" \
  --out "$PROP"

# 4b. final classification/readiness + 11-context repair validation
python3 tools/lsu_v333_trace_closure.py \
  --runs "$RUNS" \
  --propagation "$PROP" \
  --out-readiness "$READY" \
  --out-validation "$VALID"

# 4c. strict tri-state control audit (the emitter owns the classification).
python3 tools/lsu_v333_control_proof.py \
  --emit-control-audit \
  --proof "$COLL/LSU_Control_Zero_Proof_Final.csv" \
  --out "$CTL"

# Fail closed on any non-canonical tri-state, independently of the emitter's
# own exit code (missing/illegal counts must never become a zero-injection PASS).
python3 - "$CTL" <<'PY'
import csv
import sys

path = sys.argv[1]
with open(path, newline="", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
bad = [row for row in rows
       if str(row.get("ControlInjected", "")).strip() in ("UNKNOWN", "INVALID")]
if bad:
    for row in bad:
        print("error: control audit state "
              f"{row.get('ControlInjected')} for "
              f"{row.get('ModelID')}-R{row.get('ContextID')}: "
              f"{row.get('ControlInjectedReason', '')}", file=sys.stderr)
    raise SystemExit(5)
print(f"control audit OK: {len(rows)} rows, no UNKNOWN/INVALID: {path}")
PY

# 4d. 8-sheet final experiment workbook (collector_full carries its own XLSX)
python3 tools/lsu_v333_workbook.py \
  --runs "$RUNS" \
  --mapping "$MAP" \
  --controls "$CTL" \
  --causal "$PROP" \
  --out "$BOOK"

# 4e. evidence completeness (five distinct statuses) and A03 count semantics
python3 tools/lsu_v333_evidence_audit.py \
  --runs "$RUNS" \
  --propagation "$PROP" \
  --readiness "$READY" \
  --out "$AUDIT" \
  --a03-out "$A03CNT"

echo "wrote:"
echo "  $PROP"
echo "  $READY"
echo "  $VALID"
echo "  $CTL"
echo "  $BOOK"
echo "  $AUDIT"
echo "  $A03CNT"
echo "verified STEP 3 input:"
echo "  $COLL/LSU_Formal_Experiment_Config_Final.xlsx"
