# T03-F5-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T03-F5-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T03`）
- fault model：选 PPN 某 bit stuck-at-0/1，对每次 TLB 读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`卡死`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F5 — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier：`F5`；effective tier：`F5`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1`）
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_one --tlb_lsu_tier F5 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T03-F5-W4 --prop_sample_run_id s2`
- source head：`38122675b91e05aaa0d636d14a89b6c6a90ea53c`（逐 seed manifest 的 binary_source_head）
- binary source head：`38122675b91e05aaa0d636d14a89b6c6a90ea53c`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/manifest.json`（SHA-256 `02bae551fd1170b70f780ebdb4ecb0827863591cd3f3f606c91a5c8e3e567d8d`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`2`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：12084（与 `chain_report.event_count` 相同）
- fault_id 数量：7（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 有 7 个真实故障，代表故障由 escape-first 规则选为 `fault_id=1`（只有它到达 `full`，其余故障都只到 L4 的未知终局）。终局见证是 `errant_commit`（event_id=21），其单祖先为 `0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21`，共 22 个事件。这是本批 T03 样本中**注入最早**的一条：tick=237950747064，仅比 checkpoint 基准晚 950049 ticks；并且整个 seed 的事件流中没有任何 `squash_masked`。

### 2.1 故障注入前的正常状态

注入目标是 DTLB 第 2 号 entry（`event_id=1` 的 `entry_index=2`、`way=-1`）。`state_before`=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362700`：VPN=`0xffffff8001362`，ASID=206，`valid=1`、`global=1`，`ap=0`，4 KiB 页，正常 PFN=`0x81362`。触发的访存指令 `dyn_inst_seq=111`（`request_id=111`）使用 VA=`0xffffff8001362700`；偏移 `0x700`，正常 PA=`(0x81362 << 12) | 0x700 = 0x81362700`，与 `state_before` 一致。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=237950747064（cycle=714566808），`event_id=0`，`fault_id=1`，`request_id=111`，`field=stuck_at_one`，FaultType=`stuck_at_one`，`corr=origin`。注入日志：
`Tick: 237950747064, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362700, old_pfn: 0x81362, new_pfn: 0x81366, FaultType: stuck_at_one, Mask: 0x4, effective: 1`。
`before=0x81362`、`after=0x81366`，异或 `0x4`：第 2 位被强制为 1（stuck-at-1）。该 run 的全部 7 条注入行使用同一 `Mask: 0x4`。`new_pfn << 12 = 0x81366000`，或上偏移 `0x700` 得 `0x81366700`；第 2 位对应 PA 的第 14 位：`0x81362700 → 0x81366700`。`event_id=3` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=81362700`、`after=81366700`、`contained=0`、`outcome=NoFault`。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=237950747064）命中第 2 号 entry，`field=post_lookup`，`before=81362`、`after=81366`，`state_after` 的 `pfn=81366`、`pa=81366700`。`event_id=2` 的 `tlb_pfn` 记录 `state_before=81362700`、`state_after=81366700`、`pa=81366700`、`field=stuck_at_one`。`event_id=3` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 237950747064 把错误有效 PA `0x81366700` 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径：`event_id=4` 的 `lsq_push`（tick=237950747397）记录 `pc=0xffffffc0080116e0`、`opcode=ldr`、`lq_idx=2`、`sq_idx=-1`、`field=load`；`event_id=5` 的 `lq_read`（同 tick，`lq_idx=2`、`request_id=111`、VA=`0xffffff8001362700`）把请求取出。输入是错误翻译，内部变化是登记与取出，输出是错误 PA 的访存；`mem_req`/`lsq_sendfrag` 未发射（N/A），store 侧为 N/A。

### 2.5 错误如何经过 cache 和 MSHR

两次 L1D 访问都未命中，且两次 PA 相同（都是 `0x81366700`，这是本 seed 与其它样本的一个结构差异——两次访问落在同一错误行）：`event_id=6`（`cache_access`，tick=237950747397，PA=`0x81366700`）→ `event_id=7`（`cache_return`，`field=miss`）→ `event_id=8`（`mshr_alloc`，`mshr_id=1`，`cache_line=0x81366700`，`state_after=mshr_allocated`）；`event_id=9`（同一 PA，tick=237950747730）→ `event_id=10`（`miss`）→ `event_id=11`（`mshr_alloc`，`mshr_id=2`，`cache_line=0x81366700`）。随后两组真实填充：`event_id=12`（`mshr_fill`，tick=237950806671，`mshr_id=2`、`fill_id=1`、`cache_line=0x81366700`、`state_after=filled`）→ `event_id=13`（`cache_fill`，`pa=81366700`）→ `event_id=14`（`mshr_free`，`mshr_id=2`）；`event_id=15`（`mshr_fill`，tick=237950807337，`mshr_id=0`、`fill_id=2`）→ `event_id=16`（`cache_fill`，`pa=81366700`）→ `event_id=17`（`mshr_free`，`mshr_id=0`）。错误行被真实写入 cache。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、lq_complete、lq_read、lsq_push、mshr_alloc、mshr_fill、mshr_free、resp、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mem_req、lsq_sendfrag、sq_execute、sq_writeback、sq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=18` 的 `resp`（tick=237950807670，`request_id=111`，原始 `va` 记录 PA=`81366700`）回送数据；`event_id=19` 的 `lq_complete` 完成 `lq_idx=2`；`event_id=20` 的 `taint_reg` 把 `arch_reg=19` / `phys_reg=98` 从 `clean` 改为 `tainted`。输入是 cache 返回的错误数据，内部变化是污染登记，输出是污染寄存器 98。

### 2.7 最终传播终局

L5 终局是 `event_id=21` 的 `errant_commit`：parent=20，tick=237950808669，`dyn_inst_seq=111`，`commit_seq=90`，`pc=0xffffffc0080116e0`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除：L2 `contained=0`；L3 把错误行填入；本 seed 的流中**没有任何 `squash_masked`**（kinds 直方图不含该 kind，故不存在 L4 重放含住）；因此提交点是第一次真实暴露。`chain_end`（event_id=10530，parent=9766，tick=436072508316，`outcome=errant_commit_seen`、`contained=1`、`corr=none`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 21，tick 237950808669），`provable_to=L5`，`terminal=full`。运行结局是 **Timeout**：`run.out` 只有 3 条 `CHAOS_DETECT`——第一条 `layer=None contained=0 tick=237950808669 ptag=1 reason=errant_commit`，后两条为 tick=436072508316 的 `store_discarded_not_retired`；没有 panic 行，仿真未在预算内正常结束。因此同时成立：传播链已完成（真实 L5），但运行没有正常终止。注入 tick=237950747064，终局 tick=237950808669，延迟 61605 ticks（cycle 714566808→714566993，185 个 CPU cycle）。F5 统计：`attempted=264672881 eligible=264672881 injected=7 fires=264672881 no_effect=264672874`。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 2 号 DTLB 表项（PFN=`81362`） | PFN→`81366`（bit2 stuck-at-1） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x700` | PA `81362700`→`81366700`，`contained=0` | 有效 PA | 翻译层未含住 |
| LSQ（L3） | 翻译结果 | `lsq_push`（`ldr`，`lq_idx=2`）→`lq_read` | 错误 PA 的 load | 污点进入 LQ |
| L1D（L3） | PA `81366700`（两次相同） | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 同一错误行 | `mshr_id=1`、`mshr_id=2` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | 两组 `mshr_fill`/`cache_fill`/`mshr_free` | 错误行留在 cache | 错误被持久化 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `lq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | load 数据 | `arch_reg=19/phys_reg=98` clean→tainted | 污染寄存器 98 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染寄存器 98 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=237950747064 的第 2 号 DTLB 命中把 PFN 第 2 位卡死为 1，有效 PA 由 `0x81362700` 变为 `0x81366700`；翻译层记录改变却 `contained=0`，`ldr`（`lq_idx=2`）经 `lsq_push`/`lq_read` 进入 L1D，两次访问同一错误 PA 均 miss 并分配 `mshr_id=1/2`，两组 `mshr_fill`→`cache_fill`→`mshr_free`（tick=237950806671/237950807337）把错误行写入缓存；`resp`、`lq_complete`、`taint_reg`（`arch_reg=19`/`phys_reg=98`）依次完成，最终在 tick=237950808669 由 `errant_commit`（`dyn_inst_seq=111`，`commit_seq=90`）收口，距注入 61605 ticks；链完整走到 L5，运行以 Timeout 收场。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

F5 触发器：`attempted=264672881 eligible=264672881 injected=7 fires=264672881 no_effect=264672874`；`stats.txt`：`numFaultsInjected=7`；流内 `inj` 7 条；权威报告 7 个 fault：三方一致。fault 1 的卡死值被真实读取并消费（`lq_read`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此是 activated。`no_effect` 大是 F5 的正常统计（正确值已等于卡死值时不计新注入），非失败。

### 3.2 故障传播类型

**地址型**（错误物理地址）：卡死的是 PFN 第 2 位，VA/偏移/权限不变；有效 PA 从 `0x81362700` 变 `0x81366700`。不是数据位错误，也不是控制状态或时序错误；请求身份 `request_id=111` 在祖先上保持。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（`contained=0`）：翻译层记录 PA 改变却放行。`event_id=4` 的 `lsq_push` 是执行落点；`event_id=13`/`16` 的 `cache_fill` 是对后续访问也生效的升级点。

### 3.4 检测与掩蔽机制

翻译层可检测 `effective_pa_changed`（本 fault `contained=0`）；L1D/MSHR 无地址校验，且错误行已填入 cache；本 seed **完全没有 `squash_masked`**，因此 L4 重放机制在本 run 中没有对任何故障生效；提交点是首次真实暴露。观察到的盲区：翻译层检测却不阻断，且没有重放兜底，错误行留在缓存中。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 21），运行 Timeout；权威 `terminal=full`。不是 Masked/Contained；Timeout 不抹除 L5。没有应用级输出 oracle，无法判定静默错误数据，故不称 SDC；可证结论是“卡死导致错误地址、错误行入 cache、错误提交真实发生并（在仿真层面）未正常终止”。最终数据正确性无法判定。

### 3.6 与同 RunID 其他 seed 的关系

seed1 的代表故障是 fault 2（stuck_at_zero，mask `0x10`，VA=`0xffffffc008a16868`，PFN `80a16→80a06`，PA `80a16868→80a06868`，13 次注入，整个 seed 共 5 条含住事件（fault 2 自身 0 条））；seed3 的代表故障是 fault 2（stuck_at_zero，mask `0x1000`，VA=`0xffffff807fbce090`，PFN `ffbce→febce`，PA `ffbce090→febce090`，9 次注入，整个 seed 共 97 条含住事件（其中 fault 2 旁支 34 条））。本 seed 的代表故障是 fault 1（**stuck_at_one**，mask `0x4`，VA=`0xffffff8001362700`，PA `81362700→81366700`，7 次注入，0 条含住）。三者的卡死极性/位、地址、注入次数与是否含住都不同，不互相引用。

## 4. 完整主链事件表

下表按 event 21 的祖先顺序排列（`0→1→…→21`）。`mask` 只在 `inj` 行给出（`0x4`）；主链 22 个事件，无需折叠。

<!-- witness=21 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950747064 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 111 | 111 | ffffff8001362700 | — | — | — | 81362 | 81366 | 81362 | 81366 | 0x4 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=111 的地址翻译即将使用它 | 被改写后的 PFN=81366（VA=ffffff8001362700） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 237950747064 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 111 | 111 | ffffff8001362700 | — | — | — | 81362 | 81366 | 81362 | 81366 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362700 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81366;ap=0;mtype=2;page_size=1000;pa=81366700 | — | — | — | — | DTLB 命中 entry_index=2（way=-1），读取 pfn 字段 | 命中读出 pfn=81366，AP=0，page_size=1000，PA=81366700 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 237950747064 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 111 | 111 | ffffff8001362700 | 81366700 | — | — | 81362 | 81366 | 81362 | 81366 | — | 81362700 | 81366700 | — | — | — | — | lookup 得到的 PFN=81362 | PFN 记录为 81366，翻译 PA=81366700 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 237950747064 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 111 | 111 | ffffff8001362700 | 81366700 | — | — | — | — | 81362700 | 81366700 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362700 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81366;ap=0;mtype=2;page_size=1000;pa=81366700 | 0 | — | NoFault | — | PFN=81362 与页内偏移组合 | 有效 PA 81362700→81366700；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 237950747397 | 333 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 111 | ffffff8001362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ldr 指令 dyn_inst_seq=111 进入 LSQ | lq_idx=2 / sq_idx=-1，field=load，VA=ffffff8001362700 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 6 | 5 | 4 | 237950747397 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 111 | 111 | ffffff8001362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=2 的 load 请求（VA=ffffff8001362700） | request_id=111 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 7 | 6 | 5 | 237950747397 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 111 | 111 | ffffff8001362700 | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=111 访问 L1D（PA=81366700） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 8 | 7 | 6 | 237950747397 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 111 | 111 | — | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=81366700 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 9 | 8 | 7 | 237950747397 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 111 | 111 | — | — | 81366700 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=81366700 | mshr_id=1 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 10 | 9 | 8 | 237950747730 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 111 | 111 | ffffff8001362700 | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=111 访问 L1D（PA=81366700） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 11 | 10 | 9 | 237950747730 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 111 | 111 | — | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=81366700 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 12 | 11 | 10 | 237950747730 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 111 | 111 | — | — | 81366700 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=81366700 | mshr_id=2 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 13 | 12 | 11 | 237950806671 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 111 | 111 | — | — | 81366700 | 2 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=2 的数据返回（fill_id=1） | state_after=filled，cache_line=81366700 | L3：MSHR 完成填充 |
| 14 | 13 | 12 | 237950806671 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 111 | 111 | — | 81366700 | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=1 的填充数据 | cache_line=81366700 进入 L1D | L3：错误行进入 cache |
| 15 | 14 | 13 | 237950806671 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 111 | 111 | — | — | 81366700 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=2 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 16 | 15 | 14 | 237950807337 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 111 | 111 | — | — | 81366700 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=2） | state_after=filled，cache_line=81366700 | L3：MSHR 完成填充 |
| 17 | 16 | 15 | 237950807337 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 111 | 111 | — | 81366700 | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=2 的填充数据 | cache_line=81366700 进入 L1D | L3：错误行进入 cache |
| 18 | 17 | 16 | 237950807337 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 111 | 111 | — | — | 81366700 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 19 | 18 | 17 | 237950807670 | 333 | resp | L4 | L1D→LSU | 1 | seq_primary | 111 | 111 | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=111） | 响应数据返回（该事件 va 字段记录 PA=81366700） | L4：污染数据返回处理器 |
| 20 | 19 | 18 | 237950807670 | 0 | lq_complete | L4 | LQ | 1 | seq_primary | 111 | 111 | ffffff8001362700 | 81366700 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应数据 request_id=111 | LQ 条目 lq_idx=2 完成，PA=81366700 | L4：load 写回 LQ，错误值即将写寄存器 |
| 21 | 20 | 19 | 237950807670 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 111 | 111 | 81366700 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=111） | arch_reg=19 / phys_reg=98：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 22 | 21 | 20 | 237950808669 | 999 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 111 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=111，commit_seq=90） | contained=0，outcome=errant_commit，PC=ffffffc0080116e0 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：两次 `cache_access` 的 PA 都是 `81366700`（本 seed 的事实，与其它样本“两次相邻不同 PA”的形状不同）；两组填充的 `fill_id=1/2`、`mshr_id=2/0` 照原始字段；`taint_reg` 为 `arch_reg=19`/`phys_reg=98`。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 12084 个事件、7 个故障。fault 1 的事件集合为 2306+22 个（主链 22 个，旁支 2306 个）。

1. **请求分叉（`request_fork` 296 条）**：全部挂在主链 `taint_reg`（event 20）上，最早 `event_id=4294967297`（tick=237950884260，new_request_id=213，`shared_addr=0x81366000`），最晚 `event_id=4294968773`（tick=237970727064，new_request_id=61081）。它们在同一错误页内派生出大量再访问，但没有成为 event 21 的祖先。
2. **污染消费（`consumer` 544 条、`taint_reg` 296 条）**：最早 `event_id=22`（parent=20，tick=237950808669，`arch_reg=19`、`phys_reg=98`），最晚 `event_id=9766`（parent=128，tick=237970487970，`arch_reg=2`、`phys_reg=795`）。扩散面远大于 seed1 的 fault 2（5 个 consumer），说明同一卡死位在本 run 的早期就影响了大量消费。
3. **无含住事件**：整个 seed 的 `squash_masked` 计数为 0；`run.out` 的 3 条 `CHAOS_DETECT` 中也没有 `squash_replay`。因此本 seed 不存在“某故障被 L4 含住”的旁支。
4. **生命周期收口（1 条）**：`event_id=10530`（parent=9766，tick=436072508316，`outcome=errant_commit_seen`、`contained=1`、`corr=none`）。
5. **其它故障**：fault 2/3/4/5/6/7 的路径分别为 `23…58`、`78…98`、`160…180`、`535…652`、`3579…3724`、`6859…6895`，全部是 `provable_to_L4_then_unknown`；它们各有自己的注入点/VA（同一 `Mask: 0x4`），不并入 fault 1 的链。

旁支对 SDC 诊断的影响：它们证明错误页被大量再访问（296 fork、544 consumer），但没有含住事件覆盖；本链的终局仍由 event 21 单独证明，且本 seed 的“no squash”事实使“错误未被掩蔽”这一判断更强。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=21，tick=237950808669，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Timeout`（`run.out` 无 panic，仅 3 条 `CHAOS_DETECT`；仿真未在预算内正常结束） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=7`，与触发器 injected=7、inj 事件 7 条一致） |
| conservation | `ok`（consumer_summary：emitted=758、suppressed=3771308、logical_total=3772066、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=12084` 与实际解析事件数 12084 相同；injected/stats/inj 均为 7 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| 判定 | **PASS** |

判定说明：传播终局（event 21）与运行结局（Timeout）分别陈述；本 seed 没有 `squash_masked`，不存在把含住误写成终局的风险；`chain_end` 10530 未被当作 L5。15 项一致性检查全部通过。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `24af59b714fef58de59e9b9d1084d2828f3ad37f51fb27ad22e2caac0d72a26f` | 451538 | 2026-10-27T04:12:00 |
| `chain_report.json` | `efcf3e78cf316758a1c7012a5d74d74714d0f78d721df6bc456c76ea2aa2dd42` | 650316 | 2026-10-27T04:12:01 |
| `run.out` | `311615823fb7199600b4c382bbe3572332a8d0ea3b008c3998680550fd3b3d04` | 2735 | 2026-10-27T04:12:00 |
| `run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` | 129 | 2026-10-27T04:12:00 |
| `stats.txt` | `1511491e101ee8f4eee64c8550fe6b9e8a7af046cd51cc9d6cd4a0ee6a689f68` | 364709 | 2026-10-27T04:12:00 |
| `armtlb_injections.log` | `8bd050f56ab93a87db8be19b1f89de4cf5e1e44be7d1c8ea1c371be612b5455f` | 1573 | 2026-10-27T02:42:10 |
| manifest `manifest.json` | `02bae551fd1170b70f780ebdb4ecb0827863591cd3f3f606c91a5c8e3e567d8d` | 1438 | 2026-10-27T04:12:02 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_one --tlb_lsu_tier F5 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T03-F5-W4 --prop_sample_run_id s2`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2 --cells T03-F5-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `../R6-AUTHORITATIVE-EVIDENCE.md` 未登记本 (RunID, seed) 的其它副本。

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
