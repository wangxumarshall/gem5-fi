#!/usr/bin/env python3
"""P0 来源核查工具：纯标准库读取 LSU 方案 xlsx 的工作表清单与指定表内容。

仅用于 task_plan.md 允许的"Excel 来源哈希与争议核查"（G0-04 参数对照），
不作为调度输入。xlsx = zip + XML：workbook.xml 列 sheet，sharedStrings.xml
存字符串表，sheetN.xml 存单元格。
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
XLSX = "/home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"


def load_sheets(zf):
    """返回 {sheet名: (xml路径, r:id)}"""
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {}
    for rel in rels:
        rel_map[rel.get("Id")] = rel.get("Target")
    sheets = {}
    for sh in wb.iter(f"{NS}sheet"):
        name = sh.get("name")
        rid = sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = rel_map.get(rid, "")
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        sheets[name] = target
    return sheets


def load_shared_strings(zf):
    try:
        data = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    out = []
    for si in root.iter(f"{NS}si"):
        # 拼接所有 t 节点（含 rich text run）
        out.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    return out


def cell_ref_to_xy(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    col = 0
    for ch in m.group(1):
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col, int(m.group(2))


def dump_sheet(zf, path, shared, max_rows=80, max_cols=None):
    root = ET.fromstring(zf.read(path))
    rows = {}
    max_col = 0
    for c in root.iter(f"{NS}c"):
        ref = c.get("r")
        t = c.get("t")
        v = c.find(f"{NS}v")
        if v is None or v.text is None:
            val = ""
        elif t == "s":
            val = shared[int(v.text)]
        else:
            val = v.text
        col, row = cell_ref_to_xy(ref)
        rows.setdefault(row, {})[col] = val
        max_col = max(max_col, col)
    if max_cols:
        max_col = min(max_col, max_cols)
    for row in sorted(rows)[:max_rows]:
        cells = [str(rows[row].get(c, "")) for c in range(1, max_col + 1)]
        # 去掉行尾空
        while cells and cells[-1] == "":
            cells.pop()
        print(f"R{row}\t" + "\t".join(cells))


def main():
    with zipfile.ZipFile(XLSX) as zf:
        sheets = load_sheets(zf)
        print("=== 工作表清单 ===")
        for name, path in sheets.items():
            print(f"  {name} -> {path}")
        if len(sys.argv) > 1:
            target = sys.argv[1]
            if target not in sheets:
                print(f"表 '{target}' 不存在", file=sys.stderr)
                sys.exit(1)
            shared = load_shared_strings(zf)
            print(f"\n=== {target} 内容（前 {80} 行）===")
            dump_sheet(zf, sheets[target], shared)


if __name__ == "__main__":
    main()
