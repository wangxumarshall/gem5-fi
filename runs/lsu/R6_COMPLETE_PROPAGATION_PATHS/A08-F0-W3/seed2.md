# A08-F0-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F0-W3` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 80080, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=80080, dyn_inst_seq=5, request_id=5, isLoad=1, load_seq=5, store_seq=0, load_old_ea=0x7ffffefdd0, load_new_ea=0x7ffffefdd0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2 --cells A08-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=19119870，request_id=，corr=origin，注入前地址 `before=4982dc`，注入后地址 `after=4982d8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 80080, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=80080, dyn_inst_seq=5, request_id=5, isLoad=1, load_seq=5, store_seq=0, load_old_ea=0x7ffffefdd0, load_new_ea=0x7ffffefdd0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
Tick: 197890, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=197890, dyn_inst_seq=48, request_id=48, isLoad=1, load_seq=48, store_seq=0, load_old_ea=0x7ffffefde8, load_new_ea=0x7ffffefde8, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
Tick: 197890, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=197890, dyn_inst_seq=44, request_id=44, isLoad=0, load_seq=0, store_seq=44, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefda0, size=8, page_ok=0, decline_reason=store_after_load
Tick: 204820, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=204820, dyn_inst_seq=48, request_id=48, isLoad=1, load_seq=48, store_seq=0, load_old_ea=0x7ffffefde8, load_new_ea=0x7ffffefde8, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
... (1613 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4982dc` → `4982d8`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x7ffffefdd0`
- `new_ea` = `0x7ffffefdd0`
- `submodel` = `a08b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → squash_discarded → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，squash_discarded=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 19119870 |  | 4982dc |  |  |  | origin |
| addr_form | 2 | 1 | 19119870 |  | 4982d8 |  |  |  | origin |
| lsq_push | 3 | 2 | 19119870 |  | 4982d8 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 19119870 | 16751 | 4982d8 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 19119870 | 16751 | 4982d8 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 19119870 | 16751 | 4982d8 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 19119870 | 16751 | 4982d8 |  |  |  | seq_primary |
| resp | 8 | 7 | 19120640 | 16751 | 7e2d8 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 19120640 | 16751 | 4982d8 | 7e2d8 |  |  | seq_primary |
| taint_reg | 10 | 9 | 19120640 | 16751 | 7e2d8 |  |  |  | seq_primary |
| squash_discarded | 11 | 10 | 19196100 | 16751 |  |  | L4 | contained | seq_primary |
| chain_end | 12 | 11 | 19954165 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4982d8 pa=
- L2 `lsq_sendfrag`：va=4982d8 pa=
- L2 `tlb_translate`：va=4982d8 pa=
- L3 `resp`：va=7e2d8 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=12。
- 事件数：本 seed 流共 12 条，其中 fault_id=1 链 12 条；最后一条为 `chain_end`（event_id=12, tick=19954165）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2/A08-F0-W3/seed2/prop_evt.txt.gz` | `13e73a2fcad731c2788216287672ee378e982f01a68b30ed59c744e1fca56e86` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2/A08-F0-W3/seed2/stats.txt` | `6d7f7671f62da2aaa462d7379f88e6695a8343f49226d2759f43201690aacd8b` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2/A08-F0-W3/seed2/run.out` | `5a0cfa03130526e8e122210e0171b927847f91efaf4ee8112a458d7427b5a1ce` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2/A08-F0-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2/A08-F0-W3/chain_report.json` | `5d61925cc0f4aff9a02749c17b40c046136b1fa3cd995aaa161d1c1f1b7bdbaf` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W3_s2/manifest.json` | `8883fa05e76c65fdaa8ea9312579487d186b1c5d91e6679e05751d7de6f95f09` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

