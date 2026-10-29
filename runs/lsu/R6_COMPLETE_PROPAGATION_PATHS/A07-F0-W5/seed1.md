# A07-F0-W5 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F0-W5` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F0 |
| 负载 | W5 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1 --cells A07-F0-W5 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=4704315，request_id=，corr=origin，注入前地址 `before=4704315`，注入后地址 `after=4704700`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 4704315, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=3244, ready_tick=4704315, delayed_tick=4704700, delay_cycles=1, isLoad=0, isStore=1, faults_injected: 1
Tick: 4704700, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=3244, consumed=1, squashed=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4704315` → `4704700`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 4704315 |  |  |  |  |  | origin |
| lsq_push | 2 | 0 | 4704700 |  | 496908 |  |  |  | seq_primary |
| mem_req | 3 | 2 | 4704700 | 3244 | 496908 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 4704700 | 3244 | 496908 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 4704700 | 3244 | 496908 |  |  |  | seq_primary |
| sq_execute | 6 | 5 | 4704700 |  | 496908 |  |  |  | seq_primary |
| sq_writeback | 7 | 6 | 4706240 |  |  | 7c908 |  |  | seq_primary |
| resp | 8 | 7 | 4762450 | 3244 | 7c908 |  |  |  | seq_primary |
| taint_reg | 9 | 8 | 4762450 | 3244 | 7c908 |  |  |  | seq_primary |
| sq_complete | 10 | 9 | 4762450 |  | 496908 |  |  |  | seq_primary |
| store_not_retired | 11 | 10 | 19229210 | 3244 |  |  | L4 | contained | taint_prop |
| chain_end | 12 | 11 | 19229210 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=496908 pa=
- L2 `lsq_sendfrag`：va=496908 pa=
- L2 `tlb_translate`：va=496908 pa=
- L3 `resp`：va=7c908 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=12。
- 事件数：本 seed 流共 12 条，其中 fault_id=1 链 12 条；最后一条为 `chain_end`（event_id=12, tick=19229210）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1/A07-F0-W5/seed1/prop_evt.txt.gz` | `811ef0c4f8274c307e1c18670aa7ec44ffdf8116782316effdbf5045d025683f` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1/A07-F0-W5/seed1/stats.txt` | `c3375ab46bb5a68a0f516dcd2d7c407ee8784df6a42f166d596746ffc6e93f59` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1/A07-F0-W5/seed1/run.out` | `37c4df2d0e910ea28d0d08ec2df8e40d4e87ee5e2f0e8e9c296ac0458a3b2be2` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1/A07-F0-W5/seed1/run.err` | `79c4fee84c75e876e776c69f1f0af49807527b7520b0353150d609626ace8fea` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1/A07-F0-W5/chain_report.json` | `d8f34f6c17ddf7081d1c66e16fd8a6252c7291554904323092f2a319de7da1f6` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s1/manifest.json` | `158e7c9fb84fa6e86ce8d5ff53f35e450a0298093f93615677a9c160c27d8953` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

