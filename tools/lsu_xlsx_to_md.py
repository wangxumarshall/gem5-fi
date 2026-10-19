#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gem5-fi LSU 方案工作簿 → Markdown 完整转换与校验.

用法:
  python3 tools/lsu_xlsx_to_md.py --xlsx <path.xlsx> --out-dir <dir>             # 生成
  python3 tools/lsu_xlsx_to_md.py --xlsx <path.xlsx> --out-dir <dir> --validate  # 校验（Task 2）

约定（与 docs/superpowers/plans/2026-10-19-lsu-xlsx-to-md.md 一致）:
  - 源 xlsx 只读（绝不 save）；生成/校验前后 sha256 必须不变。
  - canonical(v) = md_escape(cell_to_text(v).strip())；生成与校验共用，防漂移。
  - 全宽合并横幅行 → "### 分节横幅：" 分节；其后一行为新表表头。
  - 尾部全空行不列出，注记披露；内部空行照常列出；隐藏行列内容仍完整列出。
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, time as dtime
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

MAIN_STEM = "gem5-fi-LSU单元故障注入方案"
SUB_DOC_MIN_COLS = 9     # max_column >= 9 → 子文档
SUB_DOC_MIN_ROWS = 101   # max_row >= 101 → 子文档
RUNID_RE = re.compile(r"^[A-Z]\d{2}-F\d+-W\d+$")
META_BEGIN = "<!-- lsu-xlsx2md-metadata"
META_END = "-->"
BANNER_PREFIX = "### 分节横幅："
ANCHOR_FMT = '<a id="sheet-{idx}"></a>'
FS_UNSAFE = re.compile(r'[\\/:*?"<>|]')


# ---------- 单元格文本化与转义（生成/校验共用，单一实现） ----------

def cell_to_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, dtime):
        return v.strftime("%H:%M:%S")
    return str(v)


def md_escape(text: str) -> str:
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "<br>")


def md_unescape(text: str) -> str:
    text = text.replace("<br>", "\n")
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == "\\" and i + 1 < n and text[i + 1] in "\\|":
            out.append(text[i + 1])
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def canonical(v) -> str:
    return md_escape(cell_to_text(v).strip())


def split_md_row(line: str) -> list:
    """把一条 MD 表格行拆回原始文本单元格（已反转义、已去边缘空白）。"""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells, cur, i, n = [], [], 0, len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n and body[i + 1] in "\\|":
            cur.append(body[i + 1])
            i += 2
        elif ch == "|":
            cells.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(ch)
            i += 1
    cells.append("".join(cur))
    return [md_unescape(c.strip()) for c in cells]


# ---------- 工作表模型 ----------

@dataclass
class SheetModel:
    name: str
    ncols: int
    nrows_raw: int          # ws.max_row（含尾部全空行）
    grid: list              # 行 1..last_nonempty 的原始值矩阵（每行长度 = ncols）
    trailing_empty: int     # 被披露而不列出的尾部全空行数
    banner_rows: dict       # 行号(1-based) -> 横幅文本（全宽单行合并）
    formulas: dict          # (row, col) -> 公式串
    merged: list            # 合并区间串列表，如 ['A21:E21']
    hidden_rows: list
    hidden_cols: list       # 列号列表
    sheet_state: str        # visible / hidden / veryHidden
    nonempty: int
    runids: list            # 首列中匹配 RUNID_RE 的值（行 2 起）


def build_sheet_model(ws, wsf) -> SheetModel:
    ncols, nrows = ws.max_column, ws.max_row
    grid = [[ws.cell(row=r, column=c).value for c in range(1, ncols + 1)]
            for r in range(1, nrows + 1)]
    last_nonempty = 0
    for idx, row in enumerate(grid, 1):
        if any(v is not None and v != "" for v in row):
            last_nonempty = idx
    trailing_empty = nrows - last_nonempty
    grid = grid[:last_nonempty]
    banner_rows = {}
    merged = []
    for rng in ws.merged_cells.ranges:
        merged.append(str(rng))
        if rng.min_col == 1 and rng.max_col == ncols and rng.min_row == rng.max_row:
            banner_rows[rng.min_row] = cell_to_text(
                ws.cell(row=rng.min_row, column=1).value).strip()
    formulas = {}
    for row in wsf.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("="):
                formulas[(c.row, c.column)] = c.value
    hidden_rows = sorted(r for r, d in ws.row_dimensions.items() if d.hidden)
    hidden_cols = sorted(column_index_from_string(k)
                         for k, d in ws.column_dimensions.items() if d.hidden)
    nonempty = sum(1 for row in grid for v in row if v is not None and v != "")
    runids = [str(row[0]).strip() for row in grid[1:]
              if row and isinstance(row[0], str) and RUNID_RE.match(str(row[0]).strip())]
    return SheetModel(name=ws.title, ncols=ncols, nrows_raw=nrows, grid=grid,
                      trailing_empty=trailing_empty, banner_rows=banner_rows,
                      formulas=formulas, merged=merged, hidden_rows=hidden_rows,
                      hidden_cols=hidden_cols, sheet_state=ws.sheet_state,
                      nonempty=nonempty, runids=runids)


# ---------- 渲染 ----------

def render_table(header: list, data: list) -> list:
    lines = ["| " + " | ".join(canonical(v) for v in header) + " |",
             "|" + "---|" * len(header)]
    for row in data:
        lines.append("| " + " | ".join(canonical(v) for v in row) + " |")
    return lines


def render_sheet_section(m: SheetModel, idx: int) -> str:
    lines = [ANCHOR_FMT.format(idx=idx), f"## {m.name}"]
    runid_note = f"；RunID {len(m.runids)}（唯一）" if m.runids else ""
    state_note = "" if m.sheet_state == "visible" else f"；工作表状态={m.sheet_state}（内容仍完整转换）"
    lines.append(f"> {m.ncols} 列 × {m.nrows_raw} 行；非空单元格 {m.nonempty}{runid_note}{state_note}")
    lines.append("")
    # 按全宽横幅分节；行 1 恒为首个表的表头（12 表实测如此）
    segs = []
    header = m.grid[0] if m.grid else []
    data, expect_header, seg_banner = [], False, None
    for ridx in range(2, len(m.grid) + 1):
        row = m.grid[ridx - 1]
        if ridx in m.banner_rows:
            segs.append((seg_banner, header, data))
            seg_banner, header, data, expect_header = m.banner_rows[ridx], [], [], True
        elif expect_header:
            header, expect_header = row, False
        else:
            data.append(row)
    if m.grid:
        segs.append((seg_banner, header, data))
    for banner, header, data in segs:
        if banner is not None:
            lines.append(BANNER_PREFIX + md_escape(banner))
            lines.append("")
        if header:
            lines.extend(render_table(header, data))
            lines.append("")
    notes = []
    if m.trailing_empty:
        notes.append(f"尾部全空行 {m.trailing_empty} 行（源行 {len(m.grid) + 1}–{m.nrows_raw}）未列出，内容为空")
    if m.hidden_rows:
        notes.append(f"隐藏行 {m.hidden_rows}：内容仍完整列出")
    if m.hidden_cols:
        letters = [get_column_letter(c) for c in m.hidden_cols]
        notes.append(f"隐藏列 {letters}：内容仍完整列出")
    if m.merged:
        notes.append(f"合并单元格：{', '.join(m.merged)}（全宽横幅已作分节标题；其余仅锚单元格有值）")
    for (r, c), f in sorted(m.formulas.items()):
        disp = canonical(m.grid[r - 1][c - 1]) if r - 1 < len(m.grid) else ""
        shown = disp if disp else "（无缓存值，显示为空）"
        notes.append(f"公式 {get_column_letter(c)}{r}：`{f}` → 当前显示值：{shown}")
    if notes:
        lines.append("注：" + "；".join(notes) + "。")
        lines.append("")
    return "\n".join(lines)


def subdoc_filename(name: str, idx: int) -> str:
    m = re.match(r"^(\d+)\.(.+)$", name)
    no = f"{int(m.group(1)):02d}" if m else f"{idx:02d}"
    title = FS_UNSAFE.sub("_", m.group(2)) if m else FS_UNSAFE.sub("_", name)
    return f"{MAIN_STEM}-{no}-{title}.md"


def is_subdoc(m: SheetModel) -> bool:
    return m.ncols >= SUB_DOC_MIN_COLS or m.nrows_raw >= SUB_DOC_MIN_ROWS


def parse_metadata(text: str) -> dict:
    m = re.search(re.escape(META_BEGIN) + r"\s*\n(.*?)\n\s*" + re.escape(META_END),
                  text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


# ---------- generate ----------

def generate(xlsx_path: Path, out_dir: Path) -> dict:
    sha = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    stat = xlsx_path.stat()
    wbv = openpyxl.load_workbook(xlsx_path, data_only=True)   # 显示值（公式取缓存）
    wbf = openpyxl.load_workbook(xlsx_path, data_only=False)  # 原始（探公式）
    models = [build_sheet_model(wbv[name], wbf[name]) for name in wbv.sheetnames]
    # V0 前置不变式：字面 '<br>' 会让往返解析失真——响亮中止而非静默出错
    for m in models:
        for row in m.grid:
            for v in row:
                if isinstance(v, str) and "<br>" in v:
                    sys.exit(f"[ABORT] 工作表 {m.name!r} 含字面 '<br>'，"
                             f"需先扩展 md_escape/md_unescape 规则再转换")
    out_dir.mkdir(parents=True, exist_ok=True)
    toc_rows, inline_sections, written = [], [], []
    for idx, m in enumerate(models):
        if is_subdoc(m):
            fname = subdoc_filename(m.name, idx)
            text = (f"# {m.name}（{MAIN_STEM} 子表）\n\n"
                    f"> 源工作表 `{m.name}`（{m.ncols} 列 × {m.nrows_raw} 行）；"
                    f"返回[主文档]({MAIN_STEM}.md)。\n\n"
                    + render_sheet_section(m, idx))
            p = out_dir / fname
            p.write_text(text, encoding="utf-8")
            written.append(p)
            where = f"[子文档 {fname}]({fname})"
        else:
            inline_sections.append(render_sheet_section(m, idx))
            where = f"[本文 {m.name}](#sheet-{idx})"
        toc_rows.append(f"| {idx} | {m.name} | {m.ncols} 列 × {m.nrows_raw} 行 | {where} |")
    s7 = next((m for m in models if m.name == "7.展开执行矩阵"), None)
    s9 = next((m for m in models if m.name == "9.逐RunID传播监控"), None)
    meta = (f"{META_BEGIN}\n"
            f"Source-File: {xlsx_path.name}\n"
            f"Source-SHA256: {sha}\n"
            f"Source-MTime-Local: {datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds')}\n"
            f"Source-Size-Bytes: {stat.st_size}\n"
            f"Generated-At-Local: {datetime.now().isoformat(timespec='seconds')}\n"
            f"Sheet-Count: {len(models)}\n"
            f"RunID-Count-Sheet7: {len(s7.runids) if s7 else 'n/a'}\n"
            f"RunID-Count-Sheet9: {len(s9.runids) if s9 else 'n/a'}\n"
            f"Tool: tools/lsu_xlsx_to_md.py\n"
            f"{META_END}")
    main_doc = [f"# {MAIN_STEM}（Markdown 转换版）", "", meta, "",
                "> 本文档由上述 SHA256 对应的 xlsx 工作簿**自动完整转换**生成；源文件未被修改。",
                "> 转换规则：单元格换行→`<br>`；`|`→`\\|`；全宽合并横幅→`### 分节横幅`；"
                "尾部全空行不列出（各节注记披露）；隐藏行列内容仍完整列出。",
                "", "## 目录", "", "| # | 工作表 | 规模 | 位置 |", "|---|--------|------|------|"]
    main_doc.extend(toc_rows)
    main_doc.append("")
    main_doc.extend(inline_sections)
    p = out_dir / f"{MAIN_STEM}.md"
    p.write_text("\n".join(main_doc) + "\n", encoding="utf-8")
    written.insert(0, p)
    print(f"[generate] 源: {xlsx_path} sha256={sha[:16]}…")
    for f in written:
        print(f"[generate] 写出 {f} ({f.stat().st_size} bytes)")
    print(f"[generate] 工作表 {len(models)}；子文档 {sum(1 for m in models if is_subdoc(m))}；"
          f"RunID 表7={len(s7.runids) if s7 else 'n/a'} 表9={len(s9.runids) if s9 else 'n/a'}")
    return {"sheet_count": len(models), "written": [str(f) for f in written],
            "runid_sheet7": len(s7.runids) if s7 else None,
            "runid_sheet9": len(s9.runids) if s9 else None}


# ---------- CLI ----------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="gem5-fi LSU 方案工作簿 xlsx→Markdown 转换与校验")
    ap.add_argument("--xlsx", required=True, help="源工作簿路径（只读，绝不修改）")
    ap.add_argument("--out-dir", required=True, help="Markdown 输出目录")
    ap.add_argument("--validate", action="store_true", help="校验 out-dir 中已生成文档（Task 2 实现）")
    a = ap.parse_args(argv)
    if a.validate:
        sys.exit("[ABORT] --validate 模式在 Task 2 实现（当前构建只有 generate）")
    generate(Path(a.xlsx), Path(a.out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
