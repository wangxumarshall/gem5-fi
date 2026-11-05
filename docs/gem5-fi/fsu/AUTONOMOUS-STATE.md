# FSU 自主推进状态（持久化）

> 分支 `fsu`。本文件是任务队列/发现/进度/阻塞的单一恢复点；上下文压缩后
> 先读这里，再读 `docs/superpowers/plans/2026-11-04-fsu-suite-schema-compat-full-reaudit.md`
> 与 `docs/superpowers/plans/2026-11-05-fsu-fr01-fr02-lifecycle-evidence.md`。

## 1. 当前结果（2026-11-05）

### 1.1 当前工具全量复审

详见 `docs/gem5-fi/fsu/audit/CURRENT-AUDIT.{json,md}`（tool_git_sha 已记录）：

| 范围 | total | current_verified | failed | legacy-only | missing |
|---|---:|---:|---:|---:|---:|
| suite seed | 21 | 20 | 1 | 0 | 0 |
| component | 87 | 82 | 5 | 0 | 0 |
| 非 suite 权威 seed | 35 | 35 | 0 | 0 | 0 |
| 权威 seed 合计 | 56 | 55 | 1 | 0 | 0 |

唯一失败：`FSU-FR03-F5-W5/seed1`。运行标签 `submodel=FR03-c`，冻结 plan
是 `FR03-a`；suite_hash `864c71…` vs `98d881…`。所有 fault 几何值
（mask/polarity/lane/phys）一致。**这是预冻结标签漂移，按事实保留，
不改写 manifest。**

### 1.2 索引双视图

- 历史：admitted **55 / 519 seed**，COMPLETE_3_OF_3 **17 / 173 RunID**，
  2/3 有 2 个（FR03-W3、FR03-W5）。
- 活跃（F0/F5）：**46 / 240 seed**，**14 / 80 RunID** 3/3。
- 较基线各下降 1 seed / 1 RunID，原因即 FR03-W5 seed1。
- 另有 real_outcome seed 1 个：`FSU-FR01-F0-W1/seed1`（不计 admitted）。

### 1.3 FR01/FR02

- 只读门禁 `tools/fsu_fr01_fr02_gate.py`：真实 v4 证据
  （`runs/fsu-gates/FR01-FR02-F0-W1-v4/`）两条 attempt PASS +
  `CONTAINED_BY_FREE_REALLOC`（gen1→gen2，无安装世代 read/commit）。
  报告：`docs/gem5-fi/fsu/evidence/fr01-fr02-v4-gate.json`。
- 新增 C++ 证据：overwrite full_before/fault_mask/target bits、
  post-overwrite read/write 可见性、generation_change、free_realloc /
  squashed 终局。
- 正式 `FSU-FR01-F0-W1/seed1`：attempt-1/2 真实终局 `not_consumed`，
  oracle hash 相同但不能据此判 Masked；保留 `.real_outcome`。
- **2026-11-05 审计结论（替代旧观察）**，详见
  `FR01-FR02-PRF-IDENTITY-AUDIT.md` / `FR01-FR02-PROTOCOL-V2.md`：
  - ARM64 `FloatRegClass` 是 0 寄存器占位；scalar FP 源码/rename 均为
    `VecRegClass`，与 NEON 共享 Vec PRF。旧 v8/v9/v10 探针实际跑的是
    `neon_fp32_lane_kernel`，不能作为 W1 证据。
  - HEAD 存在编译缺陷（`IQUnit::` vs `InstructionQueue::`），
    05f527f2 之后 consumer-aware 代码从未进入二进制。
  - attempt-1/2 的 not_consumed 是真实死槽；v13–v16 证明还存在
    tracking 漏读（generation 过滤、store 在 initiateAcc 读）。
  - 修复：事件级目标选择（consumer execute 前装填）+ `getRegOperand`
    精确读快照 + generation 仅 provenance + 任何真实写终止 +
    precision/field/load_id 事件身份。
- attempt 处置：attempt-3（v1，无 precision，FP32 store，SDC，子模型不符）
  保留不计；attempt-4（v2 FP64）保留；**attempt-5 为权威 seed1**：
  full/admitted/certified、SDC、`fsu_seed_audit ok=true`。
- 采样偏差：V2 是“首个合格消费者事件”，尚非工作簿要求的
  countOnly + uniform ordinal；已登记，不外推为无偏样本。

### 1.4 FQ08 / FP08 / FP05

- FQ08-b/c 与 FP08 回归：67 passed；真实日志复核见
  `docs/gem5-fi/fsu/FQ08-FP08-REGRESSION.md`。
- **2026-11-05 补齐**（`FQ08-FP08-GATE-EVIDENCE.md`）：
  - FQ08-c 新增 `woken` / `delayed_dependents_woken`；真实 Fire 正例：
    dep_chain first_clock=5000 phase=1 → sn=1469, **woken=1**；
    branchy_reduce 同；elemwise_fma Fire 但 woken=0（诚实）。
    squash 忽略有真实样本；generation/free-reuse 真实样本 BLOCKED；
    identity 负例 N/A。
  - FP08 rounding 原因分区真实守恒：
    attempted=73 = applied 20 + no_vec_dest 38 + nonfinite 15，
    `CHAOS_ROUNDING_CONSERVED=1`；不兼容组合运行前 panic（exit 134）。
  - fpsr/rounding 仍是显式代理，不因工具 PASS 升级。
- FP05：**已实现真实 burst 发射端**（`chaos_fsu_burst.hh` + CHAOSFPU
  burstMode/burstLength/... + runner/schema/审计/Markdown 接线）。
  真实 gate：same_lane len 2/3/4、lane_mask、adjacent_lane、
  cross_lane_mbu(32-bit lane) 全部 strict PASS；tail short 显式
  `run_exit` 且 strict FAIL（不冒充完成）；64-bit-lane MBU 因元素宽度
  不匹配 fail closed。证据见 `FP05-BURST-GATE-EVIDENCE.md`。
  未做：正式 F0 试点、merged>1、squash 样本、F4 间隔语义。
- FP06-d 保持 MISSING；FP07 仅允许工作簿明确的字段加权结果代理。

## 2. 已落地补丁（按单元）

1. `[FSU][suite-audit]` 版本化 seed_plan 兼容（1d862dcd）。
2. `[FSU][audit]` 全量当前复审工具（6dd4217b）。
3. `[FSU][index]` 索引改用当前重算（37aed761）。
4. `[FSU][FR01/FR02]` 只读生命周期门禁（b155802f）。
5. `[FSU][FQ08/FP08]` 回归（2391b795）。
6. `[FSU][FP05]` burst 契约门禁（7d361bf0）。
7. `[FSU][FR01/FR02]` 生命周期闭合证据（3621d5a4）。
8. `[FSU][audit]` 复审报告与索引刷新（ed326fab）。
9. `[FSU][FR01/FR02]` real_outcome + consumer-aware 选择（05f527f2）。

## 3. 待办队列

- [x] FR01/FR02：确认 W1 scalar FP 的合法 PRF class（vector vs float）；
      用非正式 directed gate 取得真实 consumer→commit/squash。
      → `VecRegClass`；attempt-5 SDC full/admitted/certified。
- [ ] FR01/FR02：同世代 overwrite、squash、commit、free/realloc、
      连续写、precision/lane fail-closed 的真实样本。
      （overwrite/free-realloc 已在 v4/v13–v19 gate 出现；squash/连续写
      与 FR02 双 bit 审计仍待补。）
- [x] 冻结 FR01-F0-W1 正式配置（ready_consumer + precision 64 + load_id）；
      seed1 attempt-5 审计通过。FR02-F0-W1 配置待建（双 bit + 几何审计）。
- [ ] seed2/3（同一冻结配置；不得为凑数换 target/seed）。
- [ ] FP05 真正 2–4 eligible burst 实现 + burst_id/ordinal/length +
      四处接线；正式计数前 gate 必须从 SKIP 变 PASS。
- [ ] FP07 只实现工作簿允许的字段加权结果代理；FP06-d 保持 MISSING。
- [ ] FQ08-c generation/identity 真实 gate；FP08 组合 fail-closed。

## 4. 阻塞与判定原则

- **FR03-W5 seed1**：证据真实，但身份漂移；不重跑、不改写，保持 2/3。
- **FR01/FR02 formal W1**：seed1 attempt-5 已认证（SDC）；attempt-3/4
  为协议演进保留，不覆盖、不重复计数。V2 采样不是 uniform ordinal，
  不得把多 seed 当无偏样本；countOnly 实现前如实标注。
- **W1 scalar FP**：已证实为 `VecRegClass`；`FloatRegClass` 在 ARM 是
  0 寄存器占位，切换会使注入直接失效。不得用 W3/NEON 结果代替 W1。
- **构建基线**：仓库根 `build/` 不存在；工具使用
  `CHAOS/gem5/build/ARM/gem5.opt`。HEAD 9afebbd2 本身无法编译（已修）。
- **FP05**：实现前 gate 只能 SKIP/BLOCKED，不能开始正式计数。

## 5. 资源与纪律

- 构建 `scons -j16`；正式 gem5 串行或最多 2 并发；失败 attempt 保留。
- 每次提交只含一个单元，提交后 push `origin/fsu`；不 force push。
- `runs/` 被 gitignore；证据文件用显式 `git add -f` 或复制到
  `docs/gem5-fi/fsu/evidence/`。
