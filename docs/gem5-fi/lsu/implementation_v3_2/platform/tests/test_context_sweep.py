import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from run_context_sweep import _entry  # noqa: E402


def _meta(path: Path, **overrides):
    meta = {
        "pilot_id": "PILOT-A01-R01",
        "seed": 7,
        "accepted": True,
        "injection": {"attempted": 1, "eligible": 1, "injected": 1},
        "injection_count": 1,
        "classification": {
            "run_status": "COMPLETED",
            "fault_activation_status": "TRIGGERED",
            "terminal_state": "MASKED",
            "terminal_state_reason": None,
            "record_integrity": "VALID",
            "propagation_coverage": "COMPLETE",
            "oracle_outcome": "PASS",
            "trace_completeness": "COMPLETE",
        },
        "trace": {"completeness": {"events": 3, "edges": 1,
                                   "injections": 1, "activations": 1}},
        "crash_evidence": None,
        "exit_code": 0,
    }
    meta.update(overrides)
    path.mkdir(parents=True, exist_ok=True)
    (path / "pilot_meta.json").write_text(json.dumps(meta))


def test_accepted_entry_carries_all_dimensions(tmp_path):
    _meta(tmp_path / "A01-R01")
    entry = _entry("A01", 1, tmp_path / "A01-R01", 0, "", "")
    assert entry["accepted"] is True
    assert entry["terminal"] == "MASKED"
    assert entry["injection_count"] == 1
    assert entry["trace_counts"]["injections"] == 1
    assert entry["failure_detail"] is None


def test_failed_context_is_recorded_not_dropped(tmp_path):
    _meta(tmp_path / "A01-R03", accepted=False,
          classification={"run_status": "COMPLETED",
                          "fault_activation_status": "TRIGGERED",
                          "terminal_state": "UNRESOLVED",
                          "terminal_state_reason": "UNRESOLVED_NO_DATA_VALUE_EVIDENCE",
                          "record_integrity": "VALID",
                          "propagation_coverage": "COMPLETE",
                          "oracle_outcome": "PASS",
                          "trace_completeness": "COMPLETE"})
    entry = _entry("A01", 3, tmp_path / "A01-R03", 1, "", "")
    assert entry["accepted"] is False
    assert entry["terminal"] == "UNRESOLVED"
    assert entry["terminal_reason"] == "UNRESOLVED_NO_DATA_VALUE_EVIDENCE"


def test_missing_meta_yields_explicit_failure(tmp_path):
    entry = _entry("FW02", 2, tmp_path / "FW02-R02", 1, "",
                   "Traceback (most recent call last): ...")
    assert entry["accepted"] is False
    assert entry["terminal_reason"] == "RUNNER_EXCEPTION"
    entry2 = _entry("FW02", 2, tmp_path / "FW02-R02", 1, "", "")
    assert entry2["terminal_reason"] == "NO_PILOT_META"
