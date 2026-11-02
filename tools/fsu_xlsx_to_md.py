#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gem5-fi FSU 方案工作簿 → Markdown 完整转换与校验.

用法:
  python3 tools/fsu_xlsx_to_md.py --xlsx <path.xlsx> --out-dir <dir>
  python3 tools/fsu_xlsx_to_md.py --xlsx <path.xlsx> --out-dir <dir> --validate

与 LSU 转换器（tools/lsu_xlsx_to_md.py）的关系:
  - 复用其“canonical 单一实现 + 回读逐格比较”的核心思路；
  - 不硬编码 LSU 文件名 / RunID 正则 / 关键列，改为 FSU 常量与自动 RunID 列探测；
  - 新增空行标记 `<!-- blank-row -->`，以正确处理 FSU 工作簿
    “空行 → 全宽横幅 → 空行 → 表头”的版式（LSU 换行器会把空行误当表头）。

约定:
  - 源 xlsx 只读（绝不 save）；生成/校验前后 sha256 必须不变。
  - canonical(v) = md_escape(cell_to_text(v).strip())；生成与校验共用。
  - 全宽合并横幅行 → "### 分节横幅："；空行 → "<!-- blank-row -->"。
  - 尾部全空行不列出，注记披露；内部空行以标记保留；隐藏行列内容完整列出。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time as dtime
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter

MAIN_STEM = "gem5-fi-FSU单元故障注入方案_逐RunID传播监控"
SUB_DOC_MIN_COLS = 9     # max_column >= 9 → 子文档
SUB_DOC_MIN_ROWS = 101   # max_row >= 101 → 子文档（含尾部空行，保守拆分）
RUNID_RE = re.compile(r"^FSU-[A-Za-z0-9]+-F\d+-W\d+$")
RUNID_SHEETS = ("7.展开执行矩阵", "9.逐RunID传播监控")
EXPECTED_SHEETS = 12
EXPECTED_RUNIDS = 173
META_BEGIN = "<!-- fsu-xlsx2md-metadata"
META_END = "-->"
BANNER_PREFIX = "### 分节横幅："
BLANK_MARKER = "<!-- blank-row -->"
ANCHOR_FMT = '<a id="sheet-{idx}"></a>'
FS_UNSAFE = re.compile(r'[\\/:*?"<>|]')

# 关键列非空计数（表名 → 表头名列表）；仅用于额外一致性证据
KEY_COLUMNS = {
    "7.展开执行矩阵": ["RunID", "模型ID", "频率", "负载ID", "传播监控", "预期结果"],
    "9.逐RunID传播监控": ["RunID", "模型ID", "频率",
                       "完整传播路径（按顺序）", "必监控单元/事件/指标"],
    "10.源码监控映射": ["模型ID", "实现状态"],
    "11.传播事件字段规范": ["字段"],
}


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
    merged: list            # 合并区间串列表
    hidden_rows: list
    hidden_cols: list
    sheet_state: str
    nonempty: int
    runid_header_row: int | None
    runid_col: int | None
    runids: list = field(default_factory=list)


def _row_is_blank(row) -> bool:
    return all(v is None or v == "" for v in row)


def build_sheet_model(ws, wsf) -> SheetModel:
    ncols, nrows = ws.max_column, ws.max_row
    grid = [[ws.cell(row=r, column=c).value for c in range(1, ncols + 1)]
            for r in range(1, nrows + 1)]
    last_nonempty = 0
    for idx, row in enumerate(grid, 1):
        if not _row_is_blank(row):
            last_nonempty = idx
    trailing_empty = nrows - last_nonempty
    grid = grid[:last_nonempty]
    banner_rows = {}
    merged = []
    for rng in ws.merged_cells.ranges:
        merged.append(str(rng))
        if (rng.min_col == 1 and rng.max_col == ncols
                and rng.min_row == rng.max_row):
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

    # RunID 列自动探测：首个“某列文本恰为 RunID”的行即表头行
    runid_header_row, runid_col = None, None
    for ridx, row in enumerate(grid, 1):
        for cidx, v in enumerate(row, 1):
            if cell_to_text(v).strip().lower() == "runid":
                runid_header_row, runid_col = ridx, cidx
                break
        if runid_header_row is not None:
            break
    runids = []
    if runid_header_row is not None:
        for row in grid[runid_header_row:]:
            if runid_col - 1 < len(row):
                v = row[runid_col - 1]
                if isinstance(v, str) and RUNID_RE.match(v.strip()):
                    runids.append(v.strip())
    else:
        # 回退：按 LSU 口径扫描首列
        for row in grid:
            if row and isinstance(row[0], str) and RUNID_RE.match(row[0].strip()):
                runids.append(row[0].strip())
    return SheetModel(name=ws.title, ncols=ncols, nrows_raw=nrows, grid=grid,
                      trailing_empty=trailing_empty, banner_rows=banner_rows,
                      formulas=formulas, merged=merged, hidden_rows=hidden_rows,
                      hidden_cols=hidden_cols, sheet_state=ws.sheet_state,
                      nonempty=nonempty, runid_header_row=runid_header_row,
                      runid_col=runid_col, runids=runids)


# ---------- 渲染 ----------

def render_table(header: list, data: list) -> list:
    lines = ["| " + " | ".join(canonical(v) for v in header) + " |",
             "|" + "---|" * len(header)]
    for row in data:
        lines.append("| " + " | ".join(canonical(v) for v in row) + " |")
    return lines


def render_sheet_section(m: SheetModel, idx: int) -> str:
    lines = [ANCHOR_FMT.format(idx=idx), f"## {m.name}"]
    runid_note = f"；RunID {len(m.runids)}（唯一 {len(set(m.runids))}）" if m.runids else ""
    state_note = "" if m.sheet_state == "visible" else f"；工作表状态={m.sheet_state}（内容仍完整转换）"
    lines.append(f"> {m.ncols} 列 × {m.nrows_raw} 行；非空单元格 {m.nonempty}{runid_note}{state_note}")
    lines.append("")

    segments = []          # ("banner", text) / ("blank", None) / ("table", (header,data))
    header, data = None, []

    def flush_table():
        nonlocal header, data
        if header is not None:
            segments.append(("table", (header, data)))
        header, data = None, []

    for ridx, row in enumerate(m.grid, 1):
        if ridx in m.banner_rows:
            flush_table()
            segments.append(("banner", m.banner_rows[ridx]))
        elif _row_is_blank(row):
            if header is None:
                flush_table()
                segments.append(("blank", None))
            else:
                data.append(row)       # 表内空行：作为空数据行保留
        elif header is None:
            header, data = row, []
        else:
            data.append(row)
    flush_table()

    for kind, payload in segments:
        if kind == "blank":
            lines.extend([BLANK_MARKER, ""])
        elif kind == "banner":
            lines.extend([BANNER_PREFIX + md_escape(payload), ""])
        else:
            header, data = payload
            lines.extend(render_table(header, data))
            lines.append("")

    notes = []
    if m.trailing_empty:
        notes.append(f"尾部全空行 {m.trailing_empty} 行"
                     f"（源行 {len(m.grid) + 1}–{m.nrows_raw}）未列出，内容为空")
    if m.hidden_rows:
        notes.append(f"隐藏行 {m.hidden_rows}：内容仍完整列出")
    if m.hidden_cols:
        letters = [get_column_letter(c) for c in m.hidden_cols]
        notes.append(f"隐藏列 {'、'.join(letters)}：内容仍完整列出")
    if m.merged:
        notes.append(f"合并单元格：{', '.join(m.merged)}"
                     f"（全宽横幅已作分节标题；其余仅锚单元格有值）")
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

def _precheck_literal_hazards(models: list) -> None:
    """V0 前置不变式：会让往返解析失真的字面内容——响亮中止。"""
    for m in models:
        for row in m.grid:
            for v in row:
                if not isinstance(v, str):
                    continue
                if "<br>" in v:
                    sys.exit(f"[ABORT] 工作表 {m.name!r} 含字面 '<br>'，"
                             f"需先扩展 md_escape/md_unescape 规则再转换")
                if v != v.strip():
                    sys.exit(f"[ABORT] 工作表 {m.name!r} 含边缘空白单元格 {v!r}，"
                             f"canonical() 会丢失空白，需先处理")


def load_models(xlsx_path: Path):
    wbv = openpyxl.load_workbook(xlsx_path, data_only=True)   # 显示值（公式取缓存）
    wbf = openpyxl.load_workbook(xlsx_path, data_only=False)  # 原始（探公式）
    return list(wbv.sheetnames), [build_sheet_model(wbv[n], wbf[n]) for n in wbv.sheetnames]


def write_runids(m: SheetModel, out_dir: Path) -> tuple:
    """表 7 展开执行矩阵 → runids.json / runids.csv（机器可读清单）。"""
    if m.runid_header_row is None:
        return None, None
    header = [canonical(v) for v in m.grid[m.runid_header_row - 1]]
    rows = []
    for row in m.grid[m.runid_header_row:]:
        rid = row[m.runid_col - 1] if m.runid_col - 1 < len(row) else None
        if not (isinstance(rid, str) and RUNID_RE.match(rid.strip())):
            continue
        item = {header[i]: cell_to_text(row[i]) for i in range(len(header))}
        parts = rid.strip().split("-")
        item["_parsed"] = {"model": parts[1], "freq": parts[2], "load": parts[3]}
        rows.append(item)
    jpath = out_dir / "runids.json"
    cpath = out_dir / "runids.csv"
    jpath.write_text(json.dumps({"sheet": m.name, "count": len(rows),
                                 "runids": rows}, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    with cpath.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header + ["_parsed"], lineterminator="\n")
        w.writeheader()
        for item in rows:
            w.writerow({**{k: item.get(k, "") for k in header},
                        "_parsed": json.dumps(item["_parsed"], ensure_ascii=False)})
    return jpath, cpath


def generate(xlsx_path: Path, out_dir: Path) -> dict:
    sha_before = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    stat = xlsx_path.stat()
    names, models = load_models(xlsx_path)
    _precheck_literal_hazards(models)
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
    by_name = {m.name: m for m in models}
    s7 = by_name.get(RUNID_SHEETS[0])
    s9 = by_name.get(RUNID_SHEETS[1])
    meta = (f"{META_BEGIN}\n"
            f"Source-File: {xlsx_path.name}\n"
            f"Source-SHA256: {sha_before}\n"
            f"Source-MTime-Local: {datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds')}\n"
            f"Source-Size-Bytes: {stat.st_size}\n"
            f"Generated-At-Local: {datetime.now().isoformat(timespec='seconds')}\n"
            f"Sheet-Count: {len(models)}\n"
            f"RunID-Count-Sheet7: {len(s7.runids) if s7 else 'n/a'}\n"
            f"RunID-Count-Sheet9: {len(s9.runids) if s9 else 'n/a'}\n"
            f"RunID-Sets-Equal: "
            f"{'true' if s7 and s9 and set(s7.runids) == set(s9.runids) else 'false'}\n"
            f"Tool: tools/fsu_xlsx_to_md.py\n"
            f"{META_END}")
    main_doc = [f"# {MAIN_STEM}（Markdown 转换版）", "", meta, "",
                "> 本文档由上述 SHA256 对应的 xlsx 工作簿**自动完整转换**生成；源文件未被修改。",
                "> 转换规则：单元格换行→`<br>`；`|`→`\\|`；全宽合并横幅→`### 分节横幅`；"
                "空行→`<!-- blank-row -->`；尾部全空行不列出（各节注记披露）；"
                "隐藏行列内容仍完整列出。",
                "", "## 目录", "", "| # | 工作表 | 规模 | 位置 |", "|---|--------|------|------|"]
    main_doc.extend(toc_rows)
    main_doc.append("")
    main_doc.extend(inline_sections)
    p = out_dir / f"{MAIN_STEM}.md"
    p.write_text("\n".join(main_doc), encoding="utf-8")
    written.insert(0, p)

    runid_files = (None, None)
    if s7 is not None:
        runid_files = write_runids(s7, out_dir)

    sha_after = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    if sha_after != sha_before:
        sys.exit("[ABORT] 生成过程中源 xlsx SHA-256 发生变化")
    print(f"[generate] 源: {xlsx_path} sha256={sha_before}")
    for f in written:
        print(f"[generate] 写出 {f} ({f.stat().st_size} bytes)")
    if runid_files[0]:
        print(f"[generate] 写出 {runid_files[0]} / {runid_files[1]}")
    print(f"[generate] 工作表 {len(models)}；子文档 "
          f"{sum(1 for m in models if is_subdoc(m))}；"
          f"RunID 表7={len(s7.runids) if s7 else 'n/a'} 表9={len(s9.runids) if s9 else 'n/a'}")
    return {"xlsx": str(xlsx_path), "sha_before": sha_before, "sha_after": sha_after,
            "size": stat.st_size, "names": names, "models": models,
            "written": [str(f) for f in written],
            "runid_files": [str(f) for f in runid_files if f]}


# ---------- validate ----------

def parse_md_tables(text: str) -> list:
    """小节文本 → 原始文本网格（行序 = 源行序；横幅/空行为单格/零格行）。"""
    grid, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            cells = [split_md_row(l) for l in block]
            if len(cells) >= 2:                      # 表头 + 分隔行 + 数据…
                grid.append(cells[0])
                grid.extend(cells[2:])
        elif line.startswith(BANNER_PREFIX):
            grid.append([md_unescape(line[len(BANNER_PREFIX):].strip())])
            i += 1
        elif line.strip() == BLANK_MARKER:
            grid.append([])
            i += 1
        else:
            i += 1
    return grid


def split_main_sections(main_text: str) -> dict:
    parts = re.split(r'^<a id="sheet-(\d+)"></a>$', main_text, flags=re.M)
    return {int(parts[j]): parts[j + 1] for j in range(1, len(parts), 2)}


def md_row_to_canonical(cells: list, ncols: int) -> list:
    out = [md_escape(c.strip()) for c in cells]
    if len(out) < ncols:
        out += [""] * (ncols - len(out))
    return out[:ncols]


def validate(xlsx_path: Path, out_dir: Path, expect_runids: int | None = EXPECTED_RUNIDS,
             expect_sheets: int | None = EXPECTED_SHEETS) -> tuple:
    checks, failures = [], []

    def check(name, ok):
        checks.append((name, ok))
        if not ok:
            failures.append(name)

    sha_before = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    main_path = out_dir / f"{MAIN_STEM}.md"
    if not main_path.exists():
        print(f"[validate] 缺主文档 {main_path}")
        return 1, [("主文档存在", False)]
    main_text = main_path.read_text(encoding="utf-8")
    meta = parse_metadata(main_text)

    names, models = load_models(xlsx_path)
    by_name = {m.name: m for m in models}

    # V0 源不变式与内容特征
    lit_br = sum(1 for m in models for row in m.grid for v in row
                 if isinstance(v, str) and "<br>" in v)
    edge_ws = sum(1 for m in models for row in m.grid for v in row
                  if isinstance(v, str) and v != v.strip())
    check(f"V0 无字面 '<br>' 单元格（实测 {lit_br}）", lit_br == 0)
    check(f"V0 无边缘空白单元格（实测 {edge_ws}）", edge_ws == 0)
    n_formula = sum(len(m.formulas) for m in models)
    n_hidden_r = sum(len(m.hidden_rows) for m in models)
    n_hidden_c = sum(len(m.hidden_cols) for m in models)
    n_hidden_sh = sum(1 for m in models if m.sheet_state != "visible")
    n_merged = sum(len(m.merged) for m in models)
    n_nonempty = sum(m.nonempty for m in models)
    checks.append((f"V0 报告: 非空 {n_nonempty}；合并 {n_merged}；公式 {n_formula}；"
                   f"隐藏行 {n_hidden_r}；隐藏列 {n_hidden_c}；非 visible 表 {n_hidden_sh}", True))
    if expect_sheets is not None:
        check(f"V0 工作表数 == {expect_sheets}（实测 {len(names)}）",
              len(names) == expect_sheets)

    # V5 源绑定
    check("V5 元数据 Source-SHA256 == 当前源", meta.get("Source-SHA256") == sha_before)
    check("V5 元数据 Sheet-Count == 实际", meta.get("Sheet-Count") == str(len(names)))

    # 定位每个表的 MD 文本
    sections = split_main_sections(main_text)
    md_of = {}
    for idx, name in enumerate(names):
        m = by_name[name]
        if is_subdoc(m):
            p = out_dir / subdoc_filename(name, idx)
            if not p.exists():
                check(f"V1 [{name}] 子文档存在", False)
                continue
            check(f"V1 [{name}] 子文档存在", True)
            md_of[name] = p.read_text(encoding="utf-8")
        else:
            md_of[name] = sections.get(idx, "")
            check(f"V1 [{name}] 内联节存在", bool(md_of[name]))

    # V1 目录链接可解析
    toc_lines = [l for l in main_text.splitlines()
                 if l.startswith("| ") and ("](#" in l or "](gem5-fi-" in l)]
    n_toc = len(toc_lines)
    check(f"V1 目录行数 == 工作表数（{n_toc} vs {len(names)}）", n_toc == len(names))
    bad_links = 0
    for l in toc_lines:
        for target in re.findall(r"\]\(([^)]+)\)", l):
            if target.startswith("#"):
                if f'<a id="{target[1:]}"></a>' not in main_text:
                    bad_links += 1
            else:
                if not (out_dir / target).exists():
                    bad_links += 1
    check(f"V1 目录链接全部可解析（断链 {bad_links}）", bad_links == 0)

    # V1b 孤儿子文档
    expected_subs = {subdoc_filename(name, idx) for idx, name in enumerate(names)
                     if is_subdoc(by_name[name])}
    actual_subs = {p.name for p in out_dir.glob(f"{MAIN_STEM}-*.md")}
    check(f"V1 无孤儿子文档（多出 {sorted(actual_subs - expected_subs)}）",
          actual_subs == expected_subs)

    # 每表 canonical 网格（xlsx 侧）
    xcan = {n: [[canonical(v) for v in row] for row in m.grid]
            for n, m in by_name.items()}

    # V3 全量往返 + V7 披露注记
    for name in names:
        m = by_name[name]
        parsed = parse_md_tables(md_of.get(name, ""))
        pcan = [md_row_to_canonical(r, m.ncols) for r in parsed]
        if len(pcan) != len(m.grid):
            check(f"V3 [{name}] 行数一致（xlsx {len(m.grid)} vs md {len(pcan)}）", False)
            continue
        diff = next((r for r, (x, p) in enumerate(zip(xcan[name], pcan), 1) if x != p), None)
        check(f"V3 [{name}] 逐格相等（{m.nonempty} 非空格）", diff is None)
        if diff:
            print(f"    V3[{name}] 首个差异行 {diff}: xlsx={xcan[name][diff-1][:3]} "
                  f"md={pcan[diff-1][:3]}")
        if m.trailing_empty:
            check(f"V7 [{name}] 尾部空行注记（{m.trailing_empty} 行）",
                  f"尾部全空行 {m.trailing_empty} 行" in md_of.get(name, ""))
        if m.merged:
            check(f"V7 [{name}] 合并单元格注记",
                  all(r in md_of.get(name, "") for r in m.merged))
        if m.formulas:
            check(f"V7 [{name}] 公式注记（{len(m.formulas)} 条）",
                  "公式 " in md_of.get(name, ""))

    # V2 RunID（对每个含 RunID 的表）
    rid_sets = {}
    for name in names:
        m = by_name[name]
        if not m.runids:
            continue
        parsed = parse_md_tables(md_of.get(name, ""))
        col = (m.runid_col or 1) - 1
        md_rids = [r[col] for r in parsed
                   if col < len(r) and RUNID_RE.match(r[col])]
        check(f"V2 [{name}] RunID 数量一致（xlsx {len(m.runids)} vs md {len(md_rids)}）",
              len(md_rids) == len(m.runids))
        check(f"V2 [{name}] RunID 无重复（{len(md_rids)}/{len(set(md_rids))}）",
              len(md_rids) == len(set(md_rids)))
        check(f"V2 [{name}] RunID 集合与源一致", set(md_rids) == set(m.runids))
        rid_sets[name] = set(m.runids)
    for name in RUNID_SHEETS:
        if name in by_name:
            m = by_name[name]
            if expect_runids is not None:
                check(f"V2 [{name}] RunID 数 == {expect_runids}（实测 {len(m.runids)}）",
                      len(m.runids) == expect_runids)
            check(f"V2 [{name}] 源内 RunID 唯一（{len(m.runids)}/{len(set(m.runids))}）",
                  len(m.runids) == len(set(m.runids)))
    if all(n in rid_sets for n in RUNID_SHEETS):
        check("V2 表7/表9 RunID 集合相等",
              rid_sets[RUNID_SHEETS[0]] == rid_sets[RUNID_SHEETS[1]])
    else:
        check(f"V2 表7/表9 均含 RunID（{sorted(rid_sets)}）", False)

    # V4 关键字段非空计数
    for name, wants in KEY_COLUMNS.items():
        if name not in by_name:
            checks.append((f"V4 [{name}] n/a（源无此表）", True))
            continue
        m, parsed = by_name[name], parse_md_tables(md_of.get(name, ""))
        pcan = [md_row_to_canonical(r, m.ncols) for r in parsed]
        hdr = xcan[name][0] if xcan[name] else []
        for want in wants:
            ci = next((i for i, h in enumerate(hdr) if h == canonical(want)), None)
            if ci is None:
                # 表头可能位于横幅之后：在表头行中再找一次
                hrow = m.runid_header_row
                if hrow:
                    hdr2 = xcan[name][hrow - 1]
                    ci = next((i for i, h in enumerate(hdr2) if h == canonical(want)), None)
            if ci is None:
                check(f"V4 [{name}][{want}] 找到列", False)
                continue
            n_x = sum(1 for row in xcan[name] if ci < len(row) and row[ci])
            n_m = sum(1 for row in pcan if ci < len(row) and row[ci])
            check(f"V4 [{name}][{want}] 非空 xlsx={n_x} md={n_m}", n_x == n_m)

    # V6 校验期间源未被修改
    sha_after = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    check("V6 校验前后源 sha256 一致（只读证明）", sha_after == sha_before)

    print("=" * 72)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print("=" * 72)
    if failures:
        print(f"VALIDATE FAIL（{len(failures)} 项失败）:")
        for f in failures:
            print(f"  - {f}")
        return 1, checks
    print("ALL PASS")
    return 0, checks


# ---------- 转换报告 ----------

def write_report(xlsx_path: Path, out_dir: Path, stats: dict | None,
                 rc: int, checks: list, report_path: Path) -> None:
    names, models = load_models(xlsx_path)
    by_name = {m.name: m for m in models}
    sha = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    stat = xlsx_path.stat()
    s7, s9 = by_name.get(RUNID_SHEETS[0]), by_name.get(RUNID_SHEETS[1])
    lines = ["# FSU 工作簿 → Markdown 转换报告", "",
             f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}；"
             f"工具：`tools/fsu_xlsx_to_md.py`。", "",
             "## 1. 源文件", "",
             "| 项 | 值 |", "|---|---|",
             f"| 路径 | `{xlsx_path}` |",
             f"| 大小 | {stat.st_size} bytes |",
             f"| SHA-256 | `{sha}` |",
             "| 只读语义 | 未通过 openpyxl 保存、未改名、未修改 |", "",
             "## 2. 工作表清单", "",
             "| # | 工作表 | 列 | 行 | 非空单元格 | 状态 | 合并 | 隐藏行 | 隐藏列 | 公式 |",
             "|---|--------|----|----|-----------|------|------|--------|--------|------|"]
    for i, m in enumerate(models, 1):
        lines.append(f"| {i} | {m.name} | {m.ncols} | {m.nrows_raw} | {m.nonempty} | "
                     f"{m.sheet_state} | {len(m.merged)} | {len(m.hidden_rows)} | "
                     f"{len(m.hidden_cols)} | {len(m.formulas)} |")
    n_nonempty = sum(m.nonempty for m in models)
    n_merged = sum(len(m.merged) for m in models)
    n_formula = sum(len(m.formulas) for m in models)
    n_hr = sum(len(m.hidden_rows) for m in models)
    n_hc = sum(len(m.hidden_cols) for m in models)
    lines += ["", "## 3. 内容统计", "",
              f"- 工作表数：{len(models)}",
              f"- 非空单元格总数：{n_nonempty}",
              f"- 合并区域：{n_merged}",
              f"- 公式：{n_formula}",
              f"- 隐藏行：{n_hr}",
              f"- 隐藏列：{n_hc}", "",
              "## 4. RunID 检查", "",
              "| 检查 | 结果 |", "|---|---|"]
    if s7 and s9:
        set7, set9 = set(s7.runids), set(s9.runids)
        lines += [f"| 表 7 `{s7.name}` RunID 数 | {len(s7.runids)} |",
                  f"| 表 7 RunID 唯一数 | {len(set7)} |",
                  f"| 表 9 `{s9.name}` RunID 数 | {len(s9.runids)} |",
                  f"| 表 9 RunID 唯一数 | {len(set9)} |",
                  f"| 表 7/表 9 集合完全相等 | {set7 == set9} |",
                  f"| 两表并集唯一 RunID 数 | {len(set7 | set9)} |",
                  f"| 仅表 7 有 | {sorted(set7 - set9) or '无'} |",
                  f"| 仅表 9 有 | {sorted(set9 - set7) or '无'} |"]
        models7 = sorted({r.split('-')[1] for r in s7.runids})
        lines.append(f"| 表 7 模型数 | {len(models7)} |")
    else:
        lines.append("| 表 7/表 9 | 缺失 |")
    lines += ["", "## 5. 生成文件", ""]
    if stats:
        for f in stats["written"]:
            lines.append(f"- `{f}`")
        for f in stats.get("runid_files", []):
            lines.append(f"- `{f}`")
    else:
        for p in sorted(out_dir.glob("*.md")):
            lines.append(f"- `{p}`")
    lines += ["", "## 6. 全量回读校验", "",
              "| 检查 | 结果 |", "|---|---|"]
    for name, ok in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    lines += ["", f"**结论：{'ALL PASS' if rc == 0 else 'FAIL'}**", ""]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] 写出 {report_path}")


# ---------- CLI ----------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="gem5-fi FSU 方案工作簿 xlsx→Markdown 转换与校验")
    ap.add_argument("--xlsx", required=True, help="源工作簿路径（只读，绝不修改）")
    ap.add_argument("--out-dir", required=True, help="Markdown 输出目录")
    ap.add_argument("--validate", action="store_true", help="校验 out-dir 中已生成文档")
    ap.add_argument("--expect-runids", type=int, default=EXPECTED_RUNIDS,
                    help=f"表7/表9 期望 RunID 数（默认 {EXPECTED_RUNIDS}；0=不检查）")
    ap.add_argument("--expect-sheets", type=int, default=EXPECTED_SHEETS,
                    help=f"期望工作表数（默认 {EXPECTED_SHEETS}；0=不检查）")
    ap.add_argument("--report", default=None,
                    help="转换报告输出路径（默认 <out-dir>/CONVERSION_REPORT.md）")
    a = ap.parse_args(argv)
    xlsx, out_dir = Path(a.xlsx), Path(a.out_dir)
    expect_runids = a.expect_runids or None
    expect_sheets = a.expect_sheets or None
    report_path = Path(a.report) if a.report else out_dir / "CONVERSION_REPORT.md"
    if a.validate:
        rc, checks = validate(xlsx, out_dir, expect_runids, expect_sheets)
        write_report(xlsx, out_dir, None, rc, checks, report_path)
        return rc
    stats = generate(xlsx, out_dir)
    rc, checks = validate(xlsx, out_dir, expect_runids, expect_sheets)
    write_report(xlsx, out_dir, stats, rc, checks, report_path)
    return rc


if __name__ == "__main__":
    sys.exit(main())
