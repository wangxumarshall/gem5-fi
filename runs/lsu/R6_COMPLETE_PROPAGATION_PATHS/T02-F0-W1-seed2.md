# T02-F0-W1 seed2 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `95ca3830…23db8`）重建；其余文件只读引用。所有字段只来自本 seed。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T02-F0-W1`（模型 ID `T02`，单元 `L1d-TLB`） |
| seed / sample_run_id | `2` / `s2` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**双比特** `bit_flip`（`--tlb_bits_to_change 2`、`--tlb_fault_type bit_flip`） |
| 故障类型 | 双比特翻转 |
| 频率 tier | 请求 `F0` / 生效 `F0` / `lookup_tier_enabled=0` |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）`（矩阵 Excel 行 47） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`（实际为 TLB-AliasPerm 探针，与矩阵标签不一致；见第 6 节） |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T02-F0-W1 --prop_sample_run_id s2` |
| source head | `N/A`（n8 batch manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/manifest.json`（SHA-256 `8d43c17339b4ca3e55a7cd8f792b2dc862d25b7457efa916ccb808eebe1954b4`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n8 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=382169 > 0`，`simTicks=932588145`，等于 `chain_end.tick(238882385160) − checkpoint(237949797015)` |
| 原始事件数 | 433（`chain_report.event_count=433`；`fault_event_count=433`） |
| fault_id 数量 | 1（`fault_id=1`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `237950233911`，请求访问 `0xffffffc009483eb8`，命中 DTLB 第 `0` 号表项（`entry_index=0`、`walk_id=0`、`way=-1`）。注入前状态：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75eb8`。4 KiB 页、偏移 `0xeb8`，正常 PA `0x81d75eb8`。注入事件本 seed 未携带 `dyn_inst_seq`/`request_id`（为空），触发指令只能由后续记录反推。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `237950233911`，`VA=0xffffffc009483eb8`），`field=bit_flip`，`before=0x81d75`，`after=0xc1975`。注入日志 `Mask: 0x40400` 与异或结果一致：**同时翻转 PFN 的第 10 位与第 18 位**。两位都在 48 位 PFN 内，因此都改变有效 PA：`0x81d75 ^ 0x40400 = 0xc1975`，偏移 `0xeb8` 不变，有效 PA = `0xc1975eb8`，`effective_pa_changed=1`。本 seed 没有高位截断，双比特全部生效。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，同 tick）记录 `dyn_inst_seq=0`、`request_id=0`、`corr=addr_fallback`（本 seed 自己的记录，与 seed1 的 `seq_primary` 不同），`state_before.pfn=81d75`、`state_after.pfn=c1975`，`state_before.pa=81d75eb8`、`state_after.pa=c1975eb8`；表项属性未动。`event_id=2`（`tlb_pfn`，parent=1）确认字段替换。与 seed1 不同，本 seed 的主链上没有 `tlb_translate_result`（kind 计数为 1，但不在本祖先上）；“TLB 交给 LSU 什么”由 `event_id=3`（`cache_access`，parent=2，tick `237950235576`，Δtick=1665，`dyn_inst_seq=32`、`request_id=32`）直接体现：它带着 `pa=c1975eb8` 访问 L1D，TLB 未报错。

### 2.4 错误如何进入 LQ/SQ/LSQ

本节 `N/A`。事实依据：本 seed 主祖先中没有 `lq_read`、`lsq_push`、`sq_execute`、`sq_writeback`、`sq_complete`、`mem_req`、`lsq_sendfrag` 任何事件（这些 kind 在整条流里计数为 0），`tlb_pfn`（event 2）之后直接是 `cache_access`（event 3）。因此不能从本 seed 证明 load/store 与队列归属；不借用其它 seed 的队列记录。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=3`（`cache_access`，`pa=c1975eb8`）→ `event_id=4`（`cache_return`，`miss`）→ `event_id=5`（`mshr_alloc`，`mshr_id=1`，`cache_line=c1975eb8`）。`event_id=6`（`cache_access`，parent=5，Δtick=333）访问同行的 `pa=c1975e80`，`event_id=7` 仍 `miss`，`event_id=8` 为 `mshr_id=2` 分配（`cache_line=c1975e80`）。随后是完整的填充序列：`event_id=82`（`mshr_fill`，parent=8，Δtick=104562）把 mshr 2 标为 `filled`（`fill_id=3`），`event_id=83`（`cache_fill`）以 `pa=c1975e80` 填行，`event_id=84`（`mshr_free`）释放 mshr 2；`event_id=85`（`mshr_fill`，Δtick=666）把 `mshr_id=0` 标为 `filled`（`fill_id=4`），`event_id=86`（`cache_fill`）再填同一行，`event_id=87`（`mshr_free`）释放。两次 fill 都针对错误行，cache 无法判断其合法性；整条链仍是同一个故障，因为所有地址都派生自同一个被改写的页基址 `c1975`。

### 2.6 污染如何返回处理器状态

`event_id=88`（`resp`，parent=87，tick `237950341470`，Δtick=333）把数据送回，`va=c1975eb8`；`event_id=89`（`taint_reg`，parent=88）记录 `before=clean`、`after=tainted`（寄存器号未记录），`corr=addr_fallback`。这是存储→CPU 边界：此前是错误地址/数据，此后是体系结构状态被标记为脏。

### 2.7 最终传播终局

真实 L5 是 `event_id=283`（`errant_commit`），parent=`89`，tick `237951341802`（相对 `taint_reg` Δtick=1,000,332），`dyn_inst_seq=391`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b1000`，`commit_seq=161`。未能在提交前消除的原因同前：TLB 无校验、L1D 正常 fill、队列/ROB 无地址一致性检查、提交前无 squash。`chain_end`（`event_id=380`，parent=379，tick `238882385160`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口，不是 L5。

提交之后有一条 `squash_masked`（`event_id=309`，parent=284，tick `237951586890`，`va=ffffffc009483e40`，`pa=c1975e40`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`containment_reason=squash_replay`），它是终局之后的事件，不是终局见证。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=161` 退休（`dyn_inst_seq=391`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `237951341802` 有 `CHAOS_DETECT: layer=None contained=0 tick=237951341802 ptag=1 reason=errant_commit`，在 `237951586890` 另有 `contained=1 reason=squash_replay`，最后 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `Kernel oops in guest`。注入 tick `237950233911` → 终局 `237951341802`，传播时延 `1,107,891` ticks。错误 PA 指向另一物理页，污染提交后 guest 内核 oops，仿真以 Crash 退出；不是 Timeout。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483eb8`、命中第 0 项 | PPN `0x81d75 → 0xc1975`（bit10、bit18 均生效） | PA `0x81d75eb8 → 0xc1975eb8` | 错误翻译被直接消费 |
| LQ/SQ/LSQ | `N/A`（无队列记录） | `N/A` | `N/A` | 不虚构队列归属 |
| L1D | `c1975eb8`/`c1975e80` | 两次 miss，两次 fill | 行填充 | 按错误地址真实取数 |
| MSHR | 行 `c1975eb8`/`c1975e80` | alloc 1/2 → fill/fill → free | `resp`（88） | 缺失管理正常，无地址合法性检查 |
| PRF/寄存器 | 响应数据 | `clean → tainted` | 污染寄存器 | 进入体系结构状态 |
| ROB/提交 | 污染寄存器（dyn 391） | 退休 | `errant_commit`（commit_seq=161） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end` | 生命周期收口 | 非 L5；提交后 squash 309 不影响终局 |

一句话总结：双比特翻转把 PFN 改成 `0xc1975`（两个位都生效），错误 PA `0xc1975eb8` 被 `dyn_inst_seq=32` 直接消费，L1D 两次 miss 后由 MSHR 1/2 完成 alloc→fill→free，响应把寄存器标脏，最终 `dyn_inst_seq=391` 在 `commit_seq=161` 错误退休并导致内核 oops；提交后的 squash 只清理后续消费，不改变 L5 终局。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：1 条 `inj`、1 条 `arm_tlb_lookup_hit`（old `0x81d75`、new `0xc1975`、`Mask: 0x40400`）、`stats.numFaultsInjected=1`、`run.out injected=1`；`attempted=150160`、`eligible=2`、`activated=W3-L0-layer`。坏值被实际读取（`tlb_pfn.after`、`cache_access.pa`）。激活成立。

### 3.2 故障传播类型

**地址型**（错误物理页）。不是数据型、不是 permission、不是 control-state、不是 timing、不是 wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`cache_access`，tick `237950235576`）：本 seed 没有 `tlb_translate_result`，错误 PA 第一次被实际使用就在这里；此后 cache/MSHR/寄存器的全部行为都基于这个错误地址，无法不重放地撤销。

### 3.4 检测与掩蔽机制

TLB 无校验；本 seed 无 translation 结果事件（更无拦截）；L1D/MSHR 只回答命中/缺失；队列/ROB 无一致性检查；提交点不校验。事后 oracle 在 `237951341802` 才报 `errant_commit`。提交后的 squash（event 309）只能清理后续消费，不能撤销已提交错误——这就是观察到的盲区：**检测发生在错误提交之后**。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 283），体系结构可见；运行结局 Crash（内核 oops），故不是 SDC。SDC 需要“对外可见且未被检测到”的错误输出；本样本以 Crash 暴露。无应用级输出 oracle，不能判断数据层面最终正确性；结论限定为“已证真实错误提交 + Crash/DUE”。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 `237950940537`（VA `…3fa8`，掩码 `0x22000`，位 13/17），seed3 `237950233578`（VA `…3eb0`，掩码 `0x10020`，位 5/16）。三者均双比特、单 fault、`full`、Crash，且两个翻转位都在 48 位 PFN 内（不同于 W4 组）。本 seed 的独特处：注入事件缺 `dyn_inst_seq/request_id`、无 LQ/SQ 记录、`tlb_lookup.corr=addr_fallback`。本 seed 的字段未与 seed1/seed3 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=283` 经 `parent_event_id` 回溯的单祖先，共 18 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | — | inj | L0 | TLB | 1 | origin | — | — | ffffffc009483eb8 | — | — | — | 81d75 | c1975 | 81d75 | c1975 | 0x40400 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 237950233911 | 0 | tlb_lookup | L1 | TLB | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | — | — | — | 81d75 | c1975 | 81d75 | c1975 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=c1975;ap=0;mtype=2;page_size=1000;pa=c1975eb8 | — | — | — | — | 命中查询 | PFN 81d75→c1975 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 237950233911 | 0 | tlb_pfn | L2 | TLB | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | c1975eb8 | — | — | 81d75 | c1975 | 81d75 | c1975 | — | 81d75eb8 | c1975eb8 | — | — | — | — | 表项当前状态 | PA 81d75eb8→c1975eb8 | 表项存储被改写 |
| 4 | 3 | 2 | 237950235576 | 1665 | cache_access | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | c1975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483eb8 | 访问 L1D | 按错误 PA 取数 |
| 5 | 4 | 3 | 237950235576 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | c1975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 c1975eb8 | miss | cache 无法判别地址合法性 |
| 6 | 5 | 4 | 237950235576 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | c1975eb8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 c1975eb8 | 分配 MSHR 1 | 错误行进入填充流水 |
| 7 | 6 | 5 | 237950235909 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | c1975e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483eb8 | 访问 L1D | 按错误 PA 取数 |
| 8 | 7 | 6 | 237950235909 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | c1975e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 c1975e80 | miss | cache 无法判别地址合法性 |
| 9 | 8 | 7 | 237950235909 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | c1975e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 c1975e80 | 分配 MSHR 2 | 错误行进入填充流水 |
| 10 | 82 | 8 | 237950340471 | 104562 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | c1975e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 2 填充（fill_id=3） | 错误行取回 |
| 11 | 83 | 82 | 237950340471 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | c1975e80 | c1975e80 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 12 | 84 | 83 | 237950340471 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | c1975e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 缺失处理结束 |
| 13 | 85 | 84 | 237950341137 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | c1975e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 0 填充（fill_id=4） | 错误行取回 |
| 14 | 86 | 85 | 237950341137 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | c1975e80 | c1975e80 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 15 | 87 | 86 | 237950341137 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | c1975e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 0 | 缺失处理结束 |
| 16 | 88 | 87 | 237950341470 | 333 | resp | L3 | L1D | 1 | addr_fallback | 32 | 32 | c1975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 17 | 89 | 88 | 237950341470 | 0 | taint_reg | L4 | PRF | 1 | addr_fallback | 32 | 32 | c1975eb8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 18 | 283 | 89 | 237951341802 | 1000332 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 391） | 错误退休（commit_seq=161） | 真实 L5 |

折叠说明：61 个 `consumer`（event 284–379，tick `237951341802..237965000796`）全在终局之后，不在 event 283 的祖先上，故无 consumer 行；提交后 `squash_masked`（309）不在主链上，见 Ch.5。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（52 条）**：全部 `L3/addr_fallback_broadcast`，`shared_addr=c1975000`、`shared_size=1000`。最早 `event_id=4294967296`，parent=8，`source_event_id=8`、`dest_event_id=9`，把请求 `32` 分叉成 `34`；后续从 8 分叉出 `35/37…`。同一错误页广播，不在 event 283 的祖先上，也不汇入主链。

**提交后的 squash（event 309）**：parent=284（终局后的 consumer），tick `237951586890`，`dyn_inst_seq=520`，`va=ffffffc009483e40`，`pa=c1975e40`，`L4/contained=1/masked/squash_replay`。它在 event 283 之后，不是终局见证，不能把本 seed 改判为含住或 L5。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、2 条 `mshr_fill`、2 条 `cache_fill`、2 条 `mshr_free`、1 条 `resp`、1 条 `taint_reg`；主链外还有 58 条 `cache_access`、58 条 `cache_return`、12 条 `mshr_alloc`、29 条 `mshr_merge`、12 条 `mshr_fill`、12 条 `cache_fill`、12 条 `mshr_free`、51 条 `resp`、52 条 `taint_reg`、4 条 `lq_complete`，均属同一错误页的重复消费者/广播分支，没有回到 event 283 的直接祖先。

**consumer（61 条）**：event 284–379，全在终局之后。**生命周期**：`chain_end`（380）parent=379，tick `238882385160`，`corr=none`、`outcome=errant_commit_seen`；其 `containment_reason=squash_replay` 只是退出回调上下文，不构成含住。本 seed 只有 1 个 fault。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`283`，tick=`237951341802`，parent=`89` |
| run outcome | `Crash`（`KERNEL OOPS under fault`） |
| admitted / certified | `True` / `True`；`violations=[]` |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=382169`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','3','89','283']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T02-F0-W1` = true |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**必须记录的不一致**：矩阵 Excel 行 47 的负载标签是 `MiBench-TC23 论文负载（…）`，且 `记录状态=blocked(fs-infra: SE has no MiBench FS pipeline)`；但本 seed 的 `run.out` 实际使用 `--readfile …/configs/fs/tlb_probe.rcS`。本文件按事实并列二者，不把矩阵标签当作实际负载；这不影响 chain evidence PASS；但 overall_experiment_status 是 NOT_MIBENCH_RESULT，但属于需要上游澄清的元数据不一致。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2/prop_evt.txt.gz` | `95ca3830975997f705573966779b4b03efd8d9eeddb85e5179658b2844923db8` | 16242 | 1793083391 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2/chain_report.json` | `168c05bc7f7e1558ed2006b07c0d752b19efcdcb25fccc0ea84dd2d7f75ecfd7` | 10661 | 1793083392 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2/run.out` | `17ccd0f01b461a2356cb5c136045d4577bb489debab6ed5af4cc0c0fc1d5404a` | 2322 | 1793083392 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` | 1726 | 1793083392 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2/stats.txt` | `270cf724fccb584568d36372fc6194501323d633d469e1850d0bfb2e5106d738` | 381972 | 1793083391 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/manifest.json` | `8d43c17339b4ca3e55a7cd8f792b2dc862d25b7457efa916ccb808eebe1954b4` | 1438 | 1793083393 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| 源码 head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s2/T02-F0-W1/seed2`。

**其它副本与分类**：本 seed 的 n8 运行根下未发现 `.sha8a229009` 型旧二进制副本（只有 `_s1` 根存在该副本）；本文件只使用上表权威目录。
