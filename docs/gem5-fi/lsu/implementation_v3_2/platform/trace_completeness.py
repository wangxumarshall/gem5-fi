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
    # LP01 (v3.2.5): load-response data fault. SDC needs the delivered value
    # to reach the register and a consumer; a committed load with no consumer
    # is MASKED; a squashed response is SQUASHED.
    ("LP01", "SDC"): [("injection", "memory_response", "register_writeback",
                       "consumer_commit")],
    ("LP01", "MASKED"): [
        ("injection", "memory_response", "register_writeback"),
        ("injection", "memory_response"),
        ("injection", "squash"),
    ],
    ("LP01", "SQUASHED"): [("injection", "squash")],
    ("LP01", "CRASH"): [("injection", "simulator_abort")],
    ("LP01", "UNRESOLVED"): [("injection",)],
    # MD04 (v3.2.6): a suppressed store->load violation. The response may be
    # consumed before the violation check (late-bound writeback), so the
    # no-response alternative is legitimate and labelled.
    ("MD04", "SDC"): [
        ("injection", "memory_response", "register_writeback",
         "consumer_commit"),
        ("injection", "register_writeback", "consumer_commit"),
    ],
    ("MD04", "MASKED"): [
        ("injection", "memory_response", "register_writeback"),
        ("injection", "register_writeback"),
        ("injection",),
    ],
    ("MD04", "SQUASHED"): [("injection", "squash")],
    ("MD04", "UNRESOLVED"): [("injection",)],
    # FW05 (v3.2.7): wrong-source forwarding. The response is the forwarded
    # delivery; a committed load with no consumer is MASKED.
    ("FW05", "SDC"): [("injection", "forwarding_decision",
                       "register_writeback", "consumer_commit")],
    ("FW05", "MASKED"): [
        ("injection", "forwarding_decision", "register_writeback"),
        ("injection", "register_writeback"),
        ("injection", "squash"),
    ],
    ("FW05", "SQUASHED"): [("injection", "squash")],
    ("FW05", "UNRESOLVED"): [("injection",)],
    # SQ03 (v3.2.8): premature store writeback permission. The store-side
    # chain is injection -> writeback -> cache write -> completion; a later
    # load/consumer is required only for the SDC claim.
    ("SQ03", "SDC"): [("injection", "store_writeback", "store_mem_write",
                       "memory_response", "register_writeback",
                       "consumer_commit")],
    ("SQ03", "MASKED"): [
        ("injection", "store_writeback", "store_mem_write",
         "sq03_complete"),
        ("injection", "store_writeback", "store_mem_write"),
        ("injection", "store_writeback"),
        ("injection", "squash"),
    ],
    ("SQ03", "SQUASHED"): [("injection", "squash")],
    ("SQ03", "CRASH"): [("injection", "simulator_abort")],
    ("SQ03", "UNRESOLVED"): [("injection",)],
    # LQ04 (v3.2.10): LQ-entry lifetime corruption. The in-flight response
    # is bound by the request's senderState, so the unchanged data still
    # reaches the register and consumers; a committed load with no consumer
    # is MASKED; a squashed target closes the window at the squash boundary.
    ("LQ04", "MASKED"): [
        ("injection", "memory_response", "register_writeback",
         "consumer_commit"),
        ("injection", "memory_response", "register_writeback"),
        ("injection", "squash"),
    ],
    ("LQ04", "SQUASHED"): [("injection", "squash")],
    ("LQ04", "CRASH"): [("injection", "simulator_abort")],
    ("LQ04", "UNRESOLVED"): [("injection",)],
}
DEFAULT_PROFILE = {"A01": ("injection",), "A03": ("injection",),
                   "FW02": ("forwarding_decision",),
                   "DA04": ("injection",), "SQ01": ("injection",),
                   "LP01": ("injection",), "MD04": ("injection",),
                   "FW05": ("injection",), "SQ03": ("injection",),
                   "LQ04": ("injection",)}


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
    consumer_nodes = [e for e in chain
                      if e.get("event_type") == "consumer_commit"]
    # v3.2.5.1: operand records are not instructions. A multi-source
    # instruction can produce several matched consumer nodes.
    consumer_operand_records = len(consumer_nodes)
    consumer_instructions = len({e.get("dyn_inst_seq")
                                 for e in consumer_nodes
                                 if e.get("dyn_inst_seq") is not None})
    mismatch_records = sum(1 for e in chain
                           if e.get("event_type") == "taint_value_mismatch")
    stages = []
    for stage in ("injection", "address_formed", "memory_request",
                  "memory_response", "register_writeback",
                  "consumer_commit", "errant_commit", "forwarding_decision",
                  "replay", "squash", "simulator_abort",
                  "store_writeback", "store_mem_write", "sq_lifecycle",
                  "sq03_complete"):
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
    execution_attempt_link = "UNKNOWN"
    if inj is None:
        chain_reasons.append("no_injection_event")
    elif not chain_scoped:
        chain_reasons.append("no_chain_identity")
    else:
        by_type: dict[str, list[dict]] = {}
        for e in chain:
            by_type.setdefault(e.get("event_type"), []).append(e)

        # v3.2.7: an execution-attempt change is not by itself a broken chain
        # (a D-cache-blocked load is re-executed in place), but it may only
        # be stitched when the identity tuple agrees across attempts:
        # (dyn seq, LQ entry, entry generation, request id). Without that
        # evidence the chain is INCONCLUSIVE, never COMPLETE.
        def _num(value):
            try:
                return int(str(value), 0)
            except (TypeError, ValueError):
                return None

        fault_inst_kinds = {"memory_response", "register_writeback",
                            "commit", "errant_commit", "squash"}
        attempt_ids = {
            e.get("execution_attempt_id") for e in chain
            if e.get("execution_attempt_id") is not None
            and e.get("event_type") in fault_inst_kinds}
        if inj.get("execution_attempt_id") is not None:
            attempt_ids.add(inj.get("execution_attempt_id"))
        attempt_ids = sorted(attempt_ids)
        execution_attempt_link = "SAME_ATTEMPT"
        if len(attempt_ids) > 1:
            execution_attempt_link = "CROSS_ATTEMPT_VERIFIED"
            inj_detail = _d(inj.get("detail")) if inj else {}
            inj_lq = _num(inj.get("lq_entry_id")
                          or inj_detail.get("lq_entry_id")
                          or inj_detail.get("load_lq_entry_id"))
            inj_gen = _num(inj.get("entry_generation")
                           or inj_detail.get("lq_entry_generation")
                           or inj_detail.get("load_entry_generation"))
            inj_req = _num(inj_detail.get("load_request_id")
                           or inj.get("request_id"))
            for e in chain:
                if e.get("execution_attempt_id") in (
                        None, inj.get("execution_attempt_id")):
                    continue
                if e.get("event_type") not in fault_inst_kinds:
                    # Consumers are different dynamic instructions; their
                    # linkage is the propagation edge, not this identity.
                    continue
                ed = _d(e.get("detail"))
                same_seq = e.get("dyn_inst_seq") == inj.get("dyn_inst_seq")
                ev_lq = _num(e.get("lq_entry_id") or ed.get("lq_entry_id"))
                ev_gen = _num(e.get("entry_generation")
                              or ed.get("entry_generation")
                              or ed.get("lq_entry_generation"))
                ev_req = _num(e.get("request_id") or ed.get("request_id"))
                same_lq = ev_lq is None or inj_lq is None or ev_lq == inj_lq
                same_gen = (ev_gen is None or inj_gen is None
                            or ev_gen == inj_gen)
                # The response is the delivery event and must be tied by the
                # real request id; other same-instruction events may omit it.
                same_req = (ev_req is None
                            or (inj_req is not None and ev_req == inj_req))
                if e.get("event_type") == "memory_response":
                    same_req = (ev_req is not None and inj_req is not None
                                and ev_req == inj_req)
                if not (same_seq and same_lq and same_gen and same_req):
                    execution_attempt_link = "CROSS_ATTEMPT_UNVERIFIED"
                    chain_reasons.append("cross_attempt_without_identity")
                    break
            if (execution_attempt_link == "CROSS_ATTEMPT_VERIFIED"
                    and (inj_lq is None or inj_gen is None
                         or inj_req is None)):
                # The injection must expose the identity it is verified by.
                execution_attempt_link = "CROSS_ATTEMPT_UNVERIFIED"
                chain_reasons.append("cross_attempt_without_identity")
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
        # Pair each taint with the response it names (source_event_id is the
        # mapped JSONL event id). Comparing the last resp with the last taint
        # would mix two loads when a chain carries more than one.
        by_id = {e.get("event_id"): e for e in chain}
        for t in taints:
            src = t.get("source_event_id")
            r = by_id.get(src) if src is not None else None
            if r is None or r.get("event_type") != "memory_response":
                continue
            rh = _d(r.get("detail")).get("data_fnv")
            th = _d(t.get("detail")).get("source_value_hash")
            if rh and th and rh != th:
                chain_reasons.append("hash_discontinuity_resp_taint")
        # A consumer must be produced by an event on the same chain. The
        # source can be a taint_reg node, or a previous consumer node when
        # the destination register is re-tainted onward.
        chain_ids = {e.get("event_id") for e in chain}
        for c in by_type.get("consumer_commit", []):
            if c.get("source_event_id") not in chain_ids:
                chain_reasons.append("consumer_without_taint_edge")
        # v3.2.5 full continuity: writeback value hash → consumer input hash.
        wb_by_id = {e.get("event_id"): e for e in taints}
        for c in by_type.get("consumer_commit", []):
            src = c.get("source_event_id")
            w = wb_by_id.get(src)
            if w is None:
                continue
            wh = _d(w.get("detail")).get("writeback_value_fnv")
            ch = _d(c.get("detail")).get("consumer_input_fnv")
            if wh and ch and wh != ch:
                chain_reasons.append("hash_discontinuity_wb_consumer")
        # Payload → writeback: comparable only when the payload is exactly
        # the 8-byte register value. Other sizes are extended by completeAcc;
        # the trace records hash_basis and this check is skipped.
        for w in taints:
            wd = _d(w.get("detail"))
            if wd.get("family") == "l1d_fwd":
                if wd.get("hash_basis") == "payload_equals_regval" and \
                        wd.get("value_matches_payload") != "1":
                    chain_reasons.append("hash_discontinuity_payload_wb")
        sm = by_type.get("store_mem_write", [])
        if sm:
            dd = _d(sm[-1].get("detail"))
            if dd.get("family") == "byte_enable" and \
                    dd.get("disabled_unchanged") != "1":
                chain_reasons.append("byte_enable_not_applied")

        # DA04 v3.2.6: the load request/response/product chain must be linked
        # by real ids and ordered by real ticks. Store-side mem_req nodes are
        # excluded by dyn seq.
        if model_id == "DA04":
            load_reqs = [e for e in by_type.get("memory_request", [])
                         if e.get("dyn_inst_seq") != inj_seq]
            req_by_id = {}
            for e in load_reqs:
                rid = e.get("request_id")
                if rid is not None:
                    req_by_id.setdefault(rid, []).append(e)
            for r in by_type.get("memory_response", []):
                rid = r.get("request_id")
                cand = [e for e in req_by_id.get(rid, [])
                        if e.get("timestamp", 0) <= r.get("timestamp", 0)]
                if not cand:
                    chain_reasons.append("response_without_request")
                    continue
                m = max(cand, key=lambda e: e.get("timestamp", 0))
                md = _d(m.get("detail"))
                if md.get("candidate") == "0":
                    chain_reasons.append("response_request_not_causal")
                if m.get("dyn_inst_seq") != r.get("dyn_inst_seq"):
                    chain_reasons.append("response_dyn_seq_mismatch")
                sw = int(md.get("store_write_tick", "0") or 0)
                ls = int(md.get("last_send_tick", "0") or 0)
                if sw and ls and ls < sw:
                    chain_reasons.append("request_before_store_write")
            if sm and load_reqs:
                first_req = min(e.get("timestamp", 0) for e in load_reqs)
                if first_req < max(e.get("timestamp", 0) for e in sm):
                    chain_reasons.append("load_request_before_store_write_event")
            for w in taints:
                src = by_id.get(w.get("source_event_id"))
                if src and w.get("timestamp", 0) < src.get("timestamp", 0):
                    chain_reasons.append("writeback_before_response")

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
        "consumer_operand_records": consumer_operand_records,
        "consumer_instructions": consumer_instructions,
        "taint_value_mismatch_records": mismatch_records,
        "chain_integrity": chain_integrity,
        "chain_reasons": chain_reasons,
        "execution_attempt_link": execution_attempt_link,
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
