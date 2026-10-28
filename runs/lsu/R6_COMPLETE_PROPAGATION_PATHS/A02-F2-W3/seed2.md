# A02-F2-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F2-W3` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2 --cells A02-F2-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=140579285，request_id=，corr=origin，注入前地址 `before=7ffffefb50`，注入后地址 `after=7fdffe7b50`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140579285, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x7ffffefb50, new_vaddr=0x7fdffe7b50, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x20008000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefb50` → `7fdffe7b50`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 140579285 |  | 7ffffefb50 |  |  |  | origin |
| addr_form | 2 | 1 | 140579285 |  | 7fdffe7b50 |  |  |  | origin |
| mem_req | 3 | 2 | 140579285 | 585139 | 7fdffe7b50 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 140579285 | 585139 | 7fdffe7b50 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 140579285 | 585139 | 7fdffe7b50 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 140579285 | 585139 | 7fdffe7b50 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 140580055 |  | 7fdffe7b50 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 140580055 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7fdffe7b50 pa=
- L2 `lsq_sendfrag`：va=7fdffe7b50 pa=
- L2 `tlb_translate`：va=7fdffe7b50 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=140580055）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2/A02-F2-W3/seed2/prop_evt.txt.gz` | `fd4f75befe5b23501301d0fab28355cdb2d6b7b890c14ae79ae469f6182f13c5` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2/A02-F2-W3/seed2/stats.txt` | `8daddc85d038a78b8225f012129fb3c9e69c5f902f1b1df593c8c108eb0fa275` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2/A02-F2-W3/seed2/run.out` | `00dfcc13bfd1ab867770f94a4d5e3754dc21735c7acad108cc1877b2851fe077` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2/A02-F2-W3/seed2/run.err` | `e05e9dad644dd1059131b26f6b1ad870c78bd10f6e3b1ee11d5b2b963a0d989a` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2/A02-F2-W3/chain_report.json` | `27f3c9471a821c2d4abcbdf14dc1ea5b34fd4130a25bbebcc49f5758334af38d` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s2/manifest.json` | `4ef10a366e357367a078fb4dc11dfaa51e855ec4b88fd5e00b97aa890a25317b` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

