# A01-F0-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F0-W3` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2 --cells A01-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=6146910，request_id=，corr=origin，注入前地址 `before=490790`，注入后地址 `after=498790`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 6146910, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x490790, new_vaddr=0x498790, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`490790` → `498790`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 6146910 |  | 490790 |  |  |  | origin |
| addr_form | 2 | 1 | 6146910 |  | 498790 |  |  |  | origin |
| mem_req | 3 | 2 | 6146910 | 4351 | 498790 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 6146910 | 4351 | 498790 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 6146910 | 4351 | 498790 |  |  |  | seq_primary |
| sq_execute | 6 | 5 | 6146910 |  | 498790 |  |  |  | seq_primary |
| sq_writeback | 7 | 6 | 6158075 |  |  | 7e790 |  |  | seq_primary |
| resp | 8 | 7 | 6217365 | 4351 | 7e790 |  |  |  | seq_primary |
| taint_reg | 9 | 8 | 6217365 | 4351 | 7e790 |  |  |  | seq_primary |
| sq_complete | 10 | 9 | 6217365 |  | 498790 |  |  |  | seq_primary |
| store_not_retired | 11 | 10 | 19994975 | 4351 |  |  | L4 | contained | taint_prop |
| chain_end | 12 | 11 | 19994975 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=498790 pa=
- L2 `lsq_sendfrag`：va=498790 pa=
- L2 `tlb_translate`：va=498790 pa=
- L3 `resp`：va=7e790 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=12。
- 事件数：本 seed 流共 12 条，其中 fault_id=1 链 12 条；最后一条为 `chain_end`（event_id=12, tick=19994975）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2/A01-F0-W3/seed2/prop_evt.txt.gz` | `de7d55da71a12146940650ba79da29a06650fd0a2ae70b6aefcb28dd6eff48f2` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2/A01-F0-W3/seed2/stats.txt` | `aa8ef7783fade96e4881fecd41c8f13b01dc93be6a4bea79711b740ba8629444` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2/A01-F0-W3/seed2/run.out` | `5362b46eb70977957c79e55c83f14fac40ec09f7f186bed90a7661bde75c4c48` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2/A01-F0-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2/A01-F0-W3/chain_report.json` | `5e05753449b598e96f0eb7b1cb57adc73dce26b5cc4e06bb5fa42b28488d6bb0` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s2/manifest.json` | `bed4b7da4637679dab82cf532eb07542cf3a1407275ca358317e3f706512a2de` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

