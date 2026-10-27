# R6 Excel 传播链回填 — 审计报告

- 生成时间：`2026-10-27T14:40:43`
- 原始 Excel：`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx`（181590 B）
  - SHA-256 `389546f0f8f3d0c6ece2ed33d3a8cfd1426faa9bbc101f7ad7d9612159e273e0`
  - 与执行前一致：**YES**；**原始 Excel 修改：NO**
- 结果 Excel：`docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-R6实验结果.xlsx`（364148 B）
  - SHA-256 `ba2e79afc97d008c874510f262ec43a0bc07b5268df65083c0f7e99807659f15`
- 证据根：`runs/lsu/r6_c9_*`（旧冻结二进制）、`runs/lsu/r6_n7_*`（新二进制）
- 目标工作表：`7.展开执行矩阵`；追加列 **AR–DN（75 列）**，原 43 列未改动

## 1. 回填统计

| 项 | 数量 |
|---|---|
| UNPROVEN | 191 |
| POLICY_EXCLUDED_F6 | 64 |
| BLOCKED | 53 |
| IN_PROGRESS | 9 |
| COMPLETE_3_OF_3 | 8 |
| **合计（325 个 RunID）** | **325** |

- **COMPLETE_3_OF_3：8**
- IN_PROGRESS（仅 seed1）：9
- 未完成/未运行：317

## 2. 8 个 COMPLETE_3_OF_3 的三 seed 摘要

| RunID | seed1 | seed2 | seed3 | binary |
|---|---|---|---|---|
| T01-F0-W4 | detected_contained | full | detected_contained | `e80528423fec` |
| T02-F0-W4 | full | full | full | `e80528423fec` |
| T02-F2-W4 | full | detected_contained | full | `e80528423fec` |
| T04-F0-W4 | full | full | full | `e80528423fec` |
| T04-F2-W4 | full | full | full | `e80528423fec` |
| T01-F1-W4 | full | full | full | `8a229009c933` |
| T01-F2-W4 | full | detected_contained | full | `8a229009c933` |
| T03-F5-W4 | full | full | full | `8a229009c933` |

## 3. 二进制分布（逐 seed 独立记录）

- `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`：15 个 seed
- `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`：9 个 seed

> 不同 RunID 允许使用不同冻结二进制；差异仅记录，不触发重跑（用户裁定 2026-10-27）。

## 4. 校验结果（23/23 PASS）

```
PASS 1 原始 Excel SHA 未变
PASS 2 结果文件可打开
PASS 3 工作表数不少于原始（12 = 12）
PASS 4 原始区域值/公式/合并单元格逐格一致（全部 12 张表）
PASS 5 RunID=325 且唯一
PASS 5b RunID 集合与 runid_map 一致
PASS 6 新增列只出现在结果文件（原 43 列 → 新 118 列）
PASS 6b 追加表头齐全
PASS 7 每个 COMPLETE 行正好 3 个合格 seed
PASS 7b COMPLETE_3_OF_3 行数 = 8
PASS 8 seed 的 terminal/admitted/certified/violations 与权威报告一致
PASS 9/10 不存在三个 seed 被复制成同一注入签名
PASS 9b 每 seed 注入事件单元格含其自身 tick
PASS 11 chain_end 未充当 L5
PASS 12 截断流未写成 containment
PASS 13 无未完成 RunID 被标 COMPLETE
PASS 14 无 Excel 错误值（#REF!/#VALUE!/#NAME?/#N/A/#DIV/0!）
PASS 15 抽查 full=T03-F5-W4 / contained=T02-F2-W4 / mixed=T01-F0-W4 / cross-binary=T01-F1-W4
PASS 15b 跨二进制版本被分别记录
PASS 16 传播路径单元格非空且非截断
```

## 5. 未回填 RunID 及原因

- **IN_PROGRESS（9）**：仅 seed1 已跑（T01-F0-W1 / T01-F1-W1 / T01-F2-W1 / T02-F0-W1 / T02-F2-W1 / T03-F5-W9 / T10-F0-W1 / T10-F1-W1 / T10-F2-W1），seed2/seed3 待跑。
- **POLICY_EXCLUDED_F6（64）**：按政策统一排除，不运行。
- **BLOCKED（53）**：coverage_matrix / 执行清单判定为 BLOCKED_INFRA 或 BLOCKED_SPEC（FS/multicore 依赖、规格未实现）。
- **UNPROVEN（191）**：尚未运行。

## 6. 重要说明

- **T02-F2-W4 seed2** 的裁决来自版本化离线重判报告 `chain_report.regrade-20261027T103833.json`（原始事件流未修改；结论由 `analysis_tool_head` 离线重判，**不是**重新运行 gem5）。Excel 指向该重判报告。
- **路径来源**：每个 seed 的传播路径由当前 checker 从该 seed **自身**未修改的 `prop_evt.txt.gz` 重算，并取 `select_representative_fault` 选中的代表 fault（escape-first）；注入行按 **tick+VA** 与该 fault 的 `inj` 事件精确配对。
- **未合并三个 seed**：每 seed 独立成列，路径/终局/二进制逐 seed 记录。