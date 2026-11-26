# RF_WB_M001_Propagation_Report

> 权威生成器：`reproduction/gen_final_reports.py`（唯一权威报告生成器）。
> 基线：`2f4e00b434ec8690fbb8cb6965e435094de7e784`；原始 Trace 未改写。
> 证据标记：`OBSERVED` / `INFERRED` / `NOT_OBSERVED`。

## 1. 故障模型及具体子单元

**GPR Physical Register File 驻留值单比特翻转**

- 具体子单元：GPR PRF 驻留槽位（SimpleFreeList 分配，flat PhysRegId + AllocationGeneration）
- 故障操作与持续性：每样本恰好一次首次激活；同一 Hook、同一错误操作、同一持续性（除非该 Context 的冻结定义另有说明）。
- 证据来源：Batch01/02/03 冻结 Trace；Batch02 旧 Trace 为 14 列，没有 gen 列时标 `NA`，不虚构代次。

## 2. C01–C05 上下文定义

| Context | 机制类 | 冻结汇编序列 | 说明 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2 → ADD x12,x10,x3 → EOR x11,x10,x3 → STR x11` | 两个直接消费者（ADD/EOR）读取同一 x10 版本；输出 x11。 |
| C02 | 激活/访问条件变化 | `ADD x10,x1,x2 → ADD x12,x10,x3 → ADD x11,x10,x3 → STR x11` | 消费者算术形式由 EOR 改为 ADD；输出 x11。 |
| C03 | 弱依赖/覆盖 | `ADD x10,x1,x2 → ADD x12,x10,x3 → ADD x10,x4,x5 → EOR x11,x10,x3 → STR x11` | seq+1 重新定义 x10（x4+x5），旧版本只在 seq 消费一次；输出消费新版本。 |
| C04 | 扩展数据依赖 | `ADD x10,x1,x2 → ADD x12,x10,x3 → EOR x11,x10,x3 → ADD x12,x10,x4 → EOR x13,x11,x12 → STR x13` | 同一 x10 旧版本被三个消费者读取，随后 EOR 合并 x11 与 x12 两个新版本；输出 x13。 |
| C05 | 控制依赖/推测 | `ADD x10,x1,x2 → ADD x12,x10,x3 → CMP x10,x3 → B.EQ → EOR/ADD x11,x10,x4 → STR x11` | CMP 读取故障版本并决定分支方向；两个分支路径都消费 x10，输出 x11。 |

## 3. 15 条独立传播链

每条链按 **具体子单元 → 故障操作 → 错误值/状态 → 实际消费者 → 计算结果 → 目的物理寄存器写回 → 后续消费者 → 覆盖/Squash/Repair/Commit → 软件结果** 展开。

### M001-C01

#### C01-T01（`RFWB-M001-C01-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C01-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=30`，AllocationGeneration=`56`；seq=14731 PC=0x400834 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 46。
2. **故障操作（OBSERVED）**：seq=14732 PC=0x400838 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：46 → 47。
3. **错误值/状态（OBSERVED）**：PRF[`phys=30`,`gen=56`] = 47；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14732 PC=0x400838 `add	x12, x10, x3`；source index=1，读取 `phys=30`,`gen=56` → 错误值 47。
5. **计算 / 目的写回（OBSERVED）**：seq=14732 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=33`,`gen=75` value=85。
6. **实际消费者 2（OBSERVED）**：seq=14733 PC=0x40083c `eor	x11, x10, x3`；source index=1，读取 `phys=30`,`gen=56` → 错误值 47。
7. **计算 / 目的写回（OBSERVED）**：seq=14733 `eor	x11, x10, x3` → 目的物理寄存器写回 `phys=47`,`gen=57` value=9。
8. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000009` vs Control `OUT 0 0000000000000008`；分类 `ACTIVATED_SDC`。

#### C01-T02（`RFWB-M001-C01-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C01-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=84`，AllocationGeneration=`74`；seq=14781 PC=0x400834 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 40。
2. **故障操作（OBSERVED）**：seq=14782 PC=0x400838 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：40 → 41。
3. **错误值/状态（OBSERVED）**：PRF[`phys=84`,`gen=74`] = 41；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14782 PC=0x400838 `add	x12, x10, x3`；source index=1，读取 `phys=84`,`gen=74` → 错误值 41。
5. **计算 / 目的写回（OBSERVED）**：seq=14782 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=59`,`gen=72` value=76。
6. **实际消费者 2（OBSERVED）**：seq=14783 PC=0x40083c `eor	x11, x10, x3`；source index=1，读取 `phys=84`,`gen=74` → 错误值 41。
7. **计算 / 目的写回（OBSERVED）**：seq=14783 `eor	x11, x10, x3` → 目的物理寄存器写回 `phys=70`,`gen=76` value=10。
8. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000000a` vs Control `OUT 3 000000000000000b`；分类 `ACTIVATED_SDC`。

#### C01-T03（`RFWB-M001-C01-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C01-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=10`，AllocationGeneration=`41`；seq=14829 PC=0x400834 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 32。
2. **故障操作（OBSERVED）**：seq=14830 PC=0x400838 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：32 → 33。
3. **错误值/状态（OBSERVED）**：PRF[`phys=10`,`gen=41`] = 33；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14830 PC=0x400838 `add	x12, x10, x3`；source index=1，读取 `phys=10`,`gen=41` → 错误值 33。
5. **计算 / 目的写回（OBSERVED）**：seq=14830 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=49`,`gen=81` value=64。
6. **实际消费者 2（OBSERVED）**：seq=14831 PC=0x40083c `eor	x11, x10, x3`；source index=1，读取 `phys=10`,`gen=41` → 错误值 33。
7. **计算 / 目的写回（OBSERVED）**：seq=14831 `eor	x11, x10, x3` → 目的物理寄存器写回 `phys=121`,`gen=69` value=62。
8. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 7 000000000000003e` vs Control `OUT 7 000000000000003f`；分类 `ACTIVATED_SDC`。

### M001-C02

#### C02-T01（`RFWB-M001-C02-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C02-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=58`，AllocationGeneration=`75`；seq=14767 PC=0x400874 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 46。
2. **故障操作（OBSERVED）**：seq=14768 PC=0x400878 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：46 → 47。
3. **错误值/状态（OBSERVED）**：PRF[`phys=58`,`gen=75`] = 47；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14768 PC=0x400878 `add	x12, x10, x3`；source index=1，读取 `phys=58`,`gen=75` → 错误值 47。
5. **计算 / 目的写回（OBSERVED）**：seq=14768 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=54`,`gen=59` value=85。
6. **实际消费者 2（OBSERVED）**：seq=14769 PC=0x40087c `add	x11, x10, x3`；source index=1，读取 `phys=58`,`gen=75` → 错误值 47。
7. **计算 / 目的写回（OBSERVED）**：seq=14769 `add	x11, x10, x3` → 目的物理寄存器写回 `phys=31`,`gen=51` value=85。
8. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000055` vs Control `OUT 0 0000000000000054`；分类 `ACTIVATED_SDC`。

#### C02-T02（`RFWB-M001-C02-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C02-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=3`，AllocationGeneration=`80`；seq=14876 PC=0x400874 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 40。
2. **故障操作（OBSERVED）**：seq=14877 PC=0x400878 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：40 → 41。
3. **错误值/状态（OBSERVED）**：PRF[`phys=3`,`gen=80`] = 41；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14877 PC=0x400878 `add	x12, x10, x3`；source index=1，读取 `phys=3`,`gen=80` → 错误值 41。
5. **计算 / 目的写回（OBSERVED）**：seq=14877 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=35`,`gen=67` value=76。
6. **实际消费者 2（OBSERVED）**：seq=14878 PC=0x40087c `add	x11, x10, x3`；source index=1，读取 `phys=3`,`gen=80` → 错误值 41。
7. **计算 / 目的写回（OBSERVED）**：seq=14878 `add	x11, x10, x3` → 目的物理寄存器写回 `phys=49`,`gen=81` value=76。
8. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000004c` vs Control `OUT 3 000000000000004b`；分类 `ACTIVATED_SDC`。

#### C02-T03（`RFWB-M001-C02-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C02-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=81`，AllocationGeneration=`64`；seq=14924 PC=0x400874 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 32。
2. **故障操作（OBSERVED）**：seq=14925 PC=0x400878 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：32 → 33。
3. **错误值/状态（OBSERVED）**：PRF[`phys=81`,`gen=64`] = 33；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14925 PC=0x400878 `add	x12, x10, x3`；source index=1，读取 `phys=81`,`gen=64` → 错误值 33。
5. **计算 / 目的写回（OBSERVED）**：seq=14925 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=90`,`gen=78` value=64。
6. **实际消费者 2（OBSERVED）**：seq=14926 PC=0x40087c `add	x11, x10, x3`；source index=1，读取 `phys=81`,`gen=64` → 错误值 33。
7. **计算 / 目的写回（OBSERVED）**：seq=14926 `add	x11, x10, x3` → 目的物理寄存器写回 `phys=106`,`gen=61` value=64。
8. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 7 0000000000000040` vs Control `OUT 7 000000000000003f`；分类 `ACTIVATED_SDC`。

### M001-C03

#### C03-T01（`RFWB-M001-C03-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M001-C03-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=12`，AllocationGeneration=`46`；seq=14800 PC=0x4008b4 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 46。
2. **故障操作（OBSERVED）**：seq=14801 PC=0x4008b8 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：46 → 47。
3. **错误值/状态（OBSERVED）**：PRF[`phys=12`,`gen=46`] = 47；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14801 PC=0x4008b8 `add	x12, x10, x3`；source index=1，读取 `phys=12`,`gen=46` → 错误值 47。
5. **计算 / 目的写回（OBSERVED）**：seq=14801 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=113`,`gen=76` value=85。
6. **覆盖/重新定义（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14802 PC=0x4008bc `add	x10, x4, x5` 写 `phys=123`,`gen=66` value=106。该指令源为 x4,x5，不读取被翻转的旧 x10 版本；它不是 seq=14801 的消费者，而是 x10 的新版本。
7. **后续消费者（数据流 INFERRED）**：seq=14803 PC=0x4008c0 `eor	x11, x10, x3` 按汇编读取新 x10 版本并写 `phys=5`,`gen=70` value=76；Trace 未记录该源读，绑定关系由寄存器重定义推断。
8. **覆盖/Squash/Repair/Commit**：旧错误版本只被 seq=14801 读取一次，其结果未被后续读取；新版本覆盖后无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 完全一致；分类 `ACTIVATED_MASKED`（错误被覆盖/未进入输出）。

#### C03-T02（`RFWB-M001-C03-T02-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M001-C03-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=48`，AllocationGeneration=`72`；seq=14869 PC=0x4008b4 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 40。
2. **故障操作（OBSERVED）**：seq=14870 PC=0x4008b8 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：40 → 41。
3. **错误值/状态（OBSERVED）**：PRF[`phys=48`,`gen=72`] = 41；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14870 PC=0x4008b8 `add	x12, x10, x3`；source index=1，读取 `phys=48`,`gen=72` → 错误值 41。
5. **计算 / 目的写回（OBSERVED）**：seq=14870 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=8`,`gen=74` value=76。
6. **覆盖/重新定义（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14871 PC=0x4008bc `add	x10, x4, x5` 写 `phys=29`,`gen=59` value=100。该指令源为 x4,x5，不读取被翻转的旧 x10 版本；它不是 seq=14870 的消费者，而是 x10 的新版本。
7. **后续消费者（数据流 INFERRED）**：seq=14872 PC=0x4008c0 `eor	x11, x10, x3` 按汇编读取新 x10 版本并写 `phys=4`,`gen=74` value=71；Trace 未记录该源读，绑定关系由寄存器重定义推断。
8. **覆盖/Squash/Repair/Commit**：旧错误版本只被 seq=14870 读取一次，其结果未被后续读取；新版本覆盖后无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 完全一致；分类 `ACTIVATED_MASKED`（错误被覆盖/未进入输出）。

#### C03-T03（`RFWB-M001-C03-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M001-C03-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=35`，AllocationGeneration=`68`；seq=14953 PC=0x4008b4 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 32。
2. **故障操作（OBSERVED）**：seq=14954 PC=0x4008b8 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：32 → 33。
3. **错误值/状态（OBSERVED）**：PRF[`phys=35`,`gen=68`] = 33；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14954 PC=0x4008b8 `add	x12, x10, x3`；source index=1，读取 `phys=35`,`gen=68` → 错误值 33。
5. **计算 / 目的写回（OBSERVED）**：seq=14954 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=6`,`gen=75` value=64。
6. **覆盖/重新定义（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14955 PC=0x4008bc `add	x10, x4, x5` 写 `phys=3`,`gen=81` value=92。该指令源为 x4,x5，不读取被翻转的旧 x10 版本；它不是 seq=14954 的消费者，而是 x10 的新版本。
7. **后续消费者（数据流 INFERRED）**：seq=14956 PC=0x4008c0 `eor	x11, x10, x3` 按汇编读取新 x10 版本并写 `phys=73`,`gen=67` value=67；Trace 未记录该源读，绑定关系由寄存器重定义推断。
8. **覆盖/Squash/Repair/Commit**：旧错误版本只被 seq=14954 读取一次，其结果未被后续读取；新版本覆盖后无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 完全一致；分类 `ACTIVATED_MASKED`（错误被覆盖/未进入输出）。

### M001-C04

#### C04-T01（`RFWB-M001-C04-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M001-C04-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=26`，AllocationGeneration=`62`；seq=14846 PC=0x4008f8 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 46。
2. **故障操作（OBSERVED）**：seq=14847 PC=0x4008fc `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：46 → 47。
3. **错误值/状态（OBSERVED）**：PRF[`phys=26`,`gen=62`] = 47；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14847 PC=0x4008fc `add	x12, x10, x3`；source index=1，读取 `phys=26`,`gen=62` → 错误值 47。
5. **计算 / 目的写回（OBSERVED）**：seq=14847 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=68`,`gen=71` value=85。
6. **实际消费者 2（OBSERVED）**：seq=14848 PC=0x400900 `eor	x11, x10, x3`；source index=1，读取 `phys=26`,`gen=62` → 错误值 47。
7. **计算 / 目的写回（OBSERVED）**：seq=14848 `eor	x11, x10, x3` → 目的物理寄存器写回 `phys=30`,`gen=57` value=9。
8. **实际消费者 3（OBSERVED）**：seq=14849 PC=0x400904 `add	x12, x10, x4`；source index=1，读取 `phys=26`,`gen=62` → 错误值 47。
9. **计算 / 目的写回（OBSERVED）**：seq=14849 `add	x12, x10, x4` → 目的物理寄存器写回 `phys=85`,`gen=78` value=95。
10. **多消费者扇出与汇合（读取/写回 OBSERVED，逐源绑定 INFERRED）**：同一旧 x10 版本被多个消费者读取；随后 `EOR x13,x11,x12` 合并 x11 与 x12 两个新版本。EOR 的逐源绑定由汇编寄存器名给出。
11. **汇合目的写回（OBSERVED）**：seq=14850 PC=0x400908 `eor	x13, x11, x12` 写 x13 `phys=73`,`gen=66` value=86。
12. **覆盖效应（OBSERVED 输出，原因 INFERRED）**：本 Timing 的最终 x13 与 Control 相同；x11 与 x12 携带同一 bit 偏移，EOR 合并时该位抵消。由 Trace 实测写回值：seq=14847 dest=x12 value=85; seq=14848 dest=x11 value=9; seq=14849 dest=x12 value=95。因此本样本为 MASKED，而不是错误未传播。
13. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
14. **软件结果（OBSERVED）**：OUT 与 Control 完全一致；分类 `ACTIVATED_MASKED`（错误被覆盖/未进入输出）。

#### C04-T02（`RFWB-M001-C04-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C04-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=21`，AllocationGeneration=`79`；seq=14918 PC=0x4008f8 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 40。
2. **故障操作（OBSERVED）**：seq=14919 PC=0x4008fc `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：40 → 41。
3. **错误值/状态（OBSERVED）**：PRF[`phys=21`,`gen=79`] = 41；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14919 PC=0x4008fc `add	x12, x10, x3`；source index=1，读取 `phys=21`,`gen=79` → 错误值 41。
5. **计算 / 目的写回（OBSERVED）**：seq=14919 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=78`,`gen=59` value=76。
6. **实际消费者 2（OBSERVED）**：seq=14920 PC=0x400900 `eor	x11, x10, x3`；source index=1，读取 `phys=21`,`gen=79` → 错误值 41。
7. **计算 / 目的写回（OBSERVED）**：seq=14920 `eor	x11, x10, x3` → 目的物理寄存器写回 `phys=81`,`gen=64` value=10。
8. **实际消费者 3（OBSERVED）**：seq=14921 PC=0x400904 `add	x12, x10, x4`；source index=1，读取 `phys=21`,`gen=79` → 错误值 41。
9. **计算 / 目的写回（OBSERVED）**：seq=14921 `add	x12, x10, x4` → 目的物理寄存器写回 `phys=90`,`gen=78` value=86。
10. **多消费者扇出与汇合（读取/写回 OBSERVED，逐源绑定 INFERRED）**：同一旧 x10 版本被多个消费者读取；随后 `EOR x13,x11,x12` 合并 x11 与 x12 两个新版本。EOR 的逐源绑定由汇编寄存器名给出。
11. **汇合目的写回（OBSERVED）**：seq=14922 PC=0x400908 `eor	x13, x11, x12` 写 x13 `phys=106`,`gen=61` value=92。
12. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
13. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000005c` vs Control `OUT 3 000000000000005e`；分类 `ACTIVATED_SDC`。

#### C04-T03（`RFWB-M001-C04-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C04-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=26`，AllocationGeneration=`63`；seq=14974 PC=0x4008f8 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 32。
2. **故障操作（OBSERVED）**：seq=14975 PC=0x4008fc `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：32 → 33。
3. **错误值/状态（OBSERVED）**：PRF[`phys=26`,`gen=63`] = 33；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14975 PC=0x4008fc `add	x12, x10, x3`；source index=1，读取 `phys=26`,`gen=63` → 错误值 33。
5. **计算 / 目的写回（OBSERVED）**：seq=14975 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=85`,`gen=79` value=64。
6. **实际消费者 2（OBSERVED）**：seq=14976 PC=0x400900 `eor	x11, x10, x3`；source index=1，读取 `phys=26`,`gen=63` → 错误值 33。
7. **计算 / 目的写回（OBSERVED）**：seq=14976 `eor	x11, x10, x3` → 目的物理寄存器写回 `phys=30`,`gen=58` value=62。
8. **实际消费者 3（OBSERVED）**：seq=14977 PC=0x400904 `add	x12, x10, x4`；source index=1，读取 `phys=26`,`gen=63` → 错误值 33。
9. **计算 / 目的写回（OBSERVED）**：seq=14977 `add	x12, x10, x4` → 目的物理寄存器写回 `phys=65`,`gen=68` value=74。
10. **多消费者扇出与汇合（读取/写回 OBSERVED，逐源绑定 INFERRED）**：同一旧 x10 版本被多个消费者读取；随后 `EOR x13,x11,x12` 合并 x11 与 x12 两个新版本。EOR 的逐源绑定由汇编寄存器名给出。
11. **汇合目的写回（OBSERVED）**：seq=14978 PC=0x400908 `eor	x13, x11, x12` 写 x13 `phys=1`,`gen=62` value=116。
12. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
13. **软件结果（OBSERVED）**：首差 `OUT 7 0000000000000074` vs Control `OUT 7 0000000000000076`；分类 `ACTIVATED_SDC`。

### M001-C05

#### C05-T01（`RFWB-M001-C05-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C05-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=14`，AllocationGeneration=`15`；seq=14840 PC=0x400940 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 38。
2. **故障操作（OBSERVED）**：seq=14841 PC=0x400944 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：38 → 39。
3. **错误值/状态（OBSERVED）**：PRF[`phys=14`,`gen=15`] = 39；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14841 PC=0x400944 `add	x12, x10, x3`；source index=1，读取 `phys=14`,`gen=15` → 错误值 39。
5. **计算 / 目的写回（OBSERVED）**：seq=14841 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=46`,`gen=76` value=77。
6. **实际消费者 2（OBSERVED）**：seq=14842 PC=0x400948 `cmp	x10, x3`；source index=1，读取 `phys=14`,`gen=15` → 错误值 39。
7. **计算 / 目的写回（OBSERVED）**：seq=14842 `cmp	x10, x3` → NZCV 物理标志写回 `phys=141`,`gen=6` value=0; NZCV 物理标志写回 `phys=140`,`gen=6` value=0; NZCV 物理标志写回 `phys=139`,`gen=6` value=1。
8. **实际消费者 3（OBSERVED）**：seq=14844 PC=0x400950 `eor	x11, x10, x4`；source index=1，读取 `phys=14`,`gen=15` → 错误值 39。
9. **计算 / 目的写回（OBSERVED）**：seq=14844 `eor	x11, x10, x4` → 目的物理寄存器写回 `phys=26`,`gen=62` value=23。
10. **控制依赖（读取 OBSERVED，方向 INFERRED）**：seq=14842 `cmp	x10, x3` 读取被翻转值并写 NZCV；该比较结果决定 B.EQ 方向。
11. **实际执行路径（读取 OBSERVED）**：Trace 在 seq=14844 PC=0x400950 `eor	x11, x10, x4` 记录到对故障版本的读取；该路径即实际执行的分支路径。
12. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
13. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000017` vs Control `OUT 0 0000000000000056`；分类 `ACTIVATED_SDC`。

#### C05-T02（`RFWB-M001-C05-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C05-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=126`，AllocationGeneration=`71`；seq=14949 PC=0x400940 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 35。
2. **故障操作（OBSERVED）**：seq=14950 PC=0x400944 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：35 → 34。
3. **错误值/状态（OBSERVED）**：PRF[`phys=126`,`gen=71`] = 34；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=14950 PC=0x400944 `add	x12, x10, x3`；source index=1，读取 `phys=126`,`gen=71` → 错误值 34。
5. **计算 / 目的写回（OBSERVED）**：seq=14950 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=21`,`gen=79` value=69。
6. **实际消费者 2（OBSERVED）**：seq=14951 PC=0x400948 `cmp	x10, x3`；source index=1，读取 `phys=126`,`gen=71` → 错误值 34。
7. **计算 / 目的写回（OBSERVED）**：seq=14951 `cmp	x10, x3` → NZCV 物理标志写回 `phys=184`,`gen=6` value=2; NZCV 物理标志写回 `phys=183`,`gen=6` value=0; NZCV 物理标志写回 `phys=182`,`gen=6` value=0。
8. **实际消费者 3（OBSERVED）**：seq=14953 PC=0x400958 `add	x11, x10, x4`；source index=1，读取 `phys=126`,`gen=71` → 错误值 34。
9. **计算 / 目的写回（OBSERVED）**：seq=14953 `add	x11, x10, x4` → 目的物理寄存器写回 `phys=16`,`gen=76` value=79。
10. **实际消费者 4（OBSERVED）**：seq=14976 PC=0x400950 `eor	x11, x10, x4`；source index=1，读取 `phys=126`,`gen=71` → 错误值 34。
11. **计算 / 目的写回（OBSERVED）**：seq=14976 `eor	x11, x10, x4` → 目的物理寄存器写回 `phys=90`,`gen=78` value=15。
12. **控制依赖（读取 OBSERVED，方向 INFERRED）**：seq=14951 `cmp	x10, x3` 读取被翻转值并写 NZCV；该比较结果决定 B.EQ 方向。
13. **实际执行路径（读取 OBSERVED）**：Trace 在 seq=14953 PC=0x400958 `add	x11, x10, x4` 记录到对故障版本的读取；该路径即实际执行的分支路径。
14. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
15. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000000f` vs Control `OUT 3 0000000000000050`；分类 `ACTIVATED_SDC`。

#### C05-T03（`RFWB-M001-C05-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M001-C05-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=1`，AllocationGeneration=`62`；seq=15005 PC=0x400940 `add	x10, x1, x2`；`PRODUCER_WRITE` 原值 31。
2. **故障操作（OBSERVED）**：seq=15006 PC=0x400944 `add	x12, x10, x3` 的 marker 读命中；`M001_INJECT` 对同版本 PRF 驻留值执行 bit0 翻转：31 → 30。
3. **错误值/状态（OBSERVED）**：PRF[`phys=1`,`gen=62`] = 30；错误只存在于该驻留版本，不改变后续新分配版本。
4. **实际消费者 1（OBSERVED）**：seq=15006 PC=0x400944 `add	x12, x10, x3`；source index=1，读取 `phys=1`,`gen=62` → 错误值 30。
5. **计算 / 目的写回（OBSERVED）**：seq=15006 `add	x12, x10, x3` → 目的物理寄存器写回 `phys=67`,`gen=65` value=61。
6. **实际消费者 2（OBSERVED）**：seq=15007 PC=0x400948 `cmp	x10, x3`；source index=1，读取 `phys=1`,`gen=62` → 错误值 30。
7. **计算 / 目的写回（OBSERVED）**：seq=15007 `cmp	x10, x3` → NZCV 物理标志写回 `phys=198`,`gen=6` value=2; NZCV 物理标志写回 `phys=199`,`gen=6` value=0; NZCV 物理标志写回 `phys=200`,`gen=6` value=0。
8. **实际消费者 3（OBSERVED）**：seq=15009 PC=0x400958 `add	x11, x10, x4`；source index=1，读取 `phys=1`,`gen=62` → 错误值 30。
9. **计算 / 目的写回（OBSERVED）**：seq=15009 `add	x11, x10, x4` → 目的物理寄存器写回 `phys=27`,`gen=55` value=71。
10. **实际消费者 4（OBSERVED）**：seq=15032 PC=0x400950 `eor	x11, x10, x4`；source index=1，读取 `phys=1`,`gen=62` → 错误值 30。
11. **计算 / 目的写回（OBSERVED）**：seq=15032 `eor	x11, x10, x4` → 目的物理寄存器写回 `phys=8`,`gen=75` value=55。
12. **控制依赖（读取 OBSERVED，方向 INFERRED）**：seq=15007 `cmp	x10, x3` 读取被翻转值并写 NZCV；该比较结果决定 B.EQ 方向。
13. **实际执行路径（读取 OBSERVED）**：Trace 在 seq=15009 PC=0x400958 `add	x11, x10, x4` 记录到对故障版本的读取；该路径即实际执行的分支路径。
14. **覆盖/Squash/Repair/Commit**：无覆盖写、无 squash、无 repair；Commit 未单独记录（NOT_OBSERVED）。
15. **软件结果（OBSERVED）**：首差 `OUT 7 0000000000000037` vs Control `OUT 7 0000000000000048`；分类 `ACTIVATED_SDC`。

## 4. 每个 Context 内 T01/T02/T03 的差异

| Context | Timing | 注入/目标 Seq | PhysRegId | Gen | 原始值/错误值 | 消费者 | 首差 | 分类 |
|---|---|---:|---:|---:|---|---|---|---|
| C01 | T01 | 14732 | 30 | 56 | 46→47 | 2 | OUT 0 0000000000000009 | ACTIVATED_SDC |
| C01 | T02 | 14782 | 84 | 74 | 40→41 | 2 | OUT 3 000000000000000a | ACTIVATED_SDC |
| C01 | T03 | 14830 | 10 | 41 | 32→33 | 2 | OUT 7 000000000000003e | ACTIVATED_SDC |
| C02 | T01 | 14768 | 58 | 75 | 46→47 | 2 | OUT 0 0000000000000055 | ACTIVATED_SDC |
| C02 | T02 | 14877 | 3 | 80 | 40→41 | 2 | OUT 3 000000000000004c | ACTIVATED_SDC |
| C02 | T03 | 14925 | 81 | 64 | 32→33 | 2 | OUT 7 0000000000000040 | ACTIVATED_SDC |
| C03 | T01 | 14801 | 12 | 46 | 46→47 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T02 | 14870 | 48 | 72 | 40→41 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T03 | 14954 | 35 | 68 | 32→33 | 1 | 一致 | ACTIVATED_MASKED |
| C04 | T01 | 14847 | 26 | 62 | 46→47 | 3 | 一致 | ACTIVATED_MASKED |
| C04 | T02 | 14919 | 21 | 79 | 40→41 | 3 | OUT 3 000000000000005c | ACTIVATED_SDC |
| C04 | T03 | 14975 | 26 | 63 | 32→33 | 3 | OUT 7 0000000000000074 | ACTIVATED_SDC |
| C05 | T01 | 14841 | 14 | 15 | 38→39 | 3 | OUT 0 0000000000000017 | ACTIVATED_SDC |
| C05 | T02 | 14950 | 126 | 71 | 35→34 | 4 | OUT 3 000000000000000f | ACTIVATED_SDC |
| C05 | T03 | 15006 | 1 | 62 | 31→30 | 4 | OUT 7 0000000000000037 | ACTIVATED_SDC |

### T01/T02/T03 差异

- **C01**：目标 Seq = 14732, 14782, 14830；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000009` / `OUT 3 000000000000000a` / `OUT 7 000000000000003e`。
- **C02**：目标 Seq = 14768, 14877, 14925；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000055` / `OUT 3 000000000000004c` / `OUT 7 0000000000000040`。
- **C03**：目标 Seq = 14801, 14870, 14954；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C04**：目标 Seq = 14847, 14919, 14975；分类 = ACTIVATED_MASKED, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `一致` / `OUT 3 000000000000005c` / `OUT 7 0000000000000074`。
  - 同一 Context 内结果不同：不同 ordinal 对应不同数据位型/消费者实例；Hook 与错误操作相同，差异只来自被选动态实例。
- **C05**：目标 Seq = 14841, 14950, 15006；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000017` / `OUT 3 000000000000000f` / `OUT 7 0000000000000037`。

## 5. 五个 Context 之间的差异

### 五个 Context 之间的差异

| Context | 机制类 | 汇编序列 | 观察到的差异 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2 → ADD x12,x10,x3 → EOR x11,x10,x3 → STR x11` | 两个直接消费者（ADD/EOR）读取同一 x10 版本；输出 x11。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |
| C02 | 激活/访问条件变化 | `ADD x10,x1,x2 → ADD x12,x10,x3 → ADD x11,x10,x3 → STR x11` | 消费者算术形式由 EOR 改为 ADD；输出 x11。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |
| C03 | 弱依赖/覆盖 | `ADD x10,x1,x2 → ADD x12,x10,x3 → ADD x10,x4,x5 → EOR x11,x10,x3 → STR x11` | seq+1 重新定义 x10（x4+x5），旧版本只在 seq 消费一次；输出消费新版本。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C04 | 扩展数据依赖 | `ADD x10,x1,x2 → ADD x12,x10,x3 → EOR x11,x10,x3 → ADD x12,x10,x4 → EOR x13,x11,x12 → STR x13` | 同一 x10 旧版本被三个消费者读取，随后 EOR 合并 x11 与 x12 两个新版本；输出 x13。 分类：ACTIVATED_MASKED/ACTIVATED_SDC/ACTIVATED_SDC |
| C05 | 控制依赖/推测 | `ADD x10,x1,x2 → ADD x12,x10,x3 → CMP x10,x3 → B.EQ → EOR/ADD x11,x10,x4 → STR x11` | CMP 读取故障版本并决定分支方向；两个分支路径都消费 x10，输出 x11。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |

## 6. 最终软件结果

### 最终软件结果（逐样本）

| SampleRunID | Context/Timing | 终态 | 分类 | 首差（Fault vs Control） |
|---|---|---|---|---|
| `RFWB-M001-C01-T01-F0` | C01/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000009` vs `OUT 0 0000000000000008` |
| `RFWB-M001-C01-T02-F0` | C01/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000000a` vs `OUT 3 000000000000000b` |
| `RFWB-M001-C01-T03-F0` | C01/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 000000000000003e` vs `OUT 7 000000000000003f` |
| `RFWB-M001-C02-T01-F0` | C02/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000055` vs `OUT 0 0000000000000054` |
| `RFWB-M001-C02-T02-F0` | C02/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000004c` vs `OUT 3 000000000000004b` |
| `RFWB-M001-C02-T03-F0` | C02/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 0000000000000040` vs `OUT 7 000000000000003f` |
| `RFWB-M001-C03-T01-F0` | C03/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M001-C03-T02-F0` | C03/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M001-C03-T03-F0` | C03/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M001-C04-T01-F0` | C04/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M001-C04-T02-F0` | C04/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000005c` vs `OUT 3 000000000000005e` |
| `RFWB-M001-C04-T03-F0` | C04/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 0000000000000074` vs `OUT 7 0000000000000076` |
| `RFWB-M001-C05-T01-F0` | C05/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000017` vs `OUT 0 0000000000000056` |
| `RFWB-M001-C05-T02-F0` | C05/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000000f` vs `OUT 3 0000000000000050` |
| `RFWB-M001-C05-T03-F0` | C05/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 0000000000000037` vs `OUT 7 0000000000000048` |

## 7. 诊断区分度总结

### 诊断区分度总结

M001 修改的是 **GPR PRF 驻留值**：同一 `PhysRegId + AllocationGeneration` 的所有后续读取都会看到坏值。因此区分点是“同版本读返回坏值”，而不是“读端口瞬时错误”。C03 的旧版本只被读取一次，随后 `ADD x10,x4,x5` 建立新版本；输出消费新版本，错误被覆盖。C04 展示多消费者扇出，其中 T01 因 EOR 合并时同一翻转位抵消而 MASKED；C05 展示 CMP/分支控制依赖，错误值改变执行路径。

证据状态统一使用 `OBSERVED` / `INFERRED` / `NOT_OBSERVED`；不同 PhysRegId 或不同 AllocationGeneration 不合并，推断边不标记为直接观察。
