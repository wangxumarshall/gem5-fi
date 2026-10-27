# T10-F0-W1 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F0-W1`；seed：`2`；sample_run_id：`s2`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 2 --chaos_propagation --prop_run_id T10-F0-W1 --prop_sample_run_id s2`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/manifest.json`（SHA-256 `b54954004584f1ba115dafe63a3f8520706326f08455c88901319c2b1f656b4f`；1438 bytes；mtime `2026-10-27T14:46:52+0800`；该 manifest 的 seed 字段为 `2`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；381972 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **443** 条；`chain_report.event_count`=**433**（不含 consumer 事件），差值为 consumer 摘要数 10
- fault_id 数量：**1**（F0 每次运行只注入 1 次；注入日志只有 1 条命中记录）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F0-W1 seed2 自己的流。终局 event 283（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,82,83,84,85,86,87,88,89,283（18 个事件）。`path_event_ids=[0,1,2,3,89,283]` 只是层锚点。tick 单调不减；0–2、3–5、6–8、82–84、85–87、88–89 分别同 tick。

### 2.1 故障注入前的正常状态

注入点的 `dyn_inst_seq=0`、`request_id=0`，这是本 seed 的特殊记录方式：注入发生时 trace 尚未绑定到具体的动态指令/请求；到 event 3 的 cache_access 才出现 `dyn_inst_seq=32`、`request_id=32`。被注入的 VA 是 `0xffffffc009483eb8`；命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75eb8`；way=-1（未记录）、entry_index=0，偏移 0xeb8。正常 PFN=0x81d75、正常 PA=0x81d75eb8。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`237950233911`，`field=bit_flip`，`before=81d75`、`after=81975`，VA=`0xffffffc009483eb8`，`corr=origin`。注入日志：`old_pfn 0x81d75 → new_pfn 0x81975, Mask: 0x400, effective: 1`。0x81d75 XOR 0x400 = 0x81975，即 bit 10 从 0 变 1；页内偏移 0xeb8 不变，PA 81d75eb8→81975eb8，effective 变化为真。没有改动 VPN/ASID/权限/页大小；这是 bit_flip 模型的单 bit 翻转，不是整页替换。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 81d75→81975（entry_index=0，way=-1）；event 2 `tlb_pfn` 记录 `state_before=81d75eb8`、`state_after=81975eb8`、`pa=81975eb8`，`corr=addr_fallback`。**本 seed 的流没有 `tlb_translate_result` 事件**：`chain_report` 的 kind 计数里也没有该 kind。因此 2.3 的 `tlb_translate_result`、`effective_pa_changed`、`contained`、`detection_layer` 字段只能记 **N/A**；原因不是丢事件，而是这个 seed 的翻译出口没有被 trace 记录。可确定的是：event 2 已把错误 PFN 拼成 PA 81975eb8，event 3 的 cache_access 立即使用该 PA，因此错误地址确实离开了 TLB 进入 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

**N/A**。本 seed 的主链上没有 `lsq_push`、`lq_read`、`sq_execute`、`sq_writeback`、`sq_complete` 或 `mem_req`/`lsq_sendfrag`：event 2（tlb_pfn）的直接 child 是 event 3 `cache_access`，动态指令序号从 0 变为 32。原始流没有记录该访问在 LQ/SQ 中的入队/读取阶段，因此不能用其它 seed 的 LQ/SQ 字段补写；只能说错误 PA 在 event 3 已被 cache 访问消费。

### 2.5 错误如何经过 cache 和 MSHR

event 3 `cache_access`（pa=81975eb8）→event 4 `cache_return field=miss`→event 5 `mshr_alloc`（mshr_id=1，line 81975eb8）；event 6 `cache_access`（pa=81975e80）→event 7 miss→event 8 `mshr_alloc`（mshr_id=2，line 81975e80）。event 82 `mshr_fill`（parent=8，fill_id=3）→83 `cache_fill`（pa=81975e80）→84 `mshr_free`；event 85 `mshr_fill`（mshr 0/fill 4）→86 `cache_fill`→87 `mshr_free`。错误行属于被翻转 PPN 的 0x81975 页，`corr=addr_fallback`；两次 fill/free 是 MSHR 既有序列，不是第二次注入。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 88 `resp`（parent=87，tick=`237950341470`）交付 request_id=32 的响应；event 89 `taint_reg`（parent=88）把 clean→tainted，VA=`81975eb8`，`corr=addr_fallback`；原始事件没有 arch_reg/phys_reg，因此不编造寄存器号。**本 seed 没有 `lq_complete` 事件**（kind 计数为 0 于主链；总 lq_complete 只有 4 条且在旁支），所以 load 完成阶段是 N/A；`taint_reg` 仍是存储→CPU 的边界，event 283 直接以它为 parent。

### 2.7 最终传播终局

终局：event 283，`errant_commit`，`parent_event_id=89`，tick=`237951341802`，`dyn_inst_seq=391`，`commit_seq=161`，`pc=ffffffc0087b1000`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 380（tick=`238882385160`，errant_commit_seen），只是流收口；本 seed 的 squash_masked 是 event 309（tick=`237951586890`，VA=ffffffc009483e40，L4，contained=1），晚于 L5 且不在祖先上。

为什么没有被提前消除：event 283 的祖先上没有 squash/replay/contained；错误值从 taint_reg 89 直接到提交。为什么架构可见：`errant_commit` 越过提交边界。dyn 不一致（taint 89 的 dyn=32，终局 dyn=391）同样用 parent/corr 约定解释：parent=89 是污染源状态，corr=taint_prop 指向后续消费者；消费者 fork 在第 5 章。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 283，tick=`237951341802`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=237951341802 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`237950233911`，终局 tick=`237951341802`，延迟 **1107891 ticks**。
- 因果链：L5 → guest kernel oops → Crash。event 309 的晚到 squash 与 chain_end 380 都不能改写 283。没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483eb8，entry=0，PFN=81d75 | bit10 翻转→81975 | PA=81975eb8（tlb_pfn） | 错误 PPN 进入地址 |
| LQ/SQ/LSQ | N/A | N/A | N/A | 原始流未记录该访问的队列阶段；不能借用其它 seed 补写 |
| L1D cache | PA=81975eb8 / line 81975e80 | access→miss→fill | miss/fill | 错误物理行进入 L1D |
| MSHR | line 81975eb8/81975e80 | alloc(1/2)→fill(3/4)→free | 响应 | 错误行完成生命周期 |
| response | request_id=32 | resp 交付 | 可交付污染值 | 回到处理器 |
| register file（taint） | 响应数据 | clean→tainted（arch/phys 未记录） | 被标记状态 | 存储→CPU 边界 |
| commit/ROB | dyn 391 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F0-W1 seed2 在 tick 237950233911 把 VA=ffffffc009483eb8 的 PPN bit10 翻转（0x81d75→0x81975，mask 0x400），错误 PA=81975eb8 直接进入 cache/MSHR（event 3–87），resp/taint_reg（88/89）后 event 283 真实错误提交；本 seed 没有 tlb_translate_result 与 LQ/SQ 事件，这两处按 N/A 处理，运行结局 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；`CHAOS_LSU_TRIGGER` 为 `attempted=150160 eligible=2 injected=1`；`stats.txt` numFaultsInjected=1；`chain_report` faults=1。四方一致。event 1/2 读取错误 PPN，event 3 的 cache_access 消费错误 PA，activated 为真。原始事件 443 条，report event_count=433（10 条 consumer 摘要），已对账。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x400 翻转 bit10，错误 PA=81975eb8 被 cache/MSHR 使用；不是 data 位翻转、permission、control-state 或 timing。

### 3.3 首个不可逆传播点

本 seed 没有 `tlb_translate_result`，因此不能用 event 3 作为翻译出口；**最早不可逆点是 event 2（`tlb_pfn`，tick=237950233911）**——它在 trace 中把错误 PPN 拼成 PA=81975eb8，紧接着 event 3 的 cache_access 已消费该 PA。从这一刻起错误地址离开 TLB 域；event 89 的 taint_reg 是寄存器层点；event 283 是架构层点。这个替换点与其它 seed 的 event 3 不同，已如实标注 N/A/差异，不硬套。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；cache/MSHR 无地址正确性检查；本 seed 有 1 条 L4 `squash_masked`（event 309，tick=237951586890，VA=ffffffc009483e40，contained=1，squash_replay），晚于 L5 且不在祖先。检测盲区：PPN bit 翻转仍落在合法编码区间，权限/有效位检查无法发现。没有 tlb_translate_result 也意味着 trace 没有在该出口记录 contained 字段，不能把缺失当成“含住”。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 283）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。silent-error 可能存在于提交后到 oops 的窗口，但没有外部数据错误证据。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed2 注入 tick=237950233911、VA=ffffffc009483eb8、mask=0x400、PFN 81d75→81975、终局 283、Crash，且没有 tlb_translate_result 与 LQ/SQ 事件；seed1 是 237950940537/...3fa8/mask 0x20000/event 118；seed3 是 237950233578/...3eb0/mask 0x10000/event 293。三者的 mask/地址/事件集合不同；本文件只用 seed2 自己的字段，不把 seed1/3 的 translate_result 或 LQ/SQ 补进 seed2。

## 4. 完整主链事件表

> 主链按终局 `errant_commit` 的 `parent_event_id` 单祖先重建；`path_event_ids` 只作层锚点，不作为完整链。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | — | inj | L0 | CHAOSArmTLB | 1 | origin | — | — | ffffffc009483eb8 | — | — | — | 81d75 | 81975 | 81d75 | 81975 | 0x400 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→81975 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 237950233911 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | — | — | — | 81d75 | 81975 | 81d75 | 81975 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81975;ap=0;mtype=2;page_size=1000;pa=81975eb8 | — | — | — | — | VA=ffffffc009483eb8 的命中查找，request_id=0 | 命中表项返回 pfn=81975 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 237950233911 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | 81975eb8 | — | — | 81d75 | 81975 | 81d75 | 81975 | — | 81d75eb8 | 81975eb8 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=81975eb8（pfn=81975） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 237950235576 | 1665 | cache_access | L3 | L1D cache | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 81975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81975eb8 的访问，request_id=32 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 5 | 4 | 3 | 237950235576 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 32 | 32 | — | 81975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81975eb8 的访问，request_id=32 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 6 | 5 | 4 | 237950235576 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975eb8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81975eb8，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 7 | 6 | 5 | 237950235909 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81975e80 的访问，request_id=32 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 237950235909 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 32 | 32 | — | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81975e80 的访问，request_id=32 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 237950235909 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81975e80，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 82 | 8 | 237950340471 | 104562 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81975e80，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 11 | 83 | 82 | 237950340471 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 32 | 32 | — | 81975e80 | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81975e80 | pa=81975e80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 12 | 84 | 83 | 237950340471 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81975e80，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 85 | 84 | 237950341137 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81975e80，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 86 | 85 | 237950341137 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 32 | 32 | — | 81975e80 | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81975e80 | pa=81975e80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 87 | 86 | 237950341137 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81975e80，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 88 | 87 | 237950341470 | 333 | resp | L3 | response path | 1 | addr_fallback | 32 | 32 | 81975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=32 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 17 | 89 | 88 | 237950341470 | 0 | taint_reg | L4 | register file (taint) | 1 | addr_fallback | 32 | 32 | 81975eb8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 18 | 283 | 89 | 237951341802 | 1000332 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 443 条原始事件（report 433 非 consumer；consumer 10）；主链只取 event 283 的 18 个单祖先。旁支事实：

- `request_fork` 52 条，主链 0 条；从主链节点 8（15 条）与 89（37 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=81975000`、`shared_size=1000`；new_request_id 如 34/35/37/38/40/…。它们不进入 283 的祖先。
- 旁支 `taint_reg` 53 条，主链 1 条（89）；`resp` 52 条，主链 1 条（88）；`lq_complete` 4 条，主链 0 条。
- `squash_masked` 1 条：event 309（tick=237951586890，VA=ffffffc009483e40，L4，contained=1，squash_replay），晚于 L5 且不在祖先。
- `chain_end` 是 event 380（tick=238882385160，errant_commit_seen），只是流收口。
- consumer 10 条摘要不在主链。
- 影响：旁支扩散与一次晚到 squash 都不能改写 event 283；由于本 seed 主链没有 LQ/SQ 与 translate_result，不能把旁支的 lq_complete 当作主链完成阶段。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 283（errant_commit，tick=237951341802）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=10，suppressed=46，logical_total=56，issues=[]）。
- count_contradiction：443−433=10（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL OOPS 一致；checker full/L5 与报告一致。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓（LQ/SQ 与 translate_result 明确 N/A） 13✓ 14✓ 15✓。
- chain_evidence_status：**PASS**
- experiment_identity_status：**WORKLOAD_IDENTITY_MISMATCH**
- overall_experiment_status：**NOT_MIBENCH_RESULT**
- verdict：**NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果）

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。

- 其它说明：，但附证据缺口说明：本 seed 的流没有 `tlb_translate_result` 与 LQ/SQ 事件，2.3/2.4 只能记 N/A；这不影响 event 283 的真实 L5。
## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/prop_evt.txt.gz` | SHA-256 `5a92c75ee16b72ad0f5b08787781f8f77713631f4d61b4fa0600dfa57869e4af`；16240 bytes；mtime `2026-10-27T14:46:50+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/prop_trace.csv.gz` | SHA-256 `2d8d106b53ae4edbadfc48ee381c57566e08cee1f7d8a204ee9d723e0754eede`；4554 bytes；mtime `2026-10-27T14:46:50+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/chain_report.json` | SHA-256 `42bb8ea5918c6799d5c55593b1a9631db9777112f7c8a36370fe94dc6b6201b6`；10661 bytes；mtime `2026-10-27T14:46:51+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.out` | SHA-256 `45dd1cbb11e8b64052d05ddc96500a1c6bf38f95e2c5e07d7ab2f3787e73b63d`；2299 bytes；mtime `2026-10-27T14:46:51+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.err` | SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`；1726 bytes；mtime `2026-10-27T14:46:51+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/stats.txt` | SHA-256 `b305018005e9d4017b9c36caadb5b96a7adec6c5fd30177a1afddaaf3c673783`；381972 bytes；mtime `2026-10-27T14:46:51+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/manifest.json` | SHA-256 `b54954004584f1ba115dafe63a3f8520706326f08455c88901319c2b1f656b4f`；1438 bytes；mtime `2026-10-27T14:46:52+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2 --cells T10-F0-W1 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/armtlb_injections.log` | SHA-256 `01f464e00985151d63ee83c297c7b4bf1df531906f8e2fd1901801d575d10546`；194 bytes；mtime `2026-10-27T14:46:44+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/board.workload.dmesg` | SHA-256 `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b`；13938 bytes；mtime `2026-10-27T14:46:50+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/board.terminal` | SHA-256 `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db`；1839 bytes；mtime `2026-10-27T14:46:50+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/config.ini` | SHA-256 `f67e777f797064401264817e52d42169e87db57320802ac48d44430c5bbc9d0a`；97179 bytes；mtime `2026-10-27T14:46:34+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/config.json` | SHA-256 `dc5da09812629808979ca3d4234e9ec7235bb88d955108830cb5836b4bcb7a8e`；277160 bytes；mtime `2026-10-27T14:46:34+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `R6-AUTHORITATIVE-EVIDENCE.md` 未列出本 seed 的其它副本；权威目录唯一。

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
