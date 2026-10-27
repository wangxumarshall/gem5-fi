# T10-F0-W1 seed2 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T10-F0-W1` seed2 中，注入器于 tick=237950233911 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81d75` 改成 `0x81975`（VA=`0xffffffc009483eb8`）；故障 PFN 使有效 PA 从 `0x81d75eb8` 变为 `0x81975eb8`（祖先中无 `tlb_translate_result`，PA 取自 `tlb_pfn` 的 state_before/state_after），随后沿 TLB 翻译 → L1D/MSHR → `resp` → `taint_reg(clean→tainted)` 一路传播，最终由 `errant_commit`（event_id=283, tick=237951341802）在 L5 形成真实错误提交；运行结局 Crash（KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode））。

## 实验身份与证据来源

- RunID: `T10-F0-W1`
- seed: `2`；sample_run_id: `s2`
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
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/prop_evt.txt.gz`
- prop_evt SHA-256: `5a92c75ee16b72ad0f5b08787781f8f77713631f4d61b4fa0600dfa57869e4af`（本次重算值；字节数 16240）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/chain_report.json`
- chain_report SHA-256: `42bb8ea5918c6799d5c55593b1a9631db9777112f7c8a36370fe94dc6b6201b6`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/manifest.json`（SHA-256 `b54954004584f1ba115dafe63a3f8520706326f08455c88901319c2b1f656b4f`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.out`（SHA-256 `45dd1cbb11e8b64052d05ddc96500a1c6bf38f95e2c5e07d7ab2f3787e73b63d`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.err`（SHA-256 `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/stats.txt`（SHA-256 `b305018005e9d4017b9c36caadb5b96a7adec6c5fd30177a1afddaaf3c673783`；`board.chaos_armtlb.numFaultsInjected=1`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 433；代表故障 `fault_id=1` 事件数: 433；权威报告 fault 数: 1
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc009483eb8，PFN 0x81d75→0x81975，PA 0x81d75eb8→0x81975eb8（无 tlb_translate_result，PA 取自 tlb_pfn） → TLB 地址翻译 → cache lookup → MSHR alloc/fill → response → taint_reg(clean→tainted) → errant_commit(L5) → Kernel OOPS / Crash`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81d75` 变成 `81975`（mask=0x400；PFN 0x81d75→0x81975），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950233911`；fault_id=`1`；corr=`origin`；request_id=`—`；dyn_inst_seq=`—`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc009483eb8`
  - 值变化：before=`81d75`→after=`81975`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950233911, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb8, old_pfn: 0x81d75, new_pfn: 0x81975, FaultType: bit_flip, Mask: 0x400, effective: 1`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=150160 eligible=2 injected=1 first_eligible_tick=237950233578 last_eligible_tick=237950233911 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950233911`；fault_id=`1`；corr=`addr_fallback`；request_id=`0`；dyn_inst_seq=`0`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc009483eb8`；PFN=`81d75`→`81975`
  - 值变化：before=`81d75`→after=`81975`；field=`post_lookup`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81975;ap=0;mtype=2;page_size=1000;pa=81975eb8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81d75`→`81975`；pa `81d75eb8`→`81975eb8`
- **event_id=`2`；parent_event_id=`1`；tick=`237950233911`；fault_id=`1`；corr=`addr_fallback`；request_id=`0`；dyn_inst_seq=`0`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc009483eb8`；PA=`0x81975eb8`；PFN=`81d75`→`81975`
  - 值变化：before=`81d75`→after=`81975`；field=`bit_flip`；state_before=`81d75eb8`；state_after=`81975eb8`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
  - 为什么把故障传给下一步：该 seed 的祖先里没有 `tlb_translate_result` 事件；原始流事实是 `tlb_pfn` 的 PA 直接进入 L3 请求，故不据未记录事件推断翻译比对结果（不猜测）。

### 第 3 步：进入 Load Queue 或 Store Queue

N/A：该 seed 的代表链在 `parent_event_id` 上从 L2 事件直接进入 L3 的 cache 访问，原始流没有为该请求记录 `lsq_push`/`lq_read`；本文件不推断未记录的结构。

### 第 4 步：缓存和 MSHR 传播

发生了什么：以错误 PA 访问 L1D，命中/失效决策与 MSHR 分配/合并/填充/释放如实记录；错误地址被 cache/MSHR 状态接受。

- **event_id=`3`；parent_event_id=`2`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483eb8`；PA=`0x81975eb8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`4`；parent_event_id=`3`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x81975eb8`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`5`；parent_event_id=`4`；tick=`237950235576`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x81975eb8`；mshr_id=`1`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`1`；cache_line=`0x81975eb8`
- **event_id=`6`；parent_event_id=`5`；tick=`237950235909`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：以错误 PA 访问 L1D（tag 查找/数据访问）。
  - 地址/身份：VA=`0xffffffc009483eb8`；PA=`0x81975e80`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`7`；parent_event_id=`6`；tick=`237950235909`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：L1D 返回访问结果（field=miss/hit），错误地址已被接受。
  - 地址/身份：PA=`0x81975e80`
  - 值变化：field=`miss`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - hit/miss 决策：field=`miss`
- **event_id=`8`；parent_event_id=`7`；tick=`237950235909`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：为该错误物理地址分配 MSHR（内存级未完成请求登记）。
  - 地址/身份：cache_line=`0x81975e80`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_allocated`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81975e80`
- **event_id=`82`；parent_event_id=`8`；tick=`237950340471`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x81975e80`；mshr_id=`2`；fill_id=`3`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81975e80`；fill_id=`3`
- **event_id=`83`；parent_event_id=`82`；tick=`237950340471`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x81975e80`；cache_line=`0x81975e80`；fill_id=`3`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`84`；parent_event_id=`83`；tick=`237950340471`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x81975e80`；mshr_id=`2`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`2`；cache_line=`0x81975e80`
- **event_id=`85`；parent_event_id=`84`；tick=`237950341137`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：内存响应填充 MSHR。
  - 地址/身份：cache_line=`0x81975e80`；mshr_id=`0`；fill_id=`4`
  - 值变化：state_before=`—`；state_after=`filled`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x81975e80`；fill_id=`4`
- **event_id=`86`；parent_event_id=`85`；tick=`237950341137`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：cache line 填充到 L1D，污染数据/地址进入 cache 状态。
  - 地址/身份：PA=`0x81975e80`；cache_line=`0x81975e80`；fill_id=`4`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`87`；parent_event_id=`86`；tick=`237950341137`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：MSHR 释放，请求完成生命周期。
  - 地址/身份：cache_line=`0x81975e80`；mshr_id=`0`
  - 值变化：state_before=`—`；state_after=`mshr_freed`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
  - MSHR 身份：mshr_id=`0`；cache_line=`0x81975e80`
  - 为什么把故障传给下一步：以错误 PA 访问 L1D 得到 miss（并触发 MSHR 分配/合并/填充）；错误地址被 MSHR/cache 接受并完成响应路径，因此污染数据/状态传给返回处理器的响应。

### 第 5 步：错误数据或污染状态返回处理器

发生了什么：响应返回 LSU，污染数据被交付；若出现 `taint_reg`，污染从存储域进入寄存器域。

- **event_id=`88`；parent_event_id=`87`；tick=`237950341470`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：内存/cache 响应返回；该响应对应的数据/地址带故障（或把污染值交付给 LSU）。
  - 地址/身份：VA=`0x81975eb8`
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L3**
- **event_id=`89`；parent_event_id=`88`；tick=`237950341470`；fault_id=`1`；corr=`addr_fallback`；request_id=`32`；dyn_inst_seq=`32`**
  - 硬件结构/事件：污染数据写入目标体系结构/物理寄存器，并被打上 taint 标记；传播从存储域进入寄存器域。
  - 地址/身份：VA=`0x81975eb8`
  - 值变化：before=`clean`→after=`tainted`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L4**
  - 为什么把故障传给下一步：污染数据已经写入寄存器（`clean→tainted`）；该寄存器随后被下游指令消费，污染从存储域进入寄存器/提交域，故传给 L4/L5 的最终判定。

### 第 6 步：最终传播终局

情况 A：真实 L5 逃逸。

- **event_id=`283`；parent_event_id=`89`；tick=`237951341802`；fault_id=`1`；corr=`taint_prop`；request_id=`—`；dyn_inst_seq=`391`**
  - 硬件结构/事件：携带污染值的指令错误提交：错误副作用越过重定序/提交边界，构成 L5 逃逸终局（detection_layer=L5, outcome=errant_commit）。
  - 地址/身份：—（该事件无地址字段）
  - 值变化：—（该事件无 before/after 载荷）
  - 检测/含住字段：detection_layer=`L5`；contained=`0`；outcome=`errant_commit`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L5（检测；观测层 L4）**
  - 说明：该 `errant_commit` 的 `detection_layer=L5`、`outcome=errant_commit`、`corr=taint_prop`，是**真实检测/结局事件**，不是生命周期 `chain_end`；按 checker 的 `_L4_TERMINAL_KINDS`/`_explicit_l5` 判定构成 `full` 终局。
  - 为什么这是终局：`errant_commit` 表明携带污染值的指令已经越过提交边界，错误副作用不可撤销；这是真实 L5 终局（不是生命周期 `chain_end`）。
  - L0–L5：L0 注入 → L1 lookup → L2 PFN/PA → L3 LQ/cache/MSHR → L4 taint_reg → **L5 errant_commit** 全部有事件。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L5 `errant_commit`（event_id=`283`, tick=`237951341802`）——真实错误提交已发生。

**运行结局（与传播链终局分开陈述）**：oracle=`Crash`；实际表现：KERNEL OOPS under fault（run.out: classify: Crash/DUE per fs_mode）。

run.out 的 CHAOS_DETECT 行（共 2 行，节选）：
- `CHAOS_DETECT: layer=None contained=0 tick=237951341802 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951586890 ptag=1 reason=squash_replay`

说明：真实 L5 逃逸与 Kernel OOPS/Crash 一致——错误提交已越过提交边界，运行以崩溃收场。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | `inj` | L0 | 1 | origin | — | s2 | 0xffffffc009483eb8 | — | 0x81d75→0x81975 | 81d75→81975 | 0x400 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950233911 | `tlb_lookup` | L1 | 1 | addr_fallback | 0 | s2 | 0xffffffc009483eb8 | — | 0x81d75→0x81975 | 81d75→81975 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→addr_fallback | L1 单元内观察 |
| 3 | 2 | 1 | 237950233911 | `tlb_pfn` | L2 | 1 | addr_fallback | 0 | s2 | 0xffffffc009483eb8 | 0x81975eb8 | 0x81d75→0x81975 | 81d75→81975 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950235576 | `cache_access` | L3 | 1 | addr_fallback | 32 | s2 | 0xffffffc009483eb8 | 0x81975eb8 | — | —→— | — | — | — | — | — | 直接 parent（parent=2）；request_id 0→32 | L3 cache 查找 |
| 5 | 4 | 3 | 237950235576 | `cache_return` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975eb8 | — | —→— | — | — | — | — | — | 直接 parent（parent=3） | L3 hit/miss 决策 |
| 6 | 5 | 4 | 237950235576 | `mshr_alloc` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975eb8 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=4） | L3 MSHR 分配 |
| 7 | 6 | 5 | 237950235909 | `cache_access` | L3 | 1 | addr_fallback | 32 | s2 | 0xffffffc009483eb8 | 0x81975e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=5） | L3 cache 查找 |
| 8 | 7 | 6 | 237950235909 | `cache_return` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=6） | L3 hit/miss 决策 |
| 9 | 8 | 7 | 237950235909 | `mshr_alloc` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→mshr_allocated | — | — | — | — | — | 直接 parent（parent=7） | L3 MSHR 分配 |
| 10 | 82 | 8 | 237950340471 | `mshr_fill` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→filled | — | — | — | — | — | 直接 parent（parent=8） | L3 MSHR 填充 |
| 11 | 83 | 82 | 237950340471 | `cache_fill` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=82） | L3 行填充 |
| 12 | 84 | 83 | 237950340471 | `mshr_free` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=83） | L3 MSHR 释放 |
| 13 | 85 | 84 | 237950341137 | `mshr_fill` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→filled | — | — | — | — | — | 直接 parent（parent=84） | L3 MSHR 填充 |
| 14 | 86 | 85 | 237950341137 | `cache_fill` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→— | — | — | — | — | — | 直接 parent（parent=85） | L3 行填充 |
| 15 | 87 | 86 | 237950341137 | `mshr_free` | L3 | 1 | addr_fallback | 32 | s2 | — | 0x81975e80 | — | —→mshr_freed | — | — | — | — | — | 直接 parent（parent=86） | L3 MSHR 释放 |
| 16 | 88 | 87 | 237950341470 | `resp` | L3 | 1 | addr_fallback | 32 | s2 | 0x81975eb8 | — | — | —→— | — | — | — | — | — | 直接 parent（parent=87） | L3 响应返回 |
| 17 | 89 | 88 | 237950341470 | `taint_reg` | L4 | 1 | addr_fallback | 32 | s2 | 0x81975eb8 | — | — | clean→tainted | — | — | — | — | — | 直接 parent（parent=88） | L4 污染寄存器 |
| 18 | 283 | 89 | 237951341802 | `errant_commit` | L5（检测；观测层 L4） | 1 | taint_prop | — | s2 | — | — | — | —→— | — | 0 | L5 | errant_commit | — | 直接 parent（parent=89）；corr addr_fallback→taint_prop | L5 错误提交（终局） |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（18 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **433**；代表故障 `fault_id=1` 的事件数 **433**；进入最终 ancestry 的事件 **18**；未进入最终 ancestry 的同 fault 事件 **415**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

| kind | 数量 | event_id 范围 | tick 范围 | 处理方式 | 异常成员检查 |
|---|---|---|---|---|---|
| `consumer` | 61 | 284–379 | 237951341802–237965000796 | 折叠为计数 + 范围（见下） | 无（outcome/contained 全空） |
| `cache_access` | 58 | 9–371 | 237950235909–237964998132 | 计数 + 范围 | 无（outcome/contained 全空） |
| `cache_return` | 58 | 10–372 | 237950235909–237964998132 | 不折叠：全量 hit/miss 索引（见下）；分布 {'miss': 41, 'hit': 17} | 无（outcome/contained 全空） |
| `request_fork` | 52 | 4294967296–4294967347 | 237950235909–237964998132 | 旁支 bridge：计数 + 首尾点名（主链 bridge 已在第二部分逐条） | 无（outcome/contained 全空） |
| `taint_reg` | 52 | 64–375 | 237950296515–237964998465 | 不折叠：全量身份索引（见下） | 无（outcome/contained 全空） |
| `resp` | 51 | 63–373 | 237950296515–237964998465 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_merge` | 29 | 17–263 | 237950236242–237951290853 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_alloc` | 12 | 11–257 | 237950235909–237951290853 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `mshr_fill` | 12 | 57–267 | 237950295183–237951336141 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `cache_fill` | 12 | 58–268 | 237950295183–237951336141 | 计数 + 范围 | 无（outcome/contained 全空） |
| `mshr_free` | 12 | 59–269 | 237950295183–237951336141 | 不折叠：全量 MSHR 索引（见下）；主链 MSHR 已在第二部分逐条 | 无（outcome/contained 全空） |
| `lq_complete` | 4 | 281–374 | 237951340803–237964998465 | 计数 + 范围 | 无（outcome/contained 全空） |
| `squash_masked` | 1 | 309–309 | 237951586890–237951586890 | 不折叠：全部逐条点名（见下） | 预期非空（检测/含住事件）：outcome={'masked': 1} contained={'1': 1} |

**每层第一个旁支事件（不折叠）**：

| 层 | kind | event_id | tick |
|---|---|---|---|
| L3 | `request_fork` | 4294967296 | 237950235909 |
| L4 | `taint_reg` | 64 | 237950296515 |

**`consumer` 折叠说明**（唯一允许折叠的 kind）：kind=`consumer`；count=61；event_id 范围 `284`–`379`；tick 范围 `237951341802`–`237965000796`；corr 分布 {'taint_prop': 61}；outcome 分布 {'': 61}；contained 分布 {'': 61}；可折叠理由：这些是同一故障的重复下游读取（可能跨多个 dyn_inst_seq/寄存器），不承担 L0–L5 任一层的首次见证，不驱动 admission/violation；异常成员：无（原始流中逐条保留，未删除）。

**`taint_reg` 旁支（不折叠）**：count=52；event_id `64`–`375`；tick `237950296515`–`237964998465`；distinct dyn_inst_seq=51；distinct phys_reg=6；distinct arch_reg=5；corr 分布 {'addr_fallback': 52}；outcome 分布 {'': 52}；contained 分布 {'': 52}；sample_run 分布 {'s2': 52}。

首 8 条 / 末 8 条（身份可回查；其余全部保留在原始流中）：

| event_id | tick | parent | dyn_inst_seq | arch_reg/phys_reg | before→after | corr |
|---|---|---|---|---|---|---|
| 64 | 237950296515 | 63 | 34 | —/— | clean→tainted | addr_fallback |
| 66 | 237950297181 | 65 | 35 | —/— | clean→tainted | addr_fallback |
| 71 | 237950297182 | 70 | 37 | —/— | clean→tainted | addr_fallback |
| 73 | 237950297183 | 72 | 38 | —/— | clean→tainted | addr_fallback |
| 75 | 237950297184 | 74 | 40 | —/— | clean→tainted | addr_fallback |
| 77 | 237950297185 | 76 | 41 | —/— | clean→tainted | addr_fallback |
| 79 | 237950297186 | 78 | 43 | —/— | clean→tainted | addr_fallback |
| 81 | 237950297187 | 80 | 44 | —/— | clean→tainted | addr_fallback |
| 290 | 237951426051 | 289 | 460 | —/— | clean→tainted | addr_fallback |
| 292 | 237951426052 | 291 | 461 | —/— | clean→tainted | addr_fallback |
| 297 | 237951484992 | 296 | 474 | 29/158 | clean→tainted | addr_fallback |
| 298 | 237951484992 | 297 | 474 | 30/159 | clean→tainted | addr_fallback |
| 304 | 237951541935 | 303 | 507 | —/— | clean→tainted | addr_fallback |
| 306 | 237951541936 | 305 | 508 | —/— | clean→tainted | addr_fallback |
| 314 | 237957366108 | 313 | 3937 | 0/2 | clean→tainted | addr_fallback |
| 375 | 237964998465 | 374 | 10529 | 1/228 | clean→tainted | addr_fallback |

<details><summary><b>taint_reg 全量身份索引（52 条，不折叠，逐条列出）</b></summary>

64@237950296515(—/—) 66@237950297181(—/—) 71@237950297182(—/—) 73@237950297183(—/—) 75@237950297184(—/—) 77@237950297185(—/—) 79@237950297186(—/—) 81@237950297187(—/—)

127@237950346465(—/—) 129@237950347131(—/—) 131@237950347132(—/—) 133@237950347133(—/—) 135@237950347134(—/—) 137@237950347135(—/—) 139@237950347136(—/—) 141@237950347137(—/—)

167@237950393751(—/—) 172@237950394417(—/—) 174@237950394418(—/—) 176@237950394419(—/—) 178@237950394420(—/—) 180@237950394421(—/—) 182@237950394422(—/—) 184@237950394423(—/—)

186@237950394750(—/—) 188@237950395416(—/—) 190@237950395417(—/—) 192@237950395418(—/—) 207@237950981829(—/—) 209@237950981830(—/—) 215@237950982495(—/—) 220@237950982496(—/—)

228@237951027450(—/—) 230@237951028116(—/—) 232@237951028117(—/—) 238@237951128016(—/—) 240@237951128017(—/—) 246@237951174969(—/—) 248@237951174970(—/—) 271@237951336474(—/—)

273@237951337140(—/—) 275@237951337141(—/—) 277@237951337142(—/—) 282@237951340803(0/142) 290@237951426051(—/—) 292@237951426052(—/—) 297@237951484992(29/158) 298@237951484992(30/159)

304@237951541935(—/—) 306@237951541936(—/—) 314@237957366108(0/2) 375@237964998465(1/228)

</details>

<details><summary><b>cache_return 全量 hit/miss 决策索引（58 条，不折叠）</b></summary>

10@237950235909:miss 13@237950236242:miss 16@237950236242:miss 19@237950236575:miss 22@237950236908:miss 25@237950237241:miss 28@237950237574:miss 31@237950237907:miss

34@237950238240:miss 37@237950238573:miss 40@237950238906:miss 43@237950238906:miss 46@237950239239:miss 49@237950239572:miss 52@237950239905:miss 55@237950240238:miss

68@237950297181:miss 91@237950343135:miss 94@237950343468:miss 97@237950343468:miss 100@237950343468:miss 103@237950343801:miss 106@237950344134:miss 112@237950345799:miss

115@237950345799:miss 118@237950345799:miss 121@237950345799:miss 143@237950348130:miss 146@237950348463:miss 149@237950348796:miss 152@237950349129:miss 155@237950349129:miss

194@237950981496:hit 196@237950981496:hit 198@237950981496:miss 201@237950981496:miss 204@237950981829:miss 211@237950982162:hit 213@237950982162:hit 217@237950982495:miss

234@237951127683:hit 236@237951127683:hit 242@237951174636:hit 244@237951174636:hit 250@237951290520:miss 253@237951290520:miss 256@237951290853:miss 259@237951290853:miss

262@237951290853:miss 279@237951340470:hit 286@237951425718:hit 288@237951425718:hit 294@237951484659:hit 300@237951541602:hit 302@237951541602:hit 308@237951586557:hit

311@237957365772:hit 372@237964998132:hit

</details>

<details><summary><b>MSHR alloc/merge/fill/free 全量索引（65 条，不折叠）</b></summary>

11@237950235909:mshr_alloc:mshr=3,fill=— 14@237950236242:mshr_alloc:mshr=4,fill=— 17@237950236242:mshr_merge:mshr=4,fill=— 20@237950236575:mshr_merge:mshr=4,fill=—

23@237950236908:mshr_merge:mshr=4,fill=— 26@237950237241:mshr_merge:mshr=4,fill=— 29@237950237574:mshr_merge:mshr=4,fill=— 32@237950237907:mshr_merge:mshr=4,fill=—

35@237950238240:mshr_merge:mshr=4,fill=— 38@237950238573:mshr_alloc:mshr=5,fill=— 41@237950238906:mshr_alloc:mshr=6,fill=— 44@237950238906:mshr_merge:mshr=6,fill=—

47@237950239239:mshr_merge:mshr=6,fill=— 50@237950239572:mshr_merge:mshr=6,fill=— 53@237950239905:mshr_merge:mshr=6,fill=— 56@237950240238:mshr_merge:mshr=6,fill=—

57@237950295183:mshr_fill:mshr=4,fill=1 59@237950295183:mshr_free:mshr=4,fill=— 60@237950296182:mshr_fill:mshr=0,fill=2 62@237950296182:mshr_free:mshr=0,fill=—

69@237950297181:mshr_merge:mshr=6,fill=— 92@237950343135:mshr_merge:mshr=6,fill=— 95@237950343468:mshr_alloc:mshr=7,fill=— 98@237950343468:mshr_merge:mshr=7,fill=—

101@237950343468:mshr_merge:mshr=7,fill=— 104@237950343801:mshr_alloc:mshr=8,fill=— 107@237950344134:mshr_merge:mshr=8,fill=— 108@237950345466:mshr_fill:mshr=6,fill=5

110@237950345466:mshr_free:mshr=6,fill=— 113@237950345799:mshr_merge:mshr=8,fill=— 116@237950345799:mshr_merge:mshr=8,fill=— 119@237950345799:mshr_merge:mshr=8,fill=—

122@237950345799:mshr_merge:mshr=8,fill=— 123@237950346132:mshr_fill:mshr=0,fill=6 125@237950346132:mshr_free:mshr=0,fill=— 144@237950348130:mshr_alloc:mshr=9,fill=—

147@237950348463:mshr_alloc:mshr=10,fill=— 150@237950348796:mshr_merge:mshr=10,fill=— 153@237950349129:mshr_merge:mshr=10,fill=— 156@237950349129:mshr_merge:mshr=10,fill=—

157@237950392752:mshr_fill:mshr=8,fill=7 159@237950392752:mshr_free:mshr=8,fill=— 160@237950393418:mshr_fill:mshr=0,fill=8 162@237950393418:mshr_free:mshr=0,fill=—

163@237950393418:mshr_fill:mshr=10,fill=9 165@237950393418:mshr_free:mshr=10,fill=— 168@237950394417:mshr_fill:mshr=0,fill=10 170@237950394417:mshr_free:mshr=0,fill=—

199@237950981496:mshr_alloc:mshr=11,fill=— 202@237950981496:mshr_merge:mshr=11,fill=— 205@237950981829:mshr_alloc:mshr=12,fill=— 218@237950982495:mshr_merge:mshr=12,fill=—

221@237951026451:mshr_fill:mshr=12,fill=11 223@237951026451:mshr_free:mshr=12,fill=— 224@237951027117:mshr_fill:mshr=0,fill=12 226@237951027117:mshr_free:mshr=0,fill=—

251@237951290520:mshr_alloc:mshr=13,fill=— 254@237951290520:mshr_merge:mshr=13,fill=— 257@237951290853:mshr_alloc:mshr=14,fill=— 260@237951290853:mshr_merge:mshr=14,fill=—

263@237951290853:mshr_merge:mshr=14,fill=— 264@237951335475:mshr_fill:mshr=14,fill=13 266@237951335475:mshr_free:mshr=14,fill=— 267@237951336141:mshr_fill:mshr=0,fill=14

269@237951336141:mshr_free:mshr=0,fill=—

</details>

**`squash_masked` 旁支（不折叠，全部点名）**：共 1 条，均为同一 fault 的 L4 contain-by-squash 见证；只有主链上的那一条（若 terminal 为 L4 含住）或权威报告 containment.metrics 指定的一条是终局见证。

| event_id | tick | parent | VA | PA | dyn_inst_seq | containment_reason |
|---|---|---|---|---|---|---|
| 309 | 237951586890 | 284 | 0xffffffc009483e40 | 0x81975e40 | 520 | squash_replay |

**旁支 `request_fork` bridge（计数 + 首尾点名）**：共 52 条；event_id `4294967296`–`4294967347`；tick `237950235909`–`237964998132`。主链上的 bridge 已在第二部分逐条列出（source/dest/shared_addr 可核验）；其余 bridge 属于同一故障的其它请求转交，不参与主链证明。

首 5 条 / 末 5 条：

| event_id | tick | old_request_id | new_request_id | source→dest | shared_addr+size |
|---|---|---|---|---|---|
| 4294967296 | 237950235909 | 32 | 34 | 8→9 | 0x81975000+1000 |
| 4294967297 | 237950236242 | 32 | 35 | 8→15 | 0x81975000+1000 |
| 4294967298 | 237950236575 | 32 | 37 | 8→18 | 0x81975000+1000 |
| 4294967299 | 237950236908 | 32 | 38 | 8→21 | 0x81975000+1000 |
| 4294967300 | 237950237241 | 32 | 40 | 8→24 | 0x81975000+1000 |
| 4294967343 | 237951541602 | 32 | 507 | 89→299 | 0x81975000+1000 |
| 4294967344 | 237951541602 | 32 | 508 | 89→301 | 0x81975000+1000 |
| 4294967345 | 237951586557 | 32 | 520 | 89→307 | 0x81975000+1000 |
| 4294967346 | 237957365772 | 32 | 3937 | 89→310 | 0x81975000+1000 |
| 4294967347 | 237964998132 | 32 | 10529 | 89→371 | 0x81975000+1000 |

**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`380`；tick=`238882385160`；detection_layer=`L5`；contained=`1`；outcome=`errant_commit_seen`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

**为什么主链选的是 L5 逃逸而不是这些 L4 含住旁支**：本 seed 的权威判定采用 escape-first 规则——只要**任一** fault 到达 `full`（真实 errant_commit 逃逸），样本 headline 就是 `full`；squash 类含住证据在同一链上存在可证 L0→L5 逃逸路径时必须让位（`errant_escape_outranks_containment`）。这些旁支 `squash_masked` 是同一故障的其它 load 实例，不改变代表故障的逃逸终局。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `full`；provable_to: `L5`；propagation terminal: `L5`
- witness: `errant_commit` event_id=`283` tick=`237951341802`（parent=`89`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=72; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 18 events |
| 3_tick_order | PASS | ticks 237950233911..237951341802 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=full/L5 report=full/L5 |
| 7_full_witness_real_L5_not_chain_end | PASS | witness kind=errant_commit id=283 dl=L5 outcome=errant_commit (kind!=chain_end) |
| 8_containment_witness_real_contained | PASS | n/a (full escape) |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (18); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T10-F0-W1 and seed2 |
| 12_tier_matches_evidence | PASS | matrix=F0 run.out=CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0 expected_enabled=0 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/prop_evt.txt.gz` | `5a92c75ee16b72ad0f5b08787781f8f77713631f4d61b4fa0600dfa57869e4af` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/chain_report.json` | `42bb8ea5918c6799d5c55593b1a9631db9777112f7c8a36370fe94dc6b6201b6` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/manifest.json` | `b54954004584f1ba115dafe63a3f8520706326f08455c88901319c2b1f656b4f` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.out` | `45dd1cbb11e8b64052d05ddc96500a1c6bf38f95e2c5e07d7ab2f3787e73b63d` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s2/T10-F0-W1/seed2/stats.txt` | `b305018005e9d4017b9c36caadb5b96a7adec6c5fd30177a1afddaaf3c673783` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
