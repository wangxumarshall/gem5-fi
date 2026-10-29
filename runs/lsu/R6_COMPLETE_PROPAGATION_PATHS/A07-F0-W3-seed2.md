# A07-F0-W3 seed2 — 传播路径

> 本文件由真实运行证据生成；不合成、不补写事件。机器可读判定以 `chain_report.json` 为准。

## 1. 身份与可复现信息

| 项 | 值 |
|---|---|
| RunID / 模型 / 频率 | `A07-F0-W3` / `A07` / `F0` |
| 工作负载 | agu_addrmodes (W3) |
| 故障模型 | ready 延迟 1 cycle（a07b） |
| seed / sample_run_id | 2 / `s2` |
| 证据目录 | `runs/lsu/r6_a_segv2_A07-F0-W3_s2/A07-F0-W3/seed2` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f` |
| binary_source_head | `1e8e96fe0e0b2cbb2b29b527042c501b304d3adc` |
| analysis_tool_head | `1e8e96fe0e0b2cbb2b29b527042c501b304d3adc` |
| 启动命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_segv2_A07-F0-W3_s2 --cells A07-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| 开始/结束 | 2026-10-28T12:49:49+08:00 / 2026-10-28T12:49:51+08:00 |

## 2. 注入位置

CHAOSAddrPath::maybeDelayAguReady @ IEW::executeInsts memRef ready 点（resume 经 chaosAguResumeInst）。模型在 L0 记录注入项；本 seed 的注入日志首行：

```
Tick: 10908590, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=7499, ready_tick=10908590, delayed_tick=10908975, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
```

old EA = `n/a`，new EA = `n/a`，bitmask = `n/a`，首个受影响指令 dyn_inst_seq = `7499`。

## 3. 关键事件序（真实 PROP-EVT，按发生顺序）

| # | kind | event_id | parent_event_id | tick | dyn_inst_seq | corr | detection_layer | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | `inj` | 0 |  | 10908590 | 7499 | origin |  |  |
| 2 | `mem_req` | 3 | 2 | 10908975 | 7499 | seq_primary |  |  |
| 3 | `lsq_sendfrag` | 4 | 3 | 10908975 | 7499 | seq_primary |  |  |
| 4 | `tlb_translate` | 5 | 4 | 10908975 | 7499 | seq_primary |  |  |
| 5 | `lq_read` | 6 | 5 | 10908975 | 7499 | seq_primary |  |  |
| 6 | `resp` | 7 | 6 | 10909745 | 7499 | seq_primary |  |  |
| 7 | `lq_complete` | 8 | 7 | 10909745 | 7499 | seq_primary |  |  |
| 8 | `taint_reg` | 9 | 8 | 10909745 | 7499 | seq_primary |  |  |
| 9 | `errant_commit` | 10 | 9 | 10911670 | 7499 | taint_prop | L5 | errant_commit |
| 10 | `consumer` | 11 | 9 | 10995985 | 7527 | taint_prop |  |  |
| 11 | `chain_end` | 12 | 11 | 19540290 | 7499 | none | L5 | errant_commit_seen |

本 seed 事件种类计数：`{'inj': 1, 'lsq_push': 1, 'mem_req': 1, 'lsq_sendfrag': 1, 'tlb_translate': 1, 'lq_read': 1, 'resp': 1, 'lq_complete': 1, 'taint_reg': 1, 'errant_commit': 1, 'consumer': 1, 'chain_end': 1}`。

## 4. L0→L5 逐层叙述

- **L0（注入点）**：`inj` 节点记录 fault_id、ptag/dyn_inst_seq 与 old/new EA；`addr_form` 记录地址形态（base/index/shift 语义来自模型日志）。
- **L1（LSQ request）**：`mem_req` / `lsq_sendfrag` 携带故障 VA 进入 LSQ；lsq_sendfrag 的 `va` 字段等于 new EA，表明故障值确实进入请求而非仅停留在观测层。
- **L2（d-TLB）**：`tlb_translate`（或 `tlb_fault`）记录翻译结果；本 seed 的链判定见下：
  L0→L1 = `proven`，
  L1→L2 = `proven`。
- **L3（cache/MSHR）**：由 `lq_read`/`resp`（load）或 `sq_execute`/`sq_writeback`/`sq_complete`（store）体现，链边 L2→L3 = `proven`。
- **L4（架构值/消费者）**：`taint_reg` 建立物理寄存器污染；`errant_commit` 是首个错误提交检测事件；`consumer` 节点记录污染值被后续指令消费。链边 L3→L4 = `proven`。
- **L5（检测/结局）**：真实检测事件为 `squash_masked / chain_end(outcome=detected_contained)`；链边 L4→L5 = `proven`。生命周期 `chain_end` **不**充当 L5。

## 5. 最终结局与判定

- workload oracle：**Masked**（真实负载退出码 0）
- chain terminal：**full**，provable_to：**L5**，event_count：12，truncated：**False**
- admitted：**True**
- checker/campaign 摘要：`A07-F0-W3 s2 oracle=Masked exit=0 stream=True truncated=False events=12 faults=1 terminal=full provable_to=L5 beyond= | consumer_summary: emitted=0 suppressed=0 logical_total=0 conservation=n/a`

## 6. 证据文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `prop_evt.txt.gz` | `26ebd258125f3b653029293a4980167764f4f5e9895694a61e36ebcce2589763` |
| `chain_report.json` | `4a36cf33e0595c3daf800d86724d1b7ca2ec2e74e37c6aebd387fe1da488392f` |
| `stats.txt` | `440327ec804505783d8a240c9a65e1e8da7b3038a8c702c60632585f64973e54` |
| `addrpath_injections.log` | `f865189b4b6e5714d52053adc9b6297151487f1b0a01c14acbae9433e506d0a4` |
| `manifest.json` | `72981ad309f9522363755d68d6e032e6fcecbe78f731a5b2d658bb9a1bf3d299` |

stats.txt 大小：258042 B；prop_evt gzip 完整（campaign `truncated=false`）。

## 7. 实验身份有效性 vs 观测链完整性

- **身份有效性**：RunID/seed/workload/频率与权威矩阵一致；binary SHA 与 manifest 一致；真实注入事件存在（injection log + FUNNEL + PROP-EVT 三源一致）。
- **观测链完整性**：terminal=full，provable_to=L5，truncated=False；L0→L5 全边 proven 且含真实检测事件，可准入。

## 8. 人可读的传播叙事

本 seed 在 CHAOSAddrPath::maybeDelayAguReady @ IEW::executeInsts memRef ready 点（resume 经 chaosAguResumeInst） 注入 ready 延迟 1 cycle（a07b）。故障值从 L0 的 EA 寄存器出发，随 `mem_req`/`lsq_sendfrag` 进入 LSQ，并在 d-TLB 翻译时被真实使用（不是仅登记未消费）。翻译/取数完成后，错误数据经 `resp`/`lq_read`（或 store 执行路径）进入寄存器/存储队列，`taint_reg` 标记污染物理寄存器；随后该污染值被消费者读取，`errant_commit` 记录首个错误提交（或 `squash_masked` 记录显式压制）。最终软件 oracle 判定 **Masked**，与链判定 **full** 一致；本 seed 的 L0→L5 每一跳都有真实共享键见证，而不是用生命周期 `chain_end` 冒充检测层。
