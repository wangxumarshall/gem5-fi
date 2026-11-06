import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from terminal import classify  # noqa: E402


def test_four_dimensions_are_independent():
    r = classify(timed_out=False, simulator_error=False, exit_code=0, eligible=3,
                 injected=1, oracle_match=True, trace_complete=True,
                 squashed=False, detected=False, arch_state_bad=False)
    assert r == {"run_status": "COMPLETED", "fault_activation_status": "TRIGGERED",
                 "terminal_state": "MASKED", "trace_completeness": "COMPLETE"}


def test_no_eligible_keeps_not_triggered():
    r = classify(timed_out=False, simulator_error=False, exit_code=0, eligible=0,
                 injected=0, oracle_match=None, trace_complete=True)
    assert r["run_status"] == "NO_ELIGIBLE_EVENT"
    assert r["fault_activation_status"] == "NOT_TRIGGERED"


def test_incomplete_trace_is_never_masked():
    r = classify(timed_out=False, simulator_error=False, exit_code=0, eligible=3,
                 injected=1, oracle_match=True, trace_complete=False)
    assert r["terminal_state"] != "MASKED"
    assert r["terminal_state"] == "UNRESOLVED"
    assert r["trace_completeness"] == "INCOMPLETE"


def test_timeout_and_simulator_error_win_over_incomplete():
    assert classify(timed_out=True, eligible=2, injected=1)["terminal_state"] == "HANG"
    assert classify(simulator_error=True, eligible=2, injected=1)["terminal_state"] == "CRASH"


def test_squash_and_detected_are_evidence_based():
    assert classify(exit_code=0, eligible=2, injected=1, squashed=True,
                    trace_complete=False)["terminal_state"] == "SQUASHED"
    assert classify(exit_code=0, eligible=2, injected=1, detected=True,
                    trace_complete=False)["terminal_state"] == "DETECTED_CONTAINED"


def test_oracle_mismatch_is_sdc_and_arch_bad_without_mismatch_is_corruption():
    assert classify(exit_code=0, eligible=2, injected=1, oracle_match=False,
                    trace_complete=True)["terminal_state"] == "SDC"
    assert classify(exit_code=0, eligible=2, injected=1, oracle_match=True,
                    arch_state_bad=True, trace_complete=True)["terminal_state"] == "ARCH_STATE_CORRUPTION"


def test_unknown_activation_when_evidence_missing():
    r = classify(exit_code=0, eligible=2, injected=0, activation_evidence=False,
                 trace_complete=True)
    assert r["fault_activation_status"] == "UNKNOWN"
