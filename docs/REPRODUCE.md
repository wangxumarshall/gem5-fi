# FPU/SIMD 5×3 最终实验复现说明 (REPRODUCE)

本文件描述如何在干净环境复现 FPU/SIMD **最终 5×3 正式实验**（12 故障模型 × 5 上下文 × 3 动态时机）。

- 权威方案：`inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx`（工作表 24–30）
- 故障模型：FPU-M001…M012（12 个，语义冻结，见 `work/FPU_SIMD_5x3_FORMAL/FPU_5x3_Preflight_Audit.md`）
- 最终规模：180 Fault + 60 Control = 240 正式运行 + 60 count-only 预扫描
- 参考基线：gem5 commit `226778cf7d71e5cd47c8153fe7ef4eeabf82b858`

---

## 0. 环境要求

| 依赖 | 说明 |
|---|---|
| 编译器 | gcc/g++（C++17），scons，python3（≥3.8） |
| 交叉工具链 | `aarch64-linux-gnu-gcc`（生成 AArch64 静态 ELF） |
| binutils | `aarch64-linux-gnu-nm` / `objdump`（读 AArch64 符号/反汇编）—— 见 §4 注意 |
| gem5 依赖 | protobuf、zlib 等（见 gem5 `README.md`） |

## 1. 获取 gem5 源码并应用 FPU 补丁

```bash
# 以只读参考树 /home/sdc/gem5-fi-ding 的 commit 为基线：
#   git clone <gem5> && git checkout 226778cf7d71e5cd47c8153fe7ef4eeabf82b858
# 或直接使用本仓库已含补丁的 gem5/ 源码树（无需再打补丁）。

# 从上游基线重建时，应用 FPU 补丁：
git apply reports/source_changes.patch
```

补丁 `reports/source_changes.patch` 新增/修改 12 个文件：
- 新增 `src/arch/arm/fpu_fi.hh`、`src/cpu/o3/FPUInjector.{hh,cc}`
- 修改 `src/arch/arm/isa.hh`、`src/arch/arm/insts/fplib.cc`（M001–M007）、
  `src/arch/arm/isa/insts/neon64.isa`（M008–M012）、`src/cpu/o3/{SConscript,dyn_inst.cc,rename.cc,inst_queue.cc,iew.cc,commit.cc}`

## 2. 构建 gem5

```bash
cd gem5
scons build/ARM/gem5.opt -j$(nproc)
```

二进制路径（脚本默认）：`gem5/build/ARM/gem5.opt`。

## 3. 生成 60 个上下文负载（12 模型 × 5 上下文）

```bash
python3 scripts/gen_5x3_workloads.py
# 产物：work/FPU_SIMD_5x3_FORMAL/workloads/src/fpu_<MM>_<Cxx>.S   (60)
#       work/FPU_SIMD_5x3_FORMAL/workloads/build/fpu_<MM>_<Cxx>   (60 ELF)
```

## 4. 复现实验（count → formal → validate）

```bash
# (a) count-only 预扫描：60 组 (ModelID,ContextID)，得到每组合格动态事件 N
python3 scripts/run_5x3.py count

# (b) 正式 180 Fault + 60 Control
python3 scripts/run_5x3.py formal

# (c) R2 修订重跑（仅 C03/C05 修订负载，写入 counts_r2/runs_r2）
python3 scripts/run_5x3_r2.py count
python3 scripts/run_5x3_r2.py formal

# (d) 完整性 + 配对校验
python3 scripts/run_5x3.py validate
```

运行产物写入 `work/FPU_SIMD_5x3_FORMAL/{counts,runs,counts_r2,runs_r2}/`。
每个 run 目录包含 `stdout.txt`（128B 记录）、`events.jsonl`（O3 生命周期 Trace）、
`summary.json`、`config.ini`、`stats.txt` 等。

## 5. 分析（统计口径 / 生产者映射）

```bash
python3 scripts/analyze_5x3_final_v6.py
# 产物：FPU_5x3_Causal_Edges_Final_v6.csv（因果边）、
#       FPU_5x3_Propagation_Evidence_Final_v6.csv（180 行传播证据）、
#       FPU_5x3_Propagation_Summary_Final_v6.json 等
```

冻结的最终结果（已随仓库保留）见 `work/FPU_SIMD_5x3_FORMAL/` 下 `*_v6.*` 文件：
- 180 Fault 终态：132 WRONG_RESULT + 36 MASKED_OVERWRITE + 12 SQUASHED
- 60 Control：CONTROL_OK

## 6. 注入机制速览

每个 run 通过环境变量配置（见 `src/cpu/o3/FPUInjector.cc`）：

| 变量 | 含义 |
|---|---|
| `FI_ENABLE` | 是否启用一次语义故障 |
| `FI_MODEL` | M001–M012 |
| `FI_PC` | 目标静态 PC（`fpu_target_r`） |
| `FI_ORDINAL` | 1-based 合格动态序号（T 组为 ceil(N×q)） |
| `FI_LANE` | SIMD lane（标量/fcmp 为 -1） |
| `FI_COUNT_ONLY` | 只计数不注入 |
| `FI_TRACE` | O3 生命周期 Trace 输出路径 |
| `FI_STATE` | `NORMAL_COMMIT` / `SPEC_EXEC_SQUASH`（C05） |

动态时机：`T01=ceil(0.10N)`、`T02=ceil(0.50N)`、`T03=ceil(0.90N)`（N 来自 count-only）。

## 7. 注意事项

1. **`nm` 工具链**：本机仅有 `aarch64-linux-gnu-gcc`，无 `aarch64-linux-gnu-nm/objdump`。
   驱动用 `nm` 读 `fpu_target_r` 符号定位 PC。若无 AArch64 binutils，请安装
   `gcc-aarch64-linux-gnu` 或 `binutils-aarch64-linux-gnu`；也可改用
   `aarch64-linux-gnu-gcc -nostdlib` 生成的符号表 / 已存反汇编。
2. **路径**：三个驱动脚本用 `Path(__file__).resolve().parent.parent` 解析项目根，
   可任意目录运行（历史硬编码路径已改为脚本相对定位）。
3. **不重跑全部实验**：本任务只要求代码级/流程级复现验证；正式 240 运行已有冻结
   证据（`work/FPU_SIMD_5x3_FORMAL/` 的 v6 交付物 + `FPU_FINAL_EXPERIMENT_EVIDENCE_PACKAGE`）。
4. **M005/M012 目标 commit 精确行号**：Excel 标注 `TARGET_COMMIT_RECHECK_REQUIRED`；
   公开参考已确认调用链语义、本机源码锚点已验证，逐行号复核为已知待办（不影响复现）。
