# R6 逐 RunID 权威状态表（两轴 + 政策轴：evidence_state × eligibility × policy_state）

- 生成时间：2026-10-25T19:27:27+0800
- 证据根：`/home/sdc/gem5-fi-ding`（runs 根 `/home/sdc/gem5-fi-ding/runs/lsu`）
- 契约 `chain_gate.evidence_root`：`/home/sdc/gem5-fi-ding` —— 一致：是
- 总 RunID：325
- 政策 overlay：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json` —— 已加载：是

## 轴 A — evidence_state 计数（磁盘事实，仅五值，永不为 BLOCKED）

- NOT_RUN: 305
- EVIDENCE_MISSING: 0
- TRUNCATED: 12
- UNPROVEN: 8
- PILOT_READY: 0

## 轴 B — eligibility 计数（是否被上游独立阻塞）

- RUNNABLE: 241
- BLOCKED: 84

## 轴 C — policy_state 计数（R6-FREQPOLICY 频率政策，只读正交）

- NORMAL: 261
- STRESS_ONLY: 39
- STRESS_REDUNDANT: 25

> policy_state 是第三条只读正交轴（唯一裁决源 lsu_freq_policy + R6-FREQUENCY-POLICY.json）：STRESS_ONLY/STRESS_REDUNDANT 表示政策不要求更多种子，绝不因此被计为 failure/BLOCKED/EVIDENCE_MISSING——evidence_state/eligibility 仍如实报告磁盘与上游事实；UNKNOWN=overlay 缺失或 RunID 不在权威 325 entries（不可治理），响亮降级，绝不静默等于 NORMAL。

## blocker_code 分类计数

- FS-INFRA: 24
- FS-MULTICORE: 35
- LICENSE: 12
- MODE-UNIMPL: 3
- RULING: 6
- UNRESOLVED: 4

> BLOCKED=0 只表示该统计维度中没有 blocker，不代表全部实验可运行或已通过；正式准入依据仍是 PILOT_READY（evidence_state=PILOT_READY 且 eligibility=RUNNABLE）。

- 正式准入（PILOT_READY ∧ RUNNABLE）：0 个 （无）
- 其中 evidence_state=PILOT_READY 的行数（纯磁盘事实）：0
- 遗留单轴 `state` 计数（**非权威**）：NOT_RUN=305 EVIDENCE_MISSING=0 TRUNCATED=12 UNPROVEN=8 PILOT_READY=0 BLOCKED=0

- 流：total=134 complete=110 truncated=24 activated=131 admitted=48
- 无任何流的 RunID（从未执行 ⇒ NOT_RUN）：305
- 上游阻塞（eligibility=BLOCKED）：84 个 A06-F0-W3, A06-F0-W5, A06-F2-W3, A06-F2-W5, A06-F6-W3, A06-F6-W5, C08-F0-W7, C08-F2-W7, C08-F5-W7, C08-F6-W7, C15-F0-W11, C15-F4-W11, C15-F6-W11, L04-F0-W11, L04-F2-W11, L04-F6-W11, O01-F0-W7, O01-F2-W7, O01-F6-W7, O02-F0-W7, O02-F2-W7, O02-F5-W7, O02-F6-W7, O03-F0-W7, O03-F2-W7, O03-F6-W7, O04-F0-W7, O04-F2-W7, O04-F6-W7, O05-F0-W7, O05-F4-W7, O05-F6-W7, O06-F0-W7, O06-F4-W7, O06-F6-W7, O07-F0-W7, O07-F2-W7, O07-F6-W7, O09-F0-W13, O09-F0-W7, O09-F1-W13, O09-F1-W7, O09-F2-W13, O09-F2-W7, P09-F0-W13, P09-F4-W13, P09-F6-W13, S01-F0-W1, S02-F0-W1, S10-F2-W5, S10-F2-W9, S13-F0-W11, S13-F1-W11, S13-F2-W11, T01-F0-W4, T01-F1-W4, T01-F2-W4, T02-F0-W4, T02-F2-W4, T03-F5-W4, T04-F0-W4, T04-F2-W4, T04-F6-W4, T05-F0-W4, T05-F2-W4, T05-F6-W4, T06-F0-W4, T06-F2-W4, T06-F6-W4, T07-F0-W4, T07-F4-W4, T07-F6-W4, T08-F0-W4, T08-F0-W9, T08-F4-W4, T08-F4-W9, T08-F6-W4, T08-F6-W9, T10-F0-W11, T10-F0-W4, T10-F1-W11, T10-F1-W4, T10-F2-W11, T10-F2-W4

## 权威表（两轴并存 + 政策只读轴）

| run_id | unit | model | evidence_state | eligibility | policy_state | blocker_code | state | contract_upstream_status | upstream_block | samples | activated_samples | admitted_samples | failure_reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A01-F0-W3 | AGU | A01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_regress_s10/A01-F0-W3/seed1/prop_evt.txt.gz） |
| A01-F0-W9 | AGU | A01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A01-F1-W3 | AGU | A01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A01-F1-W9 | AGU | A01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A01-F2-W3 | AGU | A01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A01-F2-W9 | AGU | A01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A02-F0-W3 | AGU | A02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A02-F0-W9 | AGU | A02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A02-F2-W3 | AGU | A02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A02-F2-W9 | AGU | A02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A03-F5-W10 | AGU | A03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A03-F5-W3 | AGU | A03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A04-F0-W0 | AGU | A04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A04-F0-W3 | AGU | A04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_pilot/A04-F0-W3/s1/prop_evt.txt.gz） |
| A04-F2-W0 | AGU | A04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A04-F2-W3 | AGU | A04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A04-F6-W0 | AGU | A04 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A04-F6-W3 | AGU | A04 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A05-F0-W3 | AGU | A05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A05-F2-W3 | AGU | A05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A05-F6-W3 | AGU | A05 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A06-F0-W3 | AGU | A06 | NOT_RUN | BLOCKED | NORMAL | RULING | NOT_RUN | BLOCKED | RULING | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_a06/A06-F0-W3/seed1/prop_evt.txt.gz） |
| A06-F0-W5 | AGU | A06 | NOT_RUN | BLOCKED | NORMAL | RULING | NOT_RUN | BLOCKED | RULING | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_a06/A06-F0-W5/seed1/prop_evt.txt.gz） |
| A06-F2-W3 | AGU | A06 | NOT_RUN | BLOCKED | NORMAL | RULING | NOT_RUN | BLOCKED | RULING | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A06-F2-W5 | AGU | A06 | NOT_RUN | BLOCKED | NORMAL | RULING | NOT_RUN | BLOCKED | RULING | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A06-F6-W3 | AGU | A06 | NOT_RUN | BLOCKED | STRESS_ONLY | RULING | NOT_RUN | BLOCKED | RULING | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A06-F6-W5 | AGU | A06 | NOT_RUN | BLOCKED | STRESS_REDUNDANT | RULING | NOT_RUN | BLOCKED | RULING | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A07-F0-W3 | AGU | A07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A07-F0-W3/seed1/prop_evt.txt.gz） |
| A07-F0-W5 | AGU | A07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A07-F0-W5/seed1/prop_evt.txt.gz） |
| A07-F4-W3 | AGU | A07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A07-F4-W3/seed1/prop_evt.txt.gz） |
| A07-F4-W5 | AGU | A07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A07-F4-W5/seed1/prop_evt.txt.gz） |
| A07-F6-W3 | AGU | A07 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A07-F6-W3/seed1/prop_evt.txt.gz） |
| A07-F6-W5 | AGU | A07 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/A07-F6-W5/seed1/prop_evt.txt.gz） |
| A08-F0-W3 | AGU | A08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A08-F0-W5 | AGU | A08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A08-F2-W3 | AGU | A08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A08-F2-W5 | AGU | A08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A08-F6-W3 | AGU | A08 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| A08-F6-W5 | AGU | A08 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C01-F0-W1 | L1d-Cache | C01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C01-F0-W6 | L1d-Cache | C01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_regress_s10/C01-F0-W6/seed1/prop_evt.txt.gz） |
| C01-F1-W1 | L1d-Cache | C01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C01-F1-W6 | L1d-Cache | C01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C01-F2-W1 | L1d-Cache | C01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C01-F2-W6 | L1d-Cache | C01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C02-F0-W1 | L1d-Cache | C02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C02-F0-W6 | L1d-Cache | C02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C02-F2-W1 | L1d-Cache | C02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C02-F2-W6 | L1d-Cache | C02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C03-F5-W10 | L1d-Cache | C03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C03-F5-W6 | L1d-Cache | C03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C04-F0-W1 | L1d-Cache | C04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C04-F0-W6 | L1d-Cache | C04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C04-F1-W1 | L1d-Cache | C04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C04-F1-W6 | L1d-Cache | C04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C04-F2-W1 | L1d-Cache | C04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C04-F2-W6 | L1d-Cache | C04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C05-F0-W6 | L1d-Cache | C05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C05-F2-W6 | L1d-Cache | C05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C05-F6-W6 | L1d-Cache | C05 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C06-F0-W6 | L1d-Cache | C06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C06-F2-W6 | L1d-Cache | C06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C06-F5-W6 | L1d-Cache | C06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C07-F0-W6 | L1d-Cache | C07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C07-F2-W6 | L1d-Cache | C07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C07-F5-W6 | L1d-Cache | C07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C07-F6-W6 | L1d-Cache | C07 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F0-W6 | L1d-Cache | C08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F0-W7 | L1d-Cache | C08 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F2-W6 | L1d-Cache | C08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F2-W7 | L1d-Cache | C08 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F5-W6 | L1d-Cache | C08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F5-W7 | L1d-Cache | C08 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F6-W6 | L1d-Cache | C08 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C08-F6-W7 | L1d-Cache | C08 | NOT_RUN | BLOCKED | STRESS_REDUNDANT | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C09-F0-W10 | L1d-Cache | C09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 2 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_campaign_smoke/C09-F0-W10/seed1/prop_evt.txt |
| C09-F0-W6 | L1d-Cache | C09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t3_c09w6/C09-F0-W6/seed1/prop_evt.txt.gz） |
| C09-F2-W10 | L1d-Cache | C09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C09-F2-W6 | L1d-Cache | C09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C09-F6-W10 | L1d-Cache | C09 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C09-F6-W6 | L1d-Cache | C09 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C10-F0-W10 | L1d-Cache | C10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C10-F0-W6 | L1d-Cache | C10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C10-F3-W10 | L1d-Cache | C10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C10-F3-W6 | L1d-Cache | C10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C10-F5-W10 | L1d-Cache | C10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C10-F5-W6 | L1d-Cache | C10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F0-W10 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F0-W6 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t5_c11w6/C11-F0-W6/seed1/prop_evt.txt.gz） |
| C11-F2-W10 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F2-W6 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F4-W10 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F4-W6 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F6-W10 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C11-F6-W6 | L1d-Cache | C11 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t5i1_f6_postfix/C11-F6-W6/seed1/prop_evt.txt.gz） |
| C12-F0-W10 | L1d-Cache | C12 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C12-F0-W6 | L1d-Cache | C12 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t58_regr/C12-F0-W6/seed1/prop_evt.txt.gz） |
| C12-F4-W10 | L1d-Cache | C12 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C12-F4-W6 | L1d-Cache | C12 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C12-F6-W10 | L1d-Cache | C12 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C12-F6-W6 | L1d-Cache | C12 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t52_c12f6w6/C12-F6-W6/seed1/prop_evt.txt.gz） |
| C14-F5-W10 | L1d-Cache | C14 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C14-F5-W10/seed1/prop_evt.txt.gz） |
| C14-F5-W6 | L1d-Cache | C14 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C14-F5-W6/seed1/prop_evt.txt.gz） |
| C15-F0-W10 | L1d-Cache | C15 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C15-F0-W10/seed1/prop_evt.txt.gz） |
| C15-F0-W11 | L1d-Cache | C15 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C15-F0-W6 | L1d-Cache | C15 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C15-F0-W6/seed1/prop_evt.txt.gz） |
| C15-F4-W10 | L1d-Cache | C15 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C15-F4-W10/seed1/prop_evt.txt.gz） |
| C15-F4-W11 | L1d-Cache | C15 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C15-F4-W6 | L1d-Cache | C15 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C15-F4-W6/seed1/prop_evt.txt.gz） |
| C15-F6-W10 | L1d-Cache | C15 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C15-F6-W10/seed1/prop_evt.txt.gz） |
| C15-F6-W11 | L1d-Cache | C15 | NOT_RUN | BLOCKED | STRESS_REDUNDANT | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| C15-F6-W6 | L1d-Cache | C15 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t56_pilot/C15-F6-W6/seed1/prop_evt.txt.gz） |
| L01-F0-W1 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F0-W12 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F0-W5 | Load Queue | L01 | TRUNCATED | RUNNABLE | NORMAL | NONE | TRUNCATED | READY | NONE | 7 | 7 | 0 | 3/7 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| L01-F1-W1 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F1-W12 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F1-W5 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F2-W1 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F2-W12 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L01-F2-W5 | Load Queue | L01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L02-F0-W12 | Load Queue | L02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L02-F0-W5 | Load Queue | L02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L02-F2-W12 | Load Queue | L02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L02-F2-W5 | Load Queue | L02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L02-F6-W12 | Load Queue | L02 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L02-F6-W5 | Load Queue | L02 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L03-F0-W12 | Load Queue | L03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L03-F0-W5 | Load Queue | L03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L03-F4-W12 | Load Queue | L03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L03-F4-W5 | Load Queue | L03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L03-F6-W12 | Load Queue | L03 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L03-F6-W5 | Load Queue | L03 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L04-F0-W11 | Load Queue | L04 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L04-F0-W12 | Load Queue | L04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest/L04-F0-W12/seed1/prop_evt.txt.gz） |
| L04-F0-W5 | Load Queue | L04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04f0w5/L04-F0-W5/seed1/prop_evt.txt.gz） |
| L04-F2-W11 | Load Queue | L04 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L04-F2-W12 | Load Queue | L04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest/L04-F2-W12/seed1/prop_evt.txt.gz） |
| L04-F2-W5 | Load Queue | L04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest/L04-F2-W5/seed1/prop_evt.txt.gz） |
| L04-F6-W11 | Load Queue | L04 | NOT_RUN | BLOCKED | STRESS_ONLY | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| L04-F6-W12 | Load Queue | L04 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest/L04-F6-W12/seed1/prop_evt.txt.gz） |
| L04-F6-W5 | Load Queue | L04 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t53_l04rest/L04-F6-W5/seed1/prop_evt.txt.gz） |
| O01-F0-W7 | 原子与同步 | O01 | UNPROVEN | BLOCKED | NORMAL | FS-MULTICORE | UNPROVEN | BLOCKED | FS-MULTICORE | 1 | 1 | 0 | 1 个激活样本未过 check_admission（含 oversized/Unknown）；且被上游独立阻塞 FS-MULTICORE——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY |
| O01-F2-W7 | 原子与同步 | O01 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O01-F6-W7 | 原子与同步 | O01 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O02-F0-W7 | 原子与同步 | O02 | UNPROVEN | BLOCKED | NORMAL | FS-MULTICORE | UNPROVEN | BLOCKED | FS-MULTICORE | 1 | 1 | 0 | 1 个激活样本未过 check_admission（含 oversized/Unknown）；且被上游独立阻塞 FS-MULTICORE——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY |
| O02-F2-W7 | 原子与同步 | O02 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O02-F5-W7 | 原子与同步 | O02 | UNPROVEN | BLOCKED | NORMAL | FS-MULTICORE | UNPROVEN | BLOCKED | FS-MULTICORE | 1 | 1 | 0 | 1 个激活样本未过 check_admission（含 oversized/Unknown）；且被上游独立阻塞 FS-MULTICORE——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY |
| O02-F6-W7 | 原子与同步 | O02 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O03-F0-W7 | 原子与同步 | O03 | TRUNCATED | BLOCKED | NORMAL | FS-MULTICORE | TRUNCATED | BLOCKED | FS-MULTICORE | 1 | 0 | 0 | 1/1 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| O03-F2-W7 | 原子与同步 | O03 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O03-F6-W7 | 原子与同步 | O03 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O04-F0-W7 | 原子与同步 | O04 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O04-F2-W7 | 原子与同步 | O04 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O04-F6-W7 | 原子与同步 | O04 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O05-F0-W7 | 原子与同步 | O05 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O05-F4-W7 | 原子与同步 | O05 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O05-F6-W7 | 原子与同步 | O05 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O06-F0-W7 | 原子与同步 | O06 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O06-F4-W7 | 原子与同步 | O06 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O06-F6-W7 | 原子与同步 | O06 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O07-F0-W7 | 原子与同步 | O07 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O07-F2-W7 | 原子与同步 | O07 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O07-F6-W7 | 原子与同步 | O07 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O09-F0-W13 | 原子与同步 | O09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O09-F0-W7 | 原子与同步 | O09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O09-F1-W13 | 原子与同步 | O09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O09-F1-W7 | 原子与同步 | O09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O09-F2-W13 | 原子与同步 | O09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| O09-F2-W7 | 原子与同步 | O09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P01-F0-W2 | 数据预取器 | P01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P01-F0-W8 | 数据预取器 | P01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 4 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_campaign_smoke/P01-F0-W8/seed1/prop_evt.txt. |
| P01-F1-W2 | 数据预取器 | P01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P01-F1-W8 | 数据预取器 | P01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P01-F2-W2 | 数据预取器 | P01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P01-F2-W8 | 数据预取器 | P01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P02-F0-W10 | 数据预取器 | P02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P02-F0-W8 | 数据预取器 | P02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P02-F3-W10 | 数据预取器 | P02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P02-F3-W8 | 数据预取器 | P02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P02-F5-W10 | 数据预取器 | P02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P02-F5-W8 | 数据预取器 | P02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P03-F0-W8 | 数据预取器 | P03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P03-F0-W9 | 数据预取器 | P03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P03-F2-W8 | 数据预取器 | P03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P03-F2-W9 | 数据预取器 | P03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P03-F6-W8 | 数据预取器 | P03 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P03-F6-W9 | 数据预取器 | P03 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P04-F0-W2 | 数据预取器 | P04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P04-F0-W8 | 数据预取器 | P04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P04-F4-W2 | 数据预取器 | P04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P04-F4-W8 | 数据预取器 | P04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P04-F5-W2 | 数据预取器 | P04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P04-F5-W8 | 数据预取器 | P04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P05-F0-W10 | 数据预取器 | P05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P05-F0-W8 | 数据预取器 | P05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P05-F4-W10 | 数据预取器 | P05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P05-F4-W8 | 数据预取器 | P05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P05-F6-W10 | 数据预取器 | P05 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P05-F6-W8 | 数据预取器 | P05 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P06-F0-W6 | 数据预取器 | P06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06-F0-W6/seed1/prop_evt.txt.gz） |
| P06-F0-W8 | 数据预取器 | P06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06-F0-W8/seed1/prop_evt.txt.gz） |
| P06-F2-W6 | 数据预取器 | P06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06-F2-W6/seed1/prop_evt.txt.gz） |
| P06-F2-W8 | 数据预取器 | P06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06-F2-W8/seed1/prop_evt.txt.gz） |
| P06-F6-W6 | 数据预取器 | P06 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06-F6-W6/seed1/prop_evt.txt.gz） |
| P06-F6-W8 | 数据预取器 | P06 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t54_p06/P06-F6-W8/seed1/prop_evt.txt.gz） |
| P07-F0-W6 | 数据预取器 | P07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P07-F0-W8 | 数据预取器 | P07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P07-F2-W6 | 数据预取器 | P07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P07-F2-W8 | 数据预取器 | P07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P07-F6-W6 | 数据预取器 | P07 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P07-F6-W8 | 数据预取器 | P07 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P08-F5-W10 | 数据预取器 | P08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P08-F5-W8 | 数据预取器 | P08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F0-W13 | 数据预取器 | P09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F0-W6 | 数据预取器 | P09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F0-W8 | 数据预取器 | P09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F4-W13 | 数据预取器 | P09 | NOT_RUN | BLOCKED | NORMAL | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F4-W6 | 数据预取器 | P09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F4-W8 | 数据预取器 | P09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F6-W13 | 数据预取器 | P09 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-MULTICORE | NOT_RUN | BLOCKED | FS-MULTICORE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F6-W6 | 数据预取器 | P09 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| P09-F6-W8 | 数据预取器 | P09 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S01-F0-W1 | Store Queue | S01 | NOT_RUN | BLOCKED | NORMAL | UNRESOLVED | NOT_RUN | BLOCKED | UNRESOLVED | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S01-F0-W5 | Store Queue | S01 | UNPROVEN | RUNNABLE | NORMAL | NONE | UNPROVEN | READY | NONE | 3 | 3 | 0 | 3 个激活样本未过 check_admission（含 oversized/Unknown） |
| S01-F1-W1 | Store Queue | S01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S01-F1-W5 | Store Queue | S01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S01-F2-W1 | Store Queue | S01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S01-F2-W5 | Store Queue | S01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S02-F0-W1 | Store Queue | S02 | NOT_RUN | BLOCKED | NORMAL | UNRESOLVED | NOT_RUN | BLOCKED | UNRESOLVED | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S02-F0-W5 | Store Queue | S02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t1_i2_fixed/S02-F0-W5/seed1/prop_evt.txt.gz） |
| S02-F2-W1 | Store Queue | S02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S02-F2-W5 | Store Queue | S02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S03-F5-W10 | Store Queue | S03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S03-F5-W5 | Store Queue | S03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S04-F0-W0 | Store Queue | S04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S04-F0-W5 | Store Queue | S04 | UNPROVEN | RUNNABLE | NORMAL | NONE | UNPROVEN | READY | NONE | 8 | 8 | 0 | 8 个激活样本未过 check_admission（含 oversized/Unknown） |
| S04-F2-W0 | Store Queue | S04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S04-F2-W5 | Store Queue | S04 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S04-F6-W0 | Store Queue | S04 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S04-F6-W5 | Store Queue | S04 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S05-F0-W3 | Store Queue | S05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S05-F0-W5 | Store Queue | S05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 2 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/mdspec_campaign_smoke/S05-F0-W5/seed1/prop_evt.txt. |
| S05-F2-W3 | Store Queue | S05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S05-F2-W5 | Store Queue | S05 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S05-F6-W3 | Store Queue | S05 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S05-F6-W5 | Store Queue | S05 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S06-F0-W5 | Store Queue | S06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S06-F0-W6 | Store Queue | S06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S06-F2-W5 | Store Queue | S06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S06-F2-W6 | Store Queue | S06 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S06-F6-W5 | Store Queue | S06 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S06-F6-W6 | Store Queue | S06 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S07-F0-W5 | Store Queue | S07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S07-F4-W5 | Store Queue | S07 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S07-F6-W5 | Store Queue | S07 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S08-F0-W5 | Store Queue | S08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S08-F2-W5 | Store Queue | S08 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S08-F6-W5 | Store Queue | S08 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S09-F0-W5 | Store Queue | S09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S09-F2-W5 | Store Queue | S09 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S09-F6-W5 | Store Queue | S09 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S10-F0-W5 | Store Queue | S10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_s10/S10-F0-W5/seed1/prop_evt.txt.gz） |
| S10-F0-W9 | Store Queue | S10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_s10/S10-F0-W9/seed1/prop_evt.txt.gz） |
| S10-F2-W5 | Store Queue | S10 | NOT_RUN | BLOCKED | NORMAL | UNRESOLVED | NOT_RUN | BLOCKED | UNRESOLVED | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_s10_pilot/S10-F2-W5/seed1/prop_evt.txt.gz） |
| S10-F2-W9 | Store Queue | S10 | NOT_RUN | BLOCKED | NORMAL | UNRESOLVED | NOT_RUN | BLOCKED | UNRESOLVED | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_s10_pilot/S10-F2-W9/seed1/prop_evt.txt.gz） |
| S10-F5-W5 | Store Queue | S10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/trial_r48_s10/S10-F5-W5/seed1/prop_evt.txt.gz） |
| S10-F5-W9 | Store Queue | S10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 3 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_s10_pilot/S10-F5-W9/seed1/prop_evt.txt.gz） |
| S11-F0-W5 | Store Queue | S11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S11-F0-W6 | Store Queue | S11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S11-F4-W5 | Store Queue | S11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S11-F4-W6 | Store Queue | S11 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S11-F6-W5 | Store Queue | S11 | NOT_RUN | RUNNABLE | STRESS_ONLY | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S11-F6-W6 | Store Queue | S11 | NOT_RUN | RUNNABLE | STRESS_REDUNDANT | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F0-W1 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F0-W11 | Store Queue | S13 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F0-W12 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F0-W5 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F1-W1 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F1-W11 | Store Queue | S13 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F1-W12 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F1-W5 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F2-W1 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F2-W11 | Store Queue | S13 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F2-W12 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| S13-F2-W5 | Store Queue | S13 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T01-F0-W1 | L1d-TLB | T01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T01-F0-W4 | L1d-TLB | T01 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 17 | 17 | 8 | 2/17 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T01-F1-W1 | L1d-TLB | T01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T01-F1-W4 | L1d-TLB | T01 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 1 | 1 | 0 | 1/1 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T01-F2-W1 | L1d-TLB | T01 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T01-F2-W4 | L1d-TLB | T01 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T02-F0-W1 | L1d-TLB | T02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T02-F0-W4 | L1d-TLB | T02 | UNPROVEN | BLOCKED | NORMAL | FS-INFRA | UNPROVEN | BLOCKED | FS-INFRA | 27 | 27 | 15 | 12 个激活样本未过 check_admission（含 oversized/Unknown）；且被上游独立阻塞 FS-INFRA——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY |
| T02-F2-W1 | L1d-TLB | T02 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T02-F2-W4 | L1d-TLB | T02 | UNPROVEN | BLOCKED | NORMAL | FS-INFRA | UNPROVEN | BLOCKED | FS-INFRA | 13 | 13 | 9 | 4 个激活样本未过 check_admission（含 oversized/Unknown）；且被上游独立阻塞 FS-INFRA——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY |
| T03-F5-W4 | L1d-TLB | T03 | UNPROVEN | BLOCKED | NORMAL | FS-INFRA | UNPROVEN | BLOCKED | FS-INFRA | 1 | 1 | 0 | 1 个激活样本未过 check_admission（含 oversized/Unknown）；且被上游独立阻塞 FS-INFRA——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY |
| T03-F5-W9 | L1d-TLB | T03 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T04-F0-W4 | L1d-TLB | T04 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 18 | 18 | 8 | 4/18 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T04-F2-W4 | L1d-TLB | T04 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 13 | 13 | 4 | 2/13 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T04-F6-W4 | L1d-TLB | T04 | TRUNCATED | BLOCKED | STRESS_ONLY | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 13 | 11 | 3 | 4/13 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T05-F0-W4 | L1d-TLB | T05 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 3 | 3 | 1 | 2/3 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T05-F2-W4 | L1d-TLB | T05 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T05-F6-W4 | L1d-TLB | T05 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T06-F0-W4 | L1d-TLB | T06 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 1 | 1 | 0 | 1/1 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T06-F2-W4 | L1d-TLB | T06 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T06-F6-W4 | L1d-TLB | T06 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T07-F0-W4 | L1d-TLB | T07 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 1 | 1 | 0 | 1/1 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T07-F4-W4 | L1d-TLB | T07 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T07-F6-W4 | L1d-TLB | T07 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T08-F0-W4 | L1d-TLB | T08 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 2 | 2 | 0 | 2/2 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T08-F0-W9 | L1d-TLB | T08 | NOT_RUN | BLOCKED | NORMAL | MODE-UNIMPL | NOT_RUN | BLOCKED | MODE-UNIMPL | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED；另有 1 条 pilot 路径存在但**不在权威 runs 根内**（草稿/他处产物，不构成权威证据，如 .claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_t6_pilot2/T08-F0-W9/seed1/prop_evt.txt.gz） |
| T08-F4-W4 | L1d-TLB | T08 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T08-F4-W9 | L1d-TLB | T08 | NOT_RUN | BLOCKED | NORMAL | MODE-UNIMPL | NOT_RUN | BLOCKED | MODE-UNIMPL | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T08-F6-W4 | L1d-TLB | T08 | NOT_RUN | BLOCKED | STRESS_ONLY | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T08-F6-W9 | L1d-TLB | T08 | NOT_RUN | BLOCKED | STRESS_REDUNDANT | MODE-UNIMPL | NOT_RUN | BLOCKED | MODE-UNIMPL | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F0-W1 | L1d-TLB | T10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F0-W11 | L1d-TLB | T10 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F0-W4 | L1d-TLB | T10 | TRUNCATED | BLOCKED | NORMAL | FS-INFRA | TRUNCATED | BLOCKED | FS-INFRA | 2 | 2 | 0 | 1/2 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF） |
| T10-F1-W1 | L1d-TLB | T10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F1-W11 | L1d-TLB | T10 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F1-W4 | L1d-TLB | T10 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F2-W1 | L1d-TLB | T10 | NOT_RUN | RUNNABLE | NORMAL | NONE | NOT_RUN | READY | NONE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F2-W11 | L1d-TLB | T10 | NOT_RUN | BLOCKED | NORMAL | LICENSE | NOT_RUN | BLOCKED | LICENSE | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
| T10-F2-W4 | L1d-TLB | T10 | NOT_RUN | BLOCKED | NORMAL | FS-INFRA | NOT_RUN | BLOCKED | FS-INFRA | 0 | 0 | 0 | not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED |
