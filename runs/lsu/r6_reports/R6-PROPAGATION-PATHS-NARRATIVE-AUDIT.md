# R6 叙事版传播文档审计（精确版）

- 生成时间 `2026-10-27T20:35:15`
- 文档目录 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS`
- 权威证据索引 `runs/lsu/R6-AUTHORITATIVE-EVIDENCE.json`

## 汇总

| 指标 | 值 |
|---|---|
| 文件总数 | **51** |
| 七章齐全 | **51** |
| 仍含旧章节 | **0** |
| 缺少主链叙述 | **0** |
| 缺少单元输入/内部变化/输出/传播意义表 | **0** |
| 缺少 SDC 诊断 | **0** |
| 当前 seed verdict=PASS | **27** |
| 当前 seed verdict=REVIEW_REQUIRED | **0** |
| 当前 seed verdict=NOT_MIBENCH_RESULT | **24** |
| 结构失败（真实，逐文件） | **0** |
| chain evidence PASS | **51** |
| chain evidence FAIL | **0** |
| workload identity mismatch | **24** |
| containment seed | **7** |

overall_experiment_status 分布：`NOT_MIBENCH_RESULT`=24、`PASS`=27

结构失败文件清单：**无**

workload identity mismatch 清单：**`T01-F0-W1-seed1.md`、`T01-F0-W1-seed2.md`、`T01-F0-W1-seed3.md`、`T01-F1-W1-seed1.md`、`T01-F1-W1-seed2.md`、`T01-F1-W1-seed3.md`、`T01-F2-W1-seed1.md`、`T01-F2-W1-seed2.md`、`T01-F2-W1-seed3.md`、`T02-F0-W1-seed1.md`、`T02-F0-W1-seed2.md`、`T02-F0-W1-seed3.md`、`T02-F2-W1-seed1.md`、`T02-F2-W1-seed2.md`、`T02-F2-W1-seed3.md`、`T10-F0-W1-seed1.md`、`T10-F0-W1-seed2.md`、`T10-F0-W1-seed3.md`、`T10-F1-W1-seed1.md`、`T10-F1-W1-seed2.md`、`T10-F1-W1-seed3.md`、`T10-F2-W1-seed1.md`、`T10-F2-W1-seed2.md`、`T10-F2-W1-seed3.md`**

chain evidence FAIL 清单：**无**

## 逐文件

`7章`=七章齐全；`祖先序`=第2章链逐对 parent 正确且 tick 单调；`单表`=含输入/内部变化/输出/传播意义；`4章`=事件存在于本 seed 流；`哈希`=第7章重算一致；`见证`=终局事件真实（full=L5 errant_commit，contained=L2/L4 contained）；`链证`=chain evidence；`身份`=experiment identity。

| 文件 | 7章 | 祖先序 | 子先于父 | 单表 | SDC | 4章 | 哈希 | 见证 | 链证 | 身份 | 总状态 | Ch6 verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `T01-F0-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F0-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F0-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F0-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F0-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F0-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F1-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F1-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F1-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F1-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F1-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F1-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F2-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F2-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F2-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T01-F2-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F2-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T01-F2-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T02-F0-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T02-F0-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T02-F0-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T02-F0-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T02-F0-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T02-F0-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T02-F2-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T02-F2-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T02-F2-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T02-F2-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T02-F2-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T02-F2-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T03-F5-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T03-F5-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T03-F5-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T03-F5-W9-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T03-F5-W9-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T03-F5-W9-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T04-F0-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T04-F0-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T04-F0-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T04-F2-W4-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T04-F2-W4-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T04-F2-W4-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MATCH | **PASS** | PASS |
| `T10-F0-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F0-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F0-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F1-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F1-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F1-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F2-W1-seed1.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F2-W1-seed2.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |
| `T10-F2-W1-seed3.md` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | MISMATCH | **NOT_MIBENCH_RESULT** | NOT_MIBENCH_RESULT |

## 结构失败逐文件原因

无。

## chain evidence 失败逐文件原因

无。

## REVIEW_REQUIRED / NOT_MIBENCH_RESULT 的准确原因

### `T01-F0-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F0-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F0-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F1-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F1-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F1-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F2-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F2-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T01-F2-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T02-F0-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T02-F0-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T02-F0-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T02-F2-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T02-F2-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T02-F2-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F0-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F0-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F0-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F1-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F1-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F1-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F2-W1-seed1.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F2-W1-seed2.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）

### `T10-F2-W1-seed3.md`

- Ch.6 verdict：`NOT_MIBENCH_RESULT`
- chain_evidence_status：`PASS`
- experiment_identity_status：`WORKLOAD_IDENTITY_MISMATCH`
- overall_experiment_status：`NOT_MIBENCH_RESULT`
- （文档未给出结构化理由）


## 方法论

- seed verdict 只从第 6 章的 `verdict` / `判定` / `结论` 显式字段读取，全文出现 `REVIEW_REQUIRED` 不再参与判定。
- 七章按语义匹配，`原始证据与哈希` 与 `原始证据与文件哈希` 等价。
- 第 2 章祖先链、第 4 章事件、第 7 章哈希均由本 seed 原始证据独立重算。
- containment seed 的 `L5=N/A` 不构成结构失败。
