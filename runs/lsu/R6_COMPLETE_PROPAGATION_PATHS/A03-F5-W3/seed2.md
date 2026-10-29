# A03-F5-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A03-F5-W3` |
| 模型 | A03（AGU EA bit stuck-at） |
| 频率档 | F5 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2 --cells A03-F5-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=143220，request_id=，corr=origin，注入前地址 `before=48ed88`，注入后地址 `after=148ed88`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 143220, Site: lsq_sendFragmentToTranslation, mode=a03_stuck1, old_vaddr=0x48ed88, new_vaddr=0x148ed88, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
Tick: 198660, Site: lsq_sendFragmentToTranslation, mode=a03_stuck1, old_vaddr=0x4980f0, new_vaddr=0x14980f0, faults_injected: 2, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`48ed88` → `148ed88`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → sq_execute → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，sq_execute=L3，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 143220 |  | 48ed88 |  |  |  | origin |
| addr_form | 2 | 1 | 143220 |  | 148ed88 |  |  |  | origin |
| mem_req | 3 | 2 | 143220 | 33 | 148ed88 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 143220 | 33 | 148ed88 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 143220 | 33 | 148ed88 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 143220 | 33 | 148ed88 |  | Hardware | Generic | seq_primary |
| sq_execute | 7 | 6 | 143220 |  | 148ed88 |  |  |  | seq_primary |
| arch_translation_fault | 16 | 7 | 205590 |  | 148ed88 |  | L2 | arch_exception | seq_primary |
| chain_end | 17 | 16 | 205590 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=148ed88 pa=
- L2 `lsq_sendfrag`：va=148ed88 pa=
- L2 `tlb_translate`：va=148ed88 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L3`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=17。
- 事件数：本 seed 流共 17 条，其中 fault_id=1 链 9 条；最后一条为 `chain_end`（event_id=17, tick=205590）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2/A03-F5-W3/seed2/prop_evt.txt.gz` | `4ec65f8dc8ffe7df6c688ccd32e1829a5c731faf6645beea6ab1f7099ea66080` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2/A03-F5-W3/seed2/stats.txt` | `673cbecdf0ffe12c2d6da7a241fb6553fccb716dae438a641904f5ff6627f0fc` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2/A03-F5-W3/seed2/run.out` | `09538c57ef473fc304983e870acf75ef69b159eb4e870d8fccdc2cca28c91b76` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2/A03-F5-W3/seed2/run.err` | `52cdd25769bffc9bc2998d81dd5b31c239e5fb1b5ce265eab3a4dd8192bda1d3` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2/A03-F5-W3/chain_report.json` | `96496ff9afb58dcfc872063329e62282008e1948e349410e632aa2805eb5b992` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W3_s2/manifest.json` | `8ec1485e1ad68420f372127555602ec4e6b56962789d8c1ff9591517426fbdc5` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

