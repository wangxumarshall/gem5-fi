# T02-F0-W4 seed1 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T02-F0-W4` seed1 中，注入器于 tick=237950940537 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81d75` 改成 `0x100040000081d75`（VA=`0xffffffc009483fa8`）；故障 PFN 使有效 PA 从 `0x81d75fa8` 变为 `0x40000081d75fa8`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=98, tick=237951472338）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T02-F0-W4`
- seed: `1`；sample_run_id: `s1`
- 实验模型: 模型ID=`T02`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `双比特翻转`
- 故障模型: PPN内同时翻转2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier: `F0`；effective tier: `F0`；tier enabled: `关闭(0)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- source head: N/A（该 run 的 manifest 无 binary_source_head 字段；manifest.source_head=bc82f29d8f69410461d18c07a1ee9314f18885a5 只是运行时工作树 HEAD，不等同于二进制构建源）
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/prop_evt.txt.gz`
- prop_evt SHA-256: `4fadb9e9fd6768f63b1125f2a9f5eb2c6cb0ca8707092c46424841ce61e0770a`（本次重算值；字节数 8422）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/chain_report.json`
- chain_report SHA-256: `e06393ed8010bdc23f473174423ad97101d749aecd9c87c3d1519031b3b45016`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json`（SHA-256 `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/run.out`（SHA-256 `2f095e9493fa90a69a9a44128ffa3a349e19460a6ec7fc9eb2e494269221701e`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/run.err`（SHA-256 `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/stats.txt`（SHA-256 `d57b9ce5a0be2764e334a82915714ed98801c6a0e7f6744cea79ccc73212b181`；`board.chaos_armtlb.numFaultsInjected=1`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 208；代表故障 `fault_id=1` 事件数: 208；权威报告 fault 数: 1
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc009483fa8，PFN 0x81d75→0x100040000081d75，PA 0x81d75fa8→0x40000081d75fa8 → TLB 地址翻译 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81d75` 变成 `100040000081d75`（mask=0x100040000000000；PFN 0x81d75→0x100040000081d75），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950940537`；fault_id=`1`；corr=`origin`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc009483fa8`
  - 值变化：before=`81d75`→after=`100040000081d75`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0x100040000081d75, FaultType: bit_flip, Mask: 0x100040000000000`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=150224 eligible=56 injected=1 first_eligible_tick=237950233578 last_eligible_tick=237950940537 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc009483fa8`；PFN=`81d75`→`100040000081d75`
  - 值变化：before=`81d75`→after=`100040000081d75`；field=`post_lookup`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100040000081d75;ap=0;mtype=2;page_size=1000;pa=40000081d75fa8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81d75`→`100040000081d75`；pa `81d75fa8`→`40000081d75fa8`
- **event_id=`2`；parent_event_id=`1`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0x40000081d75fa8`；PFN=`81d75`→`100040000081d75`
  - 值变化：before=`81d75`→after=`100040000081d75`；field=`bit_flip`；state_before=`81d75fa8`；state_after=`40000081d75fa8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0x40000081d75fa8`
  - 值变化：before=`81d75fa8`→after=`40000081d75fa8`；field=`effective_pa_changed`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=100040000081d75;ap=0;mtype=2;page_size=1000;pa=40000081d75fa8`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`81d75fa8`，effective=`40000081d75fa8`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`4`；parent_event_id=`3`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`301`**
  - 硬件结构/事件：store 在 LSU 发射，使用被污染的地址。
  - 地址/身份：VA=`0xffffffc009483fa8`；sq_idx=`32`
  - 值变化：state_before=`issued`；state_after=`—`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`6`；parent_event_id=`5`；tick=`237950941869`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0x40000081d75fa8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`7`；parent_event_id=`6`；tick=`237950941869`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x40000081d75fa8`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`8`；parent_event_id=`7`；tick=`237950941869`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x40000081d75fa8`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x40000081d75fa8`
- **event_id=`15`；parent_event_id=`8`；tick=`237950942202`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0x40000081d75f80`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`16`；parent_event_id=`15`；tick=`237950942202`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x40000081d75f80`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`17`；parent_event_id=`16`；tick=`237950942202`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x40000081d75f80`；mshr_id=`3`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`3`；cache_line=`0x40000081d75f80`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`5`；parent_event_id=`4`；tick=`237950941869`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`301`**
  - 硬件结构/事件：store 数据/地址写回存储子系统，错误 PA 随之进入 cache 侧。
  - 地址/身份：PA=`0x40000081d75fa8`；sq_idx=`32`
  - 值变化：state_before=`—`；state_after=`packet_built`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`30`；parent_event_id=`17`；tick=`237951050427`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x40000081d75fa8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`31`；parent_event_id=`30`；tick=`237951050427`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x40000081d75fa8`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
- **event_id=`32`；parent_event_id=`31`；tick=`237951050427`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`301`**
  - 硬件结构/事件：store 在 SQ 中完成（错误副作用已发生或已被约束）。
  - 地址/身份：VA=`0xffffffc009483fa8`；sq_idx=`32`
  - 值变化：state_before=`—`；state_after=`completed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`98`；parent_event_id=`32`；tick=`237951472338`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`391`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`98`, tick=`237951472338`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 1 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237951472338 ptag=1 reason=errant_commit`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | `inj` | L0 | 1 | origin | 301 | s1 | 0xffffffc009483fa8 | — | 0x81d75→0x100040000081d75 | 81d75→100040000081d75 | 0x100040000000000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950940537 | `tlb_lookup` | L1 | 1 | seq_primary | 301 | s1 | 0xffffffc009483fa8 | — | 0x81d75→0x100040000081d75 | 81d75→100040000081d75 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 237950940537 | `tlb_pfn` | L2 | 1 | seq_primary | 301 | s1 | 0xffffffc009483fa8 | 0x40000081d75fa8 | 0x81d75→0x100040000081d75 | 81d75→100040000081d75 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950940537 | `tlb_translate_result` | L2 | 1 | seq_primary | 301 | s1 | 0xffffffc009483fa8 | 0x40000081d75fa8 | — | 81d75fa8→40000081d75fa8 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 237950940537 | `sq_execute` | L3 | 1 | seq_primary | — | s1 | 0xffffffc009483fa8 | — | — | issued→— | — | — | — | — | — | 直接 parent（parent=3） | L3 store 发射 |
| 6 | 5 | 4 | 237950941869 | `sq_writeback` | L3 | 1 | seq_primary | — | s1 | — | 0x40000081d75fa8 | — | —→packet_built | — | — | — | — | — | 直接 parent（parent=4） | L3 store 写回 |
| 7 | 6 | 5 | 237950941869 | `cache_access` | L3 | 1 | addr_fallback | 301 | s1 | 0xffffffc009483fa8 | 0x40000081d75fa8 | — | —→— | — | — | — | — | — | 直接 parent（parent=5）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 8 | 7 | 6 | 237950941869 | `cache_return` | L3 | 1 | addr_fallback | 301 | s1 | — | 0x40000081d75fa8 | — | —→— | — | — | — | — | — | 直接 parent（parent=6） | L3 hit/miss 决策 |
| 9 | 8 | 7 | 237950941869 | `mshr_alloc` | L3 | 1 | addr_fallback | 301 | s1 | — | 0x40000081d75fa8 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=7） | L3 MSHR 分配 |
| 10 | 15 | 8 | 237950942202 | `cache_access` | L3 | 1 | addr_fallback | 301 | s1 | 0xffffffc009483fa8 | 0x40000081d75f80 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 cache 查找 |
| 11 | 16 | 15 | 237950942202 | `cache_return` | L3 | 1 | addr_fallback | 301 | s1 | — | 0x40000081d75f80 | — | —→— | — | — | — | — | — | 直接 parent（parent=15） | L3 hit/miss 决策 |
| 12 | 17 | 16 | 237950942202 | `mshr_alloc` | L3 | 1 | addr_fallback | 301 | s1 | — | 0x40000081d75f80 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=16） | L3 MSHR 分配 |
| 13 | 30 | 17 | 237951050427 | `resp` | L3 | 1 | seq_primary | 301 | s1 | 0x40000081d75fa8 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=17）；corr addr_fallback→seq_primary | L3 响应返回 |
| 14 | 31 | 30 | 237951050427 | `taint_reg` | L4 | 1 | seq_primary | 301 | s1 | 0x40000081d75fa8 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=30） | L4 污染寄存器 |
| 15 | 32 | 31 | 237951050427 | `sq_complete` | L3 | 1 | seq_primary | — | s1 | 0xffffffc009483fa8 | — | — | —→completed | — | — | — | — | — | 直接 parent（parent=31） | L3 store 完成 |
| 16 | 98 | 32 | 237951472338 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s1 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=32）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（16 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **208**；代表故障 `fault_id=1` 的事件数 **208**；进入最终 ancestry 的事件 **16**；未进入最终 ancestry 的同 fault 事件 **192**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 36 | 99–184 | 237951472338–237965443353 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `cache_access` | 30 | 9–175 | 237950941869–237965333796 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 30 | 10–176 | 237950941869–237965333796 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 30} | 无（outcome/contained 全空） |
| `request_fork` | 22 | 4294967296–4294967317 | 237950941869–237965333463 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `resp` | 20 | 33–178 | 237951050428–237965442021 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 20 | 34–180 | 237951050428–237965442021 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `mshr_alloc` | 16 | 11–177 | 237950941869–237965333796 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_merge` | 14 | 14–127 | 237950941869–237951717093 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `lq_complete` | 3 | 96–179 | 237951471339–237965442021 | 计数 + 范围 | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 237950941869 |
| L4 | `taint_reg` | 34 | 237951050428 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=36；event_id 范围 `99`–`184`；tick 范围 `237951472338`–`237965443353`；corr 分布 {'taint_prop': 36}；outcome 分布 {'': 36}；contained 分布 {'': 36}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=20；event_id `34`–`180`；tick `237951050428`–`237965442021`；distinct dyn_inst_seq=20；distinct phys_reg=4；distinct arch_reg=3；corr 分布 {'addr_fallback': 20}；outcome 分布 {'': 20}；contained 分布 {'': 20}；sample_run 分布 {'s1': 20}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 34 | 237951050428 | 33 | 307 | —/— | clean→tainted | addr_fallback |
| 36 | 237951050429 | 35 | 308 | —/— | clean→tainted | addr_fallback |
| 38 | 237951050760 | 37 | 303 | —/— | clean→tainted | addr_fallback |
| 40 | 237951050761 | 39 | 304 | —/— | clean→tainted | addr_fallback |
| 42 | 237951050762 | 41 | 310 | —/— | clean→tainted | addr_fallback |
| 59 | 237951196614 | 58 | 357 | —/— | clean→tainted | addr_fallback |
| 61 | 237951196615 | 60 | 358 | —/— | clean→tainted | addr_fallback |
| 63 | 237951196616 | 62 | 369 | —/— | clean→tainted | addr_fallback |
| 88 | 237951359454 | 87 | 386 | —/— | clean→tainted | addr_fallback |
| 97 | 237951471339 | 96 | 391 | 0/142 | clean→tainted | addr_fallback |
| 113 | 237951664812 | 112 | 496 | —/— | clean→tainted | addr_fallback |
| 115 | 237951664813 | 114 | 497 | —/— | clean→tainted | addr_fallback |
| 129 | 237951780696 | 128 | 543 | —/— | clean→tainted | addr_fallback |
| 131 | 237951780697 | 130 | 544 | —/— | clean→tainted | addr_fallback |
| 140 | 237957489315 | 139 | 3967 | 0/147 | clean→tainted | addr_fallback |
| 180 | 237965442021 | 179 | 10975 | 1/92 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（20 条，不折叠，逐条列出）</b></summary>

34@237951050428(—/—) 36@237951050429(—/—) 38@237951050760(—/—) 40@237951050761(—/—) 42@237951050762(—/—) 59@237951196614(—/—) 61@237951196615(—/—) 63@237951196616(—/—)

65@237951196617(—/—) 82@237951359451(—/—) 84@237951359452(—/—) 86@237951359453(—/—) 88@237951359454(—/—) 97@237951471339(0/142) 113@237951664812(—/—) 115@237951664813(—/—)

129@237951780696(—/—) 131@237951780697(—/—) 140@237957489315(0/147) 180@237965442021(1/92)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（30 条，不折叠）</b></summary>

10@237950941869:miss 13@237950941869:miss 19@237950942535:miss 22@237950942535:miss 25@237950942535:miss 28@237950942868:miss 44@237951088056:miss 47@237951088056:miss

50@237951088389:miss 53@237951135009:miss 56@237951135009:miss 67@237951250893:miss 70@237951250893:miss 73@237951251226:miss 76@237951251226:miss 79@237951251226:miss

90@237951362781:miss 93@237951363114:miss 101@237951556254:miss 104@237951556254:miss 107@237951556587:miss 110@237951615195:miss 117@237951672138:miss 120@237951672138:miss

123@237951672471:miss 126@237951717093:miss 133@237957380757:miss 136@237957381090:miss 173@237965333463:miss 176@237965333796:miss

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（30 条，不折叠）</b></summary>

11@237950941869:mshr_alloc:mshr=2,fill=— 14@237950941869:mshr_merge:mshr=2,fill=— 20@237950942535:mshr_alloc:mshr=4,fill=— 23@237950942535:mshr_merge:mshr=3,fill=—

26@237950942535:mshr_merge:mshr=3,fill=— 29@237950942868:mshr_merge:mshr=4,fill=— 45@237951088056:mshr_alloc:mshr=5,fill=— 48@237951088056:mshr_merge:mshr=5,fill=—

51@237951088389:mshr_alloc:mshr=6,fill=— 54@237951135009:mshr_merge:mshr=6,fill=— 57@237951135009:mshr_merge:mshr=6,fill=— 68@237951250893:mshr_alloc:mshr=7,fill=—

71@237951250893:mshr_merge:mshr=7,fill=— 74@237951251226:mshr_alloc:mshr=8,fill=— 77@237951251226:mshr_merge:mshr=8,fill=— 80@237951251226:mshr_merge:mshr=8,fill=—

91@237951362781:mshr_alloc:mshr=9,fill=— 94@237951363114:mshr_alloc:mshr=10,fill=— 102@237951556254:mshr_alloc:mshr=11,fill=— 105@237951556254:mshr_merge:mshr=11,fill=—

108@237951556587:mshr_alloc:mshr=12,fill=— 111@237951615195:mshr_merge:mshr=12,fill=— 118@237951672138:mshr_alloc:mshr=13,fill=— 121@237951672138:mshr_merge:mshr=13,fill=—

124@237951672471:mshr_alloc:mshr=14,fill=— 127@237951717093:mshr_merge:mshr=14,fill=— 134@237957380757:mshr_alloc:mshr=15,fill=— 137@237957381090:mshr_alloc:mshr=16,fill=—

174@237965333463:mshr_alloc:mshr=17,fill=— 177@237965333796:mshr_alloc:mshr=18,fill=—

</details>

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 22 条；event_id `4294967296`–`4294967317`；tick `237950941869`–`237965333463`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 237950941869 | 301 | 303 | 8→9 | 0x40000081d75000+1000 |
| 4294967297 | 237950941869 | 301 | 304 | 8→12 | 0x40000081d75000+1000 |
| 4294967298 | 237950942535 | 301 | 307 | 17→21 | 0x40000081d75000+1000 |
| 4294967299 | 237950942535 | 301 | 308 | 17→24 | 0x40000081d75000+1000 |
| 4294967300 | 237950942868 | 301 | 310 | 17→27 | 0x40000081d75000+1000 |
| 4294967313 | 237951672138 | 301 | 543 | 31→116 | 0x40000081d75000+1000 |
| 4294967314 | 237951672138 | 301 | 544 | 31→119 | 0x40000081d75000+1000 |
| 4294967315 | 237951717093 | 301 | 556 | 31→125 | 0x40000081d75000+1000 |
| 4294967316 | 237957380757 | 301 | 3967 | 31→132 | 0x40000081d75000+1000 |
| 4294967317 | 237965333463 | 301 | 10975 | 31→172 | 0x40000081d75000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`185`；tick=`238882377168`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`98` tick=`237951472338`（parent=`32`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=39; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 16 events |
| 3_tick_order | PASS | ticks 237950940537..237951472338 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=98 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (16); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T02-F0-W4 and seed1 |
| 12_tier_matches_evidence | PASS | matrix=F0 run.out=CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0 expected_enabled=0 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/prop_evt.txt.gz` | `4fadb9e9fd6768f63b1125f2a9f5eb2c6cb0ca8707092c46424841ce61e0770a` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/chain_report.json` | `e06393ed8010bdc23f473174423ad97101d749aecd9c87c3d1519031b3b45016` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/manifest.json` | `f90691e295fb2369039940878ffa273d79ed39316ecaafffa89461dede282fef` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/run.out` | `2f095e9493fa90a69a9a44128ffa3a349e19460a6ec7fc9eb2e494269221701e` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/run.err` | `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3/T02-F0-W4/seed1/stats.txt` | `d57b9ce5a0be2764e334a82915714ed98801c6a0e7f6744cea79ccc73212b181` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
