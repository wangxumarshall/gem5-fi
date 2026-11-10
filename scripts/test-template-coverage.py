#!/usr/bin/env python3
"""Real-gem5 proof that every base-template instruction has an ACE/IBR metric.

Phase 1 requires ACE/IBR coverage for the instructions used by the 19 base
templates.  This regression:

1. checks the static contract in ``sdcfuzz/coverage.py`` is complete
   (every Op.kind used by any template is mapped, every counter exists);
2. compiles and runs all 19 templates in gem5 with RF ACE / vector ACE /
   L1 ACE / FU IBR enabled;
3. asserts every metric required by each template is non-zero, so an
   instruction form cannot silently fall through the instrumentation;
4. writes ``coverage_matrix.json`` with the measured matrix.

No predicted values: every assertion below is against a live stats.txt.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sdcfuzz import coverage  # noqa: E402
from sdcfuzz.evaluate import (  # noqa: E402
    COUNTERS,
    DEFAULT_GEM5,
    build_index,
)
from sdcfuzz.templates import TEMPLATES  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gem5", default=str(DEFAULT_GEM5))
    parser.add_argument("--outdir", default=str(ROOT / "m5out/coverage-matrix"))
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--cc", default=os.environ.get(
        "ARM_CC", "aarch64-linux-gnu-gcc"))
    args = parser.parse_args()

    gem5 = Path(args.gem5).resolve()
    if not gem5.is_file():
        raise SystemExit(f"gem5 binary not found: {gem5}")

    # --- static contract completeness, before spending gem5 time ---
    unknown = coverage.missing_from_table(TEMPLATES)
    assert not unknown, f"Op kinds without ACE/IBR mapping: {unknown}"
    for metric, counters in coverage.METRIC_COUNTERS.items():
        missing = [counter for counter in counters if counter not in COUNTERS]
        assert not missing, (metric, "unknown counters", missing)
    for template in TEMPLATES:
        assert coverage.template_metrics(template), template.id
    print(f"static contract: {len(TEMPLATES)} templates, "
          f"{len(coverage.OP_METRICS)} op kinds, "
          f"{len(coverage.METRIC_COUNTERS)} metric groups")

    # --- real runs ---
    print(f"gem5: {gem5}")
    index, path, run_dir = build_index(
        gem5=gem5, outdir=Path(args.outdir), iterations=args.iterations,
        cc=args.cc)
    assert index["template_count"] == len(TEMPLATES), index["template_count"]

    matrix = {}
    for template in TEMPLATES:
        entry = index["templates"][template.id]
        counters = entry["counters"]
        failures = coverage.coverage_failures(template, counters)
        assert not failures, (template.id, failures)
        required = coverage.template_metrics(template)
        matrix[template.id] = {
            "target": template.target,
            "required": required,
            "counters": counters,
            "coverage": entry["coverage"],
            "target_activation": entry["target_activation"],
        }
        measured = " ".join(
            f"{name}="
            + "/".join(f"{counters[counter]:.0f}"
                       for counter in coverage.METRIC_COUNTERS[name])
            for name in required)
        print(f"{template.id:16s} target={template.target:6s} {measured}")

    # FP templates specifically prove the new vector-ACE + FP-IBR path.
    for template_id, metric_name in (("fp-add", "fpadd"),
                                     ("fp-mul", "fpmul")):
        counters = matrix[template_id]["counters"]
        vec = sum(counters[name] for name in coverage.METRIC_COUNTERS["vec"])
        fp_bits = sum(counters[name]
                      for name in coverage.METRIC_COUNTERS[metric_name])
        assert vec > 0, (template_id, "vec ACE", counters)
        assert fp_bits > 0, (template_id, metric_name, counters)
        print(f"{template_id}: vec accesses={vec:.0f} "
              f"{metric_name} input bits={fp_bits:.0f}")

    report = {
        "schema": "sdcfuzz.phase1.coverage_matrix.v1",
        "gem5": str(gem5),
        "iterations": args.iterations,
        "template_count": len(TEMPLATES),
        "op_metrics": {kind: list(metrics)
                       for kind, metrics in coverage.OP_METRICS.items()},
        "metric_counters": {metric: list(counters)
                            for metric, counters
                            in coverage.METRIC_COUNTERS.items()},
        "templates": matrix,
        "corpus_index": str(path),
        "runs": str(run_dir),
    }
    out = Path(args.outdir) / "coverage_matrix.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"all {len(TEMPLATES)} templates cover every mapped instruction form")
    print(f"matrix: {out}")


if __name__ == "__main__":
    main()
