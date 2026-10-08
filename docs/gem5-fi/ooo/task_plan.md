# Task Plan：OOO 单元故障注入实验

## Goal

依据已从 Excel 完整提取的 `完整任务执行清单.md`，在服务器上完成可复现、可审计、可断点续跑的 OOO 故障注入实验，闭环 6 个 OOO 单元、57 个故障模型和 310 个 ITEM/RunID，并形成原始数据、统计结果、图表、报告与复现包。Excel 仅用于来源核查，不参与日常调度。

## Next Step

执行 P0：校验文件哈希与清单规模，盘点服务器、仓库、已有 patch/脚本/进程/结果，建立编译单实例锁、实验 worker lease 注册表、资源守卫、任务心跳和恢复扫描，填写 G0-01 至 G0-10。不得直接启动大规模实验。

## Current Phase

P0

## 固定基线与口径

- 单元：Int Decode、Int Rename、Int Dispatch/ROB、FP/SIMD Decode、FP/SIMD Rename、FP/SIMD Dispatch/ROB。
- 模型/任务：57 个唯一模型，310 个唯一 RunID，对应 `7.展开执行矩阵` 第 2–311 行。
- 主基线 B0：gem5 stable `O3_ARM_v7a_3 / ArmO3CPU`；单线程；fetch/decode/rename=3，dispatch=6，issue/writeback/commit=8，ROB=40，IQ=32，Int PRF=128，Float PRF=192，Vec PRF=48。
- ISA：AArch64 + scalar FP + AdvSIMD/NEON 128-bit；SVE 不混入 B0。
- 频率：F0、F1、F2、F4、F5、F6；工作簿定义为唯一口径。
- Pilot：每个有效 RunID 取得 30 个独立 activated runs/clusters；Screening：至少 385 个。
- F1–F4 以一次运行为独立 cluster；P5 确认性扩样使用新的 holdout runs。
- 源 Excel SHA-256：`b73b6304005e507f5e8a1f41f0fc979f3d6439e6dda875ec4d2be961b867ae75`；完整清单 SHA-256：`f520d42a53ae2e44e76af5771dd1bcbdb9545082458e7996b1d306f1bbc30c91`。

## 清单调度与恢复协议

1. `完整任务执行清单.md` 中 ITEM-001 至 ITEM-310 是唯一实验项集合；每项对应一个 RunID 和 Excel 行。
2. 调度器不得直接读取 Excel 生成任务。主 AI 从清单 ITEM 创建不可变 run manifest，再实例化 runner 命令。
3. manifest 至少包含 ITEM、RunID、Excel 行、模型ID、单元、注入位置、故障类型/子模型、频率、负载、触发条件、激活口径、传播监控、phase、sample_index、seed、checkpoint、oracle、timeout、代码/patch SHA、campaign 和输出目录。
4. manifest 缺字段、与清单不一致或不能唯一实现时，该 ITEM 设为 BLOCKED，不得补默认值。
5. seed 规则：`seed = SHA256("ooo-fi-v1|" + RunID + "|" + phase + "|" + sample_index)` 的低 64 位，按无符号大端整数解释。敏感性配对实验复用 B0 seed manifest。
6. run_key 规则：`campaign/phase/RunID/sample_index/seed/config_sha`；同一 run_key 只允许一个 RUNNING owner 和一个 COMPLETE 结果。
7. 恢复顺序：读取五个 Markdown → 核查锁/PID/PGID → 扫描 COMPLETE/INTERRUPTED/tmp → 对账 progress 与磁盘 → 只恢复缺失样本。
8. 工程、pilot、screening、confirmatory、sensitivity、reproduction 使用不同 campaign/phase；工程数据禁止进入正式统计。
9. 所有重任务服从 `总方针.md`：编译≤8且单实例；实验并发硬上限4，允许不同 ITEM/RunID 并行，资源不足时降并发；60秒资源日志和30分钟进度心跳。

## 门禁

| Gate | 内容 | 通过标准 | 状态 |
|---|---|---|---|
| G0-01 | gem5 仓库、commit、分支、工作树 | commit 固定，工作树归属清楚，clean build 可重复 | **PASS**（运行时须兼容 loader，见 F-008；证据：gem5-build-001.out + 冒烟 FINAL=45737cc9a76c0dce ×2） |
| G0-02 | OOO 注入 patch 与配置生成器 | 57 模型均有唯一实现映射，确定性测试通过 | PENDING→P1（U0 映射表落地 + U1 确定性测试） |
| G0-03 | OS、编译器、Python、依赖 | environment lock 可重建 | **PASS**（F-003/F-004 供给链实测可重建；+兼容运行时 F-008） |
| G0-04 | B0/S0–S6 CPU/OOO 参数 | 与 Excel 逐项一致，单因素配置只改变预注册参数 | PENDING→P1（参数基线表转录 + ooo_proxy.py 逐项核对） |
| G0-05 | W0–W13、输入、许可证 | 清单实际使用的负载可用；不可用项获批准 | **PARTIAL**（在库 7/11；W1 已供给待上传 DR-001；W3/W8/W9/W13 为 P1 定向探针开发项） |
| G0-06 | checkpoint | 生成方式与哈希固定，golden/故障运行一致 | PENDING→DR-002（W1 规格标 FS优先、W5 标 SE+FS子集；gem5-fs 3.0G 资产在位；SE 基线则无 checkpoint 依赖） |
| G0-07 | golden、commit trace、oracle | 重复稳定，整数与 FP/SIMD 规则可自动判定 | **PARTIAL**（9 负载族 golden 台账在库 workloads/ooo/README.md；重复稳定性复验与 oracle 全量接线 → P1/P2） |
| G0-08 | seed、run_key、manifest | 稳定生成、唯一、可复现、可恢复 | **PARTIAL**（run_key/manifest/原子 COMPLETE/恢复扫描 PASS：ooo_recover selftest 10/10；seed 生成器 → P1 U11） |
| G0-09 | timeout、分类和守恒 | golden 10×规则与绝对上限固定，分类器测试通过 | PENDING→P1（U10 分类器/守恒规则实现 + 测试） |
| G0-10 | 资源防护与长任务守护 | 编译≤8且单实例；实验并发≤4、worker lease、run_key去重、PID/PGID、60秒监控、30分钟心跳、启动门禁、TRIP和恢复扫描可验证 | **PASS**（Unit1 T1–T6 + run 全路径实测 2026-10-08 + ooo_recover 10/10） |

## Phases

### P0：环境、输入与恢复预检

- [x] 启动时将本阶段设为 IN_PROGRESS，同步更新 `progress.md`。（Session 001 起）
- [x] 读取全部执行文件，核验 Excel 与完整清单 SHA-256。（`f520d42a…30c91` / `b73b630…7ae75`，2026-10-08 重连后复验一致）
- [x] 核验 57 模型、310 唯一 ITEM、310 唯一 RunID、Excel 第 2–311 行映射。（Session 001 结构核验）
- [x] 盘点 OS、CPU/RAM/swap、磁盘/配额、调度器、Python、编译器、依赖和长期存储。（findings 环境表 + F-001..F-005）
- [x] 核查 gem5 仓库、origin、目标分支、commit、工作树、patch 和构建状态；不覆盖用户修改。（worktree ooo-exec 独立分支；主树 LSU WIP 未触碰）
- [x] 核查编译、gem5、测试和实验进程的 owner/PID/PGID、锁、临时结果和 COMPLETE 标记。（Session 001 预检零残留；`tools/ooo_recover.py` 提供常态化对账）
- [x] 盘点 workload、镜像、checkpoint、golden、oracle、seed、已有脚本和已有结果。（findings 环境表：9 负载族 golden 台账 / tools/classify.py+manifest_validate.py / gem5-fs 3.0G / runs/ 无既往结果；checkpoint 挂 DR-002）
- [x] 建立并测试编译单实例锁、实验 worker lease 注册表、并发上限4、资源守卫、任务心跳、30分钟状态更新、原子 COMPLETE 标记和恢复扫描。（Unit1 `ooo_guard.py` T1–T6 + run 全路径；Unit2 `ooo_recover.py` 10/10；holder 心跳/60s 资源采样运行中；worker 状态模型=manifest+heartbeat，见 Unit2 修订注记）
- [x] 填写 G0-01 至 G0-10；缺失或冲突项生成 Decision Request。（G0 表已填；DR-001 W1 供给、DR-002 FS/SE 基线，见 findings.md）
- **Status:** COMPLETED（2026-10-08 工程收口。G0-02/04/09 与 G0-06/07/08 余项归属 P1 单元，批量实验启动前须全部关闭复验）

### P1：环境冻结、57 模型注入器与 L0–L5 观测链

- [ ] 固定 gem5 commit、patch、依赖、B0 配置和目录契约。
- [ ] 为 D01–D09、R01–R09、B01–B10、FD01–FD09、FR01–FR10、FB01–FB10 建立唯一注入映射表。
- [ ] 实现 XOR、双 bit、stuck-at、合法换值、状态、错位拼接和时序故障；每次只启用清单指定子模型。
- [ ] 建立动态指令/ROB/commit ID 贯穿 decode→rename→dispatch/IQ→execute/writeback→ROB/commit。
- [ ] 实现 L0–L5、attempted/eligible/activated、首检、主结局、Simulator failure 和守恒分类器。
- [ ] 实现稳定 seed、不可变 manifest、run_key、临时目录、COMPLETE 标记、心跳和恢复逻辑。
- [ ] 入口强制接入资源锁与守卫，单元测试、确定性测试、重复 seed 测试通过。
- **Status:** PENDING

### P2：负载、checkpoint、golden 与工程冒烟

- [ ] 准备并冻结工作簿 W0–W13；主清单未使用的负载不得擅自加入正式 campaign。
- [ ] 生成只读 checkpoint 与哈希；整数、FP32/64、NEON lane、FPSR/FPCR 和异常恢复 oracle 可自动执行。
- [ ] 每个确定性负载至少 3 次 golden；允许浮点容差时同时保存位级与容差结果并预注册规则。
- [ ] 固定 warm-up、timeout 和 commit trace 对齐规则。
- [ ] 57 个模型分别完成注入关闭、可激活、不可激活、重复 seed、寿命/清除和恢复测试。
- [ ] 冒烟全部标记 ENGINEERING_ONLY；G0-01 至 G0-10 全部 PASS/NA_APPROVED。
- **Status:** PENDING

### P3：310 RunID 全矩阵 Pilot

- [ ] 从 ITEM-001 至 ITEM-310 生成并冻结 pilot manifest；每个 run_key 唯一且可恢复。
- [ ] 每个有效 RunID 获得 30 个独立 activated runs/clusters。
- [ ] attempted 达 300 仍不足 30 个独立激活样本时暂停该 RunID，诊断并请求决策。
- [ ] 分开处理 pre_activation_infra_failure 与 post_activation_simulator_failure。
- [ ] 检查 L0–L5、计数守恒、manifest/日志完整、资源画像和断点恢复。
- [ ] 310 个 ITEM 均 COMPLETE，或有批准的 BLOCKED/NA_APPROVED。
- **Status:** PENDING

### P4：正式筛查

- [ ] 冻结 campaign、代码、配置、负载、checkpoint、oracle、seed manifest 和分类器。
- [ ] 每个有效 RunID 累计至少 385 个独立 activated runs/clusters。
- [ ] 报告激活率、五类主结局、首检四类、Hardware RAS 任意时点检测率和 SDC 率。
- [ ] 独立运行级二项结果报告 Wilson 95% 区间；F1–F4 事件传播使用 run-level cluster bootstrap。
- [ ] 所有分母、排除、重试、异常和守恒可从原始日志重算。
- **Status:** PENDING

### P5：主结果确认性扩样

- [ ] 查看新样本前冻结 selection manifest、组合数 K 和每组合主要 estimand。
- [ ] 使用新的 holdout runs，不与 P4 混作未校正确认性结果。
- [ ] 只在 n=500、1000、…、5000 十个检查点查看结果。
- [ ] 每组合使用双侧 `100×(1-0.05/(10K))%` Clopper–Pearson 区间。
- [ ] 区间半宽≤2个百分点或 n=5000 停止；普通 Wilson 95% 仅作描述。
- **Status:** PENDING

### P6：B0 单因素敏感性

- [ ] S0 仅切换 BaseO3CPU 默认宽核；S1 仅改变 decode/rename width；S2 仅改变 dispatchWidth；S3 仅改变 squashWidth。
- [ ] S4/S5 仅按工作簿改变 IQ/ROB/PRF 容量；S6 仅将 FP/SIMD FU 改为 1 个。
- [ ] 每个敏感性 campaign 与 B0 使用配对 seed、checkpoint、输入和 oracle；明确记录实际 diff。
- [ ] 报告绝对百分点差、风险比和区间；不得把敏感性样本并入 B0 主估计。
- **Status:** PENDING

### P7：稳健性与复现

- [ ] 完成论文负载对照、真实应用、FS 传播、异常恢复和整数/FP/SIMD 关键路径复核。
- [ ] 关键组合独立重跑至少 5%，核对 seed、目标、激活和分类。
- [ ] 确认性与探索性结果分栏。
- [ ] 在干净目录端到端复现至少一个整数关键 RunID 和一个 FP/SIMD 关键 RunID。
- **Status:** PENDING

### P8：分析、归档与交付

- [ ] 冻结源码/patch、环境、配置、负载、checkpoint、oracle、seed、campaign 和清单哈希。
- [ ] 归档原始日志索引、运行级汇总、分析脚本、图表、异常/排除和 Decision Request。
- [ ] 生成最终报告与复现说明。
- [ ] 核验 57 模型、310 RunID、所有门禁、样本、守恒、停止条件和复现证据。
- **Status:** PENDING

## 状态更新规则

- 阶段状态只能是 PENDING、IN_PROGRESS、BLOCKED、COMPLETE；同一时间只允许一个阶段 IN_PROGRESS。
- ITEM 阶段状态只能是 PENDING、RUNNING、COMPLETE、BLOCKED、INVALID、NA_APPROVED。
- 阶段状态变化时立即更新 Current Phase、唯一 Next Step、`progress.md` 和证据路径。
- 计划科学定义不得自行修改；状态、证据路径和用户批准可持续追加。

## Decisions Made

| ID | 时间 | 决定 | 理由 | 影响范围 | 批准/证据 |
|---|---|---|---|---|---|

## Errors Encountered

| ID | 时间 | 错误 | 尝试 | 处理/升级 | 证据 |
|---|---|---|---|---|---|
