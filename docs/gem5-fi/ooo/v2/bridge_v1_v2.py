#!/usr/bin/env python3
"""V1.0(D01-D91) ↔ V2.0(模型ID) 桥接表生成器 + 覆盖断言（V2-W0.2）。

编码 V1.0 忠实层 91 个设计单元到 V2.0 57 个故障模型的**完整行级映射**，生成
`d-bridge-v1-v2.csv`（116 行 = 91 个 V1.0 行各一次 + 25 个 V2.0 全新模型）。

映射来源（SOURCE OF TRUTH）：v2-delta-report.md §3.7.4「V1.0(D01-D91) ↔ V2.0(模型ID)
对应表」（人工语义比对：单元 + 注入位置语义 + 故障类型；依据 2026-09-28 已验证的
delta 报告，其中程序覆盖断言 91 ID 全出现且仅一次）。口径：
  relation=merged     71 行 —— V1.0 行被某 V2.0 模型吸收（同单元或单元内位置语义微调）；
  relation=migrated    3 行 —— D47/D48/D49 跨单元迁移（Int Dispatch/ROB → Int Rename R07）；
  relation=cancelled  17 行 —— V1.0 行在 V2.0 无对应（读到旧数据族 / Int+FP IQ tag 族 /
                               SVE 族整体取消）；
  relation=new        25 行 —— V2.0 全新模型（无 V1.0 祖先），v1_id 留空。
  合并口径：merged(71) + migrated(3) = 74 个 V1.0 行 → 32 个 V2.0 模型；
            32（有祖先）+ 25（全新）= 57 = V2.0 设计矩阵全部模型。

v2_submodels 列 = 目标 V2.0 模型的**子模型字母全集**（如 "a/b/c/d"，从
《gem5-fi-OoO单元故障注入方案V2.0.xlsx》「3.位置x模型矩阵」列「故障表现形式/子模型」
解析）；该 V1.0 行具体落到哪个子模型，delta 报告有指认的写入 note（如 "D01-a"），
无逐一指认的为模型级合并（note 说明）。

断言（任一失败即非零退出）：
  1) 91 个 V1.0 ID（来自 ../design-matrix.csv）每个恰好出现一次；
  2) cancelled 集合 == delta 报告的 17 个；
  3) D47/D48/D49 → R07（relation=migrated）；
  4) 映射反转 == delta 报告 §3.7.4「保留/合并」表 + 跨单元迁移（32 模型 ← 74 行）；
  5) 57 个 V2.0 模型全覆盖（32 有祖先 + 25 全新），且都存在于源工作簿；
  6) CSV 确定性再生成（重跑逐字节相同）。

纯标准库；确定性输出（无时间戳/随机数）。用法：python3 bridge_v1_v2.py
"""

import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NS_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

HERE = Path(__file__).resolve().parent
V1_CSV = (HERE / '..' / 'design-matrix.csv').resolve()
XLSX = (HERE / '..' / 'gem5-fi-OoO单元故障注入方案V2.0.xlsx').resolve()
OUT_CSV = HERE / 'd-bridge-v1-v2.csv'

# ---------------- 91 行映射（delta 报告 §3.7.4；D42 note 修正见下） ----------------
# v1_id -> (v2_model_id | None, relation, note)
M = {
    # Int Decode
    'D01': ('D01', 'merged', 'opcode 单翻 → D01-a 子模型'),
    'D02': ('D02', 'merged', 'opcode 双翻 → D02（与 D05/D07 三处双翻合并；跨字段子模型为新增）'),
    'D03': ('D03', 'merged', 'opcode 换值保留 → D03-a/b/c'),
    'D04': ('D01', 'merged', '寄存器号单翻 → D01-b'),
    'D05': ('D02', 'merged', '寄存器号双翻 → D02'),
    'D06': ('D01', 'merged', '立即数单翻 → D01-c'),
    'D07': ('D02', 'merged', '立即数双翻 → D02'),
    'D08': ('D05', 'merged', '符号扩展位定向翻转 → D05-c，并入错位拼接族'),
    'D09': ('D05', 'merged', '子字段拼接错位 → D05-a/b/d'),
    'D10': ('D06', 'merged', '裂解控制位状态翻转 → D06-e 及扩展（控制位换值族，扩展 sf/S/shift/extend）'),
    # Int Rename
    'D11': ('R01', 'merged', 'RAT 映射单翻 → R01-a/b（拆源/目的子模型）'),
    'D12': ('R02', 'merged', 'RAT 映射双翻 → R02'),
    'D13': ('R03', 'merged', 'RAT 映射换值（固定间隔）→ R03'),
    'D14': ('R03', 'merged', 'RAT 映射换值（误预测事件触发）→ R03+F6（触发语义改为确定性事件）'),
    'D15': ('R09', 'merged', 'RAT 映射卡死 → R09-a/b'),
    'D16': ('R03', 'merged', 'RAT 读到旧数据 → 并入 R03 合法换值到活跃 tag 族（"读到旧数据"独立行取消）'),
    'D17': ('R05', 'merged', '空闲表重复分配（固定）→ R05-c'),
    'D18': ('R05', 'merged', '空闲表重复分配（事件）→ R05-c+F6'),
    'D19': ('R05', 'merged', '空闲表丢失释放 → R05-a 泄漏子模型'),
    'D20': ('R05', 'merged', '空闲表头指针单翻 → R05-c head 跳'),
    'D21': ('R05', 'merged', '空闲表头指针双翻 → R05-c'),
    'D22': ('R09', 'merged', '空闲表头/尾指针卡死 → R09-c/d'),
    'D23': ('R06', 'merged', '重命名检查点单翻 → R06（故障类型改为换值/恢复错误）'),
    'D24': ('R06', 'merged', '重命名检查点双翻 → R06'),
    # Int Dispatch/ROB
    'D25': ('B01', 'merged', 'ROB PC 字段单翻 → B01-a'),
    'D26': ('B02', 'merged', 'ROB PC 字段双翻 → B02'),
    'D27': ('B10', 'merged', 'ROB PC 字段卡死 → B10-a'),
    'D28': ('B01', 'merged', 'ROB 寄存器标识符单翻 → B01-b'),
    'D29': ('B02', 'merged', 'ROB 寄存器标识符双翻 → B02'),
    'D30': ('B03', 'merged', 'ROB 寄存器标识符换值 → B03-a'),
    'D31': ('B10', 'merged', 'ROB 寄存器标识符卡死 → B10-b'),
    'D32': ('B04', 'merged', 'done 位提前置位（固定）→ B04-a'),
    'D33': ('B04', 'merged', 'done 位提前置位（事件）→ B04-a+F6'),
    'D34': ('B04', 'merged', 'done 位延迟置位（固定）→ B04-c 延后清除族'),
    'D35': ('B04', 'merged', 'done 位延迟置位（事件）→ B04-c+F6'),
    'D36': ('B01', 'merged', '旧物理寄存器字段单翻 → B01-b tag 字段（squash 触发语义取消）'),
    'D37': ('B02', 'merged', '旧物理寄存器字段双翻 → B02'),
    'D38': ('B03', 'merged', '旧物理寄存器字段换值 → B03-a'),
    'D39': ('B10', 'merged', '旧物理寄存器字段卡死 → B10-b'),
    'D40': (None, 'cancelled', '"ROB 项读到旧数据"——"读到旧数据"独立故障族取消（V1.0 共 7 行全取消；'
                             '旧值读取语义并入换值/提前 ready/lane 拼接等子模型机制）'),
    'D41': ('B06', 'merged', 'ROB 头指针单翻 → B06-a'),
    'D42': ('B02', 'merged', 'ROB 头指针双翻 → B02（与其他双翻行合并；头/尾指针单翻与尾指针双翻 → '
                            'B06 合法索引换值。注：diff_v1_v2.py 该行 note 误写 "→ B06"，目标 B02 以 '
                            'delta 报告 §3.7.4 表为准）'),
    'D43': ('B10', 'merged', 'ROB 头指针卡死 → B10（slot 卡死族）'),
    'D44': ('B06', 'merged', 'ROB 尾指针单翻 → B06-b'),
    'D45': ('B06', 'merged', 'ROB 尾指针双翻 → B06'),
    'D46': ('B10', 'merged', 'ROB 尾指针卡死 → B10'),
    'D47': ('R07', 'migrated', 'IQ ready 位提前置位 → R07-a（跨单元迁移：Int Dispatch/ROB → '
                              'Int Rename，ready/busy scoreboard）'),
    'D48': ('R07', 'migrated', 'IQ ready 位永不置位（固定）→ R07-b 丢失 ready（跨单元迁移同 D47）'),
    'D49': ('R07', 'migrated', 'IQ ready 位永不置位（事件）→ R07-b+F6（跨单元迁移同 D47）'),
    'D50': (None, 'cancelled', 'Int IQ tag 字段换值——Int IQ entry tag 独立注入族整体取消'
                             '（V2.0 dispatch 侧只保留 B07 steering）'),
    'D51': (None, 'cancelled', 'Int IQ tag 字段单翻——Int IQ entry tag 族取消'),
    'D52': (None, 'cancelled', 'Int IQ tag 字段双翻——Int IQ entry tag 族取消'),
    'D53': (None, 'cancelled', 'Int IQ tag 字段卡死——Int IQ entry tag 族取消'),
    'D54': (None, 'cancelled', 'Int IQ tag 字段读到旧数据——"读到旧数据"族取消'),
    'D55': ('B07', 'merged', '分发端口选择 → B07-c dispatch lane'),
    # FP/SIMD Decode
    'D56': ('FD01', 'merged', 'FP opcode 单翻 → FD01-a'),
    'D57': ('FD02', 'merged', 'FP opcode 双翻 → FD02'),
    'D58': ('FD03', 'merged', 'FP opcode 换值 → FD03'),
    'D59': ('FD01', 'merged', 'V 寄存器号单翻 → FD01-b'),
    'D60': ('FD02', 'merged', 'V 寄存器号双翻 → FD02'),
    'D61': ('FD05', 'merged', '指令路由判定位 → FD05 scalar/vector 模式/元素宽度'),
    # FP/SIMD Rename
    'D62': ('FR01', 'merged', '标量 FP RAT 单翻 → FR01-a'),
    'D63': ('FR02', 'merged', '标量 FP RAT 双翻 → FR02'),
    'D64': ('FR03', 'merged', '标量 FP RAT 换值 → FR03-a'),
    'D65': ('FR10', 'merged', '标量 FP RAT 卡死 → FR10-a/b'),
    'D66': (None, 'cancelled', '标量 FP RAT 读到旧数据——"读到旧数据"族取消'),
    'D67': ('FR01', 'merged', '向量 RAT 单翻 → FR01-b'),
    'D68': ('FR02', 'merged', '向量 RAT 双翻 → FR02'),
    'D69': ('FR03', 'merged', '向量 RAT 换值 → FR03-b'),
    'D70': ('FR10', 'merged', '向量 RAT 卡死 → FR10'),
    'D71': (None, 'cancelled', '向量 RAT 读到旧数据——"读到旧数据"族取消'),
    'D72': ('FR05', 'merged', '标量 FP 空闲表重复分配（固定）→ FR05-c'),
    'D73': ('FR05', 'merged', '标量 FP 空闲表重复分配（事件）→ FR05-c+F6'),
    'D74': ('FR05', 'merged', '向量空闲表重复分配（固定）→ FR05-c'),
    'D75': ('FR05', 'merged', '向量空闲表重复分配（事件）→ FR05-c+F6'),
    'D76': ('FR05', 'merged', '标量 FP 空闲表丢失释放 → FR05-a/b 泄漏'),
    'D77': ('FR05', 'merged', '向量空闲表丢失释放 → FR05-a/b'),
    'D78': (None, 'cancelled', 'SVE 谓词 RAT 单翻——SVE 从 B0 剔除（sheet3 R16/R21：SVE 仅单独扩展 '
                             'campaign；负载清单无 SVE 负载）'),
    'D79': (None, 'cancelled', 'SVE 谓词 RAT 双翻——SVE 取消'),
    'D80': (None, 'cancelled', 'SVE 谓词 RAT 换值——SVE 取消'),
    'D81': (None, 'cancelled', 'SVE 谓词 RAT 卡死——SVE 取消'),
    'D82': (None, 'cancelled', 'SVE 谓词 RAT 读到旧数据——SVE 取消'),
    # FP/SIMD Dispatch/ROB
    'D83': ('FB01', 'merged', 'ROB PC 字段（FP 自检）单翻 → FB01-a'),
    'D84': ('FB05', 'merged', 'ROB done 位（FP 自检，固定）→ FB05-a 提前 complete'),
    'D85': ('FB05', 'merged', 'ROB done 位（FP 自检，事件）→ FB05-a+F6'),
    'D86': ('FB04', 'merged', 'FP/SIMD IQ ready 位提前置位 → FB04-a（仍在 FP/SIMD Dispatch/ROB；'
                             '位置语义改为 operand-ready/issued/replay）'),
    'D87': (None, 'cancelled', 'FP/SIMD IQ tag 换值——IQ tag 族取消'),
    'D88': (None, 'cancelled', 'FP/SIMD IQ tag 单翻——IQ tag 族取消'),
    'D89': (None, 'cancelled', 'FP/SIMD IQ tag 双翻——IQ tag 族取消'),
    'D90': ('FB10', 'merged', 'FP/SIMD IQ tag 卡死 ≈ FB10（位置从 IQ 移到 ROB slot，语义近似）'),
    'D91': (None, 'cancelled', 'FP/SIMD IQ tag 读到旧数据——"读到旧数据"族取消'),
}

# delta 报告 §3.7.4「保留/合并」表 + 跨单元迁移，反转为 模型 ← [V1.0 行]
EXPECTED_ABSORPTION = {
    'D01': ['D01', 'D04', 'D06'], 'D02': ['D02', 'D05', 'D07'], 'D03': ['D03'],
    'D05': ['D08', 'D09'], 'D06': ['D10'],
    'R01': ['D11'], 'R02': ['D12'], 'R03': ['D13', 'D14', 'D16'],
    'R05': ['D17', 'D18', 'D19', 'D20', 'D21'], 'R06': ['D23', 'D24'], 'R09': ['D15', 'D22'],
    'B01': ['D25', 'D28', 'D36'], 'B02': ['D26', 'D29', 'D37', 'D42'],
    'B03': ['D30', 'D38'], 'B04': ['D32', 'D33', 'D34', 'D35'],
    'B06': ['D41', 'D44', 'D45'], 'B07': ['D55'],
    'B10': ['D27', 'D31', 'D39', 'D43', 'D46'],
    'FD01': ['D56', 'D59'], 'FD02': ['D57', 'D60'], 'FD03': ['D58'], 'FD05': ['D61'],
    'FR01': ['D62', 'D67'], 'FR02': ['D63', 'D68'], 'FR03': ['D64', 'D69'],
    'FR05': ['D72', 'D73', 'D74', 'D75', 'D76', 'D77'], 'FR10': ['D65', 'D70'],
    'FB01': ['D83'], 'FB05': ['D84', 'D85'], 'FB04': ['D86'], 'FB10': ['D90'],
    'R07': ['D47', 'D48', 'D49'],  # 跨单元迁移（原 Int Dispatch/ROB）
}

# 25 个 V2.0 全新模型（无 V1.0 祖先；delta 报告 §3.7.4「V2.0 全新行」）
NEW_MODELS = {
    'D04': '寄存器号换值', 'D07': 'decode 时序', 'D08': 'uop 序列', 'D09': 'decode 卡死',
    'R04': 'new-dest/old-dest 换值', 'R08': 'rename 事务原子性',
    'B05': 'exception/mispredict/serialize 控制状态', 'B08': 'squash 时序', 'B09': 'commit 事务时序',
    'FD04': 'V 寄存器/lane 换值', 'FD06': 'rounding/FPCR', 'FD07': 'shuffle/lane 掩码拼接',
    'FD08': 'FP uop 拆分', 'FD09': 'FP decode 时序',
    'FR04': 'FP new/old-dest 换值', 'FR06': 'FP checkpoint', 'FR07': 'FP ready/busy',
    'FR08': 'partial-write 语义', 'FR09': 'FP rename 事务',
    'FB02': 'FP ROB 双翻', 'FB03': 'FU steering', 'FB06': '完成事件配对',
    'FB07': 'writeback lane mask', 'FB08': 'FP squash 时序', 'FB09': 'FP commit 事务',
}

EXPECTED_CANCELLED = ['D40', 'D50', 'D51', 'D52', 'D53', 'D54', 'D66', 'D71',
                      'D78', 'D79', 'D80', 'D81', 'D82', 'D87', 'D88', 'D89', 'D91']


# ---------------- V2.0 设计矩阵解析（复用 extract_v2.py 的解析核心） ----------------

def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def split_ref(ref: str):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    return int(m.group(2)), col_to_num(m.group(1))


def load_design_sheet(xlsx: Path):
    """→ [(模型ID, 单元, 故障类型, 子模型字母序列)]，按源表行序。"""
    zf = zipfile.ZipFile(xlsx)
    names = zf.namelist()
    sst = []
    if 'xl/sharedStrings.xml' in names:
        root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS_MAIN}si'):
            sst.append(''.join(t.text or '' for t in si.iter(f'{NS_MAIN}t')))
    wb = ET.fromstring(zf.read('xl/workbook.xml'))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    target = None
    for sh in wb.iter(f'{NS_MAIN}sheet'):
        if '位置x模型矩阵' in (sh.get('name') or ''):
            t = relmap[sh.get(f'{NS_REL}id')]
            target = t.lstrip('/') if t.startswith('/') else (t if t.startswith('xl/') else 'xl/' + t)
            break
    assert target, 'design matrix sheet not found'
    root = ET.fromstring(zf.read(target))
    grid = {}
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
    out = []
    for rn in range(2, 59):
        mid = grid.get((rn, 1), '')
        if not mid:
            continue
        unit = grid.get((rn, 2), '')
        ftype = grid.get((rn, 4), '')
        subs_text = grid.get((rn, 6), '')
        pat = r'(?<![A-Za-z0-9])' + re.escape(mid) + r'-([a-z])(?![a-z])'
        subs = sorted(set(re.findall(pat, subs_text)))
        out.append((mid, unit, ftype, subs))
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    report = []
    ok = True

    def check(tag, cond, detail=''):
        nonlocal ok
        ok &= bool(cond)
        report.append(f'[{tag}] {"PASS" if cond else "FAIL"}' + (f' — {detail}' if detail else ''))
        return bool(cond)

    # V1.0 91 个 ID（来自 V1.0 忠实层 CSV）
    with open(V1_CSV, newline='', encoding='utf-8') as f:
        v1_rows = list(csv.DictReader(f))
    v1_ids = [r['ID'] for r in v1_rows]
    v1_unit = {r['ID']: r['单元'] for r in v1_rows}

    # V2.0 57 个模型（来自源工作簿）
    v2_models = load_design_sheet(XLSX)
    v2_ids = [m[0] for m in v2_models]
    v2_info = {m[0]: m for m in v2_models}

    report.append(f'[source] V1.0: {V1_CSV.name} ({len(v1_ids)} ids); '
                  f'V2.0: {XLSX.name} ({len(v2_ids)} models)')

    # ---- 断言 1：91 个 V1.0 ID 每个恰好一次 ----
    check('v1-coverage', len(v1_ids) == 91 and len(set(v1_ids)) == 91
          and sorted(M) == sorted(v1_ids) and len(M) == 91,
          f'{len(v1_ids)} v1 ids from design-matrix.csv, each mapped exactly once (91/91)')

    # ---- 断言 2：cancelled 集合 == delta 报告的 17 个 ----
    cancelled = sorted(d for d, (m, rel, _) in M.items() if rel == 'cancelled')
    check('cancelled-17', cancelled == EXPECTED_CANCELLED
          and all(M[d][0] is None for d in cancelled),
          f'{len(cancelled)} cancelled ids match the delta report list')

    # ---- 断言 3：D47/D48/D49 → R07（migrated） ----
    mig_ok = all(M[d][0] == 'R07' and M[d][1] == 'migrated' for d in ('D47', 'D48', 'D49'))
    migrated = sorted(d for d, (m, rel, _) in M.items() if rel == 'migrated')
    check('migrated-r07', mig_ok and migrated == ['D47', 'D48', 'D49']
          and all(v1_unit[d] == 'Int Dispatch/ROB' for d in migrated)
          and v2_info['R07'][1] == 'Int Rename',
          'D47/D48/D49 (Int Dispatch/ROB) -> R07 (Int Rename), relation=migrated')

    # ---- 断言 4：映射反转 == delta 报告吸收表 ----
    absorption = {}
    for d, (m, rel, _) in M.items():
        if m is not None:
            absorption.setdefault(m, []).append(d)
    inv_ok = (sorted(absorption) == sorted(EXPECTED_ABSORPTION)
              and all(sorted(absorption[k]) == sorted(EXPECTED_ABSORPTION[k]) for k in absorption))
    n_absorbed = sum(len(v) for v in absorption.values())
    check('absorption', inv_ok and n_absorbed == 74 and len(absorption) == 32,
          f'inverted mapping == delta report table: {n_absorbed} v1 rows -> '
          f'{len(absorption)} v2 models (74 -> 32)')

    # ---- 断言 5：57 个 V2.0 模型全覆盖（32 有祖先 + 25 全新）----+
    ancestry = set(absorption)
    new = sorted(NEW_MODELS)
    check('v2-coverage', ancestry | set(new) == set(v2_ids) and not (ancestry & set(new))
          and len(v2_ids) == 57 and all(m in v2_info for m in list(ancestry) + new),
          f'all 57 V2.0 models covered: {len(ancestry)} by ancestry + {len(new)} new; '
          f'every id exists in the design matrix sheet')

    # ---- 生成 CSV（91 V1.0 行 + 25 全新行 = 116 行） ----
    def subs_str(mid):
        return '/'.join(v2_info[mid][3]) if mid in v2_info else ''

    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['v1_id', 'v2_model_id', 'v2_submodels', 'relation', 'note'])
    for d in v1_ids:  # 按 V1.0 表序 D01..D91，每个恰好一次
        m, rel, note = M[d]
        w.writerow([d, m or '', subs_str(m) if m else '', rel, note])
    for mid in [m[0] for m in v2_models if m[0] in NEW_MODELS]:  # 按源表序
        _, unit, ftype, _ = v2_info[mid]
        w.writerow(['', mid, subs_str(mid), 'new',
                    f'V2.0 全新行（无 V1.0 祖先）：{NEW_MODELS[mid]}；单元={unit}；故障类型={ftype}'])
    content = buf.getvalue()
    n_rows = 1 + 91 + 25
    check('rows', content.count('\n') == n_rows, f'CSV = {n_rows} lines (header + 91 + 25)')

    # ---- 断言 6：确定性再生成 ----
    existed = OUT_CSV.exists()
    prev = OUT_CSV.read_text(encoding='utf-8') if existed else None
    OUT_CSV.write_text(content, encoding='utf-8')
    again = OUT_CSV.read_text(encoding='utf-8')
    check('deterministic', again == content and (prev is None or prev == content),
          f'regenerated {OUT_CSV.name} byte-identical'
          + ('' if existed else ' (first run)'))

    report.append(f'[outputs] {OUT_CSV.name} (91 v1 rows + 25 new rows = 116 data rows)')
    print('\n'.join(report))
    if not ok:
        print('\nBRIDGE VERIFICATION FAILED — do not commit generated files.')
        sys.exit(1)
    print('\nBRIDGE VERIFICATION PASSED')


if __name__ == '__main__':
    main()
