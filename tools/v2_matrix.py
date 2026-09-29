#!/usr/bin/env python3
"""V2.0 展开矩阵装载器（implementation-plan.md Task WS1）。

唯一矩阵入口：WA5/WB4 的 campaign 与 WS6 的回填/审计工具一律 import 本模块
取 V2.0 格清单，杜绝各自解析 43 列 CSV（plan §2 WS1 Interfaces）。

口径（数字永不混用 V1.0 的 337/226 格）：
- LSU  book = docs/gem5-fi/lsu/07-expanded-matrix.csv（325 格，commit 06cceb6a）
- OoO  book = docs/gem5-fi/ooo/07-expanded-matrix.csv（310 格，commit 94dfce2e）
- 列文档：docs/gem5-fi/{lsu,ooo}/07-expanded-matrix.md「列文档」节（CSV 44 列
  = 1 管理列 + 源表 43 列；本模块的 HEADER 断言与之逐名一致）。

自校验（内嵌，脚本退出非零即失败；plan WS1 Step 2）：
- 行数 LSU 325 / OoO 310；RunID 全表唯一且 == 模型ID-频率-W#；
- 频率分布 == 两簿 README「断言结果」dist-freq 行（LSU F0=105 F1=24 F2=77
  F3=4 F4=26 F5=25 F6=64；OoO F0=104 F1=12 F2=76 F3=0 F4=28 F5=10 F6=80）；
- 负载集合 LSU 14 / OoO 11（两簿 06-workloads.md 均定义 W0–W13 共 14 项）；
- 值槽（P..AP 除 Z/公式列，21 列）全空、记录状态(Z)==「待执行」
  （设计提取层不含任何实验结果——两簿 README 诚实性注记 (g)/(e)）。

用法：
    python3 tools/v2_matrix.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv --dry-run
    python3 tools/v2_matrix.py --matrix docs/gem5-fi/ooo/07-expanded-matrix.csv --dry-run
    python3 tools/v2_matrix.py --matrix <csv> --cells A01-F0-W3,P09-F6-W13
"""

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# --- 列名（与 07-expanded-matrix.md「列文档」逐名一致；源表字母 A..AQ） ---
HEADER = [  # 源表 43 列（CSV 去掉管理列后）
    "RunID",                    # A  键：模型ID-频率-负载ID(W#)
    "模型ID",                    # B ─┐
    "单元",                      # C  │
    "注入位置（结构与正常作用）",     # D  │
    "故障类型",                   # E  │
    "故障模型（实施步骤与激活口径）",  # F  │ 14 个设计展开列（B..O）
    "频率",                      # G  │
    "频率定义",                   # H  │
    "负载（真实名称）",            # I  │
    "负载定义/oracle",            # J  │
    "触发条件",                   # K  │
    "传播监控",                   # L  │
    "预期结果",                   # M  │
    "设计理由",                   # N  │
    "文献依据",                   # O ─┘
    "Seed/注入索引",              # P ─┐
    "Attempted",                # Q  │
    "Activated",                # R  │
    "Masked",                   # S  │
    "Detected-contained",       # T  │
    "Data Corruption",          # U  │
    "Crash",                    # V  │ 22 个值槽（P..AP 除 5 个公式列，
    "Timeout",                  # W  │ 含记录状态 Z；源表 21 列空 + Z=待执行）
    "SDC率(可分析activated)",    # X  公式列（不校验空）
    "激活率",                    # Y  公式列
    "记录状态",                   # Z  值槽（唯一非空：待执行）
    "实测备注",                   # AA │
    "SDC",                      # AB │
    "Hardware RAS首检（互斥）",    # AC │
    "OS首检（互斥）",             # AD │
    "Application首检（互斥）",     # AE │
    "None首检（互斥）",           # AF │
    "Contained",                # AG │
    "Detected-uncontained",     # AH │
    "RAS-silent Crash",         # AI │
    "RAS-silent Timeout",       # AJ │
    "检测/告警证据",              # AK │
    "硬件RAS检测率(任意时点)",     # AL  公式列
    "检测计数差额（应为0）",       # AM  公式列
    "结局计数差额（应为0）",       # AN  公式列
    "Hardware RAS检测（任意时点）", # AO │
    "Simulator failure",        # AP ─┘
    "故障表现形式/子模型",         # AQ 子模型全枚举（整格文本）
]
MGMT_COL = "Excel行"            # 管理列（提取层加在 CSV 首位）
FULL_HEADER = [MGMT_COL] + HEADER
assert len(FULL_HEADER) == 44 and len(HEADER) == 43

# 源表字母 B..O 的 14 个设计展开列（07-expanded-matrix.md 类别标注）
DESIGN_COLS = HEADER[1:15]
assert len(DESIGN_COLS) == 14

FORMULA_COLS = ["SDC率(可分析activated)", "激活率", "硬件RAS检测率(任意时点)",
                "检测计数差额（应为0）", "结局计数差额（应为0）"]
VALUE_SLOTS = [c for c in HEADER[15:42] if c not in FORMULA_COLS]  # P..AP 除公式列
assert len(VALUE_SLOTS) == 22, VALUE_SLOTS
EMPTY_SLOTS = [c for c in VALUE_SLOTS if c != "记录状态"]
assert len(EMPTY_SLOTS) == 21
SUBMODEL_COL = "故障表现形式/子模型"
STATUS_COL = "记录状态"

# --- 两簿期望底账（plan §1.3 V2.0 数量底账 = 两簿 README 断言结果） ---
LSU_UNITS = {"AGU", "L1d-TLB", "Store Queue", "Load Queue", "L1d-Cache",
             "原子与同步", "数据预取器"}
OOO_UNITS = {"Int Decode", "Int Rename", "Int Dispatch / ROB", "FP/SIMD Decode",
             "FP/SIMD Rename", "FP/SIMD Dispatch/ROB"}
FREQS = ["F0", "F1", "F2", "F3", "F4", "F5", "F6"]
EXPECT = {
    "lsu": {"rows": 325, "freq": {"F0": 105, "F1": 24, "F2": 77, "F3": 4,
                                  "F4": 26, "F5": 25, "F6": 64},
            "workloads": 14},
    "ooo": {"rows": 310, "freq": {"F0": 104, "F1": 12, "F2": 76, "F3": 0,
                                  "F4": 28, "F5": 10, "F6": 80},
            "workloads": 11},
}
# 两簿 06-workloads.md 均定义 W0–W13 共 14 项负载（OoO W0/W2/W12 未接线）
TOTAL_DEFINED_WORKLOADS = 14

RUNID_RE = re.compile(r"^([A-Z]+\d+)-(F[0-6])-(W\d+)$")


class MatrixError(Exception):
    """矩阵装载/自校验失败（含原因，退出非零）。"""


@dataclass
class V2Cell:
    """V2.0 展开矩阵一格（模型×频率×负载；子模型格内分层记录，plan §0.8）。"""
    run_id: str                 # 模型ID-频率-W#
    model_id: str
    unit: str
    freq: str                   # F0..F6
    workload_id: str            # W0..W13
    workload_name: str          # 负载（真实名称）列原文
    submodels: list             # [子模型ID, ...]（<模型ID>-<字母>）
    design_cols: dict           # 14 个设计展开列原文 {列名: 文本}
    raw: dict = field(compare=False, repr=False, default_factory=dict)
    # raw：整行 44 列原文（回填/审计写回 CSV 用；WS6）


def _detect_book(units):
    unknown = units - LSU_UNITS - OOO_UNITS
    if unknown:
        raise MatrixError(f"unknown units (not LSU/OoO V2.0): {sorted(unknown)}")
    if units <= LSU_UNITS and not (units & OOO_UNITS):
        return "lsu"
    if units <= OOO_UNITS and not (units & LSU_UNITS):
        return "ooo"
    raise MatrixError(f"mixed LSU/OoO units in one matrix: {sorted(units)}")


def load_v2_matrix(csv_path):
    """装载并自校验一个 V2.0 展开矩阵，返回 list[V2Cell]。

    任何自校验失败抛 MatrixError（调用方退出非零）——本模块是唯一矩阵入口，
    口径错误必须当场暴露，不许静默吞掉。
    """
    path = Path(csv_path)
    if not path.is_file():
        raise MatrixError(f"matrix csv not found: {path}")

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FULL_HEADER:
            missing = [c for c in FULL_HEADER if c not in (reader.fieldnames or [])]
            extra = [c for c in (reader.fieldnames or []) if c not in FULL_HEADER]
            raise MatrixError(
                f"header mismatch vs 07-expanded-matrix.md 列文档: "
                f"missing={missing} extra={extra}")
        rows = list(reader)

    cells = []
    seen_runids = {}
    for i, row in enumerate(rows, start=2):  # CSV 行 2 起（行 1 为表头）
        run_id = row["RunID"]
        m = RUNID_RE.match(run_id)
        if not m:
            raise MatrixError(f"csv line {i}: RunID not 模型ID-频率-W#: {run_id!r}")
        model_id, freq, workload_id = m.group(1), m.group(2), m.group(3)
        if row["模型ID"] != model_id:
            raise MatrixError(f"csv line {i}: RunID 模型ID {model_id} != 模型ID列 "
                              f"{row['模型ID']!r}")
        if row["频率"] != freq:
            raise MatrixError(f"csv line {i}: RunID 频率 {freq} != 频率列 {row['频率']!r}")
        sub_text = row[SUBMODEL_COL]
        submodels = re.findall(re.escape(model_id) + r"-[a-z]", sub_text)
        if not submodels:
            raise MatrixError(f"csv line {i}: no <模型ID>-<字母> submodels in "
                              f"{SUBMODEL_COL}: {sub_text[:60]!r}")
        if run_id in seen_runids:
            raise MatrixError(f"csv line {i}: duplicate RunID {run_id} "
                              f"(first at line {seen_runids[run_id]})")
        seen_runids[run_id] = i
        cells.append(V2Cell(
            run_id=run_id, model_id=model_id, unit=row["单元"], freq=freq,
            workload_id=workload_id, workload_name=row["负载（真实名称）"],
            submodels=submodels,
            design_cols={c: row[c] for c in DESIGN_COLS},
            raw=dict(row)))

    # --- 自校验（plan WS1 Step 2；失败即 MatrixError） ---
    units = {c.unit for c in cells}
    book = _detect_book(units)
    exp = EXPECT[book]
    if len(cells) != exp["rows"]:
        raise MatrixError(f"{book}: rows {len(cells)} != expected {exp['rows']}")
    freq_seen = {f: sum(1 for c in cells if c.freq == f) for f in FREQS}
    if freq_seen != exp["freq"]:
        raise MatrixError(f"{book}: freq distribution {freq_seen} != expected "
                          f"{exp['freq']}")
    wl = {c.workload_id for c in cells}
    if len(wl) != exp["workloads"]:
        raise MatrixError(f"{book}: workloads used {len(wl)} "
                          f"({sorted(wl)}) != expected {exp['workloads']}")
    if not wl <= {f"W{n}" for n in range(TOTAL_DEFINED_WORKLOADS)}:
        raise MatrixError(f"{book}: workload ids outside W0..W13: "
                          f"{sorted(wl - {f'W{n}' for n in range(14)})}")
    for c in cells:
        for col in EMPTY_SLOTS:
            if c.raw[col].strip():
                raise MatrixError(f"{c.run_id}: value slot {col!r} non-empty at "
                                  f"design time: {c.raw[col][:40]!r}")
        if c.raw[STATUS_COL].strip() != "待执行":
            raise MatrixError(f"{c.run_id}: {STATUS_COL} != 待执行: "
                              f"{c.raw[STATUS_COL]!r}")
    return cells


def summary_line(cells):
    """一行摘要（plan WS1 Step 3 预期输出格式）。"""
    freq = {f: sum(1 for c in cells if c.freq == f) for f in FREQS}
    used = len({c.workload_id for c in cells})
    parts = [f"cells={len(cells)}"] + [f"{f}={freq[f]}" for f in FREQS]
    parts.append(f"workloads={used}/{TOTAL_DEFINED_WORKLOADS}")
    return " ".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description="V2.0 展开矩阵装载器（自校验）")
    ap.add_argument("--matrix", required=True, help="07-expanded-matrix.csv 路径")
    ap.add_argument("--cells", default="",
                    help="逗号分隔 RunID 列表（只列出这些格；未知 RunID 报错）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印摘要行（不逐格列出）")
    args = ap.parse_args(argv)

    try:
        cells = load_v2_matrix(args.matrix)
    except MatrixError as e:
        print(f"v2_matrix: FAIL {e}", file=sys.stderr)
        return 1

    if args.cells:
        want = [s.strip() for s in args.cells.split(",") if s.strip()]
        by_id = {c.run_id: c for c in cells}
        unknown = [w for w in want if w not in by_id]
        if unknown:
            print(f"v2_matrix: FAIL unknown RunIDs: {unknown}", file=sys.stderr)
            return 1
        for w in want:
            c = by_id[w]
            print(f"{c.run_id} model={c.model_id} unit={c.unit} freq={c.freq} "
                  f"workload={c.workload_id} submodels={len(c.submodels)}")
        print(f"selected={len(want)} " + summary_line([by_id[w] for w in want]))
    elif not args.dry_run:
        for c in cells:
            print(f"{c.run_id} model={c.model_id} unit={c.unit} freq={c.freq} "
                  f"workload={c.workload_id} submodels={len(c.submodels)}")
        print(summary_line(cells))
    else:
        print(summary_line(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())
