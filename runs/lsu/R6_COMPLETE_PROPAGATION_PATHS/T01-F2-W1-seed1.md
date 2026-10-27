# T01-F2-W1 seed1 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `bce3150a…a97e`）重建；其余文件只读引用。本 seed 含 **5 个 fault_id**，代表故障按 escape-first 规则选为 fault 1；其余 fault 只作为旁支在 Ch.5 出现，不并入主链。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T01-F2-W1`（模型 ID `T01`，单元 `L1d-TLB`） |
| seed / sample_run_id | `1` / `s1` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**单比特** `bit_flip`（`--tlb_fault_type bit_flip`，1 bit） |
| 故障类型 | 单比特翻转 |
| 频率 tier | 请求 `F2` / 生效 `F2` / `lookup_tier_enabled=1` |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）`（矩阵 Excel 行 45） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`（实际为 TLB-AliasPerm 探针，与矩阵标签不一致；见第 6 节） |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 1 --chaos_propagation --prop_run_id T01-F2-W1 --prop_sample_run_id s1` |
| source head | `N/A`（n8 batch manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/manifest.json`（SHA-256 `a9adbed51c71a59a29834b7ce4a3f9c24da01581b70652a5b3e4b9bc95260804`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n8 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=1786674 > 0`，`simTicks=1440958458474`，等于 `chain_end.tick(1678908255489) − checkpoint(237949797015)` |
| 原始事件数 | 6121（`chain_report.event_count=6121`；`fault_event_count=2323`，fault 1 的事件数） |
| fault_id 数量 | 5（fault 1 为 `full` 代表故障；fault 2/4 为 L5 检测层的 squash 含住；fault 3/5 仅 `provable_to_L4`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `238085259417`，一条 **load**（`dyn_inst_seq=415526`、`request_id=415526`）访问 `0xffffff8001362708`，命中 DTLB 第 `13` 号表项（`entry_index=13`、`walk_id=0`、`way=-1`）。注入前：`vpn=ffffff8001362; asid=206; valid=1; global=1; pfn=81362; ap=0; mtype=2; page_size=1000; pa=81362708`。4 KiB 页、偏移 `0x708`，正常 PA `0x81362708`。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `238085259417`，`VA=0xffffff8001362708`，`dyn_inst_seq=415526`）。`field=bit_flip`，`before=0x81362`，`after=0x85362`。注入日志 `Mask: 0x4000` 与异或一致：**只翻转 PFN 的第 14 位**。第 14 位在 48 位 PFN 内，有效 PFN 变为 `0x85362`，偏移 `0x708` 不变，有效 PA 从 `0x81362708` 变成 `0x85362708`，`effective_pa_changed=1`。低位翻转、错误页与原页相邻。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0）记录 `pfn 81362 → 85362`、`pa 81362708 → 85362708`，属性未动。`event_id=2`（`tlb_pfn`，parent=1）确认字段替换。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81362708`、`after=85362708`、`contained=0`、`outcome=NoFault`。无检测、无拦截。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是 **load**：`event_id=4`（`lq_read`，parent=3）记录 `lq_idx=44911`、`dyn_inst_seq=415526`、`request_id=415526`（本 seed 无 `lsq_push`，入队由 `lq_read`/`lq_complete` 共享 `lq_idx=44911` 确认）。输入是错误 PA，内部变化是把 load 绑定到 LQ 第 44911 槽并读取，输出是等待响应的 load。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=5`（`cache_access`，`pa=85362708`，`miss`）→ `event_id=6`（`cache_return`，`miss`）→ `event_id=7`（`mshr_alloc`，`mshr_id=1`，`cache_line=85362708`）。`event_id=8`（`cache_access`，parent=7，Δtick=333）访问同行 `pa=85362700`，`event_id=9` 仍 `miss`，`event_id=10` 分配 `mshr_id=2`（`cache_line=85362700`）。随后完整填充：`event_id=14`（`mshr_fill`，parent=10，Δtick=58941）把 mshr 2 标为 `filled`（`fill_id=1`），`event_id=15`（`cache_fill`）以 `pa=85362700` 填行，`event_id=16`（`mshr_free`）释放 mshr 2；`event_id=17`（`mshr_fill`，Δtick=666）把 `mshr_id=0` 标为 `filled`（`fill_id=2`），`event_id=18`（`cache_fill`）再填同一行，`event_id=19`（`mshr_free`）释放。两次 fill 都针对错误行；cache/MSHR 全程“正常”，因此无法发现地址错误；整条链仍是同一故障（页基址 `85362`）。

### 2.6 污染如何返回处理器状态

`event_id=20`（`resp`，parent=19，tick `238085319690`，Δtick=333）把数据送回，`va=85362708`；`event_id=21`（`lq_complete`，parent=20，`lq_idx=44911`）完成 load；`event_id=22`（`taint_reg`，parent=21）记录 `before=clean`、`after=tainted`、`arch_reg=4`、`phys_reg=42`、`va=85362708`。`taint_reg` 是存储→CPU 边界：此后物理寄存器 42（体系结构 x4）被标脏，后续消费该寄存器的指令都会携带污染。

### 2.7 最终传播终局

真实 L5 是 `event_id=26`（`errant_commit`），parent=`22`，tick `238085320689`（相对 `taint_reg` Δtick=999），`dyn_inst_seq=415526`，`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b27ac`，`commit_seq=293614`。未能在提交前消除：TLB 无校验、cache 正常 fill、LQ/ROB 无地址一致性检查、提交前无 squash。`chain_end`（`event_id=5483`，parent=2016，tick `1678908255489`，`corr=none`，`outcome=errant_commit_seen`，`containment_reason=squash_replay`）只是生命周期收口，不是 L5；另有 5484–5487 是其它 fault 的收口。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=293614` 退休（`dyn_inst_seq=415526`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `238085320689` 有 `CHAOS_DETECT: layer=None contained=0 tick=238085320689 ptag=1 reason=errant_commit`；此后同一 RunID 还记录了大量 `ptag=1/2/4` 的 `contained=1 reason=squash_replay`，最终在 tick `1678908255489` 记录 `contained=1 reason=store_discarded_not_retired` 并以 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)` 结束；`run.err` 为 `Kernel oops in guest`。注入 tick `238085259417` → 代表故障终局 `238085320689`，传播时延 `61272` ticks。错误 PA 指向相邻物理页，污染提交后 guest 内核 oops，仿真以 Crash 退出；不是 Timeout（simTicks 与最终 `chain_end` 一致）。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffff8001362708`、命中第 13 项 | PPN `0x81362 → 0x85362`（bit14） | PA `0x81362708 → 0x85362708` | 错误翻译进入流水线 |
| LQ | `lq_idx=44911`、load、错误 PA | 绑定槽位并读取 | 等待响应的 load | 错误地址进入 LQ |
| L1D | `…2708`/`…2700` | 两次 miss，两次 fill | 行填充 | 按错误地址真实取数 |
| MSHR | 行 `85362708`/`85362700` | alloc 1/2 → fill/fill → free | `resp`（20） | 缺失管理正常，无地址合法性检查 |
| PRF/寄存器 | 响应数据 | `clean → tainted`（arch 4 / phys 42） | 污染寄存器 | 存储→CPU 边界 |
| ROB/提交 | 污染寄存器（dyn 415526） | 退休 | `errant_commit`（commit_seq=293614） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end`（5483 等） | 生命周期收口 | 非 L5 |

一句话总结：一次 load 命中被单比特改坏的 TLB 表项（bit14），错误 PA `0x85362708` 进入 LQ 第 44911 槽，L1D 两次 miss 后由 MSHR 1/2 完成 fill/free，响应把物理寄存器 42（体系结构 x4）标脏，最终注入指令本体在 `commit_seq=293614` 错误提交，guest 内核 oops，仿真以 Crash 结束；同一 seed 另有 4 个 fault 的旁支（见 Ch.5），但本链只由 fault 1 构成。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：`prop_evt` 有 5 条 `inj`（fault 1–5），`armtlb_injections.log` 有 5 条 `arm_tlb_lookup_hit`，`stats.numFaultsInjected=5`，`run.out injected=5`；`attempted=560166`、`eligible=560166`、`activated=W3-L0-layer`。代表故障（fault 1）的坏值被实际读取（`tlb_pfn.after`、`cache_access.pa`）。激活成立。

### 3.2 故障传播类型

代表故障是**地址型**（错误物理页）。不是数据型、permission、control-state、timing、wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `238085259417`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`；此后 LQ/L1D/MSHR 只是执行，无法不重放地撤销。

### 3.4 检测与掩蔽机制

TLB 无校验；翻译层无合法性检查；L1D/MSHR 只做命中/缺失；LQ/ROB 无地址一致性检查；提交点不校验。事后 oracle 在 `238085320689` 报 `errant_commit`。同一 seed 中确实出现了大量 `squash_masked`（87 条）——它们证明后续同页 load 会被 squash，但代表故障的注入指令本体已经提交，squash 无法撤销。盲区：**48 位 PFN 内的位翻转在提交前不可见**。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 26），体系结构可见；运行结局 Crash（内核 oops），故不是 SDC。SDC 需要“对外可见且未被检测到”的错误输出；本样本以 Crash 暴露。无应用级输出 oracle，不能判断数据层面最终正确性；结论限定为“已证真实错误提交 + Crash/DUE”。

### 3.6 与同 RunID 其他 seed 的关系

seed2 注入 `238083182163`（VA `…3960`，掩码 `0x1`，bit0；L4 含住），seed3 注入 `238095582084`（VA `…3950`，掩码 `0x4000`，bit14；`full`）。三个 seed 都是单比特；本 seed 与 seed3 的位号相同（bit14）、但落在不同 PFN（`0x81362` vs `0x81d75`）、不同 tick/VA。本 seed 的独特处是 5 个 fault：fault 2/4 各自在 L5 检测层以 squash 收口，fault 3/5 只到 L4；代表故障仍按 escape-first 选为 fault 1（`full`）。本 seed 的 fault 1 数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=26` 经 `parent_event_id` 回溯的单祖先，共 21 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | — | inj | L0 | TLB | 1 | origin | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 85362 | 81362 | 85362 | 0x4000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 238085259417 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | 81362 | 85362 | 81362 | 85362 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708 | — | — | — | — | 命中查询 | PFN 81362→85362 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 238085259417 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | 81362 | 85362 | 81362 | 85362 | — | 81362708 | 85362708 | — | — | — | — | 表项当前状态 | PA 81362708→85362708 | 表项存储被改写 |
| 4 | 3 | 2 | 238085259417 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | — | — | 81362708 | 85362708 | — | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708 | vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=85362;ap=0;mtype=2;page_size=1000;pa=85362708 | 0 | — | NoFault | — | 表项 PFN | PA 81362708→85362708 | 首个不可逆点 |
| 5 | 4 | 3 | 238085259417 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误翻译 | load 读取（lq_idx=44911） | 错误地址进入 LQ |
| 6 | 5 | 4 | 238085259417 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffff8001362708 | 访问 L1D | 按错误 PA 取数 |
| 7 | 6 | 5 | 238085259417 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 85362708 | miss | cache 无法判别地址合法性 |
| 8 | 7 | 6 | 238085259417 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362708 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 85362708 | 分配 MSHR 1 | 错误行进入填充流水 |
| 9 | 8 | 7 | 238085259750 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | ffffff8001362708 | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffff8001362708 | 访问 L1D | 按错误 PA 取数 |
| 10 | 9 | 8 | 238085259750 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 85362700 | miss | cache 无法判别地址合法性 |
| 11 | 10 | 9 | 238085259750 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 85362700 | 分配 MSHR 2 | 错误行进入填充流水 |
| 12 | 14 | 10 | 238085318691 | 58941 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 2 填充（fill_id=1） | 错误行取回 |
| 13 | 15 | 14 | 238085318691 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 85362700 | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 14 | 16 | 15 | 238085318691 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 缺失处理结束 |
| 15 | 17 | 16 | 238085319357 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 0 填充（fill_id=2） | 错误行取回 |
| 16 | 18 | 17 | 238085319357 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 415526 | 415526 | — | 85362700 | 85362700 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 17 | 19 | 18 | 238085319357 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 415526 | 415526 | — | — | 85362700 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 0 | 缺失处理结束 |
| 18 | 20 | 19 | 238085319690 | 333 | resp | L3 | L1D | 1 | seq_primary | 415526 | 415526 | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 19 | 21 | 20 | 238085319690 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 415526 | 415526 | ffffff8001362708 | 85362708 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应 | load 完成（lq_idx=44911） | 错误 load 完成 |
| 20 | 22 | 21 | 238085319690 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 415526 | 415526 | 85362708 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏（arch=4/phys=42） | 存储→CPU 边界 |
| 21 | 26 | 22 | 238085320689 | 999 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 415526 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 415526） | 错误退休（commit_seq=293614） | 真实 L5 |

折叠说明：1950 个 `consumer`（event 27–5438，tick `238085320689..238803035589`）全在终局之后/其它 fault 的分支上，没有一条在 event 26 的祖先上；故 Ch.4 无 consumer 行可折叠。87 条 `squash_masked` 也全部在主链之外（见 Ch.5）。

## 5. 相关旁支与未进入最终主链的事件

**fault 2–5（4 支独立注入）**：它们各自有完整的 `inj → tlb_lookup → tlb_pfn → …` 子链，但都不是 event 26 的祖先。

| fault | inj event | tick | VA | old→new pfn | mask | 该 fault 自身终局 |
|---|---|---|---|---|---|---|
| 2 | 2026 | 238527554013 | ffffffc0089a434d | `404 → 4` | `0x400`（bit10） | `detected_contained`/L5（squash 2141 等，tick 238544444773 起） |
| 3 | 2208 | 238692834567 | ffffffc008c07758 | `80c07 → 80c06` | `0x1`（bit0） | `provable_to_L4_then_unknown`（无 squash/replay 见证） |
| 4 | 4109 | 238783071573 | ffffffc008c79824 | `80c79 → 80c7d` | `0x4`（bit2） | `detected_contained`/L5（squash 4210 起） |
| 5 | 5441 | 1678896244179 | ffffffc008c730e0 | `80c73 → 80c33` | `0x40`（bit6） | `provable_to_L4_then_unknown`；`chain_end 5487` 记录 `store_discarded_not_retired` |

这些 fault 说明本 seed 是一次多注入运行：同一进程里被改了 5 个不同的 TLB 表项。`cell_results.json` 因此把 5 个 activated fault 都计为 Crash 行（`classes.Crash=5`）。代表故障的选择遵循 escape-first：fault 1 是唯一的 `full`，所以它压过 fault 2/4 的 squash 含住和 fault 3/5 的 L4 可证。

**request_fork（633 条）**：全部 `L3/addr_fallback_broadcast`，`shared_addr` 共 5 个不同页基址（对应 5 个被改页），`shared_size=1000`。最早 `event_id=4294967296`，parent=10，`source_event_id=10`、`dest_event_id=11`，把请求 `415526` 分叉成 `415576`；另有从 22 分叉出的 `415689/415692` 等。其中 296 条的直接 source 在 fault 1 祖先上；其余挂在其它 fault 的分支上。它们都不重新汇入 event 26 的主链。

**squash_masked（87 条）**：分布在本 seed 的多个错误页上；fault 1 页上例如 258（tick `238085615727`）、279、577、598、721、857、1595、1691、1941、2016；fault 2 页上例如 2141–2145、2198–2200；fault 4 页上例如 4210、4331…5426。它们都是终局之后的 squash/replay，不改变 event 26 的 L5 终局；其中 fault 2/4 的 squash 是它们各自 fault 的权威含住见证，但不能被写成代表故障的终局。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、2 条 `mshr_fill`、2 条 `cache_fill`、2 条 `mshr_free`、1 条 `resp`、1 条 `taint_reg`；主链外还有 680 条 `cache_access`、680 条 `cache_return`、48 条 `mshr_alloc`、28 条 `mshr_merge`、73 条 `mshr_fill`、73 条 `cache_fill`、73 条 `mshr_free`、530 条 `resp`、499 条 `lq_complete`、535 条 `taint_reg`，以及预取/逐出事件；均属其它 fault 分支或同一错误页的重复消费者，没有回到 event 26 的直接祖先。

**consumer（1950 条）**：event 27–5438，全部在终局/旁支之后，只作为后果列出。**生命周期**：`chain_end` 5483（fault 1）以及 5484/5486/5487（fault 2/4/5）都是退出回调；5485 是 `run_end`。它们都不是 L5。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`26`，tick=`238085320689`，parent=`22` |
| run outcome | `Crash`（`KERNEL OOPS under fault`） |
| admitted / certified | `True` / `True`；`violations=[]` |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=1786674`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','4','22','26']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T01-F2-W1` = true |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**必须记录的不一致**：矩阵 Excel 行 45 的负载标签是 `MiBench-TC23 论文负载（…）`，且 `记录状态=blocked(fs-infra: SE has no MiBench FS pipeline)`；但本 seed 的 `run.out` 实际使用 `--readfile …/configs/fs/tlb_probe.rcS`。本文件按事实并列二者，不把矩阵标签当作实际负载；不影响 chain evidence PASS；但 overall_experiment_status 是 NOT_MIBENCH_RESULT，但属于需要上游澄清的元数据不一致。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1/prop_evt.txt.gz` | `bce3150a0d452c422248d6698c3f41ceb21fcaf3d87011f0ab741428a39aa97e` | 279114 | 1793078012 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1/chain_report.json` | `7941fb2fff9611292565452266b1b6fb14bd696dd288bf4da02fcc7c7e22953c` | 1375558 | 1793078013 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1/run.out` | `9a93a73c73af17424cbd6f6b85d169ad6553c6ae7e89a47672457629c2899b9d` | 10566 | 1793078012 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1/run.err` | `672b40ab5f50c462f0243e22e65c05c2d3938b0d990d0753e0b60674d2a14f27` | 1900 | 1793078012 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1/stats.txt` | `276af53d391adfe6cd9f3f2977e061eaf299c14f39c3575031614fd004993b1d` | 400639 | 1793078012 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/manifest.json` | `a9adbed51c71a59a29834b7ce4a3f9c24da01581b70652a5b3e4b9bc95260804` | 1438 | 1793078014 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| 源码 head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s1/T01-F2-W1/seed1`。

**其它副本与分类**：`runs/lsu/r6_n8_T01-F2-W1_s1.sha8a229009/T01-F2-W1/seed1` 为 **OLD_BINARY_REFERENCE**（manifest binary `8a229009…` ≠ 权威 `20fda699…`，prop_evt SHA 不同）。本文件只使用上表权威目录。
