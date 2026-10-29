# A01-F1-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F1-W3` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F1 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1 --cells A01-F1-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=1596502600，request_id=，corr=origin，注入前地址 `before=493018`，注入后地址 `after=8493018`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 1596502600, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x493018, new_vaddr=0x8493018, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493018` → `8493018`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 1596502600 |  | 493018 |  |  |  | origin |
| addr_form | 2 | 1 | 1596502600 |  | 8493018 |  |  |  | origin |
| mem_req | 3 | 2 | 1596502600 | 7334370 | 8493018 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 1596502600 | 7334370 | 8493018 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 1596502600 | 7334370 | 8493018 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 1596502600 | 7334370 | 8493018 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 1596510685 |  | 8493018 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 1596510685 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=8493018 pa=
- L2 `lsq_sendfrag`：va=8493018 pa=
- L2 `tlb_translate`：va=8493018 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=1596510685）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1/A01-F1-W3/seed1/prop_evt.txt.gz` | `751b104da092c20ccb8b34e1654e482f844e10e7a7f60f39a556a7f2bd0235df` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1/A01-F1-W3/seed1/stats.txt` | `11911838613c1a0ae87b67dcb93b0720f6da8050964e8e1077a0d430c61dfdc9` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1/A01-F1-W3/seed1/run.out` | `ecd88afed5530aeaa800b769184d05985b255365a9930cab2f59674cef919890` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1/A01-F1-W3/seed1/run.err` | `f4b864179b7b70229e98ba2ea298ab90030ed295b2b09a09094d81c53d9cdd9b` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1/A01-F1-W3/chain_report.json` | `e190e61870b68187a08fe9413aeed41a4f4814bd1f443be06a814d42ed4d0971` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s1/manifest.json` | `b3fff1e398b565adf0797cc8d3767ff4c88575757040608484358f5efd62edc6` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

