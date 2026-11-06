import json
import sys
from pathlib import Path

import pytest

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from trace_completeness import check_completeness  # noqa: E402
from trace_schema import EDGE_FIELDS, EVENT_FIELDS, SUMMARY_FIELDS, schema_required  # noqa: E402
from trace_summary import summarize  # noqa: E402
from trace_validator import validate  # noqa: E402
from trace_writer import TraceWriteError, TraceWriter  # noqa: E402


def make_writer(tmp_path):
    return TraceWriter(tmp_path / "t.jsonl", "S-R01", "R", "S", "F1", "A01")


def test_writer_emits_every_v31_field(tmp_path):
    w = make_writer(tmp_path)
    eid = w.event("injection", unit="AGU", dyn_inst_seq=10,
                  old_value="0x1000", new_value="0x1008",
                  injection_status="INJECTED")
    rec = json.loads((tmp_path / "t.jsonl").read_text().splitlines()[0])
    assert set(rec) == set(EVENT_FIELDS)
    assert rec["event_id"] == eid
    assert rec["dyn_inst_seq"] == 10
    assert rec["replay_generation"] is None


def test_orphan_edge_rejected(tmp_path):
    w = make_writer(tmp_path)
    with pytest.raises(TraceWriteError, match="orphan"):
        w.edge(1, 2)


def test_complete_trace_validates_and_summarizes(tmp_path):
    w = make_writer(tmp_path)
    e1 = w.event("injection", unit="AGU", dyn_inst_seq=10,
                 old_value="0x1000", new_value="0x1008",
                 injection_status="INJECTED", activation_status="TRIGGERED",
                 trace_completeness="COMPLETE")
    e2 = w.event("memory_response", parent_event_id=e1, unit="L1D",
                 dyn_inst_seq=10, request_id=7, va="0x1008", pa="0x1008",
                 activation_status="TRIGGERED", trace_completeness="COMPLETE")
    w.edge(e1, e2, value_hash="deadbeef", trace_completeness="COMPLETE")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    assert validate(tmp_path / "t.jsonl") == []
    report = check_completeness(tmp_path / "t.jsonl")
    assert report["trace_completeness"] == "COMPLETE"
    assert report["terminal_state"] == "MASKED"
    summary = summarize(tmp_path / "t.jsonl")
    assert summary["events"] == 2
    assert summary["edges"] == 1
    assert summary["event_types"]["injection"] == 1


def test_incomplete_trace_never_masked(tmp_path):
    w = make_writer(tmp_path)
    w.event("injection", dyn_inst_seq=1, injection_status="INJECTED",
            activation_status="TRIGGERED")
    with pytest.raises(TraceWriteError, match="incomplete trace cannot be classified MASKED"):
        w.close(run_status="COMPLETED", activation="TRIGGERED",
                terminal="MASKED", completeness="INCOMPLETE")
    # Re-create with an honest incomplete terminal; the checker must preserve INCOMPLETE.
    w2 = make_writer(tmp_path)
    w2.event("injection", dyn_inst_seq=1, injection_status="INJECTED",
             activation_status="TRIGGERED")
    w2.close(run_status="TIMEOUT", activation="TRIGGERED",
             terminal="HANG", completeness="INCOMPLETE")
    report = check_completeness(tmp_path / "t.jsonl")
    assert report["trace_completeness"] == "INCOMPLETE"
    assert report["terminal_state"] != "MASKED"


def test_missing_field_and_bad_summary_rejected(tmp_path):
    w = make_writer(tmp_path)
    w.event("injection", dyn_inst_seq=1, injection_status="INJECTED")
    w.close(run_status="COMPLETED", activation="NOT_TRIGGERED",
            terminal="HANG", completeness="INCOMPLETE")
    path = tmp_path / "t.jsonl"
    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    del rec["replay_generation"]
    lines[0] = json.dumps(rec)
    summary = json.loads(lines[-1])
    summary["counts"]["events"] = 99
    lines[-1] = json.dumps(summary)
    path.write_text("\n".join(lines) + "\n")
    errs = validate(path)
    assert any("missing fields" in e for e in errs)
    assert any("summary events=99" in e for e in errs)


def test_nochange_counts_as_injection(tmp_path):
    w = make_writer(tmp_path)
    w.event("injection_nochange", unit="AGU", dyn_inst_seq=7,
            injection_status="NO_CHANGE", activation_status="TRIGGERED",
            trace_completeness="COMPLETE")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    report = check_completeness(tmp_path / "t.jsonl")
    assert report["injections"] == 1


def test_schema_constants_match_json_schema():
    assert schema_required("event") == EVENT_FIELDS
    assert schema_required("edge") == EDGE_FIELDS
    assert schema_required("summary") == SUMMARY_FIELDS
