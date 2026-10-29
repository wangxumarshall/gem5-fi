# T02-F2-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T02-F2-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T02`）
- fault model：PPN 内同时翻转 2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`双比特翻转`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F2 — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier：`F2`；effective tier：`F2`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`）
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T02-F2-W4 --prop_sample_run_id s1`
- source head：N/A（manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同二进制构建源）
- binary source head：N/A（manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同二进制构建源）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/manifest.json`（SHA-256 `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9`；run 根 manifest（seed 字段=3，artifacts 尺寸对应最后一个 seed；不按它推断本 seed 的逐 seed 事实）；manifest.status=`FINISHED`，manifest.exit_code=`0`，manifest.seed=`3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`0`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：1100（与 `chain_report.event_count` 相同）
- fault_id 数量：1（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本章按最终见证 `errant_commit`（event_id=20）的单祖先链重建，顺序严格为 parent 先于 child：`0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 14 → 15 → 16 → 20`。这十五个事件全部来自本 seed 自己的 `prop_evt.txt.gz`，没有借用同 RunID 其它 seed 的任何 event_id、tick 或地址。event 11–13 不在这条祖先上，它们是 `mshr_alloc`（event 10）分出的 `request_fork` 支路（见第 5 章）。

### 2.1 故障注入前的正常状态

被注入的表项属于 DTLB 的第 13 号 entry（`event_id=1` 的 `entry_index=13`，`way=-1` 表示该注入器不区分 way），`state_before` 为 `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`。这是一次 4 KiB 页（`page_size=1000`）的地址翻译：VPN=`0xffffff8001362`，ASID=206，`valid=1`、`global=1`，权限字段 `ap=0`，当前正常 PFN=`0x81362`。触发本次翻译的访存指令是 `dyn_inst_seq=415526`，其 `request_id` 也是 415526，VA=`0xffffff8001362708`；VA 的低 12 位页内偏移为 `0x708`，因此正常物理地址是 `(0x81362 << 12) | 0x708 = 0x81362708`，与 `state_before` 记录的 `pa=81362708` 完全一致。`event_id=0` 的 `inj` 事件以 `corr=origin` 标记这次注入是整条链的源头，`evidence_status=observed` 说明该事件是运行时真实发射、不是离线补写。

### 2.2 故障具体如何注入

注入发生在 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=238085259417（cycle=714970749），`event_id=0`，`fault_id=1`，`request_id=415526`，`corr=origin`，字段 `field=bit_flip`，FaultType=`bit_flip`。`armtlb_injections.log` 对同一次注入记录的 Mask 为 `0x800400000000000`：
`Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, old_pfn: 0x81362, new_pfn: 0x800400000081362, FaultType: bit_flip, Mask: 0x800400000000000`。
由前值 `before=0x81362` 与后值 `after=0x800400000081362` 可算出异或差为 `0x800400000000000`，即同时翻转了 PFN 的第 46 位与第 59 位两个 bit——这与 T02 的“双比特翻转”模型一致：两个 bit 在同一次 TLB 命中事件中生效，没有改动 `ap`、`page_size`、ASID、valid/global 等字段。`old_pfn=0x81362`、`new_pfn=0x800400000081362`，VA 不变，仍为 `0xffffff8001362708`。

这里必须把数值变化说透：gem5 在把 PFN 组装成物理地址时执行的是 `((pfn << 12) mod 2^64) | (VA & 0xFFF)`。`new_pfn << 12 = 0x800400000081362000`，它在 64 位截断后丢掉最高位的第 59 位，剩下 `0x400000081362000`；再或上页内偏移 `0x708` 得到新的有效物理地址 `0x400000081362708`。也就是说，第 59 位的翻转落在 64 位左移 12 位后被截掉的区间里，对有效 PA 没有任何贡献；真正改变有效 PA 的是第 46 位，它使 PA 的第 58 位由 0 变 1。因此 `old_pa=0x81362708`、`new_pa=0x400000081362708`，`effective_pa_changed` 为真（`event_id=3` 的 `field=effective_pa_changed`，`before=81362708`、`after=400000081362708`）。这一区分很重要：如果两个 bit 都落在被截断的高位，PA 不会改变，链会在 L2 就被含住；而本 seed 至少有一个 bit（第 46 位）落在有效宽度内，所以错误 PA 被真实交给了下游。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=238085259417，与注入同 tick）是故障值第一次被真实查询路径读取：它命中第 13 号 entry（`entry_index=13`、`way=-1`），`field=post_lookup`，`before=81362`、`after=800400000081362`，`state_after` 的 `pfn` 与 `pa` 分别变为 `800400000081362` 和 `400000081362708`。`event_id=2` 的 `tlb_pfn` 把该命中值固化为翻译的 PFN 记录（`state_before=81362708`、`state_after=400000081362708`，`pa=400000081362708`）。`event_id=3` 的 `tlb_translate_result` 是本 seed 的翻译结论点：`field=effective_pa_changed`，`before=81362708`、`after=400000081362708`，`contained=0`、`outcome=NoFault`、`detection_layer` 为空、`containment_reason` 为空。这意味着 TLB 明确知道有效 PA 已经改变，却**没有**含住它，也不存在 L2 级检测；它在 tick 238085259417 把有效 PA `0x400000081362708` 连同 `request_id=415526` 一起交给 LSU。请求的 VA 是 `0xffffff8001362708`；TLB 给出的有效 PA 是 `0x400000081362708`；`effective_pa_changed=1`；`contained=0`；`detection_layer=N/A`；`containment_reason=N/A`。从这一刻起，后续所有访存都指向错误的物理页。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径（不是 store）：`event_id=4` 的 `lq_read` 在 tick 238085259417 读取 LQ 条目 `lq_idx=44911`，`request_id=415526`，VA=`0xffffff8001362708`，`corr=seq_primary`。它的输入是 2.3 的翻译结果，内部变化是把该请求从 LQ 中取出并准备发起 L1D 访问，输出是同一 `request_id` 的 cache 访问。本 seed 的流里没有 `lsq_push`/`mem_req`/`lsq_sendfrag` 事件，因此这三类事件的字段一律为 N/A——不是“没有进入 LSQ”，而是该发射器在本次运行中未发射这几个中间 kind；可证的事实止于 `lq_read` 已把请求带入 L1D 路径。L1D 访问同样以 `request_id=415526`、VA 不变、PA=`0x400000081362708` 进行，说明 LSU 消费的正是 TLB 给出的错误 PA。

### 2.5 错误如何经过 cache 和 MSHR

第一次访问 `event_id=5`（`cache_access`，tick=238085259417，PA=`0x400000081362708`）在 L1D 中未命中：`event_id=6` 的 `cache_return` 记录 `field=miss`（tick 同上），随后 `event_id=7` 分配 `mshr_id=1`，`cache_line=0x400000081362708`，`state_after=mshr_allocated`。同一请求在 333 ticks 后（tick=238085259750）进行第二次访问 `event_id=8`，这次 PA=`0x400000081362700`，同样未命中（`event_id=9`，`field=miss`），并分配 `mshr_id=2`、`cache_line=0x400000081362700`（`event_id=10`）。两次访问的 PA 只差低位的 `0x8`，说明这是同一 4 KiB 页内的两次相邻子访问；两次都走了 miss→MSHR 分配。本故障链在 `event_id=10` 之后直接到 `event_id=14` 的 `resp`，流内没有为这两个 MSHR 发射 `mshr_fill`/`cache_fill`/`mshr_free`；因此填充动作在事件流中不可见（N/A），不能声称“填充把错误行写入了 cache”。仍可证明的是：MSHR 以错误的物理行号为键分配并等待数据，`resp` 使用 `request_id=415526` 返回，链的同一性由共享 `fault_id=1`、单祖先 `parent_event_id` 与相同 `request_id` 维持。

本链出现的 kind 集合为 `cache_access、cache_return、errant_commit、inj、lq_complete、lq_read、mshr_alloc、resp、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mshr_fill、cache_fill、mshr_free、lsq_push、mem_req、lsq_sendfrag、sq_execute、sq_writeback、sq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=14` 的 `resp`（tick=238085367975）把 MSHR 完成的数据回送给该请求；该事件的 `va` 字段记录的是 `400000081362708`（发射端在此把 PA 写进了 `va` 字段，这是原始字段值，不做改写）。紧接着 `event_id=15` 的 `lq_complete` 让 LQ 条目 `lq_idx=44911` 完成，`request_id=415526`，`pa=400000081362708`。`event_id=16` 的 `taint_reg` 是“存储→CPU”的边界事件：它把目的寄存器 `arch_reg=4` / `phys_reg=42` 从 `clean` 改成 `tainted`，tick=238085367975。其输入是 `lq_complete` 返回的污染数据，内部变化是污染集登记（before=clean、after=tainted），输出是一个被标记为受污染的物理寄存器 42；后续任何读该物理寄存器的指令都被纳入污染传播。至此错误已经从存储层（TLB/cache）越过了架构寄存器边界。

### 2.7 最终传播终局

L5 的真实终局是 `event_id=20` 的 `errant_commit`：parent_event_id=16，tick=238085368641，`dyn_inst_seq=415526`，`commit_seq=293614`，`pc=0xffffffc0087b27ac`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。它是“被污染寄存器 42 在提交点被消费并提交”的真实证据，不是生命周期事件。它没有被更早消除，原因是：L2 的 `tlb_translate_result` 明确 `contained=0`（有效 PA 改变但不含住），L3 的 cache/MSHR 没有架构可见性检查，L4 的 RAS `squash_masked` 在本 seed 中完全没有出现（kinds 直方图里没有该 kind，见第 5 章），因此提交是第一次“真实检测”，而此时错误已成架构可见事实。`chain_end`（event_id=975，tick=238090618719，`contained=1`、`outcome=errant_commit_seen`、`corr=none`）只是退出回调发射的流收口记录，按口径**不是** L5，也不能用它替代 event 20。

### 2.8 从传播终局到系统表现

传播终局是 `errant_commit`（event 20，tick 238085368641），`provable_to=L5`，权威报告 `terminal=full`。运行结局（oracle）是 `Crash`：`run.out` 明确写下 `CHAOS_DETECT: layer=None contained=0 tick=238085368641 ptag=1 reason=errant_commit`，并在末尾写下 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`，`run.err` 同时有 `warn: Kernel panic in simulated kernel` 与 `Dumping kernel dmesg buffer`。注入 tick=238085259417，终局 tick=238085368641，传播延迟为 109224 ticks（约 109224/1e12 s 的模拟时间，周期 714970749→714971077，相差 328 个 CPU cycle）。因果链是：错误 PFN→错误 PA→L1D 错误行→污染寄存器 42→提交点消费→内核 panic；这是“真实错误提交”与“运行崩溃”同时成立的情形，不是受控 Timeout，也不是 Masked/Contained。需要额外说明：run 根 `manifest.json` 的 `timeout_triggered=true` 属于该 run 根（其 `seed` 字段=3、artifacts 尺寸对应最后一个 seed），不能用它覆盖本 seed `run.out` 中真实发生的 panic；本 seed 的终止事实以 `run.out`/`run.err` 为准。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 13 号 DTLB 表项（VPN=`ffffff8001362`，PFN=`81362`） | PFN→`800400000081362`（bit46、bit59 翻转） | 命中读出错误 PFN | 故障源进入真实查找路径 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 页内偏移 `0x708` | PA `81362708`→`400000081362708`，`contained=0` | 有效 PA `0x400000081362708` | 翻译层未含住，错误 PA 被交付 |
| LQ（L3） | 翻译结果（`request_id=415526`） | `lq_read` 取出 `lq_idx=44911` | 发起 L1D 访问 | 污点进入 LQ |
| L1D（L3） | PA=`0x400000081362708`/`0x400000081362700` | 两次访问均 `miss` | 转 MSHR | 错误地址进入 cache 层级 |
| MSHR（L3） | 两个错误行 | 分配 `mshr_id=1`、`mshr_id=2` | 等待填充/响应 | 错误行被跟踪取数 |
| L1D→LSU（L4） | MSHR 完成 | `resp` 返回数据 | `lq_complete` 完成 LQ 条目 | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | `lq_complete` 的数据 | `arch_reg=4/phys_reg=42` clean→tainted | 污染寄存器 42 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染寄存器 42 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以这样概括：tick=238085259417 的一次 TLB 命中把 PFN 的两个 bit（第 46、59 位）同时翻转，其中第 59 位在 64 位左移 12 位时被截掉、对有效 PA 毫无影响，而第 46 位把有效 PA 从 `0x81362708` 推到 `0x400000081362708`；L2 的 `tlb_translate_result` 如实记录了 `effective_pa_changed` 却给出 `contained=0`，于是 `lq_read` 带着这个错误 PA 进入 L1D，两次相邻子访问（`0x...708` 与 `0x...700`）都以 miss 分配 MSHR（`mshr_id=1`、`mshr_id=2`），`resp` 把数据回送后 `lq_complete` 完成 `lq_idx=44911`，`taint_reg` 在 tick=238085367975 把 `arch_reg=4/phys_reg=42` 从 clean 改记为 tainted；随后的消费在 tick=238085368641 形成 `errant_commit`（`commit_seq=293614`，`pc=0xffffffc0087b27ac`），此时距注入 109224 ticks，运行随即 KERNEL PANIC，结局为 Crash——传播链完整走到 L5，且没有在 L2/L4 被任何显式机制含住或 squash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`run.out` 的 `CHAOS_LSU_TRIGGER` 记录 `attempted=110149 eligible=110149 injected=1`，`armtlb_injections.log` 只有一条真实注入，`stats.txt` 的 `board.chaos_armtlb.numFaultsInjected=1`，流内 `inj` 事件也只有 1 条：三方（触发器计数、stats、事件流）一致，均为 1。故障值确实被下游读取：`event_id=1` 的 `tlb_lookup` 命中的 `post_lookup` 读出故障 PFN，`event_id=2/3` 把它转成有效 PA `0x400000081362708`，`event_id=5/8` 的 L1D 访问直接使用该 PA，`event_id=16` 的 `taint_reg` 再把结果写入寄存器。因此本 seed 是严格意义上的 activated，而不是 injected-not-activated；注入后没有发生“正确值恰好等于卡死值”的无效情形（该概念属 F5，本 seed 为 F2）。

### 3.2 故障传播类型

这是**地址型（错误物理地址）**传播，不是数据位翻转直接进入数据通路：错误首先表现为 PFN→PA 的错误，请求的身份（`request_id=415526`、VA、页内偏移）保持正确，但物理落点从 `0x81362708` 变成 `0x400000081362708`。它不属于权限型（`ap=0` 未变）、控制状态型（没有 PC/分支状态被改）或时间型（没有延迟注入）；也没有出现 wrong cache line/错误请求路由的独立证据——cache_line 与 PA 一致，request_id 在祖先上保持 415526。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（tick=238085259417）：它携带 `field=effective_pa_changed`、`contained=0`、`outcome=NoFault`。在这一刻，翻译层已经知道有效 PA 改变却没有含住，且把 `0x400000081362708` 交给 LSU；此后当前结构（无 L2 含住、无访存地址校验）已无法把该请求拉回正确 PA。紧随其后的 `event_id=4`（`lq_read`）是错误进入 LQ 的第一刻，可视为同一不可逆点的执行落点；但“还能否被撤销”的分界在 event 3，而不是 event 5 的 cache 访问。

### 3.4 检测与掩蔽机制

本 seed 可动用的机制与实际表现如下：TLB 翻译结果可以检测 PA 变化（确实检测到了，`field=effective_pa_changed`），但本 seed 选择 `contained=0`，所以 L2 检测未转成含住；L1D/MSHR 没有地址正确性检查，只按给定 PA 取数；L4 的 RAS 重放/squash 机制在同一链的祖先上没有出现（event 20 的 parent 是 event 16，不是任何 `squash_masked`）；提交点的 `errant_commit` 是第一次“真实暴露”，但暴露本身不能撤回已经提交的架构状态。观察到的检测盲区是：**翻译层能看见 PA 改变却不阻断，而后续层级只对“是否命中/是否重放”负责，不对“PA 是否被故障改写”负责**。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 20，`contained=0`、`outcome=errant_commit`、`detection_layer=L5`），并且运行以 KERNEL PANIC 结束，所以这不是 Masked，也不是 Detected/Contained；权威报告把 `terminal` 判为 `full`。它同样**不应**被轻率称为 SDC：本实验没有应用级输出 oracle，无法证明错误结果被外部观测为“静默的错误数据”；现有可证事实只是“错误值到达架构提交点并使内核崩溃”，因此按 Crash/DUE 归类更符合证据。若未来补充应用级输出比对，才可能把“错误提交但未崩溃”的样本升级为 SDC 证据；本 seed 的最终数据正确性无法判定。

### 3.6 与同 RunID 其他 seed 的关系

同 RunID 的另外两个 seed 只作事实对照：seed2 的注入 VA=`0xffffffc009483960`、PFN `0x81d75→0x800000000081d77`（bit1、bit59），有效 PA `0x81d75960→0x81d77960`，最终在 L4 以 `squash_masked`（event 68）含住、L5=N/A；seed3 的 VA=`0xffffffc009483950`、PFN `0x81d75→0x20200000081d75`（bit45、bit53），有效 PA `0x81d75950→0x200000081d75950`，走 store 路径（`sq_execute`/`sq_writeback`）后 `errant_commit`（event 96），运行结局 Timeout。三者的注入站点同为 `arm_tlb_lookup_hit`，但 VA、mask、地址变化、终局与运行结局均不同；本文件只使用 seed1 自己的事实，没有把 seed2/seed3 的字段搬进本链。

## 4. 完整主链事件表

下表与第 2 章同序（`0→1→2→3→4→5→6→7→8→9→10→14→15→16→20`），每一行都是上一行的直接 child（`parent_event_id` 指向前一行）。`mask` 只在 `inj` 行给出（来自 `armtlb_injections.log`）；流内不存在独立的 mask 字段，其余行一律 `—`。`layer` 用观察层语义：`squash_masked` 记 L4、`errant_commit` 记 L5、`chain_end` 不占层。本链只有 15 个事件，无需折叠；不存在被折叠掉的 `consumer` 连续段。

<!-- witness=20 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '14', '15', '16', '20'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 800400000081362 | 81362 | 800400000081362 | 0x800400000000000 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=415526 的地址翻译即将使用它 | 被改写后的 PFN=800400000081362（VA=ffffff8001362708） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 238085259417 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 800400000081362 | 81362 | 800400000081362 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=800400000081362;ap=0;mtype=2;page_size=1000;pa=400000081362708 | — | — | — | — | DTLB 命中 entry_index=13（way=-1），读取 pfn 字段 | 命中读出 pfn=800400000081362，AP=0，page_size=1000，PA=400000081362708 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 238085259417 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | 81362 | 800400000081362 | 81362 | 800400000081362 | — | 81362708 | 400000081362708 | — | — | — | — | lookup 得到的 PFN=81362 | PFN 记录为 800400000081362，翻译 PA=400000081362708 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 238085259417 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | — | — | 81362708 | 400000081362708 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=800400000081362;ap=0;mtype=2;page_size=1000;pa=400000081362708 | 0 | — | NoFault | — | PFN=81362 与页内偏移组合 | 有效 PA 81362708→400000081362708；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 238085259417 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=44911 的 load 请求（VA=ffffff8001362708） | request_id=415526 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 6 | 5 | 4 | 238085259417 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=415526 访问 L1D（PA=400000081362708） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 7 | 6 | 5 | 238085259417 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=400000081362708 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 8 | 7 | 6 | 238085259417 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 400000081362708 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=400000081362708 | mshr_id=1 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 9 | 8 | 7 | 238085259750 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 400000081362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=415526 访问 L1D（PA=400000081362700） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 10 | 9 | 8 | 238085259750 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 400000081362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=400000081362700 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 11 | 10 | 9 | 238085259750 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 400000081362700 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=400000081362700 | mshr_id=2 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 12 | 14 | 10 | 238085367975 | 108225 | resp | L4 | L1D→LSU | 1 | seq_primary | 415526 | 415526 | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=415526） | 响应数据返回（该事件 va 字段记录 PA=400000081362708） | L4：污染数据返回处理器 |
| 13 | 15 | 14 | 238085367975 | 0 | lq_complete | L4 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 400000081362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应数据 request_id=415526 | LQ 条目 lq_idx=44911 完成，PA=400000081362708 | L4：load 写回 LQ，错误值即将写寄存器 |
| 14 | 16 | 15 | 238085367975 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 415526 | 415526 | 400000081362708 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=415526） | arch_reg=4 / phys_reg=42：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 15 | 20 | 16 | 238085368641 | 666 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 415526 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=415526，commit_seq=293614） | contained=0，outcome=errant_commit，PC=ffffffc0087b27ac | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`before/after` 与 `state_before/state_after` 为原始字段值（十六进制不带 0x 前缀者按原始文本保留）；`PA/address` 取事件的 `pa` 字段；`resp` 事件在原始流中把 PA 写进了 `va` 字段，这是发射端字段用法，表内不做改写。`本事件输入/输出/传播意义` 三列由该行真实字段生成，空字段如实标 `—`。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 的 `fault_id=1` 共 1100 个事件，主链只占 15 个，其余 1085 个全部是同一故障的旁支，按结构分三类：

1. **`request_fork` 分叉（124 条）**：`event_id=4294967296`（parent=10）把请求 415526 分叉出新请求 415576（`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=0x400000081362000`、`shared_size=0x1000`）；其余 123 条 fork 的 parent 都是主链的 `taint_reg`（event 16），`tick` 从 238085373969 一直到 238090386951，目标 request_id 覆盖 415656、415700、415750、415876、…、424680。它们是在同一错误页内由污染寄存器/同页地址触发的再访问，每条 fork 都带出自己的 cache/MSHR/taint 小分支；这些分支**没有**再回到 event 20 的祖先路径上（event 20 的 parent 始终是 16），因此不构成终局 ancestry。
2. **污染消费（`consumer` 106 条，`taint_reg` 118 条）**：消费者覆盖 `arch_reg` 0/1/2/4 等寄存器，最早 tick=238085368974（event 21，parent=16，dyn_inst_seq=415530），最晚 tick=238090493178；它们说明被污染的 `phys_reg=42` 在其生命周期内被多次读取，但没有一个 consumer 成为 event 20 的祖先——event 20 直接消费的是 event 16 的污染登记，而不是某个 consumer 的再次派生。
3. **生命周期收口（`chain_end` 1 条）**：`event_id=975`，parent=974（payload 是旁支上的最后一个事件），tick=238090618719，`outcome=errant_commit_seen`、`contained=1`、`corr=none`。它是退出回调的流收口，不是检测事件；按口径既不占 L5，也不改变 event 20 的终局。

这些旁支对 SDC 诊断的影响是“扩散广度”而不是“终局身份”：它们证明同一个被污染寄存器在同页内被多次消费（106 个 consumer、125 个不同 request_id），支持“错误已扩散到多个消费者”的判断，但第 2 章的终局仍由 event 20 单独证明。旁支中没有出现任何 `squash_masked`：本 seed 的事件种类直方图为 `inj=1、tlb_lookup=1、tlb_pfn=1、tlb_translate_result=1、lq_read=1、cache_access=169、cache_return=169、mshr_alloc=88、request_fork=124、mshr_merge=81、resp=119、lq_complete=118、taint_reg=119、errant_commit=1、consumer=106、chain_end=1`，不含 `squash_masked`，因此不存在“被 squash 含住但未进入主链”的情况。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full`（权威 `chain_report.json`） |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=20，tick=238085368641，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Crash`（`run.out` `KERNEL PANIC under fault — exiting`；`run.err` 有 `Kernel panic in simulated kernel`） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=1`，与触发器/事件流一致） |
| conservation | `ok`（consumer_summary：emitted=18、suppressed=19、logical_total=37、conservation=ok、issues=[]） |
| count_contradiction | 无：`chain_report.event_count=1100` 与实际解析事件数 1100 相同；injected/stats/inj 事件均为 1 |
| campaign/checker 一致性 | 一致（报告由 checker 产出，`chain_valid=true`、`admitted=true`、`certified=true`，无 blocked） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，且 L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5`（权威证据表登记） |
| 判定 | **PASS** |

判定说明：`propagation terminal` 与 `run outcome` 是两件事——前者是“链走到 L5 的 `errant_commit`”，后者是“这次运行以 KERNEL PANIC 结束（Crash）”；本 seed 两者都成立，故不存在“Timeout 抹掉 L5”的问题。`chain_end`（event 975）没有被当作 L5，`contained=0` 的 event 20 也没有被任何旁支 `squash_masked` 替代。所有引用的事件都在本 seed 流内存在，父子关系与 tick 单调性均通过；未出现跨 seed 字段混用。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `6caf97eea470984bce9fb11068a7721618c1abfb626686617219f1aedfb2521e` | 37591 | 2026-10-25T19:33:50 |
| `chain_report.json` | `8307a11250c09a6f9787885b31f6738dc7c42a014ce4918adc24c6c5e3384490` | 17742 | 2026-10-25T19:33:51 |
| `run.out` | `8f1b06fab788211e5c9f07a4f8ce3f466f9bcb3dd330480d4103da14aee125fc` | 2268 | 2026-10-25T19:33:51 |
| `run.err` | `542053f2316e00845e96acb4d0f3b335c76fdc87803a2c67dc0821aa4c8332a0` | 1919 | 2026-10-25T19:33:51 |
| `stats.txt` | `63782326dc21ea434a3618d624dd488f15275268940fb27e8c2e493336f7c59b` | 388359 | 2026-10-25T19:33:50 |
| `armtlb_injections.log` | `fe2611ebe5abb28f7797480d97e0d434f9ef3371c0733505e3758d5296f6b493` | 399 | 2026-10-25T19:33:50 |
| manifest `manifest.json` | `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9` | 1778 | 2026-10-25T21:04:38 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | N/A（manifest 无该字段） | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T02-F2-W4 --prop_sample_run_id s1`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3 --cells T02-F2-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `runs/lsu/r6_c5_T02-F2-W4/T02-F2-W4/seed1` — **INTERRUPTED（无 .done/.exit_code 标记）**
- `runs/lsu/r6_c7_T02-F2-W4_s1/T02-F2-W4/seed1` — **OLD_BINARY_REFERENCE（manifest binary a9b2c236… ≠ 权威 e8052842…）**
- `runs/lsu/r6_c9_T02-F2-W4_s1/T02-F2-W4/seed1` — **EXACT_DUPLICATE（prop_evt 字节相同 + 报告语义相同 + run.out 去掉时间/pid/outdir 后相同）**
- `runs/lsu/r6_c9_T02-F2-W4_s2/T02-F2-W4/seed1` — **EXACT_DUPLICATE（同上）**
- `runs/lsu/r6_canary_T02-F2-W4/T02-F2-W4/seed1` — **INTERRUPTED（无 .done/.exit_code 标记）**
- `runs/lsu/r6_p1_T02-F2-W4/T02-F2-W4/seed1` — **INTERRUPTED（无 .done/.exit_code 标记）**
- `runs/lsu/r6_rejudge_T02-F2-W4_toolfix/T02-F2-W4/seed1` — **INTERRUPTED（无 .done/.exit_code 标记）**
- `runs/lsu/r6_w1_T02-F2-W4/T02-F2-W4/seed1` — **INTERRUPTED（无 .done/.exit_code 标记）**

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
