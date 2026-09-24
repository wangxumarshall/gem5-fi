# LSU 单元故障注入方案 — 总览

> 源：工作表「0.说明与总览」（单列 24 行、21 行有文本：r1–r22、r24–r25；空行 r2/r6/r16/r23 跳过）。
> 章节 ↔ 源行：§1 ← r3–r5；§2 ← r7–r15；§3 ← r17–r22；§4 ← r24–r25；r1 为本页 H1。
> 转录规则：单元格文本逐字转录（表格内 `\n` → `<br>`、`|` → `\|`）。小节标题、列表编号、列表项末尾「（Excel rN）」行号标注与「### 源表 → 本目录文件映射」表为提取者的排版/导航结构，非源文本；提取者注一律用「> 提取注：」引用块。

## 1. 范围与基线

### 范围

范围：AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器。

### 统一基线

统一基线：LSU单元参数总表.md 的 B0。除 DTLB=32 项是为复现 TC'23 的显式覆盖外，其余优先采用 gem5 stable 的 O3_ARM_v7a_3 / BaseO3CPU / ArmMMU 配置。

> 提取注：该文档不在本仓库；B0 定值以内嵌的表2（02-parameter-baseline.md）为准。

### 重要纠正

重要纠正：B0 是可复现实验模型，不是鲲鹏 920 复刻；cache ports=200 不是物理端口数；当前 ARM 示例为 1 Load FU + 1 Store FU，L1D=32KiB/2-way，StridePrefetcher 位于 L2。

## 2. 工作簿结构

- 1.单元与现有研究：逐单元填写“现有文章”和“现有文章结果”，并严格区分 AVF、非Benign条件占比、检测率和DelayAVF。（Excel r8）
- 2.LSU参数基线：参数合理性审查、B0定值与单因素敏感性配置。（Excel r9）
- 3.位置x模型矩阵：每行一个单元×位置×故障模型，含频率、负载、传播监控、预期结果和设计理由。（Excel r10）
- 4.观测点定义：L0-L5传播链；SDC率分母只用activated，不用attempted。（Excel r11）
- 5.频率与统计：事件归一化频率、周期换算、随机化与样本量。（Excel r12）
- 6.负载清单：论文复现、公开通用和定向探针负载。（Excel r13）
- 7.展开执行矩阵：按位置×模型×频率×负载展开；黄色列是执行后人工录入，蓝色列自动计算。（Excel r14）
- 8.文献与来源：本地论文和官方源码定位。（Excel r15）

### 源表 → 本目录文件映射

| 源表 | 本目录文件 |
|---|---|
| 表0（0.说明与总览） | 00-overview.md（本文档） |
| 表1（1.单元与现有研究） | 01-units-and-research.md |
| 表2（2.LSU参数基线） | 02-parameter-baseline.md |
| 表3（3.位置x模型矩阵） | 03-design-matrix.md + design-matrix.csv |
| 表4（4.观测点定义） | 04-observation-points.md |
| 表5（5.频率与统计） | 05-frequency-and-sampling.md |
| 表6（6.负载清单） | 06-workloads.md |
| 表7（7.展开执行矩阵） | 07-expanded-matrix.csv + 07-expanded-matrix.md |
| 表8（8.文献与来源） | 08-references.md |

## 3. 统计与判定边界（五条原文）

1. ① attempted、eligible、activated分开记录。目标未被后续读取/使用的注入归入Injected-not-activated，不进入SDC率分母。
2. ② F0单次故障用于AVF/论文对照；F1-F4是重复/突发故障压力实验，不能与F0混成一个“故障率”。F5永久故障按运行分类。
3. ③ 每个实验单元先做30个activated样本试跑；正式筛查至少385个activated样本（95%置信水平、最坏比例下约±5个百分点）。论文主结果建议用Wilson 95%区间半宽≤2个百分点或达到5000个activated样本停止。
4. ④ 每个故障运行绑定同一checkpoint、输入、seed和无故障golden run；结构化换值只允许替换成明确合法值，并保存源值/目标值。
5. ⑤ 预期结果是可证伪假设，不是实测结论。没有论文直接结果的AGU、原子/同步和多数结构化模型，实测列必须保持待执行。

## 4. 完善版增量（原文）

补充PPN与SQ基础对照、Load Queue、MSHR资源记账、原子操作数、预取触发脏驱逐、真实应用负载，以及F1-F4按运行聚类的统计规则；原58条模型扩展为68条。
