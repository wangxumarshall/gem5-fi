# FP05 burst 实现：episode 语义、事件契约与门禁

日期：2026-11-05。本文记录 **已落地** 的 FP05 真实 burst 实现（不再是设计稿，
也不再返回 SKIP）。实现范围是 F0；F4 的 interval 语义在构造期 fail closed
（见 §7）。本文所有代码引用均对应本提交的真实行号。

## 1. 结论先行

| 项 | 状态 |
|---|---|
| 发射端 | `CHAOSFPU` 新增 `burstMode/burstLength/burstLaneStep/burstLaneMask/burstIdBase` 参数与真实状态机 |
| 纯协议层 | `CHAOS/gem5/src/cpu/o3/CHAOSFPU/chaos_fsu_burst.hh`（host g++ 单测） |
| PROP 事件 | 每个 burst 结果带 `burst_id/burst_ordinal/burst_length/burst_mode/burst_lane_*`、`attempted=1/applied=1`；episode 收口另行发射 `kind=burst_end` |
| F0 计数单位 | **一个 episode = 一次 F0 注入**；`maxFaults` 限制 episode 数，且构造期强制 burst 模式 `maxFaults==1` |
| 与 recurring/permanent 的关系 | 构造期互斥 panic；recurring/permanent 事件**不可能**被标成 burst |
| runner/schema/审计 | `configs/se/ooo_proxy.py`、`tools/runner.py`、`tools/fsu_seed_runner.py`、`tools/fsu_suite.py`、`schemas/manifest.schema.json`、`tools/manifest_validate.py`、`tools/fsu_prop_fields.py`、`tools/fsu_seed_audit.py` 全部接通 |
| 正式计数 | 未跑 gem5、未改 `runs/`、未改 runids/index 计数；需要主 agent 执行 §9 的 gem5 gate |

## 2. 协议依据（原文）

1. **burst 定义**：`docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控-03-位置x模型矩阵.md:43`
   > “在2–4个连续eligible结果上污染同lane或相邻lane；不将burst事件当独立Bernoulli样本”

2. **F0 频率**：`...-07-展开执行矩阵.md:156-158`（FSU-FP05-F0-W3/W5/W6）
   > “每次运行只注入1次；warm-up后在本模型eligible event中均匀抽样”
   同一行必写字段：
   > “burst_id/len/ordinal、lane mask、每结果hash、扇出与cluster结局”

3. **F0 注入单位**：`docs/gem5-fi/fsu/FP05-BURST-PREP.md:26`
   > “一次 F0 注入 = 一个 burst episode，不是 episode 内的每个事件”

4. **F4**：`...-07-展开执行矩阵.md:159-161`
   > “每100,000个eligible events触发一次，连续污2–4个事件或单事件±1周期”
   本条要求的是 **episode 起点间隔**，与 F1–F3 的 per-event ordinal 语义不同；
   本轮未实现，构造期拒绝（§7）。

由 1+2+3 得到本实现预注册的计数口径：F0 的“注入 1 次”指一个 2–4 事件
episode；episode 内每个事件仍是一个真实 L0 fault（各自 `fault_id`），但审计按
`burst_id` 聚为一个 cluster，不能当独立 Bernoulli 样本。该口径已在
`FP05-BURST-PREP.md:26` 预注册，且本轮**没有**修改 runids/index 的正式计数。

## 3. episode 定义与状态机

一个 burst episode：

- **起点**：warm-up 后、在 burst-eligible 流中按 F0 固定 uniform skip
  （`eventsToSkip`，由 driver 的 countOnly 普查生成）选中的第一个 eligible
  结果；`burst_id = burstIdBase + episode_index`。
- **成员**：从起点开始，**连续 N 个 eligible 结果**（N = `burstLength ∈ {2,3,4}`）。
- **ordinal**：成员的 `burst_ordinal = 0..N-1`，严格递增、不重复。
- **结束**：ordinal 达到 N 时发射 `kind=burst_end`、`burst_end_reason=completed`。
- **不可重入**：episode 活跃期间不再抽样；结束后才可能开始下一 episode
  （F0 由 `maxFaults==1` 保证单次运行只有一个 episode）。

非 eligible 事件（opClass 不匹配、无 FP/vector dest、decode 不满足
“NEON vector ≥2 active lane”、lane 几何不足）**不消耗 ordinal、不推进
episode**；它们只是被跳过。

实现位置：

- 纯状态机/几何：`CHAOS/gem5/src/cpu/o3/CHAOSFPU/chaos_fsu_burst.hh:143`
  （`burstLaneGeometryValid`）、`:198`（`BurstEpisodeTracker`）、
  `:269`（`burstAccountingConserved`）。
- 真实选择/注入：`CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.cc:705`
  （burst episode selector）。
- episode 收口：`CHAOSFPU.cc:1972`（`emitBurstEnd`）、`CHAOSFPU.cc:2023`
  （`flushBurstAtExit`）。

## 4. 固定参数 vs 允许变化参数（预注册）

固定（整个 run / episode 不变，构造期校验）：

| 参数 | 取值 |
|---|---|
| `burst_mode` | `same_lane` / `adjacent_lane` / `cross_lane_mbu` / `lane_mask` |
| `burst_length` | 2 / 3 / 4（1 和 ≥5 一律 panic） |
| `lane_width` / base lane | 构造期 `burstLaneGeometryValid` 校验 |
| `burst_lane_step` | `adjacent_lane` 的每事件步长（>0） |
| `lane_mask` 子模型的 mask | `burstLaneMask` 或显式 `faultMask`，episode 内不随结果变化 |
| episode 数（F0） | 1（`maxFaults==1`，构造期强制） |

允许变化（不得改变 id/length）：

| 参数 | 说明 |
|---|---|
| `burst_ordinal` | 0..N-1，逐 eligible 结果递增 |
| 事件 lane | `adjacent_lane`：base + ordinal×step；其余：固定 base |
| 事件 bit | 未 pin 显式 mask 时，`same_lane/adjacent_lane` 每个结果独立抽 1 bit；`lane_mask` 固定多 bit mask |
| `burst_id` | 每个 episode 单调递增，从不复用 |

## 5. 四个子模型

| 子模型 | 实现 |
|---|---|
| FP05-a `same_lane` | 每个结果固定 base lane，可换 bit/mask（`CHAOSFPU.cc:705` 之后统一 mask 构造） |
| FP05-b `adjacent_lane` | 第 i 个结果 lane = base + i×step；episode arm 时校验 `base + span ≤ lanes`，越界整段 fail closed，绝不夹紧 |
| FP05-c `cross_lane_mbu` | 每个事件在 base lane 与 base+1 lane **各写同一 in-lane mask**；`lane_mask` 字段写合并后的 128-bit 绝对 mask（`CHAOSFPU.cc` VecReg 注入分支） |
| FP05-d `lane_mask` | 预注册多 bit mask 原样施加到同一 lane 的每个结果 |

trigger 条件“向量 op 至少有 2 个 active lane”在 eligibility 中真实判定：
必须 `isSimdOpClass`、`VecRegClass` dest、真实 decode 为 `neon_vector`、
`decoded_lanes ≥ 2` 且 `lane_offset + span ≤ decoded_lanes`
（`CHAOSFPU.cc` burst eligibility 块）。decode 不可靠时一律不 eligible。

## 6. attempted / applied / activated

- `attempted`：进入 episode 选择、拿到 ordinal 的 eligible 事件数。
- `applied`：真实改写目的 VecReg cell 的事件数。burst 模式下若某个已选中的
  ordinal 找不到可写 VecReg dest，直接 **panic**（fail closed）：否则声明的
  2–4 长度会与事件流不一致。
- `activated`：该 faulted 物理 cell 后来被真实 consumer 读到的 burst 事件数；
  在 `noteConsumerExecute` 中累加，并把 burst 身份带到 L2–L5。
- 每个事件自身仍发射 `fault_applied` + `carrier_state`，带 `value_hash/
  after_hash`、`event_id`；episode 收口 `burst_end` 与 fault log 的
  `CHAOS_BURST_*` 汇总给出 run 级守恒。

守恒由 `chaos_fsu::burstAccountingConserved`
（`chaos_fsu_burst.hh:269`）定义，并写入 `burst_end.burst_accounting_ok`：

```
events_attempted >= events_applied
events_applied   >= events_activated
events_applied   >= events_squashed
episodes_attempted == episodes_applied + episodes_lane_rejected
episodes_attempted == episodes_completed + episodes_short + episodes_lane_rejected
```

## 7. 结束条件与显式记录

| 情况 | 行为 | 事件记录 |
|---|---|---|
| 正常完成（ordinal == N） | `finish()`，之后不再注入 | `kind=burst_end`, `burst_end_reason=completed` |
| 运行提前结束/尾部 eligible 不足 | 退出 flush 中把活跃 episode 记为 short，**不改写声明长度** | `kind=burst_end`, `burst_end_reason=run_exit`, `burst_episode_events=<实际>` |
| 预注册 lane 几何装不下 N | 整段拒绝，且本 run 不再尝试（`tracker.disabled`） | `kind=burst_end`, `burst_end_reason=lane_geometry`, `applied=0` |
| burst 事件被 squash | **不终止 episode**（episode 定义在“连续 eligible 执行结果”，不是 committed 结果）；每个被 squash 的结果单独记录 | `kind=squash`, `outcome=burst_event_squashed`，带 burst 字段 |
| 未被 consumer 读取 | 退出时按普通 L0 终局记录 | `kind=not_activated`，带 burst 字段 |

`run_exit` 的短 episode 会让 `tools/fsu_fp05_burst_gate.py --require-end`
返回 **FAIL**（声明长度 ≠ 实际事件数），不会把截断流误判为 PASS。

**recurring/permanent 不能冒充 burst**：

- 构造期 `burst_mode` 与 `recurringStuck/permanentStuck` 等互斥并 panic
  （`CHAOSFPU.cc:244` 之后的校验块）。
- `fault_installed`/`exposure` 事件不带任何 `burst_*` 字段；gate 的
  `recurring_not_burst_tagged` 检查会拒绝被误标的 recurring 流。
- `recurring_result_stuck` 的“同 mask 每 event 重复”仍只走旧分支，没有
  `burst_end`，也没有 episode 计数。

## 8. 多来源 consumer 汇合

同一 consumer 指令可能同时读多个被 burst 污染的 vector cell。
`noteConsumerExecute`（`CHAOSFPU.cc:2600` 起）先预扫描所有匹配的 burst 源：

- 每个源各自发射自己的 L2 `operand_read`（以及 FP consumer 的 L3/L4）；
- 每个事件带 `burst_merged_sources=<n>` 与 `burst_source_fault_ids=<fid,...>`；
- 第一条链作为该 consumer 的 L4/L5 主 witness，commit 事件同样携带合并计数与
  source id 列表；
- 合并计数与 source id 数量不一致时，strict gate 直接 FAIL。

因此不会静默只保留第一个源。

## 9. 门禁命令

### 9.1 host（已在本轮实际运行）

```bash
python3 -m pytest tests/test_fsu_fp05_burst.py tests/test_chaos_fsu_burst_cpp.py -q
# 33 passed

python3 -m pytest tests/test_fsu_suite.py tests/test_fsu_seed_runner.py \
  tests/test_fsu_seed_audit.py tests/test_fsu_chain_check.py \
  tests/test_lsu_prop_fields.py tests/test_fsu_seed_plan_schema.py -q
# 148 passed, 43 skipped
```

gate 自身：

```bash
python3 tools/fsu_fp05_burst_gate.py
# FP05 BURST GATE: SKIP / source implemented=True missing=[] / evidence_missing: stream / rc=2
```

### 9.2 需要主 agent 在 gem5 侧执行

> 先做 countOnly 普查拿到 `N_eligible` 与 `skip=chaosPickSkip(seed,N)`，再跑
> 注入 pass。以下命令使用仓库根 `build/ARM/gem5.opt`，并在每次运行后执行
> strict gate。`<W>` 取 W3/W5/W6 对应 workload；`reg_class vec` 与 SIMD
> opClass 用于保证目的操作数是 VecReg。

```bash
OUT=/tmp/fp05-pilot/<W>-seed1
build/ARM/gem5.opt --outdir=${OUT}/census configs/se/ooo_proxy.py \
  --cmd workloads/<W> --cpu O3 \
  --chaos_fpu --fpu_count_only --fpu_max_faults 1 \
  --fpu_burst_mode same_lane --fpu_burst_length 3 \
  --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 \
  --fpu_reg_class vec --fpu_op_classes SimdFloatAdd,SimdFloatMult,SimdFloatMultAcc \
  --fsu_model FP05 --fsu_freq F0 --fsu_submodel FP05-a --fsu_load <LOAD> \
  --chaos_propagation --prop_run_id FSU-FP05-F0-<W>-pilot \
  --prop_sample_run_id s1
# 期望：fpu_injections.log 中 CHAOS_ELIGIBLE_COUNT=N（>= 1 个 burst 起点）

SKIP=$(python3 -c "
import sys; sys.path.insert(0,'tools')
import fsu_seed_runner as R
text=open('${OUT}/census/fpu_injections.log').read()
n=R.parse_eligible_count(text)
assert n >= 0, 'census did not emit CHAOS_ELIGIBLE_COUNT'
print(R.chaos_pick_skip(1, n))")

timeout 1800 build/ARM/gem5.opt --outdir=${OUT}/inject configs/se/ooo_proxy.py \
  --cmd workloads/<W> --cpu O3 \
  --chaos_fpu --fpu_max_faults 1 --fpu_events_to_skip ${SKIP} \
  --fpu_burst_mode same_lane --fpu_burst_length 3 \
  --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 \
  --fpu_reg_class vec --fpu_op_classes SimdFloatAdd,SimdFloatMult,SimdFloatMultAcc \
  --fsu_model FP05 --fsu_freq F0 --fsu_submodel FP05-a --fsu_load <LOAD> \
  --chaos_propagation --prop_run_id FSU-FP05-F0-<W>-pilot \
  --prop_sample_run_id s1

python3 tools/fsu_fp05_burst_gate.py \
  --stream ${OUT}/inject/prop_evt.txt.gz \
  --require-end --expected-episodes 1
# 期望：PASS，rc=0；burst_episodes=1，burst_events=3；
# 所有 ordinal=0..2；burst_end_reason=completed；burst_accounting_ok=1；
# recurring_events=0。
```

**判据（全部满足才算 F0 正式候选）**：

1. census `CHAOS_ELIGIBLE_COUNT ≥ 1`，且 burst-eligible 流确实含 ≥2 lanes 的
   vector op（`CHAOS_ELIGIBLE_OPCLASS SimdFloat*` 计数 > 0）。
2. inject：`fpu_injections.log` 的 `CHAOS_BURST_EPISODES_COMPLETED=1`、
   `CHAOS_BURST_EPISODES_SHORT=0`、`CHAOS_BURST_EVENTS_APPLIED=3`、
   `CHAOS_BURST_ACCOUNTING_OK=1`。
3. `prop_evt.txt.gz` 中恰好 1 个 `burst_id`，3 个 `fault_applied` 事件，
   ordinal 连续 0..2，`eligible_ordinal` 连续，`burst_end_reason=completed`。
4. strict gate exit 0。strict 模式还要求每个 applied burst 结果都有显式传播
   终局：`operand_read activated=1`（被真实 consumer 读）、`squash`、或
   `not_activated`；缺失即 FAIL。多来源合并事件（`burst_merged_sources>1`）
   必须给出数量相等的真实 `burst_source_fault_ids`。
5. 对长度 2/3/4 与 `same_lane/adjacent_lane/lane_mask`（FP05-a/b/d）各至少
   一个 pilot；`cross_lane_mbu` 需 lane_width=64 且 base lane=0（128-bit 只有
   2 个 64-bit lane）。
6. 负例：
   - 纯 recurring/permanent 流（无 burst 字段）→ gate `SKIP`（不是 PASS）；
   - 人为删掉一个 ordinal 或改坏 burst_length → `FAIL`；
   - 人为截断成 2/4 → `FAIL`（`run_exit`/长度不符）；
   - 人为加第二个 burst_id → `FAIL`（`expected-episodes=1`）。

**超时**：countOnly 与注入 pass 各 1800s（W5/W6 可放宽到 3600s）；每次只跑
一个 gem5 进程，遵循 ≤4 并发上限。

## 10. 已知限制 / 风险

1. **F4 未实现**：`--fsu_freq F4` + burst 在构造期 panic（明确报错，不半路由）。
   workbook 的 F4 interval 语义需要 episode-start 间隔生成器，属于独立 gate。
2. **只支持 F0 单 episode**：`maxFaults` 在 burst 注入 pass 强制为 1；这是
   “单次运行不意外启动第二个 episode”的硬保证。多 episode 仅用于离线规则
   测试（synthetic stream），发射端不支持。
3. **cross_lane_mbu 几何**：128-bit Vec + 64-bit lane 只有 2 lane，因此 base
   必须为 0；更大向量宽度（>128-bit）当前不支持。
4. **squash 不终止 episode**：这是预注册语义（eligible 执行结果 vs committed
   结果）。若后续工作簿要求“以 commit 为准”，需要改口径并重新预注册，不能
   在结果出来后改。
5. **chain 审计的 admitted/certified**：`fsu_chain_check` 仍要求每个 fault 有
   L5；未被 consumer 读取的 burst 事件会走 `not_activated`。正式 workload 必须
   保证 burst 结果被真实 consumer 消费，否则 seed audit 的
   `所有 fault 均 admitted/certified` 会失败（这是诚实失败，不是本实现伪造）。
6. **未跑 gem5**：本提交只验证了 host 纯逻辑/gate/接线；C++ 构建与真实事件流
   证据由主 agent 在 §9 执行。
