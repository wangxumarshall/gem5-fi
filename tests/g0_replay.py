#!/usr/bin/env python3
"""G0 replay-consistency test (plan gate G0: 20/20 field-identical replay).

Runs the same CHAOSReg single-bit-flip injection 20 times with an identical
fixed seed and asserts the fault_injections.log is byte-identical across all
20 runs. Per plan §4 G0 exit: "same binary/config/seed/manifest must hit the
same trigger point, target field, and bit mask — 20/20 identical replay."

This tests CHAOSReg (rng_seed) reproducibility end-to-end, including the
rand()%2 -> rng() class-selection fix.

Usage: python3 tests/g0_replay.py <gem5.opt> <arm_chaos.py> <reg_chain binary>
"""
import hashlib, os, subprocess, sys, tempfile

if len(sys.argv) != 4:
    sys.exit("usage: g0_replay.py <gem5.opt> <arm_chaos.py> <reg_chain>")
g5, cfg, binary = sys.argv[1], sys.argv[2], sys.argv[3]

def run_once(tag):
    outdir = tempfile.mkdtemp(prefix=f"g0-{tag}-")
    cmd = [g5, "--quiet", f"--outdir={outdir}", cfg,
           "--cmd", binary, "--cpu", "O3", "--chaos_reg",
           "--probability=1.0", "--first_clock=100000",
           "--max_faults=1", "--rng_seed=20260825",
           "--fault_type=bit_flip", "--bits_to_change=1",
           "--reg_class=integer"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
    if r.returncode != 0:
        return None, f"gem5 exit {r.returncode}: {r.stderr[-300:]}"
    logp = os.path.join(outdir, "fault_injections.log")
    if not os.path.exists(logp):
        return None, "no fault_injections.log"
    with open(logp) as f:
        log = f.read()
    return hashlib.sha256(log.encode()).hexdigest(), log.strip()

hashes = []
first_log = None
for i in range(20):
    h, log = run_once(i)
    if h is None:
        print(f"  run {i}: FAIL — {log}")
        sys.exit(1)
    hashes.append(h)
    if first_log is None:
        first_log = log
    print(f"  run {i}: sha256={h[:16]}... log='{log[:80]}...'")

print()
unique = set(hashes)
print(f"unique hashes: {len(unique)} / 20 runs")
if len(unique) == 1:
    print(f"G0 PASS: 20/20 field-identical replay.")
    print(f"  canonical log: {first_log}")
    sys.exit(0)
else:
    print(f"G0 FAIL: {len(unique)} distinct logs — NOT reproducible.")
    sys.exit(1)
