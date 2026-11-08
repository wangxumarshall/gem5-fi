#!/usr/bin/env python3
"""Build the authoritative v3.2.2 LSU workbook from v3.2.1.

Only the MD04 rows change. Identity columns (SampleRunID, RunID, SubTaskID,
Seed) and every other model row are preserved cell-for-cell. A freeze sheet
and a change-log row record the old/new definition.
"""
from __future__ import annotations

import csv
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
SRC = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx"
DST = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx"
CSV = EXCEL / "60_SAMPLE_MATRIX.csv"

SAMPLE_SHEET = "5.60个样本执行矩阵"
MODEL_SHEET = "3.最终12模型矩阵"
HOOK_SHEET = "4.源码Hook审计"
CHANGE_SHEET = "12.变更记录"
FREEZE_SHEET = "14.MD04配置冻结"

FROZEN_SAMPLE = {
    "FaultLocation": "LSQ违规检测：LSQUnit::checkViolations",
    "TargetField": "M5PanicFault return path",
    "BitEntryByteIndex": "目标Store→YoungerLoad违规事件",
    "NormalValue": "ALLOW_M5PANICFAULT_RETURN",
    "FaultValue": "SKIP_M5PANICFAULT_RETURN_ONCE",
    "InjectionMode": "F6",
    "InjectionTiming": "checkViolations检测到真实Store→YoungerLoad违规时",
    "FaultDuration": "单次；仅目标事件；不全局关闭M5PanicFault",
    "TargetInstruction": "OlderStore=8B, YoungerLoad>=8B且真实字节重叠",
    "EligibleEventCondition": "StoreSize=8; LoadSize>=8; YoungerLoad; 真实地址范围与字节重叠",
    "ContextDifferenceRule": "R01-R05同一故障配置；仅动态事件/上下文不同；目标事件不存在时记NOT_TRIGGERED",
}

FREEZE_FIELDS = [
    ("FaultModelID", "MD04"),
    ("FaultModelName", "Store-to-Load Violation Suppression"),
    ("TargetUnit", "LSQ"),
    ("TargetSubunit", "Violation Detection"),
    ("TargetFunction", "LSQUnit::checkViolations"),
    ("TargetField", "M5PanicFault return path"),
    ("NormalValue", "ALLOW_M5PANICFAULT_RETURN"),
    ("FaultValue", "SKIP_M5PANICFAULT_RETURN_ONCE"),
    ("FaultAction", "SUPPRESS_ONE_VIOLATION_REPORT"),
    ("TriggerCondition", "Eligible Store-to-Younger-Load violation"),
    ("StoreSize", "8 bytes"),
    ("InjectionCount", "1"),
    ("AddressModification", "NONE"),
    ("SizeModification", "NONE"),
    ("DataModification", "NONE"),
    ("DefinitionVersion", "MD04-DEF-v2"),
    ("FrozenOn", "2026-11-08"),
    ("SourceDocument", "docs/gem5-fi/lsu/implementation_v3_2/MD04_Definition_Freeze_v3.2.7.md"),
]


def _header(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _update_by_header(ws, wanted):
    cols = _header(ws)
    for row in range(2, ws.max_row + 1):
        if str(ws.cell(row, cols["ModelID"]).value) != "MD04":
            continue
        for name, value in wanted.items():
            if name not in cols:
                continue
            if name in ("NormalValue", "FaultValue") and name in cols:
                # These names appear twice in the hook sheet; update every
                # occurrence (the header map keeps the first only).
                for c in range(1, ws.max_column + 1):
                    if str(ws.cell(1, c).value).strip() == name:
                        ws.cell(row, c).value = value
            else:
                ws.cell(row, cols[name]).value = value


def main():
    wb = openpyxl.load_workbook(SRC)
    ws = wb[SAMPLE_SHEET]
    cols = _header(ws)
    md04_rows = [r for r in range(2, ws.max_row + 1)
                 if str(ws.cell(r, cols["FaultModelID"]).value) == "MD04"]
    if len(md04_rows) != 5:
        raise SystemExit(f"expected 5 MD04 rows, got {len(md04_rows)}")
    for r in md04_rows:
        for name, value in FROZEN_SAMPLE.items():
            ws.cell(r, cols[name]).value = value
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value or "")
        marker = " MD04-DEF-v2 frozen 2026-11-08"
        if marker.strip() not in prov:
            ws.cell(r, cols["v3.2_ConfigProvenance"]).value = (
                prov.rstrip() + ";" + marker
                + "; see excel/MD04_CONFIG_v3.2.2.md" + ";"
            )

    # Model matrix and hook audit: MD04 row only, same semantics.
    _update_by_header(wb[MODEL_SHEET], {
        "FaultLocation": FROZEN_SAMPLE["FaultLocation"],
        "TargetField": FROZEN_SAMPLE["TargetField"],
        "NormalValue": FROZEN_SAMPLE["NormalValue"],
        "FaultValue": FROZEN_SAMPLE["FaultValue"],
        "BitEntryByteIndex": FROZEN_SAMPLE["BitEntryByteIndex"],
        "DecisionStatus": "FROZEN (researcher-confirmed 2026-11-08, MD04-DEF-v2)",
    })
    _update_by_header(wb[HOOK_SHEET], {
        "FaultDefinition": "抑制一次真实Store→YoungerLoad违规的M5PanicFault返回；仅报告路径，不改地址/size/数据",
        "TargetInstruction": FROZEN_SAMPLE["TargetInstruction"],
        "NormalValue": FROZEN_SAMPLE["NormalValue"],
        "FaultValue": FROZEN_SAMPLE["FaultValue"],
        "InjectionTiming": FROZEN_SAMPLE["InjectionTiming"],
        "DecisionStatus": "FROZEN (researcher-confirmed 2026-11-08, MD04-DEF-v2)",
    })

    freeze = wb.create_sheet(FREEZE_SHEET)
    freeze["A1"] = "MD04 final fault definition (frozen 2026-11-08)"
    freeze["A1"].font = Font(bold=True, size=12)
    freeze.append([])
    freeze.append(["Field", "Final value"])
    for name, value in FREEZE_FIELDS:
        freeze.append([name, value])
    freeze.append([])
    freeze.append(["旧定义 vs 新定义", "v3.2.1 (superseded)", "v3.2.2 (frozen)"])
    old_new = [
        ("TargetField", "possibleLoadViolation", "M5PanicFault return path"),
        ("NormalValue", "检测到alias后possibleLoadViolation=true", "ALLOW_M5PANICFAULT_RETURN"),
        ("FaultValue", "跳过一次置位", "SKIP_M5PANICFAULT_RETURN_ONCE"),
        ("FaultAction", "跳过一次置位（load/load snoop flag）", "SUPPRESS_ONE_VIOLATION_REPORT（store→load violation report）"),
        ("TriggerCondition", "真实同地址alias", "StoreSize=8; LoadSize>=8; YoungerLoad; 真实地址范围与字节重叠"),
        ("StoreSize", "未指定", "8 bytes"),
        ("InjectionCount", "F6单次（未明确）", "1"),
        ("AddressModification", "未指定", "NONE"),
        ("SizeModification", "未指定", "NONE"),
        ("DataModification", "未指定", "NONE"),
        ("Reason", "possibleLoadViolation 是 load/load snoop 标志，不是 W7 的 store→younger-load 检测", "checkViolations store 分支的 M5PanicFault 返回是真实违规检测路径"),
    ]
    for row in old_new:
        freeze.append(list(row))
    for row in freeze.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    freeze.column_dimensions["A"].width = 26
    freeze.column_dimensions["B"].width = 60
    freeze.column_dimensions["C"].width = 60

    log = wb[CHANGE_SHEET]
    log.append(["MD04定义冻结", "possibleLoadViolation置位跳过",
                "M5PanicFault返回路径抑制（MD04-DEF-v2）",
                "researcher-confirmed 2026-11-08; excel v3.2.2; MD04_Definition_Freeze_v3.2.7.md"])

    wb.save(DST)

    with CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
            writer.writerow(["" if v is None else v for v in row])
    print(f"wrote {DST} and {CSV}")


if __name__ == "__main__":
    main()
