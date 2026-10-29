# T10-F2-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F2-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`n/a`
- 二进制路径：`n/a`
- 二进制 SHA-256：`n/a`（期望 `n/a`）
- binary source head：`n/a`
- analysis tool head：`n/a`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/manifest.json`（status=`None`，exit_code=`None`，start=`None`，end=`None`）
- 运行目录进程：gem5_pid=`None`，pgid=`None`，`.done`=`None`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：6121（chain_report.event_count=`6121`）
- fault_id 数：6

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`238085259417`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`415526`，request_id=`415526`，VA=`0xffffff8001362708`
- 被改字段：`bit_flip`；before=`81362`，after=`85362`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
    protection: model=none bits=1 -> Raw
Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, old_pfn: 0x81362, new_pfn: 0x85362, FaultType: bit_flip, Mask: 0x4000, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 238527554013, Site: arm_tlb_lookup_hit, VA: 0xffffffc0089a434d, old_pfn: 0x404, new_pfn: 0x4, FaultType: bit_flip, Mask: 0x400, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 238692834567, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c07758, old_pfn: 0x80c07, new_pfn: 0x80c06, FaultType: bit_flip, Mask: 0x1, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 238783071573, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_pfn: 0x80c79, new_pfn: 0x80c7d, FaultType: bit_flip, Mask: 0x4, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 1678896244179, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_pfn: 0x80c73, new_pfn: 0x80c33, FaultType: bit_flip, Mask: 0x40, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`26`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 21 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 6121 个事件，为可读性第 3 章只逐条叙述**主链** 21 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=238085259417`，`corr=origin`，`request_id=415526`，`dyn_inst_seq=415526`，`va=ffffff8001362708`，`field=bit_flip`，`before=81362`，`after=85362`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=238085259417`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`walk_id=0`，`va=ffffff8001362708`，`entry_index=13`，`way=-1`，`field=post_lookup`，`before=81362`，`after=85362`，`state_before=vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`，`state_after=vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708` 变为 `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=238085259417`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`va=ffffff8001362708`，`pa=85362708`，`field=bit_flip`，`before=81362`，`after=85362`，`state_before=81362708`，`state_after=85362708`
  该事件把 TLB 表项的状态/字段从 `81362708` 变为 `85362708`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=238085259417`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`walk_id=0`，`va=ffffff8001362708`，`pa=85362708`，`entry_index=13`，`way=-1`，`field=effective_pa_changed`，`before=81362708`，`after=85362708`，`state_before=vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`，`state_after=vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81362708` 变为 `85362708`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=4`，`parent_event_id=3`，`tick=238085259417`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`va=ffffff8001362708`，`lq_idx=44911`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=5`，`parent_event_id=4`，`tick=238085259417`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`va=ffffff8001362708`，`pa=85362708`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=6`，`parent_event_id=5`，`tick=238085259417`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`pa=85362708`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=7`，`parent_event_id=6`，`tick=238085259417`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`cache_line=85362708`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=8`，`parent_event_id=7`，`tick=238085259750`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`va=ffffff8001362708`，`pa=85362700`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=9`，`parent_event_id=8`，`tick=238085259750`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`pa=85362700`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10`，`parent_event_id=9`，`tick=238085259750`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`cache_line=85362700`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=14`，`parent_event_id=10`，`tick=238085318691`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`cache_line=85362700`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=15`，`parent_event_id=14`，`tick=238085318691`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`pa=85362700`，`cache_line=85362700`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=16`，`parent_event_id=15`，`tick=238085318691`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`cache_line=85362700`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=17`，`parent_event_id=16`，`tick=238085319357`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`cache_line=85362700`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=18`，`parent_event_id=17`，`tick=238085319357`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`pa=85362700`，`cache_line=85362700`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=19`，`parent_event_id=18`，`tick=238085319357`，`corr=addr_fallback`，`request_id=415526`，`dyn_inst_seq=415526`，`cache_line=85362700`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `resp`（L4 内存响应）

- `event_id=20`，`parent_event_id=19`，`tick=238085319690`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`va=85362708`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `lq_complete`（L4 载入完成）

- `event_id=21`，`parent_event_id=20`，`tick=238085319690`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`va=ffffff8001362708`，`pa=85362708`，`lq_idx=44911`

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=22`，`parent_event_id=21`，`tick=238085319690`，`corr=seq_primary`，`request_id=415526`，`dyn_inst_seq=415526`，`va=85362708`，`before=clean`，`after=tainted`，`arch_reg=4`，`phys_reg=42`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `errant_commit`（L5 错误提交）

- `event_id=26`，`parent_event_id=22`，`tick=238085320689`，`corr=taint_prop`，`dyn_inst_seq=415526`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=293614`，`pc=ffffffc0087b27ac`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `415526` | `ffffff8001362708` | `81362` → `85362` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `415526` | `ffffff8001362708` | `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708` → `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `415526` | `85362708` | `81362708` → `85362708` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `415526` | `85362708` | `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708` → `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708` |
| 4 | `lq_read` | L3 | LQ | `415526` | `ffffff8001362708` | — |
| 5 | `cache_access` | L3 | L1D | `415526` | `85362708` | — |
| 6 | `cache_return` | L3 | L1D | `415526` | `85362708` | — |
| 7 | `mshr_alloc` | L3 | MSHR | `415526` | `85362708` | `` → `mshr_allocated` |
| 8 | `cache_access` | L3 | L1D | `415526` | `85362700` | — |
| 9 | `cache_return` | L3 | L1D | `415526` | `85362700` | — |
| 10 | `mshr_alloc` | L3 | MSHR | `415526` | `85362700` | `` → `mshr_allocated` |
| 14 | `mshr_fill` | L3 | MSHR | `415526` | `85362700` | `` → `filled` |
| 15 | `cache_fill` | L3 | L1D | `415526` | `85362700` | — |
| 16 | `mshr_free` | L3 | MSHR | `415526` | `85362700` | `` → `mshr_freed` |
| 17 | `mshr_fill` | L3 | MSHR | `415526` | `85362700` | `` → `filled` |
| 18 | `cache_fill` | L3 | L1D | `415526` | `85362700` | — |
| 19 | `mshr_free` | L3 | MSHR | `415526` | `85362700` | `` → `mshr_freed` |
| 20 | `resp` | L4 | LSU | `415526` | `85362708` | — |
| 21 | `lq_complete` | L4 | LQ | `415526` | `85362708` | — |
| 22 | `taint_reg` | L4 | PRF/提交 | `415526` | `85362708` | `clean` → `tainted` |
| 26 | `errant_commit` | L5 | commit | `415526` | `—` | — |


（第 4 章仅逐条列出主链 21 个事件；其余 6100 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 1950 | 27 | 5438 |
| `cache_access` | 682 | 5 | 5481 |
| `cache_return` | 682 | 6 | 5482 |
| `request_fork` | 633 | 4294967296 | 4294967928 |
| `taint_reg` | 536 | 22 | 5478 |
| `resp` | 531 | 20 | 5477 |
| `lq_complete` | 500 | 21 | 5473 |
| `squash_masked` | 87 | 258 | 5426 |
| `mshr_fill` | 75 | 14 | 5455 |
| `cache_fill` | 75 | 15 | 5456 |
| `mshr_free` | 75 | 16 | 5457 |
| `pf_demand` | 52 | 3718 | 4108 |
| `mshr_alloc` | 50 | 7 | 5451 |
| `pf_queue` | 47 | 3646 | 4059 |
| `pf_issue` | 46 | 3650 | 4063 |
| `pf_fill` | 32 | 3657 | 4097 |
| `mshr_merge` | 28 | 13 | 4204 |
| `cache_evict` | 8 | 3679 | 5479 |
| `inj` | 5 | 0 | 5441 |
| `tlb_lookup` | 5 | 1 | 5442 |
| `tlb_pfn` | 5 | 2 | 5443 |
| `tlb_translate_result` | 5 | 3 | 5444 |
| `lq_read` | 5 | 4 | 5445 |
| `chain_end` | 5 | 5483 | 5487 |
| `errant_commit` | 1 | 26 | 26 |
| `cache_writeback` | 1 | 5480 | 5480 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(lq_read) → 5(cache_access) → 6(cache_return) → 7(mshr_alloc) → 8(cache_access) → 9(cache_return) → 10(mshr_alloc) → 14(mshr_fill) → 15(cache_fill) → 16(mshr_free) → 17(mshr_fill) → 18(cache_fill) → 19(mshr_free) → 20(resp) → 21(lq_complete) → 22(taint_reg) → 26(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 238085259417 | `origin` | `415526` | 1 |
| 1 | 0 | 238085259417 | `seq_primary` | `415526` | 1 |
| 2 | 1 | 238085259417 | `seq_primary` | `415526` | 1 |
| 3 | 2 | 238085259417 | `seq_primary` | `415526` | 1 |
| 4 | 3 | 238085259417 | `seq_primary` | `415526` | 1 |
| 5 | 4 | 238085259417 | `addr_fallback` | `415526` | 1 |
| 6 | 5 | 238085259417 | `addr_fallback` | `415526` | 1 |
| 7 | 6 | 238085259417 | `addr_fallback` | `415526` | 1 |
| 8 | 7 | 238085259750 | `addr_fallback` | `415526` | 1 |
| 9 | 8 | 238085259750 | `addr_fallback` | `415526` | 1 |
| 10 | 9 | 238085259750 | `addr_fallback` | `415526` | 1 |
| 14 | 10 | 238085318691 | `addr_fallback` | `415526` | 1 |
| 15 | 14 | 238085318691 | `addr_fallback` | `415526` | 1 |
| 16 | 15 | 238085318691 | `addr_fallback` | `415526` | 1 |
| 17 | 16 | 238085319357 | `addr_fallback` | `415526` | 1 |
| 18 | 17 | 238085319357 | `addr_fallback` | `415526` | 1 |
| 19 | 18 | 238085319357 | `addr_fallback` | `415526` | 1 |
| 20 | 19 | 238085319690 | `seq_primary` | `415526` | 1 |
| 21 | 20 | 238085319690 | `seq_primary` | `415526` | 1 |
| 22 | 21 | 238085319690 | `seq_primary` | `415526` | 1 |
| 26 | 22 | 238085320689 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=26），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`560166`，eligible=`560166`，injected=`5`（日志应用行 5 条），activated=`5`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1/prop_evt.txt.gz` — SHA-256 `ee80a86656cc94f5a0cb6fba2b570a3864d8b5c68eabab8051877c6052361373`（279115 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1/chain_report.json` — SHA-256 `f426a521f0702ba922533bb09d602b068c4a68fa42fcf1bcc52428a4ccebaf4e`（1375558 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1/stats.txt` — SHA-256 `beea5f6433c15914de4bb91a11a00578e7970654e4280703340ee95a950e4278`（400639 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1/run.out` — SHA-256 `5be68e6be4697da086c3d1aee0969b986593b0cd320b88a8d1e3e65334b22e00`（10505 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1/run.err` — SHA-256 `319822eb08107697c5cf831bcef994ff52c5630a27462590693058eff7a0a78a`（2007 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/T10-F2-W4/seed1/armtlb_injections.log` — SHA-256 `3ed261cf1ec6093e5d9daebd03905f5165d81c9c080280b6f9e2c83a48d5981b`（1158 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1/manifest.json` — SHA-256 `（缺失）`

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

