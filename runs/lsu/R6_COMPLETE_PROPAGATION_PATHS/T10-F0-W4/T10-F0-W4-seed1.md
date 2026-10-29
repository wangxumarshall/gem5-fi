# T10-F0-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F0-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F0`／生效 `F0`／tier enabled=`0`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`n/a`
- 二进制路径：`n/a`
- 二进制 SHA-256：`n/a`（期望 `n/a`）
- binary source head：`n/a`
- analysis tool head：`n/a`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/manifest.json`（status=`None`，exit_code=`None`，start=`None`，end=`None`）
- 运行目录进程：gem5_pid=`None`，pgid=`None`，`.done`=`None`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：238（chain_report.event_count=`238`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`237950940537`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`301`，request_id=`301`，VA=`0xffffffc009483fa8`
- 被改字段：`bit_flip`；before=`81d75`，after=`a1d75`
- 注入器原始日志行：

```
protection: model=none bits=1 -> Raw
Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0xa1d75, FaultType: bit_flip, Mask: 0x20000, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`118`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 22 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 238 个事件，为可读性第 3 章只逐条叙述**主链** 22 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=237950940537`，`corr=origin`，`request_id=301`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`field=bit_flip`，`before=81d75`，`after=a1d75`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=237950940537`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`walk_id=0`，`va=ffffffc009483fa8`，`entry_index=0`，`way=-1`，`field=post_lookup`，`before=81d75`，`after=a1d75`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=237950940537`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`pa=a1d75fa8`，`field=bit_flip`，`before=81d75`，`after=a1d75`，`state_before=81d75fa8`，`state_after=a1d75fa8`
  该事件把 TLB 表项的状态/字段从 `81d75fa8` 变为 `a1d75fa8`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=237950940537`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`walk_id=0`，`va=ffffffc009483fa8`，`pa=a1d75fa8`，`entry_index=0`，`way=-1`，`field=effective_pa_changed`，`before=81d75fa8`，`after=a1d75fa8`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81d75fa8` 变为 `a1d75fa8`，outcome=`NoFault`，contained=`0`。

### 3.5 `sq_execute`（L3 存储执行）

- `event_id=4`，`parent_event_id=3`，`tick=237950940537`，`corr=seq_primary`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`state_before=issued`，`sq_idx=32`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `sq_writeback`（L3 存储写回）

- `event_id=5`，`parent_event_id=4`，`tick=237950941869`，`corr=seq_primary`，`dyn_inst_seq=301`，`pa=a1d75fa8`，`state_after=packet_built`，`sq_idx=32`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.7 `cache_access`（L3 L1D 访问）

- `event_id=6`，`parent_event_id=5`，`tick=237950941869`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`pa=a1d75fa8`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `cache_return`（L3 L1D 返回）

- `event_id=7`，`parent_event_id=6`，`tick=237950941869`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`pa=a1d75fa8`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `mshr_alloc`（L3 MSHR 分配）

- `event_id=8`，`parent_event_id=7`，`tick=237950941869`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`cache_line=a1d75fa8`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_access`（L3 L1D 访问）

- `event_id=15`，`parent_event_id=8`，`tick=237950942202`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`pa=a1d75f80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `cache_return`（L3 L1D 返回）

- `event_id=16`，`parent_event_id=15`，`tick=237950942202`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`pa=a1d75f80`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_alloc`（L3 MSHR 分配）

- `event_id=17`，`parent_event_id=16`，`tick=237950942202`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`cache_line=a1d75f80`，`mshr_id=3`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `mshr_fill`（L3 MSHR 填充）

- `event_id=30`，`parent_event_id=17`，`tick=237951015129`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`cache_line=a1d75f80`，`mshr_id=3`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `cache_fill`（L3 L1D 填充）

- `event_id=31`，`parent_event_id=30`，`tick=237951015129`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`pa=a1d75f80`，`cache_line=a1d75f80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_free`（L3 MSHR 释放）

- `event_id=32`，`parent_event_id=31`，`tick=237951015129`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`cache_line=a1d75f80`，`mshr_id=3`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `mshr_fill`（L3 MSHR 填充）

- `event_id=33`，`parent_event_id=32`，`tick=237951015795`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`cache_line=a1d75f80`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `cache_fill`（L3 L1D 填充）

- `event_id=34`，`parent_event_id=33`，`tick=237951015795`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`pa=a1d75f80`，`cache_line=a1d75f80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `mshr_free`（L3 MSHR 释放）

- `event_id=35`，`parent_event_id=34`，`tick=237951015795`，`corr=addr_fallback`，`request_id=301`，`dyn_inst_seq=301`，`cache_line=a1d75f80`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `resp`（L4 内存响应）

- `event_id=39`，`parent_event_id=35`，`tick=237951016128`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`va=a1d75fa8`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=40`，`parent_event_id=39`，`tick=237951016128`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`va=a1d75fa8`，`before=clean`，`after=tainted`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `sq_complete`（L4 存储完成）

- `event_id=41`，`parent_event_id=40`，`tick=237951016128`，`corr=seq_primary`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`state_after=completed`，`sq_idx=32`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.22 `errant_commit`（L5 错误提交）

- `event_id=118`，`parent_event_id=41`，`tick=237951302175`，`corr=taint_prop`，`dyn_inst_seq=391`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=161`，`pc=ffffffc0087b1000`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `301` | `ffffffc009483fa8` | `81d75` → `a1d75` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `301` | `ffffffc009483fa8` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `301` | `a1d75fa8` | `81d75fa8` → `a1d75fa8` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `301` | `a1d75fa8` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8` |
| 4 | `sq_execute` | L3 | SQ | `301` | `ffffffc009483fa8` | `issued` → `` |
| 5 | `sq_writeback` | L3 | SQ | `301` | `a1d75fa8` | `` → `packet_built` |
| 6 | `cache_access` | L3 | L1D | `301` | `a1d75fa8` | — |
| 7 | `cache_return` | L3 | L1D | `301` | `a1d75fa8` | — |
| 8 | `mshr_alloc` | L3 | MSHR | `301` | `a1d75fa8` | `` → `mshr_allocated` |
| 15 | `cache_access` | L3 | L1D | `301` | `a1d75f80` | — |
| 16 | `cache_return` | L3 | L1D | `301` | `a1d75f80` | — |
| 17 | `mshr_alloc` | L3 | MSHR | `301` | `a1d75f80` | `` → `mshr_allocated` |
| 30 | `mshr_fill` | L3 | MSHR | `301` | `a1d75f80` | `` → `filled` |
| 31 | `cache_fill` | L3 | L1D | `301` | `a1d75f80` | — |
| 32 | `mshr_free` | L3 | MSHR | `301` | `a1d75f80` | `` → `mshr_freed` |
| 33 | `mshr_fill` | L3 | MSHR | `301` | `a1d75f80` | `` → `filled` |
| 34 | `cache_fill` | L3 | L1D | `301` | `a1d75f80` | — |
| 35 | `mshr_free` | L3 | MSHR | `301` | `a1d75f80` | `` → `mshr_freed` |
| 39 | `resp` | L4 | LSU | `301` | `a1d75fa8` | — |
| 40 | `taint_reg` | L4 | PRF/提交 | `301` | `a1d75fa8` | `clean` → `tainted` |
| 41 | `sq_complete` | L4 | SQ | `301` | `ffffffc009483fa8` | `` → `completed` |
| 118 | `errant_commit` | L5 | commit | `391` | `—` | — |


（第 4 章仅逐条列出主链 22 个事件；其余 216 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 61 | 119 | 214 |
| `cache_access` | 27 | 6 | 206 |
| `cache_return` | 27 | 7 | 207 |
| `taint_reg` | 23 | 40 | 210 |
| `request_fork` | 22 | 4294967296 | 4294967317 |
| `resp` | 22 | 39 | 208 |
| `mshr_merge` | 10 | 14 | 98 |
| `mshr_alloc` | 8 | 8 | 92 |
| `mshr_fill` | 8 | 30 | 102 |
| `cache_fill` | 8 | 31 | 103 |
| `mshr_free` | 8 | 32 | 104 |
| `lq_complete` | 4 | 116 | 209 |
| `inj` | 1 | 0 | 0 |
| `tlb_lookup` | 1 | 1 | 1 |
| `tlb_pfn` | 1 | 2 | 2 |
| `tlb_translate_result` | 1 | 3 | 3 |
| `sq_execute` | 1 | 4 | 4 |
| `sq_writeback` | 1 | 5 | 5 |
| `sq_complete` | 1 | 41 | 41 |
| `errant_commit` | 1 | 118 | 118 |
| `squash_masked` | 1 | 144 | 144 |
| `chain_end` | 1 | 215 | 215 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(sq_execute) → 5(sq_writeback) → 6(cache_access) → 7(cache_return) → 8(mshr_alloc) → 15(cache_access) → 16(cache_return) → 17(mshr_alloc) → 30(mshr_fill) → 31(cache_fill) → 32(mshr_free) → 33(mshr_fill) → 34(cache_fill) → 35(mshr_free) → 39(resp) → 40(taint_reg) → 41(sq_complete) → 118(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 237950940537 | `origin` | `301` | 1 |
| 1 | 0 | 237950940537 | `seq_primary` | `301` | 1 |
| 2 | 1 | 237950940537 | `seq_primary` | `301` | 1 |
| 3 | 2 | 237950940537 | `seq_primary` | `301` | 1 |
| 4 | 3 | 237950940537 | `seq_primary` | `—` | 1 |
| 5 | 4 | 237950941869 | `seq_primary` | `—` | 1 |
| 6 | 5 | 237950941869 | `addr_fallback` | `301` | 1 |
| 7 | 6 | 237950941869 | `addr_fallback` | `301` | 1 |
| 8 | 7 | 237950941869 | `addr_fallback` | `301` | 1 |
| 15 | 8 | 237950942202 | `addr_fallback` | `301` | 1 |
| 16 | 15 | 237950942202 | `addr_fallback` | `301` | 1 |
| 17 | 16 | 237950942202 | `addr_fallback` | `301` | 1 |
| 30 | 17 | 237951015129 | `addr_fallback` | `301` | 1 |
| 31 | 30 | 237951015129 | `addr_fallback` | `301` | 1 |
| 32 | 31 | 237951015129 | `addr_fallback` | `301` | 1 |
| 33 | 32 | 237951015795 | `addr_fallback` | `301` | 1 |
| 34 | 33 | 237951015795 | `addr_fallback` | `301` | 1 |
| 35 | 34 | 237951015795 | `addr_fallback` | `301` | 1 |
| 39 | 35 | 237951016128 | `seq_primary` | `301` | 1 |
| 40 | 39 | 237951016128 | `seq_primary` | `301` | 1 |
| 41 | 40 | 237951016128 | `seq_primary` | `—` | 1 |
| 118 | 41 | 237951302175 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=118），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`150162`，eligible=`56`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1/prop_evt.txt.gz` — SHA-256 `2ed3b163e4186485406e971a6936cef04e5816ef6031e380d81038d4f5880138`（9891 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1/chain_report.json` — SHA-256 `73b4c1f880c7cc4e51f2136de1858a86b445adcf7cf2e11e99384cf9d19570b9`（10701 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1/stats.txt` — SHA-256 `3c74d224a683a57e0cb27da35ba9e69179737654f33ec61699e3a9a9317ac413`（381972 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1/run.out` — SHA-256 `ffe8c2a1ba59f0f87aaf324b17d7c63a3de60b5108fe89de7d1345f4b9fc83a1`（2239 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1/run.err` — SHA-256 `ca2a5705fb77c4088cd0623b1e77a7c516ecc8e8690060cbce63e79fb84b1a21`（1833 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/T10-F0-W4/seed1/armtlb_injections.log` — SHA-256 `2ace108f552e5017a64761fb7899a9daeb65f5965024c48927fb3bcde309a21d`（196 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1/manifest.json` — SHA-256 `（缺失）`

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

