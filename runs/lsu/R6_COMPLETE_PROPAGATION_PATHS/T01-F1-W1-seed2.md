# T01-F1-W1 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F1-W1` |
| seed | `2` |
| sample_run_id | `s2` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F1` |
| requested tier | `F1` |
| effective tier | `F1` |
| tier enabled | `开启(1)` |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`——**与矩阵标签不一致**。详见 §6。 |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s2/T01-F1-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T01-F1-W1 --prop_sample_run_id s2` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s2/T01-F1-W1/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s2/manifest.json`（`exit_code=null`；真实退出码 `.exit_code`=0） |
| 正常 EOF | **是**（解压后 2,012,859 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=3722758515`、`simInsts=4476372`、`finalTick=241672555530`、`numFaultsInjected=2` |
| 原始事件数 | `2279` |
| fault_id 数量 | `2`（fault 1 与 fault 2；见 §2/§5） |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`。本 seed 是 F1 多注入样本：`injected=2`、`stats.numFaultsInjected=2`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 有两条 fault 流。按 checker 的 escape-first 规则，代表故障是 **fault 1**（终局 `full`，真实 L5 `errant_commit`）；fault 2 是同一 run 的另一个注入，终局为 `provable_to_L4_then_unknown`，完整讨论放在 §5，绝不并入 fault 1 的祖先链。

fault 1 的祖先链 21 条：

`0 → 1 → 2 → 3 → 4(lq_read) → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17(resp) → 18(lq_complete) → 19(taint_reg) → 20(errant_commit)`

tick 段：239345234181、239345234514、239345293455、239345294121、239345294454、239345295120，单调不降（逐条 Δtick 见 §4）。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=4338322`、`request_id=4338322`，VA=`0x7f82b83d08`（页内偏移 `0xd08`）。表项 `entry_index=29`、`way=-1`、`walk_id=0`；注入前 `vpn=7f82b83`、`asid=214`、`valid=1`、`global=0`、`pfn=8313b`、`ap=3`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x8313bd08`。本链含 `lq_read`/`lq_complete`，说明这是 **load** 路径。

### 2.2 故障具体如何注入

`event_id=0`，tick=`239345234181`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=4338322`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x1`，即 PFN 最低位（第 0 位）。原 PFN `0x8313b` 异或后得 `0x8313a`：把数值变化讲完整——第 0 位由 1 变 0，表项保存的 PFN 从 `0x8313b` 变成 `0x8313a`，即数值减一；由于 PFN 左移 12 位构成页基址，这个减一使物理地址从 `0x8313bd08` 变成 `0x8313ad08`（相差 `0x1000`，正好一页）。`effective_pa_changed` 为真。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`239345234181`，`request_id=4338322`，`corr=seq_primary`，`entry_index=29`）记录 `field=post_lookup`，`before=8313b`、`after=8313a`；state 对照 `pfn=8313b→8313a`、`pa=8313bd08→8313ad08`，其余字段不变。
`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=8313ad08`、`state_before=8313bd08`、`state_after=8313ad08`。
`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）：`field=effective_pa_changed`、`before=8313bd08`、`after=8313ad08`、`contained=0`、`outcome=NoFault`。含义：翻译本身无 fault，但因 PA 改变而不含住；错误 PA 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

`event_id=4`（`lq_read`，parent=3，tick=`239345234181`，`request_id=4338322`，`lq_idx=470727`）表明错误 PA 的 load 已在 LQ 内被读取/发射。随后 `event_id=5`（`cache_access`，parent=4）以该错误 PA 发出请求。输入→内部变化→输出：翻译结果（错误 PA）→LQ 读取该条目→cache 请求。`lsq_push` 缺席，故"插入 LSQ 的时刻"为 `N/A`（证据缺席）；LQ 内的 read→complete 生命周期是完整的。

### 2.5 错误如何经过 cache 和 MSHR

- 第一次：`event_id=5`（`cache_access`，parent=4，tick=`239345234181`，`request_id=4338322`）访问 `pa=8313ad08`；`event_id=6`（`cache_return`）`field=miss`；`event_id=7`（`mshr_alloc`）`cache_line=8313ad08`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=8`（`cache_access`，parent=7，tick=`239345234514`）访问同一行基址 `pa=8313ad00`；`event_id=9` `miss`；`event_id=10`（`mshr_alloc`）`cache_line=8313ad00`、`mshr_id=2`、`state_after=mshr_allocated`。
- 填充与释放：`event_id=11`（`mshr_fill`，parent=10，tick=`239345293455`）`mshr_id=2`、`state_after=filled`；`event_id=12`（`cache_fill`）填行；`event_id=13`（`mshr_free`）`mshr_id=2`、`state_after=mshr_freed`。随后 `event_id=14`（`mshr_fill`，parent=13，tick=`239345294121`）`mshr_id=0`、`state_after=filled`；`event_id=15`（`cache_fill`）；`event_id=16`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

状态迁移：miss→alloc→fill→cache_fill→free。`mshr_id=0` 的第二次 fill/free 为原值。同一 fault 的依据：`fault_id=1`、parent 连续、两次访问同属错误 PA 所在行（`...d08` 与行基址 `...d00`）。

### 2.6 污染如何返回处理器状态

`event_id=17`（`resp`，parent=16，tick=`239345294454`，`request_id=4338322`，`corr=seq_primary`，`va=8313ad08`）返回响应；`event_id=18`（`lq_complete`，parent=17，同 tick，`request_id=4338322`，`pa=8313ad08`，`lq_idx=470727`）完成 load 生命周期；`event_id=19`（`taint_reg`，parent=18）明确记录 `before=clean`、`after=tainted`、`va=8313ad08`、`arch_reg=12`、`phys_reg=110`。这是本 seed 最清晰的存储→CPU 边界：污点落到了体系结构寄存器 12 / 物理寄存器 110。注意事件顺序：taint_reg 的父是 lq_complete，说明"响应→load 完成→寄存器被标脏"。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=20`，parent=19，tick=`239345295120`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=4338322`、`pc=7f82b8e3c4`、`commit_seq=2988647`。与 seed1 不同，这里错误提交的 `dyn_inst_seq` 就是最初访问的 `4338322`——即该 load 自己携带被污染的值提交，而非更年轻指令。为什么没被提前消除：L2 明确 `contained=0`；唯一的 squash（event 265）晚于错误提交（§5）；提交前无拦截。`chain_end`（`event_id=2126`，tick=`241672555530`，`outcome=errant_commit_seen`，`reason=squash_replay`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out：

- `CHAOS_DETECT: layer=None contained=0 tick=239345295120 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=239349889521 ptag=1 reason=squash_replay`（事后）
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=241672555530 ptag=2 reason=store_discarded_not_retired`（兄弟 fault 2 的收口）
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.160000] Unable to handle kernel NULL pointer dereference at virtual address 0000000000000008`
- `[2.160000] Internal error: Oops: 96000005 [#1] PREEMPT SMP`

注入 tick=`239345234181`，错误提交 tick=`239345295120`，传播延迟 **60,939 ticks**。L5→Crash 因果成立。链终止 tick=`241672555530`。无应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit0 置 0 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=4338322） | 读到 `pfn=8313a` | PA=`8313ad08` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=8313ad08` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L3 LQ | load（`lq_idx=470727`） | read | 访存请求 | 错误进入 LQ |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | MSHR 1/2，fill/free（2、0） | 填充完成 | 请求挂起与回收 |
| L3 L1D→core resp | 填充完成 | 返回 | `resp`（req=4338322） | 污染回到核心 |
| L3 LQ complete | load 完成 | `lq_idx=470727` | load 生命周期收口 | 值已就绪 |
| L4 taint/regfile | response | clean→tainted | **arch12/phys110 被标脏** | 存储→CPU 边界 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=4338322` | 架构可见错误 |
| SQ | — | — | — | `N/A`（load 路径） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 0 位置 0（PFN 减一），PA 从 `0x8313bd08` 变成 `0x8313ad08`；翻译结果记录 `effective_pa_changed/contained=0`，load 经 LQ（`lq_idx=470727`）发出，错误地址在 L1D 两次未命中并由 MSHR 2/0 完成填充与释放，`resp`→`lq_complete`→`taint_reg`（arch12/phys110）把污点带入寄存器，最终该 load 本身（`dyn_inst_seq=4338322`, `pc=7f82b8e3c4`）在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=1901753 eligible=1901753 injected=2`；`numFaultsInjected=2`；注入日志 2 条（fault1 tick 239345234181、fault2 tick 240401619738）。三处一致。代表故障（fault 1）的污染值被 lookup 与 LQ/cache 真实消费，属于 activated 并构成代表链。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`8313ad08`/`d00`）。不是 data/permission/control-state 型（相应字段未变）。注意 `ap=3` 的权限属性未改变，故障不是权限型。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：显式 `effective_pa_changed`+`contained=0`，结构放弃撤销；`event_id=4` 的 `lq_read` 立即消费它。

### 3.4 检测与掩蔽机制

候选：翻译结果 PA 比对（有，只在 PA 未变时含住）、权限/对齐异常（无）、ECC/parity（`model=none`）、squash/replay（1 条，晚于错误提交）、commit 前检查（无）。盲点：PA 改变后无第二道检查；squash 只影响更年轻指令。`outcome=NoFault` 不等于无故障。

### 3.5 最终 SDC 风险判断

有真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：event 19（taint_reg）→20，污染值被后续指令观测；`consumer_summary` 1285 条记录、`logical_total=826030`、`by_outcome=sd_observed`（§5）。本 seed 无应用 oracle 行，**最终数据正确性不可判**；不能仅凭 errant_commit 宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 掩码：seed1=`0x4000`（bit14）、seed2=`0x1`（bit0）、seed3=`0x4000`（bit14）。
- PA：seed1 `81d75b48→85d75b48`；seed2 `8313bd08→8313ad08`；seed3 `83111d40→87111d40`。
- 终局：三者都是 L5 `errant_commit`（87/20/45）；本 seed 的 errant 就是最初 load 本身（4338322），seed1 的 errant 是更年轻指令（5368813），seed3 的 errant 是最初 load（5536042）。
- 运行结局：三者都是 Crash，Oops 码不同。
- 多注入：本 seed 有 2 个注入（fault 2 未逃逸，见 §5）；seed1 只有 1 个；seed3 有 3 个。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 21 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239345234181 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 4338322 | 4338322 | 7f82b83d08 | — | — | — | 8313b | 8313a | 8313b | 8313a | 0x1 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit0 置 0 | 故障进入存储 |
| 2 | 1 | 0 | 239345234181 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | — | — | — | 8313b | 8313a | 8313b | 8313a | — | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08 | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 239345234181 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | 8313b | 8313a | 8313b | 8313a | — | 8313bd08 | 8313ad08 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 239345234181 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | — | — | 8313bd08 | 8313ad08 | — | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08 | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 239345234181 | 0 | `lq_read` | L3 | LQ | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | load，`lq_idx=470727` | 读取队列条目 | 错误进入 LQ |
| 6 | 5 | 4 | 239345234181 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 读取 | 首次访问 | 错误被消费 |
| 7 | 6 | 5 | 239345234181 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 8 | 7 | 6 | 239345234181 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad08 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 9 | 8 | 7 | 239345234514 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | 7f82b83d08 | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费 |
| 10 | 9 | 8 | 239345234514 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 11 | 10 | 9 | 239345234514 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 12 | 11 | 10 | 239345293455 | 58941 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 2 填充 | 数据就绪 |
| 13 | 12 | 11 | 239345293455 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad00 | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 | 行可用 |
| 14 | 13 | 12 | 239345293455 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 资源回收 |
| 15 | 14 | 13 | 239345294121 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 再次填充 | `mshr_id=0` 填充 | 原值保留 |
| 16 | 15 | 14 | 239345294121 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 4338322 | 4338322 | — | 8313ad00 | 8313ad00 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 17 | 16 | 15 | 239345294121 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 8313ad00 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 18 | 17 | 16 | 239345294454 | 333 | `resp` | L3 | L1D→core resp | 1 | seq_primary | 4338322 | 4338322 | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 19 | 18 | 17 | 239345294454 | 0 | `lq_complete` | L3 | LQ | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 8313ad08 | — | — | — | — | — | — | — | — | — | — | — | — | — | load 完成 | 值就绪 | load 完成 |
| 20 | 19 | 18 | 239345294454 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | 4338322 | 4338322 | 8313ad08 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | clean→tainted | 存储→CPU 边界 | 存储→CPU 边界 |
| 21 | 20 | 19 | 239345295120 | 666 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 4338322 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 2279 条事件，分属 fault 1（代表故障，主链 21 条）与 fault 2。旁支分两类：

1. **fault 1 的兄弟请求与消费者**：`request_fork` 56 条（`addr_fallback_broadcast`），162 条 `cache_access`、162 条 `cache_return`、20 条 `mshr_alloc`、14 条 `mshr_merge`、20 条 `mshr_fill`、20 条 `cache_fill`、20 条 `mshr_free`、145 条 `resp`、145 条 `taint_reg`、103 条 `lq_complete`，以及 1288 条 `consumer`（1285 条 summary、`logical_total=826030`、`conservation=ok`）。另有 1 条 `squash_masked`：`event_id=265`，tick=`239349889521`，事件自身 `detection_layer=L4`、`contained=1`、`outcome=masked`、`reason=squash_replay`、`dyn_inst_seq=4366204`；它晚于错误提交（239345295120），不能写成 L5，也不能抵消 event 20。
2. **fault 2（另一个注入）**：`event_id=313`（inj，tick=`240401619738`，VA=`ffffff8001af29e0`，`old=81af2 → new=c1af2`，掩码 `0x40000`），随后 314（lookup）、315（pfn）、316（translate，`effective_pa_changed/contained=0`）以及 1900+ 条访存/污染事件。它**没有** `errant_commit`，其 `chain_end`（`event_id=2127`，tick=`241672555530`，`detection_layer=L4`，`outcome=detected_contained`，`reason=store_discarded_not_retired`）记录的是"store 被丢弃、未退休"的收口。checker 对 fault 2 的裁决是 `provable_to_L4_then_unknown`（L4，开放终局），不是 full，也不是 L2 含住。它绝不能并入 fault 1 的主链，也不能用它的收口来削弱 fault 1 的 L5 结论。

旁支是否影响 SDC 诊断？fault 2 说明同一 run 的另一个注入没有逃逸到提交端；fault 1 的消费者记录说明静默面很大。二者都不改变 fault 1 的 L5 结论。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（代表故障真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=20，tick=239345295120，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效（`numFaultsInjected=2` 与 injected=2 一致） |
| conservation | `ok`（1285 条 summary；`logical_total=826030`） |
| count_contradiction | 否（attempted=1901753>0；injected=2=stats=2） |
| campaign/checker agreement | **部分不一致**：`cell_results` 记 `activated=2`、`classes.Crash=2`，即把两个注入都计为 Crash；但 checker 对 fault 2 的裁决是 `provable_to_L4_then_unknown`（不是 L5 逃逸）。样本级 outcome=Crash 与权威报告一致，fault 级计数口径不一致（见下） |
| CHAIN_DEMONSTRATED | 是（fault 1 的 `inj`→L5 单祖先连续） |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**两轴状态（不是单一 REVIEW）**：

1. `experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH`：矩阵标 MiBench-TC23，run.out/terminal 证明实际是 `tlb_probe.rcS`；矩阵记录状态仍为 `blocked(fs-infra: SE has no MiBench FS pipeline)`。
2. **计数口径（两套并列）**：campaign `classes.Crash=2` 是 run 级 outcome（本次运行 Crash）乘以 activated 数；checker 是 per-fault 终局（1 full + 1 open L4）。两者统计单元不同，样本级一致，不是数据矛盾；详见 `R6-T01-F1-W4-MULTIFAULT-RECHECK.md`。
3. 矩阵字段口径（VPN tag）与证据（PFN）不一致，属矩阵元数据记录，保留。
结论：`chain_evidence_status=PASS`；`overall_experiment_status=NOT_MIBENCH_RESULT`。

一致性自检：21 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调不降；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界（没有把 fault 2 或 squash 说成 L5）。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s2/T01-F1-W1/seed2/prop_evt.txt.gz` | `74105cde9ab7949a4dcd124dc862c2762c7375c040080e62135d7298772c90a4` | 136919 | 2026-10-27T14:43:34 |
| chain_report（权威） | `.../seed2/chain_report.json` | `b4c4133996b7152fc5b091c4f9600973d8945da7aab5c21ddf4ff2b183733d0d` | 1119921 | 2026-10-27T14:43:35 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed2/run.out` | `f684c1a5d8c06079c218b6ab593ba7dd3d20f818b6b925210f31b746048c290d` | 2746 | 2026-10-27T14:43:35 |
| run.err | `.../seed2/run.err` | `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17` | 1973 | 2026-10-27T14:43:35 |
| stats.txt | `.../seed2/stats.txt` | `766c92cc0f74b8074dee6ff9fac2d234f94e7f93e09abf3b66beff4086e157c0` | 420210 | 2026-10-27T14:43:34 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s2/manifest.json` | `887ccefbc5caed3999108c41b776a57fa6d9edfb57bd40cf46d5d7303ff70d49` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed2/board.workload.dmesg` | `8285e0b4ea657afff16bbe538c7bb208fa39eef5bc9bec7e58332b02e97b8af0` | 14608 | 2026-10-27T14:43:34 |
| 辅助证据（terminal） | `.../seed2/board.terminal` | `8182affa798cf2d54ebd90cee0dfeb50c99b866ff467c0c24a28d268ee3d8f9f` | 2635 | 2026-10-27T14:43:34 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s2/T01-F1-W1/seed2`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；旧二进制副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
