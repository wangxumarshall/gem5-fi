# T10-F0-W1 seed1 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T10-F0-W1` seed1 中，注入器于 tick=237950940537 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81d75` 改成 `0xa1d75`（VA=`0xffffffc009483fa8`）；故障 PFN 使有效 PA 从 `0x81d75fa8` 变为 `0xa1d75fa8`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=118, tick=237951302175）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T10-F0-W1`
- seed: `1`；sample_run_id: `s1`
- 实验模型: 模型ID=`T10`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `单比特翻转`
- 故障模型: 随机选择一个后续会再次命中的有效表项，在 PPN 内均匀翻转 1 bit；按低/中/高物理地址位分层，VPN、ASID、权限和页大小保持不变。仅当该表项之后被命中且故障 PPN 被用于形成物理地址时计为 activated；保存 entry、bit、原值、故障值和首次消费事务。
- 频率档位: `F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier: `F0`；effective tier: `F0`；tier enabled: `关闭(0)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- **差异说明（不推断）**: 矩阵标签为 MiBench，但该 seed 的原始 `run.out` 命令行 `--readfile` 指向 `tlb_probe.rcS`；本文件以原始证据为准，同时保留矩阵标签，二者不一致处如实标注。
- source head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/prop_evt.txt.gz`
- prop_evt SHA-256: `342e552a20f0121321a8941f90151934f87140c1b166d6061ebece5e6624a2da`（本次重算值；字节数 9891）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/chain_report.json`
- chain_report SHA-256: `71603a0b34978d0547e016780c54f121f42b73d54f4df9f0d4506d8688afc2d5`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/manifest.json`（SHA-256 `68afe2c0d1bb4c7c8114756cd6863c05ad7a0ef313f0c7428e7f72b285a1599b`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.out`（SHA-256 `78a3d6cd7f16dedb0598bee56cc1eb2310fe5814ec11903ea545aa930946988e`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.err`（SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/stats.txt`（SHA-256 `555ca143149b3e47c983c8bade030e9017ab69a35f19e7239af23a3db5d95296`；`board.chaos_armtlb.numFaultsInjected=1`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 238；代表故障 `fault_id=1` 事件数: 238；权威报告 fault 数: 1
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc009483fa8，PFN 0x81d75→0xa1d75，PA 0x81d75fa8→0xa1d75fa8 → TLB 地址翻译 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81d75` 变成 `a1d75`（mask=0x20000；PFN 0x81d75→0xa1d75），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950940537`；fault_id=`1`；corr=`origin`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc009483fa8`
  - 值变化：before=`81d75`→after=`a1d75`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0xa1d75, FaultType: bit_flip, Mask: 0x20000, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=150162 eligible=56 injected=1 first_eligible_tick=237950233578 last_eligible_tick=237950940537 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc009483fa8`；PFN=`81d75`→`a1d75`
  - 值变化：before=`81d75`→after=`a1d75`；field=`post_lookup`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81d75`→`a1d75`；pa `81d75fa8`→`a1d75fa8`
- **event_id=`2`；parent_event_id=`1`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0xa1d75fa8`；PFN=`81d75`→`a1d75`
  - 值变化：before=`81d75`→after=`a1d75`；field=`bit_flip`；state_before=`81d75fa8`；state_after=`a1d75fa8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`237950940537`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0xa1d75fa8`
  - 值变化：before=`81d75fa8`→after=`a1d75fa8`；field=`effective_pa_changed`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=a1d75;ap=0;mtype=2;page_size=1000;pa=a1d75fa8`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`81d75fa8`，effective=`a1d75fa8`）
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
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0xa1d75fa8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`7`；parent_event_id=`6`；tick=`237950941869`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0xa1d75fa8`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`8`；parent_event_id=`7`；tick=`237950941869`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0xa1d75fa8`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0xa1d75fa8`
- **event_id=`15`；parent_event_id=`8`；tick=`237950942202`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483fa8`；PA=`0xa1d75f80`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`16`；parent_event_id=`15`；tick=`237950942202`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0xa1d75f80`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`17`；parent_event_id=`16`；tick=`237950942202`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0xa1d75f80`；mshr_id=`3`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`3`；cache_line=`0xa1d75f80`
- **event_id=`30`；parent_event_id=`17`；tick=`237951015129`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0xa1d75f80`；mshr_id=`3`；fill_id=`1`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`3`；cache_line=`0xa1d75f80`；fill_id=`1`
- **event_id=`31`；parent_event_id=`30`；tick=`237951015129`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0xa1d75f80`；cache_line=`0xa1d75f80`；fill_id=`1`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`32`；parent_event_id=`31`；tick=`237951015129`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0xa1d75f80`；mshr_id=`3`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`3`；cache_line=`0xa1d75f80`
- **event_id=`33`；parent_event_id=`32`；tick=`237951015795`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0xa1d75f80`；mshr_id=`0`；fill_id=`2`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0xa1d75f80`；fill_id=`2`
- **event_id=`34`；parent_event_id=`33`；tick=`237951015795`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0xa1d75f80`；cache_line=`0xa1d75f80`；fill_id=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`35`；parent_event_id=`34`；tick=`237951015795`；fault_id=`1`；corr=`addr_fallback`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0xa1d75f80`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0xa1d75f80`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`5`；parent_event_id=`4`；tick=`237950941869`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`301`**
  - 硬件结构/事件：store 数据/地址写回存储子系统，错误 PA 随之进入 cache 侧。
  - 地址/身份：PA=`0xa1d75fa8`；sq_idx=`32`
  - 值变化：state_before=`—`；state_after=`packet_built`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`39`；parent_event_id=`35`；tick=`237951016128`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0xa1d75fa8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`40`；parent_event_id=`39`；tick=`237951016128`；fault_id=`1`；corr=`seq_primary`；request_id=`301`；dyn_inst_seq=`301`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0xa1d75fa8`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
- **event_id=`41`；parent_event_id=`40`；tick=`237951016128`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`301`**
  - 硬件结构/事件：store 在 SQ 中完成（错误副作用已发生或已被约束）。
  - 地址/身份：VA=`0xffffffc009483fa8`；sq_idx=`32`
  - 值变化：state_before=`—`；state_after=`completed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`118`；parent_event_id=`41`；tick=`237951302175`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`391`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`118`, tick=`237951302175`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 2 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951547263 ptag=1 reason=squash_replay`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | `inj` | L0 | 1 | origin | 301 | s1 | 0xffffffc009483fa8 | — | 0x81d75→0xa1d75 | 81d75→a1d75 | 0x20000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950940537 | `tlb_lookup` | L1 | 1 | seq_primary | 301 | s1 | 0xffffffc009483fa8 | — | 0x81d75→0xa1d75 | 81d75→a1d75 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 237950940537 | `tlb_pfn` | L2 | 1 | seq_primary | 301 | s1 | 0xffffffc009483fa8 | 0xa1d75fa8 | 0x81d75→0xa1d75 | 81d75→a1d75 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950940537 | `tlb_translate_result` | L2 | 1 | seq_primary | 301 | s1 | 0xffffffc009483fa8 | 0xa1d75fa8 | — | 81d75fa8→a1d75fa8 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 237950940537 | `sq_execute` | L3 | 1 | seq_primary | — | s1 | 0xffffffc009483fa8 | — | — | issued→— | — | — | — | — | — | 直接 parent（parent=3） | L3 store 发射 |
| 6 | 5 | 4 | 237950941869 | `sq_writeback` | L3 | 1 | seq_primary | — | s1 | — | 0xa1d75fa8 | — | —→packet_built | — | — | — | — | — | 直接 parent（parent=4） | L3 store 写回 |
| 7 | 6 | 5 | 237950941869 | `cache_access` | L3 | 1 | addr_fallback | 301 | s1 | 0xffffffc009483fa8 | 0xa1d75fa8 | — | —→— | — | — | — | — | — | 直接 parent（parent=5）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 8 | 7 | 6 | 237950941869 | `cache_return` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75fa8 | — | —→— | — | — | — | — | — | 直接 parent（parent=6） | L3 hit/miss 决策 |
| 9 | 8 | 7 | 237950941869 | `mshr_alloc` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75fa8 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=7） | L3 MSHR 分配 |
| 10 | 15 | 8 | 237950942202 | `cache_access` | L3 | 1 | addr_fallback | 301 | s1 | 0xffffffc009483fa8 | 0xa1d75f80 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 cache 查找 |
| 11 | 16 | 15 | 237950942202 | `cache_return` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→— | — | — | — | — | — | 直接 parent（parent=15） | L3 hit/miss 决策 |
| 12 | 17 | 16 | 237950942202 | `mshr_alloc` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=16） | L3 MSHR 分配 |
| 13 | 30 | 17 | 237951015129 | `mshr_fill` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→filled | — | — | — | — | — | 直接 parent（parent=17） | L3 MSHR 填充 |
| 14 | 31 | 30 | 237951015129 | `cache_fill` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→— | — | — | — | — | — | 直接 parent（parent=30） | L3 行填充 |
| 15 | 32 | 31 | 237951015129 | `mshr_free` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=31） | L3 MSHR 释放 |
| 16 | 33 | 32 | 237951015795 | `mshr_fill` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→filled | — | — | — | — | — | 直接 parent（parent=32） | L3 MSHR 填充 |
| 17 | 34 | 33 | 237951015795 | `cache_fill` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→— | — | — | — | — | — | 直接 parent（parent=33） | L3 行填充 |
| 18 | 35 | 34 | 237951015795 | `mshr_free` | L3 | 1 | addr_fallback | 301 | s1 | — | 0xa1d75f80 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=34） | L3 MSHR 释放 |
| 19 | 39 | 35 | 237951016128 | `resp` | L3 | 1 | seq_primary | 301 | s1 | 0xa1d75fa8 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=35）；corr addr_fallback→seq_primary | L3 响应返回 |
| 20 | 40 | 39 | 237951016128 | `taint_reg` | L4 | 1 | seq_primary | 301 | s1 | 0xa1d75fa8 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=39） | L4 污染寄存器 |
| 21 | 41 | 40 | 237951016128 | `sq_complete` | L3 | 1 | seq_primary | — | s1 | 0xffffffc009483fa8 | — | — | —→completed | — | — | — | — | — | 直接 parent（parent=40） | L3 store 完成 |
| 22 | 118 | 41 | 237951302175 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s1 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=41）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（22 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **238**；代表故障 `fault_id=1` 的事件数 **238**；进入最终 ancestry 的事件 **22**；未进入最终 ancestry 的同 fault 事件 **216**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 61 | 119–214 | 237951302175–237964973157 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `cache_access` | 25 | 9–206 | 237950941869–237964970493 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 25 | 10–207 | 237950941869–237964970493 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 16, 'hit': 9} | 无（outcome/contained 全空） |
| `request_fork` | 22 | 4294967296–4294967317 | 237950941869–237964970493 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `taint_reg` | 22 | 46–210 | 237951016794–237964970826 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `resp` | 21 | 45–208 | 237951016794–237964970826 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_merge` | 10 | 14–98 | 237950941869–237951251226 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_alloc` | 6 | 11–92 | 237950941869–237951251226 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_fill` | 6 | 36–102 | 237951015795–237951296514 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_fill` | 6 | 37–103 | 237951015795–237951296514 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_free` | 6 | 38–104 | 237951015795–237951296514 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `lq_complete` | 4 | 116–209 | 237951301176–237964970826 | 计数 + 范围 | 无（outcome/contained 全空） |
| `squash_masked` | 1 | 144–144 | 237951547263–237951547263 | 不折叠：全部逐条点名（见下） | 预期非空（检测/含住事件）：outcome={'masked': 1} contained={'1': 1} |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 237950941869 |
| L4 | `taint_reg` | 46 | 237951016794 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=61；event_id 范围 `119`–`214`；tick 范围 `237951302175`–`237964973157`；corr 分布 {'taint_prop': 61}；outcome 分布 {'': 61}；contained 分布 {'': 61}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=22；event_id `46`–`210`；tick `237951016794`–`237964970826`；distinct dyn_inst_seq=21；distinct phys_reg=6；distinct arch_reg=5；corr 分布 {'addr_fallback': 22}；outcome 分布 {'': 22}；contained 分布 {'': 22}；sample_run 分布 {'s1': 22}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 46 | 237951016794 | 45 | 307 | —/— | clean→tainted | addr_fallback |
| 48 | 237951016795 | 47 | 308 | —/— | clean→tainted | addr_fallback |
| 50 | 237951017127 | 49 | 303 | —/— | clean→tainted | addr_fallback |
| 52 | 237951017793 | 51 | 304 | —/— | clean→tainted | addr_fallback |
| 54 | 237951017794 | 53 | 310 | —/— | clean→tainted | addr_fallback |
| 77 | 237951136674 | 76 | 357 | —/— | clean→tainted | addr_fallback |
| 79 | 237951137340 | 78 | 358 | —/— | clean→tainted | addr_fallback |
| 81 | 237951137341 | 80 | 369 | —/— | clean→tainted | addr_fallback |
| 125 | 237951386424 | 124 | 460 | —/— | clean→tainted | addr_fallback |
| 127 | 237951386425 | 126 | 461 | —/— | clean→tainted | addr_fallback |
| 132 | 237951445365 | 131 | 474 | 29/158 | clean→tainted | addr_fallback |
| 133 | 237951445365 | 132 | 474 | 30/159 | clean→tainted | addr_fallback |
| 139 | 237951502308 | 138 | 507 | —/— | clean→tainted | addr_fallback |
| 141 | 237951502309 | 140 | 508 | —/— | clean→tainted | addr_fallback |
| 149 | 237957326481 | 148 | 3937 | 0/2 | clean→tainted | addr_fallback |
| 210 | 237964970826 | 209 | 10529 | 1/228 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（22 条，不折叠，逐条列出）</b></summary>

46@237951016794(—/—) 48@237951016795(—/—) 50@237951017127(—/—) 52@237951017793(—/—) 54@237951017794(—/—) 77@237951136674(—/—) 79@237951137340(—/—) 81@237951137341(—/—)

83@237951137342(—/—) 106@237951296847(—/—) 108@237951297513(—/—) 110@237951297514(—/—) 112@237951297515(—/—) 117@237951301176(0/142) 125@237951386424(—/—) 127@237951386425(—/—)

132@237951445365(29/158) 133@237951445365(30/159) 139@237951502308(—/—) 141@237951502309(—/—) 149@237957326481(0/2) 210@237964970826(1/228)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（25 条，不折叠）</b></summary>

10@237950941869:miss 13@237950941869:miss 19@237950942535:miss 22@237950942535:miss 25@237950942535:miss 28@237950942868:miss 56@237951088056:miss 59@237951088056:miss

62@237951088389:miss 65@237951135009:miss 68@237951135009:miss 85@237951250893:miss 88@237951250893:miss 91@237951251226:miss 94@237951251226:miss 97@237951251226:miss

114@237951300843:hit 121@237951386091:hit 123@237951386091:hit 129@237951445032:hit 135@237951501975:hit 137@237951501975:hit 143@237951546930:hit 146@237957326145:hit

207@237964970493:hit

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（28 条，不折叠）</b></summary>

11@237950941869:mshr_alloc:mshr=2,fill=— 14@237950941869:mshr_merge:mshr=2,fill=— 20@237950942535:mshr_alloc:mshr=4,fill=— 23@237950942535:mshr_merge:mshr=3,fill=—

26@237950942535:mshr_merge:mshr=3,fill=— 29@237950942868:mshr_merge:mshr=4,fill=— 36@237951015795:mshr_fill:mshr=4,fill=3 38@237951015795:mshr_free:mshr=4,fill=—

42@237951016794:mshr_fill:mshr=0,fill=4 44@237951016794:mshr_free:mshr=0,fill=— 57@237951088056:mshr_alloc:mshr=5,fill=— 60@237951088056:mshr_merge:mshr=5,fill=—

63@237951088389:mshr_alloc:mshr=6,fill=— 66@237951135009:mshr_merge:mshr=6,fill=— 69@237951135009:mshr_merge:mshr=6,fill=— 70@237951135675:mshr_fill:mshr=6,fill=5

72@237951135675:mshr_free:mshr=6,fill=— 73@237951136341:mshr_fill:mshr=0,fill=6 75@237951136341:mshr_free:mshr=0,fill=— 86@237951250893:mshr_alloc:mshr=7,fill=—

89@237951250893:mshr_merge:mshr=7,fill=— 92@237951251226:mshr_alloc:mshr=8,fill=— 95@237951251226:mshr_merge:mshr=8,fill=— 98@237951251226:mshr_merge:mshr=8,fill=—

99@237951295848:mshr_fill:mshr=8,fill=7 101@237951295848:mshr_free:mshr=8,fill=— 102@237951296514:mshr_fill:mshr=0,fill=8 104@237951296514:mshr_free:mshr=0,fill=—

</details>

**`squash_masked` 旁支（不折叠，全部点名）**：共 1 条，均为同一 fault 的 L4 contain-by-squash 见证；只有主链上的那一条（若 terminal 为 L4 含住）或权威报告 containment.metrics 指定的一条是终局见证。

| event_id | tick | parent | VA | PA | dyn_inst_seq | containment_reason |
|---|---|---|---|---|---|---|
| 144 | 237951547263 | 119 | 0xffffffc009483e40 | 0xa1d75e40 | 520 | squash_replay |

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 22 条；event_id `4294967296`–`4294967317`；tick `237950941869`–`237964970493`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 237950941869 | 301 | 303 | 8→9 | 0xa1d75000+1000 |
| 4294967297 | 237950941869 | 301 | 304 | 8→12 | 0xa1d75000+1000 |
| 4294967298 | 237950942535 | 301 | 307 | 17→21 | 0xa1d75000+1000 |
| 4294967299 | 237950942535 | 301 | 308 | 17→24 | 0xa1d75000+1000 |
| 4294967300 | 237950942868 | 301 | 310 | 17→27 | 0xa1d75000+1000 |
| 4294967313 | 237951501975 | 301 | 507 | 40→134 | 0xa1d75000+1000 |
| 4294967314 | 237951501975 | 301 | 508 | 40→136 | 0xa1d75000+1000 |
| 4294967315 | 237951546930 | 301 | 520 | 40→142 | 0xa1d75000+1000 |
| 4294967316 | 237957326145 | 301 | 3937 | 40→145 | 0xa1d75000+1000 |
| 4294967317 | 237964970493 | 301 | 10529 | 40→206 | 0xa1d75000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`215`；tick=`238882168377`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**为什么主链选的是 L5 逃逸而不是这些 L4 含住旁支**：本 seed 的权威判定采用 escape-first 规则——只要**任一** fault 到达 `full`（真实 errant_commit 逃逸），样本 headline 就是 `full`；squash 类含住证据在同一链上存在可证 L0→L5 逃逸路径时必须让位（`errant_escape_outranks_containment`）。这些旁支 `squash_masked` 是同一故障的其它 load 实例，不改变代表故障的逃逸终局。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`118` tick=`237951302175`（parent=`41`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=46; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 22 events |
| 3_tick_order | PASS | ticks 237950940537..237951302175 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=118 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (22); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T10-F0-W1 and seed1 |
| 12_tier_matches_evidence | PASS | matrix=F0 run.out=CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0 expected_enabled=0 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/prop_evt.txt.gz` | `342e552a20f0121321a8941f90151934f87140c1b166d6061ebece5e6624a2da` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/chain_report.json` | `71603a0b34978d0547e016780c54f121f42b73d54f4df9f0d4506d8688afc2d5` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/manifest.json` | `68afe2c0d1bb4c7c8114756cd6863c05ad7a0ef313f0c7428e7f72b285a1599b` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.out` | `78a3d6cd7f16dedb0598bee56cc1eb2310fe5814ec11903ea545aa930946988e` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s1/T10-F0-W1/seed1/stats.txt` | `555ca143149b3e47c983c8bade030e9017ab69a35f19e7239af23a3db5d95296` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
