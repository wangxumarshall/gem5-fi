# T05-F0-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T05-F0-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T05`）
- fault type / 子模型：`valid_clear`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F0`／生效 `F0`／tier enabled=`0`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1 --cells T05-F0-W4 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`（期望 `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`）
- binary source head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis tool head：`e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T00:20:34+08:00`，end=`2026-10-28T00:49:31+08:00`）
- 运行目录进程：gem5_pid=`3015881`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：5（chain_report.event_count=`5`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`237950940537`，event_id=`0`
- 被改字段：`valid_clear`；before=`1`，after=`0`
- 注入器原始日志行：

```
Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`3`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=237950940537`，`corr=origin`，`request_id=301`，`dyn_inst_seq=301`，`field=valid_clear`，`before=1`，`after=0`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=237950940537`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`walk_id=0`，`va=ffffffc009483fa8`，`entry_index=0`，`way=-1`，`field=post_lookup`，`before=1`，`after=0`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`，`state_after=vpn=ffffffc009483;asid=206;valid=0;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` 变为 `vpn=ffffffc009483;asid=206;valid=0;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2`，`parent_event_id=1`，`tick=237950940537`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`va=ffffffc009483fa8`，`field=valid_clear`，`state_before=1`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `1` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=3`，`parent_event_id=2`，`tick=237950940537`，`corr=seq_primary`，`request_id=301`，`dyn_inst_seq=301`，`walk_id=0`，`va=ffffffc009483fa8`，`pa=81d75fa8`，`entry_index=0`，`way=-1`，`field=effective_pa_unchanged`，`before=81d75fa8`，`after=81d75fa8`，`state_before=vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`，`state_after=vpn=ffffffc009483;asid=206;valid=0;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `81d75fa8` 变为 `81d75fa8`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

### 3.5 `chain_end`（生命周期结束）

- `event_id=4`，`parent_event_id=3`，`tick=314515193310`，`corr=none`，`detection_layer=L2`，`contained=1`，`outcome=detected_contained`，`containment_reason=effective_pa_unchanged`
  生命周期结束标记（outcome=`detected_contained`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `301` | `—` | `1` → `0` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `301` | `ffffffc009483fa8` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` → `vpn=ffffffc009483;asid=206;valid=0;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` |
| 2 | `tlb_state` | L2 | DTLB 表项 | `301` | `ffffffc009483fa8` | `1` → `0` |
| 3 | `tlb_translate_result` | L2 | MMU 翻译 | `301` | `81d75fa8` | `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` → `vpn=ffffffc009483;asid=206;valid=0;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8` |
| 4 | `chain_end` | — | run | `—` | `—` | — |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_state) → 3(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 237950940537 | `origin` | `301` | 1 |
| 1 | 0 | 237950940537 | `seq_primary` | `301` | 1 |
| 2 | 1 | 237950940537 | `seq_primary` | `301` | 1 |
| 3 | 2 | 237950940537 | `seq_primary` | `301` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Masked`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=3），其字段 `outcome=NoFault`、`contained=1`、`detection_layer=L2`、`containment_reason=effective_pa_unchanged`。

**为何形成该结局**：`valid_clear` 把被命中表项的 valid 位由 1 改为 0。该表项在本次查询**已经被匹配**（`tlb_lookup` 显示的是 post_lookup 状态），因此本次翻译仍用它原来的 pfn 完成；被清零的位只可能影响**之后**对同一 VPN 的查询（本流未观测到再次查询；因有效 PA 未变，本型号**不开**关联臂，`corr=seq_primary` 只是标签，链如实止于 L2）。因此本次翻译的有效 PA 不变、无下游 L3+ 事件，结局是 L2 `effective_pa_unchanged` 含住（Masked）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`66310643`，eligible=`56`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1/prop_evt.txt.gz` — SHA-256 `6269998ba394adbed2da4dc844acd6c7c90344d23e46d8d16c3397e7c2ced616`（904 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1/chain_report.json` — SHA-256 `220fff9a4ffb454b78f7fb32fa78bdade9e34532065bb7e08ad76e6ecf905851`（1801 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1/stats.txt` — SHA-256 `a5dc614d33d8386140b8361ac5ddafd4d4f7477a1d24a4448b578ba623de3abb`（427682 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1/run.out` — SHA-256 `85aff325ad61948c8680ffd8627b6e38fc0c7d5a60564c13819819ef6a0ae655`（2146 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1/run.err` — SHA-256 `ffd049540979eba3bb6154fb2233bc6a38ac18458f6ee7fb0e94d3bd210cbd86`（1872 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/T05-F0-W4/seed1/armtlb_injections.log` — SHA-256 `595a4efa7295ea3b2a2a2c6f685cca501b9e9367ce1570285fcd8d21c0f49aa6`（133 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1/manifest.json` — SHA-256 `0a82070ae51658312e6e5b470ad526c14e68130dd0377bb8a3e9a57440032645`（2102 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`b13a60abbdd3…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

