#!/usr/bin/env python3
"""Export timing maps, eligible-event lists, propagation chains and
fault/control comparisons from the executed WHEN-5X3 artifacts."""
import csv
import gzip
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "runs", "W5X3")
COND = os.path.join(ROOT, "campaign", "conditions.json")
A = os.path.join(ROOT, "analysis")
STATUS = os.path.join(ROOT, "experiment_status.csv")


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


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
            f = load(os.path.join(RUNS, c["NewSampleRunID"], "manifest.json"),
                     {})
            sel = (f.get("eligible_selected") or [{}])[0] if f else {}
            r = rows.get(c["NewSampleRunID"], {})
            w.writerow([cid, c["ModelID"], c["NewContext"],
                        c["ControlContext"], n, c["TimingID"],
                        "%.1f" % (float(c["Percentile"]) * 100),
                        r.get("TargetOrdinal", ""),
                        sel.get("eligible_ordinal", ""),
                        sel.get("event_id", ""), c["NewSampleRunID"],
                        r.get("Status", ""), r.get("TerminalState", "")])

    # Propagation chains (observed stages only).
    with open(os.path.join(A, "propagation_chains.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ModelID", "Context", "Timing",
                    "ActivationEvent", "MutationEvent", "TranslationEvent",
                    "RequestEvent", "ResponseEvent", "ConsumerEvent",
                    "CommitSquashEvent", "TerminalState", "EvidenceBoundary"])
        for p in per:
            if p["Status"] != "COMPLETE":
                continue
            s = p.get("Stages") or {}
            def eid(k):
                return (s.get(k) or {}).get("event_id", "")
            boundary = ""
            if p["GuestContext"] == "R05":
                boundary = ("MMU Execute request joined to guest oracle; "
                            "IFU response/decode/commit NOT_EMITTED_BY_"
                            "FROZEN_BINARY")
            w.writerow([p["NewSampleRunID"], p["ModelID"], p["NewContext"],
                        p["TimingID"], eid("activation"), eid("mutation"),
                        eid("translation"), eid("request"), eid("response"),
                        eid("consumer"), eid("commit_squash"),
                        p["TerminalState"], boundary])

    # Fault vs control oracle comparison.
    orc = re.compile(r"^W(?:9|10S|1[0-4])_(?:RESULT|SUMMARY|STORE)\b")
    with open(os.path.join(A, "fault_control_compare.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["SampleRunID", "ControlID", "FaultOracleLines",
                    "ControlOracleLines", "OracleDiff", "TerminalState"])
        for c in conds:
            r = rows.get(c["NewSampleRunID"], {})
            if r.get("Status") != "COMPLETE":
                continue
            f = load(os.path.join(RUNS, c["NewSampleRunID"], "manifest.json"),
                     {})
            ct = ctrls.get(c["ControlID"]) or {}
            fo = [ln for ln in (f.get("terminal_lines") or [])
                  if orc.match(ln)]
            co = [ln for ln in (ct.get("terminal_lines") or [])
                  if orc.match(ln)]
            w.writerow([c["NewSampleRunID"], c["ControlID"], len(fo), len(co),
                        "1" if fo != co else "0", r.get("TerminalState", "")])

    # Model/context summary.
    counts = defaultdict(lambda: defaultdict(int))
    for r in rows.values():
        counts[r["ModelID"]][r["TerminalState"] or r["Status"]] += 1
    with open(os.path.join(A, "summary_by_model.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ModelID", "SDC", "ACTIVATED_MASKED",
                    "DETECTED_CONTAINED", "SQUASHED", "N/A"])
        for m in sorted(counts):
            d = counts[m]
            w.writerow([m, d.get("SDC", 0), d.get("ACTIVATED_MASKED", 0),
                        d.get("DETECTED_CONTAINED", 0), d.get("SQUASHED", 0),
                        d.get("N/A", 0)])

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
        fh.write("- `analysis/propagation_chains.csv` — observed causal "
                 "stages\n")
        fh.write("- `analysis/fault_control_compare.csv` — oracle diff "
                 "per sample\n")
        fh.write("- `campaign/` — runner, rcS generator, condition map, "
                 "analysis code\n")
        fh.write("- `provenance/` — old-workspace hashes, A01–A03 audit\n")
    print("evidence exported")


if __name__ == "__main__":
    main()
