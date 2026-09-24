# LSU 单元故障注入方案 V1.0 → 项目北极星提取 · 设计文档

> **日期** 2026-09-24 · **分支** `fi-ding` · **状态** 设计已获用户批准（brainstorming 8 节呈现 + 两项范围裁定）
> **源文件** `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案V1.0.xlsx`，sha256 `2703f81240db0cc71c5fe109a6ff693617907a19c66885019ffe0da350713651`
> **先例** `docs/gem5-fi/ooo/`（OoO 北极星，2026-09-22）。本设计 = 先例的**镜像适配**：方法论、工具骨架、校验思路照搬；文档编号映射、断言体系、实施总纲内容按 LSU 源表结构重写。
> **裁决规则**：本 spec 与提取产物 00–08 忠实层冲突时，**以 00–08 为准**（同 ooo 06 的规则）。

---

## 1. 目标与范围

**目标**：把《LSU 单元故障注入方案 V1.0.xlsx》（9 工作表）完整忠实提取为 `docs/gem5-fi/lsu/` 下的**项目北极星**——面向 ARM LSU 微架构单元（AGU / L1d-TLB / Load Queue / Store Queue / L1d-Cache / 原子与同步 / 数据预取器，共 7 单元）故障注入**实现**的导航与设计数据总库。

**范围裁定**（用户 2026-09-24）：
1. **交付范围 = 完整北极星**：忠实提取层（编号文档 + 机读 CSV + extract.py + verify_extraction.py + README）**加** 09 式实施总纲（机制核实计划 + WBS）；
2. **组织方案 = 方案一（镜像适配）**：文档编号 1:1 对应源表号 0–8；extract.py 从 ooo 版改造（解析器复用、断言重写）。

**明确不做**（本轮）：
- 不改任何 C++/Python 工具代码，不跑任何仿真（这些是 09 之后的工作包）；
- 不做结果回填——展开矩阵 11 个结果槽列原样保留为空；
- 09 实施总纲写到 WBS/机制核实计划层面即可，其执行不属本轮。

## 2. 源表结构（2026-09-24 探索实证）

9 个工作表全部可见（无隐藏表、无 inlineStr 单元格），表序即逻辑序：

| 表号 | 工作表名 | 非空行×列（含表头） | 内容 |
|---|---|---|---|
| 0 | `0.说明与总览` | 24×1 | 范围=7 单元；B0 基线声明；5 条统计判定边界；完善版增量自述 |
| 1 | `1.单元与现有研究` | 8×7 | 逐单元文献/结果/指标口径/证据直接性/研究空白（7 数据行） |
| 2 | `2.LSU参数基线` | 20×5 | 19 参数 B0 定值/处理/依据/敏感性配置（S1–S5） |
| 3 | `3.位置x模型矩阵` | 69×12 | 设计主体：**68 数据行**，每行一个「单元×注入位置×故障模型」 |
| 4 | `4.观测点定义` | 7×6 | L0–L5 六层观测（6 数据行） |
| 5 | `5.频率与统计` | 18×6 | F0–F6 七档（r2–r8）+ 统计规则块（r11 子表头 + r12–r20） |
| 6 | `6.负载清单` | 15×6 | W0–W13（14 数据行） |
| 7 | `7.展开执行矩阵` | 338×27 | RunID 执行清单，**337 数据行**，11 结果槽全空 |
| 8 | `8.文献与来源` | 12×6 | 4 条 gem5 官方源码（2026-09-24 核对，**上游 stable**）+ 7 篇本地 PDF |

**关键事实**（实现时直接引用，不再重新发现）：

- **稳定 ID 源表自带**：模型ID 前缀=单元（A=AGU 8 行、T=L1d-TLB 10、S=Store Queue 13、C=L1d-Cache 15、O=原子与同步 9、P=数据预取器 9、L=Load Queue 4，合计 68）；RunID = `{模型ID}-{F档}-{W负载}`（如 `A01-F0-W3`）。**沿用源表 ID，不发明新编号**（与 ooo 的 D01/E001 体系的关键差异）。
- **完善版结构**：原始 58 行 = Excel r2–r59（按单元分组：A→T→S→C→O→P）；完善版追加 10 行 = r60–r69（`T10, S13, L01–L04, C14, C15, O09, P09`）。**Load Queue 的全部 4 行都在追加区**——原 58 行没有 LQ 模型。
- **展开矩阵 337 行**：频率分布 F0=109/F1=24/F2=77/F3=4/F4=26/F5=29/F6=68；单元分布 AGU=39/TLB=42/SQ=66/Cache=76/原子=31/预取=53/LQ=30；负载分布 W0–W13 全部用到（W5=57、W6=58 最多，W0/W2/W13=6 最少）。RunID 与 模型ID/频率列 **0 不一致**（探索期已预验证）。
- **结果槽**：col16–col25、col27 全空（337/337），col26 `记录状态`=`待执行`（337/337）。11 列 = `Seed/注入索引, Attempted, Activated, Masked, Detected/Contained, SDC, Crash, Timeout, SDC率(activated), 激活率, 实测备注`。
- **27 列构成**：col1–15 为源数据列（RunID/模型ID/单元/注入位置/故障类型/故障模型/频率/频率定义/负载/负载定义/oracle/触发条件/传播监控/预期结果/设计理由/文献依据），col16–27 为**结果区（12 列）**= 11 个空填写槽 + col26 `记录状态` 预填 `待执行`。
- **故障类型含复合标注**（`换值/时序`、`卡死/保护`、`状态/换值`、`时序/状态`）——提取时保持原文，**不拆分**。
- **新故障类型族**：`保护`（T09/S12/C13/O08）、`错位拼接`、`时序`——ooo 体系没有的族。
- **L0–L5 六层**（ooo 为 L0–L4）：L5 最终结局含 `Injected-not-activated` 与 `Detected-contained` 类；守恒式 `Activated = Masked + Detected + SDC + Crash + Timeout`。
- **F0–F6 七档**（ooo 为 F0–F5）：F4=短突发（连续污染 2–4 个 eligible events）、F6=确定性事件触发（首次出现指定事件时注入一次）。
- **自适应样本量**（ooo 为固定 n=2000）：试跑 30 activated → 筛查 ≥385 activated（95% 置信、±5pp）→ 主结果顺序加样至 Wilson 95% 区间半宽 ≤2pp 或 activated 达 5000。
- **FS/多核结构性依赖**：W4(TLB-AliasPerm)=FS、W7(Atomic-Litmus)=多核 FS、W13(PARSEC)=多核 FS、W1(MiBench)=FS 优先、W6(Cache-DirtyEvict)=SE+多核 FS 子集。原子与同步单元必须多核 FS。
- **《LSU单元参数总表.md》不在仓库**（find 已证）——总览 r4 引用它作为 B0 统一基线；好在 B0 定值已内嵌 Sheet2，以 Sheet2 为准并在 README 声明。
- **xlsx 文献核对基于上游 gem5 stable**（Sheet8，核对日期 2026-09-24）；本仓 vendored **v25.1.0.1**（upstream 62c7bf2，见 `CHAOS/gem5_base_version.md`）。09 的机制核实**一律对本仓源码**，README 注明两者可能存在差异。
- **解析器差异（必须修）**：LSU xlsx 的 workbook rels Target 带 leading slash（`/xl/worksheets/sheet1.xml`）。ooo 版 extract.py 的 `t if t.startswith('xl/') else 'xl/'+t` 会拼出 `xl/xl/...`。**必须改为先 `.lstrip('/')` 再判断**（探索期实际踩到并验证）。

## 3. 交付物与目录结构（最终形态）

```
docs/gem5-fi/lsu/
├── README.md                      # 总纲导航（含基础设施映射 + 诚实声明）          [手写]
├── 00-overview.md                 # ← 表0 说明与总览                              [手写]
├── 01-units-and-research.md       # ← 表1 单元与现有研究                          [手写]
├── 02-parameter-baseline.md       # ← 表2 LSU参数基线                             [手写]
├── 03-design-matrix.md            # ← 表3 位置x模型矩阵（68 行全列）              [extract.py 生成]
├── design-matrix.csv              #   同上机读版                                 [extract.py 生成]
├── 04-observation-points.md       # ← 表4 观测点定义                              [手写]
├── 05-frequency-and-sampling.md   # ← 表5 频率与统计                              [手写]
├── 06-workloads.md                # ← 表6 负载清单                                [手写]
├── 07-expanded-matrix.csv         # ← 表7 展开执行矩阵（337 行×27 列）            [extract.py 生成]
├── 07-expanded-matrix.md          #   列文档 + 分布汇总 + 颜色语义                [extract.py 生成]
├── 08-references.md               # ← 表8 文献与来源                              [手写]
├── 09-implementation-plan.md      # 实施层（非源表提取）                          [手写]
├── extract.py                     # 忠实层生成器 + 内置交叉校验
├── verify_extraction.py           # 独立全量回比校验器
└── gem5-fi-LSU单元故障注入方案V1.0.xlsx   # 源文件入库（sha256 见文首）
```

**引用纪律**：后续注入器实现、campaign、结果回填统一用模型ID / RunID。

## 4. 忠实层规格

1. **全列保真**：12 列设计矩阵、27 列展开矩阵的长文本列（故障模型/预期结果/设计理由/文献依据等）在人读文档中**全量呈现，不截断**（03 的 markdown 预计 ~100KB 量级，同 ooo 04）。
2. **03-design-matrix.md**：按 7 单元分节（AGU→L1d-TLB→Store Queue→L1d-Cache→原子与同步→数据预取器→Load Queue），每行附 Excel 行号；完善版追加的 10 行标注「**完善版新增**」。
3. **00-overview.md**：单列长文本按原文分段全量呈现；工作簿结构说明改为指向本目录实际文件（原文引用 Sheet 名保留，附「→ 本目录文件」映射表）。
4. **颜色语义**（总览 r14：「黄色列是执行后人工录入，蓝色列自动计算」）：从 xlsx styles.xml 提取展开矩阵各列实际填充色，在 07-expanded-matrix.md 按列文档化（黄=人工录入槽、蓝=自动计算列）；断言黄/蓝列均落在 col16–27 结果槽范围内。CSV 无法携带颜色，语义只记在 md。
5. **结果槽**：11 列原样保留为空（`记录状态`=`待执行`），是实施时填写槽——同 ooo 对 Sheet5 空结果列的处理。
6. **手写文档不编造**：00/01/02/04/05/06/08/README 的全部事实性内容来自源表对应单元格原文；提取者自己的判断只出现在明确标注「提取者注」或 README 的固定小节（如基础设施映射）里。

## 5. extract.py 设计

**解析器**：复用 ooo 版（纯标准库 `zipfile` + `xml.etree` + sharedStrings 解析；本机已实证可解析 LSU xlsx），修改点：
- rel-target 归一化：`.lstrip('/')` 后再判断是否补 `xl/` 前缀（见 §2 关键事实末条）；
- 列定义常量按 LSU 两张矩阵重写（12 列 / 27 列）。

**生成物**（4 个）：`03-design-matrix.md`、`design-matrix.csv`、`07-expanded-matrix.csv`、`07-expanded-matrix.md`。

**内置交叉校验**（断言，任一失败即非零退出，末行打印 `EXTRACTION VERIFICATION PASSED`）：
1. **展开重放**：从设计矩阵的「适用频率 × 适用负载」自行重放展开 → 与表 7 的 337 行逐行比对 col1–15 全等（col16–27 是结果槽，不在重放范围；col8 频率定义来自表5、col9/10 负载来自表6 的映射规则在实现时固化）；
2. 行数断言 68 / 337；
3. 结果槽断言：col16–25、col27 全空，col26 全为 `待执行`；
4. RunID 自洽断言：`RunID == 模型ID-频率-W编号`，且 W编号 ↔ 表6 负载名称映射一致（探索期预验证 0 异常，进正式断言防回归）；
5. 唯一性断言：模型ID 唯一；(单元, 注入位置, 故障类型) 组合唯一；
6. 颜色语义：从 styles.xml 提取展开矩阵各列的黄/蓝填充集合写入 07-md；预期黄/蓝列 ⊆ 结果区 col16–27——**若实测超出（属源表自身不一致），如实记录差异并写入 README 诚实声明，不算提取失败；但不允许省略颜色提取**。

**核心风险点（诚实标注）**：展开规则（每模型的频率×负载如何配对出平均 ~5 格/模型）需实现时从 337 行**反推并固化**。初步证据指向「适用频率 × 适用负载全叉积」（A01: F0/F1/F2 × {W3, W9} = 6 格）。断言 1 即此规则的兜底——若反推出的规则无法重放出 337 行全等，就是规则找错了，禁止放宽断言迁就。

## 6. verify_extraction.py 设计

与 ooo 版同思路、**独立实现路径**（不 import extract.py）：
1. 直接从 xlsx 重新解析，**逐格**比对两份 CSV 的每个单元格（68×13 与 337×28，含 Excel 行号列）；
2. 人读文档（00/01/02/04/05/06/08/README）的关键原文片段做空白归一化匹配（ooo 为 55 个片段；LSU 按内容定，预计 50–80 个，覆盖每表的关键定义句、五条统计边界、B0 关键参数、验证锚点）；
3. 断言 68/337、模型ID 与 RunID 集合、完善版追加 10 行的 ID 清单；
4. 全部通过输出 `ALL PASSED`，任一失败非零退出并打印差异明细。

## 7. README 总纲规格

仿 ooo README 结构，LSU 化：
1. **北极星目标**：LSU 版三问（哪些位置有真实 SDC 潜力 / SDC 前微架构层可观测前兆 / 结构化模型相对随机翻转的增量——预期结果列全部是「待验证假设」）；
2. **文档地图**：表→文件→规模；
3. **数字总账**：68 模型（7 单元分布）、337 格（频率×单元×负载分布）、自适应样本量口径（30/385/Wilson≤2pp 或 5000）、总算力规模估算；
4. **设计边界**（源表原文）：B0 是可复现实验模型**不是鲲鹏 920 复刻**；AVF/条件占比/总 AVF/检出率/DelayAVF **严禁混算**；SDC 率分母 = activated；F0 与 F1–F4 不能混成一个「故障率」；
5. **方法核心主张**（综合自设计理由列，注明出处）；
6. **实施顺序**：源表自带验证锚点优先——LQ/SQ 单 bit 复现 TC'23 的 SDC=0%（注入器正确性自检）、T01 DTLB 单 bit 对照 TC'22 Crash AVF≈50%、完善版新增 LQ 行是文献增量所在；
7. **基础设施映射**（逐项真实 grep 核实，不做空头声明）：复用候选 `lsq_fwd`/`l1d_fwd`/`l1d`/`l1_tlb`/`addr_path`/campaign/classify/manifest/`configs/se/ooo_proxy.py`；新建清单（AGU、原子与同步、预取器、LQ 生命周期、F4 突发/F6 确定性触发、自适应样本量两阶段编排、多核 FS）；
8. **诚实声明**：《LSU单元参数总表.md》不在仓库（B0 以内嵌 Sheet2 为准）；TLB 注入器 SE-inert（FS-only）；W4/W7/W13 的 FS/多核依赖是结构性缺口；xlsx 文献核对基于上游 stable 而本仓 vendored v25.1.0.1；参数非 920 真值；
9. **溯源与复现**：源文件 sha256 + `python3 extract.py` / `python3 verify_extraction.py` 重跑命令 + 提取过程记录指针（plans 目录）。

## 8. 09-implementation-plan.md 规格（实施层）

仿 ooo 06 结构：
1. **目标与成功判据**：337 格 × 11 结果列回填；L0–L5 观测数据；自检锚点记录；元分析报告；
2. **机制核实 N 表**（对本仓 vendored **v25.1.0.1**，源码级；每项「xlsx 表述 vs v25.1 实际 vs 对模型行的影响」），**初步核实对象清单（编写 09 时可扩展）**：
   - LQ/SQ 在 `src/cpu/o3/lsq.hh/.cc` 的实际结构（表项字段、head/tail、violation/replay 路径）与 16/16 项配置；
   - SSIT/LFST（store set）实现落点与 1024/1024 配置路径；
   - DTLB=32 项全相联的配置路径（gem5 默认 64）；
   - L1D 32KiB/2-way、MSHR 6/targets 8、write buffer 16 的配置来源；
   - L2 StridePrefetcher 挂接（B0 预取器在 **L2** 而非 L1D）；
   - exclusive monitor / 原子 RMW 的多核语义（SE 单核平台的差距）；
   - AGU 有效地址生成的截获点与现有 `CHAOSAddrPath` 的关系；
   - F4 短突发 / F6 确定性事件触发 vs 现有 `chaos_trigger` F0–F5 语义的差距；
   - MSHR merge、fill/writeback、dirty eviction 路径（C 系模型行落点）；
3. **WBS W0–Wn**（初步骨架：W0 平台/B0 参数落地 → W1 机制核实 → W2 触发语义 F0–F6 → W3 观测层 L0–L5 → W4+ 按单元注入器 → 收尾 元分析；编写时定稿，每个 W = 一个 patch 单元）；
4. **里程碑 M0–Mn**；
5. **算力预算**（337 格 × 自适应样本量的规模估算，含 4 并发 gem5 进程上限纪律）；
6. **裁决规则**：与 00–08 冲突时以 00–08 为准。

## 9. 验收标准（全部真实执行后才算完成）

1. `cd docs/gem5-fi/lsu && python3 extract.py` → 末行 `EXTRACTION VERIFICATION PASSED`；
2. `cd docs/gem5-fi/lsu && python3 verify_extraction.py` → `ALL PASSED`；
3. **人工抽查**：随机 ≥10 格（设计矩阵 + 展开矩阵各若干）逐格人眼比对 xlsx 原文，防「校验器自己错自己」（ooo 经验：校验器抓出过 2 处真实提取偏差，人工抽查是第三道独立防线）；
4. 每个 commit 遵守 CLAUDE.md 自验证纪律：本工作为纯文档/脚本，构建检查 = `python3 -m py_compile extract.py verify_extraction.py` 零输出；功能验证 = 上述 1/2/3；回归 = **不适用**（不改任何在产代码，明确声明而非假装跑过）。

## 10. 提交切分（one-patch-per-unit，初步 7 个 commit，writing-plans 阶段定稿）

| # | commit | 内容 |
|---|---|---|
| ① | `docs(lsu): track source xlsx V1.0` | 源 xlsx 入库（sha256 记录于 README/spec） |
| ② | `docs(lsu): extract.py + machine-readable matrices` | extract.py + 03-design-matrix.md + design-matrix.csv + 07-expanded-matrix.csv/.md（断言全过） |
| ③ | `docs(lsu): faithful docs 00/01/02` | 总览、单元与现有研究、参数基线 |
| ④ | `docs(lsu): faithful docs 04/05/06/08` | 观测点、频率统计、负载、文献 |
| ⑤ | `docs(lsu): verify_extraction.py` | 独立校验器（ALL PASSED） |
| ⑥ | `docs(lsu): README north-star navigation` | 总纲 + 基础设施映射（grep 核实）+ 诚实声明 |
| ⑦ | `docs(lsu): 09 implementation master plan` | 机制核实 + WBS + 里程碑 + 算力预算 |

全部在 `fi-ding` 分支，**显式路径 staging（绝不 `git add -A`）**，每 commit 后按 CLAUDE.md 自动 push。

## 11. 诚实约束（贯穿全部产物）

- B0 是可复现实验模型，**不是鲲鹏 920 复刻**（总览 r5 原文）；cache ports=200 不是物理端口数；
- 指标口径（AVF / 非Benign条件占比 / 检出率 / DelayAVF）**严禁混算**（表1 原文）；
- SDC 率分母 = activated；attempted/eligible/activated 分开记录（表4/表5 原文）；
- 预期结果是**可证伪假设，不是实测结论**；无论文直接结果的 AGU、原子/同步和多数结构化模型，实测列必须保持待执行（总览 r22 原文⑤）；
- F0 单故障 AVF 与 F1–F4 压力实验不得混成一个「故障率」；F5 按运行分类（总览 r19 原文②）；
- 《LSU单元参数总表.md》不在仓库——README 声明，B0 以内嵌 Sheet2 为准；
- xlsx 文献核对基于上游 stable；本仓机制核实一律对 vendored v25.1.0.1；
- TLB 注入器 SE-inert（CLAUDE.md）——TLB 单元与 FS 依赖负载的映射如实标注；
- 09 与 00–08 冲突时以 00–08 为准。
