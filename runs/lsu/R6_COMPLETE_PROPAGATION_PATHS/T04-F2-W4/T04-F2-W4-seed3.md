# T04-F2-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T04-F2-W4`；seed：`3`；sample_run_id：`s3`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`pfn_to_mapped_page`（故障类型：换值）。将命中项的 PPN 换成另一个当前合法、相同页大小的 PPN；VPN/ASID 保持一致；不生成任意随机位串。
- frequency tier：`F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type pfn_to_mapped_page --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T04-F2-W4 --prop_sample_run_id s3`
- source head：`fcacc958b799c635babd2834cce9da6942322d91`
- binary source head：`N/A`（该 manifest 不记录 binary_source_head；同 run 的 source_head 见上）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`fcacc958b799c635babd2834cce9da6942322d91`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/manifest.json`（SHA-256 `0f2a7cc4a83aa0e82ba3a5968c02af116a10c2f8a292e8382f4f6343fd503af5`；1775 bytes；mtime `2026-10-25T21:08:03+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`0`，runroot `.done`=存在，`.exit_code`=存在）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；393356 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **13769** 条；`chain_report.event_count`=**11456**（不含 consumer 事件），差值为 consumer 摘要数 2313
- fault_id 数量：**9**（注入日志共 10 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T04-F2-W4 seed3 自己的流。代表故障 fault_id=1，终局 event 54（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,9,10,11,27,28,29,30,31,32,36,37,38,54（22 个事件）。`path_event_ids=[0,1,2,4,37,54]` 只是层锚点。tick 单调不减；0–4、5–8、9–11、27–29、30–32、36–38 分别同 tick。

### 2.1 故障注入前的正常状态

这是一条 **store**：event 4 `sq_execute`（sq_idx=61201，state_before=issued），dyn/request=`570343`，VA=`0xffffffc009483968`。注入前命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75968`；way=7、entry_index=21，偏移 0x968。正常 PFN=0x81d75、正常 PA=0x81d75968。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`238100391603`，`before=81d75`、`after=81363`，`field=pfn_to_mapped_page`，VA=`0xffffffc009483968`，`request_id=570343`，`corr=origin`；注入日志 `old_pfn 0x81d75 → new_pfn 0x81363, candidates: 30`。0x81d75（531829）→0x81363（529251），合法 20 位 PFN；偏移 0x968 不变，PA 81d75968→81363968，effective 变化为真。没有 mask；整页替换。F2 档在本 seed 注入了 9 个 fault（见第 5 章），但代表故障是 fault1（full）。

### 2.3 TLB 查询与地址翻译

event 1 读取命中项 pfn 81d75→81363（way=7/entry=21）；event 2 记录 `state_before=81d75968`、`state_after=81363968`、`pa=81363968`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`contained=0`、`outcome=NoFault`。TLB 没有含住：替换页合法、ap=0 未变、4 KiB 未变。TLB 交付 request_id=570343、PA=0x81363968 的 store。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `sq_execute`（sq_idx=61201，state_before=issued）把错误 PA 的 store 置于执行态；event 5 `sq_writeback`（parent=4，tick=`238100394600`）以 `pa=81363968` 构造 packet，state_after=packet_built。本 seed 没有 lq_read；错误走 store 路径，SQ 接受错误地址后进入 cache/MSHR。

### 2.5 错误如何经过 cache 和 MSHR

event 6 `cache_access`（pa=81363968）→event 7 `cache_return field=miss`→event 8 `mshr_alloc`（mshr_id=1，line 81363968）；event 9 `cache_access`（pa=81363940）→event 10 miss→event 11 `mshr_alloc`（mshr_id=2，line 81363940）。event 27 `mshr_fill`（fill_id=1）→28 `cache_fill`→29 `mshr_free`；event 30 `mshr_fill`（mshr 0/fill 2）→31 `cache_fill`→32 `mshr_free`。错误行同属 0x81363 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列，不是第二次故障。cache_access 无 hit/miss 字段，由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 36 `resp`（parent=32，tick=`238100454873`）→event 37 `taint_reg`（parent=36，clean→tainted，VA=81363968；`arch_reg`/`phys_reg` 在原始事件中为空，因此不编造寄存器号）→event 38 `sq_complete`（sq_idx=61201，state_after=completed）。event 37 是存储→CPU 边界；event 38 把错误 store 标为完成，event 54 提交。

### 2.7 最终传播终局

终局：event 54，`errant_commit`，`parent_event_id=38`，tick=`238100456205`，`dyn_inst_seq=570353`，`commit_seq=441257`，`pc=ffffffc0087b27c4`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 9908（tick=`9751969912689`，fault1 的 errant_commit_seen），只是生命周期收口；fault2–9 还有各自的 chain_end 9909–9916。

为什么没有被提前消除：沿 event 54 的祖先没有 squash；57 条 squash_masked 都在祖先之外（例如 event 1636 起的多条 VA ...3730/...3448），它们对应后续请求。为什么架构可见：`errant_commit` 越过提交边界。这里也要解释 dyn 不一致：注入 store 的 dyn=570343，而终局 dyn=570353，相差 10；parent=38 指向被污染 store 的完成，`corr=taint_prop` 指向消费者，trace 用 parent 表达“污染源→消费者”，不是同一指令编号抄错。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 54，tick=`238100456205`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。`run.out` 有 errant_commit 的 CHAOS_DETECT 与大量 RAS squash_replay，最后 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `warn: Kernel panic in simulated kernel`。
- 注入 tick=`238100391603`，终局 tick=`238100456205`，延迟 **64602 ticks**。
- 因果链：L5 → kernel panic → Crash。fault2–9 多数只到 L4（chain_end 9909–9916，部分 run_end），不改变 fault1 的 full；没有应用级 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483968，way=7/entry=21 | PFN 81d75→81363 | request_id=570343，PA=81363968 | 错误地址进入 LSU |
| SQ | store sq_idx=61201 | sq_execute→sq_writeback packet_built→sq_complete completed | 错误 store packet | 错误地址被 SQ 接受 |
| L1D cache | PA=81363968 / line 81363940 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 81363968/81363940 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response | request_id=570343 | resp 交付 | 可交付污染值 | 回到处理器 |
| register file（taint） | store 数据 | clean→tainted（arch/phys 未记录） | 被标记状态 | 存储→CPU 边界 |
| commit/ROB | dyn 570353 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T04-F2-W4 seed3 在 tick 238100391603 把 VA=ffffffc009483968 的 PFN 0x81d75 换成 0x81363，错误 PA=81363968 经 SQ（4/5）→L1D/MSHR（6–32）→resp/taint_reg/sq_complete（36–38）传播，event 54 真实错误提交；同 seed 另有 8 个 fault（多为 L4），运行结局 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 9 条 hit 记录；`CHAOS_LSU_TRIGGER` 为 `attempted=943965 eligible=924569 injected=9`；`stats.txt` 的 `numFaultsInjected=9`；`chain_report` faults=9。四方一致。代表 fault1 的 PFN 被 event 1/2/3 读取、event 4/5 消费，activated 为真；fault2–9 的 `provable_to_L4_then_unknown` 表明它们只可证到 L4（未形成 full）；其中部分 chain_end 为 L4 detected_contained，部分为 run_end。

### 3.2 故障传播类型

**地址型（wrong physical page）**：PFN 0x81d75→0x81363，错误 PA 0x81363968 经 SQ/cache/MSHR；无 mask，不是 data/位翻转；ap=0 未变，不是 permission；不是 control-state/timing。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=238100391603）**：错误 PA 离开 TLB 并交付 LSU；之后只有 squash/replay 能撤销，而 fault1 的祖先上没有。event 37 的 `taint_reg`（寄存器号未记录）是寄存器层点；event 54 是架构层点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；L1D/MSHR 无地址正确性检查；本 seed 有 57 条 L4 squash（如 event 1636/1667/1686/1747/1850/1854），均在 fault1 祖先之外；fault2–9 的 chain_end 9909–9916 中，部分为 L4 detected_contained，部分是 run_end。RAS 对后续请求有效，但没有覆盖 event 54。检测盲区：合法页替换无法由现有权限/有效位发现。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 54）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类为 Crash。silent-error 的可能性不能从提交后到 panic 的窗口排除，但没有外部数据错误证据。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed3 的注入是 tick=238100391603、VA=ffffffc009483968、PFN 81d75→81363、event 54、9 个 fault；seed1 是 238088438901/...3970/81d75→ffbd3/event 40/2 个 fault；seed2 是 238085994681/VA ffffff807fbce008/ffbce→81362/event 42/4 个 fault。三者都 Crash，但注入点、地址方向、fault 数和终局不同；本文件不引用其它 seed 的 x19/x20 或 chain_end。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）终局见证的 `parent_event_id` 单祖先重建；同 tick 事件保留继承顺序。`path_event_ids` 只作层锚点，不作为完整链。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238100391603 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 570343 | 570343 | ffffffc009483968 | — | — | — | 81d75 | 81363 | 81d75 | 81363 | — | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→81363 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 238100391603 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 570343 | 570343 | ffffffc009483968 | — | — | — | 81d75 | 81363 | 81d75 | 81363 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75968 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81363;ap=0;mtype=2;page_size=1000;pa=81363968 | — | — | — | — | VA=ffffffc009483968 的命中查找，request_id=570343 | 命中表项返回 pfn=81363 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 238100391603 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 570343 | 570343 | ffffffc009483968 | 81363968 | — | — | 81d75 | 81363 | 81d75 | 81363 | — | 81d75968 | 81363968 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=81363968（pfn=81363） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 238100391603 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 570343 | 570343 | ffffffc009483968 | 81363968 | — | — | — | — | 81d75968 | 81363968 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75968 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81363;ap=0;mtype=2;page_size=1000;pa=81363968 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=81363968，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 238100391603 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 570343 | ffffffc009483968 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | dyn_inst_seq=570343 的请求，VA=ffffffc009483968 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 238100394600 | 2997 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 570343 | — | 81363968 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | dyn_inst_seq=570343 的请求 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 238100394600 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 570343 | 570343 | ffffffc009483968 | 81363968 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81363968 的访问，request_id=570343 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 238100394600 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 570343 | 570343 | — | 81363968 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81363968 的访问，request_id=570343 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 238100394600 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 570343 | 570343 | — | — | 81363968 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81363968，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 9 | 8 | 238100394933 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 570343 | 570343 | ffffffc009483968 | 81363940 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81363940 的访问，request_id=570343 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 238100394933 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 570343 | 570343 | — | 81363940 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81363940 的访问，request_id=570343 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 11 | 10 | 238100394933 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 570343 | 570343 | — | — | 81363940 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81363940，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 27 | 11 | 238100453874 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 570343 | 570343 | — | — | 81363940 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81363940，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 28 | 27 | 238100453874 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 570343 | 570343 | — | 81363940 | 81363940 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81363940 | pa=81363940 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 29 | 28 | 238100453874 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 570343 | 570343 | — | — | 81363940 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81363940，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 30 | 29 | 238100454540 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 570343 | 570343 | — | — | 81363940 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81363940，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 31 | 30 | 238100454540 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 570343 | 570343 | — | 81363940 | 81363940 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81363940 | pa=81363940 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 32 | 31 | 238100454540 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 570343 | 570343 | — | — | 81363940 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81363940，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 36 | 32 | 238100454873 | 333 | resp | L3 | response path | 1 | seq_primary | 570343 | 570343 | 81363968 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=570343 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 37 | 36 | 238100454873 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 570343 | 570343 | 81363968 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 38 | 37 | 238100454873 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 570343 | ffffffc009483968 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | sq_idx=61201 的 store 完成 | store 完成状态 | 错误 store 效果被标记为完成，等待提交 |
| 22 | 54 | 38 | 238100456205 | 1332 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 570353 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 13769 条原始事件（chain_report 11456 非 consumer；consumer 2313）；主链只取 event 54 的 22 个单祖先。旁支事实：

- `request_fork` 1510 条，主链 0 条；从主链节点 11（4 条）与 37（1506 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=81363000`、`shared_size=1000`；new_request_id 如 570353/570354/570358/…。它们不进入 54 的祖先。
- 旁支 `taint_reg` 1668 条（主链 1：37）；`resp` 1417（主链 1）；`lq_complete` 496（主链 0；本 seed 是 store 路径，主链用 sq_complete）；`squash_masked` 57（主链 0）。
- 57 条 `squash_masked` 均为 L4、contained=1、squash_replay，例如 event 1636（VA=ffffffc009483730）、1667（...3448）、1686（...3420）、1747（...33b0）、1850/1854；它们属于后续请求，不覆盖 event 54。
- `chain_end`：fault1 event 9908（tick=9751969912689，L5 errant_commit_seen）；fault2/4/5/8 为 9909/9911/9912/9915（run_end 或 L4）；fault3/6/7/9 为 9910/9913/9914/9916（L4 detected_contained，store_discarded_not_retired）。都只是生命周期/其它故障的收口，不是 fault1 的 L5。
- **其它 fault**：fault2 event 8322（VA=ffffffc008be8af8，PFN 80be8→8138d，lq_read，taint 8341）；fault3 event 9729（VA=...482fb0，PFN 81d74→8138d，sq，taint 9748）；fault4 event 9754（VA=...c730e0，PFN 80c73→80c92，lq，taint 9773）；fault5 event 9784（VA=...c730e0，PFN 80c92→807ea，lq，taint 9803）；fault6 event 9814（VA=...482fb0，PFN 8138d→80c07，sq，taint 9833）；fault7 event 9839（VA=...482fb0，PFN 80c07→ffbce，sq，taint 9858）；fault8 event 9864（VA=...c730e0，PFN 807ea→81363，lq，taint 9873）；fault9 event 9884（VA=...c730e0，PFN 81363→8138d，lq，taint 9903）。它们都是 F2 后续注入，终局均为 L4，不并入 fault1。
- consumer 2313 条摘要不在主链。
- 影响：旁支与 8 个其它 fault 说明 F2 的多次注入；fault1 的 event 54 未被 squash 覆盖，终局 full。


## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 54（errant_commit，tick=238100456205）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel panic。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=2313，suppressed=2817673，logical_total=2819986，issues=[]）。
- count_contradiction：13769−11456=2313（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL PANIC 一致；checker full/L5 与报告一致；fault2–9 的 L4/run_end 不改变 fault1。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- 结论：**PASS**。seed3 有 9 个 fault，代表故障按 escape-first 选 fault1（full）；其余 8 个只到 L4，不能替代 fault1 的 L5，也不能把 fault1 说成含住。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/prop_evt.txt.gz` | SHA-256 `af50e53912fdb35f79240791685576e1e1ae7c5a6bed52c487ba4996263acc93`；462824 bytes；mtime `2026-10-25T21:07:59+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/prop_trace.csv.gz` | SHA-256 `142089149f74c03c851a2d3dd86c5650813aafdba8ee22b38640199f3e6463a8`；139398 bytes；mtime `2026-10-25T21:07:59+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/chain_report.json` | SHA-256 `281bd163b3774e3c322364f9bfb8343f79a3a3322a93345f440fe713cd1dcebf`；1992831 bytes；mtime `2026-10-25T21:08:01+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/run.out` | SHA-256 `2d8f935e87b038299c7c6e0c3f070b86f0f557e20ca4f8ca22951d140b55dad3`；7869 bytes；mtime `2026-10-25T21:08:00+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/run.err` | SHA-256 `7ad31bead8127c09ea7cea7a341885ec295e9b2644bd2f109d4e694c7f8bd612`；2019 bytes；mtime `2026-10-25T21:08:00+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/stats.txt` | SHA-256 `e78d97312de629263db522f7238bf781dffa005baca4e36f6dc49346f78bc2cb`；393356 bytes；mtime `2026-10-25T21:07:59+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/manifest.json` | SHA-256 `0f2a7cc4a83aa0e82ba3a5968c02af116a10c2f8a292e8382f4f6343fd503af5`；1775 bytes；mtime `2026-10-25T21:08:03+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3 --cells T04-F2-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`；1145673848 bytes；mtime `2026-10-25T09:22:24+0800`；manifest 记录 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| source head | manifest 字段 | `fcacc958b799c635babd2834cce9da6942322d91`；binary_source_head=`N/A`；analysis_tool_head=`fcacc958b799c635babd2834cce9da6942322d91` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/armtlb_injections.log` | SHA-256 `8ddd6b912eccd540dea3befd63f8bf02db738566f760a9e8f82a4c80b6c10c68`；1582 bytes；mtime `2026-10-25T21:07:59+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/board.workload.dmesg` | SHA-256 `20d5f04ce4200e2029235dfe1b20c1f13ee5f2e586329946c02d5fab91f13717`；13299 bytes；mtime `2026-10-25T21:07:59+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/board.terminal` | SHA-256 `39f26b34aab371e90fc1bd5766f9ee6877601dd40428971100d4bcfba841c4a8`；1145 bytes；mtime `2026-10-25T21:06:04+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/config.ini` | SHA-256 `92cd3b15de82cdd00a6be337e7fec7ed491b90698d4ea1e07d7e9dd15c55c6ea`；97184 bytes；mtime `2026-10-25T21:05:46+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3/config.json` | SHA-256 `f3d2fb52c72bada6c74beff04ad13d60e65bd6163da81286b2d375c459bb960f`；277165 bytes；mtime `2026-10-25T21:05:46+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed3`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_p1_T04-F2-W4/T04-F2-W4/seed3` — **INTERRUPTED**；本 seed 的权威目录即 `r6_c9_T04-F2-W4_s3`

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
