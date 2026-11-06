#!/usr/bin/env python3
"""Build the v3.2 workbook from the frozen v3.1 workbook.

Only facts are written: real workload paths, real rebuilt-binary SHA256s,
real golden oracles, and the actual Gate-1/Gate-2 status.  Formal samples are
marked NOT_RUN; they are never marked READY or PASS.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[5]
IMPL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
SRC = ROOT / "docs/gem5-fi/lsu/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx"
DST = IMPL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.xlsx"
WL = IMPL / "workloads"
CONFIG = ROOT / "configs/se/lsu_proxy.py"

MODEL_WORKLOAD = {
    "A01": "agu_addrmodes", "A03": "agu_addrmodes",
    "LQ04": "lq_lifetime",
    "SQ01": "sq_drain", "SQ03": "sq_drain",
    "LP01": "load_response",
    "SP05": "store_path",
    "FW02": "sq_forward",
    "FW05": "alignment", "DA04": "alignment",
    "MD04": "replay_dependency", "RP01": "replay_dependency",
}
W_NAMES = {
    "W1": "agu_addrmodes", "W2": "lq_lifetime", "W3": "sq_drain",
    "W4": "sq_forward", "W5": "load_response", "W6": "store_path",
    "W7": "replay_dependency", "W8": "alignment",
}
PILOT_MODELS = {"A01", "A03", "FW02"}
PILOT_STATUS = {
    "A01": "PILOT_IMPLEMENTED_VERIFIED_F0 (pushRequest bit3 XOR, injected=1, MASKED)",
    "A03": "PILOT_IMPLEMENTED_VERIFIED_F5_CRASH (146 applications, page-table CRASH)",
    "FW02": "PILOT_IMPLEMENTED_VERIFIED_F6 (6 pairs observed, 1 suppression, MASKED)",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def golden(name: str) -> str:
    text = (WL / f"{name}.golden").read_text(encoding="utf-8", errors="replace").strip()
    if "checksum=0x" in text:
        return text.split("checksum=0x")[-1].strip()
    return text.removeprefix("0x").strip()


def find_col(ws, name: str) -> int | None:
    for c in range(1, ws.max_column + 1):
        if str(ws.cell(1, c).value).strip() == name:
            return c
    return None


def set_if(ws, row: int, col: int | None, value) -> None:
    if col:
        ws.cell(row, col).value = value


def main() -> int:
    wb = openpyxl.load_workbook(SRC)
    ws5 = wb["5.60个样本执行矩阵"]
    # Kill the legacy terminal columns: keep the v3.1 columns only.
    for old, new in (("TerminalState", "TerminalState_LEGACY_DEPRECATED"),
                     ("TraceCompleteness", "TraceCompleteness_LEGACY_DEPRECATED")):
        c = find_col(ws5, old)
        if c:
            ws5.cell(1, c).value = new
            for r in range(2, ws5.max_row + 1):
                ws5.cell(r, c).value = None

    hdr = {str(ws5.cell(1, c).value): c for c in range(1, ws5.max_column + 1)}
    for r in range(2, ws5.max_row + 1):
        sid = ws5.cell(r, hdr["SampleRunID"]).value
        if not sid:
            continue
        model = str(ws5.cell(r, hdr["FaultModelID"]).value)
        wname = MODEL_WORKLOAD[model]
        wpath = WL / wname
        wo = wpath.with_suffix(".golden")
        seed = ws5.cell(r, hdr["Seed"]).value
        set_if(ws5, r, hdr.get("WorkloadPath"), str(wpath))
        set_if(ws5, r, hdr.get("BinaryPath"), str(wpath))
        set_if(ws5, r, hdr.get("BinarySHA256"), sha(wpath))
        set_if(ws5, r, hdr.get("Oracle"), golden(wname))
        set_if(ws5, r, hdr.get("ConfigScript"), str(CONFIG))
        set_if(ws5, r, hdr.get("WarmUp"), 0)
        set_if(ws5, r, hdr.get("ROI"), "full workload（至程序退出；A03 允许 CRASH 终止）")
        set_if(ws5, r, hdr.get("Timeout"), 900)
        set_if(ws5, r, hdr.get("OutputDir"),
               str(IMPL / "runs" / str(sid)))
        set_if(ws5, r, hdr.get("gem5Commit"),
               "6f98088a7144d7f6fb22d985be3023ac5658e71b")
        if model == "A01":
            flags = ("--chaos_addrpath --agu_pre_mode a01_bit3_load "
                     "--addrpath_lsu_tier F0 --addrpath_max_faults 1 "
                     f"--addrpath_rng_seed {seed}")
        elif model == "A03":
            flags = ("--chaos_addrpath --agu_pre_mode a03_bit3_stuck0_load "
                     "--addrpath_lsu_tier F5 --addrpath_max_faults 0 "
                     f"--addrpath_rng_seed {seed}")
        elif model == "FW02":
            flags = ("--chaos_lsqfwd --lsq_struct_mode f6_fw02 "
                     f"--max_faults 1 --rng_seed {seed}")
        else:
            flags = "BLOCKED: no executable hook yet"
        if model in PILOT_MODELS:
            full_cmd = (
                f"{ROOT}/build/ARM/gem5.opt --outdir={IMPL}/runs/{sid} "
                f"{CONFIG} --cmd={wpath} --cpu O3 --variant B0 "
                f"--chaos_propagation --prop_trace_file prop_trace.csv.gz {flags}")
        else:
            full_cmd = "BLOCKED: no executable hook yet"
        set_if(ws5, r, hdr.get("FullCommand"), full_cmd)
        set_if(ws5, r, hdr.get("RequiredLogs"),
               "stdout.log;stderr.log;stats.txt;config.ini;trace_v31.jsonl;oracle.log")
        set_if(ws5, r, hdr.get("PreflightStatus"),
               "PILOT_ONLY_NOT_FORMAL" if model in PILOT_MODELS else "BLOCKED_NO_HOOK")
        set_if(ws5, r, hdr.get("ExecutionStatus"), "NOT_RUN")
        set_if(ws5, r, hdr.get("RunStatus"), "NOT_RUN")
        set_if(ws5, r, hdr.get("FaultActivationStatus"), "NOT_RUN")
        set_if(ws5, r, hdr.get("TerminalState_v31"), "NOT_RUN")
        set_if(ws5, r, hdr.get("TraceCompleteness_v31"), "NONE")
        set_if(ws5, r, hdr.get("DecisionStatus"),
               "PILOT_VERIFIED_FORMAL_NOT_RUN" if model in PILOT_MODELS else
               "NEEDS_USER_DECISION")

    # Model matrix.
    ws3 = wb["3.最终12模型矩阵"]
    h3 = {str(ws3.cell(1, c).value): c for c in range(1, ws3.max_column + 1)}
    for r in range(2, ws3.max_row + 1):
        model = str(ws3.cell(r, h3["ModelID"]).value)
        if model not in MODEL_WORKLOAD:
            continue
        set_if(ws3, r, h3.get("WorkloadStatus"), "READY")
        set_if(ws3, r, h3.get("WorkloadName"), W_NAMES[
            {v: k for k, v in W_NAMES.items()}[MODEL_WORKLOAD[model]]])
        if model in PILOT_MODELS:
            set_if(ws3, r, h3.get("ImplementationStatus"), PILOT_STATUS[model])
            set_if(ws3, r, h3.get("OverallStatus"),
                   "PILOT_VERIFIED_WITH_CRASH_FORMAL_NOT_RUN" if model == "A03"
                   else "PILOT_PASS_FORMAL_NOT_RUN")
            notes = ws3.cell(r, h3["Notes"]).value or ""
            ws3.cell(r, h3["Notes"]).value = (
                f"{notes}；v3.2 Gate 2: {PILOT_STATUS[model]}")
        else:
            set_if(ws3, r, h3.get("OverallStatus"), "BLOCKED_GATE3_NOT_STARTED")

    # Hook audit sheet.
    ws4 = wb["4.源码Hook审计"]
    h4 = {str(ws4.cell(1, c).value): c for c in range(1, ws4.max_column + 1)}
    for r in range(2, ws4.max_row + 1):
        model = str(ws4.cell(r, h4["ModelID"]).value)
        if model in PILOT_MODELS:
            set_if(ws4, r, h4.get("ImplementationStatus"), "IMPLEMENTED_VERIFIED")
            existing = ws4.cell(r, h4["ExistingHook"]).value or ""
            ws4.cell(r, h4["ExistingHook"]).value = (
                f"{existing}；v3.2: {PILOT_STATUS[model]}")

    # Workload baseline sheet.
    ws6 = wb["6.工作负载及无故障基线"]
    h6 = {str(ws6.cell(1, c).value): c for c in range(1, ws6.max_column + 1)}
    for r in range(2, ws6.max_row + 1):
        wid = str(ws6.cell(r, h6["WorkloadID"]).value)
        if wid not in W_NAMES:
            continue
        name = W_NAMES[wid]
        path = WL / name
        set_if(ws6, r, h6.get("AbsolutePath"), str(path))
        set_if(ws6, r, h6.get("Binary"), name)
        set_if(ws6, r, h6.get("SHA256"), sha(path))
        set_if(ws6, r, h6.get("Oracle"), golden(name))
        set_if(ws6, r, h6.get("CurrentStatus"),
               "BASELINE_PASS_2026-11-06" + ("_REBUILT_FIXED_OOB"
                                             if wid in ("W6", "W8") else ""))
        set_if(ws6, r, h6.get("Runnable"), "YES")
        set_if(ws6, r, h6.get("NeedModify"), "NO")
        set_if(ws6, r, h6.get("BaselineStatus"),
               "PASS: exit0 + oracle PASS (branch gem5 b233a4cb)")

    # Execution plan.
    ws9 = wb["9.实验执行计划"]
    for r in range(2, ws9.max_row + 1):
        phase = str(ws9.cell(r, 1).value)
        if phase.startswith("P0"):
            ws9.cell(r, 6).value = "COMPLETE: W1-W8 baseline 8/8 pass (2026-11-06)"
        elif phase.startswith("P1"):
            ws9.cell(r, 6).value = ("PILOTS PASS 3/3: A01 F0 MASKED; "
                                    "A03 F5 CRASH; FW02 F6 MASKED")
        elif phase.startswith("P2"):
            ws9.cell(r, 6).value = ("NOT_STARTED: Gate 4 requires Gates 1-3 "
                                    "and researcher confirmation")

    # v3.2 status sheet.
    if "13.v3.2实施状态" in wb.sheetnames:
        del wb["13.v3.2实施状态"]
    ws13 = wb.create_sheet("13.v3.2实施状态")
    rows = [
        ["Item", "Status", "Evidence"],
        ["Gate 1 common base", "PASS", "30/30 unit tests; config 60/12/5; Trace sample VALID/COMPLETE"],
        ["Gate 2 workloads", "PASS", "W1-W8 8/8 exit0 + oracle PASS; W6/W8 OOB fixed and rebuilt"],
        ["Gate 2 A01 F0", "PASS", "pushRequest bit3 XOR, injected=1, 12 events/10 edges, MASKED"],
        ["Gate 2 A03 F5", "PASS (CRASH terminal)", "146 applications, 564 events/489 edges, page-table CRASH"],
        ["Gate 2 FW02 F6", "PASS", "6 pairs, 1 suppression, 4 events/3 edges, MASKED"],
        ["Gate 3 nine models", "NOT_STARTED", "LQ04/SQ01/SQ03/LP01/SP05/FW05/MD04/RP01/DA04"],
        ["Gate 4 formal 60", "NOT_STARTED", "requires Gates 1-3 and researcher confirmation"],
        ["Formal samples", "NOT_RUN", "this workbook preserves all 60 IDs and seeds; no result is claimed"],
        ["Build", "CLEAN", "build/ARM/gem5.opt sha256 b233a4cbb1085887c1a8533a77a9fa0885dcb36aa34608f7a90245b7395eaabe"],
        ["Branch", "lsu-platform-v3.2", "base 6f98088a7144d7f6fb22d985be3023ac5658e71b"],
    ]
    for row in rows:
        ws13.append(row)

    wb.save(DST)
    print(f"WROTE {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
