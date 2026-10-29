# A01-F2-W9 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F2-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F2 |
| 负载 | W9 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1 --cells A01-F2-W9 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 900` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=158186490，request_id=，corr=origin，注入前地址 `before=4945c0`，注入后地址 `after=84945c0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 158186490, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x4945c0, new_vaddr=0x84945c0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4945c0` → `84945c0`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 158186490 |  | 4945c0 |  |  |  | origin |
| addr_form | 2 | 1 | 158186490 |  | 84945c0 |  |  |  | origin |
| mem_req | 3 | 2 | 158186490 | 576812 | 84945c0 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 158186490 | 576812 | 84945c0 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 158186490 | 576812 | 84945c0 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 158186490 | 576812 | 84945c0 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 158188030 |  | 84945c0 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 158188030 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=84945c0 pa=
- L2 `lsq_sendfrag`：va=84945c0 pa=
- L2 `tlb_translate`：va=84945c0 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=158188030）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局见证事件（本 seed 自己的流）：kind=`arch_translation_fault`，event_id=7，parent_event_id=6，tick=158188030，detection_layer=L2，outcome=arch_exception，contained=1，corr=seq_primary。
该事件是**真实交付的架构翻译异常**（guest SEGV）：L2 硬件检测 + contained 字段 + 与注入链的 corr 关联；门禁按既有规则接受为 `detected_contained`——不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1/A01-F2-W9/seed1/prop_evt.txt.gz` | `bb447571970dfcb479c51c62ec3b821c96aadb346fb89f6b0cabaa6274109fd3` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1/A01-F2-W9/seed1/stats.txt` | `b4667e7d4c3b5fc58c3de7a5f5d9ce20b50db185e0c5aba1850d4b81d13dac63` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1/A01-F2-W9/seed1/run.out` | `34553279df9602d67622bd9899dabc0b6a7871e6bf67d05af2fb5392e5a7b06d` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1/A01-F2-W9/seed1/run.err` | `52a95cee6c5389af6dd6f8eb65114eef264de88fa04d1bf033f42a390fb725c6` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1/A01-F2-W9/chain_report.json` | `557f023669ae2eb4357b9255a537ec878a877a98c770ad1b5e88b70211d1baf4` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W9_s1/manifest.json` | `24179e720d095618b671f2bfa74d59396ae8e3569581693b9fe8b485107fcba1` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

