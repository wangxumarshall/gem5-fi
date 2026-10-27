# T10-F1-W1 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F1-W1`；seed：`3`；sample_run_id：`s3`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F1` — 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T10-F1-W1 --prop_sample_run_id s3`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/manifest.json`（SHA-256 `fbdb8f8ecafc25313a304ab1c7f0b69f0c6301d76a0df6d9abf1adb1be965c10`；1438 bytes；mtime `2026-10-27T16:16:20+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；419893 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **27950** 条；`chain_report.event_count`=**25388**（不含 consumer 事件），差值为 consumer 摘要数 2562
- fault_id 数量：**3**（注入日志共 4 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F1-W1 seed3 自己的流。代表故障 fault_id=1，终局 event 45（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,9,10,35,36,37,38,39,40,41,42,43,44,45（22 个事件）。`path_event_ids=[0,1,2,4,43,45]` 只是层锚点。tick 单调不减；0–7、8–10、35–37、38–40、41–44 分别同 tick。

### 2.1 故障注入前的正常状态

**load**：event 4 `lq_read`（lq_idx=594678），dyn/request=`5536042`，VA=`0x7fe7c61d40`（用户空间）。命中项 `vpn=7fe7c61`、`asid=214`、`valid=1`、`global=0`、`pfn=83111`、`ap=1`、`mtype=2`、`page_size=1000`、`pa=83111d40`；way=-1（未记录）、entry_index=23，偏移 0xd40。正常 PFN=0x83111、正常 PA=0x83111d40；global=0、ap=1。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`239629862268`，`field=bit_flip`，`before=83111`、`after=87111`，VA=`0x7fe7c61d40`，`request_id=5536042`，`corr=origin`。注入日志：`old_pfn 0x83111 → new_pfn 0x87111, Mask: 0x4000`。0x83111 XOR 0x4000 = 0x87111，即 bit 14 从 0 变 1；偏移 0xd40 不变，PA 83111d40→87111d40，effective 变化为真。VPN/ASID/权限/页大小未变；bit_flip 单 bit 翻转。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 83111→87111（entry_index=23，way=-1）；event 2 `tlb_pfn` 记录 `state_before=83111d40`、`state_after=87111d40`、`pa=87111d40`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=83111d40`、`after=87111d40`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit14 翻转后的 PPN 仍是合法编码，global=0/ap=1 未变。TLB 交付 request_id=5536042、PA=0x87111d40 的 load。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `lq_read`（lq_idx=594678）读取错误 PA；本 seed 没有 lsq_push/sq_* 事件，记录的是 LQ 读取阶段。输入是 TLB 的 PA=87111d40；输出是 request_id=5536042 的 cache 访问。

### 2.5 错误如何经过 cache 和 MSHR

event 5 `cache_access`（pa=87111d40）→event 6 `cache_return field=miss`→event 7 `mshr_alloc`（mshr_id=1，line 87111d40）；event 8 访问同页 `pa=87111d40`（同 line）→event 9 miss→event 10 `mshr_alloc`（mshr_id=2，line 87111d40）。event 35 `mshr_fill`（fill_id=1）→36 `cache_fill`→37 `mshr_free`；event 38 `mshr_fill`（mshr 0/fill 2）→39 `cache_fill`→40 `mshr_free`。错误行属于被翻转 PPN 的 0x87111 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 41 `resp`（parent=40，tick=`239629922541`）与 event 42 `lq_complete`（parent=41，lq_idx=594678）构成本 seed 的返回阶段；随后连续两个 `taint_reg`：event 43（parent=42）写 `arch_reg=4`、`phys_reg=68`，event 44（parent=43）写 `arch_reg=5`、`phys_reg=153`，均为 clean→tainted。**需要注意**：原始事件把 resp 的 `va` 记为 0、lq_complete 的 `va=7fe7c61d32`、`pa=0`、taint_reg 的 `va=0`；这些是原始流的字段值，本文件不把它们改写成 0x87111d40。可确认的是寄存器身份 x4/phys68 与 x5/phys153，以及 `taint_reg` 是存储→CPU 边界；event 45 以 event 44 为 parent 提交。

### 2.7 最终传播终局

终局：event 45，`errant_commit`，`parent_event_id=44`，tick=`239629923207`，`dyn_inst_seq=5536042`（与 load 相同），`commit_seq=3687869`，`pc=7f82a0afd8`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 21443（tick=`243383282757`，errant_commit_seen）；本 seed 有 3 条 L4 `squash_masked`（event 86、87、101），都在 event 45 的祖先之外。

为什么没有被提前消除：event 45 的祖先上没有 squash；event 86/87/101 是后续 load 的 replay。为什么架构可见：`errant_commit` 越过提交边界。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 45，tick=`239629923207`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=239629923207 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`239629862268`，终局 tick=`239629923207`，延迟 **60939 ticks**。
- 因果链：L5 → guest kernel oops → Crash。event 86/87/101 与 fault2/3（L4）不能改写 event 45；没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=7fe7c61d40，entry=23，PFN=83111，ASID=214，global=0 | bit14 翻转→87111 | request_id=5536042，PA=87111d40 | 错误 PPN 进入地址 |
| LQ | load lq_idx=594678 | lq_read 接受错误 PA | cache 请求 | 错误地址被 LQ 接受 |
| L1D cache | PA=87111d40 / line 87111d40 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 87111d40 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response / LQ complete | request_id=5536042 | resp→lq_complete（VA/PA 字段原始为 0/部分记录） | 可交付污染值 | 回到处理器 |
| register file（taint） | load 数据 | clean→tainted（x4/68、x5/153） | 两个被污染寄存器 | 存储→CPU 边界 |
| commit/ROB | dyn 5536042 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F1-W1 seed3 在 tick 239629862268 把用户页 VA=7fe7c61d40 的 PPN bit14 翻转（0x83111→0x87111，mask 0x4000），错误 PA=87111d40 经 LQ→L1D/MSHR→resp/lq_complete 进入 x4/phys68 与 x5/phys153（43/44），event 45 真实错误提交；运行结局 Crash，3 条 L4 squash 与 fault2/3 是旁支。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 3 条 hit；`CHAOS_LSU_TRIGGER` 为 `attempted=3442472 eligible=3442472 injected=3`；`stats.txt` numFaultsInjected=3；`chain_report` faults=3。四方一致。fault1 的 PPN 被 event 1/2/3 读取、event 4/5 消费，activated 为真；fault2/3 只到 L4。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x4000 翻转 bit14，错误 PA=87111d40 经 LQ/cache/MSHR；不是 data/permission/control-state/timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=239629862268）**：错误 PA=87111d40 交付 LSU；之后只有 squash/replay 可撤销，而 45 的祖先上没有。event 43/44 的 taint_reg（x4/68、x5/153）是寄存器层点；event 45 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；本 seed 有 3 条 L4 `squash_masked`（event 86/87/101，VA=7fe7c61d18/…1d20/…1ce0，contained=1），均在 event 45 之后/其它请求上；fault2/3 的 chain_end 21444/21445 为 L4 detected_contained。RAS 对后续请求有效，但没有覆盖 event 45。检测盲区：PPN bit14 翻转仍合法。另需说明：resp/lq_complete/taint_reg 的部分 VA/PA 字段在原始流中为 0 或不完整，本文件按原值保留，不据此推断地址。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 45）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。silent-error 不能证明也不能排除。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed3 注入 tick=239629862268、VA=7fe7c61d40、mask=0x4000、PFN 83111→87111、终局 45、Crash；seed1 是 239595855309/...3b48/mask 0x4000/event 87；seed2 是 239345234181/7f82b83d08/mask 0x1/event 20。三者地址/mask/终局不同；本文件只用 seed3 的寄存器 x4/x5 与事件号。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）终局 `errant_commit` 的 `parent_event_id` 单祖先重建；`path_event_ids` 只作层锚点。`—` 表示原始事件无该字段；原始流中显式为 0 的字段保留为 0。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239629862268 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | 83111 | 87111 | 83111 | 87111 | 0x4000 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 83111→87111 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 239629862268 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | 83111 | 87111 | 83111 | 87111 | — | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40 | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40 | — | — | — | — | VA=7fe7c61d40 的命中查找，request_id=5536042 | 命中表项返回 pfn=87111 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 239629862268 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | 83111 | 87111 | 83111 | 87111 | — | 83111d40 | 87111d40 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=87111d40（pfn=87111） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 239629862268 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | — | — | 83111d40 | 87111d40 | — | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40 | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=87111d40，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 239629862268 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=5536042 的请求，VA=7fe7c61d40 | request_id=5536042 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 239629862268 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=87111d40 的访问，request_id=5536042 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 7 | 6 | 5 | 239629862268 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=87111d40 的访问，request_id=5536042 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 239629862268 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=87111d40，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 9 | 8 | 7 | 239629862601 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=87111d40 的访问，request_id=5536042 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 10 | 9 | 8 | 239629862601 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=87111d40 的访问，request_id=5536042 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 239629862601 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=87111d40，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 12 | 35 | 10 | 239629921542 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=87111d40，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 36 | 35 | 239629921542 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=87111d40 | pa=87111d40 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 14 | 37 | 36 | 239629921542 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=87111d40，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 15 | 38 | 37 | 239629922208 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=87111d40，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 39 | 38 | 239629922208 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=87111d40 | pa=87111d40 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 17 | 40 | 39 | 239629922208 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=87111d40，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 18 | 41 | 40 | 239629922541 | 333 | resp | L3 | response path | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id= 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 19 | 42 | 41 | 239629922541 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 0 | 5536042 | 7fe7c61d32 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=0 的响应 | load 完成（lq_idx=594678） | 错误值被标记为可交付，进入寄存器写回 |
| 20 | 43 | 42 | 239629922541 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=4，phys_reg=68） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 44 | 43 | 239629922541 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=5，phys_reg=153） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 22 | 45 | 44 | 239629923207 | 666 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 5536042 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 27950 条原始事件（report 25388 非 consumer；consumer 2562）；主链只取 event 45 的 22 个单祖先。旁支事实：

- `request_fork` 10 条，主链 0 条；从主链节点 10（6 条）与 40（4 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=87111000`、`shared_size=1000`；new_request_id 如 5536060/5536064/5536091/…。它们不进入 45 的祖先。
- 旁支 `taint_reg` 9 条，主链 2 条（43/44）；`resp` 8 条，主链 1 条（41）；`lq_complete` 8 条，主链 1 条（42）。
- `squash_masked` 3 条：event 86（VA=7fe7c61d18）、87（…1d20）、101（…1ce0），均 L4/contained=1，在 event 45 之后或其它请求上。
- `chain_end`：fault1 event 21443（tick=243383282757，L5 errant_commit_seen）；fault2 event 21444、fault3 event 21445，均为 L4 detected_contained。
- **其它 fault**：fault2 event 1371（VA=ffffffc00948bf78，PFN 81d4d→91d4d，mask 0x10000，sq_execute，taint 1408，squash 1615）→L4 contained；fault3 event 14621（VA=ffffffc00948bac0，PFN 81d4d→81d6d，mask 0x20，lq_read，taint 14670，squash 14678）→L4 contained。它们不并入 fault1。
- consumer 2562 条摘要不在主链。
- 影响：旁支与 fault2/3 不改变 event 45 的 L5；3 条 L4 squash 不能反推含住。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 45（errant_commit，tick=239629923207）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=2562，suppressed=3718459，logical_total=3721021，issues=[]）。
- count_contradiction：27950−25388=2562（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL OOPS 一致；checker full/L5 与报告一致；fault2/3 的 L4 不改变 fault1。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓（resp/taint 的 0 值按原样保留）8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- chain_evidence_status：**PASS**
- experiment_identity_status：**WORKLOAD_IDENTITY_MISMATCH**
- overall_experiment_status：**NOT_MIBENCH_RESULT**
- verdict：**NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果）

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。

- 其它说明：注意原始流中 resp/lq_complete/taint_reg 的 VA/PA 有 0 值/不完整，本文件没有用其它 seed 的地址补齐。
## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/prop_evt.txt.gz` | SHA-256 `0d2226c687af26db4300db1abf5f6c25470840852147d052f22f8a6e1675ffea`；963697 bytes；mtime `2026-10-27T16:16:16+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/prop_trace.csv.gz` | SHA-256 `2d799ca331951982e6bb463c8f5923761287c4910967ef045f3f47ee547fbbe8`；266724 bytes；mtime `2026-10-27T16:16:16+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/chain_report.json` | SHA-256 `c05a65bbcca8077f4c628584d32cc83d0af13c74cd608cf230370b74dd0c460b`；2236046 bytes；mtime `2026-10-27T16:16:19+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.out` | SHA-256 `4341f68f84a80fdaa9785da799d86c0fce1e6f752d7c47f567009c985a80291c`；11832 bytes；mtime `2026-10-27T16:16:17+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.err` | SHA-256 `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36`；1873 bytes；mtime `2026-10-27T16:16:17+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/stats.txt` | SHA-256 `593814dd596ff5efe16cd963181a2bab3ac26554487ba420a71a8cc352451650`；419893 bytes；mtime `2026-10-27T16:16:16+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/manifest.json` | SHA-256 `fbdb8f8ecafc25313a304ab1c7f0b69f0c6301d76a0df6d9abf1adb1be965c10`；1438 bytes；mtime `2026-10-27T16:16:20+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3 --cells T10-F1-W1 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/armtlb_injections.log` | SHA-256 `32c072f0e35ad861320a7b0697d30f1d8dbb46a732a44a560365f1378ea1ec39`；775 bytes；mtime `2026-10-27T16:16:08+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/board.workload.dmesg` | SHA-256 `f62a0e0d4167c2d2f93985d86dacf0a4449e8038da9f6689f6f89aed3f1db3a7`；13845 bytes；mtime `2026-10-27T16:16:16+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/board.terminal` | SHA-256 `f157e6855ecaaaa0774862cdf53ac249669d62fd07eef35de6e2ba5ca947fbce`；1787 bytes；mtime `2026-10-27T16:16:16+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/config.ini` | SHA-256 `96844c0714f38383ef32618d3a20dd7f0843b09f3f66c222e94b1b8ec01466a6`；97178 bytes；mtime `2026-10-27T16:14:30+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/config.json` | SHA-256 `3e0a83fcdd1eed881c18eff9d3129fc7d1ec18fc8bd38f77b4b77dd27978287e`；277159 bytes；mtime `2026-10-27T16:14:31+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `R6-AUTHORITATIVE-EVIDENCE.md` 未列出本 seed 的其它副本；权威目录唯一。

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
