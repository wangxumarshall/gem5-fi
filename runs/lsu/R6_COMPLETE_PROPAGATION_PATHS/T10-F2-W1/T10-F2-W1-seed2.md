# T10-F2-W1 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T10-F2-W1`；seed：`2`；sample_run_id：`s2`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`bit_flip`（故障类型：单比特翻转）。随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；VPN、ASID、权限和页大小保持不变。
- frequency tier：`F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`
- workload 矩阵标签：MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 两轴状态：chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_lsu_tier F2 --tlb_rng_seed 2 --chaos_propagation --prop_run_id T10-F2-W1 --prop_sample_run_id s2`
- source head：`N/A`（该 manifest 不记录 source_head）
- binary source head：`d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/manifest.json`（SHA-256 `af81b336c125f952c59b0cc34e185b9eb4030c342fba893d15c683561cc3b09f`；1438 bytes；mtime `2026-10-27T14:45:22+0800`；该 manifest 的 seed 字段为 `2`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`None`，runroot `.done`=存在，`.exit_code`=缺失）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；391280 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **10584** 条；`chain_report.event_count`=**9450**（不含 consumer 事件），差值为 consumer 摘要数 1134
- fault_id 数量：**4**（注入日志共 5 条记录，其中 F1/F2 档位首行是 tier 汇总行而非独立故障）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T10-F2-W1 seed2 自己的流。终局见证按权威口径取 **event 68**（`squash_masked`，L4，`contained=1`，`reason=squash_replay`），而不是 `chain_report.path_event_ids` 尾部的 event 1797；event 1797 是同一故障在另一个 VA 上更晚的 L4 含住，不能替换 event 68。event 68 的祖先为 0,1,2,3,4,32,33,34,35,36,68（11 个事件）：parent 逐级为 0←1←2←3←4←32←33←34←35←36←68。tick 单调不减；0–4、32–36 分别同 tick。

### 2.1 故障注入前的正常状态

**load**：event 4 `lq_read`（lq_idx=41835），dyn/request=`393897`，VA=`0xffffffc009483960`。命中项 `vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=81d75960`；way=-1（未记录）、entry_index=21，偏移 0x960。正常 PFN=0x81d75、正常 PA=0x81d75960。

### 2.2 故障具体如何注入

event 0：`inj`，tick=`238083182163`，`field=bit_flip`，`before=81d75`、`after=81d74`，VA=`0xffffffc009483960`，`request_id=393897`，`corr=origin`。注入日志：`old_pfn 0x81d75 → new_pfn 0x81d74, Mask: 0x1`。0x81d75 XOR 0x1 = 0x81d74，即 bit 0 从 1 变 0；偏移 0x960 不变，PA 81d75960→81d74960，effective 变化为真。VPN/ASID/权限/页大小未变；bit_flip 单 bit 翻转。

### 2.3 TLB 查询与地址翻译

event 1 `tlb_lookup` 读到 pfn 81d75→81d74（entry_index=21，way=-1）；event 2 `tlb_pfn` 记录 `state_before=81d75960`、`state_after=81d74960`、`pa=81d74960`；event 3 `tlb_translate_result` 记录 `effective_pa_changed`、`before=81d75960`、`after=81d74960`、`contained=0`、`outcome=NoFault`。TLB 没有含住：bit0 翻转后的 PPN 仍是合法编码，权限/有效位/页大小未变。TLB 交付 request_id=393897、PA=0x81d74960 的 load。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 的 LSU 阶段记录比其它 seed 更完整：event 4 `lq_read`（lq_idx=41835）之后，event 32 `lsq_push`（parent=4，pc=ffffffc0087b27c8，lq_idx=41835，sq_idx=-1，field=load）明确这是 load；event 33 `mem_req`（parent=32，request_id=393897）把错误 PA 作为内存请求发出；event 34 `lsq_sendfrag`（parent=33，field=load）发送 fragment；event 35 `tlb_translate`（parent=34）再次记录翻译；event 36 `lq_read`（parent=35）读取。输入是错误 PA=81d74960；内部变化是 LQ/LSU 的请求构造与 fragment 发送；输出是 request_id=393897 的访问；下一步本应由 cache/MSHR 处理，但这条代表链在 event 36 之后直接进入 event 68 的 squash（见 2.5/2.7）。

### 2.5 错误如何经过 cache 和 MSHR

**在 event 68 的单祖先上，没有 cache/MSHR 事件**：event 36 的 child 是 event 68，而不是 cache_access/mshr_*。因此 2.5 的 cache_access/cache_return/mshr_alloc/merge/fill/free/cache_fill/response 对这条主链只能记 **N/A**；原因不是 cache 不存在，而是该请求在进入 cache/MSHR 主链之前就被 squash。原始流里确实存在大量 cache/MSHR 事件（fault1 的 kind 计数：cache_access=1538、mshr_alloc=64 等），但它们属于其它请求/旁支，不能拼进 event 68 的祖先。这个事实很重要：它说明含住点发生在 LSU 之后、cache 主链之前（或至少 trace 没有把该请求的 cache 片段挂在 36 的祖先上）。

### 2.6 污染如何返回处理器状态

**N/A**：event 68 的祖先上没有 `resp`、`lq_complete` 或 `taint_reg`。event 68 的 `kind=squash_masked` 本身就是“load 在可提交前被 squash”，因此没有返回处理器的污染状态；`taint_reg` 不在主链上。原始流中 fault1 有 1654 条 taint_reg，但它们都在旁支（例如 event 81 的 taint_reg 属于 fork 出来的 request 393847，见第 5 章），不能把 event 81 当作 event 68 的祖先。

### 2.7 最终传播终局

这是**含住（detected_contained）**终局，不是 L5：

- 真实含住事件：event 68，`kind=squash_masked`，`parent_event_id=36`，tick=`238083244768`，`dyn_inst_seq=393912`，VA=`ffffffc0094839e0`，PA=`81d749e0`，`field=squashed_load`，`detection_layer=L4`，`contained=1`，`outcome=masked`，`corr=addr_fallback`，`containment_layer=L4`，`containment_reason=squash_replay`。它确实由 L4 的 squash/replay 机制丢弃了错误 load，因此是真实含住点；L5 对本主链是 N/A。
- 为什么不是 L5：event 68 的 `contained=1`、`outcome=masked`，且它是该请求在可提交前的 squash；`chain_end` event 9308 只是传播流收口（`outcome=errant_commit_seen` 是流级标记，不是 L5 见证），不能拿它冒充 L5，也不能把 event 68 的 L4 squash 写成 L5。
- 报告路径差异（必须说明）：plain `chain_report.json` 的 fault1 `path_event_ids` 尾部是 event 1797（tick=`238085898111`，VA=`ffffffc0094833c0`，PA=`81d743c0`，L4，contained=1，squash_replay）。它不是 event 68 的祖先；README 的权威口径明确“5 个 L4 含住 seed 的权威见证是 event 68，不是 1797”。因此本文件采用 68 作为终局见证，把 1797 放到第 5 章。
- 另一个 L5 标签记录：event 83，`kind=errant_commit`，parent=68，tick=`238083249096`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。它确实存在于原始流，但按 README/checker 的 `_errant_commit_escape` 口径属于“悬空”L5 记录，不是权威终局；它不能把 terminal 从 detected_contained 改成 full，也不能被忽略不写。本文件如实记录：raw stream 有 event 83，但权威 terminal 仍是 event 68 的 L4 含住。

### 2.8 从传播终局到系统表现

- 传播终局：L4 含住 event 68，tick=`238083244768`；`chain_report.terminal=detected_contained`，`provable_to=L5`（报告字段），但本主链没有真实 L5 见证，L5=N/A。
- 运行结局：**Crash**（oracle=Crash，exit=0）。`run.out` 的 `CHAOS_DETECT` 先记录 `layer=None contained=0 tick=238083249096 reason=errant_commit`（对应悬空 event 83），随后有大量 Hardware RAS `squash_replay`，最后 `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 为 `warn: Kernel panic in simulated kernel`。
- 注入 tick=`238083182163`，含住 tick=`238083244768`，延迟 **62605 ticks**。
- 因果链：fault1 的 load 被 L4 squash/replay 含住（68），但整个 run 仍以 kernel panic 结束（Crash）；这个 panic 不能归因于 fault1 的 L5（它没有权威 L5），也不能说 fault1 是 SDC。没有应用级 oracle；fault2–4 与 event 83/1797 见第 5 章。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB | VA=ffffffc009483960，entry=21，PFN=81d75 | bit0 翻转→81d74 | request_id=393897，PA=81d74960 | 错误 PPN 进入地址 |
| LQ/LSU | load lq_idx=41835 | lq_read→lsq_push→mem_req→lsq_sendfrag→tlb_translate→lq_read | LSU 请求 | 错误地址被 LSU 接受 |
| L1D cache/MSHR | N/A | N/A | N/A | 代表链在 event 36 后直接到 squash；cache/MSHR 事件属于旁支 |
| response / LQ complete | N/A | N/A | N/A | 没有污染数据返回处理器 |
| register file（taint） | N/A | N/A | N/A | 主链没有 taint_reg |
| squash/replay（L4） | event 36 的 load | 在可提交前 squash | contained=1，masked | 真实含住点；L5=N/A |
| commit/ROB | N/A | N/A | N/A | 没有权威 L5 提交 |


**一句话总括**：T10-F2-W1 seed2 在 tick 238083182163 把 VA=ffffffc009483960 的 PPN bit0 翻转（0x81d75→0x81d74，mask 0x1），错误 PA=81d74960 经 LQ/LSU（4、32–36）传播，在可提交前由 event 68 的 L4 squash/replay 真实含住；event 1797 是更晚的同类 L4，event 83 是悬空 L5 记录；权威终局是 detected_contained，L5=N/A，运行结局仍是 Crash（kernel panic）。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志有 tier 行加 4 条 hit；`CHAOS_LSU_TRIGGER` 为 `attempted=411962 eligible=411962 injected=4`；`stats.txt` numFaultsInjected=4；`chain_report` faults=4。四方一致。fault1 的 PPN 被 event 1/2/3 读取、event 4/32–36 消费，activated 为真；但它在提交前被 event 68 squash。fault2 到 L4 contained，fault3/4 到 L4-then-unknown。

### 3.2 故障传播类型

**地址型（PPN 单 bit 翻转→错误物理页）**：mask=0x1 翻转 bit0，错误 PA=81d74960 经 LQ/LSU 传播；不是 data/permission/control-state/timing。它最终被 L4 squash 含住，因此没有形成架构可见的错误数据。

### 3.3 首个不可逆传播点

**event 32/33（`lsq_push`/`mem_req`，tick=238083183495）**：错误 PA=81d74960 在 event 3 已离开 TLB，event 32/33 把它作为 LSU 内存请求真正发出；从这一刻起，要撤销只能靠 squash/replay。event 68 确实执行了 L4 squash/replay，所以它不是“不可撤销的架构错误”，而是“结构上必须由后续 squash 才能撤销”的点。这个区分很重要：本 seed 的终局是含住，不是 L5；不能把 event 32/33 说成 L5，也不能把 event 68 的 squash 写成 L5。

### 3.4 检测与掩蔽机制

TLB 检查全部通过；L1D/MSHR 在这条代表链上没有主链事件，因此没有 cache 层检测记录。真正的检测/掩蔽是 event 68 的 L4 `squash_masked`（contained=1，reason=squash_replay）：它在 load 可提交前丢弃错误值，形成 detected_contained。原始流另有 event 83 的 `errant_commit`（parent=68，tick=238083249096，L5 标签），按权威口径是悬空 L5，不是本终局；event 1797 是更晚的同类 L4。检测盲区：PPN bit0 翻转仍合法，TLB 权限/有效位无法发现；cache/MSHR 也没有地址 oracle，只是本请求在 cache 主链前被 squash。

### 3.5 最终 SDC 风险判断

权威终局是 **detected_contained**（event 68，L4，squash_replay），不是真实 L5；因此不能说本 seed 的 fault1 形成了架构可见错误提交，更不能说 SDC。运行结局仍是 Crash（kernel panic），但该 panic 不能归因于 fault1 的 L5（fault1 没有权威 L5）；fault2–4 的状态见第 5 章。没有应用级输出 oracle，最终数据正确性不能判断。event 83 的 L5 标签记录必须如实写出，但它不改变权威 terminal。

### 3.6 与同 RunID 其他 seed 的关系

seed2 的注入是 tick=238083182163、VA=ffffffc009483960、mask=0x1、PFN 81d75→81d74、权威终局 68（L4 含住）、Crash、4 个 fault；seed1 是 238085259417/VA=ffffff8001362708/mask 0x4000/终局 26（L5）/Crash/5 个 fault；seed3 是 238095582084/VA=ffffffc009483950/mask 0x4000/终局 97（L5）/Crash/3 个 fault。只有 seed2 是含住，不能把 seed1/3 的 L5 事件号或 taint 寄存器搬进 seed2。

## 4. 完整主链事件表

> 主链按代表故障（escape-first 选中 fault_id=1）的终局见证 `parent_event_id` 单祖先重建。seed2 的终局见证采用权威口径 event 68（真实 L4 含住），不是报告 `path_event_ids` 尾部的 1797；`path_event_ids` 只作层锚点。`—` 表示原始事件无该字段。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238083182163 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 81d74 | 81d75 | 81d74 | 0x1 | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→81d74 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 238083182163 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | 81d75 | 81d74 | 81d75 | 81d74 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960 | — | — | — | — | VA=ffffffc009483960 的命中查找，request_id=393897 | 命中表项返回 pfn=81d74 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 238083182163 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d74960 | — | — | 81d75 | 81d74 | 81d75 | 81d74 | — | 81d75960 | 81d74960 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=81d74960（pfn=81d74） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 238083182163 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | 81d74960 | — | — | — | — | 81d75960 | 81d74960 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75960 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d74;ap=0;mtype=2;page_size=1000;pa=81d74960 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=81d74960，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 238083182163 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=393897 的请求，VA=ffffffc009483960 | request_id=393897 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 32 | 4 | 238083183495 | 1332 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=393897 的请求，VA=ffffffc009483960 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 33 | 32 | 238083183495 | 0 | mem_req | L3 | LSU mem_req | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=393897 的请求，VA=ffffffc009483960 | request_id=393897 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 8 | 34 | 33 | 238083183495 | 0 | lsq_sendfrag | L3 | LSQ fragment | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=393897 的请求，VA=ffffffc009483960 | request_id=393897 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 9 | 35 | 34 | 238083183495 | 0 | tlb_translate | L2 | DTLB 翻译 | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | VA=ffffffc009483960 的再次翻译请求（request_id=393897） | TLB 翻译记录（不改变已交付的错误 PA） | 同一错误地址在 LSU 路径上的翻译记录；错误 PA 仍是 81d74960 |
| 10 | 36 | 35 | 238083183495 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 393897 | 393897 | ffffffc009483960 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=393897 的请求，VA=ffffffc009483960 | request_id=393897 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 11 | 68 | 36 | 238083244768 | 61273 | squash_masked | L4 | squash/replay | 1 | addr_fallback | — | 393912 | ffffffc0094839e0 | 81d749e0 | — | — | — | — | — | — | — | — | — | 1 | L4 | masked | squash_replay | VA=ffffffc0094839e0 的 load 在可提交前被 squash | contained=1，outcome=masked | L4 squash/replay 丢弃错误值，形成含住终点 |


## 5. 相关旁支与未进入最终主链的事件

本 seed 的权威终局是 event 68（L4 含住），而 plain `chain_report` 的 fault1 `path_event_ids` 尾部是 event 1797。这个差异必须单独说明，不能把两者混为一条主链：

- event 68：tick=238083244768，parent=36，VA=ffffffc0094839e0，PA=81d749e0，`squash_masked`，L4，contained=1，squash_replay。它是 event 36 的直接 child，是本文件采用的权威见证。
- event 1797：tick=238085898111，parent=1778，VA=ffffffc0094833c0，PA=81d743c0，`squash_masked`，L4，contained=1，squash_replay。它是同一 fault1 在另一个 VA 上更晚的含住，不是 event 68 的祖先；README 明确不能替换 event 68。
- event 83：`errant_commit`，parent=68，tick=238083249096，dyn=393846，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，corr=taint_prop。它是 raw stream 中的悬空 L5 标签记录，按权威口径不改变 detected_contained；本文件不把它写成终局，但也不隐瞒。
- `request_fork` 1 条：event 4294967296，parent=4，tick=238083183495，old_request_id=393897→new_request_id=393847，dest_event_id=26，`bridge_layer=L3`、`bridge_reason=request_handoff`、`shared_addr=ffffffc009483960`、`shared_size=10`。它把 fault 请求交给 request 393847，event 81 的 taint_reg 属于该分支，不在 event 68 的祖先上。
- 59 条 `squash_masked` 全部是 L4 contained=1；除了 68/1797，还可列出 event 1679（VA=ffffffc009483740）、1714（…3458）、1734（…3430）等；其中 68 是权威见证，1797 等是更晚/其它 VA 的旁支。
- `chain_end`：fault1 9308（tick=2910165686235，L5 标签 errant_commit_seen）；fault2 9309（L4）、fault3 9310（L4 store_discarded_not_retired）、fault4 9311（L4 store_discarded_not_retired）。
- **其它 fault**：fault2 event 8331（VA=ffffffc0094832c0，PFN 81d74→c1d74，mask 0x40000，cache_access 8336，taint 8357，contained 8751）；fault3 event 9255（VA=ffffffc009482eb0，PFN 81d74→81974，mask 0x400，sq_execute，taint 9274）；fault4 event 9280（VA=ffffffc008c730e0，PFN 80c73→c0c73，mask 0x40000，lq_read，taint 9299）。它们都是 F2 的后续注入，不并入 fault1。
- consumer 1134 条摘要不在主链。
- 影响：event 1797/event 83 的存在会让读者误以为权威终局是 L5 或更晚的 L4；本文件明确保留 event 68 为终局见证，并把 1797/83 作为旁支/悬空记录说明。它们不改变 detected_contained，也不能用来证明 fault1 的 L5。

## 6. 最终判定与证据完整性

- terminal：`detected_contained`（权威 `chain_report.terminal`）；provable_to：`L5`（报告字段）；传播终局：真实 L4 含住 event 68（tick=238083244768，L4，contained=1，squash_replay）。
- run outcome：`Crash`（oracle=Crash，exit=0）；guest kernel panic。**传播终局 ≠ 运行结局**：fault1 被含住，但整个 run 仍 panic。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效。
- conservation：`ok`（emitted=1134，suppressed=9870，logical_total=11004，issues=[]）。
- count_contradiction：10584−9450=1134（consumer 摘要），已对账。
- campaign/checker agreement：terminal=detected_contained 与权威报告一致；oracle=Crash 与 run.out KERNEL PANIC 一致。
- CHAIN_DEMONSTRATED：**是**（真实 contained 事件 68 + 单祖先链 + admitted/certified）。
- COMPLETE_3_OF_3：**是**（本 RunID 3 个 seed 均有权威终局；本 seed 是 contained）。
- **证据一致性说明（不影响 PASS，但必须列出）**：
  1. plain `chain_report` 的 fault1 `path_event_ids` 尾部是 event 1797，而权威口径（README）指定 event 68 为见证；本文件采用 68，1797 作为更晚的 L4 旁支处理。报告本身没有 regrade 文件，terminal/outcome 仍是 detected_contained。
  2. raw stream 有 event 83 的 `errant_commit`（L5 标签，parent=68）；按 README/checker 的 `_errant_commit_escape` 它是悬空记录，不改变 L4 含住终局。本文件如实记录，不把它写成 L5 见证。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓（terminal/outcome 匹配）10（full N/A）✓ 11✓ 12✓ 13✓ 14✓ 15✓。
- chain_evidence_status：**PASS**
- experiment_identity_status：**WORKLOAD_IDENTITY_MISMATCH**
- overall_experiment_status：**NOT_MIBENCH_RESULT**
- verdict：**NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果）

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/prop_evt.txt.gz` | SHA-256 `19abb053dfa3b960f7c545cbb74b4acf1670c60e3a76099d2de8a74b7ae1b20b`；346270 bytes；mtime `2026-10-27T14:45:19+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/prop_trace.csv.gz` | SHA-256 `50806b85cb368461db91f421cedb31f17999d0526f8309a68d3368857bf62901`；115347 bytes；mtime `2026-10-27T14:45:19+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/chain_report.json` | SHA-256 `6fa079e5cc3424fc344408b80d390aae70ff7079ea23af50811274ab2b9c724d`；960002 bytes；mtime `2026-10-27T14:45:21+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/run.out` | SHA-256 `85bbb48787bad953fa9b41c531cabad3301ae358e90e786db348e44c0fa094cc`；8216 bytes；mtime `2026-10-27T14:45:20+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/run.err` | SHA-256 `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d`；1912 bytes；mtime `2026-10-27T14:45:20+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/stats.txt` | SHA-256 `4759e37f773628f0fa90929efd45c3acc1c69db7031f067567aeaa5e492e07b5`；391280 bytes；mtime `2026-10-27T14:45:20+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/manifest.json` | SHA-256 `af81b336c125f952c59b0cc34e185b9eb4030c342fba893d15c683561cc3b09f`；1438 bytes；mtime `2026-10-27T14:45:22+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2 --cells T10-F2-W1 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`；1145680944 bytes；mtime `2026-10-27T13:09:00+0800`；manifest 记录 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| source head | manifest 字段 | `N/A`；binary_source_head=`d1543872e155943893fdd6d18a489ff7c372d97d`；analysis_tool_head=`d1543872e155943893fdd6d18a489ff7c372d97d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/armtlb_injections.log` | SHA-256 `8b2ed429bf3bf46ffdf641ce6d5ae8331628c4cbff5132f2999826722861edc2`；977 bytes；mtime `2026-10-27T14:45:19+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/board.workload.dmesg` | SHA-256 `3bc166b6e793a1dcaa6935f77c31390c1fe5d540a23e1b4a1316282d28d09637`；14056 bytes；mtime `2026-10-27T14:45:19+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/board.terminal` | SHA-256 `4654c9641a66eb58a2713ab2717b4d16ad53fdce6eee201a1a716647d5baa89b`；1309 bytes；mtime `2026-10-27T14:44:51+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/config.ini` | SHA-256 `b9b8780b8c6d07614eabfcb09d7bd78665b657d097327a6ec7763c73bfde08aa`；97178 bytes；mtime `2026-10-27T14:44:34+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2/config.json` | SHA-256 `b92e765aa16929f70fd09ca8bb51b5df1dbbc75a05375eda07104abe430b69a7`；277159 bytes；mtime `2026-10-27T14:44:34+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s2/T10-F2-W1/seed2`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `R6-AUTHORITATIVE-EVIDENCE.md` 未列出本 seed 的其它副本；权威目录唯一。

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
