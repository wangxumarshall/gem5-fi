# FPU/SIMD 项目清理前审计报告 (Pre-Cleanup Audit)

**项目目录**：`/home/sdc/gem5-fi-fpu`
**审计时间**：2026-11-26
**权威实验方案**：`inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx`（30 张工作表，其中 24–30 为最终 When_5×3 方案，16–22 已改名 `Legacy_Superseded`）
**目标 GitHub 仓库**：`https://github.com/wangxumarshall/gem5-fi`（默认分支 `main`）

---

## 1. 版本 / Git 状态（关键发现）

| 项目 | 状态 |
|---|---|
| 项目目录是否为 Git 仓库 | **否**（无 `.git`，`gem5/` 子目录亦无 `.git`） |
| 是否有 Git remote | 无 |
| 当前分支 / Commit | 无（本项目是一次无版本控制的只读 gem5 树 + 实验产物的快照） |
| 参考只读基线 | `/home/sdc/gem5-fi-ding`（HEAD `226778cf7d71e5cd47c8153fe7ef4eeabf82b858`） |

**说明**：`gem5-fi-fpu` 是本任务目标的 FPU 单元工作副本。它是把 gem5 基线
`226778cf7d71e5cd47c8153fe7ef4eeabf82b858` 的源码树拷贝出来后，叠加 FPU/SIMD
故障注入补丁（`reports/source_changes.patch`）+ 编排脚本 + 负载 + 实验产物得到的，
**整个过程中没有初始化 Git**。因此本任务第一阶段的“冻结分支/Commit/工作区状态”不适用，
以“文件树快照 + SHA256 指纹”代替版本冻结。

### 1.1 GitHub 远端状态（已核实）

- 仓库 `wangxumarshall/gem5-fi` 存在，默认分支 `main`（HEAD `f104bd830ddb892c20b54047b5e820ebe9430a73`，最近推送 2026-11-24）。
- 已存在分支：`main`、`mmu-final`、`lsu`、`IEX`、`fi-ding`、`fi-fuzz`、`fi-wx-archive-v1/v2`、`fi-wx-paper`、`hotfix/observer-tool-identity`、`documentation/...`、`feat/*`、`r4-*`、`ooo/*` 等。
- **尚无 `FPU` 分支**（需新建）。
- `gh` 已认证为 `wangxumarshall`（token 具有 `repo`/`workflow` 权限）。
- 网络：`git` 直连 github.com 需强制 `http.version=HTTP/1.1`（HTTP/2 下 `git-upload-pack` 握手会挂起），`gh api` 与 `curl` 正常。

---

## 2. 完整目录树与用途

顶层共 14G，结构如下：

| 路径 | 大小 | 用途 | 结论 |
|---|---|---|---|
| `gem5/` | 9.6G | gem5 源码树（基线 226778cf + FPU 补丁）+ build 产物 | 源码核心；`build/` 9.5G 为编译中间产物，不属代码 |
| `gem5/src/` | 79M | FPU 补丁所在（`src/arch/arm/**` + `src/cpu/o3/**`） | 保留 |
| `gem5/build/` | 9.5G | `gem5.opt` 二进制（1.2G）、`.o`、m5 生成物 | 编译产物，复现时重新 scons，不入库 |
| `inputs/` | 233K | 权威 Excel（唯一文件） | 保留 |
| `scripts/` | ~200K | 编排/分析脚本（见 §5） | 保留最终脚本，清理旧版 |
| `workloads/` | ~300K | 旧 R01–R05 12 负载（`fpu_01..fpu_12.S` + build + disasm） | 旧方案负载，被 5×3 负载取代，归档 |
| `work/FPU_SIMD_5x3_FORMAL/` | 2.3G | **最终 5×3 实验全量产物**（240 正式运行 + 60 count-only + 60 负载 + 报告） | 最终证据主体 |
| `results/` | 2.0G | 旧 156 对 / 312 运行实验结果（R/T/U 方案） | 已超期方案，归档 |
| `runs/` | 32M | pilot/test 试运行（test、test2…、golden_R） | 调试中间产物，清理 |
| `reproduction/` | ~600K | 3+1 个独立复现样本 + `source_changes.patch` + README | 复现证据，保留 |
| `reports/` | ~2M | FPU 补丁、执行摘要、哈希、MMU 完整性、`_excel_dump.txt` | 保留（`_excel_dump.txt` 为本次审计临时产物） |
| `logs/` | ~330K | 编译/阶段日志（build1-5、count_stage、validate 等） | 历史日志，归档 |
| 顶层 tarball 11 个 | ~88M | 各轮交付压缩包（v2–v6、evidence 等） | 归档/去重 |

---

## 3. 多版本实验方案识别（关键）

项目内存在**两代实验方案**，必须区分：

### 3.1 旧方案：R/T/U「156 对 / 312 运行」（已被取代）

- **依据**：Excel `06_Contexts`、`16–22 Legacy_When_*`。
- **范围**：12 模型 × 5 输入变体（R01–R05）+ 新增 T01–T05（10/30/50/70/90%）与 U01/U02/U03；合计 156 对 / 312 正式运行。
- **承载**：`results/`（312 run 目录 + 72 count_only）、`reports/FINAL_EXECUTION_SUMMARY.md`、`experiment.py`、`gen_workloads.py`、`validate_full.py`、`state_proof.py`、`final_audit.py`、`build_propagation.py`、`analyze.py`。
- **终态**：144 SDC + 12 SQUASHED_NOT_COMMITTED（`results/summary.csv` 等）。
- **状态**：已超期（Excel 明确改名 `Legacy_Superseded`，`FPU_5x3_Preflight_Audit.md` 明确“不计入本轮正式实验”）。作为历史证据保留，不作为最终方案复现依据。

### 3.2 最终方案：5×3「180 Fault + 60 Control」（权威）

- **依据**：Excel `24_Context_5x12`、`25_When_5x3_Spec`、`26_When_Fault_Matrix_180`、`27_When_Control_Baselines_60`、`28_When_Workloads_60`、`29_When_Acceptance_Gates`、`30_When_Change_Log`。
- **范围**：12 模型 × 5 上下文（C01–C05）× 3 动态时机（T01/T02/T03 = ceil(10%/50%/90%×N)）= **180 个 Fault 条件 + 60 个 (Model,Context) 控制基线** = 240 正式运行 + 60 count-only 预扫描。
- **承载**：`work/FPU_SIMD_5x3_FORMAL/`（runs 240 + counts 60、runs_r2 96 + counts_r2 24、60 个上下文负载）、`run_5x3.py`、`run_5x3_r2.py`、`gen_5x3_workloads.py`、`analyze_5x3_final_v6.py`。
- **终态**（v6）：180 Fault → 132 WRONG_RESULT + 36 MASKED_OVERWRITE + 12 SQUASHED；60 Control → CONTROL_OK。分类变化 0（v5→v6 无翻转）。
- **状态**：**此为本次收尾的权威最终方案。**

### 3.3 关键裁定（来自 `FPU_5x3_Preflight_Audit.md`，已核实）

- Control 基线按 (ModelID,ContextID) 粒度建立 **60 份**，被 T01/T02/T03 三次复用；
  Excel `26.ControlBaselineID` 的 `-Txx-CTRL` 后缀为旧命名工件，统一映射 `CTRL-FPU-Mxxx-Cxx`。
- 旧 312-run 统计**不适用**；最终正式规模为 **240 次运行**（不含 count-only）。

---

## 4. 12 故障模型 × Hook 对应关系（源码已核实）

| Model | 故障语义（Excel 02_Models） | 目标指令 | Hook 位置 | `fpu_fi::active(N)` |
|---|---|---|---|---|
| M001 | FADD 舍入控制误选（RNE→RTZ） | `FADD Sd,Sn,Sm` | `src/arch/arm/insts/fplib.cc` `fplibAdd` L3380 | active(1) |
| M002 | FMUL 符号合成漏置 | `FMUL Sd,Sn,Sm` | `fplib.cc` `fp32_mul` L2064 | active(2) |
| M003 | FMADD 累加项丢失 | `FMADD Sd,Sn,Sm,Sa` | `fplib.cc` `fplibMulAdd` L3927 | active(3) |
| M004 | FDIV 规格化后指数少 1 | `FDIV Sd,Sn,Sm` | `fplib.cc` `fp32_div` L2747 | active(4) |
| M005 | FSQRT 负数域检查漏报 | `FSQRT S0,S1` | `fplib.cc` `fp32_sqrt` L3032 | active(5) |
| M006 | FCVTZS 固定小数位参数误置 | `FCVTZS Xd,Sn` | `fplib.cc` `FcvtFpSIntXZS` L6698 | active(6) |
| M007 | FCMP 有序操作数角色互换 | `FCMP Sn,Sm→CSEL` | `fplib.cc` `fplibCompare` L3443 | active(7) |
| M008 | UQADD 单 lane 饱和结果漏替换 | `UQADD Vd.16B,...` | `isa/insts/neon64.isa` `UqaddQX` L3691 | active(8) |
| M009 | UMULL 扩宽乘积高字节丢失 | `UMULL Vd.8H,...` | `neon64.isa` `UmullX` L2580 | active(9) |
| M010 | USHL 负移位方向误读 | `USHL Vd.16B,...` | `neon64.isa` `UshlQX` L3373 | active(10) |
| M011 | TBL 越界索引别名为表内索引 | `TBL Vd,{Vn},Vm` | `neon64.isa` `Tbl1QX` L998 | active(11) |
| M012 | XTN2 保留低半区的合并丢失 | `XTN2 V0.16B,V1.8H` | `neon64.isa` `Xtn2X` L531 | active(12) |

12/12 模型已核实为 `SOURCE_LOCAL` 语义局部注入，`MaxApplications=1`，与 Excel
`02_Models`/`04_InjectionConfig` 完全一致。注入驱动/证据记录统一在
`src/cpu/o3/FPUInjector.cc`（473 行，静态 PC + 动态 ordinal 命中，`FI_*` 环境变量按 run 配置），
O3 生命周期埋点（rename/issue/writeback/commit/squash/branch）接线于
`dyn_inst.cc`/`rename.cc`/`inst_queue.cc`/`iew.cc`/`commit.cc`（共 10 处 `fpu_fi::trace_*`/`begin_exec`/`end_exec`）。

### 4.1 FPU 补丁文件清单（12 个源码文件）

新增：`src/arch/arm/fpu_fi.hh`、`src/cpu/o3/FPUInjector.hh`、`src/cpu/o3/FPUInjector.cc`
修改：`src/arch/arm/isa.hh`、`src/arch/arm/insts/fplib.cc`、`src/arch/arm/isa/insts/neon64.isa`、
`src/cpu/o3/SConscript`、`src/cpu/o3/dyn_inst.cc`、`src/cpu/o3/rename.cc`、
`src/cpu/o3/inst_queue.cc`、`src/cpu/o3/iew.cc`、`src/cpu/o3/commit.cc`

补丁全文：`reports/source_changes.patch`（= `reproduction/source_changes.patch`，28,691B，两者 diff 无差异）。
版本指纹：`reports/source_and_binary_hashes.txt` 记录 `fpu_fi.hh`、`FPUInjector.cc`、`gem5.opt` 的 SHA256。

### 4.2 预存在的 CHAOS 注入器（非本次产物）

`gem5/src/cpu/o3/CHAOSFPU/`、`gem5/src/cpu/o3/CHAOSExec/`（各 4 文件）是先前战役的
主动注入器，`dyn_inst.cc` 仍保留其 include。本次 FPU 实验以 `FI_*` 环境变量驱动、
默认关闭，与旧注入器互不影响。**保留不动**（属 gem5 基线内容，非本单元清理范围）。

---

## 5. 脚本清单（最终 vs 已超期）

| 脚本 | 行数 | 归属 | 处置 |
|---|---|---|---|
| `gen_5x3_workloads.py` | 431 | **最终**：生成 60 个 5×3 上下文负载 | 保留 |
| `run_5x3.py` | 338 | **最终**：5×3 count→formal→validate 主驱动 | 保留 |
| `run_5x3_r2.py` | 154 | **最终**：R2 修订（C03/C05 重跑，写入 runs_r2） | 保留 |
| `analyze_5x3_final_v6.py` | 572 | **最终**：最终统计口径/生产者映射（读 runs+runs_r2） | 保留 |
| `parse_records.py` | 22 | 通用 128B 记录解析器 | 保留 |
| `analyze_5x3_final.py`/`_v2.._v5.py` | 347–511 | 分析器 v1–v5 修订（已被 v6 取代） | 归档（v6 报告要求保留 v1–v5，但非复现必需，移入 evidence） |
| `analyze_5x3.py` / `analyze_5x3_r2.py` | 191/273 | R1/R2 早期分析 | 归档 |
| `experiment.py` | 294 | 旧 156 对驱动 | 归档 |
| `gen_workloads.py` | 505 | 旧 R01–R05 12 负载生成 | 归档 |
| `analyze.py` | 82 | 旧方案分析 | 归档 |
| `validate_full.py` / `state_proof.py` / `final_audit.py` / `build_propagation.py` | 65/50/45/178 | 旧 156 对校验/U 状态证明/终审/传播链 | 归档 |

---

## 6. 5×3 上下文与动态时机实现（源码级核实）

**C01–C05**（`gen_5x3_workloads.py` 的 `body_C01..C05` + Excel `24_Context_5x12`）：
- **C01 Baseline Activation**：R03 输入 + 最短激活→执行→单消费者路径。
- **C02 Activation Variation**：不同 producer 链（`mov+lsl+add` 或 `*_data` 表）构造逐位相同的 R03。
- **C03 Limited Dependency**：目标结果产生后立即被覆盖（标量 `fmov s0,#1.0` / GPR `mov x0,#0` / FCMP `cmp xzr,xzr` / 向量 `movi v0.16b,#0`），随后写正确路径哨兵 0x12345678 → 观测 MASKED_OVERWRITE（36 个正是 C03）。
- **C04 Extended Dependency**：≥2 级 RAW 链（`chain` 3 条）+ 多消费者（final/mid）。
- **C05 Control & Speculation**：TRAIN=40 次训练 branch，命中后测量期最后 1 次（ordinal=ceil(0.9N)）执行在 mispredict 窗口内被 squash（12 个 SQUASHED 正是 C05 的 T03）。

**T01/T02/T03**（`run_5x3.py`/`run_5x3_r2.py` 的 `ordinal=ceil(N×q)`）：
- count-only 预扫描 60 组，得每个 (ModelID,ContextID) 的 eligible N。
- `T01=ceil(0.10N)`、`T02=ceil(0.50N)`、`T03=ceil(0.90N)`；门槛 N≥3 且三 ordinal 互异。
- Count-only manifest：`work/.../FPU_5x3_CountOnly_Manifest.csv` + `counts/manifest.json`（60 组 READY）。
- 三个时机仅改动态 eligible 序号，不改 fault 语义/输入/ROI/FP 状态。

---

## 7. 证据与复现材料位置

### 7.1 最终 5×3 证据（主体，2.3G）
- `work/FPU_SIMD_5x3_FORMAL/runs/<RunID>/events.jsonl`（240）— 原始 O3 生命周期 Trace
- `work/.../runs_r2/`（96）— R2 修订（C03/C05）
- `work/.../counts/`（60）+ `counts_r2/`（24）— count-only 预扫描 Trace
- `work/.../FPU_5x3_Run_Manifest.csv`（240 行）、`FPU_5x3_Full_Statistics.csv`、`FPU_5x3_Trace_Index.csv`
- `FPU_5x3_Causal_Edges_Final_v6.csv`（4453 边）、`FPU_5x3_Propagation_Evidence_Final_v6.csv`（180 行）、`FPU_5x3_Propagation_Summary_Final_v6.json`
- `FPU_5x3_Final_Acceptance_Report_v6.md`、`FPU_5x3_Final_Graph_Validation_Report_v4.md` 等报告

### 7.2 旧方案证据（历史，2.0G）
- `results/runs/`（312）、`results/count_only_runs/`（72）、`results/events.jsonl.gz`、`prop_trace.csv.gz`、`summary.csv`、`control_match.csv`、`validation_full.json`、`state_proof.json`、`terminal_classification.json`、`final_audit.json`

### 7.3 复现样本
- `reproduction/`：M005-R04、M008-T03、M012-U03（+rerun）3+1 个独立复现；`reproduce_sample.sh`、`README.md`、`reproduction_results.json`、`source_changes.patch`

### 7.4 版本绑定
- `reports/source_and_binary_hashes.txt`、`reports/source_changes.patch`、`reports/FINAL_EXECUTION_SUMMARY.md`、`reports/MMU_INTEGRITY.md`、MMU pre/postflight 清单

---

## 8. 初步清理建议（待 Phase 2 核对后执行）

### 可清理 / 归档（不属最终复现路径）
1. `gem5/build/`（9.5G）——编译中间产物，复现时 `scons` 重编。
2. `runs/`（test/test2…/golden_R，32M）—— pilot 调试。
3. 旧 156 对方案脚本 + `workloads/`（R01–R05）+ `results/`（2.0G）—— 已被 5×3 取代，归档进证据包。
4. 中间修订产物：`analyze_5x3_final.py`/`_v2.._v5`、`FPU_5x3_*_v1..v5.*`、`Causal_Edges_Final(_v2..v5).csv`、`Propagation_*_v1..v5`。
5. 顶层中间 tarball（`*_Graph_Validation_v2/v3`、`*_Acceptance_v5`、`*_FORMAL_*`、`*_evidence_round2` 等）。
6. `logs/`（330K 历史日志）、`scripts/__pycache__/`。

### 必须保留（复现 + 可追溯）
1. `gem5/src/**` FPU 补丁 12 文件 + `reports/source_changes.patch` + 哈希清单。
2. `inputs/*.xlsx`（权威 Excel）。
3. `scripts/{gen_5x3_workloads,run_5x3,run_5x3_r2,analyze_5x3_final_v6,parse_records}.py`。
4. `work/FPU_SIMD_5x3_FORMAL/workloads/{src,build}`（60+60）。
5. 最终证据（§7.1，含 v6 全部交付物 + 240/96 运行 Trace）—— 若体量过大的原始 Trace 不入代码仓库，则整体归档进证据包并保留 SHA256。
6. `reproduction/`（复现样本）+ 官方复现说明。

### 不得破坏
- `/home/sdc/gem5-fi-ding`、`/home/sdc/gem5-fi-mmu*`（只读，零写入，MMU pre/post SHA 一致）。
- 最终故障模型语义、5×3 设计、原始 Trace/传播链/因果图。
- remote 上 `main`/`mmu-final`/`lsu`/`IEX` 等既有分支。

---

## 9. 已识别风险

1. **无 Git 历史**：本地非 git 仓库，FPU 分支需从“核验过的最终代码基线”新建并一次性提交。
2. **M005/M012 目标 commit 精确行号**：Excel 标注 `TARGET_COMMIT_RECHECK_REQUIRED`；公开参考已确认调用链语义，本机源码锚点已验证，但逐行号复核仍待办（不阻塞，需在最终报告注明）。
3. **M011 传播子图不完整**：32 条 phys 不匹配边 + 1665 全局 UnresolvedProducer（向量 64-bit 子寄存器现象），已如实标 UNKNOWN，不改变 132/36/12 终态。
4. **`nm` 工具链**：本机仅 `aarch64-linux-gnu-gcc`，无 `aarch64-linux-gnu-nm/objdump`（宿主 `nm` 为 x86_64，不可读 AArch64 ELF）；复现时目标 PC 定位需补齐 binutils 或改用已存 disasm/manifest。
5. **Git 直连**：需 `http.version=HTTP/1.1`，否则 `git` 操作挂起。

---

*本报告为 Phase 1 交付物。后续 Phase 2–7 会在项目内追加 `FPU_FINAL_DIRECTORY_STRUCTURE.md`、`FPU_FINAL_REPRODUCIBILITY_AUDIT.md`、`FPU_FINAL_GIT_RELEASE_REPORT.md`。*