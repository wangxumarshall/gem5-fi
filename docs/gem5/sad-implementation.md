# gem5 O3 SAD（Structure Activation Depth）实现说明

## 1. 指标定义

路线文档把 SAD 定义为 gem5 O3 可观测的“资源激活深度”：

```text
SAD(s) = Σ_cycle used_s(cycle) / (samples × capacity_s)
```

其中 `used_s(cycle)` 是某周期结构 `s` 的占用项数，`capacity_s` 是该结构的
物理容量，`samples` 是 ROI 内实际采样的 CPU 周期数。每个 `SAD(s)` 都在
`[0,1]` 内；它衡量“占用时间 × 占用比例”，不是门级路径激活，也不是故障
检出率。

本实现采样 O3 能直接观测的 7 类资源：

| 资源键 | 占用来源 | 容量 |
|---|---|---|
| `rob` | `ROB::numFreeEntries()` | `numROBEntries` |
| `iq` | `InstructionQueue::numFreeEntries()` | IQ 条目总数 |
| `lq` | `LSQ::numFreeLoadEntries()` | `LQEntries` |
| `sq` | `LSQ::numFreeStoreEntries()` | `SQEntries` |
| `intPrf` | free list 中空闲的 `IntRegClass` 物理寄存器 | `numPhysIntRegs` |
| `vecPrf` | free list 中空闲的 `VecRegClass` 物理寄存器 | `numPhysVecRegs` |
| `fu` | `FUPool::numBusyUnits()` 之和 | 所有 pool 的物理单元数 |

另外输出 `issueRatio = issuedOps / (samples × issueWidth)`，作为发射宽度
占用项。`issuedOps` 来自 `inst_queue.cc` 中真正进入执行阶段的 issue 路径
（包括 `NoNeedFU` 与 `NoCapableFU`），因此分支/NOP 也计入发射宽度，但不会
被算进 FU IBR。

## 2. 实现位置与采样语义

- `CHAOS/gem5/src/cpu/o3/sad.hh`、`sad.cc`：`SADTracker`。
- `CPU::tick()` 在 `commit.tick()` 之后调用 `sadTracker.tick()`，每个 CPU
  周期采样一次。
- `inst_queue.cc` 在指令真正进入执行阶段时调用 `cpu->sadRecordIssue()`。
- `workItemBeginMarker` / `workItemEndMarker` 与 ACE/IBR 共用同一 m5 work-item
  钩子；`m5_work_begin` 触发的标准 stats reset 会保留已打开的 ROI，并把 reset
  周期作为新的起点。
- work-item 模式只测第一个匹配 ROI；begin 周期计入，end 周期为排他边界。
- 周期模式使用 `[start, end)`；不依赖 m5 marker。若 workload 仍调用
  `m5_work_begin`，标准 stats reset 会把 `resetCycle` 推到 begin 周期，因此
  周期窗口应使用不带 marker 的负载，或把窗口设在 begin 之后。

## 3. 配置与输出

`BaseO3CPU` 新增参数：

| 参数 | 默认值 | 含义 |
| --- | ---: | --- |
| `sad` | `False` | 启用 SAD |
| `sadUseWorkItems` | `False` | 使用 m5 work-item ROI |
| `sadWorkItemId` | `-1` | 目标 work ID，`-1` 为第一个 |
| `sadStartCycle` | `0` | 周期窗口起点 |
| `sadEndCycle` | `0` | 周期窗口排他终点，`0` 为仿真结束 |

`configs/se/arm_chaos.py` 提供：

```bash
--sad --sad_window=workitem --sad_work_id=7
--sad --sad_window=cycle --sad_start_cycle=5000 --sad_end_cycle=5100
```

`stats.txt` 输出：

```text
*.sad.samples
*.sad.issueWidth
*.sad.issuedOps
*.sad.issueRatio
*.sad.measuredCycles
*.sad.windowBegins
*.sad.windowEnds
*.sad.usedSum::rob/iq/lq/sq/intPrf/vecPrf/fu
*.sad.capacity::rob/iq/lq/sq/intPrf/vecPrf/fu
*.sad.ratio::rob/iq/lq/sq/intPrf/vecPrf/fu
```

`ratio` 在 dump 时由 `usedSum / (samples × capacity)` 计算；测试逐项重算，
避免只读一个“看起来合理”的百分比。

## 4. 定向验证

```bash
GEM5_BUILD_NAME=ARM bash scripts/test-sad.sh
```

`workloads/directed/sad_workload.c` 提供 `nop`/`rob`/`lsq`/`prf` 四个模式，
每个模式在 ROI 内执行已知 body 并自校验：

- `nop`：64 个 NOP/组，低占用基线；
- `rob`：64 条依赖加法/组，拉高 ROB/PRF；
- `lsq`：32 组 load+store，拉高 LQ/SQ；
- `prf`：16 组独立目的寄存器写，拉高整数 PRF 与发射占用。

脚本断言：ROI 恰好开始/结束一次；`samples > 0`；每条资源 ratio 在 `[0,1]`
且等于 `usedSum/(samples×capacity)`；`issueRatio` 等于
`issuedOps/(samples×issueWidth)`；`rob` 模式 ROB SAD 高于 `nop`；`lsq` 模式
LQ/SQ 高于 `nop`；`prf` 模式整数 PRF 高于 `nop`；关闭与不匹配 work ID 时
` samples = 0`；cycle 模式在不带 marker 的负载上真实采样。

实测（2026-11-10，原生 aarch64 `build/ARM/gem5.opt`）：

```text
nop  samples=3745 rob=0.132089 lq=0.000075 sq=0.000000 prf=0.166771
     fu=0.009047 issue=0.028271
rob  samples=25746 rob=0.344908 lq=0.000000 sq=0.000000 prf=0.426745
     fu=0.041050 issue=0.128282
lsq  samples=19785 rob=0.314907 lq=0.907308 sq=0.917482 prf=0.284995
     fu=0.028270 issue=0.088343
prf  samples=4557 rob=0.330546 lq=0.000000 sq=0.000000 prf=0.452601
     fu=0.232144 issue=0.725450
SAD window, formula, direction, disabled and cycle-mode checks passed
(cycle samples=70)
```

这些数值只适用于本次默认 O3 配置；脚本的验收依赖方向关系与公式，不依赖
某个固定阈值。

## 5. 边界

- SAD 是**资源占用深度**，不是门级路径激活，也不是 ACE/IBR 的替代品；
  它回答“测试把流水线资源占得多满/多久”，不回答“故障能否传播到输出”。
- `fu` 使用 `FUPool::unitBusy` 的瞬时计数；共享 pool 只统计一次，多 IQ 的
  不同 pool 合计。
- 采样发生在周期末；CPU 空闲、未调度的周期不增加 `samples`，因此 SAD 是
  “活跃周期内的占用率”，不是墙钟周期占用率。
- 目前没有单独建模 issue 端口到具体 FU 的映射、LSQ 内部 bank 冲突或
  McPAT 功耗；这些属于后续阶段。
