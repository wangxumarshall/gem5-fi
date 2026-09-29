# 05 · 频率与统计（F0–F6 档位 + 统计规则）

> 来源：《gem5-fi-LSU单元故障注入方案V2.0.xlsx》（Microsoft Excel 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「5.频率与统计」：R1 表头；R2–R8 频率档位（F0–F6）；R9–R10 空行（原表分节）；R11 第二节表头；R12–R20 统计规则（9 条）。

## 频率档位（R2–R8）

| 档位 | 名称 | 定义 | 适用故障 | 设计意图 | 统计单位 |
|---|---|---|---|---|---|
| F0 | 单次瞬态 | 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样 | 瞬态/结构化 | 论文对照与注入器校验；主报告必须给 activated/attempted | run-level独立样本 |
| F1 | 低频事件归一化 | 平均每 1,000,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动 | 瞬态 | 跨负载可比，减少循环相位共振；主力低频档 | run-level cluster；事件级仅作传播记录 |
| F2 | 中频事件归一化 | 平均每 100,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动 | 瞬态/结构化 | 定位 SDC/Crash 转折 | run-level cluster；事件级仅作传播记录 |
| F3 | 高频压力 | 平均每 10,000 个 eligible events 注入 1 次，间隔加入 ±50% 抖动 | 瞬态 | 只用于压力边界，不与 F0 的单故障 AVF 混合 | run-level cluster；事件级仅作传播记录 |
| F4 | 短突发 | 每 100,000 个 eligible events 触发一次，连续污染 2-4 个 eligible events | 多事件/时序 | 模拟共享控制线或瞬态持续多个周期 | run-level cluster；事件级仅作传播记录 |
| F5 | 永久卡死 | warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段 | 永久 | stuck-at 或固定掩码；结果按运行计数，不当作单次 AVF | run-level独立样本 |
| F6 | 确定性事件触发 | 首次出现指定事件时注入一次，如 TLB hit、SQ forward、dirty eviction、CAS 成功 | 结构化 | 保证激活，适合稀有路径和传播链调试 | run-level独立样本 |

〔提取注〕各档位在「7.展开执行矩阵」325 格中的实际格数：F0=105、F1=24、F2=77、F3=4、F4=26、F5=25、F6=64——全部 7 档均被使用（F3 高频压力仅 4 格）。

## 统计规则（R11 表头；R12–R20）

| 统计项 | 规则/公式 | 筛查目标 | 主结果目标 | 原因 | 备注 |
|---|---|---|---|---|---|
| 分母与二维分类 | 激活率=activated/attempted；可分析activated=activated-Simulator failure；SDC率=SDC/可分析activated；硬件检测率=Hardware RAS任意时点检出/可分析activated | 必须报告激活、结局、首检层级和硬件RAS任意时点检出 | 必须报告激活、结局、首检层级和硬件RAS任意时点检出 | 区分真正SDC、RAS-silent Crash/Timeout和Detected-uncontained；模拟器失败单列，避免污染架构结果 | 首检四类互斥；Hardware RAS任意时点检出可与OS/Application首检交叉 |
| 试跑 | 每单元×模型×频率×负载先取得30个activated | 30 | 30 | 发现注入器错误、全Crash或零激活单元 | 不用于最终窄置信区间 |
| 筛查样本量 | 最坏p=0.5，95%正态近似，半宽5pp约385个activated | ≥385 | — | 用于淘汰纯性能/全Crash组合 | 正式报告使用Wilson区间 |
| 主结果停止 | 顺序增加样本，Wilson 95%区间半宽≤2pp或activated达到5000 | — | ≤2pp或5000 | 在可控成本下统一精度 | 报告实际区间，不只报点估计 |
| 随机化 | seed、bit、entry、eligible event分层随机；合法换值保存source/target | 固定seed清单 | 每cell独立≥5个seed批次 | 避免单一程序相位和地址段主导 | 跨模型比较用common random numbers |
| 超时 | golden wall/sim time或committed inst的10×，并设置绝对上限 | 统一 | 统一 | 区分慢化与无限循环 | F5可单独提高上限但须预注册 |
| 2.6GHz换算 | 1ms=2,600,000 cycles；100us=260,000；10us=26,000 | 仅辅助 | 仅辅助 | 主频变化不会改变事件归一化档位 | 不要用cycle频率替代eligible event分母 |
| 独立样本单位 | F0/F5/F6通常以一次运行为独立样本；F1-F4同一运行内多个activated事件属于同一cluster | 按运行保存cluster ID | 按运行聚类计算区间 | 避免共享程序状态和前序故障导致伪独立 | 不得把同一运行内事件直接当独立Bernoulli样本 |
| 重复注入归因 | F1-F4最终结局归因于整次运行的故障序列；事件级传播另行记录 | 记录事件序列 | 报告run-level SDC/Crash与cluster bootstrap区间 | 多个故障可能共同导致最终错误 | F0单故障结果与压力档结果分开 |

