# T10-F1-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F1-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F1`／生效 `F1`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2 --cells T10-F1-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:56:22+08:00`，end=`2026-10-28T00:57:26+08:00`）
- 运行目录进程：gem5_pid=`3045882`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：2279（chain_report.event_count=`2279`）
- fault_id 数：2

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`239345234181`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`4338322`，request_id=`4338322`，VA=`0x7f82b83d08`
- 被改字段：`bit_flip`；before=`8313b`，after=`8313a`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip (lookup path now polls lsuTrigger; tier=F1; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
    protection: model=none bits=1 -> Raw
Tick: 239345234181, Site: arm_tlb_lookup_hit, VA: 0x7f82b83d08, old_pfn: 0x8313b, new_pfn: 0x8313a, FaultType: bit_flip, Mask: 0x1, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 240401619738, Site: arm_tlb_lookup_hit, VA: 0xffffff8001af29e0, old_pfn: 0x81af2, new_pfn: 0xc1af2, FaultType: bit_flip, Mask: 0x40000, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`2125`（kind=`consumer`）沿 `parent_event_id` 回溯到 L0 注入，共 34 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 2279 个事件，为可读性第 3 章只逐条叙述**主链** 34 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=313`，`tick=240401619738`，`corr=origin`，`request_id=7213517`，`dyn_inst_seq=7213517`，`va=ffffff8001af29e0`，`field=bit_flip`，`before=81af2`，`after=c1af2`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=314`，`parent_event_id=313`，`tick=240401619738`，`corr=seq_primary`，`request_id=7213517`，`dyn_inst_seq=7213517`，`walk_id=0`，`va=ffffff8001af29e0`，`entry_index=28`，`way=-1`，`field=post_lookup`，`before=81af2`，`after=c1af2`，`state_before=vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=81af2;ap=0;mtype=2;page_size=1000;pa=81af29e0`，`state_after=vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=c1af2;ap=0;mtype=2;page_size=1000;pa=c1af29e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=81af2;ap=0;mtype=2;page_size=1000;pa=81af29e0` 变为 `vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=c1af2;ap=0;mtype=2;page_size=1000;pa=c1af29e0`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=315`，`parent_event_id=314`，`tick=240401619738`，`corr=seq_primary`，`request_id=7213517`，`dyn_inst_seq=7213517`，`va=ffffff8001af29e0`，`pa=c1af29e0`，`field=bit_flip`，`before=81af2`，`after=c1af2`，`state_before=81af29e0`，`state_after=c1af29e0`
  该事件把 TLB 表项的状态/字段从 `81af29e0` 变为 `c1af29e0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=316`，`parent_event_id=315`，`tick=240401619738`，`corr=seq_primary`，`request_id=7213517`，`dyn_inst_seq=7213517`，`walk_id=0`，`va=ffffff8001af29e0`，`pa=c1af29e0`，`entry_index=28`，`way=-1`，`field=effective_pa_changed`，`before=81af29e0`，`after=c1af29e0`，`state_before=vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=81af2;ap=0;mtype=2;page_size=1000;pa=81af29e0`，`state_after=vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=c1af2;ap=0;mtype=2;page_size=1000;pa=c1af29e0`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81af29e0` 变为 `c1af29e0`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=317`，`parent_event_id=316`，`tick=240401619738`，`corr=seq_primary`，`request_id=7213517`，`dyn_inst_seq=7213517`，`va=ffffff8001af29e0`，`lq_idx=771137`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=318`，`parent_event_id=317`，`tick=240401619738`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`va=ffffff8001af29e0`，`pa=c1af29e0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=319`，`parent_event_id=318`，`tick=240401619738`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`pa=c1af29e0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=320`，`parent_event_id=319`，`tick=240401619738`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`cache_line=c1af29e0`，`mshr_id=5`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=321`，`parent_event_id=320`，`tick=240401620071`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`va=ffffff8001af29e0`，`pa=c1af29c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=322`，`parent_event_id=321`，`tick=240401620071`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`pa=c1af29c0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=323`，`parent_event_id=322`，`tick=240401620071`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`cache_line=c1af29c0`，`mshr_id=6`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=345`，`parent_event_id=323`，`tick=240401692998`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`cache_line=c1af29c0`，`mshr_id=6`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=346`，`parent_event_id=345`，`tick=240401692998`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`pa=c1af29c0`，`cache_line=c1af29c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=347`，`parent_event_id=346`，`tick=240401692998`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`cache_line=c1af29c0`，`mshr_id=6`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=348`，`parent_event_id=347`，`tick=240401693664`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`cache_line=c1af29c0`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=349`，`parent_event_id=348`，`tick=240401693664`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`pa=c1af29c0`，`cache_line=c1af29c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=350`，`parent_event_id=349`，`tick=240401693664`，`corr=addr_fallback`，`request_id=7213517`，`dyn_inst_seq=7213517`，`cache_line=c1af29c0`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `request_fork`（request_fork）

- `event_id=4294967408`，`parent_event_id=350`，`tick=240405638049`，`corr=addr_fallback`，`request_id=7213517`

### 3.19 `cache_access`（L3 L1D 访问）

- `event_id=758`，`parent_event_id=4294967408`，`tick=240405638049`，`corr=addr_fallback`，`request_id=7216611`，`dyn_inst_seq=7216611`，`va=ffffff8001af2220`，`pa=c1af2220`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.20 `cache_return`（L3 L1D 返回）

- `event_id=759`，`parent_event_id=758`，`tick=240405638049`，`corr=addr_fallback`，`request_id=7216611`，`dyn_inst_seq=7216611`，`pa=c1af2220`，`field=hit`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.21 `resp`（L4 内存响应）

- `event_id=760`，`parent_event_id=759`，`tick=240405638382`，`corr=addr_fallback`，`request_id=7216611`，`dyn_inst_seq=7216611`，`va=c1af2220`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.22 `lq_complete`（L4 载入完成）

- `event_id=761`，`parent_event_id=760`，`tick=240405638382`，`corr=addr_fallback`，`request_id=7216611`，`dyn_inst_seq=7216611`，`va=ffffff8001af2220`，`pa=c1af2220`，`lq_idx=771343`

### 3.23 `taint_reg`（L4 寄存器污染）

- `event_id=762`，`parent_event_id=761`，`tick=240405638382`，`corr=addr_fallback`，`request_id=7216611`，`dyn_inst_seq=7216611`，`va=c1af2220`，`before=clean`，`after=tainted`，`arch_reg=3`，`phys_reg=126`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.24 `consumer`（L4 消费者读取）

- `event_id=767`，`parent_event_id=762`，`tick=240405644043`，`corr=taint_prop`，`dyn_inst_seq=7216613`，`arch_reg=3`，`phys_reg=126`，`pc=ffffffc008158884`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.25 `consumer`（L4 消费者读取）

- `event_id=1005`，`parent_event_id=767`，`tick=240406224129`，`corr=taint_prop`，`dyn_inst_seq=7217184`，`arch_reg=42`，`phys_reg=229`，`pc=ffffffc0087b14c0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.26 `consumer`（L4 消费者读取）

- `event_id=1007`，`parent_event_id=1005`，`tick=240406276077`，`corr=taint_prop`，`dyn_inst_seq=7217204`，`arch_reg=35`，`phys_reg=159`，`pc=ffffffc0087b138c`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.27 `consumer`（L4 消费者读取）

- `event_id=1009`，`parent_event_id=1007`，`tick=240406276410`，`corr=taint_prop`，`dyn_inst_seq=7217207`，`arch_reg=42`，`phys_reg=202`，`pc=ffffffc0087b1390`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.28 `consumer`（L4 消费者读取）

- `event_id=1012`，`parent_event_id=1009`，`tick=240406322697`，`corr=taint_prop`，`dyn_inst_seq=7217223`，`arch_reg=42`，`phys_reg=134`，`pc=ffffffc0087b13c0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.29 `consumer`（L4 消费者读取）

- `event_id=1014`，`parent_event_id=1012`，`tick=240406334685`，`corr=taint_prop`，`dyn_inst_seq=7217240`，`arch_reg=35`，`phys_reg=231`，`pc=ffffffc00802fb44`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.30 `consumer`（L4 消费者读取）

- `event_id=1017`，`parent_event_id=1014`，`tick=240406334685`，`corr=taint_prop`，`dyn_inst_seq=7217246`，`arch_reg=42`，`phys_reg=215`，`pc=ffffffc00802fb54`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.31 `consumer`（L4 消费者读取）

- `event_id=1020`，`parent_event_id=1017`，`tick=240406417602`，`corr=taint_prop`，`dyn_inst_seq=7217275`，`arch_reg=35`，`phys_reg=114`，`pc=ffffffc00802f9ec`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.32 `consumer`（L4 消费者读取）

- `event_id=1021`，`parent_event_id=1020`，`tick=240406417935`，`corr=taint_prop`，`dyn_inst_seq=7217279`，`arch_reg=42`，`phys_reg=6`，`pc=ffffffc00802f9f4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.33 `consumer`（L4 消费者读取）

- `event_id=1022`，`parent_event_id=1021`，`tick=240406432254`，`corr=taint_prop`，`dyn_inst_seq=7217295`，`arch_reg=29`，`phys_reg=251`，`pc=ffffffc00802f63c`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.34 `consumer`（L4 消费者读取）

- `event_id=2125`，`parent_event_id=1022`，`tick=240465149811`，`corr=taint_prop`，`dyn_inst_seq=7248399`，`arch_reg=2`，`phys_reg=441`，`pc=ffffffc0083afba8`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 313 | `inj` | L0 | CHAOSArmTLB | `7213517` | `ffffff8001af29e0` | `81af2` → `c1af2` |
| 314 | `tlb_lookup` | L1 | DTLB CAM | `7213517` | `ffffff8001af29e0` | `vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=81af2;ap=0;mtype=2;page_size=1000;pa=81af29e0` → `vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=c1af2;ap=0;mtype=2;page_size=1000;pa=c1af29e0` |
| 315 | `tlb_pfn` | L1 | DTLB 表项 | `7213517` | `c1af29e0` | `81af29e0` → `c1af29e0` |
| 316 | `tlb_translate_result` | L2 | MMU 翻译 | `7213517` | `c1af29e0` | `vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=81af2;ap=0;mtype=2;page_size=1000;pa=81af29e0` → `vpn=ffffff8001af2;asid=220;valid=1;global=1;pfn=c1af2;ap=0;mtype=2;page_size=1000;pa=c1af29e0` |
| 317 | `lq_read` | L3 | LQ | `7213517` | `ffffff8001af29e0` | — |
| 318 | `cache_access` | L3 | L1D | `7213517` | `c1af29e0` | — |
| 319 | `cache_return` | L3 | L1D | `7213517` | `c1af29e0` | — |
| 320 | `mshr_alloc` | L3 | MSHR | `7213517` | `c1af29e0` | `` → `mshr_allocated` |
| 321 | `cache_access` | L3 | L1D | `7213517` | `c1af29c0` | — |
| 322 | `cache_return` | L3 | L1D | `7213517` | `c1af29c0` | — |
| 323 | `mshr_alloc` | L3 | MSHR | `7213517` | `c1af29c0` | `` → `mshr_allocated` |
| 345 | `mshr_fill` | L3 | MSHR | `7213517` | `c1af29c0` | `` → `filled` |
| 346 | `cache_fill` | L3 | L1D | `7213517` | `c1af29c0` | — |
| 347 | `mshr_free` | L3 | MSHR | `7213517` | `c1af29c0` | `` → `mshr_freed` |
| 348 | `mshr_fill` | L3 | MSHR | `7213517` | `c1af29c0` | `` → `filled` |
| 349 | `cache_fill` | L3 | L1D | `7213517` | `c1af29c0` | — |
| 350 | `mshr_free` | L3 | MSHR | `7213517` | `c1af29c0` | `` → `mshr_freed` |
| 4294967408 | `request_fork` | — | request_fork | `7213517` | `—` | — |
| 758 | `cache_access` | L3 | L1D | `7216611` | `c1af2220` | — |
| 759 | `cache_return` | L3 | L1D | `7216611` | `c1af2220` | — |
| 760 | `resp` | L4 | LSU | `7216611` | `c1af2220` | — |
| 761 | `lq_complete` | L4 | LQ | `7216611` | `c1af2220` | — |
| 762 | `taint_reg` | L4 | PRF/提交 | `7216611` | `c1af2220` | `clean` → `tainted` |
| 767 | `consumer` | L4 | consumer | `7216613` | `—` | — |
| 1005 | `consumer` | L4 | consumer | `7217184` | `—` | — |
| 1007 | `consumer` | L4 | consumer | `7217204` | `—` | — |
| 1009 | `consumer` | L4 | consumer | `7217207` | `—` | — |
| 1012 | `consumer` | L4 | consumer | `7217223` | `—` | — |
| 1014 | `consumer` | L4 | consumer | `7217240` | `—` | — |
| 1017 | `consumer` | L4 | consumer | `7217246` | `—` | — |
| 1020 | `consumer` | L4 | consumer | `7217275` | `—` | — |
| 1021 | `consumer` | L4 | consumer | `7217279` | `—` | — |
| 1022 | `consumer` | L4 | consumer | `7217295` | `—` | — |
| 2125 | `consumer` | L4 | consumer | `7248399` | `—` | — |


（第 4 章仅逐条列出主链 34 个事件；其余 2245 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 1288 | 306 | 2125 |
| `cache_access` | 164 | 5 | 975 |
| `cache_return` | 164 | 6 | 976 |
| `request_fork` | 151 | 4294967296 | 4294967446 |
| `resp` | 146 | 17 | 977 |
| `taint_reg` | 146 | 19 | 979 |
| `lq_complete` | 104 | 18 | 978 |
| `mshr_alloc` | 22 | 7 | 635 |
| `mshr_fill` | 22 | 11 | 675 |
| `cache_fill` | 22 | 12 | 676 |
| `mshr_free` | 22 | 13 | 677 |
| `mshr_merge` | 14 | 332 | 647 |
| `inj` | 2 | 0 | 313 |
| `tlb_lookup` | 2 | 1 | 314 |
| `tlb_pfn` | 2 | 2 | 315 |
| `tlb_translate_result` | 2 | 3 | 316 |
| `lq_read` | 2 | 4 | 317 |
| `chain_end` | 2 | 2126 | 2127 |
| `errant_commit` | 1 | 20 | 20 |
| `squash_masked` | 1 | 265 | 265 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
313(inj) → 314(tlb_lookup) → 315(tlb_pfn) → 316(tlb_translate_result) → 317(lq_read) → 318(cache_access) → 319(cache_return) → 320(mshr_alloc) → 321(cache_access) → 322(cache_return) → 323(mshr_alloc) → 345(mshr_fill) → 346(cache_fill) → 347(mshr_free) → 348(mshr_fill) → 349(cache_fill) → 350(mshr_free) → 4294967408(request_fork) → 758(cache_access) → 759(cache_return) → 760(resp) → 761(lq_complete) → 762(taint_reg) → 767(consumer) → 1005(consumer) → 1007(consumer) → 1009(consumer) → 1012(consumer) → 1014(consumer) → 1017(consumer) → 1020(consumer) → 1021(consumer) → 1022(consumer) → 2125(consumer)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 313 | — | 240401619738 | `origin` | `7213517` | 2 |
| 314 | 313 | 240401619738 | `seq_primary` | `7213517` | 2 |
| 315 | 314 | 240401619738 | `seq_primary` | `7213517` | 2 |
| 316 | 315 | 240401619738 | `seq_primary` | `7213517` | 2 |
| 317 | 316 | 240401619738 | `seq_primary` | `7213517` | 2 |
| 318 | 317 | 240401619738 | `addr_fallback` | `7213517` | 2 |
| 319 | 318 | 240401619738 | `addr_fallback` | `7213517` | 2 |
| 320 | 319 | 240401619738 | `addr_fallback` | `7213517` | 2 |
| 321 | 320 | 240401620071 | `addr_fallback` | `7213517` | 2 |
| 322 | 321 | 240401620071 | `addr_fallback` | `7213517` | 2 |
| 323 | 322 | 240401620071 | `addr_fallback` | `7213517` | 2 |
| 345 | 323 | 240401692998 | `addr_fallback` | `7213517` | 2 |
| 346 | 345 | 240401692998 | `addr_fallback` | `7213517` | 2 |
| 347 | 346 | 240401692998 | `addr_fallback` | `7213517` | 2 |
| 348 | 347 | 240401693664 | `addr_fallback` | `7213517` | 2 |
| 349 | 348 | 240401693664 | `addr_fallback` | `7213517` | 2 |
| 350 | 349 | 240401693664 | `addr_fallback` | `7213517` | 2 |
| 4294967408 | 350 | 240405638049 | `addr_fallback` | `7213517` | 2 |
| 758 | 4294967408 | 240405638049 | `addr_fallback` | `7216611` | 2 |
| 759 | 758 | 240405638049 | `addr_fallback` | `7216611` | 2 |
| 760 | 759 | 240405638382 | `addr_fallback` | `7216611` | 2 |
| 761 | 760 | 240405638382 | `addr_fallback` | `7216611` | 2 |
| 762 | 761 | 240405638382 | `addr_fallback` | `7216611` | 2 |
| 767 | 762 | 240405644043 | `taint_prop` | `—` | 2 |
| 1005 | 767 | 240406224129 | `taint_prop` | `—` | 2 |
| 1007 | 1005 | 240406276077 | `taint_prop` | `—` | 2 |
| 1009 | 1007 | 240406276410 | `taint_prop` | `—` | 2 |
| 1012 | 1009 | 240406322697 | `taint_prop` | `—` | 2 |
| 1014 | 1012 | 240406334685 | `taint_prop` | `—` | 2 |
| 1017 | 1014 | 240406334685 | `taint_prop` | `—` | 2 |
| 1020 | 1017 | 240406417602 | `taint_prop` | `—` | 2 |
| 1021 | 1020 | 240406417935 | `taint_prop` | `—` | 2 |
| 1022 | 1021 | 240406432254 | `taint_prop` | `—` | 2 |
| 2125 | 1022 | 240465149811 | `taint_prop` | `—` | 2 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `consumer`（event_id=2125），其字段 `outcome=`、`contained=`、`detection_layer=`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`1901753`，eligible=`1901753`，injected=`2`（日志应用行 2 条），activated=`2`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2/prop_evt.txt.gz` — SHA-256 `c333fe9d5279850f4ad8720b339c3f0e7d88561e30e2e7abce26f944aaec2399`（136919 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2/chain_report.json` — SHA-256 `f2225ca3e09e996ac2ef2bec0de4c1bfe38fcce4ee8598b1385e50b179a87f53`（1119921 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2/stats.txt` — SHA-256 `e4630848dbc44d6b8e1c539a9418da16042db1727b5452e06d1e1ae86d07fade`（420210 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2/run.out` — SHA-256 `19b3a24f7494de960a7ff943432e9623bd3b2ab59870066619cc6d73cc265dfe`（2746 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2/run.err` — SHA-256 `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17`（1973 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/T10-F1-W4/seed2/armtlb_injections.log` — SHA-256 `63dd2cbe58dd058cb6826f5beaeb5aee70cb3faa5089a80239d544d728b57a62`（579 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2/manifest.json` — SHA-256 `3728b5265b3e6368e9f390a6b34b34d840b5829e70c59dba8cf2887b500d6c24`（2105 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

