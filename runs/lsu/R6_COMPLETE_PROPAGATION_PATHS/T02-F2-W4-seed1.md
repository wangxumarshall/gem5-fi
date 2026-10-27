# T02-F2-W4 seed1 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T02-F2-W4` seed1 中，注入器于 tick=238085259417 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81362` 改成 `0x800400000081362`（VA=`0xffffff8001362708`）；故障 PFN 使有效 PA 从 `0x81362708` 变为 `0x400000081362708`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=20, tick=238085368641）在 L5 形成真实错误提交；运行结局 Crash（KERNEL PANIC under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T02-F2-W4`
- seed: `1`；sample_run_id: `s1`
- 实验模型: 模型ID=`T02`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `双比特翻转`
- 故障模型: PPN内同时翻转2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier: `F2`；effective tier: `F2`；tier enabled: `开启(1)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- source head: N/A（该 run 的 manifest 无 binary_source_head 字段；manifest.source_head=fcacc958b799c635babd2834cce9da6942322d91 只是运行时工作树 HEAD，不等同于二进制构建源）
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/prop_evt.txt.gz`
- prop_evt SHA-256: `6caf97eea470984bce9fb11068a7721618c1abfb626686617219f1aedfb2521e`（本次重算值；字节数 37591）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/chain_report.json`
- chain_report SHA-256: `8307a11250c09a6f9787885b31f6738dc7c42a014ce4918adc24c6c5e3384490`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/manifest.json`（SHA-256 `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/run.out`（SHA-256 `8f1b06fab788211e5c9f07a4f8ce3f466f9bcb3dd330480d4103da14aee125fc`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/run.err`（SHA-256 `542053f2316e00845e96acb4d0f3b335c76fdc87803a2c67dc0821aa4c8332a0`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/stats.txt`（SHA-256 `63782326dc21ea434a3618d624dd488f15275268940fb27e8c2e493336f7c59b`；`board.chaos_armtlb.numFaultsInjected=1`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 1100；代表故障 `fault_id=1` 事件数: 1100；权威报告 fault 数: 1
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffff8001362708，PFN 0x81362→0x800400000081362，PA 0x81362708→0x400000081362708 → TLB 地址翻译 → LQ request_id=415526 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81362` 变成 `800400000081362`（mask=0x800400000000000；PFN 0x81362→0x800400000081362），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`238085259417`；fault_id=`1`；corr=`origin`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffff8001362708`
  - 值变化：before=`81362`→after=`800400000081362`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, old_pfn: 0x81362, new_pfn: 0x800400000081362, FaultType: bit_flip, Mask: 0x800400000000000`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F2 attempted=110149 eligible=110149 injected=1 first_eligible_tick=237950233578 last_eligible_tick=238090618719 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffff8001362708`；PFN=`81362`→`800400000081362`
  - 值变化：before=`81362`→after=`800400000081362`；field=`post_lookup`；state_before=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`；state_after=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=800400000081362;ap=0;mtype=2;page_size=1000;pa=400000081362708`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81362`→`800400000081362`；pa `81362708`→`400000081362708`
- **event_id=`2`；parent_event_id=`1`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0x400000081362708`；PFN=`81362`→`800400000081362`
  - 值变化：before=`81362`→after=`800400000081362`；field=`bit_flip`；state_before=`81362708`；state_after=`400000081362708`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0x400000081362708`
  - 值变化：before=`81362708`→after=`400000081362708`；field=`effective_pa_changed`；state_before=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`；state_after=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=800400000081362;ap=0;mtype=2;page_size=1000;pa=400000081362708`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`81362708`，effective=`400000081362708`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`4`；parent_event_id=`3`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：LQ 读出该 load 的地址/请求；地址中已包含错误 PFN 带来的错误 PA。
  - 地址/身份：VA=`0xffffff8001362708`；lq_idx=`44911`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`5`；parent_event_id=`4`；tick=`238085259417`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0x400000081362708`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`6`；parent_event_id=`5`；tick=`238085259417`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x400000081362708`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`7`；parent_event_id=`6`；tick=`238085259417`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x400000081362708`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x400000081362708`
- **event_id=`8`；parent_event_id=`7`；tick=`238085259750`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0x400000081362700`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`9`；parent_event_id=`8`；tick=`238085259750`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x400000081362700`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`10`；parent_event_id=`9`；tick=`238085259750`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x400000081362700`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x400000081362700`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`14`；parent_event_id=`10`；tick=`238085367975`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x400000081362708`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`15`；parent_event_id=`14`；tick=`238085367975`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0x400000081362708`；lq_idx=`44911`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`16`；parent_event_id=`15`；tick=`238085367975`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x400000081362708`；arch_reg=`4`/phys_reg=`42`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`20`；parent_event_id=`16`；tick=`238085368641`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`20`, tick=`238085368641`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL PANIC under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 1 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=238085368641 ptag=1 reason=errant_commit`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | `inj` | L0 | 1 | origin | 415526 | s1 | 0xffffff8001362708 | — | 0x81362→0x800400000081362 | 81362→800400000081362 | 0x800400000000000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 238085259417 | `tlb_lookup` | L1 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | — | 0x81362→0x800400000081362 | 81362→800400000081362 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 238085259417 | `tlb_pfn` | L2 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | 0x400000081362708 | 0x81362→0x800400000081362 | 81362→800400000081362 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 238085259417 | `tlb_translate_result` | L2 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | 0x400000081362708 | — | 81362708→400000081362708 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 238085259417 | `lq_read` | L3 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 读取 load 请求 |
| 6 | 5 | 4 | 238085259417 | `cache_access` | L3 | 1 | addr_fallback | 415526 | s1 | 0xffffff8001362708 | 0x400000081362708 | — | —→— | — | — | — | — | — | 直接 parent（parent=4）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 7 | 6 | 5 | 238085259417 | `cache_return` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0x400000081362708 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 hit/miss 决策 |
| 8 | 7 | 6 | 238085259417 | `mshr_alloc` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0x400000081362708 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=6） | L3 MSHR 分配 |
| 9 | 8 | 7 | 238085259750 | `cache_access` | L3 | 1 | addr_fallback | 415526 | s1 | 0xffffff8001362708 | 0x400000081362700 | — | —→— | — | — | — | — | — | 直接 parent（parent=7） | L3 cache 查找 |
| 10 | 9 | 8 | 238085259750 | `cache_return` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0x400000081362700 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 hit/miss 决策 |
| 11 | 10 | 9 | 238085259750 | `mshr_alloc` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0x400000081362700 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=9） | L3 MSHR 分配 |
| 12 | 14 | 10 | 238085367975 | `resp` | L3 | 1 | seq_primary | 415526 | s1 | 0x400000081362708 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=10）；corr addr_fallback→seq_primary | L3 响应返回 |
| 13 | 15 | 14 | 238085367975 | `lq_complete` | L3 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | 0x400000081362708 | — | —→— | — | — | — | — | — | 直接 parent（parent=14） | L3 load 完成 |
| 14 | 16 | 15 | 238085367975 | `taint_reg` | L4 | 1 | seq_primary | 415526 | s1 | 0x400000081362708 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=15） | L4 污染寄存器 |
| 15 | 20 | 16 | 238085368641 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s1 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=16）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（15 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **1100**；代表故障 `fault_id=1` 的事件数 **1100**；进入最终 ancestry 的事件 **15**；未进入最终 ancestry 的同 fault 事件 **1085**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `cache_access` | 167 | 11–966 | 238085262414–238090386951 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 167 | 12–967 | 238085262414–238090386951 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 167} | 无（outcome/contained 全空） |
| `request_fork` | 124 | 4294967296–4294967419 | 238085262414–238090386951 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `resp` | 118 | 17–969 | 238085367976–238090491846 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 118 | 19–971 | 238085367976–238090491846 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `lq_complete` | 117 | 18–970 | 238085367976–238090491846 | 计数 + 范围 | 无（outcome/contained 全空） |
| `consumer` | 106 | 21–974 | 238085368974–238090493178 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `mshr_alloc` | 86 | 25–959 | 238085373969–238090385952 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_merge` | 81 | 13–968 | 238085262414–238090386951 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 238085262414 |
| L4 | `taint_reg` | 19 | 238085367976 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=106；event_id 范围 `21`–`974`；tick 范围 `238085368974`–`238090493178`；corr 分布 {'taint_prop': 106}；outcome 分布 {'': 106}；contained 分布 {'': 106}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=118；event_id `19`–`971`；tick `238085367976`–`238090491846`；distinct dyn_inst_seq=118；distinct phys_reg=99；distinct arch_reg=6；corr 分布 {'addr_fallback': 118}；outcome 分布 {'': 118}；contained 分布 {'': 118}；sample_run 分布 {'s1': 118}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 19 | 238085367976 | 18 | 415576 | 4/16 | clean→tainted | addr_fallback |
| 37 | 238085482527 | 36 | 415656 | 4/120 | clean→tainted | addr_fallback |
| 40 | 238085482528 | 39 | 415700 | 4/163 | clean→tainted | addr_fallback |
| 43 | 238085482529 | 42 | 415750 | 4/210 | clean→tainted | addr_fallback |
| 61 | 238085606736 | 60 | 415876 | 4/177 | clean→tainted | addr_fallback |
| 64 | 238085606737 | 63 | 415920 | 4/194 | clean→tainted | addr_fallback |
| 67 | 238085606738 | 66 | 415970 | 4/45 | clean→tainted | addr_fallback |
| 85 | 238085725284 | 84 | 416050 | 4/249 | clean→tainted | addr_fallback |
| 902 | 238090066274 | 901 | 424034 | 2/45 | clean→tainted | addr_fallback |
| 905 | 238090066275 | 904 | 424035 | 2/193 | clean→tainted | addr_fallback |
| 915 | 238090068603 | 914 | 424072 | 3/210 | clean→tainted | addr_fallback |
| 926 | 238090177161 | 925 | 424037 | —/— | clean→tainted | addr_fallback |
| 929 | 238090177162 | 928 | 424043 | 0/149 | clean→tainted | addr_fallback |
| 942 | 238090372965 | 941 | 424523 | 4/71 | clean→tainted | addr_fallback |
| 945 | 238090372966 | 944 | 424569 | 4/215 | clean→tainted | addr_fallback |
| 971 | 238090491846 | 970 | 424597 | 1/104 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（118 条，不折叠，逐条列出）</b></summary>

19@238085367976(4/16) 37@238085482527(4/120) 40@238085482528(4/163) 43@238085482529(4/210) 61@238085606736(4/177) 64@238085606737(4/194) 67@238085606738(4/45) 85@238085725284(4/249)

88@238085725285(4/73) 91@238085725286(4/63) 109@238085860815(4/70) 112@238085860816(4/206) 115@238085860817(4/116) 133@238085979696(4/134) 136@238085979697(4/148) 139@238085979698(4/107)

157@238086103905(4/186) 160@238086103906(4/142) 163@238086103907(4/113) 181@238086222453(4/208) 184@238086222454(4/175) 187@238086222455(4/209) 205@238086357984(4/128) 208@238086357985(4/185)

211@238086357986(4/173) 229@238086476865(4/92) 232@238086476866(4/61) 235@238086476867(4/57) 253@238086601074(4/120) 256@238086601075(4/174) 259@238086601076(4/9) 272@238086720621(4/65)

275@238086720622(4/159) 292@238086835173(4/209) 295@238086835175(4/31) 311@238086971037(4/129) 314@238086971038(4/231) 317@238086971039(4/76) 335@238087089918(4/186) 338@238087089919(4/95)

341@238087089920(4/201) 358@238087214127(4/0) 361@238087214128(4/63) 364@238087214129(4/168) 381@238087332675(4/16) 384@238087332676(4/7) 387@238087332677(4/82) 404@238087468206(4/174)

407@238087468207(4/197) 410@238087468208(4/106) 427@238087587087(4/212) 430@238087587088(4/83) 433@238087587089(4/26) 451@238087711296(4/150) 454@238087711297(4/156) 457@238087711298(4/62)

475@238087829844(4/119) 478@238087829845(4/185) 481@238087829846(4/254) 498@238087965375(4/50) 501@238087965376(4/171) 504@238087965377(4/223) 522@238088084256(4/70) 525@238088084257(4/4)

528@238088084258(4/251) 545@238088208465(4/186) 548@238088208466(4/143) 551@238088208467(4/240) 568@238088327013(4/128) 571@238088327014(4/123) 574@238088327015(4/10) 591@238088462544(4/145)

594@238088462545(4/89) 597@238088462546(4/126) 615@238088581425(4/241) 618@238088581426(4/211) 621@238088581427(4/104) 639@238088705634(4/212) 642@238088705635(4/32) 645@238088705636(4/144)

662@238088824182(4/90) 665@238088824183(4/43) 668@238088824184(4/224) 686@238088959713(4/146) 689@238088959714(4/170) 692@238088959715(4/191) 706@238089079260(4/204) 709@238089079261(4/82)

725@238089193812(4/26) 728@238089193814(4/162) 744@238089318354(4/189) 747@238089318355(4/86) 750@238089318356(4/23) 768@238089436902(4/193) 771@238089436903(4/237) 774@238089436904(4/183)

792@238089572433(4/6) 795@238089572434(4/127) 798@238089572435(4/80) 816@238089691314(4/138) 819@238089691315(4/20) 822@238089691316(4/155) 840@238089815523(4/176) 843@238089815524(4/205)

846@238089815525(4/244) 864@238089934071(4/147) 867@238089934072(4/47) 870@238089934073(4/168) 896@238090066272(2/20) 899@238090066273(1/22) 902@238090066274(2/45) 905@238090066275(2/193)

915@238090068603(3/210) 926@238090177161(—/—) 929@238090177162(0/149) 942@238090372965(4/71) 945@238090372966(4/215) 971@238090491846(1/104)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（167 条，不折叠）</b></summary>

12@238085262414:miss 24@238085373969:miss 27@238085374302:miss 30@238085378631:miss 33@238085380962:miss 48@238085498178:miss 51@238085498511:miss 54@238085504838:miss

57@238085507169:miss 72@238085616726:miss 75@238085617059:miss 78@238085622054:miss 81@238085624385:miss 96@238085752257:miss 99@238085752590:miss 102@238085753922:miss

105@238085756586:miss 120@238085871138:miss 123@238085871471:miss 126@238085876133:miss 129@238085878464:miss 144@238085995347:miss 147@238085995680:miss 150@238086002007:miss

153@238086004338:miss 168@238086113895:miss 171@238086114228:miss 174@238086119223:miss 177@238086121554:miss 192@238086249426:miss 195@238086249759:miss 198@238086251091:miss

201@238086253755:miss 216@238086368307:miss 219@238086368640:miss 222@238086373302:miss 225@238086375633:miss 240@238086492516:miss 243@238086492849:miss 246@238086499176:miss

249@238086501507:miss 262@238086612063:miss 265@238086612396:miss 268@238086620388:miss 279@238086726615:miss 282@238086726948:miss 285@238086728946:miss 288@238086737604:miss

298@238086862479:miss 301@238086862812:miss 304@238086864144:miss 307@238086866808:miss 322@238086981360:miss 325@238086981693:miss 328@238086986355:miss 331@238086988686:miss

345@238087105569:miss 348@238087105902:miss 351@238087112229:miss 354@238087114560:miss 368@238087224117:miss 371@238087224450:miss 374@238087229445:miss 377@238087231776:miss

391@238087359648:miss 394@238087359981:miss 397@238087361313:miss 400@238087363977:miss 414@238087478529:miss 417@238087478862:miss 420@238087483524:miss 423@238087485855:miss

438@238087602738:miss 441@238087603071:miss 444@238087609398:miss 447@238087611729:miss 462@238087721286:miss 465@238087721619:miss 468@238087726614:miss 471@238087728945:miss

485@238087856817:miss 488@238087857150:miss 491@238087858482:miss 494@238087861146:miss 509@238087975698:miss 512@238087976031:miss 515@238087980693:miss 518@238087983024:miss

532@238088099907:miss 535@238088100240:miss 538@238088106567:miss 541@238088108898:miss 555@238088218455:miss 558@238088218788:miss 561@238088223783:miss 564@238088226114:miss

578@238088353986:miss 581@238088354319:miss 584@238088355651:miss 587@238088358315:miss 602@238088472867:miss 605@238088473200:miss 608@238088477862:miss 611@238088480193:miss

626@238088597076:miss 629@238088597409:miss 632@238088603736:miss 635@238088606067:miss 649@238088715624:miss 652@238088715957:miss 655@238088720952:miss 658@238088723283:miss

673@238088851155:miss 676@238088851488:miss 679@238088852820:miss 682@238088855484:miss 696@238088970702:miss 699@238088971035:miss 702@238088979027:miss 712@238089085254:miss

715@238089085587:miss 718@238089087585:miss 721@238089096243:miss 731@238089209796:miss 734@238089210129:miss 737@238089216456:miss 740@238089218787:miss 755@238089328344:miss

758@238089328677:miss 761@238089333672:miss 764@238089336003:miss 779@238089463875:miss 782@238089464208:miss 785@238089465540:miss 788@238089468204:miss 803@238089582756:miss

806@238089583089:miss 809@238089587751:miss 812@238089590082:miss 827@238089706965:miss 830@238089707298:miss 833@238089713625:miss 836@238089715956:miss 851@238089825513:miss

854@238089825846:miss 857@238089830841:miss 860@238089833172:miss 874@238089957714:miss 877@238089957714:miss 880@238089958047:miss 883@238089958713:miss 886@238089958713:miss

889@238089960045:miss 892@238089960378:miss 917@238090068603:miss 920@238090068936:miss 923@238090069269:miss 932@238090264407:miss 935@238090264740:miss 938@238090266405:miss

949@238090383288:miss 952@238090383621:miss 955@238090385619:miss 958@238090385952:miss 961@238090386618:miss 964@238090386618:miss 967@238090386951:miss

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（167 条，不折叠）</b></summary>

13@238085262414:mshr_merge:mshr=2,fill=— 25@238085373969:mshr_alloc:mshr=3,fill=— 28@238085374302:mshr_alloc:mshr=4,fill=— 31@238085378631:mshr_merge:mshr=4,fill=—

34@238085380962:mshr_merge:mshr=4,fill=— 49@238085498178:mshr_alloc:mshr=5,fill=— 52@238085498511:mshr_alloc:mshr=6,fill=— 55@238085504838:mshr_merge:mshr=6,fill=—

58@238085507169:mshr_merge:mshr=6,fill=— 73@238085616726:mshr_alloc:mshr=7,fill=— 76@238085617059:mshr_alloc:mshr=8,fill=— 79@238085622054:mshr_merge:mshr=8,fill=—

82@238085624385:mshr_merge:mshr=8,fill=— 97@238085752257:mshr_alloc:mshr=9,fill=— 100@238085752590:mshr_alloc:mshr=10,fill=— 103@238085753922:mshr_merge:mshr=10,fill=—

106@238085756586:mshr_merge:mshr=10,fill=— 121@238085871138:mshr_alloc:mshr=11,fill=— 124@238085871471:mshr_alloc:mshr=12,fill=— 127@238085876133:mshr_merge:mshr=12,fill=—

130@238085878464:mshr_merge:mshr=12,fill=— 145@238085995347:mshr_alloc:mshr=13,fill=— 148@238085995680:mshr_alloc:mshr=14,fill=— 151@238086002007:mshr_merge:mshr=14,fill=—

154@238086004338:mshr_merge:mshr=14,fill=— 169@238086113895:mshr_alloc:mshr=15,fill=— 172@238086114228:mshr_alloc:mshr=16,fill=— 175@238086119223:mshr_merge:mshr=16,fill=—

178@238086121554:mshr_merge:mshr=16,fill=— 193@238086249426:mshr_alloc:mshr=17,fill=— 196@238086249759:mshr_alloc:mshr=18,fill=— 199@238086251091:mshr_merge:mshr=18,fill=—

202@238086253755:mshr_merge:mshr=18,fill=— 217@238086368307:mshr_alloc:mshr=19,fill=— 220@238086368640:mshr_alloc:mshr=20,fill=— 223@238086373302:mshr_merge:mshr=20,fill=—

226@238086375633:mshr_merge:mshr=20,fill=— 241@238086492516:mshr_alloc:mshr=21,fill=— 244@238086492849:mshr_alloc:mshr=22,fill=— 247@238086499176:mshr_merge:mshr=22,fill=—

250@238086501507:mshr_merge:mshr=22,fill=— 263@238086612063:mshr_alloc:mshr=23,fill=— 266@238086612396:mshr_alloc:mshr=24,fill=— 269@238086620388:mshr_merge:mshr=24,fill=—

280@238086726615:mshr_alloc:mshr=25,fill=— 283@238086726948:mshr_alloc:mshr=26,fill=— 286@238086728946:mshr_merge:mshr=26,fill=— 289@238086737604:mshr_merge:mshr=26,fill=—

299@238086862479:mshr_alloc:mshr=27,fill=— 302@238086862812:mshr_alloc:mshr=28,fill=— 305@238086864144:mshr_merge:mshr=28,fill=— 308@238086866808:mshr_merge:mshr=28,fill=—

323@238086981360:mshr_alloc:mshr=29,fill=— 326@238086981693:mshr_alloc:mshr=30,fill=— 329@238086986355:mshr_merge:mshr=30,fill=— 332@238086988686:mshr_merge:mshr=30,fill=—

346@238087105569:mshr_alloc:mshr=31,fill=— 349@238087105902:mshr_alloc:mshr=32,fill=— 352@238087112229:mshr_merge:mshr=32,fill=— 355@238087114560:mshr_merge:mshr=32,fill=—

369@238087224117:mshr_alloc:mshr=33,fill=— 372@238087224450:mshr_alloc:mshr=34,fill=— 375@238087229445:mshr_merge:mshr=34,fill=— 378@238087231776:mshr_merge:mshr=34,fill=—

392@238087359648:mshr_alloc:mshr=35,fill=— 395@238087359981:mshr_alloc:mshr=36,fill=— 398@238087361313:mshr_merge:mshr=36,fill=— 401@238087363977:mshr_merge:mshr=36,fill=—

415@238087478529:mshr_alloc:mshr=37,fill=— 418@238087478862:mshr_alloc:mshr=38,fill=— 421@238087483524:mshr_merge:mshr=38,fill=— 424@238087485855:mshr_merge:mshr=38,fill=—

439@238087602738:mshr_alloc:mshr=39,fill=— 442@238087603071:mshr_alloc:mshr=40,fill=— 445@238087609398:mshr_merge:mshr=40,fill=— 448@238087611729:mshr_merge:mshr=40,fill=—

463@238087721286:mshr_alloc:mshr=41,fill=— 466@238087721619:mshr_alloc:mshr=42,fill=— 469@238087726614:mshr_merge:mshr=42,fill=— 472@238087728945:mshr_merge:mshr=42,fill=—

486@238087856817:mshr_alloc:mshr=43,fill=— 489@238087857150:mshr_alloc:mshr=44,fill=— 492@238087858482:mshr_merge:mshr=44,fill=— 495@238087861146:mshr_merge:mshr=44,fill=—

510@238087975698:mshr_alloc:mshr=45,fill=— 513@238087976031:mshr_alloc:mshr=46,fill=— 516@238087980693:mshr_merge:mshr=46,fill=— 519@238087983024:mshr_merge:mshr=46,fill=—

533@238088099907:mshr_alloc:mshr=47,fill=— 536@238088100240:mshr_alloc:mshr=48,fill=— 539@238088106567:mshr_merge:mshr=48,fill=— 542@238088108898:mshr_merge:mshr=48,fill=—

556@238088218455:mshr_alloc:mshr=49,fill=— 559@238088218788:mshr_alloc:mshr=50,fill=— 562@238088223783:mshr_merge:mshr=50,fill=— 565@238088226114:mshr_merge:mshr=50,fill=—

579@238088353986:mshr_alloc:mshr=51,fill=— 582@238088354319:mshr_alloc:mshr=52,fill=— 585@238088355651:mshr_merge:mshr=52,fill=— 588@238088358315:mshr_merge:mshr=52,fill=—

603@238088472867:mshr_alloc:mshr=53,fill=— 606@238088473200:mshr_alloc:mshr=54,fill=— 609@238088477862:mshr_merge:mshr=54,fill=— 612@238088480193:mshr_merge:mshr=54,fill=—

627@238088597076:mshr_alloc:mshr=55,fill=— 630@238088597409:mshr_alloc:mshr=56,fill=— 633@238088603736:mshr_merge:mshr=56,fill=— 636@238088606067:mshr_merge:mshr=56,fill=—

650@238088715624:mshr_alloc:mshr=57,fill=— 653@238088715957:mshr_alloc:mshr=58,fill=— 656@238088720952:mshr_merge:mshr=58,fill=— 659@238088723283:mshr_merge:mshr=58,fill=—

674@238088851155:mshr_alloc:mshr=59,fill=— 677@238088851488:mshr_alloc:mshr=60,fill=— 680@238088852820:mshr_merge:mshr=60,fill=— 683@238088855484:mshr_merge:mshr=60,fill=—

697@238088970702:mshr_alloc:mshr=61,fill=— 700@238088971035:mshr_alloc:mshr=62,fill=— 703@238088979027:mshr_merge:mshr=62,fill=— 713@238089085254:mshr_alloc:mshr=63,fill=—

716@238089085587:mshr_alloc:mshr=64,fill=— 719@238089087585:mshr_merge:mshr=64,fill=— 722@238089096243:mshr_merge:mshr=64,fill=— 732@238089209796:mshr_alloc:mshr=65,fill=—

735@238089210129:mshr_alloc:mshr=66,fill=— 738@238089216456:mshr_merge:mshr=66,fill=— 741@238089218787:mshr_merge:mshr=66,fill=— 756@238089328344:mshr_alloc:mshr=67,fill=—

759@238089328677:mshr_alloc:mshr=68,fill=— 762@238089333672:mshr_merge:mshr=68,fill=— 765@238089336003:mshr_merge:mshr=68,fill=— 780@238089463875:mshr_alloc:mshr=69,fill=—

783@238089464208:mshr_alloc:mshr=70,fill=— 786@238089465540:mshr_merge:mshr=70,fill=— 789@238089468204:mshr_merge:mshr=70,fill=— 804@238089582756:mshr_alloc:mshr=71,fill=—

807@238089583089:mshr_alloc:mshr=72,fill=— 810@238089587751:mshr_merge:mshr=72,fill=— 813@238089590082:mshr_merge:mshr=72,fill=— 828@238089706965:mshr_alloc:mshr=73,fill=—

831@238089707298:mshr_alloc:mshr=74,fill=— 834@238089713625:mshr_merge:mshr=74,fill=— 837@238089715956:mshr_merge:mshr=74,fill=— 852@238089825513:mshr_alloc:mshr=75,fill=—

855@238089825846:mshr_alloc:mshr=76,fill=— 858@238089830841:mshr_merge:mshr=76,fill=— 861@238089833172:mshr_merge:mshr=76,fill=— 875@238089957714:mshr_alloc:mshr=77,fill=—

878@238089957714:mshr_merge:mshr=77,fill=— 881@238089958047:mshr_alloc:mshr=78,fill=— 884@238089958713:mshr_merge:mshr=78,fill=— 887@238089958713:mshr_merge:mshr=78,fill=—

890@238089960045:mshr_alloc:mshr=79,fill=— 893@238089960378:mshr_alloc:mshr=80,fill=— 918@238090068603:mshr_alloc:mshr=81,fill=— 921@238090068936:mshr_alloc:mshr=82,fill=—

924@238090069269:mshr_merge:mshr=82,fill=— 933@238090264407:mshr_alloc:mshr=83,fill=— 936@238090264740:mshr_alloc:mshr=84,fill=— 939@238090266405:mshr_merge:mshr=84,fill=—

950@238090383288:mshr_alloc:mshr=85,fill=— 953@238090383621:mshr_alloc:mshr=86,fill=— 956@238090385619:mshr_alloc:mshr=87,fill=— 959@238090385952:mshr_alloc:mshr=88,fill=—

962@238090386618:mshr_merge:mshr=88,fill=— 965@238090386618:mshr_merge:mshr=88,fill=— 968@238090386951:mshr_merge:mshr=88,fill=—

</details>

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 124 条；event_id `4294967296`–`4294967419`；tick `238085262414`–`238090386951`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 238085262414 | 415526 | 415576 | 10→11 | 0x400000081362000+1000 |
| 4294967297 | 238085373969 | 415526 | 415656 | 16→23 | 0x400000081362000+1000 |
| 4294967298 | 238085378631 | 415526 | 415700 | 16→29 | 0x400000081362000+1000 |
| 4294967299 | 238085380962 | 415526 | 415750 | 16→32 | 0x400000081362000+1000 |
| 4294967300 | 238085498178 | 415526 | 415876 | 16→47 | 0x400000081362000+1000 |
| 4294967415 | 238090383288 | 415526 | 424597 | 16→948 | 0x400000081362000+1000 |
| 4294967416 | 238090385619 | 415526 | 424643 | 16→954 | 0x400000081362000+1000 |
| 4294967417 | 238090386618 | 415526 | 424671 | 16→960 | 0x400000081362000+1000 |
| 4294967418 | 238090386618 | 415526 | 424676 | 16→963 | 0x400000081362000+1000 |
| 4294967419 | 238090386951 | 415526 | 424680 | 16→966 | 0x400000081362000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`975`；tick=`238090618719`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`20` tick=`238085368641`（parent=`16`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=140; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 15 events |
| 3_tick_order | PASS | ticks 238085259417..238085368641 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=20 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (15); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T02-F2-W4 and seed1 |
| 12_tier_matches_evidence | PASS | matrix=F2 run.out=CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/prop_evt.txt.gz` | `6caf97eea470984bce9fb11068a7721618c1abfb626686617219f1aedfb2521e` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/chain_report.json` | `8307a11250c09a6f9787885b31f6738dc7c42a014ce4918adc24c6c5e3384490` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/manifest.json` | `b44315cdb65e033dc441ffb3528233868bc74b87ea0b3afe76c7777e9b2aa9e9` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/run.out` | `8f1b06fab788211e5c9f07a4f8ce3f466f9bcb3dd330480d4103da14aee125fc` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/run.err` | `542053f2316e00845e96acb4d0f3b335c76fdc87803a2c67dc0821aa4c8332a0` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3/T02-F2-W4/seed1/stats.txt` | `63782326dc21ea434a3618d624dd488f15275268940fb27e8c2e493336f7c59b` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
