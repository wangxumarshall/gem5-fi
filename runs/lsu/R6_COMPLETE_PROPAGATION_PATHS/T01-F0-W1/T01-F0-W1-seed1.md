# T01-F0-W1 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F0-W1` |
| seed | `1` |
| sample_run_id | `s1` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；传播状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F0` |
| requested tier | `F0` |
| effective tier | `F0` |
| tier enabled | `关闭(0)`（run.out `CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`） |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`——**与矩阵标签不一致**：实际跑的是 TLB page-walk 探针，不是 MiBench。详见 §6 的不一致记录。 |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 1 --chaos_propagation --prop_run_id T01-F0-W1 --prop_sample_run_id s1` |
| source head | `N/A`（manifest 无 `source_head` 字段；不得用二进制源 head 冒充运行时源） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest.binary_source_head） |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（与 manifest `binary_sha_expected` 一致） |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5。manifest 运行期记录为 `d1543872...`） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/manifest.json`（`exit_code` 字段为 `null`；实际退出码见同根 `.exit_code`=`0`） |
| 正常 EOF | **是**（gzip 解压到 EOF 无异常，解压后 165521 字节） |
| exit_code | `0`（`.exit_code` 文件；manifest.exit_code 为 `null`，属记录缺口，不改变退出码事实） |
| truncated | **False** |
| stats 是否有效 | **是**：完整 footer；`simTicks=932371362`、`simInsts=382169`、`finalTick=238882168377` |
| 原始事件数 | `238` |
| fault_id 数量 | `1`（全部事件属 `fault_id=1`） |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`。manifest 的 `run_mode = standalone-single-seed (no cumulative re-run)`、`status=FINISHED`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 的终局是真实 L5：`errant_commit`（`event_id=118`，tick=`237951302175`）。按 `parent_event_id` 回溯得到唯一祖先链 22 条：

`0 → 1 → 2 → 3 → 4(sq_execute) → 5(sq_writeback) → 6 → 7 → 8 → 15 → 16 → 17 → 30 → 31 → 32 → 33 → 34 → 35 → 39(resp) → 40(taint_reg) → 41(sq_complete) → 118(errant_commit)`

祖先内 tick 单调不降；同 tick 段依次为 237950940537、237950941869、237950942202、237951015129、237951015795、237951016128，最后跨到 237951302175。链里出现了一次"跨 tick 的父边跳跃"（8→15、17→30），这是同一请求在 cache/MSHR 内的等待与填充，不是乱序：parent 指针本身保证先后，tick 只用于校核。

### 2.1 故障注入前的正常状态

在飞访问身份：`dyn_inst_seq=301`、`request_id=301`，VA=`0xffffffc009483fa8`（页内偏移 `0xfa8`），`corr=origin` 由注入事件携带。目标表项 `entry_index=0`、`way=-1`、`walk_id=0`；注入前状态 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75fa8`。本链在 L1 之后的第一个访问侧事件是 `sq_execute`（存储队列执行），因此这次访问是 **store** 路径；但链中没有 `lsq_push` 记录，进入 LSQ 的插入时刻属于结构性缺席（见 §2.4）。

### 2.2 故障具体如何注入

`event_id=0`，tick=`237950940537`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=301`，`corr=origin`，`field=bit_flip`。注入日志：`Mask: 0x20000`，即 PFN 第 17 位。原 PFN `0x81d75` 异或后得 `0xa1d75`：用完整中文句子说明——第 17 位由 0 变 1，表项中保存的 PFN 从 `0x81d75` 变成 `0xa1d75`，其余位不变。第 17 位在物理地址中对应第 29 位（PFN 左移 12），落在有效 PA 宽度之内，因此有效物理地址随之从 `0x81d75fa8` 变成 `0xa1d75fa8`，`effective_pa_changed` 为真。与 T01-F0-W4 的两个含住 seed 不同，这里的翻转位没有被截断抵消。

注入符合"单次 XOR、选有效表项、被下游读取才计激活"的模型，但字段是 PFN 而非矩阵所写的 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`237950940537`）记录 `entry_index=0`、`walk_id=0`、`corr=seq_primary`、`field=post_lookup`，`before=81d75`、`after=a1d75`。state 对照：`pfn=81d75→a1d75`，`pa=81d75fa8→a1d75fa8`；`vpn/asid/valid/global/ap/mtype/page_size` 不变。查找读到了污染 PFN，并且 PA 已改变。

`event_id=2`（`tlb_pfn`，parent=1）独立记录物化结果：`pa=a1d75fa8`、`state_before=81d75fa8`、`state_after=a1d75fa8`。

`event_id=3`（`tlb_translate_result`，parent=2，`corr=seq_primary`）是本 seed 的翻译结果裁决：`field=effective_pa_changed`、`before=81d75fa8`、`after=a1d75fa8`、`contained=0`、`outcome=NoFault`。这里必须说清楚：`outcome=NoFault` 指的是"翻译本身没有触发 fault（权限/对齐等）"，而 `contained=0` 明确表示**没有含住**；requested 与 effective 不同，因此错误 PA 被交给下游。TLB 交给 LSU 的是 `0xa1d75fa8`。

### 2.4 错误如何进入 LQ/SQ/LSQ

本链没有 `lsq_push`/`lq_read`，但有 `sq_execute`（`event_id=4`，parent=3，tick=`237950940537`，`sq_idx=32`，`state_before=issued`）与 `sq_writeback`（`event_id=5`，parent=4，tick=`237950941869`，`sq_idx=32`，`pa=a1d75fa8`，`state_after=packet_built`）。也就是说：错误 PA 进入的是 **store queue** 的一个条目（`sq_idx=32`），在 execute 阶段被发往访存，在 writeback 阶段形成内存包。输入→内部变化→输出的顺序是：翻译结果给出错误 PA（输入）→ SQ 条目以该 PA 执行并构建 packet（内部变化）→ `cache_access` 携带 `pa=a1d75fa8` 发出（输出）。下一级 cache 之所以消费它，是因为 packet 已构建完成且地址直接取自被污染的翻译。`lsq_push` 的缺席意味着"进入 LSQ 的插入时刻"未被记录；本文件不虚构该时刻，只用 `sq_execute` 证明它已在 SQ 内。

### 2.5 错误如何经过 cache 和 MSHR

共有两次 cache 访问与两组 MSHR 生命周期：

- 第一次：`event_id=6`（`cache_access`，parent=5，tick=`237950941869`，`request_id=301`）访问 `pa=a1d75fa8`；`event_id=7`（`cache_return`，parent=6）记录 `field=miss`；`event_id=8`（`mshr_alloc`，parent=7）记录 `cache_line=a1d75fa8`、`mshr_id=1`、`state_after=mshr_allocated`。这次分配之后，主链并没有它的 fill/free（在旁支里）。
- 第二次：`event_id=15`（`cache_access`，parent=8，tick=`237950942202`）访问同一行的行基址 `pa=a1d75f80`；`event_id=16` 记录 `miss`；`event_id=17`（`mshr_alloc`）记录 `cache_line=a1d75f80`、`mshr_id=3`、`state_after=mshr_allocated`。
- 填充与释放：`event_id=30`（`mshr_fill`，parent=17，tick=`237951015129`）`mshr_id=3`、`state_after=filled`；`event_id=31`（`cache_fill`）把 `cache_line=a1d75f80` 填入；`event_id=32`（`mshr_free`）`mshr_id=3`、`state_after=mshr_freed`。随后 `event_id=33`（`mshr_fill`）以 `mshr_id=0`、`state_after=filled` 再来一次填充，`event_id=34`（`cache_fill`）再次填同一行，`event_id=35`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

这里必须如实指出两个不寻常但确实存在的记录：其一，第二次 MSHR 编号是 3（不是 2），说明本链只截取了该请求生命周期中的部分 MSHR 事件；其二，`mshr_id=0` 的 fill/free 在事件流中真实存在，本文件按原值记录，不把它改写成其它编号。为什么仍是同一个 fault？因为所有这些事件的 `fault_id=1`、`parent_event_path` 连续，且 cache_access 的 PA 都是同一个被污染 PA 派生出的地址。

### 2.6 污染如何返回处理器状态

`event_id=39`（`resp`，parent=35，tick=`237951016128`，`request_id=301`，`corr=seq_primary`，`va=a1d75fa8`）把响应送回核心侧；`event_id=40`（`taint_reg`，parent=39，同 tick）记录 `before=clean`、`after=tainted`、`va=a1d75fa8`、`dyn_inst_seq=301`。这是存储→CPU 的边界：从此刻起被污染状态进入寄存器域。证据限制：该 `taint_reg` 没有记录 `arch_reg`/`phys_reg`，因此无法给出具体寄存器号。`event_id=41`（`sq_complete`，parent=40）随后把 `sq_idx=32` 置为 `completed`，说明 store 生命周期完成，而污染状态已经随响应进入处理器。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=118`，parent=41，tick=`237951302175`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，并记录 `dyn_inst_seq=391`、`pc=ffffffc0087b1000`、`commit_seq=161`。它与上游的关系：被污染状态（event 40）在提交端由一条更年轻的指令（`391`）兑现为架构可见差异，`corr=taint_prop` 表明这是污点传播路径而非新的注入。为什么没有在提交前被消除？因为本链的 L2 翻译结果明确 `contained=0`，而且 L4 的 squash 事件（event 144，见 §5）发生在错误提交之后、且不属于本终局祖先；提交端之前没有任何拦截点。

`chain_end`（`event_id=215`，tick=`238882168377`，`detection_layer=L5`，`outcome=errant_commit_seen`，`containment_reason=squash_replay`）只是流关闭记录，**不是 L5 见证**；L5 的唯一见证是 event 118。

### 2.8 从传播终局到系统表现

传播终局 L5 `errant_commit`；`provable_to=L5`；运行结局 `Crash`。run.out 的两行证据：

- `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951547263 ptag=1 reason=squash_replay`（错误提交之后的一次 squash 收口，不能反过来抵消 event 118）

以及 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`。run.err：`Kernel oops in guest` + `Dumping kernel dmesg buffer`；guest dmesg：

- `[2.160000] Unable to handle kernel paging request at virtual address 0b8542c0087b0c40`
- `[2.160000] Internal error: Oops: 86000004 [#1] PREEMPT SMP`
- `[2.160000] Call trace:`

注入 tick=`237950940537`，错误提交 tick=`237951302175`，传播延迟 **361,638 ticks**。L5→Crash 因果成立：先有错误提交，再有 guest 内核 Oops。链终止 tick=`238882168377`，即运行结束时刻。负载没有跑到应用 oracle 行（terminal 中只有 Oops，无 `rounds ok=`），故最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit17 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req=301） | 读到 `pfn=a1d75` | 污染表项，PA=`a1d75fa8` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化错误 PA | `pa=a1d75fa8` | 错误地址成形 |
| L2 MMU translate result | requested/effective | 判定 `effective_pa_changed` | `contained=0` | 明确不含住，放行 |
| L3 SQ | 错误 PA | execute→writeback，构建 packet | 访存请求 | 错误进入存储队列 |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误地址被消费 |
| L3 MSHR | 两次 miss | 分配 MSHR 1 / 3 | `mshr_alloc` | 挂起等待 |
| L3 MSHR/L1D fill | 下层返回 | fill/free（mshr 3 与 0） | 行填充 | 数据就绪 |
| L3 L1D→core resp | 填充完成 | 返回响应 | `resp`（req=301） | 污染回到核心 |
| L4 taint/regfile | response | clean→tainted | 污染状态 | 存储→CPU 边界 |
| L3 SQ complete | store 生命周期 | completed | 队列条目收口 | store 完成 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=391` | 架构可见错误 |
| LQ | — | — | — | 本链无 LQ 事件（`N/A`） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 17 位置 1，有效 PA 由 `0x81d75fa8` 变为 `0xa1d75fa8`；翻译结果显式记录 `effective_pa_changed` 且 `contained=0`，错误地址进入 SQ（`sq_idx=32`）、在 L1D 两次未命中并分配 MSHR 1/3、经 fill/free 与 `resp` 返回，`taint_reg` 把污点带入寄存器域，最终由更年轻的指令（`dyn_inst_seq=391`, `pc=ffffffc0087b1000`）在 L5 完成真实错误提交，运行随后以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

run.out `CHAOS_LSU_TRIGGER: attempted=150162 eligible=56 injected=1`；`stats.txt numFaultsInjected=1`；注入日志 1 条。三处一致（injected=1=stats=1=日志 1 条；attempted>0）。污染值被下游真实读取（lookup）、物化（tlb_pfn）、并进入 SQ/cache，属于 activated。

### 3.2 故障传播类型

**address 型**，并导致 **wrong cache line / wrong request routing 的下游表现**：L1D 访问的 `a1d75fa8` 与 `a1d75f80` 都不是正常页的地址。不是 data 型（注入器未直接改数据字节）、不是 permission（`ap`/`valid` 未变）、不是 control-state（控制位未改）。timing 上有副作用（未命中导致延迟），但这不是注入器改变的字段。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`）：该事件显式记录 `effective_pa_changed` 且 `contained=0`，这是结构上"决定不撤销"的位置。此后 `event_id=4` 的 SQ execute 立刻把错误地址用于访存，任何下游都无法恢复。比较：在 event 2 时错误 PA 已物化，但理论上仍可由翻译结果比对撤销；event 3 明确放弃了这一撤销。

### 3.4 检测与掩蔽机制

候选机制：翻译结果 PA 比对（本 seed 有该事件，但因 PA 改变而**不**含住）、权限/对齐异常（未触发）、ECC/parity（`protection: model=none bits=1 -> Raw`，无保护）、squash/replay（event 144 在错误提交之后发生，无法回溯取消 event 118）。观察到的检测盲点：翻译比对只能在"PA 未变"时提供含住；一旦 PA 改变，它记录 `effective_pa_changed/contained=0` 后放行，下游没有第二道检测。错误提交后才出现的 squash 只影响更年轻的指令，不改变已提交的错误。

### 3.5 最终 SDC 风险判断

存在真实 errant commit（event 118）与架构可见错误，运行以 Crash 结束，因此不判 SDC：错误最终以内核 Oops 外部可见。静默期确实存在：从 event 40（taint_reg）到 event 118，污染值进入寄存器并被后续指令观测（61 条 consumer 事件、10 条 summary、`logical_total=56`、`conservation=ok`）。是否存在应用级静默错误？本 seed 没有应用 oracle 行（负载在崩溃前未完成），**最终数据正确性不可判**；不能仅凭 errant_commit 就宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 注入位点相同：`arm_tlb_lookup_hit`；三者都是 store 路径（链中均有 `sq_execute`/`sq_writeback`/`sq_complete`）。
- 掩码：seed1=`0x20000`（PFN bit17）、seed2=`0x400`（bit10）、seed3=`0x10000`（bit16）——都落在 PA 宽度内。
- PA 变化：seed1 `81d75fa8→a1d75fa8`；seed2 `81d75eb8→81975eb8`；seed3 `81d75eb0→91d75eb0`。
- 终局：三者都是 L5 `errant_commit`（seed1 event 118、seed2 event 283、seed3 event 293），且错误提交的 `dyn_inst_seq` 都是 391、`pc` 都是 `ffffffc0087b1000`。
- 运行结局：三者都是 `Crash`；三者的 `board.workload.dmesg` 与 `board.terminal` 哈希完全相同（同一 Oops 签名）。
- 共同点说明：同一注入点、不同 bit 位置在 PA 宽度内，都会造成同一消费路径崩溃。

## 4. 完整主链事件表

`mask` 取自 `armtlb_injections.log`；`layer` 用 TLB family 层映射；`old_pfn/new_pfn` 只对 PFN 事件填写。本链 22 条，逐条列出，不折叠。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | a1d75 | 81d75 | a1d75 | 0x20000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit17 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 237950940537 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | a1d75 | 81d75 | a1d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 237950940537 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | a1d75fa8 | — | — | 81d75 | a1d75 | 81d75 | a1d75 | — | 81d75fa8 | a1d75fa8 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 地址改变 |
| 4 | 3 | 2 | 237950940537 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | a1d75fa8 | — | — | — | — | 81d75fa8 | a1d75fa8 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8 | 0 | — | NoFault | field=effective_pa_changed | requested/effective PA | `effective_pa_changed`，不放行即含住 | 不可逆点：明确不含住 |
| 5 | 4 | 3 | 237950940537 | 0 | `sq_execute` | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | 错误 PA + store 条目 | 以错误 PA 执行 | 错误进入 SQ |
| 6 | 5 | 4 | 237950941869 | 1332 | `sq_writeback` | L3 | SQ | 1 | seq_primary | — | 301 | — | a1d75fa8 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | execute 完成 | 构建访存 packet | 错误地址随包发出 |
| 7 | 6 | 5 | 237950941869 | 0 | `cache_access` | L3 | L1D | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | a1d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | packet | 第一次访问错误 PA | 错误被消费 |
| 8 | 7 | 6 | 237950941869 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | a1d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 9 | 8 | 7 | 237950941869 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75fa8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss | 分配 MSHR 1 | 请求挂起 |
| 10 | 15 | 8 | 237950942202 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费错误行 |
| 11 | 16 | 15 | 237950942202 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 301 | 301 | — | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 12 | 17 | 16 | 237950942202 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 3 | 请求挂起 |
| 13 | 30 | 17 | 237951015129 | 72927 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 3 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 3 填充 | 数据就绪 |
| 14 | 31 | 30 | 237951015129 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 301 | 301 | — | a1d75f80 | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 L1D | 行可用 |
| 15 | 32 | 31 | 237951015129 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 3 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 3 | 资源回收 |
| 16 | 33 | 32 | 237951015795 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 同一行再次填充 | `mshr_id=0` 填充 | 记录原值保留 |
| 17 | 34 | 33 | 237951015795 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 301 | 301 | — | a1d75f80 | a1d75f80 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 18 | 35 | 34 | 237951015795 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | a1d75f80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 19 | 39 | 35 | 237951016128 | 333 | `resp` | L3 | L1D→core resp | 1 | seq_primary | 301 | 301 | a1d75fa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 20 | 40 | 39 | 237951016128 | 0 | `taint_reg` | L4 | taint/regfile | 1 | seq_primary | 301 | 301 | a1d75fa8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应 | clean→tainted | 存储→CPU 边界 |
| 21 | 41 | 40 | 237951016128 | 0 | `sq_complete` | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | store 已完成 | `sq_idx=32` 收口 | store 生命周期结束 |
| 22 | 118 | 41 | 237951302175 | 286047 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 238 条事件，全部 `fault_id=1`；主链 22 条，其余 215 条（含 `chain_end`）为旁支。

- **`request_fork` 22 条**：全部从 `source_event_id=8` 与 `source_event_id=17`、`40` 出发的 `addr_fallback_broadcast`，`old_request_id=301`，`new_request_id` 为 303/304/307/308/310/357/358/369/370/380/381/385/…。它们把同一错误地址广播给兄弟请求，分叉后未回流到终局祖先（终局仍走 8→15…）。
- **兄弟请求的访存/污染事件**：25 条 `cache_access`、25 条 `cache_return`、6 条 `mshr_alloc`、10 条 `mshr_merge`、6 条 `mshr_fill`、6 条 `cache_fill`、6 条 `mshr_free`、21 条 `resp`、22 条 `taint_reg`、4 条 `lq_complete`，覆盖 24 个 request_id。
- **`consumer` 61 条**：`consumer_summary` 10 条记录、`emitted=10`、`suppressed=46`、`logical_total=56`、`distinct_dyn_seq=53`、`conservation=ok`、`by_outcome=sd_observed`。
- **`squash_masked` 1 条**：`event_id=144`，tick=`237951547263`，`detection_layer=L4`（事件自身声明），`contained=1`，`outcome=masked`，`containment_reason=squash_replay`，`dyn_inst_seq=520`。它发生在错误提交（237951302175）**之后**，属于更年轻指令的 squash 收口；不能把 L5 改写成含住，也不能用它抹掉 event 118。切勿把它写成 L5 终局。
- `chain_end`（event 215）是生命周期收口。

这些旁支不构成另一条终局祖先；它们扩大污染消费面（56 个逻辑消费者），但不改变本 seed 的 L5 结论。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=118，tick=237951302175，L5 |
| run outcome | `Crash`（oracle_outcome=Crash；`.exit_code`=0；guest Oops） |
| admitted | `True`（path=`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效（完整 footer、非零 simTicks/simInsts） |
| conservation | `ok`（10 emitted + 46 suppressed = 56 logical；issues=[]） |
| count_contradiction | 否（attempted=150162 > 0；injected=1=stats=1） |
| campaign/checker agreement | 一致（cell_results seed1 outcome=Crash；chain terminal=full） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续，且 L5 是真实 `errant_commit`） |
| COMPLETE_3_OF_3 status | 三个 seed 证据齐全且 certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。

一致性自检：22 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry 顺序；tick 单调不降；未混入其它 seed 的身份；VA/PFN/PA/before/after/mask 来自本 seed 与注入日志；request_id/corr/fault_id 一致；终局与权威报告一致；L5 见证是真实 `errant_commit` 而非 `chain_end`；每个单元均给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。

**其它不一致/缺口**：

1. 矩阵把被注入字段写作"VPN tag"，证据显示为 PFN 翻转。
2. manifest 的 `exit_code`/`done_flag` 为 `null`（真实退出码在 `.exit_code`=0）；这是记录缺口。
3. `taint_reg`（event 40）未记录 `arch_reg`/`phys_reg`，无法给出被污染寄存器号。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1/prop_evt.txt.gz` | `719627235933cd49b0ff99c0c5391dba2b98de6ef6d4d8d9709c2355001b57d5` | 9891 | 2026-10-27T13:11:46 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1/chain_report.json` | `e8aae326190b1f8bb56c2138bcdf4722f5cc7551288d19f0e6d3a75baf93c6a5` | 10701 | 2026-10-27T13:11:47 |
| authoritative regrade | `N/A`（无 regrade） | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1/run.out` | `b2e1c85d092d26dfcb21d5a03a331a0b4d2d002816a62040f63488f75d993bf1` | 2300 | 2026-10-27T13:11:47 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` | 1726 | 2026-10-27T13:11:47 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1/stats.txt` | `3ab3efcc04c6d8471ab992ded96755ca14ac5e46e3737e733566554db5b8bab5` | 381972 | 2026-10-27T13:11:46 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/manifest.json` | `2acc7a13d593c90a2cb5dcd688698c3e5a01db1678e5e569f260deec485ccabb` | 1438 | 2026-10-27T13:11:48 |
| 启动命令记录 | run.out 的 `command line:` 行（§1） | 同 run.out | — | — |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — | — |
| analysis tool | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed1/board.workload.dmesg` | `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b` | 13938 | 2026-10-27T13:11:46 |
| 辅助证据（terminal） | `.../seed1/board.terminal` | `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db` | 1839 | 2026-10-27T13:11:46 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s1/T01-F0-W1/seed1`。
- 其它副本：`r6_n8_T01-F0-W1_s1.sha8a229009/...` 为 OLD_BINARY_REFERENCE（binary `8a229009...`），不得作为本文件证据；其余分类以 `R6-AUTHORITATIVE-EVIDENCE.md` 为准。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
