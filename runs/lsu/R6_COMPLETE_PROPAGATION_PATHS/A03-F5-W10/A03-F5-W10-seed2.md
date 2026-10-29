# A03-F5-W10 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A03-F5-W10` |
| 模型 | A03（AGU EA bit stuck-at） |
| 频率档 | F5 |
| 负载 | W10 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2 --cells A03-F5-W10 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=143220，request_id=，corr=origin，注入前地址 `before=48ed78`，注入后地址 `after=148ed78`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 143220, Site: lsq_sendFragmentToTranslation, mode=a03_stuck1, old_vaddr=0x48ed78, new_vaddr=0x148ed78, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
Tick: 198660, Site: lsq_sendFragmentToTranslation, mode=a03_stuck1, old_vaddr=0x4c6690, new_vaddr=0x14c6690, faults_injected: 2, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`48ed78` → `148ed78`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → sq_execute → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，sq_execute=L3，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 143220 |  | 48ed78 |  |  |  | origin |
| addr_form | 2 | 1 | 143220 |  | 148ed78 |  |  |  | origin |
| mem_req | 3 | 2 | 143220 | 33 | 148ed78 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 143220 | 33 | 148ed78 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 143220 | 33 | 148ed78 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 143220 | 33 | 148ed78 |  | Hardware | Generic | seq_primary |
| sq_execute | 7 | 6 | 143220 |  | 148ed78 |  |  |  | seq_primary |
| arch_translation_fault | 16 | 7 | 205590 |  | 148ed78 |  | L2 | arch_exception | seq_primary |
| chain_end | 17 | 16 | 205590 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=148ed78 pa=
- L2 `lsq_sendfrag`：va=148ed78 pa=
- L2 `tlb_translate`：va=148ed78 pa=

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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2/A03-F5-W10/seed2/prop_evt.txt.gz` | `677848eee51e11b1b295548fc8c073adefa28c8f530e9592cd0af178eaafd154` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2/A03-F5-W10/seed2/stats.txt` | `6eba413ed1561fd61656845c8932238bfc6de95e355a9d93a2ce06ca5ce5153b` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2/A03-F5-W10/seed2/run.out` | `956852560bba445b6ff1c2a6aeae0470abff5afedb172fe5a7af2e502b3896fd` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2/A03-F5-W10/seed2/run.err` | `4ee65dcc4055bc2b727ae90aa2e5f20f20a6eb123d24d1e909f7cceb692a9e8d` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2/A03-F5-W10/chain_report.json` | `8da6f551070d6374a72ed124849a6387b659ec7b16561eabdf3c0c116718b90d` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A03-F5-W10_s2/manifest.json` | `2754e987f50c3330ab54f671f981df39ee5cacb28c4493bb97b37396abc68ad0` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

