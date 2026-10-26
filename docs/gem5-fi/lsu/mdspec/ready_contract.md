# 325 RunID READY 契约（R4-7）

- 总数：325（**READY=0 / PARTIAL=0 / BLOCKED=325**）
- 自洽：✅
- BLOCKED 分类：{'CHAIN-UNPROVEN': 44, 'CHAIN-EVIDENCE-MISSING': 197, 'RULING': 6, 'FS-INFRA': 24, 'MODE-UNIMPL': 3, 'UNRESOLVED': 4, 'FS-MULTICORE': 35, 'LICENSE': 12}
- **频率政策（R6-FREQPOLICY，独立轴）**：{'NORMAL': 261, 'STRESS_REDUNDANT': 25, 'STRESS_ONLY': 39} —— `policy_state`（NORMAL/STRESS_ONLY/STRESS_REDUNDANT，来源 `R6-FREQUENCY-POLICY.json`）只报告不裁决：政策排除（STRESS_REDUNDANT）≠ 技术 BLOCKED，status/category 完全由技术门（台账/覆盖/链）决定
- **链准入门禁（R6-GATE）**：READY 须经 `lsu_chain_check.check_admission` 准入（完整 family-specific L0→L5 链，或显式 containment 且后续层全 N/A(contained)）。[L29] 门禁对**每一行**评估（recorded=325/325）并逐行记录，与上游类别无关；上游阻塞是**独立**阻塞，不因链准入而解除。证据根 `/home/sdc/gem5-fi-ding`，事件上限 4000；admitted=1 / evaluated=64 / CHAIN-UNPROVEN=44 / CHAIN-EVIDENCE-MISSING=197
- **链已准入但上游独立阻塞**（1 行）：T05-F0-W4——链准入不等于解锁，仍按上游理由 BLOCKED
- **准入裁决：NO-GO**（BLOCKED=325 > 0（{'CHAIN-UNPROVEN': 44, 'CHAIN-EVIDENCE-MISSING': 197, 'RULING': 6, 'FS-INFRA': 24, 'MODE-UNIMPL': 3, 'UNRESOLVED': 4, 'FS-MULTICORE': 35, 'LICENSE': 12}）；未运行 --gate 资源/测试门禁）
- 正式口径：`--phase screening`，默认 RunID 累计 ≥385 activated，21 个重点 RunID 累计 2401；`--max-parallel 1`（禁止 trial/3-seed 与 Wilson 序贯）
- FS checkpoint：`/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`

| RunID | 单元 | 模型 | F | 政策 | 状态 | 类别 | 覆盖 | 链门禁 | 命令(READY/PARTIAL) |
|---|---|---|---|---|---|---|---|---|---|
| A01-F0-W3 | AGU | A01 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/detected_translation_outcome_pending/n=1 | — |
| A01-F0-W9 | AGU | A01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A01-F1-W3 | AGU | A01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A01-F1-W9 | AGU | A01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A01-F2-W3 | AGU | A01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A01-F2-W9 | AGU | A01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A02-F0-W3 | AGU | A02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A02-F0-W9 | AGU | A02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A02-F2-W3 | AGU | A02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A02-F2-W9 | AGU | A02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A03-F5-W3 | AGU | A03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A03-F5-W10 | AGU | A03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A04-F0-W3 | AGU | A04 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| A04-F0-W0 | AGU | A04 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A04-F2-W3 | AGU | A04 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A04-F2-W0 | AGU | A04 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A04-F6-W3 | AGU | A04 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A04-F6-W0 | AGU | A04 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A05-F0-W3 | AGU | A05 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A05-F2-W3 | AGU | A05 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A05-F6-W3 | AGU | A05 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A06-F0-W3 | AGU | A06 | F0 | NORMAL | BLOCKED | RULING | BLOCKED | admitted=False/provable_to_L3_then_unknown/n=1 | — |
| A06-F0-W5 | AGU | A06 | F0 | NORMAL | BLOCKED | RULING | BLOCKED | admitted=False/provable_to_L3_then_unknown/n=1 | — |
| A06-F2-W3 | AGU | A06 | F2 | NORMAL | BLOCKED | RULING | BLOCKED | admitted=False/n=0 | — |
| A06-F2-W5 | AGU | A06 | F2 | NORMAL | BLOCKED | RULING | BLOCKED | admitted=False/n=0 | — |
| A06-F6-W3 | AGU | A06 | F6 | STRESS_ONLY | BLOCKED | RULING | BLOCKED | admitted=False/n=0 | — |
| A06-F6-W5 | AGU | A06 | F6 | STRESS_REDUNDANT | BLOCKED | RULING | BLOCKED | admitted=False/n=0 | — |
| A07-F0-W3 | AGU | A07 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L3_then_unknown/n=3 | — |
| A07-F0-W5 | AGU | A07 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L3_then_unknown/n=3 | — |
| A07-F4-W3 | AGU | A07 | F4 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| A07-F4-W5 | AGU | A07 | F4 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| A07-F6-W3 | AGU | A07 | F6 | STRESS_ONLY | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| A07-F6-W5 | AGU | A07 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| A08-F0-W3 | AGU | A08 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A08-F0-W5 | AGU | A08 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A08-F2-W3 | AGU | A08 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A08-F2-W5 | AGU | A08 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A08-F6-W3 | AGU | A08 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| A08-F6-W5 | AGU | A08 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T01-F0-W1 | L1d-TLB | T01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T01-F0-W4 | L1d-TLB | T01 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/detected_contained/n=1 | — |
| T01-F1-W1 | L1d-TLB | T01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T01-F1-W4 | L1d-TLB | T01 | F1 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T01-F2-W1 | L1d-TLB | T01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T01-F2-W4 | L1d-TLB | T01 | F2 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T02-F0-W1 | L1d-TLB | T02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T02-F0-W4 | L1d-TLB | T02 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| T02-F2-W1 | L1d-TLB | T02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T02-F2-W4 | L1d-TLB | T02 | F2 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T03-F5-W4 | L1d-TLB | T03 | F5 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/detected_contained/n=1 | — |
| T03-F5-W9 | L1d-TLB | T03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T04-F0-W4 | L1d-TLB | T04 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| T04-F2-W4 | L1d-TLB | T04 | F2 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| T04-F6-W4 | L1d-TLB | T04 | F6 | STRESS_ONLY | BLOCKED | FS-INFRA | BLOCKED | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| T05-F0-W4 | L1d-TLB | T05 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=True/detected_contained/n=1 | — |
| T05-F2-W4 | L1d-TLB | T05 | F2 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T05-F6-W4 | L1d-TLB | T05 | F6 | STRESS_ONLY | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T06-F0-W4 | L1d-TLB | T06 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/detected_contained/n=1 | — |
| T06-F2-W4 | L1d-TLB | T06 | F2 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T06-F6-W4 | L1d-TLB | T06 | F6 | STRESS_ONLY | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T07-F0-W4 | L1d-TLB | T07 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/provable_to_L2_then_unknown/n=1 | — |
| T07-F4-W4 | L1d-TLB | T07 | F4 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T07-F6-W4 | L1d-TLB | T07 | F6 | STRESS_ONLY | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T08-F0-W4 | L1d-TLB | T08 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/detected_contained/n=1 | — |
| T08-F0-W9 | L1d-TLB | T08 | F0 | NORMAL | BLOCKED | MODE-UNIMPL | BLOCKED | admitted=False/provable_to_L0_then_unknown/n=1 | — |
| T08-F4-W4 | L1d-TLB | T08 | F4 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T08-F4-W9 | L1d-TLB | T08 | F4 | NORMAL | BLOCKED | MODE-UNIMPL | BLOCKED | admitted=False/n=0 | — |
| T08-F6-W4 | L1d-TLB | T08 | F6 | STRESS_ONLY | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T08-F6-W9 | L1d-TLB | T08 | F6 | STRESS_REDUNDANT | BLOCKED | MODE-UNIMPL | BLOCKED | admitted=False/n=0 | — |
| S01-F0-W1 | Store Queue | S01 | F0 | NORMAL | BLOCKED | UNRESOLVED | PASS | admitted=False/n=0 | — |
| S01-F0-W5 | Store Queue | S01 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L2_then_unknown/n=3 | — |
| S01-F1-W1 | Store Queue | S01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S01-F1-W5 | Store Queue | S01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S01-F2-W1 | Store Queue | S01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S01-F2-W5 | Store Queue | S01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S02-F0-W5 | Store Queue | S02 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L2_then_unknown/n=3 | — |
| S02-F0-W1 | Store Queue | S02 | F0 | NORMAL | BLOCKED | UNRESOLVED | PASS | admitted=False/n=0 | — |
| S02-F2-W5 | Store Queue | S02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S02-F2-W1 | Store Queue | S02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S03-F5-W5 | Store Queue | S03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S03-F5-W10 | Store Queue | S03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S04-F0-W5 | Store Queue | S04 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L3_then_unknown/n=3 | — |
| S04-F0-W0 | Store Queue | S04 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S04-F2-W5 | Store Queue | S04 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S04-F2-W0 | Store Queue | S04 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S04-F6-W5 | Store Queue | S04 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S04-F6-W0 | Store Queue | S04 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S05-F0-W5 | Store Queue | S05 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L3_then_unknown/n=2 | — |
| S05-F0-W3 | Store Queue | S05 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S05-F2-W5 | Store Queue | S05 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S05-F2-W3 | Store Queue | S05 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S05-F6-W5 | Store Queue | S05 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S05-F6-W3 | Store Queue | S05 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S06-F0-W5 | Store Queue | S06 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S06-F0-W6 | Store Queue | S06 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S06-F2-W5 | Store Queue | S06 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S06-F2-W6 | Store Queue | S06 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S06-F6-W5 | Store Queue | S06 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S06-F6-W6 | Store Queue | S06 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S07-F0-W5 | Store Queue | S07 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S07-F4-W5 | Store Queue | S07 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S07-F6-W5 | Store Queue | S07 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S08-F0-W5 | Store Queue | S08 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S08-F2-W5 | Store Queue | S08 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S08-F6-W5 | Store Queue | S08 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S09-F0-W5 | Store Queue | S09 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S09-F2-W5 | Store Queue | S09 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S09-F6-W5 | Store Queue | S09 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S10-F0-W5 | Store Queue | S10 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L1_then_unknown/n=3 | — |
| S10-F0-W9 | Store Queue | S10 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L1_then_unknown/n=3 | — |
| S10-F2-W5 | Store Queue | S10 | F2 | NORMAL | BLOCKED | UNRESOLVED | PASS | admitted=False/n=3 | — |
| S10-F2-W9 | Store Queue | S10 | F2 | NORMAL | BLOCKED | UNRESOLVED | PASS | admitted=False/n=3 | — |
| S10-F5-W5 | Store Queue | S10 | F5 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L1_then_unknown/n=3 | — |
| S10-F5-W9 | Store Queue | S10 | F5 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| S11-F0-W5 | Store Queue | S11 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S11-F0-W6 | Store Queue | S11 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S11-F4-W5 | Store Queue | S11 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S11-F4-W6 | Store Queue | S11 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S11-F6-W5 | Store Queue | S11 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S11-F6-W6 | Store Queue | S11 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C01-F0-W1 | L1d-Cache | C01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C01-F0-W6 | L1d-Cache | C01 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| C01-F1-W1 | L1d-Cache | C01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C01-F1-W6 | L1d-Cache | C01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C01-F2-W1 | L1d-Cache | C01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C01-F2-W6 | L1d-Cache | C01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C02-F0-W6 | L1d-Cache | C02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C02-F0-W1 | L1d-Cache | C02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C02-F2-W6 | L1d-Cache | C02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C02-F2-W1 | L1d-Cache | C02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C03-F5-W6 | L1d-Cache | C03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C03-F5-W10 | L1d-Cache | C03 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C04-F0-W1 | L1d-Cache | C04 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C04-F0-W6 | L1d-Cache | C04 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C04-F1-W1 | L1d-Cache | C04 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C04-F1-W6 | L1d-Cache | C04 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C04-F2-W1 | L1d-Cache | C04 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C04-F2-W6 | L1d-Cache | C04 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C05-F0-W6 | L1d-Cache | C05 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C05-F2-W6 | L1d-Cache | C05 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C05-F6-W6 | L1d-Cache | C05 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C06-F0-W6 | L1d-Cache | C06 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C06-F2-W6 | L1d-Cache | C06 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C06-F5-W6 | L1d-Cache | C06 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C07-F0-W6 | L1d-Cache | C07 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C07-F2-W6 | L1d-Cache | C07 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C07-F5-W6 | L1d-Cache | C07 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C07-F6-W6 | L1d-Cache | C07 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C08-F0-W6 | L1d-Cache | C08 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C08-F0-W7 | L1d-Cache | C08 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| C08-F2-W6 | L1d-Cache | C08 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C08-F2-W7 | L1d-Cache | C08 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| C08-F5-W6 | L1d-Cache | C08 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C08-F5-W7 | L1d-Cache | C08 | F5 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| C08-F6-W6 | L1d-Cache | C08 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C08-F6-W7 | L1d-Cache | C08 | F6 | STRESS_REDUNDANT | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| C09-F0-W6 | L1d-Cache | C09 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| C09-F0-W10 | L1d-Cache | C09 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=2 | — |
| C09-F2-W6 | L1d-Cache | C09 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C09-F2-W10 | L1d-Cache | C09 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C09-F6-W6 | L1d-Cache | C09 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C09-F6-W10 | L1d-Cache | C09 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C10-F0-W6 | L1d-Cache | C10 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C10-F0-W10 | L1d-Cache | C10 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C10-F3-W6 | L1d-Cache | C10 | F3 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C10-F3-W10 | L1d-Cache | C10 | F3 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C10-F5-W6 | L1d-Cache | C10 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C10-F5-W10 | L1d-Cache | C10 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C11-F0-W6 | L1d-Cache | C11 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C11-F0-W10 | L1d-Cache | C11 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C11-F2-W6 | L1d-Cache | C11 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C11-F2-W10 | L1d-Cache | C11 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C11-F4-W6 | L1d-Cache | C11 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C11-F4-W10 | L1d-Cache | C11 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C11-F6-W6 | L1d-Cache | C11 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| C11-F6-W10 | L1d-Cache | C11 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C12-F0-W6 | L1d-Cache | C12 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| C12-F0-W10 | L1d-Cache | C12 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C12-F4-W6 | L1d-Cache | C12 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C12-F4-W10 | L1d-Cache | C12 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| C12-F6-W6 | L1d-Cache | C12 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=1 | — |
| C12-F6-W10 | L1d-Cache | C12 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| O01-F0-W7 | 原子与同步 | O01 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=1 | — |
| O01-F2-W7 | 原子与同步 | O01 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O01-F6-W7 | 原子与同步 | O01 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O02-F0-W7 | 原子与同步 | O02 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=1 | — |
| O02-F2-W7 | 原子与同步 | O02 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O02-F5-W7 | 原子与同步 | O02 | F5 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=1 | — |
| O02-F6-W7 | 原子与同步 | O02 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O03-F0-W7 | 原子与同步 | O03 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=1 | — |
| O03-F2-W7 | 原子与同步 | O03 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O03-F6-W7 | 原子与同步 | O03 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O04-F0-W7 | 原子与同步 | O04 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O04-F2-W7 | 原子与同步 | O04 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O04-F6-W7 | 原子与同步 | O04 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O05-F0-W7 | 原子与同步 | O05 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O05-F4-W7 | 原子与同步 | O05 | F4 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O05-F6-W7 | 原子与同步 | O05 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O06-F0-W7 | 原子与同步 | O06 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O06-F4-W7 | 原子与同步 | O06 | F4 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O06-F6-W7 | 原子与同步 | O06 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O07-F0-W7 | 原子与同步 | O07 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O07-F2-W7 | 原子与同步 | O07 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O07-F6-W7 | 原子与同步 | O07 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| P01-F0-W2 | 数据预取器 | P01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P01-F0-W8 | 数据预取器 | P01 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=4 | — |
| P01-F1-W2 | 数据预取器 | P01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P01-F1-W8 | 数据预取器 | P01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P01-F2-W2 | 数据预取器 | P01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P01-F2-W8 | 数据预取器 | P01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P02-F0-W8 | 数据预取器 | P02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P02-F0-W10 | 数据预取器 | P02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P02-F3-W8 | 数据预取器 | P02 | F3 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P02-F3-W10 | 数据预取器 | P02 | F3 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P02-F5-W8 | 数据预取器 | P02 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P02-F5-W10 | 数据预取器 | P02 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P03-F0-W8 | 数据预取器 | P03 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P03-F0-W9 | 数据预取器 | P03 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P03-F2-W8 | 数据预取器 | P03 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P03-F2-W9 | 数据预取器 | P03 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P03-F6-W8 | 数据预取器 | P03 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P03-F6-W9 | 数据预取器 | P03 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P04-F0-W2 | 数据预取器 | P04 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P04-F0-W8 | 数据预取器 | P04 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P04-F4-W2 | 数据预取器 | P04 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P04-F4-W8 | 数据预取器 | P04 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P04-F5-W2 | 数据预取器 | P04 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P04-F5-W8 | 数据预取器 | P04 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P05-F0-W8 | 数据预取器 | P05 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P05-F0-W10 | 数据预取器 | P05 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P05-F4-W8 | 数据预取器 | P05 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P05-F4-W10 | 数据预取器 | P05 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P05-F6-W8 | 数据预取器 | P05 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P05-F6-W10 | 数据预取器 | P05 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P06-F0-W6 | 数据预取器 | P06 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| P06-F0-W8 | 数据预取器 | P06 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| P06-F2-W6 | 数据预取器 | P06 | F2 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| P06-F2-W8 | 数据预取器 | P06 | F2 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| P06-F6-W6 | 数据预取器 | P06 | F6 | STRESS_ONLY | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| P06-F6-W8 | 数据预取器 | P06 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L4_then_unknown/n=3 | — |
| P07-F0-W6 | 数据预取器 | P07 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P07-F0-W8 | 数据预取器 | P07 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P07-F2-W6 | 数据预取器 | P07 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P07-F2-W8 | 数据预取器 | P07 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P07-F6-W6 | 数据预取器 | P07 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P07-F6-W8 | 数据预取器 | P07 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P08-F5-W8 | 数据预取器 | P08 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P08-F5-W10 | 数据预取器 | P08 | F5 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T10-F0-W1 | L1d-TLB | T10 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T10-F0-W4 | L1d-TLB | T10 | F0 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/detected_contained/n=1 | — |
| T10-F0-W11 | L1d-TLB | T10 | F0 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| T10-F1-W1 | L1d-TLB | T10 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T10-F1-W4 | L1d-TLB | T10 | F1 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T10-F1-W11 | L1d-TLB | T10 | F1 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| T10-F2-W1 | L1d-TLB | T10 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| T10-F2-W4 | L1d-TLB | T10 | F2 | NORMAL | BLOCKED | FS-INFRA | BLOCKED | admitted=False/n=0 | — |
| T10-F2-W11 | L1d-TLB | T10 | F2 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| S13-F0-W1 | Store Queue | S13 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F0-W5 | Store Queue | S13 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F0-W11 | Store Queue | S13 | F0 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| S13-F0-W12 | Store Queue | S13 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F1-W1 | Store Queue | S13 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F1-W5 | Store Queue | S13 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F1-W11 | Store Queue | S13 | F1 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| S13-F1-W12 | Store Queue | S13 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F2-W1 | Store Queue | S13 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F2-W5 | Store Queue | S13 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| S13-F2-W11 | Store Queue | S13 | F2 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| S13-F2-W12 | Store Queue | S13 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F0-W1 | Load Queue | L01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F0-W5 | Load Queue | L01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F0-W12 | Load Queue | L01 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F1-W1 | Load Queue | L01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F1-W5 | Load Queue | L01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F1-W12 | Load Queue | L01 | F1 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F2-W1 | Load Queue | L01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F2-W5 | Load Queue | L01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L01-F2-W12 | Load Queue | L01 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L02-F0-W5 | Load Queue | L02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L02-F0-W12 | Load Queue | L02 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L02-F2-W5 | Load Queue | L02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L02-F2-W12 | Load Queue | L02 | F2 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L02-F6-W5 | Load Queue | L02 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L02-F6-W12 | Load Queue | L02 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L03-F0-W5 | Load Queue | L03 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L03-F0-W12 | Load Queue | L03 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L03-F4-W5 | Load Queue | L03 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L03-F4-W12 | Load Queue | L03 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L03-F6-W5 | Load Queue | L03 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L03-F6-W12 | Load Queue | L03 | F6 | STRESS_ONLY | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| L04-F0-W5 | Load Queue | L04 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L0_then_unknown/n=3 | — |
| L04-F0-W11 | Load Queue | L04 | F0 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| L04-F0-W12 | Load Queue | L04 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L0_then_unknown/n=3 | — |
| L04-F2-W5 | Load Queue | L04 | F2 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| L04-F2-W11 | Load Queue | L04 | F2 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| L04-F2-W12 | Load Queue | L04 | F2 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| L04-F6-W5 | Load Queue | L04 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L0_then_unknown/n=3 | — |
| L04-F6-W11 | Load Queue | L04 | F6 | STRESS_ONLY | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| L04-F6-W12 | Load Queue | L04 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L0_then_unknown/n=3 | — |
| C14-F5-W6 | L1d-Cache | C14 | F5 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L0_then_unknown/n=3 | — |
| C14-F5-W10 | L1d-Cache | C14 | F5 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/provable_to_L0_then_unknown/n=3 | — |
| C15-F0-W6 | L1d-Cache | C15 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C15-F0-W10 | L1d-Cache | C15 | F0 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C15-F0-W11 | L1d-Cache | C15 | F0 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| C15-F4-W6 | L1d-Cache | C15 | F4 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C15-F4-W10 | L1d-Cache | C15 | F4 | NORMAL | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C15-F4-W11 | L1d-Cache | C15 | F4 | NORMAL | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| C15-F6-W6 | L1d-Cache | C15 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C15-F6-W10 | L1d-Cache | C15 | F6 | STRESS_ONLY | BLOCKED | CHAIN-UNPROVEN | PASS | admitted=False/n=3 | — |
| C15-F6-W11 | L1d-Cache | C15 | F6 | STRESS_REDUNDANT | BLOCKED | LICENSE | BLOCKED | admitted=False/n=0 | — |
| O09-F0-W7 | 原子与同步 | O09 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O09-F0-W13 | 原子与同步 | O09 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O09-F1-W7 | 原子与同步 | O09 | F1 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O09-F1-W13 | 原子与同步 | O09 | F1 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O09-F2-W7 | 原子与同步 | O09 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| O09-F2-W13 | 原子与同步 | O09 | F2 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| P09-F0-W6 | 数据预取器 | P09 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P09-F0-W8 | 数据预取器 | P09 | F0 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P09-F0-W13 | 数据预取器 | P09 | F0 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| P09-F4-W6 | 数据预取器 | P09 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P09-F4-W8 | 数据预取器 | P09 | F4 | NORMAL | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P09-F4-W13 | 数据预取器 | P09 | F4 | NORMAL | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
| P09-F6-W6 | 数据预取器 | P09 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P09-F6-W8 | 数据预取器 | P09 | F6 | STRESS_REDUNDANT | BLOCKED | CHAIN-EVIDENCE-MISSING | PASS | admitted=False/n=0 | — |
| P09-F6-W13 | 数据预取器 | P09 | F6 | STRESS_ONLY | BLOCKED | FS-MULTICORE | BLOCKED | admitted=False/n=0 | — |
