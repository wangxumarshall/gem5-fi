import csv
import hashlib
import json
from pathlib import Path

import openpyxl

ROOT = Path("docs/gem5-fi/lsu/implementation_v3_2")
XL = ROOT / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.3.xlsx"
# v3.2.10 supersedes v3.2.4 (v3.2.5 book): the CSV must mirror the newest authoritative book.
XL_LATEST = ROOT / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx"
if XL_LATEST.is_file():
    XL = XL_LATEST
ARCH_BIN = ROOT / "FW05_Workload_Archive/bin/fw05_forward"
FW05_SHA = "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_fw05_excel_archive_manifest_agree():
    ws = openpyxl.load_workbook(XL, data_only=True)["5.60个样本执行矩阵"]
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[4] == "FW05"]
    assert len(rows) == 5
    assert _sha(ARCH_BIN) == FW05_SHA
    for r in rows:
        assert "fw05_forward" in r[18]
        assert r[19] == FW05_SHA
        assert r[21] == "67afad307642983e"
        sid = r[0]
        d = ROOT / "pilots_v3_2_7" / sid.replace("FW05-F6-W8-S01-", "FW05-")
        assert d.is_dir(), d
        m = json.loads((d / "manifest.json").read_text())
        assert m["workload"]["sha256"] == FW05_SHA
        assert m["seed"] == r[3]


def test_sq03_seeds_and_manifest_agree():
    ws = openpyxl.load_workbook(XL, data_only=True)["5.60个样本执行矩阵"]
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[4] == "SQ03"]
    assert len(rows) == 5
    for r in rows:
        sid = r[0]
        d = ROOT / "pilots_v3_2_8" / sid.replace("SQ03-F0-W3-S02-", "SQ03-")
        m = json.loads((d / "pilot_meta.json").read_text())
        assert m["seed"] == r[3]
        assert m["excel_identity"]["event_ordinal_used"] == r[15]
        assert m["accepted"] is True
        c = m["trace"]["completeness"]
        assert c["trace_completeness"] == "COMPLETE"
        ev = m["injection"]["events"]
        assert len(ev) == 1
        assert ev[0]["canwb_before"] == 0 and ev[0]["canwb_after"] == 1
        assert ev[0]["stores_to_wb_after"] - ev[0]["stores_to_wb_before"] == 1


def test_config_frozen_stays_no_for_all_60():
    ws = openpyxl.load_workbook(XL, data_only=True)["5.60个样本执行矩阵"]
    for r in range(2, 62):
        assert ws.cell(r, 38).value == "NO"


def test_csv_mirrors_sheet5():
    ws = openpyxl.load_workbook(XL, data_only=True)["5.60个样本执行矩阵"]
    rows = list(csv.reader((ROOT / "excel/60_SAMPLE_MATRIX.csv").open(encoding="utf-8")))
    assert len(rows) == 61 and len(rows[0]) == 43
    for r, row in enumerate(rows[1:], start=2):
        for c, value in enumerate(row, start=1):
            v = ws.cell(r, c).value
            assert ("" if v is None else str(v)) == value, (r, c)
