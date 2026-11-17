#!/usr/bin/env python3
"""One-pass final closure helpers for LSU When-v2.

Pure, read-only classification of the existing hardened evidence plus a full
(non-truncated) target-chain edge exporter.  It never writes into results/ or
results_hardened/.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/sdc/gem5-fi-LSU")
REPO = ROOT / "repo"
sys.path.insert(0, str(ROOT / "runner"))

import evidence_hardening as eh  # noqa: E402

MODELS = ("A01", "A03", "LQ04", "SQ01", "SQ03", "SP05",
          "FW02", "FW05", "MD04", "RP01", "DA04", "LP01")
FAMILY = {"A01": "agu", "A03": "agu", "LQ04": "lq", "SQ01": "sq",
          "SQ03": "sq", "SP05": "sq", "FW02": "fwd_full",
          "FW05": "fwd_partial", "MD04": "md", "RP01": "md",
          "DA04": "align", "LP01": "lp"}
MECHANISM = {
    "A01": "A01_ADDRESS_BIT", "A03": "A03_STUCK_BIT",
    "LQ04": "LQ04_INVALIDATION", "SQ01": "SQ01_STORE_DATA",
    "SQ03": "SQ03_WRITEBACK_ELIGIBILITY",
    "SP05": "SP05_PREMATURE_COMPLETE", "FW02": "FW02_FORWARD_SUPPRESSED",
    "FW05": "FW05_OLDER_SOURCE", "MD04": "MD04_VIOLATION_TRIGGER",
    "RP01": "RP01_REPLAY_SUPPRESSED", "DA04": "DA04_BYTE_ENABLE",
    "LP01": "LP01_L1D_FORWARD_DATA",
}


def sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def pct(x: bool) -> str:
    return "YES" if x else "NO"


def parse_detail(detail: str | None) -> dict:
    out = {}
    for part in (detail or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def squash_info(ev: dict) -> dict:
    b = ev.get("BoundaryEvidence") or {}
    sq = (b.get("target_squash") or [{}])[0]
    d = parse_detail(sq.get("detail"))
    return {
        "target_squashed": bool(b.get("target_squash")),
        "target_commit": bool(b.get("target_commit") or b.get("target_lq_commit")),
        "squash_event_id": sq.get("event_id"),
        "squash_seq": sq.get("dyn_inst_seq"),
        "squash_cause": d.get("squash_cause", ""),
        "fault_caused_squash": d.get("fault_caused", ""),
    }


def classify(ev: dict) -> dict:
    """Return one authoritative set of dimensions for one fault."""
    model = ev.get("ModelID")
    a03 = ev.get("A03Semantics") or {}
    sq = ev.get("SQ01Semantics") or {}
    rp = ((ev.get("InjectionEffectiveEvidence") or {}).get("rp01") or {})
    b = ev.get("BoundaryEvidence") or {}
    si = squash_info(ev)
    terminal = (ev.get("SoftwareOracle") or {}).get("terminal")
    present = set(ev.get("PresentStages") or [])
    missing = set(ev.get("MissingStages") or [])
    inj = ev.get("InjectionEvent") or {}
    edge_count = int(ev.get("PropagationEdgeCount") or 0)
    checks = rp.get("checks") or {}
    rp_ok = bool(checks) and all(checks.values())

    triggered = bool(inj) and (ev.get("TraceCompleteness") == "COMPLETE")
    value_changed = bool((ev.get("InjectionEffectiveEvidence") or {}).get(
        "value_changed"))
    detail = str(inj.get("detail") or "")
    pevents = ev.get("PropagationEvents") or []
    types = {e.get("event_type") for e in pevents}
    pe_detail = " ".join(str(e.get("detail") or "") for e in pevents)
    effective_evidence = ""
    if model == "FW02":
        effective = ("fault_decision=suppressed" in pe_detail or
                     "fault_decision=suppressed" in detail)
        effective_evidence = "fw02_decision/forwarding_decision suppression"
    elif model == "FW05":
        effective = value_changed or "data_differs=1" in detail
        effective_evidence = "wrong source selected; data_differs"
    elif model == "RP01":
        effective = rp_ok
        effective_evidence = "RP01 A-E checks"
    elif model == "A03":
        effective = (a03.get("reason") == "ALREADY_STUCK" or value_changed)
        effective_evidence = "A03 stream affected/ALREADY_STUCK"
    elif model == "LQ04":
        effective = "valid_after=0" in detail or value_changed
        effective_evidence = "LQ valid/request invalidation"
    elif model == "SQ03":
        effective = "canwb_after" in detail or value_changed
        effective_evidence = "canWB writeback eligibility"
    elif model == "SP05":
        effective = "completed_after=1" in detail or value_changed
        effective_evidence = "premature completion flag"
    elif model == "MD04":
        effective = "checkViolations" in detail or "fault_model=MD04" in detail
        effective_evidence = "checkViolations violation event"
    elif model == "DA04":
        effective = "old_be" in detail or value_changed
        effective_evidence = "byte-enable bit change"
    else:
        effective = value_changed and model in MECHANISM
        effective_evidence = "decoded value change"
    propagation = edge_count > 0 or (model == "RP01" and rp_ok)
    target_commit = si["target_commit"]
    target_squash = si["target_squashed"]
    fault_caused = si["fault_caused_squash"] == "1"

    limitations = []
    unresolved = []
    complete = False

    if not triggered:
        unresolved.append("no complete trace/injection evidence")
    elif model == "A03" and a03.get("target_value_unchanged"):
        limitations.append(
            "ALREADY_STUCK target: persistent F5 fault affects later loads; "
            "the selected target value did not change")
    elif model == "RP01":
        if rp_ok:
            limitations.append(
                "watchdog/replay suppression; no per-cycle ROB/IQ; "
                "injection is a stdout-ledger bridge, not a raw-trace event")
        else:
            unresolved.append("RP01 A-E checks not all true")
    elif model == "SQ01" and (
            sq.get("chain_verdict") == "STORE_COMMITTED_LANE_NOT_READ" or
            (sq.get("consumer_load_commits") and
             "consumer_commit" not in present)):
        limitations.append(
            "SQ01 store-specific observation boundary: store lane not read "
            "or downstream consumer outside the store-side tracer")
    elif target_squash:
        if target_commit:
            limitations.append(
                "both target squash and target commit present; boundary ambiguous")
        elif not effective:
            limitations.append("target squash without a fault-effect record")
        else:
            # The target never becomes architectural.  A younger dependent
            # cannot commit before its producer; the squash flushes the target
            # and younger instructions.  The six records additionally have
            # squash_cause=unrelated/fault_caused=0, which is recorded while
            # still allowing causal closure of the fault path.
            complete = True
    elif target_commit:
        if terminal == "NO_VISIBLE_MISMATCH" and "consumer_commit" in missing:
            limitations.append(
                "target committed but no architectural consumer record exists; "
                "masked outcome terminates at the commit boundary")
        else:
            complete = True
    elif model == "RP01" and rp_ok:
        limitations.append("watchdog boundary without commit")
    else:
        unresolved.append("no target commit/squash/watchdog boundary")

    if terminal not in ("SDC", "NO_VISIBLE_MISMATCH", "HANG_WATCHDOG"):
        unresolved.append(f"unexpected terminal outcome {terminal}")
    if target_commit and "commit" not in present:
        unresolved.append("target_commit true but PresentStages lacks commit")
    if complete and limitations:
        unresolved.append("internal classification contradiction")
        complete = False

    if unresolved:
        status = "UNRESOLVED"
        complete = False
    elif limitations:
        status = "COMPLETE_WITH_DOCUMENTED_LIMITATION"
    else:
        status = "COMPLETE"

    return {
        "RunID": ev.get("RunID"), "ModelID": model,
        "ContextID": ev.get("ContextID"), "TimingID": ev.get("TimingID"),
        "FAULT_TRIGGERED": pct(triggered),
        "FAULT_EFFECTIVE": pct(effective),
        "EFFECTIVE_EVIDENCE": effective_evidence,
        "TARGET_VALUE_CHANGED": pct(value_changed),
        "PROPAGATION_OBSERVED": pct(propagation),
        "TARGET_COMMITTED": pct(target_commit),
        "TARGET_SQUASHED": pct(target_squash),
        "FAULT_CAUSED_SQUASH": pct(fault_caused),
        "TERMINAL_OUTCOME": terminal,
        "CHAIN_COMPLETE": pct(status == "COMPLETE"),
        "CHAIN_LIMITATION": pct(status ==
                               "COMPLETE_WITH_DOCUMENTED_LIMITATION"),
        "CHAIN_UNRESOLVED": pct(status == "UNRESOLVED"),
        "FINAL_CLASS": status,
        "MECHANISM": MECHANISM.get(model),
        "TARGET_SEQ": (ev.get("TargetIdentity") or {}).get("target_seq"),
        "INJECTION_EVENT_ID": inj.get("event_id"),
        "INJECTION_TYPE": inj.get("event_type"),
        "BOUNDARY_CLASS": b.get("boundary_class"),
        "SQUASH_EVENT_ID": si["squash_event_id"],
        "SQUASH_SEQ": si["squash_seq"],
        "SQUASH_CAUSE": si["squash_cause"],
        "SQUASH_ISOLATES_TARGET": pct(target_squash and not target_commit),
        "PROPAGATION_EDGE_COUNT": edge_count,
        "LIMITATION_REASON": " | ".join(limitations),
        "UNRESOLVED_REASON": " | ".join(unresolved),
    }


def export_full_edges(ev: dict, trace: Path, out_path: Path) -> dict:
    """Export every target-chain edge; no 200-edge cap.  Preview is separate."""
    events, edges, summary = eh.read_records(trace)
    ids = ev.get("TargetIdentity") or {}
    inj_id = (ev.get("InjectionEvent") or {}).get("event_id")
    inj = next((e for e in events if e.get("event_id") == inj_id), None)
    if inj is None:
        chain_edges = []
        target_ids = set()
    else:
        chain = [e for e in events if eh.in_chain(e, inj, ids)]
        target_ids = {e.get("event_id") for e in chain}
        chain_edges = [e for e in edges
                       if e.get("source_event_id") in target_ids and
                       e.get("destination_event_id") in target_ids]
    by_id = {e.get("event_id"): e for e in events}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "RunID", "EdgeID", "FromEvent", "ToEvent", "EdgeKind",
            "ProducerSeq", "ConsumerSeq", "FromType", "ToType",
            "FromSeq", "ToSeq", "FromDetail", "ToDetail"])
        w.writeheader()
        for e in chain_edges:
            a = by_id.get(e.get("source_event_id")) or {}
            z = by_id.get(e.get("destination_event_id")) or {}
            w.writerow({
                "RunID": ev.get("RunID"),
                "EdgeID": e.get("propagation_edge_id"),
                "FromEvent": e.get("source_event_id"),
                "ToEvent": e.get("destination_event_id"),
                "EdgeKind": e.get("edge_kind"),
                "ProducerSeq": e.get("producer_inst_seq"),
                "ConsumerSeq": e.get("consumer_inst_seq"),
                "FromType": a.get("event_type"), "ToType": z.get("event_type"),
                "FromSeq": a.get("dyn_inst_seq"), "ToSeq": z.get("dyn_inst_seq"),
                "FromDetail": a.get("detail"), "ToDetail": z.get("detail"),
            })
    preview = chain_edges[:200]
    return {
        "full_count": len(chain_edges),
        "preview_count": len(preview),
        "preview_sha": hashlib.sha256(
            json.dumps(preview, sort_keys=True).encode()).hexdigest(),
        "full_sha": sha256(out_path),
        "target_ids": len(target_ids),
    }


def preview_metadata(ev: dict, full: dict, full_path: str) -> dict:
    out = dict(ev)
    out["PropagationEdgesPreviewOnly"] = True
    out["PropagationEdges"] = (ev.get("PropagationEdges") or [])[:200]
    out["PropagationEdgesPreviewCount"] = len(out["PropagationEdges"])
    out["PropagationEdgesFullCount"] = full["full_count"]
    out["PropagationEdgesFullPath"] = full_path
    out["PropagationEdgesFullSHA256"] = full["full_sha"]
    out["PropagationEdgesPreviewSHA256"] = full["preview_sha"]
    out["PropagationEdgesAssociation"] = (
        "target identity (dyn_inst_seq/seq/load_seq/store_seq + LQ/SQ id/gen) "
        "and same ptag chain; boundary events join only by target identity")
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-root", default=str(ROOT / "results_hardened/runs"))
    ap.add_argument("--out", default=str(ROOT / "LSU_When_v2_FINAL_FROZEN"))
    ap.add_argument("--trace-root", default=str(ROOT / "results_hardened/runs"))
    args = ap.parse_args()
    out = Path(args.out)
    edge_dir = out / "propagation_edges_full"
    ev_dir = out / "evidence_authoritative"
    edge_dir.mkdir(parents=True, exist_ok=True)
    ev_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(Path(args.evidence_root).glob("*/attempt_1/evidence.json")):
        ev = json.loads(p.read_text())
        rid = ev["RunID"]
        trace = Path(args.trace_root) / rid / "attempt_1/trace_v31.jsonl"
        full_path = edge_dir / f"{rid}.csv.gz"
        full = export_full_edges(ev, trace, full_path)
        ev2 = preview_metadata(ev, full, str(full_path))
        ev2["FINAL_CLASS"] = classify(ev)["FINAL_CLASS"]
        ev2["FINAL_CLASSIFICATION_DIMENSIONS"] = classify(ev)
        (ev_dir / f"{rid}.evidence.json").write_text(
            json.dumps(ev2, indent=2))
        rows.append({
            "RunID": rid, "ModelID": ev["ModelID"],
            "ContextID": ev["ContextID"], "TimingID": ev["TimingID"],
            "FullEdgeCount": full["full_count"],
            "PreviewEdgeCount": full["preview_count"],
            "PreviewOnly": "true",
            "FullEdgePath": str(full_path),
            "FullEdgeSHA256": full["full_sha"],
            "PreviewEdgeSHA256": full["preview_sha"],
            "EvidenceFullCount": ev.get("PropagationEdgeCount"),
        })
    with open(out / "FINAL_PROPAGATION_EDGES_INDEX.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"exported {len(rows)} full edge files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
