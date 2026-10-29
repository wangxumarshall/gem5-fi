# T03-F5-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T03-F5-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T03`）
- fault model：选 PPN 某 bit stuck-at-0/1，对每次 TLB 读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`卡死`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F5 — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier：`F5`；effective tier：`F5`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1`）
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_zero --tlb_lsu_tier F5 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T03-F5-W4 --prop_sample_run_id s1`
- source head：`38122675b91e05aaa0d636d14a89b6c6a90ea53c`（逐 seed manifest 的 binary_source_head）
- binary source head：`38122675b91e05aaa0d636d14a89b6c6a90ea53c`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/manifest.json`（SHA-256 `edc14fcff3c1a38574b01efff323627fd35ed08016ad70811e7e257a707ed504`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`1`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：8327（与 `chain_report.event_count` 相同）
- fault_id 数量：13（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 共 13 个真实故障（`fault_id=1..13`），escape-first 规则选出代表故障为 `fault_id=2`：fault 1 是 `detected_contained`，只有 fault 2 到达 `full`，其余故障为含住或只到 L4 的未知终局。终局见证是 `errant_commit`（event_id=280），其单祖先为 `259 → 260 → 261 → 262 → 263 → 264 → 265 → 266 → 267 → 268 → 269 → 270 → 271 → 272 → 273 → 274 → 275 → 276 → 277 → 278 → 279 → 280`，共 22 个事件。这条链走 **load** 路径，并真实发射了两组 MSHR 填充。

### 2.1 故障注入前的正常状态

注入目标为 DTLB 第 4 号 entry（`event_id=260` 的 `entry_index=4`、`way=-1`）。`state_before`=`vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868`：VPN=`0xffffffc008a16`，ASID=206，`valid=1`、`global=1`，权限 `ap=2`（与其它 seed 的 `ap=0` 不同，本文件如实记录而不解释其特权语义），4 KiB 页，正常 PFN=`0x80a16`。触发翻译的指令 `dyn_inst_seq=373`（`request_id=373`）使用 VA=`0xffffffc008a16868`；偏移 `0x868`，正常 PA=`(0x80a16 << 12) | 0x868 = 0x80a16868`，与 `state_before` 的 `pa` 一致。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=237951174969（cycle=714568093），`event_id=259`，`fault_id=2`，`request_id=373`，`field=stuck_at_zero`，FaultType=`stuck_at_zero`，`corr=origin`。注入日志：
`Tick: 237951174969, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a16868, old_pfn: 0x80a16, new_pfn: 0x80a06, FaultType: stuck_at_zero, Mask: 0x10, effective: 1`。
`before=0x80a16`、`after=0x80a06`，异或 `0x10`：第 4 位被强制为 0（stuck-at-0），与 T03“卡死”模型一致——该 run 的所有注入行都使用同一 `Mask: 0x10`（日志 13 条 `arm_tlb_lookup_hit` 行全部如此），本文件只引用 fault 2 的这一次。`new_pfn << 12 = 0x80a06000`，或上偏移 `0x868` 得有效 PA `0x80a06868`；第 4 位对应 PA 的第 16 位：`0x80a16868 → 0x80a06868`。`event_id=262` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=80a16868`、`after=80a06868`、`contained=0`、`outcome=NoFault`。

### 2.3 TLB 查询与地址翻译

`event_id=260` 的 `tlb_lookup`（tick=237951174969）命中第 4 号 entry，`field=post_lookup`，`before=80a16`、`after=80a06`，`state_after` 的 `pfn=80a06`、`pa=80a06868`。`event_id=261` 的 `tlb_pfn` 记录 `state_before=80a16868`、`state_after=80a06868`、`pa=80a06868`、`field=stuck_at_zero`。`event_id=262` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 237951174969 把错误有效 PA `0x80a06868` 交给 LSU；请求 VA=`0xffffffc008a16868`，未含住。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径：`event_id=263` 的 `lsq_push`（tick=237951175302）记录 `pc=0xffffffc0087b10b0`、`opcode=ldr`、`lq_idx=6`、`sq_idx=-1`、`field=load`，把该 load 登记进 LQ；`event_id=264` 的 `lq_read`（同 tick，`lq_idx=6`、`request_id=373`、VA=`0xffffffc008a16868`）把请求取出并送向 L1D。输入是错误翻译，内部变化是 LSQ 登记与取出，输出是带错误 PA 的访存。本 fault 的祖先上没有 `mem_req`/`lsq_sendfrag`（未发射），因此这两个字段为 N/A；store 侧（`sq_*`）为 N/A。

### 2.5 错误如何经过 cache 和 MSHR

两次 L1D 访问都未命中：`event_id=265`（`cache_access`，tick=237951175302，PA=`0x80a06868`）→ `event_id=266`（`cache_return`，`field=miss`）→ `event_id=267`（`mshr_alloc`，`mshr_id=13`，`cache_line=0x80a06868`，`state_after=mshr_allocated`）；`event_id=268`（tick=237951175635，PA=`0x80a06840`）→ `event_id=269`（`miss`）→ `event_id=270`（`mshr_alloc`，`mshr_id=14`，`cache_line=0x80a06840`）。随后两组真实填充：`event_id=271`（`mshr_fill`，tick=237951248562，`mshr_id=14`、`fill_id=13`、`cache_line=0x80a06840`、`state_after=filled`）→ `event_id=272`（`cache_fill`，`pa=80a06840`）→ `event_id=273`（`mshr_free`，`mshr_id=14`）；`event_id=274`（`mshr_fill`，tick=237951249228，`mshr_id=0`、`fill_id=14`）→ `event_id=275`（`cache_fill`，`pa=80a06840`）→ `event_id=276`（`mshr_free`，`mshr_id=0`）。两组填充把错误行 `0x80a06840` 写入 L1D，错误从本次 load 扩展为缓存内容。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、lq_complete、lq_read、lsq_push、mshr_alloc、mshr_fill、mshr_free、resp、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mem_req、lsq_sendfrag、sq_execute、sq_writeback、sq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=277` 的 `resp`（tick=237951249561，`request_id=373`，原始 `va` 字段记录 PA=`80a06868`）回送数据；`event_id=278` 的 `lq_complete` 完成 `lq_idx=6`（`pa=80a06868`）；`event_id=279` 的 `taint_reg` 把 `arch_reg=1` / `phys_reg=132` 从 `clean` 改为 `tainted`。输入是 cache/MSHR 返回的错误数据，内部变化是污染登记，输出是污染寄存器 132；至此错误越过“存储→CPU”边界。

### 2.7 最终传播终局

L5 终局是 `event_id=280` 的 `errant_commit`：parent=279，tick=237951250227，`dyn_inst_seq=373`，`commit_seq=146`，`pc=0xffffffc0087b10b0`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除：L2 的 `tlb_translate_result` `contained=0`；L3 的 cache/MSHR 把错误行填入；本 fault 的主链上没有 `squash_masked`（该 seed 的 5 条 squash 属于 fault 1/3/6/7/12 等其它链，见第 5 章）；提交点因此首次真实暴露。`chain_end`（event_id=7639，parent=345，tick=558263733777，`outcome=errant_commit_seen`、`contained=1`、`corr=none`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 280，tick 237951250227），`provable_to=L5`，`terminal=full`。运行结局是 **Timeout**：`run.out` 第一条 `CHAOS_DETECT` 为 `layer=None contained=0 tick=237951250227 ptag=2 reason=errant_commit`，随后有若干 `Hardware RAS contained=1 … squash_replay`（属于其它 fault），最后是 tick=558263733777 的 `store_discarded_not_retired`；没有 panic 行，仿真未在预算内正常结束（`oracle_outcome=Timeout`，`exit_code=0`）。因此要同时说：**fault 2 的传播链已完成**（真实 `errant_commit`），**但运行没有正常终止**（Timeout）。注入 tick=237951174969，终局 tick=237951250227，延迟 75258 ticks（cycle 714568093→714568319，226 个 CPU cycle）。F5 的注入统计为 `attempted=226252285 eligible=226252285 injected=13 fires=226252285 no_effect=226252272`，说明绝大多数 eligible 事件因“正确值已等于卡死值”而不产生新注入。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 4 号 DTLB 表项（VPN=`ffffffc008a16`，PFN=`80a16`，AP=2） | PFN→`80a06`（bit4 stuck-at-0） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x868` | PA `80a16868`→`80a06868`，`contained=0` | 有效 PA | 翻译层未含住 |
| LSQ（L3） | 翻译结果 | `lsq_push`（`ldr`，`lq_idx=6`）→`lq_read` | 带错误 PA 的 load | 污点进入 LQ |
| L1D（L3） | PA `80a06868`/`80a06840` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | `mshr_id=13`、`mshr_id=14` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | 两组 `mshr_fill`/`cache_fill`/`mshr_free` | 错误行留在 cache | 错误被持久化 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `lq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | load 数据 | `arch_reg=1/phys_reg=132` clean→tainted | 污染寄存器 132 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染寄存器 132 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=237951174969 的第 4 号 DTLB 命中把 PFN 第 4 位卡死为 0，有效 PA 由 `0x80a16868` 变为 `0x80a06868`；翻译层记录改变却 `contained=0`，`ldr`（`lq_idx=6`）经 `lsq_push`/`lq_read` 带着错误 PA 进入 L1D，两次相邻访问（`…868`/`…840`）均 miss 并分配 `mshr_id=13/14`，两组 `mshr_fill`→`cache_fill`→`mshr_free`（tick=237951248562/237951249228）把错误行写入缓存；`resp`、`lq_complete`、`taint_reg`（`arch_reg=1`/`phys_reg=132`）依次完成，最终在 tick=237951250227 由 `errant_commit`（`dyn_inst_seq=373`，`commit_seq=146`）收口，距注入 75258 ticks；链完整走到 L5，但运行以 Timeout 收场。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

F5 触发器：`attempted=226252285 eligible=226252285 injected=13 fires=226252285 no_effect=226252272`；`stats.txt`：`numFaultsInjected=13`；流内 `inj` 13 条；权威报告 13 个 fault：三方一致。代表故障 fault 2 的卡死值被真实读取（`tlb_lookup` 读出 `0x80a06`）并消费（`lq_read`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此是 activated。`no_effect=226252272` 是 F5 的正常现象：多数命中事件的正确值本来就等于卡死值，不产生新的有效注入；本文件不把它当失败。

### 3.2 故障传播类型

**地址型**（错误物理地址）传播：卡死的是 PFN 的第 4 位，VA/偏移/权限字段不变；有效 PA 由 `0x80a16868` 变为 `0x80a06868`。没有控制状态或时序型证据；请求身份 `request_id=373` 在祖先上保持。由于是 F5，故障不是“一次性位翻转”，而是对该 run 内每次命中都施加同一 `Mask: 0x10` 的卡死掩码；本链只展示 fault 2 这一次被下游消费的实例。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=262` 的 `tlb_translate_result`（`contained=0`）：翻译层记录 PA 改变却放行。`event_id=263` 的 `lsq_push` 是把请求固着到 `lq_idx=6` 的执行落点；`event_id=272`/`275` 的 `cache_fill` 是对后续访问也生效的升级点（错误行进入 cache）。

### 3.4 检测与掩蔽机制

翻译层可检测 `effective_pa_changed`（本 fault `contained=0`，未阻断）；L1D/MSHR 无地址校验，并已把错误行填入；L4 的 RAS 重放在本 fault 的祖先上没有出现（该 seed 的 5 条 `squash_masked` 属于 fault 1/3/6/7/12 等）；提交点首次暴露。盲区与 F2 样本同类：翻译层可见但不阻断、cache 无地址校验、本故障未触发重放。F5 的掩码持续性意味着同一错误在同一 run 内可能反复出现，但本链只证明 fault 2 这一条。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 280，`contained=0`、`outcome=errant_commit`），运行结局为 Timeout；权威 `terminal=full`。因此不是 Masked/Contained；也不因 Timeout 而抹掉 L5。本实验没有应用级输出 oracle，无法证明静默错误数据，故不称 SDC；可证结论是“卡死导致错误地址、错误行入 cache、错误提交真实发生”，最终数据正确性无法判定。

### 3.6 与同 RunID 其他 seed 的关系

同 RunID：seed2 的代表故障是 fault 1（`stuck_at_one`，mask `0x4`，VA=`0xffffff8001362700`，PFN `81362→81366`，PA `81362700→81366700`，7 次注入）；seed3 的代表故障是 fault 2（`stuck_at_zero`，mask `0x1000`，VA=`0xffffff807fbce090`，PFN `ffbce→febce`，PA `ffbce090→febce090`，9 次注入）。本 seed 的代表故障是 fault 2（stuck_at_zero，mask `0x10`，VA=`0xffffffc008a16868`，PFN `80a16→80a06`，PA `80a16868→80a06868`，13 次注入）。三者的卡死位、地址、注入次数均不同；共同点仅是注入站点与 Timeout 结局，不互相引用字段。

## 4. 完整主链事件表

下表按 event 280 的祖先顺序排列（`259→260→…→280`）。`mask` 只在 `inj` 行给出（`0x10`）；主链 22 个事件，无需折叠。

<!-- witness=280 representative_fault=2 ancestors=['259', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '270', '271', '272', '273', '274', '275', '276', '277', '278', '279', '280'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 259 | — | 237951174969 | — | inj | L0 | CHAOSArmTLB | 2 | origin | 373 | 373 | ffffffc008a16868 | — | — | — | 80a16 | 80a06 | 80a16 | 80a06 | 0x10 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=373 的地址翻译即将使用它 | 被改写后的 PFN=80a06（VA=ffffffc008a16868） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 260 | 259 | 237951174969 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 2 | seq_primary | 373 | 373 | ffffffc008a16868 | — | — | — | 80a16 | 80a06 | 80a16 | 80a06 | — | vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868 | vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a06;ap=2;mtype=2;page_size=1000;pa=80a06868 | — | — | — | — | DTLB 命中 entry_index=4（way=-1），读取 pfn 字段 | 命中读出 pfn=80a06，AP=2，page_size=1000，PA=80a06868 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 261 | 260 | 237951174969 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 2 | seq_primary | 373 | 373 | ffffffc008a16868 | 80a06868 | — | — | 80a16 | 80a06 | 80a16 | 80a06 | — | 80a16868 | 80a06868 | — | — | — | — | lookup 得到的 PFN=80a16 | PFN 记录为 80a06，翻译 PA=80a06868 | L2：翻译结果开始使用错误 PFN |
| 4 | 262 | 261 | 237951174969 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 2 | seq_primary | 373 | 373 | ffffffc008a16868 | 80a06868 | — | — | — | — | 80a16868 | 80a06868 | — | vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868 | vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a06;ap=2;mtype=2;page_size=1000;pa=80a06868 | 0 | — | NoFault | — | PFN=80a16 与页内偏移组合 | 有效 PA 80a16868→80a06868；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 263 | 262 | 237951175302 | 333 | lsq_push | L3 | LSQ | 2 | seq_primary | — | 373 | ffffffc008a16868 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ldr 指令 dyn_inst_seq=373 进入 LSQ | lq_idx=6 / sq_idx=-1，field=load，VA=ffffffc008a16868 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 6 | 264 | 263 | 237951175302 | 0 | lq_read | L3 | LQ | 2 | seq_primary | 373 | 373 | ffffffc008a16868 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=6 的 load 请求（VA=ffffffc008a16868） | request_id=373 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 7 | 265 | 264 | 237951175302 | 0 | cache_access | L3 | L1D | 2 | addr_fallback | 373 | 373 | ffffffc008a16868 | 80a06868 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=373 访问 L1D（PA=80a06868） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 8 | 266 | 265 | 237951175302 | 0 | cache_return | L3 | L1D | 2 | addr_fallback | 373 | 373 | — | 80a06868 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=80a06868 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 9 | 267 | 266 | 237951175302 | 0 | mshr_alloc | L3 | MSHR | 2 | addr_fallback | 373 | 373 | — | — | 80a06868 | 13 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=80a06868 | mshr_id=13 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 10 | 268 | 267 | 237951175635 | 333 | cache_access | L3 | L1D | 2 | addr_fallback | 373 | 373 | ffffffc008a16868 | 80a06840 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=373 访问 L1D（PA=80a06840） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 11 | 269 | 268 | 237951175635 | 0 | cache_return | L3 | L1D | 2 | addr_fallback | 373 | 373 | — | 80a06840 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=80a06840 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 12 | 270 | 269 | 237951175635 | 0 | mshr_alloc | L3 | MSHR | 2 | addr_fallback | 373 | 373 | — | — | 80a06840 | 14 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=80a06840 | mshr_id=14 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 13 | 271 | 270 | 237951248562 | 72927 | mshr_fill | L3 | MSHR | 2 | addr_fallback | 373 | 373 | — | — | 80a06840 | 14 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=14 的数据返回（fill_id=13） | state_after=filled，cache_line=80a06840 | L3：MSHR 完成填充 |
| 14 | 272 | 271 | 237951248562 | 0 | cache_fill | L3 | L1D | 2 | addr_fallback | 373 | 373 | — | 80a06840 | 80a06840 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=13 的填充数据 | cache_line=80a06840 进入 L1D | L3：错误行进入 cache |
| 15 | 273 | 272 | 237951248562 | 0 | mshr_free | L3 | MSHR | 2 | addr_fallback | 373 | 373 | — | — | 80a06840 | 14 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=14 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 16 | 274 | 273 | 237951249228 | 666 | mshr_fill | L3 | MSHR | 2 | addr_fallback | 373 | 373 | — | — | 80a06840 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=14） | state_after=filled，cache_line=80a06840 | L3：MSHR 完成填充 |
| 17 | 275 | 274 | 237951249228 | 0 | cache_fill | L3 | L1D | 2 | addr_fallback | 373 | 373 | — | 80a06840 | 80a06840 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=14 的填充数据 | cache_line=80a06840 进入 L1D | L3：错误行进入 cache |
| 18 | 276 | 275 | 237951249228 | 0 | mshr_free | L3 | MSHR | 2 | addr_fallback | 373 | 373 | — | — | 80a06840 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 19 | 277 | 276 | 237951249561 | 333 | resp | L4 | L1D→LSU | 2 | seq_primary | 373 | 373 | 80a06868 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=373） | 响应数据返回（该事件 va 字段记录 PA=80a06868） | L4：污染数据返回处理器 |
| 20 | 278 | 277 | 237951249561 | 0 | lq_complete | L4 | LQ | 2 | seq_primary | 373 | 373 | ffffffc008a16868 | 80a06868 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应数据 request_id=373 | LQ 条目 lq_idx=6 完成，PA=80a06868 | L4：load 写回 LQ，错误值即将写寄存器 |
| 21 | 279 | 278 | 237951249561 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 2 | seq_primary | 373 | 373 | 80a06868 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=373） | arch_reg=1 / phys_reg=132：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 22 | 280 | 279 | 237951250227 | 666 | errant_commit | L5 | ROB/Commit | 2 | taint_prop | — | 373 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=373，commit_seq=146） | contained=0，outcome=errant_commit，PC=ffffffc0087b10b0 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`tlb_lookup`/`tlb_pfn` 的 `before/after` 是 PFN；`tlb_translate_result` 的 `before/after` 是 PA；两组填充的 `fill_id=13/14`、`mshr_id=14/0` 照原始字段；`resp` 的 `va` 字段保存 PA。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 8327 个事件、13 个故障。fault 2 的事件集合只有 28 个（主链 22 个 + 6 个旁支），是本批样本中最“干净”的链之一。

1. **污染消费（`consumer` 5 条）**：最早 `event_id=281`（parent=279，tick=237951250560，`dyn_inst_seq=388`，`arch_reg=1`、`phys_reg=132`），最晚 `event_id=345`（parent=318，tick=237951815661，`dyn_inst_seq=618`，`arch_reg=30`、`phys_reg=179`）。它们读取污染寄存器，但没有成为 event 280 的祖先（event 280 直接消费 event 279）。
2. **生命周期收口（1 条）**：`event_id=7639`（parent=345，tick=558263733777，`outcome=errant_commit_seen`、`contained=1`、`corr=none`）。
3. **其它 12 个故障**：fault 1 的路径 `0,1,2,5,74,343` 被判 `detected_contained`；fault 3/6/7/12 也各有 L4 含住；fault 4/5/8/9/10/11/13 多为 `provable_to_L4_then_unknown`。这些故障各自有注入点/VA/掩码（同一 run 共用 `Mask: 0x10`），不并入 fault 2 的链；本文件只在第 6 章引用其数量。

旁支对 SDC 诊断的影响：fault 2 的污染只被 5 个 consumer 读取，扩散面很小；它没有 `request_fork`、没有 `squash_masked`、没有 `pf_*`，因此本链的结论不会被旁支改变。该 seed 其它故障的含住不能覆盖 fault 2 的 `errant_commit`。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=280，tick=237951250227，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Timeout`（`run.out` 无 panic；最后一批 `CHAOS_DETECT … store_discarded_not_retired` 于 tick=558263733777） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=13`，与触发器 injected=13、inj 事件 13 条一致） |
| conservation | `ok`（consumer_summary：emitted=3091、suppressed=107419、logical_total=110510、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=8327` 与实际解析事件数 8327 相同；injected/stats/inj 均为 13 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| 判定 | **PASS** |

判定说明：传播终局（fault 2 的 event 280）与运行结局（Timeout）分别陈述；Timeout 是非正常终止，不抹除已证 L5；`chain_end` 7639 未被当作 L5。代表故障按 escape-first 选出（fault 2 唯一 `full`），fault 1 的含住不被用来覆盖它。15 项一致性检查全部通过。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `478530d46202e0d935d8876b2c7ff127a3e5830d9a159ff66d29c709f89fa7ab` | 394904 | 2026-10-27T02:41:30 |
| `chain_report.json` | `535c63546e52ae889d7e3b239b02472921bddf510ee1fad567219cad9086d60e` | 2617687 | 2026-10-27T02:41:31 |
| `run.out` | `811b070ab12af7a53264530ece4c07a7e0fe2241d2899a230ed49d14a808cce0` | 3302 | 2026-10-27T02:41:31 |
| `run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` | 129 | 2026-10-27T02:41:31 |
| `stats.txt` | `b37a0b817a51a21b85a210e3d81405b60ae96995e37f0c5ee5f1070a852dfdfa` | 380859 | 2026-10-27T02:41:31 |
| `armtlb_injections.log` | `60c06b196c5c01badb704b9d4b0e9ebb207530fc79ace806baa874cc67f6b94d` | 2772 | 2026-10-27T01:11:42 |
| manifest `manifest.json` | `edc14fcff3c1a38574b01efff323627fd35ed08016ad70811e7e257a707ed504` | 1438 | 2026-10-27T02:41:33 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_zero --tlb_lsu_tier F5 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T03-F5-W4 --prop_sample_run_id s1`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1 --cells T03-F5-W4 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `runs/lsu/r6_n7_T03-F5-W4_s1.RUN1_STALE_REPORT/T03-F5-W4/seed1` — **REVIEW_REQUIRED（同/未知二进制但证据与权威不同，且无分类身份证据；不得按名字清理）**
- `runs/lsu/r6_tlb_I_T03-F5-W4/T03-F5-W4/seed1` — **INTERRUPTED（无 .done/.exit_code 标记）**

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
