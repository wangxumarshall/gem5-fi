import csv
from pathlib import Path

import openpyxl

SRC = Path("docs/gem5-fi/lsu/implementation_v3_2/excel/"
           "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx")
DST = Path("docs/gem5-fi/lsu/implementation_v3_2/excel/"
           "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx")
CSV = Path("docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv")
SHA = "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"


def _fw05_rows(ws):
    return [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, 5).value) == "FW05"]


def test_only_fw05_rows_changed_in_sample_sheet():
    a = openpyxl.load_workbook(SRC, data_only=True)["5.60个样本执行矩阵"]
    b = openpyxl.load_workbook(DST, data_only=True)["5.60个样本执行矩阵"]
    fw = set(_fw05_rows(a))
    assert len(fw) == 5
    for r in range(2, a.max_row + 1):
        for c in range(1, a.max_column + 1):
            if a.cell(r, c).value != b.cell(r, c).value:
                assert r in fw, (r, c, a.cell(r, c).value, b.cell(r, c).value)
    for r in range(2, a.max_row + 1):
        for c in (1, 2, 3, 4):
            assert a.cell(r, c).value == b.cell(r, c).value


def test_fw05_rows_are_frozen_on_fw05_forward():
    ws = openpyxl.load_workbook(DST, data_only=True)["5.60个样本执行矩阵"]
    terminals = ["SQUASHED", "SDC", "SDC", "SDC", "SDC"]
    for i, r in enumerate(_fw05_rows(ws)):
        assert "fw05_forward" in ws.cell(r, 19).value
        assert ws.cell(r, 20).value == SHA
        assert ws.cell(r, 22).value == "67afad307642983e"
        assert ws.cell(r, 33).value == "PILOT_RUN_ACCEPTED"
        assert ws.cell(r, 38).value == "NO"
        assert ws.cell(r, 39).value == "PILOT_RUN"
        assert ws.cell(r, 40).value == "TRIGGERED"
        assert ws.cell(r, 41).value == terminals[i]
        assert ws.cell(r, 42).value == "COMPLETE"
        assert ws.cell(r, 37).value == "FROZEN_FW05_WORKLOAD"
        assert "fw05_forward" in ws.cell(r, 43).value


def test_other_models_untouched_in_model_and_hook_sheets():
    a = openpyxl.load_workbook(SRC, data_only=True)
    b = openpyxl.load_workbook(DST, data_only=True)
    for sheet in ("3.最终12模型矩阵", "4.源码Hook审计"):
        wa, wb = a[sheet], b[sheet]
        for r in range(2, wa.max_row + 1):
            model = str(wa.cell(r, 1).value)
            for c in range(1, wa.max_column + 1):
                if wa.cell(r, c).value != wb.cell(r, c).value:
                    assert model == "FW05", (sheet, r, c, model)


def test_v323_has_fw05_freeze_sheet_and_csv():
    wb = openpyxl.load_workbook(DST, data_only=True)
    assert "15.FW05配置冻结" in wb.sheetnames
    text = "\n".join(str(c.value) for row in wb["15.FW05配置冻结"].iter_rows()
                     for c in row if c.value is not None)
    assert "fw05_forward" in text
    assert "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf" in text
    assert "alignment" in text
    with CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) == 61 and len(rows[0]) == 43
    assert sum(1 for r in rows[1:] if r[4] == "FW05") == 5
