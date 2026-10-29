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

## Ruling F 扩展（+2 stub，2026-10-29 控制器裁定）

- [x] Stub 7（5f623ce6）: perf_event_open → 挂上游 ignoreWithEnosysFunc
  （warn+-ENOSYS）——框架 effective_cpu_freq.hpp:163-167 自有
  UINT64_MAX→NaN fallback 吸收。spike：perf fatal 消失，**第一个测试
  完整跑完**，推进至 clock_nanosleep fatal。
- [x] Stub 8（f0298c92）: fdatasync → ignoreFunc（上游 x86-64 同款
  syscall_tbl64.cc:128）。激活点（每测试 logging_flush）位于新屏障
  之后，无回归实证。
- [ ] **仍未达 exit: pass——新屏障 clock_nanosleep (#115)，按裁定 STOP
  （no third stub），BLOCKED 上报**：
  - 调用链已完全定位（gem5 --debug-flags=Exec + 符号化 + 宿主 gdb
    对照）：worker 线程 `test_loop_condition+12`（sandstone_run.cpp:626
    内联进测试体）读 shmem `current_test_sleep_duration` 得 **104µs**
    （应为 0）→ 门通过 → `usleep(104/8192)` = `usleep(0)` → glibc
    nanosleep→clock_nanosleep({0,0}) fatal。宿主同二进制 gdb 实测仅
    2 次 clock_nanosleep（均为 main 的 wait_delay_between_tests），
    worker 路径 0 次——即 shmem 该字段在 gem5 内被污染为非零。
  - 修复路径（下一裁定）：挂 clock_nanosleep（ignoreFunc 即可，
    {0,0} 睡眠本意即让出）；104µs 来源需 guest watchpoint 定位——
    候选：mprotect 被忽略→框架线程栈 PROT_NONE 护栏未生效→潜在
    越界写静默落 shmem（native 会 SIGSEGV 的写法在 gem5 里无声）。
    该污染经 N=8192 除法后为 0µs 无害，但**若确系静默越界写，对
    Task 6/7 证据有效性是实质风险**，必须查清。
  - 单位澄清：gem5 全局 tick 为 1THz(1ps)，tick 407169250000 =
    **407ms** 模拟时间（非 407s）——测试 500ms 预算近尾声时触发；
    客户时钟无问题（探针实证 syscall 时钟随模拟时间正确推进）。
- [x] 回归（8-stub 终版二进制 b1f671db…）：sve2_fmmla_dual --sve_vl 4
  SDCSHIELD_FAILS=0，checksum ef163d9b7a71160c 与 Task 4 逐位一致；
  injector 76 类 + anchor1 golden 精确匹配（anchor3 探针缺失为既有
  基线）。
- HEAD：0169ef04 → **f0298c92**（已推送）。

## Ruling H 裁定（2026-10-29 晚）：104µs 根因 + 第 9 个 stub → exit: pass

### Phase 1 根因（三重实证，全部真实输出）

1. **框架源**：字段有 NSDMI `= {}`（sandstone_p.h:429），init_shmem 的
   placement-new（sandstone.cpp:355）确会写入 0——但 **commit_shmem
   （sandstone.cpp:360）随后 munmap+重映射同一 tmpfile fd**（Linux 下
   MAP_SHARED 文件持久性保住内容；框架自身在 attach_shmem_internal 用
   assert 防线校验 thread_data_offset/main_thread_count，release 构建
   NDEBUG 将其编译掉）。
2. **gem5 探针**（/tmp/t5_shmem_probe，native 与 gem5 对照）：
   - native: `pattern_survived=YES sleep_field=0`（文件内容跨重映射存活）
   - gem5:   `pattern_survived=NO` byte0=00（重映射页为零填充**新页**，
     非陈旧垃圾；匿名页零填充 sum=0 ✓）
3. **syscall 追踪**：init_shmem 映射 4KB@0x3fff902000(tick 3.67ms) →
   munmap(0x3fff902000,4096)(tick 5.1838e9) → 重映射 12KB@**0x3fff8ff000
   (不同地址)**——旧映射（含 placement-new 零值）被弃，新页全零。

**机制链**：重映射后 thread_data_offset=0 → attach_shmem_internal 以
0 计算每线程数据指针（assert 已被 NDEBUG 关掉）→ PerThreadData 叠印
在 SharedMemory 结构体上 → 一个 per-thread 字段值（量级=log_fd≈104）
落在 +0x2c 即 current_test_sleep_duration → 104µs。旁证：gem5 内 -v
的 verbosity（存 shmem cfg）同样丢失 → per-test yaml 块被抑制（native
-v 两测试 result: pass 均打印）。

**判定：gem5 mmap 语义差异（MAP_SHARED 无跨 munmap 持久性，上游
warn_once 已文档化）× 框架 Linux 合法模式——非测试/框架越界写**。
SVE 计算与 golden memcmp（堆）不受影响；判定路径自洽（写读同址）。

### Phase 2（benign 分支）：Stub 9（55d92b63）

clock_nanosleep #115 → ignoreWarnOnceFunc，严格循树内 sleep 类先例
（x86-64 {35,"nanosleep",ignoreWarnOnceFunc} syscall_tbl64.cc:88、
riscv:634、ARM32:338 同款）。时序语义：睡眠零时长、不推进模拟时间；
-t 时长由 clock_gettime deadline 驱动不受影响；间歇延迟坍缩为 0。

### 结果

- [x] **spike `exit: pass` / `Simulated exit code: 0 @ tick 407370811000`
  （-f no，--vl 4=512-bit，真二进制）**；-v 复跑同样 exit: pass
  （tick 407373415000）。native 同参 -v 交叉：两测试（sve_rot_ldr_at_top
  + mce_check）均 result: pass。
- [x] 回归（9-stub 二进制 3f9011f4…）：sve2_fmmla_dual --sve_vl 4
  SDCSHIELD_FAILS=0，checksum ef163d9b7a71160c 与 Task 4 逐位一致；
  injector 76 类 + anchor1 golden 精确匹配（anchor3 既有探针缺失）。
- [x] HEAD：635a6631 → **55d92b63**。
- 残余风险（如实）：gem5 nofork 下 per-thread 数据区与结构体叠印，
  pass 判定自洽可信，但失败归因/明细有理论性掩蔽风险；Task 6 建议
  每测试单进程调用 + 以进程退出码与 exit: 行为准。
- 标定数据（Task 6 输入）：整 run ≈ 0.407 模拟秒（1THz tick），
  wall ≈ 9-10 分钟/测试。
