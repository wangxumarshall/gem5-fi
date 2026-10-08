#!/usr/bin/env python3
"""ooo_models.py — OOO 57 模型机读映射表（P1 U1）。

三级一致性的静态权威数据 + 交叉校验 CLI：

  MODELS    57 个模型 ID -> {unit, excel_row, fault_type, freqs, workloads,
            n_submodels, impl_status, injector, submodels}。
            数据来源（2026-10-08 生成，逐字段核对）：
              - docs/gem5-fi/ooo/03-design-matrix.md   索引表（7 列）+ 详表子模型字母
              - docs/gem5-fi/ooo/09-v2-coverage-audit.md 逐模型判定 + 注入器/模式面

  --check   三方一致性校验（退出码 0 = 全部通过）：
              1) 静态表 ↔ 03 索引表重解析：57 模型逐字段一致（顺序+集合）
              2) 静态表 ↔ 09 逐模型审计表重解析：impl_status 一致；
                 计数 implemented=9 partial=34 unimplemented=14
              3) 静态表 submodels ↔ 03 详表子模型字母重提取；len == n_submodels
              4) 注入器布线：非 unimplemented ⇔ injector 非空且在已知旗标表
              5) 清单 完整任务执行清单.md：310 个 `### ITEM-NNN — <模型>-F<f>-W<w>`
                 头全部可解析；F 在模型 freqs、W 在模型 workloads；无重复 ID/引用
  --item    ITEM-NNN -> 单条映射；模型 ID（如 D01）-> 模型档案 + 其全部 ITEM。

已知文档缺陷（F-010，如实记录不静默）：09 审计总账表「部分 | 0」与其逐模型表
34 行「部分」矛盾（9+0+14≠57）；本工具以逐模型表为权威。

独立于 gem5 构建；python3.9（login01）可运行。
计划：docs/superpowers/plans/2026-10-08-ooo-p1-injectors-observation-campaign.md U1。
"""

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC_DIR = REPO / "docs" / "gem5-fi" / "ooo"
DEFAULT_INDEX = DOC_DIR / "03-design-matrix.md"
DEFAULT_AUDIT = DOC_DIR / "09-v2-coverage-audit.md"
DEFAULT_CHECKLIST = DOC_DIR / "完整任务执行清单.md"

# 注入器 -> ooo_proxy.py 挂载旗标（configs/se/ooo_proxy.py add_argument 实测提取）
INJECTOR_TO_FLAG = {
    "CHAOSDecode": "--chaos_decode",
    "CHAOSRenameMap": "--chaos_rename",
    "CHAOSROB": "--chaos_rob",
    "CHAOSIQ": "--chaos_iq",
    "CHAOSFreeList": "--chaos_freelist",
    "CHAOSPhysReg": "--chaos_phys",
    "CHAOSFPU": "--chaos_fpu",
}

STATUS_ZH = {"implemented": "已实现", "partial": "部分", "unimplemented": "未实现"}

# 清单签发口径：310 条 ITEM（编号连续 001..310）、57 模型；偏离即错。
EXPECTED_ITEMS = 310
EXPECTED_MODELS = 57

MODEL_RE = r"(?:D|R|B|FD|FR|FB)\d{2}"

# 静态数据（生成后逐字段核对；--check 对文档重解析做逐项一致性证明）
MODELS = {
# Generated static data — sources: 03-design-matrix.md (index+detailed), 09-v2-coverage-audit.md (per-model 判定/注入器)

    "D01": {
        "unit": "Int Decode",
        "excel_row": "R2",
        "fault_type": "单比特翻转",
        "freqs": ['F0', 'F1', 'F2'],
        "workloads": "W3 A64-DecodeProbe<br>W6 CoreMark+Embench",
        "n_submodels": 4,
        "impl_status": "implemented",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "D02": {
        "unit": "Int Decode",
        "excel_row": "R3",
        "fault_type": "双比特翻转",
        "freqs": ['F0', 'F2'],
        "workloads": "W3 A64-DecodeProbe<br>W6 CoreMark+Embench",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c'],
    },
    "D03": {
        "unit": "Int Decode",
        "excel_row": "R4",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W3 A64-DecodeProbe<br>W6 CoreMark+Embench",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c'],
    },
    "D04": {
        "unit": "Int Decode",
        "excel_row": "R5",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W3 A64-DecodeProbe<br>W4 Rename-Dependency",
        "n_submodels": 5,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd', 'e'],
    },
    "D05": {
        "unit": "Int Decode",
        "excel_row": "R6",
        "fault_type": "错位拼接",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W3 A64-DecodeProbe<br>W6 CoreMark+Embench",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "D06": {
        "unit": "Int Decode",
        "excel_row": "R7",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W3 A64-DecodeProbe<br>W6 CoreMark+Embench",
        "n_submodels": 5,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd', 'e'],
    },
    "D07": {
        "unit": "Int Decode",
        "excel_row": "R8",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W3 A64-DecodeProbe<br>W5 ROB-Recovery",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "D08": {
        "unit": "Int Decode",
        "excel_row": "R9",
        "fault_type": "状态/时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W3 A64-DecodeProbe<br>W5 ROB-Recovery",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "D09": {
        "unit": "Int Decode",
        "excel_row": "R10",
        "fault_type": "卡死",
        "freqs": ['F5'],
        "workloads": "W3 A64-DecodeProbe<br>W6 CoreMark+Embench",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "R01": {
        "unit": "Int Rename",
        "excel_row": "R11",
        "fault_type": "单比特翻转",
        "freqs": ['F0', 'F1', 'F2'],
        "workloads": "W4 Rename-Dependency<br>W6 CoreMark+Embench",
        "n_submodels": 2,
        "impl_status": "implemented",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b'],
    },
    "R02": {
        "unit": "Int Rename",
        "excel_row": "R12",
        "fault_type": "双比特翻转",
        "freqs": ['F0', 'F2'],
        "workloads": "W4 Rename-Dependency<br>W7 GAP-Selected",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b'],
    },
    "R03": {
        "unit": "Int Rename",
        "excel_row": "R13",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W4 Rename-Dependency<br>W6 CoreMark+Embench",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b', 'c'],
    },
    "R04": {
        "unit": "Int Rename",
        "excel_row": "R14",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W4 Rename-Dependency<br>W7 GAP-Selected",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSFreeList',
        "submodels": ['a', 'b'],
    },
    "R05": {
        "unit": "Int Rename",
        "excel_row": "R15",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W4 Rename-Dependency<br>W7 GAP-Selected",
        "n_submodels": 3,
        "impl_status": "implemented",
        "injector": 'CHAOSFreeList',
        "submodels": ['a', 'b', 'c'],
    },
    "R06": {
        "unit": "Int Rename",
        "excel_row": "R16",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W4 Rename-Dependency<br>W5 ROB-Recovery",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b'],
    },
    "R07": {
        "unit": "Int Rename",
        "excel_row": "R17",
        "fault_type": "状态",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W4 Rename-Dependency<br>W5 ROB-Recovery",
        "n_submodels": 3,
        "impl_status": "implemented",
        "injector": 'CHAOSIQ',
        "submodels": ['a', 'b', 'c'],
    },
    "R08": {
        "unit": "Int Rename",
        "excel_row": "R18",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W4 Rename-Dependency<br>W5 ROB-Recovery",
        "n_submodels": 3,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c'],
    },
    "R09": {
        "unit": "Int Rename",
        "excel_row": "R19",
        "fault_type": "卡死",
        "freqs": ['F5'],
        "workloads": "W4 Rename-Dependency<br>W6 CoreMark+Embench",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B01": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R20",
        "fault_type": "单比特翻转",
        "freqs": ['F0', 'F1', 'F2'],
        "workloads": "W1 MiBench-TC23<br>W5 ROB-Recovery",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c'],
    },
    "B02": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R21",
        "fault_type": "双比特翻转",
        "freqs": ['F0', 'F2'],
        "workloads": "W1 MiBench-TC23<br>W5 ROB-Recovery",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b'],
    },
    "B03": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R22",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W7 GAP-Selected",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c'],
    },
    "B04": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R23",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W7 GAP-Selected",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B05": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R24",
        "fault_type": "状态",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W1 MiBench-TC23",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B06": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R25",
        "fault_type": "状态/换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W7 GAP-Selected",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B07": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R26",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W6 CoreMark+Embench",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSIQ',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B08": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R27",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W7 GAP-Selected",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B09": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R28",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W5 ROB-Recovery<br>W1 MiBench-TC23",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "B10": {
        "unit": "Int Dispatch / ROB",
        "excel_row": "R29",
        "fault_type": "卡死",
        "freqs": ['F5'],
        "workloads": "W5 ROB-Recovery<br>W7 GAP-Selected",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FD01": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R30",
        "fault_type": "单比特翻转",
        "freqs": ['F0', 'F1', 'F2'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 4,
        "impl_status": "implemented",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FD02": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R31",
        "fault_type": "双比特翻转",
        "freqs": ['F0', 'F2'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c'],
    },
    "FD03": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R32",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W10 PolyBench",
        "n_submodels": 4,
        "impl_status": "implemented",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FD04": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R33",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W11 libjpeg-turbo-NEON",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c'],
    },
    "FD05": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R34",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 3,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c'],
    },
    "FD06": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R35",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W13 FP-ExceptionRecovery",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSFPU',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FD07": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R36",
        "fault_type": "错位拼接",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W11 libjpeg-turbo-NEON",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FD08": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R37",
        "fault_type": "状态/时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSDecode',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FD09": {
        "unit": "FP/SIMD Decode",
        "excel_row": "R38",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FR01": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R39",
        "fault_type": "单比特翻转",
        "freqs": ['F0', 'F1', 'F2'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 3,
        "impl_status": "implemented",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b', 'c'],
    },
    "FR02": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R40",
        "fault_type": "双比特翻转",
        "freqs": ['F0', 'F2'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b'],
    },
    "FR03": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R41",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b', 'c'],
    },
    "FR04": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R42",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSFreeList',
        "submodels": ['a', 'b'],
    },
    "FR05": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R43",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 4,
        "impl_status": "implemented",
        "injector": 'CHAOSFreeList',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FR06": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R44",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W10 PolyBench<br>W13 FP-ExceptionRecovery",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b'],
    },
    "FR07": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R45",
        "fault_type": "状态",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W10 PolyBench",
        "n_submodels": 3,
        "impl_status": "implemented",
        "injector": 'CHAOSIQ',
        "submodels": ['a', 'b', 'c'],
    },
    "FR08": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R46",
        "fault_type": "错位拼接",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FR09": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R47",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 3,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c'],
    },
    "FR10": {
        "unit": "FP/SIMD Rename",
        "excel_row": "R48",
        "fault_type": "卡死",
        "freqs": ['F5'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSRenameMap',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FB01": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R49",
        "fault_type": "单比特翻转",
        "freqs": ['F0', 'F1', 'F2'],
        "workloads": "W10 PolyBench<br>W13 FP-ExceptionRecovery",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c'],
    },
    "FB02": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R50",
        "fault_type": "双比特翻转",
        "freqs": ['F0', 'F2'],
        "workloads": "W10 PolyBench<br>W13 FP-ExceptionRecovery",
        "n_submodels": 2,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b'],
    },
    "FB03": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R51",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W9 NEON-LaneProbe",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSIQ',
        "submodels": ['a', 'b', 'c'],
    },
    "FB04": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R52",
        "fault_type": "状态",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W10 PolyBench",
        "n_submodels": 3,
        "impl_status": "partial",
        "injector": 'CHAOSIQ',
        "submodels": ['a', 'b', 'c'],
    },
    "FB05": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R53",
        "fault_type": "状态",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W13 FP-ExceptionRecovery",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FB06": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R54",
        "fault_type": "换值",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W10 PolyBench<br>W11 libjpeg-turbo-NEON",
        "n_submodels": 3,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c'],
    },
    "FB07": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R55",
        "fault_type": "错位拼接",
        "freqs": ['F0', 'F2', 'F6'],
        "workloads": "W9 NEON-LaneProbe<br>W11 libjpeg-turbo-NEON",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSPhysReg',
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FB08": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R56",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W10 PolyBench<br>W13 FP-ExceptionRecovery",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FB09": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R57",
        "fault_type": "时序",
        "freqs": ['F0', 'F4', 'F6'],
        "workloads": "W8 FP-ScalarProbe<br>W13 FP-ExceptionRecovery",
        "n_submodels": 4,
        "impl_status": "unimplemented",
        "injector": None,
        "submodels": ['a', 'b', 'c', 'd'],
    },
    "FB10": {
        "unit": "FP/SIMD Dispatch/ROB",
        "excel_row": "R58",
        "fault_type": "卡死",
        "freqs": ['F5'],
        "workloads": "W9 NEON-LaneProbe<br>W10 PolyBench",
        "n_submodels": 4,
        "impl_status": "partial",
        "injector": 'CHAOSROB',
        "submodels": ['a', 'b', 'c', 'd'],
    },
}


# ---------------------------------------------------------------- 文档重解析

def _read(path):
    return io.open(path, encoding="utf-8").read()


def parse_index(text):
    """03 索引表 -> {mid: {字段}}（保持文档行序）。"""
    out, order = {}, []
    pat = re.compile(r"^\| (" + MODEL_RE + r") \| (R\d+) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (\d+) \|$")
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        mid, row, unit, fault, freqs, wls, n = m.groups()
        out[mid] = {
            "excel_row": row,
            "unit": unit,
            "fault_type": fault,
            "freqs": sorted(set(re.findall(r"F\d", freqs)), key=lambda x: int(x[1:])),
            "freqs_raw": freqs,
            "workloads": wls,
            "n_submodels": int(n),
        }
        order.append(mid)
    return out, order


def parse_audit(text):
    """09 逐模型审计表 -> {mid: (impl_status, injector)}。"""
    zh2en = {"已实现": "implemented", "部分": "partial", "未实现": "unimplemented"}
    out = {}
    pat = re.compile(r"^\| (" + MODEL_RE + r") \| (.+?) \| (.+?) \| (.+?) \| (已实现|部分|未实现) \| (.*) \|$")
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        mid, _unit, _fault, face, st, _gap = m.groups()
        first = face.split(":")[0].strip()
        out[mid] = (zh2en[st], first if first.startswith("CHAOS") else None)
    return out


def parse_submodel_letters(text):
    """03 详表行内 `<mid>-<letter>` 出现的字母集合（按字母排序）。"""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\| (" + MODEL_RE + r") \|", line)
        if not m:
            continue
        mid = m.group(1)
        ls = sorted(set(re.findall(mid + r"-([a-z])\b", line)))
        if ls:
            out[mid] = ls
    return out


def parse_items(text):
    """清单 -> [(item_id, mid, F, W)]（`### ITEM-001 — D01-F0-W3`）。"""
    return re.findall(r"^### ITEM-(\d{3}) — (" + MODEL_RE + r")-(F\d)-(W\d+)$", text, re.M)


# ---------------------------------------------------------------- --check

def run_check(index_path, audit_path, checklist_path):
    errs = []
    checklist_doc = _read(checklist_path)
    idx, order = parse_index(_read(index_path))
    audit = parse_audit(_read(audit_path))
    letters = parse_submodel_letters(_read(index_path))
    items = parse_items(checklist_doc)

    # 1) 静态表 ↔ 03 索引表（顺序 + 逐字段）
    static_ids = list(MODELS)
    if len(static_ids) != EXPECTED_MODELS:
        errs.append("静态表模型数 %d != 预期 %d" % (len(static_ids), EXPECTED_MODELS))
    if static_ids != order:
        errs.append("模型顺序/集合与 03 索引表不一致: 静态 %d vs 文档 %d" % (len(static_ids), len(order)))
    for mid in order:
        s, d = MODELS.get(mid), idx.get(mid)
        if s is None or d is None:
            continue
        for f in ("excel_row", "unit", "fault_type", "workloads", "n_submodels"):
            if s[f] != d[f]:
                errs.append("%s: 字段 %s 静态=%r 文档=%r" % (mid, f, s[f], d[f]))
        if s["freqs"] != d["freqs"]:
            errs.append("%s: freqs 静态=%r 文档=%r" % (mid, s["freqs"], d["freqs"]))

    # 2) 静态表 ↔ 09 逐模型判定 + 注入器
    for mid, (st, inj) in audit.items():
        s = MODELS.get(mid)
        if s is None:
            errs.append("09 审计表模型 %s 不在静态表" % mid)
            continue
        if s["impl_status"] != st:
            errs.append("%s: impl_status 静态=%s 文档=%s" % (mid, s["impl_status"], st))
        if s["injector"] != inj:
            errs.append("%s: injector 静态=%r 文档=%r" % (mid, s["injector"], inj))

    # 3) 子模型字母 ↔ 03 详表 + 数量 == n_submodels
    if set(letters) != set(MODELS):
        errs.append("03 详表子模型字母覆盖 %d != 57" % len(letters))
    for mid, ls in letters.items():
        s = MODELS.get(mid)
        if s and (s["submodels"] != ls or len(ls) != s["n_submodels"]):
            errs.append("%s: submodels 静态=%r 文档=%r n_submodels=%d" % (mid, s["submodels"], ls, s["n_submodels"]))

    # 4) 注入器布线：非 unimplemented ⇔ injector 非空且可挂载
    for mid, s in MODELS.items():
        if s["impl_status"] == "unimplemented":
            if s["injector"] is not None:
                errs.append("%s: unimplemented 但 injector=%r" % (mid, s["injector"]))
        elif s["injector"] is None:
            errs.append("%s: %s 但 injector 为空" % (mid, s["impl_status"]))
        elif s["injector"] not in INJECTOR_TO_FLAG:
            errs.append("%s: injector %s 无挂载旗标映射" % (mid, s["injector"]))

    # 5) 清单 ITEM 交叉：头行全可解析（无静默跳过）、310 条、编号连续 001..310、F/W 落在适用面
    raw_headers = re.findall(r"^### ITEM-\d{3}", checklist_doc, re.M)
    if len(raw_headers) != len(items):
        errs.append("清单存在头格式不匹配而被跳过的 ITEM 行: 头 %d / 可解析 %d" % (len(raw_headers), len(items)))
    if len(items) != EXPECTED_ITEMS:
        errs.append("清单条目数 %d != 预期 %d" % (len(items), EXPECTED_ITEMS))
    ids = [i for i, *_ in items]
    if ids != ["%03d" % i for i in range(1, EXPECTED_ITEMS + 1)]:
        errs.append("ITEM 编号非文档序连续 001..%03d" % EXPECTED_ITEMS)
    refs = ["%s-%s-%s" % (mid, f, w) for _i, mid, f, w in items]
    unresolved = []
    for i, mid, f, w in items:
        s = MODELS.get(mid)
        if s is None:
            unresolved.append("ITEM-%s: 未知模型 %s" % (i, mid))
            continue
        if f not in s["freqs"]:
            unresolved.append("ITEM-%s: %s 频率 %s 不在 %s" % (i, mid, f, s["freqs"]))
        if w not in re.findall(r"W\d+", s["workloads"]):
            unresolved.append("ITEM-%s: %s 负载 %s 不在适用表" % (i, mid, w))
    if len(ids) != len(set(ids)):
        errs.append("清单存在重复 ITEM 编号")
    if len(refs) != len(set(refs)):
        errs.append("清单存在重复 模型-频率-负载 引用")
    errs.extend(unresolved)

    from collections import Counter

    c = Counter(s["impl_status"] for s in MODELS.values())
    print("models: %d | items_scanned: %d | item_refs_resolved: %d | unresolved: %d"
          % (len(MODELS), len(items), len(items) - len(unresolved), len(unresolved)))
    print("impl_status: implemented=%d partial=%d unimplemented=%d"
          % (c["implemented"], c["partial"], c["unimplemented"]))
    if errs:
        print("CHECK FAILED: %d 项不一致" % len(errs), file=sys.stderr)
        for e in errs[:20]:
            print("  - %s" % e, file=sys.stderr)
        return 1
    print("OK: 静态表 ↔ 03 索引/详表 ↔ 09 逐模型判定 ↔ 清单 ITEM 三方一致")
    return 0


# ---------------------------------------------------------------- --item

def _print_model(mid):
    s = MODELS[mid]
    print("%s [%s] %s | excel %s | %s"
          % (mid, s["unit"], s["fault_type"], s["excel_row"], STATUS_ZH[s["impl_status"]]))
    print("  freqs: %s | submodels(%d): %s"
          % (" ".join(s["freqs"]), s["n_submodels"], " ".join(s["submodels"])))
    if s["injector"]:
        print("  injector: %s (mount: %s)" % (s["injector"], INJECTOR_TO_FLAG[s["injector"]]))
    else:
        print("  injector: —（未实现，无覆盖模式）")
    print("  workloads: %s" % s["workloads"])


def run_item(spec):
    items = parse_items(_read(DEFAULT_CHECKLIST))
    if re.match(r"^ITEM-\d{3}$", spec):
        hits = [t for t in items if t[0] == spec[5:]]
        if not hits:
            print("未找到 %s（清单共 %d 条）" % (spec, len(items)), file=sys.stderr)
            return 1
        _i, mid, f, w = hits[0]
        _print_model(mid)
        print("  this_item: %s (freq %s, workload %s)" % (spec, f, w))
        same = [i for i, m, _f, _w in items if m == mid]
        print("  model_items: %s" % " ".join("ITEM-" + i for i in same))
        return 0
    if re.match("^%s$" % MODEL_RE, spec):
        if spec not in MODELS:
            print("未知模型 %s" % spec, file=sys.stderr)
            return 1
        _print_model(spec)
        same = [i for i, m, _f, _w in items if m == spec]
        print("  model_items(%d): %s" % (len(same), " ".join("ITEM-" + i for i in same)))
        return 0
    print("参数须为 ITEM-NNN 或模型 ID（如 D01）", file=sys.stderr)
    return 2


def main():
    ap = argparse.ArgumentParser(description="OOO 57 模型机读映射表（P1 U1）")
    ap.add_argument("--check", action="store_true", help="三方一致性校验")
    ap.add_argument("--item", metavar="SPEC", help="ITEM-NNN 或模型 ID")
    ap.add_argument("--index", default=str(DEFAULT_INDEX), help="03 矩阵路径")
    ap.add_argument("--audit", default=str(DEFAULT_AUDIT), help="09 审计路径")
    ap.add_argument("--checklist", default=str(DEFAULT_CHECKLIST), help="清单路径")
    a = ap.parse_args()
    if a.check:
        sys.exit(run_check(a.index, a.audit, a.checklist))
    if a.item:
        sys.exit(run_item(a.item))
    ap.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
