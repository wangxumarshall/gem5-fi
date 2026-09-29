#!/usr/bin/env python3
"""P0 预检：核验 完整任务执行清单.md 的结构完整性。

校验项（对应 task_plan.md P0 清单）：
  C1  ITEM 数量 = 325，编号 ITEM-001..ITEM-325 连续无重复
  C2  RunID 数量 = 325 且唯一
  C3  模型数 = 64（唯一模型ID）
  C4  Excel 行映射 = 第 2..326 行，逐项一一对应
  C5  频率分布与文件头表一致（F0:105 F1:24 F2:77 F3:4 F4:26 F5:25 F6:64）
  C6  单元分布与文件头表一致（L1d-Cache:14 Store Queue:12 L1d-TLB:9 数据预取器:9 AGU:8 原子与同步:8 Load Queue:4）
  C7  每个 ITEM 均含必需设计字段（Excel定位/RunID/模型ID/单元/频率/负载/注入位置/故障类型/触发条件）
"""
import re
import sys
from collections import Counter

CHECKLIST = "/home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/完整任务执行清单.md"

EXPECTED_FREQ = {"F0": 105, "F1": 24, "F2": 77, "F3": 4, "F4": 26, "F5": 25, "F6": 64}
EXPECTED_UNIT = {
    "L1d-Cache": 14, "Store Queue": 12, "L1d-TLB": 9, "数据预取器": 9,
    "AGU": 8, "原子与同步": 8, "Load Queue": 4,
}
REQUIRED_FIELDS = [
    "Excel 定位", "RunID", "模型ID", "单元", "频率", "负载",
    "注入位置", "故障类型", "触发条件",
]

def main():
    with open(CHECKLIST, encoding="utf-8") as f:
        text = f.read()

    # 按照 ITEM 标题切块（第 8 节）
    item_pattern = re.compile(r"^### (ITEM-(\d{3})) — (.+)$", re.M)
    matches = list(item_pattern.finditer(text))
    failures = []

    # C1: ITEM 数量与连续性
    item_nums = [int(m.group(2)) for m in matches]
    c1 = (
        len(matches) == 325
        and item_nums == list(range(1, 326))
        and len(set(item_nums)) == 325
    )
    if not c1:
        failures.append(f"C1: ITEM 数量={len(matches)}, 唯一={len(set(item_nums))}, 连续={item_nums == list(range(1, 326))}")

    # 切出每个 ITEM 的文本块
    blocks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(1), m.group(3), text[start:end]))

    # C2: RunID 唯一性
    runids = [b[1] for b in blocks]
    c2 = len(runids) == 325 and len(set(runids)) == 325
    if not c2:
        dup = [r for r, n in Counter(runids).items() if n > 1]
        failures.append(f"C2: RunID 数量={len(runids)}, 唯一={len(set(runids))}, 重复={dup[:5]}")

    # 逐块解析字段
    excel_rows, models, freqs, units = [], [], [], []
    missing_fields = []
    for item, runid, block in blocks:
        # Excel 行：`7.展开执行矩阵!A<row>:AQ<row>`
        em = re.search(r"7\.展开执行矩阵!A(\d+):AQ(\d+)", block)
        if not em:
            missing_fields.append(f"{item}: 无Excel定位")
            excel_rows.append(None)
        else:
            r1, r2 = int(em.group(1)), int(em.group(2))
            if r1 != r2:
                missing_fields.append(f"{item}: Excel行范围跨行 {r1}-{r2}")
            excel_rows.append(r1)
        # 模型ID / 单元 / 频率（字段行）
        mm = re.search(r"^- \*\*模型ID：\*\* `?([^`\n]+)`?", block, re.M)
        um = re.search(r"^- \*\*单元：\*\* (.+)$", block, re.M)
        fm = re.search(r"^- \*\*频率：\*\* `(F\d)`", block, re.M)
        models.append(mm.group(1) if mm else None)
        units.append(um.group(1).strip() if um else None)
        freqs.append(fm.group(1) if fm else None)
        # 必需字段存在性
        for field in REQUIRED_FIELDS:
            if f"**{field}：" not in block and f"**{field}:**" not in block:
                missing_fields.append(f"{item}: 缺字段 {field}")

    # C4: Excel 行映射 2..326
    expected_rows = list(range(2, 327))
    c4 = excel_rows == expected_rows
    if not c4:
        bad = [(blocks[i][0], excel_rows[i]) for i in range(len(excel_rows))
               if excel_rows[i] != expected_rows[i]]
        failures.append(f"C4: Excel行映射不符, 前5个异常={bad[:5]}")

    # C3: 模型数
    uniq_models = sorted(m for m in set(models) if m)
    c3 = len(uniq_models) == 64
    if not c3:
        failures.append(f"C3: 唯一模型数={len(uniq_models)}")

    # C5: 频率分布
    freq_counter = Counter(f for f in freqs if f)
    c5 = dict(freq_counter) == EXPECTED_FREQ
    if not c5:
        failures.append(f"C5: 频率分布={dict(freq_counter)} 期望={EXPECTED_FREQ}")

    # C6: 每单元唯一模型数（头表"模型按单元分布"统计的是模型数，不是ITEM数）
    unit_counter = Counter(u for u in units if u)
    unit_model = {}
    for m, u in zip(models, units):
        if m and u:
            unit_model.setdefault(u, set()).add(m)
    unit_model_count = {u: len(s) for u, s in unit_model.items()}
    c6 = unit_model_count == EXPECTED_UNIT
    if not c6:
        failures.append(f"C6: 每单元模型数={unit_model_count} 期望={EXPECTED_UNIT}")

    # 报告
    print(f"ITEM 总数: {len(matches)}")
    print(f"唯一 RunID: {len(set(runids))}")
    print(f"唯一模型数: {len(uniq_models)}")
    print(f"Excel 行映射范围: {min(r for r in excel_rows if r)}..{max(r for r in excel_rows if r)}")
    print(f"频率分布(按ITEM): {dict(sorted(freq_counter.items()))}")
    print(f"ITEM按单元分布: {dict(sorted(unit_counter.items()))}")
    print(f"模型按单元分布: {dict(sorted(unit_model_count.items()))}")
    print(f"缺失字段/异常: {len(missing_fields)}")
    for mf in missing_fields[:10]:
        print(f"  - {mf}")
    print()
    for cid, ok in [("C1", c1), ("C2", c2), ("C3", c3), ("C4", c4), ("C5", c5), ("C6", c6)]:
        print(f"{cid}: {'PASS' if ok else 'FAIL'}")
    print(f"C7(必需字段): {'PASS' if not missing_fields else 'FAIL'}")

    if failures or not all([c1, c2, c3, c4, c5, c6]) or missing_fields:
        print("\nOVERALL: FAIL")
        for f_ in failures:
            print(f"  FAIL详情: {f_}")
        sys.exit(1)
    print("\nOVERALL: PASS — 64 模型 / 325 ITEM / 325 唯一 RunID / Excel 行 2..326 映射全部核验通过")

if __name__ == "__main__":
    main()
