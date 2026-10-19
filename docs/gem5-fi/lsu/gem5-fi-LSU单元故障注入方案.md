# gem5-fi-LSU单元故障注入方案（Markdown 转换版）

<!-- lsu-xlsx2md-metadata
Source-File: gem5-fi-LSU单元故障注入方案.xlsx
Source-SHA256: 389546f0f8f3d0c6ece2ed33d3a8cfd1426faa9bbc101f7ad7d9612159e273e0
Source-MTime-Local: 2026-10-19T20:46:38
Source-Size-Bytes: 181590
Generated-At-Local: 2026-10-19T21:23:54
Sheet-Count: 12
RunID-Count-Sheet7: 325
RunID-Count-Sheet9: 325
Tool: tools/lsu_xlsx_to_md.py
-->

> 本文档由上述 SHA256 对应的 xlsx 工作簿**自动完整转换**生成；源文件未被修改。
> 转换规则：单元格换行→`<br>`；`|`→`\|`；全宽合并横幅→`### 分节横幅`；尾部全空行不列出（各节注记披露）；隐藏行列内容仍完整列出。

## 目录

| # | 工作表 | 规模 | 位置 |
|---|--------|------|------|
| 0 | 0.说明与总览 | 1 列 × 30 行 | [本文 0.说明与总览](#sheet-0) |
| 1 | 1.单元与现有研究 | 7 列 × 8 行 | [本文 1.单元与现有研究](#sheet-1) |
| 2 | 2.LSU参数基线 | 5 列 × 29 行 | [本文 2.LSU参数基线](#sheet-2) |
| 3 | 3.位置x模型矩阵 | 14 列 × 65 行 | [子文档 gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md](gem5-fi-LSU单元故障注入方案-03-位置x模型矩阵.md) |
| 4 | 4.观测点定义 | 6 列 × 7 行 | [本文 4.观测点定义](#sheet-4) |
| 5 | 5.频率与统计 | 6 列 × 20 行 | [本文 5.频率与统计](#sheet-5) |
| 6 | 6.负载清单 | 6 列 × 15 行 | [本文 6.负载清单](#sheet-6) |
| 7 | 7.展开执行矩阵 | 43 列 × 338 行 | [子文档 gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md](gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md) |
| 8 | 8.文献与来源 | 6 列 × 12 行 | [本文 8.文献与来源](#sheet-8) |
| 9 | 9.逐RunID传播监控 | 17 列 × 326 行 | [子文档 gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md](gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md) |
| 10 | 10.源码监控映射 | 10 列 × 65 行 | [子文档 gem5-fi-LSU单元故障注入方案-10-源码监控映射.md](gem5-fi-LSU单元故障注入方案-10-源码监控映射.md) |
| 11 | 11.传播事件字段规范 | 5 列 × 24 行 | [本文 11.传播事件字段规范](#sheet-11) |

<a id="sheet-0"></a>
## 0.说明与总览
> 1 列 × 30 行；非空单元格 27

| LSU 单元故障注入方案 — 总览 |
|---|
|  |
| 范围：AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器。 |
| 统一基线：LSU单元参数总表.md 的 B0。除 DTLB=32 项是为复现 TC'23 的显式覆盖外，其余优先采用 gem5 stable 的 O3_ARM_v7a_3 / BaseO3CPU / ArmMMU 配置。 |
| 重要纠正：B0 是可复现实验模型，不是鲲鹏 920 复刻；cache ports=200 不是物理端口数；当前 ARM 示例为 1 Load FU + 1 Store FU，L1D=32KiB/2-way，StridePrefetcher 位于 L2。 |
|  |
| 工作簿结构 |
| 1.单元与现有研究：逐单元填写“现有文章”和“现有文章结果”，并严格区分 AVF、非Benign条件占比、检测率和DelayAVF。 |
| 2.LSU参数基线：参数合理性审查、B0定值与单因素敏感性配置。 |
| 3.位置×模型矩阵：按“注入位置→故障子模型→注入条件/频率→负载→观测→预期→理由→依据→保护机制”展开，避免在位置和模型之间重复叙述。 |
| 4.观测点定义：L0-L5传播链；SDC率分母只用activated，不用attempted。 |
| 5.频率与统计：事件归一化频率、周期换算、随机化与样本量。 |
| 6.负载清单：论文复现、公开通用和定向探针负载。 |
| 7.展开执行矩阵：以运行级独立样本记录；保留模型ID、频率档、负载、seed、eligible/activated、首次检测、最终结局、保护机制证据，并显式记录故障表现形式/子模型。 |
| 8.文献与来源：本地论文和官方源码定位。 |
|  |
| 统计与判定边界 |
| ① attempted、eligible、activated分开记录。目标未被后续读取/使用的注入归入Injected-not-activated，不进入结果率分母。 |
| ② F0单次故障用于AVF/论文对照；F1-F4是重复/突发故障压力实验，不能与F0混成一个“故障率”。F5永久故障按运行分类。 |
| ③ 当前批次所有RunID统一先完成385个activated样本（含前期试跑样本），暂不区分重点实验，也不设置额外扩样；完成首轮结果审查后再统一决定是否追加样本。 |
| ④ 每个故障运行绑定同一checkpoint、输入、seed和无故障golden run；结构化换值只允许替换成明确合法值，并保存源值/目标值。 |
| ⑤ 预期结果是可证伪假设，不是实测结论。没有论文直接结果的AGU、原子/同步和多数结构化模型，实测列必须保持待执行。 |
| ⑥ 检测情况与最终结局采用二维记录：首检层级为 Hardware RAS / OS / Application / None，并另记 Hardware RAS 是否在任意时点检出。SDC 是 Hardware RAS 全程静默时的错误结果总类：SDC = RAS-silent Data Corruption + RAS-silent Crash + RAS-silent Timeout。Crash、Timeout、Data Corruption 仅是最终表现形式；OS 或 Application 检出不排除 SDC。Masked 与 Simulator failure 不计入 SDC；离线 oracle 不算运行时检测。 |
| 完善版增量 |
| 补充PPN与SQ基础对照、Load Queue、MSHR资源记账、原子操作数、预取触发脏驱逐、真实应用负载，以及F1-F4按运行聚类的统计规则；原58条模型扩展为64条。 |
| 逐RunID传播监控增量（2026-10-19） |
| 9.逐RunID传播监控：覆盖325个非空RunID，逐行给出完整路径、具体指标、现有源码、缺失钩子、关联键和终止判定。 |
| 10.源码监控映射：64个模型与fi-ding提交8aec2a8b970c397379cc038c5be428fe0ccd2c12的源码审计映射。 |
| 11.传播事件字段规范：建议统一事件schema。 |
| 重跑准备：7.展开执行矩阵的P:AP旧Seed、统计、结局、检测、公式、状态和备注已在本输出副本中全部清空；原始工作簿未覆盖。 |

<a id="sheet-1"></a>
## 1.单元与现有研究
> 7 列 × 8 行；非空单元格 56

| 单元 | 作用 | 现有文章 | 现有文章结果 | 指标口径 | 证据直接性 | 研究空白/本方案增量 |
|---|---|---|---|---|---|---|
| AGU | 生成load/store有效地址，含base/index选择、扩展/移位、地址加法、访问尺寸与请求路由。 | 本地论文中无直接AGU故障注入。ITC'23仅说明访存地址生成位于独立FU，但没有注入。 | 无直接实测结果。 | 不适用 | 同机制类比 | 空白：合法地址替换、寻址模式拼接、byte-enable和ready时序。 |
| L1d-TLB | 缓存VA→PA翻译与权限/属性，未命中时触发page walk。 | TC'22：Arm A5/A9，DTLB单bit瞬态，每部件≥1000次；CRC32/FFT/MatMul/Qsort。TC'23：Armv8类A72/Armv7类A15，32项全相联DTLB，MiBench 10个，每负载2000次。 | TC'22将ITLB/DTLB合并：平均Crash AVF约50%、Hang约10%、SDC AVF<1%。TC'23 Armv8：SDC占非Benign故障22.2%，内核指令贡献2.3个百分点；执行时间错组内11.8%。 | TC'22为AVF；TC'23为非Benign条件占比，不能直接比较 | 直接 | 空白：字段级PPN/权限/ASID、合法映射替换、refill时序、永久与保护故障。 |
| Store Queue | 缓存未提交store，维护顺序并做store-to-load forwarding；本方案把SSIT/LFST归入其子位置。 | IISWC'15：LSQ/SQ数据域单bit瞬态，MiBench 10个，2000次/结构/负载。TC'23：16项LQ/SQ分别注入，2000次/负载。HPCA'24：32项LQ/SQ，MiBench 15个，1000次/结构。Harpocrates++：SQ数据域检测率。MICRO'24 DelayAVF：Ibex LSU 2027根线，BEEBS 5个，每根线抽4%执行周期。 | IISWC'15：平均非掩蔽通常<3%，五类后果均有。TC'23：LQ/SQ SDC概率均为0，论文归因于commit前依赖检查。HPCA'24总AVF：LQ Arm 2.4%-8.6%，SQ Arm 2.2%-6.2%。Harpocrates++多数基线程序检出0%-1%，个别约20%。DelayAVF证明LSQ对小延迟故障的排序与粒子AVF不同，但不提供SDC/Crash分解。 | 非掩蔽率、条件SDC、总AVF、检出率、DelayAVF并存，严禁混算 | 直接+不同模型 | 空白：forward比较/拼接、byte mask、状态指针、SSIT/LFST、事务ack和保护链。 |
| L1d-Cache | 保存最近数据，含tag/data/valid/dirty/coherence、替换、MSHR、fill/writeback。 | IISWC'15、TC'22、TC'23、HPCA'24/ITC'23/ETS'24、Harpocrates均直接注入L1D data/tag或永久故障；CHAOS补充单/多bit与stuck-at频率规律。 | IISWC'15：非掩蔽2.5%-47.3%，SDC为主导。TC'22：A9 L1D SDC AVF约30%（文中约数）。TC'23 Armv8非Benign中data/tag的SDC占53.4%/38.0%；高字节位置SDC概率下降。HPCA'24：Arm瞬态L1D AVF 4.3%-44.9%，SDC AVF 1.2%-43%；永久SDC 5.1%-53.3%。Harpocrates最佳基线约80%，生成程序接近90%检出。 | 非掩蔽率、AVF、条件SDC、检测率需分列解释 | 直接 | 空白：dirty/coherence、MSHR merge、tag-data错配、fill/writeback时序与保护失效。 |
| 原子与同步 | 实现LDXR/STXR、LSE原子RMW和DMB/DSB排序，依赖exclusive monitor与一致性。 | 本地论文中无直接原子/屏障单元故障注入。 | 无直接实测结果。 | 不适用 | 空白 | 必须用多核FS和litmus禁出现结果；普通单线程benchmark不足以激活。 |
| 数据预取器 | 训练访存模式并生成预取请求；B0用L2 StridePrefetcher代理。 | TC'23明确未注入，理由是普通预取错误不改变架构状态。MICRO'24 DelayAVF直接研究Ibex prefetch buffer：3249根线、BEEBS 5个、每根线抽4%周期。IISWC'15表中列出L1D prefetcher差异，但没有可分离的预取器结果。 | MICRO'24指出Ibex prefetcher既有较高particle-strike AVF也有较高DelayAVF，原因是内部buffer把cache line送入流水线；论文没有给SDC/Crash分解。TC'23的“无架构状态变化”只覆盖普通预测地址错误，未覆盖fill tag/data/dirty控制出错。 | DelayAVF与SDC率不同；其结果只能作机制证据 | 部分直接（不同核心/故障模型） | 空白：需求-预取事务配对、fill tag-data错配、dirty/ownership误赋、保护链。 |
| Load Queue | 跟踪在飞load的地址、发射/完成状态、与更老store的冲突及violation/replay；还参与cache response与目标动态指令配对。 | TC'23对16项LQ直接注入；HPCA'24对32项LQ报告Arm总AVF；IISWC'15覆盖LSQ数据/地址类字段。 | TC'23报告LQ SDC概率为0并归因于commit前依赖检查；HPCA'24 Arm LQ总AVF约2.4%-8.6%。两者指标口径不同。 | 条件SDC、总AVF和replay/检测率分开报告 | 直接+机制扩展 | 空白：生命周期状态、violation/replay本身、response transaction ID与目标load错配、保护链。 |

<a id="sheet-2"></a>
## 2.LSU参数基线
> 5 列 × 29 行；非空单元格 136

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
|  |  |  |  |  |

### 分节横幅：逐单元保护机制核验（只列实际存在且纳入实现的机制）

| 结构/单元 | 实际存在的机制 | 在本方案中的处理 | 实现/观测口径 | 边界说明 |
|---|---|---|---|---|
| AGU | 地址生成后进入翻译、对齐与访问权限检查 | 归入架构异常或功能性阻断，不直接计Hardware RAS | 对照EA、PA、size、mask、异常原因与提交结果 | EA oracle只用于实验观测，不是硬件保护机制 |
| L1d-TLB | TLB命中、页表遍历、权限/属性与页故障路径 | 命中错误或映射错误按传播结果分类 | 记录VPN/ASID、PPN、权限、命中way、walk/fill与fault | 未核实B0配置ECC/parity，不把正常翻译检查写成RAS |
| Load Queue | 地址冲突检测、violation与replay、提交约束 | replay视为功能性恢复；断言失败单列Simulator failure | 记录LQ entry、依赖、violation、replay目标、返回ID与提交 | 软件oracle和离线一致性检查不计硬件首检 |
| Store Queue | 转发、顺序、提交、请求/应答生命周期约束 | 成功重放/阻断可归Contained，但需有明确证据 | 记录SQ entry、地址、数据、mask、forwarding、request/ack与commit | 未核实专用ECC/parity；普通状态机检查不自动等同RAS |
| L1d-Cache | tag/data/state、一致性、fill、eviction与writeback流程 | 以真实告警或异常证据决定Hardware RAS；否则按结局分类 | 记录set/way、tag、data、MESI、dirty、MSHR、fill/writeback和snoop | B0未配置ECC/parity；一致性协议属于功能机制 |
| 原子与同步 | exclusive monitor、CAS/LL-SC返回、barrier与内存顺序 | 按原子结果、顺序和可见性是否被破坏分类 | 记录monitor、比较值、old/new value、success状态、order tag与barrier完成 | litmus oracle用于判定，不是硬件RAS |
| 数据预取器 | 地址过滤、队列、取消/节流及与需求请求的区分 | 普通预取失误通常应被屏蔽；污染所有权/dirty时重点追踪 | 记录prefetch地址、来源PC、stride、队列、请求标签、allocate/ownership | B0未配置ECC/parity；性能退化与架构错误分开统计 |

注：合并单元格：A21:E21（全宽横幅已作分节标题；其余仅锚单元格有值）。

<a id="sheet-4"></a>
## 4.观测点定义
> 6 列 × 7 行；非空单元格 42

| 层级 | 含义 | LSU必须记录的字段/状态 | 建议实现点 | 判定用途 | 注意事项 |
|---|---|---|---|---|---|
| L0 注入/激活 | 确认是否尝试注入、是否满足资格、是否真正命中并被消费 | attempted、eligible、activated、结构entry/way、bit/字段、原值/故障值、注入时刻、寿命区间、指令/事务ID、commit序号 | 故障注入器入口与目标字段读取点 | 未activated的运行不得进入错误率分母 | 单次瞬态只在一个随机合法事件生效；重复注入逐次重新抽取目标 |
| L1 单元内部 | 检查局部状态守恒与结构不变量 | AGU的EA/size/mask；TLB映射；LQ/SQ有效项与转发；cache tag-data-state；MSHR/free计数；monitor；prefetch queue | 各结构更新、仲裁、读写与状态迁移处 | 区分局部屏蔽、内部异常和向下游传播 | 断言/仿真器异常单列Simulator failure，不直接并入架构检测 |
| L2 请求形成/顺序 | 观察LSU生成的访存请求及乱序恢复是否正确 | PA、size、byte mask、request/response ID、issued/dropped/duplicate、violation、replay、依赖和顺序标签 | 请求发射、响应匹配、replay与commit前检查处 | 识别错地址、错大小、重复/丢失及错误replay | 同一事务链用统一ID贯穿，避免只按周期关联 |
| L3 Cache/一致性/内存 | 追踪错误是否进入缓存层次或内存 | hit/miss、set/way、fill、eviction、writeback、snoop、ownership、dirty、DRAM写入 | L1d接口、一致性消息与内存写入点 | 判定是否被cache命中/替换屏蔽或形成持久污染 | 预取错误要区分纯性能影响与需求数据/所有权污染 |
| L4 架构可见/软件 | 定位首次架构状态分歧及其软件后果 | commit PC/opcode、寄存器与内存副作用、首次错误load/store、异常/信号、应用校验 | 提交端、异常入口和应用oracle | 区分Data Corruption、Crash、Timeout与正确完成 | 首次错误提交与最终应用结局都要记录 |
| L5 检测与最终结局 | 把首检来源和最终结局分开记录 | Hardware RAS/OS/Application/None 首检；Hardware RAS 任意时点；Hardware RAS 静默状态；Masked、Detected-contained、Detected-uncontained、Data Corruption、Crash、Timeout、SDC、Simulator failure | 统一后处理脚本和运行日志汇总 | 按 Hardware RAS 是否静默为 Data Corruption、Crash、Timeout 统一标记 SDC，同时保留最终表现形式 | 只要 Hardware RAS 任意时点检出数为 0，Data Corruption、Crash、Timeout 均计入 SDC；OS/Application 首检不排除 SDC；Masked 与 Simulator failure 不计入 SDC |

<a id="sheet-5"></a>
## 5.频率与统计
> 6 列 × 20 行；非空单元格 108

| 档位 | 名称 | 定义 | 适用故障 | 设计意图 | 统计单位 |
|---|---|---|---|---|---|
| F0 | 单次瞬态 | 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样 | 瞬态/结构化 | 论文对照与注入器校验；主报告必须给 activated/attempted | run-level独立样本 |
| F1 | 低频事件归一化 | 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动 | 瞬态 | 跨负载可比，减少循环相位共振；主力低频档 | run-level cluster；事件级仅作传播记录 |
| F2 | 中频事件归一化 | 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动 | 瞬态/结构化 | 定位 SDC/Crash 转折 | run-level cluster；事件级仅作传播记录 |
| F3 | 高频压力 | 平均每 10,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动 | 瞬态 | 只用于压力边界，不与 F0 的单故障 AVF 混合 | run-level cluster；事件级仅作传播记录 |
| F4 | 短突发 | 每 100,000 个 eligible events 触发一次，连续污染 2-4 个 eligible events | 多事件/时序 | 模拟共享控制线或瞬态持续多个周期 | run-level cluster；事件级仅作传播记录 |
| F5 | 永久卡死 | warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段 | 永久 | stuck-at 或固定掩码；结果按运行计数，不当作单次 AVF | run-level独立样本 |
| F6 | 确定性事件触发 | 首次出现指定事件时注入一次，如 TLB hit、SQ forward、dirty eviction、CAS 成功 | 结构化 | 保证激活，适合稀有路径和传播链调试 | run-level独立样本 |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
| 统计项 | 规则/公式 | 筛查目标 | 主结果目标 | 原因 | 备注 |
| 分母与二维分类 | 激活率=activated/attempted；可分析activated=activated-Simulator failure；SDC=RAS-silent Data Corruption+RAS-silent Crash+RAS-silent Timeout；SDC率=SDC/可分析activated；硬件检测率=Hardware RAS任意时点检出/可分析activated | 必须报告激活、结局、首检层级和硬件RAS任意时点检出 | 必须报告激活、结局、首检层级和硬件RAS任意时点检出 | 把 SDC 作为 Hardware RAS 静默的上位分类，保留 Data Corruption、Crash、Timeout 的最终表现；模拟器失败单列，避免污染架构结果 | 首检四类互斥；Hardware RAS任意时点检出可与OS/Application首检交叉 |
| 试跑/冒烟检查 | 可在正式批次内部查看早期样本以排查注入错误；不再单设30样本阶段 | 计入385 | — | 仅用于排查进入器错误、全Crash或零激活 | 不改变每个RunID的385首轮目标 |
| 统一首轮样本量 | 全部RunID统一完成385个activated样本（包含试跑，不区分重点实验） | 385 | 固定 | 作为当前全部实验的统一执行目标 | 完成首轮后再统一评估是否扩样 |
| 后续扩样 | 本阶段暂不设置重点实验或额外扩样规则 | — | 暂缓 | 待首轮385个activated样本完成后再决策 | 当前批次不得自行扩样 |
| 随机化 | seed、bit、entry、eligible event分层随机；合法换值保存source/target | 固定seed清单 | 每cell独立≥5个seed批次 | 避免单一程序相位和地址段主导 | 跨模型比较用common random numbers |
| 超时 | golden wall/sim time或committed inst的10×，并设置绝对上限 | 统一 | 统一 | 区分慢化与无限循环 | F5可单独提高上限但须预注册 |
| 2.6GHz换算 | 1ms=2,600,000 cycles；100us=260,000；10us=26,000 | 仅辅助 | 仅辅助 | 主频变化不会改变事件归一化档位 | 不要用cycle频率替代eligible event分母 |
| 独立样本单位 | F0/F5/F6通常以一次运行为独立样本；F1-F4同一运行内多个activated事件属于同一cluster | 按运行保存cluster ID | 按运行聚类计算区间 | 避免共享程序状态和前序故障导致伪独立 | 不得把同一运行内事件直接当独立Bernoulli样本 |
| 重复注入归因 | F1-F4最终结局归因于整次运行的故障序列；事件级传播另行记录 | 记录事件序列 | 报告run-level SDC/Crash与cluster bootstrap区间 | 多个故障可能共同导致最终错误 | F0单故障结果与压力档结果分开 |

<a id="sheet-6"></a>
## 6.负载清单
> 6 列 × 15 行；非空单元格 90

| 负载ID | 名称 | 类型 | 定义/输入与oracle | 主要覆盖单元 | 模式 |
|---|---|---|---|---|---|
| W0 | MiniCheck | 自设最小正确性探针 | 短数组校验和、guard page、指针链、load/store round-trip；每次运行产生确定 golden output | 全部；注入器冒烟与传播调试 | SE |
| W1 | MiBench-TC23 | 公开/论文复现 | blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth；最大输入集 | DTLB、SQ、L1D；与 TC'23 定性/定量对照 | FS 优先 |
| W2 | BEEBS-DelayAVF | 公开/论文复现 | md5、libbubblesort、libstrstr、matmult、libfibcall | LSQ 与预取器的时延故障规律对照；不直接比较绝对值 | SE |
| W3 | AGU-AddrModes | 自设定向负载 | 覆盖 base+imm、base+index、LSL、UXTW/SXTW、pre/post-index、LDP/STP、非对齐和页边界；每地址附软件 oracle | AGU | SE |
| W4 | TLB-AliasPerm | 自设定向负载 | 4KiB/2MiB 页、ASID 切换、同 VA 不同 PA、只读/不可执行页、TLBI 后重填、跨页 load/store | L1d-TLB | FS |
| W5 | SQ-Forward | 自设定向负载 | 同地址与部分重叠 store-to-load forwarding、不同字节掩码、地址晚到/数据晚到、alias、replay | Store Queue/内存依赖预测器 | SE |
| W6 | Cache-DirtyEvict | 自设定向负载 | working set=0.5×/1×/2×L1D；读改写、dirty eviction、writeback、conflict set、共享行 false sharing | L1d-Cache | SE + 多核 FS 子集 |
| W7 | Atomic-Litmus | 公开 litmus + 自设 | MP、SB、LB、IRIW、Dekker、ticket lock、CAS counter、LDXR/STXR 竞争；每轮检查禁出现结果 | 原子与同步 | 多核 FS |
| W8 | Prefetch-Stride | 自设定向负载 | 正/负/交错 stride、随机 pointer chase、跨页 stride、训练后变步长、需求/预取竞争 | 数据预取器 | SE |
| W9 | GAP/Graph500 子集 | 公开通用 | BFS/SSSP/PR，使用固定图与结果哈希；强调不规则地址和大 working set | DTLB、Cache、AGU、Prefetch | FS/SE |
| W10 | STREAM+PointerChase | 公开通用 + 自设 | STREAM Copy/Scale/Add/Triad 加随机 pointer chase；检查数组 hash 与遍历节点数 | 带宽、MSHR、预取、AGU | SE |
| W11 | SPEC CPU2017 采样区间 | 公开通用（需许可证） | 选择 mcf、omnetpp、xalancbmk、lbm 的固定 SimPoint/checkpoint；不跑全程 | 外部有效性；主结论之后复核 | FS/SE |
| W12 | SQLite-Speedtest1 | 真实应用 | SQLite speedtest1 固定数据库与事务脚本；用 PRAGMA integrity_check、查询结果和数据库文件哈希作为 oracle | AGU、Load Queue、Store Queue、L1d-Cache | SE/FS |
| W13 | PARSEC-Selected | 多线程真实应用 | PARSEC 中选 dedup、ferret、streamcluster 等共享队列/锁密集程序；固定线程数与输入，核对参考输出和结果哈希 | L1d-Cache一致性、原子与同步、数据预取器 | 多核 FS |

<a id="sheet-8"></a>
## 8.文献与来源
> 6 列 × 12 行；非空单元格 72

| 代码 | 标题/资源 | 类型/发表 | 核对方式 | 本工作簿用途 | 定位 |
|---|---|---|---|---|---|
| GEM5-O3 | gem5 stable: configs/common/cores/arm/O3_ARM_v7a.py | 官方源码 | 2026-09-24核对 | LQ/SQ、FU、LSQDepCheckShift、L1D、MSHR、预取器 | https://raw.githubusercontent.com/gem5/gem5/stable/configs/common/cores/arm/O3_ARM_v7a.py |
| GEM5-BASE | gem5 stable: src/cpu/o3/BaseO3CPU.py | 官方源码 | 2026-09-24核对 | LSQCheckLoads、Store Set、cache ports | https://raw.githubusercontent.com/gem5/gem5/stable/src/cpu/o3/BaseO3CPU.py |
| GEM5-MMU | gem5 stable: ArmMMU.py / ArmTLB.py | 官方源码 | 2026-09-24核对 | Arm TLB默认64项全相联、L2 TLB 1280项5-way | https://raw.githubusercontent.com/gem5/gem5/stable/src/arch/arm/ArmTLB.py |
| GEM5-SYS | gem5 stable: src/sim/System.py | 官方源码 | 2026-09-24核对 | cache_line_size=64 | https://raw.githubusercontent.com/gem5/gem5/stable/src/sim/System.py |
| IISWC15 | Differential Fault Injection on Microarchitectural Simulators | IISWC 2015 | 本地PDF | LSQ/SQ和L1D单bit、2000次/结构/负载、MiBench | Differential_Fault_Injection_on_Microarchitectural_Simulators.pdf |
| TC22 | Soft Error Effects on Arm Microprocessors: Early Estimations versus Chip Measurements | IEEE TC 2022 | 本地PDF | Arm A5/A9 DTLB/L1D，gem5与中子束 | Soft_Error_Effects_on_Arm_Microprocessors_Early_Estimations_versus_Chip_Measurements.pdf |
| TC23 | Silent Data Corruptions: Microarchitectural Perspectives | IEEE TC 2023 | 本地PDF | Armv8/Armv7 DTLB、LQ/SQ、L1D；2000次/负载 | Silent_Data_Corruptions_Microarchitectural_Perspectives.pdf |
| HPCA24 | gem5-MARVEL: Microarchitecture-Level Resilience Analysis of Heterogeneous SoC Architectures | HPCA 2024 | 本地PDF | Arm/x86/RISC-V的LQ/SQ/L1D瞬态与永久结果 | Gem5-MARVEL_Microarchitecture-Level_Resilience_Analysis_of_Heterogeneous_SoC_Architectures.pdf |
| MICRO24 | DelayAVF: Calculating Architectural Vulnerability Factors for Delay Faults | MICRO 2024 | 本地PDF | Ibex LSU与prefetch buffer的小延迟故障；DelayAVF不是SDC率 | MICRO2024 DelayAVF_Calculating_Architectural_Vulnerability_Factors_for_Delay_Faults.pdf |
| MICRO25 | Harpocrates++: Automated Functional Program Generation Against CPU Faults and Silent Data Corruptions | IEEE Micro 2025 | 本地PDF | SQ/L1D检测率；指标不是SDC率 | Harpocrates_Automated_Functional_Program_Generation_Against_CPU_Faults_and_Silent_Data_Corruptions.pdf |
| CHAOS26 | CHAOS: Controlled Hardware fAult injectOr System for gem5 | arXiv 2602.02119, 2026 | 本地PDF | 频率、单/多bit、stuck-at与HPC偏差规律 | Chaos Controlled Hardware Fault Injector System for Gem5.pdf |

<a id="sheet-11"></a>
## 11.传播事件字段规范
> 5 列 × 24 行；非空单元格 120

| 字段 | 作用域 | 含义 | 当前代码 | 本方案要求 |
|---|---|---|---|---|
| run_id | campaign配置ID | 工作簿RunID，如A01-F0-W3 | 运行参数/manifest | 已有于目录/manifest；要求写入每条事件 |
| sample_run_id | 单次注入尝试ID | RunID下第几个独立样本 | 新增统一字段 | 必需；解决一个RunID含多次attempt的问题 |
| fault_id / ptag | 故障链ID | 把同一故障产生的所有事件连接起来 | CHAOSPropagation已有ptag | 扩展到全部注入器 |
| event_id | 事件ID | 单Run内唯一事件 | CHAOSPropagation已有node_id | 统一改名或同时保留 |
| parent_event_id | 父事件ID | 直接表达传播边，避免离线猜边 | 缺失 | 必需新增 |
| tick / cycle | 时间 | 事件时刻及CPU周期 | 大部分日志已有tick | 统一同时记录cycle |
| core_id / thread_id | 执行上下文 | 多核/SMT关联 | commit有tid；多数注入日志缺 | 必需新增 |
| dyn_inst_seq | 动态指令键 | 跨LSQ/commit/PRF主键 | CHAOSPropagation/CommitTrace v2已有 | 全部LSU事件必须携带 |
| commit_seq | 提交顺序 | 定位首个错误提交 | CommitTrace已有全局seq | 写入传播事件或离线join |
| pc / opcode | 指令身份 | 区分load/store/atomic/寻址模式 | CommitTrace已有；传播日志缺 | 注入与LSQ事件新增 |
| lq_idx / sq_idx | 队列表项 | LQ/SQ生命周期与重放 | 缺失 | LSQ事件必需 |
| request_id / packet_id | 内存事务 | 请求-响应绑定 | Request instSeqNum被当request_id；非真正唯一 | 新增单调transaction_id，保留instSeqNum |
| walk_id / tlb_entry / way | 翻译事务 | TLB lookup/walk/refill关联 | 缺失 | TLB模型必需 |
| mshr_id / fill_id | miss/fill事务 | cache miss/merge/fill/evict关联 | 缺失 | cache/prefetch模型必需 |
| pf_request_id | 预取事务 | training→queue→request→fill→demand | 缺失 | prefetch模型必需 |
| VA / PA / cache_line | 地址键 | 记录各阶段地址，不混用VA/PA | 部分已有addr | 分别存储，不以SE VA==PA替代FS |
| set / way / entry_index | 结构位置 | cache/TLB/queue定位 | 注入日志部分有 | 所有结构事件补齐 |
| field / before / after | 局部差异 | 具体字段原值/故障值 | 各注入器格式不统一 | 统一typed字段+value/hash |
| state_before / state_after | 状态转移 | valid/dirty/coh/issued/completed等 | 缺失或仅文本 | 状态模型必需 |
| arch_reg / phys_reg / src-dst | 数据依赖 | response→PRF→consumer→commit | Propagation/CommitTrace v2部分已有 | 启用v2并补响应目标 |
| detection_layer / contained | 检测与控制 | Hardware RAS/OS/App/None及是否contained | 工作簿结果列，事件日志缺 | 最终判定事件必需 |
| outcome / oracle_diff | 结局 | Masked/DC/Crash/Timeout/SDC与golden差异 | runner/classifier已有 | 与fault_id/sample_run_id绑定 |
| evidence_status | 证据状态 | observed/derived/missing/conflict | 缺失 | 防止把缺失事件解释为未传播 |

