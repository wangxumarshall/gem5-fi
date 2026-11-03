# F5（永久卡死）readiness 审计（2026-11-03）

> 8 个 F5 RunID：FP06-W1/W3/W4/W5/W6，FR03-W3/W5/W6。
> 结论：**0 READY**；本轮不运行任何 F5 正式 seed。

## 1. F5 定义（工作簿原文）

主方案 :171：

> F5 | 永久卡死 | warm-up 后第一个 eligible event 起到运行结束；每运行固定
> 1 bit/字段/极性 | stuck-at/固定 mask | 持久缺陷与重复暴露 |
> run-level 独立样本 | 仅正确值与卡死极性不同时 activated；按物理槽世代记暴露

- F5 **不是 rate 语义**；interval/jitter/ordinal 不适用（F1–F4 才用）。
- FP06：同一固定 mask/极性应用到每个 eligible 结果。
- FR03：一个固定 Vec phys cell（phys reg + lane + bit + SA0/SA1），
  每次写入/读出维持极性。
- 定义清晰，不需要 `BLOCKED_DEFINITION_AMBIGUOUS`。

## 2. 8 个 RunID readiness

| RunID | readiness | 主要缺口 |
|---|---|---|
| FSU-FP06-F5-W1 | PARTIAL | 缺 F5 调度、SA0/SA1；W1 workload/golden 存在；F5 事件量会超 200k 上限 |
| FSU-FP06-F5-W3 | PARTIAL | 同上；NEON 只覆盖 4×32-bit lane2，缺其他 lane/字段 |
| FSU-FP06-F5-W4 | PARTIAL | 同上；rate-v1 eligible 2,097,155，F5 全量不可审计 |
| FSU-FP06-F5-W5 | PARTIAL | 同上；W5 suite/2mm 未成立 |
| FSU-FP06-F5-W6 | PARTIAL | 同上；FFT/稀疏组件缺失 |
| FSU-FR03-F5-W3 | BLOCKED | Vec stuck 不持久、无 FSU_PROP、runner 无 CHAOSPhysReg 路径 |
| FSU-FR03-F5-W5 | BLOCKED | 同上 + W5 suite 未成立 |
| FSU-FR03-F5-W6 | BLOCKED | 同上 + W6 组件缺失 |

## 3. 代码缺口

### FP06（结果侧 stuck 代理）

- 注入位置：`DynInst::execute()` 后、写回边界，对目的 PRF 做结果侧改写。
- 已有：固定 `recurring_mask` 重复、L0–L5 FSU_PROP 发射端、中等规模
  多 fault 链（F3 206 fault 已实证）。
- 缺：
  1. F5 调度：没有“warm-up 后第一个 eligible 到结束”模式；runner 仍传
     随机 skip，C++ 仍做 probability 抽样。
  2. SA0/SA1：当前是 XOR，不是强制 0/1 极性。
  3. FP06-d partial-product proxy 未实现。
  4. 全 Vec 宽（只 128-bit）。
  5. F5 规模：`EVENT_CAP=200000`；每 eligible 一个 fault 会产生数十万事件，
     链会被判 truncated。
  6. 同一 consumer 同时消费两个 fault 时只记录第一个，F5 多 fault 会漏链。

### FR03（Vec PRF stuck）

- 已有：标量 int/float 写路径 stuck（`regfile.hh` + `setStuckTarget`）；
  Vec 一次性 RMW + `permanent_faults`。
- 缺：
  1. Vec 写路径没有 stuck mask；下一次向量写会覆盖注入位，状态不持久。
  2. `checkPermanent()` 把 Vec 索引当 int 处理，会误写 int PRF。
  3. `permanent_faults` key 无寄存器类/世代。
  4. CHAOSPhysReg 无 `notePropEvt`，无 FSU_PROP L0–L5。
  5. runner 固定 `--chaos_fpu`，没有 CHAOSPhysReg 路径。
- 因此此前的 FR03 “Vec stuck 实际未生效”结论成立；未证明持久卡死前，
  FR03-F5 不得进入正式运行。

## 4. 最小可运行候选

- `FSU-FP06-F5-W1`（REAL workload + golden）是最小候选；
  但需先实现 F5 调度、SA0/SA1、F5 manifest、census 与事件上限方案。
- 若严格保持 200k 事件上限，`FSU-FP06-F5-W3`（eligible 16,384）事件量
  可容纳，但 workload 仍只覆盖 lane2 sign。
- 在下列全部完成前，不得正式运行：F5 调度、SA0/SA1、FR03 Vec 持久化+
  PROP 链、runner 路径、F5 census、B0 manifest、多 fault 审计上限方案。

## 5. 多 fault 审计要求（F5）

- 每个 fault 独立 `fault_id`、L0 root、direct parent 链、terminal；
- 所有 fault 共享同一 mask/polarity/物理目标（FP06 同一结果字段；
  FR03 同一 phys cell + generation）；
- 只有正确值与卡死极性不同才算 activated；
- 一个 fault 的 L5 不得认证其他 fault；
- run-level oracle 与逐 fault terminal 分开；
- 必须保留 producer/affected sn、first impact/exposure。
