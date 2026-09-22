#!/usr/bin/env python3
"""event_density.py -- W0.3b event-density aggregator (OoO north star).

Aggregates per-run microarchitectural event counts from gem5 outdirs so that
W3.2 can back out how many runs are needed to cover >= 2000 target events
(docs/gem5-fi/ooo/02-frequency-and-sampling.md "事件覆盖计数";
06-implementation-plan.md W0.3 / W1.5 / W3.2).

Two data sources per run, both honest about absence (n/a, never fabricated):

  1. <run_dir>/stats.txt -- gem5 text stats. STATS_KEYS below are the MEASURED
     field names from real C3/O3 runs (gem5 v25.1.0.1 stdlib board naming,
     "board.processor.cores.core.*"; sources: /tmp/ooo_w03a/stats.txt and
     /tmp/ooo_w01_c3/stats.txt, cross-checked identical). A missing key is a
     loud failure (exit 1) naming the key.  NB: the W0 plan's expected names
     "system.cpu.rename.squashedInsts" and a bare "...committedInsts" do NOT
     exist in gem5 v25.1 -- the closest measured equivalents are used, and the
     whole squash family is reported so W3.2 can pick the right one:
       squash       = commit.commitSquashedInsts (in-flight insts removed by
                      squash, drained at commit -- the most complete count)
       squash_decode/..._disp/..._exec/..._bp = the same event seen at
                      decode/dispatch/execute/branch-predictor stages.
     "commits" is commit.committedInstType_0::total (the commit-stage count;
     no bare committedInsts stat exists in v25.1).

  2. an optional retained stdout capture (--stdout, e.g. the "> dir.out"
     shell redirect of a gem5 run) containing the CHAOS_PROBE summary line
     printed at end-of-sim by the CHAOSProbe SimObject (W0.3a). If a run has
     no CHAOS_PROBE line, its probe columns are reported as n/a -- never
     silently zeroed.

Usage:
  python3 tools/event_density.py --runs DIR [DIR ...] \
      [--stdout FILE [FILE ...]] [--json OUT.json]

--stdout files are attributed to runs by the sibling convention
(<run_dir>.out), or positionally when exactly one run and exactly one file
are given. A file that cannot be attributed to any run is a loud error;
a run without a file simply gets n/a probe columns.

Output: a markdown table (one row per run + MEAN/MIN/MAX rows) on stdout,
and the same content as machine-readable JSON via --json. stdlib only.
"""

import argparse
import json
import os
import re
import sys

# (stats.txt field, column label) -- MEASURED from real C3/O3 gem5 v25.1
# stats.txt files (/tmp/ooo_w03a, /tmp/ooo_w01_c3). Do not edit from memory:
# re-grep a real stats.txt first (e.g. grep -iE "mispred|squash|renamedInsts"
# <outdir>/stats.txt).
STATS_KEYS = [
    ("board.processor.cores.core.commit.branchMispredicts", "branch_mispred"),
    ("board.processor.cores.core.commit.commitSquashedInsts", "squash"),
    ("board.processor.cores.core.decode.squashedInsts", "squash_decode"),
    ("board.processor.cores.core.iew.dispSquashedInsts", "squash_disp"),
    ("board.processor.cores.core.numSquashedInsts", "squash_exec"),
    ("board.processor.cores.core.branchPred.squashes_0::total", "squash_bp"),
    ("board.processor.cores.core.rename.renamedInsts", "renamed_insts"),
    ("board.processor.cores.core.rename.renamedOperands", "rat_writes"),
    ("board.processor.cores.core.commit.committedInstType_0::total",
     "commits"),
    ("simInsts", "sim_insts"),
    ("simTicks", "sim_ticks"),
]

# CHAOS_PROBE summary-line fields (W0.3a CHAOSProbe end-of-sim print):
#   CHAOS_PROBE samples=<n> robOver80=<n> iqOver80=<n> flIntLe8=<n>
#                flFloatLe12=<n> flVecLe6=<n> robMax=<n> iqMax=<n>
#                flIntMin=<n> flFloatMin=<n> flVecMin=<n>
PROBE_KEYS = [
    "samples",
    "robOver80", "iqOver80",
    "flIntLe8", "flFloatLe12", "flVecLe6",
    "robMax", "iqMax",
    "flIntMin", "flFloatMin", "flVecMin",
]

PROBE_LINE_MARK = "CHAOS_PROBE"
KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(-?\d+)")


def die(msg):
    print("event_density.py: ERROR: %s" % msg, file=sys.stderr)
    sys.exit(1)


def parse_number(tok):
    """int(tok) if possible, else float(tok), else None (not a stat value)."""
    try:
        return int(tok)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        return None


def parse_stats_file(path):
    """Parse gem5 text stats.txt -> {name: number}.

    Duplicate names must carry the same value (a conflicting duplicate would
    mean multiple stat sections disagree -- ambiguous, fail loudly).
    """
    values = {}
    with open(path, "r", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            parts = line.split()
            if len(parts) < 2 or parts[0].startswith("#"):
                continue
            val = parse_number(parts[1])
            if val is None:
                continue  # e.g. "----- Begin Simulation Statistics -----"
            name = parts[0]
            if name in values and values[name] != val:
                die("%s:%d: stat '%s' appears twice with different values "
                    "(%r vs %r) -- ambiguous" % (path, lineno, name,
                                                 values[name], val))
            values[name] = val
    return values


def parse_probe_file(path):
    """Parse the CHAOS_PROBE summary line from a retained stdout capture.

    Returns {key: int} on success, or None when the file simply contains no
    CHAOS_PROBE line (the run was done without --chaos_probe -> reported as
    n/a upstream, not an error, and never fabricated). More than one line, or
    a line missing required keys, is a loud error.
    """
    hits = []
    with open(path, "r", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            if PROBE_LINE_MARK in line:
                hits.append((lineno, line.rstrip("\n")))
    if not hits:
        return None
    if len(hits) > 1:
        die("%s: %d CHAOS_PROBE lines found (first at line %d) -- expected "
            "exactly one" % (path, len(hits), hits[0][0]))
    lineno, line = hits[0]
    kvs = {}
    for m in KV_RE.finditer(line):
        kvs[m.group(1)] = int(m.group(2))
    missing = [k for k in PROBE_KEYS if k not in kvs]
    if missing:
        die("%s:%d: CHAOS_PROBE line is missing key(s): %s" %
            (path, lineno, missing))
    extra = sorted(set(kvs) - set(PROBE_KEYS))
    if extra:
        print("event_density.py: note: %s:%d: ignoring unknown CHAOS_PROBE "
              "key(s): %s" % (path, lineno, extra), file=sys.stderr)
    return {k: kvs[k] for k in PROBE_KEYS}


def attribute_stdout_files(run_dirs, stdout_files):
    """Map run dir -> attributed stdout file (missing runs -> no entry).

    Rules, in order:
      1. sibling convention: file path == run_dir + ".out"
      2. exactly one run AND exactly one file: pair them positionally
    Any file left unattributed is a loud error (likely a typo); runs without
    a file are fine (n/a probe columns).
    """
    assigned = {}
    stray = []
    for sf in stdout_files:
        match = None
        for d in run_dirs:
            if sf == d + ".out":
                match = d
                break
        if match is not None:
            if match in assigned:
                die("--stdout file %s: run %s already has a file (%s)" %
                    (sf, match, assigned[match]))
            assigned[match] = sf
        else:
            stray.append(sf)
    if stray:
        if len(run_dirs) == 1 and len(stray) == 1 and not assigned:
            assigned[run_dirs[0]] = stray[0]  # single run, single file
        else:
            die("--stdout file(s) cannot be attributed to any --runs dir "
                "(convention: <run_dir>.out): %s" % stray)
    return assigned


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Aggregate per-run event densities from gem5 outdirs "
                    "(stats.txt) plus optional CHAOS_PROBE stdout captures.")
    ap.add_argument("--runs", nargs="+", required=True, metavar="DIR",
                    help="gem5 outdir(s), each containing stats.txt")
    ap.add_argument("--stdout", nargs="+", default=[], metavar="FILE",
                    help="retained stdout capture(s) that contain the "
                         "CHAOS_PROBE line; attributed to runs by the "
                         "<run_dir>.out sibling convention (or positionally "
                         "when exactly one run and one file are given); "
                         "runs without a file get n/a probe columns")
    ap.add_argument("--json", metavar="OUT",
                    help="also write the same content as machine-readable "
                         "JSON to this path")
    args = ap.parse_args(argv)

    run_dirs = [os.path.abspath(d) for d in args.runs]
    if len(set(run_dirs)) != len(run_dirs):
        die("duplicate --runs entries: %s" % args.runs)
    for d in run_dirs:
        if not os.path.isdir(d):
            die("--runs entry is not a directory: %s" % d)

    stdout_files = [os.path.abspath(f) for f in args.stdout]
    for sf in stdout_files:
        if not os.path.isfile(sf):
            die("--stdout file does not exist: %s" % sf)
    stdout_of = attribute_stdout_files(run_dirs, stdout_files)

    labels = [label for _, label in STATS_KEYS]
    runs = []
    for d in run_dirs:
        stats_path = os.path.join(d, "stats.txt")
        if not os.path.isfile(stats_path):
            die("run dir %s has no stats.txt" % d)
        all_stats = parse_stats_file(stats_path)
        missing = [k for k, _ in STATS_KEYS if k not in all_stats]
        if missing:
            die("%s: missing required stat key(s): %s -- not a C3/O3 gem5 "
                "outdir? (STATS_KEYS in tools/event_density.py were measured "
                "from real runs; re-grep a real stats.txt before changing "
                "them)" % (stats_path, missing))
        stats = {label: all_stats[key] for key, label in STATS_KEYS}

        probe = None
        na_reason = None
        sf = stdout_of.get(d)
        if sf is None:
            na_reason = "no --stdout file given for this run"
        else:
            probe = parse_probe_file(sf)
            if probe is None:
                na_reason = ("no CHAOS_PROBE line in %s (run without "
                             "--chaos_probe?)" % sf)
        if na_reason is not None:
            print("event_density.py: note: %s: probe columns n/a -- %s" %
                  (d, na_reason), file=sys.stderr)
        runs.append({
            "dir": d,
            "stats_file": stats_path,
            "stdout_file": sf,
            "stats": stats,
            "probe": probe,
            "probe_na_reason": na_reason,
        })

    # Aggregates (MEAN/MIN/MAX). Probe columns aggregate over the runs that
    # have probe data; if none do, they stay n/a.
    def series(col):
        if col in labels:
            return [r["stats"][col] for r in runs]
        return [r["probe"][col] for r in runs if r["probe"] is not None]

    agg = {}
    for which in ("mean", "min", "max"):
        row = {}
        for col in labels + PROBE_KEYS:
            vals = series(col)
            if not vals:
                row[col] = None
            elif which == "mean":
                m = sum(vals) / len(vals)
                row[col] = int(m) if float(m).is_integer() else round(m, 2)
            else:
                row[col] = min(vals) if which == "min" else max(vals)
        agg[which] = row

    # Markdown table: one row per run, then MEAN/MIN/MAX.
    columns = ["run"] + labels + PROBE_KEYS
    row_labels = [os.path.basename(r["dir"]) for r in runs]
    if len(set(row_labels)) != len(row_labels):
        row_labels = [r["dir"] for r in runs]  # basename collision -> path
    body = []
    for rl, r in zip(row_labels, runs):
        cells = [rl]
        cells += [fmt(r["stats"][c]) for c in labels]
        cells += [fmt(r["probe"][c]) if r["probe"] is not None else "n/a"
                  for c in PROBE_KEYS]
        body.append(cells)
    tail = []
    for which in ("MEAN", "MIN", "MAX"):
        cells = [which]
        cells += [fmt(c) for c in (agg[which.lower()][k] for k in labels)]
        cells += [fmt(agg[which.lower()][k]) for k in PROBE_KEYS]
        tail.append(cells)
    table = [columns] + body + tail
    widths = [max(len(row[i]) for row in table) for i in range(len(columns))]
    lines = []
    for i, row in enumerate(table):
        lines.append("| " + " | ".join(
            row[j].ljust(widths[j]) if j == 0 else row[j].rjust(widths[j])
            for j in range(len(columns))) + " |")
        if i == 0:
            lines.append("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    print("\n".join(lines))

    if args.json:
        payload = {
            "tool": "tools/event_density.py",
            "stats_keys": {label: key for key, label in STATS_KEYS},
            "probe_keys": PROBE_KEYS,
            "runs": runs,
            "aggregate": {
                "n_runs": len(runs),
                "n_runs_with_probe":
                    sum(1 for r in runs if r["probe"] is not None),
                "mean": agg["mean"],
                "min": agg["min"],
                "max": agg["max"],
            },
        }
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        print("wrote %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
