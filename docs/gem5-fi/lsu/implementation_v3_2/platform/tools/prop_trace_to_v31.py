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
    "addr_form": "address_formed",
    "mem_req": "memory_request",
    "resp": "memory_response",
    "taint_reg": "register_writeback",
    "consumer": "consumer_commit",
    "errant_commit": "errant_commit",
    "funnel": "funnel",
}
UNIT_MAP = {
    "inj": ("AGU", "injection"),
    "addr_form": ("AGU", "effective_address"),
    "mem_req": ("LSQ", "request"),
    "resp": ("L1D", "response"),
    "taint_reg": ("RF", "writeback"),
    "consumer": ("Commit", "consumer"),
    "errant_commit": ("Commit", "errant_commit"),
    "funnel": ("Funnel", "counts"),
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
    next_injection = 0
    counts = {"events": 0, "edges": 0, "injections": 0, "activations": 0}
    for row in rows:
        if len(row) < 10:
            continue
        node_id, tick, ptag, kind, dyn_seq, req_id, addr, phys, arch, detail = row[:10]
        ptag_i = int(ptag or 0)
        kind = kind.strip()
        d = _detail(detail)
        old_addr = _hex(d.get("old_addr"))
        new_addr = _hex(d.get("new_addr")) or _hex(addr)
        injection_status = "NOT_APPLICABLE"
        if kind == "inj":
            injection_status = ("NO_CHANGE" if d.get("value_changed") == "0"
                                else "INJECTED")
            next_injection += 1
            injection_by_ptag[ptag_i] = next_injection
        injection_event_id = injection_by_ptag.get(ptag_i, 1)
        activation_status = "TRIGGERED" if ptag_i > 0 else "UNKNOWN"
        commit_status = "COMMITTED" if kind in ("consumer", "errant_commit") else "UNKNOWN"
        unit, sub_unit = UNIT_MAP.get(kind, ("Unknown", kind))
        # CHAOSPropagation writes a virtual address for addr_form/mem_req and
        # a physical packet address for resp. Keep them in separate fields.
        if kind == "resp":
            va, pa = None, _hex(addr)
        elif kind in ("addr_form", "mem_req"):
            va, pa = _hex(addr), None
        else:
            va, pa = None, None
        eid = w.event(
            KIND_MAP.get(kind, kind),
            parent_event_id=last_by_ptag.get(ptag_i),
            injection_event_id=injection_event_id,
            dyn_inst_seq=_int(dyn_seq),
            timestamp=int(tick or 0),
            unit=unit, sub_unit=sub_unit,
            request_id=_int(req_id),
            va=va, pa=pa,
            old_value=old_addr,
            new_value=new_addr,
            injection_status=injection_status,
            activation_status=activation_status,
            commit_status=commit_status,
            squash_status="UNKNOWN",
            trace_completeness="COMPLETE" if declared == "COMPLETE" else "INCOMPLETE",
            detail=detail,
            source_node_id=int(node_id or 0),
            ptag=ptag_i,
        )
        prev = last_by_ptag.get(ptag_i)
        if prev is not None:
            w.edge(prev, eid, edge_kind=kind,
                   trace_completeness=("COMPLETE" if declared == "COMPLETE"
                                       else "INCOMPLETE"))
        last_by_ptag[ptag_i] = eid

    if not no_summary and terminal == "CRASH":
        # The simulator aborted before its normal trailer. Record the abort
        # itself as the terminal event so the trace ends at the observed
        # terminal state instead of silently stopping mid-chain.
        w.event("simulator_abort", unit="Simulator", sub_unit="abort",
                terminal_state="CRASH", commit_status="UNKNOWN",
                squash_status="UNKNOWN", trace_completeness=declared,
                detail=("gzip truncation observed" if truncated else
                        "simulator abort after last completed node"))
    if no_summary:
        w.abort()
        return {"rows": len(rows), "truncated": truncated, "summary": None}
    summary = w.close(run_status=run_status, activation=activation,
                      terminal=terminal, completeness=declared,
                      terminal_state_reason=terminal_reason)
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
