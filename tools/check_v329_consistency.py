#!/usr/bin/env python3
"""v3.2.9 cross-artifact consistency: Excel v3.2.4 / CSV / manifests / archive."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
XL = IMPL / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx"
CSV = IMPL / "excel/60_SAMPLE_MATRIX.csv"
ARCH = IMPL / "FW05_Workload_Archive/bin/fw05_forward"
SHA = "0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf"
PILOTS = IMPL / "pilots_v3_2_9"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    errors = []
    wb = openpyxl.load_workbook(XL, data_only=True)
    ws = wb["5.60个样本执行矩阵"]
    cols = {str(c.value).strip(): c.column for c in ws[1] if c.value}
    rows = {}
    for r in range(2, ws.max_row + 1):
        sid = ws.cell(r, cols["SampleRunID"]).value
        if sid:
            rows[sid] = {name: ws.cell(r, c).value for name, c in cols.items()}

    if sha(ARCH) != SHA:
        errors.append("archive binary SHA mismatch")
    for sid, row in rows.items():
        if row["ConfigFrozen"] != "NO":
            errors.append(f"{sid}: ConfigFrozen={row['ConfigFrozen']}")
        if row["FaultModelID"] == "FW05":
            if not str(row["WorkloadPath"]).endswith("FW05_Workload_Archive/bin/fw05_forward"):
                errors.append(f"{sid}: FW05 path {row['WorkloadPath']}")
            if row["BinarySHA256"] != SHA:
                errors.append(f"{sid}: FW05 SHA")
            if str(row["Oracle"]).lower() != "67afad307642983e":
                errors.append(f"{sid}: FW05 oracle")

    # CSV mirrors sheet 5 exactly.
    with CSV.open() as fh:
        csv_rows = list(csv.reader(fh))
    sheet_rows = [[("" if c.value is None else str(c.value)) for c in r]
                  for r in ws.iter_rows(min_row=1, max_row=ws.max_row)]
    if [[str(v) for v in r] for r in csv_rows] != sheet_rows:
        errors.append("60_SAMPLE_MATRIX.csv does not mirror sheet 5")

    # Pilot identities match the Excel rows.
    for i in range(1, 6):
        for model in ("SP05", "SQ03"):
            d = PILOTS / f"{model}-R0{i}" if model == "SP05" else IMPL / f"pilots_v3_2_8/SQ03-R0{i}"
            meta_path = d / "pilot_meta.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text())
            sid = meta["excel_identity"]["sample_run_id"]
            if sid not in rows:
                errors.append(f"{model}-R0{i}: sample id {sid} absent")
            elif int(rows[sid]["Seed"]) != int(meta["seed"]):
                errors.append(f"{model}-R0{i}: seed mismatch")

    for e in errors:
        print("FAIL:", e)
    print(f"rows={len(rows)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
