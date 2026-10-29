# A01-F2-W9 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F2-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F2 |
| 负载 | W9 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3 --cells A01-F2-W9 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 900` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=194606720，request_id=，corr=origin，注入前地址 `before=49db40`，注入后地址 `after=149db40`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 194606720, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x49db40, new_vaddr=0x149db40, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`49db40` → `149db40`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → lq_read → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，lq_read=L3，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 194606720 |  | 49db40 |  |  |  | origin |
| addr_form | 2 | 1 | 194606720 |  | 149db40 |  |  |  | origin |
| mem_req | 3 | 2 | 194606720 | 728947 | 149db40 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 194606720 | 728947 | 149db40 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 194606720 | 728947 | 149db40 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 194606720 | 728947 | 149db40 |  | Hardware | Generic | seq_primary |
| lq_read | 7 | 6 | 194606720 | 728947 | 149db40 |  |  |  | seq_primary |
| arch_translation_fault | 8 | 7 | 194608260 |  | 149db40 |  | L2 | arch_exception | seq_primary |
| chain_end | 9 | 8 | 194608260 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=149db40 pa=
- L2 `lsq_sendfrag`：va=149db40 pa=
- L2 `tlb_translate`：va=149db40 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L3`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=9。
- 事件数：本 seed 流共 9 条，其中 fault_id=1 链 9 条；最后一条为 `chain_end`（event_id=9, tick=194608260）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`。
终局见证事件（本 seed 自己的流）：kind=`arch_translation_fault`，event_id=8，parent_event_id=7，tick=194608260，detection_layer=L2，outcome=arch_exception，contained=1，corr=seq_primary。
该事件是**真实交付的架构翻译异常**（guest SEGV）：L2 硬件检测 + contained 字段 + 与注入链的 corr 关联；门禁按既有规则接受为 `detected_contained`——不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3/A01-F2-W9/seed3/prop_evt.txt.gz` | `b7b388ea6dd31e6cfae4afa83993e5728f0f956d7cc1b8d517c800574c420950` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3/A01-F2-W9/seed3/stats.txt` | `75f020fc17aa17ef7b96195da13177ed8b4b1feccfae08469e82f27d879623b3` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3/A01-F2-W9/seed3/run.out` | `04ed25245b5a7b4f04ac8aab9d8514418a0fa365079ade70da5f6353bcb761c3` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3/A01-F2-W9/seed3/run.err` | `7a7ceca35934d5781ad3acb7c820e1ce250bbfc3231bcf9b29ed91b41bb46d03` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3/A01-F2-W9/chain_report.json` | `e5f6902d9caa4caeb32f2085bf0e947897f0592c2c225ec681e38a759472ebea` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s3/manifest.json` | `a5ecee56cf771be5f6aac7e6e3ad03fae9d5659a49b958e3fb881f652699d4cb` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

