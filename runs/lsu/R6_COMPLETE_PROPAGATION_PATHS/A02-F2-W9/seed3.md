# A02-F2-W9 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F2-W9` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F2 |
| 负载 | W9 |
| seed | 3（sample_run_id=） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W9_s3 --cells A02-F2-W9 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

**该样本没有 inj 事件**（流里没有可证注入根）。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

（无注入日志行）

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`None` → `None`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=）：``。
按证据层映射：。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|

## 6. 地址/数据/污点在每层如何变化


## 7. 最终结局

- oracle：`None`；chain terminal：`None`；provable_to：`None`；beyond：`—`。
- admitted=None，certified=None，violations=[]，truncated=None，evidence_truncated=None，事件数=None。
- 事件数：本 seed 流共 0 条，其中 fault_id= 链 0 条；最后一条为 `None`（event_id=None, tick=None）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault ）：已证 `（无）`。
终局不是 full/detected_contained（terminal=None），该 seed **不合格**，仅作为真实结局留证。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W9_s3/manifest.json` | `9b97349789564b453342ef01e57c0e022d98cd5ed36bba2084c1383aa12d441a` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。
- 本 seed **未通过验收**（见第 7 节），原因以证据为准。

