# T03-F5-W9 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T03-F5-W9`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T03`）
- fault model：选 PPN 某 bit stuck-at-0/1，对每次 TLB 读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`卡死`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F5 — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier：`F5`；effective tier：`F5`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1`）
- workload 矩阵标签：GAP/Graph500 子集（BFS、SSSP、PageRank，固定图与结果哈希）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`；矩阵标签写 GAP/Graph500 子集，但原始 run.out 的 `--readfile` 指向 `tlb_probe.rcS`；两者不一致处如实保留，不推断。
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_one --tlb_lsu_tier F5 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T03-F5-W9 --prop_sample_run_id s2`
- source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/manifest.json`（SHA-256 `235af047536bc72ad7360fbf7b3c815f8adcbe9d86f5362c80ce0f16dd18ae6b`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`2`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：28281（与 `chain_report.event_count` 相同）
- fault_id 数量：14（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 有 14 个真实故障，代表故障由 escape-first 规则选为 `fault_id=1`（只有它到达 `full`；fault 2 是 `detected_contained`，其余只到 L4 的未知终局）。终局见证是 `errant_commit`（event_id=293），单祖先为 `0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 64 → 65 → 66 → 67 → 68 → 69 → 73 → 74 → 75 → 293`，共 23 个事件。本 seed 的注入发生在 warm-up 后的第一个 eligible event（tick=237950233578，正好等于触发器记录的 `first_eligible_tick`），并且走 **store** 路径。

### 2.1 故障注入前的正常状态

注入目标是 DTLB 第 0 号 entry（`event_id=1` 的 `entry_index=0`、`way=-1`）。`state_before`=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`：VPN=`0xffffffc009483`，ASID=206，`valid=1`、`global=1`，`ap=0`，4 KiB 页，正常 PFN=`0x81d75`。触发翻译的指令 `dyn_inst_seq=31`（`request_id=31`）使用 VA=`0xffffffc009483eb0`；偏移 `0xeb0`，正常 PA=`(0x81d75 << 12) | 0xeb0 = 0x81d75eb0`。后续 `sq_idx=1` 表明是 store（`strxi_uop`）。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=237950233578（cycle=714565266），`event_id=0`，`fault_id=1`，`request_id=31`，`field=stuck_at_one`，FaultType=`stuck_at_one`，`corr=origin`。注入日志：
`Tick: 237950233578, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb0, old_pfn: 0x81d75, new_pfn: 0x81d77, FaultType: stuck_at_one, Mask: 0x2, effective: 1`。
`before=0x81d75`、`after=0x81d77`，异或 `0x2`：第 1 位被强制为 1。该 run 的 14 条注入行共用 `Mask: 0x2`。`new_pfn << 12 = 0x81d77000`，或上偏移 `0xeb0` 得 `0x81d77eb0`；第 1 位对应 PA 的第 13 位：`0x81d75eb0 → 0x81d77eb0`。`event_id=3` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=81d75eb0`、`after=81d77eb0`、`contained=0`、`outcome=NoFault`。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=237950233578）命中第 0 号 entry，`field=post_lookup`，`before=81d75`、`after=81d77`，`state_after` 的 `pfn=81d77`、`pa=81d77eb0`。`event_id=2` 的 `tlb_pfn` 记录 `state_before=81d75eb0`、`state_after=81d77eb0`、`pa=81d77eb0`、`field=stuck_at_one`。`event_id=3` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 237950233578 把错误有效 PA `0x81d77eb0` 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **store** 路径：`event_id=4` 的 `lsq_push`（tick=237950233911）记录 `pc=0xffffffc008011614`、`opcode=strxi_uop`、`lq_idx=-1`、`sq_idx=1`、`field=store`；`event_id=5` 的 `sq_execute`（同 tick，`sq_idx=1`，`state_before=issued`）执行该 store；`event_id=6` 的 `sq_writeback`（tick=237950235243，`sq_idx=1`，`pa=81d77eb0`，`state_after=packet_built`）构造数据包；`event_id=75` 的 `sq_complete`（tick=237950295516，`sq_idx=1`，`state_after=completed`）完成。load 侧字段（`lq_read` 等）为 N/A；store 全流程使用同一错误 PA。

### 2.5 错误如何经过 cache 和 MSHR

两次访问都未命中：`event_id=7`（`cache_access`，tick=237950235243，PA=`0x81d77eb0`）→ `event_id=8`（`cache_return`，`field=miss`）→ `event_id=9`（`mshr_alloc`，`mshr_id=1`，`cache_line=0x81d77eb0`，`state_after=mshr_allocated`）；`event_id=10`（tick=237950235576，PA=`0x81d77e80`）→ `event_id=11`（`miss`）→ `event_id=12`（`mshr_alloc`，`mshr_id=2`，`cache_line=0x81d77e80`）。两组真实填充：`event_id=64`（`mshr_fill`，tick=237950294517，`mshr_id=2`、`fill_id=1`、`cache_line=0x81d77e80`、`state_after=filled`）→ `event_id=65`（`cache_fill`，`pa=81d77e80`）→ `event_id=66`（`mshr_free`，`mshr_id=2`）；`event_id=67`（`mshr_fill`，tick=237950295183，`mshr_id=0`、`fill_id=2`）→ `event_id=68`（`cache_fill`，`pa=81d77e80`）→ `event_id=69`（`mshr_free`，`mshr_id=0`）。错误行 `0x81d77e80` 被写入 L1D。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、lsq_push、mshr_alloc、mshr_fill、mshr_free、resp、sq_complete、sq_execute、sq_writeback、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mem_req、lsq_sendfrag、lq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=73` 的 `resp`（tick=237950295516，`request_id=31`，原始 `va` 记录 PA=`81d77eb0`）回送数据；`event_id=74` 的 `taint_reg` 把状态从 `clean` 改为 `tainted`（原始记录**未填** `arch_reg`/`phys_reg`，故不能指名寄存器）；`event_id=75` 的 `sq_complete` 完成 SQ 条目。这仍是存储→CPU 边界：store 返回数据进入污染集，随后 store 架构完成。

### 2.7 最终传播终局

L5 终局是 `event_id=293` 的 `errant_commit`：parent=75，tick=237951302175，`dyn_inst_seq=391`，`commit_seq=161`，`pc=0xffffffc0087b1000`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除：L2 `contained=0`；L3 把错误行填入；L4 上本 fault 只有 1 条 `squash_masked`（event 319，旁支），不在 event 293 的祖先上；提交点因此真实暴露。`chain_end`（event_id=23984，parent=10002，tick=398895368670，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 293，tick 237951302175），`provable_to=L5`，`terminal=full`。运行结局是 **Timeout**：`run.out` 第一条 `CHAOS_DETECT` 为 `layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`，随后有含住与 `store_discarded_not_retired` 记录；没有 panic 行，仿真未在预算内正常结束。因此同时成立：fault 1 的传播链已完成（真实 L5），但运行没有正常终止。注入 tick=237950233578，终局 tick=237951302175，延迟 1068597 ticks（cycle 714565266→714568475，3209 个 CPU cycle）——这是本批 T03 样本中延迟最长的一条，与 fault 1 在 warm-up 后立刻注入、随后经过较长的 store/填充/消费路径相符。F5 统计：`attempted=298652463 eligible=298652463 injected=14 fires=298652463 no_effect=298652449`。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 0 号 DTLB 表项（PFN=`81d75`） | PFN→`81d77`（bit1 stuck-at-1） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0xeb0` | PA `81d75eb0`→`81d77eb0`，`contained=0` | 有效 PA | 翻译层未含住 |
| LSQ/SQ（L3） | 翻译结果 | `lsq_push`（`strxi_uop`，`sq_idx=1`）→`sq_execute`→`sq_writeback` | 错误 PA 的数据包 | 污点进入 store |
| L1D（L3） | PA `81d77eb0`/`81d77e80` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | `mshr_id=1`、`mshr_id=2` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | 两组 `mshr_fill`/`cache_fill`/`mshr_free` | 错误行留在 cache | 错误被持久化 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `taint_reg`/`sq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | store 返回数据 | `clean→tainted`（寄存器字段未填） | 污染状态 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染结果 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=237950233578 的第 0 号 DTLB 命中把 PFN 第 1 位卡死为 1，有效 PA 由 `0x81d75eb0` 变为 `0x81d77eb0`；翻译层记录改变却 `contained=0`，`strxi_uop`（`sq_idx=1`）经 `lsq_push`→`sq_execute`→`sq_writeback` 进入 L1D，两次相邻访问（`…eb0`/`…e80`）均 miss 并分配 `mshr_id=1/2`，两组 `mshr_fill`→`cache_fill`→`mshr_free`（tick=237950294517/237950295183）把错误行写入缓存；`resp`、`taint_reg`（clean→tainted，寄存器字段未填）与 `sq_complete` 完成写路径，最终在 tick=237951302175 由 `errant_commit`（`dyn_inst_seq=391`，`commit_seq=161`）收口，距注入 1068597 ticks；链完整走到 L5，运行以 Timeout 收场。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

F5 触发器：`attempted=298652463 eligible=298652463 injected=14 fires=298652463 no_effect=298652449`；`stats.txt`：`numFaultsInjected=14`；流内 `inj` 14 条；权威报告 14 个 fault：三方一致。fault 1 的卡死值被真实读取并消费（`sq_execute`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此 activated；`no_effect` 大是 F5 正常统计。

### 3.2 故障传播类型

**地址型**（错误物理地址）：PFN 第 1 位卡死为 1，VA/偏移/权限不变；有效 PA `0x81d75eb0→0x81d77eb0`。不是数据位错误或控制/时序错误；请求身份 `request_id=31`、`sq_idx=1` 在祖先上保持。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（`contained=0`）。`event_id=4` 的 `lsq_push`（store 登记）与 `event_id=5` 的 `sq_execute` 是执行落点；`event_id=65`/`68` 的 `cache_fill` 是对后续访问也生效的升级点。

### 3.4 检测与掩蔽机制

翻译层可检测 `effective_pa_changed`（本 fault `contained=0`）；L1D/MSHR 无地址校验且错误行已填入；L4 的 RAS 重放在本 fault 的旁支上只有 1 次（event 319，不在主链），fault 2 的 31 次与 fault 6/11 各 1 次都不属于本链；提交点首次暴露。盲区：检测可见但不阻断，主链没有被重放覆盖。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 293），运行 Timeout；权威 `terminal=full`。不是 Masked/Contained；Timeout 不抹除 L5。没有应用级输出 oracle，无法判定静默错误，故不称 SDC；最终数据正确性无法判定。

### 3.6 与同 RunID 其他 seed 的关系

seed1 的代表故障是 fault 2（stuck_at_zero，mask `0x10`，VA=`0xffffffc008a16868`，PA `80a16868→80a06868`，13 次注入）；seed3 的代表故障是 fault 1（stuck_at_zero，mask `0x20000`，VA=`0xffffff807fbce090`，PFN `ffbce→dfbce`，PA `ffbce090→dfbce090`，3 次注入）。本 seed 的代表故障是 fault 1（stuck_at_one，mask `0x2`，VA=`0xffffffc009483eb0`，PFN `81d75→81d77`，PA `81d75eb0→81d77eb0`，14 次注入）。卡死极性/位、地址与注入数均不同；本文件只用自己的事实。

## 4. 完整主链事件表

下表按 event 293 的祖先顺序排列（`0→…→75→293`）。`mask` 只在 `inj` 行给出（`0x2`）；主链 23 个事件，无需折叠。

<!-- witness=293 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '64', '65', '66', '67', '68', '69', '73', '74', '75', '293'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 81d77 | 81d75 | 81d77 | 0x2 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=31 的地址翻译即将使用它 | 被改写后的 PFN=81d77（VA=ffffffc009483eb0） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 237950233578 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 81d77 | 81d75 | 81d77 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d77;ap=0;mtype=2;page_size=1000;pa=81d77eb0 | — | — | — | — | DTLB 命中 entry_index=0（way=-1），读取 pfn 字段 | 命中读出 pfn=81d77，AP=0，page_size=1000，PA=81d77eb0 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 237950233578 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | 81d77eb0 | — | — | 81d75 | 81d77 | 81d75 | 81d77 | — | 81d75eb0 | 81d77eb0 | — | — | — | — | lookup 得到的 PFN=81d75 | PFN 记录为 81d77，翻译 PA=81d77eb0 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 237950233578 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 31 | 31 | ffffffc009483eb0 | 81d77eb0 | — | — | — | — | 81d75eb0 | 81d77eb0 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d77;ap=0;mtype=2;page_size=1000;pa=81d77eb0 | 0 | — | NoFault | — | PFN=81d75 与页内偏移组合 | 有效 PA 81d75eb0→81d77eb0；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 237950233911 | 333 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | strxi_uop 指令 dyn_inst_seq=31 进入 LSQ | lq_idx=-1 / sq_idx=1，field=store，VA=ffffffc009483eb0 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 6 | 5 | 4 | 237950233911 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | SQ 条目 sq_idx=1（state_before=issued） | 执行阶段生成 store 操作（VA=ffffffc009483eb0） | L3：store 进入执行，地址来自故障翻译 |
| 7 | 6 | 5 | 237950235243 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 31 | — | 81d77eb0 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | SQ 条目 sq_idx=1 的执行结果 | packet_built，PA=81d77eb0 | L3：store 数据包成形，携带错误地址 |
| 8 | 7 | 6 | 237950235243 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | 81d77eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=31 访问 L1D（PA=81d77eb0） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 9 | 8 | 7 | 237950235243 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | 81d77eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=81d77eb0 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 10 | 9 | 8 | 237950235243 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 81d77eb0 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=81d77eb0 | mshr_id=1 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 11 | 10 | 9 | 237950235576 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 31 | 31 | ffffffc009483eb0 | 81d77e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=31 访问 L1D（PA=81d77e80） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 12 | 11 | 10 | 237950235576 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | 81d77e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=81d77e80 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 13 | 12 | 11 | 237950235576 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 81d77e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=81d77e80 | mshr_id=2 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 14 | 64 | 12 | 237950294517 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 81d77e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=2 的数据返回（fill_id=1） | state_after=filled，cache_line=81d77e80 | L3：MSHR 完成填充 |
| 15 | 65 | 64 | 237950294517 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | 81d77e80 | 81d77e80 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=1 的填充数据 | cache_line=81d77e80 进入 L1D | L3：错误行进入 cache |
| 16 | 66 | 65 | 237950294517 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 81d77e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=2 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 17 | 67 | 66 | 237950295183 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 81d77e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=2） | state_after=filled，cache_line=81d77e80 | L3：MSHR 完成填充 |
| 18 | 68 | 67 | 237950295183 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 31 | 31 | — | 81d77e80 | 81d77e80 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=2 的填充数据 | cache_line=81d77e80 进入 L1D | L3：错误行进入 cache |
| 19 | 69 | 68 | 237950295183 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 31 | 31 | — | — | 81d77e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 20 | 73 | 69 | 237950295516 | 333 | resp | L4 | L1D→LSU | 1 | seq_primary | 31 | 31 | 81d77eb0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=31） | 响应数据返回（该事件 va 字段记录 PA=81d77eb0） | L4：污染数据返回处理器 |
| 21 | 74 | 73 | 237950295516 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 31 | 31 | 81d77eb0 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=31） | arch_reg= / phys_reg=：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 22 | 75 | 74 | 237950295516 | 0 | sq_complete | L4 | SQ | 1 | seq_primary | — | 31 | ffffffc009483eb0 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | SQ 条目 sq_idx=1 的写回完成 | state_after=completed，PA/VA=ffffffc009483eb0 | L4：store 完成，错误地址已写入存储路径 |
| 23 | 293 | 75 | 237951302175 | 1006659 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=391，commit_seq=161） | contained=0，outcome=errant_commit，PC=ffffffc0087b1000 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`lsq_push` 的 `opcode=strxi_uop`、`sq_idx=1`、`lq_idx=-1`、`field=store` 照原始字段；`taint_reg`（event 74）的 `arch_reg`/`phys_reg` 为空，标 `—`；两组填充的 `fill_id=1/2`、`mshr_id=2/0` 照原始字段。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 28281 个事件、14 个故障。fault 1 共有 400 个事件（主链 23 个 + 旁支 377 个），旁支主要构成如下：

1. **请求分叉（`request_fork` 51 条）**：15 条挂在主链 `mshr_alloc`（event 12）上，36 条挂在主链 `taint_reg`（event 74）上；最早 `event_id=4294967296`（parent=12，tick=237950235576，new_request_id=32，`shared_addr=0x81d77000`），最晚 `event_id=4294967346`（parent=74，tick=237951546930，new_request_id=520）。
2. **污染消费（`consumer` 1 条）**：`event_id=294`（parent=292，tick=237951302175，`dyn_inst_seq=392`，`arch_reg=0`、`phys_reg=142`）——本 fault 的扩散面非常小。
3. **含住旁支（`squash_masked` 1 条）**：`event_id=319`（parent=294，tick=237951547263，VA=`0xffffffc009483e40`，PA=`0x81d77e40`，`contained=1`、`outcome=masked`、`reason=squash_replay`）。整个 seed 的 `squash_masked` 共 34 条（fault 1 1、fault 2 31、fault 6 1、fault 11 1），本链只引用 fault 1 的 1 条，且它不在主链上。
4. **填充与写回旁支**：`mshr_fill`/`cache_fill`/`mshr_free` 的旁支各 12 组（主链另有 2 组；整个 seed 共 334 条 `mshr_fill`，其余 320 条属其它故障）；旁支还有 `cache_evict`/`cache_writeback` 各 7 条、`mshr_merge` 30 条。它们是同一错误页的其它请求/行。
5. **生命周期收口（1 条）**：`event_id=23984`（parent=10002，tick=398895368670，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）。
6. **其它故障**：fault 2（`detected_contained`，路径 `320,321,322,325,358,617`）与 fault 3–14（`provable_to_L4_then_unknown`，例如 fault 7 只到 L3）各有自己的注入/地址；不并入本链。

旁支对 SDC 诊断的影响：fault 1 的污染只被 1 个 consumer 读取，扩散面最小；它唯一的含住事件（event 319）不在主链上，因此不能把本故障改判为 contained；其它故障的 31 次含住与主链无关。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=293，tick=237951302175，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Timeout`（`run.out` 无 panic；最后一批 `CHAOS_DETECT … store_discarded_not_retired`） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=14`，与触发器 injected=14、inj 事件 14 条一致） |
| conservation | `ok`（consumer_summary：emitted=1726、suppressed=3176975、logical_total=3178701、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=28281` 与实际解析事件数 28281 相同；injected/stats/inj 均为 14 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| 判定 | **PASS** |

判定说明：代表故障按 escape-first 选为 fault 1；fault 2 的含住与 fault 1 旁支的 1 次 squash 都不被用来改写 event 293 的终局；`chain_end` 23984 未被当作 L5。传播终局与运行结局分别陈述。15 项一致性检查全部通过。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `11b38ce82e052647e198a9cf276d9607325b4d7989d50d4094c6c83e63497eec` | 1031384 | 2026-10-27T16:13:13 |
| `chain_report.json` | `a00d7138dd203c4ddebf11eb79e426707b33550fc716374f962726fabd98b7d9` | 1466915 | 2026-10-27T16:13:16 |
| `run.out` | `3b67d30eb5549aa30d2a24309a5866603cd53d6658d60d1a8a090db7064d5a9b` | 6045 | 2026-10-27T16:13:14 |
| `run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` | 129 | 2026-10-27T16:13:14 |
| `stats.txt` | `fc48a9ef784db977225eda2193dc363b50c3ebc71374a260b7387c74c4d10deb` | 373991 | 2026-10-27T16:13:14 |
| `armtlb_injections.log` | `3d7c07946c47f9329f81ed0e8c298a418ecf85a62506b74afea90e4637bf3deb` | 2945 | 2026-10-27T14:43:25 |
| manifest `manifest.json` | `235af047536bc72ad7360fbf7b3c815f8adcbe9d86f5362c80ce0f16dd18ae6b` | 1438 | 2026-10-27T16:13:18 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_one --tlb_lsu_tier F5 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T03-F5-W9 --prop_sample_run_id s2`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2 --cells T03-F5-W9 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `../R6-AUTHORITATIVE-EVIDENCE.md` 未登记本 (RunID, seed) 的其它副本。

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
