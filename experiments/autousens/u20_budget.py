"""Budget-locked (4096-instruction) version of the u20 comparison.

The one-pass experiment (``u20_templates.py``) is the faithful execution of each
upstream probe, but its 15-200 instruction ROI is too short for the L1 ACE
line lifetime (``aceLineCycles`` stays zero when a line never dies inside the
window) and for the SAD sampling window.  This module repeats the template
program in one m5 work item until the ROI reaches ~4096 issued instructions,
and runs the AutoµSens arm with the standard 16-group/60-iteration body
(4*16*60 = 3840 body instructions plus loop control).  Both arms therefore have
comparable ACE/SAD windows; the cost is that later template passes run with the
architectural state left by earlier passes (the first pass is the faithful one,
reported separately by ``u20_templates.py``).

D13 is applied to the AutoµSens arm only, with an explicit ``auto-load``
control (x12=3 loaded per iteration).  The D13-vs-load delta therefore isolates
operand values, not the operand-load instruction.  No template/D13 cell is
built because no seed reads x12 before writing it (see ``u20_templates``).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))

from autousens import arms, d13, u20_templates as base  # noqa: E402
from sdcfuzz import seed_templates  # noqa: E402
from sdcfuzz.target_oracle import render_candidate  # noqa: E402

TOOL = base.TOOL
GEM5 = base.GEM5
BUDGET = 4096
AUTO_ITERATIONS = 60
AUTO_GROUPS = 16
TEMPLATE_COST_OVERHEAD = 2

PRIMARY = base.PRIMARY
FOCUS = base.FOCUS
MAPPINGS = base.MAPPINGS
MAPPING_BY_SEED = base.MAPPING_BY_SEED


LOOP_WRAPPER = base.WRAPPER_ASM.replace(
    "    mov     x0, #0\n    mov     x1, #0\n    bl      probe_entry",
    "    mov     x0, #0\n"
    "    mov     x1, #0\n"
    "    mov     x29, #@K@\n"
    "1:\n"
    "    bl      probe_entry\n"
    "    subs    x29, x29, #1\n"
    "    b.ne    1b")
if LOOP_WRAPPER == base.WRAPPER_ASM:
    raise RuntimeError("loop wrapper substitution did not apply")


def build_loop_template(seed, outdir, cc, objects, iterations):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    bindir = outdir / "bin"
    bindir.mkdir(exist_ok=True)
    # compile_objects writes the shared no-loop objects; rebuild wrapper.o with
    # the loop body for this run.
    objects = dict(objects)
    wrapper_s = bindir / "wrapper.S"
    wrapper_s.write_text(LOOP_WRAPPER.replace("@K@", str(iterations)))
    wrapper_o = bindir / "wrapper.o"
    import subprocess

    subprocess.run([cc, "-c", str(wrapper_s), "-o", str(wrapper_o)],
                   check=True, capture_output=True, text=True)
    probe = outdir / "probe.S"
    probe.write_text(f'#include "{seed.path.name}"\n    ret\n')
    probe_o = outdir / "probe.o"
    subprocess.run([cc, "-c", "-I" + str(base.SEEDS_DIR),
                    "-D_start=probe_entry", str(probe), "-o", str(probe_o)],
                   check=True, capture_output=True, text=True)
    guest = outdir / "guest"
    subprocess.run([cc, "-static", "-nostdlib", "-no-pie",
                    str(wrapper_o), str(probe_o),
                    str(objects["trampoline.o"]), str(objects["m5op.o"]),
                    "-o", str(guest)], check=True, capture_output=True, text=True)
    return probe, guest


def one_pass_insts(seed_id):
    path = (ROOT / "m5out/autousens-eval/2026-11-17-u20/templates" /
            seed_id / "row.json")
    if not path.is_file():
        raise RuntimeError(f"missing one-pass baseline row: {path}")
    return float(json.loads(path.read_text())["meta"]["sim_insts"])


def run_loop_template(seed, root, cc, objects, gem5, timeout):
    base_dir = Path(root) / "templates" / seed.id
    row_path = base_dir / "row.json"
    if row_path.is_file():
        return json.loads(row_path.read_text())

    initial_k = max(1, int(round(BUDGET / (one_pass_insts(seed.id)
                                            + TEMPLATE_COST_OVERHEAD))))
    attempts = []
    k = initial_k
    best = None
    for _attempt in range(4):
        probe, guest = build_loop_template(seed, base_dir / f"k{k}", cc,
                                           objects, k)
        run_dir = base_dir / f"k{k}" / "run"
        outcome = base.run_gem5(gem5, run_dir, guest, 0, timeout)
        stats = run_dir / "stats.txt"
        if outcome["error"] or outcome["returncode"] != 0 or not stats.is_file():
            raise RuntimeError(f"{seed.id}: loop template failed: {outcome}")
        _doc, flat, meta = base.metric_row(stats)
        attempts.append({"k": k, "sim_insts": meta["sim_insts"],
                         "cycles": meta["cycles"]})
        candidate = (k, probe, guest, outcome, flat, meta)
        if best is None or abs(meta["sim_insts"] - BUDGET) < abs(
                best[5]["sim_insts"] - BUDGET):
            best = candidate
        if abs(meta["sim_insts"] - BUDGET) <= 0.08 * BUDGET:
            break
        next_k = max(1, int(round(k * BUDGET / max(1.0, meta["sim_insts"]))))
        if next_k == k:
            break
        k = next_k
    final_k, probe, guest, outcome, flat, meta = best
    row = {
        "kind": "template-loop",
        "seed": seed.id,
        "sha256": seed.sha256,
        "source": str(probe),
        "guest": str(guest),
        "mapping": MAPPING_BY_SEED[seed.id].__dict__,
        "iterations": final_k,
        "attempts": attempts,
        "outcome": outcome,
        "meta": meta,
        "flat": flat,
    }
    row_path.write_text(json.dumps(row, indent=2, sort_keys=True))
    return row


def run_auto(seed, mapping, document, variant, root, cc, gem5, timeout):
    outdir = Path(root) / "cells" / seed.id / variant
    row_path = outdir / "row.json"
    if row_path.is_file():
        return json.loads(row_path.read_text())
    mode, skipped = base.select_auto_mode(document, mapping.auto)
    sequence = base.body_for(mode)
    if variant == "auto-default":
        operands = None
    elif variant == "auto-load":
        operands = [3] * AUTO_ITERATIONS
    elif variant == "auto-d13":
        operands = d13.operand_stream(AUTO_ITERATIONS)[:AUTO_ITERATIONS]
    else:
        raise ValueError(variant)
    source_text = render_candidate(mapping.auto, sequence, AUTO_ITERATIONS,
                                   TOOL.MODE_ASM, groups=AUTO_GROUPS,
                                   operands=operands)
    source_text = base.stabilise_expected(source_text)
    source, guest = base.build_auto_guest(outdir, source_text, cc)
    outcome = base.run_gem5(gem5, outdir / "run", guest, AUTO_ITERATIONS, timeout)
    stats = outdir / "run" / "stats.txt"
    if outcome["error"] or outcome["status"] != "PASS" or not stats.is_file():
        raise RuntimeError(f"{seed.id}/{variant}: run failed: {outcome}")
    _doc, flat, meta = base.metric_row(stats)
    row = {
        "kind": "auto",
        "seed": seed.id,
        "sha256": seed.sha256,
        "variant": variant,
        "structure": mapping.auto,
        "sequence": sequence,
        "mode": mode,
        "skipped": skipped,
        "iterations": AUTO_ITERATIONS,
        "groups": AUTO_GROUPS,
        "operands": operands,
        "source": str(source),
        "guest": str(guest),
        "mapping": mapping.__dict__,
        "outcome": outcome,
        "meta": meta,
        "flat": flat,
    }
    row_path.write_text(json.dumps(row, indent=2, sort_keys=True))
    return row


def run_seed(seed, root, document, cc, objects, gem5, timeout):
    template = run_loop_template(seed, root, cc, objects, gem5, timeout)
    auto_default = run_auto(seed, MAPPING_BY_SEED[seed.id], document,
                            "auto-default", root, cc, gem5, timeout)
    auto_load = run_auto(seed, MAPPING_BY_SEED[seed.id], document,
                         "auto-load", root, cc, gem5, timeout)
    auto_d13 = run_auto(seed, MAPPING_BY_SEED[seed.id], document,
                        "auto-d13", root, cc, gem5, timeout)
    return template, auto_default, auto_load, auto_d13


# --------------------------------------------------------------------------
# Summary / CSV / tables
# --------------------------------------------------------------------------
def compact(row):
    return {
        "kind": row["kind"],
        "seed": row["seed"],
        "variant": row.get("variant"),
        "structure": row.get("structure"),
        "sequence": row.get("sequence"),
        "mode": row.get("mode"),
        "iterations": row.get("iterations"),
        "groups": row.get("groups"),
        "attempts": row.get("attempts"),
        "meta": row["meta"],
        "outcome": {
            "status": row["outcome"].get("status"),
            "returncode": row["outcome"].get("returncode"),
            "error": row["outcome"].get("error"),
            "elapsed_s": row["outcome"].get("elapsed_s"),
        },
        "flat": row["flat"],
    }


def compare(template, auto_default, auto_load, auto_d13, primary):
    def value(row):
        return row["flat"].get(primary)

    t, a = value(template), value(auto_default)
    load, directed = value(auto_load), value(auto_d13)
    diffs = sorted(key for key in set(auto_load["flat"]) | set(auto_d13["flat"])
                   if auto_load["flat"].get(key) != auto_d13["flat"].get(key))
    return {
        "primary": primary,
        "template": t,
        "auto_default": a,
        "auto_load": load,
        "auto_d13": directed,
        "template_over_auto": base.ratio(t, a),
        "template_over_auto_load": base.ratio(t, load),
        "d13_over_load": base.ratio(directed, load),
        "d13_delta": (directed - load) if (load is not None
                                           and directed is not None) else None,
        "d13_changed_metrics": len(diffs),
        "d13_changed_keys": diffs,
    }


def build_summary(root, run_id, protocol):
    cells = {}
    for seed in seed_templates.SEEDS:
        template = json.loads((Path(root) / "templates" / seed.id /
                               "row.json").read_text())
        auto_default = json.loads((Path(root) / "cells" / seed.id /
                                   "auto-default" / "row.json").read_text())
        auto_load = json.loads((Path(root) / "cells" / seed.id /
                                "auto-load" / "row.json").read_text())
        auto_d13 = json.loads((Path(root) / "cells" / seed.id /
                               "auto-d13" / "row.json").read_text())
        mapping = MAPPING_BY_SEED[seed.id]
        primary = PRIMARY[mapping.measured]
        cells[seed.id] = {
            "seed": seed.id,
            "sha256": seed.sha256,
            "mapping": mapping.__dict__,
            "template": compact(template),
            "auto_default": compact(auto_default),
            "auto_load": compact(auto_load),
            "auto_d13": compact(auto_d13),
            "comparison": compare(template, auto_default, auto_load,
                                  auto_d13, primary),
        }
    aggregates = {}
    for mapping in MAPPINGS:
        key = mapping.measured
        rows = [cells[m.seed]["comparison"] for m in MAPPINGS
                if m.measured == key]
        ratios = [row["template_over_auto"] for row in rows
                  if row["template_over_auto"] is not None]
        aggregates[key] = {
            "n": len(rows),
            "primary": PRIMARY[key],
            "template_wins": sum(1 for value in ratios if value > 1.0),
            "auto_wins": sum(1 for value in ratios if value < 1.0),
            "median_template_over_auto": base.median(ratios),
            "median_d13_over_load": base.median(
                [row["d13_over_load"] for row in rows
                 if row["d13_over_load"] is not None]),
        }
    summary = {
        "schema": "autousens.u20.budget.v1",
        "run_id": run_id,
        "protocol": protocol,
        "budget": BUDGET,
        "auto": {"iterations": AUTO_ITERATIONS, "groups": AUTO_GROUPS,
                 "body": "top-1 mode x4"},
        "mappings": [mapping.__dict__ for mapping in MAPPINGS],
        "primary": PRIMARY,
        "focus": FOCUS,
        "aggregates": aggregates,
        "cells": cells,
    }
    (Path(root) / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def write_csv(root, summary):
    rows = []
    for seed_id, cell in summary["cells"].items():
        mapping = cell["mapping"]
        for key in ("template", "auto_default", "auto_load", "auto_d13"):
            row = cell[key]
            meta = row["meta"]
            rows.append({
                "seed": seed_id,
                "nominal": mapping["nominal"],
                "measured": mapping["measured"],
                "auto_structure": mapping["auto"],
                "arm": row["kind"],
                "variant": row.get("variant") or "",
                "iterations": row.get("iterations") or "",
                "groups": row.get("groups") or "",
                "sim_insts": meta.get("sim_insts"),
                "cycles": meta.get("cycles"),
                "ipc": meta.get("ipc"),
                "window_consistent": meta.get("window_consistent"),
                **row["flat"],
            })
    keys = sorted({key for row in rows for key in row})
    meta_keys = ["seed", "nominal", "measured", "auto_structure", "arm",
                 "variant", "iterations", "groups", "sim_insts", "cycles",
                 "ipc", "window_consistent"]
    path = Path(root) / "metrics.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=meta_keys
                                + [key for key in keys if key not in meta_keys])
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_tables(root, summary):
    lines = ["# AutoµSens u20 budget-locked tables (4096 instructions)", ""]
    lines += ["## Headline metric", "",
              "| seed | target | template | auto | auto-load | auto+D13 | T/A | T/AL | D13/AL | changed metrics |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for seed in seed_templates.SEEDS:
        comp = summary["cells"][seed.id]["comparison"]
        lines.append(
            f"| {seed.id} | {comp['primary']} | {base.fmt(comp['template'])} | "
            f"{base.fmt(comp['auto_default'])} | {base.fmt(comp['auto_load'])} | "
            f"{base.fmt(comp['auto_d13'])} | "
            f"{base.fmt(comp['template_over_auto'], 4)} | "
            f"{base.fmt(comp['template_over_auto_load'], 4)} | "
            f"{base.fmt(comp['d13_over_load'], 6)} | "
            f"{comp['d13_changed_metrics']} |")
    lines += ["", "## Per measured structure", "",
              "| structure | n | primary | template wins | auto wins | median T/A | median D13/AL |",
              "|---|---:|---|---:|---:|---:|---:|"]
    for key, agg in summary["aggregates"].items():
        lines.append(
            f"| {key} | {agg['n']} | {agg['primary']} | "
            f"{agg['template_wins']} | {agg['auto_wins']} | "
            f"{base.fmt(agg['median_template_over_auto'], 4)} | "
            f"{base.fmt(agg['median_d13_over_load'], 6)} |")
    lines += ["", "## Window / length audit", "",
              "| seed | template iter | template insts | template cycles | auto insts | auto cycles | auto-load insts | auto+D13 insts |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for seed in seed_templates.SEEDS:
        cell = summary["cells"][seed.id]
        t, a = cell["template"], cell["auto_default"]
        load, d = cell["auto_load"], cell["auto_d13"]
        lines.append(
            f"| {seed.id} | {base.fmt(t.get('iterations'), 0)} | "
            f"{base.fmt(t['meta']['sim_insts'], 0)} | "
            f"{base.fmt(t['meta']['cycles'], 0)} | "
            f"{base.fmt(a['meta']['sim_insts'], 0)} | "
            f"{base.fmt(a['meta']['cycles'], 0)} | "
            f"{base.fmt(load['meta']['sim_insts'], 0)} | "
            f"{base.fmt(d['meta']['sim_insts'], 0)} |")
    path = Path(root) / "tables.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def verify(root):
    root = Path(root)
    summary = json.loads((root / "summary.json").read_text())
    problems = []
    if len(summary["cells"]) != 20:
        problems.append("cell count")
    for seed_id, cell in summary["cells"].items():
        for key in ("template", "auto_default", "auto_load", "auto_d13"):
            row = cell[key]
            if row["outcome"]["error"]:
                problems.append(f"{seed_id}/{key}: error")
            if key != "template" and row["outcome"]["status"] != "PASS":
                problems.append(f"{seed_id}/{key}: status")
            if not row["meta"]["sim_insts"]:
                problems.append(f"{seed_id}/{key}: no insts")
        if not cell["comparison"]["primary"]:
            problems.append(f"{seed_id}: no primary")
    if problems:
        print("FAIL:", problems)
        return 1
    print(f"verified {len(summary['cells'])} cells x 4 arms; all Auto PASS")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="2026-11-17-u20-budget")
    parser.add_argument("--outroot", default=str(ROOT / "m5out/autousens-eval"))
    parser.add_argument("--map", default=str(base.DEFAULT_MAP))
    parser.add_argument("--gem5", default=str(GEM5))
    parser.add_argument("--cc", default="aarch64-openEuler-linux-gcc")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--only", default="")
    parser.add_argument("--verify", metavar="RUN_ID")
    args = parser.parse_args(argv)

    if args.verify:
        target = Path(args.verify)
        if not target.is_dir():
            target = Path(args.outroot) / args.verify
        return verify(target)

    map_path = Path(args.map)
    document = json.loads(map_path.read_text())
    if not base.GEM5.is_file():
        raise SystemExit(f"gem5 not found: {base.GEM5}")
    root = Path(args.outroot) / args.run_id
    if root.exists():
        raise SystemExit(f"run directory already exists: {root}")
    root.mkdir(parents=True)
    protocol = base.protocol_document(args.run_id, map_path)
    protocol["schema"] = "autousens.u20.budget.protocol.v1"
    protocol["budget"] = BUDGET
    protocol["auto"] = {"iterations": AUTO_ITERATIONS, "groups": AUTO_GROUPS}
    (root / "protocol.json").write_text(
        json.dumps(protocol, indent=2, sort_keys=True) + "\n")

    objects = base.compile_objects(root / "bin", args.cc)
    gem5 = Path(args.gem5).resolve()
    only = {item.strip() for item in args.only.split(",") if item.strip()}
    seeds = [seed for seed in seed_templates.SEEDS
             if not only or seed.id in only]
    failures = []

    def task(seed):
        return run_seed(seed, root, document, args.cc, objects, gem5, args.timeout)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(task, seed) for seed in seeds]
        for seed, future in zip(seeds, futures):
            try:
                future.result()
                print(f"OK {seed.id}")
            except Exception as error:  # noqa: BLE001
                failures.append((seed.id, str(error)))
                print(f"FAIL {seed.id}: {error}")
    if failures:
        (root / "failures.json").write_text(json.dumps(failures, indent=2))
        print(f"{len(failures)} failed; see {root}/failures.json")
        return 1
    if only:
        print(f"partial run complete for {len(seeds)} seed(s)")
        return 0
    summary = build_summary(root, args.run_id, protocol)
    write_csv(root, summary)
    write_tables(root, summary)
    print(f"summary: {root / 'summary.json'}")
    print(f"metrics: {root / 'metrics.csv'}")
    print(f"tables : {root / 'tables.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
