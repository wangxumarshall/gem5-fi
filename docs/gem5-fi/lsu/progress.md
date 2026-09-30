# Progress Log

## 更新要求

- 活跃执行期间至少每 30 分钟更新一次。
- 阶段开始/结束、任务提交/完成、错误、重试、暂停、恢复和用户决定后立即更新。
- 只记录已实际发生的动作，不把计划写成已完成事实。
- 每次更新必须写明证据路径和唯一下一动作。

## Current Status

- **Current Phase:** P3（前三单元连续 pilot 波次，用户指令 2026-09-29 晚）
- **Phase Status:** IN_PROGRESS
- **Overall Status:** IN_PROGRESS
- **Started:** 2026-09-29 11:22 (Session 001)
- **Last Updated:** 2026-09-30 14:18（监控周期 #40：例行——AGU 8 终态（C5/B3），ITEM-009(A02-F2-W3) s55/300 act=0 持续（F2 短流预期 BLOCKED，预计 ~19:30 达上限）；波次存活，资源 NORMAL，无新终态）
- **Current Owner:** 服务器执行 AI（Claude，主协调 AI）
- **Current Checklist Item:** AGU ITEM-002（A01-F0-W9）运行中；ITEM-001 已 COMPLETE（1/31）
- **Current RunID:** A01-F0-W9
- **Excel Location:** 7.展开执行矩阵!A2:AQ2（行 2）
- **Current Experiment Stage:** pilot（正式，30 activated/ITEM，attempted 上限 300）
- **Resource Safety State:** NORMAL（守卫 experiment 锁串行 + 60s 采样）
- **Build Concurrency Limit:** 8（同一时刻最多一个编译任务，经 lsu_guard 强制）
- **Experiment Concurrency Limit:** 4（硬上限；资源压力或 WARNING 可降 3/2/1，恢复后回 4，不得超 4；2026-09-30 14:30 用户指令）
- **Active Heavy Task:** P3 pilot 波次 2（AGU ITEM-002 断点续跑起，WAVE2_PID 81524，bash nohup 串行 AGU→L1d-TLB→Load Queue；F-018 修复后 -u 无缓冲日志）
- **Active PID/PGID:** 81524（bash 链）/ unit_pilot 子进程逐 run 经守卫
- **Resource Lock:** 已占用（runs/lsu/guard/build.lock：P1-G0-01 构建，pid 19587）
- **Resource Log:** runs/lsu/guard/build_p1_rebuild_rsrc.log（60s 采样进行中）+ guard_events.log
- **Latest MemAvailable / SwapFree / Load:** 27.18 GiB / 15.59 GiB / 低，blocked=0（2026-09-29 18:42 pilot 采样，无 WARNING/TRIP）
- **Next Step:** 停机点（用户连续模式指令 §7/§8）：基础环境建设完成——等待用户确认后再提交首个正式 pilot 样本（预计 ITEM-001/A01-F0-W3）。剩余工程：17 缺口注入器补实现（13 C++ 模式/钩子 + 3 多核 FS，每单元 one-patch-per-unit：改码→守卫 -j8 重建→定向验证→commit，约 1-2 小时/单元）；DR-001/DR-002 裁决待用户。

## Git 状态

- **最新 commit SHA:** f54d22fd（[LSU][P1] runner 契约端到端验证 + SE 越界结局口径发现（F-016），17:44 推送 d74f01d1..f54d22fd）。连续模式会话累计 7 个 commit：b6445581（P0）→ ee77b992（重建+冒烟+seed+映射）→ e83d0695（A01 确定性）→ ed6323e6（五家族+F0 两遍法）→ 989f7853（GOLDEN3+env lock）→ d74f01d1（armtlb FS+G0-06）→ f54d22fd（runner 契约）
- **推送状态:** 已推送 origin/fi-ding（最新 ee77b992；上一 b6445581 = [LSU][P0] 17 文件 15:10:20）
- **提交信息:** [LSU][P0] 预检完成：清单核验、环境资产盘点、B0参数对照、资源守卫建立（G0-10 PASS）（17 文件，xlsx 识别为 100% rename）

## Phase Summary

| Phase | Status | Started | Completed | Evidence/Output |
|---|---|---|---|---|
| P0 环境与资产预检 | COMPLETE | 2026-09-29 11:22 | 2026-09-29 15:25 | evidence/P0/（verify_checklist.out、xlsx_param_baseline.out、guard_verify.out、g0_04_g0_05_check.md、rebuild_attempt2.log） |
| P1 环境/注入器/观测链 | PENDING | | | |
| P2 负载/golden/冒烟 | PENDING | | | |
| P3 全矩阵 Pilot | PENDING | | | |
| P4 正式筛查 | PENDING | | | |
| P5 主结果扩样 | PENDING | | | |
| P6 单因素敏感性 | PENDING | | | |
| P7 稳健性与复现 | PENDING | | | |
| P8 分析归档交付 | PENDING | | | |

## Session Log

### Session 001

- **Start:** 2026-09-29 11:22
- **End:**（进行中）
- **Phase:** P0
- **Actions:** ① Git 启动前检查（repo root / origin git@github.com:wangxumarshall/gem5-fi.git / 远端 fi-ding=3f67df4b=本地 HEAD=origin/fi-ding；工作树不干净但已在 fi-ding 分支，仅记录不动）；② 六文件读取 + 哈希校验（Excel 1f652936... ✓；清单 790d280d... ✓；HEAD 中 V2.0.xlsx blob 与工作树改名文件同哈希=纯改名）；③ 清单结构核验 C1-C7 全 PASS（325 ITEM 连续、325 唯一 RunID、64 唯一模型、Excel 行 2..326、频率/单元分布与头表一致、必填字段 0 缺失）；④ 环境盘点（openEuler 24.03 SP3、Kunpeng-920 126 核、29Gi RAM、/home 171G 可用、Python 3.11.6、GCC 12.3.1、SCons 4.5.2、swig 不存在、gem5-fs 3.0G 镜像在位）；⑤ 资产盘点（lsu_proxy.py + tools/lsu_*.py 等 LSU V1.0 轨道资产已在库；workloads/directed 83 项；W1 MiBench/W11 SPEC/W13 PARSEC 不存在）；⑥ lsu_proxy.py 冒烟失败（E-002：二进制缺 CHAOSPrefetch，根因=二进制 09-25 早于 LSU 源码 09-26 提交 46e912b5）；⑦ 修复 CHAOS/gem5/build 断链（E-001）；⑧ 启动 scons -j126 增量构建（尝试2）→ cc1plus 多路被 SIGKILL、6 个 .py.pyo 目标 Error 1（E-003；findings.md 记载该事故曾致服务器 94% 内存+swap 耗尽重启）；⑨ 会话恢复：重读五文件（总方针新增 §8 资源硬限制），确认无编译/gem5 残留进程，资源状态 NORMAL；Excel 参数基线表（2.LSU参数基线 B0 19 参数+S1-S4 敏感性配置）已转录。
- **Results:** P0 清单项完成 7/11（六文件读取✓、哈希✓、清单核验✓、环境盘点✓、进程核查✓、gem5 状态✓、资产盘点✓）；待办：资源守卫建立+验证、G0-01..G0-10 填写、Decision Requests。
- **Evidence:** docs/gem5-fi/lsu/evidence/P0/{verify_checklist.py,verify_checklist.out,xlsx_dump.py,xlsx_sheets.out,xlsx_param_baseline.out,rebuild_attempt2.log}
- **Errors:** E-001（构建断链，已修复）、E-002（lsu_proxy ImportError，待重建二进制）、E-003（-j126 构建 OOM 失败，被 G0-10 门禁阻塞，详见 Errors and Retries）
- **Next Step:** 建立资源守卫脚本并验证（G0-10），随后填写 G0 门禁 + Decision Requests，提交 [LSU][P0] commit。

## Active Work

| Work ID | Checklist ITEM | RunID | Excel行 | 实验阶段/动作 | 状态 | 开始 | 最近更新 | 输出/证据 |
|---|---|---|---|---|---|---|---|---|

## Checklist Status Summary

| Stage | PENDING | RUNNING | COMPLETE | BLOCKED | INVALID | UNSELECTED/NA | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Engineering | 325 | 0 | 0 | 0 | 0 | 0 | 325 |
| Pilot | 325 | 0 | 0 | 0 | 0 | 0 | 325 |
| Screening | 325 | 0 | 0 | 0 | 0 | 0 | 325 |
| Confirmatory/Sensitivity/Reproduction | 0 | 0 | 0 | 0 | 0 | 325 | 325 |

## Test and Gate Results

| Test/Gate | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| 六个输入文件可读 | 全部可读 | 5 个 md 可读 + xlsx 为改名文件（HEAD blob 同哈希） | PASS | sha256sum 输出；findings.md |
| 完整清单规模 | 64模型、325 ITEM、325唯一RunID | 325 ITEM 连续无重复 / 325 唯一 RunID / 64 唯一模型 / Excel 行 2..326 一一映射；C1-C7 全 PASS | PASS | evidence/P0/verify_checklist.out |
| 清单与Excel来源 | Excel SHA-256匹配 | 清单 790d280d... ✓ Excel 1f652936... ✓ | PASS | sha256sum；evidence/P0/verify_checklist.out |
| 服务器环境盘点 | 完整 | openEuler 24.03 SP3 / Kunpeng-920 126核 / 29Gi RAM / 171G 磁盘可用 / Python 3.11.6 / GCC 12.3.1 / SCons 4.5.2 / swig 不存在 / gem5-fs 3.0G | PASS | findings.md Server Environment Findings |
| G0-01 至 G0-09 | 均有状态与证据 | 已填写：G0-01 FAIL（二进制过期+重建失败）、G0-02 UNCHECKED、G0-03 PARTIAL、G0-04 PASS-静态（19/19）、G0-05 IN_PROGRESS（DR-001）、G0-06/07/08/09 UNCHECKED | DONE（如实记录） | task_plan.md 门禁表；findings.md Gate Findings |
| G0-10 资源防护 | 编译≤8且单实例；实验默认1；锁、PID/PGID、60秒监控和熔断可验证 | tools/lsu_guard.py 建立，T1–T7 全 PASS（含并发重复启动拒绝、陈旧锁处置、run 全生命周期、采样与 release） | PASS | evidence/P0/guard_verify.out、guard_verify.sh、guard_verify_t7.log |

## Resource Safety Status

| 时间 | 状态 | MemAvailable | SwapFree | Load 1/5/15 | blocked | 重任务 owner/PID/PGID | 锁 | 动作/证据 |
|---|---|---:|---:|---|---:|---|---|---|
| 2026-09-29 12:05 | NORMAL | 28.4 GiB | 16.3 GiB | 0.26/0.09/0.07 | 0 | 无（ps 全查：无 scons/gcc/cc1plus/gem5） | 无（守卫待建） | 会话恢复后首次采样；构建尝试2已失败终止 |
| 2026-09-29 14:53–15:00 | NORMAL | 27.1 GiB | 15.6 GiB | 0.2/0.24/0.18 | 0 | 守卫验证 T7（sleep 8，pgid 16006） | build.lock（验证用，已正常释放） | G0-10 验证：T1–T7 全 PASS（evidence/P0/guard_verify.out） |
| 2026-09-29 15:25 | NORMAL | ~27 GiB | ~15.6 GiB | 低 | 0 | 无（守卫验证完成，锁已释放） | 无 | P0 收尾：G0 门禁填写完毕，准备 [LSU][P0] 提交 |
| 2026-09-29 15:12–15:42 | NORMAL | 23.4–24.3 GiB | 15.59 GiB | 8.2/7.9/5.3 | 0 | P1-G0-01 构建 sdc/19587/19587 | build.lock（守卫采样 60s） | -j8 增量重建成功（27 分钟，零警告，scons done）；随后冒烟 experiment 槽 sdc/34025/34025 exit 0；全程无 WARNING/TRIP |
| 2026-09-29 15:41 | NORMAL | ~25 GiB（构建释放后） | 15.59 GiB | 回落 | 0 | 冒烟 lsu_proxy hello（34025，已完成） | experiment.lock（已释放） | E-002 修复验证 PASS；B0 参数运行时打印与 Excel 一致 |
| 2026-09-29 15:58–16:00 | NORMAL | 充足（gate 两次 PASS） | 15.59 GiB | 低 | 0 | DET 双跑：run1(38091)→run2(38469) 严格串行 | experiment.lock（逐次获取/释放） | A01-F0-W3 确定性 PASS（C1-C5）；采样 runs/lsu/guard/det_a01_run{1,2}_rsrc.log |

## Errors and Retries

| Error ID | 时间 | 范围 | 错误签名 | Attempt | 改变的策略 | Resolution/Decision Request | Evidence |
|---|---|---|---|---|---|---|---|
| E-001 | 2026-09-29 11:42 | gem5 构建 | scons configure ENOENT：CHAOS/gem5/build/{ARM,build} 绝对符号链接指向不存在的 /home/sdc/gem5-fi（仓库改名残留） | 1 | 修复：ln -sfn 重新指向 /home/sdc/gem5-fi-ding | RESOLVED（readlink 验证通过） | rebuild_attempt2.log 头部 Mkdir 失败栈 |
| E-002 | 2026-09-29 11:40 | lsu_proxy.py 冒烟 | ImportError: cannot import name 'CHAOSPrefetch' from 'm5.objects'（gem5.opt 09-25 构建，早于 LSU 注入器源码提交 46e912b5 09-26） | 2 | 根因=二进制过期 → 守卫 -j8 重建（E-003 处置）后复测 | RESOLVED（2026-09-29 15:41：重建成功后冒烟 exit 0，"Hello, AArch64 CHAOS!"，CHAOSPrefetch 导入正常；evidence/P1/smoke_hello.out） | /tmp/p0_smoke_hello（失败）；evidence/P1/smoke_hello.out（成功） |
| E-003 | 2026-09-29 11:48 起 | gem5 构建 | scons -j126：多个 cc1plus 被 SIGKILL、6 个 .py.pyo 目标 Error 1；findings.md 记载该事故曾致服务器内存 94%+swap 耗尽并重启 | 2 | 违反总方针 §8.1（-j8 硬上限）；第 3 次尝试必须 -j8 单实例+锁+60秒监控 | BLOCKED on G0-10：守卫验证通过后以 -j8 重启构建 | evidence/P0/rebuild_attempt2.log（331 行，6 个 scons error） |

## Periodic Update Template

```text
时间：
当前阶段/状态：
当前Checklist Item / RunID / Excel行：
当前实验阶段：
过去30分钟完成：
运行中任务：
新增发现：
错误/重试：
资源状态：
资源安全状态（NORMAL/WARNING/TRIP/BLOCKED）：
MemAvailable / SwapFree / Load / blocked：
活动重任务 owner / PID / PGID / 锁 / 日志：
门禁变化：
唯一下一动作：
证据路径：
```
