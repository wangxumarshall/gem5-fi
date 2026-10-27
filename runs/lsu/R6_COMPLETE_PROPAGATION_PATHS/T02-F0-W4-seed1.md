# T02-F0-W4 seed1 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `4fadb9e9…070a`）重建；`chain_report.json`、`manifest.json`、`run.out`、`run.err`、`stats.txt`、`armtlb_injections.log` 均按只读引用。所有 event_id / tick / 地址 / 位值 / 状态都取自这一份流，未从同 RunID 的其它 seed 借字段。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T02-F0-W4`（模型 ID `T02`，单元 `L1d-TLB`） |
| seed / sample_run_id | `1` / `s1` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 重新翻译命中项时，对命中表项的 PPN 字段做**双比特** `bit_flip`（启动命令 `--tlb_bits_to_change 2`，`--tlb_fault_type bit_flip`，`--tlb_probability 1.0`） |
| 故障类型 | 双比特翻转（矩阵“故障类型”列：双比特翻转） |
| 频率 tier | 请求 `F0` / 生效 `F0` / `lookup_tier_enabled=0`（run.out `CHAOS_LSU_TIER_CAP` 原文） |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`（矩阵 Excel 行 48） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`；`--kernel …/gem5-fs/vmlinux`、`--disk …/gem5-fs/ubuntu.img`、`--bootloader …/gem5-fs/boot.arm64`、`--cpu O3`、`--restore-checkpoint …/fs_cpt_boot/cpt.237949797015` |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T02-F0-W4 --prop_sample_run_id s1` |
| source head（run-time manifest） | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（`manifest.json → source_head`，campaign 运行工作树 HEAD） |
| binary source head | `N/A` —— 该 run-level manifest **没有** `binary_source_head` 字段；`source_head` 是运行期工作树 HEAD，不是二进制构建源 |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44`（`…/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`） |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json`（run-level，SHA-256 `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef`） |
| 正常 EOF | 是（`gzip -t` 通过；`truncated=False`，`stream_present=True`） |
| exit_code | `0`（`chain_report.json → exit_code`；manifest `gem5_exit_code=0`、`campaign_exit_code=0`、`done_marker=true`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=382322 > 0`，`simTicks=932580153`，且 `simTicks` 恰等于 `chain_end.tick(238882377168) − checkpoint(237949797015)` |
| 原始事件数 | 208（`chain_report.event_count=208`；`fault_event_count=208`） |
| fault_id 数量 | 1（`fault_id=1`） |
| 是否经过离线 regrade | 否：本 seed 只有 plain `chain_report.json`（`chain_report_kind=plain`），目录内无任何 `*regrade*` 文件 |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

在 tick `237950940537` 之前，指令流中的一条**存储**指令（`dyn_inst_seq=301`，请求号 `301`）访问虚拟地址 `0xffffffc009483fa8`。该 VA 命中 DTLB 第 `0` 号表项（`entry_index=0`，`way=-1` 表示这是直接索引/非组相联命中槽位，`walk_id=0` 表示没有触发页表遍历）。注入前该表项的状态由 `tlb_lookup` 事件如实记录：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75fa8`。也就是说，页基址 PFN 为 `0x81d75`，页大小 4 KiB（`page_size=1000` 十六进制），页内偏移 `0xfa8`，合成正常物理地址 `0x81d75fa8`；表项有效、全局、ASID=206，权限位 `ap=0`、内存类型 `mtype=2` 保持正常。此时没有任何异常，正常路径本该把 `0x81d75fa8` 交给 LSU。

### 2.2 故障具体如何注入

注入事件是 `event_id=0`（`kind=inj`），tick 与随后那次命中查询同为 `237950940537`。注入点是 `arm_tlb_lookup_hit`，即**命中重翻译时该表项的 PPN 字段**；fault_id=`1`，field=`bit_flip`，`dyn_inst_seq=301`、`request_id=301`、`VA=0xffffffc009483fa8`。事件流本身不带 `mask` 字段（空），但注入日志 `armtlb_injections.log` 明确记录 `Mask: 0x100040000000000`，与 `before=0x81d75`、`after=0x100040000081d75` 的异或结果 `0x100040000000000` 完全一致：**同时翻转了 PFN 的第 42 位和第 56 位**（`0x81d75 ^ 0x100040000000000 = 0x100040000081d75`）。第 42 位落在 48 位 PFN 有效宽度内，第 56 位高出 48 位；由于形成有效 PA 时 PFN 只保留低 48 位，第 56 位在拼接物理地址时被截掉，真正改变有效 PFN 的只有第 42 位。于是有效 PFN 由 `0x81d75` 变为 `0x40000081d75`（等价于把第 42 位置 1），页内偏移 `0xfa8` 不变，有效 PA 从 `0x81d75fa8` 变成 `0x40000081d75fa8`，`effective_pa_changed=1`。这一步已经能说明为什么它属于 `T02` 双比特模型：两个翻转位确实被同时写进同一表项，但只有一个落在可寻址的 PA 位域内；另一个成为“存储值变了、有效地址没变”的哑位。需要强调：**PFN 存储值确实变了，而且有效 PA 也变了**，所以这里不是“高位越界被吞掉后无效果”的良性情形。

### 2.3 TLB 查询与地址翻译

紧随注入的是 `event_id=1`（`kind=tlb_lookup`，parent=0）。这次查询命中同一表项，`before=0x81d75`、`after=0x100040000081d75`；`state_before` 与 `state_after` 完整保留了表项字段，唯一变化是 `pfn` 从 `81d75` 变成 `100040000081d75`，`pa` 从 `81d75fa8` 变成 `40000081d75fa8`；`valid=1`、`global=1`、`asid=206`、`ap=0`、`mtype=2`、`page_size=1000` 全部未动。`event_id=2`（`kind=tlb_pfn`，parent=1）把这次字段级变化钉死：`field=bit_flip`，`state_before=81d75fa8`，`state_after=40000081d75fa8`。`event_id=3`（`kind=tlb_translate_result`，parent=2）是 TLB 交给 LSU 的最终结果：本应交给 LSU 的 `0x81d75fa8` 被替换成 `0x40000081d75fa8`，`effective_pa_changed=1`；同时 `contained=0`、`outcome=NoFault`、`detection_layer` 为空，说明这一层**没有**发现任何异常，也没有把错误翻译拦下。因果链在这里闭合：注入改的是表项 PPN，查询把被改后的值读了出来，翻译结果把错误的 PA 原样递给了下游；TLB 结构没有任何校验位能在这里说“不”。

### 2.4 错误如何进入 LQ/SQ/LSQ

被注入的访问是**存储**（store）。`event_id=4`（`kind=sq_execute`，parent=3）显示该存储已 `issued`，`sq_idx=32`；这里没有 `lsq_push` 事件出现在主祖先上（原始流里本 seed 没有任何 `lq_read`/`lsq_push` 记录），因此“入队”只能由 `sq_execute` 的 `sq_idx=32` 与随后 `sq_complete` 的同一 `sq_idx=32` 证明它在同一个存储队列槽位里走完。`event_id=5`（`kind=sq_writeback`，parent=4，Δtick=1332）把该存储的写回包构建出来：`pa=40000081d75fa8`、`state_after=packet_built`。也就是说，SQ 的输入是翻译结果给出的错误 PA，内部变化是把这个 PA 装进写回包（`sq_idx=32` 保持），输出是带着错误 PA 的 `packet_built` 包——下一级 cache 只能消费这个包，而包里的地址已经错了。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=6`（`cache_access`，parent=5）带着 `pa=40000081d75fa8` 访问 L1D；`event_id=7`（`cache_return`，parent=6）记录 `field=miss`，说明这个“新页”在 cache 中不存在。`event_id=8`（`mshr_alloc`，parent=7）为该缺失分配 `mshr_id=1`，`cache_line=40000081d75fa8`，`state_after=mshr_allocated`。值得注意的是，随后 `event_id=15`（`cache_access`，parent=8，Δtick=333）又访问了 `pa=40000081d75f80`，与前一行的 `…fa8` 相差 `0x28`，落在同一条 64 字节 cache line 内（行地址 `…f80`）；`event_id=16` 仍是 `miss`，`event_id=17` 为它分配 `mshr_id=3`（`cache_line=40000081d75f80`）。这两次 cache 访问都是同一个错误翻译下的分支：一条按 `…fa8` 抓行，另一条按 `…f80` 抓同一行，MSHR 分别记为 1 和 3。需要如实说明：本 seed 的原始流**没有** `mshr_fill`/`mshr_free` 事件（kind 计数为 0），`event_id=30` 的 `resp` 直接以 `mshr_alloc`（17）为 parent，所以“填充—释放”这一段在本 seed 的观测里是缺失的；不能凭空补写，也不能把缺失当成“没发生”，只能说这条流的记录没有把它发射出来。

### 2.6 污染如何返回处理器状态

`event_id=30`（`kind=resp`，parent=17，tick `237951050427`，相对注入 Δtick=108225）把响应送回，`va=40000081d75fa8`（这里记录的是物理侧地址串）、`corr=seq_primary`。`event_id=31`（`kind=taint_reg`，parent=30，同一 tick）完成存储→CPU 的边界转换：`va=40000081d75fa8`，`before=clean`、`after=tainted`，但本 seed 的 `arch_reg`/`phys_reg` 字段为空（流没有记录具体寄存器号），因此只能说“某个被该存储污染的目的寄存器状态从 clean 变为 tainted”，不能编造寄存器编号。`event_id=32`（`kind=sq_complete`，parent=31）把 `sq_idx=32` 的存储标记为 `completed`，`va` 回到原始 VA `0xffffffc009483fa8`。`taint_reg` 之所以是“存储→CPU”的边界，是因为在它之前错误一直以**地址/数据包**的形态在存储子系统里流动，结构没有任何一级把它认成错误；到 `taint_reg` 时，错误第一次变成“体系结构可见状态被标记为脏”，后续任何消费该寄存器值的指令都会把污染继续带下去。

### 2.7 最终传播终局

本 seed 的真实 L5 见证是 `event_id=98`（`kind=errant_commit`），parent=`32`，tick `237951472338`（相对 `taint_reg` Δtick=421911），`dyn_inst_seq=391`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b1000`，`commit_seq=161`。它是真实提交点：一条依赖被污染寄存器的指令（`dyn_inst_seq=391`，不是注入指令本体 `301`）带着错误数据退休。为什么没能在提交前被消掉：TLB 只改变了 PA，没有任何校验位；L1D 只是按错误 PA 读写，命中/缺失都无从知道“这个 PA 不该出现”；LSQ 与 ROB 没有地址-数据一致性检查；到提交点之前，唯一可能拦下它的是分支/异常路径上的 squash，但本 seed 没有发生。`chain_end`（`event_id=185`，tick `238882377168`）只是传播监控退出回调发射的生命周期收口记录（`corr=none`，`outcome=errant_commit_seen`），它**不是** L5，也不能拿它冒充终局；本 seed 的 L5 只能是 event 98。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=161` 退休（`dyn_inst_seq=391`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局是 `L5`（`provable_to=L5`，`terminal=full`），运行结局是 `Crash`。`run.out` 在 tick `237951472338` 记录了 `CHAOS_DETECT: layer=None contained=0 tick=237951472338 ptag=1 reason=errant_commit`，与 event 98 的 tick 完全对应；紧接着 `run.out` 以 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)` 退出，`run.err` 对应行是 `src/kern/linux/events.cc:64: warn: Kernel oops in guest`。注入 tick 是 `237950940537`，终局 tick 是 `237951472338`，传播时延 `531801` ticks。因果链是：错误的 PA 让存储写/读到了不该碰的物理页（`0x40000081d75…`），污染经寄存器提交后，guest 内核在后续执行中触发 oops，仿真在故障下以 Crash 结束。这里不是 Timeout：run 在预算内正常走到了内核 oops 并退出，`simTicks` 与 `chain_end` 对得上。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB（查询/翻译） | VA `0xffffffc009483fa8`、命中第 0 项 | PPN `0x81d75 → 0x40000081d75`（bit42；bit56 越 48 位被截） | PA `0x81d75fa8 → 0x40000081d75fa8`，`contained=0` | 错误翻译进入流水线，TLB 无校验 |
| SQ | `sq_idx=32`、错误 PA | 构包 | `packet_built`（`pa=40000081d75fa8`） | 错误地址被固化成存储请求 |
| L1D | 错误 PA 行 `…fa8`/`…f80` | 两次 miss、分配 MSHR 1/3 | miss 响应路径（本流无 fill/free 记录） | cache 按错误地址做真实缺失/取数，无从判别 |
| MSHR | 行 `40000081d75fa8` / `…f80` | `mshr_alloc`（1、3） | 响应 `event_id=30` | 缺失分配是地址驱动，错误地址被当作正常地址 |
| PRF/寄存器 | `resp`（`va=40000081d75fa8`） | `clean → tainted`（寄存器号未记录） | 污染寄存器 | 错误跨入体系结构状态 |
| ROB/提交 | 污染寄存器（`dyn_inst_seq=391`） | 退休 | `errant_commit`（commit_seq=161） | 错误获得体系结构可见性 |
| PropMonitor | 退出回调 | 发射 `chain_end` | 生命周期收口（tick 238882377168） | 仅记录流结束，不是 L5 |

最后用一段话总结整条链：一条存储指令命中被双比特改坏的 TLB 表项，第 42 位把 PFN 改到 `0x40000081d75`（第 56 位因超出 48 位 PFN 宽度被截掉，但有效 PA 仍然改变），TLB 以 `contained=0` 把 `0x40000081d75fa8` 交给 SQ，SQ 在 `sq_idx=32` 构包后送 L1D，L1D 按这个错误地址连续两次 miss、分配 MSHR 1 和 3，响应回来后寄存器被标记为 tainted、存储槽位完成，最终一条依赖该寄存器的指令在 `commit_seq=161` 错误退休，内核随即 oops，仿真以 Crash 结束；全程没有任何一级在提交前识别并纠正这个地址错误。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入链路三方一致：`prop_evt` 中有 1 条 `inj`（fault_id=1），`armtlb_injections.log` 有 1 条 `Site: arm_tlb_lookup_hit` 记录，`stats.txt` 的 `board.chaos_armtlb.numFaultsInjected=1`，`run.out` 的 `CHAOS_LSU_TRIGGER … injected=1`。尝试/合格口径：`attempted=150224`、`eligible=56`、`injected=1`；`activated=W3-L0-layer`。被改坏的值确实被下游读取：`tlb_lookup` 的 `state_after.pfn`、`tlb_pfn.after`、`tlb_translate_result.after` 都是 `0x100040000081d75`/`0x40000081d75`，随后 `sq_writeback`、`cache_access` 的 `pa` 都是 `0x40000081d75fa8`。因此这是“已注入且已激活”，不是注入未被消费的空转样本。

### 3.2 故障传播类型

**地址型**（address）错误，且是“错误物理页”而非错误数据：被污染的是 TLB 表项的 PPN，传播的是 PA。它在 cache/MSHR 侧表现为对一个真实但**不该被访问**的物理页的正常 miss/取数，在寄存器侧表现为 tainted 数据。不是 permission（`ap` 未动）、不是 control-state（无异常/分支状态被改）、不是 timing（时间戳只体现排队时延）、也不是 wrong cache line（行地址由错误 PA 直接决定，没有二次错位）。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3`（`tlb_translate_result`，tick `237950940537`）。在它之前，`event_id=2` 已经把错误值写进表项存储，但严格说存储值仍可被后续 refill/flush 覆盖；到 `event_id=3`，被污染的值已经作为“本请求的有效翻译结果”交给 LSU，且 `contained=0`、`outcome=NoFault`，本结构内没有任何机制能在不重放该访问的前提下撤销它。从这个点起，后续 SQ/L1D/MSHR 都只是在忠实执行一个已经错误的地址。

### 3.4 检测与掩蔽机制

本链上可用的检测点全线沉默：TLB 无奇偶/ECC（否则 `event_id=2` 就会报错）；翻译结果层没有“PA 是否属于合法物理范围”的检查（`event_id=3` 直接放行）；L1D/MSHR 的命中-缺失只回答“这个地址在不在 cache”，不回答“该不该访问”；LSQ/ROB 无地址一致性检查；提交点本身也不校验。唯一出现的“检测”是事后 oracle：`run.out` 在 `237951472338` 打 `reason=errant_commit`，此时错误已经提交。观察到的盲区正是：**48 位 PFN 内的位翻转没有任何提交前检测**，只有在造成内核 oops 之后才以 Crash 的形式暴露。

### 3.5 最终 SDC 风险判断

存在**真实错误提交**（event 98，`detection_layer=L5`、`outcome=errant_commit`、`contained=0`、`corr=taint_prop`），体系结构可见性成立；系统层面以内核 oops 暴露，故本样本归类为 **Crash**，而不是 SDC。之所以不是 SDC：SDC 需要“对外可见且未被检测到的错误输出”，本样本的运行结局是显式崩溃，错误被系统以 Crash 形式暴露；同时本 workload 没有应用级输出 oracle，无法判断“若不崩，最终数据是否正确”，因此也不能反过来把它判成“数据正确”。结论应严格限定为：已证真实错误提交，且运行结局为 Crash/DUE。

### 3.6 与同 RunID 其他 seed 的关系

仅比较事实：seed2 的注入在 `237950233911`（VA `0xffffffc009483eb8`，掩码 `0x1000000800000000`，第 35/60 位），seed3 在 `237950233578`（VA `0xffffffc009483eb0`，掩码 `0x20000000040000`，第 18/53 位）。三个 seed 都是双比特、都只有 1 个 fault_id、都以 `full` 收口、运行结局都是 Crash。差别在注入点/掩码/有效 PA 变化：seed1 有效 PFN `0x81d75→0x40000081d75`，seed2 `→0x800081d75`，seed3 `→0xc1d75`；三者都各有一个高位（56/60/53）被 48 位 PFN 截断，真正改写 PA 的都是低位（42/35/18）。本 seed 的 event_id、tick、地址与状态只来自本 seed，未从 seed2/seed3 引入。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=98` 经 `parent_event_id` 回溯的单祖先，共 16 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | — | inj | L0 | TLB | 1 | origin | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | 100040000081d75 | 81d75 | 100040000081d75 | 0x100040000000000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 237950940537 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | 100040000081d75 | 81d75 | 100040000081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100040000081d75;ap=0;mtype=2;page_size=1000;pa=40000081d75fa8 | — | — | — | — | 命中查询 | PFN 81d75→100040000081d75 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 237950940537 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | 40000081d75fa8 | — | — | 81d75 | 100040000081d75 | 81d75 | 100040000081d75 | — | 81d75fa8 | 40000081d75fa8 | — | — | — | — | 表项当前状态 | PA 81d75fa8→40000081d75fa8 | 表项存储被改写 |
| 4 | 3 | 2 | 237950940537 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | 40000081d75fa8 | — | — | — | — | 81d75fa8 | 40000081d75fa8 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100040000081d75;ap=0;mtype=2;page_size=1000;pa=40000081d75fa8 | 0 | — | NoFault | — | 表项 PFN | PA 81d75fa8→40000081d75fa8 | 首个不可逆点 |
| 5 | 4 | 3 | 237950940537 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | 错误 PA 的 store | 发射（sq_idx=32） | 进入 SQ |
| 6 | 5 | 4 | 237950941869 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 301 | — | 40000081d75fa8 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | sq_idx=32 | 构包 | 错误地址固化为写回包 |
| 7 | 6 | 5 | 237950941869 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | 40000081d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483fa8 | 访问 L1D | 按错误 PA 取数 |
| 8 | 7 | 6 | 237950941869 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | 40000081d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 40000081d75fa8 | miss | cache 无法判别地址合法性 |
| 9 | 8 | 7 | 237950941869 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | 40000081d75fa8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 40000081d75fa8 | 分配 MSHR 1 | 错误行进入填充流水 |
| 10 | 15 | 8 | 237950942202 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | 40000081d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483fa8 | 访问 L1D | 按错误 PA 取数 |
| 11 | 16 | 15 | 237950942202 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | 40000081d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 40000081d75f80 | miss | cache 无法判别地址合法性 |
| 12 | 17 | 16 | 237950942202 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | 40000081d75f80 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 40000081d75f80 | 分配 MSHR 3 | 错误行进入填充流水 |
| 13 | 30 | 17 | 237951050427 | 108225 | resp | L3 | L1D | 1 | seq_primary | 301 | 301 | 40000081d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 14 | 31 | 30 | 237951050427 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 301 | 301 | 40000081d75fa8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 15 | 32 | 31 | 237951050427 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | 污染响应 | 存储完成（sq_idx=32） | 错误存储正式完成 |
| 16 | 98 | 32 | 237951472338 | 421911 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 391） | 错误退休（commit_seq=161） | 真实 L5 |

折叠说明：本 seed 的 36 个 `consumer` 事件全部位于终局之后（event 99–184，tick `237951472338..237965443353`），没有一个落在 `event_id=98` 的主祖先上；因此 Ch.4 没有可折叠的 consumer 行，也不存在“折叠会丢掉结论性事件”的风险。所有不可折叠事件（inj、PFN/PA 变化、request 身份变化、cache miss、MSHR alloc、resp、taint_reg、errant_commit、chain_end）均逐条保留。

## 5. 相关旁支与未进入最终主链的事件

**request_fork 广播（22 条）**：全部是 `bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`，`shared_addr=40000081d75000`、`shared_size=1000`（一个 4 KiB 页）。最早一条 `event_id=4294967296`，parent=8，`source_event_id=8`、`dest_event_id=9`，把请求 `301` 分叉成 `303`；另有从 event 17 分叉出的 `307/308/310` 等。它们都是同一个错误 PA 页内的地址回退广播，不在 `event_id=98` 的祖先上，也不重新汇入主链。它们的影响是**扩大**污染面（让更多请求经由同一错误页），但不改变代表故障的终局判定。

**off-chain 的 cache/MSHR/响应事件**：除主链上的 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、1 条 `resp`、1 条 `taint_reg` 外，流中还有 30 条 `cache_access`、30 条 `cache_return`、16 条 `mshr_alloc`、14 条 `mshr_merge`、20 条 `resp`、20 条 `taint_reg`、3 条 `lq_complete` 位于主链之外。它们是同一页内其它请求与广播分支的重复消费者，均以 `corr=addr_fallback` 挂在广播树或其它 MSHR 上，没有一条重新成为事件 98 的直接祖先。因此它们不改变“本 seed 的代表故障在 event 98 达到 L5”的结论；它们说明的是同一错误页在多个请求上被反复消费。

**consumer（36 条）**：`event_id` 99–184，tick `237951472338..237965443353`，全部是 `errant_commit` 之后的污染传播记录（`corr=taint_prop`），没有一条在主祖先上。它们是终局之后的“后果”，不是终局的“原因”，故只在此列出，不并入 Ch.2/Ch.4 的主链。

**生命周期**：`chain_end`（event 185）是唯一一条 `kind=chain_end` 记录，parent=184（consumer 链尾），tick `238882377168`，`corr=none`，`contained=1`，`outcome=errant_commit_seen`。它由退出回调发射，不是 L5，也不构成含住证据；本 seed 没有任何 `squash_masked`、没有第二支注入、没有其它 `errant_commit`。它与 event 98 的 tick 相差 `930904830` ticks，正好是 oops 之后到退出回调的时间，不代表传播还在继续。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`98`，tick=`237951472338`，parent=`32`，`detection_layer=L5`，`outcome=errant_commit`，`corr=taint_prop` |
| run outcome | `Crash`（`CHAOS_DETECT reason=errant_commit`；`KERNEL OOPS under fault`） |
| admitted | `True`（`admission.path=full_chain`，`violations=[]`，`reasons=[]`） |
| certified | `True` |
| violations | `[]` |
| truncated | `False`（gzip EOF 正常） |
| gzip EOF | 正常 |
| stats 有效性 | 有效（`simInsts=382322`，`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK`（`cell_results.conservation=OK`；`consumer_summary_accounting.conservation=ok`） |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级；per-seed 无独立字段） |
| campaign/checker agreement | 一致：`chain_report.terminal=full/L5`，权威 checker 复算同为 `full/L5`，路径 `['0','1','2','4','31','98']` 完全相同 |
| CHAIN_DEMONSTRATED | YES（代表故障在单祖先上从 `inj` 可证到真实 `errant_commit`） |
| COMPLETE_3_OF_3 | `T02-F0-W4` = true |
| 判定 | **PASS** |

说明：传播终局（L5）与运行结局（Crash）是两件事——前者证明错误确实到达提交点，后者说明系统以崩溃暴露了它；二者在本 seed 同向、不矛盾。`chain_end` 只作为生命周期收口列出，未用于任何层级判定。本 seed 不存在 Timeout，也不存在“L5 成立但运行未正常结束”的组合。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/prop_evt.txt.gz` | `4fadb9e9fd6768f63b1125f2a9f5eb2c6cb0ca8707092c46424841ce61e0770a` | 8422 | 1792917130 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/chain_report.json` | `e06393ed8010bdc23f473174423ad97101d749aecd9c87c3d1519031b3b45016` | 9033 | 1792917131 |
| 权威 regrade | `N/A` —— 本 seed 无 regrade 文件，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/run.out` | `2f095e9493fa90a69a9a44128ffa3a349e19460a6ec7fc9eb2e494269221701e` | 2159 | 1792917131 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/run.err` | `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f` | 1833 | 1792917131 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/stats.txt` | `d57b9ce5a0be2764e334a82915714ed98801c6a0e7f6744cea79ccc73212b181` | 382875 | 1792917130 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json` | `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef` | 1773 | 1792917170 |
| 启动命令记录 | `run.out` 第 8 行（`command line:`）与 `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | — | — |
| 源码 head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（run-time worktree HEAD；非二进制构建源） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1`。

**其它副本与分类**（见 `../R6-AUTHORITATIVE-EVIDENCE.md`）：`runs/lsu/r6_c9_T02-F0-W4_s1/T02-F0-W4/seed1`、`runs/lsu/r6_c9_T02-F0-W4_s2/T02-F0-W4/seed1`、`runs/lsu/r6_c9_gracecheck_T02-F0-W4/T02-F0-W4/seed1`、`runs/lsu/r6_c9_gracecheck2_T02-F0-W4/T02-F0-W4/seed1` 均为 **EXACT_DUPLICATE**（prop_evt 字节相同、chain_report 语义相同、run.out 去元数据后相同）；`runs/lsu/r6_c7_T02-F0-W4_s1/…` 为 **OLD_BINARY_REFERENCE**（binary `a9b2c236…`）；`runs/lsu/r6_c5_*`、`r6_bisect_v0..v5`、`r6_canary_*`、`r6_c9_gracecheck3_*`、`r6_p1_*`、`r6_tlb_H*`、`r6_w1_*` 等为 **INTERRUPTED**（无 `.done`/`.exit_code` 标记）。本文件未使用任何副本的数值，只使用上表权威目录。
