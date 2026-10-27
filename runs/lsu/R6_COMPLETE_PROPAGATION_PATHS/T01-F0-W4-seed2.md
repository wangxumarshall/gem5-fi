# T01-F0-W4 seed2 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T01-F0-W4` seed2 中，注入器于 tick=237950233911 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81d75` 改成 `0x800081d75`（VA=`0xffffffc009483eb8`）；故障 PFN 使有效 PA 从 `0x81d75eb8` 变为 `0x800081d75eb8`（祖先中无 `tlb_translate_result`，PA 取自 `tlb_pfn` 的 state_before/state_after），随后沿 TLB 翻译 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=259, tick=237951515628）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T01-F0-W4`
- seed: `2`；sample_run_id: `s2`
- 实验模型: 模型ID=`T01`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `单比特翻转`
- 故障模型: 随机选有效表项的VPN tag翻转1 bit；只在注入后再次命中才计activated。实施细则：每次故障运行只选一个当前有效且可被后续使用的目标，在指定字段内均匀抽取一个 bit 做一次 XOR 翻转；其余字段保持无故障值。保存目标 entry/way、bit 编号、原值和故障值，避免把未使用空项计为有效样本。激活口径：仅当“DTLB中存在有效项”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier: `F0`；effective tier: `F0`；tier enabled: `关闭(0)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- source head: N/A（该 run 的 manifest 无 binary_source_head 字段；manifest.source_head=bc82f29d8f69410461d18c07a1ee9314f18885a5 只是运行时工作树 HEAD，不等同于二进制构建源）
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/prop_evt.txt.gz`
- prop_evt SHA-256: `8c385db13bfc0a717cd55f1d1749a1c0a329d4e34af067ab21c7d752573fd9de`（本次重算值；字节数 15961）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/chain_report.json`
- chain_report SHA-256: `9b3a54333722ad6c39fb1ac643cb24881e2e564d14fcdcc680b455a15cfb595a`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json`（SHA-256 `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/run.out`（SHA-256 `6aa8706817b21539a8c88c9beefc1d62542a40c845a5ad9daee18cb181070505`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/run.err`（SHA-256 `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/stats.txt`（SHA-256 `6eebe8976ef7df1a626234267199bc388d173dbf7041607b76c26a475e15290e`；`board.chaos_armtlb.numFaultsInjected=1`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 428；代表故障 `fault_id=1` 事件数: 428；权威报告 fault 数: 1
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc009483eb8，PFN 0x81d75→0x800081d75，PA 0x81d75eb8→0x800081d75eb8（无 tlb_translate_result，PA 取自 tlb_pfn） → TLB 地址翻译 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81d75` 变成 `800081d75`（mask=0x800000000；PFN 0x81d75→0x800081d75），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950233911`；fault_id=`1`；corr=`origin`；request_id=`—`；dyn_inst_seq=`—`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc009483eb8`
  - 值变化：before=`81d75`→after=`800081d75`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950233911, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb8, old_pfn: 0x81d75, new_pfn: 0x800081d75, FaultType: bit_flip, Mask: 0x800000000`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=150217 eligible=2 injected=1 first_eligible_tick=237950233578 last_eligible_tick=237950233911 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950233911`；fault_id=`1`；corr=`addr_fallback`；request_id=`0`；dyn_inst_seq=`0`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc009483eb8`；PFN=`81d75`→`800081d75`
  - 值变化：before=`81d75`→after=`800081d75`；field=`post_lookup`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=800081d75;ap=0;mtype=2;page_size=1000;pa=800081d75eb8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81d75`→`800081d75`；pa `81d75eb8`→`800081d75eb8`
- **event_id=`2`；parent_event_id=`1`；tick=`237950233911`；fault_id=`1`；corr=`addr_fallback`；request_id=`0`；dyn_inst_seq=`0`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc009483eb8`；PA=`0x800081d75eb8`；PFN=`81d75`→`800081d75`
  - 值变化：before=`81d75`→after=`800081d75`；field=`bit_flip`；state_before=`81d75eb8`；state_after=`800081d75eb8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 为什么把故障传给下一步：该 seed 的祖先里没有 `tlb_translate_result` 事件；原始流事实是 `tlb_pfn` 的 PA 直接进入 L3 请求，故不据未记录事件推断翻译比对结果（不猜测）。

### 第 3 步：进入 Load Queue 或 Store Queue

N/A：该 seed 的代表链在 `parent_event_id` 上从 L2 事件直接进入 L3 的 cache 访问，原始流没有为该请求记录 `lsq_push`/`lq_read`；本文件不推断未记录的结构。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`3`；parent_event_id=`2`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483eb8`；PA=`0x800081d75eb8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`4`；parent_event_id=`3`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x800081d75eb8`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`5`；parent_event_id=`4`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x800081d75eb8`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x800081d75eb8`
- **event_id=`6`；parent_event_id=`5`；tick=`237950235909`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483eb8`；PA=`0x800081d75e80`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`7`；parent_event_id=`6`；tick=`237950235909`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x800081d75e80`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`8`；parent_event_id=`7`；tick=`237950235909`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x800081d75e80`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x800081d75e80`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`60`；parent_event_id=`8`；tick=`237950344134`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x800081d75eb8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`61`；parent_event_id=`60`；tick=`237950344134`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x800081d75eb8`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`259`；parent_event_id=`61`；tick=`237951515628`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`391`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`259`, tick=`237951515628`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 1 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237951515628 ptag=1 reason=errant_commit`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | `inj` | L0 | 1 | origin | — | s2 | 0xffffffc009483eb8 | — | 0x81d75→0x800081d75 | 81d75→800081d75 | 0x800000000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950233911 | `tlb_lookup` | L1 | 1 | addr_fallback | 0 | s2 | 0xffffffc009483eb8 | — | 0x81d75→0x800081d75 | 81d75→800081d75 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→addr_fallback | L1 单元内观察 |
| 3 | 2 | 1 | 237950233911 | `tlb_pfn` | L2 | 1 | addr_fallback | 0 | s2 | 0xffffffc009483eb8 | 0x800081d75eb8 | 0x81d75→0x800081d75 | 81d75→800081d75 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950235576 | `cache_access` | L3 | 1 | addr_fallback | 32 | s2 | 0xffffffc009483eb8 | 0x800081d75eb8 | — | —→— | — | — | — | — | — | 直接 parent（parent=2）；request_id 0→32 | L3 cache 查找 |
| 5 | 4 | 3 | 237950235576 | `cache_return` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x800081d75eb8 | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 hit/miss 决策 |
| 6 | 5 | 4 | 237950235576 | `mshr_alloc` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x800081d75eb8 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=4） | L3 MSHR 分配 |
| 7 | 6 | 5 | 237950235909 | `cache_access` | L3 | 1 | addr_fallback | 32 | s2 | 0xffffffc009483eb8 | 0x800081d75e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 cache 查找 |
| 8 | 7 | 6 | 237950235909 | `cache_return` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x800081d75e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=6） | L3 hit/miss 决策 |
| 9 | 8 | 7 | 237950235909 | `mshr_alloc` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x800081d75e80 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=7） | L3 MSHR 分配 |
| 10 | 60 | 8 | 237950344134 | `resp` | L3 | 1 | addr_fallback | 32 | s2 | 0x800081d75eb8 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 响应返回 |
| 11 | 61 | 60 | 237950344134 | `taint_reg` | L4 | 1 | addr_fallback | 32 | s2 | 0x800081d75eb8 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=60） | L4 污染寄存器 |
| 12 | 259 | 61 | 237951515628 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s2 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=61）；corr addr_fallback→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（12 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **428**；代表故障 `fault_id=1` 的事件数 **428**；进入最终 ancestry 的事件 **12**；未进入最终 ancestry 的同 fault 事件 **416**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `cache_access` | 65 | 9–361 | 237950235909–237965093370 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 65 | 10–362 | 237950235909–237965093370 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 65} | 无（outcome/contained 全空） |
| `consumer` | 65 | 260–374 | 237951515628–237965257206 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `request_fork` | 52 | 4294967296–4294967347 | 237950235909–237965093037 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `resp` | 50 | 62–364 | 237950344467–237965201595 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 50 | 63–366 | 237950344467–237965201595 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `mshr_merge` | 39 | 17–288 | 237950236242–237951760383 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_alloc` | 26 | 11–363 | 237950235909–237965093370 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `lq_complete` | 3 | 257–365 | 237951514629–237965201595 | 计数 + 范围 | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 237950235909 |
| L4 | `taint_reg` | 63 | 237950344467 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=65；event_id 范围 `260`–`374`；tick 范围 `237951515628`–`237965257206`；corr 分布 {'taint_prop': 65}；outcome 分布 {'': 65}；contained 分布 {'': 65}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=50；event_id `63`–`366`；tick `237950344467`–`237965201595`；distinct dyn_inst_seq=50；distinct phys_reg=4；distinct arch_reg=3；corr 分布 {'addr_fallback': 50}；outcome 分布 {'': 50}；contained 分布 {'': 50}；sample_run 分布 {'s2': 50}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 63 | 237950344467 | 62 | 34 | —/— | clean→tainted | addr_fallback |
| 65 | 237950344468 | 64 | 35 | —/— | clean→tainted | addr_fallback |
| 67 | 237950344469 | 66 | 37 | —/— | clean→tainted | addr_fallback |
| 69 | 237950344470 | 68 | 38 | —/— | clean→tainted | addr_fallback |
| 71 | 237950344471 | 70 | 40 | —/— | clean→tainted | addr_fallback |
| 73 | 237950344472 | 72 | 41 | —/— | clean→tainted | addr_fallback |
| 75 | 237950344473 | 74 | 43 | —/— | clean→tainted | addr_fallback |
| 77 | 237950344474 | 76 | 44 | —/— | clean→tainted | addr_fallback |
| 249 | 237951402744 | 248 | 386 | —/— | clean→tainted | addr_fallback |
| 258 | 237951514629 | 257 | 391 | 0/142 | clean→tainted | addr_fallback |
| 274 | 237951708102 | 273 | 496 | —/— | clean→tainted | addr_fallback |
| 276 | 237951708103 | 275 | 497 | —/— | clean→tainted | addr_fallback |
| 290 | 237951823986 | 289 | 543 | —/— | clean→tainted | addr_fallback |
| 292 | 237951823987 | 291 | 544 | —/— | clean→tainted | addr_fallback |
| 301 | 237957518619 | 300 | 3967 | 0/147 | clean→tainted | addr_fallback |
| 366 | 237965201595 | 365 | 10559 | 1/231 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（50 条，不折叠，逐条列出）</b></summary>

63@237950344467(—/—) 65@237950344468(—/—) 67@237950344469(—/—) 69@237950344470(—/—) 71@237950344471(—/—) 73@237950344472(—/—) 75@237950344473(—/—) 77@237950344474(—/—)

94@237950347131(—/—) 96@237950347132(—/—) 98@237950347133(—/—) 100@237950347134(—/—) 102@237950347135(—/—) 104@237950347136(—/—) 106@237950347137(—/—) 108@237950347138(—/—)

140@237950454690(—/—) 142@237950454691(—/—) 144@237950454692(—/—) 146@237950454693(—/—) 148@237950454694(—/—) 150@237950454695(—/—) 152@237950454696(—/—) 154@237950454697(—/—)

156@237950458353(—/—) 158@237950458354(—/—) 160@237950458355(—/—) 162@237950458356(—/—) 191@237951093717(—/—) 193@237951093718(—/—) 195@237951093719(—/—) 197@237951093720(—/—)

199@237951094050(—/—) 201@237951094051(—/—) 203@237951094052(—/—) 220@237951239904(—/—) 222@237951239905(—/—) 224@237951239906(—/—) 226@237951239907(—/—) 243@237951402741(—/—)

245@237951402742(—/—) 247@237951402743(—/—) 249@237951402744(—/—) 258@237951514629(0/142) 274@237951708102(—/—) 276@237951708103(—/—) 290@237951823986(—/—) 292@237951823987(—/—)

301@237957518619(0/147) 366@237965201595(1/231)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（65 条，不折叠）</b></summary>

10@237950235909:miss 13@237950236242:miss 16@237950236242:miss 19@237950236575:miss 22@237950236908:miss 25@237950237241:miss 28@237950237574:miss 31@237950237907:miss

34@237950238240:miss 37@237950238573:miss 40@237950238906:miss 43@237950238906:miss 46@237950239239:miss 49@237950239572:miss 52@237950239905:miss 55@237950240238:miss

58@237950297181:miss 79@237950345799:miss 82@237950346132:miss 85@237950346465:miss 88@237950346465:miss 91@237950346798:miss 110@237950347464:miss 113@237950349129:miss

116@237950349129:miss 119@237950349129:miss 122@237950349129:miss 125@237950349795:miss 128@237950350128:miss 131@237950350128:miss 134@237950350461:miss 137@237950350461:miss

164@237950985159:miss 167@237950985159:miss 170@237950985159:miss 173@237950985159:miss 176@237950985492:miss 179@237950985825:miss 182@237950985825:miss 185@237950985825:miss

188@237950986158:miss 205@237951131346:miss 208@237951131346:miss 211@237951131679:miss 214@237951178299:miss 217@237951178299:miss 228@237951294183:miss 231@237951294183:miss

234@237951294516:miss 237@237951294516:miss 240@237951294516:miss 251@237951406071:miss 254@237951406404:miss 262@237951599544:miss 265@237951599544:miss 268@237951599877:miss

271@237951658485:miss 278@237951715428:miss 281@237951715428:miss 284@237951715761:miss 287@237951760383:miss 294@237957410061:miss 297@237957410394:miss 359@237965093037:miss

362@237965093370:miss

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（65 条，不折叠）</b></summary>

11@237950235909:mshr_alloc:mshr=3,fill=— 14@237950236242:mshr_alloc:mshr=4,fill=— 17@237950236242:mshr_merge:mshr=4,fill=— 20@237950236575:mshr_merge:mshr=4,fill=—

23@237950236908:mshr_merge:mshr=4,fill=— 26@237950237241:mshr_merge:mshr=4,fill=— 29@237950237574:mshr_merge:mshr=4,fill=— 32@237950237907:mshr_merge:mshr=4,fill=—

35@237950238240:mshr_merge:mshr=4,fill=— 38@237950238573:mshr_alloc:mshr=5,fill=— 41@237950238906:mshr_alloc:mshr=6,fill=— 44@237950238906:mshr_merge:mshr=6,fill=—

47@237950239239:mshr_merge:mshr=6,fill=— 50@237950239572:mshr_merge:mshr=6,fill=— 53@237950239905:mshr_merge:mshr=6,fill=— 56@237950240238:mshr_merge:mshr=6,fill=—

59@237950297181:mshr_merge:mshr=6,fill=— 80@237950345799:mshr_merge:mshr=6,fill=— 83@237950346132:mshr_alloc:mshr=7,fill=— 86@237950346465:mshr_alloc:mshr=8,fill=—

89@237950346465:mshr_merge:mshr=8,fill=— 92@237950346798:mshr_merge:mshr=8,fill=— 111@237950347464:mshr_merge:mshr=8,fill=— 114@237950349129:mshr_merge:mshr=8,fill=—

117@237950349129:mshr_merge:mshr=8,fill=— 120@237950349129:mshr_merge:mshr=8,fill=— 123@237950349129:mshr_merge:mshr=8,fill=— 126@237950349795:mshr_alloc:mshr=9,fill=—

129@237950350128:mshr_alloc:mshr=10,fill=— 132@237950350128:mshr_merge:mshr=10,fill=— 135@237950350461:mshr_merge:mshr=10,fill=— 138@237950350461:mshr_merge:mshr=10,fill=—

165@237950985159:mshr_alloc:mshr=11,fill=— 168@237950985159:mshr_merge:mshr=11,fill=— 171@237950985159:mshr_alloc:mshr=12,fill=— 174@237950985159:mshr_merge:mshr=12,fill=—

177@237950985492:mshr_alloc:mshr=13,fill=— 180@237950985825:mshr_alloc:mshr=14,fill=— 183@237950985825:mshr_merge:mshr=13,fill=— 186@237950985825:mshr_merge:mshr=13,fill=—

189@237950986158:mshr_merge:mshr=14,fill=— 206@237951131346:mshr_alloc:mshr=15,fill=— 209@237951131346:mshr_merge:mshr=15,fill=— 212@237951131679:mshr_alloc:mshr=16,fill=—

215@237951178299:mshr_merge:mshr=16,fill=— 218@237951178299:mshr_merge:mshr=16,fill=— 229@237951294183:mshr_alloc:mshr=17,fill=— 232@237951294183:mshr_merge:mshr=17,fill=—

235@237951294516:mshr_alloc:mshr=18,fill=— 238@237951294516:mshr_merge:mshr=18,fill=— 241@237951294516:mshr_merge:mshr=18,fill=— 252@237951406071:mshr_alloc:mshr=19,fill=—

255@237951406404:mshr_alloc:mshr=20,fill=— 263@237951599544:mshr_alloc:mshr=21,fill=— 266@237951599544:mshr_merge:mshr=21,fill=— 269@237951599877:mshr_alloc:mshr=22,fill=—

272@237951658485:mshr_merge:mshr=22,fill=— 279@237951715428:mshr_alloc:mshr=23,fill=— 282@237951715428:mshr_merge:mshr=23,fill=— 285@237951715761:mshr_alloc:mshr=24,fill=—

288@237951760383:mshr_merge:mshr=24,fill=— 295@237957410061:mshr_alloc:mshr=25,fill=— 298@237957410394:mshr_alloc:mshr=26,fill=— 360@237965093037:mshr_alloc:mshr=27,fill=—

363@237965093370:mshr_alloc:mshr=28,fill=—

</details>

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 52 条；event_id `4294967296`–`4294967347`；tick `237950235909`–`237965093037`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 237950235909 | 32 | 34 | 8→9 | 0x800081d75000+1000 |
| 4294967297 | 237950236242 | 32 | 35 | 8→15 | 0x800081d75000+1000 |
| 4294967298 | 237950236575 | 32 | 37 | 8→18 | 0x800081d75000+1000 |
| 4294967299 | 237950236908 | 32 | 38 | 8→21 | 0x800081d75000+1000 |
| 4294967300 | 237950237241 | 32 | 40 | 8→24 | 0x800081d75000+1000 |
| 4294967343 | 237951715428 | 32 | 543 | 61→277 | 0x800081d75000+1000 |
| 4294967344 | 237951715428 | 32 | 544 | 61→280 | 0x800081d75000+1000 |
| 4294967345 | 237951760383 | 32 | 556 | 61→286 | 0x800081d75000+1000 |
| 4294967346 | 237957410061 | 32 | 3967 | 61→293 | 0x800081d75000+1000 |
| 4294967347 | 237965093037 | 32 | 10559 | 61→358 | 0x800081d75000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`375`；tick=`238882276602`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`259` tick=`237951515628`（parent=`61`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=65; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 12 events |
| 3_tick_order | PASS | ticks 237950233911..237951515628 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=259 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (12); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T01-F0-W4 and seed2 |
| 12_tier_matches_evidence | PASS | matrix=F0 run.out=CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0 expected_enabled=0 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/prop_evt.txt.gz` | `8c385db13bfc0a717cd55f1d1749a1c0a329d4e34af067ab21c7d752573fd9de` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/chain_report.json` | `9b3a54333722ad6c39fb1ac643cb24881e2e564d14fcdcc680b455a15cfb595a` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` | `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/run.out` | `6aa8706817b21539a8c88c9beefc1d62542a40c845a5ad9daee18cb181070505` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/run.err` | `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed2/stats.txt` | `6eebe8976ef7df1a626234267199bc388d173dbf7041607b76c26a475e15290e` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
