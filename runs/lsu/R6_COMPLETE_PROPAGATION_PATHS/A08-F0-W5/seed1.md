# A08-F0-W5 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F0-W5` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F0 |
| 负载 | W5 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd40, size=8, page_ok=0, decline_reason=store_before_load |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1 --cells A08-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=12308450，request_id=，corr=origin，注入前地址 `before=7ffffefc40`，注入后地址 `after=7ffffefc40`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd40, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141295, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141295, dyn_inst_seq=19, request_id=19, isLoad=0, load_seq=0, store_seq=19, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd48, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141680, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141680, dyn_inst_seq=23, request_id=23, isLoad=0, load_seq=0, store_seq=23, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd50, size=8, page_ok=0, decline_reason=store_before_load
Tick: 142065, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=142065, dyn_inst_seq=24, request_id=24, isLoad=0, load_seq=0, store_seq=24, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd58, size=8, page_ok=0, decline_reason=store_before_load
... (1174 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefc40` → `7ffffefc40`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x0`
- `new_ea` = `0x0`
- `submodel` = `a08a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 12308450 |  | 7ffffefc40 |  |  |  | origin |
| addr_form | 2 | 1 | 12308450 |  | 7ffffefc40 |  |  |  | origin |
| lsq_push | 3 | 2 | 12308450 |  | 7ffffefc40 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 12308450 | 9538 | 7ffffefc40 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 12308450 | 9538 | 7ffffefc40 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 12308450 | 9538 | 7ffffefc40 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 12308450 |  | 7ffffefc40 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 12310760 |  |  | 7dc40 |  |  | seq_primary |
| resp | 9 | 8 | 12311531 | 9538 | 7dc40 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 12311531 | 9538 | 7dc40 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 12311531 |  | 7ffffefc40 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 19229210 | 9538 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 19229210 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ffffefc40 pa=
- L2 `lsq_sendfrag`：va=7ffffefc40 pa=
- L2 `tlb_translate`：va=7ffffefc40 pa=
- L3 `resp`：va=7dc40 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=19229210）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1/A08-F0-W5/seed1/prop_evt.txt.gz` | `e42fe1b4c85cd2b681920ce0bb887f1e6882bd7fe38efd442ffb21299118034a` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1/A08-F0-W5/seed1/stats.txt` | `cf864d92ea99678b8596226bfbc94d406f8346f1c5ed5ba31d82feec2d7beb9f` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1/A08-F0-W5/seed1/run.out` | `b11d7e2b482a5d459e750907b0b78e62491330a6baaeddae191449f96bef7207` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1/A08-F0-W5/seed1/run.err` | `79c4fee84c75e876e776c69f1f0af49807527b7520b0353150d609626ace8fea` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1/A08-F0-W5/chain_report.json` | `7fe7bdac3fd300c4857c6d2dc4edd9773c9ba83442ab2e53763c54dee575d34f` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s1/manifest.json` | `b72459760ef15957e2490e70f06f6c2eb32b603e974f31402a2951c280b94640` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

