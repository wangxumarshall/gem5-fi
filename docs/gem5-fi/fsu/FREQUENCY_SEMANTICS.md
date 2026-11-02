# FSU 频率语义映射与 W4 可行性（D1）

> 注（2026-11-03）：本文为 D1 设计快照。F1/F2/F3-W4 的正式三 seed 已完成；
> 当前状态见 `COVERAGE_STATUS.md` 与 `FP04-W4-FREQUENCY-CLOSEOUT.md`。
>
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
| F1 | rate 模式已实现（D2） | rate=1e6；SplitMix64 确定性 interval ∈ [500000,1500000]；ordinal 精确命中 | **IMPLEMENTED（机制）**；正式 seed 0/3 |
| F2 | 同上 | rate=1e5；interval ∈ [50000,150000] | **IMPLEMENTED（机制）**；正式 seed 0/3 |
| F3 | 同上 | rate=1e4；interval ∈ [5000,15000] | **IMPLEMENTED（机制）**；正式 seed 0/3 |
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

结论（D1 事实，短 W4）：

- 短 W4 的 N=57,347 对 F1 必然零注入（首间隔下界 500,000 > N），对 F2 不稳定；
- F3 在短 W4 上约 4–7 次，可做机制门禁。

## 4. 用户裁决与 D2 执行（路径 1）

用户选择**路径 1：扩展 W4 的 ROI/重复次数**，不接受把 F1/F2 永久记为
INACTIVE，也不允许换标签。D2 已执行：

- 新增 **W4-rate-v1**（独立源/二进制，不覆盖短 W4）：
  `N_BASE=8192 × REPEAT=32 = 262144` 元素；countOnly 实测
  **N_eligible = 2,097,155**（≥1,500,000；不是线性推算）；
- 无注入 golden 连续 3 次 ARRAYHASH 一致：`e563e3e1...525aba`，ULP=0；
- 新二进制 SHA-256：`c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`；
- 预注册 F1/F2/F3 × seed1/2/3 的 ordinal 列表与 SHA-256：
  `configs/fsu/W4-rate-v1-ordinals.json`。

详细记录见 `docs/gem5-fi/fsu/W4-RATE-V1.md`。

## 5. D2 机制实现（已完成）

- `tools/fsu_rate_ordinals.py`：`build_rate_ordinals(N, rate, jitter_pct, seed,
  warmup)`；SplitMix64 v1；interval ∈ [ceil(0.5·rate), floor(1.5·rate)]；
  ordinal 为严格递增累加值，超过 N 停止；禁止 probability/geometric 近似；
- CHAOSFPU 新参数 `rateOrdinals`/`rateWarmup`/`fsuRateDivisor`/`fsuJitterPct`，
  按 eligible 序号精确命中；每个 fault 独立 fault_id + L0 root；
- manifest/事件记录 `rate_divisor`/`jitter_pct`/`interval`/`ordinal_index`/
  `eligible_ordinal`/`eligible_total`/`freq`；
- label-only fail-fast：F1/F2/F3 缺少 ordinals、F0 携带 rate、divisor 不符、
  probability≠1、ordinal 越界/非递增均在 runner/C++ 拒绝；
- F3 短 W4 门禁：N=57,347，4 个独立 fault、4 条独立 full 链、逐 fault
  Markdown/audit 通过（`docs/gem5-fi/fsu/F3-MULTIFAULT-GATE.md`）。

**尚未完成**：F1/F2/F3-W4 的正式三 seed。当前 seed 总数仍为 **3/519**，
覆盖状态见 `docs/gem5-fi/fsu/COVERAGE_STATUS.md`。
