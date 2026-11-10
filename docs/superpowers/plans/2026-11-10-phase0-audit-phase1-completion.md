# Phase 0 核查 + Phase 1 收尾：基础模板 ACE/IBR 全覆盖、SAD、NSGA-II

日期：2026-11-10
依据：`sdcfuzz/sdcfuzz-v1.2.md` §5.1、§7（Phase 1 交付物：自动靶向生成器原型 +
结构覆盖度评估工具）；`docs/roadmap/roadmap.yaml` Phase 0/Phase 1 台账。

## 目标与判定

1. 逐项核查路线图 Phase 0 的 5 个里程碑，凡是本机可复现的都用真实命令重跑；
   外部证据项给出可核验的文件/哈希/位置，并明确“未在本机复验”。核查记录写入
   `docs/sdcfuzz/phase0-verification.md`。
2. 完成 Phase 1 剩余内容：
   - 基础 19 模板涉及的每类指令都有可观测的 ACE/IBR 覆盖：整数/向量（FP）
     物理寄存器 ACE、L1 ACE、整数与 FP 功能单元 IBR；
   - SAD（结构激活深度）gem5 实现与定向验证；
   - NSGA-II 多目标序列集生成与定向验证；
   - 路线图与实现文档更新。

## 关键事实（开始前）

- 当前工作区是 `sdc-0103`（aarch64，128 核），但预置的
  `build/ARM_ACE_IBR_AUDIT/gem5.opt` 是 x86-64 ELF，无法在本机执行；
  `build/ARM/gem5.opt` 是原生 aarch64，但构建于 ACE/IBR 代码之前（2026-09-08）。
  因此 Phase 0 的实际测试必须先重建原生 aarch64 + 当前源码的 gem5。
- 交叉编译器为 `aarch64-openEuler-linux-gcc`，不是脚本默认的
  `aarch64-linux-gnu-gcc`；测试统一显式传 `ARM_CC`。
- 现有 RF ACE 只跟踪 `IntRegClass`；FU IBR 只有 intAlu/intMult/intDiv 三类。
  19 模板中的 `fp-add`/`fp-mul` 没有 RF/FP ACE 与 FP IBR，这是本次要补的缺口。

## 单元划分（每项一个提交，按序执行）

### 单元 0：Phase 0 核查（不改变行为）

- [x] 重建原生 aarch64 gem5（`build/ARM`，当前源码）。
- [x] 真实运行 `scripts/test-sdcfuzz-baseline.py`（19/19 + FI 冒烟）。
- [x] 真实运行 `tests/test_sdcfuzz_*.py`、`sdcfuzz.cli evaluate`。
- [x] 核验上游 D13/19 模板/p2 草稿/4 板部署证据：文件存在、哈希、数量；
      明确哪些不能本机复现。
- [x] 运行 `scripts/test-ace-ibr-correctness.py`、`test-rf-ace.sh`、
      `test-l1-ace.sh`、`test-fu-ibr.sh`（原生构建）。
- [x] 新增 `docs/sdcfuzz/phase0-verification.md`，逐项给命令、真实输出、结论。
- 提交：`docs(sdcfuzz): Phase 0 逐项核查与原生 aarch64 实测记录`

### 单元 1：基础模板 ACE/IBR 全覆盖

- [x] RF ACE 增加向量/FP 物理寄存器（VecRegClass）读写与按位生命周期统计，
      新增 `rfAce.vec*` 统计；整数语义保持不变。
- [x] FU IBR 增加 `fpAdd`/`fpMult` 类别（标量 FP 编码识别、端口/宽度、FUPool
      分母）；整数类别保持原样。
- [x] 结构探测负载增加模板涉及的指令形式：`movz`、`add_imm`、`add_lsl`、
      `fadd`、`fmul`（以及必要的参考语义），用于逐指令归因。
- [x] `sdcfuzz/coverage.py`：模板 Op → 必需指标清单；`scripts/test-template-coverage.py`
      运行全部 19 模板，断言每个模板的每类必需指标都 > 0，FP 模板的向量 ACE 与
      FP IBR 均 > 0；静态清单覆盖所有 Op.kind（漏项直接失败）。
- [x] `evaluate.py`/`autousens.py` 接入 `fpadd`/`fpmul` 结构键，FP 模板目标从
      `none` 改为可测结构；既有 `alu/mult/div/l1d/l1i` 口径不变。
- 验证：重建 + 运行 `scripts/test-template-coverage.py` 与既有三个 ACE/IBR
  回归脚本；真实输出写入计划/文档。
- 提交：`feat(ace-ibr): 覆盖基础模板的向量 RF ACE 与 FP FU IBR`

### 单元 2：SAD 结构激活深度

- [x] 新增 `CHAOS/gem5/src/cpu/o3/sad.{hh,cc}`：按 ROI 内每周期采样 ROB、IQ、
      LQ、SQ、int PRF、vec PRF 占用与发射宽度占用，输出
      `SAD(s) = Σ_cycle used_s / (samples × capacity_s)`。
- [x] `BaseO3CPU.py`/`arm_chaos.py` 接入 `--sad` 及窗口参数；work-item 与固定
      周期窗口语义与 ACE/IBR 一致。
- [x] 新增 `workloads/directed/sad_workload.c` + `scripts/test-sad.sh`：
      至少验证高占用（依赖链/rob 压力）SAD 高于低占用（nop），ROI 边界、关闭、
      公式（used/samples/capacity）与 ratio ∈ [0,1]。
- 验证：重建 + `scripts/test-sad.sh` + 既有 ACE/IBR 回归。
- 提交：`feat(gem5): 实现 SAD 结构激活深度指标`

### 单元 3：NSGA-II 多目标序列集

- [x] 新增 `tools/nsga2.py`：通用 NSGA-II（快速非支配排序、拥挤距离、二元锦标赛、
      均匀交叉、位翻转变异、确定性种子），无 gem5 依赖。
- [x] `tools/autousens.py` 新增 `pareto` 子命令：从 `structure_map.json` 的逐指令
      激活构造决策空间，按多结构归一化目标生成 Pareto 序列集，输出
      `pareto_set.json` 与每条序列的候选源码；可选 `--validate` 在 gem5 中跑
      knee 点并报告真实覆盖。
- [x] 新增 `tests/test_nsga2.py`：合成目标函数验证非支配排序/拥挤距离/确定性。
- [x] 扩展 `scripts/test-autousens.py`：真实 gem5 上验证 Pareto 集结构与 knee 点覆盖。
- 验证：`pytest tests/test_nsga2.py`、`scripts/test-autousens.py --gem5 <native>`。
- 提交：`feat(autousens): NSGA-II 多目标序列集生成`

### 单元 4：文档与路线图

- [x] 更新 `docs/roadmap/roadmap.yaml`/`ROADMAP.md`：Phase 1 全部 done-local
      或明确剩余项；SAD/NSGA-II 状态与证据。
- [x] 更新 `docs/gem5/{structural-coverage-autousens,fu-ibr-implementation}.md`、
      `docs/sdcfuzz/phase0-baseline.md` 等：新指标、边界、实测数据。
- [x] 勾选本计划；重新生成路线图。
- 提交：`docs(roadmap): Phase 1 完成、ACE/IBR 全覆盖与 SAD/NSGA-II 证据`

## 验证原则

- 每个单元都在真实命令上验证并引用真实输出；不把“代码看起来对”当证据。
- gem5 构建使用 `source ~/gem5-deps/env.sh`，原生 aarch64 `build/ARM`，
  `-j96 ISA_CONSTR_CCFLAGS=-g0 ISA_EXEC_CCFLAGS=-g0 --limit-ld-memory-usage`。
- 每次提交前跑至少一个不受影响的相关回归（如 `pytest tests/` 或既有 ACE/IBR 脚本）。
- 外部证据项不伪造复验；写明“已核验文件/哈希，未在本机复跑”。

## 风险

- gem5 C++ 改动会触发增量重编，ARM host 上每次约数分钟到十几分钟；尽量把
  ACE/IBR 与 SAD 的 C++ 改动分开验证，但可以共用一次全量重建。
- 向量寄存器在 ARM 上映射到 `VecRegClass`（128 位）；FP D 运算只占低 64 位，
  ACE 的掩码要按编码宽度收缩，否则会虚高。
- SAD 采样与 ROI 结束边界、stats reset 的先后顺序要与现有 tracker 对齐；用
  `samples` 作分母保证公式自洽，同时报告 measuredCycles。
- 编译器可能在同一 ROI 内引入未预期的指令；逐指令探测与静态清单优先，
  模板级断言只要求“必需指标 > 0”，不假设精确条数。


## 完成记录（2026-11-10，真实命令）

- 原生 aarch64 gem5：`build/ARM/gem5.opt`（ARM aarch64 ELF），编译零错误；
  预置 `ARM_ACE_IBR_AUDIT/gem5.opt` 为 x86-64，在本机无法执行。
- `python3 -m pytest tests/ -q` → `59 passed`。
- `scripts/test-template-coverage.py` → `all 19 templates cover every mapped
  instruction form`；FP: `vec_reads=1284 vec_writes=646 fpadd/fpmul=81920`。
- `scripts/test-sdcfuzz-baseline.py` → `19/19 templates PASS, FI loop Masked`。
- `scripts/test-fu-ibr.sh`、`test-rf-ace.sh`、`test-l1-ace.sh`、
  `test-ace-ibr-correctness.py` 全部通过（原生 aarch64）。
- `scripts/test-sad.sh` → `SAD window, formula, direction, disabled and
  cycle-mode checks passed`；`rob=0.344908` vs `nop=0.132089`。
- `scripts/test-autousens.py` → target/target-l1d+alu/mult、`pareto size=12
  knee=['str','movz','str']`、错误处理全部通过。
- Phase 0 外部证据：D13 sha256 与 `d13-repro/summary.json` 一致；上游
  `seeds/*.S` 实际 20 个/8 模块（方案写 19/7，已在路线图更正）；
  paper2 草稿与四板 446 核表格存在，但未在本机重跑。

偏差与处理：
1. 预置 x86-64 二进制无法在 aarch64 上执行，改为重建原生构建；
2. `test-rf/l1-ace.sh` 原先硬编码 x86-64 宿主，改为同时接受 aarch64；
3. 向量 ACE 初版未记录 FP 写（`getWritableRegOperand` 路径），且 read-only
   live-in 会导致 ratio>1，已补写钩子并禁止向量 live-in 推断；
4. `target l1d` 的覆盖 ratio 会随候选周期数波动，测试改为断言净激活 > 0；
5. `sad_workload` 的 PRF 期望值写错（每轮覆盖而非累加），已按真实语义修正。
