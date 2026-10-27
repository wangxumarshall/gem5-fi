# T01-F2-W4 seed3 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `9ad34b1c…5062`）重建；其余文件只读引用。event_id / tick / 地址 / 位值 / 状态均取自本 seed。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T01-F2-W4`（模型 ID `T01`，单元 `L1d-TLB`） |
| seed / sample_run_id | `3` / `s3` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**单比特** `bit_flip`（`--tlb_fault_type bit_flip`，1 bit） |
| 故障类型 | 单比特翻转 |
| 频率 tier | 请求 `F2` / 生效 `F2` / `lookup_tier_enabled=1` |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`（矩阵 Excel 行 46） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`；`--kernel …/gem5-fs/vmlinux`、`--disk …/gem5-fs/ubuntu.img`、`--bootloader …/gem5-fs/boot.arm64`、`--cpu O3`、`--restore-checkpoint …/fs_cpt_boot/cpt.237949797015` |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T01-F2-W4 --prop_sample_run_id s3` |
| source head | `N/A`（n7 batch manifest 无 `source_head`） |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/manifest.json`（SHA-256 `18df850d6742b884fed7fea5a9a3b529c150849cd9625544cb0b06e6b2858ad7`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n7 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=644136 > 0`，`simTicks=978160860`，等于 `chain_end.tick(238927957875) − checkpoint(237949797015)` |
| 原始事件数 | 2796（`chain_report.event_count=2796`；`fault_event_count=2791`，另有 fault 2 的 5 条） |
| fault_id 数量 | 2（fault 1 主故障；fault 2 是另一页的 L2 含住注入） |
| 是否经过离线 regrade | 否（plain `chain_report.json`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `238095582084`，一条**存储**指令（`dyn_inst_seq=520906`、`request_id=520906`）访问 `0xffffffc009483950`，命中 DTLB 第 `21` 号表项（`entry_index=21`、`walk_id=0`、`way=-1`）。注入前：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75950`。4 KiB 页、偏移 `0x950`，正常 PA `0x81d75950`。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `238095582084`，`VA=0xffffffc009483950`，`dyn_inst_seq=520906`）。`field=bit_flip`，`before=0x81d75`，`after=0x200000081d75`。注入日志 `Mask: 0x200000000000`（`effective: 1`）与异或一致：**只翻转 PFN 的第 45 位**。第 45 位在 48 位 PFN 内，有效 PFN 变成 `0x200000081d75`，偏移 `0x950` 不变，有效 PA 从 `0x81d75950` 变成 `0x200000081d75950`，`effective_pa_changed=1`。第 45 位虽高但未越 48 位，因此不是截断型良性故障，PA 确实改变。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0）记录 `pfn 81d75 → 200000081d75`、`pa 81d75950 → 200000081d75950`，属性未动。`event_id=2`（`tlb_pfn`，parent=1）确认字段替换。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81d75950`、`after=200000081d75950`、`contained=0`、`outcome=NoFault`。无检测、无拦截。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是**存储**：`event_id=4`（`sq_execute`，parent=3）记录 `issued`、`sq_idx=54806`；本 seed 主链上没有 `lsq_push`（流中 `lsq_push` 计数为 0），入队由 `sq_idx=54806` 在 `sq_execute`/`sq_writeback`/`sq_complete` 中重复出现来确认。`event_id=11`（`sq_writeback`，parent=4，Δtick=3330）把 `pa=200000081d75950` 装进写回包（`packet_built`）。输入是错误 PA，内部变化是 `sq_idx=54806` 的发射→构包，输出是带错误地址的包。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=12`（`cache_access`，parent=11）按 `pa=200000081d75950` 访问 L1D，`event_id=13`（`cache_return`）为 `miss`，`event_id=14` 分配 `mshr_id=3`（`cache_line=200000081d75950`）。`event_id=15`（`cache_access`，parent=14，Δtick=333）访问同行的 `pa=200000081d75940`，`event_id=16` 仍 `miss`，`event_id=17` 为 `mshr_id=4` 分配（`cache_line=200000081d75940`）。本 seed 主链上**没有** `mshr_fill`/`mshr_free`（fault 1 分支上 kind 计数为 0），`event_id=68` 的 `resp` 直接以 `mshr_alloc`（17）为 parent；填充/释放段在本 seed 的观测里缺失，按事实标注。两个访问仍落在同一个被改写页基址 `200000081d75` 上，所以是同一故障。

### 2.6 污染如何返回处理器状态

`event_id=68`（`resp`，parent=17，tick `238095693972`，Δtick=108225）把数据送回，`va=200000081d75950`；`event_id=69`（`taint_reg`，parent=68）记录 `before=clean`、`after=tainted`（寄存器号未记录），`event_id=70`（`sq_complete`，parent=69）把 `sq_idx=54806` 的存储标记为 `completed`。`taint_reg` 是存储→CPU 边界：此前是错误地址/数据，此后是体系结构状态被标记为脏。

### 2.7 最终传播终局

真实 L5 是 `event_id=96`（`errant_commit`），parent=`70`，tick `238095695637`（相对 `taint_reg` Δtick=1665），`dyn_inst_seq=520923`（注入指令是 520906，提交的是一条后继指令），`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b27c4`，`commit_seq=394130`。未能在提交前消除：TLB 无校验、L1D/MSHR 正常 miss、SQ/ROB 无地址一致性检查、提交前无 squash。`chain_end`（`event_id=2485`，parent=2454，tick `238927957875`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口，不是 L5。它之所以**体系结构可见**，是因为该指令已在 `commit_seq=394130` 退休（`dyn_inst_seq=520923`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `238095695637` 有 `CHAOS_DETECT: layer=None contained=0 tick=238095695637 ptag=1 reason=errant_commit`，在 `238624437033` 另有 `contained=1 reason=effective_pa_unchanged`（fault 2），最后 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `Kernel oops in guest`。注入 tick `238095582084` → 终局 `238095695637`，传播时延 `113553` ticks。错误 PA 指向另一物理页，污染提交后 guest 内核 oops，仿真以 Crash 退出；不是 Timeout。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483950`、命中第 21 项 | PPN `0x81d75 → 0x200000081d75`（bit45） | PA `0x81d75950 → 0x200000081d75950` | 错误翻译进入流水线 |
| SQ | `sq_idx=54806`、store、错误 PA | 发射→构包 | `packet_built`（`pa=200000081d75950`） | 错误地址固化 |
| L1D | `…5950`/`…5940` | 两次 miss | miss 路径 | 按错误地址取数 |
| MSHR | 行 `200000081d75950`/`…940` | alloc 3、4（本流无 fill/free） | `resp`（68） | 缺失登记正常，无地址合法性检查 |
| PRF/寄存器 | 响应数据 | `clean → tainted` | 污染寄存器 | 存储→CPU 边界 |
| ROB/提交 | 污染寄存器（dyn 520923） | 退休 | `errant_commit`（commit_seq=394130） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end` | 生命周期收口 | 非 L5 |

一句话总结：store 命中被单比特改坏的 TLB 表项（bit45），错误 PA `0x200000081d75950` 经 `sq_idx=54806` 构包后进 L1D，两次 miss 分配 MSHR 3/4（本 seed 未记录 fill/free），响应回来把寄存器标脏并完成存储，最终一条后继指令（dyn 520923）在 `commit_seq=394130` 错误退休，guest 内核 oops，仿真以 Crash 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：2 条 `inj`（fault 1 + fault 2）、2 条 `arm_tlb_lookup_hit`（fault 1：old `0x81d75`、new `0x200000081d75`、`Mask: 0x200000000000`；fault 2：old `0x81d74`、new `0x20000000081d74`、`Mask: 0x20000000000000`）、`stats.numFaultsInjected=2`、`run.out injected=2`；`attempted=272702`、`eligible=272702`、`activated=W3-L0-layer`。代表故障（fault 1）的坏值被实际读取。激活成立。

### 3.2 故障传播类型

**地址型**（错误物理页）。不是数据型、permission、control-state、timing、wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `238095582084`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`；此后 SQ/L1D/MSHR 只是执行，无法不重放地撤销。

### 3.4 检测与掩蔽机制

TLB 无校验；翻译层无合法性检查；L1D/MSHR 只回答命中/缺失；SQ/ROB 无地址一致性检查；提交点不校验。事后 oracle 在 `238095695637` 才报 `errant_commit`。本 seed 的 fault 2 恰好在 L2 被 `effective_pa_unchanged` 含住（第 53 位越 48 位 PFN 被截断），这从反面说明：**只有“翻转位落在 PFN 有效宽度之外”时，现有结构才天然“含住”**；落在 48 位内的 bit45 则完全逃逸。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 96），体系结构可见；运行结局 Crash（内核 oops），故不是 SDC。SDC 需要“对外可见且未被检测到”的错误输出；本样本以 Crash 暴露。无应用级输出 oracle，不能判断数据层面最终正确性；结论限定为“已证真实错误提交 + Crash/DUE”。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 `238085259417`（VA `…2708`，掩码 `0x400000000000`，bit46；`full`），seed2 `238083182163`（VA `…3960`，掩码 `0x2`，bit1；L4 含住）。三者都是单比特；本 seed 与 seed2/seed3 都属于 page `ffffffc009483`，但注入 tick、位号不同。本 seed 的独特处：表项索引 21、bit45、store（`sq_idx=54806`）、终局提交的是后继指令（dyn 520923），并另有一支 fault 2（不同页 `ffffffc009482`，bit53 越界，L2 含住）。本 seed 的数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=96` 经 `parent_event_id` 回溯的单祖先，共 16 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238095582084 | — | inj | L0 | TLB | 1 | origin | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 200000081d75 | 81d75 | 200000081d75 | 0x200000000000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 238095582084 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 200000081d75 | 81d75 | 200000081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=200000081d75;ap=0;mtype=2;page_size=1000;pa=200000081d75950 | — | — | — | — | 命中查询 | PFN 81d75→200000081d75 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 238095582084 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 200000081d75950 | — | — | 81d75 | 200000081d75 | 81d75 | 200000081d75 | — | 81d75950 | 200000081d75950 | — | — | — | — | 表项当前状态 | PA 81d75950→200000081d75950 | 表项存储被改写 |
| 4 | 3 | 2 | 238095582084 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 200000081d75950 | — | — | — | — | 81d75950 | 200000081d75950 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=200000081d75;ap=0;mtype=2;page_size=1000;pa=200000081d75950 | 0 | — | NoFault | — | 表项 PFN | PA 81d75950→200000081d75950 | 首个不可逆点 |
| 5 | 4 | 3 | 238095582084 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | 错误 PA 的 store | 发射（sq_idx=54806） | 进入 SQ |
| 6 | 11 | 4 | 238095585414 | 3330 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 520906 | — | 200000081d75950 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | sq_idx=54806 | 构包 | 错误地址固化为写回包 |
| 7 | 12 | 11 | 238095585414 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 200000081d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483950 | 访问 L1D | 按错误 PA 取数 |
| 8 | 13 | 12 | 238095585414 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 200000081d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 200000081d75950 | miss | cache 无法判别地址合法性 |
| 9 | 14 | 13 | 238095585414 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 200000081d75950 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 200000081d75950 | 分配 MSHR 3 | 错误行进入填充流水 |
| 10 | 15 | 14 | 238095585747 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 200000081d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483950 | 访问 L1D | 按错误 PA 取数 |
| 11 | 16 | 15 | 238095585747 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 200000081d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 200000081d75940 | miss | cache 无法判别地址合法性 |
| 12 | 17 | 16 | 238095585747 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 200000081d75940 | 4 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 200000081d75940 | 分配 MSHR 4 | 错误行进入填充流水 |
| 13 | 68 | 17 | 238095693972 | 108225 | resp | L3 | L1D | 1 | seq_primary | 520906 | 520906 | 200000081d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 14 | 69 | 68 | 238095693972 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 520906 | 520906 | 200000081d75950 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 15 | 70 | 69 | 238095693972 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | 污染响应 | 存储完成（sq_idx=54806） | 错误存储正式完成 |
| 16 | 96 | 70 | 238095695637 | 1665 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 520923 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 520923） | 错误退休（commit_seq=394130） | 真实 L5 |

折叠说明：22 个 `consumer`（event 97–2454，tick `238095695637..238099526136`）全在终局之后，不在 event 96 的祖先上；另有 97 条 `pf_queue`、84 条 `pf_issue`、261 条 `pf_demand` 预取事件也不在主链上。故 Ch.4 无 consumer 行可折叠。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（309 条）**：全部 `L3/addr_fallback_broadcast`，`shared_addr=200000081d75000`、`shared_size=1000`。最早 `event_id=4294967296`，parent=3，`source_event_id=3`、`dest_event_id=5`，把请求 `520906` 分叉成 `520896`；另有从 17 分叉出的 `520907/520912` 等。它们在同一错误页上广播，不在 event 96 的祖先上，也不汇入主链；作用是把错误页扩散到更多请求。

**fault 2**：独立注入 `event_id=2481`，tick `238624437033`，VA `0xffffffc009482860`（**另一个页**，vpn 结尾 9482），`old_pfn=81d74`、`new_pfn=20000000081d74`、`Mask: 0x20000000000000`（第 53 位，高于 48 位 PFN），因此有效 PA 不变；`event_id=2484`（`tlb_translate_result`，contained=1，L2，`effective_pa_unchanged`）与 `chain_end 2486` 记录其 L2 含住。它是 sibling fault，不在代表故障（fault 1）的链上。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、1 条 `resp`、1 条 `taint_reg`；主链外还有 450 条 `cache_access`、450 条 `cache_return`、200 条 `mshr_alloc`、250 条 `mshr_merge`、309 条 `resp`、322 条 `taint_reg`、20 条 `lq_complete`，以及预取事件，均属同一错误页的重复消费者/广播分支，没有回到 event 96 的直接祖先。

**consumer（22 条）**：event 97–2454，全在终局之后，只作为后果列出。**生命周期**：`chain_end` 2485（fault 1）与 2486（fault 2）都是退出回调；2485 的 `outcome=errant_commit_seen` 不是 L5。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`96`，tick=`238095695637`，parent=`70` |
| run outcome | `Crash`（`KERNEL OOPS under fault`） |
| admitted / certified | `True` / `True`；`violations=[]` |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=644136`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级；该文件把 2 个 activated fault 计为 2 行 Crash，与代表故障的 L5 终局是两个层面） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','4','69','96']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T01-F2-W4` = true |
| 判定 | **PASS** |

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3/prop_evt.txt.gz` | `9ad34b1cdac2c26ffba02a237a657d40a21a9d41306e3ba27a7aa99470dd5062` | 94084 | 1793040574 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3/chain_report.json` | `e41ee815fe42db1262f67355df997bead052ec0b4b91fa0366ee1c8dbb9aa6bc` | 15952 | 1793040575 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3/run.out` | `4b09a646a3ed1db15cb8b63b6595bab140b6ec123253da615a05775a1e77d010` | 2633 | 1793040575 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3/run.err` | `de8403ca5671675b258d5cc2e9d99a733336eef03c49490bb0d383150eb6e549` | 1800 | 1793040575 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3/stats.txt` | `fb99f3b3fa972c3bdf66f78f2280155fcea8644c45a1c32de9a147c8ed08e147` | 391042 | 1793040575 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/manifest.json` | `18df850d6742b884fed7fea5a9a3b529c150849cd9625544cb0b06e6b2858ad7` | 1438 | 1793040576 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | — | — |
| 源码 head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3/T01-F2-W4/seed3`。

**其它副本与分类**：`runs/lsu/r6_n6_T01-F2-W4_s3/T01-F2-W4/seed3` 为 **OLD_BINARY_REFERENCE**（binary `e8052842…`）。本文件只使用上表权威目录。
