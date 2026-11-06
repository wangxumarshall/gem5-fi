#!/usr/bin/env bash
# Gate-1 reproducible verification. Run from anywhere; all paths are derived
# from this script's location. Exit 0 = all platform unit tests passed.
set -uo pipefail

PLATFORM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPL="$(dirname "$PLATFORM")"
LSUS="$(dirname "$IMPL")"
WORKBOOK="$IMPL/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.xlsx"
if [ ! -f "$WORKBOOK" ]; then
  WORKBOOK="$LSUS/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx"
fi
LOGS="$IMPL/logs"
mkdir -p "$LOGS"

cd "$PLATFORM" || exit 2
echo "== pytest =="
python3 -m pytest tests -v 2>&1 | tee "$LOGS/gate1_tests.log"
test_rc=${PIPESTATUS[0]}

echo "== config parser (structural; --allow-incomplete reports the frozen workbook gaps) =="
python3 config_parser.py "$WORKBOOK" "$LOGS/config_v31.json" --allow-incomplete \
    2>&1 | tee "$LOGS/gate1_config_validation.log"
cfg_rc=${PIPESTATUS[0]}

echo "== trace sample validator =="
python3 trace_validator.py "$IMPL/LSU_Trace_Sample_v3.2.jsonl" | tee "$LOGS/gate1_trace_validator.log"
val_rc=${PIPESTATUS[0]}

echo "== trace sample completeness =="
python3 trace_completeness.py "$IMPL/LSU_Trace_Sample_v3.2.jsonl" > "$LOGS/gate1_trace_completeness.json"
comp_rc=$?

echo "== summary =="
echo "pytest_rc=$test_rc config_rc=$cfg_rc validator_rc=$val_rc completeness_rc=$comp_rc"
if [ "$test_rc" -ne 0 ] || [ "$cfg_rc" -ne 0 ] || [ "$val_rc" -ne 0 ] || [ "$comp_rc" -ne 0 ]; then
  exit 1
fi
exit 0
