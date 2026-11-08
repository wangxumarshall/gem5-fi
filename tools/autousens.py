#!/usr/bin/env python3
"""AutoµSens prototype: instruction -> structure map and reverse targeting.

Phase 1 of ``sdcfuzz/sdcfuzz-v1.2.md`` asks for a structural-coverage
evaluation tool plus an automatic targeting generator.  This prototype covers
the part that the current gem5 model can actually observe:

  * ``map``      run one AArch64 instruction per probe stream, subtract the
                 empty-loop baseline and emit per-structure activation.  The
                 result is the ``STRUCTURE_MAP`` seed used for targeting.
  * ``target``   rank instructions by activation of one target structure,
                 compose the top-k into a candidate AArch64 program, run it in
                 gem5 and report its coverage vector.
  * ``evaluate`` recompute a coverage vector for any gem5 result directory.

Observable structures are limited to the implemented metrics: integer physical
register file (rf), L1I ACE, L1D ACE, and the intAlu/intMult/intDiv FU classes.
FP/SIMD/SVE, TLB, ROB and LSQ have no metric yet and are reported as
unsupported instead of being silently invented.

Activation is measured as probe counters minus the baseline counters of an
empty loop with the same shape (16 groups of 4 instructions per iteration).
Negative differences are clamped to zero and listed under ``clamped`` so noise
is visible rather than hidden.
"""

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEM5_SRC = ROOT / "CHAOS/gem5"
PROBE_SOURCE = ROOT / "workloads/directed/structural_probe_workload.c"
M5OP = GEM5_SRC / "util/m5/src/abi/arm64/m5op.S"

DEFAULT_ITERATIONS = 100
OPS_PER_GROUP = 4
GROUPS_PER_ITER = 16

STRUCTURES = ("rf", "l1i", "l1d", "alu", "mult", "div")

# Instruction snippets used by the probe streams and by generated candidates.
MODE_ASM = {
    "baseline": "nop",
    "add": "add x8, x8, x12",
    "sub": "sub x8, x8, x12",
    "and": "and x8, x8, x12",
    "orr": "orr x8, x8, x12",
    "eor": "eor x8, x8, x12",
    "mul": "mul x8, x8, x12",
    "madd": "madd x8, x8, x12, x10",
    "udiv": "udiv x8, x8, x12",
    "ldr": "ldr x8, [%[buf]]",
    "str": "str x8, [%[buf]]",
    "ldxr": "ldxr x8, [%[buf]]",
}

PROBE_MODES = tuple(MODE_ASM)

# Exact statistic suffixes; each must match exactly one field per dump so a
# renamed or duplicated counter fails loudly instead of picking a wrong value.
COUNTERS = {
    "rf_reads": ".rfAce.intTrackedReads",
    "rf_writes": ".rfAce.intTrackedWrites",
    "alu_bits": ".fuIbr.inputBits::intAlu",
    "mult_bits": ".fuIbr.inputBits::intMult",
    "div_bits": ".fuIbr.inputBits::intDiv",
    "l1d_reads": "l1d-cache-0.l1Ace.trackedDemandReads",
    "l1d_writes": "l1d-cache-0.l1Ace.trackedDemandWrites",
    "l1i_reads": "l1i-cache-0.l1Ace.trackedDemandReads",
    "cycles": ".rfAce.measuredCycles",
}

RATIO_COUNTERS = {
    "rf": ".rfAce.intAceRatio",
    "l1i": "l1i-cache-0.l1Ace.aceRatio",
    "l1d": "l1d-cache-0.l1Ace.aceRatio",
    "alu": ".fuIbr.ibrRatio::intAlu",
    "mult": ".fuIbr.ibrRatio::intMult",
    "div": ".fuIbr.ibrRatio::intDiv",
}


def die(message):
    print(f"autousens: error: {message}", file=sys.stderr)
    raise SystemExit(2)


def stat_dumps(path):
    """Split a gem5 stats file into dumps keyed by full statistic name."""
    dumps, current = [], None
    for line in path.read_text().splitlines():
        if "Begin Simulation Statistics" in line:
            current = {}
        elif "End Simulation Statistics" in line:
            if current is not None:
                dumps.append(current)
            current = None
        elif current is not None:
            fields = line.split()
            if len(fields) >= 2:
                try:
                    current[fields[0]] = float(fields[1])
                except ValueError:
                    pass
    if not dumps:
        die(f"no statistics dumps in {path}")
    return dumps


def metric(stats, suffix):
    matches = [value for name, value in stats.items() if name.endswith(suffix)]
    if len(matches) != 1:
        die(f"statistic *{suffix} matched {len(matches)} fields in one dump")
    return matches[0]


def counters_from_dump(stats):
    return {name: metric(stats, suffix) for name, suffix in COUNTERS.items()}


def coverage_from_dump(stats):
    coverage = {}
    for structure, suffix in RATIO_COUNTERS.items():
        value = metric(stats, suffix)
        if not math.isfinite(value):
            die(f"non-finite coverage for {structure}: {value}")
        coverage[structure] = value
    return coverage


def activation_from_net(net):
    """Map raw net counters onto the six observable structures."""
    return {
        "rf": net["rf_reads"] + net["rf_writes"],
        "l1i": net["l1i_reads"],
        "l1d": net["l1d_reads"] + net["l1d_writes"],
        "alu": net["alu_bits"],
        "mult": net["mult_bits"],
        "div": net["div_bits"],
    }


def subtract_baseline(raw, baseline):
    net, clamped = {}, []
    for name, value in raw.items():
        difference = value - baseline[name]
        if difference < 0:
            clamped.append(name)
            difference = 0.0
        net[name] = difference
    return net, clamped


def per_instruction(values, dynamic_ops):
    return {name: value / dynamic_ops for name, value in values.items()}


def compile_guest(source, output, cc, extra_flags=()):
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        cc, "-O2", "-static", "-fno-pie", "-no-pie",
        "-Wall", "-Wextra", "-Werror", *extra_flags,
        "-I" + str(GEM5_SRC / "include"),
        str(source), str(M5OP), "-o", str(output),
    ]
    subprocess.run(command, check=True)
    return output.resolve()


def gem5_environment():
    env = os.environ.copy()
    conda = Path(env.get("CONDA_PREFIX", Path.home() / "miniconda3/envs/py312"))
    lib = conda / "lib"
    if lib.is_dir():
        env["LD_LIBRARY_PATH"] = str(lib) + ":" + env.get("LD_LIBRARY_PATH", "")
    return env


def run_guest(gem5, outdir, guest, workload_args, expected):
    """Run one guest under the three structural metrics and return its dumps."""
    outdir.mkdir(parents=True, exist_ok=True)
    command = [
        str(gem5), "--outdir=" + str(outdir),
        str(ROOT / "configs/se/arm_chaos.py"), "--cpu=O3",
        "--cmd=" + str(guest), "--workload_args=" + workload_args,
        "--rf_ace", "--rf_ace_granularity=bit", "--l1_ace", "--fu_ibr",
    ]
    with (outdir / "gem5.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                       env=gem5_environment(), check=True)
    text = (outdir / "gem5.log").read_text()
    if "status=" + expected not in text:
        die(f"{outdir}: guest did not report status={expected}")
    return stat_dumps(outdir / "stats.txt")


def probe_directory(args):
    outdir = args.outdir.resolve()
    guest = compile_guest(PROBE_SOURCE, outdir / "bin" / "structural_probe",
                          args.cc)
    return outdir, guest


def build_map(args):
    outdir, guest = probe_directory(args)
    if args.iterations <= 0:
        die("--iterations must be positive")
    dynamic_ops = args.iterations * GROUPS_PER_ITER * OPS_PER_GROUP
    runs, coverage = {}, {}
    for mode in args.modes:
        dumps = run_guest(args.gem5.resolve(), outdir / mode, guest,
                          f"{mode} {args.iterations}", "PASS")
        runs[mode] = counters_from_dump(dumps[-1])
        coverage[mode] = coverage_from_dump(dumps[-1])
    baseline = runs["baseline"]
    instructions = {}
    for mode in args.modes:
        if mode == "baseline":
            continue
        net, clamped = subtract_baseline(runs[mode], baseline)
        activation = activation_from_net(net)
        instructions[mode] = {
            "asm": MODE_ASM[mode],
            "raw": runs[mode],
            "net": net,
            "activation": activation,
            "activation_per_instruction": per_instruction(activation,
                                                          dynamic_ops),
            "coverage": coverage[mode],
            "clamped": clamped,
        }
    document = {
        "schema": "autousens.structure_map.v1",
        "gem5": str(args.gem5.resolve()),
        "iterations": args.iterations,
        "dynamic_ops": dynamic_ops,
        "observable_structures": list(STRUCTURES),
        "units": {
            "rf": "integer physical-register accesses (reads + writes)",
            "l1i": "L1I demand reads (cache-line events)",
            "l1d": "L1D demand reads + demand writes (cache-line events)",
            "alu": "intAlu input bits (ports * width per issued op)",
            "mult": "intMult input bits (ports * width per issued op)",
            "div": "intDiv input bits (ports * width per issued op)",
        },
        "notes": [
            "activation is net of an empty-loop baseline; negative noise is"
            " clamped to zero and listed per instruction in 'clamped'",
            "cross-structure activation values are not commensurate"
            " (events vs input bits); compare one structure across instructions",
            "FP/SIMD/SVE, TLB, ROB and LSQ have no metric and are not mapped",
            "2-source shift instructions (e.g. LSLV) are outside the FU IBR"
            " arithmetic subset and therefore not probed",
        ],
        "baseline": {
            "raw": baseline,
            "coverage": coverage["baseline"],
        },
        "instructions": instructions,
    }
    path = outdir / "structure_map.json"
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    for mode, entry in instructions.items():
        profile = " ".join(f"{structure}={entry['activation'][structure]:.0f}"
                           for structure in STRUCTURES
                           if entry["activation"][structure])
        print(f"{mode:8s} {profile if profile else 'no activation above baseline'}")
    print(f"structure map: {path}")
    return document, path


def rank_for_structure(document, structure):
    if structure not in STRUCTURES:
        die(f"unsupported structure {structure!r}; choose from "
            + ", ".join(STRUCTURES))
    entries = document.get("instructions")
    if not entries:
        die("structure map has no instructions")
    ranked = sorted(
        entries.items(),
        key=lambda item: (-item[1]["activation"][structure], item[0]),
    )
    return ranked


def candidate_source(target, chosen, iterations):
    """Compose the chosen instruction snippets into a runnable guest program."""
    snippet_block = "".join(f'        "{MODE_ASM[mode]}\\n\\t"\n' for mode in chosen)
    body = "".join(snippet_block for _ in range(OPS_PER_GROUP))
    return f"""/* Generated by tools/autousens.py --structure {target}; do not edit. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <gem5/m5ops.h>

#if !defined(__aarch64__)
#error "generated candidate requires AArch64"
#endif

static uint64_t data[64] __attribute__((aligned(64))) = {{
    [0] = 0x0123456789abcdefULL,
}};

int
main(int argc, char **argv)
{{
    if (argc != 2)
        return 2;
    const uint64_t iterations = strtoull(argv[1], NULL, 0);
    if (!iterations || iterations > 1000000)
        return 2;
    uint64_t *buffer = data;
    uint64_t count = iterations, value = 0;
    m5_work_begin(7, 0);
    __asm__ volatile(
        "mov x8, #3\\n\\t"
        "mov x10, #5\\n\\t"
        "mov x12, #3\\n\\t"
        "1:\\n\\t"
        ".rept {GROUPS_PER_ITER}\\n\\t"
{body}        ".endr\\n\\t"
        "subs %[n], %[n], #1\\n\\t"
        "b.ne 1b\\n\\t"
        "mov %[v], x8\\n\\t"
        : [n] "+r"(count), [v] "=r"(value)
        : [buf] "r"(buffer)
        : "x8", "x10", "x12", "cc", "memory");
    m5_work_end(7, 0);
    printf("candidate={target} iterations=%llu result=%llu status=DONE\\n",
           (unsigned long long)iterations, (unsigned long long)value);
    return 0;
}}
"""


def evaluate_directory(outdir, baseline_dir=None):
    stats = stat_dumps(outdir / "stats.txt")[-1]
    raw = counters_from_dump(stats)
    report = {
        "outdir": str(outdir.resolve()),
        "raw": raw,
        "coverage": coverage_from_dump(stats),
    }
    if baseline_dir is not None:
        baseline = counters_from_dump(
            stat_dumps(Path(baseline_dir) / "stats.txt")[-1])
        net, clamped = subtract_baseline(raw, baseline)
        report["net"] = net
        report["activation"] = activation_from_net(net)
        report["clamped"] = clamped
        report["baseline_coverage"] = coverage_from_dump(
            stat_dumps(Path(baseline_dir) / "stats.txt")[-1])
    return report


def target(args):
    map_path = args.map.resolve()
    if not map_path.is_file():
        die(f"structure map not found: {map_path}")
    document = json.loads(map_path.read_text())
    ranked = rank_for_structure(document, args.structure)
    if args.top <= 0:
        die("--top must be positive")
    chosen = [mode for mode, _ in ranked[:args.top]]
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    source = outdir / "candidate.c"
    source.write_text(candidate_source(args.structure, chosen,
                                       args.iterations))
    guest = compile_guest(source, outdir / "bin" / "candidate", args.cc)
    dumps = run_guest(args.gem5.resolve(), outdir / "run", guest,
                      str(args.iterations), "DONE")
    # A fresh baseline in the same build keeps the net activation honest.
    baseline_guest = compile_guest(
        PROBE_SOURCE, outdir / "bin" / "structural_probe", args.cc)
    baseline_dumps = run_guest(args.gem5.resolve(), outdir / "baseline",
                               baseline_guest,
                               f"baseline {args.iterations}", "PASS")
    stats = dumps[-1]
    raw = counters_from_dump(stats)
    baseline_raw = counters_from_dump(baseline_dumps[-1])
    net, clamped = subtract_baseline(raw, baseline_raw)
    report = {
        "schema": "autousens.candidate_report.v1",
        "structure": args.structure,
        "chosen": chosen,
        "source": str(source),
        "candidate": str(guest),
        "iterations": args.iterations,
        "raw": raw,
        "net": net,
        "activation": activation_from_net(net),
        "clamped": clamped,
        "coverage": coverage_from_dump(stats),
        "baseline_coverage": coverage_from_dump(baseline_dumps[-1]),
        "supported_structures": list(STRUCTURES),
    }
    path = outdir / "candidate_report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"target={args.structure} chosen={','.join(chosen)}")
    print(f"coverage[{args.structure}]={report['coverage'][args.structure]:.6f} "
          f"baseline={report['baseline_coverage'][args.structure]:.6f} "
          f"net_activation={report['activation'][args.structure]:.0f}")
    print(f"candidate report: {path}")
    return report, path


def evaluate(args):
    if not (args.dir / "stats.txt").is_file():
        die(f"no stats.txt under {args.dir}")
    report = evaluate_directory(args.dir, args.baseline_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--gem5", type=Path,
                       default=ROOT / "CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt",
                       help="gem5.opt with RF ACE / L1 ACE / FU IBR support")
        p.add_argument("--cc", default=os.environ.get("ARM_CC",
                                                      "aarch64-linux-gnu-gcc"),
                       help="AArch64 cross compiler")
        p.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS,
                       help="probe loop iterations (default 100)")

    map_parser = sub.add_parser("map", help="build the instruction->structure map")
    common(map_parser)
    map_parser.add_argument("--outdir", type=Path, required=True)
    map_parser.add_argument("--modes", default=",".join(PROBE_MODES),
                            help="comma-separated probe modes")

    target_parser = sub.add_parser("target", help="reverse-target one structure")
    common(target_parser)
    target_parser.add_argument("--map", type=Path, required=True)
    target_parser.add_argument("--structure", required=True, choices=STRUCTURES)
    target_parser.add_argument("--top", type=int, default=1,
                               help="number of instructions to compose")
    target_parser.add_argument("--outdir", type=Path, required=True)

    evaluate_parser = sub.add_parser("evaluate",
                                     help="recompute a coverage vector")
    evaluate_parser.add_argument("--dir", type=Path, required=True)
    evaluate_parser.add_argument("--baseline-dir", type=Path, default=None)

    args = parser.parse_args()
    if args.command == "map":
        modes = tuple(mode.strip() for mode in args.modes.split(",") if mode.strip())
        unknown = [mode for mode in modes if mode not in MODE_ASM]
        if unknown:
            die("unknown probe modes: " + ", ".join(unknown))
        if "baseline" not in modes:
            die("the probe set must include the baseline mode")
        args.modes = modes
        build_map(args)
    elif args.command == "target":
        target(args)
    else:
        evaluate(args)


if __name__ == "__main__":
    main()
