# A02-F2-W9 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F2-W9` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F2 |
| 负载 | W9 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1 --cells A02-F2-W9 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 900` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=158186490，request_id=，corr=origin，注入前地址 `before=4945c0`，注入后地址 `after=4945c6`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 158186490, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x4945c0, new_vaddr=0x4945c6, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x6 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4945c0` → `4945c6`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 158186490 |  | 4945c0 |  |  |  | origin |
| addr_form | 2 | 1 | 158186490 |  | 4945c6 |  |  |  | origin |
| mem_req | 3 | 2 | 158186490 | 576812 | 4945c6 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 158186490 | 576812 | 4945c6 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 158186490 | 576812 | 4945c6 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 158186490 | 576812 | 4945c6 |  |  |  | seq_primary |
| resp | 7 | 6 | 158187260 | 576812 | 7a5c6 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 158187260 | 576812 | 4945c6 | 7a5c6 |  |  | seq_primary |
| taint_reg | 9 | 8 | 158187260 | 576812 | 7a5c6 |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 158188030 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 158189570 |  |  |  |  |  | taint_prop |
| consumer | 12 | 11 | 158189570 |  |  |  |  |  | taint_prop |
| consumer | 13 | 11 | 158189570 |  |  |  |  |  | taint_prop |
| consumer | 14 | 11 | 158189570 |  |  |  |  |  | taint_prop |
| chain_end | 15 | 14 | 325417785 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4945c6 pa=
- L2 `lsq_sendfrag`：va=4945c6 pa=
- L2 `tlb_translate`：va=4945c6 pa=
- L3 `resp`：va=7a5c6 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=15。
- 事件数：本 seed 流共 15 条，其中 fault_id=1 链 15 条；最后一条为 `chain_end`（event_id=15, tick=325417785）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`chain_end`，event_id=15，parent_event_id=14，tick=325417785，detection_layer=L5，outcome=errant_commit_seen，contained=1，corr=none。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `full`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1/A02-F2-W9/seed1/prop_evt.txt.gz` | `4eb11608fbef389521b0d2294897c3b98405680d2ddc69f9d3fb9514648bf39c` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1/A02-F2-W9/seed1/stats.txt` | `a2e6e37553ca817150c29058ddc1bd28b1eafbd2eec25f2287d9b143285f46b1` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1/A02-F2-W9/seed1/run.out` | `45ad3399d53506acb23b211786bd657726b683f793389b0ac2b88c251e81968f` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1/A02-F2-W9/seed1/run.err` | `70eea0776f34f13af666fe542bab517beab9a8b81989f41e1d73d96763cfdc80` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1/A02-F2-W9/chain_report.json` | `02020b587bd53be95c9a0586fd8290e210c330e0b1e52a82fd2e3a283545c0d6` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s1/manifest.json` | `1d1363a8aa2067a059edba113266b888e37b813458fdbbb2a38352aef8b8667c` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

