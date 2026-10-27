# 需用户裁决 / 延期清单（325 BLOCKED 中的不可自解项）

> 生成自 `tools/lsu_blocked_triage.py --contract`，与 `blocked_triage.md` **同一分类来源**（ready_contract.json（权威契约；契约总数 {'BLOCKED': 325}））。

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

## FS-INFRA（13 项）

- **阻塞机理**：**并非缺 FS 基础设施**（该旧措辞已被本轮真机证据反驳）：载体/checkpoint 齐备，本集成二进制下 T01-F0-W4 产出真实注入（arm_tlb_lookup_hit，pfn 0x81d75→0x100000000081d75），T04-F0-W4 activated=1 / outcome=Crash / 链 L0→L5 full（1572 事件）。真正的阻塞是**逐格 campaign 入口 pilot 未完成**——T05/T06/T07/T08为本轮新实现模式、T10 PPN 分层未参数化，均无真机 pilot；且 runid_map 的 workload 级静态键 TLB-AliasPerm 仍整批拒绝该负载。
- **解除条件**：逐格（含 T05–T08 新模式）真机 30 activated pilot 后，解除 TLB-AliasPerm 键并重生成 runid_map → 契约
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
| T05-F6-W4 |
| T06-F6-W4 |
| T07-F6-W4 |
| T08-F6-W4 |

## WORKLOAD-GAP（3 项）

- **阻塞机理**：**规格负载在 FS 下不可得**：T08-W9 要求 GAP/Graph500；当前只有 SE 版 gap_bfs，FS 镜像内没有 GAP/Graph500，armtlb 载体固定为 tlb_probe.rcS——在 W9 上跑 tlb_probe 会静默改变实验身份。
- **解除条件**：取得合法 AArch64 GAP/Graph500 并装入 FS 镜像（或不改变语义的 FS 载体），验证 guest 真执行、oracle 哈希与 walk hook 可观测；否则保持 BLOCKED_WORKLOAD_GAP。
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| T08-F0-W9 |
| T08-F4-W9 |
| T08-F6-W9 |

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

## CHAIN-UNPROVEN（49 项）

- **阻塞机理**：**非范围性延期——链准入门禁（R6-GATE）**：该 cell 的 pilot PROP-EVT 未过 `lsu_chain_check.check_admission`（无 family-specific 完整 L0→L5 链，也无显式 containment 且后续层 N/A(contained)）；此前仅凭 coverage PASS 即判 READY 是假象。
- **解除条件**：为该 cell 产出真实 activated pilot，其链须满足：完整 L0→L5 链（同 parent-event DAG、无 Unknown、无跨分支/跨请求/逆时拼接、逐层必录指标齐），或显式 containment 路径。解除后重生成契约。
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| A01-F0-W3 |
| A04-F0-W3 |
| A07-F0-W3 |
| A07-F0-W5 |
| A07-F4-W3 |
| A07-F4-W5 |
| A07-F6-W3 |
| A07-F6-W5 |
| C01-F0-W6 |
| C09-F0-W10 |
| C09-F0-W6 |
| C11-F0-W6 |
| C11-F6-W6 |
| C12-F0-W6 |
| C12-F6-W6 |
| C14-F5-W10 |
| C14-F5-W6 |
| C15-F0-W10 |
| C15-F0-W6 |
| C15-F4-W10 |
| C15-F4-W6 |
| C15-F6-W10 |
| C15-F6-W6 |
| L04-F0-W12 |
| L04-F0-W5 |
| L04-F2-W12 |
| L04-F2-W5 |
| L04-F6-W12 |
| L04-F6-W5 |
| P01-F0-W8 |
| P06-F0-W6 |
| P06-F0-W8 |
| P06-F2-W6 |
| P06-F2-W8 |
| P06-F6-W6 |
| P06-F6-W8 |
| S01-F0-W5 |
| S02-F0-W5 |
| S04-F0-W5 |
| S05-F0-W5 |
| S10-F0-W5 |
| S10-F0-W9 |
| S10-F5-W5 |
| S10-F5-W9 |
| T05-F0-W4 |
| T06-F0-W4 |
| T07-F0-W4 |
| T08-F0-W4 |
| T10-F0-W4 |

## CHAIN-EVIDENCE-MISSING（203 项）

- **阻塞机理**：**非范围性延期——链准入门禁（R6-GATE）**：契约无该 cell 的 pilot PROP-EVT 证据（或证据根不可达）——链不可证，故不得判 READY（绝不因缺证据默认通过）。
- **解除条件**：为该 cell 运行 pilot 并把 prop_evt 纳入 pilot_evidence.json （或设 LSU_CHAIN_EVIDENCE_ROOT 指向证据根），再重生成契约。
- **建议处置**：批准延期，或按上述条件解除

| RunID |
|---|
| A01-F0-W9 |
| A01-F1-W3 |
| A01-F1-W9 |
| A01-F2-W3 |
| A01-F2-W9 |
| A02-F0-W3 |
| A02-F0-W9 |
| A02-F2-W3 |
| A02-F2-W9 |
| A03-F5-W10 |
| A03-F5-W3 |
| A04-F0-W0 |
| A04-F2-W0 |
| A04-F2-W3 |
| A04-F6-W0 |
| A04-F6-W3 |
| A05-F0-W3 |
| A05-F2-W3 |
| A05-F6-W3 |
| A08-F0-W3 |
| A08-F0-W5 |
| A08-F2-W3 |
| A08-F2-W5 |
| A08-F6-W3 |
| A08-F6-W5 |
| C01-F0-W1 |
| C01-F1-W1 |
| C01-F1-W6 |
| C01-F2-W1 |
| C01-F2-W6 |
| C02-F0-W1 |
| C02-F0-W6 |
| C02-F2-W1 |
| C02-F2-W6 |
| C03-F5-W10 |
| C03-F5-W6 |
| C04-F0-W1 |
| C04-F0-W6 |
| C04-F1-W1 |
| C04-F1-W6 |
| C04-F2-W1 |
| C04-F2-W6 |
| C05-F0-W6 |
| C05-F2-W6 |
| C05-F6-W6 |
| C06-F0-W6 |
| C06-F2-W6 |
| C06-F5-W6 |
| C07-F0-W6 |
| C07-F2-W6 |
| C07-F5-W6 |
| C07-F6-W6 |
| C08-F0-W6 |
| C08-F2-W6 |
| C08-F5-W6 |
| C08-F6-W6 |
| C09-F2-W10 |
| C09-F2-W6 |
| C09-F6-W10 |
| C09-F6-W6 |
| C10-F0-W10 |
| C10-F0-W6 |
| C10-F3-W10 |
| C10-F3-W6 |
| C10-F5-W10 |
| C10-F5-W6 |
| C11-F0-W10 |
| C11-F2-W10 |
| C11-F2-W6 |
| C11-F4-W10 |
| C11-F4-W6 |
| C11-F6-W10 |
| C12-F0-W10 |
| C12-F4-W10 |
| C12-F4-W6 |
| C12-F6-W10 |
| L01-F0-W1 |
| L01-F0-W12 |
| L01-F0-W5 |
| L01-F1-W1 |
| L01-F1-W12 |
| L01-F1-W5 |
| L01-F2-W1 |
| L01-F2-W12 |
| L01-F2-W5 |
| L02-F0-W12 |
| L02-F0-W5 |
| L02-F2-W12 |
| L02-F2-W5 |
| L02-F6-W12 |
| L02-F6-W5 |
| L03-F0-W12 |
| L03-F0-W5 |
| L03-F4-W12 |
| L03-F4-W5 |
| L03-F6-W12 |
| L03-F6-W5 |
| P01-F0-W2 |
| P01-F1-W2 |
| P01-F1-W8 |
| P01-F2-W2 |
| P01-F2-W8 |
| P02-F0-W10 |
| P02-F0-W8 |
| P02-F3-W10 |
| P02-F3-W8 |
| P02-F5-W10 |
| P02-F5-W8 |
| P03-F0-W8 |
| P03-F0-W9 |
| P03-F2-W8 |
| P03-F2-W9 |
| P03-F6-W8 |
| P03-F6-W9 |
| P04-F0-W2 |
| P04-F0-W8 |
| P04-F4-W2 |
| P04-F4-W8 |
| P04-F5-W2 |
| P04-F5-W8 |
| P05-F0-W10 |
| P05-F0-W8 |
| P05-F4-W10 |
| P05-F4-W8 |
| P05-F6-W10 |
| P05-F6-W8 |
| P07-F0-W6 |
| P07-F0-W8 |
| P07-F2-W6 |
| P07-F2-W8 |
| P07-F6-W6 |
| P07-F6-W8 |
| P08-F5-W10 |
| P08-F5-W8 |
| P09-F0-W6 |
| P09-F0-W8 |
| P09-F4-W6 |
| P09-F4-W8 |
| P09-F6-W6 |
| P09-F6-W8 |
| S01-F1-W1 |
| S01-F1-W5 |
| S01-F2-W1 |
| S01-F2-W5 |
| S02-F2-W1 |
| S02-F2-W5 |
| S03-F5-W10 |
| S03-F5-W5 |
| S04-F0-W0 |
| S04-F2-W0 |
| S04-F2-W5 |
| S04-F6-W0 |
| S04-F6-W5 |
| S05-F0-W3 |
| S05-F2-W3 |
| S05-F2-W5 |
| S05-F6-W3 |
| S05-F6-W5 |
| S06-F0-W5 |
| S06-F0-W6 |
| S06-F2-W5 |
| S06-F2-W6 |
| S06-F6-W5 |
| S06-F6-W6 |
| S07-F0-W5 |
| S07-F4-W5 |
| S07-F6-W5 |
| S08-F0-W5 |
| S08-F2-W5 |
| S08-F6-W5 |
| S09-F0-W5 |
| S09-F2-W5 |
| S09-F6-W5 |
| S11-F0-W5 |
| S11-F0-W6 |
| S11-F4-W5 |
| S11-F4-W6 |
| S11-F6-W5 |
| S11-F6-W6 |
| S13-F0-W1 |
| S13-F0-W12 |
| S13-F0-W5 |
| S13-F1-W1 |
| S13-F1-W12 |
| S13-F1-W5 |
| S13-F2-W1 |
| S13-F2-W12 |
| S13-F2-W5 |
| T01-F0-W1 |
| T01-F1-W1 |
| T01-F2-W1 |
| T02-F0-W1 |
| T02-F2-W1 |
| T03-F5-W9 |
| T05-F2-W4 |
| T06-F2-W4 |
| T07-F4-W4 |
| T08-F4-W4 |
| T10-F0-W1 |
| T10-F1-W1 |
| T10-F1-W4 |
| T10-F2-W1 |
| T10-F2-W4 |

**合计 325 项**（其余 0 项为可自行实现，见 `blocked_triage.md`）。

