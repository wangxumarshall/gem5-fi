# FR03 永久物理 cell：generation 语义裁决与实现

> 适用：`FSU-FR03-F5-W3 / W5 / W6`（固定 Vec phys reg / lane / bit，SA0/SA1）。
> 实现位置：`CHAOS/gem5/src/cpu/o3/regfile.hh`、
> `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/`、
> `CHAOS/gem5/src/cpu/o3/free_list.hh`、`chaos_vec_stuck.hh`。
> 状态：**语义裁决 + host/C++ 单测完成；L0–L5（含真实 commit/squash 钩子、
> 首影响、读写分离计数）已实现；真实 gem5 gate 与正式 seed 尚未运行。
> FR03-F5 仍为 PARTIAL（不可认证）**。本文不把 FR03 标为 COMPLETE。

## 1. 工作簿原文依据

以下原文直接摘自仓库内工作簿导出文件（未改写）：

**表 3（位置 × 模型矩阵）FR03 行**
`docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控-03-位置x模型矩阵.md:31`：

> | FR03 | FP/SIMD PRF | 固定Vec phys reg/lane/bit | 永久缺陷跨物理槽复用和多次读写暴露 | 卡死 | warm-up后选定phys reg、lane、bit和SA0/SA1，每次写入/读出维持极性；正确值相同时不计activation | ...
> | ... | 固定cell被分配且正确写值与卡死极性不同 | L0 run/sample/fault/event/parent/tick/sn/class/phys/arch/generation/lane/bit/mask/old-new；L1 alloc/free/reuse/ready/write version；... 模型重点：arm tick、phys generation、每次correct/stored、exposure/applied、首影响 | ... | 明确每次重分配的generation、写入应用和读暴露链 |

**表 7/9（展开执行矩阵 / 逐 RunID 传播监控）FR03 行**
`docs/gem5-fi/fsu/gem5-fi-FSU单元故障注入方案_逐RunID传播监控-07-展开执行矩阵.md:81-83`
与 `...-09-逐RunID传播监控.md:73-75`：

> | FSU-FR03-F5-W3 | FR03 | FP/SIMD PRF | 固定Vec phys reg/lane/bit | 卡死 | ... | 固定cell被分配且正确写值与卡死极性不同 | L0 CHAOSPhysReg或读写端口故障 → L1 Vec PRF cell/generation/ready与RAT映射 → L2 FP/SIMD consumer operand read/旁路/lane merge → L3 FSU execute/result → L4 dest Vec PRF writeback、wakeup与consumer扇出 → L5 ROB commit/squash、架构V/FPSR与oracle；本模型重点：arm tick、phys generation、每次correct/stored、exposure/applied、首影响 |
> ...
> | ... | 明确每次重分配的generation、写入应用和读暴露链 | run_id + sample_run_id + fault_id/ptag；event_id + parent_event_id；tick/cycle + core_id + thread_id；dyn_inst_seq + commit_seq + PC/opcode；arch_reg + reg_class + phys_reg + reg_generation；IQ slot/src_slot + producer_seq/consumer_seq；opClass + FU_class/FU_index。禁止只按tick、PC或寄存器索引单键连接。 | 完整链必须存在L0 fault_applied，每条边由fault_id/ptag、event_id/parent_event_id和dyn_seq/producer-consumer可达性共同证明，并终止于... |

## 2. 裁决

1. **永久故障 key = `reg_class` + `phys_index` + lane/bit/mask + polarity。**
   `generation` **不是** key，也**不是**故障清除条件。它只标识分配世代 /
   exposure 身份，用于把“每次重分配的 generation、写入应用和读暴露链”
   写清楚。
2. **free / realloc / squash 后同一物理 cell 仍卡死。**
   `UnifiedFreeList::addReg()` 递增 generation 只是开启一个新的 exposure
   身份；下一次写入同一物理 cell 仍然强制同一 lane/bit/mask/polarity。
3. **旧 generation 的 producer/consumer 链不得连到新 generation。**
   新 generation 的 exposure 链从 `generation_change` 生命周期事件重新
   开始，`exposure_id` 从 1 重新计数；旧 generation 的
   producer/consumer 事件不会被新的数据链继承。
4. **其他 cell / reg class / lane / bit 不泄漏。**
   匹配只按 class + phys_index；应用只改目标 lane 的 mask 位。
5. **只有运行结束或显式 reset 才清除。**
   squash 没有任何清除路径；`PhysRegFile::clearPermanentFaults()` 只在
   FR03 terminal / reset 调用。

与旧实现的冲突：旧 `regfile.hh::isVecStuckTarget` 要求
`generationOf(p) == vec_stuck.generation`，而 free 时 generation++，
于是故障在重分配后“消失”。这与表 3 FR03 的
“永久缺陷跨物理槽复用”直接冲突，已删除 generation 匹配条件。

## 3. generation 的数值来源与递增点

| 项 | 事实 | 位置 |
|---|---|---|
| 初值 | 所有 flat slot 从 0 开始 | `CHAOS/gem5/src/cpu/o3/regfile.cc:88`（`flat_generation.assign(totalNumRegs, 0)`） |
| 递增 | 物理槽被释放、重新加入 free list 时 `noteRegFreed()` 对 `flatIndex()` 做 `++` | `CHAOS/gem5/src/cpu/o3/free_list.hh` `UnifiedFreeList::addReg()`；`CHAOS/gem5/src/cpu/o3/regfile.hh` `noteRegFreed()` |
| 读取 | `generationOf(PhysRegIdPtr)` 按 `PhysRegId::flatIndex()` 取当前世代 | `regfile.hh` |
| 匹配 | **不参与**。`chaos_vec_stuck::Target::matches(cls, idx)` 只比较 class + index | `chaos_vec_stuck.hh` |
| 观测 | CHAOSPhysReg 在安装时记录 `observed_generation`；首次看到变化时发 `generation_change`（old/new），并把 `exposure_id` 归零 | `CHAOSPhysReg.cc::observeVecGeneration()` |
| 清除 | 仅 `clearPermanentFaults()`（运行结束 terminal / 显式 reset） | `regfile.hh` |

注意：`initFreeList` 的初始批量 `addRegs → addReg` 也会调用
`noteRegFreed`，所以实际世代值可能从 1 起；它是身份编号，不是“第几次
分配”的语义断言。文档与事件按“递增/变化”解释，不假设从 0 起。

## 4. 实现位置

| 文件 | 变化 |
|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/chaos_vec_stuck.hh` | 永久 key 改为 class+index；`Target::matches()`；新增 `GenerationLedger`（镜像 flat_generation）、`PermanentCell`（每次写入强制、generation 变化时 exposure_id 链重启、读写分开计数、其他 class/index/lane/bit 不变、squash 无清除接口、`clear()` 才清除）与 `L5Ledger`（纯 L5 commit/squash 状态机、诚实 terminal）。 |
| `CHAOS/gem5/src/cpu/o3/regfile.hh` | `isVecStuckTarget()` 去掉 generation 比较；新增 `vec_stuck_reads`（容器读路径计数）、`readVecRegRaw()`（注入器快照不计读）、`clearPermanentFaults()`、`vecStuckActive()/getVecStuckReads()`；更新 FR03 合同注释。 |
| `CHAOS/gem5/src/cpu/o3/free_list.hh` | 注释改为“generation 只是身份，故障跨复用存活”；行为不变（仍 `noteRegFreed`）。 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh/.cc/.py` | 安装/写入/读/执行/写回/generation change/L5 commit/L5 squash/terminal 的 FSU_PROP 发射；安装后同一 physical cell 在任意 generation 重施加；`armVecStuck` 记录安装世代仅作 provenance；`noteCommit`/`noteSquash` 真实 L5 钩子；`requireAllocated` 真实 target 策略；运行结束诚实 `chain_end` + 清除。 |
| `CHAOS/gem5/src/cpu/o3/commit.cc` | 紧邻 `chaosFPU->noteCommit` 新增只读 `chaosPhysReg->noteCommit(tid, head_inst.get())`（真实 commit 之后）。 |
| `CHAOS/gem5/src/cpu/o3/rob.cc` | 在真实 `ROB::doSquash` 循环内新增只读 `chaosPhysReg->noteSquash(tid, (*squashIt[tid]).get())`；不改变控制流。 |
| `configs/se/ooo_proxy.py` / `configs/se/arm_chaos.py` | 新增 `--phys_require_allocated` 并传给 `CHAOSPhysReg.requireAllocated`（默认 false，兼容旧 campaign）。 |

## 5. CHAOSPhysReg FSU_PROP 事件路径（L0–L5）

发射函数 `emitFsuProp()` 复用
`CHAOSPropagation::notePropEvt()`；`fault_id` 对整次运行固定一个。
事件 kind、层级和完成情况：

| 工作簿层 | 期望 | 实现 kind | 状态 |
|---|---|---|---|
| L0 | 安装、fault/event/parent/tick/sn/class/phys/arch/generation/lane/bit/mask/old-new | `fault_installed`（根；安装写同时是 exposure #1） | 已实现（真实 install 路径） |
| L1 | cell/generation/ready/RAT 映射、alloc/free/reuse/write version | `carrier_state`（安装载体、读计数 delta）、`generation_change`（old/new、free/alloc 状态） | 部分实现：free 由 generation 递增处推得；无独立 RAT/ready 时钟 |
| L2 | consumer operand read / 旁路 / lane merge | `operand_read`（execute 后扫描真实 source Vec phys reg） | 已实现（execute 钩子内的真实 operand 观察；无旁路/merge 细分） |
| L3 | FSU execute/result | `execute` | 已实现（与写入同指令） |
| L4 | dest Vec PRF writeback、wakeup、fanout | `phys_write` + `prf_writeback` + 首次/首次激活的 `stuck_reapplied` | 部分实现：writeback 已实现；wakeup/fanout 无独立钩子 |
| L5 | ROB commit / squash / 架构 V/FPSR / oracle | `commit`（真实 `Commit::commitHead` 钩子；`detection_layer=L5`、`outcome=errant_commit`）、`squash`（真实 `ROB::doSquash` 循环；`squashed=1`，绝不冒充 commit）、`chain_end`（诚实 terminal + L5 见证 id） | 已实现（真实 O3 commit/squash 钩子；架构 V/FPSR 数值 oracle 仍由 run-level oracle 提供，不在本注入器内） |
| — | 首影响 | `commit` 上的 `first_impact_sn/first_impact_tick/first_impact_latency`；`chain_end` 汇总 `l5_witness_event` | 已实现（仅在真实 L5 commit 时记录；无 L5 不伪造） |

每次写入事件至少携带（存在即写，未知留空，绝不编造）：
`fault_id`、`event_id`、`parent_event_id`、`tick`、`cycle`、
`core_id`、`thread_id`、`dyn_inst_seq`、`pc`、`opcode`、
`reg_class`、`phys_reg`、`reg_generation`、`arch_reg`、
`lane_width`、`lane_offset`、`bit_in_lane`、`lane_mask`、`fixed_mask`、
`stuck_polarity`、`field=permanent_stuck`、`producer_seq`/`consumer_seq`、
`cell_allocated`/`cell_free`、`state_before`/`state_after`、
`exposure_id`、`exposure_count`、`activated`、
`activated_exposure_count`、`first_activated_sn`、`last_exposure_sn`、
`exposures_total/sampled/dropped`、`generation_changes`、
`before`/`after`、`correct_before`/`stuck_after`、
`stuck_reapplied`、`install_event`、`sample_policy`、
`phys_reads`/`phys_reads_delta`、`corr`。

### 5.1 事件量与采样（诚实计数）

永久故障可能暴露数百万次。实现按 F5 既有纪律做有界采样，**计数保持精确**：

- `exposures_total`：安装+每次目标 cell 写入；
- `exposures_sampled` / `exposures_dropped`：实际写入事件流 / 未写；
- 强制保留：安装、每代首次 exposure、首次 activated exposure、
  每代 `generation_change`、`chain_end`；
- 上限常量：`kVecExposureEventCap=2048`、
  `kVecActivatedEventCap=256`、`kVecGenerationEventCap=4096`、
  `kVecReadEventCap=2048`、`kVecOperandReadCap=2048`。
- `sample_policy=first_of_generation+first_activated+cap`。
- L5 `commit`/`squash` 事件量同样有界：只有发射过 L2 `operand_read` 的
  consumer 才会进入 `L5Ledger`，而 L2 事件受 `kVecOperandReadCap` 限制；
  terminal 计数（`commit_events`/`squash_events`）仍精确，未发射的
  terminal 只计数不补造事件。

### 5.2 读取（phys_read/carrier）粒度

`PhysRegFile` 的 Vec 读路径对目标 phys cell 计数（`vec_stuck_reads`），
CHAOSPhysReg 在下一次 observation（下一次触碰该 cell 的 execute，或运行
结束）报告 `phys_reads_delta`。因此 `carrier_state` 的读事件是
**observation-coalesced** 的，不是逐读事件；真实 total 在
`phys_reads` 中精确。注入器自身的快照使用 `readVecRegRaw()`，不计入
程序读。

### 5.3 generation 链重启语义

- 安装：`fault_installed`（根）→ `carrier_state`；`exposure_id=1`。
- 同一代写入：`phys_write` → （首次/首次激活）`stuck_reapplied` →
  `execute` → `prf_writeback`；`exposure_id` 递增。
- generation 变化：`generation_change`（`parent` 指向旧代 chain root，
  只连接生命周期，不连接旧 producer/consumer），随后 `exposure_id`
  从 1 重新开始，`last_carrier_event` 清零；新代 L2 只能挂到
  `generation_change` 生命周期节点，不会挂到旧代 carrier。
- 运行结束：`chain_end`（诚实 terminal，携带精确 totals），然后
  `clearPermanentFaults()`。

### 5.4 L5 commit / squash / 首影响

真实钩子（只读，不改变控制流）：

| 位置 | 调用 | 事实 |
|---|---|---|
| `Commit::commitHead()`，紧邻 `chaosFPU->noteCommit` | `chaosPhysReg->noteCommit(tid, head_inst.get())` | 指令**真的已提交** |
| `ROB::doSquash()` 的真实 squash 循环 | `chaosPhysReg->noteSquash(tid, (*squashIt[tid]).get())` | 指令**真的被 squash** |

只有“真实 consumer”能到达 L5：`DynInst::execute()` 后扫描
`renamedSrcIdx()`，发现源操作数就是永久故障 cell，并且当前至少已有一次
activated exposure（缺陷确实改变过正确值），才在 `L5Ledger` 记录该
`seqNum`。任意其他指令不会产生 L5 事件。

- `noteCommit`：发射 `kind=commit`，`detection_layer=L5`，
  `outcome=errant_commit`，携带 `consumer_seq`、`dyn_inst_seq`、
  `commit_seq`（该 fault 链的 L5 commit 序号，1 起）、`pc`、`opcode`、
  `reg_class=vec`、`phys_reg`、`reg_generation`（**读取时**的世代，
  不是当前世代）、`install_event`、`value_hash`/`before`/`after`
  （读取时观察到的 lane 值）、`first_impact_sn`、
  `first_impact_tick`、`first_impact_latency`。
  事件 `parent_event_id` = 该 consumer 的 L2 `operand_read`，形成
  L1 carrier → L2 operand_read → L5 commit 的可达链。
- `noteSquash`：发射 `kind=squash`，`squashed=1`，`outcome=squashed`，
  `detection_layer` 留空（squash 不是 L5 检测），永不发射 commit；
  `parent_event_id` 同样指向该 consumer 的 L2 事件。squash 不清除永久
  故障、不消耗 fault、不改变控制流。
- 首影响只在**第一条真实 L5 commit** 记录：
  `first_impact_sn` = 该 consumer 的 `dyn_inst_seq`；
  `first_impact_tick` = commit tick；
  `first_impact_latency` = commit tick − 首次 activated exposure tick
  （若从未 activated，则改用安装 tick；文档明确该基准）。
- `chain_end.terminal` 诚实取值：
  - `committed`：存在真实 L5 commit；
  - `squashed`：consumer 被 squash 且没有任何 commit；
  - `exposed_unconsumed`：有 activated exposure，但没有 consumer 到 L5；
  - `not_activated`：没有任何 activated exposure。
  没有 L5 事件时**绝不**声称 `committed`。
- `chain_end` 另带 `first_impact_sn`、`first_impact_tick`、
  `first_impact_latency`、`l5_witness_event`（第一条 commit 的 event_id）、
  `commit_events`、`squash_events`、`consumers_recorded`。

### 5.5 读暴露与写入重施加分开计数

- `write_exposures_total` = 安装写入 + 每次对目标 cell 的写入重施加；
  与历史字段 `exposures_total` / `exposure_count` 同值（保持 F5 既有
  审计语义）。
- `read_exposures_total` = 容器读路径（`PhysRegFile::getReg(void*)`）
  对目标 cell 的真实读取总数；`phys_reads` 是同一精确值的既有别名。
- 两者**从不合并**；每个事件与 `chain_end` 都分别携带。注入器自身的
  快照使用 `readVecRegRaw()`，不计入程序读。

## 6. 需要主 agent 在共享文件添加的 PROP 字段

`CHAOSPropagation.hh` 属于共享/主 agent 文件，本任务未修改。以下字段已由
CHAOSPhysReg 发射，但不在当前 `PROP_EVT_FIELDS` /
`PROP_EVT_EXT_FIELDS` allowlist 中；若不加，`notePropEvt` 会丢弃并告警一次：

`generation_old`, `generation_new`, `generation_changes`,
`cell_allocated`, `cell_free`, `stuck_reapplied`,
`phys_reads`, `phys_reads_delta`, `permanent_key`（预留，本轮未用）。

[FR03][L5] 本轮新增、同样需要加入 allowlist 的字段（**本轮未改
`CHAOSPropagation.hh`：该文件正由 F5 加固任务并发修改；主 agent 合并后
请一次性补入 `PROP_EVT_EXT_FIELDS`**）：

`first_impact_sn`, `first_impact_tick`, `l5_witness_event`,
`commit_events`, `squash_events`, `consumers_recorded`,
`read_exposures_total`, `write_exposures_total`。

未加入前，发射端会丢弃这些键并只告警一次；`chain_end` 仍通过已存在的
`exposures_total`（写）与 `phys_reads`（读）携带精确值，`affected_sn`
在 commit 事件上等于首影响 seq。gate 断言脚本会把缺失字段判为 FAIL，
避免“静默丢证据”。

已存在、无需新增的字段：`reg_generation`, `exposure_id`,
`exposure_count`, `activated_exposure_count`, `exposures_total`,
`exposures_sampled`, `exposures_dropped`, `first_activated_sn`,
`last_exposure_sn`, `affected_sn`, `install_event`, `stuck_polarity`,
`fixed_mask`, `correct_before`, `stuck_after`, `lane_width`,
`lane_offset`, `lane_mask`, `bit_in_lane`, `reg_class`, `producer_seq`,
`consumer_seq`, `activated`, `squashed`, `terminal`, `outcome`,
`sample_policy`, `state_before`, `state_after`。

## 7. 测试（真实命令与真实输出）

```bash
g++ -O0 -std=c++17 -Wall -Wextra -Werror \
    -I CHAOS/gem5/src/cpu/o3/CHAOSPhysReg \
    tests/unit/chaos_vec_stuck_test.cc -o /tmp/chaos_vec_stuck_test
/tmp/chaos_vec_stuck_test
# -> ALL CHECKS PASSED（含 still applies after reallocation / matches ignores generation）

g++ -O0 -std=c++17 -Wall -Wextra -Werror \
    -I CHAOS/gem5/src/cpu/o3/CHAOSPhysReg \
    tests/unit/chaos_physreg_generation_test.cc -o /tmp/chaos_generation_test
/tmp/chaos_generation_test
# -> ALL GENERATION CHECKS PASSED（63 项，含：
#    PERMANENT STUCK ACROSS GENERATIONS
#    GENERATION CHAIN RESTART: exposure_id back to 1
#    SQUASH DOES NOT CLEAR
#    int/float register class does not cross-talk
#    reset clears the cell
#    write exposures exclude reads / read exposures exclude writes
#    squash does not count as a commit
#    real commit wins the terminal
#    old generation consumer keeps its own generation
#    old/new generation L2 parents never merge）

python3 -m pytest tests/test_chaos_physreg_generation_cpp.py -q
# -> 7 passed
#    （含静态 wiring：commit.cc/rob.cc 真实调用 noteCommit/noteSquash；
#      CHAOSPhysReg 仅在 emitVecTerminal 调用 clearPermanentFaults；
#      gate 断言脚本对 synthetic 链的正/负例）

python3 -m pytest tests/test_chaos_vec_stuck_cpp.py \
    tests/test_lsu_prop_fields.py -q
# -> 1 passed（字段注册表未改动，保持通过；未收集到用例的
#    test_lsu_prop_fields.py 由主 agent 的全量命令覆盖）

python3 -m pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py \
    tests/test_chaos_vec_stuck_cpp.py \
    tests/test_chaos_physreg_generation_cpp.py -q
# -> 313 passed（本轮实测快照；数字随其他并行任务新增测试变化，
#    以实际输出为准）
```

CHAOSPhysReg.cc 在真实 gem5 构建前的额外静态检查（host g++，未运行
scons/gem5）：

```bash
g++ -fsyntax-only -std=c++17 -DTRACING_ON=1 \
    -I CHAOS/gem5/build/ARM -I CHAOS/gem5/src -I CHAOS/gem5/ext \
    -I CHAOS/gem5/ext/systemc/include \
    -I CHAOS/gem5/ext/googletest/googletest/include \
    -I CHAOS/gem5/ext/googletest/googlemock/include \
    -I CHAOS/gem5/ext/fmt/include \
    -I CHAOS/gem5/ext/nlohmann_json/single_include \
    -I CHAOS/gem5/ext/pybind11/include \
    CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc
# -> 0 errors；本文件新增代码 0 warning（仅保留原有 3 条旧警告：
#    processFault 的 sign-compare ×2、checkPermanent 的 unused tid）

# L5 钩子的两个 host 文件同样做真实语法检查：
timeout 300 g++ -fsyntax-only -std=c++17 -DTRACING_ON=1 \
    -I CHAOS/gem5/build/ARM -I CHAOS/gem5/src -I CHAOS/gem5/ext \
    -I CHAOS/gem5/ext/systemc/include \
    -I CHAOS/gem5/ext/googletest/googletest/include \
    -I CHAOS/gem5/ext/googletest/googlemock/include \
    -I CHAOS/gem5/ext/fmt/include \
    -I CHAOS/gem5/ext/nlohmann_json/single_include \
    -I CHAOS/gem5/ext/pybind11/include \
    CHAOS/gem5/src/cpu/o3/commit.cc CHAOS/gem5/src/cpu/o3/rob.cc
# -> 0 errors（分别执行同样是 0）
```

注意：本轮新增 `CHAOSPhysReg.py::requireAllocated`，而
`CHAOS/gem5/build/ARM/params/CHAOSPhysReg.hh` 是 scons 生成物（未纳入
git）。为在不运行 scons 的前提下完成 `-fsyntax-only`，本机已在上述
**未跟踪的生成头**中同步加入 `bool requireAllocated;`；主 agent 的
`scons` 构建会从 `.py` 重新生成同一字段。源码树与提交内容不包含该
生成物。

真实 gem5 构建、FR03 gate 与正式 seed **未在本轮运行**（由主 agent
构建后执行）。

## 8. 仍未完成 / BLOCKED

1. **runner/schema 的 `component=physreg` 路由未接入**（`tools/fsu_seed_runner.py`
   属于 Agent A，本轮未改）。当前 runner 只走 `--chaos_fpu`；FR03 manifest
   的 `injector.component=physreg` 必须由主 agent 路由到
   `--chaos_phys`，禁止静默落到 FPU。详见 §9。
2. **L5 新字段尚未进入 tracer allowlist**：`CHAOSPropagation.hh` 正由 F5
   加固任务并发修改，本轮未动；合并后由主 agent 补入 §6 的字段列表。
3. **真实 gem5 gate 未运行**：host 单测与静态 wiring 已通过，但
   rename/free/realloc/squash 的 O3 容器级行为只能由真实 gem5 gate 证明。
   gate 配置/manifest/命令/断言脚本见 §9，由主 agent 构建后执行。
4. **wakeup/fanout（L4）与 RAT/ready（L1）细分未实现**：现有 execute
   钩子只能观察 writeback 与 operand read。
5. **采样上限是常量**（见 §5.1），FR03 正式运行前必须预注册；超过上限的
   exposure 只保留精确计数，不保留逐条值。operand_read / commit / squash
   也受各自上限约束；gate 断言会检查 `total >= observed`，不会把采样当全量。
6. **读事件是 observation-coalesced**，不是逐读；逐读需要容器回调
   injector（会引入生命周期耦合）。`read_exposures_total` 仍是精确总数。
7. **arch_reg 映射是 best-effort**：取 `staticInst->destRegIdx(i)` /
   `srcRegIdx(i)` 的架构索引，不做 rename-map 反查；无法映射时留空。
8. **多故障安装**：`armVecStuck` 仍是单目标；若一次运行安装第二个 Vec
   stuck 故障，会覆盖前一目标（前一 fault 无 terminal）。FR03 正式设计为
   “每次运行固定 1 cell”，但多故障场景需另立合同。
9. **`fault_id`/ptag 命名空间与其他 family 共享**：`notePropEvt` 用
   `fault_id` 作为 ptag 游标；若同一运行还启用了其他 FSU_PROP family，
   自动 parent 可能串到别的链。FR03 正式运行必须只启用 CHAOSPhysReg
   （或由主 agent 在审计器中按 family 隔离游标）。
10. **离线 chain checker 的 F5 分支仍按 kind=`exposure` 统计 exposure**，
    而 CHAOSPhysReg 发射 kind=`phys_write`。FR03 gate 目前使用
    `tests/unit/fr03_gate_assert.py` 做 FR03 专用断言；若要并入
    `fsu_chain_check` 的 certified 路径，需由 owner 明确 FR03 的
    branch-kind 映射（不得静默放宽 checker）。

**结论：FR03 永久物理 cell 的语义、L0–L5 真实钩子、读写分离计数与真实
target 策略已实现并通过 host 单测/静态 wiring；真实 gem5 gate 与正式
seed 尚未运行，FR03-F5 仍为 PARTIAL，不得认证。**

## 9. 交接：主 agent 需要完成的 runner/schema/gate 接线

> 本轮未修改 `tools/fsu_seed_runner.py`、`schemas/manifest.schema.json`、
> `runs/`。以下字段/命令由主 agent 接入。

### 9.1 runner / schema 字段

manifest 的 `injector` 新增（或复用）以下语义：

| 字段 | 值 | 必填 | 说明 |
|---|---|---|---|
| `component` | `"physreg"` | 是 | 显式选择 CHAOSPhysReg；runner 必须拒绝未知 component，禁止静默落到 `fsu`/FPU |
| `physreg_mode.injectionMode` | `"phys"` | 是 | 只允许 ITC'23/GeFIN 物理抽象；`arch_*` 不得用于 FR03 正式路径 |
| `physreg_mode.regTargetClass` | `"vector"` | 是 | VecRegClass |
| `physreg_mode.targetPhysRegIdx` | 整数 ≥0 | 是 | 固定真实 target（禁止随机）；建议先用 pilot 观察 `fault_injections.log` 的 `PhysReg[...]`，或从 0 起用 `requireAllocated` 保证真实占用 |
| `physreg_mode.requireAllocated` | `true` | 是 | 只在实际被 in-flight 指令持有的 cell 上安装；free 时重试且不消耗 fault |
| `physreg_mode.vecLaneWidth` | `32` | 是 | 128-bit NEON 的 4×32 lane |
| `physreg_mode.vecLaneOffset` | 0..3 | 是 | 与 W3 golden 对应的固定 lane |
| `physreg_mode.faultMask` | 如 `"0x1"` | 是 | lane 内 mask；全程固定 |
| `physreg_mode.faultType` | `"stuck_at_zero"` / `"stuck_at_one"` | 是 | 极性由 faultType 决定；不得用 bit_flip 冒充永久 |
| `physreg_mode.permanent` | `true` | 是 | 对 physreg 由 stuck_at_zero/one 隐含；runner 必须校验为 true |
| `max_faults` | `1` | 是 | 单永久 fault |
| `first_clock` | `0` | 是 | 不限制窗口（0 = unrestricted） |
| `rng_seed` | 非零 | 是 | 可复现 |
| `probability` | `1.0` | 是 | 单次安装 |

对应 CLI（本轮已在 `configs/se/ooo_proxy.py` 与 `configs/se/arm_chaos.py`
加入 `--phys_require_allocated`；其余 flag 原本已存在）：

```text
--chaos_phys --phys_mode phys --phys_reg_class vector
--phys_target_idx <IDX> --phys_require_allocated
--vec_lane_width 32 --vec_lane_offset <LANE>
--fault_type stuck_at_zero|stuck_at_one --fault_mask <MASK>
--bits_to_change 1 --first_clock 0 --max_faults 1 --rng_seed <SEED>
--chaos_propagation --prop_run_id <RUNID> --prop_sample_run_id <S>
```

schema 需要：`component` enum 增加 `"physreg"`；新增 `physreg_mode`
对象（上述字段类型/范围）；若沿用 `fault_mask` 顶层字段也可，但必须与
`physreg_mode` 一值一源。runner 需要把 `injector.physreg_mode` 翻译成上述
CLI，并把 census/injection 两次运行使用同一组参数。

### 9.2 gate manifest 片段（非正式，不计 seed）

```json
{
  "run_id": "FSU-FR03-F5-W3-PHYSREG-GATE",
  "model_id": "FR03",
  "unit": "PRF_Vec",
  "freq": "F5",
  "load_id": "W3",
  "submodel": "FR03-a",
  "config_family": "C3",
  "config_profile": "B0",
  "workload": {
    "binary": "workloads/directed/neon_fp32_lane_kernel",
    "identity": "W3-neon-fp32-lane-v1",
    "golden_id": "neonfp32lane-v1-golden",
    "oracle_kind": "array_hash",
    "oracle_tol": 0
  },
  "injector": {
    "component": "physreg",
    "physreg_mode": {
      "injectionMode": "phys",
      "regTargetClass": "vector",
      "targetPhysRegIdx": 0,
      "requireAllocated": true,
      "vecLaneWidth": 32,
      "vecLaneOffset": 2,
      "faultType": "stuck_at_zero",
      "faultMask": "0x1",
      "permanent": true
    },
    "max_faults": 1,
    "first_clock": 0,
    "probability": 1.0,
    "rng_seed": 1
  },
  "limits": { "timeout_s": 1800 },
  "notes": "FR03 permanent physical-cell gate. NOT a formal RunID. targetPhysRegIdx/requireAllocated must be validated by the assertion script: a real L5 commit or a real squash, exact read/write counters, and generation isolation."
}
```

`targetPhysRegIdx=0` 是 gate 起点：O3 的 Vec free list 在初始化时把
`0..numVecPhysRegs-1` 全部加入，`requireAllocated=true` 会等到该 cell
真正被 in-flight 指令持有才安装。若 pilot 显示 0 号 cell 在 ROI 内未被
使用，主 agent 应先跑一次 `targetPhysRegIdx=-1` 的探针（日志会打印
`PhysReg[...]`）再固定为真实被使用的索引；不得用随机 free slot 冒充。

### 9.3 gate 运行与断言

构建后（主 agent 执行，Agent B 未运行）：

```bash
build/ARM/gem5.opt -d runs/fsu-gates/FR03-F5-W3-PHYSREG-PILOT \
  configs/se/ooo_proxy.py \
  --cmd workloads/directed/neon_fp32_lane_kernel --cpu O3 \
  --chaos_phys --phys_mode phys --phys_reg_class vector \
  --phys_target_idx 0 --phys_require_allocated \
  --vec_lane_width 32 --vec_lane_offset 2 \
  --fault_type stuck_at_zero --fault_mask 0x1 --bits_to_change 1 \
  --first_clock 0 --max_faults 1 --rng_seed 1 \
  --chaos_propagation \
  --prop_run_id FSU-FR03-F5-W3-PHYSREG-GATE --prop_sample_run_id s1

python3 tests/unit/fr03_gate_assert.py \
  runs/fsu-gates/FR03-F5-W3-PHYSREG-PILOT/prop_evt.txt.gz \
  --json-out runs/fsu-gates/FR03-F5-W3-PHYSREG-PILOT/fr03_assert.json
```

断言脚本检查：唯一永久根、固定 target/mask/polarity、每次 `phys_write`
都满足 `after == force(before, mask, polarity)` 且非目标位不动、L2
consumer 与 L5 commit 的 seq 可达、squash 不是 commit、旧世代不并入
新世代、squash / generation_change 之后仍有同 cell 的后续写入（证明未
被清除）、`chain_end.terminal` 诚实、
`read_exposures_total`/`write_exposures_total` 分别存在且
`total >= observed`、`l5_witness_event`/`first_impact_sn` 与首条
commit 一致。

gate 必须覆盖（可拆成多条非正式 run，均不计 seed）：
1. 连续写仍卡死（`phys_write` 序列 + 末值仍是 polarity）；
2. squash 后仍卡死（squash 事件之后目标 cell 仍被重施加）；
3. 同 cell free/realloc 后仍卡死（`generation_change` 后 `phys_write`
   仍带同一 `fixed_mask`/`stuck_polarity`）；
4. generation 链身份（新代 `exposure_id` 从 1 起，旧代 L2/L5 不挂到
   新代根）；
5. 真实 L5（commit 或 squash 至少一个真实事件）；
6. runner 确实走 CHAOSPhysReg（`fault_injections.log` 出现
   `CHAOSPhysReg`，且 FPU 注入日志不出现）。

全部 PASS 才进入正式 `FR03-F5-W3` seed1/2/3；否则保留 PARTIAL。
