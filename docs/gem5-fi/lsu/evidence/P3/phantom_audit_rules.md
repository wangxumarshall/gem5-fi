# RULES.md — 幻影激活判定规则（Subagent D，D-2026-10-10-幻影审计 / F-047(a) 扩大审计）

本文件定义"幻影（phantom）"与相邻污染类别的**可复核判据**。全部规则基于三方独立证据源：
(1) `l5_verdict.json`（分类器记录）；(2) `<sample>_guard.out` 中的 `CHAOS_LSU_TRIGGER` stdout 漏斗行
（trigger 层计数）；(3) 样本目录内注入日志（`addrpath_injections.log` / `lsq_fwd_injections.log`，
injector 层实际写入记录 + `CHAOS_L0` / `CHAOS_L0_FUNNEL` 行）。

## 0. 缺陷机制（源码依据）

`CHAOSAddrPath::maybeCorruptPre`（`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:199-332`）：

1. **先触发**（:205-214）：`lsuTrigger->onAttempt()` → `onEligible()`。`onEligible()` 在
   `chaos_lsu_trigger.hh:132/141/145/152/168` 内部**先行 `++injected`**（trigger 层把"fire 决定"
   计为 injected）。
2. **后过滤**（:253-311）：op 类过滤在 fire 之后才执行——
   - load-only 模式 `l01_load_addr`（:309）/`l02_load_state`（:303）：`if (!isLoad) return size;`
   - store-only 模式 `s13_store_addr`（:257）/`s04_store_subst`（:264）/`s05_store_size`（:273）/
     `s11_store_lost`（:294）：`if (isLoad) return size;`
   - 早退路径**不执行** :316-331 的 `chaosL0Register` / `++l0_funnel.injected` /
     `++faults_injected_count` / `write_log`——零故障写入、零日志行。
3. 因此 fire 落错 op 类时：trigger.injected=1，注入日志零写入行。L5 分类器
   （`tools/lsu_l5_classify.py:60-64`）优先读 stdout 的 trigger 行，且 :101 `activated = injected`
   → 幻影样本被记 activated=1；checksum==golden → `Masked`（:94）。**该 Masked 是伪判定：
   从未有故障存在，checksum 一致是空真（vacuous）。**

对照组实证：POST 钩子 `maybeCorrupt`（:100-197）fire 后无 op 类过滤（A01/A02 位翻转必改变 vaddr，
:137-145 XOR 恒变），故 POST 项零幻影——本审计 6 个 POST 项 183 样本全部 trigger==写入==1，实证
缺陷为 PRE 特有。

## 1. 样本级判定规则

对每个 activated=1 样本（`l5_verdict.json` 的 `activated>=1`），按其模型的**实际注入站点**取
写入行数 W（PRE 族 = `Site: lsq_pushRequest_PRE` 行数；POST 族 = `Site: lsq_sendFragmentToTranslation`
行数；L03 = `Site: checkViolations_L03` + `Site: store->load_forward` 行数），trigger 计数 T =
guard.out `CHAOS_LSU_TRIGGER ... injected=N`（abort 样本无此行，T=None）。

### P1 纯幻影（pure phantom）
- **判据**：T >= 1 且 W == 0。
- **佐证（必须至少一条，实测全部命中）**：
  - 日志 `CHAOS_L0_FUNNEL: ... injected=0 activated=0`（injector 自身计数 = 零写入）；
  - 日志 `CHAOS_L0: ... target=0 reads=0 hit=0`（`chaosL0Register` 从未执行）。
- **结论**：trigger 计数与故障写入脱钩；样本不是 activated，原 Masked 判定无效。
- 实测签名样本：`ITEM-271_s1`（T=1, W=0, funnel injected=0, checksum=golden, verdict Masked）。

### P2 部分幻影（partial phantom）
- **判据**：T > W >= 1（多 fire 档 F1-F4 才可能出现；本次审计范围内 F0/F6 单 fire，实测 0 例）。
- **结论**：W 次真实写入 + (T−W) 次幻影 fire；分母按 W 计，幻影 fire 单列。

### N 值等同写入（no-op write）——独立于 P 的第二类污染
- **判据（按模式故障目标，mode-aware）**：
  - `a05_shift`：W >= 1 且写入行 `old_addr == new_addr`（低字节旋转对称，如 0x00/0xFF/旋转不动点）；
  - `a06_size`：W >= 1 且写入行 `old_size == new_size`（目标 size 恰等于原 size，如目标 2 而原 size 已是 2）；
  - `a04_subst`/`a08_subst`：源码 do-while 保证 `cand != addr`（:233-236, :266-268），值等同=异常，实测 0 例；
  - `l01_load_addr`：XOR 位翻转恒变（:310-311），值等同=异常，实测 0 例；
  - `l02_load_state`：**不适用**——故障目标是 `Request::STRICT_ORDER` flag（:304），日志不记录
    flags，`old_addr==new_addr && old_size==new_size` 是 l02 的**预期日志格式**，不是 no-op 证据
    （值等同性不可从日志判定；写入行存在即写入执行确认）。
  - POST 族 A01/A02：XOR 恒变（`old_vaddr != new_vaddr`），实测 0 例。
- **结论**：写入语句执行（有日志行、faults_injected 计数）但故障目标值未变——零故障效果。
  项目内先例：CHAOSAddrPath.cc:156-164 对 A03 stuck-at 的 no-op application 明确
  "logged distinctly so L5 can subtract it from injected (A03's activated 口径)"。
  a05/a06 的 no-op 行未在日志中特别标注，但 old==new 直接可见。

### R 真实写入（real）
- **判据**：W >= 1 且至少一行值变化（按上述 mode-aware 口径）。
- **结论**：故障真实施加；原分类（Masked/SDC/Crash/Timeout）保留。

### uncertain
- 判据：日志缺失 / W 无法判定 / T 与 W 均无。**不得计入有效 activated，单列。** 本次审计 0 例。

## 2. 三方一致性核对（每样本）

| 检查 | 判据 | 实测 |
|------|------|------|
| verdict vs trigger | `l5_verdict.injected` == trigger 行 injected | 全部一致 |
| verdict vs 日志写入 | `l5_verdict.injected` == W | **幻影/noop 样本必然 MISMATCH（verdict>W 或含 noop 行）——这就是污染签名**；其余一致 |
| funnel vs 日志写入 | `CHAOS_L0_FUNNEL.injected` == W | 一致（幻影样本 funnel=0==W，进一步佐证 P1） |
| 行内计数器 | 每写入行 `faults_injected` == 1..W 连续 | 全部一致 |
| 模式匹配 | 日志行 `mode=` == 模型预期 pre_mode | 全部一致 |
| outcome 复算 | 由 guard checksum+golden+exit_code 重推 outcome == verdict.outcome | 全部一致 |
| 官方记录交叉 | 样本级 outcome/injected 与 `ITEM-*_result.json` runs 列表逐项比对 | ITEM-271/279 0 失配 |

stats.txt 说明：CHAOSAddrPath 无 gem5 stat 计数器（stats.txt 中无 CHAOS 故障项，仅
CHAOSLSQFwd 有 numFaultsInjected 等）——addrpath 族三方一致性以日志两行（写入行+漏斗行）为准。

## 3. 项目级修正口径

- `write_confirmed_activated` = R + N + P2 样本数（有实际写入行的样本）。
- `tentative_effective_activated`（暂定有效 activated）= R + P2（**值变化写入**确认的样本；
  N 类剔除分母、单列待裁决——依据 A03 先例；P1 全剔除）。
- 修正五类：P1/N 样本从其原 outcome 类别中逐样本减去（ITEM-271 的 7 个 simfail Crash 均为
  真实写入样本，保留在 post_activation_simulator_failure 单列）。
- 守恒：修正后 五类之和 + simfail == tentative_effective_activated。
- L03（ITEM-285）特记：写入全部落在 checkViolations 站点（33/33），无幻影；但按 F-047(b)
  `--lsqfwd_l03` 未接线（config.ini 实证 structMode=byte_flip），模型身份存疑——单列 caveat，
  不因幻影机制剔除。

## 4. 审计范围判定规则（哪些模型入范围）

| 族 | 模式 | 模型 | fire 后过滤 | 幻影可能 |
|----|------|------|------------|---------|
| PRE op-filtered | l01/l02（load-only）、s04/s05/s11/s13（store-only） | L01 L02 S04 S05 S11 S13 | 有（isLoad/!isLoad） | **有**（本审计实证 L01-F0、L02-F0 中招；S 族 pilot 无样本） |
| PRE unfiltered | a04/a05/a06/a08 | A04 A05 A06 A08 | 无 | 无 op 类幻影；a05/a06 有 N 类（值等同）可能 |
| POST | a01/a02/a03(+F5) | A01 A02 A03 | 无（XOR 恒变） | 无（对照组，实证 0） |
| LSQFwd L03 站点 | violationCorrupt | L03 | 无（:405-407 后直接写入） | 无（写入必然执行；模型身份另有 F-047(b) 问题） |
| LSQFwd corrupt | byte_flip 等 | S01 S02 S03 S08 S09 | `size==0` 早退（:219）在 fire 后 | 理论有（size==0），pilot 无样本 |
