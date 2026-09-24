#!/usr/bin/env python3
"""LSU 北极星提取的独立校验器 — 不 import extract.py，自己解析 xlsx 再比一遍。

v1（Task 3）：CSV 逐格回比 + 集合断言。
v4a（Task 4）：追加 00/01/02 手写文档片段检查。
v4b（Task 5）：追加 04/05/06/08 手写文档片段检查。
v4c（Task 6）：追加 README 总纲片段检查。
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

    # V4b: 04/05/06/08 片段检查（空白归一化子串）
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
    for path, frags in [('04-observation-points.md', FRAGMENTS_04),
                        ('05-frequency-and-sampling.md', FRAGMENTS_05),
                        ('06-workloads.md', FRAGMENTS_06),
                        ('08-references.md', FRAGMENTS_08)]:
        for label, text in check_fragments(path, frags):
            fail(f'V4: {path} 缺片段 [{label}] {text[:40]}')

    # V4c: README 总纲片段检查（空白归一化子串）
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
    for label, text in check_fragments('README.md', FRAGMENTS_README):
        fail(f'V4: README.md 缺片段 [{label}] {text[:40]}')

    if FAILS:
        for m in FAILS[:20]:
            print('FAIL:', m)
        print(f'VERIFICATION FAILED ({len(FAILS)} issues)')
        sys.exit(1)
    print(f'ALL PASSED (design 68 cells x13, expanded 337 cells x28, sets ok + fragments 00/01/02/04/05/06/08 + README)')


if __name__ == '__main__':
    main()
