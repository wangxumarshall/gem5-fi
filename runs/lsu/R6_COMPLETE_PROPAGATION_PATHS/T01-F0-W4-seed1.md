# T01-F0-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F0-W4` |
| seed | `1` |
| sample_run_id | `s1` |
| 单元 | `L1d-TLB`（矩阵列"单元"；注入器为 `CHAOSArmTLB`，注入位点为 DTLB 命中表项） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit，只在注入后再次命中才计 activated；每次运行只选一个当前有效且可被后续使用的目标，在指定字段内均匀抽取 1 bit 做一次 XOR，其余字段保持无故障值。**证据实际记录的字段是表项 PFN**（注入日志 `old_pfn`/`new_pfn`，传播事件 `field=bit_flip` + `pfn` 状态），不是 VPN tag；此字段口径差异见 §2.2 与 §6 的不一致记录。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F0` |
| requested tier | `F0` |
| effective tier | `F0` |
| tier enabled | `关闭(0)`（run.out `CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`） |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（与矩阵标签一致：该 rcS 为 TLB page-walk 探针） |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 1 --chaos_propagation --prop_run_id T01-F0-W4 --prop_sample_run_id s1` |
| source head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（manifest.source_head，运行时工作树 HEAD） |
| binary source head | `N/A`（该 manifest 无 `binary_source_head` 字段；不得把运行时 HEAD 当作二进制构建源） |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；本次仅做只读分析，未重跑 gem5。该次运行 manifest 记录的 `analysis_tool_head` 为 `bc82f29d8f69410461d18c07a1ee9314f18885a5`，仅作运行期记录） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`，本次重算） |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` |
| 正常 EOF | **是**（gzip 解压到 EOF 无异常，解压后 4442 字节） |
| exit_code | `0`（manifest.exit_code=0；`.exit_code`=0） |
| truncated | **False**（reader 未触发 EVENT_CAP；`chain_report.truncated=false`） |
| stats 是否有效 | **是**：`stats.txt` 以 `---------- End Simulation Statistics ----------` 收尾；`simTicks=76565396295`、`simInsts=271158710`、`finalTick=314515193310` 均非零且自洽 |
| 原始事件数 | `5` |
| fault_id 数量 | `1`（`fault_id=1`，5 条事件全部归属该 fault） |
| 是否经过离线 regrade | **否**（该 seed 目录内无 `chain_report.regrade-*.json`；权威报告即 `chain_report.json`） |

补充（同一 RunID 的 sealed 配置）：DTLB=32、LQ=16、SQ=16（run.out `LSU-B0 applied`）；检查点 `cpt.237949797015`，`tlb_first_clock 1000 -> 714564955`。

## 2. 完整故障传播过程：从注入到最终结局

本节严格按终局见证的 `parent_event_id` 单祖先链排序：先重建终局见证的祖先，再用 `tick` 校核同 tick/跨 tick 次序。本 seed 的终局见证是 `tlb_translate_result`（event_id=3）——它是唯一带 `contained=1` 的真实含住事件；`chain_end`（event_id=4）只是流关闭记录，不参与传播叙事，也不占 L0–L5 任何一层。祖先链为 0 → 1 → 2 → 3，parent 关系逐条连续，tick 全程等于 237950940537，不存在事件号与 tick 的矛盾。

### 2.1 故障注入前的正常状态

被注入的那次翻译属于一次具体的在飞访问：`dyn_inst_seq=301`、`request_id=301`，VA=`0xffffffc009483fa8`。TLB 表项（`entry_index=0`；记录中 `way=-1`，本文按原值引用，不额外解释其物理含义）在注入前处于完全正常状态：`vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB）、`pa=81d75fa8`。也就是说，VA 的页内偏移是 `0xfa8`，正常物理基址是 `0x81d75 << 12`，正常 PA 是 `0x81d75fa8`。本 seed 的事件流没有记录这次访问是 load 还是 store（链终止在 L2，未出现 LQ/SQ 事件），因此"load vs store"记为 `N/A`，原因是证据未采集，而不是零值。

### 2.2 故障具体如何注入

注入事件是 `event_id=0`，tick=`237950940537`，`site=arm_tlb_lookup_hit`（注入器在"本次查找命中的表项"上落故障），`fault_id=1`，`request_id=301`，`corr=origin`，`field=bit_flip`。注入日志给出的掩码是 `Mask: 0x100000000000000`，即 PFN 的第 56 位。原值 `0x81d75` 与掩码异或后得到 `0x100000000081d75`：用中文完整说一遍这个数值变化——原 PFN 只有低位 `0x81d75`，异或把第 56 位置 1，于是表项里保存的 PFN 变成了 `0x1_0000_0000_81d75`。这是"存储值改变、有效 PA 未改变"的情形：PFN 左移 12 位构成物理地址时，第 56 位会被搬到高位；但证据记录的 effective PA 仍是 `0x81d75fa8`，说明该高位没有出现在本次物化的 PA 中（高位未参与/被丢弃），因此由该 PFN 物化出的 PA 与正常值完全相同。**必须明确写出：PFN 存储值变了，但有效 PA 没有变，因为翻转位落在本次物化 PA 可见的位之外。** 本文不进一步断言该平台的物理地址位宽（不同 seed 记录到的有效 PA 高位并不一致，不能用单一宽度去套所有 seed）。

该注入与 RunID 的故障模型在"每次运行只做一次单比特 XOR、只选当前有效且后续会被使用的表项、激活口径为下游实际读取"这一层面相符；但矩阵把被改字段写成"VPN tag"，而注入日志和表项状态显示被改的是 PFN 字段。这是模型文字与实现字段的口径差异，本文按证据记为 PFN 翻转，绝不改写成 tag 翻转（详见 §6）。

### 2.3 TLB 查询与地址翻译

故障写入后，下一次对该表项的查找立即读到了被污染的存储：`event_id=1`（`tlb_lookup`，parent=0，tick 仍为 237950940537）记录 `field=post_lookup`、`entry_index=0`、`walk_id=0`，`before=81d75`、`after=100000000081d75`。它的 `state_before` 与 `state_after` 逐字段对比说明：只有 `pfn` 从 `81d75` 变成 `100000000081d75`，而同一快照里的 `pa` 仍是 `81d75fa8`；`vpn`、`asid`、`valid`、`global`、`ap`、`mtype`、`page_size` 全部未变。换句话说，查找确实"读到了故障值"，但故障值还没有在地址层面兑现。

紧接着 `event_id=2`（`tlb_pfn`，parent=1）把表项里的 PFN 拿去拼物理地址：该事件显式记录 `pa=81d75fa8`，`state_before=81d75fa8`、`state_after=81d75fa8`，`before/after` 仍是 PFN 的 `81d75→100000000081d75`。这里要说明因果关系：L1 的 lookup 只证明"读到了错误 PFN"，L2 的 `tlb_pfn` 才把它物化为 PA；而物化结果之所以没有变化，正是因为 §2.2 的截断。

真正的裁决发生在 `event_id=3`（`tlb_translate_result`，parent=2，`corr=origin`）：它把 requested PA 与 effective PA 直接比对，记录 `field=effective_pa_unchanged`、`before=81d75fa8`、`after=81d75fa8`，并明确写出 `detection_layer=L2`、`contained=1`、`outcome=NoFault`、`containment_layer=L2`、`containment_reason=effective_pa_unchanged`。`requested vs effective` 两个值都是 `0x81d75fa8`，`effective_pa_changed=false`，因此 `contained=true`。这就是 TLB 交给 LSU 的东西：与无故障情形完全相同的物理地址。run.out 的 `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237950940537 ptag=1 reason=effective_pa_unchanged` 与该事件一一对应。

### 2.4 错误如何进入 LQ/SQ/LSQ

`N/A`。理由是结构性的：本 seed 的事件流在 `tlb_translate_result`（L2）之后没有任何 `lsq_push`/`lq_read`/`sq_execute`/`sq_writeback`/`lq_complete`/`sq_complete` 事件，而查重器也判定 `L2->L3` 为 `missing`。翻译结果已被含住，错误的物理地址没有交给队列；本 seed 的流里不是"进入队列但值为 0"，而是"根本没有这一步"。

### 2.5 错误如何经过 cache 和 MSHR

`N/A`。同理，链上没有 `cache_access`、`cache_return`、`mshr_alloc`、`mshr_fill`、`mshr_free`、`cache_fill` 或 `resp`。故障在 L2 被吸收，没有任何访存请求携带被污染的 PA 到达 cache/MSHR。

### 2.6 污染如何返回处理器状态

`N/A`。链上没有 `taint_reg`、`consumer` 或 `errant_commit`；没有任何寄存器状态被标脏，因此不存在"存储→CPU"边界事件。这是含住语义的直接结果，而不是漏记：该 seed 的 `prop_evt` 只有 5 条事件，全部列在 §4。

### 2.7 最终传播终局

这是含住终局，不是 L5。真实的 `contained=1` 事件是 `tlb_translate_result`（`event_id=3`，tick=`237950940537`，`detection_layer=L2`，`containment_layer=L2`，`reason=effective_pa_unchanged`，`outcome=NoFault`）。阻止故障继续下传的单元是 TLB 的翻译结果比对：它发现 requested PA 与 effective PA 相同，于是显式声明含住并撤销后续关联。后续层全部为 `N/A`：L3=N/A（没有访存请求事件）、L4=N/A（没有寄存器污染）、L5=N/A（没有错误提交）。`chain_end`（`event_id=4`，tick=`314515193310`，`detection_layer=L2`，`outcome=detected_contained`，`corr=none`）只是传播监控退出回调发出的生命周期收口记录，**绝不是 L5，也不构成含住证据**——含住证据只有 event 3。

### 2.8 从传播终局到系统表现

传播终局是 L2 `tlb_translate_result` 含住；`provable_to=L2`；运行结局 `Masked`；`crash_kind=N/A`（没有崩溃）。run.out 中能证明症状的是这一行：

`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237950940537 ptag=1 reason=effective_pa_unchanged`

run.err 只有常规告警，没有 `Kernel oops`；run.out 也没有 `KERNEL OOPS under fault` 行。注入 tick=`237950940537`，传播终局 tick=`237950940537`，传播延迟为 **0 tick**（同一查找/翻译周期内完成检测）。由于没有 L5，`L5→Crash` 的因果链为 `N/A`。负载本身跑完并通过了自带的 md5 oracle：`board.terminal` 记录 `[tlb_probe.rcS] b6d81b360a5672d80c27430f39153e2c rounds ok=10/10`；这说明含住之后系统表现与无故障基线一致，但该结论只覆盖本次负载的自检，不等于对所有数据通路的正确性证明。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L1 DTLB lookup | 对被污染表项的命中查找（req=301, dseq=301） | 读到 `pfn=100000000081d75`，其余字段正常 | 携带错误 PFN 的表项快照 | 故障第一次被下游真实读取（激活） |
| L2 DTLB→MMU PA 物化 | 错误 PFN + 页内偏移 0xfa8 | PFN 左移 12 位并截断到物理地址宽度 | `pa=81d75fa8`（与正常值相同） | 故障在地址层面被截断“抵消” |
| L2 MMU translate result | requested/effective PA | 比对判定 `effective_pa_unchanged` | `contained=1, reason=effective_pa_unchanged` | 显式含住，链在此终止 |
| L0 注入器 | 有效表项 | PFN bit 56 翻转 | 污染表项 | 故障源 |
| L3/L4/L5 | — | — | — | `N/A`（被 L2 含住） |

**整链一句话总结**：本 seed 的注入把 DTLB 表项 PFN 的第 56 位置 1，查找与物化路径确实读到了这个错误 PFN，但该位在物理地址截断时被丢弃，于是有效 PA 仍是 `0x81d75fa8`，TLB 翻译结果比对在 L2 显式判定 `effective_pa_unchanged` 并含住故障，L3/L4/L5 全部不发生，运行以 `Masked` 结束且负载自检 10/10 通过。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

已注入：注入日志 1 条（`Tick: 237950940537, Site: arm_tlb_lookup_hit, ...`）；run.out 的 `CHAOS_LSU_TRIGGER` 记录 `attempted=66310644 eligible=56 injected=1`；`stats.txt` 的 `board.chaos_armtlb.numFaultsInjected=1`。三处计数一致（injected=1 = numFaultsInjected=1 = 注入日志 1 条），不存在计数矛盾。故障值确实被下游读取：`event_id=1` 的 `after=100000000081d75` 就是被 lookup 读出的污染值，`event_id=2` 又把它带入 PA 物化。按矩阵的激活口径（"故障值被下游实际读取、选择或消费"），本 seed 属于 activated。

### 3.2 故障传播类型

按真实事件归类为 **address（地址翻译字段）型**：被污染的是 PFN 存储字段，影响的是"VA→PA"的地址翻译结果。它不是 data 型（没有数据字节被改）、不是 control-state 型（没有改变控制流状态）、不是 permission 型（`ap`/`valid` 未变）；也没有产生 wrong cache line 或 wrong request routing，因为链在 L2 就结束了。需要强调：类型是 address，但有效地址结果没有变化——这就是 §3.3 的含住基础。

### 3.3 首个不可逆传播点

**不存在**。若要指出"最接近不可逆"的位置，是 `event_id=2`（`tlb_pfn`）把错误 PFN 物化的那一刻；但紧接着的 `event_id=3` 判定有效 PA 未变并含住，且没有任何下游单元消费这个物化结果。因此从当前结构看，故障在造成任何不可撤销后果之前就被撤销了。不能用 `chain_end` 伪造一个"不可逆点"。

### 3.4 检测与掩蔽机制

可能发现该故障的机制有三类：TLB 翻译结果的 requested/effective PA 比对、页权限/对齐异常、以及下游 cache/commit 的一致性检查。本 seed 实际生效的是第一类：`event_id=3` 的 `detection_layer=L2` + `contained=1` + `reason=effective_pa_unchanged`，run.out 对应 `CHAOS_DETECT layer=Hardware RAS`。没有触发 squash/replay（本 seed 无 `squash_masked` 事件），也没有在 commit 端暴露。观察到的检测盲点是明确的：该机制只识别"有效 PA 不变"的翻译故障；如果翻转位落在 PA 宽度之内、真正改变了物理地址，它不会拦截（同 RunID 的 seed2 正是这种情况）。

### 3.5 最终 SDC 风险判断

本 seed 没有真实错误提交（无 `errant_commit`），没有架构可见的错误状态，运行结局为 `Masked`，因此**不能判为 SDC**。它不是 Detected-Contained 之外的任何类别：故障被显式检测并在 L2 含住，属于 Detected/Contained（运行级 oracle 记为 Masked）。是否存在静默错误可能性？本 seed 中被污染的 PFN **从未**进入任何寄存器或数据通路（无 `taint_reg`、无 `consumer`），所以没有产生"未被发现的外部可见错误"的证据。负载自带应用级 oracle（md5 10/10）通过；但这只能说明本次负载的输出未受影响，不能外推为"所有应用输出都正确"。

### 3.6 与同 RunID 其他 seed 的关系

只陈述可比事实：

- 注入位点三者相同：`arm_tlb_lookup_hit`，同 RunID 的 DTLB 表项路径。
- 掩码不同：seed1 = `0x100000000000000`（PFN bit 56）、seed2 = `0x800000000`（PFN bit 35）、seed3 = `0x20000000000000`（PFN bit 49）。
- 地址变化不同：seed1 有效 PA 不变（`81d75fa8→81d75fa8`）；seed2 有效 PA 改变（`81d75eb8→800081d75eb8`）；seed3 有效 PA 不变（`81d75eb0→81d75eb0`）。
- 终局不同：seed1 是 L2 `tlb_translate_result` 含住（event 3）；seed2 是 L5 `errant_commit`（event 259）；seed3 是 L2 含住（event 3）。
- 运行结局不同：seed1/seed3 = `Masked`；seed2 = `Crash`。

这三条 seed 共同说明：同一注入点、同一故障类型下，"是否改变有效 PA"由翻转位是否落在 PA 可见宽度内决定，而不是由注入点决定。本节不把 seed2 的地址/事件号引入本 seed 的链。

## 4. 完整主链事件表

说明：`mask` 仅注入事件有意义，取自 `armtlb_injections.log`（`prop_evt` 无 mask 字段）；`layer` 采用 TLB family 的层映射（`inj`=L0、`tlb_lookup`=L1、`tlb_pfn`/`tlb_translate_result`=L2）；`old_pfn/new_pfn` 只对 PFN 事件填写。本链只有 4 条，无需折叠。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | 100000000081d75 | 81d75 | 100000000081d75 | 0x100000000000000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点、单比特预算 | 表项 PFN 被置入 bit56 | 故障进入存储 |
| 2 | 1 | 0 | 237950940537 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | — | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | 100000000081d75 | 81d75 | 100000000081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | — | — | — | field=post_lookup | 同一表项的命中查找 | 污染 PFN 快照（PA 仍正常） | L1 读到故障值（激活） |
| 3 | 2 | 1 | 237950940537 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | — | 301 | 301 | ffffffc009483fa8 | 81d75fa8 | — | — | 81d75 | 100000000081d75 | 81d75 | 100000000081d75 | — | 81d75fa8 | 81d75fa8 | — | — | — | field=bit_flip | 污染 PFN + 偏移 0xfa8 | PA=81d75fa8（截断后不变） | 地址物化，但结果被截断抵消 |
| 4 | 3 | 2 | 237950940537 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | origin | 301 | 301 | ffffffc009483fa8 | 81d75fa8 | — | — | — | — | 81d75fa8 | 81d75fa8 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | 1 | L2 | NoFault | effective_pa_unchanged | requested/effective PA 比对输入 | contained=1，reason=effective_pa_unchanged | 含住终局：故障不下传 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 的原始事件总数是 **5**，全部属于 `fault_id=1`；进入最终祖先链的是 **4** 条（0、1、2、3），未进入祖先链的只有 `chain_end`（`event_id=4`）。不存在 `request_fork`、`consumer`、`taint_reg`、`squash_masked` 或其它 request_id 的旁支，也就不存在"旁支是否回流"的问题。`chain_end` 的分类见 §2.7：它是生命周期收口，不是传播层事件，不影响 SDC 判断。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `detected_contained` |
| provable_to | `L2` |
| propagation terminal event | `tlb_translate_result`，`event_id=3`，tick=`237950940537`，L2 |
| run outcome | `Masked`（`oracle_outcome=Masked`，exit_code=0） |
| admitted | `True`（path=`contained`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常（解压到 EOF 无异常） |
| stats validity | 有效（完整 footer、非零 simTicks/simInsts） |
| conservation | `n/a`（无 consumer summary；`consumer_summary_accounting.conservation=n/a`，issues=[]） |
| count_contradiction | 否（attempted=66310644 > 0，injected=activated=1，numFaultsInjected=1） |
| campaign/checker agreement | 一致：`cell_results.json` 的 seed1 outcome=`Masked`，chain terminal=`detected_contained`，与 run.out 的 `CHAOS_DETECT contained=1` 相符 |
| CHAIN_DEMONSTRATED | 是（代表故障的单祖先链从 `inj` 可证到真实含住事件） |
| COMPLETE_3_OF_3 status | 该 RunID 三个 seed 均完整、certified、admitted；本 seed 状态 `COMPLETE_CONTAINED_L2` |
| verdict | **PASS** |

一致性自检（15 项）：(1) 引用的事件 id 0/1/2/3 均存在于本 seed 流；(2) 每条 parent 均存在；(3) parent 均先于 child；(4) 叙事顺序等于 ancestry 顺序；(5) tick 单调不降；(6) 未混入其它 seed 的身份；(7) VA/PFN/PA/before/after/mask 均来自本 seed 原始事件与注入日志；(8) request_id/corr/fault_id 与原始事件一致；(9) 终局与权威报告一致；(10) 非 full，L5 见证为 `N/A`；(11) 含住见证是真实 `contained=1` 事件 event 3；(12) 每个单元均给出输入/变化/输出/传播意义；(13) 本章为逐事件分析而非复用模板；(14) 无 child 先于 parent 的叙述；(15) SDC 结论未超出证据。

**已知不一致（不影响本 seed 链，但必须记录）**：

1. 矩阵把被注入字段写作"VPN tag"，证据是 PFN 字段翻转（注入日志 `old_pfn/new_pfn`、表项状态 `pfn=`）。
2. 该 seed 的 `manifest.json` 位于 campaign 根目录，mtime 晚于 seed 目录内文件（2026-10-25T16:31:50），属于 campaign 收口时重写；内容与 seed1 的哈希口径一致，不影响 seed 证据本身。

## 7. 原始证据与文件哈希

所有哈希均为本次只读重算（SHA-256），字节数与 mtime 来自 `stat`。

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1/prop_evt.txt.gz` | `b1e54428677e75ce589e35b932e79ea05d6de5fe30bf104ef10e9dc3cad70701` | 887 | 2026-10-25T15:58:52 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1/chain_report.json` | `df1d9cac7209035508cad3f43446c282689482642cafa4a399c0669d1f4d01ab` | 1799 | 2026-10-25T15:58:53 |
| authoritative regrade | `N/A`（无离线 regrade；上行为权威即时报告） | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1/run.out` | `c0b948ea4a177d03f5109d00ee9dd2ae8d9ef7e7d8cf9545b63736fd38e8d05c` | 2070 | 2026-10-25T15:58:53 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1/run.err` | `482bd31fcaaa688cce6887ea0f09d70b62637376b742d7161649bcefc386b41e` | 1834 | 2026-10-25T15:58:53 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1/stats.txt` | `6b13b88ea7c7be2b2d9e407b552500d2755b68dc4cc530c747cb31b00fb76206` | 427682 | 2026-10-25T15:58:53 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` | `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03` | 1771 | 2026-10-25T16:31:50 |
| 启动命令记录 | 同一 `run.out` 的 `command line:` 行（见 §1） | 同 run.out | — | — |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | — | — |
| source head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（仅运行时记录，不宣称是构建源） | — | — | — |
| analysis tool | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173b1a2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 辅助证据（应用 oracle） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1/board.terminal`（`rounds ok=10/10`） | `90adaeabe7ddaa5eb960ca17f36fcf897f9460f1ba5c5df58512abbc314cbcbd` | 678 | 2026-10-25T15:58:27 |

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed1`（`R6-AUTHORITATIVE-EVIDENCE.md` 判定为唯一权威副本）。
- 其它副本：`r6_c9_T01-F0-W4_s1/.../seed1` 为 EXACT_DUPLICATE；`r6_c7_T01-F0-W4_s1/.../seed1` 为 OLD_BINARY_REFERENCE（binary `a9b2c236...`）；`r6_c6_T01-F0-W4/.../seed1` 为 INTERRUPTED；`r6_canary/r6_p1/r6_w1/r6_tlb_F_T01-F0-W4*` 为该 RunID 的其它 campaign 痕迹，按 `R6-AUTHORITATIVE-EVIDENCE.md`/`R6-AUTHORITATIVE-EVIDENCE.json` 的分类口径处理，均不作为本文件证据。
- 原始事件流未被修改；本次未重跑 gem5、未运行 campaign、未修改任何证据文件。
