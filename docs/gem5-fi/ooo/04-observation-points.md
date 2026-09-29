# 04 · 观测点定义（L0–L5 传播链）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「4.观测点定义」R2–R7（表头 R1），6 列 × 6 层级。

| 层级 | 名称 | 定义 | 必须采集量 | 适用范围 | 判定规则 |
|---|---|---|---|---|---|
| L0 | 注入与激活 | 记录attempt、eligible、目标动态指令/entry/bit、注入时结构状态，以及故障字段是否被后续读取、选择或用于状态转移。 | attempted、eligible、activated、目标寿命、动态指令ID、ROB序号、commit序号、source/target | 全部 | 未activated不进入SDC率分母；合法换值必须保存候选集 |
| L1 | 单元内部状态 | 与同checkpoint的无故障影子状态逐事件比较：decode tuple；RAT/free-list/ready/checkpoint；ROB entry/head/tail/state。 | 首个局部偏差周期；字段diff；映射唯一性；free+allocated守恒；ROB occupancy守恒；valid/complete合法转移 | 全部，按单元定制 | 局部偏差不等于架构错误；保留首次差异和是否恢复 |
| L2 | 跨单元依赖与分派 | 观察decode→rename→dispatch/IQ的src/dst tag、依赖边、FU/opClass steering、ready/issue/replay。 | arch/phys tag、producer-consumer边、IQ slot、FU实例、issue cycle、stall/replay、重复/漏发 | Rename、Dispatch重点 | 与golden逐动态指令匹配；区分值正确但时序不同 |
| L3 | 执行与写回传播 | 观察FU输入/输出、完成事件、writeback tag、lane mask、PRF写入和FPSR/exception。 | FU/opClass、输入/结果、完成周期、ROB index、物理tag、lane diff、异常标志、错误值扇出 | Dispatch/ROB与FP/SIMD重点 | 记录首次错误执行、错误完成配对及是否被后续覆盖 |
| L4 | 架构可见与提交 | commit处逐条比较PC、opcode、架构src/dst、寄存器值、FPSR和内存副作用，检查按序和精确异常。 | 首个分歧commit序号、错误寄存器/lane、异常、错误路径提交、漏/重复提交、错误store | 全部 | commit trace与golden对齐；时序差异单列，不自动算数据错误 |
| L5 | 检测与最终结局 | 首个运行时检测层级分Hardware RAS、OS、Application、None；最终结局分Masked、Detected-contained、Data Corruption、Crash、Timeout。离线oracle不算运行时检测。 | 首检层级、任意时点Hardware RAS、OS/应用证据、contained、输出diff、超时原因、Simulator failure | 全部 | SDC=None且Data Corruption；五类结局+Simulator failure=Activated；首检四类=可分析Activated |

