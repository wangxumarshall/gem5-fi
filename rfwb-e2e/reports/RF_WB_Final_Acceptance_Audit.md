# RF/WB Final Acceptance Audit

基线：`2f4e00b4`；原始设计基线 `226778cf` = `NOT_RECOVERABLE`；源码注入补丁与二进制 SHA 见 `reproduction/RF_WB_Source_Freeze_Manifest.tsv`。

## 1. 最终样本与终态

- 75 个最终 Fault 条件：62 Batch03 + 13 Batch02 M004 `REUSED_BATCH02_FINAL`。
- 25 个 Control：`TRACE_NOT_COLLECTED`，25/25 OUT 与独立 golden 一致。
- 25 个预扫描：20 Batch02 + 5 Batch03 M005 修正扫描。
- 20 个历史不可恢复 Attempt：`HISTORY_UNAVAILABLE`，路径与 SHA 为空。
- 终态：`ACTIVATED_SDC` 32；`ACTIVATED_MASKED` 28；`ACTIVATED_SQUASHED` 2；`ROB_HEAD_BLOCKED` 13。

## 2. Attempt Ledger

- 行数：145（25 Control + 75 Fault + 25 Prescan + 20 History）。
- 13 个 M004 Batch02 样本使用 `REUSED_BATCH02_FINAL`，真实 Trace 路径与 SHA256 已填写。
- 20 个 HISTORY_UNAVAILABLE 的 `RetainedTrace`/`TraceSHA256` 为空，未复制历史哈希。
- M005 六个修正 Timing 使用实际 `-A3` SampleRunID 与 `Batch03_traces/...-A3.csv`。

## 3. 验收 Gate

| Gate | Area | Status | 证据/理由 |
|---|---|---|---|
| A01 | Where preservation | PASS | 基线 commit + 最终注入补丁 SHA；5 个模型、Hook、故障操作与持续性未改 |
| A02 | 5×3 completeness | PASS | 20_When_5x3_75 共 75 个唯一 model/context/timing 行 |
| A03 | Control reuse | PASS | 25/25 Control 完成，25/25 OUT 匹配 golden；无 Trace |
| A04 | Distinct eligible events | PASS | 25 个预扫描 N≥3 且 10/50/90% ordinal 不重复；M005 修正 N=6/6/8/6/8 |
| A05 | Same hook and operation | PASS | 全部 75 个样本使用同一补丁/Hook；仅 ordinal/动态实例不同 |
| A06 | One activation | PASS | 每个 Fault Trace 恰好 1 个注入事件；Control 为 0 |
| A07 | Causal propagation | PARTIAL | 五份报告 + 矩阵覆盖直接记录步骤；下游 consumer commit / M005 writeback / M004 数据传播为 NOT_OBSERVED |
| A08 | Model-specific feasibility | PASS | M004 只计已执行且未 squash 的通知事件；M005 证明 WB-before-Rename |
| A09 | No forced outcomes | PASS | 检测/覆盖/squash/hang/SDC 均按证据；阻塞样本不标软件输出 |
| A10 | Scope boundary | PASS | 范围仍为 GPR/FP-SIMD PRF、read-return、IEW completion、global ready |

## 4. 最终判定

- **Overall Acceptance：PARTIAL**，唯一未通过项为 A07（因果传播完整性）。
- **Propagation Acceptance：PARTIAL**；`NOT_OBSERVED` 步骤保留为空，未用推断冒充直接观察。
- **ConfigFrozen：NO**；未打包完整 gem5 源码树，但 commit/tree/patch/binary/build log/ELF 的 SHA 已记录。在完整源码与补丁冻结清单满足前不得改为 YES。

## 5. 交付一致性

- 报告、矩阵、Ledger、Excel 使用同一 final classification 与 sample identity。
- `traces/` 与 Batch01/02/03 原始 Trace 的 SHA 基线见 `reproduction/RAW_TRACES_SHA256_BASELINE.txt`；本轮未改写任何原始 Trace。
- 原始设计工作簿 `inputs/gem5-fi-RF_WB-Final-Paper-Experiment-Plan.xlsx` 未修改。
