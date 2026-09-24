# 01 · 单元与现有研究

> 源：工作表「1.单元与现有研究」（8 行 × 7 列 = 56 格：r1 表头 + r2–r8 共 7 个单元数据行；7 列全列逐字转录）。
> 转录规则：单元格文本逐字转录；表格内 `\n` → `<br>`、`|` → `\|`（与 extract.py 的 `md_cell` 一致）；「Excel行」列为行号标注，非源表列。

| Excel行 | 单元 | 作用 | 现有文章 | 现有文章结果 | 指标口径 | 证据直接性 | 研究空白/本方案增量 |
|---|---|---|---|---|---|---|---|
| 2 | AGU | 生成load/store有效地址，含base/index选择、扩展/移位、地址加法、访问尺寸与请求路由。 | 本地论文中无直接AGU故障注入。ITC'23仅说明访存地址生成位于独立FU，但没有注入。 | 无直接实测结果。 | 不适用 | 同机制类比 | 空白：合法地址替换、寻址模式拼接、byte-enable和ready时序。 |
| 3 | L1d-TLB | 缓存VA→PA翻译与权限/属性，未命中时触发page walk。 | TC'22：Arm A5/A9，DTLB单bit瞬态，每部件≥1000次；CRC32/FFT/MatMul/Qsort。TC'23：Armv8类A72/Armv7类A15，32项全相联DTLB，MiBench 10个，每负载2000次。 | TC'22将ITLB/DTLB合并：平均Crash AVF约50%、Hang约10%、SDC AVF<1%。TC'23 Armv8：SDC占非Benign故障22.2%，内核指令贡献2.3个百分点；执行时间错组内11.8%。 | TC'22为AVF；TC'23为非Benign条件占比，不能直接比较 | 直接 | 空白：字段级PPN/权限/ASID、合法映射替换、refill时序、永久与保护故障。 |
| 4 | Store Queue | 缓存未提交store，维护顺序并做store-to-load forwarding；本方案把SSIT/LFST归入其子位置。 | IISWC'15：LSQ/SQ数据域单bit瞬态，MiBench 10个，2000次/结构/负载。TC'23：16项LQ/SQ分别注入，2000次/负载。HPCA'24：32项LQ/SQ，MiBench 15个，1000次/结构。Harpocrates++：SQ数据域检测率。MICRO'24 DelayAVF：Ibex LSU 2027根线，BEEBS 5个，每根线抽4%执行周期。 | IISWC'15：平均非掩蔽通常<3%，五类后果均有。TC'23：LQ/SQ SDC概率均为0，论文归因于commit前依赖检查。HPCA'24总AVF：LQ Arm 2.4%-8.6%，SQ Arm 2.2%-6.2%。Harpocrates++多数基线程序检出0%-1%，个别约20%。DelayAVF证明LSQ对小延迟故障的排序与粒子AVF不同，但不提供SDC/Crash分解。 | 非掩蔽率、条件SDC、总AVF、检出率、DelayAVF并存，严禁混算 | 直接+不同模型 | 空白：forward比较/拼接、byte mask、状态指针、SSIT/LFST、事务ack和保护链。 |
| 5 | L1d-Cache | 保存最近数据，含tag/data/valid/dirty/coherence、替换、MSHR、fill/writeback。 | IISWC'15、TC'22、TC'23、HPCA'24/ITC'23/ETS'24、Harpocrates均直接注入L1D data/tag或永久故障；CHAOS补充单/多bit与stuck-at频率规律。 | IISWC'15：非掩蔽2.5%-47.3%，SDC为主导。TC'22：A9 L1D SDC AVF约30%（文中约数）。TC'23 Armv8非Benign中data/tag的SDC占53.4%/38.0%；高字节位置SDC概率下降。HPCA'24：Arm瞬态L1D AVF 4.3%-44.9%，SDC AVF 1.2%-43%；永久SDC 5.1%-53.3%。Harpocrates最佳基线约80%，生成程序接近90%检出。 | 非掩蔽率、AVF、条件SDC、检测率需分列解释 | 直接 | 空白：dirty/coherence、MSHR merge、tag-data错配、fill/writeback时序与保护失效。 |
| 6 | 原子与同步 | 实现LDXR/STXR、LSE原子RMW和DMB/DSB排序，依赖exclusive monitor与一致性。 | 本地论文中无直接原子/屏障单元故障注入。 | 无直接实测结果。 | 不适用 | 空白 | 必须用多核FS和litmus禁出现结果；普通单线程benchmark不足以激活。 |
| 7 | 数据预取器 | 训练访存模式并生成预取请求；B0用L2 StridePrefetcher代理。 | TC'23明确未注入，理由是普通预取错误不改变架构状态。MICRO'24 DelayAVF直接研究Ibex prefetch buffer：3249根线、BEEBS 5个、每根线抽4%周期。IISWC'15表中列出L1D prefetcher差异，但没有可分离的预取器结果。 | MICRO'24指出Ibex prefetcher既有较高particle-strike AVF也有较高DelayAVF，原因是内部buffer把cache line送入流水线；论文没有给SDC/Crash分解。TC'23的“无架构状态变化”只覆盖普通预测地址错误，未覆盖fill tag/data/dirty控制出错。 | DelayAVF与SDC率不同；其结果只能作机制证据 | 部分直接（不同核心/故障模型） | 空白：需求-预取事务配对、fill tag-data错配、dirty/ownership误赋、保护链。 |
| 8 | Load Queue | 跟踪在飞load的地址、发射/完成状态、与更老store的冲突及violation/replay；还参与cache response与目标动态指令配对。 | TC'23对16项LQ直接注入；HPCA'24对32项LQ报告Arm总AVF；IISWC'15覆盖LSQ数据/地址类字段。 | TC'23报告LQ SDC概率为0并归因于commit前依赖检查；HPCA'24 Arm LQ总AVF约2.4%-8.6%。两者指标口径不同。 | 条件SDC、总AVF和replay/检测率分开报告 | 直接+机制扩展 | 空白：生命周期状态、violation/replay本身、response transaction ID与目标load错配、保护链。 |

> 提取注：指标口径纪律（AVF/条件占比/总 AVF/检出率/DelayAVF 严禁混算）为源表对后续全部实验的硬约束。
