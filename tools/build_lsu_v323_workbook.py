#!/usr/bin/env python3
"""Build the authoritative v3.2.3 LSU workbook from v3.2.2.

Only the five FW05 rows change: the formal workload becomes fw05_forward,
its SHA256/Oracle/PilotStatus are frozen, and the historical W8 alignment
configuration is retained in the revision sheet.
"""
from __future__ import annotations

import csv
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
SRC = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx"
DST = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx"
CSV = EXCEL / "60_SAMPLE_MATRIX.csv"

SAMPLE_SHEET = "5.60个样本执行矩阵"
MODEL_SHEET = "3.最终12模型矩阵"
HOOK_SHEET = "4.源码Hook审计"
CHANGE_SHEET = "12.变更记录"
FREEZE_SHEET = "15.FW05配置冻结"

WORKLOAD = str(ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads/fw05_forward")
WORKLOAD_SHA = "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"
GOLDEN = "67afad307642983e"

SAMPLE_VALUES = {
    "FaultLocation": "Forwarding源选择：LSQUnit::read / CHAOSLSQFwd::maybeSubstituteFW05",
    "TargetField": "true_src vs alt_src store data",
    "BitEntryByteIndex": "候选Store数据源",
    "NormalValue": "true_src=youngest matching store",
    "FaultValue": "alt_src=older full-cover store",
    "InjectionMode": "F6",
    "InjectionTiming": "full-coverage forward decision, before memcpy",
    "FaultDuration": "F6 single; wrong-source data enters Load",
    "TargetInstruction": "Load with >=2 distinct stores; alt full-cover",
    "EligibleEventCondition": "distinct older store; full cover; different bytes; younger load",
    "WorkloadPath": WORKLOAD,
    "BinarySHA256": WORKLOAD_SHA,
    "Oracle": GOLDEN,
    "ExecutionStatus": "PILOT_RUN_ACCEPTED",
    "RunStatus": "PILOT_RUN",
    "FaultActivationStatus": "TRIGGERED",
    "TraceCompleteness_v31": "COMPLETE",
    "DecisionStatus": "FROZEN_FW05_WORKLOAD",
    "ConfigFrozen": "NO",
}
TERMINALS = ["SQUASHED", "SDC", "SDC", "SDC", "SDC"]


def _header(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _update_by_header(ws, wanted):
    cols = _header(ws)
    for row in range(2, ws.max_row + 1):
        if str(ws.cell(row, cols["ModelID"]).value) != "FW05":
            continue
        for name, value in wanted.items():
            if name in cols:
                ws.cell(row, cols[name]).value = value


def main():
    wb = openpyxl.load_workbook(SRC)
    ws = wb[SAMPLE_SHEET]
    cols = _header(ws)
    rows = [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, cols["FaultModelID"]).value) == "FW05"]
    if len(rows) != 5:
        raise SystemExit(f"expected 5 FW05 rows, got {len(rows)}")
    for i, r in enumerate(rows):
        for name, value in SAMPLE_VALUES.items():
            ws.cell(r, cols[name]).value = value
        ws.cell(r, cols["TerminalState_v31"]).value = TERMINALS[i]
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value or "")
        marker = "FW05-DEF-v1 frozen workload fw05_forward 2026-11-08"
        if "fw05_forward" not in prov:
            ws.cell(r, cols["v3.2_ConfigProvenance"]).value = (
                prov.rstrip() + "; " + marker
                + "; see excel/FW05_OLD_NEW_DIFF_v3.2.3.md" + ";")

    _update_by_header(wb[MODEL_SHEET], {
        "FaultLocation": SAMPLE_VALUES["FaultLocation"],
        "TargetField": SAMPLE_VALUES["TargetField"],
        "BitEntryByteIndex": SAMPLE_VALUES["BitEntryByteIndex"],
        "NormalValue": SAMPLE_VALUES["NormalValue"],
        "FaultValue": SAMPLE_VALUES["FaultValue"],
        "DecisionStatus": "FROZEN_FW05_WORKLOAD (researcher-approved 2026-11-08)",
        "Notes": "FW05 formal workload frozen to fw05_forward; historical W8 alignment retained in revision sheet",
    })
    _update_by_header(wb[HOOK_SHEET], {
        "FaultDefinition": "错误源选择：正常选择最年轻匹配Store，故障选择更老且同样满足Forwarding条件的Store；不是多Store拼接",
        "TargetInstruction": SAMPLE_VALUES["TargetInstruction"],
        "NormalValue": SAMPLE_VALUES["NormalValue"],
        "FaultValue": SAMPLE_VALUES["FaultValue"],
        "InjectionTiming": SAMPLE_VALUES["InjectionTiming"],
        "DecisionStatus": "FROZEN_FW05_WORKLOAD (researcher-approved 2026-11-08)",
    })

    freeze = wb.create_sheet(FREEZE_SHEET)
    freeze["A1"] = "FW05 formal configuration freeze (2026-11-08)"
    freeze["A1"].font = Font(bold=True, size=12)
    freeze.append([])
    freeze.append(["Field", "Final value"])
    for name, value in [
        ("FaultModelID", "FW05"),
        ("FaultModelName", "Wrong-Source Store-to-Load Forwarding"),
        ("TargetUnit", "FWD"),
        ("TargetSubunit", "Store-to-Load Forwarding Source Selection"),
        ("TargetFunction", "LSQUnit::read / CHAOSLSQFwd::maybeSubstituteFW05"),
        ("TargetField", "true_src vs alt_src store data"),
        ("FaultAction", "SUBSTITUTE_ONE_WRONG_SOURCE"),
        ("WorkloadName", "fw05_forward"),
        ("WorkloadPath", WORKLOAD),
        ("WorkloadSHA256", WORKLOAD_SHA),
        ("Oracle", GOLDEN),
        ("PilotStatus", "R01 SQUASHED/PASS; R02-R05 SDC/FAIL; all accepted"),
        ("Definition", "FW05-DEF-v1 (option A)"),
    ]:
        freeze.append([name, value])
    freeze.append([])
    freeze.append(["Revision", "Old (v3.2.2)", "New (v3.2.3)", "Reason"])
    for row in [
        ("Workload", "W8 alignment",
         "fw05_forward",
         "1. Original W8 alignment cannot reliably trigger the target forwarding fault (probe alt=no)."),
        ("Why the new workload",
         "-", "two distinct 8-byte stores to the same address + load",
         "2. The new workload was validated by five actual pilots (R01 SQUASHED, R02-R05 SDC)."),
        ("History",
         "v3.2.7 pilots and W8 configura- tion retained",
         "historical pilot/trace/package unchanged",
         "3. Original configuration and historical pilots are preserved; nothing is overwritten."),
        ("Scope",
         "all 60 samples NEEDS_USER_DECISION",
         "only FW05 model config frozen; ConfigFrozen stays NO",
         "4. Global Warm-up/ROI still need researcher confirmation; 60-row ConfigFrozen is not set to YES."),
        ("Consistency",
         "Excel WorkloadPath=alignment, pilot override",
         "Excel=CSV=manifest=archive=fw05_forward",
         "5. Excel, CSV, pilot manifests and the workload archive now agree."),
    ]:
        freeze.append(list(row))
    for row in freeze.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in (("A", 30), ("B", 52), ("C", 52), ("D", 70)):
        freeze.column_dimensions[col].width = width

    wb[CHANGE_SHEET].append([
        "FW05工作负载冻结", "W8 alignment (pilot-only fw05_forward override)",
        "fw05_forward (formal)", "researcher-approved 2026-11-08; five pilots validated; "
        "Excel v3.2.3; see excel/FW05_OLD_NEW_DIFF_v3.2.3.md"])

    wb.save(DST)
    with CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
            writer.writerow(["" if v is None else v for v in row])
    print(f"wrote {DST} and {CSV}")


if __name__ == "__main__":
    main()
