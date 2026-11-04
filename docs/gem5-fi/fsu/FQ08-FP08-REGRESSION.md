# FQ08 / FP08 修复回归（离线契约 + 既有 gate 证据复核）

日期：2026-11-04。范围：巩固 FQ08-b/FQ08-c 与 FP08 的修复回归。
本任务**没有**运行 gem5、没有 scons 构建、没有新增 RunID/seed；文中所有
“真实运行”数字都来自仓库中**已经存在**的 gate 原始日志，并逐条注明路径。
新增内容只有 pytest 契约/离线行为测试与本文档。

## 0. 测试分层（不要把源码 grep 当成运行行为证据）

| 层 | 文件 / 测试 | 证明什么 | 不能证明什么 |
|---|---|---|---|
| 源码契约 | `tests/test_chaos_fsu_fq08_regression.py`、`tests/test_chaos_fsu_fp08_contract.py` 中的源码断言 | 分支顺序、计数位置、事件字段、早退路径形状 | 代码在 gem5 中真的跑了 |
| 离线行为 | 同文件内的 `*_behavior` / `test_lifecycle_*`，以及 FP08 的 `parse_fp08_summary` | 纯模型规则（counter 分离、victim 选择、generation/sequence 顺序、守恒式）在具体输入下的结果 | C++ 与 Python 复刻逐位等价；真实硬件/gem5 行为 |
| 既有真实证据 | `runs/fsu-gates/FQ08-*`、`runs/fsu-gates/FP08-*` 日志 | 修复后曾经在真实 gem5 中观测到的计数/事件 | 本轮重新运行；新的 seed |
| 仍需真实仿真 | 本文 §3/§5 的缺口 | — | 不得用契约测试冒充 |

`tests/unit/chaos_iq_lifecycle_test.cc` 存在且覆盖同一组语义，但按任务约束
**本任务没有编译它**（不运行 g++），只检查其覆盖点；等价规则在 Python 中
离线复算。`tests/test_chaos_iq_lifecycle_cpp.py` 同样**未运行**（它会调用
g++）。

## 1. FQ08-b：计数与施加分离

### 1.1 源码契约（已由新增 pytest 断言）

`CHAOSIQ::shouldWrongSourceWake()` 只做 ATTEMPT 门控：

- 先按 `fi_mode != Mode::SrcReadyBitflip` 早退，其他模式完全不受影响；
- 新的 producer wake 入口用 `chaos_iq_lifecycle::abortPendingAttempt()` 把
  上一次未找到 victim 的 attempt 记成 `no_victim`；
- 门控命中只 `beginAttempt()` + `iq_counts.attempted++`，**返回 false**；
- 该函数体内没有 `faults_injected_count++` / `iq_counts.applied++`。

真正施加在 `CHAOSIQ::maybeApplyWrongSourceWake()`：

- 顺序是 `chooseWrongSlot()` → `markSrcRegReady()` → `faults_injected_count++`；
- `chooseWrongSlot()` 返回 `<0` 时直接返回，不计数、不消耗预算；
- 成功后 `ws_attempt.pending = false` 并登记 one-shot 重复唤醒抑制；
- APPLIED 日志带真实 victim 身份与状态变化：`victim_sn`、`victim_pc`、
  `victim_op_class`、`victim_src_slot/phys/class/flat/generation`、
  `wrong_of_chain_flat`、`producer_sn`、`producer_wake_tick`、
  `ready_regs X -> Y / N`。

计数器定义（`chaos_iq_lifecycle.hh::Counters`）是分离的
`eligible / attempted / applied / activated / no_victim`；`noteApplied()`
独立递增 `applied` 与 `activated`；`abortPendingAttempt()` 只递增
`no_victim`。退出时 `CHAOS_IQ_COUNTS ...` 全部输出，末尾保留
`faults_injected: <n>` 供既有解析器使用。

### 1.2 离线行为（Python 复刻，规则验证）

`tests/test_chaos_fsu_fq08_regression.py` 覆盖：

- 无 victim：`applied=activated=0`、`no_victim+1`、`pending=False`；
- 只被唤醒链本身：不能当 victim；
- 正例：选到“不在本链”的未就绪源槽，`ready_regs 0->1 / 2` 时 applied
  但未 activated；`ready_regs 1->2 / 2` 时 activated；
- activated 是 applied 的严格子集；
- squashed / 已发射 / 全 ready 的 victim 被拒绝；
- 连续三次 no-victim 不消耗预算，第四次有 victim 恰好消耗 1；
- 重复真实唤醒抑制是 one-shot（不同 sn/tid/chain 不误伤）。

### 1.3 既有真实 gate 证据（只读复核）

正例 `runs/fsu-gates/FQ08-B-POS4/iq_injections.log`：

```text
... APPLIED wrong-source ready bit, tid=0, victim_sn=311, victim_pc=0x40c214,
victim_op_class=MemWrite, class=int, victim_src_slot=1, victim_src_phys=84,
victim_src_class=integer, victim_src_flat=84, victim_src_generation=2,
wrong_of_chain_flat=83, producer_sn=309, ..., ready_regs 0 -> 1 / 2 ...
CHAOS_IQ_COUNTS mode=src_ready_bitflip, eligible=96, attempted=91, applied=1,
activated=0, no_victim=90, ..., faults_injected: 1
```

负例 `runs/fsu-gates/FQ08-B-POS/iq_injections.log`（FP 负载，无合法 victim）：

```text
CHAOS_IQ_COUNTS mode=src_ready_bitflip, eligible=174038, attempted=174033,
applied=0, activated=0, no_victim=174033, ..., faults_injected: 0
```

另有 `FQ08-B-POS2`（81924 attempted / 0 applied / 81924 no_victim）与
`FQ08-B-POS3`（1157 attempted / 0 applied / 1157 no_victim）同形状。
这三份负例是“attempted 很大但 applied=0、预算不消耗”的直接证据。

**FQ08-b 回归结论**：源码契约 + 离线规则 + 既有正/负真实日志三者一致，
未发现本轮修复破坏其他模式（见 §4）。

## 2. FQ08-c：延迟唤醒生命周期

### 2.1 源码契约

- `CHAOSIQ::shouldDelayWake()` 永久 `return false`：调用方的
  `o3::DelayedWakeEvent` 路径不可达（该事件无 squash/generation 校验）。
- `CHAOSIQ::shouldOmitWake()` 在 wake_phase 命中时用
  `snapshotWakeStamp()` 取**值快照**并 `new DelayedWake(...)`，然后返回
  true 丢弃本次广播。
- `CHAOSIQ::DelayedWake` 只持有 `o3::DynInstPtr inst`（引用计数保证
  producer 对象存活）与 `chaos_iq_lifecycle::WakeStamp stamp`（seqNum、
  tid、每个目的物理寄存器的 flat + allocation generation），**不持有**
  `InstructionQueue*` 或裸指令指针；事件构造用 `AutoDelete`。
- `DelayedWake::process()` 先 `classifyWake()` 再决定是否
  `wakeDependents(inst)`。顺序固定：
  1. `ignore_no_inst`
  2. `ignore_identity`（seqNum/tid）
  3. `ignore_squashed`
  4. 目的寄存器个数不一致 → `ignore_identity`
  5. 任一目的寄存器 generation 变化 → `ignore_generation`
  6. 才 `Fire`
- 被忽略的事件由 `noteDelayedWakeIgnored()` 记录
  `IGNORED reason=...`，每行带 `faults_injected: <n>`，不会被 runner 当
  第二次注入。
- 重放保护：`replaying_delayed_wake` 在调用 `wakeDependents()` 期间为真，
  嵌套 wake 不再触发新注入。退出汇总输出
  `delayed_scheduled/fired/ignored_*`。
- 范围说明：工作簿的 FQ08-d“duplicate（重复一次 wakeup）”不在本次
  FQ08-b/c 修复范围内；本任务验证的是“延迟事件重放不二次注入”与
  “被注入源的 genuine wake 只抑制一次”，不是 FQ08-d 的完整语义。

### 2.2 离线行为

Python 复刻覆盖：正常 Fire；squash 忽略；单/多目的寄存器 generation
变化忽略；seqNum/tid/目的个数不一致忽略；no-inst 忽略；identity 先于
squash 判定；旧事件在槽位复用后不能唤醒新 owner；每个事件恰好推进一个
计数器；squash → 复用 → 另一正常事件仍可 Fire。另检查 C++ host 单测源码
覆盖了同一组检查名（未编译）。

### 2.3 既有真实 gate 证据

`runs/fsu-gates/FQ08-C-GATE/iq_injections.log`（`branch_mispred`，
wake_phase，phase_offset=2）：

```text
Tick: 398475, ... mode=wake_phase, completed_sn=105, phase_offset=+2,
delayed_event=scheduled ..., delayed_ignored_squashed=1, faults_injected: 1
Tick: 399245, ... mode=wake_phase, IGNORED reason=ignore_squashed,
completed_sn=105, delayed_fired=0, delayed_ignored_squashed=1,
delayed_ignored_generation=0, delayed_ignored_identity=0, faults_injected: 1
CHAOS_IQ_COUNTS mode=wake_phase, eligible=6, attempted=1, applied=1,
activated=0, no_victim=0, pending_attempt=0, delayed_scheduled=1,
delayed_fired=0, delayed_ignored_squashed=1, ... faults_injected: 1
```

**FQ08-c 回归结论**：squash 路径有真实 gem5 证据；延迟事件在 squash 后
被安全忽略，没有重入 `wakeDependents`，没有 abort/SIGSEGV。
**缺口**：`ignore_generation` 与 `ignore_identity` 目前只有离线规则测试，
还没有真实 gate 日志观测到（见 §5）。

## 3. FP08：fpsr_suppress / rounding_sub

### 3.1 定义

| 计数 | 路径 | 含义 |
|---|---|---|
| `fpsr_attempted` | fpsr_suppress | 通过窗口/模式/概率门控后进入 fpsr 代理分支的事件数 |
| `fpsr_applied` | fpsr_suppress | 同一分支内“模型 flag 被清除”的事件数（代理定义） |
| `suppressed_count` | fpsr_suppress | 与 applied 相同的事件数；仅该模式写入 |
| `rounding_attempted` | rounding_sub | 进入 rounding 代理分支的事件数（含随后找不到可写目的寄存器/非有限值的情况） |
| `rounding_applied` | rounding_sub | 真正完成 1-ULP nudge 并调用 `noteFaultApplied()` 的事件数 |

**守恒关系**：

- fpsr：三个 `++` 在同一个无条件块内，因此
  `attempted == applied == suppressed`（构造性守恒）。
- rounding：`attempted >= applied`；`applied` 只在 `if (okr)` 内递增，
  且同一分支递增 `faults_injected_count`、调用 `noteFaultApplied()`。
  “attempted 但未 applied”目前没有细粒度 reason 计数（见 §5）。

### 3.2 事件契约

- fpsr 早退：`emitFsu("suppress", 0, ~0ULL, kv)`，kv 含
  `field=fpsr_suppress`、`attempted/applied/suppressed=1`、
  `reason=fpsr_not_architecturally_modeled`、
  `injection_site=fpsr_suppress_proxy`、`hook_version=1`、`dyn_inst_seq`、
  `op_class`；不做任何架构/PRF 写，不消耗 `max_faults`；返回 false。
  `fsu_prop_fields.py` 将 `suppress` 映射为无 L0–L5 层。
- rounding 早退：完成 1-ULP nudge 后构造 `FaultInfo`，
  `field=rounding_sub`、`injection_site=rounding_sub_one_ulp_proxy`、
  `hook_version=1`、`producer_sn`、`before/after/mask`，调用
  `noteFaultApplied()`（因此发出真实 `fault_applied` L0 + `carrier_state`
  L1），再写含 `faults_injected: <n>` 的注入日志并返回 `okr`。
- 代理边界：rounding 仅允许 FP64 / lane_width=64 / lane_offset=0，
  只对 `VecRegClass` 目的且 `std::isfinite` 的 double 生效；方向是
  LSB=1 时 `nextafter(-inf)`、LSB=0 时 `nextafter(+inf)`（当前舍入方向
  的反向邻居）。它不是 FPCR/RMODE 的真实翻转。
- 两个注入点各自只出现一次；`suppress` kind 只出现一次
  （`tests/test_chaos_fsu_fp08_contract.py` 断言）。

### 3.3 独立计数

`fpsr_attempted/fpsr_applied/suppressed_count` 与
`rounding_attempted/rounding_applied` 是不同成员；fpsr 分支不引用
`rounding_*`，rounding 分支不引用 `fpsr_*`；`++suppressed_count;` 全文件
只出现一次。

### 3.4 既有真实证据（只读复核）

`runs/fsu-gates/FP08-FPSR-GATE/fpu_injections.log`：

```text
CHAOS_FPSR_ATTEMPTED=174018
CHAOS_FPSR_APPLIED=174018
CHAOS_FPSR_SUPPRESSED=174018
CHAOS_FPSR_REASON=fpsr_not_architecturally_modeled
```

`runs/fsu-gates/FP08-GATE/FSU-FP08-F0-W1-ROUNDING-GATE/seed1/attempt-2/inject/fpu_injections.log`：

```text
Tick: 46267760, Site: dyn_inst_execute, opClass=9, sn=36290,
mode=rounding_sub, faults_injected: 1
CHAOS_ROUNDING_ATTEMPTED=357
CHAOS_ROUNDING_APPLIED=1
```

对应 `prop_evt.txt.gz` 中的真实链（同一 attempt）：

```text
kind=fault_applied field=rounding_sub before=0x0000000000000000
after=0x0000000000000001 phys_reg=45 ...
kind=carrier_state ... kind=operand_read ... kind=execute ...
kind=prf_writeback ... kind=commit detection_layer=L5 outcome=errant_commit
```

注意：`FP08-FPSR-GATE` 中每行 `decode_reject=precision_mismatch` 是该 gate
的 FP32 负载 + FP64 manifest 造成的预期 reject，与本文件结论无关。

## 4. 其他模式回归（源码契约）

新增测试断言本轮修复没有改变其他 CHAOSIQ 模式：

- `stringToMode()` 仍接受全部 12 个模式名；
- `wake_omit` 仍 `iq_counts.applied++` + `faults_injected_count++` 并返回
  true；
- `ready_early` / `ready_never(_event)` / `dispatch_misroute` 仍各自递增
  注入计数，`gateEligible()` 仍在；
- `noteTagWake()` 的 src_ready_bitflip 早退之后，`tag_stuck` 证据路径仍在；
- `shouldDelayWake()` 关闭只影响 wake_phase，因为 wake_omit/wake_phase 都
  在 `shouldOmitWake()` 中处理，其他模式不使用该回调。

额外实跑（真实命令，非本任务新增测试）：

```text
$ python3 -m pytest tests/test_fsu_f0_readiness.py -q
..........                                                               [100%]
10 passed in 0.13s
```

## 5. 仍需真实仿真验证的缺口（不虚构）

1. **FQ08-c generation/identity 路径**：真实 gate 只观测到
   `ignore_squashed`；`ignore_generation`（明确 free+realloc 后旧事件到达）
   与 `ignore_identity` 需要专门 workload/时序窗口才能稳定命中。
2. **FQ08-b 重复唤醒抑制**：日志有
   `duplicate genuine wake suppressed` 行，但没有独立计数器；无法在
   汇总里直接核对“抑制次数 == applied 次数”。建议加
   `duplicate_wake_suppressed` 计数。
3. **FQ08-b activated 的真实比例**：现有正例 `activated=0`；需要能命中
   “最后一个未就绪源槽”的 workload 才能观测 activated 正例。
4. **FP08 rounding attempted 未 applied 的原因**：当前只有 attempted /
   applied 两个数，无法区分“没有可写 Vec 目的寄存器”和“值非有限”；
   需要新增 reason 计数或 per-skip 日志后再做正式守恒审计。
5. **FP08 countOnly 输出**：真实 countOnly 日志（`.../attempt-2/census/`）
   出现 `CHAOS_ROUNDING_ATTEMPTED=0` / `APPLIED=0` **两次**：一次来自
   `dumpCensus()`（析构），一次来自 startup 注册的 exit callback。注入
   阶段该 proxy 分支在 countOnly 下根本不会执行，因此这是“静默 0 + 重复
   行”，不能当作 attempted=0 的证据。
6. **FP08 `suppress` 事件与链审计**：`kind=suppress` 无 L0–L5 层、
   `fault_id=0`、`parent=~0ULL`、`corr=fsu_taint`。需要一次真实 gate 确认
   chain checker 把它当作非链证据而不是 orphan fault。
7. **FP08 模式组合未 fail-closed**：构造函数没有显式拒绝
   `fpsr_suppress` 与 `fma_weighted/recurring_stuck/f3_dependent/bitseg`
   的组合，也没有拒绝 `rounding_sub` 与
   `f3_dependent/fma_weighted/recurring_stuck` 的组合；由于分支顺序，
   后者会被静默变成 inert。正式计数前必须补互斥 guard。
8. **FQ08-c 运行结束清理**：`AutoDelete` + 退出汇总的源码形状已确认，但
   还没有真实 gate 在“延迟事件尚未 fire 时 workload 结束”的场景下验证
   没有悬空引用/析构问题。

## 6. 建议的 C++ 补丁（本任务未落地）

1. `CHAOSFPU.cc`：为 rounding 未 applied 增加
   `rounding_no_writable_dest` / `rounding_nonfinite` 计数并在退出汇总输出；
   fpsr 代理同样明确 `fpsr_applied` 与 `fpsr_suppressed` 的同一性来源。
2. `CHAOSFPU.cc` 构造函数：对 FP08 组合 fail-closed：
   `fpsr_suppress` 不得与 `fma_weighted/recurring_stuck/f3_dependent/bitseg`
   同开；`rounding_sub` 不得与 `f3_dependent/fma_weighted/recurring_stuck`
   同开。
3. `CHAOSFPU::dumpCensus()` / startup exit callback：countOnly 时不要输出
   `CHAOS_FPSR_*` / `CHAOS_ROUNDING_*` 的 0000，或只由一个出口输出一次，
   避免重复行；如需保留，加 `mode=count_only` 标签。
4. `CHAOSIQ.cc`：增加 `duplicate_wake_suppressed` / `ws_attempt` 丢弃原因
   的显式计数，并写入 `CHAOS_IQ_COUNTS`。
5. `emitFsu("suppress", ...)`：明确无 parent / `corr` 语义（非链记录），
   或在 chain checker 侧显式白名单。
6. `inst_queue.cc/hh`：删除或加守卫不可达的 `o3::DelayedWakeEvent` 路径
   （本任务文件所有权之外，建议单独提交）。

## 7. 本轮真实命令与输出

```text
$ python3 -m pytest tests/test_chaos_fsu_fq08_regression.py \
      tests/test_chaos_fsu_fp08_contract.py tests/test_fsu_fp05_burst.py -q
...................................................................      [100%]
67 passed in 0.44s

$ python3 -m pytest tests/test_fsu_scope.py -q
..............                                                           [100%]
14 passed in 1.75s
```

结论：FQ08-b / FQ08-c 的源码契约与离线规则回归通过；既有真实 gate 日志
与修复语义一致；FP08 的代理计数/事件契约通过源码与格式层验证，但仍是
代理模型，正式计数前需完成 §5 的真实 gate 与 fail-closed 补丁。
