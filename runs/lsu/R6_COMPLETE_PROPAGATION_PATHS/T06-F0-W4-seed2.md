# T06-F0-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T06-F0-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T06`）
- fault type / 子模型：`perm_subst`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F0`／生效 `F0`／tier enabled=`0`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2 --cells T06-F0-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`f11eb1c4b00ccf6fb14a4b2714905b8ee71f0c73`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T04:07:47+08:00`，end=`2026-10-28T04:36:27+08:00`）
- 运行目录进程：gem5_pid=`3457730`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：5（chain_report.event_count=`5`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`237951188955`，event_id=`0`
- 被改字段：`perm_subst`；before=`2`，after=`0`
- 注入器原始日志行：

```
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: perm_subst (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 237951188955, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a16868, old_perm_subst: 2, new_perm_subst: 0, FaultType: perm_subst
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`3`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=237951188955`，`corr=origin`，`request_id=373`，`dyn_inst_seq=373`，`field=perm_subst`，`before=2`，`after=0`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=237951188955`，`corr=seq_primary`，`request_id=373`，`dyn_inst_seq=373`，`walk_id=0`，`va=ffffffc008a16868`，`entry_index=4`，`way=0`，`field=post_lookup`，`before=2`，`after=0`，`state_before=vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868`，`state_after=vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=0;mtype=2;page_size=1000;pa=80a16868`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868` 变为 `vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=0;mtype=2;page_size=1000;pa=80a16868`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=237951188955`，`corr=seq_primary`，`request_id=373`，`dyn_inst_seq=373`，`va=ffffffc008a16868`，`field=perm_subst`，`state_before=2`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `2` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=237951188955`，`corr=seq_primary`，`request_id=373`，`dyn_inst_seq=373`，`walk_id=0`，`va=ffffffc008a16868`，`pa=80a16868`，`entry_index=4`，`way=0`，`field=effective_pa_unchanged`，`before=80a16868`，`after=80a16868`，`state_before=vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868`，`state_after=vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=0;mtype=2;page_size=1000;pa=80a16868`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `80a16868` 变为 `80a16868`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.5 `chain_end`（生命周期结束）

- `event_id=4`，`parent_event_id=3`，`tick=314515193310`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `373` | `—` | `2` → `0` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `373` | `ffffffc008a16868` | `vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868` → `vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=0;mtype=2;page_size=1000;pa=80a16868` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `373` | `ffffffc008a16868` | `2` → `0` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `373` | `80a16868` | `vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868` → `vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=0;mtype=2;page_size=1000;pa=80a16868` |
| 4 | `chain_end` | — | run | `—` | `—` | — |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_state) → 3(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 237951188955 | `origin` | `373` | 1 |
| 1 | 0 | 237951188955 | `seq_primary` | `373` | 1 |
| 2 | 1 | 237951188955 | `seq_primary` | `373` | 1 |
| 3 | 2 | 237951188955 | `seq_primary` | `373` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Masked`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=3），其字段 `outcome=NoFault`、`contained=1`、`detection_layer=L2`、`containment_reason=effective_pa_unchanged`。

**为何形成该结局**：`perm_subst` 用另一个合法权限编码替换 AP：`tlb_translate_result` 的 `outcome=NoFault` 表明本次访问的权限判定**没有**因替换而改变（同一 PA、同一允许级别），因此有效 PA 不变、结局为 L2 `effective_pa_unchanged` 含住（Masked）。替换后的 AP 是否会影响其它访问，本流无法归因（链在含住时闭合）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`66272314`，eligible=`49`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2/prop_evt.txt.gz` — SHA-256 `276297b2b3f6de3ede4f3e82cfdc8d63dd3e8fc115b518efa740904fd0233738`（899 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2/chain_report.json` — SHA-256 `c18041141aac6c5e9dee2a3cdc2ebf3e3926da11d3e34d5fc8eb6fc54ab6e506`（1801 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2/stats.txt` — SHA-256 `7a777ef18a68cf0591feac5421f3eeddf49d0af167c694948a8349f7cc979a31`（427682 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2/run.out` — SHA-256 `f49b1df1bbc2a38feccb010562c02fb933f963bddb82f28729a309b3dab856e3`（2145 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2/run.err` — SHA-256 `ffd049540979eba3bb6154fb2233bc6a38ac18458f6ee7fb0e94d3bd210cbd86`（1872 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/T06-F0-W4/seed2/armtlb_injections.log` — SHA-256 `6dc34bfba019664915744ffcdfbde9b9c90f99968707eb6d598d8c4a426b5ff9`（305 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2/manifest.json` — SHA-256 `88aa86aa2a8575fbebdcee83223c1d0220c442d8190314c2f59b9ce5fdf9c8e9`（2102 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

