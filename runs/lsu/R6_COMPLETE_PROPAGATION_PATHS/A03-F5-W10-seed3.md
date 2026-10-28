# A03-F5-W10 seed3 — 传播路径

> 本文件由真实运行证据生成；不合成、不补写事件。机器可读判定以 `chain_report.json` 为准。

## 1. 身份与可复现信息

| 项 | 值 |
|---|---|
| RunID / 模型 / 频率 | `A03-F5-W10` / `A03` / `F5` |
| 工作负载 | sqlite_like/流式负载 (W10) |
| 故障模型 | EA bit stuck（持续） |
| seed / sample_run_id | 3 / `s3` |
| 证据目录 | `runs/lsu/r6_a_fix2_A03-F5-W10_s3/A03-F5-W10/seed3` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary_sha256 | `37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f` |
| binary_source_head | `1e8e96fe0e0b2cbb2b29b527042c501b304d3adc` |
| analysis_tool_head | `1e8e96fe0e0b2cbb2b29b527042c501b304d3adc` |
| 启动命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_fix2_A03-F5-W10_s3 --cells A03-F5-W10 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| 开始/结束 | 2026-10-28T12:54:35+08:00 / 2026-10-28T12:54:37+08:00 |

## 2. 注入位置

CHAOSAddrPath::maybeCorrupt @ LSQ::sendFragmentToTranslation，每个 eligible 事件施加同一 stuck 掩码。模型在 L0 记录注入项；本 seed 的注入日志首行：

```
Tick: 80080, Site: lsq_sendFragmentToTranslation, mode=a03_stuck0, old_vaddr=0x7ffffefdd0, new_vaddr=0x7ffffef9d0, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x400 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

old EA = `0x7ffffefdd0`，new EA = `0x7ffffef9d0`，bitmask = `0x400`，首个受影响指令 dyn_inst_seq = `5`。

## 3. 关键事件序（真实 PROP-EVT，按发生顺序）

| # | kind | event_id | parent_event_id | tick | dyn_inst_seq | corr | detection_layer | outcome |
|---|---|---|---|---|---|---|---|---|
| 1 | `inj` | 1 |  | 80080 | 5 | origin |  |  |
| 2 | `addr_form` | 2 | 1 | 80080 | 5 | origin |  |  |
| 3 | `mem_req` | 3 | 2 | 80080 | 5 | seq_primary |  |  |
| 4 | `lsq_sendfrag` | 4 | 3 | 80080 | 5 | seq_primary |  |  |
| 5 | `tlb_translate` | 5 | 4 | 80080 | 5 | seq_primary |  |  |
| 6 | `lq_read` | 6 | 5 | 80080 | 5 | seq_primary |  |  |
| 7 | `inj` | 8 |  | 140910 | 18 | origin |  |  |
| 8 | `addr_form` | 9 | 8 | 140910 | 18 | origin |  |  |
| 9 | `mem_req` | 10 | 9 | 140910 | 18 | seq_primary |  |  |
| 10 | `lsq_sendfrag` | 11 | 10 | 140910 | 18 | seq_primary |  |  |
| 11 | `tlb_translate` | 12 | 11 | 140910 | 18 | seq_primary |  |  |
| 12 | `inj` | 15 |  | 141295 | 19 | origin |  |  |
| 13 | `addr_form` | 16 | 15 | 141295 | 19 | origin |  |  |
| 14 | `mem_req` | 17 | 16 | 141295 | 19 | seq_primary |  |  |
| 15 | `lsq_sendfrag` | 18 | 17 | 141295 | 19 | seq_primary |  |  |
| 16 | `tlb_translate` | 19 | 18 | 141295 | 19 | seq_primary |  |  |

本 seed 事件种类计数：`{'inj': 89, 'addr_form': 89, 'mem_req': 89, 'lsq_sendfrag': 89, 'tlb_translate': 89, 'lq_read': 28, 'sq_execute': 62, 'resp': 84, 'lq_complete': 26, 'taint_reg': 91, 'errant_commit': 1, 'consumer': 37, 'sq_writeback': 61, 'sq_complete': 58, 'chain_end': 89}`。

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
- chain terminal：**full**，provable_to：**L5**，event_count：982，truncated：**False**
- admitted：**True**
- checker/campaign 摘要：`A03-F5-W10 s3 oracle=Crash exit=1 stream=True truncated=False events=982 faults=89 terminal=full provable_to=L5 beyond= | consumer_summary: emitted=10 suppressed=11 logical_total=21 conservation=ok`

## 6. 证据文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `prop_evt.txt.gz` | `66fb82844d69f37b7c95d12d05017932696820701aa33088a24002fef4e2f069` |
| `chain_report.json` | `c411751025c98879bc1c4892209592b9236fa1297b1f1f2d73ae71f22ddfad9b` |
| `stats.txt` | `ec3e02f0df26c8239f85765f5abaaa840c2be649cea3b6b06225586f80e3f157` |
| `addrpath_injections.log` | `1ad06b3e3297e06d12c82d5b6c7271a1436051ca52936dc4fbf60840560efe41` |
| `manifest.json` | `790b289325c9c9e64acffbdc54478b7079988b4a4cf165adf0621cd004a04789` |

stats.txt 大小：238928 B；prop_evt gzip 完整（campaign `truncated=false`）。

## 7. 实验身份有效性 vs 观测链完整性

- **身份有效性**：RunID/seed/workload/频率与权威矩阵一致；binary SHA 与 manifest 一致；真实注入事件存在（injection log + FUNNEL + PROP-EVT 三源一致）。
- **观测链完整性**：terminal=full，provable_to=L5，truncated=False；L0→L5 全边 proven 且含真实检测事件，可准入。

## 8. 人可读的传播叙事

本 seed 在 CHAOSAddrPath::maybeCorrupt @ LSQ::sendFragmentToTranslation，每个 eligible 事件施加同一 stuck 掩码 注入 EA bit stuck（持续）。故障值从 L0 的 EA 寄存器出发，随 `mem_req`/`lsq_sendfrag` 进入 LSQ，并在 d-TLB 翻译时被真实使用（不是仅登记未消费）。翻译/取数完成后，错误数据经 `resp`/`lq_read`（或 store 执行路径）进入寄存器/存储队列，`taint_reg` 标记污染物理寄存器；随后该污染值被消费者读取，`errant_commit` 记录首个错误提交（或 `squash_masked` 记录显式压制）。最终软件 oracle 判定 **Crash**，与链判定 **full** 一致；本 seed 的 L0→L5 每一跳都有真实共享键见证，而不是用生命周期 `chain_end` 冒充检测层。
