# T06-F2-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T06-F2-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T06`）
- fault type / 子模型：`perm_subst`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2 --cells T06-F2-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`ad1a47115d778cce6283e8ffd4d0796787f546cc`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T05:05:40+08:00`，end=`2026-10-28T05:06:56+08:00`）
- 运行目录进程：gem5_pid=`3477766`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：35（chain_report.event_count=`35`）
- fault_id 数：7

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238083224787`，event_id=`0`
- 被改字段：`perm_subst`；before=`0`，after=`1`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: perm_subst (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: perm_subst (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 238083224787, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094839a0, old_perm_subst: 0, new_perm_subst: 1, FaultType: perm_subst
Tick: 238723651053, Site: arm_tlb_lookup_hit, VA: 0xffffffc008e05018, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 1487736186588, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 2933521343865, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst
Tick: 4156083003753, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 5364565994070, Site: arm_tlb_lookup_hit, VA: 0xffffffc009482480, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 5364646522794, Site: arm_tlb_lookup_hit, VA: 0xffffffc008996b80, old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`27`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=238083224787`，`corr=origin`，`request_id=394307`，`dyn_inst_seq=394307`，`field=perm_subst`，`before=0`，`after=1`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=238083224787`，`corr=seq_primary`，`request_id=394307`，`dyn_inst_seq=394307`，`walk_id=0`，`va=ffffffc0094839a0`，`entry_index=21`，`way=5`，`field=post_lookup`，`before=0`，`after=1`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=238083224787`，`corr=seq_primary`，`request_id=394307`，`dyn_inst_seq=394307`，`va=ffffffc0094839a0`，`field=perm_subst`，`state_before=0`，`state_after=1`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `1`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=238083224787`，`corr=seq_primary`，`request_id=394307`，`dyn_inst_seq=394307`，`walk_id=0`，`va=ffffffc0094839a0`，`pa=81d759a0`，`entry_index=21`，`way=5`，`field=translation_blocked`，`before=81d759a0`，`after=81d759a0`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d759a0` 变为 `81d759a0`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.5 `inj`（L0 注入）

- `event_id=4`，`tick=238723651053`，`corr=origin`，`request_id=848321`，`dyn_inst_seq=848321`，`field=perm_subst`，`before=0`，`after=2`

### 3.6 `tlb_lookup`（L1 TLB 查询）

- `event_id=5`，`parent_event_id=4`，`tick=238723651053`，`corr=seq_primary`，`request_id=848321`，`dyn_inst_seq=848321`，`walk_id=0`，`va=ffffffc008e05018`，`entry_index=17`，`way=6`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=0;mtype=1;page_size=1000;pa=1c090018`，`state_after=vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=2;mtype=1;page_size=1000;pa=1c090018`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=0;mtype=1;page_size=1000;pa=1c090018` 变为 `vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=2;mtype=1;page_size=1000;pa=1c090018`；这就是故障值进入翻译路径的位置。

### 3.7 `tlb_state`（L2 TLB 状态）

- `event_id=6`，`parent_event_id=5`，`tick=238723651053`，`corr=seq_primary`，`request_id=848321`，`dyn_inst_seq=848321`，`va=ffffffc008e05018`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.8 `tlb_translate_result`（L2 翻译结果）

- `event_id=7`，`parent_event_id=6`，`tick=238723651053`，`corr=seq_primary`，`request_id=848321`，`dyn_inst_seq=848321`，`walk_id=0`，`va=ffffffc008e05018`，`pa=1c090018`，`entry_index=17`，`way=6`，`field=effective_pa_unchanged`，`before=1c090018`，`after=1c090018`，`state_before=vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=0;mtype=1;page_size=1000;pa=1c090018`，`state_after=vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=2;mtype=1;page_size=1000;pa=1c090018`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `1c090018` 变为 `1c090018`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.9 `inj`（L0 注入）

- `event_id=8`，`tick=1487736186588`，`corr=origin`，`request_id=1300814`，`dyn_inst_seq=1300814`，`field=perm_subst`，`before=0`，`after=2`

### 3.10 `tlb_lookup`（L1 TLB 查询）

- `event_id=9`，`parent_event_id=8`，`tick=1487736186588`，`corr=seq_primary`，`request_id=1300814`，`dyn_inst_seq=1300814`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=9`，`way=0`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.11 `tlb_state`（L2 TLB 状态）

- `event_id=10`，`parent_event_id=9`，`tick=1487736186588`，`corr=seq_primary`，`request_id=1300814`，`dyn_inst_seq=1300814`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.12 `tlb_translate_result`（L2 翻译结果）

- `event_id=11`，`parent_event_id=10`，`tick=1487736186588`，`corr=seq_primary`，`request_id=1300814`，`dyn_inst_seq=1300814`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=9`，`way=0`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.13 `inj`（L0 注入）

- `event_id=12`，`tick=2933521343865`，`corr=origin`，`request_id=1727206`，`dyn_inst_seq=1727206`，`field=perm_subst`，`before=2`，`after=0`

### 3.14 `tlb_lookup`（L1 TLB 查询）

- `event_id=13`，`parent_event_id=12`，`tick=2933521343865`，`corr=seq_primary`，`request_id=1727206`，`dyn_inst_seq=1727206`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=9`，`way=1`，`field=post_lookup`，`before=2`，`after=0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.15 `tlb_state`（L2 TLB 状态）

- `event_id=14`，`parent_event_id=13`，`tick=2933521343865`，`corr=seq_primary`，`request_id=1727206`，`dyn_inst_seq=1727206`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=2`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `2` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.16 `tlb_translate_result`（L2 翻译结果）

- `event_id=15`，`parent_event_id=14`，`tick=2933521343865`，`corr=seq_primary`，`request_id=1727206`，`dyn_inst_seq=1727206`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=9`，`way=1`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.17 `inj`（L0 注入）

- `event_id=16`，`tick=4156083003753`，`corr=origin`，`request_id=2087770`，`dyn_inst_seq=2087770`，`field=perm_subst`，`before=0`，`after=2`

### 3.18 `tlb_lookup`（L1 TLB 查询）

- `event_id=17`，`parent_event_id=16`，`tick=4156083003753`，`corr=seq_primary`，`request_id=2087770`，`dyn_inst_seq=2087770`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=9`，`way=0`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.19 `tlb_state`（L2 TLB 状态）

- `event_id=18`，`parent_event_id=17`，`tick=4156083003753`，`corr=seq_primary`，`request_id=2087770`，`dyn_inst_seq=2087770`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.20 `tlb_translate_result`（L2 翻译结果）

- `event_id=19`，`parent_event_id=18`，`tick=4156083003753`，`corr=seq_primary`，`request_id=2087770`，`dyn_inst_seq=2087770`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=9`，`way=0`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.21 `inj`（L0 注入）

- `event_id=20`，`tick=5364565994070`，`corr=origin`，`request_id=2444151`，`dyn_inst_seq=2444151`，`field=perm_subst`，`before=0`，`after=2`

### 3.22 `tlb_lookup`（L1 TLB 查询）

- `event_id=21`，`parent_event_id=20`，`tick=5364565994070`，`corr=seq_primary`，`request_id=2444151`，`dyn_inst_seq=2444151`，`walk_id=0`，`va=ffffffc009482480`，`entry_index=5`，`way=0`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74480`，`state_after=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d74480`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74480` 变为 `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d74480`；这就是故障值进入翻译路径的位置。

### 3.23 `tlb_state`（L2 TLB 状态）

- `event_id=22`，`parent_event_id=21`，`tick=5364565994070`，`corr=seq_primary`，`request_id=2444151`，`dyn_inst_seq=2444151`，`va=ffffffc009482480`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.24 `tlb_translate_result`（L2 翻译结果）

- `event_id=23`，`parent_event_id=22`，`tick=5364565994070`，`corr=seq_primary`，`request_id=2444151`，`dyn_inst_seq=2444151`，`walk_id=0`，`va=ffffffc009482480`，`pa=81d74480`，`entry_index=5`，`way=0`，`field=translation_blocked`，`before=81d74480`，`after=81d74480`，`state_before=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74480`，`state_after=vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d74480`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d74480` 变为 `81d74480`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.25 `inj`（L0 注入）

- `event_id=24`，`tick=5364646522794`，`corr=origin`，`request_id=3159639`，`dyn_inst_seq=3159639`，`field=perm_subst`，`before=2`，`after=0`

### 3.26 `tlb_lookup`（L1 TLB 查询）

- `event_id=25`，`parent_event_id=24`，`tick=5364646522794`，`corr=seq_primary`，`request_id=3159639`，`dyn_inst_seq=3159639`，`walk_id=0`，`va=ffffffc008996b80`，`entry_index=6`，`way=1`，`field=post_lookup`，`before=2`，`after=0`，`state_before=vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=2;mtype=2;page_size=200000;pa=80996b80`，`state_after=vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=0;mtype=2;page_size=200000;pa=80996b80`
  该事件把 TLB 表项的状态/字段从 `vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=2;mtype=2;page_size=200000;pa=80996b80` 变为 `vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=0;mtype=2;page_size=200000;pa=80996b80`；这就是故障值进入翻译路径的位置。

### 3.27 `tlb_state`（L2 TLB 状态）

- `event_id=26`，`parent_event_id=25`，`tick=5364646522794`，`corr=seq_primary`，`request_id=3159639`，`dyn_inst_seq=3159639`，`va=ffffffc008996b80`，`field=perm_subst`，`state_before=2`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `2` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.28 `tlb_translate_result`（L2 翻译结果）

- `event_id=27`，`parent_event_id=26`，`tick=5364646522794`，`corr=seq_primary`，`request_id=3159639`，`dyn_inst_seq=3159639`，`walk_id=0`，`va=ffffffc008996b80`，`pa=80996b80`，`entry_index=6`，`way=1`，`field=effective_pa_unchanged`，`before=80996b80`，`after=80996b80`，`state_before=vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=2;mtype=2;page_size=200000;pa=80996b80`，`state_after=vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=0;mtype=2;page_size=200000;pa=80996b80`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80996b80` 变为 `80996b80`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.29 `chain_end`（生命周期结束）

- `event_id=28`，`parent_event_id=3`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.30 `chain_end`（生命周期结束）

- `event_id=29`，`parent_event_id=7`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.31 `chain_end`（生命周期结束）

- `event_id=30`，`parent_event_id=11`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.32 `chain_end`（生命周期结束）

- `event_id=31`，`parent_event_id=15`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.33 `chain_end`（生命周期结束）

- `event_id=32`，`parent_event_id=19`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.34 `chain_end`（生命周期结束）

- `event_id=33`，`parent_event_id=23`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.35 `chain_end`（生命周期结束）

- `event_id=34`，`parent_event_id=27`，`tick=5364661143825`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `394307` | `—` | `0` → `1` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `394307` | `ffffffc0094839a0` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `394307` | `ffffffc0094839a0` | `0` → `1` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `394307` | `81d759a0` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0` |
| 4 | `inj` | L0 | CHAOSArmTLB | `848321` | `—` | `0` → `2` |
| 5 | `tlb_lookup` | L1 | DTLB CAM | `848321` | `ffffffc008e05018` | `vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=0;mtype=1;page_size=1000;pa=1c090018` → `vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=2;mtype=1;page_size=1000;pa=1c090018` |
| 6 | `tlb_state` | L2 | DTLB 表项 | `848321` | `ffffffc008e05018` | `0` → `2` |
| 7 | `tlb_translate_result` | L2 | MMU 翻译 | `848321` | `1c090018` | `vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=0;mtype=1;page_size=1000;pa=1c090018` → `vpn=ffffffc008e05;asid=206;valid=1;global=1;pfn=1c090;ap=2;mtype=1;page_size=1000;pa=1c090018` |
| 8 | `inj` | L0 | CHAOSArmTLB | `1300814` | `—` | `0` → `2` |
| 9 | `tlb_lookup` | L1 | DTLB CAM | `1300814` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 10 | `tlb_state` | L2 | DTLB 表项 | `1300814` | `ffffffc008c730e0` | `0` → `2` |
| 11 | `tlb_translate_result` | L2 | MMU 翻译 | `1300814` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 12 | `inj` | L0 | CHAOSArmTLB | `1727206` | `—` | `2` → `0` |
| 13 | `tlb_lookup` | L1 | DTLB CAM | `1727206` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` |
| 14 | `tlb_state` | L2 | DTLB 表项 | `1727206` | `ffffffc008c730e0` | `2` → `0` |
| 15 | `tlb_translate_result` | L2 | MMU 翻译 | `1727206` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` |
| 16 | `inj` | L0 | CHAOSArmTLB | `2087770` | `—` | `0` → `2` |
| 17 | `tlb_lookup` | L1 | DTLB CAM | `2087770` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 18 | `tlb_state` | L2 | DTLB 表项 | `2087770` | `ffffffc008c730e0` | `0` → `2` |
| 19 | `tlb_translate_result` | L2 | MMU 翻译 | `2087770` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 20 | `inj` | L0 | CHAOSArmTLB | `2444151` | `—` | `0` → `2` |
| 21 | `tlb_lookup` | L1 | DTLB CAM | `2444151` | `ffffffc009482480` | `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74480` → `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d74480` |
| 22 | `tlb_state` | L2 | DTLB 表项 | `2444151` | `ffffffc009482480` | `0` → `2` |
| 23 | `tlb_translate_result` | L2 | MMU 翻译 | `2444151` | `81d74480` | `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74480` → `vpn=ffffffc009482;asid=206;valid=1;global=1;pfn=81d74;ap=2;mtype=2;page_size=1000;pa=81d74480` |
| 24 | `inj` | L0 | CHAOSArmTLB | `3159639` | `—` | `2` → `0` |
| 25 | `tlb_lookup` | L1 | DTLB CAM | `3159639` | `ffffffc008996b80` | `vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=2;mtype=2;page_size=200000;pa=80996b80` → `vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=0;mtype=2;page_size=200000;pa=80996b80` |
| 26 | `tlb_state` | L2 | DTLB 表项 | `3159639` | `ffffffc008996b80` | `2` → `0` |
| 27 | `tlb_translate_result` | L2 | MMU 翻译 | `3159639` | `80996b80` | `vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=2;mtype=2;page_size=200000;pa=80996b80` → `vpn=7fffffe0044;asid=206;valid=1;global=1;pfn=404;ap=0;mtype=2;page_size=200000;pa=80996b80` |
| 28 | `chain_end` | — | run | `—` | `—` | — |
| 29 | `chain_end` | — | run | `—` | `—` | — |
| 30 | `chain_end` | — | run | `—` | `—` | — |
| 31 | `chain_end` | — | run | `—` | `—` | — |
| 32 | `chain_end` | — | run | `—` | `—` | — |
| 33 | `chain_end` | — | run | `—` | `—` | — |
| 34 | `chain_end` | — | run | `—` | `—` | — |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
24(inj) → 25(tlb_lookup) → 26(tlb_state) → 27(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 24 | — | 5364646522794 | `origin` | `3159639` | 7 |
| 25 | 24 | 5364646522794 | `seq_primary` | `3159639` | 7 |
| 26 | 25 | 5364646522794 | `seq_primary` | `3159639` | 7 |
| 27 | 26 | 5364646522794 | `seq_primary` | `3159639` | 7 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=27），其字段 `outcome=NoFault`、`contained=1`、`detection_layer=L2`、`containment_reason=effective_pa_unchanged`。

**为何形成该结局**：`perm_subst` 用另一个合法权限编码替换 AP：`tlb_translate_result` 的 `outcome=NoFault` 表明本次访问的权限判定**没有**因替换而改变（同一 PA、同一允许级别），因此有效 PA 不变、结局为 L2 `effective_pa_unchanged` 含住（Masked）。替换后的 AP 是否会影响其它访问，本流无法归因（链在含住时闭合）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`770622`，eligible=`770622`，injected=`7`（日志应用行 7 条），activated=`7`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2/prop_evt.txt.gz` — SHA-256 `c13cb1ea198b75bbe540b56d6487795776aa779c662c4590a36ff489f47a34a8`（2266 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2/chain_report.json` — SHA-256 `3d6e6228bb96a29893b8f8965b97d827f89f16c9b9d4d09e857ead7e206b8644`（6567 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2/stats.txt` — SHA-256 `4eaf659ebef978f36fcfcf805ab244eb3c7f0ef6ebf3db4c914b439494f81ca9`（395628 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2/run.out` — SHA-256 `2349bcaf5062b8d2409b5a02a4bf298ccaa90a4930f64b6be4efa0db28817470`（3163 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2/run.err` — SHA-256 `73fab59a40fbd3120dcca876b25dc48cf14af5838c8ee429e8b30c6b59fccbb6`（2137 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/T06-F2-W4/seed2/armtlb_injections.log` — SHA-256 `7a65a067761615b33dc1ce3c94cdbdac3eebc175d60b97d4fb0322a1eef51d45`（1289 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2/manifest.json` — SHA-256 `8ecee40482e9e66bbbc71b1689f99d11d378dc320e6ac584ff2fc56ae2b2b3ea`（2103 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

