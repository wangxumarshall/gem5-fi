# T02-F2-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T02-F2-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T02`）
- fault model：PPN 内同时翻转 2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`双比特翻转`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F2 — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier：`F2`；effective tier：`F2`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`）
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T02-F2-W4 --prop_sample_run_id s3`
- source head：N/A（manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同二进制构建源）
- binary source head：N/A（manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同二进制构建源）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/manifest.json`（SHA-256 `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9`；run 根 manifest（seed 字段=3，artifacts 尺寸对应最后一个 seed；不按它推断本 seed 的逐 seed 事实）；manifest.status=`FINISHED`，manifest.exit_code=`0`，manifest.seed=`3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`0`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：358302（与 `chain_report.event_count` 相同）
- fault_id 数量：228（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 的代表故障由 escape-first 规则选出为 `fault_id=1`（该 seed 共 228 个真实故障，其中仅 fault 1 走到 `full`；其余为含住或只到 L4 的未知终局）。终局见证是 `errant_commit`（event_id=96），其单祖先链为 `0 → 1 → 2 → 3 → 4 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 68 → 69 → 70 → 96`，共 16 个事件。这条链走的是 **store** 路径（`sq_execute`/`sq_writeback`/`sq_complete`），与同 RunID 的 seed1（load 路径）不同；本文件只使用 seed3 自己的事实。

### 2.1 故障注入前的正常状态

注入目标是 DTLB 第 21 号 entry（`event_id=1` 的 `entry_index=21`、`way=-1`）。`state_before` 为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950`：VPN=`0xffffffc009483`，ASID=206，`valid=1`、`global=1`，权限 `ap=0`，4 KiB 页，正常 PFN=`0x81d75`。触发翻译的访存指令 `dyn_inst_seq=520906`（`request_id=520906`）使用 VA=`0xffffffc009483950`；页内偏移 `0x950`，正常物理地址 `(0x81d75 << 12) | 0x950 = 0x81d75950`，与 `state_before` 的 `pa` 相同。该指令在本 seed 的后续事件里被证明是 store（`sq_idx=54806`、`sq_writeback` → `sq_complete`）。

### 2.2 故障具体如何注入

注入组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=238095582084（cycle=715001748），`event_id=0`，`fault_id=1`，`request_id=520906`，`field=bit_flip`，FaultType=`bit_flip`，`corr=origin`。`armtlb_injections.log` 记录：
`Tick: 238095582084, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483950, old_pfn: 0x81d75, new_pfn: 0x20200000081d75, FaultType: bit_flip, Mask: 0x20200000000000`。
`before=0x81d75`、`after=0x20200000081d75`，异或 `0x20200000000000`，即翻转 PFN 的第 45 位与第 53 位；同为 T02 双比特模型，权限位与页大小字段未动。

数值上：`new_pfn << 12 = 0x20200000081d75000`，64 位截断后第 53 位（左移 12 位后落在第 65 位）被丢掉，得到 `0x200000081d75000`；或上页内偏移 `0x950` 得 `0x200000081d75950`。因此第 53 位对有效 PA 没有贡献，第 45 位使有效 PA 的第 57 位由 0 变 1：`0x81d75950 → 0x200000081d75950`。`event_id=3` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=81d75950`、`after=200000081d75950`、`contained=0`、`outcome=NoFault`，说明翻译层没有含住。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=238095582084）命中第 21 号 entry，`field=post_lookup`，`before=81d75`、`after=20200000081d75`，`state_after` 的 `pfn=20200000081d75`、`pa=200000081d75950`。`event_id=2` 的 `tlb_pfn` 把命中值写成翻译用的 PFN（`state_before=81d75950`、`state_after=200000081d75950`，`pa=200000081d75950`）。`event_id=3` 的 `tlb_translate_result` 是翻译结论：`effective_pa_changed`、`contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 238095582084 把错误有效 PA `0x200000081d75950` 连同 `request_id=520906` 交给 LSU；请求 VA=`0xffffffc009483950`，请求 PA=`0x200000081d75950`，未含住。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 走 **store** 路径：`event_id=4` 的 `sq_execute`（tick=238095582084，`sq_idx=54806`，VA=`0xffffffc009483950`，`state_before=issued`）把该 store 送入执行；它的输入是错误翻译，内部变化是 store 操作开始执行，输出是写回阶段的地址包。`event_id=11` 的 `sq_writeback`（tick=238095585414）记录 `sq_idx=54806`、`pa=200000081d75950`、`state_after=packet_built`，即写回阶段用错误 PA 构造了数据包。随后 `event_id=68` 的 `resp`、`event_id=69` 的 `taint_reg`、`event_id=70` 的 `sq_complete`（`sq_idx=54806`、`state_after=completed`）完成写路径闭环。本 fault 的祖先上没有 `lsq_push`/`lq_read`/`mem_req`/`lsq_sendfrag`（这些 kind 在同 seed 的其它 fault 或旁支出现），因此 load 侧字段为 N/A；可证的 store 事实是 `sq_execute → sq_writeback → … → sq_complete` 全部使用同一个错误 PA。

### 2.5 错误如何经过 cache 和 MSHR

store 的两次 cache 访问都未命中：`event_id=12` 的 `cache_access`（tick=238095585414，PA=`0x200000081d75950`）后接 `event_id=13` 的 `cache_return`（`field=miss`），并分配 `mshr_id=3`（`event_id=14`，`cache_line=0x200000081d75950`，`state_after=mshr_allocated`）；第二次访问 `event_id=15`（tick=238095585747，PA=`0x200000081d75940`）同样 `miss`（`event_id=16`），分配 `mshr_id=4`（`event_id=17`，`cache_line=0x200000081d75940`，`state_after=mshr_allocated`）。两次 PA 仅低位 `0x10` 之差，仍是同一错误 4 KiB 页内的相邻子访问。与 seed1 类似，本 fault 在 `event_id=17` 之后直接到 `event_id=68` 的 `resp`，祖先上没有 `mshr_fill`/`cache_fill`/`mshr_free`；因此“错误行被填进 cache”在本链上不可证（N/A），只能证明两次错误行都已在 MSHR 中分配并等待数据。fault 1 的全部 2791 个事件中都不含 fill/free 事件；流内确有 68 组 fill/free，但它们属于其它故障（见第 5 章），不能拼进本链。

本链出现的 kind 集合为 `cache_access、cache_return、errant_commit、inj、mshr_alloc、resp、sq_complete、sq_execute、sq_writeback、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mshr_fill、cache_fill、mshr_free、lsq_push、mem_req、lsq_sendfrag、lq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=68` 的 `resp`（tick=238095693972，`request_id=520906`，`va=200000081d75950`，原始字段把 PA 写进 `va`）把数据回送；`event_id=69` 的 `taint_reg`（同 tick）把状态从 `clean` 改成 `tainted`；`event_id=70` 的 `sq_complete`（同 tick，`sq_idx=54806`，`state_after=completed`）完成 SQ 条目。需要注意：event 69 的原始记录**没有**填写 `arch_reg`/`phys_reg`（两个字段为空），因此本文件不能指名具体被污染的寄存器，只能证明“该 store 的返回值已被登记为 tainted”。这仍然是存储→CPU 的边界事件：污染集从存储响应扩展到指令结果；`sq_complete` 之后，该 store 在架构上完成，错误地址写路径已走完。

### 2.7 最终传播终局

L5 真实终局是 `event_id=96` 的 `errant_commit`：parent=70，tick=238095695637，`dyn_inst_seq=520923`，`commit_seq=394130`，`pc=0xffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。它证明被污染的 store 结果在提交点被消费并以错误状态提交。未被提前消除的原因是：L2 的 `tlb_translate_result` 记录 `effective_pa_changed` 但 `contained=0`；L3 的 cache/MSHR 只按给定 PA 工作，没有地址校验；L4 上该 store 没有遇到 `squash_masked`（fault 1 的全部事件都不含该 kind；同 seed 流内的 175 条 `squash_masked` 全部属于其它故障），所以提交是第一次真实暴露。`chain_end`（event_id=312448，parent=2454，tick=3515175146493，`outcome=errant_commit_seen`、`contained=1`、`corr=none`）只是流收口，不充当 L5。

### 2.8 从传播终局到系统表现

传播终局是 `errant_commit`（event 96，tick 238095695637），`provable_to=L5`，权威 `terminal=full`。运行结局是 **Timeout**：`run.out` 没有 panic 行，最后一批输出是 tick=3515175146493 的 `CHAOS_DETECT: layer=Hardware RAS contained=1 … reason=store_discarded_not_retired`（本 seed 共 255 条 `CHAOS_DETECT`，最后几条同 tick），仿真没有在预算内正常结束；权威报告的 `oracle_outcome=Timeout`、`exit_code=0`。因此必须同时说两件事：**传播链本身已经完成**（真实 `errant_commit` 已发生），**但这次运行没有正常终止**（Timeout），二者不互相抹除。注入 tick=238095582084，终局 tick=238095695637，传播延迟 113553 ticks（cycle 715001748→715002089，341 个 CPU cycle）。因果链为：错误 PFN→错误 PA `0x200000081d75950`→store 写路径→MSHR/响应→taint_reg/sq_complete→提交点 `errant_commit`（dyn_inst_seq=520923）；Timeout 是运行层面的终止方式，不是链的终局。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 21 号 DTLB 表项（PFN=`81d75`） | PFN→`20200000081d75`（bit45、bit53） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x950` | PA `81d75950`→`200000081d75950`，`contained=0` | 有效 PA | 翻译层未含住 |
| SQ（L3） | 错误翻译（`sq_idx=54806`） | `sq_execute`（issued）→`sq_writeback`（packet_built） | 携带错误 PA 的数据包 | 污点进入 store 执行 |
| L1D（L3） | PA `…950`/`…940` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | 分配 `mshr_id=3`、`mshr_id=4` | 等待响应 | 错误行被跟踪 |
| L1D→LSU（L4） | MSHR 完成 | `resp` 返回数据 | `taint_reg`/`sq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | store 返回数据 | `clean→tainted`（`arch_reg`/`phys_reg` 未填） | 污染状态 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染结果 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可概括为：tick=238095582084 的一次 TLB 命中把 PFN 的第 45、53 位同时翻转，第 53 位在 64 位左移 12 位后被截掉、无效，第 45 位把有效 PA 从 `0x81d75950` 推到 `0x200000081d75950`；L2 的 `tlb_translate_result` 记录 `effective_pa_changed` 但 `contained=0`，store 经 `sq_execute`（`sq_idx=54806`）与 `sq_writeback`（`packet_built`，PA=`0x200000081d75950`）进入 L1D，两次相邻访问（`…950` 与 `…940`）均 miss 并分配 `mshr_id=3/4`，`resp` 回送后 `taint_reg`（`clean→tainted`，寄存器字段未填）与 `sq_complete` 完成写路径，最终在 tick=238095695637 形成 `errant_commit`（`dyn_inst_seq=520923`，`commit_seq=394130`），距注入 113553 ticks；链完整走到 L5，但运行以 Timeout 而非正常结束收场。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER` 记录 `attempted=22963727 eligible=22963727 injected=228`；`stats.txt` 为 `numFaultsInjected=228`；流内 `inj` 事件 228 条；权威报告登记 228 个 fault：三方一致。代表故障 fault 1 的注入值被真实读取并消费：`event_id=1` 的 `tlb_lookup` 读出故障 PFN，`event_id=3` 给出错误 PA，`event_id=12/15` 的 L1D 访问与 `event_id=68/69/70` 的响应/污染/完成都使用了该 PA，最终 event 96 提交。因此 fault 1 是 activated。该 seed 另有 227 个故障，本次不逐个展开；它们的终局分布见 3.6 与第 5 章。

### 3.2 故障传播类型

这是**地址型**（错误物理地址）传播：VA 与页内偏移不变，PFN 被改写为同一页内的错误值（`0x20200000081d75` 的有效低位部分）。权限字段（`ap=0`）未变，控制流未被改写（提交的 PC 由程序决定），也不是时序注入。由于是 store，错误地址会进入写路径，但它仍然属于“地址错”而不是“数据位错”——数据本身没有翻转，错的是落点。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（tick=238095582084）：它记录了 PA 改变却 `contained=0`，等于把错误地址正式交给 LSU；此后 `event_id=4` 的 `sq_execute` 把该地址绑定到 `sq_idx=54806` 并送入执行，`event_id=11` 的 `sq_writeback` 用错误 PA 构造 `packet_built`。从当前结构看，event 3 之后已没有机制能在本链上把地址改回；event 4 是不可逆点的执行落点。event 12/15 的 cache 访问是后果，而不是新的不可逆点。

### 3.4 检测与掩蔽机制

翻译层具备“看见 PA 变化”的能力（`effective_pa_changed`），但本 seed `contained=0`，未阻断；cache/MSHR 没有地址校验；L4 的 RAS 重放在本 fault 的祖先上没有出现（尽管同 seed 存在 175 条 `squash_masked`，它们属于其它 fault 链/旁支）；提交点 `errant_commit` 是首次真实暴露。观察到的盲区与 seed1 相同：翻译层能检测却不阻断，后续层级只负责“访问是否命中/是否需要重放”，不对“PA 是否被故障改写”负责。与 seed1 不同的是本 seed 走 store 路径，错误落点直接进入写路径，直到提交才被记录为错误提交。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 96，`contained=0`、`outcome=errant_commit`、`detection_layer=L5`），所以不是 Masked/Contained；权威 `terminal=full`。但运行结局是 Timeout：仿真没有在预算内正常结束，因此不能把本 seed 说成“正常完成的崩溃”或“已确认的 SDC”。本实验没有应用级输出 oracle，无法证明错误写结果被外部观测为静默错误；只能证明错误地址与错误提交是真实的。因此本 seed 归类为“真实 L5 + 非正常终止（Timeout）”，不称 SDC；最终数据正确性无法判定。Timeout 不抹除已证 L5。

### 3.6 与同 RunID 其他 seed 的关系

同 RunID 的 seed1 注入 VA=`0xffffff8001362708`、PFN `81362→800400000081362`（bit46、bit59），有效 PA `81362708→400000081362708`，load 路径，终局 `errant_commit` event 20，结局 Crash；seed2 注入 VA=`0xffffffc009483960`、PFN `81d75→800000000081d77`（bit1、bit59），有效 PA `81d75960→81d77960`，终局 L4 `squash_masked` event 68 含住、L5=N/A，结局 Crash。本 seed 的注入地址/掩码、路径（store）与终局（event 96）都与它们不同；三者只在“注入站点相同”这一点上一致，不能互相引用字段。

## 4. 完整主链事件表

下表按 event 96 的祖先顺序排列（`0→1→2→3→4→11→12→13→14→15→16→17→68→69→70→96`）。`mask` 只在 `inj` 行给出（`0x20200000000000`）；主链 16 个事件，无需折叠；同流的 `consumer`/`request_fork`/`pf_*` 等都在旁支。

<!-- witness=96 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '11', '12', '13', '14', '15', '16', '17', '68', '69', '70', '96'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238095582084 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 20200000081d75 | 81d75 | 20200000081d75 | 0x20200000000000 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=520906 的地址翻译即将使用它 | 被改写后的 PFN=20200000081d75（VA=ffffffc009483950） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 238095582084 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 20200000081d75 | 81d75 | 20200000081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20200000081d75;ap=0;mtype=2;page_size=1000;pa=200000081d75950 | — | — | — | — | DTLB 命中 entry_index=21（way=-1），读取 pfn 字段 | 命中读出 pfn=20200000081d75，AP=0，page_size=1000，PA=200000081d75950 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 238095582084 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 200000081d75950 | — | — | 81d75 | 20200000081d75 | 81d75 | 20200000081d75 | — | 81d75950 | 200000081d75950 | — | — | — | — | lookup 得到的 PFN=81d75 | PFN 记录为 20200000081d75，翻译 PA=200000081d75950 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 238095582084 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 200000081d75950 | — | — | — | — | 81d75950 | 200000081d75950 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20200000081d75;ap=0;mtype=2;page_size=1000;pa=200000081d75950 | 0 | — | NoFault | — | PFN=81d75 与页内偏移组合 | 有效 PA 81d75950→200000081d75950；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 238095582084 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | SQ 条目 sq_idx=54806（state_before=issued） | 执行阶段生成 store 操作（VA=ffffffc009483950） | L3：store 进入执行，地址来自故障翻译 |
| 6 | 11 | 4 | 238095585414 | 3330 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 520906 | — | 200000081d75950 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | SQ 条目 sq_idx=54806 的执行结果 | packet_built，PA=200000081d75950 | L3：store 数据包成形，携带错误地址 |
| 7 | 12 | 11 | 238095585414 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 200000081d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=520906 访问 L1D（PA=200000081d75950） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 8 | 13 | 12 | 238095585414 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 200000081d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=200000081d75950 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 9 | 14 | 13 | 238095585414 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 200000081d75950 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=200000081d75950 | mshr_id=3 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 10 | 15 | 14 | 238095585747 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 200000081d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=520906 访问 L1D（PA=200000081d75940） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 11 | 16 | 15 | 238095585747 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 200000081d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=200000081d75940 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 12 | 17 | 16 | 238095585747 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 200000081d75940 | 4 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=200000081d75940 | mshr_id=4 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 13 | 68 | 17 | 238095693972 | 108225 | resp | L4 | L1D→LSU | 1 | seq_primary | 520906 | 520906 | 200000081d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=520906） | 响应数据返回（该事件 va 字段记录 PA=200000081d75950） | L4：污染数据返回处理器 |
| 14 | 69 | 68 | 238095693972 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 520906 | 520906 | 200000081d75950 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=520906） | arch_reg= / phys_reg=：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 15 | 70 | 69 | 238095693972 | 0 | sq_complete | L4 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | SQ 条目 sq_idx=54806 的写回完成 | state_after=completed，PA/VA=ffffffc009483950 | L4：store 完成，错误地址已写入存储路径 |
| 16 | 96 | 70 | 238095695637 | 1665 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 520923 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=520923，commit_seq=394130） | contained=0，outcome=errant_commit，PC=ffffffc0087b27c4 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`before/after` 为原始值；`taint_reg`（event 69）的 `arch_reg`/`phys_reg` 在原始流中为空，表中如实为 `—`；`sq_execute` 只有 `state_before=issued`，`sq_writeback` 只有 `state_after=packet_built`，另一侧字段为 `—`，不补造。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 358302 个事件、228 个真实故障。fault 1 有 2791 个事件，主链 16 个，其余 2775 个是旁支；其余 227 个故障的事件（约 35.5 万条）属于独立故障链，不并入本链。

1. **请求分叉（`request_fork` 309 条）**：`event_id=4294967296`（parent=3）把请求 520906 分叉出 520896（`bridge_reason=addr_fallback_broadcast`、`shared_addr=0x200000081d75000`、`shared_size=0x1000`）；另有 11 条挂在主链 `mshr_alloc`（event 17）上；其余 297 条挂在主链 `taint_reg`（event 69）上，最晚一条 `event_id=4294967604`（parent=69，tick=238099758570，new_request_id=522407）。它们都是同页内由污染值派生的再访问，没有一条成为 event 96 的祖先。
2. **污染消费（`consumer` 22 条、`taint_reg` 322 条）**：consumer 覆盖 `arch_reg` 29/30 等，最早 tick=238095695637（event 97，dyn_inst_seq=520926），最晚 tick=238099526136（event 2454，dyn_inst_seq=522339），但没有进入主链；它们证明污染结果被少量指令继续消费。
3. **预取事件（`pf_queue` 97、`pf_issue` 84、`pf_demand` 261）**：最早 `pf_queue` event_id=694（parent=675，tick=238097127204，`pf_request_id=4294967297`），最晚 `pf_demand` event_id=2477（tick=238099758903，request_id=522407）。这些是同一错误页被预取器访问的记录，说明错误地址扩散到预取路径；它们不在主链祖先上，不能当作 L3 中间步，也不改变终局。
4. **MSHR/填充事件**：fault 1 的 2791 个事件里没有任何 `mshr_fill`/`cache_fill`/`mshr_free`；流内 68 组 fill/free（以及 175 条 `squash_masked`）都属于其它 227 个故障链。因此本链不以“填充/含住”作任何断言。
5. **生命周期收口（1 条）**：`event_id=312448`（parent=2454，tick=3515175146493，`outcome=errant_commit_seen`、`contained=1`、`corr=none`），仅收口。
6. **其它 227 个故障**：例如 fault 2 的路径 `2481,2482,2483,2485,2506,3335` 被判 `detected_contained`；fault 3–228 多为 `provable_to_L4_then_unknown`（见报告 `faults` 表）。它们各有自己的注入点/VA/掩码，不属于本文件的主链；本文件只在 3.1 与第 6 章引用其数量。

这些旁支对 SDC 诊断的影响是：它们显示错误地址被同页访问与预取器多次消费（309 条 fork、22 个 consumer、261 条 pf_demand），但终局仍由 event 96 证明；fault 1 的整个事件集合不含 `squash_masked`，因此不能把本故障说成“被含住”；流内其它故障的 175 条 `squash_masked` 与本链无关。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full`（权威 `chain_report.json`） |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=96，tick=238095695637，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Timeout`（`run.out` 无 panic，最后一组 `CHAOS_DETECT … store_discarded_not_retired` 于 tick=3515175146493；仿真未在预算内正常结束） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=228`，与触发器 injected=228、inj 事件 228 条一致） |
| conservation | `ok`（consumer_summary：emitted=1296、suppressed=90965003、logical_total=90966299、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=358302` 与实际解析事件数 358302 相同；injected/stats/inj 均为 228 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| 判定 | **PASS** |

判定说明：传播终局（event 96 的真实错误提交）与运行结局（Timeout）分别陈述；Timeout 是非正常终止，但不能据此把 L5 改写成 Unknown 或 Masked，也不能把 `chain_end` 当终局。`chain_end` 312448 的 `contained=1` 是生命周期字段，未被使用。所有 15 项一致性检查均通过：事件都在本 seed 流内、父子先于子、tick 单调、地址/掩码/corr/fault_id 均取自本 seed、终局与权威报告一致（`full`，L5）。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed3`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `937b99606969ce077c93f110215f83a17ed78c93a78671550c6f3d66c7905063` | 11390937 | 2026-10-25T21:04:11 |
| `chain_report.json` | `ca08630e64dad7470ae30ad21dafa1e6c8d321b5362688b3a6929327d9858693` | 1437808 | 2026-10-25T21:04:36 |
| `run.out` | `9fdfc3fd1fbca48fe971bd27771a42c849ecbede2d49780ee8e82e5a50ad2a93` | 26601 | 2026-10-25T21:04:13 |
| `run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` | 129 | 2026-10-25T21:04:13 |
| `stats.txt` | `780eb40447fcbd56b5bcb2952807061b268f13bc56659d30af6368fec12cd76e` | 391769 | 2026-10-25T21:04:12 |
| `armtlb_injections.log` | `f539628d2f134f5816f78e3a9ee2db9dc01dca6b34f95dbc86dee3f1f6fb0c8d` | 48117 | 2026-10-25T21:04:09 |
| manifest `manifest.json` | `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9` | 1778 | 2026-10-25T21:04:38 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | N/A（manifest 无该字段） | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T02-F2-W4 --prop_sample_run_id s3`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3 --cells T02-F2-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `runs/lsu/r6_p1_T02-F2-W4/T02-F2-W4/seed3` — **INTERRUPTED（无 .done/.exit_code 标记）**
- `runs/lsu/r6_w1_T02-F2-W4/T02-F2-W4/seed3` — **INTERRUPTED（无 .done/.exit_code 标记）**

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
