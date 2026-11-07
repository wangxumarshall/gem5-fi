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
# Coverage is judged against this profile; the presence of any single stage is
# not enough. A missing required stage downgrades COMPLETE to PARTIAL.
PROFILES = {
    ("A01", "MASKED"): ("injection", "address_formed", "memory_request",
                        "memory_response", "register_writeback",
                        "consumer_commit"),
    ("A01", "SQUASHED"): ("injection", "address_formed", "memory_request",
                          "squash"),
    ("A01", "CRASH"): ("injection", "address_formed", "memory_request",
                       "simulator_abort"),
    ("A01", "SDC"): ("injection", "address_formed", "memory_request",
                     "memory_response", "register_writeback", "consumer_commit"),
    ("A03", "CRASH"): ("injection", "address_formed", "memory_request",
                       "simulator_abort"),
    ("A03", "SQUASHED"): ("injection", "address_formed", "memory_request",
                          "squash"),
    ("A03", "MASKED"): ("injection", "address_formed", "memory_request",
                        "memory_response", "register_writeback",
                        "consumer_commit"),
    ("FW02", "MASKED"): ("forwarding_decision", "memory_response",
                         "register_writeback", "consumer_commit"),
    ("FW02", "CRASH"): ("forwarding_decision", "memory_response",
                        "simulator_abort"),
    ("FW02", "SDC"): ("forwarding_decision", "memory_response",
                      "register_writeback", "consumer_commit"),
}
DEFAULT_PROFILE = {"A01": ("injection",), "A03": ("injection",),
                   "FW02": ("forwarding_decision",)}


def expected_stages(model_id: str | None, terminal: str | None) -> tuple[str, ...]:
    if (model_id, terminal) in PROFILES:
        return PROFILES[(model_id, terminal)]
    return DEFAULT_PROFILE.get(model_id or "", ("injection",))


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
    kinds = {e.get("event_type") for e in events}
    stages = []
    for stage in ("injection", "address_formed", "memory_request",
                  "memory_response", "register_writeback",
                  "consumer_commit", "errant_commit", "forwarding_decision",
                  "replay", "squash", "simulator_abort"):
        if stage in kinds:
            stages.append(stage)
    record_integrity = "INVALID" if errs else "VALID"
    # Coverage is an independent dimension: it is judged only against the
    # expected profile for (model, terminal), not against validation reasons.
    model_id = summary.get("fault_model_id")
    expected = expected_stages(model_id, terminal)
    missing = [s for s in expected if s not in kinds]
    if not kinds:
        coverage = "NONE"
    elif missing:
        coverage = "PARTIAL"
    else:
        coverage = "COMPLETE"
    return {
        "trace": str(path),
        "trace_completeness": trace_completeness,
        "record_integrity": record_integrity,
        "propagation_coverage": coverage,
        "propagation_stages": stages,
        "expected_stages": list(expected),
        "missing_stages": missing,
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
