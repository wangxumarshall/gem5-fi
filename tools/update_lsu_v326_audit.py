#!/usr/bin/env python3
"""v3.2.11: add the 11-model propagation audit and RP01 gate to the v3.2.6 workbook.

Reads the authoritative v3.2.6 workbook, adds:
  - sheet "20.v3.2.11传播链审计" (the 20-column audit matrix),
  - v3.2.11 audit verdicts appended to sheet 3 Notes (column R),
  - audit/RP01 rows appended to "19.v3.2.11变更记录".
Every other cell keeps its v3.2.5/v3.2.6 value. No identity/ConfigFrozen/Warm-up/ROI
field is touched.
"""
from pathlib import Path
import csv
import openpyxl
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
XLSX = BASE / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx"
MATRIX = BASE / "audit_v3_2_11/LSU_11Model_Propagation_Audit_Matrix.csv"

AUDIT = {
    "A01": "v3.2.11 audit: PARTIAL 7/7; wrong EA reaches response/consumer but no correct-EA reference value; crash not address-matched.",
    "A03": "v3.2.11 audit: PARTIAL 6/6; F5 EA transform + response; no writeback/consumer in 5/6; crash not address-matched.",
    "FW02": "v3.2.11 audit: COMPLETE 1/5 control-path (R04 suppressed forward -> memory -> commit, MASKED, data identical); PARTIAL 4/5.",
    "SQ01": "v3.2.11 audit: LIFECYCLE_ONLY 5/5; store byte0 write + L1D write, lane never read.",
    "SQ03": "v3.2.11 audit: LIFECYCLE_ONLY 5/5; premature canWB writeback, lane never read.",
    "LP01": "v3.2.11 audit: COMPLETE 5/5 MASKED; orig vs inj byte0 divergence, consumer received injected value.",
    "SP05": "v3.2.11 audit: LIFECYCLE_ONLY 5/5; completion suppressed, no consumer/commit node.",
    "FW05": "v3.2.11 audit: COMPLETE 4/5 SDC; true vs alt store source, alt data to consumer, oracle 549c...; R01 squashed PARTIAL.",
    "MD04": "v3.2.11 audit: COMPLETE 3/5 MASKED; violation_report_suppressed -> load executes -> consumer -> commit; R01/R04 squashed PARTIAL.",
    "DA04": "v3.2.11 audit: COMPLETE 2/5 unique SDC (v3.2.6 R04/R05; lane0 disabled, consumer got corrupted byte, oracle FAIL recorded); raw oracle.log absent.",
    "LQ04": "v3.2.11 audit: structural COMPLETE, fault-effect LIFECYCLE_ONLY, 5/5 MASKED, oracle PASS; PROPAGATION_VERIFIED=0.",
    "RP01": "v3.2.11 design: candidate A at lsq_unit.cc:2016; IMPLEMENTABLE_WITH_CONDITIONS; DecisionStatus NEEDS_USER_DECISION.",
}

NEW_ROWS = [
    ("11-model propagation audit", "LSU_11Model_Propagation_Audit_Matrix.csv + 11 model reports under audit_v3_2_11/",
     "2026-11-10 raw-trace audit: DA04 2/5, LP01 5/5, MD04 3/5, FW05 4/5 complete; FW02 1/5 control-path; 14/15 complete pilots."),
    ("Verified models", "PROPAGATION_VERIFIED=1: DA04, LP01, MD04, FW05; FW02 not counted (control-path only); LQ04 stays 0.",
     "Fault-effect propagation requires a linked downstream path; implementation/PilotRun alone is not evidence."),
    ("Pilot terminal split", "Among 14 data-effect complete pilots: SDC 6, MASKED 8, SQUASHED 0, CRASH 0.",
     "Derived from the audit matrix, not from historical summaries."),
    ("RP01 design gate", "Candidate A (partial-forward replay loss) recommended; IMPLEMENTABLE_WITH_CONDITIONS; DecisionStatus stays NEEDS_USER_DECISION.",
     "Source audit: rescheduleMemInst at lsq_unit.cc:2016; expected terminal HANG/TIMEOUT; distinct from MD04; no implementation."),
    ("LQ04 closure", "ResearchAdjudication records StructuralChainCompleteness=COMPLETE, FaultEffectPropagationCoverage=LIFECYCLE_ONLY, PROPAGATION_VERIFIED=0.",
     "Historical pilots and pilot_meta.json untouched; watchdog and control semantics fixed for future runs."),
]


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws3 = wb["3.最终12模型矩阵"]
    for row in ws3.iter_rows(min_row=2, max_row=ws3.max_row):
        model = row[0].value
        if model in AUDIT:
            cell = ws3.cell(row=row[0].row, column=18)
            old = cell.value or ""
            tag = "v3.2.11 audit:"
            if tag in old:
                old = old.split(" | v3.2.11 audit:")[0]
            cell.value = f"{old} | {AUDIT[model]}" if old else AUDIT[model]

    if "20.v3.2.11传播链审计" in wb.sheetnames:
        del wb["20.v3.2.11传播链审计"]
    ws20 = wb.create_sheet("20.v3.2.11传播链审计")
    rows = list(csv.reader(open(MATRIX)))
    for r in rows:
        ws20.append(r)
    for c in ws20[1]:
        c.font = Font(bold=True)
    ws20.freeze_panes = "A2"

    ws19 = wb["19.v3.2.11变更记录"]
    existing = {ws19.cell(r, 1).value for r in range(1, ws19.max_row + 1)}
    start = ws19.max_row + 2
    for i, (a, b, c) in enumerate(NEW_ROWS):
        if a in existing:
            continue
        ws19.cell(row=start + i, column=1, value=a)
        ws19.cell(row=start + i, column=2, value=b)
        ws19.cell(row=start + i, column=3, value=c)

    wb.save(XLSX)
    print(f"updated {XLSX} with sheet 20, {len(AUDIT)} Notes updates, {len(NEW_ROWS)} change-log rows")


if __name__ == "__main__":
    main()
