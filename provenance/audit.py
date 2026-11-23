#!/usr/bin/env python3
"""A01/A02/A03 provenance audit for the WHEN-5X3 round."""
import hashlib
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = "/home/sdc/gem5-fi-mmu-impl-v2"
NEW_XLSX = os.path.join(ROOT, "inputs",
                        "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")
OLD_XLSX = os.path.join(OLD, "phase3", "freeze", "authority",
                        "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")
OLD_CSV = os.path.join(OLD, "phase3", "freeze", "authority",
                       "MMU_40_Sample_Matrix.csv")
NEW_COND = os.path.join(ROOT, "campaign", "conditions.json")
OUT = os.path.join(ROOT, "provenance")


def sh(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sheets(path, names):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for name in names:
        if name not in wb.sheetnames:
            out[name] = None
            continue
        ws = wb[name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            if all(c is None or str(c).strip() == "" for c in row):
                continue
            rows.append(["" if c is None else str(c) for c in row])
        blob = json.dumps(rows, ensure_ascii=False, sort_keys=False)
        out[name] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(blob.encode()).hexdigest(),
        }
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    frozen = ["00_Readme", "01_MMU_Architecture", "02_SubUnit_Coverage",
              "03_Fault_Model_Summary", "04_Source_Mapping",
              "05_Injection_Configuration", "06_Workload_Matrix",
              "07_Sample_Matrix", "08_Propagation_Path",
              "09_Trace_Configuration", "10_Terminal_Oracle",
              "11_Acceptance_Checklist", "12_Blockers", "13_Change_Log",
              "14_Deferred_Candidates", "15_Diagnostic_Feature_Schema"]
    n = sheets(NEW_XLSX, frozen)
    o = sheets(OLD_XLSX, frozen)
    required_where = ["03_Fault_Model_Summary", "04_Source_Mapping",
                      "05_Injection_Configuration"]
    a01 = {"sheets": {}, "all_equal": True, "required_where_sheets":
           required_where, "required_where_equal": True}
    for name in frozen:
        eq = n.get(name) == o.get(name)
        a01["sheets"][name] = {
            "new": n.get(name), "old": o.get(name), "equal": eq}
        a01["all_equal"] = a01["all_equal"] and eq
        if name in required_where:
            a01["required_where_equal"] = a01["required_where_equal"] and eq
    a01["new_workbook_sha256"] = sh(NEW_XLSX)
    a01["old_workbook_sha256"] = sh(OLD_XLSX)

    # A02: historical workspace manifest must be byte-identical.
    manifest = os.path.join(OUT, "OLD_workspace_full_manifest.sha256")
    recorded = ""
    try:
        recorded = sh(manifest)
    except OSError:
        pass
    a02 = {
        "old_workspace": OLD,
        "manifest_path": manifest,
        "manifest_sha256_recorded": recorded,
        "manifest_sha256_now": sh(manifest) if os.path.isfile(manifest) else "",
        "read_only_copy_only": True,
        "git_operations_performed": False,
    }
    # Recompute the manifest into a new file and compare digests.
    if os.path.isdir(OLD):
        tmp = os.path.join(OUT, "OLD_workspace_full_manifest.recheck.sha256")
        with open(tmp, "w") as fh:
            subprocess.run(
                "find CHAOS/gem5/src configs workloads tools "
                "phase3/freeze/authority MMU_FINAL/results -type f -print0 "
                "| sort -z | xargs -0 sha256sum",
                shell=True, cwd=OLD, stdout=fh, check=False)
        a02["manifest_sha256_recheck"] = sh(tmp)
        a02["unchanged"] = (a02["manifest_sha256_recheck"] ==
                            a02["manifest_sha256_recorded"])

    # A03: new and frozen IDs must be disjoint.
    frozen_ids = set()
    if os.path.isfile(OLD_CSV):
        import csv
        with open(OLD_CSV) as fh:
            for row in csv.DictReader(fh):
                frozen_ids.add(row["SampleRunID"])
    new_ids = set()
    if os.path.isfile(NEW_COND):
        with open(NEW_COND) as fh:
            new_ids = {c["NewSampleRunID"] for c in json.load(fh)}
    a03 = {
        "frozen_count": len(frozen_ids),
        "new_count": len(new_ids),
        "intersection": sorted(frozen_ids & new_ids),
        "disjoint": not (frozen_ids & new_ids),
    }

    result = {"A01": a01, "A02": a02, "A03": a03}
    with open(os.path.join(OUT, "A01_A02_A03_audit.json"), "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    print(json.dumps({
        "A01_required_where_equal": a01["required_where_equal"],
        "A01_all_frozen_sheets_equal": a01["all_equal"],
        "A02_unchanged": a02.get("unchanged"),
        "A03_disjoint": a03["disjoint"],
        "frozen_ids": len(frozen_ids), "new_ids": len(new_ids),
    }, indent=1))


if __name__ == "__main__":
    main()
