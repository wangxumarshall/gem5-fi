# SAD 评审问题修复与补全（2026-11-23）

- 状态：进行中
- 关联：`CHAOS/gem5/src/cpu/o3/sad.{hh,cc}`、`scripts/test-sad.sh`、
  `sdcfuzz/coverage_report.py`、`experiments/autousens/metrics.py`、
  `experiments/autousens/u20_templates.py`、`tests/test_coverage_report.py`、
  `tests/test_autousens_metrics.py`、`docs/sad-review-2026-11-23.md`
- 验收机：`sdc-0103`（aarch64，gem5 `build/ARM`），真实构建 + gem5 运行

## 背景（远程实测事实）

1. `sad.samples` 只统计 CPU 实际 tick 的周期。实测 6 组运行精确满足
   `samples = numCycles - idleCycles - 1`；ACE/IBR 的 `measuredCycles`
   等于 `numCycles`。所以 SAD 是“活跃周期占用”，ACE/IBR 是“ROI 周期
   （含 idle）占用”；u20 80/80 行 `samples/rf_ace` 为 70.0%–98.5%
   （中位 89.0%）。
2. `sad.measuredCycles` 是 `samples` 的别名，但描述写成
   “kept consistent with ACE/IBR reporting”，与事实相反。
3. `sad.issuedOps` 与 gem5 的 `iq.instsIssued` 逐次相等（847/847、
   26422/26422、13772/13772、682/682）；ldxr 流的 issue 事件是
   retired 的 7.849×。`u20_templates.py` 把它当 `roi_insts` 用。
4. `sad.fu` 是全体 FU 的单一聚合；定向运行 `usedSum::fu == issuedOps`，
   `fu = issueWidth/numUnits × issue`（proxy 0.16、默认 O3 0.32）；
   u20 79/80 行 `fu/issue=0.16`，e2 的 8.62× 就是 issue 比。
5. `--sad` 关闭仍输出完整 `sad.*` 零表（`sad.samples 0`、`capacity` 真实、
   `ratio 0`）；`sad_from_stats` 返回零文档，无法区分“未测量”和“测到 0”。
6. `vecPrf` 有 44/capacity 的固定地板（proxy 0.2292、默认 O3 0.1719）；
   无向量负载也报 0.2292。`sq` 在 u20 语料 72/80 为 0，但定向 lsq
   运行 sq=0.910910，资源本身可用。
7. `test-sad.sh` 实机通过；cycle 用例只采到 16/100 个活跃周期，测试只
   断言 `0<samples<=100`；disabled 用例只断言零，不断言“没有 SAD 计数”。

## 范围与决策

本轮修复“窗口/契约/解析/测试”这条主链，并更正 fu 与 PRF 的解释文档。
以下项**明确留到后续**（不在本轮代码里做，文档记录原因）：

- `sadFuBusy()` 的 `iew.fuPools` 去重 / SMT fatal：`cpu.cc` 当前有并行的
  RF ACE 未提交改动，本轮不碰共享文件；当前 `numThreads=1`，未触发。
- 按 FU 类别拆分 `sad.fu`：需要改 `FUPool` 能力映射与 stats schema，
  属于新 feature；本轮只更正“8.62× = 乘加端口占用”的错误结论。
- `sad.retiredOps` 的 C++ 提交钩子：需要 `cpu.hh/commit.cc`（共享文件）；
  本轮 Python 端用 work_end 第一 dump 的 `simInsts` 作为 ROI retired 数。
- PRF 基线扣除/改名（`vecPrf` 0.2292 地板）：本轮在文档与解析器里暴露
  `mean_used`/`capacity`，不做新的 baseline 统计。
- u20 语料补 store（sq）：属于实验语料/生成器工作，不在本轮。

## 单元分解（一个单元 = 一个提交）

### 单元 1：评审文档 + 本计划

- 文件：`docs/sad-review-2026-11-23.md`、本文件
- 内容：15 项问题、远程证据、上一轮更正、修复状态、遗留项
- 验证：文档中引用的 stats 数值均来自本轮远程命令；不写未验证数字
- 提交：`docs(sad): 评审问题总结与修复计划`

### 单元 2：SAD 统计契约（窗口）

- 文件：`CHAOS/gem5/src/cpu/o3/sad.hh`、`sad.cc`
- 内容：
  - 新增 `sad.enabled`（0/1）；
  - 新增 `sad.roiCycles`（ROI 周期数，含 idle；work-item 用
    `windowEnd - windowStart`，cycle 用 `[start,end)`）；
  - 新增 `sad.idleCycles`（`roiCycles - samples`，含 end 边界；描述写明
    `samples + idleCycles == roiCycles`）；
  - 新增 `sad.activeCycles`（等于 `samples`）；
  - `sad.measuredCycles` 保留为兼容别名，描述改为“deprecated alias of
    activeCycles; NOT the ROI length; use roiCycles”；
  - 修正 `sad.samples`、`sad.issuedOps`、`sad.issueRatio` 的描述；
  - 不修改 `cpu.cc/cpu.hh/commit.cc`（避开并行 RF ACE 工作）。
- 验证命令：
  - 构建：`cd CHAOS/gem5 && source ~/gem5-deps/env.sh && scons build/ARM/gem5.opt -j48`
  - `SAD_OUT=/tmp/sad-fix-<date> bash scripts/test-sad.sh`
  - 断言（脚本内）：`enabled==1`、`activeCycles==samples`、
    `samples+idleCycles==roiCycles`、work-item 的
    `roiCycles == work_end dump 的 numCycles`、cycle 的 `roiCycles==100`；
    disabled 的 `enabled==0` 且 `samples==0`。
- 提交：`feat(gem5): SAD 增加 ROI/活跃/空闲周期统计并修正 measuredCycles 契约`

### 单元 3：`sad_from_stats` 拒绝未测量运行

- 文件：`sdcfuzz/coverage_report.py`、`tests/test_coverage_report.py`
- 内容：
  - 解析 `enabled`、`roiCycles`、`idleCycles`、`activeCycles`；
  - `enabled == 0` 或（`samples == 0` 且 `windowBegins == 0` 且
    `roiCycles == 0`）时返回 `None`；
  - 文档字段加 `roi_cycles`、`idle_cycles`、`active_cycles`；
  - Markdown 表加 `roiCycles/samples/idleCycles`；
  - 负向测试：`sad.enabled 0` 的真实形态 → None；启用的零样本 ROI →
    document 但 `samples=0`/`roi_cycles>0`。
- 验证：`python3 -m pytest tests/test_coverage_report.py -q`；用
  `--sad` 关闭的真实 stats 跑 `sad_from_stats` 断言 None。
- 提交：`fix(coverage): 拒绝未启用的 SAD 零表并暴露 ROI 周期`

### 单元 4：autousens 窗口一致性按 ROI 周期比较

- 文件：`experiments/autousens/metrics.py`、`tests/test_autousens_metrics.py`
- 内容：
  - `SAD_GLOBALS_OPTIONAL = ("enabled","roiCycles","idleCycles","activeCycles")`；
  - `windows["sad_roi"] = roiCycles or samples`（旧 dump 回退）；
  - `window_consistent` 用 `sad_roi` 与 ACE/IBR 比较；
  - `_sad` 派生 `active_share`、`idle_cycles`；
  - 测试：`sad.samples=90`、`roiCycles=100`、ACE=100 → consistent=True；
    旧 dump 无 roiCycles → 回退 samples，保持旧行为。
- 验证：`python3 -m pytest tests/test_autousens_metrics.py -q`；用新
  stats（带 rfAce）跑 `metrics.extract`，断言 `window_consistent=True`。
- 提交：`fix(autousens): SAD 窗口一致性改用 ROI 周期而非活跃样本`

### 单元 5：u20 的 roi_insts 不再用 issuedOps

- 文件：`experiments/autousens/u20_templates.py`
- 内容：
  - `roi_insts` 取 work_end 第一 dump 的 `simInsts`（stats reset 后即
    ROI 指令数）；取不到时才回退 `sad.globals.issuedOps`；
  - 更新注释，说明 `issuedOps` 是 issue 事件（ldxr 7.849×），不是 retired；
  - `ipc` 仍用 `ace.rf.measuredCycles`。
- 验证：用现有 u20 stats 重算 e2/ldxr 单元，`roi_insts` 与第一 dump
  `simInsts` 一致；`issuedOps/roi_insts` 已在文档中记录。
- 提交：`fix(autousens): u20 的 ROI 指令数改用 simInsts 而非 issuedOps`

### 单元 6：文档更正与遗留项

- 文件：`docs/experiments/2026-11-17-u20-templates-vs-autousens-report.md`
  （顶部加 2026-11-23 更正说明）、`docs/sad-review-2026-11-23.md`（修复状态）
- 内容：
  - 8.62× 是 issue 比，不是“乘加端口占用”；
  - SAD 分母是活跃周期，`window_consistent` 必须用 `roiCycles`；
  - PRF 地板、fu 聚合、SQ 语料、SMT 去重列为已知边界/后续项；
  - 记录本轮验收命令与真实输出摘要。
- 验证：文档内数字与 stats 对得上；无未验证断言。
- 提交：`docs(sad): 更正 u20 的 fu 解释并记录 SAD 边界`

## 验收循环

每个单元按“改 → 构建/测试 → 读真实输出 → 通过才提交”执行。
若验收失败：
1. 在本 plan 追加“失败记录”（命令、真实输出、原因）；
2. 调整该单元的实现或范围，重新执行；
3. 通过后再勾选该单元。

最终验收（全部单元完成后）：
- `scons build/ARM/gem5.opt` 无新增 warning/error；
- `scripts/test-sad.sh` rc=0，且新断言全部通过；
- `pytest tests/test_coverage_report.py tests/test_autousens_metrics.py -q`
  全部通过；
- 一次 `--sad` 关闭的真实运行，`sad_from_stats` 返回 None；
- 一次带 `--rf_ace` 的真实运行，`metrics.extract` 的
  `window_consistent=True`；
- 至少一个无关回归测试（如 `tests/test_lsu_compare.py`）通过。

## 验收失败记录与调整（2026-11-23）

1. **尝试 1**：`scons build/ARM/gem5.opt -j48`（无 `--limit-ld-memory-usage`）
   - 真实输出：`/usr/bin/ld: final link failed: bad value` +
     `collect2: error: ld returned 1 exit status`；
   - 后果：`build/ARM/gem5.opt` 被删除，旧二进制不可用；
   - 判断：30 GB 内存下 48 并发 + 1.1 GB 二进制的链接内存不足，或
     linker 缺 `--limit-ld-memory-usage`。
2. **尝试 2**：按 `scripts/test-sad.sh` 的 flags `-j8`
   `"ISA_CONSTR_CCFLAGS=-g0" "ISA_EXEC_CCFLAGS=-g0" --debug-fission
   --limit-ld-memory-usage`
   - 真实输出：全量重编译（`-j8` 下 10 分钟仅 500 个对象），进展过慢；
   - 判断：`--debug-fission`/ISA 变量改变了所有 target 的签名，触发全量
     重建；`-j8` 不适合 1.1 GB 目标。终止。
3. **尝试 3（当前）**：同样 flags，`-j32`，日志 `/tmp/sad-build2.log`
   - 真实进展：`[LINK] -> ARM/gem5py_m5` 已成功；`gem5.opt` 尚未链接；
     `sad.cc` 尚未编译到（生成代码阶段）；
   - 决策：**不再改 flags**（再次改动会重新触发全量签名变化），等待
     全量构建完成；完成后立即跑 `test-sad.sh` 与 pytest。
4. **安全措施**：已终止第一次 `-j8` 的 scons 进程，避免两个 scons 同时
   写同一个 `build/ARM`；当前只有 `-j32` 一个构建。
