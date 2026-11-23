#!/usr/bin/env python3
"""Export timing maps, eligible-event lists, and the identity-based
propagation chains (with per-edge basis) from the executed WHEN-5X3
artifacts.

The propagation chain is the causal reconstruction produced by
campaign/propagation.py and stored in analysis/per_condition.json under the
"Chain" key.  Nothing here invents a stage: an empty cell means the frozen
binary did not emit a causally-linked event for that stage, and the boundary
is recorded in the EvidenceBoundary column.
"""
import csv
import gzip
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
import control_map  # noqa: E402
import oracle  # noqa: E402
RUNS = os.path.join(ROOT, "runs", "W5X3")
RETRY_RUNS = os.path.join(ROOT, "runs", "W5X3_RETRY")
RETRY2_RUNS = os.path.join(ROOT, "runs", "W5X3_RETRY2")
COND = os.path.join(ROOT, "campaign", "conditions.json")
A = os.path.join(ROOT, "analysis")
STATUS = os.path.join(ROOT, "experiment_status.csv")

STAGES = ["activation", "mutation", "translation", "request", "response",
          "writeback", "consumer", "commit_squash"]


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def fault_manifest_for(sample_id):
    """Fault manifest honouring targeted re-runs (RETRY2 > RETRY > original),
    so the ActualOrdinal / oracle lines always come from the trace that was
    actually analysed, never the original path."""
    r2 = load(os.path.join(A, "retry2_map.json"), {})
    r1 = load(os.path.join(A, "retry_map.json"), {})
    if sample_id in r2:
        return load(os.path.join(RETRY2_RUNS, r2[sample_id], "manifest.json"),
                    {})
    if sample_id in r1:
        return load(os.path.join(RETRY_RUNS, r1[sample_id], "manifest.json"),
                    {})
    return load(os.path.join(RUNS, sample_id, "manifest.json"), {})


def kv(line):
    return dict(re.findall(r"(\w+)=([^ ]*)", line))


def evt(path):
    try:
        with gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if line.startswith("PROP-EVT:"):
                    yield kv(line)
    except (OSError, EOFError):
        return


def stage_cell(ev):
    if not ev:
        return ""
    return "%s(%s)@%s" % (ev.get("event_id", ""), ev.get("kind", ""),
                          ev.get("tick", ""))


def main():
    os.makedirs(A, exist_ok=True)
    os.makedirs(os.path.join(A, "eligible_events"), exist_ok=True)
    conds = load(COND, [])
    rows = {r["NewSampleRunID"]: r for r in
            csv.DictReader(open(STATUS))}
    per = load(os.path.join(A, "per_condition.json"), [])
    permap = {p["NewSampleRunID"]: p for p in per}
    ctrls = {}
    for c in conds:
        cid = c["ControlID"]
        if cid not in ctrls:
            ctrls[cid] = load(os.path.join(RUNS, cid, "manifest.json"), {})

    # Eligible-event list per (Model, Context) from the golden pre-scan.
    for cid, m in sorted(ctrls.items()):
        if not m or not m.get("trace"):
            continue
        path = os.path.join(ROOT, m["trace"])
        out = os.path.join(A, "eligible_events", cid + ".csv")
        with open(out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["eligible_ordinal", "event_id", "tick", "va", "asid",
                        "vmid", "tlb_instance", "tlb_entry_id",
                        "entry_generation", "page_size_n", "mode",
                        "old_pfn", "new_pfn", "next_table_pa",
                        "decoy_table_base", "pte_address", "descriptor",
                        "old_pa", "new_pa", "candidate_asid", "lookup_id",
                        "tlbi_id", "tlbi_op"])
            for e in evt(path):
                if e.get("kind") != "mmu_eligible_event":
                    continue
                w.writerow([e.get("eligible_ordinal", ""), e.get("event_id", ""),
                            e.get("tick", ""), e.get("va", ""),
                            e.get("asid", ""), e.get("vmid", ""),
                            e.get("tlb_instance", ""), e.get("tlb_entry_id", ""),
                            e.get("entry_generation", ""),
                            e.get("page_size_n", ""), e.get("mode", ""),
                            e.get("old_pfn", ""), e.get("new_pfn", ""),
                            e.get("next_table_pa", ""),
                            e.get("decoy_table_base", ""),
                            e.get("pte_address", ""), e.get("descriptor", ""),
                            e.get("old_pa", ""), e.get("new_pa", ""),
                            e.get("candidate_asid", ""),
                            e.get("lookup_id", ""), e.get("tlbi_id", ""),
                            e.get("tlbi_op", "")])

    # Timing map with actual selected event ids.
    with open(os.path.join(A, "timing_map.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ControlID", "ModelID", "NewContext", "GuestContext",
                    "N", "TimingID", "Percentile", "TargetOrdinal",
                    "ActualOrdinal", "SelectedEventID", "FaultSampleRunID",
                    "Status", "TerminalState"])
        for c in conds:
            cid = c["ControlID"]
            m = ctrls.get(cid) or {}
            n = int((m.get("eligible_summary") or {}).get(
                "eligible_total", 0) or 0)
            f = fault_manifest_for(c["NewSampleRunID"])
            sel = (f.get("eligible_selected") or [{}])[0] if f else {}
            r = rows.get(c["NewSampleRunID"], {})
            w.writerow([cid, c["ModelID"], c["NewContext"],
                        c["ControlContext"], n, c["TimingID"],
                        "%.1f" % (float(c["Percentile"]) * 100),
                        r.get("TargetOrdinal", ""),
                        sel.get("eligible_ordinal", ""),
                        sel.get("event_id", ""), c["NewSampleRunID"],
                        r.get("Status", ""), r.get("TerminalState", "")])

    # Propagation chains (identity-based; empty stage = no causal event).
    with open(os.path.join(A, "propagation_chains.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ModelID", "Context", "Timing",
                    "TerminalState"] + STAGES +
                   ["Path", "Unobserved", "NotApplicable", "Boundary",
                    "Completeness", "BranchCount", "EffectBranchIndex",
                    "EdgeCount"])
        for p in per:
            if p["Status"] != "COMPLETE":
                continue
            ch = p.get("Chain") or {}
            stages = (p.get("Stages") or {})
            comp = ch.get("completeness") or {}
            path = " -> ".join(
                "%s:%s" % (s, stage_cell(stages.get(s)))
                for s in STAGES if stages.get(s))
            w.writerow([p["NewSampleRunID"], p["ModelID"], p["NewContext"],
                        p["TimingID"], p["TerminalState"]] +
                       [stage_cell(stages.get(s)) for s in STAGES] +
                       [path,
                        ",".join(ch.get("unobserved", [])),
                        ",".join(ch.get("not_applicable", [])),
                        ",".join(ch.get("boundary", [])),
                        "FULL" if (comp.get("architecture_complete") and
                                   comp.get("terminal_observed") and
                                   comp.get("edges_explicit")) else "PARTIAL",
                        len(ch.get("branches", [])),
                        ch.get("effect_branch_index", ""),
                        len(ch.get("edges", []))])

    # Multi-branch DAG: one row per consumer branch of the faulted state.
    with open(os.path.join(A, "chain_branches.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ModelID", "Timing", "BranchIndex",
                    "TranslationID", "ConsumeKind", "ConsumeEventID",
                    "ReuseOrdinal", "VA", "PA", "TerminalKind",
                    "TerminalEventID", "TerminalTick", "Commits", "Squashed"])
        for p in per:
            if p["Status"] != "COMPLETE":
                continue
            ch = p.get("Chain") or {}
            for i, b in enumerate(ch.get("branches", [])):
                w.writerow([p["NewSampleRunID"], p["ModelID"], p["TimingID"],
                            i, b.get("translation_id"), b.get("consume_kind"),
                            b.get("consume_event_id"), b.get("reuse_ordinal"),
                            b.get("va"), b.get("pa"), b.get("terminal_kind"),
                            b.get("terminal_event_id"), b.get("terminal_tick"),
                            b.get("commits"), b.get("squashed")])

    # Four-dimensional completeness record (file/edges/terminal/architecture).
    with open(os.path.join(A, "completeness.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ModelID", "Timing", "Status",
                    "TerminalState", "FileComplete", "EdgesExplicit",
                    "TerminalObserved", "ArchitectureComplete", "Completeness"])
        rows_by_id = {r["NewSampleRunID"]: r for r in
                      csv.DictReader(open(STATUS))}
        for p in per:
            rid = p["NewSampleRunID"]
            r = rows_by_id.get(rid, {})
            w.writerow([rid, p["ModelID"], p["TimingID"], p["Status"],
                        p["TerminalState"], r.get("FileComplete", ""),
                        r.get("EdgesExplicit", ""),
                        r.get("TerminalObserved", ""),
                        r.get("ArchitectureComplete", ""),
                        r.get("Completeness", "")])

    # Per-edge causal basis.
    with open(os.path.join(A, "chain_edges.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ModelID", "Context", "Timing",
                    "SourceEvent", "SourceKind", "TargetEvent", "TargetKind",
                    "Basis", "EdgeType", "Confidence"])
        for p in per:
            if p["Status"] != "COMPLETE":
                continue
            ch = p.get("Chain") or {}
            for e in ch.get("edges", []):
                w.writerow([p["NewSampleRunID"], p["ModelID"],
                            p["NewContext"], p["TimingID"],
                            e.get("source", ""), e.get("source_kind", ""),
                            e.get("target", ""), e.get("target_kind", ""),
                            e.get("basis", ""), e.get("type", ""),
                            e.get("confidence", "")])

    # Fault vs control oracle comparison (semantic + build-matched control).
    ctrl_reg = control_map.registry()
    with open(os.path.join(A, "fault_control_compare.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ControlID", "FaultOracleLines",
                    "ControlOracleLines", "OracleDiff", "BuildMatches",
                    "TerminalState"])
        for c in conds:
            r = rows.get(c["NewSampleRunID"], {})
            if r.get("Status") != "COMPLETE":
                continue
            f = fault_manifest_for(c["NewSampleRunID"])
            crec, bok = control_map.resolve_control(
                c["ModelID"], c["NewContext"], f.get("gem5_sha256", ""),
                ctrl_reg)
            ct = (crec or {}).get("manifest") or {}
            fo = oracle.oracle_lines(f.get("terminal_lines") or [])
            co = oracle.oracle_lines(ct.get("terminal_lines") or [])
            diff = "1" if not oracle.semantic_compare(
                f.get("terminal_lines") or [],
                ct.get("terminal_lines") or []) else "0"
            w.writerow([c["NewSampleRunID"], c["ControlID"], len(fo), len(co),
                        diff, "1" if bok else "0", r.get("TerminalState", "")])

    # Model/context summary with granular terminal states.
    states = ["SDC", "ACTIVATED_MASKED", "ACTIVATED_UNCONSUMED",
              "PROPAGATED_BUT_SQUASHED", "DETECTED_LOCALLY",
              "DETECTED_DELIVERED", "REQUEST_PENDING_AT_ROI_END",
              "PARTIAL_EVIDENCE", "NOT_ACTIVATED"]
    counts = defaultdict(lambda: defaultdict(int))
    for r in rows.values():
        if r.get("Status") == "N/A":
            counts[r["ModelID"]]["N/A"] += 1
        else:
            counts[r["ModelID"]][r.get("TerminalState", "")] += 1
    with open(os.path.join(A, "summary_by_model.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ModelID"] + states + ["N/A"])
        for m in sorted(counts):
            d = counts[m]
            w.writerow([m] + [d.get(s, 0) for s in states] + [d.get("N/A", 0)])

    with open(os.path.join(A, "DELIVERABLES.md"), "w") as fh:
        fh.write("# WHEN-5X3 deliverables index\n\n")
        fh.write("- `experiment_status.csv` — 120-condition status matrix\n")
        fh.write("- `run_manifest.json` — provenance, hashes and run rows\n")
        fh.write("- `final_acceptance.md` / `acceptance.json` — A01–A22\n")
        fh.write("- `blocked_tasks.md` — N/A/BLOCKED/FAILED reasons\n")
        fh.write("- `runs/W5X3/<SampleRunID>/` — raw trace, terminal, "
                 "manifest, command\n")
        fh.write("- `runs/W5X3/<ControlID>/` — golden pre-scan/control\n")
        fh.write("- `analysis/eligible_events/<ControlID>.csv` — full "
                 "eligible-event stream\n")
        fh.write("- `analysis/timing_map.csv` — N, ceil(pN), actual ordinal/"
                 "event id\n")
        fh.write("- `analysis/propagation_chains.csv` — identity-based causal "
                 "stages + boundary\n")
        fh.write("- `analysis/chain_branches.csv` — multi-branch consumer DAG\n")
        fh.write("- `analysis/completeness.csv` — four-dimension completeness "
                 "per sample\n")
        fh.write("- `analysis/chain_edges.csv` — per-edge source/target/basis/"
                 "confidence\n")
        fh.write("- `analysis/fault_control_compare.csv` — oracle diff "
                 "per sample\n")
        fh.write("- `analysis/summary_by_model.csv` — granular terminal "
                 "states\n")
        fh.write("- `campaign/` — runner, rcS generator, condition map, "
                 "analysis code\n")
        fh.write("- `provenance/` — old-workspace hashes, A01–A03 audit\n")
    print("evidence exported")


if __name__ == "__main__":
    main()
