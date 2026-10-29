# T07-F4-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T07-F4-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T07`）
- fault type / 子模型：`false_hit`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F4`／生效 `F4`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2 --cells T07-F4-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`（期望 `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`）
- binary source head：`1f344a5b66da30267c578536e00a1ad4ad56bb31`
- analysis tool head：`e30aa29d6867bbd9dd1839592baa69592dc2b50c`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T10:16:08+08:00`，end=`2026-10-28T10:38:15+08:00`）
- 运行目录进程：gem5_pid=`3982888`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：4807（chain_report.event_count=`4807`）
- fault_id 数：8

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`239076607410`，event_id=`0`
- 被改字段：`false_hit`；before=`miss`，after=`hit`
- 注入器原始日志行：

```
Tick: 237950094384, Site: arm_tlb_lookup_tier, FaultType: false_hit (lookup path now polls lsuTrigger; tier=F4; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 239076607410, Site: arm_tlb_lookup, VA: 0x18, CAM: miss -> hit, FaultType: false_hit
Tick: 239076608409, Site: arm_tlb_lookup, VA: 0x18, CAM: miss -> hit, FaultType: false_hit
Tick: 239654281158, Site: arm_tlb_lookup, VA: 0x7f82672872, CAM: miss -> hit, FaultType: false_hit
Tick: 244099678977, Site: arm_tlb_lookup, VA: 0x10000053f, CAM: miss -> hit, FaultType: false_hit
Tick: 266773546080, Site: arm_tlb_lookup, VA: 0x0, CAM: miss -> hit, FaultType: false_hit
Tick: 277391261736, Site: arm_tlb_lookup, VA: 0x5595794b58, CAM: miss -> hit, FaultType: false_hit
Tick: 289143202698, Site: arm_tlb_lookup, VA: 0xffffff800109dc18, CAM: miss -> hit, FaultType: false_hit
Tick: 289143202698, Site: arm_tlb_lookup, VA: 0xffffff800109dc08, CAM: miss -> hit, FaultType: false_hit
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`37`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 10 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 4807 个事件，为可读性第 3 章只逐条叙述**主链** 10 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=11`，`tick=239076608409`，`corr=origin`，`request_id=0`，`dyn_inst_seq=0`，`field=false_hit`，`before=miss`，`after=hit`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=12`，`parent_event_id=11`，`tick=239076608409`，`request_id=0`，`dyn_inst_seq=0`，`walk_id=0`，`va=18`，`entry_index=-1`，`way=0`，`field=post_lookup`，`before=miss`，`after=hit`，`state_before=entry=none`，`state_after=vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be9018`
  该事件把 TLB 表项的状态/字段从 `entry=none` 变为 `vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be9018`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=13`，`parent_event_id=12`，`tick=239076608409`，`request_id=0`，`dyn_inst_seq=0`，`va=18`，`field=false_hit`，`state_before=miss`，`state_after=hit`
  该事件把 TLB 表项的状态/字段从 `miss` 变为 `hit`；这就是故障值进入翻译路径的位置。

### 3.4 `mshr_fill`（L3 MSHR 填充）

- `event_id=14`，`parent_event_id=13`，`tick=239076666684`，`corr=addr_fallback`，`request_id=3423865`，`dyn_inst_seq=3423865`，`cache_line=80be9000`，`mshr_id=2`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.5 `cache_fill`（L3 L1D 填充）

- `event_id=15`，`parent_event_id=14`，`tick=239076666684`，`corr=addr_fallback`，`request_id=3423865`，`dyn_inst_seq=3423865`，`pa=80be9000`，`cache_line=80be9000`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.6 `mshr_free`（L3 MSHR 释放）

- `event_id=16`，`parent_event_id=15`，`tick=239076666684`，`corr=addr_fallback`，`request_id=3423865`，`dyn_inst_seq=3423865`，`cache_line=80be9000`，`mshr_id=2`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.7 `mshr_fill`（L3 MSHR 填充）

- `event_id=17`，`parent_event_id=16`，`tick=239076667350`，`corr=addr_fallback`，`request_id=3423865`，`dyn_inst_seq=3423865`，`cache_line=80be9000`，`mshr_id=0`，`state_after=filled`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.8 `cache_fill`（L3 L1D 填充）

- `event_id=18`，`parent_event_id=17`，`tick=239076667350`，`corr=addr_fallback`，`request_id=3423865`，`dyn_inst_seq=3423865`，`pa=80be9000`，`cache_line=80be9000`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.9 `mshr_free`（L3 MSHR 释放）

- `event_id=19`，`parent_event_id=18`，`tick=239076667350`，`corr=addr_fallback`，`request_id=3423865`，`dyn_inst_seq=3423865`，`cache_line=80be9000`，`mshr_id=0`，`state_after=mshr_freed`
  该事件发生在其携带的物理地址上（`pa`/`cache_line`），说明错误地址（或正常地址）已到达 cache/MSHR 层。

### 3.10 `errant_commit`（L5 错误提交）

- `event_id=37`，`parent_event_id=19`，`tick=239077512504`，`corr=taint_prop`，`dyn_inst_seq=3424476`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=2451904`，`pc=ffffffc00818ffc8`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 11 | `inj` | L0 | CHAOSArmTLB | `0` | `—` | `miss` → `hit` |
| 12 | `tlb_lookup` | L1 | DTLB CAM | `0` | `18` | `entry=none` → `vpn=ffffffc008be9;asid=206;valid=1;global=1;pfn=80be9;ap=0;mtype=2;page_size=1000;pa=80be9018` |
| 13 | `tlb_state` | L2 | DTLB 表项 | `0` | `18` | `miss` → `hit` |
| 14 | `mshr_fill` | L3 | MSHR | `3423865` | `80be9000` | `` → `filled` |
| 15 | `cache_fill` | L3 | L1D | `3423865` | `80be9000` | — |
| 16 | `mshr_free` | L3 | MSHR | `3423865` | `80be9000` | `` → `mshr_freed` |
| 17 | `mshr_fill` | L3 | MSHR | `3423865` | `80be9000` | `` → `filled` |
| 18 | `cache_fill` | L3 | L1D | `3423865` | `80be9000` | — |
| 19 | `mshr_free` | L3 | MSHR | `3423865` | `80be9000` | `` → `mshr_freed` |
| 37 | `errant_commit` | L5 | commit | `3424476` | `—` | — |


（第 4 章仅逐条列出主链 10 个事件；其余 4797 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `consumer` | 3207 | 38 | 4550 |
| `cache_access` | 281 | 5 | 4583 |
| `cache_return` | 281 | 6 | 4584 |
| `taint_reg` | 220 | 33 | 4581 |
| `request_fork` | 214 | 4294967296 | 4294967509 |
| `resp` | 212 | 31 | 4579 |
| `lq_complete` | 95 | 32 | 4580 |
| `mshr_merge` | 62 | 25 | 4570 |
| `mshr_alloc` | 35 | 7 | 4562 |
| `mshr_fill` | 35 | 14 | 4573 |
| `cache_fill` | 35 | 15 | 4574 |
| `mshr_free` | 35 | 16 | 4575 |
| `cache_evict` | 32 | 565 | 4582 |
| `cache_writeback` | 17 | 1335 | 4191 |
| `inj` | 8 | 0 | 4563 |
| `tlb_lookup` | 8 | 1 | 4564 |
| `tlb_state` | 8 | 2 | 4565 |
| `chain_end` | 8 | 4585 | 4592 |
| `tlb_translate_result` | 7 | 3 | 4566 |
| `lq_read` | 5 | 4 | 4567 |
| `errant_commit` | 1 | 37 | 37 |
| `squash_masked` | 1 | 4418 | 4418 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
11(inj) → 12(tlb_lookup) → 13(tlb_state) → 14(mshr_fill) → 15(cache_fill) → 16(mshr_free) → 17(mshr_fill) → 18(cache_fill) → 19(mshr_free) → 37(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 11 | — | 239076608409 | `origin` | `0` | 2 |
| 12 | 11 | 239076608409 | `—` | `0` | 2 |
| 13 | 12 | 239076608409 | `—` | `0` | 2 |
| 14 | 13 | 239076666684 | `addr_fallback` | `3423865` | 2 |
| 15 | 14 | 239076666684 | `addr_fallback` | `3423865` | 2 |
| 16 | 15 | 239076666684 | `addr_fallback` | `3423865` | 2 |
| 17 | 16 | 239076667350 | `addr_fallback` | `3423865` | 2 |
| 18 | 17 | 239076667350 | `addr_fallback` | `3423865` | 2 |
| 19 | 18 | 239076667350 | `addr_fallback` | `3423865` | 2 |
| 37 | 19 | 239077512504 | `taint_prop` | `—` | 2 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=37），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`false_hit` 对一次未命中**伪造命中**：MMU 因此不发起 page-walk，直接使用被伪造表项的 pfn 形成 PA（干净基线为 0，故 `effective_pa_changed`）。本 seed 的真实结局取决于该错误 PA 是否被后续访问消费，见主链与第 5 章。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`45536026`，eligible=`45536026`，injected=`1363`（日志应用行 8 条），activated=`8`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2/prop_evt.txt.gz` — SHA-256 `0b2659cf941a2b1576658dd28d07c8d85fcc172c8b8607c1ac748ecab911a2c4`（275283 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2/chain_report.json` — SHA-256 `c0617e81f880ab54ceb2ce3d874d2ec9b1dbb2ed83303cae372a84e0750e53b2`（2031610 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2/stats.txt` — SHA-256 `d0068e54bd559e39fe0b7929c452017d7343556a479083e09bdee5597e1bb19b`（427813 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2/run.out` — SHA-256 `c04dbdc9e940e6f007161614f4df216a8e59347c8633cda0e81b930aaec8a15c`（2880 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2/run.err` — SHA-256 `bf5d8eaabf4704fdb307cbb1b924b804e001458cd07a13a16513eb4db3d0d9a8`（2018 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/T07-F4-W4/seed2/armtlb_injections.log` — SHA-256 `8ad566fb1037dc0f6c576fa0bf11a8c24b0b9ccfedcaa951af4e93c02f090127`（976 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2/manifest.json` — SHA-256 `b8014c3e614a7a287bb929fcc1e9bbf5a53969e89ecb6d3d356e6c13212614c8`（2107 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`3db54541b7fb…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

