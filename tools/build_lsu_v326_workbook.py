#!/usr/bin/env python3
"""Build the authoritative v3.2.6 LSU workbook from v3.2.5 (v3.2.11, task A2).

Changes are limited to the LQ04 source-line corrections transcribed from
``docs/gem5-fi/lsu/implementation_v3_2/LQ04_Source_Audit_line_corrections_v3.2.11.md``
(the authoritative corrected values; §1.4/§5/§6 for sheet 4, §7.1 for
sheet 7, §7.2/§7.3 for sheet 11):
  - sheet ``4.源码Hook审计`` row 4 (LQ04) ``G4`` FunctionName: the verified
    spans insertLoad 394-463, executeLoad 719-831 (LQ04 hook 796-828),
    lq04Restore 927-943, commitLoad 945-973, commitLoads 975-987,
    squash 1202-1338 (load-side window 1205-1254);
  - sheet ``7.Trace Hook规范`` ``D20`` (Node=LQ): the corrected range list
    incl. the re-verified ``LSQUnit::read()`` 1641-2074;
  - sheet ``11.风险与待确认事项`` ``F19`` (R18) / ``F33`` (R32) / ``F45``
    (R44) CurrentEvidence line references;
  - new sheet ``19.v3.2.11变更记录`` recording the corrections, the round
    scope and the platform note.

Every other cell keeps its v3.2.5 value: the 60
SampleRunID/RunID/SubTaskID/Seed identities, ConfigFrozen=NO, Warm-up/ROI
NEEDS_RESEARCHER_CONFIRMATION, RP01 DecisionStatus NEEDS_USER_DECISION and
the frozen LQ04 fault-definition fields of sheet 4 row 4 (correction doc
§4 -- no fault-definition field is changed). The builder verifies both
ends: the v3.2.5 source must carry exactly the documented stale values
before they are overwritten, and the saved v3.2.6 must differ from v3.2.5
in exactly the five corrected cells (plus the new sheet).

Note: ``platform/run_pilot.py``'s EXCEL constant still points at v3.2.4 and
is deliberately NOT repointed by this task; the gap is recorded in the
change-log sheet. Later tasks of the round regenerate this same file with
further changes (extend CHANGED accordingly).

The content is deterministic (same input -> same cell values and sheet
order, enforced by the post-save check); like every openpyxl save, the
container timestamp reflects the build time.
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
SRC = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx"
DST = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx"

HOOK_SHEET = "4.源码Hook审计"
TRACE_SHEET = "7.Trace Hook规范"
RISK_SHEET = "11.风险与待确认事项"
REVISION_SHEET = "19.v3.2.11变更记录"

OLD_G4 = ("LSQUnit::insertLoad (353-414); commitLoad (775-798); "
          "squash (986-1020); clear/pop_front")
NEW_G4 = ("LSQUnit::insertLoad (394-463); executeLoad (719-831, "
          "LQ04 hook 796-828); lq04Restore (927-943); commitLoad (945-973); "
          "commitLoads (975-987); squash (1202-1338, "
          "load-side window 1205-1254)")

OLD_D20 = "lsq_unit.cc:353-414,775-798,986-1020,1376-1727"
NEW_D20 = ("lsq_unit.cc:394-463,719-831,927-943,945-973,975-987,"
           "1202-1338,1641-2074")

OLD_F19 = "lsq_unit.cc:775-798,986-1020"
NEW_F19 = "lsq_unit.cc:945-973,1202-1338"
OLD_F33 = "lsq_unit.cc:775-798"
NEW_F33 = "lsq_unit.cc:945-973"
OLD_F45 = "lsq_unit.hh:107-125; lsq.hh:539"
NEW_F45 = "lsq_unit.hh:117-140; lsq.hh:539"

# (sheet, coordinate): (v3.2.5 value, v3.2.6 value) -- the only cells this
# builder may change.
CHANGED = {
    (HOOK_SHEET, "G4"): (OLD_G4, NEW_G4),
    (TRACE_SHEET, "D20"): (OLD_D20, NEW_D20),
    (RISK_SHEET, "F19"): (OLD_F19, NEW_F19),
    (RISK_SHEET, "F33"): (OLD_F33, NEW_F33),
    (RISK_SHEET, "F45"): (OLD_F45, NEW_F45),
}

REVISION_ROWS = [
    ("A2 LQ04 line numbers — sheet 4 G4 (LQ04-F0-W2-S01)",
     f"{OLD_G4}  ->  {NEW_G4}",
     "LQ04_Source_Audit_line_corrections_v3.2.11.md §1.4/§5/§6: "
     "grep-verified spans of CHAOS/gem5/src/cpu/o3/lsq_unit.cc (definitions "
     "at :395/:720/:928/:946/:976/:1203; closing braces "
     ":463/:831/:943/:973/:987/:1338); the v3.2.5 ranges dated from the "
     "LSU_Source_Code_Evidence_v3.md era and were already stale at v3.2.5 "
     "publication; executeLoad, the LQ04 hook, lq04Restore and commitLoads "
     "were absent from the row and are now recorded."),
    ("A2 LQ node line numbers — sheet 7 D20 (Node=LQ)",
     f"{OLD_D20}  ->  {NEW_D20}",
     "Same document §7.1: like-for-like correction of the four v3.1-era "
     "ranges in source order, plus executeLoad/lq04Restore/commitLoads, "
     "which since v3.2.10 carry the LQ node lifecycle trace (719-831 "
     "contains the LQ04 hook 796-828); LSQUnit::read() re-verified at "
     "1641-2074 (name :1642)."),
    ("A2 LQ04 risk evidence — sheet 11 F19 (R18) / F33 (R32) / F45 (R44)",
     f"F19: {OLD_F19} -> {NEW_F19}; F33: {OLD_F33} -> {NEW_F33}; "
     f"F45: {OLD_F45} -> {NEW_F45}",
     "Same document §7.2/§7.3: R18/R32 cite commitLoad/squash at the "
     "v3.1-era positions; R44's lsq.hh:539 (LSQRequest::freeLSQEntry) is "
     "exact at HEAD, and the v3.2.10 side-channel insertion shifted "
     "~LSQEntry to :117-127 and clear() to :129-140 (117-140 covers both; "
     "clear() now opens with assert(!_lq04Corrupt) :132). The risk status "
     "cells are not altered in this revision."),
    ("v3.2.11 round scope",
     "v3.2.6 = v3.2.5 + the five corrected cells above + this change-record "
     "sheet; the round's other work (LQ04 propagation-semantics "
     "adjudication, role-exclusive control acceptance, watchdog exit-code "
     "propagation, LQ04 source-line audit) lives in the round documents and "
     "code, not in workbook cells.",
     "v3.2.11 round (2026-11-09..2026-11-10) tasks 1-7; the audit matrix, "
     "11-model propagation audit reports and the RP01 design land in later "
     "tasks and will extend this workbook."),
    ("Unchanged scope",
     "All other cells keep their v3.2.5 values: the 60 "
     "SampleRunID/RunID/SubTaskID/Seed identities, ConfigFrozen=NO, "
     "Warm-up/ROI NEEDS_RESEARCHER_CONFIRMATION, RP01 DecisionStatus "
     "NEEDS_USER_DECISION, and the frozen LQ04 fault-definition fields of "
     "sheet 4 row 4 (TargetField H4, NormalValue K4/AB4, FaultValue L4/AC4, "
     "InjectionTiming M4, Duration N4).",
     "Correction document §4: no fault-definition field is changed by the "
     "line-number corrections; the v3.2.10 decision-D6 identity freeze "
     "remains in force."),
    ("Platform EXCEL constant (not repointed)",
     "docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py still sets "
     "EXCEL to gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx and keeps "
     "reading the v3.2.4 rows; this revision deliberately does not repoint "
     "it.",
     "The A2 task corrects workbook content only; repointing the platform's "
     "EXCEL constant to a newer workbook is left to the later platform / "
     "final-matrix tasks of this round, so the gap is recorded here "
     "explicitly."),
]


def _expect(ws, coord, expected, what):
    got = ws[coord].value
    if got != expected:
        raise SystemExit(f"{ws.title}!{coord} ({what}): expected "
                         f"{expected!r}, got {got!r}")


def _verify_inputs(wb):
    """The v3.2.5 source must carry exactly the documented stale values
    (correction doc §5/§7) and must not already contain the revision."""
    if REVISION_SHEET in wb.sheetnames:
        raise SystemExit(f"{SRC} already contains {REVISION_SHEET}")
    if len(wb.sheetnames) != 18:
        raise SystemExit(f"expected 18 sheets in v3.2.5, "
                         f"got {len(wb.sheetnames)}")

    hook = wb[HOOK_SHEET]
    lq_rows = [r for r in range(2, hook.max_row + 1)
               if hook.cell(r, 1).value == "LQ04"]
    if lq_rows != [4]:
        raise SystemExit(f"expected LQ04 alone in sheet 4 row 4, got rows "
                         f"{lq_rows}")
    _expect(hook, "B4", "LQ04-F0-W2-S01", "SubTaskID")
    _expect(hook, "G4", OLD_G4, "stale FunctionName")

    trace = wb[TRACE_SHEET]
    _expect(trace, "A20", "Node", "Category")
    _expect(trace, "B20", "LQ", "Item")
    _expect(trace, "D20", OLD_D20, "stale SourceLocation")

    risk = wb[RISK_SHEET]
    _expect(risk, "A19", "R18", "RiskID")
    _expect(risk, "C19", "LQ04", "RelatedModel")
    _expect(risk, "F19", OLD_F19, "stale CurrentEvidence")
    _expect(risk, "A33", "R32", "RiskID")
    _expect(risk, "C33", "LQ04", "RelatedModel")
    _expect(risk, "F33", OLD_F33, "stale CurrentEvidence")
    _expect(risk, "A45", "R44", "RiskID")
    _expect(risk, "C45", "LQ04", "RelatedModel")
    _expect(risk, "F45", OLD_F45, "stale CurrentEvidence")


def _append_revision_sheet(wb):
    rev = wb.create_sheet(REVISION_SHEET)
    rev["A1"] = ("v3.2.11 revision record (2026-11-10; A2 LQ04 source-line "
                 "corrections per LQ04_Source_Audit_line_corrections_v3.2.11"
                 ".md)")
    rev["A1"].font = Font(bold=True, size=12)
    rev.append([])
    rev.append(["Item", "Change", "Reason"])
    for row in REVISION_ROWS:
        rev.append(list(row))
    for row in rev.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in (("A", 34), ("B", 64), ("C", 88)):
        rev.column_dimensions[col].width = width


def _verify_output():
    """The saved v3.2.6 must differ from v3.2.5 in exactly the five
    corrected cells (old -> new as documented) plus the new sheet."""
    old = openpyxl.load_workbook(SRC, data_only=True)
    new = openpyxl.load_workbook(DST, data_only=True)
    if new.sheetnames != old.sheetnames + [REVISION_SHEET]:
        raise SystemExit("sheet order/name drift between v3.2.5 and v3.2.6")
    for name in old.sheetnames:
        wa, wb = old[name], new[name]
        if (wa.max_row, wa.max_column) != (wb.max_row, wb.max_column):
            raise SystemExit(f"sheet {name}: dimensions changed")
        for row in range(1, wa.max_row + 1):
            for col in range(1, wa.max_column + 1):
                coord = wa.cell(row, col).coordinate
                va = wa.cell(row, col).value
                vb = wb.cell(row, col).value
                if (name, coord) in CHANGED:
                    if va != CHANGED[(name, coord)][0] or \
                            vb != CHANGED[(name, coord)][1]:
                        raise SystemExit(f"{name}!{coord}: {va!r} -> {vb!r} "
                                         f"is not the documented correction")
                elif va != vb:
                    raise SystemExit(f"undocumented change at "
                                     f"{name}!{coord}: {va!r} -> {vb!r}")
    rev = new[REVISION_SHEET]
    data = [row for row in rev.iter_rows(min_row=4, values_only=True)
            if row and row[0]]
    if len(data) < 2:
        raise SystemExit("revision sheet has fewer than 2 data rows")
    print(f"verified: only {len(CHANGED)} cells changed + {REVISION_SHEET} "
          f"({len(data)} rows)")


def main():
    wb = openpyxl.load_workbook(SRC)
    _verify_inputs(wb)

    wb[HOOK_SHEET]["G4"] = NEW_G4
    wb[TRACE_SHEET]["D20"] = NEW_D20
    wb[RISK_SHEET]["F19"] = NEW_F19
    wb[RISK_SHEET]["F33"] = NEW_F33
    wb[RISK_SHEET]["F45"] = NEW_F45

    _append_revision_sheet(wb)
    wb.save(DST)
    _verify_output()
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
