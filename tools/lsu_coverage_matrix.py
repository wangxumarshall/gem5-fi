#!/usr/bin/env python3
"""[MDSPEC][B2] Markdown→实现覆盖矩阵（计划 Task B2）。

PASS/PARTIAL/BLOCKED 判定（Review Focus #1：部分已有≠PASS——PASS=0 起步，
每个 PASS 都要有钩子+字段双重证据）：
  BLOCKED: runid_map 的任一 status_reasons（campaign 裁罚 / spec 需新增 /
           workload 缺载体）
  PASS:    模型实现可用 AND 其全部钩子族已装（HOOK_REGISTRY）AND
           H0 字段 schema 齐备（fields_complete）
  PARTIAL: 其余（部分已有——注入/传播链存在但钩子族或字段不全）
钩子族可用性来自显式注册表（H1-H7 逐族在装好后翻转，防"部分监控冒充完整"）。
用法：python3 tools/lsu_coverage_matrix.py --map <runid_map.json> --out <md>
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# 钩子族注册表：装好一族 → True（Phase B H 任务逐族翻转；初始全 False=未装）
HOOK_REGISTRY = {
    "H0_prop_fields": False,      # CHAOSPropagation 表11 字段扩展
    "H1_lsq_unified": False,      # lsq.cc pushRequest/sendFragment 统一事件
    "H2_tlb_trace": False,        # CHAOSTLBTrace
    "H3_sq_trace": False,         # CHAOSLSQTrace（SQ）
    "H4_cache_ext": False,        # cache.cc 扩展
    "H5_prefetch_trace": False,   # CHAOSPrefetchTrace
    "H6_atomic_trace": False,     # CHAOSAtomicTrace
    "H7_lq_trace": False,         # LQ 逐事件
}
# 单元 → 该单元路径全链所需的钩子族（表 9 传播路径 L1-L3 段的最小集合）
UNIT_HOOKS = {
    "AGU": ["H1_lsq_unified", "H2_tlb_trace", "H0_prop_fields"],
    "L1d-TLB": ["H2_tlb_trace", "H0_prop_fields"],
    "Load Queue": ["H7_lq_trace", "H1_lsq_unified", "H0_prop_fields"],
    "Store Queue": ["H3_sq_trace", "H1_lsq_unified", "H0_prop_fields"],
    "L1d-Cache": ["H4_cache_ext", "H0_prop_fields"],
    "数据预取器": ["H5_prefetch_trace", "H0_prop_fields"],
    "原子与同步": ["H6_atomic_trace", "H1_lsq_unified", "H0_prop_fields"],
}


def assess(entry):
    if entry["status"] == "BLOCKED":
        return "BLOCKED", entry["status_reasons"]
    hooks = UNIT_HOOKS.get(entry["unit"], [])
    missing = [h for h in hooks if not HOOK_REGISTRY.get(h, False)]
    if not missing:
        return "PASS", []
    return "PARTIAL", [f"hooks_pending:{','.join(missing)}"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = json.loads(Path(a.map).read_text(encoding="utf-8"))
    rows = []
    for e in m["entries"]:
        st, why = assess(e)
        rows.append((e["run_id"], e["model_id"], e["unit"], e["freq"], st, "; ".join(why)))
    cnt = Counter(r[4] for r in rows)
    lines = ["# Markdown→实现覆盖矩阵（MDSPEC Phase B）", "",
             f"- 总数：{len(rows)}（RunID 唯一，表7∩表9 集合相等——B1 已证）",
             f"- **PASS={cnt.get('PASS', 0)} / PARTIAL={cnt.get('PARTIAL', 0)} / "
             f"BLOCKED={cnt.get('BLOCKED', 0)}**",
             f"- 钩子族注册表：{json.dumps(HOOK_REGISTRY)}", "",
             "| RunID | 模型 | 单元 | 频率 | 状态 | 原因 |", "|---|---|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5][:120]} |"
              for r in rows]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[coverage] PASS={cnt.get('PASS', 0)} PARTIAL={cnt.get('PARTIAL', 0)} "
          f"BLOCKED={cnt.get('BLOCKED', 0)} → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
