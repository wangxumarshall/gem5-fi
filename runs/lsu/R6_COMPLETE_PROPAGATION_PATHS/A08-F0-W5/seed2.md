# A08-F0-W5 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F0-W5` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F0 |
| 负载 | W5 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 80080, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=80080, dyn_inst_seq=5, request_id=5, isLoad=1, load_seq=5, store_seq=0, load_old_ea=0x7ffffefdd0, load_new_ea=0x7ffffefdd0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2 --cells A08-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=18395685，request_id=，corr=origin，注入前地址 `before=49697c`，注入后地址 `after=496978`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 80080, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=80080, dyn_inst_seq=5, request_id=5, isLoad=1, load_seq=5, store_seq=0, load_old_ea=0x7ffffefdd0, load_new_ea=0x7ffffefdd0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
Tick: 197890, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=197890, dyn_inst_seq=48, request_id=48, isLoad=1, load_seq=48, store_seq=0, load_old_ea=0x7ffffefde8, load_new_ea=0x7ffffefde8, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
Tick: 197890, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=197890, dyn_inst_seq=44, request_id=44, isLoad=0, load_seq=0, store_seq=44, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefda0, size=8, page_ok=0, decline_reason=store_after_load
Tick: 204820, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=204820, dyn_inst_seq=48, request_id=48, isLoad=1, load_seq=48, store_seq=0, load_old_ea=0x7ffffefde8, load_new_ea=0x7ffffefde8, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
... (1371 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`49697c` → `496978`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x7ffffefdd0`
- `new_ea` = `0x7ffffefdd0`
- `submodel` = `a08b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → squash_discarded → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，squash_discarded=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 18395685 |  | 49697c |  |  |  | origin |
| addr_form | 2 | 1 | 18395685 |  | 496978 |  |  |  | origin |
| lsq_push | 3 | 2 | 18395685 |  | 496978 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 18395685 | 15136 | 496978 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 18395685 | 15136 | 496978 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 18395685 | 15136 | 496978 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 18395685 | 15136 | 496978 |  |  |  | seq_primary |
| resp | 8 | 7 | 18396455 | 15136 | 7c978 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 18396455 | 15136 | 496978 | 7c978 |  |  | seq_primary |
| taint_reg | 10 | 9 | 18396455 | 15136 | 7c978 |  |  |  | seq_primary |
| squash_discarded | 11 | 10 | 18496940 | 15136 |  |  | L4 | contained | seq_primary |
| chain_end | 12 | 11 | 19255005 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=496978 pa=
- L2 `lsq_sendfrag`：va=496978 pa=
- L2 `tlb_translate`：va=496978 pa=
- L3 `resp`：va=7c978 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=12。
- 事件数：本 seed 流共 12 条，其中 fault_id=1 链 12 条；最后一条为 `chain_end`（event_id=12, tick=19255005）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2/A08-F0-W5/seed2/prop_evt.txt.gz` | `cea67eb6d008f5084e6d60708729020a0b77c5697ba95978c7776da6c9230a11` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2/A08-F0-W5/seed2/stats.txt` | `57751b354dab739a0e06dedd187d5debbf4a29dfb76932b9912722a3d75e157f` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2/A08-F0-W5/seed2/run.out` | `75fb21474fdf1005d09e6728b71ca36cef60cd989d2a03e2226dddb411411045` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2/A08-F0-W5/seed2/run.err` | `79c4fee84c75e876e776c69f1f0af49807527b7520b0353150d609626ace8fea` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2/A08-F0-W5/chain_report.json` | `c380ee673d3d1fe7406f89b6018532e97df8a22e7aefbf5651a433223c3518b7` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F0-W5_s2/manifest.json` | `f0f1843cddb83e5ea4dc54e8f3fc82e8a37f313366f8db21be9a63d9657e0c5a` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

