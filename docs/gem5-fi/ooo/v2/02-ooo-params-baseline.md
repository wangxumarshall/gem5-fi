# 02 · OOO 参数基线（B0 + S0–S6 敏感性 + 逐单元保护机制核验）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract_v2.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「2.OOO参数基线」：R1 表头；R2–R24 B0 参数与敏感性配置（23 行）；R25 节标题（B–E 列空）；R26–R31 逐单元保护机制核验（6 行）。

## B0 参数与敏感性配置（R2–R24）

| 结构/参数 | B0最终值 | 处理 | 依据/合理性判断 | 敏感性配置 |
|---|---|---|---|---|
| CPU模型 | gem5 stable O3_ARM_v7a_3 / ArmO3CPU | 主基线 | 官方 Arm O3 示例，可直接复现；不是商业核复刻 | S0=BaseO3CPU 默认宽核，仅做敏感性 |
| 线程 | 1 | 保留 | 避免 SMT 共享策略把结构容量和故障传播混在一起 | 不在主 campaign 开 SMT |
| fetchWidth / fetchBufferSize | 3 / 16B | 保留 | O3_ARM_v7a_3 明确覆盖 | B0 |
| decodeWidth / fetchToDecodeDelay | 3 / 3 cycles | 保留 | O3_ARM_v7a_3 明确覆盖 | S1=4-wide decode，其他参数不变 |
| decodeToRenameDelay / renameWidth | 2 cycles / 3 | 保留 | O3_ARM_v7a_3 明确覆盖 | S1=4-wide rename |
| renameToIEWDelay / renameToROBDelay | 1 / 1 cycle | 保留 | O3_ARM_v7a_3 明确覆盖 | B0 |
| dispatchWidth | 6 | 保留 | O3_ARM_v7a_3 明确覆盖 | S2=8 |
| issueWidth / wbWidth / commitWidth | 8 / 8 / 8 | 保留 | O3_ARM_v7a_3 明确覆盖 | B0 |
| squashWidth | 8 | 保留 | O3_ARM_v7a_3 明确覆盖 | S3=无限制即时 squash（Base 默认未指定） |
| IQ entries | 32 | 保留 | O3_ARM_v7a_IQ.numEntries | S4=64 |
| ROB entries / ROBs | 40 / 1 | 保留 | O3_ARM_v7a_3 覆盖 numROBEntries；BaseO3CPU numRobs=1 | S4=128；S5=192 |
| Int physical registers | 128 | 保留 | O3_ARM_v7a_3 明确覆盖 | S4=192；S5=256 |
| Float physical registers | 192 | 保留 | O3_ARM_v7a_3 明确覆盖 | S4=256 |
| Vector physical registers | 48 | 保留 | O3_ARM_v7a_3 明确覆盖 | S4=64；不把它解释为商业核 PRF 容量 |
| Vector predicate registers | 32 | 继承默认但主负载不用 | BaseO3CPU 默认；B0 聚焦 AArch64 FP/AdvSIMD，不宣称 SVE 微架构复刻 | 仅在显式 SVE 扩展 campaign 中启用 |
| 整数 FU | 2×IntAlu(opLat=1) + 1×IntMult/IntDiv/System | 保留 | O3_ARM_v7a 官方 FU pool | 不在 OOO 主实验改变 |
| FP/SIMD FU | 2 个；按 opClass 使用 3-33 cycle 延迟 | 保留 | O3_ARM_v7a_FP 官方定义 | S6=1 个 FP/SIMD FU，研究资源竞争 |
| trapLatency | 13 cycles | 保留 | O3_ARM_v7a_3 与 BaseO3CPU 一致 | B0 |
| backComSize / forwardComSize | 5 / 5 | 保留 | O3_ARM_v7a_3 明确覆盖 | B0 |
| ISA/向量范围 | AArch64 + scalar FP + AdvSIMD/NEON 128-bit | 限定 | 与 Arm O3 示例可执行能力和公开负载相容；不把 N2/N3 的 SVE2 特性硬套到 B0 | SVE 单独扩展，不与 B0 合并 |
| OOO结构保护 | 无 ECC/parity | 按要求不实现 | 官方 gem5 参数与核对论文没有明确配置这些保护；影子 trace 只作 oracle | 不建立“有保护”主组 |
| 时钟 | 2.6GHz 仅用于辅助换算 | 沿用 LSU 口径 | 注入频率以 eligible event 为主，避免 IPC 和宽度差异造成偏置 | 1ms=2,600,000 cycles |
| 检查点与运行模式 | SE 主跑；FS 复现 TC'23/OS 传播 | 新增 | OOO 内部定位用 SE 成本低；异常、内核和完整传播必须用 FS 复核 | 每个主结论至少一个 FS 负载 |

## 逐单元保护机制核验（R25–R31）

R25（A 列）为原表节标题：**逐单元保护机制核验（只列实际存在且纳入实现的机制）**（该行 B–E 列为空）。

〔提取注〕R26–R31 沿用上表 5 列版式，该节列语义为：A=单元、B=实际存在的完整性/保护机制、C=处理、D=纳入实现的模型与观测、E=非 Hardware RAS 说明（下表表头为提取层标签）。

| 单元 | 机制（B 列原文） | 处理 | 覆盖模型与观测 | 非 RAS 说明 |
|---|---|---|---|---|
| Int Decode | 有：AArch64 非法/未定义编码的合法性判定与 Undefined Instruction 异常路径 | 实现 | D01/D02 的原始指令扰动 + L5 OS首检/最终结局；合法换值仍按 Application/None 统计 | 不是ECC/parity；不是Hardware RAS |
| FP/SIMD Decode | 有：FP/SIMD 指令合法性与异常属性元数据进入精确异常/FP状态路径 | 实现 | FD01/FD02/FD05/FD06/FD08/FD09，观察异常提交与OS/Application首检 | 不是ECC/parity；FPSR/FPCR是架构状态，不是RAS |
| Int Rename | 无 ARM 架构可见的重命名校验保护；gem5 stable无该单元ECC/parity配置 | 不实现保护对照 | 仅注入RAT/free-list/ready/checkpoint本身（R01-R09）并记录局部不变量偏差 | 影子RAT/free+allocated守恒是观测器 |
| Int Dispatch / ROB | 有功能性完整性约束：按序提交、精确异常、squash/回滚和生命周期门控；无ECC/parity | 实现 | B04/B05/B08/B09覆盖状态与事务故障；gem5依赖检查/断言只记Simulator failure | 不能记Hardware RAS |
| FP/SIMD Rename | 无 ARM 架构可见的重命名校验保护；gem5 stable无该单元ECC/parity配置 | 不实现保护对照 | 仅注入FP/Vec RAT/free-list/ready/checkpoint/partial-write（FR01-FR10） | 影子状态只用于传播观测 |
| FP/SIMD Dispatch / ROB | 有功能性完整性约束：FP异常/完成门控、按序提交、squash/回滚；无ECC/parity | 实现 | FB04/FB05/FB08/FB09覆盖；FPSR/异常标志仅在实际产生时记录 | 不能按位置推定Hardware RAS |

