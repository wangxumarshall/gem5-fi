#!/usr/bin/env python3
"""End-to-end regression for the AutoµSens structure map and targeting tool.

Runs the real gem5 binary on real AArch64 probe guests; every assertion below
is checked against measured statistics, not against predictions.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/autousens.py"


def call(command, expect=0):
    result = subprocess.run(command, text=True, capture_output=True,
                            env=os.environ.copy())
    if expect is not None and result.returncode != expect:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise AssertionError(f"command failed ({result.returncode}): "
                             + " ".join(map(str, command)))
    return result


def activation(instruction):
    return instruction["activation"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gem5", default=str(
        ROOT / "CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt"))
    parser.add_argument("--outdir", default=str(ROOT / "m5out/autousens-test"))
    parser.add_argument("--iterations", type=int, default=60)
    args = parser.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    gem5 = Path(args.gem5).resolve()
    if not gem5.is_file():
        raise SystemExit(f"gem5 binary not found: {gem5}")
    print(f"gem5: {gem5}")

    mapdir = outdir / "map"
    call([sys.executable, str(TOOL), "map", "--gem5", str(gem5),
          "--outdir", str(mapdir), "--iterations", str(args.iterations)])
    document = json.loads((mapdir / "structure_map.json").read_text())
    instructions = document["instructions"]
    assert document["schema"] == "autousens.structure_map.v1"
    assert "baseline" not in instructions
    expected_modes = {"add", "sub", "and", "orr", "eor", "mul", "madd",
                      "udiv", "ldr", "str", "ldxr"}
    assert set(instructions) == expected_modes, set(instructions)

    # --- per-structure attribution, each compared within its own units ---
    alu_modes = ["add", "sub", "and", "orr", "eor"]
    for mode in alu_modes:
        value = activation(instructions[mode])["alu"]
        assert value > 100000, (mode, "alu", value)
    alu_reference = activation(instructions["add"])["alu"]
    for mode in ["mul", "madd", "ldr", "str", "ldxr"]:
        noise = activation(instructions[mode])["alu"]
        assert noise < 0.01 * alu_reference, (mode, "alu noise", noise)
    print("alu: " + " ".join(f"{m}={activation(instructions[m])['alu']:.0f}"
                             for m in alu_modes))

    for mode in ["mul", "madd"]:
        mult = activation(instructions[mode])["mult"]
        assert mult > 500000, (mode, "mult", mult)
    for mode in ["add", "sub", "ldr", "str"]:
        noise = activation(instructions[mode])["mult"]
        assert noise < 0.01 * activation(instructions["mul"])["mult"], (
            mode, "mult noise", noise)
    print(f"mult: mul={activation(instructions['mul'])['mult']:.0f} "
          f"madd={activation(instructions['madd'])['mult']:.0f}")

    div = activation(instructions["udiv"])["div"]
    assert div > 300000, ("udiv", div)
    for mode in ["mul", "add", "ldr"]:
        noise = activation(instructions[mode])["div"]
        assert noise < 0.01 * div, (mode, "div noise", noise)
    print(f"div: udiv={div:.0f}; mul={activation(instructions['mul'])['div']:.0f}"
          f" (noise)")

    for mode in ["ldr", "ldxr", "str"]:
        l1d = activation(instructions[mode])["l1d"]
        assert l1d > 3000, (mode, "l1d", l1d)
    for mode in ["add", "sub", "and", "orr", "eor", "mul", "madd"]:
        noise = activation(instructions[mode])["l1d"]
        assert noise < 100, (mode, "l1d noise", noise)
    per_instr = instructions["ldr"]["activation_per_instruction"]["l1d"]
    assert 0.95 < per_instr < 1.05, per_instr
    print(f"l1d: ldr={activation(instructions['ldr'])['l1d']:.0f} "
          f"ldxr={activation(instructions['ldxr'])['l1d']:.0f} "
          f"str={activation(instructions['str'])['l1d']:.0f} "
          f"(ldr per instruction={per_instr:.3f})")

    for mode, entry in instructions.items():
        assert activation(entry)["rf"] > 0, (mode, "rf must be active")
    print(f"rf: " + " ".join(f"{m}={activation(instructions[m])['rf']:.0f}"
                             for m in ("add", "ldr", "str")))

    # --- reverse targeting and evaluation ---
    targetdir = outdir / "target-l1d"
    call([sys.executable, str(TOOL), "target", "--gem5", str(gem5),
          "--map", str(mapdir / "structure_map.json"),
          "--structure", "l1d", "--top", "2",
          "--outdir", str(targetdir), "--iterations", str(args.iterations)])
    report = json.loads((targetdir / "candidate_report.json").read_text())
    assert "ldr" in report["chosen"], report["chosen"]
    source = (targetdir / "candidate.c").read_text()
    assert "ldr x8, [%[buf]]" in source
    assert report["net"]["l1d_reads"] > 0, report["net"]
    assert (report["coverage"]["l1d"]
            > report["baseline_coverage"]["l1d"]), report
    print(f"target l1d: chosen={report['chosen']} "
          f"coverage={report['coverage']['l1d']:.6f} "
          f"baseline={report['baseline_coverage']['l1d']:.6f}")

    multdir = outdir / "target-mult"
    call([sys.executable, str(TOOL), "target", "--gem5", str(gem5),
          "--map", str(mapdir / "structure_map.json"),
          "--structure", "mult", "--top", "1",
          "--outdir", str(multdir), "--iterations", str(args.iterations)])
    mult_report = json.loads((multdir / "candidate_report.json").read_text())
    assert mult_report["chosen"][0] in ("mul", "madd"), mult_report["chosen"]
    assert (mult_report["coverage"]["mult"]
            > mult_report["baseline_coverage"]["mult"]), mult_report
    print(f"target mult: chosen={mult_report['chosen']} "
          f"net_mult={mult_report['activation']['mult']:.0f}")

    evaluated = call([sys.executable, str(TOOL), "evaluate",
                      "--dir", str(targetdir / "run"),
                      "--baseline-dir", str(targetdir / "baseline")])
    evaluated = json.loads(evaluated.stdout)
    assert evaluated["net"]["l1d_reads"] > 0, evaluated["net"]
    print(f"evaluate: l1d net reads={evaluated['net']['l1d_reads']:.0f}")

    # --- failure modes must be loud, not silent ---
    bad_structure = call([sys.executable, str(TOOL), "target",
                          "--map", str(mapdir / "structure_map.json"),
                          "--structure", "tlb", "--outdir",
                          str(outdir / "bad")], expect=None)
    assert bad_structure.returncode != 0, "unknown structure must fail"
    missing_baseline = call([sys.executable, str(TOOL), "map",
                             "--gem5", str(gem5), "--outdir",
                             str(outdir / "bad-map"), "--modes", "add"],
                            expect=None)
    assert missing_baseline.returncode != 0, "map without baseline must fail"
    print("error handling: unknown structure and missing baseline both fail")
    print(f"outputs: {outdir}")


if __name__ == "__main__":
    main()
