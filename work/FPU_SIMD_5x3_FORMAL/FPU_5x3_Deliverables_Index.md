# FPU/SIMD 5×3 正式实验 — 阶段性交付材料索引

- 批次：`FPU_SIMD_5x3_FORMAL`
- 生成：2026-11-23（无人值守连续执行完成）
- 权威方案：`/home/sdc/gem5-fi-fpu/inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx`（24–30 工作表）
- 数据基目录：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/`

> 本索引只报告**实际完成**数量；不修改原始数据、不重跑、不删除历史结果。
> 所有路径为服务器绝对路径。

---

## 一、实际执行统计（非计划）

| 指标 | 实际值 |
|---|---:|
| 正式运行总数（Fault + Control） | **240** |
| Fault 运行 | **180**（12 模型 × 5 上下文 × 3 时机） |
| Control 基线 | **60**（12 模型 × 5 上下文） |
| Count-only 预扫描 | **60**（全部 READY） |
| COMPLETED | **240** |
| FAILED | **0** |
| TIMEOUT | **0** |
| BLOCKED | **0** |
| 基础设施执行失败（INFRA_FAIL：超时/崩溃/非零退出） | **0** |
| Oracle 评估失败（ORACLE_FAIL：无法归因/无法比对） | **0** |

**Fault/Control 校验**（基础设施侧）：
- FaultApplied=1 的 fault 运行：**180/180**（注入命中 100%）。
- FaultApplied=0 的 control 运行：**60/60**（无控制组被误注入）。
- 全部退出码 = 0；events.jsonl 全部非空。

---

## 二、终态分类（Oracle 结果，非基础设施失败）

| OracleResult | 数量 | 含义 |
|---|---:|---|
| `WRONG_RESULT`（SDC） | **144** | 错误传播到最终软件输出（C01/C02/C04/C05） |
| `MASKED_OVERWRITE` | **36** | 错误产生但被覆盖/未消费（C03） |
| `CONTROL_OK` | **60** | 控制基线正常、无注入 |

> 说明：`WRONG_RESULT`/`MASKED_OVERWRITE`/`CONTROL_OK` 是**终端语义分类**，
> 由「fault_inject + 物理寄存器消费者关联 + commit/squash + 逐迭代 raw 输出比对」
> 共同决定，不是基础设施执行失败。本批次 **ORACLE_FAIL = 0**。
>
> **SQUASHED 注入侧计数 = 0**：动态时机公式 `ordinal=ceil(q×N)` 下 C05 的
> T01/T02/T03（7/32/58）均落在已提交合格执行上；squash 发生在末次 ordinal=64
> （每个 C05 trace 均记录真实 mispredict + 对该末次执行的 squash 事件），
> 未人为制造「注入后被 squash」。

---

## 三、交付材料清单（绝对路径）

### 1. 最终执行报告
- `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Execution_Final_Report.md`

### 2. Preflight 审计报告
- `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Preflight_Audit.md`

### 3. Count-only Manifest（60 组预扫描）
- `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_CountOnly_Manifest.csv`
- 结构化数据：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/counts/manifest.json`

### 4. 完整 Fault/Control Run Manifest（240 行）
- `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Run_Manifest.csv`
- 列：RunID / ModelID / ContextID / WhenID / FaultControl / Status / ExecOutcome /
  OracleEvaluation / OracleResult / InjectionCount / EligibleEventCount /
  TargetOrdinal / ExitCode / SummaryJSON / EventsJSONL / Stdout

### 5. Fault/Control 结果汇总
- 240 行合并统计：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Full_Statistics.csv`
- 180 行传播证据：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Propagation_Evidence.csv`
- 终态统计 JSON：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Propagation_Summary.json`

### 6. Trace 文件索引（300 个 events.jsonl 的绝对路径 + 字节数）
- `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Trace_Index.csv`
- 原始 Trace 本体（未打包，留在原地）：
  - Fault/Control：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/runs/<RunID>/events.jsonl`（240 个）
  - Count-only：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/counts/M<MM>_<Cxx>/events.jsonl`（60 个）

### 附：可复现源码与负载
- 编排/分析脚本：`/home/sdc/gem5-fi-fpu/scripts/gen_5x3_workloads.py`、
  `/home/sdc/gem5-fi-fpu/scripts/run_5x3.py`、
  `/home/sdc/gem5-fi-fpu/scripts/analyze_5x3.py`
- 60 个上下文负载源码：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/workloads/src/fpu_<MM>_<Cxx>.S`
- 60 个 ELF：`/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/workloads/build/fpu_<MM>_<Cxx>`
- gem5 注入 hook（未改动，位于源码树）：
  `/home/sdc/gem5-fi-fpu/gem5/src/cpu/o3/FPUInjector.cc`（及其 `fplib.cc`/`neon64.isa` 埋点）

---

## 四、状态标记说明

- **COMPLETED**：运行正常退出（rc=0），Trace 完整，注入/控制状态正确。
- **FAILED** / **TIMEOUT** / **BLOCKED**：本批次均为 0（无此类运行）。
- **Oracle 终态**（WRONG_RESULT / MASKED_OVERWRITE / CONTROL_OK）与
  **基础设施失败**（FAILED/TIMEOUT）是两个独立维度，已在 Run Manifest 中以
  `ExecOutcome` 与 `OracleResult` 分列，避免将终端软件错误与执行失败混淆。

---

## 五、数据保护确认

- 历史数据 `results/`、`runs/`、`reports/`、`reproduction/`：**未改动**（mtime 仍为 2026-11-16）。
- MMU 工作区 `/home/sdc/gem5-fi-mmu-impl-v2`、参考树 `/home/sdc/gem5-fi-ding`：**零写入**。
- 本轮全部产物位于 `/home/sdc/gem5-fi-fpu/work/FPU_SIMD_5x3_FORMAL/`。