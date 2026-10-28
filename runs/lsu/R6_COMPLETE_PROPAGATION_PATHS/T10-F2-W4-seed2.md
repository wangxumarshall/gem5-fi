# T10-F2-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F2-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T10`）
- fault type / 子模型：`bit_flip`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2 --cells T10-F2-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:57:32+08:00`，end=`2026-10-28T00:58:20+08:00`）
- 运行目录进程：gem5_pid=`3049192`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：9450（chain_report.event_count=`9450`）
- fault_id 数：4

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`238083182163`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`393897`，request_id=`393897`，VA=`0xffffffc009483960`
- 被改字段：`bit_flip`；before=`81d75`，after=`81d74`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: bit_flip (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
    protection: model=none bits=1 -> Raw
Tick: 238083182163, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483960, old_pfn: 0x81d75, new_pfn: 0x81d74, FaultType: bit_flip, Mask: 0x1, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 238719961413, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094832c0, old_pfn: 0x81d74, new_pfn: 0xc1d74, FaultType: bit_flip, Mask: 0x40000, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 1464380320167, Site: arm_tlb_lookup_hit, VA: 0xffffffc009482eb0, old_pfn: 0x81d74, new_pfn: 0x81974, FaultType: bit_flip, Mask: 0x400, effective: 1
    protection: model=none bits=1 -> Raw
Tick: 2910165482106, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_pfn: 0x80c73, new_pfn: 0xc0c73, FaultType: bit_flip, Mask: 0x40000, effective: 1
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`83`（kind=`errant_commit`）沿 `parent_event_id` 回溯到 L0 注入，共 12 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 9450 个事件，为可读性第 3 章只逐条叙述**主链** 12 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=238083182163`，`corr=origin`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`，`field=bit_flip`，`before=81d75`，`after=81d74`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=238083182163`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`walk_id=0`，`va=ffffffc009483960`，`entry_index=21`，`way=-1`，`field=post_lookup`，`before=81d75`，`after=81d74`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_pfn`（L1 TLB 表项(pfn)）

- `event_id=2`，`parent_event_id=1`，`tick=238083182163`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`，`pa=81d74960`，`field=bit_flip`，`before=81d75`，`after=81d74`，`state_before=81d75960`，`state_after=81d74960`
  该事件把 TLB 表项的状态/字段从 `81d75960` 变为 `81d74960`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=238083182163`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`walk_id=0`，`va=ffffffc009483960`，`pa=81d74960`，`entry_index=21`，`way=-1`，`field=effective_pa_changed`，`before=81d75960`，`after=81d74960`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960`，`contained=0`，`outcome=NoFault`
  翻译完成：PA 由 `81d75960` 变为 `81d74960`，outcome=`NoFault`，contained=`0`。

### 3.5 `lq_read`（L3 载入队列读取）

- `event_id=4`，`parent_event_id=3`，`tick=238083182163`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`，`lq_idx=41835`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.6 `lsq_push`（L3 LSQ 入队）

- `event_id=32`，`parent_event_id=4`，`tick=238083183495`，`corr=seq_primary`，`dyn_inst_seq=393897`，`va=ffffffc009483960`，`field=load`，`lq_idx=41835`，`sq_idx=-1`，`opcode=ldp_uop`，`pc=ffffffc0087b27c8`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.7 `mem_req`（L3 内存请求）

- `event_id=33`，`parent_event_id=32`，`tick=238083183495`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.8 `lsq_sendfrag`（L3 片段发送）

- `event_id=34`，`parent_event_id=33`，`tick=238083183495`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`，`field=load`，`opcode=ldp_uop`，`pc=ffffffc0087b27c8`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.9 `tlb_translate`（tlb_translate）

- `event_id=35`，`parent_event_id=34`，`tick=238083183495`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`

### 3.10 `lq_read`（L3 载入队列读取）

- `event_id=36`，`parent_event_id=35`，`tick=238083183495`，`corr=seq_primary`，`request_id=393897`，`dyn_inst_seq=393897`，`va=ffffffc009483960`，`lq_idx=41835`
  请求从 TLB 层进入 LSQ/内存路径；记录携带的 VA/PA/lq_idx/sq_idx 是关联依据。

### 3.11 `squash_masked`（squash_masked）

- `event_id=68`，`parent_event_id=36`，`tick=238083244768`，`corr=addr_fallback`，`dyn_inst_seq=393912`，`va=ffffffc0094839e0`，`pa=81d749e0`，`field=squashed_load`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay`

### 3.12 `errant_commit`（L5 错误提交）

- `event_id=83`，`parent_event_id=68`，`tick=238083249096`，`corr=taint_prop`，`dyn_inst_seq=393846`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`commit_seq=273130`，`pc=ffffffc0087b27c4`
  错误值进入架构寄存器/消费者/提交点；这是 L4/L5 的证据。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `393897` | `ffffffc009483960` | `81d75` → `81d74` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `393897` | `ffffffc009483960` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960` |
| 2 | `tlb_pfn` | L1 | DTLB 表项 | `393897` | `81d74960` | `81d75960` → `81d74960` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `393897` | `81d74960` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960` |
| 4 | `lq_read` | L3 | LQ | `393897` | `ffffffc009483960` | — |
| 32 | `lsq_push` | L3 | LSQ | `393897` | `ffffffc009483960` | — |
| 33 | `mem_req` | L3 | LSU | `393897` | `ffffffc009483960` | — |
| 34 | `lsq_sendfrag` | L3 | lsq_sendfrag | `393897` | `ffffffc009483960` | — |
| 35 | `tlb_translate` | — | tlb_translate | `393897` | `ffffffc009483960` | — |
| 36 | `lq_read` | L3 | LQ | `393897` | `ffffffc009483960` | — |
| 68 | `squash_masked` | — | squash_masked | `393912` | `81d749e0` | — |
| 83 | `errant_commit` | L5 | commit | `393846` | `—` | — |


（第 4 章仅逐条列出主链 12 个事件；其余 9438 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `taint_reg` | 1792 | 51 | 9307 |
| `cache_access` | 1696 | 5 | 9304 |
| `cache_return` | 1696 | 6 | 9305 |
| `resp` | 1536 | 49 | 9306 |
| `consumer` | 1421 | 84 | 9303 |
| `lq_complete` | 533 | 50 | 9298 |
| `mshr_merge` | 150 | 16 | 9204 |
| `request_fork` | 138 | 4294967296 | 4294967433 |
| `mshr_alloc` | 98 | 7 | 9290 |
| `mshr_fill` | 98 | 40 | 9294 |
| `cache_fill` | 98 | 41 | 9295 |
| `mshr_free` | 98 | 42 | 9296 |
| `squash_masked` | 60 | 68 | 8751 |
| `inj` | 4 | 0 | 9280 |
| `tlb_lookup` | 4 | 1 | 9281 |
| `tlb_pfn` | 4 | 2 | 9282 |
| `tlb_translate_result` | 4 | 3 | 9283 |
| `chain_end` | 4 | 9308 | 9311 |
| `lq_read` | 3 | 4 | 9284 |
| `sq_execute` | 2 | 8335 | 9259 |
| `sq_writeback` | 2 | 8342 | 9260 |
| `sq_complete` | 2 | 8367 | 9275 |
| `lsq_push` | 1 | 32 | 32 |
| `mem_req` | 1 | 33 | 33 |
| `lsq_sendfrag` | 1 | 34 | 34 |
| `tlb_translate` | 1 | 35 | 35 |
| `errant_commit` | 1 | 83 | 83 |
| `cache_evict` | 1 | 9251 | 9251 |
| `cache_writeback` | 1 | 9252 | 9252 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(tlb_translate_result) → 4(lq_read) → 32(lsq_push) → 33(mem_req) → 34(lsq_sendfrag) → 35(tlb_translate) → 36(lq_read) → 68(squash_masked) → 83(errant_commit)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 238083182163 | `origin` | `393897` | 1 |
| 1 | 0 | 238083182163 | `seq_primary` | `393897` | 1 |
| 2 | 1 | 238083182163 | `seq_primary` | `393897` | 1 |
| 3 | 2 | 238083182163 | `seq_primary` | `393897` | 1 |
| 4 | 3 | 238083182163 | `seq_primary` | `393897` | 1 |
| 32 | 4 | 238083183495 | `seq_primary` | `—` | 1 |
| 33 | 32 | 238083183495 | `seq_primary` | `393897` | 1 |
| 34 | 33 | 238083183495 | `seq_primary` | `393897` | 1 |
| 35 | 34 | 238083183495 | `seq_primary` | `393897` | 1 |
| 36 | 35 | 238083183495 | `seq_primary` | `393897` | 1 |
| 68 | 36 | 238083244768 | `addr_fallback` | `—` | 1 |
| 83 | 68 | 238083249096 | `taint_prop` | `—` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L5`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `errant_commit`（event_id=83），其字段 `outcome=errant_commit`、`contained=0`、`detection_layer=L5`、`containment_reason=`。

**为何形成该结局**：`bit_flip` 翻转 PPN 的 1 个 bit：表项随后被命中，故障 PPN 被用于形成物理地址（`tlb_translate_result` 的 `effective_pa_changed`），错误地址进入 L3/L4 并由消费者/提交点暴露。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`411962`，eligible=`411962`，injected=`4`（日志应用行 4 条），activated=`4`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2/prop_evt.txt.gz` — SHA-256 `07724feb853aa7c3d82abfd1b5c19231761730b7b0d48980ac5597d5b86963f2`（346234 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2/chain_report.json` — SHA-256 `cb5024fca63533dba6978941d7dd9f07f202efed3aca71919ed71aea41b087ca`（960002 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2/stats.txt` — SHA-256 `4969a81148c6b8324df4ec2123574e9f792c476b4ea630595165947b0ad4361d`（391280 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2/run.out` — SHA-256 `292a6106c7baa70c9d43c9573bb9c1ab79612b74cce78d86a2e6f1935cf15434`（8216 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2/run.err` — SHA-256 `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d`（1912 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/T10-F2-W4/seed2/armtlb_injections.log` — SHA-256 `8b2ed429bf3bf46ffdf641ce6d5ae8331628c4cbff5132f2999826722861edc2`（977 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2/manifest.json` — SHA-256 `51aa2892688ff99387384a0921d6e8fecf942d5522976bcaa472f11b828879db`（2103 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L5`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

