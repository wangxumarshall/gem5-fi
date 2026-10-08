# Progress Log

## 更新要求

- 活跃执行期间至少每 30 分钟更新一次。
- 阶段开始/结束、任务提交/完成、错误、重试、暂停、恢复和用户决定后立即更新。
- 只记录已实际发生的动作，不把计划写成已完成事实。
- 每次更新必须写明证据路径和唯一下一动作。

## Current Status

- **Current Phase:** P3（前三单元连续 pilot 波次，用户指令 2026-09-29 晚）
- **Phase Status:** IN_PROGRESS
- **Overall Status:** IN_PROGRESS（DR-003 裁决 A：旧机续跑 + 并发 4；波次 5 运行中；集群 Session 002 平台工程（U3b 二进制身份恢复），遵守 DR-003-A 不跑波次；F-025/F-027 已合并）
- **Started:** Session 001 2026-09-29 11:22（旧机）；Session 002 2026-09-30 16:43（集群 cn23423，持续运行——10-07/08 E-005 中断期转 Windows 取证，10-08 10:40 恢复直连）；Session 003 2026-10-08 09:49（旧机恢复）
- **Last Updated:** 2026-10-08 16:05（**两处报告更正 + 隔离迁移启动（用户指令，F-038）**：①task_plan 当前 P5 已是新版固定扩样规则（21 项名单已在全局实验口径冻结 + D-2026-10-08-采样）——上轮"待预登记"表述作废；②lsu_campaign.py 迁移在 tools/draft/ 隔离进行（MIGRATION_DESIGN.md：11 修改点 + 10 测试 + 6 应用条件），波次 5 运行期间不碰正式文件；波次 5 继续 4 并发（实时 s143+）。前记：**并发规则纠偏与采样政策迁移（用户指令）**：①当前并发硬上限再确认为 **4**（F-022 2026-09-30 批准覆盖总方针早期"画像后 2"通用规则；F-037）——波次 5 不中断不降级；②采样政策冻结：30 pilot（配置全不变计入累计）→ 全 RunID ≥385 → 仅 21 个重点 RunID 至 2401；删除 holdout/5000/n=500 检查点/半宽停止等序贯规则；Wilson 95%；eligible 分母口径确立；③静态文档已纠偏（总方针 §8.1/§8.5、findings 顶部、提示语并发节、本文件 P3=IN_PROGRESS）；④P4/P5 冻结前不启动；⑤实时核查：ITEM-020 s123、--workers 4、4 槽全占、MemAvail 26.23 GiB、gate/WARNING/TRIP 零新增。前记：**ITEM-018 COMPLETE + ITEM-019 COMPLETE（F-035）：A04 系列 6/6 整体闭合**（W3/W0 × F0/F2/F6 对称全谱）；**ITEM-019（A05-F0-W3）开张即真实五类**（M23+SDC3，79% 可分析；F-023 污染 census 重做成功）；ITEM-020（A05-F2-W3）运行中；gate ok:false 持续零新增（波次 5 累计 1850+ run）。前记：**ITEM-017（A04-F6-W3）COMPLETE 33/33 全 sim_fail**（F-034：F0/F2/F6 三档结局结构全谱——注入位置分布决定可分析性）；ITEM-018（A04-F6-W0）运行中（同模式）；gate ok:false 持续零新增（波次 5 累计 1700+ run）。前记：**ITEM-016（A04-F2-W0）BLOCKED 300/0**——F-020 模式第 6 例，守恒 OK；**ITEM-017（A04-F6-W3）运行中**（F6 确定性路径档，激活中 act=1，激活后 simulator_assert）；gate ok:false 持续零新增（波次 5 累计 1600+ run）；4 槽并行 MemAvail ~26.5 GiB。前记：**ITEM-015（A04-F2-W3）BLOCKED 300/0**——F-020 模式第 5 例（F2 短流结构性不可激活），守恒 OK；**ITEM-016（A04-F2-W0，mini_check）运行中**（act=0 起步，同预期）；gate ok:false 持续零新增（波次 5 累计 1100+ run）；4 槽并行 MemAvail 26.43 GiB。前记：ITEM-013/014（A04-F0-W3/W0）双双 COMPLETE：首批真实五类结局**（F-033）——ITEM-013 Masked 21+SDC 5+首个真实 Crash 1、ITEM-014 Masked 22+SDC 8（率 26.7%）；A01/A02/A04 可分析性梯度 0%→13%→85%+ 建立；ITEM-015（A04-F2-W3）运行中；gate ok:false 持续零新增（波次 5 已 500+ run）。前记：ITEM-010（A02-F2-W9）COMPLETE：33/33 activated 全 sim_fail 零可分析结局**（F-032，A01/A02 子模型对比数据点）；**ITEM-013（A04-F0-W3）运行中**（激活 + 真实架构级结局 Masked/Crash 混合，F-023 隔离的无效 census 已被正确重做）；gate ok:false 持续零新增；ITEM-009 已闭合 BLOCKED 300/0（F-031，resume 115 复用实战验证））
- **Excel Location:** 7.展开执行矩阵!A21（行 11-20 已闭合；行 21 = ITEM-020 运行中）
- **Current Owner:** 服务器执行 AI（Claude，主协调 AI；Session 003 旧机 localhost0101——波次 5 运行中；Session 002 集群 cn23423 keeper 1773102——平台工程（U3b CP4 重建编译中 → U3 → U6），不跑波次）
- **Current Checklist Item:** AGU ITEM-020（A05-F2-W3）运行中（F2 短流预期 BLOCKED）；已闭合：A01/A02/A04 三系列全部 + A05-F0-W3（真实五类）；其后 ITEM-021..039；Load Queue ITEM-274（有效 96）→ ITEM-277+
- **Current RunID:** A05-F2-W3（ITEM-020 运行中；A01/A02/A04/A05-F0 已闭合）
- **Current Experiment Stage:** pilot（正式，30 activated/ITEM，attempted 上限 300）
- **Resource Safety State:** NORMAL（旧机无重任务、锁目录无锁文件；集群侧 idle 无实验/编译任务（DR-003-A）——keeper 1773102 存活（11:09 djob 复核 RUNNING，10-10 16:43 到期，续期待办））
- **Build Concurrency Limit:** 8（同一时刻最多一个编译任务，经 lsu_guard 强制）
- **Experiment Concurrency Limit:** 4（硬上限；2026-09-30 14:30 用户指令；F-022 Patch A/B + F-025 guard_pid + F-027 swap_na 均已合并）
- **Active Heavy Task:** P3 pilot 波次 5（DR-003 裁决 A：旧机续跑；bash 链串行 AGU→L1d-TLB→Load Queue，--workers 4；AGU 自 ITEM-009 s115 续跑，115 个有效样本已 resume）
- **Active PID/PGID:** 654696（bash 链，WAVE5）/ 654698（AGU unit_pilot）/ 每 run 独立 guard 槽位进程
- **Resource Lock:** 4 槽位 experiment_slot_{0..3}.lock 逐 run 获取/精确释放（guard_pid 确认）
- **Resource Log:** runs/lsu/guard/guard_events.log（波次 5 运行中；gate ok:false 基线 5 次，10:51 复核零新增）
- **Latest MemAvailable / SwapFree / Load:** 28.1 GiB / 16.3 GiB / 0.21，blocked=0（2026-10-08 09:5x 旧机采样，无 WARNING/TRIP；集群 cn23423 参考：526 GiB / 无 swap / 608 核，Session 002 17:47 采样）
- **Next Step:** 波次 5 已启动并验证通过（10:49 WAVE5 bash 654696：**"resume: 115 valid samples reused"** + 4 槽并行 s123-s126 + MemAvailable 26.3 GiB + **gate ok:false 零新增（F-025 修复实机生效，12 run/3 轮槽位轮转无误报）**）。周期监控已设置（会话内 cron，每 23 分钟：进程/推进/槽位/资源/gate 失败核查）。唯一下一动作：按监控周期推进 AGU（当前 ITEM-020）→ ITEM-021..039 → L1d-TLB → Load Queue（ITEM-274 resume 96 样本）。**新增并行工作流（DR-001 裁决 D+A，2026-10-08）**：W1 MiBench + W13 PARSEC 负载补建（探路→获取→aarch64 静态交叉编译→golden×3→负载注册→W1/W13 ITEM 准入解锁），不阻塞波次 5。

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
| P3 全矩阵 Pilot | IN_PROGRESS | 2026-09-29 19:04（首个正式样本） | | runs/lsu/pilot/{AGU,Load_Queue}/（unit_status.json + result.json + 样本目录）；波次 5 运行中 |
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
- **10-06/07（compaction 前后会话）完成：** ①U1 swap_na 移植到 4 槽守卫并节点验证
  （d2b7e885，evidence/P3/u1port_4slot_swapna_cn23423.out 全 PASS）；②U3 LSU_GEM5_BIN
  接线实现 + 验证（gem5_bin() + runner/unit_pilot 引用替换 + manifest gem5_invocation
  字段；dry-run 切换与 sha/seed 稳定 + 真跑两遍法 census N=2767→s0 L5
  Crash/simulator_assert EXEC_RC=0）——**未提交**：真跑发现集群二进制 63f50c40 ≠
  记录结果 b64c808d（F-030）。
- **2026-10-08 10:37（集群口径；Windows 中继时区 -0400 vs 集群 +0800，同瞬不同区，本地钟曾示 10-07 22:37；集群中断期 Windows 本地取证）：** login01（10.39.0.1）SSH/ping 中断
  （E-005）→ 转本地取证：F-030 身份链闭合（src 树 6c336109 三方一致、lsu_proxy blob
  4001eba1、agu_addrmodes 90a19003 均与 manifest 记录吻合；b64c808d 在 Windows 全盘与
  sdc1-01-02 无副本）；计划新增 U3b（二进制身份恢复：集群搜索→工具链核查→守卫 -j8
  重建→census 2772 + det 语义连续性验证）。
- **2026-10-08 11:09（恢复后复核）：** keeper 1773102 RUNNING（djob，cn23423 未丢）；集群树 d2b7e885 + 未提交 U3 编辑完好；旧机访问：候选 172.168.177.97 SSH 存活但全部可用密钥 Permission denied（sdc@/root@ × 0102 键与 Windows 中继键）——不猜测口令，放弃该路径；origin c2dbee1d：**DR-003 已由用户裁决 A**（旧机续跑 + 并发 4 + 集群侧 idle）→ Session 002 遵守裁决：集群不跑波次，仅平台工程。
- **2026-10-08 11:41-11:47（U3b CP4 重建）：** CP1-CP3 收口（证据 evidence/P3/u3b_cp1_*.out、u3b_oldmachine_build_config.tar.gz——旧机配置物证 HAVE_PROTOBUF=1/HAVE_PNG=0）；CP4 attempt 1 因悬空符号链接失败（E-006），attempt 2 于 11:42 经守卫启动（bash 3323552 → scons 3323664，-j8 单编译任务，login01 gcc 10.3.1（低于 v25.1 支持范围 11-14.2，warning 非致命）、python 3.9.9、HAVE_PROTOBUF 预期 0（login01 无 protoc，与记录平台差异显式记录）、无 tcmalloc（仅性能差异）——配置差异由 CP5/CP6 行为等效把关）。
- **唯一下一动作：** 等 CP4 编译结果 →（成功）banner/sha256/原生冒烟 + CP5 census eligible==2772 两遍法 + CP6 A01-F0-W3 det 语义双跑比对 → U3 提交 → U6；（编译失败）评估 /opt/compiler/BiShengCompiler-3.1.0（clang 族）或回 sdc1-01-02 场地（等 opendcdiag campaign 结束且 SwapFree≥4 GiB）/提 Decision Request。keeper 续期（10-10 16:43 到期前）。波次 5 由 Session 003 旧机执行，集群不双跑（DR-003-A）。

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
| E-005 | 2026-10-08 10:40:48 恢复（集群口径；起始未知——发现前已中断；Windows 中继时区 -0400 vs 集群 +0800，同瞬不同区） | 集群接入 | login01（10.39.0.1）SSH/TCP 22 与 ping 均不通；tracert 第 3 跳 10.39.1.1 后无响应；Windows 中继、sdc1-01-02、github 均正常；Topsec SV-Connection VPN 适配器断开>14h，但中断前集群在同样断开状态下可达 → 判定集群侧故障，非本机侧；候选 10.39.0.2-6/10.39.0.11/10.39.1.2-3 端口 22 均不通 | 1 | 后台 30s 轮询 TCP 22（25 分钟一轮，到期重布）；中断期转 Windows 本地推进：F-029 取证、计划修订 U3b、文档更新与推送 | OPEN：恢复后核查 keeper job 1773102（cn23423）存续；若集群整体重启作业丢失，按目标规则重占最空闲节点（节点名最大→最小遍历） | Windows Test-NetConnection/tracert 输出；轮询任务 bbav582dx；会话工具记录 |
| E-006 | 2026-10-08 11:41 | gem5 构建 | U3b CP4 attempt 1：scons Mkdir(CHAOS/gem5/build/ARM/gem5.build) ENOENT——rm -rf build/ARM 后 CHAOS/gem5/build/ARM 符号链接（→ ../../../build/ARM）悬空 | 1 | 修复：scons 前预建 mkdir -p build/ARM | RESOLVED（attempt 2 过配置进入编译） | runs/lsu/guard/u3b_cp4_build_login01.log；lsu_keeper/u3b_cp4_outer*.log |

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

## 2026-10-08 采样政策迁移

- **同步方式：** 保留服务器既有 P0–P3 状态、证据、错误、Decision Request 和正在运行的波次；只同步本地最新版静态文件，并在远端动态文件上合并新规则，未用本地模板覆盖服务器记录。
- **生效规则：** 每个有效 RunID 先取得 30 个独立 activated pilot；若注入器、配置、workload、checkpoint 与 oracle 不变，可计入后续累计，否则作废重采。每个有效 RunID 固定累计至少 385；仅 `task_plan.md` 固定的 21 个重点 RunID 累计到 2401，且 2401 包含前 385。
- **对当前 P3 的影响：** pilot 目标仍为 30，因此 ITEM-020 及波次 5 无需中断；已有合规样本全部保留。P4/P5 启动前必须按新版清单重新冻结 manifest、sample_index/seed 范围和目标样本数。
- **统计口径：** 合法目标出现率=`eligible/attempted`，故障激活率=`activated/eligible`，条件结果率分母=`activated-post_activation_simulator_failure`；统一报告 Wilson 95% 置信区间，不按中途结果或区间半宽序贯停止。
- **新文档基线：** 完整清单 SHA-256=`4232b0839e827a1cb1ab5a4ac4fa8096eca479457249054afddfb6dc9c460f8e`；XLSX SHA-256=`1af33366d61644feb9d2c080ff6a38664ecdb064f7091d57890d2e1fb0f13c18`。
- **可比性说明：** 2026-10-08 前已经查看过 pilot 结果的重点组合属于“政策冻结前已有探索性信息”，不得宣称为完全事前预注册的独立确认性结果。
