# T01-F1-W4 seed3 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T01-F1-W4` seed3 中，注入器于 tick=239629862268 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x83111` 改成 `0x200000083111`（VA=`0x7fe7c61d40`）；故障 PFN 使有效 PA 从 `0x83111d40` 变为 `0x200000083111d40`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=39, tick=239629971492）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T01-F1-W4`
- seed: `3`；sample_run_id: `s3`
- 实验模型: 模型ID=`T01`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `单比特翻转`
- 故障模型: 随机选有效表项的VPN tag翻转1 bit；只在注入后再次命中才计activated。实施细则：每次故障运行只选一个当前有效且可被后续使用的目标，在指定字段内均匀抽取一个 bit 做一次 XOR 翻转；其余字段保持无故障值。保存目标 entry/way、bit 编号、原值和故障值，避免把未使用空项计为有效样本。激活口径：仅当“DTLB中存在有效项”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F1` — 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier: `F1`；effective tier: `F1`；tier enabled: `开启(1)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- source head: `38122675b91e05aaa0d636d14a89b6c6a90ea53c`
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/prop_evt.txt.gz`
- prop_evt SHA-256: `381505282524dd5ff1e6fcd0c460373b7b0c1100cc5362977f90e8ecd746b148`（本次重算值；字节数 238314）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/chain_report.json`
- chain_report SHA-256: `14ec8e317af555b62a5518ed6c0c6e5b8b15ed54db3ccf2ac65ed375c1fecd1c`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/manifest.json`（SHA-256 `454a07ea4c876dba80411859e79c22855717f67a61a451df58253afdaf3bf20d`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/run.out`（SHA-256 `e24668260bd66b71cd57a97854e2ce68def402496e6d9056b72c29ca9f5360ed`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/run.err`（SHA-256 `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/stats.txt`（SHA-256 `be44142668df0e3b72b9d51653e465df9795563198c5aefc22d7fae44a34b4c6`；`board.chaos_armtlb.numFaultsInjected=3`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 3445；代表故障 `fault_id=1` 事件数: 1353；权威报告 fault 数: 3
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0x7fe7c61d40，PFN 0x83111→0x200000083111，PA 0x83111d40→0x200000083111d40 → TLB 地址翻译 → LQ request_id=5536042 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `83111` 变成 `200000083111`（mask=0x200000000000；PFN 0x83111→0x200000083111），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`239629862268`；fault_id=`1`；corr=`origin`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0x7fe7c61d40`
  - 值变化：before=`83111`→after=`200000083111`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 239629862268, Site: arm_tlb_lookup_hit, VA: 0x7fe7c61d40, old_pfn: 0x83111, new_pfn: 0x200000083111, FaultType: bit_flip, Mask: 0x200000000000, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F1 attempted=3527639 eligible=3527639 injected=3 first_eligible_tick=237950233578 last_eligible_tick=243849044862 fires=0 no_effect=0 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0x7fe7c61d40`；PFN=`83111`→`200000083111`
  - 值变化：before=`83111`→after=`200000083111`；field=`post_lookup`；state_before=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40`；state_after=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=200000083111;ap=1;mtype=2;page_size=1000;pa=200000083111d40`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `83111`→`200000083111`；pa `83111d40`→`200000083111d40`
- **event_id=`2`；parent_event_id=`1`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x200000083111d40`；PFN=`83111`→`200000083111`
  - 值变化：before=`83111`→after=`200000083111`；field=`bit_flip`；state_before=`83111d40`；state_after=`200000083111d40`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x200000083111d40`
  - 值变化：before=`83111d40`→after=`200000083111d40`；field=`effective_pa_changed`；state_before=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40`；state_after=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=200000083111;ap=1;mtype=2;page_size=1000;pa=200000083111d40`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`83111d40`，effective=`200000083111d40`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`4`；parent_event_id=`3`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：LQ 读出该 load 的地址/请求；地址中已包含错误 PFN 带来的错误 PA。
  - 地址/身份：VA=`0x7fe7c61d40`；lq_idx=`594678`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`5`；parent_event_id=`4`；tick=`239629862268`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x200000083111d40`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`6`；parent_event_id=`5`；tick=`239629862268`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x200000083111d40`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`7`；parent_event_id=`6`；tick=`239629862268`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x200000083111d40`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x200000083111d40`
- **event_id=`8`；parent_event_id=`7`；tick=`239629862601`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x200000083111d40`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`9`；parent_event_id=`8`；tick=`239629862601`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x200000083111d40`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`10`；parent_event_id=`9`；tick=`239629862601`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x200000083111d40`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x200000083111d40`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`35`；parent_event_id=`10`；tick=`239629970826`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x0`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`36`；parent_event_id=`35`；tick=`239629970826`；fault_id=`1`；corr=`seq_primary`；request_id=`0`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0x7fe7c61d32`；PA=`0x0`；lq_idx=`594678`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`37`；parent_event_id=`36`；tick=`239629970826`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x0`；arch_reg=`4`/phys_reg=`68`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
- **event_id=`38`；parent_event_id=`37`；tick=`239629970826`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x0`；arch_reg=`5`/phys_reg=`153`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`39`；parent_event_id=`38`；tick=`239629971492`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`39`, tick=`239629971492`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 3 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=239629971492 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=241738405947 ptag=2 reason=effective_pa_unchanged`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=243849044862 ptag=3 reason=store_discarded_not_retired`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239629862268 | `inj` | L0 | 1 | origin | 5536042 | s3 | 0x7fe7c61d40 | — | 0x83111→0x200000083111 | 83111→200000083111 | 0x200000000000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 239629862268 | `tlb_lookup` | L1 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | — | 0x83111→0x200000083111 | 83111→200000083111 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 239629862268 | `tlb_pfn` | L2 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | 0x200000083111d40 | 0x83111→0x200000083111 | 83111→200000083111 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 239629862268 | `tlb_translate_result` | L2 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | 0x200000083111d40 | — | 83111d40→200000083111d40 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 239629862268 | `lq_read` | L3 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 读取 load 请求 |
| 6 | 5 | 4 | 239629862268 | `cache_access` | L3 | 1 | addr_fallback | 5536042 | s3 | 0x7fe7c61d40 | 0x200000083111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=4）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 7 | 6 | 5 | 239629862268 | `cache_return` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x200000083111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 hit/miss 决策 |
| 8 | 7 | 6 | 239629862268 | `mshr_alloc` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x200000083111d40 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=6） | L3 MSHR 分配 |
| 9 | 8 | 7 | 239629862601 | `cache_access` | L3 | 1 | addr_fallback | 5536042 | s3 | 0x7fe7c61d40 | 0x200000083111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=7） | L3 cache 查找 |
| 10 | 9 | 8 | 239629862601 | `cache_return` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x200000083111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 hit/miss 决策 |
| 11 | 10 | 9 | 239629862601 | `mshr_alloc` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x200000083111d40 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=9） | L3 MSHR 分配 |
| 12 | 35 | 10 | 239629970826 | `resp` | L3 | 1 | seq_primary | — | s3 | 0x0 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=10）；corr addr_fallback→seq_primary | L3 响应返回 |
| 13 | 36 | 35 | 239629970826 | `lq_complete` | L3 | 1 | seq_primary | 0 | s3 | 0x7fe7c61d32 | 0x0 | — | —→— | — | — | — | — | — | 直接 parent（parent=35） | L3 load 完成 |
| 14 | 37 | 36 | 239629970826 | `taint_reg` | L4 | 1 | seq_primary | — | s3 | 0x0 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=36） | L4 污染寄存器 |
| 15 | 38 | 37 | 239629970826 | `taint_reg` | L4 | 1 | seq_primary | — | s3 | 0x0 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=37） | L4 污染寄存器 |
| 16 | 39 | 38 | 239629971492 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s3 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=38）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（16 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **3445**；代表故障 `fault_id=1` 的事件数 **1353**；进入最终 ancestry 的事件 **16**；未进入最终 ancestry 的同 fault 事件 **1337**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 1281 | 40–1344 | 239629971825–239653972800 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `cache_access` | 10 | 11–86 | 239629863600–239629980816 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 10 | 12–87 | 239629863600–239629980816 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 10} | 无（outcome/contained 全空） |
| `request_fork` | 7 | 4294967296–4294967302 | 239629863600–239629980483 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `mshr_alloc` | 6 | 13–88 | 239629863600–239629980816 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `resp` | 6 | 41–62 | 239629972158–239629972492 | 计数 + 范围 | 无（outcome/contained 全空） |
| `lq_complete` | 6 | 42–63 | 239629972158–239629972492 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 6 | 43–64 | 239629972158–239629972492 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `mshr_merge` | 4 | 25–34 | 239629865931–239629867596 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 239629863600 |
| L4 | `consumer` | 40 | 239629971825 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=1281；event_id 范围 `40`–`1344`；tick 范围 `239629971825`–`239653972800`；corr 分布 {'taint_prop': 1281}；outcome 分布 {'': 1281}；contained 分布 {'': 1281}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=6；event_id `43`–`64`；tick `239629972158`–`239629972492`；distinct dyn_inst_seq=6；distinct phys_reg=6；distinct arch_reg=3；corr 分布 {'addr_fallback': 6}；outcome 分布 {'': 6}；contained 分布 {'': 6}；sample_run 分布 {'s3': 6}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 43 | 239629972158 | 42 | 5536060 | 2/33 | clean→tainted | addr_fallback |
| 48 | 239629972159 | 47 | 5536091 | 2/165 | clean→tainted | addr_fallback |
| 51 | 239629972160 | 50 | 5536095 | 1/248 | clean→tainted | addr_fallback |
| 54 | 239629972161 | 53 | 5536116 | 0/216 | clean→tainted | addr_fallback |
| 57 | 239629972491 | 56 | 5536064 | 1/205 | clean→tainted | addr_fallback |
| 64 | 239629972492 | 63 | 5536112 | 0/81 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（6 条，不折叠，逐条列出）</b></summary>

43@239629972158(2/33) 48@239629972159(2/165) 51@239629972160(1/248) 54@239629972161(0/216) 57@239629972491(1/205) 64@239629972492(0/81)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（10 条，不折叠）</b></summary>

12@239629863600:miss 15@239629863933:miss 18@239629863933:miss 21@239629864266:miss 24@239629865931:miss 27@239629865931:miss 30@239629867263:miss 33@239629867596:miss

84@239629980483:miss 87@239629980816:miss

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（10 条，不折叠）</b></summary>

13@239629863600:mshr_alloc:mshr=3,fill=— 16@239629863933:mshr_alloc:mshr=4,fill=— 19@239629863933:mshr_alloc:mshr=5,fill=— 22@239629864266:mshr_alloc:mshr=6,fill=—

25@239629865931:mshr_merge:mshr=4,fill=— 28@239629865931:mshr_merge:mshr=4,fill=— 31@239629867263:mshr_merge:mshr=6,fill=— 34@239629867596:mshr_merge:mshr=4,fill=—

85@239629980483:mshr_alloc:mshr=7,fill=— 88@239629980816:mshr_alloc:mshr=8,fill=—

</details>

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 7 条；event_id `4294967296`–`4294967302`；tick `239629863600`–`239629980483`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 239629863600 | 5536042 | 5536060 | 10→11 | 0x200000083111000+1000 |
| 4294967297 | 239629863933 | 5536042 | 5536064 | 10→17 | 0x200000083111000+1000 |
| 4294967298 | 239629865931 | 5536042 | 5536091 | 10→23 | 0x200000083111000+1000 |
| 4294967299 | 239629865931 | 5536042 | 5536095 | 10→26 | 0x200000083111000+1000 |
| 4294967300 | 239629867263 | 5536042 | 5536112 | 10→29 | 0x200000083111000+1000 |
| 4294967301 | 239629867596 | 5536042 | 5536116 | 10→32 | 0x200000083111000+1000 |
| 4294967302 | 239629980483 | 5536042 | 5536201 | 10→83 | 0x200000083111000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`3306`；tick=`243849044862`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 3 个 fault；本文件的代表故障 `fault_id=1` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'full': 1, 'detected_contained': 1, 'provable_to_L4_then_unknown': 1}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1（代表） | full | L5 | 1353 |
| 2 | detected_contained | L2 | 5 |
| 3 | provable_to_L4_then_unknown | L4 | 2087 |

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`39` tick=`239629971492`（parent=`38`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=24; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 16 events |
| 3_tick_order | PASS | ticks 239629862268..239629971492 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=39 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (16); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T01-F1-W4 and seed3 |
| 12_tier_matches_evidence | PASS | matrix=F1 run.out=CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/prop_evt.txt.gz` | `381505282524dd5ff1e6fcd0c460373b7b0c1100cc5362977f90e8ecd746b148` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/chain_report.json` | `14ec8e317af555b62a5518ed6c0c6e5b8b15ed54db3ccf2ac65ed375c1fecd1c` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/manifest.json` | `454a07ea4c876dba80411859e79c22855717f67a61a451df58253afdaf3bf20d` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/run.out` | `e24668260bd66b71cd57a97854e2ce68def402496e6d9056b72c29ca9f5360ed` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/run.err` | `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3/T01-F1-W4/seed3/stats.txt` | `be44142668df0e3b72b9d51653e465df9795563198c5aefc22d7fae44a34b4c6` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
