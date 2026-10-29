# R6 A 单元（AGU）Lane A 只读诊断报告 — A01 / A02 / A03

- 日期：2026-10-28
- 工作树：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`
- 分支 / HEAD：`fix/r6-a-unit-20261028` / `eab58f35`；权威起点 `659fa4cf`
- 二进制：`CHAOS/gem5/build/ARM/gem5.opt`
  - `sha256sum` 实测 = `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`
  - `ls -la` = 1,145,678,496 B，mtime 2026-10-28 10:01（与任务给定的 binary_source_head=`1f344a5b` 一致）
- 约束遵守：本轮**只读**；未构建、未启动 gem5、未修改除本文件外的任何文件；未删除/移动任何旧证据。
- 范围：A01（A01-F0/F1/F2-W3；A01-F0/F1/F2-W9）、A02（A02-F0/F2-W3；A02-F0/F2-W9）、A03（A03-F5-W3；A03-F5-W10）。

---

## 0. 结论速览（逐 RunID）

| RunID | 建议分类 | 一句话依据 |
|---|---|---|
| A01-F0-W3 | **READY_FOR_CANARY** | 注入点/模式/触发/负载/golden 全部落实；旧真机证据有真实注入（§5） |
| A01-F1-W3 | **ROUTED_NOT_TRIGGERED**（结构性零） | F1 最小首发抽签 500,000 eligible events ≫ 实测流 ~2,773；trial 5 seed activated=0 |
| A01-F2-W3 | **ROUTED_NOT_TRIGGERED**（结构性零） | F2 最小首发抽签 50,000 ≫ 实测流 ~2,773；trial 5 seed activated=0 |
| A01-F0-W9 | **READY_FOR_CANARY** | SE 载体 `gap_bfs` 真实存在、golden 匹配、trial 真机 activated=5/5 |
| A01-F1-W9 | **ROUTED_NOT_TRIGGERED**（结构性零） | 最小 500,000 > 实测 eligible ~265,000/run；trial 5 seed activated=0 |
| A01-F2-W9 | **READY_FOR_CANARY** | 最小 50,000 < ~265,000/run；trial 真机 activated=6 |
| A02-F0-W3 | **READY_FOR_CANARY** | 双 bit 模式落实；trial 真机 activated=5/5 |
| A02-F2-W3 | **ROUTED_NOT_TRIGGERED**（结构性零） | 同 A01-F2-W3（流 ~2,773 < 50,000） |
| A02-F0-W9 | **READY_FOR_CANARY** | trial 真机 activated=5/5 |
| A02-F2-W9 | **READY_FOR_CANARY** | trial 真机 activated=5/5 |
| A03-F5-W3 | **REVIEW_REQUIRED**（必须先修 F5 记账缺陷） | 注入真实发生，但当前源码 F5 的 `trigger.injected` 恒 0 → L5 证据恒 activated=0（§3.4） |
| A03-F5-W10 | **REVIEW_REQUIRED**（同因，另加事件流风险） | 同上；W10 载体 `stream_chase` 存在、golden 匹配 |

> 重要：A 计划（`docs/superpowers/plans/2026-10-28-r6-a-unit.md:23`）把 A01-F0/F1/F2-W9、A02-F0/F2-W9 列为 `BLOCKED_WORKLOAD_GAP`。**本诊断与仓库现状矛盾**：`gap_bfs` 是真实 SE 载体，`R6-STATUS-TABLE.md:54,56,58,60,62` 对这 5 格给出 `eligibility=RUNNABLE`，`ready_contract.json` 的 `upstream_status=READY`（唯一 blocker 是 `CHAIN-EVIDENCE-MISSING`，即“没跑过”，不是 workload 缺失）。详见 §4。

---

## 1. 权威来源核对

### 1.1 runid_map.json（A01–A03 共 12 条）

`docs/gem5-fi/lsu/mdspec/runid_map.json` `entries[]` 中：

| RunID | freq | fault_type | submodels | trigger | workload.binary | golden |
|---|---|---|---|---|---|---|
| A01-F*-W3 | F0/F1/F2 | 单比特翻转 | A01-a EA低位单bit；A01-b EA中位单bit；A01-c EA高位单bit | 任一已完成地址生成 | `agu_addrmodes` | `728e604ffcec539d` |
| A01-F*-W9 | F0/F1/F2 | 同上 | 同上 | 同上 | `gap_bfs` | `030921682b3731f2` |
| A02-F0/F2-W3 | F0/F2 | 双比特翻转 | A02-a 同一EA相邻双bit；A02-b 同一EA非相邻双bit | 同上 | `agu_addrmodes` | `728e604ffcec539d` |
| A02-F0/F2-W9 | F0/F2 | 同上 | 同上 | 同上 | `gap_bfs` | `030921682b3731f2` |
| A03-F5-W3 | F5 | 卡死 | A03-a EA位stuck-at-0；A03-b EA位stuck-at-1 | 首个AGU事件后持续 | `agu_addrmodes` | `728e604ffcec539d` |
| A03-F5-W10 | F5 | 同上 | 同上 | 同上 | `stream_chase` | `50ab96a7fe8f6ec2` |

- 12 条的 `capability_status` 均为 `null`、`pilot.routable=false`（只是“尚无 pilot 证据”的诚实空值，不是技术阻塞）。
- `path_nodes` 均为 `L0→L1→L2→L1→L3→L1→L4→L5`（runid_map 的 L2 TLB 往返表示法）。

### 1.2 coverage_matrix.md

- `docs/gem5-fi/lsu/mdspec/coverage_matrix.md:11-22`：A01-A03 的 12 格状态列均为 `PASS`（这是覆盖/测试轴，不是真机证据轴；不得当作本轮完成证据）。
- 同文件 `:341`：AGU 汇总 `11/11`（模型级，非 RunID 真机）。

### 1.3 频率政策

- `docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json` `entries`：A01/A02/A03 的 12 格全部 `run_policy=NORMAL`、`required_seeds=3`、`schedule_enabled=true`、`include_in_statistics=true`。
- 即：F1/F2/F5 没有被政策降为 stress-only；但**政策可运行 ≠ tier 触发可达**（见 §2.3）。

### 1.4 权威状态表（最新）

`docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md:53-64`：12 格全部
`evidence_state=NOT_RUN / eligibility=RUNNABLE / blocker_code=NONE`；
备注统一为“权威根下无任何 prop_evt 流（未执行）——非 BLOCKED”。

### 1.5 原始 XLSX

未在本轮用 openpyxl 重解（runid_map 与 07 展开矩阵已逐列转写；抽查 `gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md` 第 12 行 A01-F0-W9 与 runid_map 的 fault_type/submodels/freq/workload 一致）。若计划阶段需要对 XLSX 的 A01-A03 行做逐格机器比对，建议由主 agent 用 `openpyxl` 只读复核（本报告以 runid_map 为准）。

---

## 2. A01 — EA 单比特翻转（低/中/高位）

### 2.1 注入点是否存在（实证）

- `CHAOS/gem5/src/cpu/o3/lsq.cc:1258-1314` `LSQ::LSQRequest::sendFragmentToTranslation()`：
  - `:1264-1277` `if (_inst && _inst->cpu && _inst->cpu->chaosAddrPath) { ... maybeCorrupt(r) ... registerInjection("lsq_sendFragmentToTranslation", ...) }` —— 钩子在 `translateTiming`（`:1313`）**之前**，即 DTLB 输入前。
  - `:1285-1311` 随后 `noteMemRequest(...)` + `notePropEvt("lsq_sendfrag", …)`。
- `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:1044-1070` `startup()`：未配置 PRE/A07 时 `o3cpu->setChaosAddrPath(this)`（POST 家族注册），A01-A03 正是此家族（`CHAOSAddrPath.py:29-35` / `.cc:1054-1056` 注释）。
- **结论：注入点存在且已接线。**

### 2.2 fault type 是否真正路由（A01 单 bit）

`CHAOSAddrPath.cc:112-121` `stringToMode`：`"a01_bit" → Mode::A01Bit`；
`CHAOSAddrPath.py:19` 参数说明；`lsu_proxy.py:523-524` 的 `choices` 含 `a01_bit`。
`CHAOSAddrPath.cc:253-267`：

```
const uint64_t band = rng() % 3;
const uint64_t bit = (band == 0) ? rng() % 16
                   : (band == 1) ? 16 + rng() % 24
                   : 40 + rng() % 8;
new_vaddr = vaddr ^ (1ULL << bit);
```

- 单 bit XOR；band 0/1/2 = bit 0-15 / 16-39 / 40-47，符合 48-bit VA 的低/中/高三段定义。
- 每次事件**重新抽 band+bit**（`geom_candidates` 最多 16 次重抽，`:256-265`），无“每 run 固定 target”的锁存。
- **结论：A01-a/b/c 三个子模型都在同一模式里实现，选择由 RNG 逐事件抽样。**

### 2.3 频率 F0/F1/F2 语义是否落实（并给出可达性判决）

`CHAOSAddrPath.cc:60-66` 有 `lsuTier != off` 时构造 `ChaOSLsuTrigger`；
`chaos_lsu_trigger.hh:44` 档位；`:208-226` 间隔常量；`:236-293` 触发决策。

- F0（`chaos_lsu_trigger.hh:257-268`）：`spent` 一次性；首发 `next_fire = warmup + rng%span`；campaign 对 addrpath 非 A07 固定 `warmup=0, span=1000`（`tools/lsu_campaign.py:1116-1120`）。→ **可达**。
- F1/F2（`:269-277` + `:208-217`）：`next_fire = from + iv/2 + rng%iv`，`iv(F1)=1,000,000`、`iv(F2)=100,000`。
  - 实测流：`A01-F0-W3` 旧的 deterministic run `runs/lsu/det/A01-F0-W3/run1/addrpath_injections.log`：
    `CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=2765 eligible=2765 injected=1 activated=1`；
    `A01-F0-W3` trial（`artifacts/lsu-trial/cells/A01-F0-W3/cell_results.json`）`attempted=2773`。
  - ⇒ W3 的 eligible 流 ≈ **2,765–2,773/run**。
  - **F2 的最早一次发射阈值 = 50,000 > 2,773；F1 = 500,000 > 2,773 ⇒ 在 W3 上结构上不可能注入。**
  - Empirics：`artifacts/lsu-trial/cells/A01-F1-W3/cell_results.json` 与 `A01-F2-W3/cell_results.json` 均 `n_runs=5, activated=0`（attempted=13865，即 5×2773 的求和，印证 per-run 2,773）。
- F1-W9：`artifacts/lsu-trial/cells/A01-F1-W9/cell_results.json` `attempted=1,325,080, activated=0`。
  - gap_bfs 的 SE golden `runs/lsu/golden/gap_bfs/g1/stats.txt`：`simInsts=1,093,567`，所以 1,325,080 只能是 5 run 求和 ⇒ **~265,016 eligible/run**（< 500,000）。
  - **⇒ F1 在 W9 上也结构性不可达（实测 activated=0）。**
- F2-W9：`artifacts/lsu-trial/cells/A01-F2-W9/cell_results.json` `activated=6`（5 seed），⇒ 50,000 < 265,016，**可达且实测有注入**。
- **结论：F0 语义落实且可达；F1 在任何现有 A 载体上不可达；F2 仅在 W9 可达。** 这是 tier×workload 的规格级不匹配，不是注入器 bug；campaign 目前**没有** addrpath 版的 `LSQFWD_INTERVAL_UNREACHABLE` 守卫（对比 `tools/lsu_campaign.py:1226-1270`），所以会“诚实但无意义”地跑出 activated=0。

### 2.4 target_index / tier / trigger 是否正确

- **不存在 `target_index` 参数**：`CHAOSAddrPath.py:16-49` 的全部 Param 中没有 target/band/bit 选择项；`grep -rn target_index CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/` 无命中。
- tier 通过 `lsuTier`（`.py:34-35`）→ `ChaOSLsuTrigger`；campaign 通过 `--addrpath_lsu_tier <F>`（`tools/lsu_campaign.py:1109-1122`，`configs/se/lsu_proxy.py:532-538`）下发，模型/档位映射见 `tools/lsu_campaign.py:355`。
- trigger 语义由共享层 `chaos_lsu_trigger.hh` 统一实现（CLAUDE.md 要求的“不手搓概率”）。
- **结论：tier/trigger 正确接入；子模型“目标选择”是 RNG 抽样，没有可钉死的 target_index。**

### 2.5 workload / readfile / oracle 可判定性（W3）

- `workloads/directed/agu_addrmodes.c`：base+imm、base+index、LSL、UXTW/SXTW、pre/post-index、LDP/STP、非对齐、页边界 + store 回读；输出 16 位十六进制 FNV-1a 校验和。
- ELF：`workloads/directed/agu_addrmodes`（aarch64 static，636,776 B）。
- oracle：`tools/lsu_l5_classify.py:86-110` 取 stdout 最后一个 `^[0-9a-f]{16}$` 行，与 golden `728e604ffcec539d`（`tools/lsu_campaign.py:259` GOLDENS）比较；一致=Masked，不一致=SDC。
- **可判定。** 注意：F0 只注入一次，命中的是“首个 eligible 访存”，不保证命中探针里某个特定寻址模式；现有 pilot 的首个注入点是启动期 store/ldp（§5.1），所以“workload 覆盖 10 种寻址模式”不等于“故障落在 10 种模式上”。

### 2.6 子模型动态可达性（不接受字符串存在冒充）

| 子模型 | 实现 | 路由 | 触发 | 结论 |
|---|---|---|---|---|
| A01-a EA 低位单 bit | `.cc:258-262` band0=`rng()%16` | `a01_bit`（`.cc:116`,`.py:19`） | band 逐事件随机 | **LIKELY_ROUTABLE**：每次 F0 注入只抽 1 个 band，3 个正式 seed 不保证覆盖 a/b/c；需额外辅助 canary 或 band pin |
| A01-b EA 中位单 bit | `.cc:260` band1=`16+rng()%24` | 同上 | 同上 | **LIKELY_ROUTABLE**（同上） |
| A01-c EA 高位单 bit | `.cc:261` band2=`40+rng()%8` | 同上 | 同上 | **LIKELY_ROUTABLE**（同上） |

- 证据可判性：注入日志写 `geom_bitmask=0x…`（`.cc:357`），可由 bitmask 反推 band（bit≤15 / 16-39 / 40-47），所以“运行后是否真的覆盖了某子模型”可机判。
- 目前**没有**参数能强制 band ⇒ 要在正式 3 seed 之外补子模型覆盖，只能：(a) 加 `--addrpath_band` 类的 pin（代码改动），或 (b) 增加有界的辅助 canary 并按日志事后归类（计划阶段 5 允许“有界 auxiliary canary，单独标注”）。

---

## 3. A02 — 同一 EA 双比特翻转 与 A03 — stuck-at（F5 持续）

### 3.1 A02 注入实现

`CHAOSAddrPath.cc:268-285`：

```
if (rng() % 2) { b = rng()%46; new = vaddr ^ ((1<<b)|(1<<(b+1))); }      // adjacent
else { b1=rng()%48; b2=rng()%48; if (b1==b2) b2=(b2+1)%48;
       new = vaddr ^ ((1<<b1)|(1<<b2)); }                                // dispersed
```

- 单次事件同时翻 **2 bit**；50% 相邻 / 50% 非相邻；bit 域 0-47（48-bit VA）。
- 模式路由：`"a02_2bit" → Mode::A02DoubleBit`（`.cc:117`）；campaign `--addrpath_mode a02_2bit`（`tools/lsu_campaign.py:356`）。
- 频率 tier 与 A01 完全共用（同触发层），因此 §2.3 的 F1/F2 可达性结论对 A02 同样成立：**A02-F2-W3 结构性零；A02-F2-W9 可达**。
- oracle/readfile 同 A01（同一 agu_addrmodes SE 载体）。

子模型动态可达性：

| 子模型 | 实现/路由 | 触发 | 结论 |
|---|---|---|---|
| A02-a 相邻双 bit | `.cc:273-276` + `.cc:117` | 每次事件 `rng()%2` 50% | **LIKELY_ROUTABLE**（一次 F0 注入只覆盖二者之一；3 seed 不保证都覆盖） |
| A02-b 非相邻双 bit | `.cc:276-279` + `.cc:117` | 同上 50% | **LIKELY_ROUTABLE**（同上） |

- 证据可判性：`geom_bitmask` 的两个 1 位相邻/不相邻可直接判定。

### 3.2 A03 注入实现（stuck-at 持续）

`CHAOSAddrPath.cc:286-295`：

```
if (f5_bit == 64) f5_bit = rng() % 48;          // one fixed bit per run
const Addr mask = 1ULL << f5_bit;
new_vaddr = (stuck0) ? (vaddr & ~mask) : (vaddr | mask);
geom_failed = !geomLegal(new_vaddr);            // fixed bit: decline, never re-draw
```

- 模式：`"a03_stuck0"/"a03_stuck1" → Mode::A03Stuck0/A03Stuck1`（`.cc:118-119`）；`lsu_proxy.py:523-524` choices 齐全。
- **每 run 只锁一个 bit（0-47），从首个 eligible 事件起对每个事件施加 stuck 值** —— 符合“首个 AGU 事件后持续/F5 永久”。
- `new_vaddr == vaddr`（正确值本来就等于卡死值）→ `.cc:332` `obs_post_nochange`，不计注入；几何非法 → `.cc:314-331` `obs_post_geomreject`，不计注入。**这是正确的“no-effect 不算注入”语义。**
- 子模型选择：**不是**注入器参数，而是 campaign 按 seed 奇偶切换模式字符串：
  `tools/lsu_campaign.py:2824-2830`：
  `cmd[i+1] = "a03_stuck0" if seed % 2 else "a03_stuck1"`（`seed` 是 1-based，`:3079-3119` 从 seed=1 起）。
  - 3 个正式 seed = 1,2,3 ⇒ 模式 = `stuck0, stuck1, stuck0` ⇒ **A03-a 与 A03-b 在 3-seed 集合内都能动态到达**。
  - 注意：直接用 `lsu_proxy.py` 手工跑（不经 campaign）默认 `a03_stuck0`，A03-b 必须显式 `--addrpath_mode a03_stuck1`。

### 3.3 A03 频率 F5 语义

- 触发层 `chaos_lsu_trigger.hh:250-256`：F5 `if (!armed && eligible > warmup_events) armed = true; if (!armed) return false; ++fires; return true;` —— warm-up 后**每个 eligible 事件都发射**；campaign 对 A03 传 `warmup=0`（`tools/lsu_campaign.py:1116-1120`），即第 1 个 eligible 事件即 armed。
- 无 `maxFaults` 限制：trigger 路径不读 legacy `max_faults`（`.cc:195-216`），所以 F5 真正“持续到结束/崩溃”。
- **F5 语义在触发层是落实的。**

### 3.4 ⚠ 关键缺陷：AddrPath 的 F5 结果回报缺失 → 当前源码下 A03 证据必然 activated=0

这是本轮最重要的静态发现（不是猜测，是源码路径的事实）：

1. `chaos_lsu_trigger.hh:185-194`：F5 把 **fires** 与 **injected** 分开；`onEligible()` 的 F5 分支只 `++fires`，**不自增 injected**（`:251-256`）；真注入必须由注入器调 `noteOutcome(effective)` 记账（`:295-303`）。
2. 谁调了 `noteOutcome`？全仓 grep：只有 `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`（`:53` 置 `require_outcome_accounting=true`；`:832` 与 `:865` 分别回报 no_effect/effective）。
   - `grep -rn "noteOutcome" CHAOS/gem5/src/` 在 `CHAOSAddrPath/` 下 **0 命中**。
   - `git log -S noteOutcome -- CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/` = 空（从未实现过）。
3. 因此对 A03-F5：`lsuTrigger->injected` **恒为 0**，`no_effect` 恒 0，`fires` = 实际发射次数。
4. 汇总行 `chaos_lsu_trigger.hh:333-355` 会打印 `injected=0 fires=N no_effect=0`；`F5_UNREPORTED_OUTCOME` 告警（`:408-419`）**不会触发**，因为 `require_outcome_accounting` 默认 false 且 AddrPath 从不置 true。
5. `CHAOSAddrPath.cc:987-1010` `notifyFunnelAtInjection()` 写注入日志的 `FUNNEL: attempted=… eligible=… injected=` 用的是 `lsuTrigger->injected`（**0**）；每次注入写一条这样的 FUNNEL 行（`:1005-1008`）。
6. `tools/lsu_l5_classify.py:57-86`：
   - stdout 有 `CHAOS_LSU_TRIGGER … injected=` 时**直接采用**（= 0）；
   - stdout 无该行（崩溃样本）时回退到注入日志的**最后一条 FUNNEL 行**——而 AddrPath 的 per-injection FUNNEL 行写的是 `lsuTrigger->injected`（= 0）。
   - ⇒ **两条路径都得到 injected=0 ⇒ activated=0**，即使真实写入已经发生（注入日志里仍有 `Site:` 行）。
7. 旧的真机 A03 trial（`artifacts/lsu-trial/cells/A03-F5-W3/cell_results.json` `activated=79`、W10 `activated=102`）说明“物理注入确实发生过”，但那批结果早于 F5 fire/injected 分裂（`git log --oneline -S require_outcome_accounting` = `354af1a3` + `02da0d1d`，只改了 trigger 与 ArmTLB），**当前二进制/源码下 A03 会产生“有 Site 行、funnel=0”的自相矛盾证据**。

**判决：A03-F5-W3 / A03-F5-W10 = REVIEW_REQUIRED（必须先修注入器的 F5 outcome 记账），不是 NOT_IMPLEMENTED（物理注入已实现），也不是 READY。** 修法有明确先例：照抄 `CHAOSArmTLB.cc:49-53` + `:832/:865` 的模式，在 `CHAOSAddrPath.cc` 的 F5 路径对每次 fire 调 `noteOutcome(true/false)`，并在 ctor 里 `require_outcome_accounting = true`。

---

## 4. W9（GAP/Graph500）现状核查 —— 对 A 单元不是 BLOCKED

### 4.1 载体存在且是真实可执行体

- `workloads/directed/gap_bfs.c`（2,778 B）：确定性 CSR 图（NV=1024, NE=4096），BFS + SSSP + PageRank 一轮迭代，输出 FNV-1a 校验和。
- `workloads/directed/gap_bfs`：ELF 64-bit LSB ARM aarch64, statically linked（`file` 实测），636,832 B，mtime 2026-10-26 20:19。
- golden：`030921682b3731f2`（runid_map；`tools/lsu_campaign.py:259` GOLDENS 同值）。
- golden 真机对照：`runs/lsu/golden/gap_bfs/g1|g2|g3/stats.txt` 均 `simInsts=1,093,567`（三次确定性一致）。

### 4.2 路由

- `tools/lsu_campaign.py:243` `"GAP/Graph500": "gap_bfs"`（WL_BINARY）；`:1592+ resolve_cell` 对 `family=="addrpath"` 走 SE 分支：`flags = ["--cmd", wl_binary_path(binary), "--cpu", "O3"] + FAMILY_MOUNT["addrpath"] ...`（`:1795-1805`）。
- `WL_BLOCKED`（`:314-338`）只含 `TLB-AliasPerm / Atomic-Litmus / PARSEC / SPEC CPU2017`，**不含 GAP**。
- 唯一硬阻塞是 `T08_W9_WORKLOAD_GAP_RUNIDS`（`:590-591`），精确匹配 `T08-F0/F4/F6-W9`，**不含 A01/A02**。

### 4.3 为什么 T08-W9 仍 BLOCKED，而 A-W9 可以

- `R6-DIAG-C-T08.md:355-415`（T 单元 debugfs 只读复核，含阳性对照）：
  - `debugfs -R "ls -lR /" ubuntu.img | grep -iE 'gap|graph500|bfs|sssp|pagerank' → zero matches`；
  - `grep -aobm1 -i graph500 gem5-fs/ubuntu.img → no hit`（阳性对照 `grep md5sum` 有命中）；
  - `configs/fs/tlb_probe.rcS` 是硬编码 FS 载体（`tools/lsu_campaign.py:778,1638`），armtlb 的 `resolve_cell` 从不把 workload 映射成二进制；
  - T08 的 `TLB::lookup` 注入是 FS-only（SE 走 `translateSe`）。
  - 结论：**T08-W9 的 BLOCKED 是“FS 镜像内无 GAP + armtlb 载体硬编码”造成的 FS-only 事实，不是 GAP 不存在。**
- A 单元是 **SE 家族**，完全不经过 FS 镜像；`gap_bfs` 直接被 `--cmd` 加载。`R6-T-BLOCKED-REVALIDATION.md:260` 也明确写着“GAP 可执行体 SE 版存在”，`R6-DIAG-C-T08.md:407-411` 进一步纠正措辞为“SE-only 是 usage 陈述，不是内在属性”。

### 4.4 FS 镜像状态未变

- 本工作树 `gem5-fs/` 为空目录（worktree 未初始化 submodule）；主仓 `gem5-fs/ubuntu.img` mtime **2026-08-28 13:22:33**、2,361,393,152 B，`vmlinux` 2026-08-28、`boot.arm64` 2026-08-28 —— 自 T 单元复核以来**未变化**。
- **裁决：A01/A02 的 W9 保持 BLOCKED_WORKLOAD_GAP 是不符合事实的；应改为 RUNNABLE（进入 canary 排序）。T08-W9 的 BLOCKED 不受影响。**

---

## 5. 既有 pilot / 旧证据核查（只作诊断参考，不作本轮完成证据）

### 5.1 A01-F0-W3 旧 pilot（文档）

`docs/gem5-fi/lsu/mdspec/pilot_A01-F0-W3.md`：

- RunID/seed/workload：A01-F0-W3；seed 20260826..20260830（s1..s5）；`agu_addrmodes`。
- 二进制 SHA：文档记 `gem5.opt sha256=76d32730878a0f9c…`（**旧二进制**；本轮二进制为 `3db54541…`）。
- 模式：legacy cycle-window + `--addrpath_max_faults 1`（**不是** lsuTier 路径）。
- 真实性：5/5 有真实注入（首个注入点 `dyn_inst_seq=133`，启动 store `strqbfpxi_uop`）；结局 Crash 3 / oracle-clean 2。
- 链：`provable_to_L2_then_unknown`（L0→L1→L2 proven，L2→L3 missing，**不推断 Masked**）。
- 诚实遗留：文档 §1 明确记录“启动 store 的 L2→L3 证据缺口”。

### 5.2 A01-F0-W3 旧 run（r4_6_regress_s10，2026-10-22）

路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_6_regress_s10/A01-F0-W3/seed1/`（**不在本工作树权威 runs 根内**）。

- 命令（`run.out`）：`lsu_proxy --cmd …/agu_addrmodes --cpu O3 --chaos_addrpath --addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000 --addrpath_mode a01_bit --addrpath_rng_seed 1 --chaos_propagation --prop_run_id A01-F0-W3 --prop_sample_run_id s1`。
- 注入日志：`FUNNEL: attempted=412 eligible=412 injected=1` + `Tick: 3187800, Site: lsq_sendFragmentToTranslation, mode=a01_bit, old_vaddr=0x400110, new_vaddr=0x8400110, … geom_bitmask=0x8000000`（真实单 bit 翻转，bit 27 = A01-b 中位）。
- `prop_evt.txt.gz`：6 条事件，L0 inj → L1 addr_form → L2 mem_req/lsq_sendfrag/tlb_translate/tlb_fault；末端 `detection_layer=Hardware`，`outcome=Generic page table fault`。
- `chain_report.json`：`oracle_outcome=Crash, exit_code=-6, truncated=true, terminal=crash_translation_blocked, provable_to=L2`。
- 完整性：`stats.txt` = **0 B**；`gzip -t prop_evt.txt.gz` / `prop_trace.csv.gz` = **unexpected end of file**（崩溃中止，gzip 无 trailer）。⇒ **证据是截断前缀，且无 stats**。
- 二进制 SHA：该 run 目录**没有**记录 SHA；`run.out` 只记“compiled Oct 22 2026”。⇒ **UNKNOWN（无法从该证据自证 SHA）**。
- 同类副本：`r4_6_regress_fsfix/`、`mdspec_campaign_smoke/`、`mdspec_pilot/` 同形（seed1/s1，同样 0 B stats）。

### 5.3 trial 汇总（本工作树 `artifacts/lsu-trial/cells/`）

只有 `cell_results.json`，**没有 run 目录、没有 prop_evt、没有二进制 SHA**，`phase=trial`：

| cell | n_runs | attempted | activated | 结局 |
|---|---|---|---|---|
| A01-F0-W3 | 5 | 2773 | 5 | Masked 1 / Crash 4 |
| A02-F0-W3 | 5 | 2773 | 5 | Masked 1 / Crash 4 |
| A01-F1-W3 | 5 | 13865 | **0** | 全 0 |
| A01-F2-W3 | 5 | 13865 | **0** | 全 0 |
| A02-F2-W3 | 5 | 13865 | **0** | 全 0 |
| A01-F0-W9 | 5 | 530032 | 5 | Masked 2 / Crash 3 |
| A01-F1-W9 | 5 | 1325080 | **0** | 全 0 |
| A01-F2-W9 | 5 | 0 | 6 | Crash 6 |
| A02-F0-W9 | 5 | 530032 | 5 | Masked 2 / Crash 3 |
| A02-F2-W9 | 5 | 0 | 5 | Crash 5 |
| A03-F5-W3 | 3 | 0 | 79 | Crash 79（seed 1/2/76） |
| A03-F5-W10 | 3 | 0 | 102 | Crash 102（seed 1/2/99） |

- 这些是**真实运行的诊断参考**（与 §5.1/5.2 的物理机制一致），但：非权威 runs 根、无流、无 SHA、无 chain_report ⇒ **不得作为本轮完成证据**。
- A03 的 `activated=79/102` 与 §3.4 的“当前源码 funnel=0”并不矛盾：那批 trial 早于 F5 fire/injected 分裂（`354af1a3`/`02da0d1d`），当时 F5 的 injected 仍在 fire 时自增。**当前二进制必须重验。**

### 5.4 与旧 pilot 的关系

- 旧 pilot 证明了：A01 POST 钩子真实注入、L0→L2 逐边可证、Crash/clean 都可机判；
- 但旧 pilot **没有**权威根内的完整 L0→L5，也没有“截断流上的真实 containment”准入（`tools/lsu_chain_check.py:1390-1415` 明确拒绝 `containment_on_truncated_stream` / `containment_on_unclosed_stream`）。
- 本轮 A01/A02 若重跑，预计仍会遇到同类 L2→L3 证据缺口；这是**准入证据缺口**（不阻塞注入本身），需要在 canary 结果出来后按 `check_admission` 的实际判定决定是否补传播钩子（`CHAOS/gem5/src/cpu/o3/CHAOSPropagation` + `lsq_unit.cc` sq_complete/resp），不要先改代码再找证据。

---

## 6. A03-F5 巨型事件流风险评估

### 6.1 每次 F5 生效注入会写什么（逐路径静态核对）

| 位置 | 行为 | 频率 |
|---|---|---|
| `CHAOSAddrPath.cc:339-362` | `chaosL0Register` + `faults_injected_count++` + 注入日志一条 `Site:` 行 | 每个**生效**注入 |
| `CHAOSAddrPath.cc:347,987-1010` | `notifyFunnelAtInjection()` → prop_trace 一个 `funnel` 节点 + 注入日志一条 `FUNNEL:` 行 | 每个**生效**注入 |
| `lsq.cc:1272-1277` | `registerInjection()` → `CHAOSPropagation.cc:797-838`：`++next_ptag`，写 **2 个** prop_trace 节点（`inj` + `addr_form`），并插 addr_registry | 每个**生效**注入 |
| `lsq.cc:1285-1311` | `noteMemRequest()`（`CHAOSPropagation.cc:2183-2240`，每个匹配 registry 条目一个 `mem_req` 节点）+ `notePropEvt("lsq_sendfrag")`（`:650-686`，1 行） | 每个**生效**注入 |
| 下游 | tlb_translate / tlb_fault / resp / consumer 等（视行为） | 视路径 |

- **每次落盘即 flush**：`CHAOSPropagation.cc:482-510` 每写一行 `gzflush(Z_SYNC_FLUSH)`；`writeNode` 同样每节点 flush（`:740-746`）。gzip 压缩率因此显著下降（旧 pilot：6 条事件 ≈ 2.4 KB 原始 → 638 B gz，约 2.7×）。
- 注入日志是普通文本流（`CHAOSAddrPath.cc:91-96` `simout.create("addrpath_injections.log", …)`），**不压缩**；每个生效注入 ≈ 200 B（Site）+ ~50 B（FUNNEL）。
- **没有 tier/事件数上限**：`chaos_lsu_tier_cap.hh` 只是 TLB lookup 的启动能力标记，不是 prop 事件 cap；`CHAOSPropagation.py` 也没有采样率/上限参数。

### 6.2 规模估算（可观测依据）

- agu_addrmodes（W3）：eligible ≈ **2,765/run**（`runs/lsu/det/A01-F0-W3/run1/addrpath_injections.log`）。即使 F5 从第 1 个事件起全部生效，上限 = 2,765 × (~2-4 行 × ~450 B + ~250 B) ≈ **3–6 MB**（gz trace + 文本日志），无风险。
- stream_chase（W10）：`runs/lsu/golden/stream_chase/g1/stats.txt` `simInsts=263,619`；用 gap_bfs 的同口径比例（1.09M inst → ~265k eligible，≈0.24）外推，eligible 量级 **~6×10^4–1×10^5**。
  - 若 stuck bit 良性（等价地址仍映射）且不崩：≈ 10^5 × (0.7–2 KB trace + 0.25 KB log) ≈ **95–225 MB + 25 MB**。可承受但必须监控。
  - 若 stuck bit 致崩（trial 实测：seed1=1、seed2=2、seed3=99 次生效注入后 Crash，`artifacts/lsu-trial/cells/A03-F5-W10/cell_results.json`），实际流被崩点截断，风险大幅缩小。
- **另一个 CPU 风险**：`CHAOSPropagation.cc:310-340 sweepExpired()` 在**每次** registerInjection / noteMemRequest / correlate 时**全表扫描** `addr_registry`；registry 以 `new_addr` 为键（`:837`），默认过期 `addrExpiryTicks=20,000,000`（`CHAOSPropagation.py:23-26`）。长寿命 F5 且地址分散时，registry 可累积数千项，每个事件 O(n) → 整体 O(events×entries) 的明显减速（表现可能像“卡住”）。
- 结论：**A03-F5 的 prop_evt 增长率是“每个生效注入一组 L0-L2 行”，不是每周期重复记录同一污染状态**；没有 tier cap；规模主要由“崩点前生效注入数”决定，W3 有界（≤3–6 MB），W10 最坏 ~100–250 MB 量级。

### 6.3 监控建议（给 canary 执行者）

1. 以 detached tmux 启动首跑；每 10–30 s 记录：`prop_evt.txt.gz` 大小、`addrpath_injections.log` 行数（`grep -c 'Site:'` 与 `grep -c 'FUNNEL:'`）、`ps -o rss` 的 gem5 RSS、`stats.txt` 是否出现。
2. 设软阈值（例如 prop_evt.txt.gz > 512 MB，或 5 分钟无 tick 进展/无日志增长）即判定“事件流失控”，保留目录并 kill；不要用 SIGKILL 掩盖，优先 SIGINT 让 exit callback 落 summary。
3. 强制核对三源：注入日志 `Site:` 数、`CHAOS_L0_FUNNEL` 的 injected、stdout `CHAOS_LSU_TRIGGER` 的 **injected/fires/no_effect**。在 §3.4 未修之前，预计 stdout injected=0 而 Site 行>0 —— 这正是缺陷复现信号。
4. 记录所选 `f5_bit`（当前日志**不打印** bit 编号，只打印 old/new vaddr；建议修复时一并把 bit 写进日志，便于子模型/机理归因）。

---

## 7. 拟修改文件清单（按 owner 区分；本轮未改）

### 7.1 implementation owner（C++，必须与其它 lane 串行）

| 文件 | 改动 | 触发条件 |
|---|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` | **A03-F5 结果记账**：F5 路径每次 fire 调 `lsuTrigger->noteOutcome(effective)`（no-op / geom reject 记 false，真实写入记 true）；ctor 中 `require_outcome_accounting=true`；`notifyFunnelAtInjection()` 的 injected 口径与 applied 对齐（或在 F5 下改用 `l0_funnel.injected`）；日志打印 `f5_bit` | A03 canary **前必须** |
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh` | 如需新增 helper/计数器（f5_bit 输出等） | 同上 |
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py`（可选） | 若裁决要求“子模型可钉死”：加 `--addrpath_band`/`--addrpath_pair` 类 Param；否则不改 | 阶段 5 子模型覆盖的裁决 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` + `lsq_unit.cc`（仅在 canary 证实 L2→L3 缺口阻塞准入后） | POST 家族的 L3 `sq_complete`/`resp` 事件补齐 | 证据驱动，勿先改 |
| `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`（若需） | 不改语义；仅在需要把 F5 funnel 口径统一时动 | 不建议本轮动 |

### 7.2 test / tooling（非 C++）

| 文件 | 改动 | 说明 |
|---|---|---|
| `tools/lsu_campaign.py` | 新增 `ADDRPATH_INTERVAL_UNREACHABLE`（仿 `LSQFWD_INTERVAL_UNREACHABLE`，`:1226-1270`），把 `(A01,F1,W3)/(A01,F2,W3)/(A02,F2,W3)/(A01,F1,W9)` 按“实测流 < 最小首发抽签”响亮拒绝，而不是跑出 activated=0 | **共享工具文件**，需与 Lane B/C 协调唯一 owner |
| `tests/`（新增/扩展 kunit 或 standalone 测试） | A01 band / A02 adjacent 的 bitmask 归类测试；A03 F5 `fires == injected + no_effect` 契约测试；addrpath interval 守卫测试 | 测试文件，非实现 owner |
| `docs/gem5-fi/lsu/mdspec/coverage_matrix.md` / `runid_map.json` | 若主 agent 采纳 §4 裁决，更新 A-W9 的 capability/status 说明（**不要**动 T08-W9） | 文档派生，主 agent 收口 |

> 不建议改 `tools/lsu_l5_classify.py` / `tools/lsu_obs_core.py` 来“容忍 0”：那会把注入器缺陷变成静默的口径漂移；正确做法是修注入器（§3.4），工具侧保持严格。

---

## 8. 风险与未决项（诚实列表）

1. **A03-F5 记账缺陷是阻断项**。静态路径确定；本轮受只读约束**未运行**验证。建议主 agent 在修完后先跑 1 个 A03-F5-W3 seed1 验证 `fires == injected + no_effect` 且 `Site:` 行数 == `CHAOS_L0_FUNNEL.injected`。
2. **F1 在所有现有 A 载体上结构性不可达**；F2 在 W3 不可达。计划阶段 4 的“21 格可执行”需要按此重排（否则会出现 3 seed 全 activated=0 的“合格但空”证据）。这是规格/载体问题，需裁决：加长载体、改 tier 政策，或对 A 单元显式记录 `ROUTED_NOT_TRIGGERED`。
3. **A-W9 的 BLOCKED 分类与仓库现状矛盾**（§4）。请主 agent 在 INITIAL-STATUS 中改判，并注意 `docs/superpowers/plans/2026-10-28-r6-a-unit.md:23` 需要同步修订（计划文件是唯一工作清单）。
4. **A01/A02 的子模型覆盖不可由单次 F0 保证**；需要 pin 或辅助 canary，且辅助 canary 必须单独标注（计划阶段 5 允许）。
5. **L2→L3 证据缺口**（旧 pilot 5/5）会导致“非 full、非显式 containment”的链；而截断/未收口流上的 containment 会被 `lsu_chain_check.py` 明确拒绝（`:1390-1415`）。A01/A02 的可准入性需要在首跑后用真实 `check_admission` 判定，不能预设。
6. **A03 的 bit/子模型可观测性不足**：日志不打印 `f5_bit`，只能用 old/new vaddr 异或推断；建议随 §3.4 修复一起补日志字段。
7. **A03 事件流**：W3 有界；W10 最坏 ~100–250 MB 且 registry 扫描 O(n)，需要 §6.3 的监控；无 tier cap，不要假设工具会自动限流。
8. **旧证据的二进制身份不可自证**：`r4_6_regress_s10` 与 trial 汇总都没有 SHA；pilot 文档的 `76d32730…` 是文档转录。旧证据全部只作诊断参考。
9. **coverage_matrix 的 `PASS` 不是真机证据**；INITIAL-STATUS 不得引用它作为完成依据。
10. **W9 的 FS 镜像**：本工作树 `gem5-fs/` 为空（submodule 未初始化）；主仓镜像 mtime 未变（2026-08-28）。若主 agent 要复核 FS，需在主仓执行 debugfs，且不得改动镜像。
