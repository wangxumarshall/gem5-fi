# FR07 注入位置审计：execute-post-write 不是 PRF-WB 数据边界

> 审计日期：2026-11-04。只读源码、现有 manifest/事件流与磁盘证据；未修改
> `runs/` 中的原始日志和旧审计，未运行新的 FR07 正式 seed。
> 结论：**现实现是 PRF cell 的事后改写（post-execute），不是工作簿要求的
> “PRF 写入前修改 WB data”。三个 FR07-F0-W1 seed 保留为 PROXY_EVIDENCE，
> 不计入严格模型认证计数。**

## 1. 工作簿要求

`gem5-fi-FSU单元故障注入方案_逐RunID传播监控-03-位置x模型矩阵.md:35`：

> FR07 | FP/SIMD PRF | **FSU result→Vec PRF writeback data** | 正确结果进入
> PRF 并供全部后续消费者读取 | 单/双比特翻转 | **在PRF写入前修改1/2 bit，
> 保留FU golden result**；按 scalar/vector、lane 和字段分层

明确要求：修改发生在 PRF 写入**之前**，并且保留 FU 的正确结果。

## 2. 现实现的可复查路径与时序

| 步骤 | 位置 | 事实 |
|---|---|---|
| 1. FU 产出正确结果 | `staticInst->execute(this, traceData)`，`CHAOS/gem5/src/cpu/o3/dyn_inst.cc:360` | 指令语义执行，正确结果写入寄存器 |
| 2. 结果已进入 PRF | 同上；ARM FP/SIMD 通过 `getWritableRegOperand()` → `CPU::getWritableReg()` → `regFile.getWritableReg()` 在 execute 内直接写 PRF（`dyn_inst.hh:1230-1234`、`cpu.cc:1021-1033`） | 在本树中 execute 阶段已经写 PRF，没有独立 WB latch |
| 3. CHAOSFPU 钩子 | `dyn_inst.cc:369` → `CHAOSFPU::maybeCorrupt()`（`CHAOSFPU.cc:466`） | 在 `staticInst->execute()` 返回之后同步调用 |
| 4. 事后改写 PRF cell | `CHAOSFPU.cc:621-628` 注释原文：“post-execute (**the value is already written there**)”；`CHAOSFPU.cc:880-934` 对 VecReg 用 `getWritableReg()` 直接改，对 FloatReg 读回后 `setReg()` 重写 | 正确值曾短暂存在于 PRF；注入值是事后覆盖 |
| 5. writeback / wakeup | `CHAOS/gem5/src/cpu/o3/iew.cc:1290` 执行；同一次 `IEW::tick()` 随后 `iew.cc:1516-1530` 才 `wakeDependents()` + `scoreboard->setReg()` | 注入发生在 wakeup 之前；消费者不能在注入前读到正确值 |
| 6. squash / replay | `dyn_inst.cc:354-380` 执行期间禁止 TC squash；`IEW::executeInsts` 对已执行指令 `setExecuted()` 后送 commit | 注入值位于推测 PRF；squash 后随物理寄存器回收，重放是新动态执行 |

### 2.1 与 FP04 注入点是否相同

是。FR07 与 FP04 共用 `CHAOSFPU::maybeCorrupt()` 的同一条
`post-execute PRF destination rewrite` 路径（`CHAOSFPU.cc:880-977`），
区别只在字段/mask 与事件标签。现有 FR07 证据不能证明它比 FP04 更接近
PRF-WB 边界。

## 3. 为什么不能靠“最终数值相同”宣称等价

- 工作簿要求的是 WB **数据载荷**在写 PRF 前被修改，并保留 FU golden
  result；现实现是 PRF 已被写入后的事后 cell 覆盖。
- 时序上确实没有消费者能在注入前读到正确值（execute 与注入在同一调用内，
  wakeup 在之后的 `IEW::writebackInsts()`），但这只证明“没有观察者”，
  不证明“注入点在 WB 数据边界”。
- 现实现没有真正保留一份未被改写的 PRF/ WB 数据；`before` 字段只是日志
  记录，不是“保留 FU golden result”的硬件语义。
- 现有事件流（`runs/fsu/FSU-FR07-F0-W1/seed1/attempt-1/inject/prop_evt.txt.gz`）
  的 L0 `fault_applied` 由 `noteFaultApplied` 在事后改写点发射，事件中没有
  `injection_site`/`hook_version`/producer `writeback`/`wakeup` 证据。

因此：**位置不符合工作簿；认定为结果侧代理（unapproved proxy for the WB
boundary），不是 exact。**

## 4. 计数影响（磁盘重算，不预填）

| 视图 | 排除前 | 排除 FR07-F0-W1 三个 proxy seed 后 |
|---|---:|---:|
| 历史全量 | 50/519 seed、16/173 RunID | **47/519 seed、15/173 RunID** |
| 活跃 F0/F5 | 41/240 seed、13/80 RunID | **38/240 seed、12/80 RunID** |

- 原始 attempt、`audit.json`、`chain_report.json`、Markdown 与日志全部保留；
- 每个 seed 目录写入 `PROXY_EVIDENCE.json`，指向原 attempt，声明
  `counts_toward_completion=false`；
- `fsu_index` 将此类 seed 标为 `proxy`，不计入 admitted；若以后同一 seed
  指向新的真实 hook attempt 且审计通过，则恢复正常 admitted 计数；
- 不删除、不改名、不重写旧证据。

## 5. 后续

实现真实 PRF-WB 数据边界 hook（`injection_site=prf_wb_data`、
`hook_version=2`）：execute 前 arm，目标目的寄存器走 shadow WB 数据，
注入后再写入 PRF；增加 producer `writeback`/`wakeup` 事件与 L0–L5 证据。
通过 gate 后再重新预注册 FR07-F0-W1 三个 seed（旧 proxy attempt 保留）。
