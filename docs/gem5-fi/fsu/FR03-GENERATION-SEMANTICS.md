# FR03 永久物理 cell：generation 语义裁决与实现

> 适用：`FSU-FR03-F5-W3 / W5 / W6`（固定 Vec phys reg / lane / bit，SA0/SA1）。
> 实现位置：`CHAOS/gem5/src/cpu/o3/regfile.hh`、
> `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/`、
> `CHAOS/gem5/src/cpu/o3/free_list.hh`、`chaos_vec_stuck.hh`。
> 状态：**语义裁决 + host/C++ 单测完成；CHAOSPhysReg 真实 gem5 路径部分完成；
> FR03-F5 仍为 BLOCKED（不可认证）**。本文不把 FR03 标为 COMPLETE。

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
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/chaos_vec_stuck.hh` | 永久 key 改为 class+index；`Target::matches()`；新增 `GenerationLedger`（镜像 flat_generation）与 `PermanentCell`（每次写入强制、generation 变化时 exposure_id 链重启、其他 class/index/lane/bit 不变、squash 无清除接口、`clear()` 才清除）。 |
| `CHAOS/gem5/src/cpu/o3/regfile.hh` | `isVecStuckTarget()` 去掉 generation 比较；新增 `vec_stuck_reads`（容器读路径计数）、`readVecRegRaw()`（注入器快照不计读）、`clearPermanentFaults()`、`vecStuckActive()/getVecStuckReads()`；更新 FR03 合同注释。 |
| `CHAOS/gem5/src/cpu/o3/free_list.hh` | 注释改为“generation 只是身份，故障跨复用存活”；行为不变（仍 `noteRegFreed`）。 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh/.cc` | 安装/写入/读/执行/写回/generation change/terminal 的 FSU_PROP 发射；安装后同一 physical cell 在任意 generation 重施加；`armVecStuck` 记录安装世代仅作 provenance；运行结束 `chain_end` + 清除。 |

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
| L5 | ROB commit / squash / 架构 V/FPSR / oracle | 仅 `chain_end`（`terminal=run_end`） | **BLOCKED**：owned 文件内没有 commit/squash/oracle 钩子；不得声称 L5 或 FR03-F5 可认证 |
| — | 首影响 | 未发射 | **BLOCKED**（依赖真实 L5 消费见证；不伪造） |

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
  从 1 重新开始。
- 运行结束：`chain_end`（`terminal=run_end`，携带精确 totals），然后
  `clearPermanentFaults()`。

## 6. 需要主 agent 在共享文件添加的 PROP 字段

`CHAOSPropagation.hh` 属于共享/主 agent 文件，本任务未修改。以下字段已由
CHAOSPhysReg 发射，但不在当前 `PROP_EVT_FIELDS` /
`PROP_EVT_EXT_FIELDS` allowlist 中；若不加，`notePropEvt` 会丢弃并告警一次：

`generation_old`, `generation_new`, `generation_changes`,
`cell_allocated`, `cell_free`, `stuck_reapplied`,
`phys_reads`, `phys_reads_delta`, `permanent_key`（预留，本轮未用）。

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
# -> ALL GENERATION CHECKS PASSED（37 项，含：
#    PERMANENT STUCK ACROSS GENERATIONS
#    GENERATION CHAIN RESTART: exposure_id back to 1
#    SQUASH DOES NOT CLEAR
#    int/float register class does not cross-talk
#    reset clears the cell）

python3 -m pytest tests/test_chaos_vec_stuck_cpp.py \
    tests/test_chaos_physreg_generation_cpp.py -q
# -> 2 passed
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
```

真实 gem5 构建、FR03 gate 与正式 seed **未在本轮运行**（由主 agent
构建后执行）。

## 8. 仍未完成 / BLOCKED

1. **L5（commit/squash/oracle）与首影响未实现**：本任务 owner 范围不含
   `commit.cc` / `rob.cc` / oracle 路径，无法提供真实 L5 见证。因此
   `chain_end` 只标 `terminal=run_end`，**不**声称 committed、contained
   或 first impact。
2. **wakeup/fanout（L4）与 RAT/ready（L1）细分未实现**：现有 execute
   钩子只能观察 writeback 与 operand read。
3. **runner 显式选择 CHAOSPhysReg 的 manifest 路径不在本任务文件范围**；
   `tools/fsu_seed_runner.py`/schema 的 FR03 路由仍需主 agent owner 完成。
   当前 CHAOSPhysReg.py 也没有 `fsuModel/fsuFreq` 参数，事件中固定写
   `model_id=FR03`、`freq=F5`；正式 manifest 需要 owner 补齐参数路由。
4. **采样上限是常量**（见 §5.1），FR03 正式运行前必须预注册；超过上限的
   exposure 只保留精确计数，不保留逐条值。
5. **读事件是 observation-coalesced**，不是逐读；逐读需要容器回调
   injector（会引入生命周期耦合）。
6. **arch_reg 映射是 best-effort**：取 `staticInst->destRegIdx(i)` /
   `srcRegIdx(i)` 的架构索引，不做 rename-map 反查；无法映射时留空。
7. **多故障安装**：`armVecStuck` 仍是单目标；若一次运行安装第二个 Vec
   stuck 故障，会覆盖前一目标（前一 fault 无 terminal）。FR03 正式设计为
   “每次运行固定 1 cell”，但多故障场景需另立合同。
8. **`fault_id`/ptag 命名空间与其他 family 共享**：`notePropEvt` 用
   `fault_id` 作为 ptag 游标；若同一运行还启用了其他 FSU_PROP family，
   自动 parent 可能串到别的链。FR03 正式运行必须只启用 CHAOSPhysReg
   （或由主 agent 在审计器中按 family 隔离游标）。

**结论：FR03 永久物理 cell 语义已按工作簿裁决实现并通过 host 单测；
FR03-F5 的真实 L0–L5 链与正式实验仍 BLOCKED，不得认证。**
