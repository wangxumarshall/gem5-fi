# Flight Rules — SDC 诊断规则库（版本化）

> 规则来源：方案 §7.3–§7.6（P1–P11 / N1–N10 / 置信度分级）+ §7.7 反哺
> （formal 实验 P_SDC 先验回填）。每次新增/修改规则必须 bump 版本并
> 记录实验依据（方案 7.9 要求）。

## 版本

| 版本 | 日期 | 变更 | 依据 |
|---|---|---|---|
| 1.0.0 | 2026-09-07 | 初始：P/N 规则 + 置信度 + 首批 formal 先验回填（fpu 4 位段 / lsq_fwd / prf） | t3-1-fsu-formal-gemm-double（n=384×4）；artifacts/lsq-matrix；artifacts/prf-formal |

## 诊断规则（与 sdc_diagnose.py 实现一致）

- P1 单核浓度 >60%（同构鲲鹏 920 口径）；P2 同核 ≥2 应用；P3 30 天非计划重启 ≥6（通用）/≥3（AI）；P4 高相关异常类型同核；P5 RAS 静默；P6 误诊史；P7 FA 复现 ≥70%；P8 向量 SDC；P9 NZCV 异常；P10 持续失败；P11 兄弟核共失效
- N1–N10 排除规则（任一命中即排除）；N10 铁律：单次阴性不可靠，≤30 天重访
- 置信度：HIGH = P1+P2+P3+P5+（P4/P8/P9）→ 隔离+FA+RMA；MEDIUM = P1+P2+P5 → 延长观察；LOW → 监控；EXCLUDED = 任一 N

## 实验先验回填（§7.7 item 2：单元 P_SDC → 类型加权依据）

### fpu（FSU 数据通路，CHAOSFPU v3 源读 hook，gemm_double，n=384/cell）

| 位段 | P_SDC | 95% CI | §7.3 类型关联 |
|---|---|---|---|
| sign | 0.180 | [0.145, 0.221] | 符号位破坏 → 数值符号翻转（SDC 高） |
| exp | 0.172 | [0.137, 0.213] | 指数破坏 → 量级错误 |
| mantissa | 0.136 | [0.105, 0.174] | 尾数破坏 → 精度损失（可被吸收） |
| all | 0.159 | [0.126, 0.199] | 随机单比特混合 |

> 解读：FP 单比特位段间 P_SDC 差异有限（13.6%–18.0%），sign/exp 略高
> 于 mantissa（尾数低位误差常被累加舍入吸收——与 §6.2 位谱规律一致）。

### 其他已回填单元

| 单元 | P_SDC 先验 | 依据 campaign |
|---|---|---|
| lsq_fwd（store→load 转发） | ~0.50 | artifacts/lsq-matrix（7 case × 变体） |
| prf（寄存器堆 cell） | ~0.10 | artifacts/prf-formal（X3 位段网格） |

### 诚实边界

- 全部 P_SDC 为 gem5 O3 条件概率，非产品 FIT（无原始器件故障率）
- SE 模式：无 MMU 翻译（TLB/PTW/AGU 需 FS）
- 单机数据未第二机复现 → "single-machine, unconfirmed"
