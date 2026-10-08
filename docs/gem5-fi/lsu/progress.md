# Progress Log

## 更新要求

- 活跃执行期间至少每 30 分钟更新一次。
- 阶段开始/结束、任务提交/完成、错误、重试、暂停、恢复和用户决定后立即更新。
- 只记录已实际发生的动作，不把计划写成已完成事实。
- 每次更新必须写明证据路径和唯一下一动作。

## Current Status

- **Current Phase:** P3（前三单元连续 pilot 波次，用户指令 2026-09-29 晚）
- **Phase Status:** IN_PROGRESS
- **Overall Status:** IN_PROGRESS（**双平台局面待用户裁决**：旧机已恢复且 pilot 数据完好；集群 Session 002 停于 09-30 18:05；F-025 修复已 rebase 合并 F-027）
- **Started:** Session 001 2026-09-29 11:22（旧机）；Session 002 2026-09-30 16:43（集群 cn23423，最后更新 09-30 18:05）；Session 003 2026-10-08 09:49（旧机恢复）
- **Last Updated:** 2026-10-08 10:45（Session 003 融合合并：①**旧机实况推翻 F-028 预判**——旧机 10-03 16:32 重启后恢复，runs/lsu/pilot/ 数据完好（ITEM-009 有效前缀 115、ITEM-274 有效前缀 96，10-08 取证）；②**F-025 根因定论**（修正 Session 002 的"波次 4 死于宿主失联"记载）：波次 4 实际于失联前 16:14:55/16:36:27 两次因 gate"陈旧槽"误报竞态 fail-fast 自终止（锁内 pid 被 spawn 覆盖为 gem5 pid，正常收尾 0-60s 窗口被误判泄漏；零数据污染）；③F-025 修复（guard_pid 判定字段）隔离测试 T1-T4 全 PASS，rebase 到集群侧 F-027 swap_na 之上（guard 双语义合并：guard_pid 陈旧判定 + swap_na 门禁/熔断豁免）；④集群 Session 002 交付在库：compat 运行时（F-026）+ swap_na（F-027）；其波次从未启动、U3'（LSU_GEM5_BIN 接线）未做。**平台决策 DECISION REQUEST 待用户**）
- **Current Owner:** 服务器执行 AI（Claude，主协调 AI；Session 003，2026-10-08 09:49 起于旧机 localhost0101）
- **Current Checklist Item:** AGU ITEM-009（A02-F2-W3，旧机有效 s0–s114=115 runs 全 act=0，GUARD_FAILURE 非终态）→ 其后 ITEM-010..039；Load Queue ITEM-274（L01-F1-W5，旧机有效 s0–s95=96）→ ITEM-277+；ITEM-001..008 与 ITEM-271 有效终态不受影响（**在哪个平台续跑待用户裁决**）
- **Current RunID:** A02-F2-W3（中断于 s115——gate 误报，非数据问题）
- **Excel Location:** 7.展开执行矩阵!A11（行 11 = ITEM-009 待闭合）
- **Current Experiment Stage:** pilot（正式，30 activated/ITEM，attempted 上限 300）
- **Resource Safety State:** NORMAL（旧机无重任务、锁目录无锁文件；集群侧状态未知——Session 002 keeper 1773102 存活性待查）
- **Build Concurrency Limit:** 8（同一时刻最多一个编译任务，经 lsu_guard 强制）
- **Experiment Concurrency Limit:** 4（硬上限；2026-09-30 14:30 用户指令；F-022 Patch A/B + F-025 guard_pid + F-027 swap_na 均已合并）
- **Active Heavy Task:** 无（旧机波次 4 已于 09-30 16:36 自终止；集群波次从未启动）
- **Active PID/PGID:** 无（旧机）
- **Resource Lock:** 空闲（旧机 runs/lsu/guard/ 无锁文件）
- **Resource Log:** runs/lsu/guard/guard_events.log（旧机最后事件 09-30 16:36:27 s95 release；集群侧新起点）
- **Latest MemAvailable / SwapFree / Load:** 28.1 GiB / 16.3 GiB / 0.21，blocked=0（2026-10-08 09:5x 旧机采样，无 WARNING/TRIP；集群 cn23423 参考：526 GiB / 无 swap / 608 核，Session 002 17:47 采样）
- **Next Step:** ①完成 rebase 合并（progress 冲突融合 + push）；②向用户 DECISION REQUEST：pilot 续跑平台（旧机 resume 115+96 样本 vs 集群 s0 重跑+完成 U3' 接线）+ 双会话协调（Session 002 集群 keeper 状态）；③裁决前不启动任何波次（防双平台双跑同一矩阵）。

## Git 状态

- **最新 commit SHA:** 8b659ced（[OOO][docs] 添加服务器AI端到端执行文件，14:57——OoO 轨道提交）；LSU 轨道最新为 fb531323（[LSU][P3] 用户指令：实验并发硬上限调整为 4，14:34）
- **P3 pilot 会话提交链:** 27bf1e1b（ITEM-001）→ d5d00046（F-018 波次修复）→ 10f95e1b（ITEM-002）→ 05eda8d8（ITEM-003）→ 2eb464ac（ITEM-004）→ 9240a807（ITEM-005）→ 0442cfa0（ITEM-006，标签误标 A02 已由 874a6c76 更正）→ 784ef08b（ITEM-007，标签误标已更正）→ ba4fe2a9（ITEM-008）→ 874a6c76（F-021 更正）→ fb531323（F-022 并发指令）
- **推送状态:** 已推送 origin/fi-ding（本会话恢复时 HEAD=8b659ced 与远端一致）
- **注意:** ITEM-009..025 的 pilot 结果因 F-023 污染**不产生提交**（隔离后重跑）

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
| Pilot | 308 | 1（ITEM-009 续跑） | 5（ITEM-001/002/006/007/008） | 8（ITEM-003/004/005 真实 300/0 + ITEM-011/012 admission DR-002；**另 15 项 F-023 污染终态已作废**） | 0（污染 run 隔离中，不进统计） | 0 | 325 |
| Screening | 325 | 0 | 0 | 0 | 0 | 0 | 325 |
| Confirmatory/Sensitivity/Reproduction | 0 | 0 | 0 | 0 | 0 | 325 | 325 |

AGU pilot 细分（39 ITEM）：ELIGIBLE 28 / admission BLOCKED 11（ITEM-011/012 DR-002、ITEM-028..033 A07 缺口等）；已闭合有效终态 8（5 COMPLETE + 3 BLOCKED）；ITEM-009 集群重跑中（自 s0；旧机 76/300 有效现场丢失）；ITEM-010/013..025 因 F-023 污染待重跑；ITEM-026..039 未开始。


### Session 002（2026-09-30 16:43 起，集群 cn23423 / keeper 1773102）

- **背景：** 用户 /goal 十天长任务（占最空闲节点、dattach 执行、按清单推进直至完成）。
  正序从节点名最大值遍历：cn23423 为最大全空闲 OK 节点（q_Test 标签仅 cn23154 且被
  1766034 占用；q_hpcapp -R cpu=608,mem=440000MB 排他 -T 864000）。
- **16:43-17:30 完成：** ①gem5 兼容运行时（compat loader + sdc1→Windows→nscc 中继依赖库，
  修复悬空链接/PYTHONHOME 布局/OpenSSL3/tcmalloc，F-026）双端冒烟 PASS；②工具 py_compile
  全过（Python 3.9.9）；③guard status 节点运行正常；④发现全集群节点无 swap 门禁阻断
  （F-027）与 pilot 状态未迁移（F-028）；⑤引擎升级计划落盘
  docs/superpowers/plans/2026-09-30-lsu-cluster-engine-upgrade.md。
- **17:30-18:05 完成：** U1 swap_na（对当时单实例守卫）+ 双端验证 + 2 提交；推送时发现
  origin 已有旧会话失联前交付的 F-022 引擎升级 4 提交（Patch A/B 完整实现 4 槽位/并行/
  resume，evidence 齐全）→ 中继回集群 rebase 合并；U2/U4/U5 被其覆盖（计划改标
  superseded），U1 需移植到 4 槽守卫，U3/U6 仍需实施。
- **证据：** evidence/P3/u1_gate_{cn23423,login01}.out；/tmp/lsu_smoke_*（冒烟）；
  docs/gem5-fi/lsu/evidence/P3/f022_patch_{a,b}_test.txt（旧会话）。
- **错误/重试：** 中继 tar 悬空符号链接 3 例（补真实文件重传）；cn23423 缺
  libtcmalloc_minimal.so.4（login01 拷入 compat）；export LD_LIBRARY_PATH 污染系统工具
  （改用 loader --list 定向检查）。
- **唯一下一动作：** 将 swap_na 移植到 4 槽守卫（rebase 冲突解决中）并自验证。

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
| 2026-09-30 15:21–15:26 | NORMAL（事故期资源无压力） | 28.5 GiB | 16.3 GiB | 1.6–2.0 | 0 | F-023 空转期（无 gem5 实际运行）；15:26 TERM 波次 bash 81524/unit_pilot 81526 | experiment.lock 陈旧（15:33 已 clear-stale） | 事故不涉及资源越限——守卫中断是代码/流程缺陷非资源问题；guard_events gate 采样持续正常 |
| 2026-09-30 15:33 | NORMAL | ~28.5 GiB | 16.3 GiB | 低 | 0 | 无（波次停止，恢复准备中） | 空闲（陈旧锁已处置） | clear-stale pid 325615 确认死亡后清除；工具三件（guard/pilot/runner）与 HEAD 全等 |
| 2026-09-30 15:41–16:05 | NORMAL | 28.4 GiB（gate PASS） | 16.3 GiB | 0.16–0.28 | 0 | 波次 3（WAVE3 bash 352745，单实例引擎 F-023 加固版）；16:0x 停止，在飞 s19 独立跑完自释放 | experiment.lock 逐 run 获取/释放 | 停机切换窗口：Patch A/B 开发于 tools/draft/（隔离 LSU_GUARD_DIR 测试），波次运行期间 tools/ 零编辑（F-023 教训执行） |
| 2026-09-30 16:10–16:20 | NORMAL | 26.9 GiB（4 并发 gem5） | 16.3 GiB | 0.38 | 0 | 波次 4（WAVE4 bash 360275，--workers 4）：4 槽并行（s75-s78）+ 75 样本 resume | experiment_slot_{0..3}.lock 全占用（逐 run --slot+--confirm-pid 精确释放） | F-022 交付实机验证：MemAvail 26.9 GiB 远高于 WARNING 10 GiB；4×gem5 仅耗 ~1.5 GiB；G0-10 复验 PASS-4 槽口径（findings F-024） |

## Errors and Retries

| Error ID | 时间 | 范围 | 错误签名 | Attempt | 改变的策略 | Resolution/Decision Request | Evidence |
|---|---|---|---|---|---|---|---|
| E-001 | 2026-09-29 11:42 | gem5 构建 | scons configure ENOENT：CHAOS/gem5/build/{ARM,build} 绝对符号链接指向不存在的 /home/sdc/gem5-fi（仓库改名残留） | 1 | 修复：ln -sfn 重新指向 /home/sdc/gem5-fi-ding | RESOLVED（readlink 验证通过） | rebuild_attempt2.log 头部 Mkdir 失败栈 |
| E-002 | 2026-09-29 11:40 | lsu_proxy.py 冒烟 | ImportError: cannot import name 'CHAOSPrefetch' from 'm5.objects'（gem5.opt 09-25 构建，早于 LSU 注入器源码提交 46e912b5 09-26） | 2 | 根因=二进制过期 → 守卫 -j8 重建（E-003 处置）后复测 | RESOLVED（2026-09-29 15:41：重建成功后冒烟 exit 0，"Hello, AArch64 CHAOS!"，CHAOSPrefetch 导入正常；evidence/P1/smoke_hello.out） | /tmp/p0_smoke_hello（失败）；evidence/P1/smoke_hello.out（成功） |
| E-003 | 2026-09-29 11:48 起 | gem5 构建 | scons -j126：多个 cc1plus 被 SIGKILL、6 个 .py.pyo 目标 Error 1；findings.md 记载该事故曾致服务器内存 94%+swap 耗尽并重启 | 2 | 违反总方针 §8.1（-j8 硬上限）；第 3 次尝试必须 -j8 单实例+锁+60秒监控 | BLOCKED on G0-10：守卫验证通过后以 -j8 重启构建 | evidence/P0/rebuild_attempt2.log（331 行，6 个 scons error） |
| E-004 | 2026-09-30 14:37–15:26 | AGU pilot 波次 | F-023 守卫中断事故：guard 进程死亡未 release（陈旧锁）+ guard.py 被编辑为语法损坏 28 分钟 + 引擎忽略 guard 失败 → 约 2,670 个空转 run 被记为 attempted、9 个无效 result.json、5 个无效 census | 1 | 15:26 有序 TERM 波次链（bash 81524/unit_pilot 81526）；15:33 clear-stale 陈旧锁 | 处置中：污染数据隔离 quarantine_20260930_guard_outage/ → 引擎 fail-fast 加固 → 重启波次断点续跑（详见 findings F-023 与会话任务清单） | findings.md F-023；ITEM-009_s100/021_s0/018_s271_guard.out；guard_events.log |

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
