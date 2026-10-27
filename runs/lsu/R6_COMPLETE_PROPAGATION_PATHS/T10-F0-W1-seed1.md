# T10-F0-W1 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F0-W1`；seed：`1`；sample_run_id：`s1`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 1 --chaos_propagation --prop_run_id T10-F0-W1 --prop_sample_run_id s1`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/manifest.json`（SHA-256 `68afe2c0d1bb4c7c8114756cd6863c05ad7a0ef313f0c7428e7f72b285a1599b`；1438 bytes；mtime `2026-10-27T13:16:58+0800`；该 manifest 的 seed 字段为 `1`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；381972 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **248** 条；`chain_report.event_count`=**238**（不含 consumer 事件），差值为 consumer 摘要数 10
- fault_id 数量：**1**（F0 每次运行只注入 1 次；注入日志只有 1 条命中记录）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F0-W1 seed1 自己的流。终局 event 118（`errant_commit`）；沿 parent 回溯得到 22 个单祖先：0,1,2,3,4,5,6,7,8,15,16,17,30,31,32,33,34,35,39,40,41,118。`path_event_ids=[0,1,2,4,40,118]` 省略了 3、5–39、41，本章按完整祖先叙述。tick 单调不减；0–4、5–8、15–17、30–32、33–35、39–41 分别同 tick。

### 2.1 故障注入前的正常状态

被注入的是 **store**：event 4 `sq_execute`（sq_idx=32，state_before=issued），dyn/request=`301`，VA=`0xffffffc009483fa8`。注入前命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75fa8`；way=-1（trace 未记录具体 way，记 -1）、entry_index=0，偏移 0xfa8。正常 PFN=0x81d75、正常 PA=0x81d75fa8。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`237950940537`，`field=bit_flip`，`before=81d75`、`after=a1d75`，VA=`0xffffffc009483fa8`，`request_id=301`，`corr=origin`。注入日志：`old_pfn: 0x81d75, new_pfn: 0xa1d75, FaultType: bit_flip, Mask: 0x20000`。这说明故障不是整页替换，而是在 PPN 内翻转 1 个 bit：0x81d75 XOR 0x20000 = 0xa1d75，即 bit 17 从 0 变 1；`Mask` 与 XOR 结果一致，且 `effective: 1`。页内偏移 0xfa8 不变，PA 从 0x81d75fa8 变成 0xa1d75fa8，`effective_pa_changed` 为真。VPN、ASID、权限（ap=0）、页大小（4 KiB）与 global 都没有改变；因此这不是权限/页大小 fault，而是“PPN 数据位被翻转”的地址型故障。该 RunID 的 fault model 是 bit_flip（单比特翻转），mask=0x20000 正是模型要求的“PPN 内均匀翻转 1 bit”。

### 2.3 TLB 查询与地址翻译

event 1（`tlb_lookup`，parent=0）读到被翻转的命中项：pfn 81d75→a1d75，`entry_index=0`；event 2（`tlb_pfn`，parent=1）记录 `state_before=81d75fa8`、`state_after=a1d75fa8`、`pa=a1d75fa8`；event 3（`tlb_translate_result`，parent=2）记录 `effective_pa_changed`、`before=81d75fa8`、`after=a1d75fa8`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit 翻转后的 PFN 仍落在合法 PFN 编码范围内，权限/有效位/页大小都未变；TLB 没有 PPN 正确性 oracle。TLB 交给 LSU 的是 request_id=301、PA=0xa1d75fa8 的 4 KiB store。

### 2.4 错误如何进入 LQ/SQ/LSQ

store 路径：event 4 `sq_execute` 把 store 置为 issued（sq_idx=32）；event 5 `sq_writeback`（parent=4，tick=`237950941869`）以 `pa=a1d75fa8` 构造 packet，`state_after=packet_built`。输入是 TLB 的错误 PA；内部变化是 SQ 条目进入 packet 阶段；输出是错误地址的 store 请求；下一步 L1D/MSHR 按此地址处理。事件 4/5 的 request_id 为空，因为 store 以 sq_idx 标识；cache 阶段重新带 request_id=301。

### 2.5 错误如何经过 cache 和 MSHR

event 6 `cache_access`（pa=a1d75fa8）→event 7 `cache_return field=miss`→event 8 `mshr_alloc`（mshr_id=1，line a1d75fa8）；event 15 访问 `pa=a1d75f80`→event 16 miss→event 17 `mshr_alloc`（mshr_id=3，line a1d75f80）。event 30 `mshr_fill`（fill_id=1）→31 `cache_fill`（pa=a1d75f80）→32 `mshr_free`；event 33 `mshr_fill`（mshr 0/fill 2）→34 `cache_fill`→35 `mshr_free`。错误行属于同一个被翻转 PPN 的物理页，`corr=addr_fallback`；两次 fill/free 是 MSHR 既有序列，不是第二次注入。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 39 `resp`（parent=35，tick=`237951016128`）交付 request_id=301 的响应；event 40 `taint_reg`（parent=39）把 clean→tainted，VA=`a1d75fa8`，`corr=seq_primary`；原始事件没有记录 `arch_reg`/`phys_reg`，因此本文件不编造寄存器号。event 41 `sq_complete`（parent=40）把 sq_idx=32 标为 completed。`taint_reg` 是存储→CPU 边界；event 41 说明 store 已完成，等待提交。

### 2.7 最终传播终局

终局：event 118，`errant_commit`，`parent_event_id=41`，tick=`237951302175`，`dyn_inst_seq=391`，`commit_seq=161`，`pc=ffffffc0087b1000`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 215（tick=`238882168377`，`outcome=errant_commit_seen`），只是流收口，不是 L5。

为什么没有被提前消除：沿 event 118 祖先没有 squash；本 seed 唯一 `squash_masked` 是 event 144（tick=`237951547263`，VA=ffffffc009483e40，L4，contained=1，squash_replay），晚于 118 且在另一 VA/请求上。为什么架构可见：`errant_commit` 越过提交边界。dyn 不一致（注入 301，终局 391）用 trace 建模约定解释：parent=41 指向被污染 store 的完成，corr=taint_prop 指向后续消费者 dyn 391；消费者请求的 fork 分支在第 5 章，不在 118 的单祖先上。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 118，tick=`237951302175`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`237950940537`，终局 tick=`237951302175`，延迟 **361638 ticks**。
- 因果链：L5 → guest kernel oops → Crash。event 144 的晚到 squash 与 chain_end 215 都不能改写 118。没有应用级输出 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483fa8，entry=0，PFN=81d75 | bit17 翻转→a1d75 | request_id=301，PA=a1d75fa8 | 错误 PPN 进入地址 |
| SQ | store sq_idx=32 | sq_execute issued→sq_writeback packet_built→sq_complete completed | 错误 store packet | 错误地址被 SQ 接受 |
| L1D cache | PA=a1d75fa8 / line a1d75f80 | access→miss→fill | miss/fill | 错误物理行进入 L1D |
| MSHR | line a1d75fa8/a1d75f80 | alloc(1/3)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response | request_id=301 | resp 交付 | 可交付污染值 | 回到处理器 |
| register file（taint） | store 数据 | clean→tainted（arch/phys 未记录） | 被标记状态 | 存储→CPU 边界 |
| commit/ROB | dyn 391 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F0-W1 seed1 在 tick 237950940537 把 VA=ffffffc009483fa8 的 PPN bit17 翻转（0x81d75→0xa1d75，mask 0x20000），错误 PA=a1d75fa8 经 SQ（4/5）→L1D/MSHR（6–35）→resp/taint_reg/sq_complete（39–41）传播，event 118 真实错误提交；运行结局 Crash，晚到的 L4 squash 144 不改变 L5。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；`run.out` 的 `CHAOS_LSU_TRIGGER` 为 `attempted=150162 eligible=56 injected=1`；`stats.txt` 的 `numFaultsInjected=1`；`chain_report` faults=1。四方一致。event 1/2/3 读取并物化错误 PPN，event 4/5 消费错误 PA，activated 为真。原始事件 248 条，chain_report.event_count=238（不含 10 条 consumer 摘要），已对账。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x20000 翻转 bit17，错误 PA=a1d75fa8 被 cache/MSHR 使用。它不是 data 位翻转（翻转发生在 PPN 地址字段，不是内存数据字），不是 permission（ap=0 未变）、control-state 或 timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=237950940537）**：错误 PA=a1d75fa8 交付 LSU；之后只有 squash/replay 可撤销，而 118 的祖先上没有。event 40 的 `taint_reg` 是寄存器层不可逆点；event 118 是架构层不可逆点。

### 3.4 检测与掩蔽机制

TLB 的 valid/global/ap/mtype/page_size 检查全部通过；L1D/MSHR 无地址正确性检查；响应路径无可见地址校验。本 seed 有 1 条 L4 `squash_masked`（event 144，tick=237951547263，VA=ffffffc009483e40，contained=1，squash_replay），晚于 event 118 且在另一 VA；它不能把 L5 改写为含住。检测盲区：PPN 的合法位翻转不会触发权限/有效位检查。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 118）且架构可见；oracle=Crash；无应用级输出 oracle。不因 errant_commit 直接称 SDC；本 seed 归类为 Crash。silent-error 在提交后到 oops 前的窗口不能被完全排除，但没有外部数据错误证据。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

只比较事实：seed1 注入 tick=237950940537、VA=ffffffc009483fa8、mask=0x20000、PFN 81d75→a1d75、终局 118、Crash；seed2 是 237950233911、VA=ffffffc009483eb8、mask=0x400、PFN 81d75→81975、终局 283、无 tlb_translate_result、Crash；seed3 是 237950233578、VA=ffffffc009483eb0、mask=0x10000、PFN 81d75→91d75、终局 293、Crash。三者 mask/地址/延迟不同；本文件不把 seed2/3 的缺失事件或终局号写进 seed1。

## 4. 完整主链事件表

> 主链按终局 `errant_commit` 的 `parent_event_id` 单祖先重建；`path_event_ids` 只作层锚点，不作为完整链。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | a1d75 | 81d75 | a1d75 | 0x20000 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→a1d75 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 237950940537 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | a1d75 | 81d75 | a1d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8 | — | — | — | — | VA=ffffffc009483fa8 的命中查找，request_id=301 | 命中表项返回 pfn=a1d75 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 237950940537 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | a1d75fa8 | — | — | 81d75 | a1d75 | 81d75 | a1d75 | — | 81d75fa8 | a1d75fa8 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=a1d75fa8（pfn=a1d75） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 237950940537 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | a1d75fa8 | — | — | — | — | 81d75fa8 | a1d75fa8 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=a1d75fa8，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 237950940537 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | dyn_inst_seq=301 的请求，VA=ffffffc009483fa8 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 237950941869 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 301 | — | a1d75fa8 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | dyn_inst_seq=301 的请求 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 237950941869 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | a1d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=a1d75fa8 的访问，request_id=301 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 237950941869 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 301 | 301 | — | a1d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=a1d75fa8 的访问，request_id=301 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 237950941869 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75fa8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=a1d75fa8，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 15 | 8 | 237950942202 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=a1d75f80 的访问，request_id=301 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 16 | 15 | 237950942202 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 301 | 301 | — | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=a1d75f80 的访问，request_id=301 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 17 | 16 | 237950942202 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=a1d75f80，mshr_id=3 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 30 | 17 | 237951015129 | 72927 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 3 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=a1d75f80，mshr_id=3 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 31 | 30 | 237951015129 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 301 | 301 | — | a1d75f80 | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=a1d75f80 | pa=a1d75f80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 32 | 31 | 237951015129 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 3 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=a1d75f80，mshr_id=3 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 33 | 32 | 237951015795 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=a1d75f80，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 34 | 33 | 237951015795 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 301 | 301 | — | a1d75f80 | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=a1d75f80 | pa=a1d75f80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 35 | 34 | 237951015795 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=a1d75f80，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 39 | 35 | 237951016128 | 333 | resp | L3 | response path | 1 | seq_primary | 301 | 301 | a1d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=301 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 40 | 39 | 237951016128 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 301 | 301 | a1d75fa8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 41 | 40 | 237951016128 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | sq_idx=32 的 store 完成 | store 完成状态 | 错误 store 效果被标记为完成，等待提交 |
| 22 | 118 | 41 | 237951302175 | 286047 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 248 条原始事件（chain_report 238 非 consumer；consumer 10）；主链只取 event 118 的 22 个单祖先。旁支事实：

- `request_fork` 共 22 条，主链 0 条；从主链节点 8（2 条）、17（3 条）、40（17 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=a1d75000`、`shared_size=1000`；new_request_id 如 303/304/307/308/310/357/358/…。它们把错误页广播给后续请求，不进入 118 的祖先。
- 旁支 `taint_reg` 共 23 条，主链 1 条（40）；旁支 `resp` 22 条，主链 1 条（39）；`lq_complete` 4 条，主链 0 条（本 seed 是 store 路径）。
- `squash_masked` 1 条：event 144（tick=237951547263，VA=ffffffc009483e40，L4，contained=1，squash_replay），晚于 L5 且不在祖先；不能把 118 说成含住。
- `chain_end` 是 event 215（tick=238882168377，errant_commit_seen），只是流收口。
- consumer 10 条摘要不在主链。
- 影响：旁支说明错误页在后续请求上扩散、RAS 对一次后续 load 做了 squash；但 event 118 未被覆盖，终局仍 full/L5。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 118（errant_commit，tick=237951302175）。
- run outcome：`Crash`（oracle=Crash，exit=0）；guest kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=10，suppressed=46，logical_total=56，issues=[]）。
- count_contradiction：248−238=10（consumer 摘要），已对账。
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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/prop_evt.txt.gz` | SHA-256 `342e552a20f0121321a8941f90151934f87140c1b166d6061ebece5e6624a2da`；9891 bytes；mtime `2026-10-27T13:16:56+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/prop_trace.csv.gz` | SHA-256 `fb976f598270574d33754b953d2ea5eb46afa7bed532f94cdfa762aca8179794`；3256 bytes；mtime `2026-10-27T13:16:56+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/chain_report.json` | SHA-256 `71603a0b34978d0547e016780c54f121f42b73d54f4df9f0d4506d8688afc2d5`；10701 bytes；mtime `2026-10-27T13:16:56+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.out` | SHA-256 `78a3d6cd7f16dedb0598bee56cc1eb2310fe5814ec11903ea545aa930946988e`；2300 bytes；mtime `2026-10-27T13:16:56+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.err` | SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`；1726 bytes；mtime `2026-10-27T13:16:56+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/stats.txt` | SHA-256 `555ca143149b3e47c983c8bade030e9017ab69a35f19e7239af23a3db5d95296`；381972 bytes；mtime `2026-10-27T13:16:56+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/manifest.json` | SHA-256 `68afe2c0d1bb4c7c8114756cd6863c05ad7a0ef313f0c7428e7f72b285a1599b`；1438 bytes；mtime `2026-10-27T13:16:58+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1 --cells T10-F0-W1 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/armtlb_injections.log` | SHA-256 `2ace108f552e5017a64761fb7899a9daeb65f5965024c48927fb3bcde309a21d`；196 bytes；mtime `2026-10-27T13:16:48+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/board.workload.dmesg` | SHA-256 `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b`；13938 bytes；mtime `2026-10-27T13:16:56+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/board.terminal` | SHA-256 `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db`；1839 bytes；mtime `2026-10-27T13:16:56+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/config.ini` | SHA-256 `2bee3de5c77f6ab5595a28860d71b07629af8cebe719a10f6db6d8ad357ca981`；97179 bytes；mtime `2026-10-27T13:16:39+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/config.json` | SHA-256 `9e1c16a19d73999eee5a8ce31de4076b0d30986cbdfa11905e535758f4423fc1`；277160 bytes；mtime `2026-10-27T13:16:39+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_n8_T10-F0-W1_s1.sha8a229009/T10-F0-W1/seed1` — **OLD_BINARY_REFERENCE**（manifest binary 8a229009c933a6dc…，不是权威 20fda6994ee257e6…）

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
