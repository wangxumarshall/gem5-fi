# A02-F2-W9 seed1 — 传播路径

> 本文件由真实运行证据生成；不合成、不补写事件。机器可读判定以 `chain_report.json` 为准。

## 1. 身份与可复现信息

| 项 | 值 |
|---|---|
| RunID / 模型 / 频率 | `A02-F2-W9` / `A02` / `F2` |
| 工作负载 | gap_bfs (W9) |
| 故障模型 | 双比特翻转（相邻） |
| seed / sample_run_id | 1 / `s1` |
| 证据目录 | `runs/lsu/r6_a_segv2_A02-F2-W9_s1/A02-F2-W9/seed1` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f` |
| binary_source_head | `1e8e96fe0e0b2cbb2b29b527042c501b304d3adc` |
| analysis_tool_head | `1e8e96fe0e0b2cbb2b29b527042c501b304d3adc` |
| 启动命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_segv2_A02-F2-W9_s1 --cells A02-F2-W9 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| 开始/结束 | 2026-10-28T12:49:33+08:00 / 2026-10-28T12:49:39+08:00 |

## 2. 注入位置

CHAOSAddrPath::maybeCorrupt @ LSQ::sendFragmentToTranslation，EA 进入 d-TLB 之前。模型在 L0 记录注入项；本 seed 的注入日志首行：

```
Tick: 152693310, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x494dc8, new_vaddr=0x494dce, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x6 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

old EA = `0x494dc8`，new EA = `0x494dce`，bitmask = `0x6`，首个受影响指令 dyn_inst_seq = `581132`。

## 3. 关键事件序（真实 PROP-EVT，按发生顺序）

| # | kind | event_id | parent_event_id | tick | dyn_inst_seq | corr | detection_layer | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | `inj` | 1 |  | 152693310 | 581132 | origin |  |  |
| 2 | `addr_form` | 2 | 1 | 152693310 | 581132 | origin |  |  |
| 3 | `mem_req` | 3 | 2 | 152693310 | 581132 | seq_primary |  |  |
| 4 | `lsq_sendfrag` | 4 | 3 | 152693310 | 581132 | seq_primary |  |  |
| 5 | `tlb_translate` | 5 | 4 | 152693310 | 581132 | seq_primary |  |  |
| 6 | `lq_read` | 6 | 5 | 152693310 | 581132 | seq_primary |  |  |
| 7 | `resp` | 7 | 6 | 152694080 | 581132 | seq_primary |  |  |
| 8 | `lq_complete` | 8 | 7 | 152694080 | 581132 | seq_primary |  |  |
| 9 | `taint_reg` | 9 | 8 | 152694080 | 581132 | seq_primary |  |  |
| 10 | `errant_commit` | 10 | 9 | 152696390 | 581132 | taint_prop | L5 | errant_commit |
| 11 | `consumer` | 11 | 9 | 152696390 | 581133 | taint_prop |  |  |
| 12 | `consumer` | 12 | 11 | 152696390 | 581134 | taint_prop |  |  |
| 13 | `consumer` | 13 | 11 | 152696390 | 581134 | taint_prop |  |  |
| 14 | `consumer` | 14 | 11 | 152696390 | 581134 | taint_prop |  |  |
| 15 | `inj` | 16 |  | 217744450 | 852808 | origin |  |  |
| 16 | `addr_form` | 17 | 16 | 217744450 | 852808 | origin |  |  |

本 seed 事件种类计数：`{'inj': 2, 'addr_form': 2, 'mem_req': 2, 'lsq_sendfrag': 2, 'tlb_translate': 2, 'lq_read': 1, 'resp': 1, 'lq_complete': 1, 'taint_reg': 1, 'errant_commit': 1, 'consumer': 4, 'tlb_fault': 1, 'chain_end': 2}`。

## 4. L0→L5 逐层叙述

- **L0（注入点）**：`inj` 节点记录 fault_id、ptag/dyn_inst_seq 与 old/new EA；`addr_form` 记录地址形态（base/index/shift 语义来自模型日志）。
- **L1（LSQ request）**：`mem_req` / `lsq_sendfrag` 携带故障 VA 进入 LSQ；lsq_sendfrag 的 `va` 字段等于 new EA，表明故障值确实进入请求而非仅停留在观测层。
- **L2（d-TLB）**：`tlb_translate`（或 `tlb_fault`）记录翻译结果；本 seed 的链判定见下：
  L0→L1 = `proven`，
  L1→L2 = `proven`。
- **L3（cache/MSHR）**：由 `lq_read`/`resp`（load）或 `sq_execute`/`sq_writeback`/`sq_complete`（store）体现，链边 L2→L3 = `proven`。
- **L4（架构值/消费者）**：`taint_reg` 建立物理寄存器污染；`errant_commit` 是首个错误提交检测事件；`consumer` 节点记录污染值被后续指令消费。链边 L3→L4 = `proven`。
- **L5（检测/结局）**：真实检测事件为 `errant_commit`；链边 L4→L5 = `proven`。生命周期 `chain_end` **不**充当 L5。

## 5. 最终结局与判定

- workload oracle：**Crash**（真实负载退出码 1）
- chain terminal：**full**，provable_to：**L5**，event_count：22，truncated：**False**
- admitted：**True**
- checker/campaign 摘要：`A02-F2-W9 s1 oracle=Crash exit=1 stream=True truncated=False events=22 faults=2 terminal=full provable_to=L5 beyond= | consumer_summary: emitted=0 suppressed=0 logical_total=0 conservation=n/a`

## 6. 证据文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `prop_evt.txt.gz` | `c3a4ed85c9081c8991e933377bd879aceb03a5db54d31f267e87ce77ece96c52` |
| `chain_report.json` | `b320e9487cae455486d98ccb3808e89429d3c7552f73ace978a82b3331c13008` |
| `stats.txt` | `4596046d57635aa3785966fc79326a60376e6864973232213b07fd12e13dd919` |
| `addrpath_injections.log` | `75d60287cb90ba48d550cd535005833800c46a7a897b18f6894c6a84b669eeb4` |
| `manifest.json` | `16c42b8a6dd1d7707c9beb46cd2d1d66de517366fde495da186e05fdada7fdf6` |

stats.txt 大小：257342 B；prop_evt gzip 完整（campaign `truncated=false`）。

## 7. 实验身份有效性 vs 观测链完整性

- **身份有效性**：RunID/seed/workload/频率与权威矩阵一致；binary SHA 与 manifest 一致；真实注入事件存在（injection log + FUNNEL + PROP-EVT 三源一致）。
- **观测链完整性**：terminal=full，provable_to=L5，truncated=False；L0→L5 全边 proven 且含真实检测事件，可准入。

## 8. 人可读的传播叙事

本 seed 在 CHAOSAddrPath::maybeCorrupt @ LSQ::sendFragmentToTranslation，EA 进入 d-TLB 之前 注入 双比特翻转（相邻）。故障值从 L0 的 EA 寄存器出发，随 `mem_req`/`lsq_sendfrag` 进入 LSQ，并在 d-TLB 翻译时被真实使用（不是仅登记未消费）。翻译/取数完成后，错误数据经 `resp`/`lq_read`（或 store 执行路径）进入寄存器/存储队列，`taint_reg` 标记污染物理寄存器；随后该污染值被消费者读取，`errant_commit` 记录首个错误提交（或 `squash_masked` 记录显式压制）。最终软件 oracle 判定 **Crash**，与链判定 **full** 一致；本 seed 的 L0→L5 每一跳都有真实共享键见证，而不是用生命周期 `chain_end` 冒充检测层。
