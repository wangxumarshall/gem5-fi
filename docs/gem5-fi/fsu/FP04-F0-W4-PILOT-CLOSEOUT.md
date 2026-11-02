# FSU-FP04-F0-W4 试点收口报告（D0/D0.5）

> 生成时间：2026-11-02。三份 audit 已持久化到各自权威 attempt；本报告中的
> `certified` 由审计门禁计算，不是硬编码。

## 1. 结论

- RunID：`FSU-FP04-F0-W4`（FP04 / F0 / W4）。
- 三 seed 全部 `admitted=true`、`certified=true`、`violations=[]`，逐 seed 审计 `ok=true`。
- **seed_completion = 3/3**。
- **coverage_status = PILOT_SUBMODEL_ONLY**（不是 COMPLETE）。
- 当前总数：**1/173 RunID seed-complete，3/519 合格 seed**；其余 172 个 RunID 为 0/3。
- 原始证据（prop_evt/stats/run.out/run.err/注入日志）未修改；仅重建派生证据。

## 2. 身份

| 项 | 值 |
|---|---|
| 运行源码 HEAD | `8e86d1ba0421741f96bd5986da7a4cdb9dae48a7` |
| gem5 二进制 | `CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `f9a7cd9b4de6a47dbaceaa4dac0b58bbf8ba5bbbe8f1c8241a9e71be7af98c32` |
| 嵌入 Python | 3.11.9 |
| 构建 | `PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j4 build/ARM/gem5.opt` |
| workload | `workloads/directed/elemwise_fma_kernel`（REAL；ARRAYHASH/ULP） |
| workload SHA-256 | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 3. 三 seed 收口

| seed | authoritative attempt | eligible | skip | chain | L5 witness | oracle | admitted | certified | audit | audit.json SHA-256 |
|---|---|---:|---:|---|---|---|---|---|---|---|
| 1 | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2` | 57347 | 45070 | full (L0,L1,L2,L3,L4,L5) | 5:commit/errant_commit | SDC | True | True | PASS | `ff862f31c3c1e03ee9a8560e44a90a1357ffc0b0d44e424e726b1f6fd307049f` |
| 2 | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed2/attempt-1` | 57347 | 13908 | full (L0,L1,L2,L3,L4,L5) | 5:commit/errant_commit | SDC | True | True | PASS | `a2dc048c97f494f99f455cdcd79d3bf9ad67b17d056b7d357bbf3128af751e2d` |
| 3 | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed3/attempt-1` | 57347 | 19337 | full (L0,L1,L2,L3,L4,L5) | 5:commit/errant_commit | SDC | True | True | PASS | `f53d863cf1c4e768480b28392157aec8333fa07fbe51f1850b647148a84b5b5c` |

派生证据 SHA-256：

| seed | chain_report.json | seed Markdown |
|---|---|---|
| 1 | `be543d6990cdf710d0f6de17f3aed344a2abfd4718149b9ec5a09dd2377b0009` | `838b44b69a97770c2c6b3d10a577d4f8795d76e1449fae524d67c4bf32cf83ba` |
| 2 | `ff67f863c998f720a1c7077eb5c977c97e4ed8f81d2ba5214ea384352404af4b` | `ed2a26b991c232665e7138bc12ee24987909b3c9aa211be116a515df19a9927b` |
| 3 | `01d0e8e7cac30a45bcf7e4bc11f5c06c13ecba4a24a18537709abd2cba34c82a` | `b5d2314e4d861ecd41351303e7547e2fd0d27e478b4436b1b243bad1873ad11d` |

## 4. certified 生成逻辑（非硬编码）

1. `fsu_chain_check._check_one`：`certified = admitted = closed_terminal and not violations`；
   `closed_terminal` 只接受 `full`（真实 L5 见证）、`contained_Ln`（真实含住事件）、
   `crash`/`timeout`/`sdc`。`chain_end` 不占层，不能产生 closed terminal。
2. `fsu_chain_check.check_stream`：stream-level `certified = admitted and all(fault.certified)
   and not truncated and not identity_violations`；`violations` 汇总全部 fault、身份与截断。
3. `fsu_seed_audit.write_audit`：独立重算完整门禁（gzip EOF、event_count、身份、
   直接 parent、tick 单调、L0–L5、真实 L5 witness、stats、证据哈希、无跨 seed），
   `audit.json.certified = audit.ok`。伪造 parent / 缺事件 / 错误终局 / 跨 seed /
   哈希不符都会使 certified=false（测试已覆盖）。

## 5. attempt lineage（seed1）

- `attempt-1`：**superseded**。发射端 v1 的 `unit="FSU Pipe"` 含空格被 PROP-EVT
  截断，`fault_mask` 未在 C++ 扩展字段表中而丢失，`activated` 被 L3/L4 重复计数为 3。
- `attempt-2`：**AUTHORITATIVE**。修复后重跑，`unit=FSU_Pipe`、`fault_mask` 落盘、
  `activated=1`，审计 `certified=true`。
- `attempt-1` 的原始证据未删除、未覆盖；见
  `runs/fsu/FSU-FP04-F0-W4/seed1/lineage.json` / `lineage.md` 与
  `seed1/attempt-1/SUPERSEDED.md`。

## 6. seed_completion 与 coverage_status

- `seed_completion`：只表示真实三 seed 是否完成（0/3..3/3）。
- `coverage_status`：表示模型/子模型/workload 覆盖语义，独立于 seed 数。

工作簿表 7/表 9 对 `FSU-FP04-F0-W4` 的子模型原文为：

> `FP04-a sign；FP04-b exp_hi/lo；FP04-c mant_hi/mid/lo；FP04-d NEON lane result`

本试点只执行了 **FP04-c / mant_lo / W4 / F0** 一个组合，因此：

- `seed_completion = 3/3`；
- `coverage_status = PILOT_SUBMODEL_ONLY`；
- 不能宣称 FP04-a/b、FP04-c 的 mant_hi/mant_mid、FP04-d、FP32、NEON 全 128-bit
  或 F1/F2/F3 频率语义已覆盖；这些属于 D3/D1 的工作。

173 个 RunID 的 coverage_status 汇总：

| coverage_status | 数量 |
|---|---:|
| PILOT_SUBMODEL_ONLY | 1 |
| PARTIAL | 59 |
| BLOCKED_NOT_IMPLEMENTED | 87 |
| BLOCKED_NO_TRUE_ARTIFACT | 26 |

## 7. 门禁 1–10

| # | 门禁 | 结果 |
|---|---|---|
| 1 | 无注入 golden | PASS（`docs/gem5-fi/fsu/evidence/BASELINE.md`） |
| 2 | eligible/count-only 普查 | PASS（57347） |
| 3 | 单次故障注入 | PASS |
| 4 | attempted/eligible/activated 可区分 | PASS（1/57347/1） |
| 5 | 注入日志 ↔ 根事件 | PASS |
| 6 | 同一 manifest 可重放 | PASS（seed2 PROP-EVT 逐字节相同） |
| 7 | 原始事件流完整非截断 | PASS（gzip EOF） |
| 8 | checker/chain report | PASS（full/admitted/certified） |
| 9 | 单 seed Markdown | PASS（三份十节） |
| 10 | 审计器发现伪造/缺事件/错误终局/跨 seed | PASS（负向测试 + 本次审计） |

## 8. 证据位置

- audit.json/audit.md：
  - `runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2/`
  - `runs/fsu/FSU-FP04-F0-W4/seed2/attempt-1/`
  - `runs/fsu/FSU-FP04-F0-W4/seed3/attempt-1/`
- 权威 Markdown：
  - `runs/fsu/COMPLETE_PROPAGATION_PATHS/FSU-FP04-F0-W4/FSU-FP04-F0-W4-seed{{1,2,3}}.md`
- INDEX：`runs/fsu/COMPLETE_PROPAGATION_PATHS/{{README.md,INDEX.md,INDEX.json}}`

## 9. 已知边界

- 当前 C3 默认（ROB=128/IQ=64/4-wide），不是工作簿 B0（ROB=40/IQ=32/3-wide/8-8-8）。
- FP04 发射端是结果侧功能级模型，不是门级或商用硅复刻。
- 仅 1/173 RunID seed-complete；未启动其余 172 个 RunID。
