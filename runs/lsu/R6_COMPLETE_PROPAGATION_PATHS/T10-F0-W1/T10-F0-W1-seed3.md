# T10-F0-W1 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F0-W1`；seed：`3`；sample_run_id：`s3`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 3 --chaos_propagation --prop_run_id T10-F0-W1 --prop_sample_run_id s3`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/manifest.json`（SHA-256 `233944c091b3ee48965623449ead0e98b4ca4ba12ef98d87caf2f9b08f541f1d`；1438 bytes；mtime `2026-10-27T16:15:59+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；381642 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **454** 条；`chain_report.event_count`=**444**（不含 consumer 事件），差值为 consumer 摘要数 10
- fault_id 数量：**1**（F0 每次运行只注入 1 次；注入日志只有 1 条命中记录）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F0-W1 seed3 自己的流。终局 event 293（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,9,10,11,12,64,65,66,67,68,69,73,74,75,293（23 个事件）。`path_event_ids=[0,1,2,5,74,293]` 只是层锚点。tick 单调不减；0–3、4–5、6–8、10–12、64–66、67–69、73–75 分别同 tick。

### 2.1 故障注入前的正常状态

**store**：event 4 `lsq_push`（field=store，sq_idx=1，lq_idx=-1，pc=ffffffc008011614），event 5 `sq_execute`（sq_idx=1，state_before=issued），dyn/request=`31`，VA=`0xffffffc009483eb0`。注入前命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75eb0`；way=-1（未记录）、entry_index=0，偏移 0xeb0。正常 PFN=0x81d75、正常 PA=0x81d75eb0。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`237950233578`，`field=bit_flip`，`before=81d75`、`after=91d75`，VA=`0xffffffc009483eb0`，`request_id=31`，`corr=origin`。注入日志：`old_pfn 0x81d75 → new_pfn 0x91d75, Mask: 0x10000, effective: 1`。0x81d75 XOR 0x10000 = 0x91d75，即 bit 16 从 0 变 1；偏移 0xeb0 不变，PA 81d75eb0→91d75eb0，effective 变化为真。VPN/ASID/权限/页大小未变；这是 bit_flip 的单 bit 翻转。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 81d75→91d75（entry_index=0，way=-1）；event 2 `tlb_pfn` 记录 `state_before=81d75eb0`、`state_after=91d75eb0`、`pa=91d75eb0`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=81d75eb0`、`after=91d75eb0`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit 翻转后的 PPN 仍是合法编码，权限/有效位/页大小未变。TLB 交付 request_id=31、PA=0x91d75eb0 的 store。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `lsq_push`（field=store，sq_idx=1，lq_idx=-1）把错误 PA 的 store 压入；event 5 `sq_execute`（sq_idx=1，issued）；event 6 `sq_writeback`（parent=5，tick=`237950235243`）以 `pa=91d75eb0` 构造 packet，state_after=packet_built。输入是 TLB 的错误 PA；内部变化是 store 从入队到执行到 packet；输出是错误地址的 cache 请求；下一步 L1D/MSHR 按此地址处理。事件 4 的 request_id 为空，store 以 sq_idx 标识；cache 阶段重新带 request_id=31。

### 2.5 错误如何经过 cache 和 MSHR

event 7 `cache_access`（pa=91d75eb0）→event 8 `cache_return field=miss`→event 9 `mshr_alloc`（mshr_id=1，line 91d75eb0）；event 10 访问 `pa=91d75e80`→event 11 miss→event 12 `mshr_alloc`（mshr_id=2，line 91d75e80）。event 64 `mshr_fill`（fill_id=1）→65 `cache_fill`→66 `mshr_free`；event 67 `mshr_fill`（mshr 0/fill 2）→68 `cache_fill`→69 `mshr_free`。错误行同属 0x91d75 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 73 `resp`（parent=69，tick=`237950295516`）交付 request_id=31 的响应；event 74 `taint_reg`（parent=73）clean→tainted，VA=`91d75eb0`；原始事件没有 arch_reg/phys_reg，因此不编造。event 75 `sq_complete`（parent=74，sq_idx=1）把 store 标为 completed。`taint_reg` 是存储→CPU 边界，event 75 之后进入提交。

### 2.7 最终传播终局

终局：event 293，`errant_commit`，`parent_event_id=75`，tick=`237951302175`，`dyn_inst_seq=391`，`commit_seq=161`，`pc=ffffffc0087b1000`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 390（tick=`238882039506`，errant_commit_seen），只是流收口；唯一 squash 是 event 319（tick=`237951547263`，VA=ffffffc009483e40，L4，contained=1），晚于 L5 且在另一 VA。

为什么没有被提前消除：event 293 祖先上没有 squash；为什么架构可见：提交越过重定序边界。dyn 不一致（store 31，终局 391）用 parent=75/corr=taint_prop 的建模约定解释；消费者 fork 在第 5 章，不在 293 祖先上。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 293，tick=`237951302175`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`237950233578`，终局 tick=`237951302175`，延迟 **1068597 ticks**。
- 因果链：L5 → guest kernel oops → Crash。event 319 的晚到 squash 与 chain_end 390 都不能改写 293。没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483eb0，entry=0，PFN=81d75 | bit16 翻转→91d75 | request_id=31，PA=91d75eb0 | 错误 PPN 进入地址 |
| LQ/SQ | store sq_idx=1 | lsq_push→sq_execute→sq_writeback→sq_complete | 错误 store packet | 错误地址被 SQ 接受 |
| L1D cache | PA=91d75eb0 / line 91d75e80 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 91d75eb0/91d75e80 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response | request_id=31 | resp 交付 | 可交付污染值 | 回到处理器 |
| register file（taint） | store 数据 | clean→tainted（arch/phys 未记录） | 被标记状态 | 存储→CPU 边界 |
| commit/ROB | dyn 391 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F0-W1 seed3 在 tick 237950233578 把 VA=ffffffc009483eb0 的 PPN bit16 翻转（0x81d75→0x91d75，mask 0x10000），错误 PA=91d75eb0 经 store queue（4–6）→L1D/MSHR（7–69）→resp/taint_reg/sq_complete（73–75）传播，event 293 真实错误提交；运行结局 Crash，晚到的 L4 squash 319 不改变 L5。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；`CHAOS_LSU_TRIGGER` 为 `attempted=150170 eligible=1 injected=1`；`stats.txt` numFaultsInjected=1；`chain_report` faults=1。四方一致。event 1/2/3 读取物化错误 PPN，event 4/5/6 消费错误 PA，activated 为真。原始事件 454 条，report event_count=444（10 条 consumer 摘要），已对账。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x10000 翻转 bit16，错误 PA=91d75eb0 经 SQ/cache/MSHR；不是 data/permission/control-state/timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=237950233578）**：错误 PA=91d75eb0 交付 LSU；之后只有 squash/replay 可撤销，而 293 的祖先上没有。event 74 的 taint_reg 是寄存器层点；event 293 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；L1D/MSHR 无地址正确性检查；本 seed 有 1 条 L4 squash（event 319，tick=237951547263，VA=ffffffc009483e40，contained=1，squash_replay），晚于 L5 且在另一 VA。检测盲区：PPN 合法位翻转无法由权限/有效位检查发现。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 293）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。silent-error 不能证明也不能排除；本文件只声明 L5+Crash。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed3 注入 tick=237950233578、VA=ffffffc009483eb0、mask=0x10000、PFN 81d75→91d75、终局 293、Crash；seed1 是 237950940537/...3fa8/mask 0x20000/event 118；seed2 是 237950233911/...3eb8/mask 0x400/event 283。三者地址/mask/延迟不同；本文件不引用 seed1/2 的寄存器或事件。

## 4. 完整主链事件表

> 主链按终局 `errant_commit` 的 `parent_event_id` 单祖先重建；`path_event_ids` 只作层锚点，不作为完整链。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 91d75 | 81d75 | 91d75 | 0x10000 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→91d75 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 237950233578 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 91d75 | 81d75 | 91d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0 | — | — | — | — | VA=ffffffc009483eb0 的命中查找，request_id=31 | 命中表项返回 pfn=91d75 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 237950233578 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | 91d75eb0 | — | — | 81d75 | 91d75 | 81d75 | 91d75 | — | 81d75eb0 | 91d75eb0 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=91d75eb0（pfn=91d75） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 237950233578 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | 91d75eb0 | — | — | — | — | 81d75eb0 | 91d75eb0 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=91d75eb0，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 237950233911 | 333 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=31 的请求，VA=ffffffc009483eb0 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 237950233911 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | dyn_inst_seq=31 的请求，VA=ffffffc009483eb0 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 237950235243 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 31 | — | 91d75eb0 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | dyn_inst_seq=31 的请求 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 8 | 7 | 6 | 237950235243 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | 91d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=91d75eb0 的访问，request_id=31 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 237950235243 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 31 | 31 | — | 91d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=91d75eb0 的访问，request_id=31 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 10 | 9 | 8 | 237950235243 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75eb0 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=91d75eb0，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 11 | 10 | 9 | 237950235576 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=91d75e80 的访问，request_id=31 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 11 | 10 | 237950235576 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 31 | 31 | — | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=91d75e80 的访问，request_id=31 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 13 | 12 | 11 | 237950235576 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=91d75e80，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 64 | 12 | 237950294517 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=91d75e80，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 15 | 65 | 64 | 237950294517 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 31 | 31 | — | 91d75e80 | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=91d75e80 | pa=91d75e80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 16 | 66 | 65 | 237950294517 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=91d75e80，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 67 | 66 | 237950295183 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=91d75e80，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 18 | 68 | 67 | 237950295183 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 31 | 31 | — | 91d75e80 | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=91d75e80 | pa=91d75e80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 19 | 69 | 68 | 237950295183 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=91d75e80，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 20 | 73 | 69 | 237950295516 | 333 | resp | L3 | response path | 1 | seq_primary | 31 | 31 | 91d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=31 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 21 | 74 | 73 | 237950295516 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 31 | 31 | 91d75eb0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 22 | 75 | 74 | 237950295516 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | sq_idx=1 的 store 完成 | store 完成状态 | 错误 store 效果被标记为完成，等待提交 |
| 23 | 293 | 75 | 237951302175 | 1006659 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 454 条原始事件（report 444 非 consumer；consumer 10）；主链只取 event 293 的 23 个单祖先。旁支事实：

- `request_fork` 53 条，主链 0 条；从主链节点 12（15 条）与 74（38 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=91d75000`、`shared_size=1000`；new_request_id 如 32/34/35/37/38/40/…。它们不进入 293 的祖先。
- 旁支 `taint_reg` 54 条，主链 1 条（74）；`resp` 53 条，主链 1 条（73）；`lq_complete` 4 条，主链 0 条（store 路径，主链用 sq_complete 75）。
- `squash_masked` 1 条：event 319（tick=237951547263，VA=ffffffc009483e40，L4，contained=1，squash_replay），晚于 L5 且不在祖先。
- `chain_end` 是 event 390（tick=238882039506，errant_commit_seen），只是流收口。
- consumer 10 条摘要不在主链。
- 影响：旁支与晚到 squash 不覆盖 event 293；终局仍 full/L5。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 293（errant_commit，tick=237951302175）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=10，suppressed=46，logical_total=56，issues=[]）。
- count_contradiction：454−444=10（consumer 摘要），已对账。
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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/prop_evt.txt.gz` | SHA-256 `bce2b4519a0ff6b4de29793ee7bcc6bb36a17632a16cb53050ccbc273a135526`；16765 bytes；mtime `2026-10-27T16:15:57+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/prop_trace.csv.gz` | SHA-256 `ce987558c8862a8841aae67fb3530f0ead38443365fdd478a07836aefcce0daa`；4588 bytes；mtime `2026-10-27T16:15:57+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/chain_report.json` | SHA-256 `9d5e1ae477ceec8ef6c8d4ad225302f4463de40e76d71fb9e694b0a7ecb5d494`；10701 bytes；mtime `2026-10-27T16:15:58+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/run.out` | SHA-256 `6f0f4df61045d7fe667409b9be7fbf53757656860e14f9658a2c963437e16d41`；2299 bytes；mtime `2026-10-27T16:15:58+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/run.err` | SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`；1726 bytes；mtime `2026-10-27T16:15:58+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/stats.txt` | SHA-256 `02f59dea9d110e964ce3a6f9ce92811be79da318020b1f9d7367d7455abc96b2`；381642 bytes；mtime `2026-10-27T16:15:57+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/manifest.json` | SHA-256 `233944c091b3ee48965623449ead0e98b4ca4ba12ef98d87caf2f9b08f541f1d`；1438 bytes；mtime `2026-10-27T16:15:59+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3 --cells T10-F0-W1 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/armtlb_injections.log` | SHA-256 `3aff18f2503c31726e487b942e80f829eae99f5c147abd67850328494d6ab70b`；196 bytes；mtime `2026-10-27T16:15:50+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/board.workload.dmesg` | SHA-256 `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b`；13938 bytes；mtime `2026-10-27T16:15:57+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/board.terminal` | SHA-256 `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db`；1839 bytes；mtime `2026-10-27T16:15:57+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/config.ini` | SHA-256 `f56756efc2c2353564e4db4f68361db88b818d40286c5951551089469fd153af`；97179 bytes；mtime `2026-10-27T16:15:41+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3/config.json` | SHA-256 `d20acd307fc80bafbbcc97737dc896892476d341c0ae3153adb09f437576cea0`；277160 bytes；mtime `2026-10-27T16:15:41+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3/T10-F0-W1/seed3`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `R6-AUTHORITATIVE-EVIDENCE.md` 未列出本 seed 的其它副本；权威目录唯一。

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
