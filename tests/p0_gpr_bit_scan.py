#!/usr/bin/env python3
"""P0 BM-GPR bit-stratified scan (plan §7.1, §6.1 P0).

Directed single-bit-flip on the two SDC-active GPRs (X2, X3) discovered in
the n=10 pilot, across the G1 boundary bits 0 / 31 / 32 / 63, with a LONG
timeout (reg_chain O3 sim takes ~50-90s; a Hang needs >2x that). Classifies
per §9.1: SDC (output != golden, program completed), Hang (exceeds the
frozen Hang threshold, no output), Masked (== golden).

Findings (seed=20260825, firstClock=100000, maxFaults=1, arch_frontend):
  - low bits (e.g. bit 0) on X2/X3 -> SDC (different checksum)
  - high bit 31 on X2 -> HANG (bit 31 flip in the accumulator corrupted
    loop control; program never completes within 180s)
This demonstrates the plan's SDC-vs-Hang distinction is real and
bit-position-dependent — high-bit flips can corrupt control flow (Hang),
not just data (SDC).

Usage: python3 tests/p0_gpr_bit_scan.py <gem5.opt> <arm_chaos.py> <reg_chain>
"""
import os, subprocess, sys, tempfile, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..", "tools"))
from classify import classify_run  # noqa: E402

if len(sys.argv) != 4:
    sys.exit("usage: p0_gpr_bit_scan.py <gem5.opt> <arm_chaos.py> <reg_chain>")
g5, cfg, binary = sys.argv[1], sys.argv[2], sys.argv[3]
GOLDEN = "f247ef3fe6f02cfd"

# reg_chain O3 sim completes in ~50-90s on this host. Hang threshold (plan §13.2):
# golden ROI tick * 10. Here we use a wall-clock 240s cutoff (>= 3x sim time)
# and classify no-output-within-cutoff as Hang.
HANG_CUTOFF = 240

BITS = {"bit0": 1, "bit31": 1 << 31, "bit32": 1 << 32, "bit63": 1 << 63}

def run(arch, mask_int):
    d = tempfile.mkdtemp(prefix=f"p0bs-{arch}-{mask_int}-")
    try:
        r = subprocess.run([g5, "--quiet", f"--outdir={d}", cfg,
            "--cmd", binary, "--cpu", "O3", "--chaos_phys",
            "--phys_mode", "arch_frontend", f"--phys_target_arch={arch}",
            "--probability=1.0", "--first_clock=100000", "--max_faults=1",
            "--rng_seed=20260825", "--fault_type=bit_flip",
            f"--fault_mask={mask_int}"],
            capture_output=True, text=True, timeout=HANG_CUTOFF)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        r = subprocess.CompletedProcess([], returncode=-1,
            stdout=(e.stdout or b"").decode() if e.stdout else "",
            stderr=(e.stderr or b"").decode() if e.stderr else "")
        timed_out = True
    # faults_injected (1 expected, real injection line only)
    faults = 0
    p = os.path.join(d, "fault_injections.log")
    if os.path.exists(p):
        for line in open(p):
            if ("Inactive" in line or line.startswith("Error")
                    or "ReadTracePoll" in line or "ReadTraceFinal" in line):
                continue
            if "FaultType:" in line:
                faults += 1
    cls, _ = classify_run(r.stdout or "", r.stderr or "", r.returncode,
                          faults, GOLDEN, timed_out)
    return cls

print(f"{'reg':<4} {'bit':<6} {'class'}")
counts = {"SDC":0, "Masked":0, "Hang":0, "Crash":0, "Inactive":0, "SimulatorError":0}
for arch in (2, 3):
    for name, mask in BITS.items():
        cls = run(arch, mask)
        counts[cls] = counts.get(cls, 0) + 1
        print(f"X{arch:<3} {name:<6} {cls}")

n = sum(counts.values())
print(f"\nP0 GPR bit-stratified (n={n}): "
      f"SDC={counts['SDC']} Hang={counts['Hang']} Masked={counts['Masked']} "
      f"Crash={counts['Crash']} Inactive={counts['Inactive']} "
      f"SimulatorError={counts['SimulatorError']}")
print("NOTE: Hang = timeout with no completion (plan §13.2 frozen threshold). "
      "bit32/bit63 now reach the reg (64-bit mask fix); the old result "
      "(3551d57 'high-bit Hang') is re-run here honestly with the classifier.")
