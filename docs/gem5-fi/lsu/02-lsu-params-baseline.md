# 02 · LSU 参数基线（B0 定值与敏感性 + 逐单元保护机制核验）

> 来源：《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（Microsoft Excel 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「2.LSU参数基线」：R1 表头；R2–R19 B0 参数与敏感性配置（18 行）；R20 空行；R21 节标题（**合并单元格 A21:E21**）；R22 第二节表头；R23–R29 逐单元保护机制核验（7 行）。

## B0 参数与敏感性配置（R2–R19）

| 结构/参数 | B0最终值 | 处理 | 依据/合理性判断 | 敏感性配置 |
|---|---|---|---|---|
| LQEntries | 16 | 保留 | O3_ARM_v7a_3明确覆盖 | B0 |
| SQEntries | 16 | 保留 | O3_ARM_v7a_3明确覆盖 | B0 |
| Load FU | 1个；MemRead/FloatMemRead opLat=2 | 修正 | 原表“每周期2 load”与官方示例不符 | B0 |
| Store FU | 1个；MemWrite/FloatMemWrite opLat=2 | 修正 | 官方示例独立1个Store FU | B0 |
| LSQDepCheckShift | 0 | 修正 | ARM示例明确覆盖0，不应取BaseO3CPU默认4 | B0；S3=4 |
| LSQCheckLoads | TRUE | 保留 | BaseO3CPU默认 | B0 |
| SSITSize / LFSTSize | 1024 / 1024 | 保留 | BaseO3CPU默认；SSIT 1-way LRU | B0 |
| store_set_clear_period | 250000 | 保留 | 按load/store指令计数 | B0 |
| cacheLoadPorts / cacheStorePorts | 200 / 200 | 澄清 | 近似不由该参数限流，不是物理端口数 | B0 |
| L1 DTLB | 32项全相联 LRU | 保留但降级为比较覆盖 | 复现TC'23；gem5当前默认64项全相联 | B0；S1=64 |
| L2 TLB | 1280项 5-way | 新增 | gem5 ArmMMU stable默认 | B0 |
| L1D容量/相联度 | 32KiB / 2-way | 修正 | 与O3_ARM_v7a_DCache一致；原64/4是服务器Arm风格而非该示例 | B0；S2=64KiB/4-way |
| Cache line | 64B | 保留并补证据 | gem5 System默认 | B0 |
| L1D tag/data/response latency | 2 / 2 / 2 cycles | 修正 | 官方示例；不把它们简单相加成真实load-to-use | B0 |
| L1D MSHR / targets | 6 / 8 | 保留并更正来源 | 官方O3_ARM_v7a_DCache直接给出，不依赖错位表推断 | B0 |
| L1D write buffers | 16 | 新增 | 官方O3_ARM_v7a_DCache | B0 |
| 数据预取器 | L2 StridePrefetcher degree=8, latency=1, prefetch_on_access=True | 修正 | 官方ARM O3示例挂L2；原L1D degree=4不准确 | B0；S4挂L1D |
| 时钟 | 2.6GHz仅用于换算 | 澄清 | 注入频率以eligible event为主，避免工作负载IPC偏差 | B0 |

## 逐单元保护机制核验（R21–R29）

R21 为合并单元格 **A21:E21** 的节标题：**逐单元保护机制核验（只列实际存在且纳入实现的机制）**（值存于 A21，B–E 为合并空区——全簿唯一合并单元格）。

R22 为第二节表头（原文照录）：

| 结构/单元 | 实际存在的机制 | 在本方案中的处理 | 实现/观测口径 | 边界说明 |
|---|---|---|---|---|

| AGU | 地址生成后进入翻译、对齐与访问权限检查 | 归入架构异常或功能性阻断，不直接计Hardware RAS | 对照EA、PA、size、mask、异常原因与提交结果 | EA oracle只用于实验观测，不是硬件保护机制 |
| L1d-TLB | TLB命中、页表遍历、权限/属性与页故障路径 | 命中错误或映射错误按传播结果分类 | 记录VPN/ASID、PPN、权限、命中way、walk/fill与fault | 未核实B0配置ECC/parity，不把正常翻译检查写成RAS |
| Load Queue | 地址冲突检测、violation与replay、提交约束 | replay视为功能性恢复；断言失败单列Simulator failure | 记录LQ entry、依赖、violation、replay目标、返回ID与提交 | 软件oracle和离线一致性检查不计硬件首检 |
| Store Queue | 转发、顺序、提交、请求/应答生命周期约束 | 成功重放/阻断可归Contained，但需有明确证据 | 记录SQ entry、地址、数据、mask、forwarding、request/ack与commit | 未核实专用ECC/parity；普通状态机检查不自动等同RAS |
| L1d-Cache | tag/data/state、一致性、fill、eviction与writeback流程 | 以真实告警或异常证据决定Hardware RAS；否则按结局分类 | 记录set/way、tag、data、MESI、dirty、MSHR、fill/writeback和snoop | B0未配置ECC/parity；一致性协议属于功能机制 |
| 原子与同步 | exclusive monitor、CAS/LL-SC返回、barrier与内存顺序 | 按原子结果、顺序和可见性是否被破坏分类 | 记录monitor、比较值、old/new value、success状态、order tag与barrier完成 | litmus oracle用于判定，不是硬件RAS |
| 数据预取器 | 地址过滤、队列、取消/节流及与需求请求的区分 | 普通预取失误通常应被屏蔽；污染所有权/dirty时重点追踪 | 记录prefetch地址、来源PC、stride、队列、请求标签、allocate/ownership | B0未配置ECC/parity；性能退化与架构错误分开统计 |

