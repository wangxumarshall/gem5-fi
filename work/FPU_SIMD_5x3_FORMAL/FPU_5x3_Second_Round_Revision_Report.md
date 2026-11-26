# FPU/SIMD 5×3 第二轮修订执行报告

批号 `FPU_SIMD_5x3_FORMAL` · 生成 2026-11-23 · 工作目录 `/home/sdc/gem5-fi-fpu`

> 本轮为**修复诊断完整性**，非为获得预期结果。不重跑 C01/C02/C04，不删除历史
> 数据，不修改 MMU 工作区，不 Git push。

---

## 1. 重跑范围与保留范围

| 范围 | 处置 | 说明 |
|---|---|---|
| C03（12 模型 × 3 时机 + control） | **重跑** | 修复“覆盖前已消费” |
| C05（12 模型 × 3 时机 + control） | **重跑** | 修复“T03 未 squash” |
| C01 / C02 / C04 | **保留** | 未受影响，不重跑 |
| 第一轮全部运行与 Trace（`runs/`、`counts/`） | **保留** | 未覆盖、未删除 |
| M008/M012 原始证据 | **保留** | 未覆盖 |
| 旧负载源码/ELF | 备份 | `workloads_pre_r2_backup/` |

**重跑规模**：72 Fault + 24 Control = **96 运行** + 24 count-only，全部写入
`runs_r2/`、`counts_r2/`（与第一轮 `runs/`、`counts/` 物理隔离）。

---

## 2. 每个修改的原因

1. **C03**：第一轮 `FADD→FMOV(消费)→STR(导出)→FMOV(覆盖)` 中错误在覆盖前已
   被消费者读入并写入输出缓冲区，实际是 WRONG_RESULT；判 MASKED_OVERWRITE 错误。
2. **C05**：第一轮 N=64、T03=58 注入的错误最终 Commit（SDC），未证明错误随
   squash 消失；且 N=64 下 squash 只发生在末次 ordinal=64，`ceil(0.9N)=58` 无法
   命中。修订为“训练(40)与测量(9)解耦”，使 T03=9 命中误预测推测执行。
3. **分析器**：物理寄存器编号匹配有重用误关联；改为 arch+writer 版本因果追踪，
   并新增 MASKED_NO_CONSUMER / PARTIAL_TRACE / OTHER 等终态。

（汇编级 before/after 见 `FPU_C03_C05_Workload_Revision.md`。）

---

## 3. 新旧 eligible-event 与 ordinal

| 上下文 | 旧 N | 旧 ordinal | 新 N | 新 ordinal | 变化原因 |
|---|---|---|---|---|---|
| C03 | 100 | 10/50/90 | 100 | 10/50/90 | 仅指令顺序变化，N 不变 |
| C05 | 64 | 7/32/58 | 9 | 1/5/9 | 训练解耦；T03 命中 squash |

C05 新 N=9：N≥3、ordinal 互异（1/5/9）。T01/T02 在已提交测量目标上（错误提交
传播 → SDC），T03=9 在误预测推测路径上（错误 squash）。

---

## 4. 实际 Fault/Control 执行结果

| 指标 | 实际 |
|---|---:|
| 重跑运行总数 | 96（72 Fault + 24 Control） |
| COMPLETED | **96** |
| FAILED / TIMEOUT / BLOCKED | 0 |
| FaultApplied=1（fault） | 72/72 |
| FaultApplied=0（control） | 24/24 |
| 退出码非 0 | 0 |

---

## 5. 修订后终态分类（72 fault 运行，证据驱动）

| 终态 | 数量 | 证据 |
|---|---:|---|
| **MASKED_OVERWRITE** | 36 | fault_inject 命中 + target_end 记录错误值 + 覆盖在首消费者前（n_direct=0, overwritten=True）+ raw0/raw2 与 Control 一致 |
| **WRONG_RESULT** | 24 | C05 T01/T02：目标提交 + raw0 与 Control 存在可归因差异 |
| **SQUASHED** | 12 | C05 T03：目标 seq 出现在 squash 事件 + branch_mispredict（pred_taken=true/actual_taken=false） |
| INJECTION_MISS / PARTIAL_TRACE / OTHER | 0 | — |

---

## 6. 是否真正获得 Masked 与 Squashed 证据

**MASKED_OVERWRITE —— 是**。36 个 C03 均满足五项证据：故障实际发生
（`fault_inject` 命中、`applied=1`）；错误值实际产生（`target_end` dest 记录错误
值，如 M001 `0x40800005`、M008 lane7 `0x00` vs 饱和 `0xFF`、M012 旧低半区置零）；
覆盖发生在首次消费前（写型覆盖 `fmov/mov/cmp/movi`，`n_direct=0`，
`overwritten=True`）；正确值覆盖错误状态；最终软件输出与 Control 逐字节一致
（`raw0_diff=False`）。

**SQUASHED —— 是**。12 个 C05 T03 满足：真实分支误预测（`branch_mispredict`
pred_taken=true / actual_taken=false）；目标动态指令在预测 taken 路径上被推测
执行；恢复时该目标 seq 被 squash（`squash` 事件含目标 PC），`target_squashed=True`，
fault 施加于该被 squash 的目标（`fault_inject` 命中、`applied=1`），错误未达
架构状态。未人工制造 squash Trace，未改目标提交状态，未把 T03 改成 100%。

---

## 7. 交付物

`work/FPU_SIMD_5x3_FORMAL/` 下：
1. `FPU_5x3_Second_Round_Audit.md`
2. `FPU_C03_C05_Workload_Revision.md`
3. `FPU_Propagation_Analyzer_Revision.md`
4. `FPU_5x3_Rerun_Manifest.csv`（96 行：新旧 N/ordinal、状态、绝对路径）
5. `FPU_5x3_Propagation_Evidence_R2.csv`（72 行修订后传播证据）
6. `FPU_5x3_Propagation_Summary_R2.json`
7. `FPU_5x3_Second_Round_Revision_Report.md`（本报告）

修订后 Trace：`runs_r2/<RunID>/events.jsonl`、`summary.json`、`stdout.txt`、`stderr.txt`；
count-only：`counts_r2/M<MM>_<Cxx>/`。

脚本：`scripts/gen_5x3_workloads.py`（C03/C05 修订）、
`scripts/run_5x3_r2.py`（重跑驱动）、`scripts/analyze_5x3_r2.py`（修订分析器）。

---

## 8. 结论

第二轮修订修复了 C03 的“覆盖前消费”误判与 C05 的“T03 未 squash”缺失，并将传播
分析器升级为版本感知的因果追踪。修订后：**36 个真正 MASKED_OVERWRITE**（错误
产生但首消费前被覆盖，输出与 Control 一致）与 **12 个真正 SQUASHED**（错误施加
于误预测推测执行、恢复时 squash，未达架构态）获得完整证据支撑；C05 T01/T02 的
24 个错误仍正确提交传播为 WRONG_RESULT。第一轮 C01/C02/C04 及全部历史数据保留。