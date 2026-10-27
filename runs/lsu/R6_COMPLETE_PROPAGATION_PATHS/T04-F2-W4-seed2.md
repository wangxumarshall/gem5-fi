# T04-F2-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T04-F2-W4`；seed：`2`；sample_run_id：`s2`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`pfn_to_mapped_page`（故障类型：换值）。将命中项的 PPN 换成另一个当前合法、相同页大小的 PPN；VPN/ASID 保持一致；不生成任意随机位串。
- frequency tier：`F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type pfn_to_mapped_page --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T04-F2-W4 --prop_sample_run_id s2`
- source head：`fcacc958b799c635babd2834cce9da6942322d91`
- binary source head：`N/A`（该 manifest 不记录 binary_source_head；同 run 的 source_head 见上）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`fcacc958b799c635babd2834cce9da6942322d91`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/manifest.json`（SHA-256 `0f2a7cc4a83aa0e82ba3a5968c02af116a10c2f8a292e8382f4f6343fd503af5`；1775 bytes；mtime `2026-10-25T21:08:03+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`0`，runroot `.done`=存在，`.exit_code`=存在）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；391596 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **210338** 条；`chain_report.event_count`=**205983**（不含 consumer 事件），差值为 consumer 摘要数 4355
- fault_id 数量：**4**（注入日志共 5 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T04-F2-W4 seed2 自己的流。代表故障 fault_id=1，终局 event 42（`errant_commit`）；祖先为 0,1,2,3,4,5,6,7,8,9,10,27,28,29,30,31,32,33,34,35,42（21 个事件）。`path_event_ids=[0,1,2,4,35,42]` 只是层锚点。tick 单调不减；0–4、8–10、27–29、30–32、33–35 分别同 tick。

### 2.1 故障注入前的正常状态

**load**：event 4 `lq_read`，dyn/request=`423605`，VA=`0xffffff807fbce008`，lq_idx=45968。注入前命中项 `vpn=ffffff807fbce`、`asid=206`、`valid=1`、`global=1`、`pfn=ffbce`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=ffbce008`；way=13、entry_index=1，偏移 0x008。正常 PFN=0xffbce、正常 PA=0xffbce008。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`238085994681`，`before=ffbce`、`after=81362`，`field=pfn_to_mapped_page`，VA=`0xffffff807fbce008`，`request_id=423605`，`corr=origin`；注入日志 `old_pfn 0xffbce → new_pfn 0x81362, candidates: 30`。0xffbce（1047502）→0x81362（529250），都是合法 20 位 PFN；偏移 0x008 不变，PA 0xffbce008→0x81362008，effective 变化为真。没有 mask；整页替换，不是位翻转。F2 档允许后续再次注入，本 seed 共有 4 个 fault（见第 5 章），但代表故障是 fault1。

### 2.3 TLB 查询与地址翻译

event 1 读取命中项 pfn ffbce→81362（way=13/entry=1）；event 2 记录 `state_before=ffbce008`、`state_after=81362008`、`pa=81362008`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`contained=0`、`outcome=NoFault`。TLB 没有含住：替换页合法、ap=0 未变、4 KiB 未变。TLB 交付 request_id=423605、PA=0x81362008。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4 `lq_read`（lq_idx=45968）读取错误 PA；本 seed 无 lsq_push/sq_* 事件，记录的是 LQ 读取阶段。错误 PA 被 LQ 接受后进入 cache。

### 2.5 错误如何经过 cache 和 MSHR

event 5 以 `pa=81362008` 访问，event 6 `field=miss`，event 7 分配 mshr_id=1、line 81362008；event 8 访问同页 `pa=81362000`，event 9 miss，event 10 分配 mshr_id=2。event 27（mshr_fill，parent=10）fill_id=1，event 28 cache_fill `pa=81362000`，event 29 mshr_free；event 30 mshr_fill（mshr 0/fill 2），event 31 cache_fill，event 32 mshr_free。错误行同属 0x81362 页，`corr=addr_fallback`；两次 fill/free 是既有 MSHR 序列，不是第二次注入。hit/miss 由 cache_return 判定。

### 2.6 污染如何返回处理器状态

event 33 `resp`（parent=32，tick=`238086054954`）→event 34 `lq_complete`（lq_idx=45968）→event 35 `taint_reg`（parent=34，`arch_reg=20`、`phys_reg=39`、VA=`81362008`、clean→tainted）。这里只有 1 个 taint_reg；它把污染从存储域带入寄存器状态，event 42 随即以它为 parent 提交。

### 2.7 最终传播终局

终局：event 42，`errant_commit`，`parent_event_id=35`，tick=`238086055620`，`dyn_inst_seq=423605`（与 load 相同），`commit_seq=301181`，`pc=ffffffc0087b27b8`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。chain_end 是 event 168928（tick=`238428955377`，fault1 的 errant_commit_seen）；另有 fault2/3/4 的 L4 chain_end 168929/168930/168931。

为什么没有被提前消除：沿 event 42 祖先没有 squash；本 seed 的 133 条 squash_masked 都发生在祖先之外（后续请求/其它 VA），不覆盖这条 load。为什么架构可见：提交越过重定序边界。

### 2.8 从传播终局到系统表现

- 传播终局：L5 event 42，tick=`238086055620`；provable_to=L5。
- 运行结局：**Crash**（oracle=Crash，exit=0）。`run.out` 有 errant_commit 的 CHAOS_DETECT 与大量 Hardware RAS squash_replay，最后 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `warn: Kernel panic in simulated kernel`。
- 注入 tick=`238085994681`，终局 tick=`238086055620`，延迟 **60939 ticks**。
- 因果链：L5 错误提交 → guest kernel panic → Crash。fault2–4 的 L4 结局（chain_end 168929–168931）与 133 次 squash 都是旁支；它们不改变 fault1 的 full 终局。没有应用级输出 oracle。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffff807fbce008，way=13/entry=1 | PFN ffbce→81362 | request_id=423605，PA=81362008 | 错误地址进入 LSU |
| LQ | load lq_idx=45968 | `lq_read` 接受错误 PA | cache 请求 | 错误地址被 LQ 接受 |
| L1D cache | PA=81362008 / line 81362000 | access→miss→fill | miss/fill | 错误行进入 L1D |
| MSHR | line 81362008/81362000 | alloc(1/2)→fill(1/2)→free | 响应 | 错误行完成生命周期 |
| response / LQ complete | request_id=423605 | resp→lq_complete | 可交付污染值 | 回到处理器 |
| register file（taint） | load 数据 | clean→tainted（x20/39） | 被污染寄存器 | 存储→CPU 边界 |
| commit/ROB | dyn 423605 | 无 squash | errant_commit（L5） | 架构可见错误 |


**一句话总括**：T04-F2-W4 seed2 在 tick 238085994681 把 VA=ffffff807fbce008 的 PFN 0xffbce 换成 0x81362，错误 PA=81362008 经 LQ→L1D/MSHR（5–32）→resp/lq_complete（33/34）进入 x20/phys39（35），event 42 真实错误提交；fault2–4 只到 L4，运行结局 Crash。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 4 条 hit 记录；`run.out` 的 `CHAOS_LSU_TRIGGER` 为 `attempted=422996 eligible=413263 injected=4`；`stats.txt` 的 `numFaultsInjected=4`；`chain_report` faults=4。四方一致。fault1 的 PFN 被 event 1/2/3 读取并由 event 4/5 消费，activated 为真；fault2–4 的 `provable_to_L5_then_unknown` 说明它们可证到 L5 但 beyond=Unknown，并未形成 full；它们的 chain_end 是 L4 detected_contained。

### 3.2 故障传播类型

**地址型（wrong physical page）**：PFN 0xffbce→0x81362，错误 PA 0x81362008 被 LQ/cache/MSHR 使用；无 mask，不是 data 位翻转；ap=0 未变，不是 permission；没有控制流改写。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=238085994681）**：错误 PA 离开 TLB，交付 LSU；之后只有 squash/replay 可撤销，而 event 42 的祖先上没有。event 35 的 `taint_reg`（x20/phys 39）是寄存器层不可逆点；event 42 是架构层不可逆点。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；cache/MSHR 无地址正确性检查；本 seed 有 133 条 L4 `squash_masked`，但都在 event 42 的祖先之外，fault2–4 的 chain_end 168929–168931 也均为 L4。RAS 对后续请求有效，但没有覆盖 fault1 的提交。检测盲区：合法页替换无法由权限/有效位发现。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 42）且架构可见；oracle=Crash；无应用级输出 oracle。不称 SDC；归类为 Crash。silent-error 可能存在于提交后到 panic 前的窗口，但本 seed 的实际结局是 kernel panic，不能证明外部可见的未检测数据错误。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed2 的注入是 tick=238085994681、VA=ffffff807fbce008、PFN ffbce→81362、event 42、4 个 fault；seed1 是 238088438901/...3970/81d75→ffbd3/event 40/2 个 fault；seed3 是 238100391603/...3968/81d75→81363/event 54/9 个 fault。三者都 Crash，但地址变化、fault 数、终局与 taint 寄存器不同；本文件只用 seed2 自己的字段。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）终局见证的 `parent_event_id` 单祖先重建；同 tick 事件保留继承顺序。`path_event_ids` 只作层锚点，不作为完整链。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085994681 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 423605 | 423605 | ffffff807fbce008 | — | — | — | ffbce | 81362 | ffbce | 81362 | — | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN ffbce→81362 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 238085994681 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 423605 | 423605 | ffffff807fbce008 | — | — | — | ffbce | 81362 | ffbce | 81362 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce008 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362008 | — | — | — | — | VA=ffffff807fbce008 的命中查找，request_id=423605 | 命中表项返回 pfn=81362 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 238085994681 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 423605 | 423605 | ffffff807fbce008 | 81362008 | — | — | ffbce | 81362 | ffbce | 81362 | — | ffbce008 | 81362008 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=81362008（pfn=81362） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 238085994681 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 423605 | 423605 | ffffff807fbce008 | 81362008 | — | — | — | — | ffbce008 | 81362008 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce008 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362008 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=81362008，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 238085994681 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 423605 | 423605 | ffffff807fbce008 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=423605 的请求，VA=ffffff807fbce008 | request_id=423605 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 238085994681 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 423605 | 423605 | ffffff807fbce008 | 81362008 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81362008 的访问，request_id=423605 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 7 | 6 | 5 | 238085994681 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 423605 | 423605 | — | 81362008 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81362008 的访问，request_id=423605 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 238085994681 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 423605 | 423605 | — | — | 81362008 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81362008，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 9 | 8 | 7 | 238085995014 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 423605 | 423605 | ffffff807fbce008 | 81362000 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81362000 的访问，request_id=423605 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 10 | 9 | 8 | 238085995014 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 423605 | 423605 | — | 81362000 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81362000 的访问，request_id=423605 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 238085995014 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 423605 | 423605 | — | — | 81362000 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81362000，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 12 | 27 | 10 | 238086053955 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 423605 | 423605 | — | — | 81362000 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81362000，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 28 | 27 | 238086053955 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 423605 | 423605 | — | 81362000 | 81362000 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81362000 | pa=81362000 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 14 | 29 | 28 | 238086053955 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 423605 | 423605 | — | — | 81362000 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81362000，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 15 | 30 | 29 | 238086054621 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 423605 | 423605 | — | — | 81362000 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81362000，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 31 | 30 | 238086054621 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 423605 | 423605 | — | 81362000 | 81362000 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81362000 | pa=81362000 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 17 | 32 | 31 | 238086054621 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 423605 | 423605 | — | — | 81362000 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81362000，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 18 | 33 | 32 | 238086054954 | 333 | resp | L3 | response path | 1 | seq_primary | 423605 | 423605 | 81362008 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=423605 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 19 | 34 | 33 | 238086054954 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 423605 | 423605 | ffffff807fbce008 | 81362008 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=423605 的响应 | load 完成（lq_idx=45968） | 错误值被标记为可交付，进入寄存器写回 |
| 20 | 35 | 34 | 238086054954 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 423605 | 423605 | 81362008 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=20，phys_reg=39） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 42 | 35 | 238086055620 | 666 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 423605 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 210338 条原始事件（chain_report 205983 非 consumer；consumer 4355）；主链只取 event 42 的 21 个单祖先。旁支事实：

- `request_fork` 12176 条，主链 0 条；从主链节点 10（4 条）与 35（12172 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=81362000`、`shared_size=1000`；new_request_id 如 423646/423649/423696/…。它们不进入 42 的祖先。
- 旁支 `taint_reg` 13408 条（主链 1：35）；`resp` 11973（主链 1）；`lq_complete` 3597（主链 1）；`squash_masked` 133（主链 0）。
- 133 条 `squash_masked` 均为 L4、contained=1、squash_replay，例如 event 567（VA=ffffff8001362708）、719、869、1171…；它们属于后续请求，不覆盖 event 42。
- `chain_end`：fault1 event 168928（tick=238428955377，L5 errant_commit_seen）；fault2/3/4 分别是 168929/168930/168931，均为 L4 detected_contained。它们不是 L5 见证。
- **其它 fault**：fault2 event 55979（VA=ffffff807fbcedc8，PFN 81362→80c5c，sq_execute，taint 56049，squash 61488）→provable_to_L5_then_unknown；fault3 event 121480（VA=...e2f0，PFN 80c5c→81d74，sq，taint 121544，squash 123673）；fault4 event 164164（VA=...e5e8，PFN 81d74→80c82，sq，taint 164210，squash 165099）。它们都是同 seed 的 F2 后续注入，`provable_to_L5_then_unknown`（chain_end 为 L4），不并入 fault1 的主链。
- consumer 4355 条摘要不在主链。
- 影响：旁支与 fault2–4 证明 F2 频率模型的多次注入和 RAS 的 133 次 L4 响应；fault1 的 event 42 仍未被覆盖，终局 full。


## 6. 最终判定与证据完整性

- terminal：`full`；provable_to：`L5`；传播终局：event 42（errant_commit，tick=238086055620）。
- run outcome：`Crash`（oracle=Crash，exit=0）；kernel panic。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=4355，suppressed=162268，logical_total=166623，issues=[]）。
- count_contradiction：210338−205983=4355（consumer 摘要），已对账。
- campaign/checker agreement：oracle=Crash 与 run.out KERNEL PANIC 一致；checker full/L5 与报告一致；fault2–4 的 `provable_to_L5_then_unknown`/L4 chain_end 不改变 fault1 的 full。
- CHAIN_DEMONSTRATED：**是**；COMPLETE_3_OF_3：**是**。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- 结论：**PASS**。本 seed 的 fault 总数是 4，但代表故障仍是 fault1；不把 fault2–4 的事件号或地址写进主链。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/prop_evt.txt.gz` | SHA-256 `723dd0245c219f0ce96b1e3ae074039a6b3efbcd3f171da7970a294764017b00`；6808267 bytes；mtime `2026-10-25T21:05:29+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/prop_trace.csv.gz` | SHA-256 `f3ab8ef968156189c848ee6bc8b0b6bf2ac9393e9bbecb56341418c90160397f`；1921337 bytes；mtime `2026-10-25T21:05:29+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/chain_report.json` | SHA-256 `42d254ec24c20ac19b91b361f8282ca181fe3537a55301e982bfa41a9e0ab155`；3683687 bytes；mtime `2026-10-25T21:05:45+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/run.out` | SHA-256 `d1c6f37085be42b8dfb321f57a41cfdb6baedbfaaff1a73be8788e0d4cb7e595`；36836 bytes；mtime `2026-10-25T21:05:30+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/run.err` | SHA-256 `7ad31bead8127c09ea7cea7a341885ec295e9b2644bd2f109d4e694c7f8bd612`；2019 bytes；mtime `2026-10-25T21:05:30+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/stats.txt` | SHA-256 `70ea5f44210552067b909d844cf895269b24c3ed9a4a6676d9d9477a6408b63c`；391596 bytes；mtime `2026-10-25T21:05:29+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/manifest.json` | SHA-256 `0f2a7cc4a83aa0e82ba3a5968c02af116a10c2f8a292e8382f4f6343fd503af5`；1775 bytes；mtime `2026-10-25T21:08:03+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3 --cells T04-F2-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`；1145673848 bytes；mtime `2026-10-25T09:22:24+0800`；manifest 记录 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| source head | manifest 字段 | `fcacc958b799c635babd2834cce9da6942322d91`；binary_source_head=`N/A`；analysis_tool_head=`fcacc958b799c635babd2834cce9da6942322d91` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/armtlb_injections.log` | SHA-256 `aa60e45e2692fedd13656c6b484ebad486f0774e57f76a520edc6b0e333a8619`；815 bytes；mtime `2026-10-25T21:05:29+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/board.workload.dmesg` | SHA-256 `10bd48ba1f19a9c53a0a1d19633ec6cfa538fb75e61db1d241c9a2e3079310d8`；12332 bytes；mtime `2026-10-25T21:05:29+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/board.terminal` | SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；0 bytes；mtime `2026-10-25T21:05:01+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/config.ini` | SHA-256 `de1645d5fa13dd0386758e1c9b5bfce596d00678af8a8103ca5bb8d68725e611`；97184 bytes；mtime `2026-10-25T21:05:00+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2/config.json` | SHA-256 `cc41b84fbeb7e2c068263eab7738afdc81dd480a03288b9eff8fbd2717a8da87`；277165 bytes；mtime `2026-10-25T21:05:00+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3/T04-F2-W4/seed2`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_c9_T04-F2-W4_s2/T04-F2-W4/seed2` — **EXACT_DUPLICATE**
- `runs/lsu/r6_p1_T04-F2-W4/T04-F2-W4/seed2` — **INTERRUPTED**

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
