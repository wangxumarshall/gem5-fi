# T10-F2-W1 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F2-W1`；seed：`1`；sample_run_id：`s1`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T10-F2-W1 --prop_sample_run_id s1`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/manifest.json`（SHA-256 `24598850c17d49d5e4c4ee27c6995ff918b9c758df08753db89a119f7c28c938`；1438 bytes；mtime `2026-10-27T13:12:44+0800`；该 manifest 的 seed 字段为 `1`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；400639 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **7703** 条；`chain_report.event_count`=**6121**（不含 consumer 事件），差值为 consumer 摘要数 1582
- fault_id 数量：**5**（注入日志共 6 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F2-W1 seed1 自己的流。代表故障 fault_id=1，终局 event 26（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,9,10,14,15,16,17,18,19,20,21,22,26（21 个事件）。`path_event_ids=[0,1,2,4,22,26]` 只是层锚点。tick 单调不减；0–4、5–7、8–10、14–16、17–19、20–22 分别同 tick。

### 2.1 故障注入前的正常状态

**load**：event 4 `lq_read`（lq_idx=44911），dyn/request=`415526`，VA=`0xffffff8001362708`（内核高地址）。命中项 `vpn=ffffff8001362`、`asid=206`、`valid=1`、`global=1`、`pfn=81362`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81362708`；way=-1（未记录）、entry_index=13，偏移 0x708。正常 PFN=0x81362、正常 PA=0x81362708。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`238085259417`，`field=bit_flip`，`before=81362`、`after=85362`，VA=`0xffffff8001362708`，`request_id=415526`，`corr=origin`。注入日志：`old_pfn 0x81362 → new_pfn 0x85362, Mask: 0x4000`。0x81362 XOR 0x4000 = 0x85362，即 bit 14 从 0 变 1；偏移 0x708 不变，PA 81362708→85362708，effective 变化为真。VPN/ASID/权限/页大小未变；bit_flip 单 bit 翻转。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 81362→85362（entry_index=13，way=-1）；event 2 `tlb_pfn` 记录 `state_before=81362708`、`state_after=85362708`、`pa=85362708`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=81362708`、`after=85362708`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit14 翻转后的 PPN 仍是合法编码，权限/有效位/页大小未变。TLB 交付 request_id=415526、PA=0x85362708 的 load。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `lq_read`（lq_idx=44911）读取错误 PA 的 load；本 seed 没有 lsq_push/sq_* 事件，记录的是 LQ 读取阶段。输入是 TLB 的 PA=85362708；输出是 request_id=415526 的 cache 访问。

### 2.5 错误如何经过 cache 和 MSHR

event 5 `cache_access`（pa=85362708）→event 6 `cache_return field=miss`→event 7 `mshr_alloc`（mshr_id=1，line 85362708）；event 8 访问同页 `pa=85362700`→event 9 miss→event 10 `mshr_alloc`（mshr_id=2，line 85362700）。event 14 `mshr_fill`（fill_id=1）→15 `cache_fill`→16 `mshr_free`；event 17 `mshr_fill`（mshr 0/fill 2）→18 `cache_fill`→19 `mshr_free`。错误行同属 0x85362 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列。cache_access 无 hit/miss 字段，miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 20 `resp`（parent=19，tick=`238085319690`）交付 request_id=415526 的响应；event 21 `lq_complete`（parent=20，lq_idx=44911）完成；event 22 `taint_reg`（parent=21，`arch_reg=4`、`phys_reg=42`、VA=`85362708`、clean→tainted、corr=seq_primary）。`taint_reg` 是存储→CPU 边界，event 26 直接以它为 parent 提交。

### 2.7 最终传播终局

终局：event 26，`errant_commit`，`parent_event_id=22`，tick=`238085320689`，`dyn_inst_seq=415526`（与 load 相同），`commit_seq=293614`，`pc=ffffffc0087b27ac`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 5483（tick=`1678908255489`，errant_commit_seen），只是流收口；本 seed 的 11 条 L4 `squash_masked` 都在 26 的祖先之外（最早 event 258，VA=ffffff8001362708，tick=238085615727，晚于 L5）。

为什么没有被提前消除：event 26 的祖先上没有 squash；event 258 起是后续 load 的 replay。为什么架构可见：`errant_commit` 越过提交边界。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 26，tick=`238085320689`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。run.out：`CHAOS_DETECT: layer=None contained=0 tick=238085320689 ptag=1 reason=errant_commit`、`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；run.err：`warn: Kernel oops in guest`。
- 注入 tick=`238085259417`，终局 tick=`238085320689`，延迟 **61272 ticks**。
- 因果链：L5 → guest kernel oops → Crash。11 条 L4 squash 与 fault2–5 不能改写 event 26；没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffff8001362708，entry=13，PFN=81362 | bit14 翻转→85362 | request_id=415526，PA=85362708 | 错误 PPN 进入地址 |
| LQ | load lq_idx=44911 | lq_read 接受错误 PA | cache 请求 | 错误地址被 LQ 接受 |
| L1D cache | PA=85362708 / line 85362700 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 85362708/85362700 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response / LQ complete | request_id=415526 | resp→lq_complete | 可交付污染值 | 回到处理器 |
| register file（taint） | load 数据 | clean→tainted（x4/42） | 被污染寄存器 | 存储→CPU 边界 |
| commit/ROB | dyn 415526 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T10-F2-W1 seed1 在 tick 238085259417 把 VA=ffffff8001362708 的 PPN bit14 翻转（0x81362→0x85362，mask 0x4000），错误 PA=85362708 经 LQ→L1D/MSHR→resp/lq_complete（20/21）进入 x4/phys42（22），event 26 真实错误提交；运行结局 Crash，11 条 L4 squash 与 fault2–5 是旁支。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 5 条 hit；`CHAOS_LSU_TRIGGER` 为 `attempted=560166 eligible=560166 injected=5`；`stats.txt` numFaultsInjected=5；`chain_report` faults=5。四方一致。fault1 的 PPN 被 event 1/2/3 读取、event 4/5 消费，activated 为真；fault2–5 中 fault2/fault4 到 L4 contained，fault3/fault5 到 L4-then-unknown。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x4000 翻转 bit14，错误 PA=85362708 经 LQ/cache/MSHR；不是 data/permission/control-state/timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=238085259417）**：错误 PA=85362708 交付 LSU；之后只有 squash/replay 可撤销，而 26 的祖先上没有。event 22 的 taint_reg（x4/phys42）是寄存器层点；event 26 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；L1D/MSHR 无地址正确性检查；本 seed 有 11 条 L4 `squash_masked`，例如 event 258（VA=ffffff8001362708，tick=238085615727）、279、577、598…，均在 event 26 之后/其它请求上。RAS 对后续 load 有效，但没有覆盖 event 26。检测盲区：PPN bit14 翻转仍合法。fault2 是一个值得注意的旁支：event 2026 的 page_size=200000（2 MiB），PFN 0x404→0x4，mask 0x400，effective PA 0x809a434d→0x9a434d；它被 event 2141 的 L4 含住，不属于 fault1。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 26）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类 Crash。11 条 L4 含住与 fault2–5 不能改写 event 26；silent-error 不能证明也不能排除。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 tick=238085259417、VA=ffffff8001362708、mask=0x4000、PFN 81362→85362、终局 26、Crash、5 个 fault；seed2 是 238083182163、VA=ffffffc009483960、mask=0x1、PFN 81d75→81d74、权威终局 L4 含住 68、Crash、4 个 fault；seed3 是 238095582084、VA=ffffffc009483950、mask=0x4000、PFN 81d75→85d75、终局 97、Crash、3 个 fault。三者地址/mask/终局类型不同；本文件不把 seed2 的 68 或 seed3 的 97 写进 seed1。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）的终局见证 `parent_event_id` 单祖先重建。seed2 的终局见证采用权威口径 event 68（真实 L4 含住），不是报告 `path_event_ids` 尾部的 1797；`path_event_ids` 只作层锚点。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 85362 | 81362 | 85362 | 0x4000 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81362→85362 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 238085259417 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 85362 | 81362 | 85362 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708 | — | — | — | — | VA=ffffff8001362708 的命中查找，request_id=415526 | 命中表项返回 pfn=85362 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 238085259417 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | 81362 | 85362 | 81362 | 85362 | — | 81362708 | 85362708 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=85362708（pfn=85362） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 238085259417 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | — | — | 81362708 | 85362708 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=85362708，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 238085259417 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=415526 的请求，VA=ffffff8001362708 | request_id=415526 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 238085259417 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85362708 的访问，request_id=415526 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 7 | 6 | 5 | 238085259417 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 415526 | 415526 | — | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85362708 的访问，request_id=415526 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 238085259417 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362708 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=85362708，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 9 | 8 | 7 | 238085259750 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85362700 的访问，request_id=415526 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 10 | 9 | 8 | 238085259750 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 415526 | 415526 | — | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=85362700 的访问，request_id=415526 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 238085259750 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=85362700，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 12 | 14 | 10 | 238085318691 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=85362700，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 15 | 14 | 238085318691 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 415526 | 415526 | — | 85362700 | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=85362700 | pa=85362700 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 14 | 16 | 15 | 238085318691 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=85362700，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 15 | 17 | 16 | 238085319357 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=85362700，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 18 | 17 | 238085319357 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 415526 | 415526 | — | 85362700 | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=85362700 | pa=85362700 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 17 | 19 | 18 | 238085319357 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=85362700，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 18 | 20 | 19 | 238085319690 | 333 | resp | L3 | response path | 1 | seq_primary | 415526 | 415526 | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=415526 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 19 | 21 | 20 | 238085319690 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=415526 的响应 | load 完成（lq_idx=44911） | 错误值被标记为可交付，进入寄存器写回 |
| 20 | 22 | 21 | 238085319690 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 415526 | 415526 | 85362708 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=4，phys_reg=42） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 26 | 22 | 238085320689 | 999 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 415526 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 7703 条原始事件（report 6121 非 consumer；consumer 1582）；主链只取 event 26 的 21 个单祖先。旁支事实：

- `request_fork` 296 条，主链 0 条；从主链节点 10（1 条）与 22（295 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=85362000`、`shared_size=1000`；new_request_id 如 415576/415689/415692/…。它们不进入 26 的祖先。
- 旁支 `taint_reg` 273 条，主链 1 条（22）；`resp` 273 条，主链 1 条（20）；`lq_complete` 248 条，主链 1 条（21）；`squash_masked` 11 条，主链 0 条。
- 11 条 L4 squash 均在 event 26 之后/其它 VA，例如 event 258（VA=ffffff8001362708，tick=238085615727）、279（同 VA）、577/598 等；不能把 event 26 说成含住。
- `chain_end`：fault1 5483（tick=1678908255489，L5 errant_commit_seen）；fault2 5484（L4 detected_contained）；fault3 5485（run_end）；fault4 5486（L4 detected_contained）；fault5 5487（L4 store_discarded_not_retired）。
- **其它 fault**：fault2 event 2026（VA=ffffffc0089a434d，2 MiB 页，PFN 0x404→0x4，mask 0x400，contained at 2141）；fault3 event 2208（VA=ffffffc008c07758，PFN 80c07→80c06，mask 0x1，L4-then-unknown）；fault4 event 4109（VA=ffffffc008c79824，PFN 80c79→80c7d，mask 0x4，contained at 4210）；fault5 event 5441（VA=ffffffc008c730e0，PFN 80c73→80c33，mask 0x40，L4-then-unknown）。它们都是 F2 的后续注入，不并入 fault1。
- consumer 1582 条摘要不在主链。
- 影响：旁支与 11 次 L4 响应说明错误页持续被访问；但 event 26 未被覆盖，终局 full/L5。

## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 26（errant_commit，tick=238085320689）。
- run outcome：`Crash`（oracle=Crash，exit=0）；guest kernel oops。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=1582，suppressed=1100489，logical_total=1102071，issues=[]）。
- count_contradiction：7703−6121=1582（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL OOPS 一致；checker full/L5 与报告一致；fault2–5 不改变 fault1。
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
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/prop_evt.txt.gz` | SHA-256 `60728ff9263a073d0b6376295ed1bc3e7d96d08e79f60c8fd6234ff7e8ec2da0`；279114 bytes；mtime `2026-10-27T13:12:41+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/prop_trace.csv.gz` | SHA-256 `ae00cc242d3732d46ced098cb0648118b774c85cf6c01208956a80a55a025046`；74990 bytes；mtime `2026-10-27T13:12:41+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/chain_report.json` | SHA-256 `fd4f201a31020d0af88169e285026596a5e483dadde5aa9e53b535f546219653`；1375558 bytes；mtime `2026-10-27T13:12:43+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/run.out` | SHA-256 `11aa1ed71f05b10361c933805d70e655119c02f2394e85d3a8c7bcf184deceab`；10566 bytes；mtime `2026-10-27T13:12:42+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/run.err` | SHA-256 `672b40ab5f50c462f0243e22e65c05c2d3938b0d990d0753e0b60674d2a14f27`；1900 bytes；mtime `2026-10-27T13:12:42+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/stats.txt` | SHA-256 `497232bff119b8659f7401c7efb2fd2214f8a2a5e7a620cb28a69ed153c771fc`；400639 bytes；mtime `2026-10-27T13:12:42+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/manifest.json` | SHA-256 `24598850c17d49d5e4c4ee27c6995ff918b9c758df08753db89a119f7c28c938`；1438 bytes；mtime `2026-10-27T13:12:44+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1 --cells T10-F2-W1 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/armtlb_injections.log` | SHA-256 `3ed261cf1ec6093e5d9daebd03905f5165d81c9c080280b6f9e2c83a48d5981b`；1158 bytes；mtime `2026-10-27T13:12:41+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/board.workload.dmesg` | SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；0 bytes；mtime `2026-10-27T13:12:41+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/board.terminal` | SHA-256 `b00fe382315d7ae69a9774681987e04e870793e5315b286d02f151ef0543aad3`；1090 bytes；mtime `2026-10-27T13:12:16+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/config.ini` | SHA-256 `053e4c527158157be9088437f1cb8571922430266a4a1bca7c0bfac18e18b1d9`；97178 bytes；mtime `2026-10-27T13:11:58+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1/config.json` | SHA-256 `1816d9f516d63de53e6f0714367d87799b724c354f2465b5ca932b10b9f8df6c`；277159 bytes；mtime `2026-10-27T13:11:58+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s1/T10-F2-W1/seed1`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_n8_T10-F2-W1_s1.sha8a229009/T10-F2-W1/seed1` — **OLD_BINARY_REFERENCE**（manifest binary 8a229009c933a6dc…，不是权威 20fda6994ee257e6…）

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
