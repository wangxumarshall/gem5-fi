# FPU/SIMD 最终复现验证审计 (FPU_FINAL_REPRODUCIBILITY_AUDIT.md)

**审计时间**：2026-11-26
**范围**：代码级 + 流程级复现验证（不重跑 180 个 Fault 实验）
**结论**：12×5×3 = 180 Fault + 60 Control 的代码与流程可复现；静态检查与轻量 dry-run 全部通过；gem5 二进制未重跑（见 §4 说明）。

---

## 1. 逐项验证清单（对照任务要求）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 12 个故障模型可配置/识别 | ✅ PASS | 源码 `fpu_fi::active(1..12)` 覆盖 1–12，无遗漏 |
| 2 | 每模型 C01–C05 配置 | ✅ PASS | `gen_5x3_workloads.py` 生成 60 个 `fpu_<MM>_<Cxx>`；Excel `24_Context_5x12` 60 行 |
| 3 | 每模型 T01/T02/T03 | ✅ PASS | `run_5x3.py` 枚举 3 时机；`25_When_5x3_Spec` 10/50/90% |
| 4 | 预扫描 + ordinal 选择逻辑 | ✅ PASS | `count_stage` 计算 `ceil(N×q)`；count manifest 60 行全部 READY、ordinal 两两不同、N≥3 |
| 5 | Fault/Control 配置生成 | ✅ PASS | `load_manifest()` 240 任务（180 fault + 60 control），SID 唯一；fault 注入 ordinal、control `FI_ENABLE=0` |
| 6 | 编译入口 + 依赖 | ✅ PASS | `scons build/ARM/gem5.opt`；`reports/source_changes.patch` 新增 `SConscript` 条目 |
| 7 | Trace 采集入口 | ✅ PASS | `FPUInjector.cc` 的 `trace_rename/issue/writeback/commit/squash/branch` + `target_begin/end` |
| 8 | 传播链输出入口 | ✅ PASS | `analyze_5x3_final_v6.py` 产出 Causal_Edges/Propagation_Evidence |
| 9 | 轻量 dry-run / 现有测试 | ✅ PASS | 见 §2（负载生成/编译、记录解析、枚举） |
| 10 | 12×5×3 全部条件可枚举 | ✅ PASS | `load_manifest()` 输出 180 唯一 fault SID + 60 control |

---

## 2. 实际执行的命令与关键输出

### 2.1 源码钩子覆盖（静态）
```bash
$ python3 -c "import re; ... re.findall(r'fpu_fi::active\((\d+)\)', fplib+neon) ..."
active() model numbers in source: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
covers 1..12: True
```
（`fplib.cc` 7 处 active(1..7)，`neon64.isa` 5 处 active(8..12)。）

### 2.2 枚举 dry-run（run_5x3.py）
```bash
$ python3 -c "import run_5x3; m=run_5x3.load_manifest(); ..."
total jobs: 240 | fault: 180 | control: 60
fault SID unique: True
models: [1..12]   ctxs: ['C01'..'C05']   timings: ['T01','T02','T03']
12x5x3 = 180
```

### 2.3 负载生成 + 交叉编译 dry-run
```bash
$ python3 scripts/gen_5x3_workloads.py dump 1 C04 > /tmp/fpu_01_C04.S
$ aarch64-linux-gnu-gcc -nostdlib -static -o /tmp/fpu_01_C04 /tmp/fpu_01_C04.S
COMPILE OK
/tmp/fpu_01_C04: ELF 64-bit LSB executable, ARM aarch64, ... statically linked
```
再生成 C04/C05 与已存源码逐行比对：**内容完全一致**（仅 `print` 与 `f.write` 造成的末尾换行差）。
说明：`gen_5x3_workloads.py` 与已存 `work/FPU_SIMD_5x3_FORMAL/workloads/src/*.S` 同源、可确定性复现。

### 2.4 128B 记录解析（对真实证据 Trace）
```bash
$ python3 scripts/parse_records.py <evidence>/runs/FPU-M001-C01-T01/stdout.txt
<...>/stdout.txt 100
  {'model': 1, 'ctx': 1, 'mode': 5, 'iter': 0, 'raw0': '0x40800006', 'fpsr': '0x10', ...}
  ...
```
解析出 100 条记录，magic/model/ctx/mode/raw0/FPSR 与 `RECORD_FORMAT.md` 定义一致（raw0=0x40800006 为 FADD R03 golden+IXC）。

### 2.5 ordinal 公式核验（count manifest 60 行）
```bash
$ python3 -c "... ceil(0.10N)/ceil(0.50N)/ceil(0.90N) vs q10/q50/q90 ..."
ordinal formula mismatch: 0      all distinct: True      all N>=3: True
```
（60 行 count manifest 全部 READY，N 范围 64–100，三个 ceil ordinal 两两不同。）

### 2.6 Excel 与文件系统交叉核验
```bash
26_When_Fault_Matrix_180: 180 行 unique，== 12x5x3 预期     (MATCH)
27_When_Control_Baselines_60: 60 行 unique，== 12x5 预期    (MATCH)
28_When_Workloads_60: 60 unique
work/.../runs/ : 180 fault + 60 control 目录，与预期集合完全一致
```

---

## 3. 关键复现口径（R1 / R2 装配关系）

最终冻结结果（v6）由两轮运行装配：
- **R1（runs/ + counts/）**：C01/C02/C04 使用 R1 运行；C03/C05 的 R1 版本已被 R2 取代。
- **R2（runs_r2/ + counts_r2/）**：仅 C03/C05 修订负载重跑（见 `FPU_C03_C05_Workload_Revision.md`）：
  - C03：覆盖提前到首次消费之前（标量 `fmov s0,#1.0` / GPR `mov x0,#0` / FCMP `cmp xzr,xzr` / 向量 `movi v0.16b,#0`）。
  - C05：分支/循环结构修订，测量期 `N_C05=9`（8 commit + 1 squash）。R1 C05 N=64/PC=0x4001ac → R2 C05 N=9/PC=0x4001c4。

**复现路径说明**：
- 当前 `gen_5x3_workloads.py` 已生成 R2 修订后的负载（含 C03/C05）。
- 干净复现只需 `run_5x3.py count` + `run_5x3.py formal` 即可得到 240 个用**正确负载**的运行
  （无需再走 R1→R2 的历史两步，`run_5x3_r2.py` 保留用于说明最终结果如何由两轮装配）。
- 冻结分析器 `analyze_5x3_final_v6.py` 按历史布局读取 `runs/` + `runs_r2/`（原始 Trace 已归档至证据包）；
  干净复现时若全部落盘到 `runs/`，需将分析器 `RUNS2` 指向同处（或保留两轮装配布局）。

---

## 4. 未实际执行/无法验证项（如实声明）

1. **gem5 运行未重跑**：清理阶段删除了可复现的编译产物 `gem5/build/`（含 1.2G `gem5.opt`，其 SHA256 已记录于
   `reports/source_and_binary_hashes.txt`）。因此未做单次 gem5 smoke run。复现时需先 `scons build/ARM/gem5.opt`（约数十分钟）。
   —— 本报告的所有 gem5 相关检查为**静态代码检查**，未声称运行成功。
2. **`aarch64-linux-gnu-nm/objdump` 缺失**：本机仅有 `aarch64-linux-gnu-gcc`。驱动用 `nm` 读 `fpu_target_r` 符号；
   复现机需安装 `binutils-aarch64-linux-gnu`，或改用已存反汇编/符号信息。
3. **M005/M012 目标 commit 精确行号**：Excel `03_SourceAudit` 标注 `TARGET_COMMIT_RECHECK_REQUIRED`。
   公开 gem5 参考已确认调用链语义（FSqrtS→fplibSqrt→fp32_sqrt；XTN2 低半区自赋值），本机源码锚点已验证存在，
   但目标 commit `226778cf…` 的逐行号复核为**遗留待办**（不影响复现，最终报告需注明）。
4. **M011 传播子图完整性**：32 条 phys 不匹配边 + 1665 个全局 UnresolvedProducer（gem5 向量指令 64-bit 子寄存器现象），
   已在 v6 分析中如实标 UNKNOWN，不改变 132/36/12 终态（见 `FPU_5x3_Final_Acceptance_Report_v6.md`）。

---

## 5. 冻结结果摘要（供复现对照）

| 指标 | 值 |
|---|---|
| Fault 运行 | 180（12×5×3） |
| Control 基线 | 60（12×5，三时机复用） |
| Count-only | 60（+24 R2） |
| Fault 终态 | 132 WRONG_RESULT + 36 MASKED_OVERWRITE + 12 SQUASHED |
| Control 终态 | 60 CONTROL_OK |
| 分类变化 v5→v6 | 0 |
| 参考基线 commit | `226778cf7d71e5cd47c8153fe7ef4eeabf82b858` |
| 关键二进制 SHA256 | 见 `reports/source_and_binary_hashes.txt` |

*本报告为 Phase 5 交付物。*