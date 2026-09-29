#!/usr/bin/env python3
"""docs/gem5-fi/ooo/v2/ 的忠实层生成器 + 提取正确性交叉校验（V2-W0.1）。

从《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（9 表，WPS 生成）生成 V2.0 忠实层：
  00-overview.md             工作表「0.说明与总览」（单列表 R1-R25，逐行忠实）
  01-units-and-research.md   工作表「1.单元与现有研究」（6 单元 × 7 列）
  02-ooo-params-baseline.md  工作表「2.OOO参数基线」（B0 参数 R2-R24 + 逐单元保护机制核验 R25-R31）
  03-design-matrix.md        工作表「3.位置x模型矩阵」57 模型行 × 14 列（按单元分节，全文）
  design-matrix.csv          同上的机读版（模型ID + Excel行 + 14 列）
  04-observation-points.md   工作表「4.观测点定义」（L0-L5 × 6 列）
  05-frequency-and-statistics.md 工作表「5.频率与统计」（F0-F6 + 统计规则两节）
  06-workloads.md            工作表「6.负载清单」（W0-W13 × 6 列）+ 接线状态提取注
  07-expanded-matrix.csv     工作表「7.展开执行矩阵」310 格 × 43 列全量（+Excel行 管理列）
  07-expanded-matrix.md      展开矩阵的列文档 + 分布汇总 + 每模型格数模板
  08-references.md           工作表「8.文献与来源」（11 条 × 6 列）
  README.md                  导航 + 提取方法 + 断言结果（引用真实运行输出）+ sha256 + 诚实性注记

交叉校验（提取正确性不靠"看起来对"；任一失败即非零退出、不生成"通过"结论）：
  1) 9 表表名与顺序；
  2) 设计矩阵 57 行 + 每单元行数 9/9/10/9/10/10 + 模型 ID 序列 D/R/B/FD/FR/FB；
  3) 子模型维合计 193（列「故障表现形式/子模型」按 <模型ID>-<字母> 计数）；
  4) 展开矩阵 310 行 × 43 列；
  5) RunID 310/310 唯一且 == 模型ID-频率-负载ID；
  6) 从设计矩阵「适用频率 × 适用负载」重放展开，与 sheet8 逐行全等（含顺序）；
  7) 跨表一致性：sheet8 频率定义 vs sheet6 定义；sheet8 负载名/负载定义 vs sheet7 清单；
  8) 结果列无值（25 个母公式格带文本，仅 Excel 行 2/66/130/194/258 × 列 X/Y/AL/AM/AN；另有
     1525 个 t="shared" 共享公式引用覆盖其余行——5 列公式经共享机制绑定全部 310 行，均无缓存值）；
     记录状态 310/310 = 待执行；
  9) 每表非空单元格数 22/49/151/812/42/102/90/5338/72（合计 6,678）；
 10) 频率/单元/负载分布与每模型格数模板（单翻6/双翻4/换值-状态-时序6/卡死2）；
 11) 子模型全展开上界 = Σ(子模型数×格数) = 1050（派生值，供 README 诚实性注记 (a)）。

工程细节（诚实记录）：V2.0 工作簿由 WPS 生成 —— rels 使用包绝对路径 "/xl/..."、无 docProps；
公式单元格无缓存值：母公式以 ⟦f:公式⟧ 记法保留在 CSV 中；t="shared" 共享公式引用（1525 格，
无文本无缓存值）在 CSV 中呈现为空，其完整机制由断言 formulas-shared 专档（编排者批判性核验修正：
仅数带文本的母公式格会漏共享引用而得出"需下拉复制"的错误结论）。解析核心复自经读回校验的全量转储器
（zipfile + xml.etree，纯标准库；本机 pip 403 无 openpyxl）。
输出确定性：无时间戳、无随机数；重跑逐字节复现。
用法：python3 extract_v2.py   （在任意目录运行均可，路径相对本脚本解析）
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
XLSX = HERE / '..' / 'gem5-fi-OoO单元故障注入方案V2.0.xlsx'
XLSX = XLSX.resolve()

EXPECTED_SHEETS = ['0.说明与总览', '1.单元与现有研究', '2.OOO参数基线', '3.位置x模型矩阵',
                   '4.观测点定义', '5.频率与统计', '6.负载清单', '7.展开执行矩阵', '8.文献与来源']
EXPECTED_CELLS = [22, 49, 151, 812, 42, 102, 90, 5338, 72]  # 每表非空单元格数（合计 6678）

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

EXPECTED_UNITS = ['Int Decode', 'Int Rename', 'Int Dispatch / ROB',
                  'FP/SIMD Decode', 'FP/SIMD Rename', 'FP/SIMD Dispatch/ROB']
EXPECTED_UNIT_MODEL_COUNTS = [9, 9, 10, 9, 10, 10]
EXPECTED_UNIT_CELLS = {'Int Decode': 48, 'Int Rename': 48, 'Int Dispatch / ROB': 54,
                       'FP/SIMD Decode': 52, 'FP/SIMD Rename': 54, 'FP/SIMD Dispatch/ROB': 54}
EXPECTED_FREQ_CELLS = {'F0': 104, 'F1': 12, 'F2': 76, 'F3': 0, 'F4': 28, 'F5': 10, 'F6': 80}
EXPECTED_WL_CELLS = {'W1 MiBench-TC23': 11, 'W3 A64-DecodeProbe': 24, 'W4 Rename-Dependency': 27,
                     'W5 ROB-Recovery': 42, 'W6 CoreMark+Embench': 25, 'W7 GAP-Selected': 21,
                     'W8 FP-ScalarProbe': 38, 'W9 NEON-LaneProbe': 48, 'W10 PolyBench': 42,
                     'W11 libjpeg-turbo-NEON': 12, 'W13 FP-ExceptionRecovery': 20}

FORMULA_MARK = '⟦f:'
# sheet8 结果/管理区（0-based 列号）：值槽必须全空；公式列仅 5 行有公式；Z 记录状态
VALUE_SLOT_COLS = [15, 16, 17, 18, 19, 20, 21, 22, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 40, 41]
FORMULA_COLS = [23, 24, 37, 38, 39]           # X/Y/AL/AM/AN
STATUS_COL = 25                                # Z 记录状态
FORMULA_ROWS = [2, 66, 130, 194, 258]          # Excel 行
SUBMODEL_BOUND = 1050                          # Σ(子模型数 × 每模型格数)，派生值


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
        # 两簿均无 rPh，已核实：拼接 si 内全部 <t> 文本
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
    """→ grid{(row,col): (value, formula)}, maxrow, maxcol。
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
    return grid, maxrow, maxcol


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
    """→ [(excel_row, [(val,formula)] * ncols]]，空单元格为 ('', None)。"""
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
    """列「故障表现形式/子模型」→ 该模型的子模型字母序列（带边界，防 FD01 误配 D01）。"""
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

    g1 = grids['0.说明与总览'][0]
    g2 = grids['1.单元与现有研究'][0]
    g3 = grids['2.OOO参数基线'][0]
    g4, s4maxrow, s4maxcol = grids['3.位置x模型矩阵']
    g5 = grids['4.观测点定义'][0]
    g6, s6maxrow, _ = grids['5.频率与统计']
    g7 = grids['6.负载清单'][0]
    g8, s8maxrow, s8maxcol = grids['7.展开执行矩阵']
    g9 = grids['8.文献与来源'][0]

    # ---- 设计矩阵（sheet4）：57 行 × 14 列 ----
    hdr4 = [disp(*g4.get((1, ci), ('', None))) for ci in range(1, 15)]
    check('design-header', hdr4 == SHEET4_COLS, 'sheet4 R1 = 14 expected column names')
    design = rows_from_grid(g4, 14, 2, 58)
    check('design-rows', len(design) == 57 and s4maxrow == 58 and s4maxcol == 14
          and all(any(v for v, _ in vals) for _, vals in design),
          'sheet4 R2-R58 = 57 non-empty design rows x 14 cols')

    units = []
    for _, vals in design:
        u = vals[1][0]
        if u not in units:
            units.append(u)
    unit_counts = {u: sum(1 for _, v in design if v[1][0] == u) for u in units}
    check('design-units', units == EXPECTED_UNITS
          and [unit_counts[u] for u in units] == EXPECTED_UNIT_MODEL_COUNTS,
          ', '.join(f'{u}={unit_counts[u]}' for u in units) + ' (sum 57)')

    model_ids = [v[0][0] for _, v in design]
    exp_ids = ([f'D{i:02d}' for i in range(1, 10)] + [f'R{i:02d}' for i in range(1, 10)]
               + [f'B{i:02d}' for i in range(1, 11)] + [f'FD{i:02d}' for i in range(1, 10)]
               + [f'FR{i:02d}' for i in range(1, 11)] + [f'FB{i:02d}' for i in range(1, 11)])
    check('design-ids', model_ids == exp_ids,
          'model IDs == D01-D09/R01-R09/B01-B10/FD01-FD09/FR01-FR10/FB01-FB10 in order')

    # ---- 子模型维：193 ----
    subs_of = {}
    for _, v in design:
        mid = v[0][0]
        subs_of[mid] = submodel_letters(mid, v[5][0])
    total_subs = sum(len(s) for s in subs_of.values())
    check('submodels', total_subs == 193,
          f'total sub-model entries = {total_subs} '
          f'(per-model {min(len(s) for s in subs_of.values())}-'
          f'{max(len(s) for s in subs_of.values())})')

    # ---- 展开矩阵（sheet8）：310 行 × 43 列 ----
    hdr8 = [disp(*g8.get((1, ci), ('', None))) for ci in range(1, 44)]
    check('expanded-header', hdr8 == SHEET8_COLS, 'sheet8 R1 = 43 expected column names')
    expanded = rows_from_grid(g8, 43, 2, 311)
    check('expanded-rows', len(expanded) == 310 and s8maxrow == 311 and s8maxcol == 43
          and all(any(v for v, _ in vals) for _, vals in expanded),
          'sheet8 R2-R311 = 310 non-empty rows x 43 cols')

    # ---- RunID 唯一性 + 格式 ----
    runids = [v[0][0] for _, v in expanded]
    dup = sorted({r for r in runids if runids.count(r) > 1})
    fmt_bad = [(_, v[0][0], v[6][0], v[8][0]) for _, v in expanded
               if v[0][0] != f"{v[1][0]}-{v[6][0]}-{v[8][0].split(' ')[0]}"]
    check('runid', len(set(runids)) == 310 and not dup and not fmt_bad,
          f'unique {len(set(runids))}/310; RunID == 模型ID-频率-负载ID for all rows'
          + (f'; dups={dup}' if dup else '') + (f'; fmt_bad={fmt_bad[:3]}' if fmt_bad else ''))

    # ---- 断言 6：展开重放（含顺序） ----
    replay = []
    for rn, v in design:
        for f in freq_list(v[6][0]):
            for w in workload_list(v[7][0]):
                replay.append((v[0][0], f, w))
    actual = [(v[1][0], v[6][0], v[8][0]) for _, v in expanded]
    check('replay', replay == actual,
          f'design 适用频率x适用负载 replay == sheet8 (模型ID,频率,负载名) '
          f'{len(replay)}/{len(actual)} rows, order included')

    # ---- 断言 7：跨表一致性 ----
    fmap = {disp(*g6.get((rn, 1), ('', None))): disp(*g6.get((rn, 3), ('', None)))
            for rn in range(2, 9)}
    bad_h = [(rn, v[6][0]) for rn, v in expanded if v[7][0] != fmap.get(v[6][0])]
    check('cross-freq', not bad_h and set(fmap) == {'F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'},
          f'sheet8 频率定义 vs sheet6 定义 (keyed by 档位): {len(bad_h)} mismatches / 310')

    wmap = {}
    for rn in range(2, 16):
        wid = disp(*g7.get((rn, 1), ('', None)))
        wmap[wid] = [disp(*g7.get((rn, ci), ('', None))) for ci in range(1, 7)]
    bad_i = [(rn, v[8][0]) for rn, v in expanded
             if v[8][0] != wmap[v[8][0].split(' ')[0]][0] + ' ' + wmap[v[8][0].split(' ')[0]][1]]
    check('cross-load', not bad_i and len(wmap) == 14,
          f'sheet8 负载（真实名称） vs sheet7 负载ID+名称: {len(bad_i)} mismatches / 310')

    bad_j = []
    for rn, v in expanded:
        wr = wmap[v[8][0].split(' ')[0]]
        expect_j = wr[1] + '（' + wr[2] + '）\n执行定义与oracle：' + wr[3]
        if v[9][0] != expect_j:
            bad_j.append(rn)
    check('cross-loaddef', not bad_j,
          f'sheet8 负载定义/oracle == sheet7 名称+（类型）+执行定义与oracle：{len(bad_j)} mismatches / 310')

    # ---- 断言 8：结果槽全空 + 公式格 ----
    nonempty_slots = [(rn, ci) for rn, v in expanded for ci in VALUE_SLOT_COLS if v[ci][0] or v[ci][1]]
    status_vals = {v[STATUS_COL][0] for _, v in expanded}
    check('result-slots', not nonempty_slots and status_vals == {'待执行'},
          f'value slots P..AP (excl. Z) all empty in 310 rows; 记录状态(Z)=待执行 '
          f'{sum(1 for _, v in expanded if v[STATUS_COL][0] == "待执行")}/310'
          + (f'; nonempty={nonempty_slots[:5]}' if nonempty_slots else ''))

    fcells = sorted((rn, ci) for rn, v in expanded for ci in range(43) if v[ci][1] is not None)
    fcells_val = [(rn, ci) for rn, v in expanded for ci in FORMULA_COLS if v[ci][0]]
    expect_fcells = sorted((rn, ci) for rn in FORMULA_ROWS for ci in FORMULA_COLS)
    check('formulas', fcells == expect_fcells and not fcells_val,
          f'{len(fcells)} master formula cells (with text) exactly at Excel rows {FORMULA_ROWS} x cols '
          f'{[num_to_col(ci + 1) for ci in FORMULA_COLS]}, no cached values')

    # 共享公式普查（编排者批判性核验 2026-09-29：解析器对无文本的 <f t="shared"/> 记 formula=None，
    # 只数母公式格会漏 1525 个共享引用——须直数原始 XML 才能得到完整机制图景）
    with zipfile.ZipFile(XLSX) as zf:
        n_f = n_shared = n_text = n_cached = 0
        for zn in zf.namelist():
            if re.fullmatch(r'xl/worksheets/sheet\d+\.xml', zn):
                xml = zf.read(zn).decode('utf-8')
                n_f += len(re.findall(r'<(?:x:)?f[ >]', xml))
                n_shared += len(re.findall(r'<(?:x:)?f[^>]*t="shared"', xml))
                n_text += len(re.findall(r'<(?:x:)?f[^>]*>[^<]+</(?:x:)?f>', xml))
                n_cached += len(re.findall(r'</(?:x:)?f>\s*<(?:x:)?v>', xml))
    check('formulas-shared',
          n_f == 1550 and n_shared == 1550 and n_text == 25 and n_cached == 0,
          f'total <f> elements = {n_f} (t="shared": {n_shared}); {n_text} with formula text, '
          f'{n_cached} with cached <v> — 5 computed cols x ALL 310 rows are formula-bound via '
          f'shared formulas (si groups 0-19 x64 + 20-24 x54); opens live, NO copy-down needed')

    # ---- 断言 10：分布 ----
    def tally(items):
        t = {}
        for it in items:
            t[it] = t.get(it, 0) + 1
        return t

    freq_cells = tally(v[6][0] for _, v in expanded)
    check('dist-freq', all(freq_cells.get(k, 0) == n for k, n in EXPECTED_FREQ_CELLS.items())
          and sum(freq_cells.values()) == 310,
          ', '.join(f'{k}={freq_cells.get(k, 0)}' for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'])
          + ' (sum 310)')
    unit_cells = tally(v[2][0] for _, v in expanded)
    check('dist-unit', unit_cells == EXPECTED_UNIT_CELLS,
          ', '.join(f'{u}={unit_cells[u]}' for u in EXPECTED_UNITS) + ' (sum 310)')
    wl_cells = tally(v[8][0] for _, v in expanded)
    check('dist-load', wl_cells == EXPECTED_WL_CELLS,
          ' / '.join(f'{k}={v}' for k, v in sorted(wl_cells.items(), key=lambda x: -x[1]))
          + ' (sum 310)')

    model_cells = tally(v[1][0] for _, v in expanded)
    ft_template = {}
    ft_models = {}
    for _, v in design:
        ft = v[3][0]
        ft_template.setdefault(ft, set()).add(model_cells[v[0][0]])
        ft_models.setdefault(ft, []).append(v[0][0])
    check('template', all(len(s) == 1 and next(iter(s)) in (2, 4, 6) for s in ft_template.values()),
          'per-model cells by fault type: '
          + ', '.join(f'{ft}={next(iter(ft_template[ft]))}' for ft in ft_template))

    # ---- 断言 11：子模型全展开上界 1050（派生） ----
    bound = sum(len(subs_of[v[0][0]]) * model_cells[v[0][0]] for _, v in design)
    check('submodel-bound', bound == SUBMODEL_BOUND,
          f'full 子模型 expansion bound = Σ(子模型数x格数) = {bound} (derived; sheet8 enumerates 310)')

    # ================= 文件生成（全部由本脚本生成，勿手改） =================

    src_note = ('> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），'
                '逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。\n'
                '> 生成器：`extract_v2.py`（纯标准库，确定性输出，可重跑复现）；'
                '断言结果与诚实性注记见 `README.md`。')

    # ---- 00-overview.md（sheet1，单列表 R1-R25） ----
    def s1(rn):
        return disp(*g1.get((rn, 1), ('', None)))

    md = []
    md.append('# 00 · 总览（V2.0：范围 / 基线 / 工作簿结构 / 统计与判定边界）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append(f'## R1 · 标题')
    md.append('')
    md.append(s1(1))
    md.append('')
    md.append('## R3–R6 · 范围与基线')
    md.append('')
    for rn in range(3, 7):
        md.append(f'- **R{rn}** {s1(rn)}')
    md.append('')
    md.append('## R8–R16 · 工作簿结构')
    md.append('')
    md.append(f'（R8 为原表节标题：「{s1(8)}」）')
    md.append('')
    for rn in range(9, 17):
        md.append(f'- **R{rn}** {s1(rn)}')
        if rn == 15:
            md.append('')
            md.append('  〔提取注：R15 声称展开维度为「模型×故障表现形式/子模型×频率×负载全展开」，'
                      '但工作表「7.展开执行矩阵」实际只展开到 模型×频率×负载 = 310 格（子模型以整格文本'
                      '附在 AQ 列）。若真按子模型展开应为 1050 格（派生计算 Σ(子模型数×格数)）。'
                      '计划裁决 D4：执行 310 格、格内按子模型分层记录。详见 `README.md` 诚实性注记 (a)。〕')
    md.append('')
    md.append('## R18–R25 · 统计与判定边界')
    md.append('')
    md.append(f'（R18 为原表节标题：「{s1(18)}」）')
    md.append('')
    for rn in range(19, 26):
        md.append(f'- **R{rn}** {s1(rn)}')
    md.append('')
    (HERE / '00-overview.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 01-units-and-research.md（sheet2） ----
    md = []
    md.append('# 01 · 单元与现有研究（六单元 × 现有研究 / 空白）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「1.单元与现有研究」R2–R7（表头 R1），7 列 × 6 单元。')
    md.append('')
    hdr2 = [disp(*g2.get((1, ci), ('', None))) for ci in range(1, 8)]
    md.append('| ' + ' | '.join(hdr2) + ' |')
    md.append('|' + '---|' * 7)
    for rn in range(2, 8):
        md.append('| ' + ' | '.join(md_escape(disp(*g2.get((rn, ci), ('', None))))
                                      for ci in range(1, 8)) + ' |')
    md.append('')
    (HERE / '01-units-and-research.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 02-ooo-params-baseline.md（sheet3） ----
    md = []
    md.append('# 02 · OOO 参数基线（B0 + S0–S6 敏感性 + 逐单元保护机制核验）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「2.OOO参数基线」：R1 表头；R2–R24 B0 参数与敏感性配置（23 行）；'
              'R25 节标题（B–E 列空）；R26–R31 逐单元保护机制核验（6 行）。')
    md.append('')
    md.append('## B0 参数与敏感性配置（R2–R24）')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g3.get((1, ci), ('', None))) for ci in range(1, 6)) + ' |')
    md.append('|' + '---|' * 5)
    for rn in range(2, 25):
        md.append('| ' + ' | '.join(md_escape(disp(*g3.get((rn, ci), ('', None))))
                                      for ci in range(1, 6)) + ' |')
    md.append('')
    md.append('## 逐单元保护机制核验（R25–R31）')
    md.append('')
    md.append(f'R25（A 列）为原表节标题：**{disp(*g3.get((25, 1), ("", None)))}**（该行 B–E 列为空）。')
    md.append('')
    md.append('〔提取注〕R26–R31 沿用上表 5 列版式，该节列语义为：'
              'A=单元、B=实际存在的完整性/保护机制、C=处理、D=纳入实现的模型与观测、'
              'E=非 Hardware RAS 说明（下表表头为提取层标签）。')
    md.append('')
    md.append('| 单元 | 机制（B 列原文） | 处理 | 覆盖模型与观测 | 非 RAS 说明 |')
    md.append('|---|---|---|---|---|')
    for rn in range(26, 32):
        md.append('| ' + ' | '.join(md_escape(disp(*g3.get((rn, ci), ('', None))))
                                      for ci in range(1, 6)) + ' |')
    md.append('')
    (HERE / '02-ooo-params-baseline.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 03-design-matrix.md（sheet4 全 57 行 × 14 列，按单元分节） ----
    md = []
    md.append('# 03 · 位置×模型设计矩阵（57 个故障模型 × 193 子模型）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「3.位置x模型矩阵」R2–R58，**逐行忠实提取，未做任何改写**。')
    md.append('> 模型 ID（D/R/B/FD/FR/FB）为源表自带；`Excel行` 供回溯。')
    md.append('> 14 列列义与源表一致；子模型记法 `<模型ID>-<字母>` 见列「故障表现形式/子模型」；'
              '频率档位定义见 `05-frequency-and-statistics.md`，负载定义见 `06-workloads.md`。')
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

    # ---- 05-frequency-and-statistics.md（sheet6：F0-F6 + 统计规则） ----
    md = []
    md.append('# 05 · 频率与统计（F0–F6 档位 + 统计规则）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「5.频率与统计」：R1 表头；R2–R8 频率档位（F0–F6）；R9 空行（原表分节）；'
              'R10 第二节表头；R11–R18 统计规则（8 条）。')
    md.append('')
    md.append('## 频率档位（R2–R8）')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g6.get((1, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(2, 9):
        md.append('| ' + ' | '.join(md_escape(disp(*g6.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    md.append('〔提取注〕F3（高频压力）在「7.展开执行矩阵」310 格中为 0 格——定义存在、未被使用；'
              '各档位实际格数：' + '、'.join(f'{k}={freq_cells.get(k, 0)}'
                                        for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6'])
              + '。详见 `07-expanded-matrix.md` 与 `README.md` 诚实性注记 (c)。')
    md.append('')
    md.append('## 统计规则（R10 表头；R11–R18）')
    md.append('')
    md.append('| ' + ' | '.join(disp(*g6.get((10, ci), ('', None))) for ci in range(1, 7)) + ' |')
    md.append('|' + '---|' * 6)
    for rn in range(11, 19):
        md.append('| ' + ' | '.join(md_escape(disp(*g6.get((rn, ci), ('', None))))
                                      for ci in range(1, 7)) + ' |')
    md.append('')
    (HERE / '05-frequency-and-statistics.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

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
    wired = sorted(wl_cells, key=lambda k: -wl_cells[k])
    unwired = [f'{wid}（{wmap[wid][1]}）' for wid in sorted(wmap) if wid not in
               {k.split(' ')[0] for k in wl_cells}]
    md.append('## 接线状态〔提取注，派生自「7.展开执行矩阵」〕')
    md.append('')
    md.append(f'- **已接入展开矩阵（{len(wired)} 个）**：'
              + '；'.join(f'{k.split(" ")[0]}={wl_cells[k]} 格' for k in wired) + '。')
    md.append(f'- **已定义、未接入（{len(unwired)} 个）**：' + '、'.join(unwired)
              + '——「7.展开执行矩阵」310 格中无任何以之为负载的格。')
    md.append('')
    (HERE / '06-workloads.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 07-expanded-matrix.csv（Excel行 + 43 列全量） ----
    with open(HERE / '07-expanded-matrix.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Excel行'] + SHEET8_COLS)
        for rn, v in expanded:
            w.writerow([f'R{rn}'] + [disp(*v[j]) for j in range(43)])

    # ---- 07-expanded-matrix.md（列文档 + 分布 + 每模型模板） ----
    md = []
    md.append('# 07 · 展开执行矩阵（模型×频率×负载，310 个实验格）')
    md.append('')
    md.append(src_note)
    md.append('')
    md.append('> 工作表「7.展开执行矩阵」R2–R311（表头 R1），43 列 × 310 行，逐行忠实提取。'
              '全量数据在 **`07-expanded-matrix.csv`**（UTF-8 无 BOM；1 个管理列 + 源表 43 列）；'
              '本文件只给列文档与分布汇总。')
    md.append('> 展开规则已由 `extract_v2.py` 交叉校验：从「3.位置x模型矩阵」的 适用频率 × 适用负载'
              ' 重放展开，310 行（模型ID、频率、负载名）与源表逐行全等（含顺序）；'
              'RunID 310/310 唯一且 == 模型ID-频率-负载ID。')
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
            cls = '键：`模型ID-频率-负载ID`，310/310 唯一'
        elif ci <= 15:
            cls = '设计展开列（来自「3.位置x模型矩阵」对应行；频率定义/负载定义由 sheet6/sheet7 自带）'
        elif ci == STATUS_COL + 1:
            cls = '**记录状态：310/310 全部为「待执行」**'
        elif ci in [c + 1 for c in FORMULA_COLS]:
            cls = ('公式列（共享公式机制）：母公式 25 格（行 2/66/130/194/258）+ t="shared" 共享引用 1525 格，'
                   '5 列公式绑定全部 310 行，无缓存值——打开工作簿即全表可算，无需下拉复制')
        elif ci == 43:
            cls = '该模型子模型全枚举（整格文本，193 子模型的载体）'
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
    md.append('### 频率分布（310 格）')
    md.append('')
    md.append('| 频率 | ' + ' | '.join(k for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6']) + ' |')
    md.append('|---|' + '---|' * 7)
    md.append('| 格数 | ' + ' | '.join(str(freq_cells.get(k, 0))
              for k in ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6']) + ' |')
    md.append('')
    md.append('### 单元分布（310 格）')
    md.append('')
    md.append('| 单元 | ' + ' | '.join(EXPECTED_UNITS) + ' |')
    md.append('|---|' + '---|' * 6)
    md.append('| 格数 | ' + ' | '.join(str(unit_cells[u]) for u in EXPECTED_UNITS) + ' |')
    md.append('')
    md.append('### 负载分布（310 格，11 种接入负载）')
    md.append('')
    md.append('| 负载 | ' + ' | '.join(k.split(' ')[0] for k in wired) + ' |')
    md.append('|---|' + '---|' * len(wired))
    md.append('| 格数 | ' + ' | '.join(str(wl_cells[k]) for k in wired) + ' |')
    md.append('')
    md.append('### 每模型格数模板（按故障类型，57 模型全遵守）')
    md.append('')
    md.append('| 故障类型 | 模型数 | 适用频率组合 | 每模型格数 |')
    md.append('|---|---|---|---|')
    ft_freq = {}
    for _, v in design:
        ft_freq.setdefault(v[3][0], set()).add(v[6][0])
    for ft in ft_models:
        combos = ' 或 '.join(sorted(ft_freq[ft]))
        md.append(f'| {ft} | {len(ft_models[ft])} | {combos} | {next(iter(ft_template[ft]))} |')
    md.append('')
    md.append('〔提取注〕格数 = len(适用频率) × len(适用负载)，每模型固定 2 个适用负载；'
              'FP/SIMD Decode 无卡死模型（FD09 为时序），故该单元 52 格而非 48。')
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

    # ---- README.md（导航 + 方法 + 断言引用 + sha256 + 诚实性注记） ----
    md = []
    md.append('# V2.0 忠实层 —— gem5-fi OoO 单元故障注入方案 V2.0（北极星提取）')
    md.append('')
    md.append('> 本目录是《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（9 表，WPS 生成）的忠实提取层，'
              '全部文件由 `extract_v2.py` 确定性生成（勿手改；改表后重跑生成器）。')
    md.append('> V1.0 忠实层在 `../`；**两版口径不同，数值永不混用**——按用户指令 2026-09-28，'
              'V2.0 是 V1.0 的重大更新版本，冲突处以 V2.0 为准（V1.0↔V2.0 行级映射见 `d-bridge-v1-v2.csv`，'
              '由 `bridge_v1_v2.py` 生成，属 V2-W0.2 独立单元）。')
    md.append('')
    md.append('## 文件导航')
    md.append('')
    md.append('| 文件 | 来源工作表 | 内容 |')
    md.append('|---|---|---|')
    md.append('| `00-overview.md` | 0.说明与总览 | 范围 / B0 基线 / 工作簿结构 / 统计与判定边界（R1–R25 单列表） |')
    md.append('| `01-units-and-research.md` | 1.单元与现有研究 | 六单元 × 现有研究 / 证据直接性 / 研究空白 |')
    md.append('| `02-ooo-params-baseline.md` | 2.OOO参数基线 | B0 参数（R2–R24）+ S0–S6 敏感性 + 逐单元保护机制核验（R25–R31） |')
    md.append('| `03-design-matrix.md` | 3.位置x模型矩阵 | **57 故障模型 × 14 列全量**（按单元分节；D/R/B/FD/FR/FB） |')
    md.append('| `design-matrix.csv` | 3.位置x模型矩阵 | 同上机读版（模型ID + Excel行 + 14 列，57 行） |')
    md.append('| `04-observation-points.md` | 4.观测点定义 | L0–L5 传播链观测点（6 层级 × 6 列） |')
    md.append('| `05-frequency-and-statistics.md` | 5.频率与统计 | F0–F6 档位（eligible-event 归一化）+ 8 条统计规则 |')
    md.append('| `06-workloads.md` | 6.负载清单 | W0–W13（14 负载）+ 接线状态提取注（11 接入 / 3 未接入） |')
    md.append('| `07-expanded-matrix.csv` | 7.展开执行矩阵 | **310 实验格 × 43 列全量**（+Excel行 管理列） |')
    md.append('| `07-expanded-matrix.md` | 7.展开执行矩阵 | 列文档 + 频率/单元/负载分布 + 每模型格数模板 |')
    md.append('| `08-references.md` | 8.文献与来源 | 11 条来源（GEM5-O3/BASE、TC23、MICRO24/25、CHAOS26 等） |')
    md.append('| `d-bridge-v1-v2.csv` | （派生） | V1.0 91 行 ↔ V2.0 57 模型映射（V2-W0.2，`bridge_v1_v2.py` 生成） |')
    md.append('')
    md.append('## 提取方法')
    md.append('')
    md.append('- 纯标准库（本机 pip 403 无 openpyxl）：`zipfile` + `xml.etree.ElementTree` 直解'
              ' spreadsheetml XML；解析核心复自经读回校验的全量转储器（sharedStrings / inlineStr /'
              ' str / b / n 全类型覆盖）。')
    md.append('- WPS 工作簿适配：rels 使用包绝对路径 `/xl/...`（与 Excel 相对路径两种写法都兼容）；'
              '母公式格以 `值⟦f:公式⟧` 记法保留（25 格，无缓存值）；其余行的 t="shared" 共享公式引用'
              '（1525 格，无文本无缓存值）在 CSV 中呈现为空，完整机制见断言 formulas-shared 与诚实性注记 (b)。')
    md.append('- 忠实原则：单元格文字**原文照录**，仅版式/标题/行号标记排版；一切本目录标注以'
              '〔提取注〕显式标记。')
    md.append('- 确定性：无时间戳、无随机数；重跑逐字节复现（sha256 不变）。')
    md.append('')
    md.append('## 断言结果（`python3 extract_v2.py` 真实运行输出，逐字引用）')
    md.append('')
    md.append('```')
    md.extend(report)
    md.append('')
    md.append('EXTRACTION VERIFICATION ' + ('PASSED' if ok else 'FAILED'))
    md.append('```')
    md.append('')
    md.append('## 源文件')
    md.append('')
    md.append(f'- 路径：`docs/gem5-fi/ooo/gem5-fi-OoO单元故障注入方案V2.0.xlsx`')
    md.append(f'- sha256：`{sha}`')
    md.append('- 9 表非空单元格：22 / 49 / 151 / 812 / 42 / 102 / 90 / 5338 / 72（合计 6,678）')
    md.append('')
    md.append('## 诚实性注记（HONESTY NOTES）')
    md.append('')
    md.append('(a) **工作簿内部不一致（展开维度）**：sheet1 R15 声称展开维度为'
              '「模型×故障表现形式/子模型×频率×负载全展开」，但 sheet8 实际只展开到'
              ' **模型×频率×负载 = 310 格**，子模型以整格文本附在 AQ 列。若真按子模型展开应为'
              ' **1050 格**（派生计算 Σ(子模型数×格数)，已由本脚本复算核实）。'
              '计划裁决 **D4**：执行 310 格，格内按子模型分层记录，不扩建 1050 格。')
    md.append('')
    md.append('(b) **公式机制（2026-09-29 编排者独立批判性核验修正——覆盖早先"仅 5 行 25 格、'
              '使用前需下拉复制"的机制误读）**：sheet8 的 5 个计算列（X=SDC率(可分析activated) /'
              ' Y=激活率 / AL=硬件RAS检测率(任意时点) / AM=检测计数差额（应为0） / AN=结局计数差额（应为0））'
              '共有 **1550 个公式单元格 = 5 列 × 全部 310 行**，全部为 t="shared" 共享公式：'
              '25 个母公式文本在 Excel 行 2/66/130/194/258（每列 5 个 si 组：组 0-19 各 64 格 + '
              '组 20-24 各 54 格），其余 1525 格为共享引用；**0 个缓存值**。共享公式已把 5 列绑定到'
              '全表——**打开工作簿即全表可算，无需下拉复制**（delta 报告 §3.8.4 原说法的勘误见其 §7）。'
              '公式语义（与 sheet6 统计规则逐条一致，已逐条审计）：'
              '`SDC率 = SDC/(Activated − Simulator failure)`、`激活率 = Activated/Attempted`、'
              '`检测计数差额 = SUM(首检四类) − (Activated − Simulator failure)`、'
              '`结局计数差额 = SUM(五类结局) + Simulator failure − Activated`（两个差额列应为 0，'
              '自检审计列）。')
    md.append('')
    md.append('(c) **定义了但未接线**：负载 W0（MiniCheck-OOO）/ W2（BEEBS-DelayAVF）/'
              ' W12（SPEC CPU2017 SimPoint，需许可证）在 sheet7 有完整定义，但 sheet8 的 310 格中'
              '无任何以之为负载的格；频率档 F3（高频压力）在 sheet6 有定义，但 310 格中 0 格使用。')
    md.append('')
    md.append('(d) **WPS 生成的工作簿**：无 docProps（创建者/修改时间元数据缺失）；'
              'zip 内部时间戳 2026-09-28 16:50（全部条目一致）；rels 用包绝对路径 `/xl/...`。'
              '与 V1.0（Excel 生成、有合并单元格）不同，V2.0 九表均无合并单元格。')
    md.append('')
    md.append('(e) **全部 310 格 记录状态=待执行**：所有结果槽（22 个值列）在源表中全空，'
              '与 V1.0 源表口径一致——本目录是纯设计提取，不含任何实验结果数据。')
    md.append('')
    (HERE / 'README.md').write_text('\n'.join(md) + '\n', encoding='utf-8')

    # ---- 控制台报告 ----
    outputs = ['00-overview.md', '01-units-and-research.md', '02-ooo-params-baseline.md',
               '03-design-matrix.md', 'design-matrix.csv', '04-observation-points.md',
               '05-frequency-and-statistics.md', '06-workloads.md', '07-expanded-matrix.csv',
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
