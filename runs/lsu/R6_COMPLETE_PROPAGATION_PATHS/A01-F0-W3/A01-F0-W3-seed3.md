# A01-F0-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A01-F0-W3` |
| 模型 | A01（AGU EA 单bit翻转） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3 --cells A01-F0-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=4234615，request_id=，corr=origin，注入前地址 `before=491010`，注入后地址 `after=1491010`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 4234615, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x491010, new_vaddr=0x1491010, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x1000000 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491010` → `1491010`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault → arch_translation_fault → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，tlb_fault=L2，arch_translation_fault=L2，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 4234615 |  | 491010 |  |  |  | origin |
| addr_form | 2 | 1 | 4234615 |  | 1491010 |  |  |  | origin |
| mem_req | 3 | 2 | 4234615 | 2876 | 1491010 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 4234615 | 2876 | 1491010 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 4234615 | 2876 | 1491010 |  |  |  | seq_primary |
| tlb_fault | 6 | 5 | 4234615 | 2876 | 1491010 |  | Hardware | Generic | seq_primary |
| arch_translation_fault | 7 | 6 | 4235385 |  | 1491010 |  | L2 | arch_exception | seq_primary |
| chain_end | 8 | 7 | 4235385 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=1491010 pa=
- L2 `lsq_sendfrag`：va=1491010 pa=
- L2 `tlb_translate`：va=1491010 pa=

## 7. 最终结局

- oracle：`Crash`；chain terminal：`detected_contained`；provable_to：`L2`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=8。
- 事件数：本 seed 流共 8 条，其中 fault_id=1 链 8 条；最后一条为 `chain_end`（event_id=8, tick=4235385）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3/A01-F0-W3/seed3/prop_evt.txt.gz` | `b975f4cef7968db7059d34b6d1f680bf3be08ad4ec7329f98fa35030d083d4aa` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3/A01-F0-W3/seed3/stats.txt` | `9de4d86204b2a20a93e2732c567c705f7f0940612020b9f85f130b5ddd5fc0b1` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3/A01-F0-W3/seed3/run.out` | `1cc3bb6f2f4152d9f2b13077923fb7c32e4fe527dfaf092339cbba61c2874a0e` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3/A01-F0-W3/seed3/run.err` | `6af4058b99e9e440d288a2543a88c420ef8412ce844da1b8410e1ff2d3b3f23d` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3/A01-F0-W3/chain_report.json` | `052645d1d616fbfd9766c932cebd3b0e631f6def2e2c828f0496d6aab99c8adb` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F0-W3_s3/manifest.json` | `5f7113c94601c07960650f2a0a0ddfbac50fa5d74e89296f4f2ffafc2da6a4d2` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

