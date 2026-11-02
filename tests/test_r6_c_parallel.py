#!/usr/bin/env python3
"""R6-C queue tests: allocation integrity + authoritative scope pin."""
import csv
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = "/home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv"
SCRIPT = os.path.join(ROOT, "tools", "r6_c_parallel.sh")


def _script_runids():
    text = open(SCRIPT).read()
    m = re.search(r'RUNIDS="\$\{R6C_RUNIDS:-(.*?)\}"', text)
    assert m, "RUNIDS default not found"
    return m.group(1).split(",")


def test_dry_run_allocates_93_unique():
    out = subprocess.run(["bash", SCRIPT, "--dry-run"],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "ALLOCATION_OK" in out.stdout
    assert "tasks=93 unique=93 dup=0 runids=31" in out.stdout


def test_scope_matches_authoritative_matrix():
    """The queue's RunID list must equal the matrix's runnable non-F6 C set."""
    rows = list(csv.DictReader(open(MATRIX, encoding="utf-8-sig")))
    want = [r["RunID"] for r in rows
            if r["RunID"].startswith("C")
            and r["记录状态"] == "试跑"
            and r["频率"] != "F6"]
    got = _script_runids()
    assert got == want, (len(got), len(want), set(got) ^ set(want))
    assert len(set(got)) == len(got) == 31
