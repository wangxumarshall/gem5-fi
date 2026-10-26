# R6-GATE-B: LSU formal-admission hard gate

> **本文件是 R6-GATE-B 的单一权威计划（L34 合流版）**：把 `r6-gate` 分支的原始
> Task A/B/C 计划、B2 缺陷修复计划（D1–D5）、L29 接线修复，与集成分支
> `lsu-mdspec-20261019` 侧已落地的同一逻辑，合并成**一份**计划。完成项只记一次、
> 不重复声称；每项附提交身份与真实证据。
>
> 执行者：Agent B（`r6-gate` worktree，base `lsu-mdspec-20261019` @ `97f74786`）
> → L34 语义合流（worktree `r6-gate-reconcile`，branch `r6-gate-reconcile`，
> base `lsu-mdspec-20261019` @ `45611d59`）。

**Goal:** make `docs/gem5-fi/lsu/mdspec/ready_contract.json` a HARD GATE: an activated
sample is READY **only if** either

1. it has a family-specific COMPLETE L0→L5 chain on one parent-event DAG; or
2. propagation stops at some layer with an explicit containment layer + reason +
   per-layer metrics, and every later layer is justified `N/A(contained)`.

Forbidden (loud failure, never silent pass): any `Unknown` in an activated sample;
`cache_access` impersonating the TLB's L1; stitching edges across branches / requests /
reversed in time; READY because of `activated=1`, `RC=0`, or a `chain_end` alone; a
missing per-layer mandatory metric.

**Architecture.** All rules live in one pure function
`lsu_chain_check.check_admission(bundle)` (returning named violation tokens), consumed by
`lsu_ready_contract.build_contract` through a new per-RunID chain-evidence resolver that
reads the pilot `prop_evt.txt.gz` recorded in `pilot_evidence.json`. A RunID is READY
only when coverage is PASS **and** its pilot chain is admitted. Evidence root is
`LSU_CHAIN_EVIDENCE_ROOT` (default `REPO`), because the untracked `runs/` pilot data
lives in the base worktree, not in this worktree.

**Tech stack:** Python 3 stdlib only. Tests are plain scripts run by
`tools/lsu_test_runner.py`; PASS marker `ALL PASS`, failure marker `FAILURES: [...]`.

## File ownership (only these)

Original scope: `tools/lsu_chain_check.py`, `tools/lsu_ready_contract.py`,
`tools/lsu_audit.py`, `tools/lsu_blocked_triage.py`, `tools/lsu_prop_fields.py`,
`tests/test_lsu_chain_check.py`, `tests/test_lsu_ready_contract_*.py`,
`docs/gem5-fi/lsu/mdspec/R6-GATE-B-report.md`, `ready_contract.json/.md` (regenerated).
No C++, no `lsu_campaign.py`, no `lsu_runid_map.py`, no `lsu_coverage_matrix.py`.

**L34 合流范围追加**（跨分支冲突消解，见 Task F）：上述文件 +
`tests/test_lsu_r6_reconcile_realroot.py`（新）、本计划文件。
**明确不在范围内**：`docs/gem5-fi/lsu/mdspec/pilot_evidence.json`（注册表数据，
他 lane 所有，见 §残余缺陷 R2）。

---

### Task A — `check_admission` hard gate in `lsu_chain_check.py` (TDD)

- [x] A.1 RED: add section `[12]` to `tests/test_lsu_chain_check.py` calling
      `CC.check_admission(bundle)` for each forbidden case; run it, quote the real
      `AttributeError`-style failure. → `9a7da7cf`
- [x] A.2 Implement `GATE_VIOLATIONS`, `MANDATORY_METRICS`, `_has_unknown`,
      `_splice_detected`, `_cross_request`, `_time_reversed`, `_containment_ok`,
      `check_admission`. Re-run: quote `ALL PASS`. → `9a7da7cf`
- [x] A.3 Regression: `python3 tests/test_lsu_chain_check.py` still `ALL PASS`.
      → `9a7da7cf`

### Task B — wire the gate into the contract (`lsu_ready_contract.py`)

- [x] B.1 Add `chain_admission(runid, evidence_root)` + `CHAIN-EVIDENCE-MISSING` /
      `CHAIN-UNPROVEN` categories; READY now requires admission. → `ec75cdb1`
- [x] B.2 RED→GREEN in `tests/test_lsu_ready_contract_category.py`: a fake activated
      RunID with a non-chain pilot is BLOCKED before/after; update census. → `ec75cdb1`
- [x] B.3 Verify `test_lsu_ready_contract_verdict.py` and `-why.py` still PASS.
      → `ec75cdb1`

### Task C — regenerate contract + triage, report honest counts

- [x] C.1 `python3 tools/lsu_ready_contract.py` (with `LSU_CHAIN_EVIDENCE_ROOT` set to
      the base worktree), quote READY/BLOCKED. → `5a8841db`
- [x] C.2 `python3 tools/lsu_blocked_triage.py --contract ... --out
      docs/gem5-fi/lsu/mdspec/blocked_triage.md`, quote output. → `5a8841db`
- [x] C.3 Full suite `python3 tools/lsu_test_runner.py` — 0 **new** FAIL vs base
      `97f74786` (13 identical pre-existing FAILs from `317c71bf` chain semantics +
      missing binary; see report). → `0d0aa91b`
- [x] C.4 `docs/gem5-fi/lsu/mdspec/R6-GATE-B-report.md`; commit + push. → `0d0aa91b`

### Task D — B2 缺陷修复（门禁的四条语义漏洞）

Plan of record: `docs/superpowers/plans/2026-10-23-r6-gate-b2-chain-gate-defects.md`
（随本文件一并提交）。

- [x] D.1/D.5 `_explicit_l5` 结构化为「非生命周期 kind + detection_layer +
      outcome + 链关联 corr」。生命周期 `chain_end`（corr=none）**结构性**永不
      充当 L5：它不占任何层级（`_layer_of → None`），故
      `ready_by_chain_end_only` 由构造堵死，而非仅一条文案。真实流实证：T04/T02
      的 `chain_end` 为 `outcome=errant_commit_seen / detection_layer=None /
      corr=none`。→ `2fccab60`
- [x] D.2 `containment_from_events()`：option-2 含住束由**显式证据**推导（含住
      事件须自身从单元 L0→L_obs 前缀可证，且**后续层确无更深见证**），并把束传
      入 `check_admission`；`lsu_ready_contract.chain_admission` 据此调用。
      → `23ddfb48`
- [x] D.3 `_ancestry_request_breaks()`：跨请求拼接在**整条所选祖先**上抓（旧口径
      只比 ≤6 个层级代表，漏判真实 T04 的相邻 `resp` 跨请求对）。→ `1142a511`
- [x] D.4 族判定由 RunID 前缀给出（T/L/S/C/A/P/O），`cache_access` 不得冒充非
      cache 族的 L1；`cache` 族 L1 必须是 `cache_access`。→ `de7e5bd1`
- [x] D.* B2 回归：`tests/test_lsu_chain_check.py` sections `[13]–[16]` 全绿；
      计划/报告口径订正为「0 NEW FAIL（13 个既有 FAIL）」。→ `2b87cd9d`

### Task E — L29 链门禁接线修复（不改规则，只修可达性）

- [x] E.1 `lsu_ready_contract.build_contract`：链准入门禁对**每一行**评估并把判定
      记在行上（`row["chain"]`），与上游类别无关；上游阻塞（FS-INFRA/RULING/
      LICENSE…）是**独立**阻塞，链准入**不得**解除它，但其判定仍如实记录——
      否则"链已准入"在契约里不可见（L28 实测的"结构性不可达"）。
      `upstream_status` / `upstream_category` 与门禁判定分列。→ `77d25b47`
- [x] E.2 `chain_gate_summary()`：对**全体**行计数（`recorded/rows_total/admitted/
      evaluated/unproven/evidence_missing/blocked_upstream_admitted`），并把
      `evidence_root` 与 `event_cap` 写入契约（可复现口径）。→ `77d25b47`
- [x] E.3 `tests/test_lsu_ready_contract_chain_wiring.py`（新）：钉死"门禁对每一行
      运行 + 上游阻塞独立"。→ `77d25b47`
- [x] E.4 契约 volte-face 修正：md 镜像跟随 `--out`（此前硬编码写
      `MDS/ready_contract.md`，一次 `--out /tmp/...` 的复现运行会**静默改写**仓库
      内已提交的 md）。→ `77d25b47`
- [x] E.5 重生成契约 + 复现报告。→ `74fea866`

### Task F — L34 语义合流（本计划新增单元）

- [x] F.1 计划合并：把 `r6-gate` 与集成分支两侧的完成项、提交身份、证据合并为本
      份单一权威计划；不重复声称完成。← 本文件
- [x] F.2 `tools/lsu_chain_check.py`：把 `r6-gate` 相对集成分支基线的**净新语义**
      （D1/D5、D2、D3、D4 的 10 个 hunk）**逐函数对照**移植到集成分支基线之上
      （集成侧已有 `9a7da7cf` 的同一逻辑，作为基线保留）；不整文件覆写。
- [x] F.3 `tests/test_lsu_chain_check.py`：取两侧断言**并集**；唯一必须反演的一条
      （集成侧 `_L5_OUTCOME_KINDS == {"chain_end"}`）以**更强**形式保留（旧常量
      结构性移除 + chain_end 恒不占 L5），并在报告中点明。
- [x] F.4 `tools/lsu_ready_contract.py` + `tools/lsu_blocked_triage.py` +
      `tests/test_lsu_ready_contract_{category,verdict,gate,chain_wiring}.py`：
      前向移植（这些文件在集成分支自 merge-base 起未变动，无集成侧更新位）。
- [x] F.5 `tests/test_lsu_r6_reconcile_realroot.py`（新）：在**真证据根**上逐条
      复验 7 条强制性质 + 4 条逐 RunID 判决 + 325 行计数；缺真根时诚实 SKIPPED。
- [x] F.6 真证据根复验（`LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding`）：
      T04 拒（cross_request）、T08 认（containment L2）、T05/T01/T10 不误准入、
      L01/S10 流级不再是"no file"。
- [x] F.7 全套电池：`tests/test_lsu_chain_check.py`、`tools/lsu_ready_contract.py`
      （真根）、`tools/lsu_blocked_triage.py`、`tools/lsu_coverage_matrix.py`、
      `python3 tools/lsu_test_runner.py`。**任一 NEW FAIL ⇒ 停手上报。**
- [x] F.8 串行合入 `lsu-mdspec-20261019`；报告 merge commit、测试结果、真根
      325 行计数。**不 push 集成分支。**

## Honesty constraints

- Never relax a rule to keep READY high. A drop is expected and correct.
- Report `n/a` where a rule cannot be enforced yet, loudly.
- Quote only real command output.
- 缺流 = 未测量 ≠ "无传播/Masked"；空集不猜测。

---

## Outcome（单一权威版，完成项只记一次）

### 提交身份

| 单元 | 提交 |
|---|---|
| Task A（check_admission 硬门） | `9a7da7cf`（集成分支侧承载同一逻辑于 `lsu-mdspec-20261019`） |
| Task B（接入 contract） | `ec75cdb1` |
| Task C.1–C.2（重生成 + triage） | `5a8841db` |
| Task C.3–C.4（全套 + 报告） | `0d0aa91b` |
| Task D.1/D.5 | `2fccab60` |
| Task D.2 | `23ddfb48` |
| Task D.3 | `1142a511` |
| Task D.4 | `de7e5bd1` |
| 计划/报告口径订正 | `2b87cd9d` |
| B2 重生成 + 报告 | `d859f5ca` |
| Task E.1–E.5 | `77d25b47`、`74fea866` |
| Task F（L34 合流） | 见 `runs/lsu/r6_reports/L34.md` |

### 计数（r6-gate 侧，`LSU_CHAIN_EVIDENCE_ROOT` = 基线 worktree）

- 契约：READY 241 → 0，BLOCKED 84 → 325（CHAIN-UNPROVEN 43 /
  CHAIN-EVIDENCE-MISSING 198 / RULING 6 / LICENSE 12 / FS-MULTICORE 35 /
  FS-INFRA 24 / MODE-UNIMPL 3 / UNRESOLVED 4）。Verdict NO-GO。
- 全套：53 suites，FAIL=13 与 base `97f74786` 完全一致（0 NEW FAIL），
  PASS 33→34，ENV 5，SKIP 1。

### L34 合流后的真证据根计数（`LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding`）

见 `runs/lsu/r6_reports/L34.md`（真命令输出引用）。要点：
- 门禁对 **325/325** 行评估；`chain_gate.evidence_root` = 真根。
- READY = 0 / BLOCKED = 325；`admitted`（链证据成立）= 2（T06-F0-W4、T08-F0-W4，
  均为显式含住，**且**两者仍被上游 FS-INFRA 独立阻塞）——
  **链准入 ≠ 全局准入**：`admitted = 0/325`（L31 口径，baseline of record）。
- 契约口径 `CHAIN-UNPROVEN 44 / CHAIN-EVIDENCE-MISSING 197`（合计 241）与
  L31 全主机口径 `46 / 195` 的差值 = **2 行**（`C01-F0-W1`、`L01-F0-W5`）：
  流在盘上、但未登记进 `pilot_evidence.json` —— 见 §残余缺陷 R2。

### 残余缺陷（照实登记，留给其 owner）

- **R1** `chain_gate.unproven` / `evidence_missing` 在 r6-gate 的 worktree 根上曾
  **反向**（该 root 无 `runs/lsu/`）。L29 把 `evidence_root` 写入契约并以真根复算
  后消除；L34 的 `[7]`/`[9]` 断言把该性质钉死。
- **R2** `pilot_evidence.json` 缺 `C01-F0-W1`、`L01-F0-W5` 的登记（两者主机上有
  完整流）。L34 **未**修改该注册表（不在其文件所有权内）；门禁在**流级**已
  如实评估这两条并拒绝（`admitted=False`）。补登记 = 1 行数据修复，属注册表 owner。
