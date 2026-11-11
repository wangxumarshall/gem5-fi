#!/usr/bin/env python3
"""Create the FROZEN MMU formal authority copies (researcher decision).

Researcher decision (2026-11-11, already approved):
  * all 40 SampleRunIDs in the authoritative workbook are FROZEN;
  * every Seed is the literal text `N/A_DETERMINISTIC`;
  * SeedPolicy=DETERMINISTIC, SeedSource=RESEARCHER_APPROVED,
    SampleFreezeStatus=FROZEN;
  * no numeric seed is generated, hashed, timestamped or coerced.

This tool reads the read-only design package under
  /home/sdc/mmu_phase1_work/design/MMU_Final_Design_Package/
and writes a frozen copy under
  <repo>/phase3/freeze/authority/
It never writes to the design package and never launches gem5.

Outputs
  gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx   (all sheets preserved)
  MMU_40_Sample_Matrix.csv                        (40 rows, same IDs/triples)
  MMU_Formal_Config.json                          (mirrors the workbook)
  MMU_Formal_Config.yaml                          (same content as JSON)
"""

import argparse
import csv
import json
import os
import shutil
import sys
from collections import Counter, OrderedDict

import openpyxl
import yaml

DESIGN_DIR = "/home/sdc/mmu_phase1_work/design/MMU_Final_Design_Package"
SOURCE_XLSX = os.path.join(
    DESIGN_DIR, "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")

FROZEN_XLSX_NAME = "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx"
FROZEN_CSV_NAME = "MMU_40_Sample_Matrix.csv"
FROZEN_JSON_NAME = "MMU_Formal_Config.json"
FROZEN_YAML_NAME = "MMU_Formal_Config.yaml"

SEED_LITERAL = "N/A_DETERMINISTIC"
SEED_POLICY = "DETERMINISTIC"
SEED_SOURCE = "RESEARCHER_APPROVED"
SAMPLE_ID_STATUS = "FROZEN"
SAMPLE_FREEZE_STATUS = "FROZEN"
FREEZE_DATE = "2026-11-11"

EXTRA_COLUMNS = ["SeedPolicy", "SeedSource", "SampleFreezeStatus"]
PENDING_BUILD = "PENDING_MAIN_BUILD"
MMU_SOURCE_FILES = [
    "CHAOS/gem5/src/arch/arm/mmu.cc",
    "CHAOS/gem5/src/arch/arm/table_walker.cc",
    "CHAOS/gem5/src/arch/arm/table_walker.hh",
    "CHAOS/gem5/src/arch/arm/tlb.cc",
]
WORKLOAD_IDS = ["W9", "W10", "W10S", "W11", "W12", "W13", "W14"]
WORKLOAD_VARIANTS = OrderedDict([
    ("M06/R02", "W10S-COLD-STORE"),
    ("M08/R05", "W10S-WARM-STORE"),
])
EXPECTED_MODELS = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"]
EXPECTED_CONTEXTS = ["R01", "R02", "R03", "R04", "R05"]


def _text(value):
    return "" if value is None else str(value).strip()


def _header_map(ws):
    headers = {}
    for col in range(1, ws.max_column + 1):
        value = _text(ws.cell(row=1, column=col).value)
        if value:
            headers[value] = col
    return headers


def _ensure_column(ws, headers, name):
    if name in headers:
        return headers[name]
    col = ws.max_column + 1
    ws.cell(row=1, column=col, value=name)
    headers[name] = col
    return col


def freeze_workbook(dest_xlsx):
    wb = openpyxl.load_workbook(SOURCE_XLSX)
    ws = wb["07_Sample_Matrix"]
    headers = _header_map(ws)
    required = ["SampleRunID", "ModelID", "WorkloadID", "ContextID", "Seed",
                "SampleIDStatus"]
    for name in required:
        if name not in headers:
            raise SystemExit("07_Sample_Matrix missing column %r" % name)
    seed_col = headers["Seed"]
    status_col = headers["SampleIDStatus"]
    extra_cols = {name: _ensure_column(ws, headers, name)
                  for name in EXTRA_COLUMNS}

    frozen_rows = 0
    for row in range(2, ws.max_row + 1):
        sample_id = _text(ws.cell(row=row, column=headers["SampleRunID"]).value)
        if not sample_id:
            continue
        seed_cell = ws.cell(row=row, column=seed_col)
        seed_cell.value = SEED_LITERAL
        seed_cell.number_format = "@"
        status_cell = ws.cell(row=row, column=status_col)
        status_cell.value = SAMPLE_ID_STATUS
        status_cell.number_format = "@"
        ws.cell(row=row, column=extra_cols["SeedPolicy"],
                value=SEED_POLICY).number_format = "@"
        ws.cell(row=row, column=extra_cols["SeedSource"],
                value=SEED_SOURCE).number_format = "@"
        ws.cell(row=row, column=extra_cols["SampleFreezeStatus"],
                value=SAMPLE_FREEZE_STATUS).number_format = "@"
        frozen_rows += 1
    if frozen_rows != 40:
        raise SystemExit("expected 40 sample rows, found %d" % frozen_rows)

    # Sheets that repeat the seed / sample-status decision are made
    # consistent with the frozen 07 sheet; the exact edits are recorded in
    # 16_Freeze_Record so no change is silent.
    consistency_edits = []
    readme = wb["00_Readme"]
    for row in range(1, readme.max_row + 1):
        key = _text(readme.cell(row=row, column=1).value)
        if key == "Seed":
            readme.cell(row=row, column=2,
                        value="%s; SeedPolicy=%s; no numeric seed"
                              % (SEED_LITERAL, SEED_POLICY))
            consistency_edits.append(
                "00_Readme!B%d: Seed -> %s" % (row, SEED_LITERAL))
        elif key == "SampleRunID":
            readme.cell(row=row, column=2,
                        value="%s (40/40, %s)" % (SAMPLE_ID_STATUS, FREEZE_DATE))
            consistency_edits.append(
                "00_Readme!B%d: SampleRunID -> %s"
                % (row, SAMPLE_ID_STATUS))

    trace = wb["09_Trace_Configuration"]
    for row in range(2, trace.max_row + 1):
        if _text(trace.cell(row=row, column=1).value) == "SampleRunID":
            trace.cell(row=row, column=4,
                       value="%s (40/40, %s)" % (SAMPLE_ID_STATUS, FREEZE_DATE))
            consistency_edits.append(
                "09_Trace_Configuration!D%d: SampleRunID status -> %s"
                % (row, SAMPLE_ID_STATUS))

    checklist = wb["11_Acceptance_Checklist"]
    for row in range(2, checklist.max_row + 1):
        check_id = _text(checklist.cell(row=row, column=1).value)
        if check_id == "A11":
            checklist.cell(
                row=row, column=4,
                value="40 frozen rows; execution status tracked separately")
            consistency_edits.append(
                "11_Acceptance_Checklist!D%d: A11 evidence -> 40 frozen rows"
                % row)
        elif check_id == "A12":
            checklist.cell(
                row=row, column=4,
                value="SeedPolicy=%s; Seed=%s; researcher-approved; no "
                      "numeric seed generated" % (SEED_POLICY, SEED_LITERAL))
            consistency_edits.append(
                "11_Acceptance_Checklist!D%d: A12 evidence -> deterministic "
                "seed policy" % row)

    blockers = wb["12_Blockers"]
    for row in range(2, blockers.max_row + 1):
        if _text(blockers.cell(row=row, column=1).value) == "B10":
            blockers.cell(
                row=row, column=5,
                value="Researcher decision %s: deterministic; Seed=%s; "
                      "SeedPolicy=%s" % (FREEZE_DATE, SEED_LITERAL, SEED_POLICY))
            blockers.cell(
                row=row, column=6,
                value="No action for the seed gate; remaining runtime gates "
                      "stay open")
            blockers.cell(row=row, column=7, value="RESOLVED")
            consistency_edits.append(
                "12_Blockers!B10: status -> RESOLVED (seed policy)")

    change_log = wb["13_Change_Log"]
    new_row = change_log.max_row + 1
    change_log.append([
        "v2.0-freeze",
        "Researcher froze all 40 SampleRunIDs; Seed=%s (text)" % SEED_LITERAL,
        "Formal-freeze decision %s" % FREEZE_DATE,
        "16_Freeze_Record; 07_Sample_Matrix SeedPolicy/SeedSource/"
        "SampleFreezeStatus",
    ])
    consistency_edits.append(
        "13_Change_Log!A%d:D%d: appended v2.0-freeze record"
        % (new_row, new_row))
    # Historical row 9 ("SampleRunIDs proposed; Seed blank/authoritative
    # placeholder") is retained as history; 16_Freeze_Record records that it
    # is superseded.

    if "16_Freeze_Record" in wb.sheetnames:
        del wb["16_Freeze_Record"]
    record = wb.create_sheet("16_Freeze_Record")
    record.append(["Item", "Value"])
    for item, value in [
        ("FreezeDate", FREEZE_DATE),
        ("Decision", "Researcher-approved deterministic freeze (no re-litigation)"),
        ("FrozenWorkbook", "phase3/freeze/authority/" + FROZEN_XLSX_NAME),
        ("SourceWorkbookReadOnly", SOURCE_XLSX),
        ("SampleCount", "40"),
        ("SampleIDStatus", SAMPLE_ID_STATUS),
        ("SampleFreezeStatus", SAMPLE_FREEZE_STATUS),
        ("Seed", SEED_LITERAL),
        ("SeedCellFormat", "text (@)"),
        ("SeedPolicy", SEED_POLICY),
        ("SeedSource", SEED_SOURCE),
        ("NumericSeed", "none (never generated, hashed, timestamped or coerced)"),
        ("Coverage", "8 models x 5 contexts (R01-R05), 40 unique SampleRunIDs"),
        ("ConsistencyEdits", "; ".join(consistency_edits)),
        ("SupersededHistory",
         "13_Change_Log v2.0 rows A8/A9 and 12_Blockers B10 retain their "
         "historical wording; this sheet records the superseding decision"),
    ]:
        record.append([item, value])

    os.makedirs(os.path.dirname(dest_xlsx), exist_ok=True)
    wb.save(dest_xlsx)
    return {
        "frozen_rows": frozen_rows,
        "consistency_edits": consistency_edits,
        "sheets": list(wb.sheetnames),
    }


def read_frozen_samples(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["07_Sample_Matrix"]
    rows = list(ws.iter_rows(values_only=True))
    headers = ["" if h is None else str(h) for h in rows[0]]
    samples = []
    for raw in rows[1:]:
        rec = OrderedDict(zip(headers, raw))
        if _text(rec.get("SampleRunID")):
            samples.append(rec)
    return headers, samples


def verify(xlsx_path):
    headers, samples = read_frozen_samples(xlsx_path)
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb["07_Sample_Matrix"]
    hmap = _header_map(ws)

    problems = []
    ids = [(_text(s.get("SampleRunID"))) for s in samples]
    if len(samples) != 40:
        problems.append("sample count %d != 40" % len(samples))
    if len(set(ids)) != 40:
        dup = [k for k, n in Counter(ids).items() if n > 1]
        problems.append("duplicate/empty SampleRunID: %r" % dup)
    triples = [(_text(s.get("ModelID")), _text(s.get("WorkloadID")),
                _text(s.get("ContextID"))) for s in samples]
    if len(set(triples)) != 40:
        problems.append("duplicate ModelID/WorkloadID/ContextID triples")
    seeds = [_text(s.get("Seed")) for s in samples]
    if set(seeds) != {SEED_LITERAL}:
        problems.append("seed values are %r" % sorted(set(seeds)))
    if any(_text(s.get("SampleIDStatus")) != SAMPLE_ID_STATUS
           for s in samples):
        problems.append("SampleIDStatus not %s for every row" % SAMPLE_ID_STATUS)
    for col in EXTRA_COLUMNS:
        expected = {"SeedPolicy": SEED_POLICY, "SeedSource": SEED_SOURCE,
                    "SampleFreezeStatus": SAMPLE_FREEZE_STATUS}[col]
        if any(_text(s.get(col)) != expected for s in samples):
            problems.append("%s not %s for every row" % (col, expected))
    models = Counter(_text(s.get("ModelID")) for s in samples)
    if sorted(models) != EXPECTED_MODELS or any(n != 5 for n in models.values()):
        problems.append("model coverage %r" % dict(models))
    contexts = Counter(_text(s.get("ContextID")) for s in samples)
    if sorted(contexts) != EXPECTED_CONTEXTS or any(
            n != 8 for n in contexts.values()):
        problems.append("context coverage %r" % dict(contexts))
    # Text-format proof for every Seed cell.
    seed_col = hmap["Seed"]
    bad_format = []
    for row in range(2, ws.max_row + 1):
        if not _text(ws.cell(row=row, column=hmap["SampleRunID"]).value):
            continue
        cell = ws.cell(row=row, column=seed_col)
        if cell.number_format != "@" or not isinstance(cell.value, str):
            bad_format.append(row)
    if bad_format:
        problems.append("Seed cells not text @: rows %r" % bad_format)
    return {
        "ok": not problems,
        "problems": problems,
        "samples": len(samples),
        "unique_sample_ids": len(set(ids)),
        "unique_seeds": sorted(set(seeds)),
        "models": dict(sorted(models.items())),
        "contexts": dict(sorted(contexts.items())),
        "columns": headers,
    }


def write_csv(xlsx_path, csv_path):
    headers, samples = read_frozen_samples(xlsx_path)
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for sample in samples:
            writer.writerow({k: ("" if sample.get(k) is None
                                 else sample.get(k)) for k in headers})
    return len(samples)


def build_config(xlsx_path, frozen_dir, source_xlsx):
    headers, samples = read_frozen_samples(xlsx_path)
    sample_rows = []
    for s in samples:
        sample_rows.append(OrderedDict(
            (k, ("" if s.get(k) is None else s.get(k))) for k in headers))
    models = sorted({_text(s.get("ModelID")) for s in samples})
    workloads = sorted({_text(s.get("WorkloadID")) for s in samples})
    model_workload = OrderedDict()
    for s in samples:
        model_workload.setdefault(_text(s.get("ModelID")),
                                  _text(s.get("WorkloadID")))
    return OrderedDict([
        ("schema_version", "3.0-frozen"),
        ("project", "ARM CPU-SDC MMU/TLB fault injection and propagation "
                    "feature library"),
        ("authority", OrderedDict([
            ("kind", "FROZEN_RESEARCHER_AUTHORITY"),
            ("freeze_date", FREEZE_DATE),
            ("source_workbook_read_only", source_xlsx),
            ("frozen_workbook", os.path.join(frozen_dir, FROZEN_XLSX_NAME)),
            ("frozen_csv", os.path.join(frozen_dir, FROZEN_CSV_NAME)),
        ])),
        ("seed_policy", SEED_POLICY),
        ("seed", SEED_LITERAL),
        ("seed_source", SEED_SOURCE),
        ("seed_used_by_gem5", False),
        ("seed_note", "Literal deterministic marker only; no numeric seed was "
                      "generated, hashed, timestamped or coerced. The runner "
                      "never passes a seed to gem5."),
        ("sample_id_status", SAMPLE_ID_STATUS),
        ("sample_freeze_status", SAMPLE_FREEZE_STATUS),
        ("counts", OrderedDict([
            ("models", len(models)),
            ("workloads", len(workloads)),
            ("contexts_per_model", 5),
            ("samples", len(sample_rows)),
        ])),
        ("models", models),
        ("workloads", workloads),
        ("contexts", EXPECTED_CONTEXTS),
        ("model_workload", model_workload),
        ("sample_columns", headers),
        ("samples", sample_rows),
        ("provenance_status", PENDING_BUILD),
        ("gem5_sha256", PENDING_BUILD),
        ("gem5_binary", "CHAOS/gem5/build/ARM/gem5.opt"),
        ("source_sha256", OrderedDict(
            (path, PENDING_BUILD) for path in MMU_SOURCE_FILES)),
        ("workload_sha256", OrderedDict(
            (wid, PENDING_BUILD) for wid in WORKLOAD_IDS)),
        ("workload_variant", WORKLOAD_VARIANTS),
        ("provenance_note",
         "PLACEHOLDER: fill gem5_sha256, source_sha256, workload_sha256 and "
         "workload_variant from the Main build; never fabricate a hash. "
         "The preflight emits BLOCKED_BINARY / BLOCKED_SOURCE when a "
         "sample_manifest.json hash disagrees with these values."),
    ])


def main(argv=None):
    global SOURCE_XLSX
    ap = argparse.ArgumentParser(
        description="Create frozen MMU authority copies (read-only source)")
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--source-xlsx", default=SOURCE_XLSX)
    ap.add_argument("--outdir", default=None,
                    help="default: <repo>/phase3/freeze/authority")
    args = ap.parse_args(argv)

    SOURCE_XLSX = os.path.abspath(args.source_xlsx)
    if not os.path.isfile(SOURCE_XLSX):
        print("FREEZE ERROR: source workbook not found: %s" % SOURCE_XLSX,
              file=sys.stderr)
        return 2
    outdir = args.outdir or os.path.join(
        os.path.abspath(args.repo_root), "phase3", "freeze", "authority")
    os.makedirs(outdir, exist_ok=True)
    xlsx_path = os.path.join(outdir, FROZEN_XLSX_NAME)
    csv_path = os.path.join(outdir, FROZEN_CSV_NAME)
    json_path = os.path.join(outdir, FROZEN_JSON_NAME)
    yaml_path = os.path.join(outdir, FROZEN_YAML_NAME)

    # The frozen copy is the only thing written; the design package stays
    # read-only.  Copy first so cell styles/defined names survive even if
    # openpyxl does not model every part of the workbook.
    shutil.copy2(SOURCE_XLSX, xlsx_path)
    frozen = freeze_workbook(xlsx_path)
    verify_result = verify(xlsx_path)
    if not verify_result["ok"]:
        print(json.dumps({"ok": False, "verify": verify_result,
                          "freeze": frozen}, indent=2, sort_keys=True))
        return 5
    csv_rows = write_csv(xlsx_path, csv_path)
    config = build_config(xlsx_path, outdir, SOURCE_XLSX)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(yaml_path, "w", encoding="utf-8") as fh:
        plain = json.loads(json.dumps(config))
        yaml.safe_dump(plain, fh, sort_keys=False, allow_unicode=True,
                       default_flow_style=False)
    result = {
        "ok": True,
        "freeze": frozen,
        "verify": verify_result,
        "csv_rows": csv_rows,
        "outputs": {
            "xlsx": xlsx_path,
            "csv": csv_path,
            "json": json_path,
            "yaml": yaml_path,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
