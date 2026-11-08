#!/usr/bin/env python3
"""Build the authoritative v3.2.4 LSU workbook from v3.2.3.

Changes are limited to:
  - FW05's five rows: WorkloadPath points at the archived binary (SHA and
    Oracle unchanged); no identity change;
  - SQ03's five rows: PilotStatus/TerminalState reflect the v3.2.8 pilots;
  - SP05's five rows: PilotStatus/TerminalState reflect the v3.2.9 pilots;
  - a revision sheet recording archive repair, strict baselines and status.
ConfigFrozen stays NO for all 60.
"""
from __future__ import annotations

import csv
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
SRC = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx"
DST = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx"
CSV = EXCEL / "60_SAMPLE_MATRIX.csv"
EVID = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9"

SAMPLE_SHEET = "5.60个样本执行矩阵"
REVISION_SHEET = "17.v3.2.9变更记录"
ARCHIVE_BIN = str(ROOT / "docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/bin/fw05_forward")


def _header(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _rows_for(ws, cols, model):
    return [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, cols["FaultModelID"]).value) == model]


def _terminals_from_csv(path: Path) -> list[str]:
    if not path.is_file():
        return ["MASKED"] * 5
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    return [r.get("terminal") or r.get("terminal_state") or "MASKED"
            for r in rows][:5]


def main():
    wb = openpyxl.load_workbook(SRC)
    ws = wb[SAMPLE_SHEET]
    cols = _header(ws)

    # FW05: archive path only (SHA/Oracle already frozen in v3.2.3).
    fw05 = _rows_for(ws, cols, "FW05")
    if len(fw05) != 5:
        raise SystemExit(f"expected 5 FW05 rows, got {len(fw05)}")
    for r in fw05:
        ws.cell(r, cols["WorkloadPath"]).value = ARCHIVE_BIN
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value or "")
        ws.cell(r, cols["v3.2_ConfigProvenance"]).value = (
            prov.rstrip() + "; archive path fixed 2026-11-08 (v3.2.9);"
            + " see excel/FW05_OLD_NEW_DIFF_v3.2.4.md;")

    # SQ03: v3.2.8 pilot status.
    sq03_terms = _terminals_from_csv(EVID / "SQ03_v328_EVIDENCE.csv")
    for i, r in enumerate(_rows_for(ws, cols, "SQ03")):
        ws.cell(r, cols["ExecutionStatus"]).value = "PILOT_RUN_ACCEPTED"
        ws.cell(r, cols["RunStatus"]).value = "PILOT_RUN"
        ws.cell(r, cols["FaultActivationStatus"]).value = "TRIGGERED"
        ws.cell(r, cols["TerminalState_v31"]).value = sq03_terms[i]
        ws.cell(r, cols["TraceCompleteness_v31"]).value = "COMPLETE"
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value or "")
        ws.cell(r, cols["v3.2_ConfigProvenance"]).value = (
            prov.rstrip() + "; v3.2.8 five pilots (MASKED, no consumer);"
            + " probe v3.2.9 in SQ03_Probe_Report_v3.2.9.md;")

    # SP05: v3.2.9 pilot status.
    sp05_terms = _terminals_from_csv(EVID / "SP05_v329_EVIDENCE.csv")
    for i, r in enumerate(_rows_for(ws, cols, "SP05")):
        ws.cell(r, cols["ExecutionStatus"]).value = "PILOT_RUN_ACCEPTED"
        ws.cell(r, cols["RunStatus"]).value = "PILOT_RUN"
        ws.cell(r, cols["FaultActivationStatus"]).value = "TRIGGERED"
        ws.cell(r, cols["TerminalState_v31"]).value = sp05_terms[i]
        ws.cell(r, cols["TraceCompleteness_v31"]).value = "COMPLETE"
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value or "")
        ws.cell(r, cols["v3.2_ConfigProvenance"]).value = (
            prov.rstrip() + "; v3.2.9 premature-completion implementation;"
            + " see SP05_Implementation_v3.2.9.md;")

    # ConfigFrozen must remain NO everywhere.
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, cols["SampleRunID"]).value:
            ws.cell(r, cols["ConfigFrozen"]).value = "NO"

    rev = wb.create_sheet(REVISION_SHEET)
    rev["A1"] = "v3.2.9 revision record (2026-11-08)"
    rev["A1"].font = Font(bold=True, size=12)
    rev.append([])
    rev.append(["Item", "Change", "Reason"])
    for row in [
        ("FW05 WorkloadPath", "workloads/fw05_forward -> FW05_Workload_Archive/bin/fw05_forward",
         "Archive script repaired; the archived exact binary is the runnable input (SHA unchanged)."),
        ("FW05 baselines", "byte_flip/probability 0 -> fw05_older_src/probability 0",
         "Strict matched no-fault baseline; fault-on side rerun on the same final binary."),
        ("FW05 SDC", "R02-R05 SDC retained",
         "Original pilots kept; final-binary recheck reproduces all four checksums."),
        ("SQ03 status", "PILOT_RUN_ACCEPTED / MASKED",
         "v3.2.8 five pilots; no consumer and no SDC; propagation probe added in v3.2.9."),
        ("SP05 status", "PILOT_RUN_ACCEPTED after five pilots",
         "Real completeStore hook implemented; see SP05_Implementation_v3.2.9.md. Not a formal 60-sample result."),
        ("SP05 wording", "FaultDuration corrected from suppressed-completion to premature completion",
         "Legacy v3.2.2 Excel text described the opposite state change; frozen v3.2.8 definition governs."),
        ("ConfigFrozen", "NO for all 60", "Global Warm-up/ROI still need researcher confirmation."),
    ]:
        rev.append(list(row))

    wb.save(DST)
    with CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
            writer.writerow(["" if v is None else v for v in row])
    print(f"wrote {DST} and {CSV}")


if __name__ == "__main__":
    main()
