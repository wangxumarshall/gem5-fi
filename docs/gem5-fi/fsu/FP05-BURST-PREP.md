# FP05 burst 准备：语义、只读 gate 与所需 C++ 改动

日期：2026-11-04。本文件只做设计与只读校验，**不产生正式计数、不新增
RunID/seed、不运行 gem5**。结论先行：

> 当前 CHAOSFPU **没有** burst 实现。`tools/fsu_fp05_burst_gate.py` 对当前
> 源码返回 **SKIP + blocked=true**（exit 2），`evidence_missing` 为
> `burst_id, burst_ordinal, burst_length, stream`。这**不是** PASS。
> `recurring_result_stuck` 是“同一 mask 每 event 重复”，不是工作簿要求的
> 2–4 个连续 eligible 结果的 burst。

## 1. 工作簿语义（FSU-FP05）

来源：`gem5-fi-FSU单元故障注入方案_逐RunID传播监控-03-位置x模型矩阵.md`
FP05 行、`-07-展开执行矩阵.md` FSU-FP05-* 行、`runids.csv` FP05 行。

| 项 | 工作簿要求 |
|---|---|
| 故障位置 | FSU Pipe，NEON 结果 lane 群 / 短突发 |
| 故障模型 | 在 **2–4 个连续 eligible 结果**上污染同一 lane 或相邻 lane |
| 采样原则 | **不把 burst 事件当独立 Bernoulli 样本**；F1–F4 按 run cluster 统计 |
| 子模型 | FP05-a same-lane burst；FP05-b adjacent-lane；FP05-c cross-lane MBU；FP05-d lane-mask burst |
| 频率 | F0（每次运行只注入 1 次，warm-up 后均匀抽样） / F4（每 100,000 eligible events 触发一次，连续污 2–4 个事件或单事件 ±1 周期） |
| 触发条件 | 向量 op 至少有 2 个 active lane |
| 必写字段 | `burst_id / burst_ordinal / burst_length`、lane mask、每结果 hash、扇出与 cluster 结局 |
| F0 注入单位 | **一次 F0 注入 = 一个 burst episode**，不是 episode 内的每个事件 |

`tools/fsu_prop_fields.py` 早已把 `burst_id`、`burst_ordinal`、
`burst_length` 注册进 `PROP_EVT_FIELDS`（发射契约先行），但 C++ 发射端
尚未产生它们。

## 2. 当前实现状态（基于真实源码/命令）

```text
$ grep -n "burst_id\|burst_ordinal\|burst_length" \
    CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc \
    CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.hh \
    CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py
(no matches)
```

- runner / `ooo_proxy.py` / `schemas/manifest.schema.json` /
  `manifest_validate.py` 中的 “burst” 只出现在 **LSU 的
  `intermittent_burst`**，不是 FSU FP05：
  `grep` 结果没有任何 `fpu_*burst*` 参数或 `burst_mode` 字段。
- 现有最接近的模式是 `recurring_stuck`：`maybeCorrupt()` 里同一个
  `recurring_mask` 对**每个** eligible event 重复；每个事件都会
  `faults_injected_count++` 并 `noteFaultApplied()`（各自新的
  `fault_id`）。没有 `burst_id`、没有 ordinal、没有“连续 N 个后停止”。
  因此它在语义上**不能**认证 FP05。
- 频率方面，构造函数只接受 F1/F2/F3 rate ordinal：
  `known_freq = fsu_freq == "F1" || fsu_freq == "F2" || fsu_freq == "F3"`；
  **F4 尚未实现**，而 FP05-F4 行要求“每 100,000 eligible events 触发一次
  + 连续 2–4 事件”。F0 的 fixed-uniform-skip 已存在，但缺少 episode 语义。
- `F0-READINESS-ORDER.md` 已把 FP05 记为 ◐ partial，并明确
  “缺 2–4 事件 burst、burst_id/ordinal；当前每 event 各自 fault_id”。

## 3. 只读 gate：`tools/fsu_fp05_burst_gate.py`

工具不写文件、不启动 gem5。它做两件事：

1. **源码支持检查**：在 `CHAOSFPU.cc` 中查找带引号的发射字面量
   `"burst_id"` / `"burst_ordinal"` / `"burst_length"`。注释里出现
   “burst” 不算。
2. **事件流契约检查**：解析 `PROP-EVT:` / `FSU_PROP-EVT:` 行（支持 `.gz`），
   只取 `model_id=FP05` 的 `kind=fault_applied` 事件（无 `model_id` 时取
   全部），按顺序切成 burst episode。

### 3.1 校验规则

| 检查 | PASS 条件 | FAIL 条件 |
|---|---|---|
| `recurring_not_burst_tagged` | recurring/permanent 事件没有 burst 字段 | recurring 事件带 `burst_id/ordinal/length` |
| `all_events_tagged` | 所有正常事件要么都带 burst 字段，要么都不带 | 混用（部分带、部分不带） |
| `burst_id_integer` | 每个 tagged 事件的 id 是整数 | 非整数 |
| `burst_id_not_mixed` | 同一 `burst_id` 只出现在一个连续 run | id 在另一个 burst 之后再次出现（拆分/交叉混用） |
| `ordinal_0_to_len_minus_1` | ordinals 恰为 `0..len-1` 且顺序正确 | 重复、缺失、乱序 |
| `length_in_2_4` | `burst_length ∈ {2,3,4}` | 越界 |
| `length_declared_constant` | episode 内所有事件声明的 length 相同 | 不一致 |
| `length_matches_events` | 声明 length == 实际事件数 | 不匹配 |
| `eligible_ordinal_consecutive`（可选） | 若提供 `eligible_ordinal`，必须连续递增 | 不连续 |
| `field_*_present` | 三个字段齐全 | 缺字段 → `evidence_missing`（SKIP，不是 FAIL） |

- `recurring_result_stuck` / `permanent_stuck`（字段 `field`、`kind`、
  `stuck_polarity`、`fixed_mask` 任一命中）被单独计数
  （`recurring_event_count`），**永远不计入** `burst_event_count`。
- 没有任何 `fault_applied`、没有 FP05 事件、没有 burst 字段 → **SKIP**，
  并列出 `evidence_missing`。
- 源码无 burst 发射端、但事件流声称有合法 burst → **FAIL**（fail closed，
  防止伪造/陈旧证据）。
- 退出码：`0=PASS, 1=FAIL, 2=SKIP`。

### 3.2 当前真实 gate 结果

```text
$ python3 tools/fsu_fp05_burst_gate.py
FP05 BURST GATE: SKIP
reason: CHAOSFPU source has no burst emitter; no burst evidence can exist yet
blocked: true (source has no burst emitter)
source: implemented=False missing=['burst_id', 'burst_ordinal', 'burst_length']
burst_episodes=0 burst_events=0 recurring_events=0
evidence_missing: burst_id, burst_ordinal, burst_length, stream
$ echo $?
2
```

`--json` 的 `status` 为 `SKIP`、`blocked` 为 `true`。**没有假 PASS。**

### 3.3 合成事件流测试（只验证规则）

`tests/test_fsu_fp05_burst.py`（22 项）覆盖：

- 合法 burst（len=2/3/4）；
- 两个 episode 独立计数；
- 长度越界、声明长度不一致；
- ordinal 重复 / 缺失 / 乱序；
- 跨 `burst_id` 交叉混用 / 同一 id 拆成两段；
- recurring/permanent 被误标为 burst；
- recurring 事件被排除且不进入 episode 计数；
- 无 burst / 空流 / 部分字段 → SKIP；
- 其他 model（FP04）被过滤；
- 当前源码无 burst 发射端 → `build_report()` 为 SKIP+blocked；
- 合成 burst 对无发射端源码 → FAIL（禁止假 PASS）；
- CLI 退出码。

这些是**规则测试**，不是 gem5 行为证据。

## 4. 需要的 C++ / 配置改动（本任务未落地）

### 4.1 参数与端到端接线（必须四处一致）

1. `CHAOSFPU.py`：
   - `burstMode = Param.String("", "same_lane|adjacent_lane|cross_lane_mbu|lane_mask")`
   - `burstLength = Param.UInt64(0, "2..4; 0 = not a burst mode")`
   - 可选 `burstLaneStep` / `burstLaneMask`（adjacent / lane-mask 子模型）
   - `burstIdBase`（可选，固定 episode id 起点）
2. `configs/se/ooo_proxy.py`：对应 CLI（默认关闭，不改变既有 campaign）。
3. `tools/runner.py`：`fpu_mode` → CLI 的 1:1 映射，未知值 fail closed。
4. `schemas/manifest.schema.json` + `tools/manifest_validate.py`：
   `burst_mode` 枚举、`burst_length ∈ {2,3,4}`、与
   `recurring_stuck/permanent_stuck/rate/rounding/fpsr` 的互斥关系。
   “组件未在四处接通就响亮拒绝”，不能半路由。

### 4.2 CHAOSFPU 状态机

建议字段（命名可按实现调整）：

```text
uint64_t burst_episode_counter;   // 本 run 已完成的 episode 数
bool     burst_active;
uint64_t burst_id;                // 一个 episode 固定
uint64_t burst_length;            // 2..4
uint64_t burst_ordinal;           // 0..length-1
int      burst_lane_base;         // same/adjacent lane 起点
int      burst_lane_policy;       // a/b/c/d
```

语义：

- 每个 episode 在选中的 eligible event 上 arm；随后**同一 eligible 流的
  连续 N 个结果**各施加一次：`burst_ordinal=0..N-1`，`burst_id` 固定，
  `burst_length=N`。
- `burst_active` 期间不得重新抽取新 episode；结束（ordinal==N-1）后才允许
  下一次 F0 抽样 / F4 间隔计数。
- 一个 F0 注入单位是 **episode**：`max_faults` 必须按 episode 计数，
  不能按事件计数。需要新增 `burst_episode_injected` 计数器，并明确
  `faults_injected_count` 的语义（建议：保持“事件数”，另加 episode 数；
  或在 burst 模式下明确改为 episode 数并写入事件字段）。这一点必须在
  正式计数前预注册，不能事后选。
- 每个 episode 内的事件是否各自 `fault_id` 需预注册。工作簿只强制
  `burst_id/len/ordinal`；建议每个结果仍是真实的 L0 `fault_applied`
  （各自 fault_id），但审计时以 `burst_id` 聚为一个 cluster，不能当独立
  Bernoulli 样本。
- `recurring_stuck` / `permanent_stuck` 必须完全绕过 burst 状态机；
  burst 模式下也不得进入 recurring/permanent 分支（互斥 guard）。

### 4.3 lane 子模型

- **FP05-a same-lane**：episode 内固定 `lane_offset`，每个结果可换 bit/mask。
- **FP05-b adjacent-lane**：第 i 个结果使用 `lane_offset + i`；必须在
  arm 时校验 `lane_offset + N - 1 < 128/lane_width`，越界则整个 episode
  fail-closed 跳过并计数，不能夹紧到非法 lane。
- **FP05-c cross-lane MBU**：一次写入跨多个 lane；当前
  `FaultInfo.lane_mask` 是 lane 内 64-bit，`abs_lo/abs_hi` 是 128-bit
  绝对位置。需要明确“跨 lane 的 mask”如何映射到 128-bit Vec 存储，并
  在事件中同时给出 lane 列表与绝对 mask。
- **FP05-d lane-mask burst**：预注册固定的多 lane mask；episode 内每个
  结果应用同一 mask，或按预注册规则轮换。不得根据运行结果调整。
- 触发条件“向量 op 至少有 2 个 active lane”需要在 eligibility 中可判定；
  当前 `lane_offset != 0` 只做 SIMD 限制，没有 “active lane ≥ 2” 的检查，
  需要新增真实 decode/类型判定或明确写成 proxy 边界。

### 4.4 事件字段与计数

- 每次真实施加的 `fault_applied` / `carrier_state` / 后续 L2–L5 事件都带
  `burst_id`、`burst_ordinal`、`burst_length`；`fsu_prop_fields.py` 已
  注册，无需扩共享注册表。
- 退出汇总建议输出：
  `CHAOS_BURST_EPISODES_ATTEMPTED/APPLIED/SKIPPED`、
  `CHAOS_BURST_EVENTS_APPLIED`、
  `CHAOS_BURST_RECURRING_EXCLUDED`。
  没有这些数就不能审计“1 次注入 vs N 个事件”。

### 4.5 F4 支持

FP05-F4 要求每 100,000 eligible events 触发一次、连续 2–4 个事件或
单事件 ±1 周期。当前 rate 模式只支持 F1/F2/F3；F4 需要：

- `known_freq` 增加 F4，divisor=100000；
- 明确 F4 的 “interval” 是“episode 起点之间的 eligible 间隔”，而不是
  每个事件；
- 预注册 ordinal 生成器必须按 **episode 起点** 生成，不能把 burst 内
  事件当独立 rate 事件。

## 5. 正式计数前必须通过的 gate

FP05 的正式 3-seed 计数（`FSU-FP05-F0-W3/W5/W6` 与 F4 组）在以下全部
满足前**不得启动**：

1. C++ 实现 + 四处接线完成，未知参数 fail closed。
2. `tests/test_fsu_fp05_burst.py` 全绿（规则层）。
3. 真实 pilot 的 `prop_evt` 事件流经
   `tools/fsu_fp05_burst_gate.py --stream ...` 返回 **PASS**：
   - 恰好 `max_faults` 个 episode（F0）；
   - 每个 episode `burst_id` 固定、`ordinal 0..len-1`、`len ∈ {2,3,4}`；
   - `eligible_ordinal` 连续；
   - recurring/permanent 事件数为 0（或明确排除且不计入 burst）。
4. 负例 gate：
   - 纯 `recurring_stuck` 流 → SKIP（不是 PASS）；
   - 人为改坏 ordinal/长度 → FAIL；
   - 源码无发射端但流声称 burst → FAIL。
5. workload 条件满足：W3/W5/W6 的向量 op 确实有 ≥2 active lane，且
   episode 的 2–4 个结果都来自同一向量 op 族。
6. 预注册文件记录：burst 子模型、length、lane 策略、episode 数、
   ordinal 生成器与 SHA-256；运行后不得改写主分层。
7. F4 组还需 F4 rate 语义的独立 gate（当前完全没有）。

## 6. 阻塞项

- **无 burst 发射端**：`CHAOSFPU.cc/.hh/.py` 均无 `burst_id/ordinal/length`。
- **无 F4**：构造函数只接受 F1/F2/F3 rate ordinal。
- **无跨 lane/多 lane mask 语义**：现有 lane mask 是 lane 内 64-bit。
- **无 runner/schema/validator 接线**：FP05 参数不存在。
- **gate 当前只能 SKIP/BLOCKED**：在实现落地前不能产生任何 FP05 正式计数。

## 7. 本轮真实命令与输出（gate + 相关测试）

```text
$ python3 tools/fsu_fp05_burst_gate.py
FP05 BURST GATE: SKIP
reason: CHAOSFPU source has no burst emitter; no burst evidence can exist yet
blocked: true (source has no burst emitter)
source: implemented=False missing=['burst_id', 'burst_ordinal', 'burst_length']
burst_episodes=0 burst_events=0 recurring_events=0
evidence_missing: burst_id, burst_ordinal, burst_length, stream
$ echo $?
2

$ python3 -m pytest tests/test_fsu_fp05_burst.py -q
......................                                                   [100%]
22 passed in 0.19s
```

（三文件联合运行 67 passed 与 scope 回归 14 passed 的完整输出见
`FQ08-FP08-REGRESSION.md` §7。）
