# T10-F1-W1 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F1-W1`；seed：`1`；sample_run_id：`s1`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F1` — 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T10-F1-W1 --prop_sample_run_id s1`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/manifest.json`（SHA-256 `7c965ce3475e6898b006fb6c25ea4c8ead41b714f362b9901806c16e99109ce4`；1438 bytes；mtime `2026-10-27T13:14:32+0800`；该 manifest 的 seed 字段为 `1`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；415803 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **11165** 条；`chain_report.event_count`=**9884**（不含 consumer 事件），差值为 consumer 摘要数 1281
- fault_id 数量：**1**（注入日志共 2 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F1-W1 seed1 自己的流。代表故障 fault_id=1，终局 event 87（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,9,10,11,45,46,47,48,49,50,51,52,53,87（22 个事件）。`path_event_ids=[0,1,2,4,52,87]` 只是层锚点。tick 单调不减；0–4、5–8、9–11、45–47、48–50、51–53 分别同 tick。

### 2.1 故障注入前的正常状态

**store**：event 4 `sq_execute`（sq_idx=479071，state_before=issued），dyn/request=`5368746`，VA=`0xffffffc009483b48`。注入前命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75b48`；way=-1（未记录）、entry_index=20，偏移 0xb48。正常 PFN=0x81d75、正常 PA=0x81d75b48。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`239595855309`，`field=bit_flip`，`before=81d75`、`after=85d75`，VA=`0xffffffc009483b48`，`request_id=5368746`，`corr=origin`。注入日志：`old_pfn 0x81d75 → new_pfn 0x85d75, Mask: 0x4000`。0x81d75 XOR 0x4000 = 0x85d75，即 bit 14 从 0 变 1；偏移 0xb48 不变，PA 81d75b48→85d75b48，effective 变化为真。VPN/ASID/权限/页大小未变；这是 bit_flip 的单 bit 翻转，不是整页替换。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 81d75→85d75（entry_index=20，way=-1）；event 2 `tlb_pfn` 记录 `state_before=81d75b48`、`state_after=85d75b48`、`pa=85d75b48`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=81d75b48`、`after=85d75b48`、`contained=0`、`outcome=NoFault`。TLB 没有含住：翻转后的 PPN 仍是合法编码，权限/有效位/页大小未变。TLB 交付 request_id=5368746、PA=0x85d75b48 的 store。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `sq_execute`（sq_idx=479071）把错误 store 置为 issued；event 5 `sq_writeback`（parent=4，tick=`239595856641`）以 `pa=85d75b48` 构造 packet，state_after=packet_built。输入是 TLB 的错误 PA；内部变化是 store 从执行到 packet；输出是错误地址的 cache 请求；下一步 L1D/MSHR 按此地址访问。store 阶段的 request_id 为空，cache 阶段重新带 request_id=5368746。

### 2.5 错误如何经过 cache 和 MSHR

event 6 `cache_access`（pa=85d75b48）→event 7 `cache_return field=miss`→event 8 `mshr_alloc`（mshr_id=1，line 85d75b48）；event 9 访问 `pa=85d75b40`→event 10 miss→event 11 `mshr_alloc`（mshr_id=2，line 85d75b40）。event 45 `mshr_fill`（fill_id=1）→46 `cache_fill`→47 `mshr_free`；event 48 `mshr_fill`（mshr 0/fill 2）→49 `cache_fill`→50 `mshr_free`。错误行同属 0x85d75 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 51 `resp`（parent=50，tick=`239595916914`）交付 request_id=5368746 的响应；event 52 `taint_reg`（parent=51）clean→tainted，VA=`85d75b48`；原始事件没有 arch_reg/phys_reg，因此不编造。event 53 `sq_complete`（parent=52，sq_idx=479071）把 store 标为 completed。`taint_reg` 是存储→CPU 边界，event 53 之后进入提交。

### 2.7 最终传播终局

终局：event 87，`errant_commit`，`parent_event_id=53`，tick=`239595941223`，`dyn_inst_seq=5368813`，`commit_seq=3579740`，`pc=ffffffc0081e6204`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 8371（tick=`240442153830`，errant_commit_seen），只是流收口；本 seed 有 50 条 L4 `squash_masked`，但都不在 87 的祖先上（最早一条 event 972，tick=239597541288，晚于 L5）。

为什么没有被提前消除：event 87 的祖先上没有 squash/replay/contained；错误值从 taint_reg 52 直接提交。为什么架构可见：`errant_commit` 越过提交边界。dyn 不一致（store 5368746，终局 5368813）用 parent=53/corr=taint_prop 的建模约定解释：parent 指向被污染 store 的完成，corr 指向后续消费者；消费者 fork 在第 5 章，不在 87 祖先上。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 87，tick=`239595941223`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=239595941223 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`239595855309`，终局 tick=`239595941223`，延迟 **85914 ticks**。
- 因果链：L5 → guest kernel oops → Crash。50 条 L4 squash 与 chain_end 8371 都不能改写 event 87；没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483b48，entry=20，PFN=81d75 | bit14 翻转→85d75 | request_id=5368746，PA=85d75b48 | 错误 PPN 进入地址 |
| SQ | store sq_idx=479071 | sq_execute→sq_writeback→sq_complete | 错误 store packet | 错误地址被 SQ 接受 |
| L1D cache | PA=85d75b48 / line 85d75b40 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 85d75b48/85d75b40 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response | request_id=5368746 | resp 交付 | 可交付污染值 | 回到处理器 |
| register file（taint） | store 数据 | clean→tainted（arch/phys 未记录） | 被标记状态 | 存储→CPU 边界 |
| commit/ROB | dyn 5368813 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F1-W1 seed1 在 tick 239595855309 把 VA=ffffffc009483b48 的 PPN bit14 翻转（0x81d75→0x85d75，mask 0x4000），错误 PA=85d75b48 经 SQ（4/5）→L1D/MSHR（6–50）→resp/taint_reg/sq_complete（51–53）传播，event 87 真实错误提交；运行结局 Crash，50 条 L4 squash 是旁支。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；`CHAOS_LSU_TRIGGER` 为 `attempted=1390245 eligible=1390245 injected=1`；`stats.txt` numFaultsInjected=1；`chain_report` faults=1。四方一致。event 1/2/3 读取物化错误 PPN，event 4/5 消费错误 PA，activated 为真。原始事件 11165 条，report event_count=9884（consumer 摘要 1281），已对账。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x4000 翻转 bit14，错误 PA=85d75b48 经 SQ/cache/MSHR；不是 data（翻转在 PPN 地址字段）、permission（ap=0 未变）、control-state 或 timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=239595855309）**：错误 PA 交付 LSU；之后只有 squash/replay 可撤销，而 87 的祖先上没有。event 52 的 taint_reg 是寄存器层点；event 87 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；L1D/MSHR 无地址正确性检查；本 seed 有 50 条 L4 `squash_masked`（最早 event 972，tick=239597541288，晚于 L5），都在 87 的祖先之外；它们说明 RAS 对后续请求有效，但没有覆盖 event 87。检测盲区：PPN 的合法位翻转不触发权限/有效位检查。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 87）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。silent-error 在提交后到 oops 的窗口不能证明也不能排除；本文件只声明 L5+Crash+50 条 L4 旁支。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

事实对比：seed1 注入 tick=239595855309、VA=ffffffc009483b48、mask=0x4000、PFN 81d75→85d75、终局 87、Crash；seed2 是 239345234181、VA=7f82b83d08（用户页）、mask=0x1、PFN 8313b→8313a、终局 20、Crash，且有一条 parent=20 的 L4 squash 265；seed3 是 239629862268、VA=7fe7c61d40、mask=0x4000、PFN 83111→87111、终局 45、Crash。三者地址/mask/终局不同；本文件不把 seed2 的 x12/phys110 或 seed3 的 x4/x5 写进 seed1。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）终局 `errant_commit` 的 `parent_event_id` 单祖先重建；`path_event_ids` 只作层锚点。`—` 表示原始事件无该字段；原始流中显式为 0 的字段保留为 0。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239595855309 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 5368746 | 5368746 | ffffffc009483b48 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | 0x4000 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→85d75 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 239595855309 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48 | — | — | — | — | VA=ffffffc009483b48 的命中查找，request_id=5368746 | 命中表项返回 pfn=85d75 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 239595855309 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | 85d75b48 | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | 81d75b48 | 85d75b48 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=85d75b48（pfn=85d75） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 239595855309 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | 85d75b48 | — | — | — | — | 81d75b48 | 85d75b48 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=85d75b48，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 239595855309 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 5368746 | ffffffc009483b48 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | dyn_inst_seq=5368746 的请求，VA=ffffffc009483b48 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 239595856641 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 5368746 | — | 85d75b48 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | dyn_inst_seq=5368746 的请求 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 239595856641 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 5368746 | 5368746 | ffffffc009483b48 | 85d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75b48 的访问，request_id=5368746 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 239595856641 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75b48 的访问，request_id=5368746 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 239595856641 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b48 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=85d75b48，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 9 | 8 | 239595856974 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 5368746 | 5368746 | ffffffc009483b48 | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75b40 的访问，request_id=5368746 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 239595856974 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85d75b40 的访问，request_id=5368746 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 11 | 10 | 239595856974 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=85d75b40，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 45 | 11 | 239595915915 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=85d75b40，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 46 | 45 | 239595915915 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b40 | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=85d75b40 | pa=85d75b40 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 47 | 46 | 239595915915 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=85d75b40，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 48 | 47 | 239595916581 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=85d75b40，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 49 | 48 | 239595916581 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b40 | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=85d75b40 | pa=85d75b40 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 50 | 49 | 239595916581 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=85d75b40，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 51 | 50 | 239595916914 | 333 | resp | L3 | response path | 1 | seq_primary | 5368746 | 5368746 | 85d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=5368746 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 52 | 51 | 239595916914 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 5368746 | 5368746 | 85d75b48 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 53 | 52 | 239595916914 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 5368746 | ffffffc009483b48 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | sq_idx=479071 的 store 完成 | store 完成状态 | 错误 store 效果被标记为完成，等待提交 |
| 22 | 87 | 53 | 239595941223 | 24309 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 5368813 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 11165 条原始事件（report 9884 非 consumer；consumer 1281）；主链只取 event 87 的 22 个单祖先。旁支事实：

- `request_fork` 1512 条，主链 0 条；从主链节点 11（9 条）与 52（1503 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=85d75000`、`shared_size=1000`；new_request_id 如 5368751/5368752/5368755/…。它们不进入 87 的祖先。
- 旁支 `taint_reg` 1678 条，主链 1 条（52）；`resp` 1430 条，主链 1 条（51）；`lq_complete` 493 条，主链 0 条。
- `squash_masked` 50 条，全部 L4/contained=1/squash_replay，例如 event 972（VA=ffffffc009483860，tick=239597541288）、1399、1854、1889…；均晚于 event 87 或在其它请求上，不能改写 L5。
- `chain_end` 是 event 8371（tick=240442153830，errant_commit_seen）。
- consumer 1281 条摘要不在主链。
- 影响：旁支与 50 次 L4 响应说明错误页持续被访问、RAS 对后续 load 有效；但 event 87 的提交未被覆盖，终局 full/L5。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 87（errant_commit，tick=239595941223）。
- run outcome：`Crash`（oracle=Crash，exit=0）；guest kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=1281，suppressed=504111，logical_total=505392，issues=[]）。
- count_contradiction：11165−9884=1281（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL OOPS 一致；checker full/L5 与报告一致。
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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/prop_evt.txt.gz` | SHA-256 `0038e158450d045d4c7aa09e7532cdd3a80f7fefce2883be2afb88adc5817fb8`；386922 bytes；mtime `2026-10-27T13:14:29+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/prop_trace.csv.gz` | SHA-256 `3eeb4ceccbf4e2fdf8ce6172c709ba3944bfc63708c217887a231f9feda368d1`；107279 bytes；mtime `2026-10-27T13:14:29+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/chain_report.json` | SHA-256 `b076dd772f5175b71378dc37cfcf92a7cc41738c21adfd9f3a36e0ce544fe875`；1102976 bytes；mtime `2026-10-27T13:14:31+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/run.out` | SHA-256 `305c2e252c382dff061ee77ee7168fa6e226a510697e30fbe9256e0d703ad26b`；7100 bytes；mtime `2026-10-27T13:14:30+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/run.err` | SHA-256 `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36`；1873 bytes；mtime `2026-10-27T13:14:30+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/stats.txt` | SHA-256 `fbce23e26076a360f340deecfb24c5f03c5aa417228b410c10a7605b25dc6321`；415803 bytes；mtime `2026-10-27T13:14:30+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/manifest.json` | SHA-256 `7c965ce3475e6898b006fb6c25ea4c8ead41b714f362b9901806c16e99109ce4`；1438 bytes；mtime `2026-10-27T13:14:32+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1 --cells T10-F1-W1 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/armtlb_injections.log` | SHA-256 `1d2350948e8161c9a803ce72703f3ab86ea574aac88250036f6c726b5160e4be`；392 bytes；mtime `2026-10-27T13:14:21+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/board.workload.dmesg` | SHA-256 `af79a9fcf5b892c604e85a3ffafd3f2ba590bf35ef97d7b69bae67664c3e6fa1`；13845 bytes；mtime `2026-10-27T13:14:29+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/board.terminal` | SHA-256 `0f27e00d74fbbf704c98a36092c44601401b4cf8e67c326c925aa71b423b805b`；1736 bytes；mtime `2026-10-27T13:14:29+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/config.ini` | SHA-256 `22f66d13b660688f220828d234845552bc3c7142dc7cdc8dfa09ce83713d98c7`；97178 bytes；mtime `2026-10-27T13:13:38+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1/config.json` | SHA-256 `6d2d70dc512fb114eb37fbcf79237cf1340a87bcb79f50e751e99ebecdc4e61d`；277159 bytes；mtime `2026-10-27T13:13:38+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s1/T10-F1-W1/seed1`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_n8_T10-F1-W1_s1.sha8a229009/T10-F1-W1/seed1` — **OLD_BINARY_REFERENCE**（manifest binary 8a229009c933a6dc…，不是权威 20fda6994ee257e6…）

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
