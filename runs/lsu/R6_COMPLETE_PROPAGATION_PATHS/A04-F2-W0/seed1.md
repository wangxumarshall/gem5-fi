# A04-F2-W0 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W0 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1 --cells A04-F2-W0 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

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

- oracle：`Masked`；chain terminal：`None`；provable_to：`None`；beyond：`—`。
- admitted=None，certified=None，violations=[]，truncated=False，evidence_truncated=False，事件数=0。
- 事件数：本 seed 流共 0 条，其中 fault_id= 链 0 条；最后一条为 `None`（event_id=None, tick=None）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault ）：已证 `（无）`。
终局不是 full/detected_contained（terminal=None），该 seed **不合格**，仅作为真实结局留证。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1/A04-F2-W0/seed1/prop_evt.txt.gz` | `d1f5b4365ab1cae6477a148fc160aef061bf70ad7dfef3ee32faef52ecb75fcc` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1/A04-F2-W0/seed1/stats.txt` | `8d76ad9b103e7dc5a2a99704c352a6ae6191902a57c27acc9912c12355f882ab` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1/A04-F2-W0/seed1/run.out` | `fa2e9c18634f1b2c022ba5f6b9bdf159e38a47e102562191f996555c9db64f22` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1/A04-F2-W0/seed1/run.err` | `e6f78ab080a7d5ce5e2d0a89e18a125e11c5d554b13e1fedce85516303fc7db0` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1/A04-F2-W0/chain_report.json` | `dac9ca35190362e34ac60e9d892f085205bd6ac79bc9b9734e06fd7a06f0c7ad` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s1/manifest.json` | `dd860a336af722c1bcf89267c289e6e5bd7b99343cb1206953f1e430d488d030` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。
- 本 seed **未通过验收**（见第 7 节），原因以证据为准。

