"""v3.2.7 workbook: v3.2.6 preserved + the v3.2.12 closure audit, derived.

The builder ``tools/build_lsu_v327_workbook.py`` reads the frozen v3.2.6
workbook and the v3.2.12 closure matrix CSV and writes v3.2.7.  These tests
build a throw-away copy into a pytest tmp dir from the *current* matrix and
assert:

  - the v3.2.6 invariants still hold: 20 pre-existing sheets untouched, the
    43 sheet-5 columns, the 60 SampleRunID/RunID/SubTaskID/Seed identities,
    ConfigFrozen=NO, Warm-up/ROI NEEDS_RESEARCHER_CONFIRMATION, the sheet 9
    formal Status NOT_STARTED, and every highlighted cell;
  - the new audit sheet matches the closure matrix CSV byte-for-byte by key;
  - the per-model status mapping and the sheet 3 Notes segments equal an
    independent re-derivation from the same CSV (no hand-typed verdicts
    anywhere, including here);
  - a model with no matrix row is recorded PENDING_NO_ROW and the builder
    warns that the workbook must be regenerated once the final matrix lands.

No expectation below is keyed to a particular matrix vintage: every expected
value is recomputed from the CSV the builder was pointed at, so the suite
stays valid when the final matrix replaces the intermediate one.
"""
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
V326 = BASE / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx"
MATRIX = (BASE / "audit_v3_2_12"
          / "LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv")
BUILDER = ROOT / "tools/build_lsu_v327_workbook.py"

MODEL_SHEET = "3.最终12模型矩阵"
SAMPLE_SHEET = "5.60个样本执行矩阵"
PLAN_SHEET = "9.实验执行计划"
CHANGELOG_SHEET = "21.v3.2.12变更记录"
AUDIT_SHEET = "22.v3.2.12传播链闭包矩阵"
NOTES_COL = 18
IDENTITY_COLS = ("SampleRunID", "RunID", "SubTaskID", "Seed")
MODELS_3 = ("A01", "A03", "LQ04", "SQ01", "SQ03", "LP01", "SP05", "FW02",
            "FW05", "MD04", "RP01", "DA04")
COMPLETE_VERDICTS = ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")
FINAL_VALUES = ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT",
                "LIFECYCLE_ONLY", "PARTIAL", "UNRESOLVED")


def _load(path):
    return openpyxl.load_workbook(path, data_only=True)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_matrix(path):
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return list(csv.reader(fh))


def _complete_records(row):
    """Independent re-derivation of one group's complete-record count."""
    fc, count = row[20], int(row[3])
    if fc in FINAL_VALUES:
        return count if fc in COMPLETE_VERDICTS else 0
    assert fc.startswith("mixed(") and fc.endswith(")"), fc
    return sum(int(p.split("=")[1]) for p in fc[6:-1].split(";")
               if p.split("=")[0] in COMPLETE_VERDICTS)


def _derive(path):
    """The expected per-model mapping, recomputed from the CSV alone."""
    rows = _read_matrix(path)[1:]
    out = {}
    for model in MODELS_3:
        mine = [r for r in rows if r[0].split("@")[0] == model]
        if not mine:
            out[model] = {"MatrixRows": "0", "Groups": "-", "Records": "0",
                          "CompleteRecords": "0", "DerivedClosureStatus":
                          "PENDING_NO_ROW",
                          "GroupFinalClassification": "no closure-matrix row"}
            continue
        joined = " ".join(r[20] for r in mine)
        if "COMPLETE_CAUSAL_CHAIN" in joined:
            status = "COMPLETE_CAUSAL_CHAIN_PRESENT"
        elif "VERIFIED_SINGLE_CONTEXT" in joined:
            status = "VERIFIED_SINGLE_CONTEXT_PRESENT"
        else:
            status = "BELOW_COMPLETE"
        out[model] = {
            "MatrixRows": str(len(mine)),
            "Groups": ",".join(r[0] for r in mine),
            "Records": str(sum(int(r[3]) for r in mine)),
            "CompleteRecords": str(sum(_complete_records(r) for r in mine)),
            "DerivedClosureStatus": status,
            "GroupFinalClassification":
                "; ".join(f"{r[0]}: {r[20]}" for r in mine),
        }
    return out, rows


def _notes_segment(entry):
    if entry["DerivedClosureStatus"] == "PENDING_NO_ROW":
        return ("v3.2.12 audit: PENDING_NO_ROW; 0 groups/0 records/"
                "0 complete; no closure-matrix row.")
    return (f"v3.2.12 audit: {entry['DerivedClosureStatus']}; "
            f"{entry['MatrixRows']} groups/"
            f"{entry['Records']} records/"
            f"{entry['CompleteRecords']} complete; "
            f"group verdicts: {entry['GroupFinalClassification']}.")


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Run the real builder against a temp copy (never the repo xlsx)."""
    out = tmp_path_factory.mktemp("v327") / "workbook-v3.2.7.xlsx"
    cp = subprocess.run(
        [sys.executable, str(BUILDER), "--source", str(V326),
         "--closure-matrix", str(MATRIX), "--output", str(out)],
        capture_output=True, text=True)
    assert cp.returncode == 0, cp.stdout + cp.stderr
    return out, cp


@pytest.fixture(scope="session")
def workbooks(built):
    v326 = _load(V326)
    v327 = _load(built[0])
    return v326, v327


@pytest.fixture(scope="session")
def derived():
    return _derive(MATRIX)


def test_builder_self_check_and_pending_warning(built, derived):
    _, cp = built
    rollup, _ = derived
    assert "verified:" in cp.stdout
    assert "12 Notes segments appended" in cp.stdout
    assert "matrix rows byte-for-byte" in cp.stdout
    assert "wrote" in cp.stdout
    pending = [m for m in rollup
               if rollup[m]["DerivedClosureStatus"] == "PENDING_NO_ROW"]
    if pending:
        # intermediate matrix: the builder must warn loudly
        assert "WARNING" in cp.stdout
        assert all(m in cp.stdout for m in pending)
        assert "not publishable" in cp.stdout
    else:
        assert "WARNING" not in cp.stdout


def test_sheet_count_and_order(workbooks):
    old, new = workbooks
    assert new.sheetnames == old.sheetnames + [CHANGELOG_SHEET,
                                               AUDIT_SHEET]
    assert len(new.sheetnames) == 22


def test_43_columns_60_rows_identity_frozen(workbooks):
    old, new = workbooks
    a, b = old[SAMPLE_SHEET], new[SAMPLE_SHEET]
    assert a.max_column == 43 == b.max_column
    for c in range(1, 44):
        assert a.cell(1, c).value == b.cell(1, c).value, c
    rows = [r for r in range(2, b.max_row + 1) if b.cell(r, 1).value]
    assert len(rows) == 60
    cols = {str(b.cell(1, c).value): c for c in range(1, 44)}
    for name in IDENTITY_COLS:
        for r in rows:
            assert a.cell(r, cols[name]).value == b.cell(r, cols[name]).value, \
                (r, name)
    for r in rows:
        assert b.cell(r, cols["ConfigFrozen"]).value == "NO", r
        assert b.cell(r, cols["WarmUp"]).value == \
            "NEEDS_RESEARCHER_CONFIRMATION", r
        assert b.cell(r, cols["ROI"]).value == \
            "NEEDS_RESEARCHER_CONFIRMATION", r


def test_formal_execution_not_started(workbooks):
    old, new = workbooks
    a, b = old[SAMPLE_SHEET], new[SAMPLE_SHEET]
    ca = {str(a.cell(1, c).value): c for c in range(1, 44)}
    rows = [r for r in range(2, b.max_row + 1) if b.cell(r, 1).value]
    assert len(rows) == 60
    for r in rows:
        assert a.cell(r, ca["ExecutionStatus"]).value == \
            b.cell(r, ca["ExecutionStatus"]).value, r
    for coord in ("F4", "F5", "F6"):
        assert old[PLAN_SHEET][coord].value == new[PLAN_SHEET][coord].value
        assert str(new[PLAN_SHEET][coord].value).startswith("NOT_STARTED"), \
            coord


def test_highlights_preserved(workbooks):
    old, new = workbooks
    for name in old.sheetnames:
        wa, wb = old[name], new[name]
        for row in wa.iter_rows():
            for cell in row:
                other = wb[cell.coordinate]
                fa, fb = cell.fill, other.fill
                assert fa.fill_type == fb.fill_type, (name, cell.coordinate)
                ra = fa.start_color.rgb if fa.start_color else None
                rb = fb.start_color.rgb if fb.start_color else None
                assert ra == rb, (name, cell.coordinate, ra, rb)


def test_only_sheet3_notes_differ(workbooks, derived):
    old, new = workbooks
    rollup, _ = derived
    for name in old.sheetnames:
        wa, wb = old[name], new[name]
        assert (wa.max_row, wa.max_column) == (wb.max_row, wb.max_column), name
        for row in range(1, wa.max_row + 1):
            for col in range(1, wa.max_column + 1):
                va, vb = wa.cell(row, col).value, wb.cell(row, col).value
                if name == MODEL_SHEET and col == NOTES_COL and row >= 2:
                    model = MODELS_3[row - 2]
                    suffix = f" | {_notes_segment(rollup[model])}"
                    assert isinstance(va, str) and vb == va + suffix, \
                        (row, va, vb)
                    # the v3.2.11 audit text is still intact
                    assert "v3.2.11 audit:" in vb or model == "RP01", model
                else:
                    assert va == vb, (name, row, col, va, vb)


def test_audit_sheet_matches_csv_byte_for_byte(built, workbooks):
    _, new = workbooks
    rows = _read_matrix(MATRIX)
    audit = new[AUDIT_SHEET]
    header = [audit.cell(1, c).value for c in range(1, 25)]
    assert header == rows[0]
    data = rows[1:]
    assert audit.max_row >= len(data) + 1 + 12
    for i, row in enumerate(data):
        got = [audit.cell(2 + i, c).value for c in range(1, 25)]
        assert got == list(row), (row[0], got)


def test_audit_sheet_rollup_matches_csv_derivation(workbooks, derived):
    _, new = workbooks
    rollup, data = derived
    audit = new[AUDIT_SHEET]
    header_row = len(data) + 4
    assert [audit.cell(header_row, c).value for c in range(1, 8)] == [
        "ModelID", "MatrixRows", "Groups", "Records", "CompleteRecords",
        "DerivedClosureStatus", "GroupFinalClassification"]
    for j, model in enumerate(MODELS_3):
        got = [audit.cell(header_row + 1 + j, c).value for c in range(1, 8)]
        want = [model] + [rollup[model][k] for k in
                          ("MatrixRows", "Groups", "Records", "CompleteRecords",
                           "DerivedClosureStatus",
                           "GroupFinalClassification")]
        assert got == want, (model, got, want)


def test_changelog_records_provenance_and_preconditions(workbooks, derived):
    _, new = workbooks
    rollup, _ = derived
    log = new[CHANGELOG_SHEET]
    assert [log.cell(3, c).value for c in range(1, 4)] == \
        ["Item", "Change", "Reason"]
    data = [row for row in log.iter_rows(min_row=4, values_only=True)
            if row and row[0]]
    assert len(data) >= 5
    text = " ".join(str(v) for row in log.iter_rows(values_only=True)
                    for v in row if v is not None)
    # provenance: the exact matrix sha this build consumed
    assert _sha256(MATRIX) in text
    # the regeneration precondition and the unchanged scope are recorded
    assert "regenerate" in text
    assert "ConfigFrozen=NO" in text
    assert "NOT_STARTED" in text
    assert "NEEDS_USER_DECISION" in text
    pending = [m for m in rollup
               if rollup[m]["DerivedClosureStatus"] == "PENDING_NO_ROW"]
    if pending:
        assert all(m in text for m in pending)


def test_deterministic_content(tmp_path_factory, built, workbooks):
    """Same inputs -> same cell content (only the zip container differs)."""
    _, first = workbooks
    out = tmp_path_factory.mktemp("v327b") / "workbook-v3.2.7.xlsx"
    cp = subprocess.run(
        [sys.executable, str(BUILDER), "--source", str(V326),
         "--closure-matrix", str(MATRIX), "--output", str(out)],
        capture_output=True, text=True)
    assert cp.returncode == 0, cp.stdout + cp.stderr
    second = _load(out)
    assert second.sheetnames == first.sheetnames
    for name in second.sheetnames:
        wa, wb = first[name], second[name]
        assert (wa.max_row, wa.max_column) == (wb.max_row, wb.max_column), name
        for row in wa.iter_rows():
            for cell in row:
                assert cell.value == wb[cell.coordinate].value, \
                    (name, cell.coordinate)
