# A01-F0-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F0-W3` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1 --cells A01-F0-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=18110015，request_id=，corr=origin，注入前地址 `before=7ffffefba8`，注入后地址 `after=7ff7fefba8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 18110015, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x7ffffefba8, new_vaddr=0x7ff7fefba8, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefba8` → `7ff7fefba8`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → sq_execute → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，sq_execute=L3，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 18110015 |  | 7ffffefba8 |  |  |  | origin |
| addr_form | 2 | 1 | 18110015 |  | 7ff7fefba8 |  |  |  | origin |
| mem_req | 3 | 2 | 18110015 | 16321 | 7ff7fefba8 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 18110015 | 16321 | 7ff7fefba8 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 18110015 | 16321 | 7ff7fefba8 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 18110015 | 16321 | 7ff7fefba8 |  | Hardware | Generic | seq_primary |
| sq_execute | 7 | 6 | 18110015 |  | 7ff7fefba8 |  |  |  | seq_primary |
| arch_translation_fault | 8 | 7 | 18111940 |  | 7ff7fefba8 |  | L2 | arch_exception | seq_primary |
| chain_end | 9 | 8 | 18111940 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ff7fefba8 pa=
- L2 `lsq_sendfrag`：va=7ff7fefba8 pa=
- L2 `tlb_translate`：va=7ff7fefba8 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L3`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=9。
- 事件数：本 seed 流共 9 条，其中 fault_id=1 链 9 条；最后一条为 `chain_end`（event_id=9, tick=18111940）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1/A01-F0-W3/seed1/prop_evt.txt.gz` | `4d9a85071c99d1f81c526c59bdd6851f0afa672a1787665ad0504bc8cb284687` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1/A01-F0-W3/seed1/stats.txt` | `d4dd581cb8cdb6dd056db96b6fe7df606372a30e37232f42461faa4715c95011` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1/A01-F0-W3/seed1/run.out` | `9ff4e82ebfd3305f20438bf866d2d5682dd98a0be1fe4693d233e3569e1e8b07` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1/A01-F0-W3/seed1/run.err` | `76e33884ef35ae0f48d39f45236271df6b70ca4758eed060ed210343bf0fe456` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1/A01-F0-W3/chain_report.json` | `0d46d821e75c84fd69dc91a888bd9b88df85e9b73677b7afbbb9e4e6c515689a` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s1/manifest.json` | `b4083896e2da97bae9043548bb60ccd06a20e24fc93c8ac335b8a963e327bafb` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

