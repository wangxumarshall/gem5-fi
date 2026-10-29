# R6 S 单元续接收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 固化 21 个已合格 S seed 的逐事件传播链文档并审计，然后按 LSQ-forwarding / F2-F4 NO_FIRE / S13 crash / S08 FAIL_OTHER 四条问题线诊断修复重跑，最终原子收口 S 单元并合入 origin/fi-ding。

**Architecture:** 只读原始证据（manifest/chain_report/prop_evt/stats/run.out/注入日志），逐 seed 生成 `<RunID>/<RunID>-seedN.md`；审计测试从同一原始流重新推导 ancestry/tick/哈希并与文档比对。修复线严格 TDD：失败测试 → 最小修复 → 定向测试 → 全量非慢速回归 → 只重跑受影响格。共享 C++/tools 文件串行、单一 owner。

**Tech Stack:** Python 3（gzip/json/hashlib）、gem5 v25.1.0.1 vendored C++、pytest、flock/tmux。

**Spec:** 用户本轮工作令（S 单元续接任务书）+ `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md`

## Global Constraints

- 已通过的 7 RunID × 3 seed（21 seed）**不得重跑**，除非 C++ 修改直接改变其共享语义（须先证明）。
- 冻结二进制：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`，SHA-256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`，`binary_source_head=2498573f`。
- 文档路径固定 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`；禁止顶层散落、禁止跨 seed 复用数值。
- 不得放宽 admission/EOF/truncation/conservation/unknown-exit 规则；不得 SKIP/XFAIL；NEW FAIL 必须为 0。
- gem5 并发 ≤ 2；新跑用全新目录 + flock + detached tmux；不覆盖失败现场。
- 远端 `origin/fi-ding` = `a92f9f6d`；S 分支 `run/r6-s-unit-20261029` 不得 force push。
- 如果修改 C++：只统一构建一次、构建期 gem5=0、保存完整日志、零新增告警、新二进制另存并分开记录 SHA/head。

---

### Task 1: 21 份 S seed 传播链文档 + 审计测试

**Files:**
- Create: `tests/test_lsu_s_prop_docs.py`
- Create: `tools/r6_s_prop_docs.py`
- Generate: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`（21 份）
- Modify: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.md`（追加 S 段）

**Interfaces:**
- Consumes: `/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit/<RunID>_s<N>/`
- Produces: `tools/r6_s_prop_docs.py` 可执行入口（默认生成，`--check` 只打印资格）。

- [ ] **Step 1: 写失败审计测试**（13 项：数量、1/2/3、文件名、无顶层、event_id/parent/tick 来自原始流、ancestry、tick 单调、判定一致、数值不跨 seed、SHA、S06 L3 语义、不破坏 T/A 文档、173 旧文档 SHA 不变）
- [ ] **Step 2: 运行测试确认 RED**（文档不存在）
- [ ] **Step 3: 实现生成器并生成 21 份文档**
- [ ] **Step 4: 运行测试确认 GREEN**；`pytest tests/test_lsu_prop_doc_audit.py tests/test_lsu_results_layout.py -q` 不得新增 FAIL
- [ ] **Step 5: 提交 `docs(lsu): add verified S-unit propagation paths` 并推送**

### Task 2: LSQ-forwarding 链缺口（A 线）

**Files:**
- Read: `runs/lsu/r6_s_unit/S{01,02,09,10}-F0-W5_s1/.../prop_evt.txt.gz`
- Modify: `CHAOS/gem5/src/.../CHAOSPropagation.cc` + `CHAOSLSQFwd`（仅当证据证明 emitter/consumer 缺口）
- Test: `tests/test_lsu_hook_*.py` / 新增失败测试

- [ ] **Step 1: 只读取证**：首条缺失边、应有 consumer、身份键（fault_id/corr/request_id/dyn_inst_seq/地址/掩码）
- [ ] **Step 2: 判定根因分类**（emitter/consumer/parent/checker/workload）并写失败测试
- [ ] **Step 3: 最小实现；统一构建一次（tmux、日志落盘、零新增告警、新 SHA 记录）**
- [ ] **Step 4: 定向测试 + 完整非慢速回归 NEW FAIL=0**
- [ ] **Step 5: 重跑受影响 RunID 的 seed1 → 验收 → seed2/3；生成文档**

### Task 3: F2/F4 NO_FIRE census（B 线）

- [ ] **Step 1: 从现有日志提取 attempted/eligible/首火位置；复现 F2/F4 调度**
- [ ] **Step 2: 对每 workload 给出最小预算；不可达者标 `BLOCKED_TRIGGER_REACHABILITY`**
- [ ] **Step 3: 有界预算重跑可达格（seed1→2→3）**

### Task 4: S13 Crash 未闭合（C 线）

- [ ] **Step 1: 逐样本定位最后有效事件 + `crash_translation_blocked` 来源**
- [ ] **Step 2: 判定真实 containment / 真实 Crash / 缺终局 / 身份丢失 / checker 分支错误；正负测试**
- [ ] **Step 3: 最小修复 + 定向重跑**

### Task 5: S08-F0-W5 FAIL_OTHER（D 线）

- [ ] **Step 1: 首分歧分析（注入真实性、三方计数、流完整性、首条违规边、与 S07/S09 差异）**
- [ ] **Step 2: 仅在证据支持时修复；否则诚实归档**

### Task 6: 收口

- [ ] **Step 1: 更新 INDEX/JSON 索引/CATALOG/INTERNAL-CATALOG/EVIDENCE 相对软链/STATUS/最终报告**
- [ ] **Step 2: 完整回归 + 链接审计（断链 0）**
- [ ] **Step 3: 提交 `docs(lsu): close S-unit evidence and status`；推送 S 分支**
- [ ] **Step 4: 收口门禁全过后安全合入 origin/fi-ding（禁止 force push）**
