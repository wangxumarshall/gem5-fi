# T01-F2-W4 seed2 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `3a3ea879…852a`）重建；其余文件只读引用。**本 seed 是含住样本**：权威传播终局是 L4 `squash_masked`（event 68），不是 L5；所有 event_id / tick / 地址 / 状态只来自本 seed。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T01-F2-W4`（模型 ID `T01`，单元 `L1d-TLB`） |
| seed / sample_run_id | `2` / `s2` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**单比特** `bit_flip`（`--tlb_fault_type bit_flip`，1 bit；`--tlb_probability 1.0`） |
| 故障类型 | 单比特翻转 |
| 频率 tier | 请求 `F2` / 生效 `F2` / `lookup_tier_enabled=1` |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`（矩阵 Excel 行 46） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`；`--kernel …/gem5-fs/vmlinux`、`--disk …/gem5-fs/ubuntu.img`、`--bootloader …/gem5-fs/boot.arm64`、`--cpu O3`、`--restore-checkpoint …/fs_cpt_boot/cpt.237949797015` |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T01-F2-W4 --prop_sample_run_id s2` |
| source head | `N/A`（n7 batch manifest 无 `source_head`） |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/manifest.json`（SHA-256 `d5c08c43293f3cc1f785d224cdfe0085dbdbf9409b49fa740bc120ed318a8a9d`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n7 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=555348 > 0`，`simTicks=976756266`，等于 `chain_end.tick(238926553281) − checkpoint(237949797015)` |
| 原始事件数 | 8338（`chain_report.event_count=8338`；`fault_event_count=8333`，另有 fault 2 的 5 条） |
| fault_id 数量 | 2（fault 1 主故障；fault 2 是后段 L2 含住的独立注入） |
| 是否经过离线 regrade | 否（plain `chain_report.json`，无 `*regrade*`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `238083182163`，一条 **load**（`dyn_inst_seq=393897`、`request_id=393897`）访问 `0xffffffc009483960`，命中 DTLB 第 `21` 号表项（`entry_index=21`、`walk_id=0`、`way=-1`）。注入前：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75960`。4 KiB 页、偏移 `0x960`，正常 PA `0x81d75960`。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `238083182163`，`VA=0xffffffc009483960`，`dyn_inst_seq=393897`、`request_id=393897`）。`field=bit_flip`，`before=0x81d75`，`after=0x81d77`。注入日志 `Mask: 0x2`（`effective: 1`）与异或一致：**只翻转 PFN 的第 1 位**。第 1 位在 48 位 PFN 内，有效 PFN 变为 `0x81d77`，偏移 `0x960` 不变，有效 PA 从 `0x81d75960` 变成 `0x81d77960`，`effective_pa_changed=1`。这是一次“低位翻转、页基址相邻”的典型错误：错误页与原页只差一页。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0）记录 `pfn 81d75 → 81d77`、`pa 81d75960 → 81d77960`，属性未动。`event_id=2`（`tlb_pfn`，parent=1）确认 `field=bit_flip`、`state_before=81d75960`、`state_after=81d77960`。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81d75960`、`after=81d77960`、`contained=0`、`outcome=NoFault`——翻译层没有检测，也没有含住。

### 2.4 错误如何进入 LQ/SQ/LSQ

这次是 **load**：`event_id=4`（`lq_read`，parent=3，`dyn_inst_seq=393897`、`request_id=393897`）先建立读取；随后 `event_id=32`（`lsq_push`，parent=4，Δtick=1332）记录 `field=load`、`pc=ffffffc0087b27c8`、`opcode=ldp_uop`（`lsq_push`/`lq_read` 都带 `lq_idx=41835`、`sq_idx=-1`，说明这是 load 的队列项）。`event_id=33`（`mem_req`，parent=32）生成访存请求；`event_id=34`（`lsq_sendfrag`，parent=33）把 load 分片发出；`event_id=35`（`tlb_translate`，parent=34）在访存路径上再次走翻译；`event_id=36`（`lq_read`，parent=35）再次读取 LQ 项。输入是错误 PA，内部变化是 load 被压入 LSQ、分片、再次翻译并读回；输出是一个带着错误物理页的 load 请求，下一个消费点是 cache/mshr（本 seed 在它之前就被 squash，见 2.7）。

### 2.5 错误如何经过 cache 和 MSHR

本节在主链上为 `N/A`：`event_id=36`（`lq_read`）之后，主祖先直接跳到 `event_id=68`（`squash_masked`，Δtick=61273），中间没有 `cache_access`、`cache_return`、`mshr_alloc`、`mshr_merge`、`mshr_fill`、`mshr_free`、`cache_fill` 事件。也就是说，按本 seed 的单祖先证据，这条错误翻译在进入 cache/MSHR 之前就被 squash 掉了；流里确实存在大量 cache/MSHR 事件，但它们属于其它请求分支（Ch.5），不能并入本主链。

### 2.6 污染如何返回处理器状态

本节在主链上为 `N/A`：`event_id=68` 的直接祖先里没有任何 `taint_reg`、没有 `resp` 进入寄存器的记录。原因是这条 load 在返回寄存器之前就被 squash（`contained=1`、`outcome=masked`、`containment_reason=squash_replay`），所以主链上不存在“污染返回处理器状态”的一步。流中确实有 `taint_reg`（例如 event 81/82，位于 `request_handoff` 分支上），但那不是 event 68 的祖先，详见 Ch.5；不能把那条分支的 `taint_reg` 写成主链的一步。

### 2.7 最终传播终局（含住）

本 seed 的权威传播终局是 **event_id=68**（`kind=squash_masked`），parent=`36`，tick `238083244768`（相对 `lq_read` Δtick=61273），`dyn_inst_seq=393912`，`corr=addr_fallback`，`va=ffffffc0094839e0`，`pa=81d779e0`，`field=squashed_load`，`contained=1`，`detection_layer=L4`，`outcome=masked`，`containment_reason=squash_replay`。它是真实的 `contained=1` 事件：一条后续复用同一错误翻译的 load（`dyn_inst_seq=393912`，VA 在同一故障页的 `0x9e0` 偏移，PA `81d779e0`）被 squash 并重放，没有再返回寄存器。`parent=36` 表明它挂在原始 load 的 `lq_read` 之下——这是传播栈对同页后续 load 的归属记录，事件自身记录的是 dyn 393912 的 `squashed_load`。因此 **L5 = N/A**：本 seed 没有可证的 `errant_commit` 终局，`chain_end`（event 8335，tick `238926553281`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口，不能当作 L5；`squash_masked` 本身是 L4 含住，**绝不能写成 L5**。

需要解释两个容易误读的点：

1. **权威报告的 `provable_to=L5` 不是“错误提交”**。checker 的 `_layer_of` 会把带 `detection_layer`、`outcome`、链关联 `corr` 的显式检测事件提升到 L5（检测/结局层），`squash_masked` 满足这一条件，所以层锚点路径可以到 L5；但该事件的 `detection_layer` 字段本身是 `L4`，代表的是 squash/replay 含住，不是 `errant_commit`。本文件的 propagation terminal 取 **L4**（见 INDEX 的 `propagation_terminal`），与权威口径一致。
2. **事件 83 的存在不改变 L4 含住**。`event_id=83`（`errant_commit`，parent=68，tick `238083249096`，`dyn_inst_seq=393846`，`commit_seq=273130`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`）在流中确实存在，`run.out` 也在该 tick 打了 `reason=errant_commit`。但按单祖先回溯，它的祖先在 L4 位置没有独立的 `taint_reg`/consumer 见证（event 68 作为显式检测事件被记在 L5 检测层），因此从 root 到 event 83 的可证连续前缀只到 L3，**不能构成可证的 L0→L5 逃逸**；按权威 `_errant_commit_escape` 口径它是“悬空 errant_commit”，不改变 event 68 的 L4 含住终局。这与 README 的既定口径一致：本 seed 的权威见证是 event 68，不是 event 83，也不是更晚的 event 1797。

### 2.8 从传播终局到系统表现

传播终局是 **L4 含住**（`detected_contained`，`provable_to=L5` 仅指检测层记账）；运行结局是 `Crash`。`run.out` 在 `238083249096` 记录了 `CHAOS_DETECT: layer=None contained=0 tick=238083249096 ptag=1 reason=errant_commit`（对应 event 83），并在此后记录了大量 `contained=1 reason=squash_replay`；`run.out` 最终以 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)` 结束，`run.err` 为 `Kernel oops in guest`。也就是说：**代表故障的传播链在 L4 被 squash 含住，但这次仿真的系统结局仍是 Crash**。两者必须分开陈述，不能因为 oracle=Crash 就把 event 68 改判成 L5，也不能因为 event 68 含住就宣称整个运行没有崩溃。注入 tick `238083182163` → 含住 tick `238083244768`，含住时延 `62605` ticks；运行在 `238926553281` 的 `chain_end` 收口。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483960`、命中第 21 项 | PPN `0x81d75 → 0x81d77`（bit1） | PA `0x81d75960 → 0x81d77960`，`contained=0` | 错误翻译进入流水线，无检测 |
| LQ | load、错误 PA | `lq_read`(4) → `lsq_push`(32) → `mem_req`(33) → `lsq_sendfrag`(34) → `tlb_translate`(35) → `lq_read`(36)；槽位号未记录 | 待访问的 load 请求 | 错误地址在 LQ/LSQ 中推进 |
| cache/MSHR | `N/A` | `N/A` | `N/A` | 主链在 36 之后直接到 squash，未进入 cache |
| PRF/寄存器 | `N/A` | `N/A` | `N/A` | 未返回寄存器即被 squash |
| ROB/提交 | `N/A` | `N/A` | `N/A` | 无 L5；event 83 不可证为逃逸 |
| RAS/squash | 同页后续 load（dyn 393912） | squash + replay | `squash_masked` event 68（L4 含住） | 真实含住点 |
| PropMonitor | 退出回调 | `chain_end`（8335/8336） | 生命周期收口 | 非 L5 |

一句话总结：一次 load 命中被单比特改坏的 TLB 表项（bit1，错误页 `81d77`），错误 PA `81d77960` 经 LQ 第 44911 前后的读取/分片/再翻译推进到 LQ 尾部；同页后续 load（dyn 393912）在返回寄存器之前被 squash（event 68，L4，`squash_replay`），所以代表故障的传播链在 L4 含住、L5=N/A；流中另有 event 83 的 `errant_commit` 与更晚的 event 1797 squash，但前者沿单祖先不可证、后者只是同页更晚的一次含住，二者都不改变 event 68 的权威终局；本次运行的系统结局仍是 Crash，二者分开陈述。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：`prop_evt` 有 2 条 `inj`（fault 1 + fault 2），`armtlb_injections.log` 有 2 条 `arm_tlb_lookup_hit`（fault 1：old `0x81d75`、new `0x81d77`、`Mask: 0x2`；fault 2：old `0x81d77`、new `0x800000000081d77`、`Mask: 0x800000000000000`），`stats.numFaultsInjected=2`，`run.out injected=2`；`attempted=233994`、`eligible=233994`、`activated=W3-L0-layer`。代表故障（fault 1）的坏值被下游读取：`tlb_lookup.state_after.pfn`、`tlb_pfn.after`、`tlb_translate_result.after` 以及 event 68 的 `pa=81d779e0` 都带 `81d77`。激活成立。

### 3.2 故障传播类型

**地址型**（错误物理页）。代表故障传播的是错误 PA；它在 L4 被 squash 含住，没有进入 cache，也没有返回寄存器。不是数据型、permission、control-state、timing 或 wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `238083182163`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`。虽然是含住样本，但从这一刻起错误值已经进入执行路径；后面能否撤销取决于是否被 squash（本 seed 确实在 L4 被 squash），而不是 TLB 结构自身能纠正。

### 3.4 检测与掩蔽机制

实际起作用的掩蔽机制是 **L4 squash/replay**：event 68 以 `contained=1`、`detection_layer=L4`、`outcome=masked`、`containment_reason=squash_replay` 记录了一条同页 load 被 squash。TLB、cache、LQ/ROB 都没有检测能力。观察到的盲区/边界：(a) 触发含住的是**后续 load**（dyn 393912），不是注入的那条 load（dyn 393897）；(b) event 83 的 `errant_commit` 说明同一错误页仍有一次提交逃逸到 oracle 视野，只是它沿单祖先不可证；(c) event 1797 等更晚的 squash 只能清理后续消费。因此“含住”是本链的权威传播终局，但不是“整个系统没有被污染”的证明。

### 3.5 最终 SDC 风险判断

权威传播终局是 **L4 含住**：真实 `contained=1` 事件（event 68），没有可证的 L5 逃逸，因此本样本不判 SDC（也没有可证的 errant commit 作为 SDC 证据）。需要同时说明：事件 83 的 `errant_commit`（及其 oracle 检测）与运行结局 Crash 表明系统层面仍有错误后果；本 workload 没有应用级输出 oracle，无法判断最终数据正确性。结论只能是：**代表故障链在 L4 被 squash 含住；运行结局 Crash；不构成可证 SDC；也不得把 squash_masked 当作 L5**。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 `238085259417`（VA `…2708`，掩码 `0x400000000000`，bit46；`full`），seed3 注入 `238095582084`（VA `…3950`，掩码 `0x200000000000`，bit45；`full`）。三个 seed 都是单比特；本 seed 是唯一一个 bit1（低位）且以 L4 squash 收口的。本 seed 还额外有 fault 2（`238719961413`，VA `…32c0`，掩码 `0x800000000000000`，bit59 越界→PA 不变，L2 含住）和一条不可证的 event 83 `errant_commit`；其它 seed 的 event_id/tick/地址未被引入本链。

## 4. 完整主链事件表

主链 = 权威含住见证 `event_id=68` 经 `parent_event_id` 回溯的单祖先，共 11 个事件，按 root→witness 排列。`Δtick` 相对上一行。`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账；对 `squash_masked`，checker 因 `_explicit_l5` 把它记在 L5 检测层（表中记作 `L5*`），而事件自身 `detection_layer=L4`——两列并列，不矛盾。含住样本的 L5 = N/A。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238083182163 | — | inj | L0 | TLB | 1 | origin | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 81d77 | 81d75 | 81d77 | 0x2 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 238083182163 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 81d77 | 81d75 | 81d77 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d77;ap=0;mtype=2;page_size=1000;pa=81d77960 | — | — | — | — | 命中查询 | PFN 81d75→81d77 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 238083182163 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d77960 | — | — | 81d75 | 81d77 | 81d75 | 81d77 | — | 81d75960 | 81d77960 | — | — | — | — | 表项当前状态 | PA 81d75960→81d77960 | 表项存储被改写 |
| 4 | 3 | 2 | 238083182163 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d77960 | — | — | — | — | 81d75960 | 81d77960 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d77;ap=0;mtype=2;page_size=1000;pa=81d77960 | 0 | — | NoFault | — | 表项 PFN | PA 81d75960→81d77960 | 首个不可逆点 |
| 5 | 4 | 3 | 238083182163 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误翻译 | load 读取（lq_idx=41835） | 错误地址进入 LQ |
| 6 | 32 | 4 | 238083183495 | 1332 | lsq_push | — | LSQ | 1 | seq_primary | — | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | load | load 入队（lq_idx=41835） | 错误进入队列 |
| 7 | 33 | 32 | 238083183495 | 0 | mem_req | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LSQ 项 | 生成访存请求 | 错误地址继续 |
| 8 | 34 | 33 | 238083183495 | 0 | lsq_sendfrag | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 访存请求 | 分片发出 | 错误地址继续 |
| 9 | 35 | 34 | 238083183495 | 0 | tlb_translate | L2 | TLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 分片 | 再次翻译 | 复用同一坏表项 |
| 10 | 36 | 35 | 238083183495 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误翻译 | load 读取（lq_idx=41835） | 错误地址进入 LQ |
| 11 | 68 | 36 | 238083244768 | 61273 | squash_masked | L5* | RAS/squash | 1 | addr_fallback | — | 393912 | ffffffc0094839e0 | 81d779e0 | — | — | — | — | — | — | — | — | — | 1 | L4 | masked | squash_replay | 同页后续 load（dyn 393912） | squash + replay | 真实 L4 含住 |

折叠说明：1275 个 `consumer`（event 84–8330，tick `238083250428..238134809817`）全在终局之后/其它分支上，不在 event 68 的祖先上，故 Ch.4 无 consumer 行；58 条其它 `squash_masked`、event 83、event 1797 等也不在主链上，见 Ch.5。

## 5. 相关旁支与未进入最终主链的事件

**`request_handoff` 桥（唯一一条 request_fork）**：`event_id=4294967296`，parent=4，tick `238083183495`，`bridge_layer=L3`、`bridge_reason=request_handoff`，`old_request_id=393897`、`new_request_id=393847`，`shared_addr=ffffffc009483960`、`shared_size=10`（十六进制，16 字节），`source_event_id=4`、`dest_event_id=26`。它把请求从 393897 交给 393847，分出一条 `cache_access(26) → cache_return(27) → mshr_merge(28, mshr 5) → resp(79) → lq_complete(80) → taint_reg(81 arch29/phys236) → taint_reg(82 arch30/phys253) → consumer(84) → … → consumer(1778) → squash_masked(1797)` 的分支。这条分支**不在** event 68 的祖先上：它有自己的 `taint_reg` 与后续 squash（1797，tick `238085898111`，VA `…33c0`，PA `81d773c0`），但按权威口径它不是本 seed 的终局见证（权威见证是 event 68，不是 1797）。它对本 SDC 诊断的意义是：同一错误页确实有另一条返回了寄存器并最终被 squash 的路径，说明传播面比主链更宽，但不能把这条分支的事件并入 Ch.2/Ch.4。

**事件 83（悬空 errant_commit）**：parent=68，tick `238083249096`，`dyn_inst_seq=393846`，`commit_seq=273130`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`。它在事件 68 的子树中，但沿单祖先到它的可证连续前缀只到 L3（event 68 是显式检测事件，被记在 L5 检测层，L4 位置没有独立的 `taint_reg`/consumer 见证），故不可证为 L0→L5 逃逸；它不改变 L4 含住终局，也不能被写成 L5 终局。

**其余 `squash_masked`（58 条，流中共 59 条含 event 68）**：分布在同一错误页的多个 VA 上，例如 1679（tick `238085666676`）、1714、1734、1797、1924、1930、2013/2014/2015、2194、2357、…、7922（tick `238095210789`）。它们都是同页后续 load 的 squash/replay，发生时间晚于 event 68，按 FILE 口径只是“同一故障、同一类、不同 VA 上更晚的含住”，不改变权威终局。

**fault 2**：独立注入 `event_id=8331`，tick `238719961413`，VA `0xffffffc0094832c0`，`old_pfn=81d77`、`new_pfn=800000000081d77`、`Mask: 0x800000000000000`（第 59 位，高于 48 位 PFN），因此有效 PA 不变（`81d772c0`）；`event_id=8334`（`tlb_translate_result`，contained=1，L2，`effective_pa_unchanged`）与 `chain_end 8336` 记录其 L2 含住。它是 sibling fault，不在代表故障的链上；按 escape-first 选择（同为 detected_contained，fault 1 的可证路径 6 段长于 fault 2 的 3 段）选 fault 1。

**consumer（1275 条）**：event 84–8330，tick `238083250428..238134809817`，全部是终局/旁支之后的污染传播记录，只作为后果列出。**生命周期**：`chain_end` 8335（fault 1，L5 errant_commit_seen）与 8336（fault 2，L2 detected_contained）都是退出回调。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `detected_contained` |
| provable_to | `L5`（checker 的检测/结局层记账；squash_masked 自身 `detection_layer=L4`） |
| propagation terminal | **L4**（`propagation_terminal`，INDEX 记录） |
| 传播终局事件 | `squash_masked` event_id=`68`，tick=`238083244768`，parent=`36`，`contained=1`，`detection_layer=L4`，`outcome=masked`，`containment_reason=squash_replay` |
| L5 | `N/A` —— 无可证的 `errant_commit` 终局；事件 83 是悬空 errant_commit，不改变含住口径 |
| run outcome | `Crash`（`KERNEL OOPS under fault`；run.out 在 `238083249096` 也记录了 errant_commit） |
| admitted / certified | `True` / `True`；`violations=[]`（`admission.path=contained`） |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=555348`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级；该文件把 2 个 activated fault 都计为 Crash 行，与代表故障的 L4 含住是两个层面） |
| campaign/checker agreement | 一致：report `detected_contained/L5`，检查器复算同为 `detected_contained/L5`，路径 `['0','1','2','4','81','1797']` 相同（该路径是层锚点路径，不是终局见证） |
| CHAIN_DEMONSTRATED | YES（代表故障在单祖先上从 `inj` 可证到真实 `contained=1` 事件） |
| COMPLETE_3_OF_3 | `T01-F2-W4` = true |
| 判定 | **PASS**（含住口径按 event 68；L5=N/A；run outcome 与传播终局分开） |

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2/prop_evt.txt.gz` | `3a3ea87997a147ab913aa2950fea7fb3c11017132938ce8da528b89434ff852a` | 305472 | 1793040266 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2/chain_report.json` | `342806364ec5eb35aa2c12fb3468b5c4138f04ee846f33f7332a45b85a832f27` | 908364 | 1793040268 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2/run.out` | `d77b16173e4b98f708bf9094a3485ea299f332137a78369b1c1de3cd2d42130a` | 8002 | 1793040267 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2/run.err` | `de8403ca5671675b258d5cc2e9d99a733336eef03c49490bb0d383150eb6e549` | 1800 | 1793040267 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2/stats.txt` | `071ba1c1dc5fd587988ae4c0128d5b7e7a77ee47f8812404819ef1cf70fb63e9` | 392423 | 1793040267 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/manifest.json` | `d5c08c43293f3cc1f785d224cdfe0085dbdbf9409b49fa740bc120ed318a8a9d` | 1438 | 1793040269 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | — | — |
| 源码 head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s2/T01-F2-W4/seed2`。

**其它副本与分类**：`runs/lsu/r6_n6_T01-F2-W4_s2/T01-F2-W4/seed2` 为 **OLD_BINARY_REFERENCE**（binary `e8052842…`）。本文件只使用上表权威目录。
