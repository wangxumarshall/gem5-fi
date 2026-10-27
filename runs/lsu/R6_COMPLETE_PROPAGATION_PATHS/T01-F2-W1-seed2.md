# T01-F2-W1 seed2 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `c83d89fd…eaf7`）重建；其余文件只读引用。**本 seed 是含住样本**：权威传播终局是 L4 `squash_masked`（event 68），L5=N/A；本 seed 有 4 个 fault_id，代表故障为 fault 1。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T01-F2-W1`（模型 ID `T01`，单元 `L1d-TLB`） |
| seed / sample_run_id | `2` / `s2` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**单比特** `bit_flip`（`--tlb_fault_type bit_flip`，1 bit） |
| 故障类型 | 单比特翻转 |
| 频率 tier | 请求 `F2` / 生效 `F2` / `lookup_tier_enabled=1` |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）`（矩阵 Excel 行 45） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`（实际为 TLB-AliasPerm 探针，与矩阵标签不一致；见第 6 节） |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T01-F2-W1 --prop_sample_run_id s2` |
| source head | `N/A`（n8 batch manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/manifest.json`（SHA-256 `2da337f583fbdfb5cd3b8615d9fb254a30e011b4debf24a6bee7845ee19cf319`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n8 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=1227608 > 0`，`simTicks=2672215889220`，等于 `chain_end.tick(2910165686235) − checkpoint(237949797015)` |
| 原始事件数 | 9450（`chain_report.event_count=9450`；`fault_event_count=8333`，fault 1 的事件数） |
| fault_id 数量 | 4（fault 1 代表故障，L4 含住；fault 2 L5 检测层 squash；fault 3/4 仅 `provable_to_L4`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `238083182163`，一条 **load**（`dyn_inst_seq=393897`、`request_id=393897`）访问 `0xffffffc009483960`，命中 DTLB 第 `21` 号表项（`entry_index=21`、`walk_id=0`、`way=-1`）。注入前：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75960`。4 KiB 页、偏移 `0x960`，正常 PA `0x81d75960`。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `238083182163`，`VA=0xffffffc009483960`，`dyn_inst_seq=393897`）。`field=bit_flip`，`before=0x81d75`，`after=0x81d74`。注入日志 `Mask: 0x1`（`effective: 1`）与异或一致：**只翻转 PFN 的第 0 位**。有效 PFN 变为 `0x81d74`，偏移 `0x960` 不变，有效 PA 从 `0x81d75960` 变成 `0x81d74960`，`effective_pa_changed=1`。错误页比正确页小一页。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0）记录 `pfn 81d75 → 81d74`、`pa 81d75960 → 81d74960`，属性未动。`event_id=2`（`tlb_pfn`，parent=1）确认 `field=bit_flip`、`state_before=81d75960`、`state_after=81d74960`。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81d75960`、`after=81d74960`、`contained=0`、`outcome=NoFault`——翻译层没有检测或含住。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是 **load**：`event_id=4`（`lq_read`，parent=3，`dyn_inst_seq=393897`）；`event_id=32`（`lsq_push`，parent=4，Δtick=1332）记录 `field=load`、`pc=ffffffc0087b27c8`、`opcode=ldp_uop`（`lsq_push`/`lq_read` 都带 `lq_idx=41835`，`sq_idx=-1`，说明这是 load 的队列项）；`event_id=33`（`mem_req`）、`event_id=34`（`lsq_sendfrag`）、`event_id=35`（`tlb_translate`）、`event_id=36`（`lq_read`）依次推进同一个错误页的 load。输入是错误 PA，内部变化是压入 LSQ、分片、再翻译、读回；输出是一个待访问的 load 请求。

### 2.5 错误如何经过 cache 和 MSHR

主链上为 `N/A`：`event_id=36` 之后直接是 `event_id=68`（`squash_masked`，Δtick=61273），中间没有 `cache_access`/`cache_return`/`mshr_alloc`/`mshr_merge`/`mshr_fill`/`mshr_free`/`cache_fill`。按本 seed 的单祖先证据，这条错误翻译在进入 cache/MSHR 前就被 squash；流中的大量 cache/MSHR 事件属于其它请求或其它 fault 的分支（Ch.5），不能并入主链。

### 2.6 污染如何返回处理器状态

主链上为 `N/A`：event 68 的直接祖先里没有任何 `taint_reg` 或 `resp` 进入寄存器的记录。该 load 返回寄存器之前已被 squash（`contained=1`、`outcome=masked`），所以主链上不存在“污染返回处理器状态”的一步。流中确有 `taint_reg`（如 fault 1 的 request_handoff 分支、以及 fault 2/3/4 的分支），但它们都不是 event 68 的祖先，不能写成主链的一步。

### 2.7 最终传播终局（含住）

权威传播终局是 **event_id=68**（`kind=squash_masked`），parent=`36`，tick `238083244768`（Δtick=61273），`dyn_inst_seq=393912`，`corr=addr_fallback`，`va=ffffffc0094839e0`，`pa=81d749e0`，`field=squashed_load`，`contained=1`，`detection_layer=L4`，`outcome=masked`，`containment_reason=squash_replay`。它是真实的 `contained=1` 事件：同页后续 load（dyn 393912，偏移 `0x9e0`，PA `81d749e0`）在返回寄存器前被 squash 并重放。`parent=36` 把它挂在原始 load 的 `lq_read` 下，这体现传播栈对同页后续 load 的归属；事件自身记录的是 dyn 393912 的 `squashed_load`。所以 **L5=N/A**：本 seed 没有可证的 `errant_commit` 终局，`squash_masked` 只能作为 L4 含住，**不能写成 L5**；`chain_end`（event 9308，tick `2910165686235`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口。

两个必须解释的点：

1. 报告的 `provable_to=L5` 不是“错误提交”：checker 会把带 `detection_layer`/`outcome`/链关联 `corr` 的显式检测事件提升到 L5 检测层，`squash_masked` 满足条件；但它的 `detection_layer` 字段本身是 `L4`，表示 squash/replay 含住。本文件的 propagation terminal 取 **L4**（INDEX `propagation_terminal`）。
2. 事件 83（`errant_commit`，parent=68，tick `238083249096`，`dyn_inst_seq=393846`，`commit_seq=273130`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`）在流中存在，`run.out` 也在该 tick 打了 `reason=errant_commit`；但它沿单祖先到 L4 位置没有独立的 `taint_reg`/consumer 见证（event 68 被记在 L5 检测层），可证连续前缀只到 L3，属于悬空 `errant_commit`，按权威口径不改变 event 68 的 L4 含住终局，也不是本 seed 的 L5。

### 2.8 从传播终局到系统表现

传播终局 **L4 含住**；运行结局 `Crash`。`run.out` 在 `238083249096` 记录 `CHAOS_DETECT: layer=None contained=0 tick=238083249096 ptag=1 reason=errant_commit`（对应 event 83），此后记录大量 `contained=1 reason=squash_replay`，并以 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)` 结束；`run.err` 为 `Kernel panic in simulated kernel`。注意本 seed 是 **KERNEL PANIC**（不是 oops）。注入 tick `238083182163` → 含住 tick `238083244768`，含住时延 `62605` ticks；运行在 `2910165686235` 收口（`simTicks=2672215889220` 与之一致）。传播终局与运行结局必须分开：代表故障链在 L4 含住，但本次仿真仍以 Crash 结束。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483960`、命中第 21 项 | PPN `0x81d75 → 0x81d74`（bit0） | PA `0x81d75960 → 0x81d74960`，`contained=0` | 错误翻译进入流水线 |
| LQ | load、错误 PA | `lq_read`(4) → `lsq_push`(32) → `mem_req`(33) → `lsq_sendfrag`(34) → `tlb_translate`(35) → `lq_read`(36) | 待访问的 load | 错误地址在 LQ/LSQ 推进 |
| cache/MSHR | `N/A` | `N/A` | `N/A` | 进入 cache 前已被 squash |
| PRF/寄存器 | `N/A` | `N/A` | `N/A` | 未返回寄存器 |
| ROB/提交 | `N/A` | `N/A` | `N/A` | 无 L5；event 83 不可证 |
| RAS/squash | 同页后续 load（dyn 393912） | squash + replay | `squash_masked` event 68（L4 含住） | 真实含住点 |
| PropMonitor | 退出回调 | `chain_end`（9308–9311） | 生命周期收口 | 非 L5 |

一句话总结：一次 load 命中被单比特改坏的 TLB 表项（bit0，错误页 `81d74`），错误 PA `81d74960` 经 LQ/LSQ 的分片与再翻译推进；同页后续 load（dyn 393912）在返回寄存器前被 squash（event 68，L4，`squash_replay`），因此代表故障链在 L4 含住、L5=N/A；流中另有 event 83 的悬空 `errant_commit` 与 fault 2/3/4 的旁支，均不改变 event 68 的权威终局；本次运行的系统结局是 KERNEL PANIC。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：`prop_evt` 有 4 条 `inj`（fault 1–4），`armtlb_injections.log` 有 4 条 `arm_tlb_lookup_hit`（fault 1：old `0x81d75`、new `0x81d74`、`Mask: 0x1`；fault 2：old `0x81d74`、new `0xc1d74`、`Mask: 0x40000`；fault 3：old `0x81d74`、new `0x81974`、`Mask: 0x400`；fault 4：old `0x80c73`、new `0xc0c73`、`Mask: 0x40000`），`stats.numFaultsInjected=4`，`run.out injected=4`；`attempted=411962`、`eligible=411962`、`activated=W3-L0-layer`。代表故障（fault 1）的坏值被下游消费（event 68 的 `pa=81d749e0`）。激活成立。

### 3.2 故障传播类型

代表故障是**地址型**（错误物理页）；它在 L4 被 squash 含住，没有进入 cache/寄存器。不是数据型、permission、control-state、timing、wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `238083182163`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`。虽然是含住样本，但从这一刻起错误值已进入执行路径，是否可撤销取决于 squash（本 seed 在 L4 被 squash），而不是结构自身能纠正。

### 3.4 检测与掩蔽机制

起作用的是 **L4 squash/replay**（event 68）。TLB、cache、LQ/ROB 无检测能力。观察到的边界：(a) 含住的是**后续 load**（dyn 393912），不是注入的 load（dyn 393897）；(b) event 83 的 errant_commit 说明同一错误页仍有一次提交进入 oracle 视野，只是沿单祖先不可证；(c) 同一 seed 还有 fault 2 的 squash（event 8751）与 fault 3/4 的 L4 可证链，它们各自有各自的终局，不能与代表故障混为一谈。

### 3.5 最终 SDC 风险判断

权威传播终局是 **L4 含住**（真实 `contained=1` 事件 68），没有可证的 L5 逃逸，不构成 SDC 证据；运行结局是 KERNEL PANIC。无应用级输出 oracle，无法判断最终数据正确性。结论：代表故障链在 L4 被 squash 含住；运行 Crash；不构成可证 SDC；squash_masked 不得写成 L5。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 `238085259417`（VA `…2708`，掩码 `0x4000`，bit14；`full`），seed3 注入 `238095582084`（VA `…3950`，掩码 `0x4000`，bit14；`full`）。三个 seed 都是单比特；本 seed 是唯一位 0、错误页比正确页小一页、并以 L4 squash 收口的样本。本 seed 的 fault 2（bit18，`c1d74`）以 L4 squash 收口，fault 3（bit10，`81974`）与 fault 4（bit18，`c0c73`）只到 L4；这些都不影响代表故障选择。本 seed 的数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 权威含住见证 `event_id=68` 经 `parent_event_id` 回溯的单祖先，共 11 个事件，按 root→witness 排列。`Δtick` 相对上一行。`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账；对 `squash_masked`，checker 因 `_explicit_l5` 把它记在 L5 检测层（表中记作 `L5*`），而事件自身 `detection_layer=L4`——两列并列，不矛盾。含住样本的 L5 = N/A。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238083182163 | — | inj | L0 | TLB | 1 | origin | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 81d74 | 81d75 | 81d74 | 0x1 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 238083182163 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 81d74 | 81d75 | 81d74 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960 | — | — | — | — | 命中查询 | PFN 81d75→81d74 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 238083182163 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d74960 | — | — | 81d75 | 81d74 | 81d75 | 81d74 | — | 81d75960 | 81d74960 | — | — | — | — | 表项当前状态 | PA 81d75960→81d74960 | 表项存储被改写 |
| 4 | 3 | 2 | 238083182163 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d74960 | — | — | — | — | 81d75960 | 81d74960 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960 | 0 | — | NoFault | — | 表项 PFN | PA 81d75960→81d74960 | 首个不可逆点 |
| 5 | 4 | 3 | 238083182163 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误翻译 | load 读取（lq_idx=41835） | 错误地址进入 LQ |
| 6 | 32 | 4 | 238083183495 | 1332 | lsq_push | — | LSQ | 1 | seq_primary | — | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | load | load 入队（lq_idx=41835） | 错误进入队列 |
| 7 | 33 | 32 | 238083183495 | 0 | mem_req | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LSQ 项 | 生成访存请求 | 错误地址继续 |
| 8 | 34 | 33 | 238083183495 | 0 | lsq_sendfrag | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 访存请求 | 分片发出 | 错误地址继续 |
| 9 | 35 | 34 | 238083183495 | 0 | tlb_translate | L2 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 分片 | 再次翻译 | 复用同一坏表项 |
| 10 | 36 | 35 | 238083183495 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误翻译 | load 读取（lq_idx=41835） | 错误地址进入 LQ |
| 11 | 68 | 36 | 238083244768 | 61273 | squash_masked | L5* | RAS/squash | 1 | addr_fallback | — | 393912 | ffffffc0094839e0 | 81d749e0 | — | — | — | — | — | — | — | — | — | 1 | L4 | masked | squash_replay | 同页后续 load（dyn 393912） | squash + replay | 真实 L4 含住 |

折叠说明：1421 个 `consumer`（event 84–9303，tick `238083250428..2910165543711`）全在终局之后/其它 fault 分支上，不在 event 68 的祖先上；59 条其它 `squash_masked`、event 83 也不在主链上，故无 consumer 行可折叠。

## 5. 相关旁支与未进入最终主链的事件

**`request_handoff` 桥**：`event_id=4294967296`，parent=4，tick `238083183495`，`bridge_layer=L3`、`bridge_reason=request_handoff`，`old_request_id=393897`、`new_request_id=393847`，`shared_addr=ffffffc009483960`、`shared_size=10`（16 字节），`source_event_id=4`、`dest_event_id=26`。它分出一支 `cache_access(26) → cache_return(27) → mshr_merge(28) → resp(79) → lq_complete(80) → taint_reg(81/82) → … → 1797` 的分支；该分支有 `taint_reg` 和后续 squash，但**不在** event 68 的祖先上，也不构成权威终局。

**事件 83（悬空 errant_commit）**：parent=68，tick `238083249096`，`dyn_inst_seq=393846`，`commit_seq=273130`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`。沿单祖先到它的可证前缀只到 L3（L4 位置无独立见证），不可证为 L0→L5 逃逸；不改变 L4 含住终局。

**其余 `squash_masked`（59 条，流中共 60 条含 event 68）**：分布在同一错误页的多个 VA 上，例如 1679、1714、1734、1797、1924、1930、2013/2014/2015、2194、2357、…、7922（tick `238095210789`），以及 fault 2 页上的 8751（tick `238720227813`）。它们都是后段 squash/replay，不是 event 68 的替代见证。

**fault 2/3/4**：

| fault | inj event | tick | VA | old→new pfn | mask | 自身终局 |
|---|---|---|---|---|---|---|
| 2 | 8331 | 238719961413 | ffffffc0094832c0 | `81d74 → c1d74` | `0x40000`（bit18） | `detected_contained`/L5（squash 8751，tick 238720227813） |
| 3 | 9255 | 1464380320167 | ffffffc009482eb0 | `81d74 → 81974` | `0x400`（bit10） | `provable_to_L4_then_unknown`（chain_end 9310 `store_discarded_not_retired`） |
| 4 | 9280 | 2910165482106 | ffffffc008c730e0 | `80c73 → c0c73` | `0x40000`（bit18） | `provable_to_L4_then_unknown`（chain_end 9311 `store_discarded_not_retired`） |

fault 4 的注入 tick `2910165482106` 距运行收口 `2910165686235` 只有 `204129` ticks，是“运行末端注入”的样本；它只到 L4，不影响代表故障。

**request_fork（138 条）**：1 条 `request_handoff`（上述）+ 137 条 `addr_fallback_broadcast`（`shared_addr` 共 4 个页基址，`shared_size=1000`）。广播分支不汇入 event 68 的主链。

**off-chain 事件**：主链含 2 条 `lq_read`、1 条 `lsq_push`、1 条 `mem_req`、1 条 `lsq_sendfrag`、1 条 `tlb_translate`、1 条 `squash_masked`；其余 1696 条 `cache_access`、1696 条 `cache_return`、98 条 `mshr_alloc`、150 条 `mshr_merge`、98 条 `mshr_fill`、98 条 `cache_fill`、98 条 `mshr_free`、1536 条 `resp`、533 条 `lq_complete`、1792 条 `taint_reg`、2 条 `sq_execute`/`sq_writeback`/`sq_complete` 等都在主链之外，属其它 fault 或同页重复消费者。

**consumer（1421 条）**：event 84–9303，全在终局/旁支之后。**生命周期**：`chain_end` 9308–9311 都是退出回调；9308 的 `outcome=errant_commit_seen` 不是 L5。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `detected_contained` |
| provable_to | `L5`（检测层记账；squash_masked 自身 `detection_layer=L4`） |
| propagation terminal | **L4** |
| 传播终局事件 | `squash_masked` event_id=`68`，tick=`238083244768`，parent=`36`，`contained=1`，`detection_layer=L4`，`outcome=masked`，`containment_reason=squash_replay` |
| L5 | `N/A`（无可证 errant_commit；event 83 悬空） |
| run outcome | `Crash`（`KERNEL PANIC under fault`） |
| admitted / certified | `True` / `True`；`violations=[]`（`admission.path=contained`） |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=1227608`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级；该文件把 4 个 activated fault 计为 4 行 Crash，与代表故障的 L4 含住是两个层面） |
| campaign/checker agreement | 一致：report `detected_contained/L5`，checker 同，路径 `['0','1','2','4','81','1797']` 相同（层锚点路径，不是终局见证） |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T01-F2-W1` = true |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**必须记录的不一致**：矩阵 Excel 行 45 的负载标签是 `MiBench-TC23 论文负载（…）`，且 `记录状态=blocked(fs-infra: SE has no MiBench FS pipeline)`；但本 seed 的 `run.out` 实际使用 `--readfile …/configs/fs/tlb_probe.rcS`。按事实并列，不把矩阵标签当作实际负载。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2/prop_evt.txt.gz` | `c83d89fd9f64ded18ef3cffa85c6e1453075dfd96aeef74228ff680db783eaf7` | 346270 | 1793083470 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2/chain_report.json` | `73cda7ecfea43e1631f2717f378cdb46ba888f81b7641d7020be36bbfa955ad3` | 960002 | 1793083471 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2/run.out` | `4fa0ea2ec92839694f07615e9f5cdc1dcfe1764a99095b5743116604fb541ebe` | 8216 | 1793083471 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2/run.err` | `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d` | 1912 | 1793083471 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2/stats.txt` | `4fc67a27cc7c8e6e17f5076c5867921d9637a82abc58f3a4cb8ee71ec061d62b` | 391280 | 1793083470 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/manifest.json` | `2da337f583fbdfb5cd3b8615d9fb254a30e011b4debf24a6bee7845ee19cf319` | 1438 | 1793083473 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| 源码 head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s2/T01-F2-W1/seed2`。

**其它副本与分类**：本 seed 的 n8 运行根下未发现 `.sha8a229009` 型旧二进制副本；本文件只使用上表权威目录。注意 README 明确把本 seed 与 T01-F2-W4 seed2 / T02-F2-W4 seed2 / T02-F2-W1 seed2 / T10-F2-W1 seed2 并列为“同类 L4 `squash_masked` event 68 含住（同一 tick/parent/VA，PA 因故障模型不同而不同）”；本文件只使用本 seed 自己的 PA（`81d749e0`），不引入其它 RunID 的 PA。
