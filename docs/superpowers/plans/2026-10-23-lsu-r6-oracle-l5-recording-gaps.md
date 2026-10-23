# 2026-10-23 — L18-v2 R6-ORACLE：L5 结局记录缺口修复（G1–G7）

> 车道：L18-v2（code）。worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-oracle`，
> 分支 `r6-oracle`，base `66ab98a2`。
> 拥有文件：`tools/lsu_l5_classify.py`、`tools/lsu_obs_core.py`、
> `tools/lsu_l3_propagation.py`、`tools/lsu_handoff.py` + 其 `tests/test_lsu_*.py`。
> **不编辑**：`chain_check.py` / `ready_contract.py` / `campaign.py` / 任何 C++。

## 规格依据（真实读到的原文）

- `docs/gem5-fi/lsu/总方针.md:33`：主结局必须且只能是 Masked、Detected-contained、
  Data Corruption、Crash、Timeout 中的一项；`:32` 首检来源必须且只能是
  Hardware RAS、OS、Application、None 中的一项。
- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md:229`：
  `detection_layer / contained` … 最终判定事件**必需**。
- 同文件 `:136`：L5 需记录 Masked / Detected-contained / Detected-uncontained /
  Data Corruption / Crash / Timeout / SDC / Simulator failure。
- `docs/gem5-fi/lsu/mdspec/pilot_report.md:22`：`tlb_fault` 携带
  `detection_layer=Hardware`、`contained=`（空）→ 真实存在该字段族。
- C++ 侧已存在字段注册表（只读，不改）：
  `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh:166-186`
  的 `PROP_EVT_FIELDS` 含 `fault_id`/`event_id`/`parent_event_id`/`commit_seq`/`pc`/
  `detection_layer`/`contained`/`outcome`/`oracle_diff`/`evidence_status`（发射器已经
  有这些列，但 `chain_end` 恒写 `detection_layer="None"`, `contained="0"`,
  `seen_errant` 硬编码 false — 见 `.cc:110-124`）。

## 基线（真实运行，2026-10-23）

```
[lsu_test_runner] suites=52 ENV=5 FAIL=13 PASS=33 SKIP=1
```
FAIL 名单（全在我未拥有的文件）：`pytest::collect`、`test_lsu_campaign_propagation`、
`hook_a07/c11/c12/c14/c15/cpf/l04/o0x/p06/s10/sq`。
我拥有的：`test_lsu_obs_core.py` PASS=FAILURES:[无]；`test_lsu_l3_propagation.py` ENV
（dry-run 段缺 gem5 二进制 → FileNotFoundError，诚实 ENV，非 FAIL）。
**零 NEW FAIL 判据 = FAIL 仍为 13 且不含我的套件。**

---

## Task 1 — [G1] Crash 记录检测点 + detection_layer + outcome + 污染链关联

- [ ] RED：`tests/test_lsu_l5_classify.py` 新增 `g1_*` 断言（当前 `classify()` 输出无
      `detection_layer`/`detection_point`/`fault_linkage`/`taint_chain` → FAIL）
- [ ] GREEN：`classify()` 增加
      - `detection_layer` ∈ {Hardware RAS, OS, Application, None}（simulator_assert→None，
        guest trap→OS，并带 note 说明 detector 未接线）
      - `detection_point` = {kind, tick, pc, detail}（从 stderr/stdout 的
        `exiting @ tick N`、Assertion/panic 文本、arch trap 标记提取）
      - `fault_linkage` = {injected_tick, injected_site, fault_index}（注入日志首个 Site 行）
      - `taint_chain` = 可选 `--prop-trace` 时用 `lsu_l3_propagation.parse_prop_trace`
        取 taint 终点/ptag；未给则 `{"status":"not_provided"}`（n/a，不静默）
- [ ] 验证：`python3 tests/test_lsu_l5_classify.py` + 回归 `tests/test_lsu_obs_core.py`
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G1 Crash 记录检测点/detection_layer/污染链关联`

## Task 2 — [G2] Masked 记录 containment layer + reason

- [ ] RED：`tests/test_lsu_obs_core.py` 新增 `g2_*`（`build_l4` 无 containment 字段 → FAIL）
- [ ] GREEN：`build_l4` 输出 `containment_layer`/`containment_reason`（+`containment` 子字典）：
      `no_divergence_observed_at_L1_or_L2` / `commit_boundary`（L1 分歧、L2 无）/
      `not_applicable(non_masked_outcome)` / `inconsistent_with_masked`（L2 分歧却判 Masked
      → 加 violation，响亮）
- [ ] 验证：`tests/test_lsu_obs_core.py` + 回归 `tests/test_lsu_l3_propagation.py`
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G2 Masked 记录 containment layer/reason`

## Task 3 — [G3] 缺 stdout：先置 activated 再 INCONCLUSIVE；handoff 响亮记录不静默丢

- [ ] RED：`test_lsu_l5_classify.py` `g3_*`（INCONCLUSIVE 无 activated → FAIL）+
      `tests/test_lsu_handoff.py` `g3_handoff_*`（INCONCLUSIVE 样本被 `continue` 静默丢 → FAIL）
- [ ] GREEN：`classify()` 早退路径补 `activated`/`injected`/`error_class="input_incomplete"`；
      `lsu_handoff._nine_class_counts` 增 `inconclusive`/`classifier_error` 显式桶 +
      `unrecorded_samples` 路径列表（不再 `continue`）
- [ ] 验证：两个测试 + 回归 `tests/test_lsu_obs_core.py`
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G3 缺 stdout 不丢样本：先置 activated，handoff 响亮记录`

## Task 4 — [G4] oracle_diff 显式记录 + execution_complete 不得凭 activated=1/RC=0 通过

- [ ] RED：`g4_*`（无 golden 时仍判 Masked → FAIL）+ `test_lsu_obs_core.py` `g4_exec_*`
      （`_execution_complete` 无 oracle_diff 也 True → FAIL）
- [ ] GREEN：`classify()` 增 `oracle_diff={kind,compared,golden,observed,match,tolerance}`；
      `--golden` 缺 → 不判 Masked，响亮 `INCONCLUSIVE`+error+`unclassified=activated`；
      `_execution_complete` 要求 activated>0 且 outcome∈{Masked,SDC} 时
      `oracle_diff.compared is True`
- [ ] 验证：两个测试 + 回归 `tests/test_lsu_l3_propagation.py`
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G4 记录 oracle_diff；execution_complete 拒绝无 oracle 的 READY`

## Task 5 — [G5] terminal_verified 不接受孤立 resp

- [ ] RED：`test_lsu_l3_propagation.py` `g5_*`（仅 resp 的链 terminal_verified=True → FAIL）
- [ ] GREEN：承故障终点 = taint_reg/consumer/errant_commit；孤立 resp（resp 有而 taint 无）
      → `terminal_reason="response_without_taint_or_consumer"`、`terminal_verified=False`、
      `status="partial_no_verified_terminal"`；`first_terminal` 优先级去掉 resp
- [ ] 验证：`tests/test_lsu_l3_propagation.py`（ENV 判定不可变；直接运行读 PASS 行）+
      回归 `tests/test_lsu_obs_core.py`
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G5 L3 terminal_verified 不再接受孤立 resp`

## Task 6 — [G6] 非哈希 oracle 支持（no-drift 复用 tools/classify.py）+ 响亮拒判

- [ ] RED：`g6_*`（ARRAYHASH 运行被判 Crash → FAIL）
- [ ] GREEN：`lsu_l5_classify` 增 `--oracle-kind/--oracle-tol`；extract_* 直接 import
      `tools/classify.py`（单一分类器，零漂移）；默认 exact_hash 但输出里是
      ARRAYHASH/ELEMDIFF/ULP → 自动识别并记 `oracle_kind_source=auto_detected`；
      exit=0 无任何 oracle 行 → 响亮 error + INCONCLUSIVE（绝不判 Crash）
- [ ] 验证：`tests/test_lsu_l5_classify.py` + 回归 `tests/test_lsu_obs_core.py`
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G6 非哈希 oracle 对齐 tools/classify.py + 响亮拒判`

## Task 7 — [G7] Detected/Contained 可被填充（不再硬编码 0）；无信号记 n/a

- [ ] RED：`g7_*`（含 detector 信号行仍 detected=0 → FAIL）
- [ ] GREEN：`classify()` 解析检测器信号行
      `CHAOS_DETECT: layer=<Hardware RAS|OS|Application|None> contained=<0|1> tick=<n> ptag=<n> reason=<...>`
      （+ `--detected-layer/--contained` CLI 显式输入）；contained=1 → outcome
      "Detected/Contained"；无信号 → `detected_na=True` 且 `classes_na=["Detected/Contained"]`
      （n/a 不静默零）；`obs_core.first_detection_source` 优先消费 verdict 的 detection_layer
- [ ] 验证：`tests/test_lsu_l5_classify.py` + `tests/test_lsu_obs_core.py` + 回归
- [ ] commit `[LSU][MDSPEC][R6-ORACLE] G7 Detected/Contained 由检测器信号填充，无信号记 n/a`

## 收尾

- [ ] `python3 tools/lsu_test_runner.py` → FAIL=13（无 NEW FAIL），含我的套件
- [ ] `git push -u origin r6-oracle`
- [ ] 摘要落 `/home/sdc/gem5-fi-ding/runs/lsu/r6_reports/L18.md`

## C++ 发射器侧字段契约（本车道不给 C++，交发射器车道）

1. 崩溃事件须携带 `detection_layer` / `contained` / `outcome`（现已存在列，但
   `CHAOSPropagation.cc:chain_end` 恒写 `None`/`0`、`seen_errant` 硬编码 false）。
2. 需要一个硬件检测器信号行（stdout）：
   `CHAOS_DETECT: layer=<Hardware RAS|OS|Application|None> contained=<0|1> tick=<n> ptag=<n> reason=<...>`
3. L5 结局 join 需要的检测点字段：`fault_id`(=ptag)、`ptag`、`commit_seq`、`pc`、
   `dyn_inst_seq`（`PROP_EVT_FIELDS` 已有这些列，需在 crash/abort 路径也写出）。
