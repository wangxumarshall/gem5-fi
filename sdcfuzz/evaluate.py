"""Compile and measure the Phase-0 template corpus under gem5.

The evaluator reuses the RF ACE / L1 ACE / FU IBR metrics added earlier: every
template is run inside an m5 work-item window and its activation is attributed
to the structure the template targets.  Phase 1 now also covers the vector/FP
register lane and the FP add/multiply FU classes, so ``fp-add``/``fp-mul`` are
measured instead of being reported as ``none``.
"""

import json
import math
import os
import subprocess
from pathlib import Path

from .generator import (DEFAULT_ITERATIONS, REPS_PER_ITERATION, render_guest)
from .templates import TEMPLATES, TEMPLATE_BY_ID

ROOT = Path(__file__).resolve().parents[1]
GEM5_SRC = ROOT / "CHAOS/gem5"
M5OP = GEM5_SRC / "util/m5/src/abi/arm64/m5op.S"
CONFIG = ROOT / "configs/se/arm_chaos.py"
DEFAULT_GEM5 = GEM5_SRC / "build/ARM_ACE_IBR_AUDIT/gem5.opt"

MEASURABLE_TARGETS = ("alu", "mult", "div", "l1d", "l1i", "fpadd", "fpmul")

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


def gem5_environment():
    env = os.environ.copy()
    conda = Path(env.get("CONDA_PREFIX", Path.home() / "miniconda3/envs/py312"))
    if (conda / "lib").is_dir():
        env["LD_LIBRARY_PATH"] = str(conda / "lib") + ":" + env.get(
            "LD_LIBRARY_PATH", "")
    return env


def stat_dumps(path):
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
        raise RuntimeError(f"no statistics dumps in {path}")
    return dumps


def metric(stats, suffix):
    matches = [value for name, value in stats.items() if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(
            f"statistic *{suffix} matched {len(matches)} fields")
    return matches[0]


def target_activation(target, counters):
    if target == "l1d":
        return counters["l1d_reads"] + counters["l1d_writes"]
    if target == "l1i":
        return counters["l1i_reads"]
    if target == "alu":
        return counters["alu_bits"]
    if target == "mult":
        return counters["mult_bits"]
    if target == "div":
        return counters["div_bits"]
    if target == "fpadd":
        return counters["fpadd_bits"]
    if target == "fpmul":
        return counters["fpmul_bits"]
    return None


def build_guest(cc, source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [cc, "-O2", "-static", "-fno-pie", "-no-pie",
         "-Wall", "-Wextra", "-Werror",
         "-I" + str(GEM5_SRC / "include"), str(source), str(M5OP),
         "-o", str(output)], check=True)
    return output


def run_guest(gem5, outdir, guest):
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "gem5.log").open("w") as log:
        subprocess.run(
            [str(gem5), "--outdir=" + str(outdir), str(CONFIG), "--cpu=O3",
             "--cmd=" + str(guest),
             "--rf_ace", "--rf_ace_granularity=bit", "--l1_ace", "--fu_ibr"],
            stdout=log, stderr=subprocess.STDOUT,
            env=gem5_environment(), check=True)
    text = (outdir / "gem5.log").read_text()
    if "status=PASS" not in text:
        raise RuntimeError(f"{guest}: guest reported FAIL in {outdir}")
    return stat_dumps(outdir / "stats.txt")[-1]


def evaluate_template(template, gem5, workdir, cc, iterations,
                      operand=None):
    source = workdir / f"{template.id}.c"
    rendered, expected = render_guest(template, iterations, operand=operand)
    source.write_text(rendered)
    guest = build_guest(cc, source, workdir / "bin" / template.id)
    stats = run_guest(gem5, workdir / "runs" / template.id, guest)
    counters = {name: metric(stats, suffix)
                for name, suffix in COUNTERS.items()}
    coverage = {name: metric(stats, suffix)
                for name, suffix in RATIO_COUNTERS.items()}
    for name, value in coverage.items():
        if not math.isfinite(value):
            raise RuntimeError(f"{template.id}: non-finite {name} coverage")
    return {
        "title": template.title,
        "target": template.target,
        "injector": template.injector,
        "iterations": iterations,
        "dynamic_ops": iterations * REPS_PER_ITERATION * len(template.body),
        "status": "PASS",
        "expected_checksum": f"{expected:016x}",
        "counters": counters,
        "coverage": coverage,
        "target_activation": target_activation(template.target, counters),
        "note": template.note,
    }


def build_index(gem5=DEFAULT_GEM5, outdir=None, iterations=DEFAULT_ITERATIONS,
                cc=os.environ.get("ARM_CC", "aarch64-linux-gnu-gcc")):
    gem5 = Path(gem5).resolve()
    outdir = Path(outdir or (ROOT / "m5out/sdcfuzz-baseline")).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    entries = {}
    for template in TEMPLATES:
        entries[template.id] = evaluate_template(
            template, gem5, outdir, cc, iterations)
    ranking = {}
    for target in MEASURABLE_TARGETS:
        ranked = sorted(
            ((tid, entry["target_activation"])
             for tid, entry in entries.items() if entry["target"] == target),
            key=lambda item: (-item[1], item[0]),
        )
        ranking[target] = [{"id": tid, "activation": value}
                           for tid, value in ranked]
    index = {
        "schema": "sdcfuzz.phase0.corpus_index.v1",
        "gem5": str(gem5),
        "iterations": iterations,
        "template_count": len(entries),
        "measurable_targets": list(MEASURABLE_TARGETS),
        "unmeasured_targets": sorted({entry["target"] for entry in
                                      entries.values()
                                      if entry["target"] not in
                                      MEASURABLE_TARGETS}),
        "templates": entries,
        "ranking": ranking,
    }
    path = outdir / "corpus_index.json"
    path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    return index, path, outdir


def summarize(index):
    lines = []
    for target in MEASURABLE_TARGETS:
        ranked = index["ranking"][target]
        if not ranked:
            continue
        top = ranked[0]
        lines.append(f"{target:4s} best={top['id']:16s} "
                     f"activation={top['activation']:.0f}")
    unmeasured = index["unmeasured_targets"]
    if unmeasured:
        lines.append("no structure metric: "
                     + ", ".join(sorted(tid for tid, entry in
                                        index["templates"].items()
                                        if entry["target"] in unmeasured)))
    return "\n".join(lines)
