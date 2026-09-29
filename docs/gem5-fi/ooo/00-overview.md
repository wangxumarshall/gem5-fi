# 00 · 总览（V2.0：范围 / 基线 / 工作簿结构 / 统计与判定边界）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

## R1 · 标题

OOO 单元故障注入方案 - 总览

## R3–R6 · 范围与基线

- **R3** 范围：Int Decode、Int Rename、Int Dispatch/ROB、FP/SIMD Decode、FP/SIMD Rename、FP/SIMD Dispatch/ROB。
- **R4** 统一基线：gem5 stable O3_ARM_v7a_3。主基线是可复现实验模型，不是鲲鹏 920、Neoverse 或其他商业核的复刻。
- **R5** 关键参数：fetch/decode/rename=3，dispatch=6，issue/writeback/commit=8，ROB=40，IQ=32，Int PRF=128，Float PRF=192，Vec PRF=48，单线程。
- **R6** 保护机制核验：六个 OOO 单元均无 gem5 stable 或 ARM 通用架构定义的 ECC/parity/端到端硬件校验保护；不加入这类未来对照模型。实际纳入的完整性路径只有 ARM 译码合法性/Undefined Instruction 异常，以及 ROB 按序提交、精确异常、squash/回滚和 FP 异常提交门控；它们由现有 D/FD/B/FB 模型覆盖。影子状态、golden trace、软件 checksum/assert、gem5 assert/panic 均为观测或仿真器故障，不是 Hardware RAS。

## R8–R16 · 工作簿结构

（R8 为原表节标题：「工作簿结构」）

- **R9** 1.单元与现有研究：填入论文已经覆盖的结构、模型、负载和结果，并区分直接证据、机制类比与研究空白。
- **R10** 2.OOO参数基线：给出 gem5 可直接设置的 B0 参数，以及不改变主结论口径的单因素敏感性配置。
- **R11** 3.位置x模型矩阵：每行一个单元×注入位置×故障模型，并新增故障表现形式/子模型字段，明确频率、负载、触发、传播监控、预期结果和设计理由。
- **R12** 4.观测点定义：L0-L5 传播链。SDC 率分母使用可分析 activated，不使用 attempted。
- **R13** 5.频率与统计：按 eligible event 归一化，F0 单次、F1-F3 重复、F4 突发、F5 永久、F6 确定性事件。
- **R14** 6.负载清单：论文复现、公开通用、真实应用和针对 OOO 机制的自设探针。
- **R15** 7.展开执行矩阵：模型×故障表现形式/子模型×频率×负载全展开。黄色列执行后人工录入，蓝色列自动计算。

  〔提取注：R15 声称展开维度为「模型×故障表现形式/子模型×频率×负载全展开」，但工作表「7.展开执行矩阵」实际只展开到 模型×频率×负载 = 310 格（子模型以整格文本附在 AQ 列）。若真按子模型展开应为 1050 格（派生计算 Σ(子模型数×格数)）。计划裁决 D4：执行 310 格、格内按子模型分层记录。详见 `README.md` 诚实性注记 (a)。〕
- **R16** 8.文献与来源：本地论文与 gem5 官方源码。

## R18–R25 · 统计与判定边界

（R18 为原表节标题：「统计与判定边界」）

- **R19** 1) attempted、eligible、activated 分开记录。目标字段未被读取、选择或用于状态转移时记 Injected-not-activated，不进入结果率分母。
- **R20** 2) F0/F6 是单故障实验；F1-F4 是同一运行内多事件压力实验；F5 是永久故障。三类结果分别报告，不合并为一个故障率。
- **R21** 3) 每个模型×频率×负载先取得 30 个 activated 试跑；筛查至少 385 个；主结果使用 Wilson 95% 区间半宽<=2 个百分点或 5000 个 activated 停止。
- **R22** 4) 合法换值必须从当前有效候选集合选择，保存 source/target；不能把随机非法位串称为换值。
- **R23** 5) 首检层级与最终结局独立记录：首检四类且互斥（Hardware RAS / OS / Application / None）；Hardware RAS检测（任意时点）只在实际收到硬件错误报告时记 1，不按注入位置推定。最终结局分 Masked、Detected-contained、Data Corruption、Crash、Timeout，另列 Simulator failure。golden output 对比只作为离线 oracle，不算运行时检测。
- **R24** 6) 最终结局分为 Masked、Detected-contained、Data Corruption、Crash、Timeout；SDC = 运行时三层均未检测且正常完成，但离线 oracle 发现 Data Corruption。Simulator failure 单列。
- **R25** 7) 对共享 ROB，Int 与 FP/SIMD 行使用相同物理 ROB，但通过动态指令类型过滤形成互斥 campaign，不能把同一注入重复计入两组。

