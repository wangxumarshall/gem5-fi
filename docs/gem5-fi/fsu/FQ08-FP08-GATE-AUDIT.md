# FQ08-c / FP08 门禁逐项审计（代码—离线—真实证据三层）

日期：2026-11-05。分支 `fsu`。本文件由 subagent 编写，**未修改**任何注入器源码
（`CHAOS/gem5/src/cpu/o3/CHAOSIQ/*`、`CHAOSFPU/*`、`inst_queue.*`、
`regfile.hh` 均只读），未运行 scons / gem5，未 commit / push。

> **2026-11-05 后续修复（主 agent）**：本文件 §3.1 的 `woken` 观测缺口已补
> （`CHAOSIQ.cc` Fire 分支记录 `wakeDependents()` 返回值，退出汇总
> `delayed_dependents_woken`）；FP08 rounding 原因分区与不兼容模式
> fail-closed 已实现。真实 gate 见 `FQ08-FP08-GATE-EVIDENCE.md`。
> 仍未闭合：FQ08-c generation/free-reuse 真实样本（BLOCKED）、identity
> 真实负例（N/A）、fpsr 架构模型（代理）。

> 并发修改说明（事实）：审计期间另一 subagent 正在改 CHAOSFPU（FP05 burst，
> `CHAOSFPU.cc` mtime 2026-11-05 09:20）。本次用 `git diff` 核对了 FP08 相关
> 区域：`fpsr_suppress` / `rounding_sub` 分支与退出汇总的代码**逐字未变**，只是
> 行号整体后移；本文行号以 2026-11-05 09:2x 的工作树为准。
> `CHAOSIQ.cc` mtime 仍为 2026-11-04 16:16（未变）。

## 0. 证据分层（不要把契约测试当运行行为）

| 层 | 本轮文件 / 命令 | 能证明 | 不能证明 |
|---|---|---|---|
| 源码契约 | 本文件 §2.1/§2.3/§4.1；`tests/test_chaos_fsu_fq08c_gate_audit.py`、`tests/test_chaos_fsu_fp08_reason_audit.py` | 分支顺序、计数位置、字段、日志形状 | gem5 真的这样跑过 |
| Host 模型（真实编译执行） | `tests/unit/fq08c_delayed_wake_target_state_test.cc`，pytest 自动用 g++ 编译运行 | **真实 C++ 头文件** `chaos_iq_lifecycle.hh` 的判定，以及“Fire 才改目标状态”的后果 | gem5 事件队列 / DynInst / PRF 的运行时行为 |
| 既有真实 gem5 日志 | `runs/fsu-gates/FQ08-*`、`runs/fsu-gates/FP08-*` | 修复后曾经观测到的计数/事件 | 本轮新 seed；未观测到的路径 |
| 仍需真实仿真 | §3、§5 的缺口 | — | 不得用离线测试冒充 |

## 1. FQ08-c 逐项核对

### 1.1 代码锚点

| 位置 | 事实 |
|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc:107-202` | `shouldOmitWake()` 同时处理 `wake_omit` 与 `wake_phase`；`wake_phase` 在概率命中后取 `snapshotWakeStamp()`（:149-150）、`cpu->schedule(new DelayedWake(...))`（:151-152），然后 `dw_counts.scheduled++`、`iq_counts.applied++`、`faults_injected_count++`（:153-155），返回 true 丢弃本次广播（:176）。 |
| `CHAOSIQ.cc:250-268` | `shouldDelayWake()` 永久 `return false`；调用点的 `o3::DelayedWakeEvent` 不可达。 |
| `CHAOSIQ.hh:78-93` | `DelayedWake` 只持有 `o3::DynInstPtr inst`（引用计数）与 `chaos_iq_lifecycle::WakeStamp stamp`（值快照），不持有 `InstructionQueue*`。 |
| `CHAOSIQ.cc:1019-1038` | `snapshotWakeStamp()`：seqNum、tid、每个目的物理寄存器的 `flatIndex()` + `generationOf()`。 |
| `CHAOSIQ.cc:1073-1128` | `process()`：先 `classifyWake()`（:1096-1097），`noteWakeDecision()`（:1098）；非 Fire 写 `IGNORED` 并 return（:1100-1102）；Fire 才 `iq_counts.activated++`（:1107）并 `wakeDependents(inst)`（:1109）。 |
| `chaos_iq_lifecycle.hh:284-300` | 判定顺序：`has_inst` → seq/tid → `squashed` → dest 个数 → 每个 dest 的 flat+generation。 |
| `chaos_iq_lifecycle.hh:301-321` | 每个事件只推进一个 `DelayedWakeCounters` 字段。 |
| `inst_queue.cc:1156-1172` | 调用顺序是 `shouldOmitWake()` 先、命中即 `return 0`；`shouldDelayWake()` 因此永远看不到 `wake_phase`。 |
| `inst_queue.cc:1187` | `wakeDependents()` 自带 `assert(!completed_inst->isSquashed())`；FQ08-c 在进入前用 `classifyWake` 拦截 squash。 |

### 1.2 逐项结论

| 检查项 | 代码 | Host 目标状态证据（真实 g++ 执行） | 真实 gem5 证据 | 结论 |
|---|---|---|---|---|
| generation/identity **正例**（快照匹配 → Fire） | `classifyWake` 末尾返回 `Fire`；`process` Fire 分支唤醒 | `test_fire_really_changes_target_state`、`test_one_counter_per_event_and_drained_conservation` | 无（见 §3.1） | 模型层已证明；真实 fire 未观测 |
| 未 squash 时延迟事件**真实触发** | Fire 分支 `activated++` + `wakeDependents` | 同上：dependent ready=false→true，wake 调用恰好 1 次 | 无；现有 gate 只有 squash | **BLOCKED**（§3.1） |
| squash 后安全忽略 | `now.squashed` → `IgnoreSquashed`；不进入 `wakeDependents` | `test_squash_leaves_target_state_unchanged`（状态不变、wake=0） | `FQ08-C-GATE`：`IGNORED reason=ignore_squashed`，exit 0 | 已证明（真实） |
| free/realloc 后安全忽略 | dest generation 变化 → `IgnoreGeneration` | `test_generation_realloc_cannot_wake_new_owner`（新 owner 的 dependent 仍 not ready） | 无（§3.2） | 模型层已证明；真实未观测 |
| identity 不一致安全忽略 | seq/tid/目的个数 → `IgnoreIdentity` | `test_identity_mismatch_cannot_wake_another_instruction`、`test_identity_is_checked_before_squash` | 无（§3.3） | 模型层已证明；真实不可自然触发 |
| 旧事件不作用到**新槽位** | 先 identity、再 squash、再 generation；非 Fire 直接 return | `test_generation_realloc_cannot_wake_new_owner`、`test_squash_then_reuse_then_new_event_fires` | 无 | 模型层已证明；真实未观测 |
| 每个事件恰好一个计数 | `noteWakeDecision` 单 switch；`process` 只调用一次 | `test_one_counter_per_event_and_drained_conservation` | squash gate：`scheduled=1 = fired 0 + ignored_squashed 1` | 已证明 |
| 仅 exit=0 不够 | `activated++` 位置在 Fire 分支内、`wakeDependents` 之前（:1107-1109） | Host 断言的是目标状态而不是退出码 | `activated=0`（squash）；没有 fire 正例 | 见 §3.1 的观测缺口 |

### 1.3 关键诚实结论：`activated` 不等于“目标状态已变化”

`process()` 里 `iq_counts.activated++` 发生在 `wakeDependents(inst)` **之前**，
且 `wakeDependents()` 的返回值（实际唤醒的 dependent 数）被丢弃
（`CHAOSIQ.cc:1109`）。因此即使将来出现 `FIRED` / `activated=1`，也只能证明
“重新进入了 `wakeDependents()`”，**不能证明某个 dependent 的 ready bit 真的
从 0 变 1**。当前 `iq_injections.log` 没有任何 `woken=<n>` / dependent 计数。

另外，wake_phase 的 `applied` / `faults_injected` 在 **schedule 时** 增加
（`CHAOSIQ.cc:153-155`），即使事件随后被 squash 忽略；因此
`applied == fired + ignored_*`（同一事件只会进入一个终态，且运行结束前已排空时
成立），`applied=1` 不代表“故障生效”，只代表“广播被丢弃并预约了重放”。
squash gate 正是 `applied=1, fired=0, ignored_squashed=1`。

`tests/test_chaos_fsu_fq08c_gate_audit.py::test_fire_target_state_count_is_not_observable_yet`
以 `EXIT_SKIP`（pytest skip，reason 以 `to be implemented (placeholder)` 开头）
钉住这一缺口；`test_positive_fire_evidence` 即使在真实 fire 日志出现后，也会
因为没有 `woken>0` 而继续 BLOCKED。要解除，需要注入器侧（主 agent）在 FIRED
行增加 `woken=<wakeDependents 返回值>`。

### 1.4 既有真实日志（只读复核）

`runs/fsu-gates/FQ08-C-GATE/iq_injections.log`（`branch_mispred`，
wake_phase，phase_offset=2，first_clock=1000，max_faults=1，seed=20260825）：

```text
Tick: 398475, Site: iq_wakeDependents, mode=wake_phase, tid=0,
completed_sn=105, phase_offset=+2, delayed_event=scheduled
(CHAOSIQ-owned, identity+generation checked at fire), ... faults_injected: 1
Tick: 399245, Site: iq_delayed_wake, mode=wake_phase,
IGNORED reason=ignore_squashed, completed_sn=105, completed_tid=0,
delayed_fired=0, delayed_ignored_squashed=1, ... faults_injected: 1
CHAOS_IQ_COUNTS mode=wake_phase, eligible=6, attempted=1, applied=1,
activated=0, no_victim=0, pending_attempt=0, delayed_scheduled=1,
delayed_fired=0, delayed_ignored_no_inst=0, delayed_ignored_identity=0,
delayed_ignored_squashed=1, delayed_ignored_generation=0,
faults_injected: 1
```

核对：`scheduled(1) == fired(0) + ignored_squashed(1)`，exit 0，无 assert。
**这是 squash 负例，不是 fire/activation 正例。**

## 2. FQ08-c 需要的真实 gate（主 agent 执行）

构建：`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（只有 C++ 改动才需要）。
以下命令使用仓库根 `build/ARM/gem5.opt`。

### 3.1 正例：未 squash → Fire（依赖 `woken` 可观测性）

```bash
build/ARM/gem5.opt --outdir=/tmp/fq08c-fire \
  configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3 \
  --chaos_iq --iq_mode wake_phase --iq_phase_offset 2 \
  --iq_first_clock 10000 --iq_max_faults 1 --iq_rng_seed 20261105
```

选择 `dep_chain` 的理由：直链 MADD 循环、无数据相关分支，延迟 2 周期内生产者
大概率仍存活且未 squash；`first_clock=10000` 把首次命中推到稳态循环（有真实
dependent）。若首次命中仍无 dependent，再按 seed 扫描。

判据（全部满足才算 PASS，缺一条即 BLOCKED）：

1. exit 0，无 SIGSEGV/SIGABRT，无 `dependGraph` / `isSquashed` assert；
2. 恰好 1 条 `delayed_event=scheduled`；
3. 至少 1 条 `FIRED delayed wake (producer live, generation stable)`，且
   **该行带 `woken=<n>` 且 `n>0`**（当前代码没有，需先加，见 §1.3）；
4. 汇总 `delayed_scheduled=1, delayed_fired=1, activated=1, applied=1,
   faults_injected: 1`，所有 `delayed_ignored_*=0`；
5. 没有该事件的 `IGNORED` 行。

只看到 `FIRED` 而 `activated` 增加、但没有 `woken>0` 时，必须判
**BLOCKED（目标状态未证明）**，不得写成“激活成功”。

### 3.2 generation：free/realloc 后旧事件到达

```bash
build/ARM/gem5.opt --outdir=/tmp/fq08c-gen \
  configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3 \
  --chaos_iq --iq_mode wake_phase --iq_phase_offset 128 \
  --iq_first_clock 10000 --iq_max_faults 1 --iq_rng_seed 20261105
```

判据：

1. exit 0，无 assert；
2. `IGNORED reason=ignore_generation` 至少 1 条；
3. 汇总 `delayed_ignored_generation>=1`，且同一条事件的 `delayed_fired=0`；
4. 不得把 `ignore_squashed` / `ignore_identity` 当成 generation 证据。

窗口由 `phase_offset` 控制：128 周期通常足以让生产者提交并释放目的物理寄存器
（`UnifiedFreeList::addReg → noteRegFreed → flat_generation++`，
`free_list.hh:265-275`、`regfile.hh:277-281`）。若首次命中落在短命指令上，
按 `{64,128,256}` × `{20261105,20260825}` 扫描；每次仍只允许 max_faults=1。

### 3.3 identity：不是可自然触发的运行时路径

`seqNum` 与 `threadNumber` 在 DynInst 生命周期内不可变；同一事件持有的
`DynInstPtr` 也不会“变成另一条指令”。因此 `ignore_identity` 是**防御性检查**，
在正常 gem5 运行中不可自然命中（除非做 debug-only 的合成事件注入，超出本轮
范围）。诚实口径：

- 正例（identity 匹配 → Fire）由 host 测试证明；
- 负例（identity 不匹配 → 不作用）由 host 测试证明；
- **不得声称有真实 gem5 identity 证据**；
- 若主 agent 仍要真实观测，只能临时构造“篡改 stamp 的 unit/回归 harness”，
  属于 debug 机制，不得作为正式 gate 计数。

### 3.4 关联项：FQ08-b 的 activated 正例（真实）

现有 `FQ08-B-POS4` 是 `applied=1, activated=0`（`ready_regs 0 -> 1 / 2`），
只证明 wrong-source 写发生，不证明“写后立即可发射”。要观测 activated：

```bash
build/ARM/gem5.opt --outdir=/tmp/fq08b-act \
  configs/se/ooo_proxy.py --cmd workloads/directed/elemwise_int_kernel --cpu O3 \
  --chaos_iq --iq_mode src_ready_bitflip --iq_target_class int \
  --iq_first_clock 1000 --iq_max_faults 1 --iq_rng_seed <sweep>
```

判据：`APPLIED wrong-source ready bit` 行出现 `ready_regs 1 -> 2 / 2`，汇总
`activated>=1` 且 `applied>=activated`，`faults_injected: 1`。该行本身记录了
ready 计数变化，属于真实目标状态证据。

## 4. FP08 审计（只读）

### 4.1 当前实现锚点

| 位置（2026-11-05 工作树） | 事实 |
|---|---|
| `CHAOSFPU.hh:196,200-203` | `suppressed_count`、`fpsr_attempted/applied`、`rounding_attempted/applied` 是独立成员。 |
| `CHAOSFPU.cc:830-832` | fpsr 分支三个 `++` 在同一无条件块内 → 构造性 `attempted == applied == suppressed`。 |
| `CHAOSFPU.cc:834-849` | 发射 `suppress` 事件：`field=fpsr_suppress`、`reason=fpsr_not_architecturally_modeled`、`injection_site=fpsr_suppress_proxy`；无 PRF/架构写、无 `faults_injected_count++`、返回 false。 |
| `CHAOSFPU.cc:853-913` | rounding 分支：`++rounding_attempted` 在扫描前；`++rounding_applied`、`faults_injected_count++`、`noteFaultApplied()` 只在 `if (okr)` 内。 |
| `CHAOSFPU.cc:407-414`、`3020-3028` | 两个出口（census / injection exit callback）都输出计数。countOnly 时可能重复输出，见 §4.5。 |
| `CHAOSFPU.cc:138-142,205-209,223-226,229-232,338-342` | 现有的互斥 guard：rate、prfWbHook、bitseg、rounding 几何、permanentStuck。 |

### 4.2 rounding 未 applied 的原因分类（枚举 + 判定依据）

一次 `rounding_attempted` 之后，`okr=false` 只可能来自下列条件。判定顺序即
代码扫描顺序；`continue` 表示换下一个目的寄存器。

| 原因（建议计数名） | 代码判定 | 判定依据 |
|---|---|---|
| `no_o3cpu` | `auto *o3cpur = dynamic_cast<o3::CPU *>(cpu); if (o3cpur)` 不成立 | 注入器挂在非 O3 CPU 上 |
| `no_vec_dest` | `!dest || dest->is(InvalidRegClass)` 或 `dest->classValue() != VecRegClass` 对所有候选成立 | 该指令没有可写的 VecRegClass 目的 |
| `no_writable_dest` | `o3cpur->getWritableReg(dest, tid)` 返回空 | 目的存在但取不到可写 PRF 指针 |
| `nonfinite` | `!std::isfinite(d)` | 目的值 NaN/Inf，1-ULP nudge 无定义 |
| `applied` | 首次满足以上全部条件并完成 `nextafter` | `++rounding_applied` |

**尝试级互斥规则（本次审计采用）**：
1. 任一候选 applied → `applied`；
2. 否则 `!has_o3cpu` → `no_o3cpu`；
3. 否则没有任何合法 Vec 目的 → `no_vec_dest`；
4. 否则所有 Vec 候选都取不到可写指针 → `no_writable_dest`；
5. 否则 → `nonfinite`。

该规则的 Python 实现在
`tests/test_chaos_fsu_fp08_reason_audit.py::classify_attempt`，并用
`test_reason_classifier_is_total_and_exclusive` 证明输出总是
`ROUNDING_REASONS` 中的恰好一个。注意：多目的指令的 reason 是本审计定义的
“主因”，C++ 若要逐候选审计，应改为 per-candidate 日志；当前没有。

### 4.3 守恒关系

- fpsr：`attempted == applied == suppressed`，且 `rejected = attempted - applied = 0`
  （每个 attempt 都进入被标注的代理路径）。真实日志满足：174018/174018/174018。
- rounding：`attempted == applied + rejected`；
  `rejected = no_o3cpu + no_vec_dest + no_writable_dest + nonfinite`。
  当前代码只输出前两项，因此只能验证 `attempted >= applied`，无法验证完整分区。
- 真实 rounding 日志：`attempted=357, applied=1` → `rejected=356`，**356 个
  rejection 没有原因分类**。

`tests/test_chaos_fsu_fp08_reason_audit.py::check_conservation` 实现上述检查；
`test_per_reason_counters_are_not_implemented_yet` 与
`test_real_rounding_gate_reason_partition` 以
`to be implemented (placeholder)` 跳过，属于 **BLOCKED**（原因级守恒未闭合）。

### 4.4 不兼容模式组合：现状 fail-open

已 fail-closed（源码有显式 panic）：

| 组合 | 位置 |
|---|---|
| `rounding_sub` + `rate_mode` / `fpsr_suppress` + `rate_mode` | `CHAOSFPU.cc:138-142` |
| `rounding_sub` / `fpsr_suppress` + `prf_wb_hook` | `CHAOSFPU.cc:205-209` |
| `rounding_sub` / `fpsr_suppress` + `permanent_stuck` | `CHAOSFPU.cc:338-342` |
| `rounding_sub` + `bitseg` | `CHAOSFPU.cc:223-226` |
| `rounding_sub` 非 FP64/lane64/offset0 | `CHAOSFPU.cc:229-232` |

**未 fail-closed（本轮跳过为 BLOCKED）**：

- `fpsr_suppress` + `fma_weighted`
- `fpsr_suppress` + `recurring_stuck`
- `fpsr_suppress` + `f3_dependent`
- `fpsr_suppress` + `bitseg`
- `rounding_sub` + `fma_weighted`
- `rounding_sub` + `recurring_stuck`
- `rounding_sub` + `f3_dependent`

原因：`maybeCorrupt()` 的分支顺序让 `fpsr_suppress` / `rounding_sub` 先 `return`，
另一个模式静默变成 inert；配置不会在运行前失败。
`tests/test_chaos_fsu_fp08_reason_audit.py::test_unguarded_combinations_fail_closed`
以 skip 明确列出这 7 项；补丁建议见
`FQ08-FP08-REGRESSION.md` §6.2。

### 4.5 真实证据与证据质量问题

| 文件 | 真实内容 | 判定 |
|---|---|---|
| `runs/fsu-gates/FP08-FPSR-GATE/fpu_injections.log` | `CHAOS_FPSR_ATTEMPTED=174018`、`APPLIED=174018`、`SUPPRESSED=174018`、`REASON=fpsr_not_architecturally_modeled` | 守恒通过；仍为代理，不是架构 FPSR |
| `runs/fsu-gates/FP08-GATE/.../seed1/attempt-2/inject/fpu_injections.log` | `CHAOS_ROUNDING_ATTEMPTED=357`、`CHAOS_ROUNDING_APPLIED=1`，1 条 `mode=rounding_sub, faults_injected: 1` | `attempted>=applied` 通过；356 个 rejected 无原因分类 |
| `runs/fsu-gates/FP08-GATE/.../seed1/attempt-2/census/fpu_injections.log` | `CHAOS_ROUNDING_ATTEMPTED=0` / `APPLIED=0` **出现两次** | countOnly 下 proxy 分支不执行；重复零行不能当“发生过 attempted=0”的证据；`test_census_duplicate_rounding_zero_pair_is_flagged_not_passed` 钉住 |

### 4.6 代理分类：不得因工具 PASS 自动升级

- `tools/fsu_prop_fields.py` 的 `KIND_LAYER["suppress"] is None`：suppress 不占
  L0–L5，不是链证据。
- 两个注入点各自唯一：`fpsr_suppress_proxy`、`rounding_sub_one_ulp_proxy`。
- `tools/fsu_implementation_matrix.py` 中 FP08 仍为 `status="PARTIAL"`。
- `docs/gem5-fi/fsu/F0-READINESS-ORDER.md` 把 `FP08 rounding_sub` 列在
  “unapproved proxy / wrong site”，明确“不得用结果侧链认证”。
- `tests/test_chaos_fsu_fp08_reason_audit.py::test_tool_pass_and_chain_full_do_not_upgrade_proxy`
  把策略写成可执行断言：FP08 即使 chain full + tool PASS 仍返回 `proxy`。
- 结论：**当前没有任何证据支持把 FP08 记为正式模型认证**；工具 PASS 只代表
  该代理路径的自洽性。

### 4.7 需要主 agent 执行的 FP08 命令（在补丁后）

原因分区（需先给 C++ 增加 §4.2 计数/日志）：

```bash
build/ARM/gem5.opt --outdir=/tmp/fp08-reasons \
  configs/se/ooo_proxy.py --cmd workloads/directed/w1_fp_scalar_probe --cpu O3 \
  --chaos_fpu --fsu_model FP08 --fsu_freq F0 --fsu_load W1 \
  --fsu_submodel FP08-a --fpu_precision fp64 --fpu_lane_width 64 \
  --fpu_lane_offset 0 --fpu_decode_guard --fpu_rounding_sub \
  --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt \
  --fpu_reg_class vec --fpu_first_clock 0 --fpu_max_faults 1 \
  --fpu_rng_seed 20260825
```

判据：`CHAOS_ROUNDING_ATTEMPTED = APPLIED + SKIP_NO_O3CPU + SKIP_NO_VEC_DEST +
SKIP_NO_WRITABLE_DEST + SKIP_NONFINITE`，且每项非负；注入行数 == applied；
exit 0。若新增计数未输出，继续 BLOCKED。

fail-closed 组合（不需要跑完整 workload，构造期即应 panic）：

```bash
build/ARM/gem5.opt --outdir=/tmp/fp08-incompat \
  configs/se/ooo_proxy.py --cmd workloads/ooo/smoke/smoke --cpu O3 \
  --chaos_fpu --fpu_rounding_sub --fpu_f3_dependent
# 期望：启动即 panic "CHAOSFPU: rounding_sub is incompatible with ..."，
# 不得进入 simLoop、不得产生 injection 日志。
```

对 §4.4 的 7 个组合逐一执行；每个都应“配置期失败”。当前全部会静默运行，
因此这 7 项判 BLOCKED。

## 5. 未完成 / 阻塞清单

| 项 | 状态 | 原因 |
|---|---|---|
| FQ08-c fire 正例（真实 gem5） | **BLOCKED** | 无 `delayed_fired>=1` 日志；且 `woken` 未记录，无法证明目标状态变化（`test_fire_target_state_count_is_not_observable_yet` 另以 placeholder skip 钉住） |
| FQ08-c generation 正例（真实） | **BLOCKED** | 无 `ignore_generation` 日志 |
| FQ08-c identity 负例（真实） | **N/A（不可自然触发）** | seqNum/tid 不可变；host 已证明，不能伪造真实证据 |
| FQ08-c 旧事件不作用新槽位（真实） | **BLOCKED** | 依赖 generation 真实日志 |
| FQ08-b activated 正例（真实） | 待跑 | 现有正例 activated=0；命令见 §3.4 |
| FP08 rounding 原因级守恒 | **BLOCKED** | 无 per-reason 计数/日志 |
| FP08 7 个不兼容组合 fail-closed | **BLOCKED** | 构造期无 panic |
| FP08 countOnly 重复零行 | 已识别，未修 | 出口重复；需要 C++ 侧去重，本轮只读 |
| FQ08-c 运行结束时未 fire 事件清理 | 模型层 AutoDelete；真实未验证 | 与 fire 正例同一 gate 可覆盖 |

## 6. 本轮真实运行命令与输出（摘要）

```text
$ python3 -m pytest tests/test_chaos_fsu_fq08c_gate_audit.py -q -rs
8 passed, 4 skipped in 0.6s
# skip：
#   to be implemented (placeholder): FIRED 行没有 woken=<n>
#   BLOCKED: positive fire / generation / identity real evidence

$ python3 -m pytest tests/test_chaos_fsu_fp08_reason_audit.py -q -rs
14 passed, 3 skipped in 0.1s
# skip 均为 "to be implemented (placeholder)"：
#   per-reason counters、real reason partition、7 个 fail-open 组合
```

Host 目标态测试真实输出（g++ 10.3.1，`-Wall -Wextra -Werror`，exit 0）：

```text
FQ08-c delayed-wake target-state host test
[positive] unsquashed event fires and changes state
  PASS unsquashed producer fires
  PASS fire calls wakeDependents exactly once
  PASS fire changes dependent ready state false -> true
  PASS fire increments fired counter
  PASS fire increments no ignored counter
[negative] squash / generation / identity are no-ops
  PASS squashed producer ignored
  PASS squash does not call wakeDependents
  PASS squash leaves dependent ready=false
  PASS squash increments only ignored_squashed
  PASS freed/reallocated dest ignored
  PASS stale event does not wake the new owner
  PASS stale event leaves the new owner's dependent not ready
  PASS generation mismatch increments only ignored_generation
  PASS different seqNum ignored
  PASS different tid ignored
  PASS dest-count mismatch ignored
  PASS identity mismatches never touch target state
  PASS identity counter moved for each mismatch
  PASS one stale destination rejects the whole event
  PASS partial generation match does not wake
  PASS identity wins over squash/generation
  PASS identity-first still never wakes
  PASS identity-first increments ignored_identity only
[lifecycle] stale event cannot resurrect; new event fires
  PASS old event never wakes after squash/reuse
  PASS separate current event still fires
  PASS separate current event changes target state
  PASS counter accounting after squash+reuse+fire
  PASS one decision per processed event
  PASS each reason counted exactly once
  PASS drained run: scheduled == fired + ignored_*
  PASS drained run: one fire changed target state
ALL FQ08-C TARGET-STATE CHECKS PASSED
```
