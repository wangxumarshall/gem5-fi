#!/usr/bin/env python3
"""Aggregate Phase-1 structure coverage into a reviewable report.

Input is a ``coverage_matrix.json`` document (schema
``sdcfuzz.phase1.coverage_matrix.v1``), for example one produced by a gem5
measurement run.  The report answers three questions
that a raw matrix does not:

* which structures are covered by at least one template (and by how much);
* which structures are *targeted* by a template versus only observed
  incidentally;
* which structures have no static metric contract at all (a real gap, not a
  zero value).

Outputs ``coverage_summary.json``, ``coverage_matrix.csv`` and
``coverage_summary.md``.  An optional gem5 ``stats.txt`` with SAD counters adds
the occupancy part of the Phase-1 metric set (ROB/IQ/LQ/SQ/PRF/FU/issue).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .coverage import METRIC_COUNTERS

# Stable order used by every Phase-1 artefact.  Extra structures found in a
# future matrix are appended instead of being dropped.
STRUCTURE_ORDER = ("rf", "vec", "l1i", "l1d", "alu", "mult", "div",
                   "fpadd", "fpmul")

# A non-zero ratio is not proof that a structure was meaningfully exercised:
# every template executes instructions, so every template has a few vector
# register writes and instruction fetches.  Counters below these floors are
# treated as incidental activity, not coverage.  Floors are in each metric's
# own units (accesses/events for ACE, input bits for IBR).
OBSERVATION_FLOORS = {
    "rf": 100.0,
    "vec": 100.0,
    "l1i": 50.0,
    "l1d": 50.0,
    "alu": 1000.0,
    "mult": 1000.0,
    "div": 1000.0,
    "fpadd": 1000.0,
    "fpmul": 1000.0,
}

SAD_RESOURCES = ("rob", "iq", "lq", "sq", "intPrf", "vecPrf", "fu", "issue")


def _ordered_structures(structures):
    known = [name for name in STRUCTURE_ORDER if name in structures]
    extras = sorted(set(structures) - set(STRUCTURE_ORDER))
    return known + extras


def load_matrix(path):
    path = Path(path)
    document = json.loads(path.read_text())
    if document.get("schema") != "sdcfuzz.phase1.coverage_matrix.v1":
        raise ValueError(
            f"{path}: unexpected schema {document.get('schema')!r}")
    if not document.get("templates"):
        raise ValueError(f"{path}: matrix has no templates")
    return document


def summarize_matrix(matrix):
    """Return a per-structure rollup plus explicit gap lists."""

    templates = matrix["templates"]
    structures = set()
    for entry in templates.values():
        structures.update((entry.get("coverage") or {}).keys())
    structures = _ordered_structures(structures)

    rows = []
    for structure in structures:
        targeting = []
        requiring = []
        observing = []
        ratios = []
        observed = {}
        metric_counters = METRIC_COUNTERS.get(structure, ())
        floor = OBSERVATION_FLOORS.get(structure, 0.0)
        for template_id in sorted(templates):
            entry = templates[template_id]
            ratio = float((entry.get("coverage") or {}).get(structure, 0.0))
            ratios.append(ratio)
            counters = entry.get("counters") or {}
            if metric_counters and counters:
                counter_value = sum(float(counters.get(counter, 0.0))
                                    for counter in metric_counters)
                threshold = floor
            else:
                # Older/hand-written matrices may omit counters; fall back to
                # the ratio itself and do not apply a counter-unit floor.
                counter_value = ratio
                threshold = 0.0
            if counter_value >= threshold and counter_value > 0.0:
                observing.append(template_id)
                observed[template_id] = (ratio, counter_value)
            if entry.get("target") == structure:
                targeting.append(template_id)
            required = entry.get("required") or {}
            if structure in required or entry.get("target_metric") == structure:
                requiring.append(template_id)

        best_template = None
        if observed:
            best_template = max(observed,
                                key=lambda name: (observed[name][0], name))
        max_ratio = max((value[0] for value in observed.values()), default=0.0)
        max_counter = max((value[1] for value in observed.values()), default=0.0)
        if targeting and observing:
            status = "targeted"
        elif requiring and observing:
            status = "support"
        elif observing:
            status = "incidental"
        else:
            status = "unobserved"

        rows.append({
            "structure": structure,
            "template_count": len(templates),
            "targeting_templates": targeting,
            "requiring_templates": requiring,
            "observing_templates": observing,
            "targeting_count": len(targeting),
            "requiring_count": len(requiring),
            "observing_count": len(observing),
            "max_ratio": round(max_ratio, 9),
            "max_counter": round(max_counter, 3),
            "observation_floor": floor,
            "mean_ratio": round(sum(ratios) / len(ratios), 9)
            if ratios else 0.0,
            "best_template": best_template,
            "status": status,
        })

    covered = [row["structure"] for row in rows
               if row["observing_count"] > 0]
    gaps = {
        "no_targeting_template": [row["structure"] for row in rows
                                  if row["targeting_count"] == 0],
        "no_required_metric": [row["structure"] for row in rows
                               if row["requiring_count"] == 0],
        "never_observed": [row["structure"] for row in rows
                           if row["observing_count"] == 0],
    }
    return {
        "schema": "sdcfuzz.phase1.coverage_summary.v1",
        "template_count": len(templates),
        "structure_count": len(rows),
        "covered_structures": covered,
        "uncovered_structures": [row["structure"] for row in rows
                                 if row["observing_count"] == 0],
        "support_only_structures": [row["structure"] for row in rows
                                    if row["status"] == "support"],
        "structures": rows,
        "gaps": gaps,
    }


def _last_dump_lines(text):
    """Return the lines of the final statistics dump, or the whole file."""
    blocks, current = [], None
    for line in text.splitlines():
        if "Begin Simulation Statistics" in line:
            current = []
        elif "End Simulation Statistics" in line:
            if current is not None:
                blocks.append(current)
                current = None
        elif current is not None:
            current.append(line)
    return blocks[-1] if blocks else text.splitlines()


def sad_from_stats(path):
    """Parse SAD counters from the final dump of a gem5 stats.txt, or None.

    Only the last statistics dump is used, matching ``autousens`` and the
    template matrix.  The function is deliberately suffix-based because the
    stat hierarchy differs between the SE and board configurations.  ``issue``
    is a scalar family (``issueRatio``/``issuedOps``/``issueWidth``), not part
    of the ``ratio::`` vector, so it is parsed explicitly.

    A newer build emits ``sad.enabled``.  ``enabled == 0`` means SAD was not
    requested: the statistics group is still dumped as zeros by gem5, so this
    function returns None instead of a zero document.  The same applies to an
    enabled tracker whose selected ROI never started (no work item, or a
    mismatched work id).  ``samples`` counts only active CPU cycles; the ROI
    length (including idle cycles) is ``roi_cycles`` and is the field to
    compare with ACE/IBR ``measuredCycles``.
    """

    path = Path(path)
    if not path.is_file():
        return None
    samples = None
    enabled = None
    roi_cycles = None
    idle_cycles = None
    active_cycles = None
    window_begins = None
    window_ends = None
    ratio = {}
    used = {}
    capacity = {}
    issue = {}
    for line in _last_dump_lines(path.read_text(errors="replace")):
        fields = line.split()
        if len(fields) < 2:
            continue
        name = fields[0]
        if ".sad." not in name:
            continue
        try:
            value = float(fields[1])
        except ValueError:
            continue
        if name.endswith(".sad.samples"):
            samples = value
        elif name.endswith(".sad.enabled"):
            enabled = value
        elif name.endswith(".sad.roiCycles"):
            roi_cycles = value
        elif name.endswith(".sad.idleCycles"):
            idle_cycles = value
        elif name.endswith(".sad.activeCycles"):
            active_cycles = value
        elif name.endswith(".sad.windowBegins"):
            window_begins = value
        elif name.endswith(".sad.windowEnds"):
            window_ends = value
        elif name.endswith(".sad.issueRatio"):
            issue["ratio"] = value
        elif name.endswith(".sad.issuedOps"):
            issue["issued_ops"] = value
        elif name.endswith(".sad.issueWidth"):
            issue["width"] = value
        elif ".sad.ratio::" in name:
            ratio[name.split("::", 1)[1]] = value
        elif ".sad.usedSum::" in name:
            used[name.split("::", 1)[1]] = value
        elif ".sad.capacity::" in name:
            capacity[name.split("::", 1)[1]] = value
    if not ratio and samples is None and not issue:
        return None
    if enabled is not None and enabled == 0:
        return None
    if (samples == 0 and (window_begins is None or window_begins == 0)
            and (roi_cycles is None or roi_cycles == 0)):
        return None
    resources = [name for name in SAD_RESOURCES if name in ratio]
    resources += sorted(set(ratio) - set(resources))
    document = {
        "enabled": enabled,
        "samples": samples,
        "active_cycles": active_cycles if active_cycles is not None
        else samples,
        "roi_cycles": roi_cycles,
        "idle_cycles": idle_cycles,
        "window_begins": window_begins,
        "window_ends": window_ends,
        "ratio": {name: ratio[name] for name in resources},
        "used_sum": {name: used[name] for name in resources if name in used},
        "capacity": {name: capacity[name] for name in resources
                     if name in capacity},
        "attribution": "per-active-cycle resource occupancy; not coverage",
    }
    if issue:
        document["issue"] = issue
    return document


def _write_csv(matrix, summary, path):
    structures = [row["structure"] for row in summary["structures"]]
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["template", "target"] + structures
                        + ["target_activation"])
        for template_id in sorted(matrix["templates"]):
            entry = matrix["templates"][template_id]
            coverage = entry.get("coverage") or {}
            writer.writerow(
                [template_id, entry.get("target", "")]
                + [f"{float(coverage.get(name, 0.0)):.9f}"
                   for name in structures]
                + [entry.get("target_activation", "")])


def _write_markdown(summary, path, source, sad):
    lines = [
        "# Phase 1 结构覆盖度汇总",
        "",
        f"- 来源矩阵：`{source}`",
        f"- 模板数：{summary['template_count']}",
        f"- 结构数：{summary['structure_count']}",
        f"- 已观测结构：{', '.join(summary['covered_structures']) or '无'}",
        "",
        "| 结构 | 状态 | 定向模板数 | 必需指标模板数 | 观测模板数 "
        "| 最大覆盖比 | 最大计数器 | 最佳模板 |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["structures"]:
        lines.append(
            f"| `{row['structure']}` | {row['status']} | "
            f"{row['targeting_count']} | {row['requiring_count']} | "
            f"{row['observing_count']} | {row['max_ratio']:.6g} | "
            f"{row['max_counter']:.6g} | {row['best_template'] or '-'} |")
    lines += ["", "## 缺口", ""]
    gaps = summary["gaps"]
    labels = (
        ("no_targeting_template", "没有模板以该结构为 target"),
        ("no_required_metric", "没有模板的静态契约要求该指标"),
        ("never_observed", "所有模板中该指标均为 0"),
    )
    for key, label in labels:
        values = gaps.get(key) or []
        lines.append(f"- {label}：{', '.join(values) if values else '无'}")
    if summary.get("support_only_structures"):
        lines += ["", "说明：`support` 结构没有模板把它作为 target，但被模板的"
                  "必需指标覆盖（例如 `rf`、`vec`），属于支撑指标，不是缺陷。"]
    if sad:
        lines += ["", "## SAD 占用（可选）", "",
                  "占用是结构与容量之比，不是结构功能覆盖率。",
                  "", "| 资源 | ratio | usedSum | capacity |",
                  "|---|---:|---:|---:|"]
        for name in sad["ratio"]:
            lines.append(
                f"| `{name}` | {sad['ratio'][name]:.6f} | "
                f"{sad['used_sum'].get(name, '-')} | "
                f"{sad['capacity'].get(name, '-')} |")
        issue = sad.get("issue") or {}
        if issue.get("ratio") is not None:
            lines.append(
                f"| `issue` | {issue['ratio']:.6f} | "
                f"{issue.get('issued_ops', '-')} | "
                f"{issue.get('width', '-')} |")
        if sad.get("samples") is not None:
            lines += ["", f"samples(active cycles)={sad['samples']:.0f}"]
            if sad.get("roi_cycles") is not None:
                lines.append(f"roiCycles={sad['roi_cycles']:.0f}")
            if sad.get("idle_cycles") is not None:
                lines.append(f"idleCycles={sad['idle_cycles']:.0f}")
            if sad.get("active_cycles") is not None:
                lines.append(f"activeCycles={sad['active_cycles']:.0f}")
            lines += ["", "SAD samples are active CPU cycles; roiCycles includes "
                      "idle/unscheduled cycles and is the field to compare with "
                      "ACE/IBR measuredCycles."]
    path.write_text("\n".join(lines) + "\n")


def write_report(matrix, outdir, sad=None, source="coverage_matrix.json"):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    summary = summarize_matrix(matrix)
    summary["source"] = str(Path(source).resolve())
    if sad is not None:
        summary["sad"] = sad
    (outdir / "coverage_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_csv(matrix, summary, outdir / "coverage_matrix.csv")
    _write_markdown(summary, outdir / "coverage_summary.md", source, sad)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True, type=Path,
                        help="coverage_matrix.json from the template gate")
    parser.add_argument("--outdir", required=True, type=Path,
                        help="destination for JSON/CSV/Markdown reports")
    parser.add_argument("--sad-run", type=Path, default=None,
                        help="gem5 output directory or stats.txt with --sad")
    args = parser.parse_args(argv)

    matrix = load_matrix(args.matrix)
    sad = None
    if args.sad_run is not None:
        stats = args.sad_run
        if stats.is_dir():
            stats = stats / "stats.txt"
        sad = sad_from_stats(stats)
        if sad is None:
            raise SystemExit(f"no SAD counters in {stats}")
    summary = write_report(matrix, args.outdir, sad=sad,
                           source=args.matrix)
    print(f"templates={summary['template_count']} "
          f"structures={summary['structure_count']} "
          f"covered={len(summary['covered_structures'])}")
    for row in summary["structures"]:
        print(f"{row['structure']:6s} {row['status']:10s} "
              f"targets={row['targeting_count']} "
              f"required={row['requiring_count']} "
              f"max={row['max_ratio']:.6g} "
              f"best={row['best_template'] or '-'}")
    print(f"report: {Path(args.outdir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
