#!/usr/bin/env python3
"""Evidence-completeness audit for the LSU v3.3.3 formal campaign.

Separates five independent questions that must not be conflated:

  TraceV31Status        converted trace file present/absent (A03/RP01: direct)
  RawPropTraceStatus    raw prop_trace.csv.gz present and decompressible
  RawTraceIntegrity     node_id order / terminal completeness
  PropagationCoverage   how much of the fault chain the raw trace carries
  CausalChainCompleteness final ChainClass (control runs are CONTROL)

Also emits the A03 injection-count semantics: the raw ``InjectionCount`` is a
persistent stuck-at stream-event count, not an independent-fault count.

Read-only over the campaign root; writes only the two CSV outputs.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03",
          "SP05", "DA04", "LP01", "MD04", "LQ04", "RP01")
TRACE_COLS = ("node_id", "tick", "ptag", "kind", "dyn_inst_seq",
              "request_id", "addr", "phys_reg", "arch_reg", "detail")
AUDIT_COLS = (
    "ModelID", "ContextID", "Role", "Attempt", "TraceV31Status",
    "RawPropTraceStatus", "RawTraceIntegrity", "PropagationCoverage",
    "CausalChainCompleteness", "Evidence",
)
A03_COLS = (
    "ModelID", "ContextID", "RawInjectionCount", "FaultStateActivationCount",
    "A03StreamEventCount", "AffectedAccessCount", "Interpretation", "Evidence",
)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _trace_rows(path: Path) -> list[dict] | None:
    """Return rows, or None when the gzip is absent/unreadable."""
    if not path.is_file():
        return None
    rows: list[dict] = []
    try:
        with gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if not line.strip() or line.startswith("#"):
                    continue
                values = next(csv.reader([line]))
                if len(values) < len(TRACE_COLS):
                    continue
                rows.append(dict(zip(TRACE_COLS, values)))
    except (OSError, EOFError):
        return None
    return rows


def _detail(row: dict, key: str) -> str | None:
    for part in (row.get("detail") or "").split(";"):
        if part.startswith(key + "="):
            return part.split("=", 1)[1]
    return None


def _integrity(rows: list[dict] | None, terminal: str) -> str:
    if rows is None:
        return "UNREADABLE"
    if not rows:
        return "EMPTY"
    nodes = []
    for row in rows:
        try:
            nodes.append(int(row["node_id"]))
        except ValueError:
            return "INVALID_NODE_ID"
    if nodes != sorted(nodes):
        return "NON_MONOTONIC"
    if terminal == "HANG_WATCHDOG":
        return "VALID_TERMINAL_COMPLETE"
    return "VALID"


def _driver_direct(model: str, role: str) -> bool:
    # mirrors tools/lsu_v332_matrix.py:driver_for
    return model == "RP01" or (model == "A03" and role == "fault")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--propagation", type=Path, required=True,
                    help="LSU_60Context_Causal_Propagation_Final.csv")
    ap.add_argument("--readiness", type=Path, required=True,
                    help="LSU_60Context_Final_Readiness.csv")
    ap.add_argument("--out", type=Path, required=True,
                    help="LSU_Evidence_Completeness_Audit.csv")
    ap.add_argument("--a03-out", type=Path, required=True,
                    help="LSU_A03_Injection_Count_Semantics.csv")
    args = ap.parse_args(argv)

    def load(path: Path, key=("ModelID", "ContextID")) -> dict:
        with path.open(encoding="utf-8", newline="") as fh:
            return {tuple(r[k] for k in key): r for r in csv.DictReader(fh)}

    prop = load(args.propagation)
    readiness = load(args.readiness)
    audit, a03 = [], []
    for model in MODELS:
        for ctx_index in range(1, 6):
            ctx = f"R{ctx_index:02d}"
            for role in ("fault", "control"):
                run = args.runs / f"{model}-{ctx}-{role}"
                canonical = _read_json(run / "canonical.json")
                attempt = canonical.get("attempt_id") or "attempt_001"
                evidence = run / "attempts" / attempt
                summary = _read_json(evidence / "summary.json")
                terminal = str(summary.get("terminal") or "n/a")
                direct = _driver_direct(model, role)
                v31 = (evidence / "trace_v31.jsonl").is_file()
                rows = _trace_rows(evidence / "prop_trace.csv.gz")
                if direct and not v31:
                    trace_status = "ABSENT_DIRECT_DRIVER"
                elif v31:
                    trace_status = "PRESENT"
                else:
                    trace_status = "MISSING_UNEXPECTED"
                raw_status = ("PRESENT_DECOMPRESSIBLE" if rows is not None
                              else "MISSING")
                integrity = _integrity(rows, terminal)
                key = (model, ctx)
                if role == "control":
                    coverage = "COMPLETE_CONTROL"
                    chain = "CONTROL"
                else:
                    coverage = (prop.get(key, {}).get("TraceCompleteness")
                                or "n/a")
                    chain = readiness.get(key, {}).get("ChainClass") or "n/a"
                audit.append({
                    "ModelID": model, "ContextID": ctx, "Role": role,
                    "Attempt": attempt, "TraceV31Status": trace_status,
                    "RawPropTraceStatus": raw_status,
                    "RawTraceIntegrity": integrity,
                    "PropagationCoverage": coverage,
                    "CausalChainCompleteness": chain,
                    "Evidence": str(evidence),
                })
                if model == "A03" and role == "fault":
                    stream = [r for r in (rows or [])
                              if r.get("kind") == "a03_stream"]
                    a03.append({
                        "ModelID": model, "ContextID": ctx,
                        "RawInjectionCount": summary.get("injection_count"),
                        "FaultStateActivationCount": sum(
                            1 for r in (rows or [])
                            if r.get("kind") == "a03_activation"),
                        "A03StreamEventCount": len(stream),
                        "AffectedAccessCount": sum(
                            1 for r in stream
                            if _detail(r, "affected") == "1"),
                        "Interpretation": (
                            "persistent stuck-at state; raw InjectionCount is "
                            "the stream-event count, not independent faults"),
                        "Evidence": str(evidence),
                    })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=AUDIT_COLS)
        writer.writeheader()
        writer.writerows(audit)
    args.a03_out.parent.mkdir(parents=True, exist_ok=True)
    with args.a03_out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=A03_COLS)
        writer.writeheader()
        writer.writerows(a03)
    print(f"wrote {len(audit)} audit rows to {args.out}")
    print(f"wrote {len(a03)} A03 rows to {args.a03_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
