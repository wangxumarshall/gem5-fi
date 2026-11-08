# gem5 Item Description

## 目录

- [PCStateBase](#pcstatebase)
- [BAC](#bac)
- [BPU](#bpu)

## PCStateBase

`PCStateBase` 定义在 `CHAOS/gem5/src/arch/generic/pcstate.hh`，是 gem5 对“程序计数器状态”的通用抽象。它不是只保存一个 `PC` 地址的简单结构，而是 CPU 前端、解码器、分支预测器、异常处理、checkpoint/restore 之间共同传递的“下一条要执行哪里”的完整状态容器。

最核心的两个字段是：

- `_pc`：当前宏指令的指令地址，也就是 `instAddr()` 返回的地址。
- `_upc`：micro PC，用来表示一个 macro-op 内部当前执行到第几个 micro-op。普通 RISC 指令通常一直是 0；x86 这类会把复杂指令拆成多个 micro-op 的 ISA 会更依赖它。

`PCStateBase` 本身是抽象基类，因为不同 ISA 对 PC 状态的需求不同。gem5 的通用 CPU 流水线只需要知道“当前指令地址是什么”“怎样复制/更新/序列化”“怎样推进到下一条”“是否发生控制流跳转”；至于 ARM 的 Thumb/AArch64 状态、IT block 状态，RISC-V 的 compressed 指令长度和 vector 配置，MIPS/Power 的 delay slot 等，都由各 ISA 自己的派生类保存。

### 通用接口

`PCStateBase` 提供的是跨 ISA 的最小共同接口：

- `instAddr()`：取当前指令的内存地址。
- `microPC()`：取当前 micro-op 编号。
- `set(Addr)`：把 PC 强制设到某个地址，并重置 micro PC。
- `advance()`：推进到下一条指令或下一个 PC 状态，由派生类实现。
- `branching()`：判断当前 PC 状态是否表示发生了控制流改变，由派生类实现。
- `clone()`：多态复制。因为调用方通常只拿到 `PCStateBase&`，但实际对象可能是 `ArmISA::PCState`、`RiscvISA::PCState` 等。
- `update()` / `equals()`：多态更新和比较。
- `serialize()` / `unserialize()`：保存和恢复 checkpoint。
- `as<T>()`：在已知真实 ISA 类型时，把 `PCStateBase` 向下转型成具体 PCState 类型。

这里的 `as<T>()` 很重要，但也要小心：它只是 `static_cast`，不会做运行时检查。只有当调用方确定底层对象真的是目标类型时才安全。例如 CHAOSBPU 在 BAC 预测 hook 里把 `PCStateBase` 当成 `GenericISA::PCStateWithNext` 使用，是因为该路径需要访问 `npc()` 这类 next-PC 字段。

### PCStateWithNext

`PCStateBase` 下面最常见的通用派生类是 `GenericISA::PCStateWithNext`。它在 `_pc/_upc` 之外增加：

- `_npc`：next PC，下一条宏指令地址。
- `_nupc`：next micro PC，下一个 micro-op 编号。

因此它描述的是一个二元状态：当前在哪里，以及自然推进后应该到哪里。打印格式大致是：

```text
(pc=>npc)
```

比如固定 4 字节指令宽度的简单 ISA，`pc=0x1000, npc=0x1004` 表示顺序执行；如果分支预测或分支解析把 `npc` 改成 `0x2000`，`branching()` 就会认为这里发生了控制流跳转。

### 常见派生形态

`pcstate.hh` 里提供了几类通用模板：

- `SimplePCState<InstWidth>`：固定指令宽度，没有 delay slot。`advance()` 执行 `pc = npc; npc += InstWidth`。
- `UPCState<InstWidth>`：在 `SimplePCState` 基础上支持 micro PC。macro-op 内部可以只推进 `upc/nupc`，最后再推进宏指令 PC。
- `DelaySlotPCState<InstWidth>`：支持 delay slot，因此除了 `pc/npc` 还要有 `nnpc`。
- `DelaySlotUPCState<InstWidth>`：同时支持 delay slot 和 micro PC。

ISA 具体实现会继承这些通用形态。例如：

- `ArmISA::PCState` 继承 `GenericISA::UPCState<4>`，但额外保存 Thumb/AArch64 标志、IT state、指令大小、debug step 等状态。ARM 的 `set()` 会根据 Thumb 状态设置 `npc = pc + 2` 或 `pc + 4`。
- `RiscvISA::PCState` 也继承 `GenericISA::UPCState<4>`，但会记录 compressed 指令状态，因此 `branching()` 不能简单写死 `pc + 4`，而要看当前指令大小是 2 还是 4。

这也是为什么 O3 前端不能只传一个 `Addr`：一个地址不足以表达 ISA 模式、micro-op 位置、delay slot、下一 PC、调试状态等信息。

### 在 O3CPU 中怎么用

O3CPU 里 PCState 的生命周期大致是：

1. ThreadContext/SimpleThread 保存架构态 PC。
2. Fetch 阶段从线程 PC 开始取指，并维护自己的 speculative `pc[tid]`。
3. 每条被 Fetch 构造出来的 `DynInst` 都保存一份当前 `PCStateBase`，作为这条指令的 PC 快照。
4. BAC 或 BPU 根据当前指令更新 predicted target，把预测结果写到 `DynInst` 的 `predTarg` / `predTaken`。
5. Decode/Commit 如果发现预测目标或方向错，就通过 backward time buffer 发 squash，把正确的 `PCStateBase` 传回前端。
6. 前端收到 squash 后用这个 PCState 重置 Fetch/BAC 的 speculative PC。

因此，同一个程序点会同时存在多份 PCState：

- 线程架构态 PC：已经提交、真实可见的执行位置。
- Fetch speculative PC：前端当前正在沿预测路径取指的位置。
- BAC 的 `bacPC[tid]`：解耦前端中，BPU/BAC 独立向前跑的预测 PC。
- DynInst 内部 PC：某条动态指令被取到时的 PC 快照。
- predicted target PC：这条指令被预测执行后应该去的 PC。

这些状态不能互相混用。架构态 PC 要保守，speculative PC 可以走错；`DynInst` 的 PC 是历史快照，Fetch/BAC 的 PC 是流动游标。

### 在 BAC 中的角色

BAC 的核心工作就是不断读写 `PCStateBase`：

- 解耦前端开启时，BAC 持有每线程一个 `bacPC[tid]`，它跑在 Fetch 前面。
- `generateFetchTargets()` 从 `bacPC[tid]` 开始，用 BTB 搜索潜在分支。
- 如果 BTB 命中，BAC 调用 BPU 预测，BPU 会修改传入的 PCState，把预测后的下一 PC 写进去。
- BAC 把 start PC、end PC、predicted PC 封装进 `FetchTarget`，插入 FTQ。
- Fetch 消费 FTQ 后，在预解码真实指令时调用 `updatePC()`，用真实指令信息校准预测历史。
- 如果 Fetch/Decode/Commit 发来 squash，BAC 用正确的 `PCStateBase` 重置 `bacPC[tid]`，清空 FTQ，并回滚 BPU speculative history。

一句话说，BAC 用 `PCStateBase` 表示“预测流当前走到哪里”和“下一个 fetch target 应从哪里开始”。

### 和 StaticInst/DynInst 的关系

`StaticInst` 是静态指令描述，知道一类指令如何推进 PC。例如普通非分支指令的 `advancePC(pc)` 会把 PC 推进到顺序下一条；PC-relative branch 的 `branchTarget(pc)` 会基于当前 PC 算目标地址。

`DynInst` 是某次执行中的动态指令实例，它持有：

- 当前指令的 PCState 快照。
- 预测目标 `predTarg`。
- 预测方向 `predTaken`。

Decode 阶段会用 `inst->branchTarget()` 重新计算直接分支的真实目标，并和 `readPredTarg()` 比较。如果不同，就说明前端预测目标错了，需要 squash。

### 为什么有一组 `set()` 辅助函数

`PCStateBase` 是多态对象，很多地方用 `std::unique_ptr<PCStateBase>` 保存。直接赋值会切片，也不知道真实派生类型。因此 `pcstate.hh` 提供了一组 `set()` helper：

- 目标已有对象时，用 `update()` 原地更新。
- 目标为空但源存在时，用 `clone()` 复制出正确派生类型。
- 源为空时，把目标清空。

这样既避免对象切片，又减少了频繁释放/重新分配。

### 容易误解的点

- `instAddr()` 不是“下一条 PC”，它是当前指令地址。下一条通常在 `npc()` 或 ISA 具体字段里。
- `PCStateBase::set(addr)` 会重置 micro PC。对 macro-op 中间状态使用它要小心。
- `branching()` 不是问“这条静态指令是不是分支”，而是问“当前 PC 状态是否偏离顺序推进”。例如 RISC-V compressed 指令的顺序推进可能是 `pc + 2`。
- `PCStateBase` 不负责预测对错。它只是状态载体；预测由 BPU/BAC 做，验证由 Decode/Commit 等阶段做。
- `as<T>()` 不做类型检查。跨 ISA 通用代码最好只依赖 `PCStateBase` 接口，只有 ISA 代码或明确知道底层类型的代码才向下转型。

### 总结

`PCStateBase` 是 gem5 里“PC 不是一个裸地址”的体现。它把当前指令地址、micro-op 位置、下一 PC、ISA 模式、delay slot 或 compressed 指令等信息统一封装起来，让 O3CPU 的通用流水线可以用同一套接口处理不同 ISA 的取指、预测、重定向、异常和 checkpoint。

## BAC

`BAC`（Branch and Address Calculation）定义在
`CHAOS/gem5/src/cpu/o3/bac.hh` 和 `bac.cc`，是 O3CPU 前端中负责“分支预测协同”和“下一条 PC 计算”的阶段。它连接 Fetch、BPU、FTQ 以及 Decode/Commit 发回的 squash 信号。

### 两部分职责

BAC 的实现可以分成两部分：

- **分支预测协调**：管理 BPU 的预测调用、预测历史更新和 squash。在解耦前端开启时，BAC 独立运行，使用 BPU/BTB 生成 fetch target 并写入 FTQ。
- **PC 计算**：Fetch 对每条预译码指令调用 `updatePC()`，BAC 根据指令类型和预测结果更新 Fetch 的 `PCStateBase`。非解耦前端中，这部分与 Fetch 紧密同步。

### 解耦前端路径

启用 `decoupledFrontEnd` 后，BAC 不再等待 Fetch 发现分支才进行预测，而是通过 `generateFetchTargets()` 主动沿 BTB 搜索分支：

1. BAC 从每个线程的 `bacPC[tid]` 开始搜索潜在分支。
2. BTB 命中后，BAC 调用 BPU 预测方向和目标地址。
3. BAC 将起始 PC、结束 PC 和预测后的 PC 封装为 `FetchTarget`。
4. `FetchTarget` 插入 FTQ，由 Fetch 消费并从 I-cache 取指。
5. Fetch 预译码后通过 `updatePreDecode()` 将真实分支信息和序列号补回 BPU 历史。

这种结构把 BPU 的预测工作与 Fetch 的取指工作分开，可以缩短前端关键路径，并支持由 BPU 引导的目标预取。其代价是需要维护 FTQ、BAC speculative PC 和 BPU speculative history 的一致性。

### Squash 和预测历史

当 Decode 或 Commit 发现分支方向、目标地址或指令类型预测错误时，BAC 会：

- 使用正确的 `PCStateBase` 重置 `bacPC[tid]`；
- 清空或回滚 FTQ 中尚未消费的 fetch target；
- 调用 BPU 的 squash 接口回滚年轻的预测历史；
- 通过时间缓冲区向 Fetch 传递前端重定向信息。

因此，BAC 不是另一个独立的分支预测器，而是 BPU 与 O3 Fetch 之间的协调阶段。`PCStateBase` 负责承载 PC 状态，BPU 负责产生预测，BAC 负责把预测组织成可供 Fetch 消费的地址流。

### 与 CHAOSBPU 的连接

本仓库的 `CHAOSBPU` 通过 `BAC::predict()` 接入预测路径。调用顺序是先执行
`bpu->predict()`，再由 CHAOSBPU 对预测结果进行可选扰动：

- `target_sub`：将预测目标替换为合法的 fall-through 目标；
- `direction_flip`：翻转 BPU 返回的 taken/not-taken 结果。

该 hook 位于解耦前端的 BAC 预测路径，使用时需要确认配置确实启用了对应的 decoupled front-end 路径。

## BPU

`BPU`（Branch Predictor Unit）在 gem5 中由
`CHAOS/gem5/src/cpu/pred/bpred_unit.hh` 的 `branch_prediction::BPredUnit` 表示。它是一个包装层，统一持有方向预测器、BTB、RAS、间接分支预测器等分支预测组件，并向 O3 前端提供预测和恢复接口。

### 核心接口

`BPredUnit` 的主要接口包括：

- `predict()`：根据静态分支指令和当前 PC，预测 taken/not-taken，并在需要时写入预测目标；
- `update()`：提交已经确认的较老预测历史；
- `squash()`：回滚错误路径上的预测历史，并可用正确目标和真实方向修正分支；
- `BTBValid()`、`BTBLookup()`：查询 BTB 是否命中以及命中的预测目标；
- `BTBUpdate()`：用已经解析出的真实分支目标更新 BTB；
- `branchPlaceholder()`：在解耦前端中为未被初始 BPU 检出的分支创建占位预测历史。

### BPU 与前端的两种连接方式

- **Coupled front-end**：Fetch 预译码发现分支后直接调用 BPU，BPU 为该动态分支建立预测历史；预测结果随 Fetch 的指令流进入流水线。
- **Decoupled front-end**：BAC 根据 BTB 预先搜索分支并调用 BPU，生成的 fetch target 进入 FTQ；Fetch 后续预译码时再把真实指令和序列号与预测历史关联起来。

BPU 的预测历史是 speculative state，不等同于已经提交的架构状态。错误路径上的历史必须在 squash 时回滚，正确路径上的历史则在分支提交后通过 `update()` 固化。

### BPU、BTB、RAS 的关系

- **方向预测器**决定条件分支是否 taken。
- **BTB**保存分支 PC 到目标 PC 的快速映射，尤其用于前端尚未完成完整译码时的目标搜索。
- **RAS**为函数调用和返回提供返回地址预测。
- **间接分支预测器**处理目标地址不能由简单 PC-relative 规则直接得到的分支。

`BPredUnit` 将这些组件组合成统一接口，但它本身不负责取指，也不负责最终判断预测是否正确。预测验证发生在 Decode/IEW/Commit 等流水阶段，错误预测通过 squash 反馈给 BAC 和 BPU。

### 与 CHAOSBPU 的关系

`CHAOSBPU` 定义在
`CHAOS/gem5/src/cpu/o3/CHAOSBPU/CHAOSBPU.hh`，不是替代 gem5 原有 BPU 的新预测器，而是挂在 `BAC::predict()` 后面的故障注入器。它修改的是已经产生的 speculative 预测结果：

- 目标替换影响 `PCStateWithNext` 中的预测 next PC；
- 方向翻转影响 `predict()` 返回的 taken 状态；
- 错误预测通常会被后续分支解析检测并 squash，因此该模块主要用于观察分支预测路径和负对照行为。
