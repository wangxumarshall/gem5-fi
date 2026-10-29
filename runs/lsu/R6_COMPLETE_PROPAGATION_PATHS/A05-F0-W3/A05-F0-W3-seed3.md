# A05-F0-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A05-F0-W3` |
| 模型 | A05（AGU 操作数级寻址） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 197890, Site: lsq_pushRequest_PRE, mode=a05_prepost, old_addr=0x7ffffefde8, new_addr=0x7ffffefdf0, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a05d, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3 --cells A05-F0-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=197890，request_id=，corr=origin，注入前地址 `before=7ffffefde8`，注入后地址 `after=7ffffefdf0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 197890, Site: lsq_pushRequest_PRE, mode=a05_prepost, old_addr=0x7ffffefde8, new_addr=0x7ffffefdf0, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a05d, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefde8` → `7ffffefdf0`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a05d`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 197890 |  | 7ffffefde8 |  |  |  | origin |
| addr_form | 2 | 1 | 197890 |  | 7ffffefdf0 |  |  |  | origin |
| lsq_push | 3 | 2 | 197890 |  | 7ffffefdf0 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 197890 | 48 | 7ffffefdf0 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 197890 | 48 | 7ffffefdf0 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 197890 | 48 | 7ffffefdf0 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 197890 | 48 | 7ffffefdf0 |  |  |  | seq_primary |
| lq_read | 8 | 7 | 204820 | 48 | 7ffffefdf0 |  |  |  | seq_primary |
| resp | 9 | 8 | 205590 | 48 | 7fdf0 |  |  |  | seq_primary |
| lq_complete | 10 | 9 | 205590 | 48 | 7ffffefdf0 | 7fdf0 |  |  | seq_primary |
| taint_reg | 11 | 10 | 205590 | 48 | 7fdf0 |  |  |  | seq_primary |
| errant_commit | 12 | 11 | 206745 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 13 | 11 | 206745 |  |  |  |  |  | taint_prop |
| chain_end | 14 | 13 | 19722010 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ffffefdf0 pa=
- L2 `lsq_sendfrag`：va=7ffffefdf0 pa=
- L2 `tlb_translate`：va=7ffffefdf0 pa=
- L3 `resp`：va=7fdf0 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=14。
- 事件数：本 seed 流共 14 条，其中 fault_id=1 链 14 条；最后一条为 `chain_end`（event_id=14, tick=19722010）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3/A05-F0-W3/seed3/prop_evt.txt.gz` | `27a54b763b30ed7066a145ad22066323e1ded2c3f53b38a43d22c8b3cbac035e` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3/A05-F0-W3/seed3/stats.txt` | `4aa687345fa7d1c82dc310a0f0dcae32507f70963a7aeafabfe343481328cbe9` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3/A05-F0-W3/seed3/run.out` | `daf7e6b2acce7d93c6c7d22c8e3fd897d5f95a8c9e19f1df217ecddafc30ba38` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3/A05-F0-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3/A05-F0-W3/chain_report.json` | `5f16c8c3c0ee5814553861e03bbb95b48e4f2bfd391a6da6de609bb72286e60c` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s3/manifest.json` | `135f8a441230cec804081101ee565949758209a79f1f436c9c60ddd35ee190ff` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

