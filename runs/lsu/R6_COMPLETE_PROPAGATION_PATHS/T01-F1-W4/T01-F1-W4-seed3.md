# T01-F1-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F1-W4` |
| seed | `3` |
| sample_run_id | `s3` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F1` |
| requested tier | `F1` |
| effective tier | `F1` |
| tier enabled | `开启(1)` |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（与矩阵标签一致） |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T01-F1-W4 --prop_sample_run_id s3` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/manifest.json`（`exit_code=null`；真实退出码 `.exit_code`=0） |
| 正常 EOF | **是**（解压后 3,261,995 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=5899247847`、`simInsts=8522055`、`finalTick=243849044862`、`numFaultsInjected=3` |
| 原始事件数 | `3445` |
| fault_id 数量 | `3`（fault 1 为代表故障；fault 2/3 见 §5） |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`；run.out 另有 `CHAOS_LSU_F6_EVENTS` 与 `CHAOS_LSU_NOEFFECT: effective_injected=3 no_effect=0`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 是 3 注入样本。escape-first 规则选出的代表故障是 **fault 1**（`full`，真实 L5）。fault 2 是 L2 含住，fault 3 是开放 L4 终局，均放在 §5。

fault 1 的祖先链 16 条：

`0 → 1 → 2 → 3 → 4(lq_read) → 5 → 6 → 7 → 8 → 9 → 10 → 35(resp) → 36(lq_complete) → 37(taint_reg) → 38(taint_reg) → 39(errant_commit)`

tick 段：239629862268、239629862601、239629970826、239629971492，单调不降。**本链的 resp（35）直接以 `mshr_alloc`（10）为父，fill/free 不在主链上**（在旁支），故本节不描述主链未发生的填充状态迁移。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=5536042`、`request_id=5536042`，VA=`0x7fe7c61d40`（页内偏移 `0xd40`）。表项 `entry_index=23`、`way=-1`、`walk_id=0`；注入前 `vpn=7fe7c61`、`asid=214`、`valid=1`、`global=0`、`pfn=83111`、`ap=1`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x83111d40`。本链含 `lq_read`/`lq_complete`，说明这是 **load** 路径。

### 2.2 故障具体如何注入

`event_id=0`，tick=`239629862268`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=5536042`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x200000000000`，即 PFN 第 45 位。原 PFN `0x83111` 异或后得 `0x200000083111`：把数值变化讲完整——第 45 位由 0 变 1，表项保存的 PFN 从 `0x83111` 变成 `0x2000_0008_3111`，其余位不变。第 45 位在物理地址中对应第 57 位；本 seed 的证据显示有效物理地址确实变成 `0x200000083111d40`，`tlb_translate_result` 判定 `effective_pa_changed`。**本 seed 属于"有效 PA 改变"的案例**；本文按证据记录，不对地址宽度细节作额外推断。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`239629862268`，`request_id=5536042`，`corr=seq_primary`，`entry_index=23`）记录 `field=post_lookup`，`before=83111`、`after=200000083111`；state 对照 `pfn=83111→200000083111`、`pa=83111d40→200000083111d40`。
`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=200000083111d40`、`state_before=83111d40`、`state_after=200000083111d40`。
`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）：`field=effective_pa_changed`、`before=83111d40`、`after=200000083111d40`、`contained=0`、`outcome=NoFault`。翻译本身无 fault，但因 PA 改变而不含住；错误 PA 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

`event_id=4`（`lq_read`，parent=3，tick=`239629862268`，`request_id=5536042`，`lq_idx=594678`）表明错误 PA 的 load 已在 LQ 内被读取/发射；`event_id=5`（`cache_access`，parent=4）以该错误 PA 发出请求。`lsq_push` 缺席，故"插入 LSQ 的时刻"为 `N/A`（证据缺席）；LQ 内 read→complete 完整。

### 2.5 错误如何经过 cache 和 MSHR

- 第一次：`event_id=5`（`cache_access`，parent=4，tick=`239629862268`，`request_id=5536042`）访问 `pa=200000083111d40`；`event_id=6`（`cache_return`）`field=miss`；`event_id=7`（`mshr_alloc`）`cache_line=200000083111d40`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=8`（`cache_access`，parent=7，tick=`239629862601`）再次访问同一个 `pa=200000083111d40`；`event_id=9` `miss`；`event_id=10`（`mshr_alloc`）`cache_line=200000083111d40`、`mshr_id=2`、`state_after=mshr_allocated`。两次同址访问分别分配 MSHR 1 与 2（记录上没有合并）。
- 返回：`event_id=35`（`resp`，parent=10，tick=`239629970826`，`corr=seq_primary`）。主链没有 fill/free；旁支有若干 `mshr_fill`/`cache_fill`/`mshr_free`，但不在终局祖先上。

同一 fault 的依据：`fault_id=1`、parent 连续、两次访问同一错误 PA。

### 2.6 污染如何返回处理器状态

`event_id=35`（`resp`，parent=10）的 `va` 字段为空（记录为 0）——这是**未盖戳**，不是"地址 0"。`event_id=36`（`lq_complete`，parent=35）同样带 `request_id=0`、`pa=0`、`va=7fe7c61d32`，也是记录口径上的缺失/偏移。随后：

- `event_id=37`（`taint_reg`，parent=36）`before=clean`、`after=tainted`、`arch_reg=4`、`phys_reg=68`；
- `event_id=38`（`taint_reg`，parent=37）`before=clean`、`after=tainted`、`arch_reg=5`、`phys_reg=153`。

两个寄存器在同一 tick 被标脏，是本 seed 的存储→CPU 边界。事件 35/36 的空/0 字段必须按"未记录"处理，不能当作真实请求 0 或真实 PA 0。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=39`，parent=38，tick=`239629971492`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=5536042`、`pc=7f82a0afd8`、`commit_seq=3687869`。错误提交就是最初 load 本身。为什么没被提前消除：L2 `contained=0`，本 seed 全流没有任何 `squash_masked`，提交前无拦截。`chain_end`（`event_id=3306`，tick=`243849044862`，`outcome=errant_commit_seen`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out 的 3 条 DETECT：

- `CHAOS_DETECT: layer=None contained=0 tick=239629971492 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=241738405947 ptag=2 reason=effective_pa_unchanged`（兄弟 fault 2 的 L2 含住）
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=243849044862 ptag=3 reason=store_discarded_not_retired`（兄弟 fault 3 的 store 丢弃）

以及 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`。run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.200000] Unable to handle kernel NULL pointer dereference at virtual address 0000000000000008`
- `[2.200000] Internal error: Oops: 96000045 [#1] PREEMPT SMP`

注入 tick=`239629862268`，错误提交 tick=`239629971492`，传播延迟 **109,224 ticks**。L5→Crash 因果成立。链终止 tick=`243849044862`。无应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit45 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=5536042） | 读到 `pfn=200000083111` | PA=`200000083111d40` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=200000083111d40` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L3 LQ | load（`lq_idx=594678`） | read | 访存请求 | 错误进入 LQ |
| L3 L1D | 同址两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | 分配 MSHR 1/2 | `mshr_alloc` | 请求挂起 |
| L3 L1D→core resp | MSHR 2 请求 | 返回（va 未盖戳） | `resp` | 污染回到核心 |
| L3 LQ complete | load 完成 | 字段未盖戳 | 生命周期收口 | 值就绪 |
| L4 taint/regfile | 完成的 load | clean→tainted ×2 | **arch4/phys68、arch5/phys153** | 存储→CPU 边界 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=5536042` | 架构可见错误 |
| SQ / fill | — | — | — | `N/A`（load 路径；主链无 fill） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 45 位置 1，PA 从 `0x83111d40` 变成 `0x200000083111d40`；翻译结果记录 `effective_pa_changed/contained=0`，load 经 LQ（`lq_idx=594678`）发出，错误地址被同址访问两次、两次未命中并分配 MSHR 1/2，`resp`→`lq_complete`→两个 `taint_reg`（arch4/phys68、arch5/phys153）把污点带入寄存器，最终该 load 本身在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=3527639 eligible=3527639 injected=3`；`numFaultsInjected=3`；注入日志 3 条。三处一致。代表故障（fault 1）的污染值被 lookup 与 LQ/cache 真实消费，属于 activated。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`200000083111d40`）。不是 data/permission/control-state 型（`ap`/`valid` 未变）。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：显式 `effective_pa_changed`+`contained=0`，结构放弃撤销；`event_id=4` 的 `lq_read` 立即消费。

### 3.4 检测与掩蔽机制

候选：翻译结果 PA 比对（有，只在 PA 未变时含住）、权限/对齐异常（无）、ECC/parity（`model=none`）、squash/replay（本 run 0 条）、commit 前检查（无）。兄弟 fault 2 的 L2 含住（`effective_pa_unchanged`）与 fault 3 的 store 丢弃属于**其它注入**的收口，不能用来解释 fault 1 的逃逸。盲点：对 fault 1，PA 改变后无第二道检查，也没有 squash 兜底。

### 3.5 最终 SDC 风险判断

代表故障有真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：双寄存器污染到提交之间，污染值被后续指令观测；`consumer_summary` 2562 条记录、`logical_total=2184865`、`by_outcome=sd_observed`（§5）。无应用 oracle 行，**最终数据正确性不可判**。兄弟 fault 2 被 L2 含住、fault 3 开放 L4（store 丢弃）说明同一 run 中并非所有注入都逃逸，但也不能把 fault 3 的"store 丢弃"升格为已证明安全。

### 3.6 与同 RunID 其他 seed 的关系

- 掩码：seed1=`0x400000000000`（bit46）、seed2=`0x2`（bit1）、seed3=`0x200000000000`（bit45）。
- PA：seed1 `81d75b48→400000081d75b48`；seed2 `8313bd08→83139d08`；seed3 `83111d40→200000083111d40`。
- 终局：三者都是 L5 `errant_commit`（69/20/39）；seed2/seed3 的 errant 是最初访问本身，seed1 是更年轻指令。
- 运行结局：三者都是 Crash，Oops 码不同（86000004 / 82000005 / 96000045）。
- 多注入：seed1 1 个、seed2 5 个、seed3 3 个；seed3 的兄弟 fault 2 是 L2 含住、fault 3 是开放 L4。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 16 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239629862268 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | 83111 | 200000083111 | 83111 | 200000083111 | 0x200000000000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit45 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 239629862268 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | 83111 | 200000083111 | 83111 | 200000083111 | — | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40 | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=200000083111;ap=1;mtype=2;page_size=1000;pa=200000083111d40 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 239629862268 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | 200000083111d40 | — | — | 83111 | 200000083111 | 83111 | 200000083111 | — | 83111d40 | 200000083111d40 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 239629862268 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | 200000083111d40 | — | — | — | — | 83111d40 | 200000083111d40 | — | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40 | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=200000083111;ap=1;mtype=2;page_size=1000;pa=200000083111d40 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 239629862268 | 0 | `lq_read` | L3 | LQ | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | load，`lq_idx=594678` | 读取队列条目 | 错误进入 LQ |
| 6 | 5 | 4 | 239629862268 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | 7fe7c61d40 | 200000083111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 读取 | 首次访问 | 错误被消费 |
| 7 | 6 | 5 | 239629862268 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | — | 200000083111d40 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 8 | 7 | 6 | 239629862268 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 200000083111d40 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 9 | 8 | 7 | 239629862601 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | 7fe7c61d40 | 200000083111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同址再次访问 | 第二次访问 | 再次消费 |
| 10 | 9 | 8 | 239629862601 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | — | 200000083111d40 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 11 | 10 | 9 | 239629862601 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 200000083111d40 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 12 | 35 | 10 | 239629970826 | 108225 | `resp` | L3 | L1D→core resp | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回（va 未盖戳） | 污染回到核心 | 污染回到核心 |
| 13 | 36 | 35 | 239629970826 | 0 | `lq_complete` | L3 | LQ | 1 | seq_primary | 0 | 5536042 | 7fe7c61d32 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | load 完成 | 值就绪 | load 完成 |
| 14 | 37 | 36 | 239629970826 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | clean→tainted | 存储→CPU 边界 | 存储→CPU 边界 |
| 15 | 38 | 37 | 239629970826 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | clean→tainted | 第二个寄存器被污染 | 存储→CPU 边界 |
| 16 | 39 | 38 | 239629971492 | 666 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 5536042 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 3445 条事件，分属 3 个 fault；主链 16 条（fault 1），其余为旁支。

1. **fault 1 的兄弟请求与消费者**：136 条 `request_fork`、148 条 `cache_access`、148 条 `cache_return`、16 条 `mshr_alloc`、10 条 `mshr_fill`、10 条 `cache_fill`、10 条 `mshr_free`、136 条 `resp`、136 条 `taint_reg`、95 条 `lq_complete` 等；`consumer_summary` 2562 条（其中 fault 1 与 fault 3 各有 1281 条）、`logical_total=2184865`、`conservation=ok`。本 run **没有** `squash_masked`。
2. **fault 2（L2 含住）**：`event_id=1345`（inj，tick=`241738405947`，VA=`ffffffc008bf9e28`，`old=80bf9 → new=20000000080bf9`，掩码 `0x20000000000000`）；`event_id=1348` 记录 `field=effective_pa_unchanged`、`detection_layer=L2`、`contained=1`、`outcome=NoFault`、`reason=effective_pa_unchanged`（PA `80bf9e28→80bf9e28`）。这是真实含住；`chain_end` 3307 只是收口。
3. **fault 3（开放 L4）**：`event_id=1349`（inj，tick=`242526584313`，VA=`ffffff807fbda129`，`old=ffbda → new=bfbda`，掩码 `0x40000`），2087 条事件，无 `errant_commit`；`chain_end` 3308 记录 `detection_layer=L4`、`contained=1`、`outcome=detected_contained`、`reason=store_discarded_not_retired`。checker 对它的裁决是 `provable_to_L4_then_unknown`（开放终局），不能当作"已证明安全"。

旁支不构成第二条终局祖先；fault 2 的 L2 含住与 fault 3 的开放 L4 必须与 fault 1 的 L5 分开陈述。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（代表故障真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=39，tick=239629971492，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效（`numFaultsInjected=3` 与 injected=3 一致） |
| conservation | `ok`（2562 条 summary；`logical_total=2184865`） |
| count_contradiction | 否（attempted=3527639>0；injected=3=stats=3） |
| campaign/checker agreement | **两套口径并列（不是数据矛盾）**：campaign 为 run 级 outcome（本次运行 Crash）× activated 数 → `classes.Crash=3`；checker 为 per-fault 终局（1 full（fault 1）+ 1 L2 contained（fault 2）+ 1 open L4（fault 3））。样本级结论一致 |
| CHAIN_DEMONSTRATED | 是（fault 1 的 `inj`→L5 单祖先连续） |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **MATCH** |
| overall_experiment_status | **PASS** |
| verdict | **PASS** |

**计数口径（两套并列，不是矛盾）**：

1. campaign 的 `classes.Crash=3` 是 run 级 outcome（本次运行 Crash）乘以 activated fault 数（3），不是“3 条链都到 L5”。
2. checker 的逐 fault 终局为 1 full（fault 1）+ 1 L2 contained（fault 2）+ 1 open L4（fault 3）；代表故障按 escape-first 选 fault 1（唯一 `full`）。
3. 两者统计单元不同，样本级结论一致；详见 `R6-T01-F1-W4-MULTIFAULT-RECHECK.md`。

**保留的元数据/证据缺口（不改变 PASS）**：

1. 矩阵字段口径（VPN tag）与证据（PFN）不一致。
2. 主链代表故障 fault 1 的 `taint_reg` event 37 带 `arch_reg=4`、`phys_reg=68`；流内 138 条 `taint_reg` 中仍有 41 条缺这两个字段，属字段覆盖缺口，不伪造。

工作负载标签（TLB-AliasPerm 探针）与实际 `tlb_probe.rcS` 一致，这一项不构成 REVIEW。

一致性自检：16 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调不降；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致（并解释 35/36 的未盖戳字段）；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/prop_evt.txt.gz` | `381505282524dd5ff1e6fcd0c460373b7b0c1100cc5362977f90e8ecd746b148` | 238314 | 2026-10-27T02:49:03 |
| chain_report（权威） | `.../seed3/chain_report.json` | `14ec8e317af555b62a5518ed6c0c6e5b8b15ed54db3ccf2ac65ed375c1fecd1c` | 2235184 | 2026-10-27T02:49:04 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed3/run.out` | `e24668260bd66b71cd57a97854e2ce68def402496e6d9056b72c29ca9f5360ed` | 2746 | 2026-10-27T02:49:04 |
| run.err | `.../seed3/run.err` | `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17` | 1973 | 2026-10-27T02:49:04 |
| stats.txt | `.../seed3/stats.txt` | `be44142668df0e3b72b9d51653e465df9795563198c5aefc22d7fae44a34b4c6` | 423390 | 2026-10-27T02:49:04 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/manifest.json` | `454a07ea4c876dba80411859e79c22855717f67a61a451df58253afdaf3bf20d` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | — | — |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed3/board.workload.dmesg` | `bea48611f050d1482d4e4401d9383b6cfb4a59a753fcf8c1d4508b45ea532823` | 13845 | 2026-10-27T02:49:04 |
| 辅助证据（terminal） | `.../seed3/board.terminal` | `841977daab436d307236cd65e38fab71a0f41497e5cda90bd64ab2ef9c3e3b2c` | 1787 | 2026-10-27T02:49:04 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；旧二进制副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
