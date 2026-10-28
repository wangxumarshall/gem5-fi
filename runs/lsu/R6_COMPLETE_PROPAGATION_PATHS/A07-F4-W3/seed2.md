# A07-F4-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F4-W3` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F4 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2 --cells A07-F4-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=140503055，request_id=，corr=origin，注入前地址 `before=140503055`，注入后地址 `after=140503440`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140503055, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=584773, ready_tick=140503055, delayed_tick=140503440, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 140503440, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=584773, consumed=1, squashed=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`140503055` → `140503440`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → chain_end`。
按证据层映射：inj=L0，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 140503055 |  |  |  |  |  | origin |
| lsq_push | 2 | 0 | 140503440 |  | 490988 |  |  |  | seq_primary |
| mem_req | 3 | 2 | 140503440 | 584773 | 490988 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 140503440 | 584773 | 490988 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 140503440 | 584773 | 490988 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 140503440 | 584773 | 490988 |  |  |  | seq_primary |
| resp | 7 | 6 | 140504210 | 584773 | 76988 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 140504210 | 584773 | 490988 | 76988 |  |  | seq_primary |
| taint_reg | 9 | 8 | 140504210 | 584773 | 76988 |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 140504980 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 140505365 |  |  |  |  |  | taint_prop |
| chain_end | 12 | 11 | 214470025 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=490988 pa=
- L2 `lsq_sendfrag`：va=490988 pa=
- L2 `tlb_translate`：va=490988 pa=
- L3 `resp`：va=76988 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=12。
- 事件数：本 seed 流共 12 条，其中 fault_id=1 链 12 条；最后一条为 `chain_end`（event_id=12, tick=214470025）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2/A07-F4-W3/seed2/prop_evt.txt.gz` | `65e62b8ad3c3e132f09abbfc736a54bbff815eba71eae44f19a684082573940f` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2/A07-F4-W3/seed2/stats.txt` | `49f7ecfd378899317cb95b081d19537b7120cb7506a8616c3bed97312322c8cc` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2/A07-F4-W3/seed2/run.out` | `4b157f93d0e5b18592c7f8495736c65801bc34a5760cee70e44e4b14eabf5358` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2/A07-F4-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2/A07-F4-W3/chain_report.json` | `80136495f882e2090e5bc72fd8c5fc68b0a50f02738eb8ec8d9343684b3371ba` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s2/manifest.json` | `6a79235f22199b102df18b81cf69ba1d8b15e4dcc1b6045231d63676d1ab1cb0` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

