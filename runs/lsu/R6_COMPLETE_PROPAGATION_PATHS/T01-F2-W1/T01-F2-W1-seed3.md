# T01-F2-W1 seed3 故障传播与最终结局

> 本文件只依据本 seed 自己的 `prop_evt.txt.gz`（SHA-256 `6a65d25d…119d`）重建；其余文件只读引用。本 seed 有 3 个 fault_id，代表故障为 fault 1。

## 1. 实验身份与复现信息

| 项目 | 值 |
|---|---|
| RunID | `T01-F2-W1`（模型 ID `T01`，单元 `L1d-TLB`） |
| seed / sample_run_id | `3` / `s3` |
| 故障模型 | `CHAOSArmTLB` 在 `arm_tlb_lookup_hit` 对命中表项 PPN 做**单比特** `bit_flip`（`--tlb_fault_type bit_flip`，1 bit） |
| 故障类型 | 单比特翻转 |
| 频率 tier | 请求 `F2` / 生效 `F2` / `lookup_tier_enabled=1` |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）`（矩阵 Excel 行 45） |
| run.out 实际 workload/readfile | `--readfile …/configs/fs/tlb_probe.rcS`（实际为 TLB-AliasPerm 探针，与矩阵标签不一致；见第 6 节） |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T01-F2-W1 --prop_sample_run_id s3` |
| source head | `N/A`（n8 batch manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| 二进制路径 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（审计工具提交；运行期 manifest 值见本行下方/第7章） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` |
| 证据根 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/manifest.json`（SHA-256 `1a53ac5d8d7121c52b506802a30d956043a27c4c344fff5b52a22cdf2f175927`） |
| 正常 EOF | 是（gzip 完整；`truncated=False`、`stream_present=True`） |
| exit_code | `0`（`chain_report.exit_code`；n8 manifest `exit_code=null`，status=`FINISHED`） |
| truncated | `False` |
| stats 是否有效 | 是：`simInsts=1157339 > 0`，`simTicks=1733943313341`，等于 `chain_end.tick(1971893110356) − checkpoint(237949797015)` |
| 原始事件数 | 12752（`chain_report.event_count=12752`；`fault_event_count=9857`，fault 1 的事件数） |
| fault_id 数量 | 3（fault 1 `full`；fault 2 L5 检测层 squash 含住；fault 3 仅 `provable_to_L4`） |
| 是否经过离线 regrade | 否（plain `chain_report.json`） |

## 2. 完整故障传播过程：从注入到最终结局

### 2.1 故障注入前的正常状态

tick `238095582084`，一条**存储**指令（`dyn_inst_seq=520906`、`request_id=520906`）访问 `0xffffffc009483950`，命中 DTLB 第 `21` 号表项（`entry_index=21`、`walk_id=0`、`way=-1`）。注入前：`vpn=ffffffc009483; asid=206; valid=1; global=1; pfn=81d75; ap=0; mtype=2; page_size=1000; pa=81d75950`。4 KiB 页、偏移 `0x950`，正常 PA `0x81d75950`。

### 2.2 故障具体如何注入

`event_id=0`（`inj`，fault_id=1，tick `238095582084`，`VA=0xffffffc009483950`，`dyn_inst_seq=520906`）。`field=bit_flip`，`before=0x81d75`，`after=0x85d75`。注入日志 `Mask: 0x4000` 与异或一致：**只翻转 PFN 的第 14 位**。有效 PFN 变为 `0x85d75`，偏移不变，有效 PA 从 `0x81d75950` 变成 `0x85d75950`，`effective_pa_changed=1`。错误页与原页相邻（相差 4 个 4 KiB 页）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0）记录 `pfn 81d75 → 85d75`、`pa 81d75950 → 85d75950`。`event_id=2`（`tlb_pfn`，parent=1）确认字段替换。`event_id=3`（`tlb_translate_result`，parent=2）把错误 PA 交给 LSU：`before=81d75950`、`after=85d75950`、`contained=0`、`outcome=NoFault`。无检测、无拦截。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是**存储**：`event_id=4`（`sq_execute`，parent=3）记录 `issued`、`sq_idx=54806`；本 seed 主链上没有 `lsq_push`（流中该 kind 计数为 0），入队由 `sq_idx=54806` 在 `sq_execute`/`sq_writeback`/`sq_complete` 中重复出现来确认。`event_id=11`（`sq_writeback`，parent=4，Δtick=3330）把 `pa=85d75950` 装进写回包（`packet_built`）。输入是错误 PA，内部变化是同槽位发射→构包，输出是待访问 L1D 的错误地址。

### 2.5 错误如何经过 cache 和 MSHR

`event_id=12`（`cache_access`，`pa=85d75950`，`miss`）→ `event_id=13`（`cache_return`，`miss`）→ `event_id=14`（`mshr_alloc`，`mshr_id=3`，`cache_line=85d75950`）。`event_id=15`（`cache_access`，parent=14，Δtick=333）访问同行 `pa=85d75940`，`event_id=16` 仍 `miss`，`event_id=17` 分配 `mshr_id=4`（`cache_line=85d75940`）。随后完整填充：`event_id=60`（`mshr_fill`，parent=17，Δtick=59274）把 mshr 4 标为 `filled`（`fill_id=3`），`event_id=61`（`cache_fill`）以 `pa=85d75940` 填行，`event_id=62`（`mshr_free`）释放 mshr 4；`event_id=69`（`mshr_fill`，Δtick=999）把 `mshr_id=0` 标为 `filled`（`fill_id=4`），`event_id=70`（`cache_fill`）再填同一行，`event_id=71`（`mshr_free`）释放。两次 fill 都针对错误行；cache/MSHR 行为完全正常，无法判别地址；整条链仍是同一故障。

### 2.6 污染如何返回处理器状态

`event_id=80`（`resp`，parent=71，tick `238095646353`，Δtick=333）把数据送回，`va=85d75950`；`event_id=81`（`taint_reg`，parent=80）记录 `before=clean`、`after=tainted`（寄存器号未记录）；`event_id=82`（`sq_complete`，parent=81）把 `sq_idx=54806` 的存储标记为 `completed`。`taint_reg` 是存储→CPU 边界。

### 2.7 最终传播终局

真实 L5 是 `event_id=97`（`errant_commit`），parent=`82`，tick `238095648018`（相对 `taint_reg` Δtick=1665），`dyn_inst_seq=520923`（注入指令 520906 的后继），`corr=taint_prop`，`contained=0`，`detection_layer=L5`，`outcome=errant_commit`，`pc=ffffffc0087b27c4`，`commit_seq=394130`。未能在提交前消除：TLB 无校验、cache 正常 fill、SQ/ROB 无地址一致性检查、提交前无 squash。`chain_end`（`event_id=10930`，parent=8347，tick `1971893110356`，`corr=none`，`outcome=errant_commit_seen`）只是生命周期收口。

它之所以**体系结构可见**，是因为该指令已在 `commit_seq=394130` 退休（`dyn_inst_seq=520923`），退休后的寄存器/存储状态就是体系结构状态；此后任何 squash/flush 都无法撤销这次提交，所以 L5 成立，而 `chain_end` 只是生命周期收口。

### 2.8 从传播终局到系统表现

传播终局 `L5`、`terminal=full`；运行结局 `Crash`。`run.out` 在 `238095648018` 有 `CHAOS_DETECT: layer=None contained=0 tick=238095648018 ptag=1 reason=errant_commit`，其后记录了大量 `contained=1 reason=squash_replay`（含 fault 2 页），最终以 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)` 结束；`run.err` 为 `Kernel oops in guest`。注入 tick `238095582084` → 终局 `238095648018`，传播时延 `65934` ticks。错误 PA 指向相邻物理页，污染提交后 guest 内核 oops，仿真以 Crash 退出；不是 Timeout。

### 2.9 主线单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| TLB | VA `0xffffffc009483950`、命中第 21 项 | PPN `0x81d75 → 0x85d75`（bit14） | PA `0x81d75950 → 0x85d75950` | 错误翻译进入流水线 |
| SQ | `sq_idx=54806`、store、错误 PA | 发射→构包 | `packet_built`（`pa=85d75950`） | 错误地址固化 |
| L1D | `…5950`/`…5940` | 两次 miss，两次 fill | 行填充 | 按错误地址真实取数 |
| MSHR | 行 `85d75950`/`85d75940` | alloc 3/4 → fill/fill → free | `resp`（80） | 缺失管理正常 |
| PRF/寄存器 | 响应数据 | `clean → tainted` | 污染寄存器 | 存储→CPU 边界 |
| ROB/提交 | 污染寄存器（dyn 520923） | 退休 | `errant_commit`（commit_seq=394130） | 真实 L5 |
| PropMonitor | 退出回调 | `chain_end`（10930–10932） | 生命周期收口 | 非 L5 |

一句话总结：store 命中被单比特改坏的 TLB 表项（bit14），错误 PA `0x85d75950` 经 `sq_idx=54806` 构包后进 L1D，两次 miss 后由 MSHR 3/4 完成 fill/free，响应把寄存器标脏，最终后继指令（dyn 520923）在 `commit_seq=394130` 错误退休，guest 内核 oops，仿真以 Crash 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：3 条 `inj`、3 条 `arm_tlb_lookup_hit`（fault 1：old `0x81d75`、new `0x85d75`、`Mask: 0x4000`；fault 2：old `0x85d75`、new `0x95d75`、`Mask: 0x10000`；fault 3：old `0x80c73`、new `0x80c53`、`Mask: 0x20`）、`stats.numFaultsInjected=3`、`run.out injected=3`；`attempted=416527`、`eligible=416527`、`activated=W3-L0-layer`。代表故障（fault 1）的坏值被实际读取。激活成立。

### 3.2 故障传播类型

**地址型**（错误物理页）。不是数据型、permission、control-state、timing、wrong cache line。

### 3.3 首个不可逆传播点

`event_id=3`（`tlb_translate_result`，tick `238095582084`）：错误 PA 作为有效翻译交付，`contained=0`、`outcome=NoFault`；此后只是执行。

### 3.4 检测与掩蔽机制

TLB 无校验；翻译层无合法性检查；L1D/MSHR 只做命中/缺失；SQ/ROB 无一致性检查；提交点不校验。事后 oracle 在 `238095648018` 报 `errant_commit`。同一 seed 中 fault 2 在 L5 检测层以 squash 收口（9237），fault 3 只到 L4；这些含住发生在各自的分支上，不能撤销 fault 1 已提交的错误。

### 3.5 最终 SDC 风险判断

有真实错误提交（event 97），体系结构可见；运行结局 Crash（内核 oops），故不是 SDC。SDC 需要“对外可见且未被检测到”的错误输出；本样本以 Crash 暴露。无应用级输出 oracle，不能判断数据层面最终正确性；结论限定为“已证真实错误提交 + Crash/DUE”。

### 3.6 与同 RunID 其他 seed 的关系

seed1 注入 `238085259417`（VA `…2708`，掩码 `0x4000`，bit14；`full`），seed2 `238083182163`（VA `…3960`，掩码 `0x1`，bit0；L4 含住）。三个 seed 都是单比特；本 seed 与 seed1 的位号相同（bit14），但 PFN 不同（`0x81d75` vs `0x81362`）、tick/VA 不同，且本 seed 有 3 个 fault（seed1 有 5 个）。本 seed 的 fault 2（`95d75`）与 fault 3（`80c53`）都不在代表故障的链上。本 seed 的数值未与其它 seed 混用。

## 4. 完整主链事件表

主链 = 终局见证 `event_id=97` 经 `parent_event_id` 回溯的单祖先，共 22 个事件，按 root→witness 排列。`Δtick` 相对上一行；`layer` 列按 checker 的 `_layer_of`（TLB 族映射）记账。`before`/`after` 是事件自身的字段原文（对 `tlb_pfn`/`inj`/`tlb_lookup` 即 PFN 值），`state_before`/`state_after` 是同一事件的状态串（对 `tlb_pfn` 即 PA 值）。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238095582084 | — | inj | L0 | TLB | 1 | origin | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | 0x4000 | — | — | — | — | — | — | 命中项 VA/PPN | 被改写的 PPN | 错误源 |
| 2 | 1 | 0 | 238095582084 | 0 | tlb_lookup | L1 | TLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | — | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75950 | — | — | — | — | 命中查询 | PFN 81d75→85d75 | 坏值进入翻译路径 |
| 3 | 2 | 1 | 238095582084 | 0 | tlb_pfn | L2 | TLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 85d75950 | — | — | 81d75 | 85d75 | 81d75 | 85d75 | — | 81d75950 | 85d75950 | — | — | — | — | 表项当前状态 | PA 81d75950→85d75950 | 表项存储被改写 |
| 4 | 3 | 2 | 238095582084 | 0 | tlb_translate_result | L2 | TLB | 1 | seq_primary | 520906 | 520906 | ffffffc009483950 | 85d75950 | — | — | — | — | 81d75950 | 85d75950 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75950 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=85d75;ap=0;mtype=2;page_size=1000;pa=85d75950 | 0 | — | NoFault | — | 表项 PFN | PA 81d75950→85d75950 | 首个不可逆点 |
| 5 | 4 | 3 | 238095582084 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | 错误 PA 的 store | 发射（sq_idx=54806） | 进入 SQ |
| 6 | 11 | 4 | 238095585414 | 3330 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 520906 | — | 85d75950 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | sq_idx=54806 | 构包 | 错误地址固化为写回包 |
| 7 | 12 | 11 | 238095585414 | 0 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 85d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483950 | 访问 L1D | 按错误 PA 取数 |
| 8 | 13 | 12 | 238095585414 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 85d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 85d75950 | miss | cache 无法判别地址合法性 |
| 9 | 14 | 13 | 238095585414 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75950 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 85d75950 | 分配 MSHR 3 | 错误行进入填充流水 |
| 10 | 15 | 14 | 238095585747 | 333 | cache_access | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | ffffffc009483950 | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | ffffffc009483950 | 访问 L1D | 按错误 PA 取数 |
| 11 | 16 | 15 | 238095585747 | 0 | cache_return | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | — | 行 85d75940 | miss | cache 无法判别地址合法性 |
| 12 | 17 | 16 | 238095585747 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 4 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 行 85d75940 | 分配 MSHR 4 | 错误行进入填充流水 |
| 13 | 60 | 17 | 238095645021 | 59274 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 4 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 4 填充（fill_id=3） | 错误行取回 |
| 14 | 61 | 60 | 238095645021 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 85d75940 | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 15 | 62 | 61 | 238095645021 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 4 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 4 | 缺失处理结束 |
| 16 | 69 | 62 | 238095646020 | 999 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 上游数据 | MSHR 0 填充（fill_id=4） | 错误行取回 |
| 17 | 70 | 69 | 238095646020 | 0 | cache_fill | L3 | L1D | 1 | addr_fallback | 520906 | 520906 | — | 85d75940 | 85d75940 | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 数据 | 填行 | 错误行进入 cache |
| 18 | 71 | 70 | 238095646020 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 520906 | 520906 | — | — | 85d75940 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 0 | 缺失处理结束 |
| 19 | 80 | 71 | 238095646353 | 333 | resp | L3 | L1D | 1 | seq_primary | 520906 | 520906 | 85d75950 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 取回数据 | 数据回处理器 | 污染进入寄存器 |
| 20 | 81 | 80 | 238095646353 | 0 | taint_reg | L4 | PRF | 1 | seq_primary | 520906 | 520906 | 85d75950 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应数据 | 寄存器标脏 | 存储→CPU 边界 |
| 21 | 82 | 81 | 238095646353 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 520906 | ffffffc009483950 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | 污染响应 | 存储完成（sq_idx=54806） | 错误存储正式完成 |
| 22 | 97 | 82 | 238095648018 | 1665 | errant_commit | L5 | ROB/提交 | 1 | taint_prop | — | 520923 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染寄存器（dyn 520923） | 错误退休（commit_seq=394130） | 真实 L5 |

折叠说明：2276 个 `consumer`（event 98–10929，tick `238095648018..1971861937227`）全在终局/旁支之后，不在 event 97 的祖先上；65 条 `squash_masked` 也不在主链上，故无 consumer 行可折叠。

## 5. 相关旁支与未进入最终主链的事件

**request_fork（1819 条）**：全部 `L3/addr_fallback_broadcast`，`shared_addr` 共 3 个页基址，`shared_size=1000`。最早 `event_id=4294967296`，parent=3，`source_event_id=3`、`dest_event_id=5`，把请求 `520906` 分叉成 `520896`；另有从 17 分叉出的 `520907/520912` 等。其中 1508 条的 source 在 fault 1 祖先上；其余挂在其它 fault 的分支上。不汇入 event 97 的主链。

**fault 2**：`event_id=8348`，tick `238618556919`，VA `0xffffffc009483240`，`old_pfn=85d75`、`new_pfn=95d75`、`Mask: 0x10000`（bit16）。该 fault 的 `detected_contained`/L5 由 `event_id=9237`（`squash_masked`，tick `238619464011`，VA `…30b0`，PA `95d750b0`）等收口；它不在代表故障链上。

**fault 3**：`event_id=10880`，tick `1971861830334`，VA `0xffffffc008c730e0`，`old_pfn=80c73`、`new_pfn=80c53`、`Mask: 0x20`（bit5）；终局 `provable_to_L4_then_unknown`，`chain_end 10932` 记录 `store_discarded_not_retired`。注入 tick 距运行收口 `1971893110356` 只有 `31280022` ticks，属于运行末端注入。

**squash_masked（65 条）**：fault 1 页上例如 1661（tick `238098402927`）、1685、1702、1761、1882、1887、…、7847；fault 2 页上例如 9237、9847、9955、9958、10363、10478、10775/10778/10792。它们都是后段 squash，不改变 event 97 的 L5 终局。

**off-chain 事件**：主链含 2 条 `cache_access`、2 条 `cache_return`、2 条 `mshr_alloc`、2 条 `mshr_fill`、2 条 `cache_fill`、2 条 `mshr_free`、1 条 `resp`、1 条 `taint_reg`；主链外还有 1867 条 `cache_access`、1867 条 `cache_return`、90 条 `mshr_alloc`、163 条 `mshr_merge`、90 条 `mshr_fill`、90 条 `cache_fill`、90 条 `mshr_free`、1716 条 `resp`、583 条 `lq_complete`、2001 条 `taint_reg`、2 条 `lq_read` 等，均属其它 fault 或同页重复消费者。

**consumer（2276 条）**：event 98–10929，全在终局/旁支之后。**生命周期**：`chain_end` 10930–10932 都是退出回调；10930 的 `outcome=errant_commit_seen` 不是 L5。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| propagation terminal | `L5`（真实 `errant_commit`，非生命周期收口） |
| 传播终局事件 | `errant_commit` event_id=`97`，tick=`238095648018`，parent=`82` |
| run outcome | `Crash`（`KERNEL OOPS under fault`） |
| admitted / certified | `True` / `True`；`violations=[]` |
| truncated / gzip EOF | `False` / 正常 |
| stats 有效性 | 有效（`simInsts=1157339`；`simTicks` 与 `chain_end − checkpoint` 一致） |
| conservation | `OK` |
| count_contradiction | `False`（`cell_results.json`，RunID 汇总级） |
| campaign/checker agreement | 一致：report `full/L5`，checker `full/L5`，路径 `['0','1','2','4','81','97']` 相同 |
| CHAIN_DEMONSTRATED | YES |
| COMPLETE_3_OF_3 | `T01-F2-W1` = true |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**必须记录的不一致**：矩阵 Excel 行 45 的负载标签是 `MiBench-TC23 论文负载（…）`，且 `记录状态=blocked(fs-infra: SE has no MiBench FS pipeline)`；但本 seed 的 `run.out` 实际使用 `--readfile …/configs/fs/tlb_probe.rcS`。按事实并列，不把矩阵标签当作实际负载。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3/prop_evt.txt.gz` | `6a65d25d31f1e9f9f9965d4b24fb33ac9619654ef6417ff4544da668d358119d` | 476528 | 1793088997 |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3/chain_report.json` | `f0b6cc6a2956cc05fd1fdd9bbb3e6de9fc0fcb91577bd8e6c89ce8c04508ddab` | 1375321 | 1793089000 |
| 权威 regrade | `N/A` —— 无 regrade，plain report 即权威 | — | — | — |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3/run.out` | `ac39928d73bd8f83e09f701df0bf67e040f4ec7cb8591b52692c75eada032469` | 8564 | 1793088998 |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3/run.err` | `de8403ca5671675b258d5cc2e9d99a733336eef03c49490bb0d383150eb6e549` | 1800 | 1793088998 |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3/stats.txt` | `b67d1c225545d2044dd00cb990aacee36883ab5139264362ecb2d14a83e29755` | 394487 | 1793088998 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/manifest.json` | `1a53ac5d8d7121c52b506802a30d956043a27c4c344fff5b52a22cdf2f175927` | 1438 | 1793089001 |
| 启动命令记录 | `run.out` 的 `command line:` 行 + `manifest.json → cmd` | 同上 | — | — |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| 源码 head | `d1543872e155943893fdd6d18a489ff7c372d97d`（manifest `binary_source_head`） | — | — | — |
| 分析工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a0601732afe685be9c422159470c3b71b44` | — | — |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3/T01-F2-W1/seed3`。

**其它副本与分类**：本 seed 的 n8 运行根下未发现 `.sha8a229009` 型旧二进制副本；本文件只使用上表权威目录。
