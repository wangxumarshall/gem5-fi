# A08-F2-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A08-F2-W3` |
| 模型 | A08（AGU 通道/同周期EA互换） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 80080, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=80080, dyn_inst_seq=5, request_id=5, isLoad=1, load_seq=5, store_seq=0, load_old_ea=0x7ffffefdc0, load_new_ea=0x7ffffefdc0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2 --cells A08-F2-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

**该样本没有 inj 事件**（流里没有可证注入根）。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 80080, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=80080, dyn_inst_seq=5, request_id=5, isLoad=1, load_seq=5, store_seq=0, load_old_ea=0x7ffffefdc0, load_new_ea=0x7ffffefdc0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
Tick: 197890, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=197890, dyn_inst_seq=48, request_id=48, isLoad=1, load_seq=48, store_seq=0, load_old_ea=0x7ffffefde0, load_new_ea=0x7ffffefde0, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
Tick: 197890, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=197890, dyn_inst_seq=44, request_id=44, isLoad=0, load_seq=0, store_seq=44, load_old_ea=0x0, load_new_ea=0x0, store_old_ea=0x7ffffefd90, size=8, page_ok=0, decline_reason=store_after_load
Tick: 479325, Site: lsq_pushRequest_A08, mode=a08_pair_swap, submodel=a08b, pair_tick=479325, dyn_inst_seq=245, request_id=245, isLoad=1, load_seq=245, store_seq=0, load_old_ea=0x7ffffefde8, load_new_ea=0x7ffffefde8, store_old_ea=0x0, size=8, page_ok=0, decline_reason=pair_missing
... (87855 more lines in the injection log)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`None` → `None`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_ea` = `0x7ffffefdc0`
- `new_ea` = `0x7ffffefdc0`
- `submodel` = `a08b`

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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2/A08-F2-W3/seed2/prop_evt.txt.gz` | `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2/A08-F2-W3/seed2/stats.txt` | `1eeb229c7ee8eaf07d16a221d1d1a1aa7da784fc62abf38fcdaa02c152093ce2` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2/A08-F2-W3/seed2/run.out` | `cb5f3a67e7b9c5401ea5336873062f7be413c7afd0201fe67e09c1a1b480b2f1` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2/A08-F2-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2/A08-F2-W3/chain_report.json` | `63acd52fa53b960d80c9464deb6407628dd3403fcf16480d48dba3244e27ff65` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A08-F2-W3_s2/manifest.json` | `a5891a612acf52ad60f09f2082140651467e4e7f23b57d47e5036d88c60ec78f` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。
- 本 seed **未通过验收**（见第 7 节），原因以证据为准。

