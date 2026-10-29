# T02-F2-W1 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T02-F2-W1`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T02`）
- fault model：PPN 内同时翻转 2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`双比特翻转`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F2 — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier：`F2`；effective tier：`F2`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`）
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`；矩阵标签写 MiBench，但原始 run.out 的 `--readfile` 指向 `tlb_probe.rcS`；两者不一致处如实保留，不推断。
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s2/T02-F2-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T02-F2-W1 --prop_sample_run_id s2`
- source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s2/T02-F2-W1/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s2/manifest.json`（SHA-256 `a7048f8b298cc7b1863bd7f1ec0b740f47f39bd6987812f776d9259335d8ddfe`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`2`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：9450（与 `chain_report.event_count` 相同）
- fault_id 数量：4（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 的权威判定是显式含住。本章按含住见证 `squash_masked`（event_id=68）的单祖先链重建：`0 → 1 → 2 → 3 → 4 → 32 → 33 → 34 → 35 → 36 → 68`，共 11 个事件。event 1797 与 event 83 都不在本链祖先上：前者是同一 fault 在另一 VA 上更晚的同类 squash，按权威口径不得替代 event 68；后者是 event 68 的直接 child，身份见 2.7。本 seed 有 4 个真实故障，本章只讲代表故障 fault 1。

### 2.1 故障注入前的正常状态

注入目标是 DTLB 第 21 号 entry（`event_id=1`，`entry_index=21`、`way=-1`）。`state_before` 为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960`：VPN=`0xffffffc009483`，ASID=206，有效且 global，`ap=0`，4 KiB 页，正常 PFN=`0x81d75`。触发翻译的指令 `dyn_inst_seq=393897`（`request_id=393897`）使用 VA=`0xffffffc009483960`；偏移 `0x960`，正常 PA=`0x81d75960`，与 `state_before` 一致。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=238083182163（cycle=714964511），`event_id=0`，`fault_id=1`，`request_id=393897`，`field=bit_flip`，FaultType=`bit_flip`，`corr=origin`。注入日志：
`Tick: 238083182163, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483960, old_pfn: 0x81d75, new_pfn: 0xc1d74, FaultType: bit_flip, Mask: 0x40001, effective: 1`。
`before=0x81d75`、`after=0xc1d74`，异或 `0x40001`：翻转 PFN 的第 0 位与第 18 位，且注入日志标注 `effective: 1`（说明该掩码实际改变了地址翻译）。`new_pfn << 12 = 0xc1d74000`，或上偏移 `0x960` 得有效 PA `0xc1d74960`；两个翻转位分别对应 PA 的第 12 位与第 30 位：`0x81d75960 → 0xc1d74960`。`event_id=3` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=81d75960`、`after=c1d74960`、`contained=0`、`outcome=NoFault`——翻译层没有含住。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=238083182163）命中第 21 号 entry，`field=post_lookup`，`before=81d75`、`after=c1d74`，`state_after` 的 `pfn=c1d74`、`pa=c1d74960`。`event_id=2` 的 `tlb_pfn` 固化 `state_before=81d75960`、`state_after=c1d74960`、`pa=c1d74960`。`event_id=3` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason：TLB 在 tick 238083182163 把错误有效 PA `0xc1d74960` 交给 LSU，请求 VA 保持 `0xffffffc009483960`。与同 RunID seed1 的差别是：本 seed 的含住不在 L2，也不在提交点，而在 L4。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径，且流内发射了完整的 LSQ 中间步骤：`event_id=4` 的 `lq_read`（tick=238083182163，`lq_idx=41835`，`request_id=393897`，VA=`0xffffffc009483960`）；`event_id=32` 的 `lsq_push`（tick=238083183495，`pc=0xffffffc0087b27c8`、`opcode=ldp_uop`、`lq_idx=41835`、`sq_idx=-1`、`field=load`）；`event_id=33` 的 `mem_req`（`request_id=393897`）；`event_id=34` 的 `lsq_sendfrag`（同 request，`field=load`）；`event_id=35` 的 `tlb_translate`；`event_id=36` 的 `lq_read`（`lq_idx=41835`、`request_id=393897`）。输入是 2.3 的错误 PA；内部变化是请求在 LQ 中登记、成形、分片并再次翻译；输出是一条已被送入 L1D/重放路径的 load。store 侧字段（`sq_*`）在本链祖先上不存在，为 N/A。

### 2.5 错误如何经过 cache 和 MSHR

本 fault 的主链在 `lq_read`（event 36）之后直接到 `squash_masked`（event 68），中间没有本请求的 cache_access/cache_return/MSHR 事件；因此不能为它编造 L1D 命中/未命中或 MSHR 分配。旁支上确有 64 组 `mshr_fill`/`cache_fill`/`mshr_free`（见第 5 章），但它们属于同故障的其它请求，不在 event 68 的祖先上；本链对 L3 的可证事实是“请求被分片/翻译后收到污染响应”，而不是“错误行进入 cache 后被检出”。

本链出现的 kind 集合为 `inj、lq_read、lsq_push、lsq_sendfrag、mem_req、squash_masked、tlb_lookup、tlb_pfn、tlb_translate、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mshr_fill、cache_fill、mshr_free、sq_execute、sq_writeback、sq_complete、lq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

本 fault 的祖先上没有 `taint_reg`：含住发生在“污染值被写回寄存器之前”。`event_id=68` 的 `squash_masked`（tick=238083244768）是这层边界的具体事件：`field=squashed_load`、`detection_layer=L4`、`contained=1`、`outcome=masked`、`corr=addr_fallback`、`containment_layer=L4`、`containment_reason=squash_replay`，`dyn_inst_seq=393912`，VA=`0xffffffc0094839e0`，PA=`0xc1d749e0`。它接收的是使用错误 PA 的 load 响应，内部变化是 squash（丢弃并重放），输出是 `masked`。因此“污染返回处理器状态”在本链上表现为“在写寄存器前被拒绝”，而不是“寄存器被污染后再清除”。

### 2.7 最终传播终局

权威终局是含住：权威 `chain_report.json` 给出 `terminal=detected_contained`（该报告未内嵌 `containment.metrics` 块）；按 canonical 口径与 `../README.md` 的“5 个 L4 含住 seed”表，权威见证是 `squash_masked` event_id=68，parent=36，tick=238083244768，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_layer=L4`，`containment_reason=squash_replay`。`run.out` 的第一条 `CHAOS_DETECT` 也写 `layer=Hardware RAS contained=1 tick=238083244768 ptag=1 reason=squash_replay`。停止它的是 L4 的 RAS 重放：收到污染响应的 load 被 squash 并重放，不进入架构提交。L5 在本链上为 N/A（祖先无 `errant_commit`）。event 1797（更晚、不同 VA 的同类 squash）不得替代 event 68。

同样必须交代 event 83：它是 event 68 的直接 child（`errant_commit`，tick=238083249096，`dyn_inst_seq=393846`，`commit_seq=273130`，`pc=0xffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`）。按 checker 的 `_errant_commit_escape` 语义，它是一条悬空 `errant_commit`：其祖先的连续有序前缀只到 L0..L3，不能收口 L0→L5，故不改变 L4 含住终局，也不被用来构造 L5。本 seed 与 T02-F2-W4 seed2 恰好共享同一确定性注入点/时序（tick=238083182163、含住 tick=238083244768、event 68 的 VA=`0xffffffc0094839e0`），但两者故障值不同（本 seed 的 PA 为 `0xc1d749e0`，W4 seed2 为 `0x81d779e0`），本文件没有把 W4 的字段搬进本链。

### 2.8 从传播终局到系统表现

传播终局是 L4 `squash_masked`（event 68，tick=238083244768），含住层 L4，L5=N/A。运行结局是 `Crash`：`run.out` 在含住记录后紧接着写 `CHAOS_DETECT: layer=None contained=0 tick=238083249096 ptag=1 reason=errant_commit`（即 event 83），并在末尾写 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 有内核 panic 告警。必须区分：本 fault 的传播在 L4 被含住，**但运行仍然崩溃**；崩溃的成因（fault 2/3/4，或 event 83 这类悬空提交）不由本链证明，不能把崩溃归因给 event 68。注入 tick=238083182163，含住 tick=238083244768，延迟 62605 ticks（cycle 714964511→714964699，188 个 CPU cycle）。若只看本 fault，架构上没有出现可见错误结果；run-level 的 Crash 是独立事实。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 21 号 DTLB 表项（PFN=`81d75`） | PFN→`c1d74`（bit0、bit18） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x960` | PA `81d75960`→`c1d74960`，`contained=0` | 有效 PA | 翻译层未含住 |
| LQ（L3） | 翻译结果（`request_id=393897`） | `lq_read`/`lsq_push`/`mem_req`/`lsq_sendfrag`/`tlb_translate`/`lq_read` | 携带错误 PA 的 load | 污点穿过 LSQ |
| RAS/ROB 重放（L4） | 使用错误 PA 的 load（`dyn_inst_seq=393912`） | `squashed_load`，`contained=1` | `masked`，重放 | 含住点 |
| L5 | — | — | — | N/A（祖先无 `errant_commit`；event 83 悬空） |

整条链可以概括为：tick=238083182163 的第 21 号 DTLB 命中把 PFN 的第 0、18 位同时翻转（`effective: 1`），有效 PA 由 `0x81d75960` 变为 `0xc1d74960`；L2 的 `tlb_translate_result` 记录 `effective_pa_changed` 却 `contained=0`，请求经 `lq_read`→`lsq_push`（`ldp_uop`，`lq_idx=41835`）→`mem_req`→`lsq_sendfrag`→`tlb_translate`→`lq_read` 带着错误 PA 前进，最终在 tick=238083244768 被 L4 的 `squash_masked`（event 68，`contained=1`、`outcome=masked`、`reason=squash_replay`）重放丢弃，架构状态未被污染；L5 在祖先上为 N/A，event 83 是悬空 `errant_commit`，不构成本链 L5。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER`：`attempted=411962 eligible=411962 injected=4`；`stats.txt`：`numFaultsInjected=4`；流内 `inj` 4 条；权威报告 4 个 fault：三方一致。代表故障 fault 1 的值被真实读取（`tlb_lookup`）并消费（`event 33–36` 带着错误 PA 走完 LSQ，event 68 收到污染响应并 squash），因此是 activated；其“消费”以触发重放告终。

### 3.2 故障传播类型

**地址型**（错误物理地址）：VA、偏移、权限不变，PFN 被改写为 `0xc1d74`；两个翻转位（0、18）都改变有效 PA（PA 位 12、30）。没有控制状态/时序/权限型证据；请求身份 `request_id=393897` 在祖先上保持。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（`contained=0`）：翻译层记录 PA 改变却放行，本请求自此无法在不依赖下游撤销的情况下回到正确 PA。`event_id=32` 的 `lsq_push` 是它在 LSQ 内的固着点；`event_id=68` 是成功撤销的那一步（含住），不是不可逆点。

### 3.4 检测与掩蔽机制

可检测机制：翻译层的 `effective_pa_changed`（检测到但 `contained=0`）；L4 RAS 的 squash/重放（实际生效，`contained=1`、`reason=squash_replay`）；提交点（本链未到达）。观察到的盲区：翻译层能看见 PA 改变却不阻断，必须依赖一次真实访存触发重放；同流 event 83 的悬空 `errant_commit` 说明并非所有错误消费都被这条重放路径覆盖（但它不在本链上，不改变本 fault 的含住判定）。

### 3.5 最终 SDC 风险判断

本 fault 的权威终局是 Detected/Contained（L4 `squash_masked`，event 68），不是 SDC：污染值在写寄存器前被丢弃。运行仍以 KERNEL PANIC 结束，但该崩溃不由本链归因；因此不能说本 fault 造成了外部可见错误。本实验没有应用级输出 oracle，无法判断最终数据正确性；可证结论仅为“本 fault 在 L4 被显式含住”。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 VA=`0xffffff8001362708`、PFN `81362→c5362`（mask `0x44000`），有效 PA `81362708→c5362708`，终局 `errant_commit` event 26，结局 Crash；seed3 注入 VA=`0xffffffc009483950`、PFN `81d75→95d75`（mask `0x14000`），有效 PA `81d75950→95d75950`，走 store 路径并以 `errant_commit` event 97 收口，结局 Crash。本 seed 的故障值（PFN `c1d74`、PA `c1d74960`/`c1d749e0`）与两者不同，终局是 L4 含住；三者的注入站点相同但地址/掩码/终局不同，不互相引用。

## 4. 完整主链事件表

下表按 event 68 的祖先顺序排列（`0→1→2→3→4→32→33→34→35→36→68`）。`mask` 只在 `inj` 行给出（`0x40001`）；主链 11 个事件，无需折叠。

<!-- witness=68 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '32', '33', '34', '35', '36', '68'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238083182163 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | c1d74 | 81d75 | c1d74 | 0x40001 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=393897 的地址翻译即将使用它 | 被改写后的 PFN=c1d74（VA=ffffffc009483960） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 238083182163 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | c1d74 | 81d75 | c1d74 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=c1d74;ap=0;mtype=2;page_size=1000;pa=c1d74960 | — | — | — | — | DTLB 命中 entry_index=21（way=-1），读取 pfn 字段 | 命中读出 pfn=c1d74，AP=0，page_size=1000，PA=c1d74960 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 238083182163 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | c1d74960 | — | — | 81d75 | c1d74 | 81d75 | c1d74 | — | 81d75960 | c1d74960 | — | — | — | — | lookup 得到的 PFN=81d75 | PFN 记录为 c1d74，翻译 PA=c1d74960 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 238083182163 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | c1d74960 | — | — | — | — | 81d75960 | c1d74960 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=c1d74;ap=0;mtype=2;page_size=1000;pa=c1d74960 | 0 | — | NoFault | — | PFN=81d75 与页内偏移组合 | 有效 PA 81d75960→c1d74960；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 238083182163 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=41835 的 load 请求（VA=ffffffc009483960） | request_id=393897 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 6 | 32 | 4 | 238083183495 | 1332 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ldp_uop 指令 dyn_inst_seq=393897 进入 LSQ | lq_idx=41835 / sq_idx=-1，field=load，VA=ffffffc009483960 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 7 | 33 | 32 | 238083183495 | 0 | mem_req | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LSQ 条目 lq_idx= 的访存请求 | request_id=393897 的 mem_req 生成 | L3：请求成形，下一级消费 |
| 8 | 34 | 33 | 238083183495 | 0 | lsq_sendfrag | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | mem_req request_id=393897 | 请求分片发送到 TLB/L1D（field=load） | L3：请求离开 LSQ 进入地址翻译 |
| 9 | 35 | 34 | 238083183495 | 0 | tlb_translate | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 分片请求 request_id=393897（VA=ffffffc009483960） | 携带故障 PFN 的翻译请求进入 L1D 访问 | L2/L3 交界：LSQ 发出的请求再次使用被污染的翻译 |
| 10 | 36 | 35 | 238083183495 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=41835 的 load 请求（VA=ffffffc009483960） | request_id=393897 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 11 | 68 | 36 | 238083244768 | 61273 | squash_masked | L4 | RAS/ROB(重放) | 1 | addr_fallback | — | 393912 | ffffffc0094839e0 | c1d749e0 | — | — | — | — | — | — | — | — | — | 1 | L4 | masked | squash_replay | dyn_inst_seq=393912 的 load（PA=c1d749e0）收到污染响应 | field=squashed_load，contained=1，outcome=masked | L4：含住点，错误响应被 squash 并重放，未进入架构状态 |


**单位说明**：`squash_masked` 行如实给出 `contained=1`、`detection_layer=L4`、`outcome=masked`、`containment_layer=L4`、`reason=squash_replay`；`lsq_push` 的 `lq_idx=41835`、`sq_idx=-1`、`field=load` 来自原始字段。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 9450 个事件、4 个故障。fault 1 有 8333 个事件，主链 11 个，其余 8322 个是旁支。

1. **同类含住（`squash_masked` 58 条 + event 68 共 59 条）**：最早 `event_id=1679`（parent=1654，tick=238085666676，VA=`0xffffffc009483740`，PA=`0xc1d74740`），最晚 `event_id=7922`（parent=7915，tick=238095210789，VA=`0xffffffc009483430`，PA=`0xc1d74430`）；全部 `contained=1`、`outcome=masked`、`reason=squash_replay`。它们在同一页的不同 VA 上重复“污染响应→squash”；event 1797 属于这一组，不得替代 event 68。
2. **污染消费（`consumer` 1275 条、`taint_reg` 1654 条）**：覆盖 `arch_reg` 0–9、13、19–24、26–30、35、567 等，最早 tick=238083250428（event 84，parent=82，`phys_reg=253`），最晚 tick=238134809817（event 8330，parent=392）。它们说明污染值被大量消费者读取，但不在 event 68 的祖先上。
3. **MSHR 填充组（各 64 条）**：最早 `event_id=40/41/42`（tick=238083242103，`request_id=393913`，`mshr_id=2`、`fill_id=1`、`cache_line=0xc1d74980`），最晚 `event_id=6562/6563/6564`（tick=238092391944，`request_id=406042`，`mshr_id=0`、`fill_id=64`、`cache_line=0xc1d74200`）。
4. **悬空 `errant_commit`（1 条）**：event 83（parent=68，tick=238083249096，`dyn_inst_seq=393846`，`commit_seq=273130`，`contained=0`、`outcome=errant_commit`、`corr=taint_prop`）。作为 event 68 的 child，它不在祖先上；其有序前缀只到 L0..L3（2.7），按权威语义不改变 L4 含住。
5. **生命周期收口（1 条）**：`event_id=9308`（parent=8330，tick=2910165686235，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）。
6. **其它故障**：fault 2（`detected_contained`，路径 `8331,8332,8333,8336,8357,8751`）、fault 3/4（`provable_to_L4_then_unknown`，路径 `9255…9274`、`9280…9299`）各有自己的注入点/地址，不并入本链。

旁支对 SDC 诊断的影响：它们证明同一错误页被反复访问与反复含住（59 次 squash、1275 个 consumer），但权威含住见证仍是 event 68；event 83 的存在使“运行为何仍崩溃”成为本链未闭合的问题，本文件不猜测成因。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `detected_contained` |
| provable_to | `L5`（报告口径）；实际含住层 L4，L5 为 N/A |
| 传播终局事件 | `squash_masked` event_id=68，tick=238083244768，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay` |
| 运行结局 | `Crash`（`run.out` 末尾 KERNEL PANIC；`run.err` 内核 panic 告警）；崩溃不由本链归因 |
| admitted | `true`（`admission.path=contained`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=4`，与触发器 injected=4、inj 事件 4 条一致） |
| conservation | `ok`（consumer_summary：emitted=1134、suppressed=9870、logical_total=11004、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=9450` 与实际解析事件数 9450 相同；injected/stats/inj 均为 4 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（可证 L0→L4 连续祖先 + 真实 `contained=1` 含住事件；L5=N/A） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_CONTAINED_L4` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


判定说明：15 项一致性检查全部通过（事件存在、父子/tick 单调、取值来自本 seed、终局与权威报告一致 `detected_contained`/L4/event 68、含住事件真实、未把 `chain_end` 当 L5、未把 `squash_masked` 写成 L5）。证据张力：运行仍以 KERNEL PANIC 结束，而本 fault 在 L4 已含住；同流 event 83 是原始 `errant_commit` 记录，权威报告对 fault 1 的 `edges` 仍列出 L4→L5 边。按 checker 对 event 83 的悬空路径语义与 canonical 口径，权威终局仍是 event 68/L4；若需判定 run-level 崩溃归因，需独立证据，本文件不做推断。
## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s2/T02-F2-W1/seed2`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `5a4fe3777e4f177e0f7e7dcd87faf2d57ac0b0064f49cf2d2749e316b0168eac` | 346275 | 2026-10-27T14:47:39 |
| `chain_report.json` | `94fbe7356da0e76b859f451d447945bda1da3dd6e798171942b4e851807fd40d` | 960002 | 2026-10-27T14:47:41 |
| `run.out` | `a0ba87f5af9eef7820716d46cec13a643da9c39464d81a90cbea5b3852ee5049` | 8239 | 2026-10-27T14:47:40 |
| `run.err` | `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d` | 1912 | 2026-10-27T14:47:40 |
| `stats.txt` | `1950525eb54831c7818deb120078914670ec135ffe4704319601ddc9d0f48538` | 391280 | 2026-10-27T14:47:40 |
| `armtlb_injections.log` | `3c05c06b673ddf217c0c9a13f6e083999318146619ef9df743a97cc9ece57eca` | 979 | 2026-10-27T14:47:39 |
| manifest `manifest.json` | `a7048f8b298cc7b1863bd7f1ec0b740f47f39bd6987812f776d9259335d8ddfe` | 1438 | 2026-10-27T14:47:42 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s2/T02-F2-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T02-F2-W1 --prop_sample_run_id s2`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s2 --cells T02-F2-W1 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `../R6-AUTHORITATIVE-EVIDENCE.md` 未登记本 (RunID, seed) 的其它副本。

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
