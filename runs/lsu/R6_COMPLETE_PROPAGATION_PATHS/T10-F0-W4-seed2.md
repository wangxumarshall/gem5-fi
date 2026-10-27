# T10-F0-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F0-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F0`／生效 `F0`／tier enabled=`0`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2 --cells T10-F0-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:53:56+08:00`，end=`2026-10-28T00:54:14+08:00`）
- 运行目录进程：gem5_pid=`3033154`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：433（chain_report.event_count=`433`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`237950233911`，event_id=`0`，fault_id=`1`，dyn_inst_seq=``，request_id=``，VA=`0xffffffc009483eb8`
- 被改字段：`bit_flip`；before=`81d75`，after=`81975`
- 注入器原始日志行：

```
protection: model=none bits=1 -> Raw
Tick: 237950233911, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb8, old_pfn: 0x81d75, new_pfn: 0x81975, FaultType: bit_flip, Mask: 0x400, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`283`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 18 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 433 个事件，为可读性第 3 章只逐条叙述**主链** 18 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=237950233911`，`corr=origin`，`va=ffffffc009483eb8`，`field=bit_flip`，`before=81d75`，`after=81975`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=237950233911`，`corr=addr_fallback`，`request_id=0`，`dyn_inst_seq=0`，`walk_id=0`，`va=ffffffc009483eb8`，`entry_index=0`，`way=-1`，`field=post_lookup`，`before=81d75`，`after=81975`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81975;ap=0;mtype=2;page_size=1000;pa=81975eb8`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81975;ap=0;mtype=2;page_size=1000;pa=81975eb8`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=237950233911`，`corr=addr_fallback`，`request_id=0`，`dyn_inst_seq=0`，`va=ffffffc009483eb8`，`pa=81975eb8`，`field=bit_flip`，`before=81d75`，`after=81975`，`state_before=81d75eb8`，`state_after=81975eb8`
  该事件把 TLB 表项的状态/字段从 `81d75eb8` 变为 `81975eb8`；这就是故障值进入翻译路径的位置。

### 3.4 `cache_access`（L3 L1D 访问）

- `event_id=3`，`parent_event_id=2`，`tick=237950235576`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`va=ffffffc009483eb8`，`pa=81975eb8`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.5 `cache_return`（L3 L1D 返回）

- `event_id=4`，`parent_event_id=3`，`tick=237950235576`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`pa=81975eb8`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.6 `mshr_alloc`（L3 MSHR 分配）

- `event_id=5`，`parent_event_id=4`，`tick=237950235576`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`cache_line=81975eb8`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_access`（L3 L1D 访问）

- `event_id=6`，`parent_event_id=5`，`tick=237950235909`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`va=ffffffc009483eb8`，`pa=81975e80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `cache_return`（L3 L1D 返回）

- `event_id=7`，`parent_event_id=6`，`tick=237950235909`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`pa=81975e80`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `mshr_alloc`（L3 MSHR 分配）

- `event_id=8`，`parent_event_id=7`，`tick=237950235909`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`cache_line=81975e80`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `mshr_fill`（L3 MSHR 填充）

- `event_id=82`，`parent_event_id=8`，`tick=237950340471`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`cache_line=81975e80`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `cache_fill`（L3 L1D 填充）

- `event_id=83`，`parent_event_id=82`，`tick=237950340471`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`pa=81975e80`，`cache_line=81975e80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_free`（L3 MSHR 释放）

- `event_id=84`，`parent_event_id=83`，`tick=237950340471`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`cache_line=81975e80`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `mshr_fill`（L3 MSHR 填充）

- `event_id=85`，`parent_event_id=84`，`tick=237950341137`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`cache_line=81975e80`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `cache_fill`（L3 L1D 填充）

- `event_id=86`，`parent_event_id=85`，`tick=237950341137`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`pa=81975e80`，`cache_line=81975e80`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_free`（L3 MSHR 释放）

- `event_id=87`，`parent_event_id=86`，`tick=237950341137`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`cache_line=81975e80`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `resp`（L4 内存响应）

- `event_id=88`，`parent_event_id=87`，`tick=237950341470`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`va=81975eb8`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `taint_reg`（L4 寄存器污染）

- `event_id=89`，`parent_event_id=88`，`tick=237950341470`，`corr=addr_fallback`，`request_id=32`，`dyn_inst_seq=32`，`va=81975eb8`，`before=clean`，`after=tainted`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.18 `errant_commit`（L5 错误提交）

- `event_id=283`，`parent_event_id=89`，`tick=237951341802`，`corr=taint_prop`，`dyn_inst_seq=391`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=161`，`pc=ffffffc0087b1000`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `—` | `ffffffc009483eb8` | `81d75` → `81975` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `0` | `ffffffc009483eb8` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81975;ap=0;mtype=2;page_size=1000;pa=81975eb8` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `0` | `81975eb8` | `81d75eb8` → `81975eb8` |
| 3 | `cache_access` | L3 | L1D | `32` | `81975eb8` | — |
| 4 | `cache_return` | L3 | L1D | `32` | `81975eb8` | — |
| 5 | `mshr_alloc` | L3 | MSHR | `32` | `81975eb8` | `` → `mshr_allocated` |
| 6 | `cache_access` | L3 | L1D | `32` | `81975e80` | — |
| 7 | `cache_return` | L3 | L1D | `32` | `81975e80` | — |
| 8 | `mshr_alloc` | L3 | MSHR | `32` | `81975e80` | `` → `mshr_allocated` |
| 82 | `mshr_fill` | L3 | MSHR | `32` | `81975e80` | `` → `filled` |
| 83 | `cache_fill` | L3 | L1D | `32` | `81975e80` | — |
| 84 | `mshr_free` | L3 | MSHR | `32` | `81975e80` | `` → `mshr_freed` |
| 85 | `mshr_fill` | L3 | MSHR | `32` | `81975e80` | `` → `filled` |
| 86 | `cache_fill` | L3 | L1D | `32` | `81975e80` | — |
| 87 | `mshr_free` | L3 | MSHR | `32` | `81975e80` | `` → `mshr_freed` |
| 88 | `resp` | L4 | LSU | `32` | `81975eb8` | — |
| 89 | `taint_reg` | L4 | PRF/提交 | `32` | `81975eb8` | `clean` → `tainted` |
| 283 | `errant_commit` | L5 | commit | `391` | `—` | — |


（第 4 章仅逐条列出主链 18 个事件；其余 415 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 61 | 284 | 379 |
| `cache_access` | 60 | 3 | 371 |
| `cache_return` | 60 | 4 | 372 |
| `taint_reg` | 53 | 64 | 375 |
| `request_fork` | 52 | 4294967296 | 4294967347 |
| `resp` | 52 | 63 | 373 |
| `mshr_merge` | 29 | 17 | 263 |
| `mshr_alloc` | 14 | 5 | 257 |
| `mshr_fill` | 14 | 57 | 267 |
| `cache_fill` | 14 | 58 | 268 |
| `mshr_free` | 14 | 59 | 269 |
| `lq_complete` | 4 | 281 | 374 |
| `inj` | 1 | 0 | 0 |
| `tlb_lookup` | 1 | 1 | 1 |
| `tlb_pfn` | 1 | 2 | 2 |
| `errant_commit` | 1 | 283 | 283 |
| `squash_masked` | 1 | 309 | 309 |
| `chain_end` | 1 | 380 | 380 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(cache_access) → 4(cache_return) → 5(mshr_alloc) → 6(cache_access) → 7(cache_return) → 8(mshr_alloc) → 82(mshr_fill) → 83(cache_fill) → 84(mshr_free) → 85(mshr_fill) → 86(cache_fill) → 87(mshr_free) → 88(resp) → 89(taint_reg) → 283(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 237950233911 | `origin` | `—` | 1 |
| 1 | 0 | 237950233911 | `addr_fallback` | `0` | 1 |
| 2 | 1 | 237950233911 | `addr_fallback` | `0` | 1 |
| 3 | 2 | 237950235576 | `addr_fallback` | `32` | 1 |
| 4 | 3 | 237950235576 | `addr_fallback` | `32` | 1 |
| 5 | 4 | 237950235576 | `addr_fallback` | `32` | 1 |
| 6 | 5 | 237950235909 | `addr_fallback` | `32` | 1 |
| 7 | 6 | 237950235909 | `addr_fallback` | `32` | 1 |
| 8 | 7 | 237950235909 | `addr_fallback` | `32` | 1 |
| 82 | 8 | 237950340471 | `addr_fallback` | `32` | 1 |
| 83 | 82 | 237950340471 | `addr_fallback` | `32` | 1 |
| 84 | 83 | 237950340471 | `addr_fallback` | `32` | 1 |
| 85 | 84 | 237950341137 | `addr_fallback` | `32` | 1 |
| 86 | 85 | 237950341137 | `addr_fallback` | `32` | 1 |
| 87 | 86 | 237950341137 | `addr_fallback` | `32` | 1 |
| 88 | 87 | 237950341470 | `addr_fallback` | `32` | 1 |
| 89 | 88 | 237950341470 | `addr_fallback` | `32` | 1 |
| 283 | 89 | 237951341802 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=283），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`150160`，eligible=`2`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2/prop_evt.txt.gz` — SHA-256 `35ee3df2fd242e52b6397a695587ede6947159626fdd2cd163cedb1333be94a5`（16240 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2/chain_report.json` — SHA-256 `2e9718aee11aa996c48f47f3abc61ffe79773a39af1f6bf5f4cd982ba1a3caac`（10661 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2/stats.txt` — SHA-256 `4031f6af8b65f360fe4ab41c61070d34d52f8aefb3969aca75fdf557f6ab44d2`（381972 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2/run.out` — SHA-256 `61531ca13849ccc9ce01f0a7f0f1c4c5f5fc41971f238b09b4d6f892f8ba0f31`（2299 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2/run.err` — SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`（1726 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/T10-F0-W4/seed2/armtlb_injections.log` — SHA-256 `01f464e00985151d63ee83c297c7b4bf1df531906f8e2fd1901801d575d10546`（194 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2/manifest.json` — SHA-256 `ff7b42f4d815479df8a9ae2278c31da8bb06bfd8579c59e3554528830c79a6a3`（2098 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

