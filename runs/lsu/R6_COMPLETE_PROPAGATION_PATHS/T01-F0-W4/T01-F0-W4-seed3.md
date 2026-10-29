# T01-F0-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F0-W4` |
| seed | `3` |
| sample_run_id | `s3` |
| 单元 | `L1d-TLB`（矩阵列"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；传播状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F0` |
| requested tier | `F0` |
| effective tier | `F0` |
| tier enabled | `关闭(0)`（run.out `CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`） |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（与矩阵标签一致：rcS 即 TLB page-walk 探针） |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 3 --chaos_propagation --prop_run_id T01-F0-W4 --prop_sample_run_id s3` |
| source head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（manifest.source_head） |
| binary source head | `N/A`（manifest 无 `binary_source_head`；不得以运行时 HEAD 代替） |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5。manifest 记录的运行期 `analysis_tool_head` 为 `bc82f29d...`） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` |
| 正常 EOF | **是**（gzip 解压到 EOF 无异常，解压后 4429 字节） |
| exit_code | `0`（manifest.exit_code=0；`.exit_code`=0） |
| truncated | **False** |
| stats 是否有效 | **是**：完整 footer；`simTicks=76565396295`、`simInsts=271158710`、`finalTick=314515193310` |
| 原始事件数 | `5` |
| fault_id 数量 | `1` |
| 是否经过离线 regrade | **否**（无 regrade 文件） |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`；`tlb_first_clock 1000 -> 714564955`。

## 2. 完整故障传播过程：从注入到最终结局

本 seed 的终局见证是 `tlb_translate_result`（`event_id=3`，唯一真实 `contained=1` 事件）。按 `parent_event_id` 回溯得到唯一祖先链 0 → 1 → 2 → 3；四条事件的 tick 全部等于 `237950233578`。`chain_end`（event 4，tick=`314515193310`）只做生命周期收口，不进入传播叙事。链只有四步、每步 parent 都是上一步，因此没有任何"先讲后半段再回头"的次序问题。

### 2.1 故障注入前的正常状态

在飞翻译的身份是 `dyn_inst_seq=31`、`request_id=31`，VA=`0xffffffc009483eb0`（页内偏移 `0xeb0`）。目标表项（`entry_index=0`，`way=-1`）在注入前正常：`vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75eb0`。访问类型（load/store）在本 seed 事件流中未记录（链止于 L2），记为 `N/A` 并说明是证据缺席。

### 2.2 故障具体如何注入

`event_id=0`，tick=`237950233578`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`request_id=31`，`corr=origin`，`field=bit_flip`。注入日志给出 `Mask: 0x20000000000000`，即 PFN 第 49 位。原 PFN `0x81d75` 与该掩码异或得 `0x20000000081d75`：把这句话说完整——第 49 位原本为 0，翻转后置 1，于是表项里保存的 PFN 从 `0x81d75` 变成 `0x2_0000_0000_81d75`；其余位不变。这个改动只在存储层可见：PFN 参与物理地址构造时要左移 12 位，第 49 位会搬到高位；但证据记录的 effective PA 仍是 `0x81d75eb0`，说明该高位没有出现在本次物化的 PA 中（未参与/被丢弃），因此有效物理地址与正常值相同。**必须明确写出：PFN 存储值改变了，但有效 PA 没有改变，因为翻转位落在本次物化 PA 可见的位之外。**

注入符合该 RunID 模型中的"单次 XOR、选有效表项、以被下游读取作为激活口径"部分；字段层面与矩阵"VPN tag"的措辞差异同样存在（证据是 PFN，见 §6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0）是命中查找本身：`entry_index=0`、`walk_id=0`、`field=post_lookup`，`before=81d75`、`after=20000000081d75`。它的 `state_before/state_after` 对照显示只有 `pfn` 被改写，`pa` 仍是 `81d75eb0`；`vpn`、`asid`、`valid`、`global`、`ap`、`mtype`、`page_size` 全部保持原值。这一步证明"故障值被真实读出"，但尚未兑现为地址。

`event_id=2`（`tlb_pfn`，parent=1）把 PFN 与页内偏移拼装成 PA，记录 `pa=81d75eb0`，且 `state_before=81d75eb0`、`state_after=81d75eb0`。因果上，这就是"错误 PFN 被拿去物化，但物理地址截断把新增高位消掉"的位置。

裁决发生在 `event_id=3`（`tlb_translate_result`，parent=2，`corr=origin`）：`field=effective_pa_unchanged`、`before=81d75eb0`、`after=81d75eb0`，`detection_layer=L2`、`contained=1`、`outcome=NoFault`、`containment_layer=L2`、`containment_reason=effective_pa_unchanged`。requested 与 effective 都是 `0x81d75eb0`，`effective_pa_changed=false`、`contained=true`。TLB 交给 LSU 的是与正常值相同的 PA；run.out 的 `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237950233578 ptag=1 reason=effective_pa_unchanged` 与该事件一一对应。

### 2.4 错误如何进入 LQ/SQ/LSQ

`N/A`。链在 L2 终止，本 seed 事件流中没有任何 `lsq_push`/`lq_read`/`sq_execute`/`sq_writeback`/`lq_complete`/`sq_complete` 记录，查重器也把 `L2->L3` 判为 `missing`。这是结构性缺席：错误 PA 没有被交给任何队列，也谈不上队列内的 `state_before/state_after`。

### 2.5 错误如何经过 cache 和 MSHR

`N/A`。没有 `cache_access`/`cache_return`/`mshr_alloc`/`mshr_fill`/`mshr_free`/`cache_fill`/`resp`，因此没有 cache 命中/未命中、没有 MSHR 状态迁移可解释。链仍属于同一 fault 的证据是 `fault_id=1` 与逐级 `parent_event_id`；这条链根本没有跨入 cache 域。

### 2.6 污染如何返回处理器状态

`N/A`。没有 `taint_reg`、`consumer` 或 `errant_commit`，不存在 clean→tainted 的状态转移，也不存在存储→CPU 边界。

### 2.7 最终传播终局

这是含住终局，不是 L5。真实 `contained=1` 事件：`tlb_translate_result`，`event_id=3`，tick=`237950233578`，`detection_layer=L2`，`containment_layer=L2`，`reason=effective_pa_unchanged`。阻止下传的是 TLB 的翻译结果比对；后续层：L3=N/A（无访存请求）、L4=N/A（无寄存器污染）、L5=N/A（无错误提交）。`chain_end`（`event_id=4`，tick=`314515193310`，`outcome=detected_contained`，`corr=none`）只是流关闭记录，不是 L5、也不是含住证据。

### 2.8 从传播终局到系统表现

传播终局为 L2 `tlb_translate_result` 含住，`provable_to=L2`；运行结局 `Masked`；无崩溃（`crash_kind=N/A`）。run.out 的症状证据：

`CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237950233578 ptag=1 reason=effective_pa_unchanged`

run.err 无 `Kernel oops`，run.out 无 `KERNEL OOPS under fault`。注入 tick=`237950233578`，终局 tick=`237950233578`，传播延迟 **0 tick**。L5→Crash 因果链 `N/A`。负载跑完且应用级 oracle 通过：`board.terminal` 记录 `[tlb_probe.rcS] b6d81b360a5672d80c27430f39153e2c rounds ok=10/10`。这只证明本次负载的自检未被触发，不能外推为任意应用输出都正确。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L1 DTLB lookup | 命中被污染表项（req=31, dseq=31） | `pfn` 读成 `20000000081d75` | 污染表项快照 | 激活：下游真实读取 |
| L2 DTLB→MMU PA 物化 | 污染 PFN + 偏移 0xeb0 | 移位并截断到物理地址宽度 | `pa=81d75eb0`（未变） | 高位被截断抵消 |
| L2 MMU translate result | requested/effective PA | 比对为相同 | `contained=1, effective_pa_unchanged` | 显式含住，L3–L5 不发生 |
| L0 注入器 | 有效表项 | PFN bit49 翻转 | 污染表项 | 故障源 |
| L3/L4/L5 | — | — | — | `N/A`（被 L2 含住） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 49 位置 1；查找与物化都读到了这个错误 PFN，但该位在物理地址截断时被丢弃，PA 仍是 `0x81d75eb0`，翻译结果比对于 L2 判定 `effective_pa_unchanged` 并含住故障，L3/L4/L5 全部不发生，运行以 Masked 结束且负载自检 10/10 通过。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；run.out `CHAOS_LSU_TRIGGER: attempted=66310644 eligible=1 injected=1`；`stats.txt numFaultsInjected=1`。三者一致（injected=1 = stats=1 = 日志 1 条；attempted 远大于 0）。被污染的值被下游真实读取：`event_id=1` 的 `after` 与表项状态 `pfn` 都是 `0x20000000081d75`，`event_id=2` 还把它用于 PA 物化。按激活口径属于 activated。

### 3.2 故障传播类型

**address 型（地址翻译字段）**：污染字段是 PFN，直接影响 VA→PA；不是 data 型、不是 control-state、不是 permission（`ap`/`valid` 未变）、不是 timing、也不是 wrong cache line / wrong request routing（链未进入 cache 或请求路由层）。与 seed1 一样，类型是 address，但有效地址结果不变。

### 3.3 首个不可逆传播点

**不存在**。最接近的位置是 `event_id=2`（物化错误 PFN），但其结果在 `event_id=3` 被判定为"有效 PA 未变"并含住，且没有任何下游消费者。用 `chain_end` 冒充不可逆点是禁止的。

### 3.4 检测与掩蔽机制

候选机制包括翻译结果 PA 比对、权限/对齐异常、下游一致性与 commit 检查。本 seed 生效的是第一类（`detection_layer=L2`、`contained=1`、`reason=effective_pa_unchanged`，run.out `CHAOS_DETECT layer=Hardware RAS`）。没有 squash/replay（无 `squash_masked`），也没有 commit 暴露。盲点：该机制只捕捉 PA 不变；翻转位若落在 PA 宽度内则不会被捕捉（同 RunID 的 seed2 即为反例）。

### 3.5 最终 SDC 风险判断

没有真实 errant commit，没有架构可见错误，运行结局 Masked，故不判 SDC；属于 Detected/Contained（运行级 Masked）。本 seed 的污染 PFN 没有进入任何寄存器或数据通路（无 `taint_reg`/`consumer`），没有"未被发现的外部可见错误"证据。应用级 oracle（md5 10/10）通过，但只覆盖本次负载自检，不能作为所有数据正确的证明。

### 3.6 与同 RunID 其他 seed 的关系

- 注入位点相同：`arm_tlb_lookup_hit`。
- 掩码：seed1=`0x100000000000000`（bit56）、seed2=`0x800000000`（bit35）、seed3=`0x20000000000000`（bit49）。
- 有效 PA 变化：seed1 不变（`81d75fa8→81d75fa8`）、seed2 改变（`81d75eb8→800081d75eb8`）、seed3 不变（`81d75eb0→81d75eb0`）。
- 终局：seed1=L2 含住 event3；seed2=L5 errant_commit event259；seed3=L2 含住 event3。
- 运行结局：seed1/seed3=Masked；seed2=Crash。
- 本 seed 与 seed1 的统计面完全相同（`simTicks`/`finalTick` 一致），但注入 VA/tick/mask 不同，说明二者是同一负载的不同注入抽样，不是同一事件的重复。

本 seed 的结论只用本 seed 的事件号与地址。

## 4. 完整主链事件表

`mask` 取自 `armtlb_injections.log`；`layer` 用 TLB family 层映射；`old_pfn/new_pfn` 仅对 PFN 事件填写。4 条事件，无需折叠。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 20000000081d75 | 81d75 | 20000000081d75 | 0x20000000000000 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit49 被置 1 | 故障进入存储 |
| 2 | 1 | 0 | 237950233578 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | — | 31 | 31 | ffffffc009483eb0 | — | — | — | 81d75 | 20000000081d75 | 81d75 | 20000000081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN，PA 正常 | 激活 |
| 3 | 2 | 1 | 237950233578 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | — | 31 | 31 | ffffffc009483eb0 | 81d75eb0 | — | — | 81d75 | 20000000081d75 | 81d75 | 20000000081d75 | — | 81d75eb0 | 81d75eb0 | — | — | — | field=bit_flip | 污染 PFN + 偏移 | PA=81d75eb0（截断） | 物化被抵消 |
| 4 | 3 | 2 | 237950233578 | 0 | `tlb_translate_result` | L2 | MMU translate | 1 | origin | 31 | 31 | ffffffc009483eb0 | 81d75eb0 | — | — | — | — | 81d75eb0 | 81d75eb0 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0 | 1 | L2 | NoFault | effective_pa_unchanged | requested/effective PA | contained=1 | 含住终局 |

## 5. 相关旁支与未进入最终主链的事件

原始事件 5 条，全部 `fault_id=1`；主链 4 条（0/1/2/3）；未进入主链的只有 `chain_end`（event 4）。没有 `request_fork`、`consumer`、`taint_reg`、`squash_masked`，也没有其它 request_id，因而不存在旁支回流与否的问题。`chain_end` 只是生命周期标记，不影响 SDC 判断。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `detected_contained` |
| provable_to | `L2` |
| propagation terminal event | `tlb_translate_result`，event_id=3，tick=237950233578，L2 |
| run outcome | `Masked`（oracle_outcome=Masked，exit_code=0） |
| admitted | `True`（path=`contained`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效（完整 footer、非零 simTicks/simInsts） |
| conservation | `n/a`（无 consumer summary） |
| count_contradiction | 否（attempted=66310644 > 0；injected=1=stats=1） |
| campaign/checker agreement | 一致（cell_results seed3 outcome=Masked；chain terminal=detected_contained） |
| CHAIN_DEMONSTRATED | 是 |
| COMPLETE_3_OF_3 status | 三个 seed 证据齐全且 certified；本 seed `COMPLETE_CONTAINED_L2` |
| verdict | **PASS** |

一致性自检：引用事件 0/1/2/3 全部存在；parent 连续且先于 child；叙事顺序=ancestry 顺序；tick 单调；未混入 seed1/seed2 的身份；VA/PFN/PA/before/after/mask 全部来自本 seed 事件与注入日志；request_id/corr/fault_id 一致；终局与权威报告一致；非 full 故 L5 见证 `N/A`；含住见证是真实 `contained=1` 的 event 3；每个单元均给出输入/变化/输出/意义；本章按本 seed 自身数据写成；无 child 先于 parent 的叙述；SDC 结论未越界。

**已知不一致**：矩阵把被注入字段写作"VPN tag"，证据显示为 PFN 字段翻转。其余字段与权威报告一致。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/prop_evt.txt.gz` | `1db3d9275cfb56a0ca13007c9a009ac987f514d9d49c9ed14e0430dcbcc1aa92` | 887 | 2026-10-25T16:31:47 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/chain_report.json` | `2240b159cf91856dfabd62429831e898260382f236a30b21b74afc5f6c41114e` | 1799 | 2026-10-25T16:31:48 |
| authoritative regrade | `N/A`（无 regrade；上行为权威即时报告） | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/run.out` | `25506842d89af7d85f3df1213179a3bbb361373878411c958f1f95fea071decd` | 2069 | 2026-10-25T16:31:48 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/run.err` | `482bd31fcaaa688cce6887ea0f09d70b62637376b742d7161649bcefc386b41e` | 1834 | 2026-10-25T16:31:48 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/stats.txt` | `05fc4895e060abd97487d112dd6d740ac15279bed656f22bd06b94da9c54d198` | 427682 | 2026-10-25T16:31:48 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` | `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03` | 1771 | 2026-10-25T16:31:50 |
| 启动命令记录 | run.out 的 `command line:` 行（§1） | 同 run.out | — | — |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | — | — |
| source head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（仅运行时记录） | — | — | — |
| analysis tool | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 辅助证据（应用 oracle） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/board.terminal`（`rounds ok=10/10`） | `90adaeabe7ddaa5eb960ca17f36fcf897f9460f1ba5c5df58512abbc314cbcbd` | 678 | 2026-10-25T16:31:22 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3`（`R6-AUTHORITATIVE-EVIDENCE.md` 判定为唯一权威副本）。
- 其它副本：`r6_c9_T01-F0-W4_s1`/`_s2` 内的同名 seed（若存在）为 EXACT_DUPLICATE 或未完成 campaign 的副本；`r6_c7_T01-F0-W4_s1` 内的 seed3 为 OLD_BINARY_REFERENCE；其它 `r6_c6/r6_p1/r6_w1/r6_tlb_F` 目录为设计/试验痕迹。以上分类以 `R6-AUTHORITATIVE-EVIDENCE.md` 为准，均不作为本文件证据。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
