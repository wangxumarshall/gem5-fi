# A08-F2-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F2-W3` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd30, size=8, page_ok=0, decline_reason=store_before_load |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3 --cells A08-F2-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

**该样本没有 inj 事件**（流里没有可证注入根）。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 140910, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=140910, dyn_inst_seq=18, request_id=18, isLoad=0, load_seq=0, store_seq=18, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd30, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141295, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141295, dyn_inst_seq=19, request_id=19, isLoad=0, load_seq=0, store_seq=19, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd38, size=8, page_ok=0, decline_reason=store_before_load
Tick: 141680, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=141680, dyn_inst_seq=23, request_id=23, isLoad=0, load_seq=0, store_seq=23, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd40, size=8, page_ok=0, decline_reason=store_before_load
Tick: 142065, Site: lsq_pushRequest_A08, mode=a08_channel, submodel=a08a, pair_tick=142065, dyn_inst_seq=24, request_id=24, isLoad=0, load_seq=0, store_seq=24, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd48, size=8, page_ok=0, decline_reason=store_before_load
... (68245 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`None` → `None`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x0`
- `new_ea` = `0x0`
- `submodel` = `a08a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=）：``。
按证据层映射：。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|

## 6. 地址/数据/污点在每层如何变化


## 7. 最终结局

- oracle：`Masked`；chain terminal：`None`；provable_to：`None`；beyond：`—`。
- admitted=None，certified=None，violations=[]，truncated=False，evidence_truncated=False，事件数=0。
- 事件数：本 seed 流共 0 条，其中 fault_id= 链 0 条；最后一条为 `None`（event_id=None, tick=None）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault ）：已证 `（无）`。
终局不是 full/detected_contained（terminal=None），该 seed **不合格**，仅作为真实结局留证。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3/A08-F2-W3/seed3/prop_evt.txt.gz` | `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3/A08-F2-W3/seed3/stats.txt` | `74bef98cd0d4480d3a58c5d67d1f3f688601893601eb053665242d05c1893406` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3/A08-F2-W3/seed3/run.out` | `d9948d642d4659a77190a3cc831def4741c16b0834d6ff263b13b091f310ec51` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3/A08-F2-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3/A08-F2-W3/chain_report.json` | `f8b4e8677d1c2f97e5744f158b8a3024f88999b847e8bdab88cb0581eb8a45c6` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s3/manifest.json` | `2f6a180614f87f66900b4a361396d905f54ae0388889c2f3c673da8f06988fd9` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。
- 本 seed **未通过验收**（见第 7 节），原因以证据为准。

