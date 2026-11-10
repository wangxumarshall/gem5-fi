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
  * ``pareto``   run NSGA-II over instruction sequences with one objective per
                 target structure and emit a Pareto set plus optional gem5
                 validation of the knee point.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nsga2 import knee_point, run_nsga2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GEM5_SRC = ROOT / "CHAOS/gem5"
PROBE_SOURCE = ROOT / "workloads/directed/structural_probe_workload.c"
M5OP = GEM5_SRC / "util/m5/src/abi/arm64/m5op.S"

DEFAULT_ITERATIONS = 100
OPS_PER_GROUP = 4
GROUPS_PER_ITER = 16

STRUCTURES = ("rf", "vec", "l1i", "l1d", "alu", "mult", "div",
              "fpadd", "fpmul")

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
    "movz": "movz x8, #0x1234",
    "add_imm": "add x8, x8, #1",
    "add_lsl": "add x8, x8, x12, lsl #3",
    "fadd": "fadd d0, d0, d1",
    "fmul": "fmul d0, d0, d1",
}

PROBE_MODES = tuple(MODE_ASM)

# Exact statistic suffixes; each must match exactly one field per dump so a
# renamed or duplicated counter fails loudly instead of picking a wrong value.
COUNTERS = {
    "rf_reads": ".rfAce.intTrackedReads",
    "rf_writes": ".rfAce.intTrackedWrites",
    "vec_reads": ".rfAce.vecTrackedReads",
    "vec_writes": ".rfAce.vecTrackedWrites",
    "alu_bits": ".fuIbr.inputBits::intAlu",
    "mult_bits": ".fuIbr.inputBits::intMult",
    "div_bits": ".fuIbr.inputBits::intDiv",
    "fpadd_bits": ".fuIbr.inputBits::fpAdd",
    "fpmul_bits": ".fuIbr.inputBits::fpMult",
    "l1d_reads": "l1d-cache-0.l1Ace.trackedDemandReads",
    "l1d_writes": "l1d-cache-0.l1Ace.trackedDemandWrites",
    "l1i_reads": "l1i-cache-0.l1Ace.trackedDemandReads",
    "cycles": ".rfAce.measuredCycles",
}

RATIO_COUNTERS = {
    "rf": ".rfAce.intAceRatio",
    "vec": ".rfAce.vecAceRatio",
    "l1i": "l1i-cache-0.l1Ace.aceRatio",
    "l1d": "l1d-cache-0.l1Ace.aceRatio",
    "alu": ".fuIbr.ibrRatio::intAlu",
    "mult": ".fuIbr.ibrRatio::intMult",
    "div": ".fuIbr.ibrRatio::intDiv",
    "fpadd": ".fuIbr.ibrRatio::fpAdd",
    "fpmul": ".fuIbr.ibrRatio::fpMult",
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
    """Map raw net counters onto the observable structures."""
    return {
        "rf": net["rf_reads"] + net["rf_writes"],
        "vec": net["vec_reads"] + net["vec_writes"],
        "l1i": net["l1i_reads"],
        "l1d": net["l1d_reads"] + net["l1d_writes"],
        "alu": net["alu_bits"],
        "mult": net["mult_bits"],
        "div": net["div_bits"],
        "fpadd": net["fpadd_bits"],
        "fpmul": net["fpmul_bits"],
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
            "vec": "vector/FP physical-register low-64-bit lane accesses",
            "l1i": "L1I demand reads (cache-line events)",
            "l1d": "L1D demand reads + demand writes (cache-line events)",
            "alu": "intAlu input bits (ports * width per issued op)",
            "mult": "intMult input bits (ports * width per issued op)",
            "div": "intDiv input bits (ports * width per issued op)",
            "fpadd": "fpAdd input bits (ports * width per issued op)",
            "fpmul": "fpMult input bits (ports * width per issued op)",
        },
        "notes": [
            "activation is net of an empty-loop baseline; negative noise is"
            " clamped to zero and listed per instruction in 'clamped'",
            "cross-structure activation values are not commensurate"
            " (events vs input bits); compare one structure across instructions",
            "vector ACE tracks the low 64-bit lane used by scalar D-register"
            " arithmetic; 128-bit SIMD high lanes are outside this metric",
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
        "fmov d0, xzr\\n\\t"
        "fmov d1, xzr\\n\\t"
        "1:\\n\\t"
        ".rept {GROUPS_PER_ITER}\\n\\t"
{body}        ".endr\\n\\t"
        "subs %[n], %[n], #1\\n\\t"
        "b.ne 1b\\n\\t"
        "mov %[v], x8\\n\\t"
        : [n] "+r"(count), [v] "=r"(value)
        : [buf] "r"(buffer)
        : "x8", "x10", "x12", "d0", "d1", "cc", "memory");
    m5_work_end(7, 0);
    printf("candidate={target} iterations=%llu result=%llu status=DONE\\n",
           (unsigned long long)iterations, (unsigned long long)value);
    return 0;
}}
"""


def sequence_candidate_source(target, sequence, iterations):
    """Compose one instruction sequence per group into a runnable guest."""
    snippet_block = "".join(
        f'        "{MODE_ASM[mode]}\\n\\t"\n' for mode in sequence)
    return f"""/* Generated by tools/autousens.py pareto; do not edit. */
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
        "fmov d0, xzr\\n\\t"
        "fmov d1, xzr\\n\\t"
        "1:\\n\\t"
        ".rept {GROUPS_PER_ITER}\\n\\t"
{snippet_block}        ".endr\\n\\t"
        "subs %[n], %[n], #1\\n\\t"
        "b.ne 1b\\n\\t"
        "mov %[v], x8\\n\\t"
        : [n] "+r"(count), [v] "=r"(value)
        : [buf] "r"(buffer)
        : "x8", "x10", "x12", "d0", "d1", "cc", "memory");
    m5_work_end(7, 0);
    printf("candidate={target} iterations=%llu result=%llu status=DONE\\n",
           (unsigned long long)iterations, (unsigned long long)value);
    return 0;
}}
"""


def pareto(args):
    """Generate a Pareto set of instruction sequences with NSGA-II."""
    map_path = args.map.resolve()
    if not map_path.is_file():
        die(f"structure map not found: {map_path}")
    document = json.loads(map_path.read_text())
    structures = [name.strip() for name in args.structure.split(",")
                  if name.strip()]
    if not structures:
        die("--structure must name at least one structure")
    unknown = [name for name in structures if name not in STRUCTURES]
    if unknown:
        die("unsupported structures: " + ", ".join(unknown)
            + "; choose from " + ", ".join(STRUCTURES))
    if len(set(structures)) != len(structures):
        die("--structure must not repeat a structure")
    if args.length <= 0:
        die("--length must be positive")
    if args.population < 2:
        die("--population must be at least 2")
    if args.generations < 0:
        die("--generations must not be negative")

    instructions = document.get("instructions") or {}
    if not instructions:
        die("structure map has no instructions")
    modes = sorted(instructions)
    maxima = {}
    for structure in structures:
        maxima[structure] = max(
            entry["activation"][structure]
            for entry in instructions.values())
        if maxima[structure] <= 0:
            die(f"structure {structure!r} has no activation above baseline")
    normalised = {
        mode: {structure: instructions[mode]["activation"][structure]
               / maxima[structure] for structure in structures}
        for mode in modes
    }

    def objective(genes):
        # Each gene is an index into ``modes`` and contributes one instruction
        # to the repeated sequence. The mean of per-structure normalised
        # activations keeps every objective in [0, 1] and avoids comparing raw
        # units (events vs input bits).
        chosen_modes = [modes[gene] for gene in genes]
        return tuple(
            sum(normalised[mode][structure] for mode in chosen_modes)
            / len(chosen_modes)
            for structure in structures)

    result = run_nsga2(
        objective, genome_length=args.length, gene_space=len(modes),
        population_size=args.population, generations=args.generations,
        seed=args.seed, crossover_rate=args.crossover,
        mutation_rate=args.mutation)
    if not result.pareto:
        die("NSGA-II produced an empty Pareto front")

    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    target_name = "+".join(structures)
    candidates = []
    for index, individual in enumerate(result.pareto[:args.max_candidates]):
        source = outdir / f"candidate-{index:03d}.c"
        sequence = [modes[gene] for gene in individual.genes]
        source.write_text(sequence_candidate_source(
            target_name, sequence, args.iterations))
        candidates.append({
            "genes": list(individual.genes),
            "sequence": sequence,
            "objectives": {structure: value for structure, value
                           in zip(structures, individual.objectives)},
            "objectives_vector": list(individual.objectives),
            "source": str(source),
        })

    knee = knee_point(result.pareto)
    knee_entry = next(entry for entry in candidates
                      if tuple(entry["genes"]) == knee.genes) \
        if knee is not None else candidates[0]

    validation = None
    if args.validate:
        knee_source = Path(knee_entry["source"])
        guest = compile_guest(knee_source, outdir / "bin" / "knee", args.cc)
        dumps = run_guest(args.gem5.resolve(), outdir / "run", guest,
                          str(args.iterations), "DONE")
        baseline_guest = compile_guest(
            PROBE_SOURCE, outdir / "bin" / "structural_probe", args.cc)
        baseline_dumps = run_guest(args.gem5.resolve(), outdir / "baseline",
                                   baseline_guest,
                                   f"baseline {args.iterations}", "PASS")
        stats = dumps[-1]
        raw = counters_from_dump(stats)
        baseline_raw = counters_from_dump(baseline_dumps[-1])
        net, clamped = subtract_baseline(raw, baseline_raw)
        baseline_coverage = coverage_from_dump(baseline_dumps[-1])
        coverage = coverage_from_dump(stats)
        activation = activation_from_net(net)
        for structure in structures:
            if activation[structure] <= 0:
                die(f"knee point has no net activation for {structure}: "
                    f"{activation[structure]}")
        validation = {
            "candidate": knee_entry,
            "candidate_binary": str(guest),
            "raw": raw,
            "net": net,
            "activation": activation,
            "clamped": clamped,
            "coverage": coverage,
            "baseline_coverage": baseline_coverage,
        }

    report = {
        "schema": "autousens.pareto_set.v1",
        "map": str(map_path),
        "structures": structures,
        "gene_space": modes,
        "length": args.length,
        "population": args.population,
        "generations": args.generations,
        "seed": args.seed,
        "crossover_rate": args.crossover,
        "mutation_rate": (args.mutation if args.mutation is not None
                          else 1.0 / args.length),
        "evaluations": result.evaluations,
        "pareto_size": len(result.pareto),
        "pareto": candidates,
        "knee": knee_entry,
        "validation": validation,
    }
    path = outdir / "pareto_set.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"pareto structures={'+'.join(structures)} "
          f"size={len(result.pareto)} evaluations={result.evaluations}")
    for entry in candidates[:min(len(candidates), 8)]:
        objectives = " ".join(
            f"{structure}={entry['objectives'][structure]:.4f}"
            for structure in structures)
        print(f"  {','.join(entry['sequence']):40s} {objectives}")
    print(f"knee: {','.join(knee_entry['sequence'])}")
    if validation is not None:
        for structure in structures:
            print(f"validated {structure}={validation['coverage'][structure]:.6f} "
                  f"baseline={validation['baseline_coverage'][structure]:.6f}")
    print(f"pareto set: {path}")
    return report, path


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
    structures = [name.strip() for name in args.structure.split(",")
                  if name.strip()]
    if not structures:
        die("--structure must name at least one structure")
    if args.weights:
        weights = [float(part) for part in args.weights.split(",")]
        if len(weights) != len(structures):
            die("--weights must have one value per --structure")
        if any(weight <= 0 for weight in weights):
            die("--weights must be positive")
    else:
        weights = [1.0] * len(structures)
    if args.top <= 0:
        die("--top must be positive")
    # Greedy weighted aggregation: visit structures from highest weight to
    # lowest and take their best unused instruction(s).  Activations are
    # normalised per structure because the units differ between structures.
    chosen = []
    seen_weights = {}
    for structure in structures:
        seen_weights[structure] = seen_weights.get(structure, 0) + 1
    order = sorted(range(len(structures)),
                   key=lambda index: (-weights[index] / seen_weights[structures[index]],
                                      index))
    for index in order:
        structure = structures[index]
        ranked = rank_for_structure(document, structure)
        normaliser = max((entry["activation"][structure]
                          for entry in document["instructions"].values()),
                         default=0.0)
        if normaliser <= 0:
            die(f"structure {structure!r} has no activation above baseline")
        for mode, entry in ranked[:args.top]:
            if mode not in chosen:
                chosen.append(mode)
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    source = outdir / "candidate.c"
    source.write_text(candidate_source("+".join(structures), chosen,
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
        "structure": "+".join(structures),
        "structures": structures,
        "weights": weights,
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
    print(f"target={'+'.join(structures)} chosen={','.join(chosen)}")
    for structure in structures:
        print(f"coverage[{structure}]={report['coverage'][structure]:.6f} "
              f"baseline={report['baseline_coverage'][structure]:.6f} "
              f"net_activation={report['activation'][structure]:.0f}")
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
    target_parser.add_argument("--structure", required=True,
                               help="comma-separated structures, e.g. l1d,alu")
    target_parser.add_argument("--weights", default="",
                               help="comma-separated weights, one per structure")
    target_parser.add_argument("--top", type=int, default=1,
                               help="number of instructions to compose")
    target_parser.add_argument("--outdir", type=Path, required=True)

    pareto_parser = sub.add_parser(
        "pareto", help="generate an NSGA-II Pareto set of sequences")
    common(pareto_parser)
    pareto_parser.add_argument("--map", type=Path, required=True)
    pareto_parser.add_argument("--structure", required=True,
                               help="comma-separated structures, e.g. l1d,alu")
    pareto_parser.add_argument("--length", type=int, default=4,
                               help="instructions per repeated sequence")
    pareto_parser.add_argument("--population", type=int, default=32)
    pareto_parser.add_argument("--generations", type=int, default=20)
    pareto_parser.add_argument("--seed", type=int, default=42)
    pareto_parser.add_argument("--crossover", type=float, default=0.9)
    pareto_parser.add_argument("--mutation", type=float, default=None)
    pareto_parser.add_argument("--max-candidates", type=int, default=32,
                               help="maximum Pareto members written as C")
    pareto_parser.add_argument("--validate", action="store_true",
                               help="run the knee point in gem5 and require it"
                                    " to beat the baseline for every structure")
    pareto_parser.add_argument("--outdir", type=Path, required=True)

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
    elif args.command == "pareto":
        pareto(args)
    else:
        evaluate(args)


if __name__ == "__main__":
    main()
