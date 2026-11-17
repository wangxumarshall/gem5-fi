"""Analysis artifacts for the u20 template vs AutoµSens comparison.

Reads the two real run summaries (one-pass and 4096-instruction budget) and
writes target-metric, D13-audit and sensitivity CSVs plus a compact table file.
No gem5 run happens here; every number comes from the summaries produced by
``u20_templates.py`` and ``u20_budget.py``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))

from autousens import u20_templates as base  # noqa: E402


def load(path):
    return json.loads(Path(path).read_text())


def all_focus_fields():
    return sorted({field for values in base.FOCUS.values() for field in values})


def write_target_metrics(summary, outdir):
    fields = all_focus_fields()
    rows = []
    for seed, cell in summary["cells"].items():
        mapping = cell["mapping"]
        focus = set(base.FOCUS[mapping["measured"]])
        for arm in ("template", "auto_default", "auto_load", "auto_d13"):
            row = cell[arm]
            meta = row["meta"]
            record = {
                "seed": seed,
                "nominal": mapping["nominal"],
                "measured": mapping["measured"],
                "auto_structure": mapping["auto"],
                "mapping": mapping["kind"],
                "arm": row["kind"],
                "variant": row.get("variant") or "",
                "sim_insts": meta.get("sim_insts"),
                "cycles": meta.get("cycles"),
                "window_consistent": meta.get("window_consistent"),
            }
            for field in fields:
                record[field] = row["flat"].get(field) if field in focus else ""
            rows.append(record)
    path = Path(outdir) / "target_metrics.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_d13_audit(summary, outdir):
    rows = []
    for seed, cell in summary["cells"].items():
        comp = cell["comparison"]
        load = cell["auto_load"]["flat"]
        directed = cell["auto_d13"]["flat"]
        reads = (load.get("ace.l1d.trackedDemandReads"),
                 directed.get("ace.l1d.trackedDemandReads"))
        writes = (load.get("ace.l1d.trackedDemandWrites"),
                  directed.get("ace.l1d.trackedDemandWrites"))
        line = (load.get("ace.l1d.aceLineCycles"),
                directed.get("ace.l1d.aceLineCycles"))
        measured = (load.get("ace.l1d.measuredCycles"),
                    directed.get("ace.l1d.measuredCycles"))
        target_changed = (
            reads[0] != reads[1] or writes[0] != writes[1]
            or line[0] != line[1])
        rows.append({
            "seed": seed,
            "measured": cell["mapping"]["measured"],
            "auto_structure": cell["mapping"]["auto"],
            "primary": comp["primary"],
            "load_primary": comp["auto_load"],
            "d13_primary": comp["auto_d13"],
            "d13_over_load": comp["d13_over_load"],
            "changed_metrics": comp["d13_changed_metrics"],
            "l1d_reads_load": reads[0],
            "l1d_reads_d13": reads[1],
            "l1d_writes_load": writes[0],
            "l1d_writes_d13": writes[1],
            "l1d_line_cycles_load": line[0],
            "l1d_line_cycles_d13": line[1],
            "l1d_measured_cycles_load": measured[0],
            "l1d_measured_cycles_d13": measured[1],
            "target_access_or_line_changed": target_changed,
        })
    path = Path(outdir) / "d13_audit.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_sensitivity(one, budget, outdir):
    rows = []
    for seed in budget["cells"]:
        ob = one["cells"][seed]["comparison"]
        bb = budget["cells"][seed]["comparison"]
        rows.append({
            "seed": seed,
            "measured": budget["cells"][seed]["mapping"]["measured"],
            "primary": bb["primary"],
            "template_one_pass": ob["template"],
            "template_budget": bb["template"],
            "auto_one_pass": ob["auto_default"],
            "auto_budget": bb["auto_default"],
            "template_ratio_change": base.ratio(bb["template"], ob["template"]),
            "auto_ratio_change": base.ratio(bb["auto_default"],
                                            ob["auto_default"]),
            "one_pass_template_insts": one["cells"][seed]["template"]["meta"]["sim_insts"],
            "budget_template_insts": budget["cells"][seed]["template"]["meta"]["sim_insts"],
        })
    path = Path(outdir) / "sensitivity.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_tables(one, budget, outdir):
    lines = ["# u20 analysis tables", "", "## Budget (4096) headline", "",
             "| seed | primary | template | auto | auto+D13 | T/A | D13/AL | changed |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for seed, cell in budget["cells"].items():
        c = cell["comparison"]
        lines.append(
            f"| {seed} | {c['primary']} | {base.fmt(c['template'])} | "
            f"{base.fmt(c['auto_default'])} | {base.fmt(c['auto_d13'])} | "
            f"{base.fmt(c['template_over_auto'], 4)} | "
            f"{base.fmt(c['d13_over_load'], 6)} | {c['d13_changed_metrics']} |")
    lines += ["", "## D13 audit", "",
              "| seed | changed | reads L/D | writes L/D | lineCycles L/D | measuredCycles L/D | D13/AL |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for seed, cell in budget["cells"].items():
        c = cell["comparison"]
        load, directed = cell["auto_load"]["flat"], cell["auto_d13"]["flat"]
        lines.append(
            f"| {seed} | {c['d13_changed_metrics']} | "
            f"{base.fmt(load.get('ace.l1d.trackedDemandReads'), 0)}/"
            f"{base.fmt(directed.get('ace.l1d.trackedDemandReads'), 0)} | "
            f"{base.fmt(load.get('ace.l1d.trackedDemandWrites'), 0)}/"
            f"{base.fmt(directed.get('ace.l1d.trackedDemandWrites'), 0)} | "
            f"{base.fmt(load.get('ace.l1d.aceLineCycles'), 0)}/"
            f"{base.fmt(directed.get('ace.l1d.aceLineCycles'), 0)} | "
            f"{base.fmt(load.get('ace.l1d.measuredCycles'), 0)}/"
            f"{base.fmt(directed.get('ace.l1d.measuredCycles'), 0)} | "
            f"{base.fmt(c['d13_over_load'], 6)} |")
    lines += ["", "## One-pass vs budget (primary)", "",
              "| seed | primary | template 1-pass | template 4096 | auto 1-pass | auto 4096 |",
              "|---|---|---:|---:|---:|---:|"]
    for seed in budget["cells"]:
        ob = one["cells"][seed]["comparison"]
        bb = budget["cells"][seed]["comparison"]
        lines.append(
            f"| {seed} | {bb['primary']} | {base.fmt(ob['template'])} | "
            f"{base.fmt(bb['template'])} | {base.fmt(ob['auto_default'])} | "
            f"{base.fmt(bb['auto_default'])} |")
    path = Path(outdir) / "tables.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--one-pass",
                        default=str(ROOT / "m5out/autousens-eval/2026-11-17-u20/summary.json"))
    parser.add_argument("--budget",
                        default=str(ROOT / "m5out/autousens-eval/2026-11-17-u20-budget2/summary.json"))
    parser.add_argument("--outdir",
                        default=str(ROOT / "m5out/autousens-eval/2026-11-17-u20-budget2"))
    args = parser.parse_args(argv)
    one = load(args.one_pass)
    budget = load(args.budget)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    print(write_target_metrics(budget, outdir))
    print(write_d13_audit(budget, outdir))
    print(write_sensitivity(one, budget, outdir))
    print(write_tables(one, budget, outdir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
