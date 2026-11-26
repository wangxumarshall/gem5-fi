# FPU/SIMD 5×3 正式故障注入实验 — Preflight Audit (Phase 1)

- 批次标识：`FPU_SIMD_5x3_FORMAL`
- 生成时间：2026-11-23
- 权威方案：`inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx`
- 工作目录：`/home/sdc/gem5-fi-fpu`
- 状态：**Phase 1 完成，Ready Gate 检查中**

---

## 1. 权威 Excel 结构核对

Excel 共 30 张工作表。本轮正式依据为 24–30 号工作表；16–22 号已重命名为
`Legacy_Superseded`，仅作历史审计。

| 工作表 | 行数 | 结论 |
|---|---|---|
| 00_Overview | 37 | 仍含旧 R/T/U 312-run 描述（已标记需以 24–30 为准） |
| 02_Models | 12 模型 | FPU-M001..M012 语义冻结 |
| 03_SourceAudit | 16 项 | M005/M012 目标 commit 精确行号待复核 |
| 04_InjectionConfig | 12 CFG01 | ONE 模式，MaxApplications=1，冻结 |
| 24_Context_5x12 | 60 | 12 模型 × 5 上下文（每模型恰好 5 行）✅ |
| 25_When_5x3_Spec | T01/T02/T03 | 10%/50%/90%，`ordinal=ceil(q×N)` ✅ |
| 26_When_Fault_Matrix_180 | 180 | 180 个唯一 FaultSampleRunID ✅ |
| 27_When_Control_Baselines_60 | 60 | 60 个唯一 ControlBaselineID ✅ |
| 28_When_Workloads_60 | 60 | 60 个 ContextWorkloadID（FPU-Wxx-Cxx）✅ |
| 29_When_Acceptance_Gates | 12 gate | W5X3-01..12 ✅ |
| 30_When_Change_Log | 4 | 5×3 统一、上下文语义、动态时机定义 ✅ |

**核对结论**：24–28 号工作表的行数满足 12×5=60、12×5×3=180、12×5=60 的设计口径。

---

## 2. 关键表格引用歧义（已解决，需记录）

**问题**：`26_When_Fault_Matrix_180.ControlBaselineID` 使用
`FPU-M001-C01-T01-CTRL` 命名（180 个唯一值，每 fault 一个），而
`27_When_Control_Baselines_60.ControlBaselineID` 使用 `CTRL-FPU-M001-C01`
命名（60 个唯一值，每 (ModelID,ContextID) 一个）。二者命名不一致。

**权威裁决依据**：
- `24_Context_5x12.ControlBaselineRule`：*“同一 (ModelID,ContextID) 的
  T01/T02/T03 共用一份已验证 no-fault baseline；三时机只改变
  eligible-event ordinal”*。
- `27.MatchingRequirement`：*“与同一 (ModelID,ContextID) 的 T01/T02/T03 使用
  完全相同程序、输入、ROI、FP 状态、checkpoint、二进制与参数”*。
- `29.W5X3-06`：*“每个 (ModelID,ContextID) 有一份控制基线，三时机复用前先
  验证 hash/输入/ROI 完全匹配”*。

**裁决**：控制基线按 (ModelID,ContextID) 粒度建立，共 **60 份**，每份被其
三个动态时机复用。`26.ControlBaselineID` 的 `-Txx-CTRL` 后缀为旧设计遗留命名
工件，统一映射为 `CTRL-FPU-Mxxx-Cxx`。复用合法性由以下事实保证：控制运行不
注入故障，三个时机仅改变“被选中的 eligible 动态序号”，程序/输入/ROI/FP 状态
完全一致，因此同一控制轨迹可对齐三个目标序号。

---

## 3. 最终运行数量 Manifest

| 类别 | 数量 | 说明 |
|---|---|---|
| Fault 候选条件 | 180 | 12 模型 × 5 上下文 × 3 时机 |
| Control 基线 | 60 | 12 模型 × 5 上下文（三时机复用） |
| **正式运行合计** | **240** | 180 Fault + 60 Control |
| Count-only 预扫描 | 60 | 每 (ModelID,ContextID) 一次无故障计数 |

**明确结论**：旧 312-run 统计不适用；本轮最终正式规模为 **240 次运行**，
不计 count-only 预扫描。

---

## 4. 故障模型冻结核对（不得修改）

12 个故障模型 FaultMechanism / TargetInstruction / SourceLocationID /
FaultConfigID / Hook / Fault Mode / 故障操作 / EligibleEventCondition 全部保持
冻结，本轮只改变执行上下文与动态注入时机。核对结果：

| ModelID | FaultMechanism | Hook 位置（源码） | 状态 |
|---|---|---|---|
| FPU-M001 | FADD 舍入控制误选 | fplib.cc `fplibAdd` rMode | ✅ 存在 |
| FPU-M002 | FMUL 符号合成漏置 | fplib.cc `fp32_mul` x_sgn | ✅ 存在 |
| FPU-M003 | FMADD 累加项丢失 | fplib.cc `fplibMulAdd` addend | ✅ 存在 |
| FPU-M004 | FDIV 规格化后指数少 1 | fplib.cc `fp32_div` x_exp | ✅ 存在 |
| FPU-M005 | FSQRT 负数域检查漏报 | fplib.cc `fp32_sqrt` negative_domain | ✅ 存在（行号待复核） |
| FPU-M006 | FCVTZS 固定小数位参数误置 | fplib.cc `FcvtFpSIntXZS` fbits | ✅ 存在 |
| FPU-M007 | FCMP 有序操作数角色互换 | fplib.cc `FcmpRegS` cOp 顺序 | ✅ 存在 |
| FPU-M008 | UQADD 单 lane 饱和结果漏替换 | neon64.isa `UqaddQX` saturate | ✅ 存在 |
| FPU-M009 | UMULL 扩宽乘积高字节丢失 | neon64.isa `UmullX` high_byte | ✅ 存在 |
| FPU-M010 | USHL 负移位方向误读 | neon64.isa `UshlQX` shift_direction | ✅ 存在 |
| FPU-M011 | TBL 越界索引别名为表内索引 | neon64.isa `Tbl1QX` index_alias | ✅ 存在 |
| FPU-M012 | XTN2 保留低半区的合并丢失 | neon64.isa `Xtn2X` old_dest_low | ✅ 存在（old-dest 依赖待复核） |

**注意**：M005 与 M012 在 SourceAudit 中标注
`PUBLIC_REFERENCE_CONFIRMED_TARGET_COMMIT_RECHECK_REQUIRED`。本轮在本机核对
实际源码锚点（见 §5），确认注入点在当前源码树内与语义一致；精确到目标 commit
逐行号仍按 Excel 要求保持“待复核”，但**不阻塞实现**，因为语义调用链已在当前
源码树得到验证。

---

## 5. 源码与环境核对

- 工作目录：`/home/sdc/gem5-fi-fpu` ✅
- 参考基线 commit：`226778cf7d71e5cd47c8153fe7ef4eeabf82b858`
  - 只读参考树 `/home/sdc/gem5-fi-ding` HEAD = `226778cf`（匹配）✅
  - 当前工作树 `/home/sdc/gem5-fi-fpu/gem5` 为该 commit 的拷贝 + FPU 故障注入
    修改（非 git 仓库，无 `.git`）。
- gem5 二进制：`gem5/build/ARM/gem5.opt`（2026-11-16 16:22 构建，含 FPU hooks）。
- 12 个模型的语义 hook 均已在当前源码树验证存在（`fplib.cc` 8 处、
  `neon64.isa` 4 处），O3 生命周期埋点（rename/issue/writeback/commit/squash/
  branch）已接线于 `dyn_inst.cc` / `rename.cc` / `inst_queue.cc` / `iew.cc` /
  `commit.cc`，由 `cpu/o3/FPUInjector.cc` 统一驱动，经 `fpu_fi` 接口连接。
- 注入机制：静态 PC + 动态 ordinal 命中；`FI_ENABLE`/`FI_COUNT_ONLY`/
  `FI_MODEL`/`FI_PC`/`FI_ORDINAL`/`FI_LANE`/`FI_TRACE` 等环境变量按 run 配置。
- 12 个 workload ELF 均为 AArch64 静态可执行，目标符号 `fpu_target_r` 已定位。

**冒烟测试**（count-only，fpu_01，token `3T`）：目标 PC `0x400264`，eligible
事件 N=128，trace 事件（rename/target_begin/target_end/commit 等）正常生成，
run_end 记录 eligible_total/applied_total。工具链端到端可用。✅

---

## 6. 五个上下文与现有负载的差距（Phase 2 关键工作）

现有 12 个 workload（`workloads/src/fpu_*.S`）仅实现 **单目标指令 + 单消费者 +
5 种输入变体（R01–R05）**，其 T 模式循环 128 次仅用于旧 T01–T05 分位。它**不
能**直接满足新的 C01–C05 上下文语义：

| Context | 语义要求 | 现有负载是否满足 |
|---|---|---|
| C01 Baseline Activation | 最短激活—执行—消费 | 接近（单消费者），可复用骨架 |
| C02 Activation Variation | 不同 producer 链生成逐位相同的 R03 | ❌ 需新构造 |
| C03 Limited Dependency | 结果被覆盖/未消费 + 正确路径哨兵 | ❌ 需新构造 |
| C04 Extended Dependency | ≥2 级 RAW 依赖/多消费者 | ❌ 需新构造 |
| C05 Control & Speculation | 真实 mispredict 窗口，execute→squash/commit | 部分（U3 骨架可参考），需重做 |

**Phase 2 计划**：为每个 (ModelID,ContextID) 生成独立 ELF（共 60 个），命名
`fpu_<MM>_C<cc>`。目标静态 PC 相同（同一 `fpu_target_r`），但上下文构造不同。
每个 workload 在 ROI 内循环目标指令 N 次（N 设计为 100，保证 T01/T02/T03 =
10/50/90 三个 ordinal 两两不同），并在每次迭代写出独立 output slot。

---

## 7. Count-only 预扫描与动态时机

- 对每个 (ModelID,ContextID) 执行一次无故障 count-only。
- 统计 ROI 内合格动态事件总数 N。
- `T01 = ceil(0.10×N)`、`T02 = ceil(0.50×N)`、`T03 = ceil(0.90×N)`。
- 门槛：N≥3 且三个 ordinal 两两不同；否则标记 BLOCKED（保留预扫描证据）。
- 三个时机用相同的 fault model / hook / 输入 / 错误操作，仅 ordinal 变化，
  各自从相同初始状态独立运行。

---

## 8. Ready Gate 判定（29_When_Acceptance_Gates）

| Gate | 要求 | 当前状态 |
|---|---|---|
| W5X3-01 MODEL_PRESERVATION | 12 模型/CFG01/Hook 完全保留 | ✅ 已核对 |
| W5X3-02 CONTEXT_COVERAGE | 60 行，每模型 5 上下文 | ✅ 已核对 |
| W5X3-03 TIMING_COVERAGE | 180 行唯一 | ✅ 已核对 |
| W5X3-04 ELIGIBLE_COUNT | N≥3、ordinal 互异 | ⏳ 待 count-only（Phase 3） |
| W5X3-05 SAME_FAULT_SEMANTICS | 三时机配置一致 | ⏳ 待 manifest 生成 |
| W5X3-06 CONTROL_MATCH | 60 控制基线，复用前验证 hash/输入/ROI | ⏳ 待 Phase 4 |
| W5X3-07 FAULT_CONTROL_COUNTS | fault=1/control=0 | ⏳ 待 Phase 4 |
| W5X3-08 C05_SPECULATION | 真实 mispredict | ⏳ 待 Phase 2 负载 |
| W5X3-09 C03_MASKING | 证明已激活但未消费/被覆盖 | ⏳ 待 Phase 2 负载 |
| W5X3-10 SIMD_LANE | M008–M012 lane 级证据 | ⏳ 待 Phase 4 |
| W5X3-11 TRACE_COMPLETENESS | 完整因果链 | ⏳ 待 Phase 4 |
| W5X3-12 OUTCOME_CLASSIFICATION | 不预设终态 | ⏳ 待 Phase 4 |

---

## 9. 服务器隔离与历史数据保护

- 只读目录：`/home/sdc/gem5-fi-ding`、`/home/sdc/gem5-fi-mmu*`（ISO-01..07）——
  本轮**零写入**。
- 历史 FPU 结果（`results/`、`runs/`、`reports/`、`reproduction/`）**保留不删、
  不覆盖**。旧实验仅作历史参考，不计入本轮正式实验。
- 本轮全部输出写入 `work/FPU_SIMD_5x3_FORMAL/`（含 `runs/`、`counts/`、
  `workloads/`、`reports/`），与旧数据物理隔离。

---

## 10. 未解决问题 / 风险

1. **M005/M012 目标 commit 精确行号未复核**：公开参考已确认调用链语义，当前
   源码树注入锚点已验证；逐行号复核标记为待办（不阻塞实现，但最终报告需注明）。
2. **C05 上下文**：需构造真实分支预测 mispredict 窗口；若某模型在该上下文无法
   稳定获得合格事件，将按 B 类问题隔离并 BLOCKED，不伪造 squash。
3. **控制基线复用**：三个时机复用同一控制运行，需在 Phase 4 明确记录基线 hash
   与三次配对证据，避免误计为 180 个控制运行。

---

## 11. 下一步（Phase 2）

1. 生成 60 个上下文 workload 源码与 ELF（`fpu_<MM>_C<cc>`）。
2. 验证每个 workload 反汇编：目标 opcode、寄存器、lane、依赖与 Excel 一致。
3. 对每个 (ModelID,ContextID) 做 smoke count-only，确认 N≥3 与 target 命中。
4. 通过后进入 Phase 3 全量 count-only 预扫描。

*本文件为 Phase 1 交付物；后续各阶段完成后会在 `work/FPU_SIMD_5x3_FORMAL/`
内追加阶段报告与最终报告。*
