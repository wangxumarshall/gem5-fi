#!/usr/bin/env python3
"""Verify the MMU final results archive against its recorded SHA256 values.

Checks:
  1. every file in MMU_Final_Results_SHA256.txt exists and hashes correctly;
  2. each of the 40 formal sample directories matches its own SHA256SUMS;
  3. the 28 control oracles match Control_Map.csv;
  4. the 10 repeat traces match trace_index.csv.

Exit code 0 iff every check passes.
"""
import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.normpath(os.path.join(HERE, "..", "results"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_manifest(problems):
    manifest = os.path.join(RESULTS, "MMU_Final_Results_SHA256.txt")
    if not os.path.isfile(manifest):
        problems.append("missing manifest: %s" % manifest)
        return 0
    count = 0
    for line in open(manifest):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        repo_root = os.path.dirname(os.path.dirname(RESULTS))
        path = os.path.join(repo_root, rel)
        count += 1
        if not os.path.isfile(path):
            problems.append("missing: %s" % rel)
        elif sha256(path) != digest:
            problems.append("hash mismatch: %s" % rel)
    return count


def verify_samples(problems):
    root = os.path.join(RESULTS, "formal", "samples")
    if not os.path.isdir(root):
        problems.append("missing sample root: %s" % root)
        return 0
    samples = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    if len(samples) != 40:
        problems.append("expected 40 sample dirs, found %d" % len(samples))
    for sid in samples:
        sumfile = os.path.join(root, sid, "SHA256", "SHA256SUMS.txt")
        if not os.path.isfile(sumfile):
            problems.append("missing SHA256SUMS: %s" % sid)
            continue
        for line in open(sumfile):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            digest, _, rel = line.partition("  ")
            if rel == "disk.img" or rel.startswith(("gem5:", "source:", "workload:")):
                continue
            path = os.path.join(root, sid, rel)
            if not os.path.isfile(path):
                problems.append("missing: %s/%s" % (sid, rel))
            elif sha256(path) != digest:
                problems.append("hash mismatch: %s/%s" % (sid, rel))
    return len(samples)


def verify_controls(problems):
    root = os.path.join(RESULTS, "formal", "controls")
    audit = os.path.join(RESULTS, "formal", "audit", "Control_Map.csv")
    if not os.path.isfile(audit):
        problems.append("missing Control_Map.csv")
        return 0
    seen = {}
    for row in csv.DictReader(open(audit)):
        run = row["ControlRunDir"]
        name = os.path.basename(run)
        if name in seen:
            continue
        seen[name] = 1
        rel = os.path.relpath(row["ControlOraclePath"], run)
        path = os.path.join(root, name, rel)
        if not os.path.isfile(path):
            problems.append("missing control oracle: %s" % path)
        elif sha256(path) != row["ControlOracleSHA256Recorded"]:
            problems.append("control oracle hash mismatch: %s" % name)
    if len(seen) != 28:
        problems.append("expected 28 controls, found %d" % len(seen))
    return len(seen)


def verify_repeats(problems):
    index = os.path.join(RESULTS, "repeatability", "analysis", "repeat_campaign",
                         "trace_index.csv")
    if not os.path.isfile(index):
        problems.append("missing repeat trace index")
        return 0
    rows = list(csv.DictReader(open(index)))
    for row in rows:
        rid = row["RepeatRunID"]
        path = os.path.join(RESULTS, "repeatability", "repeats", rid,
                            "outdir", "prop_evt.txt.gz")
        if not os.path.isfile(path):
            problems.append("missing repeat trace: %s" % rid)
        elif sha256(path) != row["RepeatTraceSHA256"]:
            problems.append("repeat trace hash mismatch: %s" % rid)
    if len(rows) != 10:
        problems.append("expected 10 repeat traces, found %d" % len(rows))
    return len(rows)


def main():
    quiet = "--quiet" in sys.argv
    problems = []
    nfiles = verify_manifest(problems)
    nsamples = verify_samples(problems)
    ncontrols = verify_controls(problems)
    nrepeats = verify_repeats(problems)
    if not quiet:
        print("manifest files : %d" % nfiles)
        print("formal samples : %d" % nsamples)
        print("controls       : %d" % ncontrols)
        print("repeat traces  : %d" % nrepeats)
    if problems:
        print("MMU_ARCHIVE_INTEGRITY=FAIL (%d problem(s))" % len(problems))
        for p in problems[:50]:
            print("  -", p)
        return 1
    print("MMU_ARCHIVE_INTEGRITY=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
