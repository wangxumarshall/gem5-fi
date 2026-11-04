# FSU 覆盖状态（D2 收口 + D3 W4/F0-W3 + W5 suite + FP06-F5-W3）

> 生成时间：2026-11-03；事实刷新：F0/F1/F2/F3-W4 各三 seed、
> `FSU-FP04-F0-W3`（真实 NEON FP32 lane2）、`FSU-FP04-F0-W5`
> （PolyBench suite，每 suite seed 计 1）、`FSU-FP06-F5-W3`
> （FP06-a/b/c）与 `FSU-FP06-F5-W1`（FP06-a/b/c，W1 scalar FP）
> 均已 admitted。2026-11-04 FR07 位置审计后，`FSU-FR07-F0-W1` 的旧 3 个
> execute-post-write attempt 保留为 `PROXY_EVIDENCE`（不计认证）；该 RunID
> 已用真实 PRF-WB 数据边界 hook 重跑 seed1/2/3 并全部认证。磁盘严格计数为
> **53/519**。
> 数据源：`runs/fsu` 的 AUTHORITATIVE + audit 证据、
> `runs/fsu/COMPLETE_PROPAGATION_PATHS/INDEX.json`、
> `IMPLEMENTATION_MATRIX.json`、`W4-RATE-V1.md`、`F3-MULTIFAULT-GATE.md`。
> `runs/fsu-gates/` 下的门禁证据**不计入** seed 完成数；W5 suite 的
> component run 也不计 seed。

## 1. seed_completion

| 项 | 值 |
|---|---:|
| 已完成合格 seed | **53 / 519** |
| seed-complete RunID | **17 / 173**（F0/F1/F2/F3-W4、`FSU-FP04-F0-W1/W3/W5/W6`、`FSU-FP06-F5-W1/W3/W4/W5/W6`、`FSU-FR03-F5-W5/W6`，均 3/3；suite seed 的 component 只计 1） |
| 部分完成 RunID | **1 / 173**（`FSU-FR03-F5-W3` 2/3） |
| PROXY_EVIDENCE（保留的旧 attempt） | **3**（`FSU-FR07-F0-W1` execute-post-write；已由真实 hook seed 取代认证） |
| 其余 157 个 RunID | 0/3 |

> **活跃范围裁决（2026-11-03）**：ACTIVE = F0/F5。源注册表仍为
> 173 RunID / 519 seed（历史视图 53/519，17 个 RunID 3/3）；当前活跃范围
> 为 **80 RunID / 240 seed**，其中已完成 **44 seed / 14 RunID**（F0-W1、
> F0-W3、F0-W4、F0-W5、F0-W6、FP06-F5-W1、FP06-F5-W3、FP06-F5-W4、
> FP06-F5-W5、FP06-F5-W6、FR03-F5-W5、FR03-F5-W6）。F1–F4 为
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
| F0 | **9 seed / 3 RunID** | 短 W4 3/3；F0-W1/W3/W5/W6 各 3/3；FR07-F0-W1 的旧 3 个 execute-post-write attempt 保留为 PROXY_EVIDENCE；当前 3 seed 已用真实 PRF-WB hook 重新认证 |
| F1 | **3/3** | rate 语义已实现（1,000,000 ±50%）；W4-rate-v1；seed1（1/1）、seed2（2/2）、seed3（1/1）正式完成，fault `full`、audit PASS |
| F2 | **3/3** | rate 语义已实现（100,000 ±50%）；W4-rate-v1；seed1（21/21）、seed2（22/22）、seed3（19/19）正式完成，全部 fault `full`、audit PASS |
| F3 | **3/3** | rate 语义已实现（10,000 ±50%）；W4-rate-v1；seed1（206/206）、seed2（202/202）、seed3（210/210）正式完成，全部 fault `full`、audit PASS |
| F4 | 0/3 | DEFERRED_BY_USER（burst 语义不在当前活跃范围） |
| F5 | **23 seed / 8 RunID** | `FSU-FP06-F5-W3`（FP32 lane2）与 `FSU-FP06-F5-W1`（scalar FP32/FP64）各 3/3；FP06-a SA0 / FP06-b SA1 / FP06-c fixed mantissa 已认证；FP06-d MISSING；FP06-F5-W4 3/3（W4-rate-v1，SDC）、FP06-F5-W5 3/3（五程序 F5 suite，15 component 只计 3 seed，SDC）、FR03-F5-W5/W6 各 3/3（FR03 suite，5/3 component 只计 3 seed）；FR03-F5-W3 2/3（seed3 protocol deviation）；FP06-F5-W6 3/3（SVD/FFT/sparse suite，SDC）；FR03-F5-W5/W6 各 3/3。F5 共 23 seed / 8 RunID，不受 FR07 F0 代理排除影响 |

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

### 3.1 F5 子模型（FP06/FR03）

| 子模型/RunID | 状态 |
|---|---|
| FP06-a（结果位 SA0） | **已认证**：`FSU-FP06-F5-W3` seed1，mask `0x80000000`，16,384 exposures |
| FP06-b（结果位 SA1） | **已认证**：`FSU-FP06-F5-W3` seed2，mask `0x80000000`，16,384 exposures |
| FP06-c（固定 mantissa） | **已认证**：`FSU-FP06-F5-W3` seed3，mask `0x007f8000`，16,384 exposures |
| FP06-d（partial-product proxy） | **MISSING**：gem5 ARM FP 为功能级模型，无部分积注入点；不得用最终结果位冒充 |
| FP06-F5-W1 | **COMPLETE_3_OF_3**：FP06-a FP32 sign SA0、FP06-b FP64 sign SA1、FP06-c FP32 fixed mantissa SA0；每 seed eligible 41,216、exposures 40,192、terminal=full、oracle=SDC、audit certified |
| FP06-F5-W4 | **COMPLETE_3_OF_3**：W4-rate-v1，真实 census 1,310,723，每 seed exposures 1,309,699、activated 130,814/1,132,901/1,300,553，SDC/full/audit.ok |
| FP06-F5-W5 | **COMPLETE_3_OF_3**：suite gate 5/5 PASS；正式 suite seed1/2/3 均 5/5 component admitted、suite audit ok；15 component 只计 3 seed |
| FP06-F5-W6 | **COMPLETE_3_OF_3**：SVD/FFT/sparse suite gate 3/3 PASS；正式 seed1/2/3 各 3/3 component admitted；9 component 只计 3 seed |
| FR03-F5-W3 | **COMPLETE_3_OF_3**：L5 commit/squash/first-impact、runner 显式 CHAOSPhysReg 路径与容器级生命周期测试已落地；gate `runs/fsu-gates/F5-FR03-W3-GATE-v3/` PASS（78,022 写/151,749 读、2,046 commits、1 squash）；正式 seed1/2/3 audit.ok |
| FR03-F5-W5/W6 | **COMPLETE_3_OF_3**：suite gate 5/5 与 3/3 PASS；正式 seed1/2/3 各 component admitted、suite audit ok；W3 仍为 2/3，不借 W3 证据 |

## 4. workload_coverage

| W-ID | 身份 | 状态 |
|---|---|---|
| W4 | REAL（短 W4 + W4-rate-v1） | 短 W4：F0 3/3；W4-rate-v1：F1/F2/F3 均 3/3 |
| W1 | REAL（`w1_fp_scalar_probe`） | **部分覆盖**：F0-W1 3/3（B0-core，FP32 scalar sign）；workload 自身执行 FP64、NaN/Inf/±0/subnormal、4 舍入、FPSR/FPCR，但未逐 seed 注入；FPCR trap/异常恢复在 SE 中 N/A |
| W2 | NO_TRUE_ARTIFACT | 未覆盖（缺 FP/NEON fan-out、双源非交换、ready 竞争） |
| W3 | PARTIAL | 仅 32-bit lane |
| W5 | PARTIAL | gemm/2mm/lu/cholesky/jacobi-2d（2mm 已 vendored）；`FSU-FP04-F0-W5` suite 3/3，每 suite seed 计 1；PolyBench 全集/其他规模未覆盖 |
| W6 | REAL | SVD + FFT + 真实稀疏 CG（非 SpMV）；F0-W6 与 F5-W6 各 3/3 suite seed，逐元素 oracle |
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
| 30 模型逐模型行为测试 | 未齐全（FSU 测试基线 314 passed，覆盖编排/链/rate/F5/vec-stuck/矩阵，但不等于 30 模型逐模型全覆盖） |
| F1/F2/F3 正式三 seed | **全部完成 3/3**（F1-W4、F2-W4、F3-W4） |
