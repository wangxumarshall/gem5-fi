# A06-F2-W5 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A06-F2-W5` |
| 模型 | A06（AGU 访问尺寸/掩码） |
| 频率档 | F2 |
| 负载 | W5 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 239557395, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4919d0, new_addr=0x4919d0, old_size=8, new_size=4, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1 --cells A06-F2-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=239557395，request_id=，corr=origin，注入前地址 `before=4919d0`，注入后地址 `after=4919d0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 239557395, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4919d0, new_addr=0x4919d0, old_size=8, new_size=4, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4919d0` → `4919d0`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `4`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a06a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 239557395 |  | 4919d0 |  |  |  | origin |
| addr_form | 2 | 1 | 239557395 |  | 4919d0 |  |  |  | origin |
| lsq_push | 3 | 2 | 239557395 |  | 4919d0 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 239557395 | 1112830 | 4919d0 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 239557395 | 1112830 | 4919d0 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 239557395 | 1112830 | 4919d0 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 239557395 |  | 4919d0 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 239563170 |  |  | 779d0 |  |  | seq_primary |
| resp | 9 | 8 | 239563940 | 1112830 | 779d0 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 239563940 | 1112830 | 779d0 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 239563940 |  | 4919d0 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 290851330 | 1112830 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 290851330 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4919d0 pa=
- L2 `lsq_sendfrag`：va=4919d0 pa=
- L2 `tlb_translate`：va=4919d0 pa=
- L3 `resp`：va=779d0 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=290851330）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1/A06-F2-W5/seed1/prop_evt.txt.gz` | `56aa6b7aeada418b3ff77f830f14f217256c496267c6a31c23c69dcdd7f845bf` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1/A06-F2-W5/seed1/stats.txt` | `d7ed6ebf0f5e6a4bebe445abc0a333f9b74b84f60a5035c1f031614c474d80da` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1/A06-F2-W5/seed1/run.out` | `6e474052c679cdb2e389d2a28103ec55007a1aee7a080b530ae2a17fc87d8a56` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1/A06-F2-W5/seed1/run.err` | `79c4fee84c75e876e776c69f1f0af49807527b7520b0353150d609626ace8fea` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1/A06-F2-W5/chain_report.json` | `ddee3bb9602556d9d33d01fc80168814709d2b247d66fc767b1651bb7723f309` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W5_s1/manifest.json` | `809e57169d328ef793d24567c502a82577fdf460086cd823e6d3575c659a8d2f` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

