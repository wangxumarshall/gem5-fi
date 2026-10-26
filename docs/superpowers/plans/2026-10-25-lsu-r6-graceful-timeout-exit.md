# R6-GRACEEXIT 实现计划：超时退出必须先优雅收口（消除证据截断）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 让 `--fs-timeout` 到点后 gem5 走**正常 finalize**（stats 落盘、prop_evt gzip 收尾、退出回调打印 `CHAOS_LSU_TRIGGER`），从而 Timeout 成为**非截断**的真实实验结局；只有优雅失败才升级 SIGTERM/SIGKILL，且升级后仍诚实标截断。

**Architecture:** 只改 tools/ 与运行 harness，**不重建 gem5**。gem5 已自带 SIGINT 处理器（`src/sim/simulate.cc:195 initSigInt()` → `exitNowHandler` → `async_exit` → `exitSimLoop("user interrupt received")`），这正是优雅退出入口；而现在的超时路径直接 SIGTERM（无处理器 → 立即死亡）。把 `run_gem5` 的升级顺序改为 SIGINT → (grace) → SIGTERM → (grace) → SIGKILL，并把「谁真正终结了进程 / 是否优雅 / 预算是否耗尽」如实记录到 chain report 与 manifest。

**Spec:** 本轮用户裁决（2026-10-25 接管指令）§二/§三/§四。

## §0 设计记录

### 已定位的真实根因（只读实证）

| 事实 | 位置 |
|---|---|
| 超时判定 = `subprocess.TimeoutExpired`（`communicate(timeout=args.fs_timeout)`）| `tools/lsu_campaign.py:2346` |
| 到点后**直接 SIGTERM** 进程组，10 s 后 SIGKILL | `tools/lsu_campaign.py:2349-2362`（`run_gem5(..., grace=10)`）|
| gem5 **只**为 SIGINT 装了处理器；SIGTERM/SIGKILL 走默认动作（立即死亡，无 finalize）| `src/sim/init_signals.cc:472-478`（`initSigInt`）、`src/sim/simulate.cc:195` |
| SIGINT → `exitNowHandler` → `async_event/async_exit` → `exitSimLoop(...)` → 正常收口 | `init_signals.cc:144-150`、`simulate.cc:324-327` |
| 截断判定 = prop_evt gzip 不完整 **或** stats.txt 缺失/0 字节 | `tools/lsu_campaign.py:1640-1672` |
| Timeout 分支把 `exit_code=None` 交给 chain report，且不记录「谁杀的」 | `tools/lsu_campaign.py:2445-2472` |
| campaign rc=0 掩盖 gem5 的 `-15` | `run_gem5` 返回 `exit_code=-15`，campaign 自身正常返回 0 |

### 语义边界（不得越界）

1. 不换注入点、不改 F6 eligibility、不动传播链/ancestry。
2. 不放宽 admission / truncation / conservation / 未知退出规则。
3. 不伪造 containment，不把 chain_end 当 L5。
4. 优雅收口路径**只**负责结束模拟与刷新证据：不写任何事件、不改 oracle 类别（Timeout 不被改写为 Crash/Contained）。
5. 非超时运行路径逐字节不变（`--timeout` 内正常结束的 run 走原分支）。

---

## Global Constraints

- 只改 `tools/lsu_campaign.py` 与 `runs/lsu/` 下的 harness（+ 新增测试）。**不重建 gem5**。
- 单元测试必须快（无 gem5）；真实 gem5 验证用**短超时**隔离跑（分钟级）。
- 不得用 SKIP/XFAIL，不得删/弱化断言。
- 一单元一提交；提交后 push `origin/lsu-mdspec-20261019`。
- commit 消息不得以 `Co-Authored-By: Claude` 结尾。
- 禁止 `git add -A`；保留既有未提交/未跟踪文档。

## Review Focus

1. **优雅路径不得改变 oracle/事件** —— Timeout 仍须为 Timeout；事件流不得多出/少掉任何事件。测试：Task 1 Step 6（真 gem5 短超时）比对事件数只由真实执行决定 + `oracle=Timeout`。
2. **非超时行为不变** —— `--timeout` 内正常结束的运行必须走原路径。测试：Task 1 Step 5 单元测试 + 完整回归。
3. **升级后仍诚实** —— SIGTERM/SIGKILL 之后 `graceful=False`、截断标记保留、`admitted` 不得为 True。测试：Task 1 Step 2/3/7。
4. **manifest 不再被 rc=0 掩盖** —— 必须同时有 `campaign_exit_code` 与 `gem5_exit_code`/`gem5_exit_signal`/`timeout_triggered`。测试：Task 2。
5. **预算耗尽仍能收口** —— 即使 guest 一直不结束，SIGINT 也让 gzip/stats/摘要齐备。测试：Task 1 Step 6。

---

## File Structure

| 文件 | 责任 |
|---|---|
| `tools/lsu_campaign.py`（改） | `run_gem5` 优雅升级 + 退出事实回传；FS/SE Timeout 分支如实记录 |
| `tests/test_lsu_campaign_graceful_timeout.py`（新） | 假子进程驱动的升级顺序/字段契约（快，无 gem5） |
| `runs/lsu/r6_mkmanifest3.py`（新） | manifest 同时记 campaign/gem5/timeout 事实 |
| `runs/lsu/r6_c9_run.sh`（新） | c9 harness：调用 mkmanifest3，沿用 flock/并发上限 |

---

### Task 1: run_gem5 优雅退出升级 + Timeout 事实如实记录

**Files:** Modify `tools/lsu_campaign.py`; Create `tests/test_lsu_campaign_graceful_timeout.py`

**Interfaces — Produces:** `run_gem5(cmd, timeout, out_file, err_file, grace=10, sigint_grace=120) -> {timed_out, exit_code, signal, graceful, escalated_to, sigint_sent, stdout, stderr, pid}`；FS/SE Timeout 结果 dict 新增 `timeout_triggered`、`gem5_exit_code`、`gem5_exit_signal`、`graceful`。

- [ ] **Step 1: 写失败测试**（假子进程：SIGINT 后优雅退出 / 只认 SIGTERM / 只认 SIGKILL）——断言升级顺序、`graceful`/`signal` 字段、以及超时后**先** SIGINT。
- [ ] **Step 2: 跑测试确认红**（`graceful` 字段不存在 → KeyError/assert）。
- [ ] **Step 3: 实现 `run_gem5` 升级**：SIGINT → `sigint_grace` → SIGTERM → `grace` → SIGKILL；`graceful=True` 当且仅当 SIGINT 后自行退出。
- [ ] **Step 4: 跑测试确认绿。**
- [ ] **Step 5: FS/SE Timeout 分支**：写入 `timeout_triggered/gem5_exit_code/gem5_exit_signal/graceful`，并把**真实** exit code 传给 `write_chain_report`；非优雅时保留响亮 `run.err` 说明。
- [ ] **Step 6: 短时隔离验证（真 gem5）**：`--fs-timeout 120` 跑一格到全新目录，验证 `gzip -t`=0、stats 非零、`CHAOS_LSU_TRIGGER` 出现、`outcome=Timeout`、`graceful=true`。
- [ ] **Step 7: 提交。**

### Task 2: manifest 记录 campaign/gem5/timeout 三种事实

**Files:** Create `runs/lsu/r6_mkmanifest3.py`, `runs/lsu/r6_c9_run.sh`

- [ ] **Step 1**: manifest 从 `cell_results.json`/`chain_report.json` 提取 `gem5_exit_code`/`gem5_exit_signal`/`timeout_triggered`，与 `campaign_exit_code` 并列。
- [ ] **Step 2**: 验证：对已完成的 r6_c8 现场重生成 manifest，`campaign_exit_code=0` 且 `gem5_exit_*` 不再是空。

---

## 已知风险

- 若 `SIGINT` 后 gem5 的 exit code 非 0 或仍不写 stats，则优雅路径不成立 → 按停点规则汇报（不伪造）。
- Timeout 样本能否 `admitted=true` 由既有门禁决定（`opt1 = terminal=="full"` 且无 violation）；不放宽门禁。若门禁拒绝，按停点规则汇报。
