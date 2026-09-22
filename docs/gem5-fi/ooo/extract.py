#!/usr/bin/env python3
"""docs/gem5-fi/ooo/ 的忠实层生成器 + 提取正确性交叉校验。

从《gem5-fi-OoO单元故障注入方案V1.0.xlsx》生成：
  04-design-matrix.md      工作表「1.位置x模型矩阵」91 设计行（按 6 单元分节，13 列全列 + 稳定 ID D01-D91）
  design-matrix.csv        同上的机读版
  05-expanded-matrix.csv   工作表「5.展开矩阵」226 实验格（含 7 个空结果列，实施时填写）
  05-expanded-matrix.md    展开矩阵的列文档 + 单元×频率分布汇总

交叉校验（提取正确性不靠"看起来对"）：
  1) 从 Sheet1 的「适用频率 × 适用负载」自行重放展开，与 Sheet5 逐行比对十列全等；
  2) 断言行数 91 / 226；
  3) 断言 Sheet5 结果列（SDC%..污染扇出数）在源表中全为空；
  4) 断言 (单元, 位置标签) 在 91 设计行中唯一（E 行 → D 行映射的依据）。

纯标准库（本机 pip 403，openpyxl 不可用；xlsx = zip + spreadsheetml XML）。
用法：python3 extract.py   （在任意目录运行均可，路径相对本脚本解析）
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
XLSX = HERE.parent.parent / 'gem5-fi-OoO单元故障注入方案V1.0.xlsx'

SHEET1_COLS = ['单元', '位置标签', '注入位置', '故障类型', '故障模型（具体做法）', '适用频率',
               '事件触发条件', '适用负载', '计数基准', 'L1 重点观测点', '预期结果与依据',
               '设计理由', '可对照文献']
SHEET5_COLS = ['单元', '位置标签', '注入位置', '故障类型', '适用频率', '事件触发条件', '负载',
               '计数基准', '建议样本量', 'SDC%', 'Crash%', 'Timeout%', 'Masked%',
               '仿真器断言崩溃占比%', '潜伏期（commit序号）', '污染扇出数', '为什么这么设计（精简）']
# Sheet5 结果列（源表中为空，是实施时的填写槽）
RESULT_COLS = list(range(9, 16))  # 0-based 9..15


def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def split_ref(ref: str):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    return int(m.group(2)), col_to_num(m.group(1))


def load_sheet(zf: zipfile.ZipFile, names, wanted_substr: str):
    """返回 {excel_row: [col1..colN 字符串]}，按 workbook.xml 的表序找到目标表。"""
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    target = None
    for sh in wb.iter(f'{NS_MAIN}sheet'):
        if wanted_substr in (sh.get('name') or ''):
            t = relmap[sh.get(f'{NS_REL}id')]
            target = t if t.startswith('xl/') else 'xl/' + t.lstrip('/')
            break
    assert target, f'sheet containing {wanted_substr!r} not found'

    sst = []
    if 'xl/sharedStrings.xml' in names:
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS_MAIN}si'):
            sst.append(''.join(t.text or '' for t in si.iter(f'{NS_MAIN}t')))

    root = ET.fromstring(zf.read(target))
    grid = {}
    maxcol = 0
    sd = root.find(f'{NS_MAIN}sheetData')
    for row in sd.findall(f'{NS_MAIN}row'):
        for c in row.findall(f'{NS_MAIN}c'):
            t, v, is_ = c.get('t'), c.find(f'{NS_MAIN}v'), c.find(f'{NS_MAIN}is')
            val = None
            if t == 's' and v is not None:
                val = sst[int(v.text)]
            elif t == 'inlineStr' and is_ is not None:
                val = ''.join(x.text or '' for x in is_.iter(f'{NS_MAIN}t'))
            elif v is not None and v.text is not None:
                val = v.text
            if not val:
                continue
            rn, ci = split_ref(c.get('r'))
            grid[(rn, ci)] = val
            maxcol = max(maxcol, ci)
    return grid, maxcol


def rows_from_grid(grid, maxcol, ncols, r_from, r_to):
    """返回 [(excel_row, [c1..cN])]，空单元格为 ''。"""
    out = []
    for rn in range(r_from, r_to + 1):
        vals = [grid.get((rn, ci), '') for ci in range(1, ncols + 1)]
        out.append((rn, vals))
    return out


def md_escape(s: str) -> str:
    return s.replace('|', '\\|').replace('\r', '').replace('\n', '<br>')


def freq_list(freq_raw: str):
    """Sheet1 适用频率 → 展开用的频率值列表。

    '—（不适用固定间隔）' → [原文]（事件触发行，不按频率展开）
    'F0 / F1 / F2' → ['F0','F1','F2']
    'F1（持续到…）' → [原文]（带注释的单档，注释随行保留）
    """
    s = freq_raw.strip()
    if s.startswith('—'):
        return [s]
    parts = [p.strip() for p in s.split('/')]
    return parts if len(parts) > 1 else [s]


def workload_list(load_raw: str):
    return [p.strip() for p in load_raw.split('、') if p.strip()]


def expected_sample_size(count_basis: str) -> str:
    return '2000 次运行' if count_basis == '运行计数' else '覆盖≥2000次目标事件'


def main():
    zf = zipfile.ZipFile(XLSX)
    names = zf.namelist()

    g1, _ = load_sheet(zf, names, '位置x模型矩阵')
    g5, _ = load_sheet(zf, names, '展开矩阵')
    design = rows_from_grid(g1, 13, 13, 2, 92)    # 91 行
    expanded = rows_from_grid(g5, 17, 17, 2, 227)  # 226 行

    report = []
    ok = True

    # ---- 断言 1：行数 ----
    a1 = len(design) == 91 and len(expanded) == 226
    ok &= a1
    report.append(f'[rows] design=91? {len(design)==91}  expanded=226? {len(expanded)==226}')

    # ---- 断言 2：(单元, 位置标签) 唯一 ----
    key2d = {}
    for rn, v in design:
        key2d[(v[0], v[1])] = rn
    a2 = len(key2d) == 91
    ok &= a2
    report.append(f'[d-id-key] (单元,位置标签) unique across 91 rows: {a2}')

    # ---- 断言 3：Sheet5 结果列全空 ----
    nonempty = [(rn, SHEET5_COLS[c]) for rn, v in expanded for c in RESULT_COLS if v[c]]
    a3 = not nonempty
    ok &= a3
    report.append(f'[result-slots] sheet5 result cols empty in all 226 rows: {a3}')

    # ---- 断言 4：展开重放比对 ----
    replay = []  # (design_excel_row, [sheet5 十列])
    for rn, v in design:
        unit, label, loc, ftype = v[0], v[1], v[2], v[3]
        freq_raw, trig, loads, basis, expect = v[5], v[6], v[7], v[8], v[10]
        for f in freq_list(freq_raw):
            for w in workload_list(loads):
                replay.append((rn, [unit, label, loc, ftype, f, trig, w, basis,
                                    expected_sample_size(basis), expect]))
    a4 = len(replay) == 226
    mismatches = []
    cmp_labels = SHEET5_COLS[:9] + ['为什么这么设计（精简）']
    if a4:
        for (drn, rep), (ern, act) in zip(replay, expanded):
            # replay 十列 ↔ sheet5 的 1-9 列 + 第 17 列（跳过 7 个空结果列）
            act10 = act[:9] + [act[16]]
            if rep != act10:
                diffs = [(cmp_labels[i], rep[i], act10[i])
                         for i in range(10) if rep[i] != act10[i]]
                mismatches.append((drn, ern, diffs))
        a4 = not mismatches
    ok &= a4
    report.append(f'[expand-replay] regenerated {len(replay)} rows; '
                  f'10-column row-by-row match vs sheet5: {"ALL MATCH (226/226)" if a4 else "MISMATCH"}')
    for drn, ern, diffs in mismatches[:5]:
        report.append(f'  MISMATCH designR{drn} vs sheet5R{ern}: {diffs}')

    # ---- E→D 映射 ----
    d_of = {}
    for i, (rn, v) in enumerate(design, start=1):
        d_of[(v[0], v[1])] = f'D{i:02d}'

    # ---- 统计 ----
    units = []
    for rn, v in design:
        if v[0] not in units:
            units.append(v[0])
    unit_counts = {u: sum(1 for _, v in design if v[0] == u) for u in units}
    ftype_tally = {}
    for _, v in design:
        ftype_tally[v[3]] = ftype_tally.get(v[3], 0) + 1

    def freq_key(f):
        if f.startswith('—'):
            return '事件触发'
        return re.sub(r'（.*', '', f)

    tally = {u: {} for u in units}
    basis_tally = {}
    wl_tally = {}
    for _, v in expanded:
        fk = freq_key(v[4])
        tally[v[0]][fk] = tally[v[0]].get(fk, 0) + 1
        basis_tally[v[7]] = basis_tally.get(v[7], 0) + 1
        wl_tally[v[6]] = wl_tally.get(v[6], 0) + 1

    # ---- 输出 04-design-matrix.md ----
    md = []
    md.append('# 04 · 位置×模型设计矩阵（91 个设计单元）')
    md.append('')
    md.append('> 来源：《gem5-fi-OoO单元故障注入方案V1.0.xlsx》工作表「1.位置x模型矩阵」'
              'R2–R92，**逐行忠实提取，未做任何改写**（生成器：`extract.py`，可重跑复现）。')
    md.append('> 行 ID `D01–D91` 为本目录新增的稳定引用编号，按 Excel 行序分配；'
              '`Excel行` 列为原表行号，供回溯。后续文档/提交/注入器实现统一用 D 编号指代设计单元。')
    md.append('> 列语义：13 列与源表一致；五条贯穿性边界条件见 `00-overview.md`，'
              '频率档位定义见 `02-frequency-and-sampling.md`。')
    md.append('')
    md.append('## 索引（扫描用紧凑表）')
    md.append('')
    md.append('| ID | Excel行 | 单元 | 位置标签 | 故障类型 | 适用频率 | 事件触发条件 | 适用负载 | 计数基准 |')
    md.append('|---|---|---|---|---|---|---|---|---|')
    for i, (rn, v) in enumerate(design, start=1):
        md.append(f'| D{i:02d} | R{rn} | ' + ' | '.join(
            md_escape(v[j]) for j in (0, 1, 3, 5, 6, 7, 8)) + ' |')
    md.append('')
    for u in units:
        idxs = [i for i, (_, v) in enumerate(design, start=1) if v[0] == u]
        md.append(f'## {u}（{len(idxs)} 行：D{idxs[0]:02d}–D{idxs[-1]:02d}）')
        md.append('')
        md.append('| ' + ' | '.join(['ID', 'Excel行'] + SHEET1_COLS) + ' |')
        md.append('|' + '---|' * (len(SHEET1_COLS) + 2))
        for i, (rn, v) in enumerate(design, start=1):
            if v[0] != u:
                continue
            md.append(f'| D{i:02d} | R{rn} | ' + ' | '.join(md_escape(x) for x in v) + ' |')
        md.append('')
    (HERE / '04-design-matrix.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 输出 design-matrix.csv ----
    with open(HERE / 'design-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ID', 'Excel行'] + SHEET1_COLS)
        for i, (rn, v) in enumerate(design, start=1):
            w.writerow([f'D{i:02d}', f'R{rn}'] + v)

    # ---- 输出 05-expanded-matrix.csv ----
    with open(HERE / '05-expanded-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ID', 'Excel行', '设计单元ID'] + SHEET5_COLS)
        for i, (rn, v) in enumerate(expanded, start=1):
            w.writerow([f'E{i:03d}', f'R{rn}', d_of[(v[0], v[1])]] + v)

    # ---- 输出 05-expanded-matrix.md ----
    e = []
    e.append('# 05 · 展开矩阵（位置×频率×负载，226 个实验格）')
    e.append('')
    e.append('> 来源：工作表「5.展开矩阵（位置x频率x负载）」R2–R227，逐行忠实提取。'
             '全量数据在 **`05-expanded-matrix.csv`**（UTF-8，无 BOM）；本文件只给列文档与分布汇总。')
    e.append('> 展开规则已由 `extract.py` 交叉校验：从「1.位置x模型矩阵」的适用频率×适用负载'
             '重放展开，226 行 × 10 列与源表逐格全等。')
    e.append('')
    e.append('## 列文档（CSV 共 20 列 = 3 个管理列 + 源表 17 列）')
    e.append('')
    e.append('| 列 | 说明 |')
    e.append('|---|---|')
    e.append('| ID | `E001–E226`，本目录稳定引用编号（实验格粒度） |')
    e.append('| Excel行 | 源工作表行号 |')
    e.append('| 设计单元ID | 对应 `04-design-matrix.md` 的 `D01–D91` |')
    for c in SHEET5_COLS[:9]:
        e.append(f'| {c} | 源表原列 |')
    e.append('| SDC% ~ 污染扇出数（7 列） | **源表即空 = 实施时的结果填写槽**：'
             'SDC%/Crash%/Timeout%/Masked%/仿真器断言崩溃占比%/潜伏期（commit序号）/污染扇出数 |')
    e.append('| 为什么这么设计（精简） | 源表该列 = 设计矩阵对应行的「预期结果与依据」 |')
    e.append('')
    e.append('## 分布汇总')
    e.append('')
    e.append('### 单元 × 频率档（实验格数）')
    e.append('')
    all_fk = []
    for u in units:
        for fk in tally[u]:
            if fk not in all_fk:
                all_fk.append(fk)
    e.append('| 单元 | ' + ' | '.join(all_fk) + ' | 合计 |')
    e.append('|---|' + '---|' * (len(all_fk) + 1))
    for u in units:
        row = [str(tally[u].get(fk, 0)) for fk in all_fk]
        e.append(f'| {u} | ' + ' | '.join(row) + f' | {sum(tally[u].values())} |')
    e.append('| 合计 | ' + ' | '.join(str(sum(tally[u].get(fk, 0) for u in units)) for fk in all_fk)
             + ' | 226 |')
    e.append('')
    e.append('### 计数基准 / 负载分布')
    e.append('')
    e.append('| 计数基准 | 实验格数 |')
    e.append('|---|---|')
    for k in sorted(basis_tally):
        e.append(f'| {k} | {basis_tally[k]} |')
    e.append('')
    e.append('| 负载 | 实验格数 |')
    e.append('|---|---|')
    for k in sorted(wl_tally):
        e.append(f'| {k} | {wl_tally[k]} |')
    e.append('')
    (HERE / '05-expanded-matrix.md').write_text('\n'.join(e) + '\n', encoding='utf-8')

    # ---- 报告 ----
    sha = hashlib.sha256(XLSX.read_bytes()).hexdigest()
    report.append(f'[units] ' + ', '.join(f'{u}={unit_counts[u]}' for u in units))
    report.append('[fault-types] ' + ', '.join(f'{k}={v}' for k, v in sorted(ftype_tally.items(), key=lambda x: -x[1])))
    report.append(f'[outputs] 04-design-matrix.md, design-matrix.csv (91 rows), '
                  f'05-expanded-matrix.csv (226 rows), 05-expanded-matrix.md')
    report.append(f'[source] {XLSX.name} sha256={sha}')
    print('\n'.join(report))
    if not ok:
        print('\nEXTRACTION VERIFICATION FAILED — do not commit generated files.')
        sys.exit(1)
    print('\nEXTRACTION VERIFICATION PASSED')


if __name__ == '__main__':
    main()
