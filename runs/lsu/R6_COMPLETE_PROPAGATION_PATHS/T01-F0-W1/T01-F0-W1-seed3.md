# T01-F0-W1 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F0-W1` |
| seed | `3` |
| sample_run_id | `s3` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F0` |
| requested tier | `F0` |
| effective tier | `F0` |
| tier enabled | `关闭(0)`（`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`） |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`——**与矩阵标签不一致**（实际为 TLB page-walk 探针）。详见 §6。 |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3/T01-F0-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 3 --chaos_propagation --prop_run_id T01-F0-W1 --prop_sample_run_id s3` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3/T01-F0-W1/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3/manifest.json`（`exit_code=null`） |
| 正常 EOF | **是**（解压后 305197 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`） |
| truncated | **False** |
| stats 是否有效 | **是**：`simTicks=932242491`、`simInsts=382169`、`finalTick=238882039506` |
| 原始事件数 | `444` |
| fault_id 数量 | `1` |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`。

## 2. 完整故障传播过程：从注入到最终结局

终局为真实 L5：`errant_commit`（`event_id=293`，tick=`237951302175`）。祖先链 23 条：

`0 → 1 → 2 → 3 → 4(lsq_push) → 5(sq_execute) → 6(sq_writeback) → 7 → 8 → 9 → 10 → 11 → 12 → 64 → 65 → 66 → 67 → 68 → 69 → 73(resp) → 74(taint_reg) → 75(sq_complete) → 293(errant_commit)`

tick 段：237950233578、237950233911、237950235243、237950235576、237950294517、237950295183、237950295516、237951302175，单调不降。本 seed 与 seed2 不同：它有 `tlb_translate_result`（event 3，`effective_pa_changed/contained=0`），并且是三个 F0-W1 seed 中唯一留下 `lsq_push`（`field=store`、`sq_idx=1`、`opcode=strxi_uop`）的。

### 2.1 故障注入前的正常状态

在飞访问：`dyn_inst_seq=31`、`request_id=31`，VA=`0xffffffc009483eb0`（页内偏移 `0xeb0`）。表项 `entry_index=0`、`walk_id=0`；注入前 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75eb0`。本链的 `lsq_push.field=store` 与 `opcode=strxi_uop` 明确说明这是一条 **store**（`strxi_uop`），进入 `sq_idx=1`。

### 2.2 故障具体如何注入

`event_id=0`，tick=`237950233578`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=31`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x10000`，即 PFN 第 16 位。原 PFN `0x81d75` 异或后得 `0x91d75`：第 16 位由 0 变 1，表项中的 PFN 从 `0x81d75` 变成 `0x91d75`，其余位不变。该位在物理地址中对应第 28 位，落在有效 PA 宽度内，因此有效物理地址从 `0x81d75eb0` 变成 `0x91d75eb0`，`effective_pa_changed` 为真。

注入符合模型中的单次 XOR/有效表项/下游读取激活；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`237950233578`，`request_id=31`，`corr=seq_primary`）记录 `entry_index=0`、`walk_id=0`、`field=post_lookup`，`before=81d75`、`after=91d75`；state 对照 `pfn=81d75→91d75`、`pa=81d75eb0→91d75eb0`。

`event_id=2`（`tlb_pfn`，parent=1）记录物化：`pa=91d75eb0`、`state_before=81d75eb0`、`state_after=91d75eb0`。

`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）是本 seed 的翻译裁决：`field=effective_pa_changed`、`before=81d75eb0`、`after=91d75eb0`、`contained=0`、`outcome=NoFault`。含义：翻译没有触发权限/对齐 fault（`NoFault`），但 requested 与 effective 不同，故**不**含住；错误 PA `0x91d75eb0` 交给下游。TLB 交给 LSU 的正是这个错误地址。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是三个 F0-W1 seed 中队列证据最完整的一个：`event_id=4`（`lsq_push`，parent=3，tick=`237950233911`）记录 `field=store`、`lq_idx=-1`、`sq_idx=1`、`va=ffffffc009483eb0`、`opcode=strxi_uop`、`pc=ffffffc008011614`。`lq_idx=-1` 说明它不是 load queue 条目；`sq_idx=1` 说明它进入 store queue 的第 1 项。随后 `event_id=5`（`sq_execute`，parent=4）`state_before=issued`、`sq_idx=1`，`event_id=6`（`sq_writeback`，parent=5，tick=`237950235243`）记录 `pa=91d75eb0`、`state_after=packet_built`、`sq_idx=1`。输入→内部变化→输出：翻译给出错误 PA → LSQ 把 store 放入 SQ 并要求执行 → SQ 构建携带错误 PA 的 packet → cache 消费。下一级之所以消费，是因为 packet 的地址直接来自被污染的翻译结果。

### 2.5 错误如何经过 cache 和 MSHR

- 第一次：`event_id=7`（`cache_access`，parent=6，tick=`237950235243`，`request_id=31`）访问 `pa=91d75eb0`；`event_id=8`（`cache_return`）`field=miss`；`event_id=9`（`mshr_alloc`）`cache_line=91d75eb0`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=10`（`cache_access`，parent=9，tick=`237950235576`）访问同一行基址 `pa=91d75e80`；`event_id=11` `miss`；`event_id=12`（`mshr_alloc`）`cache_line=91d75e80`、`mshr_id=2`、`state_after=mshr_allocated`。
- 填充：`event_id=64`（`mshr_fill`，parent=12，tick=`237950294517`）`mshr_id=2`、`state_after=filled`；`event_id=65`（`cache_fill`）填行；`event_id=66`（`mshr_free`）`mshr_id=2`、`state_after=mshr_freed`。
- 再次填充：`event_id=67`（`mshr_fill`，parent=66，tick=`237950295183`）`mshr_id=0`、`state_after=filled`；`event_id=68`（`cache_fill`）；`event_id=69`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

状态迁移与同 RunID 其它 seed 一致：miss→alloc→fill→cache_fill→free。第一次访问的 MSHR 1 在主链上没有 fill/free（旁支有）；`mshr_id=0` 的 fill/free 按原值记录。同一 fault 的依据仍是 `fault_id=1`、parent 连续、地址同源。

### 2.6 污染如何返回处理器状态

`event_id=73`（`resp`，parent=69，tick=`237950295516`，`request_id=31`，`corr=seq_primary`，`va=91d75eb0`）返回响应；`event_id=74`（`taint_reg`，parent=73）`before=clean`、`after=tainted`、`va=91d75eb0`、`dyn_inst_seq=31`。这是存储→CPU 边界。`event_id=75`（`sq_complete`，parent=74）把 `sq_idx=1` 置 `completed`。证据限制：`taint_reg` 无 `arch_reg`/`phys_reg`。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=293`，parent=75，tick=`237951302175`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，`dyn_inst_seq=391`、`pc=ffffffc0087b1000`、`commit_seq=161`。为什么没有被提前消除：L2 明确 `contained=0`，L4 的 squash（event 319）发生在错误提交之后、不属于本终局祖先；提交前无拦截。`chain_end`（`event_id=390`，tick=`238882039506`，`outcome=errant_commit_seen`，`reason=squash_replay`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5；`provable_to=L5`；运行结局 `Crash`。run.out：

- `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951547263 ptag=1 reason=squash_replay`（事后）
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err/dmesg 与同 RunID 其它 seed 相同：`Unable to handle kernel paging request at virtual address 0b8542c0087b0c40`、`Internal error: Oops: 86000004 [#1] PREEMPT SMP`。注入 tick=`237950233578`，错误提交 tick=`237951302175`，传播延迟 **1,068,597 ticks**。L5→Crash 因果成立。链终止 tick=`238882039506`。无应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit16 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=31） | 读到 `pfn=91d75` | PA=`91d75eb0` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=91d75eb0` | 错误地址成形 |
| L2 MMU translate result | requested/effective | `effective_pa_changed` | `contained=0` | 明确放行 |
| L1/L3 LSQ | store（`strxi_uop`） | push 到 `sq_idx=1` | 队列条目 | 错误进入 SQ |
| L3 SQ | issued | execute→writeback | packet | 错误地址随包发出 |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误被消费 |
| L3 MSHR | 两次 miss | MSHR 1/2，fill/free（2、0） | 填充完成 | 请求挂起与回收 |
| L3 L1D→core resp | 填充完成 | 返回 | `resp`（req=31） | 污染回到核心 |
| L4 taint/regfile | response | clean→tainted | 污染状态 | 存储→CPU 边界 |
| L3 SQ complete | store 完成 | completed | 条目收口 | store 结束 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=391` | 架构可见错误 |
| LQ | — | — | — | `N/A`（`lq_idx=-1`，非 load） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 16 位置 1，PA 由 `0x81d75eb0` 变为 `0x91d75eb0`；翻译结果记录 `effective_pa_changed/contained=0`；store（`strxi_uop`）经 LSQ 进入 `sq_idx=1`、执行并构建 packet，错误地址在 L1D 两次未命中、MSHR 1/2 挂起并填充，`resp` 与 `taint_reg` 把污点带入寄存器，最终由更年轻指令（`dyn_inst_seq=391`）在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=150170 eligible=1 injected=1`；`numFaultsInjected=1`；注入日志 1 条；三处一致。污染值被 lookup 读取并进入 SQ/cache，属于 activated。

### 3.2 故障传播类型

**address 型**（PFN→PA），下游表现为 **wrong cache line**（`91d75eb0`/`91d75e80`）。由于被污染的是 store 的地址，类型上还带有"错误寻址的写"这一方向性，但注入器本身没有改写数据字节，故不归为 data 型。permission/control-state 字段未变。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）显式记录 `effective_pa_changed` 且 `contained=0`，是结构上放弃撤销的位置；紧随其后的 `lsq_push`（event 4）把错误地址写入 SQ，使其成为在飞请求。之后的 execute/writeback 只会延续，不会撤销。

### 3.4 检测与掩蔽机制

候选机制：翻译结果 PA 比对（存在，但只在 PA 未变时含住）、权限/对齐异常（未触发）、ECC/parity（`model=none`，Raw）、squash/replay（event 319 在错误提交之后）。盲点：PA 改变后没有第二道检查；squash 只能清理更年轻的指令，无法撤销 event 293。这也是三个 seed 中唯一记录了 `lsq_push` 的，说明该层的记录能力在，但没有检测能力。

### 3.5 最终 SDC 风险判断

有真实 errant commit 与架构可见错误，运行 Crash，不判 SDC。静默期存在（taint_reg→errant_commit 之间被 consumer 观测）。无应用 oracle 行，**最终数据正确性不可判**。不能仅凭 errant_commit 宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 掩码：seed1=`0x20000`（bit17）、seed2=`0x400`（bit10）、seed3=`0x10000`（bit16）。
- PA：`a1d75fa8` / `81975eb8` / `91d75eb0`（均由各自正常 PA 改变而来）。
- 终局：三者都是 L5 `errant_commit`（118/283/293），`dyn_inst_seq=391`、`pc=ffffffc0087b1000`。
- 运行结局：三者为 Crash，terminal/dmesg 哈希完全相同。
- 结构差异：只有 seed3 记录 `lsq_push`（`field=store`, `opcode=strxi_uop`）；seed1 有 `sq_execute` 但无 `lsq_push`；seed2 无任何 LQ/SQ 事件，也无 `tlb_translate_result`。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 23 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 91d75 | 81d75 | 91d75 | 0x10000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit16 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 237950233578 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 91d75 | 81d75 | 91d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 237950233578 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | 91d75eb0 | — | — | 81d75 | 91d75 | 81d75 | 91d75 | — | 81d75eb0 | 91d75eb0 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 237950233578 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | 91d75eb0 | — | — | — | — | 81d75eb0 | 91d75eb0 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=91d75;ap=0;mtype=2;page_size=1000;pa=91d75eb0 | 0 | — | NoFault | field=effective_pa_changed | requested/effective | `effective_pa_changed` | 不可逆点：放行 |
| 5 | 4 | 3 | 237950233911 | 333 | `lsq_push` | L1 | LSQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | field=store | `field=store`, opcode=strxi_uop, sq_idx=1 | store 入 SQ | 错误进入队列 |
| 6 | 5 | 4 | 237950233911 | 0 | `sq_execute` | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | SQ 条目 | 以错误 PA 执行 | 访存开始 |
| 7 | 6 | 5 | 237950235243 | 1332 | `sq_writeback` | L3 | SQ | 1 | seq_primary | — | 31 | — | 91d75eb0 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | execute 完成 | 构建 packet | 错误地址随包 |
| 8 | 7 | 6 | 237950235243 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | 91d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | packet | 首次访问错误 PA | 错误被消费 |
| 9 | 8 | 7 | 237950235243 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | 91d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 10 | 9 | 8 | 237950235243 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75eb0 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 11 | 10 | 9 | 237950235576 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费 |
| 12 | 11 | 10 | 237950235576 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 13 | 12 | 11 | 237950235576 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 14 | 64 | 12 | 237950294517 | 58941 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 2 填充 | 数据就绪 |
| 15 | 65 | 64 | 237950294517 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 31 | 31 | — | 91d75e80 | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 | 行可用 |
| 16 | 66 | 65 | 237950294517 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 资源回收 |
| 17 | 67 | 66 | 237950295183 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 再次填充 | `mshr_id=0` 填充 | 原值保留 |
| 18 | 68 | 67 | 237950295183 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 31 | 31 | — | 91d75e80 | 91d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 19 | 69 | 68 | 237950295183 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 91d75e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 20 | 73 | 69 | 237950295516 | 333 | `resp` | L3 | L1D→core resp | 1 | seq_primary | 31 | 31 | 91d75eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 21 | 74 | 73 | 237950295516 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | 31 | 31 | 91d75eb0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应 | clean→tainted | 存储→CPU 边界 |
| 22 | 75 | 74 | 237950295516 | 0 | `sq_complete` | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | store 完成 | `sq_idx=1` 收口 | store 结束 |
| 23 | 293 | 75 | 237951302175 | 1006659 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 444 条事件，全部 `fault_id=1`；主链 23 条，其余 420 条（含 `chain_end`）为旁支。

- `request_fork` 53 条：`addr_fallback_broadcast`，主要从 `source_event_id=12`（以及后续 40 等）出发，`old_request_id=31`，`new_request_id=32/34/35/37/38/40/…`；未回流终局祖先。
- 兄弟请求：59 条 `cache_access`、59 条 `cache_return`、12 条 `mshr_alloc`、30 条 `mshr_merge`、12 条 `mshr_fill`、12 条 `cache_fill`、12 条 `mshr_free`、52 条 `resp`、53 条 `taint_reg`、4 条 `lq_complete`。
- `consumer` 61 条：10 条 summary、`emitted=10`、`suppressed=46`、`logical_total=56`、`conservation=ok`。
- `squash_masked` 1 条：`event_id=319`，tick=`237951547263`，事件自身 `detection_layer=L4`、`contained=1`、`outcome=masked`、`reason=squash_replay`、`dyn_inst_seq=520`；发生在错误提交之后，不能写成 L5，也不能抵消 event 293。
- `chain_end`（event 390）为生命周期收口。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=293，tick=237951302175，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效 |
| conservation | `ok`（10+46=56） |
| count_contradiction | 否（attempted=150170>0；injected=1=stats=1） |
| campaign/checker agreement | 一致（seed3 outcome=Crash；terminal=full） |
| CHAIN_DEMONSTRATED | 是 |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**REVIEW_REQUIRED 理由**：链、认证、L5 见证全部通过；但矩阵把该 cell 标为 MiBench-TC23，run.out/terminal 证明实际是 `tlb_probe.rcS`，且矩阵"记录状态"仍是 `blocked(fs-infra: SE has no MiBench FS pipeline)`。工作负载身份矛盾必须人工复核。

一致性自检：23 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致；终局与报告一致；L5 是真实 `errant_commit`；每个单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。

**其它缺口**：字段口径（VPN tag vs PFN）；manifest `exit_code=null`；`taint_reg` 无寄存器号。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3/T01-F0-W1/seed3/prop_evt.txt.gz` | `7ab6e9550997eef1fb1bd52e91cd49c73d1f2bb64a4d3b53ef27643e5bbe9a59` | 16765 | 2026-10-27T16:16:47 |
| chain_report（权威） | `.../seed3/chain_report.json` | `a0e96a0be89b31ef27edc0e8ec263eb470d25277a96669c49c32cd6e72b8cd83` | 10701 | 2026-10-27T16:16:47 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed3/run.out` | `b8a3017852aaa110fd47929c7de107d972b582a92b5f6955c50792fa80406d0e` | 2299 | 2026-10-27T16:16:47 |
| run.err | `.../seed3/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` | 1726 | 2026-10-27T16:16:47 |
| stats.txt | `.../seed3/stats.txt` | `5f6e8272ca7bb20b6d8d0b923e7e5da41c2ccfca2c80d723b23a5db2322c8a06` | 381642 | 2026-10-27T16:16:47 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3/manifest.json` | `79bda76f6c8fb1a7e6d337bc843c1a998717a386d2fae0ae6e22f5c1c0fdca8d` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed3/board.workload.dmesg` | `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b` | 13938 | 2026-10-27T16:16:47 |
| 辅助证据（terminal） | `.../seed3/board.terminal` | `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db` | 1839 | 2026-10-27T16:16:47 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3/T01-F0-W1/seed3`。
- 其它副本：见 `R6-AUTHORITATIVE-EVIDENCE.md`；`OLD_BINARY_REFERENCE` 副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
