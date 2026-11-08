# gem5 O3CPU 执行链路教学笔记

本文面向已经能打开 gem5 源码、但还没有把 O3CPU 执行链路串起来的读者。目标不是复述乱序执行概念，而是回答一个更实用的问题：在本仓库 `CHAOS/gem5/src/cpu/o3/` 里，一条指令到底怎样从取指进入乱序核心，又怎样被执行、写回、提交、冲刷或传播到内存系统。

## 1. O3CPU 是什么模型

gem5 的 O3CPU 是一个事件驱动的、周期级的乱序 CPU 模型。它不是每个流水级一个宿主机线程，也不是简单地一次调用执行完一条目标机指令。它的核心形式是：

```text
gem5 event queue
    -> O3CPU tickEvent
        -> BAC.tick()
        -> Fetch.tick()
        -> Decode.tick()
        -> Rename.tick()
        -> IEW.tick()
        -> Commit.tick()
        -> advance all TimeBuffers
        -> decide whether schedule next CPU tick
```

入口在 `cpu/o3/cpu.cc`。构造函数里，CPU 注册了一个 `tickEvent`，优先级是 `Event::CPU_Tick_Pri`：

```cpp
tickEvent([this] { tick(); }, "O3CPU tick", false, Event::CPU_Tick_Pri)
```

见 `CHAOS/gem5/src/cpu/o3/cpu.cc:73`。每次 `CPU::tick()` 被事件队列调起，O3CPU 就前进一个 CPU 周期。真正的每拍调度在 `CHAOS/gem5/src/cpu/o3/cpu.cc:367`：

```cpp
bac.tick();
fetch.tick();
decode.tick();
rename.tick();
iew.tick();
commit.tick();

timeBuffer.advance();
fetchQueue.advance();
decodeQueue.advance();
renameQueue.advance();
iewQueue.advance();
activityRec.advance();
```

这段代码是理解 O3CPU 的坐标原点：**所有流水级都在同一个 CPU tick 里按固定顺序调用，然后统一推进 TimeBuffer**。这意味着某一级本拍写入的前向/后向信号，通常要经过配置的延迟后才被其它级看到。

## 2. CPU 对象里装了哪些部件

`cpu/o3/cpu.hh` 里的 `o3::CPU` 是总控对象。它包含：

```text
前端:
  BAC        Branch Address Calculator / 取指目标生成
  FTQ        Fetch Target Queue
  Fetch
  Decode

乱序核心:
  Rename
  IEW        Issue / Execute / Writeback
  Commit

核心结构:
  PhysRegFile
  FreeList
  ROB
  Scoreboard
  IQ         在 IEW 内
  LSQ        在 IEW 内

通信结构:
  timeBuffer
  fetchQueue
  decodeQueue
  renameQueue
  iewQueue
  activityRec
```

源码位置：

```text
cpu/o3/cpu.hh      O3CPU 总声明
cpu/o3/cpu.cc      构造、tick、线程管理、drain
cpu/o3/comm.hh     各流水级之间传递的结构体
cpu/o3/fetch.*     取指和 DynInst 创建
cpu/o3/decode.*    解码和早期分支目标修正
cpu/o3/rename.*    源/目的寄存器重命名、ROB/IQ/LSQ 资源检查
cpu/o3/iew.*       dispatch、issue、execute、writeback
cpu/o3/commit.*    ROB 头提交、异常、冲刷、精确状态
cpu/o3/rob.*       重排序缓冲区
cpu/o3/inst_queue.* 指令队列/唤醒选择
cpu/o3/lsq.*       Load/Store Queue 总封装
cpu/o3/lsq_unit.*  每线程 LSQ 具体执行
```

构造函数会把所有流水级连起来，关键代码在 `CHAOS/gem5/src/cpu/o3/cpu.cc:145` 到 `:181`。这里完成三件事：

```text
1. 每个 stage 拿到 activeThreads 指针
2. 每个 stage 拿到共享 timeBuffer
3. 相邻 stage 拿到自己的前向队列
```

例如：

```cpp
fetch.setFetchQueue(&fetchQueue);
decode.setFetchQueue(&fetchQueue);
decode.setDecodeQueue(&decodeQueue);
rename.setDecodeQueue(&decodeQueue);
rename.setRenameQueue(&renameQueue);
iew.setRenameQueue(&renameQueue);
iew.setIEWQueue(&iewQueue);
commit.setIEWQueue(&iewQueue);
```

这说明 O3CPU 的流水线不是靠函数直接调用传递指令，而是靠 `TimeBuffer<...>` 和 stage queue 传递 `DynInstPtr`。

## 3. TimeBuffer：O3CPU 的“流水线寄存器”

`cpu/o3/comm.hh` 定义了 O3CPU 级间通信的 payload。

前向路径：

```text
FetchStruct  : Fetch  -> Decode
DecodeStruct : Decode -> Rename
RenameStruct : Rename -> IEW
IEWStruct    : IEW    -> Commit
IssueStruct  : IQ     -> Execute
```

见 `CHAOS/gem5/src/cpu/o3/comm.hh:61` 到 `:110`。

后向控制路径都放在 `TimeStruct` 中，见 `CHAOS/gem5/src/cpu/o3/comm.hh:112`。它包含：

```text
fetchInfo
decodeInfo
renameInfo
iewInfo
commitInfo
decodeBlock / decodeUnblock
renameBlock / renameUnblock
iewBlock / iewUnblock
```

最重要的是 `commitInfo`，它从 Commit 向前端和中段广播：

```text
pc                 分支/异常/冲刷后的新 PC
mispredictInst     误预测指令
squashInst         触发 squash 的指令
doneSeqNum         已提交或已冲刷到的序列号
freeROBEntries     ROB 空闲项，给 Rename 做资源判断
squash             通知 Fetch/Decode/Rename/IEW 冲刷
robSquashing        ROB 正在逐步清理
interruptPending   全系统模式下前端停取
trapPending        异常处理挂起
strictlyOrdered    严格有序 load 需要在 commit 头部再执行
```

这就是乱序 CPU 的关键：前向数据流推动指令向后走，后向控制流负责停顿、释放资源、纠错和恢复精确状态。

## 4. 一条指令的前向生命周期

### 4.1 Fetch：取指并创建 DynInst

Fetch 的核心工作有两层：

```text
1. 从 PC/FTQ/BAC 指定的位置取 instruction bytes
2. 为每条静态指令创建一个动态实例 DynInst
```

`Fetch::buildInst()` 在 `CHAOS/gem5/src/cpu/o3/fetch.cc:1004`。它做了几件关键事：

```cpp
InstSeqNum seq = cpu->getAndIncrementInstSeq();
DynInstPtr instruction = new DynInst(..., seq, cpu);
instruction->setTid(tid);
instruction->setThreadState(cpu->thread[tid]);
instruction->setInstListIt(cpu->addInst(instruction));
fetchQueue[tid].push_back(instruction);
```

这里的 `seqNum` 非常重要。它是 O3CPU 内部给每条动态指令分配的单调递增序号。后续 ROB 排序、squash 范围、trace 关联、故障注入定位，基本都离不开它。

`Fetch::tick()` 在 `CHAOS/gem5/src/cpu/o3/fetch.cc:820`。每拍 Fetch 会：

```text
1. 查看 Decode/Rename/IEW/Commit 传回来的 stall/squash 信号
2. 选择活跃线程取指
3. 如有需要发起 I-cache 请求
4. 把 fetchQueue 中的 DynInst 按 decodeWidth 送到 Decode
```

Fetch 并不是“取到就立刻解码”。它先把 `DynInst` 放入本线程的 `fetchQueue`，再通过 `toDecode->insts[...]` 送入 `FetchStruct`。

### 4.2 Decode：解码和早期控制流修正

Decode 的每拍入口是 `CHAOS/gem5/src/cpu/o3/decode.cc:561`。它会：

```text
1. sortInsts() 从 FetchStruct 整理输入
2. 检查 Rename/IEW/Commit 的 stall 或 squash
3. 对每个线程调用 decode()
4. 将解码后的 DynInst 写入 DecodeStruct，送给 Rename
```

Decode 还会处理一部分早期分支目标校验。典型代码在 `CHAOS/gem5/src/cpu/o3/decode.cc:720`。如果直接控制流指令的预测目标不对，Decode 会调用 `squash()`，让前端重定向。

所以 Decode 不只是“翻译指令格式”，它也是前端误预测修正的一道早期过滤器。

### 4.3 Rename：从架构寄存器进入物理寄存器世界

Rename 的每拍入口是 `CHAOS/gem5/src/cpu/o3/rename.cc:426`。它先检查后向信号，再调用 `rename()`。

最关键的流程在 `CHAOS/gem5/src/cpu/o3/rename.cc:745`：

```cpp
renameSrcRegs(inst, inst->threadNumber);
renameDestRegs(inst, inst->threadNumber);
```

这里发生了 O3 的核心转换：

```text
架构源寄存器 -> 当前 rename map 中的物理寄存器
架构目的寄存器 -> 从 freeList 分配新的物理寄存器
旧目的映射 -> 保存为 previous mapping，等 Commit 后释放
```

Rename 还负责资源门控。它必须确认：

```text
ROB 有空项
IQ 有空项
LQ/SQ 有空项
FreeList 有足够物理寄存器
序列化/屏障指令条件满足
```

通过 Rename 后，指令被写入 `RenameStruct`：

```cpp
toIEW->insts[toIEWIndex] = inst;
++toIEW->size;
```

这一步之后，指令已经带着物理源/目的寄存器进入乱序执行域。

### 4.4 IEW：Issue / Execute / Writeback 合并阶段

IEW 是 O3CPU 中最厚的一层。入口在 `CHAOS/gem5/src/cpu/o3/iew.cc:1429`。

每拍大致顺序：

```text
1. ldstQueue.tick()
2. sortInsts() 接收 RenameStruct
3. FUPool 释放本拍完成的功能单元
4. dispatch() 把指令放入 IQ/LSQ
5. executeInsts() 执行从 IQ 选出的 ready 指令
6. writebackInsts() 将完成的结果发往 Commit
7. instQueue.scheduleReadyInsts() 调度下一拍要执行的 ready 指令
8. issueToExecQueue.advance()
9. 处理 Commit 反馈，释放 IQ/LSQ 中已提交指令
```

注意名字叫 IEW，但它内部还包含 dispatch。Rename 送来的指令先进入 IEW，再被插入 IQ 和 LSQ。普通 ALU 指令进入 IQ；load/store 也会进入 LSQ，并和 IQ 的 ready/scheduling 协同。

当指令开始执行时，IEW 会触发 Execute probe。相关代码在 `CHAOS/gem5/src/cpu/o3/iew.cc:1159`：

```cpp
DynInstPtr inst = instQueue.getInstToExecute();
ppExecute->notify(inst);
```

当执行完成、准备送 Commit 时，IEW 通过 `toCommit` 写入 `IEWStruct`。相关代码在 `CHAOS/gem5/src/cpu/o3/iew.cc:1387`：

```cpp
DynInstPtr inst = toCommit->insts[inst_num];
ppToCommit->notify(inst);
```

### 4.5 Commit：ROB 头部按程序顺序退休

Commit 的每拍入口在 `CHAOS/gem5/src/cpu/o3/commit.cc:600`。它的职责是让乱序执行重新变成精确架构状态：

```text
1. 检查 ROB squash 是否完成
2. 尝试提交 ROB 头部 ready 指令
3. 处理 fault / trap / interrupt
4. 释放旧物理寄存器
5. 更新提交统计和 probe
6. 向前端/IEW/Rename 广播 doneSeqNum、freeROBEntries、squash 等控制信号
```

真正提交 ROB 头部的逻辑在 `CHAOS/gem5/src/cpu/o3/commit.cc:940`。关键判定：

```text
只有 ROB head 且 readyToCommit 的指令才能 commit
被 squash 的指令可以从 ROB 中退休，但不会成为架构状态
有 fault 的指令在 commit 处触发精确异常
```

成功提交时：

```cpp
bool commit_success = commitHead(head_inst, num_committed);
if (commit_success) {
    ppCommit->notify(head_inst);
}
```

这就是 O3CPU 保证精确异常和按程序顺序可见的地方：前面可以乱序执行，但最后只能按 ROB 顺序提交。

## 5. Load/Store 链路：O3CPU 和内存系统的交界

Load/Store 是 O3CPU 里最容易读晕的一段，因为它横跨：

```text
IEW
InstructionQueue
LSQ
TLB/MMU
D-cache
memory response
writeback
Commit
```

`LSQUnit::executeLoad()` 在 `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:607`。核心入口是：

```cpp
load_fault = inst->initiateAcc();
```

这会让指令根据 ISA 语义发起访存访问，可能经历地址生成、地址翻译、cache 请求等。如果翻译延迟或 cache miss，load 不会本拍完成。

当内存响应回来时，`LSQUnit::writeback()` 在 `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1101`：

```cpp
if (!inst->isExecuted()) {
    inst->setExecuted();
    if (inst->fault == NoFault) {
        inst->completeAcc(pkt);
    }
}
iewStage->instToCommit(inst);
iewStage->checkMisprediction(inst);
```

这里完成两件大事：

```text
1. 把 load 返回数据写入目标寄存器或指令结果
2. 把该指令送往 Commit，等待 ROB 头部提交
```

Store 则不同。Store 的地址/数据可以先准备好，但真正对内存系统可见通常要等 Commit 允许之后。这样可以避免错误路径 store 污染架构内存状态。

## 6. 反压、阻塞和冲刷

O3CPU 不是每拍所有级都顺畅推进。任一级资源不足或控制流出错，都会通过后向信号影响前面的级。

常见阻塞源：

```text
Fetch 受 I-cache miss、interrupt、Decode stall 影响
Decode 受 Rename stall 影响
Rename 受 ROB/IQ/LSQ/FreeList 资源影响
IEW 受 IQ/LSQ/FU/cache miss 影响
Commit 受 ROB head not ready、fault、trap、squash 影响
```

常见恢复源：

```text
Decode 发现早期 branch target 错误
IEW 发现执行后 branch mispredict
LSQ 发现内存次序违例
Commit 处理 fault/trap/interrupt
Commit 发起 ROB squash
```

在代码里，冲刷范围通常由 `seqNum` 边界表达：

```text
保留某条 older 指令及其以前的状态
清理 younger 指令
恢复 PC / rename map / ROB / IQ / LSQ
```

Commit 的 `commitInfo[tid].doneSeqNum` 会告诉前级某个序列号之前的状态已经安全，或者某个序列号之后的状态需要清理。

## 7. ActivityRecorder：为什么 CPU 会停表

O3CPU 不会无意义地每拍自旋。每个 stage 如果本拍做了有意义的事情，会调用：

```cpp
cpu->activityThisCycle();
```

CPU tick 末尾检查 `activityRec.active()`。如果没有活动，CPU 可以不再调度下一拍 tick，进入 idle。见 `CHAOS/gem5/src/cpu/o3/cpu.cc:406`：

```cpp
if (!tickEvent.scheduled()) {
    if (!activityRec.active() || _status == Idle) {
        ...
    } else {
        schedule(tickEvent, clockEdge(Cycles(1)));
    }
}
```

当 cache response、线程唤醒、中断等外部事件到来，会调用 `wakeCPU()`，重新把 `tickEvent` 放回事件队列。见 `CHAOS/gem5/src/cpu/o3/cpu.cc:1336`。

这也是为什么 gem5 是事件驱动模拟器：CPU 周期本身也是一个事件，没活动时可以暂停。

## 8. O3CPU 中可用的追踪点

如果要做教学观察、ACE/IBR 指标或 CHAOS 故障传播追踪，最自然的锚点是 O3 ProbePoint。

已有典型 probe：

```text
Fetch      fetch.cc
Rename     rename.cc
Dispatch   iew.cc
Execute    iew.cc
ToCommit   iew.cc
Commit     commit.cc
Squash     commit.cc
CommitStall commit.cc
```

例子：

```cpp
ppExecute->notify(inst);
ppToCommit->notify(inst);
ppCommit->notify(head_inst);
ppSquash->notify(head_inst);
```

现有 `ElasticTrace` 就是一个很好的样板。它是一个 `ProbeListenerObject`，监听 O3 多个阶段，记录指令时间戳和依赖信息，并输出 protobuf trace。见 `CHAOS/gem5/src/cpu/o3/probe/elastic_trace.hh:72`。

如果要新增 `ACEIBRTracker`，建议不要把所有统计都塞进 `cpu.cc`。更好的方式是：

```text
ACEIBRTracker : ProbeListenerObject
    listen Fetch/Rename/Dispatch/Execute/ToCommit/Commit/Squash
    use seqNum as primary key
    add small hooks in PhysRegFile/LSQ only where ProbePoint 不够用
```

这样能保持 O3CPU 主链路干净，也方便开关和复用。

## 9. CHAOS 在 O3CPU 上的常见 hook 位置

本仓库的 CHAOS 扩展已经沿着 O3 执行链路布了不少注入点。它们大体分成几类：

```text
Rename/RAT:
  CHAOSRenameMap
  CHAOSFreeList

ROB/IQ:
  CHAOSROB
  CHAOSIQ

PRF/寄存器:
  CHAOSPhysReg

执行/写回:
  CHAOSExec
  CHAOSFPU

LSQ/转发/地址路径:
  CHAOSLSQFwd
  CHAOSAddrPath
  CHAOSL1DForward
```

这正好对应 O3CPU 的几个脆弱边界：

```text
rename map 是否指向正确物理寄存器
free list 是否错误释放/复用寄存器
IQ/ROB 是否错误调度或提交
PRF 值是否被污染
执行单元结果是否错误
load 返回路径/Store-to-Load forwarding 是否错源或错位
地址翻译前后的地址是否被污染
```

如果你在读 SDC 或 ACE/IBR 相关代码，建议按执行链路从前到后定位，而不是按注入器名字跳着读。

## 10. 用一张图记住完整链路

```text
                    后向控制/恢复路径
      +-------------------------------------------------------------+
      | squash / stall / free entries / doneSeqNum / redirect PC    |
      v                                                             |
+-----+--+   +--------+   +--------+   +--------+   +------+   +--------+
|  BAC   |-->| Fetch  |-->| Decode |-->| Rename |-->| IEW  |-->| Commit |
+--------+   +--------+   +--------+   +--------+   +------+   +---+----+
    |            |            |            |           |           |
    v            v            v            v           v           v
   FTQ       DynInst       decoded      phys regs     IQ/LSQ      ROB head
             seqNum                    ROB alloc     execute     precise state
                                         freeList     writeback   arch visible
                                                    FU/cache/MMU
```

更细一点：

```text
Fetch:
  PC/FTQ -> I-cache -> StaticInst -> DynInst(seqNum) -> fetchQueue

Decode:
  fetchQueue -> DecodeStruct -> early branch target check

Rename:
  arch src -> phys src
  arch dst -> new phys dst
  allocate ROB/IQ/LSQ resources
  -> RenameStruct

IEW:
  dispatch -> IQ/LSQ
  wakeup/select -> FU execute
  load/store -> LSQ -> TLB/MMU/cache
  writeback -> IEWStruct

Commit:
  wait ROB head ready
  commit in program order
  handle fault/trap
  release old phys regs
  broadcast doneSeqNum/free entries/squash
```

## 11. 读源码的推荐路线

第一次读，不建议从 `dyn_inst.hh` 或 `lsq_unit.cc` 直接扎进去。推荐顺序：

```text
1. cpu/o3/cpu.hh
   看 CPU 包含哪些 stage 和共享结构。

2. cpu/o3/cpu.cc
   看构造函数如何接线，再看 CPU::tick()。

3. cpu/o3/comm.hh
   看 FetchStruct/DecodeStruct/RenameStruct/IEWStruct/TimeStruct。

4. cpu/o3/fetch.cc
   看 buildInst() 和 Fetch::tick()。

5. cpu/o3/rename.cc
   看 renameSrcRegs()/renameDestRegs() 调用点。

6. cpu/o3/iew.cc
   看 IEW::tick()，再分开读 dispatch/execute/writeback。

7. cpu/o3/commit.cc
   看 Commit::tick() 和 commit()，理解 ROB head 提交。

8. cpu/o3/lsq_unit.cc
   最后读 load/store，因为它横跨 ISA、MMU、cache 和 commit。
```

读的时候抓住三个主键：

```text
DynInstPtr  指令对象本体
seqNum      指令时序和 squash 边界
ThreadID    SMT/线程维度
```

再抓住两个方向：

```text
前向: instruction/data movement
后向: control/resource/recovery movement
```

有了这五个抓手，O3CPU 的执行链路就会从“一堆文件”变成一台能在脑子里转起来的机器。

