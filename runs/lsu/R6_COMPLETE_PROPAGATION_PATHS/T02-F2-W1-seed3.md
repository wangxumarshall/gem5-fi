# T02-F2-W1 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T02-F2-W1`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T02`）
- fault model：PPN 内同时翻转 2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`双比特翻转`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F2 — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier：`F2`；effective tier：`F2`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`）
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`；矩阵标签写 MiBench，但原始 run.out 的 `--readfile` 指向 `tlb_probe.rcS`；两者不一致处如实保留，不推断。
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3/T02-F2-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T02-F2-W1 --prop_sample_run_id s3`
- source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3/T02-F2-W1/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3/manifest.json`（SHA-256 `f77b28677f274ad98525df52b98937be433f59fc6286a4cda22768320f8870d2`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：12792（与 `chain_report.event_count` 相同）
- fault_id 数量：5（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 的代表故障是 `fault_id=1`（五个故障中只有它到达 `full`）。终局见证是 `errant_commit`（event_id=97），其单祖先为 `0 → 1 → 2 → 3 → 4 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 60 → 61 → 62 → 69 → 70 → 71 → 80 → 81 → 82 → 97`，共 22 个事件。本 seed 走 **store** 路径，并且与 seed1 一样真实发射了两组 MSHR 填充。

### 2.1 故障注入前的正常状态

注入目标为 DTLB 第 21 号 entry（`event_id=1` 的 `entry_index=21`、`way=-1`）。`state_before`=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950`：VPN=`0xffffffc009483`，ASID=206，`valid=1`、`global=1`，`ap=0`，4 KiB 页，正常 PFN=`0x81d75`。触发翻译的指令 `dyn_inst_seq=520906`（`request_id=520906`）使用 VA=`0xffffffc009483950`；偏移 `0x950`，正常 PA=`0x81d75950`。后续 `sq_idx=54806` 表明这是一条 store。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=238095582084（cycle=715001748），`event_id=0`，`fault_id=1`，`request_id=520906`，`field=bit_flip`，FaultType=`bit_flip`，`corr=origin`。注入日志：
`Tick: 238095582084, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483950, old_pfn: 0x81d75, new_pfn: 0x95d75, FaultType: bit_flip, Mask: 0x14000, effective: 1`。
`before=0x81d75`、`after=0x95d75`，异或 `0x14000`：翻转 PFN 的第 14 位与第 16 位，均落在有效宽度内（注入日志也标 `effective: 1`）。`new_pfn << 12 = 0x95d75000`，或上偏移 `0x950` 得有效 PA `0x95d75950`；两位分别对应 PA 的第 26、28 位：`0x81d75950 → 0x95d75950`。`event_id=3` 的 `tlb_translate_result`：`field=effective_pa_changed`、`before=81d75950`、`after=95d75950`、`contained=0`、`outcome=NoFault`，翻译层未含住。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=238095582084）命中第 21 号 entry，`field=post_lookup`，`before=81d75`、`after=95d75`，`state_after` 的 `pfn=95d75`、`pa=95d75950`。`event_id=2` 的 `tlb_pfn` 记录 `state_before=81d75950`、`state_after=95d75950`、`pa=95d75950`。`event_id=3` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason；TLB 在 tick 238095582084 把错误有效 PA `0x95d75950` 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 走 **store** 路径：`event_id=4` 的 `sq_execute`（tick=238095582084，`sq_idx=54806`，VA=`0xffffffc009483950`，`state_before=issued`）把 store 送入执行；`event_id=11` 的 `sq_writeback`（tick=238095585414）记录 `sq_idx=54806`、`pa=95d75950`、`state_after=packet_built`，用错误 PA 构造数据包；`event_id=82` 的 `sq_complete`（tick=238095646353，`sq_idx=54806`，`state_after=completed`）完成条目。本 fault 的祖先上没有 `lq_read`/`lsq_push`/`mem_req`/`lsq_sendfrag`（这些 kind 属于同 seed 的其它故障或旁支），因此 load 字段为 N/A；可证的 store 事实是执行→写回→完成全程使用同一个错误 PA。

### 2.5 错误如何经过 cache 和 MSHR

两次 store 访问都未命中：`event_id=12` 的 `cache_access`（tick=238095585414，PA=`0x95d75950`）→ `event_id=13` 的 `cache_return`（`field=miss`）→ `event_id=14` 的 `mshr_alloc`（`mshr_id=3`，`cache_line=0x95d75950`，`state_after=mshr_allocated`）；`event_id=15` 的第二次访问（tick=238095585747，PA=`0x95d75940`）→ `event_id=16` 的 `miss` → `event_id=17` 的 `mshr_alloc`（`mshr_id=4`，`cache_line=0x95d75940`）。随后真实填充两组：`event_id=60` 的 `mshr_fill`（tick=238095645021，`mshr_id=4`，`fill_id=3`，`cache_line=0x95d75940`，`state_after=filled`）→ `event_id=61` 的 `cache_fill`（`pa=95d75940`）→ `event_id=62` 的 `mshr_free`（`mshr_id=4`，`state_after=mshr_freed`）；`event_id=69` 的 `mshr_fill`（tick=238095646020，`mshr_id=0`，`fill_id=4`）→ `event_id=70` 的 `cache_fill`（`pa=95d75940`）→ `event_id=71` 的 `mshr_free`（`mshr_id=0`）。两组填充把错误行 `0x95d75940` 真实写入 L1D；这是错误从“一次 store 请求”升级为“缓存内容”的位置。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、mshr_alloc、mshr_fill、mshr_free、resp、sq_complete、sq_execute、sq_writeback、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、lsq_push、mem_req、lsq_sendfrag、lq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=80` 的 `resp`（tick=238095646353，`request_id=520906`，原始 `va` 字段记录 PA=`95d75950`）回送数据；`event_id=81` 的 `taint_reg`（同 tick）把状态从 `clean` 改为 `tainted`；`event_id=82` 的 `sq_complete` 完成 SQ 条目。event 81 的原始记录**没有**填写 `arch_reg`/`phys_reg`，因此本文件不能指名被污染的寄存器，只能证明该 store 的结果已被登记为 tainted。这仍是存储→CPU 边界：store 返回数据进入污染集，随后该 store 在架构上完成。

### 2.7 最终传播终局

L5 终局是 `event_id=97` 的 `errant_commit`：parent=82，tick=238095648018，`dyn_inst_seq=520923`，`commit_seq=394130`，`pc=0xffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除：L2 记录 `effective_pa_changed` 却 `contained=0`；L3 把错误行填入 cache；本 fault 的主链上没有 `squash_masked`（fault 1 的 56 条都在旁支，另有 9 条属 fault 2）；提交点因此首次真实暴露。`chain_end`（event_id=10968，parent=8347，tick=4091874898464，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 97，tick 238095648018），`provable_to=L5`，`terminal=full`。运行结局 `Crash`：`run.out` 有 `CHAOS_DETECT: layer=None contained=0 tick=238095648018 ptag=1 reason=errant_commit`，末尾 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 有内核 panic 告警。注入 tick=238095582084，终局 tick=238095648018，延迟 65934 ticks（cycle 715001748→715001946，198 个 CPU cycle）。因果链：错误 PFN→错误 PA `0x95d75950`→store 执行/写回→两次 miss 与两组真实填充→`taint_reg`/`sq_complete`→提交点 `errant_commit`；随后内核 panic。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 21 号 DTLB 表项（PFN=`81d75`） | PFN→`95d75`（bit14、bit16） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x950` | PA `81d75950`→`95d75950`，`contained=0` | 有效 PA | 翻译层未含住 |
| SQ（L3） | 错误翻译（`sq_idx=54806`） | `sq_execute`→`sq_writeback`（packet_built） | 携带错误 PA 的数据包 | 污点进入 store |
| L1D（L3） | PA `95d75950`/`95d75940` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | `mshr_id=3`、`mshr_id=4` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | 两组 `mshr_fill`/`cache_fill`/`mshr_free` | 错误行留在 cache | 错误被持久化 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `taint_reg`/`sq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | store 返回数据 | `clean→tainted`（寄存器字段未填） | 污染状态 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染结果 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=238095582084 的第 21 号 DTLB 命中把 PFN 的第 14、16 位同时翻转（`effective: 1`），有效 PA 由 `0x81d75950` 变为 `0x95d75950`；翻译层记录改变却 `contained=0`，store 经 `sq_execute`（`sq_idx=54806`）与 `sq_writeback`（packet_built）进入 L1D，两次相邻访问（`…950`/`…940`）均 miss 并分配 `mshr_id=3/4`，随后两组 `mshr_fill`→`cache_fill`→`mshr_free`（fill_id=3/4，tick=238095645021/238095646020）把错误行写入缓存；`resp`、`taint_reg`（clean→tainted，寄存器字段未填）与 `sq_complete` 完成写路径，最终在 tick=238095648018 由 `errant_commit`（`dyn_inst_seq=520923`，`commit_seq=394130`）收口，距注入 65934 ticks，运行随即内核 panic，结局 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER`：`attempted=515289 eligible=515289 injected=5`；`stats.txt`：`numFaultsInjected=5`；流内 `inj` 5 条；权威报告 5 个 fault：三方一致。fault 1 的注入值被真实读取（`tlb_lookup`）并消费（`sq_execute`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此是 activated。其它 4 个故障各有自己的注入点与终局，不并入本链。

### 3.2 故障传播类型

**地址型**（错误物理地址）：VA/偏移/权限不变，PFN 被改成 `0x95d75`；两个翻转位（14、16）都改变有效 PA（PA 位 26、28）。没有控制状态或时序型证据；`request_id=520906` 与 `sq_idx=54806` 在祖先上保持一致。由于是 store，错误地址进入写路径并真实写入缓存行。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3` 的 `tlb_translate_result`（`contained=0`）——翻译层记录 PA 改变却放行。对后续访问也生效的升级点是 `event_id=61`/`event_id=70` 的 `cache_fill`：错误行 `0x95d75940` 被真实写入 L1D，未来对同一行的访问可能命中错误数据。若只取一个答案，取 event 3。

### 3.4 检测与掩蔽机制

翻译层可检测 `effective_pa_changed`（本 seed `contained=0`，未阻断）；L1D/MSHR 没有地址校验，并已把错误行填入 cache；L4 的 RAS 重放没有出现在本 fault 的祖先上（fault 1 的 56 条 squash 都在旁支，另有 9 条属 fault 2）；提交点 `errant_commit` 首次暴露。盲区是“检测到 PA 改变却不阻断 + 错误行被缓存持久化 + 本故障未触发重放”。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 97，`contained=0`、`outcome=errant_commit`），运行以 KERNEL PANIC 结束；权威 `terminal=full`，不是 Masked/Contained。本实验没有应用级输出 oracle，无法证明“外部可见且未被检测的错误数据”，因此不称 SDC；仅可证“错误地址与错误提交真实发生并导致崩溃”。最终数据正确性无法判定。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 VA=`0xffffff8001362708`、PFN `81362→c5362`（mask `0x44000`），有效 PA `81362708→c5362708`，load 路径，终局 `errant_commit` event 26，结局 Crash；seed2 注入 VA=`0xffffffc009483960`、PFN `81d75→c1d74`（mask `0x40001`），有效 PA `81d75960→c1d74960`，终局 L4 `squash_masked` event 68 含住、L5=N/A，结局 Crash。本 seed 的 PFN/PA、掩码、路径（store）与终局（event 97）都不同；三者的共同点仅是注入站点相同。

## 4. 完整主链事件表

下表按 event 97 的祖先顺序排列（`0→1→2→3→4→11→12→13→14→15→16→17→60→61→62→69→70→71→80→81→82→97`）。`mask` 只在 `inj` 行给出（`0x14000`）；主链 22 个事件，无需折叠。

<!-- witness=97 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '11', '12', '13', '14', '15', '16', '17', '60', '61', '62', '69', '70', '71', '80', '81', '82', '97'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238095582084 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 95d75 | 81d75 | 95d75 | 0x14000 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=520906 的地址翻译即将使用它 | 被改写后的 PFN=95d75（VA=ffffffc009483950） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 238095582084 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 95d75 | 81d75 | 95d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=95d75;ap=0;mtype=2;page_size=1000;pa=95d75950 | — | — | — | — | DTLB 命中 entry_index=21（way=-1），读取 pfn 字段 | 命中读出 pfn=95d75，AP=0，page_size=1000，PA=95d75950 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 238095582084 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 95d75950 | — | — | 81d75 | 95d75 | 81d75 | 95d75 | — | 81d75950 | 95d75950 | — | — | — | — | lookup 得到的 PFN=81d75 | PFN 记录为 95d75，翻译 PA=95d75950 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 238095582084 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 95d75950 | — | — | — | — | 81d75950 | 95d75950 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=95d75;ap=0;mtype=2;page_size=1000;pa=95d75950 | 0 | — | NoFault | — | PFN=81d75 与页内偏移组合 | 有效 PA 81d75950→95d75950；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 238095582084 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | SQ 条目 sq_idx=54806（state_before=issued） | 执行阶段生成 store 操作（VA=ffffffc009483950） | L3：store 进入执行，地址来自故障翻译 |
| 6 | 11 | 4 | 238095585414 | 3330 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 520906 | — | 95d75950 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | SQ 条目 sq_idx=54806 的执行结果 | packet_built，PA=95d75950 | L3：store 数据包成形，携带错误地址 |
| 7 | 12 | 11 | 238095585414 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 95d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=520906 访问 L1D（PA=95d75950） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 8 | 13 | 12 | 238095585414 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 95d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=95d75950 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 9 | 14 | 13 | 238095585414 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 95d75950 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=95d75950 | mshr_id=3 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 10 | 15 | 14 | 238095585747 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 95d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=520906 访问 L1D（PA=95d75940） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 11 | 16 | 15 | 238095585747 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 95d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=95d75940 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 12 | 17 | 16 | 238095585747 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 95d75940 | 4 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=95d75940 | mshr_id=4 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 13 | 60 | 17 | 238095645021 | 59274 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 95d75940 | 4 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=4 的数据返回（fill_id=3） | state_after=filled，cache_line=95d75940 | L3：MSHR 完成填充 |
| 14 | 61 | 60 | 238095645021 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 95d75940 | 95d75940 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=3 的填充数据 | cache_line=95d75940 进入 L1D | L3：错误行进入 cache |
| 15 | 62 | 61 | 238095645021 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 95d75940 | 4 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=4 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 16 | 69 | 62 | 238095646020 | 999 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 95d75940 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=4） | state_after=filled，cache_line=95d75940 | L3：MSHR 完成填充 |
| 17 | 70 | 69 | 238095646020 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 95d75940 | 95d75940 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=4 的填充数据 | cache_line=95d75940 进入 L1D | L3：错误行进入 cache |
| 18 | 71 | 70 | 238095646020 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 95d75940 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 19 | 80 | 71 | 238095646353 | 333 | resp | L4 | L1D→LSU | 1 | seq_primary | 520906 | 520906 | 95d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=520906） | 响应数据返回（该事件 va 字段记录 PA=95d75950） | L4：污染数据返回处理器 |
| 20 | 81 | 80 | 238095646353 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 1 | seq_primary | 520906 | 520906 | 95d75950 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=520906） | arch_reg= / phys_reg=：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 21 | 82 | 81 | 238095646353 | 0 | sq_complete | L4 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | SQ 条目 sq_idx=54806 的写回完成 | state_after=completed，PA/VA=ffffffc009483950 | L4：store 完成，错误地址已写入存储路径 |
| 22 | 97 | 82 | 238095648018 | 1665 | errant_commit | L5 | ROB/Commit | 1 | taint_prop | — | 520923 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=520923，commit_seq=394130） | contained=0，outcome=errant_commit，PC=ffffffc0087b27c4 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`taint_reg`（event 81）的 `arch_reg`/`phys_reg` 原始为空，标 `—`；`sq_execute` 只有 `state_before=issued`、`sq_writeback` 只有 `state_after=packet_built`，另一侧不补造；两组填充的 `fill_id=3/4` 与 `mshr_id=4/0` 照原始字段。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 12792 个事件、5 个故障。fault 1 的事件集合为 9835+22 个（主链 22 个，旁支 9835 个）。

1. **请求分叉（`request_fork` 1508 条）**：1 条挂在主链 `lq_read`（event 3）上（`event_id=4294967296`，parent=3，new_request_id=520896，`shared_addr=0x95d75000`）；11 条挂在主链 `mshr_alloc`（event 17）上；1496 条挂在主链 `taint_reg`（event 81）上，最晚 `event_id=4294968803`（parent=81，tick=238115507472，new_request_id=538678）。
2. **污染消费（`consumer` 1273 条、`taint_reg` 1660 条）**：最早 `event_id=98`（parent=86，tick=238095648018，`arch_reg=30`、`phys_reg=92`），最晚 `event_id=8347`（parent=584，tick=238143298320，`arch_reg=1`、`phys_reg=1273`）；不在 event 97 的祖先上。
3. **填充与含住旁支**：`mshr_fill`/`cache_fill`/`mshr_free` 的旁支各 62 组（主链另有 2 组；整个 seed 共 96 条，其余 32 条属 fault 2），`squash_masked` 56 条（全部旁支，最早 event 1661，tick=238098402927，VA=`0xffffffc009483740`，PA=`0x95d75740`；最晚 event 7847，tick=238107812175，PA=`0x95d75430`）。这些说明错误页被反复访问/含住，但不改变 event 97 的终局。
4. **生命周期收口（1 条）**：`event_id=10968`（parent=8347，tick=4091874898464，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`）。
5. **其它故障**：fault 2（`detected_contained`，路径 `8348,8349,8350,8352,8376,9237`）、fault 3/4/5（`provable_to_L4_then_unknown`，路径 `10880…10899`、`10912…10931`、`10933…10952`）各有自己的注入与地址，不属于本链。

旁支对 SDC 诊断的影响：它们显示同一错误页被大量再访问（1508 fork、1273 consumer、56 次 squash），但主链终局由 event 97 单独证明；含住旁支不能覆盖主链的 `errant_commit`，也不能把本故障改判为 contained。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=97，tick=238095648018，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Crash`（`run.out` KERNEL PANIC；`run.err` 内核 panic 告警） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=5`，与触发器 injected=5、inj 事件 5 条一致） |
| conservation | `ok`（consumer_summary：emitted=1626、suppressed=14619、logical_total=16245、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=12792` 与实际解析事件数 12792 相同；injected/stats/inj 均为 5 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


判定说明：传播终局（event 97）与运行结局（Crash）分别陈述；`chain_end` 10968 未被当作 L5；旁支 56 条 `squash_masked` 未被用来改写终局。15 项一致性检查全部通过：事件存在、父子/tick 单调、取值来自本 seed、终局与权威报告一致（`full`/L5）、L5 见证真实。
## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3/T02-F2-W1/seed3`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `7a928291cd3e1554fe7a814a66ef8c87d89f9906bf74028a9f57716cc6275988` | 478041 | 2026-10-27T16:14:19 |
| `chain_report.json` | `20ed29de287f2dd26b7c61a08ec0539edee3f45790240363738d6efefca710dc` | 1376063 | 2026-10-27T16:14:21 |
| `run.out` | `65e1b1444d1e84125d846fb875722f21bec041f4f61c25e25c8213212df87705` | 8694 | 2026-10-27T16:14:19 |
| `run.err` | `7a1330e20fb7778733f12c6460b3c22084fd40bf86f1a114fee02156ded9bbb6` | 1812 | 2026-10-27T16:14:19 |
| `stats.txt` | `a510f741d61b633befd007138e74984a9bd41b4b105cc4d981c47e9c0ab67d56` | 393194 | 2026-10-27T16:14:19 |
| `armtlb_injections.log` | `b1c5d6bd2c086ddd172d4fa24d5bd86a293c5fbed889b0461e6c8fd115261aa9` | 1175 | 2026-10-27T16:14:19 |
| manifest `manifest.json` | `f77b28677f274ad98525df52b98937be433f59fc6286a4cda22768320f8870d2` | 1438 | 2026-10-27T16:14:23 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3/T02-F2-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T02-F2-W1 --prop_sample_run_id s3`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3 --cells T02-F2-W1 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `../R6-AUTHORITATIVE-EVIDENCE.md` 未登记本 (RunID, seed) 的其它副本。

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
