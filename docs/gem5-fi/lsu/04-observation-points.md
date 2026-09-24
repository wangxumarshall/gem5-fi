# 04 · 观测点定义

> 源：工作表「4.观测点定义」（7 行 × 6 列：r1 表头 + r2–r7 共 L0–L5 六个层级数据行；6 列全列逐字转录）。
> 转录规则：单元格文本逐字转录；表格内 `\n` → `<br>`、`|` → `\|`（与 extract.py 的 `md_cell` 一致）；「Excel行」列为行号标注，非源表列。

| Excel行 | 层级 | 名称 | 定义 | 必须采集量 | 适用范围 | 判定规则 |
|---|---|---|---|---|---|---|
| 2 | L0 | 注入与激活 | attempt、eligible event、目标entry/bit、故障是否被后续读取/使用；未激活不进入SDC率分母 | attempted、eligible、activated、目标寿命、注入时commit序号 | 全部 | 未activated不进入SDC率分母 |
| 3 | L1 | 单元内部不变量 | 与无故障影子副本比较该单元状态，捕获SDC之前的局部偏差 | AGU EA；TLB映射；SQ守恒/forward；Cache tag-data-state；exclusive monitor；prefetch queue | 全部，按单元定制 | 与同checkpoint golden run逐事件/逐提交比较 |
| 4 | L2 | 请求形成与排序 | 观察翻译后PA、访问大小、依赖/重放、MSHR/事务ID、原子/屏障顺序 | PA/size/mask、request ID、replay/violation、issued/dropped/duplicate | LSU中段 | 与同checkpoint golden run逐事件/逐提交比较 |
| 5 | L3 | 缓存/一致性/内存传播 | 观察hit/miss、fill/writeback、snoop/ownership、最终DRAM写日志 | line/way、dirty、coherence、writeback data/address、跨核可见序 | Cache/Atomic/Prefetch重点 | 与同checkpoint golden run逐事件/逐提交比较 |
| 6 | L4 | 架构可见与软件传播 | commit处比较PC/opcode/register/memory side effect；记录污染到地址/分支/store的扇出 | 首次分歧commit序号、错误load值、错误store、异常、污染扇出 | 全部 | 与同checkpoint golden run逐事件/逐提交比较 |
| 7 | L5 | 最终结局 | Injected-not-activated / Masked / Detected-contained / SDC / Crash / Timeout；Crash区分gem5断言与架构崩溃 | 分类计数、输出diff、超时阈值、结束原因 | 全部 | Activated = Masked + Detected + SDC + Crash + Timeout |

> 提取注：L5 守恒式 `Activated = Masked + Detected + SDC + Crash + Timeout` 是后续统计回填的闭合校验式。
