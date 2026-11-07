#!/usr/bin/env python3
"""Convert a CHAOSPropagation CSV trace into Trace v3.1 JSONL.

The CSV is the gem5-side real trace (one row per propagation node). This
adapter preserves its node identity, dyn_inst_seq, request id, address and
detail fields, and emits the full v3.1 field set plus separate
``propagation_edge`` records. Fields gem5 does not expose (replay generation,
LQ/SQ entry generation, response id) are written as null, never guessed.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from trace_writer import TraceWriter  # noqa: E402

KIND_MAP = {
    "inj": "injection",
    "inj_nochange": "injection_nochange",
    "inj_store_data": "injection",
    "inj_store_be": "injection",
    "store_wb": "store_writeback",
    "store_mem": "store_mem_write",
    "addr_form": "address_formed",
    "mem_req": "memory_request",
    "resp": "memory_response",
    "taint_reg": "register_writeback",
    "consumer": "consumer_commit",
    "errant_commit": "errant_commit",
    "funnel": "funnel",
    "fwd": "forwarding_decision",
    "commit": "commit",
    "lq_lifecycle": "lq_lifecycle",
    "sq_lifecycle": "sq_lifecycle",
    "replay": "replay",
    "squash": "squash",
    "prop_edge": "propagation_edge",
}
UNIT_MAP = {
    "inj": ("AGU", "injection"),
    "inj_nochange": ("AGU", "injection_nochange"),
    "inj_store_data": ("SQ", "store_data"),
    "inj_store_be": ("SQ", "byte_enable"),
    "store_wb": ("SQ", "writeback"),
    "store_mem": ("L1D", "memory_write"),
    "addr_form": ("AGU", "effective_address"),
    "mem_req": ("LSQ", "request"),
    "resp": ("L1D", "response"),
    "taint_reg": ("RF", "writeback"),
    "consumer": ("Commit", "consumer"),
    "errant_commit": ("Commit", "errant_commit"),
    "funnel": ("Funnel", "counts"),
    "fwd": ("FWD", "Store-to-Load Forwarding"),
    "commit": ("Commit", "commit"),
    "lq_lifecycle": ("LSQ", "LQ lifecycle"),
    "sq_lifecycle": ("LSQ", "SQ lifecycle"),
    "replay": ("LSQ", "replay"),
    "squash": ("LSQ", "squash"),
}


def _detail(text: str) -> dict[str, str]:
    out = {}
    for item in (text or "").split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def _hex(value: str | None) -> str | None:
    if not value:
        return None
    value = value.lower()
    return value if value.startswith("0x") else "0x" + value


def _int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def convert(csv_path: Path, out_path: Path, *, sample_run_id: str, run_id: str,
            sub_task_id: str, fault_id: str, fault_model_id: str,
            run_status: str, activation: str, terminal: str,
            completeness: str, terminal_reason: str | None = None,
            observed_terminal: str | None = None,
            fault_causality: str | None = None,
            terminal_evidence: dict | None = None,
            no_summary: bool = False,
            allow_truncated_complete: bool = False) -> dict:
    rows = []
    truncated = False
    try:
        with gzip.open(csv_path, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                if not line.strip():
                    continue
                rows.append(next(csv.reader([line])))
    except (EOFError, OSError):
        truncated = True

    if allow_truncated_complete and terminal != "CRASH":
        raise SystemExit("REFUSE: a truncated stream may only be completed for CRASH")
    declared = "INCOMPLETE" if truncated and not allow_truncated_complete else completeness
    if not no_summary and declared == "INCOMPLETE" and terminal == "MASKED":
        raise SystemExit("REFUSE: incomplete trace cannot be MASKED")

    w = TraceWriter(out_path, sample_run_id, run_id, sub_task_id,
                    fault_id, fault_model_id)
    last_by_ptag: dict[int, int] = {}
    injection_by_ptag: dict[int, int] = {}
    node_to_event: dict[int, int] = {}
    next_injection = 0
    counts = {"events": 0, "edges": 0, "injections": 0, "activations": 0}
    for row in rows:
        if len(row) < 10:
            continue
        node_id, tick, ptag, kind, dyn_seq, req_id, addr, phys, arch, detail = row[:10]
        ptag_i = int(ptag or 0)
        kind = kind.strip()
        d = _detail(detail)
        if kind == "prop_edge":
            src = _int(d.get("source_event_id"))
            dst = _int(d.get("destination_event_id"))
            if src is None or dst is None or src not in node_to_event or dst not in node_to_event:
                continue
            w.edge(node_to_event[src], node_to_event[dst],
                   producer_inst_seq=_int(d.get("producer_inst_seq")),
                   consumer_inst_seq=_int(d.get("consumer_inst_seq")),
                   edge_kind=d.get("edge_type") or "data",
                   value_hash=(None if d.get("source_value_hash") in (None, "null")
                               else d.get("source_value_hash")),
                   source_value_hash=(None if d.get("source_value_hash") in (None, "null")
                                      else d.get("source_value_hash")),
                   destination_value_hash=(None if d.get("destination_value_hash") in (None, "null")
                                           else d.get("destination_value_hash")),
                   edge_type=d.get("edge_type"),
                   trace_completeness=("COMPLETE" if declared == "COMPLETE"
                                       else "INCOMPLETE"))
            continue
        old_addr = _hex(d.get("old_addr"))
        new_addr = _hex(d.get("new_addr")) or _hex(addr)
        injection_status = "NOT_APPLICABLE"
        if kind in ("inj", "inj_nochange", "inj_store_data", "inj_store_be"):
            injection_status = ("NO_CHANGE" if kind == "inj_nochange"
                                or d.get("value_changed") == "0"
                                else "INJECTED")
            next_injection += 1
            injection_by_ptag[ptag_i] = next_injection
        injection_event_id = injection_by_ptag.get(ptag_i, 1)
        activation_status = ("TRIGGERED"
                             if ptag_i > 0 or kind in ("inj", "inj_nochange",
                                                       "inj_store_data")
                             else "UNKNOWN")
        commit_status = ("COMMITTED" if kind in ("consumer", "errant_commit", "commit")
                         else "UNKNOWN")
        squash_status = "SQUASHED" if kind == "squash" else "UNKNOWN"
        unit, sub_unit = UNIT_MAP.get(kind, ("Unknown", kind))
        if kind in ("lq_lifecycle", "sq_lifecycle"):
            sub_unit = d.get("action") or kind
        # Address and data are separate fields. resp/t_aint carry actual
        # packet/writeback data; fwd carries the forwarded buffer.
        if kind == "resp":
            va, pa = None, _hex(addr)
            old_value = None
            new_value = d.get("data_hex") or d.get("data_fnv")
        elif kind in ("addr_form", "mem_req"):
            va, pa = _hex(addr), None
            old_value, new_value = old_addr, new_addr
        elif kind == "taint_reg":
            va, pa = None, None
            old_value = None
            new_value = d.get("writeback_value") or d.get("writeback_fnv")
        elif kind == "inj_store_data":
            va, pa = _hex(d.get("addr")), None
            old_value = d.get("old_byte")
            new_value = d.get("new_byte")
        elif kind == "inj_store_be":
            va, pa = _hex(d.get("addr_before")), None
            old_value = d.get("old_be")
            new_value = d.get("new_be")
        elif kind == "store_wb":
            va, pa = _hex(d.get("addr")), None
            old_value = None
            new_value = d.get("data_fnv")
        elif kind == "store_mem":
            va, pa = None, _hex(d.get("blk_addr"))
            old_value = d.get("before_hex")
            new_value = d.get("after_hex")
        elif kind in ("lq_lifecycle", "sq_lifecycle"):
            va, pa = None, None
            old_value, new_value = None, None
        elif kind == "fwd":
            va, pa = _hex(d.get("byte_begin")), None
            old_value = d.get("store_data_hex") or d.get("store_data_fnv")
            new_value = d.get("forward_data_hex") or d.get("forward_data_fnv")
        else:
            va, pa = None, None
            old_value, new_value = old_addr, new_addr
        parent = last_by_ptag.get(ptag_i)
        if ptag_i == 0:
            parent = None
        if kind == "consumer" and d.get("source_event_id") in node_to_event:
            parent = node_to_event[int(d["source_event_id"])]
        extra = {}
        if kind == "inj_store_be":
            extra = {
                "original_byte_enable": d.get("old_be"),
                "injected_byte_enable": d.get("new_be"),
                "changed_bit": _int(d.get("changed_bit")),
                "address_before": _hex(d.get("addr_before")),
                "address_after": _hex(d.get("addr_after")),
                "access_size_before": _int(d.get("size_before")),
                "access_size_after": _int(d.get("size_after")),
                "store_data_before": d.get("store_data_fnv"),
                "store_data_after": d.get("store_data_fnv"),
            }
        if kind == "fwd":
            extra = {
                "store_seq": _int(d.get("store_seq")),
                "load_seq": _int(d.get("load_seq")),
                "byte_begin": _hex(d.get("byte_begin")),
                "byte_end": _hex(d.get("byte_end")),
                "forward_decision": d.get("decision"),
                "normal_decision": d.get("normal_decision"),
                "fault_decision": d.get("fault_decision"),
                "memory_path": _int(d.get("memory_path")),
                "store_data_fnv": d.get("store_data_fnv"),
                "forward_data_fnv": d.get("forward_data_fnv"),
            }
        eid = w.event(
            KIND_MAP.get(kind, kind),
            parent_event_id=parent,
            injection_event_id=injection_event_id,
            dyn_inst_seq=_int(dyn_seq),
            execution_attempt_id=_int(d.get("execution_attempt_id")),
            replay_generation=_int(d.get("replay_generation")),
            commit_seq=_int(d.get("commit_seq")),
            timestamp=int(tick or 0),
            unit=unit, sub_unit=sub_unit,
            request_id=_int(d.get("request_id")) or _int(req_id),
            response_id=_int(d.get("response_id")),
            fragment_id=_int(d.get("fragment_id")),
            # CSV node ids are not JSONL event ids (rows can be skipped);
            # map through the converted node registry when possible.
            source_event_id=node_to_event.get(
                _int(d.get("source_event_id")),
                _int(d.get("source_event_id"))),
            destination_event_id=node_to_event.get(
                _int(d.get("destination_event_id")),
                _int(d.get("destination_event_id"))),
            lq_entry_id=(_int(d.get("index")) if kind == "lq_lifecycle"
                         else _int(d.get("lq_entry_id"))),
            sq_entry_id=(_int(d.get("index"))
                         if kind in ("sq_lifecycle", "inj_store_data")
                         else _int(d.get("sq_entry_id"))),
            # inj_store_be/store_wb carry sq_entry_id directly; the expression
            # above already reads it for every non-lifecycle kind.
            entry_generation=(_int(d.get("generation")) or
                              _int(d.get("entry_generation"))),
            va=va, pa=pa,
            old_value=old_value,
            new_value=new_value,
            injection_status=injection_status,
            activation_status=activation_status,
            commit_status=commit_status,
            squash_status=squash_status,
            trace_completeness="COMPLETE" if declared == "COMPLETE" else "INCOMPLETE",
            detail=detail,
            source_node_id=int(node_id or 0),
            ptag=ptag_i,
            **extra,
        )
        node_to_event[int(node_id or 0)] = eid
        prev = last_by_ptag.get(ptag_i)
        # consumer edges are emitted explicitly from taint-set dependencies;
        # do not manufacture a ptag-order edge for them.
        if prev is not None and ptag_i > 0 and kind not in ("consumer", "replay", "squash", "funnel"):
            w.edge(prev, eid, edge_kind=kind,
                   trace_completeness=("COMPLETE" if declared == "COMPLETE"
                                       else "INCOMPLETE"))
        last_by_ptag[ptag_i] = eid

    if not no_summary and terminal == "CRASH":
        # The simulator aborted before its normal trailer. Record the abort
        # itself as the terminal event, with the structured fault evidence,
        # so the terminal does not live only in stderr text.
        detail = ("gzip truncation observed" if truncated else
                  "simulator abort after last completed node")
        if terminal_evidence:
            detail += (";page_table_fault_addr={};last_injection_dyn_seq={}"
                       ";address_match={}").format(
                           terminal_evidence.get("page_table_fault_addr"),
                           terminal_evidence.get("last_injection_dyn_seq"),
                           terminal_evidence.get("address_match"))
        w.event("simulator_abort", unit="Simulator", sub_unit="abort",
                terminal_state="CRASH", commit_status="UNKNOWN",
                squash_status="UNKNOWN", trace_completeness=declared,
                fault_causality=fault_causality,
                terminal_evidence=terminal_evidence,
                detail=detail)
    if no_summary:
        w.abort()
        return {"rows": len(rows), "truncated": truncated, "summary": None}
    summary = w.close(run_status=run_status, activation=activation,
                      terminal=terminal, completeness=declared,
                      terminal_state_reason=terminal_reason,
                      observed_terminal=observed_terminal,
                      fault_causality=fault_causality,
                      terminal_evidence=terminal_evidence)
    return {"rows": len(rows), "truncated": truncated, "summary": summary}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv")
    ap.add_argument("out")
    ap.add_argument("--sample-run-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--sub-task-id", required=True)
    ap.add_argument("--fault-id", required=True)
    ap.add_argument("--fault-model-id", required=True)
    ap.add_argument("--run-status", required=True)
    ap.add_argument("--activation", required=True)
    ap.add_argument("--terminal", required=True)
    ap.add_argument("--completeness", required=True)
    ap.add_argument("--terminal-reason", default=None)
    ap.add_argument("--no-summary", action="store_true",
                    help="write events/edges only when the trace is incomplete")
    ap.add_argument("--allow-truncated-complete", action="store_true",
                    help="accept a gzip-truncated stream when a terminal CRASH "
                         "event is appended (abort is the terminal state)")
    args = ap.parse_args(argv)
    result = convert(
        Path(args.csv), Path(args.out),
        sample_run_id=args.sample_run_id, run_id=args.run_id,
        sub_task_id=args.sub_task_id, fault_id=args.fault_id,
        fault_model_id=args.fault_model_id, run_status=args.run_status,
        activation=args.activation, terminal=args.terminal,
        completeness=args.completeness, terminal_reason=args.terminal_reason,
        no_summary=args.no_summary,
        allow_truncated_complete=args.allow_truncated_complete)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
