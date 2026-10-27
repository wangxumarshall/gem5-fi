# T03-F5-W4 seed2 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T03-F5-W4` seed2 中，注入器于 tick=237950747064 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81362` 改成 `0x81366`（VA=`0xffffff8001362700`）；故障 PFN 使有效 PA 从 `0x81362700` 变为 `0x81366700`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=21, tick=237950808669）在 L5 形成真实错误提交；运行结局 Timeout（受控 Timeout（TIMEOUT triggered=True graceful=True signal=None exit=0 (budget 5400s exhausted; child finalized on SIGINT — evidence complete)））。

## 实验身份与证据来源

- RunID: `T03-F5-W4`
- seed: `2`；sample_run_id: `s2`
- 实验模型: 模型ID=`T03`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `卡死`
- 故障模型: 选PPN某bit stuck-at-0/1，对每次TLB读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F5` — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier: `F5`；effective tier: `F5`；tier enabled: `开启(1)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- source head: `38122675b91e05aaa0d636d14a89b6c6a90ea53c`
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/prop_evt.txt.gz`
- prop_evt SHA-256: `24af59b714fef58de59e9b9d1084d2828f3ad37f51fb27ad22e2caac0d72a26f`（本次重算值；字节数 451538）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/chain_report.json`
- chain_report SHA-256: `efcf3e78cf316758a1c7012a5d74d74714d0f78d721df6bc456c76ea2aa2dd42`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/manifest.json`（SHA-256 `02bae551fd1170b70f780ebdb4ecb0827863591cd3f3f606c91a5c8e3e567d8d`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/run.out`（SHA-256 `311615823fb7199600b4c382bbe3572332a8d0ea3b008c3998680550fd3b3d04`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/run.err`（SHA-256 `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/stats.txt`（SHA-256 `1511491e101ee8f4eee64c8550fe6b9e8a7af046cd51cc9d6cd4a0ee6a689f68`；`board.chaos_armtlb.numFaultsInjected=7`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 12084；代表故障 `fault_id=1` 事件数: 2328；权威报告 fault 数: 7
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffff8001362700，PFN 0x81362→0x81366，PA 0x81362700→0x81366700 → TLB 地址翻译 → LQ request_id=111 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → 受控 Timeout（预算耗尽）`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `stuck_at_one` 从 `81362` 变成 `81366`（mask=0x4；PFN 0x81362→0x81366），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950747064`；fault_id=`1`；corr=`origin`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffff8001362700`
  - 值变化：before=`81362`→after=`81366`；field=`stuck_at_one`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950747064, Site: arm_tlb_lookup_hit, VA: 0xffffff8001362700, old_pfn: 0x81362, new_pfn: 0x81366, FaultType: stuck_at_one, Mask: 0x4, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=264672881 eligible=264672881 injected=7 first_eligible_tick=237950233578 last_eligible_tick=436072491000 fires=264672881 no_effect=264672874 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950747064`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffff8001362700`；PFN=`81362`→`81366`
  - 值变化：before=`81362`→after=`81366`；field=`post_lookup`；state_before=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362700`；state_after=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81366;ap=0;mtype=2;page_size=1000;pa=81366700`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81362`→`81366`；pa `81362700`→`81366700`
- **event_id=`2`；parent_event_id=`1`；tick=`237950747064`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffff8001362700`；PA=`0x81366700`；PFN=`81362`→`81366`
  - 值变化：before=`81362`→after=`81366`；field=`stuck_at_one`；state_before=`81362700`；state_after=`81366700`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`237950747064`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffff8001362700`；PA=`0x81366700`
  - 值变化：before=`81362700`→after=`81366700`；field=`effective_pa_changed`；state_before=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81362;ap=0;mtype=2;page_size=1000;pa=81362700`；state_after=`vpn=ffffff8001362;asid=206;valid=1;global=1;pfn=81366;ap=0;mtype=2;page_size=1000;pa=81366700`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`81362700`，effective=`81366700`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`4`；parent_event_id=`3`；tick=`237950747397`；fault_id=`1`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`111`**
  - 硬件结构/事件：该访存指令进入 LQ（load）或 SQ（store）结构，携带被污染的地址。
  - 地址/身份：VA=`0xffffff8001362700`；lq_idx=`2`；sq_idx=`-1`
  - 值变化：field=`load`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`5`；parent_event_id=`4`；tick=`237950747397`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：LQ 读出该 load 的地址/请求；地址中已包含错误 PFN 带来的错误 PA。
  - 地址/身份：VA=`0xffffff8001362700`；lq_idx=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`6`；parent_event_id=`5`；tick=`237950747397`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffff8001362700`；PA=`0x81366700`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`7`；parent_event_id=`6`；tick=`237950747397`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x81366700`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`8`；parent_event_id=`7`；tick=`237950747397`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x81366700`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x81366700`
- **event_id=`9`；parent_event_id=`8`；tick=`237950747730`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffff8001362700`；PA=`0x81366700`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`10`；parent_event_id=`9`；tick=`237950747730`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x81366700`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`11`；parent_event_id=`10`；tick=`237950747730`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x81366700`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81366700`
- **event_id=`12`；parent_event_id=`11`；tick=`237950806671`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x81366700`；mshr_id=`2`；fill_id=`1`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81366700`；fill_id=`1`
- **event_id=`13`；parent_event_id=`12`；tick=`237950806671`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x81366700`；cache_line=`0x81366700`；fill_id=`1`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`14`；parent_event_id=`13`；tick=`237950806671`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x81366700`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81366700`
- **event_id=`15`；parent_event_id=`14`；tick=`237950807337`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x81366700`；mshr_id=`0`；fill_id=`2`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x81366700`；fill_id=`2`
- **event_id=`16`；parent_event_id=`15`；tick=`237950807337`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x81366700`；cache_line=`0x81366700`；fill_id=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`17`；parent_event_id=`16`；tick=`237950807337`；fault_id=`1`；corr=`addr_fallback`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x81366700`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x81366700`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`18`；parent_event_id=`17`；tick=`237950807670`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x81366700`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`19`；parent_event_id=`18`；tick=`237950807670`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0xffffff8001362700`；PA=`0x81366700`；lq_idx=`2`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`20`；parent_event_id=`19`；tick=`237950807670`；fault_id=`1`；corr=`seq_primary`；request_id=`111`；dyn_inst_seq=`111`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x81366700`；arch_reg=`19`/phys_reg=`98`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`21`；parent_event_id=`20`；tick=`237950808669`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`111`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`21`, tick=`237950808669`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Timeout`；实际表现：受控 Timeout（TIMEOUT triggered=True graceful=True signal=None exit=0 (budget 5400s exhausted; child finalized on SIGINT — evidence complete)）。

run.out 的 CHAOS_DETECT 行（共 3 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237950808669 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=436072508316 ptag=5 reason=store_discarded_not_retired`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=436072508316 ptag=6 reason=store_discarded_not_retired`

说明：受控 Timeout（预算耗尽、graceful）是**运行级**结局；代表链的真实 L5 逃逸（若 terminal=`full`）已经发生，不因 Timeout 抹去；两者并列保留。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950747064 | `inj` | L0 | 1 | origin | 111 | s2 | 0xffffff8001362700 | — | 0x81362→0x81366 | 81362→81366 | 0x4 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950747064 | `tlb_lookup` | L1 | 1 | seq_primary | 111 | s2 | 0xffffff8001362700 | — | 0x81362→0x81366 | 81362→81366 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 2 | 1 | 237950747064 | `tlb_pfn` | L2 | 1 | seq_primary | 111 | s2 | 0xffffff8001362700 | 0x81366700 | 0x81362→0x81366 | 81362→81366 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950747064 | `tlb_translate_result` | L2 | 1 | seq_primary | 111 | s2 | 0xffffff8001362700 | 0x81366700 | — | 81362700→81366700 | — | 0 | — | NoFault | — | 直接 parent（parent=2） | L2 翻译结果/含住点 |
| 5 | 4 | 3 | 237950747397 | `lsq_push` | L3 | 1 | seq_primary | — | s2 | 0xffffff8001362700 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 进入 LQ/SQ |
| 6 | 5 | 4 | 237950747397 | `lq_read` | L3 | 1 | seq_primary | 111 | s2 | 0xffffff8001362700 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=4） | L3 读取 load 请求 |
| 7 | 6 | 5 | 237950747397 | `cache_access` | L3 | 1 | addr_fallback | 111 | s2 | 0xffffff8001362700 | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=5）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 8 | 7 | 6 | 237950747397 | `cache_return` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=6） | L3 hit/miss 决策 |
| 9 | 8 | 7 | 237950747397 | `mshr_alloc` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=7） | L3 MSHR 分配 |
| 10 | 9 | 8 | 237950747730 | `cache_access` | L3 | 1 | addr_fallback | 111 | s2 | 0xffffff8001362700 | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=8） | L3 cache 查找 |
| 11 | 10 | 9 | 237950747730 | `cache_return` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=9） | L3 hit/miss 决策 |
| 12 | 11 | 10 | 237950747730 | `mshr_alloc` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=10） | L3 MSHR 分配 |
| 13 | 12 | 11 | 237950806671 | `mshr_fill` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→filled | — | — | — | — | — | 直接 parent（parent=11） | L3 MSHR 填充 |
| 14 | 13 | 12 | 237950806671 | `cache_fill` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=12） | L3 行填充 |
| 15 | 14 | 13 | 237950806671 | `mshr_free` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=13） | L3 MSHR 释放 |
| 16 | 15 | 14 | 237950807337 | `mshr_fill` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→filled | — | — | — | — | — | 直接 parent（parent=14） | L3 MSHR 填充 |
| 17 | 16 | 15 | 237950807337 | `cache_fill` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=15） | L3 行填充 |
| 18 | 17 | 16 | 237950807337 | `mshr_free` | L3 | 1 | addr_fallback | 111 | s2 | — | 0x81366700 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=16） | L3 MSHR 释放 |
| 19 | 18 | 17 | 237950807670 | `resp` | L3 | 1 | seq_primary | 111 | s2 | 0x81366700 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=17）；corr addr_fallback→seq_primary | L3 响应返回 |
| 20 | 19 | 18 | 237950807670 | `lq_complete` | L3 | 1 | seq_primary | 111 | s2 | 0xffffff8001362700 | 0x81366700 | — | —→— | — | — | — | — | — | 直接 parent（parent=18） | L3 load 完成 |
| 21 | 20 | 19 | 237950807670 | `taint_reg` | L4 | 1 | seq_primary | 111 | s2 | 0x81366700 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=19） | L4 污染寄存器 |
| 22 | 21 | 20 | 237950808669 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s2 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=20）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（22 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **12084**；代表故障 `fault_id=1` 的事件数 **2328**；进入最终 ancestry 的事件 **22**；未进入最终 ancestry 的同 fault 事件 **2306**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 544 | 22–9766 | 237950808669–237970487970 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `request_fork` | 296 | 4294967297–4294968773 | 237950884260–237970727064 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `cache_access` | 296 | 60–9843 | 237950884260–237970727064 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 296 | 61–9844 | 237950884260–237970727064 | 不折叠：全量 hit/miss 索引（见下）；分布 {'hit': 296} | 无（outcome/contained 全空） |
| `resp` | 296 | 62–9845 | 237950884593–237970727397 | 计数 + 范围 | 无（outcome/contained 全空） |
| `taint_reg` | 296 | 64–9847 | 237950884593–237970727397 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `lq_complete` | 281 | 63–9846 | 237950884593–237970727397 | 计数 + 范围 | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967297 | 237950884260 |
| L4 | `consumer` | 22 | 237950808669 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=544；event_id 范围 `22`–`9766`；tick 范围 `237950808669`–`237970487970`；corr 分布 {'taint_prop': 544}；outcome 分布 {'': 544}；contained 分布 {'': 544}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=296；event_id `64`–`9847`；tick `237950884593`–`237970727397`；distinct dyn_inst_seq=296；distinct phys_reg=149；distinct arch_reg=6；corr 分布 {'addr_fallback': 296}；outcome 分布 {'': 296}；contained 分布 {'': 296}；sample_run 分布 {'s2': 296}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 64 | 237950884593 | 63 | 213 | 23/111 | clean→tainted | addr_fallback |
| 69 | 237951385092 | 68 | 500 | 2/154 | clean→tainted | addr_fallback |
| 141 | 237952218924 | 140 | 794 | 0/52 | clean→tainted | addr_fallback |
| 224 | 237952729080 | 223 | 1052 | 0/165 | clean→tainted | addr_fallback |
| 272 | 237953055087 | 271 | 1306 | 0/58 | clean→tainted | addr_fallback |
| 315 | 237953209599 | 314 | 1604 | 0/91 | clean→tainted | addr_fallback |
| 354 | 237953403072 | 353 | 1937 | 0/182 | clean→tainted | addr_fallback |
| 378 | 237953537937 | 377 | 2147 | 0/156 | clean→tainted | addr_fallback |
| 9771 | 237970513278 | 9770 | 59797 | 4/20 | clean→tainted | addr_fallback |
| 9781 | 237970515276 | 9780 | 59844 | 4/234 | clean→tainted | addr_fallback |
| 9786 | 237970516941 | 9785 | 59865 | 0/24 | clean→tainted | addr_fallback |
| 9796 | 237970521603 | 9795 | 59907 | 4/198 | clean→tainted | addr_fallback |
| 9804 | 237970561563 | 9803 | 60082 | 0/182 | clean→tainted | addr_fallback |
| 9818 | 237970616841 | 9817 | 60415 | 0/135 | clean→tainted | addr_fallback |
| 9833 | 237970672119 | 9832 | 60748 | 0/84 | clean→tainted | addr_fallback |
| 9847 | 237970727397 | 9846 | 61081 | 0/122 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（296 条，不折叠，逐条列出）</b></summary>

64@237950884593(23/111) 69@237951385092(2/154) 141@237952218924(0/52) 224@237952729080(0/165) 272@237953055087(0/58) 315@237953209599(0/91) 354@237953403072(0/182) 378@237953537937(0/156)

403@237953670471(0/174) 422@237953823318(0/184) 439@237954142998(0/234) 454@237954364776(0/182) 467@237954631842(0/156) 479@237954868272(0/174) 492@237955091382(0/184) 504@237955223583(0/234)

516@237955266207(0/182) 528@237955353786(0/156) 746@237955589883(0/174) 1083@237955811661(0/184) 1450@237956078727(0/234) 1809@237956301837(0/182) 2207@237956594544(0/156) 2532@237956831640(0/174)

2852@237957009462(0/184) 3170@237957187284(0/234) 3510@237957456681(0/182) 3941@237958073397(0/156) 4324@237958340463(0/174) 4685@237958563573(0/184) 5091@237958841961(0/234) 5425@237959079057(0/182)

5763@237959256879(0/156) 6083@237959434701(0/174) 6443@237959704098(0/184) 6768@237959885583(0/234) 6842@237960220248(0/56) 6845@237960220249(0/42) 6853@237960222912(—/—) 6858@237960223578(4/215)

6878@237960269872(4/48) 6886@237960271863(0/230) 6903@237960337131(3/187) 6912@237960536598(0/227) 6926@237961094040(0/106) 6952@237961413720(0/61) 6977@237961776690(0/58) 7003@237961885914(0/157)

7019@237961990809(0/103) 7033@237962049750(0/46) 7049@237962107692(0/28) 7052@237962107693(0/147) 7059@237962110356(—/—) 7069@237962112687(4/184) 7079@237962114020(0/160) 7084@237962118015(3/23)

7092@237962157975(0/241) 7107@237962213253(0/49) 7122@237962268531(0/117) 7138@237962323809(0/94) 7152@237962379087(0/250) 7166@237962434365(0/230) 7181@237962489643(0/120) 7199@237962547585(0/173)

7202@237962547586(0/241) 7209@237962550249(—/—) 7219@237962552580(4/102) 7229@237962553913(0/90) 7234@237962557908(3/3) 7242@237962597868(0/186) 7255@237962653146(0/109) 7270@237962708424(0/117)

7282@237962763702(0/116) 7295@237962818980(0/236) 7307@237962874258(0/137) 7317@237962929536(0/125) 7331@237962986146(0/63) 7334@237962986147(0/92) 7338@237962988810(—/—) 7348@237962991141(4/135)

7358@237962992474(0/43) 7363@237962996469(3/81) 7368@237963036429(0/112) 7382@237963091707(0/191) 7395@237963146985(0/182) 7409@237963202263(0/250) 7423@237963257541(0/68) 7438@237963312819(0/144)

7454@237963368097(0/125) 7470@237963424707(0/32) 7473@237963424708(0/50) 7480@237963427371(—/—) 7490@237963429702(4/160) 7500@237963431035(0/244) 7505@237963435030(3/230) 7513@237963474990(0/152)

7527@237963530268(0/61) 7541@237963585546(0/218) 7556@237963640824(0/174) 7571@237963696102(0/150) 7583@237963751380(0/131) 7596@237963806658(0/125) 7612@237963863268(0/10) 7615@237963863269(0/111)

7622@237963865932(—/—) 7632@237963868263(4/90) 7642@237963869596(0/140) 7647@237963873591(3/147) 7655@237963913551(0/184) 7669@237963968829(0/84) 7683@237964024107(0/24) 7697@237964079385(0/252)

7712@237964134663(0/31) 7723@237964189941(0/54) 7737@237964245219(0/125) 7752@237964301829(0/226) 7755@237964301830(0/175) 7762@237964304493(—/—) 7772@237964306824(4/43) 7782@237964308157(0/116)

7787@237964312152(3/55) 7795@237964352112(0/201) 7807@237964407390(0/168) 7819@237964462668(0/123) 7831@237964517946(0/187) 7843@237964573224(0/185) 7853@237964628502(0/110) 7865@237964683780(0/125)

7881@237964740390(0/8) 7884@237964740391(0/255) 7891@237964743054(—/—) 7901@237964745385(4/244) 7911@237964746718(0/250) 7916@237964750713(3/30) 7924@237964790673(0/64) 7938@237964845951(0/52)

7951@237964901229(0/119) 7966@237964956507(0/128) 7981@237965011785(0/247) 7992@237965067063(0/86) 8005@237965122341(0/125) 8021@237965178951(0/206) 8024@237965178952(0/42) 8031@237965181615(—/—)

8041@237965183946(4/140) 8051@237965185279(0/174) 8056@237965189274(3/149) 8064@237965229234(0/25) 8078@237965284512(0/196) 8091@237965339790(0/82) 8103@237965395068(0/229) 8117@237965450346(0/249)

8128@237965505624(0/20) 8141@237965560902(0/125) 8156@237965617512(0/211) 8159@237965617513(0/96) 8166@237965620176(—/—) 8176@237965622507(4/116) 8186@237965623840(0/252) 8191@237965627835(3/38)

8199@237965667795(0/51) 8213@237965723073(0/173) 8226@237965778351(0/9) 8240@237965833629(0/134) 8255@237965888907(0/126) 8267@237965944185(0/228) 8277@237965999463(0/125) 8289@237966056073(0/91)

8292@237966056074(0/107) 8297@237966058737(—/—) 8307@237966061068(4/250) 8317@237966062401(0/187) 8322@237966066396(3/102) 8327@237966106356(0/178) 8337@237966161634(0/63) 8347@237966216912(0/153)

8359@237966272190(0/214) 8373@237966327468(0/130) 8384@237966382746(0/193) 8397@237966438024(0/125) 8412@237966494634(0/213) 8415@237966494635(0/223) 8422@237966497298(—/—) 8432@237966499629(4/174)

8442@237966500962(0/128) 8447@237966504957(3/135) 8455@237966544917(0/39) 8468@237966600195(0/32) 8481@237966655473(0/17) 8496@237966710751(0/122) 8510@237966766029(0/3) 8520@237966821307(0/33)

8533@237966876585(0/125) 8548@237966933195(0/133) 8551@237966933196(0/194) 8557@237966935859(—/—) 8567@237966938190(4/252) 8577@237966939523(0/229) 8582@237966943518(3/160) 8589@237966983478(0/146)

8602@237967038756(0/10) 8615@237967094034(0/115) 8630@237967149312(0/5) 8644@237967204590(0/81) 8654@237967259868(0/176) 8666@237967315146(0/125) 8680@237967371756(0/98) 8683@237967371757(0/246)

8689@237967374420(—/—) 8699@237967376751(4/187) 8709@237967378084(0/134) 8714@237967382079(3/90) 8721@237967422039(0/1) 8734@237967477317(0/226) 8747@237967532595(0/85) 8759@237967587873(0/222)

8772@237967643151(0/230) 8782@237967698429(0/2) 8795@237967753707(0/125) 8808@237967810317(0/138) 8811@237967810318(0/237) 8815@237967812981(—/—) 8825@237967815312(4/128) 8835@237967816645(0/214)

8840@237967820640(3/43) 8845@237967860600(0/217) 8855@237967915878(0/8) 8868@237967971156(0/148) 8883@237968026434(0/203) 8897@237968081712(0/147) 8907@237968136990(0/46) 8920@237968192268(0/125)

8935@237968248878(0/177) 8938@237968248879(0/227) 8947@237968363097(4/90) 8957@237968366094(4/215) 8967@237968367427(0/145) 9016@237968416044(0/86) 9094@237968471322(0/53) 9159@237968526600(0/177)

9199@237968581878(0/192) 9232@237968637156(0/204) 9258@237968692434(0/48) 9278@237968749044(0/222) 9281@237968749045(0/58) 9292@237968800992(4/38) 9302@237968802657(4/191) 9307@237968803989(0/107)

9322@237968849277(0/226) 9339@237968904555(0/195) 9356@237968959833(0/142) 9372@237969015111(0/202) 9390@237969070389(0/213) 9403@237969125667(0/174) 9416@237969182277(0/197) 9427@237969231228(4/156)

9437@237969232893(4/227) 9442@237969234225(0/56) 9452@237969240219(4/59) 9460@237969279513(0/99) 9474@237969334791(0/150) 9485@237969390069(0/192) 9496@237969445347(0/33) 9506@237969500625(0/232)

9517@237969555903(0/230) 9527@237969612513(0/32) 9532@237969661464(4/244) 9542@237969663129(4/13) 9547@237969664461(0/160) 9557@237969669456(4/130) 9562@237969709749(0/23) 9572@237969765027(0/138)

9587@237969820305(0/116) 9600@237969875583(0/236) 9613@237969930861(0/121) 9626@237969986139(0/191) 9641@237970042749(0/106) 9651@237970087371(4/166) 9661@237970089369(4/91) 9666@237970091034(0/92)

9676@237970095696(4/247) 9684@237970135656(0/245) 9697@237970190934(0/153) 9710@237970246212(0/105) 9723@237970301490(0/65) 9737@237970356768(0/118) 9750@237970412046(0/114) 9763@237970468656(0/85)

9771@237970513278(4/20) 9781@237970515276(4/234) 9786@237970516941(0/24) 9796@237970521603(4/198) 9804@237970561563(0/182) 9818@237970616841(0/135) 9833@237970672119(0/84) 9847@237970727397(0/122)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（296 条，不折叠）</b></summary>

61@237950884260:hit 66@237951384759:hit 138@237952218591:hit 221@237952728747:hit 269@237953054754:hit 312@237953209266:hit 351@237953402739:hit 375@237953537604:hit

400@237953670138:hit 419@237953822985:hit 436@237954142665:hit 451@237954364443:hit 464@237954631509:hit 476@237954867939:hit 489@237955091049:hit 501@237955223250:hit

513@237955265874:hit 525@237955353453:hit 743@237955589550:hit 1080@237955811328:hit 1447@237956078394:hit 1806@237956301504:hit 2204@237956594211:hit 2529@237956831307:hit

2849@237957009129:hit 3167@237957186951:hit 3507@237957456348:hit 3938@237958073064:hit 4321@237958340130:hit 4682@237958563240:hit 5088@237958841628:hit 5422@237959078724:hit

5760@237959256546:hit 6080@237959434368:hit 6440@237959703765:hit 6765@237959885250:hit 6837@237960219915:hit 6839@237960219915:hit 6851@237960222579:hit 6855@237960223245:hit

6875@237960269532:hit 6883@237960271530:hit 6900@237960336798:hit 6909@237960536265:hit 6923@237961093707:hit 6949@237961413387:hit 6974@237961776357:hit 7000@237961885581:hit

7016@237961990476:hit 7030@237962049417:hit 7044@237962107359:hit 7046@237962107359:hit 7057@237962110023:hit 7066@237962112354:hit 7073@237962113686:hit 7081@237962117682:hit

7089@237962157642:hit 7104@237962212920:hit 7119@237962268198:hit 7135@237962323476:hit 7149@237962378754:hit 7163@237962434032:hit 7178@237962489310:hit 7194@237962547252:hit

7196@237962547252:hit 7207@237962549916:hit 7216@237962552247:hit 7223@237962553579:hit 7231@237962557575:hit 7239@237962597535:hit 7252@237962652813:hit 7267@237962708091:hit

7279@237962763369:hit 7292@237962818647:hit 7304@237962873925:hit 7314@237962929203:hit 7326@237962985813:hit 7328@237962985813:hit 7336@237962988477:hit 7345@237962990808:hit

7352@237962992140:hit 7360@237962996136:hit 7365@237963036096:hit 7379@237963091374:hit 7392@237963146652:hit 7406@237963201930:hit 7420@237963257208:hit 7435@237963312486:hit

7451@237963367764:hit 7465@237963424374:hit 7467@237963424374:hit 7478@237963427038:hit 7487@237963429369:hit 7494@237963430701:hit 7502@237963434697:hit 7510@237963474657:hit

7524@237963529935:hit 7538@237963585213:hit 7553@237963640491:hit 7568@237963695769:hit 7580@237963751047:hit 7593@237963806325:hit 7607@237963862935:hit 7609@237963862935:hit

7620@237963865599:hit 7629@237963867930:hit 7636@237963869262:hit 7644@237963873258:hit 7652@237963913218:hit 7666@237963968496:hit 7680@237964023774:hit 7694@237964079052:hit

7709@237964134330:hit 7720@237964189608:hit 7734@237964244886:hit 7747@237964301496:hit 7749@237964301496:hit 7760@237964304160:hit 7769@237964306491:hit 7776@237964307823:hit

7784@237964311819:hit 7792@237964351779:hit 7804@237964407057:hit 7816@237964462335:hit 7828@237964517613:hit 7840@237964572891:hit 7850@237964628169:hit 7862@237964683447:hit

7876@237964740057:hit 7878@237964740057:hit 7889@237964742721:hit 7898@237964745052:hit 7905@237964746384:hit 7913@237964750380:hit 7921@237964790340:hit 7935@237964845618:hit

7948@237964900896:hit 7963@237964956174:hit 7978@237965011452:hit 7989@237965066730:hit 8002@237965122008:hit 8016@237965178618:hit 8018@237965178618:hit 8029@237965181282:hit

8038@237965183613:hit 8045@237965184945:hit 8053@237965188941:hit 8061@237965228901:hit 8075@237965284179:hit 8088@237965339457:hit 8100@237965394735:hit 8114@237965450013:hit

8125@237965505291:hit 8138@237965560569:hit 8151@237965617179:hit 8153@237965617179:hit 8164@237965619843:hit 8173@237965622174:hit 8180@237965623506:hit 8188@237965627502:hit

8196@237965667462:hit 8210@237965722740:hit 8223@237965778018:hit 8237@237965833296:hit 8252@237965888574:hit 8264@237965943852:hit 8274@237965999130:hit 8284@237966055740:hit

8286@237966055740:hit 8295@237966058404:hit 8304@237966060735:hit 8311@237966062067:hit 8319@237966066063:hit 8324@237966106023:hit 8334@237966161301:hit 8344@237966216579:hit

8356@237966271857:hit 8370@237966327135:hit 8381@237966382413:hit 8394@237966437691:hit 8407@237966494301:hit 8409@237966494301:hit 8420@237966496965:hit 8429@237966499296:hit

8436@237966500628:hit 8444@237966504624:hit 8452@237966544584:hit 8465@237966599862:hit 8478@237966655140:hit 8493@237966710418:hit 8507@237966765696:hit 8517@237966820974:hit

8530@237966876252:hit 8543@237966932862:hit 8545@237966932862:hit 8555@237966935526:hit 8564@237966937857:hit 8571@237966939189:hit 8579@237966943185:hit 8586@237966983145:hit

8599@237967038423:hit 8612@237967093701:hit 8627@237967148979:hit 8641@237967204257:hit 8651@237967259535:hit 8663@237967314813:hit 8675@237967371423:hit 8677@237967371423:hit

8687@237967374087:hit 8696@237967376418:hit 8703@237967377750:hit 8711@237967381746:hit 8718@237967421706:hit 8731@237967476984:hit 8744@237967532262:hit 8756@237967587540:hit

8769@237967642818:hit 8779@237967698096:hit 8792@237967753374:hit 8803@237967809984:hit 8805@237967809984:hit 8813@237967812648:hit 8822@237967814979:hit 8829@237967816311:hit

8837@237967820307:hit 8842@237967860267:hit 8852@237967915545:hit 8865@237967970823:hit 8880@237968026101:hit 8894@237968081379:hit 8904@237968136657:hit 8917@237968191935:hit

8930@237968248545:hit 8932@237968248545:hit 8944@237968362764:hit 8954@237968365761:hit 8961@237968367093:hit 9013@237968415711:hit 9091@237968470989:hit 9156@237968526267:hit

9196@237968581545:hit 9229@237968636823:hit 9255@237968692101:hit 9273@237968748711:hit 9275@237968748711:hit 9289@237968800659:hit 9299@237968802324:hit 9304@237968803656:hit

9319@237968848944:hit 9336@237968904222:hit 9353@237968959500:hit 9369@237969014778:hit 9387@237969070056:hit 9400@237969125334:hit 9413@237969181944:hit 9424@237969230895:hit

9434@237969232560:hit 9439@237969233892:hit 9449@237969239886:hit 9457@237969279180:hit 9471@237969334458:hit 9482@237969389736:hit 9493@237969445014:hit 9503@237969500292:hit

9514@237969555570:hit 9524@237969612180:hit 9529@237969661131:hit 9539@237969662796:hit 9544@237969664128:hit 9554@237969669123:hit 9559@237969709416:hit 9569@237969764694:hit

9584@237969819972:hit 9597@237969875250:hit 9610@237969930528:hit 9623@237969985806:hit 9638@237970042416:hit 9648@237970087038:hit 9658@237970089036:hit 9663@237970090701:hit

9673@237970095363:hit 9681@237970135323:hit 9694@237970190601:hit 9707@237970245879:hit 9720@237970301157:hit 9734@237970356435:hit 9747@237970411713:hit 9760@237970468323:hit

9768@237970512945:hit 9778@237970514943:hit 9783@237970516608:hit 9793@237970521270:hit 9801@237970561230:hit 9815@237970616508:hit 9830@237970671786:hit 9844@237970727064:hit

</details>

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 296 条；event_id `4294967297`–`4294968773`；tick `237950884260`–`237970727064`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967297 | 237950884260 | 111 | 213 | 20→60 | 0x81366000+1000 |
| 4294967298 | 237951384759 | 111 | 500 | 20→65 | 0x81366000+1000 |
| 4294967299 | 237952218591 | 111 | 794 | 20→137 | 0x81366000+1000 |
| 4294967300 | 237952728747 | 111 | 1052 | 20→220 | 0x81366000+1000 |
| 4294967303 | 237953054754 | 111 | 1306 | 20→268 | 0x81366000+1000 |
| 4294968766 | 237970521270 | 111 | 59907 | 20→9792 | 0x81366000+1000 |
| 4294968767 | 237970561230 | 111 | 60082 | 20→9800 | 0x81366000+1000 |
| 4294968769 | 237970616508 | 111 | 60415 | 20→9814 | 0x81366000+1000 |
| 4294968771 | 237970671786 | 111 | 60748 | 20→9829 | 0x81366000+1000 |
| 4294968773 | 237970727064 | 111 | 61081 | 20→9843 | 0x81366000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`10530`；tick=`436072508316`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 7 个 fault；本文件的代表故障 `fault_id=1` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'full': 1, 'provable_to_L4_then_unknown': 6}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1（代表） | full | L5 | 2328 |
| 2 | provable_to_L4_then_unknown | L4 | 45 |
| 3 | provable_to_L4_then_unknown | L4 | 28 |
| 4 | provable_to_L4_then_unknown | L4 | 1456 |
| 5 | provable_to_L4_then_unknown | L4 | 3522 |
| 6 | provable_to_L4_then_unknown | L4 | 3514 |
| 7 | provable_to_L4_then_unknown | L4 | 1191 |

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`21` tick=`237950808669`（parent=`20`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=319; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 22 events |
| 3_tick_order | PASS | ticks 237950747064..237950808669 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=21 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (22); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T03-F5-W4 and seed2 |
| 12_tier_matches_evidence | PASS | matrix=F5 run.out=CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/prop_evt.txt.gz` | `24af59b714fef58de59e9b9d1084d2828f3ad37f51fb27ad22e2caac0d72a26f` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/chain_report.json` | `efcf3e78cf316758a1c7012a5d74d74714d0f78d721df6bc456c76ea2aa2dd42` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/manifest.json` | `02bae551fd1170b70f780ebdb4ecb0827863591cd3f3f606c91a5c8e3e567d8d` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/run.out` | `311615823fb7199600b4c382bbe3572332a8d0ea3b008c3998680550fd3b3d04` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s2/T03-F5-W4/seed2/stats.txt` | `1511491e101ee8f4eee64c8550fe6b9e8a7af046cd51cc9d6cd4a0ee6a689f68` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
