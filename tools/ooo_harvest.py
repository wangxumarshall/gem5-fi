#!/usr/bin/env python3
"""ooo-track results harvester (M3/M4 plan Task 13) — unified CSV.

Harvestes the ooo track's campaign artifacts into one CSV so the LSU grid
and the ooo formal corpus can be analyzed/presented together (paper-scale
synthesis). HONEST SOURCE NOTE (verified 2026-09-26): the ooo run dirs
under THIS repo's runs/ are empty shells (0 files); the real artifacts live
in the sister repo /home/sdc/gem5-fi/runs/ (e.g. prf_formal_cholesky: 770
files = 384 manifests + results.jsonl). --runs-root points there.

Artifact shape (sampled):
  <campaign>/cNNNN/results.jsonl  {"manifest": "...yaml", "classification":
                                   "Crash|SDC|Masked|Hang|Inactive|
                                    SimulatorError|...", "faults_injected",
                                   "exit", "timed_out"}
  <campaign>/cNNNN/<campaign>-cNNNN-rNNNN.yaml
                                 campaign_id / platform.mode (SE|FS) /
                                 config_family / target.component /
                                 fault.model / trigger
Empty campaign dirs (cleaned runs, e.g. some pwf_v13_*) are skipped and
COUNTED — never silently.

Output columns: campaign, unit(component), fault_model, mode(SE/FS),
config_family, n_reps, counts per class, n_valid, P_SDC, P_DUE, wilson_lo,
wilson_hi, source_run. n_valid excludes Inactive/SimulatorError per the
ooo track's convention; P_* denominators = n_valid (same track convention;
NOT mixed with the LSU track's activated denominator — the CSV carries a
`denominator` column to keep the two tracks' metrics explicitly separate).

Usage: python3 tools/ooo_harvest.py [--runs-root /home/sdc/gem5-fi/runs] \
          [--out artifacts/ooo-harvest/ooo-results.csv]
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wilson import wilson_ci  # repo's single Wilson impl

VALID_CLASSES = {"SDC", "Crash", "Hang", "Masked", "DetectedContained",
                 "Corrected", "Latent"}


def load_manifest(path):
    """Read a rep manifest (pyyaml — same dependency the backfill tool
    already requires)."""
    import yaml
    return yaml.safe_load(open(path, encoding="utf-8"))


def flat(d, *keys, default=""):
    for k in keys:
        d = d.get(k, {}) if isinstance(d, dict) else {}
        if not isinstance(d, dict) and not isinstance(d, str):
            return d
    return d if d != {} else default


def harvest_campaign(camp_dir):
    cells = sorted(d for d in os.listdir(camp_dir)
                   if re.fullmatch(r"c\d{4}", d))
    if not cells:
        return None
    results_path = os.path.join(camp_dir, cells[0], "results.jsonl")
    if not os.path.exists(results_path):
        return None
    # metadata from the first rep's manifest
    mf = None
    c0 = os.path.join(camp_dir, cells[0])
    for f in sorted(os.listdir(c0)):
        if f.endswith(".yaml"):
            mf = load_manifest(os.path.join(c0, f))
            break
    counts, n_reps, n_inject0 = Counter(), 0, 0
    for cd in cells:
        rp = os.path.join(camp_dir, cd, "results.jsonl")
        if not os.path.exists(rp):
            continue
        for line in open(rp, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            n_reps += 1
            counts[r.get("classification", "?")] += 1
            if not r.get("faults_injected"):
                n_inject0 += 1
    if n_reps == 0:
        return None
    return mf, counts, n_reps, n_inject0, cells


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-root", default="/home/sdc/gem5-fi/runs")
    ap.add_argument("--out",
                    default="artifacts/ooo-harvest/ooo-results.csv")
    a = ap.parse_args()

    rows, skipped_empty, skipped_noresults = [], 0, 0
    for name in sorted(os.listdir(a.runs_root)):
        camp = os.path.join(a.runs_root, name)
        if not os.path.isdir(camp) or name in ("lsu",):
            continue
        got = harvest_campaign(camp)
        if got is None:
            if os.path.isdir(camp) and not any(
                    re.fullmatch(r"c\d{4}", d) for d in os.listdir(camp)):
                skipped_empty += 1
            else:
                skipped_noresults += 1
            continue
        mf, counts, n_reps, n_inject0, cells = got
        n_valid = sum(v for k, v in counts.items() if k in VALID_CLASSES)
        sdc, due = counts.get("SDC", 0), counts.get("Crash", 0) + \
            counts.get("Hang", 0)
        lo, hi, _p = wilson_ci(sdc, n_valid) if n_valid else (0.0, 0.0, 0.0)
        workload = name  # campaign_id encodes workload (e.g. *_cholesky)
        m = re.search(r"_([a-z0-9]+?)(?:_formal|_pilot|$)", name)
        if m:
            workload = m.group(1)
        rows.append({
            "campaign": name,
            "unit": flat(mf, "target", "component") if mf else "",
            "fault_model": flat(mf, "fault", "model") if mf else "",
            "mode": flat(mf, "platform", "mode") if mf else "",
            "config_family": flat(mf, "platform", "config_family") if mf else "",
            "workload": workload,
            "n_reps": n_reps, "n_valid": n_valid,
            "n_inactive": counts.get("Inactive", 0),
            "n_simerror": counts.get("SimulatorError", 0),
            "n_sdc": sdc, "n_crash": counts.get("Crash", 0),
            "n_hang": counts.get("Hang", 0),
            "n_masked": counts.get("Masked", 0),
            "n_inject0": n_inject0,
            "P_SDC": "%.4f" % (sdc / n_valid) if n_valid else "n/a",
            "P_DUE": "%.4f" % (due / n_valid) if n_valid else "n/a",
            "wilson_lo": "%.4f" % lo, "wilson_hi": "%.4f" % hi,
            "denominator": "n_valid(ooo)",
            "source_run": os.path.join(a.runs_root, name),
        })

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("harvested %d campaign(s) -> %s" % (len(rows), a.out))
    print("skipped: %d empty dir(s), %d without results.jsonl"
          % (skipped_empty, skipped_noresults))
    # honest census of classes encountered
    allc = Counter()
    for r in rows:
        for k in ("n_sdc", "n_crash", "n_hang", "n_masked", "n_inactive",
                  "n_simerror"):
            allc[k] += r[k]
    print("class totals:", dict(allc))


if __name__ == "__main__":
    main()
