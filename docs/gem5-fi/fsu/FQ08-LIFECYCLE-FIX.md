# FQ08-b / FQ08-c 修复记录（CHAOSIQ 生命周期）

日期：2026-11-04。范围：`CHAOS/gem5/src/cpu/o3/CHAOSIQ/` 与 host 测试。
本文件只记录**真实执行**过的命令与输出；gem5 构建/运行由主 agent 执行，本文
将未验证项单列。

## 1. 修改文件

| 文件 | 变更 |
|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.hh` | 新增 `DelayedWake` 事件、FQ08 计数器/状态、`maybeApplyWrongSourceWake` / `noteDelayedWakeIgnored` / `dumpIqCounts` / `snapshotWakeStamp` / `modeName`；`shouldOmitWake` 文档改为同时承担 wake_phase |
| `CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc` | FQ08-b 计数语义重写；FQ08-c 延迟唤醒由 CHAOSIQ 自己调度并在 fire 时校验；`shouldDelayWake` 永久关闭；退出汇总 |
| `CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh`（新建） | 纯 C++ 状态机（无 gem5 依赖），gem5 侧直接调用；host 可编译 |
| `tests/unit/chaos_iq_lifecycle_test.cc`（新建） | host 单测：无 victim/有 victim/预算/重复真实唤醒抑制/squash/generation 复用/正常事件 |
| `tests/test_chaos_iq_lifecycle_cpp.py`（新建） | 用 `g++` 编译运行上述单测 + 静态接线检查 |
| `CHAOSIQ.py` | **未改**（没有新参数需求） |

> 说明：任务要求“抽出纯函数/模型到可 host 测试的头文件”。新增的
> `chaos_iq_lifecycle.hh` 位于 CHAOSIQ 组件目录内，与仓库既有
> `chaos_fsu_fields.hh` / `chaos_vec_stuck.hh` 的做法一致。

## 2. 修复前行为（真实源码，`git show HEAD:…/CHAOSIQ.cc`）

`shouldWrongSourceWake` 在 RNG 命中后立即计数并返回 true：

```cpp
        faults_injected_count++;
        if (write_log) { ... mode=src_ready_bitflip ... }
        return true;
```

真正的 victim 选择在 `InstructionQueue::wakeDependents` 的 dependent 循环里
（`inst_queue.cc`），只在“该 producer 确实有 dependent”时才会执行。因此：

- producer 没有任何 dependent 时，`wrong_source` 从未被消费，但
  `faults_injected_count` 已 +1，`maxFaults` 预算已被消耗；
- 64 次探测都找不到合法 victim 时同样不施加但已计数。

这也就是旧测试 `tests/test_fsu_f0_readiness.py::
test_fq08b_count_precedes_victim_application` 所钉住的缺陷形状。修复后该测试
**按预期失败**（见 §5.3），需要主 agent 同步更新该“钉缺陷”测试与
`F0-READINESS-ORDER.md` 的 defect 记录。

## 3. 修复后语义

### 3.1 FQ08-b：计数与施加分离

`shouldWrongSourceWake` 现在只做 **attempt** 门控：窗口/类过滤/probability
命中后调用 `beginAttempt()` 并 `attempted++`，然后 **return false**（同时
关闭调用点里旧的“随机换链 pop”手术）。真正施加发生在
`noteTagWake()`（调用点本来就对每个即将被唤醒的 dependent 调用）：

1. 把当前 dependent 作为候选 victim，构造目标寄存器类的源槽视图；
2. `chooseWrongSlot()` 只接受：未 squash、readyRegs < numSrcRegs、且存在一个
   **不是当前唤醒链**的未就绪目标类源槽；
3. 找到才调用 `markSrcRegReady(slot)`，然后 `applied++`、`faults_injected_count++`；
   若这次写入使 readyRegs 达到 numSrcRegs（当前即可 issue），再 `activated++`；
4. 整个 wake 都没找到 victim → 下次 producer wake 入口
   `abortPendingAttempt()` 记为 `no_victim`，**不**动 applied/activated，
   **不**消耗 `maxFaults`。

计数器（退出时输出，见 §3.3）：

| 计数 | 含义 |
|---|---|
| `eligible` | 通过模式/窗口/类过滤的事件数 |
| `attempted` | 门控命中（已越过 skip + probability） |
| `applied` | 真正修改了一个存活 victim（= `faults_injected` 预算消耗） |
| `activated` | applied 且这次错误源写入本身使 victim 变为可发射 |
| `no_victim` | attempt 未找到合法 victim 而作废 |

victim 身份证据（`APPLIED wrong-source ready bit` 行）：`victim_sn`、
`victim_pc`、`victim_op_class`、`victim_src_slot`、`victim_src_phys`、
`victim_src_class`、`victim_src_flat`、`victim_src_generation`、
`wrong_of_chain_flat`、`producer_sn`、`producer_wake_tick`、ready_regs 变化。

**模型口径的诚实说明（与旧实现不同）**：旧的“换链”手术需要
`InstructionQueue::dependGraph`（private，且 `inst_queue.cc/hh` 不在本次可改
范围）。新实现把“错误源”落在**当前真实被唤醒的 dependent 上**：同一个 wake
额外把一个“不是本链”的未就绪源槽标为 ready。效果仍是 wrong-source 早唤醒
（victim 用尚未写回的源值发射），且 victim 是真实、可记录身份的指令。

**重复唤醒抑制**：注入标记了某源槽 ready 但无法把它从该源依赖链中 pop；该源
producer 真正完成时 `shouldSuppressReadyMark()` 会对同一 victim+同一 chain 抑制
**一次** `markSrcRegReady/addIfReady`，恢复 gem5 “每个源恰好一次 mark”的
不变量，避免重复入 ready 队列/重复计数。该逻辑在纯模型与 host 单测中覆盖。

### 3.2 FQ08-c：延迟唤醒生命周期

- `shouldOmitWake()` 同时处理 `wake_phase`：命中后由 CHAOSIQ 调度自己的
  `CHAOSIQ::DelayedWake` 事件并 `return true`（本次广播立即丢弃）。
- `shouldDelayWake()` 永久 `return false`：调用点的 `o3::DelayedWakeEvent`
  路径不再可达（该事件无 squash/generation 校验）。
- `DelayedWake` 持有：`o3::DynInstPtr`（引用计数保证 producer 对象存活）+
  `WakeStamp` **值快照**（seqNum、tid、每个目的物理寄存器的 flat index 与
  `flat_generation`）；**不持有** `InstructionQueue*` 或原始指令指针。
- `process()` 先 `classifyWake()`：
  1. 指令不存在 → `ignore_no_inst`；
  2. seqNum/tid/目的寄存器个数不一致 → `ignore_identity`；
  3. `isSquashed()` → `ignore_squashed`；
  4. 任一目的物理寄存器 generation 变化（已 free/复用）→ `ignore_generation`；
  5. 全部一致才 `wakeDependents(inst)`（`fire`）。
- 被忽略的事件写 `IGNORED reason=...` 日志，并且**每行都带
  `faults_injected: <n>`**，避免 `tools/runner.py` / `tools/fsu_seed_runner.py`
  把普通日志行误计为一次注入。
- 重放保护：`replaying_delayed_wake` 在调用 `wakeDependents()` 期间为真，禁止
  重放再次触发新注入（否则 `maxFaults=0` 的 wake_phase 会自我延迟、永不唤醒）。

### 3.3 可观测汇总（退出时写 `iq_injections.log`）

```
CHAOS_IQ_COUNTS mode=<mode>, eligible=.., attempted=.., applied=.., activated=..,
no_victim=.., pending_attempt=0/1, delayed_scheduled=.., delayed_fired=..,
delayed_ignored_no_inst=.., delayed_ignored_identity=..,
delayed_ignored_squashed=.., delayed_ignored_generation=..,
faults_injected: <n>
```

最后的 `faults_injected: <n>` 与既有解析器兼容（取最后一条显式计数）；
src_ready_bitflip 的 n = applied，wake_phase 的 n = 已调度延迟事件数。

## 4. 真实执行的 host 测试

### 4.1 编译与运行

```bash
g++ -O0 -std=c++17 -Wall -Wextra -Werror \
    -I CHAOS/gem5/src/cpu/o3/CHAOSIQ \
    tests/unit/chaos_iq_lifecycle_test.cc -o /tmp/chaos_iq_lifecycle
/tmp/chaos_iq_lifecycle
```

真实输出（exit=0）：

```text
CHAOSIQ FQ08 lifecycle host test
[FQ08-b] no victim => no applied count
  PASS REPRO old gate counts 1 injection with no victim
  PASS attempt dropped
  PASS no applied
  PASS no activated
  PASS no_victim counted
  PASS REPRO fixed model counts 0 injections
  PASS chain slot rejected as victim
  PASS no victim => no applied
[FQ08-b] victim => real wrong-source write + identity
  PASS wrong source slot chosen
  PASS legitimate chain slot not chosen
  PASS one wake short is not issueable
  PASS applied
  PASS not activated (still one wake short)
  PASS wrong slot chosen when chain differs
  PASS wrong write makes victim issueable
  PASS applied
  PASS activated
  PASS squashed victim rejected
  PASS fully-ready victim rejected
  PASS three no-victim attempts consumed no budget
  PASS three no_victim
  PASS still no applied
  PASS victim attempt consumed exactly one budget unit
  PASS attempted=4 applied=1
  PASS different instruction not suppressed
  PASS different thread not suppressed
  PASS different chain not suppressed
  PASS tracking survives non-matching wakes
  PASS genuine wake of the corrupted source suppressed
  PASS suppression is one-shot
  PASS second genuine wake is not suppressed again
[FQ08-c] delayed wake lifecycle
  PASS normal delayed wake fires
  PASS decision name
  PASS fired counter
  PASS no ignored counter moved
  PASS wakeDependents called exactly once
  PASS squashed producer ignored
  PASS ignored_squashed counter
  PASS squash => wakeDependents NOT called
  PASS freed/reused slot ignored
  PASS ignored_generation counter
  PASS reused slot => new owner is NOT woken
  PASS all destinations must match
  PASS sequence mismatch ignored
  PASS thread mismatch ignored
  PASS dest-count mismatch ignored
  PASS missing instruction ignored
  PASS ignored_no_inst counter
  PASS old event never fired after squash/reuse
  PASS normal event still fires
ALL CHAOS IQ LIFECYCLE CHECKS PASSED
```

### 4.2 pytest（编译运行 + 静态接线）

```bash
python3 -m pytest tests/test_chaos_iq_lifecycle_cpp.py -q
```

真实输出：

```text
........                                                                 [100%]
8 passed in 0.91s
```

### 4.3 相关既有测试

```bash
python3 -m pytest tests/test_fsu_implementation_matrix.py \
    tests/test_fsu_doc_consistency.py tests/test_fsu_scope.py -q
# 28 passed

python3 -m pytest tests/test_fsu_f0_readiness.py -q
# 1 failed, 9 passed
#   FAILED test_fq08b_count_precedes_victim_application
#   AssertionError: assert 'faults_injected_count++' in '<shouldWrongSourceWake body>'
```

该失败是**预期**的：该测试钉住的正是被修掉的缺陷形状（gate 先计数）。
它不在本 subagent 可改范围，需主 agent 在验收时改为：
`shouldWrongSourceWake` 不含 `faults_injected_count++`、含
`beginAttempt`、返回 false；并把 `F0-READINESS-ORDER.md`
（§4.1 与 defects JSON）、`IMPLEMENTATION_AUDIT.md` 的 FQ08 行从
“FQ08-b 仍存在 / FQ08-c 风险”更新为已修复（C++ host 验证 + 待 gem5 gate）。

## 5. 尚未验证 / 需要主 agent 运行的 gem5 gate

以下**未运行**（本 subagent 禁止 scons/gem5），不得声称通过。

### 5.1 FQ08-c squash gate（最小方案）

- config family：C3 `configs/se/ooo_proxy.py`（`--cpu O3`）。
- workload：`workloads/ooo/branch_mispred/branch_mispred`（分支误预测密集，
  放大延迟窗口内的 squash 概率）。对照正常 fire 可用
  `workloads/ooo/madd_chain/madd_chain_kernel`。
- 注入参数：
  `--chaos_iq --iq_mode wake_phase --iq_phase_offset 2 --iq_first_clock 1000
   --iq_max_faults 1 --iq_rng_seed 20260825`
  （`phase_offset=2` 拉宽 squash 窗口；先用 1 个 seed 观察，再换 seed 复现）。
- 预期事件：
  - 正常路径：`Site: iq_wakeDependents, mode=wake_phase ... delayed_event=scheduled`，
    随后 `Site: iq_delayed_wake ... FIRED delayed wake`；
  - squash 路径：`Site: iq_delayed_wake ... IGNORED reason=ignore_squashed`，
    **不得**出现 `assert(!completed_inst->isSquashed())` abort；
  - 槽位复用路径：`IGNORED reason=ignore_generation`；
  - 退出汇总：`CHAOS_IQ_COUNTS mode=wake_phase ... delayed_scheduled=1
    delayed_fired<=1 ... faults_injected: 1`；
  - 进程 exit 0 / 正常 workload 结束，无 SIGSEGV/SIGABRT。
- 判别点：旧实现（`o3::DelayedWakeEvent`）在窗口内 squash 时会命中
  `wakeDependents` 的 squash assert；新实现必须打印 IGNORED 且继续运行。

### 5.2 FQ08-b 计数 gate

- workload：`workloads/ooo/madd_chain/madd_chain_kernel`（FP 依赖链，
  producer 有真实 dependent）。
- 参数：`--chaos_iq --iq_mode src_ready_bitflip --iq_target_class vec
  --iq_fp_only --iq_first_clock 1000 --iq_max_faults 1 --iq_rng_seed 20260825`。
- 预期：
  - 出现 `APPLIED wrong-source ready bit`，带 `victim_sn` / `victim_src_phys` /
    `victim_src_flat` / `victim_src_generation` / `wrong_of_chain_flat`；
  - `CHAOS_IQ_COUNTS ... attempted>=1, applied=1, activated∈{0,1}, no_victim>=0,
    faults_injected: 1`；
  - runner 的 `faults_injected`（取最后一条显式计数）为 1，G5 不报
    `faults_injected` 越界。
- 负例判别：在有 `attempted>0` 但 `applied=0` 的 seed 上，日志**没有**
  `APPLIED` 行、`faults_injected: 0`、`no_victim>0`；旧实现会在相同场景写
  `faults_injected: 1` 但没有 `wrong-source early wake`。
- 回归：`--iq_mode wake_omit` 的单次运行应保持 `faults_injected: 1` 与既有
  分类不变（新增日志字段不影响解析）。

### 5.3 未验证清单

- 未编译 gem5（`CHAOSIQ.cc` 的 gem5 侧改动仅做过源码审查 + 纯模型 host 测试）。
- 未运行任何 SE/FS workload、未产生正式 seed 证据。
- `DelayedWakeEvent` 类仍留在 `inst_queue.cc/hh`（本 subagent 不可改），但已
  不可达；建议主 agent 后续单独提交删除或加守卫。

## 6. 与现有代码/文档冲突的事实

1. `tests/test_fsu_f0_readiness.py::test_fq08b_count_precedes_victim_application`
   明确断言缺陷存在（`faults_injected_count++` + `return true` 于
   `shouldWrongSourceWake`）。修复后必然失败；需主 agent 更新该测试。
2. `docs/gem5-fi/fsu/F0-READINESS-ORDER.md` §4.1 / defects JSON、
   `IMPLEMENTATION_AUDIT.md` 的 FQ08 行仍写“FQ08-b 仍存在、FQ08-c 风险存在”，
   已过时（本 subagent 无权修改这些文档）。
3. `CHAOSIQ.py` 的 `src_ready_bitflip` 注释仍描述“从不同链 pop 一个 dependent”，
   与新的“额外标记一个错误源槽”实现不一致。按任务约束（.py 仅在确需新参数时
   修改）本次未改，建议主 agent 在验收时同步注释。
4. 现有 `tests/test_fsu_f0_readiness.py::test_fq08c_delayed_wake_is_not_squash_aware`
   检查的是 `inst_queue.cc` 文本（未改动），仍通过；但它不再代表“风险存在”，
   因为调用点路径已被 `shouldDelayWake=false` 关闭。

## 6. 真实 gem5 gate 结果（2026-11-04，主 agent）

### 6.1 FQ08-c（wake_phase + squash）

`runs/fsu-gates/FQ08-C-GATE/`：`branch_mispred`，wake_phase，phase_offset=2，
first_clock=1000，max_faults=1，rng_seed=20260825。exit=0；日志：

```
IGNORED reason=ignore_squashed, completed_sn=105, delayed_fired=0,
delayed_ignored_squashed=1, faults_injected: 1
CHAOS_IQ_COUNTS ... delayed_scheduled=1, delayed_fired=0,
delayed_ignored_squashed=1 ...
```

无 `dependGraph` assert、无 panic；squash 后旧事件被安全忽略。

### 6.2 FQ08-b（有/无 victim）

- 负例（W1 FP 负载，`target_class=vec --fp_only`）：
  `attempted=174033, applied=0, no_victim=174033, faults_injected: 0`。
- 正例（`elemwise_int_kernel`，`target_class=int`）：
  `attempted=91, applied=1, no_victim=90, faults_injected: 1`；日志含真实
  victim `sn=311, pc=0x40c214, op_class=MemWrite, src_slot=1,
  src_phys=84, src_generation=2, chain_flat=83`。
- 两例都 exit=0；无 victim 时不再增加 applied/activated 或消耗 fault 预算。
