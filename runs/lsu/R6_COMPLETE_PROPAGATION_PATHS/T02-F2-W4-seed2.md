# T02-F2-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T02-F2-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T02`）
- fault model：PPN 内同时翻转 2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`双比特翻转`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F2 — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier：`F2`；effective tier：`F2`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`）
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T02-F2-W4 --prop_sample_run_id s2`
- source head：N/A（manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同二进制构建源）
- binary source head：N/A（manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同二进制构建源）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/manifest.json`（SHA-256 `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9`；run 根 manifest（seed 字段=3，artifacts 尺寸对应最后一个 seed；不按它推断本 seed 的逐 seed 事实）；manifest.status=`FINISHED`，manifest.exit_code=`0`，manifest.seed=`3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`None`；manifest.exit_code=`0`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：8599（与 `chain_report.event_count` 相同）
- fault_id 数量：2（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：是（`chain_report.regrade-20261027T103833.json` 为权威判定）


## 2. 完整故障传播过程：从注入到最终结局

本 seed 的权威判定是显式含住，因此本章重建的是**含住见证** `squash_masked`（event_id=68）的单祖先链，而不是同流中更晚的 event 1797。顺序严格为 parent 先于 child：`0 → 1 → 2 → 3 → 4 → 32 → 33 → 34 → 35 → 36 → 68`，共 11 个事件。event 1797 是同一 fault 在另一个 VA 上更晚的一次同类 squash，按权威口径不得替代 event 68；event 83 是 event 68 的直接 child，它的身份与处理单独在 2.7 与第 5 章说明。本 seed 共有两个真实故障（fault 1 与 fault 2），本章只讲代表故障 fault 1；fault 2 只在第 5 章作为“另一故障”交代，不并入本链。

### 2.1 故障注入前的正常状态

被注入的是 DTLB 第 21 号 entry（`event_id=1` 的 `entry_index=21`、`way=-1`）。注入前的 `state_before` 为 `vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960`：VPN=`0xffffffc009483`，ASID=206，有效且 global，权限 `ap=0`，页大小 4 KiB（`page_size=1000`），正常 PFN=`0x81d75`。触发翻译的指令是 `dyn_inst_seq=393897`，`request_id=393897`，VA=`0xffffffc009483960`；页内偏移为 `0x960`，因此正常物理地址为 `(0x81d75 << 12) | 0x960 = 0x81d75960`，与 `state_before` 的 `pa` 一致。`inj` 事件的 `corr=origin` 标识它是本链起点。

### 2.2 故障具体如何注入

注入站点 `arm_tlb_lookup_hit`，组件 `CHAOSArmTLB`，tick=238083182163（cycle=714964511），`event_id=0`，`fault_id=1`，`request_id=393897`，`field=bit_flip`，FaultType=`bit_flip`，`corr=origin`。`armtlb_injections.log` 记录为：
`Tick: 238083182163, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483960, old_pfn: 0x81d75, new_pfn: 0x800000000081d77, FaultType: bit_flip, Mask: 0x800000000000002`。
`before=0x81d75`、`after=0x800000000081d77`，异或为 `0x800000000000002`：翻转的是 PFN 的第 1 位与第 59 位，符合 T02 双比特模型（同一命中事件内两 bit 同时生效），`ap/page_size/asid/valid/global` 未变。

数值解释必须分开看：`new_pfn << 12 = 0x800000000081d77000`，64 位截断后丢掉第 59 位，得 `0x81d77000`；再或上页内偏移 `0x960`，有效 PA 为 `0x81d77960`。所以第 59 位对有效 PA **没有贡献**（它落在左移 12 位后被截断的高位），真正改变 PA 的是第 1 位，它使有效 PA 的第 13 位从 0 变 1：`0x81d75960 → 0x81d77960`。`event_id=3` 的 `tlb_translate_result` 如实记录 `field=effective_pa_changed`、`before=81d75960`、`after=81d77960`、`contained=0`、`outcome=NoFault`，说明翻译层看见了变化但本 seed 没有在 L2 含住。

### 2.3 TLB 查询与地址翻译

`event_id=1` 的 `tlb_lookup`（tick=238083182163）命中第 21 号 entry，`field=post_lookup`，`before=81d75`、`after=800000000081d77`，`state_after` 的 `pfn=800000000081d77`、`pa=81d77960`。`event_id=2` 的 `tlb_pfn` 把命中值写成翻译 PFN（`state_before=81d75960`、`state_after=81d77960`，`pa=81d77960`，`field=bit_flip`）。`event_id=3` 的 `tlb_translate_result` 是本链的翻译结论：`contained=0`、`outcome=NoFault`、`detection_layer` 空、`containment_reason` 空，`effective_pa_changed` 为真。TLB 在 tick 238083182163 把有效 PA `0x81d77960` 交给 LSU；请求 VA 为 `0xffffffc009483960`，请求 PA 为 `0x81d77960`，`contained=0`，`detection_layer=N/A`，`containment_reason=N/A`。与 seed1 不同，本 seed 的最终含住不发生在翻译层，而在更下游的 L4。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径，而且流内完整发射了 LSQ 的中间步骤，这是与 seed1 的结构差异。`event_id=4` 的 `lq_read`（tick=238083182163，`lq_idx=41835`，`request_id=393897`，VA=`0xffffffc009483960`）先把请求带出 LQ。`event_id=32` 的 `lsq_push`（tick=238083183495）记录 `pc=0xffffffc0087b27c8`、`opcode=ldp_uop`、`lq_idx=41835`、`sq_idx=-1`、`field=load`，即一条 `ldp` 微操作进入 LQ（不是 SQ）。`event_id=33` 的 `mem_req` 生成 `request_id=393897` 的访存请求；`event_id=34` 的 `lsq_sendfrag` 以同一 `request_id`、`field=load` 把请求分片送出 LSQ；`event_id=35` 的 `tlb_translate` 再次携带该请求做翻译；`event_id=36` 的 `lq_read`（`lq_idx=41835`、`request_id=393897`）是这条请求在 L1D 路径上的最后一次读取。整段序列的输入是 2.3 的错误 PA，内部变化是请求在 LQ 中被登记、成形并分片，输出是带着 `0x81d77960` 的请求进入后续 cache/重放路径；`sq_execute`/`sq_writeback`/`sq_complete` 在本 fault 的祖先上不存在（它们属于同流的写路径故障或旁支），因此这里的 store 字段为 N/A。

### 2.5 错误如何经过 cache 和 MSHR

本 fault 的主链在 `lq_read`（event 36）之后直接到达 `squash_masked`（event 68），中间没有 cache_access/cache_return/MSHR 事件进入祖先。也就是说：本 fault 的错误请求在被 squash 之前，流内**没有**发射它自己的 L1D 访问与 MSHR 分配证据；不能把同流中其它 request 的 cache 事件拼进来充当本链的 L3 中间步。可证的事实是：错误 PA 已经被登记进请求并送过分片/翻译（event 33–35），随后该 load 在 L4 被判定为收到污染响应并 squash。作为对照，本 seed 的同故障旁支确实有 64 组 `mshr_fill`/`cache_fill`/`mshr_free`（见第 5 章），但它们不在 event 68 的祖先上，故不写入主链，也不据此声称“错误行进入 cache 后被发现”。

本链出现的 kind 集合为 `inj、lq_read、lsq_push、lsq_sendfrag、mem_req、squash_masked、tlb_lookup、tlb_pfn、tlb_translate、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mshr_fill、cache_fill、mshr_free、sq_execute、sq_writeback、sq_complete、lq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

本 fault 的含住点直接发生在 L4，因此不存在“污染返回寄存器后再被清除”的祖先路径：`event_id=68` 的 `squash_masked`（tick=238083244768）`field=squashed_load`、`detection_layer=L4`、`contained=1`、`outcome=masked`、`corr=addr_fallback`、`containment_layer=L4`、`containment_reason=squash_replay`，`dyn_inst_seq=393912`，VA=`0xffffffc0094839e0`，PA=`0x81d779e0`。它的输入是 event 36 之后被送出的、使用故障 PA 的 load；内部变化是该 load 收到污染响应后被 squash（不提交、重放）；输出是 `masked` 结局。与 `taint_reg` 不同，`squash_masked` 不是“存储→CPU 寄存器”的边界，而是“CPU 拒绝接收污染值”的边界，因此本 fault 的祖先上没有 `taint_reg` 事件，寄存器污染集在本链上未被建立。

### 2.7 最终传播终局

本 seed 的权威终局是**含住**，不是 L5 错误提交。真实含住事件是 `squash_masked` event_id=68：parent=36，tick=238083244768，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_layer=L4`，`containment_reason=squash_replay`；权威 regrade 报告的 `containment.metrics.L4` 逐字给出同一组值（`event_id=68`、`tick=238083244768`、`field=squashed_load`、`outcome=masked`、`contained=1`），`na_layers=["L5"]`。停止它的是 L4 的 RAS 重放机制（`run.out` 也写下 `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238083244768 ptag=1 reason=squash_replay`）：收到污染响应的 load 被 squash 并重放，因而不进入架构提交。L5 在本链上为 N/A——祖先里没有 `errant_commit`；同流中确实存在 `errant_commit` 记录（event 83，见下），但它不是本链的祖先，也不能把 L4 含住改写成 L5。

必须正面交代 event 83：它是 event 68 的直接 child（`kind=errant_commit`，tick=238083249096，`dyn_inst_seq=393846`，`commit_seq=273130`，`pc=0xffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`）。本文件不隐瞒这条原始记录；按权威 checker 中 `_errant_commit_escape` 的公开语义（该函数的注释逐字点名“T02-F2-W4 seed2 的 event 83”为悬空 errant_commit），它不能收口任何连续 L0→L5 前缀：把它的祖先按 TLB family 的有序前缀规则重放，得到的连续前缀只到 L0..L3（`inj`→`tlb_lookup`→`tlb_pfn`→`lq_read`，长度 4），因此它不构成“以 errant_commit 收口的可证 L0→L5 路径”，也不触发逃逸优先权护栏去推翻 squash 含住。于是权威判定保持 `detected_contained`、`provable_to=L5`、含住层 L4、L5=N/A；event 1797（另一 VA 上更晚的同 kind squash）同样不得替代 event 68。

### 2.8 从传播终局到系统表现

传播终局是 L4 `squash_masked`（event 68，tick=238083244768），`provable_to=L5`（报告口径），含住层 L4，L5=N/A。运行结局是 `Crash`：`run.out` 先写 `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238083244768 ptag=1 reason=squash_replay`，紧接着写 `CHAOS_DETECT: layer=None contained=0 tick=238083249096 ptag=1 reason=errant_commit`，最后写 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 有内核 panic 的告警。这里必须区分两件事：本 fault 的传播在主链上于 L4 被含住，**但运行本身仍然崩溃**——同流中另有 fault 2 与 event 83 等候选，但本链证据不把崩溃归因到 event 68 之后的任何具体事件（本文件不做推断）。因此不能写“本故障导致崩溃”，也不能因为运行崩溃就把含住改判为 L5；注入 tick=238083182163，含住 tick=238083244768，二者相差 62605 ticks（cycle 714964511→714964699，相差 188 个 CPU cycle），这段时间内该 fault 的传播没有走到提交点。若只看本 fault，则架构上没有出现可见错误结果；运行层面的 Crash 属于独立的 run outcome 事实。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 21 号 DTLB 表项（VPN=`ffffffc009483`，PFN=`81d75`） | PFN→`800000000081d77`（bit1、bit59） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x960` | PA `81d75960`→`81d77960`，`contained=0` | 有效 PA `0x81d77960` | 翻译层未含住 |
| LQ（L3） | 翻译结果（`request_id=393897`） | `lq_read` / `lsq_push` / `mem_req` / `lsq_sendfrag` / `tlb_translate` / 再次 `lq_read` | 携带错误 PA 的 load 请求 | 污点穿过 LSQ 全流程 |
| RAS/ROB 重放（L4） | 使用错误 PA 的 load（`dyn_inst_seq=393912`） | `squashed_load`，`contained=1` | `masked`，重放 | 含住点：污染值被拒绝并重放 |
| L5 | — | — | — | N/A（祖先无 errant_commit；event 83 为悬空，不改变本链） |

整条链可以概括为：tick=238083182163 的第 21 号 DTLB 命中把 PFN 的第 1、59 位同时翻转，其中第 59 位在 64 位左移 12 位时被截掉、无效，第 1 位把有效 PA 从 `0x81d75960` 改成 `0x81d77960`；L2 的 `tlb_translate_result` 记录 `effective_pa_changed` 却 `contained=0`，请求经 `lq_read`→`lsq_push`（`ldp_uop`，`lq_idx=41835`）→`mem_req`→`lsq_sendfrag`→`tlb_translate`→`lq_read` 一路带着错误 PA 前进，最终在 tick=238083244768 由 L4 的 `squash_masked`（event 68，`contained=1`、`outcome=masked`、`reason=squash_replay`）接收并重放，架构状态没有被污染；L5 在祖先上为 N/A，同流的 event 83 是一条悬空的 `errant_commit` 记录，按权威规则不构成本链的 L5 终局。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER` 记录 `attempted=196732 eligible=196732 injected=2`；`stats.txt` 的 `numFaultsInjected=2`；流内有 2 条 `inj`（fault 1 与 fault 2），三方一致。代表故障 fault 1 的值确实被下游读取：`event_id=1` 的 `tlb_lookup` 读出故障 PFN，`event_id=2/3` 转成 `0x81d77960`，`event_id=33–36` 的请求带着该 PA 走完 LSQ，最终在 event 68 被 squash。因此 fault 1 是 activated，且其污染值在 L4 被真实消费（这正是触发含住的前提）；不存在“注入但未被读取”的情况。

### 3.2 故障传播类型

这是**地址型**（错误物理地址）传播：请求身份（`request_id=393897`、VA、页内偏移 `0x960`）保持正确，物理落点被改成同一 4 KiB 页内的错误 PFN（`0x81d77`）。权限字段未变（`ap=0`），控制状态未变，也没有 timing 注入；cache_line/MSHR 字段（旁支中）与该 PA 一致，没有出现“错误 cache line”或“错误请求路由”的独立证据。与 seed1 的差别不在类型而在结局：同一地址型错误在本 seed 被 L4 重放机制拦住。

### 3.3 首个不可逆传播点

按“当前结构一旦越过就无法撤销”的口径，本 seed 的首个不可逆点是 `event_id=32` 的 `lsq_push`（tick=238083183495）：此前翻译结果（event 3）虽然已是错误 PA，但请求尚未在 LSQ 中登记为可发射的 load；event 32 把 `ldp_uop` 与 `lq_idx=41835` 绑定并写入 LSQ，此后请求的地址身份在该结构内固定，只能依靠下游 squash 才能撤销。事件 33–36 是同一不可逆点的后续展开；event 68 是撤销成功的那一步，不是不可逆点。

### 3.4 检测与掩蔽机制

可检测的机制有：翻译层的 `effective_pa_changed`（检测到但 `contained=0`，未阻断）；L4 RAS 的 squash/重放（实际生效，`run.out` 记为 `layer=Hardware RAS contained=1 reason=squash_replay`）；提交点（本链未到达）。实际结果是 L4 成功掩蔽：`squash_masked` 同时携带 `contained=1`、`detection_layer=L4`、`outcome=masked`、`containment_layer=L4`、`containment_reason=squash_replay`，说明这是显式含住而非“没有事件所以猜测”。观察到的盲区是：翻译层能看见 PA 改变却不阻断，必须依赖一次真实访存触发重放才能拦住；同流中 event 83 的悬空 `errant_commit` 说明并非所有污染消费都被同一机制覆盖（该记录不在本链祖先上，按规则不改变 L4 含住判定）。

### 3.5 最终 SDC 风险判断

本 fault 的权威终局是 Detected/Contained（L4 `squash_masked`，event 68），不是 SDC：被污染的值没有进入架构寄存器或提交点，重放路径把它丢弃。虽然运行以 Crash 结束，但该崩溃不能由本链归因（见 2.8），所以不能据此把本 fault 升级为 SDC，也不能降级为“无影响”。是否存在静默错误数据无法判定：本实验没有应用级输出 oracle；本 fault 的贡献是“污染值在 L4 被拦下”，这是可证事实。若只看 event 83 的原始 `errant_commit`，它证明同流存在错误提交记录，但按权威 checker 语义它是悬空路径，不足以证明“外部可见且未被检测的错误结果”。

### 3.6 与同 RunID 其他 seed 的关系

同 RunID 的 seed1 注入 VA=`0xffffff8001362708`、PFN `81362→800400000081362`（bit46、bit59），有效 PA `81362708→400000081362708`，终局是 `errant_commit` event 20，结局 Crash；seed3 注入 VA=`0xffffffc009483950`、PFN `81d75→20200000081d75`（bit45、bit53），有效 PA `81d75950→200000081d75950`，走 store 路径并以 `errant_commit` event 96 收口，结局 Timeout。本 seed 的 VA/掩码/地址变化与两者都不同，且终局是 L4 含住（event 68），不能把 seed1/seed3 的 L5 事件或地址搬进本链。

## 4. 完整主链事件表

下表严格按 event 68 的祖先顺序排列（`0→1→2→3→4→32→33→34→35→36→68`），每一行都是上一行的直接 child。`mask` 只在 `inj` 行给出（`0x800000000000002`，来自 `armtlb_injections.log`）；`layer` 对 `squash_masked` 记 L4。主链只有 11 个事件，不需要折叠任何连续 `consumer` 段；同流的 `consumer`/`taint_reg`/其它 `squash_masked` 都在旁支，见第 5 章。

<!-- witness=68 representative_fault=1 ancestors=['0', '1', '2', '3', '4', '32', '33', '34', '35', '36', '68'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238083182163 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 800000000081d77 | 81d75 | 800000000081d77 | 0x800000000000002 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=393897 的地址翻译即将使用它 | 被改写后的 PFN=800000000081d77（VA=ffffffc009483960） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 1 | 0 | 238083182163 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 800000000081d77 | 81d75 | 800000000081d77 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=800000000081d77;ap=0;mtype=2;page_size=1000;pa=81d77960 | — | — | — | — | DTLB 命中 entry_index=21（way=-1），读取 pfn 字段 | 命中读出 pfn=800000000081d77，AP=0，page_size=1000，PA=81d77960 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 2 | 1 | 238083182163 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d77960 | — | — | 81d75 | 800000000081d77 | 81d75 | 800000000081d77 | — | 81d75960 | 81d77960 | — | — | — | — | lookup 得到的 PFN=81d75 | PFN 记录为 800000000081d77，翻译 PA=81d77960 | L2：翻译结果开始使用错误 PFN |
| 4 | 3 | 2 | 238083182163 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d77960 | — | — | — | — | 81d75960 | 81d77960 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=800000000081d77;ap=0;mtype=2;page_size=1000;pa=81d77960 | 0 | — | NoFault | — | PFN=81d75 与页内偏移组合 | 有效 PA 81d75960→81d77960；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 4 | 3 | 238083182163 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=41835 的 load 请求（VA=ffffffc009483960） | request_id=393897 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 6 | 32 | 4 | 238083183495 | 1332 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ldp_uop 指令 dyn_inst_seq=393897 进入 LSQ | lq_idx=41835 / sq_idx=-1，field=load，VA=ffffffc009483960 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 7 | 33 | 32 | 238083183495 | 0 | mem_req | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LSQ 条目 lq_idx= 的访存请求 | request_id=393897 的 mem_req 生成 | L3：请求成形，下一级消费 |
| 8 | 34 | 33 | 238083183495 | 0 | lsq_sendfrag | L3 | LSQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | mem_req request_id=393897 | 请求分片发送到 TLB/L1D（field=load） | L3：请求离开 LSQ 进入地址翻译 |
| 9 | 35 | 34 | 238083183495 | 0 | tlb_translate | L2 | CHAOSArmTLB/MMU | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 分片请求 request_id=393897（VA=ffffffc009483960） | 携带故障 PFN 的翻译请求进入 L1D 访问 | L2/L3 交界：LSQ 发出的请求再次使用被污染的翻译 |
| 10 | 36 | 35 | 238083183495 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=41835 的 load 请求（VA=ffffffc009483960） | request_id=393897 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 11 | 68 | 36 | 238083244768 | 61273 | squash_masked | L4 | RAS/ROB(重放) | 1 | addr_fallback | — | 393912 | ffffffc0094839e0 | 81d779e0 | — | — | — | — | — | — | — | — | — | 1 | L4 | masked | squash_replay | dyn_inst_seq=393912 的 load（PA=81d779e0）收到污染响应 | field=squashed_load，contained=1，outcome=masked | L4：含住点，错误响应被 squash 并重放，未进入架构状态 |


**单位说明**：`before/after` 为原始字段值；`PA/address` 取 `pa` 字段；`state_before/state_after` 原样保留分号分隔串。`squash_masked` 行同时给出 `contained=1`、`detection_layer=L4`、`outcome=masked`、`reason=squash_replay`，与权威 regrade 的 `containment.metrics.L4` 一致。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共有 8599 个事件、2 个真实故障。代表故障 fault 1 有 8333 个事件，主链只占 11 个，其余 8322 个是旁支；fault 2 有 266 个事件，全部属于另一故障，不并入本链。

1. **同故障的其它含住（`squash_masked` 58 条 + event 68 共 59 条）**：除 event 68 外，其余 58 条最早的 `event_id=1679`（parent=1654，tick=238085666676，VA=`0xffffffc009483740`，PA=`0x81d77740`），最晚的 `event_id=7922`（parent=7915，tick=238095210789，VA=`0xffffffc009483430`，PA=`0x81d77430`），全部 `contained=1`、`outcome=masked`、`reason=squash_replay`。它们都在不同 VA 上重复“收到污染响应→squash”，说明错误在同一页内被反复触发并反复含住；按权威口径，event 1797（其中一条）不得替代 event 68 作为见证。
2. **污染消费（`consumer` 1275 条、`taint_reg` 1654 条）**：覆盖 `arch_reg` 0–9、13、19–24、26–30、35、567 等，最早 tick=238083250428（event 84，parent=82，`phys_reg=253`），最晚 tick=238134809817（event 8330，parent=392）。它们证明同一页内的污染值被大量消费者读取；但这些 consumer 都在旁支，event 68 的 parent 是 36，因此不构成含住见证的 ancestry。
3. **MSHR 填充组（`mshr_fill`/`cache_fill`/`mshr_free` 各 64 条）**：最早 `event_id=40/41/42`（tick=238083242103，`request_id=393913`，`mshr_id=2`、`fill_id=1`、`cache_line=0x81d77980`），最晚 `event_id=6562/6563/6564`（tick=238092391944，`request_id=406042`，`mshr_id=0`、`fill_id=64`、`cache_line=0x81d77200`）。它们是同页其它请求的真实填充记录，但不在 event 68 的祖先上；不能把它们拼进主链来补 L3。
4. **悬空 `errant_commit`（1 条）**：event 83（parent=68，tick=238083249096，`dyn_inst_seq=393846`，`commit_seq=273130`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`）。它是 event 68 的 child，不在 event 68 的祖先上；其有序前缀只到 L0..L3（详见 2.7），按 `_errant_commit_escape` 的公开语义不构成可证 L0→L5 链，因此不推翻 squash 含住，也不被用于构造 L5。
5. **生命周期收口（1 条）**：`event_id=8569`（parent=8330，tick=238721017689，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）。它是流收口记录，不是检测事件。
6. **另一故障 fault 2**：`inj` event_id=8331（tick=238719961413，VA=`0xffffffc0094832c0`，PFN `800000000081d77→1800000800081d77`，`dyn_inst_seq=835662`），权威报告给它的 `terminal=provable_to_L4_then_unknown`（path `8331,8332,8333,8336,8351`），与本链无关；本链的 `fault_id` 始终为 1。

这些旁支对 SDC 诊断的影响是：它们表明同一错误页被反复访问、反复含住（59 次 squash、1275 个 consumer），但都没有改变“权威含住见证是 event 68”这一事实；event 83 的存在使“运行为什么仍然崩溃”成为一个未由本链闭合的问题（本文件不猜测其因果），而 event 1797 只作为同类更晚含住，不能升级为终局。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `detected_contained`（权威报告为 `chain_report.regrade-20261027T103833.json`；同目录 plain `chain_report.json` 为 pre-Task-11b 存档，不用于判定） |
| provable_to | `L5`（报告口径）；实际含住层 L4，`na_layers=["L5"]` |
| 传播终局事件 | `squash_masked` event_id=68，tick=238083244768，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_layer=L4`，`containment_reason=squash_replay` |
| 运行结局 | `Crash`（`run.out` 末尾 `KERNEL PANIC under fault — exiting`；`run.err` 有内核 panic 告警）；崩溃不由本链归因（见 2.8） |
| admitted | `true`（regrade `path=contained`，`violations=[]`） |
| certified | `true`（regrade） |
| violations | `[]`（regrade） |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=2`，与触发器 injected=2、inj 事件 2 条一致） |
| conservation | `ok`（consumer_summary：emitted=1087、suppressed=9768、logical_total=10855、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=8599` 与实际解析事件数 8599 相同；injected/stats/inj 均为 2 |
| campaign/checker 一致性 | regrade 报告 `checker_vs_campaign_agree=true`，`violations=[]` |
| CHAIN_DEMONSTRATED | 是（可证的 L0→L4 连续祖先 + 真实 `contained=1` 含住事件；L5 按口径 N/A） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_CONTAINED_L4`（权威证据表登记） |
| 判定 | **PASS**（附证据张力说明，见下） |

判定说明：本 seed 的全部 15 项一致性检查均通过——引用的事件都存在、父子关系与 tick 单调、地址/掩码/corr/fault_id 取自本 seed、终局与权威 regrade 一致（`detected_contained`，L4 见证 event 68）、含住事件真实存在（`contained=1` + L4 + `squash_replay` + 链关联 corr）、未把 `chain_end` 当 L5、未把 `squash_masked` 写成 L5。需要单独记录的证据张力有两点（不是本文件的判定依据，也不改变权威口径）：其一，运行本身仍以 KERNEL PANIC 结束，而本 fault 的传播在 L4 已含住，崩溃成因未被本链闭合；其二，同流 event 83 是一条 `kind=errant_commit`、`contained=0` 的原始错误提交记录，且 regrade 报告的 `faults_edges` 对 fault 1 写着 `L4->L5=proven`，与 `containment.na_layers=["L5"]` 表面并存；按 checker 对 event 83 的“悬空路径”语义与 canonical 口径，仍以 event 68/L4 为权威终局，event 1797 与 event 83 都不替代它。若后续要判定 run-level 崩溃归因，需要独立证据，本文件不做推断。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed2`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.regrade-20261027T103833.json`（Task-11b 重判；同目录 `chain_report.json` 与 `chain_report.pre-task11b.20261027T103833.json` 为旧判定存档，不用于判定）

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `13ac3a3c79a09571bb5c3314c32c1e1913c3a922de6c3dcbfea87a419a27b65e` | 314930 | 2026-10-25T19:34:09 |
| `chain_report.json` | `601b9d23eb427eeee09fea682fe9d92cff9bd1fe0d15e0a0b20a7a7ea5d869d7` | 918795 | 2026-10-25T19:34:11 |
| `run.out` | `f07c0f93c6cad294a5712ac3125f1d6ee35bc86e3eb68ad2bb60d225d09e337c` | 7745 | 2026-10-25T19:34:10 |
| `run.err` | `542053f2316e00845e96acb4d0f3b335c76fdc87803a2c67dc0821aa4c8332a0` | 1919 | 2026-10-25T19:34:10 |
| `stats.txt` | `e5fef9ee649eef4540bc5119fcb596ee963d8b5eab88c526d83db62ae93d6e65` | 390752 | 2026-10-25T19:34:10 |
| `armtlb_injections.log` | `466a9a2624f2deef54226e5c65064c5ad959a6bc12bddb1ed666fa5338d17d62` | 613 | 2026-10-25T19:34:09 |
| 权威 regrade `chain_report.regrade-20261027T103833.json` | `823cc582a333a45e3b054f476c565332924e1ef5fc8518db954f0f42c8cfbba1` | 3331 | 2026-10-27T10:38:34 |
| 归档 `chain_report.pre-task11b.20261027T103833.json`（旧判定，仅存档） | `601b9d23eb427eeee09fea682fe9d92cff9bd1fe0d15e0a0b20a7a7ea5d869d7` | 918795 | 2026-10-27T10:38:34 |
| manifest `manifest.json` | `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9` | 1778 | 2026-10-25T21:04:38 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | N/A（manifest 无该字段） | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T02-F2-W4 --prop_sample_run_id s2`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3 --cells T02-F2-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `runs/lsu/r6_c9_T02-F2-W4_s2/T02-F2-W4/seed2` — **EXACT_DUPLICATE（prop_evt 字节相同 + 报告语义相同 + run.out 去元数据后相同；也是 regrade 报告的 duplicate_copy）**
- `runs/lsu/r6_p1_T02-F2-W4/T02-F2-W4/seed2` — **INTERRUPTED（无 .done/.exit_code 标记）**
- `runs/lsu/r6_w1_T02-F2-W4/T02-F2-W4/seed2` — **INTERRUPTED（无 .done/.exit_code 标记）**

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
