# A04-F0-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F0-W3` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 16704380, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x7ffffefbe8, new_addr=0x7ffffefbec, old_size=4, new_size=4, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=4, be_ones=4, be_subst=0, submodel=a04b, old_be=0xf, new_be=0xf, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2 --cells A04-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=16704380，request_id=，corr=origin，注入前地址 `before=7ffffefbe8`，注入后地址 `after=7ffffefbec`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 16704380, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x7ffffefbe8, new_addr=0x7ffffefbec, old_size=4, new_size=4, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=4, be_ones=4, be_subst=0, submodel=a04b, old_be=0xf, new_be=0xf, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`7ffffefbe8` → `7ffffefbec`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `4`
- `new_size` = `4`
- `old_be` = `0xf`
- `new_be` = `0xf`
- `submodel` = `a04b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → squash_discarded → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，squash_discarded=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 16704380 |  | 7ffffefbe8 |  |  |  | origin |
| addr_form | 2 | 1 | 16704380 |  | 7ffffefbec |  |  |  | origin |
| lsq_push | 3 | 2 | 16704380 |  | 7ffffefbec |  |  |  | seq_primary |
| mem_req | 4 | 3 | 16704380 | 14682 | 7ffffefbec |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 16704380 | 14682 | 7ffffefbec |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 16704380 | 14682 | 7ffffefbec |  |  |  | seq_primary |
| lq_read | 7 | 6 | 16704380 | 14682 | 7ffffefbec |  |  |  | seq_primary |
| squash_discarded | 8 | 7 | 16704765 | 14682 |  |  | L4 | contained | seq_primary |
| chain_end | 9 | 8 | 19928370 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=7ffffefbec pa=
- L2 `lsq_sendfrag`：va=7ffffefbec pa=
- L2 `tlb_translate`：va=7ffffefbec pa=

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L3`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=9。
- 事件数：本 seed 流共 9 条，其中 fault_id=1 链 9 条；最后一条为 `chain_end`（event_id=9, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`。
终局事件的 detection_layer=、outcome=run_end、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2/A04-F0-W3/seed2/prop_evt.txt.gz` | `1e72937fcb1eb138e88f9bd606038351d1565518c14d7322e7a1364e9f80cb4d` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2/A04-F0-W3/seed2/stats.txt` | `def3932a03af06ab1925b8703349b4f135c0e36d42f599c25dfda47ea3fbd5ff` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2/A04-F0-W3/seed2/run.out` | `8e9ba61609ae5e8e914cc7b08366eff6cef81f73d1c4bd7b59b2025d98694162` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2/A04-F0-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2/A04-F0-W3/chain_report.json` | `b5d18b11acb004761eb9518066fd785ea3e2ffe961af3a0da6719099e4b34b57` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W3_s2/manifest.json` | `483875987eebd8805bb710b0c5a4bb9c1ae7a39c11f3ec0611ac1f1c03cc0f4b` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

