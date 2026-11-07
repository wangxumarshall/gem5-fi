"""Chain-scoped terminal adjudication (LSU v3.2.4).

Only events on the fault's own chain can justify a verdict. The chain is the
injection's ptag (store/load/consumer nodes) plus the fault instruction's own
dyn_inst_seq (commit/squash/lifecycle nodes are written with ptag=0).

A load that produced a response and a register writeback but was squashed
before commit is SQUASHED — the writeback never became architectural. This is
the FW02-R01/R05 defect this module fixes.
"""
from __future__ import annotations

LOAD_SIDE = ("A01", "A03", "FW02")
HARD_TERMINALS = ("CRASH", "HANG", "ARCH_STATE_CORRUPTION",
                  "DETECTED_CONTAINED")


def chain_events(events: list[dict], injection: dict | None) -> list[dict]:
    if injection is None:
        return []
    ptag = injection.get("ptag")
    seq = injection.get("dyn_inst_seq")
    out = []
    for e in events:
        if ptag and e.get("ptag") == ptag:
            out.append(e)
        elif seq is not None and e.get("dyn_inst_seq") == seq:
            out.append(e)
    return out


def adjudicate(events: list[dict], *, model: str, observed_terminal: str,
               oracle_pass: bool | None, trace_complete: bool = True):
    """Return (terminal_state, terminal_state_reason)."""
    if observed_terminal in HARD_TERMINALS:
        return observed_terminal, None
    if not trace_complete:
        return "UNRESOLVED", "TRACE_INCOMPLETE"

    injection = None
    for e in events:
        if e.get("event_type") in ("injection", "injection_nochange"):
            injection = e
    if injection is None:
        return "UNRESOLVED", "NO_INJECTION_EVENT"

    seq = injection.get("dyn_inst_seq")
    chain = chain_events(events, injection)
    own = [e for e in chain if e.get("dyn_inst_seq") == seq]
    committed = any(e.get("event_type") in ("commit", "errant_commit")
                    for e in own)
    squashed = any(e.get("event_type") == "squash" for e in own)
    if squashed and not committed:
        return "SQUASHED", "TARGET_SQUASHED_NO_COMMIT"

    if oracle_pass is False:
        return "SDC", "ORACLE_FAIL"

    if model in LOAD_SIDE:
        data_value = any(
            e.get("event_type") in ("memory_response", "register_writeback")
            and e.get("new_value") not in (None, "")
            for e in own)
        if not committed:
            return "UNRESOLVED", "TARGET_NOT_COMMITTED"
        if not data_value:
            return "UNRESOLVED", "UNRESOLVED_NO_DATA_VALUE_EVIDENCE"
        return "MASKED", "TARGET_COMMITTED_DATA_VALUE_PRESENT"

    # Store-side (SQ01 / DA04): the faulting store must commit; a later load
    # consumer distinguishes "lane read" from "lane never read".
    if not committed:
        return "UNRESOLVED", "STORE_NOT_COMMITTED"
    consumed = any(
        e.get("event_type") in ("consumer_commit", "errant_commit")
        and e.get("dyn_inst_seq") != seq
        for e in chain)
    return "MASKED", ("STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS"
                      if consumed else "STORE_COMMITTED_LANE_NOT_READ")
