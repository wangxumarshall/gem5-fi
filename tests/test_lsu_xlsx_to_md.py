"""tests/test_lsu_xlsx_to_md.py — xlsx→MD 转换器单元测试（合成 fixture，不触碰真实工作簿）。"""
import hashlib
import sys
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import lsu_xlsx_to_md as x2m

MAIN = x2m.MAIN_STEM


@pytest.fixture()
def fx(tmp_path):
    """合成工作簿：0 散文单列表(换行/竖线/内部空行)、1 小表、2 全宽横幅分节表、
    3 宽表(9 列→子文档, 公式无缓存, 隐藏行)、4 RunID 表(尾部全空行)。"""
    wb = openpyxl.Workbook()
    ws0 = wb.active
    ws0.title = "0.说明与总览"
    ws0["A1"] = "标题行"
    ws0["A2"] = None                 # 内部空行（保留列出）
    ws0["A3"] = "多行\n第二行"
    ws0["A4"] = "竖线 | 内容"
    ws1 = wb.create_sheet("1.小表")
    ws1.append(["列A", "列B"])
    ws1.append(["x|y", 3])
    ws1.append([None, 4.5])
    ws2 = wb.create_sheet("2.分节表")   # 仿真实表 2：全宽横幅 + 二级表头
    ws2.append(["H1", "H2"])
    ws2.append(["a", "b"])
    ws2.append(["横幅文字"])
    ws2.merge_cells("A3:B3")
    ws2.append(["H1b", "H2b"])
    ws2.append(["c", "d"])
    ws3 = wb.create_sheet("3.宽表")     # 9 列 → 子文档
    ws3.append([f"列{i}" for i in range(9)])
    ws3["A2"] = "=1+1"                  # 公式：openpyxl 写入无缓存值
    ws3.append(["隐藏行内容"] + ["r"] * 8)
    ws3.row_dimensions[3].hidden = True
    ws4 = wb.create_sheet("4.矩阵")     # RunID 表（小列数 → 内联）
    ws4.append(["RunID", "值"])
    ws4.append(["A01-F0-W3", "v1"])
    ws4.append(["A01-F1-W3", "v2"])
    for _ in range(5):                  # 尾部全空行 5 行（空串物化单元格；openpyxl 对全 None 不建行）
        ws4.append(["", ""])
    p = tmp_path / "fixture.xlsx"
    wb.save(p)
    return p


# ---------- 纯函数 ----------

def test_cell_to_text():
    from datetime import datetime as dt
    assert x2m.cell_to_text(None) == ""
    assert x2m.cell_to_text(True) == "TRUE"
    assert x2m.cell_to_text(False) == "FALSE"
    assert x2m.cell_to_text(3) == "3"
    assert x2m.cell_to_text(4.5) == "4.5"
    assert x2m.cell_to_text("x") == "x"
    assert x2m.cell_to_text(dt(2026, 10, 19, 8, 30, 5)) == "2026-10-19 08:30:05"


def test_escape_unescape_roundtrip():
    for s in ["a|b", "a\\b", "x\ny", "a|b\\c\nd|e", "|", "||", "plain", "竖线 | 内容"]:
        esc = x2m.md_escape(s)
        assert "\n" not in esc
        assert "|" not in esc.replace("\\|", "")
        assert x2m.md_unescape(esc) == s


# ---------- generate ----------

def test_generate_writes_docs_and_source_untouched(fx, tmp_path):
    out = tmp_path / "out"
    sha0 = hashlib.sha256(fx.read_bytes()).hexdigest()
    report = x2m.generate(fx, out)
    assert hashlib.sha256(fx.read_bytes()).hexdigest() == sha0   # 源未被修改
    main = out / f"{MAIN}.md"
    assert main.exists()
    text = main.read_text(encoding="utf-8")
    for sec in ["## 0.说明与总览", "## 1.小表", "## 2.分节表", "## 4.矩阵"]:
        assert sec in text                                          # 内联节
    assert "## 3.宽表" not in text                                  # 宽表不在主文档
    sub = out / f"{MAIN}-03-宽表.md"
    assert sub.exists()
    assert "## 3.宽表" in sub.read_text(encoding="utf-8")
    assert report["sheet_count"] == 5
    meta = x2m.parse_metadata(text)
    assert meta["Source-SHA256"] == sha0
    assert meta["Sheet-Count"] == "5"


def test_multiline_and_pipe_rendering(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}.md").read_text(encoding="utf-8")
    assert "多行<br>第二行" in text        # 换行 → <br>
    assert "竖线 \\| 内容" in text         # 竖线转义
    assert "x\\|y" in text


def test_banner_split(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}.md").read_text(encoding="utf-8")
    assert x2m.BANNER_PREFIX + "横幅文字" in text   # 横幅成为分节标题
    assert "| H1b | H2b |" in text                   # 横幅后一行为新表表头
    assert "| c | d |" in text                       # 第二表数据保留
    assert "A3:B3" in text                           # 合并区间注记


def test_trailing_empty_rows_disclosed(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}.md").read_text(encoding="utf-8")
    assert "尾部全空行 5 行" in text
    for _ in range(5):
        pass  # 尾部空行本身不列表（由 V3/V7 校验兜底）


def test_formula_and_hidden_notes(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}-03-宽表.md").read_text(encoding="utf-8")
    assert "公式 A2" in text and "`=1+1`" in text and "无缓存值" in text
    assert "隐藏行 [3]" in text
    assert "| 隐藏行内容 |" in text          # 隐藏行内容仍完整列出
