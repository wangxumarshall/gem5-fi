# A07-F0-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F0-W3` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2 --cells A07-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=16704380，request_id=14682，corr=origin，注入前地址 `before=16704380`，注入后地址 `after=16704765`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 16704380, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=14682, ready_tick=16704380, delayed_tick=16704765, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 16704765, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=14682, consumed=1, squashed=1
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`16704380` → `16704765`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → ready_delay_resume → ready_delay_squashed → chain_end`。
按证据层映射：inj=L0，ready_delay_resume=L1，ready_delay_squashed=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 16704380 | 14682 |  |  |  |  | origin |
| ready_delay_resume | 2 | 0 | 16704765 | 14682 |  |  |  |  | seq_primary |
| ready_delay_squashed | 3 | 2 | 16704765 | 14682 |  |  | L4 | contained | seq_primary |
| chain_end | 4 | 3 | 19928370 |  |  |  |  | run_end | none |

## 6. 地址/数据/污点在每层如何变化


## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L1`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=4。
- 事件数：本 seed 流共 4 条，其中 fault_id=1 链 4 条；最后一条为 `chain_end`（event_id=4, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`。
终局见证事件（本 seed 自己的流）：kind=`ready_delay_squashed`，event_id=3，parent_event_id=2，tick=16704765，detection_layer=L4，outcome=contained，contained=1，corr=seq_primary。
A07-b 时序生命周期（真实钩子，非 oracle 推断）：`inj`(ready_tick=16704380 → delayed_tick=16704765, delay_cycles=1) → `ready_delay_resume`(tick=16704765, consumed=1, squashed=1) → `ready_delay_squashed`(tick=16704765, outcome=contained, containment_layer=L4, reason=squash_before_retire)。该终局来自 IEW 延迟重入/Commit 真实提交或 ROB 真实 squash，watchdog 不参与；故障只改时序、不改数据值。
该终局来自真实生命周期钩子（见上段），其 parent 链 resume→inj 逐级可证；门禁据此接受为 `detected_contained`——不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2/A07-F0-W3/seed2/prop_evt.txt.gz` | `315bab9d7cc130a3a7eefec3180a104c4249d73d0841a4177878dd45de3811fa` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2/A07-F0-W3/seed2/stats.txt` | `79e1296bf9e5dbcd1c0750e38dbc7b1b934874f16bd81476371e5ceacd2a09bf` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2/A07-F0-W3/seed2/run.out` | `9acee45c392e6a532af879e37e75453647a311d37e4451757311ca0b9b4c2bc5` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2/A07-F0-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2/A07-F0-W3/chain_report.json` | `b95616cba9f62f121bf8ca4d47e81f25432915a32d718eadc10cc1b79e35ffc5` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A07-F0-W3_s2/manifest.json` | `856b50ea98041de521b6bcb8f40928041e61b3e8ac0d9c1500b3c3c6d2aaf8ae` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

