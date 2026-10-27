# T02-F0-W4 seed3 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `b75d9bf9…e8d4`）重建；其余文件只读引用。event_id / tick / 地址 / 位值 / 状态全部取自本 seed，不借用 seed1/seed2。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T02-F0-W4`（模型 ID `T02`，单元 `L1d-TLB`） |
| seed / sample_run_id | `3` / `s3` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**双比特** `bit_flip`（`--tlb_bits_to_change 2`、`--tlb_fault_type bit_flip`、`--tlb_probability 1.0`） |
| 故障类型 | 双比特翻转 |
| 频率 tier | 请求 `F0` / 生效 `F0` / `lookup_tier_enabled=0` |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`（矩阵 Excel 行 48） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`；`--kernel …/gem5-fs/vmlinux`、`--disk …/gem5-fs/ubuntu.img`、`--bootloader …/gem5-fs/boot.arm64`、`--cpu O3`、`--restore-checkpoint …/fs_cpt_boot/cpt.237949797015` |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T02-F0-W4 --prop_sample_run_id s3` |
| source head（run-time manifest） | `bc82f29d8f69410461d18c07a1ee9314f18885a5` |
| binary source head | `N/A` —— run-level manifest 无 `binary_source_head` 字段 |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json`（SHA-256 `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；manifest `gem5_exit_code=0`、`campaign_exit_code=0`、`done_marker=true`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=382169 > 0`，`simTicks=932242491`，等于 `chain_end.tick(238882039506) − checkpoint(237949797015)` |
| 原始事件数 | 444（`chain_report.event_count=444`；`fault_event_count=444`） |
| fault_id 数量 | 1（`fault_id=1`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`，无 `*regrade*`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `237950233578`，一条**存储**指令（`dyn_inst_seq=31`、`request_id=31`）访问 `0xffffffc009483eb0`，命中 DTLB 第 `0` 号表项（`entry_index=0`、`walk_id=0`、`way=-1`）。注入前状态：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75eb0`。4 KiB 页、页内偏移 `0xeb0`，正常 PA 应为 `0x81d75eb0`；表项有效、全局、ASID=206，权限 `ap=0`、类型 `mtype=2` 均正常。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `237950233578`）记录 `field=bit_flip`、`before=0x81d75`、`after=0x200000000c1d75`、`VA=0xffffffc009483eb0`、`dyn_inst_seq=31`。注入日志 `Mask: 0x20000000040000` 与 `before ^ after` 一致：**同时翻转 PFN 的第 18 位与第 53 位**。第 18 位在 48 位 PFN 内，第 53 位高于 48 位；拼接 PA 时 PFN 只保留低 48 位，第 53 位被截掉，有效 PFN 变成 `0xc1d75`（`0x81d75 ^ 0x40000`，第 18 位置 1），页内偏移 `0xeb0` 不变，有效 PA = `0xc1d75eb0`，`effective_pa_changed=1`。所以：存储的 PFN 两个位都被改写，但只有第 18 位改变了有效 PA；第 53 位是“存储变了、PA 没变”的越界位。这与 `T02` 双比特模型的描述相符。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，同 tick）命中同一表项，`state_before.pfn=81d75`、`state_after.pfn=200000000c1d75`，`state_before.pa=81d75eb0`、`state_after.pa=c1d75eb0`；`valid/global/asid/ap/mtype/page_size` 未动。`event_id=2`（`tlb_pfn`，parent=1）钉死字段变化：`pa=c1d75eb0`、`before=81d75`、`after=200000000c1d75`。`event_id=3`（`tlb_translate_result`，parent=2）把结果交给 LSU：`before=81d75eb0`、`after=c1d75eb0`、`field=effective_pa_changed`、`contained=0`、`outcome=NoFault`。TLB 层没有任何校验/拦截，错误 PA 直接进入 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

这次是**存储**。`event_id=4`（`lsq_push`，parent=3，Δtick=333）明确记录 `field=store`、`sq_idx=1`、`lq_idx=-1`、`pc=ffffffc008011614`、`opcode=strxi_uop`——一个 64/128 位存储微操作进入 SQ 第 1 槽。`event_id=5`（`sq_execute`，parent=4）显示该槽 `issued`（`sq_idx=1`）；`event_id=6`（`sq_writeback`，parent=5，Δtick=1332）把错误 PA `c1d75eb0` 装进写回包（`state_after=packet_built`）。输入是翻译层给出的错误 PA，内部变化是同槽位 `sq_idx=1` 的发射→构包，输出是待访问 L1D 的错误地址；下一级只能消费这个包。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=7`（`cache_access`，parent=6）访问 `pa=c1d75eb0`，`event_id=8`（`cache_return`）为 `miss`；`event_id=9` 分配 `mshr_id=1`（`cache_line=c1d75eb0`）。`event_id=10`（`cache_access`，parent=9，Δtick=333）访问 `pa=c1d75e80`（同一 64B 行），`event_id=11` 仍 `miss`，`event_id=12` 分配 `mshr_id=2`（`cache_line=c1d75e80`）。随后这条 seed **完整记录了填充/释放**：`event_id=64`（`mshr_fill`，parent=12，Δtick=58941）把 mshr 2 标为 `filled`（`fill_id=1`），`event_id=65`（`cache_fill`）以 `pa=c1d75e80` 填行，`event_id=66`（`mshr_free`）释放 mshr 2；紧接着 `event_id=67`（`mshr_fill`，Δtick=666）把 `mshr_id=0` 标为 `filled`（`fill_id=2`），`event_id=68`（`cache_fill`）再次填同一行，`event_id=69`（`mshr_free`）释放 mshr 0。两次 fill 针对同一错误行，说明即使数据真的被取回并放进 cache，cache 也只会回答“这行在哪”，不会回答“这行该不该存在”。整条链仍然是同一个故障：所有地址都派生自同一个被改写的页基址 `0xc1d75`。

### 2.6 污染如何返回处理器状态

`event_id=73`（`resp`，parent=69，tick `237950295516`，Δtick=333）把数据送回，`va=c1d75eb0`。`event_id=74`（`taint_reg`，parent=73）记录 `before=clean`、`after=tainted`、`va=c1d75eb0`（寄存器号本 seed 未记录）。`event_id=75`（`sq_complete`，parent=74）把 `sq_idx=1` 的存储标记为 `completed`，`va=ffffffc009483eb0`。至此错误已从“错误 PA/错误数据”变成“被标脏的体系结构状态”；`taint_reg` 正是存储→CPU 的边界。

### 2.7 最终传播终局

真实 L5 是 `event_id=293`（`errant_commit`），parent=`75`，tick `237951302175`（相对 `taint_reg` Δtick=1,006,659），`dyn_inst_seq=391`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b1000`，`commit_seq=161`。它没能被提前消掉：TLB 无校验、L1D 按错误地址正常 fill、SQ/ROB 无地址一致性检查，本 seed 在提交前没有发生 squash。`chain_end`（event 390，parent=389，tick `238882039506`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口，不是 L5。

注意：本 seed 在提交**之后**还有一条 `squash_masked`（`event_id=319`，parent=294，tick `237951547263`，`va=ffffffc009483e40`，`pa=c1d75e40`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay`）。它发生在 event 293 之后，是终局之后的另一次 squash，按权威口径**不是**终局见证，也不能把本 seed 改判为含住；本 seed 的终局仍是 event 293 的真实 `errant_commit`。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=161` 退休（`dyn_inst_seq=391`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `237951302175` 有 `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`（与 event 293 对齐），其后在 `237951547263` 还有一条 `contained=1 reason=squash_replay`（与 side 事件 319 对齐）；最后是 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`，`run.err` 为 `Kernel oops in guest`。注入 tick `237950233578` → 终局 tick `237951302175`，传播时延 `1,068,597` ticks。因果链：错误 PA 让存储访问到另一个物理页，取回数据经寄存器提交后导致 guest 内核 oops，仿真以 Crash 结束。不是 Timeout。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483eb0`、命中第 0 项 | PPN `0x81d75 → 0xc1d75`（bit18；bit53 越界被截） | PA `0x81d75eb0 → 0xc1d75eb0`，`contained=0` | 错误翻译直接交付 |
| SQ | `sq_idx=1`、store、错误 PA | push → execute → writeback | `packet_built`（`pa=c1d75eb0`） | 错误地址固化为存储请求 |
| L1D | 错误页内 `…eb0`/`…e80` | 两次 miss，两次 fill | 行填充（`pa=c1d75e80`） | cache 按错误地址真实填充 |
| MSHR | 行 `c1d75eb0` / `c1d75e80` | alloc 1/2 → fill/fill → free | `resp`（event 73） | 缺失/填充全流程正常，不判别地址合法性 |
| PRF/寄存器 | 响应数据 | `clean → tainted` | 污染寄存器 | 错误进入体系结构状态 |
| ROB/提交 | 污染寄存器（dyn 391） | 退休 | `errant_commit`（commit_seq=161） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end` | 生命周期收口 | 非 L5；另有提交后 squash 319 不改变终局 |

一句话总结：一条 store 命中被双比特改坏的 TLB 表项（bit18 生效、bit53 截断），错误 PA `0xc1d75eb0` 经 `sq_idx=1` 的 push→execute→writeback 送进 L1D，两次 miss 后由 MSHR 1/2 走完 alloc→fill→free，响应把寄存器标脏，最终 `dyn_inst_seq=391` 在 `commit_seq=161` 错误退休并触发内核 oops；提交之后虽然还有一次 squash（event 319），但它不改变本 seed 的 L5 终局。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：`prop_evt` 1 条 `inj`，`armtlb_injections.log` 1 条 `arm_tlb_lookup_hit`（old `0x81d75`、new `0x200000000c1d75`、`Mask: 0x20000000040000`），`stats.txt` `numFaultsInjected=1`，`run.out` `injected=1`；`attempted=150170`、`eligible=1`、`activated=W3-L0-layer`。坏值被下游读取：`tlb_lookup.state_after.pfn`、`tlb_pfn.after`、`lsq_push` 之后的 `sq_writeback.pa`、`cache_access.pa` 都是 `0xc1d75…`。激活成立。

### 3.2 故障传播类型

**地址型**。传播的是 PA（错误物理页）；数据本身没有被翻转。表现为 cache 对错误页的真实 miss/fill，最终以污染寄存器形式进入体系结构状态。不是 permission、不是 control-state、不是 timing、不是 wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `237950233578`）：错误 PA 作为本请求的有效翻译结果交付给 LSU，`contained=0`、`outcome=NoFault`；此后 SQ/L1D/MSHR 只是执行。严格说 `event_id=2` 已把坏值写进表项，但真正不可撤销的是它被当作有效翻译使用的那一刻。

### 3.4 检测与掩蔽机制

TLB 无校验；翻译结果层无合法性检查；L1D 的 fill 只证明“数据取到了”，不证明“地址是对的”；MSHR 只做缺失管理；SQ/ROB 无一致性检查；提交点不校验。事后 oracle 在 `237951302175` 报 `errant_commit`。提交后 `237951547263` 的 squash（event 319）说明后续同一错误页的 load 确实被 RAS 类机制 squash 掉，但它发生在错误已经提交之后，不能改变终局，也说明“squash 只能清理后续消费，不能撤销已提交的错误”。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 293），体系结构可见；运行结局为 Crash（内核 oops），故不是 SDC。SDC 要求“对外可见且未被检测到”的错误输出；本样本的错误被 Crash 显式暴露。应用级输出 oracle 不存在，因此不能判断“若没有崩溃，数据是否最终正确”，只能限定结论为：已证真实错误提交 + Crash/DUE。提交后的 squash（event 319）不能被写成含住，也不能被写成 L5；它只是终局之后的一次事件。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 `237950940537`（VA `…3fa8`，掩码 `0x100040000000000`，位 42/56），seed2 `237950233911`（VA `…3eb8`，掩码 `0x1000000800000000`，位 35/60），本 seed `237950233578`（VA `…3eb0`，掩码 `0x20000000040000`，位 18/53）。三者均双比特、单 fault、`full`、Crash；均有一个高位被 48 位 PFN 截断。差别：本 seed 是 store（`strxi_uop`、`sq_idx=1`）且流里完整记录了 fill/free，还在提交后多了一次 squash；seed1 也是 store（`sq_idx=32`）但无 fill/free 记录；seed2 无 LQ/SQ 记录。本 seed 的数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=293` 经 `parent_event_id` 回溯的单祖先，共 23 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | — | inj | L0 | TLB | 1 | origin | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 200000000c1d75 | 81d75 | 200000000c1d75 | 0x20000000040000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 237950233578 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 200000000c1d75 | 81d75 | 200000000c1d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=200000000c1d75;ap=0;mtype=2;page_size=1000;pa=c1d75eb0 | — | — | — | — | 命中查询 | PFN 81d75→200000000c1d75 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 237950233578 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | c1d75eb0 | — | — | 81d75 | 200000000c1d75 | 81d75 | 200000000c1d75 | — | 81d75eb0 | c1d75eb0 | — | — | — | — | 表项当前状态 | PA 81d75eb0→c1d75eb0 | 表项存储被改写 |
| 4 | 3 | 2 | 237950233578 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | c1d75eb0 | — | — | — | — | 81d75eb0 | c1d75eb0 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=200000000c1d75;ap=0;mtype=2;page_size=1000;pa=c1d75eb0 | 0 | — | NoFault | — | 表项 PFN | PA 81d75eb0→c1d75eb0 | 首个不可逆点 |
| 5 | 4 | 3 | 237950233911 | 333 | lsq_push | — | LSQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | store | store 入队（sq_idx=1） | 错误进入队列 |
| 6 | 5 | 4 | 237950233911 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | 错误 PA 的 store | 发射（sq_idx=1） | 进入 SQ |
| 7 | 6 | 5 | 237950235243 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 31 | — | c1d75eb0 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | sq_idx=1 | 构包 | 错误地址固化为写回包 |
| 8 | 7 | 6 | 237950235243 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | c1d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483eb0 | 访问 L1D | 按错误 PA 取数 |
| 9 | 8 | 7 | 237950235243 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | c1d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 c1d75eb0 | miss | cache 无法判别地址合法性 |
| 10 | 9 | 8 | 237950235243 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | c1d75eb0 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 c1d75eb0 | 分配 MSHR 1 | 错误行进入填充流水 |
| 11 | 10 | 9 | 237950235576 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | c1d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483eb0 | 访问 L1D | 按错误 PA 取数 |
| 12 | 11 | 10 | 237950235576 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | c1d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 c1d75e80 | miss | cache 无法判别地址合法性 |
| 13 | 12 | 11 | 237950235576 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | c1d75e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 c1d75e80 | 分配 MSHR 2 | 错误行进入填充流水 |
| 14 | 64 | 12 | 237950294517 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | c1d75e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 2 填充（fill_id=1） | 错误行取回 |
| 15 | 65 | 64 | 237950294517 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | c1d75e80 | c1d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 16 | 66 | 65 | 237950294517 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | c1d75e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 缺失处理结束 |
| 17 | 67 | 66 | 237950295183 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | c1d75e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 0 填充（fill_id=2） | 错误行取回 |
| 18 | 68 | 67 | 237950295183 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | c1d75e80 | c1d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 19 | 69 | 68 | 237950295183 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | c1d75e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 0 | 缺失处理结束 |
| 20 | 73 | 69 | 237950295516 | 333 | resp | L3 | L1D | 1 | seq_primary | 31 | 31 | c1d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 21 | 74 | 73 | 237950295516 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 31 | 31 | c1d75eb0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 22 | 75 | 74 | 237950295516 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | 污染响应 | 存储完成（sq_idx=1） | 错误存储正式完成 |
| 23 | 293 | 75 | 237951302175 | 1006659 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 391） | 错误退休（commit_seq=161） | 真实 L5 |

折叠说明：61 个 `consumer`（event 294–389，tick `237951302175..237964934862`）全部在终局之后，不在 event 293 的祖先上，故 Ch.4 无 consumer 行；`squash_masked`（319）也不在主链上，列在 Ch.5。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（53 条）**：全部 `bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`，`shared_addr=c1d75000`、`shared_size=1000`。最早 `event_id=4294967296`，parent=12，`source_event_id=12`、`dest_event_id=13`，把请求 `31` 分叉成 `32`；后续从 12 分叉出 `34/35…`。它们在同一个错误页上广播，不在 event 293 的祖先上，也不汇入主链；作用是扩大错误页的消费面，不改变终局。

**提交后的 squash（event 319）**：`kind=squash_masked`，parent=294（终局之后的 consumer），tick `237951547263`，`dyn_inst_seq=520`，`va=ffffffc009483e40`，`pa=c1d75e40`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay`。它证明同一错误页的后续 load 会被 squash，但它发生在 event 293 的真实提交之后，**不能**把本 seed 改判为 detected_contained，也**不能**当作 L5；它只是终局后的事件。`run.out` 对应行也单独打了一条 `contained=1 reason=squash_replay`。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、2 条 `mshr_fill`、2 条 `cache_fill`、2 条 `mshr_free`、1 条 `resp`、1 条 `taint_reg`；主链外还有 59 条 `cache_access`、59 条 `cache_return`、12 条 `mshr_alloc`、30 条 `mshr_merge`、12 条 `mshr_fill`、12 条 `cache_fill`、12 条 `mshr_free`、52 条 `resp`、53 条 `taint_reg`、4 条 `lq_complete`，均属同一错误页的重复消费者/广播分支，不重新成为 event 293 的直接祖先。

**consumer（61 条）**：event 294–389，全部在终局之后，只作为后果列出。**生命周期**：`chain_end`（390）parent=389，tick `238882039506`，`corr=none`、`outcome=errant_commit_seen`，其 `containment_reason=squash_replay` 只是退出回调携带的上下文字段，不构成含住。本 seed 只有 1 个 fault。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`293`，tick=`237951302175`，parent=`75`，`detection_layer=L5`，`outcome=errant_commit` |
| run outcome | `Crash`（`CHAOS_DETECT reason=errant_commit` + 后续 squash_replay；`KERNEL OOPS under fault`） |
| admitted | `True`（`path=full_chain`，`violations=[]`） |
| certified | `True` |
| violations | `[]` |
| truncated | `False`；gzip EOF 正常 |
| stats 有效性 | 有效（`simInsts=382169`，`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','5','74','293']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T02-F0-W4` = true |
| 判定 | **PASS** |

说明：提交后的 squash（event 319）不影响 L5 终局；`chain_end`（390）只是生命周期收口。传播终局（L5）与运行结局（Crash）分开陈述，二者同向、无 Timeout。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3/prop_evt.txt.gz` | `b75d9bf97fbf6476f137af49a1612a1e1a205c42db0c3df5bfb29a51cf54e8d4` | 16778 | 1792917168 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3/chain_report.json` | `a41ec6417187630ba0ae9f6d1f2d92501dbb5e18f01699aef0bc6284d99aceb2` | 10701 | 1792917169 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3/run.out` | `0fe79af194bdfda02059e68b105d8eefbf060561681607861bf1508b885b71d4` | 2249 | 1792917169 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3/run.err` | `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f` | 1833 | 1792917169 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3/stats.txt` | `ab734396d9c85ed527ef651dbeb0cfdad4d3e003719a7c558aed4e7087ae732b` | 381642 | 1792917168 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json` | `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef` | 1773 | 1792917170 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | — | — |
| 源码 head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（run-time worktree HEAD） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed3`。

**其它副本与分类**：`runs/lsu/r6_p1_T02-F0-W4/T02-F0-W4/seed3`、`runs/lsu/r6_w1_T02-F0-W4/T02-F0-W4/seed3` 为 **INTERRUPTED**（无 `.done`/`.exit_code`）。本文件只使用上表权威目录。
