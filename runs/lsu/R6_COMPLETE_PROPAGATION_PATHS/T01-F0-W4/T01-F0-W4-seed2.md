# T01-F0-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F0-W4` |
| seed | `2` |
| sample_run_id | `s2` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；传播状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F0` |
| requested tier | `F0` |
| effective tier | `F0` |
| tier enabled | `关闭(0)`（run.out `CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`） |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（与矩阵标签一致） |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 2 --chaos_propagation --prop_run_id T01-F0-W4 --prop_sample_run_id s2` |
| source head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（manifest.source_head） |
| binary source head | `N/A`（manifest 无 `binary_source_head`） |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5。manifest 运行期记录为 `bc82f29d...`） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` |
| 正常 EOF | **是**（gzip 解压到 EOF 无异常，解压后 296123 字节） |
| exit_code | `0`（manifest.exit_code=0；`.exit_code`=0） |
| truncated | **False** |
| stats 是否有效 | **是**：完整 footer；`simTicks=932479587`、`simInsts=382207`、`finalTick=238882276602` |
| 原始事件数 | `428` |
| fault_id 数量 | `1`（全部 428 条事件属 `fault_id=1`） |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 的终局是真实 L5：`errant_commit`（`event_id=259`，tick=`237951515628`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`）。按 `parent_event_id` 回溯得到唯一祖先链：

`0(inj) → 1(tlb_lookup) → 2(tlb_pfn) → 3(cache_access) → 4(cache_return) → 5(mshr_alloc) → 6(cache_access) → 7(cache_return) → 8(mshr_alloc) → 60(resp) → 61(taint_reg) → 259(errant_commit)`

共 12 条事件。祖先链内 tick 单调不降（同 tick 的连续段分别是 237950233911、237950235576、237950235909、237950344134；最后跨到 237951515628）。这里有一个必须点明的结构事实：**本 seed 的 fault 1 流里根本没有 `tlb_translate_result` 事件**，L2 锚点由 `tlb_pfn` 承担（`chain_report.path_event_ids=['0','1','2','3','61','259']`）；也就是说，本 seed 没有发生"翻译结果比对"这一步，缺失是结构性缺席，不是"比对结果为 0"或"NoFault"。

### 2.1 故障注入前的正常状态

被污染的翻译属于一次 `dyn_inst_seq=32`、`request_id=32` 的访问（注入事件本身没有 identity 字段，身份由紧随其后的 `tlb_lookup` 与 `tlb_pfn` 以 `request_id=0`/`dyn_inst_seq=0` 的 `addr_fallback` 记录开路，随后在 `cache_access` 以 `request_id=32`/`dyn_inst_seq=32` 落定；这一身份变化见 §2.4）。VA=`0xffffffc009483eb8`，页内偏移 `0xeb8`。表项在注入前正常：`vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75eb8`。目标表项 `entry_index=0`，`walk_id=0`。访问类型（load/store）在本链中没有 LQ/SQ 事件，记为 `N/A`。

### 2.2 故障具体如何注入

`event_id=0`，tick=`237950233911`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`corr=origin`，`field=bit_flip`；该注入事件没有 `request_id`/`dyn_inst_seq` 字段（原文为空）。注入日志：`Mask: 0x800000000`，即 PFN 第 35 位。原 PFN `0x81d75` 异或后得到 `0x800081d75`：把数值变化讲完整——第 35 位由 0 变 1，表项保存的 PFN 从 `0x81d75` 变成 `0x8_0008_1d75`，其余位不变。与 seed1/seed3 不同，这一次翻转位落在物理地址可见宽度以内：PFN 左移 12 位后，第 35 位落在物理地址的第 47 位，仍然属于有效 PA 的一部分。因此有效 PA 从 `0x81d75eb8` 变成 `0x800081d75eb8`，`effective_pa_changed` 为真。这是本 seed 与两个含住 seed 的分水岭。

同样需要记录：注入符合"单次 XOR、选有效表项、以下游读取为激活口径"，但字段是 PFN 而非矩阵所写的 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`237950233911`）记录 `entry_index=0`、`walk_id=0`、`field=post_lookup`，`before=81d75`、`after=800081d75`；`state_before` 的 `pa=81d75eb8`、`state_after` 的 `pa=800081d75eb8`，同时 `pfn` 变为 `800081d75`。这里查找不仅读到了污染 PFN，而且物化出的 PA 已经改变。

`event_id=2`（`tlb_pfn`，parent=1）把这个物化结果独立记录一次：`pa=800081d75eb8`、`state_before=81d75eb8`、`state_after=800081d75eb8`。语义上这是"L2 地址物化"：请求从此刻起携带一个错误的物理地址。与 seed1/seed3 的关键差别是，**本 seed 没有 `tlb_translate_result`**，因此没有任何事件去比较 requested/effective PA，也没有任何 `contained=1` 的 L2 记录。下游因此完全信任这个错误 PA——这正是它能够走到 L5 的结构原因。

### 2.4 错误如何进入 LQ/SQ/LSQ

本链没有 `lsq_push`/`lq_read`/`sq_execute`/`sq_writeback`/`lq_complete`/`sq_complete`，因此"进入队列"这一步的具体动作记为 `N/A`（证据缺席）。但错误 PA 确实进入了访存路径：`event_id=3`（`cache_access`，parent=2，tick=`237950235576`）以 `request_id=32`、`dyn_inst_seq=32`、`corr=addr_fallback` 携带 `pa=800081d75eb8` 发起第一次访问。这里发生了本链唯一的身份切换：注入与 lookup 记录的是 `request_id=0`/`dyn_inst_seq=0`（未盖戳），而 cache 侧把请求归到真实的 `32/32`；`corr=addr_fallback` 就是这次关联的注记。parent 指针保证它与前一步同属一条祖先链，身份差异是记录口径，不是跨链拼接。

### 2.5 错误如何经过 cache 和 MSHR

错误 PA 在 L1D 侧经历了两次访问、两次未命中、两次 MSHR 分配：

第一次，`event_id=3`（`cache_access`）在 `pa=800081d75eb8` 访问，`event_id=4`（`cache_return`，parent=3）记录 `field=miss`，随后 `event_id=5`（`mshr_alloc`，parent=4）记录 `cache_line=800081d75eb8`、`mshr_id=1`、`state_after=mshr_allocated`。这说明首次访问的行地址就是该 PA 本身，且未命中。

第二次，`event_id=6`（`cache_access`，parent=5，tick=`237950235909`）以 `pa=800081d75e80` 访问——这是同一 64 字节行（`0x...eb8 & ~0x3f = 0x...e80`）的行基址；`event_id=7` 记录 `field=miss`，`event_id=8` 记录 `cache_line=800081d75e80`、`mshr_id=2`、`state_after=mshr_allocated`。两次未命中说明该行在 L1D 中不存在；两次 MSHR 分配说明请求被挂起等待下层。

本链的返回发生在 `event_id=60`（`resp`，parent=8，tick=`237950344134`）：它直接以 `mshr_alloc`（event 8）为父，记录 `request_id=32`、`dyn_inst_seq=32`、`va=800081d75eb8`。**注意：本链的祖先里没有 `mshr_fill`/`cache_fill`/`mshr_free`**，这些填充事件存在于同一 fault 的旁支（§5），但不在终局见证的祖先上；因此本条主链只能证明"请求挂入 MSHR 后收到 response"，不能凭空描述 fill 的状态迁移。两次访问仍属同一 fault，因为它们的 `fault_id=1`、`parent_event_path` 连续，且第二次访问的地址是第一次访问同一行的对齐形式。

### 2.6 污染如何返回处理器状态

`event_id=61`（`taint_reg`，parent=60，tick=`237950344134`）把响应携带的污点落到处理器状态：`request_id=32`、`dyn_inst_seq=32`、`va=800081d75eb8`、`field` 记为 `clean→tainted`（`before=clean`、`after=tainted`）。这是存储→CPU 的边界：在此之前的错误都还只是"存储/缓存里的地址与数据"，从此之后被污染的值进入寄存器状态。证据限制：本事件的 `arch_reg`/`phys_reg` 为空，因此**无法从本 seed 的证据给出具体寄存器号**；这条盲点必须保留，不能用猜测补上。

### 2.7 最终传播终局

真实 L5 是 `errant_commit`（`event_id=259`，parent=61，tick=`237951515628`）：`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，并且明确记录 `dyn_inst_seq=391`、`pc=ffffffc0087b1000`、`commit_seq=161`。它与上游的关系是"被污染状态在提交端第一次形成架构可见的差异"：被污染的是一个更年轻的指令（`dyn_inst_seq=391`），而不是最初那次访问（`32`），说明污染沿寄存器依赖传播到了后续指令。为什么在提交前没有被消除？因为本 seed 的链上不存在任何拦截机制：没有 `tlb_translate_result`（L2 比对缺席）、没有 `squash_masked`（L4 无 squash 收口）、也没有其它 `contained=1` 事件。错误因此在 L5 直接可见。

`chain_end`（`event_id=375`，tick=`238882276602`，`detection_layer=L5`，`contained=1`，`outcome=errant_commit_seen`）只是流关闭记录，**不是 L5 见证**，不能替代 event 259；L5 的唯一见证是 event 259。

### 2.8 从传播终局到系统表现

传播终局是 L5 `errant_commit`（L5）；`provable_to=L5`；运行结局 `Crash`。run.out 中能证明症状的两行是：

- `CHAOS_DETECT: layer=None contained=0 tick=237951515628 ptag=1 reason=errant_commit`（错误提交已被记录，且 `contained=0`）
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err 的证据是 `src/kern/linux/events.cc:64: warn: Kernel oops in guest` 与随后的 `Dumping kernel dmesg buffer to board.workload.dmesg...`；guest dmesg 记录：

- `[2.160000] Unable to handle kernel paging request at virtual address 0b8542c0087b0c40`
- `[2.160000] Internal error: Oops: 86000004 [#1] PREEMPT SMP`
- `[2.160000] Call trace:`

注入 tick=`237950233911`，错误提交 tick=`237951515628`，传播延迟 **1,281,717 ticks**。L5→Crash 的因果链是成立的：错误提交发生在崩溃之前，随后 guest 内核在访问一个畸形地址时触发 Oops；本证据不能进一步给出该畸形地址与错误 PA 之间的逐位对应，故只陈述时序与事件类型，不虚构微观机理。链终止（`chain_end`）tick=`238882276602`，即运行结束时刻，晚于错误提交 932,042,691 ticks。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit35 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req 未盖戳） | 读到 `pfn=800081d75` | 污染表项，PA 变为 `800081d75eb8` | 激活，且有效 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 0xeb8 | 物化出错误 PA | `pa=800081d75eb8` | 错误地址进入下游 |
| L2 MMU translate result | — | — | — | `N/A`：本 fault 无该事件（比对机制缺席） |
| L3 L1D | 错误 PA 第一次访问 | 未命中 | `cache_return miss` | 错误地址被真实消费 |
| L3 MSHR | miss 请求 | 分配 MSHR 1 | `mshr_alloc, line=...eb8` | 挂起等待 |
| L3 L1D | 同一行基址 `...e80` 再次访问 | 未命中 | `cache_return miss` | 第二次消费同一错误行 |
| L3 MSHR | 第二次 miss | 分配 MSHR 2 | `mshr_alloc, line=...e80` | 挂起等待 |
| L3 L1D→core resp | MSHR 2 的返回 | 返回数据/响应 | `resp`（req=32, va=...eb8） | 污染回到核心侧 |
| L4 taint/regfile | response | clean→tainted | 污染寄存器状态 | 存储→CPU 边界 |
| L5 ROB/commit | 被污染状态 | 首次错误提交 | `errant_commit, dseq=391, pc=...7b1000` | 架构可见错误 |
| LQ/SQ | — | — | — | `N/A`（本链无队列事件） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 35 位置 1，翻转位落在物理地址宽度内，于是有效 PA 由 `0x81d75eb8` 变成 `0x800081d75eb8`；这条翻译没有产生 `tlb_translate_result` 比对，错误 PA 被 L1D 以两次未命中、两次 MSHR 分配消费，经 `resp` 与 `taint_reg` 进入寄存器状态，最终在 L5 由一条更年轻的指令（`dyn_inst_seq=391`）完成真实错误提交，运行随后以 guest 内核 Oops 结束（Crash）。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；run.out `CHAOS_LSU_TRIGGER: attempted=150217 eligible=2 injected=1`；`stats.txt numFaultsInjected=1`。三处一致（injected=1 = stats=1 = 日志 1 条；attempted>0）。污染值被下游真实读取并由 cache、response、taint_reg 一路消费，属于 activated。

### 3.2 故障传播类型

**address 型**：污染 PFN，直接改变 VA→PA。它进而表现为 **wrong cache line / wrong request routing** 的后果——两次 L1D 访问针对 `0x800081d75eb8`/`0x800081d75e80` 这个错误行，而不是正常行；但这只是 address 型故障的下游表现，不是独立类型。不是 data 型（字节内容未被注入器直接改写）、不是 permission（`ap`/`valid` 未变）、不是 control-state（注入器未改控制位）。

### 3.3 首个不可逆传播点

`event_id=2`（`tlb_pfn`）：在这一步，结构已经把一个错误的物理地址物化给了请求，且本 seed **没有**随后的 `tlb_translate_result` 去撤销它。从此刻起，任何下游单元都只能消费这个错误地址。更严格地说，`event_id=3`（第一个 `cache_access`）是错误地址第一次被外部结构真实使用的位置；两者分别代表"决定已做出"与"后果已发生"，本文把 `event_id=2` 记为不可逆点，并在 §2.5 说明 event 3 首次消费它。

### 3.4 检测与掩蔽机制

可能发现该故障的机制：TLB 翻译结果的 PA 比对（本 seed 缺席）、权限/对齐异常（未触发）、L1D 一致性/ECC（`protection: model=none bits=1 -> Raw`，没有 ECC/parity）、squash/replay（本 seed 无 `squash_masked`）、commit 前的架构检查（没有拦截）。实际观察到的检测只有提交端：`CHAOS_DETECT ... reason=errant_commit` 是"事后记录"，不是拦截。检测盲点因此非常明确：当翻转位改变有效 PA、且该翻译没有触发 `tlb_translate_result` 比对时，整条路径没有任何端到端保护，错误会一路到提交端；guest 内核的 Oops 只是错误提交后的后果，不是对故障本身的检测。

### 3.5 最终 SDC 风险判断

存在真实 errant commit（event 259）与架构可见错误（L5），运行以 Crash 结束。因此本 seed **不判 SDC**：错误最终以内核 Oops 的形式外部可见，不属于"未被发现的静默错误"。但也不能反过来说"没有静默期"：在 event 61（taint_reg）到 event 259 之间，污染值已经进入寄存器并被 65 条 consumer 事件观测（`consumer_summary` 11 条记录、`logical_total=60`、`by_outcome=sd_observed`，见 §5），这段区间内的错误在架构上尚未被拦截，只是最终被崩溃暴露。是否存在"应用级输出已被静默污染"？本 seed 的负载没有跑到应用 oracle 行（terminal 中只有 Oops，没有 `rounds ok=` 行），因此**无法判断最终数据正确性**；绝不能仅凭 errant_commit 就称其为 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 注入位点相同：`arm_tlb_lookup_hit`。
- 掩码：seed1=`0x100000000000000`（bit56，PA 之外）、seed2=`0x800000000`（bit35，PA 之内）、seed3=`0x20000000000000`（bit49，PA 之外）。
- 有效 PA：seed1 不变、seed2 改变（`81d75eb8→800081d75eb8`）、seed3 不变。
- 终局：seed1/seed3 为 L2 含住；seed2 为 L5 errant_commit（event 259）。
- 运行结局：seed1/seed3=Masked；seed2=Crash。
- 决定性差异不在注入点，而在两个结构条件：翻转位是否落在有效 PA 宽度内，以及该翻译是否产生 `tlb_translate_result` 比对。seed2 同时满足"PA 改变"与"比对缺席"，因此逃逸。

## 4. 完整主链事件表

`mask` 取自 `armtlb_injections.log`；`layer` 用 TLB family 层映射；`old_pfn/new_pfn` 只对 PFN 事件有意义。本链 12 条，无需折叠。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | — | — | ffffffc009483eb8 | — | — | — | 81d75 | 800081d75 | 81d75 | 800081d75 | 0x800000000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit35 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 237950233911 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | — | — | — | 81d75 | 800081d75 | 81d75 | 800081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=800081d75;ap=0;mtype=2;page_size=1000;pa=800081d75eb8 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 237950233911 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | 800081d75eb8 | — | — | 81d75 | 800081d75 | 81d75 | 800081d75 | — | 81d75eb8 | 800081d75eb8 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 不可逆点 |
| 4 | 3 | 2 | 237950235576 | 1665 | `cache_access` | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 800081d75eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误 PA + 真实请求 32 | 首次访问错误地址 | 错误被消费 |
| 5 | 4 | 3 | 237950235576 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | 800081d75eb8 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次访问未命中 | 需要下层数据 | 未命中，需下层 |
| 6 | 5 | 4 | 237950235576 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 800081d75eb8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 | 挂入 MSHR 1 | 请求等待 |
| 7 | 6 | 5 | 237950235909 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 800081d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行的行基址 | 第二次访问 | 再次消费错误行 |
| 8 | 7 | 6 | 237950235909 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | 800081d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | — | — | — |
| 9 | 8 | 7 | 237950235909 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 800081d75e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 挂入 MSHR 2 | 请求等待 |
| 10 | 60 | 8 | 237950344134 | 108225 | `resp` | L3 | L1D→core resp | 1 | addr_fallback | 32 | 32 | 800081d75eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | response 返回 | 污染回到核心侧 | 污染回到核心 |
| 11 | 61 | 60 | 237950344134 | 0 | `taint_reg` | L4 | taint/regfile | 1 | addr_fallback | 32 | 32 | 800081d75eb8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 污染 response | 寄存器状态 clean→tainted | 存储→CPU 边界 |
| 12 | 259 | 61 | 237951515628 | 1171494 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 被污染状态 | 首次架构可见错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 428 条事件，全部属于 `fault_id=1`；主链 12 条，其余 415 条（另加 `chain_end`）为旁支。旁支的主要形态：

- **`request_fork` 52 条**：全部是 `parent_event_id=8` 出发的 `addr_fallback_broadcast`（`source_event_id=8`，`old_request_id=32`，`new_request_id` 依次为 34、35、37、38、40、41、43、44、46、47、49、50、…），在 L3 层把同一个错误地址广播给兄弟请求。它们从 MSHR 分配处分叉，**没有**回流到终局见证的祖先（终局祖先仍走 8→60）。
- **兄弟请求的访存事件**：65 条 `cache_access`、65 条 `cache_return`、26 条 `mshr_alloc`、39 条 `mshr_merge`、50 条 `resp`、50 条 `taint_reg`、3 条 `lq_complete`，覆盖 54 个不同 request_id（含 34/35/37/…/3967/10559）。这些旁支说明"同一错误地址被多个兄弟请求消费"，但它们各自有自己的父边，不能并入主链。
- **65 条 `consumer`**：`consumer_summary` 给出 11 条记录、`emitted_events=11`、`suppressed_consumers=49`、`logical_total=60`、`conservation=ok`；`by_outcome=sd_observed`，即污染值被后续指令观测。它们是主链之后的消费面证据，不是主链事件。
- **无 `squash_masked`**：本 seed 没有任何 squash/replay 收口，这也是错误能够到达 L5 的直接原因之一。

旁支是否影响 SDC 诊断？它们扩大"被污染值被后续指令观测"的规模（60 个逻辑消费者），但不改变终局：终局由主链 event 259 证明，而旁支不构成另一条可选的终局祖先。`chain_end` 仍是生命周期记录。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=259，tick=237951515628，L5 |
| run outcome | `Crash`（oracle_outcome=Crash，exit_code=0；guest 内核 Oops） |
| admitted | `True`（path=`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效（完整 footer、非零 simTicks/simInsts） |
| conservation | `ok`（consumer_summary_accounting：emitted 11 + suppressed 49 = logical 60；issues=[]） |
| count_contradiction | 否（attempted=150217 > 0；injected=1=stats=1） |
| campaign/checker agreement | 一致（cell_results seed2 outcome=Crash；chain terminal=full；run.out `CHAOS_DETECT reason=errant_commit`） |
| CHAIN_DEMONSTRATED | 是（`inj`→L5 单祖先连续，L4 终局与显式 L5 见证同时在场） |
| COMPLETE_3_OF_3 status | 三个 seed 证据齐全且 certified；本 seed `COMPLETE_L5` |
| verdict | **PASS** |

一致性自检：12 个引用事件全部存在；parent 连续（259←61←60←8←7←6←5←4←3←2←1←0）；parent 先于 child；叙事顺序=ancestry 顺序；tick 单调不降；未混入 seed1/seed3 的身份；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致（并已解释 0→32 的身份变化）；终局与权威报告一致（terminal=`full`，witness=259）；L5 见证是真实 `errant_commit` 而非 `chain_end`；每个单元均给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。

**已知不一致/缺口**：

1. 矩阵把被注入字段写作"VPN tag"，证据显示为 PFN 翻转。
2. 注入事件与 lookup/pfn 的 `request_id`/`dyn_inst_seq` 为空或 0，直到 `cache_access` 才落定 32；本文件已显式解释，不把这一身份切换隐藏掉。
3. 主链没有 `mshr_fill`/`cache_fill`/`mshr_free`（它们在旁支），因此 §2.5 不描述填充状态迁移。
4. `taint_reg` 未记录 `arch_reg`/`phys_reg`，无法给出被污染寄存器号。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/prop_evt.txt.gz` | `8c385db13bfc0a717cd55f1d1749a1c0a329d4e34af067ab21c7d752573fd9de` | 15961 | 2026-10-25T15:59:11 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/chain_report.json` | `9b3a54333722ad6c39fb1ac643cb24881e2e564d14fcdcc680b455a15cfb595a` | 11493 | 2026-10-25T15:59:12 |
| authoritative regrade | `N/A`（无 regrade） | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/run.out` | `6aa8706817b21539a8c88c9beefc1d62542a40c845a5ad9daee18cb181070505` | 2135 | 2026-10-25T15:59:12 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/run.err` | `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f` | 1833 | 2026-10-25T15:59:12 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/stats.txt` | `6eebe8976ef7df1a626234267199bc388d173dbf7041607b76c26a475e15290e` | 382875 | 2026-10-25T15:59:12 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` | `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03` | 1771 | 2026-10-25T16:31:50 |
| 启动命令记录 | run.out 的 `command line:` 行（§1） | 同 run.out | — | — |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | — | — |
| source head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（仅运行时记录） | — | — | — |
| analysis tool | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/board.workload.dmesg` | `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b` | 13938 | 2026-10-25T15:59:11 |
| 辅助证据（terminal） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/board.terminal` | `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db` | 1839 | 2026-10-25T15:59:11 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2`。
- 其它副本：`r6_c9_T01-F0-W4_s2`/`_s1` 内的同名 seed（若存在）为 EXACT_DUPLICATE 或未完成 campaign 副本；`r6_c7` 系列为 OLD_BINARY_REFERENCE；分类以 `R6-AUTHORITATIVE-EVIDENCE.md` 为准。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
