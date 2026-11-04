# F0 readiness 排序与已知缺陷复核（2026-11-04）

> 范围：源注册表 **173 RunID** 中的 **72 个 F0 RunID**；排除已完成的 5 个 F0 RunID（`FSU-FP04-F0-W1/W3/W4/W5/W6`，各 3 seed）以及 F1–F4（DEFERRED_BY_USER）。
> 剩余 **64 个 F0 RunID** 全部在本文排序。数据源：`runids.json`（sha256 `dbdb5962…ae5`）、`IMPLEMENTATION_MATRIX.json`、`CHAOS/gem5/src` 真实代码、`workloads/` 与 suite golden。
> **2026-11-04 更新**：`FSU-FR07-F0-W1` 的旧 attempt 是
> execute-post-write 代理（保留为 `PROXY_EVIDENCE`）；该 RunID 已用真实
> PRF-WB 数据边界 hook v2 重跑 seed1/2/3 并全部认证，因此回到 completed，
> 不再列入 remaining。详见 `FR07-PRF-WB-POSITION-AUDIT.md` 与
> `FR07-PRF-WB-HOOK.md`。
> 代码存在 ≠ 已认证；本文只评估 readiness 与缺陷，不产生任何正式 seed，不修改 runids.json。

## 0. 结论摘要

- 真正具备 **注入点 + FSU L0–L5 全链 + REAL workload + 可判定 oracle** 的剩余 F0 模型只有 CHAOSFPU 结果侧一族：`FR07`（结果→PRF WB）、`FP05`（结果 lane 群/短突发）、`FP07`（FMA 字段加权结果代理）。`FP02` 的故障位置是**输入操作数总线**，结果侧 XOR 是错位代理；`FP08` 的 roundingSub 路径未接链。
- **严格排序前 3** 是 `FSU-FR07-F0-W3`, `FSU-FR07-F0-W5`, `FSU-FP07-F0-W4`；三者共用 CHAOSFPU 结果侧注入器，但语义分别是 exact / exact / proxy。作为三个独立试点，推荐 **三个不同模型族**：`FSU-FR07-F0-W3`, `FSU-FP07-F0-W4`, `FSU-FP05-F0-W6`。
- 已知缺陷复核（修复前基线）：**FQ08-b 仍存在**、**FP08 suppressed_count 仍未输出**、**FQ08-c 延迟唤醒 squash 风险仍存在**；**PRF 身份/generation 为“部分”**（FR03 正确，FR01/FR02 未接链且 FR02 双 bit 可能碰撞）。
- 下一试点建议 **`FSU-FR07-F0-W3`**：真实 PRF-WB 数据边界 hook v2 已在
  `FSU-FR07-F0-W1` 上通过 gate 并完成 3 个正式 seed；W3 可按同一 hook 与
  预注册的 lane mask 推进。旧 W1 proxy attempt 仍不能外推。

## 1. 评分口径

`score = injector + chain + workload − cost − defect`：

- **注入点**：`exact=3`（代码与模型语义一致）、`partial=2`（主体存在但子模型/字段/几何不完整）、`proxy=2`（有明确行为代理、非真实内部点）、`wrong=1`（代码存在但注入位置/域不符）、`none=0`。
- **L0–L5 链**：`full=3`（该注入器真实发射 fault root→L5）、`partial=1`（同注入器只有别的模式能发链，当前模式不发）、`none=0`。
- **Workload/oracle**：`real=3`（真实源/二进制/golden，ARRAYHASH 或逐元素/容差）、`partial=2`（真实产物但身份/覆盖面不完整）、`none=1`（NO_TRUE_ARTIFACT / NO_FP_ARTIFACT，无逐边或 golden）。
- **成本**：`S=0 / M=0.5 / L=1`；**已知缺陷罚分**：`0 / 0.5 / 1`。
- 分层：T1 ≥7；T2 5–6.9；T3 3–4.9；T4 1–2.9；T5 <1。

### 1.1 F0 语义核对要点

- 频率口径：F0 = 每次 run 只注入 1 次（`maxFaults=1`），warm-up 后在本模型 eligible event 中均匀抽样；单/双 bit 或换值，**没有 F5 的持续极性**。`polarity` 只在 F5 permanent-stuck 语义中出现，F0 不应把 polarity 当成注入参数。
- 当前可用的 F0 单 bit 随机路径：`CHAOSFPU`（默认在 lane 内均匀抽 1 bit，`CHAOSFPU.cc:765–768`）、`CHAOSIQ`（tag 单 bit，`CHAOSIQ.cc:587–592`）、`CHAOSPhysReg`（`bitsToChange=1` + 随机 mask）。多 bit 路径：`CHAOSFPU faultMask`（显式 mask，`buildExplicitMask` 校验 lane 域）、`CHAOSIQ tag_bitflip2`（两个不同 bit）、`CHAOSPhysReg bitsToChange=2`（但随机 mask 可碰撞，见 §4.2）。
- 语义偏差必须显式标注：`fmaWeighted`（FP07-a 允许的代理）、`roundingSub`（FP08-a 代理）、`recurringStuck`（FP05 的 per-event 重复，不是 burst）、结果侧 XOR 用于 FP01/FP02 输入操作数模型属于**错位**。
- L0–L5 工具：`tools/fsu_prop_fields.py` 定义事件 kind→层映射（`fault_applied`/`fault_installed` 为 L0 根，`commit`/`arch_state`/`oracle_diff`/`first_impact` 为 L5 见证，`chain_end` 不占层），`tools/fsu_chain_check.py` 做单祖先直接 parent 链审计。注入器不发射这些事件时，链审计无法认证。

## 1.1 代理分类（2026-11-04，严格区分，不作为认证捷径）

| 分类 | 当前条目 | 认证含义 |
|---|---|---|
| exact implemented | FR07 W1/W3/W5（真实 PRF-WB 数据边界 hook v2，已正式 seed）；FR01/FR02 瞬态单/双 bit（W1 gate 通过，尚无正式 seed） | 只有已通过对应 gate/正式 seed 的条目才进入计数；FR01/FR02 仍为 0/3 |
| partial implemented | FP05（`recurringStuck` 同 mask 每 event 重复，**不是**工作簿的 2–4 event burst；缺 burst_id/ordinal）；FP07（`fmaWeighted` 行为代理，真实 FMA 中间值不可达） | 只能做 gate/partial 证据，不得直接扩正式计数 |
| workbook explicitly allowed proxy | FP07 的最终结果字段加权（工作簿原文允许“字段加权结果代理”），但必须逐事件标注 proxy | 可在明确标注下进入 gate；正式认证需预注册且不得冒充硬件中间值 |
| unapproved proxy / wrong site | FP01/FP02/FP03 结果侧 XOR（工作簿位置是输入操作数/op-select）；FP08 rounding_sub（1-ULP 代理） | 不得用结果侧链认证这些模型 |
| missing | FP09/FP10/FQ03/FQ05/FQ07/FQ09/FQ10/FR04/FR05/FR06/FR08/FR09/FR10 等 | 0 认证 |

> FP05 的 “2–4 event burst” 与 FP07 的 “partial-product 中间值” 均未实现；
> 现有 recurring/weighted 路径只能作为 proxy/partial，不能因为“代码存在 +
> 能发链”就当作模型匹配。

## 2. 排序表（67 个剩余 F0 RunID）

图例：注入点 ✅ exact / ◐ partial / △ proxy 或错位 / ✗ missing；链 ✅ full / ◐ partial / ✗ none；workload ✅ REAL / ◐ PARTIAL / ✗ 无真实产物。

“主要缺口 / 已知缺陷”列：只有明确写出“仍存在/碰撞/错位”等的是已定位缺陷；其余仅表示能力缺口，不虚构缺陷。

| # | RunID | 模型/负载 | 注入点 | 语义 | L0–L5 | Workload / oracle | 成本/风险 | 分 | 主要缺口 / 已知缺陷 |
|---:|---|---|---|---|---|---|---|---:|---|
| 1 | `FSU-FP07-F0-W4` | FP07/W4 | △ proxy | 代理 | ✅ full | ✅ REAL | S/中 | 7.5 | CHAOSFPU `fmaWeighted` mant85/exp10/sign5 行为代理 + 全链；真实 FMA 中间值/partial row 不可达，未限定 FMA opClass |
| 2 | `FSU-FP07-F0-W6` | FP07/W6 | △ proxy | 代理 | ✅ full | ✅ REAL | S/中 | 7.5 | CHAOSFPU `fmaWeighted` mant85/exp10/sign5 行为代理 + 全链；真实 FMA 中间值/partial row 不可达，未限定 FMA opClass |
| 3 | `FSU-FP05-F0-W6` | FP05/W6 | ◐ partial | 部分 | ✅ full | ✅ REAL | M/中 | 7.0 | CHAOSFPU `recurringStuck` 同 mask 重复；缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id |
| 4 | `FSU-FP07-F0-W5` | FP07/W5 | △ proxy | 代理 | ✅ full | ◐ PARTIAL | S/中 | 6.5 | CHAOSFPU `fmaWeighted` mant85/exp10/sign5 行为代理 + 全链；真实 FMA 中间值/partial row 不可达，未限定 FMA opClass |
| 5 | `FSU-FR01-F0-W1` | FR01/W1 | ✅ exact | 瞬态 | ◐ partial | ✅ REAL | M/中 | 6.5 | 真实 Vec 瞬态单 bit；L0/L1/overwrite 已发射，seed2 真实写覆盖终止；缺 L2/L5 完整覆盖与正式 3 seed |
| 6 | `FSU-FR02-F0-W1` | FR02/W1 | ✅ exact | 瞬态 | ◐ partial | ✅ REAL | M/中 | 6.5 | 两个 bit 必互异（碰撞 fail closed）；L0/L1/overwrite 已发射；缺 L2/L5 完整覆盖与正式 3 seed |
| 7 | `FSU-FP05-F0-W3` | FP05/W3 | ◐ partial | 部分 | ✅ full | ◐ PARTIAL | M/中 | 6.0 | CHAOSFPU `recurringStuck` 同 mask 重复；缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id |
| 8 | `FSU-FP05-F0-W5` | FP05/W5 | ◐ partial | 部分 | ✅ full | ◐ PARTIAL | M/中 | 6.0 | CHAOSFPU `recurringStuck` 同 mask 重复；缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id |
| 9 | `FSU-FP08-F0-W1` | FP08/W1 | ◐ partial | 部分 | ✗ none | ✅ REAL | M/中 | 4.0 | CHAOSFPU `roundingSub` 1-ULP 代理真实；该路径提前 return，不发射 PROP；`suppressed_count` 未输出；runner 无 fpsr 开关 |
| 10 | `FSU-FR01-F0-W3` | FR01/W3 | ◐ partial | 部分 | ◐ partial | ◐ PARTIAL | M/中 | 4.0 | CHAOSPhysReg vec `bit_flip` 真实；但 bit_flip 路径不 arm、不发射 FSU PROP，无 generation/consumer 证据；仅 ≤64-bit lane，无 128-bit/FP 字段分层 |
| 11 | `FSU-FR01-F0-W5` | FR01/W5 | ◐ partial | 部分 | ◐ partial | ◐ PARTIAL | M/中 | 4.0 | CHAOSPhysReg vec `bit_flip` 真实；但 bit_flip 路径不 arm、不发射 FSU PROP，无 generation/consumer 证据；仅 ≤64-bit lane，无 128-bit/FP 字段分层 |
| 12 | `FSU-FR02-F0-W3` | FR02/W3 | ◐ partial | 部分 | ◐ partial | ◐ PARTIAL | M/中 | 4.0 | CHAOSPhysReg `bitsToChange=2`；random mask 可能把两个 bit 抽成同一个（实际 1 bit）；跨 lane/字段对缺失；无 PROP |
| 13 | `FSU-FR02-F0-W5` | FR02/W5 | ◐ partial | 部分 | ◐ partial | ◐ PARTIAL | M/中 | 4.0 | CHAOSPhysReg `bitsToChange=2`；random mask 可能把两个 bit 抽成同一个（实际 1 bit）；跨 lane/字段对缺失；无 PROP |
| 14 | `FSU-FQ01-F0-W5` | FQ01/W5 | ◐ partial | 部分 | ✗ none | ◐ PARTIAL | M/中 | 3.5 | CHAOSIQ `tag_bitflip`(targetClass=vec) 真实改源 tag；缺 src0/src1 子模型选择、producer_sn/ready 证据；无 FSU PROP 根 |
| 15 | `FSU-FQ02-F0-W5` | FQ02/W5 | ◐ partial | 部分 | ✗ none | ◐ PARTIAL | M/中 | 3.5 | CHAOSIQ `tag_bitflip2` 选两个不同 tag bit；缺相邻/非相邻/跨子字段分类、target writer/首读者证据；无 FSU PROP 根 |
| 16 | `FSU-FQ04-F0-W5` | FQ04/W5 | ◐ partial | 部分 | ✗ none | ◐ PARTIAL | M/中 | 3.0 | `ready_early` 可作用 Vec；`ready_never/_event` 硬编码拒绝 FP/vector（CHAOSIQ.cc:745）；无 stale-ready/PROP |
| 17 | `FSU-FP01-F0-W1` | FP01/W1 | △ wrong-site | 错位 | ✗ none | ✅ REAL | L/高 | 2.5 | CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点） |
| 18 | `FSU-FP01-F0-W4` | FP01/W4 | △ wrong-site | 错位 | ✗ none | ✅ REAL | L/高 | 2.5 | CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点） |
| 19 | `FSU-FP02-F0-W1` | FP02/W1 | △ wrong-site | 错位 | ✗ none | ✅ REAL | L/高 | 2.5 | FP02 的故障位置是 **FSU 输入操作数总线**（同/邻/跨 lane 双 bit）；CHAOSFPU `faultMask` 只改**结果**目的 PRF，属错位代理；矩阵的 "结果侧粗粒度多位 XOR" 正是该代理，不能算输入操作数故障 |
| 20 | `FSU-FP03-F0-W1` | FP03/W1 | △ wrong-site | 错位 | ✗ none | ✅ REAL | L/高 | 2.5 | 无 FSU op-select 换值；仅 CHAOSDecode 解码级 opcode swap 越界代理，且无 FSU 链 |
| 21 | `FSU-FQ01-F0-W2` | FQ01/W2 | ◐ partial | 部分 | ✗ none | ✗ 无真实产物 | M/中 | 2.5 | CHAOSIQ `tag_bitflip`(targetClass=vec) 真实改源 tag；缺 src0/src1 子模型选择、producer_sn/ready 证据；无 FSU PROP 根；W2 本身无 true artifact |
| 22 | `FSU-FQ02-F0-W2` | FQ02/W2 | ◐ partial | 部分 | ✗ none | ✗ 无真实产物 | M/中 | 2.5 | CHAOSIQ `tag_bitflip2` 选两个不同 tag bit；缺相邻/非相邻/跨子字段分类、target writer/首读者证据；无 FSU PROP 根；W2 本身无 true artifact |
| 23 | `FSU-FQ06-F0-W1` | FQ06/W1 | △ wrong-site | 错位 | ✗ none | ✅ REAL | L/高 | 2.5 | `dispatch_misroute` 仅 IntAlu↔IntMult；FP/SIMD add↔mul pipe、compatible FU index 未实现；无 PROP |
| 24 | `FSU-FQ08-F0-W5` | FQ08/W5 | ◐ partial | 部分 | ✗ none | ◐ PARTIAL | M/高 | 2.5 | wake_omit/src_ready_bitflip/wake_phase 真实；无 PROP；FQ08-b 无 victim 仍计数，FQ08-c 延迟事件不随 squash 取消 |
| 25 | `FSU-FP08-F0-W7` | FP08/W7 | ◐ partial | 部分 | ✗ none | ✗ 无真实产物 | M/中 | 2.0 | CHAOSFPU `roundingSub` 1-ULP 代理真实；该路径提前 return，不发射 PROP；`suppressed_count` 未输出；runner 无 fpsr 开关；W7 本身无 FP artifact/golden |
| 26 | `FSU-FP09-F0-W9` | FP09/W9 | ✗ missing | 缺失 | ✗ none | ✅ REAL | L/高 | 2.0 | 无 lane swap/rotate、元素宽度替代、mask 移位、新旧拼接注入 |
| 27 | `FSU-FQ04-F0-W2` | FQ04/W2 | ◐ partial | 部分 | ✗ none | ✗ 无真实产物 | M/中 | 2.0 | `ready_early` 可作用 Vec；`ready_never/_event` 硬编码拒绝 FP/vector（CHAOSIQ.cc:745）；无 stale-ready/PROP；W2 本身无 true artifact |
| 28 | `FSU-FR05-F0-W1` | FR05/W1 | ✗ missing | 缺失 | ✗ none | ✅ REAL | L/高 | 2.0 | 无 Vec 读端口输出 1-bit 翻转注入；regfile 只有只读计数 |
| 29 | `FSU-FP01-F0-W3` | FP01/W3 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点） |
| 30 | `FSU-FP01-F0-W5` | FP01/W5 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点） |
| 31 | `FSU-FP02-F0-W3` | FP02/W3 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | FP02 的故障位置是 **FSU 输入操作数总线**（同/邻/跨 lane 双 bit）；CHAOSFPU `faultMask` 只改**结果**目的 PRF，属错位代理；矩阵的 "结果侧粗粒度多位 XOR" 正是该代理，不能算输入操作数故障 |
| 32 | `FSU-FP02-F0-W5` | FP02/W5 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | FP02 的故障位置是 **FSU 输入操作数总线**（同/邻/跨 lane 双 bit）；CHAOSFPU `faultMask` 只改**结果**目的 PRF，属错位代理；矩阵的 "结果侧粗粒度多位 XOR" 正是该代理，不能算输入操作数故障 |
| 33 | `FSU-FP03-F0-W5` | FP03/W5 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | 无 FSU op-select 换值；仅 CHAOSDecode 解码级 opcode swap 越界代理，且无 FSU 链 |
| 34 | `FSU-FQ06-F0-W3` | FQ06/W3 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | `dispatch_misroute` 仅 IntAlu↔IntMult；FP/SIMD add↔mul pipe、compatible FU index 未实现；无 PROP |
| 35 | `FSU-FQ06-F0-W5` | FQ06/W5 | △ wrong-site | 错位 | ✗ none | ◐ PARTIAL | L/高 | 1.5 | `dispatch_misroute` 仅 IntAlu↔IntMult；FP/SIMD add↔mul pipe、compatible FU index 未实现；无 PROP |
| 36 | `FSU-FQ08-F0-W2` | FQ08/W2 | ◐ partial | 部分 | ✗ none | ✗ 无真实产物 | M/高 | 1.5 | wake_omit/src_ready_bitflip/wake_phase 真实；无 PROP；FQ08-b 无 victim 仍计数，FQ08-c 延迟事件不随 squash 取消；W2 本身无 true artifact |
| 37 | `FSU-FP09-F0-W3` | FP09/W3 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 lane swap/rotate、元素宽度替代、mask 移位、新旧拼接注入 |
| 38 | `FSU-FP09-F0-W5` | FP09/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 lane swap/rotate、元素宽度替代、mask 移位、新旧拼接注入 |
| 39 | `FSU-FP10-F0-W5` | FP10/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 completion early/late/drop/duplicate、result/dest swap、stale completion 注入 |
| 40 | `FSU-FQ03-F0-W3` | FQ03/W3 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 src0↔src1 配对交换；现有 tag_swap 是换成随机 producer，不是配对交换；无 PROP |
| 41 | `FSU-FQ07-F0-W5` | FQ07/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 ready-list rank/age 注入；seqNum 只用于日志/tag_stuck |
| 42 | `FSU-FQ09-F0-W5` | FQ09/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | `noteIqDeparture` 只读；无 issue→execute early/late/drop/duplicate/stale slot 注入 |
| 43 | `FSU-FQ10-F0-W5` | FQ10/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 FU index 替代 / busy↔free / release lost 注入；无 FUPool 证据 |
| 44 | `FSU-FR04-F0-W5` | FR04/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 Vec 读地址/tag 替代到另一 active-ready Vec phys reg 的注入 API |
| 45 | `FSU-FR05-F0-W3` | FR05/W3 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 Vec 读端口输出 1-bit 翻转注入；regfile 只有只读计数 |
| 46 | `FSU-FR05-F0-W5` | FR05/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 Vec 读端口输出 1-bit 翻转注入；regfile 只有只读计数 |
| 47 | `FSU-FR06-F0-W3` | FR06/W3 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 Vec 读端口多位/跨 lane 翻转注入 |
| 48 | `FSU-FR06-F0-W5` | FR06/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 Vec 读端口多位/跨 lane 翻转注入 |
| 49 | `FSU-FR08-F0-W5` | FR08/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 Vec 写目标 tag 替代/交换注入 |
| 50 | `FSU-FR09-F0-W5` | FR09/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | 无 write-enable/ready/wakeup 原子性（lost/early/late/split）注入 |
| 51 | `FSU-FR10-F0-W3` | FR10/W3 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | gem5 O3 无 bypass/forwarding mux hook，未实现 partial-lane merge 注入 |
| 52 | `FSU-FR10-F0-W5` | FR10/W5 | ✗ missing | 缺失 | ✗ none | ◐ PARTIAL | L/高 | 1.0 | gem5 O3 无 bypass/forwarding mux hook，未实现 partial-lane merge 注入 |
| 53 | `FSU-FP10-F0-W2` | FP10/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 completion early/late/drop/duplicate、result/dest swap、stale completion 注入；W2 本身无 true artifact |
| 54 | `FSU-FP10-F0-W7` | FP10/W7 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 completion early/late/drop/duplicate、result/dest swap、stale completion 注入；W7 本身无 FP artifact/golden |
| 55 | `FSU-FQ03-F0-W2` | FQ03/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 src0↔src1 配对交换；现有 tag_swap 是换成随机 producer，不是配对交换；无 PROP；W2 本身无 true artifact |
| 56 | `FSU-FQ05-F0-W2` | FQ05/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 valid/issued/squashed 注入 API；IQ slot 生命周期/occupancy 守恒无证据；W2 本身无 true artifact |
| 57 | `FSU-FQ05-F0-W7` | FQ05/W7 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 valid/issued/squashed 注入 API；IQ slot 生命周期/occupancy 守恒无证据；W7 本身无 FP artifact/golden |
| 58 | `FSU-FQ07-F0-W2` | FQ07/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 ready-list rank/age 注入；seqNum 只用于日志/tag_stuck；W2 本身无 true artifact |
| 59 | `FSU-FQ09-F0-W2` | FQ09/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | `noteIqDeparture` 只读；无 issue→execute early/late/drop/duplicate/stale slot 注入；W2 本身无 true artifact |
| 60 | `FSU-FQ10-F0-W2` | FQ10/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 FU index 替代 / busy↔free / release lost 注入；无 FUPool 证据；W2 本身无 true artifact |
| 61 | `FSU-FR04-F0-W2` | FR04/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 Vec 读地址/tag 替代到另一 active-ready Vec phys reg 的注入 API；W2 本身无 true artifact |
| 62 | `FSU-FR08-F0-W2` | FR08/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 Vec 写目标 tag 替代/交换注入；W2 本身无 true artifact |
| 63 | `FSU-FR09-F0-W2` | FR09/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | 无 write-enable/ready/wakeup 原子性（lost/early/late/split）注入；W2 本身无 true artifact |
| 64 | `FSU-FR10-F0-W2` | FR10/W2 | ✗ missing | 缺失 | ✗ none | ✗ 无真实产物 | L/高 | 0.0 | gem5 O3 无 bypass/forwarding mux hook，未实现 partial-lane merge 注入；W2 本身无 true artifact |

> 认证状态：本表 64 个 RunID 的 `seed_completion` 都是 0/3；所有“注入点存在”都只是代码事实，**不是正式认证**。已完成的 F0 项是 `FSU-FP04-F0-W1/W3/W4/W5/W6` 与 `FSU-FR07-F0-W1/W3/W5`（各 3/3；FR07 使用真实 PRF-WB hook v2）。

### 2.1 注入点代码证据（grep `CHAOS/gem5/src`）

- **CHAOSFPU（结果侧，FR07/FP05/FP07，以及错位代理 FP01/FP02/FP08）**：`CHAOSFPU.cc:466` `maybeCorrupt`，目的 PRF 注入在 880–977，`noteFaultApplied` 1084，consumer execute 1709，commit L5 1855；`dyn_inst.cc:369/377`；`commit.cc:1349`。这是本树唯一对结果侧发射完整 L0–L5 的注入器。
- **CHAOSPhysReg（Vec PRF，FR01/FR02；FR03 已认证）**：`processFault` 1043；Vec 写入 1227–1313；`FaultType::BitFlip` 只 XOR（1291–1294），只有 `StuckAtZero/One` 才 `armVecStuck`（1275/1286）并 `noteVecStuckInstalled`（1303）；Vec 写后重施在 `maybeReapplyStuck` 538；container key 在 `regfile.hh:289`；L5 在 `commit.cc:1356` / `rob.cc:380`。
- **CHAOSIQ（Issue Queue，FQ01/02/04/08）**：`maybeCorruptTag` 312（tag_swap/tag_bitflip/tag_bitflip2/tag_stuck/tag_stale_read），`maybeReadyEarly` 666，`shouldSuppressReadyMark` 742（745 拒绝 FP/vector），`shouldOmitWake` 107 / `shouldWrongSourceWake` 149 / `shouldDelayWake` 192；hook 在 `inst_queue.cc:694/706/946/1035/1128–1145/1257–1279`。
- **CHAOSDecode（FP03 错位代理）**：`maybeCorrupt` 443 / `maybeCorruptEncoding` 497；hook 在 `rename.cc:1203–1204` 与 `fetch.cc:1257–1259`。只有解码级 opcode/dest 改值，不是 FSU op-select。
- **CHAOSExec**：`maybeCorrupt` 76–191 只接受 `IntAluOp/IntMultOp/IntDivOp` 且有 Int dest，不覆盖 FSU FP/SIMD。
- **FSU PROP 发射器只有** `CHAOSFPU`、`CHAOSPhysReg`（仅 FR03 permanent-stuck 路径）、`CHAOSAddrPath`、`CHAOSLSQFwd`。`CHAOSIQ`/`CHAOSDecode`/`CHAOSExec`/`CHAOSRenameMap`/`CHAOSFreeList`/`CHAOSROB` 均无 `notePropEvt`，因此这些模型即使有注入点也无法过 L0–L5 链审计。

**矩阵陈旧性修正**：`IMPLEMENTATION_MATRIX.json` 在 FR07/FP07/FP05/FP02 的 `missing_hooks` 中仍列有“PROP 事件”，但真实代码 `CHAOSFPU` 已经发射 `fault_applied→carrier_state→operand_read→execute→prf_writeback→consumer→commit`（`CHAOSFPU.cc:1084/1709/1855`, `commit.cc:1349`）。本表按代码把结果侧链记为 full。例外：`FP08` 的 `roundingSub` 分支在 `CHAOSFPU.cc:663–696` 提前 `return`，不会走到 `noteFaultApplied`（976），所以 FP08 链仍为 none；`FP02` 的链虽是 full，但注入位置是结果而不是输入操作数总线，不能用来认证 FP02。

### 2.2 分层统计

| 层 | 数量 | RunID |
|---|---:|---|
| T1 | 3 | `FSU-FP07-F0-W4`, `FSU-FP07-F0-W6`, `FSU-FP05-F0-W6` |
| T2 | 5 | `FSU-FP07-F0-W5`, `FSU-FP05-F0-W3`, `FSU-FP05-F0-W5`, `FSU-FR01-F0-W1`, `FSU-FR02-F0-W1` |
| T3 | 8 | `FSU-FP08-F0-W1`, `FSU-FR01-F0-W3`, `FSU-FR01-F0-W5`, `FSU-FR02-F0-W3`, `FSU-FR02-F0-W5`, `FSU-FQ01-F0-W5`, `FSU-FQ02-F0-W5`, `FSU-FQ04-F0-W5` |
| T4 | 36 | `FSU-FP01-F0-W1`, `FSU-FP01-F0-W4`, `FSU-FP02-F0-W1`, `FSU-FP03-F0-W1`, `FSU-FQ01-F0-W2`, `FSU-FQ02-F0-W2`, `FSU-FQ06-F0-W1`, `FSU-FQ08-F0-W5`, `FSU-FP08-F0-W7`, `FSU-FP09-F0-W9`, `FSU-FQ04-F0-W2`, `FSU-FR05-F0-W1`, `FSU-FP01-F0-W3`, `FSU-FP01-F0-W5`, `FSU-FP02-F0-W3`, `FSU-FP02-F0-W5`, `FSU-FP03-F0-W5`, `FSU-FQ06-F0-W3`, `FSU-FQ06-F0-W5`, `FSU-FQ08-F0-W2`, `FSU-FP09-F0-W3`, `FSU-FP09-F0-W5`, `FSU-FP10-F0-W5`, `FSU-FQ03-F0-W3`, `FSU-FQ07-F0-W5`, `FSU-FQ09-F0-W5`, `FSU-FQ10-F0-W5`, `FSU-FR04-F0-W5`, `FSU-FR05-F0-W3`, `FSU-FR05-F0-W5`, `FSU-FR06-F0-W3`, `FSU-FR06-F0-W5`, `FSU-FR08-F0-W5`, `FSU-FR09-F0-W5`, `FSU-FR10-F0-W3`, `FSU-FR10-F0-W5` |
| T5 | 12 | `FSU-FP10-F0-W2`, `FSU-FP10-F0-W7`, `FSU-FQ03-F0-W2`, `FSU-FQ05-F0-W2`, `FSU-FQ05-F0-W7`, `FSU-FQ07-F0-W2`, `FSU-FQ09-F0-W2`, `FSU-FQ10-F0-W2`, `FSU-FR04-F0-W2`, `FSU-FR08-F0-W2`, `FSU-FR09-F0-W2`, `FSU-FR10-F0-W2` |

### 2.3 Workload / golden / hash 证据

| W-ID | 源 | 二进制 sha256（前 16） | golden / oracle |
|---|---|---|---|
| W1 | `workloads/directed/w1_fp_scalar_probe.c` | `c2b8a553bd44c87f` | `ffe18c8279bf419d…f2eba183`；ARRAYHASH 64-hex + ULP（`configs/fsu/FSU-FP04-F0-W1.json`） |
| W3 | `workloads/directed/neon_fp32_lane_kernel.c` | `d8b01bc0ac140f43` | `cb66197d92c7656b…bce8c2e`；ARRAYHASH+ULP+LANEHASH0..3 |
| W4 | `workloads/directed/elemwise_fma_kernel.c` | `80e633a0cd4b8f64` | `ced113fdd122842d…f43e7`；exact ARRAYHASH，toler=0（`FSU-FP04-F0-W4-GATE.json`） |
| W5 | `workloads/ooo/polybench/` 五程序 | suite hash `7282decf461243a8…a7493` | 逐元素 golden `configs/fsu/suites/polybench-fp-v1/golden/*.bin`（manifest sha256 `74f0e6460b6ac56b…a0db6`）；suite 内各程序 16-hex FINAL |
| W6 | SVD/FFT/sparse 三程序 | suite hash `7af52ddcbc1ad03d…d43adf1a` | 逐元素 golden `configs/fsu/suites/w6-fp-v1/golden/*.bin`（manifest sha256 `add7343f598141ed…25dd4`） |
| W2 | `workloads/ooo/dep_chain/dep_chain_vec` | `1016473f55bdfb12` | 仅 `b1e661a247b95774` 16-hex checksum；**非逐边 oracle** |
| W7 | `workloads/directed/divzero_loop_kernel` | `76e662bd9aec3561` | **无 golden**（NO_FP_ARTIFACT） |
| W9 | `workloads/ooo/libjpeg/jpeg_wl` | `b1b0068dbc9d6c5a` | `c712f8f6fb9e21ec`；FINAL 16-hex（解码 RGB FNV-1a） |

> W2/W7 的 `NO_TRUE_ARTIFACT` / `NO_FP_ARTIFACT` 是真实缺口，不是“文件丢失”；W5/W6 golden 文件实际存在，`polybench-fp-v1.json` 里 `element_oracle_status: pending_generation` 的旧注释与磁盘不一致，正式认证仍以已生成的 golden/manifest 与 seed 审计为准。

## 3. 推荐候选

### 3.1 严格排序前 3（同族，仅供比较）

1. `FSU-FR07-F0-W3`（FR07/W3，8.0 分）：CHAOSFPU 结果侧注入 + L0–L5；在真实
   PRF-WB hook 落地前仍沿用 execute-post-write 代理，不能认证。
2. `FSU-FR07-F0-W5`（FR07/W5，8.0 分）：同上；W5 为五程序 suite。
3. `FSU-FP07-F0-W4`（FP07/W4，7.5 分）：`fmaWeighted` 行为代理。
   `FSU-FR07-F0-W1` 的旧 attempt 保留为 `PROXY_EVIDENCE`；当前 3 seed 已由
   真实 PRF-WB hook 重新认证。

### 3.2 最接近真实端到端运行的前 3 个独立候选（推荐）

#### 1) `FSU-FR07-F0-W3` — 首选（真实 PRF-WB hook 落地后）

> W1 的真实 hook 门禁已通过并完成 3 seed；旧 proxy attempt 仍保留但不再
> 用于认证，也不能直接外推到 W3/W5。

- **为什么最接近**：`CHAOSFPU` 的结果侧 L0–L5 链已在本树真实存在
  （`CHAOSFPU.cc:1084/1709/1855`，`commit.cc:1349`，`dyn_inst.cc:369/377`）；
  W3 `neon_fp32_lane_kernel` 是真实的 4×32-bit lane workload，已有
  ARRAYHASH + LANEHASH golden。W3 的 lane 语义必须在真实 PRF-WB hook 下
  才能认证。
- **缺口**：当前共享注入器仍是 execute-post-write，不是工作簿要求的
  “PRF 写入前修改 WB data”；必须先实现真实 hook 并通过 W1 门禁，再为
  W3 新建预注册 manifest，把 `fsu_model=FR07`、`submodel` 写对。
- **成本/风险**：S / 低（前提是真实 hook 先通过 gate）。

#### 2) `FSU-FP07-F0-W4` — 第二（与 W6 并列）

- **为什么**：`FP07` 的定义明确允许“字段加权的最终结果代理，或丢失/复制部分积、错位对齐累加数；代理与真实信号分栏”。`fmaWeighted` 已实现 mant 85%/exp 10%/sign 5% 的 FP07-a 行为代理，并复用 CHAOSFPU 全链；W4 `elemwise_fma_kernel` 是 REAL workload，exact ARRAYHASH（toler=0），已有 F0-W4 的 gate/seed 先例。
- **缺口**：gem5 是功能级 FP 模型，真实 FMA partial product/中间值不可达；未限定 FMA opClass，partial row drop/dup/align shift（FP07-b/c）未实现。必须作为“代理”报告，不能冒充硬件中间值。`FSU-FP07-F0-W6` 分数相同，但 W6 suite 引入 suite 聚合复杂度，故 W4 优先。
- **成本/风险**：S / 中（语义代理风险）。

#### 3) `FSU-FP05-F0-W6` — 第三

- **为什么**：`FP05` 的故障位置是 NEON 结果 lane 群/短突发，`CHAOSFPU` 的 `recurringStuck` 确实作用在结果目的 PRF，并复用全链；W6 suite 是 REAL workload（SVD/FFT/sparse，逐元素 golden）。
- **缺口**：当前 `recurringStuck` 是“同一 mask 对每个 eligible event 重复”，不是“2–4 个连续 eligible 结果的 run-level burst”；缺 `burst_id`/`burst_ordinal`，且每个 event 各自 `fault_id`。相邻 lane/cross-lane MBU 也未实现。必须先补 burst 语义/预注册口径（成本 M），否则只能报“同 mask 重复”，不能认证 FP05。
- **成本/风险**：M / 中。

### 3.3 次优观察（不建议先做）

- `FSU-FR01-F0-W1`：注入点真实、W1 REAL，但 vec `bit_flip` 不发射 FSU PROP（只有 FR03 permanent-stuck 路径发），没有 L0 根就无法过链审计；需要新的链接线，成本 M。
- `FSU-FP02-F0-W1`：矩阵写着“结果侧粗粒度多位 XOR”，但 FP02 的 workbook 位置是**输入操作数总线**（同 lane 相邻/非相邻、跨 lane 双 bit）；CHAOSFPU 只改结果，属错位代理。若要做 FP02，应先在操作数读取路径加 A/B/C hook，而不是复用结果侧 mask。
- `FSU-FP08-F0-W1`：`roundingSub` 代理真实，但该分支提前 `return`，不发射任何 PROP，且 `suppressed_count` 无输出；需先修链/计数，成本 M。

## 4. 四个已知缺陷复核（按真实代码，不假定仍存在）

### 4.1 FQ08-b：无 victim 时仍计注入 — **已修复（待 gem5 gate 实证）**

**修复后事实**：`shouldWrongSourceWake` 只做 candidate/attempted 判定，不再增加
`faults_injected_count`、不再返回 true；真正的施加移到
`CHAOSIQ::noteTagWake`，只有当 dependent 存在、未 squash/未 issue 且存在另一个
未就绪源槽时才 `markSrcRegReady`、`iq_counts.applied++` 并消耗 `maxFaults`；
无 victim 只增加 `iq_counts.no_victim`。`attempted / eligible / applied /
activated / no_victim` 分开输出在 `CHAOS_IQ_COUNTS`。
host 证据：`tests/unit/chaos_iq_lifecycle_test.cc`（正例/负例/预算）与
`tests/test_chaos_iq_lifecycle_cpp.py` 8 passed。gem5 gate 尚待主 agent 运行。

**最小测试**：`injectionMode=src_ready_bitflip, probability=1, maxFaults=1,
targetClass=vec, fpOnly=1`；无 victim 负例应 `applied=0, faults_injected: 0`，
有 victim 正例应 `applied=1, faults_injected: 1`。

### 4.2 FR03 以外 PRF 模型的身份与 generation — **已修复（待正式 seed）**

**FR03（已认证，正确）**：永久 key 是 `reg_class + phys_index + lane/bit/mask + polarity`，generation 只作分配/暴露身份。`regfile.hh:289–293` 的 `isVecStuckTarget` 只匹配 class+index；`noteRegFreed` 在 `regfile.hh:268–272` 递增 `flat_generation`；`reapplyVecStuck`（318–329）在每次 Vec 写后重施；`clearPermanentFaults`（297–301）只在 run-end（`CHAOSPhysReg.cc:532–534`）调用。free/realloc/squash 都不清除，generation 变化重启 exposure 链（`CHAOSPhysReg.cc:329–386`）。host 单测 `tests/unit/chaos_physreg_generation_test.cc` 已覆盖。

**FR01/FR02（本轮修复）**：`FaultType::BitFlip` 的 Vec 路径改为真实瞬态注入
（`chaos_vec_transient.hh`）：FR01 单 bit；FR02 用无放回抽样保证两个不同 bit，
显式 mask popcount/几何不符时 fail closed 且不消费故障；128-bit 域内只改目标位；
事件包含 `phys_reg`、`reg_generation`、`bit_indices`、`lane_width/lane_offset`、
`before/after`；真实写覆盖发射 `overwrite`（L1, `phys_cell_rewritten`）并终止
故障，不安装永久 stuck。host 单测 36 项与 gem5 W1 gate 均通过（FR01 seed2 /
FR02 seed2 的 overwrite、FR02 碰撞负例 fail closed）。仍缺 L2 consumer/L5
commit 的完整覆盖与正式 3 seed。

### 4.3 FP08 suppressed_count 与 roundingSub 早退路径 — **已修复（待 gem5 gate 实证）**

**修复后事实**：`fpsr_suppress` 分支现在分别累计 `fpsr_attempted/applied/
suppressed`，退出时输出 `CHAOS_FPSR_ATTEMPTED/APPLIED/SUPPRESSED/REASON`
并发射 `suppress` 事件；`rounding_sub` 早退路径在完成 1-ULP 改动后调用
`noteFaultApplied`，产生真实 L0/L1，并输出 `CHAOS_ROUNDING_ATTEMPTED/
APPLIED`。两者均标注为代理边界（`injection_site=fpsr_suppress_proxy` /
`rounding_sub_one_ulp_proxy`），在 gate 闭合前不产生正式认证。
host 侧源码检查通过；gem5 gate 尚待主 agent 运行。

**最小测试**：fpsr_suppress 运行退出应满足
`attempted == suppressed` 且 `applied == attempted`；rounding_sub 运行应
出现 `fault_applied` 根与 `CHAOS_ROUNDING_APPLIED>=1`。

### 4.4 FQ08-c：squash / 延迟唤醒风险 — **已修复（待 gem5 gate 实证）**

**修复后事实**：`wake_phase` 不再依赖 `inst_queue.cc` 的
`o3::DelayedWakeEvent`；`CHAOSIQ` 自有 `DelayedWake` 事件，持有
`DynInstPtr` + seq/tid + 每个目的物理寄存器的 generation 快照。fire 前经
`chaos_iq_lifecycle` 状态机校验：squash → `ignore_squashed`，槽位复用/
generation 不符 → `ignore_generation`，身份不符 → `ignore_identity`；只有
全部匹配才再次唤醒。squash 后旧事件不会再作用于新占用者。
host 证据：`tests/unit/chaos_iq_lifecycle_test.cc` 覆盖 squash、复用、
身份不符与正常事件；`tests/test_chaos_iq_lifecycle_cpp.py` 8 passed。
gem5 squash gate 尚待主 agent 运行。

**最小可测路径**：非正式 out-root 运行
`workloads/ooo/branch_mispred/branch_mispred`，`wake_phase` +
`phaseOffset` 跨过 squash 窗口；预期出现 `IGNORED reason=ignore_squashed`
（或 `ignore_generation`）且无 `dependGraph` assert，exit 0。

## 5. 下一试点与最小验证

**建议下一试点：`FSU-FP07-F0-W4`**（FR07 的 W1/W3/W5 已在真实 PRF-WB hook 下认证；FP07 是独立模型族，仍为行为代理）。顺序：

1. 模型行为 host 测试：目的 PRF XOR、mask 精确、`fault_applied` 根与 L2–L5 发射存在；
2. 非正式 gate（`/tmp`，不写 `runs/fsu`，不计 seed）：1 个 seed，chain audit + oracle 分类；
3. gate PASS 后由主 agent 预注册正式 seed1/2/3。

**最小验证命令**（需先创建 FR07 manifest；不产生正式 seed）：

```bash
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FR07-F0-W3-HOOK-LANE-GATE.json --seed 1 --out-root /tmp/fsu-fr07-w3-gate
```

或直接最小 gem5 观察（非正式）：

```bash
# build/ARM/gem5.opt --outdir=/tmp/fr07 configs/se/ooo_proxy.py \
#   --cmd workloads/directed/w1_fp_scalar_probe --cpu O3 \
#   --chaos_fpu --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 \
#   --fpu_max_faults 1 --fpu_rng_seed 1 --chaos_propagation \
#   --prop_run_id FSU-FR07-F0-W1 --prop_sample_run_id s1
```

本任务配套只读测试：`python3 -m pytest tests/test_fsu_f0_readiness.py -q`。

## 6. 机器可读块（供测试读取）

<!-- F0_READINESS_JSON_BEGIN -->
{
  "schema": "fsu-f0-readiness-v1",
  "date": "2026-11-04",
  "active_frequency": "F0",
  "source_registry_count": 173,
  "f0_total": 72,
  "completed_f0": [
    "FSU-FP04-F0-W1",
    "FSU-FP04-F0-W3",
    "FSU-FP04-F0-W4",
    "FSU-FP04-F0-W5",
    "FSU-FP04-F0-W6",
    "FSU-FR07-F0-W1",
    "FSU-FR07-F0-W3",
    "FSU-FR07-F0-W5"
  ],
  "remaining_f0_count": 64,
  "scoring": "injector(exact3/partial2/proxy2/wrong1/none0)+chain(full3/partial1/none0)+workload(real3/partial2/none1)-cost(S0/M0.5/L1)-known_defect_penalty",
  "rows": [
    {
      "runid": "FSU-FP07-F0-W4",
      "model_id": "FP07",
      "load_id": "W4",
      "rank": 1,
      "score": 7.5,
      "tier": "T1",
      "injector": "proxy",
      "chain": "full",
      "workload": "real",
      "cost": "S",
      "risk": "medium",
      "gap": "CHAOSFPU `fmaWeighted` mant85/exp10/sign5 行为代理 + 全链；真实 FMA 中间值/partial row 不可达，未限定 FMA opClass"
    },
    {
      "runid": "FSU-FP07-F0-W6",
      "model_id": "FP07",
      "load_id": "W6",
      "rank": 2,
      "score": 7.5,
      "tier": "T1",
      "injector": "proxy",
      "chain": "full",
      "workload": "real",
      "cost": "S",
      "risk": "medium",
      "gap": "CHAOSFPU `fmaWeighted` mant85/exp10/sign5 行为代理 + 全链；真实 FMA 中间值/partial row 不可达，未限定 FMA opClass"
    },
    {
      "runid": "FSU-FP05-F0-W6",
      "model_id": "FP05",
      "load_id": "W6",
      "rank": 3,
      "score": 7.0,
      "tier": "T1",
      "injector": "partial",
      "chain": "full",
      "workload": "real",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSFPU `recurringStuck` 同 mask 重复；缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id"
    },
    {
      "runid": "FSU-FP07-F0-W5",
      "model_id": "FP07",
      "load_id": "W5",
      "rank": 4,
      "score": 6.5,
      "tier": "T2",
      "injector": "proxy",
      "chain": "full",
      "workload": "partial",
      "cost": "S",
      "risk": "medium",
      "gap": "CHAOSFPU `fmaWeighted` mant85/exp10/sign5 行为代理 + 全链；真实 FMA 中间值/partial row 不可达，未限定 FMA opClass"
    },
    {
      "runid": "FSU-FR01-F0-W1",
      "model_id": "FR01",
      "load_id": "W1",
      "rank": 5,
      "score": 6.5,
      "tier": "T2",
      "injector": "exact",
      "chain": "partial",
      "workload": "real",
      "cost": "M",
      "risk": "medium",
      "gap": "真实 Vec 瞬态单 bit；L0/L1/overwrite 已发射，seed2 真实写覆盖终止；缺 L2 consumer/L5 commit 完整覆盖与正式 3 seed"
    },
    {
      "runid": "FSU-FR02-F0-W1",
      "model_id": "FR02",
      "load_id": "W1",
      "rank": 6,
      "score": 6.5,
      "tier": "T2",
      "injector": "exact",
      "chain": "partial",
      "workload": "real",
      "cost": "M",
      "risk": "medium",
      "gap": "两个 bit 必互异（碰撞 fail closed）；L0/L1/overwrite 已发射；缺 L2/L5 完整覆盖与正式 3 seed"
    },
    {
      "runid": "FSU-FP05-F0-W3",
      "model_id": "FP05",
      "load_id": "W3",
      "rank": 7,
      "score": 6.0,
      "tier": "T2",
      "injector": "partial",
      "chain": "full",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSFPU `recurringStuck` 同 mask 重复；缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id"
    },
    {
      "runid": "FSU-FP05-F0-W5",
      "model_id": "FP05",
      "load_id": "W5",
      "rank": 8,
      "score": 6.0,
      "tier": "T2",
      "injector": "partial",
      "chain": "full",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSFPU `recurringStuck` 同 mask 重复；缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id"
    },
    {
      "runid": "FSU-FP08-F0-W1",
      "model_id": "FP08",
      "load_id": "W1",
      "rank": 9,
      "score": 4.0,
      "tier": "T3",
      "injector": "partial",
      "chain": "none",
      "workload": "real",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSFPU `roundingSub` 1-ULP 代理真实；该路径提前 return，不发射 PROP；`suppressed_count` 未输出；runner 无 fpsr 开关"
    },
    {
      "runid": "FSU-FR01-F0-W3",
      "model_id": "FR01",
      "load_id": "W3",
      "rank": 10,
      "score": 4.0,
      "tier": "T3",
      "injector": "partial",
      "chain": "partial",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSPhysReg vec `bit_flip` 真实；但 bit_flip 路径不 arm、不发射 FSU PROP，无 generation/consumer 证据；仅 ≤64-bit lane，无 128-bit/FP 字段分层"
    },
    {
      "runid": "FSU-FR01-F0-W5",
      "model_id": "FR01",
      "load_id": "W5",
      "rank": 11,
      "score": 4.0,
      "tier": "T3",
      "injector": "partial",
      "chain": "partial",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSPhysReg vec `bit_flip` 真实；但 bit_flip 路径不 arm、不发射 FSU PROP，无 generation/consumer 证据；仅 ≤64-bit lane，无 128-bit/FP 字段分层"
    },
    {
      "runid": "FSU-FR02-F0-W3",
      "model_id": "FR02",
      "load_id": "W3",
      "rank": 12,
      "score": 4.0,
      "tier": "T3",
      "injector": "partial",
      "chain": "partial",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSPhysReg `bitsToChange=2`；random mask 可能把两个 bit 抽成同一个（实际 1 bit）；跨 lane/字段对缺失；无 PROP"
    },
    {
      "runid": "FSU-FR02-F0-W5",
      "model_id": "FR02",
      "load_id": "W5",
      "rank": 13,
      "score": 4.0,
      "tier": "T3",
      "injector": "partial",
      "chain": "partial",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSPhysReg `bitsToChange=2`；random mask 可能把两个 bit 抽成同一个（实际 1 bit）；跨 lane/字段对缺失；无 PROP"
    },
    {
      "runid": "FSU-FQ01-F0-W5",
      "model_id": "FQ01",
      "load_id": "W5",
      "rank": 14,
      "score": 3.5,
      "tier": "T3",
      "injector": "partial",
      "chain": "none",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSIQ `tag_bitflip`(targetClass=vec) 真实改源 tag；缺 src0/src1 子模型选择、producer_sn/ready 证据；无 FSU PROP 根"
    },
    {
      "runid": "FSU-FQ02-F0-W5",
      "model_id": "FQ02",
      "load_id": "W5",
      "rank": 15,
      "score": 3.5,
      "tier": "T3",
      "injector": "partial",
      "chain": "none",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSIQ `tag_bitflip2` 选两个不同 tag bit；缺相邻/非相邻/跨子字段分类、target writer/首读者证据；无 FSU PROP 根"
    },
    {
      "runid": "FSU-FQ04-F0-W5",
      "model_id": "FQ04",
      "load_id": "W5",
      "rank": 16,
      "score": 3.0,
      "tier": "T3",
      "injector": "partial",
      "chain": "none",
      "workload": "partial",
      "cost": "M",
      "risk": "medium",
      "gap": "`ready_early` 可作用 Vec；`ready_never/_event` 硬编码拒绝 FP/vector（CHAOSIQ.cc:745）；无 stale-ready/PROP"
    },
    {
      "runid": "FSU-FP01-F0-W1",
      "model_id": "FP01",
      "load_id": "W1",
      "rank": 17,
      "score": 2.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点）"
    },
    {
      "runid": "FSU-FP01-F0-W4",
      "model_id": "FP01",
      "load_id": "W4",
      "rank": 18,
      "score": 2.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点）"
    },
    {
      "runid": "FSU-FP02-F0-W1",
      "model_id": "FP02",
      "load_id": "W1",
      "rank": 19,
      "score": 2.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "FP02 的故障位置是 **FSU 输入操作数总线**（同/邻/跨 lane 双 bit）；CHAOSFPU `faultMask` 只改**结果**目的 PRF，属错位代理；矩阵的 \"结果侧粗粒度多位 XOR\" 正是该代理，不能算输入操作数故障"
    },
    {
      "runid": "FSU-FP03-F0-W1",
      "model_id": "FP03",
      "load_id": "W1",
      "rank": 20,
      "score": 2.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "无 FSU op-select 换值；仅 CHAOSDecode 解码级 opcode swap 越界代理，且无 FSU 链"
    },
    {
      "runid": "FSU-FQ01-F0-W2",
      "model_id": "FQ01",
      "load_id": "W2",
      "rank": 21,
      "score": 2.5,
      "tier": "T4",
      "injector": "partial",
      "chain": "none",
      "workload": "none",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSIQ `tag_bitflip`(targetClass=vec) 真实改源 tag；缺 src0/src1 子模型选择、producer_sn/ready 证据；无 FSU PROP 根；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FQ02-F0-W2",
      "model_id": "FQ02",
      "load_id": "W2",
      "rank": 22,
      "score": 2.5,
      "tier": "T4",
      "injector": "partial",
      "chain": "none",
      "workload": "none",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSIQ `tag_bitflip2` 选两个不同 tag bit；缺相邻/非相邻/跨子字段分类、target writer/首读者证据；无 FSU PROP 根；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FQ06-F0-W1",
      "model_id": "FQ06",
      "load_id": "W1",
      "rank": 23,
      "score": 2.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "`dispatch_misroute` 仅 IntAlu↔IntMult；FP/SIMD add↔mul pipe、compatible FU index 未实现；无 PROP"
    },
    {
      "runid": "FSU-FQ08-F0-W5",
      "model_id": "FQ08",
      "load_id": "W5",
      "rank": 24,
      "score": 2.5,
      "tier": "T4",
      "injector": "partial",
      "chain": "none",
      "workload": "partial",
      "cost": "M",
      "risk": "high",
      "gap": "wake_omit/src_ready_bitflip/wake_phase 真实；无 PROP；FQ08-b 无 victim 仍计数，FQ08-c 延迟事件不随 squash 取消"
    },
    {
      "runid": "FSU-FP08-F0-W7",
      "model_id": "FP08",
      "load_id": "W7",
      "rank": 25,
      "score": 2.0,
      "tier": "T4",
      "injector": "partial",
      "chain": "none",
      "workload": "none",
      "cost": "M",
      "risk": "medium",
      "gap": "CHAOSFPU `roundingSub` 1-ULP 代理真实；该路径提前 return，不发射 PROP；`suppressed_count` 未输出；runner 无 fpsr 开关；W7 本身无 FP artifact/golden"
    },
    {
      "runid": "FSU-FP09-F0-W9",
      "model_id": "FP09",
      "load_id": "W9",
      "rank": 26,
      "score": 2.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "无 lane swap/rotate、元素宽度替代、mask 移位、新旧拼接注入"
    },
    {
      "runid": "FSU-FQ04-F0-W2",
      "model_id": "FQ04",
      "load_id": "W2",
      "rank": 27,
      "score": 2.0,
      "tier": "T4",
      "injector": "partial",
      "chain": "none",
      "workload": "none",
      "cost": "M",
      "risk": "medium",
      "gap": "`ready_early` 可作用 Vec；`ready_never/_event` 硬编码拒绝 FP/vector（CHAOSIQ.cc:745）；无 stale-ready/PROP；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FR05-F0-W1",
      "model_id": "FR05",
      "load_id": "W1",
      "rank": 28,
      "score": 2.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "real",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读端口输出 1-bit 翻转注入；regfile 只有只读计数"
    },
    {
      "runid": "FSU-FP01-F0-W3",
      "model_id": "FP01",
      "load_id": "W3",
      "rank": 29,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点）"
    },
    {
      "runid": "FSU-FP01-F0-W5",
      "model_id": "FP01",
      "load_id": "W5",
      "rank": 30,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "CHAOSFPU 仅结果侧 XOR；A/B/C 操作数注入缺失（错注入点）"
    },
    {
      "runid": "FSU-FP02-F0-W3",
      "model_id": "FP02",
      "load_id": "W3",
      "rank": 31,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "FP02 的故障位置是 **FSU 输入操作数总线**（同/邻/跨 lane 双 bit）；CHAOSFPU `faultMask` 只改**结果**目的 PRF，属错位代理；矩阵的 \"结果侧粗粒度多位 XOR\" 正是该代理，不能算输入操作数故障"
    },
    {
      "runid": "FSU-FP02-F0-W5",
      "model_id": "FP02",
      "load_id": "W5",
      "rank": 32,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "FP02 的故障位置是 **FSU 输入操作数总线**（同/邻/跨 lane 双 bit）；CHAOSFPU `faultMask` 只改**结果**目的 PRF，属错位代理；矩阵的 \"结果侧粗粒度多位 XOR\" 正是该代理，不能算输入操作数故障"
    },
    {
      "runid": "FSU-FP03-F0-W5",
      "model_id": "FP03",
      "load_id": "W5",
      "rank": 33,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 FSU op-select 换值；仅 CHAOSDecode 解码级 opcode swap 越界代理，且无 FSU 链"
    },
    {
      "runid": "FSU-FQ06-F0-W3",
      "model_id": "FQ06",
      "load_id": "W3",
      "rank": 34,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "`dispatch_misroute` 仅 IntAlu↔IntMult；FP/SIMD add↔mul pipe、compatible FU index 未实现；无 PROP"
    },
    {
      "runid": "FSU-FQ06-F0-W5",
      "model_id": "FQ06",
      "load_id": "W5",
      "rank": 35,
      "score": 1.5,
      "tier": "T4",
      "injector": "wrong",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "`dispatch_misroute` 仅 IntAlu↔IntMult；FP/SIMD add↔mul pipe、compatible FU index 未实现；无 PROP"
    },
    {
      "runid": "FSU-FQ08-F0-W2",
      "model_id": "FQ08",
      "load_id": "W2",
      "rank": 36,
      "score": 1.5,
      "tier": "T4",
      "injector": "partial",
      "chain": "none",
      "workload": "none",
      "cost": "M",
      "risk": "high",
      "gap": "wake_omit/src_ready_bitflip/wake_phase 真实；无 PROP；FQ08-b 无 victim 仍计数，FQ08-c 延迟事件不随 squash 取消；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FP09-F0-W3",
      "model_id": "FP09",
      "load_id": "W3",
      "rank": 37,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 lane swap/rotate、元素宽度替代、mask 移位、新旧拼接注入"
    },
    {
      "runid": "FSU-FP09-F0-W5",
      "model_id": "FP09",
      "load_id": "W5",
      "rank": 38,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 lane swap/rotate、元素宽度替代、mask 移位、新旧拼接注入"
    },
    {
      "runid": "FSU-FP10-F0-W5",
      "model_id": "FP10",
      "load_id": "W5",
      "rank": 39,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 completion early/late/drop/duplicate、result/dest swap、stale completion 注入"
    },
    {
      "runid": "FSU-FQ03-F0-W3",
      "model_id": "FQ03",
      "load_id": "W3",
      "rank": 40,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 src0↔src1 配对交换；现有 tag_swap 是换成随机 producer，不是配对交换；无 PROP"
    },
    {
      "runid": "FSU-FQ07-F0-W5",
      "model_id": "FQ07",
      "load_id": "W5",
      "rank": 41,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 ready-list rank/age 注入；seqNum 只用于日志/tag_stuck"
    },
    {
      "runid": "FSU-FQ09-F0-W5",
      "model_id": "FQ09",
      "load_id": "W5",
      "rank": 42,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "`noteIqDeparture` 只读；无 issue→execute early/late/drop/duplicate/stale slot 注入"
    },
    {
      "runid": "FSU-FQ10-F0-W5",
      "model_id": "FQ10",
      "load_id": "W5",
      "rank": 43,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 FU index 替代 / busy↔free / release lost 注入；无 FUPool 证据"
    },
    {
      "runid": "FSU-FR04-F0-W5",
      "model_id": "FR04",
      "load_id": "W5",
      "rank": 44,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读地址/tag 替代到另一 active-ready Vec phys reg 的注入 API"
    },
    {
      "runid": "FSU-FR05-F0-W3",
      "model_id": "FR05",
      "load_id": "W3",
      "rank": 45,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读端口输出 1-bit 翻转注入；regfile 只有只读计数"
    },
    {
      "runid": "FSU-FR05-F0-W5",
      "model_id": "FR05",
      "load_id": "W5",
      "rank": 46,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读端口输出 1-bit 翻转注入；regfile 只有只读计数"
    },
    {
      "runid": "FSU-FR06-F0-W3",
      "model_id": "FR06",
      "load_id": "W3",
      "rank": 47,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读端口多位/跨 lane 翻转注入"
    },
    {
      "runid": "FSU-FR06-F0-W5",
      "model_id": "FR06",
      "load_id": "W5",
      "rank": 48,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读端口多位/跨 lane 翻转注入"
    },
    {
      "runid": "FSU-FR08-F0-W5",
      "model_id": "FR08",
      "load_id": "W5",
      "rank": 49,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 写目标 tag 替代/交换注入"
    },
    {
      "runid": "FSU-FR09-F0-W5",
      "model_id": "FR09",
      "load_id": "W5",
      "rank": 50,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "无 write-enable/ready/wakeup 原子性（lost/early/late/split）注入"
    },
    {
      "runid": "FSU-FR10-F0-W3",
      "model_id": "FR10",
      "load_id": "W3",
      "rank": 51,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "gem5 O3 无 bypass/forwarding mux hook，未实现 partial-lane merge 注入"
    },
    {
      "runid": "FSU-FR10-F0-W5",
      "model_id": "FR10",
      "load_id": "W5",
      "rank": 52,
      "score": 1.0,
      "tier": "T4",
      "injector": "none",
      "chain": "none",
      "workload": "partial",
      "cost": "L",
      "risk": "high",
      "gap": "gem5 O3 无 bypass/forwarding mux hook，未实现 partial-lane merge 注入"
    },
    {
      "runid": "FSU-FP10-F0-W2",
      "model_id": "FP10",
      "load_id": "W2",
      "rank": 53,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 completion early/late/drop/duplicate、result/dest swap、stale completion 注入；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FP10-F0-W7",
      "model_id": "FP10",
      "load_id": "W7",
      "rank": 54,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 completion early/late/drop/duplicate、result/dest swap、stale completion 注入；W7 本身无 FP artifact/golden"
    },
    {
      "runid": "FSU-FQ03-F0-W2",
      "model_id": "FQ03",
      "load_id": "W2",
      "rank": 55,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 src0↔src1 配对交换；现有 tag_swap 是换成随机 producer，不是配对交换；无 PROP；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FQ05-F0-W2",
      "model_id": "FQ05",
      "load_id": "W2",
      "rank": 56,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 valid/issued/squashed 注入 API；IQ slot 生命周期/occupancy 守恒无证据；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FQ05-F0-W7",
      "model_id": "FQ05",
      "load_id": "W7",
      "rank": 57,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 valid/issued/squashed 注入 API；IQ slot 生命周期/occupancy 守恒无证据；W7 本身无 FP artifact/golden"
    },
    {
      "runid": "FSU-FQ07-F0-W2",
      "model_id": "FQ07",
      "load_id": "W2",
      "rank": 58,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 ready-list rank/age 注入；seqNum 只用于日志/tag_stuck；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FQ09-F0-W2",
      "model_id": "FQ09",
      "load_id": "W2",
      "rank": 59,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "`noteIqDeparture` 只读；无 issue→execute early/late/drop/duplicate/stale slot 注入；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FQ10-F0-W2",
      "model_id": "FQ10",
      "load_id": "W2",
      "rank": 60,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 FU index 替代 / busy↔free / release lost 注入；无 FUPool 证据；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FR04-F0-W2",
      "model_id": "FR04",
      "load_id": "W2",
      "rank": 61,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 读地址/tag 替代到另一 active-ready Vec phys reg 的注入 API；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FR08-F0-W2",
      "model_id": "FR08",
      "load_id": "W2",
      "rank": 62,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 Vec 写目标 tag 替代/交换注入；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FR09-F0-W2",
      "model_id": "FR09",
      "load_id": "W2",
      "rank": 63,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "无 write-enable/ready/wakeup 原子性（lost/early/late/split）注入；W2 本身无 true artifact"
    },
    {
      "runid": "FSU-FR10-F0-W2",
      "model_id": "FR10",
      "load_id": "W2",
      "rank": 64,
      "score": 0.0,
      "tier": "T5",
      "injector": "none",
      "chain": "none",
      "workload": "none",
      "cost": "L",
      "risk": "high",
      "gap": "gem5 O3 无 bypass/forwarding mux hook，未实现 partial-lane merge 注入；W2 本身无 true artifact"
    }
  ],
  "strict_top3": [
    "FSU-FP07-F0-W4",
    "FSU-FP07-F0-W6",
    "FSU-FP05-F0-W6"
  ],
  "recommended_top3_distinct": [
    "FSU-FP07-F0-W4",
    "FSU-FP05-F0-W6"
  ],
  "next_pilot": "FSU-FP07-F0-W4",
  "minimal_verification_command": "python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FR07-F0-W1-seed1.json --seed 1 --out-root /tmp/fsu-fr07-w1-gate",
  "defects": {
    "FQ08-b": {
      "verdict": "fixed_pending_gem5_gate",
      "summary": "已修复：shouldWrongSourceWake 只记 attempted 并返回 false；真正施加在 noteTagWake，只有存在合法 victim 才 applied++/消耗 maxFaults；无 victim 只增加 no_victim。host 单测通过，gem5 gate 待运行。",
      "evidence": [
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc",
          "pattern": "CHAOSIQ::noteTagWake"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc",
          "pattern": "iq_counts.applied++;"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh",
          "pattern": "no_victim"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh",
          "pattern": "WakeDecision"
        }
      ],
      "minimal_test": "src_ready_bitflip：无 victim 负例 applied=0/faults_injected: 0；有 victim 正例 applied=1/faults_injected: 1。"
    },
    "PRF-identity-generation": {
      "verdict": "fixed_pending_gem5_gate",
      "summary": "FR03 永久 cell 语义保持正确；FR01/FR02 的 Vec bit_flip 现为真实瞬态路径：单 bit / 两个必互异 bit、128-bit lane/字段域、phys_reg+reg_generation 证据、L0/L1/overwrite/L5 观察；显式 mask popcount 不符时 fail closed。仍缺正式 3 seed 与全字段覆盖。",
      "evidence": [
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/chaos_vec_transient.hh",
          "pattern": "chooseDistinct"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/chaos_vec_transient.hh",
          "pattern": "onlySelectedBitsDiffer"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/chaos_vec_transient.hh",
          "pattern": "TransientCell"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc",
          "pattern": "VecFaultFailClosed"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/regfile.hh",
          "pattern": "noteTraceOverwrite"
        }
      ],
      "minimal_test": "FR01 mask 0x20 -> bit_indices=5, before 0x0/after 0x20, overwrite contained；FR02 mask 0x2000000020 -> bit_indices=5,37；mask popcount 不符 -> fail closed 且无 fault_applied。"
    },
    "FP08-suppressed_count": {
      "verdict": "fixed_pending_gem5_gate",
      "summary": "已修复：fpsr_suppress 输出 attempted/applied/suppressed/reason 并发射 suppress 事件；rounding_sub 早退路径接入 noteFaultApplied（L0/L1），并记录 rounding_attempted/applied。两者均标注为代理边界，未产生正式认证。host 构建通过，gem5 gate 待运行。",
      "evidence": [
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc",
          "pattern": "CHAOS_FPSR_SUPPRESSED="
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc",
          "pattern": "rounding_sub_one_ulp_proxy"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc",
          "pattern": "++rounding_applied;"
        },
        {
          "file": "tools/fsu_seed_runner.py",
          "pattern": "fpu_fpsr_suppress"
        }
      ],
      "minimal_test": "fpsr_suppress 运行退出应输出 CHAOS_FPSR_ATTEMPTED/APPLIED/SUPPRESSED 且 attempted==suppressed；rounding_sub 运行应产生 fault_applied 根与 CHAOS_ROUNDING_APPLIED。"
    },
    "FQ08-c": {
      "verdict": "fixed_pending_gem5_gate",
      "summary": "已修复：wake_phase 改用 CHAOSIQ 自有 DelayedWake，持有 DynInstPtr+seq/tid+dest generation 快照；fire 前状态机校验 squash/generation/identity，不匹配则安全忽略；不再使用 inst_queue.cc 的旧 DelayedWakeEvent。host 单测通过，gem5 squash gate 待运行。",
      "evidence": [
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh",
          "pattern": "IgnoreSquashed"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh",
          "pattern": "IgnoreGeneration"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc",
          "pattern": "CHAOSIQ::DelayedWake::process()"
        },
        {
          "file": "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc",
          "pattern": "delayed_scheduled"
        }
      ],
      "minimal_test": "branch_mispred + wake_phase/phaseOffset 跨 squash：出现 ignore_squashed/ignore_generation，无 dependGraph assert，exit 0。"
    }
  }
}
<!-- F0_READINESS_JSON_END -->


## 执行更新（2026-11-04）

- 已完成 `FSU-FR07-F0-W1`、`FSU-FR07-F0-W3`、`FSU-FR07-F0-W5`：
  W1/W3 各 3 个单 seed、W5 3 个五程序 suite seed，全部 audit/certified、SDC/full。
- 配置：W1 FP-ScalarProbe；FR07-a mask 0x80000000、FR07-c mask 0x80000001、
  FR07-d mask 0x00080000。旧 attempt-1 是 execute-post-write 代理并保留为
  `PROXY_EVIDENCE`；当前 attempt-2 使用真实 PRF-WB 数据边界 hook v2
  （`injection_site=prf_wb_data`）。
- 证据：`runs/fsu/FSU-FR07-F0-W1/seed{1,2,3}/attempt-2/`、
  `runs/fsu/FSU-FR07-F0-W3/seed{1,2,3}/attempt-1/`、
  `runs/fsu/FSU-FR07-F0-W5/seed{1,2,3}/`；gate：
  `runs/fsu-gates/FR07-HOOK-GATE-FINAL/` 与 `FR07-HOOK-SQUASH9/`。
- 矩阵将该 RunID 标为 COMPLETE_3_OF_3，coverage_reason 记录真实 hook 与保留的
  旧 execute-post-write proxy attempt；真实 hook 证据见 `FR07-PRF-WB-HOOK.md`。
