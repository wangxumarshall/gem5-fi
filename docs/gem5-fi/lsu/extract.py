#!/usr/bin/env python3
"""docs/gem5-fi/lsu/ 的忠实层生成器 + 提取正确性交叉校验。

从《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（9 表，Microsoft Excel 生成）生成 V2.0 忠实层：
  00-overview.md             工作表「0.说明与总览」（单列表 R1-R25，逐行忠实）
  01-units-and-research.md   工作表「1.单元与现有研究」（7 单元 × 7 列）
  02-lsu-params-baseline.md  工作表「2.LSU参数基线」（B0 参数 R2-R19 + 合并节标题 R21 + 核验 R22-R29）
  03-design-matrix.md        工作表「3.位置x模型矩阵」64 模型行 × 14 列（按单元分节，全文）
  design-matrix.csv          同上的机读版（模型ID + Excel行 + 14 列）
  04-observation-points.md   工作表「4.观测点定义」（L0-L5 × 6 列）
  05-frequency-and-sampling.md 工作表「5.频率与统计」（F0-F6 + 9 条统计规则两节）
  06-workloads.md            工作表「6.负载清单」（W0-W13 × 6 列）+ 接线状态提取注
  07-expanded-matrix.csv     工作表「7.展开执行矩阵」325 格 × 43 列全量（+Excel行 管理列）
  07-expanded-matrix.md      展开矩阵的列文档 + 分布汇总 + 每模型格数
  08-references.md           工作表「8.文献与来源」（11 条 × 6 列）
  README.md                  导航 + 提取方法 + 断言结果（引用真实运行输出）+ sha256
                             + 诚实性注记 + 与仓库源码的映射（2026-09-29 核实）

交叉校验（提取正确性不靠"看起来对"；任一失败即非零退出、不生成"通过"结论）：
  1) 9 表表名与顺序（含 "2.LSU参数基线"）；
  2) 设计矩阵 64 行 × 14 列 + 七单元行数 8/9/12/4/14/8/9 + 模型 ID 精确序列
     （A01-A08 / T01,T10,T02-T08 / S01-S11,S13 / L01-L04 / C01-C12,C14,C15 / O01-O07,O09 / P01-P09；
      注意 T10 插在 T01 后、S12/C13/O08 缺号）；
  3) 子模型维合计 178（列「故障表现形式/子模型」按 <模型ID>-<字母> 计数，每模型 1-4 个）；
  4) 展开矩阵 325 行 × 43 列；RunID 325/325 唯一且 == 模型ID-频率-负载ID(W#)；
  5) 展开重放（多重集）：设计矩阵「适用频率 × 适用负载」与 sheet8 逐行多重集全等（顺序不等，
     见诚实性注记 (b)：sheet3 把追加模型并入各单元块、sheet8 保留原展开序置尾）；
  6) 跨表一致性：sheet8 负载列以表6 名称开头 325/325；J 列 == I列 + '\n执行定义与 oracle：'
     + 表6 D列 精确成立 313/325，其余 12 行（全部 SPEC CPU2017）为改写 oracle 文本（注记 (d)）；
     频率定义 312/325 与表5 全等，其余 13 行（L02/L03/L04/C15/P09 的 F6 行）为另一版 F6 定义（注记 (c)）；
  7) 结果列无值；记录状态 325/325 = 待执行；
  8) 公式机制：母公式 27 格（行 2/66/130/194/258 × X/Y/AL/AM/AN 全 5 列 + 行 322 仅 X/Y），
     无缓存值；原始 XML <f> 共 1649 个全 t="shared"；X/Y 列公式延伸至 R338（数据区 R326 之下
     有 12 行无数据模板行），AL/AM/AN 恰覆盖 325 数据行；
  9) 每表非空单元格数 22/56/136/910/42/108/90/5595/72（合计 7,031）；
 10) 频率/单元/负载分布（14 负载全部接入；F0-F6 全部档位均有使用）；
     每模型格数 == len(适用频率) × len(适用负载)（2-12 格）；
 11) 子模型全展开上界 = Σ(子模型数×格数) = 922（派生值，供 README 诚实性注记 (a)）；
 12) 合并单元格唯一：sheet2 R21 = A21:E21（节标题），其余八表无合并。

工程细节（诚实记录）：V2.0 工作簿由 Microsoft Excel 生成（docProps: Excel 16.0300，
lastModifiedBy Borise Ding，modified 2026-09-28T11:03:46Z）—— 与 OoO V2.0（WPS 生成）不同。
公式单元格无缓存值：母公式以 ⟦f:公式⟧ 记法保留在 CSV 中；t="shared" 共享公式引用（无文本无
缓存值）在 CSV 中呈现为空。解析核心复自经读回校验的全量转储器（zipfile + xml.etree，
纯标准库；本机 pip 403 无 openpyxl）。
输出确定性：无时间戳、无随机数；重跑逐字节复现。
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
XLSX = HERE / 'gem5-fi-LSU单元故障注入方案V2.0.xlsx'
XLSX = XLSX.resolve()

EXPECTED_SHEETS = ['0.说明与总览', '1.单元与现有研究', '2.LSU参数基线', '3.位置x模型矩阵',
                   '4.观测点定义', '5.频率与统计', '6.负载清单', '7.展开执行矩阵', '8.文献与来源']
EXPECTED_CELLS = [22, 56, 136, 910, 42, 108, 90, 5595, 72]  # 每表非空单元格数（合计 7031）

SHEET4_COLS = ['模型ID', '单元', '注入位置（结构与正常作用）', '故障类型',
               '故障模型（实施步骤与激活口径）', '故障表现形式/子模型', '适用频率',
               '适用负载（真实名称）', '事件触发条件', '传播链重点观测',
               '预期结果（待验证假设）', '设计理由', '文献依据/直接性', '保护机制归属']
SHEET8_COLS = ['RunID', '模型ID', '单元', '注入位置（结构与正常作用）', '故障类型',
               '故障模型（实施步骤与激活口径）', '频率', '频率定义', '负载（真实名称）',
               '负载定义/oracle', '触发条件', '传播监控', '预期结果', '设计理由', '文献依据',
               'Seed/注入索引', 'Attempted', 'Activated', 'Masked', 'Detected-contained',
               'Data Corruption', 'Crash', 'Timeout', 'SDC率(可分析activated)', '激活率',
               '记录状态', '实测备注', 'SDC', 'Hardware RAS首检（互斥）', 'OS首检（互斥）',
               'Application首检（互斥）', 'None首检（互斥）', 'Contained',
               'Detected-uncontained', 'RAS-silent Crash', 'RAS-silent Timeout',
               '检测/告警证据', '硬件RAS检测率(任意时点)', '检测计数差额（应为0）',
               '结局计数差额（应为0）', 'Hardware RAS检测（任意时点）', 'Simulator failure',
               '故障表现形式/子模型']

EXPECTED_UNITS = ['AGU', 'L1d-TLB', 'Store Queue', 'Load Queue',
                  'L1d-Cache', '原子与同步', '数据预取器']
EXPECTED_UNIT_MODEL_COUNTS = [8, 9, 12, 4, 14, 8, 9]
EXPECTED_UNIT_CELLS = {'AGU': 39, 'L1d-TLB': 39, 'Store Queue': 63, 'Load Queue': 30,
                       'L1d-Cache': 73, '原子与同步': 28, '数据预取器': 53}
EXPECTED_FREQ_CELLS = {'F0': 105, 'F1': 24, 'F2': 77, 'F3': 4, 'F4': 26, 'F5': 25, 'F6': 64}
# 64 个模型 ID 的精确序列（源表自带顺序：T10 插在 T01 后；S12/C13/O08 缺号）
EXPECTED_IDS = (['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08']
                + ['T01', 'T10', 'T02', 'T03', 'T04', 'T05', 'T06', 'T07', 'T08']
                + ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10', 'S11', 'S13']
                + ['L01', 'L02', 'L03', 'L04']
                + ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 'C12',
                   'C14', 'C15']
                + ['O01', 'O02', 'O03', 'O04', 'O05', 'O06', 'O07', 'O09']
                + ['P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P09'])
# 13 行 F6 频率定义与表5 不一致（模型 → 行数）
EXPECTED_F6_MISMATCH = {'L02': 2, 'L03': 2, 'L04': 3, 'C15': 3, 'P09': 3}
F6_ALT_DEF = '首次出现指定事件时注入一次；仍以故障值被下游消费作为 activated 判据'
# 12 行 SPEC CPU2017 的 J 列为改写 oracle 文本（≠ 表6 D 列）
SPEC_ALT_ORACLE = 'mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/checkpoint；使用参考输出或结果哈希'
N_SPEC_ROWS = 12

FORMULA_MARK = '⟦f:'
# sheet8 结果/管理区（0-based 列号）：值槽必须全空；公式列；Z 记录状态
VALUE_SLOT_COLS = [15, 16, 17, 18, 19, 20, 21, 22, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 40, 41]
FORMULA_COLS = [23, 24, 37, 38, 39]           # X/Y/AL/AM/AN
STATUS_COL = 25                                # Z 记录状态
FORMULA_ROWS_MAIN = [2, 66, 130, 194, 258]     # Excel 行（全 5 列母公式）
FORMULA_ROWS_XY = [322]                        # 仅 X/Y 有母公式
SUBMODEL_BOUND = 922                           # Σ(子模型数 × 每模型格数)，派生值
# 公式普查期望（原始 XML，逐列）
EXPECT_F_TOTAL = 1649
EXPECT_F_PERCOL = {'X': 337, 'Y': 337, 'AL': 325, 'AM': 325, 'AN': 325}
EXPECT_F_MAXROW = 338                          # X/Y 模板行延伸至 R338（数据区止于 R326）


# ---------------- xlsx 解析核心（复自经读回校验的全量转储器，纯标准库） ----------------

def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def num_to_col(n: int) -> str:
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


REF_RE = re.compile(r'([A-Z]+)(\d+)')


def split_ref(ref: str):
    m = REF_RE.match(ref)
    return int(m.group(2)), col_to_num(m.group(1))


def load_shared_strings(zf, names):
    sst = []
    if 'xl/sharedStrings.xml' not in names:
        return sst
    root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
    for si in root.findall(f'{NS_MAIN}si'):
        sst.append(''.join(t.text or '' for t in si.iter(f'{NS_MAIN}t')))
    return sst


def cell_text(c, sst):
    """解析一个 <c>，返回 (value_or_None, formula_or_None)。"""
    t = c.get('t')
    v = c.find(f'{NS_MAIN}v')
    f = c.find(f'{NS_MAIN}f')
    formula = f.text if f is not None else None
    val = None
    if t == 's' and v is not None:
        val = sst[int(v.text)]
    elif t == 'inlineStr':
        is_ = c.find(f'{NS_MAIN}is')
        if is_ is not None:
            val = ''.join(x.text or '' for x in is_.iter(f'{NS_MAIN}t'))
    elif t == 'b' and v is not None:
        val = 'TRUE' if v.text.strip() not in ('0', '') else 'FALSE'
    elif v is not None and v.text is not None:
        val = v.text  # n / str / e / 无类型数字：原样
    return val, formula


def parse_sheet(zf, target, sst):
    """→ grid{(row,col): (value, formula)}, maxrow, maxcol, merges。
    与经读回校验的转储器同口径：val 与 formula 皆空的单元格不入 grid。"""
    root = ET.fromstring(zf.read(target))
    grid = {}
    maxrow = maxcol = 0
    sd = root.find(f'{NS_MAIN}sheetData')
    if sd is not None:
        for row in sd.findall(f'{NS_MAIN}row'):
            for c in row.findall(f'{NS_MAIN}c'):
                val, formula = cell_text(c, sst)
                if not (val or formula):
                    continue
                rn, ci = split_ref(c.get('r'))
                grid[(rn, ci)] = (val, formula)
                maxrow = max(maxrow, rn)
                maxcol = max(maxcol, ci)
    merges = []
    mc = root.find(f'{NS_MAIN}mergeCells')
    if mc is not None:
        merges = [m.get('ref') for m in mc.findall(f'{NS_MAIN}mergeCell')]
    return grid, maxrow, maxcol, merges


def sheet_targets(zf):
    """按 workbook.xml 表序返回 [(name, state, 包内路径)]。
    兼容 WPS 包绝对路径 '/xl/...' 与 Excel 相对 'worksheets/...' 两种 rels 写法。"""
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    out = []
    for sh in wb.iter(f'{NS_MAIN}sheet'):
        name = sh.get('name') or ''
        state = sh.get('state') or 'visible'
        target = relmap.get(sh.get(f'{NS_REL}id'))
        assert target, f'sheet {name!r} has no rel target'
        if target.startswith('/'):
            t = target.lstrip('/')
        elif target.startswith('xl/'):
            t = target
        else:
            t = 'xl/' + target.lstrip('/')
        out.append((name, state, t))
    return out


def disp(val, formula):
    """单元格 → 展示文本；公式记法：值⟦f:公式⟧（V2.0 公式均无缓存值）。"""
    text = val or ''
    if formula is not None:
        text = (text + FORMULA_MARK + formula + '⟧') if text else (FORMULA_MARK + formula + '⟧')
    return text


def rows_from_grid(grid, ncols, r_from, r_to):
    """→ [(excel_row, [(val,formula)] * ncols)]，空单元格为 ('', None)。"""
    out = []
    for rn in range(r_from, r_to + 1):
        out.append((rn, [grid.get((rn, ci), ('', None)) for ci in range(1, ncols + 1)]))
    return out


def md_escape(s: str) -> str:
    return s.replace('|', '\\|').replace('\r', '').replace('\n', '<br>')


def freq_list(freq_raw: str):
    """适用频率 'F0 / F1 / F2' → ['F0','F1','F2']。"""
    return [p.strip() for p in freq_raw.split('/') if p.strip()]


def workload_list(load_raw: str):
    """适用负载（真实名称）按换行拆分。"""
    return [p.strip() for p in load_raw.split('\n') if p.strip()]


def submodel_letters(mid: str, text: str):
    """列「故障表现形式/子模型」→ 该模型的子模型字母序列（带边界，防 C01 误配等）。"""
    pat = r'(?<![A-Za-z0-9])' + re.escape(mid) + r'-([a-z])(?![a-z])'
    seen = []
    for m in re.findall(pat, text):
        if m not in seen:
            seen.append(m)
    return sorted(seen)


# ---------------- 主流程 ----------------

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    zf = zipfile.ZipFile(XLSX)
    names = zf.namelist()
    sst = load_shared_strings(zf, names)
    targets = sheet_targets(zf)

    report = []
    ok = True

    def check(tag, cond, detail=''):
        nonlocal ok
        ok &= bool(cond)
        report.append(f'[{tag}] {"PASS" if cond else "FAIL"}' + (f' — {detail}' if detail else ''))
        return bool(cond)

    sha = hashlib.sha256(XLSX.read_bytes()).hexdigest()
    report.append(f'[source] {XLSX.name} sha256={sha}')

    # ---- 断言 1：表数与表名 ----
    sheet_names = [n for n, _, _ in targets]
    check('sheets', len(targets) == 9 and sheet_names == EXPECTED_SHEETS,
          f'{len(targets)} sheets: ' + ' / '.join(sheet_names))

    grids = {}
    for name, state, target in targets:
        grids[name] = parse_sheet(zf, target, sst)

    # ---- 断言 9（提前算好，供 README）：每表非空单元格数 ----
    cell_counts = [len(grids[n][0]) for n, _, _ in targets]
    check('cell-counts', cell_counts == EXPECTED_CELLS,
          'non-empty cells per sheet: ' + '/'.join(str(c) for c in cell_counts)
          + f' (total {sum(cell_counts)})')

    # ---- 断言 12：合并单元格（sheet2 唯一 A21:E21） ----
    merges_all = {n: grids[n][3] for n, _, _ in targets}
    check('merges', merges_all['2.LSU参数基线'] == ['A21:E21']
          and all(v == [] for k, v in merges_all.items() if k != '2.LSU参数基线'),
          'mergeCells: sheet2 = [A21:E21] (R21 节标题), 其余 8 表均无合并单元格')

    g1 = grids['0.说明与总览'][0]
    g2 = grids['1.单元与现有研究'][0]
    g3 = grids['2.LSU参数基线'][0]
    g4, s4maxrow, s4maxcol, _ = grids['3.位置x模型矩阵']
    g5 = grids['4.观测点定义'][0]
    g6, s6maxrow, _, _ = grids['5.频率与统计']
    g7 = grids['6.负载清单'][0]
    g8, s8maxrow, s8maxcol, _ = grids['7.展开执行矩阵']
    g9 = grids['8.文献与来源'][0]

    # ---- 设计矩阵（sheet4）：64 行 × 14 列 ----
    hdr4 = [disp(*g4.get((1, ci), ('', None))) for ci in range(1, 15)]
    check('design-header', hdr4 == SHEET4_COLS, 'sheet4 R1 = 14 expected column names')
    design = rows_from_grid(g4, 14, 2, 65)
    check('design-rows', len(design) == 64 and s4maxrow == 65 and s4maxcol == 14
          and all(any(v for v, _ in vals) for _, vals in design),
          'sheet4 R2-R65 = 64 non-empty design rows x 14 cols')

    units = []
    for _, vals in design:
        u = vals[1][0]
        if u not in units:
            units.append(u)
    unit_counts = {u: sum(1 for _, v in design if v[1][0] == u) for u in units}
    check('design-units', units == EXPECTED_UNITS
          and [unit_counts[u] for u in units] == EXPECTED_UNIT_MODEL_COUNTS,
          ', '.join(f'{u}={unit_counts[u]}' for u in units) + ' (sum 64)')

    model_ids = [v[0][0] for _, v in design]
    check('design-ids', model_ids == EXPECTED_IDS,
          'model IDs == A01-A08 / T01,T10,T02-T08 / S01-S11,S13 / L01-L04 / C01-C12,C14,C15 / '
          'O01-O07,O09 / P01-P09 in source order (T10 after T01; no S12/C13/O08)')

    # ---- 子模型维：178 ----
    subs_of = {}
    for _, v in design:
        mid = v[0][0]
        subs_of[mid] = submodel_letters(mid, v[5][0])
    total_subs = sum(len(s) for s in subs_of.values())
    check('submodels', total_subs == 178,
          f'total sub-model entries = {total_subs} '
          f'(per-model {min(len(s) for s in subs_of.values())}-'
          f'{max(len(s) for s in subs_of.values())})')

    # ---- 展开矩阵（sheet8）：325 行 × 43 列 ----
    hdr8 = [disp(*g8.get((1, ci), ('', None))) for ci in range(1, 44)]
    check('expanded-header', hdr8 == SHEET8_COLS, 'sheet8 R1 = 43 expected column names')
    expanded = rows_from_grid(g8, 43, 2, 326)
    check('expanded-rows', len(expanded) == 325 and s8maxrow == 326 and s8maxcol == 43
          and all(any(v for v, _ in vals) for _, vals in expanded),
          'sheet8 R2-R326 = 325 non-empty rows x 43 cols')

    # ---- RunID 唯一性 + W# 可解析 + 负载列前缀 ----
    runids = [v[0][0] for _, v in expanded]
    dup = sorted({r for r in runids if runids.count(r) > 1})
    wmap = {}
    for rn in range(2, 16):
        wid = disp(*g7.get((rn, 1), ('', None)))
        wmap[wid] = [disp(*g7.get((rn, ci), ('', None))) for ci in range(1, 7)]
    bad_resolv = [(_, v[0][0]) for _, v in expanded if v[0][0].split('-')[2] not in wmap]
    bad_prefix = [(rn, v[0][0]) for rn, v in expanded
                  if not v[8][0].startswith(wmap[v[0][0].split('-')[2]][1])]
    check('runid', len(set(runids)) == 325 and not dup and not bad_resolv and not bad_prefix,
          f'unique {len(set(runids))}/325; RunID == 模型ID-频率-负载ID(W#) for all rows; '
          f'sheet8 负载列以表6 名称开头 325/325'
          + (f'; dups={dup}' if dup else '')
          + (f'; bad_prefix={bad_prefix[:3]}' if bad_prefix else ''))

    # ---- 断言 5：展开重放（多重集；顺序差异见诚实性注记 (b)） ----
    replay = []
    for rn, v in design:
        for f in freq_list(v[6][0]):
            for w in workload_list(v[7][0]):
                replay.append((v[0][0], f, w))
    actual = [(v[1][0], v[6][0], v[8][0]) for _, v in expanded]
    order_eq = replay == actual
    check('replay', sorted(replay) == sorted(actual),
          f'design 适用频率x适用负载 replay == sheet8 (模型ID,频率,负载名) as MULTISET '
          f'{len(replay)}/{len(actual)} rows (order differs: {not order_eq} — sheet3 追加模型'
          f'并入单元块、sheet8 保留原展开序置尾，见 README 注记 (b))')

    # ---- 断言 6a：频率定义（312 全等 + 13 行 F6 另版定义） ----
    fmap = {disp(*g6.get((rn, 1), ('', None))): disp(*g6.get((rn, 3), ('', None)))
            for rn in range(2, 9)}
    bad_h = [(rn, v[1][0], v[6][0], v[7][0]) for rn, v in expanded if v[7][0] != fmap.get(v[6][0])]
    mismatch_models = {}
    alt_text_ok = True
    for rn, mid, f, alt in bad_h:
        mismatch_models[mid] = mismatch_models.get(mid, 0) + 1
        if f != 'F6' or alt != F6_ALT_DEF:
            alt_text_ok = False
    check('cross-freq', len(bad_h) == 13 and mismatch_models == EXPECTED_F6_MISMATCH and alt_text_ok
          and set(fmap) == {'F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'},
          f'sheet8 频率定义 vs sheet6 定义: {len(bad_h)} mismatches / 325 — exactly the F6 rows of '
          f'L02/L03/L04/C15/P09 ({sum(EXPECTED_F6_MISMATCH.values())} rows) carrying an alternative '
          f'F6 definition text (README 注记 (c)); other 312 rows exact')

    # ---- 断言 6b：负载定义/oracle（313 全等 + 12 行 SPEC 改写） ----
    bad_j_spec = []
    bad_j_other = []
    for rn, v in expanded:
        wid = v[0][0].split('-')[2]
        expect_j = v[8][0] + '\n执行定义与 oracle：' + wmap[wid][3]
        if v[9][0] != expect_j:
            if wmap[wid][1] == 'SPEC CPU2017 采样区间':
                if v[9][0] == v[8][0] + '\n执行定义与 oracle：' + SPEC_ALT_ORACLE:
                    bad_j_spec.append(rn)
                else:
                    bad_j_other.append(rn)
            else:
                bad_j_other.append(rn)
    check('cross-loaddef', not bad_j_other and len(bad_j_spec) == N_SPEC_ROWS,
          f'sheet8 负载定义/oracle == I列 + 换行 + 表6 D列: {325 - len(bad_j_spec) - len(bad_j_other)}'
          f'/325 exact; other {len(bad_j_spec)} rows = SPEC CPU2017 (W11) with rewritten oracle text '
          f'(README 注记 (d))')

    # ---- 断言 7：结果槽全空 + 记录状态 ----
    nonempty_slots = [(rn, ci) for rn, v in expanded for ci in VALUE_SLOT_COLS if v[ci][0] or v[ci][1]]
    status_vals = {v[STATUS_COL][0] for _, v in expanded}
    check('result-slots', not nonempty_slots and status_vals == {'待执行'},
          f'value slots P..AP (excl. Z) all empty in 325 rows; 记录状态(Z)=待执行 '
          f'{sum(1 for _, v in expanded if v[STATUS_COL][0] == "待执行")}/325'
          + (f'; nonempty={nonempty_slots[:5]}' if nonempty_slots else ''))

    # ---- 断言 8：公式格（27 母格：5 行全列 + R322 仅 X/Y；无缓存值） ----
    fcells = sorted((rn, ci) for rn, v in expanded for ci in range(43) if v[ci][1] is not None)
    fcells_val = [(rn, ci) for rn, v in expanded for ci in FORMULA_COLS if v[ci][0]]
    expect_fcells = sorted([(rn, ci) for rn in FORMULA_ROWS_MAIN for ci in FORMULA_COLS]
                           + [(rn, ci) for rn in FORMULA_ROWS_XY for ci in (23, 24)])
    check('formulas', fcells == expect_fcells and not fcells_val,
          f'{len(fcells)} master formula cells (with text) exactly at Excel rows '
          f'{FORMULA_ROWS_MAIN} x cols X/Y/AL/AM/AN + row {FORMULA_ROWS_XY} x cols X/Y, '
          f'no cached values')

    # 共享公式普查（逐列直数原始 XML；无文本的 <f t="shared"/> 不入 grid）
    root8 = ET.fromstring(zf.read('xl/worksheets/sheet8.xml'))
    percol = {}
    f_rows = set()
    n_f = n_text = n_cached = 0
    for row in root8.iter(f'{NS_MAIN}row'):
        for c in row.findall(f'{NS_MAIN}c'):
            f = c.find(f'{NS_MAIN}f')
            if f is not None:
                ref = c.get('r')
                col = ''.join(ch for ch in ref if ch.isalpha())
                percol[col] = percol.get(col, 0) + 1
                f_rows.add(int(''.join(ch for ch in ref if ch.isdigit())))
                n_f += 1
                if f.text:
                    n_text += 1
                v_el = c.find(f'{NS_MAIN}v')
                if v_el is not None and (v_el.text or '').strip():
                    n_cached += 1
    check('formulas-shared',
          n_f == EXPECT_F_TOTAL and percol == EXPECT_F_PERCOL and n_text == 27 and n_cached == 0
          and max(f_rows) == EXPECT_F_MAXROW,
          f'total <f> elements = {n_f} (all t="shared"); with text = {n_text}, non-empty cached <v> '
          f'= {n_cached} (Excel 写法：每个公式格带自闭合空 <v/> 占位，无缓存值文本); '
          f'per column {percol}; formula rows span 2-{max(f_rows)} — X/Y shared formulas extend to '
          f'R{max(f_rows)} ({max(f_rows) - 326} template rows below the 325 data rows, no data there), '
          f'AL/AM/AN exactly cover the data rows')

    # ---- 断言 10：分布 ----
    def tally(items):
        t = {}
        for it in items:
            t[it] = t.get(it, 0) + 1
        return t

    freq_cells = tally(v[6][0] for _, v in expanded)
    check('dist-freq', all(freq_cells.get(k, 0) == n for k, n in EXPECTED_FREQ_CELLS.items())
          and sum(freq_cells.values()) == 325,
          ', '.join(f'{k}={freq_cells.get(k, 0)}' for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'])
          + ' (sum 325; 全部 7 档均被使用，F3 仅 4 格)')
    unit_cells = tally(v[2][0] for _, v in expanded)
    check('dist-unit', unit_cells == EXPECTED_UNIT_CELLS,
          ', '.join(f'{u}={unit_cells[u]}' for u in EXPECTED_UNITS) + ' (sum 325)')
    wl_cells = tally(v[8][0] for _, v in expanded)
    wid_cells = tally(v[0][0].split('-')[2] for _, v in expanded)
    check('dist-load', len(wl_cells) == 14 and sum(wid_cells.values()) == 325,
          f'{len(wl_cells)}/14 workloads wired (all defined workloads used); cells per W id: '
          + ', '.join(f'{k}={v}' for k, v in sorted(wid_cells.items())))

    model_cells = tally(v[1][0] for _, v in expanded)
    permodel_ok = all(model_cells[v[0][0]] == len(freq_list(v[6][0])) * len(workload_list(v[7][0]))
                      for _, v in design)
    cells_dist = tally(model_cells.values())
    check('per-model', permodel_ok and sum(model_cells.values()) == 325,
          f'per-model cells == len(适用频率)xlen(适用负载) for all 64 models; '
          f'cells distribution {dict(sorted(cells_dist.items()))} (range '
          f'{min(model_cells.values())}-{max(model_cells.values())})')

    # ---- 断言 11：子模型全展开上界 922（派生） ----
    bound = sum(len(subs_of[v[0][0]]) * model_cells[v[0][0]] for _, v in design)
    check('submodel-bound', bound == SUBMODEL_BOUND,
          f'full 子模型 expansion bound = Σ(子模型数x格数) = {bound} (derived; sheet8 enumerates 325 '
          f'with submodels as whole-cell text in AQ)')

    # ================= 文件生成（全部由本脚本生成，勿手改） =================

    src_note = ('> 来源：《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（Microsoft Excel 生成，9 表），'
                '逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。\n'
                '> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；'
                '断言结果与诚实性注记见 `README.md`。')

    # ---- 00-overview.md（sheet1，单列表 R1-R25） ----
    def s1(rn):
        return disp(*g1.get((rn, 1), ('', None)))

    md = []
    md.append('# 00 · 总览（V2.0：范围 / 基线 / 工作簿结构 / 统计与判定边界 / 完善版增量）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('## R1 · 标题')
    md.append('')
    md.append(s1(1))
    md.append('')
    md.append('## R3–R5 · 范围与基线')
    md.append('')
    for rn in range(3, 6):
        md.append(f'- **R{rn}** {s1(rn)}')
    md.append('')
    md.append('## R7–R15 · 工作簿结构')
    md.append('')
    md.append(f'（R7 为原表节标题：「{s1(7)}」）')
    md.append('')
    for rn in range(8, 16):
        md.append(f'- **R{rn}** {s1(rn)}')
    md.append('')
    md.append('## R17–R23 · 统计与判定边界')
    md.append('')
    md.append(f'（R17 为原表节标题：「{s1(17)}」）')
    md.append('')
    for rn in range(18, 24):
        md.append(f'- **R{rn}** {s1(rn)}')
    md.append('')
    md.append('## R24–R25 · 完善版增量')
    md.append('')
    md.append(f'（R24 为原表节标题：「{s1(24)}」）')
    md.append('')
    md.append(f'- **R25** {s1(25)}')
    md.append('')
    (HERE / '00-overview.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 01-units-and-research.md（sheet2，7 单元） ----
    md = []
    md.append('# 01 · 单元与现有研究（七单元 × 现有研究 / 空白）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「1.单元与现有研究」R2–R8（表头 R1），7 列 × 7 单元。')
    md.append('')
    hdr2 = [disp(*g2.get((1, ci), ('', None))) for ci in range(1, 8)]
    md.append('| ' + ' | '.join(hdr2) + ' |')
    md.append('|' + '---|' * 7)
    for rn in range(2, 9):
        md.append('| ' + ' | '.join(md_escape(disp(*g2.get((rn, ci), ('', None))))
                                      for ci in range(1, 8)) + ' |')
    md.append('')
    (HERE / '01-units-and-research.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 02-lsu-params-baseline.md（sheet3） ----
    md = []
    md.append('# 02 · LSU 参数基线（B0 定值与敏感性 + 逐单元保护机制核验）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「2.LSU参数基线」：R1 表头；R2–R19 B0 参数与敏感性配置（18 行）；'
              'R20 空行；R21 节标题（**合并单元格 A21:E21**）；R22 第二节表头；'
              'R23–R29 逐单元保护机制核验（7 行）。')
    md.append('')
    md.append('## B0 参数与敏感性配置（R2–R19）')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g3.get((1, ci), ('', None))) for ci in range(1, 6)) + ' |')
    md.append('|' + '---|' * 5)
    for rn in range(2, 20):
        md.append('| ' + ' | '.join(md_escape(disp(*g3.get((rn, ci), ('', None))))
                                      for ci in range(1, 6)) + ' |')
    md.append('')
    md.append('## 逐单元保护机制核验（R21–R29）')
    md.append('')
    md.append(f'R21 为合并单元格 **A21:E21** 的节标题：**{disp(*g3.get((21, 1), ("", None)))}**'
              '（值存于 A21，B–E 为合并空区——全簿唯一合并单元格）。')
    md.append('')
    md.append('R22 为第二节表头（原文照录）：')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g3.get((22, ci), ('', None))) for ci in range(1, 6)) + ' |')
    md.append('|' + '---|' * 5)
    md.append('')
    for rn in range(23, 30):
        md.append('| ' + ' | '.join(md_escape(disp(*g3.get((rn, ci), ('', None))))
                                      for ci in range(1, 6)) + ' |')
    md.append('')
    (HERE / '02-lsu-params-baseline.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 03-design-matrix.md（sheet4 全 64 行 × 14 列，按单元分节） ----
    md = []
    md.append('# 03 · 位置×模型设计矩阵（64 个故障模型 × 178 子模型）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「3.位置x模型矩阵」R2–R65，**逐行忠实提取，未做任何改写**。')
    md.append('> 模型 ID（A/T/S/L/C/O/P）为源表自带；`Excel行` 供回溯。')
    md.append('> 14 列列义与源表一致；子模型记法 `<模型ID>-<字母>` 见列「故障表现形式/子模型」；'
              '频率档位定义见 `05-frequency-and-sampling.md`，负载定义见 `06-workloads.md`。')
    md.append('> 〔提取注〕ID 序列为源表原序：**T10 插在 T01 之后**；S12/C13/O08 **缺号**'
              '（源表即无此三行，R25 完善版增量称「原58条模型扩展为64条」）。')
    md.append('')
    md.append('## 索引（扫描用紧凑表）')
    md.append('')
    md.append('| 模型ID | Excel行 | 单元 | 故障类型 | 适用频率 | 适用负载 | 子模型数 |')
    md.append('|---|---|---|---|---|---|---|')
    for rn, v in design:
        md.append(f'| {v[0][0]} | R{rn} | ' + ' | '.join(
            md_escape(v[j][0]) for j in (1, 3, 6, 7)) + f' | {len(subs_of[v[0][0]])} |')
    md.append('')
    for u in units:
        rows_u = [(rn, v) for rn, v in design if v[1][0] == u]
        ids_u = [v[0][0] for _, v in rows_u]
        md.append(f'## {u}（{len(rows_u)} 行：{ids_u[0]}–{ids_u[-1]}）')
        md.append('')
        md.append('| ' + ' | '.join(['模型ID', 'Excel行'] + SHEET4_COLS) + ' |')
        md.append('|' + '---|' * (len(SHEET4_COLS) + 2))
        for rn, v in rows_u:
            md.append(f'| {v[0][0]} | R{rn} | ' + ' | '.join(md_escape(disp(*v[j])) for j in range(14)) + ' |')
        md.append('')
    (HERE / '03-design-matrix.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- design-matrix.csv（模型ID + Excel行 + 14 列） ----
    with open(HERE / 'design-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['模型ID', 'Excel行'] + SHEET4_COLS)
        for rn, v in design:
            w.writerow([v[0][0], f'R{rn}'] + [disp(*v[j]) for j in range(14)])

    # ---- 04-observation-points.md（sheet5，L0-L5） ----
    md = []
    md.append('# 04 · 观测点定义（L0–L5 传播链）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「4.观测点定义」R2–R7（表头 R1），6 列 × 6 层级。')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g5.get((1, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(2, 8):
        md.append('| ' + ' | '.join(md_escape(disp(*g5.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    (HERE / '04-observation-points.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 05-frequency-and-sampling.md（sheet6：F0-F6 + 9 条统计规则） ----
    md = []
    md.append('# 05 · 频率与统计（F0–F6 档位 + 统计规则）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「5.频率与统计」：R1 表头；R2–R8 频率档位（F0–F6）；R9–R10 空行（原表分节）；'
              'R11 第二节表头；R12–R20 统计规则（9 条）。')
    md.append('')
    md.append('## 频率档位（R2–R8）')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g6.get((1, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(2, 9):
        md.append('| ' + ' | '.join(md_escape(disp(*g6.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    md.append('〔提取注〕各档位在「7.展开执行矩阵」325 格中的实际格数：'
              + '、'.join(f'{k}={freq_cells.get(k, 0)}' for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'])
              + '——全部 7 档均被使用（F3 高频压力仅 4 格）。')
    md.append('')
    md.append('## 统计规则（R11 表头；R12–R20）')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g6.get((11, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(12, 21):
        md.append('| ' + ' | '.join(md_escape(disp(*g6.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    (HERE / '05-frequency-and-sampling.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 06-workloads.md（sheet7，W0-W13 + 接线状态提取注） ----
    md = []
    md.append('# 06 · 负载清单（W0–W13）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「6.负载清单」R2–R15（表头 R1），6 列 × 14 负载。')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g7.get((1, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(2, 16):
        md.append('| ' + ' | '.join(md_escape(disp(*g7.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    md.append('## 接线状态〔提取注，派生自「7.展开执行矩阵」〕')
    md.append('')
    md.append(f'- **已接入展开矩阵（14/14 个，全部接入）**：'
              + '；'.join(f'{k}={wid_cells[k]} 格' for k in sorted(wid_cells)) + '。')
    md.append('- **已定义、未接入（0 个）**：与 OoO V2.0（3 个负载未接线）不同，'
              '本簿全部 14 个负载均出现在展开矩阵中。')
    md.append('')
    (HERE / '06-workloads.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 07-expanded-matrix.csv（Excel行 + 43 列全量） ----
    with open(HERE / '07-expanded-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Excel行'] + SHEET8_COLS)
        for rn, v in expanded:
            w.writerow([f'R{rn}'] + [disp(*v[j]) for j in range(43)])

    # ---- 07-expanded-matrix.md（列文档 + 分布 + 每模型格数） ----
    md = []
    md.append('# 07 · 展开执行矩阵（模型×频率×负载，325 个实验格）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「7.展开执行矩阵」R2–R326（表头 R1），43 列 × 325 行，逐行忠实提取。'
              '全量数据在 **`07-expanded-matrix.csv`**（UTF-8 无 BOM；1 个管理列 + 源表 43 列）；'
              '本文件只给列文档与分布汇总。')
    md.append('> 展开规则已由 `extract.py` 交叉校验：从「3.位置x模型矩阵」的 适用频率 × 适用负载'
              ' 重放展开，325 行（模型ID、频率、负载名）与源表**多重集全等**（顺序不同——'
              'sheet3 把 10 个追加模型并入各单元块，sheet8 保留原展开序、追加模型置尾，'
              '见 `README.md` 诚实性注记 (b)）；RunID 325/325 唯一且 == 模型ID-频率-负载ID(W#)。')
    md.append('')
    md.append('## 列文档（CSV 共 44 列 = 1 个管理列 + 源表 43 列）')
    md.append('')
    md.append('| 列 | 名称 | 类别 |')
    md.append('|---|---|---|')
    md.append('| Excel行（管理列） | — | 源工作表行号，供回溯 |')
    for ci in range(1, 44):
        letter = num_to_col(ci)
        name = SHEET8_COLS[ci - 1]
        if ci == 1:
            cls = '键：`模型ID-频率-负载ID(W#)`，325/325 唯一'
        elif ci <= 15:
            cls = '设计展开列（来自「3.位置x模型矩阵」对应行；频率定义/负载定义由 sheet6/sheet7 自带）'
        elif ci == STATUS_COL + 1:
            cls = '**记录状态：325/325 全部为「待执行」**'
        elif ci in [c + 1 for c in FORMULA_COLS]:
            cls = ('公式列（共享公式机制）：母公式 27 格（行 2/66/130/194/258 全 5 列 + 行 322 仅 X/Y）'
                   '+ t="shared" 共享引用 1622 格；X/Y 列公式延伸至 R338（数据区 R326 之下 12 行无数据'
                   '模板行），AL/AM/AN 恰覆盖 325 数据行；无缓存值')
        elif ci == 43:
            cls = '该模型子模型全枚举（整格文本，178 子模型的载体）'
        else:
            cls = '**结果/管理填写槽：源表即空（待执行后录入）**'
        md.append(f'| {letter} | {md_escape(name)} | {cls} |')
    md.append('')
    md.append('结果/管理填写槽明细（源表全空的 22 个值列）：Seed/注入索引、Attempted、Activated、'
              'Masked、Detected-contained、Data Corruption、Crash、Timeout、实测备注、SDC、'
              'Hardware RAS首检、OS首检、Application首检、None首检、Contained、Detected-uncontained、'
              'RAS-silent Crash、RAS-silent Timeout、检测/告警证据、Hardware RAS检测（任意时点）、'
              'Simulator failure。')
    md.append('')
    md.append('## 分布汇总')
    md.append('')
    md.append('### 频率分布（325 格）')
    md.append('')
    md.append('| 频率 | ' + ' | '.join(k for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6']) + ' |')
    md.append('|---|' + '---|' * 7)
    md.append('| 格数 | ' + ' | '.join(str(freq_cells.get(k, 0))
              for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6']) + ' |')
    md.append('')
    md.append('### 单元分布（325 格）')
    md.append('')
    md.append('| 单元 | ' + ' | '.join(EXPECTED_UNITS) + ' |')
    md.append('|---|' + '---|' * 7)
    md.append('| 格数 | ' + ' | '.join(str(unit_cells[u]) for u in EXPECTED_UNITS) + ' |')
    md.append('')
    md.append('### 负载分布（325 格，14 种负载全部接入）')
    md.append('')
    md.append('| 负载ID | ' + ' | '.join(k for k in sorted(wid_cells)) + ' |')
    md.append('|---|' + '---|' * 14)
    md.append('| 格数 | ' + ' | '.join(str(wid_cells[k]) for k in sorted(wid_cells)) + ' |')
    md.append('')
    md.append('### 每模型格数（= 适用频率数 × 适用负载数）')
    md.append('')
    md.append(f'64 个模型的格数为 {min(model_cells.values())}–{max(model_cells.values())}，'
              '分布（格数: 模型数）：'
              + '、'.join(f'{k} 格={v} 个' for k, v in sorted(cells_dist.items())) + '。')
    md.append('')
    (HERE / '07-expanded-matrix.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 08-references.md（sheet9，11 条） ----
    md = []
    md.append('# 08 · 文献与来源（11 条）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「8.文献与来源」R2–R12（表头 R1），6 列 × 11 条。')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g9.get((1, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(2, 13):
        md.append('| ' + ' | '.join(md_escape(disp(*g9.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    (HERE / '08-references.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- README.md（导航 + 方法 + 断言引用 + sha256 + 诚实性注记 + 源码映射） ----
    md = []
    md.append('# gem5-fi LSU 单元故障注入方案 V2.0 —— 忠实提取层（北极星）')
    md.append('')
    md.append('> 本目录是《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（9 表，Microsoft Excel 生成）的忠实提取层，'
              '全部文件由 `extract.py` 确定性生成（勿手改；改表后重跑生成器）。')
    md.append('> 历史：V1.0 工作簿与 V1.0 提取层曾并存于本仓库，2026-09-29 随清库移除'
              '（commit `26cff381`/`3415ae69`，git 历史可查）；本目录是仓库内唯一现行版本。')
    md.append('')
    md.append('## 文件导航')
    md.append('')
    md.append('| 文件 | 来源工作表 | 内容 |')
    md.append('|---|---|---|')
    md.append('| `00-overview.md` | 0.说明与总览 | 范围 / B0 基线 / 工作簿结构 / 统计与判定边界 / 完善版增量（R1–R25 单列表） |')
    md.append('| `01-units-and-research.md` | 1.单元与现有研究 | 七单元 × 现有研究 / 证据直接性 / 研究空白 |')
    md.append('| `02-lsu-params-baseline.md` | 2.LSU参数基线 | B0 参数（R2–R19）+ 敏感性配置 + 逐单元保护机制核验（R21–R29，含全簿唯一合并单元格 A21:E21） |')
    md.append('| `03-design-matrix.md` | 3.位置x模型矩阵 | **64 故障模型 × 14 列全量**（按单元分节；A/T/S/L/C/O/P） |')
    md.append('| `design-matrix.csv` | 3.位置x模型矩阵 | 同上机读版（模型ID + Excel行 + 14 列，64 行） |')
    md.append('| `04-observation-points.md` | 4.观测点定义 | L0–L5 传播链观测点（6 层级 × 6 列） |')
    md.append('| `05-frequency-and-sampling.md` | 5.频率与统计 | F0–F6 档位（eligible-event 归一化）+ 9 条统计规则 |')
    md.append('| `06-workloads.md` | 6.负载清单 | W0–W13（14 负载）+ 接线状态提取注（14/14 全部接入） |')
    md.append('| `07-expanded-matrix.csv` | 7.展开执行矩阵 | **325 实验格 × 43 列全量**（+Excel行 管理列） |')
    md.append('| `07-expanded-matrix.md` | 7.展开执行矩阵 | 列文档 + 频率/单元/负载分布 + 每模型格数 |')
    md.append('| `08-references.md` | 8.文献与来源 | 11 条来源（GEM5-O3/BASE/MMU/SYS、IISWC15、TC22/23、HPCA24、MICRO24/25、CHAOS26） |')
    md.append('')
    md.append('## 提取方法')
    md.append('')
    md.append('- 纯标准库（本机 pip 403 无 openpyxl）：`zipfile` + `xml.etree.ElementTree` 直解'
              ' spreadsheetml XML；解析核心复自经读回校验的全量转储器（sharedStrings / inlineStr /'
              ' str / b / n 全类型覆盖）。')
    md.append('- Excel 生成的工作簿（docProps: Microsoft Excel 16.0300、lastModifiedBy Borise Ding、'
              'modified 2026-09-28T11:03:46Z）；rels 为相对路径（解析器对 WPS 绝对路径写法亦兼容）；'
              'sheet2 R21 有全簿唯一合并单元格 A21:E21。')
    md.append('- XML 行尾规范化（§2.11）：Excel 在单元格内写入的 CRLF（如「适用负载」多行文本）'
              '经 XML 解析规范为 LF——这是一切 XML 一致性解析器（ElementTree/Excel/WPS/openpyxl）'
              '的共同行为；本目录 CSV/md 中此类文本为 LF 分行。')
    md.append('- 母公式格以 `值⟦f:公式⟧` 记法保留（27 格，无缓存值）；其余行的 t="shared" 共享公式引用'
              '（1622 格，无文本无缓存值）在 CSV 中呈现为空，完整机制见断言 formulas-shared 与'
              '诚实性注记 (e)。')
    md.append('- 忠实原则：单元格文字**原文照录**，仅版式/标题/行号标记排版；一切本目录标注以'
              '〔提取注〕显式标记。')
    md.append('- 确定性：无时间戳、无随机数；重跑逐字节复现（sha256 不变）。')
    md.append('')
    md.append('## 断言结果（`python3 extract.py` 真实运行输出，逐字引用）')
    md.append('')
    md.append('```')
    md.extend(report)
    md.append('')
    md.append('EXTRACTION VERIFICATION ' + ('PASSED' if ok else 'FAILED'))
    md.append('```')
    md.append('')
    md.append('## 源文件')
    md.append('')
    md.append(f'- 路径：`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V2.0.xlsx`')
    md.append(f'- sha256：`{sha}`')
    md.append('- 9 表非空单元格：22 / 56 / 136 / 910 / 42 / 108 / 90 / 5595 / 72（合计 7,031）')
    md.append('')
    md.append('## 诚实性注记（HONESTY NOTES）')
    md.append('')
    md.append('(a) **子模型维度未展开**：sheet8 的 325 格按 模型×频率×负载 展开，子模型以整格文本'
              '附在 AQ 列（178 个子模型）。若按子模型全展开应为 **922 格**（派生计算'
              ' Σ(子模型数×格数)，已由本脚本复算核实）。执行时格内按子模型分层记录。')
    md.append('')
    md.append('(b) **双表模型顺序不一致（重放为多重集全等）**：sheet3 设计矩阵把 10 个追加模型'
              '并入各单元块（T10 插在 T01 之后、S13 接 S11、L01–L04 在 SQ 块后、C14/C15 接 C12、'
              'O09 接 O07、P09 殿后）；sheet8 展开矩阵则保留原 54 模型展开序、10 个追加模型'
              '置尾（T10 在 R250–R258 一带）。两序不同但多重集全等（断言 replay）；'
              '本提取对 sheet3/sheet8 各自原序忠实，不重排。')
    md.append('')
    md.append('(c) **13 行 F6 频率定义与表5 不一致**：L02/L03/L04/C15/P09 的 F6 行（共 13 格）在'
              'sheet8 的「频率定义」列为「首次出现指定事件时注入一次；仍以故障值被下游消费作为'
              ' activated 判据」，而表5 F6 定义为「首次出现指定事件时注入一次，如 TLB hit、'
              'SQ forward、dirty eviction、CAS 成功」——语义兼容但文本不同（断言 cross-freq 锁定'
              '该 13 行与文本）。其余 312 行频率定义与表5 逐字全等。')
    md.append('')
    md.append('(d) **12 行 SPEC CPU2017 的负载定义/oracle 为改写文本**：W11（SPEC CPU2017 采样区间）'
              '的 12 格 J 列为「…checkpoint；使用参考输出或结果哈希」，而表6 W11 D 列为'
              '「选择 …checkpoint；不跑全程」——非逐字复制（断言 cross-loaddef 锁定该 12 行）。'
              '其余 313 行 J == I列 + 换行 +「执行定义与 oracle：」+ 表6 D列 精确成立。')
    md.append('')
    md.append('(e) **公式机制与数据区外模板行**：sheet8 的 5 个计算列（X=SDC率(可分析activated) /'
              ' Y=激活率 / AL=硬件RAS检测率(任意时点) / AM=检测计数差额（应为0） / AN=结局计数差额'
              '（应为0））共有 **1649 个公式单元格**，全部 t="shared" 共享公式：27 个母公式文本'
              '在 Excel 行 2/66/130/194/258（全 5 列）与 322（仅 X/Y），其余 1622 格为共享引用；'
              '**0 个非空缓存值**（Excel 写法：每个公式格带自闭合空 `<v/>` 占位——与 WPS 生成的'
              ' OoO V2.0 无 `<v>` 元素的写法不同，但同样无缓存值文本）。逐列：X=337 / Y=337 /'
              ' AL=325 / AM=325 / AN=325——**X/Y 列的共享公式'
              '延伸到 R338**，即数据区（R2–R326）之下有 **12 行无数据的公式模板行**（R327–R338，'
              '复制粘贴残留，无任何数据单元格）；AL/AM/AN 恰好只覆盖 325 个数据行。'
              '公式语义：`SDC率 = SDC/(Activated − Simulator failure)`、`激活率 = Activated/Attempted`、'
              '`检测计数差额 = SUM(首检四类) − (Activated − Simulator failure)`、'
              '`结局计数差额 = SUM(五类结局) + Simulator failure − Activated`（两个差额列应为 0，'
              '自检审计列）。')
    md.append('')
    md.append('(f) **模型 ID 序列特征（源表原样）**：T10 插在 T01 之后；S12/C13/O08 缺号（源表无此'
              '三行）；R25 完善版增量称「原58条模型扩展为64条」。本提取按源表原序忠实照录，'
              '不补号、不重排。')
    md.append('')
    md.append('(g) **全部 325 格 记录状态=待执行**：所有结果槽（22 个值列）在源表中全空——'
              '本目录是纯设计提取，不含任何实验结果数据。')
    md.append('')
    md.append('## 与仓库源码的映射〔提取注，2026-09-29 grep/ls 核实；非源表内容〕')
    md.append('')
    md.append('### 复用（file:line 证据）')
    md.append('')
    md.append('| 方案需要 | 仓库现状 |')
    md.append('|---|---|')
    md.append('| B0 = O3_ARM_v7a_3 + LSU 修正 | `CHAOS/gem5/configs/common/cores/arm/O3_ARM_v7a.py:163-166`'
              ' LQEntries=16 / SQEntries=16 / LSQDepCheckShift=0；`:246-247` StridePrefetcher'
              '(degree=8, latency=1, prefetch_on_access=True)；`configs/se/lsu_proxy.py`（C4-LSU B0 平台）'
              '按 02 表逐参数落地并固化 L2 TLB=1280/5-way |')
    md.append('| 敏感性配置 S1–S4 | `configs/se/lsu_proxy.py:157-159,589-693` `--variant B0/S1/S2/S3/S4`：'
              'S1=DTLB 64（回默认）、S2=64KiB/4-way、S3=LSQDepCheckShift=4、S4=预取器挂 L1D——'
              '与表2 敏感性列逐项对应 |')
    md.append('| LSU SE 平台（挂 16+ 注入器） | `configs/se/lsu_proxy.py:30` 导入 CHAOSReg/PhysReg/Mem/'
              'Cache/LSQFwd/RenameMap/FreeList/ROB/IQ/Exec/FPU/L1DForward/BPU/AddrPath/Decode/ExMon/'
              'RAS/Probe/CommitTrace/MicroSnap/**CHAOSPrefetch** |')
    md.append('| LSU FS 平台（W7 等） | `configs/fs/lsu_b0_fs.py`（经 `arm_chaos_fs.py --lsu_b0` 施加'
              ' B0 增量；W7/M3 计划 Task 4 交付） |')
    md.append('| SQ forwarding / L1D 行 注入（S01–S13 / C01–C15 部分） | `tools/runner.py:1108`'
              ' `elif comp == "lsq_fwd":`；`:1186` `elif comp == "l1d_fwd":`；'
              '`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/`、`CHAOSL1DForward/`、`src/mem/cache/CHAOSCache/` |')
    md.append('| L1d-TLB 注入（T01–T10） | `tools/runner.py:1331` `elif comp == "l1_tlb":`——'
              'Arm TLB 注入器 FS-only、SE-inert（`l1_tlb requires platform`） |')
    md.append('| 预取器注入器（P01–P09） | `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/`'
              '（.cc/.hh/.py 四件套）；`configs/se/lsu_proxy.py:699-713` `--chaos_prefetch` 挂载'
              '（W8 P 系列） |')
    md.append('| F0/F1/F2/F3/F5 触发语义 | `CHAOS/gem5/src/cpu/o3/chaos_trigger.hh:23-26`'
              ' `enum class ChaOSTier { F0, F1, F2, F3, F5 }` |')
    md.append('| 统一分类 / Wilson CI / LSU 工具链 | `tools/classify.py`（runner 与 campaign 共用）；'
              '`tools/wilson.py`；`tools/lsu_campaign.py`、`tools/lsu_l5_classify.py`、'
              '`tools/lsu_meta_analysis.py`、`tools/event_density.py` |')
    md.append('| 定向负载（已建） | `workloads/directed/`：mini_check(W0)、beebs_kernels(W2)、'
              'agu_addrmodes(W3)、sq_forward(W5)、cache_dirtyevict(W6)、atomics_probe(W7)、'
              'prefetch_stride(W8)、gap_bfs(W9)、stream_chase+stream_triad(W10)、'
              'sqlite_like(≈W12)、stuck_persist/spinlock_checksum（F5/原子辅助） |')
    md.append('')
    md.append('### 缺口（如实列出，实施前须补齐）')
    md.append('')
    md.append('| 方案需要 | 缺口 |')
    md.append('|---|---|')
    md.append('| F4（短突发）/ F6（确定性事件触发）触发语义 | `chaos_trigger.hh:23-26` 枚举**仅 F0/F1/F2/F3/F5**；'
              '展开矩阵 F4=26 格、F6=64 格依赖这两档 |')
    md.append('| AGU 注入器（A01–A08） | `tools/runner.py` 组件分派无 `agu`；`src/cpu/o3/` 无 AGU 类'
              ' CHAOS 注入器目录 |')
    md.append('| 原子与同步注入器（O01–O09） | 同上：无 `atomic` 组件分支；且 W7 Atomic-Litmus 依赖'
              '多核 FS——`configs/fs/` 仅单核代理 |')
    md.append('| 预取器接线（P 系列端到端） | `CHAOSPrefetch` 注入器与 `lsu_proxy.py` 挂载旗标已在，但'
              '`tools/runner.py` 无 `prefetch` 组件分派、`schemas/manifest.schema.json` 组件枚举'
              '（21 项）无 `prefetch`——端到端接线缺 runner+schema 两环 |')
    md.append('| LQ 生命周期/响应配对注入器（L01–L04） | `src/cpu/o3/` 仅 `CHAOSLSQFwd`（forwarding 场景），'
              '无 LQ 生命周期/violation-replay/response 配对注入器 |')
    md.append('| manifest schema 组件枚举 | `schemas/manifest.schema.json` **缺 bpu/decode/exmon/ras/'
              'addr_path**（`tools/runner.py:1197-1388` 有分派但校验层未登记） |')
    md.append('| 负载 W1/W4/W11/W13 | `workloads/directed/` 无 MiBench-TC23（W1）、TLB-AliasPerm FS 探针'
              '（W4，FS-only）、SPEC CPU2017（W11，需许可证）、PARSEC-Selected（W13，多核 FS） |')
    md.append('')
    (HERE / 'README.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 控制台报告 ----
    outputs = ['00-overview.md', '01-units-and-research.md', '02-lsu-params-baseline.md',
               '03-design-matrix.md', 'design-matrix.csv', '04-observation-points.md',
               '05-frequency-and-sampling.md', '06-workloads.md', '07-expanded-matrix.csv',
               '07-expanded-matrix.md', '08-references.md', 'README.md']
    report.append(f'[outputs] {len(outputs)} files written under {HERE.name}/: '
                  + ', '.join(outputs))
    print('\n'.join(report))
    if not ok:
        print('\nEXTRACTION VERIFICATION FAILED — do not commit generated files.')
        sys.exit(1)
    print('\nEXTRACTION VERIFICATION PASSED')


if __name__ == '__main__':
    main()
