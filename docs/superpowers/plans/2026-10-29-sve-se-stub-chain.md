# 2026-10-29 SVE SE stub 链迭代——打通 SDCShield 真二进制全链路（Task 5）

## 目标

Task 4 后的真二进制 spike 死于
`warn: ignoring syscall sched_getaffinity` → `internal error: ambient logical
processor set appears to be empty!` → `no devices found`（exit 71）。
本任务为时间盒迭代（≤6 个新 stub）：逐屏障推进，直至 spike 出现真
`exit: pass`（VL=512）。

## 双侧分析结论（sdcshield framework ↔ gem5 SE，2026-10-29 静态读码实测）

屏障链（按执行序，均经框架源码定位）：

1. **sched_getaffinity（当前）**：`framework/sysdeps/linux/cpu_affinity.cpp:28`
   以 `sched_getaffinity(0, CPU_SETSIZE bytes, mask)` 取亲和掩码；
   `topology.cpp:1829` 掩码为空 → `device_count==0` → exit 71。gem5 侧
   `syscall_emul.hh:3055` 已有上游 `schedGetaffinityFunc`（riscv/x86-64 在
   用），填全系统 thread context 位图——**只需挂 ARM64 表**（#242）。
2. **memfd_create（#279，无 handler→fatal）**：`init_shmem`（sandstone.cpp:352）
   与每线程日志 `open_new_log()`（logging.cpp:343）都走 `open_memfd()` →
   `memfd_create`。框架自带 fallback 链（O_TMPFILE→常规 tmpfile，
   sysdeps/unix/tmpfile.c:117-144），故 stub 语义 = 返回 `-ENOSYS` 触发框架
   自身 fallback（gem5 不模拟 memfd 跨进程共享，ENOSYS 是诚实语义）。
3. **fdatasync（#83，无 handler→fatal）**：`logging_flush()`（logging.cpp:1034，
   每测试的 YamlLogger::print 调用）对 log fd fdatasync。
4. **线程/子进程需要空闲 ThreadContext**：se_sve.py 只配 1 CPU 1 TC，
   `doClone` 的 `threads.findFree()` 找不到 → clone -EAGAIN。需要
   se_sve.py（sdcshield-main 仓的配置脚本）配 N CPU。
5. **fork 模式专属链**（默认 fork_each_test）：call_forkfd 探测
   （sandstone_run.cpp:1307）依次踩 eventfd2（#19 fatal）、waitid（#95
   fatal，P_PIDFD 探测）、clone(CLONE_PIDFD)（doClone 不建 pidfd）、
   poll 对 fd=-1（pollFunc 对负 fd 直接 `(*p->fds)[-1]` 断言崩溃）。

**关键约束（gem5 SE 上游限制，如实记录）**：
- SE 无异步信号投递（signalList 仅被 wait4/poll 消费），forkfd 的
  SIGCHLD-handler 兜底路径**不可行**；可行路径是 pidfd 仿真
  （waitid(P_PIDFD)+CLONE_PIDFD+poll）。
- SE 的 `mmap` 写共享区不跨进程传播（mmapFunc warn_once，fork 页复制）：
  fork 模式下逐线程明细日志降级，但 pass/fail/skip 判定经子进程退出码
  （`_exit(test_result_to_exit_code)`→waitid si_status）完整传递。
- 框架自带 `-f no`（no_fork，usage.md:91 调试模式）：单进程 + pthread
  worker（CLONE_THREAD 共享页表），shmem 进程内共享，完整保真。
  3-4 个 stub 即可到 exit: pass；默认 fork 模式全链需 7 个（超时间盒 1 个）。

## 迭代策略（时间盒内的最优路径）

1. Stub 1：挂 `schedGetaffinityFunc<ArmLinux64>`（#242）→ spike 验证屏障
   推进。
2. Stub 2：`memfd_create` → -ENOSYS（warn_once 说明框架 fallback 接管）。
3. Stub 3：`fdatasync` → 宿主透传（FileFDEntry）。
4. se_sve.py 多 CPU（sdcshield-main 配置变更，非 gem5 stub）。
5. `-f no` spike（框架自身模式）拿到真 `exit: pass`（保真路径）。
6. 剩余预算（≤3 stub）推进默认 fork 模式：eventfd2 → waitid →
   CLONE_PIDFD；用尽即停，链况如实上报（FS/模式路由交人工）。

## 验证（每 stub）

- 增量重建 `scons -C CHAOS/gem5 build/ARM/gem5.opt -j16` 零新警告；
  产物拷回 `CHAOS/gem5/build/ARM/gem5.opt`。
- spike：run_sve.sh 真二进制 `sve_rot_ldr_at_top -t 500 -n 1 --vl 4`，
  提交信息引用 before/after fatal 行；跑完 `rm -rf m5out`。
- 最终回归：`sve2_fmmla_dual --sve_vl 4` SDCSHIELD_FAILS=0 +
  `tools/verify_gem5_injectors.sh`。

## Steps

- [ ] Step 1: getaffinity 挂表 + 重建 + spike（屏障 1 消失证据）
- [ ] Step 2: memfd_create ENOSYS stub + spike
- [ ] Step 3: fdatasync stub + spike
- [ ] Step 4: se_sve.py 多 CPU + spike
- [ ] Step 5: -f no spike → exit: pass（或继续排障）
- [ ] Step 6: 默认模式 fork 链推进（预算内）
- [ ] Step 7: 回归 + injector + 记录 HEAD sha
