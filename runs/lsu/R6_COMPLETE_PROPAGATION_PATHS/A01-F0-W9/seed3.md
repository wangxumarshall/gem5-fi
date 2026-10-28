# A01-F0-W9 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F0-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F0 |
| 负载 | W9 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3 --cells A01-F0-W9 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=98430640，request_id=，corr=origin，注入前地址 `before=494df8`，注入后地址 `after=1494df8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 98430640, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x494df8, new_vaddr=0x1494df8, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`494df8` → `1494df8`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 98430640 |  | 494df8 |  |  |  | origin |
| addr_form | 2 | 1 | 98430640 |  | 1494df8 |  |  |  | origin |
| mem_req | 3 | 2 | 98430640 | 313320 | 1494df8 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 98430640 | 313320 | 1494df8 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 98430640 | 313320 | 1494df8 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 98430640 | 313320 | 1494df8 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 98432565 |  | 1494df8 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 98432565 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=1494df8 pa=
- L2 `lsq_sendfrag`：va=1494df8 pa=
- L2 `tlb_translate`：va=1494df8 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=98432565）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3/A01-F0-W9/seed3/prop_evt.txt.gz` | `a50bb69bf92c1c294bd9dd3cb9c88c62fa5b20d4602c7ec89337cec970ba8ea5` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3/A01-F0-W9/seed3/stats.txt` | `7e1bda1b6ec14a17abd126ad4a0af2a308e7164e2845a080c14d426e9c8a0d79` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3/A01-F0-W9/seed3/run.out` | `3134690025ef1a0f32a01411cb03302b8b508c9d1956c9880d535cd52e2dd10f` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3/A01-F0-W9/seed3/run.err` | `66e06f55a4ef14019f2c42b51c37d976b18e588e00c03fb7ff4f5f9dd1d79a53` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3/A01-F0-W9/chain_report.json` | `af4b9be4000b4bc6632177095d9d68bf03a0071168584fcb8b7919c9ddfe1932` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W9_s3/manifest.json` | `4db22887195c092bf94de00749f91f10c4118b7c7968c4103351ae561404dc32` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

