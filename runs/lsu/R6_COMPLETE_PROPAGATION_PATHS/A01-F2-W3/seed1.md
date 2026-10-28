# A01-F2-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F2-W3` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1 --cells A01-F2-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=149330720，request_id=，corr=origin，注入前地址 `before=4932b0`，注入后地址 `after=84932b0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 149330720, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x4932b0, new_vaddr=0x84932b0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4932b0` → `84932b0`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 149330720 |  | 4932b0 |  |  |  | origin |
| addr_form | 2 | 1 | 149330720 |  | 84932b0 |  |  |  | origin |
| mem_req | 3 | 2 | 149330720 | 625711 | 84932b0 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 149330720 | 625711 | 84932b0 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 149330720 | 625711 | 84932b0 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 149330720 | 625711 | 84932b0 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 149339575 |  | 84932b0 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 149339575 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=84932b0 pa=
- L2 `lsq_sendfrag`：va=84932b0 pa=
- L2 `tlb_translate`：va=84932b0 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=149339575）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1/A01-F2-W3/seed1/prop_evt.txt.gz` | `d1cf4153afe5dd16231675100c5a0b047a4d71d278263c0a98c2e901d4b0d716` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1/A01-F2-W3/seed1/stats.txt` | `13c83d64b14d0ee91b543dbf4c36d29738842db35e65f5b807e8aafece16f01a` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1/A01-F2-W3/seed1/run.out` | `dd6fca42d167dba1395f3f6d01929ce2a58c59962bf023c43b99b44755bb9dac` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1/A01-F2-W3/seed1/run.err` | `052592906747de250d910c11180d5b0cae43646e53877cdf665de8c10838b771` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1/A01-F2-W3/chain_report.json` | `a19be89b19180ea1a11515dc85110475af64f92e6aecedec9087df76263e6ec5` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s1/manifest.json` | `e3e985a1ccbbafecab5d9da089cf7a4c965be2cae7ebdd2b1948cca22126436b` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

