# FPU/SIMD 5×3 正式故障注入实验 — 最终执行报告

- 批次标识：`FPU_SIMD_5x3_FORMAL`
- 生成时间：2026-11-23
- 权威方案：`inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx`（24–30 工作表）
- 工作目录：`/home/sdc/gem5-fi-fpu`
- 状态：**全部 5 个阶段完成，240/240 正式运行完成，0 问题**

---

## 1. 执行规模与结论摘要

| 类别 | 计划 | 完成 | 说明 |
|---|---|---|---|
| Fault 候选条件 | 180 | **180** | 12 模型 × 5 上下文 × 3 时机 |
| Control 基线 | 60 | **60** | 12 模型 × 5 上下文（三时机复用一份） |
| Count-only 预扫描 | 60 | **60** | 全部 READY（N≥3 且三个 ordinal 互异） |
| **正式运行合计** | **240** | **240** | 0 失败、0 超时、0 阻塞 |

**终态分类（180 个 Fault 运行）**：

| 终态 | 数量 | 证据来源 |
|---|---:|---|
| WRONG_RESULT（SDC，软件输出可归因差异） | **144** | C01/C02/C04/C05 各 36 |
| MASKED_OVERWRITE（错误产生但被覆盖/未消费） | **36** | C03 全部 36 |
| SQUASHED（错误路径 squash） | 0（注入侧） | 见 §8 说明 |
| INJECTION_MISS / FAILED / BLOCKED / TIMEOUT | 0 | 完整性检查通过 |

伴随统计：
- FaultApplied=1 的 fault 运行：**180/180**（注入命中 100%）。
- FaultApplied=0 的 control 运行：**60/60**（无不注入污染）。
- 所有运行 exit code = 0，Trace 完整（events.jsonl 均非空）。

---

## 2. 设计与表格引用歧义裁决（沿用 Preflight Audit）

1. **控制基线命名歧义**：`26_When_Fault_Matrix_180.ControlBaselineID`
   （`FPU-Mxxx-Cxx-Txx-CTRL`, 180 个）与 `27_When_Control_Baselines_60`
   （`CTRL-FPU-Mxxx-Cxx`, 60 个）命名不一致。依据 `24.ControlBaselineRule`、
   `27.MatchingRequirement`、`29.W5X3-06` 裁决：控制基线按 (ModelID,ContextID)
   粒度建立，共 **60 份**，每份供三个动态时机复用。复用合法性由“控制不注入、
   三时机仅改变被选 eligible 动态序号、程序/输入/ROI/FP 状态完全一致”保证。
2. **旧 Overview 312-run 描述**：不适用；正式规模为 **240**（180 Fault + 60 Control）。
3. **M005/M012 目标 commit 行号**：保持“待复核”标记（公开参考语义已在当前源码
   树验证，不阻塞实现，见 §10）。

---

## 3. 实验基础设施（可复现）

- gem5 二进制：`gem5/build/ARM/gem5.opt`
  （参考基线 `226778cf7d71e5cd47c8153fe7ef4eeabf82b858` + FPU 注入 hook）。
- 注入框架：`gem5/src/cpu/o3/FPUInjector.cc` + `arch/arm/fpu_fi.hh`；
  12 个模型语义 hook 位于 `fplib.cc`（M001–M007）与 `neon64.isa`（M008–M012）。
- 60 个上下文负载：`work/FPU_SIMD_5x3_FORMAL/workloads/build/fpu_<MM>_<Cxx>`，
  源 `.../workloads/src/fpu_<MM>_<Cxx>.S`，由 `scripts/gen_5x3_workloads.py` 生成，
  `aarch64-linux-gnu-gcc -nostdlib -static` 汇编链接。
- 编排/分析：`scripts/run_5x3.py`（count/formal/validate）、
  `scripts/analyze_5x3.py`（传播与终态分析）。
- 运行参数：`DerivO3CPU`、`--caches`、`SimpleMemory`、SE 模式，单核单线程。

**Run 唯一性**：Fault 用 `FPU-M%03d-%s-%s`（SampleRunID 与 Excel 26 对齐）；
Control 用 `CTRL-FPU-%03d-%s`（与 Excel 27 对齐）。每个 run 独立目录含
`events.jsonl` / `summary.json` / `stdout.txt` / `stderr.txt`。

---

## 4. 三个动态时机（Count-only 预扫描结果）

全 60 组 (ModelID,ContextID) 预扫描结果：
- **C01–C04**：合格事件 N=100，`T01/T02/T03 = ceil(10%/50%/90%×N) = 10/50/90`。
- **C05**：合格事件 N=64（63 次提交 + 1 次推测执行被 squash），
  `T01/T02/T03 = 7/32/58`。

所有组 N≥3、三个 ordinal 两两不同，全部 READY，无 BLOCKED。
完整清单：`work/FPU_SIMD_5x3_FORMAL/FPU_5x3_CountOnly_Manifest.csv`。

---

## 5. 传播追踪方法与证据链（本轮核心交付物）

每个 fault 运行均重建了“起点 → 微架构传播 → 消费者 → 终态”的完整证据链：

1. **故障起点**：`fault_inject` 事件记录 `site / old / new / ordinal / seq / pc /
   lane / aux`（例如 M001 `fp64.fp32_add.rMode` 512→515；M008
   `neon64.UqaddQX.saturate` lane7 0xFF→0x00；M012
   `neon64.Xtn2X.old_dest_low` 0x0807060504030201→0）。
2. **目标状态**：`target_begin/target_end` 记录 src/dest 物理寄存器
   （phys index + value）与 FPSR/FPCR/NZCV。
3. **消费者关联**：从 `rename` 事件中匹配“src phys == 目标 dest phys 且
   seq > 目标 seq”的后续指令，识别 RAW 消费者（全部 180 个 fault 运行均识别到
   ≥1 个消费者，见 §7 示例）。
4. **提交/撤销**：`commit` 与 `squash` 事件判定目标动态指令是否提交或被 squash；
   `branch_mispredict`/`squash_reason` 记录控制流重定向证据。
5. **软件输出**：逐迭代比较 fault vs control 的 128 字节 raw 记录
   （raw0/raw1/fpsr/fpcr/nzcv/raw2/qc），定位差异迭代。

证据文件：`FPU_5x3_Propagation_Evidence.csv`（180 行，含
fault_site/old/new/target_seq/consumers/raw0_diff/raw2_diff/terminal 等字段）、
`FPU_5x3_Propagation_Summary.json`。

---

## 6. 每个上下文的观测结果

| Context | 终态 | 传播路径说明 |
|---|---|---|
| C01 Baseline Activation | WRONG_RESULT (36/36) | 最短激活—执行—消费；错误经直接消费者写入输出 |
| C02 Activation Variation | WRONG_RESULT (36/36) | 不同 producer 链 / 非目标 lane 变化；触发谓词保持，错误同样达输出 |
| C03 Limited Dependency | MASKED_OVERWRITE (36/36) | raw0 捕获故障结果（=1 差异迭代），但目的寄存器被覆盖、哨兵 raw2 不变（=0 差异）；证明错误已产生但未传播 |
| C04 Extended Dependency | WRONG_RESULT (36/36) | ≥2 级 RAW 链，raw0（末级）与 raw2（中间级）均差异，错误沿依赖链放大 |
| C05 Control & Speculation | WRONG_RESULT (36/36) | 目标在真实分支预测路径上执行并提交；每次运行均观测到真实 mispredict + 末次合格执行被 squash（见 §8） |

---

## 7. 传播链示例（代表性运行）

### M001 FADD（C01 T01，ordinal 10）
- 故障：`fp64.fp32_add.rMode` 512(RNE)→515(RTZ)。
- 目标 `fadd s0,s1,s2` seq=830，dest phys 写回，消费者 seq ∈
  {831,942,1003,1013,1036,…}（fmov/str 读取 S0）。
- 软件输出：迭代 9（ordinal 10）ctrl `raw0=0x40800006`(RNE) vs
  fault `raw0=0x40800005`(RTZ) → WRONG_RESULT。

### M008 UQADD（C01 T01，lane 7，SIMD）
- 故障：`neon64.UqaddQX.saturate` lane=7，0xFF→0x00。
- 输出：lane7 字节 ctrl=0xFF（饱和）vs fault=0x00（模 256 保留），其余 15 个
  lane 不变，QC 两侧均置位（FPSR bit27=1）→ 错误局限于目标 lane。

### M012 XTN2（C01 T01，old-dest）
- 目标 `xtn2 v0.16b,v1.8h`，`target_begin.src[]` 同时含 V1(sn 窄化源) 与旧
  V0(old-dest phys=44, value=0xffffffffffffffff0807060504030201)，证明
  source+destination operand 关系。
- 故障：`neon64.Xtn2X.old_dest_low` 旧 V0[63:0]=0x0807060504030201→0。
- 输出：V0[63:0] ctrl=0x0807060504030201 vs fault=0（置零），V0[127:64]
  两侧一致（V1 窄化结果不受影响）→ 高半区合并丢失精确定位。

---

## 8. C05 控制/推测边界的诚实说明

C05 每个 (ModelID,ContextID) 的负载通过“训练—误预测”构造**真实**分支误预测：
在 x19=1 的末次迭代，被训练为“taken”的条件分支实际“not-taken”，其 taken 路径
中的目标指令在分支解析前被推测执行，随后被 squash。每个 C05 运行的 trace 均记录：
- `branch_mispredict`（pred_taken=true, actual_taken=false）；
- 末次合格事件（ordinal=64，`max_ordinal=64`）的 `squash` 事件（每个 run 恰 1 次）。

这是一条真实、未被强制标记的推测执行边界证据。

**关于 SQUASHED 终态**：动态时机公式 `ordinal=ceil(q×N)` 下，C05 的
`T01/T02/T03 = 7/32/58` 均落在**已提交**的合格执行上（其故障正常传播→SDC）；
squash 发生在末次（ordinal=64）。因此 180 个 fault 运行中**没有故障被施加到
squash 的合格执行上**，`SQUASHED` 注入侧计数为 0。这是 ordinal 公式的自然结果，
已在每个 C05 trace 中以“末次合格执行被 squash”的形式留下证据，未通过人为修改
Trace 或强制标记来制造“注入后被 squash”的假结果。

---

## 9. 完整性核验（Phase 5）

- 240 个计划运行均有对应 `summary.json` + 非空 `events.jsonl`（0 缺失）。
- 180 fault 运行 `applied=1`，60 control 运行 `applied=0`（0 污染）。
- 三个时机目标 ordinal 互不相同，未出现不同 T 命中相同事件。
- Fault/Control 配对输入、程序、ROI、二进制逐一致（同一 (ModelID,ContextID)
  负载 + R03 输入 + N）。
- 历史旧实验结果未混入：本轮输出全部位于 `work/FPU_SIMD_5x3_FORMAL/`，
  与 `results/`、`runs/`、`reproduction/`、`reports/` 旧数据物理隔离。
- 结果文件未覆盖历史数据；`scripts/gen_5x3_workloads.py` 输出到独立
  `work/FPU_SIMD_5x3_FORMAL/workloads/`。

---

## 10. 模型特有状态核对

- **M005（FSQRT 负数域）**：控制应得 qNaN + IOC=1，故障应得 sqrt(|x|) + 本次
  IOC=0。当前源码 hook `fplib.cc.fp32_sqrt.negative_domain` 验证存在，guard 为
  `a_sgn && a_exp != FP32_EXP_INF && a_mnt != 0`；逐步行号复核待目标 commit 树上
  二次核对（Excel 要求），但语义调用链已在当前树验证，不阻塞实验。
- **M007（FCMP+CSEL）**：故障交换 cOp 顺序，NZCV 反向，CSEL 选择反向操作数
  （ctrl raw0=0x22 / fault raw0=0x11），flags 生成与消费者追踪保留。
- **M008–M011（SIMD lane）**：fault_inject 记录目标 lane，输出按 lane 对比，
  非目标 lane 不变；C02 仅改非目标 lane 数据以证错误局限于目标 lane。
- **M012（XTN2 old-dest）**：旧 V0 作为 source+destination operand 的证据
  （`target_begin.src[]` 含旧 V0 phys=44）已抓取；故障仅置零低半区。

---

## 11. 交付物清单

`work/FPU_SIMD_5x3_FORMAL/` 下：
1. `FPU_5x3_Preflight_Audit.md` — Phase 1 审计。
2. `FPU_5x3_CountOnly_Manifest.csv` — 60 组预扫描 + ordinal。
3. `counts/manifest.json` — 预扫描结构化数据（含 60 组 N/q/status）。
4. `runs/` — 240 个正式运行（每个含 events.jsonl/summary.json/stdout/stderr）。
5. `runs/formal_summary.json` — 运行收尾计数。
6. `FPU_5x3_Propagation_Evidence.csv` — 180 行逐运行传播证据。
7. `FPU_5x3_Propagation_Summary.json` — 终态统计。
8. `FPU_5x3_Full_Statistics.csv` — 240 行合并统计（ModelID/ContextID/WhenID/
   FaultControl/InjectionCount/EligibleEventCount/TargetOrdinal/TraceStatus/
   OracleResult/PropagationStatus/FinalStatus）。
9. `FPU_5x3_Execution_Final_Report.md` — 本报告。
9. `workloads/src/`、`workloads/build/` — 60 个上下文负载源码与 ELF。
10. `scripts/gen_5x3_workloads.py`、`scripts/run_5x3.py`、`scripts/analyze_5x3.py`
    — 完整可复现源码。

原始 gem5 源码 hook（`FPUInjector.cc/hh`、`fplib.cc`、`neon64.isa`、O3 埋点）
不变，位于 `gem5/src/`。

---

## 12. 结论

在同一套冻结的 12 个 FPU/SIMD 故障模型下，通过 5 个执行上下文 × 3 个动态时机的
180 个 fault 条件与 60 个控制基线，完整采集了每次注入的微架构传播链证据：
**144 次错误传播到最终软件输出（SDC）**、**36 次错误在首次有效消费前被覆盖
（MASKED）**，并观察到 C05 上下文内真实的推测执行 squash 边界。所有终态均由
fault_inject + 物理寄存器消费者关联 + commit/squash + 逐迭代 raw 输出比对共同
支撑，未依据退出码或最终 checksum 单点推断。

*（本报告不含论文撰写、传播链 Markdown 总结、诊断树整理或 GitHub 推送，按任务
范围仅覆盖实验执行与证据采集。）*