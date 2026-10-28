# A01-F2-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F2-W3` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2 --cells A01-F2-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=140579285，request_id=，corr=origin，注入前地址 `before=7ffffefb50`，注入后地址 `after=7ffffe7b50`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140579285, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x7ffffefb50, new_vaddr=0x7ffffe7b50, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefb50` → `7ffffe7b50`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → squash_discarded → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，squash_discarded=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 140579285 |  | 7ffffefb50 |  |  |  | origin |
| addr_form | 2 | 1 | 140579285 |  | 7ffffe7b50 |  |  |  | origin |
| mem_req | 3 | 2 | 140579285 | 585139 | 7ffffe7b50 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 140579285 | 585139 | 7ffffe7b50 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 140579285 | 585139 | 7ffffe7b50 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 140579285 | 585139 | 7ffffe7b50 |  | Hardware | Generic | seq_primary |
| squash_discarded | 7 | 6 | 140585830 | 585139 |  |  | L4 | contained | seq_primary |
| chain_end | 8 | 7 | 214480420 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ffffe7b50 pa=
- L2 `lsq_sendfrag`：va=7ffffe7b50 pa=
- L2 `tlb_translate`：va=7ffffe7b50 pa=

## 7. 最终结局

- oracle：`Masked`；chain terminal：`provable_to_L2_then_unknown`；provable_to：`L2`；beyond：`Unknown`。
- admitted=False，certified=False，violations=['no_closed_chain_and_no_containment: A01-F2-W3 既无 family-specific L0→L5 完整链，也无显式 containment——不得判 READY', 'ready_by_activated_only: A01-F2-W3 activated=1 本身不是 READY 依据（须完整链或 containment）', 'ready_by_rc0: A01-F2-W3 RC=0 不是 READY 依据（进程正常退出≠链完整）', 'ready_by_chain_end_only: A01-F2-W3 仅存在 chain_end 事件，不构成 L5 结终局证据——不得据此判 READY']，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=214480420）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局不是 full/detected_contained（terminal=provable_to_L2_then_unknown），该 seed **不合格**，仅作为真实结局留证。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/A01-F2-W3/seed2/prop_evt.txt.gz` | `44d6a209d3b386f974acf194df16ab67d94d8368bd026ec46481760ba889ffe5` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/A01-F2-W3/seed2/stats.txt` | `0cb6e4da5f1d6d6016252c464d519353f8d7e26530a9f245dd72c82c50deceaa` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/A01-F2-W3/seed2/run.out` | `a86d96911d46682120a5161da8854a7abf61b1a3a647761ab7f1c66e9bc9d4ed` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/A01-F2-W3/seed2/run.err` | `5c8de06bae63aa5f52fb80babe441e4bd242fe13be863b061961ce01c27209f0` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/A01-F2-W3/chain_report.json` | `3f3e528ad53d8566f3755a66586a5a07842671440aff8b188f400ac07014c194` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/manifest.json` | `df39ab9adb2ecd812b2292388eb19477a5112f61ecd5678853d3fc136143137c` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。
- 本 seed **未通过验收**（见第 7 节），原因以证据为准。

