# LSU OBS driver activated target 精确停止修复（OBS-FIX-1）

> 单元：`_run_item_parallel` 派发门不计在飞样本 → workers=2 在 target 附近超采。
> 触发事件：p5_formal_full_c01_f0_w6（C01-F0-W6）target_activated=385、实际 386、
> concurrency_overshoot=1（中央指令 2026-10-14 三.6-8）。
> 分支：`fix/lsu-obs-exact-stop-20261014`（基于 5d33c763，独立 worktree
> `.claude/worktrees/lsu-obs-fix`；不合并主分支，中央统一处理 Git 合并）。

## 根因（已实证定位）

`tools/lsu_obs_driver.py::_run_item_parallel` 派发循环（行 650-655）：

```python
while (... and len(futures) < workers and nxt < len(plan)
       and (self.args.samples
            or (activated < self.args.target and dispatched < self.args.cap))):
```

`activated` 只计**已完成**样本。workers=2、target=385 时：activated=384 且 1 个在飞 →
门放行第 2 个 → 两个都激活 → 386（超采 ≤ workers-1）。串行路径（workers=1）决策时无
在飞，无此问题。

## 修复设计

派发门 `activated < target` → `activated + len(futures) < target`（在飞按最坏情况
全激活计）。不变式：任一派发点 activated + 在飞 ≤ target → 终态 activated ≤ target
（精确停止）。代价：target 附近最后 ≤ workers-1 个样本串行化（对 35 分钟批次 < 1 分钟）。

- [x] 1. 复现测试先行（红）：`tests/test_lsu_obs_driver_workers.py` 新增 (g) 组——
      (g1) 全激活+时序抖动：finalized 数 == target 精确（旧代码必然 > target）；
      (g2) 混合激活模式（部分 activated=0）：不欠采不卡死，activated == target；
      (g3) 压力 30 轮随机时序/模式：每轮 activated == target、dispatched ≤ cap。
      对未修复代码运行 → (g) FAIL（超采实证）。
- [x] 2. 修复 `tools/lsu_obs_driver.py` 派发门 + `_run_item_parallel` docstring
      （OBS-FIX-1 语义注释）。
- [x] 3. 复跑 (g) → PASS；全量回归：`tests/test_lsu_obs_driver_workers.py`（a-f 原项
      不回退）+ `tests/test_lsu_obs_driver_cli.py` + `tests/test_claim_concurrency.py`。
- [ ] 4. 一个提交（计划+修复+测试 = 一个单元），push 分支
      `fix/lsu-obs-exact-stop-20261014`（非 main）。

## 验证命令（真实执行记录）

```bash
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-obs-fix
# 红（修复前，预期 g 组 FAIL：overshoot）
python3 $WT/tests/test_lsu_obs_driver_workers.py
# 修复后（预期全 PASS）
python3 $WT/tests/test_lsu_obs_driver_workers.py
python3 $WT/tests/test_lsu_obs_driver_cli.py
python3 $WT/tests/test_claim_concurrency.py
```

## 不变量与影响面

- 只改并行派发门；串行路径、--samples 显式清单模式、cap、GuardFailure/verify_refused
  停止语义全部不变。
- 观测产物/证据链零变化（改动在调度层，不在观测层）；观测二进制（70ff317b）不重建。
- handoff 侧（已有）：target/actual/overshoot 三字段显式记账；本修复后 overshoot
  预期恒 0，若非 0 必须在 handoff 显式记录并追查。

## 真实执行记录（2026-10-14）

- 红（修复前）：`g1/g2/g3` 全 FAIL——超采实证：g3 round0 target=3 实采 4；
  round3 target=7 activated=8（与 C01 target=385→386 同构）。(a)-(f) 原项全 PASS。
- 绿（修复后）：`python3 tests/test_lsu_obs_driver_workers.py` → `FAILURES: 无`、
  exit=0（a-f 43 项 + g1/g2/g3 全 PASS；g2 断言修正说明：混合模式下
  fin = activated + 未激活截断 ≥ act，activated 精确 == target 才是不变式）。
- 回归：`tests/test_lsu_obs_driver_cli.py` exit=0 `FAILURES: 无`；
  `tests/test_claim_concurrency.py` exit=0 `FAILURES: 无`。
- C01 证据零改动：本分支只动 tools/lsu_obs_driver.py 派发门 + 测试 + 本计划文件。
