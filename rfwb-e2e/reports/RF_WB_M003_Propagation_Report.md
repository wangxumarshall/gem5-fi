# RF_WB_M003_Propagation_Report

> 权威生成器：`reproduction/gen_final_reports.py`（唯一权威报告生成器）。
> 基线：`2f4e00b434ec8690fbb8cb6965e435094de7e784`；原始 Trace 未改写。
> 证据标记：`OBSERVED` / `INFERRED` / `NOT_OBSERVED`。

## 1. 故障模型及具体子单元

**Register Read Port 返回值瞬态翻转**

- 具体子单元：Rename/Read Port 返回副本（PRF 读出的临时值，不回写 PRF）
- 故障操作与持续性：每样本恰好一次首次激活；同一 Hook、同一错误操作、同一持续性（除非该 Context 的冻结定义另有说明）。
- 证据来源：Batch01/02/03 冻结 Trace；Batch02 旧 Trace 为 14 列，没有 gen 列时标 `NA`，不虚构代次。

## 2. C01–C05 上下文定义

| Context | 机制类 | 冻结汇编序列 | 说明 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2 → EOR x11,x10,x3（读返回翻转）→ ADD x12,x10,x11 → STR x11` | 错误返回副本进入 x11，并被后续 ADD 与输出消费。 |
| C02 | 激活/访问条件变化 | `ADD x10,x1,x2 → EOR x11,x3,x10（源序号 1）→ ADD x12,x10,x11 → STR x11` | 目标源在 EOR 中位于不同 operand index；只翻转该 source 的返回副本。 |
| C03 | 弱依赖/覆盖 | `ADD x10,x1,x2 → EOR x11,x10,x3 → ADD x11,x4,x5 → STR x11` | 错误 x11 在下一指令被新版本覆盖；输出消费新版本。 |
| C04 | 扩展数据依赖 | `ADD x10,x1,x2 → EOR x11,x10,x3 → ADD x12,x10,x4 → EOR x13,x11,x12 → STR x13` | 错误返回只进入 x11；x13 合并 x11 与正确 x12。 |
| C05 | 控制依赖/推测 | `ADD x10,x1,x2 → CMP x3,x4 → B.EQ → EOR x11,x10,x4 → STR x11` | 目标读位于分支路径；CMP 恒等，目标 EOR 实际执行。 |

## 3. 15 条独立传播链

每条链按 **具体子单元 → 故障操作 → 错误值/状态 → 实际消费者 → 计算结果 → 目的物理寄存器写回 → 后续消费者 → 覆盖/Squash/Repair/Commit → 软件结果** 展开。

### M003-C01

#### C01-T01（`RFWB-M003-C01-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C01-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=30`；生产者 seq=14731, pc=0x400834, phys=30, gen=56 写回原值 46。
2. **故障操作（OBSERVED）**：seq=14732 PC=0x400838 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 38 → 返回 39。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`38` 与 return=`39`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14732 `eor	x11, x10, x3` → `phys=33`,`gen=75` value=9。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=26` 共记录 90 次读，出现代次 100,101,103,104,105,106…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=38 / return=39 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000009` vs Control `OUT 0 0000000000000008`；分类 `ACTIVATED_SDC`。

#### C01-T02（`RFWB-M003-C01-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C01-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=84`；生产者 seq=14781, pc=0x400834, phys=84, gen=74 写回原值 40。
2. **故障操作（OBSERVED）**：seq=14782 PC=0x400838 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 35 → 返回 34。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`35` 与 return=`34`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14782 `eor	x11, x10, x3` → `phys=59`,`gen=72` value=10。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=99` 共记录 111 次读，出现代次 100,101,103,104,106,107…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=35 / return=34 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000000a` vs Control `OUT 3 000000000000000b`；分类 `ACTIVATED_SDC`。

#### C01-T03（`RFWB-M003-C01-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C01-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=10`；生产者 seq=14829, pc=0x400834, phys=10, gen=41 写回原值 32。
2. **故障操作（OBSERVED）**：seq=14830 PC=0x400838 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 31 → 返回 30。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`31` 与 return=`30`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14830 `eor	x11, x10, x3` → `phys=49`,`gen=81` value=62。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=100` 共记录 119 次读，出现代次 100,101,102,103,104,105…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=31 / return=30 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 7 000000000000003e` vs Control `OUT 7 000000000000003f`；分类 `ACTIVATED_SDC`。

### M003-C02

#### C02-T01（`RFWB-M003-C02-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C02-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=58`；生产者 seq=14767, pc=0x400874, phys=58, gen=75 写回原值 46。
2. **故障操作（OBSERVED）**：seq=14768 PC=0x400878 `eor	x11, x3, x10` 的指定 source index=1 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 38 → 返回 39。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`38` 与 return=`39`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14768 `eor	x11, x3, x10` → `phys=54`,`gen=59` value=9。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=63` 共记录 137 次读，出现代次 101,102,104,105,106,108…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=38 / return=39 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000009` vs Control `OUT 0 0000000000000008`；分类 `ACTIVATED_SDC`。

#### C02-T02（`RFWB-M003-C02-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C02-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=3`；生产者 seq=14876, pc=0x400874, phys=3, gen=80 写回原值 40。
2. **故障操作（OBSERVED）**：seq=14877 PC=0x400878 `eor	x11, x3, x10` 的指定 source index=1 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 35 → 返回 34。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`35` 与 return=`34`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14877 `eor	x11, x3, x10` → `phys=35`,`gen=67` value=10。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=71` 共记录 111 次读，出现代次 100,102,103,105,106,107…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=35 / return=34 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000000a` vs Control `OUT 3 000000000000000b`；分类 `ACTIVATED_SDC`。

#### C02-T03（`RFWB-M003-C02-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C02-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=81`；生产者 seq=14924, pc=0x400874, phys=81, gen=64 写回原值 32。
2. **故障操作（OBSERVED）**：seq=14925 PC=0x400878 `eor	x11, x3, x10` 的指定 source index=1 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 31 → 返回 30。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`31` 与 return=`30`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14925 `eor	x11, x3, x10` → `phys=90`,`gen=78` value=62。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=16` 共记录 119 次读，出现代次 100,101,102,103,104,105…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=31 / return=30 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 7 000000000000003e` vs Control `OUT 7 000000000000003f`；分类 `ACTIVATED_SDC`。

### M003-C03

#### C03-T01（`RFWB-M003-C03-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M003-C03-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=12`；生产者 seq=14800, pc=0x4008b4, phys=12, gen=46 写回原值 46。
2. **故障操作（OBSERVED）**：seq=14801 PC=0x4008b8 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 38 → 返回 39。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`38` 与 return=`39`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14801 `eor	x11, x10, x3` → `phys=113`,`gen=76` value=9。
5. **覆盖/重新定义（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14802 PC=0x4008bc `add	x11, x4, x5` 写 `phys=123`,`gen=66` value=106；该指令源为 x4,x5，不读取故障返回副本，是 x11 的新版本。
6. **后续消费者（INFERRED）**：`STR x11` 消费新版本；旧错误 x11 未被后续指令读取（同版本后续读 NOT_OBSERVED）。
7. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=51` 共记录 162 次读，出现代次 100,101,103,104,106,108…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=38 / return=39 同行记录。
8. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C03-T02（`RFWB-M003-C03-T02-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M003-C03-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=6`；生产者 seq=14858, pc=0x4008b4, phys=6, gen=74 写回原值 40。
2. **故障操作（OBSERVED）**：seq=14859 PC=0x4008b8 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 35 → 返回 34。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`35` 与 return=`34`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14859 `eor	x11, x10, x3` → `phys=35`,`gen=67` value=10。
5. **覆盖/重新定义（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14860 PC=0x4008bc `add	x11, x4, x5` 写 `phys=0`,`gen=75` value=100；该指令源为 x4,x5，不读取故障返回副本，是 x11 的新版本。
6. **后续消费者（INFERRED）**：`STR x11` 消费新版本；旧错误 x11 未被后续指令读取（同版本后续读 NOT_OBSERVED）。
7. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=85` 共记录 97 次读，出现代次 100,102,104,105,106,107…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=35 / return=34 同行记录。
8. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

#### C03-T03（`RFWB-M003-C03-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M003-C03-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=116`；生产者 seq=14906, pc=0x4008b4, phys=116, gen=78 写回原值 32。
2. **故障操作（OBSERVED）**：seq=14907 PC=0x4008b8 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 31 → 返回 30。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`31` 与 return=`30`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14907 `eor	x11, x10, x3` → `phys=87`,`gen=75` value=62。
5. **覆盖/重新定义（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14908 PC=0x4008bc `add	x11, x4, x5` 写 `phys=88`,`gen=79` value=92；该指令源为 x4,x5，不读取故障返回副本，是 x11 的新版本。
6. **后续消费者（INFERRED）**：`STR x11` 消费新版本；旧错误 x11 未被后续指令读取（同版本后续读 NOT_OBSERVED）。
7. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=49` 共记录 88 次读，出现代次 101,103,105,106,107,110…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=31 / return=30 同行记录。
8. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`。

### M003-C04

#### C04-T01（`RFWB-M003-C04-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C04-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=26`；生产者 seq=14846, pc=0x4008f4, phys=26, gen=62 写回原值 46。
2. **故障操作（OBSERVED）**：seq=14847 PC=0x4008f8 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 38 → 返回 39。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`38` 与 return=`39`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14847 `eor	x11, x10, x3` → `phys=68`,`gen=71` value=9。
5. **后续消费者（INFERRED）**：错误返回只进入 x11；`ADD x12,x10,x4` 使用正确 x10，`EOR x13,x11,x12` 合并 x11 与正确 x12。逐源绑定由汇编给出，Trace 未记录这些读（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=32` 共记录 91 次读，出现代次 101,102,103,104,105,107…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=38 / return=39 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000057` vs Control `OUT 0 0000000000000056`；分类 `ACTIVATED_SDC`。

#### C04-T02（`RFWB-M003-C04-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C04-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=124`；生产者 seq=14915, pc=0x4008f4, phys=124, gen=62 写回原值 40。
2. **故障操作（OBSERVED）**：seq=14916 PC=0x4008f8 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 35 → 返回 34。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`35` 与 return=`34`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14916 `eor	x11, x10, x3` → `phys=74`,`gen=78` value=10。
5. **后续消费者（INFERRED）**：错误返回只进入 x11；`ADD x12,x10,x4` 使用正确 x10，`EOR x13,x11,x12` 合并 x11 与正确 x12。逐源绑定由汇编给出，Trace 未记录这些读（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=122` 共记录 131 次读，出现代次 101,102,103,104,105,107…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=35 / return=34 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000005f` vs Control `OUT 3 000000000000005e`；分类 `ACTIVATED_SDC`。

#### C04-T03（`RFWB-M003-C04-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C04-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=86`；生产者 seq=14967, pc=0x4008f4, phys=86, gen=64 写回原值 32。
2. **故障操作（OBSERVED）**：seq=14968 PC=0x4008f8 `eor	x11, x10, x3` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 31 → 返回 30。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`31` 与 return=`30`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14968 `eor	x11, x10, x3` → `phys=96`,`gen=64` value=62。
5. **后续消费者（INFERRED）**：错误返回只进入 x11；`ADD x12,x10,x4` 使用正确 x10，`EOR x13,x11,x12` 合并 x11 与正确 x12。逐源绑定由汇编给出，Trace 未记录这些读（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=55` 共记录 124 次读，出现代次 101,102,103,104,105,106…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=31 / return=30 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 7 0000000000000077` vs Control `OUT 7 0000000000000076`；分类 `ACTIVATED_SDC`。

### M003-C05

#### C05-T01（`RFWB-M003-C05-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C05-T01-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=14`；生产者 seq=14840, pc=0x400938, phys=14, gen=15 写回原值 46。
2. **故障操作（OBSERVED）**：seq=14865 PC=0x40094c `eor	x11, x10, x4` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 38 → 返回 39。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`38` 与 return=`39`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14865 `eor	x11, x10, x4` → `phys=3`,`gen=80` value=9。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=83` 共记录 80 次读，出现代次 100,102,103,106,108,109…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=38 / return=39 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 0 0000000000000009` vs Control `OUT 0 0000000000000008`；分类 `ACTIVATED_SDC`。

#### C05-T02（`RFWB-M003-C05-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C05-T02-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=51`；生产者 seq=14938, pc=0x400938, phys=51, gen=73 写回原值 40。
2. **故障操作（OBSERVED）**：seq=14941 PC=0x40094c `eor	x11, x10, x4` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 35 → 返回 34。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`35` 与 return=`34`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14941 `eor	x11, x10, x4` → `phys=108`,`gen=57` value=10。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=84` 共记录 160 次读，出现代次 100,102,103,106,109,110…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=35 / return=34 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 3 000000000000000a` vs Control `OUT 3 000000000000000b`；分类 `ACTIVATED_SDC`。

#### C05-T03（`RFWB-M003-C05-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M003-C05-T03-F0.csv`。

**传播链：**

1. **子单元/生产者（OBSERVED）**：GPR PRF `phys=30`；生产者 seq=14990, pc=0x400938, phys=30, gen=58 写回原值 32。
2. **故障操作（OBSERVED）**：seq=14993 PC=0x40094c `eor	x11, x10, x4` 的指定 source index=0 命中 read-return Hook；`M003_INJECT` 只翻转返回副本：PRF 原值 31 → 返回 30。
3. **错误值/状态（OBSERVED）**：同一 Trace 行给出 PRF 驻留值 value=`31` 与 return=`30`；错误只在返回副本，PRF 本体未被修改。
4. **计算结果 / 目的物理寄存器写回（OBSERVED）**：seq=14993 `eor	x11, x10, x4` → `phys=68`,`gen=72` value=62。
5. **后续消费者（INFERRED）**：错误值随目标目的寄存器进入后续指令/输出；具体读绑定由汇编给出，Trace 未逐源记录（INFERRED）。
6. **PRF 驻留值完整性检查（OBSERVED，单独口径）**：`M003_PRF_READ` 对同一物理槽位 `phys=73` 共记录 160 次读，出现代次 100,102,103,104,106,107…；这些是槽位复用后的 PRF 正确读，不是本次故障版本的消费者。PRF 本体正确的直接证据是上面的 value=31 / return=30 同行记录。
7. **覆盖/Squash/Repair/Commit**：无 squash、无 M005 repair；Commit 未单独记录（NOT_OBSERVED）。
8. **软件结果（OBSERVED）**：首差 `OUT 7 000000000000003e` vs Control `OUT 7 000000000000003f`；分类 `ACTIVATED_SDC`。

## 4. 每个 Context 内 T01/T02/T03 的差异

| Context | Timing | 注入/目标 Seq | PhysRegId | Gen | 原始值/错误值 | 消费者 | 首差 | 分类 |
|---|---|---:|---:|---:|---|---|---|---|
| C01 | T01 | 14732 | 26 | 61 | 38→39 | 1 | OUT 0 0000000000000009 | ACTIVATED_SDC |
| C01 | T02 | 14782 | 99 | 70 | 35→34 | 1 | OUT 3 000000000000000a | ACTIVATED_SDC |
| C01 | T03 | 14830 | 100 | 75 | 31→30 | 1 | OUT 7 000000000000003e | ACTIVATED_SDC |
| C02 | T01 | 14768 | 63 | 64 | 38→39 | 1 | OUT 0 0000000000000009 | ACTIVATED_SDC |
| C02 | T02 | 14877 | 71 | 69 | 35→34 | 1 | OUT 3 000000000000000a | ACTIVATED_SDC |
| C02 | T03 | 14925 | 16 | 76 | 31→30 | 1 | OUT 7 000000000000003e | ACTIVATED_SDC |
| C03 | T01 | 14801 | 51 | 72 | 38→39 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T02 | 14859 | 85 | 78 | 35→34 | 1 | 一致 | ACTIVATED_MASKED |
| C03 | T03 | 14907 | 49 | 81 | 31→30 | 1 | 一致 | ACTIVATED_MASKED |
| C04 | T01 | 14847 | 32 | 70 | 38→39 | 1 | OUT 0 0000000000000057 | ACTIVATED_SDC |
| C04 | T02 | 14916 | 122 | 76 | 35→34 | 1 | OUT 3 000000000000005f | ACTIVATED_SDC |
| C04 | T03 | 14968 | 55 | 60 | 31→30 | 1 | OUT 7 0000000000000077 | ACTIVATED_SDC |
| C05 | T01 | 14865 | 83 | 76 | 38→39 | 1 | OUT 0 0000000000000009 | ACTIVATED_SDC |
| C05 | T02 | 14941 | 84 | 75 | 35→34 | 1 | OUT 3 000000000000000a | ACTIVATED_SDC |
| C05 | T03 | 14993 | 73 | 67 | 31→30 | 1 | OUT 7 000000000000003e | ACTIVATED_SDC |

### T01/T02/T03 差异

- **C01**：目标 Seq = 14732, 14782, 14830；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000009` / `OUT 3 000000000000000a` / `OUT 7 000000000000003e`。
- **C02**：目标 Seq = 14768, 14877, 14925；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000009` / `OUT 3 000000000000000a` / `OUT 7 000000000000003e`。
- **C03**：目标 Seq = 14801, 14859, 14907；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C04**：目标 Seq = 14847, 14916, 14968；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000057` / `OUT 3 000000000000005f` / `OUT 7 0000000000000077`。
- **C05**：目标 Seq = 14865, 14941, 14993；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 0000000000000009` / `OUT 3 000000000000000a` / `OUT 7 000000000000003e`。

## 5. 五个 Context 之间的差异

### 五个 Context 之间的差异

| Context | 机制类 | 汇编序列 | 观察到的差异 |
|---|---|---|---|
| C01 | 基准激活 | `ADD x10,x1,x2 → EOR x11,x10,x3（读返回翻转）→ ADD x12,x10,x11 → STR x11` | 错误返回副本进入 x11，并被后续 ADD 与输出消费。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |
| C02 | 激活/访问条件变化 | `ADD x10,x1,x2 → EOR x11,x3,x10（源序号 1）→ ADD x12,x10,x11 → STR x11` | 目标源在 EOR 中位于不同 operand index；只翻转该 source 的返回副本。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |
| C03 | 弱依赖/覆盖 | `ADD x10,x1,x2 → EOR x11,x10,x3 → ADD x11,x4,x5 → STR x11` | 错误 x11 在下一指令被新版本覆盖；输出消费新版本。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C04 | 扩展数据依赖 | `ADD x10,x1,x2 → EOR x11,x10,x3 → ADD x12,x10,x4 → EOR x13,x11,x12 → STR x13` | 错误返回只进入 x11；x13 合并 x11 与正确 x12。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |
| C05 | 控制依赖/推测 | `ADD x10,x1,x2 → CMP x3,x4 → B.EQ → EOR x11,x10,x4 → STR x11` | 目标读位于分支路径；CMP 恒等，目标 EOR 实际执行。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |

## 6. 最终软件结果

### 最终软件结果（逐样本）

| SampleRunID | Context/Timing | 终态 | 分类 | 首差（Fault vs Control） |
|---|---|---|---|---|
| `RFWB-M003-C01-T01-F0` | C01/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000009` vs `OUT 0 0000000000000008` |
| `RFWB-M003-C01-T02-F0` | C01/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000000a` vs `OUT 3 000000000000000b` |
| `RFWB-M003-C01-T03-F0` | C01/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 000000000000003e` vs `OUT 7 000000000000003f` |
| `RFWB-M003-C02-T01-F0` | C02/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000009` vs `OUT 0 0000000000000008` |
| `RFWB-M003-C02-T02-F0` | C02/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000000a` vs `OUT 3 000000000000000b` |
| `RFWB-M003-C02-T03-F0` | C02/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 000000000000003e` vs `OUT 7 000000000000003f` |
| `RFWB-M003-C03-T01-F0` | C03/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M003-C03-T02-F0` | C03/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M003-C03-T03-F0` | C03/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M003-C04-T01-F0` | C04/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000057` vs `OUT 0 0000000000000056` |
| `RFWB-M003-C04-T02-F0` | C04/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000005f` vs `OUT 3 000000000000005e` |
| `RFWB-M003-C04-T03-F0` | C04/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 0000000000000077` vs `OUT 7 0000000000000076` |
| `RFWB-M003-C05-T01-F0` | C05/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 0000000000000009` vs `OUT 0 0000000000000008` |
| `RFWB-M003-C05-T02-F0` | C05/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 000000000000000a` vs `OUT 3 000000000000000b` |
| `RFWB-M003-C05-T03-F0` | C05/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 000000000000003e` vs `OUT 7 000000000000003f` |

## 7. 诊断区分度总结

### 诊断区分度总结

M003 修改的是 **Read Port 返回副本**：同一行的 `value`（PRF 驻留值）保持正确，`return` 才是错误值。`M003_PRF_READ` 只用于 PRF 驻留值完整性检查，且通常是槽位复用后的不同代次，不能当作错误返回值的后续消费者。C03 的错误 x11 被新版本覆盖；其余 Context 展示直接、多级与控制依赖传播。

证据状态统一使用 `OBSERVED` / `INFERRED` / `NOT_OBSERVED`；不同 PhysRegId 或不同 AllocationGeneration 不合并，推断边不标记为直接观察。
