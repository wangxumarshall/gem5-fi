#!/usr/bin/env python3
"""Quarantine / feedback loop (paper section 2.6).

Reads checker results from the fleet database, groups mismatches by
(snapshot, core), and re-runs them to confirm reproducibility.  Confirmed
findings are recorded in the quarantine table and copied into the corpus found/
directory (snapshots that expose a defect are kept regardless of coverage).

The production rule is "reproduce on the same core over multiple days".  On a
single machine we use repeated independent runs as the reproducibility test;
that difference is documented and is not presented as a real hardware finding.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_mismatches(run_dir: str):
    path = os.path.join(run_dir, "mismatches.jsonl")
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="work/fleet/results.db")
    ap.add_argument("--player", default=os.path.join(ROOT, "bin", "sf_player"))
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--min-hits", type=int, default=1)
    ap.add_argument("--inject", default="")
    ap.add_argument("--found", default="work/fleet/found")
    ap.add_argument("--out", default="work/fleet/quarantine.json")
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    rows = db.execute(
        "SELECT run_dir, cores FROM runs WHERE mismatches > 0").fetchall()
    groups = defaultdict(lambda: {"hits": 0, "runs": set()})
    for run_dir, cores in rows:
        for item in load_mismatches(run_dir):
            snap = item.get("snapshot")
            core = item.get("core")
            if not snap or snap == "<batch>":
                continue
            key = (snap, int(core))
            groups[key]["hits"] += 1
            groups[key]["runs"].add(run_dir)

    os.makedirs(args.found, exist_ok=True)
    results = []
    confirmed = 0
    for (snap, core), info in sorted(groups.items()):
        if info["hits"] < args.min_hits:
            continue
        cmd = [args.player, "--snapshot", snap, "--core", str(core),
               "--repeat", str(args.repeat)]
        if args.inject:
            cmd += ["--inject", args.inject]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        mismatches = proc.stdout.count('"match":false')
        ok = mismatches == args.repeat
        if ok:
            confirmed += 1
            base = os.path.basename(snap)
            dst = os.path.join(args.found, base)
            try:
                with open(snap, "rb") as src, open(dst, "wb") as out:
                    out.write(src.read())
            except OSError:
                pass
        db.execute(
            """INSERT INTO quarantine(snapshot, core, hits, last_seen,
                                      confirmed, details)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(snapshot, core) DO UPDATE SET
                 hits=excluded.hits, last_seen=excluded.last_seen,
                 confirmed=excluded.confirmed, details=excluded.details""",
            (snap, core, info["hits"], 0.0 if not info["runs"] else max(
                os.path.getmtime(r) for r in info["runs"] if os.path.exists(r)),
             1 if ok else 0,
             json.dumps({"reruns": args.repeat, "mismatches": mismatches,
                         "runs": sorted(info["runs"]), "inject": args.inject})))
        results.append({"snapshot": snap, "core": core, "hits": info["hits"],
                        "reruns": args.repeat, "mismatches": mismatches,
                        "confirmed": ok})
        db.commit()

    db.close()
    with open(args.out, "w") as f:
        json.dump({"groups": len(results), "confirmed": confirmed,
                   "results": results}, f, indent=2)
    print(json.dumps({"groups": len(results), "confirmed": confirmed,
                      "out": args.out}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
