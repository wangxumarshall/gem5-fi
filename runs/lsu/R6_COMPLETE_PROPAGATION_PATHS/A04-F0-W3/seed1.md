# A04-F0-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F0-W3` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 15931685, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493060, new_addr=0x493190, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=arr, object_base=0x493000, object_size=512, source_offset=96, target_offset=400 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1 --cells A04-F0-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=15931685，request_id=，corr=origin，注入前地址 `before=493060`，注入后地址 `after=493190`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 15931685, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493060, new_addr=0x493190, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=arr, object_base=0x493000, object_size=512, source_offset=96, target_offset=400
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493060` → `493190`（来自 inj/addr_form 节点，本 seed 自己的值）。
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
| inj | 1 |  | 15931685 |  | 493060 |  |  |  | origin |
| addr_form | 2 | 1 | 15931685 |  | 493190 |  |  |  | origin |
| lsq_push | 3 | 2 | 15931685 |  | 493190 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 15931685 | 12321 | 493190 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 15931685 | 12321 | 493190 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 15931685 | 12321 | 493190 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 15931685 |  | 493190 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 15933225 |  |  | 79190 |  |  | seq_primary |
| resp | 9 | 8 | 15987510 | 12321 | 79190 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 15987510 | 12321 | 79190 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 15987510 |  | 493190 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 20019615 | 12321 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 20019615 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493190 pa=
- L2 `lsq_sendfrag`：va=493190 pa=
- L2 `tlb_translate`：va=493190 pa=
- L3 `resp`：va=79190 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`SDC`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=20019615）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1/A04-F0-W3/seed1/prop_evt.txt.gz` | `163792f8a567d9d62325af2be614ae5028e82cb54d6d51ecc0417c3563e7be28` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1/A04-F0-W3/seed1/stats.txt` | `39010aa70ecc0ffd9253f283fbafcf9766b3a71dd8c29cf68e322daa7f8e899d` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1/A04-F0-W3/seed1/run.out` | `433d4ab9d4b6039d557ff8cd318d94b5c9862a949e9c412206890b83a103a4c4` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1/A04-F0-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1/A04-F0-W3/chain_report.json` | `1cc086e8c7253b0fc0c704a79c60b9e4b2a9a337d62847071a1d7d090f7c3d91` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s1/manifest.json` | `69264d86a6ad284612fc26d5e401939aedd0708a07597b11ed87f4e8eb3c70d8` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

