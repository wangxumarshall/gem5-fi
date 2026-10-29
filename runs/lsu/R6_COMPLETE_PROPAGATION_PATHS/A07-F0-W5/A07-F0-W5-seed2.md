# A07-F0-W5 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F0-W5` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F0 |
| 负载 | W5 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2 --cells A07-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=12373130，request_id=，corr=origin，注入前地址 `before=12373130`，注入后地址 `after=12373515`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 12373130, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=9588, ready_tick=12373130, delayed_tick=12373515, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 12373515, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=9588, consumed=1, squashed=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`12373130` → `12373515`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → squash_discarded → chain_end`。
按证据层映射：inj=L0，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，squash_discarded=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 12373130 |  |  |  |  |  | origin |
| lsq_push | 2 | 0 | 12373515 |  | 490a50 |  |  |  | seq_primary |
| mem_req | 3 | 2 | 12373515 | 9588 | 490a50 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 12373515 | 9588 | 490a50 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 12373515 | 9588 | 490a50 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 12373515 | 9588 | 490a50 |  |  |  | seq_primary |
| resp | 7 | 6 | 12374285 | 9588 | 76a50 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 12374285 | 9588 | 490a50 | 76a50 |  |  | seq_primary |
| taint_reg | 9 | 8 | 12374285 | 9588 | 76a50 |  |  |  | seq_primary |
| squash_discarded | 10 | 9 | 12374670 | 9588 |  |  | L4 | contained | seq_primary |
| chain_end | 11 | 10 | 19229210 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=490a50 pa=
- L2 `lsq_sendfrag`：va=490a50 pa=
- L2 `tlb_translate`：va=490a50 pa=
- L3 `resp`：va=76a50 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=11。
- 事件数：本 seed 流共 11 条，其中 fault_id=1 链 11 条；最后一条为 `chain_end`（event_id=11, tick=19229210）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2/A07-F0-W5/seed2/prop_evt.txt.gz` | `d6f87e912451209ebcba161e17104ce8a47c67d1a1a715dd859b2bcae7c7153e` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2/A07-F0-W5/seed2/stats.txt` | `c342e1a2af82cad1559bcb6ff1288ece9feff8770a8ce154a9490b9765b951df` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2/A07-F0-W5/seed2/run.out` | `6d5a6700b6879606afd5030f77cf6b5bd9c9ca443ba57bc6c864a55ac31a8756` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2/A07-F0-W5/seed2/run.err` | `79c4fee84c75e876e776c69f1f0af49807527b7520b0353150d609626ace8fea` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2/A07-F0-W5/chain_report.json` | `bd1d6475347bd5f6aa190fe1b5e7f5af3fb1fab9ceb1c26d7c18a8805adfe38f` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W5_s2/manifest.json` | `23490baba4254cf8e969c21950d2d0210b8cf808ce12196190bb9ce8a9277bb6` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

