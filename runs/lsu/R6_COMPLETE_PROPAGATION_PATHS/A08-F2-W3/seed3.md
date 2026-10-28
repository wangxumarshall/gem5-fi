# A08-F2-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F2-W3` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd30, size=8, page_ok=0, decline_reason=store_before_load |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3 --cells A08-F2-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 3600` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=5241184410，request_id=，corr=origin，注入前地址 `before=493350`，注入后地址 `after=493350`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd30, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141295, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141295, dyn_inst_seq=19, request_id=19, isLoad=0, load_seq=0, store_seq=19, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd38, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141680, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141680, dyn_inst_seq=23, request_id=23, isLoad=0, load_seq=0, store_seq=23, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd40, size=8, page_ok=0, decline_reason=store_before_load
Tick: 142065, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=142065, dyn_inst_seq=24, request_id=24, isLoad=0, load_seq=0, store_seq=24, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd48, size=8, page_ok=0, decline_reason=store_before_load
... (1818320 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493350` → `493350`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x0`
- `new_ea` = `0x0`
- `submodel` = `a08a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 5241184410 |  | 493350 |  |  |  | origin |
| addr_form | 2 | 1 | 5241184410 |  | 493350 |  |  |  | origin |
| lsq_push | 3 | 2 | 5241184410 |  | 493350 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 5241184410 | 24230587 | 493350 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 5241184410 | 24230587 | 493350 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 5241184410 | 24230587 | 493350 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 5241184410 |  | 493350 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 5241185950 |  |  | 79350 |  |  | seq_primary |
| resp | 9 | 8 | 5241186720 | 24230587 | 79350 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 5241186720 | 24230587 | 79350 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 5241186720 |  | 493350 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 7017584805 | 24230587 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 7017584805 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493350 pa=
- L2 `lsq_sendfrag`：va=493350 pa=
- L2 `tlb_translate`：va=493350 pa=
- L3 `resp`：va=79350 pa=（响应回到 LSQ）
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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3/A08-F2-W3/seed3/prop_evt.txt.gz` | `af10c7ffc3eddc64efa33e4ddcc48704f9e402d5ba4d6ef3ca5228e8a34c1c05` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3/A08-F2-W3/seed3/stats.txt` | `1afc6a52f188e5702900219f141fce49b726237c52fab4b370f64a111aa6f55c` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3/A08-F2-W3/seed3/run.out` | `aa587858e8fe4f2297780fb1f561ca660e3e8fa74ac89b021f87181a99e68f04` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3/A08-F2-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3/A08-F2-W3/chain_report.json` | `2c8e331ee88d522b6a8ded82cff73c752db365d2318e04a32f9eb9d3f8931391` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s3/manifest.json` | `991a15ea06d8a3814fd49c8958e0ec265a0820d9d61aff1754e67d163c0dd6ce` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

