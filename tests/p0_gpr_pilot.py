#!/usr/bin/env python3
"""P0 BM-GPR pilot (plan §7.1): directed single-bit-flip on AArch64 GPRs.

Scans arch_frontend-mode CHAOSPhysReg injection across X0-X9 (and a
selected set), each with exactly 1 bit flip (bit chosen by RNG=20260825),
maxFaults=1, firstClock=100000, on the reg_chain dependency-chain kernel.
Classifies each run vs the golden checksum (f247ef3fe6f02cfd) per §9.1:
  Masked  = output == golden (flip did not propagate)
  SDC     = output != golden AND program completed (no detection)
  Inactive= 0 valid injections
This is a PILOT (per-cell n=1), not a formal 384-sample cell. It demonstrates
the GPR target is reachable and produces measurable SDC on O3 via physical-
register injection.

Usage: python3 tests/p0_gpr_pilot.py <gem5.opt> <arm_chaos.py> <reg_chain>
"""
import os, subprocess, sys, tempfile, re

if len(sys.argv) != 4:
    sys.exit("usage: p0_gpr_pilot.py <gem5.opt> <arm_chaos.py> <reg_chain>")
g5, cfg, binary = sys.argv[1], sys.argv[2], sys.argv[3]
GOLDEN = "f247ef3fe6f02cfd"  # reg_chain no-injection golden

def run(arch_idx):
    d = tempfile.mkdtemp(prefix=f"p0-{arch_idx}-")
    r = subprocess.run([g5, "--quiet", f"--outdir={d}", cfg,
        "--cmd", binary, "--cpu", "O3", "--chaos_phys",
        "--phys_mode", "arch_frontend", f"--phys_target_arch={arch_idx}",
        "--probability=1.0", "--first_clock=100000", "--max_faults=1",
        "--rng_seed=20260825", "--fault_type=bit_flip",
        "--bits_to_change=1"],
        capture_output=True, text=True, timeout=120)
    m = re.findall(r"^[0-9a-fA-F]{16}$", r.stdout, re.MULTILINE)
    out = m[-1] if m else "?"
    # faults_injected from log: count real injection lines only.
    # CHAOSPhysReg log has 1 injection line + many ReadTracePoll lines;
    # exclude ReadTracePoll/Inactive/Error lines.
    faults = 0
    for log in ("fault_injections.log","main_mem_injections.log"):
        p = os.path.join(d, log)
        if os.path.exists(p):
            for line in open(p):
                if ("Inactive" in line or line.startswith("Error")
                        or "ReadTracePoll" in line or "Cycle:" in line and "PhysReg" not in line):
                    continue
                if "FaultType:" in line or "Fault Type:" in line:
                    faults += 1
            break
    # phys reg from log
    phys = ""
    for log in ("fault_injections.log","main_mem_injections.log"):
        p = os.path.join(d, log)
        if os.path.exists(p):
            mm = re.search(r"PhysReg\[\d+\]", open(p).read())
            if mm: phys = mm.group(0)
            break
    return out, faults, phys

sdc=masked=inactive=0
print(f"{'ArchReg':>8} {'Output':<18} {'Class':<10} {'Phys':<14} {'faults'}")
for r in range(10):  # X0-X9 (X10+ caller-saved beyond the dep chain)
    out, faults, phys = run(r)
    if faults == 0:
        cls = "Inactive"; inactive += 1
    elif out == GOLDEN:
        cls = "Masked"; masked += 1
    else:
        cls = "SDC"; sdc += 1
    print(f"X{r:<7} {out:<18} {cls:<10} {phys:<14} {faults}")

n = sdc + masked + inactive
print(f"\nP0 GPR pilot (n={n}, directed 1-bit-flip, arch_frontend, O3):")
print(f"  SDC={sdc}  Masked={masked}  Inactive={inactive}")
if n > 0:
    print(f"  P_SDC = {sdc}/{n} = {100*sdc/n:.0f}%  (pilot, not formal; "
          f"no 95% CI at n={n})")
