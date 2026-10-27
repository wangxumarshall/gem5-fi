# T01-F2-W4 seed1 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `feaa5ebf…efdfc`）重建；`chain_report.json`、`manifest.json`、`run.out`、`run.err`、`stats.txt`、`armtlb_injections.log` 均按只读引用。所有 event_id / tick / 地址 / 位值 / 状态只来自本 seed。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T01-F2-W4`（模型 ID `T01`，单元 `L1d-TLB`） |
| seed / sample_run_id | `1` / `s1` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项的 PPN 做**单比特** `bit_flip`（`--tlb_fault_type bit_flip`，无 `--tlb_bits_to_change`，即 1 bit；`--tlb_probability 1.0`） |
| 故障类型 | 单比特翻转 |
| 频率 tier | 请求 `F2` / 生效 `F2` / `lookup_tier_enabled=1`（`CHAOS_LSU_TIER_CAP`） |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`（矩阵 Excel 行 46） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`；`--kernel …/gem5-fs/vmlinux`、`--disk …/gem5-fs/ubuntu.img`、`--bootloader …/gem5-fs/boot.arm64`、`--cpu O3`、`--restore-checkpoint …/fs_cpt_boot/cpt.237949797015` |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T01-F2-W4 --prop_sample_run_id s1` |
| source head | `N/A`（n7 batch manifest 无 `source_head` 字段） |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c`（manifest 记录） |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/manifest.json`（SHA-256 `4bc8b3afdd83c5f784d00f7c9f1f3a579c9e8a4fa25fd4b51c4f2d3036a94c31`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n7 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=239900 > 0`，`simTicks=140821704`，等于 `chain_end.tick(238090618719) − checkpoint(237949797015)` |
| 原始事件数 | 1100（`chain_report.event_count=1100`；`fault_event_count=1100`） |
| fault_id 数量 | 1（`fault_id=1`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`，无 `*regrade*`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `238085259417` 之前，一条 **load**（`dyn_inst_seq=415526`、`request_id=415526`）访问 `0xffffff8001362708`，命中 DTLB 第 `13` 号表项（`entry_index=13`、`walk_id=0`、`way=-1`）。注入前表项：`vpn=ffffff8001362; asid=206; valid=1; global=1; pfn=81362; ap=0; mtype=2; page_size=1000; pa=81362708`。4 KiB 页、偏移 `0x708`，正常 PA `0x81362708`；表项有效、全局、ASID=206，权限与内存类型正常。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `238085259417`，`VA=0xffffff8001362708`，`dyn_inst_seq=415526`、`request_id=415526`）。`field=bit_flip`，`before=0x81362`，`after=0x400000081362`。注入日志 `Mask: 0x400000000000`（`effective: 1`）与异或结果一致：**只翻转 PFN 的第 46 位**。第 46 位在 48 位 PFN 内，因此直接改变有效 PFN：`0x81362 ^ 0x400000000000 = 0x400000081362`；偏移 `0x708` 不变，有效 PA 从 `0x81362708` 变成 `0x400000081362708`，`effective_pa_changed=1`。注意这里虽然 PFN 高位被置 1，但第 46 位仍在 48 位 PFN 有效范围内，所以**不是**“越界被截断、PA 不变”的良性情形——有效 PA 确实改变。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，同 tick）记录命中查询与表项前后状态：`pfn 81362 → 400000081362`，`pa 81362708 → 400000081362708`；`valid/global/asid/ap/mtype/page_size` 未动。`event_id=2`（`tlb_pfn`，parent=1）确认 `field=bit_flip`、`state_before=81362708`、`state_after=400000081362708`。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81362708`、`after=400000081362708`、`field=effective_pa_changed`、`contained=0`、`outcome=NoFault`。TLB 层没有任何校验或拦截。

### 2.4 错误如何进入 LQ/SQ/LSQ

这次是 **load**：`event_id=4`（`lq_read`，parent=3）记录 `lq_idx=44911`、`dyn_inst_seq=415526`、`request_id=415526`。本 seed 的主链上没有 `lsq_push`（流中该 kind 计数为 0），入队只能由 `lq_read`/`lq_complete` 共享同一 `lq_idx=44911` 来确认。`lq_read` 的输入是翻译结果给出的错误 PA，内部变化是把该 load 绑定到 LQ 第 44911 槽并发起读取，输出是等待 cache/MSHR 响应的 load 请求——下一级 cache 只能按错误 PA 服务。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=5`（`cache_access`，parent=4）以 `pa=400000081362708` 访问 L1D，`event_id=6`（`cache_return`）为 `miss`，`event_id=7` 分配 `mshr_id=1`（`cache_line=400000081362708`）。`event_id=8`（`cache_access`，parent=7，Δtick=333）访问同行的 `pa=400000081362700`，`event_id=9` 仍 `miss`，`event_id=10` 分配 `mshr_id=2`（`cache_line=400000081362700`）。本 seed 的流**没有** `mshr_fill`/`mshr_free` 记录（kind 计数为 0），`event_id=14` 的 `resp` 直接以 `mshr_alloc`（10）为 parent——填充/释放这段在本 seed 的观测里缺失，按事实标注，不虚构。为什么仍是同一故障：两个 cache 访问的 PA 都落在 `0x400000081362` 这一个被改写的页基址上，MSHR 行地址由它派生。

### 2.6 污染如何返回处理器状态

`event_id=14`（`resp`，parent=10，tick `238085367975`，Δtick=108225）把数据送回，`va=400000081362708`；`event_id=15`（`lq_complete`，parent=14，`lq_idx=44911`）完成该 load；`event_id=16`（`taint_reg`，parent=15）记录 `before=clean`、`after=tainted`，`arch_reg=4`、`phys_reg=42`，`va=400000081362708`。`taint_reg` 是存储→CPU 边界：此前错误是错误地址/取回数据，此后它是被标记为脏的具体物理寄存器 42（体系结构寄存器 4），后续消费该寄值的指令都会携带污染。

### 2.7 最终传播终局

真实 L5 是 `event_id=20`（`errant_commit`），parent=`16`，tick `238085368641`（相对 `taint_reg` Δtick=666），`dyn_inst_seq=415526`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b27ac`，`commit_seq=293614`。为什么没被提前消掉：TLB 无校验、L1D/MSHR 按错误地址正常 miss、LQ/ROB 无地址一致性检查，提交前没有 squash。`chain_end`（`event_id=975`，parent=974，tick `238090618719`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口，不是 L5。它之所以**体系结构可见**，是因为该指令已在 `commit_seq=293614` 退休（`dyn_inst_seq=415526`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `238085368641` 有 `CHAOS_DETECT: layer=None contained=0 tick=238085368641 ptag=1 reason=errant_commit`，随后 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `src/kern/linux/events.cc:64: warn: Kernel panic in simulated kernel`。注入 tick `238085259417` → 终局 `238085368641`，传播时延 `109224` ticks。错误 PA 指向另一个物理页，污染经寄存器 42 提交后 guest 内核 panic，仿真以 Crash 退出；不是 Timeout。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffff8001362708`、命中第 13 项 | PPN `0x81362 → 0x400000081362`（bit46） | PA `0x81362708 → 0x400000081362708`，`contained=0` | 错误翻译进入流水线 |
| LQ | `lq_idx=44911`、load、错误 PA | 绑定槽位并发起读取 | 等待响应的 load | 错误地址进入 LQ |
| L1D | `…2708`/`…2700` | 两次 miss | miss 路径 | 按错误地址取数 |
| MSHR | 行 `400000081362708`/`…2700` | alloc 1、2（本流无 fill/free） | `resp`（14） | 缺失登记正常，无地址合法性检查 |
| PRF/寄存器 | 响应数据 | `clean → tainted`（arch 4 / phys 42） | 污染寄存器 | 存储→CPU 边界 |
| ROB/提交 | 污染寄存器（dyn 415526） | 退休 | `errant_commit`（commit_seq=293614） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end` | 生命周期收口 | 非 L5 |

一句话总结：一次 load 命中被单比特改坏的 TLB 表项（bit46），错误 PA `0x400000081362708` 进入 LQ 第 44911 槽，L1D 两次 miss、分配 MSHR 1/2（本 seed 未记录 fill/free），响应回来把物理寄存器 42（体系结构 x4）标脏，最终注入指令本体在 `commit_seq=293614` 错误提交，guest 内核 panic，仿真以 Crash 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：1 条 `inj`（fault_id=1）、1 条 `arm_tlb_lookup_hit`（old `0x81362`、new `0x400000081362`、`Mask: 0x400000000000`、`effective: 1`）、`stats.numFaultsInjected=1`、`run.out injected=1`；`attempted=110149`、`eligible=110149`、`activated=W3-L0-layer`。坏值被实际读取（`tlb_pfn.after`、`cache_access.pa`）。激活成立。

### 3.2 故障传播类型

**地址型**（错误物理页）。不是数据型、不是 permission、不是 control-state、不是 timing、不是 wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `238085259417`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`；在此之前 `event_id=2` 只是存储被改写，此后错误已进入执行路径，无法不重放地撤销。

### 3.4 检测与掩蔽机制

TLB 无校验；翻译层无合法性检查；L1D/MSHR 只回答命中/缺失；LQ/ROB 无地址一致性检查；提交点不校验。唯一“检测”是事后 oracle（`CHAOS_DETECT reason=errant_commit`）。盲区：**48 位 PFN 内的位翻转在提交前完全不可见**，直到内核 panic 才以 Crash 暴露。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 20），体系结构可见；运行结局 Crash（内核 panic），故不是 SDC。SDC 需要“对外可见且未被检测到”的错误输出；本样本以 Crash 暴露。无应用级输出 oracle，不能判断数据层面最终正确性；结论限定为“已证真实错误提交 + Crash/DUE”。

### 3.6 与同 RunID 其他 seed 的关系

seed2 注入 `238083182163`（VA `…3960`，掩码 `0x2`，bit1；终局为 L4 含住），seed3 `238095582084`（VA `…3950`，掩码 `0x200000000000`，bit45；`full`）。三者都是单比特、都只有一个代表 fault（seed2/seed3 还有一支独立的 L2 含住 fault）。本 seed 的独特处：表项索引 13（seed2/seed3 为 21）、PA 改变落在 bit46、终局是注入指令本体（`dyn_inst_seq=415526`）而非后继指令。本 seed 的数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=20` 经 `parent_event_id` 回溯的单祖先，共 15 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | — | inj | L0 | TLB | 1 | origin | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 400000081362 | 81362 | 400000081362 | 0x400000000000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 238085259417 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 400000081362 | 81362 | 400000081362 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=400000081362;ap=0;mtype=2;page_size=1000;pa=400000081362708 | — | — | — | — | 命中查询 | PFN 81362→400000081362 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 238085259417 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | 81362 | 400000081362 | 81362 | 400000081362 | — | 81362708 | 400000081362708 | — | — | — | — | 表项当前状态 | PA 81362708→400000081362708 | 表项存储被改写 |
| 4 | 3 | 2 | 238085259417 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | — | — | 81362708 | 400000081362708 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=400000081362;ap=0;mtype=2;page_size=1000;pa=400000081362708 | 0 | — | NoFault | — | 表项 PFN | PA 81362708→400000081362708 | 首个不可逆点 |
| 5 | 4 | 3 | 238085259417 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误翻译 | load 读取（lq_idx=44911） | 错误地址进入 LQ |
| 6 | 5 | 4 | 238085259417 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffff8001362708 | 访问 L1D | 按错误 PA 取数 |
| 7 | 6 | 5 | 238085259417 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 400000081362708 | miss | cache 无法判别地址合法性 |
| 8 | 7 | 6 | 238085259417 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 400000081362708 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 400000081362708 | 分配 MSHR 1 | 错误行进入填充流水 |
| 9 | 8 | 7 | 238085259750 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 400000081362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffff8001362708 | 访问 L1D | 按错误 PA 取数 |
| 10 | 9 | 8 | 238085259750 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 400000081362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 400000081362700 | miss | cache 无法判别地址合法性 |
| 11 | 10 | 9 | 238085259750 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 400000081362700 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 400000081362700 | 分配 MSHR 2 | 错误行进入填充流水 |
| 12 | 14 | 10 | 238085367975 | 108225 | resp | L3 | L1D | 1 | seq_primary | 415526 | 415526 | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 13 | 15 | 14 | 238085367975 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应 | load 完成（lq_idx=44911） | 错误 load 完成 |
| 14 | 16 | 15 | 238085367975 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 415526 | 415526 | 400000081362708 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏（arch=4/phys=42） | 存储→CPU 边界 |
| 15 | 20 | 16 | 238085368641 | 666 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 415526 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 415526） | 错误退休（commit_seq=293614） | 真实 L5 |

折叠说明：106 个 `consumer`（event 21–974，tick `238085368974..238090493178`）全部在终局之后，不在 event 20 的祖先上，故 Ch.4 无 consumer 行可折叠；不可折叠事件逐条保留。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（124 条）**：全部 `L3/addr_fallback_broadcast`，`shared_addr=400000081362000`、`shared_size=1000`（4 KiB 页）。最早 `event_id=4294967296`，parent=10，`source_event_id=10`、`dest_event_id=11`，把请求 `415526` 分叉成 `415576`；另从 event 16 分叉出多条（如 `415656`、`415700`）。它们都在同一错误页上广播，不在 event 20 的祖先上，也不重新汇入主链；影响是扩大错误页消费面，不改变终局。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、1 条 `lq_complete`、1 条 `resp`、1 条 `taint_reg`；主链外还有 167 条 `cache_access`、167 条 `cache_return`、86 条 `mshr_alloc`、81 条 `mshr_merge`、118 条 `resp`、117 条 `lq_complete`、118 条 `taint_reg`，均属同一错误页的重复消费者/广播分支，没有回到 event 20 的直接祖先。

**consumer（106 条）**：event 21–974，tick `238085368974..238090493178`，全部是终局之后的污染传播记录（`corr=taint_prop`），只作为后果列出。**生命周期**：`chain_end`（975）parent=974，tick `238090618719`，`corr=none`、`contained=1`、`outcome=errant_commit_seen`；它是退出回调，不是 L5、不是含住。本 seed 没有 `squash_masked`、没有第二支注入、没有其它 `errant_commit`。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`20`，tick=`238085368641`，parent=`16` |
| run outcome | `Crash`（`KERNEL PANIC under fault`） |
| admitted / certified | `True` / `True`；`violations=[]` |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=239900`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','4','16','20']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T01-F2-W4` = true |
| 判定 | **PASS** |

说明：传播终局（L5）与运行结局（Crash）分开陈述；本 seed 无 Timeout，`chain_end` 未被用于层级判定。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1/prop_evt.txt.gz` | `feaa5ebf6df37bf9438bc7e024e30089812e9a7b87117040badb7f91b38efdfc` | 37584 | 1793040243 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1/chain_report.json` | `bd04a71abac4374c5407b41ba54a63561e0e0c348253118d27e5296dea1cd08b` | 17742 | 1793040244 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1/run.out` | `275b1e58a19d9b6af1813839f6b723c56bd7e05a62138f9bf96366b62a5fafbe` | 2531 | 1793040244 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1/run.err` | `7a1330e20fb7778733f12c6460b3c22084fd40bf86f1a114fee02156ded9bbb6` | 1812 | 1793040244 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1/stats.txt` | `18ca3bd46d79a1ed82143b894e981003ad17fab206a59d64b415dc072ba6e03b` | 388359 | 1793040244 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/manifest.json` | `4bc8b3afdd83c5f784d00f7c9f1f3a579c9e8a4fa25fd4b51c4f2d3036a94c31` | 1438 | 1793040245 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | — | — |
| 源码 head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s1/T01-F2-W4/seed1`。

**其它副本与分类**：`runs/lsu/r6_n6_T01-F2-W4_s1/T01-F2-W4/seed1` 为 **OLD_BINARY_REFERENCE**（binary `e8052842…` ≠ 权威 `8a229009…`，prop_evt SHA 不同）。本文件只使用上表权威目录。
