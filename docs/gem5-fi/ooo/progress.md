# Progress Log

## 更新要求

- 活跃执行期间至少每 30 分钟更新一次；阶段/ITEM/长任务/错误/重试/资源状态变化时立即更新。
- 只记录已实际发生的动作；所有完成声明附证据路径。
- 每次更新写明当前 ITEM、RunID、Excel 行、campaign/phase、资源状态和唯一下一动作。

## Current Status

- **Current Phase:** P0
- **Phase Status:** PENDING
- **Overall Status:** NOT_STARTED
- **Started / Last Updated / Owner:** 由服务器 AI 填写
- **Current Checklist Item / RunID / Excel Location:** NONE / NONE / NONE
- **Current Experiment Stage:** preflight
- **Campaign:** NONE
- **Completed ITEM Stages:** 0
- **Resource Safety State:** UNCHECKED
- **Build Limit:** `-j8`，全局单实例
- **Experiment Concurrency Limit:** 4（资源不足时降为3/2/1，不得超过4）
- **Active Heavy Task / PID / PGID / Lock / Resource Log:** NONE
- **Latest MemAvailable / SwapFree / Load / blocked:** 未检查
- **Checklist SHA-256:** `f520d42a53ae2e44e76af5771dd1bcbdb9545082458e7996b1d306f1bbc30c91`
- **Next Step:** 读取全部文件，校验57模型/310 ITEM与哈希，执行P0和G0预检。

## Phase Summary

| Phase | Status | Started | Completed | Evidence/Output |
|---|---|---|---|---|
| P0 环境/输入/恢复预检 | PENDING | | | |
| P1 注入器/观测链 | PENDING | | | |
| P2 负载/golden/冒烟 | PENDING | | | |
| P3 全矩阵 Pilot | PENDING | | | |
| P4 正式筛查 | PENDING | | | |
| P5 确认性扩样 | PENDING | | | |
| P6 单因素敏感性 | PENDING | | | |
| P7 稳健性与复现 | PENDING | | | |
| P8 分析归档交付 | PENDING | | | |

## Session Log

### Session 001

- **Start:** 由服务器 AI 填写
- **Phase:** P0
- **Actions:** 尚未执行服务器预检或实验。
- **Results / Evidence / Errors:**
- **Next Step:** 读取全部文件并执行 P0。

## Active Work

| Work ID | ITEM | RunID | Excel行 | campaign/phase | sample_index/seed | 状态 | owner/PID/PGID/锁 | 心跳 | 输出/证据 |
|---|---|---|---|---|---|---|---|---|---|

## Checklist Status Summary

| Stage | PENDING | RUNNING | COMPLETE | BLOCKED | INVALID | NA/UNSELECTED | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Engineering | 310 | 0 | 0 | 0 | 0 | 0 | 310 |
| Pilot | 310 | 0 | 0 | 0 | 0 | 0 | 310 |
| Screening | 310 | 0 | 0 | 0 | 0 | 0 | 310 |
| Confirmatory/Sensitivity/Reproduction | 0 | 0 | 0 | 0 | 0 | 310 | 310 |

## Test and Gate Results

| Test/Gate | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| 六个输入文件可读 | 全部可读 | 未检查 | UNCHECKED | |
| 清单规模 | 57模型、310 ITEM、310唯一RunID | 未检查 | UNCHECKED | |
| 清单哈希 | `f520d42a53ae2e44e76af5771dd1bcbdb9545082458e7996b1d306f1bbc30c91` | 未检查 | UNCHECKED | |
| Excel哈希 | 与总方针一致 | 未检查 | UNCHECKED | |
| G0-01 至 G0-09 | 均有状态与证据 | 未检查 | UNCHECKED | |
| G0-10 | 编译锁、实验worker lease、实验并发≤4、资源守卫、60秒监控、30分钟心跳、恢复扫描可验证 | 未检查 | UNCHECKED | |

## Resource Safety Status

| 时间 | 状态 | MemAvailable | SwapFree | Load 1/5/15 | blocked | 磁盘 | owner/PID/PGID | 锁 | 动作/证据 |
|---|---|---:|---:|---|---:|---:|---|---|---|

## Errors and Retries

| Error ID | 时间 | ITEM/RunID | 错误签名 | Attempt | 改变的策略 | Resolution/Decision Request | Evidence |
|---|---|---|---|---:|---|---|---|

## Periodic Update Template

```text
时间：
当前阶段/状态：
当前 ITEM / RunID / Excel行：
campaign / phase / sample_index / seed：
过去30分钟完成：
运行中任务与最近心跳：
错误/重试/BLOCKED：
资源状态（NORMAL/WARNING/TRIP/BLOCKED）：
MemAvailable / SwapFree / Load / blocked / 磁盘：
owner / PID / PGID / 锁 / 日志：
门禁变化：
唯一下一动作：
证据路径：
```

## Pause Entry（2026-10-09 用户指令暂停）

- 动作：dkill 1773145（cn22986 RUNNING）+ 1823682（PENDING）→ djob 复核 0 残留；取消 session cron 9177bcc2；U5 Step-2 冻结至 runs/ooo-node/evidence/u5-step2-frozen/；复盘报告 docs/gem5-fi/ooo/10-p1-pause-retrospective.md。
- 状态：U0–U4/U10/U10b/U11 完成（10 单元，19/57 模型，--check 310/310 三方一致）；U5 冻结于 Step-2 推导 80%（五族编码规则全实证）；U6–U9/U12 未开始。
- 唯一下一动作（恢复时）：完成 u5verify.py 闭环 → C++ VecStitchRule 表 → 三模型实现。
- 证据路径：runs/ooo-node/evidence/u5-step2-frozen/FREEZE-NOTES.md。
