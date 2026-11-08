# LSU v3.2.9 work order (researcher, 2026-11-08)

> Verbatim copy of the researcher's v3.2.9 work order delivered in the session.
> Baseline: LSU v3.2.8 (`d5c15309`).

## 一、任务目标

以LSU v3.2.8作为当前基线，开展本轮工作。

本轮包含三个工作流：

A. SP05正式实现及五次Pilot。

B. SQ03传播路径补充验证。

C. FW05工作负载归档及基线收尾。

其中SP05是本轮主要开发任务。

不重新设计12个故障模型，不改变60个SampleRunID及Seed，不重建公共Trace平台。

不启动60次正式实验。

---

# 二、工作流A：SP05正式实现及五次Pilot

## 2.1 当前设计

SP05已经完成故障定义冻结和规则单元测试，但尚未完成真实源码Hook和Pilot。

最终故障模型：

**Premature Store Completion**

目标源码位置：

`LSQUnit::completeStore()`

请以v3.2.8中已有的SP05源码审计报告和故障模型设计为依据。

不要重新设计故障模型，不要擅自改变已冻结的故障语义。

特别注意：

SP05与SQ03是两个不同的故障模型：

- SQ03：Premature Store Writeback Permission，涉及SQEntry::_canWB及LSQUnit::executeStore()。
- SP05：Premature Store Completion，目标位置为LSQUnit::completeStore()。

不得将两个模型的Hook、触发条件和故障语义混为一谈。

## 2.2 源码审计和Hook实现

首先检查：

1. LSQUnit::completeStore()的真实执行时机。
2. 正常情况下Store完成状态如何更新。
3. Store Writeback、Store Commit和Store Completion之间的关系。
4. 当前SP05故障设计具体提前改变哪个状态。
5. 故障是否可能导致Store提前对其他指令可见。
6. 是否影响SQ Entry生命周期和storesToWB计数。
7. 是否会造成重复完成、重复写入或状态不一致。

根据原有冻结定义实现真实Hook。

要求：

- 只对符合资格的目标Store注入。
- 每个样本最多注入一次。
- 使用独立one-shot保护。
- 记录目标DynamicInstSeqNum。
- 记录SQEntryID和Generation。
- 记录正常状态及故障后状态。
- 不影响其他Store。
- 不直接修改Store地址和数据。
- 不将Hook调用等同于故障成功。

如果发现原设计与实际gem5源码存在不一致，先提供证据和最小修正建议，不得自行扩大故障模型。

## 2.3 安全性

SP05可能涉及Store完成状态，因此必须增加安全检查：

1. max_faults必须为有限值。
2. max_faults=0不得解释为无限制注入。
3. 独立one-shot保护。
4. 防止同一Store重复注入。
5. 检查SQ计数器一致性。
6. 检查Store状态转换是否合法。
7. 增加内部Watchdog。
8. 增加外部进程Timeout。
9. HANG时保留部分Trace和日志。
10. TIMEOUT不能被判定为MASKED。

## 2.4 测试及编译

完成：

- SP05规则单元测试。
- Hook触发测试。
- 非目标Store不受影响测试。
- 重复注入防护测试。
- SQ状态和计数一致性测试。
- Watchdog测试。
- gem5完整编译。

使用独立Git分支或Worktree。

## 2.5 五次Pilot

使用原有SP05的五个SampleRunID和Seed。

不得修改样本身份。

每次Pilot记录：

- SampleRunID
- Seed
- EventOrdinal
- DynamicInstSeqNum
- Store PC
- Store Address
- Store Size
- SQEntryID
- SQGeneration
- 正常Store状态
- 故障后的Store状态
- 故障注入时间
- Store Writeback时间
- Store Commit时间
- Store Completion时间
- 后续相关Load
- Register Writeback
- Consumer Commit
- TerminalState
- Application Oracle

必须验证故障实际影响了目标Store。

如果没有下游Consumer，不得人为构造传播边。

如果最终没有影响应用层结果，记录MASKED。

如果发生Squash、Crash、HANG或SDC，按照实际证据记录。

## 2.6 SP05传播链

根据真实执行路径追踪：

Target Store
→ Store Queue
→ Store Completion Hook
→ 实际状态变化
→ 后续访存及相关指令
→ Register Writeback
→ Consumer Commit
→ Application Oracle。

注意：这是需要验证的路径，不是要求每次Pilot都必须出现全部事件。

RecordIntegrity、TraceCompleteness和PropagationCoverage必须独立判定。

---

# 三、工作流B：SQ03传播路径补充验证

## 3.1 保留原有结果

v3.2.8已经完成SQ03五次Pilot：

- R01–R05全部运行。
- 每次注入一次。
- 五次没有HANG。
- 五次Oracle PASS。
- 当前没有后续Load Consumer。

不得覆盖或删除这些历史结果。

不得为了追求SDC修改原始SQ03故障定义。

## 3.2 核查现有传播情况

重新检查五次SQ03原始Trace。

重点区分：

1. _canWB获得写回许可。
2. Store Writeback事件。
3. Store实际更新Cache/Memory的时刻。
4. Store Commit。
5. Store Completion。
6. 后续Load读取。
7. Consumer数据依赖。

不能把获得写回许可直接解释为数据已经写入Cache或Memory。

不能把Writeback事件与实际数据可见性混为一谈。

## 3.3 补充探索性工作负载

设计一个独立的SQ03传播诊断工作负载。

目标是让目标Store后续存在能够观察的Load或其他相关操作。

优先考虑：

- 相同地址的后续Load。
- 明确的数据依赖。
- 可观察的Load返回值。
- 后续Consumer使用。
- 应用层Checksum。

但必须先检查当前SQ03故障机制是否真的能够影响这些操作。

不要仅仅为了出现SDC而设计工作负载。

如果提前Writeback Permission并不会导致数据提前可见，应如实说明其微架构含义。

## 3.4 探索性实验要求

新增独立探索性运行：

`SQ03_Propagation_Probe`

使用独立SampleID，不得冒用原60个正式SampleRunID。

记录：

- 目标Store动态指令。
- SQ Entry及Generation。
- _canWB状态变化。
- Writeback事件。
- 实际Cache更新。
- Store Commit。
- 后续Load Request/Response。
- Register Writeback。
- Consumer Commit。
- Application Oracle。

至少完成一个无故障对照。

如果探索性工作负载能够形成真实传播链，再根据结果提出是否需要将其纳入正式实验。

未经研究者确认，不得修改SQ03原有正式Excel配置。

## 3.5 SQ03结论

最终区分：

- 故障是否成功注入。
- 是否提前获得Writeback Permission。
- 是否提前发生实际数据可见性。
- 是否影响后续Load。
- 是否产生Consumer传播。
- 是否产生应用层SDC。

不能因为没有SDC就判定模型无效。

---

# 四、工作流C：FW05归档及基线收尾

## 4.1 保留已有四次SDC

v3.2.8已经有：

- R01：SQUASHED
- R02：SDC
- R03：SDC
- R04：SDC
- R05：SDC

五次原始Pilot均已验证。

不得重新设计FW05，不得覆盖原始Pilot。

## 4.2 修复工作负载归档脚本

当前问题：

`FW05_Workload_Archive/run_pilot.sh`

存在仓库根目录定位错误，以及工作负载路径仍然指向原始工作区的问题。

请修复：

1. 通过GEM5_ROOT或git rev-parse定位仓库根目录。
2. 使用归档目录内的bin/fw05_forward。
3. 不依赖原始开发目录。
4. 从独立临时目录测试运行。
5. 验证归档脚本能够独立找到所有输入文件。
6. 保留原始归档和SHA256。

原始工作负载SHA256：

`0cf405092e33882750aee31fc43e96752a311ec25c4bd6762b09faff39f5b1cf`

必须继续验证R01–R05与该Hash一致。

## 4.3 无故障基线严格匹配

v3.2.8已经有五次无故障基线，但原命令使用：

`--lsq_struct_mode byte_flip --probability=0.0`

而故障实验使用：

`--lsq_struct_mode fw05_older_src --probability=1.0`

请补充严格匹配的无故障基线：

`--lsq_struct_mode fw05_older_src --probability=0.0`

要求：

- 相同工作负载。
- 相同Seed。
- 相同初始化条件。
- 相同gem5二进制。
- 相同运行参数。
- 唯一差异是故障注入关闭。

优先使用原始Pilot所用的gem5二进制。

如果使用v3.2.8最终二进制，则不能将其无故障基线单独当作旧版故障Pilot的严格配对对照。

如需证明最终二进制下的故障结果，必须使用同一最终二进制分别运行故障开启和关闭的匹配实验。

不要无意义地重跑已经通过的五次故障Pilot。

## 4.4 Excel配置

基于v3.2.3权威Excel生成新版本：

`gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx`

如果版本已占用，使用下一个未占用版本。

FW05五行统一为：

- WorkloadName：fw05_forward
- WorkloadPath：归档后的工作负载路径
- WorkloadSHA256：完整SHA256
- FaultModel：Wrong-Source Store-to-Load Forwarding

保留原SampleRunID和Seed。

保留W8 alignment历史配置及修订记录。

SQ03五行同步PilotStatus，但不要将Pilot完成误写为正式实验完成。

60行ConfigFrozen仍保持NO，等待研究者确认全局Warm-up和ROI。

---

# 五、测试和公共平台

检查v3.2.8完整测试套件。

之前存在5个pytest fixture错误，原因是缺少pytest-check依赖。

请检查项目原有依赖管理文件：

- requirements文件
- pyproject.toml
- setup.cfg
- CI配置

采用项目兼容的pytest-check版本，记录安装版本，并重新执行完整测试。

不得把缺少依赖导致的测试错误解释为代码通过。

公共Trace文件由一个统一工作流维护，避免SP05、SQ03同时修改相同文件。

不得执行git clean -fd。

不得随意git add整个工作目录。

保留所有历史交付。

---

# 六、最新状态矩阵

更新MODEL_STATUS_MATRIX.csv。

严格区分：

DESIGNED
SOURCE_AUDITED
IMPLEMENTED
COMPILED
UNIT_TESTED
PILOT_RUN
PROPAGATION_VERIFIED

具体要求：

- FW05：归档及基线收尾完成后更新。
- SQ03：保留PILOT_RUN=1，传播状态根据实际补充结果判断。
- SP05：只有五次Pilot实际完成后才标记PILOT_RUN。
- 没有Consumer的模型不得自动标记端到端传播验证通过。

---

# 七、交付要求

生成：

`LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip`

包含：

## A. SP05

1. 冻结故障定义。
2. 源码审计。
3. C++ Hook。
4. Git Diff。
5. 单元测试。
6. 编译日志。
7. 安全性与Watchdog报告。
8. 五次Pilot。
9. 五组JSONL Trace。
10. Oracle及终态分析。
11. 传播链审计。

## B. SQ03

1. 原始五次Pilot保留说明。
2. 传播路径分析。
3. SQ03_Propagation_Probe工作负载。
4. 无故障对照。
5. 探索性Trace。
6. 是否存在实际数据可见性变化的结论。
7. 是否存在Consumer传播的结论。
8. HANG风险分析。

## C. FW05

1. 完整工作负载归档。
2. 修复后的独立运行脚本。
3. SHA256清单。
4. 严格匹配的无故障基线。
5. Golden Output。
6. 更新后的Excel。
7. 原始四次SDC证据保留说明。

## D. 全局

1. 最新12模型状态矩阵。
2. 最新权威Excel。
3. 60_SAMPLE_MATRIX.csv。
4. Git Branch、完整40位HEAD、Status和Diff。
5. 最终gem5二进制SHA256。
6. 完整测试日志。
7. 文件SHA256清单。
8. 未解决问题报告。

最终分别回答：

**SP05：**
- 是否完成真实源码实现？
- 五次Pilot是否全部完成？
- 是否存在完整传播链？
- 是否出现SDC？

**SQ03：**
- 原始五次Pilot是否保留？
- 补充工作负载是否真正观察到数据传播？
- 提前Writeback Permission是否导致实际数据提前可见？
- 是否影响应用层结果？

**FW05：**
- 工作负载是否能够独立复现？
- 五次无故障基线是否严格匹配？
- 四次SDC是否有完整对应证据？
- Excel与Manifest是否一致？

本轮完成后继续LQ04。

不启动60次正式实验。
