#!/usr/bin/env python3
"""M06-C05 speculative wrong-path cold-fetch FEASIBILITY PILOT.

Runs ONE gem5 O3 pre-scan with the mmu_w15 speculative-cold-fetch workload to
answer: can a SPECULATIVE (wrong-path) cold instruction fetch form an eligible
M06 event (Stage-1, L3, valid descriptor 0b11)?

The pre-scan (`--mmu_prescan true`) never mutates and never activates; it
emits an `mmu_eligible_event` per eligible occurrence, so the eligible total
count is the direct answer.

Evidence written under runs/pilot/M06-C05/: rcS, command.txt, terminal,
prop_evt.txt.gz, gem5 stdout, and pilot_result.json (N, eligible stream).
"""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEM5 = os.path.join(ROOT, "CHAOS", "gem5", "build", "ARM", "gem5.opt")
CONFIG = os.path.join(ROOT, "configs", "fs", "lsu_b0_fs.py")
KERNEL = os.path.join(ROOT, "gem5-fs", "vmlinux")
BOOTLOADER = os.path.join(ROOT, "gem5-fs", "boot.arm64")
CHECKPOINT = os.path.join(ROOT, "runs", "mmu_bootF1", "cpt.244799013609")
DISK_TEMPLATE = os.path.join(ROOT, "runs", "disks", "mmu_template.img")
WL = os.path.join(ROOT, "workloads", "mmu_w5x3", "mmu_w15_nosys")
OUT = os.path.join(ROOT, "runs", "pilot", "M06-C05")

TARGET_VA = 0x4001680000   # inside the M06 trace window (cold JIT page)
LO = 0x4001600000
HI = 0x4001700000


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def gen_rcs(binary, out_path):
    raw = open(binary, "rb").read()
    gz = subprocess.run(["xz", "-9ec", "-T1"], input=raw,
                        stdout=subprocess.PIPE, check=True).stdout
    b64 = base64.b64encode(gz).decode("ascii")
    tag = "MMU_W15_M06_C05"
    lines = ["#!/bin/sh",
             "# PILOT M06-C05 speculative wrong-path cold walk",
             "# WorkloadID=W15 guest_ctx=SPEC reps=3 binary_sha256=%s" %
             hashlib.sha256(raw).hexdigest(),
             "ulimit -l unlimited 2>/dev/null || true",
             'echo "[when5x3] install M06 C05"',
             "base64 -d > /tmp/w5x3_workload.xz <<'%s'" % tag]
    for i in range(0, len(b64), 76):
        lines.append(b64[i:i + 76])
    lines += [tag,
              "if ! xz -dc /tmp/w5x3_workload.xz > /tmp/w5x3_workload; then",
              '  echo "[when5x3] FATAL payload decode failed"',
              "  m5 exit", "fi",
              "chmod +x /tmp/w5x3_workload",
              'echo "[when5x3] start M06 C05"',
              "i=0",
              "while [ $i -lt 3 ]; do",
              "  i=$((i+1))",
              '  echo "[when5x3] episode=$i"',
              "  /tmp/w5x3_workload --episodes 1",
              '  echo "[when5x3] episode=$i rc=$?"',
              "done",
              'echo "[when5x3] done M06 C05"',
              "m5 exit"]
    with open(out_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return sha(out_path), hashlib.sha256(raw).hexdigest()


def main():
    if not os.path.isfile(WL):
        print("PILOT: workload missing", WL, file=sys.stderr)
        return 2
    os.makedirs(OUT, exist_ok=True)
    rcs = os.path.join(OUT, "M06-C05.rcS")
    rcs_sha, wl_sha = gen_rcs(WL, rcs)

    disk = os.path.join(OUT, "disk.img")
    subprocess.run(["cp", "--reflink=auto", DISK_TEMPLATE, disk], check=True)
    outdir = os.path.join(OUT, "run")
    os.makedirs(os.path.join(OUT, "Trace"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "Run_Log"), exist_ok=True)
    cmd = [GEM5, "--outdir", outdir, CONFIG,
           "--kernel", KERNEL, "--disk", disk, "--bootloader", BOOTLOADER,
           "--cpu", "O3", "--restore-checkpoint", CHECKPOINT,
           "--readfile", rcs, "--chaos_propagation",
           "--prop_mmu_va_lo", hex(LO), "--prop_mmu_va_hi", hex(HI),
           "--prop_run_id", "PILOT-M06-C05", "--prop_sample_run_id",
           "PILOT-M06-C05", "--prop_mmu_trace", "--prop_write_log", "on",
           "--mmu_fault_model", "M06", "--mmu_fault_enable", "true",
           "--mmu_eligible_event_index", "1", "--mmu_prescan", "true",
           "--mmu_m02_dram_lo", "0x80000000", "--mmu_m02_dram_hi",
           "0x100000000",
           "--mmu_target_va", hex(TARGET_VA), "--mmu_target_n", "12",
           "--mmu_target_mode", "Execute", "--mmu_target_walk_level", "3"]
    with open(os.path.join(OUT, "Run_Log", "command.txt"), "w") as fh:
        fh.write(" ".join(cmd) + "\n")
    with open(os.path.join(OUT, "Run_Log", "gem5_stdout.log"), "w") as logf:
        proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT,
                              timeout=1800)
    rc = proc.returncode
    evt = os.path.join(outdir, "prop_evt.txt.gz")
    term = os.path.join(outdir, "board.terminal")
    eligible = 0
    elig_lines = []
    if os.path.isfile(evt):
        import gzip
        with gzip.open(evt, "rt", errors="replace") as fh:
            for line in fh:
                if "kind=mmu_eligible_event" in line:
                    eligible += 1
                    m = re.search(r"eligible_ordinal=(\d+)", line)
                    va = re.search(r"va=([0-9a-fA-F]+)", line)
                    elig_lines.append({"ordinal": m.group(1) if m else "?",
                                       "va": va.group(1) if va else "?"})
                elif "kind=mmu_eligible_selected" in line:
                    elig_lines.append({"ordinal": "SELECTED", "va": ""})
        shutil.copy2(evt, os.path.join(OUT, "Trace", "prop_evt.txt.gz"))
    if os.path.isfile(term):
        shutil.copy2(term, os.path.join(OUT, "Run_Log", "board.terminal"))
    result = {
        "pilot": "M06-C05 speculative wrong-path cold-walk feasibility",
        "workload": "workloads/mmu_w5x3/mmu_w15",
        "workload_sha256": wl_sha, "rcs": rcs, "rcs_sha256": rcs_sha,
        "gem5_sha256": sha(GEM5) if os.path.isfile(GEM5) else "",
        "returncode": rc,
        "target_va": hex(TARGET_VA), "target_mode": "Execute",
        "eligible_total": eligible,
        "eligible_events": elig_lines,
        "conclusion": ("FEASIBLE" if eligible >= 3 else "INFEASIBLE"),
    }
    with open(os.path.join(OUT, "pilot_result.json"), "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(json.dumps(result, indent=2))
    if os.path.isfile(disk):
        os.remove(disk)
    return 0


if __name__ == "__main__":
    sys.exit(main())