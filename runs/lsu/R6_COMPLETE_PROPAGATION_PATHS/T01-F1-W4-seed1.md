# T01-F1-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F1-W4` |
| seed | `1` |
| sample_run_id | `s1` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F1` |
| requested tier | `F1` |
| effective tier | `F1` |
| tier enabled | `开启(1)`（`CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1`） |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（与矩阵标签一致：该 rcS 即 TLB page-walk 探针） |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s1/T01-F1-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T01-F1-W4 --prop_sample_run_id s1` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`（与 manifest `binary_sha_expected` 一致） |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s1/T01-F1-W4/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s1/manifest.json`（`exit_code=null`；真实退出码 `.exit_code`=0） |
| 正常 EOF | **是**（解压后 2,161,247 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=3316459554`、`simInsts=3663280`、`finalTick=241266256569` |
| 原始事件数 | `3091` |
| fault_id 数量 | `1` |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`；run.out 另有 `CHAOS_LSU_F6_EVENTS: TlbHit=2383421 SqForward=191232 DirtyEviction=277038 CasSuccess=1390348`（该构建的 F6 事件计数，属负载侧统计，不是本故障链）。

## 2. 完整故障传播过程：从注入到最终结局

终局是真实 L5：`errant_commit`（`event_id=69`，tick=`239595975522`）。祖先链 16 条：

`0 → 1 → 2 → 3 → 4(sq_execute) → 5(sq_writeback) → 6 → 7 → 8 → 9 → 10 → 11 → 45(resp) → 46(taint_reg) → 47(sq_complete) → 69(errant_commit)`

tick 段：239595855309、239595856641、239595856974、239595965199、239595975522，单调不降。本链的 resp（45）直接以 `mshr_alloc`（11）为父，**fill 不在主链上**（旁支有 2 条 `mshr_fill`/`cache_fill`/`mshr_free`），因此本节不描述主链未发生的填充状态迁移。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=5368746`、`request_id=5368746`，VA=`0xffffffc009483b48`（页内偏移 `0xb48`）。目标表项 `entry_index=20`、`way=-1`、`walk_id=0`；注入前 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75b48`。本链含 `sq_execute`/`sq_writeback`/`sq_complete`，说明这是 **store** 路径。

### 2.2 故障具体如何注入

`event_id=0`，tick=`239595855309`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=5368746`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x400000000000`，即 PFN 第 46 位。原 PFN `0x81d75` 异或后得 `0x400000081d75`：把数值变化讲完整——第 46 位由 0 变 1，表项保存的 PFN 从 `0x81d75` 变成 `0x4000_0008_1d75`，其余位不变。第 46 位在物理地址中对应第 58 位；本 seed 的证据（`tlb_pfn` 的 `pa`）显示有效物理地址确实变成了 `0x400000081d75b48`，`tlb_translate_result` 也判定 `effective_pa_changed`。**因此本 seed 属于"有效 PA 改变"的案例**，而不是"高位被截断抵消"的案例；本文按证据记录这一点，不对地址宽度细节作额外推断。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`239595855309`，`request_id=5368746`，`corr=seq_primary`，`entry_index=20`）记录 `field=post_lookup`，`before=81d75`、`after=400000081d75`；state 对照 `pfn=81d75→400000081d75`、`pa=81d75b48→400000081d75b48`。
`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=400000081d75b48`、`state_before=81d75b48`、`state_after=400000081d75b48`。
`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）：`field=effective_pa_changed`、`before=81d75b48`、`after=400000081d75b48`、`contained=0`、`outcome=NoFault`。翻译本身无 fault，但因 PA 改变而不含住；错误 PA 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

`event_id=4`（`sq_execute`，parent=3，tick=`239595855309`，`sq_idx=479071`，`state_before=issued`）表明错误 PA 所在的 store 已在 SQ 内执行；`event_id=5`（`sq_writeback`，parent=4，tick=`239595856641`，`pa=400000081d75b48`，`state_after=packet_built`）构建访存 packet；`event_id=6`（`cache_access`，parent=5）以该 PA 发出。`lsq_push` 缺席，故"插入 LSQ 的时刻"为 `N/A`（证据缺席）；SQ 内 execute→writeback→complete 完整。

### 2.5 错误如何经过 cache 和 MSHR

- 第一次：`event_id=6`（`cache_access`，parent=5，tick=`239595856641`，`request_id=5368746`）访问 `pa=400000081d75b48`；`event_id=7`（`cache_return`）`field=miss`；`event_id=8`（`mshr_alloc`）`cache_line=400000081d75b48`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=9`（`cache_access`，parent=8，tick=`239595856974`）访问同一行基址 `pa=400000081d75b40`；`event_id=10` `miss`；`event_id=11`（`mshr_alloc`）`cache_line=400000081d75b40`、`mshr_id=2`、`state_after=mshr_allocated`。
- 返回：`event_id=45`（`resp`，parent=11，tick=`239595965199`，`request_id=5368746`，`corr=seq_primary`，`va=400000081d75b48`）。

两次未命中、两次分配说明该错误行不在 L1D；主链没有 fill/free，故不从主链描述它们。同一 fault 的依据：`fault_id=1`、parent 连续、两次访问同属错误 PA 所在行（`...b48` 与行基址 `...b40`）。旁支中还有 95 条 `pf_queue`、87 条 `pf_issue`、275 条 `pf_demand`、1 条 `pf_fill` 等预取事件（§5），它们不属于本次翻译的祖先。

### 2.6 污染如何返回处理器状态

`event_id=46`（`taint_reg`，parent=45，tick=`239595965199`，`request_id=5368746`，`corr=seq_primary`，`va=400000081d75b48`）记录 `before=clean`、`after=tainted`、`dyn_inst_seq=5368746`。这是存储→CPU 边界。`event_id=47`（`sq_complete`，parent=46，`sq_idx=479071`，`state_after=completed`）收口 store 生命周期。证据限制：`taint_reg` 无 `arch_reg`/`phys_reg`。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=69`，parent=47，tick=`239595975522`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=5368813`、`pc=ffffffc0081e6204`、`commit_seq=3579740`。错误提交是更年轻的 `5368813`（最初访问是 `5368746`），说明污点沿寄存器依赖传播后才兑现。为什么没被提前消除：L2 `contained=0`，本 seed 没有 `squash_masked`，提交前无拦截。`chain_end`（`event_id=2741`，tick=`241266256569`，`outcome=errant_commit_seen`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out：

- `CHAOS_DETECT: layer=None contained=0 tick=239595975522 ptag=1 reason=errant_commit`
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.160000] Call trace:`
- `[2.160000] Unable to handle kernel paging request at virtual address 0020000000000000`
- `[2.160000] Internal error: Oops: 86000004 [#1] PREEMPT SMP`

注入 tick=`239595855309`，错误提交 tick=`239595975522`，传播延迟 **120,213 ticks**。L5→Crash 因果成立。链终止 tick=`241266256569`。无应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit46 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=5368746） | 读到 `pfn=400000081d75` | PA=`400000081d75b48` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=400000081d75b48` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L3 SQ | store（`sq_idx=479071`） | execute→writeback | packet | 错误地址随包发出 |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | 分配 MSHR 1/2 | `mshr_alloc` | 请求挂起 |
| L3 L1D→core resp | MSHR 2 请求 | 返回 | `resp`（req=5368746） | 污染回到核心 |
| L4 taint/regfile | response | clean→tainted | 污染状态 | 存储→CPU 边界 |
| L3 SQ complete | store 完成 | completed | 条目收口 | store 结束 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=5368813` | 架构可见错误 |
| LQ / LSQ push / fill | — | — | — | `N/A`（无对应主链事件） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 46 位置 1，PA 由 `0x81d75b48` 变为 `0x400000081d75b48`；翻译结果记录 `effective_pa_changed/contained=0`，store 经 SQ（`sq_idx=479071`）发出，错误地址在 L1D 两次未命中并分配 MSHR 1/2，`resp` 与 `taint_reg` 把污点带入寄存器，最终由更年轻的指令（`dyn_inst_seq=5368813`, `pc=ffffffc0081e6204`）在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=1529499 eligible=1529499 injected=1`；`numFaultsInjected=1`；注入日志 1 条；三处一致。污染值被 lookup 与 SQ/cache 真实消费，属于 activated。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`400000081d75b48`/`b40`）。不是 data/permission/control-state 型（相应字段未变）；store 路径意味着"错误寻址的写"，但注入器没有改写数据字节。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：显式 `effective_pa_changed`+`contained=0`，结构放弃撤销；`event_id=4` 的 SQ execute 立即消费。

### 3.4 检测与掩蔽机制

候选：翻译结果 PA 比对（有，只在 PA 未变时含住）、权限/对齐异常（无）、ECC/parity（`model=none`）、squash/replay（本 seed 0 条）、commit 前检查（无）。盲点：PA 改变后无第二道检查；本 seed 连事后的 squash 都没有，错误提交是唯一记录。

### 3.5 最终 SDC 风险判断

有真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：event 46→69 之间污染状态被后续指令观测；`consumer_summary` 19 条记录、`logical_total=42`、`by_outcome=sd_observed`（§5）。无应用 oracle 行，**最终数据正确性不可判**；不能仅凭 errant_commit 宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 注入位点相同；掩码 seed1=`0x400000000000`（bit46）、seed2=`0x2`（bit1）、seed3=`0x200000000000`（bit45）。
- PA：seed1 `81d75b48→400000081d75b48`；seed2 `8313bd08→83139d08`；seed3 `83111d40→200000083111d40`。
- 终局：三者都是 L5 `errant_commit`（69/20/39）；seed1 的 errant 是更年轻指令（5368813），seed2/seed3 是最初访问本身。
- 运行结局：三者都是 Crash，Oops 地址/码不同（seed1 `0020000000000000`/86000004；seed2 `0000000000000000`/82000005；seed3 `0000000000000008`/96000045）。
- 多注入：seed1 1 个、seed2 5 个、seed3 3 个。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 16 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239595855309 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 5368746 | 5368746 | ffffffc009483b48 | — | — | — | 81d75 | 400000081d75 | 81d75 | 400000081d75 | 0x400000000000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit46 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 239595855309 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | — | — | — | 81d75 | 400000081d75 | 81d75 | 400000081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=400000081d75;ap=0;mtype=2;page_size=1000;pa=400000081d75b48 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 239595855309 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | 400000081d75b48 | — | — | 81d75 | 400000081d75 | 81d75 | 400000081d75 | — | 81d75b48 | 400000081d75b48 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 239595855309 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | 400000081d75b48 | — | — | — | — | 81d75b48 | 400000081d75b48 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=400000081d75;ap=0;mtype=2;page_size=1000;pa=400000081d75b48 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 239595855309 | 0 | `sq_execute` | L3 | SQ | 1 | seq_primary | — | 5368746 | ffffffc009483b48 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | store，`sq_idx=479071` | 以错误 PA 执行 | 进入访存 |
| 6 | 5 | 4 | 239595856641 | 1332 | `sq_writeback` | L3 | SQ | 1 | seq_primary | — | 5368746 | — | 400000081d75b48 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | execute 完成 | 构建 packet | 错误地址随包 |
| 7 | 6 | 5 | 239595856641 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | ffffffc009483b48 | 400000081d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | packet | 首次访问 | 错误被消费 |
| 8 | 7 | 6 | 239595856641 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | — | 400000081d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 9 | 8 | 7 | 239595856641 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 400000081d75b48 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 10 | 9 | 8 | 239595856974 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | ffffffc009483b48 | 400000081d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费 |
| 11 | 10 | 9 | 239595856974 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | — | 400000081d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 12 | 11 | 10 | 239595856974 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 400000081d75b40 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 13 | 45 | 11 | 239595965199 | 108225 | `resp` | L3 | L1D→core resp | 1 | seq_primary | 5368746 | 5368746 | 400000081d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 14 | 46 | 45 | 239595965199 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | 5368746 | 5368746 | 400000081d75b48 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应 | clean→tainted | 存储→CPU 边界 |
| 15 | 47 | 46 | 239595965199 | 0 | `sq_complete` | L3 | SQ | 1 | seq_primary | — | 5368746 | ffffffc009483b48 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | store 完成 | `sq_idx=479071` 收口 | store 结束 |
| 16 | 69 | 47 | 239595975522 | 10323 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 5368813 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 3091 条事件，全部 `fault_id=1`；主链 16 条，其余 3075 条（含 `chain_end`）为旁支。主要形态：

- **`request_fork` 349 条**：`addr_fallback_broadcast`，从主链 MSHR 分配点（尤其 event 11）向兄弟请求广播；未回流终局祖先。
- **兄弟请求**：503 条 `cache_access`、503 条 `cache_return`、228 条 `mshr_alloc`、275 条 `mshr_merge`、348 条 `resp`、356 条 `taint_reg`、17 条 `lq_complete` 等。
- **预取事件**：95 条 `pf_queue`、87 条 `pf_issue`、275 条 `pf_demand`、1 条 `pf_fill`；这些是该构建新增的预取侧记录，不属于本次翻译的祖先，也不改变 SDC 结论。
- **填充事件**：旁支有 2 条 `mshr_fill`、2 条 `cache_fill`、2 条 `mshr_free`（主链没有）。
- **`consumer` 31 条**：19 条 summary、`emitted=19`、`suppressed=23`、`logical_total=42`、`conservation=ok`、`by_outcome=sd_observed`。
- **无 `squash_masked`**：本 seed 没有任何 squash 收口，这也是错误直达 L5 的直接原因之一。

旁支不构成第二条终局祖先；它们扩大污染消费面（42 个逻辑消费者），但不改变 L5 结论。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=69，tick=239595975522，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效 |
| conservation | `ok`（19+23=42） |
| count_contradiction | 否（attempted=1529499>0；injected=1=stats=1） |
| campaign/checker agreement | 一致（seed1 outcome=Crash；terminal=full） |
| CHAIN_DEMONSTRATED | 是 |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| verdict | **PASS** |

一致性自检：16 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调不降；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。工作负载标签（TLB-AliasPerm 探针）与实际 `tlb_probe.rcS` 一致。

**其它缺口（不改变 PASS，但必须记录）**：矩阵把被注入字段写作"VPN tag"，证据是 PFN 翻转；manifest `exit_code=null`；`taint_reg` 无寄存器号；主链无 fill 事件。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s1/T01-F1-W4/seed1/prop_evt.txt.gz` | `c0828cb4f9aac064a04e38d8700fb76e080842f3f106bf931bb4868447b390a2` | 104086 | 2026-10-27T02:43:42 |
| chain_report（权威） | `.../seed1/chain_report.json` | `0cefdbcb2760d05259c02c7d7b9faef453cfbf6075ac14918508bba71eb00273` | 18632 | 2026-10-27T02:43:43 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed1/run.out` | `a052c13615df251f0817f0e98490355d924d48d379275cddf3b443a7d54ea2a1` | 2541 | 2026-10-27T02:43:43 |
| run.err | `.../seed1/run.err` | `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36` | 1873 | 2026-10-27T02:43:43 |
| stats.txt | `.../seed1/stats.txt` | `16ef492372fae25f3732f39de6115d3da1b68ca3a63d4b0a1ca71365a682dee2` | 416526 | 2026-10-27T02:43:43 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s1/manifest.json` | `ae4fa31b5e26d7dcdde01fd700fff123707247e5de27b353109f811acc9eaf13` | 1438 | 2026-10-27T02:43:44 |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | — | — |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed1/board.workload.dmesg` | `e6037ec93da2ca28193748c08104d2f1d498ea7ee93bec0cab509363731480f5` | 13845 | 2026-10-27T02:43:42 |
| 辅助证据（terminal） | `.../seed1/board.terminal` | `ba0002d31be55d6b192e25fadcfe80cc2fba7d7f7318e445c5b73a76fd8ae041` | 1736 | 2026-10-27T02:43:42 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s1/T01-F1-W4/seed1`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；旧二进制副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
