import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from trace_completeness import check_completeness  # noqa: E402
from trace_writer import TraceWriter  # noqa: E402


def _write_trace(path, model, terminal, event_types):
    w = TraceWriter(path, "S-R01", "R", "S", "F1", model)
    for i, kind in enumerate(event_types, start=1):
        w.event(kind, dyn_inst_seq=100 + i,
                injection_status=("INJECTED" if kind == "injection"
                                  else "NOT_APPLICABLE"),
                activation_status="TRIGGERED",
                trace_completeness="COMPLETE")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal=terminal, completeness="COMPLETE")


def test_coverage_requires_the_full_profile(tmp_path):
    full = tmp_path / "full.jsonl"
    _write_trace(full, "A01", "SQUASHED",
                 ["injection", "address_formed", "memory_request", "squash"])
    report = check_completeness(full)
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["missing_stages"] == []

    partial = tmp_path / "partial.jsonl"
    _write_trace(partial, "A01", "MASKED", ["injection"])
    report = check_completeness(partial)
    assert report["propagation_coverage"] == "PARTIAL"
    assert "memory_response" in report["missing_stages"]

    crash = tmp_path / "crash.jsonl"
    _write_trace(crash, "A03", "CRASH",
                 ["injection", "address_formed", "memory_request"])
    report = check_completeness(crash)
    assert report["propagation_coverage"] == "PARTIAL"
    assert report["missing_stages"] == ["simulator_abort"]


def test_coverage_is_independent_of_summary_reasons(tmp_path):
    path = tmp_path / "hands.jsonl"
    w = TraceWriter(path, "S-R01", "R", "S", "F1", "FW02")
    for kind in ("forwarding_decision", "memory_response",
                 "register_writeback", "consumer_commit"):
        w.event(kind, dyn_inst_seq=1, trace_completeness="COMPLETE")
    # Deliberately inconsistent: TRIGGERED without an injection event makes
    # TraceCompleteness INCOMPLETE, but the stages are all present.
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    report = check_completeness(path)
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["trace_completeness"] == "INCOMPLETE"
