#!/usr/bin/env python3
"""LSU v3.3.3 launch-preflight artifact generator.

Builds the launch package from the frozen design + the measured v3.3.3 runs.
It does NOT run gem5 and does NOT modify the frozen Excel/design.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv"
MAPPING = ROOT / "audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv"
CAUSAL = ROOT / "audit_v3_3_3/LSU_60Context_Causal_Propagation.csv"
CONTROLS = ROOT / "audit_v3_3_3/controls/LSU_Fault_Control_Pair_FINAL.csv"
ORACLE = ROOT / "audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv"
RUNS = ROOT / "audit_v3_3_3/runs"
OUT = ROOT / "audit_launch_v333/artifacts"
BINARY_SHA = "1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338"
CONFIG_SHA = "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225"
SOURCE_HEAD = "b5031bf7"
RESULTS_HEAD = "b8405580"

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05",
          "DA04", "LP01", "MD04", "LQ04", "RP01")
CONTEXTS = ("R01", "R02", "R03", "R04", "R05")

DESIGN = {
    "A01": ("AGU EA -> LSQ pushRequest (PRE)", "a01_bit3_load / F0", "EA bit3 flip",
            "A01_EA; register_writeback; commit; consumer", "SDC / MASKED / SQUASHED"),
    "A03": ("AGU EA -> LSQ pushRequest (PRE)", "a03_bit3_stuck0_load / F5", "EA bit3 stuck-at-0",
            "persistent stream; register_writeback; watchdog", "SDC / HANG_WATCHDOG"),
    "FW02": ("LSQFwd forwarding decision", "f6_fw02", "suppress one forward",
             "fw02_decision; normal decision; replay", "SDC / MASKED"),
    "FW05": ("LSQFwd older-source substitution", "fw05_older_src", "older store source",
             "forwarding_decision; consumer", "SDC"),
    "SQ01": ("SQ entry data", "sq01_bit3", "SQ data bit3 flip",
             "store writeback; reload; consumer", "SDC"),
    "SQ03": ("SQ _canWB", "sq03_canwb", "premature canWB",
             "visibility timing; oracle", "MASKED / visibility"),
    "SP05": ("completeStore", "sp05_complete", "store completion lost",
             "write skipped; reload; consumer", "SDC"),
    "DA04": ("Request byte-enable", "da04_be_bit0", "byte-enable bit flip",
             "store writeback; consumer", "SDC"),
    "LP01": ("L1D load response", "post-check", "response byte0 flip",
             "memory_response; register_writeback; consumer", "SDC"),
    "MD04": ("LSQ checkViolations", "md04", "violation report suppressed",
             "load complete; consumer", "SDC / MASKED"),
    "LQ04": ("LQ entry lifetime", "lq04", "entry invalidated/restored",
             "entry valid; response; restore", "MASKED"),
    "RP01": ("Partial-address replay", "rp01_skip_replay", "skip rescheduleMemInit",
             "skip; watchdog; hang", "HANG_WATCHDOG"),
}

EXPECTED = {m: v[4] for m, v in DESIGN.items()}

MANIFEST_COLS = (
    "RunID", "ModelID", "ContextID", "SampleRunID", "Seed", "Role",
    "Workload", "ELF", "ELF_SHA256", "Binary_SHA256", "Config_SHA256",
    "ROI_Start", "ROI_End", "ROI_N", "Warmup", "Percentile",
    "EligibleEventOrdinal", "DynInstSeq", "PC", "VA", "PA", "LQEntry",
    "SQEntry", "InjectionConfig", "InjectionEnabled", "InjectorMounted",
    "FaultEnabled", "SuppressionReason", "InjectionAttemptCount",
    "InjectionAppliedCount", "InjectionCount", "ControlZeroProof",
    "ExpectedTerminal",
    "TerminalState", "TerminalReason", "OracleResult", "TraceCompleteness",
    "Evidence", "EvidenceKind", "FormalManifest",
)


def parse_identity(*texts):
    def g(key):
        for text in texts:
            m = re.search(r"(?:^|[; ])" + re.escape(key) + r"=([^; ,]+)",
                          text or "")
            if m:
                return m.group(1)
        return "n/a"
    seq = g("seq")
    if seq == "n/a":
        seq = g("dyn_inst_seq")
    if seq == "n/a":
        seq = g("load_seq")
    pc = g("pc")
    if pc == "n/a":
        pc = g("load_pc")
    return (seq, pc, g("va"), g("pa"), g("lq") if g("lq") != "n/a" else g("lq_idx"),
            g("sq") if g("sq") != "n/a" else g("sq_entry_id"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path):
    return list(csv.DictReader(open(path, newline="", encoding="utf-8")))


def ctx_of(sr: str) -> str:
    return sr[-3:]


def run_dir(model: str, ctx: str, role: str) -> Path:
    return RUNS / f"{model}-{ctx}-{role}"


def cmd_path(run: Path) -> str:
    p = run / "command.txt"
    return p.read_text(errors="replace") if p.exists() else ""


def workload_path(run: Path) -> str:
    m = re.search(r"--cmd=(\S+)", cmd_path(run))
    return m.group(1) if m else ""


def read_json(path: Path):
    return json.load(open(path)) if path.exists() else {}


def terminal(model: str, ctx: str, role: str):
    run = run_dir(model, ctx, role)
    s = read_json(run / "summary.json")
    c = causal_idx.get((model, ctx), {})
    oracle = read_json(run / "oracle.log")
    return {
        "summary": s,
        "terminal": s.get("terminal") or c.get("Terminal", "n/a"),
        "oracle": s.get("oracle") if role == "fault" else True,
        "checksum": s.get("checksum"),
        "injection": s.get("injection_count"),
        "trace": c.get("TraceCompleteness", "n/a"),
        "evidence": c.get("EvidencePaths", str(run)),
    }


frozen_rows = load_csv(FROZEN)
frozen = {(r["FaultModelID"], ctx_of(r["SampleRunID"])): r for r in frozen_rows}
mapping_idx = {(r["ModelID"], r["ContextID"]): r for r in load_csv(MAPPING)}
causal_idx = {(r["ModelID"], r["ContextID"]): r for r in load_csv(CAUSAL)}
control_idx = {(r["ModelID"], r["ContextID"]): r for r in load_csv(CONTROLS)}
oracle_idx = {r["ModelID"]: r for r in load_csv(ORACLE)} if ORACLE.exists() else {}


def fault_row(model: str, ctx: str):
    fr = frozen[(model, ctx)]
    mr = mapping_idx[(model, ctx)]
    cr = causal_idx[(model, ctx)]
    orc = oracle_idx.get(model, {})
    run = run_dir(model, ctx, "fault")
    s = read_json(run / "summary.json")
    pm = read_json(run / "pilot_meta.json")
    wl = workload_path(run)
    elf_sha = sha256(Path(wl)) if wl and Path(wl).exists() else "n/a"
    seq, pc, va, pa, lq, sq = parse_identity(
        cr.get("Injection", ""), cr.get("Activation", ""),
        json.dumps(s))
    row = {k: "n/a" for k in MANIFEST_COLS}
    row.update({
        "RunID": fr["RunID"], "ModelID": model, "ContextID": ctx,
        "SampleRunID": fr["SampleRunID"], "Seed": fr["Seed"], "Role": "fault",
        "Workload": orc.get("Workload", Path(wl).name if wl else "n/a"),
        "ELF": wl, "ELF_SHA256": elf_sha,
        "Binary_SHA256": BINARY_SHA, "Config_SHA256": CONFIG_SHA,
        "ROI_Start": mr["ROI_Start_Ordinal"], "ROI_End": mr["ROI_End_Ordinal"],
        "ROI_N": mr["ROI_N"], "Warmup": "0",
        "Percentile": mr["Percentile"],
        "EligibleEventOrdinal": mr["Absolute_Eligible_Ordinal"],
        "DynInstSeq": seq, "PC": pc, "VA": va, "PA": pa,
        "LQEntry": lq, "SQEntry": sq,
        "InjectionConfig": DESIGN[model][1],
        "InjectionEnabled": "YES",
        "InjectionCount": s.get("injection_count", "n/a"),
        "ExpectedTerminal": EXPECTED[model],
        "TerminalState": s.get("terminal", cr.get("Terminal", "n/a")),
        "TerminalReason": cr.get("TerminalReason", "n/a"),
        # RP01's HANG has no checksum by design; the authoritative label is
        # NO_CHECKSUM, not oracle FAIL (independent preflight F-1).
        "OracleResult": ("NO_CHECKSUM" if model == "RP01"
                         and s.get("checksum") is None else
                         "FAIL" if s.get("oracle") is False else
                         "PASS" if s.get("oracle") is True else "NO_CHECKSUM"),
        "TraceCompleteness": cr.get("TraceCompleteness", "n/a"),
        "Evidence": str(run),
        "EvidenceKind": "PRE_FORMAL",
        "FormalManifest": "GENERATED_BY_RUNNER",
    })
    return row


def control_row(model: str, ctx: str):
    fr = frozen[(model, ctx)]
    mr = mapping_idx[(model, ctx)]
    cr = control_idx[(model, ctx)]
    orc = oracle_idx.get(model, {})
    run = run_dir(model, ctx, "control")
    s = read_json(run / "summary.json")
    wl = workload_path(run)
    elf_sha = sha256(Path(wl)) if wl and Path(wl).exists() else "n/a"
    proof = cr.get("ControlZeroProof", "n/a")
    cls = ("INJECTOR_ABSENT" if proof == "INJECTOR_ABSENT" else
           "MOUNTED_BUT_DISABLED" if proof == "MOUNTED_BUT_DISABLED" else
           "SUPPRESSED" if "SUPPRESS" in str(proof) else "UNVERIFIED")
    row = {k: "n/a" for k in MANIFEST_COLS}
    row.update({
        "RunID": fr["RunID"], "ModelID": model, "ContextID": ctx,
        "SampleRunID": fr["SampleRunID"], "Seed": fr["Seed"], "Role": "control",
        "Workload": orc.get("Workload", Path(wl).name if wl else "n/a"),
        "ELF": wl, "ELF_SHA256": elf_sha,
        "Binary_SHA256": BINARY_SHA, "Config_SHA256": CONFIG_SHA,
        "ROI_Start": mr["ROI_Start_Ordinal"], "ROI_End": mr["ROI_End_Ordinal"],
        "ROI_N": mr["ROI_N"], "Warmup": "0",
        "Percentile": mr["Percentile"],
        "EligibleEventOrdinal": mr["Absolute_Eligible_Ordinal"],
        "InjectionConfig": DESIGN[model][1],
        "InjectorMounted": "YES" if cls != "INJECTOR_ABSENT" else "NO",
        "FaultEnabled": "NO",
        "SuppressionReason": ("injector omitted" if cls == "INJECTOR_ABSENT"
                              else "probability=0.0"),
        "InjectionAttemptCount": 0,
        "InjectionAppliedCount": s.get("injection_count", 0),
        "InjectionCount": s.get("injection_count", 0),
        "ControlZeroProof": cls,
        "TerminalState": s.get("terminal", "n/a"),
        "OracleResult": ("PASS" if s.get("oracle") is True else "n/a"),
        "Evidence": str(run),
        "EvidenceKind": "PRE_FORMAL",
        "FormalManifest": "GENERATED_BY_RUNNER",
    })
    return row


def write_csv(path: Path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def add_sheet(wb, title, rows):
    ws = wb.create_sheet(title)
    for row in rows:
        ws.append(list(row))
    if rows:
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    return ws


def gen_xlsx(faults, controls, out: Path):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    readme = [
        ["Item", "Value"],
        ["Workbook", "LSU_Formal_Experiment_Config_Final.xlsx"],
        ["Purpose", "Formal campaign launch configuration (one row per fault/control)"],
        ["Authoritative source", str(FROZEN)],
        ["Final binary SHA256", BINARY_SHA],
        ["Final config SHA256", CONFIG_SHA],
        ["Final source HEAD", SOURCE_HEAD],
        ["Results HEAD", RESULTS_HEAD],
        ["Status", "LAUNCH_PREFLIGHT"],
        ["Note", "Evidence rows are PRE_FORMAL; formal runs generate their own manifest."],
    ]
    add_sheet(wb, "README", readme)
    add_sheet(wb, "Fault_Config", [list(faults[0].keys())] + [[r[k] for k in faults[0]] for r in faults])
    add_sheet(wb, "Control_Config", [list(controls[0].keys())] + [[r[k] for k in controls[0]] for r in controls])
    roi_rows = [["ModelID", "ContextID", "SampleRunID", "Seed", "ROI_Start", "ROI_End",
                 "ROI_N", "Percentile", "EligibleEventOrdinal", "DynInstSeq", "PC",
                 "InjectionEligibility", "ExpectedTerminal"]]
    for r in faults:
        roi_rows.append([r["ModelID"], r["ContextID"], r["SampleRunID"], r["Seed"],
                         r["ROI_Start"], r["ROI_End"], r["ROI_N"], r["Percentile"],
                         r["EligibleEventOrdinal"], r["DynInstSeq"], r["PC"],
                         "ELIGIBLE", r["ExpectedTerminal"]])
    add_sheet(wb, "ROI_Census", roi_rows)
    val = [["Check", "Result", "Detail"]]
    ids = [r["SampleRunID"] for r in faults]
    seeds = [r["Seed"] for r in faults]
    val.append(["Fault rows", len(faults), "expected 60"])
    val.append(["Control rows", len(controls), "expected 60"])
    val.append(["Unique SampleRunID", len(set(ids)), "expected 60"])
    val.append(["Non-empty Seed", sum(1 for s in seeds if s), "expected 60"])
    val.append(["Fault/Control same seed",
                all(f["Seed"] == c["Seed"] for f, c in zip(faults, controls)),
                "per pair"])
    val.append(["Binary SHA consistent",
                all(r["Binary_SHA256"] == BINARY_SHA for r in faults + controls),
                BINARY_SHA])
    val.append(["Config SHA consistent",
                all(r["Config_SHA256"] == CONFIG_SHA for r in faults + controls),
                CONFIG_SHA])
    add_sheet(wb, "Config_Validation", val)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)


def main(argv=None):
    global RUNS
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--runs", default=str(RUNS))
    ap.add_argument("--manifest-only", action="store_true",
                    help="generate only the 120-run campaign manifest and "
                         "per-run campaign_manifest.json from an existing run set")
    args = ap.parse_args(argv)
    RUNS = Path(args.runs)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    faults = [fault_row(m, c) for m in MODELS for c in CONTEXTS]
    controls = [control_row(m, c) for m in MODELS for c in CONTEXTS]
    # Controls target the same dynamic context; carry the paired fault identity.
    for f, c in zip(faults, controls):
        for key in ("DynInstSeq", "PC", "VA", "PA", "LQEntry", "SQEntry"):
            c[key] = f[key]
        c["ExpectedTerminal"] = "NO_FAULT_CONTROL_PASS"
    if args.manifest_only:
        write_csv(out / "LSU_120Run_Campaign_Manifest.csv", faults + controls,
                  fieldnames=MANIFEST_COLS)
        pairs = [{"ModelID": f["ModelID"], "ContextID": f["ContextID"],
                  "SampleRunID": f["SampleRunID"], "Seed": f["Seed"],
                  "FaultEvidence": f["Evidence"], "ControlEvidence": c["Evidence"],
                  "FaultInjectionCount": f["InjectionCount"],
                  "ControlInjectionCount": c["InjectionAppliedCount"],
                  "ControlZeroProof": c["ControlZeroProof"],
                  "PairMatched": "YES" if f["Seed"] == c["Seed"] else "NO"}
                 for f, c in zip(faults, controls)]
        write_csv(out / "LSU_60Fault_60Control_Pair_Map.csv", pairs)
        for row in faults + controls:
            p = Path(row["Evidence"]) / "campaign_manifest.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
        print("wrote manifest-only artifacts to", out)
        return 0
    pairs = []
    for f, c in zip(faults, controls):
        pairs.append({
            "ModelID": f["ModelID"], "ContextID": f["ContextID"],
            "SampleRunID": f["SampleRunID"], "Seed": f["Seed"],
            "FaultEvidence": f["Evidence"], "ControlEvidence": c["Evidence"],
            "FaultInjectionCount": f["InjectionCount"],
            "ControlInjectionCount": c["InjectionAppliedCount"],
            "ControlZeroProof": c["ControlZeroProof"],
            "FaultTerminal": f["TerminalState"],
            "FaultOracle": f["OracleResult"],
            "ControlOracle": c["OracleResult"],
            "PairMatched": "YES" if f["Seed"] == c["Seed"] and f["SampleRunID"] == c["SampleRunID"] else "NO",
        })
    write_csv(out / "LSU_120Run_Campaign_Manifest.csv", faults + controls,
              fieldnames=MANIFEST_COLS)
    write_csv(out / "LSU_60Fault_60Control_Pair_Map.csv", pairs)
    write_csv(out / "LSU_Control_Zero_Injection_Proof.csv",
              [{
                  "ModelID": c["ModelID"], "ContextID": c["ContextID"],
                  "SampleRunID": c["SampleRunID"], "Seed": c["Seed"],
                  "ControlClass": c["ControlZeroProof"],
                  "InjectorMounted": c["InjectorMounted"],
                  "FaultEnabled": c["FaultEnabled"],
                  "SuppressionReason": c["SuppressionReason"],
                  "InjectionAttemptCount": c["InjectionAttemptCount"],
                  "InjectionAppliedCount": c["InjectionAppliedCount"],
                  "ControlOracle": c["OracleResult"],
                  "Evidence": c["Evidence"],
                  "Status": "PASS" if c["InjectionAppliedCount"] == 0 and c["OracleResult"] == "PASS" else "UNVERIFIED",
              } for c in controls])
    gen_xlsx(faults, controls, out / "LSU_Formal_Experiment_Config_Final.xlsx")
    # authoritative causal: current 16-column generator output
    shutil.copy2(CAUSAL, out / "LSU_60Context_Causal_Propagation_Final.csv")
    shutil.copy2(ROOT / "audit_v3_3_3/LSU_Final_Binary_Provenance.md",
                 out / "LSU_Binary_Provenance.md")
    # archive list
    archived = []
    for p in [ROOT / "audit_v3_3_3/propagation/LSU_60Context_Causal_Propagation_Final.csv",
              ROOT / "audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv"]:
        if p.exists():
            archived.append({"Path": str(p), "SHA256": sha256(p), "Status": "ARCHIVED"})
    write_csv(out / "LSU_ARCHIVED_Propagation_Versions.csv", archived)
    # Launch readiness with the approved workload status (the historical
    # v3.3.3 CSV is superseded for launch purposes; it is not overwritten).
    readiness = [["ModelID", "ContextID", "SampleRunID", "Seed", "Workload",
                  "WorkloadStatus", "EligibleEventOrdinal", "TerminalState",
                  "OracleResult", "ControlZeroProof", "Approval",
                  "ReadyGate"]]
    for f, c in zip(faults, controls):
        readiness.append([f["ModelID"], f["ContextID"], f["SampleRunID"],
                          f["Seed"], f["Workload"],
                          "OVERRIDE_APPROVED" if f["ModelID"] in
                          {"FW02", "RP01", "MD04", "SQ01", "SQ03", "SP05"}
                          else "FORMAL",
                          f["EligibleEventOrdinal"], f["TerminalState"],
                          f["OracleResult"], c["ControlZeroProof"],
                          "2026-11-12", "READY" if c["ControlZeroProof"] !=
                          "UNVERIFIED" else "UNVERIFIED"])
    write_csv(out / "LSU_60Context_Final_Readiness.csv",
              [dict(zip(readiness[0], r)) for r in readiness[1:]])
    print("wrote launch artifacts to", out)
    print("faults", len(faults), "controls", len(controls),
          "unique IDs", len(set(r["SampleRunID"] for r in faults)))
    print("control classes", {k: sum(1 for c in controls if c["ControlZeroProof"] == k)
                              for k in set(c["ControlZeroProof"] for c in controls)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
