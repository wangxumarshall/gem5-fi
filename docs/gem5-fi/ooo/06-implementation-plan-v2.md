# gem5-fi OoO 单元故障注入 — V2.0 实现计划

> 状态：**ACTIVE（现行计划）** · 制定 2026-09-28 · 接替 `06-implementation-plan.md`（V1.0 轨道）的"当前计划"地位
> 权威源：`docs/gem5-fi/ooo/gem5-fi-OoO单元故障注入方案V2.0.xlsx`（commit `55c60378`，85,875 B，WPS 生成，zip 内时间戳 2026-09-28 16:50）
> 冲突裁决总则（用户指令 2026-09-28）：**V2.0 是 V1.0 的重大更新版本，一切以 V2.0 为准**——V1.0 文档/数据/平台/口径与 V2.0 冲突处，一律 V2.0 胜出。
> 制定依据：V2.0 九表全量转储 + V1.0↔V2.0 逐项差异报告（310/310 展开重放、91/91 映射覆盖、9/9 转储自校验全部 PASS，
> 工作件在 `.planning/2026-09-22-ooo-fault-injection-implementation-plan/v2-extract/` 与 `v2-delta-report.md`）+
> V1.0 实现基线盘点（`v2-mapping-baseline.md`）。V2-W0 将把忠实层与桥接表入库，使本计划的证据链在仓库内可复现。

---

## 0. 一页总览

**V2.0 不是 V1.0 的增补，而是四个轴同时重写**：

| 轴 | V1.0（已实现 W0-W7 + W8.1/W8.2 + W8.3×24/103 暂停） | V2.0（本计划） |
|---|---|---|
| 平台 | 自拼 4-wide / ROB=128 / IQ=64（A72+gem5 示例估计值） | **gem5 stable `O3_ARM_v7a_3` 基线 B0**：3-wide / ROB=40 / IQ=32 / dispatch=6 / issue-wb-commit=8（+S0-S6 敏感性；SVE 剔除；SE 主跑 + FS 复现强制） |
| 统计 | 四分类 + 固定 n=2000 + 时间基频率 | **activated 序贯**（30→≥385→Wilson 95%≤2pp 或 5000）+ **五类结局 + Simulator failure 单列 + 首检四类** + eligible-event 归一化频率 F0-F6 |
| 粒度 | 91 设计行 × 226 格（17 列） | **57 模型 × 193 子模型 × F0-F6 × 11 负载 = 310 格**（43 列，RunID=模型-频率-负载） |
| 负载 | 8 负载（CoreMark/Embench/GAP/PolyBench/libjpeg + 3 自设核） | **14 定义 / 11 接线**（新增 MiBench-TC23〔FS 优先，TC'23 锚点〕、FP/SIMD 探针、定向译码/重命名/ROB 负载；SPEC 待许可证） |

**核心裁决（§2，共 8 条）**：平台重置 B0；**W8.3 剩余 79 stanza 不原样续跑**（平台/负载/行定义/统计四项失效）——Int Dispatch/ROB 在 V2.0 下以 B 族模型在 B0 上重启；W8.1/W8.2/W8.3 数据封存为 **V1.0-track 历史资产**（与新轨道**永不混数**）；统计引擎先于一切新数据（activated 口径是采集期要求，事后不可重建）；子模型粒度默认 310 格+格内分层记录；91 注入器按 91↔57 桥接表改造复用；M2 门按 V2.0 格定义重过。

**新 WBS（V2-W0…V2-W9，§4）**：忠实层与封存 → 平台 B0 → 触发语义 F0-F6 → 统计引擎 → 负载集 → 观测 L0-L5 → 注入器改造/新建（六族）→ 编排与矩阵 → 三关与量产 → 元分析。约 41+ 实现 patch 单元 + 量产批次（批次=数据提交）。

**里程碑（§5）**：M0' 忠实层 → M1' B0 平台 → M2' 统计引擎 → **M3' TC'23 锚点门（B01×W1×F0，不过不量产）** → M4' 首族量产闭环 → M5' 310 格全量 → M6' 交付。

---

## 1. V2.0 重写面与地基核验

### 1.1 平台基线 B0（已亲验）

V2.0 sheet3「2.OOO参数基线」指定 B0 = gem5 stable `O3_ARM_v7a_3`。**编排者已对照 vendored 源码逐项核验**（`CHAOS/gem5/configs/common/cores/arm/O3_ARM_v7a.py:163-204`，2026-09-28）：

```
fetchWidth=3 · fetchBufferSize=16 · fetchToDecodeDelay=3 · decodeWidth=3 · decodeToRenameDelay=2
renameWidth=3 · dispatchWidth=6 · issueWidth=8 · wbWidth=8 · commitWidth=8 · squashWidth=8
trapLatency=13 · backComSize=5 · forwardComSize=5
numPhysIntRegs=128 · numPhysFloatRegs=192 · numPhysVecRegs=48 · numROBEntries=40
IQ numEntries=32（O3_ARM_v7a_IQ，:158-160）· LQ=16 · SQ=16
```

17 项参数与 V2.0 声明**全等**——B0 是可直接引用的官方配置，非估计值。剩余项（FU 池 `O3_ARM_v7a_FUP`、BiModeBP 分支预测器）在 V2-W1.1 落地时以 config.ini 审计断言逐项确认。
敏感性配置：S0=BaseO3CPU 默认宽核 · S1=4-wide decode/rename · S2=dispatch 8 · S3=无限制即时 squash · S4=IQ64+ROB128+IntPRF192+FloatPRB256+VecPRF64 · S5=ROB192+IntPRF256 · S6=单 FP/SIMD FU。
**ROB=40 恰与 TC'23 的 Armv7/A15 端（ROB 40）对齐**——B01×W1 MiBench-TC23 锚点比 V1.0 更贴论文原文。

### 1.2 统计口径（决定所有新数据可用性）

- **三计数**：attempted / eligible / activated 分开记录；未激活记 Injected-not-activated，不进分母。
- **结局五类 + 单列**：Masked / Detected-contained / Data Corruption / Crash / Timeout；gem5 assert/panic = **Simulator failure 单列**（从结局分母剔除，不记 Hardware RAS）。
- **首检四类**（互斥，与最终结局独立）：Hardware RAS / OS / Application / None；Hardware RAS 只在真实硬件错误报告时记 1，不按注入位置推定。另记 RAS-silent Crash/Timeout。
- **SDC 定义**：首检 None + 正常完成 + 离线 oracle 判 Data Corruption；**SDC率分母 = 可分析 activated（= activated − Simulator failure）**。
- **抽样**：每格先 30 activated 试跑 → ≥385 筛查（95%/5pp）→ 主结果序贯加样至 Wilson 95% 半宽≤2pp 或 activated=5000；每格 ≥5 seed 批次 + 跨模型 common random numbers；F1-F4 为 run-level cluster（事件级仅作传播记录，不得当 Bernoulli 样本，cluster bootstrap 求区间）。
- **超时**：golden sim time 或 committed inst 的 10 倍 + 绝对上限（区分慢化与死锁）。
- **换值合法性（R22）**：必须从当前有效且生命周期合法的候选集合选择，保存 source/target 与候选集大小；禁止空闲/越界/编码非法候选——"不能把随机非法位串称为换值"。
- **共享 ROB**：Int 与 FP/SIMD 同一物理 ROB，按动态指令类型过滤形成互斥 campaign，不重复计数。

### 1.3 设计矩阵与展开（57 × 193 → 310 格）

- 57 模型：Int Decode D01-D09 · Int Rename R01-R09 · Int Dispatch/ROB B01-B10 · FP/SIMD Decode FD01-FD09 · FP/SIMD Rename FR01-FR10 · FP/SIMD Dispatch/ROB FB01-FB10（每单元 9-10 行，六单元均匀化）。
- 193 子模型（`-a/b/c/d/e`）：每行 2-5 个，是 V2.0 新粒度维度。
- 310 格分布：频率 F0=104 / F6=80 / F2=76 / F4=28 / F1=12 / F5=10 / **F3=0**；负载 W9=48 / W5=42 / W10=42 / W8=38 / W4=27 / W6=25 / W3=24 / W7=21 / W13=20 / W11=12 / W1=11（W0/W2/W12 定义未接线）。
- 与 V1.0 的行级关系（91↔57 桥接表，V2-W0.2 入库）：**74 V1.0 行合并为 32 V2.0 行；17 行取消**（"读到旧数据"族 7 行、Int IQ tag 族 5 行、FP/SIMD IQ tag 族 4 行、SVE 谓词 5 行——部分行归多类；"读到旧数据"语义并入换值/提前 ready/lane 拼接子模型）；**D47-D49（IQ ready）跨单元迁移至 R07**；**25 行全新**（时序/事务/状态机 + FP/SIMD 结构化：D07/D08/D09、R04/R08、B05/B08/B09、FD04/FD06/FD07/FD08/FD09、FR04/FR06/FR07/FR08/FR09、FB02/FB03/FB06/FB07/FB08/FB09）。
- **工作簿内部不一致（诚实记录）**：概览声称"模型×子模型×频率×负载全展开"（上限 1050 格），sheet8 实际只展开到模型×频率×负载=310 格，子模型以整格文本附注。裁决见 §2-D4。

### 1.4 观测 L0-L5（层级重划）

| 层 | 内容 | 相对 V1.0 |
|---|---|---|
| L0 注入与激活 | attempted/eligible/activated 三计数 + 目标动态指令/entry/bit + 注入时结构状态 + 目标寿命 + ROB/commit 序号 + source/target | 扩展（V1.0 L0 仅命中/未命中） |
| L1 单元内部状态 | 与同 checkpoint 无故障影子**逐事件**比较；守恒不变量（映射唯一性、free+allocated 守恒、ROB occupancy 守恒、valid/complete 合法转移） | 重定义 |
| **L2 跨单元依赖与分派**（新） | decode→rename→dispatch/IQ 的 src/dst tag、依赖边、FU/opClass steering、ready/issue/replay；与 golden 逐动态指令匹配 | 新增 |
| **L3 执行与写回传播**（新） | FU 输入/输出、完成事件、writeback tag、lane mask、PRF 写入、FPSR/exception、错误值扇出 | 新增（V1.0"污染扇出数"结果列移此为采集量） |
| L4 架构可见与提交 | commit 逐条比对（PC/opcode/架构 src/dst/寄存器值/FPSR/内存副作用/按序/精确异常；时序差异单列；首分歧 commit 序号） | 细化（TC'23 五分类不再是层级定义） |
| L5 检测与最终结局 | 首检四类 + 五类结局 + Simulator failure | 新增（与统计引擎联动） |

V1.0 L3 软件层传播独立观测取消（内容并入 L4/L5 采集量）；"潜伏期"改为 L4 采集量。

### 1.5 负载集（W0-W13）

新增：W0 MiniCheck-OOO（冒烟）· **W1 MiBench-TC23**（10 程序×最大输入集，**FS 优先**，TC'23 锚点负载）· W2 BEEBS-DelayAVF（5 程序，时延对照，未接线）· W3 A64-DecodeProbe · W8 FP-ScalarProbe · W9 NEON-LaneProbe · W13 FP-ExceptionRecovery（FS）。
改制：W4 Rename-Dependency（← dep_chain + branch_mispred 核合并升级）· W5 ROB-Recovery（← rob_fill 升级）· W6 CoreMark+Embench 合并 · W7 GAP（延续）· W10 PolyBench（去 SVE）· W11 libjpeg-NEON（延续）。
W12 SPEC CPU2017 SimPoint 待许可证（主结论后复核，显式 deferred）。

### 1.6 文献基础（sheet9，11 条）

+GEM5 源码两条（B0 参数来源，2026-09-27 在线核对）· HPCA'24 MARVEL · MICRO'25 Harpocrates++ · **CHAOS26（arXiv 2602.02119）** · DATE'25 From Gates to SDCs · 本地案例笔记（仅候选生成不作定量）。**Veritas 不再被引用**；CHAOS 频率-结局规律不再作为档位设计依据。

---

## 2. 关键裁决（编排者，依据 V2.0 + 基线事实）

| # | 裁决 | 依据与后果 |
|---|---|---|
| **D1** | **平台重置 B0**：`ooo_proxy.py` 从 4-wide/ROB=128 改为逐参数引用 `O3_ARM_v7a_3`；S0-S6 做成命名预设 | V2.0 sheet3；B0 已亲验（§1.1）。现平台全部绝对数值在 V2.0 口径下不可比。PRF 128/192/48 恰与现平台一致，golden 风险降低 |
| **D2** | **W8.3 不续跑**：剩余 79 stanza（含 s21/d30 重跑）不按原样执行；Int Dispatch/ROB 量产在 V2.0 下以 B01-B10 × 新负载 × 新口径于 B0 重启 | 平台、负载（B 族主负载改 W1/W5/W7）、行定义（D50-D54 取消、D47-49 迁移、B05/B08/B09 新增）、统计口径四项同时失效，续跑产物无法进入 V2.0 矩阵 |
| **D3** | **V1.0-track 封存**：W8.1（8008）、W8.2（72,024）、W8.3 已完成 24 stanza（≈22,024，未提交）全部按 V1.0 口径归档提交并标注 track=v1.0；21/226 回填格为 V1.0-track 专属资产；**V2.0 310 格 100% 待执行，两轨数字永不混用** | activated/首检是采集期口径，事后无法从现有 run 产物重建；CLAUDE.md 双轨道不混数纪律的第三次应用（鲲鹏/V1.0-OoO/V2.0-OoO 三轨并存）。W8.3 数据在 /tmp 与 runs/ 工作区，须最先归档（在险） |
| **D4** | **子模型粒度 = 310 格 + 格内子模型分层记录**：每个 run 记录其子模型 ID，回填按 子模型×格 双层聚合；仅当格内子模型结果显著分歧时对该格做 1050 式定向展开 | sheet8 实际只展开 310 格（与概览 1050 声明不一致，§1.3）；分层记录保留全部子模型信息且不放大矩阵管理成本 |
| **D5** | **统计引擎先于一切新数据**：V2-W3（三计数/五类+首检/序贯停止）必须在新平台第一批 formal 数据之前落地并验证 | 口径是采集期属性；先跑数据后改口径=重蹈 V1.0-track 不可比覆辙 |
| **D6** | **91 注入器 = 模式库**：按 91↔57 桥接表改造复用（74 行有 V2.0 后裔）；17 取消行的模式代码保留、退出 campaign（防口径漂移的代码考古价值）；25 新行按族实现 | 注入器是模式参数化 SimObject，改造面=模式定义+候选集合合法性+source/target 记录；FP/SIMD 三单元是新增大头 |
| **D7** | **频率语义换轨 F0-F6**：`chaos_trigger.hh` 增加 eligible-event 归一化模式（F1=1/1M、F2=1/100k、F3=1/10k、F4=突发 2-4、F5=warm-up 后单 bit 永久、F6=首次确定性事件）；V1.0 时间基模式保留为 legacy 开关 | F3 设计矩阵未使用（310 格 F3=0），实现但不上量；F6 取代 V1.0"事件触发"行的时间语义 |
| **D8** | **W1 FS 优先走 LSU 轨道 FS 管线经验**（checkpoint 恢复 tick 基准=目录名、4-slot 硬上限、rcS 载荷）；SE 冒烟先行、FS 主跑随后；"每个主结论至少一个 FS 负载"列入批次完成协议 | V2.0 sheet3 R23 运行模式条款；本仓 FS 管线（checkpoint+TLB+PTW）已在 LSU 轨道验证 |

---

## 3. 资产映射（复用 / 改造 / 新建）

### 3.1 直接复用（V1.0 交付物，~40 个 feat(ooo) 提交）

| 资产 | V2.0 去向 |
|---|---|
| chaos_trigger.hh 共享触发层（F0-F5 + 5 断言组单测） | 扩展为 F0-F6 事件归一化（V2-W2），legacy 模式保留 |
| 91 注入器模式库（CHAOSDecode / RenameMap / FreeList / ROB / IQ + FP 参数化 + 自挂接机制） | 按桥接表映射 57 模型；25 新行同骨架新增 |
| CHAOSProbe + event_density.py | 密度口径重定义为 eligible-event 流（V2-W2/W5） |
| CHAOSCommitTrace（debug-flags 全等验证过）+ commit_diff.py | L4 基础，按逐项比对细化 |
| CHAOSMicroSnap + micro_diff.py | L1 基础，向守恒不变量口径改造 |
| fanout.py / chaos_l0.hh 生命周期契约 | L3 / L0 骨架 |
| campaign 引擎骨架 / runner 组件路由 / manifest 机制 / 回填+审计方法论 | 序贯化改造（V2-W3/W7） |
| 负载资产：CoreMark、Embench 6、GAP、PolyBench 4、libjpeg-NEON、smoke、三探针核 + golden 方法论（native==gem5 位级一致 + GOLDEN_IDS） | → W6/W7/W10/W11 与 W4/W5 原料；全部在 B0 重注册 golden |
| 96 路资源纪律、300s hang 裁决、SimErr 调查协议、完成协议机械化、LSU FS 管线经验 | 批次纪律直接继承 |

### 3.2 改造（现有代码换轨）

`ooo_proxy.py`→B0+S0-S6 · `classify.py`→五类+首检 v2（保留 v1 分类函数供 V1.0-track 审计）· `campaign.py` two_phase→序贯停止 · 回填/审计→43 列 schema · 四份伞形 yaml→310 格矩阵生成器 · drivers→V2 批次链（修链标记 bug 教训：完成标记字符串统一）。

### 3.3 新建

25 新模型行 · W0/W1/W2/W3/W8/W9/W13 负载 · L2/L3 观测层 · F4/F5/F6 触发模式 · 序贯停止引擎 · 91↔57 桥接表 · V2.0 忠实层（9 表）。

---

## 4. 工作分解结构（V2-W0…V2-W9；每单元 = 一个验证过的 patch）

> 执行纪律继承 CLAUDE.md：one-patch-per-unit（构建零新警告 + 真机定向验证 + golden 回归 → commit → push 非 main）；
> patch 严格串行；只读机制 spike 可并行（≤2 subagent）。本节 ~41 实现 patch 单元 + 量产批次（批次=数据提交单元）。

### V2-W0 忠实层 · 桥接 · V1.0-track 封存（3 单元）— *立即执行*
- **W0.1 V2.0 忠实层提取入库**：`extract_v2.py`（纯 stdlib，WPS 兼容）→ `docs/gem5-fi/ooo/v2/` 九表忠实层（00-08 对应 md/csv + 全量 TSV 转储）+ 展开重放断言（57 行适用频率×适用负载 = sheet8 310 行逐行全等）+ RunID 唯一性 + 公式行标注。
- **W0.2 91↔57 桥接表入库**：映射 CSV（V1.0 D-id → V2.0 模型ID/子模型，含 合并/取消/迁移/新建 四类标注）+ 程序断言 91 全覆盖恰一次 + V2.0 v2/ 目录 README。
- **W0.3 V1.0-track 封存提交**：W8.3 24 stanza（≈22,024 run）统计+归档（track=v1.0 标注）+ V1.0-track 收官报告（21/226 格、Q1 排序 D29 10.41%>D17 6.05%>D13 4.91%、M2 结果、6 项平台发现、15 格边际差额显式声明不补、W8.6/W8.7 意图转入 V2.0 对应物）。
- 验收：extract_v2 重跑逐字节一致；桥接断言 PASS；封存数据可从 git 恢复。

### V2-W1 平台基线 B0（3 单元）
- **W1.1 ooo_proxy B0 化**：参数逐项引用 `O3_ARM_v7a_3`（§1.1 已核验 17 项；FU 池/分支预测器随 config.ini 审计断言确认）+ S0-S6 命名预设 + C0 回归不破坏。
- **W1.2 B0 golden 重确立**：11 接线负载 native==gem5 位级一致 ×2 + GOLDEN_IDS v2 注册 + 探针密度表 B0 重测（eligible-event 口径）。
- **W1.3 观测无扰动复证**：probe 开销（V1.0 基线 +0.16%）+ CommitTrace 纯读门 + C0 golden。
- 验收门 **M1'**：config.ini 逐参数 == O3_ARM_v7a_3；11 负载 golden 稳定；探针开销 <1%；C0 回归 pass。

### V2-W2 触发语义 F0-F6（2 单元）
- **W2.1 eligible-event 归一化模式**：per-site eligible 事件流钩子 + F1/F2 事件间隔注入 + F4 突发 2-4 + F6 首次确定性事件（单发）+ 单测扩展。
- **W2.2 F5 修订 + legacy 兼容**：warm-up 后首个 eligible 起永久 + 单 bit/字段约束；V1.0 时间基模式保留开关（V1.0-track 复现用）。
- 验收：每档定向单次注入真机证据（事件序号精确命中）+ 同 seed 确定性 + F0-F6 单测全 PASS。

### V2-W3 统计引擎（4 单元）— *先于一切新 formal 数据（裁决 D5）*
- **W3.1 三计数口径**：attempted/eligible/activated 注入器侧记录（chaos_l0.hh v2）+ runner 解析 + Injected-not-activated 显式结局。
- **W3.2 classifier v2**：五类 + Simulator failure 单列 + 首检四类 + RAS-silent + 换值候选集合/source/target 记录；v1 分类函数保留（V1.0-track 审计）。
- **W3.3 序贯停止引擎**：30 activated 试跑 → ≥385 筛查 → Wilson 95%≤2pp / 5000 activated 停止 + ≥5 seed 批次 + CRN 清单 + cluster bootstrap（F1-F4）+ 10× golden 超时。
- **W3.4 结果 schema v2 + 回填/审计 v2**：43 列（含检测计数差额/结局计数差额两个应为 0 的审计列）+ 子模型分层聚合 + audit G 清零规则。
- 验收门 **M2'**：合成玩具网格 + 真实小批端到端——三计数自洽、五类互斥穷尽、Wilson 区间正确、审计差额=0、序贯停止点符合规则。

### V2-W4 负载集 W0-W13（6 单元）
- **W4.1 W0 MiniCheck + W3 A64-DecodeProbe**（自设探针；W0 为全注入器冒烟载体）。
- **W4.2 W4 Rename-Dependency + W5 ROB-Recovery**（由 dep_chain/branch_mispred/rob_fill 原料改制；B0 密度门重校准——rename skid 平台属性结论需在 ROB=40 复核）。
- **W4.3 W6/W7/W10/W11 迁移**（CoreMark+Embench 合并、GAP、PolyBench 去 SVE、libjpeg-NEON；B0 golden 重注册）。
- **W4.4 W8 FP-ScalarProbe + W9 NEON-LaneProbe**（NaN/Inf/±0/subnormal/舍入/FPSR oracle；8/16/32/64-bit lane、widen/narrow、permute、reduce、逐 lane 比对）。
- **W4.5 W1 MiBench-TC23**（10 程序最大输入集：blowfish/patricia/fft/gsm/dijkstra/rijndael/sha/bitcount/edge/smooth；SE 冒烟 + **FS 主跑**，复用 LSU checkpoint 纪律与 4-slot 上限）。
- **W4.6 W2 BEEBS-DelayAVF（5 程序对照）+ W13 FP-ExceptionRecovery（FS）**；W12 SPEC 显式 deferred（许可证）。
- 验收：每负载 golden 位级一致（SE）/FS 可复现；W0 冒烟对全部 57 模型可激活性预检；B0 密度表入库。

### V2-W5 观测链 L0-L5（5 单元）
- **W5.1 L0 v2**（三计数+目标寿命+ROB/commit 序号+source/target+候选集大小——与 W3.1 同一契约）。
- **W5.2 L1 守恒不变量**（映射唯一/free+allocated/ROB occupancy/合法转移；MicroSnap 改造）。
- **W5.3 L2 跨单元依赖与分派**（tag/依赖边/steering 逐动态指令 vs golden——新 trace，CommitTrace 模式扩展）。
- **W5.4 L3 执行与写回**（FU in/out、wb tag、lane mask、FPSR、扇出；fanout.py 扩展）。
- **W5.5 L4 细化 + L5 接线**（逐项比对含 FPSR/内存副作用/按序/精确异常 + 首检/结局与 classifier v2 联动）。
- 验收：每层合成+真实定向样本；全链无扰动门（golden 不变）。

### V2-W6 注入器改造与新建（六族，12-16 单元；25 新行主体在此）
- **W6.R Int Rename R01-R09**：7 行复用改造（含 D47-49→R07 ready/busy 迁移）+ 新增 R04（new/old-dest 换值）R08（rename 事务原子性）。
- **W6.B Int Dispatch/ROB B01-B10**：remap（B01←D25/D28/D36、B02←D26/D29/D37/D42、B03←D30/D38、B04←D32-D35、B06←D41/D44/D45〔翻转→合法换值〕、B07←D55、B10←D27/D31/D39/D43/D46）+ 新增 B05（exception/mispredict/serialize）B08（squash 时序）B09（commit 事务）；IQ tag 族退役。
- **W6.D Int Decode D01-D09**：子模型化 remap（D01←D01/D04/D06 等）。
- **W6.FD FP/SIMD Decode FD01-FD09** / **W6.FR FP/SIMD Rename FR01-FR10** / **W6.FB FP/SIMD Dispatch/ROB FB01-FB10**：FR08 partial-write、FB06 完成配对、FB07 lane mask、FD06 FPCR 等 25 新行的 FP 部分集中于此。
- 共通验收（每单元）：构建零新警告 + 定向单次注入证据（含 activated 判定与 source/target 日志）+ B0 golden 回归 + 候选集合合法性断言（R22）。
- 前置：W6.B/W6.FR 的 B05/B08/B09/R08 等事务/时序行挂点先做只读机制 spike（rename 提交路径、squash 广播、commit 事务边界），≤2 subagent 并行。

### V2-W7 编排与矩阵（3 单元）
- **W7.1 310 格矩阵生成器**：RunID=模型-频率-负载 + 子模型分层记录格式 + 与 V2.0 sheet8 逐行全等断言。
- **W7.2 campaign 引擎 v2**：序贯编排（pilot 30→筛查 385→主结果循环）+ FS 复现调度（4-slot）+ SE/FS 混排资源纪律。
- **W7.3 driver 链 v2**：六族批次顺序（R→B→D→FD→FR→FB，先已有 V1.0 数据的 R/B）+ 互锁守卫（完成标记字符串统一——V1.0 链 W3/W8.3 标记 bug 教训）+ 监控。
- 验收：玩具网格 pilot→序贯→停止→回填全链端到端；守卫 grep 与打印逐字一致。

### V2-W8 三关与量产（批次=数据提交）
- **W8.0' TC'23 锚点门（M3'，不过不量产）**：B01×W1×F0 于 B0——ROB=40 与 TC'23 A15 端对齐 + W1 同负载，预期"SDC 接近 0 且 Masked/Crash 主导"（口径：到达软件层的 non-Benign 故障中产生 SDC 的比例）；配阴性/阳性对照。
- **W8.1'-W8.6' 六族量产**：每族 = 30-activated 试跑（发现零激活/全 Crash）→ 筛查 → 序贯主结果 → 回填（43 列）→ audit → 数据提交；**每个主结论至少一个 FS 负载复现**（W1/W13 + 关键格 FS 复算）；SimErr 调查协议沿用。
- **W8.7' S0-S6 敏感性 campaign**（关键格：轨道头部模型 × S 变体）。
- 验收：每批 activated 达标 + Wilson CI + 审计差额列=0 + audit G 清零。

### V2-W9 元分析与交付（3 单元）
- **W9.1' 全量回填 + 完整性审计**（310 格无空值非 deferred + CI 齐 + 子模型分层完整）。
- **W9.2' 元分析报告**（新口径）：单元/模型/子模型三级 SDC-per-可分析activated 排序 · 结构化 vs 随机（接 V1.0 Q3a 25-40× 假设重验）· 首检层级分布与 RAS-silent 占比 · 激活率谱 · 序贯 vs 固定 n 方法论对照 · S0-S6 敏感性结论 · V1.0/V2.0 双轨演化诚实记录。
- **W9.3' 论文素材**：TC'23 锚点复现章节（B01×W1）、SVE/S12/W0-W2 未接线边界声明、双轨声明。
- 验收：结论每条带 模型ID/RunID 与样本量；audit 全绿。

---

## 5. 里程碑

| 门 | 内容 | 通过判据 |
|---|---|---|
| M0' | V2-W0（忠实层+桥接+封存） | 提取断言全 PASS；V1.0-track 数据入 git |
| M1' | V2-W1（B0 平台） | config.ini==O3_ARM_v7a_3；11 负载 golden；探针 <1% |
| M2' | V2-W3（统计引擎） | 玩具+真实端到端；审计差额=0 |
| **M3'** | **W8.0' TC'23 锚点门** | B01×W1×F0 SDC≈0（可分析 activated 口径）且 Masked/Crash 主导；对照齐 |
| M4' | 首族量产闭环（Int Rename R01-R09） | 9 模型×格 序贯达标+回填+audit |
| M5' | 310 格全量回填 | audit G 清零 |
| M6' | 元分析+交付 | W9.2'/W9.3' 验收 |

依赖序：W0→W1→{W2,W3}→W4→W5→W6（R→B→D→FD→FR→FB）→W7→W8.0'→W8 量产→W9。W3（纯工具）可与 W2/W4 交错；W4.5（W1 FS）与 W6 前段并行准备。

---

## 6. 规模与算力账（派生估算，V2.0 未给总量——所有数字必须如此标注）

- 每格 activated 需求：SDC≈0 格 Wilson 半宽≤2pp 需 n≈190；p≈0.5 最坏 ≈2400；上限 5000。310 格 ⇒ **约 0.35M-0.9M activated**；除以激活率（0.3-1.0，W0 试跑实测后修正）⇒ **约 0.4M-1.2M attempted run**。
- SE 主跑：按 W8.2 实测吞吐（72,024 run / ~2 天 @96 路）⇒ **约 2-5 周**。F5/F6 单发格便宜；F1/F2 多事件格与卡死族贵（300s hang 等待）。
- FS 复现：4-slot 硬上限另行排期（W1 11 格 + W13 20 格 + 主结论复算格）。
- 资源纪律沿用：96 路 / P0 ≥14G / ~105MB·gem5⁻¹ / 300s hang / 与 LSU 轨道共存（watchdog 8G、构建窗口协调）。

---

## 7. 风险登记册

| # | 风险 | 缓解 |
|---|---|---|
| R1' | B0 参数与 vendored gem5 漂移 | 已亲验 17 项全等（§1.1）；W1.1 config.ini 审计断言锁死 |
| R2' | 子模型粒度不一致（310 vs 1050） | 裁决 D4：310+分层记录；分歧格定向展开 |
| R3' | W8.3 数据在险（/tmp + runs/ 未提交） | W0.3 最先归档（本计划第一优先数据单元） |
| R4' | activated 口径事后不可重建 | 裁决 D5：统计引擎先行；W0 试跑即带三计数 |
| R5' | 25 新行机制风险（事务/时序挂点） | W6 前只读 spike（≤2 subagent 并行）；honest-reject 条款保留 |
| R6' | W1/W13 FS 依赖（checkpoint/4-slot） | 复用 LSU 轨道已验证管线；SE 冒烟先行 |
| R7' | 双轨混数 | campaign_id `v2_` 前缀 + 矩阵文件分离 + manifest track 字段 + 论文双轨声明 |
| R8' | 与 LSU 轨道机器竞争 | 96 路纪律 + watchdog + 构建窗口协调（V1.0 期间零污染先例） |
| R9' | 序贯引擎复杂度（CRN/bootstrap） | 先玩具网格再真跑；W3.3 单测覆盖停止规则全分支 |
| R10' | 取消行代码误用 | 17 行模式代码标注 deprecated-in-v2-campaigns；campaign 生成器白名单拒绝 |

---

## 8. 执行纪律（继承 + 修订）

1. one-patch-per-unit、构建零新警告、真机定向验证、golden 回归、commit→push 非 main——全部继承 CLAUDE.md。
2. patch 严格串行；只读 spike ≤2 subagent 并行（用户指令上限）。
3. 批次完成协议沿用：统计 → §5.5 完整性调查 → 回填 dry-run → 正式回填 → audit → 数据提交 → 下一 driver。
4. 诚实公约：n/a 显式化、deferred 显式声明（W12/SVE/F3）、pilot 永不入结果列、双轨不混数、派生估算必标注。
5. 机制 spike 结论先于实现（B05/B08/B09/R08 等事务行挂点）。

## 9. 立即下一步（本计划获批后的前三个单元）

1. **V2-W0.1**：`extract_v2.py` 入库 + `docs/gem5-fi/ooo/v2/` 忠实层生成与断言。
2. **V2-W0.2**：91↔57 桥接表入库（映射 CSV + 覆盖断言）。
3. **V2-W0.3**：V1.0-track 封存提交（W8.3 22k run 归档 + 收官报告）。

> 本文档由编排者基于 V2.0 全量提取（310/310 重放断言）与 V1.0 基线盘点制定；后续修订在本文件追加变更记录，不改写历史结论。
