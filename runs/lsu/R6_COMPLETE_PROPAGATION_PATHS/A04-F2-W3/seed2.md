# A04-F2-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W3` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 140503055, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x490988, new_addr=0x4906ed, old_size=1, new_size=1, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=1, be_ones=1, be_subst=0, submodel=a04b, old_be=0x1, new_be=0x1, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2 --cells A04-F2-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=140503055，request_id=，corr=origin，注入前地址 `before=490988`，注入后地址 `after=4906ed`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140503055, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x490988, new_addr=0x4906ed, old_size=1, new_size=1, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=1, be_ones=1, be_subst=0, submodel=a04b, old_be=0x1, new_be=0x1, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`490988` → `4906ed`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `1`
- `new_size` = `1`
- `old_be` = `0x1`
- `new_be` = `0x1`
- `submodel` = `a04b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 140503055 |  | 490988 |  |  |  | origin |
| addr_form | 2 | 1 | 140503055 |  | 4906ed |  |  |  | origin |
| lsq_push | 3 | 2 | 140503055 |  | 4906ed |  |  |  | seq_primary |
| mem_req | 4 | 3 | 140503055 | 584773 | 4906ed |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 140503055 | 584773 | 4906ed |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 140503055 | 584773 | 4906ed |  |  |  | seq_primary |
| lq_read | 7 | 6 | 140503055 | 584773 | 4906ed |  |  |  | seq_primary |
| resp | 8 | 7 | 140503825 | 584773 | 766ed |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 140503825 | 584773 | 4906ed | 766ed |  |  | seq_primary |
| taint_reg | 10 | 9 | 140503825 | 584773 | 766ed |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 140504980 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 140504980 |  |  |  |  |  | taint_prop |
| chain_end | 13 | 12 | 214738755 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4906ed pa=
- L2 `lsq_sendfrag`：va=4906ed pa=
- L2 `tlb_translate`：va=4906ed pa=
- L3 `resp`：va=766ed pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=214738755）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2/A04-F2-W3/seed2/prop_evt.txt.gz` | `2bdaf3c00f7b50eb235f6bcabd3dc0dc6bdde348d19b6cf2b59fe567213b7fa2` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2/A04-F2-W3/seed2/stats.txt` | `1e5e44f5e47083b2a38f848b86c0efedd7ed915a0b6c2412519a4d3a3e3bd204` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2/A04-F2-W3/seed2/run.out` | `3bb7cbab3c254dbadeabd2de095c45f29ef1e68cdf4b165c5302575ef53fe9c6` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2/A04-F2-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2/A04-F2-W3/chain_report.json` | `bf944b106808b6366be74b9223ee2449a42e65327e228406946062f1d4411d3e` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W3_s2/manifest.json` | `6a64fe65e9195f4f1f4be0697f264ca3b28a2335ac49ed50ab84dba1ff27b82c` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

