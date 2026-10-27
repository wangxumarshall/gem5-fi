# T02-F2-W1 seed1 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T02-F2-W1` seed1 中，注入器于 tick=238085259417 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81362` 改成 `0xc5362`（VA=`0xffffff8001362708`）；故障 PFN 使有效 PA 从 `0x81362708` 变为 `0xc5362708`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=26, tick=238085320689）在 L5 形成真实错误提交；运行结局 Crash（KERNEL PANIC under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T02-F2-W1`
- seed: `1`；sample_run_id: `s1`
- 实验模型: 模型ID=`T02`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `双比特翻转`
- 故障模型: PPN内同时翻转2 bit，邻近/非邻近各半；权限位不动。实施细则：每次故障运行只选一个有效结构项，在同一字段内同时异或两个不同 bit；相邻位与非相邻位分层各占一半，并记录两个 bit 的编号、距离、原值和故障值。两个 bit 必须在同一个微架构事件生效，不与其他字段故障叠加。激活口径：仅当“有效表项且后续复用”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F2` — 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动
- requested tier: `F2`；effective tier: `F2`；tier enabled: `开启(1)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- **差异说明（不推断）**: 矩阵标签为 MiBench，但该 seed 的原始 `run.out` 命令行 `--readfile` 指向 `tlb_probe.rcS`；本文件以原始证据为准，同时保留矩阵标签，二者不一致处如实标注。
- source head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/prop_evt.txt.gz`
- prop_evt SHA-256: `09123a77e98c32503b479e026ff8dc43ad0eb3aefa4de349ae4010003f9a212c`（本次重算值；字节数 101366）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/chain_report.json`
- chain_report SHA-256: `85c328179d1847d316c81aa30d1c42f12592caf154d7c514cf1a14bf867e3def`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/manifest.json`（SHA-256 `5e351346f7a7002e9f05f26b3e26bd0e4b8909d8ecf10402e2fd5c0a9b0ed04b`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/run.out`（SHA-256 `ecd786ebbd64e990c68c99c0473c490349284258b374111b82bd96fb86854cf8`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/run.err`（SHA-256 `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/stats.txt`（SHA-256 `8b5284423283c9ee642c6443f2818f4eec633b0f092437b8e2e4ac72bedebef6`；`board.chaos_armtlb.numFaultsInjected=3`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 2631；代表故障 `fault_id=1` 事件数: 2323；权威报告 fault 数: 3
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffff8001362708，PFN 0x81362→0xc5362，PA 0x81362708→0xc5362708 → TLB 地址翻译 → LQ request_id=415526 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81362` 变成 `c5362`（mask=0x44000；PFN 0x81362→0xc5362），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`238085259417`；fault_id=`1`；corr=`origin`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffff8001362708`
  - 值变化：before=`81362`→after=`c5362`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 238085259417, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362708, old_pfn: 0x81362, new_pfn: 0xc5362, FaultType: bit_flip, Mask: 0x44000, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F2 attempted=248635 eligible=248635 injected=3 first_eligible_tick=237950233578 last_eligible_tick=238693668732 fires=n/a no_effect=n/a (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffff8001362708`；PFN=`81362`→`c5362`
  - 值变化：before=`81362`→after=`c5362`；field=`post_lookup`；state_before=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`；state_after=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=c5362;ap=0;mtype=2;page_size=1000;pa=c5362708`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81362`→`c5362`；pa `81362708`→`c5362708`
- **event_id=`2`；parent_event_id=`1`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0xc5362708`；PFN=`81362`→`c5362`
  - 值变化：before=`81362`→after=`c5362`；field=`bit_flip`；state_before=`81362708`；state_after=`c5362708`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`238085259417`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0xc5362708`
  - 值变化：before=`81362708`→after=`c5362708`；field=`effective_pa_changed`；state_before=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362708`；state_after=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=c5362;ap=0;mtype=2;page_size=1000;pa=c5362708`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`81362708`，effective=`c5362708`）
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
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0xc5362708`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`6`；parent_event_id=`5`；tick=`238085259417`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0xc5362708`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`7`；parent_event_id=`6`；tick=`238085259417`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0xc5362708`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0xc5362708`
- **event_id=`8`；parent_event_id=`7`；tick=`238085259750`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0xc5362700`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`9`；parent_event_id=`8`；tick=`238085259750`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0xc5362700`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`10`；parent_event_id=`9`；tick=`238085259750`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0xc5362700`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0xc5362700`
- **event_id=`14`；parent_event_id=`10`；tick=`238085318691`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0xc5362700`；mshr_id=`2`；fill_id=`1`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0xc5362700`；fill_id=`1`
- **event_id=`15`；parent_event_id=`14`；tick=`238085318691`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0xc5362700`；cache_line=`0xc5362700`；fill_id=`1`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`16`；parent_event_id=`15`；tick=`238085318691`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0xc5362700`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0xc5362700`
- **event_id=`17`；parent_event_id=`16`；tick=`238085319357`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0xc5362700`；mshr_id=`0`；fill_id=`2`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0xc5362700`；fill_id=`2`
- **event_id=`18`；parent_event_id=`17`；tick=`238085319357`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0xc5362700`；cache_line=`0xc5362700`；fill_id=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`19`；parent_event_id=`18`；tick=`238085319357`；fault_id=`1`；corr=`addr_fallback`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0xc5362700`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0xc5362700`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`20`；parent_event_id=`19`；tick=`238085319690`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0xc5362708`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`21`；parent_event_id=`20`；tick=`238085319690`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0xffffff8001362708`；PA=`0xc5362708`；lq_idx=`44911`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`22`；parent_event_id=`21`；tick=`238085319690`；fault_id=`1`；corr=`seq_primary`；request_id=`415526`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0xc5362708`；arch_reg=`4`/phys_reg=`42`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`26`；parent_event_id=`22`；tick=`238085320689`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`415526`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`26`, tick=`238085320689`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL PANIC under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 26 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=238085320689 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238085615727 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238085646363 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238086128214 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238086158850 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=238086346330 ptag=1 reason=squash_replay`
- …其余 20 行见原始 `run.out`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 238085259417 | `inj` | L0 | 1 | origin | 415526 | s1 | 0xffffff8001362708 | — | 0x81362→0xc5362 | 81362→c5362 | 0x44000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 238085259417 | `tlb_lookup` | L1 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | — | 0x81362→0xc5362 | 81362→c5362 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 238085259417 | `tlb_pfn` | L2 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | 0xc5362708 | 0x81362→0xc5362 | 81362→c5362 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 238085259417 | `tlb_translate_result` | L2 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | 0xc5362708 | — | 81362708→c5362708 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 238085259417 | `lq_read` | L3 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 读取 load 请求 |
| 6 | 5 | 4 | 238085259417 | `cache_access` | L3 | 1 | addr_fallback | 415526 | s1 | 0xffffff8001362708 | 0xc5362708 | — | —→— | — | — | — | — | — | 直接 parent（parent=4）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 7 | 6 | 5 | 238085259417 | `cache_return` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362708 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 hit/miss 决策 |
| 8 | 7 | 6 | 238085259417 | `mshr_alloc` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362708 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=6） | L3 MSHR 分配 |
| 9 | 8 | 7 | 238085259750 | `cache_access` | L3 | 1 | addr_fallback | 415526 | s1 | 0xffffff8001362708 | 0xc5362700 | — | —→— | — | — | — | — | — | 直接 parent（parent=7） | L3 cache 查找 |
| 10 | 9 | 8 | 238085259750 | `cache_return` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 hit/miss 决策 |
| 11 | 10 | 9 | 238085259750 | `mshr_alloc` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=9） | L3 MSHR 分配 |
| 12 | 14 | 10 | 238085318691 | `mshr_fill` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→filled | — | — | — | — | — | 直接 parent（parent=10） | L3 MSHR 填充 |
| 13 | 15 | 14 | 238085318691 | `cache_fill` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→— | — | — | — | — | — | 直接 parent（parent=14） | L3 行填充 |
| 14 | 16 | 15 | 238085318691 | `mshr_free` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=15） | L3 MSHR 释放 |
| 15 | 17 | 16 | 238085319357 | `mshr_fill` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→filled | — | — | — | — | — | 直接 parent（parent=16） | L3 MSHR 填充 |
| 16 | 18 | 17 | 238085319357 | `cache_fill` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→— | — | — | — | — | — | 直接 parent（parent=17） | L3 行填充 |
| 17 | 19 | 18 | 238085319357 | `mshr_free` | L3 | 1 | addr_fallback | 415526 | s1 | — | 0xc5362700 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=18） | L3 MSHR 释放 |
| 18 | 20 | 19 | 238085319690 | `resp` | L3 | 1 | seq_primary | 415526 | s1 | 0xc5362708 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=19）；corr addr_fallback→seq_primary | L3 响应返回 |
| 19 | 21 | 20 | 238085319690 | `lq_complete` | L3 | 1 | seq_primary | 415526 | s1 | 0xffffff8001362708 | 0xc5362708 | — | —→— | — | — | — | — | — | 直接 parent（parent=20） | L3 load 完成 |
| 20 | 22 | 21 | 238085319690 | `taint_reg` | L4 | 1 | seq_primary | 415526 | s1 | 0xc5362708 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=21） | L4 污染寄存器 |
| 21 | 26 | 22 | 238085320689 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s1 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=22）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（21 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **2631**；代表故障 `fault_id=1` 的事件数 **2323**；进入最终 ancestry 的事件 **21**；未进入最终 ancestry 的同 fault 事件 **2302**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 535 | 27–1884 | 238085320689–238098636360 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `cache_access` | 303 | 11–2022 | 238085262414–238099691637 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 303 | 12–2023 | 238085262414–238099691637 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 20, 'hit': 283} | 无（outcome/contained 全空） |
| `request_fork` | 296 | 4294967296–4294967591 | 238085262414–238099691637 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `resp` | 272 | 23–2024 | 238085319691–238099691970 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 272 | 25–2025 | 238085319691–238099691970 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `lq_complete` | 247 | 24–2020 | 238085319691–238099649013 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_alloc` | 14 | 35–1061 | 238085324019–238087907100 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_fill` | 14 | 101–1084 | 238085383293–238087953054 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_fill` | 14 | 102–1085 | 238085383293–238087953054 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_free` | 14 | 103–1086 | 238085383293–238087953054 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `squash_masked` | 11 | 258–2016 | 238085615727–238099645684 | 不折叠：全部逐条点名（见下） | 预期非空（检测/含住事件）：outcome={'masked': 11} contained={'1': 11} |
| `mshr_merge` | 6 | 13–1011 | 238085262414–238087271736 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 238085262414 |
| L4 | `taint_reg` | 25 | 238085319691 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=535；event_id 范围 `27`–`1884`；tick 范围 `238085320689`–`238098636360`；corr 分布 {'taint_prop': 535}；outcome 分布 {'': 535}；contained 分布 {'': 535}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=272；event_id `25`–`2025`；tick `238085319691`–`238099691970`；distinct dyn_inst_seq=272；distinct phys_reg=164；distinct arch_reg=10；corr 分布 {'addr_fallback': 272}；outcome 分布 {'': 272}；contained 分布 {'': 272}；sample_run 分布 {'s1': 272}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 25 | 238085319691 | 24 | 415576 | 4/16 | clean→tainted | addr_fallback |
| 32 | 238085323686 | 31 | 415689 | 0/85 | clean→tainted | addr_fallback |
| 43 | 238085329680 | 42 | 415786 | 4/172 | clean→tainted | addr_fallback |
| 49 | 238085334009 | 48 | 415843 | 0/33 | clean→tainted | addr_fallback |
| 57 | 238085341668 | 56 | 415975 | 4/207 | clean→tainted | addr_fallback |
| 63 | 238085348328 | 62 | 416065 | 4/22 | clean→tainted | addr_fallback |
| 69 | 238085352657 | 68 | 416077 | 0/203 | clean→tainted | addr_fallback |
| 77 | 238085358651 | 76 | 416191 | 4/179 | clean→tainted | addr_fallback |
| 1989 | 238099342653 | 1988 | 445517 | —/— | clean→tainted | addr_fallback |
| 1996 | 238099636359 | 1995 | 445723 | 2/42 | clean→tainted | addr_fallback |
| 1999 | 238099636360 | 1998 | 445724 | 2/14 | clean→tainted | addr_fallback |
| 2003 | 238099639023 | 2002 | 445726 | —/— | clean→tainted | addr_fallback |
| 2008 | 238099639689 | 2007 | 445729 | 0/104 | clean→tainted | addr_fallback |
| 2015 | 238099645683 | 2014 | 445786 | 1/182 | clean→tainted | addr_fallback |
| 2021 | 238099649013 | 2020 | 445844 | 0/210 | clean→tainted | addr_fallback |
| 2025 | 238099691970 | 2024 | 445846 | —/— | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（272 条，不折叠，逐条列出）</b></summary>

25@238085319691(4/16) 32@238085323686(0/85) 43@238085329680(4/172) 49@238085334009(0/33) 57@238085341668(4/207) 63@238085348328(4/22) 69@238085352657(0/203) 77@238085358651(4/179)

83@238085362647(0/187) 91@238085373969(4/78) 97@238085381295(0/7) 111@238085386956(4/32) 117@238085393616(4/187) 123@238085401941(4/164) 129@238085408934(4/243) 135@238085415261(4/58)

141@238085443899(4/190) 147@238085450226(4/75) 153@238085456553(4/116) 159@238085464878(4/244) 165@238085471871(4/173) 171@238085478198(4/129) 177@238085488855(4/11) 183@238085500842(4/5)

189@238085507502(4/198) 195@238085515494(4/193) 201@238085522487(4/14) 207@238085528814(4/169) 213@238085552124(4/0) 219@238085558451(4/44) 225@238085564778(4/25) 231@238085573103(4/250)

237@238085580096(4/82) 243@238085586423(4/150) 249@238085597080(4/147) 255@238085609067(4/173) 263@238085620722(4/215) 269@238085632377(4/72) 275@238085639370(4/202) 284@238085651358(4/246)

290@238085677998(4/11) 295@238085684325(4/250) 300@238085694981(4/192) 306@238085703306(4/204) 312@238085710299(4/195) 318@238085717292(4/43) 324@238085727948(4/100) 330@238085739270(4/226)

336@238085745930(4/47) 342@238085753922(4/3) 348@238085760915(4/165) 354@238085767908(4/105) 360@238085790552(4/248) 366@238085796879(4/114) 372@238085803539(4/163) 378@238085811864(4/217)

384@238085818857(4/96) 390@238085825184(4/56) 396@238085835841(4/206) 402@238085847828(4/195) 407@238085854488(4/166) 413@238085862480(4/27) 419@238085869473(4/118) 425@238085875800(4/245)

431@238085899110(4/113) 437@238085905437(4/120) 443@238085911764(4/108) 449@238085920089(4/179) 454@238085927082(4/196) 460@238085933409(4/138) 466@238085944066(4/101) 472@238085956053(4/96)

477@238085962713(4/231) 483@238085970705(4/211) 489@238085977698(4/6) 495@238085984025(4/213) 501@238086007335(4/210) 507@238086013662(4/51) 513@238086019989(4/137) 519@238086028314(4/254)

525@238086035307(4/192) 530@238086041634(4/230) 536@238086052291(4/255) 542@238086064278(4/196) 547@238086070938(4/147) 552@238086078930(4/105) 557@238086085923(4/42) 562@238086092250(4/20)

568@238086115560(4/171) 574@238086121887(4/44) 582@238086133209(4/235) 588@238086144864(4/232) 594@238086151857(4/145) 603@238086163845(4/153) 609@238086177832(4/124) 615@238086189819(4/13)

621@238086196479(4/248) 626@238086204471(4/56) 631@238086211464(4/131) 637@238086217791(4/250) 642@238086241101(4/211) 647@238086247428(4/223) 653@238086253755(4/96) 658@238086262080(4/95)

664@238086269073(4/73) 670@238086275400(4/118) 675@238086286057(4/10) 681@238086298044(4/145) 686@238086304704(4/244) 691@238086312696(4/35) 697@238086319689(4/11) 702@238086326016(4/136)

710@238086345330(2/84) 713@238086345331(1/185) 720@238086346329(2/201) 741@238086562113(1/221) 747@238086564111(4/179) 752@238086743598(2/113) 757@238086743931(2/143) 762@238086745929(—/—)

767@238086747594(2/156) 773@238086805869(—/—) 781@238086870138(0/255) 784@238086870139(0/215) 788@238086872469(—/—) 793@238086874134(0/138) 818@238086945729(0/214) 828@238086985023(—/—)

833@238086991683(4/50) 839@238086996013(1/47) 853@238087048626(4/112) 862@238087056285(0/113) 867@238087066608(4/161) 872@238087072935(0/85) 884@238087160847(1/212) 890@238087170504(4/202)

901@238087191150(1/126) 906@238087191483(1/111) 913@238087193814(—/—) 918@238087196145(1/171) 923@238087196478(1/73) 928@238087198809(—/—) 935@238087207467(2/222) 938@238087207468(1/2)

953@238087212129(2/134) 956@238087212130(2/151) 961@238087214793(—/—) 982@238087255419(2/107) 991@238087259082(0/158) 1020@238087305036(21/98) 1023@238087305037(2/64) 1035@238087809531(0/244)

1040@238087881459(4/65) 1058@238087906768(0/208) 1066@238087917090(2/251) 1071@238087922418(0/75) 1083@238087952388(5/240) 1089@238087953387(24/242) 1192@238089255417(1/211) 1197@238089255750(1/215)

1202@238089258081(—/—) 1211@238089419253(2/126) 1214@238089419254(1/4) 1221@238089419919(2/64) 1224@238089419920(2/111) 1229@238089420585(0/59) 1237@238089422583(—/—) 1242@238089424248(0/149)

1248@238089478527(0/122) 1253@238089578427(0/67) 1258@238089708963(4/9) 1263@238089782556(2/213) 1267@238089784887(—/—) 1272@238089785553(2/97) 1276@238089787884(—/—) 1281@238089836502(1/127)

1286@238089840498(1/209) 1296@238090586751(5/197) 1305@238090633038(1/80) 1310@238090633039(6/171) 1313@238090633040(0/110) 1316@238090633371(0/174) 1328@238090695975(1/29) 1335@238090848156(4/238)

1343@238090974696(5/163) 1498@238092706296(5/231) 1544@238093197471(2/178) 1556@238093282054(2/108) 1562@238093496505(3/123) 1567@238094347653(0/200) 1572@238094443558(2/52) 1577@238094589745(2/56)

1582@238094725608(5/175) 1587@238095032301(5/135) 1592@238095073260(2/56) 1602@238095150850(2/208) 1607@238095441225(2/174) 1615@238095443556(1/155) 1620@238095443889(1/166) 1625@238095447219(0/9)

1630@238095447552(0/175) 1634@238095449550(—/—) 1639@238095451215(0/70) 1647@238095595737(0/132) 1651@238095598068(—/—) 1656@238095637695(0/81) 1660@238095642024(—/—) 1665@238095642690(0/218)

1670@238095725940(1/248) 1675@238095726273(1/232) 1681@238095729603(0/120) 1685@238095731934(—/—) 1698@238095746586(2/200) 1703@238095746587(2/92) 1706@238095746919(0/221) 1710@238095749250(—/—)

1715@238095750915(0/104) 1721@238095771228(0/126) 1725@238095773559(—/—) 1730@238095817515(0/209) 1734@238095819846(—/—) 1739@238095821511(0/176) 1747@238095894105(2/32) 1752@238096178821(1/130)

1757@238096323675(4/181) 1762@238096426905(2/20) 1767@238096430568(2/98) 1772@238096434231(2/170) 1780@238096716948(4/30) 1785@238096732600(2/9) 1790@238096736595(2/159) 1795@238096740258(2/106)

1803@238096762236(3/81) 1811@238096984015(3/87) 1817@238097269062(5/99) 1822@238097318346(5/30) 1829@238097489841(5/16) 1834@238097546118(2/72) 1847@238097606724(5/211) 1852@238098309021(2/96)

1860@238098336994(2/63) 1865@238098337993(2/57) 1876@238098575754(1/180) 1881@238098635028(1/129) 1889@238098642354(0/54) 1894@238098642687(0/103) 1898@238098644685(—/—) 1903@238098646350(0/183)

1907@238098648681(—/—) 1912@238098650346(0/199) 1917@238098662334(1/2) 1922@238098662667(1/141) 1927@238098665997(0/207) 1931@238098668328(—/—) 1936@238098680316(2/64) 1948@238098683979(2/173)

1951@238098683980(2/149) 1955@238098734263(—/—) 1960@238098734928(0/105) 1965@238098764898(4/159) 1970@238098776886(4/103) 1975@238099336659(1/132) 1980@238099336992(1/95) 1985@238099340322(0/3)

1989@238099342653(—/—) 1996@238099636359(2/42) 1999@238099636360(2/14) 2003@238099639023(—/—) 2008@238099639689(0/104) 2015@238099645683(1/182) 2021@238099649013(0/210) 2025@238099691970(—/—)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（303 条，不折叠）</b></summary>

12@238085262414:miss 29@238085323353:hit 34@238085324019:miss 37@238085324352:miss 40@238085329347:hit 46@238085333676:hit 51@238085334342:miss 54@238085341335:hit

60@238085347995:hit 66@238085352324:hit 71@238085352990:miss 74@238085358318:hit 80@238085362314:hit 85@238085362980:miss 88@238085373636:hit 94@238085380962:hit

99@238085381961:miss 108@238085386623:hit 114@238085393283:hit 120@238085401608:hit 126@238085408601:hit 132@238085414928:hit 138@238085443566:hit 144@238085449893:hit

150@238085456220:hit 156@238085464545:hit 162@238085471538:hit 168@238085477865:hit 174@238085488521:hit 180@238085500509:hit 186@238085507169:hit 192@238085515161:hit

198@238085522154:hit 204@238085528481:hit 210@238085551791:hit 216@238085558118:hit 222@238085564445:hit 228@238085572770:hit 234@238085579763:hit 240@238085586090:hit

246@238085596746:hit 252@238085608734:hit 257@238085615394:hit 260@238085620389:hit 266@238085632044:hit 272@238085639037:hit 278@238085646030:hit 281@238085651025:hit

287@238085677665:hit 292@238085683992:hit 297@238085694648:hit 303@238085702973:hit 309@238085709966:hit 315@238085716959:hit 321@238085727615:hit 327@238085738937:hit

333@238085745597:hit 339@238085753589:hit 345@238085760582:hit 351@238085767575:hit 357@238085790219:hit 363@238085796546:hit 369@238085803206:hit 375@238085811531:hit

381@238085818524:hit 387@238085824851:hit 393@238085835507:hit 399@238085847495:hit 404@238085854155:hit 410@238085862147:hit 416@238085869140:hit 422@238085875467:hit

428@238085898777:hit 434@238085905104:hit 440@238085911431:hit 446@238085919756:hit 451@238085926749:hit 457@238085933076:hit 463@238085943732:hit 469@238085955720:hit

474@238085962380:hit 480@238085970372:hit 486@238085977365:hit 492@238085983692:hit 498@238086007002:hit 504@238086013329:hit 510@238086019656:hit 516@238086027981:hit

522@238086034974:hit 527@238086041301:hit 533@238086051957:hit 539@238086063945:hit 544@238086070605:hit 549@238086078597:hit 554@238086085590:hit 559@238086091917:hit

565@238086115227:hit 571@238086121554:hit 576@238086127881:hit 579@238086132876:hit 585@238086144531:hit 591@238086151524:hit 597@238086158517:hit 600@238086163512:hit

606@238086177498:hit 612@238086189486:hit 618@238086196146:hit 623@238086204138:hit 628@238086211131:hit 634@238086217458:hit 639@238086240768:hit 644@238086247095:hit

650@238086253422:hit 655@238086261747:hit 661@238086268740:hit 667@238086275067:hit 672@238086285723:hit 678@238086297711:hit 683@238086304371:hit 688@238086312363:hit

694@238086319356:hit 699@238086325683:hit 705@238086344997:hit 707@238086344997:hit 715@238086345996:hit 717@238086345996:hit 727@238086516159:miss 730@238086516492:miss

744@238086563778:hit 749@238086743265:hit 754@238086743598:hit 760@238086745596:hit 764@238086747261:hit 771@238086805536:hit 776@238086869805:hit 778@238086869805:hit

786@238086872136:hit 790@238086873801:hit 809@238086939069:miss 812@238086939402:miss 815@238086945396:hit 830@238086991350:hit 836@238086995679:hit 850@238087048293:hit

856@238087052955:hit 859@238087055952:hit 864@238087066275:hit 869@238087072602:hit 881@238087160514:hit 887@238087170171:hit 892@238087178829:miss 895@238087179162:miss

898@238087190817:hit 903@238087191150:hit 911@238087193481:hit 915@238087195812:hit 920@238087196145:hit 926@238087198476:hit 930@238087207134:hit 932@238087207134:hit

948@238087211796:hit 950@238087211796:hit 959@238087214460:hit 977@238087255086:hit 988@238087258749:hit 993@238087259082:miss 996@238087259415:miss 1010@238087271736:miss

1032@238087809198:hit 1037@238087881126:hit 1046@238087906434:miss 1049@238087906434:hit 1051@238087906767:miss 1054@238087906767:miss 1060@238087907100:miss 1063@238087916757:hit

1068@238087922085:hit 1189@238089255084:hit 1194@238089255417:hit 1200@238089257748:hit 1206@238089418920:hit 1208@238089418920:hit 1216@238089419586:hit 1218@238089419586:hit

1226@238089420252:hit 1235@238089422250:hit 1239@238089423915:hit 1245@238089478194:hit 1250@238089578094:hit 1255@238089708630:hit 1260@238089782223:hit 1265@238089784554:hit

1269@238089785220:hit 1274@238089787551:hit 1278@238089836169:hit 1283@238089840165:hit 1293@238090586418:hit 1298@238090632705:hit 1300@238090632705:hit 1302@238090632705:hit

1307@238090633038:hit 1325@238090695642:hit 1332@238090847823:hit 1340@238090974363:hit 1413@238091433903:hit 1495@238092705963:hit 1541@238093197138:hit 1548@238093199469:hit

1551@238093214121:hit 1553@238093281720:hit 1559@238093496172:hit 1564@238094347320:hit 1569@238094443224:hit 1574@238094589411:hit 1579@238094725275:hit 1584@238095031968:hit

1589@238095072927:hit 1594@238095074592:hit 1597@238095146187:hit 1599@238095150516:hit 1604@238095440892:hit 1612@238095443223:hit 1617@238095443556:hit 1622@238095446886:hit

1627@238095447219:hit 1632@238095449217:hit 1636@238095450882:hit 1644@238095595404:hit 1649@238095597735:hit 1653@238095637362:hit 1658@238095641691:hit 1662@238095642357:hit

1667@238095725607:hit 1672@238095725940:hit 1678@238095729270:hit 1683@238095731601:hit 1690@238095743256:hit 1693@238095746253:hit 1695@238095746253:hit 1700@238095746586:hit

1708@238095748917:hit 1712@238095750582:hit 1718@238095770895:hit 1723@238095773226:hit 1727@238095817182:hit 1732@238095819513:hit 1736@238095821178:hit 1744@238095893772:hit

1749@238096178487:hit 1754@238096323342:hit 1759@238096426572:hit 1764@238096430235:hit 1769@238096433898:hit 1777@238096716615:hit 1782@238096732266:hit 1787@238096736262:hit

1792@238096739925:hit 1800@238096761903:hit 1808@238096983681:hit 1814@238097268729:hit 1819@238097318013:hit 1824@238097447217:hit 1826@238097489508:hit 1831@238097545785:hit

1839@238097547783:hit 1842@238097570094:hit 1844@238097606391:hit 1849@238098308688:hit 1857@238098336660:hit 1862@238098337659:hit 1873@238098575421:hit 1878@238098634695:hit

1886@238098642021:hit 1891@238098642354:hit 1896@238098644352:hit 1900@238098646017:hit 1905@238098648348:hit 1909@238098650013:hit 1914@238098662001:hit 1919@238098662334:hit

1924@238098665664:hit 1929@238098667995:hit 1933@238098679983:hit 1938@238098680316:hit 1940@238098680316:hit 1943@238098683646:hit 1945@238098683646:hit 1953@238098733929:hit

1957@238098734595:hit 1962@238098764565:hit 1967@238098776553:hit 1972@238099336326:hit 1977@238099336659:hit 1982@238099339989:hit 1987@238099342320:hit 1991@238099636026:hit

1993@238099636026:hit 2001@238099638690:hit 2005@238099639356:hit 2010@238099645350:hit 2012@238099645350:hit 2018@238099648680:hit 2023@238099691637:hit

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（48 条，不折叠）</b></summary>

13@238085262414:mshr_merge:mshr=2,fill=— 35@238085324019:mshr_alloc:mshr=3,fill=— 38@238085324352:mshr_alloc:mshr=4,fill=— 52@238085334342:mshr_merge:mshr=4,fill=—

72@238085352990:mshr_merge:mshr=4,fill=— 86@238085362980:mshr_merge:mshr=4,fill=— 100@238085381961:mshr_merge:mshr=4,fill=— 101@238085383293:mshr_fill:mshr=4,fill=3

103@238085383293:mshr_free:mshr=4,fill=— 104@238085383959:mshr_fill:mshr=0,fill=4 106@238085383959:mshr_free:mshr=0,fill=— 728@238086516159:mshr_alloc:mshr=5,fill=—

731@238086516492:mshr_alloc:mshr=6,fill=— 733@238086561114:mshr_fill:mshr=6,fill=5 735@238086561114:mshr_free:mshr=6,fill=— 736@238086561780:mshr_fill:mshr=0,fill=6

738@238086561780:mshr_free:mshr=0,fill=— 810@238086939069:mshr_alloc:mshr=7,fill=— 813@238086939402:mshr_alloc:mshr=8,fill=— 821@238086984024:mshr_fill:mshr=8,fill=7

823@238086984024:mshr_free:mshr=8,fill=— 824@238086984690:mshr_fill:mshr=0,fill=8 826@238086984690:mshr_free:mshr=0,fill=— 893@238087178829:mshr_alloc:mshr=9,fill=—

896@238087179162:mshr_alloc:mshr=10,fill=— 963@238087223784:mshr_fill:mshr=10,fill=9 965@238087223784:mshr_free:mshr=10,fill=— 966@238087224450:mshr_fill:mshr=0,fill=10

968@238087224450:mshr_free:mshr=0,fill=— 994@238087259082:mshr_alloc:mshr=11,fill=— 997@238087259415:mshr_alloc:mshr=12,fill=— 1011@238087271736:mshr_merge:mshr=12,fill=—

1012@238087304037:mshr_fill:mshr=12,fill=11 1014@238087304037:mshr_free:mshr=12,fill=— 1015@238087304703:mshr_fill:mshr=0,fill=12 1017@238087304703:mshr_free:mshr=0,fill=—

1047@238087906434:mshr_alloc:mshr=13,fill=— 1052@238087906767:mshr_alloc:mshr=14,fill=— 1055@238087906767:mshr_alloc:mshr=15,fill=— 1061@238087907100:mshr_alloc:mshr=16,fill=—

1072@238087951389:mshr_fill:mshr=14,fill=13 1074@238087951389:mshr_free:mshr=14,fill=— 1075@238087952055:mshr_fill:mshr=0,fill=14 1077@238087952055:mshr_free:mshr=0,fill=—

1078@238087952055:mshr_fill:mshr=16,fill=15 1080@238087952055:mshr_free:mshr=16,fill=— 1084@238087953054:mshr_fill:mshr=0,fill=16 1086@238087953054:mshr_free:mshr=0,fill=—

</details>

**`squash_masked` 旁支（不折叠，全部点名）**：共 11 条，均为同一 fault 的 L4 contain-by-squash 见证；只有主链上的那一条（若 terminal 为 L4 含住）或权威报告 containment.metrics 指定的一条是终局见证。

| event_id | tick | parent | VA | PA | dyn_inst_seq | containment_reason |
|---|---|---|---|---|---|---|
| 258 | 238085615727 | 250 | 0xffffff8001362708 | 0xc5362708 | 418557 | squash_replay |
| 279 | 238085646363 | 276 | 0xffffff8001362708 | 0xc5362708 | 418835 | squash_replay |
| 577 | 238086128214 | 569 | 0xffffff8001362708 | 0xc5362708 | 423113 | squash_replay |
| 598 | 238086158850 | 595 | 0xffffff8001362708 | 0xc5362708 | 423391 | squash_replay |
| 721 | 238086346330 | 703 | 0xffffff8001362708 | 0xc5362708 | 424999 | squash_replay |
| 857 | 238087053288 | 854 | 0xffffff80013629e4 | 0xc53629e4 | 425741 | squash_replay |
| 1595 | 238095074925 | 1557 | 0xffffff8001362b58 | 0xc5362b58 | 438047 | squash_replay |
| 1691 | 238095743589 | 1688 | 0xffffff8001362708 | 0xc5362708 | 439355 | squash_replay |
| 1840 | 238097548117 | 1837 | 0xffffff8001362b58 | 0xc5362b58 | 442443 | squash_replay |
| 1941 | 238098680649 | 1884 | 0xffffff8001362708 | 0xc5362708 | 445034 | squash_replay |
| 2016 | 238099645684 | 1941 | 0xffffff8001362708 | 0xc5362708 | 445788 | squash_replay |

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 296 条；event_id `4294967296`–`4294967591`；tick `238085262414`–`238099691637`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 238085262414 | 415526 | 415576 | 10→11 | 0xc5362000+1000 |
| 4294967297 | 238085323353 | 415526 | 415689 | 22→28 | 0xc5362000+1000 |
| 4294967298 | 238085324019 | 415526 | 415692 | 22→33 | 0xc5362000+1000 |
| 4294967299 | 238085329347 | 415526 | 415786 | 22→39 | 0xc5362000+1000 |
| 4294967300 | 238085333676 | 415526 | 415843 | 22→45 | 0xc5362000+1000 |
| 4294967587 | 238099639356 | 415526 | 445729 | 22→2004 | 0xc5362000+1000 |
| 4294967588 | 238099645350 | 415526 | 445786 | 22→2009 | 0xc5362000+1000 |
| 4294967589 | 238099645350 | 415526 | 445788 | 22→2011 | 0xc5362000+1000 |
| 4294967590 | 238099648680 | 415526 | 445844 | 22→2017 | 0xc5362000+1000 |
| 4294967591 | 238099691637 | 415526 | 445846 | 22→2022 | 0xc5362000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`2295`；tick=`238693668732`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 3 个 fault；本文件的代表故障 `fault_id=1` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'full': 1, 'detected_contained': 1, 'provable_to_L4_then_unknown': 1}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1（代表） | full | L5 | 2323 |
| 2 | detected_contained | L5 | 241 |
| 3 | provable_to_L4_then_unknown | L4 | 67 |

**为什么主链选的是 L5 逃逸而不是这些 L4 含住旁支**：本 seed 的权威判定采用 escape-first 规则——只要**任一** fault 到达 `full`（真实 errant_commit 逃逸），样本 headline 就是 `full`；squash 类含住证据在同一链上存在可证 L0→L5 逃逸路径时必须让位（`errant_escape_outranks_containment`）。这些旁支 `squash_masked` 是同一故障的其它 load 实例，不改变代表故障的逃逸终局。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`26` tick=`238085320689`（parent=`22`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=329; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 21 events |
| 3_tick_order | PASS | ticks 238085259417..238085320689 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=26 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (21); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T02-F2-W1 and seed1 |
| 12_tier_matches_evidence | PASS | matrix=F2 run.out=CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/prop_evt.txt.gz` | `09123a77e98c32503b479e026ff8dc43ad0eb3aefa4de349ae4010003f9a212c` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/chain_report.json` | `85c328179d1847d316c81aa30d1c42f12592caf154d7c514cf1a14bf867e3def` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/manifest.json` | `5e351346f7a7002e9f05f26b3e26bd0e4b8909d8ecf10402e2fd5c0a9b0ed04b` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/run.out` | `ecd786ebbd64e990c68c99c0473c490349284258b374111b82bd96fb86854cf8` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/run.err` | `17db81ed631aa13198beb85b2a55b70862d3f35789a6e64ac32805456268ba1d` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s1/T02-F2-W1/seed1/stats.txt` | `8b5284423283c9ee642c6443f2818f4eec633b0f092437b8e2e4ac72bedebef6` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
