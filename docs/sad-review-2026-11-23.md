# SAD 实现评审与修复记录（2026-11-23）

- 评审对象：`CHAOS/gem5/src/cpu/o3/sad.{hh,cc}` 及其集成/解析/测试链
- 评审方式：远程 `sdc-0103` 真实构建 + gem5 运行 + 归档 stats 重算
- 结论：**算术与管线正确；问题集中在度量口径、统计契约、解析/测试覆盖**。
  SAD 可作为“gem5 O3 活跃周期占用压力”的协变量，不能作为
  “结构激活/覆盖”或与 ACE/IBR 同窗口比较的证据。

## 1. 上一轮评审的更正（远程实机后）

| 上一轮说法 | 远程事实 | 处理 |
|---|---|---|
| `workloads/directed/sad_workload.c` 缺失、`test-sad.sh` 不可运行 | 文件存在；`SAD_OUT=/tmp/... bash scripts/test-sad.sh` rc=0 | 撤回 |
| `CHAOS/gem5` 集成代码缺失、无法审计/重建 | `cpu.cc/cpu.hh/inst_queue.cc/BaseO3CPU.py/fu_pool.*/rob.hh` 均在；AArch64 构建可用 | 撤回 |
| SAD 窗口差 10%–30%，原因不明，疑似漏采样 | `sad.samples = numCycles - idleCycles - 1`；ACE/IBR `measuredCycles = numCycles`；差值是 idle 周期 | 修正为 active-cycle 口径 |
| `sad.issuedOps` 是 SAD 自己的重复计数 | 与 `iq.instsIssued` 逐次精确相等（847/847、26422/26422、13772/13772、682/682） | 修正为 gem5 issue-event 口径；下游误用仍在 |
| SAD `sq` 资源是死的 | 定向 `lsq`：`sq=0.910910`、`lq=0.900647` | 修正：u20 语料 72/80 为 0，不是实现坏 |
| `--sad` 关闭仍输出零表 | 真实无 `--sad` 运行：`sad.samples 0`、`capacity` 真实、`ratio 0` | 保留 |
| `fu` 共线、8.62× 是 issue 比 | `usedSum::fu == issuedOps`；u20 79/80 行 `fu/issue=0.16` | 保留 |
| `vecPrf` 0.2292 地板 | 定向 nop/rob/lsq 全为 0.22916667（44/192） | 保留 |

## 2. 远程实测证据

### 2.1 窗口：活跃周期 vs ROI 周期

在 proxy（issueWidth=4）与默认 O3（issueWidth=8）两种配置下，均精确满足
`samples = numCycles - idleCycles - 1`：

| 运行 | numCycles | idleCycles | sad.samples | ACE/IBR measuredCycles |
|---|---:|---:|---:|---:|
| proxy nop 400 | 7749 | 795 | 6953 | 7749 |
| proxy rob 400 | 27079 | 1314 | 25764 | 27079 |
| proxy lsq 200 | 20410 | 581 | 19828 | 20410 |
| default nop 400 | 4320 | 574 | 3745 | — |
| default rob 400 | 26290 | 543 | 25746 | — |
| default rob 10 + rfAce | 1303 | 516 | 786 | 1303 |

u20 归档 80/80 行 `samples/rf_ace = 70.05%–98.55%`，中位 **88.99%**，
`window.consistent` 全 False。原因不是漏采样，而是 SAD 的 `samples`
只统计 CPU 实际 tick 的周期；CPU idle 时会 unschedule tick，而唤醒时
`baseStats.numCycles` 又补回 idle 周期（`cpu.cc:1416-1423`），ACE/IBR
的窗口用 `curCycle` 差值，包含 idle。

`measuredCycles` 只是 `samples` 的别名（`sad.cc:209`），但描述写成
“kept consistent with ACE/IBR reporting”（`sad.cc:185-186`），与事实相反。

### 2.2 `issuedOps` 是 issue 事件，不是 retired 指令

`inst_queue.cc:939-941` 的 `sadRecordIssue()` 与
`iqStats.instsIssued += total_issued`（`inst_queue.cc:1025`）同分支；
4 组运行逐次相等。ldxr 流：ROI 38,800 条 vs `issuedOps=304,554`
（**7.849×**）；`tools/lsu_compare.py:19-28` 已记录 7×。
`experiments/autousens/u20_templates.py:678` 把 `issuedOps` 当
`roi_insts`/IPC 分子；当前 20 单元 `issuedOps≈4,096`，所以 u20 表暂时
未被污染，但任何 replay-heavy 流会放大 2–8×。

另：`sad-implementation` 文档称 `issuedOps` 包含 `NoNeedFU`，但
`nop 400` 的 25,600 个 NOP 对应 `issuedOps=847`（NOP 不走这条 IQ
issue 路径），该描述也不准确。

### 2.3 `sad.fu` 是 issue 的线性缩放

- 实现只有单个聚合 `usedSum[Fu] += cpu->sadFuBusy()`（`sad.cc:100`），
  `sadFuBusy()` 汇总 `iew.fuPools` 的 `numBusyUnits()`（`cpu.cc:405-412`），
  容量为 `funcUnits.size()`；没有按端口/类别拆分。
- 定向运行全部 `usedSum::fu == issuedOps`，因此
  `fu_ratio = (issueWidth / numUnits) × issueRatio`：
  proxy（4/25）= **0.16**，默认 O3（8/25）= **0.32**。
- u20 79/80 行 `fu/issue = 0.16`；唯一例外 `f1_subnormal_nan`
  0.238966（1.49×，多周期 FP）。
- e2：fu 0.11843705 / issue 0.74023155 = 0.16，**8.62× 就是
  issue 比 8.6234**；`docs/experiments/2026-11-17-u20-...` 把它解释为
  “乘加端口占用”没有实现依据。

### 2.4 `--sad` 关闭仍输出零表

无 `--sad` 的 `rob 10` 运行：

```text
sad.samples 0
sad.issueWidth 8
sad.issuedOps 0
sad.capacity::rob 128
sad.usedSum::rob 0
sad.ratio::rob 0.00000000
```

`SADTracker` 是 CPU 成员（`cpu.hh:487`、`cpu.cc:109`），`Stats` 组在
构造函数无条件注册（`sad.cc:175-212`），`enabled` 只控制累加。
`sad_from_stats` 返回 `{'samples':0.0,'ratio':{...0...},'capacity':{...}}`，
与 `experiments/autousens/metrics.py:12-15` 声明的“缺失≠零”契约冲突。

### 2.5 PRF 地板与“占用≠激活”

- `vecPrf` 用 `numPhysVecRegs - free`；整数/无向量负载固定 44 个已用：
  proxy 192 → **0.22916667**；默认 O3 256 → **0.171875**；
  u20 14/80 行 `mean_used` 恰为 44.0，最大 108.05。
- `intPrf` 地板约 43（proxy 0.2648、默认 0.1668）。
- u20 `corr(iq, issue) = -0.897`、`corr(rob, issue) = -0.659`；
  IQ>0.9 有 33/80；新跑 `rob` IQ=0.939 对应 IPC≈1.0，`lsq` LQ=0.900/
  SQ=0.911 对应 IPC≈0.667。SAD 高是停顿/等待，不是激活/覆盖。

### 2.6 测试

`test-sad.sh` 在远程通过：

```text
nop  samples=3745 rob=0.132089 lq=0.000075 sq=0.000000 prf=0.166771 fu=0.009047 issue=0.028271
rob  samples=25746 rob=0.344890 ...
lsq  samples=19798 rob=0.317024 lq=0.900647 sq=0.910910 ...
prf  samples=4556 ...
SAD window, formula, direction, disabled and cycle-mode checks passed (cycle samples=16)
```

但：

- cycle 用例窗口 `[5000,5100)` 只采到 **16/100** 个活跃周期
  （`numCycles=69043`、`idleCycles=27458`），测试只断言
  `0<samples<=100`，没有验证窗口完整/ workload 在窗口内；
- disabled 用例只断言 `samples==0`/`ratio==0`，没有断言
  “SAD 未启用/无计数”；
- `test-sad.sh` 用默认 O3（ROB 192、IQ 64、LQ 32、SQ 32、
  intPrf 256、vecPrf 256、FU 25、issueWidth 8）；`p1_sad`/autousens
  用 kp920 proxy（128/64/48/42/160/192、width 4）；文档混用两种配置；
- `p1_sad` 的 `verify.py:671-709` 只检查 rob/lq/sq，且用 `w_ibr`，
  不检查 intPrf/vecPrf/fu/issue/窗口。

## 3. 问题分级与状态

| 级别 | 编号 | 问题 | 状态 |
|---|---|---|---|
| S1 | S1-1 | `samples` 活跃周期 vs ACE/IBR ROI 周期；`measuredCycles` 假别名 | 本轮修复：新增 `enabled/roiCycles/idleCycles/activeCycles`，改描述 |
| S1 | S1-2 | `fu` 单值聚合，8.62× 被解释为端口占用 | 本轮更正文档；按类别拆分留后续 |
| S1 | S1-3 | `--sad` 关闭仍输出零表，解析器当“测到 0” | 本轮修复：`enabled` 统计 + 解析器拒绝 |
| S2 | S2-1 | `issuedOps` 是 issue 事件，被当 `roi_insts` | 本轮修复 u20 取第一 dump `simInsts` |
| S2 | S2-2 | PRF 固定地板；无向量负载也报 0.229/0.172 | 本轮文档暴露；baseline 留后续 |
| S2 | S2-3 | 占用压力被当激活/覆盖 | 本轮文档更正 + window 契约 |
| S3 | S3-1 | cycle 测试 16/100，断言过弱 | 本轮修复测试断言 |
| S3 | S3-2 | workitem 只测第一个 ROI；cycle 模式忽略 start/end | 文档记录；不扩范围 |
| S3 | S3-3 | 缺 `enabled/roiCycles` 等审计统计；无零样本告警 | 本轮补 `enabled/roiCycles/idleCycles` |
| S3 | S3-4 | 测试只验公式/方向；disabled 只验零；`p1_sad` 只查 3 资源 | 本轮补 disabled/窗口断言；`p1_sad` 留后续 |
| S3 | S3-5 | u20 语料 `sq` 72/80 为 0 | 语料问题；SQ 实现可用，留后续 |
| S3 | S3-6 | `sadFuBusy` 对 `iew.fuPools` 不去重（SMT 隐患） | 留后续（cpu.cc 并行改动） |
| S4 | S4-1 | 默认 O3 与 proxy 两套容量/issueWidth 混用 | 文档标注；测试保留默认 O3 |
| S4 | S4-2 | PRF 只测 Int/Vec；Float/CC/Mat/VecPred 未测 | 文档边界 |
| S4 | S4-3 | 死代码/描述不实/只有均值 | 部分修复；分布/死代码留后续 |

## 4. 本轮修复清单

1. `sad.{hh,cc}`：新增 `enabled`、`roiCycles`、`idleCycles`、`activeCycles`；
   修正 `measuredCycles`/`samples`/`issuedOps`/`issueRatio` 描述。
2. `scripts/test-sad.sh`：新增 `enabled`、`activeCycles==samples`、
   `samples+idleCycles==roiCycles`、work-item `roiCycles==numCycles`、
   cycle `roiCycles==100`；disabled `enabled==0`。
3. `sdcfuzz/coverage_report.py`：解析新字段；`enabled==0` 或未开始 ROI
   返回 None；Markdown 显示 ROI/active/idle。
4. `experiments/autousens/metrics.py`：`window_consistent` 用
   `sad.roiCycles`（旧 dump 回退 `samples`）；派生 active share。
5. `experiments/autousens/u20_templates.py`：`roi_insts` 取 work_end
   第一 dump 的 `simInsts`，不再用 `issuedOps`。
6. 文档：本文件 + `docs/experiments/2026-11-17-u20-...` 顶部更正。

## 5. 已知边界（不在本轮实现）

- `sadFuBusy` 去重/SMT fatal（`cpu.cc` 有并行 RF ACE 未提交改动）。
- 按 FU 类别拆分 `sad.fu`（新 feature；需要 FUPool 能力映射）。
- `sad.retiredOps` 的 C++ commit 钩子（用第一 dump `simInsts` 替代）。
- PRF baseline 扣除/改名；u20 语料补 store；`p1_sad` 扩到 7 资源。
- Float/CC/Mat/VecPred 的 PRF 覆盖。

## 6. 验收命令（真实执行）

```bash
cd /home/sdc/sdc-mhw/CHAOS/gem5
source ~/gem5-deps/env.sh
scons build/ARM/gem5.opt -j48

cd /home/sdc/sdc-mhw
SAD_OUT=/tmp/sad-fix-20261123 bash scripts/test-sad.sh
python3 -m pytest tests/test_coverage_report.py tests/test_autousens_metrics.py -q
```

**注意**：本轮会话期间工作树存在并行的 RF ACE/SVE 未提交改动
（`cpu.cc/cpu.hh/dyn_inst.hh/rf_ace.*`、`workloads/directed/sve_probe*.c`），
不是本评审改动；SAD 文件 `sad.{hh,cc}` 未被并行任务修改。

## 7. 本轮验收记录（进行中，2026-11-23 21:0x）

- `python3 -m pytest tests/test_coverage_report.py tests/test_autousens_metrics.py -q`
  → **18 passed**（含新增 disabled/roi window 用例）。
- `python3 -m pytest tests/test_lsu_compare.py tests/test_phase1_audit.py -q`
  → **14 passed**。
- `python3 -m pytest tests -q --ignore=tests/test_u20_templates.py`
  → **227 passed**；`tests/test_u20_templates.py` 单独跑 → **9 passed**。
  全量 collection 失败是既有的 `autousens` 模块名遮蔽（`tools/autousens.py`
  vs `experiments/autousens`），与本 SAD 改动无关，未改该测试。
- `u20_templates.metric_row` 用真实 u20 stats 验证：
  `l1_disambig/k87` 第一 dump `simInsts=2183`、`sad.issuedOps=3045`；
  新代码取 2183（旧代码会取 3045），`ipc=1.4166`；
  `window_consistent=False` 是因为旧 stats 没有 `roiCycles`（回退 samples）。
- 构建：见 plan 的“验收失败记录”。`scons -j48` 链接失败（`bad value`，
  旧 binary 被删）；canonical flags 全量重建中，`gem5py_m5` 已链接，
  `gem5.opt` 未完成；`test-sad.sh` 待构建完成后自动运行
  （watcher 日志 `/tmp/sad-watch-test.log`）。

## 8. 最终验收结果（2026-11-23 21:17）

### 8.1 真实 gem5 测试

`SAD_OUT=/tmp/sad-verify-final bash scripts/test-sad.sh` → rc=0：

```text
nop           samples=3736 roi=4311 idle=575 rob=0.132584 lq=0.000050 sq=0.000000 prf=0.166738 fu=0.008972 issue=0.028038
rob           samples=25746 roi=26291 idle=545 rob=0.344908 lq=0.000000 sq=0.000000 prf=0.426745 fu=0.041050 issue=0.128282
lsq           samples=19678 roi=19951 idle=273 rob=0.315577 lq=0.918110 sq=0.928165 prf=0.285977 fu=0.027972 issue=0.087414
prf           samples=4557 roi=5218 idle=661 rob=0.330546 lq=0.000000 sq=0.000000 prf=0.452601 fu=0.232144 issue=0.725450
SAD window, formula, direction, disabled and cycle-mode checks passed (cycle samples=48, roi=100)
outputs: /tmp/sad-verify-final
test_sad_rc=0
```

新增断言全部通过：`enabled`、`activeCycles==samples`、
`samples+idleCycles==roiCycles`、work-item
`abs(roiCycles - work_end_dump_numCycles) <= 1`、cycle `roiCycles==100`、
disabled `enabled==0`、unmatched `enabled==1` 且 `roiCycles==0`。

### 8.2 解析器/分析层真实探针

- `sad_from_stats` 新 stats：`enabled=1`、`samples=activeCycles`、
  `roiCycles`、`idleCycles` 全部解析；`nop-disabled` 与 `rob-unmatched`
  返回 None（不再打印零表）。
- `--sad --rf_ace` 的 `rob 10` 运行：`rf_ace=1303`、`sad_roi=1303`；
  `metrics.extract` 的 `window_consistent=True`（忽略未启用家族的 0 窗口），
  `active_share≈0.603`、`idle_cycles=517`。
- `u20_templates.metric_row` 真实 stats：first `simInsts=2183` 优先于
  `issuedOps=3045`；单测覆盖（`test_roi_insts_uses_work_end_siminsts_not_issued_ops`）。

### 8.3 Python 测试

- `pytest tests/test_coverage_report.py tests/test_autousens_metrics.py
  tests/test_u20_templates.py -q` → **29 passed**。
- `pytest tests -q --ignore=tests/test_u20_templates.py` → **227 passed**；
  `test_u20_templates.py` 单独 → **10 passed**。
- 全量 collection 的 `autousens` 模块遮蔽是既有问题，与本改动无关。

### 8.4 构建结果与边界

- `sad.cc` 已编译：`build/ARM/cpu/o3/sad.o`（21:09），无编译错误。
- 本进程的 canonical `scons` 在 2852 个动作后因**生成头文件竞态**失败
  （`params/ClockDomain.hh: No such file or directory`）；
- 同 flags、同 source 的并行 scons 在 21:17 成功 `LINK -> ARM/gem5.opt`，
  watcher 用该二进制跑通 `test-sad.sh`。这是共享构建目录中两个任务的
  瞬态竞态，不是 SAD 代码的编译/链接错误。
- 该二进制包含并行 RF ACE 的未提交改动；SAD 的 `sad.o` 来自本轮源码。
  严格隔离的“仅 HEAD+SAD”构建未单独执行，原因是共享 `build/ARM` 被
  并行任务占用；该边界已在 plan 记录。

### 8.5 提交

- `d5d537de docs(sad): 增加 SAD 评审、修复计划与 u20 口径更正`
- `e265ec5f fix(coverage): SAD 解析拒绝未启用运行并暴露 ROI 周期`
- `0318c8d8 feat(autousens): 增加 ACE/IBR/SAD 指标层并用 ROI 周期校验 SAD 窗口`
- `31cdeb97 fix(autousens): u20 ROI 指令数改用 work_end simInsts`
- `66cfe3c1 test(autousens): 覆盖 u20 roi_insts 选择并抽取 helper`
- `742d32b7 fix(autousens): 忽略未启用家族的零窗口`
- `a7284056 feat(gem5): SAD 增加 ROI/活跃/空闲周期统计并强化测试`
- 已推送到 `origin/feat/u20-templates-vs-autousens`。

### 8.6 仍留后续（不在本轮）

`sadFuBusy` 去重/SMT fatal（cpu.cc 并行改动）、按 FU 类别拆分 `sad.fu`、
`sad.retiredOps` 的 C++ 钩子（Python 用 work_end `simInsts` 替代）、
PRF baseline 扣除/改名、u20 语料补 store、`p1_sad` 扩到 7 资源、
Float/CC/Mat/VecPred 覆盖。
