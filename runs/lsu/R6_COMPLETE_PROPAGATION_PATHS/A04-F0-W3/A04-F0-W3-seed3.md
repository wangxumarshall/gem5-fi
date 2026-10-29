# A04-F0-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F0-W3` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 15627535, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493030, new_addr=0x493148, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=arr, object_base=0x493000, object_size=512, source_offset=48, target_offset=328 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3 --cells A04-F0-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=15627535，request_id=，corr=origin，注入前地址 `before=493030`，注入后地址 `after=493148`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 15627535, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493030, new_addr=0x493148, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=arr, object_base=0x493000, object_size=512, source_offset=48, target_offset=328
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493030` → `493148`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a04a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 15627535 |  | 493030 |  |  |  | origin |
| addr_form | 2 | 1 | 15627535 |  | 493148 |  |  |  | origin |
| lsq_push | 3 | 2 | 15627535 |  | 493148 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 15627535 | 12199 | 493148 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 15627535 | 12199 | 493148 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 15627535 | 12199 | 493148 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 15627535 |  | 493148 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 15629460 |  |  | 79148 |  |  | seq_primary |
| resp | 9 | 8 | 15920905 | 12199 | 79148 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 15920905 | 12199 | 79148 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 15920905 |  | 493148 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 19908735 | 12199 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 19908735 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493148 pa=
- L2 `lsq_sendfrag`：va=493148 pa=
- L2 `tlb_translate`：va=493148 pa=
- L3 `resp`：va=79148 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`SDC`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=19908735）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3/A04-F0-W3/seed3/prop_evt.txt.gz` | `06a8db7df2abb0f652892fc88fb914a7b8aa3218d654c44720ea715d5d8e90df` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3/A04-F0-W3/seed3/stats.txt` | `18dc15afb3fe377f6839e1e5ff123416de8b756cbecf77e4cf034527f6f3dd18` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3/A04-F0-W3/seed3/run.out` | `aa957f098bb450487f7286be3f66be98dd411ef408bd1bbcf3e31d6f02f0f05e` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3/A04-F0-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3/A04-F0-W3/chain_report.json` | `bd7d923e09a58d6c09a50f892a8c2d16e9b405ed6fec2ff31403597930af081b` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s3/manifest.json` | `ff36633c5c10847b6091843490851d645a14c37394c39d6d97b112046957ffcb` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

