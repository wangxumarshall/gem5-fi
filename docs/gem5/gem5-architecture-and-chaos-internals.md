# 深入理解 gem5 及 CHAOS 架设计与源码实现

> 本书以《深入理解 Linux 内核》的方式讲解本仓库的仿真器与故障注入体系：先建立全局模型，再逐层下潜到真实源码，每个论断都给出 `文件:行号` 供复核。
> 基线：gem5 v25.1.0.1（commit 62c7bf28，见 `CHAOS/gem5_base_version.md`）+ CHAOS 集成层（19 个注入器模块）。
> 编制日期：2026-09-10。所有引用均来自本仓库 `CHAOS/gem5/` 与仓库根的工具/配置层。

---

## 第一章 总论：gem5 是一个离散事件仿真内核

理解 gem5 的正确起点不是"CPU 模拟器"，而是"**离散事件仿真内核（DES）+ 一棵 SimObject 对象树**"。CPU、Cache、总线、内存、故障注入器，全都只是挂在这棵树上的"事件生产者"。本章先看内核本身——它相当于 Linux 内核里的调度器与中断子系统：一切上层行为最终都还原为它的基本操作。

### 1.1 一次仿真的顶层控制流

Python 侧的 `m5.simulate()` 直接进入 C++ 的 `simulate()`（`src/sim/simulate.cc:190`）。它做四件事：

1. 安装 SIGINT/SIGCONT 处理器（`simulate.cc:195-196`）；
2. 为多事件队列模式创建 `SimulatorThreads`（`simulate.cc:205-206`，类定义 `:68-168`）；
3. 若用户给了周期上限，调 `set_max_tick()` 挂一个 `GlobalSimLoopExitEvent`（`simulate.cc:213-224`，`set_max_tick` 定义 `:257-265`）；
4. 进入主循环 `doSimLoop(mainEventQueue[0])`（`simulate.cc:238`）。

`doSimLoop`（`simulate.cc:292-346`）是整个仿真器的心跳，值得逐行读：

```cpp
Event *
doSimLoop(EventQueue *eventq)
{
    curEventQueue(eventq);                    // 每线程的当前队列指针
    eventq->handleAsyncInsertions();          // 合并其它线程投递的异步事件

    bool mainQueue = eventq == getEventQueue(0);

    while (1) {
        assert(!eventq->empty());
        assert(curTick() <= eventq->nextTick() &&   // 事件不能被调度到过去
               "event scheduled in the past");

        if (mainQueue && async_event) { ... }  // stat dump / IO / 退出等异步服务
        Event *exit_event = eventq->serviceOne();   // 取队头事件并执行
        if (exit_event != NULL)
            return exit_event;                 // 唯一的出口：退出事件
    }
}
```

注意与 Linux 内核 `while (1) schedule()` 主循环的同构性：**循环体只做一件事——取下一个事件、执行它**。时间的前进不是连续的，而是 `serviceOne()` 内部一步跳到事件时刻：

```cpp
// src/sim/eventq.cc:224 起（节选）
EventQueue::serviceOne()
{
    std::lock_guard<EventQueue> lock(*this);
    Event *event = head;
    ...
    if (!event->squashed()) {
        setCurTick(event->when());   // ← 时间直接跳到事件时刻
        event->process();            // ← 多态分发：全世界所有的"行为"都在这里发生
        if (event->isExitEvent())
            return event;
    }
    ...
}
```

`curTick` 从此只增不减（除非 checkpoint 回退）。**gem5 里没有"线程"在跑程序——只有事件链在互相触发**。一条 O3 指令的执行、一次 DRAM 刷新、一个注入器的攻击，全是 `process()` 虚函数的一次调用。

### 1.2 时间系统：Tick 与事件优先级

`Tick` 是 64 位最小时间单位（默认 1ps，`src/base/types.hh`）。但仅有时刻不足以确定同拍事件的执行顺序，所以 `EventBase`（`src/sim/eventq.hh:99`）定义了第二维——**优先级**（`eventq.hh:126-244`）。这张表是理解 gem5 行为次序的关键，值得像背内核中断优先级一样背下来：

| 优先级常量 | 值 | 含义 |
|---|---|---|
| `Debug_Enable_Pri` | -101 | 开 trace，必须最先 |
| `Debug_Break_Pri` | -100 | 断点 |
| `CPU_Switch_Pri` | -31 | CPU 切换须先于任何 tick |
| `Delayed_Writeback_Pri` | -1 | 延迟写回 |
| `Default_Pri` | 0 | 缺省 |
| `DVFS_Update_Pri` | 31 | 电压频率更新（先于统计 dump） |
| `Serialize_Pri` | 32 | checkpoint 序列化 |
| `CPU_Tick_Pri` | 50 | **CPU 周期事件**——在写回等关联事件之后 |
| `CPU_Exit_Pri` | 64 | 线程退出 |
| `Stat_Event_Pri` | 90 | 统计 dump/reset |
| `Progress_Event_Pri` | 95 | 进度心跳 |
| `Sim_Exit_Pri` | 100 | 仿真退出，永远最后 |

一个直接后果：**O3 CPU 的周期事件用 `CPU_Tick_Pri`（50）注册**（`src/cpu/o3/cpu.cc:76`：`tickEvent([this]{tick();}, "O3CPU tick", false, Event::CPU_Tick_Pri)`），所以同一 tick 内，缓存写回（Default_Pri=0）先于 CPU 下一拍执行——这保证了 CPU 在下一拍读到的是本拍已完成的状态。第七章会看到，注入器的"时间窗"若用错时间域（tick vs cycle），正是被这个双时间轴咬伤的。

### 1.3 事件队列的数据结构

`EventQueue`（`eventq.hh:615`）的队列不是堆，而是**链表的链表**（`eventq.hh:258-269` 注释）：外层 `nextBin` 按 `(when, priority)` 排序的 bin 串，内层 `nextInBin` 是同 bin 事件的 LIFO 栈。`schedule()`（`eventq.hh:757-782`）插入时线性找 bin、常数入栈；`serviceOne()` 出队是常数操作。这个设计换来了**确定性**：同 seed 下事件执行顺序严格可复现——这是本仓库全部 384-seed 统计方法的存在前提（第七章 §7.4）。

多队列并行模式（`numMainEventQueues > 1`）下，跨队列调度走 `async_queue`，在每个 `simQuantum` 边界由 `handleAsyncInsertions()` 合并（`eventq.hh:604-613` 注释、`simulate.cc:226-235`），以量子同步换取确定性——类比内核的 tick 间中断合并。本仓库全部实验为单队列，不展开。

### 1.4 SimObject：一切组件的基类

`SimObject`（`src/sim/sim_object.hh:146`）多重继承了五个角色，每个角色对应一块框架设施：

```cpp
class SimObject : public EventManager,        // 拥有事件队列访问（schedule/deschedule）
                  public Serializable,        // checkpoint 序列化
                  public Drainable,           // drain 协议（切 CPU/存盘前排空）
                  public statistics::Group,   // 统计树
                  public Named                // 名称
```

生命周期由 `sim_object.hh:72-89` 的注释明确规定，而驱动它的是 Python 侧 `instantiate()`（`src/python/m5/simulate.py:220-241`）里的 `_create_cpp_objects()`（`simulate.py:147-213`）——注意它对整棵对象树做的**六遍扫描**（先序深度优先，父先于子）：

```
第1遍  createCCObject()    C++ 构造（参数从 Params 结构体读入）
       connectPorts()      端口绑定（内存系统拓扑成型）
第2遍  init()              依赖全图的初始化
第3遍  regStats()          统计注册
第4遍  regProbePoints()    探针点注册
第5遍  regProbeListeners() 探针监听连接
第6遍  initState()/loadState()  冷启动 / checkpoint 恢复
之后（首次 simulate() 时，simulate.py:254-258）：
       startup()           仿真即将开始——注入器在这里把 cycle 域快照成 tick 域
```

**这张时刻表是注入器的宪法**：构造函数里只准读参数、挂指针；`startup()` 里才准触碰全局时间（第七章 §7.6 的 D1/D4 陷阱正是违反/遵守它的正反案例）。

### 1.5 双语言架构：Python 配置面，C++ 行为面

gem5 最具特色的设计：每个 SimObject 有一个 Python 参数类（`.py`）和一个 C++ 实现类，SCons 扫描 `.py` 生成纯 C++ 的 `params/<Name>.hh` 结构体。以本仓库的 CHAOSLSQFwd 为例（`src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py`）：

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

运行时链路：配置脚本 `CHAOSLSQFwd(cpu=cpu0, probability=...)` → Python 对象入树 → `createCCObject()` 时生成的 `create()` 调 C++ 构造函数 `CHAOSLSQFwd(const CHAOSLSQFwdParams &p)`（`sim_object.hh:103-125` 注释详解了三种 create 约定）→ 构造函数把 `p.probability` 等读进成员。

构建侧的关键在 `src/SConscript:570`：`for root, dirs, files in os.walk(base_dir, ...)` 递归发现所有 `SConscript`。因此**给 gem5 加一个 SimObject 不需要碰任何框架代码**——放好 `.py`/`.hh`/`.cc`/`SConscript` 四个文件即可，SConscript 只需两行（`src/cpu/o3/CHAOSLSQFwd/SConscript`）：

```python
SimObject('CHAOSLSQFwd.py', sim_objects=['CHAOSLSQFwd'], enums=[])
Source('CHAOSLSQFwd.cc')
```

这就是 CHAOS README 说"实现为 SimObject，升级 gem5 版本也容易装"的机械原理：19 个注入器全是标准 SimObject 插件，对 gem5 的侵入只剩各流水级里几十行 hook 代码（第五章逐个清点）。

`CHAOS/Makefile` 的 `sync_chaos`（`Makefile:56-66`）从工程上守护同一件事：顶层 `CHAOS/CHAOSxxx/` 副本与 `CHAOS/gem5/src/...` 内嵌副本必须一致（vendored 为权威），防止 `cp -rf` 把陈旧顶层副本盖回已修复的构建源——"构建源被静默回滚"这类工具正确性事故在该 Makefile 注释里被明确列为设计动机。

### 1.6 精度谱系与 SE/FS 两种世界

同一内存系统上可挂四种 CPU 模型：AtomicSimpleCPU（功能级）、TimingSimpleCPU（时序近似）、MinorCPU（顺序流水线）、**O3CPU（周期级乱序流水线）**。物理寄存器堆、重命名、乱序调度这些微架构状态**只有 O3 建模**——这决定了 CHAOS 的 12 个 CPU 侧注入器全部 `dynamic_cast<o3::CPU *>` 且失败即抛异常（如 `CHAOSLSQFwd.cc:37-42`）。

Workload 分 SE（syscall emulation：gem5 内置 syscall 表拦截 read/write/futex，不跑内核）与 FS（full system：真实 bootloader→vmlinux→用户态）。这条看似平凡的边界，在第四章 §4.5 将被证明是**实验有效性的分水岭**——一行 if 决定了某些注入器有没有研究对象。

---

## 第二章 O3CPU：gem5 的乱序核

O3CPU（`src/cpu/o3/`，命名来自"Out of Order"）是本仓库全部 CPU 侧注入的研究对象。本章按数据流顺序讲透每个阶段，并在每处标注 CHAOS 的 hook 落点——第五章再从注入器视角回看同一批代码。

### 2.1 阶段组合模型与 TimeBuffer

`o3::CPU`（`src/cpu/o3/cpu.hh:114`）**组合**（而非继承）六个阶段对象（`cpu.hh:440-466`）：

```cpp
BAC     bac;       // 分支地址计算（解耦前端）
FTQ     ftq;       // 取指目标队列
Fetch   fetch;     // 取指
Decode  decode;    // 译码
Rename  rename;    // 重命名
IEW     iew;       // 发射/执行/写回（含 LSQ）
Commit  commit;    // 按序提交
PhysRegFile     regFile;          // 物理寄存器堆
UnifiedFreeList freeList;         // 空闲物理寄存器表
PerThreadUnifiedRenameMap renameMap, commitRenameMap;  // 前端/提交两张 RAT
ROB     rob;       // 重排序缓冲
Scoreboard scoreboard;  // 就绪位记分牌
```

阶段间不用回调而用**时间滑窗队列** `TimeBuffer<T>`（`src/cpu/timebuf.hh:40`）通信。CPU 持有五个（`cpu.hh:556-568`）：总线的 `timeBuffer<TimeStruct>` 加四级指令队列。`TimeStruct`（`src/cpu/o3/comm.hh:113` 起）是纯数据聚合：`FetchComm`（squash/nextPC）、`DecodeComm`（mispredict 信息）、`IewComm`（freeIQEntries/freeLQEntries 等反压计数）、`CommitComm`（ROB 空位、squash 序号）等。每个阶段通过 `wire`（`timebuf.hh:59`）读写本拍/前几拍/后几拍的槽位——**这建模的是真实流水线的段间寄存器**：上游写进 wire 的信号，下游在延迟若干拍后看到。

主循环在 `CPU::tick()`（`src/cpu/o3/cpu.cc:368-425`）：

```cpp
void CPU::tick()
{
    ...
    bac.tick();
    fetch.tick();
    decode.tick();
    rename.tick();
    iew.tick();
    commit.tick();

    // Now advance the time buffers
    timeBuffer.advance();
    fetchQueue.advance(); decodeQueue.advance();
    renameQueue.advance(); iewQueue.advance();
    activityRec.advance();
    ...
    if (!tickEvent.scheduled()) {
        ... schedule(tickEvent, clockEdge(Cycles(1)));   // 自我重排下一拍
    }
}
```

三个结构性事实：① 六阶段**同拍顺序执行**（不并行），乱序语义由各阶段内部状态机给出；② `advance()` 在六个 tick 之后统一推窗——阶段间的"一拍延迟"由此产生；③ 事件自我重排 + `ActivityRecorder` 空闲检测（`cpu.cc:411-415`），无活动时 CPU 自动停拍节能——**这意味着注入器的时间窗参数必须保证落在活动区间内，否则"窗口外"注入会静默变零**（第七章 §7.6）。

### 2.2 关键参数：乱序窗口的形状

`BaseO3CPU.py`（`src/cpu/o3/BaseO3CPU.py`）的缺省值刻画了一个 8 发射宽机器：

| 参数 | 缺省 | 行号 | 注 |
|---|---|---|---|
| fetchWidth / decodeWidth / renameWidth / issueWidth / commitWidth | 8 | 86/101/108/120/127 | 全 8 宽 |
| numPhysIntRegs / numPhysFloatRegs / numPhysVecRegs | 256 | 174/177/180 | PRF 深度 |
| numROBEntries | 192 | 188 | ROB 深度 |
| LQEntries / SQEntries | 32 / 32 | 142/143 | LSQ 深度 |
| branchPred | TournamentBP | ~199 | 缺省预测器 |

本仓库的 H2 实验沿 numROBEntries/numPhysIntRegs/LQ/SQ 扫参（`campaigns/h2-window-sweep.yaml`），FS 侧另有 TaiShan V110 代理参数（`configs/se/arm_chaos_fs.py:57-66`：ROB=128、PhysInt=160、PhysFloat=192、LQ=48、SQ=42）——配置面明确声明"NOT cycle-exact"，这是贯穿全仓库的诚实边界风格。

### 2.3 前端：BAC → FTQ → Fetch

v25 的 O3 前端有一层新结构：**BAC（Branch and Address Calculation，`src/cpu/o3/bac.hh:57`）+ FTQ（Fetch Target Queue）**构成的"解耦前端"——分支预测可以领先取指若干拍独立推进（`bac.hh:60-80` 类注释）。但解耦模式（`decoupledFrontEnd`）缺省关闭，耦合路径下 Fetch 直接查询 BPU，BAC 空转。

**CHAOSBPU 的 hook** 落在 `BAC::predict`（`src/cpu/o3/bac.cc:581-590`）：

```cpp
bool taken = bpu->predict(inst, ft->ftNum(), pc, tid, ft->bpuHistory);
// CHAOSBPU (S8-4): optionally substitute the predicted target (F5)
// or flip the direction (F1).
if (chaosBpu) {
    taken = chaosBpu->maybeSubstituteTarget(
        pc.as<GenericISA::PCStateWithNext>(), taken);
}
```

注意配置面的诚实声明（`configs/se/arm_chaos.py` BPU 段）：SimpleBoard 上开解耦前端**不能启动**（v25 实验特性），所以该 hook 在本仓库的标准 SE 配置里实际不被行使——BPU 注入因此定位为"负对照面"（错误预测流应被 squash 恢复，P(架构态==golden)≈1），其价值恰恰在于验证"流水线自愈"这一保护机制。

### 2.4 Rename：两张 RAT 与历史缓冲

Rename 阶段维护**两张映射表**（`cpu.hh:459-463`）：

- `renameMap`（前端 RAT）：架构寄存器 → 物理寄存器的**投机**映射，在飞指令读它；
- `commitRenameMap`（提交 RAT）：已提交指令确立的**提交**映射。

每次重命名压入一条 `RenameHistory`（`src/cpu/o3/rename.hh:311-330`）：`(instSeqNum, archReg, newPhysReg, prevPhysReg)`。squash 时 `Rename::doSquash`（`rename.cc:935`）沿历史缓冲逐条回滚：把 RAT 恢复到 prevPhysReg，把 newPhysReg 归还 FreeList（经 `freeingInProgress` 延迟队列避开 SMT 所有权冒险）。

**CHAOSROB 的 spec_leak hook** 精确插在回滚的归还点上（`rename.cc:963-976`）：

```cpp
// CHAOSROB spec_leak (S6-4): optionally SKIP the freelist
// return — the wrong-path dest physReg is neither referenced
// by the RAT nor returned to the free list, leaking the
// speculative write (method1's state-leak 4x signature).
if (chaosRob && chaosRob->maybeDelayFree(hb_it->newPhysReg)) {
    ... // 跳过 freeingInProgress[tid].push_back(...)
} else {
    freeingInProgress[tid].push_back(hb_it->newPhysReg);
}
```

这是全仓库"hook 位置必须忠实于微架构语义"的最佳标本：**错路径写保留**这个故障模型，在物理上对应"物理寄存器既不被 RAT 引用、也不回到空闲池"的泄漏态——它不是翻一个 bit，而是破坏一个**协议不变量**。

### 2.5 物理寄存器堆与 FreeList：CHAOSPhysReg 的靶场

`PhysRegFile`（`src/cpu/o3/regfile.hh`）按类别分 bank：intRegFile / floatRegFile / vectorRegFile / vecPredRegFile / matRegFile / ccRegFile 各是一维数组，配套 `PhysRegId` 表。`UnifiedFreeList`（`free_list.hh:143`）按类别包了 N 个 `SimpleFreeList`（`std::queue<PhysRegIdPtr>`）。两个 CHAOS 需要的探针级 API：

- `isFree(type, reg)`（`free_list.hh:213-218`）→ `SimpleFreeList::contains`（`free_list.hh:110-127`）：O(N) 扫队列判断寄存器是否空闲。注释给出判据："**一个物理寄存器不在 free list 里 = 已分配 = 活跃**——即使当前没有任何 RAT 项指向它（老映射被覆盖但在飞指令仍持有它当源）"。这个判据是 CHAOSPhysReg 探活的基础，也修正过早期"沿 RAT 反查"的过窄判据（曾把活槽误标死，制造 dead-slot SDC 假象）。
- `addReg(reg)`（`free_list.hh:83`）：直接把寄存器压回空闲队列——CHAOSFreeList 的 `mark_free` 故障正是滥用它（见 §5.7）。

regfile.hh 本身被注入器"借道"加了三组热路径内联代码（`regfile.hh:185-231`）：

1. **read-trace**（`:185-209` 声明，`:248-253`/`:259-263`/`:296-300` 计数，`:353-359`/`:373-374`/`:413-416` 置 overwritten）——读注入值计数、写即封存；
2. **G2 stuck-at 写路径掩码**（`:211-231` 声明，`:363-366`/`:375-379` 施加）——永久故障在**每次写**该槽位时强制粘死位；
3. **旁路访问器**（`:167-183`）：`numIntPhysRegs()/intPhysRegId(idx)/…/vecRegBytes()` 把私有 bank 暴露给注入器。

第五章会逐行读这三组代码；这里先记结构教训：**注入逻辑不塞进 regfile，regfile 只开最小通道**——侵入面控制在可审计的几十行。

### 2.6 IEW：发射队列与依赖图

`IEW::tick`（`src/cpu/o3/iew.cc:1430` 起）一拍内的次序：`ldstQueue.tick()`（LSQ）→ `sortInsts` → 各线程 `checkSignalsAndUpdate` + `dispatch` → `executeInsts` → `writebackInsts` → `instQueue.scheduleReadyInsts`（为下一拍排发射）→ `issueToExecQueue.advance()`。

发射队列 `InstructionQueue` 的唤醒核心是 `wakeDependents`（`src/cpu/o3/inst_queue.cc:1078`）：沿依赖图 `dependGraph` 弹出目的寄存器的等待者，`markSrcRegReady()` 后 `addIfReady()`。**CHAOSIQ 在每个依赖者被弹出后、置就绪位前插问**（`inst_queue.cc:1172-1187`）：

```cpp
if (cpu->chaosIQ) {
    CHAOSIQ::HookAction act =
        cpu->chaosIQ->hookWakeDependents(dep_inst, dest_reg);
    if (act != CHAOSIQ::HookAction::None) {
        DynInstPtr skipped = dep_inst;
        dep_inst = dependGraph.pop(dest_reg->flatIndex());  // 先弹下一个
        dependGraph.insert(dest_reg->flatIndex(), skipped); // 再塞回被跳过者
        if (act == CHAOSIQ::HookAction::Defer)
            cpu->chaosIQ->recordDeferred(skipped, dest_reg->flatIndex());
        requeued = true; ++dependents; continue;
    }
}
```

两处防御性细节写进了 hook 本身：先弹后塞（否则 pop-push 死循环返回同一节点）；被延迟的唤醒在**下一次** `wakeDependents` 开头由 `takePendingWakeups()` 投递并**从依赖图移除**（`inst_queue.cc:1082-1094`）——不删会触发 drain 时的"依赖图非空"断言。hook 的注释还自我声明建模局限：wake_phase 是"一拍延迟近似"，gem5 的同步 IQ 没有真正的相位流水可移位——**代理位置错位要如实声明**是这个项目的方法论纪律。

### 2.7 LSQ 与 store→load 转发：CHAOSLSQFwd 的靶点

`lsq_unit.cc` 的转发判定在 `:1440-1473`：遍历 SQ 中比 load 年轻的 store，按地址覆盖算出 `AddrRangeCoverage`（None/Partial/Full）。`FullAddrRangeCoverage` 分支（`:1475`）就是硅上 store buffer 前递网络的模型：

```cpp
// src/cpu/o3/lsq_unit.cc:1489-1516（节选，两处 CHAOS hook 原样保留）
uint8_t *fwd_src = (uint8_t*)(store_it->data() + shift_amt);
if (cpu->lsqFwd) {                       // hook ①：换源
    fwd_src = cpu->lsqFwd->pickSource(
        (uint8_t*)(store_it->data() + shift_amt),
        request->mainReq()->getSize(),
        request->mainReq()->getVaddr());
}
memcpy(load_inst->memData, fwd_src,
    request->mainReq()->getSize());       // ← 转发即这个 memcpy

if (cpu->lsqFwd) {                        // hook ②：毁数
    cpu->lsqFwd->corrupt(load_inst->memData,
                         request->mainReq()->getSize(),
                         request->mainReq()->getVaddr());
}
```

两个 hook 的分工对应两类故障语义：`pickSource` 在 **memcpy 之前**替换数据源（错源转发/陈旧行重放/相位错位——"拿错的数据"），`corrupt` 在 **memcpy 之后**改写目的缓冲（位级/结构化故障——"数据在通路上被毁"）。**转发数据不经过 cache、不经过 PRF 读端口**（消费即生产时甚至不写 PRF cell）——这个微架构事实是必须独立造 LSQFwd 注入器的全部根据：PRF/Cache 位翻转注入器对这条通路天然失明。第七章 §7.3 的"forwarding 掩蔽定律"是同一事实的反向利用。

### 2.8 Commit 与 ROB

`Commit::tick`（`src/cpu/o3/commit.cc:600`）先处理 squash 收尾（`rob->doSquash`），再 `commit()` 按序退休 ROB 头指令，最后 `markCompletedInsts()` 通知 IEW 回收。ROB（`src/cpu/o3/rob.hh:71`）是 `std::list<DynInstPtr>` 加每线程状态机（Running/Idle/ROBSquashing）。

CHAOSROB 从 `cpu->robAccess()`（`cpu.hh:497`）拿到 `readHeadInst(tid)`，对**即将提交**的指令做 entry_bitflip（改 seqNum）/exc_suppress（吞异常位）——注意它攻击的是 ROB 头而非任意槽位，因为只有头部的状态能进入架构态。

### 2.9 DynInst：指令的运行时载体

`DynInst`（`src/cpu/o3/dyn_inst.hh`）是在飞指令的全状态载体：PC、seqNum、重命名后的物理源/目的、`instResult` 结果队列、fault、memData……第五章三个注入器的 hook 直接写进它的寄存器读写接口：

- `getRegOperand`（读源，`:1184-1204`）——CHAOSFPU 的 source-read hook：**消费者读操作数的瞬间**毁值；
- `setRegOperand`（写目的，`:1223-1244`）——CHAOSFPU 的 writeback hook：**值进 PRF 之前**毁值；
- `corruptResultRegVal`（`:712`）——通用结果毁伤入口，CHAOSExec/CHAOSL1DForward 用它攻击 ROB 头 load/ALU 结果。

CHAOSFPU.hh 的注释记录了一次教科书式的 hook 迁移：v1 挂在 ROB 头攻击 `corruptResultRegVal`，在 gemm_double 上 5089/5089 次命中"result already popped"（到 ROB 头时结果早已弹出）——**hook 点选错，注入器就成了永不击发的枪**。v2 迁到 setRegOperand 写回路径后才有真实命中。第七章 §7.1 把这条经验上升为定律。

---

## 第三章 内存系统：从 Request 到 DRAM

### 3.1 Request 与 Packet

一次访存的三个抽象层：`Request`（谁、哪个虚地址、什么语义——`src/mem/request.hh`）→ `Packet`（带上 MemCmd 与数据缓冲的传输单元——`src/mem/packet.hh`）→ Port 间协议交互。request.hh 里有一处 CHAOS 修改值得注意（`request.hh:858-868`）：

```cpp
/** CHAOSAddrPath (P-D2) injector: in-place vaddr mutation at the
 *  address->MMU boundary ... Only meaningful pre-translation. */
void setVaddr(Addr vaddr) { _vaddr = vaddr; }
```

为什么不用现成的 `setVirt()`？注释说得明确：setVirt 会重置 size/flags/requestorId/翻译状态，而地址通路注入需要**只改 vaddr、保全其余全部元数据**——被腐蚀的 vaddr 必须原样进入 MMU 走查，才忠实复现"架构寄存器是对的、MMU 收到的是错的"这一现场签名。一个 8 行的访问器，承载的是注入语义的精确性。

### 3.2 Port 系统

`RequestPort`/`ResponsePort`（`src/mem/port.hh:134`/`:347`）以三套接口覆盖三种访问模式：timing（周期精确，带 retry 反压）、atomic（单拍功能模拟）、functional（debugger/注入器直捅，绕过时序）。标准拓扑：

```
CPU.dcache_port ──► L1D(ResponsePort) ──► XBar ──► L2 ──► XBar ──► MemCtrl ──► DRAM
```

CHAOSMem 对 DRAM 的攻击走 **functional 通道**（`CHAOSMem.cc:244/331`：`memory->access(read_pkt)`）——构造 ReadReq/WriteReq 包直读直写物理内存，不占用时序资源。这是"注入器是旁观者，不是访存者"原则的体现。

### 3.3 Cache 层级：BaseCache 与 tags

`BaseCache`（`src/mem/cache/base.hh:103`）实现命中/缺失/MSHR 合并/写回状态机；标签阵列抽象为 `BaseTags`（`src/mem/cache/tags/base.hh:81`），具体是 `BaseSetAssoc`/`FALRU`/`SectorTags` 等子类。CHAOSCache 在这层有**两个 hook**，分别建模两类故障：

**hook ①：查找期假命中**（`src/mem/cache/tags/base.cc:94-107`，`BaseTags::findBlock`）：

```cpp
if (blk->match(key)) {
    if (chaosCache && blk->isValid()) {
        CacheBlk* div = chaosCache->chaosDivertFindBlock(
            blk, entries, key);
        if (div) return div;    // 查 A 却返回 B 的数据块
    }
    return blk;
}
```

CHAOSCache.hh 的长注释解释了为什么不在标签存储里改 tag：直接改存 tag 会让该行在**另一个地址**下逐出，触发 snoop filter 未跟踪行的 WritebackDirty 断言（`snoop_filter.cc:144` 的 panic）——那是 SimulatorError，不是合法 DUE 结局。于是故障模型改在**查找时改道**：tag 存储不动，逐出/写回仍按真实地址走协议，只有**数据供给**错了——恰好是 SDC 相关的语义。

**hook ②：牺牲者路径写回毁伤**（`src/mem/cache/base.cc:1798-1805`，`BaseCache::writebackBlk`）：`pkt->setDataFromBlock` 把完好行数据拷进写回包**之后**、包离开**之前**毁 payload——"cache 里的行是好的，下行通路的数据是坏的"，一个数据阵列与标签阵列注入器都看不见的盲区。

### 3.4 物理内存与 CHAOSMem

`AbstractMemory` 提供字节粒度的 backing store。CHAOSMem 的攻击循环（`CHAOSMem.cc:207` `attackMemory`）：几何分布抽地址 → （可选）`addr_map_sub` 异或重定向（`:222-239`，F5 合法域内错址）→ functional 读-改-写回单字节。注释里的 G4 修复记录了曾把区间写成 `[start, end-1]` 静默丢掉末字节的边界 bug——注入器自身的 off-by-one 会变成"最后字节永不中弹"的采样偏差。

### 3.5 ARM MMU、TLB、页表走查器——与 SE/FS 边界

ARM 翻译栈：MMU（`src/arch/arm/mmu.cc`）→ TLB（`src/arch/arm/tlb.cc`）→ TableWalker（`src/arch/arm/table_walker.cc`）。四个注入器挂在这条链上，全部 **FS-only**，原因在 `mmu.cc:1212` 这一行 if：

```cpp
// If guest MMU is off or hcr.vm=0 go straight to stage2
if ((state.isStage2 && !vm) || (!state.isStage2 && !state.sctlr.m)) {
    fault = translateMmuOff(tc, req, mode, tran_type, vaddr, ...);  // :1005
} else {
    fault = translateMmuOn(tc, req, mode, translation, delay, ...);
}
```

`sctlr.m` 是 SCTLR_EL1 的 MMU 使能位。**SE 模式从不打开它**——所有翻译走 `translateMmuOff`（恒等映射，直接 `setPaddr(vaddr)`），TLB 不查、页表不走。后果链：CHAOSArmTLB 的 hook（`tlb.cc:167-168`，命中后毁 entry 的 pfn）恒零调用；CHAOSPTW 的 hook（`table_walker.cc:1954-1963`，描述符取回后、判读前）恒零调用；CHAOSAddrPath 清零 byte7 后地址仍落物理范围、不 fault。项目早期 H6/H7 的 SE null 结果险些被当成"注入器无效"的发现——实为**仿真模式伪迹**。这不是文档层面的提醒，而是本仓库写在 `configs/se/arm_chaos.py` AddrPath 段注释里的工程约束："FS MODE REQUIRED for observable effect"。

四个 MMU 链注入器的挂载方式各不相同，本身就是一份挂载模式教材：

- **CHAOSArmTLB**：`tlb.cc` 文件级指针 `chaosTLB`，命中 hook 传 `TlbEntry*`；字段级目标（pfn/ap/xn/attridx/ng/asid）；`mapped_page` 模式把命中项的 pfn 换成**同 TLB 另一有效项**的 pfn——替换结果必是已映射页，永不触发 DUE 守卫，最危险的静默 SDC 通路；
- **CHAOSPTW**：构造时 `mmu->setPtwInj(this)`（`mmu.hh:94-95` 提供 setter/getter），walker 经 `mmu->getPtwInj()` 取回；
- **CHAOSArmSysReg**：`isa.cc:459-465`，挂在 `readMiscRegNoEffect`（MRS 读路径）返回前，按 miscRegName 白名单（sctlr_el1/ttbr0_el1/tcr_el1…）放行，`value_to_legal` 模式替换成另一合法值——F5 合法域内错误；
- **CHAOSAddrPath**：见 §3.1 与 §2.7，hook 在 `lsq.cc:1135-1152` 的 `sendFragmentToTranslation`，翻译**前**毁 vaddr。

---

## 第四章 CHAOS 框架总览：19 个注入器的组织法

### 4.1 模块清单与目录学

上游 CHAOS（巴西侧，README 署名 Vinciguerra 等）提供 4 个模块：CHAOSReg / CHAOSPhysReg / CHAOSCache / CHAOSMem，故障原语仅三种位级操作（bit_flip / stuck_at_zero / stuck_at_one）。本仓库在 fi-fuzz 分支扩展到 **19 个编译进 `build/ARM` 的模块**（可由 `build/ARM` 目录逐一核对），按微架构位置分组：

| 组 | 模块 | 靶点 | 挂载方式 | 故障模式（超出位级的部分） |
|---|---|---|---|---|
| 前端 | CHAOSBPU | BAC::predict | cpu->bacAccess 自挂（bac.hh:344） | target_sub / direction_flip |
| 重命名 | CHAOSRenameMap | 前端 RAT | attackEvent 自驱动 | F5Substitute（映射张冠李戴）/ F4FieldStuck / map_bitflip |
| 重命名 | CHAOSFreeList | 物理寄存器空闲表 | attackEvent 自驱动 | mark_free（活寄存器入空闲池→双重占用）/ pop_wrong |
| 重命名 | CHAOSPhysReg | PRF cell | attackEvent + regfile 内联 hook | phys/arch_frontend/arch_commit 三抽象、F3 数据触发、G2 写路径粘死、read-trace、NEON 分 lane |
| 发射 | CHAOSIQ | 依赖图唤醒 | cpu->chaosIQ 自挂 + wake hook | src_ready_bitflip / tag_sub / wake_omit / wake_phase |
| 提交 | CHAOSROB | ROB 头指令 | cpu->robAccess + rename 回滚 hook | entry_bitflip / exc_suppress（DUE→SDC）/ spec_leak（错路径写保留） |
| 提交 | CHAOSRAS | RAS 错误记录 | attackEvent | ERR* 记录抑制（可报告 DUE 变不报告 SDC） |
| 执行 | CHAOSExec | 整数 ALU 结果 | attackEvent + corruptResultRegVal | 位段分层（low/mid/high） |
| 执行 | CHAOSFPU | FSU 写回/源读 | cpu->chaosFPUHook + DynInst 四个 hook | writeback 毁值 / source-read 毁值 / IEEE754 位段（sign/exp/mantissa） |
| 执行 | CHAOSL1DForward | load 结果（ECC 后） | attackEvent + corruptResultRegVal | post-check escape：校验过后通路毁值 |
| LSU | CHAOSLSQFwd | store→load 转发 | cpu->lsqFwd 自挂 + lsq_unit 双 hook | 结构化：byte_lane_skew / all_zero；错源：fwd_source_sub / stale_line_replay / phase_offset |
| LSU | CHAOSAddrPath | AGU→MMU 地址通路 | cpu->addrPath 自挂 + lsq hook | byte7 清零（D2 签名） |
| 内存 | CHAOSCache | cache 数据/标签/元数据/牺牲者路径 | attackEvent + findBlock/writebackBlk 双 hook | tag false-hit、victim 路径、repl/valid/dirty 元数据、SED/SECDED 保护模型、128B 配对扇区 |
| 内存 | CHAOSMem | DRAM 字节 | attackEvent + functional 包 | addr_map_sub（F5 错址）、secded 保护模型 |
| 内存 | CHAOSExMon | ARM 独占监视器 | 命名空间指针 chaos_exmon_g + isa.cc 双 hook | stale_reservation（SC 假成功→丢失更新）/ clear_reservation |
| 内存 | CHAOSArmTLB | D/ITLB 命中项 | tlb.cc 文件级指针 | pfn 位翻 / mapped_page（活页替换）/ ap/xn/attridx 字段 / parity 保护 |
| 内存 | CHAOSPTW | 页表走查器读出 | mmu->setPtwInj | 描述符位翻 / clearValidBit（绕 ECC）/ conditional_valid / ptwEcc 对照 |
| 系统 | CHAOSArmSysReg | MRS 系统寄存器读 | isa.cc 文件级指针 | value_to_legal（F5 白名单合法值） |
| 系统 | CHAOSReg（上游） | 架构寄存器（ThreadContext） | attackEvent | 上游原样；配置面声明其 O3 局限 |

三个诚实注记：① 旧版本文档提到过的 CHAOSDecode 与 CHAOSPosParity **在源码树中不存在**（`grep -r` 全树无此类）——前者从未实现（译码覆盖由 BPU/RAS/Exec/FPU 承担），后者是研究设计（`docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md` 与两篇 posparity paper），其 tag/verify 双侧校验 hook 并未进入当前 lsq_unit.cc；② CHAOSIQ 的 v1 attackEvent 与 v2 wake hook 并存，前者保留兼容；③ 同名顶层 `CHAOS/CHAOSxxx/` 目录是 vendored 副本的镜像，构建以 vendored 为权威（`CHAOS/Makefile:49-66`）。

### 4.2 四种挂载模式

**模式 A：自挂载（self-attach）**——注入器构造函数把 `this` 写进宿主的裸指针，热路径判空短路。全家福：

```cpp
cpu->lsqFwd     = this;   // CHAOSLSQFwd.cc:60
cpu->addrPath   = this;   // CHAOSAddrPath.cc:50
cpu->setChaosFPUHook(this);   // CHAOSFPU.cc:47
cpu->setChaosIQ(this);        // CHAOSIQ.cc:55
cpu->renameAccess().setChaosRob(this);   // CHAOSROB.cc:53
// + BaseCache::chaosCacheVictim / BaseTags::chaosCache / tlb.cc chaosTLB /
//   isa.cc chaosSysReg 与 chaos_exmon_g / mmu->setPtwInj
```

宿主指针在 `cpu.hh:506-538` 集中声明，每条注释都写明"SImObject 构造先于执行，lsq 只在 execute() 里读它，故安全"。不挂时的代价是热路径一次判空——这是"零框架开销"与"可插拔"的折中点。

**模式 B：旁路访问器**——对本应 private 的状态开最小公开通道：`cpu.hh:484-504` 的 `physRegFile()/frontRenameMap()/commitRenameMapAccess()/physFreeList()/robAccess()/renameAccess()/bacAccess()`，`regfile.hh:167-183` 的按索引取 cell，`free_list.hh:115/213` 的 contains/isFree。原则：**通道只暴露读/定位，注入逻辑仍留在注入器**——保证 gem5 树的 diff 可审计。

**模式 C：自驱动 attackEvent**——目标不是 SimObject（RAT/FreeList/ROB/PRF 都只是 CPU 的成员），注入器自己挂事件循环：`EventFunctionWrapper attackEvent`（如 `CHAOSPhysReg.cc:46`），构造时 `scheduleAttackEvent(first_clock + geometric(p))`（`:67-69`），每次触发调 `processFault` 后再自排。**事件驱动注入器与宿主解耦最彻底**，代价是要自己处理"攻击时刻目标不存在"的拒绝路径——四个注入器（RenameMap/FreeList/FPU v1/CHAOSRAS）都写过同一条修复：拒绝时几何分布可能给出 0 拍间隔导致每拍空转死循环（`CHAOSFPU.cc:215-228` 注释记录了 gemm_kernel + probability=1.0 挂死、只有 numSkippedNonFp 在涨的事故），修法统一为"未命中则强制 +1 拍退避"。

**模式 D：热路径 hook**——模式 A 的调用侧：宿主代码里 `if (cpu->xxx) cpu->xxx->method(...)` 的那几行，全部已在第二、三章逐个引用。这就是 CHAOS 对 gem5 的**全部侵入**：全树 grep "CHAOS" 在 `src/cpu/o3/` 命中约 15 处文件、在 `src/mem/` 命中 8 个文件、`src/arch/arm/` 4 个文件，每处都是判空调用加注释。

### 4.3 注入门控模板：corrupt() 的五层门

以 `CHAOSLSQFwd::corrupt`（`CHAOSLSQFwd.cc:281-364`）为范本，门控次序是全部注入器的公约：

```cpp
if (probability <= 0.0f) return;                     // ① 未配置 → 零开销退出
Cycles cur = cpu->curCycle();
if (cur < first_clock) return;                       // ② 时间窗下界
if (last_clock != Cycles(0) && cur > last_clock) return;  // ③ 上界（0=不限）
if (max_faults != 0 && faults_injected_count >= max_faults) return;  // ④ 单故障纪律
std::uniform_real_distribution<float> dist(0.0f, 1.0f);
if (dist(rng) >= probability) return;                // ⑤ Bernoulli 抽样
// …门门过了才真正改数据
```

每一条门都是踩坑换来的，项目注释就是证据链：

- **②③ 的时间域陷阱（D1/D4）**：LSQ/TLB/PTW 不是 ClockedObject，够不到 `curCycle()`，只能用 `curTick()`——CHAOSMem 曾因 `tickToClockRatio=1000`（1GHz 假设）在 2.6GHz 配置下把窗口推出仿真总长，384 次全 Inactive。修法（CHAOSArmTLB.hh 的 D1 fix 注释）：firstClock/lastClock 语义改为 **sim tick 域**，`startup()` 里快照一次，不猜换算比。
- **③ 的 lastClock=0 约定**：README 明文警告"不要拿小非零值当窗口用——会静默零注入"，计数控制一律用 maxFaults。
- **④ 单故障纪律（G5）**：max_faults=1 + 固定 rngSeed = 可复现实验单元，384 个 seed 就是 384 次独立单故障实验，配 golden 对照算 Wilson CI。
- **⑤ 的 RNG 构造 UB（patch bc4feb4）**：早期 `rng(rng_seed != 0 ? rng_seed : rd())` 因成员声明顺序（rng 声明在 rd 之前）在构造期调用未构造的 `std::random_device` → SIGSEGV。修法是 lambda 局部构造（CHAOSAddrPath.cc:31-35 现状）：

```cpp
rng([this]() {
    std::random_device local_rd;
    return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
}()),
```

这解释了历史上"seed 42 能跑、默认 seed 0 必崩"的诡异现象——不是概率问题，是构造顺序 UB。

- **numHooksCalled 先于一切门**（CHAOSExMon 的 Stats：numInWindowChecks/numOutOfWindow 分列）：区分"路径没被行使"和"行使了但概率没中"。没有这个计数器，FS boot 期"零注入"就无法归因——是 walk 密度太低，还是 hook 没接上？（第七章 §7.5 的 PTW walk 密度 0.069% 结论就靠它支撑。）

### 4.4 故障模型的三层表达力

上游 CHAOS 只有位级三原语（对一个 byte：`&=~mask` / `|=mask` / `^=mask`，LSQFwd.cc:339-353 的窗口化版本把它们扩到连续 maskWidth 字节）。本仓库的扩展沿三个正交轴展开：

**轴一：结构化故障（整字错路由）**——`CHAOSLSQFwd::applyStructuralFault`（`CHAOSLSQFwd.cc:203-244`）：

```cpp
case StructuralFault::ByteLaneSkew: {
    int k = skew_bytes;               // 0 = 随机 1..7
    ...
    // Right-rotate the byte array by k (byte lane n gets data[(n+k)%size]).
    std::vector<uint8_t> tmp(data, data + size);
    for (unsigned n = 0; n < size; n++)
        data[n] = tmp[(n + k) % size];
}
case StructuralFault::AllZero:
    std::memset(data, 0, size);
```

动因写在注释里：core 179 现场的撕裂值是**源数组的字节流循环移位**——与真值汉明距离可以为 0 的"旋转"，**任何位翻转都无法表达**（穷举 8 字节 × 256 掩码无命中）。byte_lane_skew 的物理解释是 fill-buffer 字节通道 mux 选错相位；all_zero 对应"空槽"形态（15:42 案 `__per_cpu_offset[176]` 交付 0）。当 structuralFault ≠ none 时**优先于位级轴**（`corrupt()` :299-302）。

**轴二：错源/时序故障（拿错的数据）**——`pickSource`（`CHAOSLSQFwd.cc:139-200`）维护一个 HIST_CAP 环形历史缓冲，每次转发先记录当前 store 数据；命中概率门后不 memcpy 真源，而是返回**历史槽**：fwd_source_sub 取最近有效项（错 store 转发）、stale_line_replay 同（陈旧 fill-buffer）、phase_offset 取 `phaseOffset` 步之前的深槽（时序相位竞态，method3 的 100%→10-20% 签名）。历史太浅（无残影可提供）时诚实返回真源、不计数。

**轴三：协议/结构不变量破坏**——RAT 张冠李戴（RenameMap F5）、活寄存器入空闲池（FreeList mark_free）、错路径写保留（ROB spec_leak）、SC 假成功（ExMon stale_reservation）、TLB 活页替换（ArmTLB mapped_page）、cache 假命中改道（Cache divert）。这些故障不是"数据错了"而是"**决定数据从哪来的机制错了**"——位级注入器对它们全体失明。

### 4.5 保护模型：注入器内置 ECC 模拟

CHAOSCache 的 `ProtectionModel`（`CHAOSCache.hh:105-110` 一带）与 CHAOSMem 的 `protection_model`、CHAOSArmTLB 的 `parity_interleaved`、CHAOSPTW 的 `ptwEcc`，把"注入后 ECC 会怎样"建模进注入器本身：SED/SECDED/SECDEDPoison/ParityInterleaved 在注入后判定纠正（还原字节）/检测不可纠（毒化）/静默放行（≥3 bit 超 SECDED），并由 `classify_run_pa`（`tools/classify.py:195` 起）九类分类读出 Corrected / DetectedContained / Latent 标记。这使"加 ECC 后逃逸面还剩多少"成为可运行的对照实验，而非纸面推理（L1D raw 97.7% SDC → +SECDED 单 bit 全纠 → ECC 后通路仍 90.9% 逃逸，正是这套机制跑出来的结论）。

---

## 第五章 注入器深读：六个代表案例

本章选六个注入器逐行讲透——它们合起来覆盖全部四种挂载模式与全部故障轴。

### 5.1 CHAOSPhysReg：物理 cell 抽象与 read-trace 闭环

**目标解析**（`CHAOSPhysReg.cc:164-277` `processFault`）分三步：

1. **选寄存器类别**（:170-181）：integer/float/vector，`both` 模式三类均匀抽——注释点明"真实坏 cell 不知道自己是什么类"（ITC'23/GeFIN 抽象）；
2. **解析物理寄存器**（:188-254）：`phys` 模式按物理索引直取（`-1` 随机），然后做**探活**——`physFreeList().isFree()` 判活，活槽再尽力反查"当前被哪个 arch reg 映射"（仅为日志诊断，不是判活依据，:226-251）；`arch_frontend` 模式走 `frontRenameMap()[tid].lookup(flat)` 拿在飞映射；`arch_commit` 走 commitRenameMap（保留上游 CHAOSReg 行为，注释明说它**在 O3 上会失效**——提交映射滞后于在飞读——仅作对照）。
3. **毁值**（:281-410）：向量类走 void* 缓冲路径，**按 lane** 施加故障（`vec_lane_width` 8/16/32/64 位 + `vec_lane_offset`，:306-357，缓冲按 `vecRegBytes()` 实宽分配——注释记录了固定 64B 栈缓冲在 SVE-2048b 下溢出 192B 的 report issue #3）；标量类支持 **F3 数据依赖触发**（:368-380）：

```cpp
if (trigger_value_mask != 0 &&
    ((uint64_t)reg_val & trigger_value_mask) != trigger_value_pattern) {
    ... log "trigger MISS — injection skipped" ...
    return;  // F3: not triggered, do not inject or count
}
```

建模 method2 的欠压 setup-time violation：缺陷只在特定位模式（特定 `__per_cpu_offset` 值）下显形。不中不算注入、不进统计——分母干净。

**永久故障的正确模型（G2）**：stuck-at 不在注入时改一次了事，而是调 `physRegFile().setStuckTarget(class, idx, mask, polarity)`（:391-401）把粘死掩码装进 **setReg 写路径**——之后对该槽位的每次写都被强制 `&=~mask` 或 `|=mask`（`regfile.hh:363-366`）。注释记录了旧方案 `checkPermanent` 周期性重粘为何错误：两次轮询之间的在飞写会漏网——与 CHAOSReg 的 commit-vs-frontend 伪迹同根：**在乱序机上，"定期快照式"的外部干预永远追不上流水线内部状态变迁**。

**read-trace 闭环**（`regfile.hh:185-209` + `CHAOSPhysReg.cc:420-428`）：注入后 `setReadTraceTarget` 装订追踪目标，之后每次 `getReg` 命中该槽且未 overwritten 则 `++reads_before_overwrite`（`regfile.hh:248-253`），首次 `setReg` 写该槽则 `trace_overwritten=true`（:353-359）。计数语义在注释里有段修正史：数的是**注入值**被读的次数，不是槽位被读的次数——槽位被重新分配后读的是新值，早期版本把 free-list 复用槽位误记为高读数。配合输出 diff，每个故障被归入四分类：**Benign（reads=0 未消费）/ Masked（被读但被逻辑屏蔽）/ SDC（传播到输出）/ Crash**。这是 AVF 分析的仿真级实现——分母从"注入次数"细化到"消费与否"，比只统计 SDC/注入数的既有工具多一层可解释性。

### 5.2 CHAOSLSQFwd：双 hook 与结构化故障

§2.7 已展示双 hook 宿主侧；注入器侧再补三件事：`pickSource` 的历史环（§4.4 轴二）；`applyStructuralFault` 的旋转移位（§4.4 轴一）；以及位级路径的**多字节窗口**（`corrupt()` :304-356）——`byteOffset` 定窗口低字节，`maskWidth` 定宽度（1..8，截断到转发缓冲尾），64 位 faultMask 按 little-endian 窗口施加（D2 修复注释：原 32 位单字节掩码够不着 `1<<32` 以上的高位字节，无法复现 method2 的高位谱）。

### 5.3 CHAOSFreeList：mark_free 的双重占用链

`processFault`（`CHAOSFreeList.cc`）的攻击链：扫前端 RAT 找**活的**物理寄存器（isFree==false，:46-66 的 donor 搜索）→ 合法性检查（目标是空闲则拒绝，:70+）→ `physFreeList().addReg(target_phys)` 把它压回空闲队列（:77）→ 下一次 rename 会把它分给**另一个** arch reg → 双重占用：旧主的在飞读返回**新主的值**（历史残留）。`pop_wrong` 模式更进一步：压入后立即 `getReg()` 弹出，在注入时刻就强制完成双重分配。与 CHAOSRenameMap 的分工在头注释里写明：RenameMap 换的是**映射决定**，FreeList 腐蚀的是**分配状态**——同一"历史残留"现象的两个物理根因。

### 5.4 CHAOSExMon：无对象上下文的 hook 怎么挂

ARM 的 SE 独占监视器实现为两个 misc 寄存器（MISCREG_LOCKADDR/LOCKFLAG，`CHAOSExMon.hh` 头注释指路 `isa.cc` 的 handleLockedRead/lockedWriteHandler）。麻烦在于 `lockedWriteHandler` 是**无对象上下文的自由模板函数**——没有 this 可挂。解法是命名空间级指针（`CHAOSExMon.cc:12`：`CHAOSExMon *chaos_exmon_g = nullptr;`，构造置、析构清 :48/:64-65），两个 hook 都插在 **STXR 的架构判定点**（`isa.cc:1934-1938` 失败分支里的假成功、`:1966-1970` 成功路径上的假失败）。头注释记录了一条关键经验：曾在 LDXR 处清标志的方案在 O3 上**不可见**——squash-replay 重放的 LDXR 会把标志重新立起来；改插到 STXR 判定点才稳定。**hook 必须落在架构判定点，而不是状态建立点**——乱序机的 squash 语义会把后者的效果洗掉。

### 5.5 CHAOSPTW：ECC 语义要精确到 descriptor type

hook 在 `WalkUnit::doLongDescriptor`（`table_walker.cc:1954-1963`）：描述符从内存取回、字节序转换完成之后、type 判读之前——注入的翻转就是 walker"读到"的东西。故障模式的三代演化是"现场形态学驱动设计"的教材：

1. 初版对描述符 XOR bit0 想制造 invalid PTE——但 ARM PTE 低 2 位是 descriptor type（0b01=block，0b11=table），`0b01^1=0b00` 才 invalid，`0b11^1=0b10` 仍 valid——实测 629 次注入全 benign；
2. 修复一 `clearValidBit`：AND `~0x3` 强制 invalid——2 bit 不可纠正、绕过 ECC，用于稳定制造 spurious fault（core 179 的 73 例 D3 签名）；
3. 修复二 `conditional_valid`：只对 0b01 描述符 XOR bit0——单 bit 使 ECC-on 时被纠正 / ECC-off 时 spurious，用于 H7 的忠实 ECC on/off 对照。

**同一个注入器里两种模式分别服务"制造症状"与"对照实验"**，参数文档必须把这一点写死，混用即污染对照。

### 5.6 CHAOSCache：字段级 × 保护模型的矩阵

`injectFault`（`CHAOSCache.cc:575` 起）按 `target_field` 分派：data（字节路径，含 directed 定址 `target_block_addr`/`target_byte_offset` 与 paired_sector 128B 故障域代理）、tag/tag_to_legal/valid/dirty/repl/coh（元数据路径）、victim（无 attackEvent 动作，纯靠 writebackBlk hook）。tag false-hit 的别名注册与 findBlock 改道已在 §3.3 讲过；这里补 attackEvent 采样与 hook 的分工注释（`CHAOSCache.cc:685`）："attackEvent does NOT inject; it only reschedules"——victim 字段下事件只维持时间窗，注入由写回事件驱动。**采样器与触发器分离**是 hook-on-event 注入器的标准形。

---

## 第六章 实验基础设施：从 manifest 到结论

仿真器之上是三层实验机器（全部在仓库根，非 gem5 树）：

```
campaigns/*.yaml ──campaign.py──► manifests/*.yaml ──runner.py──► gem5.opt 一次运行
      │        (笛卡尔展开+seed律)        │       (参数映射+断言)      │
      ▼                                  ▼                          ▼
 artifacts/<camp>/{cells.csv,summary.md} ◄──classify.py 六类/九类 ◄─ stdout/stderr/stats
                                                    │
                              escape_decomp.py(逃逸机理A-F) + sdc_fingerprint.py(位谱库)
```

**manifest（`schemas/arm-chaos-fi/v1`）**是实验的可复现单元：source 双 commit 锁（chaos_commit+gem5_commit）、workload 哈希、trigger（mode: cycle, value: 100000）、target（layer/component/instance/index/field/width_bits）、fault（model/bit_indices/duration_events）、rng（master_seed+selection_seed）、limits（max_faults: 1）。一个 manifest = 一次确定性单故障运行。

**runner.py** 把 manifest 字段映射为 `arm_chaos.py` 的命令行（`tools/runner.py:34-40` 定位 gem5.opt 与配置），跑完从输出抓 `FINAL=<16hex>` 校验和，**断言 faults∈{0,1}**（单故障纪律的运行时执法），golden 注册表 `GOLDEN_IDS`（:50-67）把 15 个 workload 的无注入校验和定死——工具回归会立刻暴露为 golden 不匹配。

**classify.py** 的六类有序分类（`tools/classify.py:73` 起）次序即语义：

```
SimulatorError → Hang → Crash → Inactive → Masked → SDC
```

关键设计：**SimulatorError 必须最先判**（gem5 panic/assert/SIGSEGV 是工具坏了，不是故障结局，混入会污染全部比率——report issue #4 修复前，exit!=0 + 空 stdout + 1 次注入记录曾被静默标成 SDC）；Hang（超时无校验和）与 Crash（trap/exit!=0）按"有没有完成"切开；Inactive（0 注入）单独成类，防止"没打中"被算进"打中了没事"。九类扩展再按注入器报告的 ECC 结局把 Masked/SDC 拆出 Corrected/DetectedContained/Latent。

**campaign.py**（`tools/campaign.py:52` 起）把 YAML 网格笛卡尔展开成 cell×rep，seed 律 `base + cell_ordinal×1000 + rep`，5% replay 自检（不一致即冻结），Wilson 95% CI（0-SDC 上界用 3/n 规则）。

**分析层**：`escape_decomp.py` 把每个 SDC 归因到六种逃逸机理（A 无保护/B SED≥2bit/C 超SECDED/D 后校验通路/E ECC逻辑故障/F 毒化丢失，`tools/escape_decomp.py:37-60` 的映射表）；`sdc_fingerprint.py` 从 golden⊕actual 掩码算 IEEE754 位谱（sign/exp/mantissa 份额+popcount 中位数）建"单元→位谱"指纹库，支持反向 lookup（现场位谱 → 嫌疑单元）——诊断闭环的起点。

**探针 kernel 层**（`workloads/directed/` 30+ 个 libc-only 静态 AArch64 自检程序）：reg_chain/cholesky（PRF 依赖谱）、fwd_7case 全家族（转发时序）、ptrskew（core179 故障链直译：指针数组装载→旋转错位→加基址→解引用）、gemm/fma（FSU 位谱）、exmon_kernel（LL/SC）。每个 kernel exit 0=pass / 1=SDC / 2=setup error，自带校验和。

---

## 第七章 方法论：架构理解如何决定实验有效性

本章是全书的落点：前六章的每一条架构事实，都曾直接决定一次实验的生死。

### 7.1 hook 点选择 = 微架构定位

同一个"数据损坏"可注在 cache、PRF、转发路径、内存——它们对应**不同的物理缺陷位置**。L1D 数据 97.7% SDC vs L1I 0%（错误指令流被 squash 或非法崩溃——取指通路自掩蔽）的悬崖，直接回答"ECC 预算投给取数还是取指"。CHAOSFPU v1→v2 的迁移（§2.9：ROB 头攻击 5089/5089 次"result already popped"）从反面证明：hook 位置差一个流水级，注入器就是哑炮。**写 hook 前先问：硅上这个故障发生在哪一级？数据在这一级长什么样？**

### 7.2 合法域内错误是 SDC 的核心形态

跨单元成立的横断定律（project-understanding.md §3.2 的定量总账）：错值全程**合法**（错源整字 / 活页 pfn / PRF 低位偏移 / RAT 合法 tag）才静默传播；域外错（RAT 越界 / PRF 高位 / byte7 清零）必崩或自愈。LSQ 转发路径上同一结论的定量版本：错源整字 37.6% SDC vs 单 bit 4.7%（8 倍）。**故障形态 > 故障位置**——这是对"只翻位"类工具的系统性批评，也是 §4.4 三条故障轴的存在理由。

### 7.3 forwarding 掩蔽定律

紧循环 chase 里指针的生产者-消费者距离只有一条 ldp——O3 转发直接把生产者结果递给消费者，**物理 cell 无读者**（read-trace reads=0 佐证），PRF 位翻转架构不可见。这条从仿真架构本身推导出的定律解释了：为何 PRF 臂实验必须在 FS 内核态跑（内核指针使用模式的依赖距离更长），也修正了"physreg 保护"的优先级评估。架构知识反过来指导注入有效性——**不是所有靶点对所有 workload 都暴露**。

### 7.4 确定性仿真的统计学陷阱

gem5 同 seed 同结果。事件驱动注入器若"窗口开后第一个过概率门的事件"恒为同一条动态指令，384 个 seed 全部命中同一事件，**统计独立性是假的**。修复机制在代码里有三处体现：attackEvent 类用几何分布抽**间隔**（`CHAOSPhysReg.cc:67-69`）而非固定首拍；hook 类用 per-event Bernoulli（§4.3 门⑤）；CHAOSFPU.cc:56 注释里的 "events_to_skip semantics" 标记了旧 manifest 语义的兼容路径。同类陷阱还有：argparse exit=2 被分类器当 Crash、campaign 组件映射表静默改道。项目的答案是把**工具正确性审计制度化**：golden 注册表 + faults 来源日志核对 + 5% replay + Wilson CI。

### 7.5 事件密度定标

`numHooksCalled`（先于一切门计数）回答"这条通路被行使了没有"。FS 内核态启动期 PTW walk 密度仅 0.069%、早期 boot 0.0066%——**概率参数必须按实测密度定标**，否则"期望注入次数"算不出来，"零注入"也无法归因（低密度 vs hook 断线）。这是把 instrumentation gap 写进注入器的直接理由（§4.3）。

### 7.6 双时间轴与窗口语义

`cpu->curCycle()`（CPU 域）与 `curTick()`（全局域）比值随配置变——§4.3 已展开 CHAOSMem 的 1GHz 假设事故与 D1/D4 修复（tick 域窗口 + startup 快照）。配套教训：O3 的 ActivityRecorder 空闲停拍意味着"窗口"必须覆盖实际活动区间，且 lastClock 小非零值 = 静默零注入（README 警告原文）。

### 7.7 SE/FS 边界：mmu.cc:1212 的实验有效性含义

§3.5 的那行 if 把四个注入器（ArmTLB/PTW/SysReg 有感，AddrPath 症状畸变）钉死在 FS 模式。配套工程方案：Atomic 快速 boot → `m5 checkpoint` → O3 restore（`configs/se/fs_checkpoint.py`），绕开 FS 启动的 wall-time 代价。方法论结论已写进 mspc_paper：**仿真实验的 null 结果必须先排除环境几何伪迹**——"SE 下零注入"不是发现，是模式边界。

### 7.8 诚实边界（项目自我声明）

1. gem5 O3 ≠ TSV110 RTL；无 HCCS/NoC 周期精确模型；跨 ISA 结论限可建模子集，TSO-vs-弱序不可建模（wake_phase 不捕获 method3 相位签名即为一例，§2.6 已注明）。
2. 本机即 CPU179 故障机：全部 formal 需第二台健康机复现才算最终确认。
3. CHAOSBPU 在标准 SE 板上不被行使（解耦前端不兼容 SimpleBoard，§2.3）；CHAOSDecode/CHAOSPosParity 不存在于源码树（§4.1）——文档与代码不一致时，以代码为准并如实声明。

---

## 第八章 一图总览

```
┌──────────────────────── gem5 离散事件内核（第一章）────────────────────────┐
│  doSimLoop → EventQueue::serviceOne → event->process()   [tick 优先级排序]  │
│         ▲                                    │                             │
│  Python instantiate(): createCCObject→init→regStats→probe→initState        │
│  （六遍扫描建对象图；startup 时注入器快照时间窗）                            │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ CPU_Tick_Pri 自排事件
┌──────────────────── O3CPU::tick()（第二章）────────────────────────────────┐
│  BAC──►FTQ──►Fetch──►Decode──►Rename──►IEW──►Commit   ⟨TimeBuffer×5⟩       │
│   │BPU注入     │        │RAT/FreeList │  │IQ/LSQ/写回  │ROB头               │
│   │(负对照)    │        │  ↑↑  ↓↓     │  ↑↑           │                     │
│   │           │     ┌──┴──────────────┴──┴──┐         │                     │
│   │           │     │ PhysRegFile + FreeList │◄─旁路访问器                  │
│   │           │     │ （read-trace/stuck 内联hook）       │                     │
│   │           │     └────────────────────────┘         │                     │
│   │           │  spec_leak hook: rename.cc:967 跳过freelist归还             │
│   ▼           ▼                                        ▼                     │
│  LSQ::executeLoad                                                      │
│   ├─ sendFragmentToTranslation ──CHAOSAddrPath(翻译前毁vaddr)──► MMU     │
│   │        │                                                            │
│   │  mmu.cc:1212: !sctlr.m ──► translateMmuOff（SE 恒走此路，PTW/TLB死路）│
│   │        │ FS: SCTLR.M=1                                              │
│   │        ├─► TLB::lookup ──CHAOSArmTLB(命中毁pfn)                     │
│   │        └─► TableWalker::doLongDescriptor ──CHAOSPTW(PTE读出后)       │
│   └─ LSQUnit 转发 memcpy（lsq_unit.cc:1502）                             │
│        ├─ pickSource(换源:错源/陈旧行/相位)   ← hook ①                   │
│        └─ corrupt(毁数:位级/byte_lane_skew)   ← hook ②                   │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               │ RequestPort/ResponsePort（第三章）
┌──────────────────── 内存系统 ──────────────────────────────────────────────┐
│ L1D/L1I ──► BaseCache ──► BaseTags::findBlock ◄─CHAOSCache(假命中改道)      │
│    │          └writebackBlk ◄─CHAOSCache(victim毁写回payload)              │
│    ▼  XBar ─► L2 ─► MemCtrl ─► AbstractMemory ◄─CHAOSMem(functional RMW)  │
│  isa.cc: MRS读──CHAOSArmSysReg   STXR判定──CHAOSExMon(chaos_exmon_g)       │
└────────────────────────────────────────────────────────────────────────────┘
        ▲ 全部注入器 = SimObject 插件（.py/.hh/.cc/SConscript 四文件自发现）
        ▲ 门控公约：prob→0短路 ‖ 时间窗(tick域) ‖ maxFaults ‖ Bernoulli
        ▲ 实验机器：campaign→manifest→runner→classify(六类)→escape(A-F)→fingerprint
```

## 附录：关键源码索引

| 主题 | 文件 | 关键位置 |
|---|---|---|
| 主仿真循环 | `src/sim/simulate.cc` | doSimLoop :292 / simulate :190 |
| 事件队列 | `src/sim/eventq.hh/.cc` | 优先级表 :126-244 / serviceOne(cc) :224 |
| SimObject 生命周期 | `src/sim/sim_object.hh` | 类 :146 / 生命周期注释 :72-89 |
| 实例化流程 | `src/python/m5/simulate.py` | _create_cpp_objects :147 / instantiate :220 |
| 构建自动发现 | `src/SConscript` | os.walk :570 |
| O3 阶段组合 | `src/cpu/o3/cpu.hh/.cc` | hook 指针区 :484-538 / tick :368 |
| 阶段间通信 | `src/cpu/o3/comm.hh` | TimeStruct :113 |
| 转发判定与 hook | `src/cpu/o3/lsq_unit.cc` | coverage :1440-1473 / memcpy :1502 / corrupt :1512 |
| 地址通路 hook | `src/cpu/o3/lsq.cc` | sendFragmentToTranslation :1135-1152 |
| PRF 内联 hook | `src/cpu/o3/regfile.hh` | 访问器 :167 / read-trace :185 / stuck :211 |
| 探活判据 | `src/cpu/o3/free_list.hh` | contains :110 / isFree :213 |
| IQ 唤醒 hook | `src/cpu/o3/inst_queue.cc` | wakeDependents :1078 / hook :1172 |
| spec_leak hook | `src/cpu/o3/rename.cc` | doSquash :935 / hook :963-976 |
| SE/FS 分界 | `src/arch/arm/mmu.cc` | gate :1212 / translateMmuOff :1005 |
| TLB hook | `src/arch/arm/tlb.cc` | :167-168 |
| PTW hook | `src/arch/arm/table_walker.cc` | :1954-1963 |
| SysReg/ExMon hook | `src/arch/arm/isa.cc` | :459-465 / :1934, :1966 |
| 假命中改道 | `src/mem/cache/tags/base.cc` | findBlock :94-107 |
| victim 毁伤 | `src/mem/cache/base.cc` | writebackBlk :1798-1805 |
| vaddr 原地改 | `src/mem/request.hh` | setVaddr :858 |
| 注入门控范本 | `src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc` | corrupt :281 / pickSource :139 / structural :203 |
| 物理cell注入 | `src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc` | processFault :164 / F3 :368 / read-trace 装订 :420 |
| 分类器 | `tools/classify.py` | classify_run :73 / 九类 :195 |
| 逃逸分解 | `tools/escape_decomp.py` | 机理表 :37-60 |
| 位谱指纹 | `tools/sdc_fingerprint.py` | 全文件 |

> 本文与其姊妹篇 `docs/gem5/project-understanding.md`（研究主线与定量结论）互为表里：本文讲"机器怎么造的"，彼篇讲"机器跑出了什么"。
