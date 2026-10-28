# A02-F0-W9 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F0-W9` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F0 |
| 负载 | W9 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2 --cells A02-F0-W9 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=206105130，request_id=，corr=origin，注入前地址 `before=49c760`，注入后地址 `after=20494760`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 206105130, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x49c760, new_vaddr=0x20494760, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x20008000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`49c760` → `20494760`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 206105130 |  | 49c760 |  |  |  | origin |
| addr_form | 2 | 1 | 206105130 |  | 20494760 |  |  |  | origin |
| mem_req | 3 | 2 | 206105130 | 776920 | 20494760 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 206105130 | 776920 | 20494760 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 206105130 | 776920 | 20494760 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 206105130 | 776920 | 20494760 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 206105900 |  | 20494760 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 206105900 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=20494760 pa=
- L2 `lsq_sendfrag`：va=20494760 pa=
- L2 `tlb_translate`：va=20494760 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=206105900）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2/A02-F0-W9/seed2/prop_evt.txt.gz` | `ded26dfb332eaa734199d3a08101c41b2e180b8767414664744fe30ed4f519b9` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2/A02-F0-W9/seed2/stats.txt` | `a4381b444a726ec5e85ba9ea810bf49ea30cbf8f118865603a634ac44862c7f7` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2/A02-F0-W9/seed2/run.out` | `0c16f528a0c1b244a49ad914c0b4563ff408abc8f64c0f268763edaab4f79902` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2/A02-F0-W9/seed2/run.err` | `c5212bddfd3ebc8de35e79aa68cd6f386b00d1a9388af34fe74a58f3b34acaaa` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2/A02-F0-W9/chain_report.json` | `a882d28bdc6cf5974f4bd5bed921e2b18664996e00782defabb6c2f8b05cf677` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s2/manifest.json` | `b1f9ed231486e5f14f8bd0a3d457ebacd307c3affcd3eac34bc4da3745569905` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

