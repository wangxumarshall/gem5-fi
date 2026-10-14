#!/usr/bin/env python3
"""[OOO][P1] commit_diff.py --seq-range windowed-diff test (plan Task 3).

Pins:
  1. legacy path: without the flag the JSON has NO seq_range key and the
     verdict/classification is exactly the pre-change behavior;
  2. --seq-range LO:HI restricts the comparison to seq in [LO, HI]: a run
     whose only divergence is OUTSIDE the window reads no_divergence IN THE
     WINDOW, with an explicit coverage note (windowed no_divergence is
     never presented as whole-trace evidence);
  3. a window covering the divergence reproduces the full-diff verdict;
  4. a malformed range (LO > HI) exits 2 (argparse misuse).

Run: python3 tools/tests/test_commit_diff_seqrange.py
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CD = os.path.join(REPO, "tools", "commit_diff.py")

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def tline(seq, tick, pc, val):
    """One pinned-format trace line: one dest register quad."""
    return (f"{seq},0,{tick},{pc},add,1,1,2,80,{val}")


def build_traces(td):
    ref_lines = [tline(s, 100 + s, "4194304", "0000000000000000")
                 for s in range(10)]
    run_lines = [tline(s, 100 + s, "4194304", "0000000000000000")
                 for s in range(10)]
    # the ONLY divergence: run's seq-7 dest val differs (class ⑤数据损坏)
    run_lines[7] = tline(7, 107, "4194304", "deadbeefdeadbeef")
    ref = os.path.join(td, "ref.csv")
    run = os.path.join(td, "run.csv")
    with open(ref, "w") as f:
        f.write("\n".join(ref_lines) + "\n")
    with open(run, "w") as f:
        f.write("\n".join(run_lines) + "\n")
    return ref, run


def run_cd(ref, run, extra, out_json):
    cmd = [sys.executable, CD, "--ref", ref, "--run", run,
           "--json", out_json] + extra
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    data = None
    if os.path.exists(out_json):
        with open(out_json) as f:
            data = json.load(f)
    return r, data


def main():
    with tempfile.TemporaryDirectory(prefix="seqrange-") as td:
        ref, run = build_traces(td)
        jpath = os.path.join(td, "out.json")

        # 1) legacy: no flag -> byte-for-byte legacy semantics, no new key
        r1, d1 = run_cd(ref, run, [], os.path.join(td, "j1.json"))
        check("legacy-exit0", r1.returncode == 0, r1.stderr[-200:])
        check("legacy-diverged", d1 and d1["verdict"] == "diverged")
        check("legacy-primary", d1 and d1["primary_class"] == "data_corruption")
        check("legacy-latency", d1 and d1["latency_seq"] == 7)
        check("legacy-no-seqrange-key", d1 and "seq_range" not in d1)
        check("legacy-no-coverage-note", d1 and "coverage_note" not in d1)

        # 2) window excludes the divergence -> no_divergence IN WINDOW + note
        r2, d2 = run_cd(ref, run, ["--seq-range", "0:5"],
                        os.path.join(td, "j2.json"))
        check("win-exit0", r2.returncode == 0, r2.stderr[-200:])
        check("win-no-divergence", d2 and d2["verdict"] == "no_divergence",
              f"verdict={d2 and d2['verdict']}")
        check("win-aligned-6", d2 and d2["aligned_pairs"] == 6,
              f"aligned={d2 and d2['aligned_pairs']}")
        check("win-seqrange-recorded",
              d2 and d2.get("seq_range") == {"lo": 0, "hi": 5})
        check("win-coverage-note",
              d2 and "coverage_note" in d2 and "0" in d2["coverage_note"]
              and "unobserved" in d2["coverage_note"],
              f"note={d2 and d2.get('coverage_note')}")

        # 3) window covering the divergence == the full-diff verdict
        r3, d3 = run_cd(ref, run, ["--seq-range", "0:9"],
                        os.path.join(td, "j3.json"))
        check("winfull-diverged", d3 and d3["verdict"] == "diverged")
        check("winfull-primary",
              d3 and d3["primary_class"] == "data_corruption")
        check("winfull-latency", d3 and d3["latency_seq"] == 7)
        check("winfull-aligned-10", d3 and d3["aligned_pairs"] == 10)

        # 4) malformed range -> argparse exit 2
        r4, _ = run_cd(ref, run, ["--seq-range", "5:1"],
                       os.path.join(td, "j4.json"))
        check("bad-range-exit2", r4.returncode == 2,
              f"rc={r4.returncode}")

    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
