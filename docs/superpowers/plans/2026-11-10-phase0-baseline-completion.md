# Phase 0 基线补全：D13 变异启发式 + 19 模板语料 + 结构评估

日期：2026-11-10
状态：全部完成（提交见 git history）
依据：`sdcfuzz/sdcfuzz-v1.2.md` §7 Phase 0（交付物：D13 启发式 + 19 模板 +
gem5-CHAOS + 4 板部署 + p2 草稿）与 §5.2（D13 反逻辑屏蔽变异）。

## 背景与判定

技术路线文档的 Phase 0 是“sdcfuzz 基线完善”。其中 D13 启发式、19 个手工
微架构模板、4 板真机部署与 p2 草稿属于外部 sdcfuzz 仓库/硬件，本仓库
（gem5 + CHAOS 侧）此前没有可复现的基线实现。本计划把 Phase 0 中
**能在本仓库落地并可验证**的部分补全：

- D13 操作数启发式（进位链 / 翻转密度，显式规避固定值逻辑屏蔽）
- 19 条微架构靶向模板语料（本仓库本地实现，不是对 sdcfuzz 原模板的复制，
  命名与结构映射写在文档里）
- 模板生成器 + gem5 结构指标评估器（复用 Phase 1 的 ACE/IBR 指标）
- 模板语料 → gem5-CHAOS 故障注入的闭环冒烟
- 4 板部署与 p2 草稿保留为“外部证据”状态，由进度图单独区分，不谎称本地完成

## 单元与提交

### 单元 1：D13 启发式
- [x] 新增 `sdcfuzz/d13.py`：64 位加法进位链长度、翻转密度、固定值惩罚，
  `select()` 从候选集中确定性选出操作数。
- [x] 新增 `tests/test_sdcfuzz_d13.py`：进位链手工样例、固定值被拒、
  选中得分高于随机基线的下界、确定性/种子。
- 提交：`feat(sdcfuzz-baseline): D13 反逻辑屏蔽操作数启发式`

### 单元 2：模板 DSL 与 19 模板
- [x] 新增 `sdcfuzz/isa.py`：AArch64 子集指令描述、汇编发射器、Python 参考
  解释器（64/32 位、无符号除法语义、double 运算）。
- [x] 新增 `sdcfuzz/templates.py`：19 条模板（ALU/MUL/DIV/L1D/L1I/依赖链/
  分支/FP），每条给出目标结构、对应 CHAOS 注入器类别与参考语义。
- [x] 新增 `sdcfuzz/generator.py`：生成带 m5 work-item 标记、确定性
  16-hex 校验和的 C guest；支持 D13 选择操作数常量。
- 提交：`feat(sdcfuzz-baseline): 19 条微架构模板与 AArch64 生成器`

### 单元 3：结构评估器
- [x] 新增 `sdcfuzz/evaluate.py`：编译并运行全部模板，采集 RF/L1/FU 指标，
  输出 `corpus_index.json`（覆盖向量、目标结构净激活、PASS 状态）。
- 提交：`feat(sdcfuzz-baseline): 模板语料结构评估与索引`

### 单元 4：端到端与 FI 闭环
- [x] 新增 `scripts/test-sdcfuzz-baseline.py`：19/19 模板真实编译 + gem5 运行
  `status=PASS`，目标结构归因正确，索引可复现；
  再用 CHAOSReg 注入一次，按 `tools/classify.py` 输出 SDC/Masked/Crash/
  Inactive 之一（证明语料能进入故障注入闭环）。
- 提交：`test(sdcfuzz-baseline): 19 模板与 FI 闭环回归`

### 单元 5：长期路线图台账与进度图
- [x] 新增 `docs/roadmap/roadmap.yaml`：Phase 0–5 全部里程碑与子项，状态取
  `done-local / done-external / partial / todo / gated`，附证据路径。
- [x] 新增 `tools/render_roadmap.py`：从台账渲染
  `docs/roadmap/roadmap.svg` / `.png` 与 `ROADMAP.md`（含状态图例与进度百分比）。
- 提交：`docs(roadmap): Phase 0–5 里程碑台账与长期进度图`

### 单元 6：文档
- [x] 新增 `docs/sdcfuzz/phase0-baseline.md`：模板清单、D13 口径、评估方法、
  外部证据项与边界。
- [x] 勾选本计划。
- 提交：`docs(sdcfuzz-baseline): Phase 0 基线实现与边界说明`

## 验证记录（真实输出，2026-11-10）

```bash
$ python3 -m pytest tests/test_sdcfuzz_d13.py tests/test_sdcfuzz_generator.py -q
15 passed

$ python3 scripts/test-sdcfuzz-baseline.py
alu-add-carry    target=alu   activation=91904.0 ...
mul64            target=mult  activation=123264.0 ...
l1d-load-stream  target=l1d   activation=3852.0 ...
l1i-big-body     target=l1i   activation=1333.0 ...
reproducibility: mul64 activation stable at 123264
d13: operand=0xff1b36114f09638f carry_chain=16 alu_bits=92160 (default 91904)
fi smoke: chaos_reg faults=1 -> Masked (completed exit=0, checksum==golden)
phase-0 baseline: 19/19 templates PASS, FI loop Masked

$ python3 -m sdcfuzz.cli evaluate --outdir m5out/sdcfuzz-baseline/corpus --iterations 40
alu  best=branch-busy      activation=1463424
mult best=madd64           activation=123264
div  best=div64            activation=81920
l1d  best=l1d-load-stream  activation=3852
l1i  best=l1i-big-body     activation=1333
no structure metric: fp-add, fp-mul
```

## 执行中的事实与偏差

- FI 冒烟用 CHAOSReg 注入 1 次，分类为 Masked：架构状态注入器在 O3 上
  不改变已发射循环的操作数，这正是 `summary.md` 记录的已知限制；脚本按
  真实结果分类，不伪造 SDC。
- 19 模板的 `iterations=40` 是回归默认值；文档中的激活表同口径。
- 进度图由 `docs/roadmap/roadmap.yaml` 生成，Phase 0 的 5 项中 3 项是
  本仓库实测、2 项是外部证据，图中用不同颜色区分。

## 边界

- 19 模板是本仓库的本地语料，不声称与 sdcfuzz 原 19 模板逐条一致；
  对应关系与设计依据写在 `docs/sdcfuzz/phase0-baseline.md`。
- 4 板真机部署（历史证据在 sdcfuzz 文档）与 p2 草稿不在本机可验证范围，
  台账中标为 `done-external` 并注明“未在本机复验”。
- FP 模板当前没有 FP 结构指标，评估只报告 RF 与“无结构指标”状态。
