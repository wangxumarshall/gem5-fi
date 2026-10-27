# T01-F1-W1 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F1-W1` |
| seed | `1` |
| sample_run_id | `s1` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F1` |
| requested tier | `F1` |
| effective tier | `F1` |
| tier enabled | `开启(1)`（`CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1`） |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`——**与矩阵标签不一致**（实际为 TLB page-walk 探针）。详见 §6。 |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s1/T01-F1-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T01-F1-W1 --prop_sample_run_id s1` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s1/T01-F1-W1/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s1/manifest.json`（`exit_code=null`；真实退出码 `.exit_code`=0） |
| 正常 EOF | **是**（解压后 7,270,326 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=2492356815`、`simInsts=3291573`、`finalTick=240442153830` |
| 原始事件数 | `9884` |
| fault_id 数量 | `1` |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`；run.out `CHAOS_LSU_NOEFFECT: fires=n/a no_effect=n/a`（该构建未提供 fires/no_effect 计数，如实记为 n/a）。

## 2. 完整故障传播过程：从注入到最终结局

终局是真实 L5：`errant_commit`（`event_id=87`，tick=`239595941223`）。按 `parent_event_id` 回溯得到唯一祖先链 22 条：

`0 → 1 → 2 → 3 → 4(sq_execute) → 5(sq_writeback) → 6 → 7 → 8 → 9 → 10 → 11 → 45(mshr_fill) → 46(cache_fill) → 47(mshr_free) → 48(mshr_fill) → 49(cache_fill) → 50(mshr_free) → 51(resp) → 52(taint_reg) → 53(sq_complete) → 87(errant_commit)`

tick 段：239595855309、239595856641、239595856974、239595915915、239595916581、239595916914、239595941223，单调不降（逐条 Δtick 见 §4；无负值）。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=5368746`、`request_id=5368746`，VA=`0xffffffc009483b48`（页内偏移 `0xb48`）。目标表项 `entry_index=20`、`way=-1`、`walk_id=0`；注入前 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75b48`。本链含 `sq_execute`/`sq_writeback`/`sq_complete`，说明这是 **store** 路径。

### 2.2 故障具体如何注入

`event_id=0`，tick=`239595855309`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=5368746`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x4000`，即 PFN 第 14 位。原 PFN `0x81d75` 异或后得 `0x85d75`：把数值变化讲完整——第 14 位由 0 变 1，表项保存的 PFN 从 `0x81d75` 变成 `0x85d75`，其余位不变。第 14 位在物理地址中对应第 26 位，落在有效 PA 宽度内，因此有效物理地址从 `0x81d75b48` 变成 `0x85d75b48`，`effective_pa_changed` 为真。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`239595855309`，`request_id=5368746`，`corr=seq_primary`，`entry_index=20`）记录 `field=post_lookup`，`before=81d75`、`after=85d75`；state 对照 `pfn=81d75→85d75`、`pa=81d75b48→85d75b48`，其余字段不变。

`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=85d75b48`、`state_before=81d75b48`、`state_after=85d75b48`。

`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）给出裁决：`field=effective_pa_changed`、`before=81d75b48`、`after=85d75b48`、`contained=0`、`outcome=NoFault`。含义：翻译没有触发权限/对齐 fault（`NoFault`），但因 requested 与 effective 不同，**不**含住；错误 PA 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

`event_id=4`（`sq_execute`，parent=3，tick=`239595855309`，`sq_idx=479071`，`state_before=issued`）表明错误 PA 所在的 store 已在 SQ 内执行；`event_id=5`（`sq_writeback`，parent=4，tick=`239595856641`，`pa=85d75b48`，`state_after=packet_built`，`sq_idx=479071`）构建访存 packet；`event_id=6`（`cache_access`，parent=5）以该 PA 发出。输入→内部变化→输出：翻译给出错误 PA→SQ 执行并构建 packet→cache 请求。`lsq_push` 在本链与其祖先中缺席，故"进入 LSQ 的插入时刻"记为 `N/A`（证据缺席）；SQ 内的 execute→writeback→complete 是完整的。

### 2.5 错误如何经过 cache 和 MSHR

两次访问、两次未命中、两次 MSHR 生命周期：

- 第一次：`event_id=6`（`cache_access`，parent=5，tick=`239595856641`，`request_id=5368746`）访问 `pa=85d75b48`；`event_id=7`（`cache_return`）`field=miss`；`event_id=8`（`mshr_alloc`）`cache_line=85d75b48`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=9`（`cache_access`，parent=8，tick=`239595856974`）访问同一行基址 `pa=85d75b40`；`event_id=10` `miss`；`event_id=11`（`mshr_alloc`）`cache_line=85d75b40`、`mshr_id=2`、`state_after=mshr_allocated`。
- 填充与释放（全部在祖先上）：`event_id=45`（`mshr_fill`，parent=11，tick=`239595915915`）`mshr_id=2`、`state_after=filled`；`event_id=46`（`cache_fill`）填 `cache_line=85d75b40`；`event_id=47`（`mshr_free`）`mshr_id=2`、`state_after=mshr_freed`。随后 `event_id=48`（`mshr_fill`，parent=47，tick=`239595916581`）`mshr_id=0`、`state_after=filled`；`event_id=49`（`cache_fill`）再填同一行；`event_id=50`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

状态迁移解释：miss→alloc（请求挂起）→fill（数据到）→cache_fill（行入 L1D）→free（资源释放）。`mshr_id=0` 的第二次 fill/free 是事件流原值。为什么仍是同一 fault：`fault_id=1`、parent 连续、两次访问同属错误 PA 所在行（`...b48` 与行基址 `...b40`）。

### 2.6 污染如何返回处理器状态

`event_id=51`（`resp`，parent=50，tick=`239595916914`，`request_id=5368746`，`corr=seq_primary`，`va=85d75b48`）返回响应；`event_id=52`（`taint_reg`，parent=51）`before=clean`、`after=tainted`、`va=85d75b48`、`dyn_inst_seq=5368746`。这是存储→CPU 边界。`event_id=53`（`sq_complete`，parent=52）把 `sq_idx=479071` 置 `completed`。证据限制：`taint_reg` 无 `arch_reg`/`phys_reg`。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=87`，parent=53，tick=`239595941223`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=5368813`、`pc=ffffffc0081e6204`、`commit_seq=3579740`。与上游的关系：最初被污染的访问是 `5368746`，错误提交是 **更年轻** 的 `5368813`，说明污点沿寄存器依赖传播后在提交端兑现。为什么没被提前消除：L2 明确 `contained=0`；50 条 squash 全部发生在错误提交之后（§5）；提交前无拦截。`chain_end`（`event_id=8371`，tick=`240442153830`，`outcome=errant_commit_seen`，`reason=squash_replay`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out：

- `CHAOS_DETECT: layer=None contained=0 tick=239595941223 ptag=1 reason=errant_commit`
- 之后 50 条 `CHAOS_DETECT: layer=Hardware RAS contained=1 ... reason=squash_replay`（首条 tick 239597541288）——都是错误提交之后对更年轻指令的 squash，不能抵消 event 87
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.160000] Unable to handle kernel paging request at virtual address 0020000000000000`
- `[2.160000] Internal error: Oops: 86000004 [#1] PREEMPT SMP`

注入 tick=`239595855309`，错误提交 tick=`239595941223`，传播延迟 **85,914 ticks**。L5→Crash 因果成立。链终止 tick=`240442153830`。无应用 oracle 行（terminal 仅 Oops），最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit14 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=5368746） | 读到 `pfn=85d75` | PA=`85d75b48` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=85d75b48` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L3 SQ | store（`sq_idx=479071`） | execute→writeback | packet | 错误地址随包发出 |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | 分配并填充/释放（mshr 2、0） | fill/free 序列 | 请求挂起与回收 |
| L3 L1D→core resp | 填充完成 | 返回 | `resp`（req=5368746） | 污染回到核心 |
| L4 taint/regfile | response | clean→tainted | 污染状态 | 存储→CPU 边界 |
| L3 SQ complete | store 完成 | completed | 条目收口 | store 结束 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=5368813` | 架构可见错误 |
| LQ / LSQ push | — | — | — | `N/A`（无对应事件） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 14 位置 1，PA 由 `0x81d75b48` 变为 `0x85d75b48`；翻译结果记录 `effective_pa_changed/contained=0`，store 经 SQ（`sq_idx=479071`）发出，错误地址在 L1D 两次未命中并由 MSHR 2/0 完成填充与释放，`resp` 与 `taint_reg` 把污点带入寄存器，最终由更年轻的指令（`dyn_inst_seq=5368813`, `pc=ffffffc0081e6204`）在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=1390245 eligible=1390245 injected=1`；`numFaultsInjected=1`；注入日志 1 条；三处一致。污染值被 lookup 与 SQ/cache 真实消费，属于 activated。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`85d75b48`/`b40`）。不是 data/permission/control-state 型（相应字段未变）。store 路径意味着"错误寻址的写"，但注入器没有改写数据字节。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：显式 `effective_pa_changed` + `contained=0`，是结构放弃撤销的位置；`event_id=4` 的 SQ execute 立即消费它。

### 3.4 检测与掩蔽机制

候选：翻译结果 PA 比对（有，但只在 PA 未变时含住）、权限/对齐异常（无）、ECC/parity（`model=none`）、squash/replay（50 条，全在错误提交之后）、commit 前检查（无）。盲点：PA 改变后无第二道检查；squash 只影响更年轻指令。`outcome=NoFault` 不等于"无故障"，`contained=0` 才是"未含住"。

### 3.5 最终 SDC 风险判断

有真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：event 52→87 之间污染状态被后续指令观测；`consumer_summary` 1281 条记录、`logical_total=505392`、`by_outcome=sd_observed`（§5）。本 seed 无应用 oracle 行，**最终数据正确性不可判**；不能仅凭 errant_commit 宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 掩码：seed1=`0x4000`（bit14）、seed2=`0x1`（bit0）、seed3=`0x4000`（bit14）。seed1 与 seed3 掩码相同，但注入 tick/VA 不同（239595855309/`b48` vs 239629862268/`d40`），是两个独立抽样。
- PA：seed1 `81d75b48→85d75b48`；seed2 `8313bd08→8313ad08`；seed3 `83111d40→87111d40`。
- 终局：三者都是 L5 `errant_commit`（87/20/45）；seed1 与 seed3 的 errant `dyn_inst_seq` 分别是 5368813 与 5536042（后者就是最初访问），seed2 是 4338322（也是最初访问）。
- 运行结局：三者都是 Crash，Oops 地址/码不同（seed1 `0020000000000000`/`86000004`；seed2 `0000000000000008`/`96000005`；seed3 `0020000000000000`/`86000004`）。
- 多注入：seed1 只有 1 个注入；seed2 共 2 个、seed3 共 3 个（见各自文件）。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 22 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239595855309 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 5368746 | 5368746 | ffffffc009483b48 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | 0x4000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit14 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 239595855309 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 239595855309 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | 85d75b48 | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | 81d75b48 | 85d75b48 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 239595855309 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 5368746 | 5368746 | ffffffc009483b48 | 85d75b48 | — | — | — | — | 81d75b48 | 85d75b48 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75b48 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75b48 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 239595855309 | 0 | `sq_execute` | L3 | SQ | 1 | seq_primary | — | 5368746 | ffffffc009483b48 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | store，`sq_idx=479071` | 以错误 PA 执行 | 进入访存 |
| 6 | 5 | 4 | 239595856641 | 1332 | `sq_writeback` | L3 | SQ | 1 | seq_primary | — | 5368746 | — | 85d75b48 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | execute 完成 | 构建 packet | 错误地址随包 |
| 7 | 6 | 5 | 239595856641 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | ffffffc009483b48 | 85d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | packet | 首次访问 | 错误被消费 |
| 8 | 7 | 6 | 239595856641 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 9 | 8 | 7 | 239595856641 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b48 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 10 | 9 | 8 | 239595856974 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | ffffffc009483b48 | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费 |
| 11 | 10 | 9 | 239595856974 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 12 | 11 | 10 | 239595856974 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 13 | 45 | 11 | 239595915915 | 58941 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 2 填充 | 数据就绪 |
| 14 | 46 | 45 | 239595915915 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b40 | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 L1D | 行可用 |
| 15 | 47 | 46 | 239595915915 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 资源回收 |
| 16 | 48 | 47 | 239595916581 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 再次填充 | `mshr_id=0` 填充 | 原值保留 |
| 17 | 49 | 48 | 239595916581 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 5368746 | 5368746 | — | 85d75b40 | 85d75b40 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 18 | 50 | 49 | 239595916581 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 5368746 | 5368746 | — | — | 85d75b40 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 19 | 51 | 50 | 239595916914 | 333 | `resp` | L3 | L1D→core resp | 1 | seq_primary | 5368746 | 5368746 | 85d75b48 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 20 | 52 | 51 | 239595916914 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | 5368746 | 5368746 | 85d75b48 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应 | clean→tainted | 存储→CPU 边界 |
| 21 | 53 | 52 | 239595916914 | 0 | `sq_complete` | L3 | SQ | 1 | seq_primary | — | 5368746 | ffffffc009483b48 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | store 完成 | `sq_idx=479071` 收口 | store 结束 |
| 22 | 87 | 53 | 239595941223 | 24309 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 5368813 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 9884 条事件，全部 `fault_id=1`；主链 22 条，其余 9862 条（含 `chain_end`）为旁支。规模最大的几类：

- **`consumer` 1281 条**：1281 条 summary、`emitted=1281`、`suppressed=504111`、`logical_total=505392`、`distinct_dyn_seq=504289`、`conservation=ok`、`by_outcome=sd_observed`。污染值被后续指令大量观测，全部不在主链。
- **`request_fork` 1512 条**：`addr_fallback_broadcast`，从主链的 MSHR 分配点（尤其 event 11）向兄弟请求广播错误地址；未回流终局祖先。
- **`squash_masked` 50 条**：事件自身 `detection_layer=L4`、`contained=1`、`outcome=masked`、`reason=squash_replay`；首条 tick 239597541288，全部晚于 event 87。它们不能把本 seed 改判为含住，也不能写成 L5 终局（事件声明是 L4）。
- 另有 1543 条 `cache_access`、1543 条 `cache_return`、60 条 `mshr_alloc`、93 条 `mshr_merge`、60 条 `mshr_fill`、60 条 `cache_fill`、60 条 `mshr_free`、1429 条 `resp`、1677 条 `taint_reg`、493 条 `lq_complete` 等兄弟请求事件。

旁支不构成第二条终局祖先；它们扩大污染消费面（505392 个逻辑消费者记录），但不改变 L5 结论。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=87，tick=239595941223，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效 |
| conservation | `ok`（1281 + 504111 = 505392） |
| count_contradiction | 否（attempted=1390245>0；injected=1=stats=1） |
| campaign/checker agreement | 一致（seed1 outcome=Crash；terminal=full） |
| CHAIN_DEMONSTRATED | 是 |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**REVIEW_REQUIRED 理由**：链一致性、认证、L5 见证均通过；但工作负载身份与矩阵不符——矩阵标 `T01-F1-W1` 为 MiBench-TC23，run.out/terminal 证明实际是 `tlb_probe.rcS`，且矩阵记录状态仍为 `blocked(fs-infra: SE has no MiBench FS pipeline)`。工作负载是 cell 契约的一部分，必须人工复核。

一致性自检：22 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调不降（逐条 Δtick 均为非负）；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。

**其它缺口**：字段口径（VPN tag vs PFN）；manifest `exit_code=null`；`taint_reg` 无寄存器号。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s1/T01-F1-W1/seed1/prop_evt.txt.gz` | `90b713c7a597bf29985cd9087eae6353dd5a10978c08f960af38cdf282dc528b` | 386922 | 2026-10-27T13:16:30 |
| chain_report（权威） | `.../seed1/chain_report.json` | `bd4850988fe8fa69ed5baee876cc7ba1c74c589f7df949dc9db27d012f1d032d` | 1102976 | 2026-10-27T13:16:32 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed1/run.out` | `20c59a5a8190b5d4cec34b9807302e0b5fb9b053c0d20390f76bfd68ed304e1f` | 7100 | 2026-10-27T13:16:31 |
| run.err | `.../seed1/run.err` | `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36` | 1873 | 2026-10-27T13:16:31 |
| stats.txt | `.../seed1/stats.txt` | `5ee0283ba5491de374f07fa0a83b57e3b73d80a30149336b99cb5bf357558e46` | 415803 | 2026-10-27T13:16:31 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s1/manifest.json` | `adc17de4455fc090d7727af5d17a2219d92aa380c6eb23481f78de58618b759e` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed1/board.workload.dmesg` | `af79a9fcf5b892c604e85a3ffafd3f2ba590bf35ef97d7b69bae67664c3e6fa1` | 13845 | 2026-10-27T13:16:30 |
| 辅助证据（terminal） | `.../seed1/board.terminal` | `0f27e00d74fbbf704c98a36092c44601401b4cf8e67c326c925aa71b423b805b` | 1736 | 2026-10-27T13:16:30 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s1/T01-F1-W1/seed1`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；旧二进制副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
