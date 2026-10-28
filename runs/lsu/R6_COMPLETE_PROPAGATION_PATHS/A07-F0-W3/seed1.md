# A07-F0-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F0-W3` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1 --cells A07-F0-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=12606440，request_id=，corr=origin，注入前地址 `before=12606440`，注入后地址 `after=12606825`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 12606440, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=9703, ready_tick=12606440, delayed_tick=12606825, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 12606825, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=9703, consumed=1, squashed=1
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`12606440` → `12606825`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → chain_end`。
按证据层映射：inj=L0，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 12606440 |  |  |  |  |  | origin |
| chain_end | 2 | 0 | 19928370 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化


## 7. 最终结局

- oracle：`Masked`；chain terminal：`provable_to_L0_then_unknown`；provable_to：`L0`；beyond：`Unknown`。
- admitted=False，certified=False，violations=['no_closed_chain_and_no_containment: A07-F0-W3 既无 family-specific L0→L5 完整链，也无显式 containment——不得判 READY', 'ready_by_activated_only: A07-F0-W3 activated=1 本身不是 READY 依据（须完整链或 containment）', 'ready_by_rc0: A07-F0-W3 RC=0 不是 READY 依据（进程正常退出≠链完整）', 'ready_by_chain_end_only: A07-F0-W3 仅存在 chain_end 事件，不构成 L5 结终局证据——不得据此判 READY']，truncated=False，evidence_truncated=False，事件数=2。
- 事件数：本 seed 流共 2 条，其中 fault_id=1 链 2 条；最后一条为 `chain_end`（event_id=2, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `（无）`。
终局不是 full/detected_contained（terminal=provable_to_L0_then_unknown），该 seed **不合格**，仅作为真实结局留证。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1/A07-F0-W3/seed1/prop_evt.txt.gz` | `bf5abbe716d5079343693cb3f33874354a3cb2320eae51186fef98823a95732f` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1/A07-F0-W3/seed1/stats.txt` | `e1b91a2c93116bf934035ba34784837aed8e41ae8bac359e1dd0043204eb92eb` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1/A07-F0-W3/seed1/run.out` | `141a86f2a35576ba19496f79caf60b025016acb6601dae094011d6d41d4aa591` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1/A07-F0-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1/A07-F0-W3/chain_report.json` | `3a11ab9af19ec925a4404d5efa797d496725f9550105da978d1bf0a4259563e9` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F0-W3_s1/manifest.json` | `b99c0252534fd3234311393bf22966787eeeb719877c3adfa0be487743df59fe` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。
- 本 seed **未通过验收**（见第 7 节），原因以证据为准。

