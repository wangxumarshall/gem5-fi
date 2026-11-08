#!/usr/bin/env python3
"""Run real AArch64 regressions against an explicitly selected gem5 build."""
import argparse
import math
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GEM5 = ROOT / "CHAOS/gem5"


def stat_dumps(path):
    dumps, current = [], {}
    for line in path.read_text().splitlines():
        if "Begin Simulation Statistics" in line:
            current = {}
        elif "End Simulation Statistics" in line:
            dumps.append(current)
        else:
            fields = line.split()
            if len(fields) >= 2:
                try:
                    current[fields[0]] = float(fields[1])
                except ValueError:
                    pass
    assert dumps, path
    return dumps


def metric(stats, suffix):
    matches = [v for k, v in stats.items() if k.endswith(suffix)]
    assert len(matches) == 1, (suffix, matches)
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gem5", type=Path, required=True)
    parser.add_argument("--outdir", type=Path,
                        default=ROOT / "m5out/ace-ibr-correctness")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    conda = Path(env.get("CONDA_PREFIX", Path.home() / "miniconda3/envs/py312"))
    env["LD_LIBRARY_PATH"] = str(conda / "lib") + ":" + env.get("LD_LIBRARY_PATH", "")
    cc = env.get("ARM_CC", "aarch64-linux-gnu-gcc")

    def compile_guest(source, name, *flags):
        binary = args.outdir / name
        subprocess.run([cc, "-O2", "-static", "-fno-pie", "-no-pie",
                        "-Wall", "-Wextra", "-Werror", *flags,
                        "-I" + str(GEM5 / "include"), str(source),
                        str(GEM5 / "util/m5/src/abi/arm64/m5op.S"),
                        "-o", str(binary)], check=True)
        return binary.resolve()

    guest = compile_guest(ROOT / "workloads/directed/ace_ibr_correctness_workload.c",
                          "correctness", "-march=armv8.1-a")
    fu_guest = compile_guest(ROOT / "workloads/directed/fu_ibr_workload.c", "fu_ibr")

    def run(name, binary, argv, debug=False):
        out = (args.outdir / name).resolve()
        out.mkdir(exist_ok=True)
        command = [str(args.gem5.resolve()), "--outdir=" + str(out)]
        if debug:
            command += ["--debug-flags=IQ,PseudoInst", "--debug-file=issue.trace"]
        command += [str(ROOT / "configs/se/arm_chaos.py"), "--cpu=O3",
                    "--cmd=" + str(binary), "--workload_args=" + argv,
                    "--rf_ace", "--rf_ace_granularity=bit", "--l1_ace", "--fu_ibr"]
        with (out / "gem5.log").open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                           env=env, check=True)
        assert "status=PASS" in (out / "gem5.log").read_text(), out
        dumps = stat_dumps(out / "stats.txt")
        assert len(dumps) >= 2, (name, "work-end and final dumps required")
        # Work-end is an observable, final ROI score. Output code must not
        # change its numerator later by committing earlier speculative reads.
        for group, fields in {
            ".rfAce.": ["intAceBitCycles", "intAceBitCyclesLow32",
                        "intAceBitCyclesHigh32", "intTrackedReads",
                        "intTrackedWrites", "intAceRatio", "measuredCycles"],
            ".fuIbr.": ["inputBits::intAlu", "inputBits::intMult",
                        "inputBits::intDiv", "measuredCycles"],
        }.items():
            for field in fields:
                first = metric(dumps[0], group + field)
                assert all(metric(d, group + field) == first for d in dumps[1:]), (
                    name, group + field, [metric(d, group + field) for d in dumps])
        s = dumps[-1]
        assert metric(s, ".rfAce.windowBegins") == metric(s, ".rfAce.windowEnds") == 1
        for key, value in s.items():
            if key.endswith((".aceRatio", ".intAceRatio")) or ".ibrRatio::" in key:
                assert math.isfinite(value) and 0 <= value <= 1, (name, key, value)
        return s

    results = {name: run(name, guest, name)
               for name in ["ldr", "ldxr", "llsc", "failedsc", "swp", "mixed", "wide",
                            "casfail", "cassame"]}
    for name in ["ldr", "ldxr", "llsc", "swp", "casfail", "cassame"]:
        reads = metric(results[name], "l1d-cache-0.l1Ace.trackedDemandReads")
        assert reads >= 4096, (name, reads)
        if name in ["llsc", "swp", "cassame"]:
            writes = metric(results[name], "l1d-cache-0.l1Ace.trackedDemandWrites")
            assert writes >= 4096, (name, writes)
        else:
            assert metric(results[name], "l1d-cache-0.l1Ace.aceRatio") > 0
        print(f"{name}: demand reads={reads:.0f}")
    failed_writes = metric(results["failedsc"], "l1d-cache-0.l1Ace.trackedDemandWrites")
    assert failed_writes < 10, failed_writes
    assert metric(results["casfail"], "l1d-cache-0.l1Ace.trackedDemandWrites") < 10
    mixed = metric(results["mixed"], ".rfAce.intAceBitCyclesHigh32")
    wide = metric(results["wide"], ".rfAce.intAceBitCyclesHigh32")
    assert mixed < 0.9 * wide, (mixed, wide)
    print(f"mixed-source high32 cycles={mixed:.0f}; all-X control={wide:.0f}")
    run("roi-stability", fu_guest, "alu64 1000")
    boundary = run("issue-boundary", guest, "boundary", debug=True)
    trace = (args.outdir / "issue-boundary/issue.trace").read_text().splitlines()
    disassembly = subprocess.check_output(
        [env.get("ARM_OBJDUMP", "aarch64-linux-gnu-objdump"), "-d", str(guest)],
        text=True)
    words = {int(m[1], 16): int(m[2], 16) for m in re.finditer(
        r"^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s", disassembly, re.MULTILINE)}
    end_tick = next(int(line.split(":", 1)[0]) for line in trace
                    if "pseudo_inst::workend(7," in line)
    begin_tick = next(int(line.split(":", 1)[0]) for line in trace
                      if "pseudo_inst::workbegin(7," in line)
    inside, expected_bits, expected_ops, end_ops = False, 0, 0, 0
    for line in trace:
        if "pseudo_inst::workbegin(7," in line:
            inside = True
        issue = re.match(r"\s*(\d+): .*Issuing instruction PC \((0x[0-9a-f]+)", line)
        if not inside or not issue:
            continue
        tick, pc = int(issue[1]), int(issue[2], 16)
        # After the marker, speculative issues may enter padding that
        # objdump -d omits. Only the ROI and its end cycle are relevant.
        if tick <= begin_tick or tick > end_tick:
            continue
        assert pc in words, f"missing in-window instruction at {pc:#x}, tick={tick}"
        word = words[pc]
        if word & 0x1f000000 not in (0x11000000, 0x12000000, 0x0b000000, 0x0a000000):
            continue
        # The stdlib work-begin handler resets stats after that cycle's
        # pipeline work, discarding issues in the marker/reset cycle.
        if begin_tick < tick < end_tick:
            expected_ops += 1
            expected_bits += 2 * (64 if word >> 31 else 32)
        elif tick == end_tick:
            end_ops += 1
    assert end_ops > 0, "test must exercise an ALU issue in the exclusive end cycle"
    assert metric(boundary, ".fuIbr.issuedOps::intAlu") == expected_ops
    assert metric(boundary, ".fuIbr.inputBits::intAlu") == expected_bits
    print(f"IBR: {expected_ops} in-window ALU issues; {end_ops} end-cycle issues excluded")
    print("Atomic access, mixed-width and ROI snapshot checks passed")
    print(f"outputs: {args.outdir}")


if __name__ == "__main__":
    main()
