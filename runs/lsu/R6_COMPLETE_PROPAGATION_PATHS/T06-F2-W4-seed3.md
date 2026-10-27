# T06-F2-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T06-F2-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T06`）
- fault type / 子模型：`perm_subst`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3 --cells T06-F2-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`ad1a47115d778cce6283e8ffd4d0796787f546cc`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T05:06:59+08:00`，end=`2026-10-28T05:07:46+08:00`）
- 运行目录进程：gem5_pid=`3478332`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：20（chain_report.event_count=`20`）
- fault_id 数：4

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238095622710`，event_id=`0`
- 被改字段：`perm_subst`；before=`0`，after=`1`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: perm_subst (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: perm_subst (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 238095622710, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483958, old_perm_subst: 0, new_perm_subst: 1, FaultType: perm_subst
Tick: 238645142640, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094827b3, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 1801534897431, Site: arm_tlb_lookup_hit, VA: 0xffffffc009481ba0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 3043546179894, Site: arm_tlb_lookup_hit, VA: 0xffffffc009480c14, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`15`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=238095622710`，`corr=origin`，`request_id=521363`，`dyn_inst_seq=521363`，`field=perm_subst`，`before=0`，`after=1`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=238095622710`，`corr=seq_primary`，`request_id=521363`，`dyn_inst_seq=521363`，`walk_id=0`，`va=ffffffc009483958`，`entry_index=21`，`way=5`，`field=post_lookup`，`before=0`，`after=1`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75958`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d75958`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75958` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d75958`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=238095622710`，`corr=seq_primary`，`request_id=521363`，`dyn_inst_seq=521363`，`va=ffffffc009483958`，`field=perm_subst`，`state_before=0`，`state_after=1`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `1`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=238095622710`，`corr=seq_primary`，`request_id=521363`，`dyn_inst_seq=521363`，`walk_id=0`，`va=ffffffc009483958`，`pa=81d75958`，`entry_index=21`，`way=5`，`field=translation_blocked`，`before=81d75958`，`after=81d75958`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75958`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d75958`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d75958` 变为 `81d75958`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.5 `inj`（L0 注入）

- `event_id=4`，`tick=238645142640`，`corr=origin`，`request_id=903780`，`dyn_inst_seq=903780`，`field=perm_subst`，`before=0`，`after=2`

### 3.6 `tlb_lookup`（L1 TLB 查询）

- `event_id=5`，`parent_event_id=4`，`tick=238645142640`，`corr=seq_primary`，`request_id=903780`，`dyn_inst_seq=903780`，`walk_id=0`，`va=ffffffc0094827b3`，`entry_index=5`，`way=6`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d747b3`，`state_after=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d747b3`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d747b3` 变为 `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d747b3`；这就是故障值进入翻译路径的位置。

### 3.7 `tlb_state`（L2 TLB 状态）

- `event_id=6`，`parent_event_id=5`，`tick=238645142640`，`corr=seq_primary`，`request_id=903780`，`dyn_inst_seq=903780`，`va=ffffffc0094827b3`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.8 `tlb_translate_result`（L2 翻译结果）

- `event_id=7`，`parent_event_id=6`，`tick=238645142640`，`corr=seq_primary`，`request_id=903780`，`dyn_inst_seq=903780`，`walk_id=0`，`va=ffffffc0094827b3`，`pa=81d747b3`，`entry_index=5`，`way=6`，`field=translation_blocked`，`before=81d747b3`，`after=81d747b3`，`state_before=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d747b3`，`state_after=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d747b3`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d747b3` 变为 `81d747b3`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.9 `inj`（L0 注入）

- `event_id=8`，`tick=1801534897431`，`corr=origin`，`request_id=1470942`，`dyn_inst_seq=1470942`，`field=perm_subst`，`before=0`，`after=2`

### 3.10 `tlb_lookup`（L1 TLB 查询）

- `event_id=9`，`parent_event_id=8`，`tick=1801534897431`，`corr=seq_primary`，`request_id=1470942`，`dyn_inst_seq=1470942`，`walk_id=0`，`va=ffffffc009481ba0`，`entry_index=19`，`way=0`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d73ba0`，`state_after=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d73ba0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d73ba0` 变为 `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d73ba0`；这就是故障值进入翻译路径的位置。

### 3.11 `tlb_state`（L2 TLB 状态）

- `event_id=10`，`parent_event_id=9`，`tick=1801534897431`，`corr=seq_primary`，`request_id=1470942`，`dyn_inst_seq=1470942`，`va=ffffffc009481ba0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.12 `tlb_translate_result`（L2 翻译结果）

- `event_id=11`，`parent_event_id=10`，`tick=1801534897431`，`corr=seq_primary`，`request_id=1470942`，`dyn_inst_seq=1470942`，`walk_id=0`，`va=ffffffc009481ba0`，`pa=81d73ba0`，`entry_index=19`，`way=0`，`field=translation_blocked`，`before=81d73ba0`，`after=81d73ba0`，`state_before=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d73ba0`，`state_after=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d73ba0`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d73ba0` 变为 `81d73ba0`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.13 `inj`（L0 注入）

- `event_id=12`，`tick=3043546179894`，`corr=origin`，`request_id=1756682`，`dyn_inst_seq=1756682`，`field=perm_subst`，`before=0`，`after=2`

### 3.14 `tlb_lookup`（L1 TLB 查询）

- `event_id=13`，`parent_event_id=12`，`tick=3043546179894`，`corr=seq_primary`，`request_id=1756682`，`dyn_inst_seq=1756682`，`walk_id=0`，`va=ffffffc009480c14`，`entry_index=3`，`way=0`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=0;mtype=2;page_size=1000;pa=81d72c14`，`state_after=vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=2;mtype=2;page_size=1000;pa=81d72c14`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=0;mtype=2;page_size=1000;pa=81d72c14` 变为 `vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=2;mtype=2;page_size=1000;pa=81d72c14`；这就是故障值进入翻译路径的位置。

### 3.15 `tlb_state`（L2 TLB 状态）

- `event_id=14`，`parent_event_id=13`，`tick=3043546179894`，`corr=seq_primary`，`request_id=1756682`，`dyn_inst_seq=1756682`，`va=ffffffc009480c14`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.16 `tlb_translate_result`（L2 翻译结果）

- `event_id=15`，`parent_event_id=14`，`tick=3043546179894`，`corr=seq_primary`，`request_id=1756682`，`dyn_inst_seq=1756682`，`walk_id=0`，`va=ffffffc009480c14`，`pa=81d72c14`，`entry_index=3`，`way=0`，`field=translation_blocked`，`before=81d72c14`，`after=81d72c14`，`state_before=vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=0;mtype=2;page_size=1000;pa=81d72c14`，`state_after=vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=2;mtype=2;page_size=1000;pa=81d72c14`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d72c14` 变为 `81d72c14`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.17 `chain_end`（生命周期结束）

- `event_id=16`，`parent_event_id=3`，`tick=3043573328718`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.18 `chain_end`（生命周期结束）

- `event_id=17`，`parent_event_id=7`，`tick=3043573328718`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.19 `chain_end`（生命周期结束）

- `event_id=18`，`parent_event_id=11`，`tick=3043573328718`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.20 `chain_end`（生命周期结束）

- `event_id=19`，`parent_event_id=15`，`tick=3043573328718`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `521363` | `—` | `0` → `1` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `521363` | `ffffffc009483958` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75958` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d75958` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `521363` | `ffffffc009483958` | `0` → `1` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `521363` | `81d75958` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75958` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d75958` |
| 4 | `inj` | L0 | CHAOSArmTLB | `903780` | `—` | `0` → `2` |
| 5 | `tlb_lookup` | L1 | DTLB CAM | `903780` | `ffffffc0094827b3` | `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d747b3` → `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d747b3` |
| 6 | `tlb_state` | L2 | DTLB 表项 | `903780` | `ffffffc0094827b3` | `0` → `2` |
| 7 | `tlb_translate_result` | L2 | MMU 翻译 | `903780` | `81d747b3` | `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d747b3` → `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d747b3` |
| 8 | `inj` | L0 | CHAOSArmTLB | `1470942` | `—` | `0` → `2` |
| 9 | `tlb_lookup` | L1 | DTLB CAM | `1470942` | `ffffffc009481ba0` | `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d73ba0` → `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d73ba0` |
| 10 | `tlb_state` | L2 | DTLB 表项 | `1470942` | `ffffffc009481ba0` | `0` → `2` |
| 11 | `tlb_translate_result` | L2 | MMU 翻译 | `1470942` | `81d73ba0` | `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d73ba0` → `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d73ba0` |
| 12 | `inj` | L0 | CHAOSArmTLB | `1756682` | `—` | `0` → `2` |
| 13 | `tlb_lookup` | L1 | DTLB CAM | `1756682` | `ffffffc009480c14` | `vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=0;mtype=2;page_size=1000;pa=81d72c14` → `vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=2;mtype=2;page_size=1000;pa=81d72c14` |
| 14 | `tlb_state` | L2 | DTLB 表项 | `1756682` | `ffffffc009480c14` | `0` → `2` |
| 15 | `tlb_translate_result` | L2 | MMU 翻译 | `1756682` | `81d72c14` | `vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=0;mtype=2;page_size=1000;pa=81d72c14` → `vpn=ffffffc009480;asid=206;valid=1;global=1;pfn=81d72;ap=2;mtype=2;page_size=1000;pa=81d72c14` |
| 16 | `chain_end` | — | run | `—` | `—` | — |
| 17 | `chain_end` | — | run | `—` | `—` | — |
| 18 | `chain_end` | — | run | `—` | `—` | — |
| 19 | `chain_end` | — | run | `—` | `—` | — |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
12(inj) → 13(tlb_lookup) → 14(tlb_state) → 15(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 12 | — | 3043546179894 | `origin` | `1756682` | 4 |
| 13 | 12 | 3043546179894 | `seq_primary` | `1756682` | 4 |
| 14 | 13 | 3043546179894 | `seq_primary` | `1756682` | 4 |
| 15 | 14 | 3043546179894 | `seq_primary` | `1756682` | 4 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=15），其字段 `outcome=Data`、`contained=1`、`detection_layer=L2`、`containment_reason=translation_blocked`。

**为何形成该结局**：`perm_subst` 用另一个合法权限编码替换 AP：`tlb_translate_result` 的 `outcome=NoFault` 表明本次访问的权限判定**没有**因替换而改变（同一 PA、同一允许级别），因此有效 PA 不变、结局为 L2 `effective_pa_unchanged` 含住（Masked）。替换后的 AP 是否会影响其它访问，本流无法归因（链在含住时闭合）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`477697`，eligible=`477697`，injected=`4`（日志应用行 4 条），activated=`4`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3/prop_evt.txt.gz` — SHA-256 `a8fc20e9288e62a5f284b16c6a7f14612c91f1fac573fcf741b65fb81935590e`（1585 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3/chain_report.json` — SHA-256 `c87c76b4334c08e1dd100eb5540fdaf25356ff9146ec5bb0b34a65e0956c6b79`（4311 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3/stats.txt` — SHA-256 `6883ea04bf69abffb7f464f0b5657533f58de5afcf7a08abfdbce39c3498cd7b`（394852 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3/run.out` — SHA-256 `6fb71bef1cb6155877ed1b21b822b46e073be869348df8ee8e1c0df9e54f285c`（2853 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3/run.err` — SHA-256 `bb8b684acbfc1ed077589a64902034f668dfe926772db69984728fb9b1896296`（2137 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/T06-F2-W4/seed3/armtlb_injections.log` — SHA-256 `7196b0d685463b5b01cfa397d7e2edacaaba45a5a4c8d8df8d91db2625f3fee4`（896 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3/manifest.json` — SHA-256 `3d14495dbb2b4b0a9cfa92013b57a64390bf3f067bc732ef822040034b0f54c4`（2103 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

