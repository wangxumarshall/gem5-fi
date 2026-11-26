# RF_WB_M005_Propagation_Report

> 权威生成器：`reproduction/gen_final_reports.py`（唯一权威报告生成器）。
> 基线：`2f4e00b434ec8690fbb8cb6965e435094de7e784`；原始 Trace 未改写。
> 证据标记：`OBSERVED` / `INFERRED` / `NOT_OBSERVED`。

## 1. 故障模型及具体子单元

**全局 Register Ready 置位漏发**

- 具体子单元：IEW 全局 ready bitmap（setReg 全局置位）
- 故障操作与持续性：每样本恰好一次首次激活；同一 Hook、同一错误操作、同一持续性（除非该 Context 的冻结定义另有说明）。
- 证据来源：Batch01/02/03 冻结 Trace；Batch02 旧 Trace 为 14 列，没有 gen 列时标 `NA`，不虚构代次。

## 2. C01–C05 上下文定义

| Context | 机制类 | 冻结汇编序列 | 说明 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2（真实 WB）→ PAD×24 → EOR x11,x10,x3 → STR x11` | 晚到 Rename 消费者绑定同一 tag/代次。 |
| C02 | 激活/操作变化 | `ADD x10,x1,x2（真实 WB）→ PAD×24 → ADD x11,x3,x10 → STR x11` | 改变消费者指令类型与源位置。 |
| C03 | 弱依赖/有限消费 | `ADD x10（真实 WB）→ PAD×24 → EOR x11,x10,x3 → ADD x11,x4,x5 → STR x11` | 单个晚到消费者；结果随后被覆盖。 |
| C04 | 扩展数据依赖 | `ADD x10（真实 WB）→ PAD×24 → EOR x11,x10,x3；ADD x12,x10,x4 → EOR x13,x11,x12 → STR x13` | 两个晚到消费者绑定同一 tag/代次。 |
| C05 | 控制依赖/推测 | `CMP x3,x4 / B.NE → PAD×24 → EOR x11,x10,x3 → STR x11` | 晚到消费者位于分支路径。 |

## 3. 15 条独立传播链

每条链按 **具体子单元 → 故障操作 → 错误值/状态 → 实际消费者 → 计算结果 → 目的物理寄存器写回 → 后续消费者 → 覆盖/Squash/Repair/Commit → 软件结果** 展开。

### M005-C01

#### C01-T01（`RFWB-M005-C01-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C01-T01-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14798 PC=0x400838 `add	x10, x1, x2`；写回 `phys=24`,`gen=71` value=46；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14798，`phys=24`,`gen=71`，value=46。
3. **消费者 Rename 1（OBSERVED）**：seq=14823 PC=0x40089c `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=14823 PC=0x40089c `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=14823 PC=0x40089c `eor	x11, x10, x3`；source index=1；读取 `phys=24`,`gen=71`，data=46（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=14823 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C01-T02（`RFWB-M005-C01-T02-F0-A3`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C01-T02-F0-A3.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14880 PC=0x400838 `add	x10, x1, x2`；写回 `phys=10`,`gen=39` value=42；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14880，`phys=10`,`gen=39`，value=42。
3. **消费者 Rename 1（OBSERVED）**：seq=14905 PC=0x40089c `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=14905 PC=0x40089c `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=14905 PC=0x40089c `eor	x11, x10, x3`；source index=1；读取 `phys=10`,`gen=39`，data=42（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=14905 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C01-T03（`RFWB-M005-C01-T03-F0-A3`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C01-T03-F0-A3.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15028 PC=0x400838 `add	x10, x1, x2`；写回 `phys=24`,`gen=73` value=34；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15028，`phys=24`,`gen=73`，value=34。
3. **消费者 Rename 1（OBSERVED）**：seq=15053 PC=0x40089c `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=15053 PC=0x40089c `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=15053 PC=0x40089c `eor	x11, x10, x3`；source index=1；读取 `phys=24`,`gen=73`，data=34（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=15053 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

### M005-C02

#### C02-T01（`RFWB-M005-C02-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C02-T01-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14834 PC=0x4008d8 `add	x10, x1, x2`；写回 `phys=117`,`gen=57` value=46；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14834，`phys=117`,`gen=57`，value=46。
3. **消费者 Rename 1（OBSERVED）**：seq=14859 PC=0x40093c `add	x11, x3, x10`；source index=0；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=14859 PC=0x40093c `add	x11, x3, x10`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=14859 PC=0x40093c `add	x11, x3, x10`；source index=0；读取 `phys=117`,`gen=57`，data=46（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=14859 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C02-T02（`RFWB-M005-C02-T02-F0-A3`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C02-T02-F0-A3.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14925 PC=0x4008d8 `add	x10, x1, x2`；写回 `phys=83`,`gen=70` value=42；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14925，`phys=83`,`gen=70`，value=42。
3. **消费者 Rename 1（OBSERVED）**：seq=14950 PC=0x40093c `add	x11, x3, x10`；source index=0；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=14950 PC=0x40093c `add	x11, x3, x10`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=14950 PC=0x40093c `add	x11, x3, x10`；source index=0；读取 `phys=83`,`gen=70`，data=42（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=14950 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C02-T03（`RFWB-M005-C02-T03-F0-A3`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C02-T03-F0-A3.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15100 PC=0x4008d8 `add	x10, x1, x2`；写回 `phys=29`,`gen=75` value=34；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15100，`phys=29`,`gen=75`，value=34。
3. **消费者 Rename 1（OBSERVED）**：seq=15125 PC=0x40093c `add	x11, x3, x10`；source index=0；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=15125 PC=0x40093c `add	x11, x3, x10`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=15125 PC=0x40093c `add	x11, x3, x10`；source index=0；读取 `phys=29`,`gen=75`，data=34（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=15125 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

### M005-C03

#### C03-T01（`RFWB-M005-C03-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C03-T01-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14867 PC=0x400978 `add	x10, x1, x2`；写回 `phys=49`,`gen=65` value=46；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14867，`phys=49`,`gen=65`，value=46。
3. **消费者 Rename 1（OBSERVED）**：seq=14892 PC=0x4009dc `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=14892 PC=0x4009dc `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=14892 PC=0x4009dc `eor	x11, x10, x3`；source index=1；读取 `phys=49`,`gen=65`，data=46（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=14892 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C03-T02（`RFWB-M005-C03-T02-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C03-T02-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15000 PC=0x400978 `add	x10, x1, x2`；写回 `phys=74`,`gen=79` value=40；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15000，`phys=74`,`gen=79`，value=40。
3. **消费者 Rename 1（OBSERVED）**：seq=15025 PC=0x4009dc `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=15025 PC=0x4009dc `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=15025 PC=0x4009dc `eor	x11, x10, x3`；source index=1；读取 `phys=74`,`gen=79`，data=40（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=15025 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C03-T03（`RFWB-M005-C03-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C03-T03-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15148 PC=0x400978 `add	x10, x1, x2`；写回 `phys=106`,`gen=77` value=32；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15148，`phys=106`,`gen=77`，value=32。
3. **消费者 Rename 1（OBSERVED）**：seq=15173 PC=0x4009dc `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=15173 PC=0x4009dc `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=15173 PC=0x4009dc `eor	x11, x10, x3`；source index=1；读取 `phys=106`,`gen=77`，data=32（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=15173 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

### M005-C04

#### C04-T01（`RFWB-M005-C04-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C04-T01-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14913 PC=0x400a1c `add	x10, x1, x2`；写回 `phys=122`,`gen=74` value=46；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14913，`phys=122`,`gen=74`，value=46。
3. **消费者 Rename 1（OBSERVED）**：seq=14938 PC=0x400a80 `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **消费者 Rename 2（OBSERVED）**：seq=14939 PC=0x400a84 `add	x12, x10, x4`；source index=1；`global=0`,`iq=1`,`target=1`。
5. **IQ Repair 1（OBSERVED）**：seq=14938 PC=0x400a80 `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
6. **IQ Repair 2（OBSERVED）**：seq=14939 PC=0x400a84 `add	x12, x10, x4`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
7. **消费者 PRF Read 1（OBSERVED）**：seq=14938 PC=0x400a80 `eor	x11, x10, x3`；source index=1；读取 `phys=122`,`gen=74`，data=46（正确数据，不是 faulted read）。
8. **消费者 PRF Read 2（OBSERVED）**：seq=14939 PC=0x400a84 `add	x12, x10, x4`；source index=1；读取 `phys=122`,`gen=74`，data=46（正确数据，不是 faulted read）。
9. **消费者 Commit 1（OBSERVED）**：seq=14938 出现 `M005_CONSUMER_COMMIT`。
10. **消费者 Commit 2（NOT_OBSERVED）**：seq=14939 只有 Rename/IQ Repair/Read 证据，未观察到 Commit；不得声称已提交。
11. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
12. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C04-T02（`RFWB-M005-C04-T02-F0-A3`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C04-T02-F0-A3.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15003 PC=0x400a1c `add	x10, x1, x2`；写回 `phys=117`,`gen=58` value=42；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15003，`phys=117`,`gen=58`，value=42。
3. **消费者 Rename 1（OBSERVED）**：seq=15028 PC=0x400a80 `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **消费者 Rename 2（OBSERVED）**：seq=15029 PC=0x400a84 `add	x12, x10, x4`；source index=1；`global=0`,`iq=1`,`target=1`。
5. **IQ Repair 1（OBSERVED）**：seq=15028 PC=0x400a80 `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
6. **IQ Repair 2（OBSERVED）**：seq=15029 PC=0x400a84 `add	x12, x10, x4`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
7. **消费者 PRF Read 1（OBSERVED）**：seq=15028 PC=0x400a80 `eor	x11, x10, x3`；source index=1；读取 `phys=117`,`gen=58`，data=42（正确数据，不是 faulted read）。
8. **消费者 PRF Read 2（OBSERVED）**：seq=15029 PC=0x400a84 `add	x12, x10, x4`；source index=1；读取 `phys=117`,`gen=58`，data=42（正确数据，不是 faulted read）。
9. **消费者 Commit 1（OBSERVED）**：seq=15028 出现 `M005_CONSUMER_COMMIT`。
10. **消费者 Commit 2（NOT_OBSERVED）**：seq=15029 只有 Rename/IQ Repair/Read 证据，未观察到 Commit；不得声称已提交。
11. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
12. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C04-T03（`RFWB-M005-C04-T03-F0-A3`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C04-T03-F0-A3.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15155 PC=0x400a1c `add	x10, x1, x2`；写回 `phys=100`,`gen=78` value=34；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15155，`phys=100`,`gen=78`，value=34。
3. **消费者 Rename 1（OBSERVED）**：seq=15180 PC=0x400a80 `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **消费者 Rename 2（OBSERVED）**：seq=15181 PC=0x400a84 `add	x12, x10, x4`；source index=1；`global=0`,`iq=1`,`target=1`。
5. **IQ Repair 1（OBSERVED）**：seq=15180 PC=0x400a80 `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
6. **IQ Repair 2（OBSERVED）**：seq=15181 PC=0x400a84 `add	x12, x10, x4`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
7. **消费者 PRF Read 1（OBSERVED）**：seq=15180 PC=0x400a80 `eor	x11, x10, x3`；source index=1；读取 `phys=100`,`gen=78`，data=34（正确数据，不是 faulted read）。
8. **消费者 PRF Read 2（OBSERVED）**：seq=15181 PC=0x400a84 `add	x12, x10, x4`；source index=1；读取 `phys=100`,`gen=78`，data=34（正确数据，不是 faulted read）。
9. **消费者 Commit 1（OBSERVED）**：seq=15180 出现 `M005_CONSUMER_COMMIT`。
10. **消费者 Commit 2（NOT_OBSERVED）**：seq=15181 只有 Rename/IQ Repair/Read 证据，未观察到 Commit；不得声称已提交。
11. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
12. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

### M005-C05

#### C05-T01（`RFWB-M005-C05-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C05-T01-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=14907 PC=0x400ac4 `add	x10, x1, x2`；写回 `phys=9`,`gen=57` value=46；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=14907，`phys=9`,`gen=57`，value=46。
3. **消费者 Rename 1（OBSERVED）**：seq=14935 PC=0x400b34 `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=14935 PC=0x400b34 `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=14935 PC=0x400b34 `eor	x11, x10, x3`；source index=1；读取 `phys=9`,`gen=57`，data=46（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=14935 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C05-T02（`RFWB-M005-C05-T02-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C05-T02-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15059 PC=0x400ac4 `add	x10, x1, x2`；写回 `phys=115`,`gen=67` value=40；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15059，`phys=115`,`gen=67`，value=40。
3. **消费者 Rename 1（OBSERVED）**：seq=15087 PC=0x400b34 `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=15087 PC=0x400b34 `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=15087 PC=0x400b34 `eor	x11, x10, x3`；source index=1；读取 `phys=115`,`gen=67`，data=40（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=15087 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C05-T03（`RFWB-M005-C05-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M005-C05-T03-F0.csv`。

**传播链：**

1. **生产者 WB（OBSERVED）**：seq=15251 PC=0x400ac4 `add	x10, x1, x2`；写回 `phys=67`,`gen=83` value=32；`M005_WB` extra=`global_before=0,iq_ready=1`。
2. **故障操作（OBSERVED）**：`M005_SKIP_GLOBAL_READY` 在生产者 WB 时跳过全局 ready 置位；目标 seq=15251，`phys=67`,`gen=83`，value=32。
3. **消费者 Rename 1（OBSERVED）**：seq=15279 PC=0x400b34 `eor	x11, x10, x3`；source index=1；`global=0`,`iq=1`,`target=1`。
4. **IQ Repair 1（OBSERVED）**：seq=15279 PC=0x400b34 `eor	x11, x10, x3`；`target=1` — IQ 独立 scoreboard 补标，不是全局 ready 恢复。
5. **消费者 PRF Read 1（OBSERVED）**：seq=15279 PC=0x400b34 `eor	x11, x10, x3`；source index=1；读取 `phys=67`,`gen=83`，data=32（正确数据，不是 faulted read）。
6. **消费者 Commit 1（OBSERVED）**：seq=15279 出现 `M005_CONSUMER_COMMIT`。
7. **下游结果写回（NOT_OBSERVED）**：M005 Trace 未记录消费者目的寄存器写回事件；不得补写下游值。
8. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

## 4. 每个 Context 内 T01/T02/T03 的差异

| Context | Timing | 注入/目标 Seq | PhysRegId | Gen | 原始值/错误值 | 消费者 | 首差 | 分类 |
|---|---|---:|---:|---:|---|---|---|---|
| C01 | T01 | 14798 | 24 | 71 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C01 | T02 | 14880 | 10 | 39 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C01 | T03 | 15028 | 24 | 73 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C02 | T01 | 14834 | 117 | 57 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C02 | T02 | 14925 | 83 | 70 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C02 | T03 | 15100 | 29 | 75 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T01 | 14867 | 49 | 65 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T02 | 15000 | 74 | 79 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T03 | 15148 | 106 | 77 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C04 | T01 | 14913 | 122 | 74 | 正确数据 | 2 | 一致 | ACTIVATED_MASKED |
| C04 | T02 | 15003 | 117 | 58 | 正确数据 | 2 | 一致 | ACTIVATED_MASKED |
| C04 | T03 | 15155 | 100 | 78 | 正确数据 | 2 | 一致 | ACTIVATED_MASKED |
| C05 | T01 | 14907 | 9 | 57 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C05 | T02 | 15059 | 115 | 67 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |
| C05 | T03 | 15251 | 67 | 83 | 正确数据 | 1 | 一致 | ACTIVATED_MASKED |

### T01/T02/T03 差异

M005 的 Timing 不是对总 WB 数取分位，而是对修正后的 `WB-before-Rename` eligible 事件取 ordinal：C01/C02/C04 的 N=6（1/3/6），C03/C05 的 N=8（1/4/8）。六个 −A3 样本使用实际 A3 AttemptID。

- **C01**：目标 Seq = 14798, 14880, 15028；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C02**：目标 Seq = 14834, 14925, 15100；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C03**：目标 Seq = 14867, 15000, 15148；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C04**：目标 Seq = 14913, 15003, 15155；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C05**：目标 Seq = 14907, 15059, 15251；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。

## 5. 五个 Context 之间的差异

### 五个 Context 之间的差异

| Context | 机制类 | 汇编序列 | 观察到的差异 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2（真实 WB）→ PAD×24 → EOR x11,x10,x3 → STR x11` | 晚到 Rename 消费者绑定同一 tag/代次。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C02 | 激活/操作变化 | `ADD x10,x1,x2（真实 WB）→ PAD×24 → ADD x11,x3,x10 → STR x11` | 改变消费者指令类型与源位置。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C03 | 弱依赖/有限消费 | `ADD x10（真实 WB）→ PAD×24 → EOR x11,x10,x3 → ADD x11,x4,x5 → STR x11` | 单个晚到消费者；结果随后被覆盖。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C04 | 扩展数据依赖 | `ADD x10（真实 WB）→ PAD×24 → EOR x11,x10,x3；ADD x12,x10,x4 → EOR x13,x11,x12 → STR x13` | 两个晚到消费者绑定同一 tag/代次。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C05 | 控制依赖/推测 | `CMP x3,x4 / B.NE → PAD×24 → EOR x11,x10,x3 → STR x11` | 晚到消费者位于分支路径。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |

## 6. 最终软件结果

### 最终软件结果（逐样本）

| SampleRunID | Context/Timing | 终态 | 分类 | 首差（Fault vs Control） |
|---|---|---|---|---|
| `RFWB-M005-C01-T01-F0` | C01/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C01-T02-F0-A3` | C01/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C01-T03-F0-A3` | C01/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C02-T01-F0` | C02/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C02-T02-F0-A3` | C02/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C02-T03-F0-A3` | C02/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C03-T01-F0` | C03/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C03-T02-F0` | C03/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C03-T03-F0` | C03/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C04-T01-F0` | C04/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C04-T02-F0-A3` | C04/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C04-T03-F0-A3` | C04/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C05-T01-F0` | C05/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C05-T02-F0` | C05/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M005-C05-T03-F0` | C05/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |

## 7. 诊断区分度总结

### 诊断区分度总结

M005 不修改 PRF 数据，也没有 faulted read。区分点是 **WB 已发生、全局 ready 被跳过、消费者 Rename 时 global=0/iq=1、IQ Repair 补标、随后正确读取并提交**。C04 有两个消费者；第二个只有 Rename/IQ Repair/Read 证据时不得声称已提交。下游结果写回没有 Trace 事件，统一标 NOT_OBSERVED。

证据状态统一使用 `OBSERVED` / `INFERRED` / `NOT_OBSERVED`；不同 PhysRegId 或不同 AllocationGeneration 不合并，推断边不标记为直接观察。
