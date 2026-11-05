# FSU 测试 skip 分类（以当前工作树实测为准）

日期：2026-11-05。分支 `fsu`。本文件只记录**真实运行**过的 pytest 输出；
未运行 scons / gem5，未 commit / push。

> **2026-11-05 后续更新（主 agent，修复后重跑）**：
> FQ08/FP08 的 `woken`、rounding 原因分区、fail-closed 已实现并有真实
> gem5 证据（见 `FQ08-FP08-GATE-EVIDENCE.md`）。FSU 子集重跑：
> **588 passed, 45 skipped, 0 failed（240.66s）**，EXIT=0。
> skip 分类：environment=2（1 个 generation/free-reuse BLOCKED +
> 1 个 identity N/A）、other=37（suite seed 参数化筛选）、
> unimplemented=6（legacy F0 无冻结 seed_plan）。
> 核心门禁 BLOCKED 只剩 `test_generation_reuse_evidence` 1 项；
> 该结论不把 588 passed 当作已验证能力。

## 0. 结论先行

1. **基线报告的 “543 passed / 43 skipped” 是全量 `pytest tests/` 的数字，
   当前不可复现**。全量实际为（排除会中断 collection 的单个文件，见 §1）：
   **748 passed, 52 skipped, 20 failed, 3 errors, 1 warning（375.59s）**。
   原因是当前收集到 823 个测试，且 `/home/sdc/gem5-fi-ding` 证据根缺少 LSU
   资产，另有 3 项 swap 环境门禁失败。**不能用 543/43 代表全量现状。**
   但 **43 这个 skip 数与 FSU 子集的既有 skip 数完全吻合**（37 个
   “not a suite seed” + 6 个 “legacy F0 suite has no frozen seed_plan”）；
   FSU 子集实测为 **574 passed, 49 skipped**（其中 43 个既有 + 6 个本轮
   BLOCKED），EXIT=0；该次运行早于最后新增的 1 个同源 placeholder skip，
   随后两个新文件单独重跑为 **22 passed, 7 skipped**，故当前子集按算术为
   574 passed / 50 skipped。因此原基线很可能是 FSU 子集口径（543 passed 是
   当时的用例数，现存量已增长到 552；再加本轮 22 个新测试 = 574），不是全量
   口径。两个口径必须分开报告，不能混用。
2. 直接运行 `python3 -m pytest tests/` **无法完成 collection**：
   `tests/test_lsu_r6_reconcile_realroot.py` 在模块级发现证据缺失后
   `sys.exit(0)`（第 74 行），pytest 报 `INTERNALERROR ... SystemExit: 0`，
   `no tests ran`。这本身就是测试入口缺陷（诚实跳过写成了进程退出）。
3. 本轮新增的 7 个 skip 中，6 个是**核心门禁未闭合**（FQ08-c 真实 fire /
   generation、FP08 原因分区、FP08 fail-closed；另有一个同源的
   `woken` 可观测性占位），1 个是 identity 真实不可自然触发（N/A）。核心项
   已在本文件标 BLOCKED。**总 passed 数不能证明这些能力**。
4. 52 个既有 skip 中：43 个来自 `test_fsu_seed_plan_schema.py`（其中 37 个
   是参数化筛选，6 个是 legacy F0 无冻结 seed_plan），9 个来自
   `test_lsu_prop_doc_audit.py`（证据树缺失）。**没有 FSU 核心门禁被静默
   skip 后仍被当作已验证**；FSU 核心门禁的缺口由本轮新增测试显式标出。

## 1. 实际运行方式与计数

仓库根**没有** `pytest.ini` / `pyproject.toml` / `setup.cfg` 的 pytest 配置
（`CHAOS/gem5/pyproject.toml` 是 vendored 上游 gem5 的，不作用于本仓库
`tests/`）；`tests/conftest.py` 只提供脚本式测试的 `check` fixture 和
claim-concurrency 环境门禁。现有命令来自文档（全量 `pytest tests/`、
FSU 子集 `pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py ...`）。

> 运行快照：全量运行于 2026-11-05 09:09–09:15，FSU 子集运行于 09:19–09:23。
> 审计期间另一 subagent 正在改 CHAOSFPU（FP05 burst，mtime 09:20）并新增
> `tests/test_chaos_fsu_burst_cpp.py`。全量快照早于这些改动；FSU 子集虽在改动
> 窗口内启动，但其收集未包含该新文件（574 = 552 既有 + 22 本轮）。上述数字
> 只对应这一快照，后续并发改动需重跑后再引用。

| 命令 | 真实结果 |
|---|---|
| `python3 -m pytest tests/ -q -rs` | `INTERNALERROR`（`SystemExit: 0`），`no tests ran`，EXIT=3 |
| `python3 -m pytest tests/ -q -rs --ignore=tests/test_lsu_r6_reconcile_realroot.py` | **20 failed, 748 passed, 52 skipped, 1 warning, 3 errors in 375.59s**，EXIT=1 |
| `python3 -m pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py tests/test_chaos_vec_stuck_cpp.py tests/test_chaos_physreg_generation_cpp.py tests/test_chaos_iq_lifecycle_cpp.py -q -rs` | **574 passed, 49 skipped, EXIT=0（245.91s）**；其中 43 个既有 skip + 6 个本轮新增 BLOCKED（该次运行后新增第 7 个同源 skip；两文件复跑为 22 passed / 7 skipped） |
| `python3 -m pytest tests/test_fsu_seed_plan_schema.py -v -rs` | 42 passed，43 skipped |
| `python3 -m pytest tests/test_lsu_prop_doc_audit.py -v -rs` | 全部 real-doc 项 9 skipped（原因均为 `real R6 docs/evidence tree not present`） |
| `python3 -m pytest tests/test_chaos_fsu_fq08c_gate_audit.py -q -rs` | 8 passed，**4 skipped（1 个 placeholder + 3 个 BLOCKED）** |
| `python3 -m pytest tests/test_chaos_fsu_fp08_reason_audit.py -q -rs` | 14 passed，**3 skipped（placeholder/BLOCKED）** |

分类工具（本轮新增）：`tools/fsu_skip_classify.py`。它读取 pytest JUnit
报告（或自行调用 pytest），输出
`nodeid | reason | category | core gate? | status`，并把任何被 skip 的核心门禁
标成 `BLOCKED`（不会把 skip 变成 pass）。真实运行示例：

```text
$ python3 tools/fsu_skip_classify.py --pytest-args \
    "tests/test_chaos_fsu_fq08c_gate_audit.py tests/test_chaos_fsu_fp08_reason_audit.py"
totals: 22 passed, 7 skipped, 0 failed, 0 errors
core gates BLOCKED: 6
by category: environment=3, unimplemented=4

$ python3 tools/fsu_skip_classify.py --junit /tmp/seedplan.xml
totals: 15 passed, 43 skipped, 0 failed, 0 errors
core gates BLOCKED: 0
by category: other=37, unimplemented=6
```

> 说明：第 1–2 行是全量快照；其余各行是分类/子集所需的定点重跑。新增两个
> 文件的 22 passed + 7 skipped 不计入 748/52 全量快照（快照在文件创建前收集），
> 但**计入了 574/49 的 FSU 子集**（该次运行只有 6 个新 skip）。若按最终文件
> 相加，全量口径对应值为 770 passed / 59 skipped（其余 20 failed、3 errors
> 不变），但这不是单条命令的输出，故不冒充。

## 2. 既有 skip 逐条分类（52 项）

### 2.1 `tests/test_fsu_seed_plan_schema.py`（43 项）

参数化测试 `test_real_suite_seed_binding[runs/fsu/FSU-.../seedN]`，两段原因：

| 分类 | 数量 | nodeid（逐条） | 原文 skip reason | 影响 | 核心门禁？ |
|---|---:|---|---|---|---|
| 其他：测试筛选（非 suite seed，设计如此） | 37 | `tests/test_fsu_seed_plan_schema.py::test_real_suite_seed_binding[runs/fsu/FSU-FP04-F0-W1/seed1]`、`…[FSU-FP04-F0-W1/seed2]`、`…[seed3]`、`…[FSU-FP04-F0-W3/seed1..3]`、`…[FSU-FP04-F0-W4/seed1..3]`、`…[FSU-FP04-F1-W4/seed1..3]`、`…[FSU-FP04-F2-W4/seed1..3]`、`…[FSU-FP04-F3-W4/seed1..3]`、`…[FSU-FP06-F5-W1/seed1..3]`、`…[FSU-FP06-F5-W3/seed1..3]`、`…[FSU-FP06-F5-W4/seed1..3]`、`…[FSU-FR01-F0-W1/seed1]`、`…[FSU-FR03-F5-W3/seed1..3]`、`…[FSU-FR07-F0-W1/seed1..3]`、`…[FSU-FR07-F0-W3/seed1..3]` | `not a suite seed` | 这些目录没有 `suite_manifest.json`，不属于 suite-seed 绑定审计范围；组件 seed 由其他测试覆盖。 | 否 |
| 未实现能力：legacy F0 无冻结 seed_plan | 6 | `…[runs/fsu/FSU-FP04-F0-W5/seed1]`、`…[seed2]`、`…[seed3]`、`…[runs/fsu/FSU-FP04-F0-W6/seed1]`、`…[seed2]`、`…[seed3]` | `legacy F0 suite has no frozen seed_plan` | 这 6 个真实 seed 的 binding 无法按冻结 plan 复算；属于“旧 suite 未冻结”的能力缺口，不是证据伪造。 | 否（schema 审计，非能力认证） |

### 2.2 `tests/test_lsu_prop_doc_audit.py`（9 项）

统一 `skipif`：`not os.path.isdir(DOCS_DIR) or not os.path.isfile(EVIDENCE_JSON)`，
原因原文 **`real R6 docs/evidence tree not present`**。

| nodeid | 分类 | 影响 | 核心门禁？ |
|---|---|---|---|
| `::test_real_t03_f5_w4_seed1_is_pass` | 环境依赖缺失 | 无法复核真实文档 | 否（LSU） |
| `::test_real_t01_f1_w4_seed2_is_pass_with_two_calibers` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_w1_docs_are_two_axis_not_single_pass` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_w1_identity_mismatch_and_w4_match` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_t01_f0_w4_seed2_arrow_chain_with_parens` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_t04_f0_w4_seeds_use_full_ch4_ancestry` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_t10_f1_w1_seed2_full_chain` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_t02_f2_w4_seed2_regrade_containment` | 环境依赖缺失 | 同上 | 否 |
| `::test_real_full_audit_counts` | 环境依赖缺失 | 同上 | 否 |

缺失的路径由测试常量决定：`DOCS_DIR` 默认
`/home/sdc/gem5-fi-ding/runs/lsu/...`，`EVIDENCE_JSON` 默认
`/home/sdc/gem5-fi-ding/runs/lsu/R6-AUTHORITATIVE-EVIDENCE.json`；本机
`/home/sdc/gem5-fi-ding` 存在，但缺少这些子资产/文件。

### 2.3 收集阶段被中断的 skip（不计入 52）

| nodeid | 原因原文 | 分类 | 影响 | 核心门禁？ |
|---|---|---|---|---|
| `tests/test_lsu_r6_reconcile_realroot.py`（模块级） | `SKIPPED [L34-reconcile] 真证据根缺 pilot 证据：/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2 不存在（设 LSU_CHAIN_EVIDENCE_ROOT 指向含 runs/lsu/ 的真根后重跑）` | 环境依赖缺失 + 测试入口缺陷 | 该文件全部测试未收集，且 `sys.exit(0)` 中断整个 suite collection | 否（LSU）；但**必须修**，否则 `pytest tests/` 永远不能全量运行 |

### 2.4 本轮新增测试的 skip（7 项；表中 6 项 + 同源 1 项）

| nodeid | 原文 skip reason（首句） | 分类 | 影响 | 核心门禁？ |
|---|---|---|---|---|
| `tests/test_chaos_fsu_fq08c_gate_audit.py::test_positive_fire_evidence` | `BLOCKED: no real gem5 log shows FIRED delayed wake (delayed_fired>=1)` | 环境依赖缺失（真实 gate 未跑） + 未实现可观测能力（`woken`） | FQ08-c 未 squash 正例、真实 activated 无法证明 | **是 → BLOCKED** |
| `tests/test_chaos_fsu_fq08c_gate_audit.py::test_generation_reuse_evidence` | `BLOCKED: no real gem5 log shows IGNORED reason=ignore_generation` | 环境依赖缺失（真实 gate 未跑） | free/realloc 后旧事件安全忽略未在 gem5 观测 | **是 → BLOCKED** |
| `tests/test_chaos_fsu_fq08c_gate_audit.py::test_identity_mismatch_evidence` | `BLOCKED: no real gem5 log shows IGNORED reason=ignore_identity` | 其他：不可自然触发（seqNum/tid 不可变） | 该路径只能 host 证明；不得伪造真实证据 | 否（design-level N/A） |
| `tests/test_chaos_fsu_fp08_reason_audit.py::test_per_reason_counters_are_not_implemented_yet` | `to be implemented (placeholder): rounding attempts rejected before apply have no per-reason counters/log lines` | 未实现能力 | 356 个 rejected rounding 事件无法分类 | **是 → BLOCKED** |
| `tests/test_chaos_fsu_fp08_reason_audit.py::test_real_rounding_gate_reason_partition` | `to be implemented (placeholder): the 356 rejected rounding attempts have no reason breakdown in the real log` | 未实现能力 + 环境证据不足 | attempted/applied 守恒只能验到 `>=` | **是 → BLOCKED** |
| `tests/test_chaos_fsu_fp08_reason_audit.py::test_unguarded_combinations_fail_closed` | `to be implemented (placeholder): no constructor guard rejects these FP08 combinations before the run: ...` | 未实现能力 | 7 个不兼容组合会静默 inert，不会在运行前 fail-closed | **是 → BLOCKED** |

另有 1 个非 skip 的静态缺口测试
`test_chaos_fsu_fq08c_gate_audit.py::test_fire_target_state_count_is_not_observable_yet`
同样以 `to be implemented (placeholder)` skip；它与 positive fire 门禁同源，
不计入上表 6 项以免重复计数。

## 3. 非 skip 的失败/错误（必须与 skip 分开看）

20 failed 与 3 errors **全部**来自 LSU 轨道/环境，不属于 FSU 能力结论；但它们
使“全量 pytest 绿”不成立，不能把 748 passed 当作整体验收。

| 类别 | 数量 | 明细 | 证据 |
|---|---:|---|---|
| 环境：swap < 4 GiB 的 autouse 前置 | 3 errors | `test_claim_concurrency.py::test_c_slot_race`、`::test_d_run_concurrency_cap`、`::test_e_heartbeat` | `ENV-FAIL（拒绝静默跳过：环境不可验收=失败）: env_swap_free_ge_4gib(0.00 GiB)` |
| 环境：ding 证据根缺文件 | 14 failed | `test_lsu_r6a4_repeat_census.py` 2 项、`test_lsu_r6a4_unit_close.py` 2 项、`test_lsu_s_prop_docs.py::test_s_evidence_sha256_matches` 1 项、`test_lsu_s_trigger_census.py` 6 项、`test_lsu_s_unit_blocked.py` 1 项、`test_lsu_results_layout.py::test_referenced_evidence_paths_exist` 1 项 | 多为 `FileNotFoundError: /home/sdc/gem5-fi-ding/runs/lsu/...`；`test_referenced_evidence_paths_exist` 还发现当前仓库文档引用了另一 worktree 的构建路径 |
| 证据/文档漂移（非 FSU） | 6 failed | `test_lsu_s_prop_docs.py` 的 `test_s_docs_total_39`（实际 65 ≠ 39）、`test_s_each_runid_has_seed_coverage`、`test_s_event_rows_come_from_raw_stream`、`test_s_parent_ancestry_in_raw_stream`、`test_s_verdict_matches_chain_report`、`test_s_injection_values_belong_to_own_seed` | 见 `/tmp/pytest_full.log` 对应段落 |

> 注：上表 “14 + 6 = 20”，两者都不是 FSU 结论。

## 4. 分类汇总

| 分类 | 数量（既有 52） | 数量（本轮新增） |
|---|---:|---:|
| 环境依赖缺失 | 10（9 个 LSU real-doc + 1 个 collection skip） | 2 |
| 未实现能力 | 6（legacy F0 seed_plan） | 4 |
| 手动集成测试 | 0 | 0 |
| 其他（参数化筛选 / 不可自然触发） | 37 | 1 |
| 合计 | 52（另有 1 个 collection 中断） | 7（6 计入 + 1 同源） |

## 5. 核心门禁状态（不得用 passed 总数替代）

| 门禁 | 状态 | 证据/阻塞 |
|---|---|---|
| FQ08-c 真实 squash 安全忽略 | PASS（既有真实日志） | `runs/fsu-gates/FQ08-C-GATE/iq_injections.log` |
| FQ08-c 真实 Fire / activated 目标状态 | **BLOCKED** | 无 fire 日志；且 `woken` 未记录；见 `FQ08-FP08-GATE-AUDIT.md` §1.3/§3.1 |
| FQ08-c 真实 generation free/realloc | **BLOCKED** | 无 `ignore_generation` 日志；§3.2 |
| FQ08-c identity 负例 | N/A（host 已证明，真实不可自然触发） | §3.3 |
| FP08 fpsr 守恒 | PASS（代理口径） | 174018 == 174018 == 174018 |
| FP08 rounding attempted/applied | PARTIAL PASS | 357 ≥ 1；356 rejected 无原因 |
| FP08 rounding 原因级守恒 | **BLOCKED** | 无 per-reason 计数 |
| FP08 7 个组合 fail-closed | **BLOCKED** | 构造期无 panic |
| FP08 代理分类不自动升级 | PASS | `suppress` 无层、FP08 仍 PARTIAL/unapproved proxy |

## 6. 原始日志位置

- 全量：`/tmp/pytest_full.log`（本轮生成，未入库）
- FSU 定点：`/tmp/pytest_fsu.log`（本轮生成，未入库）
- seed_plan 逐条 skip：`/tmp/seedplan.xml`（junit，本轮生成，未入库）
- 既有 gem5 gate：`runs/fsu-gates/FQ08-B-POS*`、`runs/fsu-gates/FQ08-C-GATE`、
  `runs/fsu-gates/FP08-FPSR-GATE`、`runs/fsu-gates/FP08-GATE/...`。
