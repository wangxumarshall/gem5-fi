"""No-fault control validity semantics (LSU v3.2.11 Task 4 / A4).

A matched no-fault control (``--probability 0.0``) is a record of absence:
the injector must not fire, the un-faulted workload must pass its oracle,
and the trace must still convert cleanly.  Before v3.2.11 the fault-run
acceptance expression was applied to controls too, so every healthy control
was written as ``accepted: false`` -- the A4 defect.  These tests pin the
corrected semantics: controls have their own validity gate
(``run_roles.control_valid``), their terminal honestly stays ``UNRESOLVED``
/ ``NO_INJECTION_EVENT`` (never ``MASKED``), their activation status is
``NOT_TRIGGERED``, and a valid control exits 0.

The synthetic records below are built through the same helpers ``run_pilot``
calls (``run_roles``, ``terminal_rules.adjudicate``,
``run_pilot._lq04_target_proof``); gem5 is never invoked.
"""
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
sys.path.insert(0, str(PLATFORM))

import run_pilot  # noqa: E402
import run_roles  # noqa: E402
import terminal_rules  # noqa: E402

PILOTS_V3_2_10 = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
                  / "pilots_v3_2_10")

# A committed, propagated-and-masked LQ04 fault chain, in the v3.1 JSONL
# event shape terminal_rules.adjudicate consumes.
FAULT_CHAIN_EVENTS = [
    {"record_type": "event", "event_type": "injection", "ptag": 7,
     "dyn_inst_seq": 42, "detail": ""},
    {"record_type": "event", "event_type": "commit", "ptag": 0,
     "dyn_inst_seq": 42, "detail": ""},
    {"record_type": "event", "event_type": "register_writeback", "ptag": 7,
     "dyn_inst_seq": 42, "detail": "", "new_value": "0xdeadbeef"},
]


def test_classify_run_role_boundaries():
    assert run_roles.classify_run_role(0.0) == "CONTROL"
    assert run_roles.classify_run_role(1.0) == "FAULT"
    # Boundary: any nonzero probability -- however small -- is a fault run.
    assert run_roles.classify_run_role(1e-9) == "FAULT"
    assert run_roles.classify_run_role(0.5) == "FAULT"
    # Boundary: a negative probability is never a control.
    assert run_roles.classify_run_role(-1e-9) == "FAULT"
    assert run_roles.classify_run_role(-0.5) == "FAULT"
    assert run_roles.classify_run_role(-1.0) == "FAULT"


def test_control_valid_accepts_clean_zero_injection_control():
    assert run_roles.control_valid(exit_code=0, oracle_pass=True,
                                   injection_count=0,
                                   trace_completeness="COMPLETE",
                                   validator_errors=[]) is True


def test_control_valid_rejects_nonzero_exit_code():
    assert run_roles.control_valid(exit_code=1, oracle_pass=True,
                                   injection_count=0,
                                   trace_completeness="COMPLETE",
                                   validator_errors=[]) is False
    # A signal-killed gem5 (negative returncode) is not a clean exit.
    assert run_roles.control_valid(exit_code=-11, oracle_pass=True,
                                   injection_count=0,
                                   trace_completeness="COMPLETE",
                                   validator_errors=[]) is False


def test_control_valid_rejects_oracle_failure():
    assert run_roles.control_valid(exit_code=0, oracle_pass=False,
                                   injection_count=0,
                                   trace_completeness="COMPLETE",
                                   validator_errors=[]) is False


def test_control_valid_rejects_any_injection():
    assert run_roles.control_valid(exit_code=0, oracle_pass=True,
                                   injection_count=1,
                                   trace_completeness="COMPLETE",
                                   validator_errors=[]) is False


def test_control_valid_requires_complete_trace():
    assert run_roles.control_valid(exit_code=0, oracle_pass=True,
                                   injection_count=0,
                                   trace_completeness="INCOMPLETE",
                                   validator_errors=[]) is False


def test_control_valid_requires_no_validator_errors():
    assert run_roles.control_valid(exit_code=0, oracle_pass=True,
                                   injection_count=0,
                                   trace_completeness="COMPLETE",
                                   validator_errors=["trace missing"]) is False


def _build_meta(*, probability, exit_code, oracle_pass, injected,
                trace_completeness, validator_errors,
                adjudication_events=(), target_proof_injections=()):
    """Mirror run_pilot.main's acceptance + meta wiring via its helpers.

    The expressions below replicate the v3.2.11 acceptance block (kept in
    lockstep by test_run_pilot_wires_roles_into_acceptance); the record
    shape is what run_pilot would write for these inputs.
    """
    crash_by_fault = False
    observed_terminal = "MASKED" if (exit_code == 0 and oracle_pass) else "SDC"
    activation = "TRIGGERED" if injected else "NOT_TRIGGERED"
    final_terminal, terminal_reason = terminal_rules.adjudicate(
        list(adjudication_events), model="LQ04",
        observed_terminal=observed_terminal, oracle_pass=oracle_pass,
        trace_complete=(trace_completeness == "COMPLETE"))
    if final_terminal == "UNRESOLVED" and terminal_reason is None:
        terminal_reason = "UNRESOLVED_NO_TERMINAL_EVIDENCE"
    target_proof = run_pilot._lq04_target_proof(
        list(target_proof_injections), None)
    run_role = run_roles.classify_run_role(probability)
    fault_valid = (
        (exit_code == 0 or crash_by_fault) and injected > 0
        and target_proof.get("events", 1) > 0
        and final_terminal not in (None, "UNRESOLVED")
        and not validator_errors
        and trace_completeness == "COMPLETE"
    )
    control_valid = (
        run_roles.control_valid(
            exit_code=exit_code, oracle_pass=oracle_pass,
            injection_count=injected,
            trace_completeness=trace_completeness,
            validator_errors=validator_errors)
        if run_role == "CONTROL" else False
    )
    return {
        "run_role": run_role,
        "exit_code": exit_code,
        "oracle_pass": oracle_pass,
        "injection_count": injected,
        "classification": {
            "fault_activation_status": activation,
            "observed_terminal": observed_terminal,
            "terminal_state": final_terminal,
            "terminal_state_reason": terminal_reason,
            "trace_completeness": trace_completeness,
            "oracle_outcome": "PASS" if oracle_pass else "FAIL",
        },
        "control_valid": (control_valid if run_role == "CONTROL" else "n/a"),
        "accepted": fault_valid or control_valid,
        "process_exit_code": 0 if (fault_valid or control_valid) else 1,
    }


def test_synthetic_control_meta_is_accepted():
    # The required inputs of a healthy matched no-fault control (the values
    # the real v3.2.10 LQ04 controls recorded): clean exit, oracle PASS,
    # zero injections, COMPLETE trace, no validator errors.
    meta = _build_meta(probability=0.0, exit_code=0, oracle_pass=True,
                       injected=0, trace_completeness="COMPLETE",
                       validator_errors=[])
    assert meta["run_role"] == "CONTROL"
    assert meta["control_valid"] is True
    assert meta["accepted"] is True
    # The process exit code becomes 0 for a valid control.
    assert meta["process_exit_code"] == 0
    # Honesty: the fault gates still reject this record on their own.
    cls = meta["classification"]
    assert cls["fault_activation_status"] == "NOT_TRIGGERED"
    assert cls["oracle_outcome"] == "PASS"
    # The terminal stays the honest UNRESOLVED/NO_INJECTION_EVENT --
    # acceptance never relabels a control as MASKED.
    assert cls["terminal_state"] == "UNRESOLVED"
    assert cls["terminal_state_reason"] == "NO_INJECTION_EVENT"
    assert cls["terminal_state"] != "MASKED"


def test_synthetic_control_meta_with_oracle_failure_is_not_accepted():
    # An oracle failure on an un-faulted run is an infrastructure problem
    # (golden mismatch), not SDC and not a valid control.
    meta = _build_meta(probability=0.0, exit_code=0, oracle_pass=False,
                       injected=0, trace_completeness="COMPLETE",
                       validator_errors=[])
    assert meta["run_role"] == "CONTROL"
    assert meta["control_valid"] is False
    assert meta["accepted"] is False
    assert meta["process_exit_code"] == 1
    cls = meta["classification"]
    assert cls["oracle_outcome"] == "FAIL"
    assert cls["fault_activation_status"] == "NOT_TRIGGERED"
    assert cls["terminal_state"] == "UNRESOLVED"
    assert cls["terminal_state_reason"] == "NO_INJECTION_EVENT"


def test_synthetic_fault_meta_keeps_fault_gates_and_na_control_field():
    meta = _build_meta(probability=1.0, exit_code=0, oracle_pass=True,
                       injected=1, trace_completeness="COMPLETE",
                       validator_errors=[],
                       adjudication_events=FAULT_CHAIN_EVENTS,
                       target_proof_injections=[{"kind": "injection",
                                                 "ordinal": 1}])
    assert meta["run_role"] == "FAULT"
    # Fault runs keep the fault gates; control_valid is reported as n/a.
    assert meta["control_valid"] == "n/a"
    assert meta["accepted"] is True
    assert meta["process_exit_code"] == 0
    cls = meta["classification"]
    assert cls["fault_activation_status"] == "TRIGGERED"
    assert cls["terminal_state"] == "MASKED"


def test_run_pilot_wires_roles_into_acceptance():
    src = inspect.getsource(run_pilot.main)
    # The role comes from the CLI probability via the shared classifier.
    assert "run_roles.classify_run_role(args.probability)" in src
    # Controls are gated by the shared control predicate.
    assert "run_roles.control_valid(" in src
    # Acceptance is the disjunction of the two role gates.
    assert "fault_valid or control_valid" in src
    # Every run records its role in pilot_meta.json.
    assert '"run_role": run_role' in src


def test_real_v3_2_10_controls_satisfy_the_control_gate():
    # Read-only grounding in the frozen v3.2.10 artifacts (never rewritten):
    # the recorded inputs of every real no-fault control are exactly what
    # run_roles.control_valid accepts, and the records already carry the
    # honest control fields.
    paths = sorted(PILOTS_V3_2_10.glob("LQ04-CONTROL-R*/pilot_meta.json"))
    assert len(paths) == 5
    for path in paths:
        meta = json.loads(path.read_text(encoding="utf-8"))
        assert run_roles.control_valid(
            exit_code=meta["exit_code"],
            oracle_pass=meta["oracle_pass"],
            injection_count=meta["injection_count"],
            trace_completeness=meta["classification"]["trace_completeness"],
            validator_errors=meta["trace"]["validator_errors"],
        ) is True, path.parent.name
        cls = meta["classification"]
        assert cls["fault_activation_status"] == "NOT_TRIGGERED"
        assert cls["oracle_outcome"] == "PASS"
        assert cls["terminal_state"] == "UNRESOLVED"
        assert cls["terminal_state_reason"] == "NO_INJECTION_EVENT"
