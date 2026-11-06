"""Four independent status dimensions (v3.1)."""
from __future__ import annotations
from enum import Enum
class RunStatus(str,Enum): COMPLETED="COMPLETED"; NO_ELIGIBLE_EVENT="NO_ELIGIBLE_EVENT"; TIMEOUT="TIMEOUT"; SIMULATOR_ERROR="SIMULATOR_ERROR"
class FaultActivationStatus(str,Enum): NOT_TRIGGERED="NOT_TRIGGERED"; TRIGGERED="TRIGGERED"; UNKNOWN="UNKNOWN"
class TerminalState(str,Enum): MASKED="MASKED"; SQUASHED="SQUASHED"; DETECTED_CONTAINED="DETECTED_CONTAINED"; ARCH_STATE_CORRUPTION="ARCH_STATE_CORRUPTION"; SDC="SDC"; CRASH="CRASH"; HANG="HANG"
class TraceCompleteness(str,Enum): COMPLETE="COMPLETE"; INCOMPLETE="INCOMPLETE"

def classify(*, exit_code:int|None, timed_out:bool, simulator_error:bool,
             eligible:int, injected:int, oracle_match:bool|None,
             squashed:bool=False, detected:bool=False,
             arch_state_bad:bool=False, trace_complete:bool=False) -> dict:
    if simulator_error: run=RunStatus.SIMULATOR_ERROR
    elif timed_out: run=RunStatus.TIMEOUT
    elif eligible==0: run=RunStatus.NO_ELIGIBLE_EVENT
    else: run=RunStatus.COMPLETED
    act = FaultActivationStatus.NOT_TRIGGERED if injected==0 else FaultActivationStatus.TRIGGERED
    if not trace_complete:
        terminal=TerminalState.HANG if timed_out else TerminalState.MASKED
    elif squashed: terminal=TerminalState.SQUASHED
    elif detected: terminal=TerminalState.DETECTED_CONTAINED
    elif arch_state_bad and oracle_match is False: terminal=TerminalState.SDC
    elif arch_state_bad: terminal=TerminalState.ARCH_STATE_CORRUPTION
    elif exit_code not in (0,None): terminal=TerminalState.CRASH
    elif timed_out: terminal=TerminalState.HANG
    else: terminal=TerminalState.MASKED
    comp = TraceCompleteness.COMPLETE if trace_complete else TraceCompleteness.INCOMPLETE
    # Honesty rule: incomplete trace cannot be MASKED
    if comp is TraceCompleteness.INCOMPLETE and terminal is TerminalState.MASKED:
        terminal=TerminalState.ARCH_STATE_CORRUPTION if arch_state_bad else TerminalState.HANG
    return {"run_status":run.value,"fault_activation_status":act.value,
            "terminal_state":terminal.value,"trace_completeness":comp.value}
