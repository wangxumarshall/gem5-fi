# A07-F0-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F0-W3` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3 --cells A07-F0-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=15229830，request_id=，corr=origin，注入前地址 `before=15229830`，注入后地址 `after=15230215`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 15229830, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=12058, ready_tick=15229830, delayed_tick=15230215, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 15230215, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=12058, consumed=1, squashed=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`15229830` → `15230215`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → lsq_push → mem_req → lsq_sendfrag → tlb_translate → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → chain_end`。
按证据层映射：inj=L0，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 15229830 |  |  |  |  |  | origin |
| lsq_push | 2 | 0 | 15230215 |  | 4990f8 |  |  |  | seq_primary |
| mem_req | 3 | 2 | 15230215 | 12058 | 4990f8 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 15230215 | 12058 | 4990f8 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 15230215 | 12058 | 4990f8 |  |  |  | seq_primary |
| mem_req | 6 | 5 | 15230215 | 12058 | 499100 |  |  |  | seq_primary |
| lsq_sendfrag | 7 | 6 | 15230215 | 12058 | 499100 |  |  |  | seq_primary |
| tlb_translate | 8 | 7 | 15230215 | 12058 | 499100 |  |  |  | seq_primary |
| lq_read | 9 | 8 | 15230215 | 12058 | 4990f8 |  |  |  | seq_primary |
| resp | 10 | 9 | 15316070 |  | 0 |  |  |  | seq_primary |
| lq_complete | 11 | 10 | 15316070 | 0 | 4990f8 | 0 |  |  | seq_primary |
| taint_reg | 12 | 11 | 15316070 |  | 0 |  |  |  | seq_primary |
| errant_commit | 13 | 12 | 15316840 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 14 | 12 | 15317995 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 15318765 |  |  |  |  |  | taint_prop |
| chain_end | 16 | 15 | 19928370 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4990f8 pa=
- L2 `lsq_sendfrag`：va=4990f8 pa=
- L2 `tlb_translate`：va=4990f8 pa=
- L2 `mem_req`：va=499100 pa=
- L2 `lsq_sendfrag`：va=499100 pa=
- L2 `tlb_translate`：va=499100 pa=
- L3 `resp`：va=0 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=16。
- 事件数：本 seed 流共 16 条，其中 fault_id=1 链 16 条；最后一条为 `chain_end`（event_id=16, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3/A07-F0-W3/seed3/prop_evt.txt.gz` | `45b2368700d8574e12b977335ee8918b0a5eb8941718ed03b2f0d3cff26f9398` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3/A07-F0-W3/seed3/stats.txt` | `b9bece259a7c73357580577464b9438a39dd8d994c0766757edb8586c4ac020f` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3/A07-F0-W3/seed3/run.out` | `83dd998c3512cb765a32f1cbcbeaa4724dde9e4fa4c38845b80f8db59f0d37d7` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3/A07-F0-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3/A07-F0-W3/chain_report.json` | `147896dc6e1b8aff9792fef2ea7f4393930f5b1b89488cac37943f032214b28a` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s3/manifest.json` | `8389d806533d085aef61d9cd8fd259a76261c7818a4c941ed5a96db67312b3e7` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

