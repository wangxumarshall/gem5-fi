# T10-F0-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F0-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F0`／生效 `F0`／tier enabled=`0`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3 --cells T10-F0-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:55:35+08:00`，end=`2026-10-28T00:55:53+08:00`）
- 运行目录进程：gem5_pid=`3040235`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：444（chain_report.event_count=`444`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`237950233578`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`31`，request_id=`31`，VA=`0xffffffc009483eb0`
- 被改字段：`bit_flip`；before=`81d75`，after=`91d75`
- 注入器原始日志行：

```
protection: model=none bits=1 -> Raw
Tick: 237950233578, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb0, old_pfn: 0x81d75, new_pfn: 0x91d75, FaultType: bit_flip, Mask: 0x10000, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`293`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 23 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 444 个事件，为可读性第 3 章只逐条叙述**主链** 23 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=237950233578`，`corr=origin`，`request_id=31`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`field=bit_flip`，`before=81d75`，`after=91d75`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=237950233578`，`corr=seq_primary`，`request_id=31`，`dyn_inst_seq=31`，`walk_id=0`，`va=ffffffc009483eb0`，`entry_index=0`，`way=-1`，`field=post_lookup`，`before=81d75`，`after=91d75`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=237950233578`，`corr=seq_primary`，`request_id=31`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`pa=91d75eb0`，`field=bit_flip`，`before=81d75`，`after=91d75`，`state_before=81d75eb0`，`state_after=91d75eb0`
  该事件把 TLB 表项的状态/字段从 `81d75eb0` 变为 `91d75eb0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=237950233578`，`corr=seq_primary`，`request_id=31`，`dyn_inst_seq=31`，`walk_id=0`，`va=ffffffc009483eb0`，`pa=91d75eb0`，`entry_index=0`，`way=-1`，`field=effective_pa_changed`，`before=81d75eb0`，`after=91d75eb0`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81d75eb0` 变为 `91d75eb0`，outcome=`NoFault`，contained=`0`。

### 3.5 `lsq_push`（L3 LSQ 入队）

- `event_id=4`，`parent_event_id=3`，`tick=237950233911`，`corr=seq_primary`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`field=store`，`lq_idx=-1`，`sq_idx=1`，`opcode=strxi_uop`，`pc=ffffffc008011614`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `sq_execute`（L3 存储执行）

- `event_id=5`，`parent_event_id=4`，`tick=237950233911`，`corr=seq_primary`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`state_before=issued`，`sq_idx=1`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.7 `sq_writeback`（L3 存储写回）

- `event_id=6`，`parent_event_id=5`，`tick=237950235243`，`corr=seq_primary`，`dyn_inst_seq=31`，`pa=91d75eb0`，`state_after=packet_built`，`sq_idx=1`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.8 `cache_access`（L3 L1D 访问）

- `event_id=7`，`parent_event_id=6`，`tick=237950235243`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`pa=91d75eb0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_return`（L3 L1D 返回）

- `event_id=8`，`parent_event_id=7`，`tick=237950235243`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`pa=91d75eb0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `mshr_alloc`（L3 MSHR 分配）

- `event_id=9`，`parent_event_id=8`，`tick=237950235243`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`cache_line=91d75eb0`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `cache_access`（L3 L1D 访问）

- `event_id=10`，`parent_event_id=9`，`tick=237950235576`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`pa=91d75e80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `cache_return`（L3 L1D 返回）

- `event_id=11`，`parent_event_id=10`，`tick=237950235576`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`pa=91d75e80`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `mshr_alloc`（L3 MSHR 分配）

- `event_id=12`，`parent_event_id=11`，`tick=237950235576`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`cache_line=91d75e80`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_fill`（L3 MSHR 填充）

- `event_id=64`，`parent_event_id=12`，`tick=237950294517`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`cache_line=91d75e80`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `cache_fill`（L3 L1D 填充）

- `event_id=65`，`parent_event_id=64`，`tick=237950294517`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`pa=91d75e80`，`cache_line=91d75e80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `mshr_free`（L3 MSHR 释放）

- `event_id=66`，`parent_event_id=65`，`tick=237950294517`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`cache_line=91d75e80`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_fill`（L3 MSHR 填充）

- `event_id=67`，`parent_event_id=66`，`tick=237950295183`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`cache_line=91d75e80`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `cache_fill`（L3 L1D 填充）

- `event_id=68`，`parent_event_id=67`，`tick=237950295183`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`pa=91d75e80`，`cache_line=91d75e80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `mshr_free`（L3 MSHR 释放）

- `event_id=69`，`parent_event_id=68`，`tick=237950295183`，`corr=addr_fallback`，`request_id=31`，`dyn_inst_seq=31`，`cache_line=91d75e80`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.20 `resp`（L4 内存响应）

- `event_id=73`，`parent_event_id=69`，`tick=237950295516`，`corr=seq_primary`，`request_id=31`，`dyn_inst_seq=31`，`va=91d75eb0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.21 `taint_reg`（L4 寄存器污染）

- `event_id=74`，`parent_event_id=73`，`tick=237950295516`，`corr=seq_primary`，`request_id=31`，`dyn_inst_seq=31`，`va=91d75eb0`，`before=clean`，`after=tainted`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.22 `sq_complete`（L4 存储完成）

- `event_id=75`，`parent_event_id=74`，`tick=237950295516`，`corr=seq_primary`，`dyn_inst_seq=31`，`va=ffffffc009483eb0`，`state_after=completed`，`sq_idx=1`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.23 `errant_commit`（L5 错误提交）

- `event_id=293`，`parent_event_id=75`，`tick=237951302175`，`corr=taint_prop`，`dyn_inst_seq=391`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=161`，`pc=ffffffc0087b1000`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `31` | `ffffffc009483eb0` | `81d75` → `91d75` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `31` | `ffffffc009483eb0` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `31` | `91d75eb0` | `81d75eb0` → `91d75eb0` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `31` | `91d75eb0` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0` |
| 4 | `lsq_push` | L3 | LSQ | `31` | `ffffffc009483eb0` | — |
| 5 | `sq_execute` | L3 | SQ | `31` | `ffffffc009483eb0` | `issued` → `` |
| 6 | `sq_writeback` | L3 | SQ | `31` | `91d75eb0` | `` → `packet_built` |
| 7 | `cache_access` | L3 | L1D | `31` | `91d75eb0` | — |
| 8 | `cache_return` | L3 | L1D | `31` | `91d75eb0` | — |
| 9 | `mshr_alloc` | L3 | MSHR | `31` | `91d75eb0` | `` → `mshr_allocated` |
| 10 | `cache_access` | L3 | L1D | `31` | `91d75e80` | — |
| 11 | `cache_return` | L3 | L1D | `31` | `91d75e80` | — |
| 12 | `mshr_alloc` | L3 | MSHR | `31` | `91d75e80` | `` → `mshr_allocated` |
| 64 | `mshr_fill` | L3 | MSHR | `31` | `91d75e80` | `` → `filled` |
| 65 | `cache_fill` | L3 | L1D | `31` | `91d75e80` | — |
| 66 | `mshr_free` | L3 | MSHR | `31` | `91d75e80` | `` → `mshr_freed` |
| 67 | `mshr_fill` | L3 | MSHR | `31` | `91d75e80` | `` → `filled` |
| 68 | `cache_fill` | L3 | L1D | `31` | `91d75e80` | — |
| 69 | `mshr_free` | L3 | MSHR | `31` | `91d75e80` | `` → `mshr_freed` |
| 73 | `resp` | L4 | LSU | `31` | `91d75eb0` | — |
| 74 | `taint_reg` | L4 | PRF/提交 | `31` | `91d75eb0` | `clean` → `tainted` |
| 75 | `sq_complete` | L4 | SQ | `31` | `ffffffc009483eb0` | `` → `completed` |
| 293 | `errant_commit` | L5 | commit | `391` | `—` | — |


（第 4 章仅逐条列出主链 23 个事件；其余 421 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `cache_access` | 61 | 7 | 381 |
| `cache_return` | 61 | 8 | 382 |
| `consumer` | 61 | 294 | 389 |
| `taint_reg` | 54 | 74 | 385 |
| `request_fork` | 53 | 4294967296 | 4294967348 |
| `resp` | 53 | 73 | 383 |
| `mshr_merge` | 30 | 15 | 273 |
| `mshr_alloc` | 14 | 9 | 267 |
| `mshr_fill` | 14 | 64 | 277 |
| `cache_fill` | 14 | 65 | 278 |
| `mshr_free` | 14 | 66 | 279 |
| `lq_complete` | 4 | 291 | 384 |
| `inj` | 1 | 0 | 0 |
| `tlb_lookup` | 1 | 1 | 1 |
| `tlb_pfn` | 1 | 2 | 2 |
| `tlb_translate_result` | 1 | 3 | 3 |
| `lsq_push` | 1 | 4 | 4 |
| `sq_execute` | 1 | 5 | 5 |
| `sq_writeback` | 1 | 6 | 6 |
| `sq_complete` | 1 | 75 | 75 |
| `errant_commit` | 1 | 293 | 293 |
| `squash_masked` | 1 | 319 | 319 |
| `chain_end` | 1 | 390 | 390 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(lsq_push) → 5(sq_execute) → 6(sq_writeback) → 7(cache_access) → 8(cache_return) → 9(mshr_alloc) → 10(cache_access) → 11(cache_return) → 12(mshr_alloc) → 64(mshr_fill) → 65(cache_fill) → 66(mshr_free) → 67(mshr_fill) → 68(cache_fill) → 69(mshr_free) → 73(resp) → 74(taint_reg) → 75(sq_complete) → 293(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 237950233578 | `origin` | `31` | 1 |
| 1 | 0 | 237950233578 | `seq_primary` | `31` | 1 |
| 2 | 1 | 237950233578 | `seq_primary` | `31` | 1 |
| 3 | 2 | 237950233578 | `seq_primary` | `31` | 1 |
| 4 | 3 | 237950233911 | `seq_primary` | `—` | 1 |
| 5 | 4 | 237950233911 | `seq_primary` | `—` | 1 |
| 6 | 5 | 237950235243 | `seq_primary` | `—` | 1 |
| 7 | 6 | 237950235243 | `addr_fallback` | `31` | 1 |
| 8 | 7 | 237950235243 | `addr_fallback` | `31` | 1 |
| 9 | 8 | 237950235243 | `addr_fallback` | `31` | 1 |
| 10 | 9 | 237950235576 | `addr_fallback` | `31` | 1 |
| 11 | 10 | 237950235576 | `addr_fallback` | `31` | 1 |
| 12 | 11 | 237950235576 | `addr_fallback` | `31` | 1 |
| 64 | 12 | 237950294517 | `addr_fallback` | `31` | 1 |
| 65 | 64 | 237950294517 | `addr_fallback` | `31` | 1 |
| 66 | 65 | 237950294517 | `addr_fallback` | `31` | 1 |
| 67 | 66 | 237950295183 | `addr_fallback` | `31` | 1 |
| 68 | 67 | 237950295183 | `addr_fallback` | `31` | 1 |
| 69 | 68 | 237950295183 | `addr_fallback` | `31` | 1 |
| 73 | 69 | 237950295516 | `seq_primary` | `31` | 1 |
| 74 | 73 | 237950295516 | `seq_primary` | `31` | 1 |
| 75 | 74 | 237950295516 | `seq_primary` | `—` | 1 |
| 293 | 75 | 237951302175 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=293），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`150170`，eligible=`1`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3/prop_evt.txt.gz` — SHA-256 `5d4b2d3c7c3f3af35b78e9969ea06302e6660c0a059b09fac016c6dc7ea1192d`（16778 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3/chain_report.json` — SHA-256 `9223c0c94f1f0d09de473b2879d4c45c46b79c160aab350839a15ad3ec327d1d`（10701 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3/stats.txt` — SHA-256 `22d19dc6b4511a6c71b2bd7e49bb4ac80b0256d83a6c73948bff6f6ee84cdcb1`（381642 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3/run.out` — SHA-256 `847d38b370591ff6b87facae5ac7d284057abaf91ddaf6cfa6f131cd24a441ef`（2299 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3/run.err` — SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`（1726 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/T10-F0-W4/seed3/armtlb_injections.log` — SHA-256 `3aff18f2503c31726e487b942e80f829eae99f5c147abd67850328494d6ab70b`（196 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3/manifest.json` — SHA-256 `334d82b3be8d42a20ada878982f6688e6521f09b98921a72124f8bdeba06a1d3`（2098 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

