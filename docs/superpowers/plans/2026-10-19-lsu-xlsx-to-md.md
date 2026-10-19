# gem5-fi LSU 方案工作簿（xlsx）→ Markdown 完整转换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx`（12 工作表）完整、无损、可校验地转换为 Markdown 方案文档（主文档 + 4 子文档），全程只读源文件。

**Architecture:** 一个双模式工具 `tools/lsu_xlsx_to_md.py`（generate / --validate）。generate 用 openpyxl 双加载（data_only=True 取显示值 + data_only=False 探公式）把 12 表渲染为主文档+子文档；validate 把生成的 MD **解析回网格**与 xlsx 现场重算的 canonical 网格逐格对比（全量往返），外加结构/RunID/关键字段/源哈希绑定七类检查。生成与校验共用同一套 canonical 函数，防实现漂移。

**Tech Stack:** Python 3 + openpyxl 3.1.5（已装）+ pytest 9.1.1（已装）。纯 Python/docs 变更，**无 gem5 重建**。

**Spec:** 用户指令（2026-10-19，/superpowers:writing-plans 参数原文）：

> 读取：/home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx
> 将工作簿全部工作表完整转换为 Markdown 方案文档，要求：
> 1. 保留工作表顺序、表名、表头、RunID、传播监控、结果统计及备注。
> 2. 不遗漏隐藏行列、合并单元格内容和公式的当前显示值。
> 3. 大型"展开执行矩阵"不得截断；每个 RunID 必须保留且唯一。
> 4. 输出到：/home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md
> 5. 不修改或覆盖原 Excel。
> 6. 转换后校验：工作表数量、RunID 数量、RunID 唯一性，以及关键字段的非空数量；在计划中写明校验方法。
> 7. Markdown 过宽时，可按工作表分节或拆分为主文档加子文档，但主文档必须提供目录和链接。

---

## Global Constraints

- **源 xlsx 只读**：绝不 `wb.save()`、绝不覆盖/重命名/移动；以 sha256+mtime 在生成与校验前后不变为证（校验 V5/V6）。
- **xlsx 的 git 状态是"已跟踪 + 工作树已修改"**（` M`，2026-10-19 20:46 被替换为当前副本）：本任务**不 stage、不还原、不提交**该文件——工作树改动属于用户。
- **主文档路径精确** = `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md`；子文档同目录，命名 `gem5-fi-LSU单元故障注入方案-NN-题名.md`。
- **绝不 `git add -A`**：每次 commit 显式列路径。
- **分支**：留在当前分支 `fi-ding`（非 main）；每个任务验证通过后立即 commit 并 `git push origin fi-ding`。
- **空 = 空**：本副本的结果统计列被刻意清空（表 0 行 30 自述"旧Seed、统计、结局、检测、公式、状态和备注已在本输出副本中全部清空"），照实输出空单元格，**绝不补 0/NA 造数**。
- **one-patch-per-unit**：Task 0–3 每任务恰好一个 commit，严格串行。
- **环境事实**（2026-10-19 实测）：openpyxl 3.1.5、pytest 9.1.1 已装；`tests/` 现有模块均为脚本式，`pytest tests/ --collect-only -q` 基线 = **"5 tests collected in 0.24s"**（test_claim_concurrency 的 5 个收集错误为既有状态）；不受影响回归用 collect-only 对照 + `python3 tools/manifest_validate.py --help`（实测 exit 0）。
- 本任务不触碰 `CHAOS/gem5/src/`，不触发 scons。

## 侦察基线（2026-10-19 只读实测，全部来自真实命令输出）

12 个工作表，顺序与维度：

| # | 工作表 | 维度 | 去向 |
|---|--------|------|------|
| 0 | 0.说明与总览 | 1 列 × 30 行（散文式，空行 2/6/16 为分节间隔） | 主文档内联 |
| 1 | 1.单元与现有研究 | 7 列 × 8 行 | 主文档内联 |
| 2 | 2.LSU参数基线 | 5 列 × 29 行，**两张叠放表**：全宽合并横幅 A21:E21 + 行 22 二级表头 | 主文档内联 |
| 3 | 3.位置x模型矩阵 | 14 列 × 65 行（64 模型） | 子文档 |
| 4 | 4.观测点定义 | 6 列 × 7 行 | 主文档内联 |
| 5 | 5.频率与统计 | 6 列 × 20 行 | 主文档内联 |
| 6 | 6.负载清单 | 6 列 × 15 行（14 负载） | 主文档内联 |
| 7 | 7.展开执行矩阵 | **43 列 × 338 行** = 表头 1 + RunID 行 2–326 + **全空尾行 327–338（12 行，0 非空格）** | 子文档 |
| 8 | 8.文献与来源 | 6 列 × 12 行 | 主文档内联 |
| 9 | 9.逐RunID传播监控 | 17 列 × 326 行 = 表头 + 325 RunID（无尾空行） | 子文档 |
| 10 | 10.源码监控映射 | 10 列 × 65 行（64 模型） | 子文档 |
| 11 | 11.传播事件字段规范 | 5 列 × 24 行 | 主文档内联 |

关键数字（校验时现场重算，本表仅供人审对照）：

- 工作表 12，全部 `visible`；隐藏行 0、隐藏列 0、公式 0、批注 0。
- 非空单元格 **12,996**；数值单元格 331。
- 含换行单元格 **371**；`|` 字符 **778**；反斜杠 0；反引号 0；最长单元格 589 字符（9.逐RunID传播监控!J20）。
- **字面 `<br>` 单元格 0；边缘空白单元格 0**（canonical strip 规则对本工作簿无损，V0 不变式）。
- 合并单元格仅 1 处：`2.LSU参数基线!A21:E21`（全宽横幅，锚值"逐单元保护机制核验（只列实际存在且纳入实现的机制）"）。
- 表 7 RunID：325 个，全部唯一，全部匹配 `^[A-Z]\d{2}-F\d+-W\d+$`（前缀分布 A39/T39/S63/C73/O28/P53/L30）；**与表 9 RunID 集合完全相等**。
- 表 7 关键列非空：传播监控 325、预期结果 325、故障表现形式/子模型 325；结果统计列（Seed、Attempted、Activated、Masked、Crash、SDC、记录状态、实测备注、检测/告警证据 等 P:AP 区间）= **0**（刻意清空的输出副本）。
- 表 9 关键列非空：完整传播路径 325、必监控单元/事件/指标 325、完整性/传播终止判定 325、首轮目标Activated样本数 325。
- 所有 12 表的行 1 均为表头行。

## 转换设计（锁定决策）

1. **布局**：子文档规则 `max_column ≥ 9 或 max_row ≥ 101` → 表 3/7/9/10 出子文档（4 个），其余 8 表内联主文档。主文档含元数据块、目录表（12 行链接）、8 个内联节。
2. **单元格渲染**：`canonical(v) = md_escape(cell_to_text(v).strip())`。`cell_to_text`：None→`''`、bool→`TRUE/FALSE`、datetime→`%Y-%m-%d %H:%M:%S`、date→`%Y-%m-%d`、time→`%H:%M:%S`、数值→`str(v)`、其余 `str(v)`。`md_escape`：`\`→`\\`、`|`→`\|`、`\r\n|\r`→`\n`、`\n`→`<br>`。
3. **全宽合并横幅**（合并区间 min_col=1 且 max_col=ncols 且单行）→ 渲染为 `### 分节横幅：<文本>`，其后一行作为新表表头（表 2 实测形态：行 1–20 表一，行 21 横幅，行 22 表头，行 23–29 表二）。非全宽合并：仅锚单元格有值（openpyxl 语义），节末注记列出合并区间。
4. **尾部全空行**（连续、全列为空的尾段）：不列表，节末注记披露行号区间与数量；**内部空行照常列出**（表 0 的 2/6/16）。
5. **隐藏行列/公式/隐藏工作表**：当前 0；实现为注记——隐藏行列内容仍完整列出 + 注记；公式格显示 data_only 缓存值，无缓存则空 + 脚注（openpyxl 写出的公式无缓存，本工作簿 0 公式）。
6. **元数据块**：主文档顶部 HTML 注释 `<!-- lsu-xlsx2md-metadata … -->`，含 Source-File/Source-SHA256/Source-MTime-Local/Source-Size-Bytes/Generated-At-Local/Sheet-Count/RunID-Count-Sheet7/RunID-Count-Sheet9/Tool——把产出绑定到源文件字节。
7. **锚点**：每节前置 `<a id="sheet-N"></a>`（N=工作表序号），目录内联节链接 `#sheet-N`，子文档链接相对文件名——渲染器无关。

## 校验方法（V0–V7，requirement 6 的完整答案）

校验命令：`python3 tools/lsu_xlsx_to_md.py --xlsx <源> --out-dir <目录> --validate`；全部通过 exit 0 打印 `ALL PASS`，任一失败 exit 1 逐条列出。所有检查都是 **MD ↔ 同一份 xlsx 现场重算** 的对照，不依赖本计划冻结的历史数字（基线数字仅人审用）。

| 检查 | 内容 | 判定 |
|------|------|------|
| V0 源不变式 | 无字面 `<br>` 单元格、无边缘空白单元格（往返无损前提）；报告公式数/隐藏行列数/隐藏工作表数 | 前两项非 0 → FAIL；其余如实报告 |
| V1 结构 | MD 侧工作表节数 = xlsx 工作表数（12）且顺序表名逐一相同；目录 12 行链接全部可解析（`#sheet-N` 锚存在 / 子文档文件存在） | 不等/断链 → FAIL |
| V2 RunID | 每个含 RunID 的表（实测 = 表 7、表 9）：xlsx 数 == MD 数（325）、无重复、集合相等、全部匹配正则；且表 7 集合 == 表 9 集合 | 任一不满足 → FAIL |
| V3 全量往返 | 12 表全部行×列：把 MD 解析回网格（unescape + 分节重组）与 xlsx canonical 网格**逐格相等**（覆盖全部 12,996 非空格；空格两侧均为 `''`） | 行数不等或任一格不等 → FAIL |
| V4 关键字段非空 | 17 个关键列（表 7：RunID/传播监控/预期结果/故障表现形式子模型/Attempted/Activated/Masked/Crash/SDC/记录状态/实测备注/检测告警证据；表 9：RunID/完整传播路径/必监控/完整性判定/首轮目标；表 3 模型ID；表 10 模型ID；表 6 负载ID）逐一报告 xlsx 与 MD 非空数 | 任一列不等 → FAIL |
| V5 源绑定 | 主文档元数据 Source-SHA256 == 当前源文件 sha256（防"生成后源又变"的静默漂移） | 不等 → FAIL（提示重新生成） |
| V6 非修改证明 | 校验开始与结束时源 sha256 一致（工具全程只读的直接证据） | 不等 → FAIL |
| V7 披露注记 | 尾部空行/隐藏/合并/公式注记在应有处存在，数字与实算一致（如"尾部全空行 12 行"） | 缺失或数字不符 → FAIL |

**校验器有牙齿的证明**（单测级负向变异，Task 2 实现）：删一行数据、篡改一格、重复一个 RunID、篡改元数据 SHA、删一表节 → 五种变异各自必须令 validate 返回非 0。

## Review Focus

1. **778 个 `|` 字符**会撑破 GFM 管道表格 → 转义/反转义往返测试（Task 1 `test_escape_unescape_roundtrip`）+ V3 全量往返兜底。
2. **371 个多行单元格**的裸换行会提前终止表格行、静默丢列 → `<br>` 渲染测试（Task 1 `test_multiline_and_pipe_rendering`）+ V3。
3. **325 行大表被截断后看起来仍"完整"**（人工浏览无法察觉少几行）→ 负向变异测试：删行/重复 RunID/改格必须 FAIL（Task 2），V2+V3 双保险。
4. **源是活文档**（今日 20:46 刚被替换；memory 记载多会话曾对 Excel 单写者回填）——转换期间或之后源再变 → V5 SHA 绑定 + `test_validate_detects_source_drift` + Task 3 前后 sha 记录。
5. **本副本结果列刻意清空**（表 0 行 30 自述），有人可能误当"缺数据"去补全 → Global Constraint"空=空" + V4 明细如实报告 Attempted…=0，绝不造数。

---

### Task 0: 计划入库

**Files:**
- Create: `docs/superpowers/plans/2026-10-19-lsu-xlsx-to-md.md`（本文件，已在计划阶段写出）

**Interfaces:** 无代码。为 Task 1–3 提供唯一工作清单。

- [ ] **Step 0.1: 确认计划文件存在且为最新**

Run: `ls -la docs/superpowers/plans/2026-10-19-lsu-xlsx-to-md.md`
Expected: 文件存在（本会话计划阶段已写出）。

- [ ] **Step 0.2: 记录源文件初始指纹（供 Task 3 终验比对）**

Run: `sha256sum "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" && stat -c '%y %s' "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"`
Expected: 输出一行 sha256 + 一行 mtime/size，**抄录进提交信息或执行记录**（Task 3 Step 3.6 比对用）。

- [ ] **Step 0.3: 提交计划文件**

```bash
git add docs/superpowers/plans/2026-10-19-lsu-xlsx-to-md.md
git commit -m "[LSU-XLSX2MD][PLAN] xlsx→MD 完整转换计划（侦察基线+设计+校验方法 V0–V7）"
git push origin fi-ding
```

---

### Task 1: 转换器 generate 模式（TDD）

**Files:**
- Create: `tools/lsu_xlsx_to_md.py`
- Test: `tests/test_lsu_xlsx_to_md.py`

**Interfaces:**
- Consumes: 无（首个代码任务）。
- Produces（后续任务依赖的精确签名，全部保持稳定）:
  - `cell_to_text(v) -> str`、`md_escape(text: str) -> str`、`md_unescape(text: str) -> str`、`canonical(v) -> str`
  - `split_md_row(line: str) -> list[str]`（把 MD 表格行拆回原始文本单元格，已反转义）
  - `@dataclass SheetModel`：字段 `name, ncols, nrows_raw, grid, trailing_empty, banner_rows, formulas, merged, hidden_rows, hidden_cols, sheet_state, nonempty, runids`
  - `build_sheet_model(ws, wsf) -> SheetModel`（ws=值工作表，wsf=公式工作表）
  - `subdoc_filename(name: str, idx: int) -> str`、`is_subdoc(m: SheetModel) -> bool`
  - `generate(xlsx_path: Path, out_dir: Path) -> dict`（返回报告：写入文件、各表规模、RunID 数）
  - 常量 `MAIN_STEM = "gem5-fi-LSU单元故障注入方案"`、`BANNER_PREFIX = "### 分节横幅："`、`META_BEGIN/META_END`、`RUNID_RE`
  - Task 1 只实现 `main()` 的 generate 分支；`--validate` 参数**先占位为未实现错误**（`sys.exit("validate 模式在 Task 2 实现")`），Task 2 补齐。

- [ ] **Step 1.1: 写失败测试**

创建 `tests/test_lsu_xlsx_to_md.py`（完整内容；fixture 用 openpyxl 在 `tmp_path` 合成迷你工作簿，覆盖换行/竖线/横幅分节/公式无缓存/隐藏行/RunID/宽表子文档/尾部空行全要素——**不触碰真实工作簿**）：

```python
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
    for _ in range(5):                  # 尾部全空行 5 行
        ws4.append([None, None])
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
```

- [ ] **Step 1.2: 运行确认 RED**

Run: `python3 -m pytest tests/test_lsu_xlsx_to_md.py -v`
Expected: 收集失败或全部 ERROR/FAIL（`ModuleNotFoundError: No module named 'lsu_xlsx_to_md'`）。

- [ ] **Step 1.3: 实现转换器 generate 部分**

创建 `tools/lsu_xlsx_to_md.py`（完整内容；validate 相关函数 Task 2 追加，本步 `main()` 的 `--validate` 分支先响亮报错）：

```python
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
```

- [ ] **Step 1.4: 运行测试确认 GREEN**

Run: `python3 -m pytest tests/test_lsu_xlsx_to_md.py -v`
Expected: **7 passed**（test_cell_to_text、test_escape_unescape_roundtrip、test_generate_writes_docs_and_source_untouched、test_multiline_and_pipe_rendering、test_banner_split、test_trailing_empty_rows_disclosed、test_formula_and_hidden_notes），0 FAIL、0 ERROR。

- [ ] **Step 1.5: 不受影响回归（基线对照）**

Run: `python3 -m pytest tests/ --collect-only -q | tail -1 && python3 tools/manifest_validate.py --help >/dev/null && echo smoke-ok`
Expected: `5 tests collected …`（与基线相同，证明未干扰既有套件）+ `smoke-ok`（exit 0）。

- [ ] **Step 1.6: 提交并推送**

```bash
git add tools/lsu_xlsx_to_md.py tests/test_lsu_xlsx_to_md.py
git commit -m "[LSU-XLSX2MD][TOOL] xlsx→MD 转换器 generate 模式（转义/横幅分节/尾空行披露/公式缓存值，单测全绿）"
git push origin fi-ding
```

---

### Task 2: 校验器 validate 模式（TDD，负向变异优先）

**Files:**
- Modify: `tools/lsu_xlsx_to_md.py`（追加校验函数；`main()` 的 `--validate` 分支接通 `validate()`）
- Modify: `tests/test_lsu_xlsx_to_md.py`（追加校验测试）

**Interfaces:**
- Consumes: Task 1 的全部函数与常量（签名不变）。
- Produces:
  - `parse_md_tables(text: str) -> list[list[str]]`（把一个小节的 MD 解析回原始文本网格：表格行 + 横幅行；跳过标题/注记/引用等非表格行）
  - `split_main_sections(main_text: str) -> dict[int, str]`（按 `<a id="sheet-N">` 锚切出内联节）
  - `md_row_to_canonical(cells: list[str], ncols: int) -> list[str]`（原始文本行 → canonical 行，右侧补空到 ncols）
  - `validate(xlsx_path: Path, out_dir: Path) -> int`（0=全过，1=有失败；打印逐项 PASS/FAIL 表）

- [ ] **Step 2.1: 先写失败的校验测试（含 5 种负向变异）**

追加到 `tests/test_lsu_xlsx_to_md.py`：

```python
# ---------- validate（Task 2） ----------

def test_validate_pass_on_fresh_generation(fx, tmp_path):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    assert x2m.validate(fx, out) == 0


def _mutated_fails(fx, tmp_path, mutate):
    out = tmp_path / "out"
    x2m.generate(fx, out)
    mutate(out)
    assert x2m.validate(fx, out) != 0


def _edit(out, fname, fn):
    p = out / fname
    lines = p.read_text(encoding="utf-8").splitlines()
    fn(lines)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_validate_detects_missing_row(fx, tmp_path):
    def drop(lines):
        for i, l in enumerate(lines):
            if l.startswith("| A01-F1-W3"):
                del lines[i]
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", drop))


def test_validate_detects_cell_mutation(fx, tmp_path):
    def change(lines):
        for i, l in enumerate(lines):
            if l.startswith("| A01-F0-W3"):
                lines[i] = l.replace("v1", "TAMPERED")
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", change))


def test_validate_detects_duplicate_runid(fx, tmp_path):
    def dup(lines):
        for i, l in enumerate(lines):
            if l.startswith("| A01-F1-W3"):
                lines.insert(i, l)
                return
        raise AssertionError("fixture 行未找到")
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", dup))


def test_validate_detects_source_drift(fx, tmp_path):
    def drift(text):
        return text.replace("Source-SHA256: ", "Source-SHA256: 0")  # 篡改绑定哈希
    def mutate(out):
        p = out / f"{MAIN}.md"
        p.write_text(drift(p.read_text(encoding="utf-8")), encoding="utf-8")
    _mutated_fails(fx, tmp_path, mutate)


def test_validate_detects_missing_sheet(fx, tmp_path):
    def drop_section(lines):
        keep, skipping = [], False
        for l in lines:
            if l.startswith('<a id="sheet-2"'):
                skipping = True
            elif l.startswith('<a id="sheet-'):
                skipping = False
            if not skipping:
                keep.append(l)
        lines[:] = keep
    _mutated_fails(fx, tmp_path, lambda out: _edit(out, f"{MAIN}.md", drop_section))
```

- [ ] **Step 2.2: 运行确认 RED**

Run: `python3 -m pytest tests/test_lsu_xlsx_to_md.py -v`
Expected: 新增 6 个校验测试全部 FAIL（`AttributeError: module 'lsu_xlsx_to_md' has no attribute 'validate'`），Task 1 的 7 个保持 PASS。

- [ ] **Step 2.3: 实现 validate**

在 `tools/lsu_xlsx_to_md.py` 中追加（并把 `main()` 的 `--validate` 分支改为 `return validate(Path(a.xlsx), Path(a.out_dir))`）：

```python
# ---------- validate（Task 2） ----------

KEY_COLUMNS = {  # V4 显式报告的关键字段（表名 → 表头名列表）
    "7.展开执行矩阵": ["RunID", "传播监控", "预期结果", "故障表现形式/子模型",
                     "Attempted", "Activated", "Masked", "Crash", "SDC",
                     "记录状态", "实测备注", "检测/告警证据"],
    "9.逐RunID传播监控": ["RunID", "完整传播路径（按顺序）", "必监控单元/事件/指标",
                       "完整性/传播终止判定", "首轮目标Activated样本数"],
    "3.位置x模型矩阵": ["模型ID"],
    "10.源码监控映射": ["模型ID"],
    "6.负载清单": ["负载ID"],
}


def parse_md_tables(text: str) -> list:
    """小节文本 → 原始文本网格（行序 = 源行序；横幅行为单格行；跳过非表格行）。"""
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


def validate(xlsx_path: Path, out_dir: Path) -> int:
    checks, failures = [], []

    def check(name, ok):
        checks.append((name, ok))
        if not ok:
            failures.append(name)

    sha_before = hashlib.sha256(xlsx_path.read_bytes()).hexdigest()
    main_path = out_dir / f"{MAIN_STEM}.md"
    if not main_path.exists():
        print(f"[validate] 缺主文档 {main_path}")
        return 1
    main_text = main_path.read_text(encoding="utf-8")
    meta = parse_metadata(main_text)

    wbv = openpyxl.load_workbook(xlsx_path, data_only=True)
    wbf = openpyxl.load_workbook(xlsx_path, data_only=False)
    names = list(wbv.sheetnames)
    models = {n: build_sheet_model(wbv[n], wbf[n]) for n in names}

    # V0 源不变式
    lit_br = sum(1 for m in models.values() for row in m.grid for v in row
                 if isinstance(v, str) and "<br>" in v)
    edge_ws = sum(1 for m in models.values() for row in m.grid for v in row
                  if isinstance(v, str) and v != v.strip())
    check(f"V0 无字面 '<br>' 单元格（实测 {lit_br}）", lit_br == 0)
    check(f"V0 无边缘空白单元格（实测 {edge_ws}）", edge_ws == 0)
    n_formula = sum(len(m.formulas) for m in models.values())
    n_hidden_r = sum(len(m.hidden_rows) for m in models.values())
    n_hidden_c = sum(len(m.hidden_cols) for m in models.values())
    n_hidden_sh = sum(1 for m in models.values() if m.sheet_state != "visible")
    checks.append((f"V0 报告: 公式 {n_formula}；隐藏行 {n_hidden_r}；"
                   f"隐藏列 {n_hidden_c}；非 visible 工作表 {n_hidden_sh}", True))

    # V5 源绑定
    check(f"V5 元数据 Source-SHA256 == 当前源", meta.get("Source-SHA256") == sha_before)
    check("V5 元数据 Sheet-Count == 实际", meta.get("Sheet-Count") == str(len(names)))

    # 定位每个表的 MD 文本
    sections = split_main_sections(main_text)
    md_of = {}
    for idx, name in enumerate(names):
        m = models[name]
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

    # 每表 canonical 网格（xlsx 侧）
    xcan = {n: [[canonical(v) for v in row] for row in m.grid]
            for n, m in models.items()}

    # V3 全量往返 + V7 披露注记
    for name in names:
        m = models[name]
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
        m = models[name]
        if not m.runids:
            continue
        parsed = parse_md_tables(md_of.get(name, ""))
        md_rids = [r[0] for r in parsed[1:] if r and RUNID_RE.match(r[0])]
        check(f"V2 [{name}] RunID 数量一致（xlsx {len(m.runids)} vs md {len(md_rids)}）",
              len(md_rids) == len(m.runids))
        check(f"V2 [{name}] RunID 无重复", len(md_rids) == len(set(md_rids)))
        check(f"V2 [{name}] RunID 集合与源一致", set(md_rids) == set(m.runids))
        rid_sets[name] = set(m.runids)
    pair = [n for n in ("7.展开执行矩阵", "9.逐RunID传播监控") if n in rid_sets]
    if len(pair) == 2:
        check("V2 表7/表9 RunID 集合相等", rid_sets[pair[0]] == rid_sets[pair[1]])
    else:
        checks.append(("V2 表7/表9 RunID 集合相等：n/a（源不足两张 RunID 表）", True))

    # V4 关键字段非空计数
    for name, wants in KEY_COLUMNS.items():
        if name not in models:
            checks.append((f"V4 [{name}] n/a（源无此表）", True))
            continue
        m, parsed = models[name], parse_md_tables(md_of.get(name, ""))
        pcan = [md_row_to_canonical(r, m.ncols) for r in parsed]
        hdr = xcan[name][0] if xcan[name] else []
        for want in wants:
            ci = next((i for i, h in enumerate(hdr) if h == canonical(want)), None)
            if ci is None:
                check(f"V4 [{name}][{want}] 找到列", False)
                continue
            n_x = sum(1 for row in xcan[name][1:] if row[ci])
            n_m = sum(1 for row in pcan[1:] if ci < len(row) and row[ci])
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
        return 1
    print("ALL PASS")
    return 0
```

- [ ] **Step 2.4: 运行全部测试确认 GREEN**

Run: `python3 -m pytest tests/test_lsu_xlsx_to_md.py -v`
Expected: 全部 PASS（Task 1 的 7 个 + Task 2 的 6 个 = 13 个，0 FAIL），确认输出里 5 个负向变异测试均为 PASS（即校验器抓到了每一种破坏）。

- [ ] **Step 2.5: 真实工作簿 /tmp 冒烟（generate + validate 全链）**

```bash
rm -rf /tmp/lsu_md_smoke && python3 tools/lsu_xlsx_to_md.py \
  --xlsx "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" --out-dir /tmp/lsu_md_smoke
python3 tools/lsu_xlsx_to_md.py \
  --xlsx "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" --out-dir /tmp/lsu_md_smoke --validate
```

Expected: generate 写出 5 个文件（主 + 4 子）；validate 逐项打印并 `ALL PASS`，其中关键行：Sheet-Count=12、`V2 [7.展开执行矩阵] RunID 数量一致（xlsx 325 vs md 325）`、`V2 [7.展开执行矩阵] RunID 无重复`、`V2 表7/表9 RunID 集合相等`、`V3 [7.展开执行矩阵] 逐格相等`、`V4 [7.展开执行矩阵][Attempted] 非空 xlsx=0 md=0`（空=空的诚实呈现）。**引用真实输出进提交信息**。若任何一项 FAIL：停下按 systematic-debugging 修复后重跑，不得跳过。

- [ ] **Step 2.6: 冒烟后源文件未动 + 不受影响回归**

Run: `sha256sum "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" && python3 -m pytest tests/ --collect-only -q | tail -1`
Expected: sha256 与 Task 0 Step 0.2 记录一致；collect 仍为 `5 tests collected`。

- [ ] **Step 2.7: 提交并推送**

```bash
git add tools/lsu_xlsx_to_md.py tests/test_lsu_xlsx_to_md.py
git commit -m "[LSU-XLSX2MD][TOOL] --validate 校验模式（V0-V7 全量往返+RunID+关键字段+SHA绑定，5 负向变异测试 + 真实工作簿冒烟 ALL PASS）"
git push origin fi-ding
```

---

### Task 3: 正式产出、终验、提交

**Files:**
- Create（工具生成，非手写）: `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md`
- Create（工具生成）: `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md`、`…-07-展开执行矩阵.md`、`…-09-逐RunID传播监控.md`、`…-10-源码监控映射.md`
- Modify: `docs/superpowers/plans/2026-10-19-lsu-xlsx-to-md.md`（勾选本任务复选框）

**Interfaces:**
- Consumes: Task 1/2 的 `generate`/`validate` CLI。
- Produces: 最终交付文档集（requirement 4 的精确路径）。

- [ ] **Step 3.1: 正式生成到 docs/gem5-fi/lsu/**

```bash
python3 tools/lsu_xlsx_to_md.py \
  --xlsx "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" \
  --out-dir "docs/gem5-fi/lsu"
```

Expected: 写出主文档 + 4 子文档（03/07/09/10），打印各文件字节数。

- [ ] **Step 3.2: 就地终验（V0–V7）**

```bash
python3 tools/lsu_xlsx_to_md.py \
  --xlsx "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" \
  --out-dir "docs/gem5-fi/lsu" --validate
```

Expected: 退出码 0，`ALL PASS`；关键数字：12 表、表 7/表 9 各 325 RunID 无重复且集合相等、V3 12 表逐格相等（12,996 非空格）、V4 各关键列 xlsx==md。**真实输出原文引用进提交信息**。

- [ ] **Step 3.3: 独立抽查（不依赖校验器的第二证据链）**

```bash
grep -cE '^\| [A-Z][0-9]{2}-F[0-9]+-W[0-9]+ ' "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md"
grep -cE '^\| [A-Z][0-9]{2}-F[0-9]+-W[0-9]+ ' "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md"
grep -c '^## ' "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md"
ls -la docs/gem5-fi/lsu/*.md
```

Expected: 两个 grep 均输出 **325**；主文档 `^## ` = **9**（目录 + 8 内联表节）；5 个 .md 文件存在。表 7 子文档应含 43 列表头行（`| RunID | 模型ID | … | 故障表现形式/子模型 |`）。

- [ ] **Step 3.4: 不受影响回归**

Run: `python3 -m pytest tests/ --collect-only -q | tail -1 && python3 tools/manifest_validate.py --help >/dev/null && echo smoke-ok`
Expected: `5 tests collected …` + `smoke-ok`（与基线一致）。

- [ ] **Step 3.5: 源文件未被修改的最终证明**

```bash
sha256sum "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
stat -c '%y %s' "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
git status --short -- "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"
```

Expected: sha256/mtime 与 Task 0 Step 0.2 抄录值完全一致；git 状态仍为 ` M`（用户的工作树改动原样保留，未被 stage）。

- [ ] **Step 3.6: 勾选计划复选框并提交推送**

本计划文件勾选 Task 3（及补勾执行中发现的一切）后：

```bash
git add docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md \
        "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md" \
        "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md" \
        "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md" \
        "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-10-源码监控映射.md" \
        docs/superpowers/plans/2026-10-19-lsu-xlsx-to-md.md
git commit -m "[LSU-XLSX2MD][DOCS] 正式产出主文档+4子文档（12表/325RunID唯一/325∩325集合相等，V0-V7 终验 ALL PASS，源xlsx sha256 前后一致未修改）"
git push origin fi-ding
```

注意：**不 stage** xlsx 本身（保持用户的 ` M` 状态）；生成的 5 个 .md 与计划文件逐路径显式加入。

---

## 执行注意事项

- **源文件活变动**：若 Task 1–3 任何一步发现 xlsx sha256 与 Task 0 记录不一致（说明期间有人改写了工作簿），停下向用户确认后再以新版本重新生成——元数据 SHA 绑定会诚实地暴露这一点（V5）。
- **xlsx 是否入库**：本计划不提交 xlsx（用户工作树改动归用户）。若用户后续希望像 OoO 轨道那样把 xlsx 纳入版本管理，是独立的一个后续 commit，不属于本计划。
- **再生成**：xlsx 更新后重跑 generate+validate 即可重建文档；元数据块会自动绑定新 SHA。
