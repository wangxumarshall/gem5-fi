# T06-F2-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T06-F2-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T06`）
- fault type / 子模型：`perm_subst`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1 --cells T06-F2-W4 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`ad1a47115d778cce6283e8ffd4d0796787f546cc`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T05:03:56+08:00`，end=`2026-10-28T05:05:37+08:00`）
- 运行目录进程：gem5_pid=`3476832`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：40（chain_report.event_count=`40`）
- fault_id 数：8

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238085303040`，event_id=`0`
- 被改字段：`perm_subst`；before=`0`，after=`1`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: perm_subst (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: perm_subst (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 238085303040, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094839a0, old_perm_subst: 0, new_perm_subst: 1, FaultType: perm_subst
Tick: 238527104463, Site: arm_tlb_lookup_hit, VA: 0xffffffc008bff750, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 1160428529547, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 3130703461035, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst
Tick: 5077296986634, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 5945126135121, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst
Tick: 7269167785770, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c730e0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
Tick: 8244743170500, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094812c0, old_perm_subst: 0, new_perm_subst: 2, FaultType: perm_subst
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`31`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=238085303040`，`corr=origin`，`request_id=415932`，`dyn_inst_seq=415932`，`field=perm_subst`，`before=0`，`after=1`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=238085303040`，`corr=seq_primary`，`request_id=415932`，`dyn_inst_seq=415932`，`walk_id=0`，`va=ffffffc0094839a0`，`entry_index=21`，`way=5`，`field=post_lookup`，`before=0`，`after=1`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0` 变为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=238085303040`，`corr=seq_primary`，`request_id=415932`，`dyn_inst_seq=415932`，`va=ffffffc0094839a0`，`field=perm_subst`，`state_before=0`，`state_after=1`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `1`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=238085303040`，`corr=seq_primary`，`request_id=415932`，`dyn_inst_seq=415932`，`walk_id=0`，`va=ffffffc0094839a0`，`pa=81d759a0`，`entry_index=21`，`way=5`，`field=translation_blocked`，`before=81d759a0`，`after=81d759a0`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0`，`state_after=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d759a0` 变为 `81d759a0`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.5 `inj`（L0 注入）

- `event_id=4`，`tick=238527104463`，`corr=origin`，`request_id=708766`，`dyn_inst_seq=708766`，`field=perm_subst`，`before=0`，`after=2`

### 3.6 `tlb_lookup`（L1 TLB 查询）

- `event_id=5`，`parent_event_id=4`，`tick=238527104463`，`corr=seq_primary`，`request_id=708766`，`dyn_inst_seq=708766`，`walk_id=0`，`va=ffffffc008bff750`，`entry_index=31`，`way=6`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=0;mtype=2;page_size=1000;pa=80bff750`，`state_after=vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=2;mtype=2;page_size=1000;pa=80bff750`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=0;mtype=2;page_size=1000;pa=80bff750` 变为 `vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=2;mtype=2;page_size=1000;pa=80bff750`；这就是故障值进入翻译路径的位置。

### 3.7 `tlb_state`（L2 TLB 状态）

- `event_id=6`，`parent_event_id=5`，`tick=238527104463`，`corr=seq_primary`，`request_id=708766`，`dyn_inst_seq=708766`，`va=ffffffc008bff750`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.8 `tlb_translate_result`（L2 翻译结果）

- `event_id=7`，`parent_event_id=6`，`tick=238527104463`，`corr=seq_primary`，`request_id=708766`，`dyn_inst_seq=708766`，`walk_id=0`，`va=ffffffc008bff750`，`pa=80bff750`，`entry_index=31`，`way=6`，`field=translation_blocked`，`before=80bff750`，`after=80bff750`，`state_before=vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=0;mtype=2;page_size=1000;pa=80bff750`，`state_after=vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=2;mtype=2;page_size=1000;pa=80bff750`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `80bff750` 变为 `80bff750`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.9 `inj`（L0 注入）

- `event_id=8`，`tick=1160428529547`，`corr=origin`，`request_id=1024981`，`dyn_inst_seq=1024981`，`field=perm_subst`，`before=0`，`after=2`

### 3.10 `tlb_lookup`（L1 TLB 查询）

- `event_id=9`，`parent_event_id=8`，`tick=1160428529547`，`corr=seq_primary`，`request_id=1024981`，`dyn_inst_seq=1024981`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=3`，`way=6`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.11 `tlb_state`（L2 TLB 状态）

- `event_id=10`，`parent_event_id=9`，`tick=1160428529547`，`corr=seq_primary`，`request_id=1024981`，`dyn_inst_seq=1024981`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.12 `tlb_translate_result`（L2 翻译结果）

- `event_id=11`，`parent_event_id=10`，`tick=1160428529547`，`corr=seq_primary`，`request_id=1024981`，`dyn_inst_seq=1024981`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=3`，`way=6`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.13 `inj`（L0 注入）

- `event_id=12`，`tick=3130703461035`，`corr=origin`，`request_id=1606057`，`dyn_inst_seq=1606057`，`field=perm_subst`，`before=2`，`after=0`

### 3.14 `tlb_lookup`（L1 TLB 查询）

- `event_id=13`，`parent_event_id=12`，`tick=3130703461035`，`corr=seq_primary`，`request_id=1606057`，`dyn_inst_seq=1606057`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=3`，`way=0`，`field=post_lookup`，`before=2`，`after=0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.15 `tlb_state`（L2 TLB 状态）

- `event_id=14`，`parent_event_id=13`，`tick=3130703461035`，`corr=seq_primary`，`request_id=1606057`，`dyn_inst_seq=1606057`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=2`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `2` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.16 `tlb_translate_result`（L2 翻译结果）

- `event_id=15`，`parent_event_id=14`，`tick=3130703461035`，`corr=seq_primary`，`request_id=1606057`，`dyn_inst_seq=1606057`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=3`，`way=0`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.17 `inj`（L0 注入）

- `event_id=16`，`tick=5077296986634`，`corr=origin`，`request_id=2180137`，`dyn_inst_seq=2180137`，`field=perm_subst`，`before=0`，`after=2`

### 3.18 `tlb_lookup`（L1 TLB 查询）

- `event_id=17`，`parent_event_id=16`，`tick=5077296986634`，`corr=seq_primary`，`request_id=2180137`，`dyn_inst_seq=2180137`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=3`，`way=6`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.19 `tlb_state`（L2 TLB 状态）

- `event_id=18`，`parent_event_id=17`，`tick=5077296986634`，`corr=seq_primary`，`request_id=2180137`，`dyn_inst_seq=2180137`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.20 `tlb_translate_result`（L2 翻译结果）

- `event_id=19`，`parent_event_id=18`，`tick=5077296986634`，`corr=seq_primary`，`request_id=2180137`，`dyn_inst_seq=2180137`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=3`，`way=6`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.21 `inj`（L0 注入）

- `event_id=20`，`tick=5945126135121`，`corr=origin`，`request_id=2436069`，`dyn_inst_seq=2436069`，`field=perm_subst`，`before=2`，`after=0`

### 3.22 `tlb_lookup`（L1 TLB 查询）

- `event_id=21`，`parent_event_id=20`，`tick=5945126135121`，`corr=seq_primary`，`request_id=2436069`，`dyn_inst_seq=2436069`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=3`，`way=0`，`field=post_lookup`，`before=2`，`after=0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.23 `tlb_state`（L2 TLB 状态）

- `event_id=22`，`parent_event_id=21`，`tick=5945126135121`，`corr=seq_primary`，`request_id=2436069`，`dyn_inst_seq=2436069`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=2`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `2` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.24 `tlb_translate_result`（L2 翻译结果）

- `event_id=23`，`parent_event_id=22`，`tick=5945126135121`，`corr=seq_primary`，`request_id=2436069`，`dyn_inst_seq=2436069`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=3`，`way=0`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.25 `inj`（L0 注入）

- `event_id=24`，`tick=7269167785770`，`corr=origin`，`request_id=2826541`，`dyn_inst_seq=2826541`，`field=perm_subst`，`before=0`，`after=2`

### 3.26 `tlb_lookup`（L1 TLB 查询）

- `event_id=25`，`parent_event_id=24`，`tick=7269167785770`，`corr=seq_primary`，`request_id=2826541`，`dyn_inst_seq=2826541`，`walk_id=0`，`va=ffffffc008c730e0`，`entry_index=3`，`way=6`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` 变为 `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`；这就是故障值进入翻译路径的位置。

### 3.27 `tlb_state`（L2 TLB 状态）

- `event_id=26`，`parent_event_id=25`，`tick=7269167785770`，`corr=seq_primary`，`request_id=2826541`，`dyn_inst_seq=2826541`，`va=ffffffc008c730e0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.28 `tlb_translate_result`（L2 翻译结果）

- `event_id=27`，`parent_event_id=26`，`tick=7269167785770`，`corr=seq_primary`，`request_id=2826541`，`dyn_inst_seq=2826541`，`walk_id=0`，`va=ffffffc008c730e0`，`pa=80c730e0`，`entry_index=3`，`way=6`，`field=effective_pa_unchanged`，`before=80c730e0`，`after=80c730e0`，`state_before=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0`，`state_after=vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80c730e0` 变为 `80c730e0`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.29 `inj`（L0 注入）

- `event_id=28`，`tick=8244743170500`，`corr=origin`，`request_id=3114254`，`dyn_inst_seq=3114254`，`field=perm_subst`，`before=0`，`after=2`

### 3.30 `tlb_lookup`（L1 TLB 查询）

- `event_id=29`，`parent_event_id=28`，`tick=8244743170500`，`corr=seq_primary`，`request_id=3114254`，`dyn_inst_seq=3114254`，`walk_id=0`，`va=ffffffc0094812c0`，`entry_index=8`，`way=3`，`field=post_lookup`，`before=0`，`after=2`，`state_before=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d732c0`，`state_after=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d732c0`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d732c0` 变为 `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d732c0`；这就是故障值进入翻译路径的位置。

### 3.31 `tlb_state`（L2 TLB 状态）

- `event_id=30`，`parent_event_id=29`，`tick=8244743170500`，`corr=seq_primary`，`request_id=3114254`，`dyn_inst_seq=3114254`，`va=ffffffc0094812c0`，`field=perm_subst`，`state_before=0`，`state_after=2`
  该事件把 TLB 表项的状态/字段从 `0` 变为 `2`；这就是故障值进入翻译路径的位置。

### 3.32 `tlb_translate_result`（L2 翻译结果）

- `event_id=31`，`parent_event_id=30`，`tick=8244743170500`，`corr=seq_primary`，`request_id=3114254`，`dyn_inst_seq=3114254`，`walk_id=0`，`va=ffffffc0094812c0`，`pa=81d732c0`，`entry_index=8`，`way=3`，`field=translation_blocked`，`before=81d732c0`，`after=81d732c0`，`state_before=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d732c0`，`state_after=vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d732c0`，`detection_layer=L2`，`contained=1`，`outcome=Data`，`containment_reason=translation_blocked`
  翻译完成：PA 由 `81d732c0` 变为 `81d732c0`，outcome=`Data`，contained=`1`，detection_layer=`L2`，reason=`translation_blocked`。

### 3.33 `chain_end`（生命周期结束）

- `event_id=32`，`parent_event_id=3`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.34 `chain_end`（生命周期结束）

- `event_id=33`，`parent_event_id=7`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.35 `chain_end`（生命周期结束）

- `event_id=34`，`parent_event_id=11`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.36 `chain_end`（生命周期结束）

- `event_id=35`，`parent_event_id=15`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.37 `chain_end`（生命周期结束）

- `event_id=36`，`parent_event_id=19`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.38 `chain_end`（生命周期结束）

- `event_id=37`，`parent_event_id=23`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.39 `chain_end`（生命周期结束）

- `event_id=38`，`parent_event_id=27`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

### 3.40 `chain_end`（生命周期结束）

- `event_id=39`，`parent_event_id=31`，`tick=8244769213098`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=translation_blocked`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `415932` | `—` | `0` → `1` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `415932` | `ffffffc0094839a0` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `415932` | `ffffffc0094839a0` | `0` → `1` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `415932` | `81d759a0` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d759a0` → `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=1;mtype=2;page_size=1000;pa=81d759a0` |
| 4 | `inj` | L0 | CHAOSArmTLB | `708766` | `—` | `0` → `2` |
| 5 | `tlb_lookup` | L1 | DTLB CAM | `708766` | `ffffffc008bff750` | `vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=0;mtype=2;page_size=1000;pa=80bff750` → `vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=2;mtype=2;page_size=1000;pa=80bff750` |
| 6 | `tlb_state` | L2 | DTLB 表项 | `708766` | `ffffffc008bff750` | `0` → `2` |
| 7 | `tlb_translate_result` | L2 | MMU 翻译 | `708766` | `80bff750` | `vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=0;mtype=2;page_size=1000;pa=80bff750` → `vpn=ffffffc008bff;asid=206;valid=1;global=1;pfn=80bff;ap=2;mtype=2;page_size=1000;pa=80bff750` |
| 8 | `inj` | L0 | CHAOSArmTLB | `1024981` | `—` | `0` → `2` |
| 9 | `tlb_lookup` | L1 | DTLB CAM | `1024981` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 10 | `tlb_state` | L2 | DTLB 表项 | `1024981` | `ffffffc008c730e0` | `0` → `2` |
| 11 | `tlb_translate_result` | L2 | MMU 翻译 | `1024981` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 12 | `inj` | L0 | CHAOSArmTLB | `1606057` | `—` | `2` → `0` |
| 13 | `tlb_lookup` | L1 | DTLB CAM | `1606057` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` |
| 14 | `tlb_state` | L2 | DTLB 表项 | `1606057` | `ffffffc008c730e0` | `2` → `0` |
| 15 | `tlb_translate_result` | L2 | MMU 翻译 | `1606057` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` |
| 16 | `inj` | L0 | CHAOSArmTLB | `2180137` | `—` | `0` → `2` |
| 17 | `tlb_lookup` | L1 | DTLB CAM | `2180137` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 18 | `tlb_state` | L2 | DTLB 表项 | `2180137` | `ffffffc008c730e0` | `0` → `2` |
| 19 | `tlb_translate_result` | L2 | MMU 翻译 | `2180137` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 20 | `inj` | L0 | CHAOSArmTLB | `2436069` | `—` | `2` → `0` |
| 21 | `tlb_lookup` | L1 | DTLB CAM | `2436069` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` |
| 22 | `tlb_state` | L2 | DTLB 表项 | `2436069` | `ffffffc008c730e0` | `2` → `0` |
| 23 | `tlb_translate_result` | L2 | MMU 翻译 | `2436069` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` |
| 24 | `inj` | L0 | CHAOSArmTLB | `2826541` | `—` | `0` → `2` |
| 25 | `tlb_lookup` | L1 | DTLB CAM | `2826541` | `ffffffc008c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 26 | `tlb_state` | L2 | DTLB 表项 | `2826541` | `ffffffc008c730e0` | `0` → `2` |
| 27 | `tlb_translate_result` | L2 | MMU 翻译 | `2826541` | `80c730e0` | `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=0;mtype=2;page_size=1000;pa=80c730e0` → `vpn=ffffffc008c73;asid=206;valid=1;global=1;pfn=80c73;ap=2;mtype=2;page_size=1000;pa=80c730e0` |
| 28 | `inj` | L0 | CHAOSArmTLB | `3114254` | `—` | `0` → `2` |
| 29 | `tlb_lookup` | L1 | DTLB CAM | `3114254` | `ffffffc0094812c0` | `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d732c0` → `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d732c0` |
| 30 | `tlb_state` | L2 | DTLB 表项 | `3114254` | `ffffffc0094812c0` | `0` → `2` |
| 31 | `tlb_translate_result` | L2 | MMU 翻译 | `3114254` | `81d732c0` | `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=0;mtype=2;page_size=1000;pa=81d732c0` → `vpn=ffffffc009481;asid=206;valid=1;global=1;pfn=81d73;ap=2;mtype=2;page_size=1000;pa=81d732c0` |
| 32 | `chain_end` | — | run | `—` | `—` | — |
| 33 | `chain_end` | — | run | `—` | `—` | — |
| 34 | `chain_end` | — | run | `—` | `—` | — |
| 35 | `chain_end` | — | run | `—` | `—` | — |
| 36 | `chain_end` | — | run | `—` | `—` | — |
| 37 | `chain_end` | — | run | `—` | `—` | — |
| 38 | `chain_end` | — | run | `—` | `—` | — |
| 39 | `chain_end` | — | run | `—` | `—` | — |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
28(inj) → 29(tlb_lookup) → 30(tlb_state) → 31(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 28 | — | 8244743170500 | `origin` | `3114254` | 8 |
| 29 | 28 | 8244743170500 | `seq_primary` | `3114254` | 8 |
| 30 | 29 | 8244743170500 | `seq_primary` | `3114254` | 8 |
| 31 | 30 | 8244743170500 | `seq_primary` | `3114254` | 8 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Crash`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=31），其字段 `outcome=Data`、`contained=1`、`detection_layer=L2`、`containment_reason=translation_blocked`。

**为何形成该结局**：`perm_subst` 用另一个合法权限编码替换 AP：`tlb_translate_result` 的 `outcome=NoFault` 表明本次访问的权限判定**没有**因替换而改变（同一 PA、同一允许级别），因此有效 PA 不变、结局为 L2 `effective_pa_unchanged` 含住（Masked）。替换后的 AP 是否会影响其它访问，本流无法归因（链在含住时闭合）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`822010`，eligible=`822010`，injected=`8`（日志应用行 8 条），activated=`8`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1/prop_evt.txt.gz` — SHA-256 `b13b8a719c9813e68d9e8c658cab4f8d42f2adaba77ea9e9375656ec29f44272`（2375 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1/chain_report.json` — SHA-256 `924fd5049f87bd8b60b0ee65a8191bd1bf1cd99b1dc4b76669e2bd4ead875844`（7319 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1/stats.txt` — SHA-256 `67c0d0f5faa6c58c1e622e23554089f1ea37b34e097ead73b3a6822a8ff946a5`（394579 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1/run.out` — SHA-256 `38c9690bfbd2001171c6f52ec3605d7ac955d5ed99999716341b7c440bb4e688`（3261 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1/run.err` — SHA-256 `c947b037c1265cea6b21a0e6d79d30f4dd2e9242655830b13341b9250f3764af`（1957 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/T06-F2-W4/seed1/armtlb_injections.log` — SHA-256 `b05a9ab972f178b6a1152e9a107167a4ed0e5d12d9eb93f94a59de0503c49587`（1420 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1/manifest.json` — SHA-256 `ed697d0ed71c7d5bfbdfeda99bb436abb81eff8544c5c20f76e9d55042b35576`（2103 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

