# FSU 频率语义映射与 W4 可行性（D1）

> 数据源：工作簿 `5.频率与统计`（F0–F5 原文）、`7.展开执行矩阵` FP04 行、
> 试点 census 实测 `CHAOS_ELIGIBLE_COUNT=57347`。本文件只记录事实与映射，
> 不声称 F1/F2/F3 已实现。

## 1. 工作簿原文（表 5）

| 档位 | 定义（原文） | 统计单位 |
|---|---|---|
| F0 | 每次运行只注入1次；warm-up后在本模型eligible event中均匀抽样 | run-level 独立样本 |
| F1 | 平均每1,000,000个eligible events注入1次，间隔±50%抖动 | run-level cluster |
| F2 | 平均每100,000个eligible events注入1次，间隔±50%抖动 | run-level cluster |
| F3 | 平均每10,000个eligible events注入1次，间隔±50%抖动 | run-level cluster |
| F4 | 每100,000个eligible events触发一次，连续污2–4个事件或单事件±1周期 | run-level cluster |
| F5 | warm-up后第一个eligible event起到运行结束；每运行固定1 bit/字段/极性 | run-level 独立样本 |

表 5 的 FSU 注意事项列对 F0–F4 均写：
“使用 countOnly + fixed uniform ordinal；时序/多 lane 模型按 run cluster 报告”。
表 7 的 FP04 行：F0 的采样说明是“每次运行只注入1次…”，F1/F2/F3 分别是
“平均每1,000,000 / 100,000 / 10,000 个 eligible events 注入1次，间隔±50%抖动”。

## 2. 代码/runner 映射

| 档位 | 当前代码能力 | 正确实现所需 | 状态 |
|---|---|---|---|
| F0 | `maxFaults=1` + `eventsToSkip=chaos_pick_skip(seed,N)`；单次注入 | 已实现并试点验证 | **IMPLEMENTED** |
| F1 | 无 rate 模式 | countOnly 得 N；按 rate=1e6、±50% 抖动生成注入 ordinal 列表；注入器在 eligible ordinal 命中时注入；事件写 `eligible_ordinal`/`eligible_total`/`freq` | **NOT IMPLEMENTED** |
| F2 | 同上 | rate=1e5 | **NOT IMPLEMENTED** |
| F3 | 同上 | rate=1e4 | **NOT IMPLEMENTED** |
| F4 | 无 burst 模式 | rate=1e5 + 2–4 事件 burst / ±1 cycle | **NOT IMPLEMENTED** |
| F5 | `recurringStuck` 有结果侧固定 mask 代理 | 首 eligible 起永久 stuck；Vec 写路径、exposure 计数 | **PARTIAL PROXY** |

禁止只改 `--fsu_freq` 标签：manifest/事件必须记录真实 rate/ordinal/jitter，
否则同一 F0 语义被贴成 F1/F2/F3。

## 3. W4 的 eligible 预算（真实 census）

`workloads/directed/elemwise_fma_kernel` 在 C3/O3 下实测
`CHAOS_ELIGIBLE_COUNT = 57,347`（F0 pilot seed1/2/3 的 census 一致）。

| 档位 | rate | 期望注入数 = N/rate | 第一个间隔下界（0.5×rate） | W4 可行性 |
|---|---:|---:|---:|---|
| F1 | 1,000,000 | 0.0573 | 500,000 | **必然 0 次**（N < 下限） |
| F2 | 100,000 | 0.573 | 50,000 | 0 或 1 次（取决于 seed；不稳定） |
| F3 | 10,000 | 5.73 | 5,000 | 可行（约 4–6 次） |

结论：

- **FSU-FP04-F1-W4 在当前 W4 上不可能产生 activated seed**：即使间隔取下界
  500,000，也大于 N=57,347。它只能被记为 `INACTIVE / eligible_below_rate`，
  不能伪造注入或把 F0 结果换标签。
- **FSU-FP04-F2-W4** 依赖第一个间隔是否落在 50,000–57,347 的窄窗口内，
  3 个 seed 不一定都能 activated；不能保证 3/3。
- **FSU-FP04-F3-W4** 有真实可行的 multiple-injection 预算，可作为 D1 的真实
  小型门禁。

## 4. 若要真正覆盖 F1/F2-W4，需要用户裁决

可行路径（三选一，均需重新标定 workload/golden，不能静默换标签）：

1. **扩展 W4 的 ROI/重复次数**：例如让 `elemwise_fma_kernel` 循环足够多次，
   使 N ≥ 1,000,000（F1）或 ≥ 300,000（F2 稳定多注入）；需要固定输入规模、
   重新生成 ARRAYHASH/ULP golden、记录新的 workload identity 和 SHA-256。
2. **接受 F1/F2-W4 为 BLOCKED/INACTIVE**：只跑 F3-W4（D2 顺序改为 F3 先行），
   F1/F2 在 INDEX 中保持 0/3 + `eligible_below_rate`。
3. **为 F1/F2 换更大 eligible 预算的 workload**：这违反当前 D2 的“同 workload
   W4 扩展”约束，需要用户明确批准并更新工作簿/实施矩阵。

在裁决前，不会启动 F1/F2 的运行，也不会用 F0 语义冒充 F1/F2。

## 5. 下一步实现（待裁决后）

- 在 runner 中实现 `build_rate_ordinals(N, rate, jitter, seed, warmup)`；
- CHAOSFPU 增加 `injectOrdinals` 参数，在 eligible ordinal 命中时注入；
- 事件写 `eligible_ordinal`/`eligible_total`/`freq`/`rate_divisor`/`jitter_pct`；
- 合成测试覆盖：F1/F2/F3 的期望次数、间隔上下界、replay；
- F3-W4 真实小型门禁：census → ordinal 生成 → 注入 → 多 fault chain 汇总；
- F1/F2-W4 记录 `INACTIVE / eligible_below_rate`，不计入 3/3。
