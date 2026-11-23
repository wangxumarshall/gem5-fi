#!/usr/bin/env python3
"""Assemble LSU_E2E_Causal_Propagation_Final.zip (local only)."""
from __future__ import annotations

import os

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L

EXT = L.EXT
ROOT = Path(os.environ.get("LSU_WORKSPACE_ROOT", str(Path(__file__).resolve().parents[1].parent)))
STAGE = ROOT / "LSU_E2E_Causal_Propagation_Final"
ZIP = ROOT / "LSU_E2E_Causal_Propagation_Final.zip"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def copytree(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    # 1. required reports
    for p in (EXT / "reports").glob("*"):
        shutil.copy2(p, STAGE / p.name)
    # 2. causal chains
    copytree(EXT / "evidence/causal_chains", STAGE / "causal_chains")
    # 3. reproduction code and manifests
    code = STAGE / "code"
    (code / "runner").mkdir(parents=True)
    (code / "configs").mkdir()
    (code / "workloads/src").mkdir(parents=True)
    for p in (EXT / "runner").glob("*.py"):
        shutil.copy2(p, code / "runner" / p.name)
    for p in (EXT / "runner").glob("*.json"):
        shutil.copy2(p, code / "runner" / p.name)
    shutil.copy2(EXT / "configs/lsu_proxy_e2e.py", code / "configs")
    for p in (EXT / "workloads/src").glob("*"):
        shutil.copy2(p, code / "workloads/src" / p.name)
    shutil.copy2(EXT / "workloads/build_e2e_workloads.sh", code / "workloads")
    shutil.copy2(EXT / "workloads/MANIFEST.csv", code / "workloads")
    shutil.copy2(EXT / "workloads/SHA256SUMS", code / "workloads")
    # 4. run state / command / control census snippets
    states = STAGE / "run_states"
    states.mkdir()
    for p in (EXT / "results/state").glob("*.json"):
        shutil.copy2(p, states / p.name)
    cmds = STAGE / "run_commands"
    cmds.mkdir()
    for p in (EXT / "results").glob("*/E2E-*/attempt_1/command.txt"):
        d = p.parts[-3]
        shutil.copy2(p, cmds / f"{d}.command.txt")
    census = STAGE / "control_census"
    census.mkdir()
    for p in (EXT / "results/controls").glob("E2E-*-CTRL/attempt_1/eligible_events.csv"):
        shutil.copy2(p, census / f"{p.parts[-3]}.eligible_events.csv")
    # 5. FS evidence
    fs_src = EXT / "results/fs/boot_ctrl"
    fs_dst = STAGE / "fs_evidence"
    fs_dst.mkdir()
    for name in ("board.terminal", "run.log", "config.ini", "device.dtb"):
        p = fs_src / name
        if p.exists():
            shutil.copy2(p, fs_dst / name)
    # 6. frozen integrity
    frozen = []
    for z in ("LSU_When_v2_Final_Results.zip",
              "LSU_When_v2_Evidence_Hardening_Final.zip",
              "LSU_When_v2_FINAL_CLOSURE.zip"):
        p = ROOT / z
        if p.exists():
            frozen.append((z, sha(p)))
    frozen.append(("inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx",
                   sha(ROOT / "inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx")))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=EXT,
                          capture_output=True, text=True).stdout.strip()
    tag = subprocess.run(["git", "rev-parse",
                          "E2E_Causal_Propagation_20261117"],
                         cwd=EXT, capture_output=True, text=True).stdout.strip()
    with open(STAGE / "FROZEN_INTEGRITY.txt", "w") as f:
        f.write("Historical frozen artifacts (read-only, not modified)\n")
        for k, v in frozen:
            f.write(f"{v}  {k}\n")
        f.write("\nFrozen repo commit: e8759972a8e65856b540629a0defdd7e744ff921\n")
        f.write("Frozen tag: LSU_When_v2_FINAL_FROZEN\n")
        f.write(f"E2E local commit: {head}\n")
        f.write(f"E2E local tag: E2E_Causal_Propagation_20261117 -> {tag}\n")
        f.write("Remote writes: NONE\n")
    # 7. large trace manifest (paths are absolute for recovery)
    with open(EXT / "reports/E2E_Evidence_Index.csv") as fi, \
            open(STAGE / "E2E_Large_Trace_Manifest.csv", "w", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["RunID", "PathRelativeToE2EWorkspace", "Exists",
                    "SizeBytes", "SHA256", "Recovery"])
        rd = csv.DictReader(fi)
        for r in rd:
            w.writerow([r["RunID"], r["Path"], r["Exists"],
                        r["SizeBytes"], r["SHA256"],
                        f"/home/sdc/gem5-fi-LSU/e2e_extension/{r['Path']}"])
    # 8. index
    idx = """# LSU E2E causal propagation — package index

This archive is the local-only deliverable of
`LSU_End_to_End_Causal_Propagation_and_Symptom_Analysis`.

## Contents

* `E2E_Executive_Report.md` — final summary and the ten required answers.
* `E2E_180_Run_Symptom_Matrix.csv` — one row per fault (required columns).
* `E2E_180_Run_Causal_Completion.csv` — per-run layer booleans.
* `E2E_Causal_Gap_Audit.csv` — missing-evidence audit (no invented gaps).
* `E2E_Where_When_Symptom_Comparison.csv` — old When-v2 vs new E2E outcome.
* `E2E_Microarchitecture_to_Software_Evidence.csv` — key evidence per run.
* `E2E_Application_Oracle_Diff.csv` — checksum and first-divergence values.
* `E2E_Crash_Hang_Squash_Masking_Audit.csv` — terminal mechanism audit.
* `E2E_Control_Fault_Pairing.csv` — control/fault identity and ordinals.
* `E2E_Regression_and_Validation.md` — gates and honest limits.
* `E2E_Reproduction_Guide.md` — commands.
* `E2E_Git_Status.md` — local git identity, no remote.
* `E2E_FS_Symptom_Report.md` — FS environment result (blocked; no panic claim).
* `E2E_Symptom_Statistics.csv`, `E2E_Eligible_Census_Comparison.csv`.
* `E2E_Large_Trace_Manifest.csv` — path + size + SHA256 for every raw trace;
  the traces themselves are outside the ZIP at the listed paths.
* `causal_chains/` — 180 x `{json,csv,md}` complete per-fault evidence.
* `run_states/`, `run_commands/`, `control_census/` — exact run identity.
* `code/` — runner, config copy, instrumented workload sources and build.
* `fs_evidence/` — real FS serial boot log and instantiated config.
* `FROZEN_INTEGRITY.txt` — frozen hashes and local commit/tag.

## Verification

```bash
sha256sum -c LSU_E2E_Causal_Propagation_Final.zip.sha256
# restore a raw trace:
gzip -t /home/sdc/gem5-fi-LSU/e2e_extension/<path from manifest>
```

The 180 SE runs are `E2E-*`; the frozen `*-WHEN-*` results were not modified.
No GitHub/remote write was performed.
"""
    (STAGE / "README_INDEX.md").write_text(idx)
    if ZIP.exists():
        ZIP.unlink()
    subprocess.run(["zip", "-r", "-q", str(ZIP), STAGE.name],
                   cwd=ROOT, check=True)
    zh = sha(ZIP)
    (ROOT / "LSU_E2E_Causal_Propagation_Final.zip.sha256").write_text(
        f"{zh}  {ZIP.name}\n")
    print("staged", STAGE)
    print("zip", ZIP, ZIP.stat().st_size, zh)


if __name__ == "__main__":
    main()
