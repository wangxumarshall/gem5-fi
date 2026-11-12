#!/usr/bin/env python3
"""Apply the 2026-11-12 final-authority corrections (evidence-driven).

The frozen authority was copied from the read-only design workbook.  Two rows
carried metadata that no longer matched the realized workloads:

  * M07-F0-W14-S01-R04: the realized context is EL0 execute from a
    PROT_READ/XN JIT page (W14 phase exec_xn, marker 0xc7).  The workbook still
    described the obsolete "read-only store" realization.
  * M02-F0-W10-S01-R0{1..5}: the OracleMethod text still named the obsolete
    baseline PFN 0x83480->0x83481.  The final control evidence
    (runs/TEST-F1-CTRL-W10-R0*) records target PFN 0x834b2 -> 0x834b3
    (XOR-1 neighbour).  The faulted trace
    (runs/TEST-F1-M02-R02 .../prop_evt.txt.gz, refill_pfn_corrupt event 4424)
    records old_pfn=0x834b2 -> new_pfn=0x834b3.

The correction is applied to the workbook, the CSV, the JSON and the YAML so
the four artifacts cannot drift.  SampleRunIDs, ModelIDs, contexts, counts,
Seeds and SeedPolicy are never changed.

Usage:
  tools/mmu_apply_authority_corrections.py [--check]
"""

import argparse
import csv
import json
import os
import sys

import openpyxl
import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH = os.path.join(REPO, "phase3", "freeze", "authority")
XLSX = os.path.join(AUTH, "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")
CSV_PATH = os.path.join(AUTH, "MMU_40_Sample_Matrix.csv")
JSON_PATH = os.path.join(AUTH, "MMU_Formal_Config.json")
YAML_PATH = os.path.join(AUTH, "MMU_Formal_Config.yaml")

M07_R04 = "M07-F0-W14-S01-R04"
M07_R05 = "M07-F0-W14-S01-R05"
W10_PREFIX = "M02-F0-W10-S01-R0"

R04_FIELDS = {
    "TargetVA": "XN code VA 0x400d400100",
    "TargetEvent": ("target EL0 instruction-execute permission decision with "
                    "normal grant=false (UXN=1 on a valid leaf)"),
    "TargetInstruction": ("EL0 execute from a read-only (PROT_READ) JIT code "
                          "page with UXN=1 (distinct VA/code blob/marker "
                          "0xc7 from R05)"),
    "OracleMethod": ("W14: no-fault XN execute faults with SEGV_ACCERR on a "
                     "valid UXN=1 leaf; injected execute fetches/executes "
                     "the R04 JIT blob and returns marker 0xc7; trace "
                     "pte_decode L3 Page must show UXN=1 and "
                     "translation_result/lsu_request(mode=Execute) at "
                     "0x400d400100."),
    "ExpectedPropagationPath": ("Translation -> permission grant false "
                                "(UXN=1) -> invert true -> no Permission "
                                "Fault -> IFU fetch request at target VA -> "
                                "instruction fetch/execute -> guest marker "
                                "0xc7 -> oracle."),
}

M05_FIELDS = {
    "ExpectedPropagationPath": ("Valid XN leaf (UXN=1) -> EL0 indirect "
                                "branch (br xN, target from runtime table) -> "
                                "permission grant false -> invert true -> no "
                                "Permission Fault -> IFU fetch request at "
                                "target VA -> execute R05 blob -> guest "
                                "marker 0x5a -> oracle."),
}

W10_ORACLE = ("W10: target sentinel vs neighbor sentinel (final control: "
              "0x63 vs 0x60); prove te.pfn 0x834b2->0x834b3 and later lookup "
              "consumed it.")


def sample_corrections(sample_id):
    if sample_id == M07_R04:
        return dict(R04_FIELDS)
    if sample_id == M07_R05:
        return dict(M05_FIELDS)
    if sample_id.startswith(W10_PREFIX):
        return {"OracleMethod": W10_ORACLE}
    return {}


def _text(v):
    return "" if v is None else str(v).strip()


def _header_map(ws):
    return {_text(ws.cell(row=1, column=c).value): c
            for c in range(1, ws.max_column + 1)
            if _text(ws.cell(row=1, column=c).value)}


def correct_workbook(check):
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["07_Sample_Matrix"]
    hmap = _header_map(ws)
    changed = []
    for row in range(2, ws.max_row + 1):
        sid = _text(ws.cell(row=row, column=hmap["SampleRunID"]).value)
        for col, value in sample_corrections(sid).items():
            cell = ws.cell(row=row, column=hmap[col])
            if _text(cell.value) != value:
                changed.append((sid, col, _text(cell.value), value))
                if not check:
                    cell.value = value
                    cell.number_format = "@"

    # Record the R04 metadata correction on 17_M07_Context_Change_Record.
    ws17 = wb["17_M07_Context_Change_Record"]
    existing = {
        (_text(r[0]), _text(r[1]))
        for r in ws17.iter_rows(min_row=2, values_only=True) if r
    }
    record_rows = []
    for col, after in R04_FIELDS.items():
        if (M07_R04, col) in existing:
            continue
        before = {
            "TargetVA": "XN code VA",
            "TargetEvent": "target permission decision with normal grant=false",
            "TargetInstruction": ("EL0 store through read-only alias "
                                  "(primary); additional read/atomic/execute "
                                  "contexts."),
            "OracleMethod": ("W14: baseline RO store faults; injected store "
                             "succeeds and writable alias observes the "
                             "changed value."),
            "ExpectedPropagationPath": ("Translation -> permission grant "
                                        "false -> invert true -> no "
                                        "Permission Fault -> physical "
                                        "request -> memory update/fetch -> "
                                        "alias/consumer -> commit/oracle."),
        }[col]
        record_rows.append((
            M07_R04, col, before, after,
            "Align TargetInstruction/OracleMethod/TargetEvent/TargetVA/path "
            "with the frozen R04 DynamicContext 'EL0 execute from XN "
            "mapping' and the realized W14 exec_xn workload (marker 0xc7). "
            "No SampleRunID, ModelID, context, count or Seed changed.",
            "Researcher-frozen 07_Sample_Matrix DynamicContext for R04; this "
            "correction removes the obsolete store wording.",
            "W14 mmu_w14 (marker R04=0xc7, distinct from R05=0x5a)",
            "runs/TEST-F1-CTRL-W14-R04/Run_Log/golden_output.txt",
            "runs/TEST-F1-M07-R04/Trace/prop_evt.txt.gz",
            "READY after v2 closure: permission_eval(Execute,deny) -> "
            "activation inversion -> translation_result + "
            "lsu_request(mode=Execute) at 0x400d400100; guest marker 0xc7",
        ))
    if record_rows and not check:
        for rec in record_rows:
            ws17.append(rec)

    # Record the correction in 13_Change_Log.
    ws13 = wb["13_Change_Log"]
    log_rows = []
    known = {_text(r[1]) for r in ws13.iter_rows(min_row=2, values_only=True)
             if r and len(r) > 1}
    m07_change = ("M07-F0-W14-S01-R04 context metadata corrected: "
                  "TargetVA/TargetEvent/TargetInstruction/OracleMethod/"
                  "ExpectedPropagationPath")
    m02_change = ("M02-F0-W10-S01-R01..R05 OracleMethod PFN corrected to the "
                  "final-control value 0x834b2->0x834b3")
    if m07_change not in known:
        log_rows.append((("v2.3-M07"), m07_change,
                         "The workbook still described the obsolete "
                         "read-only-store realization; the frozen R04 "
                         "DynamicContext is EL0 execute from XN (marker 0xc7).",
                         "07_Sample_Matrix DynamicContext; W14 exec_xn; "
                         "TEST-F1-M07-R04 trace"))
    if m02_change not in known:
        log_rows.append((("v2.3-M02"), m02_change,
                         "te.pfn is per-run; the final scoped control reads "
                         "0x834b2->0x834b3. 0x83480/0x834b6 predate the "
                         "final EPAN checkpoint and are superseded.",
                         "runs/TEST-F1-CTRL-W10-R02 golden; "
                         "TEST-F1-M02-R02 refill_pfn_corrupt event 4424"))
    if log_rows and not check:
        for rec in log_rows:
            ws13.append(rec)

    if changed and not check:
        wb.save(XLSX)
    return {
        "workbook_cells_changed": changed,
        "sheet17_rows_added": len(record_rows),
        "change_log_rows_added": len(log_rows),
    }


def correct_csv(check):
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    headers = list(rows[0].keys()) if rows else []
    changed = []
    for row in rows:
        for col, value in sample_corrections(row["SampleRunID"]).items():
            if row.get(col) != value:
                changed.append((row["SampleRunID"], col, row.get(col), value))
                row[col] = value
    if changed and not check:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    return changed


def correct_json_yaml(check):
    with open(JSON_PATH, encoding="utf-8") as fh:
        cfg = json.load(fh)
    changed = []
    for sample in cfg.get("samples", []):
        for col, value in sample_corrections(sample.get("SampleRunID", "")).items():
            if sample.get(col) != value:
                changed.append((sample.get("SampleRunID"), col,
                                sample.get(col), value))
                sample[col] = value
    if changed and not check:
        with open(JSON_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        with open(YAML_PATH, "w", encoding="utf-8") as fh:
            yaml.safe_dump(json.loads(json.dumps(cfg)), fh,
                           sort_keys=False, allow_unicode=True,
                           default_flow_style=False)
    return changed


def correct_golden_report(check):
    path = os.path.join(
        REPO, "phase3", "final", "MMU_Final_Formal_Readiness_Package",
        "10_MMU_Golden_Control_Report.md")
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8").read()
    old = ("The legacy `--ctx all` W10 control is rejected: it reports target "
           "PFN `0x83480` / sentinel `0x7d`, while a scoped R02 run reports "
           "`0x834b6` / `0x63`.  No reference to `0x83480` is used as a run "
           "parameter.")
    new = ("The legacy `--ctx all` W10 control is rejected: it reports target "
           "PFN `0x83480` / sentinel `0x7d`, while the final scoped control "
           "`TEST-F1-CTRL-W10-R02` reports target PFN `0x834b2`, neighbour "
           "`0x834b3` and sentinel `0x63`. The earlier scoped control "
           "`TEST-ENV-CTRL-W10` reported `0x834b6`; it predates the final EPAN "
           "checkpoint and is superseded. No reference to `0x83480` or "
           "`0x834b6` is used as a run parameter.")
    if old not in text:
        return None
    if not check:
        open(path, "w", encoding="utf-8").write(text.replace(old, new))
    return "corrected"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report drift without writing")
    args = ap.parse_args(argv)
    wb = correct_workbook(args.check)
    csv_changed = correct_csv(args.check)
    cfg_changed = correct_json_yaml(args.check)
    report = correct_golden_report(args.check)
    result = {
        "mode": "check" if args.check else "apply",
        "workbook": wb,
        "csv_cells_changed": csv_changed,
        "config_cells_changed": cfg_changed,
        "golden_report": report,
        "ok": not any([wb["workbook_cells_changed"], csv_changed, cfg_changed])
              if args.check else True,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
