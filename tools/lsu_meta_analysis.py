#!/usr/bin/env python3
"""LSU meta-analysis report generator (09 W11) — answers the three questions.

Reads the BACKFILLED 07-expanded-matrix.csv (post-W10 campaign) and produces:
  1. Three-question answers (09 §1.1):
     Q1: Which locations have real SDC potential?
     Q2: What observable precursors exist before SDC (L0-L3 signals)?
     Q3: What's the increment of structured models vs random bit flips?
  2. Position × SDC potential ranking (per-unit, per-model)
  3. Conservation check across all cells (Activated = Masked+Detected+SDC+Crash+Timeout)
  4. Boundary declarations (B0 experimental model, no-920, metric discipline)

Usage: python3 tools/lsu_meta_analysis.py --matrix <backfilled.csv> --output <report.md>
"""
import argparse
import csv
import json
import math
from pathlib import Path
from collections import defaultdict

# Expanded matrix columns (+1 shift for Excel行)
COL_EXCEL = 0
COL_RUNID = 1
COL_MODEL = 2
COL_UNIT = 3
COL_FAULT_TYPE = 5
COL_FREQ = 7
COL_WORKLOAD = 9
COL_ATTEMPTED = 17
COL_ACTIVATED = 18
COL_MASKED = 19
COL_DETECTED = 20
COL_SDC = 21
COL_CRASH = 22
COL_TIMEOUT = 23
COL_SDC_RATE = 24
COL_ACTIVATION_RATE = 25
COL_STATUS = 26


def wilson_ci(p, n, z=1.96):
    """Wilson 95% confidence interval for proportion p with sample size n."""
    if n == 0:
        return 0.0, 0.0, 0.0
    denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    spread = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return center, max(0, center - spread), min(1, center + spread)


def load_matrix(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    cells = []
    for r in rows[1:]:
        if len(r) > COL_RUNID and r[COL_RUNID].strip():
            cells.append(r)
    return cells


def parse_num(s):
    try:
        return int(s) if s.strip() else 0
    except ValueError:
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", required=True, help="backfilled 07-expanded-matrix.csv")
    p.add_argument("--output", default="lsu_meta_report.md")
    a = p.parse_args()

    cells = load_matrix(a.matrix)
    executed = [c for c in cells if c[COL_STATUS].strip() not in ("", "待执行")]
    pending = [c for c in cells if c[COL_STATUS].strip() in ("", "待执行")]

    report = []
    report.append("# LSU 故障注入元分析报告\n")
    report.append(f"> 数据源: {a.matrix} · 337 格中 {len(executed)} 已执行 / {len(pending)} 待执行\n")
    report.append(f"> 生成: W11 元分析脚本 (09 §1.1 三问 + 守恒 + 排序 + 边界)\n")

    # ---- Conservation check ----
    report.append("\n## 1. 守恒校验 (04 L5: Activated = Masked + Detected + SDC + Crash + Timeout)\n")
    violations = 0
    for c in executed:
        activated = parse_num(c[COL_ACTIVATED]) if len(c) > COL_ACTIVATED else 0
        masked = parse_num(c[COL_MASKED]) if len(c) > COL_MASKED else 0
        detected = parse_num(c[COL_DETECTED]) if len(c) > COL_DETECTED else 0
        sdc = parse_num(c[COL_SDC]) if len(c) > COL_SDC else 0
        crash = parse_num(c[COL_CRASH]) if len(c) > COL_CRASH else 0
        timeout = parse_num(c[COL_TIMEOUT]) if len(c) > COL_TIMEOUT else 0
        total = masked + detected + sdc + crash + timeout
        if total != activated:
            violations += 1
            report.append(f"  VIOLATION {c[COL_RUNID]}: activated={activated} "
                         f"sum={total} (M={masked} D={detected} S={sdc} C={crash} T={timeout})")
    report.append(f"\n  守恒检验: {len(executed) - violations}/{len(executed)} 通过, "
                 f"{violations} 违规\n")

    # ---- Q1: SDC potential ranking ----
    report.append("\n## 2. Q1 — 哪些位置有真实 SDC 潜力？\n")
    unit_stats = defaultdict(lambda: {"cells": 0, "sdc_cells": 0, "total_activated": 0,
                                      "total_sdc": 0})
    model_stats = defaultdict(lambda: {"unit": "", "fault": "", "sdc": 0, "activated": 0})
    for c in executed:
        unit = c[COL_UNIT]
        model = c[COL_MODEL]
        fault = c[COL_FAULT_TYPE]
        sdc = parse_num(c[COL_SDC]) if len(c) > COL_SDC else 0
        activated = parse_num(c[COL_ACTIVATED]) if len(c) > COL_ACTIVATED else 0
        us = unit_stats[unit]
        us["cells"] += 1
        us["total_activated"] += activated
        us["total_sdc"] += sdc
        if sdc > 0:
            us["sdc_cells"] += 1
        ms = model_stats[model]
        ms["unit"] = unit
        ms["fault"] = fault
        ms["sdc"] += sdc
        ms["activated"] += activated

    report.append("| 单元 | 格数 | SDC>0 格 | 总 activated | 总 SDC | SDC 率 |\n|---|---|---|---|---|---|\n")
    for unit in sorted(unit_stats, key=lambda u: unit_stats[u]["total_sdc"], reverse=True):
        s = unit_stats[unit]
        rate = s["total_sdc"] / s["total_activated"] if s["total_activated"] else 0
        report.append(f"| {unit} | {s['cells']} | {s['sdc_cells']} | "
                     f"{s['total_activated']} | {s['total_sdc']} | {rate:.1%} |\n")

    # ---- Q3: Structured vs random ----
    report.append("\n## 3. Q3 — 结构化模型 vs 随机翻转增量\n")
    random_types = {"单比特翻转", "双比特翻转"}
    structured_types = {"换值", "错位拼接", "状态", "时序", "保护"}
    random_sdc = sum(m["sdc"] for m in model_stats.values() if m["fault"] in random_types)
    random_act = sum(m["activated"] for m in model_stats.values() if m["fault"] in random_types)
    struct_sdc = sum(m["sdc"] for m in model_stats.values() if m["fault"] in structured_types)
    struct_act = sum(m["activated"] for m in model_stats.values() if m["fault"] in structured_types)
    report.append(f"| 模型族 | 总 activated | 总 SDC | SDC 率 |\n|---|---|---|---|\n")
    rr = f"{random_sdc/random_act:.1%}" if random_act else "n/a"
    sr = f"{struct_sdc/struct_act:.1%}" if struct_act else "n/a"
    report.append(f"| 随机翻转(单bit+双bit) | {random_act} | {random_sdc} | {rr} |\n")
    report.append(f"| 结构化(换值/拼接/状态/时序/保护) | {struct_act} | {struct_sdc} | {sr} |\n")

    # ---- Q2: Precursors ----
    report.append("\n## 4. Q2 — SDC 前的可观测前兆（需 L1/L2 观测数据回填后分析）\n")
    report.append("  [待填] 此节需要 W3 L1 影子比对和 L2 请求级观测的 campaign 数据回填后生成。\n")

    # ---- Boundary declarations ----
    report.append("\n## 5. 边界声明\n")
    report.append("- B0 是可复现实验模型，不是鲲鹏 920 复刻（00 总览）\n")
    report.append("- 指标口径（AVF / 条件占比 / 总 AVF / 检出率 / DelayAVF）严禁混算\n")
    report.append("- SDC 率分母 = activated（04 L0）；Injected-not-activated 单列\n")
    report.append("- 无论文直接结果的 AGU、原子/同步和多数结构化模型，结论标注探索性\n")
    report.append("- B0 无保护配置下保护类行（T09/S12/C13/O08）标不适用\n")

    # Write report
    output = Path(a.output)
    output.write_text("".join(report), encoding="utf-8")
    print(f"Report written to {output}")
    print(f"  Cells: {len(cells)} total, {len(executed)} executed, {len(pending)} pending")
    print(f"  Conservation violations: {violations}")


if __name__ == "__main__":
    main()
