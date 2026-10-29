# A01-F1-W9 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F1-W9` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F1 |
| 负载 | W9 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1 --cells A01-F1-W9 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=1426936665，request_id=，corr=origin，注入前地址 `before=496b68`，注入后地址 `after=8496b68`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 1426936665, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x496b68, new_vaddr=0x8496b68, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`496b68` → `8496b68`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 1426936665 |  | 496b68 |  |  |  | origin |
| addr_form | 2 | 1 | 1426936665 |  | 8496b68 |  |  |  | origin |
| mem_req | 3 | 2 | 1426936665 | 5953745 | 8496b68 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 1426936665 | 5953745 | 8496b68 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 1426936665 | 5953745 | 8496b68 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 1426936665 | 5953745 | 8496b68 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 1426940130 |  | 8496b68 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 1426940130 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=8496b68 pa=
- L2 `lsq_sendfrag`：va=8496b68 pa=
- L2 `tlb_translate`：va=8496b68 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=1426940130）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1/A01-F1-W9/seed1/prop_evt.txt.gz` | `41833cb4faa78a5b1149f7c8ed8a5d4684940e646da04349f7a83d12fc9e3e11` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1/A01-F1-W9/seed1/stats.txt` | `017c55b809d13cb7abc296f8a8100446355fea56fa11db821162a99722946bf0` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1/A01-F1-W9/seed1/run.out` | `5b234e053dcea5955326f79a568ff713e78d0a8d5911131fba6b0b0cc33d81f6` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1/A01-F1-W9/seed1/run.err` | `45e9140f4298c1f1be13ae3cb69e1747289df18da924ee673e60d9b139748ae5` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1/A01-F1-W9/chain_report.json` | `abe5da0819793c45e93decd7f81bb206165478835b2f9e48468de110188b0643` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W9_s1/manifest.json` | `8f70edef959ab1e7f716fbb8d86fc5eeb9a91438d42ca0ed00781e88b48ec204` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

