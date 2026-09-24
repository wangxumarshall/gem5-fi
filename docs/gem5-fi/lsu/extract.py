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
