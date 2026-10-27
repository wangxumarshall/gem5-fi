# T03-F5-W9 seed2 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T03-F5-W9` seed2 中，注入器于 tick=237950233578 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81d75` 改成 `0x81d77`（VA=`0xffffffc009483eb0`）；故障 PFN 使有效 PA 从 `0x81d75eb0` 变为 `0x81d77eb0`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=293, tick=237951302175）在 L5 形成真实错误提交；运行结局 Timeout（受控 Timeout（TIMEOUT triggered=True graceful=True signal=None exit=0 (budget 5400s exhausted; child finalized on SIGINT — evidence complete)））。

## 实验身份与证据来源

- RunID: `T03-F5-W9`
- seed: `2`；sample_run_id: `s2`
- 实验模型: 模型ID=`T03`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `卡死`
- 故障模型: 选PPN某bit stuck-at-0/1，对每次TLB读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F5` — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier: `F5`；effective tier: `F5`；tier enabled: `开启(1)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: GAP/Graph500 子集（BFS、SSSP、PageRank，固定图与结果哈希）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- **差异说明（不推断）**: 矩阵标签为 `GAP/Graph500 子集（BFS、SSSP、PageRank，固定图与结果哈希）`，但该 seed 的原始 `run.out` 命令行 `--readfile` 指向 `tlb_probe.rcS`；本文件以原始证据为准，同时保留矩阵标签，二者不一致处如实标注。
- source head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/prop_evt.txt.gz`
- prop_evt SHA-256: `11b38ce82e052647e198a9cf276d9607325b4d7989d50d4094c6c83e63497eec`（本次重算值；字节数 1031384）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/chain_report.json`
- chain_report SHA-256: `a00d7138dd203c4ddebf11eb79e426707b33550fc716374f962726fabd98b7d9`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/manifest.json`（SHA-256 `235af047536bc72ad7360fbf7b3c815f8adcbe9d86f5362c80ce0f16dd18ae6b`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/run.out`（SHA-256 `3b67d30eb5549aa30d2a24309a5866603cd53d6658d60d1a8a090db7064d5a9b`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/run.err`（SHA-256 `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/stats.txt`（SHA-256 `fc48a9ef784db977225eda2193dc363b50c3ebc71374a260b7387c74c4d10deb`；`board.chaos_armtlb.numFaultsInjected=14`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 28281；代表故障 `fault_id=1` 事件数: 400；权威报告 fault 数: 14
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc009483eb0，PFN 0x81d75→0x81d77，PA 0x81d75eb0→0x81d77eb0 → TLB 地址翻译 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → 受控 Timeout（预算耗尽）`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `stuck_at_one` 从 `81d75` 变成 `81d77`（mask=0x2；PFN 0x81d75→0x81d77），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950233578`；fault_id=`1`；corr=`origin`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc009483eb0`
  - 值变化：before=`81d75`→after=`81d77`；field=`stuck_at_one`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950233578, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb0, old_pfn: 0x81d75, new_pfn: 0x81d77, FaultType: stuck_at_one, Mask: 0x2, effective: 1`
  - **F5 掩码锁定说明（permanent）**：F5 是 warm-up 后第一个 eligible event 起持续到运行结束的永久模型；本 seed 全程只锁存一个掩码 `0x2`（14 条命中注入行的 Mask 全部相同：['0x2']），此后每次 TLB 读出都施加同一掩码。
  - **`no_effect` 只聚合、不逐条记录**：未改变目标值的 fires 不写入 `prop_evt` 事件流，也不逐条写入 `armtlb_injections.log`；它们由 run.out 的 `CHAOS_LSU_NOEFFECT` 行聚合计数：`CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F5 requested=F5 effective=F5 attempted=298652463 eligible=298652463 fires=298652463 effective_injected=14 no_effect=298652449 first_no_effect_tick=237950233911 last_no_effect_tick=398895367671`。
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=298652463 eligible=298652463 injected=14 first_eligible_tick=237950233578 last_eligible_tick=398895367671 fires=298652463 no_effect=298652449 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950233578`；fault_id=`1`；corr=`seq_primary`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc009483eb0`；PFN=`81d75`→`81d77`
  - 值变化：before=`81d75`→after=`81d77`；field=`post_lookup`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d77;ap=0;mtype=2;page_size=1000;pa=81d77eb0`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81d75`→`81d77`；pa `81d75eb0`→`81d77eb0`
- **event_id=`2`；parent_event_id=`1`；tick=`237950233578`；fault_id=`1`；corr=`seq_primary`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d77eb0`；PFN=`81d75`→`81d77`
  - 值变化：before=`81d75`→after=`81d77`；field=`stuck_at_one`；state_before=`81d75eb0`；state_after=`81d77eb0`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`237950233578`；fault_id=`1`；corr=`seq_primary`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d77eb0`
  - 值变化：before=`81d75eb0`→after=`81d77eb0`；field=`effective_pa_changed`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d77;ap=0;mtype=2;page_size=1000;pa=81d77eb0`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`81d75eb0`，effective=`81d77eb0`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`4`；parent_event_id=`3`；tick=`237950233911`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`31`**
  - 硬件结构/事件：该访存指令进入 LQ（load）或 SQ（store）结构，携带被污染的地址。
  - 地址/身份：VA=`0xffffffc009483eb0`；lq_idx=`-1`；sq_idx=`1`
  - 值变化：field=`store`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`5`；parent_event_id=`4`；tick=`237950233911`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`31`**
  - 硬件结构/事件：store 在 LSU 发射，使用被污染的地址。
  - 地址/身份：VA=`0xffffffc009483eb0`；sq_idx=`1`
  - 值变化：state_before=`issued`；state_after=`—`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`7`；parent_event_id=`6`；tick=`237950235243`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d77eb0`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`8`；parent_event_id=`7`；tick=`237950235243`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x81d77eb0`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`9`；parent_event_id=`8`；tick=`237950235243`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x81d77eb0`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x81d77eb0`
- **event_id=`10`；parent_event_id=`9`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d77e80`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`11`；parent_event_id=`10`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x81d77e80`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`12`；parent_event_id=`11`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x81d77e80`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81d77e80`
- **event_id=`64`；parent_event_id=`12`；tick=`237950294517`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x81d77e80`；mshr_id=`2`；fill_id=`1`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81d77e80`；fill_id=`1`
- **event_id=`65`；parent_event_id=`64`；tick=`237950294517`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x81d77e80`；cache_line=`0x81d77e80`；fill_id=`1`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`66`；parent_event_id=`65`；tick=`237950294517`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x81d77e80`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81d77e80`
- **event_id=`67`；parent_event_id=`66`；tick=`237950295183`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x81d77e80`；mshr_id=`0`；fill_id=`2`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x81d77e80`；fill_id=`2`
- **event_id=`68`；parent_event_id=`67`；tick=`237950295183`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x81d77e80`；cache_line=`0x81d77e80`；fill_id=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`69`；parent_event_id=`68`；tick=`237950295183`；fault_id=`1`；corr=`addr_fallback`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x81d77e80`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x81d77e80`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`6`；parent_event_id=`5`；tick=`237950235243`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`31`**
  - 硬件结构/事件：store 数据/地址写回存储子系统，错误 PA 随之进入 cache 侧。
  - 地址/身份：PA=`0x81d77eb0`；sq_idx=`1`
  - 值变化：state_before=`—`；state_after=`packet_built`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`73`；parent_event_id=`69`；tick=`237950295516`；fault_id=`1`；corr=`seq_primary`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x81d77eb0`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`74`；parent_event_id=`73`；tick=`237950295516`；fault_id=`1`；corr=`seq_primary`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x81d77eb0`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
- **event_id=`75`；parent_event_id=`74`；tick=`237950295516`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`31`**
  - 硬件结构/事件：store 在 SQ 中完成（错误副作用已发生或已被约束）。
  - 地址/身份：VA=`0xffffffc009483eb0`；sq_idx=`1`
  - 值变化：state_before=`—`；state_after=`completed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`293`；parent_event_id=`75`；tick=`237951302175`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`391`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`293`, tick=`237951302175`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Timeout`；实际表现：受控 Timeout（TIMEOUT triggered=True graceful=True signal=None exit=0 (budget 5400s exhausted; child finalized on SIGINT — evidence complete)）。

run.out 的 CHAOS_DETECT 行（共 39 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951547263 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237952468008 ptag=2 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237954443031 ptag=2 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237954458016 ptag=2 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237954462345 ptag=2 reason=squash_replay`
- …其余 33 行见原始 `run.out`

说明：受控 Timeout（预算耗尽、graceful）是**运行级**结局；代表链的真实 L5 逃逸（若 terminal=`full`）已经发生，不因 Timeout 抹去；两者并列保留。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | `inj` | L0 | 1 | origin | 31 | s2 | 0xffffffc009483eb0 | — | 0x81d75→0x81d77 | 81d75→81d77 | 0x2 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950233578 | `tlb_lookup` | L1 | 1 | seq_primary | 31 | s2 | 0xffffffc009483eb0 | — | 0x81d75→0x81d77 | 81d75→81d77 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 237950233578 | `tlb_pfn` | L2 | 1 | seq_primary | 31 | s2 | 0xffffffc009483eb0 | 0x81d77eb0 | 0x81d75→0x81d77 | 81d75→81d77 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950233578 | `tlb_translate_result` | L2 | 1 | seq_primary | 31 | s2 | 0xffffffc009483eb0 | 0x81d77eb0 | — | 81d75eb0→81d77eb0 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 237950233911 | `lsq_push` | L3 | 1 | seq_primary | — | s2 | 0xffffffc009483eb0 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 进入 LQ/SQ |
| 6 | 5 | 4 | 237950233911 | `sq_execute` | L3 | 1 | seq_primary | — | s2 | 0xffffffc009483eb0 | — | — | issued→— | — | — | — | — | — | 直接 parent（parent=4） | L3 store 发射 |
| 7 | 6 | 5 | 237950235243 | `sq_writeback` | L3 | 1 | seq_primary | — | s2 | — | 0x81d77eb0 | — | —→packet_built | — | — | — | — | — | 直接 parent（parent=5） | L3 store 写回 |
| 8 | 7 | 6 | 237950235243 | `cache_access` | L3 | 1 | addr_fallback | 31 | s2 | 0xffffffc009483eb0 | 0x81d77eb0 | — | —→— | — | — | — | — | — | 直接 parent（parent=6）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 9 | 8 | 7 | 237950235243 | `cache_return` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77eb0 | — | —→— | — | — | — | — | — | 直接 parent（parent=7） | L3 hit/miss 决策 |
| 10 | 9 | 8 | 237950235243 | `mshr_alloc` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77eb0 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=8） | L3 MSHR 分配 |
| 11 | 10 | 9 | 237950235576 | `cache_access` | L3 | 1 | addr_fallback | 31 | s2 | 0xffffffc009483eb0 | 0x81d77e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=9） | L3 cache 查找 |
| 12 | 11 | 10 | 237950235576 | `cache_return` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=10） | L3 hit/miss 决策 |
| 13 | 12 | 11 | 237950235576 | `mshr_alloc` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=11） | L3 MSHR 分配 |
| 14 | 64 | 12 | 237950294517 | `mshr_fill` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→filled | — | — | — | — | — | 直接 parent（parent=12） | L3 MSHR 填充 |
| 15 | 65 | 64 | 237950294517 | `cache_fill` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=64） | L3 行填充 |
| 16 | 66 | 65 | 237950294517 | `mshr_free` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=65） | L3 MSHR 释放 |
| 17 | 67 | 66 | 237950295183 | `mshr_fill` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→filled | — | — | — | — | — | 直接 parent（parent=66） | L3 MSHR 填充 |
| 18 | 68 | 67 | 237950295183 | `cache_fill` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=67） | L3 行填充 |
| 19 | 69 | 68 | 237950295183 | `mshr_free` | L3 | 1 | addr_fallback | 31 | s2 | — | 0x81d77e80 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=68） | L3 MSHR 释放 |
| 20 | 73 | 69 | 237950295516 | `resp` | L3 | 1 | seq_primary | 31 | s2 | 0x81d77eb0 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=69）；corr addr_fallback→seq_primary | L3 响应返回 |
| 21 | 74 | 73 | 237950295516 | `taint_reg` | L4 | 1 | seq_primary | 31 | s2 | 0x81d77eb0 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=73） | L4 污染寄存器 |
| 22 | 75 | 74 | 237950295516 | `sq_complete` | L3 | 1 | seq_primary | — | s2 | 0xffffffc009483eb0 | — | — | —→completed | — | — | — | — | — | 直接 parent（parent=74） | L3 store 完成 |
| 23 | 293 | 75 | 237951302175 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s2 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=75）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（23 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **28281**；代表故障 `fault_id=1` 的事件数 **400**；进入最终 ancestry 的事件 **23**；未进入最终 ancestry 的同 fault 事件 **377**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `cache_access` | 64 | 13–10001 | 237950235576–237963702429 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 64 | 14–10002 | 237950235576–237963702429 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 42, 'hit': 22} | 无（outcome/contained 全空） |
| `request_fork` | 51 | 4294967296–4294967346 | 237950235576–237951546930 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `taint_reg` | 51 | 80–316 | 237950296182–237951502309 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `resp` | 50 | 79–315 | 237950296182–237951502309 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_merge` | 30 | 15–273 | 237950235576–237951251226 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_alloc` | 12 | 18–267 | 237950235909–237951251226 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_fill` | 12 | 70–277 | 237950295183–237951296514 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_fill` | 12 | 71–278 | 237950295183–237951296514 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_free` | 12 | 72–279 | 237950295183–237951296514 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_evict` | 7 | 7592–9999 | 237960515619–237963702096 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_writeback` | 7 | 7593–10000 | 237960515619–237963702096 | 计数 + 范围 | 无（outcome/contained 全空） |
| `lq_complete` | 2 | 291–306 | 237951301176–237951445365 | 计数 + 范围 | 无（outcome/contained 全空） |
| `consumer` | 1 | 294–294 | 237951302175–237951302175 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `squash_masked` | 1 | 319–319 | 237951547263–237951547263 | 不折叠：全部逐条点名（见下） | 预期非空（检测/含住事件）：outcome={'masked': 1} contained={'1': 1} |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 237950235576 |
| L4 | `taint_reg` | 80 | 237950296182 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=1；event_id 范围 `294`–`294`；tick 范围 `237951302175`–`237951302175`；corr 分布 {'taint_prop': 1}；outcome 分布 {'': 1}；contained 分布 {'': 1}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=51；event_id `80`–`316`；tick `237950296182`–`237951502309`；distinct dyn_inst_seq=50；distinct phys_reg=4；distinct arch_reg=4；corr 分布 {'addr_fallback': 51}；outcome 分布 {'': 51}；contained 分布 {'': 51}；sample_run 分布 {'s2': 51}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 80 | 237950296182 | 79 | 32 | —/— | clean→tainted | addr_fallback |
| 82 | 237950296515 | 81 | 34 | —/— | clean→tainted | addr_fallback |
| 84 | 237950297181 | 83 | 35 | —/— | clean→tainted | addr_fallback |
| 89 | 237950297182 | 88 | 37 | —/— | clean→tainted | addr_fallback |
| 91 | 237950297183 | 90 | 38 | —/— | clean→tainted | addr_fallback |
| 93 | 237950297184 | 92 | 40 | —/— | clean→tainted | addr_fallback |
| 95 | 237950297185 | 94 | 41 | —/— | clean→tainted | addr_fallback |
| 97 | 237950297186 | 96 | 43 | —/— | clean→tainted | addr_fallback |
| 287 | 237951297515 | 286 | 386 | —/— | clean→tainted | addr_fallback |
| 292 | 237951301176 | 291 | 391 | 0/142 | clean→tainted | addr_fallback |
| 300 | 237951386424 | 299 | 460 | —/— | clean→tainted | addr_fallback |
| 302 | 237951386425 | 301 | 461 | —/— | clean→tainted | addr_fallback |
| 307 | 237951445365 | 306 | 474 | 29/158 | clean→tainted | addr_fallback |
| 308 | 237951445365 | 307 | 474 | 30/159 | clean→tainted | addr_fallback |
| 314 | 237951502308 | 313 | 507 | —/— | clean→tainted | addr_fallback |
| 316 | 237951502309 | 315 | 508 | —/— | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（51 条，不折叠，逐条列出）</b></summary>

80@237950296182(—/—) 82@237950296515(—/—) 84@237950297181(—/—) 89@237950297182(—/—) 91@237950297183(—/—) 93@237950297184(—/—) 95@237950297185(—/—) 97@237950297186(—/—)

99@237950297187(—/—) 125@237950300511(—/—) 127@237950301177(—/—) 129@237950301178(—/—) 131@237950301179(—/—) 133@237950301180(—/—) 135@237950301181(—/—) 137@237950301182(—/—)

139@237950301183(—/—) 174@237950344134(—/—) 176@237950344800(—/—) 178@237950344801(—/—) 180@237950344802(—/—) 182@237950344803(—/—) 184@237950344804(—/—) 186@237950344805(—/—)

188@237950344806(—/—) 196@237950348463(—/—) 198@237950349129(—/—) 200@237950349130(—/—) 202@237950349131(—/—) 217@237950942202(—/—) 219@237950942203(—/—) 225@237950942868(—/—)

230@237950942869(—/—) 238@237950987823(—/—) 240@237950988489(—/—) 242@237950988490(—/—) 248@237951088389(—/—) 250@237951088390(—/—) 256@237951135342(—/—) 258@237951135343(—/—)

281@237951296847(—/—) 283@237951297513(—/—) 285@237951297514(—/—) 287@237951297515(—/—) 292@237951301176(0/142) 300@237951386424(—/—) 302@237951386425(—/—) 307@237951445365(29/158)

308@237951445365(30/159) 314@237951502308(—/—) 316@237951502309(—/—)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（64 条，不折叠）</b></summary>

14@237950235576:miss 17@237950235909:miss 20@237950236242:miss 23@237950236242:miss 26@237950236575:miss 29@237950236908:miss 32@237950237241:miss 35@237950237574:miss

38@237950237907:miss 41@237950238240:miss 44@237950238573:miss 47@237950238906:miss 50@237950238906:miss 53@237950239239:miss 56@237950239572:miss 59@237950239905:miss

62@237950240238:miss 86@237950297181:miss 101@237950297847:miss 104@237950298180:miss 107@237950298513:miss 110@237950298846:miss 113@237950299179:miss 122@237950300178:miss

141@237950301843:miss 144@237950301843:miss 147@237950301843:miss 150@237950301843:miss 153@237950302509:miss 156@237950302842:miss 159@237950302842:miss 162@237950303175:miss

165@237950303175:miss 204@237950941869:hit 206@237950941869:hit 208@237950941869:miss 211@237950941869:miss 214@237950942202:miss 221@237950942535:hit 223@237950942535:hit

227@237950942868:miss 244@237951088056:hit 246@237951088056:hit 252@237951135009:hit 254@237951135009:hit 260@237951250893:miss 263@237951250893:miss 266@237951251226:miss

269@237951251226:miss 272@237951251226:miss 289@237951300843:hit 296@237951386091:hit 298@237951386091:hit 304@237951445032:hit 310@237951501975:hit 312@237951501975:hit

318@237951546930:hit 7595@237960515952:hit 9555@237961975824:hit 9559@237962083050:hit 9563@237962087046:hit 9980@237963652812:hit 9998@237963697434:hit 10002@237963702429:hit

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（66 条，不折叠）</b></summary>

15@237950235576:mshr_merge:mshr=2,fill=— 18@237950235909:mshr_alloc:mshr=3,fill=— 21@237950236242:mshr_alloc:mshr=4,fill=— 24@237950236242:mshr_merge:mshr=4,fill=—

27@237950236575:mshr_merge:mshr=4,fill=— 30@237950236908:mshr_merge:mshr=4,fill=— 33@237950237241:mshr_merge:mshr=4,fill=— 36@237950237574:mshr_merge:mshr=4,fill=—

39@237950237907:mshr_merge:mshr=4,fill=— 42@237950238240:mshr_merge:mshr=4,fill=— 45@237950238573:mshr_alloc:mshr=5,fill=— 48@237950238906:mshr_alloc:mshr=6,fill=—

51@237950238906:mshr_merge:mshr=6,fill=— 54@237950239239:mshr_merge:mshr=6,fill=— 57@237950239572:mshr_merge:mshr=6,fill=— 60@237950239905:mshr_merge:mshr=6,fill=—

63@237950240238:mshr_merge:mshr=6,fill=— 70@237950295183:mshr_fill:mshr=4,fill=3 72@237950295183:mshr_free:mshr=4,fill=— 76@237950296182:mshr_fill:mshr=0,fill=4

78@237950296182:mshr_free:mshr=0,fill=— 87@237950297181:mshr_merge:mshr=6,fill=— 102@237950297847:mshr_merge:mshr=6,fill=— 105@237950298180:mshr_alloc:mshr=7,fill=—

108@237950298513:mshr_alloc:mshr=8,fill=— 111@237950298846:mshr_merge:mshr=8,fill=— 114@237950299179:mshr_merge:mshr=8,fill=— 115@237950299512:mshr_fill:mshr=6,fill=5

117@237950299512:mshr_free:mshr=6,fill=— 118@237950300178:mshr_fill:mshr=0,fill=6 120@237950300178:mshr_free:mshr=0,fill=— 123@237950300178:mshr_merge:mshr=8,fill=—

142@237950301843:mshr_merge:mshr=8,fill=— 145@237950301843:mshr_merge:mshr=8,fill=— 148@237950301843:mshr_merge:mshr=8,fill=— 151@237950301843:mshr_merge:mshr=8,fill=—

154@237950302509:mshr_alloc:mshr=9,fill=— 157@237950302842:mshr_alloc:mshr=10,fill=— 160@237950302842:mshr_merge:mshr=10,fill=— 163@237950303175:mshr_merge:mshr=10,fill=—

166@237950303175:mshr_merge:mshr=10,fill=— 167@237950343135:mshr_fill:mshr=8,fill=7 169@237950343135:mshr_free:mshr=8,fill=— 170@237950343801:mshr_fill:mshr=0,fill=8

172@237950343801:mshr_free:mshr=0,fill=— 189@237950347464:mshr_fill:mshr=10,fill=9 191@237950347464:mshr_free:mshr=10,fill=— 192@237950348130:mshr_fill:mshr=0,fill=10

194@237950348130:mshr_free:mshr=0,fill=— 209@237950941869:mshr_alloc:mshr=11,fill=— 212@237950941869:mshr_merge:mshr=11,fill=— 215@237950942202:mshr_alloc:mshr=12,fill=—

228@237950942868:mshr_merge:mshr=12,fill=— 231@237950986824:mshr_fill:mshr=12,fill=11 233@237950986824:mshr_free:mshr=12,fill=— 234@237950987490:mshr_fill:mshr=0,fill=12

236@237950987490:mshr_free:mshr=0,fill=— 261@237951250893:mshr_alloc:mshr=13,fill=— 264@237951250893:mshr_merge:mshr=13,fill=— 267@237951251226:mshr_alloc:mshr=14,fill=—

270@237951251226:mshr_merge:mshr=14,fill=— 273@237951251226:mshr_merge:mshr=14,fill=— 274@237951295848:mshr_fill:mshr=14,fill=13 276@237951295848:mshr_free:mshr=14,fill=—

277@237951296514:mshr_fill:mshr=0,fill=14 279@237951296514:mshr_free:mshr=0,fill=—

</details>

**`squash_masked` 旁支（不折叠，全部点名）**：共 1 条，均为同一 fault 的 L4 contain-by-squash 见证；只有主链上的那一条（若 terminal 为 L4 含住）或权威报告 containment.metrics 指定的一条是终局见证。

| event_id | tick | parent | VA | PA | dyn_inst_seq | containment_reason |
|---|---|---|---|---|---|---|
| 319 | 237951547263 | 294 | 0xffffffc009483e40 | 0x81d77e40 | 520 | squash_replay |

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 51 条；event_id `4294967296`–`4294967346`；tick `237950235576`–`237951546930`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 237950235576 | 31 | 32 | 12→13 | 0x81d77000+1000 |
| 4294967297 | 237950235909 | 31 | 34 | 12→16 | 0x81d77000+1000 |
| 4294967298 | 237950236242 | 31 | 35 | 12→22 | 0x81d77000+1000 |
| 4294967299 | 237950236575 | 31 | 37 | 12→25 | 0x81d77000+1000 |
| 4294967300 | 237950236908 | 31 | 38 | 12→28 | 0x81d77000+1000 |
| 4294967342 | 237951386091 | 31 | 461 | 74→297 | 0x81d77000+1000 |
| 4294967343 | 237951445032 | 31 | 474 | 74→303 | 0x81d77000+1000 |
| 4294967344 | 237951501975 | 31 | 507 | 74→309 | 0x81d77000+1000 |
| 4294967345 | 237951501975 | 31 | 508 | 74→311 | 0x81d77000+1000 |
| 4294967346 | 237951546930 | 31 | 520 | 74→317 | 0x81d77000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`23984`；tick=`398895368670`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 14 个 fault；本文件的代表故障 `fault_id=1` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'full': 1, 'detected_contained': 2, 'provable_to_L4_then_unknown': 10, 'provable_to_L3_then_unknown': 1}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1（代表） | full | L5 | 400 |
| 2 | detected_contained | L5 | 4903 |
| 3 | provable_to_L4_then_unknown | L4 | 32 |
| 4 | provable_to_L4_then_unknown | L4 | 919 |
| 5 | provable_to_L4_then_unknown | L4 | 1323 |
| 6 | provable_to_L4_then_unknown | L4 | 1813 |
| 7 | provable_to_L3_then_unknown | L3 | 70 |
| 8 | provable_to_L4_then_unknown | L4 | 1311 |
| 9 | provable_to_L4_then_unknown | L4 | 619 |
| 10 | provable_to_L4_then_unknown | L4 | 1730 |
| 11 | detected_contained | L5 | 454 |
| 12 | provable_to_L4_then_unknown | L4 | 238 |
| 13 | provable_to_L4_then_unknown | L4 | 3606 |
| 14 | provable_to_L4_then_unknown | L4 | 10863 |

**为什么主链选的是 L5 逃逸而不是这些 L4 含住旁支**：本 seed 的权威判定采用 escape-first 规则——只要**任一** fault 到达 `full`（真实 errant_commit 逃逸），样本 headline 就是 `full`；squash 类含住证据在同一链上存在可证 L0→L5 逃逸路径时必须让位（`errant_escape_outranks_containment`）。这些旁支 `squash_masked` 是同一故障的其它 load 实例，不改变代表故障的逃逸终局。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`293` tick=`237951302175`（parent=`75`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=76; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 23 events |
| 3_tick_order | PASS | ticks 237950233578..237951302175 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 51 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=293 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (23); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T03-F5-W9 and seed2 |
| 12_tier_matches_evidence | PASS | matrix=F5 run.out=CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/prop_evt.txt.gz` | `11b38ce82e052647e198a9cf276d9607325b4d7989d50d4094c6c83e63497eec` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/chain_report.json` | `a00d7138dd203c4ddebf11eb79e426707b33550fc716374f962726fabd98b7d9` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/manifest.json` | `235af047536bc72ad7360fbf7b3c815f8adcbe9d86f5362c80ce0f16dd18ae6b` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/run.out` | `3b67d30eb5549aa30d2a24309a5866603cd53d6658d60d1a8a090db7064d5a9b` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s2/T03-F5-W9/seed2/stats.txt` | `fc48a9ef784db977225eda2193dc363b50c3ebc71374a260b7387c74c4d10deb` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:53:48`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v3.py`（SHA-256 `6bfae052db6e77fe26ee935f7606cf684096bc079d4689e45ac3d870fe90d3fe`）
