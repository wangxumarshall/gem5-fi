# T04-F2-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T04-F2-W4`；seed：`1`；sample_run_id：`s1`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`pfn_to_mapped_page`（故障类型：换值）。将命中项的 PPN 换成另一个当前合法、相同页大小的 PPN；VPN/ASID 保持一致；不生成任意随机位串。
- frequency tier：`F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type pfn_to_mapped_page --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T04-F2-W4 --prop_sample_run_id s1`
- source head：`fcacc958b799c635babd2834cce9da6942322d91`
- binary source head：`N/A`（该 manifest 不记录 binary_source_head；同 run 的 source_head 见上）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`fcacc958b799c635babd2834cce9da6942322d91`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/manifest.json`（SHA-256 `0f2a7cc4a83aa0e82ba3a5968c02af116a10c2f8a292e8382f4f6343fd503af5`；1775 bytes；mtime `2026-10-25T21:08:03+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`0`，runroot `.done`=存在，`.exit_code`=存在）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；392187 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **12395** 条；`chain_report.event_count`=**11184**（不含 consumer 事件），差值为 consumer 摘要数 1211
- fault_id 数量：**2**（注入日志共 3 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T04-F2-W4 seed1 自己的流。代表故障是 fault_id=1，终局 event 40（`errant_commit`）；沿 parent 回溯得到 22 个单祖先事件：0,1,2,3,4,5,6,7,14,15,16,20,21,22,23,24,25,29,30,31,32,40。`chain_report.path_event_ids=[0,1,2,4,31,40]` 省略了 3、5–30、32，本章不按它裁剪。tick 单调不减；0–4 同 tick，随后 5–7 同 tick，14–16 同 tick，20–22 同 tick，23–25 同 tick，29–32 同 tick。

### 2.1 故障注入前的正常状态

这是一条 **load**：event 4 的 `lq_read`，`dyn_inst_seq=448236`，`request_id=448236`，VA=`0xffffffc009483970`，lq_idx=49500。注入前命中项 `state_before` 为 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75970`；way=26、entry_index=21，页内偏移 0x970。正常 PFN=0x81d75、正常 PA=0x81d75970，权限/页大小/global 都正常。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`238088438901`，`fault_id=1`，`request_id=448236`，`field=pfn_to_mapped_page`，`before=81d75`、`after=ffbd3`，VA=`0xffffffc009483970`，`corr=origin`。注入日志为 `Site: arm_tlb_lookup_hit`、`old_pfn: 0x81d75, new_pfn: 0xffbd3, candidates: 30`。0x81d75（531829）→0xffbd3（1047507），仍在 20 位 PFN 内；偏移 0x970 不变，PA 0x81d75970→0xffbd3970，`effective_pa_changed` 为真。没有 mask，因为是整页换值而非位翻转；候选 30 说明注入器从多个合法映射页中选了一个，符合 pfn_to_mapped_page 的“保持 VPN/ASID/页大小/权限合法，只换物理页”口径。这个 seed 是 F2 频率档：除了 fault1，后面还有 fault2（见第 5 章），但代表故障按 escape-first 选 fault1（full）。

### 2.3 TLB 查询与地址翻译

event 1（`tlb_lookup`，parent=0）读取命中项：pfn 81d75→ffbd3，`way=26`、`entry_index=21`、`walk_id=0`；event 2（`tlb_pfn`）记录 `state_before=81d75970`、`state_after=ffbd3970`、`pa=ffbd3970`；event 3（`tlb_translate_result`）记录 `effective_pa_changed`、`before=81d75970`、`after=ffbd3970`、`contained=0`、`outcome=NoFault`。TLB 没有含住它：替换页合法、ap=0 未变、页大小 4 KiB 未变，因此权限/有效位/页大小检查都不会报错。TLB 交给 LSU 的是 request_id=448236、PA=0xffbd3970 的 load。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4（`lq_read`，parent=3，tick=`238088438901`）以 `lq_idx=49500` 读取错误 PA 的 load；本 seed 没有 `lsq_push` 或 `sq_*` 事件，说明该流记录的是 LQ 读取阶段而不是入队/store 阶段。输入是 TLB 的 PA=ffbd3970；内部变化是 load 以错误地址进入 LQ 读取；输出是 request_id=448236 的 cache 访问。下一步 L1D/MSHR 按错误 PA 查找。

### 2.5 错误如何经过 cache 和 MSHR

event 5（`cache_access`，parent=4）以 `pa=ffbd3970` 访问；event 6 的 `cache_return field=miss` 表明 miss；event 7 分配 mshr_id=1、line `ffbd3970`。event 14（`cache_access`，parent=7）访问同页 `pa=ffbd3940`，event 15 miss，event 16 分配 mshr_id=3。event 20（`mshr_fill`，parent=16）fill_id=1 填充 mshr 3，event 21 `cache_fill` 填入 `pa=ffbd3940`，event 22 `mshr_free` 释放；event 23（`mshr_fill`，parent=22）以 mshr_id=0/fill_id=2 重填，event 24 `cache_fill`，event 25 `mshr_free` 收口。错误行属于同一被替换的 0xffbd3 页，`corr=addr_fallback`；两次 fill/free 是 MSHR 的既有序列，不是两次独立故障。cache_access 无 hit/miss 字段，miss 由紧随的 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 29（`resp`，parent=25，tick=`238088499174`）交付 request_id=448236 的响应；event 30（`lq_complete`，parent=29）完成 lq_idx=49500；随后连续两个 `taint_reg`：event 31（parent=30）写 `arch_reg=19`、`phys_reg=128`，event 32（parent=31）写 `arch_reg=20`、`phys_reg=16`，两者都是 `before=clean`→`after=tainted`、VA=`ffbd3970`、`corr=seq_primary`。这说明同一个错误 load 的污染同时进入两个架构寄存器/物理寄存器；`taint_reg` 是存储→CPU 的边界，event 32 之后 event 40 直接提交。

### 2.7 最终传播终局

终局是真实 L5：event 40，`errant_commit`，`parent_event_id=32`，tick=`238088499840`，`dyn_inst_seq=448236`（与错误 load 相同），`commit_seq=324841`，`pc=ffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。它不是 chain_end：chain_end 是 event 9514（tick=`238533352542`，fault1 的 `errant_commit_seen`），另有 fault2 的 chain_end 9515（L4，`store_discarded_not_retired`）。

为什么没有被提前消除：沿 event 40 的祖先，L4 之后没有 squash；本 seed 的 55 条 `squash_masked` 全部在祖先之外（VA 多为 ...3xxx/...7xxx 等其它地址），它们对应后续请求的 replay，不覆盖这条 load。为什么架构可见：`errant_commit` 越过提交边界，错误值成为架构状态。

### 2.8 从传播终局到系统表现

- 传播终局：L5 `errant_commit` event 40，tick=`238088499840`；`provable_to=L5`。
- 运行结局：**Crash**（oracle=Crash，exit=0）。`run.out` 有 `CHAOS_DETECT: layer=None contained=0 tick=238088499840 ptag=1 reason=errant_commit`、多条 Hardware RAS `squash_replay`，最后是 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `warn: Kernel panic in simulated kernel`。
- 注入 tick=`238088438901`，终局 tick=`238088499840`，传播延迟 **60939 ticks**。
- 因果链：L5 错误提交 → guest kernel panic → Crash。注意 55 次 L4 squash 说明 RAS 对后续请求做了掩蔽，但它们不能改写 event 40 的 L5；fault2 的 L4 结局（chain_end 9515）也不改变 fault1 的 full 终局。没有应用级输出 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483970，way=26/entry=21，PFN=81d75 | PFN→ffbd3，PA 81d75970→ffbd3970 | request_id=448236，PA=ffbd3970 | 错误地址进入 LSU |
| LQ | load lq_idx=49500 | `lq_read` 接受错误 PA | cache 请求 | 错误地址被 LQ 接受 |
| L1D cache | PA=ffbd3970 / line ffbd3940 | access→miss→fill | miss/fill | 错误物理行进入 L1D |
| MSHR | line ffbd3970/ffbd3940 | alloc(1/3)→fill(1/2)→free | 响应数据 | 错误行完成 MSHR 生命周期 |
| response / LQ complete | request_id=448236 | resp→lq_complete | 可交付污染值 | 回到处理器侧 |
| register file（taint） | load 数据 | clean→tainted（x19/128、x20/16） | 两个被污染寄存器 | 存储→CPU 状态边界 |
| commit/ROB | dyn 448236 | 无 squash 覆盖 | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T04-F2-W4 seed1 在 tick 238088438901 把 VA=ffffffc009483970 的命中项 PFN 0x81d75 换成 0xffbd3，错误 PA=ffbd3970 经 LQ（4）→L1D/MSHR（5–25）→resp/lq_complete（29/30）进入 x19/phys128 与 x20/phys16（31/32），event 40 真实错误提交；其余 55 个 L4 squash 与 fault2 都是旁支，运行结局是 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

F2 是频率模型，不是“每次运行只注入 1 次”的 max_faults 模型：注入日志有 tier 汇总行加 2 条 `arm_tlb_lookup_hit`，`run.out` 的 `CHAOS_LSU_TRIGGER` 为 `attempted=182081 eligible=168990 injected=2`，`stats.txt` 的 `numFaultsInjected=2`，`chain_report` faults=2。四方对 fault 总数一致；对代表故障 fault1，event 1/2/3 读取并物化错误 PFN，event 4/5 消费，故 activated 是实证的。fault2 只到 L4（见第 5 章），不影响 fault1 的 full 终局。

### 3.2 故障传播类型

**地址型（wrong physical page）**：错误在 PFN 字段，错误 PA 0xffbd3970 被 LQ/cache/MSHR 使用。不是 data 位翻转（无 mask），不是 permission（ap=0 未变），不是 control-state，也不是 timing。响应把错误页的数据带回，但根因仍是地址翻译。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=238088438901）**：错误 PA 0xffbd3970 在此离开 TLB 并交付 LSU；之后只有 squash/replay 能撤销，而这条祖先链没有发生。event 31/32 的 `taint_reg` 把污染写入 x19/128 与 x20/16，是寄存器层不可逆点；event 40 是架构层不可逆点。

### 3.4 检测与掩蔽机制

TLB 的 valid/global/ap/mtype/page_size 检查全部通过；L1D/MSHR 无地址正确性检查；响应路径无可见地址校验。本 seed 有 55 条 `squash_masked`（L4，contained=1，squash_replay），说明 RAS 能对后续 load 做 replay，但它们都不在 event 40 的祖先上；fault2 的 chain_end 9515 是 L4 `store_discarded_not_retired`，也不改写 fault1。检测盲区仍是“合法页替换”：只有权限/有效位检查，没有正确 PFN 的冗余。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 40）且架构可见；oracle=Crash；没有应用级输出 oracle。不能因为 errant_commit 就直接叫 SDC；本 seed 归类为 Crash。silent-error 可能性在提交后到 panic 前不能被证明，也不能被排除；本文件只声明“真实 L5 + Crash + 若干 L4 旁支”。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed1 的注入点/地址/终局是 tick=238088438901、VA=ffffffc009483970、PFN 81d75→ffbd3、event 40；seed2 是 238085994681、VA=ffffff807fbce008、PFN ffbce→81362、event 42、4 个 fault；seed3 是 238100391603、VA=ffffffc009483968、PFN 81d75→81363、event 54、9 个 fault。三者都 Crash，但注入点、地址变化、fault 数、终局 event 与 taint 寄存器都不同；本文件不把 seed2/3 的 x20/39 或 chain_end tick 写进 seed1。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）终局见证的 `parent_event_id` 单祖先重建；同 tick 事件保留继承顺序。`path_event_ids` 只作层锚点，不作为完整链。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238088438901 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 448236 | 448236 | ffffffc009483970 | — | — | — | 81d75 | ffbd3 | 81d75 | ffbd3 | — | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→ffbd3 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 238088438901 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 448236 | 448236 | ffffffc009483970 | — | — | — | 81d75 | ffbd3 | 81d75 | ffbd3 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75970 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=ffbd3;ap=0;mtype=2;page_size=1000;pa=ffbd3970 | — | — | — | — | VA=ffffffc009483970 的命中查找，request_id=448236 | 命中表项返回 pfn=ffbd3 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 238088438901 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 448236 | 448236 | ffffffc009483970 | ffbd3970 | — | — | 81d75 | ffbd3 | 81d75 | ffbd3 | — | 81d75970 | ffbd3970 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=ffbd3970（pfn=ffbd3） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 238088438901 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 448236 | 448236 | ffffffc009483970 | ffbd3970 | — | — | — | — | 81d75970 | ffbd3970 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75970 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=ffbd3;ap=0;mtype=2;page_size=1000;pa=ffbd3970 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=ffbd3970，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 238088438901 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 448236 | 448236 | ffffffc009483970 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=448236 的请求，VA=ffffffc009483970 | request_id=448236 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 238088438901 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 448236 | 448236 | ffffffc009483970 | ffbd3970 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbd3970 的访问，request_id=448236 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 7 | 6 | 5 | 238088438901 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 448236 | 448236 | — | ffbd3970 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbd3970 的访问，request_id=448236 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 238088438901 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 448236 | 448236 | — | — | ffbd3970 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=ffbd3970，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 9 | 14 | 7 | 238088439234 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 448236 | 448236 | ffffffc009483970 | ffbd3940 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbd3940 的访问，request_id=448236 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 10 | 15 | 14 | 238088439234 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 448236 | 448236 | — | ffbd3940 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbd3940 的访问，request_id=448236 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 16 | 15 | 238088439234 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 448236 | 448236 | — | — | ffbd3940 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=ffbd3940，mshr_id=3 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 12 | 20 | 16 | 238088498175 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 448236 | 448236 | — | — | ffbd3940 | 3 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=ffbd3940，mshr_id=3 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 21 | 20 | 238088498175 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 448236 | 448236 | — | ffbd3940 | ffbd3940 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=ffbd3940 | pa=ffbd3940 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 14 | 22 | 21 | 238088498175 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 448236 | 448236 | — | — | ffbd3940 | 3 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=ffbd3940，mshr_id=3 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 15 | 23 | 22 | 238088498841 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 448236 | 448236 | — | — | ffbd3940 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=ffbd3940，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 24 | 23 | 238088498841 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 448236 | 448236 | — | ffbd3940 | ffbd3940 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=ffbd3940 | pa=ffbd3940 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 17 | 25 | 24 | 238088498841 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 448236 | 448236 | — | — | ffbd3940 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=ffbd3940，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 18 | 29 | 25 | 238088499174 | 333 | resp | L3 | response path | 1 | seq_primary | 448236 | 448236 | ffbd3970 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=448236 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 19 | 30 | 29 | 238088499174 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 448236 | 448236 | ffffffc009483970 | ffbd3970 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=448236 的响应 | load 完成（lq_idx=49500） | 错误值被标记为可交付，进入寄存器写回 |
| 20 | 31 | 30 | 238088499174 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 448236 | 448236 | ffbd3970 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=19，phys_reg=128） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 32 | 31 | 238088499174 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 448236 | 448236 | ffbd3970 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=20，phys_reg=16） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 22 | 40 | 32 | 238088499840 | 666 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 448236 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 12395 条事件（非 consumer 口径另计 11184；consumer 摘要 1211）；主链只取 event 40 的 22 个单祖先。旁支事实：

- `request_fork` 1487 条，主链 0 条；从主链节点 7（2 条）与 32（1485 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=ffbd3000`、`shared_size=1000`；new_request_id 如 448237/448241/448411/…。它们把错误页广播给后续请求，不进入 40 的祖先。
- 旁支 `taint_reg` 1639 条（主链 2 条：31/32）；`resp` 1398（主链 1）；`lq_complete` 482（主链 1）；`squash_masked` 55（主链 0）。
- 55 条 `squash_masked` 全部为 L4、`contained=1`、`squash_replay`，例如 event 1569（VA=ffffffc009483740）、1602（...3458）、1621（...3430）、1687（...33c0）；它们发生在 event 40 之后或其它请求上，不能把 L5 说成含住。
- `chain_end`：fault1 event 9514（tick=238533352542，L5 errant_commit_seen）；fault2 event 9515（L4，store_discarded_not_retired）。两者都不是 L5 见证。
- **另一个故障 fault2**：event 8180 注入 tick=238532810751、VA=ffffffc009483268、PFN ffbd3→81b94、candidates 29；路径 8181/8182/8184/8189 到 `taint_reg`，终局 `provable_to_L4_then_unknown`，chain_end 9515。它属于同一 seed 的 F2 第二次注入，不是 fault1 的旁支，因此不并入 Ch.2；也不影响 fault1 的 full。
- consumer 1211 条摘要全部不在主链。
- 影响：旁支说明错误页被后续请求继续访问，RAS 对其中 55 次做了 L4 squash；但 event 40 的提交没有被覆盖，终局仍是真实 L5。


## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 40（errant_commit，tick=238088499840）。
- run outcome：`Crash`（oracle=Crash，exit=0）；崩溃类型：guest kernel panic（`KERNEL PANIC under fault`）。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效（`End Simulation Statistics`）。
- conservation：`ok`（emitted=1211，suppressed=10321，logical_total=11532，issues=[]）。
- count_contradiction：原始 12395 − report 11184 = 1211，正好是 consumer 摘要；无丢事件。
- campaign/checker agreement：oracle=Crash 与 run.out 的 KERNEL PANIC 一致；checker full/L5 与报告一致；fault2 的 L4 终局不改变 fault1。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**（3 个 seed 均 full/Crash）。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- 结论：**PASS**。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/prop_evt.txt.gz` | SHA-256 `00827d400f4677d740fe9b29db7943d4d33cba2900d875eed4eabd9cc7241d09`；410718 bytes；mtime `2026-10-25T21:04:57+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/prop_trace.csv.gz` | SHA-256 `a49bed225bb7b54de5db20351aa027b725f84b2e99e489169248a3adad7deb1d`；124783 bytes；mtime `2026-10-25T21:04:57+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/chain_report.json` | SHA-256 `50ac66c6998e67bec9d111d4f7a9adde4ed9f2a78f91fd55748f28aceec140c5`；1021946 bytes；mtime `2026-10-25T21:04:59+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/run.out` | SHA-256 `9c00a2cce1514120e50efbc8ab6d922d726f27288858e15ade0a9824f60ca6ad`；7366 bytes；mtime `2026-10-25T21:04:58+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/run.err` | SHA-256 `542053f2316e00845e96acb4d0f3b335c76fdc87803a2c67dc0821aa4c8332a0`；1919 bytes；mtime `2026-10-25T21:04:58+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/stats.txt` | SHA-256 `9252638a86f5d441854a19abfa13bf6bb1bd216bdc91160e15a6db2e762c8ce8`；392187 bytes；mtime `2026-10-25T21:04:58+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/manifest.json` | SHA-256 `0f2a7cc4a83aa0e82ba3a5968c02af116a10c2f8a292e8382f4f6343fd503af5`；1775 bytes；mtime `2026-10-25T21:08:03+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3 --cells T04-F2-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`；1145673848 bytes；mtime `2026-10-25T09:22:24+0800`；manifest 记录 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| source head | manifest 字段 | `fcacc958b799c635babd2834cce9da6942322d91`；binary_source_head=`N/A`；analysis_tool_head=`fcacc958b799c635babd2834cce9da6942322d91` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/armtlb_injections.log` | SHA-256 `c9733329176951e4462e31657a26fa35154db98e16dfb10f5fca3781c310d735`；511 bytes；mtime `2026-10-25T21:04:57+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/board.workload.dmesg` | SHA-256 `f912e23c3f8472c206b98b62a2a55a5485eb1bd4c8f3aea7d4991be4abac6d19`；13101 bytes；mtime `2026-10-25T21:04:57+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/board.terminal` | SHA-256 `12dcea7e35defdadc5efa1e55dd258fd2142d0418c0e25f22949197d142dea00`；899 bytes；mtime `2026-10-25T21:04:57+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/config.ini` | SHA-256 `7b37e97a222bbf81ce1776c978df192320006b41aa6ee9abfebaa791a4a75e9a`；97184 bytes；mtime `2026-10-25T21:04:40+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1/config.json` | SHA-256 `f2ffd517e63cec4f8bdeb3afde9e40e3f40ac38b1a50b75bf8f29fb41968f38e`；277165 bytes；mtime `2026-10-25T21:04:40+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed1`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_c9_T04-F2-W4_s1/T04-F2-W4/seed1` — **EXACT_DUPLICATE**
- `runs/lsu/r6_c9_T04-F2-W4_s2/T04-F2-W4/seed1` — **EXACT_DUPLICATE**
- `runs/lsu/r6_c7_T04-F2-W4_s1/T04-F2-W4/seed1` — **OLD_BINARY_REFERENCE**（manifest binary a9b2c236…）
- `r6_c6_T04-F2-W4`、`r6_p1_T04-F2-W4`、`r6_tlb_G_T04-F2-W4`、`r6_w1_T04-F2-W4`、`r6_w1b_T04-F2-W4` — **INTERRUPTED**

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
