# T10-F2-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F2-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3 --cells T10-F2-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T01:00:43+08:00`，end=`2026-10-28T01:01:23+08:00`）
- 运行目录进程：gem5_pid=`3060090`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：12752（chain_report.event_count=`12752`）
- fault_id 数：3

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`238095582084`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`520906`，request_id=`520906`，VA=`0xffffffc009483950`
- 被改字段：`bit_flip`；before=`81d75`，after=`85d75`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
    protection: model=none bits=1 -> Raw
Tick: 238095582084, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483950, old_pfn: 0x81d75, new_pfn: 0x85d75, FaultType: bit_flip, Mask: 0x4000, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 238618556919, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483240, old_pfn: 0x85d75, new_pfn: 0x95d75, FaultType: bit_flip, Mask: 0x10000, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 1971861830334, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_pfn: 0x80c73, new_pfn: 0x80c53, FaultType: bit_flip, Mask: 0x20, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`10929`（kind=`consumer`）沿 `parent_event_id` 回溯到 L0 注入，共 23 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 12752 个事件，为可读性第 3 章只逐条叙述**主链** 23 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=10880`，`tick=1971861830334`，`corr=origin`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=ffffffc008c730e0`，`field=bit_flip`，`before=80c73`，`after=80c53`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=10881`，`parent_event_id=10880`，`tick=1971861830334`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=6`，`way=-1`，`field=post_lookup`，`before=80c73`，`after=80c53`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c53;ap=0;mtype=2;page_size=1000;pa=80c530e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c53;ap=0;mtype=2;page_size=1000;pa=80c530e0`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=10882`，`parent_event_id=10881`，`tick=1971861830334`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=ffffffc008c730e0`，`pa=80c530e0`，`field=bit_flip`，`before=80c73`，`after=80c53`，`state_before=80c730e0`，`state_after=80c530e0`
  该事件把 TLB 表项的状态/字段从 `80c730e0` 变为 `80c530e0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=10883`，`parent_event_id=10882`，`tick=1971861830334`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c530e0`，`entry_index=6`，`way=-1`，`field=effective_pa_changed`，`before=80c730e0`，`after=80c530e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c53;ap=0;mtype=2;page_size=1000;pa=80c530e0`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `80c730e0` 变为 `80c530e0`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=10884`，`parent_event_id=10883`，`tick=1971861830334`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=ffffffc008c730e0`，`lq_idx=185826`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=10885`，`parent_event_id=10884`，`tick=1971861830334`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=ffffffc008c730e0`，`pa=80c530e0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=10886`，`parent_event_id=10885`，`tick=1971861830334`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`pa=80c530e0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10887`，`parent_event_id=10886`，`tick=1971861830334`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`cache_line=80c530e0`，`mshr_id=91`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=10888`，`parent_event_id=10887`，`tick=1971861830667`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=ffffffc008c730e0`，`pa=80c530c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=10889`，`parent_event_id=10888`，`tick=1971861830667`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`pa=80c530c0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10890`，`parent_event_id=10889`，`tick=1971861830667`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`cache_line=80c530c0`，`mshr_id=92`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=10891`，`parent_event_id=10890`，`tick=1971861889608`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`cache_line=80c530c0`，`mshr_id=92`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=10892`，`parent_event_id=10891`，`tick=1971861889608`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`pa=80c530c0`，`cache_line=80c530c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=10893`，`parent_event_id=10892`，`tick=1971861889608`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`cache_line=80c530c0`，`mshr_id=92`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=10894`，`parent_event_id=10893`，`tick=1971861890274`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`cache_line=80c530c0`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=10895`，`parent_event_id=10894`，`tick=1971861890274`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`pa=80c530c0`，`cache_line=80c530c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=10896`，`parent_event_id=10895`，`tick=1971861890274`，`corr=addr_fallback`，`request_id=1456805`，`dyn_inst_seq=1456805`，`cache_line=80c530c0`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `resp`（L4 内存响应）

- `event_id=10897`，`parent_event_id=10896`，`tick=1971861890607`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=80c530e0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `lq_complete`（L4 载入完成）

- `event_id=10898`，`parent_event_id=10897`，`tick=1971861890607`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=ffffffc008c730e0`，`pa=80c530e0`，`lq_idx=185826`

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=10899`，`parent_event_id=10898`，`tick=1971861890607`，`corr=seq_primary`，`request_id=1456805`，`dyn_inst_seq=1456805`，`va=80c530e0`，`before=clean`，`after=tainted`，`arch_reg=0`，`phys_reg=204`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `consumer`（L4 消费者读取）

- `event_id=10900`，`parent_event_id=10899`，`tick=1971861891939`，`corr=taint_prop`，`dyn_inst_seq=1456806`，`arch_reg=0`，`phys_reg=204`，`pc=ffffffc0080bf5d4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.22 `consumer`（L4 消费者读取）

- `event_id=10908`，`parent_event_id=10900`，`tick=1971861897267`，`corr=taint_prop`，`dyn_inst_seq=1456828`，`arch_reg=0`，`phys_reg=65535`，`pc=ffffffc0087bbfdc`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.23 `consumer`（L4 消费者读取）

- `event_id=10929`，`parent_event_id=10908`，`tick=1971861937227`，`corr=taint_prop`，`dyn_inst_seq=1457135`，`arch_reg=24`，`phys_reg=90`，`pc=ffffffc0080c5ba4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 10880 | `inj` | L0 | CHAOSArmTLB | `1456805` | `ffffffc008c730e0` | `80c73` → `80c53` |
| 10881 | `tlb_lookup` | L1 | DTLB CAM | `1456805` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c53;ap=0;mtype=2;page_size=1000;pa=80c530e0` |
| 10882 | `tlb_pfn` | L1 | DTLB 表项 | `1456805` | `80c530e0` | `80c730e0` → `80c530e0` |
| 10883 | `tlb_translate_result` | L2 | MMU 翻译 | `1456805` | `80c530e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c53;ap=0;mtype=2;page_size=1000;pa=80c530e0` |
| 10884 | `lq_read` | L3 | LQ | `1456805` | `ffffffc008c730e0` | — |
| 10885 | `cache_access` | L3 | L1D | `1456805` | `80c530e0` | — |
| 10886 | `cache_return` | L3 | L1D | `1456805` | `80c530e0` | — |
| 10887 | `mshr_alloc` | L3 | MSHR | `1456805` | `80c530e0` | `` → `mshr_allocated` |
| 10888 | `cache_access` | L3 | L1D | `1456805` | `80c530c0` | — |
| 10889 | `cache_return` | L3 | L1D | `1456805` | `80c530c0` | — |
| 10890 | `mshr_alloc` | L3 | MSHR | `1456805` | `80c530c0` | `` → `mshr_allocated` |
| 10891 | `mshr_fill` | L3 | MSHR | `1456805` | `80c530c0` | `` → `filled` |
| 10892 | `cache_fill` | L3 | L1D | `1456805` | `80c530c0` | — |
| 10893 | `mshr_free` | L3 | MSHR | `1456805` | `80c530c0` | `` → `mshr_freed` |
| 10894 | `mshr_fill` | L3 | MSHR | `1456805` | `80c530c0` | `` → `filled` |
| 10895 | `cache_fill` | L3 | L1D | `1456805` | `80c530c0` | — |
| 10896 | `mshr_free` | L3 | MSHR | `1456805` | `80c530c0` | `` → `mshr_freed` |
| 10897 | `resp` | L4 | LSU | `1456805` | `80c530e0` | — |
| 10898 | `lq_complete` | L4 | LQ | `1456805` | `80c530e0` | — |
| 10899 | `taint_reg` | L4 | PRF/提交 | `1456805` | `80c530e0` | `clean` → `tainted` |
| 10900 | `consumer` | L4 | consumer | `1456806` | `—` | — |
| 10908 | `consumer` | L4 | consumer | `1456828` | `—` | — |
| 10929 | `consumer` | L4 | consumer | `1457135` | `—` | — |


（第 4 章仅逐条列出主链 23 个事件；其余 12729 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 2276 | 98 | 10929 |
| `taint_reg` | 2002 | 64 | 10921 |
| `cache_access` | 1869 | 5 | 10918 |
| `cache_return` | 1869 | 6 | 10919 |
| `request_fork` | 1819 | 4294967296 | 4294969114 |
| `resp` | 1717 | 63 | 10920 |
| `lq_complete` | 583 | 66 | 10913 |
| `mshr_merge` | 163 | 20 | 8932 |
| `mshr_alloc` | 92 | 7 | 10890 |
| `mshr_fill` | 92 | 54 | 10894 |
| `cache_fill` | 92 | 55 | 10895 |
| `mshr_free` | 92 | 56 | 10896 |
| `squash_masked` | 65 | 1661 | 10792 |
| `inj` | 3 | 0 | 10880 |
| `tlb_lookup` | 3 | 1 | 10881 |
| `tlb_pfn` | 3 | 2 | 10882 |
| `tlb_translate_result` | 3 | 3 | 10883 |
| `chain_end` | 3 | 10930 | 10932 |
| `lq_read` | 2 | 8352 | 10884 |
| `sq_execute` | 1 | 4 | 4 |
| `sq_writeback` | 1 | 11 | 11 |
| `sq_complete` | 1 | 82 | 82 |
| `errant_commit` | 1 | 97 | 97 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
10880(inj) → 10881(tlb_lookup) → 10882(tlb_pfn) → 10883(tlb_translate_result) → 10884(lq_read) → 10885(cache_access) → 10886(cache_return) → 10887(mshr_alloc) → 10888(cache_access) → 10889(cache_return) → 10890(mshr_alloc) → 10891(mshr_fill) → 10892(cache_fill) → 10893(mshr_free) → 10894(mshr_fill) → 10895(cache_fill) → 10896(mshr_free) → 10897(resp) → 10898(lq_complete) → 10899(taint_reg) → 10900(consumer) → 10908(consumer) → 10929(consumer)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 10880 | — | 1971861830334 | `origin` | `1456805` | 3 |
| 10881 | 10880 | 1971861830334 | `seq_primary` | `1456805` | 3 |
| 10882 | 10881 | 1971861830334 | `seq_primary` | `1456805` | 3 |
| 10883 | 10882 | 1971861830334 | `seq_primary` | `1456805` | 3 |
| 10884 | 10883 | 1971861830334 | `seq_primary` | `1456805` | 3 |
| 10885 | 10884 | 1971861830334 | `addr_fallback` | `1456805` | 3 |
| 10886 | 10885 | 1971861830334 | `addr_fallback` | `1456805` | 3 |
| 10887 | 10886 | 1971861830334 | `addr_fallback` | `1456805` | 3 |
| 10888 | 10887 | 1971861830667 | `addr_fallback` | `1456805` | 3 |
| 10889 | 10888 | 1971861830667 | `addr_fallback` | `1456805` | 3 |
| 10890 | 10889 | 1971861830667 | `addr_fallback` | `1456805` | 3 |
| 10891 | 10890 | 1971861889608 | `addr_fallback` | `1456805` | 3 |
| 10892 | 10891 | 1971861889608 | `addr_fallback` | `1456805` | 3 |
| 10893 | 10892 | 1971861889608 | `addr_fallback` | `1456805` | 3 |
| 10894 | 10893 | 1971861890274 | `addr_fallback` | `1456805` | 3 |
| 10895 | 10894 | 1971861890274 | `addr_fallback` | `1456805` | 3 |
| 10896 | 10895 | 1971861890274 | `addr_fallback` | `1456805` | 3 |
| 10897 | 10896 | 1971861890607 | `seq_primary` | `1456805` | 3 |
| 10898 | 10897 | 1971861890607 | `seq_primary` | `1456805` | 3 |
| 10899 | 10898 | 1971861890607 | `seq_primary` | `1456805` | 3 |
| 10900 | 10899 | 1971861891939 | `taint_prop` | `—` | 3 |
| 10908 | 10900 | 1971861897267 | `taint_prop` | `—` | 3 |
| 10929 | 10908 | 1971861937227 | `taint_prop` | `—` | 3 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `consumer`（event_id=10929），其字段 `outcome=`、`contained=`、`detection_layer=`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`416527`，eligible=`416527`，injected=`3`（日志应用行 3 条），activated=`3`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3/prop_evt.txt.gz` — SHA-256 `6261d8ec274b3eaae291da32a9e79c9d82a616593e8dd4e4a90614e3d233c967`（476526 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3/chain_report.json` — SHA-256 `371a607146a2661f60c466873682eee366a6cfcb666276d2f1bedf43eea5012d`（1375321 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3/stats.txt` — SHA-256 `b776ba826f3a2acce91c248b8c124551927c31a1ae6e4f01a1d6cfbb013cbec7`（394487 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3/run.out` — SHA-256 `0f3dc3b6837848bbb0c648e25f7d25acb41eb6262b2b69a702a3d25d5d606f75`（8564 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3/run.err` — SHA-256 `de8403ca5671675b258d5cc2e9d99a733336eef03c49490bb0d383150eb6e549`（1800 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/T10-F2-W4/seed3/armtlb_injections.log` — SHA-256 `9b2befa5916174de9465dba72b0db2219110e5e17ba633f45e77e10f893d04a1`（782 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3/manifest.json` — SHA-256 `2bfe49fa9df45bc8a9d7a5af6773a14c3e5f27b950c141cfa678b90e007c2e3d`（2103 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

