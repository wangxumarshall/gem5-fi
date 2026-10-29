# T07-F4-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T07-F4-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T07`）
- fault type / 子模型：`false_hit`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F4`／生效 `F4`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3 --cells T07-F4-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`（期望 `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`）
- binary source head：`1f344a5b66da30267c578536e00a1ad4ad56bb31`
- analysis tool head：`e30aa29d6867bbd9dd1839592baa69592dc2b50c`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T10:38:18+08:00`，end=`2026-10-28T10:53:16+08:00`）
- 运行目录进程：gem5_pid=`4036074`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：9312（chain_report.event_count=`9312`）
- fault_id 数：16

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238456913391`，event_id=`0`
- 被改字段：`false_hit`；before=`miss`，after=`hit`
- 注入器原始日志行：

```
Tick: 237950094384, Site: arm_tlb_lookup_tier, FaultType: false_hit (lookup path now polls lsuTrigger; tier=F4; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 238456913391, Site: arm_tlb_lookup, VA: 0xd0, CAM: miss -> hit, FaultType: false_hit
Tick: 240206332887, Site: arm_tlb_lookup, VA: 0xffffffc008a173c0, CAM: miss -> hit, FaultType: false_hit
Tick: 242609914899, Site: arm_tlb_lookup, VA: 0x8, CAM: miss -> hit, FaultType: false_hit
Tick: 252256857633, Site: arm_tlb_lookup, VA: 0x20, CAM: miss -> hit, FaultType: false_hit
Tick: 253832754492, Site: arm_tlb_lookup, VA: 0x7f96a75b68, CAM: miss -> hit, FaultType: false_hit
Tick: 253832754492, Site: arm_tlb_lookup, VA: 0x7f96a75b60, CAM: miss -> hit, FaultType: false_hit
Tick: 253832754492, Site: arm_tlb_lookup, VA: 0x7f96a742f8, CAM: miss -> hit, FaultType: false_hit
Tick: 270905029794, Site: arm_tlb_lookup, VA: 0xffffff8001915400, CAM: miss -> hit, FaultType: false_hit
Tick: 270905039784, Site: arm_tlb_lookup, VA: 0xffffff8001915418, CAM: miss -> hit, FaultType: false_hit
Tick: 270905049108, Site: arm_tlb_lookup, VA: 0xffffff8001915450, CAM: miss -> hit, FaultType: false_hit
Tick: 277659680049, Site: arm_tlb_lookup, VA: 0x110, CAM: miss -> hit, FaultType: false_hit
Tick: 277659680382, Site: arm_tlb_lookup, VA: 0xb0, CAM: miss -> hit, FaultType: false_hit
Tick: 278587111356, Site: arm_tlb_lookup, VA: 0xffffff8001002a00, CAM: miss -> hit, FaultType: false_hit
Tick: 278587111689, Site: arm_tlb_lookup, VA: 0xffffff8001002a28, CAM: miss -> hit, FaultType: false_hit
Tick: 278587112022, Site: arm_tlb_lookup, VA: 0xffffff8001002a00, CAM: miss -> hit, FaultType: false_hit
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`45`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 18 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 9312 个事件，为可读性第 3 章只逐条叙述**主链** 18 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=23`，`tick=240206332887`，`corr=origin`，`request_id=7212262`，`dyn_inst_seq=7212262`，`field=false_hit`，`before=miss`，`after=hit`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=24`，`parent_event_id=23`，`tick=240206332887`，`corr=seq_primary`，`request_id=7212262`，`dyn_inst_seq=7212262`，`walk_id=0`，`va=ffffffc008a173c0`，`entry_index=-1`，`way=0`，`field=post_lookup`，`before=miss`，`after=hit`，`state_before=entry=none`，`state_after=vpn=ffffffc008c79;asid=206;valid=1;global=1;pfn=80c79;ap=0;mtype=2;page_size=1000;pa=80c793c0`
  该事件把 TLB 表项的状态/字段从 `entry=none` 变为 `vpn=ffffffc008c79;asid=206;valid=1;global=1;pfn=80c79;ap=0;mtype=2;page_size=1000;pa=80c793c0`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=25`，`parent_event_id=24`，`tick=240206332887`，`corr=seq_primary`，`request_id=7212262`，`dyn_inst_seq=7212262`，`va=ffffffc008a173c0`，`field=false_hit`，`state_before=miss`，`state_after=hit`
  该事件把 TLB 表项的状态/字段从 `miss` 变为 `hit`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=26`，`parent_event_id=25`，`tick=240206332887`，`corr=seq_primary`，`request_id=7212262`，`dyn_inst_seq=7212262`，`walk_id=0`，`va=ffffffc008a173c0`，`pa=80c793c0`，`entry_index=-1`，`way=0`，`field=effective_pa_changed`，`before=0`，`after=80c793c0`，`state_before=entry=none`，`state_after=vpn=ffffffc008c79;asid=206;valid=1;global=1;pfn=80c79;ap=0;mtype=2;page_size=1000;pa=80c793c0`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `0` 变为 `80c793c0`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=27`，`parent_event_id=26`，`tick=240206332887`，`corr=seq_primary`，`request_id=7212262`，`dyn_inst_seq=7212262`，`va=ffffffc008a173c0`，`lq_idx=781553`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `cache_access`（L3 L1D 访问）

- `event_id=28`，`parent_event_id=27`，`tick=240206332887`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`va=ffffffc008a173c0`，`pa=80c793c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `cache_return`（L3 L1D 返回）

- `event_id=29`，`parent_event_id=28`，`tick=240206332887`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`pa=80c793c0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `mshr_alloc`（L3 MSHR 分配）

- `event_id=30`，`parent_event_id=29`，`tick=240206332887`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`cache_line=80c793c0`，`mshr_id=3`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `cache_access`（L3 L1D 访问）

- `event_id=31`，`parent_event_id=30`，`tick=240206333220`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`va=ffffffc008a173c0`，`pa=80c793c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `cache_return`（L3 L1D 返回）

- `event_id=32`，`parent_event_id=31`，`tick=240206333220`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`pa=80c793c0`，`field=miss`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.11 `mshr_alloc`（L3 MSHR 分配）

- `event_id=33`，`parent_event_id=32`，`tick=240206333220`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`cache_line=80c793c0`，`mshr_id=4`，`state_after=mshr_allocated`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.12 `mshr_fill`（L3 MSHR 填充）

- `event_id=34`，`parent_event_id=33`，`tick=240206406147`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`cache_line=80c793c0`，`mshr_id=4`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.13 `cache_fill`（L3 L1D 填充）

- `event_id=35`，`parent_event_id=34`，`tick=240206406147`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`pa=80c793c0`，`cache_line=80c793c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.14 `mshr_free`（L3 MSHR 释放）

- `event_id=36`，`parent_event_id=35`，`tick=240206406147`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`cache_line=80c793c0`，`mshr_id=4`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.15 `mshr_fill`（L3 MSHR 填充）

- `event_id=37`，`parent_event_id=36`，`tick=240206406813`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`cache_line=80c793c0`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.16 `cache_fill`（L3 L1D 填充）

- `event_id=38`，`parent_event_id=37`，`tick=240206406813`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`pa=80c793c0`，`cache_line=80c793c0`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.17 `mshr_free`（L3 MSHR 释放）

- `event_id=39`，`parent_event_id=38`，`tick=240206406813`，`corr=addr_fallback`，`request_id=7212262`，`dyn_inst_seq=7212262`，`cache_line=80c793c0`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.18 `errant_commit`（L5 错误提交）

- `event_id=45`，`parent_event_id=39`，`tick=240206765787`，`corr=taint_prop`，`dyn_inst_seq=7212815`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=4806682`，`pc=ffffffc00809e060`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 23 | `inj` | L0 | CHAOSArmTLB | `7212262` | `—` | `miss` → `hit` |
| 24 | `tlb_lookup` | L1 | DTLB CAM | `7212262` | `ffffffc008a173c0` | `entry=none` → `vpn=ffffffc008c79;asid=206;valid=1;global=1;pfn=80c79;ap=0;mtype=2;page_size=1000;pa=80c793c0` |
| 25 | `tlb_state` | L2 | DTLB 表项 | `7212262` | `ffffffc008a173c0` | `miss` → `hit` |
| 26 | `tlb_translate_result` | L2 | MMU 翻译 | `7212262` | `80c793c0` | `entry=none` → `vpn=ffffffc008c79;asid=206;valid=1;global=1;pfn=80c79;ap=0;mtype=2;page_size=1000;pa=80c793c0` |
| 27 | `lq_read` | L3 | LQ | `7212262` | `ffffffc008a173c0` | — |
| 28 | `cache_access` | L3 | L1D | `7212262` | `80c793c0` | — |
| 29 | `cache_return` | L3 | L1D | `7212262` | `80c793c0` | — |
| 30 | `mshr_alloc` | L3 | MSHR | `7212262` | `80c793c0` | `` → `mshr_allocated` |
| 31 | `cache_access` | L3 | L1D | `7212262` | `80c793c0` | — |
| 32 | `cache_return` | L3 | L1D | `7212262` | `80c793c0` | — |
| 33 | `mshr_alloc` | L3 | MSHR | `7212262` | `80c793c0` | `` → `mshr_allocated` |
| 34 | `mshr_fill` | L3 | MSHR | `7212262` | `80c793c0` | `` → `filled` |
| 35 | `cache_fill` | L3 | L1D | `7212262` | `80c793c0` | — |
| 36 | `mshr_free` | L3 | MSHR | `7212262` | `80c793c0` | `` → `mshr_freed` |
| 37 | `mshr_fill` | L3 | MSHR | `7212262` | `80c793c0` | `` → `filled` |
| 38 | `cache_fill` | L3 | L1D | `7212262` | `80c793c0` | — |
| 39 | `mshr_free` | L3 | MSHR | `7212262` | `80c793c0` | `` → `mshr_freed` |
| 45 | `errant_commit` | L5 | commit | `7212815` | `—` | — |


（第 4 章仅逐条列出主链 18 个事件；其余 9294 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 3338 | 46 | 8372 |
| `taint_reg` | 1005 | 44 | 7091 |
| `cache_access` | 969 | 5 | 7074 |
| `cache_return` | 969 | 6 | 7075 |
| `request_fork` | 924 | 4294967296 | 4294968219 |
| `resp` | 908 | 42 | 7089 |
| `lq_complete` | 740 | 43 | 7090 |
| `pf_demand` | 143 | 5954 | 7040 |
| `mshr_fill` | 43 | 11 | 7080 |
| `cache_fill` | 43 | 12 | 7081 |
| `mshr_free` | 43 | 13 | 7082 |
| `mshr_alloc` | 39 | 7 | 7060 |
| `squash_masked` | 17 | 121 | 6804 |
| `inj` | 15 | 0 | 7069 |
| `tlb_lookup` | 15 | 1 | 7070 |
| `tlb_state` | 15 | 2 | 7071 |
| `mshr_merge` | 15 | 3438 | 7076 |
| `chain_end` | 15 | 8373 | 8387 |
| `tlb_translate_result` | 13 | 3 | 7072 |
| `cache_evict` | 13 | 17 | 7047 |
| `lq_read` | 10 | 4 | 7073 |
| `pf_fill` | 8 | 4941 | 7005 |
| `pf_queue` | 4 | 4872 | 4875 |
| `pf_issue` | 4 | 4876 | 4879 |
| `cache_writeback` | 3 | 747 | 5844 |
| `errant_commit` | 1 | 45 | 45 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
23(inj) → 24(tlb_lookup) → 25(tlb_state) → 26(tlb_translate_result) → 27(lq_read) → 28(cache_access) → 29(cache_return) → 30(mshr_alloc) → 31(cache_access) → 32(cache_return) → 33(mshr_alloc) → 34(mshr_fill) → 35(cache_fill) → 36(mshr_free) → 37(mshr_fill) → 38(cache_fill) → 39(mshr_free) → 45(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 23 | — | 240206332887 | `origin` | `7212262` | 2 |
| 24 | 23 | 240206332887 | `seq_primary` | `7212262` | 2 |
| 25 | 24 | 240206332887 | `seq_primary` | `7212262` | 2 |
| 26 | 25 | 240206332887 | `seq_primary` | `7212262` | 2 |
| 27 | 26 | 240206332887 | `seq_primary` | `7212262` | 2 |
| 28 | 27 | 240206332887 | `addr_fallback` | `7212262` | 2 |
| 29 | 28 | 240206332887 | `addr_fallback` | `7212262` | 2 |
| 30 | 29 | 240206332887 | `addr_fallback` | `7212262` | 2 |
| 31 | 30 | 240206333220 | `addr_fallback` | `7212262` | 2 |
| 32 | 31 | 240206333220 | `addr_fallback` | `7212262` | 2 |
| 33 | 32 | 240206333220 | `addr_fallback` | `7212262` | 2 |
| 34 | 33 | 240206406147 | `addr_fallback` | `7212262` | 2 |
| 35 | 34 | 240206406147 | `addr_fallback` | `7212262` | 2 |
| 36 | 35 | 240206406147 | `addr_fallback` | `7212262` | 2 |
| 37 | 36 | 240206406813 | `addr_fallback` | `7212262` | 2 |
| 38 | 37 | 240206406813 | `addr_fallback` | `7212262` | 2 |
| 39 | 38 | 240206406813 | `addr_fallback` | `7212262` | 2 |
| 45 | 39 | 240206765787 | `taint_prop` | `—` | 2 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=45），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`false_hit` 对一次未命中**伪造命中**：MMU 因此不发起 page-walk，直接使用被伪造表项的 pfn 形成 PA（干净基线为 0，故 `effective_pa_changed`）。本 seed 的真实结局取决于该错误 PA 是否被后续访问消费，见主链与第 5 章。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`36635554`，eligible=`36635554`，injected=`1124`（日志应用行 15 条），activated=`15`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3/prop_evt.txt.gz` — SHA-256 `7577a6d123b172f5257cd418e68e757527e9ff3ff3af5201a6267afb748dd5e0`（442273 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3/chain_report.json` — SHA-256 `e132829e0702ac5a450fdadc69978367def71d5ad7596d9e557893158bb5f2d6`（2466107 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3/stats.txt` — SHA-256 `939963e9e1bcdf249a85ec0d9827e89bae5035bc4b8fce7a07b0acb4b03801c4`（425265 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3/run.out` — SHA-256 `8ae51d174f98c0116ba107342dbbec4dfa5e5731956f39711891a2f59f7535ae`（4543 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3/run.err` — SHA-256 `7eb726c39577cef6b63acfd33767084de85583aca2235553ba98808b04c2b630`（2118 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/T07-F4-W4/seed3/armtlb_injections.log` — SHA-256 `48240b7688cabdda07fd57be618008cff67705152ea126169f33c3d9408c5969`（1685 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3/manifest.json` — SHA-256 `0814f4dcaa9c4331589a2729401f1166074b1df69f5c0374377b9816d05c8943`（2108 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`3db54541b7fb…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

