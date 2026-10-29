# A04-F2-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W3` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 305224920, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493070, new_addr=0x4930b0, old_size=16, new_size=16, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=16, be_ones=16, be_subst=0, submodel=a04a, old_be=0xffff, new_be=0xffff, object_id=arr, object_base=0x493000, object_size=512, source_offset=112, target_offset=176 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1 --cells A04-F2-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 1200` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=305224920，request_id=，corr=origin，注入前地址 `before=493070`，注入后地址 `after=4930b0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 305224920, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x493070, new_addr=0x4930b0, old_size=16, new_size=16, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=16, be_ones=16, be_subst=0, submodel=a04a, old_be=0xffff, new_be=0xffff, object_id=arr, object_base=0x493000, object_size=512, source_offset=112, target_offset=176
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493070` → `4930b0`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `16`
- `new_size` = `16`
- `old_be` = `0xffff`
- `new_be` = `0xffff`
- `submodel` = `a04a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 305224920 |  | 493070 |  |  |  | origin |
| addr_form | 2 | 1 | 305224920 |  | 4930b0 |  |  |  | origin |
| lsq_push | 3 | 2 | 305224920 |  | 4930b0 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 305224920 | 1348215 | 4930b0 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 305224920 | 1348215 | 4930b0 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 305224920 | 1348215 | 4930b0 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 305224920 | 1348215 | 4930b0 |  |  |  | seq_primary |
| resp | 8 | 7 | 305225690 | 1348215 | 790b0 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 305225690 | 1348215 | 4930b0 | 790b0 |  |  | seq_primary |
| taint_reg | 10 | 9 | 305225690 | 1348215 | 790b0 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 305227615 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 305228000 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 305228770 |  |  |  |  |  | taint_prop |
| chain_end | 14 | 13 | 476273105 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4930b0 pa=
- L2 `lsq_sendfrag`：va=4930b0 pa=
- L2 `tlb_translate`：va=4930b0 pa=
- L3 `resp`：va=790b0 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=14。
- 事件数：本 seed 流共 14 条，其中 fault_id=1 链 14 条；最后一条为 `chain_end`（event_id=14, tick=476273105）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`chain_end`，event_id=14，parent_event_id=13，tick=476273105，detection_layer=L5，outcome=errant_commit_seen，contained=1，corr=none。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `full`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1/A04-F2-W3/seed1/prop_evt.txt.gz` | `cc9cf75734f13d85eb5ebcf1eaa9c25bcb08ee724e19fdda5e53ca0701b16049` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1/A04-F2-W3/seed1/stats.txt` | `98ac2dff168ad74a3dc817c85bd645dfa62ee10b8ae46880173fb4c7a6a2e689` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1/A04-F2-W3/seed1/run.out` | `9962fec7e2d3279f5795826f8bc360c5a19471b8c6a8747b3db7c2e520bf4882` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1/A04-F2-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1/A04-F2-W3/chain_report.json` | `fc22771c084e6696d8143d1e7461fbedc1125d12289fd3c671c8c912e42a09a9` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W3_s1/manifest.json` | `f57325e9d377bdbd4ea7f9c88cefa126d953da27ebbaac3449083c2c7edf1fd6` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

