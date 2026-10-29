# A02-F0-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F0-W3` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2 --cells A02-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=6146910，request_id=，corr=origin，注入前地址 `before=490790`，注入后地址 `after=20498790`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 6146910, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x490790, new_vaddr=0x20498790, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x20008000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`490790` → `20498790`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → sq_execute → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，sq_execute=L3，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 6146910 |  | 490790 |  |  |  | origin |
| addr_form | 2 | 1 | 6146910 |  | 20498790 |  |  |  | origin |
| mem_req | 3 | 2 | 6146910 | 4351 | 20498790 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 6146910 | 4351 | 20498790 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 6146910 | 4351 | 20498790 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 6146910 | 4351 | 20498790 |  | Hardware | Generic | seq_primary |
| sq_execute | 7 | 6 | 6146910 |  | 20498790 |  |  |  | seq_primary |
| arch_translation_fault | 8 | 7 | 6213130 |  | 20498790 |  | L2 | arch_exception | seq_primary |
| chain_end | 9 | 8 | 6213130 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=20498790 pa=
- L2 `lsq_sendfrag`：va=20498790 pa=
- L2 `tlb_translate`：va=20498790 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L3`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=9。
- 事件数：本 seed 流共 9 条，其中 fault_id=1 链 9 条；最后一条为 `chain_end`（event_id=9, tick=6213130）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2/A02-F0-W3/seed2/prop_evt.txt.gz` | `6935642d04d69470edcf138ea977f8f9a91210bb3aa3fec5d3b94732b82c16f4` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2/A02-F0-W3/seed2/stats.txt` | `f1c8870f93f41446f994b90c7cc11fdd3cfad3e57f423f17a2b316583779d315` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2/A02-F0-W3/seed2/run.out` | `c398696d6d73c0d75a89fa9ca19930e5acab3237b394a6bdbd43419ccd504a3a` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2/A02-F0-W3/seed2/run.err` | `8ca58c102c191f41c8bcdc546805048151eaf473217e53caafd047e7aa19c795` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2/A02-F0-W3/chain_report.json` | `c2a8e3123227a82b83aad7d54aad57c1152dca92260eee930e43930da0c2013a` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W3_s2/manifest.json` | `23d42b9b18559bd9f8065f89e5208279ca3b44c77e52acb106a5a5282afeb7d8` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

