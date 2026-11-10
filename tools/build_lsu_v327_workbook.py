#!/usr/bin/env python3
"""Build the v3.2.7 LSU workbook from the frozen v3.2.6 (v3.2.12, Task 19).

v3.2.7 = v3.2.6 + the v3.2.12 propagation-closure evidence, and nothing else:

  - new sheet ``22.v3.2.12传播链闭包矩阵`` -- the closure matrix CSV rows
    verbatim (24 columns, one row per (model, binary) group, keys like
    ``A01@0fa610c2``), followed by a blank row, a marker row and the
    per-model status mapping derived from those rows (one row per sheet-3
    model, in sheet-3 order).  ``FinalClassification`` values are never
    merged across binaries (frozen v3.2.12 acceptance standard); the
    per-model mapping therefore reports the group verdicts and a derived
    presence word, never a merged verdict.
  - new sheet ``21.v3.2.12变更记录`` -- the change record for this
    revision, including the sha256 of the closure matrix actually read.
  - sheet ``3.最终12模型矩阵`` column R (Notes): one appended segment per
    model, `` | v3.2.12 audit: <derived status>; <g> groups/<r>
    records/<c> complete; group verdicts: <key: verdict>; ...``.

Every verdict written anywhere is derived programmatically from the
closure matrix CSV at build time; none is hand-typed.  A model with no
matrix row is recorded ``PENDING_NO_ROW`` (currently RP01 -- the matrix
is the Task 16/17 intermediate), and the builder then prints a loud
warning: a workbook built from an intermediate matrix must be
regenerated after the final matrix lands.  The closure matrix path is a
parameter (``--closure-matrix``) exactly so the final build can read the
final matrix.

Every other cell keeps its v3.2.6 value: the 20 pre-existing sheets, the
60 SampleRunID/RunID/SubTaskID/Seed identities, ConfigFrozen=NO, Warm-up/
ROI NEEDS_RESEARCHER_CONFIRMATION, the sheet 9 formal Status NOT_STARTED,
the RP01 DecisionStatus NEEDS_USER_DECISION and every highlighted cell.
The builder verifies both ends: the v3.2.6 source must be the post-A2,
post-v3.2.11-audit workbook (corrected G4, 20 sheets, sheet 20 present)
before anything is read, and the saved v3.2.7 must differ from v3.2.6 in
exactly the appended Notes segments plus the two new sheets.

The content is deterministic (same inputs -> same cell values and sheet
order, enforced by the post-save check); like every openpyxl save, the
container timestamp reflects the build time.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
DEFAULT_SOURCE = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx"
DEFAULT_OUTPUT = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx"
DEFAULT_MATRIX = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12"
                  / "LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv")

MODEL_SHEET = "3.最终12模型矩阵"
SAMPLE_SHEET = "5.60个样本执行矩阵"
PLAN_SHEET = "9.实验执行计划"
HOOK_SHEET = "4.源码Hook审计"
PREV_AUDIT_SHEET = "20.v3.2.11传播链审计"
CHANGELOG_SHEET = "21.v3.2.12变更记录"
AUDIT_SHEET = "22.v3.2.12传播链闭包矩阵"

# the exact v3.2.6 sheet order (18 v3.2.5 sheets + the v3.2.11 revision and
# audit sheets added by the v3.2.11 round)
V326_SHEETS = (
    "1.实验总览", "2.研究问题与Observation映射", "3.最终12模型矩阵",
    "4.源码Hook审计", "5.60个样本执行矩阵", "6.工作负载及无故障基线",
    "7.Trace Hook规范", "8.终态分类", "9.实验执行计划", "10.暂缓研究模型",
    "11.风险与待确认事项", "12.变更记录", "13.v3.2实施状态",
    "13.v3.2.1实施状态", "14.MD04配置冻结", "15.FW05配置冻结",
    "17.v3.2.9变更记录", "18.v3.2.10变更记录", "19.v3.2.11变更记录",
    "20.v3.2.11传播链审计",
)

# sheet 4 G4 carries the A2-corrected LQ04 spans in v3.2.6 (proves the
# source is the post-A2 workbook, not the stale v3.2.5)
V326_G4 = ("LSQUnit::insertLoad (394-463); executeLoad (719-831, "
           "LQ04 hook 796-828); lq04Restore (927-943); commitLoad (945-973); "
           "commitLoads (975-987); squash (1202-1338, "
           "load-side window 1205-1254)")

# the 43 columns of sheet 5 (60-sample execution matrix)
SAMPLE_COLS = (
    "SampleRunID", "RunID", "SubTaskID", "Seed", "FaultModelID",
    "FaultLocation", "TargetField", "BitEntryByteIndex", "NormalValue",
    "FaultValue", "InjectionMode", "InjectionTiming", "FaultDuration",
    "TargetInstruction", "EligibleEventCondition", "EventOrdinal",
    "FaultConfigID", "ContextDifferenceRule", "WorkloadPath", "BinarySHA256",
    "InputHash", "Oracle", "WarmUp", "ROI", "gem5Commit", "BinaryPath",
    "ConfigScript", "FullCommand", "Timeout", "OutputDir", "RequiredLogs",
    "PreflightStatus", "ExecutionStatus", "TerminalState_LEGACY_DEPRECATED",
    "TraceCompleteness_LEGACY_DEPRECATED", "EvidencePath", "DecisionStatus",
    "ConfigFrozen", "RunStatus", "FaultActivationStatus", "TerminalState_v31",
    "TraceCompleteness_v31", "v3.2_ConfigProvenance",
)

# the 24 columns of the v3.2.12 closure matrix CSV (tools/lsu_12model_closure.py)
MATRIX_COLS = (
    "ModelID", "SubUnit", "FaultDefinition", "PilotCount", "InjectionVerified",
    "ActivationVerified", "EarlyAnomalyVerified",
    "IntermediatePropagationVerified", "RegisterWritebackVerified",
    "ConsumerVerified", "CommitVerified", "TerminalVerified",
    "OracleVerified", "RecordIntegrity", "TraceCompleteness",
    "StructuralChainCompleteness", "FaultEffectPropagationCoverage",
    "ObservedTerminal", "ApplicationOracle", "FaultCausality",
    "FinalClassification", "MissingEvidence", "SupplementaryPilotRequired",
    "EvidencePath",
)

COMPLETE_VERDICTS = ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")
# the closed FinalClassification value set (frozen standard §6)
FINAL_VALUES = ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT",
                "LIFECYCLE_ONLY", "PARTIAL", "UNRESOLVED")
IDENTITY_COLS = ("SampleRunID", "RunID", "SubTaskID", "Seed")
NOTES_COL = 18  # column R of sheet 3

# the frozen sheet-3 model rows of the v3.2.6 workbook (identity, not a
# verdict: the builder writes one Notes segment per row, in this order)
MODELS_3 = ("A01", "A03", "LQ04", "SQ01", "SQ03", "LP01", "SP05", "FW02",
            "FW05", "MD04", "RP01", "DA04")


def _fail(msg: str) -> None:
    raise SystemExit(f"build_lsu_v327_workbook: {msg}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cell(ws, coord):
    return ws[coord].value


# ---------------------------------------------------------------- matrix --

def load_matrix(path: Path):
    """Read the closure matrix CSV; loud validation, no interpretation."""
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        _fail(f"{path}: empty closure matrix")
    if tuple(rows[0]) != MATRIX_COLS:
        _fail(f"{path}: unexpected closure-matrix header {rows[0]!r}")
    data = rows[1:]
    for r in data:
        if len(r) != len(MATRIX_COLS):
            _fail(f"{path}: row {r[:1]} has {len(r)} cells, "
                  f"expected {len(MATRIX_COLS)}")
        for name, v in zip(MATRIX_COLS, r):
            if v == "":
                _fail(f"{path}: empty cell in column {name} of {r[0]} "
                      f"(closure-matrix honesty invariant: no empty cells)")
    keys = [r[0] for r in data]
    if len(keys) != len(set(keys)):
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        _fail(f"{path}: duplicate matrix keys {dupes}")
    for r in data:
        if int(r[3]) <= 0:
            _fail(f"{path}: {r[0]}: PilotCount={r[3]}")
        # mixed verdict cells must account for every record of the group
        fc = r[20]
        if fc.startswith("mixed(") and fc.endswith(")"):
            total = sum(int(p.split("=")[1]) for p in fc[6:-1].split(";"))
            if total != int(r[3]):
                _fail(f"{path}: {r[0]}: mixed FinalClassification counts "
                      f"sum to {total}, PilotCount={r[3]}")
    return rows[0], data


def _complete_records(row) -> int:
    """Records of one group whose record-level verdict is complete."""
    fc, count = row[20], int(row[3])
    if fc in FINAL_VALUES:
        return count if fc in COMPLETE_VERDICTS else 0
    if fc.startswith("mixed(") and fc.endswith(")"):
        return sum(int(p.split("=")[1]) for p in fc[6:-1].split(";")
                   if p.split("=")[0] in COMPLETE_VERDICTS)
    _fail(f"unparseable FinalClassification {fc!r}")


def build_rollup(models, matrix):
    """Per-model status mapping derived from the matrix rows.

    Verdicts are never merged across binaries (frozen standard): the
    mapping reports each group's verdict verbatim plus a derived presence
    word, and nothing else.
    """
    rollup = {}
    for model in models:
        rows = [r for r in matrix if r[0].split("@")[0] == model]
        if rows:
            verdicts = "; ".join(f"{r[0]}: {r[20]}" for r in rows)
            joined = " ".join(r[20] for r in rows)
            if "COMPLETE_CAUSAL_CHAIN" in joined:
                status = "COMPLETE_CAUSAL_CHAIN_PRESENT"
            elif "VERIFIED_SINGLE_CONTEXT" in joined:
                status = "VERIFIED_SINGLE_CONTEXT_PRESENT"
            else:
                status = "BELOW_COMPLETE"
            rollup[model] = {
                "MatrixRows": str(len(rows)),
                "Groups": ",".join(r[0] for r in rows),
                "Records": str(sum(int(r[3]) for r in rows)),
                "CompleteRecords": str(sum(_complete_records(r)
                                            for r in rows)),
                "DerivedClosureStatus": status,
                "GroupFinalClassification": verdicts,
            }
        else:
            rollup[model] = {
                "MatrixRows": "0", "Groups": "-", "Records": "0",
                "CompleteRecords": "0", "DerivedClosureStatus":
                "PENDING_NO_ROW",
                "GroupFinalClassification": "no closure-matrix row",
            }
    return rollup


def notes_segment(model: str, entry: dict) -> str:
    if entry["DerivedClosureStatus"] == "PENDING_NO_ROW":
        return (f"v3.2.12 audit: PENDING_NO_ROW; 0 groups/0 records/"
                f"0 complete; no closure-matrix row.")
    return (f"v3.2.12 audit: {entry['DerivedClosureStatus']}; "
            f"{entry['MatrixRows']} groups/"
            f"{entry['Records']} records/"
            f"{entry['CompleteRecords']} complete; "
            f"group verdicts: {entry['GroupFinalClassification']}.")


# --------------------------------------------------------------- verify in --

def verify_inputs(wb, matrix, models):
    if tuple(wb.sheetnames) != V326_SHEETS:
        _fail(f"source is not the v3.2.6 workbook: {wb.sheetnames!r}")
    if _cell(wb[HOOK_SHEET], "G4") != V326_G4:
        _fail(f"{HOOK_SHEET}!G4 does not carry the v3.2.6 corrected value "
              f"(source must be the post-A2 v3.2.6)")
    prev = wb[PREV_AUDIT_SHEET]
    prev_models = [prev.cell(r, 1).value for r in range(2, prev.max_row + 1)]
    if prev_models != ["A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04",
                       "FW05", "SQ03", "SP05", "LQ04"]:
        _fail(f"{PREV_AUDIT_SHEET} does not carry the 11 v3.2.11 audit rows")

    ws5 = wb[SAMPLE_SHEET]
    header = tuple(str(ws5.cell(1, c).value) for c in range(1, 44))
    if header != SAMPLE_COLS:
        _fail(f"{SAMPLE_SHEET}: expected 43 known columns, got {header!r}")
    rows5 = [r for r in range(2, ws5.max_row + 1) if ws5.cell(r, 1).value]
    if len(rows5) != 60:
        _fail(f"{SAMPLE_SHEET}: expected 60 sample rows, got {len(rows5)}")
    frozen_col = header.index("ConfigFrozen") + 1
    for r in rows5:
        if ws5.cell(r, frozen_col).value != "NO":
            _fail(f"{SAMPLE_SHEET}: ConfigFrozen != NO at row {r}")

    for coord in ("F4", "F5", "F6"):
        v = str(_cell(wb[PLAN_SHEET], coord))
        if not v.startswith("NOT_STARTED"):
            _fail(f"{PLAN_SHEET}!{coord}: formal status {v!r} is not "
                  f"NOT_STARTED")

    ws3 = wb[MODEL_SHEET]
    got = [ws3.cell(r, 1).value for r in range(2, ws3.max_row + 1)]
    if tuple(got) != MODELS_3:
        _fail(f"{MODEL_SHEET}: unexpected model rows {got!r} (the v3.2.6 "
              f"source must carry the frozen 12-model rows)")
    matrix_models = {r[0].split("@")[0] for r in matrix}
    unknown = sorted(matrix_models - set(MODELS_3))
    if unknown:
        _fail(f"closure matrix carries models absent from {MODEL_SHEET}: "
              f"{unknown} (a model not wired into the workbook must be "
              f"rejected, not half-routed)")


# ------------------------------------------------------------------ build --

def append_notes(wb, rollup):
    ws3 = wb[MODEL_SHEET]
    for r in range(2, ws3.max_row + 1):
        model = ws3.cell(r, 1).value
        cell = ws3.cell(r, NOTES_COL)
        old = cell.value or ""
        if "v3.2.12 audit:" in old:
            _fail(f"{MODEL_SHEET} row {r}: v3.2.12 segment already present "
                  f"in the v3.2.6 source")
        cell.value = f"{old} | {notes_segment(model, rollup[model])}"


def _wrap(ws, widths):
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def append_audit_sheet(wb, matrix_header, matrix, models, rollup):
    ws = wb.create_sheet(AUDIT_SHEET)
    ws.append(list(matrix_header))
    for row in matrix:
        ws.append(list(row))
    ws.append([])
    ws.append(["Per-model status mapping, derived from the rows above "
               "(verdicts are never merged across binaries; a model with "
               "no row is PENDING_NO_ROW)"])
    ws.append(["ModelID", "MatrixRows", "Groups", "Records",
               "CompleteRecords", "DerivedClosureStatus",
               "GroupFinalClassification"])
    for model in models:
        e = rollup[model]
        ws.append([model, e["MatrixRows"], e["Groups"], e["Records"],
                   e["CompleteRecords"], e["DerivedClosureStatus"],
                   e["GroupFinalClassification"]])
    for c in ws[1]:
        c.font = Font(bold=True)
    for c in ws[len(matrix) + 4]:
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    _wrap(ws, {"A": 34, "B": 12, "C": 60, "D": 22, "E": 34, "F": 12,
               "G": 26, "H": 12, "I": 12, "J": 12, "K": 12, "L": 12,
               "M": 14, "N": 16, "O": 16, "P": 30, "Q": 30, "R": 34,
               "S": 40, "T": 20, "U": 34, "V": 24, "W": 26, "X": 34})


def append_changelog(wb, matrix_path, matrix, rollup):
    sha = _sha256(matrix_path)
    pending = [m for m in rollup
               if rollup[m]["DerivedClosureStatus"] == "PENDING_NO_ROW"]
    today = datetime.date.today().isoformat()
    rows = [
        ("v3.2.12 closure-matrix sheet",
         f"new sheet {AUDIT_SHEET!r} = the {len(matrix)} closure-matrix "
         f"CSV rows verbatim (24 columns, keys ModelID@BinarySHA256) plus "
         f"the derived per-model status mapping "
         f"({len(rollup)} rows, sheet-3 model order).",
         f"source CSV: {matrix_path} (sha256 {sha}); generated by "
         f"tools/lsu_12model_closure.py per the frozen standard "
         f"LSU_Propagation_Acceptance_Standard_v3.2.12.md; verdicts are "
         f"computed per (model, binary) group and never merged across "
         f"binaries."),
        ("Model-status columns (sheet 3 Notes)",
         f"appended one segment ' | v3.2.12 audit: <status>; <g> groups/"
         f"<r> records/<c> complete; group verdicts: ...' to the Notes "
         f"cell (column R) of all {len(rollup)} model rows; no other cell "
         f"of any pre-existing sheet changed.",
         "the segments are derived programmatically from the closure "
         "matrix at build time -- no verdict is hand-typed; a model "
         "without a matrix row is recorded PENDING_NO_ROW."),
        ("Regeneration precondition (INTERMEDIATE matrix)",
         f"this build read the closure matrix at {matrix_path} (sha256 "
         f"{sha}, {len(matrix)} rows); models with no row: "
         f"{', '.join(pending) if pending else 'none'}. The v3.2.12 "
         f"matrix must be the FINAL one before this workbook is "
         f"published: regenerate v3.2.7 with the same command after the "
         f"final matrix lands.",
         "the builder takes --closure-matrix as a parameter precisely so "
         "the final build reads the final matrix; a workbook whose "
         "recorded matrix sha256 is not the final matrix's must not be "
         "published (the sha is recorded here for exactly that check)."),
        ("Unchanged scope",
         "all other cells keep their v3.2.6 values: the 20 pre-existing "
         "sheets, the 60 SampleRunID/RunID/SubTaskID/Seed identities, "
         "ConfigFrozen=NO (sheet 5), Warm-up/ROI "
         "NEEDS_RESEARCHER_CONFIRMATION, the sheet 9 formal Status "
         "NOT_STARTED, the RP01 DecisionStatus NEEDS_USER_DECISION, and "
         "every highlighted cell.",
         "the v3.2.6 A2 corrections and the v3.2.11 audit content are "
         "frozen; the v3.2.12 round adds audit evidence and never "
         "rewrites identity or freeze fields."),
        ("Finalization preconditions",
         "final closure matrix (including the RP01 row or its explicit "
         "absence), final binary SHA (current final-candidate sha8 "
         "68c6ce73, full SHA in "
         "logs_v3_2_12/binary_v3212_final_candidate.sha256), and the "
         "W1-W8 rebaseline recorded before the published build.",
         "the closure matrix is keyed per BinarySHA256, so the workbook "
         "build must happen after the matrix, the binary SHA and the "
         "W1-W8 baselines are final; see "
         "audit_v3_2_12/EXCEL_V327_BUILDER_PREP.md."),
    ]
    ws = wb.create_sheet(CHANGELOG_SHEET)
    ws["A1"] = (f"v3.2.12 revision record ({today}; 12-model propagation "
                f"closure audit per "
                f"LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv)")
    ws["A1"].font = Font(bold=True, size=12)
    ws.append([])
    ws.append(["Item", "Change", "Reason"])
    for row in rows:
        ws.append(list(row))
    _wrap(ws, {"A": 34, "B": 64, "C": 88})


# -------------------------------------------------------------- verify out --

def _fill_key(cell):
    fill = cell.fill
    rgb = fill.start_color.rgb if fill.start_color is not None else None
    return (fill.fill_type, rgb)


def verify_output(source: Path, output: Path, matrix_path: Path,
                  matrix_header, matrix, models, rollup):
    old = openpyxl.load_workbook(source, data_only=True)
    new = openpyxl.load_workbook(output, data_only=True)
    expected_sheets = list(V326_SHEETS) + [CHANGELOG_SHEET, AUDIT_SHEET]
    if new.sheetnames != expected_sheets:
        _fail(f"sheet order/name drift: {new.sheetnames!r}")

    changed = 0
    for name in V326_SHEETS:
        wa, wb = old[name], new[name]
        if (wa.max_row, wa.max_column) != (wb.max_row, wb.max_column):
            _fail(f"sheet {name}: dimensions changed")
        for row in range(1, wa.max_row + 1):
            for col in range(1, wa.max_column + 1):
                ca, cb = wa.cell(row, col), wb.cell(row, col)
                va, vb = ca.value, cb.value
                if name == MODEL_SHEET and col == NOTES_COL and row >= 2:
                    model = MODELS_3[row - 2]
                    suffix = f" | {notes_segment(model, rollup[model])}"
                    if not isinstance(va, str) or vb != va + suffix:
                        _fail(f"{name}!{ca.coordinate}: Notes segment is not "
                              f"the derived v3.2.12 append ({vb!r})")
                    changed += 1
                elif va != vb:
                    _fail(f"undocumented change at {name}!"
                          f"{ca.coordinate}: {va!r} -> {vb!r}")
                if _fill_key(ca) != _fill_key(cb):
                    _fail(f"{name}!{ca.coordinate}: highlight changed "
                          f"{_fill_key(ca)} -> {_fill_key(cb)}")
    if changed != len(models):
        _fail(f"expected {len(models)} Notes appends, got {changed}")

    # identity / freeze invariants of sheet 5
    a5, b5 = old[SAMPLE_SHEET], new[SAMPLE_SHEET]
    ca = {str(a5.cell(1, c).value): c for c in range(1, 44)}
    cb = {str(b5.cell(1, c).value): c for c in range(1, 44)}
    if ca != cb:
        _fail("sheet 5 header changed")
    rows = [r for r in range(2, b5.max_row + 1) if b5.cell(r, 1).value]
    if len(rows) != 60:
        _fail(f"sheet 5: expected 60 rows, got {len(rows)}")
    for r in rows:
        for name in IDENTITY_COLS:
            if a5.cell(r, ca[name]).value != b5.cell(r, cb[name]).value:
                _fail(f"sheet 5 row {r}: identity column {name} changed")
        if b5.cell(r, cb["ConfigFrozen"]).value != "NO":
            _fail(f"sheet 5 row {r}: ConfigFrozen != NO")

    # formal execution still not started
    for coord in ("F4", "F5", "F6"):
        if str(new[PLAN_SHEET][coord].value) != \
                str(old[PLAN_SHEET][coord].value):
            _fail(f"{PLAN_SHEET}!{coord}: formal status changed")

    # audit sheet: matrix rows byte-for-byte, then the derived rollup
    audit = new[AUDIT_SHEET]
    got_header = [audit.cell(1, c).value for c in range(1, 25)]
    if got_header != list(matrix_header):
        _fail(f"{AUDIT_SHEET}: header does not match the CSV")
    for i, row in enumerate(matrix):
        got = [audit.cell(2 + i, c).value for c in range(1, 25)]
        if got != list(row):
            _fail(f"{AUDIT_SHEET}: matrix row {row[0]!r} does not match the "
                  f"CSV byte-for-byte")
    # layout: row 1 header, rows 2..len+1 matrix, row len+2 blank,
    # row len+3 marker, row len+4 rollup header, rows len+5.. rollup
    header_row = len(matrix) + 4
    if audit.cell(header_row, 1).value != "ModelID" or \
            audit.cell(header_row, 7).value != "GroupFinalClassification":
        _fail(f"{AUDIT_SHEET}: rollup header not found at row {header_row}")
    if not str(audit.cell(len(matrix) + 3, 1).value or "").startswith(
            "Per-model status mapping"):
        _fail(f"{AUDIT_SHEET}: marker row missing before the rollup")
    for j, model in enumerate(models):
        got = [audit.cell(header_row + 1 + j, c).value for c in range(1, 8)]
        want = [model, rollup[model]["MatrixRows"], rollup[model]["Groups"],
                rollup[model]["Records"], rollup[model]["CompleteRecords"],
                rollup[model]["DerivedClosureStatus"],
                rollup[model]["GroupFinalClassification"]]
        if got != want:
            _fail(f"{AUDIT_SHEET}: rollup row {model} is {got!r}, "
                  f"expected {want!r}")

    # changelog sheet
    log = new[CHANGELOG_SHEET]
    if [log.cell(3, c).value for c in range(1, 4)] != ["Item", "Change",
                                                       "Reason"]:
        _fail(f"{CHANGELOG_SHEET}: header row is not Item/Change/Reason")
    data = [row for row in log.iter_rows(min_row=4, values_only=True)
            if row and row[0]]
    if len(data) < 5:
        _fail(f"{CHANGELOG_SHEET}: fewer than 5 data rows")
    text = " ".join(str(v) for row in log.iter_rows(values_only=True)
                    for v in row if v is not None)
    if _sha256(matrix_path) not in text:
        _fail(f"{CHANGELOG_SHEET}: matrix sha256 not recorded")
    print(f"verified: {changed} Notes segments appended; {len(matrix)} "
          f"matrix rows byte-for-byte; {len(rollup)} rollup rows; "
          f"{len(data)} change-log rows; highlights and identities intact")
    return pending_models(rollup)


def pending_models(rollup):
    return [m for m in rollup
            if rollup[m]["DerivedClosureStatus"] == "PENDING_NO_ROW"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                    help="frozen v3.2.6 workbook to read (never modified)")
    ap.add_argument("--closure-matrix", type=Path, default=DEFAULT_MATRIX,
                    help="v3.2.12 closure matrix CSV the statuses are "
                    "derived from")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                    help="v3.2.7 workbook to write")
    args = ap.parse_args(argv)

    if args.source == args.output:
        _fail("--output must differ from --source (the frozen v3.2.6 "
              "workbook is never overwritten)")
    for path in (args.source, args.closure_matrix):
        if not path.is_file():
            _fail(f"input not found: {path}")

    matrix_header, matrix = load_matrix(args.closure_matrix)
    print(f"closure matrix: {args.closure_matrix} "
          f"({len(matrix)} rows, sha256 {_sha256(args.closure_matrix)})")

    wb = openpyxl.load_workbook(args.source)
    models = [wb[MODEL_SHEET].cell(r, 1).value
              for r in range(2, wb[MODEL_SHEET].max_row + 1)]
    verify_inputs(wb, matrix, models)

    rollup = build_rollup(models, matrix)
    append_notes(wb, rollup)
    append_changelog(wb, args.closure_matrix, matrix, rollup)
    append_audit_sheet(wb, matrix_header, matrix, models, rollup)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    pending = verify_output(args.source, args.output, args.closure_matrix,
                            matrix_header, matrix, models, rollup)
    print(f"wrote {args.output}")
    if pending:
        print("WARNING: the closure matrix has no row for "
              f"{', '.join(pending)} (recorded PENDING_NO_ROW). If this is "
              f"not the FINAL matrix, this workbook is not publishable -- "
              f"regenerate it after the final matrix lands "
              f"(see audit_v3_2_12/EXCEL_V327_BUILDER_PREP.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
