# 09 · LSU 故障注入实施总纲（宏伟计划）

> **文档地位**：本文件是北极星方案（`00`–`08` + 两个 CSV，源 xlsx V1.0 的忠实提取）的**落地路线图**——实施层计划，不是设计数据，更不是源表转录。
> **裁决规则（用户指令 2026-09-24）**：本文件与 `00`–`08` 冲突时，**一律以 `00`–`08` 为准**；本文件只回答「怎么排、怎么建、怎么验」。
> 编号体系沿用源表模型 ID（A/T/S/C/O/P/L 前缀，68 个）与 RunID（`{模型ID}-{F档}-{W负载}`，337 格）；本文件新增工作包编号 W0–W11、里程碑 M0–M6。**注意字面冲突**：工作包 W# 与负载 W#（06-workloads.md 的 W0–W13）同形，本文一律以「工作包 W#」/「负载 W#」限定。
> 编写日期：2026-09-24 · 分支 `fi-ding` · 依据：北极星 00–08 全文（裁决基准）+ README §7 基础设施映射（2026-09-24 grep 核实）+ spec §8 机制核实清单 + 本仓 vendored gem5 v25.1.0.1（upstream 62c7bf2）源码存在性检查（2026-09-24 执行，路径调整记录见 §2 表后注）。

---

## 1. 目标与成功判据

### 1.1 三问（README §1，源自北极星目标）

1. **哪些位置有真实 SDC 潜力？** LSU 七单元（AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器）中，区分真正产生静默数据损坏的位置与只影响性能/只会崩溃（DUE/Crash）的位置。
2. **SDC 之前，微架构层有哪些可观测前兆？** 通过 L0–L5 传播链（04）在架构可见错误之前捕获局部偏差——L1 影子比对、请求配对、提交首分歧——为在线检测提供锚点。
3. **结构化模型相对随机翻转的增量有多大？** 随机位翻转大多被非法编码检查、依赖检查或异常拦截（TC'23 实测 LQ/SQ SDC=0）；合法换值、状态、时序与保护类模型专门测试这些检查之外的静默路径。

### 1.2 最终交付物

| 交付物 | 形态 | 验收 |
|---|---|---|
| 337 实验格 × 11 结果列回填 | `07-expanded-matrix.csv` col16–25、col27（Seed/注入索引、Attempted、Activated、Masked、Detected/Contained、SDC、Crash、Timeout、SDC率(activated)、激活率、实测备注）+ col26 记录状态 | 全部 337 格记录状态离开「待执行」；L5 守恒式 `Activated = Masked + Detected + SDC + Crash + Timeout` 逐格闭合（04 L5） |
| L0–L5 六层观测数据 | artifacts + 元分析素材 | 每格 attempted/eligible/activated 分开记录（04 L0）；L1 影子比对与 L4 首分歧 commit 序号可追溯到 RunID |
| 自检锚点记录 | 自检报告（M2/M3 门） | ① LQ/SQ 单 bit 复现 **TC'23 SDC=0%**（S01/S13/L01 对照 TC'23 的每负载设置；复现不出 0% 先怀疑注入器）；② **T01 DTLB 单 bit 对照 TC'22**（平均 Crash AVF≈50%、Hang≈10%、SDC AVF<1%，01 原文） |
| 元分析报告 | 三问的回答 + 位置×SDC 潜力排序 + 结构化 vs 随机增量对照 | 结论每条带模型 ID/RunID、样本量与 Wilson CI；负对照（C10、P01–P03）与守恒校验结论一并呈现 |

### 1.3 不可妥协的口径（00 §3 五条原文 + 05 统计规则，防口径漂移）

- **SDC 率分母 = activated**；attempted/eligible/activated 分开记录；Injected-not-activated 单列，不进分母（04 L0 / 05 r12）。
- **试跑 30 activated/格**只用于发现注入器错误、全 Crash 或零激活单元，不用于最终窄置信区间（05 r13）。
- **筛查 ≥385 activated**（95% 置信、最坏 p=0.5、约 ±5pp）；**主结果**顺序加样至 Wilson 95% 区间半宽 ≤2pp 或 activated 达 5000 停止，报告实际区间不只报点估计（05 r14/r15）。
- **F0 单故障 AVF 与 F1–F4 压力实验不得混成一个「故障率」**；F5 永久故障按运行分类；F1–F4 同一运行内多 activated 事件属同一 cluster，按运行聚类计算区间（00 §3 ②、05 r19/r20）。
- **超时** = golden wall/sim time 或 committed inst 的 10× 并设绝对上限；F5 可单独提高上限但须预注册（05 r17）。
- **预期结果是可证伪假设**：无论文直接结果的 AGU、原子/同步和多数结构化模型，实测列回填前保持待执行（00 §3 ⑤）。
- **Crash 双拆分**：gem5 断言崩溃 ≠ 架构崩溃（04 L5），避免把模拟器伪影计为架构脆弱性。

## 2. 机制核实九项表（对本仓 vendored v25.1.0.1）

> 本表是**计划**：状态列初始全部「待核实」，由工作包 W1 逐条源码核实后回填结论——不预填。
> 第三列「v25.1 实际」给出的是 2026-09-24 存在性检查的**初查锚点**（当日实际执行 ls/grep，路径存在、行号为当日所见）——只证明「去哪里核实」，不等于核实结论。
> xlsx 文献核对基于上游 gem5 stable（08 提取注，核对日期 2026-09-24）；机制核实**一律以本仓 vendored v25.1.0.1 源码为准**，两者可能有差异。

| # | xlsx 表述（02/03 源） | v25.1 实际（源码:行号；初查锚点，待 W1 回填核实结论） | 对模型行的影响 | 状态 |
|---|---|---|---|---|
| ① | LQ/SQ 16/16 项；表项字段、head/tail、violation/replay 路径 | `src/cpu/o3/lsq.hh`（LSQ/LSQRequest 类；:761 起 LQ head 访问）+ `lsq.cc`（v25 实现已并入，无 lsq_impl.hh）+ `lsq_unit.hh/.cc`（:80 起职责注释、:247/:287 ordering violation）；16/16 定值在 `configs/common/cores/arm/O3_ARM_v7a.py:164-165`（`src/cpu/o3/BaseO3CPU.py:142-143` 默认为 32/32，故 16/16 须由配置显式落地） | L01–L04、S01–S13 全部落点；TC'23 自检锚点的宿主结构 | 待核实 |
| ② | SSIT/LFST（store set）落点与 1024/1024 配置 | `src/cpu/o3/store_set.hh/.cc`（SSIT/LFST 类定义，store_set.hh:70-105）+ 消费方 `src/cpu/o3/mem_dep_unit.cc`；容量参数 `src/cpu/o3/BaseO3CPU.py:157-158`（SSITSize/LFSTSize 默认即 1024/1024） | SQ 内存序预测相关模型行（S05/S07 等）的落点 | 待核实 |
| ③ | DTLB=32 项全相联（gem5 默认 64） | `src/arch/arm/ArmTLB.py:74`（`size = Param.Int(64, ...)`，默认 64 与 02 r11 表述一致）+ `src/arch/arm/tlb.hh/.cc`；B0 须显式配 32（S1 敏感性=64 回默认） | T01–T10 全部 + TC'22 对照锚点的宿主 | 待核实 |
| ④ | L1D 32KiB/2-way、tag/data/response latency 2/2/2、MSHR 6/targets 8、write buffer 16 | `configs/common/cores/arm/O3_ARM_v7a.py:222-232`（O3_ARM_v7a_DCache：size 32KiB、assoc 2、lat 2/2/2、mshrs 6、tgts_per_mshr 8、write_buffers 16——逐项与 02 r13/r15/r16/r17 吻合）。**注意**：当前 C3 平台 `configs/se/ooo_proxy.py:337-339` 用 stdlib 层级 64KiB L1D/512KiB L2，≠ B0 → 工作包 W0 必须新建 LSU 配置家族而非沿用 | C01–C15 落点基准；负载 W6 的 working set 标定（0.5×/1×/2×L1D） | 待核实 |
| ⑤ | L2 StridePrefetcher degree=8、latency=1、prefetch_on_access=True（B0 预取器在 L2 而非 L1D） | `configs/common/cores/arm/O3_ARM_v7a.py:236-247`（O3_ARM_v7aL2 挂 `prefetcher = StridePrefetcher(degree=8, latency=1, prefetch_on_access=True)`）+ 实现 `src/mem/cache/prefetch/stride.hh`；当前 ooo_proxy L2 未挂预取器，W0 须补 | P01–P09 的被测对象挂接点（S4 敏感性=挂 L1D） | 待核实 |
| ⑥ | exclusive monitor / 原子 RMW 的多核语义（SE 单核平台的差距） | `src/arch/arm/isa.cc:1871-1960`（handleLockedRead/handleLockedWrite，LLSC 监视器置位/清除）+ `src/arch/arm/insts/macromem.cc`（LDXR/STXR 等宏指令）；本仓已有注入器 `src/arch/arm/CHAOSExMon/`（`tools/runner.py:1193` `exmon` 分派，stxr_force_fail 模式）；单核 SE 与多核 FS 语义差距待 W1 核实 | O01–O09 全部 + 负载 W7（Atomic-Litmus，多核 FS） | 待核实 |
| ⑦ | AGU 有效地址生成的截获点与现有 CHAOSAddrPath 的关系 | `src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh`（四件套目录；挂 `LSQ::LSQRequest::sendFragmentToTranslation`、translateTiming 前改 vaddr；现有 Byte7Zero/LowBitFlip 两模式；头注释自述 SE-inert——SE 物理内存从 0 起，byte7 清零仍在范围内）；EA 计算本体在 `src/cpu/o3/lsq_unit.cc`（executeAddrCalc 路径，行号待 W1 核实） | A01–A08 落点：现有 addr_path 是 vaddr 观测/污染，AGU EA 注入是否新挂点由 W1 定 | 待核实 |
| ⑧ | F4 短突发（每 100K eligible 触发一次、连续污染 2–4 个 eligible events）/ F6 确定性事件触发（首次出现指定事件注入一次） | `src/cpu/o3/chaos_trigger.hh:25` 枚举仅 `{ F0, F1, F2, F3, F5 }`（:46-48 F1/F2/F3 = 2.6M/260K/26K cycle 固定均值间隔）——**F4/F6 均缺失**，而展开矩阵 F4=26 格、F6=68 格（共 94 格）依赖这两档；F6 事件枚举（TLB hit、SQ forward、dirty eviction、CAS 成功，05 r8 原文）在触发层尚无对应物 | 94 个 F4/F6 格的可执行性；工作包 W2 的扩展范围 | 待核实 |
| ⑨ | MSHR merge、fill/writeback、dirty eviction 路径 | `src/mem/cache/mshr.hh/.cc`（MSHR/merge）+ `mshr_queue.cc` + `cache.cc` + `base.cc`（fill/writeback/dirty 路径）+ `write_queue.cc` + `write_queue_entry.cc`；本仓已有注入器 `src/mem/cache/CHAOSCache/`（四件套）与 `src/cpu/o3/CHAOSL1DForward/` | C 系 fill/writeback/dirty 模型行（C11/C12/C14 等）落点 | 待核实 |

> **路径调整记录（2026-09-24 存在性检查，brief 原引 → 真实位置）**：
> 1. ② brief 引 `lsq_impl.hh`——该文件在 v25 **不存在**（实现并入 `lsq.cc`），且 `lsq.hh` 中 grep SSIT/LFST 零命中；真实落点 `store_set.hh/.cc`。
> 2. ③ `tlb.hh` 存在，但 DTLB=32 的**配置参数**路径是 `ArmTLB.py:74`（非 tlb.hh）。
> 3. ⑥ brief 引 `tlb.cc` 的 exclusiveMonitor——grep 零命中；真实语义在 `isa.cc` handleLockedRead/handleLockedWrite + `insts/macromem.cc`。
> 4. ⑦ CHAOSAddrPath 为**目录**（`src/cpu/o3/CHAOSAddrPath/` 四件套），非单文件。
> 5. ④⑤ 补充事实：`configs/common/caches/O3_ARM_v7a.py` 路径不存在，真实位置 `configs/common/cores/arm/O3_ARM_v7a.py`。

## 3. WBS（工作包 W0–W11，每个 W = 一个 patch 单元序列）

> 每个 patch 遵守 CLAUDE.md 纪律：构建零警告（涉 C++ 时）+ 定向功能验证（真机输出为证）+ 回归（reg_chain golden `f247ef3fe6c02cfd` 不变）→ commit → 自动 push 到非 main 分支。
> 每个工作包启动时先用 `superpowers:writing-plans` 写执行计划到 `docs/superpowers/plans/`（两级计划体系：本文件=总纲，执行计划=逐补丁细化）。
> 复用优先：README §7 已 grep 核实的复用清单（lsq_fwd/l1d_fwd/l1d/addr_path/l1_tlb/exmon 组件分派、CHAOSLSQFwd/CHAOSL1DForward/CHAOSCache/CHAOSAddrPath/CHAOSExMon 注入器、tools/wilson.py、configs/se/ooo_proxy.py、configs/fs/kp920_proxy_fs.py）。

### 工作包 W0：平台与 B0 参数落地（依赖：无）

- 新建 LSU 配置家族（`configs/se/lsu_proxy.py`，或经裁定扩展 `ooo_proxy.py`——二选一在执行计划期定，隔离理由同 ooo A2：B0 口径 ≠ C3 现状）：B0 19 参数（02 表）逐项落地——LQ/SQ=16/16、1 Load FU + 1 Store FU（MemRead/FloatMemRead/MemWrite/FloatMemWrite opLat=2）、LSQDepCheckShift=0、SSIT/LFST=1024/1024、DTLB=32 全相联、L1D 32KiB/2-way/lat 2-2-2/MSHR 6/targets 8/write buffer 16、L2 挂 StridePrefetcher（degree=8, latency=1, prefetch_on_access=True）；L2 几何未在 B0 19 参数中单列，按 00 §1 统一基线条款跟随 O3_ARM_v7a 示例并在配置中显式固化。
- S1–S5 敏感性开关（02 敏感性配置列）做成配置变体；`tools/runner.py` `CONFIG_FAMILY` + `schemas/manifest.schema.json` 枚举 + `tools/manifest_validate.py` 四链全接（CLAUDE.md「未全链接线即拒绝」纪律）。
- 验证：reg_chain golden 不变；B0 关键参数（LQ/SQ/DTLB/L1D 几何/预取器在 L2）经 m5 stats/配置 dump 证实生效。

### 工作包 W1：机制核实（依赖：无，可与 W0 并行；产出回填 §2 表）

- §2 九项逐条源码行号级核实：每项给出「xlsx 表述 vs v25.1 实际 vs 对模型行的影响」结论并回填状态列；结论只修正**落点**不修正**故障语义**（同 ooo 06 N 表先例，见 §6）。
- 附加核实（编写期新增）：AGU EA 截获的具体函数与 CHAOSAddrPath 复用/新建裁定；F6 事件枚举到 gem5 事件的映射表（TLB hit/SQ forward/dirty eviction/CAS 成功）。

### 工作包 W2：触发语义 F0–F6（依赖：W1 的事件清单）

- 扩展 `src/cpu/o3/chaos_trigger.hh`：新增 F4（每 100,000 eligible events 触发一次、连续污染 2–4 个 eligible events）与 F6（首次出现指定事件注入一次；事件由 W1 映射表注册）；保持 F0/F1/F2/F3/F5 语义不变。
- attempted/eligible/activated 三计数在触发层统一输出（`src/cpu/o3/chaos_l0.hh` 已有基础，扩展之）。
- 验证：定向负载上 F4 突发长度实测 ∈ [2,4]、F6 首事件命中且仅注入一次（日志为证）；既有 F0–F3/F5 行为回归不变。

### 工作包 W3：观测层 L0–L5（依赖：W2）

- L0 注入生命周期：attempted/eligible/activated、目标 entry/bit 寿命、注入时 commit 序号（04 L0 必采量）。
- L1 影子比对按 04 L1 必采清单扩展 LSU 字段：AGU EA、TLB 映射、SQ 守恒/forward、Cache tag-data-state、exclusive monitor、prefetch queue——复用/扩展 `CHAOSMicroSnap`（ooo W2.4 先例：快照+离线 diff、commit 序号对齐）。
- L2 请求形成与排序：翻译后 PA/size/mask、request ID、replay/violation、issued/dropped/duplicate。L3 缓存/一致性传播：hit/miss、fill/writeback、snoop/ownership、writeback data/address、跨核可见序。
- L4 架构可见：commit 级比较（复用 `CHAOSCommitTrace` + commit-diff 两遍法先例）——首次分歧 commit 序号、错误 load 值/store、污染扇出。
- L5 结局分类 + 守恒式闭合校验（回填工具内建断言）。
- 验证：一次已知注入运行 vs 无故障参照，L0–L5 全链可产出且字段齐。

### 工作包 W4：AGU 注入器（A01–A08，39 格；依赖：W0–W3）

- 全新组件（README §7：runner 20 个分派中无 agu）：挂点按 W1 ⑦ 裁定（lsq_unit EA 计算路径）；含 A04 合法换值（base+imm/LSL/UXTW 等寻址模式由负载 W3 覆盖）。
- 接线：W2 触发 + W3 L0 生命周期 + manifest 扩展块（RunID 贯穿）。

### 工作包 W5：SQ/LQ 注入器（S01–S13 + L01–L04，96 格；依赖：W0–W3）

- 扩展 `CHAOSLSQFwd`（forwarding 场景已有）+ 新建 LQ 生命周期/violation-replay/response 配对注入（L02/L03/L04，文献增量所在）。
- **TC'23 自检锚点**：S01/S13/L01 单 bit 复现 SDC=0%——M2 门，不过关先回修注入器。

### 工作包 W6：L1d-Cache 注入器（C01–C15，76 格；依赖：W0–W3）

- 扩展 `src/mem/cache/CHAOSCache/`（行/tag）+ `CHAOSL1DForward`（post-check 逃逸）；MSHR merge/fill/writeback/dirty eviction 落点按 W1 ⑨ 结论；C13 保护面行在 B0 无保护时标不适用（不填零，README §5.2）。

### 工作包 W7：L1d-TLB 注入器（T01–T10，42 格；依赖：W0–W3 + FS 管线）

- FS-only（Arm TLB 注入器 SE-inert，CLAUDE.md/README §8.2）：挂 `src/arch/arm/` TLB 注入器族；W4 负载（TLB-AliasPerm）FS 管线补齐后才可跑。
- **TC'22 对照锚点**：T01 单 bit 对照 Crash AVF≈50%/Hang≈10%/SDC AVF<1%——M3 门。

### 工作包 W8：原子与同步 + 数据预取器（O01–O09 + P01–P09，84 格；依赖：W0–W3 + 多核 FS）

- O 系：exclusive monitor/原子 RMW 注入（`isa.cc` handleLocked 路径 + `CHAOSExMon` 扩展）；多核 FS 语义按 W1 ⑥ 结论。
- P 系：新建预取器注入器（被测对象 StridePrefetcher 由 W0 ⑤ 挂好）；P01–P03 负对照（出现 SDC 优先怀疑注入器污染 fill 路径，README §5.4）。

### 工作包 W9：负载准备（负载 W0–W13，14 个；依赖：W0，与其他工作包并行滚动）

- 按 06 表逐负载建设：负载 W0 MiniCheck（冒烟）→ W3/W5/W6/W8/W10 SE 定向探针 → W2/W9/W12 SE 优先 → W1/W12 FS 优先 → W4（FS）、W7/W13（多核 FS）→ W11（SPEC，需许可证，主结论后复核）。
- SE 预算纪律（单次运行 wall time 上限，同 ooo A7）；每负载 golden 输出 + oracle 入 `GOLDEN_IDS`。
- 诚实边界：W4/W7/W13 共 65 格在 FS/多核 FS 管线补齐前**不可执行**（README §8.3），在 campaign 里标 blocked 而非静默跳过。

### 工作包 W10：campaign 编排（依赖：W2 + W3 + 首批注入器）

- 自适应样本量两阶段：试跑 30 activated → 筛查 ≥385 → 主结果顺序加样至 Wilson 95% 半宽 ≤2pp 或 5000 activated（05 r13–r15）；复用 `tools/wilson.py`。
- F1–F4 按运行聚类（cluster ID 落盘，05 r19/r20）；每 cell ≥5 个独立 seed 批次（05 r16）；跨模型比较用 common random numbers。
- 回填工具：`tools/backfill_expanded_matrix.py` 扩展到 11 结果列 + col26 记录状态机（待执行→已筛查→主结果）+ 守恒式断言。
- 验证：玩具网格端到端（试跑→筛查→停止规则触发→回填）全链产物齐全。

### 工作包 W11：元分析与报告（依赖：全部）

- 337×11 完整性审计：脚本断言非 blocked 格无空值、守恒式逐格闭合、CI 齐。
- 三问回答 + 位置×SDC 潜力排序 + 结构化 vs 随机翻转增量对照（同字段成对，如 S01 bitflip vs S04 合法换值）+ 事件触发 vs 固定间隔配对结论（F6 vs F1/F2 同模型行）。
- 边界声明：B0 是实验模型非 920 复刻；指标口径不混算；无文献锚点行结论标注探索性。

## 4. 里程碑

| 里程碑 | 包含 | 出口判据 |
|---|---|---|
| M0 平台就绪 | 工作包 W0–W1 | B0 参数落地并证实；§2 九项机制核实全部回填（状态列无「待核实」残留） |
| M1 触发与观测就绪 | 工作包 W2–W3 | F0–F6 七档可用；L0–L5 全链在一次定向注入上端到端产出 |
| M2 SE 单元首批 formal | 工作包 W4–W6 + W9/W10（SE 部分） | AGU/SQ/LQ/Cache 四单元筛查档完成；**TC'23 锚点通过**（LQ/SQ 单 bit SDC=0% 复现） |
| M3 FS 单元 | 工作包 W7 + FS 管线 | TLB 单元可跑；**TC'22 锚点通过**（T01 对照 Crash AVF≈50%） |
| M4 多核 | 工作包 W8 + 多核 FS 管线 | 原子/预取单元可跑；W7/W13 负载解除 blocked |
| M5 全网格回填完成 | W10 全量 | 337 格记录状态全部离开「待执行」（FS 依赖格若管线仍缺，如实标 blocked 并在报告声明——不伪造完成） |
| M6 元分析报告 | 工作包 W11 | 三问回答 + 排序 + 增量对照定稿，每条结论可溯源到 RunID |

推进序（README §6）：AGU → SQ/LQ → Cache → TLB → 原子/预取；自检锚点先于新结论。

## 5. 算力预算

- **量级骨架（activated 计数）**：试跑 337 × 30 ≈ 1.0 万；筛查下限 337 × 385 ≈ **13 万 activated 起**（129,845）；主结果上限 337 × 5000 ≈ **168.5 万**（README §3 底线数字）。
- **activated ≠ 运行数**：每运行产生的 activated 数取决于激活率（attempted→eligible→activated 漏斗），试跑前未知；运行数 = 目标 activated ÷ 每运行 activated 数，**W10 试跑后才能把预算换算成运行数/机时**——本节不编造换算系数，如实保留该不确定性。
- **并发硬上限**：同时运行的 gem5 进程 ≤ **4**（CLAUDE.md：29 GB 主机，超发 OOM 屠批）；campaign 编排器内置槽位限制与崩溃重启，禁止静默屠批。FS/多核运行内存占用更高，M3/M4 阶段按实测单独下调并发数。
- **时间上限**：单次运行超时 = golden wall/sim time 或 committed inst 的 10× + 绝对上限（05 r17）；F5 档可单独提高上限但须预注册。
- **seed 批次倍率**：每 cell ≥5 个独立 seed 批次（05 r16）计入运行数倍率（不改变 activated 目标）。
- **预算纪律**：先 M2（SE 四单元筛查档）实测定机时/格，再滚动外推 M3–M5；每里程碑附实际机时对账，超预算 20% 触发范围复议而不是默默扩样。

## 6. 裁决规则

1. **本文件与 00–08 冲突时，一律以 00–08 为准**（用户指令 2026-09-24；同 ooo 06 先例）。
2. **机制核实结论只修正「落点」，不修正「故障语义」**：注入的故障模型、观测口径、统计规则以源表为准；宿主结构按 vendored v25.1.0.1 实际实现对应（同 ooo 06 N 表先例——落点修正≠设计变更）。
3. **xlsx 文献核对基于上游 stable；本仓机制核实一律对 vendored v25.1.0.1**（08 提取注）；两者差异在 W1 回填时逐条记录。
4. **预期结果是可证伪假设不是实测结论**（00 §3 ⑤）：实测列回填前保持待执行；B0 无保护时保护类行（T09/S12/C13/O08）标不适用，不填零故障率。
5. 引用纪律：后续注入器、campaign、结果回填统一用模型 ID / RunID（spec §3），不发明新编号。
