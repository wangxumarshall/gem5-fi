# A02-F0-W9 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F0-W9` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F0 |
| 负载 | W9 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1 --cells A02-F0-W9 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=39635750，request_id=，corr=origin，注入前地址 `before=4958c8`，注入后地址 `after=4958ce`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 39635750, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x4958c8, new_vaddr=0x4958ce, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x6 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4958c8` → `4958ce`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 39635750 |  | 4958c8 |  |  |  | origin |
| addr_form | 2 | 1 | 39635750 |  | 4958ce |  |  |  | origin |
| mem_req | 3 | 2 | 39635750 | 49467 | 4958ce |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 39635750 | 49467 | 4958ce |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 39635750 | 49467 | 4958ce |  |  |  | seq_primary |
| lq_read | 6 | 5 | 39635750 | 49467 | 4958ce |  |  |  | seq_primary |
| resp | 7 | 6 | 39636520 | 49467 | 7b8ce |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 39636520 | 49467 | 4958ce | 7b8ce |  |  | seq_primary |
| taint_reg | 9 | 8 | 39636520 | 49467 | 7b8ce |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 39637290 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 39637675 |  |  |  |  |  | taint_prop |
| consumer | 12 | 11 | 39638060 |  |  |  |  |  | taint_prop |
| consumer | 13 | 11 | 39638060 |  |  |  |  |  | taint_prop |
| consumer | 14 | 11 | 39638060 |  |  |  |  |  | taint_prop |
| chain_end | 15 | 14 | 325381980 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4958ce pa=
- L2 `lsq_sendfrag`：va=4958ce pa=
- L2 `tlb_translate`：va=4958ce pa=
- L3 `resp`：va=7b8ce pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=15。
- 事件数：本 seed 流共 15 条，其中 fault_id=1 链 15 条；最后一条为 `chain_end`（event_id=15, tick=325381980）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1/A02-F0-W9/seed1/prop_evt.txt.gz` | `b5c94321e96be7e2eb9d15058b9c7216746f1bd840f2dc9a0683b42ae7f9fa99` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1/A02-F0-W9/seed1/stats.txt` | `fe33541683b27ec1a54a132b50ec78961a38b562fe1a83b33a612d01eab94510` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1/A02-F0-W9/seed1/run.out` | `25e430eef938013f5aa0509a6b103e9e476f53dd2a77c0b018d400fcaccf88bd` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1/A02-F0-W9/seed1/run.err` | `70eea0776f34f13af666fe542bab517beab9a8b81989f41e1d73d96763cfdc80` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1/A02-F0-W9/chain_report.json` | `8291ab1ae099bae51971d3e0d0caeca76def27eebc5d81d59243ae3e5c46f923` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F0-W9_s1/manifest.json` | `43b544e7983984419879704b0ef989d84d55cf186bcf813bf306ce4db1c244c6` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

