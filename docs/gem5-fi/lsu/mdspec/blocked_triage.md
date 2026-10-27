# 325 BLOCKED 逐项裁决（互斥分类）

- 分类来源：ready_contract.json（权威契约；契约总数 {'BLOCKED': 325}）
- BLOCKED 总数：325（守恒校验通过：Σ 分类 == 总数）
- 分类统计：RULING=6 / LICENSE=12 / FS-MULTICORE=35 / FS-INFRA=13 / WORKLOAD-GAP=3 / MODE-UNIMPL=0 / HOOK-UNIMPL=0 / UNRESOLVED=4 / PLATFORM-DEFECT=0 / CHAIN-UNPROVEN=49 / CHAIN-EVIDENCE-MISSING=203 / UNCLASSIFIED=0 / OK=0

## 互斥类别定义

| 类别 | 含义 | 解除条件 |
|---|---|---|
| RULING | 模型级裁决封锁（A06 load 侧 / byte-enable） | §2.c 路径 spike 验证 + 测试 |
| LICENSE | SPEC CPU2017 授权缺失（W11） | 取得授权 |
| FS-MULTICORE | 需多核 FS（litmus/PARSEC 语义） | 多核 FS 基础设施落地 |
| FS-INFRA | 需 FS 基础设施（TLB 翻译负载） | FS checkpoint 流水线 |
| WORKLOAD-GAP | 规格负载在 FS 下不可得（GAP/Graph500 等） | 取得并装入合法 FS 载体，或规格裁决 |
| MODE-UNIMPL | 规格表 10 标注『先实现』的子模型模式 | 实现该模式 + 测试 |
| HOOK-UNIMPL | 钩子/载体缺口（无模式标注） | 补钩子或补 SE 载体映射 |
| OK | 无上述阻塞（应为 0） | — |

## 需用户批准的延期清单

以下类别**在可预见范围内无法由本轨道单方面解除**，需批准延期：

- **LICENSE**（12 个）：C15-F0-W11, C15-F4-W11, C15-F6-W11, L04-F0-W11, L04-F2-W11, L04-F6-W11, S13-F0-W11, S13-F1-W11, S13-F2-W11, T10-F0-W11, T10-F1-W11, T10-F2-W11
- **FS-MULTICORE**（35 个）：C08-F0-W7, C08-F2-W7, C08-F5-W7, C08-F6-W7, O01-F0-W7, O01-F2-W7, O01-F6-W7, O02-F0-W7, O02-F2-W7, O02-F5-W7, O02-F6-W7, O03-F0-W7, O03-F2-W7, O03-F6-W7, O04-F0-W7, O04-F2-W7, O04-F6-W7, O05-F0-W7, O05-F4-W7, O05-F6-W7, O06-F0-W7, O06-F4-W7, O06-F6-W7, O07-F0-W7, O07-F2-W7, O07-F6-W7, O09-F0-W13, O09-F0-W7, O09-F1-W13, O09-F1-W7, O09-F2-W13, O09-F2-W7, P09-F0-W13, P09-F4-W13, P09-F6-W13
- **FS-INFRA**（13 个）：T01-F0-W4, T01-F1-W4, T01-F2-W4, T02-F0-W4, T02-F2-W4, T03-F5-W4, T04-F0-W4, T04-F2-W4, T04-F6-W4, T05-F6-W4, T06-F6-W4, T07-F6-W4, T08-F6-W4
- **WORKLOAD-GAP**（3 个）：T08-F0-W9, T08-F4-W9, T08-F6-W9
- **RULING**（6 个）：A06-F0-W3, A06-F0-W5, A06-F2-W3, A06-F2-W5, A06-F6-W3, A06-F6-W5
- **UNRESOLVED**（4 个）：S01-F0-W1, S02-F0-W1, S10-F2-W5, S10-F2-W9
- **CHAIN-UNPROVEN**（49 个）：A01-F0-W3, A04-F0-W3, A07-F0-W3, A07-F0-W5, A07-F4-W3, A07-F4-W5, A07-F6-W3, A07-F6-W5, C01-F0-W6, C09-F0-W10, C09-F0-W6, C11-F0-W6, C11-F6-W6, C12-F0-W6, C12-F6-W6, C14-F5-W10, C14-F5-W6, C15-F0-W10, C15-F0-W6, C15-F4-W10, C15-F4-W6, C15-F6-W10, C15-F6-W6, L04-F0-W12, L04-F0-W5, L04-F2-W12, L04-F2-W5, L04-F6-W12, L04-F6-W5, P01-F0-W8, P06-F0-W6, P06-F0-W8, P06-F2-W6, P06-F2-W8, P06-F6-W6, P06-F6-W8, S01-F0-W5, S02-F0-W5, S04-F0-W5, S05-F0-W5, S10-F0-W5, S10-F0-W9, S10-F5-W5, S10-F5-W9, T05-F0-W4, T06-F0-W4, T07-F0-W4, T08-F0-W4, T10-F0-W4
- **CHAIN-EVIDENCE-MISSING**（203 个）：A01-F0-W9, A01-F1-W3, A01-F1-W9, A01-F2-W3, A01-F2-W9, A02-F0-W3, A02-F0-W9, A02-F2-W3, A02-F2-W9, A03-F5-W10, A03-F5-W3, A04-F0-W0, A04-F2-W0, A04-F2-W3, A04-F6-W0, A04-F6-W3, A05-F0-W3, A05-F2-W3, A05-F6-W3, A08-F0-W3, A08-F0-W5, A08-F2-W3, A08-F2-W5, A08-F6-W3, A08-F6-W5, C01-F0-W1, C01-F1-W1, C01-F1-W6, C01-F2-W1, C01-F2-W6, C02-F0-W1, C02-F0-W6, C02-F2-W1, C02-F2-W6, C03-F5-W10, C03-F5-W6, C04-F0-W1, C04-F0-W6, C04-F1-W1, C04-F1-W6, C04-F2-W1, C04-F2-W6, C05-F0-W6, C05-F2-W6, C05-F6-W6, C06-F0-W6, C06-F2-W6, C06-F5-W6, C07-F0-W6, C07-F2-W6, C07-F5-W6, C07-F6-W6, C08-F0-W6, C08-F2-W6, C08-F5-W6, C08-F6-W6, C09-F2-W10, C09-F2-W6, C09-F6-W10, C09-F6-W6, C10-F0-W10, C10-F0-W6, C10-F3-W10, C10-F3-W6, C10-F5-W10, C10-F5-W6, C11-F0-W10, C11-F2-W10, C11-F2-W6, C11-F4-W10, C11-F4-W6, C11-F6-W10, C12-F0-W10, C12-F4-W10, C12-F4-W6, C12-F6-W10, L01-F0-W1, L01-F0-W12, L01-F0-W5, L01-F1-W1, L01-F1-W12, L01-F1-W5, L01-F2-W1, L01-F2-W12, L01-F2-W5, L02-F0-W12, L02-F0-W5, L02-F2-W12, L02-F2-W5, L02-F6-W12, L02-F6-W5, L03-F0-W12, L03-F0-W5, L03-F4-W12, L03-F4-W5, L03-F6-W12, L03-F6-W5, P01-F0-W2, P01-F1-W2, P01-F1-W8, P01-F2-W2, P01-F2-W8, P02-F0-W10, P02-F0-W8, P02-F3-W10, P02-F3-W8, P02-F5-W10, P02-F5-W8, P03-F0-W8, P03-F0-W9, P03-F2-W8, P03-F2-W9, P03-F6-W8, P03-F6-W9, P04-F0-W2, P04-F0-W8, P04-F4-W2, P04-F4-W8, P04-F5-W2, P04-F5-W8, P05-F0-W10, P05-F0-W8, P05-F4-W10, P05-F4-W8, P05-F6-W10, P05-F6-W8, P07-F0-W6, P07-F0-W8, P07-F2-W6, P07-F2-W8, P07-F6-W6, P07-F6-W8, P08-F5-W10, P08-F5-W8, P09-F0-W6, P09-F0-W8, P09-F4-W6, P09-F4-W8, P09-F6-W6, P09-F6-W8, S01-F1-W1, S01-F1-W5, S01-F2-W1, S01-F2-W5, S02-F2-W1, S02-F2-W5, S03-F5-W10, S03-F5-W5, S04-F0-W0, S04-F2-W0, S04-F2-W5, S04-F6-W0, S04-F6-W5, S05-F0-W3, S05-F2-W3, S05-F2-W5, S05-F6-W3, S05-F6-W5, S06-F0-W5, S06-F0-W6, S06-F2-W5, S06-F2-W6, S06-F6-W5, S06-F6-W6, S07-F0-W5, S07-F4-W5, S07-F6-W5, S08-F0-W5, S08-F2-W5, S08-F6-W5, S09-F0-W5, S09-F2-W5, S09-F6-W5, S11-F0-W5, S11-F0-W6, S11-F4-W5, S11-F4-W6, S11-F6-W5, S11-F6-W6, S13-F0-W1, S13-F0-W12, S13-F0-W5, S13-F1-W1, S13-F1-W12, S13-F1-W5, S13-F2-W1, S13-F2-W12, S13-F2-W5, T01-F0-W1, T01-F1-W1, T01-F2-W1, T02-F0-W1, T02-F2-W1, T03-F5-W9, T05-F2-W4, T06-F2-W4, T07-F4-W4, T08-F4-W4, T10-F0-W1, T10-F1-W1, T10-F1-W4, T10-F2-W1, T10-F2-W4

可自行解除（不需批准，但需实现工作）：

## 逐项明细

| RunID | 单元 | 模型 | 互斥类别 | 理由 |
|---|---|---|---|---|
| A01-F0-W3 | AGU | A01 | CHAIN-UNPROVEN | A01-F0-W3 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A01-F0-W3 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_regress_s |
| A01-F0-W9 | AGU | A01 | CHAIN-EVIDENCE-MISSING | 无 A01-F0-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A01-F1-W3 | AGU | A01 | CHAIN-EVIDENCE-MISSING | 无 A01-F1-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A01-F1-W9 | AGU | A01 | CHAIN-EVIDENCE-MISSING | 无 A01-F1-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A01-F2-W3 | AGU | A01 | CHAIN-EVIDENCE-MISSING | 无 A01-F2-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A01-F2-W9 | AGU | A01 | CHAIN-EVIDENCE-MISSING | 无 A01-F2-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A02-F0-W3 | AGU | A02 | CHAIN-EVIDENCE-MISSING | 无 A02-F0-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A02-F0-W9 | AGU | A02 | CHAIN-EVIDENCE-MISSING | 无 A02-F0-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A02-F2-W3 | AGU | A02 | CHAIN-EVIDENCE-MISSING | 无 A02-F2-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A02-F2-W9 | AGU | A02 | CHAIN-EVIDENCE-MISSING | 无 A02-F2-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A03-F5-W10 | AGU | A03 | CHAIN-EVIDENCE-MISSING | 无 A03-F5-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A03-F5-W3 | AGU | A03 | CHAIN-EVIDENCE-MISSING | 无 A03-F5-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A04-F0-W0 | AGU | A04 | CHAIN-EVIDENCE-MISSING | 无 A04-F0-W0 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A04-F0-W3 | AGU | A04 | CHAIN-UNPROVEN | A04-F0-W3 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A04-F0-W3 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_pilot/A |
| A04-F2-W0 | AGU | A04 | CHAIN-EVIDENCE-MISSING | 无 A04-F2-W0 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A04-F2-W3 | AGU | A04 | CHAIN-EVIDENCE-MISSING | 无 A04-F2-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A04-F6-W0 | AGU | A04 | CHAIN-EVIDENCE-MISSING | 无 A04-F6-W0 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A04-F6-W3 | AGU | A04 | CHAIN-EVIDENCE-MISSING | 无 A04-F6-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A05-F0-W3 | AGU | A05 | CHAIN-EVIDENCE-MISSING | 无 A05-F0-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A05-F2-W3 | AGU | A05 | CHAIN-EVIDENCE-MISSING | 无 A05-F2-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A05-F6-W3 | AGU | A05 | CHAIN-EVIDENCE-MISSING | 无 A05-F6-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A06-F0-W3 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F0-W5 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F2-W3 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F2-W5 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F6-W3 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A06-F6-W5 | AGU | A06 | RULING | campaign:BLOCKED(load WIDEN + store size/shrink + A06-b store mask are real-machine verified (campaign trial: activated=1); load SHRINK is a PROVEN-un |
| A07-F0-W3 | AGU | A07 | CHAIN-UNPROVEN | A07-F0-W3 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A07-F0-W3 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A |
| A07-F0-W5 | AGU | A07 | CHAIN-UNPROVEN | A07-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A07-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A |
| A07-F4-W3 | AGU | A07 | CHAIN-UNPROVEN | A07-F4-W3 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A07-F4-W3 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A |
| A07-F4-W5 | AGU | A07 | CHAIN-UNPROVEN | A07-F4-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A07-F4-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A |
| A07-F6-W3 | AGU | A07 | CHAIN-UNPROVEN | A07-F6-W3 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A07-F6-W3 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A |
| A07-F6-W5 | AGU | A07 | CHAIN-UNPROVEN | A07-F6-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: A07-F6-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A |
| A08-F0-W3 | AGU | A08 | CHAIN-EVIDENCE-MISSING | 无 A08-F0-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A08-F0-W5 | AGU | A08 | CHAIN-EVIDENCE-MISSING | 无 A08-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A08-F2-W3 | AGU | A08 | CHAIN-EVIDENCE-MISSING | 无 A08-F2-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A08-F2-W5 | AGU | A08 | CHAIN-EVIDENCE-MISSING | 无 A08-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A08-F6-W3 | AGU | A08 | CHAIN-EVIDENCE-MISSING | 无 A08-F6-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| A08-F6-W5 | AGU | A08 | CHAIN-EVIDENCE-MISSING | 无 A08-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C01-F0-W1 | L1d-Cache | C01 | CHAIN-EVIDENCE-MISSING | 无 C01-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C01-F0-W6 | L1d-Cache | C01 | CHAIN-UNPROVEN | C01-F0-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C01-F0-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_regress_s |
| C01-F1-W1 | L1d-Cache | C01 | CHAIN-EVIDENCE-MISSING | 无 C01-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C01-F1-W6 | L1d-Cache | C01 | CHAIN-EVIDENCE-MISSING | 无 C01-F1-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C01-F2-W1 | L1d-Cache | C01 | CHAIN-EVIDENCE-MISSING | 无 C01-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C01-F2-W6 | L1d-Cache | C01 | CHAIN-EVIDENCE-MISSING | 无 C01-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C02-F0-W1 | L1d-Cache | C02 | CHAIN-EVIDENCE-MISSING | 无 C02-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C02-F0-W6 | L1d-Cache | C02 | CHAIN-EVIDENCE-MISSING | 无 C02-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C02-F2-W1 | L1d-Cache | C02 | CHAIN-EVIDENCE-MISSING | 无 C02-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C02-F2-W6 | L1d-Cache | C02 | CHAIN-EVIDENCE-MISSING | 无 C02-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C03-F5-W10 | L1d-Cache | C03 | CHAIN-EVIDENCE-MISSING | 无 C03-F5-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C03-F5-W6 | L1d-Cache | C03 | CHAIN-EVIDENCE-MISSING | 无 C03-F5-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C04-F0-W1 | L1d-Cache | C04 | CHAIN-EVIDENCE-MISSING | 无 C04-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C04-F0-W6 | L1d-Cache | C04 | CHAIN-EVIDENCE-MISSING | 无 C04-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C04-F1-W1 | L1d-Cache | C04 | CHAIN-EVIDENCE-MISSING | 无 C04-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C04-F1-W6 | L1d-Cache | C04 | CHAIN-EVIDENCE-MISSING | 无 C04-F1-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C04-F2-W1 | L1d-Cache | C04 | CHAIN-EVIDENCE-MISSING | 无 C04-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C04-F2-W6 | L1d-Cache | C04 | CHAIN-EVIDENCE-MISSING | 无 C04-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C05-F0-W6 | L1d-Cache | C05 | CHAIN-EVIDENCE-MISSING | 无 C05-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C05-F2-W6 | L1d-Cache | C05 | CHAIN-EVIDENCE-MISSING | 无 C05-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C05-F6-W6 | L1d-Cache | C05 | CHAIN-EVIDENCE-MISSING | 无 C05-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C06-F0-W6 | L1d-Cache | C06 | CHAIN-EVIDENCE-MISSING | 无 C06-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C06-F2-W6 | L1d-Cache | C06 | CHAIN-EVIDENCE-MISSING | 无 C06-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C06-F5-W6 | L1d-Cache | C06 | CHAIN-EVIDENCE-MISSING | 无 C06-F5-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C07-F0-W6 | L1d-Cache | C07 | CHAIN-EVIDENCE-MISSING | 无 C07-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C07-F2-W6 | L1d-Cache | C07 | CHAIN-EVIDENCE-MISSING | 无 C07-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C07-F5-W6 | L1d-Cache | C07 | CHAIN-EVIDENCE-MISSING | 无 C07-F5-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C07-F6-W6 | L1d-Cache | C07 | CHAIN-EVIDENCE-MISSING | 无 C07-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C08-F0-W6 | L1d-Cache | C08 | CHAIN-EVIDENCE-MISSING | 无 C08-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C08-F0-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C08-F2-W6 | L1d-Cache | C08 | CHAIN-EVIDENCE-MISSING | 无 C08-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C08-F2-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C08-F5-W6 | L1d-Cache | C08 | CHAIN-EVIDENCE-MISSING | 无 C08-F5-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C08-F5-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C08-F6-W6 | L1d-Cache | C08 | CHAIN-EVIDENCE-MISSING | 无 C08-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C08-F6-W7 | L1d-Cache | C08 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| C09-F0-W10 | L1d-Cache | C09 | CHAIN-UNPROVEN | C09-F0-W10 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C09-F0-W10 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_campa |
| C09-F0-W6 | L1d-Cache | C09 | CHAIN-UNPROVEN | C09-F0-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C09-F0-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t3_c09w6/C0 |
| C09-F2-W10 | L1d-Cache | C09 | CHAIN-EVIDENCE-MISSING | 无 C09-F2-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C09-F2-W6 | L1d-Cache | C09 | CHAIN-EVIDENCE-MISSING | 无 C09-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C09-F6-W10 | L1d-Cache | C09 | CHAIN-EVIDENCE-MISSING | 无 C09-F6-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C09-F6-W6 | L1d-Cache | C09 | CHAIN-EVIDENCE-MISSING | 无 C09-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C10-F0-W10 | L1d-Cache | C10 | CHAIN-EVIDENCE-MISSING | 无 C10-F0-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C10-F0-W6 | L1d-Cache | C10 | CHAIN-EVIDENCE-MISSING | 无 C10-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C10-F3-W10 | L1d-Cache | C10 | CHAIN-EVIDENCE-MISSING | 无 C10-F3-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C10-F3-W6 | L1d-Cache | C10 | CHAIN-EVIDENCE-MISSING | 无 C10-F3-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C10-F5-W10 | L1d-Cache | C10 | CHAIN-EVIDENCE-MISSING | 无 C10-F5-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C10-F5-W6 | L1d-Cache | C10 | CHAIN-EVIDENCE-MISSING | 无 C10-F5-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F0-W10 | L1d-Cache | C11 | CHAIN-EVIDENCE-MISSING | 无 C11-F0-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F0-W6 | L1d-Cache | C11 | CHAIN-UNPROVEN | C11-F0-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C11-F0-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t5_c11w6/C1 |
| C11-F2-W10 | L1d-Cache | C11 | CHAIN-EVIDENCE-MISSING | 无 C11-F2-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F2-W6 | L1d-Cache | C11 | CHAIN-EVIDENCE-MISSING | 无 C11-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F4-W10 | L1d-Cache | C11 | CHAIN-EVIDENCE-MISSING | 无 C11-F4-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F4-W6 | L1d-Cache | C11 | CHAIN-EVIDENCE-MISSING | 无 C11-F4-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F6-W10 | L1d-Cache | C11 | CHAIN-EVIDENCE-MISSING | 无 C11-F6-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C11-F6-W6 | L1d-Cache | C11 | CHAIN-UNPROVEN | C11-F6-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C11-F6-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t5i1_f6_pos |
| C12-F0-W10 | L1d-Cache | C12 | CHAIN-EVIDENCE-MISSING | 无 C12-F0-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C12-F0-W6 | L1d-Cache | C12 | CHAIN-UNPROVEN | C12-F0-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C12-F0-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t58_regr/C1 |
| C12-F4-W10 | L1d-Cache | C12 | CHAIN-EVIDENCE-MISSING | 无 C12-F4-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C12-F4-W6 | L1d-Cache | C12 | CHAIN-EVIDENCE-MISSING | 无 C12-F4-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C12-F6-W10 | L1d-Cache | C12 | CHAIN-EVIDENCE-MISSING | 无 C12-F6-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| C12-F6-W6 | L1d-Cache | C12 | CHAIN-UNPROVEN | C12-F6-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C12-F6-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t52_c12f6w6 |
| C14-F5-W10 | L1d-Cache | C14 | CHAIN-UNPROVEN | C14-F5-W10 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C14-F5-W10 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot |
| C14-F5-W6 | L1d-Cache | C14 | CHAIN-UNPROVEN | C14-F5-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C14-F5-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C |
| C15-F0-W10 | L1d-Cache | C15 | CHAIN-UNPROVEN | C15-F0-W10 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C15-F0-W10 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot |
| C15-F0-W11 | L1d-Cache | C15 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| C15-F0-W6 | L1d-Cache | C15 | CHAIN-UNPROVEN | C15-F0-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C15-F0-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C |
| C15-F4-W10 | L1d-Cache | C15 | CHAIN-UNPROVEN | C15-F4-W10 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C15-F4-W10 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot |
| C15-F4-W11 | L1d-Cache | C15 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| C15-F4-W6 | L1d-Cache | C15 | CHAIN-UNPROVEN | C15-F4-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C15-F4-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C |
| C15-F6-W10 | L1d-Cache | C15 | CHAIN-UNPROVEN | C15-F6-W10 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C15-F6-W10 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot |
| C15-F6-W11 | L1d-Cache | C15 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| C15-F6-W6 | L1d-Cache | C15 | CHAIN-UNPROVEN | C15-F6-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: C15-F6-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C |
| L01-F0-W1 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F0-W12 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F0-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F0-W5 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F1-W1 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F1-W12 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F1-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F1-W5 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F1-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F2-W1 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F2-W12 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F2-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L01-F2-W5 | Load Queue | L01 | CHAIN-EVIDENCE-MISSING | 无 L01-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L02-F0-W12 | Load Queue | L02 | CHAIN-EVIDENCE-MISSING | 无 L02-F0-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L02-F0-W5 | Load Queue | L02 | CHAIN-EVIDENCE-MISSING | 无 L02-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L02-F2-W12 | Load Queue | L02 | CHAIN-EVIDENCE-MISSING | 无 L02-F2-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L02-F2-W5 | Load Queue | L02 | CHAIN-EVIDENCE-MISSING | 无 L02-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L02-F6-W12 | Load Queue | L02 | CHAIN-EVIDENCE-MISSING | 无 L02-F6-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L02-F6-W5 | Load Queue | L02 | CHAIN-EVIDENCE-MISSING | 无 L02-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L03-F0-W12 | Load Queue | L03 | CHAIN-EVIDENCE-MISSING | 无 L03-F0-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L03-F0-W5 | Load Queue | L03 | CHAIN-EVIDENCE-MISSING | 无 L03-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L03-F4-W12 | Load Queue | L03 | CHAIN-EVIDENCE-MISSING | 无 L03-F4-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L03-F4-W5 | Load Queue | L03 | CHAIN-EVIDENCE-MISSING | 无 L03-F4-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L03-F6-W12 | Load Queue | L03 | CHAIN-EVIDENCE-MISSING | 无 L03-F6-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L03-F6-W5 | Load Queue | L03 | CHAIN-EVIDENCE-MISSING | 无 L03-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| L04-F0-W11 | Load Queue | L04 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| L04-F0-W12 | Load Queue | L04 | CHAIN-UNPROVEN | L04-F0-W12 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: L04-F0-W12 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04re |
| L04-F0-W5 | Load Queue | L04 | CHAIN-UNPROVEN | L04-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: L04-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04f0w5 |
| L04-F2-W11 | Load Queue | L04 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| L04-F2-W12 | Load Queue | L04 | CHAIN-UNPROVEN | L04-F2-W12 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: L04-F2-W12 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04re |
| L04-F2-W5 | Load Queue | L04 | CHAIN-UNPROVEN | L04-F2-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: L04-F2-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest |
| L04-F6-W11 | Load Queue | L04 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| L04-F6-W12 | Load Queue | L04 | CHAIN-UNPROVEN | L04-F6-W12 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: L04-F6-W12 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04re |
| L04-F6-W5 | Load Queue | L04 | CHAIN-UNPROVEN | L04-F6-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: L04-F6-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest |
| O01-F0-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O01-F2-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O01-F6-W7 | 原子与同步 | O01 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F0-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F2-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F5-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O02-F6-W7 | 原子与同步 | O02 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O03-F0-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O03-F2-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O03-F6-W7 | 原子与同步 | O03 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: 载体已就绪——2 核 Ruby/CHI FS + 仓库本地 freestanding litmus（O01/O02/O03 的 F0/F5 格已 routable，见 tools/lsu_fsmc_verdi |
| O04-F0-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC)  |
| O04-F2-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC)  |
| O04-F6-W7 | 原子与同步 | O04 | FS-MULTICORE | campaign:deferred(RMW data-path hook LANDED (rmw_mux @ SwapReq commit) but COMPILE-UNVERIFIED — build + RMW-commit census + pilot pending, R4-9-FSMC)  |
| O05-F0-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) but un-piloted |
| O05-F4-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) but un-piloted |
| O05-F6-W7 | 原子与同步 | O05 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; RMW-completion hook rmw_order LANDED @ SwapReq commit and COMPILED (build OK) but un-piloted |
| O06-F0-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) |
| O06-F4-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) |
| O06-F6-W7 | 原子与同步 | O06 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; barrier-completion hook LANDED (MemDepUnit barrier-SN bookkeeping, CHAOSLSQFwd --lsqfwd_o06) |
| O07-F0-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLS |
| O07-F2-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLS |
| O07-F6-W7 | 原子与同步 | O07 | FS-MULTICORE | campaign:blocked(multicore-fs: W7 Atomic-Litmus workload; order-tag exchange hook LANDED (MemDepUnit barrier-SN set as the ordering-tag proxy, CHAOSLS |
| O09-F0-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F0-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F1-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F1-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F2-W13 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| O09-F2-W7 | 原子与同步 | O09 | FS-MULTICORE | campaign:deferred(RMW operand hook LANDED (rmw_latch @ SwapReq commit, result/old-value latch) but COMPILE-UNVERIFIED — build + RMW-commit census + pi |
| P01-F0-W2 | 数据预取器 | P01 | CHAIN-EVIDENCE-MISSING | 无 P01-F0-W2 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P01-F0-W8 | 数据预取器 | P01 | CHAIN-UNPROVEN | P01-F0-W8 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P01-F0-W8 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_campaig |
| P01-F1-W2 | 数据预取器 | P01 | CHAIN-EVIDENCE-MISSING | 无 P01-F1-W2 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P01-F1-W8 | 数据预取器 | P01 | CHAIN-EVIDENCE-MISSING | 无 P01-F1-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P01-F2-W2 | 数据预取器 | P01 | CHAIN-EVIDENCE-MISSING | 无 P01-F2-W2 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P01-F2-W8 | 数据预取器 | P01 | CHAIN-EVIDENCE-MISSING | 无 P01-F2-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P02-F0-W10 | 数据预取器 | P02 | CHAIN-EVIDENCE-MISSING | 无 P02-F0-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P02-F0-W8 | 数据预取器 | P02 | CHAIN-EVIDENCE-MISSING | 无 P02-F0-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P02-F3-W10 | 数据预取器 | P02 | CHAIN-EVIDENCE-MISSING | 无 P02-F3-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P02-F3-W8 | 数据预取器 | P02 | CHAIN-EVIDENCE-MISSING | 无 P02-F3-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P02-F5-W10 | 数据预取器 | P02 | CHAIN-EVIDENCE-MISSING | 无 P02-F5-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P02-F5-W8 | 数据预取器 | P02 | CHAIN-EVIDENCE-MISSING | 无 P02-F5-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P03-F0-W8 | 数据预取器 | P03 | CHAIN-EVIDENCE-MISSING | 无 P03-F0-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P03-F0-W9 | 数据预取器 | P03 | CHAIN-EVIDENCE-MISSING | 无 P03-F0-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P03-F2-W8 | 数据预取器 | P03 | CHAIN-EVIDENCE-MISSING | 无 P03-F2-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P03-F2-W9 | 数据预取器 | P03 | CHAIN-EVIDENCE-MISSING | 无 P03-F2-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P03-F6-W8 | 数据预取器 | P03 | CHAIN-EVIDENCE-MISSING | 无 P03-F6-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P03-F6-W9 | 数据预取器 | P03 | CHAIN-EVIDENCE-MISSING | 无 P03-F6-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P04-F0-W2 | 数据预取器 | P04 | CHAIN-EVIDENCE-MISSING | 无 P04-F0-W2 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P04-F0-W8 | 数据预取器 | P04 | CHAIN-EVIDENCE-MISSING | 无 P04-F0-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P04-F4-W2 | 数据预取器 | P04 | CHAIN-EVIDENCE-MISSING | 无 P04-F4-W2 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P04-F4-W8 | 数据预取器 | P04 | CHAIN-EVIDENCE-MISSING | 无 P04-F4-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P04-F5-W2 | 数据预取器 | P04 | CHAIN-EVIDENCE-MISSING | 无 P04-F5-W2 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P04-F5-W8 | 数据预取器 | P04 | CHAIN-EVIDENCE-MISSING | 无 P04-F5-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P05-F0-W10 | 数据预取器 | P05 | CHAIN-EVIDENCE-MISSING | 无 P05-F0-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P05-F0-W8 | 数据预取器 | P05 | CHAIN-EVIDENCE-MISSING | 无 P05-F0-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P05-F4-W10 | 数据预取器 | P05 | CHAIN-EVIDENCE-MISSING | 无 P05-F4-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P05-F4-W8 | 数据预取器 | P05 | CHAIN-EVIDENCE-MISSING | 无 P05-F4-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P05-F6-W10 | 数据预取器 | P05 | CHAIN-EVIDENCE-MISSING | 无 P05-F6-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P05-F6-W8 | 数据预取器 | P05 | CHAIN-EVIDENCE-MISSING | 无 P05-F6-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P06-F0-W6 | 数据预取器 | P06 | CHAIN-UNPROVEN | P06-F0-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P06-F0-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06 |
| P06-F0-W8 | 数据预取器 | P06 | CHAIN-UNPROVEN | P06-F0-W8 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P06-F0-W8 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06 |
| P06-F2-W6 | 数据预取器 | P06 | CHAIN-UNPROVEN | P06-F2-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P06-F2-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06 |
| P06-F2-W8 | 数据预取器 | P06 | CHAIN-UNPROVEN | P06-F2-W8 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P06-F2-W8 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06 |
| P06-F6-W6 | 数据预取器 | P06 | CHAIN-UNPROVEN | P06-F6-W6 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P06-F6-W6 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06 |
| P06-F6-W8 | 数据预取器 | P06 | CHAIN-UNPROVEN | P06-F6-W8 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: P06-F6-W8 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06 |
| P07-F0-W6 | 数据预取器 | P07 | CHAIN-EVIDENCE-MISSING | 无 P07-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P07-F0-W8 | 数据预取器 | P07 | CHAIN-EVIDENCE-MISSING | 无 P07-F0-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P07-F2-W6 | 数据预取器 | P07 | CHAIN-EVIDENCE-MISSING | 无 P07-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P07-F2-W8 | 数据预取器 | P07 | CHAIN-EVIDENCE-MISSING | 无 P07-F2-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P07-F6-W6 | 数据预取器 | P07 | CHAIN-EVIDENCE-MISSING | 无 P07-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P07-F6-W8 | 数据预取器 | P07 | CHAIN-EVIDENCE-MISSING | 无 P07-F6-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P08-F5-W10 | 数据预取器 | P08 | CHAIN-EVIDENCE-MISSING | 无 P08-F5-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P08-F5-W8 | 数据预取器 | P08 | CHAIN-EVIDENCE-MISSING | 无 P08-F5-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P09-F0-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tes |
| P09-F0-W6 | 数据预取器 | P09 | CHAIN-EVIDENCE-MISSING | 无 P09-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P09-F0-W8 | 数据预取器 | P09 | CHAIN-EVIDENCE-MISSING | 无 P09-F0-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P09-F4-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tes |
| P09-F4-W6 | 数据预取器 | P09 | CHAIN-EVIDENCE-MISSING | 无 P09-F4-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P09-F4-W8 | 数据预取器 | P09 | CHAIN-EVIDENCE-MISSING | 无 P09-F4-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P09-F6-W13 | 数据预取器 | P09 | FS-MULTICORE | workload:workload-level:blocked(multicore-fs: W13 负载身份——PARSEC(dedup/ferret/streamcluster) **开源（不是授权障碍）但本仓库不可得**：find 实证只有 gem5 上游测试脚手架 CHAOS/gem5/tes |
| P09-F6-W6 | 数据预取器 | P09 | CHAIN-EVIDENCE-MISSING | 无 P09-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| P09-F6-W8 | 数据预取器 | P09 | CHAIN-EVIDENCE-MISSING | 无 P09-F6-W8 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S01-F0-W1 | Store Queue | S01 | UNRESOLVED | BLOCKED(F0-span-unmeasured: model S01 on workload mibench/bin/w1_all — measure its eligible stream with a real run and set LSQFWD_F0_SPAN[('S01', 'mib |
| S01-F0-W5 | Store Queue | S01 | CHAIN-UNPROVEN | S01-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S01-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t58_regr/S0 |
| S01-F1-W1 | Store Queue | S01 | CHAIN-EVIDENCE-MISSING | 无 S01-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S01-F1-W5 | Store Queue | S01 | CHAIN-EVIDENCE-MISSING | 无 S01-F1-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S01-F2-W1 | Store Queue | S01 | CHAIN-EVIDENCE-MISSING | 无 S01-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S01-F2-W5 | Store Queue | S01 | CHAIN-EVIDENCE-MISSING | 无 S01-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S02-F0-W1 | Store Queue | S02 | UNRESOLVED | BLOCKED(F0-span-unmeasured: model S02 on workload mibench/bin/w1_all — measure its eligible stream with a real run and set LSQFWD_F0_SPAN[('S02', 'mib |
| S02-F0-W5 | Store Queue | S02 | CHAIN-UNPROVEN | S02-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S02-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t1_i2_fixed |
| S02-F2-W1 | Store Queue | S02 | CHAIN-EVIDENCE-MISSING | 无 S02-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S02-F2-W5 | Store Queue | S02 | CHAIN-EVIDENCE-MISSING | 无 S02-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S03-F5-W10 | Store Queue | S03 | CHAIN-EVIDENCE-MISSING | 无 S03-F5-W10 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S03-F5-W5 | Store Queue | S03 | CHAIN-EVIDENCE-MISSING | 无 S03-F5-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S04-F0-W0 | Store Queue | S04 | CHAIN-EVIDENCE-MISSING | 无 S04-F0-W0 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S04-F0-W5 | Store Queue | S04 | CHAIN-UNPROVEN | S04-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S04-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t58_regr/S0 |
| S04-F2-W0 | Store Queue | S04 | CHAIN-EVIDENCE-MISSING | 无 S04-F2-W0 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S04-F2-W5 | Store Queue | S04 | CHAIN-EVIDENCE-MISSING | 无 S04-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S04-F6-W0 | Store Queue | S04 | CHAIN-EVIDENCE-MISSING | 无 S04-F6-W0 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S04-F6-W5 | Store Queue | S04 | CHAIN-EVIDENCE-MISSING | 无 S04-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S05-F0-W3 | Store Queue | S05 | CHAIN-EVIDENCE-MISSING | 无 S05-F0-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S05-F0-W5 | Store Queue | S05 | CHAIN-UNPROVEN | S05-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S05-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_campaig |
| S05-F2-W3 | Store Queue | S05 | CHAIN-EVIDENCE-MISSING | 无 S05-F2-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S05-F2-W5 | Store Queue | S05 | CHAIN-EVIDENCE-MISSING | 无 S05-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S05-F6-W3 | Store Queue | S05 | CHAIN-EVIDENCE-MISSING | 无 S05-F6-W3 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S05-F6-W5 | Store Queue | S05 | CHAIN-EVIDENCE-MISSING | 无 S05-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S06-F0-W5 | Store Queue | S06 | CHAIN-EVIDENCE-MISSING | 无 S06-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S06-F0-W6 | Store Queue | S06 | CHAIN-EVIDENCE-MISSING | 无 S06-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S06-F2-W5 | Store Queue | S06 | CHAIN-EVIDENCE-MISSING | 无 S06-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S06-F2-W6 | Store Queue | S06 | CHAIN-EVIDENCE-MISSING | 无 S06-F2-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S06-F6-W5 | Store Queue | S06 | CHAIN-EVIDENCE-MISSING | 无 S06-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S06-F6-W6 | Store Queue | S06 | CHAIN-EVIDENCE-MISSING | 无 S06-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S07-F0-W5 | Store Queue | S07 | CHAIN-EVIDENCE-MISSING | 无 S07-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S07-F4-W5 | Store Queue | S07 | CHAIN-EVIDENCE-MISSING | 无 S07-F4-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S07-F6-W5 | Store Queue | S07 | CHAIN-EVIDENCE-MISSING | 无 S07-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S08-F0-W5 | Store Queue | S08 | CHAIN-EVIDENCE-MISSING | 无 S08-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S08-F2-W5 | Store Queue | S08 | CHAIN-EVIDENCE-MISSING | 无 S08-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S08-F6-W5 | Store Queue | S08 | CHAIN-EVIDENCE-MISSING | 无 S08-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S09-F0-W5 | Store Queue | S09 | CHAIN-EVIDENCE-MISSING | 无 S09-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S09-F2-W5 | Store Queue | S09 | CHAIN-EVIDENCE-MISSING | 无 S09-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S09-F6-W5 | Store Queue | S09 | CHAIN-EVIDENCE-MISSING | 无 S09-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S10-F0-W5 | Store Queue | S10 | CHAIN-UNPROVEN | S10-F0-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S10-F0-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_s10/ |
| S10-F0-W9 | Store Queue | S10 | CHAIN-UNPROVEN | S10-F0-W9 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S10-F0-W9 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_s10/ |
| S10-F2-W5 | Store Queue | S10 | UNRESOLVED | BLOCKED(interval-tier-unreachable: model S10 tier F2 on workload sq_forward — the tier's SPEC-FIXED first-fire draw is U[F2/2, 3*F2/2) = at least 5000 |
| S10-F2-W9 | Store Queue | S10 | UNRESOLVED | BLOCKED(interval-tier-unreachable: model S10 tier F2 on workload gap_bfs — the tier's SPEC-FIXED first-fire draw is U[F2/2, 3*F2/2) = at least 50000 e |
| S10-F5-W5 | Store Queue | S10 | CHAIN-UNPROVEN | S10-F5-W5 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S10-F5-W5 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_s10/ |
| S10-F5-W9 | Store Queue | S10 | CHAIN-UNPROVEN | S10-F5-W9 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: S10-F5-W9 证据文件缺 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_s10_pilot |
| S11-F0-W5 | Store Queue | S11 | CHAIN-EVIDENCE-MISSING | 无 S11-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S11-F0-W6 | Store Queue | S11 | CHAIN-EVIDENCE-MISSING | 无 S11-F0-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S11-F4-W5 | Store Queue | S11 | CHAIN-EVIDENCE-MISSING | 无 S11-F4-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S11-F4-W6 | Store Queue | S11 | CHAIN-EVIDENCE-MISSING | 无 S11-F4-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S11-F6-W5 | Store Queue | S11 | CHAIN-EVIDENCE-MISSING | 无 S11-F6-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S11-F6-W6 | Store Queue | S11 | CHAIN-EVIDENCE-MISSING | 无 S11-F6-W6 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F0-W1 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F0-W11 | Store Queue | S13 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| S13-F0-W12 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F0-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F0-W5 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F0-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F1-W1 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F1-W11 | Store Queue | S13 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| S13-F1-W12 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F1-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F1-W5 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F1-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F2-W1 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F2-W11 | Store Queue | S13 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| S13-F2-W12 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F2-W12 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| S13-F2-W5 | Store Queue | S13 | CHAIN-EVIDENCE-MISSING | 无 S13-F2-W5 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T01-F0-W1 | L1d-TLB | T01 | CHAIN-EVIDENCE-MISSING | 无 T01-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T01-F0-W4 | L1d-TLB | T01 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T01-F1-W1 | L1d-TLB | T01 | CHAIN-EVIDENCE-MISSING | 无 T01-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T01-F1-W4 | L1d-TLB | T01 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T01-F2-W1 | L1d-TLB | T01 | CHAIN-EVIDENCE-MISSING | 无 T01-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T01-F2-W4 | L1d-TLB | T01 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T02-F0-W1 | L1d-TLB | T02 | CHAIN-EVIDENCE-MISSING | 无 T02-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T02-F0-W4 | L1d-TLB | T02 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T02-F2-W1 | L1d-TLB | T02 | CHAIN-EVIDENCE-MISSING | 无 T02-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T02-F2-W4 | L1d-TLB | T02 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T03-F5-W4 | L1d-TLB | T03 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T03-F5-W9 | L1d-TLB | T03 | CHAIN-EVIDENCE-MISSING | 无 T03-F5-W9 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T04-F0-W4 | L1d-TLB | T04 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T04-F2-W4 | L1d-TLB | T04 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T04-F6-W4 | L1d-TLB | T04 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T05-F0-W4 | L1d-TLB | T05 | CHAIN-UNPROVEN | T05-F0-W4 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: T05-F0-W4 证据文件缺 runs/lsu/r6_tlb_pilot2/T05-F0-W4/seed1/prop_evt.txt.gz（root=/ |
| T05-F2-W4 | L1d-TLB | T05 | CHAIN-EVIDENCE-MISSING | 无 T05-F2-W4 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T05-F6-W4 | L1d-TLB | T05 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T06-F0-W4 | L1d-TLB | T06 | CHAIN-UNPROVEN | T06-F0-W4 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: T06-F0-W4 证据文件缺 runs/lsu/r6_tlb_D_T06-F0-W4/T06-F0-W4/seed1/prop_evt.txt.gz（r |
| T06-F2-W4 | L1d-TLB | T06 | CHAIN-EVIDENCE-MISSING | 无 T06-F2-W4 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T06-F6-W4 | L1d-TLB | T06 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T07-F0-W4 | L1d-TLB | T07 | CHAIN-UNPROVEN | T07-F0-W4 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: T07-F0-W4 证据文件缺 runs/lsu/r6_tlb_pilot2/T07-F0-W4/seed1/prop_evt.txt.gz（root=/ |
| T07-F4-W4 | L1d-TLB | T07 | CHAIN-EVIDENCE-MISSING | 无 T07-F4-W4 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T07-F6-W4 | L1d-TLB | T07 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T08-F0-W4 | L1d-TLB | T08 | CHAIN-UNPROVEN | T08-F0-W4 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: T08-F0-W4 证据文件缺 runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1/prop_evt.txt.gz（r |
| T08-F0-W9 | L1d-TLB | T08 | WORKLOAD-GAP | workload:BLOCKED_WORKLOAD_GAP: T08 W9 requires a GAP/Graph500 FS workload; the fetchable GAP binary is SE-only (workloads/directed/gap_bfs), the FS im |
| T08-F4-W4 | L1d-TLB | T08 | CHAIN-EVIDENCE-MISSING | 无 T08-F4-W4 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T08-F4-W9 | L1d-TLB | T08 | WORKLOAD-GAP | workload:BLOCKED_WORKLOAD_GAP: T08 W9 requires a GAP/Graph500 FS workload; the fetchable GAP binary is SE-only (workloads/directed/gap_bfs), the FS im |
| T08-F6-W4 | L1d-TLB | T08 | FS-INFRA | workload:fs-infra: refuted(stale workload-level claim 'TLB workload needs FS' — the FS carrier fs:tlb_probe (golden b6d81b360a5672d80c27430f39153e2c)  |
| T08-F6-W9 | L1d-TLB | T08 | WORKLOAD-GAP | workload:BLOCKED_WORKLOAD_GAP: T08 W9 requires a GAP/Graph500 FS workload; the fetchable GAP binary is SE-only (workloads/directed/gap_bfs), the FS im |
| T10-F0-W1 | L1d-TLB | T10 | CHAIN-EVIDENCE-MISSING | 无 T10-F0-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T10-F0-W11 | L1d-TLB | T10 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| T10-F0-W4 | L1d-TLB | T10 | CHAIN-UNPROVEN | T10-F0-W4 链未准入（违规规则 ['chain_evidence_missing']）: chain_evidence_missing: T10-F0-W4 证据文件缺 runs/lsu/r6_tlb_F_T10-F0-W4/T10-F0-W4/seed1/prop_evt.txt.gz（r |
| T10-F1-W1 | L1d-TLB | T10 | CHAIN-EVIDENCE-MISSING | 无 T10-F1-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T10-F1-W11 | L1d-TLB | T10 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| T10-F1-W4 | L1d-TLB | T10 | CHAIN-EVIDENCE-MISSING | 无 T10-F1-W4 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T10-F2-W1 | L1d-TLB | T10 | CHAIN-EVIDENCE-MISSING | 无 T10-F2-W1 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
| T10-F2-W11 | L1d-TLB | T10 | LICENSE | BLOCKED_SPEC: SPEC CPU2017 needs a license |
| T10-F2-W4 | L1d-TLB | T10 | CHAIN-EVIDENCE-MISSING | 无 T10-F2-W4 的 pilot 证据（pilot_evidence.json 中无该 RunID 或其 seed 样本）——链不可证，故不准入 |
