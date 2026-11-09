"""Run-role semantics for the LSU pilot platform (LSU v3.2.11 Task 4 / A4).

A pilot is either a FAULT run or a matched no-fault CONTROL, decided by the
CLI ``--probability``.  The two roles have different -- and equally strict --
validity semantics:

* FAULT: the injector must have fired and the record must carry a resolved
  terminal verdict (gated in ``run_pilot.main`` as ``fault_valid``).
* CONTROL: the injector must NOT have fired.  A control is valid when the
  process exited cleanly, the un-faulted workload passed its oracle, zero
  injections were recorded, and the converted trace is COMPLETE with no
  validator errors.

Acceptance is role-exclusive (``compute_acceptance``): a CONTROL is judged
only by the control gate and a FAULT run only by the fault gate.  Recorded
controller ruling (Task 4 fix loop): this supersedes the brief's literal
``fault_valid or control_valid`` disjunction, under which a CONTROL whose
injector misfired (``injection_count > 0`` -- reachable for ordinal-gated
injectors run with ``--probability 0.0``) could be accepted through the
fault criteria even though it is an invalid control.  A control is not a
fault run.

Before v3.2.11 the fault-run expression was applied to controls too, so a
perfectly healthy no-fault control was recorded as ``accepted: false`` (the
A4 defect).  A control is a record of absence: its honest terminal stays
``UNRESOLVED``/``NO_INJECTION_EVENT`` (never ``MASKED``) and its activation
status is ``NOT_TRIGGERED``; only its validity gate changes.
"""
from __future__ import annotations


def classify_run_role(probability: float) -> str:
    """Return "CONTROL" for a zero-probability run, "FAULT" otherwise."""
    return "CONTROL" if probability == 0.0 else "FAULT"


def control_valid(*, exit_code: int, oracle_pass: bool,
                  injection_count: int, trace_completeness: str,
                  validator_errors: list[str]) -> bool:
    """A matched no-fault control is valid iff nothing went wrong.

    True iff the process exited 0, the workload oracle passed, no injection
    was recorded, the converted trace is COMPLETE and the trace validator
    reported no errors.  Anything else (a crash, an oracle failure on the
    un-faulted run, an injector that fired anyway, a broken trace) makes
    the control record invalid.
    """
    return (exit_code == 0
            and oracle_pass is True
            and injection_count == 0
            and trace_completeness == "COMPLETE"
            and not validator_errors)


def compute_acceptance(run_role: str, fault_valid: bool,
                       control_valid: bool) -> bool:
    """Role-exclusive acceptance: each role is judged only by its own gate.

    A CONTROL is accepted iff ``control_valid`` -- it can never be accepted
    through the fault criteria, because a control whose injector (mis)fired
    is an invalid control, not a fault run.  Any other role (FAULT) is
    accepted iff ``fault_valid``; the control gate does not apply to it.

    Recorded controller ruling (Task 4 fix loop): this supersedes the
    brief's literal ``fault_valid or control_valid`` disjunction.
    """
    return control_valid if run_role == "CONTROL" else fault_valid
