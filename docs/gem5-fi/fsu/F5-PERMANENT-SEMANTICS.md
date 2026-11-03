# F5 永久卡死语义（一个故障、多次 exposure）

> 适用：`FSU-FP06-F5-*`（结果侧 stuck-at）。实现位置
> `CHAOS/gem5/src/cpu/o3/CHAOSFPU/`。本文是实现与离线审计的合同；
> 不与 F0/F1–F4 的数字混用。
>
> 状态：代码 + host 单测 + 合成事件流审计已验证；**真实 gem5 构建与
> 正式 seed 未在本轮运行**（宿主 loadavg > 90）。构建由主 agent 在负载
> 恢复后执行。

## 1. 四个定义

| 术语 | 定义 | 证据 |
|---|---|---|
| **install（安装）** | warm-up 后的第一个 eligible event 上安装**一次**永久故障：一个固定 `fault_id`、固定 `fault_mask`、固定极性（SA0/SA1）。整次运行只允许一个安装根。 | `kind=fault_installed`（L0 根）+ `kind=carrier_state`（L1） |
| **exposure（暴露）** | 安装后每个 eligible event 都重新施加**同一个**强制极性；每次暴露都是同一 `fault_id` 的一次 exposure，**不新建 fault**。 | `kind=exposure`（旁支，层 = None） |
| **activation（激活 exposure）** | 施加前（正确值）在至少一个目标 bit 上与卡死极性不同。多 bit mask 下**任一**目标 bit 不同即 activated。 | exposure 事件 `activated=1` |
| **terminal（终局）** | 首个 activated exposure 经真实 consumer/commit 到达 L5 时为 `full`；激活但未被消费为 `exposed_unconsumed`；从未激活为 `not_activated`。 | `commit`（L5）或 F5 `chain_end` |

安装事件本身的结果也被强制施加同一 mask/polarity，因此它同时是
**exposure #1**；`exposures_total` 从安装当次开始计数（独立参考计数时
必须把安装 event 计入，否则会差 1）。

关键区别：`exposure` 是**数据暴露**；L2–L5 的“激活”仍是 FSU 既有语义——
真实 consumer 读取了被污染物理寄存器。`activated_exposure_count > 0`
**不**自动等于 L5；必须有真实 commit 见证。

## 2. 强制极性（不是 XOR）

`chaos_fsu_fields.hh` 提供纯函数（host 可单测）：

```cpp
inline bool stuckPolarityValid(int polarity);          // 0/1
inline uint64_t applyStuck(uint64_t value, uint64_t mask, int polarity);
inline bool stuckActivated(uint64_t correct, uint64_t mask, int polarity);
```

- SA0（`polarity=0`）：`value &= ~mask`，目标 bit 强制为 0。
- SA1（`polarity=1`）：`value |= mask`，目标 bit 强制为 1。
- `applyStuck` 幂等；非目标 bit 永不改变（`onlyTargetBitsChanged` 成立）。
- `stuckActivated`：SA0 看 `(correct & mask) != 0`；SA1 看
  `(~correct & mask) != 0`；`mask == 0` 永不激活。
- 旧 `recurringStuck` 仍使用 XOR；**F5 路径禁止 XOR**，只调用
  `applyStuck`。两者互斥。

## 3. CHAOSFPU 参数

| 参数 | 类型/默认 | 语义 |
|---|---|---|
| `permanentStuck` | Bool / False | 启用 F5 永久语义。要求 `fsuFreq=F5`、`probability=1.0`、显式 `faultMask`、`maxFaults=0/1`。 |
| `stuckPolarity` | Int / -1 | `-1` = 安装时从 `rngSeed` 抽取一次后固定；`0`=SA0；`1`=SA1。正式 seed 应显式固定。 |
| `f5Warmup` | UInt64 / 0 | 安装前跳过的 eligible 数。eligible ordinal `> f5Warmup` 的第一个事件安装。 |
| `f5SampleLimit` | UInt64 / 0 | **普通** exposure 样本预算；强制事件（首次 exposure、首次 activated exposure）不计入。`0` = 只保留强制事件。 |
| `f5KeepFirstLastN` | UInt64 / 0 | `0` = 前缀策略（前 `f5SampleLimit` 个）；`N>0` = 在预算内保留前 N + 后 N。 |

构造函数 fail-closed：`permanentStuck` 与 rate / `recurringStuck` /
`roundingSub` / `f3Dependent` / `fpsrSuppress` / `fmaWeighted` / `bitseg` /
显式 `eventsToSkip` 互斥；裸 `fsuFreq=F5` 而没有 `permanentStuck` 直接
panic（`countOnly` census 除外）。

### 3.1 采样预算解析

```
budget = f5SampleLimit
if f5KeepFirstLastN == 0:  keep_first = budget, keep_last = 0
else:                      keep_first = min(N, budget)
                           keep_last  = min(N, budget - keep_first)
```

强制事件始终发射：安装事件、carrier、**首次 exposure**、**首次 activated
exposure**、首个 activated exposure 的真实 L2–L5、F5 `chain_end`。
因此最大值 = `keep_first + keep_last + 2` 个 exposure 事件；
构造函数额外要求该值 + 8 < 190000，确保低于 `EVENT_CAP=200000`，
不可能静默截断。

## 4. 事件与字段

### 4.1 kind 与层级

| kind | 层级 | 说明 |
|---|---|---|
| `fault_installed` | L0 | 唯一安装根，`parent_event_id` 为空 |
| `carrier_state` | L1 | 安装载体的值/位置 |
| `exposure` | None | 同一 fault 的旁支；不作为独立 fault |
| `operand_read` | L2 | 首个 activated exposure 的真实 consumer |
| `execute` | L3 | FSU 执行 |
| `prf_writeback` | L4 | 结果写回 |
| `commit` | L5 | 首个真实架构影响（errant commit） |
| `chain_end` | None | 生命周期收口，**不是 L5**；携带容量账目 |

`activation`/`first_impact` 若被显式发射，分别映射 L2/L5；当前
CHAOSFPU 把激活/影响信息放在 `exposure`/`commit` 事件上。

### 4.2 F5 字段

| 字段 | 出现位置 | 语义 |
|---|---|---|
| `install_event` | exposure/commit/chain_end | 唯一安装事件 id（根 event_id） |
| `stuck_polarity` | 全部 F5 事件 | `0`=SA0，`1`=SA1；全程不变 |
| `fixed_mask` | 全部 F5 事件 | 与 `fault_mask` 相同的固定 lane mask |
| `first_eligible_sn` | 安装/chain_end | 安装事件 `dyn_inst_seq` |
| `exposure_id` | exposure | 该 fault 内 exposure 序号（1 起） |
| `exposure_count` | exposure/commit/chain_end | `exposures_total` 同值（总暴露数） |
| `activated_exposure_count` | exposure/commit/chain_end | 累计 activated exposure 数 |
| `first_activated_sn` | exposure/commit/chain_end | 首个 activated exposure 的 producer sn |
| `last_exposure_sn` | exposure/commit/chain_end | 最近一次 exposure 的 sn |
| `affected_sn` | exposure/commit/chain_end | exposure 事件 = 该 producer sn；commit 事件 = 首个真实影响 consumer sn |
| `correct_before` | exposure | 施加前的正确 lane 值 |
| `stuck_after` | exposure | 强制后的 lane 值 |
| `first_impact_latency` | commit/chain_end | `commit tick - first_activated_tick`（CPU ticks） |
| `sample_policy` | 全部 F5 事件 | 例如 `bounded_first_last(limit=1024,first=256,last=256)` |
| `exposures_total` | exposure/commit/chain_end | 总 exposure 数（含安装当次） |
| `exposures_sampled` | exposure/commit/chain_end | 实际写入事件流的 exposure 数 |
| `exposures_dropped` | exposure/commit/chain_end | `total - sampled`（没有采样的暴露，计数仍精确） |

`field`：单 bit mask 且完全落在一个 IEEE754 字段内时写字段名
（`sign`/`exp_hi`/…）；多 bit mask（FP06-c fixed mantissa）写
`permanent_stuck`，由 `fixed_mask` 表达真实位集合。这样
`fsu_seed_audit._field_violations` 的单 bit 规则不会被多 bit mask 误伤。

## 5. 容量策略（为什么不是数百万 L0–L5）

一个永久故障可能在数百万个结果上暴露。若每个 exposure 都建链：

- 事件数超过 `EVENT_CAP=200000`，流被 `truncated=True`；
- 一个 fault 会被审计成数万个独立 fault（每 event 新 `fault_id`）。

因此采用：

1. **一个安装根**：`fault_id` 只在安装时分配一次，之后不变。
2. **完整直接 parent 链**保留：
   `fault_installed → carrier_state → exposure(first activated) →
   operand_read → execute → prf_writeback → commit → chain_end`。
3. **所有 exposure 精确计数**（`exposures_total`），**所有 activated
   exposure 精确计数**（`activated_exposure_count`），与是否采样无关。
4. **有界样本**：`f5SampleLimit` + `f5KeepFirstLastN`，显式记录
   `sample_policy` / `exposures_total` / `exposures_sampled` /
   `exposures_dropped`。
5. **强制事件**（首次 exposure、首次 activated）永不丢弃。
6. 仅**首个 activated exposure** 获得 L2–L5 真实传播链；后续 exposure
   只计数/采样，不调用 `noteFaultApplied`，不新建 fault。

### 5.1 已知边界

- 若首个 activated exposure 从未被真实 consumer 读取，即使后续某个
  activated exposure 被消费，本实现也不会补建第二条 L2–L5 链；终局诚实
  记为 `exposed_unconsumed`（不是 `full`）。这是“只为首个 activated
  exposure 建链”的预定语义，不做结果驱动的补链。
- 被丢弃的 exposure 只保留精确计数（`exposures_total` /
  `activated_exposure_count` / `exposures_dropped`），不保留逐条值；
  需要逐条值时提高 `f5SampleLimit` 并重新预注册。
- `first_impact_latency` 是 CPU tick 差（`commit tick - first activated
  tick`），不是周期或指令数。

建议正式运行参数：`permanentStuck=true`、`f5SampleLimit<=1024`、
`f5KeepFirstLastN<=256`（现有 gate/seed manifest 即此配置），事件量远低于
200000。若需更大样本，必须同步提高审计器的路径剪枝/上限，并在运行前
预注册。

审计器的路径枚举会剪掉**无子节点的旁支 exposure 叶子**，因此数万条
非激活 exposure 不会耗尽 `MAX_PATHS`，也不会遮住真实激活链。实测
50,008 条事件（50,000 条旁支 exposure）的审计耗时约 7 秒，
`fault_count=1`、`path_len=8`、`violations=[]`。即使接近
`f5SampleLimit≈190000` 仍可审计（约 27 秒），但正式 seed 仍建议
`<=1024`，证据更易读。

## 6. 审计规则（`tools/fsu_chain_check.py`）

对每个 `fault_id`：

1. 根可以是 `fault_applied`（F0–F4）或 `fault_installed`（F5）；
   两者混用、或多个 `fault_installed` 根 → violation。
2. `exposure` 必须有 parent；`install_event` 必须指向该 fault 的根；
   `fault_id` 必须与根一致。
3. 所有 exposure 的 `fixed_mask`/`stuck_polarity` 必须与安装值一致；
   `exposure_id` 不得重复。
3b. 审计器用 `fixed_mask`/`stuck_polarity` 对每条 exposure 重放
   `applyStuck(correct_before)`，校验 `stuck_after`、非目标 bit 不变、
   `activated` 标志；任何不一致都是 violation（从事件流本身证明是强制
   stuck-at，而不是 XOR/随机）。
4. 只有 exposure、没有安装根的组**不进入** `faults`/`fault_count`；
   记为 `orphan_exposure_groups` / `exposure_without_fault_installed_root`
   并阻断 `admitted`。
5. `chain_end`（带 `exposures_total` 的 F5 收口）必须存在，且：
   - `total == sampled + dropped`；
   - 未截断时 `sampled == 流内 exposure 事件数`；
   - `activated_exposure_count >= 流内 activated=1 的事件数`；
   - `activated_exposure_count > 0` 时，必须存在首个 activated 事件，
     且其 `dyn_inst_seq == first_activated_sn`；
   - `first_eligible_sn == 安装事件 dyn_inst_seq`；
   - `install_event`/`fixed_mask`/`stuck_polarity` 与根一致。
6. 若存在 L5 commit 且 `activated_exposure_count > 0`，最佳直接 parent
   链**必须经过**首个 activated exposure；绕开它 → violation。
7. `chain_end` 不得声称 `committed` 而没有 L5 见证；不得声称
   `not_activated` 而 `activated_exposure_count > 0`。
8. 非 activated 的 exposure 叶子不参与路径枚举（避免 `MAX_PATHS`
   被数万旁支耗尽）；它们仍完整保留在 `off_chain_event_ids` 与计数中。
9. `truncated=True` 一律阻断认证（`truncated_stream`）。

## 7. 与 F0 / F1–F4 的区别

| 频率 | 事件 | 次数 | fault_id | 语义 |
|---|---|---|---|---|
| F0 | 单次 `fault_applied` | 1 | 1 个 | 单点故障 |
| F1/F2/F3 | 按显式 eligible ordinal 的 `fault_applied` | 多个独立故障 | 每故障 1 个 | rate 语义 |
| F4 | 由对应速率模型定义 | — | — | 非本轮活跃频率 |
| **F5** | **1 个 `fault_installed` + N 个 `exposure`** | **1 个永久故障、多次暴露** | **始终 1 个** | **stuck-at 持久缺陷** |

F5 不使用 interval/jitter/ordinal，也不做概率抽样；`probability` 必须为
1.0，warm-up 之后每个 eligible 都是 exposure。

## 8. FP06 子模型

| 子模型 | 状态 | 说明 |
|---|---|---|
| FP06-a | 支持 | 结果位 SA0；`stuckPolarity=0` |
| FP06-b | 支持 | 结果位 SA1；`stuckPolarity=1` |
| FP06-c | 支持 | 固定 mantissa mask（可多 bit）；`faultMask` 固定，`field=permanent_stuck` |
| FP06-d | **MISSING** | multiplier partial-product proxy 仍未实现；**不得用最终结果位冒充**。需要真实部分积/中间结果观测点，当前 gem5 ARM FP 功能模型不可达。 |

## 9. 合成事件样例（来自 `tests/test_fsu_chain_check.py::f5_full()`）

一条合法 F5 链的关键事件（省略空字段）：

```
# L0 root
kind=fault_installed event_id=0 parent_event_id= fault_id=1
  dyn_inst_seq=100 first_eligible_sn=100 fault_mask=0x20 fixed_mask=0x20
  stuck_polarity=1 field=mant_lo observed
# L1 carrier
kind=carrier_state event_id=1 parent_event_id=0
# exposure #1: correct bit5=1, SA1 -> exposed-but-not-activated
kind=exposure event_id=2 parent_event_id=1 exposure_id=1
  dyn_inst_seq=101 install_event=0 activated=0
  activated_exposure_count=0 fixed_mask=0x20 stuck_polarity=1
# exposure #2: correct bit5=0, SA1 -> first activated exposure
kind=exposure event_id=3 parent_event_id=1 exposure_id=2
  dyn_inst_seq=102 install_event=0 activated=1
  first_activated_sn=102 activated_exposure_count=1
# real L2-L5, parented through the FIRST ACTIVATED exposure (event 3)
kind=operand_read   event_id=4 parent_event_id=3 activated=1
kind=execute        event_id=5 parent_event_id=4
kind=prf_writeback  event_id=6 parent_event_id=5
kind=commit         event_id=7 parent_event_id=6 detection_layer=L5
                    outcome=errant_commit
# lifecycle terminus, NOT L5
kind=chain_end event_id=9 parent_event_id=7 install_event=0
  exposures_total=3 exposures_sampled=2 exposures_dropped=1
  activated_exposure_count=1 first_activated_sn=102
  sample_policy=bounded_first_last(limit=4,first=2,last=2)
  terminal=committed outcome=committed
```

审计结果：`fault_count=1`、`terminal=full`、`layers=L0,L1,L2,L3,L4,L5`、
`admitted=true`；exposure #1 与任何未采样的 exposure 只在
`off_chain_event_ids` / 计数中出现，不会被当成新 fault。

## 10. 验证

```bash
g++ -O0 -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
    tests/unit/chaos_fsu_f5_test.cc -o /tmp/fsu_f5_test && /tmp/fsu_f5_test
# -> chaos_fsu_f5: all checks passed

python3 -m pytest tests/test_chaos_fsu_f5_cpp.py \
    tests/test_fsu_chain_check.py tests/test_chaos_fsu_fields_cpp.py -q
# -> 40 passed
```

真实 gem5 构建（`scons -j16 build/ARM/gem5.opt`）与 F5 gate/seed 由主
agent 在负载恢复后执行；本文件不声称这些运行已完成。

## 11. 集成注意（owner 边界）

- `CHAOSPropagation.hh` 的 `PROP_EVT_EXT_FIELDS` 已包含本文全部 F5 字段
  （主 agent 已加入）；否则 `notePropEvt` 会丢弃未知键。
- `configs/se/ooo_proxy.py` 已暴露 `--fpu_permanent_stuck` /
  `--fpu_stuck_polarity` / `--fpu_f5_warmup` / `--fpu_f5_sample_limit` /
  `--fpu_f5_keep_first_last_n`。
- **`tools/fsu_seed_runner.py` 尚未把 manifest 的 `injector.fpu_mode`
  转成上述 CLI**；F5 正式运行前必须由该文件 owner 补齐。
- **`tools/fsu_seed_audit.py` 仍只把 `fault_applied` 当 L0 根**；F5 运行前
  必须让它：
  1. 接受 `fault_installed` 作为 L0 根（`scheduled` 计数仍是 1）；
  2. 把 `exposure` 排除出独立 fault 计数；
  3. 对 F5 用 `stuck_after == applyStuck(correct_before, fixed_mask,
     stuck_polarity)` 校验，而**不是** `before ^ after == mask`
     （SA0/SA1 下“正确位已是该极性”的 exposure 不会翻转任何 bit）；
  4. 把 `permanent_stuck` 加入 `MODE_FIELDS`，多 bit FP06-c mask 不做
     `fault_mask == 1<<bit` 的单 bit 校验（由 `fixed_mask` 表达）。
- F5 运行时不要传 `--fpu_events_to_skip`（默认哨兵即可）；构造函数会对
  非哨兵值 panic。
