# T03-F5-W4 seed1 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T03-F5-W4` seed1 中，注入器于 tick=237951174969 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x80a16` 改成 `0x80a06`（VA=`0xffffffc008a16868`）；故障 PFN 使有效 PA 从 `0x80a16868` 变为 `0x80a06868`，随后沿 TLB 翻译 → LQ/SQ 请求 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=280, tick=237951250227）在 L5 形成真实错误提交；运行结局 Timeout（受控 Timeout（TIMEOUT triggered=True graceful=True signal=None exit=0 (budget 5400s exhausted; child finalized on SIGINT — evidence complete)））。

## 实验身份与证据来源

- RunID: `T03-F5-W4`
- seed: `1`；sample_run_id: `s1`
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
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/prop_evt.txt.gz`
- prop_evt SHA-256: `478530d46202e0d935d8876b2c7ff127a3e5830d9a159ff66d29c709f89fa7ab`（本次重算值；字节数 394904）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/chain_report.json`
- chain_report SHA-256: `535c63546e52ae889d7e3b239b02472921bddf510ee1fad567219cad9086d60e`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/manifest.json`（SHA-256 `edc14fcff3c1a38574b01efff323627fd35ed08016ad70811e7e257a707ed504`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/run.out`（SHA-256 `811b070ab12af7a53264530ece4c07a7e0fe2241d2899a230ed49d14a808cce0`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/run.err`（SHA-256 `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/stats.txt`（SHA-256 `b37a0b817a51a21b85a210e3d81405b60ae96995e37f0c5ee5f1070a852dfdfa`；`board.chaos_armtlb.numFaultsInjected=13`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 8327；代表故障 `fault_id=2` 事件数: 28；权威报告 fault 数: 13
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc008a16868，PFN 0x80a16→0x80a06，PA 0x80a16868→0x80a06868 → TLB 地址翻译 → LQ request_id=373 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → 受控 Timeout（预算耗尽）`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `stuck_at_zero` 从 `80a16` 变成 `80a06`（mask=0x10；PFN 0x80a16→0x80a06），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`259`；parent_event_id=`—`；tick=`237951174969`；fault_id=`2`；corr=`origin`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc008a16868`
  - 值变化：before=`80a16`→after=`80a06`；field=`stuck_at_zero`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237951174969, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a16868, old_pfn: 0x80a16, new_pfn: 0x80a06, FaultType: stuck_at_zero, Mask: 0x10, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=226252285 eligible=226252285 injected=13 first_eligible_tick=237950233578 last_eligible_tick=558263733111 fires=226252285 no_effect=226252272 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`260`；parent_event_id=`259`；tick=`237951174969`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc008a16868`；PFN=`80a16`→`80a06`
  - 值变化：before=`80a16`→after=`80a06`；field=`post_lookup`；state_before=`vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868`；state_after=`vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a06;ap=2;mtype=2;page_size=1000;pa=80a06868`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `80a16`→`80a06`；pa `80a16868`→`80a06868`
- **event_id=`261`；parent_event_id=`260`；tick=`237951174969`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc008a16868`；PA=`0x80a06868`；PFN=`80a16`→`80a06`
  - 值变化：before=`80a16`→after=`80a06`；field=`stuck_at_zero`；state_before=`80a16868`；state_after=`80a06868`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`262`；parent_event_id=`261`；tick=`237951174969`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffffc008a16868`；PA=`0x80a06868`
  - 值变化：before=`80a16868`→after=`80a06868`；field=`effective_pa_changed`；state_before=`vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a16;ap=2;mtype=2;page_size=1000;pa=80a16868`；state_after=`vpn=ffffffc008a16;asid=206;valid=1;global=1;pfn=80a06;ap=2;mtype=2;page_size=1000;pa=80a06868`
  - 检测/含住字段：detection_layer=`—`；contained=`0`；outcome=`NoFault`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_changed`（requested=`80a16868`，effective=`80a06868`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **确实改变**（`effective_pa_changed`），错误 PA 被写入请求，因此故障继续传给 L3 的 LQ/SQ 与 cache 访问。

### 第 3 步：进入 Load Queue 或 Store Queue

发生了什么：错误地址已进入 LSU 的请求结构（LQ/SQ），并沿请求路径发往 cache；跨请求处由 `request_fork` bridge 显式承载。

- **event_id=`263`；parent_event_id=`262`；tick=`237951175302`；fault_id=`2`；corr=`seq_primary`；request_id=`—`；dyn_inst_seq=`373`**
  - 硬件结构/事件：该访存指令进入 LQ（load）或 SQ（store）结构，携带被污染的地址。
  - 地址/身份：VA=`0xffffffc008a16868`；lq_idx=`6`；sq_idx=`-1`
  - 值变化：field=`load`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`264`；parent_event_id=`263`；tick=`237951175302`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：LQ 读出该 load 的地址/请求；地址中已包含错误 PFN 带来的错误 PA。
  - 地址/身份：VA=`0xffffffc008a16868`；lq_idx=`6`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - 为什么把故障传给下一步：错误地址已进入 LQ/SQ 请求并被发往 cache；物理请求携带错误 PA，故传给 L1D/MSHR。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`265`；parent_event_id=`264`；tick=`237951175302`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc008a16868`；PA=`0x80a06868`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`266`；parent_event_id=`265`；tick=`237951175302`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x80a06868`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`267`；parent_event_id=`266`；tick=`237951175302`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x80a06868`；mshr_id=`13`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`13`；cache_line=`0x80a06868`
- **event_id=`268`；parent_event_id=`267`；tick=`237951175635`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc008a16868`；PA=`0x80a06840`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`269`；parent_event_id=`268`；tick=`237951175635`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x80a06840`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`270`；parent_event_id=`269`；tick=`237951175635`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x80a06840`；mshr_id=`14`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`14`；cache_line=`0x80a06840`
- **event_id=`271`；parent_event_id=`270`；tick=`237951248562`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x80a06840`；mshr_id=`14`；fill_id=`13`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`14`；cache_line=`0x80a06840`；fill_id=`13`
- **event_id=`272`；parent_event_id=`271`；tick=`237951248562`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x80a06840`；cache_line=`0x80a06840`；fill_id=`13`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`273`；parent_event_id=`272`；tick=`237951248562`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x80a06840`；mshr_id=`14`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`14`；cache_line=`0x80a06840`
- **event_id=`274`；parent_event_id=`273`；tick=`237951249228`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x80a06840`；mshr_id=`0`；fill_id=`14`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x80a06840`；fill_id=`14`
- **event_id=`275`；parent_event_id=`274`；tick=`237951249228`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x80a06840`；cache_line=`0x80a06840`；fill_id=`14`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`276`；parent_event_id=`275`；tick=`237951249228`；fault_id=`2`；corr=`addr_fallback`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x80a06840`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x80a06840`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`277`；parent_event_id=`276`；tick=`237951249561`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x80a06868`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`278`；parent_event_id=`277`；tick=`237951249561`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：load 在 LQ 中完成，污染数据被交付。
  - 地址/身份：VA=`0xffffffc008a16868`；PA=`0x80a06868`；lq_idx=`6`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`279`；parent_event_id=`278`；tick=`237951249561`；fault_id=`2`；corr=`seq_primary`；request_id=`373`；dyn_inst_seq=`373`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x80a06868`；arch_reg=`1`/phys_reg=`132`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`280`；parent_event_id=`279`；tick=`237951250227`；fault_id=`2`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`373`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`280`, tick=`237951250227`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Timeout`；实际表现：受控 Timeout（TIMEOUT triggered=True graceful=True signal=None exit=0 (budget 5400s exhausted; child finalized on SIGINT — evidence complete)）。

run.out 的 CHAOS_DETECT 行（共 9 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237951250227 ptag=2 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951533277 ptag=1 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237963256542 ptag=6 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237963342123 ptag=7 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237967875252 ptag=3 reason=squash_replay`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237970868589 ptag=12 reason=squash_replay`
- …其余 3 行见原始 `run.out`

说明：受控 Timeout（预算耗尽、graceful）是**运行级**结局；代表链的真实 L5 逃逸（若 terminal=`full`）已经发生，不因 Timeout 抹去；两者并列保留。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 259 | — | 237951174969 | `inj` | L0 | 2 | origin | 373 | s1 | 0xffffffc008a16868 | — | 0x80a16→0x80a06 | 80a16→80a06 | 0x10 | — | — | — | — | 起点 | L0 注入 |
| 2 | 260 | 259 | 237951174969 | `tlb_lookup` | L1 | 2 | seq_primary | 373 | s1 | 0xffffffc008a16868 | — | 0x80a16→0x80a06 | 80a16→80a06 | — | — | — | — | — | 直接 parent（parent=259）；corr origin→seq_primary | L1 单元内观察 |
| 3 | 261 | 260 | 237951174969 | `tlb_pfn` | L2 | 2 | seq_primary | 373 | s1 | 0xffffffc008a16868 | 0x80a06868 | 0x80a16→0x80a06 | 80a16→80a06 | — | — | — | — | — | 直接 parent（parent=260） | L2 地址物化 |
| 4 | 262 | 261 | 237951174969 | `tlb_translate_result` | L2 | 2 | seq_primary | 373 | s1 | 0xffffffc008a16868 | 0x80a06868 | — | 80a16868→80a06868 | — | 0 | — | NoFault | — | 直接 parent（parent=261） | L2 翻译结果/含住点 |
| 5 | 263 | 262 | 237951175302 | `lsq_push` | L3 | 2 | seq_primary | — | s1 | 0xffffffc008a16868 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=262） | L3 进入 LQ/SQ |
| 6 | 264 | 263 | 237951175302 | `lq_read` | L3 | 2 | seq_primary | 373 | s1 | 0xffffffc008a16868 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=263） | L3 读取 load 请求 |
| 7 | 265 | 264 | 237951175302 | `cache_access` | L3 | 2 | addr_fallback | 373 | s1 | 0xffffffc008a16868 | 0x80a06868 | — | —→— | — | — | — | — | — | 直接 parent（parent=264）；corr seq_primary→addr_fallback | L3 cache 查找 |
| 8 | 266 | 265 | 237951175302 | `cache_return` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06868 | — | —→— | — | — | — | — | — | 直接 parent（parent=265） | L3 hit/miss 决策 |
| 9 | 267 | 266 | 237951175302 | `mshr_alloc` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06868 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=266） | L3 MSHR 分配 |
| 10 | 268 | 267 | 237951175635 | `cache_access` | L3 | 2 | addr_fallback | 373 | s1 | 0xffffffc008a16868 | 0x80a06840 | — | —→— | — | — | — | — | — | 直接 parent（parent=267） | L3 cache 查找 |
| 11 | 269 | 268 | 237951175635 | `cache_return` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→— | — | — | — | — | — | 直接 parent（parent=268） | L3 hit/miss 决策 |
| 12 | 270 | 269 | 237951175635 | `mshr_alloc` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=269） | L3 MSHR 分配 |
| 13 | 271 | 270 | 237951248562 | `mshr_fill` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→filled | — | — | — | — | — | 直接 parent（parent=270） | L3 MSHR 填充 |
| 14 | 272 | 271 | 237951248562 | `cache_fill` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→— | — | — | — | — | — | 直接 parent（parent=271） | L3 行填充 |
| 15 | 273 | 272 | 237951248562 | `mshr_free` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=272） | L3 MSHR 释放 |
| 16 | 274 | 273 | 237951249228 | `mshr_fill` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→filled | — | — | — | — | — | 直接 parent（parent=273） | L3 MSHR 填充 |
| 17 | 275 | 274 | 237951249228 | `cache_fill` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→— | — | — | — | — | — | 直接 parent（parent=274） | L3 行填充 |
| 18 | 276 | 275 | 237951249228 | `mshr_free` | L3 | 2 | addr_fallback | 373 | s1 | — | 0x80a06840 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=275） | L3 MSHR 释放 |
| 19 | 277 | 276 | 237951249561 | `resp` | L3 | 2 | seq_primary | 373 | s1 | 0x80a06868 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=276）；corr addr_fallback→seq_primary | L3 响应返回 |
| 20 | 278 | 277 | 237951249561 | `lq_complete` | L3 | 2 | seq_primary | 373 | s1 | 0xffffffc008a16868 | 0x80a06868 | — | —→— | — | — | — | — | — | 直接 parent（parent=277） | L3 load 完成 |
| 21 | 279 | 278 | 237951249561 | `taint_reg` | L4 | 2 | seq_primary | 373 | s1 | 0x80a06868 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=278） | L4 污染寄存器 |
| 22 | 280 | 279 | 237951250227 | `errant_commit` | L5（检测；观测层 L4） | 2 | taint_prop | — | s1 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=279）；corr seq_primary→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=2` 从 `inj` 到终局见证的**完整单祖先链**（22 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **8327**；代表故障 `fault_id=2` 的事件数 **28**；进入最终 ancestry 的事件 **22**；未进入最终 ancestry 的同 fault 事件 **6**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 5 | 281–345 | 237951250560–237951815661 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L4 | `consumer` | 281 | 237951250560 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=5；event_id 范围 `281`–`345`；tick 范围 `237951250560`–`237951815661`；corr 分布 {'taint_prop': 5}；outcome 分布 {'': 5}；contained 分布 {'': 5}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`7639`；tick=`558263733777`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**其它 fault（不在本代表链上的独立故障链）**：权威报告共记录 13 个 fault；本文件的代表故障 `fault_id=2` 由 escape-first 规则选出。其余 fault 的终局分布如下（它们各有独立的 `inj` 与祖先链，**不并入**本代表链）：

- 终局分布：{'detected_contained': 5, 'full': 1, 'provable_to_L4_then_unknown': 7}

| fault_id | terminal | provable_to | event_count |
|---|---|---|---|
| 1 | detected_contained | L5 | 383 |
| 2（代表） | full | L5 | 28 |
| 3 | detected_contained | L5 | 922 |
| 4 | provable_to_L4_then_unknown | L4 | 2751 |
| 5 | provable_to_L4_then_unknown | L4 | 88 |
| 6 | detected_contained | L5 | 654 |
| 7 | detected_contained | L5 | 1427 |
| 8 | provable_to_L4_then_unknown | L4 | 82 |
| 9 | provable_to_L4_then_unknown | L4 | 145 |
| 10 | provable_to_L4_then_unknown | L4 | 34 |
| 11 | provable_to_L4_then_unknown | L4 | 140 |
| 12 | detected_contained | L5 | 42 |
| 13 | provable_to_L4_then_unknown | L4 | 1631 |

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`280` tick=`237951250227`（parent=`279`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=23; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 22 events |
| 3_tick_order | PASS | ticks 237951174969..237951250227 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=2; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=280 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (22); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T03-F5-W4 and seed1 |
| 12_tier_matches_evidence | PASS | matrix=F5 run.out=CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1 expected_enabled=1 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/prop_evt.txt.gz` | `478530d46202e0d935d8876b2c7ff127a3e5830d9a159ff66d29c709f89fa7ab` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/chain_report.json` | `535c63546e52ae889d7e3b239b02472921bddf510ee1fad567219cad9086d60e` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/manifest.json` | `edc14fcff3c1a38574b01efff323627fd35ed08016ad70811e7e257a707ed504` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/run.out` | `811b070ab12af7a53264530ece4c07a7e0fe2241d2899a230ed49d14a808cce0` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/stats.txt` | `b37a0b817a51a21b85a210e3d81405b60ae96995e37f0c5ee5f1070a852dfdfa` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
