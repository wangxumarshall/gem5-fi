#!/usr/bin/env python3
"""End-to-end regression for the local sdcfuzz Phase-0 baseline.

Real gem5 runs only: every template is compiled for AArch64, executed inside
an m5 work-item window, and checked against the checksum computed by the
Python reference interpreter.  The final step injects one CHAOSReg fault into
a generated guest and classifies the outcome with ``tools/classify.py``.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from classify import classify_run, extract_checksum  # noqa: E402
from sdcfuzz import operand_heuristic as heuristic  # noqa: E402
from sdcfuzz.evaluate import (  # noqa: E402
    CONFIG, COUNTERS, DEFAULT_GEM5, build_guest, evaluate_template,
    gem5_environment, metric, run_guest)
from sdcfuzz.generator import render_guest  # noqa: E402
from sdcfuzz.templates import TEMPLATES, TEMPLATE_BY_ID  # noqa: E402


def run_with_args(gem5, outdir, guest, extra, timeout):
    outdir.mkdir(parents=True, exist_ok=True)
    command = [str(gem5), "--outdir=" + str(outdir), str(CONFIG),
               "--cpu=O3", "--cmd=" + str(guest), *extra]
    timed_out = False
    with (outdir / "gem5.log").open("w") as log:
        try:
            completed = subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT,
                env=gem5_environment(), timeout=timeout)
            returncode, timed_out = completed.returncode, False
        except subprocess.TimeoutExpired:
            returncode, timed_out = -1, True
    text = (outdir / "gem5.log").read_text()
    return returncode, timed_out, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gem5", default=str(DEFAULT_GEM5))
    parser.add_argument("--outdir", default=str(ROOT / "m5out/sdcfuzz-baseline"))
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--cc", default=os.environ.get("ARM_CC",
                                                      "aarch64-linux-gnu-gcc"))
    args = parser.parse_args()
    gem5 = Path(args.gem5).resolve()
    if not gem5.is_file():
        raise SystemExit(f"gem5 binary not found: {gem5}")
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"gem5: {gem5}\niterations: {args.iterations}")

    entries = {}
    for template in TEMPLATES:
        entry = evaluate_template(template, gem5, outdir, args.cc,
                                  args.iterations)
        entries[template.id] = entry
        if template.target in ("alu", "mult", "div", "l1d", "l1i",
                               "fpadd", "fpmul"):
            activation = entry["target_activation"]
            assert activation > 0, (template.id, template.target, activation)
        else:
            assert entry["target_activation"] is None, template.id
        assert entry["counters"]["rf_reads"] > 0, template.id
        profile = " ".join(
            f"{structure}={entry['coverage'][structure]:.4f}"
            for structure in ("rf", "vec", "l1i", "l1d", "alu", "mult",
                              "div", "fpadd", "fpmul")
            if entry["coverage"][structure] > 0)
        print(f"{template.id:16s} target={template.target:5s} "
              f"activation={entry['target_activation']} {profile}")
    assert len(entries) == 19, len(entries)

    # Determinism: the same guest under the same build must reproduce its
    # target activation exactly.
    again = evaluate_template(TEMPLATE_BY_ID["mul64"], gem5, outdir, args.cc,
                              args.iterations)
    assert again["target_activation"] == entries["mul64"]["target_activation"]
    print(f"reproducibility: mul64 activation stable at "
          f"{again['target_activation']:.0f}")

    # The LOCAL heuristic changes the operand and the change must reach the
    # hardware: the checksum differs from the default template while the guest
    # still passes.  This is not the upstream D13 baseline (see
    # sdcfuzz/operand_heuristic.py); the real D13 is reproduced separately.
    template = TEMPLATE_BY_ID["alu-add-carry"]
    operand = heuristic.choose_operand(0x00FF00FF00FF00FF, count=64)
    variant_source, variant_expected = render_guest(template,
                                                    args.iterations,
                                                    operand=operand)
    variant = outdir / "heuristic" / f"{template.id}-heuristic.c"
    variant.parent.mkdir(parents=True, exist_ok=True)
    variant.write_text(variant_source)
    guest = build_guest(args.cc, variant, outdir / "bin" / "alu-heuristic")
    stats = run_guest(gem5, outdir / "runs" / "alu-heuristic", guest)
    variant_alu = metric(stats, COUNTERS["alu_bits"])
    default_alu = entries[template.id]["counters"]["alu_bits"]
    assert variant_expected != int(entries[template.id]["expected_checksum"], 16)
    assert variant_alu > 0
    print(f"local heuristic: operand=0x{operand:016x} "
          f"carry_chain={heuristic.carry_chain(operand, 0x00FF00FF00FF00FF)} "
          f"alu_bits={variant_alu:.0f} (default {default_alu:.0f})")

    # Fault-injection smoke: one CHAOSReg fault must land and be classified.
    golden_log = (outdir / "runs" / "alu-add-carry" / "gem5.log").read_text()
    golden = extract_checksum(golden_log)
    assert golden, "golden run produced no checksum"
    fi_dir = outdir / "fi-chaos-reg"
    returncode, timed_out, text = run_with_args(
        gem5, fi_dir, outdir / "bin" / "alu-add-carry",
        ["--chaos_reg", "--probability=1.0", "--max_faults=1",
         "--target_reg_idx=12"], timeout=120)
    injections = fi_dir / "fault_injections.log"
    faults = 0
    if injections.is_file():
        faults = sum(1 for line in injections.read_text().splitlines()
                     if "FaultType:" in line)
    category, reason = classify_run(text, "", returncode, faults, golden,
                                    timed_out=timed_out)
    assert faults == 1, (faults, text[-500:])
    assert category in ("SDC", "Masked", "Crash", "Hang"), category
    assert category != "Inactive", reason
    print(f"fi smoke: chaos_reg faults={faults} -> {category} ({reason})")

    summary = {
        "schema": "sdcfuzz.phase0.baseline_test.v1",
        "gem5": str(gem5),
        "iterations": args.iterations,
        "templates": len(entries),
        "local_heuristic_operand": f"0x{operand:016x}",
        "fi_category": category,
        "fi_faults": faults,
        "entries": entries,
    }
    path = outdir / "baseline_test.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"\nphase-0 baseline: 19/19 templates PASS, FI loop {category}")
    print(f"report: {path}")


if __name__ == "__main__":
    main()
