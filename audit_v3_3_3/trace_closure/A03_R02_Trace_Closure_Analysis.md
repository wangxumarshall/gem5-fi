# A03-R02 Trace Closure 根因分析

**Agent A · LSU v3.3.3 收口轮 · 只读分析**  
HEAD `78ac9ba730afb5bf9a5714568a8b8fa197cf0bbb`（分支 `lsu-v3.3.1-context-workload-20261111`）  
证据目录：`audit_v3_3_3/runs/A03-R02-fault/`

---

## 1. 结论摘要

**A03-R02 不能改判为 SQUASHED 终态；现有证据已足以完整闭合 SDC 因果链，且不需要新增运行时 Hook。**

- `event_ordinal=1094 / dyn_inst_seq=13718`（首个 `affected=1` 的 A03_STREAM 行）确实被 squash；但 squash 边界是 `triggering_seq=13717`（不是故障指令本身），冻结规则判为 `squash_cause=unrelated;fault_caused=0`。该条 13718 链在 writeback 前即被截断（整条链只有 7 个节点，无 `resp`/`taint_reg`/`commit`）。
- 但 A03 是**持续性** stuck-at bit3（`A03_STUCK_LIFECYCLE`：`eligible_events=51303;applications=51222;already_stuck=81`），故障在后续动态实例上继续生效。**第一台真正把错误数据提交进架构态的是 `dyn_inst_seq=13772`（pc=400678，ordinal=1099）**，prop_trace 的唯一 `errant_commit` 节点即指向它（`trigger=faulting_load_commit;pc=400678;commit_seq=6495`）。
- 13772 读出的错误字节 `0xab` 经消费者 `13774`（pc=40067c）XOR 进校验和累加器，最终应用打印 `d48b947fc08d5a75`（golden `728e604ffcec539d`）。用工作负载源码 + 本 run 的 6 个被污染字节与第 11 步 32 个奇地址重复块做离线重算，**精确复现 `d48b947fc08d5a75`**（见 §6），因此 SDC 终态是实证的，而非推断。
- 当前 `tools/lsu_v333_qualified.py` 报 `QUALIFIED`（缺 `load_result`/`register_writeback`/`consumer`）是**解析层锚点问题**：它把因果链锚定在"首个 affected 行 13718"，而 13718 是错误路径上的投机实例、没有响应/WB/消费者。运行时不缺数据（trace 中 13772 的 `resp→taint_reg→consumer→commit→errant_commit` 全在），因此**无需新增 C++ Hook**；最小修复是在解析层把锚点改到 `errant_commit`（或"首个带 resp→taint→consumer 的 affected seq"）。

---

## 2. 冻结输入与证据清单

二进制/配置哈希（本次实测复核，与冻结事实一致）：

| 文件 | SHA256 |
|---|---|
| `build/ARM/gem5.opt` | `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338` |
| `configs/se/lsu_proxy.py` | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` |

证据文件（`audit_v3_3_3/runs/A03-R02-fault/`）：

| 文件 | 大小 | SHA256 |
|---|---|---|
| `summary.json` | 3478 B | `421be9191bab6c18607e2102f6ae9c1685994778f33fa4c58fff8903a3971351` |
| `pilot_meta.json` | 2088 B | `db6230247e2c1ab8a25774c5a93c382eefafdbe12e14a6d0cdf635b45759d71f` |
| `manifest.json` | 1849 B | `50e1bf6e26b5fb81ce357cb6c92572705b74cc9d05806e6afdc46d5452e4dde2` |
| `prop_trace.csv.gz` | 20,069,090 B | `6980ba41f81fed3b6f3d63796a68a2952b37e0e45f5d950d5954f7eac6c625f1` |
| `stats.txt` | 256,600 B | `c9d94e5075ce7ec2516285415cf30ccc9258d323a8e7b341674b1f503bf71d25` |
| `addrpath_injections.log` | 13,250,847 B | `f6c92120fc4ec210255eeeaf31902293cc9cbd27f0655f855e28e5ff9fecd727` |
| `stdout.log` | 1937 B | `c427da440e5594f011000f572d401b455e10623254b74eb6fc71ffaf66a798ec` |
| `stderr.log` | 1954 B | `024006003e5bbb74e6cbe9b5ae42a2e1d66a70068c4f771e9f230649df1c3059` |
| `oracle.log` | 59 B | `c71450f2130ea4c337ff2fcdd6b39cf1c4806fb89caf9b8e712bbe762212a7d0` |
| `campaign_manifest.json` | 1482 B | `08f40288e54fe7c241bd64dee5a4bd1fb4898440f916ef46e536aaef85ad5951` |

工作负载：`docs/gem5-fi/lsu/implementation_v3_2/workloads/agu_addrmodes`
（`manifest.json` 记录 `workload_sha256=90a1900377d2499625bf401c6b8ce1a7d4a22c8327aeef98f11dc842b406b49b`）。

`prop_trace.csv.gz` 完整性：header `# lsu-propagation v1: ...`，**672,494 数据行**，首 tick `79310`，末 tick `401170385`；`_scan_prop_trace` 判定 `trace_complete=true`、`rows_scanned=672494`（说明 gzip 流完整读到尾部）。记录种类计数：

```
sq_lifecycle 105285 · lq_lifecycle 105263 · prop_edge 51547 · funnel 51304
a03_stream 51303 · mem_req 51222 · inj 51222 · addr_form 51222 · taint_reg 51212
resp 51212 · commit 51211 · consumer 335 · inj_nochange 81
taint_value_mismatch 56 · squash 10 · fwd 7 · errant_commit 1 · a03_activation 1
```

`a03_stream` 51303 = `affected=1` 51222 + `affected=0`(ALREADY_STUCK) 81，与 lifecycle 的 `applications=51222;already_stuck=81` 完全一致。

---

## 3. 故障激活与 First Affected Instruction

### 3.1 激活（真实记录）

`addrpath_injections.log:1`：

```
A03_ACTIVATION: tick=16170385;bit=3;mode=a03_bit3_stuck0_load
```

prop_trace 另有同一事件的节点 `5336,16170385,1,a03_activation,...,tick=16170385;bit=3;mode=a03_bit3_stuck0_load`。

### 3.2 lifecycle（真实记录）

`addrpath_injections.log:122611`（= `summary.a03.lifecycle`）：

```
A03_STUCK_LIFECYCLE: fault_id=1;bit=3;mode=a03_bit3_stuck0_load;eligible_events=51303;applications=51222;already_stuck=81;activation_ordinal=1094;activation_dyn_inst_seq=13718;activation_pc=40068c;activation_golden_ea=493ff8;first_affected_ordinal=1094;first_affected_dyn_inst_seq=13718;first_affected_pc=40068c
```

即：持久 stuck-at-0（`addr & ~0x8`，bit3），激活发生在第 1094 个 eligible 事件、`dyn_inst_seq=13718`、`pc=0x40068c`、golden EA `0x493ff8`。

### 3.3 目标行与 13718 的完整轨迹

`summary.json` 的 `a03.first_affected`：

```
A03_STREAM: event_ordinal=1094;dyn_inst_seq=13718;pc=40068c;eligible=1;affected=1;golden_ea=493ff8;actual_ea=493ff0;bit=3;reason=STUCK_APPLIED
```

在 `prop_trace.csv.gz` 中 `dyn_inst_seq=13718` **只有 7 行**（无 `resp`、无 `taint_reg`、无 `commit`）：

```
5332,16169615,0,lq_lifecycle,13718,...,queue=LQ;action=alloc;index=802;generation=1308;reason=insert
5334,16170385,1,inj,13718,,493ff8,...,site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;new_size=8;old_addr=493ff8;new_addr=493ff0
5335,16170385,1,addr_form,13718,,493ff0,...,site=lsq_pushRequest_PRE;old_addr=493ff8;new_addr=493ff0
5337,16170385,1,a03_stream,13718,,493ff0,...,event_ordinal=1094;...;golden_ea=493ff8;actual_ea=493ff0;bit=3;reason=STUCK_APPLIED
5338,16170385,1,mem_req,13718,74,493ff0,...,site=lsq_sendFragmentToTranslation;family=addrpath;size=8;request_id=74;fragment_id=2197;lq_entry_id=802
5339,16170770,0,squash,13718,...,record=squash_reason;dyn_inst_seq=13718;reason=lsq_squash;triggering_seq=13717;...;squash_cause=unrelated;fault_caused=0;...;execution_attempt_id=1;replay_generation=0
5340,16170770,0,lq_lifecycle,13718,...,queue=LQ;action=free;index=802;generation=1308;reason=squash
```

**结论：13718 在发出 `mem_req`（tick 16170385）后、任何响应返回前（tick 16170770）即被 squash；它没有任何架构层结果。** 模型层面的 "first affected" 是第一个触发 F5 的 eligible 事件（含投机执行），不是第一台到达架构态的受影响指令。

---

## 4. Squash 事件与原因（event_id / parent 链）

目标 squash 节点 `node_id=5339`，tick `16170770`：

```
record=squash_reason;dyn_inst_seq=13718;reason=lsq_squash;
triggering_seq=13717;triggering_seq_recorded=1;fault_tracked=1;
squash_cause=unrelated;fault_caused=0;pc=40068c;
execution_attempt_id=1;replay_generation=0;lq_entry_id=802;sq_entry_id=-1
```

- `reason=lsq_squash` 对应 `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1245-1256` 的 `LSQUnit::squash(squashed_num)` 钩子；`triggering_seq` 即 `squashed_num`，语义是"比它更年轻的 LSQ 项被清除"。
- 判定器在 `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/fw02_rules.hh:106-119` `chaos_fw02::classifySquash(dyn_inst_seq, triggering_seq, fault_seq)`：`FaultCaused` 要求 `triggering_seq == fault_seq`。此处 `fault_seq=13718`（该指令在 `fault_seqs` 中），而 `triggering_seq=13717`，故返回 `Unrelated`。记录写入点 `CHAOSPropagation::noteSquash`（`CHAOSPropagation.cc:2382-2420`）。
- 全 run 共 **10 条 `squash` 记录**，全部 `pc=40068c`、全部 `triggering_seq = dyn_inst_seq - 1`、全部 `squash_cause=unrelated;fault_caused=0`：

```
5339  13718  triggering_seq=13717
5352  13738  triggering_seq=13737
5365  13758  triggering_seq=13757
5380  13778  triggering_seq=13777
5394  13802  triggering_seq=13801
5408  13826  triggering_seq=13825
5438  13850  triggering_seq=13849
5469  13874  triggering_seq=13873
5491  13898  triggering_seq=13897
5516  13922  triggering_seq=13921
```

- 这些是同一静态 load `pc=40068c` 的**投机执行实例**：在 `0x400678` 的 16 次字节循环中，循环回边 `0x400688 b.ne` 多次预测"退出"，把 `0x40068c` 取入；回边实际 taken 后，`0x40068c` 被 squash。eligible 事件流因此按奇偶交替：40068c（偶 ordinal，投机）↔ 400678（奇 ordinal，实际迭代），与 §5 的记录一致。
- 同 run 的 `stats.txt`：`lsq0.squashedLoads=541`、`bac.branchMisspredict=537`、`commitStats0.numLoadInsts=52090`、`simTicks/finalTick=401170385`。
- 注意：prop_trace 只记录与故障相关的指令，**不记录 13717 的 pc/指令类型**。因此"13717 是 0x400688 的循环分支"是由控制流与严格 `seq-1` 模式给出的**强一致推断**，而非 trace 直接记录的字段；trace 直接证明的只有"边界 13717 不是故障指令 13718"。

---

## 5. 传播是否被截断 / 是否有其他进入架构态的链

### 5.1 13718 这一条链被截断

13718 的 7 行中没有 `resp`/`taint_reg`/`prop_edge`/`commit`，因此 **ptag=1 链在 writeback 前终止**。若只看 13718，确实是"被 squash 截断"。

### 5.2 但故障本身未被截断：13772 首次进入架构态

持续故障在后续动态实例继续施加。`ptag` 按"实际改变 EA 的注入链"递增（`ptag=1` 对应 13718，`ptag=4` 对应 13772；`ALREADY_STUCK` 行为 `ptag=0`）。13772 的完整传播链（`inj→addr_form→a03_stream→mem_req→resp→taint_reg→prop_edge→commit→errant_commit→consumer`）：

```
5371,16201570,4,inj,13772,,493019,...,site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=1;new_size=1;old_addr=493019;new_addr=493011
5373,16201570,4,a03_stream,13772,,493011,...,event_ordinal=1099;dyn_inst_seq=13772;pc=400678;eligible=1;affected=1;golden_ea=493019;actual_ea=493011;bit=3;reason=STUCK_APPLIED
5374,16201570,4,mem_req,13772,70,493011,...,request_id=70;fragment_id=2202;lq_entry_id=804
5410,16214660,4,resp,13772,70,78011,...,data_len=1;data_fnv=af64264c86026a4a;data_hex=ab;...;pa=78011
5411,16214660,4,taint_reg,13772,70,,53,1,...,arch_reg=1;phys_reg=53;writeback_value=ab;writeback_value_fnv=5da39ae7a43fa14e;...
5419,16215430,0,commit,13772,...,trigger=fault_instruction_commit;tracked=fault;pc=400678;commit_seq=6495;...;is_load=1
5420,16215430,4,errant_commit,13772,...,trigger=faulting_load_commit;pc=400678;commit_seq=6495
5422,16215815,0,lq_lifecycle,13772,...,queue=LQ;action=free;index=804;generation=1313;reason=commit
```

`errant_commit` 在实现上是"整 run 一次"的传播视图锚点（`CHAOSPropagation.cc:2711-2726`），本 run 唯一一条即 13772，`trigger=faulting_load_commit`（表示是该 load 自身提交其带污点的目的寄存器，而不是消费者）。

### 5.3 静态目标 PC 0x40068c 本身也有一个架构实例（但值未变）

11 个 `pc=40068c` 的 a03_stream 实例中，10 个被 squash，**第 11 个 `dyn_inst_seq=13946`（ordinal=1114）提交**：

```
5537,16237375,17,inj,13946,,493ff8,...,old_addr=493ff8;new_addr=493ff0
5543,16238145,17,resp,13946,70,78ff0,...,data_hex=0000000000000000;...;pa=78ff0
5544,16238145,17,taint_reg,13946,70,,52,2,...,arch_reg=2;phys_reg=52;writeback_value=0;...
5562,16239685,0,commit,13946,...,trigger=fault_instruction_commit;tracked=fault;pc=40068c;commit_seq=6543
```

`array` 在 `0x493000`（512 B），`output` 在 `0x493200`（512 B，`readelf -s`），`0x493ff0/0x493ff8` 均落在 BSS 零页，因此 13946 **地址被改但读到的值仍为 0**（与 golden 一致）——这是"地址 affected、数据未 affected"的情形，不贡献 SDC。

### 5.4 持续性证据

- `A03_STREAM` 最后一条（tick 401169230）：`event_ordinal=52396;dyn_inst_seq=169935;pc=401a04;...;golden_ea=493c88;actual_ea=493c80`，说明注入一直持续到 watchdog（tick 401170385）。
- 51303 次 fired eligible 中 51222 次实际改地址，51211 条 `commit`（fault-tracked load 的提交记录）、335 条 `consumer`、56 条 `taint_value_mismatch`（phys-reg 回收导致的陈旧污点诊断，被正确排除为边）。
- 因此：**存在其他 First Affected Instruction 进入架构态并成为真正传播起点——13772（ordinal 1099）**；13718（ordinal 1094）不是。

---

## 6. 应用层 SDC 的实际因果链（可追溯且已数值验证）

### 6.1 负载映射（`objdump` + 源码）

`docs/.../workloads/agu_addrmodes.c` 的 FNV-1a 校验和，编译后：

```
400678: ldrb w1,[x2],#3        ; 第 9 步：非对齐字节循环，(offset 1,4,7,...,46)
40067c: eor  x0,x1,x0
400680: mul  x0,x0,x3          ; x3 = FNV prime 0x100000001b3
400688: b.ne 400678
40068c: ldr  x2,[x4,#4088]     ; 第 10 步：页边界 *(base+4096-8) = 0x493ff8
400698: eor  x0,x0,x2
4006a8: ldr  q0,[x4,x2]        ; 第 9/10 步的 NEON 搬运（output[i]=array[i]^const）
4006b0: str  q0,[x2,x1]
4006d0: ldr  x2,[x1],#8        ; 第 11 步：对 output[] 的 64×8B 校验和循环
4006d4: eor  x0,x0,x2
4006d8: mul  x0,x0,x4
...
4006f4..40071c: x0 的 16 进制转换
400720: mov x2,#16 ; 400728: bl __libc_write   ; write(1, buf, 16)
```

### 6.2 进入最终 checksum 的具体污染集合

第 9 步（pc=400678）在激活（ordinal 1094）之后还剩 10 次迭代（offset 19..46）；其中 6 次 bit3=1 被实际改址：

| dyn_inst_seq | ordinal | golden_ea | actual_ea | 实际读到 |
|---|---|---|---|---|
| 13772 | 1099 | 493019 (offset 25) | 493011 (offset 17) | `ab` |
| 13796 | 1101 | 49301c (28) | 493014 (20) | `cf` |
| 13820 | 1103 | 49301f (31) | 493017 (23) | `02` |
| 13892 | 1109 | 493028 (40) | 493020 (32) | `bc` |
| 13916 | 1111 | 49302b (43) | 493023 (35) | `26` |
| 13940 | 1113 | 49302e (46) | 493026 (38) | `8d` |

（13732/13752/13844/13868 为 `ALREADY_STUCK`，地址未变，仍读 golden。）

第 10 步（pc=40068c）读 BSS 零页，改址后仍为 0（§5.3），不贡献差异。  
第 9/10 步的 NEON 搬运 load（pc=4006a8，33 条）**全部 `ALREADY_STUCK`**（地址 16B 对齐，bit3 恒 0），因此 `output[]` 由 golden `array[]` 正确构造。  
第 11 步（pc=4006d0，64 次迭代）地址从 `0x493200` 起每 8B 递增：**偶数迭代 bit3=0（ALREADY_STUCK，正确），奇数迭代 bit3=1 被清零 → 读到前一个 8B 块**，即 `output[i-1]` 覆盖 `output[i]`（32 个污染块）。

### 6.3 精确复现（离线重算，只读，未运行 gem5）

用工作负载源码逐项实现 FNV-1a（`array[i]=0x1000+i*0x0123456789ABCDEF`，步 1–11 全部照抄）：

```
golden 重算            = 728e604ffcec539d   （与 oracle expected 完全一致）
若只污染 13772 单字节   = 2aadb1ebcf5988df   （≠ 观测值）
代入上述 6 个实测字节 +
第 11 步奇数块重复      = d48b947fc08d5a75   （= oracle.log got，精确一致）
```

因此 SDC 的最终因果链是**多指令复合**：13772 是**第一台**把错误值提交进架构态的受影响指令（errant_commit），后续 13796/13820/13892/13916/13940 以及第 11 步的 32 个奇块继续叠加，最终得到 `d48b947fc08d5a75`。

### 6.4 消费者链（prop_trace 原文节选）

```
5423,16215815,4,consumer,13774,...,orig=phys 53/arch x1; pc=40067c;
     source_event_id=5411; consumer_input_value=ab;
     consumer_output_value=9f278f06cc7314a9; dest_phys_reg=72; dest_arch_reg=0; commit_seq=6497
5429,16216970,4,consumer,13775,...,pc=400680; source_event_id=5423;
     consumer_input_value=9f278f06cc7314a9; consumer_output_value=e34cb18d678c1b2b;
     dest_phys_reg=51; dest_arch_reg=0; commit_seq=6498
5440,16217740,4,consumer,13798,...,pc=40067c; source_event_id=5429; ...
5442,16217740,6,consumer,13798,...,pc=40067c; source_event_id=5414; ...  (ptag 4 与 ptag 6 在 13798 汇合)
...
最后一条 consumer: 15818, pc=4019f8, commit_seq=7484
```

即 13772 的 `x1=0xab` 在 `13774:40067c eor` 进入累加器 `x0`，`13775:400680 mul` 继续，此后 `x0` 一直携带错误值直到 `0x4006f4..0x40071c` 的十六进制转换与 `0x400728` 的 `write(1,buf,16)`。

---

## 7. 是否需要新增只读 Hook

### 7.1 判定

- **不需要把 A03-R02 改判为 SQUASHED**：squash 只截断了 13718 等 10 个投机实例（ptag=1 等链），没有截断故障语义；13772 之后的错误值明确进入架构态并造成 `d48b947fc08d5a75`。改判 SQUASHED 会与 §6 的实证结果矛盾。
- **也不需要新增 C++ 运行时 Hook**：现有 prop_trace 已包含完整证据（`resp`/`taint_reg`/`prop_edge`/`consumer`/`commit`/`errant_commit`/`squash`），足够闭合 13772 的链。
- `QUALIFIED` 的直接原因在解析层：`tools/lsu_v333_qualified.py` 的 `_a03()` 以 `first_downstream_instruction_affected`（13718）的 `dyn_inst_seq` 作为 `target_seq` 调用 `_scan_prop_trace()`（第 341 行），而 13718 在 trace 中没有 `resp`/`taint_reg`，于是三个字段均为 `None`（`missing=[load_result, register_writeback, consumer]`）。注意 `consumer` 的兜底分支（第 362 行）在 `if edge is not None`（第 356 行）内部，而 `edge` 又要求 `taint is not None`（第 349 行起），所以兜底不会触发。

### 7.2 最小修复清单（解析层；无执行语义/二进制变化）

| 项 | 内容 |
|---|---|
| 文件/函数 | `tools/lsu_v333_qualified.py` → `_a03()`（约 284–430 行） |
| 锚点 | 当首个 `affected=1` 的 seq 在 trace 中无 `resp`/`taint_reg` 时，改用 **`errant_commit` 节点的 `dyn_inst_seq`**（本 run = 13772）作为因果链锚点；或扫描 `a03_stream` 中最早一个同时具备 `resp→taint_reg→consumer` 的 affected seq |
| 需记录字段 | 无需新增；沿用 `errant_commit.dyn_inst_seq`（现文件已有）+ 13772 的 `resp.data_hex/data_fnv`、`taint_reg.arch_reg/phys_reg/writeback_value_fnv`、`consumer.pc/commit_seq` |
| 同时保留 | 仍把 13718 的 `A03_STREAM` 与其 `squash` 记录作为"首个 affected 被非故障 squash"的 provenance 输出，避免丢失原始锚点 |
| Behavior Impact | 无（分析工具；不改变仿真） |
| Binary Impact | 无（不触碰 `CHAOS/gem5/src/**`，不需要重编译） |
| Validation | 对 `audit_v3_3_3/runs/A03-R02-fault` 重跑 `qualified_evidence("A03", run_dir)`，确认 `load_result/register_writeback/consumer` 三个字段出现且 `status` 不再因这三项为 `QUALIFIED`；再用 §6.3 的重算脚本核验 checksum 链（golden 与 fault 两个值都精确匹配） |

### 7.3 如果必须补运行时 Hook（不推荐，非必需）

现有 `errant_commit` 节点（`CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:2711-2726`）已经精确承担"第一个进入架构态的故障路径提交"的语义；`noteSquash`（同文件 2382–2420）已经记录 squash 边界。两者组合已覆盖所需观测点。**若组织上仍要求新增节点，最小方案是在 `noteCommit` 的 `fault_tracked` 分支中为"首个 affected seq 与首个 errant_commit seq 不同"的情形写一条只读 `first_affected_outcome` 记录**（字段：`first_affected_seq`、`outcome=squashed|committed`、`errant_commit_seq`、`squash_boundary`），但它不改变执行语义，也不应改变故障数据路径。结论：**这不是本 run 的必要条件**。

---

## 8. 残余不确定性

1. **squash 起因的指令身份**：trace 未记录 `triggering_seq=13717` 的 pc/类型；"0x400688 循环分支误预测"是由反汇编控制流 + 严格 `seq-1` 边界模式给出的强一致推断。trace 直接证明的只有"边界不是故障指令 13718，故 `squash_cause=unrelated`"。
2. **对 POST_ORACLE_SIM_HANG 的归因**：`stdout.log` 已打印 `d48b947fc08d5a75`，随后 `stderr.log` 显示 `NotImplementedError: Exit event 'CHAOS_A03_WATCHDOG_EXPIRED' not implemented`，watchdog tick=401170385。trace 末段 51169 个 affected load 位于 `pc=401a04`（`__lll_lock_wait_private` 的 `ldaxr w0,[x4]`，golden `0x493c88` → actual `0x493c80`）。hang 与"原子锁 load 地址被清 bit3"高度相关，但仅凭 trace 无法证明因果（也可能程序本就等待）。**该不确定性不影响 SDC 判定**：checksum 在 hang 之前已经写出。
3. **各污染源的相对贡献**：离线重算证明"6 个字节 + 32 个奇块"这组污染足以精确复现 `d48b947fc08d5a75`，也证明 13772 单字节不足以复现（得到 `2aadb1ebcf5988df`）。但若存在其他等价的污染组合也能得到同一 checksum，仅凭单次 run 无法排除；本报告的结论是"这组实际观测到的污染即可解释终态"，不是"唯一可能解释"。
4. **`taint_value_mismatch` 56 条**：为 phys-reg 回收/陈旧污点的诊断记录（按 `CHAOSPropagation` 规则不构成边），已在本链分析中排除；不影响 13772→13774→…→checksum 的主链。
