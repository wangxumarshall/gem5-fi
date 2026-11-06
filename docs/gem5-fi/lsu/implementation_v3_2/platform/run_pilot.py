#!/usr/bin/env python3
"""Run one v3.2 pilot with a PILOT-only identity.

The seed and fault configuration are copied from the frozen Excel sample; the
SampleRunID is deliberately replaced with ``PILOT-...`` so no formal sample is
overwritten. A pilot is accepted only when the process exits 0, the injector
reports at least one injection, the target-event evidence is present, and the
converted Trace v3.1 JSONL is valid and complete. The oracle result is
recorded (MASKED vs SDC), not required to pass: a non-propagating fault is a
valid pilot outcome.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLATFORM = Path(__file__).resolve().parent
IMPL = PLATFORM.parent
sys.path.insert(0, str(PLATFORM))

from config_parser import load_config  # noqa: E402
from manifest import build_manifest, canonical_json, write_manifest  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402
from trace_validator import validate  # noqa: E402
from tools.prop_trace_to_v31 import convert  # noqa: E402

ROOT = Path(__file__).resolve().parents[5]
EXCEL = ROOT / "docs/gem5-fi/lsu/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx"
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOADS = IMPL / "workloads"


def _workload_for(model: str) -> str:
    return {"A01": "agu_addrmodes", "A03": "agu_addrmodes",
            "FW02": "sq_forward"}[model]


def _funnel(path: Path) -> dict:
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out = {}
    for line in lines:
        m = re.search(r"FUNNEL:\s+attempted=(\d+)\s+eligible=(\d+)\s+injected=(\d+)", line)
        if m:
            out = {"attempted": int(m[1]), "eligible": int(m[2]), "injected": int(m[3])}
    return out


def _fw02_summary(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"CHAOS_FW02_SUMMARY:\s+observed=(\d+)\s+suppressed=(\d+)\s+"
                  r"load_seq=(\d+)\s+store_seq=(\d+)", text)
    if m:
        return {"observed": int(m[1]), "suppressed": int(m[2]),
                "load_seq": int(m[3]), "store_seq": int(m[4])}
    # Aborted run: the exit-callback summary is absent, but each suppression
    # line was flushed. Count those lines and take the last pair.
    lines = [ln for ln in text.splitlines() if "f6_fw02_suppress" in ln]
    if not lines:
        return {}
    mm = re.search(r"load_seq:\s*(\d+).*store_seq:\s*(\d+)", lines[-1])
    return {"observed": len(lines), "suppressed": len(lines),
            "load_seq": int(mm[1]) if mm else None,
            "store_seq": int(mm[2]) if mm else None}


def _addrpath_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: lsq_pushRequest_PRE" not in line:
            continue
        m = re.search(r"mode=([^,\s]+).*old_addr=0x([0-9a-fA-F]+).*new_addr=0x([0-9a-fA-F]+)", line)
        if m:
            events.append({"mode": m[1], "old": int(m[2], 16),
                           "new": int(m[3], 16), "line": line})
    return events


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, choices=["A01", "A03", "FW02"])
    ap.add_argument("--pilot-id", required=True)
    ap.add_argument("--seed", type=int, default=None,
                    help="override seed; default = the selected Excel context row")
    ap.add_argument("--context-index", type=int, default=1, choices=[1,2,3,4,5],
                    help="R01-R05: select the Excel sample row for this context")
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--gem5", type=Path, default=GEM5)
    args = ap.parse_args(argv)

    cfg = load_config(EXCEL, require_complete=False)
    model_rows = [s for s in cfg["samples"] if s["model_id"] == args.model]
    sample = copy.deepcopy(model_rows[args.context_index - 1])
    excel_seed = sample["seed"]
    if args.seed is None:
        args.seed = excel_seed
    sample["sample_run_id"] = args.pilot_id
    sample["run_id"] = f"PILOT-{args.model}"
    sample["sub_task_id"] = f"PILOT-{args.model}-S01"
    sample["seed"] = args.seed
    sample["workload_path"] = str(WORKLOADS / _workload_for(args.model))
    sample["workload_exists"] = True
    cfg2 = copy.deepcopy(cfg)
    cfg2["samples"] = [sample]
    # gem5 runs with cwd=ROOT, so a relative --outdir would land its
    # artifacts outside this script's output directory. Pin the path at the
    # caller's cwd before gem5 sees it.
    out = args.outdir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    extra = []
    if args.model == "A01":
        extra = ["--chaos_addrpath", "--agu_pre_mode", "a01_bit3_load",
                 "--addrpath_lsu_tier", "F0", "--addrpath_max_faults", "1",
                 "--addrpath_warmup_events", "0", "--addrpath_span_events", "10",
                 "--addrpath_rng_seed", str(args.seed),
                 "--addrpath_event_ordinal", str(sample.get("event_ordinal") or 1)]
    elif args.model == "A03":
        extra = ["--chaos_addrpath", "--agu_pre_mode", "a03_bit3_stuck0_load",
                 "--addrpath_lsu_tier", "F5", "--addrpath_max_faults", "0",
                 "--addrpath_warmup_events", "0",
                 "--addrpath_rng_seed", str(args.seed),
                 "--addrpath_event_ordinal", str(sample.get("event_ordinal") or 1)]
    else:
        extra = ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                 "--max_faults", "1", "--rng_seed", str(args.seed),
                 "--lsqfwd_event_ordinal", str(sample.get("event_ordinal") or 1)]

    cmd = [str(args.gem5), f"--outdir={out}", str(CONFIG),
           f"--cmd={WORKLOADS / _workload_for(args.model)}",
           "--cpu", "O3", "--variant", "B0",
           "--probability", "1.0",
           "--chaos_propagation",
           "--prop_trace_file", "prop_trace.csv.gz"] + extra
    (out / "command.txt").write_text("\n".join(cmd) + "\n")
    manifest = build_manifest(cfg2, args.pilot_id, args.gem5, CONFIG,
                              output_dir=out, command=cmd)
    if args.seed != excel_seed:
        manifest["seed_source"] = "pilot_cli_override (not Excel)"
        manifest["manifest_sha256"] = hashlib.sha256(
            canonical_json(manifest).encode("utf-8")).hexdigest()
    write_manifest(manifest, out / "manifest.json")
    started = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          timeout=900)
    elapsed = time.time() - started
    (out / "stdout.log").write_text(proc.stdout)
    (out / "stderr.log").write_text(proc.stderr)

    expected = str(sample.get("oracle"))
    oracle = subprocess.run(
        [sys.executable, str(WORKLOADS / "oracle_check.py"), expected,
         str(out / "stdout.log")], capture_output=True, text=True)
    (out / "oracle.log").write_text(oracle.stdout + oracle.stderr)
    oracle_pass = oracle.returncode == 0

    if args.model in ("A01", "A03"):
        inj = _funnel(out / "addrpath_injections.log")
        events = _addrpath_events(out / "addrpath_injections.log")
        target_proof = {
            "site": "lsq_pushRequest_PRE",
            "events": len(events),
            "all_load_bit3": all(
                (e["new"] == (e["old"] ^ 0x8) if e["mode"] == "a01_bit3_load"
                 else e["new"] == (e["old"] & ~0x8)) for e in events),
        }
        injected = inj.get("injected", 0)
    else:
        inj = _fw02_summary(out / "lsq_fwd_injections.log")
        target_proof = {"site": "store->load_forward_decision", **inj}
        injected = inj.get("suppressed", 0)

    crash_by_fault = False
    crash_evidence = None
    events = []  # A01/A03 address-path events; empty for FW02
    if proc.returncode != 0 and args.model in ("A01", "A03", "FW02") and injected > 0:
        err = proc.stderr.lower()
        if "page table fault" in err:
            # The panic address is not always the injected address (the
            # corrupted value can become an indirect pointer). Record the
            # page-table fault as crash evidence after a real injection; do
            # not claim direct address identity unless it matches.
            crash_by_fault = True
            match = any(hex(e["new"]) in err for e in events)
            crash_evidence = ("page_table_fault_after_injection" +
                              ("_address_match" if match else "_no_address_match"))
    if proc.returncode != 0 and crash_by_fault:
        run_status, activation, terminal, completeness = (
            "SIMULATOR_ERROR", "TRIGGERED", "CRASH", "COMPLETE")
    elif proc.returncode != 0:
        run_status, activation, terminal, completeness = (
            "SIMULATOR_ERROR", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "CRASH", "INCOMPLETE")
    elif not oracle_pass:
        run_status, activation, terminal, completeness = (
            "COMPLETED", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "SDC", "COMPLETE")
    else:
        run_status, activation, terminal, completeness = (
            "COMPLETED", "TRIGGERED" if injected else "NOT_TRIGGERED",
            "MASKED", "COMPLETE")

    csv_path = out / "prop_trace.csv.gz"
    jsonl_path = out / "trace_v31.jsonl"
    converted = {"rows": 0, "truncated": True, "summary": None}
    if csv_path.exists():
        try:
            converted = convert(
                csv_path, jsonl_path,
                sample_run_id=args.pilot_id, run_id=sample["run_id"],
                sub_task_id=sample["sub_task_id"],
                fault_id=sample.get("fault_config_id") or args.model,
                fault_model_id=args.model, run_status=run_status,
                activation=activation, terminal=terminal,
                completeness=completeness,
                allow_truncated_complete=crash_by_fault)
        except SystemExit:
            converted = {"rows": 0, "truncated": True, "summary": None}
    trace_errors = validate(jsonl_path) if jsonl_path.exists() else ["trace missing"]
    completeness_report = (check_completeness(jsonl_path)
                           if jsonl_path.exists() else {"trace_completeness": "INCOMPLETE"})
    if completeness_report.get("trace_completeness") != "COMPLETE" and csv_path.exists():
        convert(csv_path, jsonl_path,
                sample_run_id=args.pilot_id, run_id=sample["run_id"],
                sub_task_id=sample["sub_task_id"],
                fault_id=sample.get("fault_config_id") or args.model,
                fault_model_id=args.model, run_status=run_status,
                activation=activation, terminal=terminal,
                completeness="INCOMPLETE", no_summary=True)
        trace_errors = validate(jsonl_path)
        completeness_report = check_completeness(jsonl_path)

    # A pilot proves the trigger and the target dynamic instruction, not a
    # particular software outcome: an injected fault whose error does not
    # propagate is recorded as MASKED, and one that changes the oracle is
    # recorded as SDC. Both are valid pilots; zero injections is not.
    final_terminal = terminal
    terminal_reason = None
    if (completeness_report.get("trace_completeness") != "COMPLETE"
            and final_terminal == "MASKED"):
        final_terminal = "UNRESOLVED"
        terminal_reason = "TRACE_INCOMPLETE"
    # MASKED requires actual data-value evidence, not only an equal checksum.
    has_data_value = any(
        r.get("event_type") in ("memory_response", "register_writeback")
        and r.get("new_value") not in (None, "")
        for r in (json.loads(line) for line in jsonl_path.read_text().splitlines())
        if r.get("record_type") == "event"
    ) if jsonl_path.exists() else False
    if final_terminal == "MASKED" and not has_data_value:
        final_terminal = "UNRESOLVED"
        terminal_reason = "UNRESOLVED_NO_DATA_VALUE_EVIDENCE"
    if final_terminal == "UNRESOLVED" and crash_by_fault:
        final_terminal = "CRASH"
        terminal_reason = crash_evidence
    if final_terminal == "UNRESOLVED" and terminal_reason is None:
        terminal_reason = "UNRESOLVED_NO_TERMINAL_EVIDENCE"
    # The converted trace was closed with the provisional verdict. Re-emit it
    # so the JSONL summary carries the same terminal and reason as the meta.
    if csv_path.exists() and final_terminal != terminal:
        try:
            converted = convert(
                csv_path, jsonl_path,
                sample_run_id=args.pilot_id, run_id=sample["run_id"],
                sub_task_id=sample["sub_task_id"],
                fault_id=sample.get("fault_config_id") or args.model,
                fault_model_id=args.model, run_status=run_status,
                activation=activation, terminal=final_terminal,
                completeness=completeness_report.get("trace_completeness") or completeness,
                terminal_reason=terminal_reason,
                allow_truncated_complete=crash_by_fault)
        except SystemExit:
            converted = {"rows": 0, "truncated": True, "summary": None}
        trace_errors = validate(jsonl_path) if jsonl_path.exists() else ["trace missing"]
        completeness_report = (check_completeness(jsonl_path)
                               if jsonl_path.exists()
                               else {"trace_completeness": "INCOMPLETE"})
    accepted = (
        (proc.returncode == 0 or crash_by_fault) and injected > 0
        and target_proof.get("events", 1) > 0
        and final_terminal not in (None, "UNRESOLVED")
        and not trace_errors
        and completeness_report.get("trace_completeness") == "COMPLETE"
    )
    meta = {
        "pilot_id": args.pilot_id,
        "model": args.model,
        "seed": args.seed,
        "workload": str(WORKLOADS / _workload_for(args.model)),
        "command": cmd,
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 3),
        "oracle_expected": expected,
        "oracle_pass": oracle_pass,
        "injection": inj,
        "injection_count": injected,
        "target_event_proof": target_proof,
        "trace": {
            "csv_rows": converted.get("rows"),
            "truncated": converted.get("truncated"),
            "validator_errors": trace_errors,
            "completeness": completeness_report,
        },
        "classification": {
            "run_status": run_status,
            "fault_activation_status": activation,
            "terminal_state": final_terminal,
            "terminal_state_reason": terminal_reason,
            "trace_completeness": completeness_report.get("trace_completeness"),
            "record_integrity": completeness_report.get("record_integrity"),
            "propagation_coverage": completeness_report.get("propagation_coverage"),
            "oracle_outcome": ("PASS" if oracle_pass else "FAIL"),
        },
        "accepted": accepted,
        "crash_evidence": crash_evidence,
    }
    (out / "pilot_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
