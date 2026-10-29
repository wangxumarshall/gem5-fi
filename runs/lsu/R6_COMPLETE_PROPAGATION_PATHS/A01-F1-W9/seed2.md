# A01-F1-W9 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F1-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F1 |
| 负载 | W9 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2 --cells A01-F1-W9 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=1191250060，request_id=，corr=origin，注入前地址 `before=4929b8`，注入后地址 `after=49a9b8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 1191250060, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x4929b8, new_vaddr=0x49a9b8, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4929b8` → `49a9b8`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 1191250060 |  | 4929b8 |  |  |  | origin |
| addr_form | 2 | 1 | 1191250060 |  | 49a9b8 |  |  |  | origin |
| mem_req | 3 | 2 | 1191250060 | 4951431 | 49a9b8 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 1191250060 | 4951431 | 49a9b8 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 1191250060 | 4951431 | 49a9b8 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 1191250060 | 4951431 | 49a9b8 |  |  |  | seq_primary |
| resp | 7 | 6 | 1191250830 | 4951431 | 809b8 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 1191250830 | 4951431 | 49a9b8 | 809b8 |  |  | seq_primary |
| taint_reg | 9 | 8 | 1191250830 | 4951431 | 809b8 |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 1191251600 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 1191251985 |  |  |  |  |  | taint_prop |
| consumer | 12 | 11 | 1191252755 |  |  |  |  |  | taint_prop |
| chain_end | 13 | 12 | 1772954645 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=49a9b8 pa=
- L2 `lsq_sendfrag`：va=49a9b8 pa=
- L2 `tlb_translate`：va=49a9b8 pa=
- L3 `resp`：va=809b8 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=1772954645）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2/A01-F1-W9/seed2/prop_evt.txt.gz` | `cbe3ba2321ca046412958f7feb64ea61c3c37d6d69a68e33b2505b7d0e70b812` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2/A01-F1-W9/seed2/stats.txt` | `1eae6d37cc5d6eafe8ec8366d183d70659e4e8955d801222379638d4658f5c33` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2/A01-F1-W9/seed2/run.out` | `0bedaf3e993e0a62a070972a641add1f3940f8933d185baaea26420a1df167e6` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2/A01-F1-W9/seed2/run.err` | `70eea0776f34f13af666fe542bab517beab9a8b81989f41e1d73d96763cfdc80` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2/A01-F1-W9/chain_report.json` | `3f676ed5b00a0bafa2074b52a17fdc4927dbe8e36956c38fc7ba3c61e66270df` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s2/manifest.json` | `fb5c325ca2ed9790f92c1cdb331a2b992ba59024c2300f62d38762947d7e096f` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

