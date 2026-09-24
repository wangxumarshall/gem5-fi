# LSU 单元故障注入方案 V1.0 → 项目北极星提取 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把《gem5-fi-LSU单元故障注入方案V1.0.xlsx》（9 工作表）忠实提取为 `docs/gem5-fi/lsu/` 完整项目北极星（忠实层 + 09 实施总纲），全部提取正确性由机器断言背书。

**Architecture:** 镜像适配 `docs/gem5-fi/ooo/` 先例——文档编号 1:1 对应源表号 0–8；`extract.py`（纯标准库解析 xlsx）生成 4 个机械产物并内置六项交叉校验；`verify_extraction.py` 独立重解析做逐格回比；手写文档逐表转录并用片段检查兜底。

**Tech Stack:** Python 3.11 纯标准库（zipfile + xml.etree + csv + hashlib；本机 pip 403，openpyxl 不可用）。无 C++、无仿真。

**Spec:** `docs/superpowers/specs/2026-09-24-lsu-north-star-extraction-design.md`（commit 4fe4b7dd）。本计划与 spec 冲突时以 spec 为准，除提交顺序：spec §10 表格自注"writing-plans 阶段定稿"，本计划把 verify_extraction.py 前移到文档任务之前（TDD：先有校验器，文档写完即受检），共 7 个 commit。

## Global Constraints（每个任务隐含遵守）

- 分支 `fi-ding`；**绝不 `git add -A`**，只 add 任务列出的显式路径；commit message **不得**以 `Co-Authored-By: Claude` 结尾；每次 commit 后 `git push origin fi-ding`，若被拒先 `git pull --rebase --autostash origin fi-ding`（多会话并发推同分支，远端可能领先）。
- 源文件 sha256 必须恒等于 `2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651`；任何脚本运行前先校验。
- 本机无 openpyxl：解析一律用标准库 zipfile + ElementTree。
- 提取忠实原则：源表文本**逐字转录**，不截断、不改写、不"顺手修正"；提取者观点只出现在明确标注处（README 固定小节、07-md 的"源表特例"节）。
- 工作目录：所有命令在仓库根 `/home/sdc/gem5-fi-lsu` 执行（脚本内部路径相对脚本自身解析）。
- 纯文档/脚本工作：每任务"回归检查"= **不适用**（不改在产代码），在 commit message 或任务记录里明确声明，不假装跑过。

## 已实证的提取规则（2026-09-24 用一次性脚本对源表 100% 验证；extract.py 直接固化，禁止重新发明）

- **R1 展开规则**：每个设计模型 → `适用频率`按`/`切分 × `适用负载`按`\n`切分，**全叉积**；行序 = 模型（设计矩阵源序）→ 频率（格内顺序）→ 负载（格内顺序）。68/68 模型吻合（如 A01: F0/F1/F2 × {W3,W9} = 6 格）。
- **R2 verbatim 拷贝列**：展开表 col4/5/6/11/12/13/14/15 == 设计矩阵 col3/4/5/8/9/10/11/12，337/337 逐格全等；col2(模型ID)/col3(单元) 同源。
- **R3 col8 频率定义**：= 表5[F档].定义，**例外 13 行**（F6 且 模型ID ∈ {L02,L03,L04,C15,P09}）→ `首次出现指定事件时注入一次；仍以故障值被下游消费作为 activated 判据`。
- **R4 col9 负载**：= 设计矩阵`适用负载`按`\n`切出的对应条目；每条 **startswith** 表6 的某个`名称`（唯一匹配，337/337）。
- **R5 col10**：= `col9 + '\n执行定义与 oracle：' + 表6[W].定义`，**例外 = 全部 12 行 W11** → oracle 文本为 `mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/checkpoint；使用参考输出或结果哈希`（325+12=337）。
- **R6 RunID**：= `{模型ID}-{频率}-{W编号}`，337/337 与列值一致。
- **R7 结果槽**：col16–25、col27 全空（337/337）；col26 `记录状态` = `待执行`（337/337）。
- **R8 颜色**：黄 `FFFFF2CC` = col16–23 + col27；蓝 `FFDDEBF7` = col24–25；**col26 = 完善版 10 模型的 77 格黄 / 其余 260 格蓝（已验证集合相等）**；col1–15 无填充。
- **R9 完善版**：设计矩阵 Excel r60–r69 = `T10,S13,L01,L02,L03,L04,C14,C15,O09,P09`（58+10=68）。
- **R10 解析**：workbook rels 的 Target 带 leading slash（`/xl/worksheets/sheet1.xml`），归一化必须先 `.lstrip('/')`；无 mergeCells、无 inlineStr；字符串走 sharedStrings。
- **R11 表5 结构**：r1 表头 + r2–r8 七档（col1=档位, col3=定义）+ r11 子表头 + r12–r20 九条统计规则（r9/r10 空行）。
- 分布数字（写进 07-md/README）：频率 F0=109/F1=24/F2=77/F3=4/F4=26/F5=29/F6=68；单元 AGU=39/L1d-TLB=42/SQ=66/Cache=76/原子=31/预取=53/LQ=30；负载 W0=6,W1=27,W2=6,W3=24,W4=27,W5=57,W6=58,W7=32,W8=25,W9=15,W10=27,W11=12,W12=15,W13=6。

## File Structure（全部交付物）

```
docs/gem5-fi/lsu/
├── README.md                        [Task 6]  总纲导航
├── 00-overview.md                   [Task 4]  ← 表0
├── 01-units-and-research.md         [Task 4]  ← 表1（7单元×7列）
├── 02-parameter-baseline.md         [Task 4]  ← 表2（19参数×5列）
├── 03-design-matrix.md              [Task 2]  ← 表3（extract.py 生成）
├── design-matrix.csv                [Task 2]
├── 04-observation-points.md         [Task 5]  ← 表4（L0–L5）
├── 05-frequency-and-sampling.md     [Task 5]  ← 表5（F0–F6 + 统计规则）
├── 06-workloads.md                  [Task 5]  ← 表6（W0–W13）
├── 07-expanded-matrix.csv           [Task 2]  ← 表7（extract.py 生成）
├── 07-expanded-matrix.md            [Task 2]
├── 08-references.md                 [Task 5]  ← 表8（11条）
├── 09-implementation-plan.md        [Task 7]  实施层（手写）
├── extract.py                       [Task 2]
├── verify_extraction.py             [Task 3 起，任务4/5/6递增扩展]
└── gem5-fi-LSU单元故障注入方案V1.0.xlsx   [Task 1]
```

---

### Task 1: 源 xlsx 入库

**Files:**
- Add: `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V1.0.xlsx`（已存在于工作区，未跟踪）

**Interfaces:**
- Produces: 仓库内源文件，后续所有任务的唯一数据源；sha256 见 Global Constraints。

- [x] **Step 1: 校验 sha256 与 spec 一致**

Run: `sha256sum docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V1.0.xlsx`
Expected: `2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651  docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V1.0.xlsx`

- [x] **Step 2: 提交并推送**

```bash
git add docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V1.0.xlsx
git commit -m "docs(lsu): track source xlsx V1.0 (sha256 2703f812)"
git push origin fi-ding
```

- [x] **Step 3: 验证入库**

Run: `git show --stat HEAD | tail -3`
Expected: 显示该 xlsx 1 file changed。

---

### Task 2: extract.py 生成器 + 4 个机械产物

**Files:**
- Create: `docs/gem5-fi/lsu/extract.py`
- Create（由 extract.py 生成并入库）: `docs/gem5-fi/lsu/03-design-matrix.md`、`docs/gem5-fi/lsu/design-matrix.csv`、`docs/gem5-fi/lsu/07-expanded-matrix.csv`、`docs/gem5-fi/lsu/07-expanded-matrix.md`

**Interfaces:**
- Consumes: 源 xlsx（Task 1）。
- Produces: 上列 4 产物 + 六项断言（A1–A6，见脚本）；`design-matrix.csv` 表头 `['Excel行'] + 12 源列名`、68 数据行；`07-expanded-matrix.csv` 表头 `['Excel行'] + 27 源列名`、337 数据行；运行成功时 stdout 末行 `EXTRACTION VERIFICATION PASSED`。Task 3 的校验器逐格消费这两份 CSV。

- [x] **Step 1: 写入 extract.py 全文**

创建 `docs/gem5-fi/lsu/extract.py`，内容如下（完整、可直接运行）：

```python
#!/usr/bin/env python3
"""docs/gem5-fi/lsu/ 的忠实层生成器 + 提取正确性交叉校验。

从《gem5-fi-LSU单元故障注入方案V1.0.xlsx》生成：
  03-design-matrix.md      工作表「3.位置x模型矩阵」68 设计行（按 7 单元分节，12 列全列 + Excel 行号）
  design-matrix.csv        同上机读版（Excel行 + 12 列）
  07-expanded-matrix.csv   工作表「7.展开执行矩阵」337 实验格（Excel行 + 27 列，11 结果槽原样为空）
  07-expanded-matrix.md    展开矩阵列文档 + 分布汇总 + 颜色语义 + 源表特例

交叉校验（提取正确性不靠"看起来对"；任一失败即非零退出）：
  A1 展开重放：设计矩阵 适用频率 × 适用负载 全叉积 → 与表7 337 行 col1–15 逐格全等
  A2 行数 68 / 337
  A3 结果槽 col16–25、col27 全空；col26 == '待执行'
  A4 RunID == 模型ID-频率-W编号，且 W编号 ↔ 表6 名称唯一前缀匹配
  A5 模型ID 唯一；(单元, 注入位置, 故障类型) 唯一
  A6 颜色：col16–23+27 黄(FFFFF2CC)；col24–25 蓝(FFDDEBF7)；col26 黄集合 == 完善版77格

纯标准库（本机 pip 403，openpyxl 不可用；xlsx = zip + spreadsheetml XML）。
用法：python3 extract.py（任意目录，路径相对本脚本解析）
"""
import csv
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, OrderedDict
from pathlib import Path

NS_MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NS_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

HERE = Path(__file__).resolve().parent
XLSX = HERE / 'gem5-fi-LSU单元故障注入方案V1.0.xlsx'
EXPECT_SHA256 = '2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651'

SHEET3_COLS = ['模型ID', '单元', '注入位置（结构与正常作用）', '故障类型',
               '故障模型（实施步骤与激活口径）', '适用频率', '适用负载（真实名称）',
               '事件触发条件', '传播链重点观测', '预期结果（待验证假设）',
               '设计理由', '文献依据/直接性']
SHEET7_COLS = ['RunID', '模型ID', '单元', '注入位置（结构与正常作用）', '故障类型',
               '故障模型（实施步骤与激活口径）', '频率', '频率定义', '负载（真实名称）',
               '负载定义/oracle', '触发条件', '传播监控', '预期结果', '设计理由', '文献依据',
               'Seed/注入索引', 'Attempted', 'Activated', 'Masked', 'Detected/Contained',
               'SDC', 'Crash', 'Timeout', 'SDC率(activated)', '激活率', '记录状态', '实测备注']
UNIT_ORDER = ['AGU', 'L1d-TLB', 'Store Queue', 'L1d-Cache', '原子与同步', '数据预取器', 'Load Queue']
APPENDED_IDS = ['T10', 'S13', 'L01', 'L02', 'L03', 'L04', 'C14', 'C15', 'O09', 'P09']  # 完善版 r60-r69
F6_OVERRIDE_MODELS = {'L02', 'L03', 'L04', 'C15', 'P09'}
F6_OVERRIDE_TEXT = '首次出现指定事件时注入一次；仍以故障值被下游消费作为 activated 判据'
W11_ORACLE = 'mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/checkpoint；使用参考输出或结果哈希'
YELLOW, BLUE = 'FFFFF2CC', 'FFDDEBF7'

SST = []  # sharedStrings 表（main() 里初始化）


def die(msg):
    print(f'EXTRACTION VERIFICATION FAILED: {msg}', file=sys.stderr)
    sys.exit(1)


def col_to_num(col):
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def read_grid(zf, relmap, name_substr):
    """返回 (OrderedDict[excel_row -> {colnum -> text}], sheet_root)。按表序找名字含子串的表。"""
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    for sh in wb.iter(f'{NS_MAIN}sheet'):
        if name_substr in (sh.get('name') or ''):
            t = relmap[sh.get(f'{NS_REL}id')].lstrip('/')  # 本 xlsx 的 Target 带 leading slash
            target = t if t.startswith('xl/') else 'xl/' + t
            root = ET.fromstring(zf.read(target))
            grid = OrderedDict()
            for row in root.iter(f'{NS_MAIN}row'):
                cells = {}
                for c in row.iter(f'{NS_MAIN}c'):
                    m = re.match(r'([A-Z]+)(\d+)', c.get('r') or '')
                    coln = col_to_num(m.group(1)) if m else len(cells) + 1
                    v = c.find(f'{NS_MAIN}v')
                    txt = v.text if v is not None else ''
                    if c.get('t') == 's' and txt != '':
                        txt = SST[int(txt)]
                    cells[coln] = txt or ''
                if cells:
                    grid[int(row.get('r'))] = cells
            return grid, root
    die(f'sheet {name_substr!r} not found')


def md_cell(s):
    return s.replace('|', '\\|').replace('\n', '<br>')


def main():
    raw = XLSX.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECT_SHA256:
        die(f'sha256 mismatch: {sha}')
    zf = zipfile.ZipFile(XLSX)
    global SST
    if 'xl/sharedStrings.xml' in zf.namelist():
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS_MAIN}si'):
            SST.append(''.join(t.text or '' for t in si.iter(f'{NS_MAIN}t')))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}

    dm, _ = read_grid(zf, relmap, '3.位置x模型矩阵')
    fs, _ = read_grid(zf, relmap, '5.频率与统计')
    wl, _ = read_grid(zf, relmap, '6.负载清单')
    ex, ex_root = read_grid(zf, relmap, '7.展开执行矩阵')

    # ---- 设计矩阵 68 行 ----
    design = OrderedDict()  # mid -> (excel_row, {colnum->text})
    seen_keys = set()
    for r in sorted(dm)[1:]:
        g = dm[r]
        mid = g.get(1, '')
        if not mid:
            continue
        if mid in design:
            die(f'A5: 模型ID 重复 {mid}')
        key = (g.get(2, ''), g.get(3, ''), g.get(4, ''))
        if key in seen_keys:
            die(f'A5: (单元,注入位置,故障类型) 重复 {key}')
        seen_keys.add(key)
        design[mid] = (r, g)
    if len(design) != 68:
        die(f'A2: 设计矩阵应为 68 行, 实得 {len(design)}')
    appended_actual = [mid for mid, (r, _) in design.items() if r >= 60]
    if appended_actual != APPENDED_IDS:
        die(f'R9: 完善版追加行应为 {APPENDED_IDS}, 实得 {appended_actual}')

    # ---- 表5 档位定义 / 表6 负载 ----
    freq_def = {fs[r][1]: fs[r][3] for r in fs
                if fs[r].get(1, '').startswith('F') and fs[r].get(2, '')}
    if sorted(freq_def) != [f'F{i}' for i in range(7)]:
        die(f'表5 档位不全: {sorted(freq_def)}')
    wname, wdef = {}, {}
    for r in sorted(wl):
        g = wl[r]
        if g.get(1, '').startswith('W') and g.get(2, ''):
            wname[g[2]] = g[1]
            wdef[g[1]] = g[4]
    if len(wdef) != 14:
        die(f'表6 应为 14 个负载, 实得 {len(wdef)}')

    # ---- A1: 展开重放（R1–R6 全部规则在此固化）----
    rebuilt = []
    for mid, (erow, g) in design.items():
        freqs = [t.strip() for t in g.get(6, '').split('/') if t.strip()]
        entries = [e for e in g.get(7, '').split('\n') if e.strip()]
        for e in entries:  # A4: 唯一前缀匹配
            if sum(1 for nm in wname if e.startswith(nm)) != 1:
                die(f'A4: 负载条目前缀匹配数 != 1: {mid} {e[:30]!r}')
        for f in freqs:
            for e in entries:
                wid = next(wname[nm] for nm in wname if e.startswith(nm))
                col8 = F6_OVERRIDE_TEXT if (f == 'F6' and mid in F6_OVERRIDE_MODELS) else freq_def[f]
                col10 = e + '\n执行定义与 oracle：' + (W11_ORACLE if wid == 'W11' else wdef[wid])
                rebuilt.append([f'{mid}-{f}-{wid}', mid, g.get(2, ''), g.get(3, ''),
                                g.get(4, ''), g.get(5, ''), f, col8, e, col10,
                                g.get(8, ''), g.get(9, ''), g.get(10, ''), g.get(11, ''),
                                g.get(12, '')] + [''] * 10 + ['待执行', ''])
    actual_rows = [ex[r] for r in sorted(ex)[1:]]
    if len(actual_rows) != 337 or len(rebuilt) != 337:
        die(f'A2: 展开矩阵应为 337 行, 重放 {len(rebuilt)}, 源表 {len(actual_rows)}')
    for i, (reb, act) in enumerate(zip(rebuilt, actual_rows)):
        for c in range(27):
            if reb[c] != act.get(c + 1, ''):
                die(f'A1: 第 {i + 1} 行列 {c + 1} 不等: 重放 {reb[c][:40]!r} vs 源 {act.get(c + 1, "")[:40]!r}')
    # ---- A3: 结果槽 ----
    for i, act in enumerate(actual_rows):
        if any(act.get(c, '') != '' for c in list(range(16, 26)) + [27]):
            die(f'A3: 第 {i + 1} 行结果槽非空')
        if act.get(26, '') != '待执行':
            die(f'A3: 第 {i + 1} 行记录状态 != 待执行')

    # ---- A6: 颜色 ----
    styles = ET.fromstring(zf.read('xl/styles.xml'))
    fills = []
    for f in styles.iter(f'{NS_MAIN}fill'):
        pf = f.find(f'{NS_MAIN}patternFill')
        rgb = ''
        if pf is not None:
            fg = pf.find(f'{NS_MAIN}fgColor')
            if fg is not None:
                rgb = fg.get('rgb') or ''
        fills.append(rgb)
    xfs = [xf.get('fillId') for xf in styles.find(f'{NS_MAIN}cellXfs')]
    col_fill = {}   # 列字母 -> Counter(颜色)
    cell_fill = {}  # (列字母, 行号) -> 颜色
    for c in ex_root.iter(f'{NS_MAIN}c'):
        m = re.match(r'([A-Z]+)(\d+)', c.get('r') or '')
        if not m or int(m.group(2)) < 2:
            continue
        rgb = fills[int(xfs[int(c.get('s'))])] if c.get('s') is not None else ''
        col_fill.setdefault(m.group(1), Counter())[rgb] += 1
        cell_fill[(m.group(1), int(m.group(2)))] = rgb
    for L in 'ABCDEFGHIJKLMNO':
        if set(col_fill.get(L, Counter())) - {''}:
            die(f'A6: col1-15 出现填充 {L}: {dict(col_fill[L])}')
    for L in 'PQRSTUVW':  # col16-23
        if set(col_fill.get(L, Counter())) != {YELLOW}:
            die(f'A6: col16-23 应全黄: {L} {dict(col_fill.get(L, {}))}')
    for L in 'XY':  # col24-25
        if set(col_fill.get(L, Counter())) != {BLUE}:
            die(f'A6: col24-25 应全蓝: {L} {dict(col_fill.get(L, {}))}')
    if set(col_fill.get('AA', Counter())) != {YELLOW}:
        die(f'A6: col27 应全黄: {dict(col_fill.get("AA", {}))}')
    yellow26 = {ex[r][1] for r in sorted(ex)[1:] if cell_fill.get(('Z', r)) == YELLOW}
    want26 = {ex[r][1] for r in sorted(ex)[1:] if ex[r][2] in APPENDED_IDS}
    if yellow26 != want26:
        die(f'A6: col26 黄色集合 != 完善版77格 (差 {len(yellow26 ^ want26)} 个)')

    # ---- 生成 design-matrix.csv / 03-design-matrix.md ----
    with open(HERE / 'design-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Excel行'] + SHEET3_COLS)
        for mid, (r, g) in design.items():
            w.writerow([r] + [g.get(c, '') for c in range(1, 13)])
    lines = ['# 03 · 位置×模型矩阵（设计主体）', '',
             '> 源：工作表「3.位置x模型矩阵」（Excel r2–r69，68 个设计模型，12 列全列）。',
             '> 提取注记列中「完善版新增」= 源表 r60–r69 追加的 10 行（源表总览自述"原58条模型扩展"）。',
             '> 机读版：`design-matrix.csv`。引用编号 = 源表自带模型ID（A/T/S/C/O/P/L 前缀 = 单元）。', '']
    for unit in UNIT_ORDER:
        rows = [(mid, r, g) for mid, (r, g) in design.items() if g.get(2, '') == unit]
        if not rows:
            continue
        lines += [f'## {unit}（{len(rows)} 个模型）', '',
                  '| ' + ' | '.join(['Excel行'] + SHEET3_COLS + ['提取注记']) + ' |',
                  '|' + '---|' * (len(SHEET3_COLS) + 2)]
        for mid, r, g in rows:
            note = '完善版新增' if mid in APPENDED_IDS else ''
            cells = [str(r)] + [md_cell(g.get(c, '')) for c in range(1, 13)] + [note]
            lines.append('| ' + ' | '.join(cells) + ' |')
        lines.append('')
    (HERE / '03-design-matrix.md').write_text('\n'.join(lines), encoding='utf-8')

    # ---- 生成 07-expanded-matrix.csv / 07-expanded-matrix.md ----
    with open(HERE / '07-expanded-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Excel行'] + SHEET7_COLS)
        for r in sorted(ex)[1:]:
            w.writerow([r] + [ex[r].get(c, '') for c in range(1, 28)])
    freq_c = Counter(a.get(7, '') for a in actual_rows)
    unit_c = Counter(a.get(3, '') for a in actual_rows)
    wl_c = Counter(a.get(1, '').rsplit('-', 1)[1] for a in actual_rows)
    md = ['# 07 · 展开执行矩阵 — 列文档、分布与源表特例', '',
          '> 源：工作表「7.展开执行矩阵」（Excel r2–r338，337 实验格 × 27 列）。逐格数据在 `07-expanded-matrix.csv`。',
          '> RunID = `{模型ID}-{频率}-{W负载}`。展开规则 = 设计矩阵「适用频率 × 适用负载」全叉积（extract.py A1 重放验证）。',
          '', '## 列语义与颜色（源表总览 r14：黄色=执行后人工录入，蓝色=自动计算）', '',
          '| 列 | 名称 | 语义 | 填充色 |', '|---|---|---|---|']
    semantics = [
        (list(range(1, 16)), '源数据列（RunID/模型/位置/故障模型/频率/负载/触发/传播/预期/理由/文献）', '由设计矩阵与表5/表6 派生', '无'),
        (list(range(16, 24)), 'Seed/注入索引、Attempted、Activated、Masked、Detected/Contained、SDC、Crash、Timeout', '执行后人工录入槽（现为空）', f'黄 {YELLOW}'),
        ([24, 25], 'SDC率(activated)、激活率', '自动计算（SDC/activated、activated/attempted）', f'蓝 {BLUE}'),
        ([26], '记录状态', '全表预填「待执行」；完善版 10 模型的 77 格黄、原 58 模型 260 格蓝（源表用颜色区分新增行）', '黄/蓝混合'),
        ([27], '实测备注', '执行后人工录入槽（现为空）', f'黄 {YELLOW}'),
    ]
    for cols, names, meaning, color in semantics:
        md.append(f'| {",".join(map(str, cols))} | {names} | {meaning} | {color} |')
    md += ['', '## 分布汇总（337 格）', '',
           '| 维度 | 分布 |', '|---|---|',
           f'| 频率 | {" · ".join(f"{k}={v}" for k, v in sorted(freq_c.items()))} |',
           f'| 单元 | {" · ".join(f"{k}={v}" for k, v in sorted(unit_c.items()))} |',
           f'| 负载 | {" · ".join(f"{k}={v}" for k, v in sorted(wl_c.items()))} |',
           f'| 完善版 | 10 模型共 77 格（原 58 模型 260 格） |',
           '', '## 源表特例（提取时如实保留，非提取偏差）', '',
           f'1. **13 行 F6 频率定义覆盖**：{", ".join(sorted(F6_OVERRIDE_MODELS))} 的 F6 行，col8 =「{F6_OVERRIDE_TEXT}」（表5 标准 F6 定义的 activated 判据强化版）。',
           f'2. **12 行 W11 oracle 覆盖**：全部 W11（SPEC CPU2017）行，col10 的 oracle 段 =「{W11_ORACLE}」（比表6 W11 定义更完整的执行版文本）。',
           '3. **结果槽**：col16–25、col27 在源表中全空、col26 全为「待执行」——是实施时的填写槽，CSV 原样保留。', '']
    (HERE / '07-expanded-matrix.md').write_text('\n'.join(md), encoding='utf-8')

    print(f'source sha256: {sha}')
    print(f'design models: {len(design)} (完善版追加 {len(APPENDED_IDS)}), expanded runs: {len(actual_rows)}')
    print('EXTRACTION VERIFICATION PASSED')


if __name__ == '__main__':
    main()
```

- [x] **Step 2: 语法检查**

Run: `python3 -m py_compile docs/gem5-fi/lsu/extract.py && echo OK`
Expected: `OK`

- [x] **Step 3: 运行生成器（六项断言全过才算数）**

Run: `cd docs/gem5-fi/lsu && python3 extract.py`
Expected: 末行 `EXTRACTION VERIFICATION PASSED`；之前打印 `design models: 68 (完善版追加 10), expanded runs: 337`。
若断言失败：**禁止放宽断言**——按报错定位是规则理解错还是转录错，修脚本重跑。

- [x] **Step 4: 产物规模检查**

Run: `wc -l docs/gem5-fi/lsu/design-matrix.csv docs/gem5-fi/lsu/07-expanded-matrix.csv && ls -la docs/gem5-fi/lsu/03-design-matrix.md docs/gem5-fi/lsu/07-expanded-matrix.md`
Expected: CSV **记录数** 69 / 338（用 csv 模块计数；物理 `wc -l` 因单元格内嵌换行为 122/675——已裁定 csv 记录为准）；两个 md 非空（03 约 99KB）。

- [x] **Step 5: 人工抽查 3 格**（防"校验器自己错自己"）

Run: `python3 -c "
import csv
rows = list(csv.reader(open('docs/gem5-fi/lsu/07-expanded-matrix.csv', encoding='utf-8')))
for rid in ['A01-F0-W3', 'C07-F5-W6', 'P09-F6-W13']:
    r = next(x for x in rows if x[1] == rid)
    print(rid, '|', r[8][:60])"`
Expected: 打印的三行 `频率定义` 值与 xlsx 中对应行一致（打开 xlsx 用肉眼比对这三格；A01-F0-W3 应为「每次运行只注入 1 次…」，P09-F6-W13 应为 F6 覆盖文本）。

- [x] **Step 6: 提交并推送**

```bash
git add docs/gem5-fi/lsu/extract.py docs/gem5-fi/lsu/03-design-matrix.md docs/gem5-fi/lsu/design-matrix.csv docs/gem5-fi/lsu/07-expanded-matrix.csv docs/gem5-fi/lsu/07-expanded-matrix.md
git commit -m "docs(lsu): extract.py generator + machine-readable design/expanded matrices (68/337)

六项内置断言全过: A1 展开337行col1-15逐格重放全等 / A2 68+337 /
A3 结果槽全空+待执行 / A4 RunID自洽 / A5 唯一性 / A6 颜色(黄16-23+27,
蓝24-25,col26黄=完善版77格)。13行F6定义覆盖与12行W11 oracle覆盖如实保留并文档化。"
git push origin fi-ding
```

---

### Task 3: verify_extraction.py v1 — 独立逐格回比校验器

**Files:**
- Create: `docs/gem5-fi/lsu/verify_extraction.py`

**Interfaces:**
- Consumes: `design-matrix.csv`（69 行）、`07-expanded-matrix.csv`（338 行）、源 xlsx。
- Produces: 全部通过时 stdout `ALL PASSED`；提供 `check_fragments(path, [(label, text), ...])` 函数供 Task 4/5/6 扩展调用（签名固定：`(str, list[tuple[str, str]]) -> list[str]`，返回未命中片段的 label 列表）。

- [x] **Step 1: 写入 verify_extraction.py v1**

```python
#!/usr/bin/env python3
"""LSU 北极星提取的独立校验器 — 不 import extract.py，自己解析 xlsx 再比一遍。

v1（本任务）：CSV 逐格回比 + 集合断言。
后续任务递增：手写文档片段检查（00/01/02 → 04/05/06/08 → README）。
用法：python3 verify_extraction.py   → ALL PASSED
"""
import csv
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NS_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
HERE = Path(__file__).resolve().parent
XLSX = HERE / 'gem5-fi-LSU单元故障注入方案V1.0.xlsx'
EXPECT_SHA256 = '2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651'
APPENDED_IDS = {'T10', 'S13', 'L01', 'L02', 'L03', 'L04', 'C14', 'C15', 'O09', 'P09'}

SST = []
FAILS = []


def fail(msg):
    FAILS.append(msg)


def col_to_num(col):
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def read_grid(zf, relmap, name_substr):
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    for sh in wb.iter(f'{NS_MAIN}sheet'):
        if name_substr in (sh.get('name') or ''):
            t = relmap[sh.get(f'{NS_REL}id')].lstrip('/')
            target = t if t.startswith('xl/') else 'xl/' + t
            root = ET.fromstring(zf.read(target))
            grid = {}
            for row in root.iter(f'{NS_MAIN}row'):
                d = {}
                for c in row.iter(f'{NS_MAIN}c'):
                    m = re.match(r'([A-Z]+)(\d+)', c.get('r') or '')
                    coln = col_to_num(m.group(1)) if m else len(d) + 1
                    v = c.find(f'{NS_MAIN}v')
                    txt = v.text if v is not None else ''
                    if c.get('t') == 's' and txt != '':
                        txt = SST[int(txt)]
                    d[coln] = txt or ''
                if d:
                    grid[int(row.get('r'))] = d
            return grid
    raise KeyError(name_substr)


def norm(s):
    return re.sub(r'\s+', '', s)


def check_fragments(path, fragments):
    """空白归一化后做子串匹配；返回未命中 [(label, text)]。"""
    p = HERE / path
    if not p.exists():
        return [(label, text) for label, text in fragments] + [('__missing_file__', path)]
    text = norm(p.read_text(encoding='utf-8'))
    return [(label, frag) for label, frag in fragments if norm(frag) not in text]


def main():
    sha = hashlib.sha256(XLSX.read_bytes()).hexdigest()
    if sha != EXPECT_SHA256:
        fail(f'sha256 mismatch: {sha}')
    zf = zipfile.ZipFile(XLSX)
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    global SST
    if 'xl/sharedStrings.xml' in zf.namelist():
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS_MAIN}si'):
            SST.append(''.join(t.text or '' for t in si.iter(f'{NS_MAIN}t')))

    # V1: design-matrix.csv 逐格 == 表3
    dm = read_grid(zf, relmap, '3.位置x模型矩阵')
    rows = list(csv.reader(open(HERE / 'design-matrix.csv', encoding='utf-8')))
    if len(rows) != 69:
        fail(f'V1: design-matrix.csv 应 69 行(含表头), 实得 {len(rows)}')
    src = [dm[r] for r in sorted(dm)[1:]]
    for i, row in enumerate(rows[1:]):
        excel_row = int(row[0])
        if excel_row != sorted(dm)[1:][i]:
            fail(f'V1: 第 {i+1} 数据行 Excel行号 {excel_row} != 源 {sorted(dm)[1:][i]}')
        for c in range(12):
            if row[c + 1] != src[i].get(c + 1, ''):
                fail(f'V1: design r{excel_row} col{c+1} 不等')
    # V2: 07-expanded-matrix.csv 逐格 == 表7
    ex = read_grid(zf, relmap, '7.展开执行矩阵')
    rows = list(csv.reader(open(HERE / '07-expanded-matrix.csv', encoding='utf-8')))
    if len(rows) != 338:
        fail(f'V2: 07-expanded-matrix.csv 应 338 行, 实得 {len(rows)}')
    src = [ex[r] for r in sorted(ex)[1:]]
    for i, row in enumerate(rows[1:]):
        excel_row = int(row[0])
        if excel_row != sorted(ex)[1:][i]:
            fail(f'V2: 第 {i+1} 数据行 Excel行号错位')
        for c in range(27):
            if row[c + 1] != src[i].get(c + 1, ''):
                fail(f'V2: expanded r{excel_row} col{c+1} 不等: {row[c+1][:30]!r} vs {src[i].get(c+1, "")[:30]!r}')
    # V3: 集合断言
    dmids = {dm[r][1] for r in sorted(dm)[1:]}
    runids = {ex[r][1] for r in sorted(ex)[1:]}
    if len(dmids) != 68:
        fail(f'V3: 模型ID 应 68, 实得 {len(dmids)}')
    if len(runids) != 337:
        fail(f'V3: RunID 应 337, 实得 {len(runids)}')
    if not APPENDED_IDS <= dmids:
        fail('V3: 完善版 10 ID 不齐')

    if FAILS:
        for m in FAILS[:20]:
            print('FAIL:', m)
        print(f'VERIFICATION FAILED ({len(FAILS)} issues)')
        sys.exit(1)
    print(f'ALL PASSED (design 68 cells x13, expanded 337 cells x28, sets ok)')


if __name__ == '__main__':
    main()
```

- [x] **Step 2: 运行（此时应 ALL PASSED）**

Run: `cd docs/gem5-fi/lsu && python3 verify_extraction.py`
Expected: `ALL PASSED (design 68 cells x13, expanded 337 cells x28, sets ok)`

- [x] **Step 3: 提交并推送**

```bash
git add docs/gem5-fi/lsu/verify_extraction.py
git commit -m "docs(lsu): verify_extraction.py v1 — independent cell-by-cell CSV back-comparison"
git push origin fi-ding
```

---

### Task 4: 手写忠实文档 00/01/02 + 校验器扩展

**Files:**
- Create: `docs/gem5-fi/lsu/00-overview.md`、`docs/gem5-fi/lsu/01-units-and-research.md`、`docs/gem5-fi/lsu/02-parameter-baseline.md`
- Modify: `docs/gem5-fi/lsu/verify_extraction.py`（追加 00/01/02 片段检查）

**Interfaces:**
- Consumes: 源 xlsx 表0（单列 24 非空行）、表1（8 行×7 列）、表2（20 行×5 列）；`check_fragments()`（Task 3）。
- Produces: 三份人读文档；`FRAGMENTS_00_01_02` 片段列表（Task 6 的 README 校验在同一函数体系下扩展）。

**转录规则（三份文档通用）**：单元格文本逐字转录；表格内 `\n` → `<br>`、`|` → `\|`（与 extract.py 的 `md_cell` 一致）；每张表附 Excel 行号列；文档头部注明源表与规模；**不添加任何源表没有的事实**，提取者注一律用「> 提取注：」引用块。

- [x] **Step 1: 写 00-overview.md**

结构（源行号 → 章节）：r1 标题 → H1；r3 范围、r4 统一基线、r5 重要纠正 → 「## 1. 范围与基线」三个小节；r7–r15 工作簿结构 → 「## 2. 工作簿结构」列表 + 「### 源表 → 本目录文件映射」表（9 行：表0→00-overview.md … 表8→08-references.md，表3→03-design-matrix.md+design-matrix.csv，表7→07-expanded-matrix.csv+.md）；r17–r22 → 「## 3. 统计与判定边界（五条原文）」编号列表；r24–r25 → 「## 4. 完善版增量（原文）」。空行 r2/r6/r16/r23 跳过。r4 提到《LSU单元参数总表.md》处加「> 提取注：该文档不在本仓库；B0 定值以内嵌的表2（02-parameter-baseline.md）为准」。

- [x] **Step 2: 写 01-units-and-research.md**

H1 + 源说明（8 行×7 列，7 数据行）；7 列全列 markdown 表（列名照源表：单元/作用/现有文章/现有文章结果/指标口径/证据直接性/研究空白·本方案增量），每行附 Excel 行号列。表后加「> 提取注：指标口径纪律（AVF/条件占比/总 AVF/检出率/DelayAVF 严禁混算）为源表对后续全部实验的硬约束」。

- [x] **Step 3: 写 02-parameter-baseline.md**

H1 + 源说明（20 行×5 列，19 参数）；5 列全列表（结构/参数、B0最终值、处理、依据/合理性判断、敏感性配置）+ Excel 行号列。表后小节「### 敏感性配置一览」：从 `敏感性配置` 列归纳 S1–S5 各自改动点（S1=DTLB 64 项、S2=L1D 64KiB/4-way、S3=LSQDepCheckShift=4、S4=预取器挂 L1D、S5=启用 L1D 保护）——只使用列内已有文字，不引入新值。

- [x] **Step 4: 扩展 verify_extraction.py**

在 `main()` 的集合断言后追加：

```python
    # V4a: 00/01/02 片段检查（空白归一化子串）
    FRAGMENTS_00 = [
        ('00-范围', '范围：AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器'),
        ('00-纠正', 'B0 是可复现实验模型，不是鲲鹏 920 复刻'),
        ('00-边界1', 'attempted、eligible、activated分开记录'),
        ('00-边界3', '每个实验单元先做30个activated样本试跑'),
        ('00-边界5', '预期结果是可证伪假设，不是实测结论'),
        ('00-完善版', '原58条模型扩展'),
    ]
    FRAGMENTS_01 = [
        ('01-AGU空白', '本地论文中无直接AGU故障注入'),
        ('01-口径纪律', '严禁混算'),
        ('01-LQ', 'LQ SDC概率为0并归因于commit前依赖检查'),
        ('01-原子', '必须用多核FS和litmus禁出现结果'),
        ('01-预取', 'DelayAVF与SDC率不同'),
    ]
    FRAGMENTS_02 = [
        ('02-LQ', 'LQEntries'),
        ('02-DTLB', '32项全相联 LRU'),
        ('02-ports', '200 / 200'),
        ('02-预取', 'L2 StridePrefetcher degree=8'),
        ('02-时钟', '2.6GHz仅用于换算'),
        ('02-ECC', '关闭'),
    ]
    for path, frags in [('00-overview.md', FRAGMENTS_00), ('01-units-and-research.md', FRAGMENTS_01),
                        ('02-parameter-baseline.md', FRAGMENTS_02)]:
        for label, text in check_fragments(path, frags):
            fail(f'V4: {path} 缺片段 [{label}] {text[:40]}')
```

- [x] **Step 5: 运行校验器**

Run: `cd docs/gem5-fi/lsu && python3 verify_extraction.py`
Expected: `ALL PASSED`（打印的计数行可追加 `+ fragments 00/01/02` 字样，同步修改打印行）。
若报缺片段：先怀疑文档转录漏了原文，回 xlsx 核对，**不改片段迁就文档**。

- [x] **Step 6: 提交并推送**

```bash
git add docs/gem5-fi/lsu/00-overview.md docs/gem5-fi/lsu/01-units-and-research.md docs/gem5-fi/lsu/02-parameter-baseline.md docs/gem5-fi/lsu/verify_extraction.py
git commit -m "docs(lsu): faithful docs 00 overview / 01 units-research / 02 parameter-baseline (+verify fragments)"
git push origin fi-ding
```

---

### Task 5: 手写忠实文档 04/05/06/08 + 校验器扩展

**Files:**
- Create: `docs/gem5-fi/lsu/04-observation-points.md`、`docs/gem5-fi/lsu/05-frequency-and-sampling.md`、`docs/gem5-fi/lsu/06-workloads.md`、`docs/gem5-fi/lsu/08-references.md`
- Modify: `docs/gem5-fi/lsu/verify_extraction.py`

**Interfaces:**
- Consumes: 源 xlsx 表4（7 行×6 列）、表5（r2–r8 七档 + r11–r20 统计规则）、表6（15 行×6 列）、表8（12 行×6 列）；`check_fragments()`。
- Produces: 四份人读文档 + V4b 片段检查。

转录规则同 Task 4。

- [x] **Step 1: 写 04-observation-points.md**

H1 + 源说明；6 列全列表（层级/名称/定义/必须采集量/适用范围/判定规则）+ Excel 行号列，L0–L5 六行。表后「> 提取注：L5 守恒式 `Activated = Masked + Detected + SDC + Crash + Timeout` 是后续统计回填的闭合校验式」。

- [x] **Step 2: 写 05-frequency-and-sampling.md**

两个表：①「F0–F6 七档」（源 r2–r8，5 列：档位/名称/定义/适用故障/设计意图）+ Excel 行号；②「统计规则」（源 r12–r20，5 列：统计项/规则·公式/筛查目标/主结果目标/原因/备注——以源表 r11 子表头为准逐列照抄）+ Excel 行号。表后「> 提取注：表5 r9/r10 为源表空行，未转录」。

- [x] **Step 3: 写 06-workloads.md**

H1 + 源说明（15 行×6 列，14 负载）；6 列全列表（负载ID/名称/类型/定义·输入与oracle/主要覆盖单元/模式）+ Excel 行号列。表后「> 提取注：W4/W7/W13 为 FS/多核 FS 结构性依赖；W1 标注 FS 优先、W6 标注 SE+多核 FS 子集」。

- [x] **Step 4: 写 08-references.md**

H1 + 源说明（12 行×6 列，11 条）；6 列全列表（代码/标题·资源/类型·发表/核对方式/本工作簿用途/定位）+ Excel 行号列。表后「> 提取注：4 条 gem5 源码条目核对的是上游 stable（2026-09-24）；本仓库 vendored gem5 v25.1.0.1（upstream 62c7bf2），实施前机制核实一律以本仓源码为准（见 09-implementation-plan.md §机制核实）」。

- [x] **Step 5: 扩展 verify_extraction.py（V4b 片段）**

```python
    FRAGMENTS_04 = [
        ('04-L0', '未activated不进入SDC率分母'),
        ('04-L5守恒', 'Activated = Masked + Detected + SDC + Crash + Timeout'),
        ('04-L5类', 'Injected-not-activated'),
        ('04-判定', '与同checkpoint golden run逐事件/逐提交比较'),
    ]
    FRAGMENTS_05 = [
        ('05-F6', '首次出现指定事件时注入一次'),
        ('05-分母', 'SDC率=SDC/activated；激活率=activated/attempted'),
        ('05-筛查', '半宽5pp约385个activated'),
        ('05-停止', 'Wilson 95%区间半宽≤2pp或activated达到5000'),
        ('05-独立样本', '不得把同一运行内事件直接当独立Bernoulli样本'),
        ('05-换算', '1ms=2,600,000 cycles'),
    ]
    FRAGMENTS_06 = [
        ('06-W0', 'MiniCheck'),
        ('06-W1', 'blowfish、patricia、fft、gsm、dijkstra'),
        ('06-W7', 'MP、SB、LB、IRIW、Dekker'),
        ('06-W12', 'PRAGMA integrity_check'),
        ('06-W11', '选择 mcf、omnetpp、xalancbmk、lbm'),
    ]
    FRAGMENTS_08 = [
        ('08-核对', '2026-09-24核对'),
        ('08-O3', 'O3_ARM_v7a.py'),
        ('08-TC23', 'Silent Data Corruptions: Microarchitectural Perspectives'),
        ('08-CHAOS', 'arXiv 2602.02119'),
    ]
```

（循环注册方式与 Task 4 的 V4a 相同。）

- [x] **Step 6: 运行校验器**

Run: `cd docs/gem5-fi/lsu && python3 verify_extraction.py`
Expected: `ALL PASSED`。

- [x] **Step 7: 提交并推送**

```bash
git add docs/gem5-fi/lsu/04-observation-points.md docs/gem5-fi/lsu/05-frequency-and-sampling.md docs/gem5-fi/lsu/06-workloads.md docs/gem5-fi/lsu/08-references.md docs/gem5-fi/lsu/verify_extraction.py
git commit -m "docs(lsu): faithful docs 04 observation / 05 frequency / 06 workloads / 08 references (+verify fragments)"
git push origin fi-ding
```

---

### Task 6: README 总纲（含基础设施映射）+ 校验器扩展

**Files:**
- Create: `docs/gem5-fi/lsu/README.md`
- Modify: `docs/gem5-fi/lsu/verify_extraction.py`

**Interfaces:**
- Consumes: 全部已交付文档与 CSV（Task 1–5）、仓库工具链（grep 核实对象）、`check_fragments()`。
- Produces: 北极星入口文档；V4c 片段检查。

- [x] **Step 1: 基础设施映射的真实 grep（结果如实写入 README §7，不做空头声明）**

Run:
```bash
grep -n "lsq_fwd\|l1d_fwd\|addr_path\|l1_tlb" tools/runner.py | head -8
ls configs/se/ooo_proxy.py configs/se/kp920_proxy.py 2>&1
ls CHAOS/gem5/src/cpu/o3/ | grep -i "LSQ\|chaos" | head -10
grep -rn "stride\|Stride" CHAOS/gem5/configs/common/cores/arm/O3_ARM_v7a.py 2>/dev/null | head -3
ls CHAOS/gem5/src/mem/cache/prefetch/ 2>/dev/null | head -5
```
把**实际输出**记入 README §7 的映射表（复用列）；命令未命中/文件不存在的项写入「需要新建」列。§7 表格两列：「方案需要 → 仓库现状（grep 证据）」。

- [x] **Step 2: 写 README.md**

章节（按 spec §7）：
1. `## 1. 北极星目标`——LSU 三问（哪些位置有真实 SDC 潜力 / SDC 前微架构层可观测前兆 / 结构化模型相对随机翻转的增量）；一段话总述 7 单元 × 68 模型 × 337 格。
2. `## 2. 文档地图`——9 行表（源工作表 → 本目录文件 → 规模），加 extract.py / verify_extraction.py / 源 xlsx 三行。
3. `## 3. 数字总账`——68 模型（7 单元分布 A8/T10/S13/C15/O9/P9/L4，完善版 58+10）、337 格（频率×单元×负载三个分布，数字用 Global Constraints 的分布数字）、自适应样本量口径（试跑 30 activated → 筛查 ≥385 → 主结果 Wilson ≤2pp 或 5000）、规模量级估算（筛查下限 337×385 ≈ 13 万次 activated 起）。
4. `## 4. 设计边界（源表原文）`——B0 非鲲鹏 920 复刻 / 指标口径严禁混算 / SDC 率分母=activated / F0 与 F1–F4 不混为一个故障率。
5. `## 5. 方法的核心主张`——从 03 设计理由列归纳 4–6 条（结构化换值/合法映射替换绕过地址异常、保护故障族 T09/S12/C13/O08、L1 影子比对、Crash 双拆分对应 L5 分类），每条注明出处模型ID。
6. `## 6. 实施顺序`——源表自带验证锚点优先：LQ/SQ 单 bit 复现 TC'23 LQ/SQ SDC=0%（注入器自检）、T01 DTLB 对照 TC'22 Crash AVF≈50%、完善版 LQ 行（L01–L04）是文献增量所在；再排 AGU → SQ/LQ → Cache → TLB → 原子/预取（FS 依赖后置）。
7. `## 7. 与本仓库现有基础设施的映射（2026-09-24 grep 核实）`——Step 1 的真实结果表 + 需要新建清单（AGU、原子与同步、预取器、LQ 生命周期、F4/F6 触发语义、自适应样本量两阶段编排、多核 FS）。
8. `## 8. 诚实声明`——《LSU单元参数总表.md》不在仓库（B0 以 02 为准）/ TLB 注入器 SE-inert / W4/W7/W13 FS 结构性缺口 / 文献核对基于上游 stable 而本仓 vendored v25.1.0.1 / 参数非 920 真值 / 结果槽全空=待执行。
9. `## 9. 溯源与复现`——sha256、`cd docs/gem5-fi/lsu && python3 extract.py`（预期 `EXTRACTION VERIFICATION PASSED`）、`python3 verify_extraction.py`（预期 `ALL PASSED`）、计划文件指针 `docs/superpowers/plans/2026-09-24-lsu-north-star-extraction.md`。

- [x] **Step 3: 扩展 verify_extraction.py（V4c）**

```python
    FRAGMENTS_README = [
        ('RM-sha', '2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651'),
        ('RM-68', '68'),
        ('RM-337', '337'),
        ('RM-复现', 'python3 extract.py'),
        ('RM-校验', 'python3 verify_extraction.py'),
        ('RM-诚实-920', '不是鲲鹏 920 复刻'),
        ('RM-诚实-TLB', 'SE-inert'),
        ('RM-地图', '09-implementation-plan.md'),
    ]
```

- [x] **Step 4: 运行校验器**

Run: `cd docs/gem5-fi/lsu && python3 verify_extraction.py`
Expected: `ALL PASSED`。

- [x] **Step 5: 提交并推送**

```bash
git add docs/gem5-fi/lsu/README.md docs/gem5-fi/lsu/verify_extraction.py
git commit -m "docs(lsu): README north-star navigation + grep-verified infra mapping (+verify fragments)"
git push origin fi-ding
```

---

### Task 7: 09 实施总纲 + 人工抽查 + 收尾

**Files:**
- Create: `docs/gem5-fi/lsu/09-implementation-plan.md`
- Modify: 本计划文件（勾选最后的抽查记录）、`progress.md`（收尾条目）

**Interfaces:**
- Consumes: 00–08 全部忠实层（裁决基准）、spec §8 的机制核实清单、仓库源码结构。
- Produces: LSU 故障注入实施总纲（后续所有注入器/campaign 工作包的母计划）。

- [x] **Step 1: 机制核实对象的真实存在性检查（写进 09 的引用必须指向真实文件）**

Run:
```bash
ls CHAOS/gem5/src/cpu/o3/lsq.hh CHAOS/gem5/src/cpu/o3/lsq.cc
grep -n "SSIT\|LFST" CHAOS/gem5/src/cpu/o3/lsq_impl.hh CHAOS/gem5/src/cpu/o3/lsq.hh 2>/dev/null | head -5
ls CHAOS/gem5/src/arch/arm/tlb.hh CHAOS/gem5/src/mem/cache/prefetch/stride.hh 2>&1
grep -rn "exclusiveMonitor\|monitor" CHAOS/gem5/src/arch/arm/tlb.cc 2>/dev/null | head -3
```
09 中每条机制核实项引用的文件路径必须先通过存在性检查；不存在的路径改到真实位置（如实记录）。

- [x] **Step 2: 写 09-implementation-plan.md**

章节（按 spec §8，头部声明「本文件与 00–08 冲突时以 00–08 为准」+ 编写日期 + 依据）：
1. `## 1. 目标与成功判据`——337 格 × 11 结果列回填（记录状态全部离开「待执行」）；L0–L5 观测数据；自检锚点记录（TC'23 LQ/SQ SDC=0% 复现、TC'22 DTLB Crash AVF≈50% 对照）；元分析报告（三问的回答 + 位置×SDC 潜力排序）。
2. `## 2. 机制核实 N 表`——9 行表（对本仓 vendored v25.1.0.1），列 = 「# / xlsx 表述 / v25.1 实际（源码:行号）/ 对模型行的影响 / 状态」；九项：① LQ/SQ 结构（lsq.hh/lsq.cc 表项字段、head/tail、violation/replay 路径、16/16 项配置）② SSIT/LFST 落点与 1024/1024 配置 ③ DTLB=32 配置路径（gem5 默认 64）④ L1D 32KiB/2-way、MSHR 6/targets 8、write buffer 16 配置来源 ⑤ L2 StridePrefetcher 挂接 ⑥ exclusive monitor/原子 RMW 多核语义 ⑦ AGU 有效地址截获点与 CHAOSAddrPath 关系 ⑧ F4 短突发/F6 确定性触发 vs chaos_trigger F0–F5 差距 ⑨ MSHR merge/fill/writeback/dirty eviction 路径。**状态列初始全部「待核实」**——本表是计划，不预填结论。
3. `## 3. WBS（W0–Wn，每个 W = 一个 patch 单元）`——初始骨架：W0 平台/B0 参数落地（configs 新 LSU 家族或扩展 ooo_proxy）→ W1 机制核实（§2 九项逐条源码核实并回填表）→ W2 触发语义 F0–F6（含 F4 突发/F6 确定性事件，扩展 chaos_trigger）→ W3 观测层 L0–L5（attempted/eligible/activated 记录、影子比对、commit 级比较）→ W4 AGU 注入器 → W5 SQ/LQ 注入器 → W6 L1d-Cache 注入器 → W7 L1d-TLB（FS 依赖）→ W8 原子与同步+数据预取器（多核 FS 依赖）→ W9 负载准备（W0–W13）→ W10 campaign 编排（自适应样本量两阶段）→ W11 元分析与报告。每个 W 注明依赖关系。
4. `## 4. 里程碑`——M0 平台就绪（W0–W1）→ M1 触发与观测（W2–W3）→ M2 SE 单元首批 formal（AGU/SQ/LQ/Cache）→ M3 FS 单元（TLB）→ M4 多核（原子/预取）→ M5 全网格回填完成 → M6 元分析报告。
5. `## 5. 算力预算`——量级估算：筛查下限 337×385 ≈ 13 万次 activated 起、主结果上限 337×5000 ≈ 168 万；遵守 4 并发 gem5 进程硬上限（CLAUDE.md）；试跑 30 activated/格。
6. `## 6. 裁决规则`——与 00–08 冲突时以 00–08 为准；机制核实结论只修正「落点」不修正「故障语义」（同 ooo 06 的 N 表先例）。

- [x] **Step 3: 结构自检**

Run: `grep -c '^## ' docs/gem5-fi/lsu/09-implementation-plan.md && grep -c '待核实' docs/gem5-fi/lsu/09-implementation-plan.md`
Expected: `6`（六个章节）；`≥9`（九个待核实状态）。

- [x] **Step 4: 人工抽查 ≥10 格（spec §9.3 的第三道防线）**

Run: `python3 -c "
import csv, random
random.seed(42)
rows = list(csv.reader(open('docs/gem5-fi/lsu/07-expanded-matrix.csv', encoding='utf-8')))[1:]
for r in random.sample(rows, 6):
    print(r[0], '|', r[7][:50])
dms = list(csv.reader(open('docs/gem5-fi/lsu/design-matrix.csv', encoding='utf-8')))[1:]
for r in random.sample(dms, 4):
    print(r[1], '|', r[3][:50])"`
打开 xlsx 对应行逐格肉眼比对这 10 行（打印的是锚点列，比对时看整行）；结果记录在本步骤后面：
`抽查记录（执行时填写，2026-09-24）：10/10 一致（seed=42 抽样：展开矩阵 Excel 行 329/59/14/142/127/116 共 6 行 × 27 格 + 设计矩阵 S01/T06/T04/P05 共 4 行 × 12 格；执行代理无法打开 Excel，改用独立第三方 stdlib 解析器（zipfile+ElementTree+sharedStrings，rels Target 先 lstrip('/')）逐格比对 xlsx vs CSV，不 import extract.py/verify_extraction.py；人眼复核可随时用 xlsx+CSV 进行）`

- [x] **Step 5: 终验（全链）**

Run: `cd docs/gem5-fi/lsu && python3 extract.py && python3 verify_extraction.py && python3 -m py_compile extract.py verify_extraction.py && echo DONE`
Expected: 依次 `EXTRACTION VERIFICATION PASSED` → `ALL PASSED` → `DONE`。

- [ ] **Step 6: 更新 progress.md 收尾条目并提交推送**

progress.md 追加：交付清单（文件数/行数）、三重验证结果（六断言/ALL PASSED/人工抽查 N/10）、与 ooo 轨道并列关系、下一步指向 09 的 W0。

```bash
git add docs/gem5-fi/lsu/09-implementation-plan.md progress.md docs/superpowers/plans/2026-09-24-lsu-north-star-extraction.md
git commit -m "docs(lsu): 09 implementation master plan (9 mechanism checks + WBS W0-W11 + milestones)

人工抽查 10/10 一致; extract 六断言 + verify ALL PASSED 全链终验通过;
北极星提取完成, 下一步 = 09 W0 (平台/B0 参数落地)。"
git push origin fi-ding
```

---

## Self-Review 结论（写计划时已自查）

- **Spec 覆盖**：spec §3 目录结构 → Tasks 1–7 全部文件；§4 忠实层规格 → Tasks 4/5 转录规则 + Task 2 生成器；§5 extract.py 六断言 → Task 2（A1–A6 与 spec 编号一一对应）；§6 校验器 → Tasks 3/4/5/6（V1–V4 递增）；§7 README → Task 6；§8 09 → Task 7；§9 验收 → 各任务 Step + Task 7 Step 4/5；§10 提交切分 → 7 个 commit（顺序按 spec 授权调整为 verify 前移）；§11 诚实约束 → Global Constraints + 各文档提取注。
- **占位符扫描**：无 TBD/TODO；唯一运行时填写点是 Task 7 Step 4 的抽查记录行（设计如此，spec §9.3 要求）。
- **类型/命名一致性**：`check_fragments(path, fragments) -> list`、CSV 表头 `['Excel行']+源列名`、断言编号 A1–A6/V1–V4、片段 label 前缀与文件名一一对应，已逐任务核对。
