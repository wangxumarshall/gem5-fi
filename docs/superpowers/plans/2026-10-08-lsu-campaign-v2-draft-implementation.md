# LSU Campaign v2 Draft 实施计划（F-038 采样政策迁移，隔离实施）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在隔离副本 `tools/draft/lsu_campaign_v2.py` 上实施 MIGRATION_DESIGN.md 冻结的修改点（M1-M11 + 本计划论证新增的 M12）与测试 T1-T10，使 P4 正式筛查引擎就绪——波次 5 运行期间**绝不触碰** `tools/lsu_campaign.py`。

**Architecture:** 每任务一个 commit（one patch per unit），TDD：先写失败测试→实现→通过→提交→中继。顺序：政策核心（目标解析/停止规则/常量）→ 事件账目（两层率/sim_fail 剔除）→ config_fp + verdict 落盘 + resume 前缀 → 回归门（常量接口零变更 + dry-run 冒烟比对）。测试用 stdlib unittest + mock `run_single_cell`（不跑 gem5）。

**Tech Stack:** Python 3.9.9（login01；stdlib only：unittest/importlib/tempfile/hashlib/json；无 pytest）。

**Spec:** `tools/draft/MIGRATION_DESIGN.md`（0994fe60 冻结版：政策依据、KEY_RUNIDS 21 项名单、M1-M11 行号表、T1-T10、六条应用条件）。

## Global Constraints

- **绝不修改 `tools/lsu_campaign.py`**（波次 5 运行中 `lsu_unit_pilot.py` 的 import 依赖，F-023 教训）；每任务后 `git diff --stat tools/lsu_campaign.py` 必须为空。
- **常量接口零变更**：WL_BINARY / GOLDENS / WL_BLOCKED / MODEL_FLAGS / FAMILY_SEED / COL_* / G5 / LSU_PROXY / L5 / REPO 在 draft 与正式文件间必须相等（T10 门）。
- **应用（替换正式文件）不在本计划范围**——须待 MIGRATION_DESIGN.md 六条安全边界条件全部满足后另行执行（WAVE_DONE + 无进程 + 四槽空 + guard 安静 + 无引用 + 测试全 PASS）。
- **诚实性**：unknown 率写 None（JSON null），禁止伪造 0；funnel 缺失 run 单列计数（`funnel_missing_runs`）。
- Python 3.9 兼容（运行时路径无 match 语句/无 PEP604 求值——E-009 教训）。
- commit 前缀 `[LSU][P3]`，禁止 Co-Authored-By 尾注，显式路径 `git add`，禁止 `git add -A`。
- 每任务验证三件套：`python3 -m py_compile` + 单测真实输出 + `git diff --stat tools/lsu_campaign.py` 为空。
- 每任务提交后中继：Windows `git fetch nscc fi-ding` → `git merge --ff-only nscc/fi-ding` → `git push origin fi-ding`。

## 设计偏差（对冻结设计的补充，已论证）

- **M12（本计划新增，必须）**：draft 副本原样保留 `REPO = Path(__file__).resolve().parent.parent`，在 `tools/draft/` 深度下解析到 `tools/`（错误——G5/LSU_PROXY/L5/workloads 路径全部失效，draft 不可运行不可测）。改为向上查找标记目录（`configs/se` 存在）的深度无关实现；文件未来复制回 `tools/` 时解析结果与原式一致（T10 的 REPO 相等断言守护应用时不回退）。
- **D1（M7/M9 实现细节）**：C 系列（legacy firstClock）/FS/Timeout 路径无 `CHAOS_LSU_TRIGGER` 行 → `attempted`/`eligible` 为 None。账目规则：`funnel_missing_runs` 计数单列；`attempted`/`eligible` 只从有 funnel 的 run 累计；`attempted==0` 或全缺失 → `eligible_rate`/`activation_rate` = None（不伪造）。
- **D2（不改项明确化）**：`_wilson_stats` 仅用于报告（M6 删除的是**停止判断**）；其输入语义（F0: SDC/activated；F1-F4: per-run k/n）保留不动；`sdc_rate` 的新分母（activated−sim_fail）不回灌 Wilson 报告字段——如需对齐留待应用前评审。
- **D3（证据保全）**：fp 不一致的旧 verdict / 旧 `cell_results.json` 改名保留（`l5_verdict.fp_<oldfp>.json` / `cell_results.fp_<oldfp>.json`），不覆盖不删除——"不静默混合"的落盘形态。

---

### Task 0: 计划入库 + 所有权声明

**Files:**
- Create: `docs/superpowers/plans/2026-10-08-lsu-campaign-v2-draft-implementation.md`（本文件）
- Modify: `docs/gem5-fi/lsu/progress.md`

**Interfaces:**
- Produces: 本计划（Task 1-4 的依据）；progress.md 中集群会话对 F-038 draft 实施的所有权声明（并行会话可见，防撞车）。

- [x] **Step 1: 写本计划文件**（本文件即产物）
- [ ] **Step 2: progress.md 所有权声明**

在 Session 002 的唯一下一动作（line ~118）末尾插入：
```
；⑤F-038 draft 实施（集群平台工程轨道承接：tools/draft/lsu_campaign_v2.py M1-M12 + T1-T10，MIGRATION_DESIGN.md 冻结设计，绝不触碰 tools/lsu_campaign.py 正式文件——应用待六条安全边界）。
```
并将 dashboard Current Owner 行中 Session 002 括号内"U3 LSU_GEM5_BIN 接线完成；下一步 U6 守卫复验"更新为"U1/U3b/U3/U6 全部完成；现承接 F-038 campaign v2 draft 实施（tools/draft/ 隔离）"。

- [ ] **Step 3: 提交 + 中继**

```bash
git add docs/superpowers/plans/2026-10-08-lsu-campaign-v2-draft-implementation.md docs/gem5-fi/lsu/progress.md
git commit -m "[LSU][P3] F-038 draft 实施计划：集群承接 campaign v2 采样政策迁移（M1-M12 + T1-T10，tools/draft/ 隔离，不触碰正式文件）"
```
中继（PowerShell，Windows 克隆）：`git fetch nscc fi-ding; git merge --ff-only nscc/fi-ding; git push origin fi-ding`。

---
### Task 1: 采样政策核心（M1-M6 + M12）— 测试 T1/T2/T3/T8

**Files:**
- Modify: `tools/draft/lsu_campaign_v2.py`（docstring、REPO、常量块、CLI、run_cell_adaptive 目标解析与停止块）
- Create: `tools/draft/test_campaign_v2.py`（helpers + PolicyTests）

**Interfaces:**
- Consumes: MIGRATION_DESIGN.md M1-M6 定义；KEY_RUNIDS 21 项名单（冻结，不得依结果增删）。
- Produces: 模块常量 `KEY_RUNIDS`（frozenset, 21 项）、`SCREENING_TARGET=385`、`MAIN_TARGET_KEY=2401`；函数 `resolve_main_target(runid, args) -> int`（KEY→2401，否则 `args.screening_target`）；`--main-target` default=None（deprecated、传入即 stderr 警告、不参与解析）；`--wilson-stop-hw` 保留形参（deprecated，不参与任何停止判断）；main 阶段 Wilson 停止块删除；`REPO` 深度无关解析。Task 2/3 依赖 `resolve_main_target` 与这些常量；测试 helpers（`load_draft`/`make_cell`/`Args`/`MATRIX`）供 Task 2-4 复用。

- [ ] **Step 1: 写失败测试（test_campaign_v2.py 首建）**

```python
#!/usr/bin/env python3
"""tools/draft/test_campaign_v2.py — MIGRATION_DESIGN.md T1-T10（+fp 隔离）
mock run_single_cell；不跑 gem5。运行：python3 tools/draft/test_campaign_v2.py -v
（单类：python3 tools/draft/test_campaign_v2.py PolicyTests -v）"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS = REPO_ROOT / "tools"
DRAFT = TOOLS / "draft" / "lsu_campaign_v2.py"
MATRIX = REPO_ROOT / "runs/lsu/07-expanded-matrix-backfilled.csv"


def load_draft():
    sys.path.insert(0, str(TOOLS))  # draft 依赖 `from wilson import wilson_ci`
    spec = importlib.util.spec_from_file_location("lsu_campaign_v2", DRAFT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def make_cell(runid="A01-F0-W3", model="A01", freq="F0",
              workload="STREAM+PointerChase (W3)"):
    # CSV 行：col1=RunID col2=Model col3=Unit col7=Freq col9=Workload
    row = [""] * 10
    row[1], row[2], row[3], row[7], row[9] = runid, model, "AGU", freq, workload
    return row


class Args:
    phase = "trial"
    trial_target = 30
    screening_target = 385
    main_target = None
    wilson_stop_hw = 0.02
    max_seeds_per_cell = 1000
    timeout = 300
    fs_checkpoint = None


class PolicyTests(unittest.TestCase):
    def test_T1_key_runids_resolve_2401(self):
        m = load_draft()
        a = Args()
        self.assertEqual(len(m.KEY_RUNIDS), 21)
        for rid in sorted(m.KEY_RUNIDS):
            self.assertEqual(m.resolve_main_target(rid, a), 2401, rid)

    def test_T2_non_key_resolve_385(self):
        m = load_draft()
        a = Args()
        header, cells = m.load_matrix(str(MATRIX))
        runids = {c[m.COL_RUNID] for c in cells}
        self.assertGreaterEqual(len(runids), 300)
        self.assertTrue(m.KEY_RUNIDS <= runids,
                        "KEY runid absent from matrix: %s"
                        % sorted(m.KEY_RUNIDS - runids))
        non_key = runids - m.KEY_RUNIDS
        for rid in non_key:
            self.assertEqual(m.resolve_main_target(rid, a), 385, rid)
        print("T2: matrix runids=%d key=21 non_key=%d"
              % (len(runids), len(non_key)))

    def test_T3_no_nonkey_gets_2401(self):
        m = load_draft()
        a = Args()
        a.main_target = 2401  # 即使错误地传入全局 2401 也不得泄漏给非重点项
        header, cells = m.load_matrix(str(MATRIX))
        for c in cells:
            rid = c[m.COL_RUNID]
            want = 2401 if rid in m.KEY_RUNIDS else 385
            self.assertEqual(m.resolve_main_target(rid, a), want, rid)

    def test_T8_legacy_knobs_do_not_stop(self):
        m = load_draft()
        calls = []

        def mock(cell, args, seed, outdir):
            calls.append(seed)
            return {"outcome": "Masked", "activated": 50, "attempted": 60,
                    "eligible": 55, "injected": 50}

        m.run_single_cell = mock
        with tempfile.TemporaryDirectory() as td:
            a = Args()
            a.phase = "main"
            a.main_target = 5000        # 旧全局 5000：必须被忽略
            a.wilson_stop_hw = 0.5      # 旧序贯停止：必须被忽略
            m.run_cell_adaptive(make_cell(runid="X99-F0-W0"), a, Path(td))
            self.assertEqual(len(calls), 8)    # 385/50 → 8 runs
            calls.clear()
            m.run_cell_adaptive(make_cell(runid="A01-F0-W3"), a, Path(td))
            self.assertEqual(len(calls), 49)   # 2401/50 → 49 runs


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 tools/draft/test_campaign_v2.py PolicyTests -v
```
预期：FAIL/ERROR——`AttributeError: module 'lsu_campaign_v2' has no attribute 'KEY_RUNIDS'`（或 resolve_main_target 不存在）。

---
- [ ] **Step 3: 实现 M1-M6 + M12（全部在 tools/draft/lsu_campaign_v2.py）**

3a. **M12 REPO**——替换 `REPO = Path(__file__).resolve().parent.parent` 为：
```python
# M12: 深度无关 repo 根——draft 位于 tools/draft/（比正式文件深一层），
# parent.parent 会错解析到 tools/。向上查找标记目录；复制回 tools/ 后
# 解析结果与原式一致（T10 REPO 相等断言守护）。
_REPO = Path(__file__).resolve()
while not (_REPO / "configs" / "se").is_dir() and _REPO.parent != _REPO:
    _REPO = _REPO.parent
REPO = _REPO
```

3b. **M1 docstring**——模块 docstring 中 Phase 3 两行替换为：
```
  Phase 3 (main): fixed-sample — the 21 frozen KEY_RUNIDS (task_plan
                   D-2026-10-08-采样) accumulate to MAIN_TARGET_KEY=2401;
                   every other RunID stays at the screening target (385,
                   no expansion). No sequential stop — Wilson 95% is
                   reported, never a stop condition (2026-10-08 policy).
```

3c. **M2 常量**——插入 GOLDENS 块之后：
```python
# ---- 2026-10-08 sampling policy (task_plan 全局实验口径,
# D-2026-10-08-采样; tools/draft/MIGRATION_DESIGN.md M2) ----
KEY_RUNIDS = frozenset({
    "A01-F0-W3", "A04-F0-W3", "T10-F0-W4", "T04-F0-W4",
    "S13-F0-W5", "S04-F0-W5", "L01-F0-W5", "L03-F0-W5",
    "C04-F0-W6", "C05-F0-W6", "C10-F0-W6", "C12-F0-W6",
    "O01-F0-W7", "O05-F0-W7", "P03-F0-W8", "P07-F0-W8", "P09-F0-W6",
    "T10-F0-W11", "S13-F0-W12", "O09-F0-W13", "P09-F0-W13",
})
SCREENING_TARGET = 385   # 全部有效 RunID 累计 activated 目标
MAIN_TARGET_KEY = 2401   # 仅 KEY_RUNIDS 累计 activated 目标


def resolve_main_target(runid, args):
    """M3/M5: main 阶段目标按 RunID 解析——KEY_RUNIDS→2401，其余→
    screening 目标（不扩样）。--main-target 已废弃，不参与解析。"""
    return MAIN_TARGET_KEY if runid in KEY_RUNIDS else args.screening_target
```

3d. **M3/M4 CLI**——替换两个 add_argument：
```python
    p.add_argument("--main-target", type=int, default=None,
                   help="[deprecated 2026-10-08] ignored — main-phase target "
                        "resolves per RunID (KEY_RUNIDS→2401, others→"
                        "screening-target)")
    p.add_argument("--wilson-stop-hw", type=float, default=0.02,
                   help="[deprecated 2026-10-08] ignored — fixed-sample "
                        "policy; Wilson 95% is reported, never a stop")
```
并在 `a = p.parse_args()` 与 n_seeds 归并之后追加：
```python
    if a.main_target is not None:
        print("warning: --main-target is deprecated (2026-10-08 sampling "
              "policy) and ignored; main target = 2401 for KEY_RUNIDS, "
              "else screening-target", file=sys.stderr)
```

3e. **M5 目标解析**——run_cell_adaptive 内替换：
```python
    target = {"trial": args.trial_target,
              "screening": args.screening_target,
              "main": args.main_target}[args.phase]
```
为：
```python
    if args.phase == "main":
        target = resolve_main_target(runid, args)   # M5: KEY→2401 其余→385
    else:
        target = {"trial": args.trial_target,
                  "screening": args.screening_target}[args.phase]
```

3f. **M6 停止块删除**——删除整个块：
```python
        if args.phase == "main" and activated > 0:
            hw, _lo, _hi = _wilson_stats(classes, activated, runs, clustered)
            if hw <= args.wilson_stop_hw:
                stop_reason = "wilson-halfwidth(%.4f<=%.2f)" % (hw,
                                                            args.wilson_stop_hw)
                break
```
并将 run_cell_adaptive docstring 中 main 停止描述行替换为：`main: fixed-sample — KEY_RUNIDS→2401, others→screening target; no sequential stop (2026-10-08 policy)`。

- [ ] **Step 4: 运行确认通过**

```bash
python3 tools/draft/test_campaign_v2.py PolicyTests -v
```
预期：4 tests OK（T1/T2/T3/T8），T2 打印实际 runids/non_key 计数。

- [ ] **Step 5: 验证三件套 + 提交 + 中继**

```bash
python3 -m py_compile tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git diff --stat tools/lsu_campaign.py   # 必须为空
git add tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git commit -m "[LSU][P3] campaign v2 draft M1-M6+M12：固定样本政策核心（KEY_RUNIDS 21 项→2401 / 其余 385、废弃 main-target 与 wilson 序贯停止、REPO 深度无关）+ T1/T2/T3/T8"
```
中继同 Task 0 Step 3。

---
### Task 2: 事件账目两层率（M7-M9 + D1）— 测试 T5/T6

**Files:**
- Modify: `tools/draft/lsu_campaign_v2.py`（run_cell_adaptive 累计段与 result 组装段）
- Modify: `tools/draft/test_campaign_v2.py`（追加 AccountingTests）

**Interfaces:**
- Consumes: Task 1 的 helpers（`load_draft`/`make_cell`/`Args`）；`run_single_cell` 返回 dict 的既有键（`outcome`/`activated`/`attempted`/`eligible`/`injected`/`crash_kind`）。
- Produces: run_cell_adaptive 累计器（attempted/eligible 只从有 funnel 的 run 累计；`sim_fail` = outcome==Crash 且 crash_kind==simulator_assert 的 activated 之和，单列不计入五类）；result 新增键：`eligible`、`sim_fail`、`funnel_missing_runs`、`eligible_rate`（eligible/attempted）、`activation_rate`（activated/eligible）、`sdc_rate`（SDC/(activated−sim_fail)）——三者分母为 0 时 **None**（禁止 0.0）；runs 记录增 `crash_kind`/`attempted`/`eligible`（可 null）。conservation 判定变为 `activated == sum(classes) + sim_fail`。Task 3 在此结构上叠加 resume（`_acc` 闭包化）。

- [ ] **Step 1: 写失败测试（追加到 test_campaign_v2.py，`if __name__` 块之前）**

```python
class AccountingTests(unittest.TestCase):
    def _run(self, m, mock_results, runid="A01-F0-W3", freq="F0",
             trial_target=15):
        seq = list(mock_results)

        def mock(cell, args, seed, outdir):
            return seq[seed - 1] if seed <= len(seq) else seq[-1]

        m.run_single_cell = mock
        a = Args()
        a.phase = "trial"
        a.trial_target = trial_target
        a.max_seeds_per_cell = 100
        with tempfile.TemporaryDirectory() as td:
            m.run_cell_adaptive(make_cell(runid=runid, freq=freq), a, Path(td))
            return json.loads((Path(td) / runid / "cell_results.json")
                              .read_text())

    def test_T5_simfail_excluded_from_sdc_denominator(self):
        m = load_draft()
        r = self._run(m, [
            {"outcome": "SDC", "activated": 5, "attempted": 6,
             "eligible": 5, "injected": 5},
            {"outcome": "Crash", "crash_kind": "simulator_assert",
             "activated": 10, "attempted": 10, "eligible": 10,
             "injected": 10},
        ])  # 5+10=15 ≥ trial_target=15 → 恰好 2 runs
        self.assertEqual(r["activated"], 15)
        self.assertEqual(r["sim_fail"], 10)
        self.assertEqual(r["classes"]["SDC"], 5)
        self.assertEqual(r["classes"]["Crash"], 0)      # sim_fail 单列
        self.assertEqual(r["sdc_rate"], 1.0)            # 5/(15-10)
        self.assertEqual(r["eligible"], 15)
        self.assertEqual(r["eligible_rate"], 0.9375)    # 15/16
        self.assertEqual(r["activation_rate"], 1.0)     # 15/15
        self.assertEqual(r["conservation"], "OK")       # 5+10 == 15

    def test_T6_zero_denominator_rates_none_not_zero(self):
        m = load_draft()
        r = self._run(m, [
            {"outcome": "Masked", "activated": 0, "attempted": 0,
             "eligible": 0, "injected": 0},
        ], trial_target=5)  # 永不达标 → seed-cap(100)…改用小 cap 更快：
        self.assertIsNone(r["sdc_rate"])      # 分母 0 → None，不是 0.0
        self.assertEqual(r["classes"]["Masked"], 0)    # 计数保留
        self.assertEqual(r["stop_reason"], "seed-cap(100)")

    def test_D1_funnel_missing_counts_separately(self):
        m = load_draft()
        r = self._run(m, [
            {"outcome": "Timeout", "activated": 0, "attempted": None,
             "eligible": None, "injected": None},
        ], trial_target=5)
        self.assertEqual(r["funnel_missing_runs"], 100)  # 每 run 都缺 funnel
        self.assertIsNone(r["eligible_rate"])
        self.assertIsNone(r["activation_rate"])
```

注意 test_T6/test_D1 用 `max_seeds_per_cell=100` 会跑 100 个 mock run（快，纯内存）——若嫌慢可把 `a.max_seeds_per_cell = 3`，对应 stop_reason 断言改 `"seed-cap(3)"`、funnel_missing 断言改 3。实现时选小 cap 版本（3 runs）以保持测试秒级。

- [ ] **Step 2: 运行确认失败**

```bash
python3 tools/draft/test_campaign_v2.py AccountingTests -v
```
预期：KeyError/AssertionError——result 无 `sim_fail`/`sdc_rate` 新语义（旧 sdc_rate=SDC/activated 或 0.0）。

- [ ] **Step 3: 实现 M7-M9 + D1**

3a. run_cell_adaptive 计数器初始化段替换为：
```python
    runs, attempted, eligible = [], 0, 0
    activated = sim_fail = funnel_missing = 0
```

3b. 循环体内（`seed += 1` 与 `r = run_single_cell(...)` 之后）替换累计段为：
```python
        act = int(r.get("activated", 0) or 0)
        runs.append({"seed": seed, "cluster_id": "%s#%d" % (runid, seed),
                     "activated": act,
                     "outcome": r.get("outcome", "Unclassified"),
                     "crash_kind": r.get("crash_kind"),
                     "attempted": r.get("attempted"),
                     "eligible": r.get("eligible")})
        if r.get("attempted") is None or r.get("eligible") is None:
            funnel_missing += 1          # D1: legacy/FS/Timeout 无 funnel 行
        else:
            attempted += int(r["attempted"])
            eligible += int(r["eligible"])
        activated += act
        oc = r.get("outcome")
        if oc == "Crash" and r.get("crash_kind") == "simulator_assert":
            sim_fail += act              # M7: post_activation_simulator_failure
        elif oc in classes:
            classes[oc] += act
```

3c. result 组装段替换（保留旧键、新增 M7-M9 键）：
```python
    hw, lo, hi = _wilson_stats(classes, activated, runs, clustered)
    denom = activated - sim_fail                       # M8
    sdc_rate = (classes["SDC"] / denom) if denom > 0 else None
    eligible_rate = (eligible / attempted) if attempted > 0 else None   # M9
    activation_rate = (activated / eligible) if eligible > 0 else None  # M9
    cons = (activated == sum(classes.values()) + sim_fail)
    result = {
        "runid": runid, "phase": args.phase, "seed_batches": seed,
        "clustered": clustered, "n_runs": len(runs),
        "attempted": attempted, "eligible": eligible,
        "activated": activated, "sim_fail": sim_fail,
        "funnel_missing_runs": funnel_missing,
        "classes": classes,
        "eligible_rate": None if eligible_rate is None else round(eligible_rate, 4),
        "activation_rate": None if activation_rate is None else round(activation_rate, 4),
        "sdc_rate": None if sdc_rate is None else round(sdc_rate, 4),
        "wilson": {"lo": round(lo, 4), "hi": round(hi, 4)},
        "stop_reason": stop_reason, "conservation": "OK" if cons else "VIOLATION",
        "runs": runs,
    }
```
返回行同步加 simfail：
```python
    return runid, ("  %s: phase=%s n_runs=%d activated=%d sdc=%d "
                   "simfail=%d stop=%s cons=%s" %
                   (runid, args.phase, len(runs), activated, classes["SDC"],
                    sim_fail, stop_reason, result["conservation"]))
```

- [ ] **Step 4: 运行确认通过**

```bash
python3 tools/draft/test_campaign_v2.py PolicyTests AccountingTests -v
```
预期：7 tests OK（Task 1 的 4 个 + Task 2 的 3 个）——证明无回归。

- [ ] **Step 5: 验证三件套 + 提交 + 中继**

```bash
python3 -m py_compile tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git diff --stat tools/lsu_campaign.py   # 必须为空
git add tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git commit -m "[LSU][P3] campaign v2 draft M7-M9+D1：事件账目两层率（eligible/activated 分层、sim_fail 单列剔除出 SDC 分母、零分母→None、funnel 缺失单列）+ T5/T6/D1"
```
中继同 Task 0 Step 3。

---
### Task 3: config_fp + verdict 落盘 + resume 前缀（M2-CONFIG_FP, M10, M11, D3）— 测试 T4/T9 + fp 隔离

**Files:**
- Modify: `tools/draft/lsu_campaign_v2.py`（新增 `import hashlib`；新增 `_FP_CACHE`/`_sha256_file`/`config_fp_for`/`_resume_prefix`/`_write_verdict`/`_prior_results_fp`；run_cell_adaptive 循环重构为 resume 型）
- Modify: `tools/draft/test_campaign_v2.py`（追加 ResumeTests）

**Interfaces:**
- Consumes: Task 1 常量与 `resolve_main_target`；Task 2 的累计语义（本任务闭包化为 `_acc`）；模块常量 G5/LSU_PROXY/L5/REPO/WL_BINARY/GOLDENS/COL_WORKLOAD。
- Produces:
  - `_sha256_file(path) -> str`（进程内缓存 `_FP_CACHE`，键=路径字符串）
  - `config_fp_for(cell, args) -> str`（六分量 sha256 前 16 hex：injector=G5、config=LSU_PROXY、workload=workloads/directed/<binary> 哈希（无匹配→workload 原串）、checkpoint=args.fs_checkpoint 绝对路径或 "SE"、oracle=GOLDENS[binary]（无→"none"）、classify=L5）
  - `_resume_prefix(cell_out, config_fp) -> (verdicts, next_seed)`（seed1..k 的 l5_verdict.json 存在、可解析、无 error、fp 一致→复用；首个失效即停；next_seed=k+1）
  - `_write_verdict(seed_dir, verdict, config_fp)`（旧 verdict fp 不一致→改名 `l5_verdict.fp_<old>.json` 后写新）
  - verdict JSON schema：`{**run_single_cell 返回键, "seed": int, "config_fp": str}`
  - cell_results.json 新增：`config_fp`、`prior_config_fp`（上一轮聚合结果的 fp；无→null）、`config_fp_isolated`（bool）；上一轮聚合 fp 不一致→改名 `cell_results.fp_<old>.json` 保留
  - run_cell_adaptive 新行为：先 resume 再补跑；`seed_batches`=next_seed-1

- [ ] **Step 1: 写失败测试（追加到 test_campaign_v2.py，`if __name__` 块之前）**

```python
class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.m = load_draft()
        # 封闭 fp：小文件替身（不哈希真实 1.2GB gem5.opt）
        self.tmp = tempfile.TemporaryDirectory()
        tp = Path(self.tmp.name)
        for name in ("g5", "proxy", "l5"):
            (tp / name).write_bytes(b"pad-" + name.encode())
        self.m.G5 = tp / "g5"
        self.m.LSU_PROXY = tp / "proxy"
        self.m.L5 = tp / "l5"
        self.m._FP_CACHE.clear()
        self.out = tp / "runs"
        self.calls = []
        self.m.run_single_cell = self._mock

    def tearDown(self):
        self.tmp.cleanup()

    def _mock(self, cell, args, seed, outdir):
        self.calls.append(seed)
        return {"outcome": "Masked", "activated": 5, "attempted": 6,
                "eligible": 5, "injected": 5}

    def _args(self, target):
        a = Args()
        a.phase = "trial"
        a.trial_target = target
        return a

    def test_T4_no_double_count_on_rerun(self):
        m = self.m
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)  # 6 runs
        self.assertEqual(len(self.calls), 6)
        self.calls.clear()
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)  # 全复用
        self.assertEqual(len(self.calls), 0)
        cell = self.out / "A01-F0-W3"
        self.assertEqual(len(list(cell.glob("seed*/l5_verdict.json"))), 6)
        r = json.loads((cell / "cell_results.json").read_text())
        self.assertEqual(r["n_runs"], 6)
        self.assertEqual(r["activated"], 30)

    def test_T9_resume_extends_without_seed_duplication(self):
        m = self.m
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)  # 6 seeds
        self.calls.clear()
        m.run_cell_adaptive(make_cell(), self._args(40), self.out)  # +2 seeds
        self.assertEqual(self.calls, [7, 8])
        seeds = sorted(json.loads(p.read_text())["seed"] for p in
                       (self.out / "A01-F0-W3").glob("seed*/l5_verdict.json"))
        self.assertEqual(seeds, [1, 2, 3, 4, 5, 6, 7, 8])

    def test_fp_mismatch_stratifies_not_mixes(self):
        m = self.m
        cell = self.out / "A01-F0-W3"
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)
        # 篡改 seed3 的 fp → 前缀止于 2 → 重跑 3..6
        v3 = cell / "seed3" / "l5_verdict.json"
        v = json.loads(v3.read_text())
        v["config_fp"] = "deadbeef00000000"
        v3.write_text(json.dumps(v))
        self.calls.clear()
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)
        self.assertEqual(self.calls, [3, 4, 5, 6])
        self.assertTrue((cell / "seed3" /
                         "l5_verdict.fp_deadbeef00000000.json").exists())
        cur = json.loads((cell / "cell_results.json").read_text())["config_fp"]
        for p in cell.glob("seed*/l5_verdict.json"):
            self.assertEqual(json.loads(p.read_text())["config_fp"], cur)
        # 篡改聚合结果 fp → 下轮分层标记 + 旧文件改名保留
        cr = cell / "cell_results.json"
        r = json.loads(cr.read_text())
        r["config_fp"] = "cafe000000000000"
        cr.write_text(json.dumps(r))
        m.run_cell_adaptive(make_cell(), self._args(30), self.out)
        r2 = json.loads(cr.read_text())
        self.assertTrue(r2["config_fp_isolated"])
        self.assertEqual(r2["prior_config_fp"], "cafe000000000000")
        self.assertTrue(
            (cell / "cell_results.fp_cafe000000000000.json").exists())
```

- [ ] **Step 2: 运行确认失败**

```bash
python3 tools/draft/test_campaign_v2.py ResumeTests -v
```
预期：AttributeError——模块无 `_FP_CACHE`/`config_fp_for`；或 run_cell_adaptive 重跑重复计数（T4 第二次 6 calls 而非 0）。

---
- [ ] **Step 3: 实现（tools/draft/lsu_campaign_v2.py）**

3a. 模块顶部 import 区加 `import hashlib`。

3b. 在 `resolve_main_target` 之后新增（M2-CONFIG_FP/M10/M11/D3）：
```python
_FP_CACHE = {}


def _sha256_file(path):
    """文件 sha256，进程内缓存（F-023 教训：单次运行内脚本不改动）。"""
    path = Path(path)
    key = str(path)
    if key not in _FP_CACHE:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _FP_CACHE[key] = h.hexdigest()
    return _FP_CACHE[key]


def config_fp_for(cell, args):
    """六项版本指纹（M2/M10，sha256[:16]）：注入器/配置/workload/
    checkpoint/oracle/分类规则。pilot 样本计入累计前必须一致——不一致
    → 分层隔离标记，绝不静默混合。"""
    workload = cell[COL_WORKLOAD].strip()
    binary = None
    for key, bin_name in WL_BINARY.items():
        if key in workload:
            binary = bin_name
            break
    wl_fp = (_sha256_file(REPO / "workloads" / "directed" / binary)
             if binary else workload)
    comp = [
        ("injector", _sha256_file(G5)),
        ("config", _sha256_file(LSU_PROXY)),
        ("workload", wl_fp),
        ("checkpoint", (str(Path(args.fs_checkpoint).resolve())
                        if getattr(args, "fs_checkpoint", None) else "SE")),
        ("oracle", GOLDENS.get(binary, "none") if binary else "none"),
        ("classify", _sha256_file(L5)),
    ]
    return hashlib.sha256("|".join("%s=%s" % kv for kv in comp)
                          .encode()).hexdigest()[:16]


def _resume_prefix(cell_out, config_fp):
    """M11 样本级 resume（对齐 unit_pilot._valid_resumed 前缀语义）：
    seed1..k 的 l5_verdict.json 存在、可解析、无 error、且 config_fp 一致
    → 复用；首个失效/不一致即停止（旧轮证据不复活、不静默混合）。
    返回 (verdicts, next_seed)，next_seed = k+1。"""
    resumed, s = [], 1
    while True:
        vj = cell_out / ("seed%d" % s) / "l5_verdict.json"
        if not vj.exists():
            break
        try:
            v = json.loads(vj.read_text())
        except json.JSONDecodeError:
            break
        if v.get("error") or v.get("config_fp") != config_fp:
            break
        resumed.append(v)
        s += 1
    return resumed, s


def _write_verdict(seed_dir, verdict, config_fp):
    """落盘 per-seed verdict（resume 依据）。旧轮 fp 不一致 → 改名保留
    （D3），不覆盖不删除。"""
    seed_dir.mkdir(parents=True, exist_ok=True)
    vj = seed_dir / "l5_verdict.json"
    if vj.exists():
        try:
            old_fp = json.loads(vj.read_text()).get("config_fp")
        except json.JSONDecodeError:
            old_fp = "unreadable"
        if old_fp != config_fp:
            vj.rename(seed_dir / ("l5_verdict.fp_%s.json" % old_fp))
    vj.write_text(json.dumps(verdict, indent=1))


def _prior_results_fp(cell_out):
    """上一轮聚合结果的 fp（无文件→None；不可解析→"unreadable"）。"""
    cr = cell_out / "cell_results.json"
    if not cr.exists():
        return None
    try:
        return json.loads(cr.read_text()).get("config_fp")
    except json.JSONDecodeError:
        return "unreadable"
```

3c. run_cell_adaptive 主体重构——计数器初始化段替换为：
```python
    classes = {k: 0 for k in ("Masked", "Detected/Contained", "SDC",
                              "Crash", "Timeout")}
    runs, attempted, eligible = [], 0, 0
    activated = sim_fail = funnel_missing = 0
    cell_out = outroot / runid
    fp = config_fp_for(cell, args)                     # M2/M10
    prior_fp = _prior_results_fp(cell_out)             # M10 分层隔离
    resumed, next_seed = _resume_prefix(cell_out, fp)  # M11
```
（注：原代码中 `cell_out = outroot / runid` 若在别处已定义则合并到此。）

3d. Task 2 的循环体累计段闭包化——在计数器之后定义：
```python
    def _acc(r):
        nonlocal attempted, eligible, activated, sim_fail, funnel_missing
        act = int(r.get("activated", 0) or 0)
        runs.append({"seed": r.get("seed"),
                     "cluster_id": "%s#%s" % (runid, r.get("seed")),
                     "activated": act,
                     "outcome": r.get("outcome", "Unclassified"),
                     "crash_kind": r.get("crash_kind"),
                     "attempted": r.get("attempted"),
                     "eligible": r.get("eligible")})
        if r.get("attempted") is None or r.get("eligible") is None:
            funnel_missing += 1          # D1: legacy/FS/Timeout 无 funnel 行
        else:
            attempted += int(r["attempted"])
            eligible += int(r["eligible"])
        activated += act
        oc = r.get("outcome")
        if oc == "Crash" and r.get("crash_kind") == "simulator_assert":
            sim_fail += act              # M7: post_activation_simulator_failure
        elif oc in classes:
            classes[oc] += act

    for v in resumed:
        _acc(v)
```

3e. 主循环替换（原 `seed = 0` 起的 while 结构）：
```python
    stop_reason = None
    while True:
        if activated >= target:
            stop_reason = "%s-target-met" % args.phase
            break
        if next_seed > args.max_seeds_per_cell:
            stop_reason = "seed-cap(%d)" % args.max_seeds_per_cell
            break
        r = run_single_cell(cell, args, next_seed,
                            cell_out / ("seed%d" % next_seed))
        r = dict(r)
        r["seed"] = next_seed
        r["config_fp"] = fp
        _write_verdict(cell_out / ("seed%d" % next_seed), r, fp)
        _acc(r)
        next_seed += 1
```
result 中 `"seed_batches": seed` 改为 `"seed_batches": next_seed - 1`。
（M6 已删除 Wilson 停止块，此处不再出现。）

3f. cell_results.json 写盘段前追加分层隔离处理，result 增三键：
```python
    if prior_fp not in (None, fp, "unreadable"):
        # D3: 旧轮聚合结果改名保留，不静默混合
        (cell_out / "cell_results.json").rename(
            cell_out / ("cell_results.fp_%s.json" % prior_fp))
    result["config_fp"] = fp
    result["prior_config_fp"] = prior_fp
    result["config_fp_isolated"] = (prior_fp not in (None, fp))
```

- [ ] **Step 4: 运行确认通过**

```bash
python3 tools/draft/test_campaign_v2.py PolicyTests AccountingTests ResumeTests -v
```
预期：10 tests OK（Task 1 的 4 + Task 2 的 3 + Task 3 的 3）——无回归。

- [ ] **Step 5: 验证三件套 + 提交 + 中继**

```bash
python3 -m py_compile tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git diff --stat tools/lsu_campaign.py   # 必须为空
git add tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git commit -m "[LSU][P3] campaign v2 draft M10/M11+D3：config_fp 六项版本指纹 + per-seed verdict 落盘 + 前缀 resume（fp 不一致分层隔离改名保留）+ T4/T9/fp 隔离"
```
中继同 Task 0 Step 3。

---
### Task 4: 回归门（T7/T10 + 全套 + 冒烟比对 + 收口）

**Files:**
- Modify: `tools/draft/test_campaign_v2.py`（追加 RegressionTests）
- Modify: `docs/superpowers/plans/2026-10-08-lsu-campaign-v2-draft-implementation.md`（勾选全部 checkbox）
- Modify: `docs/gem5-fi/lsu/progress.md`（draft 完成记录 + 唯一下一动作刷新）
- Modify: `docs/gem5-fi/lsu/findings.md`（F 编号新行：M12 发现——naive 文件复制改变 `__file__` 相对路径语义；先 `git fetch origin` 再取 max+1 分配）

**Interfaces:**
- Consumes: Task 1-3 全部产物；正式文件 `tools/lsu_campaign.py`（只读对比，绝不修改）；`tools/lsu_unit_pilot.py`（T10 swap 导入，只读）。
- Produces: 完整测试套件（T1-T10 + D1 + fp 隔离，共 13 test）全 PASS；draft 与正式文件 dry-run 输出逐字节一致证明；F 编号新行；plan 全勾选；progress 收口。

- [ ] **Step 1: 写测试（追加到 test_campaign_v2.py，`if __name__` 块之前）**

```python
class RegressionTests(unittest.TestCase):
    def _run_cell(self, m, runid, freq, results, trial_target):
        seq = list(results)

        def mock(cell, args, seed, outdir):
            return seq[min(seed - 1, len(seq) - 1)]

        m.run_single_cell = mock
        a = Args()
        a.phase = "trial"
        a.trial_target = trial_target
        a.max_seeds_per_cell = 100
        with tempfile.TemporaryDirectory() as td:
            m.run_cell_adaptive(make_cell(runid=runid, freq=freq), a, Path(td))
            return json.loads((Path(td) / runid / "cell_results.json")
                              .read_text())

    def test_T7_clustered_wilson_per_run(self):
        m = load_draft()
        # F2（clustered）：单 run SDC → per-run k=1, n=1
        r = self._run_cell(m, "S02-F2-W0", "F2", [
            {"outcome": "SDC", "activated": 3, "attempted": 3,
             "eligible": 3, "injected": 3}], trial_target=3)
        lo, hi, _p = m.wilson_ci(1, 1)
        self.assertEqual(r["wilson"], {"lo": round(lo, 4), "hi": round(hi, 4)})
        # F0（非 cluster）：per-activated k=2, n=5
        r = self._run_cell(m, "A02-F0-W0", "F0", [
            {"outcome": "SDC", "activated": 2, "attempted": 2,
             "eligible": 2, "injected": 2},
            {"outcome": "Masked", "activated": 3, "attempted": 3,
             "eligible": 3, "injected": 3}], trial_target=5)
        lo, hi, _p = m.wilson_ci(2, 5)
        self.assertEqual(r["wilson"], {"lo": round(lo, 4), "hi": round(hi, 4)})

    def test_T10_constant_interface_zero_regression(self):
        m = load_draft()
        spec = importlib.util.spec_from_file_location(
            "lc_formal",
            Path(__file__).resolve().parent.parent / "lsu_campaign.py")
        f = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f)
        for name in ("WL_BINARY", "GOLDENS", "WL_BLOCKED", "MODEL_FLAGS",
                     "FAMILY_SEED", "COL_RUNID", "COL_MODEL", "COL_UNIT",
                     "COL_FREQ", "COL_WORKLOAD", "G5", "LSU_PROXY", "L5",
                     "REPO"):
            self.assertEqual(getattr(m, name, "<missing>"),
                             getattr(f, name, "<missing>"), name)
        # swap 模拟：unit_pilot 的 `import lsu_campaign as LC` 取到 draft
        tools_dir = str(Path(__file__).resolve().parent.parent)
        sys.path.insert(0, tools_dir)
        sys.modules["lsu_campaign"] = m
        try:
            import lsu_unit_pilot as UP
            self.assertIs(UP.LC, m)
            self.assertEqual(UP.SAMPLES_TARGET, 30)
            self.assertEqual(UP.ATTEMPTED_CAP, 300)
        finally:
            sys.modules.pop("lsu_campaign", None)
            sys.path.remove(tools_dir)
```

- [ ] **Step 2: 运行全套确认通过**

```bash
python3 tools/draft/test_campaign_v2.py -v
```
预期：13 tests OK（4+3+3+3）。若 T10 的 FAMILY_SEED 等常量名在任一文件缺失，两侧 getattr 默认值相等即通过；若一侧独有则 FAIL——此时以正式文件为准核对拼写，修正测试名单（不改正式文件）。

- [ ] **Step 3: dry-run 冒烟比对（draft vs 正式，只读，不跑 gem5）**

```bash
python3 tools/lsu_campaign.py --matrix runs/lsu/07-expanded-matrix-backfilled.csv --dry-run > /tmp/dry_formal.txt 2>&1
python3 tools/draft/lsu_campaign_v2.py --matrix runs/lsu/07-expanded-matrix-backfilled.csv --dry-run > /tmp/dry_draft.txt 2>&1
diff /tmp/dry_formal.txt /tmp/dry_draft.txt && echo "DRY-RUN IDENTICAL"
```
预期：`DRY-RUN IDENTICAL`（M1-M11 不触碰 resolve_cell/加载路径；差异即回归，必须归零）。注意正式文件作为 `__main__` 运行 dry-run 是只读操作（加载矩阵→解析→打印→return），不影响波次 5 的 import。

- [ ] **Step 4: 验证三件套 + 提交**

```bash
python3 -m py_compile tools/draft/lsu_campaign_v2.py tools/draft/test_campaign_v2.py
git diff --stat tools/lsu_campaign.py   # 必须为空
git add tools/draft/test_campaign_v2.py
git commit -m "[LSU][P3] campaign v2 draft T7/T10 回归门：per-run Wilson 语义 + 常量接口零变更（含 unit_pilot swap 模拟 30/300）+ 全套 13 test PASS"
```

- [ ] **Step 5: findings.md F 编号新行（先 fetch origin 防撞号）**

```bash
git fetch origin 2>/dev/null; grep -oE '^- F-[0-9]+' docs/gem5-fi/lsu/findings.md | sort -t- -k2 -n | tail -1
```
取 max+1（预期 F-043，若 origin 已占用更高则顺延）。新行内容（M12 发现）：
```
- F-0XX（2026-10-08 HH:MM，集群）draft 副本 REPO 陷阱：`lsu_campaign_v2.py` 若原样保留 `REPO = Path(__file__).resolve().parent.parent`，在 tools/draft/ 深度下解析到 tools/（G5/LSU_PROXY/L5/workloads 全部失效）——任何"复制脚本到子目录做隔离开发"的操作都会静默改变 `__file__` 相对路径语义。修复：深度无关向上查找标记目录（configs/se 存在），T10 的 REPO 相等断言守护未来复制回 tools/ 时不回退。附带：磁盘配额事件（10-08 晚，用户配额 ~1T 触顶，根因 sdcshield-sve-repro 913G）→ 删除冗余传输快照 gem5-fi-wx-paper.tar.gz（4.8G，Sep 30 建仓种子，活性 repo 为超集且 git 同步、Windows 源在），写入恢复。
```

- [ ] **Step 6: plan 全勾选 + progress 收口 + 提交 + 中继**

plan 文件所有 `- [ ]` 改 `- [x]`（Task 0 Step 1 已是 [x]）。
progress.md：Session 002 条目追加 ⑩（quota 事件 + 应对）；唯一下一动作刷新为：①push、②keeper 监控（1830226 + crons）、③DR-003-A 待命、④draft 已完成——待六条安全边界满足后应用（应用流程独立执行，不在本计划）。

```bash
git add docs/superpowers/plans/2026-10-08-lsu-campaign-v2-draft-implementation.md docs/gem5-fi/lsu/progress.md docs/gem5-fi/lsu/findings.md
git commit -m "[LSU][P3] campaign v2 draft 收口：plan 全勾选 + F-0XX M12 发现 + quota 事件记录 + progress 唯一下一动作刷新"
```
中继同 Task 0 Step 3。

---

## Self-Review 记录（写计划时已完成）

1. **Spec 覆盖**：M1→Task1-3b、M2→Task1-3c+Task3-3b、M3→Task1-3d、M4→Task1-3d、M5→Task1-3e、M6→Task1-3f、M7→Task2-3b、M8→Task2-3c、M9→Task2-3c、M10→Task3-3b/3f、M11→Task3-3b/3e；T1-T10 全部有测试（T1/T2/T3/T8→PolicyTests、T5/T6→AccountingTests、T4/T9→ResumeTests、T7/T10→RegressionTests）+ 计划外补充 D1/fp 隔离两测。无遗漏。
2. **占位符扫描**：无 TBD/TODO/"稍后实现"；所有代码块完整可执行。
3. **类型一致性**：`resolve_main_target(runid, args)->int`、`_sha256_file(path)->str`、`config_fp_for(cell, args)->str`、`_resume_prefix(cell_out, fp)->(list,int)`、`_write_verdict(seed_dir, verdict, fp)`、`_prior_results_fp(cell_out)` 各任务引用一致；result 键名（sim_fail/funnel_missing_runs/eligible_rate/activation_rate/sdc_rate/config_fp/prior_config_fp/config_fp_isolated）Task 2/3/4 一致；verdict 键 `seed`/`config_fp` 读写一致。

## 实施期计划修正（2026-10-08，实施前核实时发现）

1. **矩阵路径**：计划初稿写 `docs/gem5-fi/lsu/07-expanded-matrix.csv`——实际不存在。真实矩阵为 `runs/lsu/07-expanded-matrix-backfilled.csv`（675 行；与 `artifacts/lsu-trial/` 副本 diff 相同；backfill_expanded_matrix.py 的输出即 campaign 实际使用版）。测试 MATRIX 常量与 Task 4 冒烟命令同步改用该路径。
2. **wilson 依赖**：draft 模块顶部 `from wilson import wilson_ci`（tools/wilson.py）——importlib 加载前必须 `sys.path.insert(0, str(TOOLS))`，否则 ModuleNotFoundError。已加入 load_draft() helper。
3. **M12 实证**：未修复的 draft 加载后 `REPO` 实测解析为 `<repo>/tools`（错误）——M12 修复的必要性已用真实命令验证（python3 importlib 探针）。

## 执行模式说明

本会话为远端单通道（Bash→login01 集群），subagent 无法共享该通道的认证与工作目录上下文，故采用 executing-plans 内联执行（CLAUDE.md 允许两种模式之一）。每任务按 TDD 步骤推进并即时勾选。
