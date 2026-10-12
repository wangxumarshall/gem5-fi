#!/usr/bin/env python3
"""[LSU][XLSX-BACKFILL] 权威 Excel 矩阵回填器（原生 zip+XML，无 openpyxl 依赖）。

协议（用户指令 2026-10-12 第二节）：
  1. 带时间戳备份（仓库外 /home/sdc/gem5-fi-backups/excel_backups/）；
  2. 单写入者（主 Agent 串行调用）；
  3. 先写临时文件；
  4. 重新打开校验：9 工作表、325 条矩阵记录（RunID 唯一）、表头 43 列逐字
     不变、无公式破坏、目标单元格新值正确；
  5. 校验全过才 os.replace 原子替换；
  6. 任何校验失败 → 保留原文件不动，退出码非 0。

写入语义：
  - 数值列（Q,R,S,T,U,V,W,AB,AC..AJ,AL..AP 等）写 <v> 数字；
  - 文本列（X,Y,Z,AA 等）写 inlineStr（不动 sharedStrings，Excel 兼容）；
  - 只更新 draft 中 backfill=true 的行的数值列 + 所有目标行的 Z/AA；
  - 绝不新增/删除/改名任何列、行、工作表。

用法：
  python3 tools/lsu_xlsx_backfill.py --draft /tmp/lsu_backfill_draft.json [--apply]
  不带 --apply = 干跑（只校验草案与目标行定位，不写）。
"""
import argparse
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX = "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
SHEET = "xl/worksheets/sheet8.xml"          # 7.展开执行矩阵
BACKUP_DIR = "/home/sdc/gem5-fi-backups/excel_backups"

# 列号 → 列字母（1 基）
def col_letter(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

NUM_COL_ORDER = [17, 18, 19, 20, 21, 22, 23, 42]   # attempted..simfail 对应列
# 草案键名（Subagent F 约定：attempted/activated 小写、simfail、五类大写驼峰）
DRAFT_NUM_KEYS = ["attempted", "activated", "Masked", "DC", "SDC", "Crash",
                  "Timeout", "simfail"]   # 依次写入列 17,18,19,20,21,22,23,42
TXT_COLS = ["SDC率", "激活率", "记录状态", "实测备注"]
TXT_COL_ORDER = {"SDC率": 24, "激活率": 25, "记录状态": 26, "实测备注": 27}


def cell_ref(col, row):
    return f"{col_letter(col)}{row}"


def read_rows(zf, sheet=SHEET):
    """(shared, sheet_root, rows{row:{col:text}}) —— 与 evidence/P0/xlsx_dump 同款只读解析。"""
    shared = []
    if "xl/sharedStrings.xml" in zf.namelist():
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        for si in root.iter(f"{{{NS}}}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS}}}t")))
    sheet = ET.fromstring(zf.read(sheet))
    rows = {}
    for c in sheet.iter(f"{{{NS}}}c"):
        m = re.match(r"([A-Z]+)(\d+)", c.get("r"))
        col = 0
        for ch in m.group(1):
            col = col * 26 + ord(ch) - 64
        r = int(m.group(2))
        t = c.get("t")
        v = c.find(f"{{{NS}}}v")
        if v is None or v.text is None:
            is_ = c.find(f"{{{NS}}}is")          # inlineStr（本工具写入格式）
            val = "" if is_ is None else "".join(
                tt.text or "" for tt in is_.iter(f"{{{NS}}}t"))
        else:
            val = shared[int(v.text)] if t == "s" else v.text
        rows.setdefault(r, {})[col] = val
    return rows


def make_cell(col, row, value, numeric):
    """规范 <c> 元素：数字直写 <v>；文本 inlineStr。"""
    c = ET.Element(f"{{{NS}}}c")
    c.set("r", cell_ref(col, row))
    if numeric:
        c.set("t", "n")
        v = ET.SubElement(c, f"{{{NS}}}v")
        v.text = str(value)
    else:
        c.set("t", "inlineStr")
        is_ = ET.SubElement(c, f"{{{NS}}}is")
        t = ET.SubElement(is_, f"{{{NS}}}t")
        t.text = str(value)
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return c


def apply_draft(draft, apply=False):
    zf = zipfile.ZipFile(XLSX)
    rows = read_rows(zf)
    # 定位目标行：列 1 = RunID
    rid_row = {rows[r].get(1, ""): r for r in rows if rows[r].get(1)}
    # 逐条核验草案定位
    plan = []          # (row, col, value, numeric)
    errors = []
    for rec in draft:
        rid = rec["runid"]
        row = rec.get("excel_row") or rid_row.get(rid)
        if not row or rid_row.get(rid) != row:
            errors.append(f"{rid}: excel_row={rec.get('excel_row')} 与矩阵实际行 "
                          f"{rid_row.get(rid)} 不一致")
            continue
        if rid_row.get(rid) is None:
            errors.append(f"{rid}: 矩阵无此 RunID")
            continue
        if rec.get("backfill"):
            for i, key in enumerate(DRAFT_NUM_KEYS):
                if rec.get(key) is not None:
                    plan.append((row, NUM_COL_ORDER[i], rec[key], True))
        for key in TXT_COLS:
            if rec.get(key) is not None:
                plan.append((row, TXT_COL_ORDER[key], rec[key], False))
    if errors:
        print("❌ 草案定位核验失败：")
        for e in errors:
            print("  ", e)
        return 1
    print(f"✓ 草案定位核验通过：{len(draft)} 条记录，{len(plan)} 个单元格写入计划")

    if not apply:
        for row, col, val, num in sorted(plan):
            print(f"  [dry] {cell_ref(col, row)} = {val!r}{'(数)' if num else ''}")
        print("干跑完成（--apply 执行写入）")
        return 0

    # ── 写入：解析 sheet8 XML，逐行插入/覆写单元格 ──
    ET.register_namespace("", NS)
    sheet = ET.fromstring(zf.read(SHEET))
    row_elems = {int(re.match(r"\d+", r.get("r")).group(0)): r
                 for r in sheet.iter(f"{{{NS}}}row")}
    ncols_changed = 0
    for row, col, val, num in plan:
        relem = row_elems.get(row)
        if relem is None:
            errors.append(f"行 {row} 不存在于 sheet8")
            continue
        ref = cell_ref(col, row)
        # 删除既有同引用单元格（覆写）
        for c in list(relem):
            if c.get("r") == ref:
                relem.remove(c)
        # 按列序插入
        newc = make_cell(col, row, val, num)
        inserted = False
        for c in relem:
            m = re.match(r"([A-Z]+)", c.get("r"))
            cc = 0
            for ch in m.group(1):
                cc = cc * 26 + ord(ch) - 64
            if cc > col:
                relem.insert(list(relem).index(c), newc)
                inserted = True
                break
        if not inserted:
            relem.append(newc)
        ncols_changed += 1
    if errors:
        print("❌ 写入阶段定位失败：", errors)
        return 1

    # ── 新 zip 临时文件（复制其余条目，替换 sheet8）──
    new_sheet = ET.tostring(sheet, xml_declaration=True, encoding="UTF-8")
    fd, tmp = tempfile.mkstemp(suffix=".xlsx", dir=os.path.dirname(
        os.path.abspath(XLSX)))
    os.close(fd)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zf.namelist():
            if item == SHEET:
                zout.writestr(item, new_sheet)
            else:
                zout.writestr(item, zf.read(item))

    # ── 校验临时文件 ──
    v = verify(tmp, draft, plan)
    if v:
        os.remove(tmp)
        print("❌ 校验失败，原文件未动：", v)
        return 1

    # ── 备份 + 原子替换 ──
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"lsu-matrix-{ts}.xlsx")
    shutil.copy2(XLSX, bak)
    os.replace(tmp, XLSX)
    print(f"✓ 回填完成：{ncols_changed} 单元格；备份 {bak}；原子替换 {XLSX}")
    return 0


def verify(path, draft, plan):
    """返回错误列表（空=通过）：9 表、325 RunID、表头、目标值。"""
    errs = []
    zf = zipfile.ZipFile(path)
    # ① 9 工作表
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    n = len(list(wb.iter(f"{{{NS}}}sheet")))
    if n != 9:
        errs.append(f"工作表数 {n} != 9")
    # ② 325 唯一 RunID（行 2-326）
    rows = read_rows(zf)
    rids = [rows[r].get(1) for r in range(2, 327) if rows.get(r, {}).get(1)]
    if len(rids) != 325 or len(set(rids)) != 325:
        errs.append(f"RunID 数 {len(rids)}/唯一 {len(set(rids))} != 325")
    # ③ 表头 43 列逐字不变（对照原文件）
    zo = zipfile.ZipFile(XLSX)
    ro = read_rows(zo)
    hdr_new = rows.get(1, {})
    hdr_old = ro.get(1, {})
    for c in sorted(set(hdr_old) | set(hdr_new)):
        if hdr_old.get(c, "") != hdr_new.get(c, ""):
            errs.append(f"表头列 {c} 变化: {hdr_old.get(c)!r} -> {hdr_new.get(c)!r}")
    # ④ 无公式损坏（本表原本 0 公式）
    xml = zf.read(SHEET).decode("utf-8", errors="replace")
    if "<f>" in xml:
        errs.append("出现公式元素（原表无公式）")
    # ⑤ 目标单元格值正确
    for row, col, val, num in plan:
        got = rows.get(row, {}).get(col)
        want = str(val) if num else str(val)
        if got != want:
            errs.append(f"{cell_ref(col, row)} 期望 {want!r} 实得 {got!r}")
    # ⑥ 未计划的目标行 RunID 列未被触碰（行号取矩阵实际解析值）
    rid_row = {rows[r].get(1, ""): r for r in rows if rows.get(r, {}).get(1)}
    for rec in draft:
        r = rid_row.get(rec["runid"])
        if r is None or rows.get(r, {}).get(1) != rec["runid"]:
            errs.append(f"{rec['runid']}: 校验文件中 RunID 行缺失/被改动")
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draft", required=True, help="回填草案 JSON（Subagent 产物）")
    ap.add_argument("--apply", action="store_true", help="执行写入（默认干跑）")
    args = ap.parse_args()
    draft = json.load(open(args.draft))
    sys.exit(apply_draft(draft, apply=args.apply))


if __name__ == "__main__":
    main()
