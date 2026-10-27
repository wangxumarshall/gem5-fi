# T10-F1-W1 seed2 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T10-F1-W1` seed2 中，注入器于 tick=239345234181 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x8313b` 改成 `0x8313a`（VA=`0x7f82b83d08`）；故障 PFN 使有效 PA 从 `0x8313bd08` 变为 `0x8313ad08`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=20, tick=239345295120）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T10-F1-W1`
- seed: `2`；sample_run_id: `s2`
- 实验模型: 模型ID=`T10`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `单比特翻转`
- 故障模型: 随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；按低/中/高物理地址位分层，VPN、ASID、权限和页大小保持不变。仅当该表项之后被命中且故障 PPN 被用于形成物理地址时计为 activated；保存 entry、bit、原值、故障值和首次消费事务。
- 频率档位: `F1` — 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier: `F1`；effective tier: `F1`；tier enabled: `开启(1)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- **差异说明（不推断）**: 矩阵标签为 MiBench，但该 seed 的原始 `run.out` 命令行 `--readfile` 指向 `tlb_probe.rcS`；本文件以原始证据为准，同时保留矩阵标签，二者不一致处如实标注。
- source head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/prop_evt.txt.gz`
- prop_evt SHA-256: `5680f0a4e26d16433434a5bbc146cd8d073167668a964a8cff97626561cd5c01`（本次重算值；字节数 136919）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/chain_report.json`
- chain_report SHA-256: `214430c01a30fcdcdbbf76f9e0001070c8679aaaa46fb07328dbce98d91d2f75`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/manifest.json`（SHA-256 `069e0cb462608bc0227860deec73e5dac2efba623a414a67a71c581b752287eb`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.out`（SHA-256 `418bc61b8c11c1f018632381ab5870ef795186d8c78cc6b245e20d932ba14939`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.err`（SHA-256 `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/stats.txt`（SHA-256 `652d4f46d0e65b462544ef4892eba6172c0b90970ccfefff8fafadd9a8671e91`；`board.chaos_armtlb.numFaultsInjected=2`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 2279；代表故障 `fault_id=1` 事件数: 370；权威报告 fault 数: 2
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0x7f82b83d08，PFN 0x8313b→0x8313a，PA 0x8313bd08→0x8313ad08 → TLB 地址翻译 → LQ request_id=4338322 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `8313b` 变成 `8313a`（mask=0x1；PFN 0x8313b→0x8313a），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`239345234181`；fault_id=`1`；corr=`origin`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0x7f82b83d08`
  - 值变化：before=`8313b`→after=`8313a`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 239345234181, Site: arm_tlb_lookup_hit, VA: 0x7f82b83d08, old_pfn: 0x8313b, new_pfn: 0x8313a, FaultType: bit_flip, Mask: 0x1, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F1 attempted=1901753 eligible=1901753 injected=2 first_eligible_tick=237950233578 last_eligible_tick=241672555530 fires=n/a no_effect=n/a (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`239345234181`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0x7f82b83d08`；PFN=`8313b`→`8313a`
  - 值变化：before=`8313b`→after=`8313a`；field=`post_lookup`；state_before=`vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08`；state_after=`vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `8313b`→`8313a`；pa `8313bd08`→`8313ad08`
- **event_id=`2`；parent_event_id=`1`；tick=`239345234181`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0x7f82b83d08`；PA=`0x8313ad08`；PFN=`8313b`→`8313a`
  - 值变化：before=`8313b`→after=`8313a`；field=`bit_flip`；state_before=`8313bd08`；state_after=`8313ad08`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`239345234181`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0x7f82b83d08`；PA=`0x8313ad08`
  - 值变化：before=`8313bd08`→after=`8313ad08`；field=`effective_pa_changed`；state_before=`vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313b;ap=3;mtype=2;page_size=1000;pa=8313bd08`；state_after=`vpn=7f82b83;asid=214;valid=1;global=0;pfn=8313a;ap=3;mtype=2;page_size=1000;pa=8313ad08`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`8313bd08`，effective=`8313ad08`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`4`；parent_event_id=`3`；tick=`239345234181`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：LQ 读出该 load 的地址/请求；地址中已包含错误 PFN 带来的错误 PA。
  - 地址/身份：VA=`0x7f82b83d08`；lq_idx=`470727`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`5`；parent_event_id=`4`；tick=`239345234181`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0x7f82b83d08`；PA=`0x8313ad08`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`6`；parent_event_id=`5`；tick=`239345234181`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x8313ad08`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`7`；parent_event_id=`6`；tick=`239345234181`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x8313ad08`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x8313ad08`
- **event_id=`8`；parent_event_id=`7`；tick=`239345234514`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0x7f82b83d08`；PA=`0x8313ad00`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`9`；parent_event_id=`8`；tick=`239345234514`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x8313ad00`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`10`；parent_event_id=`9`；tick=`239345234514`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x8313ad00`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x8313ad00`
- **event_id=`11`；parent_event_id=`10`；tick=`239345293455`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x8313ad00`；mshr_id=`2`；fill_id=`1`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x8313ad00`；fill_id=`1`
- **event_id=`12`；parent_event_id=`11`；tick=`239345293455`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x8313ad00`；cache_line=`0x8313ad00`；fill_id=`1`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`13`；parent_event_id=`12`；tick=`239345293455`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x8313ad00`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x8313ad00`
- **event_id=`14`；parent_event_id=`13`；tick=`239345294121`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x8313ad00`；mshr_id=`0`；fill_id=`2`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x8313ad00`；fill_id=`2`
- **event_id=`15`；parent_event_id=`14`；tick=`239345294121`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x8313ad00`；cache_line=`0x8313ad00`；fill_id=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`16`；parent_event_id=`15`；tick=`239345294121`；fault_id=`1`；corr=`addr_fallback`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x8313ad00`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x8313ad00`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`17`；parent_event_id=`16`；tick=`239345294454`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x8313ad08`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`18`；parent_event_id=`17`；tick=`239345294454`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0x7f82b83d08`；PA=`0x8313ad08`；lq_idx=`470727`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`19`；parent_event_id=`18`；tick=`239345294454`；fault_id=`1`；corr=`seq_primary`；request_id=`4338322`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x8313ad08`；arch_reg=`12`/phys_reg=`110`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`20`；parent_event_id=`19`；tick=`239345295120`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`4338322`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`20`, tick=`239345295120`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 3 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=239345295120 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=239349889521 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=241672555530 ptag=2 reason=store_discarded_not_retired`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239345234181 | `inj` | L0 | 1 | origin | 4338322 | s2 | 0x7f82b83d08 | — | 0x8313b→0x8313a | 8313b→8313a | 0x1 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 239345234181 | `tlb_lookup` | L1 | 1 | seq_primary | 4338322 | s2 | 0x7f82b83d08 | — | 0x8313b→0x8313a | 8313b→8313a | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 239345234181 | `tlb_pfn` | L2 | 1 | seq_primary | 4338322 | s2 | 0x7f82b83d08 | 0x8313ad08 | 0x8313b→0x8313a | 8313b→8313a | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 239345234181 | `tlb_translate_result` | L2 | 1 | seq_primary | 4338322 | s2 | 0x7f82b83d08 | 0x8313ad08 | — | 8313bd08→8313ad08 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 239345234181 | `lq_read` | L3 | 1 | seq_primary | 4338322 | s2 | 0x7f82b83d08 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 读取 load 请求 |
| 6 | 5 | 4 | 239345234181 | `cache_access` | L3 | 1 | addr_fallback | 4338322 | s2 | 0x7f82b83d08 | 0x8313ad08 | — | —→— | — | — | — | — | — | 直接 parent（parent=4）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 7 | 6 | 5 | 239345234181 | `cache_return` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad08 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 hit/miss 决策 |
| 8 | 7 | 6 | 239345234181 | `mshr_alloc` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad08 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=6） | L3 MSHR 分配 |
| 9 | 8 | 7 | 239345234514 | `cache_access` | L3 | 1 | addr_fallback | 4338322 | s2 | 0x7f82b83d08 | 0x8313ad00 | — | —→— | — | — | — | — | — | 直接 parent（parent=7） | L3 cache 查找 |
| 10 | 9 | 8 | 239345234514 | `cache_return` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 hit/miss 决策 |
| 11 | 10 | 9 | 239345234514 | `mshr_alloc` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=9） | L3 MSHR 分配 |
| 12 | 11 | 10 | 239345293455 | `mshr_fill` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→filled | — | — | — | — | — | 直接 parent（parent=10） | L3 MSHR 填充 |
| 13 | 12 | 11 | 239345293455 | `cache_fill` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→— | — | — | — | — | — | 直接 parent（parent=11） | L3 行填充 |
| 14 | 13 | 12 | 239345293455 | `mshr_free` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=12） | L3 MSHR 释放 |
| 15 | 14 | 13 | 239345294121 | `mshr_fill` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→filled | — | — | — | — | — | 直接 parent（parent=13） | L3 MSHR 填充 |
| 16 | 15 | 14 | 239345294121 | `cache_fill` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→— | — | — | — | — | — | 直接 parent（parent=14） | L3 行填充 |
| 17 | 16 | 15 | 239345294121 | `mshr_free` | L3 | 1 | addr_fallback | 4338322 | s2 | — | 0x8313ad00 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=15） | L3 MSHR 释放 |
| 18 | 17 | 16 | 239345294454 | `resp` | L3 | 1 | seq_primary | 4338322 | s2 | 0x8313ad08 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=16）；corr addr_fallback→seq_primary | L3 响应返回 |
| 19 | 18 | 17 | 239345294454 | `lq_complete` | L3 | 1 | seq_primary | 4338322 | s2 | 0x7f82b83d08 | 0x8313ad08 | — | —→— | — | — | — | — | — | 直接 parent（parent=17） | L3 load 完成 |
| 20 | 19 | 18 | 239345294454 | `taint_reg` | L4 | 1 | seq_primary | 4338322 | s2 | 0x8313ad08 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=18） | L4 污染寄存器 |
| 21 | 20 | 19 | 239345295120 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s2 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=19）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（21 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **2279**；代表故障 `fault_id=1` 的事件数 **370**；进入最终 ancestry 的事件 **21**；未进入最终 ancestry 的同 fault 事件 **349**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `cache_access` | 57 | 21–298 | 239345523225–239350590819 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 57 | 22–299 | 239345523225–239350590819 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 2, 'hit': 55} | 无（outcome/contained 全空） |
| `request_fork` | 56 | 4294967296–4294967351 | 239345523225–239350590819 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `resp` | 54 | 26–303 | 239345523558–239350591153 | 计数 + 范围 | 无（outcome/contained 全空） |
| `lq_complete` | 54 | 27–304 | 239345523558–239350591153 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 54 | 28–305 | 239345523558–239350591153 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `consumer` | 7 | 306–312 | 239350606803–239350644432 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `mshr_alloc` | 2 | 23–31 | 239345523225–239345523558 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_fill` | 2 | 32–35 | 239345582499–239345583165 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_fill` | 2 | 33–36 | 239345582499–239345583165 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_free` | 2 | 34–37 | 239345582499–239345583165 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `squash_masked` | 1 | 265–265 | 239349889521–239349889521 | 不折叠：全部逐条点名（见下） | 预期非空（检测/含住事件）：outcome={'masked': 1} contained={'1': 1} |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 239345523225 |
| L4 | `taint_reg` | 28 | 239345523558 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=7；event_id 范围 `306`–`312`；tick 范围 `239350606803`–`239350644432`；corr 分布 {'taint_prop': 7}；outcome 分布 {'': 7}；contained 分布 {'': 7}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=54；event_id `28`–`305`；tick `239345523558`–`239350591153`；distinct dyn_inst_seq=54；distinct phys_reg=48；distinct arch_reg=2；corr 分布 {'addr_fallback': 54}；outcome 分布 {'': 54}；contained 分布 {'': 54}；sample_run 分布 {'s2': 54}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 28 | 239345523558 | 27 | 4339264 | 12/219 | clean→tainted | addr_fallback |
| 40 | 239345583498 | 39 | 4339263 | 7/189 | clean→tainted | addr_fallback |
| 47 | 239345868213 | 46 | 4340744 | 7/46 | clean→tainted | addr_fallback |
| 50 | 239345868214 | 49 | 4340745 | 12/209 | clean→tainted | addr_fallback |
| 57 | 239346021726 | 56 | 4341753 | 7/110 | clean→tainted | addr_fallback |
| 60 | 239346021727 | 59 | 4341754 | 12/16 | clean→tainted | addr_fallback |
| 67 | 239346189558 | 66 | 4343146 | 7/216 | clean→tainted | addr_fallback |
| 70 | 239346189559 | 69 | 4343147 | 12/166 | clean→tainted | addr_fallback |
| 272 | 239349915495 | 271 | 4366472 | 7/113 | clean→tainted | addr_fallback |
| 275 | 239349915496 | 274 | 4366473 | 12/229 | clean→tainted | addr_fallback |
| 282 | 239350126617 | 281 | 4367401 | 7/126 | clean→tainted | addr_fallback |
| 285 | 239350126618 | 284 | 4367402 | 12/157 | clean→tainted | addr_fallback |
| 292 | 239350306770 | 291 | 4368553 | 7/51 | clean→tainted | addr_fallback |
| 295 | 239350306771 | 294 | 4368554 | 12/196 | clean→tainted | addr_fallback |
| 302 | 239350591152 | 301 | 4369828 | 7/4 | clean→tainted | addr_fallback |
| 305 | 239350591153 | 304 | 4369829 | 12/189 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（54 条，不折叠，逐条列出）</b></summary>

28@239345523558(12/219) 40@239345583498(7/189) 47@239345868213(7/46) 50@239345868214(12/209) 57@239346021726(7/110) 60@239346021727(12/16) 67@239346189558(7/216) 70@239346189559(12/166)

77@239346335079(7/82) 80@239346335080(12/67) 87@239346497250(7/202) 90@239346497251(12/215) 95@239346682731(7/148) 100@239346683064(12/130) 107@239346913500(7/243) 110@239346913501(12/7)

117@239347059687(7/245) 120@239347059688(12/201) 127@239347128951(7/209) 130@239347128952(12/221) 137@239347401678(7/170) 140@239347401679(12/213) 147@239347548864(7/138) 150@239347548865(12/234)

157@239347888524(7/210) 160@239347888525(12/230) 167@239348105307(7/77) 170@239348105308(12/226) 177@239348211867(7/98) 180@239348211868(12/209) 187@239348478600(7/225) 190@239348478601(12/128)

197@239348675736(7/3) 200@239348675737(12/174) 207@239348900511(7/217) 210@239348900512(12/148) 217@239349081996(7/107) 220@239349081997(12/59) 227@239349185226(7/184) 230@239349185227(12/172)

237@239349437973(7/35) 240@239349437974(12/226) 247@239349581496(7/108) 250@239349581497(12/219) 257@239349683061(7/44) 260@239349683062(12/171) 272@239349915495(7/113) 275@239349915496(12/229)

282@239350126617(7/126) 285@239350126618(12/157) 292@239350306770(7/51) 295@239350306771(12/196) 302@239350591152(7/4) 305@239350591153(12/189)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（57 条，不折叠）</b></summary>

22@239345523225:miss 25@239345523225:hit 30@239345523558:miss 42@239345867880:hit 44@239345867880:hit 52@239346021393:hit 54@239346021393:hit 62@239346189225:hit

64@239346189225:hit 72@239346334746:hit 74@239346334746:hit 82@239346496917:hit 84@239346496917:hit 92@239346682398:hit 97@239346682731:hit 102@239346913167:hit

104@239346913167:hit 112@239347059354:hit 114@239347059354:hit 122@239347128618:hit 124@239347128618:hit 132@239347401345:hit 134@239347401345:hit 142@239347548531:hit

144@239347548531:hit 152@239347888191:hit 154@239347888191:hit 162@239348104974:hit 164@239348104974:hit 172@239348211534:hit 174@239348211534:hit 182@239348478267:hit

184@239348478267:hit 192@239348675403:hit 194@239348675403:hit 202@239348900178:hit 204@239348900178:hit 212@239349081663:hit 214@239349081663:hit 222@239349184893:hit

224@239349184893:hit 232@239349437640:hit 234@239349437640:hit 242@239349581163:hit 244@239349581163:hit 252@239349682728:hit 254@239349682728:hit 262@239349889188:hit

264@239349889188:hit 267@239349915162:hit 269@239349915162:hit 277@239350126284:hit 279@239350126284:hit 287@239350306437:hit 289@239350306437:hit 297@239350590819:hit

299@239350590819:hit

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（6 条，不折叠）</b></summary>

23@239345523225:mshr_alloc:mshr=3,fill=— 31@239345523558:mshr_alloc:mshr=4,fill=— 32@239345582499:mshr_fill:mshr=4,fill=3 34@239345582499:mshr_free:mshr=4,fill=—

35@239345583165:mshr_fill:mshr=0,fill=4 37@239345583165:mshr_free:mshr=0,fill=—

</details>

**`squash_masked` 旁支（不折叠，全部点名）**：共 1 条，均为同一 fault 的 L4 contain-by-squash 见证；只有主链上的那一条（若 terminal 为 L4 含住）或权威报告 containment.metrics 指定的一条是终局见证。

| event_id | tick | parent | VA | PA | dyn_inst_seq | containment_reason |
|---|---|---|---|---|---|---|
| 265 | 239349889521 | 20 | 0x7f82b83cf8 | 0x8313acf8 | 4366204 | squash_replay |

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 56 条；event_id `4294967296`–`4294967351`；tick `239345523225`–`239350590819`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 239345523225 | 4338322 | 4339263 | 19→21 | 0x8313a000+1000 |
| 4294967297 | 239345523225 | 4338322 | 4339264 | 19→24 | 0x8313a000+1000 |
| 4294967298 | 239345867880 | 4338322 | 4340744 | 19→41 | 0x8313a000+1000 |
| 4294967299 | 239345867880 | 4338322 | 4340745 | 19→43 | 0x8313a000+1000 |
| 4294967300 | 239346021393 | 4338322 | 4341753 | 19→51 | 0x8313a000+1000 |
| 4294967347 | 239350126284 | 4338322 | 4367402 | 19→278 | 0x8313a000+1000 |
| 4294967348 | 239350306437 | 4338322 | 4368553 | 19→286 | 0x8313a000+1000 |
| 4294967349 | 239350306437 | 4338322 | 4368554 | 19→288 | 0x8313a000+1000 |
| 4294967350 | 239350590819 | 4338322 | 4369828 | 19→296 | 0x8313a000+1000 |
| 4294967351 | 239350590819 | 4338322 | 4369829 | 19→298 | 0x8313a000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`2126`；tick=`241672555530`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 2 个 fault；本文件的代表故障 `fault_id=1` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'full': 1, 'provable_to_L4_then_unknown': 1}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1（代表） | full | L5 | 370 |
| 2 | provable_to_L4_then_unknown | L4 | 1909 |

**为什么主链选的是 L5 逃逸而不是这些 L4 含住旁支**：本 seed 的权威判定采用 escape-first 规则——只要**任一** fault 到达 `full`（真实 errant_commit 逃逸），样本 headline 就是 `full`；squash 类含住证据在同一链上存在可证 L0→L5 逃逸路径时必须让位（`errant_escape_outranks_containment`）。这些旁支 `squash_masked` 是同一故障的其它 load 实例，不改变代表故障的逃逸终局。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`20` tick=`239345295120`（parent=`19`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=79; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 21 events |
| 3_tick_order | PASS | ticks 239345234181..239345295120 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=20 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (21); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T10-F1-W1 and seed2 |
| 12_tier_matches_evidence | PASS | matrix=F1 run.out=CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/prop_evt.txt.gz` | `5680f0a4e26d16433434a5bbc146cd8d073167668a964a8cff97626561cd5c01` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/chain_report.json` | `214430c01a30fcdcdbbf76f9e0001070c8679aaaa46fb07328dbce98d91d2f75` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/manifest.json` | `069e0cb462608bc0227860deec73e5dac2efba623a414a67a71c581b752287eb` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.out` | `418bc61b8c11c1f018632381ab5870ef795186d8c78cc6b245e20d932ba14939` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/run.err` | `88189a144966053141dc15fda8084d3651396edd970718c52fcc9c807f716b17` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s2/T10-F1-W1/seed2/stats.txt` | `652d4f46d0e65b462544ef4892eba6172c0b90970ccfefff8fafadd9a8671e91` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
