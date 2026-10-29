# T03-F5-W9 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T03-F5-W9`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T03`）
- fault model：选 PPN 某 bit stuck-at-0/1，对每次 TLB 读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`卡死`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F5 — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier：`F5`；effective tier：`F5`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1`）
- workload 矩阵标签：GAP/Graph500 子集（BFS、SSSP、PageRank，固定图与结果哈希）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`；矩阵标签写 GAP/Graph500 子集，但原始 run.out 的 `--readfile` 指向 `tlb_probe.rcS`；两者不一致处如实保留，不推断。
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3/T03-F5-W9/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_zero --tlb_lsu_tier F5 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T03-F5-W9 --prop_sample_run_id s3`
- source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3/T03-F5-W9/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3/manifest.json`（SHA-256 `ff4b9d8a0f32dffebe8a12b7d1032cb3d1063eadaa9fa92b71462bedd10df7da`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：63693（与 `chain_report.event_count` 相同）
- fault_id 数量：3（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 有 3 个真实故障（另有 `fault_id=0` 的预取事件组，它不是注入故障、没有 `inj`，见 3.1），代表故障由 escape-first 规则选为 `fault_id=1`（只有它到达 `full`；fault 2/3 只到 L4 的未知终局）。终局见证是 `errant_commit`（event_id=21），单祖先为 `0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21`，共 22 个事件。本 seed 走 **load** 路径，整个流中没有任何 `squash_masked`。

### 2.1 故障注入前的正常状态

注入目标为 DTLB 第 1 号 entry（`event_id=1` 的 `entry_index=1`、`way=-1`）。`state_before`=`vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090`：VPN=`0xffffff807fbce`，ASID=206，`valid=1`、`global=1`，`ap=0`，4 KiB 页，正常 PFN=`0xffbce`。触发翻译的指令 `dyn_inst_seq=109`（`request_id=109`）使用 VA=`0xffffff807fbce090`；偏移 `0x90`，正常 PA=`0xffbce090`。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=237950546931（cycle=714566207），`event_id=0`，`fault_id=1`，`request_id=109`，`field=stuck_at_zero`，FaultType=`stuck_at_zero`，`corr=origin`。注入日志：
`Tick: 237950546931, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce090, old_pfn: 0xffbce, new_pfn: 0xdfbce, FaultType: stuck_at_zero, Mask: 0x20000`。
`before=0xffbce`、`after=0xdfbce`，异或 `0x20000`：第 17 位被强制为 0。该 run 的 3 条注入行共用 `Mask: 0x20000`。`new_pfn << 12 = 0xdfbce000`，或上偏移 `0x90` 得 `0xdfbce090`；第 17 位对应 PA 的第 29 位：`0xffbce090 → 0xdfbce090`。`event_id=3` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=ffbce090`、`after=dfbce090`、`contained=0`、`outcome=NoFault`。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=237950546931）命中第 1 号 entry，`field=post_lookup`，`before=ffbce`、`after=dfbce`，`state_after` 的 `pfn=dfbce`、`pa=dfbce090`。`event_id=2` 的 `tlb_pfn` 记录 `state_before=ffbce090`、`state_after=dfbce090`、`pa=dfbce090`、`field=stuck_at_zero`。`event_id=3` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 237950546931 把错误有效 PA `0xdfbce090` 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径：`event_id=4` 的 `lsq_push`（tick=237950547264）记录 `pc=0xffffffc0080116d8`、`opcode=ldr`、`lq_idx=1`、`sq_idx=-1`、`field=load`；`event_id=5` 的 `lq_read`（同 tick，`lq_idx=1`、`request_id=109`、VA=`0xffffff807fbce090`）取出请求。`mem_req`/`lsq_sendfrag` 未发射（N/A），store 侧 N/A。

### 2.5 错误如何经过 cache 和 MSHR

两次 L1D 访问都未命中：`event_id=6`（`cache_access`，tick=237950547264，PA=`0xdfbce090`）→ `event_id=7`（`cache_return`，`field=miss`）→ `event_id=8`（`mshr_alloc`，`mshr_id=1`，`cache_line=0xdfbce090`，`state_after=mshr_allocated`）；`event_id=9`（tick=237950547597，PA=`0xdfbce080`）→ `event_id=10`（`miss`）→ `event_id=11`（`mshr_alloc`，`mshr_id=2`，`cache_line=0xdfbce080`）。两组真实填充：`event_id=12`（`mshr_fill`，tick=237950606538，`mshr_id=2`、`fill_id=1`、`cache_line=0xdfbce080`、`state_after=filled`）→ `event_id=13`（`cache_fill`，`pa=dfbce080`）→ `event_id=14`（`mshr_free`，`mshr_id=2`）；`event_id=15`（`mshr_fill`，tick=237950607204，`mshr_id=0`、`fill_id=2`）→ `event_id=16`（`cache_fill`，`pa=dfbce080`）→ `event_id=17`（`mshr_free`，`mshr_id=0`）。错误行 `0xdfbce080` 被真实写入 L1D。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、lq_complete、lq_read、lsq_push、mshr_alloc、mshr_fill、mshr_free、resp、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mem_req、lsq_sendfrag、sq_execute、sq_writeback、sq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=18` 的 `resp`（tick=237950607537，`request_id=109`，原始 `va` 记录 PA=`dfbce090`）回送数据；`event_id=19` 的 `lq_complete` 完成 `lq_idx=1`（`pa=dfbce090`）；`event_id=20` 的 `taint_reg` 把 `arch_reg=28` / `phys_reg=96` 从 `clean` 改为 `tainted`。输入是 cache 返回的错误数据，内部变化是污染登记，输出是污染寄存器 96。

### 2.7 最终传播终局

L5 终局是 `event_id=21` 的 `errant_commit`：parent=20，tick=237950608203，`dyn_inst_seq=109`，`commit_seq=88`，`pc=0xffffffc0080116d8`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除：L2 `contained=0`；L3 把错误行填入；本 seed 的流中**没有任何 `squash_masked`**（kinds 直方图不含该 kind），因此 L4 没有重放含住；提交点首次真实暴露。`chain_end`（event_id=52781，parent=52780，tick=411127123671，`outcome=errant_commit_seen`、`contained=1`、`corr=none`；该记录没有 `containment_layer`/`containment_reason`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 21，tick 237950608203），`provable_to=L5`，`terminal=full`。运行结局是 **Timeout**：`run.out` 只有 2 条 `CHAOS_DETECT`——`layer=None contained=0 tick=237950608203 ptag=1 reason=errant_commit` 与 `layer=Hardware RAS contained=1 tick=411127123671 ptag=3 reason=store_discarded_not_retired`；没有 panic 行，仿真未在预算内正常结束。因此同时成立：fault 1 的传播链已完成（真实 L5），但运行没有正常终止。注入 tick=237950546931，终局 tick=237950608203，延迟 61272 ticks（cycle 714566207→714566391，184 个 CPU cycle）。F5 统计：`attempted=230828898 eligible=230828898 injected=3 fires=230828898 no_effect=230828895`。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 1 号 DTLB 表项（PFN=`ffbce`） | PFN→`dfbce`（bit17 stuck-at-0） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x90` | PA `ffbce090`→`dfbce090`，`contained=0` | 有效 PA | 翻译层未含住 |
| LSQ（L3） | 翻译结果 | `lsq_push`（`ldr`，`lq_idx=1`）→`lq_read` | 错误 PA 的 load | 污点进入 LQ |
| L1D（L3） | PA `dfbce090`/`dfbce080` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | `mshr_id=1`、`mshr_id=2` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | 两组 `mshr_fill`/`cache_fill`/`mshr_free` | 错误行留在 cache | 错误被持久化 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `lq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | load 数据 | `arch_reg=28/phys_reg=96` clean→tainted | 污染寄存器 96 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染寄存器 96 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=237950546931 的第 1 号 DTLB 命中把 PFN 第 17 位卡死为 0，有效 PA 由 `0xffbce090` 变为 `0xdfbce090`；翻译层记录改变却 `contained=0`，`ldr`（`lq_idx=1`）经 `lsq_push`/`lq_read` 进入 L1D，两次相邻访问（`…090`/`…080`）均 miss 并分配 `mshr_id=1/2`，两组 `mshr_fill`→`cache_fill`→`mshr_free`（tick=237950606538/237950607204）把错误行写入缓存；`resp`、`lq_complete`、`taint_reg`（`arch_reg=28`/`phys_reg=96`）依次完成，最终在 tick=237950608203 由 `errant_commit`（`commit_seq=88`）收口，距注入 61272 ticks；链完整走到 L5，运行以 Timeout 收场。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

F5 触发器：`attempted=230828898 eligible=230828898 injected=3 fires=230828898 no_effect=230828895`；`stats.txt`：`numFaultsInjected=3`；流内 `inj` 3 条；权威报告 3 个 fault：三方一致（流内另有 `fault_id=0` 的 2745 条 `pf_demand` 预取事件，它们没有 `inj`、不属于注入故障，权威报告也不把它们计为 fault，本文件同样排除）。fault 1 的卡死值被真实读取并消费（`lq_read`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此 activated；`no_effect` 大是 F5 正常统计。

### 3.2 故障传播类型

**地址型**（错误物理地址）：PFN 第 17 位卡死为 0，VA/偏移/权限不变；有效 PA `0xffbce090→0xdfbce090`。不是数据位错误或控制/时序错误；请求身份 `request_id=109` 在祖先上保持。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（`contained=0`）。`event_id=4` 的 `lsq_push` 是执行落点；`event_id=13`/`16` 的 `cache_fill` 是对后续访问也生效的升级点。

### 3.4 检测与掩蔽机制

翻译层可检测 `effective_pa_changed`（本 fault `contained=0`）；L1D/MSHR 无地址校验且错误行已填入；本 seed 没有任何 `squash_masked`，L4 重放未对任何故障生效；提交点首次暴露。观察到的盲区是：检测可见但不阻断、cache 无地址校验、且没有重放兜底——这是本批 T03 样本中“最纯”的逃逸形态之一。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 21），运行 Timeout；权威 `terminal=full`。不是 Masked/Contained；Timeout 不抹除 L5。没有应用级输出 oracle，无法判定静默错误，故不称 SDC；最终数据正确性无法判定。

### 3.6 与同 RunID 其他 seed 的关系

seed1 的代表故障是 fault 2（stuck_at_zero，mask `0x10`，VA=`0xffffffc008a16868`，PA `80a16868→80a06868`，13 次注入）；seed2 的代表故障是 fault 1（stuck_at_one，mask `0x2`，VA=`0xffffffc009483eb0`，PA `81d75eb0→81d77eb0`，14 次注入）。本 seed 的代表故障是 fault 1（stuck_at_zero，mask `0x20000`，VA=`0xffffff807fbce090`，PA `ffbce090→dfbce090`，3 次注入）。三者的卡死位/地址/注入数都不同。跨 RunID 方面，本 seed 与 `T03-F5-W4` seed3 共享同一确定性注入点（tick=237950546931、VA=`0xffffff807fbce090`，README 已记录），但 mask 不同（本 seed `0x20000`，W4 为 `0x1000`）、PA 不同（本 seed `dfbce090`，W4 为 `febce090`）、证据 SHA 与 `simTicks` 不同；本文件只使用本 seed 自己的事实。

## 4. 完整主链事件表

下表按 event 21 的祖先顺序排列（`0→1→…→21`）。`mask` 只在 `inj` 行给出（`0x20000`）；主链 22 个事件，无需折叠。

<!-- witness=21 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950546931 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | dfbce | ffbce | dfbce | 0x20000 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=109 的地址翻译即将使用它 | 被改写后的 PFN=dfbce（VA=ffffff807fbce090） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 237950546931 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | dfbce | ffbce | dfbce | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=dfbce;ap=0;mtype=2;page_size=1000;pa=dfbce090 | — | — | — | — | DTLB 命中 entry_index=1（way=-1），读取 pfn 字段 | 命中读出 pfn=dfbce，AP=0，page_size=1000，PA=dfbce090 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 237950546931 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | dfbce090 | — | — | ffbce | dfbce | ffbce | dfbce | — | ffbce090 | dfbce090 | — | — | — | — | lookup 得到的 PFN=ffbce | PFN 记录为 dfbce，翻译 PA=dfbce090 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 237950546931 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | dfbce090 | — | — | — | — | ffbce090 | dfbce090 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=dfbce;ap=0;mtype=2;page_size=1000;pa=dfbce090 | 0 | — | NoFault | — | PFN=ffbce 与页内偏移组合 | 有效 PA ffbce090→dfbce090；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 237950547264 | 333 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ldr 指令 dyn_inst_seq=109 进入 LSQ | lq_idx=1 / sq_idx=-1，field=load，VA=ffffff807fbce090 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 6 | 5 | 4 | 237950547264 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=1 的 load 请求（VA=ffffff807fbce090） | request_id=109 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 7 | 6 | 5 | 237950547264 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 109 | 109 | ffffff807fbce090 | dfbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 访问 L1D（PA=dfbce090） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 8 | 7 | 6 | 237950547264 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 109 | 109 | — | dfbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=dfbce090 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 9 | 8 | 7 | 237950547264 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | dfbce090 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=dfbce090 | mshr_id=1 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 10 | 9 | 8 | 237950547597 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 109 | 109 | ffffff807fbce090 | dfbce080 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 访问 L1D（PA=dfbce080） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 11 | 10 | 9 | 237950547597 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 109 | 109 | — | dfbce080 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=dfbce080 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 12 | 11 | 10 | 237950547597 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | dfbce080 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=dfbce080 | mshr_id=2 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 13 | 12 | 11 | 237950606538 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | dfbce080 | 2 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=2 的数据返回（fill_id=1） | state_after=filled，cache_line=dfbce080 | L3：MSHR 完成填充 |
| 14 | 13 | 12 | 237950606538 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 109 | 109 | — | dfbce080 | dfbce080 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=1 的填充数据 | cache_line=dfbce080 进入 L1D | L3：错误行进入 cache |
| 15 | 14 | 13 | 237950606538 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | dfbce080 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=2 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 16 | 15 | 14 | 237950607204 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | dfbce080 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=2） | state_after=filled，cache_line=dfbce080 | L3：MSHR 完成填充 |
| 17 | 16 | 15 | 237950607204 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 109 | 109 | — | dfbce080 | dfbce080 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=2 的填充数据 | cache_line=dfbce080 进入 L1D | L3：错误行进入 cache |
| 18 | 17 | 16 | 237950607204 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | dfbce080 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 19 | 18 | 17 | 237950607537 | 333 | resp | L4 | L1D→LSU | 1 | seq_primary | 109 | 109 | dfbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=109） | 响应数据返回（该事件 va 字段记录 PA=dfbce090） | L4：污染数据返回处理器 |
| 20 | 19 | 18 | 237950607537 | 0 | lq_complete | L4 | LQ | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | dfbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应数据 request_id=109 | LQ 条目 lq_idx=1 完成，PA=dfbce090 | L4：load 写回 LQ，错误值即将写寄存器 |
| 21 | 20 | 19 | 237950607537 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 109 | 109 | dfbce090 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=109） | arch_reg=28 / phys_reg=96：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 22 | 21 | 20 | 237950608203 | 666 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 109 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=109，commit_seq=88） | contained=0，outcome=errant_commit，PC=ffffffc0080116d8 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`tlb_*` 的 `before/after` 含义见 2.2；两组填充的 `fill_id=1/2`、`mshr_id=2/0` 照原始字段；`taint_reg` 为 `arch_reg=28`/`phys_reg=96`。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 63693 个事件、3 个真实故障（另有 fault 0 的预取事件组）。fault 1 的主链 22 个，旁支 55880 个，是本批样本中旁支最多的之一。

1. **请求分叉（`request_fork` 9970 条）**：全部挂在主链 `taint_reg`（event 20）上；最早 `event_id=4294967296`（tick=237951924885，new_request_id=990，`shared_addr=0xdfbce000`），最晚 `event_id=4294977893`（tick=237970530927，new_request_id=68558）。它们是在同一错误页内派生的海量再访问，说明卡死后错误地址被大量复用。
2. **污染消费（`consumer` 1281 条、`taint_reg` 9969 条）**：最早 `event_id=22`（parent=20，tick=237950608536，`arch_reg=28`、`phys_reg=96`），最晚 `event_id=52780`（parent=161，tick=238013704377，`arch_reg=2`、`phys_reg=406`）。
3. **缓存与 MSHR 旁支**：`cache_access`/`cache_return` 各 10031、`resp` 9969、`lq_complete` 249、`mshr_alloc` 96、`mshr_fill`/`cache_fill`/`mshr_free` 各 121、`mshr_merge` 191、`cache_evict` 1；最早 `mshr_fill` event 173（tick=237951969840，request 990，`mshr_id=4`、`fill_id=3`、`cache_line=0xdfbce000`），最晚 event 3369（tick=237959998803，request 11883，`mshr_id=0`、`fill_id=131`、`cache_line=0xdfbce280`）。
4. **预取旁支**：`pf_queue` 36、`pf_issue` 34、`pf_demand` 3617、`pf_fill` 41；最早 `pf_queue` event 936（tick=237958465005，`pf_request_id=4294967297`），最晚 `pf_demand` event 48103（tick=237970530927，request 68558，`field=demand_hit`）。这些事件说明错误地址扩散到预取器；它们不在主链祖先上，不能当 L3 中间步。
5. **生命周期收口（1 条）**：`event_id=52781`（parent=52780，tick=411127123671，`outcome=errant_commit_seen`、`contained=1`、`corr=none`；无 containment 字段）。
6. **其它故障**：fault 2（`provable_to_L4_then_unknown`，路径 `240,241,242,278,282`）与 fault 3（`provable_to_L4_then_unknown`，路径 `718,719,720,723,759`）各有自己的注入/地址；不并入本链。整个 seed 的 `squash_masked` 计数为 0。

旁支对 SDC 诊断的影响：它们显示了极强的扩散（9970 fork、1281 consumer、3617 pf_demand），但主链没有任何含住事件，终局由 event 21 单独证明；fault 2/3 的 L4 未知不改变 fault 1 的 `full`。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=21，tick=237950608203，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Timeout`（`run.out` 仅 2 条 `CHAOS_DETECT`；仿真未在预算内正常结束） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=3`，与触发器 injected=3、inj 事件 3 条一致；fault_id=0 的预取事件不计为注入） |
| conservation | `ok`（consumer_summary：emitted=1281、suppressed=338093209、logical_total=338094490、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=63693` 与实际解析事件数 63693 相同；injected/stats/inj 均为 3（报告 faults=3） |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| 判定 | **PASS** |

判定说明：代表故障按 escape-first 选为 fault 1；本 seed 没有 `squash_masked`，不存在把含住当终局的风险；`chain_end` 52781 未被当作 L5。传播终局与运行结局分别陈述。15 项一致性检查全部通过；fault_id=0 的预取事件已明确排除在“真实故障数”之外，未与故障链混算。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3/T03-F5-W9/seed3`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `7cdc2fd4c88fa45e94e5635b23a529c99aebf4913e16ae1a25a6ba9d696c098b` | 2168447 | 2026-10-27T17:46:50 |
| `chain_report.json` | `5ddfab7b2758b2f20c7ed96be2b5bd1a26332f7d8bafddf2a13730e50a8ad91e` | 1138842 | 2026-10-27T17:46:57 |
| `run.out` | `1b9249278869142bac4e29d21984292455ef57a2b1773f5ab646e9b9aba0962e` | 2628 | 2026-10-27T17:46:52 |
| `run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` | 129 | 2026-10-27T17:46:52 |
| `stats.txt` | `53b07212959acb238a5fdc08be687e849c28aa2f21030dc5ab68c12380e15a8e` | 362830 | 2026-10-27T17:46:50 |
| `armtlb_injections.log` | `ab9554547c6547dcf8188e8afde4c3fd01dc5ea8451e1749ee50bbc8989b8977` | 805 | 2026-10-27T16:17:01 |
| manifest `manifest.json` | `ff4b9d8a0f32dffebe8a12b7d1032cb3d1063eadaa9fa92b71462bedd10df7da` | 1438 | 2026-10-27T17:46:59 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3/T03-F5-W9/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_zero --tlb_lsu_tier F5 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T03-F5-W9 --prop_sample_run_id s3`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3 --cells T03-F5-W9 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `../R6-AUTHORITATIVE-EVIDENCE.md` 未登记本 (RunID, seed) 的其它副本。

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
