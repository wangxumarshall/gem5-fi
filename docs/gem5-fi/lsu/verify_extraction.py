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
