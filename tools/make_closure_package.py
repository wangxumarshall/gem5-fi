#!/usr/bin/env python3
"""Assemble MMU_PreFormal_Closure_Package.zip from real artefacts.

Never copies multi-GB disk images; records their paths + SHA256 instead.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys

RUNS = [
    "TEST-M01-R01", "TEST-M02-R01",
    "TEST-M03-R01", "TEST-M03-R02", "TEST-M03-R03", "TEST-M03-R04",
    "TEST-M03-R05",
    "TEST-M04-FR01", "TEST-M04-FR02", "TEST-M04-FR03", "TEST-M04-FR04",
    "TEST-M04-FR05",
    "TEST-M05-R01", "TEST-M05-R02", "TEST-M05-R03", "TEST-M05-R04",
    "TEST-M05-R05",
    "TEST-M06-R01", "TEST-M06-R02C", "TEST-M06-R03B", "TEST-M06-R04B",
    "TEST-M06-R05B",
    "TEST-M07-R01", "TEST-M07-R02", "TEST-M07-R03", "TEST-M07-R04",
    "TEST-M07-R05",
    "TEST-M08-R01", "TEST-M08-R02", "TEST-M08-R03", "TEST-M08-R04",
    "TEST-M08-R05B",
    "TEST-CTRL-W11-CLOSURE", "TEST-CTRL-W12-R01", "TEST-CTRL-W12-R02",
    "TEST-CTRL-W12-R03", "TEST-CTRL-W12-R04", "TEST-CTRL-W12-R05",
]

RUN_FILES = [
    "Run_Log/board.terminal", "Run_Log/golden_output.txt",
    "Run_Log/observed_output.txt", "Run_Log/gem5_stdout.log",
    "Run_Log/gem5_exit_code.txt", "Run_Log/command.txt",
    "Run_Log/stats.txt", "Trace/prop_evt.txt.gz",
    "Validation/verdict.json", "Validation/verdict.md",
    "sample_manifest.json", "SHA256/SHA256SUMS.txt",
    "FAILED_LAUNCH.txt", "TIMEOUT_EVIDENCE.txt", "FAILED_SCOPE.txt",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = os.path.abspath(args.repo_root)
    out = args.out or os.path.join(root, "phase3", "closure_package",
                                   "MMU_PreFormal_Closure_Package")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)

    def rp(rel):
        return os.path.join(root, rel)

    # A_Status
    for rel in ("phase3/formal/MMU_Readiness_Matrix_FINAL.md",
                "phase3/formal/MMU_Context_Readiness_FINAL.csv",
                "phase3/formal/evidence_index.json",
                "phase3/formal/FS_RUN_MATRIX.md",
                "phase3/formal/Seed_Semantics_Audit.md",
                "phase3/formal/pilot_runs.json",
                "phase3/formal/w12_decoy_map.json",
                "phase3/formal/preflight_summary.json",
                "phase3/formal/MMU_40_Sample_DryRun.csv",
                "phase3/formal/MMU_40_Sample_DryRun.md",
                "phase3/formal/Missing_Seed_Report.md",
                "phase3/formal/MMU_Formal_Readiness_FINAL.md",
                "phase3/formal/final/preflight_summary.json",
                "phase3/formal/final/MMU_40_Sample_DryRun.csv",
                "phase3/formal/final/MMU_40_Sample_DryRun.md",
                "phase3/formal/final/Missing_Seed_Report.md",
                "phase3/final_binary.sha256",
                "phase3_build_closure_final.log"):
        if os.path.isfile(rp(rel)):
            copy(rp(rel), os.path.join(out, "A_Status", os.path.basename(rel)))

    # B_Code
    src_files = [
        "CHAOS/gem5/src/arch/arm/tlb.cc",
        "CHAOS/gem5/src/arch/arm/tlb.hh",
        "CHAOS/gem5/src/arch/arm/pagetable.hh",
        "CHAOS/gem5/src/arch/arm/table_walker.cc",
        "CHAOS/gem5/src/arch/arm/table_walker.hh",
        "CHAOS/gem5/src/arch/arm/mmu.cc",
        "CHAOS/gem5/src/arch/arm/mmu.hh",
        "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc",
        "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh",
        "CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.py",
        "CHAOS/gem5/src/cpu/o3/commit.cc",
        "configs/se/arm_chaos_fs.py",
    ]
    hashes = []
    for rel in src_files:
        if os.path.isfile(rp(rel)):
            dst = copy(rp(rel), os.path.join(out, "B_Code",
                                             rel.replace("/", "__")))
            hashes.append("%s  %s" % (sha256(dst), rel))
    with open(os.path.join(out, "B_Code", "Source_SHA256.txt"), "w") as fh:
        fh.write("\n".join(hashes) + "\n")

    # C_Workloads
    for rel in ("workloads/mmu/W10S/mmu_w10s.c",
                "workloads/mmu/W10S/mmu_w10s",
                "workloads/mmu/W11/mmu_w11.c",
                "workloads/mmu/W11/mmu_w11",
                "workloads/mmu/W13/mmu_w13.c",
                "workloads/mmu/W13/mmu_w13",
                "workloads/mmu/W10/mmu_w10.c",
                "workloads/mmu/W10/mmu_w10"):
        if os.path.isfile(rp(rel)):
            copy(rp(rel), os.path.join(out, "C_Workloads",
                                       os.path.basename(rel)))
    for rel in ("configs/fs/mmu_w11_run.rcS", "configs/fs/mmu_w13_run.rcS",
                "configs/fs/mmu_w10s_run.rcS"):
        if os.path.isfile(rp(rel)):
            copy(rp(rel), os.path.join(out, "C_Workloads",
                                       os.path.basename(rel)))

    # D_FaultPilot (no disk images)
    for run in RUNS:
        run_dir = rp("runs/" + run)
        if not os.path.isdir(run_dir):
            continue
        for rel in RUN_FILES:
            src = os.path.join(run_dir, rel)
            if os.path.isfile(src):
                copy(src, os.path.join(out, "D_FaultPilot", run,
                                       rel.replace("/", "__")))

    # E_Contexts / model reports
    for rel in ("phase3/m03/M03_W11_HANDSHAKE.md",
                "phase3/m03/M03_R01_EVIDENCE.md",
                "phase3/m04/M04_LINEAGE_FIX.md",
                "phase3/m04/M04_VALIDATOR_REQUIREMENTS.md",
                "phase3/m05/M05_FINAL_R01_FINDING.md",
                "phase3/m05/M05_TERMINAL_ANALYSIS.md",
                "phase3/m06/M06_FINAL_R01_EVIDENCE.md",
                "phase3/m06/M06_R02_COLD_FINDING.md",
                "phase3/m06/M06_TERMINAL_PROPOSAL.md",
                "phase3/m07/M07_R02_ATOMIC_FINDING.md",
                "phase3/m07/M07_R03_R05_FINDING.md",
                "phase3/w10s/W10S_FIX.md"):
        if os.path.isfile(rp(rel)):
            copy(rp(rel), os.path.join(out, "E_Contexts",
                                       os.path.basename(rel)))

    # F_Formal tools
    for name in ("mmu_formal_preflight.py", "mmu_formal_runner.py",
                 "mmu_formal_validate.py", "mmu_trace_validate_v3.py",
                 "mmu_trace_validate_v4.py", "mmu_build_evidence_index.py",
                 "mmu_readiness_matrix.py", "mmu_collect_w12_decoy.py"):
        src = rp("tools/" + name)
        if os.path.isfile(src):
            copy(src, os.path.join(out, "F_Formal", "tools", name))

    # Manifest
    manifest = []
    for dirpath, _dirs, files in os.walk(out):
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            manifest.append("%s  %s" % (sha256(path),
                                        os.path.relpath(path, out)))
    os.makedirs(os.path.join(out, "G_Manifest"), exist_ok=True)
    with open(os.path.join(out, "G_Manifest", "MANIFEST_SHA256.txt"), "w") as fh:
        fh.write("\n".join(manifest) + "\n")
    print(json.dumps({"out": out, "files": len(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
