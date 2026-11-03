# FP04 F0-W5 suite 权威裁决（2026-11-03）

> 状态：**裁决生效**。本文是 `FSU-FP04-F0-W5` 的计数、身份、失败重试与
> 术语的唯一权威来源；与旧 `FP04-W5-W6-ARTIFACT-STATUS.md` 的“suite 身份
> 未定义 / 3-seed 计数未裁决”阻塞点相对应，本文完成裁决。
>
> 适用范围：`fsu` 分支。W5 是活跃 F0 范围，但**正式 seed 仍 BLOCKED**，
> 直到五程序逐元素 oracle（计划任务 4）与无故障 gate（任务 5）通过。

## 1. 固定 suite

`FSU-FP04-F0-W5` 是一个**固定 5 程序 suite**，程序顺序永远是：

```
gemm → 2mm → lu → cholesky → jacobi-2d
```

- `program_order` 由代码常量 `tools/fsu_suite.py:PROGRAM_ORDER` 固化；
- `program_count = 5`；
- **顺序不可按结果调整**。不得因为某程序失败、oracle 通过或 eligible 较大
  而重排、删除或替换程序；
- 单程序（例如 2mm）只能作为 GATE 或 component run，**绝不能冒充 W5
  formal suite seed**；
- 2mm decode-gate（`runs/fsu-gates/F0-W5-2MM-DECODE-gate`）不计 519，也不
  是 W5 suite seed。

## 2. 三个术语（必须分开书写）

| 术语 | 定义 | 数量关系 |
|---|---|---|
| **formal suite seed** | `FSU-FP04-F0-W5` 的正式计数单位；一个 suite seed 内含固定 5 个 component run | 正式目标 3 个 |
| **component run** | 一个 suite seed 内、只跑**一个** PolyBench 程序的一次独立运行；拥有独立 census / golden / fault / oracle / 传播链审计 | 每个 suite seed 5 个；3 个 suite seed = 15 个 |
| **component fault** | 一个 component run 内注入的**一次**故障 | 每个 component run 1 次；3 个 suite seed = 15 次 |

禁止用 “3 seeds = 15 seeds” 或 “15 component = 15 seeds” 之类的表述。
**3 个 suite seed = 15 个 component run = 15 次 component fault，但正式
计数只 +3。**

## 3. 计数规则

- 一个 suite seed 在 `fsu_index` 中只增加 **1** 个 admitted seed；
- `admitted_seeds_total` **绝不**累加 component run 数；
- 历史全量视图：目标 `173 RunID × 3 = 519`；活跃视图：
  `80 RunID × 3 = 240`，F1–F4 仍为 `DEFERRED_BY_USER`；
- W5 完成后：历史 `18 → 21`（21/519，7/173 RunID）；活跃
  `9 → 12`（12/240，4/80 RunID）；
- suite seed 的 component 明细单独报告（`suite_seed_dirs`、
  `suite_seed_admitted`、`component_runs_in_admitted_suites`），不进入
  `admitted_seeds_total`；
- component 的 eligible 不得合并成单一分母；每个程序独立报告
  eligible / activated / terminal / oracle。

## 4. suite 认证条件

一个 suite seed 只有在下列条件**全部**成立时才可认证：

1. seed 目录存在真实 `suite_manifest.json`，其 suite 身份与
   `suite_hash` 自洽；
2. seed 目录 `audit.json.ok = true`（suite 级审计）；
3. 恰好 5 个 component，顺序固定、无缺失、无重复；
4. 每个 component：
   - `component_status = admitted`；
   - component attempt 的 `audit.json.ok = true` 且 `certified = true`；
   - `component_manifest.json` 的 `component_manifest_sha256` 与真实
     attempt `manifest.json` 一致；
   - oracle 不是 `SimulatorError` / `Inactive`，且传播链真实
     certified；
5. `suite_report.json` 明确记录 `formal_suite_seed_count = 1`、
   `component_run_count = 5`。

任一条件不成立 → **整个 suite seed 不认证**。不得用其余 4 个成功
component 认证 suite；不得用 component 级 AUTHORITATIVE 冒充 suite 级
AUTHORITATIVE。

## 5. 失败与重试

- 失败的 component attempt **保留** `.failed`，不删除、不改写；
- 同一 suite seed 只要任一 component 失败：
  - 不写 suite 级 `suite_manifest.json` / `audit.json`；
  - **不写 suite 级 `AUTHORITATIVE`**；
  - `suite_report.json` 记录失败 component 列表，并追加
    `suite_failures.jsonl`；
- 重试时：
  - 已 admitted 的 component 可复用其真实 attempt（不重复跑 gem5）；
  - 失败 component 新建 `attempt-k+1`，**旧 attempt-1 原样保留**；
  - 不用新结果覆盖失败证据；不允许手工补写事件、audit 或 Markdown；
- 只有 5/5 component 全部通过独立审计后，按顺序写：
  `suite_manifest.json` → `suite_report.json` → suite `audit.json` →
  suite 级 Markdown → **最后**写 `AUTHORITATIVE`。

## 6. 目录与身份

### 6.1 路径

```
runs/fsu/<RunID>/seed<N>/components/<program_id>/<RunID>/seed<derived>/attempt-k/
```

- `<RunID>` 是 registry 中的真实 RunID（例如 `FSU-FQ01-F0-W5`）；
- `<N>` 是 formal suite seed（1..3）；
- `<derived>` 是该 component 的派生 seed，不是 `<N>`；
- `attempt-k` 只增不改。

### 6.2 suite_hash

`tools/fsu_suite.py:compute_suite_hash`：

- SHA-256 over **canonical JSON**（键排序、无多余空白、UTF-8）；
- 严格只含身份字段：
  - `suite_id`、`suite_version`、`program_order`、`program_count`；
  - 每个程序：`program_id`、`program_index`、`source_sha256`、
    `binary_sha256`、固定 `scale`；
  - `compiler.version`、`compiler.cflags`；
  - `oracle.version`；
- **绝不包含运行结果**：不含 golden、attempt、component status、
  eligible/activated、terminal、oracle 结局、路径或时间戳；
- 任一身份字段被篡改 → 重算 hash 必变；manifest 声明的 hash 与重算
  不一致时 `validate_suite_manifest` 抛 `SuiteError`；
- 二进制尚未按当前源码重建时，`binary_sha256 = "pending"`；正式运行
  前必须回填 64-hex 并重算 `suite_hash`（`require_hashes=True` 会拒绝
  pending）。

### 6.3 component seed

```
component_seed = SHA-256(suite_id | suite_version | suite_seed |
                         program_id | policy_version)[0:8]  (大端)
```

- 0 映射为 1；
- 同一 suite seed + 程序 + policy 完全确定；
- 5 个程序的派生 seed 必须互不相同，`derive_component_seeds` 在碰撞时
  直接抛错；
- component seed 不得回退为 suite seed，也不得按程序顺序递增。

## 7. component manifest 必填字段

`schemas/fsu_component.schema.json` 与
`tools/fsu_suite.py:validate_component_manifest` 共同约束：

```
suite_id, suite_hash, suite_seed,
program_id, program_index, program_count=5,
component_attempt,
component_manifest_sha256,
component_binary_sha256, component_source_sha256,
component_golden_sha256,
component_status, component_eligible, component_activated,
component_terminal, component_oracle
```

补充字段（允许但非 schema 必填）：
`component_seed`、`component_seed_policy_version`、`component_faults`、
`component_audit_ok`、`component_certified`、`attempt`。

`component_manifest_sha256` 定义为该 component attempt 真实
`manifest.json` 的 SHA-256；suite 审计会重算并拒绝漂移。
`component_golden_sha256` 若未显式提供 64-hex golden artifact 哈希，则
按 `sha256-utf8-of-golden-token-v1` 对 suite config 的 golden token 求
SHA-256，并在 manifest 中显式记录 scheme（不伪造 golden 文件哈希）。

### 7.1 逐元素 oracle（W5 认证必需）

每个 component 的 workload manifest 带 `element_oracle`：

```json
{"golden_array": "configs/fsu/suites/polybench-fp-v1/golden/<program>.bin",
 "meta": {"program_id": "...", "golden_id": "...", "dtype": "fp32",
          "layout": "row-major", "endianness": "little",
          "count": N, "shape": [..], "domain": "full",
          "abs_tol": 0.0, "rel_tol": 0.0, "ulp_tol": 0,
          "oracle_version": "polybench-element-v1"},
 "oracle_version": "polybench-element-v1"}
```

- 注入运行通过 `--cmd_arg --array-dump=<attempt>/inject/array.bin` 写出
  **一个** live-out 数组（小端原始 fp32 字节）；census 运行不写。
- suite runner 在 component attempt 完成后调用
  `tools/fsu_oracle.compare(...)`，写 `oracle_elements.json`，至少包含
  `mismatch_count`、`first_mismatch_index`、`max_abs_error`、
  `max_rel_error`、`max_ulp`、`golden_sha256`、`fault_sha256`。
- `component_oracle`：`mismatch_count > 0 → SDC`；
  `mismatch_count == 0 → MASKED`（含 EXACT_MATCH / WITHIN_TOLERANCE）。
- component 认证要求 `oracle_elements.json` 与 `inject/array.bin` 都存在，
  且两者的 SHA-256 被 `evidence_sha256.json` 覆盖；缺 array、oracle 异常
  或证据未被覆盖 → component 失败，suite 不认证。
- SDC 是合法故障结局（不是 suite 失败）；suite 失败只由 component
  admitted/audit/oracle 证据不成立触发。

## 8. 与 oracle / gate 的关系

- 现有 `FINAL=<16hex>` exact-hash 继续作为 run-level 分类器输入；
  **W5 认证额外要求** 逐元素 oracle 结果（`oracle_elements.json`）。
- 逐元素 oracle 的代码与 schema 已接入（`tools/fsu_oracle.py`、
  `schemas/fsu_oracle.schema.json`）；suite runner 已强制要求
  `element_oracle`，缺 golden array 或缺 `inject/array.bin` 时响亮拒绝。
- 在计划任务 5（W5 无故障 element-oracle gate）真实通过前，
  **F0-W5 保持 BLOCKED**，即使 suite 身份、seed 派生与 runner 已就绪。
- 当前五个 `.c` 已由 oracle owner 增加 dump hunk（源码 SHA 已变化），
  对应二进制尚未重建，golden array 也尚未生成；
  `configs/fsu/suites/polybench-fp-v1.json` 因此将五个
  `binary_sha256` 标记为 `pending`，并将 `element_oracle.golden_array`
  标记为 `pending_generation`，待重建/生成后回填并重算 `suite_hash`。
- `load_suite` 在这些资产缺失时抛出 `SuiteError`（不降级、不静默）；
  正式 suite seed 只能在这些真实证据齐备后运行。
- 2mm decode gate 只证明“单程序链可成立”，不证明 suite 认证。

## 9. 旧证据不变

- 18 个历史正式 seed 与 2mm gate 证据只读保留，不追改、不改标；
- 旧单 seed manifest 行为不变：不带 `component` 字段时
  `fsu_seed_runner.run_seed` 与 `fsu_seed_audit.audit_attempt` 语义
  完全保持；
- suite 目录审计（`audit_suite`）与旧单 attempt 审计
  （`audit_attempt`）是两个入口，互不替代。
