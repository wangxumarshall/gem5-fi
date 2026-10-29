# A01-F1-W9 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F1-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F1 |
| 负载 | W9 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3 --cells A01-F1-W9 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=1463349195，request_id=，corr=origin，注入前地址 `before=494ff0`，注入后地址 `after=1494ff0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 1463349195, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x494ff0, new_vaddr=0x1494ff0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`494ff0` → `1494ff0`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 1463349195 |  | 494ff0 |  |  |  | origin |
| addr_form | 2 | 1 | 1463349195 |  | 1494ff0 |  |  |  | origin |
| mem_req | 3 | 2 | 1463349195 | 6105825 | 1494ff0 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 1463349195 | 6105825 | 1494ff0 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 1463349195 | 6105825 | 1494ff0 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 1463349195 | 6105825 | 1494ff0 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 1463353045 |  | 1494ff0 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 1463353045 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=1494ff0 pa=
- L2 `lsq_sendfrag`：va=1494ff0 pa=
- L2 `tlb_translate`：va=1494ff0 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=1463353045）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3/A01-F1-W9/seed3/prop_evt.txt.gz` | `efd0e2f634ec90a06940e396a625139a674df1e13d4bb5cbe4f2df08e68aa5cc` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3/A01-F1-W9/seed3/stats.txt` | `c537525049ded58cfcb40132a50039859b58aa0e8c7dcc976abc304cc158db86` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3/A01-F1-W9/seed3/run.out` | `a633e00e8d038387ef5b2683f3f515f8b9c93ffefa3364db874e0cf4f5405844` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3/A01-F1-W9/seed3/run.err` | `e58a432a1a0457094143b43f3a1a55e01047311cf2215e497d8befc05f3be4fd` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3/A01-F1-W9/chain_report.json` | `a3b1343024a02520b3fbda0485b0c8d831c675e126afe2d9b4479cd95f48794f` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s3/manifest.json` | `02c17e4c0533fc6e45c7fdaaa6ea33f67bd13cd2484c1a8884d9bbf03606e56b` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

