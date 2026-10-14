# LSU guard 锁/claim 文件创建原子化（OBS-FIX-4）

> 单元：lsu_guard.py 两处 O_EXCL 后就地 json.dump 的创建路径（experiment
> slot 锁 :370-377、claim :423-435）——O_CREAT|O_EXCL 先落**空文件**，
> json.dump 后才有内容；窗口期内并发读者（其他 driver 的 acquire 扫描/
> release/gate）读到空/半文件 → 判"锁文件损坏" → F-023 立即失败。
> 今日实证 5 次进程死亡全是它：
>   - driver D 11:55（slot_2 损坏）与 13:01（slot_1 陈旧）
>   - C02 正式批 12:46（slot_1 陈旧）与 15:07（slot_2 损坏）
>   - tests/test_claim_concurrency.py 14:44（隔离目录 slot_2 损坏）
> 基线：fi-ding @b8be45aa。

## 修复设计

`tmp 写全内容 + os.link 原子发布`：
1. 写 `{path}.tmp.{pid}.{tid}` 完整 JSON；
2. `os.link(tmp, path)`——link(2) 目标存在即 EEXIST，保持 O_EXCL 语义；
3. 读者从此只见"不存在"或"完整 JSON"，永不见空/半文件；
4. EEXIST → 走既有"已被占/损坏"分支；unlink tmp 清理。

心跳路径 `_write_lock_atomic`（tmp+os.replace）不动——它是覆写已存在
文件，replace 语义正确。claim 与 slot 锁的**创建**路径是本单元范围。

竞态正确性：两进程同 slot 同刻 link → 恰一个成功（另一个 EEXIST 落
占坑分支）；tmp 名含 pid+tid 不冲突；crash 遗留 tmp 不匹配
`experiment_slot_*.lock`/claim glob，不污染扫描。

- [x] 1. 复现测试先行（红）：tests/test_lsu_guard_v2.py 新增——
      (r) 创建原子性：monkeypatch json.dump 前 pread 新建锁文件路径，
      断言读者视角永非空（旧代码窗口实证=读到空文件）；并发 16 进程 ×
      4 槽 link 抢占恰 4 成功；crash-sim（写 tmp 后不 link）无锁可见。
- [x] 2. 修复两处创建路径（_publish_lock_atomic 辅助函数）。
- [x] 3. 复跑 (r) → PASS；回归 test_lsu_guard_v2 + test_claim_concurrency
      ×3 轮（历史偶发正是该测试先抓到的）+ workers 全测。
- [x] 4. 提交 fi-ding + push，报告提交号。

## 真实执行记录（2026-10-14）

（执行后回填）

- 红（修复前）：r1_no_torn_lock_visible FAIL——0.5s 放大窗口内读者连续
  观测到 9 字节半文件（'{"torn": '）×多轮，acquire 本身成功（与生产
  "锁文件损坏"误拒同构）；r2 并发抢占在旧代码即 PASS（EEXIST 语义正确，
  问题只在窗口）。
- 绿（修复后）：test_lsu_guard_v2 全测 exit=0 `FAILURES: 无`（1-8 原项 +
  r1 无 torn + r2 恰 6 成功/全可解析/无 tmp 残留）；
  test_claim_concurrency ×3 轮全 exit=0（历史偶发正源于此竞态）；
  test_lsu_obs_driver_workers 全测 exit=0。
