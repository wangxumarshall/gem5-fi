# T02-F0-W1 seed1 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `dbfd7e82…510a`）重建；其余文件只读引用。所有 event_id / tick / 地址 / 位值 / 状态只来自本 seed。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T02-F0-W1`（模型 ID `T02`，单元 `L1d-TLB`） |
| seed / sample_run_id | `1` / `s1` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**双比特** `bit_flip`（`--tlb_bits_to_change 2`、`--tlb_fault_type bit_flip`、`--tlb_probability 1.0`） |
| 故障类型 | 双比特翻转 |
| 频率 tier | 请求 `F0` / 生效 `F0` / `lookup_tier_enabled=0` |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）`（矩阵 Excel 行 47） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`（**注意**：实际 readfile 是 TLB-AliasPerm 探针，不是矩阵标签所写的 MiBench；见第 6 节的一致性说明） |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T02-F0-W1 --prop_sample_run_id s1` |
| source head | `N/A`（n8 batch manifest 无 `source_head` 字段；只有 `binary_source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest 记录） |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/manifest.json`（batch manifest，SHA-256 `aeb0ea2269ca78792bf5b308e0ffad6f2f3a00606dc21c97e883e5b09530024c`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n8 manifest 的 `exit_code` 字段为 `null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=382169 > 0`，`simTicks=932371362`，等于 `chain_end.tick(238882168377) − checkpoint(237949797015)` |
| 原始事件数 | 238（`chain_report.event_count=238`；`fault_event_count=238`） |
| fault_id 数量 | 1（`fault_id=1`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`，无 `*regrade*`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `237950940537` 之前，一条**存储**指令（`dyn_inst_seq=301`、`request_id=301`）访问 `0xffffffc009483fa8`，命中 DTLB 第 `0` 号表项（`entry_index=0`、`walk_id=0`、`way=-1`）。注入前表项：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75fa8`。4 KiB 页、偏移 `0xfa8`，正常 PA 为 `0x81d75fa8`；有效、全局、ASID=206，权限与内存类型正常。

### 2.2 故障具体如何注入

注入是 `event_id=0`（`inj`，fault_id=1，tick `237950940537`，`VA=0xffffffc009483fa8`，`dyn_inst_seq=301`）。`field=bit_flip`，`before=0x81d75`，`after=0xa3d75`。注入日志 `Mask: 0x22000` 与异或结果一致：**同时翻转 PFN 的第 13 位与第 17 位**。两个位都在 48 位 PFN 宽度内，因此都会进入有效 PA：`0x81d75 ^ 0x22000 = 0xa3d75`，偏移 `0xfa8` 不变，有效 PA 从 `0x81d75fa8` 变成 `0xa3d75fa8`，`effective_pa_changed=1`。这是最“纯粹”的双比特地址改变：没有任何高位被截断，两个翻转位都直接改变页基址。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，同 tick）记录命中查询：`state_before.pfn=81d75`、`state_after.pfn=a3d75`，`state_before.pa=81d75fa8`、`state_after.pa=a3d75fa8`；其余表项属性未动。`event_id=2`（`tlb_pfn`，parent=1）确认 `pa=a3d75fa8`、`before=81d75`、`after=a3d75`。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81d75fa8`、`after=a3d75fa8`、`contained=0`、`outcome=NoFault`。TLB 没有检测，也没有阻断。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是**存储**：`event_id=4`（`sq_execute`，parent=3）记录 `issued`、`sq_idx=32`；本 seed 的主链上没有 `lsq_push`（流中 `lsq_push` 计数为 0），入队只能由 `sq_idx=32` 在 `sq_execute`/`sq_complete` 中重复出现来确认。`event_id=5`（`sq_writeback`，parent=4，Δtick=1332）把 `pa=a3d75fa8` 装进写回包（`packet_built`）。输入是错误 PA，内部变化是 `sq_idx=32` 的发射→构包，输出是带错误地址的写回包。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=6`（`cache_access`，parent=5）以 `pa=a3d75fa8` 访问 L1D，`event_id=7`（`cache_return`）为 `miss`，`event_id=8` 分配 `mshr_id=1`（`cache_line=a3d75fa8`）。`event_id=15`（`cache_access`，parent=8，Δtick=333）访问 `pa=a3d75f80`（同一条 64B 行），`event_id=16` 仍 `miss`，`event_id=17` 分配 `mshr_id=3`（`cache_line=a3d75f80`）。随后完整记录填充：`event_id=30`（`mshr_fill`，parent=17，Δtick=72927）把 mshr 3 标为 `filled`（`fill_id=1`），`event_id=31`（`cache_fill`）以 `pa=a3d75f80` 填行，`event_id=32`（`mshr_free`）释放 mshr 3；`event_id=33`（`mshr_fill`，Δtick=666）把 `mshr_id=0` 标为 `filled`（`fill_id=2`），`event_id=34`（`cache_fill`）再次填同一行，`event_id=35`（`mshr_free`）释放 mshr 0。整个 alloc→fill→free 流程完全正常，唯一“不正常”的是行地址来自被改写的页基址 `a3d75`；cache/MSHR 没有任何手段判断这一点。

### 2.6 污染如何返回处理器状态

`event_id=39`（`resp`，parent=35，tick `237951016128`，Δtick=333）把数据送回，`va=a3d75fa8`；`event_id=40`（`taint_reg`，parent=39）记录 `before=clean`、`after=tainted`（`arch_reg`/`phys_reg` 本 seed 未记录）；`event_id=41`（`sq_complete`，parent=40）把 `sq_idx=32` 的存储标记为 `completed`。`taint_reg` 是存储→CPU 边界：此前错误只是错误地址/数据，此后它变成被标记为脏的体系结构状态。

### 2.7 最终传播终局

真实 L5 是 `event_id=118`（`errant_commit`），parent=`41`，tick `237951302175`（相对 `taint_reg` Δtick=286047），`dyn_inst_seq=391`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b1000`，`commit_seq=161`。为什么没被消除：TLB 无校验、cache 按地址正常填充、SQ/ROB 无地址一致性检查、提交前没有 squash。`chain_end`（`event_id=215`，parent=214，tick `238882168377`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口，不是 L5。

本 seed 在提交**之后**还有一条 `squash_masked`（`event_id=144`，parent=119，tick `237951547263`，`va=ffffffc009483e40`，`pa=a3d75e40`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay`）。它在 event 118 之后，按权威口径不是终局见证，不能把本 seed 改判为含住。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=161` 退休（`dyn_inst_seq=391`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `237951302175` 有 `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`，其后 `237951547263` 有 `contained=1 reason=squash_replay`，再以 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)` 结束；`run.err` 为 `Kernel oops in guest`。注入 tick `237950940537` → 终局 `237951302175`，传播时延 `361638` ticks。错误 PA 指向另一个物理页，污染提交后 guest 内核 oops，仿真以 Crash 退出；不是 Timeout。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483fa8`、命中第 0 项 | PPN `0x81d75 → 0xa3d75`（bit13、bit17 均在位域内） | PA `0x81d75fa8 → 0xa3d75fa8`，`contained=0` | 错误翻译进入流水线 |
| SQ | `sq_idx=32`、store、错误 PA | 发射→构包 | `packet_built`（`pa=a3d75fa8`） | 错误地址固化 |
| L1D | `a3d75fa8`/`a3d75f80` | 两次 miss，两次 fill | 行填充 | 按错误地址真实取数 |
| MSHR | 行 `a3d75fa8`/`a3d75f80` | alloc 1/3 → fill/fill → free | `resp`（39） | 缺失管理正常，地址合法性无检查 |
| PRF/寄存器 | 响应数据 | `clean → tainted` | 污染寄存器 | 跨入体系结构状态 |
| ROB/提交 | 污染寄存器（dyn 391） | 退休 | `errant_commit`（commit_seq=161） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end` | 生命周期收口 | 非 L5；提交后 squash 144 不影响终局 |

一句话总结：store 命中被双比特改坏的 TLB 表项（bit13/bit17 都生效），错误 PA `0xa3d75fa8` 经 `sq_idx=32` 构包后进 L1D，两次 miss 后由 MSHR 1/3 完成 fill/free，响应把寄存器标脏，最终 `dyn_inst_seq=391` 在 `commit_seq=161` 错误退休并导致内核 oops；提交后虽有一次 squash，但不能改变本 seed 的 L5 终局。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：1 条 `inj`（fault_id=1）、1 条 `arm_tlb_lookup_hit`（old `0x81d75`、new `0xa3d75`、`Mask: 0x22000`）、`stats.numFaultsInjected=1`、`run.out injected=1`；`attempted=150162`、`eligible=56`、`activated=W3-L0-layer`。坏值被实际读取：`tlb_lookup.state_after.pfn`、`tlb_pfn.after`、`sq_writeback.pa`、`cache_access.pa` 都是 `a3d75…`。激活成立。

### 3.2 故障传播类型

**地址型**：错误物理页。不是数据型（数据字未翻转）、不是 permission、不是 control-state、不是 timing、不是 wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `237950940537`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`；此前 `event_id=2` 只是存储被改写，此后错误进入执行路径，无法不重放地撤销。

### 3.4 检测与掩蔽机制

TLB 无校验；翻译层无合法性检查；L1D/MSHR 的 fill 正常完成但不判别地址；SQ/ROB 无一致性检查；提交点不校验。事后 oracle 在 `237951302175` 才报 `errant_commit`。提交后 `237951547263` 的 squash 只清理后续消费，不能撤销已提交错误；这正是观察到的盲区：**错误提交后才出现“检测/掩蔽”**。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 118），体系结构可见；运行结局 Crash（内核 oops），因此不是 SDC。SDC 需要“对外可见且未被检测到”的错误输出；本样本以 Crash 暴露。无应用级输出 oracle，无法判断数据层面最终正确性；结论只能是“已证真实错误提交 + Crash/DUE”。

### 3.6 与同 RunID 其他 seed 的关系

seed2 注入 `237950233911`（VA `…3eb8`，掩码 `0x40400`，位 10/18），seed3 `237950233578`（VA `…3eb0`，掩码 `0x10020`，位 5/16）。三个 seed 都是双比特、单 fault、`full`、Crash，且两个翻转位都在 48 位 PFN 内（不同于 W4 组的高位截断）。本 seed 是 store（`sq_idx=32`）且完整记录 fill/free；seed2 无 LQ/SQ 记录；seed3 是 store（`sq_idx=1`、`strxi_uop`、有 `lsq_push`）。本 seed 的数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=118` 经 `parent_event_id` 回溯的单祖先，共 22 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | — | inj | L0 | TLB | 1 | origin | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | a3d75 | 81d75 | a3d75 | 0x22000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 237950940537 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | a3d75 | 81d75 | a3d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a3d75;ap=0;mtype=2;page_size=1000;pa=a3d75fa8 | — | — | — | — | 命中查询 | PFN 81d75→a3d75 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 237950940537 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | a3d75fa8 | — | — | 81d75 | a3d75 | 81d75 | a3d75 | — | 81d75fa8 | a3d75fa8 | — | — | — | — | 表项当前状态 | PA 81d75fa8→a3d75fa8 | 表项存储被改写 |
| 4 | 3 | 2 | 237950940537 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | a3d75fa8 | — | — | — | — | 81d75fa8 | a3d75fa8 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a3d75;ap=0;mtype=2;page_size=1000;pa=a3d75fa8 | 0 | — | NoFault | — | 表项 PFN | PA 81d75fa8→a3d75fa8 | 首个不可逆点 |
| 5 | 4 | 3 | 237950940537 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | 错误 PA 的 store | 发射（sq_idx=32） | 进入 SQ |
| 6 | 5 | 4 | 237950941869 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 301 | — | a3d75fa8 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | sq_idx=32 | 构包 | 错误地址固化为写回包 |
| 7 | 6 | 5 | 237950941869 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | a3d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483fa8 | 访问 L1D | 按错误 PA 取数 |
| 8 | 7 | 6 | 237950941869 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | a3d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 a3d75fa8 | miss | cache 无法判别地址合法性 |
| 9 | 8 | 7 | 237950941869 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a3d75fa8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 a3d75fa8 | 分配 MSHR 1 | 错误行进入填充流水 |
| 10 | 15 | 8 | 237950942202 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | a3d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483fa8 | 访问 L1D | 按错误 PA 取数 |
| 11 | 16 | 15 | 237950942202 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | a3d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 a3d75f80 | miss | cache 无法判别地址合法性 |
| 12 | 17 | 16 | 237950942202 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a3d75f80 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 a3d75f80 | 分配 MSHR 3 | 错误行进入填充流水 |
| 13 | 30 | 17 | 237951015129 | 72927 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a3d75f80 | 3 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 3 填充（fill_id=1） | 错误行取回 |
| 14 | 31 | 30 | 237951015129 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | a3d75f80 | a3d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 15 | 32 | 31 | 237951015129 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a3d75f80 | 3 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 3 | 缺失处理结束 |
| 16 | 33 | 32 | 237951015795 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a3d75f80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 0 填充（fill_id=2） | 错误行取回 |
| 17 | 34 | 33 | 237951015795 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | a3d75f80 | a3d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 18 | 35 | 34 | 237951015795 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a3d75f80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 0 | 缺失处理结束 |
| 19 | 39 | 35 | 237951016128 | 333 | resp | L3 | L1D | 1 | seq_primary | 301 | 301 | a3d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 20 | 40 | 39 | 237951016128 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 301 | 301 | a3d75fa8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 21 | 41 | 40 | 237951016128 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | 污染响应 | 存储完成（sq_idx=32） | 错误存储正式完成 |
| 22 | 118 | 41 | 237951302175 | 286047 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 391） | 错误退休（commit_seq=161） | 真实 L5 |

折叠说明：61 个 `consumer`（event 119–214，tick `237951302175..237964973157`）全在终局之后，不在 event 118 的祖先上，故无 consumer 行可折叠；提交后的 `squash_masked`（144）也不在主链上，见 Ch.5。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（22 条）**：全部 `L3/addr_fallback_broadcast`，`shared_addr=a3d75000`、`shared_size=1000`。最早 `event_id=4294967296`，parent=8，`source_event_id=8`、`dest_event_id=9`，把请求 `301` 分叉成 `303`；另有从 17 分叉出的 `307/308/310` 等。它们在同一错误页上广播，不在 event 118 的祖先上，也不汇入主链；影响是扩大错误页消费面，不改变终局。

**提交后的 squash（event 144）**：`kind=squash_masked`，parent=119（终局后的 consumer），tick `237951547263`，`dyn_inst_seq=520`，`va=ffffffc009483e40`，`pa=a3d75e40`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay`。它在 event 118 之后，**不是**终局见证，也**不能**把本 seed 写成 detected_contained 或 L5；它只说明提交后同一错误页的后续 load 被 squash。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、2 条 `mshr_fill`、2 条 `cache_fill`、2 条 `mshr_free`、1 条 `resp`、1 条 `taint_reg`；主链外还有 25 条 `cache_access`、25 条 `cache_return`、6 条 `mshr_alloc`、10 条 `mshr_merge`、6 条 `mshr_fill`、6 条 `cache_fill`、6 条 `mshr_free`、21 条 `resp`、22 条 `taint_reg`、4 条 `lq_complete`，均属同一错误页的重复消费者/广播分支，没有回到 event 118 的直接祖先。

**consumer（61 条）**：event 119–214，全在终局之后，只作为后果列出。**生命周期**：`chain_end`（215）parent=214，tick `238882168377`，`corr=none`、`outcome=errant_commit_seen`；其 `containment_reason=squash_replay` 只是退出回调携带的上下文，不构成含住。本 seed 只有 1 个 fault。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`118`，tick=`237951302175`，parent=`41` |
| run outcome | `Crash`（`KERNEL OOPS under fault`） |
| admitted / certified | `True` / `True`；`violations=[]` |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=382169`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','4','40','118']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T02-F0-W1` = true |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**必须记录的不一致**：矩阵 Excel 行 47 的负载标签是 `MiBench-TC23 论文负载（…）`，且 `记录状态=blocked(fs-infra: SE has no MiBench FS pipeline)`；但本 seed 的 `run.out` 实际使用 `--readfile …/configs/fs/tlb_probe.rcS`（TLB-AliasPerm 探针），与矩阵标签不符。本文件按事实同时列出二者，不把矩阵标签当成实际负载；这不影响本 seed 的 chain evidence PASS；但 overall_experiment_status 是 NOT_MIBENCH_RESULT，但属于需要上游澄清的元数据不一致。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1/prop_evt.txt.gz` | `dbfd7e829f852464ce7d0869a53de5dcb1bcac513c98d44e3ce81e95baf7510a` | 9898 | 1793078096 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1/chain_report.json` | `017e76d88eb1379e1cf3e1e80dd8578dfd21342f7924ea8e5027a3514d9a307e` | 10701 | 1793078097 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1/run.out` | `ad966044519ca70bada85ebecc99f4864adabf313774ccd8c8c4c596b17e28df` | 2323 | 1793078097 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` | 1726 | 1793078097 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1/stats.txt` | `3f5b73bc6cb6f7019f56878612c55a1c30da9048e7b80ac1c36d7835f3764878` | 381972 | 1793078097 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/manifest.json` | `aeb0ea2269ca78792bf5b308e0ffad6f2f3a00606dc21c97e883e5b09530024c` | 1438 | 1793078098 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| 源码 head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s1/T02-F0-W1/seed1`。

**其它副本与分类**：`runs/lsu/r6_n8_T02-F0-W1_s1.sha8a229009/T02-F0-W1/seed1` 为 **OLD_BINARY_REFERENCE**（manifest binary `8a229009…` ≠ 权威 `20fda699…`，prop_evt SHA 也不同）。本文件只使用上表权威目录。
