#!/usr/bin/env python3
"""Assemble LSU_E2E_Strict_Causal_Evidence_Final.zip (local only)."""
from __future__ import annotations

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
ROOT = L.ROOT
STAGE = ROOT / "LSU_E2E_Strict_Causal_Evidence_Final"
ZIP = ROOT / "LSU_E2E_Strict_Causal_Evidence_Final.zip"

REQUIRED = [
    "STRICT_E2E_EXECUTIVE_REPORT.md",
    "STRICT_E2E_180_FAULT_AUDIT.csv",
    "STRICT_E2E_CAUSAL_EDGES.csv",
    "STRICT_E2E_SOFTWARE_SYMPTOMS.csv",
    "STRICT_E2E_MASKING_AUDIT.csv",
    "STRICT_E2E_RP01_STALL_AUDIT.csv",
    "STRICT_E2E_SQUASH_AUDIT.csv",
    "STRICT_E2E_OBSERVATION_EQUIVALENCE.csv",
    "STRICT_E2E_RERUN_MANIFEST.csv",
    "STRICT_E2E_GAP_MATRIX.csv",
    "STRICT_E2E_REGRESSION_REPORT.md",
    "STRICT_E2E_REPRODUCTION_GUIDE.md",
    "STRICT_E2E_GIT_STATUS.md",
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def copy_required():
    for name in REQUIRED:
        p = EXT / "reports" / name
        if not p.exists():
            raise SystemExit(f"missing required report: {name}")
        shutil.copy2(p, STAGE / name)


def copy_code():
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
    for name in ("build_e2e_workloads.sh", "MANIFEST.csv", "SHA256SUMS"):
        p = EXT / "workloads" / name
        if p.exists():
            shutil.copy2(p, code / "workloads" / name)
    for p in (EXT / "tests").glob("*.py"):
        (code / "tests").mkdir(exist_ok=True)
        shutil.copy2(p, code / "tests" / p.name)
    # gem5 observation source + local patch (frozen commit -> observation).
    obs = code / "gem5_observation"
    files = [
        "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc",
        "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh",
        "CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py",
        "CHAOS/gem5/src/cpu/o3/inst_queue.cc",
        "CHAOS/gem5/src/cpu/o3/inst_queue.hh",
        "CHAOS/gem5/src/cpu/o3/lsq_unit.cc",
        "CHAOS/gem5/src/cpu/o3/lsq_unit.hh",
        "CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc",
        "CHAOS/gem5/src/cpu/o3/mem_dep_unit.hh",
    ]
    for f in files:
        dst = obs / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "repo" / f, dst)
    patch = subprocess.run(
        ["git", "diff", "e8759972a8e65856b540629a0defdd7e744ff921..HEAD",
         "--"] + files, cwd=str(ROOT / "repo"), capture_output=True,
        text=True).stdout
    (code / "gem5_observation.patch").write_text(patch)


def copy_states():
    st = STAGE / "run_states"
    st.mkdir()
    for p in (EXT / "results/state").glob("*.json"):
        shutil.copy2(p, st / p.name)
    rst = STAGE / "rp01_rerun_states"
    rst.mkdir()
    for p in (EXT / "results_strict_rp01/state").glob("*.json"):
        shutil.copy2(p, rst / p.name)
    cmds = STAGE / "run_commands"
    cmds.mkdir()
    for p in (EXT / "results").glob("*/E2E-*/attempt_1/command.txt"):
        d = p.parts[-3]
        shutil.copy2(p, cmds / f"{d}.command.txt")
    for p in (EXT / "results_strict_rp01").glob(
            "*/RP01OBS-*/attempt_1/command.txt"):
        d = p.parts[-3]
        shutil.copy2(p, cmds / f"{d}.command.txt")
    census = STAGE / "control_census"
    census.mkdir()
    for p in (EXT / "results/controls").glob(
            "E2E-*-CTRL/attempt_1/eligible_events.csv"):
        shutil.copy2(p, census / f"{p.parts[-3]}.eligible_events.csv")
    # RP01 stall traces are small and are the key new evidence.
    stall = STAGE / "rp01_stall_traces"
    stall.mkdir()
    for p in (EXT / "results_strict_rp01/faults").glob(
            "RP01OBS-*/attempt_1/rp01_stall.csv.gz"):
        shutil.copy2(p, stall / f"{p.parts[-3]}.rp01_stall.csv.gz")


def frozen_integrity():
    frozen = []
    for z in ("LSU_When_v2_Final_Results.zip",
              "LSU_When_v2_Evidence_Hardening_Final.zip",
              "LSU_When_v2_FINAL_CLOSURE.zip"):
        p = ROOT / z
        if p.exists():
            frozen.append((z, sha(p)))
    frozen.append(("inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx",
                   sha(ROOT / "inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx")))
    frozen.append(("LSU_When_v2_FINAL_FROZEN/FINAL_180_FAULT_EVIDENCE.csv",
                   sha(ROOT / "LSU_When_v2_FINAL_FROZEN/"
                       "FINAL_180_FAULT_EVIDENCE.csv")))
    e2e_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=EXT,
                              capture_output=True, text=True).stdout.strip()
    e2e_tag = subprocess.run(["git", "rev-parse",
                              "E2E_Pre_Strict_Repair_20261117"], cwd=EXT,
                             capture_output=True, text=True).stdout.strip()
    with open(STAGE / "FROZEN_INTEGRITY.txt", "w") as f:
        f.write("Historical frozen artifacts (read-only, not modified)\n")
        for k, v in frozen:
            f.write(f"{v}  {k}\n")
        f.write("\nFrozen repo commit: "
                "e8759972a8e65856b540629a0defdd7e744ff921\n")
        f.write("Frozen tag: LSU_When_v2_FINAL_FROZEN\n")
        f.write(f"E2E strict commit: {e2e_head}\n")
        f.write(f"E2E pre-repair checkpoint tag: "
                f"E2E_Pre_Strict_Repair_20261117 -> {e2e_tag}\n")
        f.write(f"Observation binary: bin/gem5.opt.obs "
                f"{sha(EXT / 'bin/gem5.opt.obs')}\n")
        f.write(f"Original binary: bin/gem5.opt.original "
                f"{sha(EXT / 'bin/gem5.opt.original')}\n")
        f.write("Remote writes: NONE\n")


def trace_manifest():
    src = EXT / "reports/STRICT_E2E_EVIDENCE_INDEX.csv"
    out = STAGE / "STRICT_E2E_LARGE_TRACE_MANIFEST.csv"
    with open(src) as fi, open(out, "w", newline="") as fo:
        r = csv.DictReader(fi)
        w = csv.writer(fo)
        w.writerow(["RunID", "EvidenceType", "PathRelativeToE2E",
                    "AbsolutePath", "Exists", "SizeBytes", "SHA256"])
        for row in r:
            w.writerow([row["RunID"], row["EvidenceType"], row["Path"],
                        str(EXT / row["Path"]), row["Exists"],
                        row["SizeBytes"], row["SHA256"]])


def index_md():
    text = """# LSU strict E2E causal evidence — package index

This archive is the local-only deliverable of
`LSU_E2E_Strict_Causal_Evidence_Repair`.

## Reports

* `STRICT_E2E_EXECUTIVE_REPORT.md` — what was repaired and the ten answers.
* `STRICT_E2E_180_FAULT_AUDIT.csv` — one row per fault with its strict status.
* `STRICT_E2E_CAUSAL_EDGES.csv` — every exported edge with its evidence level.
* `STRICT_E2E_SOFTWARE_SYMPTOMS.csv` — first divergent object and value.
* `STRICT_E2E_MASKING_AUDIT.csv` — A–F termination mechanism with proof.
* `STRICT_E2E_RP01_STALL_AUDIT.csv` — 15 post-injection stall chains.
* `STRICT_E2E_SQUASH_AUDIT.csv` — six frozen squash paths.
* `STRICT_E2E_OBSERVATION_EQUIVALENCE.csv` — marker impact on the stream.
* `STRICT_E2E_RERUN_MANIFEST.csv` — the 20 RP01 observation re-runs.
* `STRICT_E2E_GAP_MATRIX.csv` — every unresolved gap (if any).
* `STRICT_E2E_REGRESSION_REPORT.md` — executed gates and real output.
* `STRICT_E2E_REPRODUCTION_GUIDE.md` — commands.
* `STRICT_E2E_GIT_STATUS.md` — true branch/commit/binary state.

## Evidence

* `causal_chains/` — 180 x `{json,csv,md}` strict chains.
* `rp01_stall_traces/` — the new RP01 post-injection traces.
* `run_states/`, `rp01_rerun_states/`, `run_commands/`,
  `control_census/` — run identity.
* `code/` — runner, config, workload sources, tests.
* `STRICT_E2E_LARGE_TRACE_MANIFEST.csv` — absolute path and SHA256 for every
  large raw trace; traces stay outside the ZIP.
* `FROZEN_INTEGRITY.txt` — frozen and local artifact hashes.

## Verification

```bash
sha256sum -c LSU_E2E_Strict_Causal_Evidence_Final.zip.sha256
unzip -t LSU_E2E_Strict_Causal_Evidence_Final.zip
```

No GitHub/remote write was performed.
"""
    (STAGE / "README_INDEX.md").write_text(text)


def main():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    copy_required()
    shutil.copytree(EXT / "evidence/strict_delivery/causal_chains",
                    STAGE / "causal_chains")
    copy_code()
    copy_states()
    frozen_integrity()
    trace_manifest()
    index_md()
    # Per-file hashes for the packaged tree.
    with open(STAGE / "SHA256SUMS", "w") as f:
        for p in sorted(STAGE.rglob("*")):
            if p.is_file() and p.name != "SHA256SUMS":
                f.write(f"{sha(p)}  {p.relative_to(STAGE)}\n")
    if ZIP.exists():
        ZIP.unlink()
    subprocess.run(["zip", "-r", "-q", str(ZIP), STAGE.name],
                   cwd=ROOT, check=True)
    zh = sha(ZIP)
    (ROOT / "LSU_E2E_Strict_Causal_Evidence_Final.zip.sha256").write_text(
        f"{zh}  {ZIP.name}\n")
    print("staged", STAGE)
    print("zip", ZIP, ZIP.stat().st_size, zh)


if __name__ == "__main__":
    main()
