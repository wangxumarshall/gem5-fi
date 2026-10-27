# T01-F1-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F1-W4` |
| seed | `2` |
| sample_run_id | `s2` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F1` |
| requested tier | `F1` |
| effective tier | `F1` |
| tier enabled | `开启(1)` |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（与矩阵标签一致） |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s2/T01-F1-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T01-F1-W4 --prop_sample_run_id s2` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s2/T01-F1-W4/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s2/manifest.json`（`exit_code=null`；真实退出码 `.exit_code`=0） |
| 正常 EOF | **是**（解压后 21,508,966 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=8390204730`、`simInsts=13049826`、`finalTick=246340001745`、`numFaultsInjected=5` |
| 原始事件数 | `30172` |
| fault_id 数量 | `5`（fault 1–5；另有 632 条 `fault_id=0` 的 `pf_demand` 事件） |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`；run.out 另有 `CHAOS_LSU_F6_EVENTS` 与 `CHAOS_LSU_NOEFFECT: effective_injected=5 no_effect=0`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 是 5 注入样本。escape-first 规则选出的代表故障是 **fault 1**（`full`，真实 L5）。fault 2–5 的终局各不相同（两个 L2 含住、两个开放 L4），全部放在 §5，绝不并入 fault 1 的祖先链。

fault 1 的祖先链 21 条：

`0 → 1 → 2 → 3 → 4(lq_read) → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17(resp) → 18(lq_complete) → 19(taint_reg) → 20(errant_commit)`

tick 段：239345234181、239345234514、239345293455、239345294121、239345294454、239345295120，单调不降。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=4338322`、`request_id=4338322`，VA=`0x7f82b83d08`（页内偏移 `0xd08`）。表项 `entry_index=29`、`way=-1`、`walk_id=0`；注入前 `vpn=7f82b83`、`asid=214`、`valid=1`、`global=0`、`pfn=8313b`、`ap=3`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x8313bd08`。本链含 `lq_read`/`lq_complete`，说明这是 **load** 路径。

### 2.2 故障具体如何注入

`event_id=0`，tick=`239345234181`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=4338322`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x2`，即 PFN 第 1 位。原 PFN `0x8313b` 异或后得 `0x83139`：把数值变化讲完整——第 1 位由 1 变 0，表项保存的 PFN 从 `0x8313b` 变成 `0x83139`，即数值减二；由于 PFN 左移 12 位构成页基址，物理地址从 `0x8313bd08` 变成 `0x83139d08`（相差 `0x2000`，两页）。`effective_pa_changed` 为真。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`239345234181`，`request_id=4338322`，`corr=seq_primary`，`entry_index=29`）记录 `field=post_lookup`，`before=8313b`、`after=83139`；state 对照 `pfn=8313b→83139`、`pa=8313bd08→83139d08`。
`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=83139d08`、`state_before=8313bd08`、`state_after=83139d08`。
`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）：`field=effective_pa_changed`、`before=8313bd08`、`after=83139d08`、`contained=0`、`outcome=NoFault`。翻译本身无 fault，但因 PA 改变而不含住；错误 PA 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

`event_id=4`（`lq_read`，parent=3，tick=`239345234181`，`request_id=4338322`，`lq_idx=470727`）表明错误 PA 的 load 已在 LQ 内被读取/发射；`event_id=5`（`cache_access`，parent=4）以该错误 PA 发出请求。`lsq_push` 缺席，故"插入 LSQ 的时刻"为 `N/A`（证据缺席）；LQ 内 read→complete 完整。

### 2.5 错误如何经过 cache 和 MSHR

- 第一次：`event_id=5`（`cache_access`，parent=4，tick=`239345234181`，`request_id=4338322`）访问 `pa=83139d08`；`event_id=6`（`cache_return`）`field=miss`；`event_id=7`（`mshr_alloc`）`cache_line=83139d08`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=8`（`cache_access`，parent=7，tick=`239345234514`）访问同一行基址 `pa=83139d00`；`event_id=9` `miss`；`event_id=10`（`mshr_alloc`）`cache_line=83139d00`、`mshr_id=2`、`state_after=mshr_allocated`。
- 填充与释放：`event_id=11`（`mshr_fill`，parent=10，tick=`239345293455`）`mshr_id=2`、`state_after=filled`；`event_id=12`（`cache_fill`）填行；`event_id=13`（`mshr_free`）`mshr_id=2`、`state_after=mshr_freed`。随后 `event_id=14`（`mshr_fill`，parent=13，tick=`239345294121`）`mshr_id=0`、`state_after=filled`；`event_id=15`（`cache_fill`）；`event_id=16`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

状态迁移：miss→alloc→fill→cache_fill→free。`mshr_id=0` 为原值。同一 fault 的依据：`fault_id=1`、parent 连续、两次访问同属错误 PA 所在行（`...d08` 与行基址 `...d00`）。

### 2.6 污染如何返回处理器状态

`event_id=17`（`resp`，parent=16，tick=`239345294454`，`request_id=4338322`，`corr=seq_primary`，`va=83139d08`）返回响应；`event_id=18`（`lq_complete`，parent=17，同 tick，`request_id=4338322`，`pa=83139d08`，`lq_idx=470727`）完成 load；`event_id=19`（`taint_reg`，parent=18）明确记录 `before=clean`、`after=tainted`、`va=83139d08`、`arch_reg=12`、`phys_reg=110`。这是存储→CPU 边界：污点落到体系结构寄存器 12 / 物理寄存器 110。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=20`，parent=19，tick=`239345295120`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=4338322`、`pc=7f82b8e3c4`、`commit_seq=2988647`。错误提交就是最初 load 本身。为什么没被提前消除：L2 `contained=0`；fault 1 唯一的 squash（`event_id=265`，tick=`239349866544`）晚于错误提交（§5）；提交前无拦截。`chain_end`（`event_id=26946`，tick=`246340001745`，`outcome=errant_commit_seen`，`reason=squash_replay`）只是流关闭记录（它的 `parent_event_id=312` 说明收口是按 fault 分别发出的），不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out 的 5 条 DETECT：

- `CHAOS_DETECT: layer=None contained=0 tick=239345295120 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=239349866544 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=240400096929 ptag=2 reason=effective_pa_unchanged`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=243461336292 ptag=4 reason=effective_pa_unchanged`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=246340001745 ptag=5 reason=store_discarded_not_retired`

以及 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`。run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.200000] Call trace:`
- `[2.200000] Unable to handle kernel NULL pointer dereference at virtual address 0000000000000000`
- `[2.200000] Internal error: Oops: 82000005 [#1] PREEMPT SMP`

注入 tick=`239345234181`，错误提交 tick=`239345295120`，传播延迟 **60,939 ticks**。L5→Crash 因果成立。链终止 tick=`246340001745`。无应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit1 置 0 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=4338322） | 读到 `pfn=83139` | PA=`83139d08` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=83139d08` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L3 LQ | load（`lq_idx=470727`） | read | 访存请求 | 错误进入 LQ |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | MSHR 1/2，fill/free（2、0） | 填充完成 | 请求挂起与回收 |
| L3 L1D→core resp | 填充完成 | 返回 | `resp`（req=4338322） | 污染回到核心 |
| L3 LQ complete | load 完成 | `lq_idx=470727` | 生命周期收口 | 值就绪 |
| L4 taint/regfile | response | clean→tainted | **arch12/phys110 被标脏** | 存储→CPU 边界 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=4338322` | 架构可见错误 |
| SQ | — | — | — | `N/A`（load 路径） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 1 位置 0（PFN 减二），PA 从 `0x8313bd08` 变成 `0x83139d08`；翻译结果记录 `effective_pa_changed/contained=0`，load 经 LQ（`lq_idx=470727`）发出，错误地址在 L1D 两次未命中并由 MSHR 2/0 完成填充与释放，`resp`→`lq_complete`→`taint_reg`（arch12/phys110）把污点带入寄存器，最终该 load 本身在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=5530941 eligible=5530941 injected=5`；`numFaultsInjected=5`；注入日志 5 条。三处一致。代表故障（fault 1）的污染值被 lookup 与 LQ/cache 真实消费，属于 activated。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`83139d08`/`d00`）。不是 data/permission/control-state 型（`ap=3` 等属性未变）。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：显式 `effective_pa_changed`+`contained=0`，结构放弃撤销；`event_id=4` 的 `lq_read` 立即消费。

### 3.4 检测与掩蔽机制

候选：翻译结果 PA 比对（有，只在 PA 未变时含住）、权限/对齐异常（无）、ECC/parity（`model=none`）、squash/replay（fault 1 有 1 条，晚于错误提交；fault 2/4 的 L2 含住与 fault 5 的 store 丢弃属于兄弟故障）、commit 前检查（无）。盲点：PA 改变后无第二道检查；对 fault 1 而言，squash 只影响更年轻指令。

### 3.5 最终 SDC 风险判断

代表故障有真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：event 19→20 之间污染值被后续指令观测；`consumer_summary` 1297 条记录、`logical_total=11484`、`by_outcome=sd_observed`（§5）。无应用 oracle 行，**最终数据正确性不可判**。另外必须区分：兄弟 fault 2/4 被 L2 含住（`effective_pa_unchanged`），说明**同一个 run 里并非所有注入都逃逸**；但 fault 3/5 是开放 L4 终局（一个 `run_end`、一个 `store_discarded_not_retired`），不能当作"已被证明安全"。

### 3.6 与同 RunID 其他 seed 的关系

- 掩码：seed1=`0x400000000000`（bit46）、seed2=`0x2`（bit1）、seed3=`0x200000000000`（bit45）。
- PA：seed1 `81d75b48→400000081d75b48`；seed2 `8313bd08→83139d08`；seed3 `83111d40→200000083111d40`。
- 终局：三者都是 L5 `errant_commit`（69/20/39）；seed1 是更年轻指令，seed2/seed3 是最初访问本身。
- 运行结局：三者都是 Crash，Oops 码不同（seed1 86000004；seed2 82000005；seed3 96000045）。
- 多注入：seed1 1 个、seed2 5 个、seed3 3 个；只有 seed2/seed3 出现 L2 含住的兄弟故障。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 21 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239345234181 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 4338322 | 4338322 | 7f82b83d08 | — | — | — | 8313b | 83139 | 8313b | 83139 | 0x2 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit1 置 0 | 故障进入存储 |
| 2 | 1 | 0 | 239345234181 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | — | — | — | 8313b | 83139 | 8313b | 83139 | — | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08 | vpn=7f82b83;asid=214;valid=1;global=0;pfn=83139;ap=3;mtype=2;page_size=1000;pa=83139d08 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 239345234181 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 83139d08 | — | — | 8313b | 83139 | 8313b | 83139 | — | 8313bd08 | 83139d08 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 239345234181 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 83139d08 | — | — | — | — | 8313bd08 | 83139d08 | — | vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08 | vpn=7f82b83;asid=214;valid=1;global=0;pfn=83139;ap=3;mtype=2;page_size=1000;pa=83139d08 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 239345234181 | 0 | `lq_read` | L3 | LQ | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | load，`lq_idx=470727` | 读取队列条目 | 错误进入 LQ |
| 6 | 5 | 4 | 239345234181 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | 7f82b83d08 | 83139d08 | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 读取 | 首次访问 | 错误被消费 |
| 7 | 6 | 5 | 239345234181 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | — | 83139d08 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 8 | 7 | 6 | 239345234181 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 83139d08 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 9 | 8 | 7 | 239345234514 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | 7f82b83d08 | 83139d00 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费 |
| 10 | 9 | 8 | 239345234514 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 4338322 | 4338322 | — | 83139d00 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 11 | 10 | 9 | 239345234514 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 83139d00 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 12 | 11 | 10 | 239345293455 | 58941 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 83139d00 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 2 填充 | 数据就绪 |
| 13 | 12 | 11 | 239345293455 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 4338322 | 4338322 | — | 83139d00 | 83139d00 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 | 行可用 |
| 14 | 13 | 12 | 239345293455 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 83139d00 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 资源回收 |
| 15 | 14 | 13 | 239345294121 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 83139d00 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 再次填充 | `mshr_id=0` 填充 | 原值保留 |
| 16 | 15 | 14 | 239345294121 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 4338322 | 4338322 | — | 83139d00 | 83139d00 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 17 | 16 | 15 | 239345294121 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 4338322 | 4338322 | — | — | 83139d00 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 18 | 17 | 16 | 239345294454 | 333 | `resp` | L3 | L1D→core resp | 1 | seq_primary | 4338322 | 4338322 | 83139d08 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 19 | 18 | 17 | 239345294454 | 0 | `lq_complete` | L3 | LQ | 1 | seq_primary | 4338322 | 4338322 | 7f82b83d08 | 83139d08 | — | — | — | — | — | — | — | — | — | — | — | — | — | load 完成 | 值就绪 | load 完成 |
| 20 | 19 | 18 | 239345294454 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | 4338322 | 4338322 | 83139d08 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | clean→tainted | 存储→CPU 边界 | 存储→CPU 边界 |
| 21 | 20 | 19 | 239345295120 | 666 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 4338322 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 30172 条事件。主链只覆盖 fault 1 的 21 条；旁支包括：

1. **fault 1 的兄弟请求与消费者**：3221 条 `request_fork`、3739 条 `cache_access`、3739 条 `cache_return`、678 条 `mshr_alloc`、3006 条 `mshr_merge`、3204 条 `resp`、3213 条 `taint_reg`、2930 条 `lq_complete`、1314 条 `consumer`；`consumer_summary` 1297 条、`logical_total=11484`、`conservation=ok`。fault 1 另有 1 条 `squash_masked`：`event_id=265`，tick=`239349866544`，事件自身 `detection_layer=L4`、`contained=1`、`outcome=masked`、`reason=squash_replay`、`dyn_inst_seq=4366204`，晚于错误提交。
2. **fault 2（L2 含住）**：`event_id=313`（inj，tick=`240400096929`，VA=`ffffffc00949bc50`，`old=81ce3 → new=800000000081ce3`，掩码 `0x800000000000000`），随后 lookup/pfn/translate；`event_id=316` 记录 `field=effective_pa_unchanged`、`detection_layer=L2`、`contained=1`、`outcome=NoFault`、`reason=effective_pa_unchanged`（PA `81ce3c50→81ce3c50`）。这是真实的 L2 含住事件，`chain_end` 26947 只是收口。
3. **fault 3（开放 L4）**：`event_id=317`（inj，tick=`241705664388`，VA=`5582e34e31`，`old=8319a → new=80008319a`，掩码 `0x800000000`），26735 条事件，无 `errant_commit`；`chain_end` 26948 的 `outcome=run_end`、无检测层。checker 裁决 `provable_to_L4_then_unknown`——开放终局，不能当作安全或已证明。
4. **fault 4（L2 含住）**：`event_id=24805`（inj，tick=`243461336292`，VA=`ffffffc00948b9c0`，`old=81c44 → new=1000000000081c44`，掩码 `0x1000000000000000`）；`event_id=24808` 记录 `effective_pa_unchanged`、L2、`contained=1`（PA `81c449c0→81c449c0`）。
5. **fault 5（开放 L4）**：`event_id=24809`（inj，tick=`244620082386`，VA=`ffffffc00948b9e0`，`old=81c44 → new=8081c44`，掩码 `0x8000000`），2425 条事件，无 `errant_commit`；`chain_end` 26950 记录 `detection_layer=L4`、`contained=1`、`outcome=detected_contained`、`reason=store_discarded_not_retired`（store 被丢弃），但 checker 对该 fault 的裁决仍是 `provable_to_L4_then_unknown`（开放）。
6. **632 条 `fault_id=0` 的 `pf_demand`**：不属于任何注入故障，是该构建的预取侧记录，绝不能归入任何一个 fault。

旁支不构成第二条终局祖先；fault 2/4 的真实含住与 fault 3/5 的开放终局必须分别陈述，不能合并成"全部含住"或"全部逃逸"。

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
| stats validity | 有效（`numFaultsInjected=5` 与 injected=5 一致） |
| conservation | `ok`（1297 条 summary；`logical_total=11484`） |
| count_contradiction | 否（attempted=5530941>0；injected=5=stats=5） |
| campaign/checker agreement | **两套口径并列（不是数据矛盾）**：campaign 为 run 级 outcome（本次运行 Crash）× activated 数 → `classes.Crash=5`；checker 为 per-fault 终局（1 full（fault 1）+ 2 L2 contained（fault 2、4）+ 2 open L4（fault 3、5））。样本级结论一致 |
| CHAIN_DEMONSTRATED | 是（fault 1 的 `inj`→L5 单祖先连续） |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **MATCH** |
| overall_experiment_status | **PASS** |
| verdict | **PASS** |

**计数口径（两套并列，不是矛盾）**：

1. campaign 的 `classes.Crash=5` 是 run 级 outcome（本次运行 Crash）乘以 activated fault 数（5），不是“5 条链都到 L5”。
2. checker 的逐 fault 终局为 1 full（fault 1）+ 2 L2 contained（fault 2、4）+ 2 open L4（fault 3、5）；代表故障按 escape-first 选 fault 1（唯一 `full`）。
3. 两者统计单元不同，样本级结论一致；详见 `R6-T01-F1-W4-MULTIFAULT-RECHECK.md`。

**保留的元数据/证据缺口（不改变 PASS）**：

1. 矩阵字段口径（VPN tag）与证据（PFN）不一致。
2. 主链代表故障 fault 1 的 `taint_reg` event 19 带 `arch_reg=12`、`phys_reg=110`；流内 3214 条 `taint_reg` 中仍有 274 条缺这两个字段（含 sibling fault 5 的主链 event 24870），属字段覆盖缺口，不伪造。
3. 本 seed 的 `fault_id=0` 预取事件（632 条）不属于任何注入，按 fault 聚合时必须排除。

工作负载标签（TLB-AliasPerm 探针）与实际 `tlb_probe.rcS` 一致，这一项不构成 REVIEW。

一致性自检：21 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调不降；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界（区分了 L2 含住、L4 开放与 L5 逃逸）。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s2/T01-F1-W4/seed2/prop_evt.txt.gz` | `21417fbd5166ff021aa84145fb67b38245bf56147389f7dde333f5bb5192f394` | 1106134 | 2026-10-27T02:47:09 |
| chain_report（权威） | `.../seed2/chain_report.json` | `e95718e5a1528e861640b65f750148bba5d8271426c552c52b9341ab01e022de` | 1105501 | 2026-10-27T02:47:12 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed2/run.out` | `8056e4edee172757e838e1eb97acd0d8e7cb9830e74e79137795e0aadee6ec01` | 2938 | 2026-10-27T02:47:09 |
| run.err | `.../seed2/run.err` | `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36` | 1873 | 2026-10-27T02:47:09 |
| stats.txt | `.../seed2/stats.txt` | `ece2481c5ce96a7ec3c44af62ad4b9b70cb6e0f1735760080897cb7555f447a4` | 423751 | 2026-10-27T02:47:09 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s2/manifest.json` | `0c88f33c972735354d34344cc2db0463ac4220c25f9e89ce42d1144d5a37902e` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | — | — |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed2/board.workload.dmesg` | `e242d7f433d74be6a5ad6af0731e3e668b2f35fac97f46caac0a76a7e263282b` | 14608 | 2026-10-27T02:47:09 |
| 辅助证据（terminal） | `.../seed2/board.terminal` | `75e19db226cc69a9ea668635e4b4b3a060b9e228cede05c5955ca2e4f8833389` | 2635 | 2026-10-27T02:47:09 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s2/T01-F1-W4/seed2`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；旧二进制副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
