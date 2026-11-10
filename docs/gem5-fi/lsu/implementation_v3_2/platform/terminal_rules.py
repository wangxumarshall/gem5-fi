"""Chain-scoped terminal adjudication (LSU v3.2.4).

Only events on the fault's own chain can justify a verdict. The chain is the
injection's ptag (store/load/consumer nodes) plus the fault instruction's own
dyn_inst_seq (commit/squash/lifecycle nodes are written with ptag=0).

A load that produced a response and a register writeback but was squashed
before commit is SQUASHED — the writeback never became architectural. This is
the FW02-R01/R05 defect this module fixes.
"""
from __future__ import annotations

LOAD_SIDE = ("A01", "A03", "FW02", "LP01", "MD04", "FW05", "LQ04")
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
    if model == "RP01" and observed_terminal == "TIMEOUT":
        # RP01 (v3.2.12): the run was cut by the external timeout around the
        # in-simulator watchdog window (design gate condition 4: the expected
        # terminal is HANG/TIMEOUT and the retained partial trace is
        # evidence). The observation is terminal for this model — no
        # downstream chain state (commit + consumer + a passing oracle) may
        # relabel it MASKED. Model-scoped: no other model's adjudication
        # changes.
        return "TIMEOUT", "RP01_EXTERNAL_TIMEOUT"
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
    if model == "SP05":
        # SP05's hook fires in writebackStores, i.e. after commitStores has
        # already granted canWB. The store is therefore committed by
        # construction; the commit trace node predates fault_seqs membership,
        # so absence of a commit node is not evidence of no commit.
        detail = injection.get("detail") or ""
        if "writebackStores_prematureComplete" in detail:
            committed = True
    squashed = any(e.get("event_type") == "squash" for e in own)
    if squashed and not committed:
        return "SQUASHED", "TARGET_SQUASHED_NO_COMMIT"

    if model in LOAD_SIDE:
        # v3.2.5: oracle failure alone is not SDC. The fault must have
        # reached the architectural register as a committed value.
        data_value = any(
            e.get("event_type") == "register_writeback"
            and e.get("new_value") not in (None, "")
            for e in chain)
        if not committed:
            return "UNRESOLVED", "TARGET_NOT_COMMITTED"
        if not data_value:
            return "UNRESOLVED", "UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE"
        if oracle_pass is False:
            return "SDC", "ORACLE_FAIL"
        return "MASKED", "TARGET_COMMITTED_DATA_VALUE_PRESENT"

    # Store-side (SQ01 / DA04): the faulting store must commit; a later load
    # consumer distinguishes "lane read" from "lane never read". v3.2.5:
    # an oracle failure without a causally attributable consumer is not SDC —
    # the checksum change has no supported path through the fault (the
    # v3.2.4 response-time attribution was the false positive this fixes).
    if not committed:
        return "UNRESOLVED", "STORE_NOT_COMMITTED"
    consumed = any(
        e.get("event_type") in ("consumer_commit", "errant_commit")
        and e.get("dyn_inst_seq") != seq
        for e in chain)
    if oracle_pass is False:
        if not consumed:
            return "UNRESOLVED", "ORACLE_FAIL_NO_CAUSAL_CONSUMER"
        return "SDC", "ORACLE_FAIL"
    return "MASKED", ("STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS"
                      if consumed else "STORE_COMMITTED_LANE_NOT_READ")
