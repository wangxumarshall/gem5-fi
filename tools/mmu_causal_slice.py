#!/usr/bin/env python3
"""Export an auditable causal slice for one of the five IFU contexts.

The slice contains the exact PROP-EVT lines from the frozen raw trace for the
events named by tools/mmu_evidence_chain.py, plus the structured identity join
and the guest oracle lines.  Nothing is synthesised: every event id in the
JSON must exist in the source trace, and the raw lines are copied verbatim.

Usage:
  tools/mmu_causal_slice.py --run-dir runs/TEST-F1-M03-R05 \
      --out-dir phase3/final/slices/M03-R05
"""

import argparse
import csv
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_trace_validate_v3 as v3
import mmu_evidence_chain as chain


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_raw_lines(path):
    out = {}
    header = ""
    with gzip.open(path, "rt", errors="replace") as fh:
        for line in fh:
            if line.startswith("#") and not header:
                header = line.rstrip("\n")
                continue
            if not line.startswith("PROP-EVT:"):
                continue
            eid = None
            for tok in line[9:].split():
                if tok.startswith("event_id="):
                    try:
                        eid = int(tok.split("=", 1)[1])
                    except ValueError:
                        eid = None
                    break
            if eid is not None:
                out[eid] = line.rstrip("\n")
    return header, out


def event_ids(strict):
    ids = []
    if strict.get("activation"):
        ids.append(strict["activation"]["event_id"])
    ids += list(strict.get("consumption_events") or [])
    for key, value in (strict.get("identity") or {}).items():
        if key.endswith("_event") and isinstance(value, int):
            ids.append(value)
    if strict.get("consumption"):
        ids.append(strict["consumption"]["event_id"])
    # Preserve first-seen order, drop duplicates/None.
    out = []
    for eid in ids:
        if eid and eid not in out:
            out.append(eid)
    return out


def logical_order(strict, model):
    """Causal (not raw-file) order of the joined events."""
    act = (strict.get("activation") or {}).get("event_id")
    seq = list(strict.get("consumption_events") or [])
    identity = strict.get("identity") or {}
    if model == "M07" and identity.get("permission_eval_event"):
        seq = [identity["permission_eval_event"]] + \
            [e for e in seq if e != identity["permission_eval_event"]]
        if act and act not in seq:
            seq.insert(1, act)
    elif act and act not in seq:
        seq.insert(0, act)
    out = []
    for eid in seq:
        if eid and eid not in out:
            out.append(eid)
    return out


def sample_id_map(repo_root):
    path = os.path.join(repo_root, "phase3", "freeze", "authority",
                        "MMU_40_Sample_Matrix.csv")
    out = {}
    if os.path.isfile(path):
        for row in csv.DictReader(open(path)):
            out[(row["ModelID"], row["ContextID"])] = row["SampleRunID"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--context", default=None)
    ap.add_argument("--target-va", default=None)
    ap.add_argument("--target-mode", default=None)
    args = ap.parse_args(argv)

    run_dir = os.path.abspath(args.run_dir)
    manifest = json.load(open(os.path.join(run_dir, "sample_manifest.json")))
    model = args.model or manifest["model"]
    context = args.context or manifest["context"]
    target_va = int(args.target_va, 0) if args.target_va else int(
        manifest["target_va"])
    target_mode = args.target_mode or manifest.get("target_mode", "")
    trace = os.path.join(run_dir, "Trace", "prop_evt.txt.gz")
    oracle_path = os.path.join(run_dir, "Run_Log", "observed_output.txt")
    control = manifest.get("control_run", "")

    events, bad = v3.load_events(trace)
    oracle_text = open(oracle_path, errors="replace").read()
    strict = chain.evaluate(model, context, events, target_va, target_mode,
                            oracle_text)
    if strict is None:
        print("no strict chain for %s/%s" % (model, context), file=sys.stderr)
        return 2
    ids = event_ids(strict)
    logical = logical_order(strict, model)
    by_id = {e["event_id"]: e for e in events}
    # Raw-trace order for the audit table and the exported lines.
    raw_ids = sorted(eid for eid in ids if eid in by_id)

    header, raw = read_raw_lines(trace)
    missing = [eid for eid in ids if eid not in raw]
    slice_events = []
    for eid in raw_ids:
        ev = by_id.get(eid, {})
        slice_events.append({
            "event_id": eid,
            "kind": chain.kind(ev),
            "fields": {k: v for k, v in ev.items() if v not in ("", None)},
            "raw_line": raw.get(eid, ""),
        })
    causal_steps = []
    for step, eid in enumerate(logical, 1):
        ev = by_id.get(eid, {})
        causal_steps.append({
            "step": step,
            "event_id": eid,
            "kind": chain.kind(ev),
            "va": ev.get("va", ""),
            "pa": ev.get("pa", ""),
            "translation_id": ev.get("translation_id", ""),
            "tlb_instance": ev.get("tlb_instance", ""),
            "tlb_entry_id": ev.get("tlb_entry_id", ""),
            "entry_generation": ev.get("entry_generation", ""),
            "permission_result": ev.get("permission_result", ""),
        })

    # Terminal commit/squash status: report the real rows, never a guess.
    commit_rows = [e for e in events
                   if e["event_id"] in ids and chain.kind(e) == "commit"]
    squash_rows = [e for e in events
                   if e["event_id"] in ids and chain.kind(e) in
                   ("squash", "squash_discarded", "squash_masked")]
    summary = next((e for e in events if chain.kind(e) == "mmu_fault_summary"),
                   {})

    verdict_path = os.path.join(run_dir, "Validation", "verdict.json")
    verdict = json.load(open(verdict_path)) if os.path.isfile(verdict_path) \
        else {}

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sid = manifest.get("sample_run_id", "") or \
        sample_id_map(repo_root).get((model, context), "")

    out = {
        "schema": "mmu-causal-slice-v2",
        "sample_run_id": sid,
        "run_id": manifest.get("run_id", os.path.basename(run_dir)),
        "model": model,
        "context": context,
        "workload": manifest.get("workload"),
        "target_va": hex(target_va),
        "target_mode": target_mode,
        "fault_id": strict.get("fault_id"),
        "trace": trace,
        "trace_sha256": sha256(trace),
        "trace_header": header,
        "observed_output": oracle_path,
        "observed_output_sha256": sha256(oracle_path),
        "control_run": control,
        "oracle_lines": [ln for ln in oracle_text.splitlines()
                         if ln.startswith(("W9_", "W10", "W11_", "W12_",
                                           "W13_", "W14_"))],
        "activation_basis": strict.get("activation_basis"),
        "join_note": strict.get("join_note"),
        "consumption_basis": strict.get("consumption_basis"),
        "required_kinds": strict.get("required_kinds"),
        "missing_kinds": strict.get("missing_kinds"),
        "guards": strict.get("guards"),
        "identity": strict.get("identity"),
        "fetch_request": strict.get("fetch_request"),
        "terminal_evidence": strict.get("terminal_evidence"),
        "terminal_rows_in_slice": {
            "commit": [e["event_id"] for e in commit_rows],
            "squash": [e["event_id"] for e in squash_rows],
            "fault_summary": summary.get("event_id"),
            "fault_summary_outcome": summary.get("outcome"),
            "fault_summary_consumed": summary.get("consumed"),
        },
        "instrumentation_boundary": {
            "ifu_fetch_request_event": "lsu_request(mode=Execute)",
            "ifu_fetch_response": "NOT_EMITTED_BY_FROZEN_BINARY",
            "per_instruction_decode_execute": "NOT_EMITTED_BY_FROZEN_BINARY",
            "per_instruction_commit_for_synthetic_ifu": "NOT_EMITTED",
            "execution_terminal_evidence":
                "guest oracle marker tied to the fetched PA/code page",
            "binary_sha256": manifest.get("gem5_sha256"),
        },
        "verdict": {k: verdict.get(k) for k in (
            "ActivationStatus", "FaultConsumptionStatus", "PropagationStatus",
            "TraceCompleteness", "TerminalState", "OracleResult",
            "activation_event_id", "consumption_event_id")},
        "strict_chain_ok": strict.get("ok"),
        "causal_order": causal_steps,
        "events": slice_events,
    }

    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "causal_slice.json")
    txt_path = os.path.join(args.out_dir, "causal_slice.prop_evt.txt")
    md_path = os.path.join(args.out_dir, "causal_slice.md")
    with open(json_path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
        fh.write("\n")
    with open(txt_path, "w") as fh:
        fh.write(header + "\n")
        for eid in raw_ids:
            if eid in raw:
                fh.write(raw[eid] + "\n")

    lines = ["# MMU causal slice — %s/%s" % (model, context), ""]
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for key in ("sample_run_id", "run_id", "model", "context", "workload",
                "target_va", "target_mode", "fault_id", "trace_sha256",
                "activation_basis", "consumption_basis", "strict_chain_ok"):
        lines.append("| %s | `%s` |" % (key, out.get(key)))
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("| %s | `%s` |" % ("ActivationStatus",
                                     out["verdict"].get("ActivationStatus")))
    for k in ("FaultConsumptionStatus", "PropagationStatus",
              "TraceCompleteness", "TerminalState", "OracleResult"):
        lines.append("| %s | `%s` |" % (k, out["verdict"].get(k)))
    lines.append("")
    lines.append("## Identity join")
    lines.append("")
    for k, v in (out.get("identity") or {}).items():
        lines.append("- `%s` = `%s`" % (k, v))
    lines.append("")
    lines.append("## Join note")
    lines.append("")
    lines.append(out.get("join_note") or "-")
    lines.append("")
    lines.append("## Causal chain (logical order)")
    lines.append("")
    lines.append("| Step | EventID | Kind | VA | PA | Translation | Entry | "
                 "Decision |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for item in causal_steps:
        entry = "%s:%s:%s" % (item.get("tlb_instance", ""),
                              item.get("tlb_entry_id", ""),
                              item.get("entry_generation", ""))
        lines.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
            item["step"], item["event_id"], item["kind"],
            item.get("va", ""), item.get("pa", ""),
            item.get("translation_id", ""), entry,
            item.get("permission_result", "")))
    lines.append("")
    lines.append("## Events present in the raw trace (ascending EventID)")
    lines.append("")
    lines.append("| EventID | Kind |")
    lines.append("|---|---|")
    for item in slice_events:
        lines.append("| %s | %s |" % (item["event_id"], item["kind"]))
    lines.append("")
    lines.append("## Guest oracle")
    lines.append("")
    lines.append("```")
    lines.extend(out["oracle_lines"])
    lines.append("```")
    lines.append("")
    lines.append("## Instrumentation boundary (honest)")
    lines.append("")
    for k, v in out["instrumentation_boundary"].items():
        lines.append("- `%s`: %s" % (k, v))
    lines.append("")
    lines.append("## Missing kinds / guards")
    lines.append("")
    lines.append("- missing_kinds: `%s`" % (out["missing_kinds"] or []))
    lines.append("- guards: `%s`" % (out["guards"] or []))
    lines.append("")
    lines.append("The exact PROP-EVT lines are in `causal_slice.prop_evt.txt`; "
                 "every event id above is present in `%s`." %
                 (out["sample_run_id"] or out["run_id"]))
    with open(md_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    print(json.dumps({
        "slice": json_path,
        "raw_lines": txt_path,
        "markdown": md_path,
        "event_count": len(ids),
        "missing_in_trace": missing,
        "strict_chain_ok": strict.get("ok"),
        "trace_sha256": out["trace_sha256"],
    }, indent=2, sort_keys=True))
    return 0 if not missing else 3


if __name__ == "__main__":
    sys.exit(main())
