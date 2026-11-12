#!/usr/bin/env python3
"""Build the per-context and per-model readiness matrices.

Inputs (all real artefacts):
  * phase3/formal/evidence_index.json      - runtime pilot/validator evidence
  * phase3/formal/MMU_40_Sample_DryRun.csv - preflight primary status per
                                             formal SampleRunID (if present)

Outputs:
  * phase3/formal/MMU_Context_Readiness_FINAL.csv
  * phase3/formal/MMU_Model_Readiness_FINAL.csv
  * phase3/formal/MMU_Readiness_Matrix_FINAL.md

A context is READY only when the preflight says READY (which already requires
real runtime evidence, a frozen binary/source match and an independent
control).  When the preflight CSV is absent the runtime index alone decides,
and the status is explicitly marked `PREFLIGHT_MISSING`.
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter

MODELS = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"]
CONTEXTS = ["R01", "R02", "R03", "R04", "R05"]


def _read_csv(path):
    if not os.path.isfile(path):
        return {}
    with open(path, newline="") as fh:
        return {r.get("SampleRunID", ""): r for r in csv.DictReader(fh)}


def _runtime_status(ev):
    if not ev:
        return "NOT_RUN"
    act = ev.get("fault_activation", "")
    cons = ev.get("fault_consumption", "")
    trace = ev.get("trace_completeness", "")
    term = ev.get("terminal_state", "")
    oracle = ev.get("oracle_result", "")
    if act == "ACTIVATED" and cons == "CONSUMED" and trace == "COMPLETE" \
            and oracle not in ("", "NOT_OBSERVED", "CONTRADICTION"):
        return "PASS"
    if act in ("ACTIVATED", "NOT_ACTIVATED", "NO_ELIGIBLE_EVENT") or \
            term not in ("", "NOT_OBSERVED"):
        return "PARTIAL"
    return "NOT_RUN"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--index", default=None)
    ap.add_argument("--preflight-csv", default=None)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--model-csv", default=None)
    ap.add_argument("--md", default=None)
    args = ap.parse_args(argv)
    root = os.path.abspath(args.repo_root)
    index_path = args.index or os.path.join(root, "phase3", "formal",
                                            "evidence_index.json")
    preflight_path = args.preflight_csv or os.path.join(
        root, "phase3", "formal", "MMU_40_Sample_DryRun.csv")
    with open(index_path) as fh:
        index = json.load(fh)
    ctxs = index.get("contexts", {})
    preflight = _read_csv(preflight_path)

    rows = []
    for model in MODELS:
        for ctx in CONTEXTS:
            key = "%s/%s" % (model, ctx)
            ev = ctxs.get(key, {})
            pf_row = preflight.get("", {})
            sample_id = ""
            # Map by ModelID/ContextID when the CSV has the formal IDs.
            for sid, rec in preflight.items():
                if rec.get("ModelID") == model and rec.get("ContextID") == ctx:
                    pf_row = rec
                    sample_id = sid
                    break
            if preflight and pf_row:
                primary = pf_row.get("PrimaryStatus", "BLOCKED_BINARY")
                readiness = "PASS" if primary == "READY" else "FAIL"
                blockers = pf_row.get("AllBlockers", primary)
            else:
                readiness = _runtime_status(ev)
                primary = "PREFLIGHT_MISSING"
                blockers = "PREFLIGHT_MISSING"
            rows.append({
                "Model": model,
                "Context": ctx,
                "SampleRunID": sample_id,
                "RunID": ev.get("run_id", ""),
                "TargetEvent": (pf_row.get("TargetEvent", "")
                                if pf_row else ev.get("target_event", "")),
                "InjectionActivation": ev.get("fault_activation", "NOT_RUN"),
                "NormalState": "CONTROL_PRESENT" if (
                    ev.get("control_oracle") or {}).get("present") else
                    "NOT_RUN",
                "FaultState": "ACTIVATED" if ev.get("fault_activation") ==
                    "ACTIVATED" else "NOT_ACTIVATED",
                "FaultConsumption": ev.get("fault_consumption", "NOT_RUN"),
                "PropagationPath": ev.get("propagation", "NOT_RUN"),
                "TraceCompleteness": ev.get("trace_completeness", "NOT_RUN"),
                "TerminalState": ev.get("terminal_state", "NOT_RUN"),
                "OracleResult": ev.get("oracle_result", "NOT_RUN"),
                "BinarySHA256": (pf_row.get("BinarySHA256Manifest", "")
                                 if pf_row else ""),
                "SourceCommit": (pf_row.get("SourceCommitManifest", "")
                                 if pf_row else ""),
                "PrimaryStatus": primary,
                "AllBlockers": blockers,
                "EvidenceDir": ev.get("run_dir", ""),
                "Readiness": readiness,
            })

    csv_path = args.csv or os.path.join(root, "phase3", "formal",
                                        "MMU_Context_Readiness_FINAL.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    model_rows = []
    for model in MODELS:
        mine = [r for r in rows if r["Model"] == model]
        ready = sum(1 for r in mine if r["Readiness"] == "PASS")
        blockers = Counter()
        terminals = Counter()
        for r in mine:
            for b in str(r["AllBlockers"]).split(";"):
                if b and b != "READY":
                    blockers[b] += 1
            terminals["%s/%s" % (r["TerminalState"], r["OracleResult"])] += 1
        if ready == len(CONTEXTS):
            overall = "READY"
        elif ready == 0:
            overall = "BLOCKED" if any(
                b.startswith("BLOCKED") for b in blockers) else "NOT_RUN"
        else:
            overall = "PARTIAL"
        model_rows.append({
            "Model": model,
            "ContextsReady": ready,
            "ContextsTotal": len(CONTEXTS),
            "Readiness": overall,
            "Blockers": ";".join("%s:%d" % (k, v)
                                 for k, v in sorted(blockers.items())),
            "Terminals": ";".join("%s:%d" % (k, v)
                                  for k, v in sorted(terminals.items())),
        })
    model_csv = args.model_csv or os.path.join(
        root, "phase3", "formal", "MMU_Model_Readiness_FINAL.csv")
    with open(model_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(model_rows[0].keys()))
        w.writeheader()
        w.writerows(model_rows)

    md_path = args.md or os.path.join(root, "phase3", "formal",
                                      "MMU_Readiness_Matrix_FINAL.md")
    lines = ["# MMU Context Readiness (final binary)", "",
             "| Model | R01 | R02 | R03 | R04 | R05 | Readiness |",
             "|---|---|---|---|---|---|---|"]
    for model in MODELS:
        by_ctx = {r["Context"]: r["Readiness"] for r in rows
                  if r["Model"] == model}
        vals = [by_ctx.get(c, "NOT_RUN") for c in CONTEXTS]
        if all(v == "PASS" for v in vals):
            overall = "READY"
        elif all(v == "NOT_RUN" for v in vals):
            overall = "NOT_RUN"
        else:
            overall = "PARTIAL"
        lines.append("| %s | %s | **%s** |" % (
            model, " | ".join(vals), overall))
    lines.append("")
    lines.append("Readiness is the preflight PRIMARY status; a PASS requires "
                 "real runtime evidence, a frozen binary/source match and an "
                 "independent control oracle.  `FAIL` is any non-READY "
                 "preflight status and the exact blockers are in "
                 "`MMU_Context_Readiness_FINAL.csv`.")
    lines.append("")
    with open(md_path, "w") as fh:
        fh.write("\n".join(lines))
    print(json.dumps({"csv": csv_path, "model_csv": model_csv, "md": md_path,
                      "rows": len(rows),
                      "model_readiness": {r["Model"]: r["Readiness"]
                                          for r in model_rows}},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
