# 需用户裁决 / 延期清单（84 BLOCKED 中的不可自解项）

> 生成自 `tools/lsu_blocked_triage.py --contract`，与 `blocked_triage.md` **同一分类来源**（ready_contract.json（权威契约；契约总数 {'READY': 241, 'BLOCKED': 84}））。

## LICENSE（12 项）

- **阻塞机理**：SPEC CPU2017 需授权；仓库内无任何 SPEC 二进制/golden 可替代
- **解除条件**：取得授权，或书面同意以 SE 近似负载替代（改变规格负载）
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| C15-F0-W11 |
| C15-F4-W11 |
| C15-F6-W11 |
| L04-F0-W11 |
| L04-F2-W11 |
| L04-F6-W11 |
| S13-F0-W11 |
| S13-F1-W11 |
| S13-F2-W11 |
| T10-F0-W11 |
| T10-F1-W11 |
| T10-F2-W11 |

## FS-MULTICORE（35 项）

- **阻塞机理**：语义需多核 FS（litmus MP/SB/LB/IRIW、PARSEC 共享队列）
- **解除条件**：多核 FS 平台 + 载具落地
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| C08-F0-W7 |
| C08-F2-W7 |
| C08-F5-W7 |
| C08-F6-W7 |
| O01-F0-W7 |
| O01-F2-W7 |
| O01-F6-W7 |
| O02-F0-W7 |
| O02-F2-W7 |
| O02-F5-W7 |
| O02-F6-W7 |
| O03-F0-W7 |
| O03-F2-W7 |
| O03-F6-W7 |
| O04-F0-W7 |
| O04-F2-W7 |
| O04-F6-W7 |
| O05-F0-W7 |
| O05-F4-W7 |
| O05-F6-W7 |
| O06-F0-W7 |
| O06-F4-W7 |
| O06-F6-W7 |
| O07-F0-W7 |
| O07-F2-W7 |
| O07-F6-W7 |
| O09-F0-W13 |
| O09-F0-W7 |
| O09-F1-W13 |
| O09-F1-W7 |
| O09-F2-W13 |
| O09-F2-W7 |
| P09-F0-W13 |
| P09-F4-W13 |
| P09-F6-W13 |

## FS-INFRA（24 项）

- **阻塞机理**：TLB 翻译负载需 FS；且 FS 载体在预算内不终止 → 无 L5
- **解除条件**：FS 载具可终止化 + campaign 入口 pilot
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| T01-F0-W4 |
| T01-F1-W4 |
| T01-F2-W4 |
| T02-F0-W4 |
| T02-F2-W4 |
| T03-F5-W4 |
| T04-F0-W4 |
| T04-F2-W4 |
| T04-F6-W4 |
| T05-F0-W4 |
| T05-F2-W4 |
| T05-F6-W4 |
| T06-F0-W4 |
| T06-F2-W4 |
| T06-F6-W4 |
| T07-F0-W4 |
| T07-F4-W4 |
| T07-F6-W4 |
| T08-F0-W4 |
| T08-F4-W4 |
| T08-F6-W4 |
| T10-F0-W4 |
| T10-F1-W4 |
| T10-F2-W4 |

## RULING（6 项）

- **阻塞机理**：A06 load 侧定宽完成契约；load SHRINK 结构性不可达（已源码实证与契约钉死）
- **解除条件**：实现 load 侧 size 注入 + byte-enable 钩子，或规格裁决仅保留 widen
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| A06-F0-W3 |
| A06-F0-W5 |
| A06-F2-W3 |
| A06-F2-W5 |
| A06-F6-W3 |
| A06-F6-W5 |

## UNRESOLVED（4 项）

- **阻塞机理**：S10-F2 为规格结构性拒绝（F2 首抽下界 ≫ 实测流长）；S01/S02-F0-W1 待 span census 收敛
- **解除条件**：规格级重划 cell（长载体）或接受拒绝；census 收敛后写入 span
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| S01-F0-W1 |
| S02-F0-W1 |
| S10-F2-W5 |
| S10-F2-W9 |

**合计 81 项**（其余 3 项为可自行实现，见 `blocked_triage.md`）。

