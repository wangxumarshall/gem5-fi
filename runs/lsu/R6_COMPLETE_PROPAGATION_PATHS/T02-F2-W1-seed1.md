# T02-F2-W1 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T02-F2-W1`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T02`）
- fault model：PPN 内同时翻转 2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`双比特翻转`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F2 — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier：`F2`；effective tier：`F2`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`）
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`；矩阵标签写 MiBench，但原始 run.out 的 `--readfile` 指向 `tlb_probe.rcS`；两者不一致处如实保留，不推断。
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T02-F2-W1 --prop_sample_run_id s1`
- source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/manifest.json`（SHA-256 `5e351346f7a7002e9f05f26b3e26bd0e4b8909d8ecf10402e2fd5c0a9b0ed04b`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`1`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：2631（与 `chain_report.event_count` 相同）
- fault_id 数量：3（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 的 `fault_id=1` 是代表故障（escape-first：三个故障中只有它到达 `full`）。终局见证是 `errant_commit`（event_id=26），其单祖先链为 `0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 26`，共 21 个事件。与 T02-F2-W4 的旧二进制样本相比，本 seed 的链在 MSHR 之后多出发射了的 `mshr_fill`/`cache_fill`/`mshr_free` 序列（两组），说明错误行被真实填入了 cache。

### 2.1 故障注入前的正常状态

注入目标是 DTLB 第 13 号 entry（`event_id=1` 的 `entry_index=13`、`way=-1`）。`state_before` 为 `vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`：VPN=`0xffffff8001362`，ASID=206，`valid=1`、`global=1`，权限 `ap=0`，4 KiB 页，正常 PFN=`0x81362`。触发翻译的是 `dyn_inst_seq=415526`（`request_id=415526`），VA=`0xffffff8001362708`；页内偏移 `0x708`，正常 PA=`(0x81362 << 12) | 0x708 = 0x81362708`，与 `state_before` 的 `pa` 一致。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=238085259417（cycle=714970749），`event_id=0`，`fault_id=1`，`request_id=415526`，`field=bit_flip`，FaultType=`bit_flip`，`corr=origin`。`armtlb_injections.log`：
`Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, old_pfn: 0x81362, new_pfn: 0xc5362, FaultType: bit_flip, Mask: 0x44000, effective: 1`。
`before=0x81362`、`after=0xc5362`，异或 `0x44000`：翻转 PFN 的第 14 位与第 18 位，两 bit 都落在有效宽度内（这是本 seed 与 W4 样本的关键差别之一：没有“高位被截断”的情况）。`new_pfn << 12 = 0xc5362000`，或上页内偏移 `0x708` 得 `0xc5362708`；因此两个 bit 都真实改变了有效 PA——第 14 位与第 18 位分别对应 PA 的第 26、30 位：`0x81362708 → 0xc5362708`。`event_id=3` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=81362708`、`after=c5362708`、`contained=0`、`outcome=NoFault`，即翻译层知道 PA 改变但不含住。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=238085259417）命中第 13 号 entry，`field=post_lookup`，`before=81362`、`after=c5362`，`state_after` 的 `pfn=c5362`、`pa=c5362708`。`event_id=2` 的 `tlb_pfn` 固化 `state_before=81362708`、`state_after=c5362708`、`pa=c5362708`。`event_id=3` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 238085259417 把错误有效 PA `0xc5362708` 交给 LSU；请求 VA 仍是 `0xffffff8001362708`。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径：`event_id=4` 的 `lq_read`（tick=238085259417，`lq_idx=44911`，`request_id=415526`，VA=`0xffffff8001362708`）把请求从 LQ 取出；本 fault 的祖先上没有 `lsq_push`/`mem_req`/`lsq_sendfrag`，因此这些字段为 N/A——可证事实止于 `lq_read` 带着错误 PA 进入 L1D 访问。L1D 访问（`event_id=5`、`event_id=8`）使用 `request_id=415526`，PA 分别为 `0xc5362708`、`0xc5362700`。

### 2.5 错误如何经过 cache 和 MSHR

第一次访问 `event_id=5`（`cache_access`，tick=238085259417，PA=`0xc5362708`）未命中（`event_id=6`，`field=miss`），分配 `mshr_id=1`（`event_id=7`，`cache_line=0xc5362708`，`state_after=mshr_allocated`）。第二次访问 `event_id=8`（tick=238085259750，PA=`0xc5362700`）同样未命中（`event_id=9`），分配 `mshr_id=2`（`event_id=10`，`cache_line=0xc5362700`，`state_after=mshr_allocated`）。随后真实发生了两组填充：`event_id=14` 的 `mshr_fill`（tick=238085318691，`mshr_id=2`，`fill_id=1`，`cache_line=0xc5362700`，`state_after=filled`）→ `event_id=15` 的 `cache_fill`（`fill_id=1`，`pa=c5362700`，`cache_line=c5362700`）→ `event_id=16` 的 `mshr_free`（`mshr_id=2`，`state_after=mshr_freed`）；紧接着 `event_id=17` 的 `mshr_fill`（tick=238085319357，`mshr_id=0`，`fill_id=2`，`cache_line=c5362700`）→ `event_id=18` 的 `cache_fill`（`fill_id=2`，`pa=c5362700`）→ `event_id=19` 的 `mshr_free`（`mshr_id=0`）。这两组填充的输入是错误 PA 对应的 MSHR 请求，内部变化是错误行在 L1D 中由 “miss” 变为 “filled”，输出是缓存行 `0xc5362700`；这使错误数据不仅被本次请求读取，还留在 cache 中供后续访问命中——是本 seed 比 W4 样本更“持久”的污染点。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、lq_complete、lq_read、mshr_alloc、mshr_fill、mshr_free、resp、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、lsq_push、mem_req、lsq_sendfrag、sq_execute、sq_writeback、sq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=20` 的 `resp`（tick=238085319690，`request_id=415526`，原始 `va` 字段记录 PA=`c5362708`）把数据回送；`event_id=21` 的 `lq_complete` 完成 `lq_idx=44911`（`pa=c5362708`）；`event_id=22` 的 `taint_reg` 把 `arch_reg=4` / `phys_reg=42` 从 `clean` 改成 `tainted`。输入是 cache/MSHR 返回的错误数据，内部变化是污染集登记，输出是污染寄存器 42。至此存储层的错误越过寄存器边界。

### 2.7 最终传播终局

L5 终局是 `event_id=26` 的 `errant_commit`：parent=22，tick=238085320689，`dyn_inst_seq=415526`，`commit_seq=293614`，`pc=0xffffffc0087b27ac`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除的原因：L2 `tlb_translate_result` 记录 `effective_pa_changed` 却 `contained=0`；L3 的 cache/MSHR 已把错误行填入并在本链上被命中（没有出现针对本故障的 squash 事件）；fault 1 的 11 条 `squash_masked` 全部在旁支上（本 seed 另有 13 条属于 fault 2），都不在本链祖先；提交点因此成为第一次真实暴露。`chain_end`（event_id=2295，parent=2016，tick=238693668732，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 26，tick 238085320689），`provable_to=L5`，`terminal=full`。运行结局 `Crash`：`run.out` 有 `CHAOS_DETECT: layer=None contained=0 tick=238085320689 ptag=1 reason=errant_commit` 与末尾 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 有内核 panic 告警。注入 tick=238085259417，终局 tick=238085320689，传播延迟 61272 ticks（cycle 714970749→714970933，184 个 CPU cycle）。因果链：错误 PFN→错误 PA `0xc5362708`→L1D 两次 miss→两组真实填充→污染寄存器 42→提交点消费→panic。本 seed 的 manifest 是逐 seed manifest（`r6_n8_T02-F2-W1_s1/manifest.json`，`status=FINISHED`、`exit_code=null`、无 `done_flag`），终止事实以 `run.out`/`run.err` 为准。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 13 号 DTLB 表项（PFN=`81362`） | PFN→`c5362`（bit14、bit18） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x708` | PA `81362708`→`c5362708`，`contained=0` | 有效 PA | 翻译层未含住 |
| LQ（L3） | 翻译结果 | `lq_read` 取出 `lq_idx=44911` | L1D 访问 | 污点进入 LQ |
| L1D（L3） | PA `c5362708`/`c5362700` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | `mshr_id=1`、`mshr_id=2` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | `mshr_fill`/`cache_fill`/`mshr_free` 两组 | 错误行留在 cache | 错误被持久化到缓存 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `lq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | load 数据 | `arch_reg=4/phys_reg=42` clean→tainted | 污染寄存器 42 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染寄存器 42 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=238085259417 的第 13 号 DTLB 命中把 PFN 的第 14、18 位同时翻转（两 bit 均在有效宽度内），有效 PA 由 `0x81362708` 变为 `0xc5362708`；翻译层记录 `effective_pa_changed` 却 `contained=0`，`lq_read`（`lq_idx=44911`）带着错误 PA 进入 L1D，两次相邻访问（`0xc5362708`、`0xc5362700`）均 miss 并分配 `mshr_id=1/2`，随后两组 `mshr_fill`→`cache_fill`→`mshr_free`（fill_id=1/2，tick=238085318691/238085319357）把错误行真实填入缓存；`resp` 与 `lq_complete` 完成请求，`taint_reg` 在 tick=238085319690 把 `arch_reg=4/phys_reg=42` 从 clean 改为 tainted，最终在 tick=238085320689 由 `errant_commit`（`commit_seq=293614`）收口，距注入 61272 ticks，运行随即内核 panic，结局 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER`：`attempted=248635 eligible=248635 injected=3`；`stats.txt`：`numFaultsInjected=3`；流内 `inj` 3 条；权威报告 3 个 fault：三方一致。代表故障 fault 1 的值被真实读取（`tlb_lookup`）并消费（`lq_read`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此是 activated。该 seed 的另外两个故障分别是 fault 2（`detected_contained`，路径 `2026…2119`）与 fault 3（`provable_to_L4_then_unknown`，路径 `2234…2247`），不在本链。

### 3.2 故障传播类型

**地址型**（错误物理地址）传播：VA、页内偏移、权限都不变，PFN 被改成同一 4 KiB 页内的错误值（`0xc5362`）。两个翻转位（14、18）都改变有效 PA（PA 位 26、30），因此没有“只改存储值不改 PA”的情况。没有控制状态、时序或权限型证据；错误请求的路由（`request_id=415526`）保持一致。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（`contained=0`）：翻译层记录 PA 改变却放行，此后本请求无法回到正确 PA。第二个、对后续请求也生效的不可逆点是 `event_id=15`/`event_id=18` 的 `cache_fill`：错误行被真实写入 L1D，后续对同一行（`0xc5362700`）的访问可以命中错误数据，污染从“一次请求”升级为“缓存内容”。若只允许一个答案，取 event 3（本请求的不可逆点），并在 2.5 中已说明 event 15/18 的升级作用。

### 3.4 检测与掩蔽机制

可检测的机制：翻译层（检测到 `effective_pa_changed`，但 `contained=0`）；L1D/MSHR（无地址校验）；L4 的 RAS 重放（本链未触发；fault 1 的 11 条 squash 都在旁支，另有 13 条属 fault 2）；提交点（`errant_commit`，首次暴露）。实际结果是未掩蔽：本链没有 `squash_masked`，错误行又已填入 cache，所以盲区是“翻译层可见但不阻断 + cache 无地址校验 + 本请求未触发重放”。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 26，`contained=0`、`detection_layer=L5`），且运行以 KERNEL PANIC 结束；权威 `terminal=full`。因此不是 Masked/Detected-Contained。仍不应轻率称为 SDC：本实验没有应用级输出 oracle，只能证明“错误值到达提交点并使内核崩溃”，不能证明“外部可见且未被检测的错误数据”。最终数据正确性无法判定；按证据归类为 Crash/DUE。

### 3.6 与同 RunID 其他 seed 的关系

同 RunID：seed2 注入 VA=`0xffffffc009483960`、PFN `81d75→c1d74`（mask `0x40001`，bit0、bit18），有效 PA `81d75960→c1d74960`，终局是 L4 `squash_masked` event 68 含住、L5=N/A，结局 Crash；seed3 注入 VA=`0xffffffc009483950`、PFN `81d75→95d75`（mask `0x14000`，bit14、bit16），有效 PA `81d75950→95d75950`，走 store 路径并 `errant_commit` event 97，结局 Crash。本 seed 的地址、掩码、两 bit 位置与终局都不同；只共享注入站点。本文件没有引用它们的任何字段。

## 4. 完整主链事件表

下表按 event 26 的祖先顺序排列（`0→1→2→3→4→5→6→7→8→9→10→14→15→16→17→18→19→20→21→22→26`）。`mask` 只在 `inj` 行给出（`0x44000`，来自注入日志；注意注入日志还带 `effective: 1`，表示该 mask 实际改变了地址翻译）。主链 21 个事件，无需折叠任何连续 `consumer` 段；本链本身不含 `consumer`。

<!-- witness=26 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '14', '15', '16', '17', '18', '19', '20', '21', '22', '26'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | c5362 | 81362 | c5362 | 0x44000 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=415526 的地址翻译即将使用它 | 被改写后的 PFN=c5362（VA=ffffff8001362708） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 238085259417 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | c5362 | 81362 | c5362 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=c5362;ap=0;mtype=2;page_size=1000;pa=c5362708 | — | — | — | — | DTLB 命中 entry_index=13（way=-1），读取 pfn 字段 | 命中读出 pfn=c5362，AP=0，page_size=1000，PA=c5362708 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 238085259417 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | c5362708 | — | — | 81362 | c5362 | 81362 | c5362 | — | 81362708 | c5362708 | — | — | — | — | lookup 得到的 PFN=81362 | PFN 记录为 c5362，翻译 PA=c5362708 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 238085259417 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | c5362708 | — | — | — | — | 81362708 | c5362708 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=c5362;ap=0;mtype=2;page_size=1000;pa=c5362708 | 0 | — | NoFault | — | PFN=81362 与页内偏移组合 | 有效 PA 81362708→c5362708；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 238085259417 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=44911 的 load 请求（VA=ffffff8001362708） | request_id=415526 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 6 | 5 | 4 | 238085259417 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | c5362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=415526 访问 L1D（PA=c5362708） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 7 | 6 | 5 | 238085259417 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | c5362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=c5362708 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 8 | 7 | 6 | 238085259417 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | c5362708 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=c5362708 | mshr_id=1 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 9 | 8 | 7 | 238085259750 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | c5362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=415526 访问 L1D（PA=c5362700） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 10 | 9 | 8 | 238085259750 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | c5362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=c5362700 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 11 | 10 | 9 | 238085259750 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | c5362700 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=c5362700 | mshr_id=2 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 12 | 14 | 10 | 238085318691 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | c5362700 | 2 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=2 的数据返回（fill_id=1） | state_after=filled，cache_line=c5362700 | L3：MSHR 完成填充 |
| 13 | 15 | 14 | 238085318691 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | c5362700 | c5362700 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=1 的填充数据 | cache_line=c5362700 进入 L1D | L3：错误行进入 cache |
| 14 | 16 | 15 | 238085318691 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | c5362700 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=2 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 15 | 17 | 16 | 238085319357 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | c5362700 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=2） | state_after=filled，cache_line=c5362700 | L3：MSHR 完成填充 |
| 16 | 18 | 17 | 238085319357 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | c5362700 | c5362700 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=2 的填充数据 | cache_line=c5362700 进入 L1D | L3：错误行进入 cache |
| 17 | 19 | 18 | 238085319357 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | c5362700 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 18 | 20 | 19 | 238085319690 | 333 | resp | L4 | L1D→LSU | 1 | seq_primary | 415526 | 415526 | c5362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=415526） | 响应数据返回（该事件 va 字段记录 PA=c5362708） | L4：污染数据返回处理器 |
| 19 | 21 | 20 | 238085319690 | 0 | lq_complete | L4 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | c5362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应数据 request_id=415526 | LQ 条目 lq_idx=44911 完成，PA=c5362708 | L4：load 写回 LQ，错误值即将写寄存器 |
| 20 | 22 | 21 | 238085319690 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 415526 | 415526 | c5362708 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=415526） | arch_reg=4 / phys_reg=42：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 21 | 26 | 22 | 238085320689 | 999 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 415526 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=415526，commit_seq=293614） | contained=0，outcome=errant_commit，PC=ffffffc0087b27ac | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`mshr_fill` 的 `state_after=filled`、`cache_fill` 的 `pa/cache_line`、`mshr_free` 的 `state_after=mshr_freed` 均照原始字段填写；`resp` 事件的 `va` 字段保存 PA，表中不改写。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 2631 个事件、3 个真实故障。fault 1 有 2323 个事件，主链 21 个，其余 2302 个是旁支。

1. **请求分叉（`request_fork` 296 条）**：1 条挂在主链 `mshr_alloc`（event 10）上（`event_id=4294967296`，new_request_id=415576，`shared_addr=0xc5362000`）；其余 295 条挂在主链 `taint_reg`（event 22）上，最晚 `event_id=4294967591`（parent=22，tick=238099691637，new_request_id=445846）。它们都是同一错误页/同一污染寄存器的再访问，没有成为 event 26 的祖先。
2. **污染消费（`consumer` 535 条、`taint_reg` 272 条）**：consumer 覆盖 `arch_reg` 0–9 等，最早 `event_id=27`（parent=22，tick=238085320689，`phys_reg=42`），最晚 `event_id=1884`（parent=172，tick=238098636360，`phys_reg=553`）。它们说明污染寄存器在生命周期内被大量读取，但没有成为 event 26 的祖先。
3. **含住旁支（`squash_masked` 11 条）**：最早 `event_id=258`（parent=250，tick=238085615727，VA=`0xffffff8001362708`，PA=`0xc5362708`），最晚 `event_id=2016`（parent=1941，tick=238099645684，VA=`0xffffff8001362708`，PA=`0xc5362708`），全部 `contained=1`、`outcome=masked`、`reason=squash_replay`。它们说明同一错误地址的其它 load 在 L4 被重放含住（fault 1 共 11 条；本 seed 另有 13 条 `squash_masked` 属于 fault 2，共 24 条）；但本链的 event 26 是 `errant_commit`，含住旁支不能把它改写成 contained。
4. **填充旁支（旁支各 14 组）**：fault 1 的主链另有 2 组（event 14–16、17–19，见 2.5）；旁支 14 组在其它请求上（最早 `event_id=101`，tick=238085383293，request 415692；最晚 `event_id=1084`，tick=238087953054，request 426885）。整个 seed 的 `mshr_fill` 共 24 条，其中 8 条属于 fault 2/3。它们进一步说明错误页被大量填充；不并入本链。
5. **生命周期收口（1 条）**：`event_id=2295`（parent=2016，tick=238693668732，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）。
6. **其它故障**：fault 2（`detected_contained`，路径 `2026,2027,2028,2030,2072,2119`）与 fault 3（`provable_to_L4_then_unknown`，路径 `2234,2235,2236,2238,2247`）各有自己的注入点和地址，不属于本链。

这些旁支对 SDC 诊断的影响：它们显示错误地址被反复访问（296 fork、535 consumer、14 组填充），但本链的终局仍是 event 26；旁支中的 11 次 squash 不能覆盖主链的 `errant_commit`，反而说明同一错误在不同地址/时刻既有含住也有逃逸。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=26，tick=238085320689，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Crash`（`run.out` KERNEL PANIC；`run.err` 内核 panic 告警） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=3`，与触发器 injected=3、inj 事件 3 条一致） |
| conservation | `ok`（consumer_summary：emitted=259、suppressed=1215、logical_total=1474、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=2631` 与实际解析事件数 2631 相同；injected/stats/inj 均为 3 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


判定说明：传播终局（event 26 错误提交）与运行结局（Crash）分别陈述；`chain_end`（2295）未被当作 L5；旁支 11 条 `squash_masked` 未被用来改写终局。15 项一致性检查全部通过：事件存在、父子与 tick 单调、取值来自本 seed、终局与权威报告一致（`full`/L5）、L5 见证真实。
## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `09123a77e98c32503b479e026ff8dc43ad0eb3aefa4de349ae4010003f9a212c` | 101366 | 2026-10-27T13:15:27 |
| `chain_report.json` | `85c328179d1847d316c81aa30d1c42f12592caf154d7c514cf1a14bf867e3def` | 222415 | 2026-10-27T13:15:28 |
| `run.out` | `ecd786ebbd64e990c68c99c0473c490349284258b374111b82bd96fb86854cf8` | 4855 | 2026-10-27T13:15:27 |
| `run.err` | `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d` | 1912 | 2026-10-27T13:15:27 |
| `stats.txt` | `8b5284423283c9ee642c6443f2818f4eec633b0f092437b8e2e4ac72bedebef6` | 393496 | 2026-10-27T13:15:27 |
| `armtlb_injections.log` | `bdde1b34770ad67fc5db544b62bab6e9017401be29680ba8375a7cfdbd7bf141` | 777 | 2026-10-27T13:15:27 |
| manifest `manifest.json` | `5e351346f7a7002e9f05f26b3e26bd0e4b8909d8ecf10402e2fd5c0a9b0ed04b` | 1438 | 2026-10-27T13:15:29 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T02-F2-W1 --prop_sample_run_id s1`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1 --cells T02-F2-W1 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `runs/lsu/r6_n8_T02-F2-W1_s1.sha8a229009/T02-F2-W1/seed1` — **OLD_BINARY_REFERENCE（manifest binary 8a229009… ≠ 权威 20fda699…）**

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
