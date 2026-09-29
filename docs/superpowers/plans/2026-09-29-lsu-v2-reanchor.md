# LSU V2.0 原位重锚 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `docs/gem5-fi/lsu/` 从 V1.0 口径原位重锚到 V2.0 xlsx（64 模型/325 格/43 列/新分类学），产出北极星 + 完整实现方案 + 宏伟计划，全部内容以 V2.0 为准。

**Architecture:** 五层文档体系（README 索引 / NORTH-STAR 北极星 / 00–08+2CSV 转录层 / 09-v2 现行计划+旧 09 封存 / 10–11 历史层）。转录层由 extract.py（机器，生成 03/07+2CSV）+ 人工转录（00/01/02/04/05/06/08，verify 片段校验）构成——与 V1.0 史同构。

**Tech Stack:** Python 3 stdlib only（zipfile + xml.etree；本机无 openpyxl/pandas，pip 403）；markdown 文档；git。

**Spec:** `docs/superpowers/specs/2026-09-29-lsu-v2-reanchor-design.md`（五决策 D1–D5、全部口径与验收；执行者必读，本计划从 spec 论证）

## Global Constraints

- **一切以 V2.0 为准**：源 `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V2.0.xlsx`，sha256 `1f65293669a6bf8a1bcc678555d4a5f2f56193e94fa90e453396c6fbc512441c`。V1.0 xlsx（sha `2703f812…713651`）留档不动。
- **核心数字**：64 模型（A8/T9/S12/C14/O8/P9/L4）；325 运行；design-matrix.csv 65 逻辑行×15 列（Excel行+14 源列）；07-expanded-matrix.csv 326 逻辑行×44 列（Excel行+43 源列）；col26 黄格 65+蓝 260；col43 浅蓝 `FFD9E2F3` 全 325；APPENDED_IDS 10 个不变。
- **D4 裁决**：表3 col10 vs 表7 col12 在 AGU 系 8 模型 39 运行不同步 → 表7 为执行权威；表3 照实转录 + 注记；A1 重放对这 39 格豁免并精确计数 39。
- **不变量**：表1/表6/表8 值零变化 → `01-units-and-research.md`、`06-workloads.md`、`08-references.md` 三文件**逐字节不变**（Task 1/7 验证）。
- **源永远是对的**：A1 重放失败时调整推导常量/发现新特例并照实转录，绝不"修正"源表。
- **分支纪律**：fi-ding 分支；每 Task 一个 commit，验证通过才提交，提交即 push（push 被拒先 `git pull --rebase origin fi-ding`——并行会话常在）；**绝不 `git add -A`**，一律显式路径；commit message 不加 Co-Authored-By 尾注。
- **文档中文**；脚本注释风格沿用现状（中英混合）。
- /tmp/lsu_v2/ 的探索 dump 可能已不存在——一切以 xlsx 直读为准（计划附录已固化全部探测事实）。

---

### Task 1: extract.py V2.0 化 + 四个机器产物再生

**Files:**
- Modify: `docs/gem5-fi/lsu/extract.py`
- Create(再生): `docs/gem5-fi/lsu/03-design-matrix.md`、`docs/gem5-fi/lsu/design-matrix.csv`、`docs/gem5-fi/lsu/07-expanded-matrix.csv`、`docs/gem5-fi/lsu/07-expanded-matrix.md`

**Interfaces:**
- Consumes: V2.0 xlsx（9 表结构见附录 B）
- Produces: extract.py 末行输出 `EXTRACTION VERIFICATION PASSED`；design-matrix.csv 表头 `Excel行` + 14 列；07-expanded-matrix.csv 表头 `Excel行` + 43 列（列名见下方 SHEET7_COLS）——Task 3 的 verify 逐格消费这两个 CSV。

- [ ] **Step 1: 读现状**：Read `docs/gem5-fi/lsu/extract.py` 全文（284 行）与本计划的附录 B 事实卡。

- [ ] **Step 2: 改常量区**（文件头 docstring 同步改数字与描述）：

```python
XLSX = HERE / 'gem5-fi-LSU单元故障注入方案V2.0.xlsx'
EXPECT_SHA256 = '1f65293669a6bf8a1bcc678555d4a5f2f56193e94fa90e453396c6fbc512441c'

SHEET3_COLS = ['模型ID', '单元', '注入位置（结构与正常作用）', '故障类型',
               '故障模型（实施步骤与激活口径）', '故障表现形式/子模型', '适用频率', '适用负载（真实名称）',
               '事件触发条件', '传播链重点观测', '预期结果（待验证假设）',
               '设计理由', '文献依据/直接性', '保护机制归属']
SHEET7_COLS = ['RunID', '模型ID', '单元', '注入位置（结构与正常作用）', '故障类型',
               '故障模型（实施步骤与激活口径）', '频率', '频率定义', '负载（真实名称）',
               '负载定义/oracle', '触发条件', '传播监控', '预期结果', '设计理由', '文献依据',
               'Seed/注入索引', 'Attempted', 'Activated', 'Masked', 'Detected-contained',
               'Data Corruption', 'Crash', 'Timeout', 'SDC率(可分析activated)', '激活率',
               '记录状态', '实测备注',
               'SDC', 'Hardware RAS首检（互斥）', 'OS首检（互斥）', 'Application首检（互斥）',
               'None首检（互斥）', 'Contained', 'Detected-uncontained', 'RAS-silent Crash',
               'RAS-silent Timeout', '检测/告警证据', '硬件RAS检测率(任意时点)',
               '检测计数差额（应为0）', '结局计数差额（应为0）', 'Hardware RAS检测（任意时点）',
               'Simulator failure', '故障表现形式/子模型']
# APPENDED_IDS 10 个不变；注释改为"V2.0 行序按单元重排，追加模型不再位于表尾连续区，只能按 ID 集合识别"
APPENDED_IDS = ['T10', 'S13', 'L01', 'L02', 'L03', 'L04', 'C14', 'C15', 'O09', 'P09']
```

- [ ] **Step 3: 设计矩阵循环**——A2 68→64；R9 位置断言（`r >= 60`）替换为集合断言（V2.0 表3 r2–r65，追加模型散布各单元节，最后 10 行是 O09+P01–P09 而非追加集）：

```python
    if len(design) != 64:
        die(f'A2: 设计矩阵应为 64 行, 实得 {len(design)}')
    if not set(APPENDED_IDS) <= set(design):
        die(f'R9: 完善版追加 ID 缺失: {sorted(set(APPENDED_IDS) - set(design))}')
```

- [ ] **Step 4: A1 重放列位移 + 39 格豁免 + col43**——表3 因 col6 插入，col≥7 全部 +1：适用频率 `g.get(6)`→`g.get(7)`、适用负载 `g.get(7)`→`g.get(8)`、触发/传播/预期/理由/文献 `g.get(8..12)`→`g.get(9..13)`。rebuilt 扩为 43 列（15 派生 + 10 空 + ['待执行',''] + 15 空 + 表3 col6 菜单）：

```python
    rebuilt = []
    for mid, (erow, g) in design.items():
        freqs = [t.strip() for t in g.get(7, '').split('/') if t.strip()]
        entries = [e for e in g.get(8, '').split('\n') if e.strip()]
        for e in entries:
            if sum(1 for nm in wname if e.startswith(nm)) != 1:
                die(f'A4: 负载条目前缀匹配数 != 1: {mid} {e[:30]!r}')
        for f in freqs:
            for e in entries:
                wid = next(wname[nm] for nm in wname if e.startswith(nm))
                col8 = F6_OVERRIDE_TEXT if (f == 'F6' and mid in F6_OVERRIDE_MODELS) else freq_def[f]
                col10 = e + '\n执行定义与 oracle：' + (W11_ORACLE if wid == 'W11' else wdef[wid])
                rebuilt.append([f'{mid}-{f}-{wid}', mid, g.get(2, ''), g.get(3, ''),
                                g.get(4, ''), g.get(5, ''), f, col8, e, col10,
                                g.get(9, ''), g.get(10, ''), g.get(11, ''), g.get(12, ''),
                                g.get(13, '')] + [''] * 10 + ['待执行', ''] + [''] * 15
                               + [g.get(6, '')])
    actual_rows = [ex[r] for r in sorted(ex)[1:]]
    if len(actual_rows) != 325 or len(rebuilt) != 325:
        die(f'A2: 展开矩阵应为 325 行, 重放 {len(rebuilt)}, 源表 {len(actual_rows)}')
    exempt = []
    for i, (reb, act) in enumerate(zip(rebuilt, actual_rows)):
        for c in range(43):
            if reb[c] != act.get(c + 1, ''):
                if c == 11 and reb[1].startswith('A'):  # D4: AGU 系 col12 表7 已更新、表3 仍旧文
                    exempt.append(reb[0])
                    continue
                die(f'A1: 第 {i + 1} 行列 {c + 1} 不等: 重放 {reb[c][:40]!r} vs 源 {act.get(c + 1, "")[:40]!r}')
    if len(exempt) != 39 or not all(r.startswith('A') for r in exempt):
        die(f'A1: col12 豁免应为 AGU 系 39 格, 实得 {len(exempt)}: {exempt[:5]}…')
```

- [ ] **Step 5: A3 结果槽扩展**——空槽从 `range(16,26)+[27]` 改为 `range(16,26)+range(27,43)`；新增 col43 非空：

```python
    for i, act in enumerate(actual_rows):
        if any(act.get(c, '') != '' for c in list(range(16, 26)) + list(range(27, 43))):
            die(f'A3: 第 {i + 1} 行结果槽非空')
        if act.get(26, '') != '待执行':
            die(f'A3: 第 {i + 1} 行记录状态 != 待执行')
        if act.get(43, '') == '':
            die(f'A3: 第 {i + 1} 行 col43 子模型菜单为空')
```

- [ ] **Step 6: A6 颜色重写**（V2.0 实测：col1–15 无填充；col16–23/27/28–37/41/42 **无数据格**；col24/25 仅 6 模板行蓝、col38/39/40 仅 5 格蓝；col26 = 65 黄 + 260 蓝；col43 全 `FFD9E2F3`）：

```python
    for L in 'ABCDEFGHIJKLMNO':
        if set(col_fill.get(L, Counter())) - {''}:
            die(f'A6: col1-15 出现填充 {L}: {dict(col_fill[L])}')
    for L in ['P','Q','R','S','T','U','V','W','AA','AB','AC','AD','AE','AF','AG',
              'AH','AI','AJ','AK','AO','AP']:  # col16-23/27/28-37/41-42 不应有带填充的数据格
        if set(col_fill.get(L, Counter())) - {''}:
            die(f'A6: col {L} 不应有填充: {dict(col_fill[L])}')
    for L, want in (('X', 6), ('Y', 6), ('AL', 5), ('AM', 5), ('AN', 5)):
        if col_fill.get(L, Counter()) != Counter({BLUE: want}):
            die(f'A6: col {L} 应为 {want} 格蓝, 实得 {dict(col_fill.get(L, {}))}')
    yellow26 = {ex[r][1] for r in sorted(ex)[1:] if cell_fill.get(('Z', r)) == YELLOW}
    if len(yellow26) != 65:
        die(f'A6: col26 黄格应为 65, 实得 {len(yellow26)}')
    allruns = {ex[r][1] for r in sorted(ex)[1:]}
    want26 = ({rid for rid in allruns if rid.split('-')[0] in APPENDED_IDS}
              - {rid for rid in allruns if rid.startswith('T10-')}
              - {rid for rid in allruns if rid.startswith('S13-F0-')})
    if yellow26 != want26:
        die(f'A6: col26 黄色集合 != 完善版格−T10−S13(F0) (差 {len(yellow26 ^ want26)})')
    for r in sorted(ex)[1:]:
        if cell_fill.get(('AQ', r)) != 'FFD9E2F3':
            die(f'A6: col43 应全浅蓝 FFD9E2F3, r{r} 实得 {cell_fill.get(("AQ", r))!r}')
```

- [ ] **Step 7: 输出区**——design CSV/03 md 单元格范围 `range(1,13)`→`range(1,15)`；07 CSV `range(1,28)`→`range(1,44)`；03 md 头注改为"Excel r2–r65，64 个设计模型，14 列全列"，完善版注记改为"源表总览 r25 自述'原58条模型扩展为64条'；V2.0 行序按单元重排，追加模型不再位于表尾"，并**新增一行提取注记**："V2.0 提取注记：col10「传播链重点观测」在 AGU 系 8 模型（39 运行）仍为旧文，表7 col12 已更新为'L5检测层级、控制情况与最终结局'——裁决表7 为执行权威（spec D4），本表照实转录"。07 md 全部重写：头注 r2–r326/325 格×43 列；列语义表按 43 列分七段（1–15 源数据 / 16–23 人工录入槽空 / 24–25 自动计算含 6 模板行公式 / 26 记录状态 65黄+260蓝 / 27 实测备注空 / 28–42 新分类学结果槽空+col38–40 模板行公式 / 43 子模型菜单浅蓝预填=表3 col6）；分布汇总计数自动生成（完善版行改为 10 模型 77 格、原 54 模型 248 格——用 `sum(1 for a in actual_rows if a.get(2,'') in APPENDED_IDS)` 计算，若≠77 如实输出实值）；源表特例六条：①AGU 39 格 col12（D4 裁决+豁免计数）②13 行 F6 col8 覆盖③12 行 W11 col10 覆盖④结果槽 col16–25/27–42 全空⑤col43 预填=表3 col6 菜单⑥公式仅存 6 模板行 r2/66/130/194/258/322（col24/25/38/39/40）。末尾 print 数字改 64/325。

- [ ] **Step 8: 运行并迭代**：`cd /home/sdc/gem5-fi-lsu/docs/gem5-fi/lsu && python3 extract.py` → 预期末行 `EXTRACTION VERIFICATION PASSED`。若 A1 失败：逐格看重放 vs 源差异——源是对的：新覆盖特例则照实加常量；大面积行序错位则查表7 实际行序并调整 rebuilt 排序匹配源。若 A6/A3 失败：对照附录 B 事实卡核数。**禁止**为通过校验而放宽断言数字（65/39/6/5 等都是源事实）。

- [ ] **Step 9: diff 审查**：`git diff --stat` + 逐文件看 03/07 md 与两个 CSV——变化应与附录 B/SPEC §4.3 一一对应；确认 `git status` 里 **01/06/08 三个 md 不出现**（零变化不变量）。

- [ ] **Step 10: Commit + push**

```bash
git add docs/gem5-fi/lsu/extract.py docs/gem5-fi/lsu/03-design-matrix.md docs/gem5-fi/lsu/design-matrix.csv docs/gem5-fi/lsu/07-expanded-matrix.csv docs/gem5-fi/lsu/07-expanded-matrix.md
git commit -m "feat(lsu): V2.0 重提取机器 — extract.py 64/325/43列 + A1 39格D4豁免 + A6新颜色图，四产物再生"
git pull --rebase origin fi-ding && git push
```

### Task 2: 00/02/04/05 人工重转录（V2.0 变更四表）

**Files:**
- Modify: `docs/gem5-fi/lsu/00-overview.md`（表0）、`docs/gem5-fi/lsu/02-parameter-baseline.md`（表2）、`docs/gem5-fi/lsu/04-observation-points.md`（表4 整表重写）、`docs/gem5-fi/lsu/05-frequency-and-sampling.md`（表5）

**Interfaces:**
- Consumes: 附录 A 的 V2.0 四表全文（转录底稿）；各文件现有格式约定（先 Read 再改）
- Produces: 四个 md 的 V2.0 版内容——Task 3 的 V4a/V4b 片段校验依赖其中的关键句

- [ ] **Step 1: Read 四个 md 现状**，掌握各自表格式与"源行映射"注记约定。
- [ ] **Step 2: 00-overview.md**——对照附录 A.1 逐行更新：新增 r23 判定边界⑥（全文照录）；r25 "原58条模型扩展为64条"；r10 表3 描述（含"故障子模型…保护机制"）；r14 表7 描述（运行级独立样本/首检/结局/子模型）；r11 保持"SDC率分母只用activated"照录，但在提取注记加一句："表0 r11 为简写，统计口径以表5 r12'可分析activated=activated−Simulator failure'及表7 col24 公式为准"。源行映射注记 r1–r25。
- [ ] **Step 3: 02-parameter-baseline.md**——参数表删除"L1D ECC/parity=关闭"行（源行映射改 r2–r19，18 参数）；表格后新增"逐单元保护机制核验（源 r21–r29，只列实际存在且纳入实现的机制）"小节：合并标题行 + 5 列×7 单元表格，内容照录附录 A.2（AGU/L1d-TLB/Load Queue/Store Queue/L1d-Cache/原子与同步/数据预取器）。
- [ ] **Step 4: 04-observation-points.md**——整表重写为附录 A.3 的 V2.0 版（6 列×L0–L5 六层，L5 行含新分类学全文）；删除 V1 守恒式提取注，替换为"V2.0 以首检来源互斥 + Simulator failure 分栏 + 两条守恒列（表7 col39/40）替代 V1 守恒式"。
- [ ] **Step 5: 05-frequency-and-sampling.md**——频率表加"统计单位"列（F0/F5/F6=run-level独立样本；F1–F4=run-level cluster；事件级仅作传播记录）；统计规则表更新为附录 A.4 的 r11–r20 九行（首行"分母与二维分类"为新口径全文；"独立样本单位""重复注入归因"两行为 V2.0 新增/改写）。
- [ ] **Step 6: 验证**：`git diff` 仅这四个文件；`git status` 确认 01/06/08 未动；对附录 A 逐行核对无遗漏、无添加（转录保真，不润色）。
- [ ] **Step 7: Commit + push**

```bash
git add docs/gem5-fi/lsu/00-overview.md docs/gem5-fi/lsu/02-parameter-baseline.md docs/gem5-fi/lsu/04-observation-points.md docs/gem5-fi/lsu/05-frequency-and-sampling.md
git commit -m "docs(lsu): 00/02/04/05 V2.0 重转录 — 判定边界⑥/保护核验节/L0-L5重写/统计单位与新口径"
git pull --rebase origin fi-ding && git push
```

### Task 3: verify_extraction.py V2.0 化（独立校验链）

**Files:**
- Modify: `docs/gem5-fi/lsu/verify_extraction.py`

**Interfaces:**
- Consumes: Task 1 的两个 CSV + Task 2 的四个 md + V2.0 xlsx（独立重解析，**不 import extract.py**——沿用现状）
- Produces: 末行 `ALL PASSED`——Task 7 全局审计的依赖

- [ ] **Step 1: Read verify_extraction.py 全文**（213 行），掌握 V1/V2/V3/V4a/b/c 结构与片段断言写法。
- [ ] **Step 2: 更新既有链**：源路径/sha → V2.0；V1 design 逐格 65 行×15 列；V2 expanded 逐格 326 行×44 列；V3 集合断言 64 模型/325 RunID/APPENDED_IDS 10 个/RunID 格式与负载前缀；V4a/b 片段改为 Task 2 后的关键句（00 的⑥句、02 的保护核验节标题、04 的 L5 新分类学句、05 的"可分析activated"句）；V4c README 片段留待 Task 7 后最终核对（本 Task 先注释掉 README 片段或在 Task 7 补——选择：本 Task 保留旧 README 片段会让 ALL PASSED 失败，故**本 Task 起将 V4c 改为仅检查 README 存在 + V2.0 sha 字符串出现**，Task 7 再补全片段）。
- [ ] **Step 3: 新增断言组 V5**（全部从 V2.0 xlsx 独立重解析）：
  1. col43 每行非空且 == 该行模型在表3 col6 的菜单文本；
  2. col26 全"待执行"；col16–25、col27–42 全空；
  3. 39 格豁免精确枚举：独立重放表3 叉积（同 Task 1 逻辑但独立实现），收集 col12 不等的 RunID 集合，断言 == 39 个且全部 `A` 前缀，并输出清单；
  4. col39/40 表头存在（"检测计数差额（应为0）"/"结局计数差额（应为0）"）；公式模板行 r2/66/130/194/258/322 的 col24/25/38/39/40 存在 `<f>` 公式（27 格）；
  5. **零变化表不变量**：`01-units-and-research.md`、`06-workloads.md`、`08-references.md` 的 git HEAD 版本与工作区逐字节相同（`git show HEAD:<path>` 比对）；
  6. 表1/表6/表8 的 xlsx 值与 01/06/08 md 转录抽查（各 3 格）。
- [ ] **Step 4: 运行**：`cd /home/sdc/gem5-fi-lsu/docs/gem5-fi/lsu && python3 verify_extraction.py` → 末行 `ALL PASSED`。失败则修 verify 或回溯 Task 1/2（**不得**为通过而删断言）。
- [ ] **Step 5: Commit + push**

```bash
git add docs/gem5-fi/lsu/verify_extraction.py
git commit -m "feat(lsu): verify_extraction.py V2.0 — 65x15/326x44 逐格 + V5 新断言组(39格枚举/col43一致性/零变化不变量)"
git pull --rebase origin fi-ding && git push
```

### Task 4: 10/11 历史层标注

**Files:**
- Modify: `docs/gem5-fi/lsu/10-trial-results.md`、`docs/gem5-fi/lsu/11-meta-analysis.md`

**Interfaces:** 无下游依赖（Task 5/6 引用其"历史轮"地位）。

- [ ] **Step 1: 两文件顶部（标题行后）插入统一标注块**（正文零改动）：

```markdown
> **【V1.0 历史轮标注（2026-09-29 重锚时加）】** 本文件数据为 V1.0 口径：337 格、旧五分类
> （Masked/Detected/SDC/Crash/Timeout）、旧守恒式 Activated = Masked+Detected+SDC+Crash+Timeout。
> 地位：V1.0 轮试跑证据，数据不作废，不与 V2.0 新轮直接比较。V2.0 已删除其中 12 格
> （T09/S12/C13/O08 × F0/F5/F6——本试跑轮"不适用 6 格"结论的形式化）；其余试跑数据格只能经
> V2-W1 的旧→新分类学映射器做**有损**对照（旧 Crash/Timeout 无法回溯判定 RAS/OS 检出状态）。
> 新轮结果写入 V2.0 版 07-expanded-matrix.csv 的 col16–25/col27–42，不覆盖本文件。
> 现行方案见 NORTH-STAR.md 与 09-implementation-plan-v2.md。
```

- [ ] **Step 2: 验证**：`git diff` 仅两文件顶部插入，正文零改动（`git diff` 逐行看）。
- [ ] **Step 3: Commit + push**

```bash
git add docs/gem5-fi/lsu/10-trial-results.md docs/gem5-fi/lsu/11-meta-analysis.md
git commit -m "docs(lsu): 10/11 加 V1.0 历史轮标注 — 旧口径声明/与V2.0关系/有损映射边界"
git pull --rebase origin fi-ding && git push
```

### Task 5: NORTH-STAR.md 新建（北极星层）

**Files:**
- Create: `docs/gem5-fi/lsu/NORTH-STAR.md`

**Interfaces:** Task 6/7 的 README 文档地图引用它；内容数字必须与 10/11/09 交叉一致。

- [ ] **Step 1: Read** `09-implementation-plan.md` §1（三问原文）与 `10-trial-results.md`、`11-meta-analysis.md`（遗产数字）。
- [ ] **Step 2: 写 NORTH-STAR.md**（~150 行，六节，结构照 spec §5）：
  1. **使命**——三问按 V2.0 口径重述（读 09 v1 §1 原文后重述：单元级脆弱性谱、结构化 vs 随机、首检来源×结局分布——子模型分层为新维度）；
  2. **不可妥协口径（V2.0 版）**——可分析 activated 分母（表5 r12 全文引用）、统计单位、首检四分互斥、Simulator failure 分栏、两条守恒、三轨道不混算、B0 非鲲鹏 920 复刻、AVF/条件占比/检出率/DelayAVF 严禁混算（表1 硬约束）、表7 为执行权威（D4）；
  3. **我们现在在哪**——V1.0 轮遗产：177 格试跑/2624 activated（1583 Masked+1041 Crash+0 SDC+0 Timeout+0 Detected，旧口径）、11 个 LSU 相关注入器（LSQFwd/L1DForward/AddrPath/ArmTLB/PTW/ArmSysReg/ExMon/Cache/Prefetch/Mem）、chaos_lsu_trigger.hh F0–F6 事件归一化、FS 管线（真 B0 平台 DTLB=32 三证 + tlb_probe golden `b6d81b36…` + boot_ckpt v3）、已修工具 bug（采样偏差家族 9 员/超时证据丢弃/runner decode 崩溃）、暂停点 c6e07fa6；
  4. **要去哪**——325 格 × 16 新结果列全回填 + 两条守恒逐格闭合 + 子模型记录覆盖 + 首检×结局矩阵；
  5. **怎么去**——V2-W0..V2-W9 一览表（从 spec §6.2 抄）+ 里程碑 M0'–M6'；
  6. **裁决规则链**——V2.0 xlsx > 转录层 00–08 > 计划层 09-v2；V2.0 内部冲突表7 执行权威（39 格）；机制核实以 vendored gem5 v25.1.0.1 为准。
- [ ] **Step 3: 交叉核对**：文中每个数字与 10/11/spec 对照（无编造）；`grep -c "" NORTH-STAR.md` 行数记录。
- [ ] **Step 4: Commit + push**

```bash
git add docs/gem5-fi/lsu/NORTH-STAR.md
git commit -m "docs(lsu): NORTH-STAR.md — 项目北极星（使命/V2.0口径/现状/目标/V2-W路线/裁决链）"
git pull --rebase origin fi-ding && git push
```

### Task 6: 09-implementation-plan-v2.md 新建 + 旧 09 接替横幅

**Files:**
- Create: `docs/gem5-fi/lsu/09-implementation-plan-v2.md`
- Modify: `docs/gem5-fi/lsu/09-implementation-plan.md`（仅顶部加横幅）

**Interfaces:** Task 7 的 README 文档地图引用；W 表内容以 spec §6.2 为权威底稿。

- [ ] **Step 1: Read** `09-implementation-plan.md` 全文（193 行——V1.0 轮记账与三问、机制核实九项、遗产映射的素材）。
- [ ] **Step 2: 写 09-implementation-plan-v2.md**（现行计划，结构照 spec §6.1）：
  - §0 裁决规则（spec §2 全文收录：权威链 + D1–D5 + 沿用规则三条）；
  - §1 目标与成功判据：三问（V2.0 口径）+ 最终交付物（325 格 × 16 结果列回填 + 守恒逐格闭合 + 元分析报告）+ 不可妥协口径引用 NORTH-STAR §2；
  - §2 机制核实：V1.0 轮九项核实继承声明（从旧 09 §2.1 摘要"已核实（2026-09-25 W1）"）+ 新核实项（表2 保护核验节 7 单元各机制在 vendored gem5 的落点）+ 39 格裁决记录（D4）；
  - §3 WBS：V2-W0..V2-W9 十工作包表——**逐字采用 spec §6.2 的表**（V2-W0 网格与工具重锚 / V2-W1 分类学工具链 / V2-W2 子模型记录 / V2-W3 观测层对齐 / V2-W4 SE 重基线 / V2-W5 FS T 系列 / V2-W6 锚点复验 / V2-W7 screening / V2-W8 main / V2-W9 元分析，各含目标/验收/依赖/遗产映射）；
  - §4 里程碑 M0'–M6'（spec §6.3）；
  - §5 算力预算（spec §6.4：试跑 325×30≈9,750 / screening 325×385≈125,125 / main ≤325×5000≈162.5 万；≤4 并发；超时 10×；≥5 seeds/格；blocked 格数量以 V2-W0 重算为准）；
  - §6 V1.0 遗产映射表（从旧 09 的 W0–W11 完成状态映射到 V2-W，含"已完成不重做"清单）；
  - §7 诚实边界（spec §6.5 七条逐字）；
  - §8 风险登记 R1'–R8'（草拟：R1' A1 重放行序/覆盖特例漂移、R2' 分类学工具工作量超预期、R3' FS T05–T08 实现复杂度、R4' 历史映射有损引发误读、R5' 并行会话 push 冲突、R6' 39 格豁免被误用为漏检、R7' col28 SDC 与 col21 Data Corruption 语义需 W1 裁决、R8' 多核 FS 格长期 blocked）。
- [ ] **Step 3: 旧 09 顶部加横幅**（标题行后，正文零改动）：

```markdown
> **【已被 V2.0 接替（2026-09-29）】** 本文件为 V1.0 轮（68 模型/337 格）实施总纲，已由
> `09-implementation-plan-v2.md` 接替。V1.0 轮遗产记账见新计划 §6。本文件保留供溯源：W0/W1
> 已交付（B0 平台 + 九项机制核实）、W2–W8 注入器已建成、W10 trial（177 格）与 W11 元分析
> 已完成——详见 `10-trial-results.md`（历史轮标注）。
```

- [ ] **Step 4: 验证**：新文件 W 表与 spec §6.2 逐行一致（diff 核对）；旧 09 `git diff` 仅顶部横幅。
- [ ] **Step 5: Commit + push**

```bash
git add docs/gem5-fi/lsu/09-implementation-plan-v2.md docs/gem5-fi/lsu/09-implementation-plan.md
git commit -m "docs(lsu): 09-implementation-plan-v2.md 现行计划（V2-W0..W9/M0'-M6'/遗产映射/风险登记）+ 旧09接替横幅"
git pull --rebase origin fi-ding && git push
```

### Task 7: README 更新 + 全局批判性审计

**Files:**
- Modify: `docs/gem5-fi/lsu/README.md`

**Interfaces:** 消费 Task 1–6 全部产物；最终验收门。

- [ ] **Step 1: Read README.md**，更新：§范围 64/325/43 列；§文档地图加 NORTH-STAR.md 首链、09-v2 现行行 + 09 封存说明、10/11 历史层标注；§数字总账 68/337→64/325、新增 16 结果列/两条守恒/可分析 activated/子模型菜单条目；§溯源与复现源文件条目改 V2.0 xlsx + sha、V1.0 留档说明、两命令验证链不变；§诚实声明补 39 格裁决与历史层关系。
- [ ] **Step 2: 补全 verify V4c**——README 片段断言更新为新内容关键句（Task 3 预留处），`python3 verify_extraction.py` → `ALL PASSED`。
- [ ] **Step 3: 全局 V1.0 残留批判性审计**（在 repo 根执行，结果写进 commit message）：
  1. `grep -rn "68 个设计模型\|68 模型\|337 \|69 逻辑行\|338 \|27 列\|77 格\|r2–r338\|2703f812" docs/gem5-fi/lsu/*.md`——命中只允许出现在：10/11 历史标注块内、旧 09 横幅/正文的 V1.0 记账、README 的 V1.0 留档说明、08/00 的文献性引用；其余命中即残留，修掉；
  2. `ls docs/gem5-fi/lsu/*.md | wc -l` 与文件清单核对（应含 NORTH-STAR.md 与 09-implementation-plan-v2.md）；
  3. 隔离检查 `git status --porcelain`——本交付全程只动 docs/gem5-fi/lsu/** 与本计划/spec 文件；
  4. canonical 不受影响测试：`grep -n "reg_chain" progress.md task_plan.md | head -20` 检索既有命令与 oracle 比对法（golden `f247ef3fe6f02cfd`），运行一次 SE golden，输出一致（CLAUDE.md 回归纪律）；
  5. 双命令终验：`python3 extract.py` → PASSED；`python3 verify_extraction.py` → ALL PASSED。
- [ ] **Step 4: Commit + push**

```bash
git add docs/gem5-fi/lsu/README.md docs/gem5-fi/lsu/verify_extraction.py
git commit -m "docs(lsu): README V2.0 口径 + 全局审计通过（残留grep零命中/隔离/golden一致/双命令PASSED）"
git pull --rebase origin fi-ding && git push
```

---

## 附录 A：V2.0 四表转录底稿（2026-09-29 从 xlsx 直读探测，Task 2 唯一底稿）

### A.1 表0「0.说明与总览」（25 行单列；r2/r6/r16/r20 为空行跳过）

- r1: LSU 单元故障注入方案 — 总览
- r3: 范围：AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器。
- r4: 统一基线：LSU单元参数总表.md 的 B0。除 DTLB=32 项是为复现 TC'23 的显式覆盖外，其余优先采用 gem5 stable 的 O3_ARM_v7a_3 / BaseO3CPU / ArmMMU 配置。
- r5: 重要纠正：B0 是可复现实验模型，不是鲲鹏 920 复刻；cache ports=200 不是物理端口数；当前 ARM 示例为 1 Load FU + 1 Store FU，L1D=32KiB/2-way，StridePrefetcher 位于 L2。
- r7: 工作簿结构
- r8: 1.单元与现有研究：逐单元填写"现有文章"和"现有文章结果"，并严格区分 AVF、非Benign条件占比、检测率和DelayAVF。
- r9: 2.LSU参数基线：参数合理性审查、B0定值与单因素敏感性配置。
- r10: 3.位置×模型矩阵：按"注入位置→故障子模型→注入条件/频率→负载→观测→预期→理由→依据→保护机制"展开，避免在位置和模型之间重复叙述。
- r11: 4.观测点定义：L0-L5传播链；SDC率分母只用activated，不用attempted。
- r12: 5.频率与统计：事件归一化频率、周期换算、随机化与样本量。
- r13: 6.负载清单：论文复现、公开通用和定向探针负载。
- r14: 7.展开执行矩阵：以运行级独立样本记录；保留模型ID、频率档、负载、seed、eligible/activated、首次检测、最终结局、保护机制证据，并显式记录故障表现形式/子模型。
- r15: 8.文献与来源：本地论文和官方源码定位。
- r17: 统计与判定边界
- r18: ① attempted、eligible、activated分开记录。目标未被后续读取/使用的注入归入Injected-not-activated，不进入结果率分母。
- r19: ② F0单次故障用于AVF/论文对照；F1-F4是重复/突发故障压力实验，不能与F0混成一个"故障率"。F5永久故障按运行分类。
- r20: ③ 每个实验单元先做30个activated样本试跑；正式筛查至少385个activated样本（95%置信水平、最坏比例下约±5个百分点）。论文主结果建议用Wilson 95%区间半宽≤2个百分点或达到5000个activated样本停止。
- r21: ④ 每个故障运行绑定同一checkpoint、输入、seed和无故障golden run；结构化换值只允许替换成明确合法值，并保存源值/目标值。
- r22: ⑤ 预期结果是可证伪假设，不是实测结论。没有论文直接结果的AGU、原子/同步和多数结构化模型，实测列必须保持待执行。
- r23: ⑥ 检测情况与最终结局分开记录：首检层级为Hardware RAS / OS / Application / None，并另记Hardware RAS是否在任意时点检出。SDC只指三层运行时检测都沉默、程序表面正常完成，但离线oracle发现Data Corruption。全程无硬件RAS但最终Crash/Timeout分别记为RAS-silent Crash/Timeout；gem5 panic/assert或实验基础设施故障单列Simulator failure，不算架构级Crash或SDC
- r24: 完善版增量
- r25: 补充PPN与SQ基础对照、Load Queue、MSHR资源记账、原子操作数、预取触发脏驱逐、真实应用负载，以及F1-F4按运行聚类的统计规则；原58条模型扩展为64条。

### A.2 表2「2.LSU参数基线」新节（r21–r29；r2–r19 参数区 = V1.0 减 ECC 行，r20 空行）

r21（合并区 A21:E21）: 逐单元保护机制核验（只列实际存在且纳入实现的机制）
r22 列头: 结构/单元 | 实际存在的机制 | 在本方案中的处理 | 实现/观测口径 | 边界说明
- r23 AGU: 地址生成后进入翻译、对齐与访问权限检查 | 归入架构异常或功能性阻断，不直接计Hardware RAS | 对照EA、PA、size、mask、异常原因与提交结果 | EA oracle只用于实验观测，不是硬件保护机制
- r24 L1d-TLB: TLB命中、页表遍历、权限/属性与页故障路径 | 命中错误或映射错误按传播结果分类 | 记录VPN/ASID、PPN、权限、命中way、walk/fill与fault | 未核实B0配置ECC/parity，不把正常翻译检查写成RAS
- r25 Load Queue: 地址冲突检测、violation与replay、提交约束 | replay视为功能性恢复；断言失败单列Simulator failure | 记录LQ entry、依赖、violation、replay目标、返回ID与提交 | 软件oracle和离线一致性检查不计硬件首检
- r26 Store Queue: 转发、顺序、提交、请求/应答生命周期约束 | 成功重放/阻断可归Contained，但需有明确证据 | 记录SQ entry、地址、数据、mask、forwarding、request/ack与commit | 未核实专用ECC/parity；普通状态机检查不自动等同RAS
- r27 L1d-Cache: tag/data/state、一致性、fill、eviction与writeback流程 | 以真实告警或异常证据决定Hardware RAS；否则按结局分类 | 记录set/way、tag、data、MESI、dirty、MSHR、fill/writeback和snoop | B0未配置ECC/parity；一致性协议属于功能机制
- r28 原子与同步: exclusive monitor、CAS/LL-SC返回、barrier与内存顺序 | 按原子结果、顺序和可见性是否被破坏分类 | 记录monitor、比较值、old/new value、success状态、order tag与barrier完成 | litmus oracle用于判定，不是硬件RAS
- r29 数据预取器: 地址过滤、队列、取消/节流及与需求请求的区分 | 普通预取失误通常应被屏蔽；污染所有权/dirty时重点追踪 | 记录prefetch地址、来源PC、stride、队列、请求标签、allocate/ownership | B0未配置ECC/parity；性能退化与架构错误分开统计

（参数区 r18=数据预取器 L2 StridePrefetcher degree=8, latency=1, prefetch_on_access=True｜修正｜官方ARM O3示例挂L2；原L1D degree=4不准确｜B0；S4挂L1D；r19=时钟 2.6GHz仅用于换算｜澄清｜注入频率以eligible event为主，避免工作负载IPC偏差｜B0）

### A.3 表4「4.观测点定义」（7×6 整表重写；列：层级|含义|LSU必须记录的字段/状态|建议实现点|判定用途|注意事项）

- L0 注入/激活 | 确认是否尝试注入、是否满足资格、是否真正命中并被消费 | attempted、eligible、activated、结构entry/way、bit/字段、原值/故障值、注入时刻、寿命区间、指令/事务ID、commit序号 | 故障注入器入口与目标字段读取点 | 未activated的运行不得进入错误率分母 | 单次瞬态只在一个随机合法事件生效；重复注入逐次重新抽取目标
- L1 单元内部 | 检查局部状态守恒与结构不变量 | AGU的EA/size/mask；TLB映射；LQ/SQ有效项与转发；cache tag-data-state；MSHR/free计数；monitor；prefetch queue | 各结构更新、仲裁、读写与状态迁移处 | 区分局部屏蔽、内部异常和向下游传播 | 断言/仿真器异常单列Simulator failure，不直接并入架构检测
- L2 请求形成/顺序 | 观察LSU生成的访存请求及乱序恢复是否正确 | PA、size、byte mask、request/response ID、issued/dropped/duplicate、violation、replay、依赖和顺序标签 | 请求发射、响应匹配、replay与commit前检查处 | 识别错地址、错大小、重复/丢失及错误replay | 同一事务链用统一ID贯穿，避免只按周期关联
- L3 Cache/一致性/内存 | 追踪错误是否进入缓存层次或内存 | hit/miss、set/way、fill、eviction、writeback、snoop、ownership、dirty、DRAM写入 | L1d接口、一致性消息与内存写入点 | 判定是否被cache命中/替换屏蔽或形成持久污染 | 预取错误要区分纯性能影响与需求数据/所有权污染
- L4 架构可见/软件 | 定位首次架构状态分歧及其软件后果 | commit PC/opcode、寄存器与内存副作用、首次错误load/store、异常/信号、应用校验 | 提交端、异常入口和应用oracle | 区分Data Corruption、Crash、Timeout与正确完成 | 首次错误提交与最终应用结局都要记录
- L5 检测与最终结局 | 把首检来源和最终结局分开记录 | Hardware RAS/OS/Application/None首检；Hardware RAS任意时点；Masked、Detected-contained、Detected-uncontained、Data Corruption、RAS-silent Crash/Timeout、Simulator failure | 统一后处理脚本和运行日志汇总 | 支持互斥首检、任意时点硬件检测率和结局守恒校验 | 首检来源互斥；Simulator failure与体系结构结局分栏

### A.4 表5「5.频率与统计」（20×6；频率区 r2–r8 新增 col6 统计单位；统计区 r11–r20 九行）

频率表（col6 统计单位）：F0=run-level独立样本；F1/F2/F3/F4=run-level cluster；事件级仅作传播记录；F5=run-level独立样本；F6=run-level独立样本。（col1–5 与 V1.0 相同：F0 单次瞬态…F6 确定性事件触发，定义文本未变）

统计规则（r11 列头：统计项|规则/公式|筛查目标|主结果目标|原因|备注）：
- r12 分母与二维分类 | 激活率=activated/attempted；可分析activated=activated-Simulator failure；SDC率=SDC/可分析activated；硬件检测率=Hardware RAS任意时点检出/可分析activated | 必须报告激活、结局、首检层级和硬件RAS任意时点检出 | 同左 | 区分真正SDC、RAS-silent Crash/Timeout和Detected-uncontained；模拟器失败单列，避免污染架构结果 | 首检四类互斥；Hardware RAS任意时点检出可与OS/Application首检交叉
- r13 试跑 | 每单元×模型×频率×负载先取得30个activated | 30 | 30 | 发现注入器错误、全Crash或零激活单元 | 不用于最终窄置信区间
- r14 筛查样本量 | 最坏p=0.5，95%正态近似，半宽5pp约385个activated | ≥385 | — | 用于淘汰纯性能/全Crash组合 | 正式报告使用Wilson区间
- r15 主结果停止 | 顺序增加样本，Wilson 95%区间半宽≤2pp或activated达到5000 | — | ≤2pp或5000 | 在可控成本下统一精度 | 报告实际区间，不只报点估计
- r16 随机化 | seed、bit、entry、eligible event分层随机；合法换值保存source/target | 固定seed清单 | 每cell独立≥5个seed批次 | 避免单一程序相位和地址段主导 | 跨模型比较用common random numbers
- r17 超时 | golden wall/sim time或committed inst的10×，并设置绝对上限 | 统一 | 统一 | 区分慢化与无限循环 | F5可单独提高上限但须预注册
- r18 2.6GHz换算 | 1ms=2,600,000 cycles；100us=260,000；10us=26,000 | 仅辅助 | 仅辅助 | 主频变化不会改变事件归一化档位 | 不要用cycle频率替代eligible event分母
- r19 独立样本单位 | F0/F5/F6通常以一次运行为独立样本；F1-F4同一运行内多个activated事件属于同一cluster | 按运行保存cluster ID | 按运行聚类计算区间 | 避免共享程序状态和前序故障导致伪独立 | 不得把同一运行内事件直接当独立Bernoulli样本
- r20 重复注入归因 | F1-F4最终结局归因于整次运行的故障序列；事件级传播另行记录 | 记录事件序列 | 报告run-level SDC/Crash与cluster bootstrap区间 | 多个故障可能共同导致最终错误 | F0单故障结果与压力档结果分开

## 附录 B：表3/表7 机器事实卡（Task 1 断言依据，2026-09-29 直读探测）

**表3**：65 行（r1 表头 + r2–r65 共 64 模型）；14 列（col6 故障表现形式/子模型、col14 保护机制归属为新列；col7=适用频率、col8=适用负载、col9=事件触发条件、col10=传播链重点观测、col11=预期结果、col12=设计理由、col13=文献依据/直接性）；**追加 10 模型（T10/S13/L01–L04/C14/C15/O09/P09）不再位于表尾**——最后 10 行是 O09,P01–P09（行序按单元重排）；删除 T09/S12/C13/O08。

**表7**：326 行（r1 表头 + 325 数据行）；43 列。关键事实：
- col20 头=Detected-contained、col21 头=Data Corruption（原位改名）；col24 头=SDC率(可分析activated)。
- 数据行填充色：col1–15 无；col16–23/27/28–37/41/42 **无数据格**；col24=蓝×6、col25=蓝×6、col38=蓝×5、col39=蓝×5、col40=蓝×5（全部在模板行）；col26=黄 `FFFFF2CC`×65 + 蓝 `FFDDEBF7`×260；col43=浅蓝 `FFD9E2F3`×325。
- 公式仅存 6 模板行 r2/66/130/194/258/322，共 27 格（col24 `IF(OR(R2="",R2-AP2<=0),"",AB2/(R2-AP2))`、col25 `IF(OR(Q2="",Q2=0),"",R2/Q2)`、col38 `IF(OR(R2="",R2-AP2<=0),"",AO2/(R2-AP2))`、col39 `IF(R2="","",SUM(AC2:AF2)-(R2-AP2))`、col40 `IF(R2="","",SUM(S2:W2)+AP2-R2)`）。
- col26 黄格集合 = APPENDED_IDS 运行 − T10 全部 − S13-F0（77−12=65）。
- F6 覆盖仍存：13 行（L02/L03/L04/C15/P09 × F6），col8=「首次出现指定事件时注入一次；仍以故障值被下游消费作为 activated 判据」（F6_OVERRIDE_TEXT 不变）。
- W11 覆盖仍存：12 行，col10=负载名（如「SPEC CPU2017 采样区间」）+ '\n执行定义与 oracle：' + W11_ORACLE（不变）。
- col43 预填 = 该模型表3 col6 菜单原样复制（64 distinct 值）。
- AGU 系 8 模型（A01–A08）共 39 运行的 col12=「L5检测层级、控制情况与最终结局」新措辞，与表3 col10 旧文不同（D4 豁免源）。

**表1/表6/表8**：值零变化（表1 仅 7 格共享串存储类型变化）→ 01/06/08 md 逐字节不变。

**表2**：29 行 = r1 表头 + r2–r19 参数区（18 参数，ECC 行已删）+ r20 空 + r21 合并标题 + r22 列头 + r23–r29 七单元（内容见附录 A.2）。

**表0**：25 行，22 非空格；r23 新增⑥；r25 已改"原58条模型扩展为64条"（V2.0 自洽）。
