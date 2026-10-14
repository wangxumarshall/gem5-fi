# LSU OBS driver target 模式续跑的 skipped 样本 activated 计数修复（OBS-FIX-2）

> 单元：`run_item`（串行）与 `_run_item_parallel`（并行）对 `run_sample` 返回
> `"skipped"`（COMPLETE 已存在→只读核验跳过）的样本**不计入 activated**——
> target 模式断点续跑会漏计既有样本，继续跑到 target 个"新"激活，总数超采。
> 触发事件：p5_formal_full_c02_f0_w6（C02-F0-W6）12:46:18 因 slot 1 陈旧锁
> GUARD_FAILURE，已有 169 COMPLETE（activated=155/385）；直接续跑将跑到
> 155+385=540。中央指令 2026-10-14 #1-#3：从下一合法样本安全续跑且最终
> activated 严格 =385、overshoot=0。
> 基线：fi-ding @2aeb2f3f（精确停止已合并；本修复**不触碰**派发门——只修
> skipped 计数，属精确停止的配套缺口，非重新实现）。

## 根因

`run_sample` 对已 COMPLETE 样本返回 `"skipped"`（tools/lsu_obs_driver.py:501），
但两条路径的计数分支只认 `r == "complete"`：

- 串行 `run_item`：`if r == "complete": ... activated += ...`
- 并行 `_run_item_parallel`：同

→ 续跑遍从 0 开始计 activated，把既有样本当不存在。

## 修复设计

两处 `r == "complete"` → `r in ("complete", "skipped")`；skipped 样本的
`l5_verdict.json` 在最终目录中已由 `verify_complete` 核验存在且身份一致
（git_commit + gem5_opt_sha256 匹配 manifest），直接读出计数。精确停止门
（`activated + len(futures) < target`）不变——skip 计入后不变式依旧成立：
终态总 activated（既有 + 新）精确 == target。

- [x] 1. 复现测试先行（红）：`tests/test_lsu_obs_driver_workers.py` 新增 (h) 组——
      (h1) 串行两遍：pass1 target=4 全激活跑完（4 COMPLETE）；pass2 同
      campaign target=6 续跑 → 期望 s0-s3 skipped 且计入 4、只新跑 s4/s5、
      总 activated==6 精确、COMPLETE 目录==6、run_fault 新调用仅 {4,5}。
      旧代码必然红（新跑 6 个 → 目录 10 个）。
      (h2) 并行同款（workers=2，pass1 target=3 → pass2 target=5）。
- [x] 2. 修复两处计数分支 + 注释（OBS-FIX-2）。
- [x] 3. 复跑 (h) → PASS；全量回归：workers 全测（a-h）+
      `tests/test_lsu_obs_driver_cli.py` + `tests/test_claim_concurrency.py`。
- [ ] 4. 提交 fi-ding（前向新提交，非重复合并；stage 显式三文件，不碰
      未提交 Excel），push origin fi-ding（非 main），报告提交号。

## 验证命令

```bash
cd /home/sdc/gem5-fi-ding
python3 tests/test_lsu_obs_driver_workers.py     # 红：h1/h2 FAIL（修复前）
python3 tests/test_lsu_obs_driver_workers.py     # 绿：FAILURES 无 exit 0
python3 tests/test_lsu_obs_driver_cli.py
python3 tests/test_claim_concurrency.py
```

## 影响面

- 只改计数分支；派发门/cap/GuardFailure/verify_refused/claim/观测产物链全部
  不变；C02 既有 169 样本零改动（只读核验路径）。
- C02 续跑后批内 identity 将含两个 commit（s0-s168@2aeb2f3f + s169+@本修复），
  handoff 如实记录边界；审计 v2 逐样本校验不受影响。

## 真实执行记录（2026-10-14）

- 红（修复前）：h1_resume_counts_skipped_exact FAIL（新跑 s4-s9 共 6 个、
  fin=10、磁盘 act=10，期望 {4,5}/6/6）；h2 FAIL（新跑 s3-s7 共 5 个、
  fin=8/act=8，期望 {3,4}/5/5）——与 C02 续跑 155+385=540 超采同构。
- 绿（修复后）：workers 全测 exit=0 `FAILURES: 无`（a-g 原项 + h1/h2）；
  test_lsu_obs_driver_cli.py exit=0 `FAILURES: 无`。
- test_claim_concurrency.py：首轮 3 项 FAIL（d_no_fatal 等）= **预存偶发
  guard 锁损坏竞态**（失败发生在测试自己的隔离临时 guard 目录
  .tmp_lsu_conc/gd_*/experiment_slot_2.lock，"锁文件损坏"；该测试不 import
  lsu_obs_driver，与本修复无关）；同代码 fix worktree@2aeb2f3f 通过、
  主树复跑 2 次均 exit=0 `FAILURES: 无`。根因另行定位（guard 创建路径
  lsu_guard.py:375 O_EXCL 后就地 json.dump，非原子；_write_lock_atomic
  心跳路径已是 tmp+replace）。
