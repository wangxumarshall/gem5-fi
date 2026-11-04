# F5（永久卡死）readiness 审计（2026-11-03 事实刷新）

> 8 个 F5 RunID：FP06-W1/W3/W4/W5/W6，FR03-W3/W5/W6。
> 数据源：`runs/fsu` 磁盘证据（AUTHORITATIVE + `audit.json`）与
> `runs/fsu/COMPLETE_PROPAGATION_PATHS/INDEX.json`；代码能力证据见
> `IMPLEMENTATION_MATRIX.json` 的 `capability_evidence`。
> **代码存在不等于正式认证**；本表以磁盘 certified seed 为准。
>
> 当前：**FP06-F5-W3 COMPLETE_3_OF_3**、**FP06-F5-W1 COMPLETE_3_OF_3**、
> **FP06-F5-W4 COMPLETE_3_OF_3**、**FP06-F5-W5 COMPLETE_3_OF_3**
> （gate PASS 后正式 suite seed 全部 audit.ok/certified）、**FP06-F5-W6 COMPLETE_3_OF_3**（SVD/FFT/sparse）；
> FR03-F5-W3 PARTIAL_2_OF_3（seed3 protocol deviation）；FR03-F5-W5/W6 COMPLETE_3_OF_3；
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
| FSU-FP06-F5-W4 | COMPLETE_3_OF_3 | 3/3 | gate PASS 后完成 3 个正式 seed（W4-rate-v1，B0/FP64/decode，真实 census 1,310,723）：seed1 FP06-a sign SA0、seed2 FP06-b sign SA1、seed3 FP06-c fixed mantissa SA0；每 seed exposures 1,309,699、activated 130,814/1,132,901/1,300,553、terminal=full、oracle=SDC、audit.ok/certified。历史文档中的 2,097,155 是旧未过滤 D2 配置，不是本 RunID 的 eligible 流；**FP06-d 仍 MISSING** |
| FSU-FP06-F5-W5 | COMPLETE_3_OF_3 | 3/3 | suite gate `runs/fsu-gates/F5-FP06-W5-GATE-v5/` 5/5 PASS；正式 suite seed1/2/3 均 5/5 component admitted + suite audit ok；每 suite seed 只计 1，15 component 不进入 seed 总数；三个 suite seed 均 SDC |
| FSU-FP06-F5-W6 | COMPLETE_3_OF_3 | 3/3 | W6 suite gate 3/3 PASS；正式 seed1/2/3 各 3/3 component admitted；SVD fp64、FFT/sparse fp32 逐组件精度覆盖；9 component 只计 3 seed |
| FSU-FR03-F5-W3 | PARTIAL_2_OF_3 | 2/3 | gate v3 PASS（L5/生命周期/runner 均真实）；seed1/2 audit.ok。seed3 attempt-1 是原预注册目标的真实结局（activated gen3/6，但 committed gen8 未被故障改变；terminal=exposed_unconsumed、oracle=Masked、chain_certified=false）；attempt-2 改为 sign SA1 lane0，属于 **protocol deviation / supplemental evidence**，不计入原 seed3。详见 `FR03-SEED3-PROTOCOL-REVIEW.md` |
| FSU-FR03-F5-W5 | COMPLETE_3_OF_3 | 3/3 | FR03 五程序 suite gate 5/5 PASS；正式 seed1/2/3 各 5/5 component admitted；每 suite seed 只计 1 |
| FSU-FR03-F5-W6 | COMPLETE_3_OF_3 | 3/3 | FR03 W6 三组件 suite gate 3/3 PASS；正式 seed1/2/3 各 3/3 component admitted；9 component 只计 3 seed |

> 双视图（磁盘权威，2026-11-04 FR07 位置审计后）：历史全量
> **56/519 seed、18/173 RunID**；活跃 F0/F5 **47/240 seed、15/80 RunID**。
> FR07-F0-W1 的旧 3 个 execute-post-write attempt 保留为 PROXY_EVIDENCE；
> 该 RunID 已用真实 PRF-WB hook 重新认证。F5 自身 23 seed / 8 RunID 不受影响。suite seed 3 个对应 15 个
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
`runs/fsu-gates/F5-FP06-W1-v3/`（不计 519/240）。

**认证边界**：W1 + W3 两组 seed 只认证 FP06-a/b/c 的结果侧代理（W3 为
FP32 32-bit lane2；W1 为 scalar FP32/FP64）。它们不认证 FP06-d，也不
认证其他 lane、全 128-bit 字段矩阵或其他 workload。

### 3.2 FP06-d（MISSING）

- 工作簿要求 multiplier **partial-product** 级故障。
- gem5 ARM FP 是功能级模型，没有可观测的部分积/对齐移位内部点；当前
  `CHAOSFPU` 也没有 partial-product 注入代码。
- 因此 **FP06-d 保持 MISSING**；不得用最终结果位冒充 partial-product。
- 影响：`FSU-FP06-F5-W3` 不能把 FP06 标成完整；FP06 模型整体保持
  **PARTIAL**。

### 3.3 FP06-W1/W4/W5/W6

- W1：已完成 3/3。gate（FP32 SA0、FP64 SA1、FP32 fixed mantissa、
  precision mismatch eligible=0、opClass/regClass 过滤、守恒、采样、
  chain_end、B0、oracle）在 `runs/fsu-gates/F5-FP06-W1-v3/` PASS，
  产物不计 519/240；正式 seed 在 `runs/fsu/FSU-FP06-F5-W1/seed{1,2,3}/`。
- W4：已完成 3/3。非正式 gate `runs/fsu-gates/F5-FP06-W4-GATE/` PASS：
  短 W4 全量 32,643 exposures 与 bounded 32,643 完全一致（activated
  4,077，oracle 均 SDC）；正式规模 bounded 1,309,699 exposures、513
  事件、prop_evt 73 KB；注入日志 382 MB 无损 gzip 后 ~13-17 MB；
  提前终止 fail-closed。正式 seed 在 `runs/fsu/FSU-FP06-F5-W4/seed{1,2,3}/
  attempt-1/`，三 seed 均 SDC/full/audit.ok。
- W5：已完成 3/3。非正式 gate `runs/fsu-gates/F5-FP06-W5-GATE-v5/`
  5/5 PASS；正式 suite seed1/2/3 均 5/5 component admitted、suite audit ok，
  15 component 只计 3 seed。
- W6：已完成 3/3（SVD/FFT/sparse suite，9 component 只计 3 seed）。

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

仍未完成（代码已提交并构建通过；尚未在 FR03 真实 gate 验证）：

1. 真实 CHAOSPhysReg 的 FSU_PROP：L0–L4 部分层已接入并随 gem5 构建通过；
   L5 commit/squash/oracle/first-impact 仍未实现，未在 FR03 真实 gate 验证；
2. runner 显式 CHAOSPhysReg 路径（当前 runner 固定 FPU manifest 路径，
   runner 改动只有 FP06 opClass/regClass 过滤）；
3. squash / rename / free / realloc 的容器级完整测试（当前 host 单测覆盖
   generation 身份，不等于 O3 容器级验证）；
4. FR03-F5 的正式 seed 与逐 fault 链审计。

结论：**FR03-F5-W3 为 2/3（seed3 protocol deviation）；FR03-F5-W5/W6 各 3/3 suite seed 已认证**；不得借用
FP06 结果侧证据认证 FR03。model 级 `audited_status` 仍为 PARTIAL，
`f5_readiness` 为 BLOCKED。代码存在/已构建不等于认证，只有 L0–L5 完整
链、runner 路径、容器级测试通过并跑完正式 seed 后才会改变 readiness。

## 5. 最小可运行候选与门禁

- `FSU-FP06-F5-W1` 已完成 3/3（REAL workload + golden；见 §3.1 与
  `runs/fsu-gates/F5-FP06-W1-v3/GATE.md`）。
- `FSU-FP06-F5-W3` 已完成 3/3；其事件量（16,384 eligible）在
  `EVENT_CAP=200000` 内，有界采样使证据可审计。
- 正式运行前必须具备：F5 manifest 预注册、polarity/mask 运行前固定、
  B0 配置、golden/fault oracle、chain_end、逐 seed audit。
- FR03-W3 的 4 项缺口已完成并通过 gate；W5/W6 仍需各自的 suite/artifact 门禁。

## 6. 多 fault 审计要求（F5）

- 每个 fault 独立 `fault_id`、L0 root、direct parent 链、terminal；
- 所有 fault 共享同一 mask/polarity/物理目标（FP06 同一结果字段；
  FR03 同一 phys cell；generation 只作为该次 exposure 的世代身份，不是
  故障 key 或清除条件）；
- 只有正确值与卡死极性不同才算 activated；
- 一个 fault 的 L5 不得认证其他 fault；
- run-level oracle 与逐 fault terminal 分开；
- 必须保留 producer/affected sn、first impact/exposure。
