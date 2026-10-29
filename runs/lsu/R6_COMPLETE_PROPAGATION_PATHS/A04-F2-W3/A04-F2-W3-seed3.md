# A04-F2-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W3` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 398180475, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493188, new_addr=0x493140, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=arr, object_base=0x493000, object_size=512, source_offset=392, target_offset=320 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3 --cells A04-F2-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 1200` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=398180475，request_id=，corr=origin，注入前地址 `before=493188`，注入后地址 `after=493140`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 398180475, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493188, new_addr=0x493140, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=arr, object_base=0x493000, object_size=512, source_offset=392, target_offset=320
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493188` → `493140`（来自 inj/addr_form 节点，本 seed 自己的值）。
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
| inj | 1 |  | 398180475 |  | 493188 |  |  |  | origin |
| addr_form | 2 | 1 | 398180475 |  | 493140 |  |  |  | origin |
| lsq_push | 3 | 2 | 398180475 |  | 493140 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 398180475 | 1779154 | 493140 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 398180475 | 1779154 | 493140 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 398180475 | 1779154 | 493140 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 398180475 |  | 493140 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 398182015 |  |  | 79140 |  |  | seq_primary |
| resp | 9 | 8 | 398182785 | 1779154 | 79140 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 398182785 | 1779154 | 79140 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 398182785 |  | 493140 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 476273105 | 1779154 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 476273105 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493140 pa=
- L2 `lsq_sendfrag`：va=493140 pa=
- L2 `tlb_translate`：va=493140 pa=
- L3 `resp`：va=79140 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=476273105）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`store_not_retired`，event_id=12，parent_event_id=11，tick=476273105，detection_layer=L4，outcome=contained，contained=1，corr=taint_prop。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `detected_contained`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3/A04-F2-W3/seed3/prop_evt.txt.gz` | `07ec8d1a83320b57e5d60517a409f52653e99f6686148ad46a2e8e82ea83a007` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3/A04-F2-W3/seed3/stats.txt` | `774226d323aff3f4b2ff5e5e511d1c08d4907fc7cffafef6bbab23278850fb73` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3/A04-F2-W3/seed3/run.out` | `db14f8f7af812179ff38d694555c57113bd0bcf0a2e37d4c3cd0dec9cfb99bdd` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3/A04-F2-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3/A04-F2-W3/chain_report.json` | `1d08a49406bc853b4c0416b0fb7bdfa273e73816323fcf64f70a4a0a123c9b46` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s3/manifest.json` | `abd6873cc0fb99f65c88089838bc17f286a00d10ae97eb8efd7de4f219db6125` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

