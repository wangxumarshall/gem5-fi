# Phase 0 基线与真基线复现：本地支撑件 + 上游 D13

本文记录本仓库落地的 sdcfuzz Phase 0 基线。它对应技术路线文档
`sdcfuzz/sdcfuzz-v1.2.md` §7 的 Phase 0（“sdcfuzz 基线完善：D13 启发式 +
19 模板 + gem5-CHAOS + 4 板部署 + p2 草稿”）中**能在本仓库实现并验证**的
部分。

**重要更正（2026-11-10）。** 技术路线文档里的 D13 和 19 模板是上游
sdcfuzz 仓库已有的资产，不是本仓库需要重新实现的东西：

- 真 D13 在 `sdcfuzz/gem5_config/workloads/sdc_probe_workload_d13.c`，
  是运行时随机候选 + 定向变异 + `popcount(x^(x+1))` 选择的 workload；
- 19 个微架构模板在 `sdcfuzz/seeds/*.S`（覆盖 MMU/L2C/LSU/OoO/IEX/FSU/IFU）。

本仓库里的 `sdcfuzz/operand_heuristic.py` 和 19 条本地语料是**支撑件**
（可选对照与结构评估语料），不是上述两者的复刻：前者与 D13 的算法、作用
位置、随机源都不同，后者与上游 19 模板没有逐条对应关系。上游 D13 的真基线
已在 sdc-0103 上复现，记录见
`docs/sdcfuzz/d13-baseline-reproduction.md`。4 板真机部署和 p2 论文草稿属于
外部证据，本机无法复验（见第 6 节与进度图）。

## 1. 代码结构

| 文件 | 作用 |
|---|---|
| `sdcfuzz/operand_heuristic.py` | 本地操作数启发式（非上游 D13）：进位链、翻转密度、屏蔽判定与确定性选择 |
| `sdcfuzz/isa.py` | AArch64 子集：指令描述、汇编渲染、Python 参考解释器、校验和契约 |
| `sdcfuzz/templates.py` | 19 条模板（目标结构、CHAOS 注入器、指令体） |
| `sdcfuzz/generator.py` | 生成自校验 AArch64 guest（m5 work-item 窗口 + 16-hex 校验和） |
| `sdcfuzz/evaluate.py` | 编译/运行全部模板，采集 RF/L1/FU 指标，写 `corpus_index.json` |
| `sdcfuzz/cli.py` | `list` / `generate` / `heuristic` / `evaluate` 入口 |
| `tests/test_sdcfuzz_{operand_heuristic,generator}.py` | 15 项主机侧单元测试（不需要 gem5） |
| `scripts/test-sdcfuzz-baseline.py` | 19/19 真实 gem5 回归 + D13 变体 + FI 闭环冒烟 |

## 2. 本地操作数启发式（不是上游 D13）

上游 D13 的做法（`sdc_probe_workload_d13.c`）：每次用固定种子 RNG 生成两个
随机 64 位候选 A、B，对 A 施加定向变异（异或随机 mask、+1、循环左移、再与
`~A` 异或），再用 `popcount(x ^ (x+1))`（尾部连续 1 的长度，进位链代理）
比较变异值与原随机值，保留较大者；同时保留若干纯随机操作数以维持覆盖广度。
它运行在 guest 内部、每次迭代都重新选择。

本节描述的是**另一个**主机侧启发式，仅作为本仓库的可选对照；它把路线文档
描述的两个要素（进位链近似 ACE、避免固定值逻辑屏蔽）写成可检验规则：

```text
carry_chain(a, b) = a + b 过程中进位连续保持为 1 的最长位数
toggle_bits(a, b) = popcount(a ^ b)
score(a, b)       = (carry_chain, toggle_bits, a)     # 字典序
masking_risk(a, b) = a ∈ {0, 1, 2^64-1} 或 a == b 或 toggle_bits(a, b) < 8
select(pool, ref)  = argmax(score) over pool \ {masking_risk == True}
```

参考操作数本身允许是 0（累加种子）：`x + 0` 不会屏蔽单 bit 故障；被拒绝的是
**候选值**是固定常量、与参考值完全相同，或与参考值差异位少于 8 位的情况。
候选项由结构化位模式（1–8 位周期的重复块及其取反）加 SplitMix64 确定性
随机扩展组成，因此同一 `seed` 永远得到同一选择。

`python3 -m sdcfuzz.cli heuristic --reference 0x00ff00ff00ff00ff` 会打印选中的操作数
及其进位链、翻转位数；`generate --operand-heuristic` 用该值替换模板里 x12 的常量。

## 3. 19 条模板

每条模板 = 一组初始化 + 一个在 m5 ROI 内重复 16 次的指令组。目标结构是
gem5 能真实测量的六类之一；FP 模板目前没有结构指标，明确标为 `none`，
不伪造激活值。下表是 `iterations=40`（每条模板 40×16 个指令组）时的实测
目标结构激活：

| 模板 | 说明 | 目标 | 注入器 | 目标激活 |
|---|---|---|---|---|
| `alu-add-carry` | 整数加法进位链 | alu | CHAOSExec | 91904 |
| `alu-sub-borrow` | 整数减法借位链 | alu | CHAOSExec | 91904 |
| `alu-eor-toggle` | 逻辑异或翻转 | alu | CHAOSExec | 91904 |
| `alu-and-mask` | 逻辑与掩码 | alu | CHAOSExec | 91904 |
| `alu-add-shifted` | 移位加法 | alu | CHAOSExec | 91776 |
| `mul64` | 64 位乘法 | mult | CHAOSExec | 123264 |
| `mul32` | 32 位乘法 | mult | CHAOSExec | 61824 |
| `madd64` | 乘法累加 | mult | CHAOSExec | 123264 |
| `div64` | 64 位无符号除法 | div | CHAOSExec | 81920 |
| `div32` | 32 位无符号除法 | div | CHAOSExec | 40960 |
| `l1d-load-hot` | L1D 热行重复读 | l1d | CHAOSCache | 647 |
| `l1d-load-stream` | L1D 多行顺序读 | l1d | CHAOSCache | 3852 |
| `l1d-store-hot` | L1D 热行重复写 | l1d | CHAOSCache | 643 |
| `l1d-load-store` | L1D 同址写后读 | l1d | CHAOSCache | 650 |
| `l1i-big-body` | L1I 大指令足迹 | l1i | CHAOSCache | 1333 |
| `dep-chain` | 长依赖链 | alu | CHAOSPhysReg | 174208 |
| `branch-busy` | 分支密集小循环 | alu | CHAOSBPU | 1463424 |
| `fp-add` | 双精度浮点加法 | none | CHAOSFPU | — |
| `fp-mul` | 双精度浮点乘法 | none | CHAOSFPU | — |

激活值的口径与 Phase 1 的结构指标一致：alu/mult/div 是 FU 输入位数，
l1d/l1i 是需求访问次数。不同模板的指令组大小不同，因此跨结构不可比；
同一结构内可直接比较（例如 `l1d-load-stream` 的 3852 远高于热行读的 647）。

## 4. 生成与自校验

`generator.render_guest()` 先把模板交给 `isa.py` 的 Python 解释器执行
`iterations × 16` 遍，算出期望校验和，再把同一个模板渲染成汇编嵌进 guest。
guest 在 `m5_work_begin(7, 0)`/`m5_work_end(7, 0)` 之间运行指令组，结束后对
6 个 GPR、4 个 FP 寄存器和 128 字数据缓冲区做与 Python 完全相同的 FNV
折叠，打印：

```text
template=mul64 target=mult status=PASS
0123456789abcdef        # 与参考解释器逐位一致
```

因此“PASS”不是自己和自己比：期望值来自独立实现，且校验和格式与
`tools/classify.py` 兼容（独立的 16-hex 行），故障注入结果可以直接被现有
分类器消费。

## 5. 评估与故障注入闭环

```bash
# 19 条模板全部真实运行（约 20 s）
python3 scripts/test-sdcfuzz-baseline.py \
  --gem5 CHAOS/gem5/build/ARM_ACE_IBR_AUDIT/gem5.opt

# 只生成结构索引
python3 -m sdcfuzz.cli evaluate --outdir m5out/sdcfuzz-baseline/corpus \
  --iterations 40

# 单模板 + D13 操作数
python3 -m sdcfuzz.cli generate --id alu-add-carry --operand-heuristic \
  --outdir m5out/sdcfuzz-generated
```

`corpus_index.json` 给出每条模板的计数器、覆盖向量、目标激活以及按目标
结构的排名（schema `sdcfuzz.phase0.corpus_index.v1`）。

回归脚本最后做一次真实的故障注入闭环：对 `alu-add-carry` 生成物用
CHAOSReg 在 cycle 1000 注入 1 个 bit flip（`--target_reg_idx=12`），按
`tools/classify.py` 分类。实测结果是 **Masked**（校验和等于 golden）。
这不是失败：CHAOSReg 是架构状态注入器，O3 下在途指令使用的是重命名后的
物理寄存器，架构寄存器写回不会改变已经发射的循环操作数——与
`summary.md` 记录的“architectural-state baseline”限制一致。要得到传播性
证据应使用 CHAOSPhysReg/CHAOSExec，那属于 Phase 3 的注入闭环工作，不与
本基线混为一谈。

## 6. 与外部证据的边界

| Phase 0 交付物 | 状态 | 说明 |
|---|---|---|
| D13 启发式 | 上游已完成（外部证据） | `gem5_config/workloads/sdc_probe_workload_d13.c`；原 exp02 bit 3.143× / struct 12.8×；sdc-0103 复现 bit 2.833× / struct 12.8×（均 BEAT），详见 `d13-baseline-reproduction.md` |
| 19 模板 | 上游已完成（外部证据） | `seeds/*.S`，本仓库无副本 |
| gem5-CHAOS | 本仓库实测 | 19 注入器 + 一次 CHAOSReg 分类闭环 |
| 4 板真机部署 | 上游已完成（外部证据） | sdcfuzz 论文/文档记录；本机无该硬件 |
| p2 草稿 | 上游已完成（外部证据） | 外部仓库；本仓库无副本 |
| 本地操作数启发式 | 支撑件（非交付） | 与 D13 不同物，仅作可选对照，15 项单测 |
| 本地 19 条结构语料 | 支撑件（非交付） | 19/19 PASS，与上游 19 模板无逐条对应 |

进度图对“本仓库实测”和“外部证据”用不同颜色，并在每个阶段显示
“完成 x/y · 实测 a/y”，避免把外部已有资产读成本仓库完成。
