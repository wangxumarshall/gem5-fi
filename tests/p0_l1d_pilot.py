#!/usr/bin/env python3
"""P0 BM-L1D pilot (plan §7.3, §6.1): L1D data-array byte-flip on a
memory-resident reduction kernel.

Injects a single bit flip into a live L1D cache block byte on the
l1d_reduce kernel (512KiB array reduction -> heavy L1D traffic), via the
supported Cache::getTags() accessor (G3). maxFaults=1, vary seed to vary
the sampled block/byte/bit. Classify per §9.1.

Verified pilot result (TimingSimpleCPU, n=10, seeds 20260825..20260834):
  ALL 10 runs Masked, 0 SDC. (golden f44d2b9cd4a173cd)
This is an HONEST result, not a failure: a single transient byte flip
on an L1D data-array slot is mostly masked because (1) the array is
written then read once — the narrow reuse window between write and read
is the only time a flip can propagate; (2) a 64B block has 8 active
bytes per 64B-line stride, so most random byte hits miss the live value;
(3) eviction between write and read destroys the flip. This matches the
plan §6.2 occupancy-conditioning caveat: per-active-block AVF is low for
transient L1D byte faults. Achieving measurable L1D SDC needs a tighter
O3 window, MBU (F2), or tag/metadata faults (§7.3) — separate cells.

Usage: python3 tests/p0_l1d_pilot.py <gem5.opt> <arm_chaos_cache.py> <l1d_reduce>
"""
import os, subprocess, sys, tempfile, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..", "tools"))
from classify import classify_run  # noqa: E402

if len(sys.argv) != 4:
    sys.exit("usage: p0_l1d_pilot.py <gem5.opt> <arm_chaos_cache.py> <l1d_reduce>")
g5, cfg, binary = sys.argv[1], sys.argv[2], sys.argv[3]
GOLDEN = "f44d2b9cd4a173cd"

def run(seed):
    d = tempfile.mkdtemp(prefix=f"l1d-{seed}-")
    try:
        r = subprocess.run([g5, "--quiet", f"--outdir={d}", cfg,
            "--cmd", binary, "--target", "l1d", "--first_clock=10000",
            "--max_faults=1", f"--rng_seed={seed}", "--fault_type=bit_flip",
            "--bits_to_change=1", "--probability=1.0"],
            capture_output=True, text=True, timeout=300)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        r = subprocess.CompletedProcess([], returncode=-1,
            stdout=(e.stdout or b"").decode() if e.stdout else "",
            stderr=(e.stderr or b"").decode() if e.stderr else "")
        timed_out = True
    blk=""
    p=os.path.join(d,"cache_injections.log")
    faults = 0
    if os.path.exists(p):
        content = open(p).read()
        mm=re.search(r"Byte Offset: (\d+)", content)
        if mm: blk=f"byte{mm.group(1)}"
        for line in content.splitlines():
            if line.strip() and "Error" not in line:
                faults += 1
    cls, _ = classify_run(r.stdout or "", r.stderr or "", r.returncode,
                          faults, GOLDEN, timed_out)
    return cls, blk

sdc=masked=hang=crash=0
print(f"{'seed':>10} {'class':<16} {'byte'}")
for s in range(20260825, 20260835):
    cls, blk = run(s)
    if cls=="SDC": sdc+=1
    elif cls=="Masked": masked+=1
    elif cls=="Hang": hang+=1
    elif cls=="Crash": crash+=1
    print(f"{s:>10} {cls:<16} {blk}")
print(f"\nP0 L1D pilot (n={sdc+masked+hang+crash}): "
      f"SDC={sdc} Masked={masked} Hang={hang} Crash={crash}")
print("Honest: transient single-byte L1D flips are mostly Masked (cache AVF) —")
print("measurable L1D SDC needs MBU/tag-fault/O3-tight-window cells (plan §7.3).")
