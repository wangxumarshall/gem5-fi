# T10-F2-W1 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F2-W1`；seed：`3`；sample_run_id：`s3`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T10-F2-W1 --prop_sample_run_id s3`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/manifest.json`（SHA-256 `58db0c380218d55c7d9bb69a388ff398f23e51028a16cf7b75ba1fd5d3782ba6`；1438 bytes；mtime `2026-10-27T16:17:31+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；394487 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **14380** 条；`chain_report.event_count`=**12752**（不含 consumer 事件），差值为 consumer 摘要数 1628
- fault_id 数量：**3**（注入日志共 4 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F2-W1 seed3 自己的流。代表故障 fault_id=1，终局 event 97（`errant_commit`）；祖先为 0,1,2,3,4,11,12,13,14,15,16,17,60,61,62,69,70,71,80,81,82,97（22 个事件）。`path_event_ids=[0,1,2,4,81,97]` 只是层锚点。tick 单调不减；0–4、11–14、15–17、60–62、69–71、80–82 分别同 tick。

### 2.1 故障注入前的正常状态

**store**：event 4 `sq_execute`（sq_idx=54806，state_before=issued），dyn/request=`520906`，VA=`0xffffffc009483950`。命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75950`；way=-1（未记录）、entry_index=21，偏移 0x950。正常 PFN=0x81d75、正常 PA=0x81d75950。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`238095582084`，`field=bit_flip`，`before=81d75`、`after=85d75`，VA=`0xffffffc009483950`，`request_id=520906`，`corr=origin`。注入日志：`old_pfn 0x81d75 → new_pfn 0x85d75, Mask: 0x4000`。0x81d75 XOR 0x4000 = 0x85d75，即 bit 14 从 0 变 1；偏移 0x950 不变，PA 81d75950→85d75950，effective 变化为真。VPN/ASID/权限/页大小未变；bit_flip 单 bit 翻转。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 81d75→85d75（entry_index=21，way=-1）；event 2 `tlb_pfn` 记录 `state_before=81d75950`、`state_after=85d75950`、`pa=85d75950`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=81d75950`、`after=85d75950`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit14 翻转后的 PPN 仍是合法编码，权限/有效位/页大小未变。TLB 交付 request_id=520906、PA=0x85d75950 的 store。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `sq_execute`（sq_idx=54806）把错误 store 置为 issued；event 11 `sq_writeback`（parent=4，tick=`238095585414`）以 `pa=85d75950` 构造 packet，state_after=packet_built；event 12 `cache_access` 随即使用该 PA。store 阶段 request_id 为空，cache 阶段重新带 request_id=520906。

### 2.5 错误如何经过 cache 和 MSHR

event 12 `cache_access`（pa=85d75950）→event 13 `cache_return field=miss`→event 14 `mshr_alloc`（mshr_id=3，line 85d75950）；event 15 访问 `pa=85d75940`→event 16 miss→event 17 `mshr_alloc`（mshr_id=4，line 85d75940）。event 60 `mshr_fill`（fill_id=3）→61 `cache_fill`→62 `mshr_free`；event 69 `mshr_fill`（mshr 0/fill 4）→70 `cache_fill`→71 `mshr_free`。错误行同属 0x85d75 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 80 `resp`（parent=71，tick=`238095646353`）交付 request_id=520906 的响应；event 81 `taint_reg`（parent=80）clean→tainted，VA=`85d75950`；原始事件没有 arch_reg/phys_reg，因此不编造。event 82 `sq_complete`（parent=81，sq_idx=54806）把 store 标为 completed。`taint_reg` 是存储→CPU 边界，event 97 直接以 event 82 的链条提交。

### 2.7 最终传播终局

终局：event 97，`errant_commit`，`parent_event_id=82`，tick=`238095648018`，`dyn_inst_seq=520923`，`commit_seq=394130`，`pc=ffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 10930（tick=`1971893110356`，errant_commit_seen）；本 seed 有 56 条 L4 `squash_masked`，都在 97 的祖先之外（最早 event 1661，tick=238098402927，晚于 L5）。

为什么没有被提前消除：event 97 的祖先上没有 squash；为什么架构可见：`errant_commit` 越过提交边界。dyn 不一致（store 520906，终局 520923）用 parent=82/corr=taint_prop 的建模约定解释；消费者 fork 在第 5 章，不在 97 祖先上。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 97，tick=`238095648018`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=238095648018 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`238095582084`，终局 tick=`238095648018`，延迟 **65934 ticks**。
- 因果链：L5 → guest kernel oops → Crash。56 条 L4 squash 与 fault2/3 不能改写 event 97；没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483950，entry=21，PFN=81d75 | bit14 翻转→85d75 | request_id=520906，PA=85d75950 | 错误 PPN 进入地址 |
| SQ | store sq_idx=54806 | sq_execute→sq_writeback→sq_complete | 错误 store packet | 错误地址被 SQ 接受 |
| L1D cache | PA=85d75950 / line 85d75940 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 85d75950/85d75940 | alloc(3/4)→fill(3/4)→free | 响应 | 错误行完成生命周期 |
| response | request_id=520906 | resp 交付 | 可交付污染值 | 回到处理器 |
| register file（taint） | store 数据 | clean→tainted（arch/phys 未记录） | 被标记状态 | 存储→CPU 边界 |
| commit/ROB | dyn 520923 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F2-W1 seed3 在 tick 238095582084 把 VA=ffffffc009483950 的 PPN bit14 翻转（0x81d75→0x85d75，mask 0x4000），错误 PA=85d75950 经 SQ（4/11）→L1D/MSHR（12–71）→resp/taint_reg/sq_complete（80–82）传播，event 97 真实错误提交；运行结局 Crash，56 条 L4 squash 与 fault2/3 是旁支。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 3 条 hit；`CHAOS_LSU_TRIGGER` 为 `attempted=416527 eligible=416527 injected=3`；`stats.txt` numFaultsInjected=3；`chain_report` faults=3。四方一致。fault1 的 PPN 被 event 1/2/3 读取、event 4/11 消费，activated 为真；fault2 到 L4 contained，fault3 到 L4-then-unknown。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x4000 翻转 bit14，错误 PA=85d75950 经 SQ/cache/MSHR；不是 data/permission/control-state/timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=238095582084）**：错误 PA 交付 LSU；之后只有 squash/replay 可撤销，而 97 的祖先上没有。event 81 的 taint_reg 是寄存器层点；event 97 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；L1D/MSHR 无地址正确性检查；本 seed 有 56 条 L4 squash（例如 event 1661、1685、1702、1761，均在 event 97 之后/其它请求上）；fault2 的 chain_end 10931 为 L4 detected_contained，fault3 的 10932 为 L4。RAS 对后续请求有效，但没有覆盖 event 97。检测盲区：PPN bit14 翻转仍合法。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 97）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。56 条 L4 与 fault2/3 不能改写 event 97。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed3 注入 tick=238095582084、VA=ffffffc009483950、mask=0x4000、PFN 81d75→85d75、终局 97、Crash、3 个 fault；seed1 是 238085259417/VA=ffffff8001362708/mask 0x4000/终局 26；seed2 是 238083182163/VA=ffffffc009483960/mask 0x1/终局 68（含住）。三者地址/终局类型不同；本文件只用 seed3 的字段。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）的终局见证 `parent_event_id` 单祖先重建。seed2 的终局见证采用权威口径 event 68（真实 L4 含住），不是报告 `path_event_ids` 尾部的 1797；`path_event_ids` 只作层锚点。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238095582084 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | 0x4000 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→85d75 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 238095582084 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75950 | — | — | — | — | VA=ffffffc009483950 的命中查找，request_id=520906 | 命中表项返回 pfn=85d75 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 238095582084 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 85d75950 | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | 81d75950 | 85d75950 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=85d75950（pfn=85d75） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 238095582084 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 85d75950 | — | — | — | — | 81d75950 | 85d75950 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75950 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=85d75950，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 238095582084 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | dyn_inst_seq=520906 的请求，VA=ffffffc009483950 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 11 | 4 | 238095585414 | 3330 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 520906 | — | 85d75950 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | dyn_inst_seq=520906 的请求 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 12 | 11 | 238095585414 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 85d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75950 的访问，request_id=520906 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 13 | 12 | 238095585414 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 520906 | 520906 | — | 85d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75950 的访问，request_id=520906 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 14 | 13 | 238095585414 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75950 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=85d75950，mshr_id=3 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 15 | 14 | 238095585747 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75940 的访问，request_id=520906 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 16 | 15 | 238095585747 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 520906 | 520906 | — | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75940 的访问，request_id=520906 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 17 | 16 | 238095585747 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 4 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=85d75940，mshr_id=4 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 60 | 17 | 238095645021 | 59274 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 4 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=85d75940，mshr_id=4 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 61 | 60 | 238095645021 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 520906 | 520906 | — | 85d75940 | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=85d75940 | pa=85d75940 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 62 | 61 | 238095645021 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 4 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=85d75940，mshr_id=4 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 69 | 62 | 238095646020 | 999 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=85d75940，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 70 | 69 | 238095646020 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 520906 | 520906 | — | 85d75940 | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=85d75940 | pa=85d75940 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 71 | 70 | 238095646020 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=85d75940，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 80 | 71 | 238095646353 | 333 | resp | L3 | response path | 1 | seq_primary | 520906 | 520906 | 85d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=520906 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 81 | 80 | 238095646353 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 520906 | 520906 | 85d75950 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 82 | 81 | 238095646353 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | sq_idx=54806 的 store 完成 | store 完成状态 | 错误 store 效果被标记为完成，等待提交 |
| 22 | 97 | 82 | 238095648018 | 1665 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 520923 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 14380 条原始事件（report 12752 非 consumer；consumer 1628）；主链只取 event 97 的 22 个单祖先。旁支事实：

- `request_fork` 1508 条，主链 0 条；从主链节点 3（1 条）与 17（11 条）、81（1496 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=85d75000`、`shared_size=1000`；new_request_id 如 520896/520907/520912/…。它们不进入 97 的祖先。
- 旁支 `taint_reg` 1661 条，主链 1 条（81）；`resp` 1413 条，主链 1 条（80）；`lq_complete` 490 条，主链 0 条（store 路径，主链用 sq_complete 82）；`squash_masked` 56 条，主链 0 条。
- 56 条 L4 squash 均在 event 97 之后/其它 VA，例如 event 1661（VA=ffffffc009483740，tick=238098402927）、1685（…3458）、1702（…3430）、1761（…33c0）；不能把 event 97 说成含住。
- `chain_end`：fault1 10930（tick=1971893110356，L5 errant_commit_seen）；fault2 10931（L4 detected_contained）；fault3 10932（L4 store_discarded_not_retired）。
- **其它 fault**：fault2 event 8348（VA=ffffffc009483240，PFN 85d75→95d75，mask 0x10000，lq_read，taint 8376，contained 9237）；fault3 event 10880（VA=ffffffc008c730e0，PFN 80c73→80c53，mask 0x20，lq_read，taint 10899）。它们不并入 fault1。
- consumer 1628 条摘要不在主链。
- 影响：旁支与 56 次 L4 响应说明错误页持续被访问；但 event 97 未被覆盖，终局 full/L5。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 97（errant_commit，tick=238095648018）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=1628，suppressed=14627，logical_total=16255，issues=[]）。
- count_contradiction：14380−12752=1628（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL OOPS 一致；checker full/L5 与报告一致；fault2/3 不改变 fault1。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- chain_evidence_status：**PASS**
- experiment_identity_status：**WORKLOAD_IDENTITY_MISMATCH**
- overall_experiment_status：**NOT_MIBENCH_RESULT**
- verdict：**NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果）

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/prop_evt.txt.gz` | SHA-256 `97e0b0a092a6464904b89f51c701e7e698f3008e53abc6cbede65fd47c8738ab`；476528 bytes；mtime `2026-10-27T16:17:27+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/prop_trace.csv.gz` | SHA-256 `00cadd63123516f0a04f9326cd6946e6397fc1aa447cd4e1d91c0ec16a9138cf`；143967 bytes；mtime `2026-10-27T16:17:27+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/chain_report.json` | SHA-256 `4aaa8c4d46e290cb589079268f8a9ebb45fb7096e56d40c05727a0b741dc8f21`；1375321 bytes；mtime `2026-10-27T16:17:30+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/run.out` | SHA-256 `b324dd7990e7daa87d35485a316b8231ef874ed747b81cb618f1bfee8389d600`；8564 bytes；mtime `2026-10-27T16:17:28+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/run.err` | SHA-256 `de8403ca5671675b258d5cc2e9d99a733336eef03c49490bb0d383150eb6e549`；1800 bytes；mtime `2026-10-27T16:17:28+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/stats.txt` | SHA-256 `e8e5f423524ad10474f9c3ec4571ea734bdb1f8ffcbb91f0532d3e022b97c47e`；394487 bytes；mtime `2026-10-27T16:17:28+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/manifest.json` | SHA-256 `58db0c380218d55c7d9bb69a388ff398f23e51028a16cf7b75ba1fd5d3782ba6`；1438 bytes；mtime `2026-10-27T16:17:31+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3 --cells T10-F2-W1 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/armtlb_injections.log` | SHA-256 `9b2befa5916174de9465dba72b0db2219110e5e17ba633f45e77e10f893d04a1`；782 bytes；mtime `2026-10-27T16:17:26+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/board.workload.dmesg` | SHA-256 `a5e96cb52b66e2124641c5bff31a2ceced6749066cd54d7d80ec619d276cb78a`；14888 bytes；mtime `2026-10-27T16:17:27+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/board.terminal` | SHA-256 `7d1a3aacc81ff77749593781e23448842564682be3ae2ab138d6dc2b25433103`；1063 bytes；mtime `2026-10-27T16:17:07+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/config.ini` | SHA-256 `13d0d91f130e56c36c7d185ddb13280828e9b431a9a4d9f47dcc3166e62dcc65`；97178 bytes；mtime `2026-10-27T16:16:51+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3/config.json` | SHA-256 `f16c0415193cf8ba678bdd0c067636881767aa54e4fc87c005a246a56031846c`；277159 bytes；mtime `2026-10-27T16:16:51+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3/T10-F2-W1/seed3`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `R6-AUTHORITATIVE-EVIDENCE.md` 未列出本 seed 的其它副本；权威目录唯一。

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
