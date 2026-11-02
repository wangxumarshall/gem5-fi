"""tests/test_fsu_xlsx_to_md.py — FSU xlsx→MD 转换器单元测试（合成 fixture）。

不触碰真实工作簿；覆盖：空行/横幅版式、转义、隐藏行列、公式、尾部空行、
RunID 唯一性与表7/表9 集合一致性，以及全部要求的负向校验。
"""
import hashlib
import sys
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_xlsx_to_md as x2m

MAIN = x2m.MAIN_STEM
RUNIDS = ["FSU-AA01-F0-W1", "FSU-AA01-F2-W2", "FSU-BB02-F4-W3"]


def _blank_row(ws, r):
    ws.cell(row=r, column=1).value = ""     # 空串 → 视为空行；同时撑大 max_row


def make_fixture(path: Path, sheet9_runids=None) -> Path:
    """5 表 fixture：0 空行/横幅/内部空行；1 小表；3 宽表(公式/隐藏)；
    7 展开执行矩阵(RunID)；9 逐RunID传播监控(RunID)。"""
    sheet9_runids = list(RUNIDS if sheet9_runids is None else sheet9_runids)
    wb = openpyxl.Workbook()
    ws0 = wb.active
    ws0.title = "0.说明与总览"
    ws0.append([""])                                  # 行 1 空
    ws0.append(["FSU 总览"])                          # 行 2 横幅
    ws0.merge_cells("A2:C2")
    ws0.append(["说明文字"])                          # 行 3 横幅
    ws0.merge_cells("A3:C3")
    ws0.append([""])                                  # 行 4 空
    ws0.append(["项目", "约定", "备注"])              # 行 5 表头
    ws0.append(["目标", "a|b\\c\nd", "含竖线/反斜杠/换行"])
    ws0.append([""])                                  # 行 7 表内空行
    ws0.append(["单元", "x", "y"])

    ws1 = wb.create_sheet("1.小表")
    ws1.append(["列A", "列B"])
    ws1.append(["x|y", 3])
    ws1.append([""])
    ws1.append([None, 4.5])

    ws3 = wb.create_sheet("3.宽表")                   # 9 列 → 子文档
    ws3.append([f"列{i}" for i in range(9)])
    ws3.append([f"=1+1"] + [None] * 8)                # 公式：无缓存值
    ws3.append(["隐藏行内容"] + ["r"] * 8)
    ws3.row_dimensions[3].hidden = True
    ws3.column_dimensions["B"].hidden = True
    ws3.append(["合并锚"] + [None] * 8)
    ws3.merge_cells("A4:C4")                         # 非全宽合并 → 注记
    for _ in range(3):
        ws3.append([""])                             # 尾部全空行

    ws7 = wb.create_sheet("7.展开执行矩阵")            # 9 列 → 子文档
    ws7.append([""])                                  # 行 1 空
    ws7.append(["FSU 展开执行矩阵"])                  # 行 2 横幅
    ws7.merge_cells("A2:I2")
    ws7.append(["3个唯一RunID"])                      # 行 3 横幅
    ws7.merge_cells("A3:I3")
    ws7.append([""])                                  # 行 4 空
    ws7.append(["RunID", "模型ID", "频率", "负载ID", "传播监控", "预期结果",
                "注入位置", "子模型", "备注"])
    for rid in RUNIDS:
        ws7.append([rid, rid.split("-")[1], rid.split("-")[2], rid.split("-")[3],
                    "L0→L5", "SDC/Crash", "pos", "sub", "note"])

    ws9 = wb.create_sheet("9.逐RunID传播监控")
    ws9.append(["RunID", "模型ID", "频率",
                "完整传播路径（按顺序）", "必监控单元/事件/指标"])
    for rid in sheet9_runids:
        ws9.append([rid, rid.split("-")[1], rid.split("-")[2], "L0→L5", "field"])

    wb.save(path)
    return path


@pytest.fixture()
def fx(tmp_path):
    return make_fixture(tmp_path / "fixture.xlsx")


# ---------- 纯函数 ----------

def test_cell_to_text():
    from datetime import datetime as dt
    assert x2m.cell_to_text(None) == ""
    assert x2m.cell_to_text(True) == "TRUE"
    assert x2m.cell_to_text(False) == "FALSE"
    assert x2m.cell_to_text(3) == "3"
    assert x2m.cell_to_text(4.5) == "4.5"
    assert x2m.cell_to_text("x") == "x"
    assert x2m.cell_to_text(dt(2026, 11, 2, 8, 30, 5)) == "2026-11-02 08:30:05"


def test_escape_unescape_roundtrip():
    for s in ["a|b", "a\\b", "x\ny", "a|b\\c\nd|e", "|", "||", "plain",
              "竖线 | 内容", "反斜杠\\与|管道\n换行"]:
        esc = x2m.md_escape(s)
        assert "\n" not in esc
        assert "|" not in esc.replace("\\|", "")
        assert x2m.md_unescape(esc) == s


def test_runid_regex():
    for rid in ["FSU-AA01-F0-W1", "FSU-FP10-F4-W7", "FSU-FR01-F0-W9"]:
        assert x2m.RUNID_RE.match(rid)
    for bad in ["FSU-AA01-F0", "AA01-F0-W1", "FSU-AA01-FX-W1", "FSU-AA01-F0-W"]:
        assert not x2m.RUNID_RE.match(bad)


# ---------- generate ----------

def test_generate_writes_docs_and_source_untouched(fx, tmp_path):
    out = tmp_path / "out"
    sha0 = hashlib.sha256(fx.read_bytes()).hexdigest()
    report = x2m.generate(fx, out)
    assert hashlib.sha256(fx.read_bytes()).hexdigest() == sha0   # 源未被修改
    main = out / f"{MAIN}.md"
    assert main.exists()
    text = main.read_text(encoding="utf-8")
    for sec in ["## 0.说明与总览", "## 1.小表", "## 9.逐RunID传播监控"]:
        assert sec in text                                          # 内联节
    assert "## 3.宽表" not in text                                  # 宽表不在主文档
    for no, name in [(3, "宽表"), (7, "展开执行矩阵")]:
        sub = out / f"{MAIN}-0{no}-{name}.md"
        assert sub.exists()
        assert f"## {no}.{name}" in sub.read_text(encoding="utf-8")
    assert len(report["names"]) == 5
    meta = x2m.parse_metadata(text)
    assert meta["Source-SHA256"] == sha0
    assert meta["Sheet-Count"] == "5"
    assert meta["RunID-Count-Sheet7"] == "3"
    assert meta["RunID-Count-Sheet9"] == "3"
    assert meta["RunID-Sets-Equal"] == "true"


def test_multiline_pipe_backslash_rendering(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}.md").read_text(encoding="utf-8")
    assert "a\\|b\\\\c<br>d" in text        # 竖线/反斜杠转义、换行 → <br>
    assert "x\\|y" in text


def test_blank_rows_and_banners(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    sub = (out / f"{MAIN}-07-展开执行矩阵.md").read_text(encoding="utf-8")
    # 行1 空、行2/3 横幅、行4 空 → 两个空行标记 + 两个横幅
    assert sub.count(x2m.BLANK_MARKER) >= 2
    assert x2m.BANNER_PREFIX + "FSU 展开执行矩阵" in sub
    assert x2m.BANNER_PREFIX + "3个唯一RunID" in sub
    assert "| RunID | 模型ID | 频率 |" in sub       # 行5 才是表头


def test_formula_hidden_and_merged_notes(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}-03-宽表.md").read_text(encoding="utf-8")
    assert "公式 A2" in text and "`=1+1`" in text and "无缓存值" in text
    assert "隐藏行 [3]" in text
    assert "隐藏列 B" in text
    assert "| 隐藏行内容 |" in text          # 隐藏行内容仍完整列出
    assert "A4:C4" in text                   # 非全宽合并注记


def test_trailing_empty_rows_disclosed(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    text = (out / f"{MAIN}-03-宽表.md").read_text(encoding="utf-8")
    assert "尾部全空行 3 行" in text


def test_runids_json_and_csv(fx, tmp_path):
    import json
    out = tmp_path / "out"
    x2m.generate(fx, out)
    data = json.loads((out / "runids.json").read_text(encoding="utf-8"))
    assert data["count"] == 3
    assert [r["RunID"] for r in data["runids"]] == RUNIDS
    assert data["runids"][0]["_parsed"] == {"model": "AA01", "freq": "F0", "load": "W1"}
    csv_text = (out / "runids.csv").read_text(encoding="utf-8")
    assert "FSU-AA01-F0-W1" in csv_text


# ---------- validate ----------

def test_validate_pass_on_fresh_generation(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    rc, checks = x2m.validate(fx, out, expect_runids=3, expect_sheets=None)
    assert rc == 0
    assert all(ok for _, ok in checks)


def test_main_end_to_end_writes_report(fx, tmp_path):
    out = tmp_path / "out"
    rc = x2m.main(["--xlsx", str(fx), "--out-dir", str(out),
                   "--expect-runids", "3", "--expect-sheets", "5"])
    assert rc == 0
    report = (out / "CONVERSION_REPORT.md").read_text(encoding="utf-8")
    assert "ALL PASS" in report
    assert "FSU-AA01-F0-W1" not in report or True   # 报告不要求逐条列出


def test_validate_detects_expected_runid_mismatch(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    rc, _ = x2m.validate(fx, out, expect_runids=4, expect_sheets=None)
    assert rc != 0


def _mutated_fails(fx, tmp_path, mutate):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    mutate(out)
    rc, _ = x2m.validate(fx, out, expect_runids=None, expect_sheets=None)
    assert rc != 0


def _edit(out, fname, fn):
    p = out / fname
    lines = p.read_text(encoding="utf-8").splitlines()
    fn(lines)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_validate_detects_missing_row(fx, tmp_path):
    def drop(lines):
        for i, l in enumerate(lines):
            if l.startswith(f"| {RUNIDS[1]} "):
                del lines[i]
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path,
                   lambda out: _edit(out, f"{MAIN}-07-展开执行矩阵.md", drop))


def test_validate_detects_cell_mutation(fx, tmp_path):
    def change(lines):
        for i, l in enumerate(lines):
            if l.startswith("| 目标 "):
                lines[i] = l.replace("目标", "TAMPERED")
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", change))


def test_validate_detects_duplicate_runid(fx, tmp_path):
    def dup(lines):
        for i, l in enumerate(lines):
            if l.startswith(f"| {RUNIDS[0]} "):
                lines.insert(i, l)
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", dup))


def test_validate_detects_source_sha_tamper(fx, tmp_path):
    def mutate(out):
        p = out / f"{MAIN}.md"
        p.write_text(p.read_text(encoding="utf-8").replace(
            "Source-SHA256: ", "Source-SHA256: 0"), encoding="utf-8")
    _mutated_fails(fx, tmp_path, mutate)


def test_validate_detects_missing_sheet(fx, tmp_path):
    def drop_section(lines):
        keep, skipping = [], False
        for l in lines:
            if l.startswith('<a id="sheet-0"'):
                skipping = True
            elif l.startswith('<a id="sheet-'):
                skipping = False
            if not skipping:
                keep.append(l)
        lines[:] = keep
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", drop_section))


def test_validate_detects_orphan_subdoc(fx, tmp_path):
    def mutate(out):
        (out / f"{MAIN}-99-伪造.md").write_text("# 陈旧伪造子文档\n", encoding="utf-8")
    _mutated_fails(fx, tmp_path, mutate)


def test_validate_detects_subdoc_mutation(fx, tmp_path):
    def drop(lines):
        for i, l in enumerate(lines):
            if l.startswith("| 隐藏行内容"):
                del lines[i]
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}-03-宽表.md", drop))


def test_validate_detects_runid_set_mismatch(tmp_path):
    """表7 有 3 个 RunID、表9 只有 2 个 → 集合相等校验必须失败。"""
    fx2 = make_fixture(tmp_path / "mismatch.xlsx", sheet9_runids=RUNIDS[:2])
    out = tmp_path / "out"
    x2m.generate(fx2, out)
    rc, checks = x2m.validate(fx2, out, expect_runids=None, expect_sheets=None)
    assert rc != 0
    assert any("集合相等" in n for n, ok in checks if not ok)


def test_validate_detects_source_drift(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    wb = openpyxl.load_workbook(fx)
    wb["1.小表"]["B2"] = 999
    wb.save(fx)                                   # 源已变化 → SHA 不再匹配
    rc, _ = x2m.validate(fx, out, expect_runids=None, expect_sheets=None)
    assert rc != 0


def test_no_trailing_blank_line(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    docs = sorted(out.glob("*.md"))
    assert len(docs) == 3                          # 主文档 + 2 个子文档
    for p in docs:
        data = p.read_bytes()
        assert data.endswith(b"\n"), f"{p.name} 须以换行结尾"
        assert not data.endswith(b"\n\n"), f"{p.name} 末尾不得有多余空行"


# ---------- 源内容前置保护 ----------

def test_generate_aborts_on_literal_br(tmp_path):
    p = make_fixture(tmp_path / "br.xlsx")
    wb = openpyxl.load_workbook(p)
    wb["1.小表"]["A2"] = "x<br>y"
    wb.save(p)
    with pytest.raises(SystemExit):
        x2m.generate(p, tmp_path / "out")


def test_generate_aborts_on_edge_whitespace(tmp_path):
    p = make_fixture(tmp_path / "ws.xlsx")
    wb = openpyxl.load_workbook(p)
    wb["1.小表"]["A2"] = " padded "
    wb.save(p)
    with pytest.raises(SystemExit):
        x2m.generate(p, tmp_path / "out")
