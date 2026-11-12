#!/usr/bin/env python3
"""Regenerate Validation/verdict.{json,md} from the frozen traces.

No gem5 process is launched and no trace is modified.  For every sample in
phase3/formal/evidence_index.json the canonical run directory is revalidated
with tools/mmu_formal_validate.py.  The previous verdict is preserved as
Validation/pre_v2_verdict.{json,md,stdout.log} before the first overwrite.

Usage:
  tools/mmu_regenerate_verdicts.py [--only M03/R05 M07/R04 ...] [--dry-run]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "phase3", "formal", "evidence_index.json")
VALIDATOR = os.path.join(REPO, "tools", "mmu_formal_validate.py")


def _read_json(path):
    with open(path) as fh:
        return json.load(fh)


def _backup(run_dir):
    val = os.path.join(run_dir, "Validation")
    pairs = [("verdict.json", "pre_v2_verdict.json"),
             ("verdict.md", "pre_v2_verdict.md"),
             ("validator_stdout.log", "pre_v2_validator_stdout.log")]
    for src, dst in pairs:
        s = os.path.join(val, src)
        d = os.path.join(val, dst)
        if os.path.isfile(s) and not os.path.isfile(d):
            shutil.copy2(s, d)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None,
                    help="sample keys, e.g. M03/R05")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    index = _read_json(INDEX)["contexts"]
    keys = args.only or sorted(index)
    rows = []
    for key in keys:
        entry = index.get(key)
        if not entry:
            print("MISSING INDEX ENTRY", key, file=sys.stderr)
            return 2
        run_dir = entry["run_dir"]
        manifest = _read_json(os.path.join(run_dir, "sample_manifest.json"))
        va = manifest.get("target_va")
        cmd = [sys.executable, VALIDATOR, "--run-dir", run_dir,
               "--model", manifest["model"],
               "--workload", manifest["workload"],
               "--context", manifest["context"],
               "--target-va", hex(int(va)),
               "--target-mode", manifest.get("target_mode", "") or "",
               "--run-id", manifest.get("run_id") or os.path.basename(run_dir)]
        ctrl = manifest.get("control_run")
        if ctrl:
            cmd += ["--control-run", ctrl]
        out_json = os.path.join(run_dir, "Validation", "verdict.json")
        out_md = os.path.join(run_dir, "Validation", "verdict.md")
        if args.dry_run:
            rows.append((key, manifest.get("run_id"), "DRY_RUN", ""))
            continue
        _backup(run_dir)
        cmd += ["--report-json", out_json, "--report-md", out_md]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print("FAIL", key, proc.stderr[-500:], file=sys.stderr)
            return 3
        with open(os.path.join(run_dir, "Validation",
                               "validator_stdout.log"), "w") as fh:
            fh.write(proc.stdout)
        d = _read_json(out_json)
        rows.append((key, manifest.get("run_id"),
                     d.get("TerminalState"),
                     "%s/%s/%s/%s" % (d.get("ActivationStatus"),
                                      d.get("FaultConsumptionStatus"),
                                      d.get("PropagationStatus"),
                                      d.get("TraceCompleteness"))))
    for key, run, terminal, status in rows:
        print("%-8s %-22s %-18s %s" % (key, run, terminal, status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
