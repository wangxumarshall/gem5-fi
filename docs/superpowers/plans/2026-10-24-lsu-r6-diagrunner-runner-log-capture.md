# Plan — R6-DIAGRUNNER：runner 逐套件完整日志捕获（诊断基础设施）

Date: 2026-10-24 · Branch: `r6-diagrunner` · Worktree: `.claude/worktrees/r6-diagrunner`
Base: `848d803a`（合并 LINCHECK+FTIER+DIAG 三支之后的集成 HEAD）

## 背景 / 现象（已确证）

`tests/test_lsu_obs_driver_workers.py` 在 `tools/lsu_test_runner.py` 下 `[FAIL]`
（`/tmp/merged3.log:74`），失败详情被 runner 的打印上限截断为
`File ".../tools/lsu_o…`；同一套件 standalone 直接跑 `rc=0`。更早两个集成点
（`184c1a92`→`int_abcd.log:73`、`a01ad2fe`→`int_abrec.log:73`）runner 下均 `[PASS]`。

## 目标

1. 让 runner 在**不改变 PASS/FAIL 判定**的前提下，为每个套件落盘**完整**
   stdout / stderr / traceback / return code / 开始与结束时间 / 耗时 /
   是否 timeout · 是否被 signal 终止。
2. 提供 `--only SPEC` 选择器，使单个套件可作为 runner 的一部分被复现。

## 任务（一 patch = 一 commit）

- [x] T1 `tools/lsu_test_runner.py` 通用日志增强：
  - 新增 `_run_and_capture()`：`subprocess.run(capture_output=True, timeout=…)`，
    如实记录 `rc`（`rc<0` ⇒ `signal=-rc`）、`timeout` 标记、起止时间与耗时；
    `TimeoutExpired` 时保留已捕获输出。
  - 新增 `--log-dir DIR`：逐套件写 `<suite>.stdout` / `<suite>.stderr` /
    `<suite>.meta.json`（含 `argv/cwd/start/end/seconds/rc/signal/timeout/
    runner_status/runner_detail`）；pytest 收集阶段同样落盘。
  - 新增 `--only SPEC ...`：只跑匹配的套件（相对路径或文件名），跳过 pytest 收集。
  - `classify()` 逐字节未改（机械核验：新旧的 `classify()` 源码完全相同）。
  - 验证：`py_compile` 通过；`--only tests/test_lsu_obs_driver_workers.py
    --log-dir …` 判定与旧 runner 一致（SKIP），artifacts 完整。
  - 回归：同一 worktree/环境用**原 runner** 与**增强 runner** 各跑一次完整回归，
    FAIL 集合逐一相同（NEW FAIL = 0）。

## 明确不做（诚实边界）

- 不改 `tools/lsu_chain_check.py` / `tools/lsu_campaign.py` /
  `tools/lsu_ready_contract.py` / 任何 C++。
- 不改测试语义：不 SKIP/XFAIL、不删/弱化断言。
- **未测量即提高 timeout** 禁止：实测套件耗时 30.8s / 53.0s（含 d-real），
  runner 预算 900s ⇒ timeout 与本次现象无关，不改预算。
- 不启动 gem5 pilot；不 push 集成分支。
