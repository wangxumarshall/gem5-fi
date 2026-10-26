# R6-FIXD2 — 权威状态表改「两轴表达」（axis A evidence_state × axis B eligibility）

> Lane D2（独占）：按用户裁决 B（`docs/gem5-fi/lsu/mdspec/R6-RULINGS-20261023.md`）
> 把 Lane D 的**一轴六态**表改为**两轴、互不覆盖**的表达。
> 证据根：`LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding`（与契约
> `ready_contract.chain_gate.evidence_root` 一致，已实测）。
> base：Lane D 交付 `r6-fixd`（8ee2f320）——注意 lane 指令给出的 `94c1c13d` 上
> **没有** `tools/lsu_r6_status_table.py`（该文件由 Lane D 新建于 07c004e5 之后），
> 也无 `R6-RULINGS-20261023.md`；改造对象只能从 Lane D 交付派生。
> TDD：先写到真实 RED（复现旧口径把带证据的阻塞行压成 BLOCKED / 单轴短路），
> 再实现到真实 GREEN；既有断言**不得删除或弱化**。
> 基线：`python3 tools/lsu_test_runner.py` FAIL=13，**NEW FAIL 必须为 0**。

## 独占文件

- `tools/lsu_r6_status_table.py`
- `tests/test_lsu_r6_status_table.py`

**不碰**：`tools/lsu_chain_check.py`、`tools/lsu_campaign.py`、`tools/lsu_ready_contract.py`、C++、集成分支。

## 问题（裁决 B 的动机）

Lane D 的表是**一轴六态**：`NOT_RUN / EVIDENCE_MISSING / TRUNCATED / UNPROVEN /
PILOT_READY / BLOCKED`。真根实测 `BLOCKED=0`，因为"带证据的上游阻塞行"又同时是
截断/未跑流，于是 BLOCKED 被压成 0 —— **一个状态同时承担"观测进度"与"是否被阻塞"**，
且汇总只有一轴，"BLOCKED=0"极易被误读成"全部可运行/已通过"。

## 目标（两轴，互不覆盖）

- **轴 A `evidence_state`（磁盘事实，仅五值）**：`NOT_RUN` · `EVIDENCE_MISSING` ·
  `TRUNCATED` · `UNPROVEN` · `PILOT_READY`。**永不为 BLOCKED**。
- **轴 B `eligibility`**：`RUNNABLE` · `BLOCKED`，附 `blocker_code` + `blocker_detail`。
- 两轴**并存**：磁盘事实照实显示，阻塞单独表达，绝不互相覆盖。
- 汇总**同时**报告：各 `evidence_state` 数量 · `RUNNABLE`/`BLOCKED` 数量 ·
  `PILOT_READY`（准入）数量 · `blocker_code` 分类数量；并显式声明
  "`BLOCKED=0` 只表示该维度无 blocker，不代表全部可运行/已通过"。
- 正式准入依据**仍是 `PILOT_READY`**（evidence PILOT_READY ∧ eligibility RUNNABLE）。

---

## 任务 1（唯一单元 → 唯一 commit `[LSU][MDSPEC][R6-FIXD2]`）

**RED**：在 `tests/test_lsu_r6_status_table.py` 新增（不改既有断言）：
- `test_two_axes_present_and_disjoint`：每行含 `evidence_state∈EVIDENCE_STATES`、
  `eligibility∈{RUNNABLE,BLOCKED}`、`blocker_code`/`blocker_detail`；无行 `evidence_state==BLOCKED`。
- `test_blocked_row_keeps_disk_fact`：合成 X06（证据已准入 + FS-INFRA 阻塞）⇒
  `evidence_state=="PILOT_READY"` **且** `eligibility=="BLOCKED"` **且** `blocker_code=="FS-INFRA"`（并存）；
  X03（截断+阻塞）⇒ `evidence_state=="TRUNCATED"` 且 `eligibility` 照实。
- `test_summary_reports_both_axes`：`summary["evidence_states"]` 五键、`summary["eligibility"]`
  两键、`summary["pilot_ready"]["count"]`、`summary["blocker_codes"]` 分类，且含
  `BLOCKED=0` 解释注记。
- `test_real_root_two_axes`：真根锚点——
  `C01-F0-W1`⇒`evidence_state=="NOT_RUN"`；`T06-F0-W4`/`T08-F0-W4`⇒`TRUNCATED` **且**
  `eligibility=="BLOCKED"`/`blocker_code=="FS-INFRA"`；`L01-F0-W5`⇒`TRUNCATED` 且
  `conditions.unproven is True`（并存）。
- 把新测试挂进 `__main__` 列表。
- **RED 证据**：`LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding python3 tests/test_lsu_r6_status_table.py`
  在旧实现上真实 FAIL（`KeyError: 'evidence_state'`）。

**GREEN**：改 `tools/lsu_r6_status_table.py`（加性，保留兼容字段）：
- 增 `EVIDENCE_STATES`（5）/`ELIGIBILITIES`（2）；`STATES`（6）保留为**遗留单轴**兼容常量。
- `adjudicate()` 计算 `evidence_state`（五值，永不为 BLOCKED）、`eligibility`、
  `blocker_code`、`blocker_detail`；保留 `state`（遗留单轴，旧值语义不变）与
  `upstream_block`/`upstream_blocked`/`conditions`/`failure_reason`。
- `summarize()` 增 `evidence_states`/`eligibility`/`pilot_ready`/`blocker_codes` 与
  `BLOCKED=0` 解释注记；保留遗留 `states`/`pilot_ready_list`。
- `write_outputs()` MD 增两轴列与两轴计数小节。
- 模块 docstring 更新为两轴口径。

**GREEN 证据**：同测试文件 `FAILURES: 0`（含真根锚点）；工具真根跑给出两轴计数；
`python3 tools/lsu_test_runner.py` NEW FAIL=0。

- [x] RED 测试写入并实测 FAIL
      （`AttributeError: module 'lsu_r6_status_table' has no attribute 'EVIDENCE_STATES'`）
- [x] 实现两轴，实测 GREEN（`FAILURES: 0`；pytest `8 passed`）
- [x] 真根跑工具，记录两轴计数
      （evidence: NOT_RUN 305 / EVIDENCE_MISSING 0 / TRUNCATED 8 / UNPROVEN 12 /
      PILOT_READY 0；eligibility: RUNNABLE 241 / BLOCKED 84；blocker_code:
      FS-MULTICORE 35 / FS-INFRA 24 / LICENSE 12 / RULING 6 / UNRESOLVED 4 /
      MODE-UNIMPL 3；正式准入 PILOT_READY∧RUNNABLE = 0）
- [x] 全量 `lsu_test_runner.py` NEW FAIL=0（基线 FAIL=13，改后 FAIL=13，集合逐一相同）
- [x] commit `[LSU][MDSPEC][R6-FIXD2]` + push `r6-fixd2`
