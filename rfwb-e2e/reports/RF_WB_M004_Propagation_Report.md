# RF_WB_M004_Propagation_Report

> 权威生成器：`reproduction/gen_final_reports.py`（唯一权威报告生成器）。
> 基线：`2f4e00b434ec8690fbb8cb6965e435094de7e784`；原始 Trace 未改写。
> 证据标记：`OBSERVED` / `INFERRED` / `NOT_OBSERVED`。

## 1. 故障模型及具体子单元

**Writeback 完成通知（instToCommit）漏发**

- 具体子单元：IEW → Commit 的完成通知 / instToCommit 队列项
- 故障操作与持续性：每样本恰好一次首次激活；同一 Hook、同一错误操作、同一持续性（除非该 Context 的冻结定义另有说明）。
- 证据来源：Batch01/02/03 冻结 Trace；Batch02 旧 Trace 为 14 列，没有 gen 列时标 `NA`，不虚构代次。

## 2. C01–C05 上下文定义

| Context | 机制类 | 冻结汇编序列 | 说明 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2（目标完成通知跳过）→ EOR x11,x3,x4 → STR x11` | 目标数据写回存在，但完成通知缺失。 |
| C02 | 激活/操作变化 | `EOR x10,x1,x2（目标）→ ADD x11,x3,x4 → STR x11` | 改变目标整数运算形式，通知抑制点不变。 |
| C03 | 弱依赖/最小后继 | `ADD x10（目标）→ ADD x6 → ADD x7 → EOR x11 → STR x11` | 年轻指令与目标无数据依赖，仍受 ROB 顺序约束。 |
| C04 | 扩展数据依赖 | `ADD x10（目标）→ EOR x11,x10,x3 → ADD x12,x11,x4 → STR x12` | 存在数据依赖消费者，但 M004 不注入数据错误，只缺完成通知。 |
| C05 | 控制依赖/推测 | `CMP x3,x4 → B.EQ → ADD x10,x1,x2（目标）→ EOR x11,x10,x3 → STR x11` | 目标位于实际执行的分支路径。 |

## 3. 15 条独立传播链

每条链按 **具体子单元 → 故障操作 → 错误值/状态 → 实际消费者 → 计算结果 → 目的物理寄存器写回 → 后续消费者 → 覆盖/Squash/Repair/Commit → 软件结果** 展开。

### M004-C01

#### C01-T01（`RFWB-M004-C01-T01-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C01-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14795 PC=0x400834 `add	x10, x1, x2`；目的 PhysRegId=`110`，写回值 value=46。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14795（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14795 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14795 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83132 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C01-T02（`RFWB-M004-C01-T02-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C01-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14853 PC=0x400834 `add	x10, x1, x2`；目的 PhysRegId=`96`，写回值 value=38。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14853（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14853 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14853 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83080 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C01-T03（`RFWB-M004-C01-T03-F0`）

- 终态：`SQUASHED`；分类：`ACTIVATED_SQUASHED`；证据文件：`traces/RFWB-M004-C01-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14897 PC=0x400834 `add	x10, x1, x2`；目的 PhysRegId=`7`，写回值 value=30。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14897（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14897 — Commit 的 `instToCommit` 完成通知被跳过。
4. **Squash（OBSERVED）**：同一 Dynamic Seq=14897 出现 `M004_SQUASH`；目标在提交前被 squash。
5. **排除其他 Squash（OBSERVED）**：Trace 还有 seq=14908 的 squash 事件，其 Dynamic Seq 不等于故障目标，未计入本链。
6. **ROB/Commit**：无 ROB_HEAD_BLOCKED；目标未提交（squashed）。
7. **软件结果（OBSERVED）**：ROI_DONE 完成，OUT 与 Control 一致；分类 `ACTIVATED_SQUASHED`。

### M004-C02

#### C02-T01（`RFWB-M004-C02-T01-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C02-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14831 PC=0x400870 `eor	x10, x1, x2`；目的 PhysRegId=`88`，写回值 value=14。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14831（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14831 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14831 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83163 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C02-T02（`RFWB-M004-C02-T02-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C02-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14937 PC=0x400870 `eor	x10, x1, x2`；目的 PhysRegId=`111`，写回值 value=22。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14937（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14937 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14937 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83109 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C02-T03（`RFWB-M004-C02-T03-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C02-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=15089 PC=0x400870 `eor	x10, x1, x2`；目的 PhysRegId=`82`，写回值 value=30。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=15089（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=15089 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=15089 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83061 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

### M004-C03

#### C03-T01（`RFWB-M004-C03-T01-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C03-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14864 PC=0x4008ac `add	x10, x1, x2`；目的 PhysRegId=`71`，写回值 value=46。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14864（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14864 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14864 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83210 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C03-T02（`RFWB-M004-C03-T02-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C03-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14917 PC=0x4008ac `add	x10, x1, x2`；目的 PhysRegId=`110`，写回值 value=40。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14917（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14917 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14917 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83171 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C03-T03（`RFWB-M004-C03-T03-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C03-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14969 PC=0x4008ac `add	x10, x1, x2`；目的 PhysRegId=`83`，写回值 value=32。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14969（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14969 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14969 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83154 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

### M004-C04

#### C04-T01（`RFWB-M004-C04-T01-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C04-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14910 PC=0x4008f0 `add	x10, x1, x2`；目的 PhysRegId=`3`，写回值 value=46。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14910（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14910 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14910 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83185 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C04-T02（`RFWB-M004-C04-T02-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C04-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14988 PC=0x4008f0 `add	x10, x1, x2`；目的 PhysRegId=`69`，写回值 value=38。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14988（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14988 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14988 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83143 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C04-T03（`RFWB-M004-C04-T03-F0`）

- 终态：`SQUASHED`；分类：`ACTIVATED_SQUASHED`；证据文件：`traces/RFWB-M004-C04-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=15036 PC=0x4008f0 `add	x10, x1, x2`；目的 PhysRegId=`30`，写回值 value=30。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=15036（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=15036 — Commit 的 `instToCommit` 完成通知被跳过。
4. **Squash（OBSERVED）**：同一 Dynamic Seq=15036 出现 `M004_SQUASH`；目标在提交前被 squash。
5. **排除其他 Squash（OBSERVED）**：Trace 还有 seq=15048 的 squash 事件，其 Dynamic Seq 不等于故障目标，未计入本链。
6. **ROB/Commit**：无 ROB_HEAD_BLOCKED；目标未提交（squashed）。
7. **软件结果（OBSERVED）**：ROI_DONE 完成，OUT 与 Control 一致；分类 `ACTIVATED_SQUASHED`。

### M004-C05

#### C05-T01（`RFWB-M004-C05-T01-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C05-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14908 PC=0x40093c `add	x10, x1, x2`；目的 PhysRegId=`30`，写回值 value=46。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14908（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14908 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14908 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83161 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C05-T02（`RFWB-M004-C05-T02-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C05-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=14995 PC=0x40093c `add	x10, x1, x2`；目的 PhysRegId=`112`，写回值 value=40。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=14995（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=14995 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=14995 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83061 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

#### C05-T03（`RFWB-M004-C05-T03-F0`）

- 终态：`NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类：`ROB_HEAD_BLOCKED`；证据文件：`traces/RFWB-M004-C05-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：IEW → Commit 完成通知（instToCommit）；目标 seq=15043 PC=0x40093c `add	x10, x1, x2`；目的 PhysRegId=`98`，写回值 value=32。
2. **目标已执行（OBSERVED）**：`M004_EXECUTED` seq=15043（noFault=1），PRF 数据写回已发生；故障不修改 PRF 数据。
3. **故障操作（OBSERVED）**：`M004_SKIP_INSTTOCOMMIT` seq=15043 — Commit 的 `instToCommit` 完成通知被跳过。
4. **到达 ROB head（OBSERVED）**：目标 seq=15043 的最后一条 `M004_COMMIT_STALL` Dynamic Seq 与故障目标一致；head=1，canCommit=0；目标被跳过 instToCommit 后成为 ROB head。
5. **无 Squash（OBSERVED）**：目标没有同 Seq 的 `M004_SQUASH`；REE/GEM5 未撤销该指令。
6. **Commit 停滞（OBSERVED）**：`M004_COMMIT_STALL` 对目标 seq 记录 83041 次；最后一次 tick=49999950，达到 max_ticks=50000000 的终态。目标无 `M004_COMMIT`。
7. **ROI/软件结果（OBSERVED）**：无 `ROI_DONE`、无 `OUT`；终态 `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS`；分类 `ROB_HEAD_BLOCKED`。不得标记为软件输出或同版本数据消费者。

## 3A. DiagnosticOutcome（逐样本）

### DiagnosticOutcome（逐样本，原始终态保留）

| SampleRunID | Skip Seq | 目标 PC/指令 | Executed | 最后 Stall Seq | head | canCommit | Stall 次数 | 同 Seq Squash | 其他 Squash Seq | 最后 tick | ROI/OUT | 终态/分类 |
|---|---:|---|---|---|---:|---:|---:|---|---|---:|---|---|
| `RFWB-M004-C01-T01-F0` | 14795 | 0x400834 `add	x10, x1, x2` | YES | 14795 | 1 | 0 | 83132 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C01-T02-F0` | 14853 | 0x400834 `add	x10, x1, x2` | YES | 14853 | 1 | 0 | 83080 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C01-T03-F0` | 14897 | 0x400834 `add	x10, x1, x2` | YES | NA | NA | NA | 0 | YES | 14908 | 24375890 | ROI_DONE+OUT | `SQUASHED` / `ACTIVATED_SQUASHED` |
| `RFWB-M004-C02-T01-F0` | 14831 | 0x400870 `eor	x10, x1, x2` | YES | 14831 | 1 | 0 | 83163 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C02-T02-F0` | 14937 | 0x400870 `eor	x10, x1, x2` | YES | 14937 | 1 | 0 | 83109 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C02-T03-F0` | 15089 | 0x400870 `eor	x10, x1, x2` | YES | 15089 | 1 | 0 | 83061 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C03-T01-F0` | 14864 | 0x4008ac `add	x10, x1, x2` | YES | 14864 | 1 | 0 | 83210 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C03-T02-F0` | 14917 | 0x4008ac `add	x10, x1, x2` | YES | 14917 | 1 | 0 | 83171 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C03-T03-F0` | 14969 | 0x4008ac `add	x10, x1, x2` | YES | 14969 | 1 | 0 | 83154 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C04-T01-F0` | 14910 | 0x4008f0 `add	x10, x1, x2` | YES | 14910 | 1 | 0 | 83185 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C04-T02-F0` | 14988 | 0x4008f0 `add	x10, x1, x2` | YES | 14988 | 1 | 0 | 83143 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C04-T03-F0` | 15036 | 0x4008f0 `add	x10, x1, x2` | YES | NA | NA | NA | 0 | YES | 15048 | 24266550 | ROI_DONE+OUT | `SQUASHED` / `ACTIVATED_SQUASHED` |
| `RFWB-M004-C05-T01-F0` | 14908 | 0x40093c `add	x10, x1, x2` | YES | 14908 | 1 | 0 | 83161 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C05-T02-F0` | 14995 | 0x40093c `add	x10, x1, x2` | YES | 14995 | 1 | 0 | 83061 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |
| `RFWB-M004-C05-T03-F0` | 15043 | 0x40093c `add	x10, x1, x2` | YES | 15043 | 1 | 0 | 83041 | NO | NONE | 49999950 | NO_ROI_DONE/NO_OUT | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` / `ROB_HEAD_BLOCKED` |

说明：13 个 `ROB_HEAD_BLOCKED` 样本的最后一条 Commit Stall Seq 与故障目标一致、head=1、canCommit=0，达到 max_ticks 且没有 ROI_DONE/OUT；两个 `ACTIVATED_SQUASHED` 样本必须在同一 Dynamic Seq 上同时出现 Skip 与 Squash（C01-T03=14897，C04-T03=15036），其他 squash seq 只是同 Trace 事件，不计入。

## 4. 每个 Context 内 T01/T02/T03 的差异

| Context | Timing | 注入/目标 Seq | PhysRegId | Gen | 原始值/错误值 | 消费者 | 首差 | 分类 |
|---|---|---:|---:|---:|---|---|---|---|
| C01 | T01 | 14795 | 110 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C01 | T02 | 14853 | 96 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C01 | T03 | 14897 | 7 | 58 | 通知缺失 | 0 | 一致 | ACTIVATED_SQUASHED |
| C02 | T01 | 14831 | 88 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C02 | T02 | 14937 | 111 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C02 | T03 | 15089 | 82 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C03 | T01 | 14864 | 71 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C03 | T02 | 14917 | 110 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C03 | T03 | 14969 | 83 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C04 | T01 | 14910 | 3 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C04 | T02 | 14988 | 69 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C04 | T03 | 15036 | 30 | 73 | 通知缺失 | 0 | 一致 | ACTIVATED_SQUASHED |
| C05 | T01 | 14908 | 30 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C05 | T02 | 14995 | 112 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |
| C05 | T03 | 15043 | 98 | NA | 通知缺失 | 0 | <missing> | ROB_HEAD_BLOCKED |

### T01/T02/T03 差异

- **C01**：目标 Seq = 14795, 14853, 14897；分类 = ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED, ACTIVATED_SQUASHED；首差 = `<missing>` / `<missing>` / `一致`。
  - 同一 Context 内结果不同：T03 的目标动态实例在完成通知被跳过后、提交前被 squash，所以终态为 `ACTIVATED_SQUASHED`；T01/T02 到达 ROB head 并阻塞到 max_ticks。这不是数据位型差异，而是同一 Hook 命中的不同动态实例的 ROB 生命周期不同。
- **C02**：目标 Seq = 14831, 14937, 15089；分类 = ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED；首差 = `<missing>` / `<missing>` / `<missing>`。
- **C03**：目标 Seq = 14864, 14917, 14969；分类 = ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED；首差 = `<missing>` / `<missing>` / `<missing>`。
- **C04**：目标 Seq = 14910, 14988, 15036；分类 = ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED, ACTIVATED_SQUASHED；首差 = `<missing>` / `<missing>` / `一致`。
  - 同一 Context 内结果不同：T03 的目标动态实例在完成通知被跳过后、提交前被 squash，所以终态为 `ACTIVATED_SQUASHED`；T01/T02 到达 ROB head 并阻塞到 max_ticks。这不是数据位型差异，而是同一 Hook 命中的不同动态实例的 ROB 生命周期不同。
- **C05**：目标 Seq = 14908, 14995, 15043；分类 = ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED, ROB_HEAD_BLOCKED；首差 = `<missing>` / `<missing>` / `<missing>`。

## 5. 五个 Context 之间的差异

### 五个 Context 之间的差异

| Context | 机制类 | 汇编序列 | 观察到的差异 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2（目标完成通知跳过）→ EOR x11,x3,x4 → STR x11` | 目标数据写回存在，但完成通知缺失。 分类：ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED/ACTIVATED_SQUASHED |
| C02 | 激活/操作变化 | `EOR x10,x1,x2（目标）→ ADD x11,x3,x4 → STR x11` | 改变目标整数运算形式，通知抑制点不变。 分类：ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED |
| C03 | 弱依赖/最小后继 | `ADD x10（目标）→ ADD x6 → ADD x7 → EOR x11 → STR x11` | 年轻指令与目标无数据依赖，仍受 ROB 顺序约束。 分类：ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED |
| C04 | 扩展数据依赖 | `ADD x10（目标）→ EOR x11,x10,x3 → ADD x12,x11,x4 → STR x12` | 存在数据依赖消费者，但 M004 不注入数据错误，只缺完成通知。 分类：ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED/ACTIVATED_SQUASHED |
| C05 | 控制依赖/推测 | `CMP x3,x4 → B.EQ → ADD x10,x1,x2（目标）→ EOR x11,x10,x3 → STR x11` | 目标位于实际执行的分支路径。 分类：ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED/ROB_HEAD_BLOCKED |

## 6. 最终软件结果

### 最终软件结果（逐样本）

| SampleRunID | Context/Timing | 终态 | 分类 | 首差（Fault vs Control） |
|---|---|---|---|---|
| `RFWB-M004-C01-T01-F0` | C01/T01 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000016` |
| `RFWB-M004-C01-T02-F0` | C01/T02 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000016` |
| `RFWB-M004-C01-T03-F0` | C01/T03 | `SQUASHED` | `ACTIVATED_SQUASHED` | OUT 一致 |
| `RFWB-M004-C02-T01-F0` | C02/T01 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000056` |
| `RFWB-M004-C02-T02-F0` | C02/T02 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000056` |
| `RFWB-M004-C02-T03-F0` | C02/T03 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000056` |
| `RFWB-M004-C03-T01-F0` | C03/T01 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000082` |
| `RFWB-M004-C03-T02-F0` | C03/T02 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000082` |
| `RFWB-M004-C03-T03-F0` | C03/T03 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000082` |
| `RFWB-M004-C04-T01-F0` | C04/T01 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000038` |
| `RFWB-M004-C04-T02-F0` | C04/T02 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000038` |
| `RFWB-M004-C04-T03-F0` | C04/T03 | `SQUASHED` | `ACTIVATED_SQUASHED` | OUT 一致 |
| `RFWB-M004-C05-T01-F0` | C05/T01 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000008` |
| `RFWB-M004-C05-T02-F0` | C05/T02 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000008` |
| `RFWB-M004-C05-T03-F0` | C05/T03 | `NO_RETIREMENT_PROGRESS_BY_MAX_TICKS` | `ROB_HEAD_BLOCKED` | `<missing>` vs `OUT 0 0000000000000008` |

## 7. 诊断区分度总结

### 诊断区分度总结

M004 不修改数据，也没有同版本数据消费者。区分点是 **目标已执行、PRF 已写、instToCommit 被跳过、目标到达 ROB head 且 canCommit=0、直到 max_ticks**。13 个样本没有 ROI_DONE/OUT，不能标记为软件输出；两个 T03 样本在同一 Dynamic Seq 上被 squash（C01 seq=14897，C04 seq=15036），其他 squash 事件不得混入。

证据状态统一使用 `OBSERVED` / `INFERRED` / `NOT_OBSERVED`；不同 PhysRegId 或不同 AllocationGeneration 不合并，推断边不标记为直接观察。
