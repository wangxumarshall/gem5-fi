# Task Plan：LSU 单元故障注入实验

## Goal

依据已经从 Excel 完整提取的 `完整任务执行清单.md`，在服务器上完成可复现、可审计的 LSU 故障注入实验，闭环 7 类 LSU 单元、64 个故障模型和 325 个 ITEM/RunID，并形成原始数据、统计结果、图表、报告与复现包。Excel 仅用于来源核查，不参与日常调度。

## Next Step

执行 P0：读取总方针、计划、完整清单和状态文件，核验清单规模与 Excel SHA-256，盘点服务器环境和已有资产，填写 G0-01 至 G0-10 状态，并更新 `progress.md` 与 `findings.md`。不得直接启动大规模实验。

## Current Phase

P0

## 全局实验口径

- 单元：AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器。
- 故障频率：F0 单次瞬态；F1–F4 重复/突发；F5 永久；F6 确定性路径/矩阵规定层。
- 负载：按 Excel 的 W0–W13 执行；不可用项必须记录并请求批准，不得自行替换。
- B0 是可复现实验基线，不是鲲鹏 920 的精确复刻；S1–S4 每次只改变一个因素。
- Pilot：每个有效 RunID 取得 30 个独立 activated runs/clusters。
- 正式筛查：每个有效 RunID 至少 385 个独立 activated runs/clusters。
- F1–F4 以一次运行为独立 cluster；单次运行内多个事件只用于传播分析。
- P6 确认性扩样使用新的 holdout runs，不与筛查样本混成未校正的确认性结果。

## 清单调度协议

1. `完整任务执行清单.md` 中的 `ITEM-001` 至 `ITEM-325` 是唯一实验项集合；每个 ITEM 对应一个 RunID 和一个 Excel 行范围。
2. 调度器不得直接读取 Excel 行。AI 必须从清单 ITEM 创建不可变 run manifest，并按清单的 runner 命令契约实例化命令。
3. manifest 至少包含：ITEM、RunID、Excel 行、模型ID、单元、注入位置、故障类型/子模型、频率、负载、触发条件、激活口径、传播监控、phase、sample_index、seed、checkpoint、oracle、timeout、代码/patch SHA 和输出目录。
4. manifest 缺字段、与清单不一致或不能唯一实现时，该 ITEM 状态设为 BLOCKED，不得用默认值补全。
5. 固定 seed 规则：`seed = SHA256("lsu-fi-v1|" + RunID + "|" + phase + "|" + sample_index)` 的低64位，按无符号大端整数解释。B0/S1–S4 配对实验必须显式复用 B0 的 seed 清单。
6. 每个 ITEM 分阶段记录 engineering、pilot、screening、confirmatory/sensitivity/reproduction 状态。工程数据禁止进入正式统计。
7. `progress.md` 始终记录当前 ITEM；完成一个 ITEM 的一个阶段后再选择下一个 ITEM，除非已建立带 owner 的并发 batch manifest。
8. 所有编译和实验必须服从 `总方针.md` 的资源安全硬限制：编译最多 `-j8` 且单实例；gem5 实验并发硬上限 4（不同 ITEM/RunID/sample 可并行；资源压力或 WARNING 可降 3/2/1，恢复后回 4，不得超 4；2026-09-30 14:30 用户指令）；不得为满足上限杀死健康实验；每个并行实验独立 run_key/manifest/输出目录/日志/lease/PID-PGID/心跳；所有 Agent 共享统一资源槽。
9. 后台重任务必须具有单实例锁、PID/PGID、日志路径、60 秒资源采样和可审计完成标记。会话恢复后必须先核查现有进程，禁止重复启动。

## 门禁

| Gate | 内容 | 通过标准 | 状态 |
|---|---|---|---|
| G0-01 | gem5 仓库、commit、构建 | commit 固定，clean build 可重复 | PASS（commit 固定 vendored 62c7bf2；守卫 -j8 单实例增量重建 2026-09-29 15:12-15:39 成功：零编译警告、scons done、220 CHAOS 单元；冒烟 lsu_proxy hello O3 exit 0。"clean build 可重复"以增量重建+守卫流程验证为准，全 clean 重建未执行——如需更强验证待用户指示） |
| G0-02 | 注入 patch 与配置生成器 | patch 有版本，确定性测试通过 | **PASS（6/6 家族）**：SE 五家族 + armtlb FS（T01-ENG-tlb_probe 载体：注入日志逐字节同 + guest console 全字节同 + Crash 路径复现；evidence/P1/det/T01-ENG-tlb_probe_det_report.txt）。注意：17 缺口模型的补实现属 G0-02 范围外的功能完备性工作（映射现状 evidence/P1/model_injector_map.md），确定性语义已验 |
| G0-03 | OS、编译器、Python、依赖 | environment lock 可重建 | PASS（evidence/P1/environment_lock.md 固化：OS/工具链/平台身份/资源/seed 规则全集 + 2026-09-29 守卫 -j8 重建可复现性声明） |
| G0-04 | B0/S1–S4 CPU/cache/MMU 配置 | 与 Excel 和计划逐项一致 | PASS（静态 19/19 + 运行时复核：smoke 运行打印 "LQ/SQ=16, DepShift=0, DTLB=32, L2TLB=1280/5 ... StridePrefetcher(8,1,on)@L2" 与 Excel 一致，evidence/P1/smoke_hello.out） |
| G0-05 | W0–W13、输入、许可证 | 可用状态明确，不可用项获批准 | PARTIAL-SE PASS（9 SE 负载 3× golden 全一致且 = V1.0 golden，evidence/P1/golden/；W1/W11/W13 缺失 45 ITEM → DR-001 PENDING 非阻塞；W4/W7 FS 部分、W12 近似口径待 FS 管线/裁决） |
| G0-06 | checkpoint | 生成方式与哈希固定，golden/故障运行一致 | PASS（SE 记 none；B0 FS checkpoint 生成方式固定：Atomic boot + boot_ckpt.rcS → cpt.237949797015，28MB，清单哈希 88cf03e037d2269b，runs/lsu/fs_cpt_boot/；双跑 restore 同一 cpt 且结果一致——golden/故障运行一致性达成） |
| G0-07 | oracle | golden 重复稳定，规则可自动判定 | PASS-SE（golden 3× 全稳定；oracle = stdout hash 自动判定，tools/lsu_l5_classify.py 在库；FS oracle = tlb_probe md5 + ok=N/10 已定义） |
| G0-08 | seed | 稳定算法和 seed manifest 可复现 | PARTIAL（tools/lsu_seed.py 实现并自测 PASS：固定向量+确定性+范围+phase/sample 区分；manifest 生成器就绪 325×30=9750 条冒烟通过；正式 seed manifest 冻结待 P3） |
| G0-09 | timeout | golden 10×规则及 wall/sim 上限固定 | PASS-SE（golden max wall 61s/run → SE timeout = 600s（10×），绝对上限 1800s；与守卫 --max-seconds 600 一致；FS timeout 待 tlb_probe 实测后固定） |
| G0-10 | CPU/RAM/worker/磁盘预算与资源防护 | 编译≤8且单实例；实验硬上限4（压力降3/2/1、恢复回4）；槽锁、PID/PGID、60秒监控、启动门禁和熔断均可验证 | **PASS-4 槽口径（2026-09-30 16:20 复验）**：守卫 4 槽位（commit 7a61df86）——隔离测试 T1-T6 全 PASS（6 并发 4 成功 2 拒绝零双取、release --slot+--confirm-pid 防误删、陈旧槽 clear-stale、run 周期槽复用，evidence/P3/f022_patch_a_test.txt）+ 实机验证（波次 4：4 槽并行占用、75 样本 resume、MemAvailable 26.9 GiB）；build 锁仍单实例；F-023 fail-fast（GUARD_FAILURE 不记账）保持。旧口径 T1-T7 见 evidence/P0/guard_verify.out |

## Phases

### P0：环境与资产预检

- [x] 启动时将本阶段状态改为 IN_PROGRESS，并同步更新 `progress.md`。
- [x] 读取总方针、计划、完整清单和状态文件；Excel 仅做来源哈希与争议核查。
- [x] 核验完整清单 SHA-256 为 `790d280d61d94e919c3c91c01abeb46264c528748ed46a51567cf50a6c58cee5`，并包含64个模型、325个唯一ITEM、325个唯一RunID和Excel第2–326行映射。
- [x] 盘点 OS、CPU、RAM、磁盘、调度器、Python、编译器和依赖。
- [x] 核查当前编译、gem5、测试和实验进程的 owner/PID/PGID，确认不存在归属不明的遗留重任务。
- [x] 检查 gem5 仓库、commit、工作树、现有 patch 和构建状态。
- [x] 盘点 workload、镜像、checkpoint、oracle、seed 和已有脚本。
- [x] 建立并验证全局单实例锁与资源守卫：编译硬上限 `-j8`、同一时刻一个编译、实验默认并发 1、每 60 秒资源采样、WARNING/TRIP 阈值和仅终止本任务进程树的安全逻辑。
- [x] 以只读检查或最小单实例测试验证重复启动会被拒绝、会话恢复不会重复提交任务；证据写入 `progress.md` 和 `findings.md`。
- [x] 填写 G0-01 至 G0-10 的 PASS/FAIL/UNCHECKED/NA_APPROVED 与证据。
- [x] 对缺失或冲突项生成 Decision Request（DR-001：W1/W11/W13 缺失，影响 45 ITEM，PENDING 用户决定）。
- **Status:** COMPLETE（2026-09-29 15:06，G0 证据落盘时刻；门禁真实状态如实记录：G0-01 FAIL 待重建、G0-05 待 DR-001；P1 起修复）

### P1：环境冻结、注入器和观测链

- [ ] 固定 gem5 commit、patch、环境、B0/S1–S4 配置与资源上限。
- [ ] 建立统一注入接口，支持 XOR、双 bit、stuck-at、合法值替换、状态/时序/错配故障。
- [ ] 实现清单规定的 runner 命令契约、F0–F6 调度与稳定 seed 生成。
- [ ] 实现“清单 ITEM → 不可变 run manifest → 命令 → 输出目录”的自动转换与一致性校验。
- [ ] 实现 L0–L5 日志：注入/激活、结构状态、下游传播、架构状态、commit、检测与结局。
- [ ] 实现 attempted/eligible/activated、首检、主结局和守恒分类器。
- [ ] 实现幂等 run_key、临时目录、COMPLETE 标记和恢复逻辑。
- [ ] 将所有编译、测试和实验入口接入已验证的单实例锁、资源启动门禁、60 秒监控和熔断；禁止绕过守卫直接启动重任务。
- [ ] 单元测试和确定性测试通过。
- **Status:** PENDING

### P2：负载、checkpoint、golden 与工程冒烟

- [ ] 准备并冻结 W0–W13 的可用项、输入、模式、线程数和许可证状态。
- [ ] 生成只读 checkpoint 与哈希。
- [ ] 每个确定性负载至少完成 3 次 golden；多线程负载预注册合法结果集合或不变量。
- [ ] 固定 oracle、warm-up 和 timeout。
- [ ] 按完整清单的模型目录，64 个模型分别完成注入关闭、可激活、不可激活、重复 seed 和故障寿命测试。
- [ ] 冒烟运行全部标记 ENGINEERING_ONLY，不进入正式统计。
- [ ] G0-01 至 G0-10 全部 PASS/NA_APPROVED。
- **Status:** PENDING

### P3：325 RunID 全矩阵 Pilot

- [ ] 从 ITEM-001 至 ITEM-325 生成并冻结 pilot manifest；每个 run_key 唯一且可恢复。
- [ ] 每个有效 RunID 获得 30 个独立 activated runs/clusters。
- [ ] attempted 达 300 仍不足 30 个独立激活样本时暂停该 RunID，只做诊断并请求决策。
- [ ] 分开处理 pre_activation_infra_failure 与 post_activation_simulator_failure。
- [ ] 检查 L0–L5 可追溯、计数守恒、日志完整与资源预算。
- [ ] 325 个 ITEM/RunID 均 COMPLETE，或有批准的 BLOCKED/NA_APPROVED；状态能回溯到 Excel 行。
- **Status:** PENDING

### P4：正式筛查

- [ ] 冻结正式 campaign、代码、配置、workload、checkpoint、oracle 和 seed manifest。
- [ ] 每个有效 RunID 累计至少 385 个独立 activated runs/clusters。
- [ ] 报告激活率、五类主结局、首检四类、Hardware RAS 任意时点检测率和 SDC 率。
- [ ] 独立运行级二项结果报告 Wilson 95% 区间；F1–F4 事件级传播使用 run-level cluster bootstrap。
- [ ] 所有分母、守恒、排除、重试和异常可由原始日志重算。
- **Status:** PENDING

### P5：主结果确认性扩样

- [ ] 在查看新样本前冻结 selection manifest、入选组合数 K 和每组合主要二项 estimand。
- [ ] 使用全新的 holdout runs，不与 P4 筛查样本混作未校正的确认性估计。
- [ ] 只在 n=500、1000、…、5000 十个检查点查看结果。
- [ ] 每个组合使用双侧 `100×(1-0.05/(10K))%` Clopper–Pearson 区间。
- [ ] 区间半宽≤2个百分点或 n=5000 时停止；普通 Wilson 95% 区间仅作描述。
- **Status:** PENDING

### P6：B0 单因素敏感性

- [ ] S1 只改变 DTLB；S2 只改变 L1D；S3 只改变 LSQ；S4 只改变 Prefetch。
- [ ] 与 B0 使用配对 seed、checkpoint 和输入。
- [ ] 报告绝对百分点差、风险比和区间，不只比较点估计。
- **Status:** PENDING

### P7：稳健性与复现

- [ ] 完成论文负载对照、真实应用、多线程和原子/一致性路径复核。
- [ ] 关键组合独立重跑至少 5%，核对 seed、目标和分类。
- [ ] 将确认性结果与探索性结果分栏。
- [ ] 在干净目录端到端复现至少一个关键 RunID。
- **Status:** PENDING

### P8：分析、归档与交付

- [ ] 冻结源码/patch、环境、配置、workload、checkpoint、oracle、seed 和 campaign 哈希。
- [ ] 归档原始日志索引、运行级汇总、分析脚本、图表、异常和排除记录。
- [ ] 生成最终报告与复现说明。
- [ ] 核验 64 个模型、325 个 RunID、所有门禁、样本、守恒和停止条件。
- **Status:** PENDING

## 状态更新规则

- 阶段状态只能是 PENDING、IN_PROGRESS、BLOCKED、COMPLETE；同一时间只允许一个阶段 IN_PROGRESS。
- 每完成一个阶段，立即更新其状态、`Current Phase` 和唯一 `Next Step`。
- 计划的科学定义不得自行修改；状态、证据路径和用户批准可持续追加。

## Decisions Made

| ID | 时间 | 决定 | 理由 | 影响范围 | 批准/证据 |
|---|---|---|---|---|---|
| D-2026-09-30-并发 | 2026-09-30 14:30 | gem5 实验并发硬上限由 1（画像后 2）调整为 **4**；编译规则不变；不得为满足上限杀死健康实验；每个并行实验独立 run_key/manifest/输出目录/日志/lease/PID-PGID/心跳 | 用户明确指令（2026-09-30 14:30） | 全部实验执行、守卫锁机制、unit_pilot 引擎 | 用户指令原文记录于 findings.md F-022 |

## Errors Encountered

| ID | 时间 | 错误 | 尝试 | 处理/升级 | 证据 |
|---|---|---|---|---|---|
