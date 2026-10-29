# T02-F0-W4 seed2 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `32f66098…cfd6`）重建；`chain_report.json`、`manifest.json`、`run.out`、`run.err`、`stats.txt`、`armtlb_injections.log` 均按只读引用。本 seed 与其兄弟 seed 的 event_id、tick、地址、状态不共用。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T02-F0-W4`（模型 ID `T02`，单元 `L1d-TLB`） |
| seed / sample_run_id | `2` / `s2` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**双比特** `bit_flip`（`--tlb_bits_to_change 2`、`--tlb_fault_type bit_flip`、`--tlb_probability 1.0`） |
| 故障类型 | 双比特翻转 |
| 频率 tier | 请求 `F0` / 生效 `F0` / `lookup_tier_enabled=0` |
| workload 矩阵标签 | `TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`（矩阵 Excel 行 48） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`；`--kernel …/gem5-fs/vmlinux`、`--disk …/gem5-fs/ubuntu.img`、`--bootloader …/gem5-fs/boot.arm64`、`--cpu O3`、`--restore-checkpoint …/fs_cpt_boot/cpt.237949797015` |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T02-F0-W4 --prop_sample_run_id s2`（`--tlb_rng_seed` 取值见 `run.out` 原文；本条按 run.out 逐字复制） |
| source head（run-time manifest） | `bc82f29d8f69410461d18c07a1ee9314f18885a5` |
| binary source head | `N/A` —— run-level manifest 无 `binary_source_head`；`source_head` 只是运行期工作树 HEAD |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json`（SHA-256 `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；manifest `gem5_exit_code=0`、`campaign_exit_code=0`、`done_marker=true`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=382360 > 0`，`simTicks=932894838`，等于 `chain_end.tick(238882691853) − checkpoint(237949797015)` |
| 原始事件数 | 403（`chain_report.event_count=403`；`fault_event_count=403`） |
| fault_id 数量 | 1（`fault_id=1`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`，无 `*regrade*` 文件） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

在 tick `237950233911`，一条访问虚拟地址 `0xffffffc009483eb8` 的请求命中 DTLB 第 `0` 号表项（`entry_index=0`、`walk_id=0`、`way=-1`）。注入前的表项状态是 `vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75eb8`：页大小 4 KiB，页内偏移 `0xeb8`，正常物理地址应为 `0x81d75eb8`。这一 seed 的注入事件本身**没有**携带 `dyn_inst_seq`/`request_id`（两个字段为空），所以“哪条指令触发这次注入”只能由紧随其后的 `tlb_lookup`/`cache_access` 记录反推；这一点与 seed1/seed3 不同，属于原始流的记录差异，不应补造。

### 2.2 故障具体如何注入

注入是 `event_id=0`（`kind=inj`，`fault_id=1`，tick `237950233911`，`va=0xffffffc009483eb8`）。`field=bit_flip`，`before=0x81d75`，`after=0x1000000800081d75`。注入日志给出的 `Mask: 0x1000000800000000` 与 `before ^ after` 一致：**同时翻转 PFN 的第 35 位与第 60 位**。第 35 位位于 48 位 PFN 的有效宽度内，第 60 位高出该宽度；在把 PFN 拼成物理地址时只保留低 48 位，因此第 60 位被截掉，有效 PFN 变成 `0x800081d75`（`0x81d75 ^ 0x8000000000`，即第 35 位置 1），页内偏移 `0xeb8` 不变，有效 PA = `0x800081d75eb8`，`effective_pa_changed=1`。这里必须说清楚两件事：**存储的 PFN 值确实变了（两个位都被写入），有效 PA 也变了**；被“吞掉”的只是第 60 位，而不是整个故障。对 `T02`（双比特）模型来说，这是一次真实的双位写入 + 单一位有效改变。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，同 tick）记录了这次命中查询：`dyn_inst_seq=0`、`request_id=0`、`corr=addr_fallback`（这三个字段的值与 seed1/seed3 的 `seq_primary` 不同，属于本 seed 自己的记录），`state_before.pfn=81d75`、`state_after.pfn=1000000800081d75`，`state_before.pa=81d75eb8`、`state_after.pa=800081d75eb8`，`valid/global/asid/ap/mtype/page_size` 未变。`event_id=2`（`tlb_pfn`，parent=1）确认 `pa=800081d75eb8`、`before=81d75`、`after=1000000800081d75`。与 seed1/seed3 不同，本 seed 的主链上**没有** `tlb_translate_result` 事件（kind 计数为 1，但那一条在另一条分支上），因此“TLB 交给 LSU 什么”由紧接着的 cache 访问直接体现：`event_id=3`（`cache_access`，parent=2，tick `237950235576`，Δtick=1665）以 `dyn_inst_seq=32`、`request_id=32`、`pa=800081d75eb8` 访问 L1D。也就是说，TLB 没有报错（没有 `contained=1`、没有 `outcome`），错误 PA 被直接消费。

### 2.4 错误如何进入 LQ/SQ/LSQ

本节为 `N/A`，原因是原始流的事实：本 seed 的主祖先里没有 `lq_read`、`lsq_push`、`sq_execute`、`sq_writeback`、`sq_complete`、`mem_req`、`lsq_sendfrag` 中任何一类事件（kind 计数中这些 kinds 均为 0），`tlb_pfn`（event 2）之后直接就是 `cache_access`（event 3，`dyn_inst_seq=32`）。因此无法从本 seed 的事件流证明它是 load 还是 store、进入了哪个队列槽位；能确定的只有“错误翻译被 `dyn_inst_seq=32` 的访问消费”。按诚实口径写 `N/A`，不借用 seed1/seed3 的 SQ 记录，也不推断队列号。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=3`（`cache_access`）按错误 PA `0x800081d75eb8` 访问 L1D；`event_id=4`（`cache_return`）给出 `field=miss`。`event_id=5`（`mshr_alloc`，parent=4）分配 `mshr_id=1`，`cache_line=800081d75eb8`，`state_after=mshr_allocated`。随后 `event_id=6`（`cache_access`，parent=5，Δtick=333）换成 `pa=800081d75e80`（与 `…eb8` 同一条 64 字节 cache line），`event_id=7` 仍是 `miss`，`event_id=8` 分配 `mshr_id=2`（`cache_line=800081d75e80`）。两次访问都落在同一个错误物理页的同一行内，MSHR 1 与 2 分别登记。之后 `event_id=60`（`resp`，parent=8，tick `237950344134`，Δtick=108225）返回数据，`va=800081d75eb8`。与 seed1 一样，本 seed 的流里没有 `mshr_fill`/`mshr_free`（kind 计数为 0），响应直接挂在 `mshr_alloc` 之后；这是记录缺失，不是“没有填充”。为什么这仍是同一个故障：两次 cache 访问的 PA 都落在 `0x800081d75` 这一个被改写的页基址上，MSHR 的行地址也由它派生，没有任何一级换成了别的地址。

### 2.6 污染如何返回处理器状态

`event_id=60`（`resp`）把数据送回处理器侧，`corr=addr_fallback`。`event_id=61`（`taint_reg`，parent=60，同 tick）记录 `before=clean`、`after=tainted`、`va=800081d75eb8`；`arch_reg`/`phys_reg` 在本 seed 为空，故只能陈述“目的寄存器被标记为 tainted”，不能给出寄存器编号。`taint_reg` 是存储→CPU 的边界：在它之前错误表现为错误的物理地址与由它取回的数据，结构没有任何一级把它当成错误；在它之后，体系结构状态第一次被显式标记为脏，后续依赖该寄存器的指令会继续携带污染。

### 2.7 最终传播终局

真实 L5 见证是 `event_id=259`（`errant_commit`），parent=`61`，tick `237951515628`（相对 `taint_reg` Δtick=1,171,494），`dyn_inst_seq=391`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b1000`，`commit_seq=161`。为什么没被提前消掉：错误的 PA 在 TLB 层无校验、L1D/MSHR 只按地址服务、LSQ/ROB 没有地址一致性检查；这个 seed 也没有发生 squash，因此一条依赖污染寄存器的指令在 `commit_seq=161` 退休。`chain_end`（`event_id=350`，parent=349，tick `238882691853`）只是生命周期收口（`corr=none`、`outcome=errant_commit_seen`），不是 L5，也不构成含住证据。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=161` 退休（`dyn_inst_seq=391`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 tick `237951515628` 有 `CHAOS_DETECT: layer=None contained=0 tick=237951515628 ptag=1 reason=errant_commit`，与 event 259 对齐；随后是 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`，`run.err` 为 `Kernel oops in guest`。注入 tick `237950233911` → 终局 tick `237951515628`，传播时延 `1,281,717` ticks。系统表现与本链的因果一致：错误 PA `0x800081d75…` 指向另一个物理页，取回的错误数据经寄存器提交后让 guest 内核 oops。不是 Timeout，仿真在预算内正常走到崩溃退出。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483eb8`、命中第 0 项 | PPN `0x81d75 → 0x800081d75`（bit35；bit60 越 48 位被截） | PA `0x81d75eb8 → 0x800081d75eb8` | 错误翻译被消费，无告警 |
| LQ/SQ/LSQ | `N/A`（本 seed 无队列事件记录） | `N/A` | `N/A` | 不能证明队列归属，不虚构 |
| L1D | 错误页内 `…eb8`/`…e80` 两地址 | 两次 miss | miss 路径 | 按错误地址做真实缺失 |
| MSHR | `800081d75eb8`、`800081d75e80` | `mshr_alloc` 1、2 | `resp`(event 60) | 错误地址被当作正常缺失 |
| PRF/寄存器 | 响应数据 | `clean → tainted`（寄存器号未记录） | 污染寄存器 | 错误进入体系结构状态 |
| ROB/提交 | 污染寄存器（dyn 391） | 退休 | `errant_commit`（commit_seq=161） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end` | 生命周期收口 | 非 L5 |

一句话总结：双比特翻转把第 0 号 TLB 表项的 PPN 改成 `0x800081d75`（第 60 位被 48 位 PFN 截断，第 35 位生效），错误 PA `0x800081d75eb8` 被 `dyn_inst_seq=32` 直接送进 L1D，两次 miss 分别登记 MSHR 1/2，响应回来后寄存器被标脏，最终 `dyn_inst_seq=391` 在 `commit_seq=161` 错误退休并导致内核 oops；本 seed 的流没有 LQ/SQ 记录，也没有 fill/free 记录，这两处缺失按事实标注，不影响“错误 PA 确实被消费并最终逃逸”的结论。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：`prop_evt` 1 条 `inj`（fault_id=1），`armtlb_injections.log` 1 条 `Site: arm_tlb_lookup_hit`（old `0x81d75`、new `0x1000000800081d75`、`Mask: 0x1000000800000000`），`stats.txt` `numFaultsInjected=1`，`run.out` `injected=1`。`attempted=150260`、`eligible=2`、`injected=1`，`activated=W3-L0-layer`。坏值被下游实际读取：`tlb_lookup.state_after.pfn`、`tlb_pfn.after`、`cache_access.pa` 都带 `0x800081d75…`。激活成立。

### 3.2 故障传播类型

**地址型**。被改的是 TLB PPN，传播的是 PA；cache/MSHR 侧表现为对另一个物理页的正常 miss。不是数据型（没有对数据字做位翻转）、不是 permission（`ap` 未动）、不是 control-state（无异常状态被改）、不是 timing、不是 wrong cache line（行地址由错误 PA 直接派生）。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=3`（`cache_access`，tick `237950235576`）：在本 seed 里没有 `tlb_translate_result` 记录，错误 PA 第一次被 LSU/L1D 实际使用就发生在这里。此前 `event_id=2` 只改了表项存储（可被 refill 覆盖），而 `event_id=3` 已经用一个错误物理地址发起了真实 cache 访问，本结构无法在不重放的情况下撤销。

### 3.4 检测与掩蔽机制

TLB 无校验；translation 结果层在本 seed 没有事件记录（更没有拦截）；L1D/MSHR 只回答命中/缺失；LSQ/ROB 无地址一致性检查；提交点不校验。唯一“检测”是事后 oracle（`CHAOS_DETECT reason=errant_commit`）。观察到的盲区：**48 位 PFN 内的位翻转在提交前完全不可见**；第 60 位这类越界位会被静默截断，既不报错也不改变 PA，容易被误读成“良性”，但同一注入的另一位（第 35 位）已经改变了有效 PA。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 259），体系结构可见；系统以 oops 暴露，故归类 **Crash**，不是 SDC。SDC 需要“对外可见且未被检测到的错误输出”；本样本运行结局是显式崩溃，错误被暴露。本 workload 无应用级输出 oracle，无法判断数据层面最终是否正确，因此不能据此宣称“数据没错”，只能宣称“已证真实错误提交 + Crash”。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入在 `237950940537`（VA `…3fa8`，掩码 `0x100040000000000`，位 42/56），seed3 在 `237950233578`（VA `…3eb0`，掩码 `0x20000000040000`，位 18/53）。三者都是双比特、单 fault_id、`full`、Crash；都属“高位被 48 位 PFN 截断、低位改写 PA”。本 seed 的独特处是：注入事件缺 `dyn_inst_seq/request_id`、主链缺少 LQ/SQ 与 fill/free 记录、`tlb_lookup.corr=addr_fallback`。本 seed 的字段未与 seed1/seed3 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=259` 经 `parent_event_id` 回溯的单祖先，共 12 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | — | inj | L0 | TLB | 1 | origin | — | — | ffffffc009483eb8 | — | — | — | 81d75 | 1000000800081d75 | 81d75 | 1000000800081d75 | 0x1000000800000000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 237950233911 | 0 | tlb_lookup | L1 | TLB | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | — | — | — | 81d75 | 1000000800081d75 | 81d75 | 1000000800081d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=1000000800081d75;ap=0;mtype=2;page_size=1000;pa=800081d75eb8 | — | — | — | — | 命中查询 | PFN 81d75→1000000800081d75 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 237950233911 | 0 | tlb_pfn | L2 | TLB | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | 800081d75eb8 | — | — | 81d75 | 1000000800081d75 | 81d75 | 1000000800081d75 | — | 81d75eb8 | 800081d75eb8 | — | — | — | — | 表项当前状态 | PA 81d75eb8→800081d75eb8 | 表项存储被改写 |
| 4 | 3 | 2 | 237950235576 | 1665 | cache_access | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 800081d75eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483eb8 | 访问 L1D | 按错误 PA 取数 |
| 5 | 4 | 3 | 237950235576 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | 800081d75eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 800081d75eb8 | miss | cache 无法判别地址合法性 |
| 6 | 5 | 4 | 237950235576 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 800081d75eb8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 800081d75eb8 | 分配 MSHR 1 | 错误行进入填充流水 |
| 7 | 6 | 5 | 237950235909 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 800081d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483eb8 | 访问 L1D | 按错误 PA 取数 |
| 8 | 7 | 6 | 237950235909 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | 800081d75e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 800081d75e80 | miss | cache 无法判别地址合法性 |
| 9 | 8 | 7 | 237950235909 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 800081d75e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 800081d75e80 | 分配 MSHR 2 | 错误行进入填充流水 |
| 10 | 60 | 8 | 237950344134 | 108225 | resp | L3 | L1D | 1 | addr_fallback | 32 | 32 | 800081d75eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 11 | 61 | 60 | 237950344134 | 0 | taint_reg | L4 | PRF | 1 | addr_fallback | 32 | 32 | 800081d75eb8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 12 | 259 | 61 | 237951515628 | 1171494 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 391） | 错误退休（commit_seq=161） | 真实 L5 |

折叠说明：40 个 `consumer` 全部位于终局之后（event 260–349，tick `237951515628..237965857272`），不在 `event_id=259` 的祖先上，故 Ch.4 无 consumer 行可折叠；不可折叠事件逐条保留。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（52 条）**：全部 `bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`，`shared_addr=800081d75000`、`shared_size=1000`。最早 `event_id=4294967296`，parent=8，`source_event_id=8`、`dest_event_id=9`，把请求 `32` 分叉成 `34`；随后还有从 8 分叉出的 `35/37…`。它们都在同一个错误页上广播，不在 event 259 的祖先上，也不重新汇入主链；影响是扩大错误页的消费面，不改变终局。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、1 条 `resp`、1 条 `taint_reg`；其余 65 条 `cache_access`、65 条 `cache_return`、26 条 `mshr_alloc`、39 条 `mshr_merge`、50 条 `resp`、50 条 `taint_reg`、3 条 `lq_complete` 都在主链外，是同一错误页的重复消费者与广播分支。没有一条回到 event 259 的直接祖先，故不改变 L5 结论。

**consumer（40 条）**：event 260–349，tick `237951515628..237965857272`，全部在终局之后，只作为后果列出。

**生命周期**：`chain_end`（350）是唯一一条，parent=349，tick `238882691853`，`corr=none`、`contained=1`、`outcome=errant_commit_seen`；它是退出回调，不是 L5、不是含住。本 seed 没有 `squash_masked`、没有第二支注入、没有其它 `errant_commit`。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`259`，tick=`237951515628`，parent=`61`，`detection_layer=L5`，`outcome=errant_commit` |
| run outcome | `Crash`（`CHAOS_DETECT reason=errant_commit`；`KERNEL OOPS under fault`） |
| admitted | `True`（`path=full_chain`，`violations=[]`） |
| certified | `True` |
| violations | `[]` |
| truncated | `False`；gzip EOF 正常 |
| stats 有效性 | 有效（`simInsts=382360`，`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK`（cell + consumer_summary 两层均 ok） |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker 复算 `full/L5`，路径 `['0','1','2','3','61','259']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T02-F0-W4` = true |
| 判定 | **PASS** |

传播终局与运行结局分开陈述：L5 证明错误到达提交点，Crash 是系统层结果；两者同向。`chain_end` 不参与层级判定。本 seed 无 Timeout。

## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2/prop_evt.txt.gz` | `32f66098c484fac18b93665c2ecd58384369a69f748f5756f441d85b2cedcfd6` | 14679 | 1792917149 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2/chain_report.json` | `073ec6dfc2fcc16eddc9d3ca9f1bb3158756fa0c2e33e6195faa8cec8e04fb36` | 9832 | 1792917150 |
| 权威 regrade | `N/A` —— 无 regrade 文件，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2/run.out` | `d91d34058b355d731df75688f98ffffde3b3083b5836d124e7c3315593ec955a` | 2158 | 1792917150 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2/run.err` | `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f` | 1833 | 1792917150 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2/stats.txt` | `0a9943e163783f88a1b030ad7eae1bcac6b2113a13b070d9c76d1d1ad80b8184` | 382875 | 1792917149 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json` | `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef` | 1773 | 1792917170 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` | — | — |
| 源码 head | `bc82f29d8f69410461d18c07a1ee9314f18885a5`（run-time worktree HEAD） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed2`。

**其它副本与分类**：`runs/lsu/r6_c9_T02-F0-W4_s2/T02-F0-W4/seed2` 为 **EXACT_DUPLICATE**（prop_evt 字节相同、report 语义相同、run.out 去元数据相同）；`runs/lsu/r6_p1_T02-F0-W4/T02-F0-W4/seed2`、`runs/lsu/r6_w1_T02-F0-W4/T02-F0-W4/seed2` 为 **INTERRUPTED**（无 `.done`/`.exit_code`）。本文件只使用上表权威目录。
