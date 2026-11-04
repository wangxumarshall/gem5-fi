# FR01 / FR02 F0 审计与瞬态注入实现

> 审计/实现基线：本工作树（`fsu` 分支，HEAD `f7656299`，另有其他会话对
> CHAOSFPU/CHAOSIQ 的未提交修改；本文只涉及 CHAOSPhysReg、regfile.hh、
> 新增 host 测试与本文档）。
>
> 角色限制：本会话**没有**执行 scons/gem5 构建或 gem5 运行。文中所有
> “已实现/已通过”只对应真实执行的 host 单测与静态源码检查；gem5 侧 gate
> 由主 agent 执行。凡未运行的一律标为“待主 agent 执行”。

工作簿定义（`gem5-fi-FSU单元故障注入方案_逐RunID传播监控-10-源码监控映射.md:21-22`）：

| 模型 | 位置 | 故障 | 子模型 |
|---|---|---|---|
| FR01 | FP/SIMD PRF（VecRegClass 物理寄存器存储位） | 单比特翻转，瞬态 | FR01-a FP64 sign/exp/mant；FR01-b FP32 字段；FR01-c NEON 8/16/32/64-bit lane |
| FR02 | Vec PRF cell 多位字段 | **两个不同 bit** 翻转，瞬态 | FR02-a 同 lane 相邻；FR02-b 同 lane 非相邻；FR02-c 跨 lane；FR02-d exp+mant 跨字段 |

`docs/gem5-fi/fsu/runids.json` 中 `FSU-FR01-F0-W1` / `FSU-FR02-F0-W1`
确实存在（详见第 7 节）。

---

## 1. 精确注入位置与调用时序

### 1.1 修复后的注入点

| 位置 | 文件:行号（当前工作树） | 说明 |
|---|---|---|
| 目标物理寄存器解析 | `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc:1667` `processFault()` | phys 模式按物理索引；`require_allocated` 时只接受不在 free list 的 cell |
| Vec 分支读改写 | `CHAOSPhysReg.cc:1858` | `getReg(phys_reg, buf)` 读整块 → 修改 → `setReg(phys_reg, buf)` 写回 |
| **FR01/FR02 瞬态选择/翻转** | `CHAOSPhysReg.cc:1901-1979` | `selectionFromMask()`（显式 mask）或 `select(rng, ...)`（随机），`applyToVec()` 只 XOR 目标 bit |
| 失败关闭（fail closed） | `CHAOSPhysReg.cc:1905-1955` | `VecFaultFailClosed` 日志 + `vec_transient_fatal=true`；不消费故障、不改 PRF |
| 瞬态事件安装（L0/L1） | `CHAOSPhysReg.cc:258-377` `noteVecTransientInstalled()` | 发 `fault_applied` / `carrier_state` |
| 真实 consumer 读 + 写覆盖观察 | `CHAOSPhysReg.cc:379-598` `observeVecTransient()` | 由既有 execute 后钩子调用 |
| L5 commit / squash | `CHAOSPhysReg.cc:600-725` | 只记录真正读过目标 cell 的 seqNum |
| run 末 chain_end | `CHAOSPhysReg.cc:727-800` `finalizeVecTransient()` | propagation exit-flush 优先，`l0Final` 兜底 |
| 攻击事件失败关闭 | `CHAOSPhysReg.cc:2153-2168` `attackCheck()` | `vec_transient_fatal` 时 unschedule，避免永久重试 |

### 1.2 运行时调用时序

1. `CHAOSPhysReg::startup()`（`CHAOSPhysReg.cc:150` 附近）自附到
   `cpu.chaosPhysReg`，并注册 propagation 的 exit-flush（L0/L1/L5 事件流
   关闭前发 `chain_end`）。
2. attack 事件 → `attackCheck()`（`CHAOSPhysReg.cc:2153`）→
   `processFault(tid)`（`:1667`）。
3. `processFault()` 在 `target_class == VecRegClass` 分支读取目标物理 cell，
   **只对 BitFlip 走瞬态路径**：选择/校验 bit 身份 → 一次 XOR 回写 →
   `noteVecTransientInstalled()`。
4. 之后 `processFault()` 公共尾部设置读跟踪目标
   （`setReadTraceTarget`，`CHAOSPhysReg.cc` 约 `:2070` 之后的公共段），
   由 `readTraceEvent` 轮询 `reads_before_overwrite` / `overwritten`。
5. 每条指令 `staticInst->execute()` 返回后，
   `DynInst::execute()`（`CHAOS/gem5/src/cpu/o3/dyn_inst.cc:382`）调用
   `CHAOSPhysReg::maybeReapplyStuck(this)`。该函数**先**调用
   `observeVecTransient(inst)`（`CHAOSPhysReg.cc:1150-1162`），再走 FR03
   永久 cell 逻辑。
6. 真正 commit：`Commit::commitHead()` 调
   `noteCommit()`（`commit.cc:1356` → `CHAOSPhysReg.cc:1440`），先处理瞬态
   L5。真正 squash：`ROB::doSquash()`（`rob.cc:380` →
   `CHAOSPhysReg.cc:1539`）。
7. 读路径：`PhysRegFile::getReg(PhysRegIdPtr, void*)`
   （`CHAOS/gem5/src/cpu/o3/regfile.hh:401-412`）对 Vec cell 计数真实读取。
8. 写路径（重要）：AArch64 向量目的寄存器在 execute 期间通过
   `PhysRegFile::getWritableReg()`（`regfile.hh:437`）裸指针写入，**不经过**
   `setReg()`。因此写入覆盖检测放在第 5 步的 post-execute 钩子中，并在
   观察到写覆盖时调用新增的 `noteTraceOverwrite()`
   （`regfile.hh:214-218`）冻结读计数。

### 1.3 修复前的位置（本审计起点）

- `CHAOSPhysReg.cc:1043` `processFault()`；Vec 分支 `:1234`；
  lane 解析 `:1247-1259`；`lane_mask` 截断 `:1265`；
  BitFlip `lane_val ^= lane_mask` `:1298`；
  `setReadTraceTarget` `:1394`。
- `generateRandomMask()` `:1029-1035`。
- `regfile.hh:399-440` 是当时的 Vec 读跟踪/写回路径。
- 这些旧行号仅用于说明缺陷来源；修复后位置见 1.1。

---

## 2. 能力状态矩阵

状态定义：IMPLEMENTED = 有真实注入/事件/测试；PARTIAL = 只覆盖部分语义或
证据；MISSING = 无实现。

| 能力 | 修复前 | 修复后 | 证据 |
|---|---|---|---|
| FR01 单 bit 翻转 | **PARTIAL** | **IMPLEMENTED（F0 瞬态路径）** | `chaos_vec_transient.hh`；host 单测；`CHAOSPhysReg.cc:1901+` |
| FR01 目标 lane/bit 定向 | PARTIAL（lane 8/16/32/64） | IMPLEMENTED（128-bit 域内） | `Selection.bits[]` 给出 flat/lane/bit_in_lane/field |
| FR01 非目标位保持 | 结构上只改 lane 字节，但 lane 域是 256B | IMPLEMENTED + host 单测 | `onlySelectedBitsDiffer` |
| FR01 瞬态终止（真实写覆盖） | **PARTIAL/有缺陷** | IMPLEMENTED | post-execute dest 观察 + `noteTraceOverwrite()` |
| FR01 L0–L5 证据 | **MISSING** | IMPLEMENTED（需 `--chaos_propagation`） | `fault_applied`/`carrier_state`/`operand_read`/`commit`/`overwrite`/`chain_end` |
| FR01 generation 身份 | MISSING（bit_flip 不记录） | IMPLEMENTED（provenance） | `reg_generation` 字段 |
| FR01 FP 字段分层（sign/exp/mant 命名） | MISSING | **PARTIAL**：bit 位置/bit_indices 精确，字段名需由 lane/bit 位置与 workload 精度映射 | 未发 `field=sign/exp/mant` 标签 |
| FR02 两个不同 bit | **MISSING（可碰撞）** | IMPLEMENTED | `chooseDistinct()` / `mask_popcount_mismatch` |
| FR02 碰撞 fail closed | MISSING | IMPLEMENTED | host 单测 + `VecFaultFailClosed` |
| FR02 同 lane 相邻/非相邻 | MISSING | IMPLEMENTED | `Geometry::SameLaneAdjacent/NonAdjacent` |
| FR02 跨 lane | MISSING | IMPLEMENTED | `Geometry::CrossLane` |
| FR02 跨 32-bit 字段（exp+mant） | MISSING | IMPLEMENTED（定向 64-bit lane 内两个字段） | `Geometry::CrossField` |
| FR02 128-bit 域正确 | **PARTIAL/错域** | IMPLEMENTED | `kVecBits=128` |
| FR02 两 bit 身份证据 | MISSING | IMPLEMENTED | `bit_indices` / `fault_mask` / `lane_mask` / `full_before` `full_after` |
| 目标 cell 必须 allocated | 仅 `requireAllocated` 可选 | 不变 | `CHAOSPhysReg.cc:1740+` |
| “ready 且后续有 consumer”触发条件 | **未强制** | 仍未强制（只有 not-free 采样；consumer 读取作为事后证据） | 工作簿触发条件的偏差见第 6 节 |

---

## 3. FR01/FR02 的修复前实现与缺陷

### 3.1 FR01

修复前 Vec BitFlip 路径：

```cpp
uint64_t mask = fault_mask.any()
    ? fault_mask.to_ullong()
    : generateRandomMask(rng, num_bits_to_change, 64);
...
uint64_t lane_mask = (lw < 64) ? (mask & ((1ULL << lw) - 1)) : mask;
...
case FaultType::BitFlip:
    lane_val ^= lane_mask;
    stats->numBitFlips++;
    break;
```

缺陷：

1. **域错误**：`generateRandomMask()` 在 `0..63` 均匀抽 bit；随后
   `mask & ((1<<lw)-1)`。当抽取 bit ≥ lane 宽度时 `lane_mask == 0`，
   仍执行 `numBitFlips++` / `numFaultsInjected++`，属于**静默空注入**。
2. **lane 数错误**：`max_lanes = vecRegBytes()/lane_bytes`，AArch64
   `VecRegClass::regBytes()` 是 SVE 后备宽度 256B
   （`arch/arm/types.hh:535-545`，`MaxSveVecLenInBytes=256`），
   32-bit lane 下得到 64 个 lane；随机 lane 可落在架构 128-bit NEON/标量
   FP 值之外（bit 512..2047），不是 FR01 定义的 128-bit Vec 值。
3. **无瞬态证据**：bit_flip 分支不调用任何 FSU PROP 发射函数，没有
   `fault_applied` 根，也没有 generation/consumer/overwrite 事件。
4. **写覆盖不可观测**：Vec 目的寄存器走 `getWritableReg()` 裸指针，
   `trace_overwritten` 只在 `setReg(void*)` 的 Vec 分支置位
   （旧 `regfile.hh:399-440`），真实向量写不会触发，读计数会把覆盖后的
   新值读取也算成“注入值读取”。
5. **无 fail closed**：mask 截断为 0 或部分 bit 丢失时不报错。

### 3.2 FR02

修复前同样走 `generateRandomMask(rng, bitsToChange, 64)`：

```cpp
while (bits_to_change-- > 0) mask |= (1ULL << bitDist(gen));
```

缺陷：

1. **随机碰撞**：`bitsToChange=2` 时两次独立抽 bit 可抽到同一 bit，
   OR 后只剩 1 bit；实际注入的是 FR01 而不是 FR02，且无任何告警。
2. **跨 lane/越界丢失**：`lane_mask` 只保留当前 lane 的 bit；第二个 bit
   若落在别的 lane（跨 lane 子模型）会被截掉。
3. **显式 mask 与 bitsToChange 不一致时不校验**：`fault_mask != 0` 时
   完全忽略 `bitsToChange`；一个 1-bit mask 可以冒充 2-bit 故障。
4. **无 bit 距离/相邻性/lane pair/字段对证据**。
5. 与 FR01 相同的域错误、无 PROP、写覆盖不可观测问题。

---

## 4. 128-bit lane/字段范围与身份

### 4.1 故障域

- 新模型固定 `kVecBits = 128`、`kVecBytes = 16`
  （`chaos_vec_transient.hh:43-45`）。所有 bit 选择/校验都限制在
  **架构 128-bit Vec 值**内；SVE 大于 128-bit 的尾部不属于 FR01/FR02 F0
  的定义，不参与抽取。
- 每个 bit 的身份是四元组：`flat`（0..127）、`lane`
  （`flat / lane_width`）、`bit_in_lane`（`flat % lane_width`）、
  `field`（`flat / 32`）。
- 同 lane 几何要求所有 bit 的 `lane` 相同；跨 lane 几何要求至少两个
  `lane`；跨字段几何要求至少两个 32-bit `field`。定向 64-bit lane 的
  FR02-d 被限制在该 lane 的两个 32-bit 字段内（exp+mant），见
  `chaos_vec_transient.hh` 的 `selectionFromMask` / `select`
  CrossField 分支。
- 失败条件（均 fail closed）：非法 lane 宽度、lane offset 越界、
  `count<=0`、`count>128`、同 lane 域不足、跨 lane 域不足（lane 数<2）、
  跨字段域不足、显式 mask 的 popcount 与请求 bit 数不符、显式 mask 违反
  定向 lane/相邻性/跨 lane/跨字段约束。

### 4.2 物理 cell / generation / producer-consumer 身份

- 物理 cell 身份：`reg_class=VecRegClass` + `phys_reg` 索引。
- generation：`PhysRegFile::flat_generation`，由 `noteRegFreed()` 在
  free list 释放时递增（`regfile.hh` 的 `noteRegFreed`）。FR01/FR02 把它
  作为**provenance**写入每个事件；它不是清除/匹配条件。瞬态故障在真实写
  覆盖后自然消失，与 generation 变化无关。
- producer：覆盖事件在 post-execute 钩子中记录真实写入指令的
  `dyn_inst_seq` / `pc` / `opcode` / `arch_reg` / `reg_generation`，
  作为 `producer_seq`。
- consumer：`operand_read` 事件记录真实读取指令的
  `dyn_inst_seq` / `consumer_seq` / `arch_reg` / `reg_generation` /
  lane 值；只有这些 seqNum 才会在 `noteCommit()` 中产生 L5 `commit`
  （或 `noteSquash()` 产生 `squash`）。squash 永远不是 commit，也不清除
  瞬态状态。
- 证据字段：`bit_indices`（如 `5,37`）、`fault_mask`（128-bit 十六进制）、
  `lane_mask`（首个 lane 的相对 mask）、`before/after`（首个 lane 值）、
  `full_before/full_after`（128-bit 全值）、`value_hash`。

---

## 5. 瞬态故障会不会意外变成永久 stuck？

**不会。** 逐项核对：

1. Vec BitFlip 分支（`CHAOSPhysReg.cc:1901+`）不调用 `armVecStuck()`，
   不写 `permanent_faults`，不调用 `setStuckTarget()`。
   全文件 `armVecStuck(` 恰好 2 次，均在 StuckAtZero/StuckAtOne 分支
   （FR03 永久语义）。
2. `PhysRegFile::reapplyVecStuck()` 只在 `vec_stuck.valid` 时生效；
   瞬态路径从不设置 `vec_stuck.valid`。
3. `setReg(void*)` 的 Vec 分支会在写后调用 `reapplyVecStuck()`，但目标
   未 armed，调用是 no-op。
4. `checkPermanent()` 只处理 `permanent_faults` 中 `IntRegClass` 的条目；
   瞬态路径不登记任何条目。
5. host 单测 `FR01 no permanent/stuck re-apply on later reads` 证明真实写
   覆盖后连续读取返回写入值，而不是再次 XOR。
6. 注意：`faultType=random` 抽到 StuckAtZero/StuckAtOne 时仍按 FR03
   永久语义执行——这是配置选择，不是 bit_flip 瞬态路径的意外。

---

## 6. 与工作簿定义的全部已知偏差

1. **触发条件“目标 Vec phys reg active、ready 且后续有 consumer read”**：
   当前只保证“目标 slot 不在 free list”（随机采样时重采样 K=32 次；
   `requireAllocated` 时可等待分配），**没有 ready 位/consumer 存在性
   的前置判定**。consumer read 与写覆盖是事后证据。
2. **FR01 字段分层**：FR01-a/b 要求 sign/exp/mant 字段语义。当前实现给出
   精确 bit 位置（`lane`/`bit_in_lane`/`field`/`bit_indices`）和 128-bit
   前后值，但不额外发 `field=sign|exp|mant` 标签；字段归属需由
   lane_width/offset + bit 位置 + workload 精度解释。
3. **FR02 子模型分层**：实现支持 a/b/c/d 四种几何，但默认（无
   `semantic_role` 提示）是 128-bit 内任意两个不同 bit（`Geometry::Any`，
   可能同 lane 也可能跨 lane），不会自动按 a/b/c/d 均匀分层。需要
   `--phys_semantic_role FR02-a|b|c|d`（或包含关键字）显式选择；这对
   F0 W1 单次注入是合理的（一次运行本来只能覆盖一个子模型）。
4. **显式 `faultMask` 只有 64 bit**（`Param.UInt64`）：通过配置无法表达
   bit 64..127 的显式 mask；随机路径可以覆盖全部 128 bit。若显式 mask 与
   `bitsToChange`/几何不符，现在 fail closed，不再静默降级。
5. **SVE >128-bit**：FR01/FR02 的故障域固定为 128-bit；AArch64
   `VecRegClass` 的 256B 后备空间不属于本模型。若未来要覆盖 SVE，需要
   单独的域参数，不能复用本模型。
6. **FR01-c “NEON 8/16/32/64-bit lane”**：lane_width 8/16/32/64 均支持，
   但 128-bit 域下 lane 数分别为 16/8/4/2；显式越界 lane offset 现在
   fail closed（修复前会随机换 lane）。
7. **修复前已存在的历史 run 可复现性**：修复前 Vec bit_flip 的随机域是
   `0..63` bit + 256B lane；修复后为 128-bit distinct 域。旧 manifest 的
   相同 seed 不再字节复现旧 bit 选择。这是修复 FR01/FR02 语义的必然代价，
   旧的 transient_bit_flip 结果不能与新结果混算。
8. **stats 语义**：修复前即使 `lane_mask==0` 也计 `numBitFlips` 和
   `numFaultsInjected`；修复后只有真正完成回写才计数，fail closed 不计。
9. **L5 证据依赖 `--chaos_propagation`**：未挂 propagation 时行为仍正确
   （只改 PRF），但没有 FSU PROP 链，gate 不可用。
10. **chain_end terminal**：瞬态终局词表为 `committed` / `overwritten` /
    `exposed_unconsumed` / `not_consumed`；`overwritten` 是 L1 containment
    （detection_layer=L1，containment_reason=phys_cell_rewritten）。
    这与 FR03 永久 cell 的 `committed|squashed|exposed_unconsumed|
    not_activated` 是不同模型，不得混用。

---

## 7. RunID 复核

`docs/gem5-fi/fsu/runids.json`（173 条）中两条均存在，字段如下：

| 字段 | `FSU-FR01-F0-W1` | `FSU-FR02-F0-W1` |
|---|---|---|
| 模型ID | FR01 | FR02 |
| 单元 | FP/SIMD PRF | FP/SIMD PRF |
| 注入位置 | VecRegClass物理寄存器存储位 | Vec PRF cell多位字段 |
| 故障类型 | 单比特翻转 | 双比特翻转 |
| 频率 | **F0** | **F0** |
| 负载ID / 名称 | **W1 / FP-ScalarProbe** | **W1 / FP-ScalarProbe** |
| 采样说明 | 每次运行只注入1次；warm-up后在本模型eligible event中均匀抽样 | 同左 |
| 预期结果/结果状态 | 待实测 / Not run | 待实测 / Not run |
| Pilot目标 / 累计目标 | 30 / 385 | 30 / 385 |

---

## 8. W1 非正式 gate 最小方案（不运行 gem5，交主 agent 执行）

### 8.1 前置

- 需要含本 diff 的 `build/ARM/gem5.opt`（CHAOSPhysReg/regfile.hh 为 C++
  改动，必须重建；按项目纪律 `-j16` 干净构建）。
- workload：`workloads/directed/w1_fp_scalar_probe`（本会话已在 host
  原生执行，exit=0，输出身份/哈希见 8.4）。
- 所有命令在 repo root `/home/sdc/gem5-fi-fsu` 下执行；同时最多 4 个
  gem5 进程。

### 8.2 FR01-F0-W1（FR01-a：FP64 lane0 单 bit）

```bash
build/ARM/gem5.opt --quiet \
  -d runs/fsu-gates/FR01-FR02-F0-W1/FR01-a/seed1 \
  configs/se/ooo_proxy.py \
  --cmd workloads/directed/w1_fp_scalar_probe --cpu O3 \
  --first_clock 10000 --max_faults 1 --rng_seed 1 \
  --chaos_phys --phys_mode phys --phys_reg_class vector \
  --phys_target_idx -1 --phys_require_allocated \
  --vec_lane_width 64 --vec_lane_offset 0 \
  --fault_type bit_flip --fault_mask 0x20 --bits_to_change 1 \
  --phys_semantic_role FR01-a \
  --chaos_propagation --prop_run_id FSU-FR01-F0-W1 \
  --prop_sample_run_id s1
```

- `fault_mask=0x20` = 64-bit lane0 的 bit 5（FP64 exp 字段）；代码会校验
  popcount==1 且落在定向 lane 内。
- 若先跑对照，可加 `--no-inject` 等价的无注入运行（同 workload/seed），
  用于 oracle 差分；本 gate 不要求。

### 8.3 FR02-F0-W1（两种最小变体，任选其一或都跑）

FR02-c 跨 lane（32-bit lane 0 的 bit5 + lane 1 的 bit5）：

```bash
build/ARM/gem5.opt --quiet \
  -d runs/fsu-gates/FR01-FR02-F0-W1/FR02-c/seed1 \
  configs/se/ooo_proxy.py \
  --cmd workloads/directed/w1_fp_scalar_probe --cpu O3 \
  --first_clock 10000 --max_faults 1 --rng_seed 1 \
  --chaos_phys --phys_mode phys --phys_reg_class vector \
  --phys_target_idx -1 --phys_require_allocated \
  --vec_lane_width 32 --vec_lane_offset -1 \
  --fault_type bit_flip --fault_mask 0x2000000020 --bits_to_change 2 \
  --phys_semantic_role FR02-c \
  --chaos_propagation --prop_run_id FSU-FR02-F0-W1 \
  --prop_sample_run_id s1
```

- `0x2000000020` = bit 5 和 bit 37，32-bit lane 下分别是 lane0/lane1，
  跨 lane；代码校验 popcount==2 且至少两个 lane。

FR02-d 定向 64-bit lane 内 exp+mant 跨字段（同样 bit 5/37，均在 lane0）：

```bash
build/ARM/gem5.opt --quiet \
  -d runs/fsu-gates/FR01-FR02-F0-W1/FR02-d/seed1 \
  configs/se/ooo_proxy.py \
  --cmd workloads/directed/w1_fp_scalar_probe --cpu O3 \
  --first_clock 10000 --max_faults 1 --rng_seed 1 \
  --chaos_phys --phys_mode phys --phys_reg_class vector \
  --phys_target_idx -1 --phys_require_allocated \
  --vec_lane_width 64 --vec_lane_offset 0 \
  --fault_type bit_flip --fault_mask 0x2000000020 --bits_to_change 2 \
  --phys_semantic_role FR02-d \
  --chaos_propagation --prop_run_id FSU-FR02-F0-W1 \
  --prop_sample_run_id s1
```

### 8.4 预期事件与 oracle

事件流文件：`<outdir>/prop_evt.txt.gz`。

FR01 期望：

1. 恰好 1 个 `fault_applied` 根（L0）：
   `model_id=FR01`, `freq=F0`, `reg_class=vec`, `phys_reg=<idx>`,
   `reg_generation=<gen>`, `lane_width=64`, `lane_offset=0`,
   `bit_indices=5`, `lane_mask=0x20`, `before!=after`
   （bit5 翻转），`full_before/full_after` 为 128-bit 全值。
2. 至少 1 个 `carrier_state`（L1，parent=根）。
3. 若 cell 被 consumer 读取：`operand_read`（L2），带真实
   `dyn_inst_seq`/`consumer_seq`/`arch_reg`/`reg_generation`。
4. 若该 consumer 真正 commit：`commit`（L5，`detection_layer=L5`,
   `outcome=errant_commit`，parent=对应 `operand_read`）。
5. 若先发生真实写覆盖：`overwrite`（`detection_layer=L1`, `contained=1`,
   `containment_layer=L1`, `containment_reason=phys_cell_rewritten`），
   之后不得再有目标 bit 的重新施加。
6. `chain_end` 一次，terminal ∈
   `committed|overwritten|exposed_unconsumed|not_consumed`。

FR02 期望：同上，但根事件 `model_id=FR02`、`bit_indices` 必须恰好两个
不同位置（如 `5,37`）、`fault_mask` popcount=2；跨 lane 变体两个
`lane` 不同；跨字段变体两个 `field` 不同且定向 64-bit lane 内。
**不得**出现只含 1 个 bit 的 `fault_applied`；若出现，即 FR02
碰撞回归，直接判 gate 失败。

链审计（真实运行后执行）：

```bash
python3 tools/fsu_chain_check.py \
  runs/fsu-gates/FR01-FR02-F0-W1/FR01-a/seed1/prop_evt.txt.gz \
  --run-id FSU-FR01-F0-W1 --sample-run-id s1
```

期望 JSON：`fault_count=1`，`admitted_faults` 包含该 fault，
`truncated=false`，`identity_violations=[]`，无 `orphan_parent`；
terminal 为 `full`（有真实 L5 commit）或 `contained_L1`（写覆盖），
`beyond` 分别为 `N/A`。若只有 L2 读取而无 commit/覆盖，则为
`provable_to_L2_then_unknown`，**不算 gate 通过**（说明 workload 太短或
注入点太晚）。

oracle（`w1_fp_scalar_probe` 原生真实输出，2026-11-04 本会话执行）：

```
W1REP=1
NP=32
OPS32=20608
OPS64=20608
ARRAYHASH32=ffe18c8279bf419d
ARRAYHASH64=9b0aad0f5e039018
FPSRHASH=74d3440506066d93
ARRAYHASH=ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183
ULP=0 ULPMAX=0 BITMISMATCH=0 FPSRMISMATCH=0 FPCRMISMATCH=0
FIRSTDIFF=none
DONE
```

gate 判定建议（非正式）：

- **链证据必须存在**：根 + carrier + （L2 读 或 L1 覆盖）+ 终局。
- **oracle 分类**：
  - 写覆盖先于读取 / 无 consumer → `Masked`（contained_L1）。
  - 有 consumer 且 commit、workload 自身 `BITMISMATCH/ARRAYHASH` 变化 →
    `SDC`。
  - 有 consumer commit 但 workload 输出不变 → 仍需按 L5 证据与 oracle
    分别记录，不得仅由哈希不变推断 Masked。
- 非正式 gate 不要求 3 seed、不写 runids.json、不宣称正式认证。

---

## 9. 本次真实执行的验证

命令与结果（host，非 gem5）：

```bash
g++ -O0 -std=c++17 -Wall -Wextra -Werror \
  -I CHAOS/gem5/src/cpu/o3/CHAOSPhysReg \
  tests/unit/chaos_vec_transient_test.cc -o /tmp/chaos_vec_transient_test \
  && /tmp/chaos_vec_transient_test
```

真实输出（节选，完整 36 项全部 PASS）：

```
PASS FR01 single-bit: only target bit changes
PASS FR01 non-target lanes/bytes unchanged
PASS FR01 overwrite terminates the transient
PASS FR01 overwrite: reads return the written value, not the flip
PASS FR01 no permanent/stuck re-apply on later reads
PASS FR02 two bits are always distinct
PASS FR02 collision in explicit mask rejected (fail closed)
PASS FR02 insufficient lane width rejected (fail closed)
PASS FR02 out-of-range lane rejected (fail closed)
PASS FR02 explicit two-bit mask has two distinct identities
PASS FR02 cross-lane geometry is in-range and only target bits change
PASS FR02 cross-field geometry uses two 32-bit fields
PASS FR02 cross-field inside a directed 64-bit lane
PASS FR02 adjacent geometry: distance exactly 1 in one lane
PASS FR02 non-adjacent geometry: distance >= 2 in one lane
PASS 128-bit boundary bit 127 is addressable
ALL TRANSIENT CHECKS PASSED
```

pytest 包装与既有回归：

```bash
python3 -m pytest -q tests/test_chaos_physreg_transient_cpp.py \
  tests/test_chaos_physreg_generation_cpp.py tests/test_chaos_vec_stuck_cpp.py
# 11 passed
```

```bash
python3 -m pytest -q "tests/test_fsu_f0_readiness.py::test_prf_generation_evidence_is_pinned"
# 1 passed
```

已知与本 diff 无关的失败：`tests/test_fsu_f0_readiness.py::
test_fq08b_count_precedes_victim_application` 因工作树中其他会话的
CHAOSIQ 未提交修改而失败（该文件不在本任务允许修改范围），本 diff 未触碰
CHAOSIQ。

---

## 10. 修改文件清单

| 文件 | 变更 |
|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/chaos_vec_transient.hh` | 新增纯模型：distinct bit 选择、几何校验、128-bit 应用、瞬态 cell |
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh` | 新增瞬态状态/方法声明 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc` | BitFlip 瞬态路径、事件发射、覆盖/consumer/L5 观察、fail closed |
| `CHAOS/gem5/src/cpu/o3/regfile.hh` | 新增 `noteTraceOverwrite()`（Vec 裸指针写覆盖时冻结读计数） |
| `tests/unit/chaos_vec_transient_test.cc` | 新增 FR01/FR02 host 单测 |
| `tests/test_chaos_physreg_transient_cpp.py` | 新增编译/运行 + 静态接线检查 |
| `docs/gem5-fi/fsu/FR01-FR02-F0-AUDIT.md` | 本文档 |

---

## 11. 真实 gem5 W1 gate 结果（2026-11-04，主 agent）

证据目录：`runs/fsu-gates/FR01-FR02-F0-W1/`（不计 519，不是正式 seed）。

| gate | 关键事件 | 结果 |
|---|---|---|
| FR01-a（单 bit，64-bit lane0 bit5） | `fault_applied`（model=FR01, phys_reg=1, gen=1, bit_indices=5, before=0x0, after=0x20）→ `carrier_state` → `overwrite`（L1, contained=1, reason=phys_cell_rewritten, gen=2）→ `chain_end(overwritten)` | PASS（seed2） |
| FR02-c（两个不同 bit，bits 5+37） | `fault_applied`（model=FR02, bit_indices=5,37, full_after 同时含两位）→ `overwrite`（L1，真实写覆盖）→ `chain_end(overwritten)` | PASS（seed2） |
| FR02 碰撞负例（mask 0x20 popcount=1，bits_to_change=2） | 无 `fault_applied`；日志 `VecFaultFailClosed ... reason=mask_popcount_mismatch (no injection; fault not consumed)`，exit=0 | PASS（fail closed） |

- FR01 seed1/3/4/5 的注入 cell 未被消费（terminal=`not_consumed`），保留为
  真实证据；gate 以 seed2 的 overwrite 终结链为准。
- 链审计：`fault_count=1`、`truncated=False`、`violations=[]`。
- 两个 RunID 仍未运行正式 3 seed；本 gate 不改变 519/240 计数。
