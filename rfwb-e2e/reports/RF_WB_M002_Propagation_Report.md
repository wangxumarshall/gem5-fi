# RF_WB_M002_Propagation_Report

> 权威生成器：`reproduction/gen_final_reports.py`（唯一权威报告生成器）。
> 基线：`2f4e00b434ec8690fbb8cb6965e435094de7e784`；原始 Trace 未改写。
> 证据标记：`OBSERVED` / `INFERRED` / `NOT_OBSERVED`。

## 1. 故障模型及具体子单元

**FP/SIMD Physical Register File 目标 byte 清零**

- 具体子单元：FP/SIMD VecReg writable operand 的 shadow 写入代理（EOR .16B 目的）
- 故障操作与持续性：每样本恰好一次首次激活；同一 Hook、同一错误操作、同一持续性（除非该 Context 的冻结定义另有说明）。
- 证据来源：Batch01/02/03 冻结 Trace；Batch02 旧 Trace 为 14 列，没有 gen 列时标 `NA`，不虚构代次。

## 2. C01–C05 上下文定义

| Context | 机制类 | 冻结汇编序列 | 说明 |
|---|---|---|---|
| C01 | 基准激活 | `EOR V0.16B,V1,V2 → STR Q0` | 目标 byte 0 被清零后由 STR Q0 输出。 |
| C02 | 激活/访问条件变化 | `EOR V0.16B,V1,V2 → STR Q0` | 输入位型与目标 byte 改为 byte 5；由 STR Q0 输出。 |
| C03 | 弱依赖/覆盖 | `EOR V0,V1,V2 → EOR V0,V3,V4 → STR Q0` | 同一 VecReg 槽位被新代次覆盖；消费者只读取新代次。 |
| C04 | 扩展数据依赖 | `EOR V0,V1,V2 → EOR V3,V0,V4 → ADDV B5,V3.16B → STR Q0` | EOR V3 与 STR Q0 消费故障 v0；ADDV 消费 V3（数据流由汇编给出）。 |
| C05 | 控制依赖/推测 | `EOR V0,V1,V2 → CMEQ V3,V0,V4 → ADDV B5,V3 → UMOV W6,V5.B[0] → CBZ → STR Q0` | CMEQ/ADDV/UMOV/CBZ 依赖故障 v0；实际输出为 STR Q0。 |

## 3. 15 条独立传播链

每条链按 **具体子单元 → 故障操作 → 错误值/状态 → 实际消费者 → 计算结果 → 目的物理寄存器写回 → 后续消费者 → 覆盖/Squash/Repair/Commit → 软件结果** 展开。

### M002-C01

#### C01-T01（`RFWB-M002-C01-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C01-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14771 PC=0x400880 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`45`，AllocationGeneration=`14`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `0` 清零；`M002_COMMIT` 记录 byte=0、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=45`,`gen=14` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14772 PC=0x400884 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=0:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14773 PC=0x400884 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=0:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：首差 `OUT 0 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C01-T02（`RFWB-M002-C01-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C01-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14813 PC=0x400880 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`2`，AllocationGeneration=`7`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `0` 清零；`M002_COMMIT` 记录 byte=0、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=2`,`gen=7` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14814 PC=0x400884 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=2`,`gen=7`；该指令共 1 条读事件；bytes16=0:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14815 PC=0x400884 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=2`,`gen=7`；该指令共 1 条读事件；bytes16=0:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：首差 `OUT 4 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 4 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C01-T03（`RFWB-M002-C01-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M002-C01-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14837 PC=0x400880 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`5`，AllocationGeneration=`15`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `0` 清零；`M002_COMMIT` 记录 byte=0、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=5`,`gen=15` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14838 PC=0x400884 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=5`,`gen=15`；该指令共 1 条读事件；bytes16=0:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14839 PC=0x400884 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=5`,`gen=15`；该指令共 1 条读事件；bytes16=0:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`（错误版本未被输出消费）。

### M002-C02

#### C02-T01（`RFWB-M002-C02-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C02-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14800 PC=0x4008c4 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`45`，AllocationGeneration=`14`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `5` 清零；`M002_COMMIT` 记录 byte=5、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=45`,`gen=14` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14801 PC=0x4008c8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14802 PC=0x4008c8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：首差 `OUT 0 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C02-T02（`RFWB-M002-C02-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C02-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14887 PC=0x4008c4 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`5`，AllocationGeneration=`14`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `5` 清零；`M002_COMMIT` 记录 byte=5、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=5`,`gen=14` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14888 PC=0x4008c8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=5`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14889 PC=0x4008c8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=5`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：首差 `OUT 3 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 3 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C02-T03（`RFWB-M002-C02-T03-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C02-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=15011 PC=0x4008c4 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`0`，AllocationGeneration=`20`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `5` 清零；`M002_COMMIT` 记录 byte=5、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=0`,`gen=20` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=15012 PC=0x4008c8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=0`,`gen=20`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=15013 PC=0x4008c8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=0`,`gen=20`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
6. **实际消费者 3（OBSERVED）**：seq=15042 PC=0x401818 `str	q0, [sp, #96]`；source index=3；读取同版本 `phys=0`,`gen=20`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
7. **实际消费者 4（OBSERVED）**：seq=15043 PC=0x401818 `str	q0, [sp, #96]`；source index=3；读取同版本 `phys=0`,`gen=20`；该指令共 1 条读事件；bytes16=33:33:33:33:33:0:33:33:33:33:33:33:33:33:33:33。
8. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 7 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 7 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

### M002-C03

#### C03-T01（`RFWB-M002-C03-T01-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M002-C03-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14815 PC=0x400908 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`45`，AllocationGeneration=`14`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `0` 清零；`M002_COMMIT` 记录 byte=0、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=45`,`gen=14` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **同版本消费者**：`NOT_OBSERVED`。故障版本 `gen=14` 没有被实际读取；不得用同 PhysRegId 的其他代次替代。
5. **seq+1 重新定义 v0（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14816 PC=0x40090c `eor	v0.16b, v3.16b, v4.16b` 写新的 PhysRegId=`3`,`gen=12`。旧故障版本被重命名掉，该指令不是旧版本的消费者。
6. **同一物理槽位的新分配代次（OBSERVED）**：seq=14844 PC=0x40090c `eor	v0.16b, v3.16b, v4.16b` 把 `phys=45` 重新分配为 `gen=15`。这是新的分配代次，不是故障版本 `gen=14` 的消费者。
7. **新分配代次读取（OBSERVED）**：seq=14845 PC=0x400910 `str	q0, [x20], #16` 读取 `gen=15`；bytes16=11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11。该读取属于新代次，不能标记为 `gen=14` 的消费者。
8. **覆盖/Squash/Repair/Commit**：旧故障版本在 seq+1 被新版本取代，旧版本没有同版本消费者；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`（错误版本未被输出消费）。

#### C03-T02（`RFWB-M002-C03-T02-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M002-C03-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14854 PC=0x400908 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`3`，AllocationGeneration=`13`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `0` 清零；`M002_COMMIT` 记录 byte=0、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=3`,`gen=13` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **同版本消费者**：`NOT_OBSERVED`。故障版本 `gen=13` 没有被实际读取；不得用同 PhysRegId 的其他代次替代。
5. **seq+1 重新定义 v0（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14855 PC=0x40090c `eor	v0.16b, v3.16b, v4.16b` 写新的 PhysRegId=`0`,`gen=20`。旧故障版本被重命名掉，该指令不是旧版本的消费者。
6. **同一物理槽位的新分配代次（OBSERVED）**：seq=14873 PC=0x40090c `eor	v0.16b, v3.16b, v4.16b` 把 `phys=3` 重新分配为 `gen=14`。这是新的分配代次，不是故障版本 `gen=13` 的消费者。
7. **新分配代次读取（OBSERVED）**：seq=14874 PC=0x400910 `str	q0, [x20], #16` 读取 `gen=14`；bytes16=11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11。该读取属于新代次，不能标记为 `gen=13` 的消费者。
8. **覆盖/Squash/Repair/Commit**：旧故障版本在 seq+1 被新版本取代，旧版本没有同版本消费者；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`（错误版本未被输出消费）。

#### C03-T03（`RFWB-M002-C03-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M002-C03-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14886 PC=0x400908 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`2`，AllocationGeneration=`9`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `0` 清零；`M002_COMMIT` 记录 byte=0、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=2`,`gen=9` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **同版本消费者**：`NOT_OBSERVED`。故障版本 `gen=9` 没有被实际读取；不得用同 PhysRegId 的其他代次替代。
5. **seq+1 重新定义 v0（写回 OBSERVED，Rename 映射 INFERRED）**：seq=14887 PC=0x40090c `eor	v0.16b, v3.16b, v4.16b` 写新的 PhysRegId=`45`,`gen=17`。旧故障版本被重命名掉，该指令不是旧版本的消费者。
6. **同一物理槽位的新分配代次（OBSERVED）**：seq=15008 PC=0x40187c `ldp	q0, q1, [x4]` 把 `phys=2` 重新分配为 `gen=10`。这是新的分配代次，不是故障版本 `gen=9` 的消费者。
7. **新分配代次读取（OBSERVED）**：seq=15012 PC=0x401880 `stp	q0, q1, [x8]` 读取 `gen=10`；bytes16=80:fb:fe:ff:7f:0:0:0:c8:ff:ff:ff:80:ff:ff:ff。该读取属于新代次，不能标记为 `gen=9` 的消费者。
8. **覆盖/Squash/Repair/Commit**：旧故障版本在 seq+1 被新版本取代，旧版本没有同版本消费者；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`（错误版本未被输出消费）。

### M002-C04

#### C04-T01（`RFWB-M002-C04-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C04-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14893 PC=0x400950 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`45`，AllocationGeneration=`14`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `7` 清零；`M002_COMMIT` 记录 byte=7、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=45`,`gen=14` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14894 PC=0x400954 `eor	v3.16b, v0.16b, v4.16b`；source index=2；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:33:33:0:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14896 PC=0x40095c `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:33:33:0:33:33:33:33:33:33:33:33。
6. **实际消费者 3（OBSERVED）**：seq=14897 PC=0x40095c `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:33:33:33:33:0:33:33:33:33:33:33:33:33。
7. **二级消费者（INFERRED）**：按汇编，`EOR V3,V0,V4` 消费故障 v0；`ADDV B5,V3.16B` 再消费 V3。Trace 只对故障 v0 的读取记录 bytes16，ADDV 的源不是故障 PhysRegId，故其数值传播标 INFERRED。
8. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 0 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33` vs Control `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C04-T02（`RFWB-M002-C04-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C04-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14974 PC=0x400950 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`44`，AllocationGeneration=`19`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `7` 清零；`M002_COMMIT` 记录 byte=7、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=44`,`gen=19` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14975 PC=0x400954 `eor	v3.16b, v0.16b, v4.16b`；source index=2；读取同版本 `phys=44`,`gen=19`；该指令共 1 条读事件；bytes16=33:33:33:33:33:33:33:0:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14977 PC=0x40095c `str	q0, [x20], #16`；source index=3；读取同版本 `phys=44`,`gen=19`；该指令共 1 条读事件；bytes16=33:33:33:33:33:33:33:0:33:33:33:33:33:33:33:33。
6. **实际消费者 3（OBSERVED）**：seq=14978 PC=0x40095c `str	q0, [x20], #16`；source index=3；读取同版本 `phys=44`,`gen=19`；该指令共 1 条读事件；bytes16=33:33:33:33:33:33:33:0:33:33:33:33:33:33:33:33。
7. **二级消费者（INFERRED）**：按汇编，`EOR V3,V0,V4` 消费故障 v0；`ADDV B5,V3.16B` 再消费 V3。Trace 只对故障 v0 的读取记录 bytes16，ADDV 的源不是故障 PhysRegId，故其数值传播标 INFERRED。
8. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 4 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33` vs Control `OUT 4 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C04-T03（`RFWB-M002-C04-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M002-C04-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=15006 PC=0x400950 `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`5`，AllocationGeneration=`17`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `7` 清零；`M002_COMMIT` 记录 byte=7、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=5`,`gen=17` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **同版本消费者**：`NOT_OBSERVED`。故障版本 `gen=17` 没有被实际读取；不得用同 PhysRegId 的其他代次替代。
5. **二级消费者（INFERRED）**：按汇编，`EOR V3,V0,V4` 消费故障 v0；`ADDV B5,V3.16B` 再消费 V3。Trace 只对故障 v0 的读取记录 bytes16，ADDV 的源不是故障 PhysRegId，故其数值传播标 INFERRED。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`（错误版本未被输出消费）。

### M002-C05

#### C05-T01（`RFWB-M002-C05-T01-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C05-T01-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14887 PC=0x40099c `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`45`，AllocationGeneration=`14`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `3` 清零；`M002_COMMIT` 记录 byte=3、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=45`,`gen=14` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14888 PC=0x4009a0 `cmeq	v3.16b, v0.16b, v4.16b`；source index=2；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14892 PC=0x4009b0 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
6. **实际消费者 3（OBSERVED）**：seq=14893 PC=0x4009b0 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
7. **实际消费者 4（OBSERVED）**：seq=14901 PC=0x4009b8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
8. **实际消费者 5（OBSERVED）**：seq=14902 PC=0x4009b8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=45`,`gen=14`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
9. **控制消费者（INFERRED）**：按汇编，`CMEQ V3,V0,V4 → ADDV B5,V3 → UMOV W6,V5.B[0] → CBZ` 依次消费。Trace 只直接记录 CMEQ 对故障 v0 的读取和 STR Q0 的读取；ADDV/UMOV/CBZ 的数值传播标 INFERRED。
10. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
11. **软件结果（OBSERVED）**：首差 `OUT 0 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C05-T02（`RFWB-M002-C05-T02-F0`）

- 终态：`WRONG_ANSWER`；分类：`ACTIVATED_SDC`；证据文件：`traces/RFWB-M002-C05-T02-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=14980 PC=0x40099c `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`44`，AllocationGeneration=`19`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `3` 清零；`M002_COMMIT` 记录 byte=3、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=44`,`gen=19` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **实际消费者 1（OBSERVED）**：seq=14981 PC=0x4009a0 `cmeq	v3.16b, v0.16b, v4.16b`；source index=2；读取同版本 `phys=44`,`gen=19`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
5. **实际消费者 2（OBSERVED）**：seq=14985 PC=0x4009b8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=44`,`gen=19`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
6. **实际消费者 3（OBSERVED）**：seq=14986 PC=0x4009b8 `str	q0, [x20], #16`；source index=3；读取同版本 `phys=44`,`gen=19`；该指令共 1 条读事件；bytes16=33:33:33:0:33:33:33:33:33:33:33:33:33:33:33:33。
7. **控制消费者（INFERRED）**：按汇编，`CMEQ V3,V0,V4 → ADDV B5,V3 → UMOV W6,V5.B[0] → CBZ` 依次消费。Trace 只直接记录 CMEQ 对故障 v0 的读取和 STR Q0 的读取；ADDV/UMOV/CBZ 的数值传播标 INFERRED。
8. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
9. **软件结果（OBSERVED）**：首差 `OUT 4 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33` vs Control `OUT 4 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33`；分类 `ACTIVATED_SDC`。

#### C05-T03（`RFWB-M002-C05-T03-F0`）

- 终态：`MATCH_CONTROL`；分类：`ACTIVATED_MASKED`；证据文件：`traces/RFWB-M002-C05-T03-F0.csv`。

**传播链：**

1. **子单元/目标（OBSERVED）**：FP/SIMD VecReg writable destination；seq=15020 PC=0x40099c `eor	v0.16b, v1.16b, v2.16b`；PhysRegId=`5`，AllocationGeneration=`17`；`M002_VEC_ELIGIBLE` 记录寄存器字节数 value=256。
2. **故障操作（OBSERVED）**：shadow 写入代理在目标 instruction 执行时把 目标 byte `3` 清零；`M002_COMMIT` 记录 byte=3、已落库。
3. **错误值/状态（OBSERVED）**：故障版本 `phys=5`,`gen=17` 的目标 byte 为 0；其余 lane 保持 EOR 结果。正确/Control 同位置为 0x33（16 lanes 的 EOR 结果）。
4. **同版本消费者**：`NOT_OBSERVED`。故障版本 `gen=17` 没有被实际读取；不得用同 PhysRegId 的其他代次替代。
5. **控制消费者（INFERRED）**：按汇编，`CMEQ V3,V0,V4 → ADDV B5,V3 → UMOV W6,V5.B[0] → CBZ` 依次消费。Trace 只直接记录 CMEQ 对故障 v0 的读取和 STR Q0 的读取；ADDV/UMOV/CBZ 的数值传播标 INFERRED。
6. **覆盖/Squash/Repair/Commit**：上述消费发生在本版本生命周期内；后续循环迭代会重新分配该物理槽位，但不改变本链；无 squash、无 repair；消费者 Commit 未单独记录（NOT_OBSERVED）。
7. **软件结果（OBSERVED）**：OUT 与 Control 一致；分类 `ACTIVATED_MASKED`（错误版本未被输出消费）。

## 4. 每个 Context 内 T01/T02/T03 的差异

| Context | Timing | 注入/目标 Seq | PhysRegId | Gen | 原始值/错误值 | 消费者 | 首差 | 分类 |
|---|---|---:|---:|---:|---|---|---|---|
| C01 | T01 | 14771 | 45 | 14 | byte 0→0 | 2 | OUT 0 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C01 | T02 | 14813 | 2 | 7 | byte 0→0 | 2 | OUT 4 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C01 | T03 | 14837 | 5 | 15 | byte 0→0 | 2 | 一致 | ACTIVATED_MASKED |
| C02 | T01 | 14800 | 45 | 14 | byte 5→0 | 2 | OUT 0 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C02 | T02 | 14887 | 5 | 14 | byte 5→0 | 2 | OUT 3 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C02 | T03 | 15011 | 0 | 20 | byte 5→0 | 4 | OUT 7 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C03 | T01 | 14815 | 45 | 14 | byte 0→0 | 0 | 一致 | ACTIVATED_MASKED |
| C03 | T02 | 14854 | 3 | 13 | byte 0→0 | 0 | 一致 | ACTIVATED_MASKED |
| C03 | T03 | 14886 | 2 | 9 | byte 0→0 | 0 | 一致 | ACTIVATED_MASKED |
| C04 | T01 | 14893 | 45 | 14 | byte 7→0 | 3 | OUT 0 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C04 | T02 | 14974 | 44 | 19 | byte 7→0 | 3 | OUT 4 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C04 | T03 | 15006 | 5 | 17 | byte 7→0 | 0 | 一致 | ACTIVATED_MASKED |
| C05 | T01 | 14887 | 45 | 14 | byte 3→0 | 5 | OUT 0 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C05 | T02 | 14980 | 44 | 19 | byte 3→0 | 3 | OUT 4 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33 | ACTIVATED_SDC |
| C05 | T03 | 15020 | 5 | 17 | byte 3→0 | 0 | 一致 | ACTIVATED_MASKED |

### T01/T02/T03 差异

- **C01**：目标 Seq = 14771, 14813, 14837；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_MASKED；首差 = `OUT 0 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` / `OUT 4 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` / `一致`。
  - 同一 Context 内结果不同：不同 ordinal 对应不同目标 byte 位置/向量实例；byte 清零规则与写入代理相同，差异只来自被选动态实例。
- **C02**：目标 Seq = 14800, 14887, 15011；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_SDC；首差 = `OUT 0 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` / `OUT 3 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` / `OUT 7 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33`。
- **C03**：目标 Seq = 14815, 14854, 14886；分类 = ACTIVATED_MASKED, ACTIVATED_MASKED, ACTIVATED_MASKED；首差 = `一致` / `一致` / `一致`。
- **C04**：目标 Seq = 14893, 14974, 15006；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_MASKED；首差 = `OUT 0 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33` / `OUT 4 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33` / `一致`。
  - 同一 Context 内结果不同：不同 ordinal 对应不同目标 byte 位置/向量实例；byte 清零规则与写入代理相同，差异只来自被选动态实例。
- **C05**：目标 Seq = 14887, 14980, 15020；分类 = ACTIVATED_SDC, ACTIVATED_SDC, ACTIVATED_MASKED；首差 = `OUT 0 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33` / `OUT 4 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33` / `一致`。
  - 同一 Context 内结果不同：不同 ordinal 对应不同目标 byte 位置/向量实例；byte 清零规则与写入代理相同，差异只来自被选动态实例。

## 5. 五个 Context 之间的差异

### 五个 Context 之间的差异

| Context | 机制类 | 汇编序列 | 观察到的差异 |
|---|---|---|---|
| C01 | 基准激活 | `EOR V0.16B,V1,V2 → STR Q0` | 目标 byte 0 被清零后由 STR Q0 输出。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_MASKED |
| C02 | 激活/访问条件变化 | `EOR V0.16B,V1,V2 → STR Q0` | 输入位型与目标 byte 改为 byte 5；由 STR Q0 输出。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_SDC |
| C03 | 弱依赖/覆盖 | `EOR V0,V1,V2 → EOR V0,V3,V4 → STR Q0` | 同一 VecReg 槽位被新代次覆盖；消费者只读取新代次。 分类：ACTIVATED_MASKED/ACTIVATED_MASKED/ACTIVATED_MASKED |
| C04 | 扩展数据依赖 | `EOR V0,V1,V2 → EOR V3,V0,V4 → ADDV B5,V3.16B → STR Q0` | EOR V3 与 STR Q0 消费故障 v0；ADDV 消费 V3（数据流由汇编给出）。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_MASKED |
| C05 | 控制依赖/推测 | `EOR V0,V1,V2 → CMEQ V3,V0,V4 → ADDV B5,V3 → UMOV W6,V5.B[0] → CBZ → STR Q0` | CMEQ/ADDV/UMOV/CBZ 依赖故障 v0；实际输出为 STR Q0。 分类：ACTIVATED_SDC/ACTIVATED_SDC/ACTIVATED_MASKED |

## 6. 最终软件结果

### 最终软件结果（逐样本）

| SampleRunID | Context/Timing | 终态 | 分类 | 首差（Fault vs Control） |
|---|---|---|---|---|
| `RFWB-M002-C01-T01-F0` | C01/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` vs `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C01-T02-F0` | C01/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 4 00 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` vs `OUT 4 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C01-T03-F0` | C01/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M002-C02-T01-F0` | C02/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` vs `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C02-T02-F0` | C02/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 3 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` vs `OUT 3 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C02-T03-F0` | C02/T03 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 7 33 33 33 33 33 00 33 33 33 33 33 33 33 33 33 33` vs `OUT 7 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C03-T01-F0` | C03/T01 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M002-C03-T02-F0` | C03/T02 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M002-C03-T03-F0` | C03/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M002-C04-T01-F0` | C04/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33` vs `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C04-T02-F0` | C04/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 4 33 33 33 33 33 33 33 00 33 33 33 33 33 33 33 33` vs `OUT 4 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C04-T03-F0` | C04/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |
| `RFWB-M002-C05-T01-F0` | C05/T01 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 0 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33` vs `OUT 0 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C05-T02-F0` | C05/T02 | `WRONG_ANSWER` | `ACTIVATED_SDC` | `OUT 4 33 33 33 00 33 33 33 33 33 33 33 33 33 33 33 33` vs `OUT 4 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33 33` |
| `RFWB-M002-C05-T03-F0` | C05/T03 | `MATCH_CONTROL` | `ACTIVATED_MASKED` | OUT 一致 |

## 7. 诊断区分度总结

### 诊断区分度总结

M002 只改 **VecReg 目标 byte**：同版本读的 `bytes16` 保留完整 16 字节，目标 byte 为 0，其余 lane 正常。C03 的旧代次没有任何同版本读，随后同一物理槽位出现新代次 `gen+1`；新代次读取不能被当作旧代次消费者。C04/C05 分别展示 EOR→ADDV→Store 与 CMEQ→ADDV→UMOV→CBZ 的向量/控制依赖。

证据状态统一使用 `OBSERVED` / `INFERRED` / `NOT_OBSERVED`；不同 PhysRegId 或不同 AllocationGeneration 不合并，推断边不标记为直接观察。
