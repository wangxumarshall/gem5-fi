#!/usr/bin/env python3
"""Build MMU FINAL FROZEN DELIVERY: 3 ZIPs + manifest (no V3 overwrite).

Mirrors campaign/package_v2_delivery.py but targets the frozen delivery dir,
uses the corrected final files, and expands the source snapshot to the full
key-source set + cumulative patch. ZIP64 + deflate. No experiment changes.
"""
import csv
import hashlib
import os
import shutil
import zipfile

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
DELIVERY = os.path.join(ROOT, "exports", "MMU_FINAL_FROZEN_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
V3 = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
RETRY2 = os.path.join(ROOT, "runs", "W5X3_RETRY2")
GEM5 = os.path.join(ROOT, "CHAOS", "gem5")
WORK = os.path.join(ROOT, "work")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def add_file(zf, src, arc):
    zf.write(src, arc, compress_type=zipfile.ZIP_DEFLATED)


def add_dir_tree(zf, base, prefix):
    n = 0
    for root, _, files in os.walk(base):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, base)
            zf.write(p, os.path.join(prefix, rel),
                     compress_type=zipfile.ZIP_DEFLATED)
            n += 1
    return n


def pick(fn):
    """Return an existing path for fn, searching DELIVERY, V3, ANALYSIS, ROOT."""
    for base in (DELIVERY, V3, ANALYSIS, ROOT):
        p = os.path.join(base, fn)
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(fn)


# ---- 19 key source files (relative path in CHAOS/gem5) ----
SOURCE_FILES = [
    "src/cpu/o3/lsq.cc",
    "src/cpu/o3/lsq.hh",
    "src/cpu/o3/lsq_unit.cc",
    "src/cpu/o3/fetch.cc",
    "src/cpu/o3/fetch.hh",
    "src/cpu/o3/decode.cc",
    "src/cpu/o3/commit.cc",
    "src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc",
    "src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh",
    "src/mem/cache/cache.cc",
    "src/mem/cache/base.cc",
    "src/arch/arm/mmu.cc",
    "src/arch/arm/mmu.hh",
    "src/arch/arm/tlb.cc",
    "src/arch/arm/tlb.hh",
    "src/arch/arm/table_walker.cc",
    "src/arch/arm/table_walker.hh",
    "src/arch/arm/pagetable.hh",
    "src/arch/arm/faults.cc",
]

SOURCE_PATCHES = [
    (os.path.join(V3, "..", "MMU_E2E_FINAL_DELIVERY", "_stage", "raw_source",
                  "source", "Frozen_Source.patch"),
     "source_patches/Frozen_Source.patch"),
    (os.path.join(WORK, "gem5_observational_changes.diff"),
     "source_patches/gem5_observational_changes.diff"),
]


def zip1(zf):
    files = ["REPORT.md", "final_acceptance.md", "acceptance.json",
             "FINAL_EVIDENCE_REPORT.md",
             "experiment_status.csv", "per_condition.json",
             "partial23_repair_comparison.csv", "per_model_completeness.csv",
             "terminal_symptoms.csv", "completeness.csv",
             "propagation_chains.csv", "summary_by_model.csv",
             "fault_control_compare.csv", "timing_map.csv",
             "conditions.json", "control_map.json",
             "final_issue_closure.csv",
             "M07_C02_FINAL_CLOSURE.md", "M06_C05_PILOT_EVIDENCE.md",
             "M07_C02_T01_COMPLETE_PROPAGATION.md",
             "M07_C02_T02_COMPLETE_PROPAGATION.md"]
    for fn in files:
        add_file(zf, pick(fn), fn)


def zip2(zf):
    files = ["causal_nodes.csv", "causal_edges.csv", "causal_branches.csv",
             "per_condition.json", "propagation_chains.csv",
             "chain_edges.csv", "chain_branches.csv",
             "authoritative_trace_index.csv", "completeness.csv",
             "retry2_map.json", "retry2_evidence_index.json",
             "control_map.json"]
    for fn in files:
        add_file(zf, pick(fn), fn)
    add_dir_tree(zf, os.path.join(V3, "PARTIAL23_REPAIR_EVIDENCE"),
                 "PARTIAL23_REPAIR_EVIDENCE")
    add_dir_tree(zf, os.path.join(V3, "per_sample_e2e_paths"),
                 "per_sample_e2e_paths")


def zip3(zf):
    add_dir_tree(zf, RETRY2, "runs/W5X3_RETRY2")
    # W5X3-OBS-0222 re-runs (M07-C02-T01/T02 + matching control)
    add_dir_tree(zf, os.path.join(ROOT, "runs", "W5X3_OBS"), "runs/W5X3_OBS")
    # full key-source snapshot
    for rel in SOURCE_FILES:
        add_file(zf, os.path.join(GEM5, rel),
                 "gem5_source/" + rel.replace("/", "_"))
    for src, arc in SOURCE_PATCHES:
        add_file(zf, src, arc)
    add_file(zf, os.path.join(ROOT, "work", "0222_lsq_translation_lifecycle.patch"),
             "source_patches/0222_lsq_translation_lifecycle.patch")
    add_file(zf, os.path.join(DELIVERY, "SOURCE_SNAPSHOT.md"),
             "SOURCE_SNAPSHOT.md")
    for fn in ["0202c_source_diff.md", "0202c_instrumentation_spec.md",
               "0202c_source_call_sites.md"]:
        add_file(zf, os.path.join(WORK, fn), "docs/" + fn)
    for fn in ["campaign/propagation.py", "campaign/finalize.py",
               "campaign/acceptance.py", "campaign/validate.py",
               "campaign/export_evidence.py", "campaign/gen_v2_delivery.py",
               "campaign/gen_causal_dag.py", "campaign/gen_repair_evidence.py",
               "campaign/control_map.py", "campaign/oracle.py",
               "campaign/gen_report.py", "campaign/gen_issue_closure.py",
               "campaign/run_fb1b_controls.py",
               "campaign/when5x3_retry2.py", "campaign/make_retry2_index.py",
               "tools/prop_trace_dump.py"]:
        add_file(zf, os.path.join(ROOT, fn), fn)
    repro = os.path.join(V3, "REPRODUCTION.md")
    if not os.path.isfile(repro):
        repro = os.path.join(WORK, "REPRODUCTION_V3.md")
    add_file(zf, repro, "REPRODUCTION.md")
    add_dir_tree(zf, os.path.join(ANALYSIS, "eligible_events"),
                 "analysis/eligible_events")
    add_dir_tree(zf, os.path.join(ROOT, "workloads", "mmu_w5x3"),
                 "workloads/mmu_w5x3")
    add_dir_tree(zf, os.path.join(ROOT, "campaign", "rcs"), "campaign/rcs")
    add_dir_tree(zf, os.path.join(ROOT, "runs", "pilot", "M06-C05"),
                 "runs/pilot/M06-C05")
    add_dir_tree(zf, os.path.join(WORK, "disasm"), "disasm")
    add_file(zf, os.path.join(WORK, "REPRODUCTION_V3.md"),
             "docs/REPRODUCTION_V3.md")


def main():
    os.makedirs(DELIVERY, exist_ok=True)
    zips = {
        "MMU_FINAL_REPORT.zip": zip1,
        "MMU_FINAL_CAUSAL_EVIDENCE.zip": zip2,
        "MMU_FINAL_RAW_AND_SOURCE.zip": zip3,
    }
    results = []
    for name, fn in zips.items():
        path = os.path.join(DELIVERY, name)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED,
                             allowZip64=True) as zf:
            fn(zf)
        size = os.path.getsize(path)
        h = sha256(path)
        # count files
        with zipfile.ZipFile(path) as zf:
            n = len(zf.namelist())
        results.append((name, path, size, n, h))
        print("%s  %d bytes  %d files  %s" % (name, size, n, h))

    # copy historical archives into frozen delivery as sibling files
    copied = []
    for src, dst in [
        (os.path.join(ROOT, "MMU_Propagation_Traces.tar.zst"),
         "MMU_Propagation_Traces.tar.zst"),
        (os.path.join(ROOT, "MMU_When_Golden_Evidence.tar.gz"),
         "MMU_When_Golden_Evidence.tar.gz"),
    ]:
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(DELIVERY, dst))
            copied.append((dst, os.path.getsize(src), sha256(src)))
    for dst, size, h in copied:
        print("copied %s  %d bytes  %s" % (dst, size, h))

    # persistence for manifest
    with open(os.path.join(DELIVERY, "_build.json"), "w") as f:
        import json
        json.dump({"zips": results, "archives": copied}, f, indent=2)
    print("DONE")


if __name__ == "__main__":
    main()