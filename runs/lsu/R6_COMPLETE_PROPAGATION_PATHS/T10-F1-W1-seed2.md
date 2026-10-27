# T10-F1-W1 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F1-W1`；seed：`2`；sample_run_id：`s2`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F1` — 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T10-F1-W1 --prop_sample_run_id s2`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/manifest.json`（SHA-256 `069e0cb462608bc0227860deec73e5dac2efba623a414a67a71c581b752287eb`；1438 bytes；mtime `2026-10-27T14:46:28+0800`；该 manifest 的 seed 字段为 `2`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；420210 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **3564** 条；`chain_report.event_count`=**2279**（不含 consumer 事件），差值为 consumer 摘要数 1285
- fault_id 数量：**2**（注入日志共 3 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F1-W1 seed2 自己的流。代表故障 fault_id=1，终局 event 20（`errant_commit`）；祖先为 0–20（21 个事件，全部 parent 先于 child）。`path_event_ids=[0,1,2,4,19,20]` 只是层锚点。tick 单调不减；0–7、8–10、11–13、14–16、17–19 分别同 tick。

### 2.1 故障注入前的正常状态

**load**：event 4 `lq_read`（lq_idx=470727），dyn/request=`4338322`，VA=`0x7f82b83d08`。这不是内核高地址，而是用户空间地址；命中项 `vpn=7f82b83`、`asid=214`、`valid=1`、`global=0`、`pfn=8313b`、`ap=3`、`mtype=2`、`page_size=1000`、`pa=8313bd08`；way=-1（未记录）、entry_index=29，偏移 0xd08。正常 PFN=0x8313b、正常 PA=0x8313bd08；global=0 与 ap=3 是用户页的属性，与 seed1 的内核页不同。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`239345234181`，`field=bit_flip`，`before=8313b`、`after=8313a`，VA=`0x7f82b83d08`，`request_id=4338322`，`corr=origin`。注入日志：`old_pfn 0x8313b → new_pfn 0x8313a, Mask: 0x1`。0x8313b XOR 0x1 = 0x8313a，即 bit 0 从 1 变 0；偏移 0xd08 不变，PA 8313bd08→8313ad08，effective 变化为真。VPN/ASID/权限/页大小未变；这是 bit_flip 的单 bit 翻转。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 8313b→8313a（entry_index=29，way=-1）；event 2 `tlb_pfn` 记录 `state_before=8313bd08`、`state_after=8313ad08`、`pa=8313ad08`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=8313bd08`、`after=8313ad08`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit0 翻转后的 PPN 仍是合法编码，global=0/ap=3 未变。TLB 交付 request_id=4338322、PA=0x8313ad08 的 load。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `lq_read`（lq_idx=470727）读取错误 PA 的 load；本 seed 没有 lsq_push/sq_* 事件，记录的是 LQ 读取阶段。输入是 TLB 的 PA=8313ad08；内部变化是 load 以错误地址进入 LQ 读取；输出是 request_id=4338322 的 cache 访问。

### 2.5 错误如何经过 cache 和 MSHR

event 5 `cache_access`（pa=8313ad08）→event 6 `cache_return field=miss`→event 7 `mshr_alloc`（mshr_id=1，line 8313ad08）；event 8 访问 `pa=8313ad00`→event 9 miss→event 10 `mshr_alloc`（mshr_id=2，line 8313ad00）。event 11 `mshr_fill`（fill_id=1）→12 `cache_fill`→13 `mshr_free`；event 14 `mshr_fill`（mshr 0/fill 2）→15 `cache_fill`→16 `mshr_free`。错误行同属 0x8313a 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 17 `resp`（parent=16，tick=`239345294454`）交付 request_id=4338322 的响应；event 18 `lq_complete`（parent=17，lq_idx=470727）完成；event 19 `taint_reg`（parent=18，`arch_reg=12`、`phys_reg=110`、VA=`8313ad08`、clean→tainted、corr=seq_primary）。这是本 seed 明确记录的寄存器身份：x12/phys 110。`taint_reg` 是存储→CPU 边界，event 20 直接以它为 parent 提交。

### 2.7 最终传播终局

终局：event 20，`errant_commit`，`parent_event_id=19`，tick=`239345295120`，`dyn_inst_seq=4338322`（与 load 相同），`commit_seq=2988647`，`pc=7f82b8e3c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 2126（tick=`241672555530`，errant_commit_seen）；另有一条 `squash_masked` event 265（parent=20，tick=239349889521，VA=7f82b83cf8，L4，contained=1），它竟然是 event 20 的 child——说明在 L5 之后同一故障还有一次后续 load 被 squash；它不能把 event 20 的 L5 改写为含住。

为什么没有被提前消除：event 20 的祖先上没有 squash；event 265 晚于提交且不是祖先。为什么架构可见：`errant_commit` 越过提交边界。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 20，tick=`239345295120`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=239345295120 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`239345234181`，终局 tick=`239345295120`，延迟 **60939 ticks**。
- 因果链：L5 → guest kernel oops → Crash。event 265 与 fault2（L4）都不能改写 event 20；没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=7f82b83d08，entry=29，PFN=8313b，ASID=214，global=0 | bit0 翻转→8313a | request_id=4338322，PA=8313ad08 | 错误 PPN 进入地址 |
| LQ | load lq_idx=470727 | lq_read 接受错误 PA | cache 请求 | 错误地址被 LQ 接受 |
| L1D cache | PA=8313ad08 / line 8313ad00 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 8313ad08/8313ad00 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response / LQ complete | request_id=4338322 | resp→lq_complete | 可交付污染值 | 回到处理器 |
| register file（taint） | load 数据 | clean→tainted（x12/110） | 被污染寄存器 | 存储→CPU 边界 |
| commit/ROB | dyn 4338322 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F1-W1 seed2 在 tick 239345234181 把用户页 VA=7f82b83d08 的 PPN bit0 翻转（0x8313b→0x8313a，mask 0x1），错误 PA=8313ad08 经 LQ→L1D/MSHR→resp/lq_complete（17/18）进入 x12/phys110（19），event 20 真实错误提交；event 265 是 L5 之后的 L4 squash，不能改写终局，运行结局 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 2 条 hit；`CHAOS_LSU_TRIGGER` 为 `attempted=1901753 eligible=1901753 injected=2`；`stats.txt` numFaultsInjected=2；`chain_report` faults=2。四方一致。fault1 的 PPN 被 event 1/2/3 读取、event 4/5 消费，activated 为真；fault2 只到 L4。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x1 翻转 bit0，错误 PA=8313ad08 经 LQ/cache/MSHR；不是 data/permission/control-state/timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=239345234181）**：错误 PA=8313ad08 交付 LSU；之后只有 squash/replay 可撤销，而 event 20 的祖先上没有。event 19 的 taint_reg（x12/phys110）是寄存器层点；event 20 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；本 seed 只有 1 条 L4 `squash_masked`（event 265，tick=239349889521，VA=7f82b83cf8，contained=1），它的 parent 是 event 20（已提交的 L5）；它属于 L5 之后的后续 load，不能把 event 20 改写为含住。检测盲区：PPN bit0 翻转仍合法，权限/有效位检查无效。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 20）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。event 265 的 L4 含住发生在 L5 之后，不能反推 L5 被消除。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed2 注入 tick=239345234181、VA=7f82b83d08、mask=0x1、PFN 8313b→8313a、终局 20、Crash；seed1 是 239595855309/VA=ffffffc009483b48/mask 0x4000/event 87；seed3 是 239629862268/VA=7fe7c61d40/mask 0x4000/event 45。三者地址/mask/终局不同；本文件不引用 seed1/3 的寄存器或 squash。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）终局 `errant_commit` 的 `parent_event_id` 单祖先重建；`path_event_ids` 只作层锚点。`—` 表示原始事件无该字段；原始流中显式为 0 的字段保留为 0。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239345234181 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 4338322 | 4338322 | 7f82b83d08 | — | — | — | 8313b | 8313a | 8313b | 8313a | 0x1 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 8313b→8313a | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 239345234181 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | — | — | — | 8313b | 8313a | 8313b | 8313a | — | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08 | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08 | — | — | — | — | VA=7f82b83d08 的命中查找，request_id=4338322 | 命中表项返回 pfn=8313a | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 239345234181 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | 8313b | 8313a | 8313b | 8313a | — | 8313bd08 | 8313ad08 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=8313ad08（pfn=8313a） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 239345234181 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | — | — | 8313bd08 | 8313ad08 | — | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08 | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=8313ad08，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 239345234181 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=4338322 的请求，VA=7f82b83d08 | request_id=4338322 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 239345234181 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=8313ad08 的访问，request_id=4338322 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 7 | 6 | 5 | 239345234181 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=8313ad08 的访问，request_id=4338322 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 239345234181 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad08 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=8313ad08，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 9 | 8 | 7 | 239345234514 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 4338322 | 4338322 | 7f82b83d08 | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=8313ad00 的访问，request_id=4338322 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 10 | 9 | 8 | 239345234514 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=8313ad00 的访问，request_id=4338322 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 239345234514 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=8313ad00，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 12 | 11 | 10 | 239345293455 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=8313ad00，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 12 | 11 | 239345293455 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad00 | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=8313ad00 | pa=8313ad00 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 14 | 13 | 12 | 239345293455 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=8313ad00，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 15 | 14 | 13 | 239345294121 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=8313ad00，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 15 | 14 | 239345294121 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad00 | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=8313ad00 | pa=8313ad00 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 17 | 16 | 15 | 239345294121 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=8313ad00，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 18 | 17 | 16 | 239345294454 | 333 | resp | L3 | response path | 1 | seq_primary | 4338322 | 4338322 | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=4338322 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 19 | 18 | 17 | 239345294454 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=4338322 的响应 | load 完成（lq_idx=470727） | 错误值被标记为可交付，进入寄存器写回 |
| 20 | 19 | 18 | 239345294454 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 4338322 | 4338322 | 8313ad08 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=12，phys_reg=110） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 20 | 19 | 239345295120 | 666 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 4338322 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 3564 条原始事件（report 2279 非 consumer；consumer 1285）；主链只取 event 20 的 21 个单祖先。旁支事实：

- `request_fork` 56 条，主链 0 条；全部从主链节点 19（taint_reg）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=8313a000`、`shared_size=1000`；new_request_id 如 4339263/4339264/4340744/…。它们不进入 event 20 的祖先。
- 旁支 `taint_reg` 55 条，主链 1 条（19）；`resp` 55 条，主链 1 条（17）；`lq_complete` 55 条，主链 1 条（18）。
- `squash_masked` 1 条：event 265（parent=20，tick=239349889521，VA=7f82b83cf8，L4，contained=1，squash_replay）。它是已提交 L5 的 child，属于后到的含住，不是终点见证；不能把 event 20 说成 contained。
- `chain_end`：fault1 event 2126（tick=241672555530，L5 errant_commit_seen）；fault2 event 2127（L4 detected_contained，store_discarded_not_retired）。
- **另一个故障 fault2**：event 313 注入 tick=240401619738、VA=ffffff8001af29e0、PFN 81af2→c1af2、mask 0x40000；路径 314/315/317/362 到 taint_reg，终局 provable_to_L4_then_unknown。它不并入 fault1。
- consumer 1285 条摘要不在主链。
- 影响：旁支与 fault2 不改变 event 20 的 L5；event 265 的 L4 发生在 L5 之后，不能反推含住。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 20（errant_commit，tick=239345295120）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=1285，suppressed=824745，logical_total=826030，issues=[]）。
- count_contradiction：3564−2279=1285（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL OOPS 一致；checker full/L5 与报告一致；event 265 的 L4 是 L5 之后的旁支，不改变 terminal。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（真实含住事件存在于旁支，但终局不是含住）✓ 12✓ 13✓ 14✓ 15✓。
- chain_evidence_status：**PASS**
- experiment_identity_status：**WORKLOAD_IDENTITY_MISMATCH**
- overall_experiment_status：**NOT_MIBENCH_RESULT**
- verdict：**NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果）

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。

- 其它说明：event 265 的 parent 是 event 20（L5），它是“L5 之后的后到 squash”，不是被选中的终局见证；不能把它写成 L5 被含住。
## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/prop_evt.txt.gz` | SHA-256 `5680f0a4e26d16433434a5bbc146cd8d073167668a964a8cff97626561cd5c01`；136919 bytes；mtime `2026-10-27T14:46:26+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/prop_trace.csv.gz` | SHA-256 `850f05b5a44489f5279698ca533a3ac5f5d9ea78c4d7b6bc6da764f3ff8fec03`；40274 bytes；mtime `2026-10-27T14:46:26+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/chain_report.json` | SHA-256 `214430c01a30fcdcdbbf76f9e0001070c8679aaaa46fb07328dbce98d91d2f75`；1119921 bytes；mtime `2026-10-27T14:46:27+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.out` | SHA-256 `418bc61b8c11c1f018632381ab5870ef795186d8c78cc6b245e20d932ba14939`；2746 bytes；mtime `2026-10-27T14:46:26+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.err` | SHA-256 `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17`；1973 bytes；mtime `2026-10-27T14:46:26+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/stats.txt` | SHA-256 `652d4f46d0e65b462544ef4892eba6172c0b90970ccfefff8fafadd9a8671e91`；420210 bytes；mtime `2026-10-27T14:46:26+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/manifest.json` | SHA-256 `069e0cb462608bc0227860deec73e5dac2efba623a414a67a71c581b752287eb`；1438 bytes；mtime `2026-10-27T14:46:28+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2 --cells T10-F1-W1 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/armtlb_injections.log` | SHA-256 `63dd2cbe58dd058cb6826f5beaeb5aee70cb3faa5089a80239d544d728b57a62`；579 bytes；mtime `2026-10-27T14:46:14+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/board.workload.dmesg` | SHA-256 `8285e0b4ea657afff16bbe538c7bb208fa39eef5bc9bec7e58332b02e97b8af0`；14608 bytes；mtime `2026-10-27T14:46:26+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/board.terminal` | SHA-256 `8182affa798cf2d54ebd90cee0dfeb50c99b866ff467c0c24a28d268ee3d8f9f`；2635 bytes；mtime `2026-10-27T14:46:26+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/config.ini` | SHA-256 `2c8b2d064871099e3ca0e1fe5750c610953b84aaaf2560c9abcb0f8ea0c83ed3`；97178 bytes；mtime `2026-10-27T14:45:24+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/config.json` | SHA-256 `79682bdc44dc66229e31b3fc9ce68593913139b48f86d74abd8e885675e05a25`；277159 bytes；mtime `2026-10-27T14:45:24+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `R6-AUTHORITATIVE-EVIDENCE.md` 未列出本 seed 的其它副本；权威目录唯一。

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
