# FSU 覆盖状态（D2 收口）

> 生成时间：2026-11-02。数据源：`runs/fsu` 的 AUTHORITATIVE 证据、
> `IMPLEMENTATION_MATRIX.json`、`W4-RATE-V1.md`、`F3-MULTIFAULT-GATE.md`。
> `runs/fsu-gates/` 下的门禁证据**不计入** seed 完成数。

## 1. seed_completion

| 项 | 值 |
|---|---:|
| 已完成合格 seed | **3 / 519** |
| seed-complete RunID | **1 / 173**（`FSU-FP04-F0-W4` = 3/3） |
| 其余 172 个 RunID | 0/3 |

## 2. frequency_coverage（限 `FSU-FP04-*-W4`）

| 档位 | 正式 seed | 机制/预算状态 |
|---|---|---|
| F0 | **3/3** | 已实现；短 W4 pilot 三 seed |
| F1 | **0/3** | rate 语义已实现（1,000,000 ±50%）；W4-rate-v1 N=2,097,155；ordinals 预注册；未运行 |
| F2 | **0/3** | rate 语义已实现（100,000 ±50%）；W4-rate-v1；ordinals 预注册；未运行 |
| F3 | **0/3** | rate 语义已实现（10,000 ±50%）；W4-rate-v1；ordinals 预注册；仅短 W4 机制门禁通过 |
| F4/F5 | 0/3 | 未按本报告实现（F4 burst / F5 stuck 不在 D2 范围） |

> F3 门禁（4 个独立 fault、逐 fault full 链）是机制证据，不是正式 seed；
> 不能计为 1/3。

## 3. submodel_coverage

| 子模型 | 状态 |
|---|---|
| FP04-c / mant_lo | 已覆盖（F0 三 seed + F3 门禁） |
| FP04-a / sign | **未覆盖** |
| FP04-b / exp_hi, exp_lo | **未覆盖** |
| FP04-c / mant_hi, mant_mid | **未覆盖** |
| FP04-d / NEON lane result | **未覆盖** |
| FP32 字段映射 | **未覆盖** |
| NEON 全 128-bit lane | **未覆盖** |

## 4. workload_coverage

| W-ID | 身份 | 状态 |
|---|---|---|
| W4 | REAL（短 W4 + W4-rate-v1） | 短 W4：F0 3/3；W4-rate-v1：golden/census 就绪，0/3 |
| W1 | NO_TRUE_ARTIFACT | 未覆盖（缺 NaN/Inf/±0/subnormal、4 舍入、FPSR/FPCR 载体） |
| W2 | NO_TRUE_ARTIFACT | 未覆盖（缺 FP/NEON fan-out、双源非交换、ready 竞争） |
| W3 | PARTIAL | 仅 32-bit lane |
| W5 | PARTIAL | gemm/lu/cholesky/jacobi-2d；2mm 缺失 |
| W6 | PARTIAL | SVD；FFT/稀疏缺失 |
| W7 | NO_FP_ARTIFACT | 未覆盖 |
| W9 | REAL | libjpeg NEON，尚未绑定 FSU RunID |
| W0/W8/W10 | UNUSED | 173 RunID 未使用 |

## 5. overall coverage_status

**NOT_COMPLETE**。

即使 F1/F2/F3-W4 未来完成三 seed，FP04 仍不能标记 COMPLETE，因为以下仍未覆盖：

- sign（FP04-a）；
- exp_hi / exp_lo（FP04-b）；
- mant_hi / mant_mid（FP04-c 其余字段）；
- FP32；
- NEON 全 128-bit lane；
- FP04-d lane result；
- W1/W3/W5/W6（及其它未绑定 workload）。

## 6. 当前仍存在的实现缺口

| 缺口 | 状态 |
|---|---|
| B0 配置（ROB=40、IQ=32、3/3/3、8/8/8） | 未实现，仍用 C3 默认 |
| 30 模型逐模型行为测试 | 未齐全（现有 94 项 FSU 测试覆盖编排/链/rate/矩阵） |
| F1/F2/F3 正式三 seed | **未启动**（用户指令：先完成门禁，不批量运行） |
