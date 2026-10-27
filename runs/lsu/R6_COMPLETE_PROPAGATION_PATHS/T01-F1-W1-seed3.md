# T01-F1-W1 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F1-W1` |
| seed | `3` |
| sample_run_id | `s3` |
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
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3/T01-F1-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F1 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T01-F1-W1 --prop_sample_run_id s3` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3/T01-F1-W1/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3/manifest.json`（`exit_code=null`；真实退出码 `.exit_code`=0） |
| 正常 EOF | **是**（解压后 18,541,249 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=5433485742`、`simInsts=8265921`、`finalTick=243383282757`、`numFaultsInjected=3` |
| 原始事件数 | `25388` |
| fault_id 数量 | `3`（fault 1 为代表故障；fault 2/3 见 §5） |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`。本 seed 是 F1 多注入样本：`injected=3`、`stats.numFaultsInjected=3`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 有 3 条 fault 流。按 checker 的 escape-first 规则，代表故障是 **fault 1**（`full`，真实 L5 `errant_commit`）；fault 2/3 的终局由 squash 收口（checker 记为 `detected_contained`，事件自身声明 L4），放在 §5，绝不并入 fault 1 的主链。

fault 1 的祖先链 22 条：

`0 → 1 → 2 → 3 → 4(lq_read) → 5 → 6 → 7 → 8 → 9 → 10 → 35 → 36 → 37 → 38 → 39 → 40 → 41(resp) → 42(lq_complete) → 43(taint_reg) → 44(taint_reg) → 45(errant_commit)`

tick 段：239629862268、239629862601、239629921542、239629922208、239629922541、239629923207，单调不降（逐条 Δtick 见 §4）。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=5536042`、`request_id=5536042`，VA=`0x7fe7c61d40`（页内偏移 `0xd40`）。表项 `entry_index=23`、`way=-1`、`walk_id=0`；注入前 `vpn=7fe7c61`、`asid=214`、`valid=1`、`global=0`、`pfn=83111`、`ap=1`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x83111d40`。本链含 `lq_read`/`lq_complete`，说明这是 **load** 路径。

### 2.2 故障具体如何注入

`event_id=0`，tick=`239629862268`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=5536042`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x4000`，即 PFN 第 14 位。原 PFN `0x83111` 异或后得 `0x87111`：把数值变化讲完整——第 14 位由 0 变 1，表项保存的 PFN 从 `0x83111` 变成 `0x87111`，其余位不变。第 14 位在物理地址中对应第 26 位，落在有效 PA 宽度内，因此有效物理地址从 `0x83111d40` 变成 `0x87111d40`，`effective_pa_changed` 为真。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`239629862268`，`request_id=5536042`，`corr=seq_primary`，`entry_index=23`）记录 `field=post_lookup`，`before=83111`、`after=87111`；state 对照 `pfn=83111→87111`、`pa=83111d40→87111d40`。

`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=87111d40`、`state_before=83111d40`、`state_after=87111d40`。

`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）：`field=effective_pa_changed`、`before=83111d40`、`after=87111d40`、`contained=0`、`outcome=NoFault`。翻译本身无 fault，但因 PA 改变而不含住；错误 PA 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

`event_id=4`（`lq_read`，parent=3，tick=`239629862268`，`request_id=5536042`，`lq_idx=594678`）表明错误 PA 的 load 已在 LQ 内被读取/发射；`event_id=5`（`cache_access`，parent=4）以该错误 PA 发出请求。`lsq_push` 缺席，故"插入 LSQ 的时刻"为 `N/A`（证据缺席）；LQ 内的 read→complete 生命周期完整。

### 2.5 错误如何经过 cache 和 MSHR

本 seed 的两次访问**地址相同**（都是 `pa=87111d40`），这是与同 RunID 其它 seed（第二次访问行基址）不同的事实：

- 第一次：`event_id=5`（`cache_access`，parent=4，tick=`239629862268`，`request_id=5536042`）访问 `pa=87111d40`；`event_id=6`（`cache_return`）`field=miss`；`event_id=7`（`mshr_alloc`）`cache_line=87111d40`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=8`（`cache_access`，parent=7，tick=`239629862601`）再次访问同一个 `pa=87111d40`；`event_id=9` `miss`；`event_id=10`（`mshr_alloc`）`cache_line=87111d40`、`mshr_id=2`、`state_after=mshr_allocated`。两次同址访问分别分配 MSHR 1 与 2，说明它们没有被合并为一次（或记录上没有体现 `mshr_merge`）。
- 填充与释放：`event_id=35`（`mshr_fill`，parent=10，tick=`239629921542`）`mshr_id=2`、`state_after=filled`；`event_id=36`（`cache_fill`）填行；`event_id=37`（`mshr_free`）`mshr_id=2`、`state_after=mshr_freed`。随后 `event_id=38`（`mshr_fill`，parent=37，tick=`239629922208`）`mshr_id=0`、`state_after=filled`；`event_id=39`（`cache_fill`）；`event_id=40`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

状态迁移：miss→alloc→fill→cache_fill→free。同一 fault 的依据：`fault_id=1`、parent 连续、两次访问同一错误 PA。第一次访问的 MSHR 1 在主链上没有 fill/free（旁支有）。

### 2.6 污染如何返回处理器状态

`event_id=41`（`resp`，parent=40，tick=`239629922541`，`corr=seq_primary`）的 `va` 字段为空（记录为 0），这属于**未盖戳**，不是"地址 0"。`event_id=42`（`lq_complete`，parent=41）同样带 `request_id=0`、`pa=0`、`va=7fe7c61d32`，这些都是记录口径上的缺失/偏移，不能当作真实请求 0 或真实 PA 0。随后：

- `event_id=43`（`taint_reg`，parent=42）`before=clean`、`after=tainted`、`arch_reg=4`、`phys_reg=68`；
- `event_id=44`（`taint_reg`，parent=43）`before=clean`、`after=tainted`、`arch_reg=5`、`phys_reg=153`。

两个寄存器在同一 tick 被标脏，是本 seed 的存储→CPU 边界。要明确：事件 41/42 的空/0 字段是"未记录"，而 43/44 的寄存器号是真实记录；两者不能互相替代。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=45`，parent=44，tick=`239629923207`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=5536042`、`pc=7f82a0afd8`、`commit_seq=3687869`。错误提交就是最初 load（`5536042`）本身。为什么没被提前消除：L2 明确 `contained=0`；本 fault 自身有 3 条 squash（event 86/87/101，全部晚于错误提交），其余 99 条 squash 属于 fault 2/3（见 §5），提交前无拦截。`chain_end`（`event_id=21443`，tick=`243383282757`，`outcome=errant_commit_seen`，`reason=squash_replay`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out：

- `CHAOS_DETECT: layer=None contained=0 tick=239629923207 ptag=1 reason=errant_commit`
- 之后 102 条 `CHAOS_DETECT ... reason=squash_replay`（ptag=1 三条、ptag=2 若干等），全部晚于错误提交
- 其余 102 条全部是 `squash_replay`；**run.out 中没有 ptag=2/3 的 `effective_pa_unchanged` 行**，尽管 `prop_evt` 的 fault 2（event 1348）记录了 L2 `contained=1`——这是一处必须复核的证据不一致（见 §6 理由 4）
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.200000] Unable to handle kernel paging request at virtual address 0020000000000000`
- `[2.200000] Internal error: Oops: 86000004 [#1] PREEMPT SMP`

注入 tick=`239629862268`，错误提交 tick=`239629923207`，传播延迟 **60,939 ticks**。L5→Crash 因果成立。链终止 tick=`243383282757`。无应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit14 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=5536042） | 读到 `pfn=87111` | PA=`87111d40` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=87111d40` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L3 LQ | load（`lq_idx=594678`） | read | 访存请求 | 错误进入 LQ |
| L3 L1D | 同址两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | MSHR 1/2，fill/free（2、0） | 填充完成 | 请求挂起与回收 |
| L3 L1D→core resp | 填充完成 | 返回（va 未盖戳） | `resp` | 污染回到核心 |
| L3 LQ complete | load 完成 | 字段未盖戳 | 生命周期收口 | 值就绪 |
| L4 taint/regfile | 完成的 load | clean→tainted ×2 | **arch4/phys68、arch5/phys153** | 存储→CPU 边界 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=5536042` | 架构可见错误 |
| SQ | — | — | — | `N/A`（load 路径） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 14 位置 1，PA 从 `0x83111d40` 变成 `0x87111d40`；翻译结果记录 `effective_pa_changed/contained=0`，load 经 LQ（`lq_idx=594678`）发出，错误地址被同址访问两次、两次未命中并由 MSHR 2/0 完成填充与释放，`resp`→`lq_complete`→两个 `taint_reg`（arch4/phys68、arch5/phys153）把污点带入寄存器，最终该 load 本身在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=3442472 eligible=3442472 injected=3`；`numFaultsInjected=3`；注入日志 3 条（fault1 tick 239629862268、fault2 tick 241738137882、fault3 tick 242538826392）。三处一致。代表故障（fault 1）的污染值被 lookup 与 LQ/cache 真实消费，属于 activated。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`87111d40`）。不是 data/permission/control-state 型（`ap`/`valid` 未变）。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：显式 `effective_pa_changed`+`contained=0`，结构放弃撤销；`event_id=4` 的 `lq_read` 立即消费。

### 3.4 检测与掩蔽机制

候选：翻译结果 PA 比对（有，只在 PA 未变时含住）、权限/对齐异常（无）、ECC/parity（`model=none`）、squash/replay（本 fault 3 条、兄弟 fault 99 条，全部晚于本 fault 的错误提交）、commit 前检查（无）。盲点：PA 改变后无第二道检查；squash 只影响更年轻指令。`outcome=NoFault` 不等于无故障。

### 3.5 最终 SDC 风险判断

有真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：双寄存器污染（arch4/arch5）到提交之间，污染值被后续指令观测；`consumer_summary` 2562 条记录、`logical_total=3721021`、`by_outcome=sd_observed`（§5）。无应用 oracle 行，**最终数据正确性不可判**；不能仅凭 errant_commit 宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 掩码：seed1=`0x4000`（bit14）、seed2=`0x1`（bit0）、seed3=`0x4000`（bit14）；seed1 与 seed3 掩码相同但注入 tick/VA 不同。
- PA：seed1 `81d75b48→85d75b48`；seed2 `8313bd08→8313ad08`；seed3 `83111d40→87111d40`。
- 终局：三者都是 L5 `errant_commit`（87/20/45）；seed2/seed3 的 errant 是最初 load 本身，seed1 的 errant 是更年轻指令。
- 运行结局：三者都是 Crash，Oops 地址/码不同。
- 多注入：seed1 1 个、seed2 2 个、seed3 3 个；本 seed 的 fault 2/3 都被 squash 收口（见 §5），只有 fault 1 逃逸。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 22 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239629862268 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | 83111 | 87111 | 83111 | 87111 | 0x4000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit14 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 239629862268 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | 83111 | 87111 | 83111 | 87111 | — | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40 | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 239629862268 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | 83111 | 87111 | 83111 | 87111 | — | 83111d40 | 87111d40 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 239629862268 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | — | — | 83111d40 | 87111d40 | — | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40 | vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 239629862268 | 0 | `lq_read` | L3 | LQ | 1 | seq_primary | 5536042 | 5536042 | 7fe7c61d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | load，`lq_idx=594678` | 读取队列条目 | 错误进入 LQ |
| 6 | 5 | 4 | 239629862268 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 读取 | 首次访问 | 错误被消费 |
| 7 | 6 | 5 | 239629862268 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 8 | 7 | 6 | 239629862268 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 9 | 8 | 7 | 239629862601 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | 7fe7c61d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同址再次访问 | 第二次访问 | 再次消费 |
| 10 | 9 | 8 | 239629862601 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 11 | 10 | 9 | 239629862601 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 12 | 35 | 10 | 239629921542 | 58941 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 2 填充 | 数据就绪 |
| 13 | 36 | 35 | 239629921542 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 | 行可用 |
| 14 | 37 | 36 | 239629921542 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 资源回收 |
| 15 | 38 | 37 | 239629922208 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 再次填充 | `mshr_id=0` 填充 | 原值保留 |
| 16 | 39 | 38 | 239629922208 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 5536042 | 5536042 | — | 87111d40 | 87111d40 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 17 | 40 | 39 | 239629922208 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 5536042 | 5536042 | — | — | 87111d40 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 18 | 41 | 40 | 239629922541 | 333 | `resp` | L3 | L1D→core resp | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回（va 未盖戳） | 污染回到核心 | 污染回到核心 |
| 19 | 42 | 41 | 239629922541 | 0 | `lq_complete` | L3 | LQ | 1 | seq_primary | 0 | 5536042 | 7fe7c61d32 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | load 完成 | 值就绪 | load 完成 |
| 20 | 43 | 42 | 239629922541 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | clean→tainted | 存储→CPU 边界 | 存储→CPU 边界 |
| 21 | 44 | 43 | 239629922541 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | — | 5536042 | 0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | clean→tainted | 第二个寄存器被污染 | 存储→CPU 边界 |
| 22 | 45 | 44 | 239629923207 | 666 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 5536042 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 25388 条事件，分属 3 个 fault；主链 22 条（fault 1），其余为旁支。

1. **fault 1 的兄弟请求与消费者**：`request_fork`（从主链 MSHR 点广播）、4029 条 `cache_access`、4029 条 `cache_return`、159 条 `mshr_alloc`、269 条 `mshr_merge`、158 条 `mshr_fill`、158 条 `cache_fill`、158 条 `mshr_free`、3775 条 `resp`、4559 条 `taint_reg`、1447 条 `lq_complete` 等；`consumer_summary` 2562 条、`logical_total=3721021`、`conservation=ok`。
2. **fault 2**：`event_id=1371`（inj，tick=`241738137882`，VA=`ffffffc00948bf78`，`old=81d4d → new=91d4d`，掩码 `0x10000`），随后 lookup/pfn/translate（`effective_pa_changed/contained=0`）与大量访存。它**没有** `errant_commit`，由 49 条 `squash_masked` 收口（首条 `event_id=1615`，tick=`241738443243`，事件自身 `detection_layer=L4`、`contained=1`、`outcome=masked`、`reason=squash_replay`、`dyn_inst_seq=12113895`）。checker 记其终局为 `detected_contained`、`provable_to=L5`：这里的 L5 来自 checker 的 D1 规则（带 detection_layer+outcome+corr 的显式检测事件被提升为 L5 锚点），而**事件自身声明的层是 L4**。本文按事件声明称其为 L4 squash 收口，**绝不把它写成 L5 终局**。
3. **fault 3**：`event_id=14621`（inj，tick=`242538826392`，VA=`ffffffc00948bac0`，`old=81d4d → new=81d6d`，掩码 `0x20`），同样由 50 条 `squash_masked` 收口（首条 `event_id=14678`，tick=`242538887332`，L4、`masked`、`squash_replay`、`dyn_inst_seq=14834736`）。同为 `detected_contained`，同样不是 L5 终局。

这三条流不构成同一祖先：fault 1 的 L5 见证（event 45）与 fault 2/3 的 squash 收口各自独立。旁支不改变 fault 1 的逃逸结论；它们说明同一 run 中还有两个注入被 squash 拦住。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（代表故障真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=45，tick=239629923207，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效（`numFaultsInjected=3` 与 injected=3 一致） |
| conservation | `ok`（2562 条 summary；`logical_total=3721021`） |
| count_contradiction | 否（attempted=3442472>0；injected=3=stats=3） |
| campaign/checker agreement | **部分不一致**：`cell_results` 记 `activated=3`、`classes.Crash=3`；checker 只有 fault 1 是 full，fault 2/3 是 `detected_contained`（L4 squash 收口）。样本级 outcome=Crash 一致，fault 级计数口径不一致 |
| CHAIN_DEMONSTRATED | 是（fault 1 的 `inj`→L5 单祖先连续） |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**两轴状态（不是单一 REVIEW）**：

1. `experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH`：矩阵标 MiBench-TC23，run.out/terminal 证明实际是 `tlb_probe.rcS`；矩阵记录状态仍为 `blocked(fs-infra: SE has no MiBench FS pipeline)`。
2. **计数口径（两套并列）**：campaign `classes.Crash=3` 是 run 级 outcome（本次运行 Crash）乘以 activated 数；checker 是 per-fault 终局（1 full + 2 contained）。两者统计单元不同，样本级一致，不是数据矛盾；详见 `R6-T01-F1-W4-MULTIFAULT-RECHECK.md`。
3. 矩阵字段口径（VPN tag）与证据（PFN）不一致，属矩阵元数据记录，保留。
4. **保留的记录缺口**：`prop_evt` 的 fault 2（event 1348）记录 `detection_layer=L2, contained=1, effective_pa_unchanged`，但 run.out 无对应 `effective_pa_unchanged` 行；本文件以 `prop_evt` 为链证据，同时把该 stdout 缺口列为待复核，不猜测原因。

结论：`chain_evidence_status=PASS`；`overall_experiment_status=NOT_MIBENCH_RESULT`。

一致性自检：22 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调不降；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致（并解释事件 41/42 的未盖戳字段）；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界（没有把 squash 写成 L5）。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3/T01-F1-W1/seed3/prop_evt.txt.gz` | `c88d6b2bd6d52f34311f9e5c0135ae521686e1eadaead497b6b0fa5cc215f3d1` | 963697 | 2026-10-27T16:15:07 |
| chain_report（权威） | `.../seed3/chain_report.json` | `1e7af3ffd779bcd1f9da37092d867fda2845ce9e9a7728935d290cf3747f8ed0` | 2236046 | 2026-10-27T16:15:09 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed3/run.out` | `a5035845b619acbe6673266bf2be32270e0558d88068026f35c4c0fb30f5b130` | 11832 | 2026-10-27T16:15:07 |
| run.err | `.../seed3/run.err` | `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36` | 1873 | 2026-10-27T16:15:07 |
| stats.txt | `.../seed3/stats.txt` | `e47b3b271fdf0b4df379598ae47c973daa5bff3d2c3c30903e77286bc7676f43` | 419893 | 2026-10-27T16:15:07 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3/manifest.json` | `123e99193c06a841d1864a85726531251785fc80c4c118f567ec9937a95414f4` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed3/board.workload.dmesg` | `f62a0e0d4167c2d2f93985d86dacf0a4449e8038da9f6689f6f89aed3f1db3a7` | 13845 | 2026-10-27T16:15:07 |
| 辅助证据（terminal） | `.../seed3/board.terminal` | `f157e6855ecaaaa0774862cdf53ac249669d62fd07eef35de6e2ba5ca947fbce` | 1787 | 2026-10-27T16:15:07 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3/T01-F1-W1/seed3`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；旧二进制副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
