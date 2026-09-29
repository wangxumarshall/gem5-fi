#!/usr/bin/env python3
"""docs/gem5-fi/lsu/ 独立校验器（不 import extract.py）。

用与 extract.py 不同的解析路径（regex 直扫 spreadsheetml XML，非 ElementTree）重新
解析《gem5-fi-LSU单元故障注入方案V2.0.xlsx》，对生成产物逐格回比：
  V1  9 表表名与顺序 + 每表非空 cell 数 22/56/136/910/42/108/90/5595/72（独立复算）；
  V2  design-matrix.csv：65 行（表头+64），每行 2 管理列 + 14 列 == 独立解析值（逐格）；
  V3  07-expanded-matrix.csv：326 行（表头+325），每行 1 管理列 + 43 列 == 独立解析值
      （逐格，含 27 个母公式格的 ⟦f:公式⟧ 记法与空值槽）；
  V4  md 覆盖：00–08 各 md 文件包含其源工作表全部非空 cell 的展示文本
      （表格 md 查 md_escape 后文本；00-overview 查原文；07-expanded-matrix.md 仅查
      43 个表头列名——全量数据由 V3 的 CSV 承担）；
  V5  README 含 sha256 与 cell 计数字符串。

任一失败即非零退出。用法：python3 verify_extraction.py（在任意目录运行均可）
"""

import csv
import hashlib
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import unescape

HERE = Path(__file__).resolve().parent
XLSX = HERE / 'gem5-fi-LSU单元故障注入方案V2.0.xlsx'

SHEETS = ['0.说明与总览', '1.单元与现有研究', '2.LSU参数基线', '3.位置x模型矩阵',
          '4.观测点定义', '5.频率与统计', '6.负载清单', '7.展开执行矩阵', '8.文献与来源']
EXPECTED_CELLS = [22, 56, 136, 910, 42, 108, 90, 5595, 72]
N_DESIGN, N_EXP = 64, 325
FORMULA_MARK = '⟦f:'


def fail(msg):
    print(f'FAIL: {msg}')
    sys.exit(1)


# ---------------- 独立 regex 解析路径 ----------------

def unent(s):
    s = unescape(s, {'&quot;': '"', '&apos;': "'"})
    # XML 行尾规范化（§2.11）：ElementTree 等 XML 解析器自动把 \r\n / \r 规范为 \n；
    # regex 直扫原始字节须显式做同样规范化，才能与 extract.py 的产物逐字比对。
    return s.replace('\r\n', '\n').replace('\r', '\n')


def parse_shared_strings(zf):
    xml = zf.read('xl/sharedStrings.xml').decode('utf-8')
    sst = []
    for si in re.findall(r'<si>(.*?)</si>', xml, re.S):
        sst.append(''.join(unent(t) for t in re.findall(r'<t[^>]*>(.*?)</t>', si, re.S)))
    return sst


def sheet_files(zf):
    """表名 → 包内路径（按 workbook.xml + rels 顺序，regex 路径）。"""
    wb = zf.read('xl/workbook.xml').decode('utf-8')
    rels = zf.read('xl/_rels/workbook.xml.rels').decode('utf-8')
    relmap = dict(re.findall(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    # 也兼容属性倒序写法 Target 在前
    for m in re.finditer(r'<Relationship\b[^>]*/>', rels):
        tag = m.group(0)
        rid = re.search(r'Id="([^"]+)"', tag)
        tgt = re.search(r'Target="([^"]+)"', tag)
        if rid and tgt:
            relmap[rid.group(1)] = tgt.group(1)
    out = []
    for m in re.finditer(r'<sheet\b[^>]*/>', wb):
        tag = m.group(0)
        name = re.search(r'name="([^"]+)"', tag).group(1)
        rid = re.search(r'r:id="([^"]+)"', tag).group(1)
        t = relmap[rid].lstrip('/')
        if not t.startswith('xl/'):
            t = 'xl/' + t
        out.append((name, t))
    return out


def parse_cells(xml, sst):
    """regex 直扫 <c> → {(row, col): (val|None, formula|None)}。自闭合 <c/> 跳过。"""
    grid = {}
    for m in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*?)(/>|>(.*?)</c>)', xml, re.S):
        col, row, attrs, tail, inner = m.group(1), int(m.group(2)), m.group(3), m.group(4), m.group(5) or ''
        t = re.search(r'\bt="([^"]+)"', attrs)
        t = t.group(1) if t else None
        val = None
        formula = None
        fm = re.search(r'<f[^>]*?(/>|>(.*?)</f>)', inner, re.S)
        if fm:
            formula = unent(fm.group(2)) if fm.group(2) else None
        vm = re.search(r'<v[^>]*?(/>|>(.*?)</v>)', inner, re.S)
        if vm and vm.group(2) is not None and vm.group(2) != '':
            raw = unent(vm.group(2))
            if t == 's':
                val = sst[int(raw)]
            elif t == 'b':
                val = 'TRUE' if raw.strip() not in ('0', '') else 'FALSE'
            else:
                val = raw
        elif t == 'inlineStr':
            is_ = re.search(r'<is>(.*?)</is>', inner, re.S)
            if is_:
                val = ''.join(unent(x) for x in re.findall(r'<t[^>]*>(.*?)</t>', is_.group(1), re.S))
        if val or formula:
            ci = 0
            for ch in col:
                ci = ci * 26 + (ord(ch) - 64)
            grid[(row, ci)] = (val, formula)
    return grid


def disp(val, formula):
    text = val or ''
    if formula is not None:
        text = (text + FORMULA_MARK + formula + '⟧') if text else (FORMULA_MARK + formula + '⟧')
    return text


def md_escape(s):
    return s.replace('|', '\\|').replace('\r', '').replace('\n', '<br>')


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    zf = zipfile.ZipFile(XLSX)
    sst = parse_shared_strings(zf)
    files = sheet_files(zf)

    # V1: 表清单 + cell 计数（独立复算）
    names = [n for n, _ in files]
    if names != SHEETS:
        fail(f'V1 sheet list mismatch: {names}')
    grids = {n: parse_cells(zf.read(t).decode('utf-8'), sst) for n, t in files}
    counts = [len(grids[n]) for n in names]
    if counts != EXPECTED_CELLS:
        fail(f'V1 cell counts mismatch: {counts} != {EXPECTED_CELLS}')
    print(f'V1 PASS — sheets + cell counts (independent regex path): '
          + '/'.join(map(str, counts)))

    g = {n: grids[n] for n in names}
    s4 = g['3.位置x模型矩阵']
    s8 = g['7.展开执行矩阵']

    # V2: design-matrix.csv 逐格回比
    with open(HERE / 'design-matrix.csv', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    if len(rows) != N_DESIGN + 1:
        fail(f'V2 design csv rows {len(rows)} != {N_DESIGN + 1}')
    bad = 0
    for i, row in enumerate(rows[1:], start=2):  # Excel 行 2..65
        if len(row) != 16:
            fail(f'V2 row R{i} has {len(row)} cols != 16')
        if row[1] != f'R{i}':
            fail(f'V2 row R{i} Excel行 mismatch: {row[1]}')
        for ci in range(14):
            expect = disp(*s4.get((i, ci + 1), (None, None)))
            if row[ci + 2] != expect:
                bad += 1
                if bad <= 3:
                    print(f'  V2 diff R{i} col{ci + 1}: csv={row[ci + 2]!r} xlsx={expect!r}')
    if bad:
        fail(f'V2 design csv: {bad} cell mismatches')
    print(f'V2 PASS — design-matrix.csv: {N_DESIGN} rows x 14 cols, cell-by-cell equal')

    # V3: 07-expanded-matrix.csv 逐格回比
    with open(HERE / '07-expanded-matrix.csv', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    if len(rows) != N_EXP + 1:
        fail(f'V3 expanded csv rows {len(rows)} != {N_EXP + 1}')
    bad = n_formula_cells = 0
    for i, row in enumerate(rows[1:], start=2):  # Excel 行 2..326
        if len(row) != 44:
            fail(f'V3 row R{i} has {len(row)} cols != 44')
        if row[0] != f'R{i}':
            fail(f'V3 row R{i} Excel行 mismatch: {row[0]}')
        for ci in range(43):
            expect = disp(*s8.get((i, ci + 1), (None, None)))
            if row[ci + 1] != expect:
                bad += 1
                if bad <= 3:
                    print(f'  V3 diff R{i} col{ci + 1}: csv={row[ci + 1]!r} xlsx={expect!r}')
            if '⟦f:' in (row[ci + 1] or ''):
                n_formula_cells += 1
    if bad:
        fail(f'V3 expanded csv: {bad} cell mismatches')
    if n_formula_cells != 27:
        fail(f'V3 formula cells in csv {n_formula_cells} != 27')
    print(f'V3 PASS — 07-expanded-matrix.csv: {N_EXP} rows x 43 cols, cell-by-cell equal '
          f'(27 master-formula cells carried as ⟦f:…⟧)')

    # V4: md 覆盖
    md_map = [  # (md 文件, sheet 名, 覆盖模式)
        ('00-overview.md', '0.说明与总览', 'raw'),
        ('01-units-and-research.md', '1.单元与现有研究', 'escape'),
        ('02-lsu-params-baseline.md', '2.LSU参数基线', 'escape'),
        ('03-design-matrix.md', '3.位置x模型矩阵', 'escape'),
        ('04-observation-points.md', '4.观测点定义', 'escape'),
        ('05-frequency-and-sampling.md', '5.频率与统计', 'escape'),
        ('06-workloads.md', '6.负载清单', 'escape'),
        ('07-expanded-matrix.md', '7.展开执行矩阵', 'header-only'),
        ('08-references.md', '8.文献与来源', 'escape'),
    ]
    for fname, sheet, mode in md_map:
        content = (HERE / fname).read_text(encoding='utf-8')
        if mode == 'header-only':
            missing = [disp(*v) for v in (s8.get((1, ci), (None, None)) for ci in range(1, 44))
                       if v and disp(*v) and md_escape(disp(*v)) not in content]
            # 重新写清楚：检查 43 个表头列名
            missing = []
            for ci in range(1, 44):
                val = s8.get((1, ci), (None, None))[0]
                if val and md_escape(val) not in content:
                    missing.append(val)
        else:
            missing = []
            for (rn, ci), vf in sorted(g[sheet].items()):
                text = disp(*vf)
                if not text:
                    continue
                needle = text if mode == 'raw' else md_escape(text)
                if needle not in content:
                    missing.append(f'R{rn}C{ci}:{text[:40]}')
        if missing:
            fail(f'V4 {fname}: {len(missing)} cells not covered, e.g. {missing[:3]}')
        ncells = len(g[sheet])
        if mode == 'header-only':
            print(f'V4 PASS — {fname} covers the 43 header column names of "{sheet}" '
                  f'(全量 {ncells} cells 由 V3 的 CSV 逐格回比覆盖)')
        else:
            print(f'V4 PASS — {fname} covers all {ncells} non-empty cells of "{sheet}"')

    # V5: README 锚点
    sha = hashlib.sha256(XLSX.read_bytes()).hexdigest()
    readme = (HERE / 'README.md').read_text(encoding='utf-8')
    if sha not in readme:
        fail('V5 README missing sha256')
    if '22 / 56 / 136 / 910 / 42 / 108 / 90 / 5595 / 72（合计 7,031）' not in readme:
        fail('V5 README missing cell-count line')
    print('V5 PASS — README carries sha256 + cell-count anchors')

    print('\nALL PASSED')


if __name__ == '__main__':
    main()
