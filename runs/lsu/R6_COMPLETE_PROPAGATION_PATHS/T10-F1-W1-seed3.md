# T10-F1-W1 seed3 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T10-F1-W1` seed3 中，注入器于 tick=239629862268 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x83111` 改成 `0x87111`（VA=`0x7fe7c61d40`）；故障 PFN 使有效 PA 从 `0x83111d40` 变为 `0x87111d40`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=45, tick=239629923207）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T10-F1-W1`
- seed: `3`；sample_run_id: `s3`
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
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/prop_evt.txt.gz`
- prop_evt SHA-256: `0d2226c687af26db4300db1abf5f6c25470840852147d052f22f8a6e1675ffea`（本次重算值；字节数 963697）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/chain_report.json`
- chain_report SHA-256: `c05a65bbcca8077f4c628584d32cc83d0af13c74cd608cf230370b74dd0c460b`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/manifest.json`（SHA-256 `fbdb8f8ecafc25313a304ab1c7f0b69f0c6301d76a0df6d9abf1adb1be965c10`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.out`（SHA-256 `4341f68f84a80fdaa9785da799d86c0fce1e6f752d7c47f567009c985a80291c`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.err`（SHA-256 `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/stats.txt`（SHA-256 `593814dd596ff5efe16cd963181a2bab3ac26554487ba420a71a8cc352451650`；`board.chaos_armtlb.numFaultsInjected=3`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 25388；代表故障 `fault_id=1` 事件数: 1382；权威报告 fault 数: 3
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0x7fe7c61d40，PFN 0x83111→0x87111，PA 0x83111d40→0x87111d40 → TLB 地址翻译 → LQ request_id=5536042 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `83111` 变成 `87111`（mask=0x4000；PFN 0x83111→0x87111），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`239629862268`；fault_id=`1`；corr=`origin`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0x7fe7c61d40`
  - 值变化：before=`83111`→after=`87111`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 239629862268, Site: arm_tlb_lookup_hit, VA: 0x7fe7c61d40, old_pfn: 0x83111, new_pfn: 0x87111, FaultType: bit_flip, Mask: 0x4000, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F1 attempted=3442472 eligible=3442472 injected=3 first_eligible_tick=237950233578 last_eligible_tick=243383282757 fires=n/a no_effect=n/a (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0x7fe7c61d40`；PFN=`83111`→`87111`
  - 值变化：before=`83111`→after=`87111`；field=`post_lookup`；state_before=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40`；state_after=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `83111`→`87111`；pa `83111d40`→`87111d40`
- **event_id=`2`；parent_event_id=`1`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x87111d40`；PFN=`83111`→`87111`
  - 值变化：before=`83111`→after=`87111`；field=`bit_flip`；state_before=`83111d40`；state_after=`87111d40`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`239629862268`；fault_id=`1`；corr=`seq_primary`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x87111d40`
  - 值变化：before=`83111d40`→after=`87111d40`；field=`effective_pa_changed`；state_before=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=83111;ap=1;mtype=2;page_size=1000;pa=83111d40`；state_after=`vpn=7fe7c61;asid=214;valid=1;global=0;pfn=87111;ap=1;mtype=2;page_size=1000;pa=87111d40`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`83111d40`，effective=`87111d40`）
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
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x87111d40`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`6`；parent_event_id=`5`；tick=`239629862268`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x87111d40`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`7`；parent_event_id=`6`；tick=`239629862268`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x87111d40`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x87111d40`
- **event_id=`8`；parent_event_id=`7`；tick=`239629862601`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0x7fe7c61d40`；PA=`0x87111d40`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`9`；parent_event_id=`8`；tick=`239629862601`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x87111d40`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`10`；parent_event_id=`9`；tick=`239629862601`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x87111d40`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x87111d40`
- **event_id=`35`；parent_event_id=`10`；tick=`239629921542`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x87111d40`；mshr_id=`2`；fill_id=`1`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x87111d40`；fill_id=`1`
- **event_id=`36`；parent_event_id=`35`；tick=`239629921542`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x87111d40`；cache_line=`0x87111d40`；fill_id=`1`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`37`；parent_event_id=`36`；tick=`239629921542`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x87111d40`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x87111d40`
- **event_id=`38`；parent_event_id=`37`；tick=`239629922208`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x87111d40`；mshr_id=`0`；fill_id=`2`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x87111d40`；fill_id=`2`
- **event_id=`39`；parent_event_id=`38`；tick=`239629922208`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x87111d40`；cache_line=`0x87111d40`；fill_id=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`40`；parent_event_id=`39`；tick=`239629922208`；fault_id=`1`；corr=`addr_fallback`；request_id=`5536042`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x87111d40`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x87111d40`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`41`；parent_event_id=`40`；tick=`239629922541`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x0`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`42`；parent_event_id=`41`；tick=`239629922541`；fault_id=`1`；corr=`seq_primary`；request_id=`0`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0x7fe7c61d32`；PA=`0x0`；lq_idx=`594678`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`43`；parent_event_id=`42`；tick=`239629922541`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x0`；arch_reg=`4`/phys_reg=`68`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
- **event_id=`44`；parent_event_id=`43`；tick=`239629922541`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x0`；arch_reg=`5`/phys_reg=`153`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`45`；parent_event_id=`44`；tick=`239629923207`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`5536042`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`45`, tick=`239629923207`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 103 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=239629923207 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=239629938859 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=239629938860 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=239629943187 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=241738443243 ptag=2 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=241739074611 ptag=2 reason=squash_replay`
- …其余 97 行见原始 `run.out`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 239629862268 | `inj` | L0 | 1 | origin | 5536042 | s3 | 0x7fe7c61d40 | — | 0x83111→0x87111 | 83111→87111 | 0x4000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 239629862268 | `tlb_lookup` | L1 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | — | 0x83111→0x87111 | 83111→87111 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 239629862268 | `tlb_pfn` | L2 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | 0x87111d40 | 0x83111→0x87111 | 83111→87111 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 239629862268 | `tlb_translate_result` | L2 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | 0x87111d40 | — | 83111d40→87111d40 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 239629862268 | `lq_read` | L3 | 1 | seq_primary | 5536042 | s3 | 0x7fe7c61d40 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 读取 load 请求 |
| 6 | 5 | 4 | 239629862268 | `cache_access` | L3 | 1 | addr_fallback | 5536042 | s3 | 0x7fe7c61d40 | 0x87111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=4）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 7 | 6 | 5 | 239629862268 | `cache_return` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 hit/miss 决策 |
| 8 | 7 | 6 | 239629862268 | `mshr_alloc` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=6） | L3 MSHR 分配 |
| 9 | 8 | 7 | 239629862601 | `cache_access` | L3 | 1 | addr_fallback | 5536042 | s3 | 0x7fe7c61d40 | 0x87111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=7） | L3 cache 查找 |
| 10 | 9 | 8 | 239629862601 | `cache_return` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 hit/miss 决策 |
| 11 | 10 | 9 | 239629862601 | `mshr_alloc` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=9） | L3 MSHR 分配 |
| 12 | 35 | 10 | 239629921542 | `mshr_fill` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→filled | — | — | — | — | — | 直接 parent（parent=10） | L3 MSHR 填充 |
| 13 | 36 | 35 | 239629921542 | `cache_fill` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=35） | L3 行填充 |
| 14 | 37 | 36 | 239629921542 | `mshr_free` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=36） | L3 MSHR 释放 |
| 15 | 38 | 37 | 239629922208 | `mshr_fill` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→filled | — | — | — | — | — | 直接 parent（parent=37） | L3 MSHR 填充 |
| 16 | 39 | 38 | 239629922208 | `cache_fill` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→— | — | — | — | — | — | 直接 parent（parent=38） | L3 行填充 |
| 17 | 40 | 39 | 239629922208 | `mshr_free` | L3 | 1 | addr_fallback | 5536042 | s3 | — | 0x87111d40 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=39） | L3 MSHR 释放 |
| 18 | 41 | 40 | 239629922541 | `resp` | L3 | 1 | seq_primary | — | s3 | 0x0 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=40）；corr addr_fallback→seq_primary | L3 响应返回 |
| 19 | 42 | 41 | 239629922541 | `lq_complete` | L3 | 1 | seq_primary | 0 | s3 | 0x7fe7c61d32 | 0x0 | — | —→— | — | — | — | — | — | 直接 parent（parent=41） | L3 load 完成 |
| 20 | 43 | 42 | 239629922541 | `taint_reg` | L4 | 1 | seq_primary | — | s3 | 0x0 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=42） | L4 污染寄存器 |
| 21 | 44 | 43 | 239629922541 | `taint_reg` | L4 | 1 | seq_primary | — | s3 | 0x0 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=43） | L4 污染寄存器 |
| 22 | 45 | 44 | 239629923207 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s3 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=44）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（22 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **25388**；代表故障 `fault_id=1` 的事件数 **1382**；进入最终 ancestry 的事件 **22**；未进入最终 ancestry 的同 fault 事件 **1360**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 1281 | 46–1370 | 239629923540–239654376063 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `cache_access` | 12 | 11–106 | 239629863600–239629945851 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 12 | 12–107 | 239629863600–239629945851 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 8, 'hit': 4} | 无（outcome/contained 全空） |
| `request_fork` | 10 | 4294967296–4294967305 | 239629863600–239629945851 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `resp` | 7 | 68–108 | 239629927536–239629946184 | 计数 + 范围 | 无（outcome/contained 全空） |
| `lq_complete` | 7 | 69–109 | 239629927536–239629946184 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 7 | 70–110 | 239629927536–239629946184 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `mshr_alloc` | 4 | 13–22 | 239629863600–239629864266 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_merge` | 4 | 25–34 | 239629865931–239629867596 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_fill` | 4 | 62–77 | 239629926537–239629937859 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_fill` | 4 | 63–78 | 239629926537–239629937859 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_free` | 4 | 64–79 | 239629926537–239629937859 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `squash_masked` | 3 | 86–101 | 239629938859–239629943187 | 不折叠：全部逐条点名（见下） | 预期非空（检测/含住事件）：outcome={'masked': 3} contained={'1': 3} |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 239629863600 |
| L4 | `consumer` | 46 | 239629923540 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=1281；event_id 范围 `46`–`1370`；tick 范围 `239629923540`–`239654376063`；corr 分布 {'taint_prop': 1281}；outcome 分布 {'': 1281}；contained 分布 {'': 1281}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=7；event_id `70`–`110`；tick `239629927536`–`239629946184`；distinct dyn_inst_seq=7；distinct phys_reg=7；distinct arch_reg=3；corr 分布 {'addr_fallback': 7}；outcome 分布 {'': 7}；contained 分布 {'': 7}；sample_run 分布 {'s3': 7}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 70 | 239629927536 | 69 | 5536064 | 1/205 | clean→tainted | addr_fallback |
| 73 | 239629928202 | 72 | 5536112 | 0/81 | clean→tainted | addr_fallback |
| 82 | 239629938192 | 81 | 5536060 | 2/33 | clean→tainted | addr_fallback |
| 85 | 239629938858 | 84 | 5536091 | 2/165 | clean→tainted | addr_fallback |
| 95 | 239629941855 | 94 | 5536199 | 2/64 | clean→tainted | addr_fallback |
| 98 | 239629941856 | 97 | 5536203 | 1/173 | clean→tainted | addr_fallback |
| 110 | 239629946184 | 109 | 5536269 | 0/77 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（7 条，不折叠，逐条列出）</b></summary>

70@239629927536(1/205) 73@239629928202(0/81) 82@239629938192(2/33) 85@239629938858(2/165) 95@239629941855(2/64) 98@239629941856(1/173) 110@239629946184(0/77)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（12 条，不折叠）</b></summary>

12@239629863600:miss 15@239629863933:miss 18@239629863933:miss 21@239629864266:miss 24@239629865931:miss 27@239629865931:miss 30@239629867263:miss 33@239629867596:miss

90@239629941522:hit 92@239629941522:hit 100@239629942854:hit 107@239629945851:hit

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（16 条，不折叠）</b></summary>

13@239629863600:mshr_alloc:mshr=3,fill=— 16@239629863933:mshr_alloc:mshr=4,fill=— 19@239629863933:mshr_alloc:mshr=5,fill=— 22@239629864266:mshr_alloc:mshr=6,fill=—

25@239629865931:mshr_merge:mshr=4,fill=— 28@239629865931:mshr_merge:mshr=4,fill=— 31@239629867263:mshr_merge:mshr=6,fill=— 34@239629867596:mshr_merge:mshr=4,fill=—

62@239629926537:mshr_fill:mshr=6,fill=3 64@239629926537:mshr_free:mshr=6,fill=— 65@239629927203:mshr_fill:mshr=0,fill=4 67@239629927203:mshr_free:mshr=0,fill=—

74@239629936860:mshr_fill:mshr=4,fill=5 76@239629936860:mshr_free:mshr=4,fill=— 77@239629937859:mshr_fill:mshr=0,fill=6 79@239629937859:mshr_free:mshr=0,fill=—

</details>

**`squash_masked` 旁支（不折叠，全部点名）**：共 3 条，均为同一 fault 的 L4 contain-by-squash 见证；只有主链上的那一条（若 terminal 为 L4 含住）或权威报告 containment.metrics 指定的一条是终局见证。

| event_id | tick | parent | VA | PA | dyn_inst_seq | containment_reason |
|---|---|---|---|---|---|---|
| 86 | 239629938859 | 61 | 0x7fe7c61d18 | 0x87111d18 | 5536095 | squash_replay |
| 87 | 239629938860 | 86 | 0x7fe7c61d20 | 0x87111d20 | 5536116 | squash_replay |
| 101 | 239629943187 | 88 | 0x7fe7c61ce0 | 0x87111ce0 | 5536225 | squash_replay |

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 10 条；event_id `4294967296`–`4294967305`；tick `239629863600`–`239629945851`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 239629863600 | 5536042 | 5536060 | 10→11 | 0x87111000+1000 |
| 4294967297 | 239629863933 | 5536042 | 5536064 | 10→17 | 0x87111000+1000 |
| 4294967298 | 239629865931 | 5536042 | 5536091 | 10→23 | 0x87111000+1000 |
| 4294967299 | 239629865931 | 5536042 | 5536095 | 10→26 | 0x87111000+1000 |
| 4294967300 | 239629867263 | 5536042 | 5536112 | 10→29 | 0x87111000+1000 |
| 4294967301 | 239629867596 | 5536042 | 5536116 | 10→32 | 0x87111000+1000 |
| 4294967302 | 239629941522 | 5536042 | 5536199 | 40→89 | 0x87111000+1000 |
| 4294967303 | 239629941522 | 5536042 | 5536203 | 40→91 | 0x87111000+1000 |
| 4294967304 | 239629942854 | 5536042 | 5536225 | 40→99 | 0x87111000+1000 |
| 4294967305 | 239629945851 | 5536042 | 5536269 | 40→106 | 0x87111000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`21443`；tick=`243383282757`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 3 个 fault；本文件的代表故障 `fault_id=1` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'full': 1, 'detected_contained': 2}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1（代表） | full | L5 | 1382 |
| 2 | detected_contained | L5 | 15733 |
| 3 | detected_contained | L5 | 8273 |

**为什么主链选的是 L5 逃逸而不是这些 L4 含住旁支**：本 seed 的权威判定采用 escape-first 规则——只要**任一** fault 到达 `full`（真实 errant_commit 逃逸），样本 headline 就是 `full`；squash 类含住证据在同一链上存在可证 L0→L5 逃逸路径时必须让位（`errant_escape_outranks_containment`）。这些旁支 `squash_masked` 是同一故障的其它 load 实例，不改变代表故障的逃逸终局。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`45` tick=`239629923207`（parent=`44`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=36; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 22 events |
| 3_tick_order | PASS | ticks 239629862268..239629923207 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=45 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (22); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T10-F1-W1 and seed3 |
| 12_tier_matches_evidence | PASS | matrix=F1 run.out=CHAOS_LSU_TIER_CAP: requested=F1 effective=F1 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/prop_evt.txt.gz` | `0d2226c687af26db4300db1abf5f6c25470840852147d052f22f8a6e1675ffea` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/chain_report.json` | `c05a65bbcca8077f4c628584d32cc83d0af13c74cd608cf230370b74dd0c460b` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/manifest.json` | `fbdb8f8ecafc25313a304ab1c7f0b69f0c6301d76a0df6d9abf1adb1be965c10` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.out` | `4341f68f84a80fdaa9785da799d86c0fce1e6f752d7c47f567009c985a80291c` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/run.err` | `aa5dc7ea7b8182029ceb4ca56fc7d72541ed6064d3353724646f72abd1543a36` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3/T10-F1-W1/seed3/stats.txt` | `593814dd596ff5efe16cd963181a2bab3ac26554487ba420a71a8cc352451650` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
