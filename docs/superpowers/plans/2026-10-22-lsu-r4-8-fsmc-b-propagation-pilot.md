# R4-8-FSMC-B 计划：FS-MULTICORE 35 项收口（传播链 + 注入 pilot + 待构建 C++）

- 分支：`r4-8-fsmc-b`（worktree `.claude/worktrees/r4-8-fsmcb`）
- base：`lsu-mdspec-20261019` @ `d63a5dd8`（已含 R4-8/R4-9 的 A、C 两轮集成）
- 二进制（只读复用，**不跑 scons**）：
  `.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
  （sha256 前缀 `54c2c78ce4c84bb2`）。**更正**：repo-root `build/ARM/gem5.opt`
  （`10590f6295bc4dec`）**不含** `CHAOSPropagation` 的新参数，用它 + `--chaos_propagation`
  会在 tick 0 抛 `pybind11::cast_error` abort（实测）。
  多核 FS 检查点 `/tmp/r4-8-fsmc/mc_boot/cpt.243414599076`（实测仍在）。
- gem5 预算：≤6 次；每次 `flock /tmp/lsu_gem5_slot1.lock`；outdir 只写 `/tmp/r4-8-fsmcb/`。

## 起点事实（实测复核，不是转述）

baseline `d63a5dd8` 已经把两轮集成进来：

| 组 | 10+15 格的既有结论 | 产物 |
|---|---|---|
| A（O01/O02/O03 × W7，10 格） | 平台+freestanding 载体**真机跑通**；F0/F5 = `CARRIER_ROUTED_PENDING_RUN`（4 格），F2/F6 = `BLOCKED_TRIGGER_TIER_UNIMPL`（6 格） | `configs/fs/lsu_multicore_fs.py`、`configs/fs/litmus_free.rcS`、campaign 家族 `exmon-fsmc` |
| C（O04/O05/O06/O07/O09，15 格） | 五个模型的钩子**已落地**（compile-unverified），格子仍 BLOCKED（负载身份 + 未 pilot） | `CHAOSCache` rmw 模式、`chaos_barrier_hook.hh`、`CHAOSLSQFwd` o06/o07 |
| B（C08，4 格） | 构造性互斥（CHAOSCache=classic `Param.Cache` vs Ruby controller） | — |
| D（O09/P09 × W13，6 格） | PARSEC 本仓库不可得 + 模型/宿主缺口叠加 | — |

**本轮的净新增**（其余项已由 baseline 覆盖，只做复核与汇总）：

1. **传播链**：`configs/fs/lsu_multicore_fs.py` 目前**不挂** `CHAOSPropagation`，
   所以 R4-9-FSMC-A 的 A 组只有 oracle 行、**没有** `exmon_monitor → exmon_rmw →
   exmon_stxr` 链（`CHAOSExMon.cc:255/97/113` 已经会发这些事件，只是 FS 侧没有
   实例 ⇒ `CHAOSPropagation::instance()` 为 nullptr ⇒ 全部 no-op）。这是
   **Python-only** 的缺口，可当场补齐并真机验证。
2. **注入臂**：R4-9-FSMC-A §2.6 明确未做"注入 vs 无故障"对照（ATOMIC 在观测窗
   内跑不完）。本轮用**小轮次 pilot 载体**取这条对照。
3. **待构建 C++ 清单**：CHAOSExMon 的 F 档位（A-2 六格）与 Ruby CHI L1 钩子
   （B 四格）—— 本轮禁 scons，整理成清单（含最小 diff 与落点）。

## Task 1 [R4-8-FSMC-B-1]：FS 多核传播链挂载（Python-only）

- [x] `configs/fs/lsu_multicore_fs.py`：增 `--chaos_propagation`、`--prop_trace_file`
      （默认 `prop_trace.csv.gz`）、`--prop_run_id`、`--prop_sample_run_id`；
      **O3-only 响亮拒绝**（镜像 `configs/se/arm_chaos_fs.py:555-573` 的 FS 先例）；
      import `CHAOSPropagation`，挂 `processor.get_cores()[0].core`。
- [x] 契约测试：新增断言（可写进 `tests/test_lsu_fs_infra.py`）：flag 存在、
      非 O3 拒绝、缺席时行为不变。
- [x] 真机验证：一次恢复臂带 `--chaos_propagation` 跑到底 ⇒ outdir 出现
      `prop_trace.csv.gz` / `prop_evt.txt.gz`。
- [x] commit + push。

## Task 2 [R4-8-FSMC-B-2]：A 组双核 O3+CHI 注入 pilot + 传播链证据

- [x] 小轮次 pilot 载体：Makefile 增 `payload_free_pilot`（`-DLITMUS_FREE_SB_ROUNDS=8
      -DLITMUS_FREE_ATOM_ROUNDS=2 -DLITMUS_FREE_ATOM_INCR=1`），产出
      `configs/fs/litmus_free_pilot.rcS`。**canonical `litmus_free.rcS` 与其
      sha256/golden 不动**（pilot 载体是同一份源码的另一个参数化，报告里显式记录）。
- [x] Run 1（干净臂）：恢复 + `--chaos_propagation --readfile=litmus_free_pilot.rcS`
      ⇒ 三条 oracle 行 + FINAL（记为该载体的 golden）+ prop 链非空。
- [x] Run 2（注入臂）：+ `--chaos_exmon --exmon_mode o01_monitor_addr_bitflip
      --exmon_max_faults 1` ⇒ `exmon_injections.log` 非空 + prop 链出现
      `exmon_monitor`/`exmon_rmw`/`exmon_stxr`（同一 fault_id 关联）。
- [x] 原始输出摘进报告；**只有真跑通才写"通过"**。
- [x] commit + push。

## Task 3 [R4-8-FSMC-B-3]：待构建 C++ 清单

- [x] CHAOSExMon F 档位：消费 `lsuTier/lsuWarmupEvents/lsuSpanEvents`
      （`chaos_trigger.hh` 的 F0/F2/F6 语义落点），解除 A-2 六格。
- [x] Ruby CHI L1 controller 上的 coherence-state 钩子（解除 B 四格）——给落点与
      最小 diff 草图。
- [x] 两处都标 `compile-unverified, pending integration`；写清"编排方要构建什么、
      断言什么"。
- [x] commit + push。

## Task 4 [R4-8-FSMC-B-4]：35 项逐项裁决 + 报告

- [x] `docs/gem5-fi/lsu/mdspec/R4-8-FSMC-B-report.md`：35 行表（RunID | 分类
      a–e | 证据 | 状态）+ 构造性互斥证明 + 外部缺失清单。
- [x] 复核 baseline 断言仍全绿：`python3 tests/test_lsu_fsmc_verdict.py`、
      `python3 tests/test_lsu_hook_o0x.py`、`pytest tests/ --ignore=…claim_concurrency`。
- [x] commit + push。

## 停止条件

所有 Task 完成，或真机证据证明某条路不可达且已如实记录。**不得**在未跑通时宣称解锁。
