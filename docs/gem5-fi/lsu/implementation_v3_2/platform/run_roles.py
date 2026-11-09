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
