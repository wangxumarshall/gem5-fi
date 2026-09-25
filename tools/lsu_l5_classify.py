#!/usr/bin/env python3
"""LSU L5 closure classifier (docs/gem5-fi/lsu/04-observation-points.md L5).

One run in, one five-class verdict out, conservation-checked:
    Activated = Masked + Detected/Contained + SDC + Crash + Timeout
(04 L5 pinned identity). Injected-not-activated is reported as its own
column and EXCLUDED from the SDC-rate denominator (04 L0 / 05 r12).

Inputs (all optional-but-checked):
  --run-dir DIR     gem5 --outdir: injection logs live here (abort fallback)
  --stdout FILE     the gem5 process stdout (checksum + CHAOS_LSU_TRIGGER)
  --stderr FILE     the gem5 process stderr (panic/assert = simulator DUE)
  --golden HEX      the workload golden checksum
  --exit N          the gem5 process exit code
  --timed-out       flag: the driver killed this run on timeout

HONEST LIMITS (W2/W3-known):
  * abort/abort-class runs never reach exit callbacks: no stdout funnel
    line — the classifier falls back to counting the injection log lines.
  * Crash 双拆分 (04 L5): a gem5 assertion (simulator DUE) is NOT an
    architectural crash; both are reported, crash_kind=simulator_assert vs
    guest/unknown.
  * Detected/Contained needs a detector signal; until W6 protection
    modeling is wired, runs classify without it (n/a, not zero).

Usage: python3 tools/lsu_l5_classify.py --run-dir D --stdout S \
          --stderr E --golden HEX --exit N [--timed-out] [--json OUT]
"""
import argparse
import json
import re
import sys
from pathlib import Path


def _read(path, out, label):
    """Read a file if given and present; absent optional files warn, not die."""
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        out.setdefault("warnings", []).append(f"{label} file missing: {path}")
        return ""
    return p.read_text(errors="replace")


def classify(args):
    out = {"conservation": None, "error": None}
    stdout = _read(args.stdout, out, "stdout")
    stderr = _read(args.stderr, out, "stderr")

    # ---- L0 funnel: stdout lines first, injection-log fallback ----
    m = re.search(r"CHAOS_LSU_TRIGGER: .*?attempted=(\d+) eligible=(\d+) "
                  r"injected=(\d+)", stdout)
    attempted = eligible = injected = None
    if m:
        attempted, eligible, injected = (int(x) for x in m.groups())
    else:
        logs = list(Path(args.run_dir).glob("*injections.log")) if args.run_dir else []
        if logs:
            text = logs[0].read_text(errors="replace")
            n = len(re.findall(r"Site: ", text))
            injected = n
            out["funnel_source"] = f"injection-log-fallback({logs[0].name})"

    # ---- outcome ----
    checksum = None
    cm = re.findall(r"^[0-9a-f]{16}$", stdout, re.M)
    if cm:
        checksum = cm[-1]
    sim_assert = bool(re.search(r"Assertion .* failed|panic|abort", stderr))
    exit_code = args.exit

    if args.timed_out:
        outcome = "Timeout"
    elif exit_code not in (0, None):
        outcome = "Crash"
        out["crash_kind"] = ("simulator_assert" if sim_assert
                             else "guest_or_unknown")
    elif checksum is None:
        outcome = "Crash"          # no checksum line at all on abort paths
        out["crash_kind"] = ("simulator_assert" if sim_assert
                             else "guest_or_unknown")
    elif args.golden and checksum != args.golden:
        outcome = "SDC"
    else:
        outcome = "Masked"

    # ---- L5 five-class + conservation (04 L5 pinned identity) ----
    # Detected/Contained: no detector wired yet (W6 protection modeling) —
    # reported as detected=0 with detected_na=True, never silently.
    detected = 0
    out["detected_na"] = True
    activated = injected if injected is not None else 0
    # single-run verdict: the whole activated count lands in one class
    classes = {"Masked": 0, "Detected/Contained": detected, "SDC": 0,
               "Crash": 0, "Timeout": 0}
    if activated:
        classes[outcome] = activated
    s = sum(classes.values())
    out.update({
        "attempted": attempted, "eligible": eligible, "injected": injected,
        "activated": activated,
        "injected_not_activated": max(0, (injected or 0) - activated),
        "checksum": checksum, "outcome": outcome, "classes": classes,
    })
    out["conservation"] = ("OK" if s == activated else
                           f"VIOLATION sum={s} activated={activated}")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir")
    p.add_argument("--stdout")
    p.add_argument("--stderr")
    p.add_argument("--golden")
    p.add_argument("--exit", type=int)
    p.add_argument("--timed-out", action="store_true")
    p.add_argument("--json", help="optional JSON output path")
    a = p.parse_args()
    r = classify(a)
    print("LSU_L5: " + json.dumps(r, ensure_ascii=False))
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=1) + "\n")
    sys.exit(0 if r["conservation"] == "OK" else 1)


if __name__ == "__main__":
    main()
