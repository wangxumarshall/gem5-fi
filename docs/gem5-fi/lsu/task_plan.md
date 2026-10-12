# Task Plan：LSU 单元故障注入实验

## Goal

依据已经从 Excel 完整提取的 `完整任务执行清单.md`，在服务器上完成可复现、可审计的 LSU 故障注入实验，闭环 7 类 LSU 单元、64 个故障模型和 325 个 ITEM/RunID，并形成原始数据、统计结果、图表、报告与复现包。Excel 仅用于来源核查，不参与日常调度。

## Next Step

继续 P3 全矩阵 pilot；当前 ITEM、RunID、PID、资源状态和唯一下一动作以 `progress.md` 的 Current Status 为准。现有 pilot 仍以 30 个独立 activated runs/clusters 为目标，不因本次采样政策迁移中断或重跑。

## Current Phase

P3

## 全局实验口径

- 单元：AGU、L1d-TLB、Load Queue、Store Queue、L1d-Cache、原子与同步、数据预取器。
- 故障频率：F0 单次瞬态；F1–F4 重复/突发；F5 永久；F6 确定性路径/矩阵规定层。
- 负载：按 Excel 的 W0–W13 执行；不可用项必须记录并请求批准，不得自行替换。
- B0 是可复现实验基线，不是鲲鹏 920 的精确复刻；S1–S4 每次只改变一个因素。
- Pilot：每个有效 RunID 先取得 30 个独立 activated runs/clusters，用于检查注入器、负载、日志和 oracle；注入器、配置、workload、checkpoint 与 oracle 均未改变时，这 30 个可计入后续累计，否则作废重采。
- 正式筛查：每个有效 RunID 固定累计至少 385 个独立 activated runs/clusters；统一报告 Wilson 95% 置信区间。
- 重点扩样：仅以下 21 个固定 RunID 累计到 2401，且 2401 包含前 385 个，不是额外再取 2401 个，也不适用于其余 304 个 RunID：`A01-F0-W3`、`A04-F0-W3`、`T10-F0-W4`、`T04-F0-W4`、`S13-F0-W5`、`S04-F0-W5`、`L01-F0-W5`、`L03-F0-W5`、`C04-F0-W6`、`C05-F0-W6`、`C10-F0-W6`、`C12-F0-W6`、`O01-F0-W7`、`O05-F0-W7`、`P03-F0-W8`、`P07-F0-W8`、`P09-F0-W6`、`T10-F0-W11`、`S13-F0-W12`、`O09-F0-W13`、`P09-F0-W13`。
- 采样数量在 campaign 开始前按本清单固定，不依据中途点估计或普通置信区间半宽序贯停止；本政策版本自 2026-10-08 起生效。
- F1–F4 以一次运行为独立 cluster；单次运行内多个事件只用于传播分析。

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
| G0-05 | W0–W13、输入、许可证 | 可用状态明确，不可用项获批准 | PARTIAL-SE PASS（9 SE 负载 3× golden 全一致且 = V1.0 golden，evidence/P1/golden/；**DR-001 已裁决 D+A（2026-10-08）**：补建 W1 MiBench + W13 PARSEC（aarch64 静态 + golden 重确立后解锁 33 ITEM），W11 SPEC 无证则 NA_APPROVED；W4/W7 FS 部分、W12 近似口径待 FS 管线/DR-002） |
| G0-06 | checkpoint | 生成方式与哈希固定，golden/故障运行一致 | PASS（SE 记 none；B0 FS checkpoint 生成方式固定：Atomic boot + boot_ckpt.rcS → cpt.237949797015，28MB，清单哈希 88cf03e037d2269b，runs/lsu/fs_cpt_boot/；双跑 restore 同一 cpt 且结果一致——golden/故障运行一致性达成） |
| G0-07 | oracle | golden 重复稳定，规则可自动判定 | PASS-SE（golden 3× 全稳定；oracle = stdout hash 自动判定，tools/lsu_l5_classify.py 在库；FS oracle = tlb_probe md5 + ok=N/10 已定义） |
| G0-08 | seed | 稳定算法和 seed manifest 可复现 | PARTIAL（tools/lsu_seed.py 实现并自测 PASS：固定向量+确定性+范围+phase/sample 区分；manifest 生成器就绪 325×30=9750 条冒烟通过；正式 seed manifest 冻结待 P3） |
| G0-09 | timeout | golden 10×规则及 wall/sim 上限固定 | PASS-SE（golden max wall 61s/run → SE timeout = 600s（10×），绝对上限 1800s；与守卫 --max-seconds 600 一致；FS timeout 待 tlb_probe 实测后固定） |
| G0-10 | CPU/RAM/worker/磁盘预算与资源防护 | 编译≤8且单实例；实验硬上限4（压力降3/2/1、恢复回4）；槽锁、PID/PGID、60秒监控、启动门禁和熔断均可验证 | **PASS-4 槽口径（2026-09-30 16:20 复验）**：守卫 4 槽位（commit 7a61df86）——隔离测试 T1-T6 全 PASS（6 并发 4 成功 2 拒绝零双取、release --slot+--confirm-pid 防误删、陈旧槽 clear-stale、run 周期槽复用，evidence/P3/f022_patch_a_test.txt）+ 实机验证（波次 4：4 槽并行占用、75 样本 resume、MemAvailable 26.9 GiB）；build 锁仍单实例；F-023 fail-fast（GUARD_FAILURE 不记账）保持。旧口径 T1-T7 见 evidence/P0/guard_verify.out |

## 逐单元调度协议（2026-10-12 用户指令，自此取代"三单元连续波次"模式）

1. **单元顺序**：新实验按 `AGU → L1d-TLB → Store Queue → L1d-Cache → 原子与同步 → 数据预取器 → Load Queue` 推进；**当前新调度单元 = AGU**。
2. **跨单元既有结果**：已完成的跨单元结果（如 W1 重跑已闭合的 LQ 274/277/281 与旧波次各单元项）保留并**提前回填**矩阵，但其所属单元未轮到时**不继续扩展该单元调度**（LQ 剩余工作如 ITEM-287 pilot/重跑等排队至 LQ 单元轮次）。
3. **单元内并行**：不同 RunID 可并行；**全机 gem5 总并发 ≤4**、编译单实例且 ≤-j8；每个实验独立 manifest/run_key/输出目录/PID-PGID/锁/心跳/恢复命令；每批启动前检查 MemAvailable/SwapFree/load/磁盘/锁/现有进程。
4. **RunID 阶梯**：count-only/工程门禁 → n=5 准入 → pilot-30 → formal 累计 385 → 指定重点 RunID（全局实验口径 21 项名单）累计 2401；30/385/2401 与 seed 规则按全局实验口径，pilot-30 在配置不变时计入 385 累计。
5. **增量记录**：完成一个阶段立即更新 progress.md 与权威 Excel（tools/lsu_xlsx_backfill.py 备份/临时/校验/原子替换协议），**不等待整个单元结束**；Excel 回填单独 [LSU][DATA] 提交。
6. **BLOCKED 纪律**：某项 BLOCKED 立即记录原因与证据路径，继续同单元其他可运行项；BLOCKED 不得伪造完成，不得通过更换故障语义、负载或放宽 eligibility 绕过；载体改指须有用户裁决先例（如 D-2026-10-09-重跑）。
7. **单元出口**：该单元全部 RunID 均为 COMPLETE、批准的 BLOCKED 或 NA_APPROVED，且计数守恒、证据路径齐全、Excel 回填校验通过后，方可进入下一单元。
8. **Subagent 协调**（2026-10-12 第六节）：主 Agent 为唯一调度者与唯一写入协调者（Excel/progress/task_plan/Git 串行写入）；subagent 可并行只读审计/矩阵核对/结果统计/回填草案生成，或执行主 Agent 明确分配的独立实验任务；不得自选 RunID/启动未分配 campaign/改实验口径；同一 RunID/sample 唯一 owner。
9. **服务器身份锁**（2026-10-12 第零节）：本机 = localhost0101/172.168.177.97（0101 LSU 执行服务器，progress.md 服务器身份字段实测记录）；只维护 docs/gem5-fi/lsu/ 与 LSU 专用工具；共享文件（runner/campaign/classify/schema/gem5 C++）修改前在 progress.md 登记，已知 0201 修改同一文件时停写只出草案；等主协调端独立干净克隆统一集成，本地提交不自行 push。

## Phases

### P0：环境与资产预检

- [x] 启动时将本阶段状态改为 IN_PROGRESS，并同步更新 `progress.md`。
- [x] 读取总方针、计划、完整清单和状态文件；Excel 仅做来源哈希与争议核查。
- [x] 核验完整清单 SHA-256；2026-10-08 采样政策迁移后的当前值为 `4232b0839e827a1cb1ab5a4ac4fa8096eca479457249054afddfb6dc9c460f8e`，并包含64个模型、325个唯一ITEM、325个唯一RunID和Excel第2–326行映射。
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
- **Status:** IN_PROGRESS（服务器 `progress.md` 显示自 2026-09-29 起执行；2026-10-08 同步时继续运行，具体 ITEM 以 Current Status 为准）

### P4：正式筛查（2026-10-08 采样政策迁移：本节旧定义为历史口径，新口径 = 全部有效 RunID 累计 ≥385 activated，pilot 30 在配置全不变时计入；扩样前须冻结新版 manifest 目标与样本范围——findings F-037；下同）

- [ ] 冻结正式 campaign、代码、配置、workload、checkpoint、oracle 和 seed manifest。
- [ ] 每个有效 RunID 累计至少 385 个独立 activated runs/clusters。
- [ ] 报告激活率、五类主结局、首检四类、Hardware RAS 任意时点检测率和 SDC 率。
- [ ] 独立运行级二项结果报告 Wilson 95% 区间；F1–F4 事件级传播使用 run-level cluster bootstrap。
- [ ] 所有分母、守恒、排除、重试和异常可由原始日志重算。
- **Status:** PENDING

### P5：固定重点组合扩样

- [ ] 冻结上述 21 个重点 RunID 的 selection manifest、sample_index/seed 范围和每组合主要二项 estimand。
- [ ] 每个重点 RunID 从累计 385 继续到固定累计 2401；其余 304 个 RunID 保持累计至少 385。
- [ ] 2401 中可包含满足同一冻结配置与质量门禁的 pilot/screening 样本；任何配置、workload、checkpoint 或 oracle 改变都必须分层或重采。
- [ ] 全程报告 Wilson 95% 置信区间；不得因中途结果、区间半宽或达到旧的 5000 上限而序贯停止。
- [ ] 对 2026-10-08 前已经查看过 pilot 结果的组合，明确标为“政策冻结前已有探索性信息”，不得表述为事前预注册的独立确认性结果。
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
| D-2026-10-10-Overlay口径 | 2026-10-10 16:55 | **不扩充 L5 终类**（五类闭集不变）；幻影/noop 以**正交注入有效性字段**记入 correction overlay：raw_class（永久保留）/trigger_observed/fault_write_attempted/fault_effective/valid_for_l5/exclusion_reason（≥5 枚举：pre_filter_rejected_after_trigger、fault_write_not_applied、fault_write_noop、missing_effective_write_evidence、other_invalid_injection）/evidence_path/corrected_class（仅 valid_for_l5=true 填写否则 null）；统计规则：仅 fault_effective=true 且证据闭环计 activated，仅 valid_for_l5=true 进 L5 分母，invalid 无新终类 corrected_class=null，raw_class 不删不覆盖，报告六元组 attempted/triggered/write_attempted/effective_activated/invalid_excluded/valid_L5_denominator，禁 Masked→Inactive 绕过、禁 noop 计有效 Masked；当前暂定：ITEM-271=16/30、ITEM-279=19/33、ITEM-019=31/33、ITEM-022=32/33（逐样本证据确认后方可转最终）；共享 schema 不在 golden 期间修改——本轮只在 overlay 实现，oracle 冻结后单独提最小向后兼容只增字段方案，改共享 runner/campaign/classify/schema 前再次汇报范围 | NoInjection/InvalidInjection/NoEffect 是注入有效性维度而非程序执行终态，混入 L5 会破坏统计口径 | F-049 污染审计 4 项 + 未来所有幻影/noop 处置 | 用户裁决原文 2026-10-10 |
| D-2026-10-10-ITEM285撤销 | 2026-10-10 16:55 | **ITEM-285（L03-F0-W5）撤销 L03 模型身份**：33/33 全部不得作为"L03-F0"科学结果；状态标记 model_identity_invalid / quarantined / rerun_required；不得改标签后纳入原 L03 结果；原始结果与日志保留作接线缺陷证据与工程调试；仅当精确证明实际配置对应另一已定义模型时可在独立审计中讨论作辅助工程证据，不得自动转归正式数据；**全库搜索 --lsqfwd_l03 已执行（2026-10-10）：仅 L03 家族 3 项命中（ITEM-285 含 census 34 文件、ITEM-287 300、ITEM-289 300），det/engineering/manifests 零命中——失真范围封闭**；SEM-B 修复后 ITEM-285 须重走完整准入（config.ini 确认 l03 实传 → count-only>0 → 正/负对照 → n=5 真实有效注入 → pilot 30 → 确定性重放 → golden+不受影响回归 → 再决 formal）；ITEM-287/289 同样使用 --lsqfwd_l03，其重跑亦以 SEM-B 接线修复为前置 | --lsqfwd_l03 参数未接线，实际执行模型（byte_flip）与声明 L03 模型不一致——数据有效但模型身份失真 | ITEM-285 全部 33 样本；ITEM-287/289 重跑前置条件；L03 家族统计口径 | 用户裁决原文 2026-10-10；F-047(b)/F-049 审计；全库 grep 实证 |
| D-2026-10-10-SEM-F6管理 | 2026-10-10 16:55 | F-048 MemoryOrderViolation 设计方向**批准**，但仍按独立语义变更管理：ITEM-289 继续 capability-gap/design-blocked，新事件源通过守恒/count-only/正负对照/n=5/pilot/重放全部准入门之前不得宣称已解决；不得用该事件源挽救 F4 或 ITEM-287；ITEM-287 等 W1 census 实测后再裁决 | 语义变更须全门禁验证；事件源与档位需求不匹配时不得挪用 | [LSU][SEM-F6] 实施全程；ITEM-287 裁决时点 | 用户裁决原文 2026-10-10 |
| D-2026-10-10-ITEM289 | 2026-10-10 16:20 | **ITEM-289（L03-F6-W5）裁定 capability-gap / design-blocked / 当前实现不可激活**：禁止将内存序违规近似映射到 SqForward；15 项按载体事件供给路线重跑，ITEM-289 不进本轮批次、不计"已修复并完成重跑"；后续以独立 MemoryOrderViolation 事件源解决（[LSU][SEM-F6] 单独语义提交：定义事件产生条件/触发位置/eligibility/故障写入点/守恒关系，区分 event_seen/eligible/triggered/fault_applied/faults_injected，须正对照+负对照+count-only+最小注入+确定性重放），通过全部准入门后单独重跑；此前不得用替代事件生成结果 | SqForward 与内存序违规不是同一微架构事件，近似映射改变模型语义使结果不可解释；不能为激活率把现有事件冒充目标事件 | ITEM-289 及 L03-F6 语义；本轮重跑批次（15 项） | 用户裁决原文 2026-10-10；F-047 三源审计 |
| D-2026-10-10-幻影审计 | 2026-10-10 16:20 | **ITEM-271 幻影激活数据更正单独先行**（不等重跑）：全 PRE-hook 历史项目只读扩大审计（逐 activated 样本核对 trigger/eligibility/实际故障写入/faults_injected/注入前后目标值或等价写入证据/日志-stats-分类三方一致性）；原始 runs/results.jsonl 永久保留、只增 correction overlay/manifest；14 幻影样本剔除 activated 与有效注入分母；其余 16 样本逐样本确认实际写入前只记"暂定 16/30"不得冻结；幻影终类按现有 schema（NoEffect/NoInjection/InvalidInjection 若支持），不得因 faults_injected=1 判 Masked、不得无 schema 依据伪装 Inactive；schema 无法表达"triggered 但未施加故障"则先报告不擅自改共享 schema；提交 [LSU][DATA] 只含审计报告/overlay/勘误/离线审计工具 | 数据诚实优先；幻影激活污染统计分母；原始数据不可篡改 | 所有 PRE 钩子历史项目（ITEM-271 已实证 14/30 幻影）；P3 已采数据统计口径 | 用户裁决原文 2026-10-10；F-047/B 审计 |
| D-2026-10-09-重跑 | 2026-10-09 10:50 | 16 个运行时 BLOCKED 项（AGU 11 + LQ 5，F1/F2/F4/F6 × 短流负载）定性为环境未配置；修复环境（W1 长流载体 w1_all）后**直接重跑**；RunID 不变、载体改指 W1；原 300/0 归档为 SE 短流环境证据，重跑入新 campaign | 用户明确指令（2026-10-09 上午，findings F-041）：blocked = 环境问题，非科学结论 | 16 ITEM 重跑（addrpath/lsqfwd 家族全 SE 可跑）；重跑优先于 W1 列新 ITEM | 用户指令原文记录于 findings.md F-041 |
| D-2026-09-30-并发 | 2026-09-30 14:30 | gem5 实验并发硬上限由 1（画像后 2）调整为 **4**；编译规则不变；不得为满足上限杀死健康实验；每个并行实验独立 run_key/manifest/输出目录/日志/lease/PID-PGID/心跳 | 用户明确指令（2026-09-30 14:30） | 全部实验执行、守卫锁机制、unit_pilot 引擎 | 用户指令原文记录于 findings.md F-022 |
| D-2026-10-08-采样 | 2026-10-08 | 每个有效 RunID 先 30 个 pilot、固定累计至少 385；仅固定清单中的 21 个重点 RunID 累计到 2401；取消旧 holdout/5000/区间半宽序贯停止规则 | 385 与 2401 分别对应最坏比例 p=0.5、95% 置信水平下约 ±5pp 与 ±2pp 的固定样本量；统一固定规则便于解释和审计 | P3 pilot 目标不变；P4/P5 manifest、调度、统计与文档基线更新 | 用户 2026-10-08 本地修订；见 findings.md“2026-10-08 采样政策迁移” |

## Errors Encountered

| ID | 时间 | 错误 | 尝试 | 处理/升级 | 证据 |
|---|---|---|---|---|---|
