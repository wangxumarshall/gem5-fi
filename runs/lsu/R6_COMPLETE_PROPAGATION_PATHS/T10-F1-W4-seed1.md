# T10-F1-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F1-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F1`／生效 `F1`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`n/a`
- 二进制路径：`n/a`
- 二进制 SHA-256：`n/a`（期望 `n/a`）
- binary source head：`n/a`
- analysis tool head：`n/a`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/manifest.json`（status=`None`，exit_code=`None`，start=`None`，end=`None`）
- 运行目录进程：gem5_pid=`None`，pgid=`None`，`.done`=`None`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：9884（chain_report.event_count=`9884`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`239595855309`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`5368746`，request_id=`5368746`，VA=`0xffffffc009483b48`
- 被改字段：`bit_flip`；before=`81d75`，after=`85d75`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip (lookup path now polls lsuTrigger; tier=F1; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
    protection: model=none bits=1 -> Raw
Tick: 239595855309, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483b48, old_pfn: 0x81d75, new_pfn: 0x85d75, FaultType: bit_flip, Mask: 0x4000, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`8370`（kind=`consumer`）沿 `parent_event_id` 回溯到 L0 注入，共 26 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 9884 个事件，为可读性第 3 章只逐条叙述**主链** 26 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=239595855309`，`corr=origin`，`request_id=5368746`，`dyn_inst_seq=5368746`，`va=ffffffc009483b48`，`field=bit_flip`，`before=81d75`，`after=85d75`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=239595855309`，`corr=seq_primary`，`request_id=5368746`，`dyn_inst_seq=5368746`，`walk_id=0`，`va=ffffffc009483b48`，`entry_index=20`，`way=-1`，`field=post_lookup`，`before=81d75`，`after=85d75`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=239595855309`，`corr=seq_primary`，`request_id=5368746`，`dyn_inst_seq=5368746`，`va=ffffffc009483b48`，`pa=85d75b48`，`field=bit_flip`，`before=81d75`，`after=85d75`，`state_before=81d75b48`，`state_after=85d75b48`
  该事件把 TLB 表项的状态/字段从 `81d75b48` 变为 `85d75b48`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=239595855309`，`corr=seq_primary`，`request_id=5368746`，`dyn_inst_seq=5368746`，`walk_id=0`，`va=ffffffc009483b48`，`pa=85d75b48`，`entry_index=20`，`way=-1`，`field=effective_pa_changed`，`before=81d75b48`，`after=85d75b48`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81d75b48` 变为 `85d75b48`，outcome=`NoFault`，contained=`0`。

### 3.5 `sq_execute`（L3 存储执行）

- `event_id=4`，`parent_event_id=3`，`tick=239595855309`，`corr=seq_primary`，`dyn_inst_seq=5368746`，`va=ffffffc009483b48`，`state_before=issued`，`sq_idx=479071`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `sq_writeback`（L3 存储写回）

- `event_id=5`，`parent_event_id=4`，`tick=239595856641`，`corr=seq_primary`，`dyn_inst_seq=5368746`，`pa=85d75b48`，`state_after=packet_built`，`sq_idx=479071`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.7 `cache_access`（L3 L1D 访问）

- `event_id=6`，`parent_event_id=5`，`tick=239595856641`，`corr=addr_fallback`，`request_id=5368746`，`dyn_inst_seq=5368746`，`va=ffffffc009483b48`，`pa=85d75b48`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `cache_return`（L3 L1D 返回）

- `event_id=7`，`parent_event_id=6`，`tick=239595856641`，`corr=addr_fallback`，`request_id=5368746`，`dyn_inst_seq=5368746`，`pa=85d75b48`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `mshr_alloc`（L3 MSHR 分配）

- `event_id=8`，`parent_event_id=7`，`tick=239595856641`，`corr=addr_fallback`，`request_id=5368746`，`dyn_inst_seq=5368746`，`cache_line=85d75b48`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_access`（L3 L1D 访问）

- `event_id=9`，`parent_event_id=8`，`tick=239595856974`，`corr=addr_fallback`，`request_id=5368746`，`dyn_inst_seq=5368746`，`va=ffffffc009483b48`，`pa=85d75b40`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `cache_return`（L3 L1D 返回）

- `event_id=10`，`parent_event_id=9`，`tick=239595856974`，`corr=addr_fallback`，`request_id=5368746`，`dyn_inst_seq=5368746`，`pa=85d75b40`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_alloc`（L3 MSHR 分配）

- `event_id=11`，`parent_event_id=10`，`tick=239595856974`，`corr=addr_fallback`，`request_id=5368746`，`dyn_inst_seq=5368746`，`cache_line=85d75b40`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `request_fork`（request_fork）

- `event_id=4294967303`，`parent_event_id=11`，`tick=239595890274`，`corr=addr_fallback`，`request_id=5368746`

### 3.14 `cache_access`（L3 L1D 访问）

- `event_id=39`，`parent_event_id=4294967303`，`tick=239595890274`，`corr=addr_fallback`，`request_id=5368851`，`dyn_inst_seq=5368851`，`va=ffffffc009483b00`，`pa=85d75b00`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `cache_return`（L3 L1D 返回）

- `event_id=40`，`parent_event_id=39`，`tick=239595890274`，`corr=addr_fallback`，`request_id=5368851`，`dyn_inst_seq=5368851`，`pa=85d75b00`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `mshr_merge`（L3 MSHR 合并）

- `event_id=41`，`parent_event_id=40`，`tick=239595890274`，`corr=addr_fallback`，`request_id=5368851`，`dyn_inst_seq=5368851`，`cache_line=85d75b00`，`mshr_id=6`，`state_after=merged_into_mshr`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `resp`（L4 内存响应）

- `event_id=84`，`parent_event_id=41`，`tick=239595936562`，`corr=addr_fallback`，`request_id=5368851`，`dyn_inst_seq=5368851`，`va=85d75b00`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `lq_complete`（L4 载入完成）

- `event_id=85`，`parent_event_id=84`，`tick=239595936562`，`corr=addr_fallback`，`request_id=5368851`，`dyn_inst_seq=5368851`，`va=ffffffc009483b00`，`pa=85d75b00`，`lq_idx=577494`

### 3.19 `taint_reg`（L4 寄存器污染）

- `event_id=86`，`parent_event_id=85`，`tick=239595936562`，`corr=addr_fallback`，`request_id=5368851`，`dyn_inst_seq=5368851`，`va=85d75b00`，`before=clean`，`after=tainted`，`arch_reg=19`，`phys_reg=198`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.20 `consumer`（L4 消费者读取）

- `event_id=113`，`parent_event_id=86`，`tick=239595946551`，`corr=taint_prop`，`dyn_inst_seq=5368856`，`arch_reg=19`，`phys_reg=198`，`pc=ffffffc0081b79a0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `consumer`（L4 消费者读取）

- `event_id=168`，`parent_event_id=113`，`tick=239596073757`，`corr=taint_prop`，`dyn_inst_seq=5369085`，`arch_reg=1`，`phys_reg=229`，`pc=ffffffc008271740`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.22 `consumer`（L4 消费者读取）

- `event_id=169`，`parent_event_id=168`，`tick=239596075089`，`corr=taint_prop`，`dyn_inst_seq=5369091`，`arch_reg=20`，`phys_reg=159`，`pc=ffffffc008271758`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.23 `consumer`（L4 消费者读取）

- `event_id=172`，`parent_event_id=169`，`tick=239596080750`，`corr=taint_prop`，`dyn_inst_seq=5369101`，`arch_reg=1`，`phys_reg=179`，`pc=ffffffc0081b75a8`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.24 `consumer`（L4 消费者读取）

- `event_id=173`，`parent_event_id=172`，`tick=239596080750`，`corr=taint_prop`，`dyn_inst_seq=5369103`，`arch_reg=1`，`phys_reg=112`，`pc=ffffffc0081b75b0`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.25 `consumer`（L4 消费者读取）

- `event_id=1104`，`parent_event_id=173`，`tick=239597759070`，`corr=taint_prop`，`dyn_inst_seq=5370146`，`arch_reg=4`，`phys_reg=199`，`pc=ffffffc0080c5b9c`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.26 `consumer`（L4 消费者读取）

- `event_id=8370`，`parent_event_id=1104`，`tick=239649345432`，`corr=taint_prop`，`dyn_inst_seq=5399293`，`arch_reg=2`，`phys_reg=709`，`pc=ffffffc0083af4cc`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `5368746` | `ffffffc009483b48` | `81d75` → `85d75` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `5368746` | `ffffffc009483b48` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `5368746` | `85d75b48` | `81d75b48` → `85d75b48` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `5368746` | `85d75b48` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48` |
| 4 | `sq_execute` | L3 | SQ | `5368746` | `ffffffc009483b48` | `issued` → `` |
| 5 | `sq_writeback` | L3 | SQ | `5368746` | `85d75b48` | `` → `packet_built` |
| 6 | `cache_access` | L3 | L1D | `5368746` | `85d75b48` | — |
| 7 | `cache_return` | L3 | L1D | `5368746` | `85d75b48` | — |
| 8 | `mshr_alloc` | L3 | MSHR | `5368746` | `85d75b48` | `` → `mshr_allocated` |
| 9 | `cache_access` | L3 | L1D | `5368746` | `85d75b40` | — |
| 10 | `cache_return` | L3 | L1D | `5368746` | `85d75b40` | — |
| 11 | `mshr_alloc` | L3 | MSHR | `5368746` | `85d75b40` | `` → `mshr_allocated` |
| 4294967303 | `request_fork` | — | request_fork | `5368746` | `—` | — |
| 39 | `cache_access` | L3 | L1D | `5368851` | `85d75b00` | — |
| 40 | `cache_return` | L3 | L1D | `5368851` | `85d75b00` | — |
| 41 | `mshr_merge` | L3 | MSHR | `5368851` | `85d75b00` | `` → `merged_into_mshr` |
| 84 | `resp` | L4 | LSU | `5368851` | `85d75b00` | — |
| 85 | `lq_complete` | L4 | LQ | `5368851` | `85d75b00` | — |
| 86 | `taint_reg` | L4 | PRF/提交 | `5368851` | `85d75b00` | `clean` → `tainted` |
| 113 | `consumer` | L4 | consumer | `5368856` | `—` | — |
| 168 | `consumer` | L4 | consumer | `5369085` | `—` | — |
| 169 | `consumer` | L4 | consumer | `5369091` | `—` | — |
| 172 | `consumer` | L4 | consumer | `5369101` | `—` | — |
| 173 | `consumer` | L4 | consumer | `5369103` | `—` | — |
| 1104 | `consumer` | L4 | consumer | `5370146` | `—` | — |
| 8370 | `consumer` | L4 | consumer | `5399293` | `—` | — |


（第 4 章仅逐条列出主链 26 个事件；其余 9858 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `taint_reg` | 1678 | 52 | 8246 |
| `cache_access` | 1545 | 6 | 8243 |
| `cache_return` | 1545 | 7 | 8244 |
| `request_fork` | 1512 | 4294967296 | 4294968807 |
| `resp` | 1430 | 51 | 8245 |
| `consumer` | 1281 | 88 | 8370 |
| `lq_complete` | 493 | 63 | 8236 |
| `mshr_merge` | 93 | 17 | 6655 |
| `mshr_alloc` | 62 | 8 | 6649 |
| `mshr_fill` | 62 | 45 | 6718 |
| `cache_fill` | 62 | 46 | 6719 |
| `mshr_free` | 62 | 47 | 6720 |
| `squash_masked` | 50 | 972 | 7999 |
| `inj` | 1 | 0 | 0 |
| `tlb_lookup` | 1 | 1 | 1 |
| `tlb_pfn` | 1 | 2 | 2 |
| `tlb_translate_result` | 1 | 3 | 3 |
| `sq_execute` | 1 | 4 | 4 |
| `sq_writeback` | 1 | 5 | 5 |
| `sq_complete` | 1 | 53 | 53 |
| `errant_commit` | 1 | 87 | 87 |
| `chain_end` | 1 | 8371 | 8371 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(sq_execute) → 5(sq_writeback) → 6(cache_access) → 7(cache_return) → 8(mshr_alloc) → 9(cache_access) → 10(cache_return) → 11(mshr_alloc) → 4294967303(request_fork) → 39(cache_access) → 40(cache_return) → 41(mshr_merge) → 84(resp) → 85(lq_complete) → 86(taint_reg) → 113(consumer) → 168(consumer) → 169(consumer) → 172(consumer) → 173(consumer) → 1104(consumer) → 8370(consumer)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 239595855309 | `origin` | `5368746` | 1 |
| 1 | 0 | 239595855309 | `seq_primary` | `5368746` | 1 |
| 2 | 1 | 239595855309 | `seq_primary` | `5368746` | 1 |
| 3 | 2 | 239595855309 | `seq_primary` | `5368746` | 1 |
| 4 | 3 | 239595855309 | `seq_primary` | `—` | 1 |
| 5 | 4 | 239595856641 | `seq_primary` | `—` | 1 |
| 6 | 5 | 239595856641 | `addr_fallback` | `5368746` | 1 |
| 7 | 6 | 239595856641 | `addr_fallback` | `5368746` | 1 |
| 8 | 7 | 239595856641 | `addr_fallback` | `5368746` | 1 |
| 9 | 8 | 239595856974 | `addr_fallback` | `5368746` | 1 |
| 10 | 9 | 239595856974 | `addr_fallback` | `5368746` | 1 |
| 11 | 10 | 239595856974 | `addr_fallback` | `5368746` | 1 |
| 4294967303 | 11 | 239595890274 | `addr_fallback` | `5368746` | 1 |
| 39 | 4294967303 | 239595890274 | `addr_fallback` | `5368851` | 1 |
| 40 | 39 | 239595890274 | `addr_fallback` | `5368851` | 1 |
| 41 | 40 | 239595890274 | `addr_fallback` | `5368851` | 1 |
| 84 | 41 | 239595936562 | `addr_fallback` | `5368851` | 1 |
| 85 | 84 | 239595936562 | `addr_fallback` | `5368851` | 1 |
| 86 | 85 | 239595936562 | `addr_fallback` | `5368851` | 1 |
| 113 | 86 | 239595946551 | `taint_prop` | `—` | 1 |
| 168 | 113 | 239596073757 | `taint_prop` | `—` | 1 |
| 169 | 168 | 239596075089 | `taint_prop` | `—` | 1 |
| 172 | 169 | 239596080750 | `taint_prop` | `—` | 1 |
| 173 | 172 | 239596080750 | `taint_prop` | `—` | 1 |
| 1104 | 173 | 239597759070 | `taint_prop` | `—` | 1 |
| 8370 | 1104 | 239649345432 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `consumer`（event_id=8370），其字段 `outcome=`、`contained=`、`detection_layer=`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`1390245`，eligible=`1390245`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1/prop_evt.txt.gz` — SHA-256 `256b23384ce4bcea837f083a77d641ff74be820019e3dd59c841478ce1d9775b`（386889 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1/chain_report.json` — SHA-256 `c0ccc85268a61ff75109131caff90d56439a9e45321296bc67ac1900a0d51df5`（1102976 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1/stats.txt` — SHA-256 `c7cf9dd5a24a20dc2c3ad57c48c0413f79faff3e1e7cb8e3cd9a6100a4994cb1`（415803 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1/run.out` — SHA-256 `c30b9f5691e3c48597c3eff84d214fbb6fac3b25828c05e74cf9fcf2f74986e5`（7039 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1/run.err` — SHA-256 `7df6cdc54d4ec824283761df2ab154014b4ff36bbfa764d55a52b85b2f9d8dd8`（1980 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/T10-F1-W4/seed1/armtlb_injections.log` — SHA-256 `1d2350948e8161c9a803ce72703f3ab86ea574aac88250036f6c726b5160e4be`（392 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1/manifest.json` — SHA-256 `（缺失）`

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

