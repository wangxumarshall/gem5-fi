# A07-F4-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F4-W3` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F4 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1 --cells A07-F4-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=149296455，request_id=，corr=origin，注入前地址 `before=149296455`，注入后地址 `after=149296840`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 149296455, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=625513, ready_tick=149296455, delayed_tick=149296840, delay_cycles=1, isLoad=0, isStore=1, faults_injected: 1
Tick: 149296840, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=625513, consumed=1, squashed=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`149296455` → `149296840`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 149296455 |  |  |  |  |  | origin |
| lsq_push | 2 | 0 | 149296840 |  | 4933d8 |  |  |  | seq_primary |
| mem_req | 3 | 2 | 149296840 | 625513 | 4933d8 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 149296840 | 625513 | 4933d8 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 149296840 | 625513 | 4933d8 |  |  |  | seq_primary |
| sq_execute | 6 | 5 | 149296840 |  | 4933d8 |  |  |  | seq_primary |
| sq_writeback | 7 | 6 | 149298380 |  |  | 793d8 |  |  | seq_primary |
| resp | 8 | 7 | 149299150 | 625513 | 793d8 |  |  |  | seq_primary |
| taint_reg | 9 | 8 | 149299150 | 625513 | 793d8 |  |  |  | seq_primary |
| sq_complete | 10 | 9 | 149299150 |  | 4933d8 |  |  |  | seq_primary |
| store_not_retired | 11 | 10 | 214469640 | 625513 |  |  | L4 | contained | taint_prop |
| chain_end | 12 | 11 | 214469640 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4933d8 pa=
- L2 `lsq_sendfrag`：va=4933d8 pa=
- L2 `tlb_translate`：va=4933d8 pa=
- L3 `resp`：va=793d8 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=12。
- 事件数：本 seed 流共 12 条，其中 fault_id=1 链 12 条；最后一条为 `chain_end`（event_id=12, tick=214469640）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1/A07-F4-W3/seed1/prop_evt.txt.gz` | `4d058daf6d16283fad45c51965f488403917c3f14a062dc04c14a9cb862a0398` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1/A07-F4-W3/seed1/stats.txt` | `5e95bafd96bdad8dd1b6ebb84385e972230db9be5a65a50e0ff940a1be8b029f` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1/A07-F4-W3/seed1/run.out` | `8cb5f1e8e351e6ccbfca1915c7d9ee9978274034ee55a56b1903760ca0b7035c` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1/A07-F4-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1/A07-F4-W3/chain_report.json` | `eb20578bb8bf63248b2df4a4c57e4a779739c3d0e38d3d4db68ffdda8f9c6b17` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s1/manifest.json` | `d40cf3a557bd141b8339cce29f062e0b0ce24d45ba724d7fd481028334f642c2` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

