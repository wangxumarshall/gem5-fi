# Progress Log

## 更新要求

- 活跃执行期间至少每 30 分钟更新一次；阶段/ITEM/长任务/错误/重试/资源状态变化时立即更新。
- 只记录已实际发生的动作；所有完成声明附证据路径。
- 每次更新写明当前 ITEM、RunID、Excel 行、campaign/phase、资源状态和唯一下一动作。

## Current Status

- **Current Phase:** P0
- **Phase Status:** IN_PROGRESS
- **Overall Status:** IN_PROGRESS
- **Started / Last Updated / Owner:** 2026-09-30 16:30+08:00 / 2026-10-08 11:15+08:00 / 服务器 AI（Claude @ NSCC login01, reach nscc）
- **Current Checklist Item / RunID / Excel Location:** NONE / NONE / NONE
- **Current Experiment Stage:** P0 工程收口完成（G0 填表 + Unit3 提交）；P1 待启动
- **Campaign:** NONE（P0 无实验；工程 campaign 待 P2 冒烟建立）
- **Completed ITEM Stages:** 0
- **Resource Safety State:** NORMAL（无活跃编译/实验进程；4 实验槽位全空——2026-10-08 guard status 实测；login01 无 swap 属主机配置，F-005）
- **Build Limit:** `-j8`，全局单实例
- **Experiment Concurrency Limit:** 4（资源不足时降为3/2/1，不得超过4）
- **Active Heavy Task / PID / PGID / Lock / Resource Log:** NONE（gem5 clean build 已于 09-30 18:13 COMPLETE：SCONS RC=0，见 `runs/ooo-node/logs/gem5-build-001.out`）；节点占用 job 1773145 @ cn22986（holder.sh，心跳 `runs/ooo-node/state/heartbeat`，60s 资源采样 `runs/ooo-node/state/resources.log`；**到期 2026-10-10 16:54:45，须提前提交续占作业**）
- **Latest MemAvailable / SwapFree / Load / blocked:** login01（2026-10-08 重连实测）: ~306GiB MemAvailable / 0 swap / 负载正常；cn22986: 见 runs/ooo-node/state/resources.log
- **Checklist SHA-256:** `f520d42a53ae2e44e76af5771dd1bcbdb9545082458e7996b1d306f1bbc30c91`（2026-10-08 重连复验一致）；Excel `b73b6304005e507f5e8a1f41f0fc979f3d6439e6dda875ec4d2be961b867ae75`（同）
- **Next Step:** ①✅Unit3 提交+推送（362e01c3，远程 9d32d412→362e01c3 实证）；②✅W1 tarball+PROVENANCE 上传校验一致（sha256 7bc51c7d…/43e555e3…，login01 构建=W1 单元属 P2）；③✅holder 续占 1823682 PENDING（-nl cn22986，10-10 到期自动接续，-T 864000）；④✅P1 计划落盘 docs/superpowers/plans/2026-10-08-ooo-p1-injectors-observation-campaign.md（14 单元 U0–U12+U1b）；⑤执行 P1：U0 文档桥接 → U1 映射表 → U1b guard_pid 移植 → U2 起。

## Phase Summary

| Phase | Status | Started | Completed | Evidence/Output |
|---|---|---|---|---|
| P0 环境/输入/恢复预检 | COMPLETED（工程收口） | 2026-09-30 | 2026-10-08 | Units 1–3 提交（guard/recover/文档）；`gem5-build-001.out`（SCONS RC=0）；冒烟 ×2 FINAL=45737cc9a76c0dce；G0 表已填（G0-01/03/10 PASS，05/07/08 PARTIAL，02/04/09 →P1，06 →DR-002）；DR-001/DR-002 OPEN |
| P1 注入器/观测链 | PENDING | | | |
| P2 负载/golden/冒烟 | PENDING | | | |
| P3 全矩阵 Pilot | PENDING | | | |
| P4 正式筛查 | PENDING | | | |
| P5 确认性扩样 | PENDING | | | |
| P6 单因素敏感性 | PENDING | | | |
| P7 稳健性与复现 | PENDING | | | |
| P8 分析归档交付 | PENDING | | | |

## Session Log

### Session 001

- **Start:** 2026-09-30 16:30+08:00（/goal 下达；10 天长时任务）
- **Phase:** P0
- **Actions:**
  1. 启动前检查：repo gem5-fi-wx-paper @ fi-ding 8b659ced 工作树 clean；login01 无遗留 gem5/实验进程；按用户指令创建 git worktree `/home/share/suke/wangxu/gem5-fi-ooo`（branch ooo-exec @ 8b659ced）。
  2. 计划核验：5 个 Markdown 读取；完整清单 SHA-256 `f520d42a…30c91` 与 Excel SHA-256 `b73b630…7ae75` 均已核验一致；310 ITEM/310 唯一 RunID/57 模型结构核验通过。
  3. 节点占用（正序遍历规则下的可调度实现）：q_Test_20260903 仅 cn23154（外部作业占用至 ~10-02）；q_hpcapp 睡眠节点不调度 → 不带 -nl 提交 608 副本全节点作业 → **job 1773145 RUNNING @ cn22986**（-T 864000），holder.sh 心跳+60s 资源采样落盘 NFS；废弃 PENDING 作业 1773108/1773126/1773143 已 dkill。
  4. 二进制兼容性：预置 build/ARM/gem5.opt（源自 sdc 机 /home/sdc/gem5-fi-lsu，16:26 拷入）需 GLIBC_2.38+libpython3.11，login01（glibc 2.28）与节点（glibc 2.34）均无法运行 → 判定必须本集群重建（findings F-002）。
  5. 工具链落位：login01 有 g++ 10.3.1/python3.9.9+headers/libpython3.9.so，但无 scons、无系统 protobuf；无外网（DNS 失败）。protobuf 27.2.0（bisheng 构建，静态库+protoc+abseil）发现于 `/work_ssd/software/soft/app/protobuf/27.2-hpckit25.1.0.SPC001-bisheng4.2.0.2.B002`；SCons 4.11.1 wheel 经本地 Windows（有外网）下载→`reach fs write` 推送→SHA256 校验一致（`454cef36…4f95c8d11d`）→`pip3 install --user` 成功（findings F-003/F-004）。
  6. gem5 clean build 启动（17:17）：worktree ooo-exec @ 8b659ced（dirty=0），`scons -j8 build/ARM/gem5.opt`，flock 单实例锁，nice -n 10，日志 `runs/ooo-node/logs/gem5-build-001.out`；configure 阶段通过（含 "GCC 10.3.1 not officially supported" 警告，非失败，持续观察）。
- **Results / Evidence / Errors:** build RUNNING（证据：日志持续增长，scons PID 2816362 存活）；无 BLOCKED；错误 0。
- **Next Step:** build 完成→G0-01 证据固化；P0 剩余预检（锁/lease/守卫实测、负载盘点、G0 填表）→ [OOO][P0] commit+push。

### Session 002（跨 2 个日历段：09-30 18:13 断连 + 10-08 10:44 重连）

- **Start:** 2026-09-30 18:13 – 2026-10-08 11:15+08:00（含 7.3 天 VPN 断连期，F-009）
- **Phase:** P0（收口）
- **Actions:**
  1. **断连期（Windows 侧离线预备）**：reach/SSH 因 SSL VPN（Topsec NGVONE）OTP 断连不可达（F-009）；期间完成：①W1 MiBench 子集供给（embecosm/mibench@0f3cbcf6 定向 9 程序目录 tarball 2.62MB，sha256 7bc51c7d…，PROVENANCE 记录源/许可/构建约定）；②P1 13 单元计划草稿（U0 文档桥接→U11 campaign 引擎→U12 收口）；③G0 填表草稿；④RECONNECT-RUNBOOK.md 重连对账手册；⑤cron 自动探测通道恢复。
  2. **重连对账（10-08 10:44–11:00）**：清单/Excel SHA-256 复验一致；worktree git 状态符合预期（HEAD=ce8d6d8a + Unit3 文档 WIP）；主树 LSU 轨道并行推进至 d2b7e885（未触碰）；holder job 1773145 RUNNING @ cn22986；build 产物 COMPLETE（SCONS RC=0，gem5.opt sha256 9ef9c3b4…，1,252,069,576B）。
  3. **G0-01 运行时兼容性判定（F-008）**：login01 原生构建链系统 libpython3.9 → gem5 v25.1 stdlib PEP 604 TypeError（RC=1 实测）；预置 sdc 构建（63f50c40…）经 LSU 兼容运行时（lsu_keeper/compat）可运行；两树 CHAOS/gem5/src diff=0（二进制源等价）；worktree 仓根 build/ARM/gem5.opt 硬链接采用（同 inode）；**冒烟 ×2**（ooo_proxy.py + smoke，--cpu O3）：FINAL=45737cc9a76c0dce RC=0，golden 匹配。
  4. **G0-10 run 全路径实测**：`ooo_guard.py run --type experiment -- sha256sum build/ARM/gem5.opt` → SPAWNED pid=2909412 pgid=2909412 slot=0 → run-finish exit_code=0 target-exited → 4 槽位全释放（status 实测）。
  5. **G0 填表**：task_plan.md G0-01..G0-10 全部填写（PASS×3 / PARTIAL×3 / PENDING→P1×3 / PENDING→DR×1）；findings.md Gate Findings 同步；F-002 修订（clean rebuild 结论作废）+ F-007 通道实证更新 + F-008/F-009 新增；DR-001（W1 供给，方案A 自主推进）/DR-002（FS vs SE，推荐 SE 基线）记录。
  6. **Unit 3 提交**：[OOO][P0] Unit3 文档收口（本提交），bundle 通道推送。
- **Results / Evidence / Errors:** 冒烟证据 /tmp/ooo-smoke-00{2,3,4}.log；guard runpath /tmp/ooo-guard-runpath.log + status 输出；无 BLOCKED；错误 0（F-008 属判定性发现而非错误）。
- **Next Step:** W1 上传+构建（DR-001）；holder 续占（10-10 16:54 到期前）；P1 计划落盘并启动 U0/U1。

## Active Work

| Work ID | ITEM | RunID | Excel行 | campaign/phase | sample_index/seed | 状态 | owner/PID/PGID/锁 | 心跳 | 输出/证据 |
|---|---|---|---|---|---|---|---|---|---|

## Checklist Status Summary

| Stage | PENDING | RUNNING | COMPLETE | BLOCKED | INVALID | NA/UNSELECTED | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Engineering | 310 | 0 | 0 | 0 | 0 | 0 | 310 |
| Pilot | 310 | 0 | 0 | 0 | 0 | 0 | 310 |
| Screening | 310 | 0 | 0 | 0 | 0 | 0 | 310 |
| Confirmatory/Sensitivity/Reproduction | 0 | 0 | 0 | 0 | 0 | 310 | 310 |

## Test and Gate Results

| Test/Gate | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| 六个输入文件可读 | 全部可读 | 未检查 | UNCHECKED | |
| 清单规模 | 57模型、310 ITEM、310唯一RunID | 未检查 | UNCHECKED | |
| 清单哈希 | `f520d42a53ae2e44e76af5771dd1bcbdb9545082458e7996b1d306f1bbc30c91` | 未检查 | UNCHECKED | |
| Excel哈希 | 与总方针一致 | 未检查 | UNCHECKED | |
| G0-01 至 G0-09 | 均有状态与证据 | 未检查 | UNCHECKED | |
| G0-10 | 编译锁、实验worker lease、实验并发≤4、资源守卫、60秒监控、30分钟心跳、恢复扫描可验证 | 未检查 | UNCHECKED | |

## Resource Safety Status

| 时间 | 状态 | MemAvailable | SwapFree | Load 1/5/15 | blocked | 磁盘 | owner/PID/PGID | 锁 | 动作/证据 |
|---|---|---:|---:|---|---:|---:|---|---|---|
| 2026-09-30 17:17 | NORMAL（build 启动） | 290690MiB | 0MiB（login01 无 swap，主机配置） | 7.29/8.04/8.04 | 未采样 | /home/share 999T 可用 | suke/2816362/2815276 | runs/ooo-node/state/gem5-build.lock | build-gem5.sh：-j8 单实例 flock，日志 gem5-build-001.out |

## Errors and Retries

| Error ID | 时间 | ITEM/RunID | 错误签名 | Attempt | 改变的策略 | Resolution/Decision Request | Evidence |
|---|---|---|---|---:|---|---|---|

## Periodic Update Template

```text
时间：
当前阶段/状态：
当前 ITEM / RunID / Excel行：
campaign / phase / sample_index / seed：
过去30分钟完成：
运行中任务与最近心跳：
错误/重试/BLOCKED：
资源状态（NORMAL/WARNING/TRIP/BLOCKED）：
MemAvailable / SwapFree / Load / blocked / 磁盘：
owner / PID / PGID / 锁 / 日志：
门禁变化：
唯一下一动作：
证据路径：
```
