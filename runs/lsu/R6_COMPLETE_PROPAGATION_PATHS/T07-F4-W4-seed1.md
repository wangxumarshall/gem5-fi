# T07-F4-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T07-F4-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T07`）
- fault type / 子模型：`false_hit`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F4`／生效 `F4`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1 --cells T07-F4-W4 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`（期望 `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`）
- binary source head：`1f344a5b66da30267c578536e00a1ad4ad56bb31`
- analysis tool head：`e30aa29d6867bbd9dd1839592baa69592dc2b50c`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T10:04:57+08:00`，end=`2026-10-28T10:16:04+08:00`）
- 运行目录进程：gem5_pid=`3904986`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：2289（chain_report.event_count=`2289`）
- fault_id 数：4

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238297534929`，event_id=`0`
- 被改字段：`false_hit`；before=`miss`，after=`hit`
- 注入器原始日志行：

```
Tick: 237950094384, Site: arm_tlb_lookup_tier, FaultType: false_hit (lookup path now polls lsuTrigger; tier=F4; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 238297534929, Site: arm_tlb_lookup, VA: 0xffffffc008c830d8, CAM: miss -> hit, FaultType: false_hit
Tick: 242852548356, Site: arm_tlb_lookup, VA: 0xffffffc008c0d280, CAM: miss -> hit, FaultType: false_hit
Tick: 265799144790, Site: arm_tlb_lookup, VA: 0xffffff8001002a00, CAM: miss -> hit, FaultType: false_hit
Tick: 265799145123, Site: arm_tlb_lookup, VA: 0xffffff8001002a28, CAM: miss -> hit, FaultType: false_hit
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`25`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 21 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 2289 个事件，为可读性第 3 章只逐条叙述**主链** 21 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=238297534929`，`corr=origin`，`request_id=1162674`，`dyn_inst_seq=1162674`，`field=false_hit`，`before=miss`，`after=hit`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=238297534929`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`walk_id=0`，`va=ffffffc008c830d8`，`entry_index=-1`，`way=0`，`field=post_lookup`，`before=miss`，`after=hit`，`state_before=entry=none`，`state_after=vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be90d8`
  该事件把 TLB 表项的状态/字段从 `entry=none` 变为 `vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be90d8`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=238297534929`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=ffffffc008c830d8`，`field=false_hit`，`state_before=miss`，`state_after=hit`
  该事件把 TLB 表项的状态/字段从 `miss` 变为 `hit`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=238297534929`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`walk_id=0`，`va=ffffffc008c830d8`，`pa=80be90d8`，`entry_index=-1`，`way=0`，`field=effective_pa_changed`，`before=0`，`after=80be90d8`，`state_before=entry=none`，`state_after=vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be90d8`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `0` 变为 `80be90d8`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=4`，`parent_event_id=3`，`tick=238297534929`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=ffffffc008c830d8`，`lq_idx=133250`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=5`，`parent_event_id=4`，`tick=238297534929`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=ffffffc008c830d8`，`pa=80be90d8`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=6`，`parent_event_id=5`，`tick=238297534929`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`pa=80be90d8`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=7`，`parent_event_id=6`，`tick=238297534929`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`cache_line=80be90d8`，`mshr_id=1`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=8`，`parent_event_id=7`，`tick=238297535262`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=ffffffc008c830d8`，`pa=80be90c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=9`，`parent_event_id=8`，`tick=238297535262`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`pa=80be90c0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=10`，`parent_event_id=9`，`tick=238297535262`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`cache_line=80be90c0`，`mshr_id=2`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=16`，`parent_event_id=10`，`tick=238297594203`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`cache_line=80be90c0`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=17`，`parent_event_id=16`，`tick=238297594203`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`pa=80be90c0`，`cache_line=80be90c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=18`，`parent_event_id=17`，`tick=238297594203`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`cache_line=80be90c0`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=19`，`parent_event_id=18`，`tick=238297594869`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`cache_line=80be90c0`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=20`，`parent_event_id=19`，`tick=238297594869`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`pa=80be90c0`，`cache_line=80be90c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=21`，`parent_event_id=20`，`tick=238297594869`，`corr=addr_fallback`，`request_id=1162674`，`dyn_inst_seq=1162674`，`cache_line=80be90c0`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `resp`（L4 内存响应）

- `event_id=22`，`parent_event_id=21`，`tick=238297595202`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=80be90d8`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.19 `lq_complete`（L4 载入完成）

- `event_id=23`，`parent_event_id=22`，`tick=238297595202`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=ffffffc008c830d8`，`pa=80be90d8`，`lq_idx=133250`

### 3.20 `taint_reg`（L4 寄存器污染）

- `event_id=24`，`parent_event_id=23`，`tick=238297595202`，`corr=seq_primary`，`request_id=1162674`，`dyn_inst_seq=1162674`，`va=80be90d8`，`before=clean`，`after=tainted`，`arch_reg=0`，`phys_reg=127`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

### 3.21 `errant_commit`（L5 错误提交）

- `event_id=25`，`parent_event_id=24`，`tick=238297595868`，`corr=taint_prop`，`dyn_inst_seq=1162674`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=869827`，`pc=ffffffc008181080`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `1162674` | `—` | `miss` → `hit` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `1162674` | `ffffffc008c830d8` | `entry=none` → `vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be90d8` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `1162674` | `ffffffc008c830d8` | `miss` → `hit` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `1162674` | `80be90d8` | `entry=none` → `vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be90d8` |
| 4 | `lq_read` | L3 | LQ | `1162674` | `ffffffc008c830d8` | — |
| 5 | `cache_access` | L3 | L1D | `1162674` | `80be90d8` | — |
| 6 | `cache_return` | L3 | L1D | `1162674` | `80be90d8` | — |
| 7 | `mshr_alloc` | L3 | MSHR | `1162674` | `80be90d8` | `` → `mshr_allocated` |
| 8 | `cache_access` | L3 | L1D | `1162674` | `80be90c0` | — |
| 9 | `cache_return` | L3 | L1D | `1162674` | `80be90c0` | — |
| 10 | `mshr_alloc` | L3 | MSHR | `1162674` | `80be90c0` | `` → `mshr_allocated` |
| 16 | `mshr_fill` | L3 | MSHR | `1162674` | `80be90c0` | `` → `filled` |
| 17 | `cache_fill` | L3 | L1D | `1162674` | `80be90c0` | — |
| 18 | `mshr_free` | L3 | MSHR | `1162674` | `80be90c0` | `` → `mshr_freed` |
| 19 | `mshr_fill` | L3 | MSHR | `1162674` | `80be90c0` | `` → `filled` |
| 20 | `cache_fill` | L3 | L1D | `1162674` | `80be90c0` | — |
| 21 | `mshr_free` | L3 | MSHR | `1162674` | `80be90c0` | `` → `mshr_freed` |
| 22 | `resp` | L4 | LSU | `1162674` | `80be90d8` | — |
| 23 | `lq_complete` | L4 | LQ | `1162674` | `80be90d8` | — |
| 24 | `taint_reg` | L4 | PRF/提交 | `1162674` | `80be90d8` | `clean` → `tainted` |
| 25 | `errant_commit` | L5 | commit | `1162674` | `—` | — |


（第 4 章仅逐条列出主链 21 个事件；其余 2268 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 2091 | 26 | 2269 |
| `cache_access` | 30 | 5 | 1774 |
| `cache_return` | 30 | 6 | 1775 |
| `resp` | 18 | 13 | 972 |
| `lq_complete` | 18 | 14 | 973 |
| `taint_reg` | 18 | 15 | 974 |
| `request_fork` | 15 | 4294967296 | 4294967310 |
| `cache_evict` | 9 | 312 | 1772 |
| `mshr_alloc` | 7 | 7 | 954 |
| `mshr_fill` | 7 | 16 | 966 |
| `cache_fill` | 7 | 17 | 967 |
| `mshr_free` | 7 | 18 | 968 |
| `cache_writeback` | 6 | 937 | 1773 |
| `inj` | 4 | 0 | 955 |
| `tlb_lookup` | 4 | 1 | 956 |
| `tlb_state` | 4 | 2 | 957 |
| `tlb_translate_result` | 4 | 3 | 958 |
| `lq_read` | 4 | 4 | 959 |
| `chain_end` | 4 | 2270 | 2273 |
| `errant_commit` | 1 | 25 | 25 |
| `mshr_merge` | 1 | 962 | 962 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_state) → 3(tlb_translate_result) → 4(lq_read) → 5(cache_access) → 6(cache_return) → 7(mshr_alloc) → 8(cache_access) → 9(cache_return) → 10(mshr_alloc) → 16(mshr_fill) → 17(cache_fill) → 18(mshr_free) → 19(mshr_fill) → 20(cache_fill) → 21(mshr_free) → 22(resp) → 23(lq_complete) → 24(taint_reg) → 25(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 238297534929 | `origin` | `1162674` | 1 |
| 1 | 0 | 238297534929 | `seq_primary` | `1162674` | 1 |
| 2 | 1 | 238297534929 | `seq_primary` | `1162674` | 1 |
| 3 | 2 | 238297534929 | `seq_primary` | `1162674` | 1 |
| 4 | 3 | 238297534929 | `seq_primary` | `1162674` | 1 |
| 5 | 4 | 238297534929 | `addr_fallback` | `1162674` | 1 |
| 6 | 5 | 238297534929 | `addr_fallback` | `1162674` | 1 |
| 7 | 6 | 238297534929 | `addr_fallback` | `1162674` | 1 |
| 8 | 7 | 238297535262 | `addr_fallback` | `1162674` | 1 |
| 9 | 8 | 238297535262 | `addr_fallback` | `1162674` | 1 |
| 10 | 9 | 238297535262 | `addr_fallback` | `1162674` | 1 |
| 16 | 10 | 238297594203 | `addr_fallback` | `1162674` | 1 |
| 17 | 16 | 238297594203 | `addr_fallback` | `1162674` | 1 |
| 18 | 17 | 238297594203 | `addr_fallback` | `1162674` | 1 |
| 19 | 18 | 238297594869 | `addr_fallback` | `1162674` | 1 |
| 20 | 19 | 238297594869 | `addr_fallback` | `1162674` | 1 |
| 21 | 20 | 238297594869 | `addr_fallback` | `1162674` | 1 |
| 22 | 21 | 238297595202 | `seq_primary` | `1162674` | 1 |
| 23 | 22 | 238297595202 | `seq_primary` | `1162674` | 1 |
| 24 | 23 | 238297595202 | `seq_primary` | `1162674` | 1 |
| 25 | 24 | 238297595868 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `full`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=25），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`false_hit` 对一次未命中**伪造命中**：MMU 因此不发起 page-walk，直接使用被伪造表项的 pfn 形成 PA（干净基线为 0，故 `effective_pa_changed`）。本 seed 的真实结局取决于该错误 PA 是否被后续访问消费，见主链与第 5 章。
- 该 seed 具备真实 L0→L5 ancestry（见第 5 章主链），不是由 `chain_end` 冒充的终局。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`25607183`，eligible=`25607183`，injected=`762`（日志应用行 4 条），activated=`4`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1/prop_evt.txt.gz` — SHA-256 `cc4a013cb37fc7458b927bfedc7f9b543f3ae386a641cff1300129edaa96b994`（142290 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1/chain_report.json` — SHA-256 `df3a9c754f6e76b4321cbf31049b11fc74cdf903aeaffda72dc706f19cd20a61`（1308559 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1/stats.txt` — SHA-256 `3e39a550bffd012cfe0a0834359f8e37b4b05bc9b140f6bb1a88f0edfa96577c`（426682 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1/run.out` — SHA-256 `10e335d408968cca1a279050095ac8b4fc5a3ada6497e4c062c67314a30cadb0`（2691 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1/run.err` — SHA-256 `7eb726c39577cef6b63acfd33767084de85583aca2235553ba98808b04c2b630`（2118 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/T07-F4-W4/seed1/armtlb_injections.log` — SHA-256 `4bbebfdada0af70ee3a974b78576887b5b0b83f052c289b5284126bcf43e1808`（618 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1/manifest.json` — SHA-256 `aaf074c6539f7e70c06512eaac8c9c98a603cd03a6c0e4f616b51d72265a09b3`（2107 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`3db54541b7fb…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`full`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

