#!/usr/bin/env python3
"""LSU v3.3.3 final trace-closure collector.

Reads one merged evidence root (49 historical contexts + the 11 re-run
contexts), re-grades every context with ``lsu_v333_qualified`` and writes:

  * LSU_60Context_Final_Readiness.csv
  * LSU_11Context_Repair_Validation.csv

Honesty rules:
  * the grader's QUALIFIED / TRACE_INCOMPLETE status is never upgraded;
  * SP05's lost-writeback mechanism is reported as a valid terminal chain,
    but its frozen ``writeback_event`` field is still missing -> QUALIFIED;
  * RP01's flush record set is reported as complete, but the run is still
    TRACE_INCOMPLETE because the simulation stopped at the watchdog;
  * every row records its evidence root and binary SHA (mixed provenance is
    explicit, never hidden).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lsu_v333_qualified import QUALIFIED_MODELS, qualified_evidence  # noqa: E402

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05", "DA04",
          "LP01", "MD04", "LQ04", "RP01")
RESTRICTED = {("A03", "R02")}
RESTRICTED |= {("SP05", f"R0{i}") for i in range(1, 6)}
RESTRICTED |= {("RP01", f"R0{i}") for i in range(1, 6)}
VALID_TERMINALS = {"SDC", "MASKED", "SQUASHED", "HANG_WATCHDOG", "DETECTED",
                   "CRASH", "HANG_TIMEOUT"}


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _prop_rows(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {(r["ModelID"], r["ContextID"]): r for r in csv.DictReader(fh)}


def _valid_chain_class(prop: dict) -> str:
    terminal = (prop.get("Terminal") or "").strip()
    tc = (prop.get("TraceCompleteness") or "").strip()
    if not tc or tc.startswith("INCOMPLETE"):
        return "TRACE_INCOMPLETE"
    if terminal not in VALID_TERMINALS:
        return "QUALIFIED"
    # COMPLETE_CAUSAL_CHAIN is reserved for an SDC: the fault dataflow
    # reached the application terminal. MASKED / SQUASHED / HANG are valid
    # terminals with their own evidence, but they are NOT a complete
    # data-consumer chain (the user's v3.3.3 distinction).
    if tc.startswith("COMPLETE") and terminal == "SDC":
        return "COMPLETE_CAUSAL_CHAIN"
    if tc == "PARTIAL_WATCHDOG" or tc.startswith("COMPLETE"):
        return "VALID_TERMINAL_CHAIN"
    return "QUALIFIED"


def _row(model: str, ctx: str, run: Path, prop: dict,
         control: Path | None) -> dict:
    summary = _json(run / "summary.json")
    q = qualified_evidence(model, run) if model in QUALIFIED_MODELS else {
        "status": "PASS", "missing": [], "terminal_rule": "NO_EXTRA_RULES",
        "evidence": {},
    }
    qstatus = q.get("status") or "PASS"
    if qstatus == "TRACE_INCOMPLETE":
        chain_class = "TRACE_INCOMPLETE"
    elif qstatus == "QUALIFIED":
        chain_class = "QUALIFIED"
    elif qstatus == "PASS" and model in QUALIFIED_MODELS:
        chain_class = ("COMPLETE_CAUSAL_CHAIN"
                       if prop.get("Terminal") == "SDC"
                       else "VALID_TERMINAL_CHAIN")
    else:
        chain_class = _valid_chain_class(prop)

    csum = _json(control / "summary.json") if control else {}
    return {
        "ModelID": model,
        "ContextID": ctx,
        "RunID": f"{model}-{ctx}-fault",
        "EvidenceRoot": str(run),
        "BinarySHA256": summary.get("binary_sha"),
        "Terminal": prop.get("Terminal", summary.get("terminal")),
        "TerminalReason": prop.get("TerminalReason", summary.get("terminal_reason")),
        "ApplicationOracle": prop.get("ApplicationOracle",
                                      "PASS" if summary.get("oracle") is True
                                      else "FAIL" if summary.get("oracle") is False
                                      else "n/a"),
        "QualifiedStatus": qstatus,
        "MissingFields": ";".join(q.get("missing") or []),
        "ChainClass": chain_class,
        "TraceCompleteness": prop.get("TraceCompleteness", "n/a"),
        "Mechanism": prop.get("MaskingMechanism", "n/a"),
        "ControlRunID": f"{model}-{ctx}-control" if control else "n/a",
        "ControlInjectionCount": csum.get("injection_count", "n/a"),
        "ControlOracle": csum.get("oracle", "n/a"),
        "ControlZeroInjection": (
            "YES" if control and csum.get("injection_count") == 0 else
            "NO" if control else "n/a"),
        "EvidencePaths": prop.get("EvidencePaths", str(run)),
    }


def _validation_row(model: str, ctx: str, run: Path, prop: dict) -> dict:
    q = qualified_evidence(model, run)
    ev = q.get("evidence", {})
    detail = {}
    if model == "A03":
        detail = {
            "first_affected_dyn_seq": ev.get("first_affected_load_dyn_seq"),
            "first_affected_squash": ev.get("first_affected_squash"),
            "causal_anchor_dyn_seq": ev.get("causal_anchor_dyn_seq"),
            "causal_anchor_pc": ev.get("causal_anchor_pc"),
            "load_result": ev.get("load_result"),
            "register_writeback": ev.get("register_writeback"),
            "consumer": ev.get("consumer"),
            "checksum": ev.get("application_checksum"),
        }
    elif model == "SP05":
        detail = {
            "commit_event": ev.get("commit_event"),
            "commit_tick_source": ev.get("commit_tick_source"),
            "writeback_outcome": ev.get("writeback_outcome"),
            "writeback_suppressed": ev.get("writeback_suppressed"),
            "memory_visibility": ev.get("memory_visibility"),
            "reload": ev.get("reload"),
            "consumer": ev.get("consumer"),
            "application_oracle": ev.get("application_oracle"),
        }
    elif model == "RP01":
        detail = {
            "trace_flush_start": ev.get("trace_flush_start"),
            "watchdog_terminal": ev.get("watchdog_terminal"),
            "trace_flush_complete": ev.get("trace_flush_complete"),
            "flush_complete": ev.get("flush_complete"),
            "last_valid_event_id": ev.get("last_valid_event_id"),
            "terminal_source": ev.get("terminal_source"),
            "replay_eligibility": ev.get("replay_eligibility"),
            "replay_decision": ev.get("replay_decision"),
            "replay_skip": ev.get("replay_skip"),
        }
    return {
        "ModelID": model,
        "ContextID": ctx,
        "RunID": f"{model}-{ctx}-fault",
        "EvidenceRoot": str(run),
        "BinarySHA256": _json(run / "summary.json").get("binary_sha"),
        "Terminal": prop.get("Terminal"),
        "ApplicationOracle": prop.get("ApplicationOracle"),
        "QualifiedStatus": q.get("status"),
        "MissingFields": ";".join(q.get("missing") or []),
        "ChainClass": ("TRACE_INCOMPLETE" if q.get("status") == "TRACE_INCOMPLETE"
                       else "QUALIFIED" if q.get("status") == "QUALIFIED"
                       else "COMPLETE_CAUSAL_CHAIN"),
        "TraceCompleteness": prop.get("TraceCompleteness"),
        "RepairEvidence": json.dumps(detail, sort_keys=True),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, required=True,
                    help="merged 60-context evidence root")
    ap.add_argument("--propagation", type=Path, required=True,
                    help="LSU_60Context_Causal_Propagation_Final.csv")
    ap.add_argument("--out-readiness", type=Path, required=True)
    ap.add_argument("--out-validation", type=Path, required=True)
    args = ap.parse_args(argv)

    props = _prop_rows(args.propagation)
    rows = []
    validation = []
    for model in MODELS:
        for i in range(1, 6):
            ctx = f"R{i:02d}"
            run = args.runs / f"{model}-{ctx}-fault"
            control = args.runs / f"{model}-{ctx}-control"
            prop = props.get((model, ctx), {})
            if not run.is_dir():
                rows.append({
                    "ModelID": model, "ContextID": ctx,
                    "RunID": f"{model}-{ctx}-fault", "EvidenceRoot": "MISSING",
                    "BinarySHA256": "n/a", "Terminal": "UNRESOLVED",
                    "TerminalReason": "NO_RUN_DIRECTORY",
                    "ApplicationOracle": "n/a", "QualifiedStatus": "TRACE_INCOMPLETE",
                    "MissingFields": "run_dir", "ChainClass": "TRACE_INCOMPLETE",
                    "TraceCompleteness": "INCOMPLETE(no_run)", "Mechanism": "n/a",
                    "ControlRunID": "n/a", "ControlInjectionCount": "n/a",
                    "ControlOracle": "n/a", "ControlZeroInjection": "n/a",
                    "EvidencePaths": "n/a",
                })
                continue
            rows.append(_row(model, ctx, run, prop,
                             control if control.is_dir() else None))
            if (model, ctx) in RESTRICTED:
                validation.append(_validation_row(model, ctx, run, prop))

    args.out_readiness.parent.mkdir(parents=True, exist_ok=True)
    with args.out_readiness.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with args.out_validation.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(validation[0].keys()))
        w.writeheader()
        w.writerows(validation)

    from collections import Counter
    counts = Counter(r["ChainClass"] for r in rows)
    print(f"readiness rows: {len(rows)}")
    for key in ("COMPLETE_CAUSAL_CHAIN", "VALID_TERMINAL_CHAIN",
                "QUALIFIED", "TRACE_INCOMPLETE"):
        print(f"  {key}={counts.get(key, 0)}")
    print(f"repair validation rows: {len(validation)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
