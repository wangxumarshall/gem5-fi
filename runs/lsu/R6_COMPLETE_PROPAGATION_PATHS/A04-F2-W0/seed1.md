# A04-F2-W0 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W0 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 313465845, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491b40, new_addr=0x491a40, old_size=16, new_size=16, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=16, be_ones=16, be_subst=0, submodel=a04a, old_be=0xffff, new_be=0xffff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=416, target_offset=160 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1 --cells A04-F2-W0 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 1200` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=313465845，request_id=，corr=origin，注入前地址 `before=491b40`，注入后地址 `after=491a40`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 313465845, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491b40, new_addr=0x491a40, old_size=16, new_size=16, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=16, be_ones=16, be_subst=0, submodel=a04a, old_be=0xffff, new_be=0xffff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=416, target_offset=160
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491b40` → `491a40`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `16`
- `new_size` = `16`
- `old_be` = `0xffff`
- `new_be` = `0xffff`
- `submodel` = `a04a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 313465845 |  | 491b40 |  |  |  | origin |
| addr_form | 2 | 1 | 313465845 |  | 491a40 |  |  |  | origin |
| lsq_push | 3 | 2 | 313465845 |  | 491a40 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 313465845 | 987897 | 491a40 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 313465845 | 987897 | 491a40 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 313465845 | 987897 | 491a40 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 313465845 | 987897 | 491a40 |  |  |  | seq_primary |
| resp | 8 | 7 | 313466615 | 987897 | 77a40 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 313466615 | 987897 | 491a40 | 77a40 |  |  | seq_primary |
| taint_reg | 10 | 9 | 313466615 | 987897 | 77a40 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 313467385 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 313470850 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 313477395 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 313478165 |  |  |  |  |  | taint_prop |
| chain_end | 15 | 14 | 488009060 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=491a40 pa=
- L2 `lsq_sendfrag`：va=491a40 pa=
- L2 `tlb_translate`：va=491a40 pa=
- L3 `resp`：va=77a40 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=15。
- 事件数：本 seed 流共 15 条，其中 fault_id=1 链 15 条；最后一条为 `chain_end`（event_id=15, tick=488009060）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`chain_end`，event_id=15，parent_event_id=14，tick=488009060，detection_layer=L5，outcome=errant_commit_seen，contained=1，corr=none。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `full`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1/A04-F2-W0/seed1/prop_evt.txt.gz` | `7a30121eca68ced71949aef296aa8f628024e0aa6efb0495b5dd7f33433c9c7c` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1/A04-F2-W0/seed1/stats.txt` | `f3d5d0bf4b690f398e75f49f3e4f16329a7f110e53f86cc841ecfb97a73234c8` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1/A04-F2-W0/seed1/run.out` | `95a3770475c9b686b8dfbab25885ee5d6dc4c01b8372170802036f758be0b285` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1/A04-F2-W0/seed1/run.err` | `00cfdbd7e5c6bed454738d0a109ea8335c4cf6c681f79e6d16a10f6cfaa16357` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1/A04-F2-W0/chain_report.json` | `eba684b4b847b7a3e551931d1428a2f84e0476275e5dffc6b959b1094c583131` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s1/manifest.json` | `7a58b1da57475ad6d34f5a47122af3f74c92ce8dc1ac7d4d699c166194c10774` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

