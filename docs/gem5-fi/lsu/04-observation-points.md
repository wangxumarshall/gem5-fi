# 04 · 观测点定义（L0–L5 传播链）

> 来源：《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（Microsoft Excel 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「4.观测点定义」R2–R7（表头 R1），6 列 × 6 层级。

| 层级 | 含义 | LSU必须记录的字段/状态 | 建议实现点 | 判定用途 | 注意事项 |
|---|---|---|---|---|---|
| L0 注入/激活 | 确认是否尝试注入、是否满足资格、是否真正命中并被消费 | attempted、eligible、activated、结构entry/way、bit/字段、原值/故障值、注入时刻、寿命区间、指令/事务ID、commit序号 | 故障注入器入口与目标字段读取点 | 未activated的运行不得进入错误率分母 | 单次瞬态只在一个随机合法事件生效；重复注入逐次重新抽取目标 |
| L1 单元内部 | 检查局部状态守恒与结构不变量 | AGU的EA/size/mask；TLB映射；LQ/SQ有效项与转发；cache tag-data-state；MSHR/free计数；monitor；prefetch queue | 各结构更新、仲裁、读写与状态迁移处 | 区分局部屏蔽、内部异常和向下游传播 | 断言/仿真器异常单列Simulator failure，不直接并入架构检测 |
| L2 请求形成/顺序 | 观察LSU生成的访存请求及乱序恢复是否正确 | PA、size、byte mask、request/response ID、issued/dropped/duplicate、violation、replay、依赖和顺序标签 | 请求发射、响应匹配、replay与commit前检查处 | 识别错地址、错大小、重复/丢失及错误replay | 同一事务链用统一ID贯穿，避免只按周期关联 |
| L3 Cache/一致性/内存 | 追踪错误是否进入缓存层次或内存 | hit/miss、set/way、fill、eviction、writeback、snoop、ownership、dirty、DRAM写入 | L1d接口、一致性消息与内存写入点 | 判定是否被cache命中/替换屏蔽或形成持久污染 | 预取错误要区分纯性能影响与需求数据/所有权污染 |
| L4 架构可见/软件 | 定位首次架构状态分歧及其软件后果 | commit PC/opcode、寄存器与内存副作用、首次错误load/store、异常/信号、应用校验 | 提交端、异常入口和应用oracle | 区分Data Corruption、Crash、Timeout与正确完成 | 首次错误提交与最终应用结局都要记录 |
| L5 检测与最终结局 | 把首检来源和最终结局分开记录 | Hardware RAS/OS/Application/None首检；Hardware RAS任意时点；Masked、Detected-contained、Detected-uncontained、Data Corruption、RAS-silent Crash/Timeout、Simulator failure | 统一后处理脚本和运行日志汇总 | 支持互斥首检、任意时点硬件检测率和结局守恒校验 | 首检来源互斥；Simulator failure与体系结构结局分栏 |

