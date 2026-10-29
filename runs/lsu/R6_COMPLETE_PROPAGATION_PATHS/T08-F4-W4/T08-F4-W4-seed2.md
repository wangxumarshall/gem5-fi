# T08-F4-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T08-F4-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T08`）
- fault type / 子模型：`walk_pairing`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F4`／生效 `F4`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2 --cells T08-F4-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`ed8a08ca5bf61f4e8f0895c95e591015da8fe92f`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T07:34:47+08:00`，end=`2026-10-28T08:03:04+08:00`）
- 运行目录进程：gem5_pid=`3586908`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：6（chain_report.event_count=`6`）
- fault_id 数：1

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`（站点取自注入日志）；tick=`296673509853`，event_id=`0`，fault_id=`1`，dyn_inst_seq=`277013784`，request_id=`277013784`，VA=`0x18`
- 被改字段：`walk_pairing`；before=`walk_issued`，after=`walk_pairing`
- 注入器原始日志行：

```
Tick: 237949797348, Site: arm_tlb_walk_issue_probe, walk_id: 1, VA: 0x40b4c0, FaultType: walk_pairing (walk-issue hook REACHED: TableWalker::walk -> maybeDropWalkFill)
Tick: 237950233578, Site: arm_tlb_lookup_hit_skipped, VA: 0xffffffc009483eb0, FaultType: walk_pairing (T08 walk-issue-only: NOT consumed at lookup-hit; see maybeDropWalkFill)
Tick: 296673509853, Site: arm_tlb_walk_issue_drop, walk_id: 172622, VA: 0x18, FaultType: walk_pairing (T08-a lost walk/fill)
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`4`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 5 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

### 3.1 `inj`（L0 注入）

- `event_id=0`，`tick=296673509853`，`corr=origin`，`request_id=277013784`，`dyn_inst_seq=277013784`，`walk_id=172622`，`va=18`，`field=walk_pairing`，`before=walk_issued`，`after=walk_pairing`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=1`，`parent_event_id=0`，`tick=296673509853`，`corr=origin`，`request_id=277013784`，`dyn_inst_seq=277013784`，`walk_id=172622`，`va=18`，`entry_index=-1`，`way=-1`，`field=post_lookup`，`state_before=entry=miss`，`state_after=entry=miss`，`outcome=miss`
  该事件把 TLB 表项的状态/字段从 `entry=miss` 变为 `entry=miss`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_walk`（L1/L2 page-walk 发起）

- `event_id=2`，`parent_event_id=1`，`tick=296673509853`，`corr=origin`，`request_id=277013784`，`dyn_inst_seq=277013784`，`walk_id=172622`，`va=18`，`field=walk_pairing`
  该事件属于 page-walk 配对链；`walk_id` 与 `tlb_walk`/`tlb_refill` 的绑定关系是本层的证据。

### 3.4 `tlb_refill`（L2 page-walk 回填）

- `event_id=3`，`parent_event_id=2`，`tick=296673509853`，`corr=origin`，`walk_id=172622`，`va=18`，`field=lost`，`outcome=lost`
  该事件属于 page-walk 配对链；`walk_id` 与 `tlb_walk`/`tlb_refill` 的绑定关系是本层的证据。

### 3.5 `tlb_translate_result`（L2 翻译结果）

- `event_id=4`，`parent_event_id=3`，`tick=296673509853`，`corr=origin`，`request_id=277013784`，`dyn_inst_seq=277013784`，`walk_id=172622`，`va=18`，`entry_index=-1`，`way=-1`，`field=walk_refill_lost`，`state_before=entry=miss`，`state_after=entry=miss`，`detection_layer=L2`，`contained=1`，`outcome=translation_blocked`
  翻译完成：PA 由 `` 变为 ``，outcome=`translation_blocked`，contained=`1`。

### 3.6 `chain_end`（生命周期结束）

- `event_id=5`，`parent_event_id=4`，`tick=314515193310`，`corr=none`，`contained=0`，`outcome=run_end`
  生命周期结束标记（outcome=`run_end`）。`chain_end` 本身**不是** L5 证据，只表示运行收尾；终局判定要看本章之前是否有真实 L5 见证。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 0 | `inj` | L0 | CHAOSArmTLB | `277013784` | `18` | `walk_issued` → `walk_pairing` |
| 1 | `tlb_lookup` | L1 | DTLB CAM | `277013784` | `18` | `entry=miss` → `entry=miss` |
| 2 | `tlb_walk` | L1 | TableWalker | `277013784` | `18` | — |
| 3 | `tlb_refill` | L2 | TableWalker 回填 | `—` | `18` | — |
| 4 | `tlb_translate_result` | L2 | MMU 翻译 | `277013784` | `18` | `entry=miss` → `entry=miss` |
| 5 | `chain_end` | — | run | `—` | `—` | — |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
0(inj) → 1(tlb_lookup) → 2(tlb_walk) → 3(tlb_refill) → 4(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 0 | — | 296673509853 | `origin` | `277013784` | 1 |
| 1 | 0 | 296673509853 | `origin` | `277013784` | 1 |
| 2 | 1 | 296673509853 | `origin` | `277013784` | 1 |
| 3 | 2 | 296673509853 | `origin` | `—` | 1 |
| 4 | 3 | 296673509853 | `origin` | `277013784` | 1 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Masked`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=4），其字段 `outcome=translation_blocked`、`contained=1`、`detection_layer=L2`、`containment_reason=`。

**为何形成该结局**：结局由第 3/4/5 章的真实事件链与本型号的注入语义共同决定；未在本表登记的解释不臆测。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`126005`，eligible=`99417`，injected=`1`（日志应用行 1 条），activated=`1`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2/prop_evt.txt.gz` — SHA-256 `1f5b4d827d166530773e7ca9c107c59dece6eafdefb37c844b17b3bb3381d06c`（831 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2/chain_report.json` — SHA-256 `b974dfdbd383acb89a2bc79d735a116a1bff03e75fd0974a4350a4b0d4782436`（2063 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2/stats.txt` — SHA-256 `ea1a8cebe0aa9854a61e378db4251b29a1cc231242f2f5aef6196b08807369ad`（427682 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2/run.out` — SHA-256 `004d7a3f873cf0f187909368c7e27f75023ca649a0d695e80c596b9218176b96`（2438 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2/run.err` — SHA-256 `9778c183ac4a46175f380d0690f09e38e909d8af4e95499eb36af596a471b2f0`（1872 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/T08-F4-W4/seed2/armtlb_injections.log` — SHA-256 `a6e34ce3e4288160f608694ce0c7a64bea5f6e91f7360fb80300c55a17078b1b`（468 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2/manifest.json` — SHA-256 `cd375cce89e449c65ae5086d4b17539fc94b32780fd17a5d40139b234a5eb642`（2103 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

