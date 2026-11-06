"""Four independent v3.1 terminal dimensions.

The classifier never lets a missing/incomplete trace masquerade as MASKED.
When the trace is incomplete and no other evidence exists, ``terminal_state``
is ``None``; the caller must record ``TraceCompleteness=INCOMPLETE`` and keep
the sample out of any Masked/SDC rate.  ``RunStatus`` and
``FaultActivationStatus`` remain usable in that case.
"""
from __future__ import annotations

RUN_STATUS = ("COMPLETED", "NO_ELIGIBLE_EVENT", "TIMEOUT", "SIMULATOR_ERROR")
ACTIVATION = ("NOT_TRIGGERED", "TRIGGERED", "UNKNOWN")
TERMINAL = ("MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "ARCH_STATE_CORRUPTION", "SDC", "CRASH", "HANG")
COMPLETENESS = ("COMPLETE", "INCOMPLETE")


def classify(*, exit_code: int | None = None, timed_out: bool = False,
             simulator_error: bool = False, eligible: int = 0,
             injected: int = 0, oracle_match: bool | None = None,
             squashed: bool = False, detected: bool = False,
             arch_state_bad: bool = False, trace_complete: bool = False,
             activation_evidence: bool = True) -> dict:
    """Classify one run into the four independent v3.1 dimensions."""
    if simulator_error:
        run_status = "SIMULATOR_ERROR"
    elif timed_out:
        run_status = "TIMEOUT"
    elif eligible == 0:
        run_status = "NO_ELIGIBLE_EVENT"
    else:
        run_status = "COMPLETED"

    if not activation_evidence:
        activation = "UNKNOWN"
    elif injected > 0:
        activation = "TRIGGERED"
    else:
        activation = "NOT_TRIGGERED"

    if simulator_error:
        terminal = "CRASH"
    elif timed_out:
        terminal = "HANG"
    elif exit_code not in (0, None):
        terminal = "CRASH"
    elif squashed:
        terminal = "SQUASHED"
    elif detected:
        terminal = "DETECTED_CONTAINED"
    elif oracle_match is False and exit_code == 0:
        terminal = "SDC"
    elif arch_state_bad:
        terminal = "ARCH_STATE_CORRUPTION"
    elif not trace_complete:
        # Honesty rule: no complete trace means no MASKED verdict.
        terminal = None
    else:
        terminal = "MASKED"

    return {
        "run_status": run_status,
        "fault_activation_status": activation,
        "terminal_state": terminal,
        "trace_completeness": "COMPLETE" if trace_complete else "INCOMPLETE",
    }
