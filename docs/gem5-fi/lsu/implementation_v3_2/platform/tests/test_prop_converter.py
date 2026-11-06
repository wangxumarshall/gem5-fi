import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from tools.prop_trace_to_v31 import convert  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402
from trace_validator import validate  # noqa: E402

IMPL = PLATFORM.parent
CSV = IMPL / "preexisting_rejected/pilots/A01F0/prop_trace.csv.gz"
A03_CSV = IMPL / "pilots/A03F5/prop_trace.csv.gz"


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


def test_response_address_is_pa_not_va(tmp_path):
    out = tmp_path / "trace.jsonl"
    convert(CSV, out, sample_run_id="PILOT-A01-TEST", run_id="PILOT-A01",
            sub_task_id="PILOT-A01-S01", fault_id="A01-CFG01",
            fault_model_id="A01", run_status="COMPLETED",
            activation="TRIGGERED", terminal="MASKED", completeness="COMPLETE")
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    resp = next(r for r in rows if r.get("event_type") == "memory_response")
    assert resp["pa"] is not None and resp["va"] is None


def test_each_injection_gets_its_own_injection_event_id(tmp_path):
    import pytest
    out = tmp_path / "trace.jsonl"
    convert(A03_CSV, out, sample_run_id="PILOT-A03-TEST", run_id="PILOT-A03",
            sub_task_id="PILOT-A03-S01", fault_id="A03-CFG01",
            fault_model_id="A03", run_status="SIMULATOR_ERROR",
            activation="TRIGGERED", terminal="CRASH", completeness="COMPLETE",
            allow_truncated_complete=True)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    injections = [r for r in rows if r.get("event_type") == "injection"]
    ids = [r["injection_event_id"] for r in injections]
    assert len(ids) == len(set(ids)) == 73
    # Downstream nodes inherit the injection id of their own ptag.
    assert all(r["injection_event_id"] >= 1 for r in rows if r.get("record_type") == "event")


def test_truncated_complete_requires_crash(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        convert(A03_CSV, tmp_path / "trace.jsonl",
                sample_run_id="PILOT-A03-TEST", run_id="PILOT-A03",
                sub_task_id="PILOT-A03-S01", fault_id="A03-CFG01",
                fault_model_id="A03", run_status="COMPLETED",
                activation="TRIGGERED", terminal="MASKED", completeness="COMPLETE",
                allow_truncated_complete=True)
