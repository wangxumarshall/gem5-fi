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
import terminal_rules  # noqa: E402
from tools.prop_trace_to_v31 import convert  # noqa: E402

ROOT = Path(__file__).resolve().parents[5]
EXCEL = ROOT / "docs/gem5-fi/lsu/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx"
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOADS = IMPL / "workloads"


def _workload_for(model: str) -> str:
    return {"A01": "agu_addrmodes", "A03": "agu_addrmodes",
            "FW02": "sq_forward", "SQ01": "sq_drain",
            "DA04": "alignment", "LP01": "load_response",
            "MD04": "replay_dependency"}[model]


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


def _sq01_summary(path: Path) -> dict:
    events = []
    if not path.exists():
        return {"events": events, "injected": 0}
    pattern = re.compile(
        r"seq:\s*(\d+).*sq_idx:\s*(\d+).*entry_generation:\s*(\d+)"
        r".*old_byte0:\s*0x([0-9a-fA-F]+).*new_byte0:\s*0x([0-9a-fA-F]+)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: lsq_write_sq_entry" not in line:
            continue
        m = pattern.search(line)
        if m:
            events.append({"seq": int(m[1]), "idx": int(m[2]),
                           "gen": int(m[3]), "old": int(m[4], 16),
                           "new": int(m[5], 16)})
    return {"events": events, "injected": len(events)}


def _da04_summary(path: Path) -> dict:
    events = []
    if not path.exists():
        return {"events": events, "injected": 0}
    pattern = re.compile(
        r"seq:\s*(\d+).*sq_idx:\s*(\d+).*entry_generation:\s*(\d+)"
        r".*old_addr:\s*0x([0-9a-fA-F]+).*new_addr:\s*0x([0-9a-fA-F]+)"
        r".*size:\s*(\d+).*old_be:\s*0x([0-9a-fA-F]+)"
        r".*new_be:\s*0x([0-9a-fA-F]+).*changed_bit:\s*(\d+)")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "Site: lsq_pushRequest_byte_enable" not in line:
            continue
        m = pattern.search(line)
        if m:
            events.append({"seq": int(m[1]), "sq_idx": int(m[2]),
                           "gen": int(m[3]), "old_addr": int(m[4], 16),
                           "new_addr": int(m[5], 16), "size": int(m[6]),
                           "old_be": int(m[7], 16), "new_be": int(m[8], 16),
                           "changed_bit": int(m[9])})
    return {"events": events, "injected": len(events)}


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


def _md04_events(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(
            r"Tick:\s*(\d+).*load_seq=(\d+), store_seq=(\d+), "
            r"addr=0x([0-9a-fA-F]+), size=(\d+), "
            r"store_addr=0x([0-9a-fA-F]+), store_size=(\d+), "
            r"load_pc=0x([0-9a-fA-F]+), store_pc=0x([0-9a-fA-F]+), "
            r"sq_entry_id=(-?\d+), sq_entry_generation=(\d+), "
            r"lq_entry_id=(-?\d+), lq_entry_generation=(\d+), "
            r"eligible_ordinal=(\d+), event_ordinal=(\d+), seed=(\d+), "
            r"load_complete=(\d+).*faults_injected:\s*(\d+)", line)
        if m:
            out.append({
                "tick": int(m[1]), "load_seq": int(m[2]),
                "store_seq": int(m[3]), "addr": int(m[4], 16),
                "size": int(m[5]), "store_addr": int(m[6], 16),
                "store_size": int(m[7]), "load_pc": int(m[8], 16),
                "store_pc": int(m[9], 16), "sq_entry_id": int(m[10]),
                "sq_entry_generation": int(m[11]), "lq_entry_id": int(m[12]),
                "lq_entry_generation": int(m[13]),
                "eligible_ordinal": int(m[14]), "event_ordinal": int(m[15]),
                "seed": int(m[16]), "load_complete": int(m[17]),
                "target_pair_id": f"MD04-L{m[2]}-S{m[3]}-T{m[1]}",
                "faults_injected": int(m[18]),
            })
    return out


def _md04_status(path: Path) -> str:
    if not path.exists():
        return "UNKNOWN"
    status = "UNKNOWN"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"CHAOS_MD04_TARGET_STATUS=([A-Z_]+)", line)
        if m:
            status = m[1]
    return status


def _l1dfwd_events(path: Path) -> list[dict]:
    """Parse LP01 injection lines (one per injected load response)."""
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(
            r"Tick:\s*(\d+).*addr=0x([0-9a-fA-F]+), size=(\d+), "
            r"mask=0x([0-9a-fA-F]+),\s*eligible_ordinal=(\d+).*"
            r"faults_injected:\s*(\d+)", line)
        if m:
            out.append({"tick": int(m[1]), "addr": int(m[2], 16),
                        "size": int(m[3]), "mask": int(m[4], 16),
                        "eligible_ordinal": int(m[5]),
                        "faults_injected": int(m[6])})
    return out


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [r for r in (json.loads(line) for line in path.read_text().splitlines())
            if r.get("record_type") == "event"]


def _fault_injection(events: list[dict]) -> dict | None:
    injections = [e for e in events
                  if e.get("event_type") in ("injection", "injection_nochange")]
    return injections[-1] if injections else None


def _seq_events(events: list[dict], seq) -> list[dict]:
    return [e for e in events if seq is not None and e.get("dyn_inst_seq") == seq]


def _terminal_evidence(events: list[dict], pt_fault_addr: str | None,
                       stderr: str) -> dict:
    injection = _fault_injection(events)
    new_value = injection.get("new_value") if injection else None
    match = bool(pt_fault_addr and new_value
                 and str(new_value).lower() == str(pt_fault_addr).lower())
    return {
        "page_table_fault_addr": pt_fault_addr,
        "last_injection_dyn_seq": injection.get("dyn_inst_seq") if injection else None,
        "last_injection_new_value": new_value,
        "address_match": match,
        "stderr_has_page_table_fault": "page table fault" in stderr.lower(),
    }


def _fault_causality(events: list[dict], terminal: str,
                     pt_fault_addr: str | None, model: str = "A01") -> str:
    """Relation between the injected fault and the observed terminal.

    This is deliberately weaker than the terminal itself: a crash that happens
    after an injection is not claimed to be caused by it.
    """
    injection = _fault_injection(events)
    if injection is None:
        return "UNKNOWN"
    if terminal == "CRASH":
        new_value = injection.get("new_value")
        if (pt_fault_addr and new_value
                and str(new_value).lower() == str(pt_fault_addr).lower()):
            return "DIRECT_ADDRESS_MATCH"
        return "TEMPORAL_ASSOCIATION_ONLY"
    seq = injection.get("dyn_inst_seq")
    if terminal == "SQUASHED":
        if any(e.get("event_type") == "squash" for e in _seq_events(events, seq)):
            return "INDIRECT_EVIDENCE"
        return "TEMPORAL_ASSOCIATION_ONLY"
    if terminal in ("MASKED", "SDC"):
        if model == "SQ01":
            if any(e.get("event_type") == "sq_lifecycle"
                   and e.get("dyn_inst_seq") == seq
                   and ("reason=complete" in (e.get("detail") or "")
                        or "reason=commit" in (e.get("detail") or ""))
                   for e in events):
                return "DIRECT_DATAFLOW_EVIDENCE"
            return "INDIRECT_EVIDENCE"
        if any(e.get("event_type") in ("memory_response", "register_writeback")
               for e in events):
            return "DIRECT_DATAFLOW_EVIDENCE"
        return "INDIRECT_EVIDENCE"
    return "INDIRECT_EVIDENCE"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True,
                    choices=["A01", "A03", "FW02", "SQ01", "DA04", "LP01",
                             "MD04"])
    ap.add_argument("--pilot-id", required=True)
    ap.add_argument("--seed", type=int, default=None,
                    help="override seed; default = the selected Excel context row")
    ap.add_argument("--context-index", type=int, default=1, choices=[1,2,3,4,5],
                    help="R01-R05: select the Excel sample row for this context")
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--gem5", type=Path, default=GEM5)
    ap.add_argument("--preserve-sample-id", action="store_true",
                    help="Keep the Excel SampleRunID/RunID/SubTaskID "
                         "(pilots still write only to --outdir); v3.2.4 DA04")
    ap.add_argument("--event-ordinal", type=int, default=None,
                    help="TEMPORARY_EVENT_SELECTION override for the F0 "
                         "eligible-event ordinal (v3.2.4 DA04 pilots); the "
                         "Excel ordinal is recorded separately")
    args = ap.parse_args(argv)

    cfg = load_config(EXCEL, require_complete=False)
    model_rows = [s for s in cfg["samples"] if s["model_id"] == args.model]
    sample = copy.deepcopy(model_rows[args.context_index - 1])
    excel_seed = sample["seed"]
    excel_event_ordinal = sample.get("event_ordinal")
    if args.event_ordinal is not None:
        sample["event_ordinal"] = args.event_ordinal
    if args.seed is None:
        args.seed = excel_seed
    if args.preserve_sample_id:
        excel = model_rows[args.context_index - 1]
        sample["sample_run_id"] = excel["sample_run_id"]
        sample["run_id"] = excel["run_id"]
        sample["sub_task_id"] = excel["sub_task_id"]
    else:
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
    elif args.model == "SQ01":
        extra = ["--chaos_lsqfwd", "--lsq_struct_mode", "sq01_bit3",
                 "--lsqfwd_lsu_tier", "F0",
                 "--lsqfwd_warmup_events", "0", "--lsqfwd_span_events", "10",
                 "--max_faults", "1", "--rng_seed", str(args.seed),
                 "--lsqfwd_event_ordinal", str(sample.get("event_ordinal") or 1)]
    elif args.model == "DA04":
        extra = ["--chaos_lsqfwd", "--lsq_struct_mode", "da04_be_bit0",
                 "--lsqfwd_lsu_tier", "F0",
                 "--lsqfwd_warmup_events", "0", "--lsqfwd_span_events", "10",
                 "--max_faults", "1", "--rng_seed", str(args.seed),
                 "--lsqfwd_event_ordinal",
                 str(sample.get("event_ordinal") or 1)]
    elif args.model == "MD04":
        extra = ["--chaos_md04", "--md04_first_clock", "0",
                 "--md04_max_faults", "1",
                 "--md04_probability", "1.0",
                 "--md04_rng_seed", str(args.seed),
                 "--md04_event_ordinal",
                 str(sample.get("event_ordinal") or 1)]
    elif args.model == "LP01":
        extra = ["--chaos_l1dfwd", "--l1dfwd_first_clock", "0",
                 "--l1dfwd_max_faults", "1",
                 "--l1dfwd_fault_mask", "0x8",
                 "--l1dfwd_rng_seed", str(args.seed),
                 "--l1dfwd_event_ordinal",
                 str(sample.get("event_ordinal") or 1)]
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
    # build_manifest looks the sample up by SampleRunID: with
    # --preserve-sample-id that is the Excel id, not the pilot id.
    manifest = build_manifest(cfg2, sample["sample_run_id"], args.gem5, CONFIG,
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
    oracle_source = "excel"
    if expected.strip().upper() in ("N/A", "NONE", "", "NAN"):
        golden = WORKLOADS / f"{_workload_for(args.model)}.golden"
        if golden.exists():
            expected = golden.read_text().strip()
            oracle_source = "workload_golden"
    oracle = subprocess.run(
        [sys.executable, str(WORKLOADS / "oracle_check.py"), expected,
         str(out / "stdout.log")], capture_output=True, text=True)
    (out / "oracle.log").write_text(oracle.stdout + oracle.stderr)
    oracle_pass = oracle.returncode == 0

    events: list[dict] = []  # A01/A03 address-path events; empty for FW02
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
    elif args.model == "SQ01":
        inj = _sq01_summary(out / "lsq_fwd_injections.log")
        events = inj.get("events", [])
        target_proof = {
            "site": "lsq_write_sq_entry",
            "events": len(events),
            "all_store_bit3": all(e["new"] == (e["old"] ^ 0x08)
                                  for e in events),
        }
        injected = len(events)
    elif args.model == "DA04":
        inj = _da04_summary(out / "lsq_fwd_injections.log")
        events = inj.get("events", [])
        target_proof = {
            "site": "lsq_pushRequest_byte_enable",
            "events": len(events),
            "all_store_only": True,   # hook is inside the !isLoad branch
            "all_mask_0xf_to_0xe": all(
                e["old_be"] == 0xF and e["new_be"] == 0xE for e in events),
            "all_size_4": all(e["size"] == 4 for e in events),
            "all_addr_unchanged": all(
                e["old_addr"] == e["new_addr"] for e in events),
        }
        injected = len(events)
    elif args.model == "MD04":
        events = _md04_events(out / "md04_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "LSQUnit::checkViolations",
            "events": len(events),
            "target_status": _md04_status(out / "md04_injections.log"),
            "all_store_size_8": all(e["store_size"] == 8 for e in events),
            "all_load_size_ge_8": all(e["size"] >= 8 for e in events),
            "all_real_byte_overlap": all(
                e["store_addr"] <= e["addr"] + e["size"] - 1
                and e["addr"] <= e["store_addr"] + e["store_size"] - 1
                for e in events),
            "all_store_younger_ordering": all(
                e["load_seq"] > e["store_seq"] for e in events),
            "all_targets_selected": all(
                args.event_ordinal is None
                or e["eligible_ordinal"] == args.event_ordinal
                for e in events),
            "all_address_size_data_unchanged": True,
        }
        injected = len(events)
    elif args.model == "LP01":
        events = _l1dfwd_events(out / "l1d_fwd_injections.log")
        inj = {"events": events, "injected": len(events)}
        target_proof = {
            "site": "LSQUnit::completeDataAccess",
            "events": len(events),
            "all_load_only": True,
            "all_mask_0x8": all(e["mask"] == 0x8 for e in events),
            "all_size_nonzero": all(e["size"] > 0 for e in events),
            "all_ordinals_distinct": len({e["eligible_ordinal"]
                                          for e in events}) == len(events),
        }
        injected = len(events)
    else:
        inj = _fw02_summary(out / "lsq_fwd_injections.log")
        target_proof = {"site": "store->load_forward_decision", **inj}
        injected = inj.get("suppressed", 0)

    crash_by_fault = False
    crash_evidence = None
    pt_fault_addr = None
    if proc.returncode != 0 and args.model in ("A01", "A03", "FW02") and injected > 0:
        err = proc.stderr.lower()
        pt_match = re.search(
            r"page table fault when accessing virtual address "
            r"(0x[0-9a-fA-F]+|0)\b", proc.stderr, re.I)
        if pt_match:
            # The panic address is not assumed to be the injected address; it
            # is recorded separately and compared with the trace later.
            crash_by_fault = True
            pt_fault_addr = pt_match.group(1).lower()
            crash_evidence = "page_table_fault_after_injection"
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
    # v3.2.4: chain-scoped adjudication (FW02 defect fix). Only events on the
    # fault's own chain can justify a verdict; a target Load that produced a
    # response and a register writeback but was squashed before commit is
    # SQUASHED, not MASKED. A different dynamic instruction's data cannot
    # rescue the target chain.
    trace_events = _read_events(jsonl_path)
    final_terminal, terminal_reason = terminal_rules.adjudicate(
        trace_events, model=args.model, observed_terminal=terminal,
        oracle_pass=oracle_pass,
        trace_complete=(completeness_report.get("trace_completeness")
                        == "COMPLETE"))
    if final_terminal == "UNRESOLVED" and crash_by_fault:
        final_terminal = "CRASH"
        terminal_reason = crash_evidence
    if final_terminal == "UNRESOLVED" and terminal_reason is None:
        terminal_reason = "UNRESOLVED_NO_TERMINAL_EVIDENCE"

    evidence = _terminal_evidence(trace_events, pt_fault_addr, proc.stderr)
    if crash_evidence:
        crash_evidence += ("_address_match" if evidence["address_match"]
                           else "_no_address_match")
        terminal_reason = crash_evidence
    fault_causality = _fault_causality(trace_events, final_terminal,
                                       pt_fault_addr, args.model)

    # Close the trace with the adjudicated verdict and the structured evidence,
    # so JSONL, pilot_meta and the sweep carry the same fields.
    if csv_path.exists():
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
                observed_terminal=terminal,
                fault_causality=fault_causality,
                terminal_evidence=evidence,
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
        "event_selection": ("TEMPORARY_EVENT_SELECTION (Excel EventOrdinal; "
                            "warm-up/ROI not frozen)"),
        "excel_identity": {
            "run_id": sample["run_id"],
            "sub_task_id": sample["sub_task_id"],
            "sample_run_id": sample["sample_run_id"],
            "seed": sample["seed"],
            "event_ordinal": excel_event_ordinal,
            "event_ordinal_used": sample.get("event_ordinal"),
        },
        "workload": str(WORKLOADS / _workload_for(args.model)),
        "command": cmd,
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 3),
        "oracle_expected": expected,
        "oracle_source": oracle_source,
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
            "observed_terminal": terminal,
            "terminal_state": final_terminal,
            "terminal_state_reason": terminal_reason,
            "fault_causality": fault_causality,
            "terminal_evidence": evidence,
            "trace_completeness": completeness_report.get("trace_completeness"),
            "record_integrity": completeness_report.get("record_integrity"),
            "propagation_coverage": completeness_report.get("propagation_coverage"),
            "oracle_outcome": ("PASS" if oracle_pass else "FAIL"),
        },
        "accepted": accepted,
        "accepted_meaning": "record validity; not a claim that the fault caused the terminal",
        "crash_evidence": crash_evidence,
    }
    (out / "pilot_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
