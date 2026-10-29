# A01-F2-W9 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F2-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F2 |
| 负载 | W9 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2 --cells A01-F2-W9 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 900` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=150760225，request_id=，corr=origin，注入前地址 `before=49d5e0`，注入后地址 `after=4955e0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 150760225, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x49d5e0, new_vaddr=0x4955e0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`49d5e0` → `4955e0`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 150760225 |  | 49d5e0 |  |  |  | origin |
| addr_form | 2 | 1 | 150760225 |  | 4955e0 |  |  |  | origin |
| mem_req | 3 | 2 | 150760225 | 545815 | 4955e0 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 150760225 | 545815 | 4955e0 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 150760225 | 545815 | 4955e0 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 150760225 | 545815 | 4955e0 |  |  |  | seq_primary |
| resp | 7 | 6 | 150760995 | 545815 | 7b5e0 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 150760995 | 545815 | 4955e0 | 7b5e0 |  |  | seq_primary |
| taint_reg | 9 | 8 | 150760995 | 545815 | 7b5e0 |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 150761765 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 150762150 |  |  |  |  |  | taint_prop |
| consumer | 12 | 11 | 150763690 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 150764075 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 150764460 |  |  |  |  |  | taint_prop |
| consumer | 15 | 13 | 150764460 |  |  |  |  |  | taint_prop |
| consumer | 16 | 13 | 150764460 |  |  |  |  |  | taint_prop |
| chain_end | 17 | 16 | 325381980 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4955e0 pa=
- L2 `lsq_sendfrag`：va=4955e0 pa=
- L2 `tlb_translate`：va=4955e0 pa=
- L3 `resp`：va=7b5e0 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=17。
- 事件数：本 seed 流共 17 条，其中 fault_id=1 链 17 条；最后一条为 `chain_end`（event_id=17, tick=325381980）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`chain_end`，event_id=17，parent_event_id=16，tick=325381980，detection_layer=L5，outcome=errant_commit_seen，contained=1，corr=none。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `full`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2/A01-F2-W9/seed2/prop_evt.txt.gz` | `f71d4a32134cd911074329befcbaece3d865d0e4f03540a38f2ebde7ac279065` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2/A01-F2-W9/seed2/stats.txt` | `26d968a06878e5fbd1883bc62165da48a11bc908de74ea5b152b4da1bcb6715a` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2/A01-F2-W9/seed2/run.out` | `0d97e08a6808c69163aa3d92b0ede2c31bba96d3a4375cdf41a9ac79fc94854e` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2/A01-F2-W9/seed2/run.err` | `70eea0776f34f13af666fe542bab517beab9a8b81989f41e1d73d96763cfdc80` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2/A01-F2-W9/chain_report.json` | `73d0d4f457cfed9ad1c319817a57e4d0c02b581ea9d2467967c3f1c2fd2138af` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s2/manifest.json` | `f51db45908bc6e1f097bc0ff3f177530768e7146c4baa2c8710978b31d33ad58` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

