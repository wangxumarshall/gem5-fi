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
  oracle hash 相同但不能据此判 Masked；已重分类为 `.real_outcome`，
  **不计正式 seed**。
- 发现：W1 是 scalar FP；`reg_class=vector` 的 Vec PRF 注入在该负载
  找不到 consumer。`arch_frontend` 定向 V0 的非正式 probe
  （`runs/fsu-gates/FR01-FR02-F0-W1-v8/`）取得真实
  operand_read + commit（gen17149），证明 consumer 路径存在，但
  `arch_frontend` 不是 FR01/FR02 的 phys 模型，不能当正式证据。
- 目标选择已优先“IQ 中未发射指令的 pending source”；严格版
  “找不到 consumer 就无限重试”在 `floating_point` probe 中 31 分钟
  未注入且拖慢运行，已 revert（67f8eee8），保留“优先 + 最终回退到
  已分配槽”的版本。Vec 随机目标 probe 仍得到 not_consumed。

### 1.4 FQ08 / FP08 / FP05

- FQ08-b/c 与 FP08 回归：67 passed；真实日志复核见
  `docs/gem5-fi/fsu/FQ08-FP08-REGRESSION.md`。缺口：generation/identity
  真实 gate、activated 正例、rounding 未 applied 原因、模式组合 fail-closed。
- FP05：CHACOSFPU 尚无 burst 发射端，gate 返回 SKIP/BLOCKED；
  设计与 C++ 改动清单见 `docs/gem5-fi/fsu/FP05-BURST-PREP.md`。
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

- [ ] FR01/FR02：确认 W1 scalar FP 的合法 PRF class（vector vs float）；
      用非正式 directed gate 取得真实 consumer→commit/squash。
- [ ] FR01/FR02：同世代 overwrite、squash、commit、free/realloc、
      连续写、precision/lane fail-closed 的真实样本。
- [ ] 冻结 FR01-F0-W1 / FR02-F0-W1 正式配置；seed1 审计通过后
      seed2/3；不得为凑数换 target/seed。
- [ ] FP05 真正 2–4 eligible burst 实现 + burst_id/ordinal/length +
      四处接线；正式计数前 gate 必须从 SKIP 变 PASS。
- [ ] FP07 只实现工作簿允许的字段加权结果代理；FP06-d 保持 MISSING。
- [ ] FQ08-c generation/identity 真实 gate；FP08 组合 fail-closed。

## 4. 阻塞与判定原则

- **FR03-W5 seed1**：证据真实，但身份漂移；不重跑、不改写，保持 2/3。
- **FR01/FR02 formal W1**：当前未认证；不把 not_consumed 当 SDC/失败，
  也不因最终 hash 相同判 Masked。
- **W1 scalar FP**：若确认 VecRegClass 无 consumer，需按工作簿确认
  FloatRegClass 是否属于同一 FP/SIMD PRF 边界；不得用 W3 结果代替 W1。
- **FP05**：实现前 gate 只能 SKIP/BLOCKED，不能开始正式计数。

## 5. 资源与纪律

- 构建 `scons -j16`；正式 gem5 串行或最多 2 并发；失败 attempt 保留。
- 每次提交只含一个单元，提交后 push `origin/fsu`；不 force push。
- `runs/` 被 gitignore；证据文件用显式 `git add -f` 或复制到
  `docs/gem5-fi/fsu/evidence/`。
