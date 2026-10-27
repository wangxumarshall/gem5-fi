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

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`14620`（kind=`consumer`）沿 `parent_event_id` 回溯到 L0 注入，共 58 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 25388 个事件，为可读性第 3 章只逐条叙述**主链** 58 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=1371`，`tick=241738137882`，`corr=origin`，`request_id=12113502`，`dyn_inst_seq=12113502`，`va=ffffffc00948bf78`，`field=bit_flip`，`before=81d4d`，`after=91d4d`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1372`，`parent_event_id=1371`，`tick=241738137882`，`corr=seq_primary`，`request_id=12113502`，`dyn_inst_seq=12113502`，`walk_id=0`，`va=ffffffc00948bf78`，`entry_index=23`，`way=-1`，`field=post_lookup`，`before=81d4d`，`after=91d4d`，`state_before=vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=81d4d;ap=0;mtype=2;page_size=1000;pa=81d4df78`，`state_after=vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=91d4d;ap=0;mtype=2;page_size=1000;pa=91d4df78`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=81d4d;ap=0;mtype=2;page_size=1000;pa=81d4df78` 变为 `vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=91d4d;ap=0;mtype=2;page_size=1000;pa=91d4df78`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=1373`，`parent_event_id=1372`，`tick=241738137882`，`corr=seq_primary`，`request_id=12113502`，`dyn_inst_seq=12113502`，`va=ffffffc00948bf78`，`pa=91d4df78`，`field=bit_flip`，`before=81d4d`，`after=91d4d`，`state_before=81d4df78`，`state_after=91d4df78`
  该事件把 TLB 表项的状态/字段从 `81d4df78` 变为 `91d4df78`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=1374`，`parent_event_id=1373`，`tick=241738137882`，`corr=seq_primary`，`request_id=12113502`，`dyn_inst_seq=12113502`，`walk_id=0`，`va=ffffffc00948bf78`，`pa=91d4df78`，`entry_index=23`，`way=-1`，`field=effective_pa_changed`，`before=81d4df78`，`after=91d4df78`，`state_before=vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=81d4d;ap=0;mtype=2;page_size=1000;pa=81d4df78`，`state_after=vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=91d4d;ap=0;mtype=2;page_size=1000;pa=91d4df78`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81d4df78` 变为 `91d4df78`，outcome=`NoFault`，contained=`0`。

### 3.5 `sq_execute`（L3 存储执行）

- `event_id=1375`，`parent_event_id=1374`，`tick=241738137882`，`corr=seq_primary`，`dyn_inst_seq=12113502`，`va=ffffffc00948bf78`，`state_before=issued`，`sq_idx=1026404`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `sq_writeback`（L3 存储写回）

- `event_id=1376`，`parent_event_id=1375`，`tick=241738139214`，`corr=seq_primary`，`dyn_inst_seq=12113502`，`pa=91d4df78`，`state_after=packet_built`，`sq_idx=1026404`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.7 `cache_access`（L3 L1D 访问）

- `event_id=1377`，`parent_event_id=1376`，`tick=241738139214`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`va=ffffffc00948bf78`，`pa=91d4df78`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `cache_return`（L3 L1D 返回）

- `event_id=1378`，`parent_event_id=1377`，`tick=241738139214`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`pa=91d4df78`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `mshr_alloc`（L3 MSHR 分配）

- `event_id=1379`，`parent_event_id=1378`，`tick=241738139214`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`cache_line=91d4df78`，`mshr_id=7`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_access`（L3 L1D 访问）

- `event_id=1380`，`parent_event_id=1379`，`tick=241738139547`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`va=ffffffc00948bf78`，`pa=91d4df40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `cache_return`（L3 L1D 返回）

- `event_id=1381`，`parent_event_id=1380`，`tick=241738139547`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`pa=91d4df40`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_alloc`（L3 MSHR 分配）

- `event_id=1382`，`parent_event_id=1381`，`tick=241738139547`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`cache_line=91d4df40`，`mshr_id=8`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `mshr_fill`（L3 MSHR 填充）

- `event_id=1398`，`parent_event_id=1382`，`tick=241738212474`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`cache_line=91d4df40`，`mshr_id=8`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `cache_fill`（L3 L1D 填充）

- `event_id=1399`，`parent_event_id=1398`，`tick=241738212474`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`pa=91d4df40`，`cache_line=91d4df40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_free`（L3 MSHR 释放）

- `event_id=1400`，`parent_event_id=1399`，`tick=241738212474`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`cache_line=91d4df40`，`mshr_id=8`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `mshr_fill`（L3 MSHR 填充）

- `event_id=1401`，`parent_event_id=1400`，`tick=241738213140`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`cache_line=91d4df40`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `cache_fill`（L3 L1D 填充）

- `event_id=1402`，`parent_event_id=1401`，`tick=241738213140`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`pa=91d4df40`，`cache_line=91d4df40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `mshr_free`（L3 MSHR 释放）

- `event_id=1403`，`parent_event_id=1402`，`tick=241738213140`，`corr=addr_fallback`，`request_id=12113502`，`dyn_inst_seq=12113502`，`cache_line=91d4df40`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `resp`（L4 内存响应）

- `event_id=1407`，`parent_event_id=1403`，`tick=241738213473`，`corr=seq_primary`，`request_id=12113502`，`dyn_inst_seq=12113502`，`va=91d4df78`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=1408`，`parent_event_id=1407`，`tick=241738213473`，`corr=seq_primary`，`request_id=12113502`，`dyn_inst_seq=12113502`，`va=91d4df78`，`before=clean`，`after=tainted`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `request_fork`（request_fork）

- `event_id=4294967324`，`parent_event_id=1408`，`tick=241738342344`，`corr=addr_fallback`，`request_id=12113502`

### 3.22 `cache_access`（L3 L1D 访问）

- `event_id=1511`，`parent_event_id=4294967324`，`tick=241738342344`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`va=ffffffc00948bef0`，`pa=91d4def0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.23 `cache_return`（L3 L1D 返回）

- `event_id=1512`，`parent_event_id=1511`，`tick=241738342344`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`pa=91d4def0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.24 `mshr_alloc`（L3 MSHR 分配）

- `event_id=1513`，`parent_event_id=1512`，`tick=241738342344`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`cache_line=91d4def0`，`mshr_id=17`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.25 `cache_access`（L3 L1D 访问）

- `event_id=1514`，`parent_event_id=1513`，`tick=241738342677`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`va=ffffffc00948bef0`，`pa=91d4dec0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.26 `cache_return`（L3 L1D 返回）

- `event_id=1515`，`parent_event_id=1514`，`tick=241738342677`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`pa=91d4dec0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.27 `mshr_alloc`（L3 MSHR 分配）

- `event_id=1516`，`parent_event_id=1515`，`tick=241738342677`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`cache_line=91d4dec0`，`mshr_id=18`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.28 `mshr_fill`（L3 MSHR 填充）

- `event_id=1522`，`parent_event_id=1516`，`tick=241738387299`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`cache_line=91d4dec0`，`mshr_id=18`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.29 `cache_fill`（L3 L1D 填充）

- `event_id=1523`，`parent_event_id=1522`，`tick=241738387299`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`pa=91d4dec0`，`cache_line=91d4dec0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.30 `mshr_free`（L3 MSHR 释放）

- `event_id=1524`，`parent_event_id=1523`，`tick=241738387299`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`cache_line=91d4dec0`，`mshr_id=18`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.31 `mshr_fill`（L3 MSHR 填充）

- `event_id=1525`，`parent_event_id=1524`，`tick=241738387965`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`cache_line=91d4dec0`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.32 `cache_fill`（L3 L1D 填充）

- `event_id=1526`，`parent_event_id=1525`，`tick=241738387965`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`pa=91d4dec0`，`cache_line=91d4dec0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.33 `mshr_free`（L3 MSHR 释放）

- `event_id=1527`，`parent_event_id=1526`，`tick=241738387965`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`cache_line=91d4dec0`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.34 `resp`（L4 内存响应）

- `event_id=1528`，`parent_event_id=1527`，`tick=241738388298`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`va=91d4def0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.35 `lq_complete`（L4 载入完成）

- `event_id=1529`，`parent_event_id=1528`，`tick=241738388298`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`va=ffffffc00948bef0`，`pa=91d4def0`，`lq_idx=1276881`

### 3.36 `taint_reg`（L4 寄存器污染）

- `event_id=1530`，`parent_event_id=1529`，`tick=241738388298`，`corr=addr_fallback`，`request_id=12113824`，`dyn_inst_seq=12113824`，`va=91d4def0`，`before=clean`，`after=tainted`，`arch_reg=1`，`phys_reg=85`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.37 `consumer`（L4 消费者读取）

- `event_id=1536`，`parent_event_id=1530`，`tick=241738389630`，`corr=taint_prop`，`dyn_inst_seq=12113843`，`arch_reg=1`，`phys_reg=85`，`pc=ffffffc008025040`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.38 `consumer`（L4 消费者读取）

- `event_id=1569`，`parent_event_id=1536`，`tick=241738395957`，`corr=taint_prop`，`dyn_inst_seq=12113863`，`arch_reg=0`，`phys_reg=65535`，`pc=ffffffc008024f30`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.39 `consumer`（L4 消费者读取）

- `event_id=1634`，`parent_event_id=1569`，`tick=241738623729`，`corr=taint_prop`，`dyn_inst_seq=12114015`，`arch_reg=0`，`phys_reg=188`，`pc=ffffffc008218fcc`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.40 `consumer`（L4 消费者读取）

- `event_id=1685`，`parent_event_id=1634`，`tick=241738688997`，`corr=taint_prop`，`dyn_inst_seq=12114047`，`arch_reg=0`，`phys_reg=143`，`pc=ffffffc008010a04`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.41 `consumer`（L4 消费者读取）

- `event_id=1686`，`parent_event_id=1685`，`tick=241738689330`，`corr=taint_prop`，`dyn_inst_seq=12114048`，`arch_reg=42`，`phys_reg=66`，`pc=ffffffc008010a08`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.42 `consumer`（L4 消费者读取）

- `event_id=1689`，`parent_event_id=1686`，`tick=241738694991`，`corr=taint_prop`，`dyn_inst_seq=12114062`，`arch_reg=42`，`phys_reg=147`，`pc=ffffffc008011280`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.43 `consumer`（L4 消费者读取）

- `event_id=1929`，`parent_event_id=1689`，`tick=241738926093`，`corr=taint_prop`，`dyn_inst_seq=12114174`，`arch_reg=35`，`phys_reg=236`，`pc=ffffffc0087b1aec`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.44 `consumer`（L4 消费者读取）

- `event_id=1933`，`parent_event_id=1929`，`tick=241738926426`，`corr=taint_prop`，`dyn_inst_seq=12114178`，`arch_reg=42`，`phys_reg=213`，`pc=ffffffc0087b1af4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.45 `consumer`（L4 消费者读取）

- `event_id=1942`，`parent_event_id=1933`，`tick=241739000685`，`corr=taint_prop`，`dyn_inst_seq=12114200`，`arch_reg=35`，`phys_reg=28`，`pc=ffffffc0087b14bc`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.46 `consumer`（L4 消费者读取）

- `event_id=1954`，`parent_event_id=1942`，`tick=241739005680`，`corr=taint_prop`，`dyn_inst_seq=12114203`，`arch_reg=42`，`phys_reg=76`，`pc=ffffffc0087b14c0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.47 `consumer`（L4 消费者读取）

- `event_id=1980`，`parent_event_id=1954`，`tick=241739051967`，`corr=taint_prop`，`dyn_inst_seq=12114223`，`arch_reg=35`，`phys_reg=132`，`pc=ffffffc0087b138c`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.48 `consumer`（L4 消费者读取）

- `event_id=1983`，`parent_event_id=1980`，`tick=241739052300`，`corr=taint_prop`，`dyn_inst_seq=12114226`，`arch_reg=42`，`phys_reg=7`，`pc=ffffffc0087b1390`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.49 `consumer`（L4 消费者读取）

- `event_id=2020`，`parent_event_id=1983`，`tick=241739056962`，`corr=taint_prop`，`dyn_inst_seq=12114262`，`arch_reg=42`，`phys_reg=90`，`pc=ffffffc0087b13c0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.50 `consumer`（L4 消费者读取）

- `event_id=2030`，`parent_event_id=2020`，`tick=241739068950`，`corr=taint_prop`，`dyn_inst_seq=12114279`，`arch_reg=35`，`phys_reg=198`，`pc=ffffffc00802fb44`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.51 `consumer`（L4 消费者读取）

- `event_id=2033`，`parent_event_id=2030`，`tick=241739068950`，`corr=taint_prop`，`dyn_inst_seq=12114285`，`arch_reg=42`，`phys_reg=204`，`pc=ffffffc00802fb54`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.52 `consumer`（L4 消费者读取）

- `event_id=2097`，`parent_event_id=2033`，`tick=241739118900`，`corr=taint_prop`，`dyn_inst_seq=12114333`，`arch_reg=35`，`phys_reg=121`，`pc=ffffffc00802f9ec`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.53 `consumer`（L4 消费者读取）

- `event_id=2100`，`parent_event_id=2097`，`tick=241739119233`，`corr=taint_prop`，`dyn_inst_seq=12114337`，`arch_reg=42`，`phys_reg=65`，`pc=ffffffc00802f9f4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.54 `consumer`（L4 消费者读取）

- `event_id=2114`，`parent_event_id=2100`，`tick=241739134884`，`corr=taint_prop`，`dyn_inst_seq=12114376`，`arch_reg=35`，`phys_reg=171`，`pc=ffffffc00802f63c`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.55 `consumer`（L4 消费者读取）

- `event_id=2126`，`parent_event_id=2114`，`tick=241739139879`，`corr=taint_prop`，`dyn_inst_seq=12114380`，`arch_reg=42`，`phys_reg=101`，`pc=ffffffc00802f644`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.56 `consumer`（L4 消费者读取）

- `event_id=2130`，`parent_event_id=2126`，`tick=241739140545`，`corr=taint_prop`，`dyn_inst_seq=12114391`，`arch_reg=35`，`phys_reg=68`，`pc=ffffffc00802f65c`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.57 `consumer`（L4 消费者读取）

- `event_id=2625`，`parent_event_id=2130`，`tick=241740281403`，`corr=taint_prop`，`dyn_inst_seq=12115600`，`arch_reg=19`，`phys_reg=162`，`pc=ffffffc0083752f0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.58 `consumer`（L4 消费者读取）

- `event_id=14620`，`parent_event_id=2625`，`tick=241770466188`，`corr=taint_prop`，`dyn_inst_seq=12173776`，`arch_reg=1`，`phys_reg=795`，`pc=ffffffc00801db20`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 1371 | `inj` | L0 | CHAOSArmTLB | `12113502` | `ffffffc00948bf78` | `81d4d` → `91d4d` |
| 1372 | `tlb_lookup` | L1 | DTLB CAM | `12113502` | `ffffffc00948bf78` | `vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=81d4d;ap=0;mtype=2;page_size=1000;pa=81d4df78` → `vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=91d4d;ap=0;mtype=2;page_size=1000;pa=91d4df78` |
| 1373 | `tlb_pfn` | L1 | DTLB 表项 | `12113502` | `91d4df78` | `81d4df78` → `91d4df78` |
| 1374 | `tlb_translate_result` | L2 | MMU 翻译 | `12113502` | `91d4df78` | `vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=81d4d;ap=0;mtype=2;page_size=1000;pa=81d4df78` → `vpn=ffffffc00948b;asid=228;valid=1;global=1;pfn=91d4d;ap=0;mtype=2;page_size=1000;pa=91d4df78` |
| 1375 | `sq_execute` | L3 | SQ | `12113502` | `ffffffc00948bf78` | `issued` → `` |
| 1376 | `sq_writeback` | L3 | SQ | `12113502` | `91d4df78` | `` → `packet_built` |
| 1377 | `cache_access` | L3 | L1D | `12113502` | `91d4df78` | — |
| 1378 | `cache_return` | L3 | L1D | `12113502` | `91d4df78` | — |
| 1379 | `mshr_alloc` | L3 | MSHR | `12113502` | `91d4df78` | `` → `mshr_allocated` |
| 1380 | `cache_access` | L3 | L1D | `12113502` | `91d4df40` | — |
| 1381 | `cache_return` | L3 | L1D | `12113502` | `91d4df40` | — |
| 1382 | `mshr_alloc` | L3 | MSHR | `12113502` | `91d4df40` | `` → `mshr_allocated` |
| 1398 | `mshr_fill` | L3 | MSHR | `12113502` | `91d4df40` | `` → `filled` |
| 1399 | `cache_fill` | L3 | L1D | `12113502` | `91d4df40` | — |
| 1400 | `mshr_free` | L3 | MSHR | `12113502` | `91d4df40` | `` → `mshr_freed` |
| 1401 | `mshr_fill` | L3 | MSHR | `12113502` | `91d4df40` | `` → `filled` |
| 1402 | `cache_fill` | L3 | L1D | `12113502` | `91d4df40` | — |
| 1403 | `mshr_free` | L3 | MSHR | `12113502` | `91d4df40` | `` → `mshr_freed` |
| 1407 | `resp` | L4 | LSU | `12113502` | `91d4df78` | — |
| 1408 | `taint_reg` | L4 | PRF/提交 | `12113502` | `91d4df78` | `clean` → `tainted` |
| 4294967324 | `request_fork` | — | request_fork | `12113502` | `—` | — |
| 1511 | `cache_access` | L3 | L1D | `12113824` | `91d4def0` | — |
| 1512 | `cache_return` | L3 | L1D | `12113824` | `91d4def0` | — |
| 1513 | `mshr_alloc` | L3 | MSHR | `12113824` | `91d4def0` | `` → `mshr_allocated` |
| 1514 | `cache_access` | L3 | L1D | `12113824` | `91d4dec0` | — |
| 1515 | `cache_return` | L3 | L1D | `12113824` | `91d4dec0` | — |
| 1516 | `mshr_alloc` | L3 | MSHR | `12113824` | `91d4dec0` | `` → `mshr_allocated` |
| 1522 | `mshr_fill` | L3 | MSHR | `12113824` | `91d4dec0` | `` → `filled` |
| 1523 | `cache_fill` | L3 | L1D | `12113824` | `91d4dec0` | — |
| 1524 | `mshr_free` | L3 | MSHR | `12113824` | `91d4dec0` | `` → `mshr_freed` |
| 1525 | `mshr_fill` | L3 | MSHR | `12113824` | `91d4dec0` | `` → `filled` |
| 1526 | `cache_fill` | L3 | L1D | `12113824` | `91d4dec0` | — |
| 1527 | `mshr_free` | L3 | MSHR | `12113824` | `91d4dec0` | `` → `mshr_freed` |
| 1528 | `resp` | L4 | LSU | `12113824` | `91d4def0` | — |
| 1529 | `lq_complete` | L4 | LQ | `12113824` | `91d4def0` | — |
| 1530 | `taint_reg` | L4 | PRF/提交 | `12113824` | `91d4def0` | `clean` → `tainted` |
| 1536 | `consumer` | L4 | consumer | `12113843` | `—` | — |
| 1569 | `consumer` | L4 | consumer | `12113863` | `—` | — |
| 1634 | `consumer` | L4 | consumer | `12114015` | `—` | — |
| 1685 | `consumer` | L4 | consumer | `12114047` | `—` | — |
| 1686 | `consumer` | L4 | consumer | `12114048` | `—` | — |
| 1689 | `consumer` | L4 | consumer | `12114062` | `—` | — |
| 1929 | `consumer` | L4 | consumer | `12114174` | `—` | — |
| 1933 | `consumer` | L4 | consumer | `12114178` | `—` | — |
| 1942 | `consumer` | L4 | consumer | `12114200` | `—` | — |
| 1954 | `consumer` | L4 | consumer | `12114203` | `—` | — |
| 1980 | `consumer` | L4 | consumer | `12114223` | `—` | — |
| 1983 | `consumer` | L4 | consumer | `12114226` | `—` | — |
| 2020 | `consumer` | L4 | consumer | `12114262` | `—` | — |
| 2030 | `consumer` | L4 | consumer | `12114279` | `—` | — |
| 2033 | `consumer` | L4 | consumer | `12114285` | `—` | — |
| 2097 | `consumer` | L4 | consumer | `12114333` | `—` | — |
| 2100 | `consumer` | L4 | consumer | `12114337` | `—` | — |
| 2114 | `consumer` | L4 | consumer | `12114376` | `—` | — |
| 2126 | `consumer` | L4 | consumer | `12114380` | `—` | — |
| 2130 | `consumer` | L4 | consumer | `12114391` | `—` | — |
| 2625 | `consumer` | L4 | consumer | `12115600` | `—` | — |
| 14620 | `consumer` | L4 | consumer | `12173776` | `—` | — |


（第 4 章仅逐条列出主链 58 个事件；其余 25330 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

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
1371(inj) → 1372(tlb_lookup) → 1373(tlb_pfn) → 1374(tlb_translate_result) → 1375(sq_execute) → 1376(sq_writeback) → 1377(cache_access) → 1378(cache_return) → 1379(mshr_alloc) → 1380(cache_access) → 1381(cache_return) → 1382(mshr_alloc) → 1398(mshr_fill) → 1399(cache_fill) → 1400(mshr_free) → 1401(mshr_fill) → 1402(cache_fill) → 1403(mshr_free) → 1407(resp) → 1408(taint_reg) → 4294967324(request_fork) → 1511(cache_access) → 1512(cache_return) → 1513(mshr_alloc) → 1514(cache_access) → 1515(cache_return) → 1516(mshr_alloc) → 1522(mshr_fill) → 1523(cache_fill) → 1524(mshr_free) → 1525(mshr_fill) → 1526(cache_fill) → 1527(mshr_free) → 1528(resp) → 1529(lq_complete) → 1530(taint_reg) → 1536(consumer) → 1569(consumer) → 1634(consumer) → 1685(consumer) → 1686(consumer) → 1689(consumer) → 1929(consumer) → 1933(consumer) → 1942(consumer) → 1954(consumer) → 1980(consumer) → 1983(consumer) → 2020(consumer) → 2030(consumer) → 2033(consumer) → 2097(consumer) → 2100(consumer) → 2114(consumer) → 2126(consumer) → 2130(consumer) → 2625(consumer) → 14620(consumer)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 1371 | — | 241738137882 | `origin` | `12113502` | 2 |
| 1372 | 1371 | 241738137882 | `seq_primary` | `12113502` | 2 |
| 1373 | 1372 | 241738137882 | `seq_primary` | `12113502` | 2 |
| 1374 | 1373 | 241738137882 | `seq_primary` | `12113502` | 2 |
| 1375 | 1374 | 241738137882 | `seq_primary` | `—` | 2 |
| 1376 | 1375 | 241738139214 | `seq_primary` | `—` | 2 |
| 1377 | 1376 | 241738139214 | `addr_fallback` | `12113502` | 2 |
| 1378 | 1377 | 241738139214 | `addr_fallback` | `12113502` | 2 |
| 1379 | 1378 | 241738139214 | `addr_fallback` | `12113502` | 2 |
| 1380 | 1379 | 241738139547 | `addr_fallback` | `12113502` | 2 |
| 1381 | 1380 | 241738139547 | `addr_fallback` | `12113502` | 2 |
| 1382 | 1381 | 241738139547 | `addr_fallback` | `12113502` | 2 |
| 1398 | 1382 | 241738212474 | `addr_fallback` | `12113502` | 2 |
| 1399 | 1398 | 241738212474 | `addr_fallback` | `12113502` | 2 |
| 1400 | 1399 | 241738212474 | `addr_fallback` | `12113502` | 2 |
| 1401 | 1400 | 241738213140 | `addr_fallback` | `12113502` | 2 |
| 1402 | 1401 | 241738213140 | `addr_fallback` | `12113502` | 2 |
| 1403 | 1402 | 241738213140 | `addr_fallback` | `12113502` | 2 |
| 1407 | 1403 | 241738213473 | `seq_primary` | `12113502` | 2 |
| 1408 | 1407 | 241738213473 | `seq_primary` | `12113502` | 2 |
| 4294967324 | 1408 | 241738342344 | `addr_fallback` | `12113502` | 2 |
| 1511 | 4294967324 | 241738342344 | `addr_fallback` | `12113824` | 2 |
| 1512 | 1511 | 241738342344 | `addr_fallback` | `12113824` | 2 |
| 1513 | 1512 | 241738342344 | `addr_fallback` | `12113824` | 2 |
| 1514 | 1513 | 241738342677 | `addr_fallback` | `12113824` | 2 |
| 1515 | 1514 | 241738342677 | `addr_fallback` | `12113824` | 2 |
| 1516 | 1515 | 241738342677 | `addr_fallback` | `12113824` | 2 |
| 1522 | 1516 | 241738387299 | `addr_fallback` | `12113824` | 2 |
| 1523 | 1522 | 241738387299 | `addr_fallback` | `12113824` | 2 |
| 1524 | 1523 | 241738387299 | `addr_fallback` | `12113824` | 2 |
| 1525 | 1524 | 241738387965 | `addr_fallback` | `12113824` | 2 |
| 1526 | 1525 | 241738387965 | `addr_fallback` | `12113824` | 2 |
| 1527 | 1526 | 241738387965 | `addr_fallback` | `12113824` | 2 |
| 1528 | 1527 | 241738388298 | `addr_fallback` | `12113824` | 2 |
| 1529 | 1528 | 241738388298 | `addr_fallback` | `12113824` | 2 |
| 1530 | 1529 | 241738388298 | `addr_fallback` | `12113824` | 2 |
| 1536 | 1530 | 241738389630 | `taint_prop` | `—` | 2 |
| 1569 | 1536 | 241738395957 | `taint_prop` | `—` | 2 |
| 1634 | 1569 | 241738623729 | `taint_prop` | `—` | 2 |
| 1685 | 1634 | 241738688997 | `taint_prop` | `—` | 2 |
| 1686 | 1685 | 241738689330 | `taint_prop` | `—` | 2 |
| 1689 | 1686 | 241738694991 | `taint_prop` | `—` | 2 |
| 1929 | 1689 | 241738926093 | `taint_prop` | `—` | 2 |
| 1933 | 1929 | 241738926426 | `taint_prop` | `—` | 2 |
| 1942 | 1933 | 241739000685 | `taint_prop` | `—` | 2 |
| 1954 | 1942 | 241739005680 | `taint_prop` | `—` | 2 |
| 1980 | 1954 | 241739051967 | `taint_prop` | `—` | 2 |
| 1983 | 1980 | 241739052300 | `taint_prop` | `—` | 2 |
| 2020 | 1983 | 241739056962 | `taint_prop` | `—` | 2 |
| 2030 | 2020 | 241739068950 | `taint_prop` | `—` | 2 |
| 2033 | 2030 | 241739068950 | `taint_prop` | `—` | 2 |
| 2097 | 2033 | 241739118900 | `taint_prop` | `—` | 2 |
| 2100 | 2097 | 241739119233 | `taint_prop` | `—` | 2 |
| 2114 | 2100 | 241739134884 | `taint_prop` | `—` | 2 |
| 2126 | 2114 | 241739139879 | `taint_prop` | `—` | 2 |
| 2130 | 2126 | 241739140545 | `taint_prop` | `—` | 2 |
| 2625 | 2130 | 241740281403 | `taint_prop` | `—` | 2 |
| 14620 | 2625 | 241770466188 | `taint_prop` | `—` | 2 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `consumer`（event_id=14620），其字段 `outcome=`、`contained=`、`detection_layer=`、`containment_reason=`。

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

