import csv
from pathlib import Path

import openpyxl

SRC = Path("docs/gem5-fi/lsu/implementation_v3_2/excel/"
           "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx")
DST = Path("docs/gem5-fi/lsu/implementation_v3_2/excel/"
           "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.2.xlsx")
CSV = Path("docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv")


def _md04_rows(ws):
    return [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, 5).value) == "MD04"]


def test_v322_only_md04_rows_changed_in_sample_sheet():
    src = openpyxl.load_workbook(SRC, data_only=True)["5.60个样本执行矩阵"]
    dst = openpyxl.load_workbook(DST, data_only=True)["5.60个样本执行矩阵"]
    md04 = set(_md04_rows(src))
    assert len(md04) == 5
    for r in range(2, src.max_row + 1):
        for c in range(1, src.max_column + 1):
            if src.cell(r, c).value == dst.cell(r, c).value:
                continue
            assert r in md04, (r, c, src.cell(r, c).value, dst.cell(r, c).value)
    # Identity columns never change.
    for r in range(2, src.max_row + 1):
        for c in (1, 2, 3, 4):
            assert src.cell(r, c).value == dst.cell(r, c).value


def test_v322_md04_config_rows_are_frozen():
    ws = openpyxl.load_workbook(DST, data_only=True)["5.60个样本执行矩阵"]
    for r in _md04_rows(ws):
        assert ws.cell(r, 6).value == "LSQ违规检测：LSQUnit::checkViolations"
        assert ws.cell(r, 7).value == "M5PanicFault return path"
        assert ws.cell(r, 9).value == "ALLOW_M5PANICFAULT_RETURN"
        assert ws.cell(r, 10).value == "SKIP_M5PANICFAULT_RETURN_ONCE"
        assert "StoreSize=8" in ws.cell(r, 15).value
        assert "MD04-DEF-v2" in ws.cell(r, 43).value


def test_v322_other_models_untouched_in_model_and_hook_sheets():
    a = openpyxl.load_workbook(SRC, data_only=True)
    b = openpyxl.load_workbook(DST, data_only=True)
    for sheet in ("3.最终12模型矩阵", "4.源码Hook审计"):
        wa, wb = a[sheet], b[sheet]
        for r in range(2, wa.max_row + 1):
            model = str(wa.cell(r, 1).value)
            for c in range(1, wa.max_column + 1):
                if wa.cell(r, c).value != wb.cell(r, c).value:
                    assert model == "MD04", (sheet, r, c, model)


def test_v322_has_freeze_sheet_and_60_row_csv():
    wb = openpyxl.load_workbook(DST, data_only=True)
    assert "14.MD04配置冻结" in wb.sheetnames
    text = "\n".join(str(c.value) for row in wb["14.MD04配置冻结"].iter_rows()
                     for c in row if c.value is not None)
    assert "FaultModelName" in text
    assert "Store-to-Load Violation Suppression" in text
    assert "旧定义" in text and "新定义" in text
    with CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) == 61          # header + 60 samples
    assert len(rows[0]) == 43
    assert sum(1 for r in rows[1:] if r[4] == "MD04") == 5
