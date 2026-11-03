# F5（永久卡死）readiness 审计（2026-11-03 事实刷新）

> 8 个 F5 RunID：FP06-W1/W3/W4/W5/W6，FR03-W3/W5/W6。
> 数据源：`runs/fsu` 磁盘证据（AUTHORITATIVE + `audit.json`）与
> `runs/fsu/COMPLETE_PROPAGATION_PATHS/INDEX.json`；代码能力证据见
> `IMPLEMENTATION_MATRIX.json` 的 `capability_evidence`。
> **代码存在不等于正式认证**；本表以磁盘 certified seed 为准。
>
> 当前：**FP06-F5-W3 COMPLETE_3_OF_3**、**FP06-F5-W1 COMPLETE_3_OF_3**
> （gate PASS 后 3 个正式 seed 全部 audit.ok/certified）；
> FP06-F5-W4/W5/W6 未正式运行；FR03-F5-W3/W5/W6 PARTIAL/BLOCKED；
> **FP06-d partial-product proxy MISSING**。

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

## 2. 8 个 F5 RunID readiness

| RunID | readiness | seed_completion | 主要缺口 |
|---|---|---|---|
| FSU-FP06-F5-W1 | COMPLETE_3_OF_3 | 3/3 | gate PASS 后完成 3 个正式 seed：FP06-a FP32 scalar sign SA0、FP06-b FP64 scalar sign SA1、FP06-c FP32 scalar 固定 mantissa SA0；每 seed eligible 41,216、exposures 40,192，terminal=full、oracle=SDC、audit.ok/certified。仅覆盖 W1 的 scalar FP precision/opClass 子集；**FP06-d 仍 MISSING** |
| FSU-FP06-F5-W3 | COMPLETE_3_OF_3 | 3/3 | 已认证 FP06-a SA0、FP06-b SA1、FP06-c 固定 mantissa（每 seed 16,384 exposures）；仅覆盖结果侧代理与 W3 32-bit lane2 sign/mantissa 域；**FP06-d MISSING**；其他 lane/字段未覆盖 |
| FSU-FP06-F5-W4 | NOT_RUN | 0/3 | W4-rate-v1 eligible=2,097,155；有界 exposure 采样已实现，但 F0-W4 仍是短 W4 pilot，FP06-F5-W4 无正式 seed |
| FSU-FP06-F5-W5 | NOT_RUN | 0/3 | W5 PolyBench suite artifact 已成立（`FSU-FP04-F0-W5` 3/3，gemm/2mm/lu/cholesky/jacobi-2d，2mm 已 vendored 且 gate PASS），但 FP06-F5-W5 未运行；suite component 不计 seed |
| FSU-FP06-F5-W6 | NOT_RUN | 0/3 | W6 的 FFT/稀疏组件仍 PARTIAL；无 FP06-F5-W6 正式 seed |
| FSU-FR03-F5-W3 | BLOCKED | 0/3 | Vec 写路径 stuck + 永久物理 cell 跨 generation 语义已在代码与 host 单测中实现，CHAOSPhysReg 的 FSU_PROP 部分层已构建；仍缺 L5 commit/squash/oracle、runner 显式 CHAOSPhysReg 路径、O3 容器级 squash/free/realloc 验证；不得认证 |
| FSU-FR03-F5-W5 | BLOCKED | 0/3 | 同 FR03-F5-W3；W5 suite artifact 已成立但不能替代 FR03 未验证的 PRF 传播链 |
| FSU-FR03-F5-W6 | BLOCKED | 0/3 | 同 FR03-F5-W3 + W6 FFT/稀疏组件仍 PARTIAL |

> 双视图（磁盘权威）：历史全量 **27/519 seed、9/173 RunID**；
> 活跃 F0/F5 **18/240 seed、6/80 RunID**。suite seed 3 个对应 15 个
> component run，component **不进入** seed 总数。

## 3. FP06 代码能力与认证边界

### 3.1 FP06-a / FP06-b / FP06-c（已认证）

实现位置 `CHAOS/gem5/src/cpu/o3/CHAOSFPU/`：

- `permanentStuck`：warm-up 后第一个 eligible event **安装一次**，全程唯一
  `fault_id`；后续每个 eligible 都是同一 fault 的 **exposure**，不新建 fault。
- `applyStuck`：SA0 `&~mask`、SA1 `|mask`，**不是 XOR**；非目标 bit 不变。
- 有界 exposure 采样：`f5SampleLimit` / `f5KeepFirstLastN`，精确记录
  `exposures_total/sampled/dropped`；强制事件不丢弃。
- FSU_PROP L0–L5 与 `chain_end` 已发射，链审计接受 `fault_installed` 根。

`FSU-FP06-F5-W3` 的 3 个正式 seed 全部 `audit.ok / certified=true`：

| seed | 预注册 | mask | polarity | exposures | activated | terminal | oracle |
|---|---|---|---|---|---:|---:|---|---|
| 1 | FP06-a FP32 sign SA0 | `0x80000000` | 0 | 16,384 | 764 | full | SDC |
| 2 | FP06-b FP32 sign SA1 | `0x80000000` | 1 | 16,384 | 15,620 | full | SDC |
| 3 | FP06-c fixed mantissa | `0x007f8000` | 0 | 16,384 | 16,296 | full | SDC |

证据：`runs/fsu/FSU-FP06-F5-W3/seed{1,2,3}/attempt-1/`
（`audit.json`、`chain_report.json`、`manifest.json`、`oracle.json`）。

`FSU-FP06-F5-W1` 的 3 个正式 seed（W1 FP-ScalarProbe，B0，scalar FP
precision/opClass 过滤）同样全部 `audit.ok / certified=true`：

| seed | 预注册 | precision | mask | polarity | eligible | exposures | sampled | dropped | activated | terminal | oracle |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | FP06-a | fp32 | `0x80000000` | 0 | 41,216 | 40,192 | 513 | 39,679 | 15,027 | full | SDC |
| 2 | FP06-b | fp64 | `0x8000000000000000` | 1 | 41,216 | 40,192 | 514 | 39,678 | 25,543 | full | SDC |
| 3 | FP06-c | fp32 | `0x007f8000` | 0 | 41,216 | 40,192 | 514 | 39,678 | 29,559 | full | SDC |

证据：`runs/fsu/FSU-FP06-F5-W1/seed{1,2,3}/attempt-1/`；gate PASS 证据：
`runs/fsu-gates/F5-FP06-F5-W1-v3/`（不计 519/240）。

**认证边界**：这 3 个 seed 只认证 FP06-a/b/c 的结果侧代理，且 W3 载体是
32-bit lane2。它们不认证 FP06-d，也不认证其他 lane、FP64/全 128-bit
字段矩阵或其他 workload。

### 3.2 FP06-d（MISSING）

- 工作簿要求 multiplier **partial-product** 级故障。
- gem5 ARM FP 是功能级模型，没有可观测的部分积/对齐移位内部点；当前
  `CHAOSFPU` 也没有 partial-product 注入代码。
- 因此 **FP06-d 保持 MISSING**；不得用最终结果位冒充 partial-product。
- 影响：`FSU-FP06-F5-W3` 不能把 FP06 标成完整；FP06 模型整体保持
  **PARTIAL**。

### 3.3 FP06-W1/W4/W5/W6（未正式完成）

- W1：已完成 3/3。gate（FP32 SA0、FP64 SA1、FP32 fixed mantissa、
  precision mismatch eligible=0、opClass/regClass 过滤、守恒、采样、
  chain_end、B0、oracle）在 `runs/fsu-gates/F5-FP06-F5-W1-v3/` PASS，
  产物不计 519/240；正式 seed 在 `runs/fsu/FSU-FP06-F5-W1/seed{1,2,3}/`。
- W4/W5/W6：均 0/3；W5 suite artifact 已成立，但“有 workload”不等于
  “该 F5 RunID 已运行/认证”。

## 4. FR03（Vec PRF stuck）状态：PARTIAL / BLOCKED

已完成（代码 + host 单测）：

- Vec 写路径每次写入后重新施加 SA0/SA1（`regfile.hh` `reapplyVecStuck`）；
- 永久物理 cell 语义：故障 key 是 reg_class + phys_index + lane/mask +
  polarity；generation 只标识分配世代，**不是清除条件**；free/realloc
  后同一物理 cell 仍卡死，新 generation 的 exposure 链从 1 重新开始
  （工作簿表 3「永久缺陷跨物理槽复用」；见
  `docs/gem5-fi/fsu/FR03-GENERATION-SEMANTICS.md`）；
- Vec 索引不再被 legacy periodic re-apply 当 int 写入；
- `tests/unit/chaos_vec_stuck_test.cc` + `tests/unit/chaos_physreg_generation_test.cc`
  验证连续写保持 SA0、非 XOR、跨 generation 持久、generation 链重启、
  squash 后仍卡死、其他 cell/class 不串扰、reset 后清除。

仍未完成（截至本文件写入时，工作区存在未提交的 FR03 代码改动）：

1. 真实 CHAOSPhysReg 的 FSU_PROP L0–L5：工作区已开始接入
   `notePropEvt`/`emitFsuProp`，但尚未提交、未构建、未在 gem5 中验证；
2. runner 显式 CHAOSPhysReg 路径（当前 runner 固定 FPU manifest 路径，
   工作区 runner 改动只有 FP06 opClass/regClass 过滤）；
3. squash / rename / free / realloc 的容器级完整测试（当前 host 单测覆盖
   generation 身份，不等于 O3 容器级验证）；
4. FR03-F5 的正式 seed 与逐 fault 链审计。

结论：**FR03-F5-W3/W5/W6 保持 BLOCKED，0/3，不得认证**；不得借用
FP06 结果侧证据认证 FR03。model 级 `audited_status` 仍为 PARTIAL，
`f5_readiness` 为 BLOCKED。代码存在（包括工作区未提交改动）不等于认证，
只有构建通过、容器级测试通过并跑完正式 seed 后才会改变 readiness。

## 5. 最小可运行候选与门禁

- `FSU-FP06-F5-W1` 已完成 3/3（REAL workload + golden；见 §3.1 与
  `runs/fsu-gates/F5-FP06-F5-W1-v3/GATE.md`）。
- `FSU-FP06-F5-W3` 已完成 3/3；其事件量（16,384 eligible）在
  `EVENT_CAP=200000` 内，有界采样使证据可审计。
- 正式运行前必须具备：F5 manifest 预注册、polarity/mask 运行前固定、
  B0 配置、golden/fault oracle、chain_end、逐 seed audit。
- FR03 在上述 4 项缺口完成前不得正式运行。

## 6. 多 fault 审计要求（F5）

- 每个 fault 独立 `fault_id`、L0 root、direct parent 链、terminal；
- 所有 fault 共享同一 mask/polarity/物理目标（FP06 同一结果字段；
  FR03 同一 phys cell；generation 只作为该次 exposure 的世代身份，不是
  故障 key 或清除条件）；
- 只有正确值与卡死极性不同才算 activated；
- 一个 fault 的 L5 不得认证其他 fault；
- run-level oracle 与逐 fault terminal 分开；
- 必须保留 producer/affected sn、first impact/exposure。
