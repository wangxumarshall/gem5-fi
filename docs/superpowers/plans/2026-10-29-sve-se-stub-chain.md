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

- [x] Step 1: getaffinity 挂表（accf5166）——屏障 1 消失实证（exit 71→memfd fatal）
- [x] Step 2: memfd_create ENOSYS（f34ca013）——框架 tmpfile fallback 接管实证
- [x] Step 3': prlimit RLIMIT_NOFILE（df3eef1e，实测屏障 3 与预测不同：
      非 fdatasync 而是 prlimit 资源 7→getrlimit EINVAL→exit 71）
- [x] Step 4': socket 三件套挂表（070f0451，实测屏障 4：宿主 PATH 有 gdb
      →backtrace_on_crash→create_crash_pipe→socketpair fatal）
- [x] Step 5': fcntl64 F_DUPFD/F_DUPFD_CLOEXEC（f17448d3，实测屏障 5：
      passthrough 丢第三参→EPERM→fdopen exit 204）
- [x] Step 6': dup3 handler（fa18c8dd，实测屏障 6：aarch64 无 dup2，
      glibc dup2→dup3 fatal；-f no + se_sve.py 4CPU 后 worker 线程栈
      分配走通，推进至 perf_event_open fatal）
- [x] Step 7: 回归 sve2_fmmla_dual --sve_vl 4：SDCSHIELD_FAILS=0，
      checksum ef163d9b7a71160c 与 Task 4 逐位一致；injector 76 类在位 +
      anchor1 reg_chain golden 精确匹配（anchor3 探针二进制缺失为
      2026-10-13 /tmp 历史产物，与 Task 4 基线一致，非本次回归）
- [ ] **时间盒跳闸（6 stub 用尽，未达 exit: pass）——STOP，链况交人工**：
      - -f no 剩余链：perf_event_open #241（ENOSYS 即触发框架
        effective_cpu_freq.hpp 自有 UINT64_MAX→NaN fallback）→ fdatasync
        #83（x86-64 上游先例 ignoreFunc）→ 可能的后续小项。约 2 个 stub。
      - 默认 fork 模式剩余链：eventfd2 #19 → waitid(P_PIDFD) →
        CLONE_PIDFD+pidfd FDEntry+BasicSignal 带退出码 → pollFunc 负 fd
        断言（server_debug_socket=-1）→ fdatasync。约 5 个 stub。
      - 结构性约束（上游限制）：SE 无异步信号投递（forkfd SIGCHLD 兜底
        不可行）；mmap 共享区不跨 fork 传播（fork 模式逐线程明细降级，
        判定仍经退出码完整传递）。

## 附记（执行事实）

- 并行会话于 070f0451 后将共享 checkout 切至 feat/sve-oob-audit-dual-
  2026-10-29；fcntl64 一度提交到该分支（5fe0d5c1），已 cherry-pick 回本
  分支（f17448d3）并推送；对端分支留有该 commit（其文件与本链不相交）。
- 产物二进制经 6 stub 链构建，CHAOS/gem5/build/ARM/gem5.opt md5
  450010ff4a314019fbb8377ca80653f3。
- se_sve.py 多 CPU（4×AtomicSimpleCPU 同 VL，单 Process 挂全 CPU 的
  上游 se.py SMP 模式）在 sdcshield-main 仓提交，非 gem5 stub。
