# LSU OBS driver 跨 commit 续跑的 resume 身份核验修正（OBS-FIX-3）

> 单元：`run_sample` 的 COMPLETE 已存在分支（tools/lsu_obs_driver.py:495-501）
> 把 `git_commit` 一并传给 `verify_complete` 强制相等——跨工具修复提交的
> 前向续跑（既有样本记录旧 commit、driver 在新 commit）在第一个样本即
> verify_refused。触发事件：C02-F0-W6 续跑——s0-s168 记录 2aeb2f3f，
> OBS-FIX-2 合入后 driver HEAD=15c2af54+（与远程 OOO 线会师为 92f68d1e），
> 逐样本强等 git_commit 使 169 个完好样本全部拒收。
> 基线：fi-ding @92f68d1e（OBS-FIX-1/2 已在内；本修复不触碰派发门与
> skip 计数）。

## 根因与设计依据

- **身份对象 = 观测二进制**：中央指令 2026-10-14 第 6 条 / 提交 82583a6d
  （"admission identity 修正：准入对象=观测版二进制"）。gem5_opt_sha256
  才是身份闸门；git_commit 是溯源元数据（逐样本记录、审计逐样本校验，
  但不作续跑闸门）。
- **代码库自身先例**：`ensure_golden` 的缓存复用核验（driver:245-247）
  只传 `gem5_opt_sha256 + baseline_key`，从不传 git_commit；`baseline_ident`
  （driver:220-231）也不含 git_commit——golden 跨 commit 复用早已合法。
  run_sample 的 skip 核验是不一致的例外。
- 修复：skip 核验只强制 `gem5_opt_sha256`（与 golden 路径同款）；检出
  git_commit 漂移时打显式日志行（前向续跑边界，入 handoff），不拒收；
  二进制不一致 = 真身份违规，维持 verify_refused。

## 验收

- [x] 1. 复现测试先行（红）：`tests/test_lsu_obs_driver_workers.py` 新增
      (i) 组——(i1) pass2 manifest 注入 git_commit 漂移：续跑仍 skipped
      计数、只新跑差额样本、总数精确 target、状态 COMPLETE（旧代码
      verify_refused 必红）；(i2) 注入 gem5_opt_sha256 漂移：维持
      VERIFY_REFUSED、既有目录不被触碰（守护性断言，修复前后均绿）。
- [x] 2. 修复 run_sample skip 核验键集 + 漂移日志；docstring 注明依据。
- [x] 3. 复跑 (i) → PASS；全量回归 workers（a-i）+ cli + claim。
- [x] 4. 提交 fi-ding + push（非 main），报告提交号。

## 真实执行记录（2026-10-14）

（执行后回填）

- 红（修复前）：i1_commit_drift_resume_ok FAIL（pass2 VERIFY_REFUSED、
  fin=4/act=4，期望 COMPLETE/6/6——C02 跨 commit 续跑同构拒收实证）；
  i2 守护断言修复前即 PASS。
- 绿（修复后）：workers 全测 exit=0 `FAILURES: 无`（a-h 原项 + i1/i2）；
  test_lsu_obs_driver_cli.py exit=0；test_lsu_obs_core.py exit=0
  （verify_complete 本体未改——只改调用方键集，core 直测不受影响）。
- 提交后随 C02 续跑验证生产路径。
