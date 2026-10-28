# A06-F0-W5 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A06-F0-W5` |
| 模型 | A06（AGU 访问尺寸/掩码） |
| 频率档 | F0 |
| 负载 | W5 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 15964795, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x491a58, new_addr=0x491a58, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=none, be_len=8, be_ones=8, be_subst=1, submodel=a06b, old_be=0xff, new_be=0x7f, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2 --cells A06-F0-W5 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=15964795，request_id=，corr=origin，注入前地址 `before=491a58`，注入后地址 `after=491a58`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 15964795, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x491a58, new_addr=0x491a58, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=none, be_len=8, be_ones=8, be_subst=1, submodel=a06b, old_be=0xff, new_be=0x7f, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491a58` → `491a58`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0x7f`
- `submodel` = `a06b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 15964795 |  | 491a58 |  |  |  | origin |
| addr_form | 2 | 1 | 15964795 |  | 491a58 |  |  |  | origin |
| lsq_push | 3 | 2 | 15964795 |  | 491a58 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 15964795 | 13362 | 491a58 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 15964795 | 13362 | 491a58 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 15964795 | 13362 | 491a58 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 15964795 |  | 491a58 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 15966335 |  |  | 77a58 |  |  | seq_primary |
| resp | 9 | 8 | 15967105 | 13362 | 77a58 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 15967105 | 13362 | 77a58 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 15967105 |  | 491a58 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 19229210 | 13362 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 19229210 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=491a58 pa=
- L2 `lsq_sendfrag`：va=491a58 pa=
- L2 `tlb_translate`：va=491a58 pa=
- L3 `resp`：va=77a58 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=19229210）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2/A06-F0-W5/seed2/prop_evt.txt.gz` | `985173f89caf3462f0d1f630e64c1723aa53f6130b92b0a84986c97bd7e56a29` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2/A06-F0-W5/seed2/stats.txt` | `9f98f7dcac4c01be9d02d5ad7ead42aaccb19c9066af285b1f9ba93d6daa35f4` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2/A06-F0-W5/seed2/run.out` | `9feaaece36dbe712ea9a6e0f3ced66cc8aa8e24217f36b8dfe7eb8e95f850376` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2/A06-F0-W5/seed2/run.err` | `79c4fee84c75e876e776c69f1f0af49807527b7520b0353150d609626ace8fea` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2/A06-F0-W5/chain_report.json` | `217bc55a694e6201ed2d441e88a7754af35bbfbf0e2861a9a64e44d70de9899c` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F0-W5_s2/manifest.json` | `aed92624f5917c016bb23495e9a887a8efc3d926a552e64473a052b2358a6ef0` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

