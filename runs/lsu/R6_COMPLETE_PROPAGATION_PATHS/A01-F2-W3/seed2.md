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
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2 --cells A01-F2-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

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

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=214480420）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局见证事件（本 seed 自己的流）：kind=`squash_discarded`，event_id=7，parent_event_id=6，tick=140585830，detection_layer=L4，outcome=contained，contained=1，corr=seq_primary。
该 squash 属 A01 翻译 fault 请求的**窄白名单终局**：请求在翻译期（L2）硬件 fault 后从未进入下游，L3 见证结构性缺失；白名单要求同一 request（request_id 与 dyn_inst_seq 全等）、严格 ancestry（inj→addr_form→mem_req→lsq_sendfrag→tlb_translate→tlb_fault→squash）、tick 单调、squash 后无任何更深观测、流已收口，且oracle=Masked 与 rc=0（必要条件）。见 `tools/lsu_chain_check._a01_translation_squash_witness`。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2/A01-F2-W3/seed2/prop_evt.txt.gz` | `0a3b504598976450852643f11c67b3a3b8187f3ae89d13a5e01bcded8953148d` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2/A01-F2-W3/seed2/stats.txt` | `5ba00525439dda589f5bc2eb040b5d5443feda7c0120b3e07210668f1b272a94` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2/A01-F2-W3/seed2/run.out` | `ae157c487b25dc506f2be050826d87c792dee35068209613d78b7ce47a5e8db8` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2/A01-F2-W3/seed2/run.err` | `5c8de06bae63aa5f52fb80babe441e4bd242fe13be863b061961ce01c27209f0` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2/A01-F2-W3/chain_report.json` | `96c1bc6c855560c608afafd3d04c9d91763f4ff18043585a69e85d8438ae5984` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A01-F2-W3_s2/manifest.json` | `d57a98989af5d2537def9920f825b977b20e9d115b3e65ac7bd2fdcde59448ac` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

