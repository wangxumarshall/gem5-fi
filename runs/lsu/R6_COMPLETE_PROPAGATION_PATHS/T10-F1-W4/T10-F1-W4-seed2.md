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

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`20`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 21 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 2279 个事件，为可读性第 3 章只逐条叙述**主链** 21 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=239345234181`，`corr=origin`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=7f82b83d08`，`field=bit_flip`，`before=8313b`，`after=8313a`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=239345234181`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`walk_id=0`，`va=7f82b83d08`，`entry_index=29`，`way=-1`，`field=post_lookup`，`before=8313b`，`after=8313a`，`state_before=vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08`，`state_after=vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08`
  该事件把 TLB 表项的状态/字段从 `vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08` 变为 `vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=239345234181`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=7f82b83d08`，`pa=8313ad08`，`field=bit_flip`，`before=8313b`，`after=8313a`，`state_before=8313bd08`，`state_after=8313ad08`
  该事件把 TLB 表项的状态/字段从 `8313bd08` 变为 `8313ad08`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=239345234181`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`walk_id=0`，`va=7f82b83d08`，`pa=8313ad08`，`entry_index=29`，`way=-1`，`field=effective_pa_changed`，`before=8313bd08`，`after=8313ad08`，`state_before=vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08`，`state_after=vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `8313bd08` 变为 `8313ad08`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=4`，`parent_event_id=3`，`tick=239345234181`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=7f82b83d08`，`lq_idx=470727`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=5`，`parent_event_id=4`，`tick=239345234181`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=7f82b83d08`，`pa=8313ad08`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=6`，`parent_event_id=5`，`tick=239345234181`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`pa=8313ad08`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=7`，`parent_event_id=6`，`tick=239345234181`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`cache_line=8313ad08`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=8`，`parent_event_id=7`，`tick=239345234514`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=7f82b83d08`，`pa=8313ad00`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=9`，`parent_event_id=8`，`tick=239345234514`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`pa=8313ad00`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10`，`parent_event_id=9`，`tick=239345234514`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`cache_line=8313ad00`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=11`，`parent_event_id=10`，`tick=239345293455`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`cache_line=8313ad00`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=12`，`parent_event_id=11`，`tick=239345293455`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`pa=8313ad00`，`cache_line=8313ad00`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=13`，`parent_event_id=12`，`tick=239345293455`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`cache_line=8313ad00`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=14`，`parent_event_id=13`，`tick=239345294121`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`cache_line=8313ad00`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=15`，`parent_event_id=14`，`tick=239345294121`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`pa=8313ad00`，`cache_line=8313ad00`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=16`，`parent_event_id=15`，`tick=239345294121`，`corr=addr_fallback`，`request_id=4338322`，`dyn_inst_seq=4338322`，`cache_line=8313ad00`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `resp`（L4 内存响应）

- `event_id=17`，`parent_event_id=16`，`tick=239345294454`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=8313ad08`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `lq_complete`（L4 载入完成）

- `event_id=18`，`parent_event_id=17`，`tick=239345294454`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=7f82b83d08`，`pa=8313ad08`，`lq_idx=470727`

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=19`，`parent_event_id=18`，`tick=239345294454`，`corr=seq_primary`，`request_id=4338322`，`dyn_inst_seq=4338322`，`va=8313ad08`，`before=clean`，`after=tainted`，`arch_reg=12`，`phys_reg=110`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `errant_commit`（L5 错误提交）

- `event_id=20`，`parent_event_id=19`，`tick=239345295120`，`corr=taint_prop`，`dyn_inst_seq=4338322`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=2988647`，`pc=7f82b8e3c4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `4338322` | `7f82b83d08` | `8313b` → `8313a` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `4338322` | `7f82b83d08` | `vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08` → `vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `4338322` | `8313ad08` | `8313bd08` → `8313ad08` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `4338322` | `8313ad08` | `vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08` → `vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08` |
| 4 | `lq_read` | L3 | LQ | `4338322` | `7f82b83d08` | — |
| 5 | `cache_access` | L3 | L1D | `4338322` | `8313ad08` | — |
| 6 | `cache_return` | L3 | L1D | `4338322` | `8313ad08` | — |
| 7 | `mshr_alloc` | L3 | MSHR | `4338322` | `8313ad08` | `` → `mshr_allocated` |
| 8 | `cache_access` | L3 | L1D | `4338322` | `8313ad00` | — |
| 9 | `cache_return` | L3 | L1D | `4338322` | `8313ad00` | — |
| 10 | `mshr_alloc` | L3 | MSHR | `4338322` | `8313ad00` | `` → `mshr_allocated` |
| 11 | `mshr_fill` | L3 | MSHR | `4338322` | `8313ad00` | `` → `filled` |
| 12 | `cache_fill` | L3 | L1D | `4338322` | `8313ad00` | — |
| 13 | `mshr_free` | L3 | MSHR | `4338322` | `8313ad00` | `` → `mshr_freed` |
| 14 | `mshr_fill` | L3 | MSHR | `4338322` | `8313ad00` | `` → `filled` |
| 15 | `cache_fill` | L3 | L1D | `4338322` | `8313ad00` | — |
| 16 | `mshr_free` | L3 | MSHR | `4338322` | `8313ad00` | `` → `mshr_freed` |
| 17 | `resp` | L4 | LSU | `4338322` | `8313ad08` | — |
| 18 | `lq_complete` | L4 | LQ | `4338322` | `8313ad08` | — |
| 19 | `taint_reg` | L4 | PRF/提交 | `4338322` | `8313ad08` | `clean` → `tainted` |
| 20 | `errant_commit` | L5 | commit | `4338322` | `—` | — |


（第 4 章仅逐条列出主链 21 个事件；其余 2258 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

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
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(lq_read) → 5(cache_access) → 6(cache_return) → 7(mshr_alloc) → 8(cache_access) → 9(cache_return) → 10(mshr_alloc) → 11(mshr_fill) → 12(cache_fill) → 13(mshr_free) → 14(mshr_fill) → 15(cache_fill) → 16(mshr_free) → 17(resp) → 18(lq_complete) → 19(taint_reg) → 20(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 239345234181 | `origin` | `4338322` | 1 |
| 1 | 0 | 239345234181 | `seq_primary` | `4338322` | 1 |
| 2 | 1 | 239345234181 | `seq_primary` | `4338322` | 1 |
| 3 | 2 | 239345234181 | `seq_primary` | `4338322` | 1 |
| 4 | 3 | 239345234181 | `seq_primary` | `4338322` | 1 |
| 5 | 4 | 239345234181 | `addr_fallback` | `4338322` | 1 |
| 6 | 5 | 239345234181 | `addr_fallback` | `4338322` | 1 |
| 7 | 6 | 239345234181 | `addr_fallback` | `4338322` | 1 |
| 8 | 7 | 239345234514 | `addr_fallback` | `4338322` | 1 |
| 9 | 8 | 239345234514 | `addr_fallback` | `4338322` | 1 |
| 10 | 9 | 239345234514 | `addr_fallback` | `4338322` | 1 |
| 11 | 10 | 239345293455 | `addr_fallback` | `4338322` | 1 |
| 12 | 11 | 239345293455 | `addr_fallback` | `4338322` | 1 |
| 13 | 12 | 239345293455 | `addr_fallback` | `4338322` | 1 |
| 14 | 13 | 239345294121 | `addr_fallback` | `4338322` | 1 |
| 15 | 14 | 239345294121 | `addr_fallback` | `4338322` | 1 |
| 16 | 15 | 239345294121 | `addr_fallback` | `4338322` | 1 |
| 17 | 16 | 239345294454 | `seq_primary` | `4338322` | 1 |
| 18 | 17 | 239345294454 | `seq_primary` | `4338322` | 1 |
| 19 | 18 | 239345294454 | `seq_primary` | `4338322` | 1 |
| 20 | 19 | 239345295120 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=20），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

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

