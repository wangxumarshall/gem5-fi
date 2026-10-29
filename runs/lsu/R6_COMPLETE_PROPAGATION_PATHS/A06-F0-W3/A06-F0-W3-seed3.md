# A06-F0-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A06-F0-W3` |
| 模型 | A06（AGU 访问尺寸/掩码） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 18227440, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x7ffffefaa0, new_addr=0x7ffffefaa0, old_size=8, new_size=4, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3 --cells A06-F0-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=18227440，request_id=，corr=origin，注入前地址 `before=7ffffefaa0`，注入后地址 `after=7ffffefaa0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 18227440, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x7ffffefaa0, new_addr=0x7ffffefaa0, old_size=8, new_size=4, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefaa0` → `7ffffefaa0`（来自 inj/addr_form 节点，本 seed 自己的值）。
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
| inj | 1 |  | 18227440 |  | 7ffffefaa0 |  |  |  | origin |
| addr_form | 2 | 1 | 18227440 |  | 7ffffefaa0 |  |  |  | origin |
| lsq_push | 3 | 2 | 18227440 |  | 7ffffefaa0 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 18227440 | 16363 | 7ffffefaa0 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 18227440 | 16363 | 7ffffefaa0 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 18227440 | 16363 | 7ffffefaa0 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 18227440 |  | 7ffffefaa0 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 18231675 |  |  | 7faa0 |  |  | seq_primary |
| resp | 9 | 8 | 18295201 | 16363 | 7faa0 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 18295201 | 16363 | 7faa0 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 18295201 |  | 7ffffefaa0 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 19928370 | 16363 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 19928370 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ffffefaa0 pa=
- L2 `lsq_sendfrag`：va=7ffffefaa0 pa=
- L2 `tlb_translate`：va=7ffffefaa0 pa=
- L3 `resp`：va=7faa0 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3/A06-F0-W3/seed3/prop_evt.txt.gz` | `3f7877c41dec078a4706f82178ed60181476c39106b38842de04bf47b42c5c5b` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3/A06-F0-W3/seed3/stats.txt` | `4e5084ffc904ed831333ef06ef800a7b15f0c81f6b4c5dce04765542ade3f4b5` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3/A06-F0-W3/seed3/run.out` | `83f451c609ac0faccb710ef404699f385e874ca5fc3ec1963a6cc9a5fc465b71` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3/A06-F0-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3/A06-F0-W3/chain_report.json` | `c40afc02b235301930851ff63a70c9ec91c2c52beb5653e939765c42f36075a4` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W3_s3/manifest.json` | `92661d28d94fe90741edf57b272a106d5a82427af20a61d2a270fa25d823de78` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

