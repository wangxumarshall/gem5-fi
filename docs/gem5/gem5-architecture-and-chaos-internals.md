# gem5 架构设计与实现原理——以及 CHAOS 故障注入器的嵌入方式

> 本文讲解 gem5 仿真器的架构设计与实现原理，并以本仓库的 CHAOS 注入器为例说明"如何把一个故障注入器正确地嵌进这套架构"。
> 编制日期：2026-09-09。所有源码引用均来自本仓库 `CHAOS/gem5/`（gem5 v25.1.0.1 + CHAOS 集成层），标注文件与行号可复核。

## 1. gem5 是什么：离散事件驱动的多精度仿真平台

gem5 的本质是一个**离散事件模拟器**（DES），在此之上叠了三层内容：

1. **事件与时间系统**：全局事件队列按 tick（最小时间单位，默认 1ps）排序，`simulate()` 循环取队头事件执行。所有组件的"动作"最终都是往队列里塞事件。
2. **对象系统（SimObject）**：一切可配置组件（CPU、Cache、内存控制器、总线、注入器……）都是 `SimObject` 的子类。Python 参数类（`.py`）声明配置面，C++ 类实现行为——这是 gem5 最具特色的双语言设计。
3. **精度谱系**：同一套内存系统上可挂不同精度的 CPU 模型——AtomicSimpleCPU（功能级，每条指令一拍完成）、TimingSimpleCPU（时序近似）、MinorCPU（顺序流水线）、**O3CPU（乱序乱序流水线，周期级）**。CHAOSPhysReg 等注入器只对 O3 有意义，因为只有 O3 建模了物理寄存器堆、重命名和乱序调度这些微架构状态。

### 1.1 Python/C++ 双语言：参数系统的实现原理

以 CHAOSLSQFwd 为例（`src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py`）：

```python
class CHAOSLSQFwd(SimObject):
    type = "CHAOSLSQFwd"
    cxx_class = "gem5::CHAOSLSQFwd"          # 映射到 C++ 类
    cxx_header = "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(0.0, "Per-forwarding-event probability ...")
    structuralFault = Param.String("none", "none | byte_lane_skew | all_zero")
    ...
```

构建系统（SCons）扫描 `src/` 下的 `.py` 文件，对每个 SimObject 生成 `params/CHAOSLSQFwd.hh`（一个纯 C++ 结构体，成员与 Param 一一对应）。运行时 Python 侧实例化对象、用户脚本设置参数，`instantiate()` 阶段 C++ 构造函数拿到 `const CHAOSLSQFwdParams &p` 读走全部参数。**这套机制意味着：给 gem5 加一个 SimObject 不需要碰任何框架代码**——放好 `.py`/`.hh`/`.cc`/`SConscript` 四个文件，SConscript 里两行：

```python
SimObject('CHAOSLSQFwd.py', sim_objects=['CHAOSLSQFwd'], enums=[])
Source('CHAOSLSQFwd.cc')
```

`src/SConscript` 用 `os.walk` 自动发现。这正是 CHAOS README 说"实现为 SimObject，升级 gem5 版本也容易装"的原理。

### 1.2 一次仿真的组成

```
Python 配置脚本（如 o3_chaos_smoke.py）
  └─ System：内存范围、总线/NoC、物理内存、Workload
  └─ CPU 实例 + 各级 Cache + 互连，端口互相连接
  └─（本项目追加）注入器 SimObject，指向目标 CPU
m5.instantiate() → C++ 对象图建立 → m5.simulate() → 事件循环
```

SE（syscall emulation）与 FS（full system）是两种 Workload：SE 由 gem5 内置的 syscall 表拦截 `read/write/futex` 等，不跑真实内核；FS 走真实 bootloader→vmlinux→用户态，需要磁盘镜像、DTB。这个区别对故障注入是致命的（§4.4）。

## 2. O3CPU：gem5 乱序核的架构设计

O3CPU（`src/cpu/o3/`）按经典乱序流水线分阶段实现，**每个阶段是独立的 C++ 类，阶段间用 `TimeBuffer<T>` 通信**（`cpu.hh:532-544`）：

```
Fetch ⇄ Decode ⇄ Rename ⇄ (IEW: Dispatch→Issue→Execute) ⇄ Commit
                    │              │
                    └─ FreeList ───┤
                                   ├─ InstructionQueue（发射队列）
                                   └─ LSQ（load/store queue）
```

```cpp
// cpu.hh —— CPU 类持有各阶段实例（组合，不是继承）
Fetch fetch;        // 取指：分支预测驱动，产 ImmediateInst
Decode decode;      // 译码：接 branch 的重定向
Rename rename;      // 重命名：arch reg → phys reg，管理 FreeList
IEW iew;            // 含 Dispatch/Issue/Execute 与 LSQ
Commit commit;      // 按序提交，处理异常/冲刷
```

`TimeBuffer<TimeStruct>` 是一个**多写者多读者的时间滑窗队列**：每个阶段每拍把自己阶段的广播（重定向、空闲计数、squash 信号）写进 wire，下游阶段延迟若干拍后读到——这建模了真实流水线的段间寄存器。gem5 用它解耦各阶段，使每段可以独立发展。

### 2.1 重命名与物理寄存器堆（CHAOSPhysReg 的靶点）

Rename 阶段维护两类映射（`rename_map.hh`）：

- **arch → phys**（"提交映射" commitRenameMap）：架构寄存器当前对应的物理寄存器，按序提交后更新；
- ** speculative map**：在飞指令建立的临时映射，squash 时靠 ROB 里的 HB（history buffer）恢复。

物理寄存器堆 `PhysRegFile`（`regfile.hh`）是分 bank 的存储：`intRegFile / floatRegFile / vectorRegFile / ccRegFile` 各是一维数组，加上配套的 `PhysRegId` 表。FreeList（`free_list.hh`）管理空闲物理寄存器——**一个物理寄存器不在 free list 里 = 已分配 = 活跃**（可能仍被在飞指令当源使用），这个判据是 CHAOSPhysReg 探活的基础（free_list.hh:109-118 注释）。

O3 的关键参数（`BaseO3CPU.py`，即"乱序窗口"）：`numROBEntries=192`、`numPhysIntRegs/numPhysFloatRegs=256`、`LQEntries=SQEntries=32`。本项目的 H2 实验就扫这条轴。

### 2.2 LSQ 与 store→load 转发（CHAOSLSQFwd 的靶点）

LSQ 分 LQ（load queue）与 SQ（store queue），`lsq_unit.cc` 是单线程单元。当一条 load 的地址与 SQ 中更年轻的 store 完全重叠时，走**转发**（`lsq_unit.cc:1454` 判定 `FullAddrRangeCoverage`，:1476 进入分支），核心就是一个 memcpy：

```cpp
// lsq_unit.cc:1490（转发点，删节）
memcpy(load_inst->memData, store_it->data() + shift_amt, size);
```

真实硅里这对应 store buffer 的前递网络——method2 定位的 core179 故障通路。**转发数据不经过 cache、不经过物理寄存器堆的读端口**（消费即生产时甚至不写 PRF），所以位翻转注入器（PRF/Cache）对这条通路天然失明——这是必须做独立 LSQFwd 注入器的微架构根据。

### 2.3 内存视角：Request → MMU → 端口系统

一条访存指令的生命周期：`LSQ::executeLoad` 生成 `Request`（含 vaddr）→ MMU 翻译（`translateTiming`）→ 翻译后的 Request 送到 CPU 的 dcache_port → Cache 层级（MissQueue/MSHR）→ 内存控制器。ARM 的翻译分派在 `arch/arm/mmu.cc:1226`：

```cpp
if ((state.isStage2 && !vm) || (!state.isStage2 && !state.sctlr.m)) {
    fault = translateMmuOff(tc, req, mode, ...);   // MMU 关：直接 setPaddr(vaddr)
```

`sctlr.m` 是 SCTLR_EL1 的 MMU 使能位。**SE 模式从不打开它**——这条 if 是 SE/FS 边界的源码根源（§4.4 详述）。

## 3. CHAOS 注入器的架构：如何正确嵌入

### 3.1 三种挂载模式

仓库里的注入器按"怎么够到热路径"分三类：

**（a）自挂载（self-attach）——最常用**。C++ 构造函数里直接把 `this` 写进 CPU 的成员指针：

```cpp
// CHAOSLSQFwd.cc:54（构造函数）
cpu->lsqFwd = this;
```

`cpu.hh` 预声明 `class CHAOSLSQFwd;` 并持有裸指针（:87-90）。热路径调用点判空短路：

```cpp
// lsq_unit.cc:1506（转发 memcpy 之后）
if (cpu->lsqFwd)
    cpu->lsqFwd->corrupt(load_inst->memData, size, vaddr);
```

优点：**热路径零开销**（无注入器时一次指针判空）、不改公共接口、对 gem5 的侵入只有 hook 点那几行。CHAOSLSQFwd / CHAOSAddrPath / CHAOSPosParity / CHAOSIQ / CHAOSExMon 全走这条范式。CHAOSPTW 变体是挂在 MMU 上（`mmu->setPtwInj(this)`，table_walker.cc:1958 经 `mmu->getPtwInj()` 取回）。

**（b）参数直挂——上游 CHAOSReg/Cache/Mem 的方式**。配置脚本里 `system.chaos_reg = ...` 显式赋值，适合通用组件；缺点是每 CPU×注入器组合都要配置代码。

**（c）旁路访问器——为注入器开的受控后门**。`regfile.hh:167-177` 给本应 private 的物理寄存器表加了公开访问器：

```cpp
/** Accessors for CHAOSPhysReg ... these are the only public route. */
unsigned numIntPhysRegs() const { return intRegIds.size(); }
PhysRegIdPtr intPhysRegId(RegIndex idx) { return &intRegIds[idx]; }
```

这是"最小侵入"原则的体现：不把注入逻辑塞进 regfile，只暴露按索引取 cell 的通道。

### 3.2 注入语义的三层门控（以 corrupt() 为例）

`CHAOSLSQFwd::corrupt()` 的门控序列是全部注入器的模板（CHAOSLSQFwd.cc）：

```cpp
if (stats) stats->numHooksCalled++;        // ① 钩子被调用就计数（门控前）
if (probability <= 0.0f) return;           // ② 未配置 → 零开销返回
Cycles cur = cpu->curCycle();
if (cur < first_clock) return;             // ③ 时间窗
if (max_faults && count >= max_faults) return;
if (dist(rng) >= probability) return;      // ④ Bernoulli 抽样
// …然后才真正改数据
```

三个设计要点都来自项目踩过的坑：

- **numHooksCalled 在一切门控之前**：区分"路径没被行使"和"行使了但概率没中"。没有这个计数，D1 在 FS 早期 boot 里 `numStructuralByteLaneSkew=0` 就无法归因（注入器注释原文称之为 adversarial-review instrumentation gap）。
- **maxFaults=1 + rngSeed**：formal 实验的可复现单元——每次 run 注入恰好一个故障，seed 决定它落在哪个事件上。384 个 seed = 384 次独立单故障实验，配 golden 对照即可算 P_SDC 的 Wilson CI。
- **RNG 构造的 UB 教训**：早期 `rng(rng_seed != 0 ? rng_seed : rd())` 因成员声明顺序（`rng` 在 `rd` 前）在构造期调用了未构造的 `std::random_device` → SIGSEGV。修复为立即调用 lambda 局部构造（CHAOSPTW.cc:28 可见）。seed≠0 时才躲得过——这解释了"H5 seed 42 能跑而 H6/H7 默认 seed 0 必崩"的历史现象。

### 3.3 位级故障 vs 结构化故障：P-D1 的本质

上游 CHAOS 的故障原语是三个位级操作（对单个 byte）：

```cpp
case FaultType::StuckAtZero: data[off] &= ~mask; break;
case FaultType::StuckAtOne:  data[off] |=  mask; break;
case FaultType::BitFlip:     data[off] ^=  mask; break;
```

本项目的关键洞察是**core179 的现场签名无法用任何位翻转表达**：撕裂值是源数组的字节流循环移位（与真值汉明距离 0 的"旋转"，穷举 8 字节 × 256 掩码无命中）。因此 P-D1 扩展了独立于位级故障的**结构化故障轴**（CHAOSLSQFwd.cc:124-166）：

```cpp
case StructuralFault::ByteLaneSkew: {
    // 整字右旋 k 字节：byte lane n 拿到 data[(n+k) mod size]
    std::vector<uint8_t> tmp(data, data + size);
    for (unsigned n = 0; n < size; n++)
        data[n] = tmp[(n + k) % size];
}
case StructuralFault::AllZero:
    std::memset(data, 0, size);
```

参数面（`structuralFault`/`skewBytes`）与位级轴（`faultType`/`faultMask`）正交，结构化优先。`ptrskew_kernel` 探针在用户态复刻 `__per_cpu_offset[i]→rq` 解引用链，`byte_lane_skew rot1` 注入 30 次检出 28 次（93%），端到端复现了生产的 Oops 链——**这是"故障模型必须忠实于现场形态学"的完整闭环**。

### 3.4 read-trace 传播闭环：把"注入"变成"可解释的实验"

位翻进去之后发生了什么？既有工具只能看最终输出对不对。CHAOSPhysReg 在 `regfile.hh` 的读写热路径埋了两个计数（:218-234, :327-343）：

```cpp
// getReg 读路径：数注入值被读了几次
if (trace_type == IntRegClass && !trace_overwritten && (int)idx == trace_idx)
    ++reads_before_overwrite;
// setReg 写路径：槽位被写 = 注入值被销毁
if (trace_type == IntRegClass && (int)idx == trace_idx)
    trace_overwritten = true;
```

注意计数的语义修正史（regfile.hh:179-187 注释）：数的是**注入值**被读的次数而不是槽位被读的次数——槽位被重新分配后读的是新值，早期版本把 free-list 槽位误记为高读数。`reads_before_overwrite` + 输出 diff + 退出码，把每个故障归入四分类：**Benign（reads=0，未消费）/ Masked（被读但逻辑屏蔽）/ SDC（传播到输出）/ Crash**。这是 AVF 分析的仿真级实现——分母从"注入次数"细化到"消费与否"，比既有工具（只统计 SDC/注入）多出一层可解释性。

### 3.5 三个"通路型"注入器的 hook 位置与忠实性声明

| 注入器 | hook | 建模的通路 | 忠实性边界（源码注释里如实声明） |
|---|---|---|---|
| CHAOSLSQFwd | `lsq_unit.cc:1506`（转发 memcpy 后、packet 化前） | store buffer→load 前递数据 | 转发判定用 gem5 的 coverage 模型，非 TSV110 微架构 |
| CHAOSAddrPath | `lsq.cc:1141-1149`（`translateTiming` 前 setVaddr） | AGU 输出→MMU 输入的地址通路 | gem5 翻译发生在 `DynInst::initiateAcc` 内，注入落在**翻译后**的 effAddr（cache 访问路径），症状类别保持、流水级与硅有偏差（CHAOSAddrPath.hh 注释原话：declared as a modeling limitation） |
| CHAOSPTW | `table_walker.cc:1958`（`doLongDescriptor` 取回描述符后、判读前） | 页表走查器读出 | ARM walker 本身是简化模型，但注入点（内存中 PTE 读出）与 D3 物理位置一致 |

CHAOSPTW 的故障模式演化是"ECC 语义要精确到 ARM descriptor type"的教材案例：初版 XOR 翻 bit0 想制造 invalid PTE，但 ARM PTE 低 2 位是 descriptor type（0b01=block，0b11=table），`0b01^0x01=0b00` 才 invalid、`0b11^0x01=0b10` 仍 valid——实测 629 次注入全 benign。修复分两步：`clearValidBit`（AND `~0x3` 强制 invalid，2-bit 不可纠正、绕过 ECC，用于制造 spurious）和 `conditional_valid`（只对 0b01 描述符 XOR bit0，单 bit 使 ECC-on 纠正 / ECC-off spurious，用于忠实的 ECC on/off 对照）。**同一个注入器里两种模式分别服务"制造症状"与"对照实验"两个目的**，不能混用。

### 3.6 CHAOSPosParity：校验器也是 SimObject

PosParity 不是注入器而是**检测器原型**——回答"位置锚定校验能否捕获字节通道置换"。挂载在转发路径两端（`lsq_unit.cc:1494-1529`）：tag() 在注入前快照双加权聚合，verify() 在注入后比对。数学设计（CHAOSPosParity.hh 大段注释）：两权向量 `w1_i=2i+1`、`w2_i=(2i+1)^0x5A` 两两不同且全奇——奇性保证单 bit 翻转必被检出（`w·2^b mod 256 ≠ 0`），相异性使置换逃逸约束是非零系数超平面；双聚合在 Z/256（非域）上相交为 codim≤2。检出数字是穷举+2×10⁶ 蒙特卡洛算出的诚实值：单 bit 翻转 0 逃逸（确定性），随机数据旋转逃逸 2⁻¹²~2⁻⁵，对抗性逃逸存在（概率性，注释明说）。

## 4. 方法论层：架构理解直接决定实验有效性

### 4.1 hook 点选择 = 微架构定位

同一个"数据损坏"可以注在 cache、PRF、转发路径、内存——它们对应**不同的物理缺陷位置**。L1D 注入 97.7% SDC vs L1I 0%（错误指令被 squash/非法崩溃——取指通路自掩蔽）的悬崖，直接回答了"ECC 预算投给取数还是取指"。这正是注入点选择承载的科学含义。

### 4.2 采样偏差：确定性仿真的统计学陷阱

gem5 是确定性仿真——同 seed 同结果。hook-on-event 注入器若"窗口打开后第一个过概率门的事件"恒为同一条动态指令，384 个 seed 全部命中同一事件，统计独立性是假的（l1dfwd 384/384 全 Masked 曾因此作废）。修复：**events_to_skip 几何分布（p=0.1）**，让单故障在 eligible 事件流上均匀采样。同类陷阱还有 argparse exit=2 被分类器当 Crash、campaign 组件映射表静默改道。本项目的答案是把"工具正确性审计"本身制度化：golden 注册表 + faults 来源日志核对 + replay 5%。

### 4.3 forwarding 掩蔽定律：架构知识反过来指导注入有效性

紧循环 chase 里指针的物理寄存器生命周期只有一条 ldp——PRF 位翻转架构不可见（O3 forwarding 直接传递生产者结果，物理 cell 无读者，readtrace reads=0 佐证）。这条**从仿真架构本身推导出的定律**解释了为何 method2 的 PRF 臂必须在 FS 内核态跑（内核指针使用模式的依赖距离更长），也修正了"physreg 保护"的优先级评估。

### 4.4 SE/FS 边界：mmu.cc:1226 的一行 if 决定实验有无意义

`!state.sctlr.m → translateMmuOff`（直接 `setPaddr(vaddr)`）：SE 模式下**页表走查器从不运行**。后果：CHAOSPTW 钩子恒 0 注入、CHAOSAddrPath 的 byte7 清零后地址仍落 512MiB 物理范围不 fault。项目早期 H6/H7 的 SE null 结果差点被当成"注入器无效"，实为**仿真模式伪迹**——FS 模式（SCTLR.M=1）下 D2 `numAddrFaults=20`、D3 `numFaultsInjected=7963` 立即非零。教训已写进 mspc_paper：仿真实验的 null 结果必须先排除环境几何伪迹。配套工程方案是 Atomic 快速 boot → `m5 checkpoint` → O3 restore，绕开 FS 启动的 wall-time 代价。

### 4.5 clock 语义与事件密度

注入器用 `cpu->curCycle()` 门控时间窗，但 CHAOSMem 曾因 `tickToClockRatio=1000`（1GHz 假设）在 2.6GHz 配置下把窗口推到仿真总长之外——384 次全 Inactive。walk 密度（`numHooksCalled`）则回答"这个通路有没有被行使到值得注入"：FS 内核态启动期 PTW walk 密度仅 0.069%，早期 boot 0.0066%——概率参数必须按实测密度定标，否则期望注入次数算不出来。

## 5. 一图总览

```
┌─────────────────────── gem5 事件驱动内核（tick 队列）──────────────────────┐
│                                                                            │
│  Python 配置层 ──SCons 生成 params──► C++ SimObject 图                      │
│   (o3_chaos_smoke.py)                     │                                │
│        │ 挂载                             │                                │
│        ▼                                  ▼                                │
│  ┌───────────── O3CPU（cpu.hh 组合各阶段）──────────────┐                   │
│  │ Fetch→Decode→Rename→IEW→Commit   ⟨TimeBuffer 通信⟩   │                   │
│  │   │           │        │        │                     │                  │
│  │   │      FreeList◄──PhysRegFile◄─┼─┐                 │                   │
│  │   │           （regfile.hh）      │ │                 │                   │
│  │   │      ┌────CHAOSPhysReg 注入+read-trace（b/c 旁路访问器）              │
│  │   ▼      ▼                           │             │   │                │
│  │  LSQ::executeLoad ──► LSQUnit 转发 memcpy ──► load data                  │
│  │   │  │                    │   │  │        │                             │
│  │   │  └CHAOSAddrPath◄──────┘   └tag─┤      └corrupt──► CHAOSLSQFwd       │
│  │   │   (lsq.cc:1146,              verify（PosParity）   （结构化 P-D1）   │
│  │   │    translateTiming 前)                                      │            │
│  │   ▼                                                              │           │
│  │  MMU::translateTiming ─► ARM TableWalker::doLongDescriptor       │           │
│  │                              └──► CHAOSPTW（PTE 读出后）          │           │
│  │        SE: sctlr.m=0 → translateMmuOff（PTW 永不走）◄─ 实验有效性边界     │
│  └──────────────────────────────────────────────────────────┘                │
└────────────────────────────────────────────────────────────────────────────┘
```

## 6. 延伸阅读（仓库内）

- `CHAOS/README.md` — 上游 CHAOS 四模块的参数文档
- `fi_research/EXPERIMENT_DESIGN.md` — H0–H4 实验设计（§2.1 故障四分类、read-trace 闭环）
- `docs/cases/core179-microarch-rootcause-synthesis/FI_DESIGN_SUPPLEMENT.md` — P-D1/D2/D3 设计与 SE/FS 边界的完整实证记录
- `docs/gem5/project-understanding.md` — 本项目全景（研究主线与定量结论）
- `src/cpu/o3/`、`src/arch/arm/` — 本文引用的全部源码
