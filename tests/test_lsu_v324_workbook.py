"""v3.2.4 workbook: only FW05/SQ03/SP05 rows may change; identities stay."""
import openpyxl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
V323 = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx"
V324 = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx"
SHEET = "5.60个样本执行矩阵"
ARCHIVE = "FW05_Workload_Archive/bin/fw05_forward"
SHA = "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"
ORACLE = "67afad307642983e"


def _headers(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _rows(ws, cols, model):
    return [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, cols["FaultModelID"]).value) == model]


def test_fw05_rows_point_at_archive():
    ws = openpyxl.load_workbook(V324, data_only=True)[SHEET]
    cols = _headers(ws)
    rows = _rows(ws, cols, "FW05")
    assert len(rows) == 5
    for r in rows:
        assert str(ws.cell(r, cols["WorkloadPath"]).value).endswith(ARCHIVE)
        assert ws.cell(r, cols["BinarySHA256"]).value == SHA
        assert ws.cell(r, cols["Oracle"]).value == ORACLE


def test_sq03_and_sp05_status_are_pilot_runs():
    ws = openpyxl.load_workbook(V324, data_only=True)[SHEET]
    cols = _headers(ws)
    for model in ("SQ03", "SP05"):
        rows = _rows(ws, cols, model)
        assert len(rows) == 5, model
        for r in rows:
            assert ws.cell(r, cols["ExecutionStatus"]).value == "PILOT_RUN_ACCEPTED"
            assert ws.cell(r, cols["RunStatus"]).value == "PILOT_RUN"
            assert ws.cell(r, cols["TerminalState_v31"]).value in (
                "MASKED", "SDC", "SQUASHED", "CRASH", "HANG", "UNRESOLVED")


def test_identities_and_config_frozen_unchanged():
    a = openpyxl.load_workbook(V323, data_only=True)[SHEET]
    b = openpyxl.load_workbook(V324, data_only=True)[SHEET]
    ca, cb = _headers(a), _headers(b)
    id_cols = ["SampleRunID", "RunID", "SubTaskID", "Seed", "FaultModelID"]
    for r in range(2, b.max_row + 1):
        if not b.cell(r, cb["SampleRunID"]).value:
            continue
        for name in id_cols:
            assert a.cell(r, ca[name]).value == b.cell(r, cb[name]).value, (r, name)
        assert b.cell(r, cb["ConfigFrozen"]).value == "NO"


def test_only_allowed_rows_changed():
    a = openpyxl.load_workbook(V323, data_only=True)[SHEET]
    b = openpyxl.load_workbook(V324, data_only=True)[SHEET]
    ca, cb = _headers(a), _headers(b)
    changed_models = set()
    for r in range(2, b.max_row + 1):
        for name in ca:
            if name not in cb:
                continue
            if a.cell(r, ca[name]).value != b.cell(r, cb[name]).value:
                changed_models.add(str(b.cell(r, cb["FaultModelID"]).value))
    assert changed_models <= {"FW05", "SQ03", "SP05"}, changed_models


def test_revision_sheet_exists():
    wb = openpyxl.load_workbook(V324, data_only=True)
    assert "17.v3.2.9变更记录" in wb.sheetnames
