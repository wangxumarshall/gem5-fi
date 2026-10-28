# A03-F5-W10 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A03-F5-W10` |
| 模型 | A03（AGU EA bit stuck-at） |
| 频率档 | F5 |
| 负载 | W10 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3 --cells A03-F5-W10 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=80080，request_id=，corr=origin，注入前地址 `before=7ffffefdd0`，注入后地址 `after=7ffffef9d0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 80080, Site: lsq_sendFragmentToTranslation, mode=a03_stuck0, old_vaddr=0x7ffffefdd0, new_vaddr=0x7ffffef9d0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x400 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
Tick: 140910, Site: lsq_sendFragmentToTranslation, mode=a03_stuck0, old_vaddr=0x7ffffefd40, new_vaddr=0x7ffffef940, faults_injected: 2, geom_candidates=1, geom_rejects=0, geom_bitmask=0x400 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
Tick: 141295, Site: lsq_sendFragmentToTranslation, mode=a03_stuck0, old_vaddr=0x7ffffefd48, new_vaddr=0x7ffffef948, faults_injected: 3, geom_candidates=1, geom_rejects=0, geom_bitmask=0x400 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
Tick: 141680, Site: lsq_sendFragmentToTranslation, mode=a03_stuck0, old_vaddr=0x7ffffefd50, new_vaddr=0x7ffffef950, faults_injected: 4, geom_candidates=1, geom_rejects=0, geom_bitmask=0x400 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
... (85 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefdd0` → `7ffffef9d0`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 80080 |  | 7ffffefdd0 |  |  |  | origin |
| addr_form | 2 | 1 | 80080 |  | 7ffffef9d0 |  |  |  | origin |
| mem_req | 3 | 2 | 80080 | 5 | 7ffffef9d0 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 80080 | 5 | 7ffffef9d0 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 80080 | 5 | 7ffffef9d0 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 80080 | 5 | 7ffffef9d0 |  |  |  | seq_primary |
| resp | 84 | 6 | 148225 | 5 | ac9d0 |  |  |  | seq_primary |
| lq_complete | 85 | 84 | 148225 | 5 | 7ffffef9d0 | ac9d0 |  |  | seq_primary |
| taint_reg | 86 | 85 | 148225 | 5 | ac9d0 |  |  |  | seq_primary |
| errant_commit | 87 | 86 | 148995 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 88 | 86 | 149765 |  |  |  |  |  | taint_prop |
| consumer | 89 | 88 | 149765 |  |  |  |  |  | taint_prop |
| consumer | 142 | 89 | 199045 |  |  |  |  |  | taint_prop |
| consumer | 143 | 142 | 199430 |  |  |  |  |  | taint_prop |
| consumer | 178 | 143 | 206745 |  |  |  |  |  | taint_prop |
| consumer | 189 | 143 | 284130 |  |  |  |  |  | taint_prop |
| consumer | 379 | 189 | 570185 |  |  |  |  |  | taint_prop |
| consumer | 380 | 379 | 570185 |  |  |  |  |  | taint_prop |
| chain_end | 1044 | 380 | 1282820 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ffffef9d0 pa=
- L2 `lsq_sendfrag`：va=7ffffef9d0 pa=
- L2 `tlb_translate`：va=7ffffef9d0 pa=
- L3 `resp`：va=ac9d0 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Crash`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=1044。
- 事件数：本 seed 流共 1044 条，其中 fault_id=1 链 19 条；最后一条为 `chain_end`（event_id=1044, tick=1282820）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3/A03-F5-W10/seed3/prop_evt.txt.gz` | `35169546f11110a56285ec6730630930b2f5524a3b63fa551d4200d325fb49ec` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3/A03-F5-W10/seed3/stats.txt` | `f2c12f5b21ed3af0ed037a226e36d349ec4e486b9a07c98e1f66a852a6f43713` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3/A03-F5-W10/seed3/run.out` | `6b9aad6f256030ee13b5d605d3d65aeb08868e027d54ad10b32ea6ab29501d78` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3/A03-F5-W10/seed3/run.err` | `87b49b6f00c21ef4b216f8b9b14f4310d64991040e0db55e3df6dd852b0efaf3` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3/A03-F5-W10/chain_report.json` | `5d0944422cad36a9b7e3e40787904f42d6944a6c3619345f703dfa1086f100d0` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s3/manifest.json` | `20763a74c183138add003cb669951060ec54bf4b09d426acce7424530afbfc62` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

