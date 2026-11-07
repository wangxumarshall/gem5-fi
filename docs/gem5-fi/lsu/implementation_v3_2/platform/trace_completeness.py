"""Trace completeness checker.

A trace is COMPLETE only when it validates, has exactly one summary, and the
summary is internally consistent with the events (TRIGGERED requires an
injection event).  An incomplete trace never reports a terminal MASKED state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from trace_validator import read_records, validate

# Required propagation stages for a (fault model, observed terminal) pair.
# v3.2.4: each entry is a LIST of alternative profiles. Coverage is COMPLETE
# when ANY alternative is satisfied by events on the fault's own chain.
PROFILES = {
    ("A01", "MASKED"): [("injection", "address_formed", "memory_request",
                         "memory_response", "register_writeback",
                         "consumer_commit")],
    ("A01", "SQUASHED"): [("injection", "address_formed", "memory_request",
                           "squash")],
    ("A01", "CRASH"): [("injection", "address_formed", "memory_request",
                        "simulator_abort")],
    ("A01", "SDC"): [("injection", "address_formed", "memory_request",
                      "memory_response", "register_writeback",
                      "consumer_commit")],
    ("A03", "CRASH"): [("injection", "address_formed", "memory_request",
                        "simulator_abort")],
    ("A03", "SQUASHED"): [("injection", "address_formed", "memory_request",
                           "squash")],
    ("A03", "MASKED"): [("injection", "address_formed", "memory_request",
                         "memory_response", "register_writeback",
                         "consumer_commit")],
    ("FW02", "MASKED"): [("forwarding_decision", "memory_response",
                          "register_writeback", "consumer_commit")],
    ("FW02", "CRASH"): [("forwarding_decision", "memory_response",
                         "simulator_abort")],
    ("FW02", "SDC"): [("forwarding_decision", "memory_response",
                       "register_writeback", "consumer_commit")],
    # v3.2.4: a store-side chain must reach the actual cache write; a MASKED
    # store may instead be explained by forwarding (BE not applied) or by a
    # drain whose lane is never read.
    ("DA04", "SDC"): [("injection", "store_writeback", "store_mem_write",
                       "memory_response", "register_writeback",
                       "consumer_commit")],
    ("DA04", "MASKED"): [
        ("injection", "forwarding_decision"),
        ("injection", "store_writeback", "store_mem_write"),
        ("injection", "sq_lifecycle", "store_writeback"),
    ],
    ("DA04", "SQUASHED"): [("injection", "squash")],
    ("DA04", "UNRESOLVED"): [("injection",)],
    ("SQ01", "SDC"): [("injection", "store_writeback", "store_mem_write",
                       "memory_response", "register_writeback",
                       "consumer_commit")],
    ("SQ01", "MASKED"): [
        ("injection", "store_writeback", "store_mem_write"),
        ("injection", "forwarding_decision"),
        ("injection", "sq_lifecycle"),
    ],
    ("SQ01", "SQUASHED"): [("injection", "squash")],
    ("SQ01", "CRASH"): [("injection", "simulator_abort")],
}
DEFAULT_PROFILE = {"A01": ("injection",), "A03": ("injection",),
                   "FW02": ("forwarding_decision",),
                   "DA04": ("injection",), "SQ01": ("injection",)}


def expected_stages(model_id: str | None,
                    terminal: str | None) -> list[tuple[str, ...]]:
    """Return alternative stage profiles; COMPLETE if any one is satisfied."""
    value = PROFILES.get((model_id, terminal))
    if value is None:
        return [DEFAULT_PROFILE.get(model_id or "", ("injection",))]
    return value if isinstance(value, list) else [value]


def check_completeness(path: Path) -> dict:
    path = Path(path)
    reasons: list[str] = []
    errs = validate(path)
    if errs:
        reasons.append(f"validation failed: {len(errs)} error(s)")
        reasons.extend(errs[:20])
    records = [r for r in read_records(path) if "__parse_error__" not in r]
    events = [r for r in records if r.get("record_type") == "event"]
    edges = [r for r in records if r.get("record_type") == "propagation_edge"]
    summaries = [r for r in records if r.get("record_type") == "summary"]

    if len(summaries) != 1:
        reasons.append(f"expected one summary, got {len(summaries)}")
        summary = summaries[0] if summaries else {}
    else:
        summary = summaries[0]

    injections = [e for e in events
                  if e.get("injection_status") in ("INJECTED", "NO_CHANGE")
                  or e.get("event_type") == "injection"]
    activations = [e for e in events if e.get("activation_status") == "TRIGGERED"]
    if summary.get("fault_activation_status") == "TRIGGERED" and not injections:
        reasons.append("summary says TRIGGERED but no injection event exists")
    if summary.get("fault_activation_status") == "TRIGGERED" and not activations:
        reasons.append("summary says TRIGGERED but no activation event exists")

    declared = summary.get("trace_completeness")
    if declared == "INCOMPLETE":
        reasons.append("summary declares INCOMPLETE")
    terminal = summary.get("terminal_state")
    if declared == "INCOMPLETE" and terminal == "MASKED":
        reasons.append("incomplete trace declares MASKED (forbidden)")
        terminal = None

    trace_completeness = "COMPLETE" if not reasons and declared == "COMPLETE" else "INCOMPLETE"
    if trace_completeness == "INCOMPLETE" and terminal == "MASKED":
        reasons.append("downgraded: MASKED requires a complete trace")
        terminal = None
    # v3.2.4: coverage and integrity are judged on the fault's OWN chain.
    # chain = same ptag (store/load/consumer nodes) OR the fault instruction's
    # own dyn_inst_seq (commit/squash/lifecycle nodes carry ptag=0).
    injections_all = [e for e in events
                      if e.get("event_type") in ("injection",
                                                 "injection_nochange")
                      or e.get("injection_status") in ("INJECTED", "NO_CHANGE")]
    inj = injections_all[-1] if injections_all else None
    chain_ptag = inj.get("ptag") if inj else None
    inj_seq = inj.get("dyn_inst_seq") if inj else None
    chain_scoped = False
    if inj is None:
        # Legacy trace without an injection event: no chain identity exists;
        # stage presence is reported as a global observation, not a claim.
        chain = events
        chain_source = "none"
    elif chain_ptag:
        chain = [e for e in events
                 if e.get("ptag") == chain_ptag
                 or (inj_seq is not None
                     and e.get("dyn_inst_seq") == inj_seq)]
        chain_scoped = True
        chain_source = "ptag"
    else:
        chain = [e for e in events
                 if inj_seq is not None and e.get("dyn_inst_seq") == inj_seq]
        chain_source = "dyn_seq"
    kinds = {e.get("event_type") for e in chain}
    stages = []
    for stage in ("injection", "address_formed", "memory_request",
                  "memory_response", "register_writeback",
                  "consumer_commit", "errant_commit", "forwarding_decision",
                  "replay", "squash", "simulator_abort",
                  "store_writeback", "store_mem_write", "sq_lifecycle"):
        if stage in kinds:
            stages.append(stage)
    record_integrity = "INVALID" if errs else "VALID"
    # Coverage is judged only against the expected profile for (model,
    # terminal), using chain events only.
    model_id = summary.get("fault_model_id")
    alternatives = expected_stages(model_id, terminal)

    def _missing(alt):
        return [s for s in alt if s not in kinds]

    best_alt = min(alternatives, key=lambda alt: len(_missing(alt)))
    missing = _missing(best_alt)
    if not kinds:
        coverage = "NONE"
    elif missing:
        coverage = "PARTIAL"
    else:
        coverage = "COMPLETE"

    # Chain integrity: real correlation, not a same-trace concatenation.
    def _d(detail):
        return dict(item.split("=", 1) for item in (detail or "").split(";")
                    if "=" in item)

    chain_reasons: list[str] = []
    if inj is None:
        chain_reasons.append("no_injection_event")
    elif not chain_scoped:
        chain_reasons.append("no_chain_identity")
    else:
        by_type: dict[str, list[dict]] = {}
        for e in chain:
            by_type.setdefault(e.get("event_type"), []).append(e)
        for t in ("store_writeback", "store_mem_write"):
            for e in by_type.get(t, []):
                if e.get("dyn_inst_seq") != inj_seq:
                    chain_reasons.append(f"{t}_seq_mismatch")
        # A load-side model's own response legitimately carries the faulting
        # instruction's seq; only a STORE-side chain must never do so.
        if model_id in ("DA04", "SQ01"):
            for e in by_type.get("memory_response", []):
                if e.get("dyn_inst_seq") == inj_seq:
                    chain_reasons.append("response_on_store_seq")
        resp = by_type.get("memory_response", [])
        taints = by_type.get("register_writeback", [])
        if resp and taints:
            rh = _d(resp[-1].get("detail")).get("data_fnv")
            th = _d(taints[-1].get("detail")).get("source_value_hash")
            if rh and th and rh != th:
                chain_reasons.append("hash_discontinuity_resp_taint")
        # A consumer must be produced by an event on the same chain. The
        # source can be a taint_reg node, or a previous consumer node when
        # the destination register is re-tainted onward.
        chain_ids = {e.get("event_id") for e in chain}
        for c in by_type.get("consumer_commit", []):
            if c.get("source_event_id") not in chain_ids:
                chain_reasons.append("consumer_without_taint_edge")
        sm = by_type.get("store_mem_write", [])
        if sm:
            dd = _d(sm[-1].get("detail"))
            if dd.get("family") == "byte_enable" and \
                    dd.get("disabled_unchanged") != "1":
                chain_reasons.append("byte_enable_not_applied")

    if inj is None or not chain_scoped:
        # No chain identity (legacy trace): coverage is a global observation,
        # never a claim that the fault's own chain is complete.
        chain_integrity = "UNKNOWN"
    else:
        chain_integrity = "PASS" if not chain_reasons else "FAIL"
    chain_reasons = sorted(set(chain_reasons))
    if chain_integrity == "FAIL":
        coverage = "PARTIAL" if coverage != "NONE" else "NONE"

    return {
        "trace": str(path),
        "trace_completeness": trace_completeness,
        "record_integrity": record_integrity,
        "propagation_coverage": coverage,
        "propagation_stages": stages,
        "expected_stages": list(best_alt),
        "missing_stages": missing,
        "chain_ptag": chain_ptag,
        "chain_scoped": chain_scoped,
        "chain_source": chain_source,
        "chain_events": len(chain),
        "chain_integrity": chain_integrity,
        "chain_reasons": chain_reasons,
        "terminal_state": terminal,
        "run_status": summary.get("run_status"),
        "fault_activation_status": summary.get("fault_activation_status"),
        "events": len(events),
        "edges": len(edges),
        "injections": len(injections),
        "activations": len(activations),
        "reasons": reasons,
    }


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: trace_completeness.py <trace.jsonl[.gz]>", file=sys.stderr)
        return 2
    report = check_completeness(Path(argv[0]))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["trace_completeness"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
