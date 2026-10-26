# R4-8-S10 证据报告：S10 F0/F2 —— 触发窗 vs eligible 流长（worktree `r4-7-s10-span`）

> Agent 1（3-agent closeout）交付。分支 `r4-7-s10-span`，base `d5fc8727`。
> 只读引用二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
> sha256 前缀 **`7d52bc1392a10055`**（本报告全部真机运行都用它）；configs 取**本 worktree**。
> 未构建 gem5（无 scons）；未跑正式 campaign/pilot；未改共享证据目录既有文件。

## 1. 结论速览

| cell | 改前 | 改后 | 依据 |
|---|---|---|---|
| S10-F0-W5 | BLOCKED（平台缺陷 / 窗超流长） | **RUNNABLE**，真机 `injected=1 activated=1` | 路线 (b)：实测窗 span=3 |
| S10-F0-W9 | BLOCKED | **RUNNABLE**，真机 `injected=1 activated=1` | 路线 (b)：实测窗 span=4 |
| S10-F5-W5 | 已激活（`--allow-blocked-models`） | **RUNNABLE（默认路径）** | §R4-6-S10b + MODEL_BLOCKED 移除 |
| S10-F5-W9 | 已激活 | **RUNNABLE（默认路径）** | 同上 |
| S10-F2-W5 | BLOCKED（平台缺陷） | **仍 BLOCKED**，理由=实测结构性不可达 | F2 下界 50000 ≫ 实测流长 3 |
| S10-F2-W9 | BLOCKED | **仍 BLOCKED**，理由=实测结构性不可达 | F2 下界 50000 ≫ 实测流长 4 |

平台缺陷（O3 `StoreSet` SSIT 共享索引策略串表）**已修**（`a2e1f311` / §R4-6-S10），
本报告**不重开**平台修复。S10 的 `MODEL_BLOCKED` 条目已删除（F0/F5 有真机证据，
F2 由逐格拒绝表把关）。

## 2. 真机实测：eligible 事件流（任务书第 1 步）

命令形态（逐字复现；`--lsqfwd_span_events 1000000` 使 F0 draw 永不落，
故 teardown `eligible=` **就是整条流长**；`warmup=1`）：

```bash
flock /tmp/lsu_gem5_slot1.lock -c 'cd <THIS_WORKTREE> && \
  /home/.../lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt \
  --outdir=/tmp/r4-7-s10span/census_sq_forward configs/se/lsu_proxy.py \
  --cmd <THIS_WORKTREE>/workloads/directed/sq_forward --cpu O3 \
  --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 \
  --lsqfwd_span_events 1000000 --lsqfwd_s10 --rng_seed 1'   # (gap_bfs 同形)
```

原始输出（逐字引用，`/tmp/r4-7-s10span/census_<wl>.log`）：

```
# (S10, sq_forward)  —— W5 的 spec 载体「SQ-Forward 转发探针」
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=4 eligible=3 injected=0 first_eligible_tick=3296755 last_eligible_tick=3896970 (activated=W3-L0-layer)
CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSLSQFwd mode=SPAN_UNREACHABLE attempted=4 eligible=3 injected=0 draw_next_fire=756413 span=1000000 warmup=1 (F0 draw never landed inside the observed eligible stream; no injection though the hook fired)
CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd attempted=4 eligible=3 arm1_events=4 arm1_cand_empty=1 arm1_cand_ok=3 max_live_ssids=3 max_cands=3 distinct_arm1_load_pcs=4
```
```
# (S10, gap_bfs)  —— W9 的 spec 载体「GAP/Graph500 子集」
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=5 eligible=4 injected=0 first_eligible_tick=3329095 last_eligible_tick=86106405 (activated=W3-L0-layer)
CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSLSQFwd mode=SPAN_UNREACHABLE attempted=5 eligible=4 injected=0 draw_next_fire=756413 span=1000000 warmup=1 (F0 draw never landed inside the observed eligible stream; no injection though the hook fired)
CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd attempted=5 eligible=4 arm1_events=5 arm1_cand_empty=1 arm1_cand_ok=4 max_live_ssids=4 max_cands=4 distinct_arm1_load_pcs=5
```

**实测 eligible 流长**（= `LSQFWD_F0_SPAN` 新条目）：

| (model, workload binary) | RunID | attempted | **eligible** | arm1_cand_ok | max_live_ssids |
|---|---|---|---|---|---|
| (S10, `sq_forward`) | W5 | 4 | **3** | 3 | 3 |
| (S10, `gap_bfs`) | W9 | 5 | **4** | 4 | 4 |

两条 `CHAOS_LSU_S10_FORK` 行的 `arm1_cand_ok>0 / max_live_ssids>0` 同时**复证平台修复**
（§R4-6-S10 修复前是 `arm1_cand_empty == arm1_events`、`max_live_ssids == 0`）。

## 3. 选定的路线与数字论证（任务书第 2 步）

### 3.1 F0 —— 路线 (b)：R4-1 逐 (model, workload) 实测窗

`resolve_cell` → `_lsqfwd_tier_flags` 对 lsqfwd 家族的 F0 契约（R4-1-review-I2）是：
**窗 span 必须逐 (model, workload) 实测**，未实测的对**响亮拒绝**
（`BLOCKED(F0-span-unmeasured)`），绝不静默复用别对的窗。S10 的两行此前被
**刻意留空**（"census 归集成侧"）——本轮完成普查即补上：

```
("S10", "sq_forward"): 3,
("S10", "gap_bfs"):    4,
```

为什么这**不改语义**：F0 的定义是"warm-up 后在 eligible 事件中**均匀抽样一次**"
（规格 05 + `chaos_lsu_trigger.hh` F0 分支：`next_fire = warmup + rng % span`）。
取 `warmup=1 + span=3` 时 `next_fire ∈ [1,3]`，3 个 eligible 事件各以 1/3 命中——
**这正是"均匀抽样"的精确实现**，对 S01-S09/L03/L04/A07/P06/C11-C15 全都这么用。
"C++ 里 `lastClock` 式的 100000 窗"从未被 S10 采用过；S10 的窗一直是（留空的）
span 表这一条路。

### 3.2 F2 —— 保持 BLOCKED：规格固定的 interval 下界 ≫ 实测流长

F1/F2/F3(/F4) 不消费 span：它们的触发点由 `intervalEvents(tier)` 决定
（`chaos_lsu_trigger.hh`：F1=1e6 / **F2=1e5** / F3=1e4 / F4=1e5），且
`scheduleNext()` 取 `from + iv/2 + rng % iv` ⇒ **首次触发下界 = iv/2**。

- F2 首次触发下界 = 100000/2 = **50000**（eligible 事件）；
- 实测流长 = **3**（`sq_forward`）/ **4**（`gap_bfs`）；
- 差 **4 个数量级** ⇒ 对 spec 指定的 W5/W9 载体**结构性零**，任何 seed 都不落。

为什么**不能**靠调参解决：调 `interval` 就是改故障模型语义（F2 的语义字面就是
"平均每 100,000 个 eligible events 注入 1 次"，05 r3-r5）。**F0 之所以能校准正是
因为它没有 interval**——这个不对称是本轮新增拒绝表的全部理由。

实现：新增拒绝表（逐格、带数字，`resolve_cell` 直出理由字符串）：

```python
LSU_INTERVAL_EVENTS = {"F1": 1000000, "F2": 100000, "F3": 10000, "F4": 100000}
LSQFWD_INTERVAL_UNREACHABLE = {
    ("S10", "F2", "sq_forward"),   # measured stream 3 << min draw 50000
    ("S10", "F2", "gap_bfs"),      # measured stream 4 << min draw 50000
}
```

六格路由器实测输出（`python3 -c` 调 `resolve_cell`）：

```
S10-F0-W5      RUNNABLE  --cmd .../sq_forward --cpu O3 --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 3 --lsqfwd_s10
S10-F0-W9      RUNNABLE  --cmd .../gap_bfs    ... --lsqfwd_span_events 4 ...
S10-F2-W5      BLOCKED(interval-tier-unreachable: model S10 tier F2 on workload sq_forward — the tier's SPEC-FIXED first-fire draw is U[F2/2, 3*F2/2) = at least 50000 eligible events, but the measured eligible stream is 3; ...)
S10-F2-W9      BLOCKED(interval-tier-unreachable: ... measured eligible stream is 4; ...)
S10-F5-W5      RUNNABLE  --lsqfwd_lsu_tier F5 --lsqfwd_warmup_events 0 --lsqfwd_span_events 1000
S10-F5-W9      RUNNABLE  （同形）
S10 in MODEL_BLOCKED: False
```

### 3.3 路线 (a)（长载体）为何**未**采用

(a) 需要构造能持续产出 ≥5×10⁴ eligible 事件的载体。**机理上** eligible 事件对同一
`(store_PC, load_PC)` 对在**每个 `StoreSet::clear()` 周期内只出现一次**
（`store_set.cc` arm-1：两 PC 皆未训练才进；`checkClear()` 每 250000 次访存清表），
故 `eligible 速率 ≈ NSITES / 250000 memops`。把现有载体（NSITES=8）拉长到 5×10⁴ 需要
约 **1.6×10⁹ memops**（≈10¹⁰ 条指令、小时级），远超"数分钟级"的运行预算。

更关键的是**它不是本轮可单方面决定的事**：W5/W9 是**规格钉死的 oracle 载体**
（`sq_forward` golden `1f4cbf14327717df`、`gap_bfs` golden `030921682b3731f2`，
来自 runner.py GOLDEN_IDS）——换/改载体即改 cell 定义与 oracle，属 spec 级裁决。
因此按任务书"若诚实实测后确实结构性不可能，就明确给出数字并保持 BLOCKED"办理。

**建议裁决**（交给 orchestrator/规格侧）二选一：
(a') 为 S10 的 F2 指定一个**长载体**（须一并定义其 golden/oracle 与 W 类语义）；
(b') 明确 S10 不出 F2 cell（或改记 F2 为"spec 载体下不可达"的显式 n/a）。

## 4. 真机验证：F0 真注入（任务书第 3 步，campaign 正式入口）

```bash
LSU_GEM5_BIN=<prebuilt 7d52bc1392a10055> python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /tmp/r4-7-s10span/r4_8_s10_pilot \
  --cells S10-F0-W5,S10-F0-W9 --phase trial --max-seeds-per-cell 1 --max-parallel 1
```

（**无** `--allow-blocked-models`——MODEL_BLOCKED 已删，走默认可跑路径。）

进程汇总逐字：

```
Resolution: {'runnable': 2}
  S10-F0-W5: phase=trial n_runs=1 activated=1 sdc=0 stop=seed-cap(1) cons=OK
  S10-F0-W9: phase=trial n_runs=1 activated=1 sdc=0 stop=seed-cap(1) cons=OK
```

每个 seed 的真机原始行：

```
# S10-F0-W5 / seed1
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=3 eligible=3 injected=1 first_eligible_tick=3296755 last_eligible_tick=3896970 (activated=W3-L0-layer)
CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd attempted=3 eligible=3 arm1_events=4 arm1_cand_empty=1 arm1_cand_ok=3 max_live_ssids=3 max_cands=3 distinct_arm1_load_pcs=4
# lsq_fwd_injections.log:
Tick: 3364515, Site: StoreSet_violation_ssid_assign, mode=ssid_subst (S10-a SSIT-ID 换值), old_ssid=731, new_ssid=144, store_pc=0x40acb0, load_pc=0x400ed8, ssid_candidates=2, faults_injected: 1
CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=3 eligible=3 injected=1 activated=1
```
```
# S10-F0-W9 / seed1
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=2 eligible=4 injected=1 first_eligible_tick=3329095 last_eligible_tick=86106405 (activated=W3-L0-layer)
CHAOS_LSU_S10_FORK: injector=CHAOSLSQFwd attempted=2 eligible=4 arm1_events=5 arm1_cand_empty=1 arm1_cand_ok=4 max_live_ssids=4 max_cands=4 distinct_arm1_load_pcs=5
# lsq_fwd_injections.log:
Tick: 3329095, Site: StoreSet_violation_ssid_assign, mode=ssid_subst (S10-a SSIT-ID 换值), old_ssid=483, new_ssid=528, store_pc=0x40c100, load_pc=0x40adc8, ssid_candidates=1, faults_injected: 1
CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=2 eligible=4 injected=1 activated=1
```

- **两条 cell 都 `injected=1 / activated=1`**（injection 日志非空，带 `old_ssid/new_ssid`
  与候选集合）⇒ F0 通道真机打通。
- W9 的 `attempted(2) < eligible(4)` 是**既有漏斗冻结约定**，非异常：`maxFaults=1`
  命中后 `s10ViolationCb` 在 `onAttempt()` 之前早退（store_set.cc 钩子 1/3 的 (b) 点），
  而 `eligible` 仍由候选臂（subst 钩子）继续计数——与 §R4-6-S10 记录的
  "cap 后漏斗冻结"同型。
- 链（`chain_summary.md`）：两 cell `terminal=provable_to_L1_then_unknown`、
  `provable_to=L1`、`beyond=Unknown`、`events=3`、`oracle=Masked`、`exit_code=0`。
  按纪律**不得**据此推断 Masked：S10 是 PC 键预测器状态故障，L2 之后无链事件，
  `beyond` 保持 Unknown（这是本模型的**正确诚实终局**，与 synthetic 契约测试同旨）。

## 5. 契约测试（任务书第 3 步）

| 测试 | 改前 | 改后 |
|---|---|---|
| `tests/test_lsu_hook_s10.py` | 8 FAIL（"S10 仍在 MODEL_BLOCKED / 无 span 条目 / 6 格全 blocked"） | **75 PASS / ALL PASS** |
| `tests/test_lsu_hook_s10_fork.py` | ALL PASS | **40 PASS**（不受影响） |
| `tests/test_lsu_hook_s10_platformfix.py` | 4 FAIL | **33 PASS（1 段 SKIP）** |
| `tests/test_lsu_hook_c11.py` | ALL PASS | **ALL PASS**（跨模型守卫 S10 子句已按 S10 落地翻转） |
| `tests/test_lsu_hook_c12.py` | ALL PASS | **ALL PASS**（同上） |
| `tests/test_lsu_hook_l04.py` | ALL PASS | **ALL PASS**（同上） |

新增/翻转的断言（要点）：S10 不在 `MODEL_BLOCKED`；`LSQFWD_F0_SPAN` 两条实测值 = 3/4；
`LSQFWD_INTERVAL_UNREACHABLE` 两格存在；`LSU_INTERVAL_EVENTS` 与 trigger 头一致；
**六格逐格解析**（F0 span 必须是实测值、F5 runnable、F2 理由含
`interval-tier-unreachable`）；响亮拒绝不变式（未实测对 → None/拒绝，绝不静默）。

回归：`python3 -m pytest tests/ -q` → **16 passed / 5 errors**，与基线
（commit `302ec9cf` 记录"16 passed + 5 errors（全在 test_claim_concurrency.py）"）
**逐字一致**，零回归。

## 6. 改动文件清单

| 文件 | 改动 | 为什么 |
|---|---|---|
| `tools/lsu_campaign.py` | `LSQFWD_F0_SPAN` 增 S10 两行；新增 `LSU_INTERVAL_EVENTS` + `LSQFWD_INTERVAL_UNREACHABLE` + `_lsqfwd_tier_flags` 拒绝分支；`resolve_cell` 支持字符串理由；删 `MODEL_BLOCKED["S10"]` | F0 实测窗解锁 + F2 逐格响亮拒绝 |
| `tests/test_lsu_hook_s10.py` | 路由/矩阵断言翻转为诚实新态 + 新增拒绝表/interval 常量断言 | 本 change 的契约 |
| `tests/test_lsu_hook_s10_platformfix.py` | [B4] 段翻转为"平台已修 + 逐格门禁" | 同上 |
| `tests/test_lsu_hook_c11.py` / `_c12.py` / `_l04.py` | 跨模型"未误解锁"守卫的 S10 子句翻转 | 本 change 使旧断言失效（避免 collateral 红） |
| `docs/superpowers/plans/2026-10-22-r4-8-s10-span.md` | 新增计划 | CLAUDE.md plan-driven 要求 |
| 本文件 | 新增证据 | 任务书第 4 步 |

未改：维修后的 C++（平台修复已由 `a2e1f311` 落地，本 worktree 不构建）、
`MODEL_FLAGS["S10"]`、`tools/lsu_prop_fields.py`（S10 字段早已注册）、
`tools/lsu_runid_map.py` / `runid_map.json` / `blocked_triage.md` /
`round4_findings.md`（共享证据，见 §7 待办）。

## 7. 仍 BLOCKED / 待 orchestrator 处理

**仍 BLOCKED（不是我的轮次能解、需 spec 裁决）**
- `S10-F2-W5`、`S10-F2-W9`：**结构性不可达**。数字：F2 interval=100000（规格固定），
  首次触发下界 50000；实测 eligible 流长 3 / 4。**差 4 个数量级。**
  出路见 §3.3 的 (a')/(b') 二选一。

**orchestrator 需在集成时做**
1. **台账/证据合并**：把本报告的 §R4-8-S10 追加进 `round4_findings.md`；
   订正 `blocked_triage.md` 的 S10 行（6 行 PLATFORM-DEFECT → F0/F5 解锁 + F2
   结构性不可达）；订正 `runid_map.json` / `tools/lsu_runid_map.py` 的 S10
   `campaign:` 字段（现仍写 `BLOCKED(platform-defect ...)`，已过时）——
   这些是共享文件，本 worktree 未改以免冲突。
2. **矩阵重生成**：S10 六格状态重算（F0×2、F5×2 → READY 侧；F2×2 → BLOCKED
   理由改 `interval-tier-unreachable`）。覆盖矩阵计数会变。
3. **构建/普查/pilot/链检**：本轮**用既有二进制 `7d52bc1392a10055`** 完成，
   未构建。若集成侧有新 build，建议按其二进制复核 F0 两格（命令见 §4）并跑
   3 seed 的 pilot + 逐边链检。
4. **跨模型 F2 同类问题（本轮**只登记不处理**）**：同样的 `interval/2 > 实测流长`
   条件对**其他 lsqfwd 家族 F2 cell 同样成立**（`S01/S02/L01/L02/L04/S04-S06/
   S08/S09/S13` 的 F2-* 共 **26 格**，实测流长 2-5597，F2 下界 50000）。
   本轮按 one-patch-per-unit 只覆盖 S10，未把这 26 格一并 re-block。
   ——**若规格认为 F2 应当机立断拒绝，这是一个需要统一裁决的面。**
5. **既有红测试（非本轮引入，勿混入本轮）**：`tests/test_lsu_hook_p06.py` 的
   "后续模型未误解锁"守卫在 **base `d5fc8727` 上即为红**，根因是 C14/C15 早已
   解锁而该守卫仍要求其 BLOCKED（他人遗留，本轮按"不碰他人遗留"未改）。
   `test_lsu_hook_cpf.py` / `_tlb.py` / `test_lsu_obs_e2e_select.py` /
   `test_lsu_geom_distribution.py` / `test_lsu_campaign_propagation.py` /
   `test_lsu_obs_driver_workers.py` 的失败同样在 base 上即存在（分别因需已构建
   二进制 / 与 S10 无关）。

## 8. 未能验证 / 诚实边界

- **未构建 gem5**（任务书禁止）。所有结论基于既有二进制 `7d52bc1392a10055`。
  若该二进制与集成侧最终二进制不同，F0 两格需按 §4 命令复核。
- **只跑了 1 seed/cell**（预算：全程 4 次 gem5 运行：2 次普查 + 2 次 pilot 格），
  未做 3-seed pilot 与逐边链检——那属 orchestrator 的集成步骤。
- **路线 (a)（长载体）未做实测**：§3.3 的"小时级 / 1.6×10⁹ memops"是**由源码机理
  推得的估算**（arm-1 每对每清表周期一次 + 清表周期 250000 memops），**不是实测**。
  若 orchestrator 要走 (a')，应先做一次标定run 再定。
- **F2 的零是本模型推导 + 规格字面**（`intervalEvents(F2)=1e5`、`scheduleNext` 的
  `iv/2 + rng%iv`），未用一次真实 F2 运行去"观测到零"——因为已知其必为零，跑它
  只会消耗预算并产出一个空洞的 `activated=0`（正是本 change 要避免的静默态）。
- `runid_map.json` / `blocked_triage.md` / `round4_findings.md` **未改**（共享文件，
  避免与并行 agent 冲突）；其内容与 §1 的结论存在**已知的暂时不一致**，见 §7.1。
