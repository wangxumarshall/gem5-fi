#!/usr/bin/env python3
"""Generate the LSU v3.3.3 final experiment config package.

Reads the frozen authorization manifest and launch script, re-freezes the
binary SHA to the trace-closure build, and writes the final template files.
Historical authorization files are left untouched.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
AUTH = ROOT / "audit_launch_fix_v333/authorization"

# Single source of truth for the model->workload mapping and for the real
# workload bytes: tools/lsu_v333_provenance.py (which imports
# tools/lsu_v332_matrix.py read-only).
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
import lsu_v333_provenance as provenance  # noqa: E402

# The three explicit workload fields; ELF_SHA256 already exists and is
# refreshed from real bytes below.
PROVENANCE_COLUMNS = ("WorkloadSourcePath", "FormalExecutionPath")
OLD_SHA = "1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338"
NEW_SHA = "62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd"
CONFIG_SHA = "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225"
FORMAL_BASE = ROOT / "runs/lsu/formal_v333_final_20261112"
CAMPAIGN_ID = "LSU-V333-FINAL-20261112"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. 120-run campaign manifest template with explicit workload provenance
    src = AUTH / "LSU_120Run_Campaign_Manifest.csv"
    with src.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys())
    # Insert the two new provenance columns next to ELF; ELF_SHA256 already
    # exists and is refreshed from the real bytes below.
    insert_at = fields.index("ELF") + 1
    for offset, name in enumerate(PROVENANCE_COLUMNS):
        if name not in fields:
            fields.insert(insert_at + offset, name)
    for row in rows:
        exec_path = provenance.formal_execution_path(row["ModelID"])
        source_path = provenance.workload_source_path(exec_path.name)
        row["Workload"] = exec_path.name
        # FormalExecutionPath is the only execution path: ELF mirrors it.
        row["ELF"] = str(exec_path)
        row["WorkloadSourcePath"] = str(source_path) if source_path else ""
        row["FormalExecutionPath"] = str(exec_path)
        row["ELF_SHA256"] = provenance.sha256_file(exec_path)
        row["Binary_SHA256"] = NEW_SHA
        row["Config_SHA256"] = CONFIG_SHA
        row["Evidence"] = str(FORMAL_BASE / f"{row['ModelID']}-{row['ContextID']}-{row['Role']}")
        row["EvidenceKind"] = "FORMAL_TEMPLATE"
    dst = OUT / "LSU_Final_Campaign_Manifest_Template.csv"
    with dst.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # 2. launch commands (new SHA / campaign id)
    # The shipped script is maintained by the pipeline owner (campaign root
    # already corrected); never clobber it with the authorization base copy.
    launch_path = OUT / "launch_commands_final.sh"
    if not launch_path.exists():
        launch = (AUTH / "launch_commands.sh").read_text()
        launch = launch.replace(OLD_SHA, NEW_SHA)
        launch = launch.replace("LSU-V333-FORMAL-20261112", CAMPAIGN_ID)
        launch_path.write_text(launch)
        launch_path.chmod(0o755)

    # 3. binary provenance
    binary = ROOT / "build/ARM/gem5.opt"
    config = ROOT / "configs/se/lsu_proxy.py"
    build_log = ROOT / "audit_v3_3_3/trace_closure/baseline/build.log"
    old_binary = ROOT / "audit_v3_3_3/trace_closure/baseline/gem5.opt.v333-old-1126e0fd"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                   text=True).strip()
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                     cwd=ROOT, text=True).strip()
    diff_stat = subprocess.check_output(
        ["git", "diff", "--stat", "--", "CHAOS/gem5/src", "tools", "tests",
         "docs/superpowers/plans"], cwd=ROOT, text=True)
    provenance_doc = f"""# LSU v3.3.3 Final Binary Provenance (Trace Closure)

**Date:** 2026-11-12
**Worktree:** `{ROOT}`
**Branch:** `{branch}`
**HEAD at generation:** `{head}`
**Config SHA256:** `{sha(config)}`
**Previous frozen binary (superseded):** `{OLD_SHA}` (backup: `{old_binary}`)
**Final frozen binary:** `{sha(binary) if binary.exists() else 'MISSING'}`
**Build log:** `{build_log}`

## Build and install (one build only)

```console
$ cd {ROOT}/CHAOS/gem5
$ scons -j16 build/ARM/gem5.opt
$ cp CHAOS/gem5/build/ARM/gem5.opt {ROOT}/build/ARM/gem5.opt
$ sha256sum {ROOT}/build/ARM/gem5.opt
{NEW_SHA}  {ROOT}/build/ARM/gem5.opt
```

The runner resolves `ROOT/build/ARM/gem5.opt` (the worktree root). The
main-repo binary `/home/sdc/gem5-fi-ding/build/ARM/gem5.opt`
(`6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`) is
not this build and must never be used.

## Source changes in this build

{diff_stat.strip()}

The only C++ behavior changes are read-only observation hooks:
`CHAOSPropagation` (SP05 store-commit capture / writeback-suppressed record /
RP01 watchdog terminal flush), `CHAOSLSQFwd` (RP01 terminal snapshot and
last-eligible bookkeeping), `lsq_unit.cc` (post-completion suppression
record), and read-only `LSQ` accessors. No injection semantics, workload,
seed, SampleRunID, ROI percentile, dynamic context or Fault-Control pairing
was changed.

## Workload ELF SHA256 (unchanged)

| Workload | SHA256 |
|---|---|
| `agu_addrmodes` | `90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b` |
| `sq_reload_v3212` | `bcab9cc5e1e4ed3854c3677bda0265d7aaefdedc0e7d69beecd6a2567d178de6` |
| `replay_partial_v332` | `3f880cba7b6d16b61a453c37c68d6dbaaf63980dba5c9231218cf8dd8fa42e42` |

The full frozen workload table remains in
`audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`.

## Campaign identity

`{CAMPAIGN_ID}`. All 120 formal runs must use this binary and the config SHA
above; old-binary pilot traces are archived separately and must not be mixed
into the formal result set.
"""
    # The corrected provenance is maintained explicitly; never overwrite it
    # with this legacy template when it already exists.
    if not (OUT / "LSU_Final_Binary_Provenance.md").exists():
        (OUT / "LSU_Final_Binary_Provenance.md").write_text(provenance_doc)

    # 4. checksums
    lines = []
    for name in ("LSU_Final_Experiment_Config.xlsx",
                 "LSU_Final_Campaign_Manifest_Template.csv",
                 "LSU_Final_Binary_Provenance.md",
                 "SOURCE_MANIFEST.sha256",
                 "01_launch_campaign.sh", "02_manifest_only.sh",
                 "03_full_collector.sh", "04_final_reports.sh",
                 "launch_commands_final.sh",
                 "RUNBOOK_Final_Formal_Campaign.md"):
        p = OUT / name
        if p.exists():
            lines.append(f"{sha(p)}  ./{name}")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
