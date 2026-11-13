#!/usr/bin/env python3
"""Build the v3.0.2 MMU parameter authority without touching v3.0.1.

The v3.0.1 authority has no M05 DecoyVA field and stores the M07 R04/R05
exact instruction VA only inside a symbolic TargetVA string.  This tool
creates a NEW versioned directory next to it.  It never writes into the
v3.0.1 directory.

New machine-readable fields per 07_Sample_Matrix row:
  TargetVAExact       exact instruction VA for M07 R01-R05 (blank elsewhere)
  M05DecoyVA          W13 decoy VA for M05 R01-R05 (blank elsewhere)
  M05DecoyTableBase   approved decoy table base (0) for M05 R01-R05
"""

import csv
import hashlib
import json
import os
import shutil
import sys

import openpyxl
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "phase3", "final",
                   "MMU_Final_Formal_Readiness_Package_v3.0.1")
DST = os.path.join(ROOT, "phase3", "final",
                   "MMU_Final_Formal_Readiness_Package_v3.0.2")
XLSX = "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx"
CSV = "MMU_40_Sample_Matrix.csv"

NEW_COLUMNS = ["TargetVAExact", "M05DecoyVA", "M05DecoyTableBase"]

M05_DECOY_VA = "0x4010200000"
M05_DECOY_TABLE_BASE = "0"
M07_EXACT = {
    "M07-F0-W14-S01-R01": "0x400d000000",
    "M07-F0-W14-S01-R02": "0x400d000000",
    "M07-F0-W14-S01-R03": "0x400d200000",
    "M07-F0-W14-S01-R04": "0x400d400100",
    "M07-F0-W14-S01-R05": "0x400d600180",
}
M05_IDS = ["M05-F0-W13-S01-R%02d" % i for i in range(1, 6)]
M07_IDS = ["M07-F0-W14-S01-R%02d" % i for i in range(1, 6)]

EVIDENCE = [
    ("W13 source", "workloads/mmu/W13/mmu_w13.c"),
    ("W13 binary", "workloads/mmu/W13/mmu_w13"),
    ("W14 source", "workloads/mmu/W14/mmu_w14.c"),
    ("W14 binary", "workloads/mmu/W14/mmu_w14"),
] + [("pilot %s" % sid.split("-S01-")[1],
      "runs/TEST-F1-%s-%s/sample_manifest.json" %
      (sid.split("-")[0], sid.split("-")[-1]))
     for sid in M05_IDS + M07_IDS]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cell_values(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for ws in wb.worksheets:
        out[ws.title] = [[c for c in row]
                         for row in ws.iter_rows(values_only=True)]
    return out


def build_excel():
    src_path = os.path.join(SRC, XLSX)
    dst_path = os.path.join(DST, XLSX)
    wb = openpyxl.load_workbook(src_path)
    ws = wb["07_Sample_Matrix"]
    headers = [c.value for c in ws[1]]
    for name in NEW_COLUMNS:
        if name in headers:
            raise SystemExit("column already exists: %s" % name)
    start = len(headers) + 1
    for off, name in enumerate(NEW_COLUMNS):
        ws.cell(row=1, column=start + off, value=name)
    idx = {name: start + off for off, name in enumerate(NEW_COLUMNS)}
    sid_col = headers.index("SampleRunID") + 1
    for row in range(2, ws.max_row + 1):
        sid = ws.cell(row=row, column=sid_col).value
        if not sid:
            continue
        if sid in M07_EXACT:
            ws.cell(row=row, column=idx["TargetVAExact"],
                    value=M07_EXACT[sid])
        if sid in M05_IDS:
            ws.cell(row=row, column=idx["M05DecoyVA"], value=M05_DECOY_VA)
            ws.cell(row=row, column=idx["M05DecoyTableBase"],
                    value=M05_DECOY_TABLE_BASE)

    auth = wb.create_sheet("18_Parameter_Authority_v3.0.2")
    auth.append(["Field", "Scope", "SampleRunID", "Value",
                 "AuthoritySource", "EvidenceSHA256"])
    for sid in M05_IDS:
        auth.append(["M05DecoyVA", "M05", sid, M05_DECOY_VA,
                     "W13_DECOY_VA + TEST-F1-%s-%s pilot" %
                     ("M05", sid.split("-")[-1]),
                     sha256(os.path.join(
                         ROOT, "runs", "TEST-F1-M05-%s" %
                         sid.split("-")[-1], "sample_manifest.json"))])
        auth.append(["M05DecoyTableBase", "M05", sid,
                     M05_DECOY_TABLE_BASE,
                     "TEST-F1-%s-%s pilot explicit" %
                     ("M05", sid.split("-")[-1]),
                     sha256(os.path.join(
                         ROOT, "runs", "TEST-F1-M05-%s" %
                         sid.split("-")[-1], "sample_manifest.json"))])
    for sid in M07_IDS:
        auth.append(["TargetVAExact", "M07", sid, M07_EXACT[sid],
                     "TEST-F1-M07-%s pilot + W14 macro" %
                     sid.split("-")[-1],
                     sha256(os.path.join(
                         ROOT, "runs", "TEST-F1-M07-%s" %
                         sid.split("-")[-1], "sample_manifest.json"))])
    auth.append([])
    auth.append(["Note", "", "", "",
                 "v3.0.1 is preserved unchanged; this sheet is the v3.0.2 "
                 "addendum. The older closure pilot TEST-M07-R05 used "
                 "0x400d600100 and is superseded by the final F1 pilot "
                 "0x400d600180 and W14 R05_CODE_OFF=0x180.", ""])
    for col, width in zip("ABCDEF", (24, 10, 30, 18, 70, 70)):
        auth.column_dimensions[col].width = width
    wb.save(dst_path)
    return dst_path


def build_csv():
    src_path = os.path.join(SRC, CSV)
    dst_path = os.path.join(DST, CSV)
    with open(src_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys()) if rows else []
    fields = fields + NEW_COLUMNS
    for row in rows:
        sid = row.get("SampleRunID", "")
        row["TargetVAExact"] = M07_EXACT.get(sid, "")
        if sid in M05_IDS:
            row["M05DecoyVA"] = M05_DECOY_VA
            row["M05DecoyTableBase"] = M05_DECOY_TABLE_BASE
        else:
            row["M05DecoyVA"] = ""
            row["M05DecoyTableBase"] = ""
    with open(dst_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return dst_path


def build_json():
    out = {
        "authority_version": "3.0.2",
        "supersedes": "3.0.1",
        "created_utc": "2026-11-13T00:00:00Z",
        "kind": "PARAMETER_PARITY_ADDENDUM",
        "scope": "M05 decoy VA/table base; M07 exact target VA parity",
        "source_v3_0_1": {
            "dir": SRC,
            "xlsx_sha256": sha256(os.path.join(SRC, XLSX)),
            "csv_sha256": sha256(os.path.join(SRC, CSV)),
        },
        "provenance": {},
        "samples": {},
    }
    for label, rel in EVIDENCE:
        full = os.path.join(ROOT, rel)
        out["provenance"][label] = {
            "path": full, "sha256": sha256(full)}
    out["provenance"]["W13_DECOY_VA"] = {
        "source": os.path.join(ROOT, "workloads/mmu/W13/mmu_w13.c"),
        "symbol": "W13_DECOY_VA", "value": M05_DECOY_VA,
    }
    out["provenance"]["W14_exact_VA"] = {
        "source": os.path.join(ROOT, "workloads/mmu/W14/mmu_w14.c"),
        "symbols": {
            "W14_XN_VA": "0x400d400000", "CODE_OFF": "0x100",
            "W14_NONE_CODE_VA": "0x400d600000",
            "R05_CODE_OFF": "0x180",
        },
    }
    out["provenance"]["supersession_note"] = (
        "The older closure pilot TEST-M07-R05 used 0x400d600100; the final "
        "F1 pilot TEST-F1-M07-R05 uses 0x400d600180, matching "
        "W14_NONE_CODE_VA + R05_CODE_OFF (0x180).")
    for sid in M05_IDS:
        ctx = sid.split("-")[-1]
        man = os.path.join(ROOT, "runs", "TEST-F1-M05-%s" % ctx,
                           "sample_manifest.json")
        out["samples"][sid] = {
            "ModelID": "M05", "ContextID": ctx,
            "M05DecoyVA": M05_DECOY_VA,
            "M05DecoyTableBase": M05_DECOY_TABLE_BASE,
            "pilot_manifest": man,
            "pilot_manifest_sha256": sha256(man),
            "pilot_decoy_va": M05_DECOY_VA,
            "pilot_decoy_table_base": M05_DECOY_TABLE_BASE,
        }
    for sid in M07_IDS:
        ctx = sid.split("-")[-1]
        man = os.path.join(ROOT, "runs", "TEST-F1-M07-%s" % ctx,
                           "sample_manifest.json")
        pilot = json.load(open(man, "r", encoding="utf-8"))
        cmd = pilot.get("command") or []
        val = (cmd[cmd.index("--mmu_target_va") + 1]
               if "--mmu_target_va" in cmd else "")
        out["samples"][sid] = {
            "ModelID": "M07", "ContextID": ctx,
            "TargetVAExact": M07_EXACT[sid],
            "pilot_manifest": man,
            "pilot_manifest_sha256": sha256(man),
            "pilot_target_va": val,
            "pilot_target_mode": pilot.get("target_mode", ""),
            "pilot_target_n": (
                cmd[cmd.index("--mmu_target_n") + 1]
                if "--mmu_target_n" in cmd else ""),
        }
    path = os.path.join(DST, "MMU_Parameter_Authority_v3.0.2.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def write_docs():
    changelog = os.path.join(DST, "MMU_Change_Log_v3.0.2.md")
    with open(changelog, "w", encoding="utf-8") as fh:
        fh.write("""# MMU authority change log v3.0.2

Supersedes v3.0.1 (preserved unchanged in the sibling directory).

## Added

- `07_Sample_Matrix.TargetVAExact`: exact instruction VA for M07 R01-R05
  (M07 R04 `0x400d400100`, R05 `0x400d600180`).
- `07_Sample_Matrix.M05DecoyVA`: `0x4010200000` for M05 R01-R05.
- `07_Sample_Matrix.M05DecoyTableBase`: `0` for M05 R01-R05.
- `18_Parameter_Authority_v3.0.2`: per-value source and pilot SHA256.
- `MMU_Parameter_Authority_v3.0.2.json`: machine-readable parity authority
  with W13/W14 source and final F1 pilot provenance.

## Unchanged

All original 40 SampleRunIDs, model/workload/context triples, Seeds
(`N/A_DETERMINISTIC`), controls, pilots, binaries and fault semantics.

## Evidence

- `workloads/mmu/W13/mmu_w13.c` `W13_DECOY_VA 0x4010200000`.
- `workloads/mmu/W14/mmu_w14.c` `CODE_OFF 0x100`, `R05_CODE_OFF 0x180`.
- Final F1 pilots M05 R01-R05 and M07 R01-R05 (SHA256 in the JSON and sheet).
- The older closure pilot TEST-M07-R05 (`0x400d600100`) is superseded by the
  final F1 pilot (`0x400d600180`).
""")
    readme = os.path.join(DST, "README_v3.0.2.md")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write("""# MMU Final authority v3.0.2

This directory is additive. The v3.0.1 directory is not modified.

Files:

- `gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx` — v3.0.1 workbook plus the
  three parity columns and `18_Parameter_Authority_v3.0.2`.
- `MMU_40_Sample_Matrix.csv` — v3.0.1 matrix plus the same three columns.
- `MMU_Parameter_Authority_v3.0.2.json` — machine-readable parity authority.
- `pilot_evidence/` — copies of the seven final F1 pilot manifests used as
  evidence, with `SHA256SUMS.txt`.
- `MMU_Change_Log_v3.0.2.md`.
""")
    return changelog, readme


def copy_evidence():
    ev = os.path.join(DST, "pilot_evidence")
    os.makedirs(ev, exist_ok=True)
    lines = []
    for sid in M05_IDS + M07_IDS:
        model = sid.split("-")[0]
        ctx = sid.split("-")[-1]
        src = os.path.join(ROOT, "runs", "TEST-F1-%s-%s" % (model, ctx),
                           "sample_manifest.json")
        dst = os.path.join(ev, "%s.json" % sid)
        shutil.copy2(src, dst)
        lines.append("%s  %s" % (sha256(dst), os.path.basename(dst)))
    with open(os.path.join(ev, "SHA256SUMS.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return ev


def main():
    if not os.path.isfile(os.path.join(SRC, XLSX)):
        raise SystemExit("v3.0.1 authority missing: %s" % SRC)
    os.makedirs(DST, exist_ok=True)
    before = {p: sha256(os.path.join(SRC, p)) for p in (XLSX, CSV)}
    build_excel()
    build_csv()
    build_json()
    write_docs()
    copy_evidence()
    after = {p: sha256(os.path.join(SRC, p)) for p in (XLSX, CSV)}
    if before != after:
        raise SystemExit("v3.0.1 was modified: %s -> %s" % (before, after))

    # Prove every original cell survived the Excel round-trip.
    a = cell_values(os.path.join(SRC, XLSX))
    b = cell_values(os.path.join(DST, XLSX))
    for sheet, rows in a.items():
        if sheet not in b:
            raise SystemExit("sheet lost: %s" % sheet)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                # New columns exist only on 07_Sample_Matrix (appended after
                # the original 34). Every original cell must survive.
                if sheet == "07_Sample_Matrix" and c >= 34:
                    continue
                if b[sheet][r][c] != val:
                    raise SystemExit(
                        "cell drift %s!%s: %r -> %r" %
                        (sheet, get_column_letter(c + 1) + str(r + 1),
                         val, b[sheet][r][c]))
    print("v3.0.2 authority built: %s" % DST)
    for name in sorted(os.listdir(DST)):
        path = os.path.join(DST, name)
        if os.path.isfile(path):
            print("  %s  %s" % (sha256(path), name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
