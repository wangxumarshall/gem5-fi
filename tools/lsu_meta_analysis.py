#!/usr/bin/env python3
"""LSU meta-analysis report generator (09 W11) — answers the three questions.

Reads the BACKFILLED 07-expanded-matrix.csv (post-W10 campaign) and produces:
  1. 337-cell status audit (data / blocked / deferred / 不适用 / 待执行,
     with reasons — blocked is accounted, never silently skipped)
  2. Conservation check on DATA cells only (Activated = Masked+Detected+SDC
     +Crash+Timeout, 04 L5)
  3. Three-question answers (09 §1.1):
     Q1: Which locations have real SDC potential? (per-unit/model ranking,
         activated-denominated, Wilson 95% CI)
     Q2: Observable precursors before SDC — L0 funnel proxy (activation-rate
         spread); L1/L2 shadow-compare data remains future work (honest)
     Q3: Structured vs random increment — fault-type family split plus the
         same-unit paired comparison (S01 bitflip vs S04 substitution)
  4. Boundary declarations (B0 experimental model, no-920, metric discipline)

Usage: python3 tools/lsu_meta_analysis.py --matrix <backfilled.csv> --output <report.md>
"""
import argparse
import csv
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
COL_ACT_RATE = 25
COL_STATUS = 26

# Data-phase statuses (cells with real campaign numbers); everything else
# with a non-empty status is a classification (blocked/deferred/不适用).
DATA_STATUSES = ("试跑", "已筛查", "主结果")
# Fault-type families (03 col5 actual values, verified against the matrix):
RANDOM_TYPES = {"单比特翻转", "双比特翻转"}
PROTECTION_TYPES = {"保护"}
# everything else = structured (换值/状态/时序/错位拼接/卡死/状态换值/时序状态)


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


def num(c, col):
    return parse_num(c[col]) if len(c) > col else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", required=True, help="backfilled 07-expanded-matrix.csv")
    p.add_argument("--output", default="lsu_meta_report.md")
    a = p.parse_args()

    cells = load_matrix(a.matrix)

    # ---- status audit: every cell lands in exactly one bucket ----
    data = [c for c in cells if c[COL_STATUS].strip() in DATA_STATUSES]
    pending = [c for c in cells if c[COL_STATUS].strip() in ("", "待执行")]
    classified = [c for c in cells
                  if c[COL_STATUS].strip() and c[COL_STATUS].strip() not in
                  DATA_STATUSES and c[COL_STATUS].strip() not in ("", "待执行")]
    reason_count = defaultdict(int)
    for c in classified:
        key = c[COL_STATUS].split("(")[0]
        reason_count[key] += 1

    report = []
    report.append("# LSU 故障注入元分析报告\n")
    report.append(f"> 数据源: {a.matrix}\n")
    report.append(f"> 337 格状态审计: 数据 {len(data)} · 分类 {len(classified)} "
                  f"({' · '.join('%s %d' % kv for kv in sorted(reason_count.items()))}) "
                  f"· 待执行 {len(pending)}\n")
    report.append("> 生成: W11 元分析脚本 (09 §1.1 三问 + 守恒 + 排序 + 边界)\n")

    # ---- Conservation check (DATA cells only) ----
    report.append("\n## 1. 守恒校验 (04 L5: Activated = Masked + Detected + SDC + Crash + Timeout)\n")
    violations = 0
    for c in data:
        activated = num(c, COL_ACTIVATED)
        total = sum(num(c, col) for col in
                    (COL_MASKED, COL_DETECTED, COL_SDC, COL_CRASH, COL_TIMEOUT))
        if total != activated:
            violations += 1
            report.append(f"  VIOLATION {c[COL_RUNID]}: activated={activated} sum={total}\n")
    report.append(f"\n  守恒检验: {len(data) - violations}/{len(data)} 数据格通过, "
                  f"{violations} 违规\n")

    # ---- Q1: SDC potential ranking (data cells, activated denominator) ----
    report.append("\n## 2. Q1 — 哪些位置有真实 SDC 潜力？\n")
    unit_stats = defaultdict(lambda: {"cells": 0, "sdc_cells": 0,
                                      "activated": 0, "sdc": 0})
    model_stats = defaultdict(lambda: {"unit": "", "fault": "", "sdc": 0,
                                       "activated": 0, "cells": 0})
    for c in data:
        unit, model = c[COL_UNIT], c[COL_MODEL]
        sdc, activated = num(c, COL_SDC), num(c, COL_ACTIVATED)
        us = unit_stats[unit]
        us["cells"] += 1
        us["activated"] += activated
        us["sdc"] += sdc
        if sdc > 0:
            us["sdc_cells"] += 1
        ms = model_stats[model]
        ms.update(unit=unit, fault=c[COL_FAULT_TYPE])
        ms["sdc"] += sdc
        ms["activated"] += activated
        ms["cells"] += 1

    report.append("\n### 单元级（SDC 率分母 = activated，Wilson 95% CI）\n\n")
    report.append("| 单元 | 数据格 | SDC>0 格 | activated | SDC | SDC 率 [Wilson95] |\n|---|---|---|---|---|---|\n")
    for unit in sorted(unit_stats, key=lambda u: unit_stats[u]["sdc"],
                       reverse=True):
        s = unit_stats[unit]
        rate = s["sdc"] / s["activated"] if s["activated"] else 0.0
        _c, lo, hi = wilson_ci(rate, s["activated"])
        report.append(f"| {unit} | {s['cells']} | {s['sdc_cells']} | "
                      f"{s['activated']} | {s['sdc']} | "
                      f"{rate:.1%} [{lo:.1%},{hi:.1%}] |\n")

    report.append("\n### 模型级（SDC>0 的模型；trial 级样本——CI 宽，方向性参考）\n\n")
    sdc_models = [(m, v) for m, v in model_stats.items() if v["sdc"] > 0]
    if sdc_models:
        report.append("| 模型 | 单元 | 故障类型 | activated | SDC | SDC 率 [Wilson95] |\n|---|---|---|---|---|---|\n")
        for m, v in sorted(sdc_models, key=lambda kv: kv[1]["sdc"], reverse=True):
            rate = v["sdc"] / v["activated"] if v["activated"] else 0.0
            _c, lo, hi = wilson_ci(rate, v["activated"])
            report.append(f"| {m} | {v['unit']} | {v['fault']} | {v['activated']} "
                          f"| {v['sdc']} | {rate:.1%} [{lo:.1%},{hi:.1%}] |\n")
    else:
        report.append("（trial 级无 SDC>0 模型——见边界声明的样本量局限）\n")

    # ---- Q3: Structured vs random ----
    report.append("\n## 3. Q3 — 结构化模型 vs 随机翻转增量\n")

    def family(fault):
        if fault in RANDOM_TYPES:
            return "随机翻转"
        if fault in PROTECTION_TYPES:
            return "保护"
        return "结构化"

    fam_stats = defaultdict(lambda: {"sdc": 0, "activated": 0})
    for m, v in model_stats.items():
        f = family(v["fault"])
        fam_stats[f]["sdc"] += v["sdc"]
        fam_stats[f]["activated"] += v["activated"]
    report.append("\n### 故障类型族（activated 分母）\n\n| 族 | activated | SDC | SDC 率 |\n|---|---|---|---|\n")
    for f in ("随机翻转", "结构化", "保护"):
        s = fam_stats[f]
        rate = f"{s['sdc']/s['activated']:.1%}" if s["activated"] else "n/a"
        report.append(f"| {f} | {s['activated']} | {s['sdc']} | {rate} |\n")

    # Same-unit paired comparison: S01 (bitflip) vs S04 (substitution) and
    # S13 (addr bitflip) vs S04 — the 09-W11 spec's canonical pairing.
    report.append("\n### 同单元配对对照（09 W11: S01 bitflip vs S04 合法换值 等）\n\n")
    PAIRS = [("S01", "S04"), ("S13", "S04"), ("C01", "C05"), ("P01", "P03")]
    report.append("| 配对（随机 vs 结构化） | activated A/B | SDC A/B | SDC 率 A/B |\n|---|---|---|---|\n")
    for x, y in PAIRS:
        vx, vy = model_stats.get(x), model_stats.get(y)
        if not vx or not vy:
            report.append(f"| {x} vs {y} | 数据缺（格 blocked/未跑） | — | — |\n")
            continue
        rx = f"{vx['sdc']/vx['activated']:.1%}" if vx["activated"] else "n/a"
        ry = f"{vy['sdc']/vy['activated']:.1%}" if vy["activated"] else "n/a"
        report.append(f"| {x}({vx['fault']}) vs {y}({vy['fault']}) | "
                      f"{vx['activated']}/{vy['activated']} | "
                      f"{vx['sdc']}/{vy['sdc']} | {rx}/{ry} |\n")

    # ---- Q2: Precursors (L0 funnel proxy) ----
    report.append("\n## 4. Q2 — SDC 前的可观测前兆（L0 漏斗代理）\n")
    report.append("  激活率（activated/attempted，04 L0）最低的数据格 = 注入后未达下游消费的格，\n"
                  "  即 L0→L4 传播链断点最浅处——在线检测锚点的首选位置：\n\n")
    ranked = sorted(data, key=lambda c: (num(c, COL_ACT_RATE)
                                         if num(c, COL_ATTEMPTED) else 1.0))
    report.append("| RunID | attempted | activated | 激活率 |\n|---|---|---|---|\n")
    for c in ranked[:10]:
        att, act = num(c, COL_ATTEMPTED), num(c, COL_ACTIVATED)
        rate = f"{act/att:.2%}" if att else "n/a"
        report.append(f"| {c[COL_RUNID]} | {att} | {act} | {rate} |\n")
    report.append("\n  诚实边界: L1 影子比对与 L2 请求级观测需 W3 观测链的 campaign 数据\n"
                  "  回填（当前 trial 只带 L0 漏斗行）——本节为 L0 代理，非完整前兆谱。\n")

    # ---- Boundary declarations ----
    report.append("\n## 5. 边界声明\n")
    report.append("- B0 是可复现实验模型，不是鲲鹏 920 复刻（00 总览）\n")
    report.append("- 指标口径（AVF / 条件占比 / 总 AVF / 检出率 / DelayAVF）严禁混算\n")
    report.append("- SDC 率分母 = activated（04 L0）；Injected-not-activated 单列\n")
    report.append("- trial 级样本只用于发现注入器错误/全 Crash/零激活（05 r13），\n"
                  "  不用于最终窄置信区间——正式结论需筛查档 ≥385 activated/格\n")
    report.append("- FS/多核/SPEC 依赖格如实标 blocked（M5 口径：不伪造完成）：\n")
    for reason, count in sorted(reason_count.items()):
        report.append(f"  - {reason}: {count} 格\n")
    report.append("- B0 无保护配置下保护类行（T09/S12/C13/O08）标不适用，不填零\n")
    report.append("- 无论文直接结果的 AGU、原子/同步和多数结构化模型，结论标注探索性\n")

    output = Path(a.output)
    output.write_text("".join(report), encoding="utf-8")
    print(f"Report written to {output}")
    print(f"  Cells: {len(cells)} total | data {len(data)} | classified "
          f"{len(classified)} | pending {len(pending)}")
    print(f"  Conservation violations: {violations}")


if __name__ == "__main__":
    main()
