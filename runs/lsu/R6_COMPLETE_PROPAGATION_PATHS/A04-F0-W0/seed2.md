# A04-F0-W0 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F0-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F0 |
| 负载 | W0 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 12558315, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x490d40, new_addr=0x490a58, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04b, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2 --cells A04-F0-W0 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=12558315，request_id=，corr=origin，注入前地址 `before=490d40`，注入后地址 `after=490a58`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 12558315, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x490d40, new_addr=0x490a58, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04b, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`490d40` → `490a58`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a04b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → squash_discarded → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，squash_discarded=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 12558315 |  | 490d40 |  |  |  | origin |
| addr_form | 2 | 1 | 12558315 |  | 490a58 |  |  |  | origin |
| lsq_push | 3 | 2 | 12558315 |  | 490a58 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 12558315 | 9595 | 490a58 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 12558315 | 9595 | 490a58 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 12558315 | 9595 | 490a58 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 12558315 | 9595 | 490a58 |  |  |  | seq_primary |
| squash_discarded | 8 | 7 | 12558700 | 9595 |  |  | L4 | contained | seq_primary |
| chain_end | 9 | 8 | 20430025 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=490a58 pa=
- L2 `lsq_sendfrag`：va=490a58 pa=
- L2 `tlb_translate`：va=490a58 pa=

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L3`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=9。
- 事件数：本 seed 流共 9 条，其中 fault_id=1 链 9 条；最后一条为 `chain_end`（event_id=9, tick=20430025）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2/A04-F0-W0/seed2/prop_evt.txt.gz` | `3c37729bded5b503b1bc4996bc5c879d3f35dc77bd3c652567669786dbe40d42` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2/A04-F0-W0/seed2/stats.txt` | `9ecbeebfad93ac65885774f7079bf86bc0abb589b171529bccdb971428b387f1` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2/A04-F0-W0/seed2/run.out` | `4ebd0a7911f0ddfa60dea26341c16bc4e2d6025d37cfd8b32faffc4f0df2779a` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2/A04-F0-W0/seed2/run.err` | `6a37888cc97b5c9a4f5f9a2b8b139c7727e622cdd19640036d76440d3b90ad34` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2/A04-F0-W0/chain_report.json` | `a6084daf3211e42ce4351591dc11755473d4e65a22fb893c5dd7cf89e514bb07` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s2/manifest.json` | `db8bdff6cec56e80fff38bb81f4383a074f3e29d75ce1d4285c4aa2a4e717a03` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

