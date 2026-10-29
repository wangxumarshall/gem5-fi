# A02-F2-W9 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F2-W9` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F2 |
| 负载 | W9 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2 --cells A02-F2-W9 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 900` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=150760225，request_id=，corr=origin，注入前地址 `before=49d5e0`，注入后地址 `after=204955e0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 150760225, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x49d5e0, new_vaddr=0x204955e0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x20008000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`49d5e0` → `204955e0`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 150760225 |  | 49d5e0 |  |  |  | origin |
| addr_form | 2 | 1 | 150760225 |  | 204955e0 |  |  |  | origin |
| mem_req | 3 | 2 | 150760225 | 545815 | 204955e0 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 150760225 | 545815 | 204955e0 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 150760225 | 545815 | 204955e0 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 150760225 | 545815 | 204955e0 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 150760995 |  | 204955e0 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 150760995 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=204955e0 pa=
- L2 `lsq_sendfrag`：va=204955e0 pa=
- L2 `tlb_translate`：va=204955e0 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=150760995）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局见证事件（本 seed 自己的流）：kind=`arch_translation_fault`，event_id=7，parent_event_id=6，tick=150760995，detection_layer=L2，outcome=arch_exception，contained=1，corr=seq_primary。
该事件是**真实交付的架构翻译异常**（guest SEGV）：L2 硬件检测 + contained 字段 + 与注入链的 corr 关联；门禁按既有规则接受为 `detected_contained`——不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2/A02-F2-W9/seed2/prop_evt.txt.gz` | `94a1fecccfb1c85df76a8f89c3db99eff6405790b52139a2ddd1886bee7228d0` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2/A02-F2-W9/seed2/stats.txt` | `908bc599ff3616e54ab538f438eacf0a5ec38b99581a3e2ee02c07ea9a92b0bb` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2/A02-F2-W9/seed2/run.out` | `4c3f904fce3f741efb7fbcad2964f7239aa74fb1a8eb6a627eba4b8f6bd125a3` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2/A02-F2-W9/seed2/run.err` | `9e6f5aae2c5cc9df116a9c8d7ebe10201fe4b9ba039ac7d0a92111798e55c691` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2/A02-F2-W9/chain_report.json` | `beab03835073d0508fbd88dc3b531fee63c24a35dc25f75b81dfaab25ae24a0f` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A02-F2-W9_s2/manifest.json` | `b0b13417dc8681869c41800b833943df804534c010dd10037a9052dde6234e2f` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

