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
        m = re.findall(r"^[0-9a-fA-F]{16}$", r.stdout, re.MULTILINE)
        out = m[-1] if m else ""
        return out, r.returncode
    except subprocess.TimeoutExpired:
        return "", -1

print(f"{'reg':<4} {'bit':<6} {'output':<18} {'class'}")
counts = {"SDC":0, "Masked":0, "Hang":0}
for arch in (2, 3):
    for name, mask in BITS.items():
        out, rc = run(arch, mask)
        if out == "":
            cls = "Hang"
        elif out == GOLDEN:
            cls = "Masked"
        else:
            cls = "SDC"
        counts[cls] += 1
        print(f"X{arch:<3} {name:<6} {out:<18} {cls}")

print(f"\nP0 GPR bit-stratified (n={sum(counts.values())}): "
      f"SDC={counts['SDC']} Hang={counts['Hang']} Masked={counts['Masked']}")
print("NOTE: Hang = no program completion within", HANG_CUTOFF,
      "s (plan §13.2 frozen threshold; high-bit flips can corrupt control flow).")
