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
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1 --cells A07-F0-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=12606440，request_id=9703，corr=origin，注入前地址 `before=12606440`，注入后地址 `after=12606825`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 12606440, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=9703, ready_tick=12606440, delayed_tick=12606825, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 12606825, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=9703, consumed=1, squashed=1
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`12606440` → `12606825`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → ready_delay_resume → ready_delay_squashed → chain_end`。
按证据层映射：inj=L0，ready_delay_resume=L1，ready_delay_squashed=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 12606440 | 9703 |  |  |  |  | origin |
| ready_delay_resume | 2 | 0 | 12606825 | 9703 |  |  |  |  | seq_primary |
| ready_delay_squashed | 3 | 2 | 12606825 | 9703 |  |  | L4 | contained | seq_primary |
| chain_end | 4 | 3 | 19928370 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化


## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L1`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=4。
- 事件数：本 seed 流共 4 条，其中 fault_id=1 链 4 条；最后一条为 `chain_end`（event_id=4, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`。
终局见证事件（本 seed 自己的流）：kind=`ready_delay_squashed`，event_id=3，parent_event_id=2，tick=12606825，detection_layer=L4，outcome=contained，contained=1，corr=seq_primary。
A07-b 时序生命周期（真实钩子，非 oracle 推断）：`inj`(ready_tick=12606440 → delayed_tick=12606825, delay_cycles=1) → `ready_delay_resume`(tick=12606825, consumed=1, squashed=1) → `ready_delay_squashed`(tick=12606825, outcome=contained, containment_layer=L4, reason=squash_before_retire)。该终局来自 IEW 延迟重入/Commit 真实提交或 ROB 真实 squash，watchdog 不参与；故障只改时序、不改数据值。
该终局来自真实生命周期钩子（见上段），其 parent 链 resume→inj 逐级可证；门禁据此接受为 `detected_contained`——不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1/A07-F0-W3/seed1/prop_evt.txt.gz` | `10e50077fc93a1b27c209421662ef56923bd1150f18eb02cfafc673e6f57ba8c` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1/A07-F0-W3/seed1/stats.txt` | `63196e50965e1390b2b6de226eeb518641e4b73fa5dc5fd9500f196d14e08471` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1/A07-F0-W3/seed1/run.out` | `9b8bf8c092e40c3056294b911897d5f284788d4251e3ce8edfb1f23c4d915b04` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1/A07-F0-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1/A07-F0-W3/chain_report.json` | `afd43da5b32fd827c3600019197b44409e3ea4500989214739c9822e19a39167` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s1/manifest.json` | `a33061c975fdc436704a3aa121f33660779bad117df8d7f18976d18c746d616f` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

