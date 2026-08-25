#!/usr/bin/env python3
"""
P7: read-trace heavy-tail / propagation-closure analyzer.

Parses a CHAOSPhysReg fault_injections.log and classifies every injected
fault into the 4-class propagation taxonomy from EXPERIMENT_DESIGN.md §2.1:

    Benign   : reads_before_overwrite == 0  (injected value never consumed)
    Masked   : reads > 0 but kernel output unchanged (logic-masked)
    SDC      : reads > 0 AND kernel output diff (silent corruption)  ★
    Crash    : simulation aborted (panic / SEGV / non-clean exit)

And tests H3 (state-leakage signature): the reads_before_overwrite
distribution should be heavy-tailed / bimodal — a few active cells with high
read counts (the SDC-producing tail), a large Benign mass at reads=0.

This is the closure-side counterpart to bit_spectrum.py (P6): P6 profiles
the bit-position signature of corruption; P7 profiles the propagation
probability. Together they answer "did it propagate?" (P7) + "what did it
look like?" (P6) for every injected fault — the two axes H3/H4 need.

Usage:
  python3 read_trace_stats.py fault_injections.log --kernel-exit 0
      # --kernel-exit 0 = kernel exited cleanly (exit code 0); nonzero = Crash
  python3 read_trace_stats.py m5out/fault_injections.log --stdout run.stdout
      # parse run.stdout for "fails=" line to classify Masked vs SDC
"""
import argparse
import re
import sys
from pathlib import Path
from collections import Counter

INJ_RE = re.compile(r"Cycle:\s*(\d+).*PhysReg\[(\d+)\]\s*\(([^)]*)\).*FaultType:\s*(\w+)")
TRACE_RE = re.compile(r"ReadTracePoll:.*reads_before_overwrite=(\d+).*overwritten=(\d+)")
FINAL_RE = re.compile(r"ReadTraceFinal:.*reads_before_overwrite=(\d+).*overwritten=(\d+)")
FAILS_RE = re.compile(r"^iters=\d+\s+fails=(\d+)", re.M)
PANIC_RE = re.compile(r"panic|fatal|aborted|Page table fault", re.I)
EXIT_RE = re.compile(r"Exiting @ tick.*cause=([^\n]+)")

def parse_log(path):
    faults = []  # list of dicts
    # A fault's final reads is the LAST ReadTracePoll/Final line before the
    # next "Cycle:" injection line (or EOF).
    cur = None
    with open(path) as f:
        for line in f:
            m = INJ_RE.search(line)
            if m:
                if cur is not None:
                    faults.append(cur)
                cur = dict(cycle=int(m.group(1)), phys=int(m.group(2)),
                           liveness=m.group(3).strip(), fault=m.group(4),
                           reads=0, overwritten=False)
                continue
            m = TRACE_RE.search(line)
            if m and cur is not None:
                cur["reads"] = int(m.group(1))
                cur["overwritten"] = (int(m.group(2)) == 1)
                continue
            m = FINAL_RE.search(line)
            if m and cur is not None:
                cur["reads"] = int(m.group(1))
                cur["overwritten"] = (int(m.group(2)) == 1)
    if cur is not None:
        faults.append(cur)
    return faults

def classify(faults, kernel_fails, crashed):
    # Each fault: Benign / Masked / SDC / Crash(contextual)
    # Crash is a property of the whole run (one bad fault aborts the sim),
    # so we mark the highest-reads fault in a crashed run as the Crash
    # culprit and the rest by their reads.
    classes = Counter()
    for f in faults:
        if f["reads"] == 0:
            classes["Benign"] += 1
        else:
            classes["Masked"] += 1  # reads>0, output unchanged (default)
    if crashed:
        # the run crashed -> at least one fault propagated to a fault
        classes["Crash"] = 1
        classes["Masked"] = max(0, classes["Masked"] - 1)
    if kernel_fails > 0 and not crashed:
        # kernel detected output diff but sim didn't crash -> SDC
        classes["SDC"] = kernel_fails
    return classes

def heavy_tail_test(faults):
    reads = [f["reads"] for f in faults]
    n = len(reads)
    if n == 0:
        return None
    nz = [r for r in reads if r > 0]
    dist = Counter(reads)
    # bimodality: share at reads==0 vs reads>=k
    zero = dist.get(0,0)
    high = sum(c for r,c in dist.items() if r >= 4)
    return dict(n=n, nonzero=len(nz), zero=zero, high_read=high,
                max_read=max(reads), median_read=sorted(reads)[n//2],
                dist=dict(dist))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="fault_injections.log path")
    ap.add_argument("--stdout", default=None, help="run stdout file (for fails= / panic / Exiting)")
    ap.add_argument("--kernel-exit", type=int, default=None, help="kernel exit code (override)")
    args = ap.parse_args()

    faults = parse_log(args.log)
    if not faults:
        print("no fault injections parsed"); return
    crashed = False
    kernel_fails = 0
    if args.stdout and Path(args.stdout).exists():
        txt = Path(args.stdout).read_text()
        if PANIC_RE.search(txt):
            crashed = True
        m = FAILS_RE.search(txt)
        if m: kernel_fails = int(m.group(1))
    elif args.kernel_exit is not None:
        if args.kernel_exit != 0:
            # nonzero kernel exit but no panic text -> could be SDC (exit 1) or crash
            kernel_fails = 1 if args.kernel_exit == 1 else 0
            if args.kernel_exit > 1: crashed = True

    print(f"=== read-trace closure ({len(faults)} faults injected) ===")
    classes = classify(faults, kernel_fails, crashed)
    total = sum(classes.values())
    for c in ("Benign","Masked","SDC","Crash"):
        v = classes.get(c,0)
        print(f"  {c:7s}: {v:4d}  ({100*v/max(total,1):5.1f}%)")
    print(f"  run     : {'CRASHED' if crashed else 'clean'}  kernel_fails={kernel_fails}")

    ht = heavy_tail_test(faults)
    if ht:
        print(f"=== H3 heavy-tail test (reads_before_overwrite) ===")
        print(f"  n={ht['n']} nonzero_reads={ht['nonzero']} ({100*ht['nonzero']/ht['n']:.1f}%)  "
              f"max_read={ht['max_read']} median={ht['median_read']}")
        print(f"  reads==0 (Benign mass): {ht['zero']}  ({100*ht['zero']/ht['n']:.1f}%)")
        print(f"  reads>=4 (active tail): {ht['high_read']}  ({100*ht['high_read']/ht['n']:.1f}%)")
        # H3 prediction: heavy-tailed (few active high-read, large benign zero-mass)
        zero_share = ht['zero']/ht['n']
        if zero_share >= 0.5 and ht['max_read'] >= 4:
            print(f"  => heavy-tailed/bimodal (zero_share {zero_share:.0%}, max_read {ht['max_read']}) — "
                  f"consistent with H3 state-leakage signature")
        else:
            print(f"  => NOT heavy-tailed (needs more samples or different workload)")

if __name__ == "__main__":
    main()
