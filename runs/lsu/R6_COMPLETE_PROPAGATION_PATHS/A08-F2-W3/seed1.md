# A08-F2-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F2-W3` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd30, size=8, page_ok=0, decline_reason=store_before_load |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1 --cells A08-F2-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 3600` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=3964502080，request_id=，corr=origin，注入前地址 `before=493240`，注入后地址 `after=493240`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd30, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141295, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141295, dyn_inst_seq=19, request_id=19, isLoad=0, load_seq=0, store_seq=19, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd38, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141680, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141680, dyn_inst_seq=23, request_id=23, isLoad=0, load_seq=0, store_seq=23, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd40, size=8, page_ok=0, decline_reason=store_before_load
Tick: 142065, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=142065, dyn_inst_seq=24, request_id=24, isLoad=0, load_seq=0, store_seq=24, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd48, size=8, page_ok=0, decline_reason=store_before_load
... (1374058 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493240` → `493240`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x0`
- `new_ea` = `0x0`
- `submodel` = `a08a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 3964502080 |  | 493240 |  |  |  | origin |
| addr_form | 2 | 1 | 3964502080 |  | 493240 |  |  |  | origin |
| lsq_push | 3 | 2 | 3964502080 |  | 493240 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 3964502080 | 18312178 | 493240 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 3964502080 | 18312178 | 493240 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 3964502080 | 18312178 | 493240 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 3964502080 |  | 493240 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 3964503620 |  |  | 79240 |  |  | seq_primary |
| resp | 9 | 8 | 3964504390 | 18312178 | 79240 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 3964504390 | 18312178 | 79240 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 3964504390 |  | 493240 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 7017584805 | 18312178 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 7017584805 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493240 pa=
- L2 `lsq_sendfrag`：va=493240 pa=
- L2 `tlb_translate`：va=493240 pa=
- L3 `resp`：va=79240 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=7017584805）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`store_not_retired`，event_id=12，parent_event_id=11，tick=7017584805，detection_layer=L4，outcome=contained，contained=1，corr=taint_prop。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `detected_contained`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1/A08-F2-W3/seed1/prop_evt.txt.gz` | `17c450273a5241f6907a6e93c784699b4fa0ce7f9b6a5b08a494bcd63ffe1f50` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1/A08-F2-W3/seed1/stats.txt` | `f99353ae9864940d82c00adb36cf06484aea0d3c790a6ae711ffb78073b2fcaa` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1/A08-F2-W3/seed1/run.out` | `a091760ef2558edce3641d7a372ef3569b6408c71d3e1623eb37904133c6c4d5` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1/A08-F2-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1/A08-F2-W3/chain_report.json` | `0173561a3900ade896c94c1e35099672fca874baf0fcad774639869958153cc5` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s1/manifest.json` | `b31dd326f008deefcad096fa5a9cfa248447dfa2940504939d4147e5c03f0891` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

