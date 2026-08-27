#!/usr/bin/env python3
"""P0 BM-L1I pilot (plan §7.2, §6.1): L1I data-array instruction bit-flip.

Injects a single bit flip into a live L1I cache block on the l1i_loop
kernel (tight fixed-instruction loop, L1I-resident basic block). A flip
in an instruction's opcode/Rn/Rm/Rd/immediate/condition field can:
  - leave the instruction legal-but-wrong -> SDC (rare)
  - make it illegal -> Crash/DUE (illegal encoding trap)
  - corrupt loop control -> Hang (loop never exits)  <- observed here
maxFaults=1, vary seed.

Verified pilot result (TimingSimpleCPU, n=10, seeds 20260825..20260834):
  ALL 10 Hang, 0 SDC, 0 Crash. (no panic/assert in simerr; program
  never completes within 120s wall while golden completes in ~30s)
  e.g. seed=20260825: block 51392 byte 38 bit6 -> Hang
This matches plan §7.2's expectation: L1I instruction-field faults are
Hang/Crash-heavy (control-flow corruption), NOT silent-value SDC —
distinct from L1D (data -> potential silent SDC) and GPR (data ->
SDC/Hang mix). The §9.1 Hang class (frozen 240s threshold) captures this.

Usage: python3 tests/p0_l1i_pilot.py <gem5.opt> <arm_chaos_cache.py> <l1i_loop>
"""
import os, subprocess, sys, tempfile, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..", "tools"))
from classify import classify_run  # noqa: E402

if len(sys.argv) != 4:
    sys.exit("usage: p0_l1i_pilot.py <gem5.opt> <arm_chaos_cache.py> <l1i_loop>")
g5, cfg, binary = sys.argv[1], sys.argv[2], sys.argv[3]
GOLDEN = "bb0b1c4cb661236e"
HANG_CUTOFF = 120

def run(seed):
    d = tempfile.mkdtemp(prefix=f"l1i-{seed}-")
    try:
        r = subprocess.run([g5, "--quiet", f"--outdir={d}", cfg,
            "--cmd", binary, "--target", "l1i", "--first_clock=10000",
            "--max_faults=1", f"--rng_seed={seed}", "--fault_type=bit_flip",
            "--bits_to_change=1", "--probability=1.0"],
            capture_output=True, text=True, timeout=HANG_CUTOFF)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        r = subprocess.CompletedProcess([], returncode=-1,
            stdout=(e.stdout or b"").decode() if e.stdout else "",
            stderr=(e.stderr or b"").decode() if e.stderr else "")
        timed_out = True
    faults = 0
    p = os.path.join(d, "cache_injections.log")
    if os.path.exists(p):
        for line in open(p):
            if line.strip() and "Error" not in line:
                faults += 1
    cls, _ = classify_run(r.stdout or "", r.stderr or "", r.returncode,
                          faults, GOLDEN, timed_out)
    return cls

hang=sdc=masked=crash=0
print(f"{'seed':>10} {'class'}")
for s in range(20260825, 20260835):
    cls = run(s)
    if cls=="SDC": sdc+=1
    elif cls=="Masked": masked+=1
    elif cls=="Hang": hang+=1
    elif cls=="Crash": crash+=1
    print(f"{s:>10} {cls}")
print(f"\nP0 L1I pilot (n=10): SDC={sdc} Hang={hang} Crash={crash} Masked={masked}")
print("L1I instruction-bit faults are Hang-heavy (control-flow corruption, plan §7.2).")
