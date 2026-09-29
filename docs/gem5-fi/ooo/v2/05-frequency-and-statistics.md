# 05 · 频率与统计（F0–F6 档位 + 统计规则）

> 来源：《gem5-fi-OoO单元故障注入方案V2.0.xlsx》（WPS 生成，9 表），逐格忠实提取：单元格文字原文照录，仅版式/标题排版；〔提取注〕为本目录标注。
> 生成器：`extract_v2.py`（纯标准库，确定性输出，可重跑复现）；断言结果与诚实性注记见 `README.md`。

> 工作表「5.频率与统计」：R1 表头；R2–R8 频率档位（F0–F6）；R9 空行（原表分节）；R10 第二节表头；R11–R18 统计规则（8 条）。

## 频率档位（R2–R8）

| 档位 | 名称 | 定义 | 适用故障 | 设计意图 | 统计单位 |
|---|---|---|---|---|---|
| F0 | 单次瞬态 | 每次运行只注入1次；warm-up后在 eligible event 中均匀抽样 | 瞬态/结构化 | 论文对照与AVF主基线 | run-level独立样本 |
| F1 | 低频事件归一化 | 平均每1,000,000个 eligible events 注入1次，间隔加入±50%抖动 | 瞬态/结构化 | 低频跨负载比较 | run-level cluster；事件级仅作传播记录 |
| F2 | 中频事件归一化 | 平均每100,000个 eligible events 注入1次，间隔加入±50%抖动 | 瞬态/结构化 | 观察SDC/Crash转折 | run-level cluster；事件级仅作传播记录 |
| F3 | 高频压力 | 平均每10,000个 eligible events 注入1次，间隔加入±50%抖动 | 瞬态/结构化 | 仅作压力上界 | run-level cluster；事件级仅作传播记录 |
| F4 | 短突发 | 每100,000个 eligible events 触发一次，连续污染2-4个 eligible events | 时序/多周期突发 | 共享控制线或短时延持续 | run-level cluster；事件级仅作传播记录 |
| F5 | 永久卡死 | warm-up后第一个 eligible event 起持续至运行结束；每次运行只选1 bit/字段 | 永久stuck-at/固定掩码 | 永久缺陷 | run-level独立样本 |
| F6 | 确定性事件触发 | 首次出现指定稀有事件时注入1次，保证结构化模型被激活 | 稀有结构化事件 | 保证激活与传播调试 | run-level独立样本 |

〔提取注〕F3（高频压力）在「7.展开执行矩阵」310 格中为 0 格——定义存在、未被使用；各档位实际格数：F0=104、F1=12、F2=76、F3=0、F4=28、F5=10、F6=80。详见 `07-expanded-matrix.md` 与 `README.md` 诚实性注记 (c)。

## 统计规则（R10 表头；R11–R18）

| 统计项 | 规则/公式 | 筛查目标 | 主结果目标 | 原因 | 备注 |
|---|---|---|---|---|---|
| 分母与二维分类 | 可分析activated=activated-Simulator failure；SDC率=SDC/可分析activated；激活率=activated/attempted | 报告激活、结局、首检层级 | 同左并给Wilson区间 | 避免空项和模拟器失败稀释结果 | 检测维度与结局维度分开 |
| 试跑 | 每模型×频率×负载先取得30个activated | 30 | 30 | 发现注入器错误、零激活或全Crash组合 | 不用于窄置信区间 |
| 筛查样本量 | 最坏p=0.5，95%正态近似，半宽5pp约385 | 385 | - | 淘汰低价值组合 | 正式报告仍用Wilson |
| 主结果停止 | 顺序增加样本，Wilson 95%半宽<=2pp或activated=5000 | - | <=2pp或5000 | 统一精度和成本 | 报告实际样本量 |
| 随机化 | seed、entry、bit、eligible event分层随机；合法换值保存source/target | 固定seed清单 | 每cell独立>=5个seed批次 | 避免程序相位、固定ROB slot和寄存器热点 | 跨模型用common random numbers |
| 超时 | golden sim time或committed inst的10倍，并设置绝对上限 | 统一 | 统一 | 区分慢化和死锁 | F5可预注册更高上限 |
| 重复注入 | F1-F4最终结局归因于整次运行故障序列 | 保存cluster ID | cluster bootstrap区间 | 同一运行内事件不独立 | 不得把事件直接当Bernoulli样本 |
| 跨结构比较 | 只比较同一频率口径、负载、activated定义和保护基线 | 必须 | 必须 | 不同论文指标不可直接横比 | DelayAVF/AVF/条件SDC分开 |

