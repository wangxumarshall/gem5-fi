# RF/WB reproducible fault-injection project

本目录是 gem5-fi 中 RF/WB（Register File / Writeback）故障注入实验的最终
可复现代码与材料。它只包含复现 5 个故障模型 × 5 个执行上下文 × 3 个动态
执行时机所需的内容；历史 Trace、完整批次结果和旧版本压缩包不在本目录。

本项目的实验设计已冻结：**75 个 Fault 条件 + 25 个 Control 条件**。本轮
发布不重新设计、不重新执行完整实验，也不改变任何故障语义。

- 实际源码基线：`2f4e00b434ec8690fbb8cb6965e435094de7e784`
- 源码树：`f34ae2d1e8f002c03e919218ef4f2c00e40b0a95`
- 注入补丁：`src/RF_WB_Source_Injection_Final.patch`
- 补丁 SHA256：`87c8968fe1e555db97fc8b5e735e6e975fdafa1e9f867732789d9e5822f8e60a`
- 历史设计基线 `226778cf`：`NOT_RECOVERABLE`，不是源码基线。

---

## 1. 项目介绍

RF/WB 研究的是 AArch64 乱序核中寄存器堆（PRF）、寄存器读端口（read port）、
写回完成通知（writeback completion）和全局 ready 状态发生硬件故障时，错误
是否被掩盖、被 squash，或传播为软件可见的 SDC。实验在 gem5-fi 的 O3 模型上
通过一个统一的最小注入器 `RFWB` 完成：同一二进制通过环境变量选择模型、模式
和动态事件序号。

实验边界是 **RF/WB 单元**，不涉及 LSU、MMU、BPU、Cache 等其他单元的故障
模型。gem5-fi 基线中的其他单元代码只是构建依赖，不是本实验的注入对象。

---

## 2. 目录结构

```text
.
├── README.md
├── inputs/
│   └── gem5-fi-RF_WB-Final-Paper-Experiment-Plan.xlsx   # 权威实验设计（25 sheets）
├── configs/
│   ├── targets.tsv                    # 25 个模型/上下文目标 PC 与目标 byte
│   ├── fault_models/
│   │   ├── models.tsv                 # M001–M005 语义与事件
│   │   └── frozen_classification.tsv  # 75 个冻结分类（回归预期）
│   ├── contexts/contexts.tsv          # C01–C05 与工作负载映射
│   └── timing/
│       ├── timing_rules.md
│       ├── frozen_timing_plan.tsv     # 25 个 N / T01–T03 / M005 target seq
│       ├── corrected_prescan_summary.tsv
│       ├── evidence_sample_ids.tsv    # 条件 → 冻结样本 ID
│       └── M005_Paired_Producer_Consumer_Audit.tsv
├── src/
│   ├── RF_WB_Source_Injection_Final.patch
│   ├── rfwb/rfwb.hh, rfwb.cc          # 注入实现全文
│   └── HOOKS.md                       # 12 个 patch 文件与 5 个模型 Hook 对照
├── workloads/
│   ├── source/rfwb_0{1..5}.{c,S}      # 五个上下文工作负载源码
│   └── build/rfwb_0{1..5}             # 五个权威 ELF
│       └── rfwb_0x_C0y -> rfwb_0x     # 25 个上下文选择符号链接
├── golden/M00{1..5}_C0{1..5}.txt      # 25 个独立 golden
├── scripts/
│   ├── build/                         # gem5 与工作负载构建
│   ├── prescan/                       # 25 个 count-only 预扫描与 timing 计算
│   ├── experiment/                    # run_one / run_faults / run_controls
│   └── validation/                    # 设计、golden、分类、结果验证
├── reproduction/
│   ├── reproduce_all.sh               # 唯一总入口
│   └── README.md
├── manifests/                         # baseline / patch / binary / 100 条件清单
└── reports/                           # 5 份传播报告 + 总结 + 验收/修正文档
```

运行产物写入 `runs/`（已加入 `.gitignore`），不污染代码目录。

---

## 3. 五个故障模型

所有模型共用同一个 `gem5.opt`；`RFWB_MODEL=M00x` 选择模型，
`RFWB_MODE=off|count|fault` 选择关闭/预扫描/注入。完整实现见
`src/rfwb/rfwb.cc`，Hook 对照见 `src/HOOKS.md`。

| 模型 | 故障语义 | 修改位置与动作 | Hook |
|---|---|---|---|
| **M001** | GPR PRF 驻留值单比特翻转 | `onScalarRead` 在命中 marker/序号时直接修改 **PRF 驻留槽位**：`setReg(producerReg, cur ^ (1<<bit))` | `dyn_inst.hh` 读/写操作数、`dyn_inst.cc` execute、`free_list.hh` PhysRegId 代次 |
| **M002** | FP/SIMD PRF 目标 byte 清零 | 对目标向量指令启用 per-DynInst shadow；execute 成功后把目标 byte 置 0，再 `setReg` 写回；不修改其他 byte | `dyn_inst.hh` `getWritableRegOperand` 返回 shadow、vector read 记录、`dyn_inst.cc` execute |
| **M003** | Register Read Port 返回值翻转 | 只翻转 **read port 返回副本** `val ^ (1<<bit)`；PRF 驻留值不变，不调用 `setReg` | `dyn_inst.hh` `getRegOperand`；`setRegOperand` 只做 consumer 记录 |
| **M004** | Writeback 完成通知漏发 | `IEW::executeInsts` 中门控 `instToCommit(inst)`；目标指令的数据写回仍发生，但 completion notification 缺失 | `rfwb.cc:skipCommit`、`iew.cc` executeInsts、`commit.cc` stall/commit、`dyn_inst.cc` squash |
| **M005** | Global Register Ready 漏置位 | `IEW::writebackInsts` 中门控 `scoreboard->setReg(dest)`；PRF 数据正确；IQ 独立 scoreboard repair 保留 | `rfwb.cc:skipGlobalReady/onRenameSrc/onIQRepair`、`iew.cc` writebackInsts、`inst_queue.hh` `isRegReady`、`rename.cc`、`inst_queue.cc` |

注入事件（每个 Fault 样本恰好 1 个）：

```text
M001_INJECT
M002_COMMIT
M003_INJECT
M004_SKIP_INSTTOCOMMIT
M005_SKIP_GLOBAL_READY
```

---

## 4. 五个执行上下文

每个模型有一个工作负载源文件对（`.c` + `.S`），其中实现 `c01_*`…`c05_*`
五个函数。C `main` 通过 `argv[1]` 或可执行文件名最后一个 `_C0x` 后缀选择
上下文；25 个 `_C0x` 符号链接因此指向 5 个基础 ELF。25 个上下文 ELF 与
基础 ELF **逐字节相同**；链接名只负责上下文选择。

| 上下文 | 类别 | 负载差异 |
|---|---|---|
| **C01** | Baseline Activation | 最短 producer → consumer 激活路径 |
| **C02** | Activation Variation | 改变 consumer 指令形式、源操作数位置或目标 byte |
| **C03** | Limited Dependency | 故障值/通知后继很少，或错误结果很快被新版本覆盖 |
| **C04** | Extended Dependency | 多个 consumer 或更长数据依赖链 |
| **C05** | Control & Speculation | 目标位于分支/推测路径，并参与控制或最终输出 |

每个模型的 25 个目标 PC/byte 在 `configs/targets.tsv`；上下文类别、工作负载
与目标映射在 `configs/contexts/contexts.tsv`。五个上下文不是同一个负载的
重复运行：汇编中的消费者数量、覆盖关系、分支路径和目标 byte 都不同。

---

## 5. 三个动态执行时机

动态时机由 **eligible event 预扫描**决定，不是静态指令位置：

1. `run_prescan.sh` 以 `RFWB_MODE=count` 运行 25 个 model/context 扫描；
2. `compute_timing_plan.py` 统计合格事件 N；
3. 生成：

```text
T01 = ceil(0.10 * N)
T02 = ceil(0.50 * N)
T03 = ceil(0.90 * N)
```

要求 N ≥ 3 且三个序号互不相同；否则该条件 `BLOCKED`，不注入。

合格事件：

| 模型 | 事件 |
|---|---|
| M001 | `M001_MARKER_READ` |
| M002 | `M002_VEC_ELIGIBLE`（同一指令 seq 只计一次） |
| M003 | `M003_CONSUMER_READ` |
| M004 | `M004_ELIGIBLE`（已执行、未 squash、非访存/控制） |
| M005 | `M005_WB` 且存在同 PhysRegId/代次的 consumer Rename **在 WB 之后** |

M005 必须使用修正后的 **WB-before-Rename** 定义。历史 Batch02 M005 扫描把
8 个 Producer WB 全部计为合格，是错误的；修正后：

| Context | Eligible N | T01/T02/T03 | 合格 producer seq |
|---|---:|---|---|
| C01 | 6 | 1 / 3 / 6 | 14798,14844,14880,14920,14956,15028 |
| C02 | 6 | 1 / 3 / 6 | 14834,14889,14925,14992,15028,15100 |
| C03 | 8 | 1 / 4 / 8 | 14867,14918,14955,15000,15037,15074,15111,15148 |
| C04 | 6 | 1 / 3 / 6 | 14913,14965,15003,15041,15079,15155 |
| C05 | 8 | 1 / 4 / 8 | 14907,14963,15011,15059,15107,15155,15203,15251 |

六个 M005 T02/T03 修正样本使用 `RFWB_TARGET_SEQ`（不是 raw WB ordinal），且
保留历史 `-A3` sample ID。其他模型使用各自的 N 与 10/50/90% ordinal，绝不
套用 M005 数值。

运行选择：

- M001–M004：`RFWB_ORDINAL=<Txx>`；
- M005：`RFWB_TARGET_SEQ=<producer seq>`，因为 raw WB 计数包含不合格事件；
- 每个样本是独立 gem5 进程，模型状态完全重置；
- 若目标事件未发生，trace 中没有注入事件，分类为 `NOT_ACTIVATED`，不会伪造
  故障。

### 5.1 关于 M005 producer sequence 的可复现性

`target_seq` 是 guest 动态指令序号，不是静态 PC。它依赖 guest 初始栈布局
（尤其 workload 路径字符串），因此不同 checkout 路径下绝对序号可能整体
平移。**可复现的设计不变量是 eligible N 与 ordinal（1/3/6 或 1/4/8）**；
producer seq 只是本次运行中第 N 个合格 WB 的实例身份。

`run_one.sh` 因此：

1. 若项目位于冻结路径 `/home/sdc/gem5-fi-RF_WB`，workload 路径正好是冻结
   运行的 51 字节路径，可直接复现冻结 seq；
2. 否则在 `/tmp` 下建立 51 字节的稳定 symlink 路径，保证 guest 栈布局与
   冻结运行同长，复现相同的 N 与 ordinal；绝对 seq 可能整体偏移 29 等常量。

在外部路径上复现时，`compute_timing_plan.py` 会用新 scan 的 target seq 运行
M005；`validate_timing_plan.py` 默认比较 N/ordinal/sample ID，并对 M005 seq
差异给出 `WARN`。只有在冻结路径上做逐字节复核时才使用：

```bash
RFWB_STRICT_TARGET_SEQ=1 ./reproduction/reproduce_all.sh --plan
```

本次验证结果：25/25 个 (model, context) 在非冻结路径下复现了与冻结计划
完全相同的 N 和 T01/T02/T03；M005 为 6/6/8/6/8；仅绝对 seq 平移。

---

## 6. 实验规模与冻结结果

- **75 个 Fault**：5 模型 × 5 上下文 × 3 时机，全部唯一；
- **25 个 Control**：每模型每上下文一个 `RFWB_MODE=off` 运行；
- **25 个预扫描**：20 个 Batch02 + 5 个修正后的 Batch03 M005 扫描；
- 冻结分类：**32 ACTIVATED_SDC / 28 ACTIVATED_MASKED /
  2 ACTIVATED_SQUASHED / 13 ROB_HEAD_BLOCKED**；
- Control：**25/25 OUT 与独立 golden 一致**；
- 每个 Fault trace **恰好 1 个注入事件**。

冻结证据的验收结论是 **Overall Acceptance: PARTIAL**，唯一未通过项是 A07
（下游 consumer commit / M005 downstream writeback / M004 数据传播为
`NOT_OBSERVED`）。v5 证据同时记录 **ConfigFrozen=NO**；本仓库补齐了
source/patch/binary/build/ELF 冻结清单，但不追溯修改已冻结的验收标签。

---

## 7. 环境依赖

| 项 | 冻结/验证值 |
|---|---|
| 主机架构 | aarch64（原生，无需交叉编译） |
| OS | openEuler 24.03 LTS-SP3 |
| C/C++ | gcc 12.3.1（冻结 ELF 由 `12.3.1-109` 构建；当前主机 `-111`） |
| Python | 3.11.6（仅标准库） |
| 构建 | SCons 4.5.2；gem5 25.1.0.1（上游 `62c7bf2`） |
| gem5 构建 | `scons -j16 build/ARM/gem5.opt`（29 GB 主机请勿用 `-j126`，会 OOM） |
| 运行工具 | `timeout`、`awk`、`sha256sum` |
| 工作负载 | `gcc -O2 -static` 生成 aarch64 静态 ELF |

冻结工作负载 ELF 已随仓库提供。重新编译可能因 gcc patch level 或 BuildID
不同而改变文件 SHA256；**冻结 ELF 是官方结果的权威输入**，不要用重编译
结果覆盖 `workloads/build/`。

---

## 8. 快速开始

### 8.1 使用已发布的 RF_WB 分支（推荐）

```bash
git clone -b RF_WB https://github.com/wangxumarshall/gem5-fi.git gem5-fi
cd gem5-fi/rfwb-e2e
export GEM5_ROOT=$(cd .. && pwd)

# 1) 设计/依赖 dry-run（不需要 gem5 二进制）
./reproduction/reproduce_all.sh --check

# 2) 可选：构建 gem5（若分支中没有 build/ARM/gem5.opt）
./scripts/build/build_gem5.sh

# 3) 最小 smoke：5 个 Fault + 5 个 Control + 1 个 M005 预扫描
./reproduction/reproduce_all.sh --smoke

# 4) 完整复现（25 预扫描 + 75 Fault + 25 Control + 验证）
./reproduction/reproduce_all.sh --all
```

### 8.2 使用本目录 + 独立 gem5-fi checkout

```bash
# 基线 2f4e00b4 在 RF_WB 分支发布后可从远端取得
git clone https://github.com/wangxumarshall/gem5-fi.git gem5-fi
cd gem5-fi
git checkout 2f4e00b4
git apply /path/to/rfwb-e2e/src/RF_WB_Source_Injection_Final.patch
cd ..
export GEM5_ROOT=$PWD/gem5-fi
export GEM5_BIN=$GEM5_ROOT/CHAOS/gem5/build/ARM/gem5.opt
cd rfwb-e2e   # 或本目录
./reproduction/reproduce_all.sh --check
./reproduction/reproduce_all.sh --all
```

路径解析顺序：`GEM5_ROOT` 环境变量 → 项目父目录（RF_WB 分支布局）→
同级 `../gem5-fi`。如果 gem5 位于其他位置，必须显式设置 `GEM5_ROOT`。

---

## 9. 完整复现步骤

```bash
cd rfwb-e2e
export GEM5_ROOT=/path/to/gem5-fi
export GEM5_BIN=$GEM5_ROOT/CHAOS/gem5/build/ARM/gem5.opt

# 0. 环境/设计检查（75+25 条件、模型、timing、patch、binary SHA）
./reproduction/reproduce_all.sh --check

# 1. 构建（可选；冻结 ELF 已随仓库提供）
./scripts/build/build_workloads.sh        # 重建到 workloads/build_rebuilt/
./scripts/build/build_gem5.sh             # 生成 build/ARM/gem5.opt

# 2. 25 个 count-only 预扫描
./reproduction/reproduce_all.sh --prescan

# 3. 从 scan 计算 T01/T02/T03，并与冻结 timing 计划逐项比较
./reproduction/reproduce_all.sh --plan

# 4. 75 个 Fault（由 timing plan 驱动，M005 使用 target seq）
./reproduction/reproduce_all.sh --faults

# 5. 25 个 Control
./reproduction/reproduce_all.sh --controls

# 6. golden / 分类 / 结果验证
./reproduction/reproduce_all.sh --validate
```

等价的一键流程（不包含 gem5 构建）：

```bash
./reproduction/reproduce_all.sh --all
```

实验参数由 `scripts/experiment/run_one.sh` 固定：
`--cpu O3 --maxinsts=1000000 --max_ticks=50000000`，`timeout 120`。
不得为了“跑出结果”修改这些参数或注入模型。

重跑已有 `runs/` 时需要显式允许覆盖：

```bash
RFWB_FORCE=1 ./reproduction/reproduce_all.sh --controls
```

---

## 10. 输出与验证

```text
runs/
├── scan/SCAN-Mxxx-C0y-N/          # 25 个 count-only 预扫描
├── faults/<sample_id>/            # 75 个 Fault
├── controls/CTRL-RFWB-Mxxx-C0y-RUN/
├── traces/<sample>.csv            # 注入/合格事件 trace
├── timing_plan.tsv                # 新生成的 timing 计划
├── fault_classification.tsv       # 新分类结果
└── index.tsv                      # rc / duration 记录
```

验证门：

| 脚本 | 作用 |
|---|---|
| `scripts/validation/validate_design.py` | 25 目标、25 golden、25 timing、75+25、M005 修正、patch/binary/manifest、仓库卫生 |
| `scripts/prescan/validate_timing_plan.py` | 新 plan 与冻结 plan 逐项一致；M005 6/6/8/6/8 |
| `scripts/validation/check_golden.py` | Control OUT 与独立 golden 逐行一致（25/25） |
| `scripts/validation/classify_results.py` | 按冻结顺序分类 75 个 Fault |
| `scripts/validation/validate_results.py` | 检查 75/25 样本、单注入、ordinal/target seq、rc、golden、分类 |

`configs/fault_models/frozen_classification.tsv` 是 75 个样本的冻结分类。
复现结果必须与它逐项一致；这同时验证动态时机和故障语义没有漂移。

---

## 11. 基线与版本信息

| 项 | 值 |
|---|---|
| Source commit | `2f4e00b434ec8690fbb8cb6965e435094de7e784` |
| Source tree | `f34ae2d1e8f002c03e919218ef4f2c00e40b0a95` |
| Commit subject | `[LSU][MDSPEC][0202-T02F2-MSHR] 报告/freeze 回填确切提交 SHA` |
| Remote | `https://github.com/wangxumarshall/gem5-fi.git` |
| RF/WB patch | `src/RF_WB_Source_Injection_Final.patch` |
| Patch SHA256 | `87c8968fe1e555db97fc8b5e735e6e975fdafa1e9f867732789d9e5822f8e60a` |
| gem5 | 25.1.0.1；上游 `62c7bf2` |
| gem5.opt SHA256（冻结证据二进制） | `16a7bc1eac1b86c14219f02fc7484449bc3cd01b9560830fa7ba63c210cc6c61` |
| gem5.opt SHA256（本轮增量重建验证） | `761eba05b074d625622943d70b7c9329b840ad05ded56da3d46639f8e62f82fb`（同源码；时间戳/链接状态不同） |
| Final build log SHA256 | `9ecad86fe47e5a3b94f859bc1f73643aaeb27b2c482a7e41a080db8d28f8af3b` |
| 实验方案 | `inputs/gem5-fi-RF_WB-Final-Paper-Experiment-Plan.xlsx`（25 sheets，2026-11-24） |
| 实验方案 SHA256 | `e7eccf2d1f494fc940dcaf7b7aee7638fe5cf8f805a960540b5894860b0a20a2` |
| 冻结 timing plan SHA256 | `7000eabd5bdd1e5b0c74b1465b7662970cd2f3c0151dc78d9cf7fe6a5da1d1c7` |
| 100 条件清单 SHA256 | `af09f656c468e7203464864ad0d3cde60183dcad5e4be7f036755ae5fc03f632` |

工作负载 ELF SHA256：

| 文件 | SHA256 |
|---|---|
| `rfwb_01` | `935aa6aef2cecc2e66d12182b97a88f728ceee88fa938de4a6c679c33f401bb6` |
| `rfwb_02` | `564220e906e8c0b23d675f7e522048f996798b4be63c23c74e86f19f549779f4` |
| `rfwb_03` | `d214467dfbc567b2819a4f6d5c8440fac9845d0d1c5417988d61af311681af8f` |
| `rfwb_04` | `01dda2c06f3d3412b22402f63c33f96fa83105b9c8236301c6f07a1e1b6d1433` |
| `rfwb_05` | `94716bef8f77d4108351520fed9e9ff16384c069a418683d9ebe89705a5e1ede` |

完整清单：

- `manifests/source_baseline.txt`
- `manifests/patch_manifest.txt`
- `manifests/source_freeze_manifest.tsv`
- `manifests/binary_sha256.txt`
- `manifests/build_info.txt`
- `manifests/experiment_conditions.tsv`

---

## 12. 证据边界与已知限制

- 传播链验收是 **PARTIAL (A07)**：M001–M003 consumer commit、M005
  downstream writeback、M004 数据传播等没有直接 Hook，报告标
  `NOT_OBSERVED`，未用推断冒充观察。
- M002 C04-T03/C05-T03 没有同代次 consumer read；静态路径不提升为动态证据。
- M003 的实际翻转源是 x3（C01–C04）或 x4（C05）；x10 是 EOR 的另一源，
  不是故障源。报告与审计文档已修正该归属。
- M004 不注入数据错误；ROB_HEAD_BLOCKED 是缺通知导致的提交阻塞，不是 SDC。
- 历史 Batch01/02/03 原始 Trace、75 份 Fault 记录、25 份 Control、预扫描、
  Attempt Ledger、因果矩阵、验收报告与 SHA256 清单保存在服务器独立证据
  归档中；其中权威冻结包为：
  `RF_WB_Final_Documentation_Closure_Package_v5.tar.zst`
  SHA256 `04d9f57840eb186a402a05f63fb311b8249ba8a18f1f9747a219348d854b7ba6`
  （内部 4,057 项 SHA 校验通过）。本代码仓库不包含这些大文件。

---

## 13. 引用与联系

- 代码基线：gem5-fi（`wangxumarshall/gem5-fi`），RF/WB 分支。
- 实验设计：`inputs/gem5-fi-RF_WB-Final-Paper-Experiment-Plan.xlsx`。
- 发布包审计：`RF_WB_PreCleanup_Audit.md`、`RF_WB_File_Inventory.tsv`、
  `RF_WB_Reproduction_Validation_Report.md`、`RF_WB_GitHub_Release_Report.md`。
