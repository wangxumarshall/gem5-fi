import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from tools.prop_trace_to_v31 import convert  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402
from trace_validator import validate  # noqa: E402

IMPL = PLATFORM.parent
CSV = IMPL / "preexisting_rejected/pilots/A01F0/prop_trace.csv.gz"


def test_real_csv_converts_to_valid_complete_trace(tmp_path):
    out = tmp_path / "trace.jsonl"
    result = convert(
        CSV, out, sample_run_id="PILOT-A01-TEST", run_id="PILOT-A01",
        sub_task_id="PILOT-A01-S01", fault_id="A01-CFG01",
        fault_model_id="A01", run_status="COMPLETED", activation="TRIGGERED",
        terminal="MASKED", completeness="COMPLETE")
    assert result["rows"] == 6
    assert validate(out) == []
    report = check_completeness(out)
    assert report["trace_completeness"] == "COMPLETE"
    assert report["injections"] == 1


def test_truncated_or_incomplete_can_omit_summary(tmp_path):
    out = tmp_path / "trace.jsonl"
    convert(
        CSV, out, sample_run_id="PILOT-A01-TEST", run_id="PILOT-A01",
        sub_task_id="PILOT-A01-S01", fault_id="A01-CFG01",
        fault_model_id="A01", run_status="COMPLETED", activation="TRIGGERED",
        terminal="MASKED", completeness="INCOMPLETE", no_summary=True)
    report = check_completeness(out)
    assert report["trace_completeness"] == "INCOMPLETE"
    assert report["terminal_state"] is None
