#!/usr/bin/env python3
"""docs/gem5-fi/ooo 提取交付物的全量验证（T4）。

V1 生成物回比：design-matrix.csv / 05-expanded-matrix.csv 逐格与 xlsx 解析结果全等。
V2 04-design-matrix.md：91 个位置标签 + 每行「预期结果与依据」首段均出现在 md 中。
V3 手写文档关键原文：从 xlsx 取出关键单元格文本片段，断言逐串出现在对应 md 中。
"""
import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NS_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
HERE = Path(__file__).resolve().parent
XLSX = HERE.parent.parent / 'gem5-fi-OoO单元故障注入方案V1.0.xlsx'


def col_to_num(col):
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def load(zf, names, substr):
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    target = None
    for sh in wb.iter(f'{NS_MAIN}sheet'):
        if substr in (sh.get('name') or ''):
            t = relmap[sh.get(f'{NS_REL}id')]
            target = t if t.startswith('xl/') else 'xl/' + t.lstrip('/')
    sst = []
    if 'xl/sharedStrings.xml' in names:
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS_MAIN}si'):
            sst.append(''.join(t.text or '' for t in si.iter(f'{NS_MAIN}t')))
    root = ET.fromstring(zf.read(target))
    grid = {}
    for row in root.find(f'{NS_MAIN}sheetData').findall(f'{NS_MAIN}row'):
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
            m = re.match(r'([A-Z]+)(\d+)', c.get('r'))
            grid[(int(m.group(2)), col_to_num(m.group(1)))] = val
    return grid


def row(grid, rn, ncols):
    return [grid.get((rn, ci), '') for ci in range(1, ncols + 1)]


zf = zipfile.ZipFile(XLSX)
names = zf.namelist()
g1 = load(zf, names, '位置x模型矩阵')
g5 = load(zf, names, '展开矩阵')
g0 = load(zf, names, '说明与总览')
g2 = load(zf, names, '观测点定义')
g3 = load(zf, names, '频率与时钟换算')
g4 = load(zf, names, '负载清单')

fails = []

# ---- V1a: design-matrix.csv 逐格 ----
with open(HERE / 'design-matrix.csv', newline='', encoding='utf-8') as f:
    rd = list(csv.reader(f))
assert rd[0] == ['ID', 'Excel行'] + row(g1, 1, 13), 'csv header'
n_bad = 0
for i, rec in enumerate(rd[1:], start=1):
    src = row(g1, i + 1, 13)
    if rec[0] != f'D{i:02d}' or rec[1] != f'R{i+1}' or rec[2:] != src:
        n_bad += 1
        if n_bad <= 3:
            fails.append(f'V1a D{i:02d} mismatch')
print(f'V1a design-matrix.csv: {len(rd)-1} rows, cell-exact vs xlsx: {"PASS" if n_bad==0 else f"FAIL({n_bad})"}')

# ---- V1b: 05-expanded-matrix.csv 逐格 ----
with open(HERE / '05-expanded-matrix.csv', newline='', encoding='utf-8') as f:
    rd5 = list(csv.reader(f))
assert rd5[0][3:] == row(g5, 1, 17), 'csv5 header'
n_bad = 0
for i, rec in enumerate(rd5[1:], start=1):
    src = row(g5, i + 1, 17)
    if rec[0] != f'E{i:03d}' or rec[1] != f'R{i+1}' or rec[3:] != src:
        n_bad += 1
        if n_bad <= 3:
            fails.append(f'V1b E{i:03d} mismatch')
print(f'V1b 05-expanded-matrix.csv: {len(rd5)-1} rows, cell-exact vs xlsx: {"PASS" if n_bad==0 else f"FAIL({n_bad})"}')

# ---- V2: 04-design-matrix.md 覆盖 ----
md4 = (HERE / '04-design-matrix.md').read_text(encoding='utf-8')
miss_label = [rn for rn in range(2, 93) if g1[(rn, 2)] not in md4]
miss_text = [rn for rn in range(2, 93)
             if g1[(rn, 11)][:40].replace('\n', '') not in md4.replace('<br>', '')]
print(f'V2 04-design-matrix.md: 91 labels present: {"PASS" if not miss_label else f"FAIL {miss_label}"}; '
      f'91 expectation-text fragments present: {"PASS" if not miss_text else f"FAIL {miss_text}"}')
if miss_label:
    fails.append(f'V2 label {miss_label}')
if miss_text:
    fails.append(f'V2 text {miss_text}')

# ---- V3: 手写文档关键原文逐串（空白归一化后子串匹配） ----
def norm(s):
    return re.sub(r'\s+', '', s)


def frag(s, n=50):
    return norm(s)[:n]


checks = {
    '00-overview.md': (
        ['Int Decode / Int Rename / Int Dispatch-ROB / FP-SIMD Decode / FP-SIMD Rename / FP-SIMD Dispatch-ROB 六个单元',
         '对应工作簿《2.2 全单元对比总表》A11:A16',
         'gem5 ARMv8 O3CPU，参数取自《OoO单元参数总表.md》最终版（NEON+SVE+SME 都打开的那份配置）',
         '时钟按鲲鹏 920 的 2.6 GHz 折算（来源：公开资料，非 TRM 逐型号核实'] +
        [g0[(rn, 1)] for rn in range(17, 22)] +                       # ①-⑤ 全文
        ['每行一个「单元 x 注入位置 x 故障模型」的设计单元，是整份方案的主体',
         '（第 1/2/3/4 点的设计依据都在这张表）',
         '按每行标注的适用频率、适用负载展开']
    ),
    '01-observation-points.md': (
        [g2[(rn, 3)] for rn in range(2, 7)] +                         # L0-L4 定义全文
        ['执行时间错（Execution Time Error）', '首次出现分歧的 commit 序号',
         '借鉴 CHAOS 论文用 HPC 计数器偏差捕捉「未崩溃但已严重偏离」的做法']
    ),
    '02-frequency-and-sampling.md': (
        [g3[(rn, 6)] for rn in range(4, 10)] +                        # F0-F5 设计意图全文
        [g3[(rn, 1)] for rn in (4, 5, 6, 7, 8, 9)] +                  # F0-F5 注入间隔全文
        ['e=2.88%、t=99%', '16,587', '91 行，展开到「5.展开矩阵」后共 226 行',
         '先在无故障基线下测该事件在所选负载里的平均发生频率',
         g3[(15, 3)][:80], g3[(16, 3)][:80]]                          # 两类计数基准含义
    ),
    '03-workloads.md': (
        [g4[(rn, 3)] for rn in range(2, 10)] +                        # 8 负载简介全文
        [g4[(rn, 4)] for rn in range(2, 10)] +                        # 8 校验方式全文
        [g4[(12, 1)]]                                                 # 分配原则全文
    ),
}
for fname, frags in checks.items():
    md = norm((HERE / fname).read_text(encoding='utf-8'))
    missing = [x for x in frags if norm(x) not in md]
    print(f'V3 {fname}: {len(frags)-len(missing)}/{len(frags)} key verbatim fragments present: '
          f'{"PASS" if not missing else "FAIL -> " + str([norm(m)[:50] for m in missing[:3]])}')
    if missing:
        fails.append(f'V3 {fname} missing {len(missing)}')

# ---- V4: README 数字引用与 04 一致性 ----
mdr = (HERE / 'README.md').read_text(encoding='utf-8')
csv5_text = (HERE / '05-expanded-matrix.csv').read_text(encoding='utf-8')
num_checks = [
    ('91', 'D91' in md4 and '91' in mdr),
    ('226', 'E226' in csv5_text and '226' in mdr),
    ('D25=ROB PC 单比特', g1[(26, 2)] in md4),
    ('D32=done位 提前(固定)', g1[(33, 2)] in md4),
    ('D83=FP自检', g1[(84, 2)] in md4),
    ('sha256 in README', '9c8193577b8e6729315c28dc5ee482cabac8250986c06bad017f033574a431ba' in mdr),
]
bad = [k for k, v in num_checks if not v]
print(f'V4 README cross-refs: {"PASS" if not bad else f"FAIL {bad}"}')
if bad:
    fails.append(f'V4 {bad}')

print()
if fails:
    print('OVERALL: FAIL —', fails)
    raise SystemExit(1)
print('OVERALL: ALL VERIFICATION PASSED')
