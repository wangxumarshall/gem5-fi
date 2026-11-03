# FSU 覆盖状态（D2 收口 + D3 W4 批次与 F0-W3）

> 生成时间：2026-11-03；D3 更新：F0/F1/F2/F3-W4 各三 seed 与
> `FSU-FP04-F0-W3`（真实 NEON FP32 lane2）均已 admitted（15/519）。
> 数据源：`runs/fsu` 的 AUTHORITATIVE 证据、
> `IMPLEMENTATION_MATRIX.json`、`W4-RATE-V1.md`、`F3-MULTIFAULT-GATE.md`。
> `runs/fsu-gates/` 下的门禁证据**不计入** seed 完成数。

## 1. seed_completion

| 项 | 值 |
|---|---:|
| 已完成合格 seed | **18 / 519** |
| seed-complete RunID | **6 / 173**（W4 四个：F0/F1/F2/F3-W4；`FSU-FP04-F0-W3`；`FSU-FP04-F0-W1`（B0-core），均 3/3） |
| 部分完成 RunID | **0 / 173** |
| 其余 167 个 RunID | 0/3 |

> **活跃范围裁决（2026-11-03）**：ACTIVE = F0/F5。源注册表仍为
> 173 RunID / 519 seed（历史视图 18/519，6 个 RunID 3/3）；当前活跃范围
> 为 **80 RunID / 240 seed**，其中已完成 **9 seed / 3 RunID**。F1–F4 为
> **DEFERRED_BY_USER**（不是失败/缺失/删除）；F1/F2/F3-W4 的历史完成标为
> **HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE**，不追溯改标。详见
> `configs/fsu/ACTIVE_SCOPE.json`、`docs/gem5-fi/fsu/ACTIVE_SCOPE.md`
> 与 `INDEX.json` 的 `active_scope` 段。
>
> 频率批次（F0/F1/F2/F3-W4，12 个 seed）的总审计见
> `docs/gem5-fi/fsu/FP04-W4-FREQUENCY-CLOSEOUT.md`。
> 字段/FP32/NEON lane 的门禁与 `FSU-FP04-F0-W3` 正式试点见
> `docs/gem5-fi/fsu/FP04-FIELD-LANE-GATE-CLOSEOUT.md`；
> `FSU-FP04-F0-W1`（真实 W1 workload + 指令级 decode + B0-core）见
> `docs/gem5-fi/fsu/FP04-W1-B0-CLOSEOUT.md`。

## 2. frequency_coverage（限 `FSU-FP04-*-W4`）

| 档位 | 正式 seed | 机制/预算状态 |
|---|---|---|
| F0 | **3/3** | 已实现；短 W4 pilot 三 seed |
| F1 | **3/3** | rate 语义已实现（1,000,000 ±50%）；W4-rate-v1；seed1（1/1）、seed2（2/2）、seed3（1/1）正式完成，fault `full`、audit PASS |
| F2 | **3/3** | rate 语义已实现（100,000 ±50%）；W4-rate-v1；seed1（21/21）、seed2（22/22）、seed3（19/19）正式完成，全部 fault `full`、audit PASS |
| F3 | **3/3** | rate 语义已实现（10,000 ±50%）；W4-rate-v1；seed1（206/206）、seed2（202/202）、seed3（210/210）正式完成，全部 fault `full`、audit PASS |
| F4/F5 | 0/3 | 未按本报告实现（F4 burst / F5 stuck 不在 D2 范围） |

> F3 门禁（4 个独立 fault、逐 fault full 链）是机制证据，不是正式 seed；
> 不能计为 1/3。

## 3. submodel_coverage

| 子模型 | 状态 |
|---|---|
| FP04-c / mant_lo | 已覆盖（F0/F1/F2/F3-W4 各三 seed + F3 门禁） |
| FP04-a / sign | **部分覆盖**：`FSU-FP04-F0-W1` 3/3（B0-core，真实 FP32 scalar FMOV/FMADD/FDIV），只注入 FP32 scalar sign 位；FP64 sign 及其他精度组合未正式注入 |
| FP04-b / exp_hi, exp_lo | **未覆盖** |
| FP04-c / mant_hi, mant_mid | **未覆盖** |
| FP04-d / NEON lane result | **部分覆盖**：`FSU-FP04-F0-W3` 3/3，真实 float32x4 FMA workload，仅 32-bit lane2 的 sign 位（绝对 bit 95）；其他 lane 与字段未覆盖 |
| FP32 字段映射 | **未覆盖** |
| NEON 全 128-bit lane | **未覆盖** |

## 4. workload_coverage

| W-ID | 身份 | 状态 |
|---|---|---|
| W4 | REAL（短 W4 + W4-rate-v1） | 短 W4：F0 3/3；W4-rate-v1：F1/F2/F3 均 3/3 |
| W1 | REAL（`w1_fp_scalar_probe`） | **部分覆盖**：F0-W1 3/3（B0-core，FP32 scalar sign）；workload 自身执行 FP64、NaN/Inf/±0/subnormal、4 舍入、FPSR/FPCR，但未逐 seed 注入；FPCR trap/异常恢复在 SE 中 N/A |
| W2 | NO_TRUE_ARTIFACT | 未覆盖（缺 FP/NEON fan-out、双源非交换、ready 竞争） |
| W3 | PARTIAL | 仅 32-bit lane |
| W5 | PARTIAL | gemm/lu/cholesky/jacobi-2d；2mm 缺失 |
| W6 | PARTIAL | SVD；FFT/稀疏缺失 |
| W7 | NO_FP_ARTIFACT | 未覆盖 |
| W9 | REAL | libjpeg NEON，尚未绑定 FSU RunID |
| W0/W8/W10 | UNUSED | 173 RunID 未使用 |

## 5. overall coverage_status

**NOT_COMPLETE**。

即使 F1/F2/F3-W4 全部完成三 seed，FP04 仍不能标记 COMPLETE，因为以下仍未覆盖：

- sign（FP04-a）的 FP64 与其他精度组合；
- exp_hi / exp_lo（FP04-b）；
- mant_hi / mant_mid（FP04-c 其余字段）；
- FP32；
- NEON 全 128-bit lane；
- FP04-d lane result 的其余 lane / 字段组合；
- W1/W3/W5/W6（及其它未绑定 workload）。

## 6. 当前仍存在的实现缺口

| 缺口 | 状态 |
|---|---|
| B0 配置（ROB=40、IQ=32、3/3/3、dispatch6、8/8/8） | **B0-core 已实现并验证**（F0-W1 的 config.ini 逐项匹配）；完整 v7a_3 的 FP FUPool=2 未实现。历史 15 个 W4/W3 seed 仍为 C3-valid，不追溯改标 |
| 30 模型逐模型行为测试 | 未齐全（现有 94 项 FSU 测试覆盖编排/链/rate/矩阵） |
| F1/F2/F3 正式三 seed | **全部完成 3/3**（F1-W4、F2-W4、F3-W4） |
