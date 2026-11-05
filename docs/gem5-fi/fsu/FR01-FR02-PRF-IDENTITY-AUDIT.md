# FR01/FR02 W1 PRF 身份路径审计（真实 W1 证据）

日期：2026-11-05　分支：`fsu`　基线 HEAD：`9afebbd2`

本文替代此前“W1 scalar FP 在 vector PRF 找不到 consumer”的观察性结论。
该结论的原始证据（v8/v9/v10 探针）实际运行的是
`workloads/directed/neon_fp32_lane_kernel`（见各 `run.out` 中
`readlink()` 返回路径），**不是 W1**，因此不能作为 W1 的结论。

## 1. 结论（按任务清单逐项）

| # | 问题 | 事实结论 | 证据 |
|---|---|---|---|
| 1 | W1 FP32/FP64 指令的 arch reg class | **VecRegClass**。AArch64 的 `FloatRegClass` 是 0 寄存器占位（注释 “Not applicable to ARM”）；AA64 FP 操作数 `VectorReg` → `VecRegOp` → `reg_class = vecRegClass` | `CHAOS/gem5/src/arch/arm/isa.cc:85`；`arch/arm/isa/operands.isa:90,427-443`；`arch/arm/regs/vec.hh:101` |
| 2 | rename 后实际 phys reg class | **VecRegClass**（`renameSrcRegs` 对 `srcRegIdx` flatten 后查 `UnifiedRenameMap`） | `cpu/o3/rename.cc:1109-1145` |
| 3 | scalar FP 与 NEON 是否共享 Vec PRF | **是**。V0-V31 与 NEON lane 使用同一个 `VecRegClass` 物理寄存器池（`NumVecRegs=44`） | `arch/arm/regs/vec.hh:95-107` |
| 4 | pending-source 搜索是否遗漏 scalar FP 的 Vec source | **没有类遗漏**；但 `ready` 的未发射 FP source 在 O3 中极稀少（FP 指令 source 一旦 ready 立即发射）。旧的 32 次随机抽样 + 回退会落到无消费者的死槽 | v10/attempt-1/2：phys=34, gen=1, before=0x0，全运行 0 读 |
| 5 | phys / flat / lane index 是否混用 | 未混用：phys index 限定 `numVecPhysRegs()`；fault 域固定 128-bit flat；lane 由 `flat / lane_width` 派生；`getReg` 使用 phys index | `CHAOSPhysReg.cc` 选择/`chaos_vec_transient.hh` |
| 6 | producer/consumer/generation 记录时刻是否一致 | **旧实现不一致（已修复）**：consumer 的 generation 在 post-execute 时读取，cell 可能已在读后释放/复用；store 的数据读发生在 `initiateAcc()`，晚于 post-execute 钩子 | 见 §3 |
| 7 | 目标是否在源读取后才注入 | 旧随机路径可能；新实现保证在消费者 `execute()` 前安装 | `DynInst::execute()` → `maybeInjectBeforeExecute()` |
| 8 | `not_consumed` 是真实无消费还是链没接上 | **两者都出现过**：attempt-1/2 是真实死槽；v13–v16 是真实消费（输出 SDC）但链把读丢弃 | §3 |
| 9 | arch_frontend 与 phys 路径差异 | 仅目标解析不同：arch_frontend 用 `renameMap.lookup(arch)` 取当前 phys；phys 直接用 phys index。注入点、PRF 读跟踪、事件链**完全同一条路径**。v9（显式 phys=46）与 v8（arch V0→46）产生逐字相同的 consumer 身份 | §2.3 |

## 2. 真实 W1 身份链

### 2.1 正式 FR01-F0-W1 seed1 attempt-5（`runs/fsu/FSU-FR01-F0-W1/seed1/attempt-5`）

配置：phys, vector, target=-1, `target_selection=ready_consumer`,
`target_precision=64`, lane_width=64, lane_offset=0, bit 5, FR01-a。

| 阶段 | 真实值 |
|---|---|
| arch reg | V0 (`arch_reg=0`) |
| rename phys | `phys_reg=44`，`reg_generation=12` |
| install | cycle 35608，`before=0x7ff8000000000000`（FP64 qNaN），`after=0x7ff8000000000020` |
| field/precision | `field=mant_lo`，`precision=fp64` |
| consumer | `dyn_inst_seq=13161`，`pc=0x400d9c`，`opcode=fadd`（D 寄存器），`precision=fp64`，读值 `0x7ff8000000000020` |
| L5 | same seq commit @ cycle 35611，`terminal=committed` |
| oracle | `ARRAYHASH=ffe18c8279bf419d94ad7b1592c56fb874d3440506066d93ede75820f2eba183` ≠ golden `ffe18c8279bf419d9b0aad0f5e039018...` → **SDC** |
| 审计 | `fsu_chain_check`: full / admitted / certified；`fsu_seed_audit`: ok=true |

机器码核对：`0x400d9c` 为 `fadd d0, d0, d1`（objdump），D 寄存器 = FP64。

### 2.2 v16 非正式 gate（`runs/fsu-gates/FR01-FR02-F0-W1-v16`）

store 消费者路径（证明 store 数据读也属于 L2）：

```
fault_applied phys=5 gen=5938 before=0x7f800000 after=0x7f800020
operand_read  sn=160525 pc=0x400ee8 opcode=str  value=0x7f800020 activated=1
commit        sn=160525 @ cycle 501503
chain_end     terminal=committed
oracle ARRAYHASH32 923eb96e... != golden ffe18c82...   (SDC)
```

`str s0, [x0, x10, lsl #2]` 的 vector 数据操作数在 `initiateAcc()` 读取，
晚于 `DynInst::execute()` 的 post-execute 钩子——这是旧追踪漏读的具体机制。

### 2.3 arch_frontend 与 phys 的等价性

历史探针（NEON kernel）中：
- v8 `arch_frontend`, ArchReg 0 → phys 46, gen 17149；
- v9 `phys`, 显式 phys 46；
两者产生相同的 `operand_read dyn_inst_seq=732176 / pc=0x400624 / fmadd /
gen=17149` 与 commit。这证明差异只在目标解析，不在追踪路径。
（因该探针不是 W1，只用于路径等价性，不作为 W1 证据。）

## 3. 根因与修复（按缺陷单元）

### 缺陷 1：HEAD 无法编译，consumer-aware 代码从未生效

`physRegHasPendingSource` 声明在 `InstructionQueue`，定义写成
`IQUnit::`（`8a...`，commit `05f527f2`）。HEAD `9afebbd2` 因此
`scons` 失败；01:02 的旧二进制被复用到 01:16 之后的全部 W1 运行。
修复：定义改为 `InstructionQueue::physRegHasPendingSource`，并新增
`collectReadyPendingSources`。

### 缺陷 2：随机 phys 目标可落在无消费者死槽

旧逻辑 32 次随机抽样后回退到任意已分配槽。W1 formal doubt seed1
attempt-1/2 命中 phys=34/gen=1（值 0，全运行无读）。
修复：`target_selection=ready_consumer` 只在“真实消费者事件”上目标选择；
无候选时延期（不消耗 fault），并在消费者 `execute()` 前装填（见缺陷 4）。

### 缺陷 3：generation 被当作读过滤条件

post-execute 钩子用 `generationOf(src)`（当前世代）与安装世代比较；
cell 在读取后释放/复用即把真实读丢弃，得到虚假 `free_realloc`/`not_consumed`。
W1 v13/v14 输出已改变（SDC）但链记录无读。
修复：generation 只作 provenance；任何对目标 cell 的真实写才终止瞬态；
读事件使用 `getRegOperand` 处捕获的实际值。

### 缺陷 4：store 数据读晚于 post-execute 观察

store 的 vector 数据操作数在 `initiateAcc()` 读取。旧钩子先于读运行，
因此漏掉 store 消费者。修复：在 `DynInst::getRegOperand(void*)` 处直接
记录精确读快照并发射 L2；post-execute 观察仅作非 store 回退。

### 缺陷 5：precision 由 cell 值无法判定

同一个 V cell 可被 `str s0`（FP32）和 `fadd d0`（FP64）读取。
v1 选择曾把 FP32 读当成 FR01-a（attempt-3，SDC 但子模型不符）。
修复：从消费者真实 AArch64 编码 `ArmStaticInst::encoding()` +
`chaos_fsu::decodedPrecision` 判定 precision，`target_precision=64`
才进入 FR01-a 的 eligible 集合；事件写入 `precision`/`field`。

## 4. 修复后仍存在的协议偏差（必须登记）

- 新目标选择是“warm-up 后第一个 precision 合格的消费者事件”，
  不是工作簿要求的“全部 eligible events 上均匀抽样（countOnly +
  fixed uniform ordinal）”。见 `FR01-FR02-PROTOCOL-V2.md`。
- `ready_consumer` 的事件粒度是 (instruction, source operand)，同一
  cell 可被多个事件选中；这是对“eligible event”的正确解释。
- FR02 的两位审计仍使用单 bit 校验路径；在正式 FR02 运行前需扩展
  审计到 bit pair/geometry（本审计已记录，不冒充通过）。

## 5. 复现命令

```bash
# 正式 seed1（会新建 attempt-N，不覆盖旧 attempt）
python3 tools/fsu_seed_runner.py \
  --manifest configs/fsu/FR01-F0-W1-seed1.json --seed 1 --allow-rerun
python3 tools/fsu_seed_audit.py runs/fsu/FSU-FR01-F0-W1/seed1/attempt-5
```

非正式 directed gate（500k == 预热后）：

```bash
CHAOS/gem5/build/ARM/gem5.opt --quiet -d /tmp/fr01-gate \
  configs/se/ooo_proxy.py --cmd workloads/directed/w1_fp_scalar_probe --cpu O3 \
  --first_clock 500000 --max_faults 1 --rng_seed 1 \
  --chaos_phys --phys_mode phys --phys_reg_class vector --phys_target_idx -1 \
  --phys_target_selection ready_consumer --phys_target_precision 64 \
  --phys_require_allocated --vec_lane_width 64 --vec_lane_offset 0 \
  --fault_type bit_flip --fault_mask 0x20 --bits_to_change 1 \
  --phys_semantic_role FR01-a --phys_load_id W1 \
  --chaos_propagation --prop_run_id FSU-FR01-F0-W1 --prop_sample_run_id s1
```
