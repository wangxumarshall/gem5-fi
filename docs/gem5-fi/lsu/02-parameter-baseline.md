# 02 · LSU参数基线

> 源：工作表「2.LSU参数基线」（20 行 × 5 列 = 100 格：r1 表头 + r2–r20 共 19 个参数数据行；5 列全列逐字转录）。
> 转录规则：单元格文本逐字转录；表格内 `\n` → `<br>`、`|` → `\|`（与 extract.py 的 `md_cell` 一致）；「Excel行」列为行号标注，非源表列。

| Excel行 | 结构/参数 | B0最终值 | 处理 | 依据/合理性判断 | 敏感性配置 |
|---|---|---|---|---|---|
| 2 | LQEntries | 16 | 保留 | O3_ARM_v7a_3明确覆盖 | B0 |
| 3 | SQEntries | 16 | 保留 | O3_ARM_v7a_3明确覆盖 | B0 |
| 4 | Load FU | 1个；MemRead/FloatMemRead opLat=2 | 修正 | 原表“每周期2 load”与官方示例不符 | B0 |
| 5 | Store FU | 1个；MemWrite/FloatMemWrite opLat=2 | 修正 | 官方示例独立1个Store FU | B0 |
| 6 | LSQDepCheckShift | 0 | 修正 | ARM示例明确覆盖0，不应取BaseO3CPU默认4 | B0；S3=4 |
| 7 | LSQCheckLoads | 1 | 保留 | BaseO3CPU默认 | B0 |
| 8 | SSITSize / LFSTSize | 1024 / 1024 | 保留 | BaseO3CPU默认；SSIT 1-way LRU | B0 |
| 9 | store_set_clear_period | 250000 | 保留 | 按load/store指令计数 | B0 |
| 10 | cacheLoadPorts / cacheStorePorts | 200 / 200 | 澄清 | 近似不由该参数限流，不是物理端口数 | B0 |
| 11 | L1 DTLB | 32项全相联 LRU | 保留但降级为比较覆盖 | 复现TC'23；gem5当前默认64项全相联 | B0；S1=64 |
| 12 | L2 TLB | 1280项 5-way | 新增 | gem5 ArmMMU stable默认 | B0 |
| 13 | L1D容量/相联度 | 32KiB / 2-way | 修正 | 与O3_ARM_v7a_DCache一致；原64/4是服务器Arm风格而非该示例 | B0；S2=64KiB/4-way |
| 14 | Cache line | 64B | 保留并补证据 | gem5 System默认 | B0 |
| 15 | L1D tag/data/response latency | 2 / 2 / 2 cycles | 修正 | 官方示例；不把它们简单相加成真实load-to-use | B0 |
| 16 | L1D MSHR / targets | 6 / 8 | 保留并更正来源 | 官方O3_ARM_v7a_DCache直接给出，不依赖错位表推断 | B0 |
| 17 | L1D write buffers | 16 | 新增 | 官方O3_ARM_v7a_DCache | B0 |
| 18 | L1D ECC/parity | 关闭 | 明确实验因子 | 与无保护文献可比；不能把未披露等同于无保护事实 | B0；S5启用保护 |
| 19 | 数据预取器 | L2 StridePrefetcher degree=8, latency=1, prefetch_on_access=True | 修正 | 官方ARM O3示例挂L2；原L1D degree=4不准确 | B0；S4挂L1D |
| 20 | 时钟 | 2.6GHz仅用于换算 | 澄清 | 注入频率以eligible event为主，避免工作负载IPC偏差 | B0 |

### 敏感性配置一览

从「敏感性配置」列归纳（19 行中 5 行带 S 变体，其余 14 行均为「B0」）：

- S1：DTLB 64 项 — 源 r11「B0；S1=64」（L1 DTLB 行）
- S2：L1D 64KiB/4-way — 源 r13「B0；S2=64KiB/4-way」（L1D容量/相联度行）
- S3：LSQDepCheckShift=4 — 源 r6「B0；S3=4」（LSQDepCheckShift 行）
- S4：预取器挂 L1D — 源 r19「B0；S4挂L1D」（数据预取器行）
- S5：启用 L1D 保护 — 源 r18「B0；S5启用保护」（L1D ECC/parity 行）
