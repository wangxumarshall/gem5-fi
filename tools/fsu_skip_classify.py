#!/usr/bin/env python3
"""Classify pytest skips for the FSU gates.

Why this exists
---------------
A green ``passed`` count says nothing about a test that was skipped.  This tool
turns a pytest JUnit report into an explicit table of

    nodeid | skip reason (verbatim) | category | core gate? | status

and marks every skipped CORE gate as ``BLOCKED``.  It never converts a skip
into a pass and never counts a skipped capability as verified.

Usage
-----
    # Run pytest first (no gem5 needed), then classify:
    python3 -m pytest tests/ --ignore=tests/test_lsu_r6_reconcile_realroot.py \
        --junitxml=/tmp/pytest.xml -q
    python3 tools/fsu_skip_classify.py --junit /tmp/pytest.xml

    # Or let the tool run pytest itself (args after --pytest-args):
    python3 tools/fsu_skip_classify.py \
        --pytest-args "tests/test_chaos_fsu_fq08c_gate_audit.py tests/test_chaos_fsu_fp08_reason_audit.py"

    # Machine-readable output / fail when a core gate is blocked:
    python3 tools/fsu_skip_classify.py --junit /tmp/pytest.xml --json
    python3 tools/fsu_skip_classify.py --junit /tmp/pytest.xml --fail-on-blocked

Categories
----------
    environment      evidence/toolchain not present on this host
    unimplemented    capability/counter/log not implemented yet
    manual           needs a manual/hardware integration step
    other            intentional scope filter or not naturally reachable

This is a reporting tool only; it does not modify any test or injector.
"""
import argparse
import json
import shlex
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# If any of these are skipped, the corresponding capability is NOT verified.
# Keep this list explicit: "all FSU tests" is too broad to mean a gate.
CORE_GATE_PATTERNS = (
    # FQ08-c positive activation / generation / stale-event safety.
    "test_positive_fire_evidence",
    "test_generation_reuse_evidence",
    "test_fire_target_state_count_is_not_observable_yet",
    # FP08 reason-level conservation and fail-closed combinations.
    "test_per_reason_counters_are_not_implemented_yet",
    "test_real_rounding_gate_reason_partition",
    "test_unguarded_combinations_fail_closed",
    # Existing FSU gate suites: if they ever skip, that is a blocked gate.
    "test_fsu_fr01_fr02_gate",
    "test_fsu_f5_w1_gate",
    "test_fsu_w6_gate",
    "test_fsu_suite_f5_gate",
    "test_fsu_fr03_suite",
)

# Identity mismatch cannot happen naturally (seqNum/threadNumber are
# immutable); its skip is design-level N/A, not a blocked runtime gate.
NON_RUNTIME_EVIDENCE = (
    "test_identity_mismatch_evidence",
)


def classify_reason(reason, nodeid):
    text = (reason or "").lower()
    if "to be implemented (placeholder)" in text:
        return "unimplemented"
    if "blocked" in text:
        # BLOCKED says why, but not what kind; use the evidence wording.
        if "no real gem5 log" in text or "real gem5" in text:
            return "environment"
        return "other"
    if ("not present" in text or "not available" in text or
            "不存在" in reason or "缺失" in reason or
            "evidence tree" in text or "evidence root" in text):
        return "environment"
    if "not a suite seed" in text:
        return "other"
    if "legacy" in text and "seed_plan" in text:
        return "unimplemented"
    if "manual" in text or "hardware" in text:
        return "manual"
    return "other"


def is_core_gate(nodeid):
    return any(p in nodeid for p in CORE_GATE_PATTERNS)


def is_non_runtime(nodeid):
    return any(p in nodeid for p in NON_RUNTIME_EVIDENCE)


def parse_junit(path):
    tree = ET.parse(path)
    rows = []
    totals = {"passed": 0, "skipped": 0, "failed": 0, "error": 0}
    for tc in tree.iter("testcase"):
        name = tc.get("name", "")
        classname = tc.get("classname", "")
        # pytest junit: classname = package.Class, name = test[params]
        # Build a nodeid-like identifier.
        if classname.startswith("tests."):
            parts = classname[len("tests."):].split(".")
            mod = [p for p in parts if not p[:1].isupper()]
            cls = [p for p in parts if p[:1].isupper()]
            nodeid = "tests/" + "/".join(mod) + ".py"
            if cls:
                nodeid += "::" + "::".join(cls)
            nodeid += "::" + name
        elif classname:
            nodeid = classname.replace(".", "/") + ".py::" + name
        else:
            nodeid = name
        skipped = tc.findall("skipped")
        failed = tc.findall("failure")
        error = tc.findall("error")
        if skipped:
            totals["skipped"] += 1
            reason = skipped[0].get("message") or (skipped[0].text or "")
            rows.append({"nodeid": nodeid, "reason": reason.strip()})
        elif failed:
            totals["failed"] += 1
        elif error:
            totals["error"] += 1
        else:
            totals["passed"] += 1
    return rows, totals


def run_pytest(args):
    fd, path = tempfile.mkstemp(prefix="fsu_skips_", suffix=".xml")
    Path(path).unlink(missing_ok=True)
    cmd = [sys.executable, "-m", "pytest", "-q",
           "--junitxml=" + path] + args
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if not Path(path).is_file():
        sys.stderr.write(proc.stdout + "\n" + proc.stderr)
        raise SystemExit("pytest produced no JUnit report (rc=%d)" % proc.returncode)
    return path, proc


def classify(rows):
    out = []
    for row in rows:
        nodeid = row["nodeid"]
        cat = classify_reason(row["reason"], nodeid)
        core = is_core_gate(nodeid)
        if is_non_runtime(nodeid):
            status = "N/A (host-only / not naturally reachable)"
            core = False
        elif core:
            status = "BLOCKED"
        else:
            status = "skip (not a core gate)"
        out.append({"nodeid": nodeid, "reason": row["reason"],
                    "category": cat, "core_gate": core, "status": status})
    return out


def print_table(rows, totals):
    print("nodeid | skip reason | category | core gate? | status")
    print("---|---|---|---|---")
    for r in rows:
        reason = " ".join(r["reason"].split())
        print("%s | %s | %s | %s | %s" % (
            r["nodeid"], reason, r["category"],
            "YES" if r["core_gate"] else "no", r["status"]))
    print()
    print("totals: %d passed, %d skipped, %d failed, %d errors" % (
        totals["passed"], totals["skipped"], totals["failed"],
        totals["error"]))
    blocked = [r for r in rows if r["status"] == "BLOCKED"]
    print("core gates BLOCKED: %d" % len(blocked))
    for r in blocked:
        print("  BLOCKED %s" % r["nodeid"])
    counts = {}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    print("by category: " + ", ".join(
        "%s=%d" % (k, counts[k]) for k in sorted(counts)))
    return blocked


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--junit", help="pytest JUnit XML to classify")
    ap.add_argument("--pytest-args",
                    help="run pytest with these arguments, then classify")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--fail-on-blocked", action="store_true",
                    help="exit 2 when a core gate is skipped")
    args = ap.parse_args(argv)

    if not args.junit and not args.pytest_args:
        ap.error("give --junit or --pytest-args")
    tmp = None
    if args.pytest_args:
        tmp, proc = run_pytest(shlex.split(args.pytest_args))
        if proc.returncode not in (0, 1):
            sys.stderr.write(proc.stdout + "\n" + proc.stderr)
        junit = tmp
    else:
        junit = args.junit

    rows, totals = parse_junit(junit)
    classified = classify(rows)
    if args.json:
        print(json.dumps({"totals": totals, "skips": classified},
                         indent=2, ensure_ascii=False))
        blocked = [r for r in classified if r["status"] == "BLOCKED"]
    else:
        blocked = print_table(classified, totals)
    if tmp:
        Path(tmp).unlink(missing_ok=True)
    if args.fail_on_blocked and blocked:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
