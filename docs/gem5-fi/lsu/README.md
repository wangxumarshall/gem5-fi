# LSU 单元故障注入北极星 — README 总纲

> 本文件是**导航与综合层**，不是源表转录：数字与原文以 00–08 文档和两个 CSV 为准，若与本 README 有出入，一律以 00–08 为准。
> 源工作簿：`gem5-fi-LSU单元故障注入方案V1.0.xlsx`（sha256 见 §9），提取日期 2026-09-24，分支 `fi-ding`。

## 1. 北极星目标

本方案围绕 LSU 故障注入的三个问题组织全部实验：

1. **哪些位置有真实 SDC 潜力？** LSU 七个单元（AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器）中，区分真正能产生静默数据损坏的位置与只影响性能/只会崩溃（DUE/Crash）的位置。
2. **SDC 之前，微架构层有哪些可观测前兆？** 通过 L0–L5 传播链（04-observation-points.md）在架构可见错误之前捕获局部偏差——L1 影子比对、请求配对、提交首分歧——为在线检测提供锚点。
3. **结构化模型相对随机翻转的增量有多大？** 随机位翻转大多被非法编码检查、依赖检查或异常拦截（TC'23 实测 LQ/SQ SDC=0）；合法换值、状态、时序与保护类模型专门测试这些检查之外的静默路径。

总述：**7 个单元 × 68 个设计模型 × 337 个展开实验格**，从源 xlsx 忠实提取到本目录（00–08 文档 + 2 个 CSV，由 `verify_extraction.py` 逐格回比），本 README 提供地图、数字总账、方法主张、实施顺序与仓库基础设施映射。

## 2. 文档地图

| 源工作表 | 本目录文件 | 规模 |
|---|---|---|
| 表0（0.说明与总览） | `00-overview.md` | 24 个非空行 |
| 表1（1.单元与现有研究） | `01-units-and-research.md` | 7 单元 × 7 列 |
| 表2（2.LSU参数基线） | `02-parameter-baseline.md` | 19 参数 × 5 列 |
| 表3（3.位置x模型矩阵） | `03-design-matrix.md` + `design-matrix.csv` | 68 模型 × 12 列 |
| 表4（4.观测点定义） | `04-observation-points.md` | L0–L5 共 6 行 × 6 列 |
| 表5（5.频率与统计） | `05-frequency-and-sampling.md` | F0–F6 七档 + 9 个统计项 |
| 表6（6.负载清单） | `06-workloads.md` | W0–W13 共 14 负载 × 6 列 |
| 表7（7.展开执行矩阵） | `07-expanded-matrix.csv` + `07-expanded-matrix.md` | 337 格 × 27 列 |
| 表8（8.文献与来源） | `08-references.md` | 11 条 × 6 列 |
| —（源文件） | `gem5-fi-LSU单元故障注入方案V1.0.xlsx` | 9 个工作表，sha256 见 §9 |
| —（工具） | `extract.py` | 机械再生成器 + 内嵌自校验 |
| —（工具） | `verify_extraction.py` | 独立校验器（CSV 逐格回比 + 片段检查 V4a–V4c） |
| —（后续交付） | `09-implementation-plan.md` | 实施总纲（Task 7 交付，非源表转录） |

## 3. 数字总账

**68 个设计模型（7 单元分布）**：AGU=8（A01–A08）、L1d-TLB=10（T01–T10）、Store Queue=13（S01–S13）、L1d-Cache=15（C01–C15）、原子与同步=9（O01–O09）、数据预取器=9（P01–P09）、Load Queue=4（L01–L04）。完善版构成 = 原 58 条（Excel r2–r59）+ 追加 10 条（r60–r69：T10、S13、L01–L04、C14、C15、O09、P09）。

**337 个展开实验格**（= 设计矩阵「适用频率 × 适用负载」全叉积，extract.py A1 重放验证）：

| 维度 | 分布 |
|---|---|
| 频率 | F0=109 · F1=24 · F2=77 · F3=4 · F4=26 · F5=29 · F6=68 |
| 单元 | AGU=39 · L1d-TLB=42 · Store Queue=66 · L1d-Cache=76 · 原子与同步=31 · 数据预取器=53 · Load Queue=30 |
| 负载 | W0=6 · W1=27 · W2=6 · W3=24 · W4=27 · W5=57 · W6=58 · W7=32 · W8=25 · W9=15 · W10=27 · W11=12 · W12=15 · W13=6 |
| 完善版 | 10 个追加模型共 77 格（原 58 模型 260 格） |

**自适应样本量口径**（05-frequency-and-sampling.md）：每格先试跑 **30 个 activated** → 正式筛查 **≥385 个 activated**（95% 置信、最坏 p=0.5、约 ±5pp）→ 论文主结果按 **Wilson 95% 区间半宽 ≤2pp 或 activated 达到 5000** 停止；F1–F4 按运行聚类计算区间，不得把同一运行内事件当独立 Bernoulli 样本。

**规模量级估算**：仅筛查下限就是 337 格 × 385 ≈ **13 万次 activated 起**（129,845）；若主结果普遍触到 5000 上限，量级至 337 × 5000 ≈ 168.5 万。这是排期与算力预算的底线数字。

## 4. 设计边界（源表原文）

1. **B0 是可复现实验模型，不是鲲鹏 920 复刻**（00 §1「重要纠正」原文）；cache ports=200 不是物理端口数，2.6GHz 仅用于换算。
2. **指标口径严禁混算**（01 提取注）：AVF、非 Benign 条件占比、总 AVF、检测率、DelayAVF 是五种不同口径，跨文献比较必须先对齐口径。
3. **SDC 率分母 = activated**（04 L0 / 05 r12）：`SDC率=SDC/activated；激活率=activated/attempted` 两者必须同时报告；未 activated 的注入单列 Injected-not-activated。
4. **F0 与 F1–F4 不混为一个故障率**（00 §3 ②）：F0 单次故障用于 AVF/论文对照；F1–F4 是重复/突发压力实验；F5 永久故障按运行分类。
5. **预期结果是可证伪假设，不是实测结论**（00 §3 ⑤）：无论文直接结果的 AGU、原子/同步和多数结构化模型，实测列必须保持待执行。

## 5. 方法的核心主张

从 03 设计理由列归纳（每条注明出处模型 ID；引号为源表设计理由原文摘录）：

1. **结构化合法值替换绕过地址异常**：随机翻转高位多成异常/Crash、非法编码多被拦截；把字段换成「另一个满足对齐、范围、编码和生命周期约束的合法值」专门命中静默路径。A04「专门检验"合法但错误地址"这一随机翻转难命中的路径」、T04「构造合法映射以测静默上限」、S04「绕开地址异常后预期SDC高」、C05「合法false hit…绕开无效地址与自然miss防线」、O07（交换合法 order tag）。
2. **保护链本身是故障面**：T09「验证保护链本身而非只攻击数据」、S12「把保护作为显式故障面…攻击保护链可把DUE变成SDC」、C13「直接评估保护机制自身的单点失效」、O08「为未来保护实现预留，不在B0强行假定存在」；B0 无保护时这些行标不适用，不允许填成零故障率。
3. **L1 影子比对作为 SDC 前兆观测**：04 L1 定义「与无故障影子副本比较该单元状态，捕获SDC之前的局部偏差」；03 中 SQ 系模型（S01–S13）的传播链列均挂「影子SQ」——在 L4 架构可见之前给出微架构级前兆，直接服务北极星第二问。
4. **负对照与守恒校验**：C10（replacement「作为负对照验证"只影响性能"的假设」）、P01/P02/P03（预取地址/控制错误不应改变架构结果，检验 TC'23 排除理由的边界——若出现 SDC 优先怀疑注入器污染了 fill 路径）；L5 守恒式 `Activated = Masked + Detected + SDC + Crash + Timeout` 作为每格回填的闭合校验。
5. **生命周期/时序/事务配对是随机翻转的盲区**：S06（store 生命周期状态）、S11（request/ack 握手）、C12（fill/writeback 事务配对，「tag-data错配是高风险SDC」）、L02/L03/L04（LQ 生命周期、violation/replay、response 配对）、P05（需求-预取竞争配对）。TC'23 的 LQ/SQ SDC=0 恰说明 commit 前依赖检查拦住了随机翻转，而这些模型测试检查之外的路径（S04 设计理由）。
6. **Crash 双拆分对应 L5 分类**：04 L5「Crash区分gem5断言与架构崩溃」，把模拟器伪影与真实架构崩溃分开统计，避免把 gem5 断言误计为架构脆弱性（预期列如 A01「高位翻转多为异常/Crash」的验证依赖此拆分）。

## 6. 实施顺序

**源表自带验证锚点优先**（先证明注入器本身正确，再谈新结论）：

1. **LQ/SQ 单 bit 复现 TC'23 的 LQ/SQ SDC=0%**（01：「TC'23：LQ/SQ SDC概率均为0，论文归因于commit前依赖检查」）——用 S01/S13/L01 对照 TC'23 的 2000 次/负载设置做注入器自检；复现不出 0% 先怀疑注入器。
2. **T01 DTLB 单 bit 对照 TC'22**（01：「平均Crash AVF约50%、Hang约10%、SDC AVF<1%」）。
3. **完善版 LQ 行（L01–L04）是文献增量所在**：现有文献只覆盖 LQ 存储字段（TC'23/HPCA'24/IISWC'15），L02 生命周期、L03 violation/replay、L04 response 配对无直接实测。

**单元排序**：AGU → SQ/LQ → Cache → TLB → 原子/预取。理由：AGU/SQ/LQ/Cache 的模型在 SE 模式可跑且带文献锚点或自设探针（W3/W5/W6）；TLB 注入器 FS-only（见 §7/§8）；原子与预取依赖多核 FS 与新建注入器，后置。逐阶段落地见 `09-implementation-plan.md`。

## 7. 与本仓库现有基础设施的映射（2026-09-24 grep 核实）

以下「仓库现状」列全部来自当日实际执行的 grep/ls 输出（证据原文见任务报告）；未命中的项如实列入「需要新建」。

### 复用（grep 命中，附 file:line 证据）

| 方案需要 | 仓库现状（grep 证据） |
|---|---|
| SQ store-to-load forwarding 注入（S01–S13 部分位置） | `tools/runner.py:956` `elif comp == "lsq_fwd":`；`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/` 目录存在 |
| L1d-Cache 行/tag 注入（C01–C15 部分位置） | `tools/runner.py:1034` `elif comp == "l1d_fwd":`；`src/cpu/o3/CHAOSL1DForward/` 存在；`src/mem/cache/CHAOSCache/`（CHAOSCache.cc/.hh/.py/SConscript 四件套）存在 |
| 地址通路观测 | `tools/runner.py:1206` `elif comp == "addr_path":`；`src/cpu/o3/CHAOSAddrPath/` 存在 |
| L1d-TLB 注入（T01–T10） | `tools/runner.py:1155` `elif comp == "l1_tlb":`（`:1159` requires platform）——Arm TLB 注入器为 FS-only、SE-inert（见 §8） |
| O3 实验平台配置家族 | `configs/se/ooo_proxy.py`、`configs/se/kp920_proxy.py` 均存在（ls 确认） |
| B0 预取器代理（P01–P09 的被测对象） | `CHAOS/gem5/configs/common/cores/arm/O3_ARM_v7a.py:246-247`：`# Simple stride prefetcher` / `prefetcher = StridePrefetcher(degree=8, latency=1, prefetch_on_access=True)`；`src/mem/cache/prefetch/`（base.hh 等基类）存在 |
| F0/F1/F2/F3/F5 触发语义（5/7 档） | `CHAOS/gem5/src/cpu/o3/chaos_trigger.hh:23-26`：`enum class ChaOSTier : uint8_t { F0, F1, F2, F3, F5 };` |
| Wilson 95% CI 计算（主结果停止规则） | `tools/wilson.py` 存在；`tools/backfill_expanded_matrix.py:93` `from wilson import wilson_ci` |
| FS 单核管线（W4 等 FS 依赖负载） | `configs/fs/kp920_proxy_fs.py` 存在（`:41` `cpu0 = core0.core`，单核 V110 代理） |

### 需要新建（grep 未命中或不存在）

| 方案需要 | 仓库现状（grep 证据） |
|---|---|
| AGU 注入器（A01–A08） | `tools/runner.py` 组件分派共 20 个（gpr/physreg/memory/rat/freelist/rob/iq/lsq_fwd/exec/fsu/l1d_fwd/bpu/decode/l1i/l1_tlb/sysreg/exmon/ras/addr_path/ptw），**无 agu**；`grep -n "prefetch\|agu\|atomic" tools/runner.py` 零命中；`src/cpu/o3/` 无 AGU 类 CHAOS 注入器目录 |
| 原子与同步注入器（O01–O09） | 同上：无 atomic 组件分支、无对应注入器目录 |
| 预取器注入器（P01–P09） | 同上：无 prefetch 组件分支（被测对象 StridePrefetcher 已在，缺的是注入器） |
| LQ 生命周期/响应配对注入器（L01–L04） | `src/cpu/o3/` 仅有 `CHAOSLSQFwd`（forwarding 场景）；`lsq.hh`/`lsq_unit.hh` 是 gem5 基础实现而非注入器；无 LQ 生命周期类注入器 |
| F4（短突发）/ F6（确定性事件触发）触发语义 | `chaos_trigger.hh` 枚举仅 `F0, F1, F2, F3, F5`；全文件 grep F4/F6 零命中——而展开矩阵有 F4=26 格、F6=68 格依赖这两档 |
| 自适应样本量两阶段编排（试跑 30 → 筛查 ≥385 → 主结果停止规则） | `tools/campaign.py` grep `385\|试跑\|adaptive` 零命中（唯一 stage 命中是 `:391` `fault_stage`，保护模型阶段，与样本量无关）；Wilson 计算可复用 `tools/wilson.py`，缺的是编排层 |
| 多核 FS（W7 Atomic-Litmus、W13 PARSEC、C08 完整一致性协议） | `configs/fs/` 仅 `kp920_proxy_fs.py`（单核）；无多核 FS 配置 |

## 8. 诚实声明

1. **《LSU单元参数总表.md》不在本仓库**：B0 定值以内嵌表 2（`02-parameter-baseline.md`）为准（00 提取注）。
2. **TLB 注入器 SE-inert**：本仓 Arm TLB 注入器按构造 FS-only（`tools/runner.py:1159` `component 'l1_tlb' requires platform`），T01–T10 没有 SE 直接路线。
3. **W4/W7/W13 FS 结构性缺口**：06 模式列——W4（TLB-AliasPerm）=FS、W7（Atomic-Litmus）=多核 FS、W13（PARSEC-Selected）=多核 FS；当前仓库只有单核 FS 代理，这三组负载共 65 格（W4=27、W7=32、W13=6）在 FS/多核 FS 管线补齐前无法执行。
4. **文献核对基于上游 stable**（2026-09-24 核对），本仓为 vendored gem5 v25.1.0.1（upstream 62c7bf2）；实施前机制核实一律以本仓源码为准（08 提取注，详见 `09-implementation-plan.md` §机制核实）。
5. **参数非 920 真值**：B0 是可复现实验模型，不是鲲鹏 920 复刻；一切数值结论的适用对象是该实验模型。
6. **结果槽全空 = 待执行**：07 展开矩阵 col16–25、col27 在源表中全空、col26 全为「待执行」；本 README 及 00–08 不含任何实测结果，所有「预期」均为待证伪假设。

## 9. 溯源与复现

- 源文件：`gem5-fi-LSU单元故障注入方案V1.0.xlsx`，sha256 `2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651`；提取日期 2026-09-24；分支 `fi-ding`。
- 机械再生成 + 自校验：`cd docs/gem5-fi/lsu && python3 extract.py` → 预期末行输出 `EXTRACTION VERIFICATION PASSED`。
- 独立校验（不 import extract.py，自己解析 xlsx 再比一遍）：`python3 verify_extraction.py` → 预期 `ALL PASSED`（CSV 逐格回比 + 集合断言 + 00/01/02/04/05/06/08/README 片段检查）。
- 计划文件：`docs/superpowers/plans/2026-09-24-lsu-north-star-extraction.md`；实施总纲：`09-implementation-plan.md`（Task 7）。
