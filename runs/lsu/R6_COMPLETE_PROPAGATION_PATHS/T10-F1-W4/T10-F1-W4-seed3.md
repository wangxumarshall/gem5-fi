# T10-F1-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F1-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F1`／生效 `F1`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3 --cells T10-F1-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:58:43+08:00`，end=`2026-10-28T01:00:34+08:00`）
- 运行目录进程：gem5_pid=`3057200`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：25388（chain_report.event_count=`25388`）
- fault_id 数：3

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`239629862268`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`5536042`，request_id=`5536042`，VA=`0x7fe7c61d40`
- 被改字段：`bit_flip`；before=`83111`，after=`87111`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip (lookup path now polls lsuTrigger; tier=F1; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
    protection: model=none bits=1 -> Raw
Tick: 239629862268, Site: arm_tlb_lookup_hit, VA: 0x7fe7c61d40, old_pfn: 0x83111, new_pfn: 0x87111, FaultType: bit_flip, Mask: 0x4000, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 241738137882, Site: arm_tlb_lookup_hit, VA: 0xffffffc00948bf78, old_pfn: 0x81d4d, new_pfn: 0x91d4d, FaultType: bit_flip, Mask: 0x10000, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 242538826392, Site: arm_tlb_lookup_hit, VA: 0xffffffc00948bac0, old_pfn: 0x81d4d, new_pfn: 0x81d6d, FaultType: bit_flip, Mask: 0x20, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`45`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 22 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 25388 个事件，为可读性第 3 章只逐条叙述**主链** 22 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=239629862268`，`corr=origin`，`request_id=5536042`，`dyn_inst_seq=5536042`，`va=7fe7c61d40`，`field=bit_flip`，`before=83111`，`after=87111`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=239629862268`，`corr=seq_primary`，`request_id=5536042`，`dyn_inst_seq=5536042`，`walk_id=0`，`va=7fe7c61d40`，`entry_index=23`，`way=-1`，`field=post_lookup`，`before=83111`，`after=87111`，`state_before=vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40`，`state_after=vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40`
  该事件把 TLB 表项的状态/字段从 `vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40` 变为 `vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=239629862268`，`corr=seq_primary`，`request_id=5536042`，`dyn_inst_seq=5536042`，`va=7fe7c61d40`，`pa=87111d40`，`field=bit_flip`，`before=83111`，`after=87111`，`state_before=83111d40`，`state_after=87111d40`
  该事件把 TLB 表项的状态/字段从 `83111d40` 变为 `87111d40`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=239629862268`，`corr=seq_primary`，`request_id=5536042`，`dyn_inst_seq=5536042`，`walk_id=0`，`va=7fe7c61d40`，`pa=87111d40`，`entry_index=23`，`way=-1`，`field=effective_pa_changed`，`before=83111d40`，`after=87111d40`，`state_before=vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40`，`state_after=vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `83111d40` 变为 `87111d40`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=4`，`parent_event_id=3`，`tick=239629862268`，`corr=seq_primary`，`request_id=5536042`，`dyn_inst_seq=5536042`，`va=7fe7c61d40`，`lq_idx=594678`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=5`，`parent_event_id=4`，`tick=239629862268`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`va=7fe7c61d40`，`pa=87111d40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=6`，`parent_event_id=5`，`tick=239629862268`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`pa=87111d40`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=7`，`parent_event_id=6`，`tick=239629862268`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`cache_line=87111d40`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=8`，`parent_event_id=7`，`tick=239629862601`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`va=7fe7c61d40`，`pa=87111d40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=9`，`parent_event_id=8`，`tick=239629862601`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`pa=87111d40`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10`，`parent_event_id=9`，`tick=239629862601`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`cache_line=87111d40`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=35`，`parent_event_id=10`，`tick=239629921542`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`cache_line=87111d40`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=36`，`parent_event_id=35`，`tick=239629921542`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`pa=87111d40`，`cache_line=87111d40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=37`，`parent_event_id=36`，`tick=239629921542`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`cache_line=87111d40`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=38`，`parent_event_id=37`，`tick=239629922208`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`cache_line=87111d40`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=39`，`parent_event_id=38`，`tick=239629922208`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`pa=87111d40`，`cache_line=87111d40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=40`，`parent_event_id=39`，`tick=239629922208`，`corr=addr_fallback`，`request_id=5536042`，`dyn_inst_seq=5536042`，`cache_line=87111d40`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `resp`（L4 内存响应）

- `event_id=41`，`parent_event_id=40`，`tick=239629922541`，`corr=seq_primary`，`dyn_inst_seq=5536042`，`va=0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `lq_complete`（L4 载入完成）

- `event_id=42`，`parent_event_id=41`，`tick=239629922541`，`corr=seq_primary`，`request_id=0`，`dyn_inst_seq=5536042`，`va=7fe7c61d32`，`pa=0`，`lq_idx=594678`

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=43`，`parent_event_id=42`，`tick=239629922541`，`corr=seq_primary`，`dyn_inst_seq=5536042`，`va=0`，`before=clean`，`after=tainted`，`arch_reg=4`，`phys_reg=68`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `taint_reg`（L4 寄存器污染）

- `event_id=44`，`parent_event_id=43`，`tick=239629922541`，`corr=seq_primary`，`dyn_inst_seq=5536042`，`va=0`，`before=clean`，`after=tainted`，`arch_reg=5`，`phys_reg=153`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.22 `errant_commit`（L5 错误提交）

- `event_id=45`，`parent_event_id=44`，`tick=239629923207`，`corr=taint_prop`，`dyn_inst_seq=5536042`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=3687869`，`pc=7f82a0afd8`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `5536042` | `7fe7c61d40` | `83111` → `87111` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `5536042` | `7fe7c61d40` | `vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40` → `vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `5536042` | `87111d40` | `83111d40` → `87111d40` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `5536042` | `87111d40` | `vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40` → `vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40` |
| 4 | `lq_read` | L3 | LQ | `5536042` | `7fe7c61d40` | — |
| 5 | `cache_access` | L3 | L1D | `5536042` | `87111d40` | — |
| 6 | `cache_return` | L3 | L1D | `5536042` | `87111d40` | — |
| 7 | `mshr_alloc` | L3 | MSHR | `5536042` | `87111d40` | `` → `mshr_allocated` |
| 8 | `cache_access` | L3 | L1D | `5536042` | `87111d40` | — |
| 9 | `cache_return` | L3 | L1D | `5536042` | `87111d40` | — |
| 10 | `mshr_alloc` | L3 | MSHR | `5536042` | `87111d40` | `` → `mshr_allocated` |
| 35 | `mshr_fill` | L3 | MSHR | `5536042` | `87111d40` | `` → `filled` |
| 36 | `cache_fill` | L3 | L1D | `5536042` | `87111d40` | — |
| 37 | `mshr_free` | L3 | MSHR | `5536042` | `87111d40` | `` → `mshr_freed` |
| 38 | `mshr_fill` | L3 | MSHR | `5536042` | `87111d40` | `` → `filled` |
| 39 | `cache_fill` | L3 | L1D | `5536042` | `87111d40` | — |
| 40 | `mshr_free` | L3 | MSHR | `5536042` | `87111d40` | `` → `mshr_freed` |
| 41 | `resp` | L4 | LSU | `5536042` | `0` | — |
| 42 | `lq_complete` | L4 | LQ | `0` | `0` | — |
| 43 | `taint_reg` | L4 | PRF/提交 | `5536042` | `0` | `clean` → `tainted` |
| 44 | `taint_reg` | L4 | PRF/提交 | `5536042` | `0` | `clean` → `tainted` |
| 45 | `errant_commit` | L5 | commit | `5536042` | `—` | — |


（第 4 章仅逐条列出主链 22 个事件；其余 25366 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `taint_reg` | 4561 | 43 | 21442 |
| `cache_access` | 4031 | 5 | 21439 |
| `cache_return` | 4031 | 6 | 21440 |
| `request_fork` | 3942 | 4294967296 | 4294971237 |
| `resp` | 3776 | 41 | 21441 |
| `consumer` | 2562 | 46 | 14620 |
| `lq_complete` | 1448 | 42 | 21432 |
| `mshr_merge` | 269 | 25 | 19924 |
| `mshr_alloc` | 161 | 7 | 19927 |
| `mshr_fill` | 160 | 35 | 19984 |
| `cache_fill` | 160 | 36 | 19985 |
| `mshr_free` | 160 | 37 | 19986 |
| `squash_masked` | 102 | 86 | 21168 |
| `inj` | 3 | 0 | 14621 |
| `tlb_lookup` | 3 | 1 | 14622 |
| `tlb_pfn` | 3 | 2 | 14623 |
| `tlb_translate_result` | 3 | 3 | 14624 |
| `chain_end` | 3 | 21443 | 21445 |
| `lq_read` | 2 | 4 | 14625 |
| `cache_evict` | 2 | 12580 | 13443 |
| `cache_writeback` | 2 | 12581 | 13444 |
| `errant_commit` | 1 | 45 | 45 |
| `sq_execute` | 1 | 1375 | 1375 |
| `sq_writeback` | 1 | 1376 | 1376 |
| `sq_complete` | 1 | 1409 | 1409 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(lq_read) → 5(cache_access) → 6(cache_return) → 7(mshr_alloc) → 8(cache_access) → 9(cache_return) → 10(mshr_alloc) → 35(mshr_fill) → 36(cache_fill) → 37(mshr_free) → 38(mshr_fill) → 39(cache_fill) → 40(mshr_free) → 41(resp) → 42(lq_complete) → 43(taint_reg) → 44(taint_reg) → 45(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 239629862268 | `origin` | `5536042` | 1 |
| 1 | 0 | 239629862268 | `seq_primary` | `5536042` | 1 |
| 2 | 1 | 239629862268 | `seq_primary` | `5536042` | 1 |
| 3 | 2 | 239629862268 | `seq_primary` | `5536042` | 1 |
| 4 | 3 | 239629862268 | `seq_primary` | `5536042` | 1 |
| 5 | 4 | 239629862268 | `addr_fallback` | `5536042` | 1 |
| 6 | 5 | 239629862268 | `addr_fallback` | `5536042` | 1 |
| 7 | 6 | 239629862268 | `addr_fallback` | `5536042` | 1 |
| 8 | 7 | 239629862601 | `addr_fallback` | `5536042` | 1 |
| 9 | 8 | 239629862601 | `addr_fallback` | `5536042` | 1 |
| 10 | 9 | 239629862601 | `addr_fallback` | `5536042` | 1 |
| 35 | 10 | 239629921542 | `addr_fallback` | `5536042` | 1 |
| 36 | 35 | 239629921542 | `addr_fallback` | `5536042` | 1 |
| 37 | 36 | 239629921542 | `addr_fallback` | `5536042` | 1 |
| 38 | 37 | 239629922208 | `addr_fallback` | `5536042` | 1 |
| 39 | 38 | 239629922208 | `addr_fallback` | `5536042` | 1 |
| 40 | 39 | 239629922208 | `addr_fallback` | `5536042` | 1 |
| 41 | 40 | 239629922541 | `seq_primary` | `—` | 1 |
| 42 | 41 | 239629922541 | `seq_primary` | `0` | 1 |
| 43 | 42 | 239629922541 | `seq_primary` | `—` | 1 |
| 44 | 43 | 239629922541 | `seq_primary` | `—` | 1 |
| 45 | 44 | 239629923207 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=45），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`3442472`，eligible=`3442472`，injected=`3`（日志应用行 3 条），activated=`3`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3/prop_evt.txt.gz` — SHA-256 `dff2cdb899d70c913ef947515c2334d489c76324510bb43d446b8485b4eab18b`（963697 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3/chain_report.json` — SHA-256 `79811817f1dd15fd510e08bca28340de0d04f4d68aab92a303c9d6a9e7a32c7d`（2236046 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3/stats.txt` — SHA-256 `51755505ce119005c52629545bf9c8502901c114c0de667eab7167f5ac6a7fc0`（419893 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3/run.out` — SHA-256 `84bef630bd8c2db18d08a87f07ea60d64a8725e50bb3dc19b4de2460734b4ed4`（11832 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3/run.err` — SHA-256 `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36`（1873 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/T10-F1-W4/seed3/armtlb_injections.log` — SHA-256 `32c072f0e35ad861320a7b0697d30f1d8dbb46a732a44a560365f1378ea1ec39`（775 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3/manifest.json` — SHA-256 `3c28c5b683046a0a1e2ed6546a43def1dc2433a4b8c63b6e2506769a00127bd7`（2105 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

