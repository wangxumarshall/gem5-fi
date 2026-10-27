# T07-F0-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T07-F0-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T07`）
- fault type / 子模型：`false_hit`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F0`／生效 `F0`／tier enabled=`0`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1 --cells T07-F0-W4 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:54:06+08:00`，end=`2026-10-28T02:24:09+08:00`）
- 运行目录进程：gem5_pid=`3354376`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：4610（chain_report.event_count=`4610`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`237950351460`，event_id=`0`
- 被改字段：`false_hit`；before=`miss`，after=`hit`
- 注入器原始日志行：

```
Tick: 237950351460, Site: arm_tlb_lookup, VA: 0xffffff807fbce090, CAM: miss -> hit, FaultType: false_hit
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`20`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 21 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 4610 个事件，为可读性第 3 章只逐条叙述**主链** 21 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=237950351460`，`corr=origin`，`request_id=109`，`dyn_inst_seq=109`，`field=false_hit`，`before=miss`，`after=hit`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=237950351460`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`walk_id=0`，`va=ffffff807fbce090`，`entry_index=-1`，`way=0`，`field=post_lookup`，`before=miss`，`after=hit`，`state_before=entry=none`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090`
  该事件把 TLB 表项的状态/字段从 `entry=none` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=237950351460`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`va=ffffff807fbce090`，`field=false_hit`，`state_before=miss`，`state_after=hit`
  该事件把 TLB 表项的状态/字段从 `miss` 变为 `hit`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=237950351460`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`walk_id=0`，`va=ffffff807fbce090`，`pa=81d75090`，`entry_index=-1`，`way=0`，`field=effective_pa_changed`，`before=0`，`after=81d75090`，`state_before=entry=none`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `0` 变为 `81d75090`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=4`，`parent_event_id=3`，`tick=237950351460`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`va=ffffff807fbce090`，`lq_idx=1`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=5`，`parent_event_id=4`，`tick=237950351460`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`va=ffffff807fbce090`，`pa=81d75090`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=6`，`parent_event_id=5`，`tick=237950351460`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`pa=81d75090`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=7`，`parent_event_id=6`，`tick=237950351460`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`cache_line=81d75090`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=8`，`parent_event_id=7`，`tick=237950351793`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`va=ffffff807fbce090`，`pa=81d75080`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=9`，`parent_event_id=8`，`tick=237950351793`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`pa=81d75080`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10`，`parent_event_id=9`，`tick=237950351793`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`cache_line=81d75080`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=11`，`parent_event_id=10`，`tick=237950399412`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`cache_line=81d75080`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=12`，`parent_event_id=11`，`tick=237950399412`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`pa=81d75080`，`cache_line=81d75080`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=13`，`parent_event_id=12`，`tick=237950399412`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`cache_line=81d75080`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=14`，`parent_event_id=13`，`tick=237950400078`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`cache_line=81d75080`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=15`，`parent_event_id=14`，`tick=237950400078`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`pa=81d75080`，`cache_line=81d75080`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=16`，`parent_event_id=15`，`tick=237950400078`，`corr=addr_fallback`，`request_id=109`，`dyn_inst_seq=109`，`cache_line=81d75080`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `resp`（L4 内存响应）

- `event_id=17`，`parent_event_id=16`，`tick=237950400411`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`va=81d75090`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `lq_complete`（L4 载入完成）

- `event_id=18`，`parent_event_id=17`，`tick=237950400411`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`va=ffffff807fbce090`，`pa=81d75090`，`lq_idx=1`

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=19`，`parent_event_id=18`，`tick=237950400411`，`corr=seq_primary`，`request_id=109`，`dyn_inst_seq=109`，`va=81d75090`，`before=clean`，`after=tainted`，`arch_reg=28`，`phys_reg=96`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `errant_commit`（L5 错误提交）

- `event_id=20`，`parent_event_id=19`，`tick=237950401077`，`corr=taint_prop`，`dyn_inst_seq=109`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=88`，`pc=ffffffc0080116d8`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `109` | `—` | `miss` → `hit` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `109` | `ffffff807fbce090` | `entry=none` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `109` | `ffffff807fbce090` | `miss` → `hit` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `109` | `81d75090` | `entry=none` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090` |
| 4 | `lq_read` | L3 | LQ | `109` | `ffffff807fbce090` | — |
| 5 | `cache_access` | L3 | L1D | `109` | `81d75090` | — |
| 6 | `cache_return` | L3 | L1D | `109` | `81d75090` | — |
| 7 | `mshr_alloc` | L3 | MSHR | `109` | `81d75090` | `` → `mshr_allocated` |
| 8 | `cache_access` | L3 | L1D | `109` | `81d75080` | — |
| 9 | `cache_return` | L3 | L1D | `109` | `81d75080` | — |
| 10 | `mshr_alloc` | L3 | MSHR | `109` | `81d75080` | `` → `mshr_allocated` |
| 11 | `mshr_fill` | L3 | MSHR | `109` | `81d75080` | `` → `filled` |
| 12 | `cache_fill` | L3 | L1D | `109` | `81d75080` | — |
| 13 | `mshr_free` | L3 | MSHR | `109` | `81d75080` | `` → `mshr_freed` |
| 14 | `mshr_fill` | L3 | MSHR | `109` | `81d75080` | `` → `filled` |
| 15 | `cache_fill` | L3 | L1D | `109` | `81d75080` | — |
| 16 | `mshr_free` | L3 | MSHR | `109` | `81d75080` | `` → `mshr_freed` |
| 17 | `resp` | L4 | LSU | `109` | `81d75090` | — |
| 18 | `lq_complete` | L4 | LQ | `109` | `81d75090` | — |
| 19 | `taint_reg` | L4 | PRF/提交 | `109` | `81d75090` | `clean` → `tainted` |
| 20 | `errant_commit` | L5 | commit | `109` | `—` | — |


（第 4 章仅逐条列出主链 21 个事件；其余 4589 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 1281 | 21 | 4199 |
| `cache_access` | 528 | 5 | 3173 |
| `cache_return` | 528 | 6 | 3174 |
| `resp` | 410 | 17 | 2858 |
| `taint_reg` | 410 | 19 | 2859 |
| `request_fork` | 409 | 4294967296 | 4294967704 |
| `pf_demand` | 223 | 673 | 3170 |
| `mshr_merge` | 155 | 27 | 2815 |
| `mshr_fill` | 115 | 11 | 2824 |
| `cache_fill` | 115 | 12 | 2825 |
| `mshr_free` | 115 | 13 | 2826 |
| `mshr_alloc` | 94 | 7 | 2820 |
| `cache_evict` | 60 | 2872 | 3171 |
| `cache_writeback` | 60 | 2873 | 3172 |
| `pf_fill` | 44 | 769 | 2726 |
| `pf_queue` | 29 | 655 | 2504 |
| `pf_issue` | 26 | 670 | 2508 |
| `inj` | 1 | 0 | 0 |
| `tlb_lookup` | 1 | 1 | 1 |
| `tlb_state` | 1 | 2 | 2 |
| `tlb_translate_result` | 1 | 3 | 3 |
| `lq_read` | 1 | 4 | 4 |
| `lq_complete` | 1 | 18 | 18 |
| `errant_commit` | 1 | 20 | 20 |
| `chain_end` | 1 | 4200 | 4200 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_state) → 3(tlb_translate_result) → 4(lq_read) → 5(cache_access) → 6(cache_return) → 7(mshr_alloc) → 8(cache_access) → 9(cache_return) → 10(mshr_alloc) → 11(mshr_fill) → 12(cache_fill) → 13(mshr_free) → 14(mshr_fill) → 15(cache_fill) → 16(mshr_free) → 17(resp) → 18(lq_complete) → 19(taint_reg) → 20(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 237950351460 | `origin` | `109` | 1 |
| 1 | 0 | 237950351460 | `seq_primary` | `109` | 1 |
| 2 | 1 | 237950351460 | `seq_primary` | `109` | 1 |
| 3 | 2 | 237950351460 | `seq_primary` | `109` | 1 |
| 4 | 3 | 237950351460 | `seq_primary` | `109` | 1 |
| 5 | 4 | 237950351460 | `addr_fallback` | `109` | 1 |
| 6 | 5 | 237950351460 | `addr_fallback` | `109` | 1 |
| 7 | 6 | 237950351460 | `addr_fallback` | `109` | 1 |
| 8 | 7 | 237950351793 | `addr_fallback` | `109` | 1 |
| 9 | 8 | 237950351793 | `addr_fallback` | `109` | 1 |
| 10 | 9 | 237950351793 | `addr_fallback` | `109` | 1 |
| 11 | 10 | 237950399412 | `addr_fallback` | `109` | 1 |
| 12 | 11 | 237950399412 | `addr_fallback` | `109` | 1 |
| 13 | 12 | 237950399412 | `addr_fallback` | `109` | 1 |
| 14 | 13 | 237950400078 | `addr_fallback` | `109` | 1 |
| 15 | 14 | 237950400078 | `addr_fallback` | `109` | 1 |
| 16 | 15 | 237950400078 | `addr_fallback` | `109` | 1 |
| 17 | 16 | 237950400411 | `seq_primary` | `109` | 1 |
| 18 | 17 | 237950400411 | `seq_primary` | `109` | 1 |
| 19 | 18 | 237950400411 | `seq_primary` | `109` | 1 |
| 20 | 19 | 237950401077 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Timeout`
- **运行终止方式**：进程在 `fs-timeout` 墙钟上限处被优雅终止（run.err `TIMEOUT triggered=True`, `graceful=True`）；这不是结局本身——链的终局由终止前已发生的真实事件决定，且证据流完整未截断。
- 结局形成：终局见证是 `errant_commit`（event_id=20），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`false_hit` 对一次未命中**伪造命中**：MMU 因此不发起 page-walk，直接使用被伪造表项的 pfn 形成 PA（干净基线为 0，故 `effective_pa_changed`）。本 seed 的真实结局取决于该错误 PA 是否被后续访问消费，见主链与第 5 章。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`259782160`，eligible=`62`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1/prop_evt.txt.gz` — SHA-256 `ec7bc1e5ff861ea0e64457d7fac141a3db3fd1bc28cb9ccbef57b83a346e91b3`（206951 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1/chain_report.json` — SHA-256 `9e6649c11ff108c6b6a0eae2e461efcf7ea95642f89a59c2ba8539fc434471a7`（1136180 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1/stats.txt` — SHA-256 `2897870ee1395e1ad8e35172ef1c85c8748efbbf3627b9460c7be5f0d9b13f64`（362577 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1/run.out` — SHA-256 `d35ed3eb1e759383fd5212263b885bf20e26e3dfc6462182734c48a1d79af2b6`（2128 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1/run.err` — SHA-256 `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900`（129 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/T07-F0-W4/seed1/armtlb_injections.log` — SHA-256 `efdbd1c37a1477f1bd3bc6e40d6ba94f7f3edc1b25a046d217cdbc01e0e5f84b`（105 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1/manifest.json` — SHA-256 `bf6995b89ed26634b48b640880f8eab86c03d6dbe447fc334a1016e7d3e6f770`（2104 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

