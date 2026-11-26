# FPU/SIMD 最终 Git 发布报告 (FPU_FINAL_GIT_RELEASE_REPORT.md)

**发布时间**：2026-11-26

---

## 1. 仓库与分支

| 项 | 值 |
|---|---|
| GitHub 仓库 | https://github.com/wangxumarshall/gem5-fi |
| 目标分支 | `FPU` |
| 分支地址 | https://github.com/wangxumarshall/gem5-fi/tree/FPU |
| Git remote (origin) | `https://github.com/wangxumarshall/gem5-fi` |
| 本地 HEAD | `7012567e7827f7a802281d783fd063700cc1b4d4` |
| 远端 HEAD | `7012567e7827f7a802281d783fd063700cc1b4d4`（一致 ✅） |
| Commit Message | `Finalize FPU/SIMD fault injection experiments (12 models, 5 contexts, 3 timings)` |
| 推送结果 | ✅ 成功（`[new branch] FPU -> FPU`，`PUSH_EXIT: 0`） |
| Force push | 否 |
| 修改/覆盖其他分支 | 否（main/mmufinal/lsu/IEX 均未改动，见 §3） |

## 2. 发布内容

FPU 分支为**自包含**的最终代码基线（全新独立分支，因基线 commit
`226778cf…` 不在远端、且本地工作副本无 Git 历史）：

```
gem5/           gem5 源码树（基线 226778cf + FPU 补丁，无 build/）
inputs/         权威 Excel
scripts/        5 个最终脚本（gen_5x3_workloads / run_5x3 / run_5x3_r2 /
                analyze_5x3_final_v6 / parse_records）
reports/        source_changes.patch + 二进制/源码哈希 + MMU 完整性
docs/           REPRODUCE.md
work/FPU_SIMD_5x3_FORMAL/   最终 v6 交付物 + 60 负载 + count manifests
FPU_PRE_CLEANUP_AUDIT.md / FPU_FINAL_DIRECTORY_STRUCTURE.md /
FPU_FINAL_REPRODUCIBILITY_AUDIT.md / FPU_FINAL_GIT_RELEASE_REPORT.md
```

- 提交文件数：10429（gem5 10269 + work 146 + scripts 5 + reports 3 + 其他 6）
- 提交行数：+2,341,016
- 无大体积中间文件（无 >10M 文件）、无密钥/令牌（secret scan 干净）
- `gem5/build/`、`m5out/`、`__pycache__` 已从工作树删除，`.gitignore` 排除其复现产物

## 3. 分支完整性核对（发布后）

| 分支 | HEAD | 状态 |
|---|---|---|
| FPU | `7012567e7827f7a802281d783fd063700cc1b4d4` | 新建 ✅ |
| main | `f104bd830ddb892c20b54047b5e820ebe9430a73` | 未改动 ✅ |
| mmu-final | `0bcfda1eef295614ae4d8d6bfb6a2e5738798bb4` | 未改动 ✅ |
| lsu | `e52f7ab1453efbebc3ae5e82a8edfd523c9c58d1` | 未改动 ✅ |
| IEX | `52c29ca7794821e0c1a8e72930e1c39e75e47182` | 未改动 ✅ |

工作区状态：`git status --porcelain` 为空（clean ✅）。

## 4. 发布说明（异常与注意事项）

1. **本地无 Git 历史**：`gem5-fi-fpu` 原为无版本控制的工作快照，本次在清理后的
   最终树内 `git init` 并一次性提交为独立 `FPU` 分支。
2. **网络**：`git` 直连需 `http.version=HTTP/1.1`（HTTP/2 下 `git-upload-pack` 握手挂起）；
   已在本地 git config 固化。
3. **`git remote`**：`origin = https://github.com/wangxumarshall/gem5-fi`（与任务要求一致）。
4. **未推送内容**：`gem5/build/`（9.5G 复现中间产物）、原始实验 Trace（2.3G）与已超期
   156 对结果（2.0G）等证据文件，单独归档于证据包（见 Phase 7），不进代码分支。

## 5. 目录 / 清理 / 复现 / SHA256

- 最终目录路径：`/home/sdc/gem5-fi-fpu`
- 清理统计：保留 127M；归档证据 4.4G（`/home/sdc/gem5-fi-fpu-evidence/`）；删除 `gem5/build/` 9.5G
- 复现验证结果：见 `FPU_FINAL_REPRODUCIBILITY_AUDIT.md`（12×5×3 枚举、钩子覆盖、
  ordinal 公式、负载交叉编译、记录解析全部 PASS；gem5 运行未重跑、已如实声明）

## 6. 交付包 SHA256

| 交付包 / 关键文件 | SHA256 |
|---|---|
| `FPU_FINAL_CODE_RELEASE_PACKAGE.zip` | `dd273c7a935df49c1ac474e8b744f4196cc34ea6511f8544a959167c0568b230` |
| `FPU_FINAL_EXPERIMENT_EVIDENCE_PACKAGE.zip` | `9fe5eebb8bc7aa3292d9896d29a3edf46797af185cd162f0b1cf980d0a091391` |
| `reports/source_changes.patch` | `0d96e7fddfc2f1ee1de9a4331fe0f3336f562b19b5fa84f36d9c82f16524da32` |
| `inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx` | `1484dbbb94420dd8a65071c80e0c9a52262355d6f697286976315af161f9b140` |
| `gem5/src/arch/arm/fpu_fi.hh` | `99583266772bcceeb33f75a3bf5a34485e9296a09483cffae635fe20a658a502` |
| `gem5/src/cpu/o3/FPUInjector.hh` | `0a380ba464b655928e4c78525c4485beba937d44adf5a4431dc0de4acf230594` |
| `gem5/src/cpu/o3/FPUInjector.cc` | `327d4467cdab218853eaff136f66b00a1b9346f971bb4478a6c3e0eb6359d2f1` |

> 注：`fpu_fi.hh` 与 `FPUInjector.cc` 的 SHA256 与实验期记录的 `reports/source_and_binary_hashes.txt`
> **完全一致**，证明最终发布代码与正式实验所用源码字节相同。

交付包绝对路径：
- `/home/sdc/gem5-fi-fpu/FPU_FINAL_CODE_RELEASE_PACKAGE.zip`（27.4 MB，12776 项）
- `/home/sdc/gem5-fi-fpu/FPU_FINAL_EXPERIMENT_EVIDENCE_PACKAGE.zip`（367 MB，22069 项，未压缩 4.59 GB）

---

*本报告为 Phase 6 交付物。*