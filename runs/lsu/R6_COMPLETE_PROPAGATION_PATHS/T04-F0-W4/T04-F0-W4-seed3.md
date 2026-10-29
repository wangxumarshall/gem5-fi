# T04-F0-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T04-F0-W4`；seed：`3`；sample_run_id：`s3`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`pfn_to_mapped_page`（故障类型：换值）。将命中项的 PPN 换成另一个当前合法、相同页大小的 PPN；VPN/ASID 保持一致；不生成任意随机位串。
- frequency tier：`F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type pfn_to_mapped_page --tlb_rng_seed 3 --chaos_propagation --prop_run_id T04-F0-W4 --prop_sample_run_id s3`
- source head：`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`
- binary source head：`N/A`（该 manifest 不记录 binary_source_head；同 run 的 source_head 见上）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/manifest.json`（SHA-256 `8c51599c7fc95522b54c4a5d7d7aa593feee9897a86d4ef89dd85eac2a877e1d`；1774 bytes；mtime `2026-10-25T19:33:33+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`0`，runroot `.done`=存在，`.exit_code`=存在）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；362834 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **65554** 条；`chain_report.event_count`=**64273**（不含 consumer 事件），差值为 consumer 摘要数 1281
- fault_id 数量：**1**（F0 每次运行只注入 1 次；注入日志只有 1 条命中记录）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T04-F0-W4 seed3 自己的事件流。终局是 event 21（`errant_commit`）；按 `parent_event_id` 回溯得到 22 个单祖先事件（0–21），全部 parent 先于 child，tick 单调不减。`path_event_ids=[0,1,2,5,20,21]` 仍是层锚点而非完整链，本章不按该数组裁剪祖先。

### 2.1 故障注入前的正常状态

本 seed 与 seed2 共享同一注入点：**load** 动态指令 `dyn_inst_seq=109`，`request_id=109`，VA=`0xffffff807fbce090`；注入前命中表项 `vpn=ffffff807fbce`、`asid=206`、`valid=1`、`global=1`、`pfn=ffbce`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=ffbce090`；way=0、entry_index=1，页内偏移 0x090。正常 PA 是 0xffbce090。

### 2.2 故障具体如何注入

event 0（`inj`，tick=`237950546931`）把 `before=ffbce` 换成 `after=81d75`，`field=pfn_to_mapped_page`，VA=`0xffffff807fbce090`，`request_id=109`，`corr=origin`；注入日志为 `Site: arm_tlb_lookup_hit`、`candidates: 1`。数值上 0xffbce→0x81d75，两个都是合法 PFN；页内偏移 0x090 不变，PA 0xffbce090→0x81d75090，`effective_pa_changed` 为真。没有 mask；这是整页替换，不是位翻转；VPN/ASID/权限/页大小合法，所以普通 page fault 与权限 fault 都不会触发。它与 T04-F0-W4 的 pfn_to_mapped_page 定义一致。

### 2.3 TLB 查询与地址翻译

event 1（`tlb_lookup`）读取命中项：pfn ffbce→81d75；event 2（`tlb_pfn`）记录 `state_before=ffbce090`、`state_after=81d75090`、`pa=81d75090`；event 3（`tlb_translate_result`）记录 `field=effective_pa_changed`、`before=ffbce090`、`after=81d75090`、`contained=0`、`outcome=NoFault`。TLB 没有识别/含住这个替换，因为两个物理页都合法且权限位未变；TLB 交给 LSU 的是 request_id=109、PA=0x81d75090 的 4 KiB load。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4（`lsq_push`，`field=load`，`lq_idx=1`，`sq_idx=-1`，`pc=ffffffc0080116d8`）把错误 PA 的 load 压入 LQ；event 5（`lq_read`）以 request_id=109 读取；随后 cache/MSHR 按错误 PA 访问。本 seed 没有 sq_* 事件，路径是 load 而不是 store。

### 2.5 错误如何经过 cache 和 MSHR

event 6 以 `pa=81d75090` 访问，event 7 `field=miss`，event 8 分配 mshr_id=1；event 9 访问 `pa=81d75080`，event 10 miss，event 11 分配 mshr_id=2；event 12 `mshr_fill`（fill_id=1）、event 13 `cache_fill`、event 14 `mshr_free`；event 15 以 mshr_id=0/fill_id=2 重填、event 16 `cache_fill`、event 17 `mshr_free`。错误行属于同一个被替换的 0x81d75 物理页，`corr=addr_fallback` 贯穿；两次 fill/free 是 MSHR 的既有状态序列，不是第二次故障。cache_access 无 hit/miss 字段，miss 由紧随的 cache_return 记录。


### 2.6 污染如何返回处理器状态

与 seed2 完全同构，但本 seed 的独立运行在 tick 上留下了不同的收口：event 18 `resp`（request_id=109）→ event 19 `lq_complete`（lq_idx=1）→ event 20 `taint_reg`（`before=clean`→`after=tainted`，`arch_reg=28`，`phys_reg=96`，`VA=81d75090`，`corr=seq_primary`）。`taint_reg` 之所以是存储→CPU 的边界，是因为它第一次把“污染”附着到架构/物理寄存器状态；event 21 随即以它为 parent 提交。原始流对这两个寄存器身份记录完整，不需要用 N/A 代替。

### 2.7 最终传播终局

终局是真实 L5：event 21，`kind=errant_commit`，`parent_event_id=20`，tick=`237950593884`，`dyn_inst_seq=109`，`commit_seq=88`，`pc=ffffffc0080116d8`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。`chain_end` 是 event 52795（tick=`356484834324`，`outcome=errant_commit_seen`），只是生命周期收口；它与 seed2 的 chain_end tick 不同，恰好说明两个 seed 是独立运行，而不是转抄。

为什么没有被提前消除：祖先链上没有 `squash_masked`/replay/contained 事件；L4 只有 event 20；错误 load 完成后直接提交。为什么架构可见：`errant_commit` 越过提交边界，错误值已成为架构状态。

### 2.8 从传播终局到系统表现

- 传播链终局：L5 `errant_commit`，event 21，tick=`237950593884`；`provable_to=L5`。
- 运行结局：**Timeout**（`oracle_outcome=Timeout`，`exit_code=0`）。`run.out` 的证据行是 `CHAOS_DETECT: layer=None contained=0 tick=237950593884 ptag=1 reason=errant_commit` 和 `CHAOS_LSU_TRIGGER: ... attempted=153324467 eligible=46 injected=1 ...`；没有 KERNEL 行，`run.err` 也没有。run 级 manifest `timeout_triggered=True`。
- 注入 tick=`237950546931`，终局 tick=`237950593884`，传播延迟 **46953 ticks**。
- 因果链：L5 已成立，但仿真在预算内没有正常终止，oracle 归为 Timeout；必须同时陈述“传播完成”和“非正常结束”。没有应用级 oracle，不能据此判断最终数据正确性。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB（CHAOSArmTLB） | VA=ffffff807fbce090，way=0/entry=1，PFN=ffbce | PFN 替换为 81d75 | request_id=109，PA=81d75090 | 错误地址进入 LSU |
| LQ | load lq_idx=1，request_id=109 | `lsq_push`/`lq_read` 接受错误 PA | 请求进入 cache | 错误地址被 LQ 接受 |
| L1D cache | PA=81d75090 / line 81d75080 | `cache_access`→miss→`cache_fill` | miss/fill | 错误行进入 L1D |
| MSHR | line 81d75080 | alloc→fill→free（mshr 1/2） | 响应 | 错误行完成 MSHR 生命周期 |
| response / LQ complete | request_id=109 | `resp`→`lq_complete` | 可交付污染值 | 回到处理器侧 |
| register file（taint） | load 数据 | clean→tainted（x28/phys 96） | 被污染寄存器 | 存储→CPU 状态边界 |
| commit/ROB | dyn 109 | 无 squash | `errant_commit`（L5） | 架构可见错误 |


**一句话总括**：T04-F0-W4 seed3 与 seed2 共享同一确定性注入 (tick 237950546931, VA ffffff807fbce090, PFN 0xffbce→0x81d75)，但它是独立运行（prop_evt SHA 不同、chain_end tick 不同）；错误 PA=81d75090 沿 LQ→L1D/MSHR→resp/lq_complete→x28/phys 96 传播，event 21 真实错误提交；终局 L5，运行结局受控 Timeout。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；`run.out` 的 `CHAOS_LSU_TRIGGER` 为 `attempted=153324467 eligible=46 injected=1`；`stats.txt` 的 `numFaultsInjected=1`；`chain_report` faults=1。三方一致。event 1/2/3 读取并物化错误 PFN，event 4/5 消费错误 PA，因此 activated 为真。原始事件 65554 条，其中 consumer 1281 条被 chain_report 以摘要计入（event_count=64273），不是丢事件。

### 3.2 故障传播类型

**地址型（wrong physical page）**。错误在 PFN 字段，错误 PA 0x81d75090 被 LQ/L1D/MSHR 使用；没有 mask，所以不是 data 位翻转；ap=0 未变，所以不是 permission；没有控制流改写。用“地址/错误物理页”分类，与 seed2 同型但独立运行。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`）**：错误 PA 在 tick=237950546931 交付 LSU，TLB 不再复核；event 20 的 `taint_reg`（x28/phys 96）是寄存器层不可逆点；event 21 的提交是架构层不可逆点。祖先链上没有 squash/replay，因此 event 3 之后没有恢复动作。

### 3.4 检测与掩蔽机制

TLB 的合法位/权限/页大小检查全部通过；cache/MSHR 无地址正确性检查；没有 ECC/地址冗余的可见记录。祖先上无 squash_masked；本 seed 的 kind 计数中 `squash_masked=0`，所以没有“晚到的含住”可以误读。检测盲区是“另一个合法映射页”无法由现有权限/有效位检查发现，错误只在提交边界暴露。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 21）且架构可见；oracle=Timeout；无应用输出 oracle，不能判定最终数据正确性。Timeout 不抹去 L5，但运行没有正常结束。按纪律不称 SDC；本 seed 的结论是“真实 L5 + 受控 Timeout”。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed3 与 seed2 共享同一注入点（同 tick/VA/PFN/候选），但 prop_evt SHA 不同、chain_end tick 不同（356484834324 vs 337969869489），是独立运行；seed1 的注入点/地址方向/终局不同。本文件不引用 seed1/seed2 的寄存器号或事件号作为 seed3 的事实。

## 4. 完整主链事件表

> 主链按终局见证的 `parent_event_id` 单祖先逐事件重建（parent 在前、child 在后）；同 tick 内按事件继承关系排列。`path_event_ids` 只作层锚点核对，不当作完整链。表中 `—` 表示该事件在原始流中无此字段，不是 0。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950546931 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | 81d75 | ffbce | 81d75 | — | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN ffbce→81d75 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 237950546931 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | 81d75 | ffbce | 81d75 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090 | — | — | — | — | VA=ffffff807fbce090 的命中查找，request_id=109 | 命中表项返回 pfn=81d75 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 237950546931 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | ffbce | 81d75 | ffbce | 81d75 | — | ffbce090 | 81d75090 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=81d75090（pfn=81d75） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 237950546931 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | — | — | ffbce090 | 81d75090 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=81d75090，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 237950547264 | 333 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=109 的请求，VA=ffffff807fbce090 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 237950547264 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=109 的请求，VA=ffffff807fbce090 | request_id=109 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 237950547264 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75090 的访问，request_id=109 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 237950547264 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 109 | 109 | — | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75090 的访问，request_id=109 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 237950547264 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75090 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81d75090，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 9 | 8 | 237950547597 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 109 | 109 | ffffff807fbce090 | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75080 的访问，request_id=109 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 237950547597 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 109 | 109 | — | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75080 的访问，request_id=109 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 11 | 10 | 237950547597 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81d75080，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 12 | 11 | 237950592219 | 44622 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81d75080，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 13 | 12 | 237950592219 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 109 | 109 | — | 81d75080 | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81d75080 | pa=81d75080 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 14 | 13 | 237950592219 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81d75080，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 15 | 14 | 237950592885 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81d75080，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 16 | 15 | 237950592885 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 109 | 109 | — | 81d75080 | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81d75080 | pa=81d75080 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 17 | 16 | 237950592885 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81d75080，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 18 | 17 | 237950593218 | 333 | resp | L3 | response path | 1 | seq_primary | 109 | 109 | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 19 | 18 | 237950593218 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 的响应 | load 完成（lq_idx=1） | 错误值被标记为可交付，进入寄存器写回 |
| 21 | 20 | 19 | 237950593218 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 109 | 109 | 81d75090 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=28，phys_reg=96） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 22 | 21 | 20 | 237950593884 | 666 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 109 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 的事件总数为 64273（非 consumer）加 1281 条 consumer 摘要；主链只有 event 21 的 22 个祖先。旁支事实：

- `request_fork`：11477 条，主链 0 条；全部从主链节点 20（taint_reg）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=81d75000`、`shared_size=1000`；new_request_id 从 168/169/171/172 等开始。它们把错误页广播给后续请求，不进入 21 的祖先。
- 旁支 `taint_reg`：11477 条；主链 1 条（event 20）。这些旁支证明污染在多个请求上传播，但没有终端提交链。
- 旁支 `lq_complete` 274 条、`resp` 11477 条；主链各有 1 条（19、18）。
- `squash_masked`：0 条，因此没有 L4 含住可误读为 L5，也没有 L5 可误读为含住。
- `chain_end`：event 52795（tick=356484834324），只作生命周期收口；它与 seed2 的 chain_end tick 不同，进一步说明两 seed 是独立运行。
- consumer 1281 条全部不在主链。
- 影响：旁支只说明错误页被后续请求继续访问；终局仍是 event 21 的真实 L5，未被任何 squash 覆盖。


## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 21（errant_commit，tick=237950593884）。
- run outcome：`Timeout`（oracle=Timeout，exit=0），无 kernel 行；受控 Timeout。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=1281，suppressed=231412627，logical_total=231413908，issues=[]）。
- count_contradiction：65554−64273=1281（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Timeout 与 run.out 无 KERNEL 行、manifest timeout=True 一致；checker full/L5 与报告一致。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- 结论：**PASS**。seed3 与 seed2 共享注入点但为独立运行；本文件的 L5、chain_end tick 与 prop_evt SHA 均取自 seed3 自己。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/prop_evt.txt.gz` | SHA-256 `850f6d6d20b21e8064d813397745d929448973cc913c48ee979be9392223d025`；2143904 bytes；mtime `2026-10-25T19:33:21+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/prop_trace.csv.gz` | SHA-256 `a7960b788bedae6a14fbe907c6795cc558e312808f37e541d23af6d4c5f835e4`；543101 bytes；mtime `2026-10-25T19:33:21+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/chain_report.json` | SHA-256 `e6cb219978b8117d779b5e3b203c7095c97575eb26bdeafcedf099198edb0701`；1133793 bytes；mtime `2026-10-25T19:33:31+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/run.out` | SHA-256 `0734bb99d055d6d719546124571cf8f30ecc560328aed62333e5dcca01761500`；2064 bytes；mtime `2026-10-25T19:33:25+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/run.err` | SHA-256 `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900`；129 bytes；mtime `2026-10-25T19:33:25+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/stats.txt` | SHA-256 `4c6134798421843fbcfaa96bb69f145ba468dbe16b5725553cfdda97df4339ed`；362834 bytes；mtime `2026-10-25T19:33:22+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/manifest.json` | SHA-256 `8c51599c7fc95522b54c4a5d7d7aa593feee9897a86d4ef89dd85eac2a877e1d`；1774 bytes；mtime `2026-10-25T19:33:33+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3 --cells T04-F0-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`；1145673848 bytes；mtime `2026-10-25T09:22:24+0800`；manifest 记录 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| source head | manifest 字段 | `f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`；binary_source_head=`N/A`；analysis_tool_head=`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/armtlb_injections.log` | SHA-256 `094b855b00e7bf402718858dcf65ead730bc2d4dc5312c05af378b06acb9ff3e`；151 bytes；mtime `2026-10-25T18:03:32+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/board.workload.dmesg` | **ABSENT** |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/board.terminal` | SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；0 bytes；mtime `2026-10-25T18:03:22+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/config.ini` | SHA-256 `f3e678eac72ba1d2771e69f4c91341bcd7dd6c18efe8f39089cc2f418224b3b8`；97185 bytes；mtime `2026-10-25T18:03:22+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3/config.json` | SHA-256 `8e592ec55740d5a07a19ec6da69a49537467b19eea00ea31149071d4d6fcaec1`；277166 bytes；mtime `2026-10-25T18:03:22+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed3`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_p1_T04-F0-W4/T04-F0-W4/seed3` — **INTERRUPTED**；本 seed 的权威目录即 `r6_c9_T04-F0-W4_s3`

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
