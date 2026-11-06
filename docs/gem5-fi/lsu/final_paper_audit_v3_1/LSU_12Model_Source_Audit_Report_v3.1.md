# LSU 12 模型源码审计报告 v3

**源码**：`/home/sdc/gem5-fi-ding/CHAOS/gem5`，HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`。
**基准**：`gem5-fi-LSU最终论文实验方案` v2.2.1；**性质**：只读审计，未改源码/未编译/未运行。

## 0. 摘要

| 指标 | 结果 |
|---|---|
| 源码路径核实 | 12/12 VERIFIED |
| 当前可直接运行 | 0/12 |
| 工作负载可运行 | 3/12（A01/A03→W1；FW02→W4） |
| 需新增/修改Hook | 11/12（LP01/FW05为PARTIAL） |
| 60 SampleRunID可追溯 | 60/60 |
| 需研究者确认的精确语义 | 12/12 |

**证据等级**：VERIFIED=源码已核对；TECHNICAL_JUDGMENT=基于源码的工程判断；DESIGN_PROPOSAL=未实现Hook设计；NEEDS_USER_DECISION=需研究者选项确认。

## 1. 逐模型

### A01 — Effective Address 单比特翻转（AGU）

- 候选SubTaskID：`A01-F0-W1-S01`（RunID `A01-F0-W1`，模式 F0，负载 W1）
- 最终故障定义：唯一正式Hook=pushRequest；sendFragmentToTranslation是split后逐fragment，不是AGU输出，不选
- 注入位置：AGU EA输出→LSQ pushRequest入口（唯一正式Hook）
- 源码：`CHAOS/gem5/src/cpu/o3/lsq.cc; CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc; CHAOS/gem5/src/arch/arm/isa/insts/ldr64.isa`
- 类/函数：LSQ::LSQRequest; Request; CHAOSAddrPath；LSQ::pushRequest (lsq.cc:764-878); LSQRequest::sendFragmentToTranslation (lsq.cc:1166-1199); CHAOSAddrPath::maybeCorrupt (CHAOSAddrPath.cc:102-204)
- 成员/类型/位宽：Request::_vaddr; DynInst::effAddr；Addr (uint64_t)；64
- 正常值→故障值：AGU原始EA → EA ^ 0x8
- 目标字段/索引：pushRequest addr (Addr 64)；bit 3（低位段0-15）
- 注入时机/持续时间：pushRequest入口，split/Request构造前；F0单次；错误EA随Request进入翻译/访存
- 目标指令/触发条件：Load地址生成（必须加Load过滤）；目标Load完成AGU地址生成并被pushRequest接收
- 传播路径：AGU→LSQ→DTLB→L1D→Load响应→RF/WB→消费者→Commit
- 现有Hook：CHAOSAddrPath a01_bit（部分；band随机、无Load过滤）；需修改：CHAOSAddrPath增加band/op参数；lsq.cc注入点记录PC/seq/lqIdx/request_id
- 实现状态：NEEDS_HOOK；工作量：READY；难度/风险：低-中；当前无法固定低位段与Load方向；SE下VA→PA平坦，地址错误可能不触发翻译异常
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：READY
- **Options（NEEDS_USER_DECISION）**：A: bit3（推荐）；B: bit0；C: bit7；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §A01`

### A03 — Effective Address 永久性错误（Stuck-at）（AGU）

- 候选SubTaskID：`A03-F5-W1-S01`（RunID `A03-F5-W1`，模式 F5，负载 W1）
- 最终故障定义：一个SampleRun一个固定故障源；R01-R05同一bit/value；不得描述为物理寄存器永久锁存
- 注入位置：AGU EA输出→LSQ pushRequest入口（F5持续条件）
- 源码：`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc; CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh; CHAOS/gem5/src/cpu/o3/lsq.cc`
- 类/函数：CHAOSAddrPath; ChaOSLsuTrigger; LSQ::LSQRequest；CHAOSAddrPath::maybeCorrupt (158-166); ChaOSLsuTrigger::onEligible F5 (156-161); sendFragmentToTranslation (1166-1199)
- 成员/类型/位宽：Request::_vaddr; f5_bit；Addr (uint64_t)；64（bit 0-47随机）
- 正常值→故障值：EA bit3 → EA & ~0x8
- 目标字段/索引：pushRequest addr (Addr 64)；bit3 stuck-at-0，Load-only
- 注入时机/持续时间：每个eligible Load的pushRequest入口；从首个post-warmup eligible Load到运行结束；逐事件重施加，不是物理锁存
- 目标指令/触发条件：Load（必须加Load过滤）；每个符合条件的Load地址生成
- 传播路径：AGU→LSQ→DTLB→L1D→多请求→Commit/软件
- 现有Hook：CHAOSAddrPath a03_stuck0/a03_stuck1（部分）；需修改：增加band/op过滤；明确F5是逐事件重施加而非锁存；记录受影响dyn_inst_seq
- 实现状态：NEEDS_HOOK；工作量：READY；难度/风险：中；把逐事件重施加误称为永久硬件状态；bit随机；无op过滤
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：READY
- **Options（NEEDS_USER_DECISION）**：A: 逐eligible事件重施加bit3=0（推荐，非锁存）；B: 实现物理锁存状态（需新增结构）；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §A03`

### LQ04 — Load Queue Entry 生命周期错误（LQ）

- 候选SubTaskID：`LQ04-F0-W2-S01`（RunID `LQ04-F0-W2`，模式 F0，负载 W2）
- 最终故障定义：原'提前free+重用'子模型在gem5无安全pop任意entry接口；先做提前失效，重用子模型BLOCKED
- 注入位置：LQEntry生命周期：executeLoad后提前失效
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/lsq_unit.hh`
- 类/函数：LSQUnit::LSQEntry; LSQUnit；LSQUnit::insertLoad (353-414); commitLoad (775-798); squash (986-1020); clear/pop_front
- 成员/类型/位宽：LQEntry::_valid; _request; loadQueue；bool; LSQRequest*; CircularQueue<LQEntry>；1; 64; 64(index)
- 正常值→故障值：valid=1，request在途 → executeLoad后清valid/request；不pop、不复用
- 目标字段/索引：LQEntry::_valid / _request；目标lqIdx；entry_generation
- 注入时机/持续时间：executeLoad后、响应到达前；F0单次；目标entry保持无效到commit/squash
- 目标指令/触发条件：Load（目标lqIdx）；目标Load已分配LQ entry并发出request
- 传播路径：LQ entry→request/response→replay/commit；错误可导致响应错配或丢失
- 现有Hook：无；需修改：lsq_unit.cc增加LQ生命周期Hook；LQEntry增加entry_generation；trace记录lqIdx/seq
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：中-高；响应到达前释放会破坏request/response配对；W2缺失
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: 仅提前失效（推荐，可审计）；B: 提前pop并复用（需结构性修改，BLOCKED）；C: 正常commitLoad释放（不是故障）；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §LQ04`

### SQ01 — Store 数据错误（SQ）

- 候选SubTaskID：`SQ01-F0-W3-S01`（RunID `SQ01-F0-W3`，模式 F0，负载 W3）
- 最终故障定义：原始低/中/高位与单/双bit歧义；R01-R05同一byte/bit
- 注入位置：SQ entry数据：write()写入后
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/lsq_unit.hh; CHAOS/gem5/src/cpu/o3/dyn_inst.hh`
- 类/函数：LSQUnit::SQEntry; LSQUnit; DynInst；LSQUnit::write() (1729-1756); writebackStores() (847-977)，数据复制905-911
- 成员/类型/位宽：SQEntry::_data; DynInst::memData；char[MaxVecRegLenInBytes]; uint8_t*；65536 B; size×8
- 正常值→故障值：Store原始byte0 → byte0 ^ 0x08
- 目标字段/索引：SQEntry::_data[0]；byte0 bit3
- 注入时机/持续时间：write() memcpy后、writeback/forwarding前；F0单次；错误数据留在SQ entry
- 目标指令/触发条件：Store（目标sqIdx）；目标Store已写SQ entry
- 传播路径：SQ→FWD/Load或writeback→L1D→Memory→消费者
- 现有Hook：无（CHAOSLSQFwd只改load侧转发拷贝）；需修改：lsq_unit.cc write()/writebackStores()增加数据Hook；记录sqIdx/request_id/commit_seq
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：中；未被转发的Store当前无法注入；W3缺失
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: 单bit byte0 bit3（推荐）；B: 单bit byte0 bit0；C: 双bit byte0 bit3-4；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §SQ01`

### SQ03 — Store Queue 状态错误（SQ）

- 候选SubTaskID：`SQ03-F0-W3-S02`（RunID `SQ03-F0-W3`，模式 F0，负载 W3）
- 最终故障定义：_committed只在writebackStores assert，不参与关键控制；_canWB控制writebackStores/willWB；_completed控制completeStore/pop
- 注入位置：SQ状态：_canWB提前置位
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.hh; CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- 类/函数：LSQUnit::SQEntry; LSQUnit；executeStore (763-769); commitStores (811-835); completeStore (1197-1255)
- 成员/类型/位宽：SQEntry::_canWB; _committed; _completed；bool；1 each
- 正常值→故障值：0（normal Store在commitStores才置1） → executeStore时置1（提前可写回）
- 目标字段/索引：SQEntry::_canWB；1 bit
- 注入时机/持续时间：executeStore后；F0单次；状态保持到writeback/completeStore
- 目标指令/触发条件：Store（目标sqIdx）；目标Store执行完成、尚未commit
- 传播路径：SQ→writebackStores→completeStore→Commit
- 现有Hook：无；需修改：lsq_unit.cc状态位写入点增加Hook；trace记录state_before/after
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：中；状态错乱可能导致writeback顺序/释放错误；W3缺失
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: _canWB提前true（推荐）；B: _completed提前true；C: _committed（拒绝：仅assert/bookkeeping，不控制释放）；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §SQ03`

### LP01 — Load 返回数据错误（LP）

- 候选SubTaskID：`LP01-F0-W5-S01`（RunID `LP01-F0-W5`，模式 F0，负载 W5）
- 最终故障定义：必须修复现有 uint64_t* 8字节访问；size<8时越界；R01-R05同一byte/bit；Trace增加Post-Injection事件
- 注入位置：Load响应数据：completeDataAccess前
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc`
- 类/函数：LSQUnit; CHAOSL1DForward; Packet；LSQUnit::completeDataAccess (107-214); writeback (1135-1195); CHAOSL1DForward::maybeCorrupt (60-140)
- 成员/类型/位宽：Packet::data; DynInst::memData；uint8_t*；size×8
- 正常值→故障值：正常响应byte0 → data[0] ^= 0x08（严格按size逐字节）
- 目标字段/索引：Packet::data[0]；byte0 bit3
- 注入时机/持续时间：completeDataAccess前、writeback前；F0单次；错误数据进入Load结果
- 目标指令/触发条件：Load（目标lqIdx）；目标Load响应到达
- 传播路径：L1D→LSQ→RF/WB→消费者→Commit
- 现有Hook：CHAOSL1DForward（部分：仅响应数据翻转）；需修改：增加PC/seq/lqIdx/request_id日志；扩展mask到全size；接入propagation tracer
- 实现状态：PARTIAL；工作量：BLOCKED；难度/风险：中；只覆盖数据，不覆盖身份/时序；W5缺失；传播链未接入
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：PARTIAL；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: byte0 bit3（推荐）；B: byte0 bit0；C: byte0 bit7；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §LP01`

### SP05 — Store 完成/响应状态异常（SP）

- 候选SubTaskID：`SP05-F6-W6-S01`（RunID `SP05-F6-W6`，模式 F6，负载 W6）
- 最终故障定义：gem5无独立Store Ack；completeStore控制_completed/storesToWB/释放；不虚构Ack结构
- 注入位置：Store完成记账：completeStore
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/lsq_unit.hh; CHAOS/gem5/src/mem/packet.hh`
- 类/函数：LSQUnit; SQEntry；storePostSend (1104-1133); completeStore (1197-1255); recvRetry (1332-1339); trySendPacket (1257-1297)
- 成员/类型/位宽：storeInFlight; retryPkt; SQEntry::_completed；bool; PacketPtr; bool；1; 64; 1
- 正常值→故障值：响应后completeStore置_completed=1、--storesToWB、可pop → 抑制一次completeStore/_completed更新
- 目标字段/索引：SQEntry::_completed / storesToWB；目标sqIdx
- 注入时机/持续时间：响应到达后completeStore调用点；F6单次；SQ entry无法释放，可能backpressure/HANG
- 目标指令/触发条件：Store（目标sqIdx）；目标Store响应到达/完成事件
- 传播路径：Store→Cache/L1D→completeStore→Commit；丢失可能导致Hang/Timeout
- 现有Hook：无；需修改：lsq_unit.cc完成路径增加Hook；定义ack丢失/重复的受控语义
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：高；原模型“Ack”与gem5实际完成机制不一致；可能死锁；W6缺失
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: Store queue completion bookkeeping failure（推荐，重命名）；B: 保留Ack名称但标NOT_IMPLEMENTED；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §SP05`

### FW02 — Store-to-Load Forwarding False Miss（FWD）

- 候选SubTaskID：`FW02-F6-W4-S01`（RunID `FW02-F6-W4`，模式 F6，负载 W4）
- 最终故障定义：W4构造真实同地址对；记录候选、期望/实际数据来源
- 注入位置：Forwarding匹配判定：read()覆盖判断
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- 类/函数：LSQUnit；LSQUnit::read() (1376-1727); 地址覆盖判定 (1465-1508); full coverage (1510-1646); partial (1647-1684)
- 成员/类型/位宽：store_it; AddrRangeCoverage; shift_amt; load_inst->memData；iterator; enum; uint32_t; uint8_t*；N/A; 32; size×8
- 正常值→故障值：FullAddrRangeCoverage → NoAddrRangeCoverage一次
- 目标字段/索引：AddrRangeCoverage result；目标Load/Store同地址对
- 注入时机/持续时间：read() forwarding判定；F6单次；该Load数据来源改变
- 目标指令/触发条件：Load（与older Store同地址）；目标Load遇到同地址older Store
- 传播路径：SQ→FWD判定→L1D/Memory→Load数据→RF/WB→Commit
- 现有Hook：无（CHAOSLSQFwd只改已转发数据/源选择）；需修改：lsq_unit.cc覆盖判定处增加Hook；记录候选store/真实源/选中源
- 实现状态：NEEDS_HOOK；工作量：READY；难度/风险：高；必须构造真实同地址Store；W4可触发；错误可能只影响性能而非SDC
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：READY
- **Options（NEEDS_USER_DECISION）**：A: 同地址8B Store→Load（推荐）；B: 部分重叠对；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §FW02`

### FW05 — 部分重叠数据拼接错误（FWD）

- 候选SubTaskID：`FW05-F6-W8-S01`（RunID `FW05-F6-W8`，模式 F6，负载 W8）
- 最终故障定义：原部分重叠拼接错误不可实现；改为错误源选择，保留ID，需研究者确认语义变更
- 注入位置：Forwarding源选择：CHAOSLSQFwd::maybeSubstituteSource
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- 类/函数：LSQUnit；LSQUnit::read() full coverage memcpy (1552-1555); partial coverage (1647-1684); shift_amt (1512-1513)
- 成员/类型/位宽：load_inst->memData; store_it->data(); shift_amt; size；uint8_t*; char*; uint32_t；size×8; 32
- 正常值→故障值：true_src=最年轻匹配Store → copy alt_src=较老Store数据
- 目标字段/索引：store_it._idx / alt_src；较老SQ entry索引
- 注入时机/持续时间：full-coverage转发决定后、memcpy前；F6单次；错误数据进入Load
- 目标指令/触发条件：Load（同地址/部分重叠，多个候选Store）；目标Load存在多个候选Store
- 传播路径：SQ→FWD merge→Load数据→RF/WB→Commit
- 现有Hook：无（byte_lane_skew仅整buffer旋转）；需修改：lsq_unit.cc merge处增加Hook；记录逐字节source map
- 实现状态：PARTIAL；工作量：BLOCKED；难度/风险：高；必须构造真实部分重叠；W8缺失；错误可能被后续覆盖
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：PARTIAL；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: Wrong-source forwarding（推荐，现有Hook）；B: 原部分重叠拼接（源码无多Store拼接路径，NOT SUPPORTED/BLOCKED）；C: 删除FW05（不允许）；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §FW05`

### MD04 — Memory Dependency 漏报（MD）

- 候选SubTaskID：`MD04-F6-W7-S01`（RunID `MD04-F6-W7`，模式 F6，负载 W7）
- 最终故障定义：只抑制possibleLoadViolation一次；不混用依赖预测错误；记录正常/故障路径
- 注入位置：Violation检测：checkViolations
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc; CHAOS/gem5/src/cpu/o3/store_set.cc`
- 类/函数：LSQUnit; MemDepUnit; StoreSet；checkViolations (550-636); checkSnoop (467-548); MemDepUnit::violation; StoreSet::violation/checkInst
- 成员/类型/位宽：memDepViolator; possibleLoadViolation; memDeps; depCheckShift；DynInstPtr; bool; int; unsigned；64; 1; 32; 32
- 正常值→故障值：检测到alias后possibleLoadViolation=true → 跳过一次置位
- 目标字段/索引：possibleLoadViolation；目标Load/Store alias
- 注入时机/持续时间：checkViolations地址范围匹配时；F6单次；错误Load可继续执行/提交
- 目标指令/触发条件：年轻Load vs 较老Store（同地址）；真实同地址alias且正常应触发violation
- 传播路径：MD check→issue/replay→Load数据→Commit
- 现有Hook：CHAOSLSQFwd violationCorrupt（只改比较地址）；需修改：lsq_unit.cc checkViolations/MemDepUnit增加Hook；记录alias/violation结果
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：高；W7缺失；强制false negative可能造成SDC；需构造真实alias
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: 同地址8B alias漏报（推荐）；B: 部分重叠alias漏报；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §MD04`

### RP01 — Replay 触发丢失（RPL）

- 候选SubTaskID：`RP01-F6-W7-S01`（RunID `RP01-F6-W7`，模式 F6，负载 W7）
- 最终故障定义：记录execution_attempt_id/replay_generation；区分MD04漏报
- 注入位置：Replay触发：partial-forward rescheduleMemInst
- 源码：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc; CHAOS/gem5/src/cpu/o3/iew.cc; CHAOS/gem5/src/cpu/o3/inst_queue.cc; CHAOS/gem5/src/cpu/o3/mem_dep_unit.cc`
- 类/函数：LSQUnit; IEW; InstructionQueue; MemDepUnit；checkViolations (550-636); IEW::rescheduleMemInst (iew.cc:563-567); IQ::rescheduleMemInst (inst_queue.cc:1323-1334); MemDepUnit::reschedule (380-384)
- 成员/类型/位宽：memDepViolator; instsToReplay; retryMemInsts；DynInstPtr; list; queue；64; N/A
- 正常值→故障值：partial forward时reschedule/replay → 跳过一次rescheduleMemInst
- 目标字段/索引：IEW::rescheduleMemInst call；目标Load/stallingLoadIdx
- 注入时机/持续时间：read() partial coverage分支；F6单次；Load不被重放
- 目标指令/触发条件：部分重叠Store→Load的年轻Load；目标Load命中PartialAddrRangeCoverage
- 传播路径：MD detect→Replay→re-execute→Commit/Squash
- 现有Hook：无；需修改：iew.cc/inst_queue.cc/MemDepUnit增加replay Hook；记录replay_id/target
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：高；W7缺失；抑制replay可能导致SDC或Hang
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: partial-forward replay丢失（推荐）；B: strict-order replay丢失；C: violation/snoop replay丢失；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §RP01`

### DA04 — Byte-enable 错误（ALIGN）

- 候选SubTaskID：`DA04-F0-W8-S02`（RunID `DA04-F0-W8`，模式 F0，负载 W8）
- 最终故障定义：bit0对应vaddr+0字节；小端不改变mask索引映射；必须实际修改Request mask；不同时改size/address
- 注入位置：Byte-enable构造：Request::setByteEnable前
- 源码：`CHAOS/gem5/src/cpu/o3/lsq.cc; CHAOS/gem5/src/cpu/o3/lsq.hh; CHAOS/gem5/src/mem/request.hh`
- 类/函数：LSQ::LSQRequest; Request；LSQ::pushRequest (764-878); _byteEnable构造 (833-834); addReq (1114-1149); SplitDataRequest::initiateTranslation (993-1060)
- 成员/类型/位宽：LSQRequest::_byteEnable; Request::_byteEnable；std::vector<bool>；size bits（每字节1 bit）
- 正常值→故障值：1111 (0xF) → 1110 (0xE)
- 目标字段/索引：Request::_byteEnable；4-bit mask bit0（地址最低字节）
- 注入时机/持续时间：pushRequest/addReq构造Request时；F0单次；错误mask进入Cache/Memory
- 目标指令/触发条件：4B Load/Store；目标访存size=4且mask全1
- 传播路径：LSQ→DTLB→L1D→data merge→RF/WB或Memory
- 现有Hook：无（PRE hook明确不能改byte_enable）；需修改：lsq.cc pushRequest/addReq增加可写byte-enable Hook；记录mask before/after
- 实现状态：NEEDS_HOOK；工作量：BLOCKED；难度/风险：中-高；const ref限制；错误mask可能触发断言；W8缺失
- **SourceAuditStatus：VERIFIED**；ImplementationStatus：NEEDS_HOOK；Workload：BLOCKED
- **Options（NEEDS_USER_DECISION）**：A: 清除bit0（0xF→0xE，推荐）；B: 清除bit3（0xF→0x7）；C: 8B清除bit0（0xFF→0xFE）；推荐 A
- 代码证据：`LSU_Source_Code_Evidence_v3.md §DA04`

## 2. 关键源码判断

- **A01 Hook唯一性**：`DynInst::initiateMemRead/writeMem` 把 ISA 计算的 EA 交给 `LSQ::pushRequest`；`sendFragmentToTranslation` 是 split 后逐 fragment 的翻译前点，不是 AGU 原始 EA 输出。因此正式 Hook 选 `pushRequest` 入口。
- **A03 F5语义**：`CHAOSAddrPath` 在 F5 下每个 eligible 事件重新施加 pin 住的 bit；这是“持续故障条件”，不是硬件锁存状态。
- **LQ04**：`insertLoad` 分配、`commitLoad` 在队列头释放、`squash` 清理；gem5 无安全 pop 任意 entry 的接口，因此只定义“提前失效”，不定义“提前 pop+重用”。
- **SQ03**：`_committed` 只在 `writebackStores` 的 `assert(!storeWBIt->committed())` 和 `committed()=true` 出现，**不控制SQ释放**；`_canWB` 控制 `writebackStores/willWB`；`_completed` 控制 `completeStore/pop`。正式模型选 `_canWB` 提前置1。
- **LP01**：现有 `uint64_t* p = reinterpret_cast<uint64_t*>(data); n=sz/8; if(n==0)n=1;` 在 size<8 时越界；必须改为逐字节操作。
- **SP05**：gem5 无独立 Store Ack；`completeStore` 设置 `_completed`、递减 `storesToWB` 并 pop；模型重定义为 Store queue completion bookkeeping failure。
- **FW05**：`maybeSubstituteSource` 已实现“从较老SQ entry复制数据”的真实错误源选择；原“部分重叠多Store拼接”在源码中不存在（partial coverage 是 stall/reschedule），因此原语义 BLOCKED，建议改为 wrong-source forwarding。



## v3.1 补充修正

- **A01/A03 实际实现位置冲突**：当前 `a01_bit`/`a03_stuck` 走的是 `sendFragmentToTranslation` 的 POST hook；第三轮建议的 `pushRequest` PRE hook **没有对应 a01/a03 模式**。要使用 pushRequest，必须新增 PRE 模式；在此之前两模型为 `NEEDS_HOOK`，不能标记 READY。
- **LQ04**：`LSQEntry::clear()` 会调用 `_request->freeLSQEntry()`；提前 clear 会释放在途请求资源，安全性未证明。只提出“提前失效、不主动 pop/reuse”，并标记 `NEEDS_USER_DECISION`。
- **RP01**：仅抑制 `rescheduleMemInst` 不足；`storePostSend`/`completeStore` 仍可能对 `stallingLoadIdx` 调用 `replayMemInst`。需清 `stalled/stallingLoadIdx` 或抑制 `replayMemInst`；当前不能证明单点抑制，标记 `NEEDS_HOOK/BLOCKED`。
- **六个工作负载**：已实际编写 C 源码、编译静态 aarch64 二进制，并在当前 gem5 上跑通无故障基线（exit 0，输出匹配 native checksum）。微架构目标事件触发仍未验证，不能标 READY。

