# R6-A2 阶段 1 — Lane C 只读诊断：A07-a/b/c 时序、A08-a/b 配对、37 个开放 seed 终局分类

- 诊断者：Lane C 只读 subagent；日期 2026-10-28
- 工作树 `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`，分支 `fix/r6-a-unit-20261028`，HEAD `defb3e0d`
- 二进制 `CHAOS/gem5/build/ARM/gem5.opt` 实测 `sha256=37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f`（与 STATUS 一致）
- 只读纪律：未改任何源码/配置/测试，未跑 gem5/scons/campaign/pytest，未在主检出目录做 git 操作；唯一写入 = 本文件。原始证据只读引用 `/home/sdc/gem5-fi-ding/runs/lsu/r6_a*_<RunID>_s<seed>/`。
- 上一轮权威材料已读并不重做：`R6-A-FINAL-REPORT.md`、`R6-A-STATUS.md/.json`、`R6-A-DIAG-C.md`（A07/A08 静态审计）。

---

## 0. 结论先行（全部有实证）

1. **A07-b 是"真延迟到有限周期并恢复"**，不是文字游戏。实证 `r6_a_segv2_A07-F0-W3_s2`：`ready_tick=10908590 → delayed_tick=10908975`（差 385 tick = 1 个 CPU cycle，`delay_cycles=1`），`resumed consumed=1, squashed=0`，随后 prop 流出现 `lq_read/resp/lq_complete/taint_reg/errant_commit/consumer`（L0→L5 全链，QUALIFIED）。保存位置、下游消费点见 §1.2。
2. **A07-a 的"旧 EA"在 O3 里确有真实载体，但不是"AGU 流水锁存器"**：`gem5` 的 EA 在 `DynInst::initiateAcc → LSQ::pushRequest` 内部现算，没有独立的 AGU 输出锁存。可证存在的旧值只有三个：`DynInst::effAddr`（`dyn_inst.hh:337` + `effAddrValid()` `:392-393`，上一次执行/重放留下的 EA）、`DynInst::physEffAddr`（`:340`，上一次翻译完成后的 PA）、以及 `DynInst::savedRequest` 里已构造的 `LSQRequest`（`lsq.cc:900-902` 重执行时直接复用，新的 `addr` 形参被**忽略**）。因此 A07-a 必须把"旧 EA 存在"做成**显式 eligibility**（`inst->effAddrValid()`），并在 `pushRequest` PRE 点用旧值覆盖新算的 EA —— 详见 §1.1，这是唯一能让下游 TLB/cache 真吃到旧 EA 的两点实现。
3. **"chain_end 冒充 containment"这道门禁已经存在且在真实样本上生效**：`tools/lsu_chain_check.py:76-87 _explicit_l5` 结构性排除生命周期 `chain_end`（`_LIFECYCLE_KINDS`, `:63`）。实证：A04/A05/A08/A07 的 store 样本在 `chain_end` 上写了 `outcome=detected_contained, detection_layer=L4, containment_reason=store_discarded_not_retired`（例 `r6_a_spanfix_A04-F0-W3_s1` 的 event_id=12），门禁仍判 `provable_to_L4_then_unknown`。**这是正确行为，不得改 chain_end 来"修好"这些 seed。**
4. **上一轮 36 个开放 seed 的真实终局只有 5 类**（逐条见 §3）：(a) L2 翻译 abort 且**已交付**为 guest SEGV → Crash（A01/A02/A03 共 15 个）；(b) L2 翻译 abort 但**从未交付**（无 resp、无 SEGV、oracle 干净）→ 错误未越过架构边界（A01-F0-W3 s2/s3、A02-F0-W3 s3）；(c) store 已写内存（`sq_writeback/resp/sq_complete`）但**未退休**，退出时 RAS 启发式判 squash/replay 含住（14 个，仅生命周期声明，无逐事件证据）；(d) store 写错址后**下游指针被污染**，后续访问未映射地址 `0x18/0x76` 触发 guest SEGV（4 个，缺跨请求 lineage）；(e) **oracle 校验和真的变了（SDC，A04-F0-W0 s2）但无 L5 事件**。另有 1 个 TRUNCATED（A08-F0-W5 s3）是**探针自身 SIGSEGV**，不是页错误（§3.37）。
5. **A08-a/A08-b 的可执行设计结论**：`Request` 在 PRE hook **之后**才构造（`lsq.cc:907-914`，翻译 `:933`）——这条既有结论成立。但存在两个真实"构造后、进内存前"的安全点，且**load 与 store 的窗口不对称**：
   - **load**：`pushRequest` 返回前就已 `initiateTranslation` 并在 `read()` 里 `buildPackets()+sendPacketToCache()`（`lsq.cc:933`、`lsq_unit.cc:1972-1973`）⇒ 构造后窗口只有 `lsq.cc:929-932`（几行），错通道只能在此翻转，且极易触发完成契约断言。
   - **store**：request 构造后长期驻留 SQ，真正建包在 `LSQUnit::writebackStores` 的 `request->buildPackets()`（`lsq_unit.cc:1036`）⇒ **store 侧有长窗口**，A08-b 的"把 store EA 换成配对 load 的 EA"可在此安全落地（`Request::setPaddr` 存在，`request.hh:608`），但受**同 4KiB 页**约束（paddr 已翻译，无请求级重翻译设施）。详见 §2。
6. **已发现并定位一个真实工具缺陷**（非模型语义）：`a08_subst` 对 64B 对齐 store 做同页替换会生成跨 64B cache line 的 `SplitDataRequest`，其响应路径在 `CHAOSPropagation::noteMemResponse` 的 `data_fnv` 计算中 SIGSEGV。`addr2line` 实证：`CHAOSPropagation.cc:288 (fnv1a64)` ← `lsq_unit.cc:250 (completeDataAccess)` ← `lsq.cc:1378 (SplitDataRequest::recvTimingResp)`。A08-F0-W5 s3 的 TRUNCATED 由此造成。详见 §3.37 与 §6.2。

---

## 1. A07-a/b/c 真实 ready 时序

### 1.1 生命周期与精确事件（file:line 全部实测）

| 阶段 | 真实位置 | 语义 |
|---|---|---|
| IQ 交付 ready 指令 | `CHAOS/gem5/src/cpu/o3/iew.cc:1154-1161`（`insts_to_execute = fromIssue->size`；`instQueue.getInstToExecute()`） | **`getInstToExecute()` 会把指令从 IQ 弹出**，这是 A07-c 挂死风险的根源 |
| squash 早退 | `iew.cc:1171-1187` | 已 squash 的指令置 executed/canCommit 后 continue，不执行 AGU |
| **ready 钩子** | `iew.cc:1194-1218`（`if (inst->isMemRef()) { … if (cpu->chaosAguReady && cpu->chaosAguReady->maybeDelayAguReady(inst)) continue; }`） | EA 尚不存在；返回 true 时本拍跳过常规执行 |
| 通道分派 | `iew.cc:1221-1282`（atomic→`executeStore`，load→`executeLoad`，store→`executeStore`） | 真正的 load/store 通道选择点 |
| AGU/EA 生成（真实点） | `lsq_unit.cc:725`（`inst->initiateAcc()`）→ `LSQ::pushRequest` `lsq.cc:772` | EA 在被调用的 arch 代码里算好后作为 `addr` 形参传入 |
| EA 锁存 | `lsq.cc:936-941`（`inst->effAddr = request->getVaddr(); inst->effSize = size; inst->effAddrValid(true)`）；PA 在 `lsq.cc:987`（`inst->physEffAddr = request->getPaddr()`，`SingleDataRequest::finish`） | **这就是 gem5 里"EA 锁存"的真实结构** |
| 请求构造 | `lsq.cc:907-914`（`new SplitDataRequest/SingleDataRequest`）；`inst->setRequest()` `:926`；`initiateTranslation()` `:933` | PRE hook（`:800`）之后才构造 |
| 翻译模式 | `lsq.cc:1314-1316`（`translateTiming(..., isLoad() ? BaseMmu::Read : Write)`） | 通道由 **`LSQRequest::isLoad()` 标志**（`lsq.hh:227 Flag::IsLoad`、`:301-305`）决定 |
| A07-b 注入器 | `CHAOSAddrPath.cc:883-982`（ready_tick=`curTick()` `:940`；`delayed_tick=clockEdge(Cycles(delay))` `:941-944`；单槽 `:945-948`；`schedule(aguResumeEvent, delayed_tick)` `:949`；`registerAguReadyFault` `:960-966`；日志 `:968-980`） | 时序移动，值不变 |
| resume | `CHAOSAddrPath.cc:994-1014` → `IEW::chaosAguResumeInst` `iew.cc:1412-1483` | 逐字镜像 executeInsts 的 memRef 分支；squash 分支 `:1415-1422` |
| A07 晚绑定（EA→链） | `CHAOSAddrPath.cc:484-494`（`maybeCorruptPre` 顶部：`dyn_inst_seq==agu_fault_seq` 时 `bindAguFaultAddr(addr,size)`） | 只做链绑定，不做值故障 |

### 1.2 A07-a：ready 过早 + 真实旧 EA（可执行设计）

**旧 EA 的真实保存位置（结论）**：
- `DynInst::effAddr`（`CHAOS/gem5/src/cpu/o3/dyn_inst.hh:337`），有效性 `effAddrValid()`（`:392-393`，写于 `lsq.cc:939-941`）。这是**唯一在 ready 点可读、且属于本指令的 EA 旧值**；只在"本指令已被执行过一次"时存在（重放/违例重执行/严格序 load 重调度）。注意 `LSQUnit::read` 的严格序路径会主动 `effAddrValid(false)`（`lsq_unit.cc:1617-1619`），所以必须在 ready 点**先读后判**，并记录该次失效。
- `DynInst::physEffAddr`（`dyn_inst.hh:340`，写于 `lsq.cc:987`）+ `memReqFlags`：上一次翻译完成后的 PA，可用于记录 old_pa。
- `DynInst::savedRequest`（`LSQRequest*`；`lsq.cc:900-902` 重执行时复用）：其中 `LSQRequest::_addr`（`lsq.hh:284`，**const**）与 `mainReq()->getVaddr()`（`lsq.hh:407-412`）保存着上一次请求的 VA。**重要陷阱**：这条路径下 `pushRequest` 的新 `addr` 形参对请求无效（请求不重建），所以在此情形下 A07-a 的"换 EA"会变成空操作 —— 必须显式拒绝并计数。
- `inst->reqToVerify`（`lsq.cc:944`，`Request` 拷贝）：第二个只读旁证，可用于交叉核对 old VA。

**两点实现（最小、可审计）**：
1. **观测点**：`CHAOSAddrPath::maybeDelayAguReady`（`CHAOSAddrPath.cc:883`，从 `iew.cc:1215` 调用）。新增 eligibility 门（在现有 op-class 过滤之后、trigger 之前，保持 F-049 语义）：
   - `inst->effAddrValid() == false` ⇒ 无旧 EA ⇒ `++obs_a07_no_stale_ea`，decline（**不消耗 trigger 的 once-ever 机会**）。
   - 否则 fire：`agu_stale_ea = inst->effAddr; agu_stale_pa = inst->physEffAddr; agu_stale_from_saved_req = (inst->savedRequest != nullptr)`，记录 `ready_tick=curTick()`、`dyn_inst_seq`、`lqIdx/sqIdx`；**本拍不跳过执行**（与 a07b 相反，A07-a 需要"当前 EA 也被真实算出"作为 old/current 对照）。
   - 新增日志 `Site: iew_memRef_AGU_ready_early, dyn_inst_seq=…, request_id=<seq>, stale_ea=0x…, stale_pa=0x…, stale_source=eff_addr|saved_request, ready_tick=…`。
2. **消费点**：`CHAOSAddrPath::maybeCorruptPre`（`CHAOSAddrPath.cc:462`，从 `lsq.cc:800` 在**请求构造 `:907-914` 与翻译 `:933` 之前**调用）。当 `dyn_inst_seq == agu_fault_seq`：
   - `current_ea = addr`（AGU 新算出的值）；若 `inst->translationStarted()`（不可区分时用 `agu_stale_from_saved_req` 标志）⇒ `++obs_a07_stale_unreachable`，返回不改（空操作不得计激活）。
   - 否则 `addr = agu_stale_ea`，随后照常 `bindAguFaultAddr(agu_fault_ptag, seq, addr, size)`（`:488-491`）——注意绑定的是**坏 EA** 的范围，链才自洽。
   - 日志 `Site: lsq_pushRequest_PRE, mode=a07a_ready_early, dyn_inst_seq=…, request_id=<seq>, old_ea=0x<current>, new_ea=0x<stale>, old_pa=…, stale_source=…, ready_tick=…, consume_tick=…`。
   - 下游"确实拿到旧 EA"的证据：随后 `lsq_push`（`lsq.cc:834-861`）的 `va`、`mem_req`/`lsq_sendfrag` 的 `va`（`lsq.cc:1275`）以及 `tlb_translate` 的 CPA 都等于 `stale_ea`；`resp` 的 `data_fnv` 来自旧地址的数据。这三条即"进入 TLB/cache 并被消费"的实证链。
- **记录字段**（要求项全覆盖）：`dyn_inst_seq`、`request_id`（= `Request::getReqInstSeqNum()`，见 §2.2 的身份说明）、`old_ea`(=current)、`current_ea`(同左)、`new_ea/stale_ea`、`old_pa/stale_pa`、`original_ready_tick`、`consume_tick`、`stale_source`、`downstream_consumed ∈ {1,0}`（在看门狗/退出回调中由 prop 流是否出现该 request 的 `resp` 决定，绝不猜）。
- **诚实边界**：`effAddr` 是"上一次执行的 EA"，不是"上一条指令的 EA 锁存器"；spec 若要的是跨指令 EA 流水锁存，则 gem5 中不存在该结构，必须新增（并会引入一条额外的数据通路），不得用 `effAddr` 冒充而不写明。这一条必须进 `runid_map` 的 `spec_landed` 说明。

### 1.3 A07-b：真延迟、真恢复、真消费（已成立，不需重做）

- 实证（`r6_a_segv2_A07-F0-W3_s2/…/seed2/addrpath_injections.log`）：
  `Tick: 10908590, Site: iew_memRef_AGU_ready, dyn_inst_seq=7499, ready_tick=10908590, delayed_tick=10908975, delay_cycles=1, isLoad=1`；
  `Tick: 10908975, Site: iew_memRef_AGU_ready_resume, dyn_inst_seq=7499, consumed=1, squashed=0`；
  `CHAOS_AGU_READY: … fault_seq=7499 addr_bound=1 activated=1`；prop 链 `lq_read→resp→lq_complete→taint_reg→errant_commit→consumer`（`errant_commit@t10911670`，L5）。
- 有限周期证明：`delayed_tick - ready_tick = 385 tick`，等于 1 个 CPU cycle（`clockEdge(Cycles(1))`，`CHAOSAddrPath.cc:941-944`），且 resume 事件必然被调度（`schedule(aguResumeEvent, delayed_tick)` `:949`），不存在无界等待。
- 下游消费证明：`addr_bound=1` 说明延迟后的指令走到 `pushRequest` 并完成晚绑定（`CHAOSAddrPath.cc:484-494`）；`activated=1` 只在 `resumeDeferredAgu` 真正重入执行时自增（`:1002-1004`）。
- 未覆盖：无（A07-b 语义 = 时序平移，构造上不可能 SDC；STATUS 预期 Masked 正确）。

### 1.4 A07-c：ready 丢失的有界 watchdog（可执行设计，禁止无界挂死）

**为什么必须注入器自己恢复**：ready 点之前 `instQueue.getInstToExecute()` 已把指令**弹出 IQ**（`iew.cc:1161`）；若"丢失 ready"后什么都不做，该指令既不在 IQ 也不会被执行，ROB 永不退休 ⇒ **确定性死锁**（不是概率挂死）。

**设计**：
1. 新增配置 `agu_ready_mode=a07c_ready_loss`、`agu_ready_watchdog_cycles`（默认 4096，硬上限 `agu_ready_watchdog_max=1<<20`，超上限在 config 解析期 `fatal`）。
2. fire 点仍为 `maybeDelayAguReady`（`CHAOSAddrPath.cc:883`）：**不调度 resume**，改调度新事件 `aguWatchdogEvent` 于 `curTick()+watchdog_cycles`；记录 `ready_tick`、`dyn_inst_seq`、`isLoad`、`wd_cycles`；`++faults_injected_count`；注册 inj 节点（`registerAguReadyFault` 复用，reason 增 `ready_loss`）。
3. 超时收口（唯一三条出口，全部发真实事件）：
   - **已被 squash**：`inst->isSquashed()` ⇒ 发 `ready_loss_squashed`（`detection_layer=L4, contained=1, outcome=contained, containment_reason=squash_before_ready, corr=seq_primary, dyn_inst_seq, request_id=<seq>, elapsed_cycles`），不发 resume（指令已被 commit 侧清理），链合法闭合（终局 (3)）。
   - **仍存活**：发 `ready_loss_watchdog`（`detection_layer=Hardware, contained=1, outcome=hang_recovered, containment_reason=watchdog_forced_resume, corr=seq_primary`），随后**强制** `o3cpu_resolved->o3IEW().chaosAguResumeInst(inst)`（`iew.cc:1412`，与 a07b 同一恢复通道，值正确）——这是唯一有界恢复路径；随后 `addr_bound/activated` 按 a07b 同口径记账。
   - **强制 resume 仍未执行**：若 `inst->isTranslationDelayed()`，`chaosAguResumeInst` 会 `instQueue.deferMemInst`（`iew.cc:1442-1446`），指令回到 IQ，不再需要 watchdog；若退出时该 seq 仍无 `lsq_push/resp`，退出回调打印 `CHAOS_AGU_WATCHDOG_UNRESOLVED: …` 且该样本必须分类为 **OPEN/HANG，不得 PASS**（`lsu_chain_check` 会因无 L5 真实事件自然拒绝，不需要新门禁）。
   - **硬边界**：`agu_ready_watchdog_hard_exit=true`（默认开）时，watchdog 若发现 `curTick()-ready_tick > agu_ready_watchdog_max`（例如事件被更深层死锁阻塞）则 `exitSimLoop("chaos_ready_watchdog", 124)`，保证仿真**有限时间必然结束**，且证据可收口（`stats.txt` 正常写出）。
4. 记录字段：`dyn_inst_seq/request_id/ready_tick/watchdog_tick/elapsed_cycles/drop_reason∈{squashed,forced_resume,hard_exit}/downstream_consumed`。
5. **必须同时修**：`CHAOS_AGU_READY` 汇总行（`CHAOSAddrPath.cc:1159-1169`）增加 `watchdogs/forced_resumes/unresolved`，否则新模型的收口无法在 stdout 自证。

---

## 2. A08-a/b：真实请求配对

### 2.1 同周期可见集合与通道选择点（file:line）

| 事项 | 真实位置 | 备注 |
|---|---|---|
| 本拍执行组 | `iew.cc:1154-1161`（`insts_to_execute = fromIssue->size`，逐条 `getInstToExecute()`） | "同周期"= 同一次 `executeInsts` 调用、同一 `curTick()`；没有预收集数组，**只能边弹边看** |
| 发射组大小来源 | `Issue` 的 `fromIssue` TimeBuffer（`iew.cc:1154`） | 即发射宽度 3/6/8（run.out 的 B0 params） |
| 通道分派 | `iew.cc:1221-1282` → `LSQ::executeLoad/executeStore`（`lsq.cc:287-299`） → `LSQUnit::executeLoad/executeStore`（`lsq_unit.cc:710/782`） | load/store 是**两个不同入口** |
| 队列选择 | `LSQUnit::insert`（`lsq_unit.cc:406-419`），`if (inst->isLoad()) insertLoad else insertStore` | 通道选择=队列选择 |
| 请求构造 | `lsq.cc:907-914`（Single/SplitDataRequest），`inst->setRequest()` `:926` | **PRE hook（`:800`）之后** |
| 翻译/进内存 | 翻译 `lsq.cc:933`；load 立即 `read()`→`buildPackets()+sendPacketToCache()`（`lsq_unit.cc:1969-1974`） | load 构造后窗口≈0 |
| store 建包/发送 | `LSQUnit::writebackStores`（`lsq_unit.cc:971`）→ `request->buildPackets()` `:1036` → `trySendPacket`/`dcachePort->sendTimingReq`（`lsq_unit.cc:1433-1444`） | **store 构造后有长窗口** |
| 包命令选择 | `LSQ::SingleDataRequest::buildPackets` `lsq.cc:1385-1415`（`isLoad()?Packet::createRead:createWrite`）；`SplitDataRequest::buildPackets` `lsq.cc:1417-1470` | 通道 = `LSQRequest::flags` 的 `IsLoad` 位（`lsq.hh:227,301-305`） |

### 2.2 请求身份字段（纠正上轮的一处表述）

- 线程内唯一：`DynInst::seqNum`（`lsq.cc:847`、`lsq_unit.cc:1581-1582`）、`DynInst::lqIdx/sqIdx`（`lsq.cc:853-856`；**对侧队列须写 -1**，池复用会留残留值，实证注释见 `lsq.cc:850-852`）、`isLoad`。
- 流里的 `request_id` **不是** gem5 的全局 Request id（`Request` 无此字段，`mem/request.hh` 只有 `_taskId`/`_contextId`）；它等于 `Request::getReqInstSeqNum()`（`request.hh:1014-1027`），取值来自 `lsq_unit.cc:1581-1582` 的 `h7_req`，缺省回退 `inst->seqNum`。**因此 request_id 与 dyn_inst_seq 同源，不能当"同一指令多次请求"的区分键**；要区分 split 分片必须另加字段（见 §4 的 `frag_idx/total`）。
- 与内存系统交互时的真实键：`pkt->req->getVaddr()/getPaddr()`、`pkt->getAddr()`、`Request::getFlags()`（读/写由 `isLoad` 决定翻译模式 `lsq.cc:1314-1316`）。

### 2.3 A08-a 错通道：最小安全点与契约风险

**可行的最小点（按语义忠实度排序）**：
1. **store 侧（推荐）**：`LSQUnit::writebackStores` 在 `request->buildPackets()`（`lsq_unit.cc:1036`）**之前**，把该请求的包命令从 `WriteReq` 改为 `ReadReq`（即"store 走了 load 端口"：写丢失、读回数据覆盖 `inst->memData`）。此时请求身份（seq/lqIdx/sqIdx/flags）与"类型矛盾"证据同时保留：`inst->isStore()==1`、`request->isLoad()==0`、`pkt->isWrite()==0`。日志字段：`Site: sq_writeback_channel_swap, dyn_inst_seq, request_id=<seq>, expected_channel=store, actual_channel=load, old_cmd=WriteReq, new_cmd=ReadReq, va, pa, pair_rule=none`。
   - 风险：响应是 `ReadResp`，store 的完成路径（`LSQUnit::recvTimingResp/completeDataAccess`、`SingleDataRequest::recvTimingResp` `lsq.cc:1360-1378`）会把 store 当 load 处理（`wb_to_reg=false` 走 store taint 分支，`CHAOSPropagation.cc:2370-2395`），功能上表现为"store 未生效"；若 `recvTimingResp` 内部对 `pkt->isRead()` 有断言，需先加显式豁免。**这是一条需要在实现前用 `--debug-flags=LSQUnit,LSQ` 单 seed 试跑验证的风险**（本轮禁止运行）。
2. **load 侧（不建议作为正式格）**：`load` 的包在 `read()` 内立即发送（`lsq_unit.cc:1972-1973`），唯一窗口是 `lsq.cc:929-932`（`setRequest/taskId/getFault=NoFault` 之后、`initiateTranslation()` 之前）。把 `IsLoad` 清掉会让翻译走 `BaseMMU::Write`（`lsq.cc:1314-1316`）、`buildPackets` 建 `WriteReq`、完成路径拿不到读数据：`LoadCompleteAcc` 的 `pkt->getRaw<T>()` 依赖包的 `STATIC_DATA|DYNAMIC_DATA` 与 `size`（`mem/packet_access.hh:47-56`），`WriteResp` 包无数据 ⇒ 要么断言（`sizeof(T) <= size` / 数据标志），要么零值。**与 A06 load-shrink 同类结论：A08-a load 侧大概率只能产出 Crash/断言，不能形成"被下游合法消费"的激活事件。**
3. **禁止的做法**：只改地址（那是 A04-b/A08_subst 的语义，不是通道）；直接改 `inst->isLoad()`（会破坏 IQ/ROB/commit 与 LSQ 队列索引一致性，必崩）。

### 2.4 A08-b 同周期 EA 互换：两点实现 + 4KiB 页约束

**真实配对定义（严格、不拼接）**：
- 同一 `IEW::executeInsts` 调用（`iew.cc:1154-1161`）、同一 `curTick()`、组内**恰好一条 load + 一条 store**，且两条的 `executeLoad/executeStore` 都真实发生（各产生 `lq_read` 或 `sq_execute`，见 `lsq_unit.cc:1561-1590` / `:800-838`）。
- **顺序约束**：store 必须**先于** load 在同组执行（store→load，正是 W5 `sq_forward` 的形态），这样 load 执行时 store 的 EA 已在 SQ 实例里（`LSQUnit::insert` 已建 entry `lsq_unit.cc:437-440`，store 的 `sq_execute`/`request()->getVaddr()` 可取）。若同组是 load 先 store 后，**当前流水线无法在不延迟第一条的前提下知道第二条的 EA** —— 必须走"一拍延迟"（复用 `instQueue.deferMemInst`，`iew.cc:1439-1446`，与 A07-b 同类的时序副作用），本轮应显式登记为 `pair_order=store_after_load → DEFER_REQUIRED`，不得硬拼。
- **页约束（关键、架构性）**：store 侧地址替换发生在翻译之后（`sq_writeback` 建包），`Request` 的 paddr 已由 `SingleDataRequest::finish` 写入（`lsq.cc:987`）。`Request::setPaddr` 可写（`request.hh:608`），但没有请求级重翻译设施（`markAsStaleTranslation` 只是 TLB flush 标记，`lsq.cc:1318-1355` + `lsq_unit.cc:1480-1505`，不是换址重译）。因此 **只有当两条 EA 落在同一 4KiB 页时**，paddr 才能按页内偏移直接改；否则 PA 会指向旧页 ⇒ 必须拒绝并计数 `obs_a08_cross_page_declined`。

**两点实现**：
1. **load 侧（可信、任意页都可）**：`CHAOSAddrPath::maybeCorruptPre`（`lsq.cc:800` 调用）在请求构造前把 `addr` 换成配对 store 的 EA（`storeEntry.request()->getVaddr()`），随后正常翻译（`lsq.cc:933`）⇒ load 的 TLB/cache 访问就是 store 的地址，身份与类型不变（`field=load` 但 `va=store_ea`，这就是"类型/地址矛盾"的可证证据）。记录 `pair_tick, load_seq, load_request_id, load_old_ea, load_new_ea=store_ea, store_seq, store_old_ea`。
2. **store 侧（受页约束）**：`LSQUnit::writebackStores` 在 `request->buildPackets()`（`lsq_unit.cc:1036`）之前调用新钩子：若该 store 是配对成员且 `(load_old_ea >> 12) == (store_old_ea >> 12)`，则 `request->mainReq()->setPaddr(pa_of(load_old_ea))` 并把 VA 记录为 `load_old_ea`（`SingleDataRequest::_addr` 是 const，paddr 是唯一可改点；cache 查找用 `pkt->getAddr()`，来自 req 的 paddr）。记录 `store_new_ea=load_old_ea, store_old_ea, store_old_pa, store_new_pa`。
   - 若不同页：不换（只做 load 侧）并记 `swap_partial=1, reason=cross_page`；**不得**只改 vaddr 不改 paddr。
- **记录字段**：`pair_tick, pair_order, load{seq,request_id,old_ea,new_ea}, store{seq,request_id,old_ea,new_ea,old_pa,new_pa}, page_ok, decline_reason`；两条的 `field` 仍是 load/store，`old/new channel` 仍是 load/store（通道未变，交换的是 EA —— 这正是与 A08-a 的区别，必须自描述）。
- **禁止**：跨周期配对、把不相邻的两条访存拼成一对、把 A04-b 的"同页代理"包装成 A08-b（现有 `a08_subst` 即此代理，`CHAOSAddrPath.cc:615-625`，与 spec 的"两条请求互换"不等价）。

### 2.5 "Request 在 PRE hook 之后构造"结论的评估（回答要求项）

- 结论**成立**且更精确：`Request` 在 `lsq.cc:907-914` 构造，PRE hook 在 `:800`；`initiateTranslation` 在 `:933`，load 的包在同一调用栈内发送（`lsq_unit.cc:1972-1973`）。所以：
  - 存在"构造后、进入内存系统前"的安全点 = **`lsq.cc:929-932`**（load，极窄，共 4 行）与 **`lsq_unit.cc:1036` 之前**（store，宽，SQ 驻留期）。
  - 不存在"构造后重定向并重翻译"的安全设施：`Request` 已翻译、`LSQRequest::_addr` 为 const、stale-translation 只服务 TLB flush。**最小未来方案**：给 `LSQRequest` 增加 `retarget(Addr va, Addr pa, unsigned size)`（重置 `_state`、`TranslationStarted` 位，重跑 `initiateTranslation`，同步 `_addr`），或在 `LSQ::pushRequest` 构造点引入"两槽 stash + 延后一拍翻译"；两者都会改变发射时序，须作为模型的一部分显式记账（类似 A07-b 的 `delay_cycles`）。

---

## 3. 逐 seed 真实终局表（36 个开放 seed + 1 个 TRUNCATED）

字段约定：`last event` = 该 seed prop 流中**最后一个非 chain_end 真实事件**；`terminal` = `chain_report.json` 的 terminal；`真实终局` = 本 Lane 依据证据的判定；`缺证据` = 无法进一步证明时缺的那条事件。所有目录均在 `/home/sdc/gem5-fi-ding/runs/lsu/` 下。

> 共同事实：A01/A02/A03 是 **sendFragment 位翻转/stuck（POST 钩子，`CHAOSAddrPath.cc` A01/A02/A03 分支）**，A04/A05/A08 是 **pushRequest PRE 同页/移位代理**，A07 是 **AGU ready 延迟**。A04/A05/A08/A07 的 store 样本都在 stdout 打 `CHAOS_DETECT: layer=Hardware RAS contained=1 … reason=store_discarded_not_retired`，但该结论**只写进 lifecycle chain_end**（`CHAOSPropagation.cc:161-170` 设 `containment_ptags`，`:193-229` 写 chain_end），流里**没有检测事件**，故门禁（`lsu_chain_check.py:76-87,479-504`）正确地不接受。

### 3.1 A01 / A02 / A03（翻译阻断族，7 事件链）

| # | RunID s | 目录 | last event | terminal | 真实终局 | gem5 hook | 缺证据 |
|---|---|---|---|---|---|---|---|
| 1 | A01-F0-W3 s1 | `r6_a_segv_A01-F0-W3_s1` | tlb_fault eid6 t=15513575 sn=12793 req=12793 va=0x8493018 Generic/Hardware | crash_translation_blocked | **L2 翻译异常已交付 = guest SEGV → Crash**（err: `chaos: injected address 0x8493018 faulted (guest SEGV)`；stats 256400） | `faults.cc:98-123`（`GenericPageTableFault::invoke`；`:112-117` exitSimLoop） | 无（只需把 arch exception 发成事件，§4-E1） |
| 2 | A01-F0-W3 s2 | `r6_a_spanfix_A01-F0-W3_s2` | tlb_fault eid6 t=16700530 sn=15561 va=0x7ffffe7be0 (ldp_uop) | provable_to_L2_then_unknown | **L2 异常但从未交付**：无 SEGV、无 resp、checksum `728e604ffcec539d`=golden ⇒ 错误未越过架构边界；是否 squash **UNKNOWN** | `faults.cc:98-123`（未进入 chaos 分支）；squash 点在 `LSQUnit::squash` `lsq_unit.cc:1132-1244` | 缺"该 load 被 squash"事件（§4-E3） |
| 3 | A01-F0-W3 s3 | `r6_a_spanfix_A01-F0-W3_s3` | tlb_fault eid6 t=9859080 sn=6702 va=0x7ffefeec40 | provable_to_L2_then_unknown | 同 #2 | 同上 | 同上 |
| 4 | A01-F0-W9 s1 | `r6_a_segv2_A01-F0-W9_s1` | tlb_fault eid6 t=226968665 sn=891313 va=0x849b1a8 | crash_translation_blocked | **已交付 guest SEGV → Crash**（err 实证） | `faults.cc:112-117` | 无 |
| 5 | A01-F0-W9 s3 | `r6_a_segv2_A01-F0-W9_s3` | tlb_fault eid6 t=287088725 sn=1142335 va=0x14951e8 | crash_translation_blocked | 同 #4 | 同上 | 无 |
| 6 | A01-F2-W9 s1 | `r6_a_segv2_A01-F2-W9_s1` | tlb_fault eid6 t=152693310 sn=581132 va=0x8494dc8 | crash_translation_blocked | 同 #4 | 同上 | 无 |
| 7 | A01-F2-W9 s3 | `r6_a_segv2_A01-F2-W9_s3` | tlb_fault eid6 t=189120855 sn=733266 va=0x1495d40 | crash_translation_blocked | 同 #4 | 同上 | 无 |
| 8 | A02-F0-W3 s2 | `r6_a_segv2_A02-F0-W3_s2` | tlb_fault eid6 t=16700530 sn=15561 va=0x7fdffe7be0 | crash_translation_blocked | **已交付 guest SEGV → Crash** | 同上 | 无 |
| 9 | A02-F0-W3 s3 | `r6_a_spanfix_A02-F0-W3_s3` | tlb_fault eid6 t=9859080 sn=6702 va=0x7ffdfeed40 | provable_to_L2_then_unknown | **未交付**（无 SEGV，checksum=golden）⇒ 未越过架构边界；squash UNKNOWN | 同 #2 | 同 #2 |
| 10 | A02-F0-W9 s2 | `r6_a_segv2_A02-F0-W9_s2` | tlb_fault eid6 t=146775090 sn=556456 va=0x2049e088 | crash_translation_blocked | 已交付 SEGV → Crash | 同上 | 无 |
| 11 | A02-F0-W9 s3 | `r6_a_segv2_A02-F0-W9_s3` | tlb_fault eid6 t=287088725 sn=1142335 va=0x24950e8 | crash_translation_blocked | 已交付 SEGV → Crash | 同上 | 无 |
| 12 | A02-F2-W9 s2 | `r6_a_segv2_A02-F2-W9_s2` | tlb_fault eid6 t=145271665 sn=550123 va=0x20495320 | crash_translation_blocked | 已交付 SEGV → Crash | 同上 | 无 |
| 13 | A02-F2-W9 s3 | `r6_a_segv2_A02-F2-W9_s3` | tlb_fault eid6 t=189120855 sn=733266 va=0x2495c40 | crash_translation_blocked | 已交付 SEGV → Crash | 同上 | 无 |
| 14 | A03-F5-W3 s1 | `r6_a_segv2_A03-F5-W3_s1` | tlb_fault eid6 t=80080 sn=5 va=0x5ffffefdd0 (store) | crash_translation_blocked | 已交付 SEGV → Crash（stats 201114，早停） | 同上 | 无 |
| 15 | A03-F5-W3 s2 | `r6_a_segv2_A03-F5-W3_s2` | 两故障：sn=33 va=0x148ed78（tlb_fault eid6 + sq_execute eid7）、sn=47 va=0x14980f0（eid14/15）；最后 `sq_execute eid15 t=198660` | crash_translation_blocked | **两个 store 均 L2 异常并交付 guest SEGV（0x148ed78）→ Crash**；`sq_execute` 是同一 store 的真实执行（fault 在 commit 交付） | `lsq_unit.cc:782-838`（executeStore）+ `faults.cc:112-117` | 无（多故障选择按 escape-first `lsu_chain_check.py:596-641`，本样本无逃逸） |
| 16 | A03-F5-W10 s1 | `r6_a_fix2_A03-F5-W10_s1` | tlb_fault eid6 t=80080 sn=5 va=0x5ffffefdd0 | crash_translation_blocked | 同 #14 | 同上 | 无 |
| 17 | A03-F5-W10 s2 | `r6_a_fix2_A03-F5-W10_s2` | 同 #15（0x148ed78 / 0x14980f0） | crash_translation_blocked | 同 #15 | 同上 | 无 |

### 3.2 A04 / A05 / A08（PRE 同页/移位代理，store 12 事件链）

共同链形：`inj → addr_form → lsq_push(store) → mem_req(req=seq) → lsq_sendfrag(store) → tlb_translate → sq_execute → sq_writeback(pa) → resp → taint_reg → sq_complete → chain_end(detected_contained/L4/store_discarded_not_retired)`。
共同最后真实事件 = `sq_complete`（除非另注）。`sq_execute` 在 `lsq_unit.cc:798`，`sq_writeback` 建包在 `:1036`，`resp/taint_reg/sq_complete` 在 `:1288+/completeStore`。

| # | RunID s | 目录 | last event (t / sn / va) | terminal | 真实终局 | 缺证据 |
|---|---|---|---|---|---|---|
| 18 | A04-F0-W3 s1 | `r6_a_spanfix_A04-F0-W3_s1` | 277200 / 41 / 0x7ffffef250（store `strxi_uop`，old 0x7ffffefd90） | provable_to_L4_then_unknown | **store 已写内存且完成，但从未退休**；golden checksum ⇒ 错误未影响架构输出；RAS 判 squash+同 PC 重放含住（启发式，非逐事件） | 逐事件 squash/retire（§4-E3/E4） |
| 19 | A04-F0-W3 s2 | `r6_a_segv2_A04-F0-W3_s2` | 11158840 / 8069 / 0x7ffffefa80 | provable_to_L4_then_unknown | **下游污染型 Crash**：err `chaos: downstream-unmapped address 0x18 faulted (guest SEGV)`；stats 252845 ⇒ 错误经内存副作用传到后续访存，真逃逸但**无 lineage** | 跨请求 lineage 事件（§4-E5） |
| 20 | A04-F0-W3 s3 | `r6_a_spanfix_A04-F0-W3_s3` | 209440 / 29 / 0x7ffffef6a0 | provable_to_L4_then_unknown | 同 #18（golden） | 同 #18 |
| 21 | A04-F0-W0 s1 | `r6_a_segv2_A04-F0-W0_s1` | 2817430 / 1794 / 0x490250 | provable_to_L4_then_unknown | **下游污染型 Crash**：err `downstream-unmapped address 0x76` | §4-E5 |
| 22 | A04-F0-W0 s2 | `r6_a_segv2_A04-F0-W0_s2` | 15117025 / 12039 / 0x491a80（pa=0x76a80），checksum `a852a0ab10d91b17` | provable_to_L4_then_unknown | **SDC 逃逸**：golden(W0=mini_check)=`07568da9f3ad5665`，实测不同 ⇒ 错误值到达程序输出；但无 L5 事件 | oracle-diff L5 join（§4-E6） |
| 23 | A04-F0-W0 s3 | `r6_a_segv2_A04-F0-W0_s3` | 18069590 / 18857 / 0x7ffffef6a0，checksum=`07568da9f3ad5665` | provable_to_L4_then_unknown | 同 #18（golden ⇒ Masked） | 同 #18 |
| 24 | A05-F0-W3 s1 | `r6_a_spanfix_A05-F0-W3_s1` | 277200 / 41 / 0x7ffffefd21（A05 低字节旋转） | provable_to_L4_then_unknown | 同 #18（golden） | 同 #18 |
| 25 | A05-F0-W3 s2 | `r6_a_segv2_A05-F0-W3_s2` | 11103785 / 8069 / 0x7ffffefc41 | provable_to_L4_then_unknown | **下游污染型 Crash**（0x18） | §4-E5 |
| 26 | A05-F0-W3 s3 | `r6_a_segv2_A05-F0-W3_s3` | 209440 / 29 / 0x7ffffefd1a | provable_to_L4_then_unknown | 同 #18（golden） | 同 #18 |
| 27 | A08-F0-W3 s1 | `r6_a_spanfix_A08-F0-W3_s1` | 277200 / 41 / 0x7ffffef250（a08_subst 同页代理） | provable_to_L4_then_unknown | 同 #18（golden） | 同 #18 |
| 28 | A08-F0-W3 s2 | `r6_a_segv2_A08-F0-W3_s2` | 11158840 / 8069 / 0x7ffffefa80 | provable_to_L4_then_unknown | **下游污染型 Crash**（0x18） | §4-E5 |
| 29 | A08-F0-W3 s3 | `r6_a_segv2_A08-F0-W3_s3` | 209440 / 29 / 0x7ffffef6a0 | provable_to_L4_then_unknown | 同 #18（golden） | 同 #18 |
| 30 | A08-F0-W5 s1 | `r6_a_fix2_A08-F0-W5_s1` | 18754120 / 15384 / 0x496250 | provable_to_L4_then_unknown | 同 #18（W5 golden `1f4cbf14327717df`） | 同 #18 |
| 31 | A08-F0-W5 s2 | `r6_a_fix2_A08-F0-W5_s2` | 10569790 / 7281 / 0x7ffffefa80 | provable_to_L4_then_unknown | 同 #18（golden） | 同 #18 |
| 32 | A08-F0-W5 s3 | `r6_a_fix2_A08-F0-W5_s3` | `sq_writeback` t=9670430（流被截断） | provable_to_L3_then_unknown, truncated=true | **宿主机 SIGSEGV（探针缺陷）**：注入 `a08_subst 0x497d00→0x4976a0, size=64, store`（0x6a0 mod 64=0x20 ⇒ 跨行 ⇒ SplitDataRequest）；崩溃栈 `fnv1a64`(`CHAOSPropagation.cc:288`) ← `completeDataAccess`(`lsq_unit.cc:250`) ← `SplitDataRequest::recvTimingResp`(`lsq.cc:1378`)；stats 0B；`.done` 记 `exit_code=0` 与崩溃矛盾 | 根因 UNKNOWN（需 debug build/addr2line 带行号或 gdb）；最小修见 §6.2 |

### 3.3 A07（ready 延迟族）

| # | RunID s | 目录 | last event (t / sn) | terminal | 真实终局 | 缺证据 |
|---|---|---|---|---|---|---|
| 33 | A07-F0-W3 s1 | `r6_a_spanfix_A07-F0-W3_s1` | sq_complete 15461216 / 12413（store） | provable_to_L4_then_unknown | 同 #18：store 完成未退休，RAS 判含住；golden | §4-E3/E4 |
| 34 | A07-F0-W3 s3 | `r6_a_segv2_A07-F0-W3_s3` | sq_execute 541695 / 286（store）**无 sq_writeback** | provable_to_L3_then_unknown | **store 在执行后、写回前被 squash**（未建包、未写内存）⇒ 真含住；golden | `LSQUnit::squash` 中的逐事件 squash 事件（§4-E3） |
| 35 | A07-F0-W5 s1 | `r6_a_spanfix_A07-F0-W5_s1` | sq_complete 4832520 / 3200（store） | provable_to_L4_then_unknown | 同 #33 | §4-E3/E4 |
| 36 | A07-F0-W5 s3 | `r6_a_segv2_A07-F0-W5_s3` | sq_complete 14988435 / 11963（store） | provable_to_L4_then_unknown | 同 #33 | §4-E3/E4 |

> 对照（已合格，不入开放表）：`r6_a_segv2_A07-F0-W5_s2` 是 load 路径，链含真实 `squash_masked`（`CHAOSPropagation.cc:2314-2334`，`detection_layer=L4, contained=1, reason=squash_replay`）⇒ `detected_contained` 被门禁接受。**这证明"有真实检测事件才准入"不是空话，也证明修法只能是"发事件"，不是改 chain_end。**

### 3.4 统计（本 Lane 的独立计数）

| 真实终局 | seed 数 | 明细 |
|---|---|---|
| L2 翻译异常 + 交付为 guest SEGV（Crash） | 15 | 表 3.1 除 #2/#3/#9 |
| L2 翻译异常 + 未交付（错误未越界） | 3 | #2 A01-F0-W3 s2、#3 s3、#9 A02-F0-W3 s3 |
| store 未退休（squash/replay 含住，仅启发式） | 13 | #18/#20/#23/#24/#26/#27/#29/#30/#31/#33/#35/#36 + #34（另一种：写回前 squash） |
| 下游污染 → guest SEGV（缺 lineage） | 4 | #19/#21/#25/#28 |
| SDC 逃逸（无 L5 事件） | 1 | #22 |
| 探针崩溃 + 证据截断（无效样本） | 1 | #32 |

（15+3+13+4+1+1 = 37，与本轮开放 seed 数一致。）

---

## 4. 需要补发的真实检测/containment 事件清单（设计）

原则：**新事件必须是"非生命周期 kind + 真实 detection_layer + 非空 outcome + 链关联 corr"**，并挂在同一 parent DAG 上；`chain_end` 一律不改语义。

| ID | 事件 kind | 发射位置（file:line） | 必带字段 | corr | 可闭合的终局 | 备注 |
|---|---|---|---|---|---|---|
| E1 | `arch_translation_fault` | `CHAOS/gem5/src/sim/faults.cc:112-118`（`GenericPageTableFault::invoke`，chaos guest SEGV 分支） | `fault_id/ptag`、`dyn_inst_seq`、`request_id`、`va`、`exc_type=page_table`、`delivered=1`、`outcome=arch_exception`、`detection_layer=Hardware`、`contained=0`、`trigger_source∈{injected,downstream_unmapped}` | `seq_primary`（injected）/`none`（downstream） | #1/#4-#8/#10-#17（Crash 收口，终局 (1) 的"架构异常"分支需裁决） | 需在 `FaultBase::invoke` 能拿到 `tc`/`inst` → `inst->seqNum`；`GenericPageTableFault` 已持有 `vaddr` |
| E2 | `translation_fault_undelivered` | `LSQUnit::squash`（`lsq_unit.cc:1132-1244`）里对被 squash 且 `savedRequest->isPartialFault()/translationCompleted()==true && !executed` 的条目发射（或 commit 侧 squash 统一发射） | `dyn_inst_seq/request_id/va/fault=GenericPageTableFault/outcome=undelivered/detection_layer=none/contained=1/containment_reason=squash_before_delivery` | `seq_primary` | #2/#3/#9 | 若取不到 ptag，按 `addr_registry` 的 `dyn_seq` 反查 |
| E3 | `squash_discarded`（通用） | `LSQUnit::squash` `lsq_unit.cc:1132-1244`（load 分支 `:1139-1171`，store 分支 `:1215-1244`） | `seq, lq_idx/sq_idx, field=load/store, state_before∈{issued,executed,writeback}, outcome=contained, detection_layer=L4, contained=1, containment_reason=squash_before_{writeback,completion}, request_id` | `seq_primary` | #34（写回前 squash）、A07-c 的 squash 出口 | 这是最干净的"显式含住"证据；所有 store 样本都应有 |
| E4 | `store_not_retired` | `CHAOSPropagation.cc:161-170`（退出回调，store_taint 残留处）——**改为发真实事件**（不是 chain_end） | `ptag, dyn_inst_seq(store), sq_idx, outcome=contained, detection_layer=L4, contained=1, containment_reason=store_discarded_not_retired, last_state=sq_complete/squash, replay_pc_present∈{0,1}` | `taint_prop`（`store_taint` 成员关系） | #18/#20/#23/#24/#26/#27/#29/#30/#31/#33/#35/#36 | 必须先验证 `same-PC replay` 真实发生（可从 commit 流按 PC 统计），否则不得声称 replay；缺该证据时 `containment_reason=store_taint_unerased_unknown` |
| E5 | `downstream_fault`（lineage 桥） | `faults.cc:112-118` 的 `downstream_unmapped` 分支 | `va, access_pc(若可得), outcome=arch_exception, detection_layer=Hardware, contained=0, original_fault_id=<哪个 ptag 的地址范围污染了该数据>` | `taint_prop` 或 `none` | #19/#21/#25/#28 | **关键限制**：当前无内存数据流污染追踪，`original_fault_id` 多数情况下不可证 ⇒ 必须允许 `lineage=unknown` 且**不得**据此闭合链（诚实记为 Crash + 未证 lineage） |
| E6 | `oracle_diff` | runner 侧（`tools/lsu_campaign.py` 分类阶段，非 C++；或 `CHAOSPropagation` 退出回调接收 oracle 结果） | `ptag, dyn_inst_seq, outcome=sdc, detection_layer=Application, contained=0, oracle_before=golden, oracle_after=observed, join=offline` | `taint_prop`（只有能证明单一 fault 的样本） | #22（SDC） | **不得**在链上伪造 L5：只有 `corr` 能落到该 fault 时才准入；多故障样本只能作为样本级终局（escape-first 已有规则） |
| E7 | `ready_loss_watchdog` / `ready_loss_squashed` | `CHAOSAddrPath.cc` 新 watchdog 事件（`~:983` 之后） | §1.4 字段 | `seq_primary` | A07-c 新模型 | — |
| E8 | `channel_swap` / `paired_ea_swap` | A08-a：`lsq_unit.cc:1036` 之前；A08-b：`lsq.cc:929-932`（load）+ `lsq_unit.cc:1036` 之前（store） | §2.3/§2.4 字段（含 `frag_idx/total` 以区分 split 分片） | `seq_primary` | A08-a/b 新模型 | 事件必须同时带 `expected_channel/actual_channel`（A08-a）或 `load{old,new}/store{old,new}`（A08-b） |

**禁止项（工作令）已逐条落实**：
- 不改 `chain_end` 为 L5：`_LIFECYCLE_KINDS`/`_explicit_l5` 保持（`lsu_chain_check.py:63,76-87`）。
- 通用 chain_end 不冒充 containment：E4 要求"发独立事件"，不是把 `chain_end` 的 `contained=1` 挪个位置。
- 新事件一律要 `corr ∈ {seq_primary, addr_fallback, origin, taint_prop}`（`lsu_chain_check.py:65-67`），`corr=none` 的事件不得准入。

---

## 5. 组合负向测试设计（断言方向）

测试风格沿用现有脚本式 `check(说明, 条件, 证据)`（`tests/test_lsu_chain_check.py`）。建议新增单文件 `tests/test_lsu_r6a2_gate_negatives.py`，并在既有文件补 2 条。

| # | 场景 | 测试位置 | 断言方向（必须真实构造 PROP-EVT 文本，不得 mock 门禁） |
|---|---|---|---|
| N1 | **truncated 不能通过** | `tests/test_lsu_campaign_truncation.py` + 新文件 | 构造 `prop_evt.txt.gz` 在 `chain_end` 之前被截断（EOFError）+ `stats.txt` 0B ⇒ `detect_evidence_truncation` 返回 `(True, reasons)` 且 reasons 含 "incomplete gzip stream" 与 "stats.txt empty"；`write_chain_report` 的 `truncated=True`；`chain.containment_from_events(events, truncated=True)` 返回 `None`（`lsu_chain_check.py:1196-1197`）；`check_admission` 抛 `containment_on_truncated_stream` 而非准入。**并断言** 用 A08-F0-W5 s3 的真实残片（898B gz、11 事件、末 `sq_writeback`）复现该判定；**同时断言 `.done` 的 `exit_code=0` 不得被当作通过依据**（新增一条响亮检查：`exit_code==0` 且 `truncated==True` ⇒ 必须 `admitted=False`） |
| N2 | **open chain 不能通过** | `tests/test_lsu_chain_check.py`（新 section） | 用表 3.2 任一真实链（`sq_complete` 收尾、`provable_to_L4_then_unknown`）⇒ `check_admission` 的 `admitted is False` 且 violations 含 `no_closed_chain_and_no_containment`；`select_representative_fault` 不得因 `oracle=SDC` 提升 rank（`_TERMINAL_RANK` 只认 full/detected_contained） |
| N3 | **chain_end 不能当 L5** | 既有 `test_lsu_chain_check.py:337-361,455-467,518` 已有；新增"contained=1 的 chain_end"用例 | 用 `r6_a_spanfix_A04-F0-W3_s1` 的真实 chain_end 行（`detection_layer=L4 contained=1 outcome=detected_contained`）⇒ `_explicit_l5==False`、terminal 仍 `provable_to_L4_then_unknown`、`ready_by_chain_end_only` 出现。**回归锁**：`CC._LIFECYCLE_KINDS == {"chain_end"}`（已有 `:121-122`） |
| N4 | **未知终局不能通过** | `tests/test_lsu_chain_check.py` + `tests/test_lsu_ready_contract_gate.py` | 无 `resp/errant_commit/squash_masked` 的链（如 A01-F0-W3 s2 的 7 事件）⇒ `beyond=="Unknown"`、`admitted=False`；`ready_contract._runid_chain`（`lsu_ready_contract.py:286-341`）对"缺失证据"返回 `admitted=False` + `evaluated==0`（而非 None/True） |
| N5 | **新增 containment 不会绕过既有门禁** | 新文件（三组联合断言） | (a) 给 E3/E4 事件但 **`corr=none`** ⇒ 仍不准入（`_explicit_l5` 拒）；(b) 给 E3 事件但 **不在同一祖先路径**（`parent_event_id` 指向别的 fault）⇒ `_event_has_prefix` 拒 ⇒ 不准入；(c) 给 E3 但 `containment_layer=L4` 且同时存在 `errant_commit` 逃逸 ⇒ `errant_escape_outranks_containment`（`lsu_chain_check.py:1205-1210`）→ 不准入；(d) 给 E4 但 `detection_layer` 空/`outcome=run_end` ⇒ 拒；(e) **truncated + E3** ⇒ `containment_on_truncated_stream` |
| N6 | **A07-c watchdog 不得无界** | 新 `tests/test_lsu_hook_a07.py` 扩展 | 断言配置解析：`agu_ready_watchdog_cycles>=1`、`<=agu_ready_watchdog_max`，越界 `fatal`；断言退出回调在"watchdog 未收口"时打印 `CHAOS_AGU_WATCHDOG_UNRESOLVED` 且该样本 `admitted=False`；断言 `actual_channel/expected_channel`（A08-a）与 `pair_tick`（A08-b）字段在日志行中存在（字符串契约测试，防"只改地址"冒充） |
| N7 | **A08-b 禁跨周期/跨页** | 新同上 | 断言：`pair_tick` 不等 ⇒ 事件必须带 `decline_reason=cross_cycle`，且流里**不得**出现两条请求的 new_ea 互换；跨 4KiB 页 ⇒ `cross_page`，store 侧 `pa` 不变；split 请求 ⇒ 每分片带 `frag_idx/total` |

---

## 6. 文件所有权建议与风险清单

### 6.1 建议 owner 划分（按共享面，必须串行）

| 文件 | 归属 | 改动内容 | 冲突面 |
|---|---|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc,py}` | **Owner-1（A07/A08 唯一 owner）** | A07-a 两点实现（stale EA + watchdog 事件）、A07-c、A08-a/b 钩子与字段；`a08_subst` 的跨行保护 | A04/A05/A06/S13/S04/L01 共用 ⇒ 一次只允许一个模型改动；必须与 §4 的事件 tx 同 commit |
| `CHAOS/gem5/src/cpu/o3/iew.cc` / `iew.hh` | **Owner-2（O3 共享）** | 如需在 `executeInsts` 顶部登记 pair_tick（A08-b），只加只读观测，不改执行路径 | 全 O3 家族；任何改动需全家族回归 |
| `CHAOS/gem5/src/cpu/o3/lsq.cc` / `lsq.hh` | **Owner-3（LSU 共享）** | `pushRequest` 的 A08-b load 侧钩子（`:929-932`）、`buildPackets` 的 A08-a store 侧点；新增 `LSQRequest::retarget` 时同文件 | 所有 LSU 模型；高风险串行 |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | **Owner-3** | store 写回点（`:1036` 之前）、`squash()`（`:1132-1244`）发 E3 | 同上 |
| `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}` | **Owner-4（证据层）** | E4 真实事件化、`noteMemResponse` 的 split 保护（§6.2）、`faults.cc` 事件对接 API | 与 Sheet9 事件词表（`tools/lsu_prop_fields.py`）联动 |
| `CHAOS/gem5/src/sim/faults.cc` | **Owner-4** | E1/E5 发射（需要 ptag 反查接口） | SE 全局；`chaos::` 侧只读接口 |
| `tools/lsu_chain_check.py` | **Owner-5（门禁）** | 注册新 kind 的层级（`_TLB_KIND_LAYER`/`KIND_LAYER`）、负向测试配套（**只收紧，不放松**） | 325 行共享门禁 |
| `tools/lsu_prop_fields.py` | **Owner-5** | 新 kind → L4/L5 映射、`CORR` 白名单 | 同上 |
| `tools/lsu_campaign.py` / `tools/lsu_runid_map.py` / `.py` 配置面 | **Owner-6（编排）** | `--agu_ready_mode a07a/a07c`、`--agu_pair_mode`、A08-a/b 路由；`ADDRPATH_F0_SPAN` 增加 A08 census（若采用）；interval-reachability 门禁（A07-F4/A08-F2 的静默零） | 编排层；须与 manifest schema 枚举同步 |

### 6.2 风险清单（按严重度）

1. **P0 — 证据层 SIGSEGV（已复现）**：`a08_subst` 64B 跨行替换 → SplitDataRequest → `noteMemResponse` 的 `data_fnv` 在 `fnv1a64`（`CHAOSPropagation.cc:288`）崩溃，样本 0B、证据截断，且 `.done` 记 `exit_code=0`（**假通过风险**）。最小修：(a) `d = ... data_fnv` 仅在 `pkt->isRead() && pkt->hasData()` 且 `pkt->getPtr` 非空时计算；(b) `a08_subst` 保持原访问的行内偏移（`cand = (addr & ~0x3F) | (rnd & 0x3C)`），从根本上不新增跨行；(c) `.done`/`.exit_code` 必须反映真实退出（`exit_code` 由 gem5 返回码写入，`128+SIGSEGV` 不得写 0）。
2. **P0 — A07-c 无界挂死**：若只"丢 ready"不设 watchdog，因 IQ 已弹出（`iew.cc:1161`）必然死锁。§1.4 的三出口 + 硬上限是强制项；任何"丢 ready"实现缺 watchdog 都不得合入。
3. **P1 — A07-a 的旧 EA 语义偏差**：`DynInst::effAddr` 是"本指令上一次执行的值"，不是"上一条指令的 AGU 锁存值"。必须以 `spec_landed` 明写；若裁决要求跨指令锁存，需要新增一条数据通路（不在本轮范围）。
4. **P1 — A08-a 的断言/契约风险**：load 侧错通道几乎必定踩完成契约（`packet_access.hh:47-56`）；store 侧改 `WriteReq→ReadReq` 需先确认 `recvTimingResp`/`completeDataAccess` 对 `ReadResp` 的容忍度。建议 A08-a 只做 store 侧，并把它登记为"可能只产出 Crash/断言"的高风险模型，单独裁决。
5. **P1 — A08-b 的页约束与顺序约束**：store 侧只能在同 4KiB 页内换 PA（无重翻译设施）；同组 load→store 顺序需要一拍延迟（会改变时序，必须记 `delay_cycles` 并像 A07-b 一样显式声明）。跨页/跨周期一律 decline 并计数，禁止硬拼。
6. **P1 — 下游 lineage 不可证**：`downstream-unmapped`（0x18/0x76）样本是**真逃逸**，但当前无内存污染追踪，`original_fault_id` 不可证；E5 必须允许 `lineage=unknown` 且不得据此闭合链，否则会制造"伪闭链"。若需要闭合，最小未来方案 = 给 store 的写地址范围建"污染页表"，后续 fault 落在该范围才允许 `addr_fallback` 关联（有误报风险，需裁决）。
7. **P2 — request_id 语义**：`request_id` = `Request::getReqInstSeqNum()`（= dyn seq），不是唯一请求 id；split 请求的多分片会**共用**该值。A08 事件若要区分分片，必须新增 `frag_idx/total`，否则"配对/通道矛盾"证据会串片。
8. **P2 — 静默零/静默偏置（上轮遗留）**：A07-F4 / A08-F2 结构性不可达仍无 `addrpath` 版 interval-reachability 门禁；A08-F0 的 span 仍建议补 census（本轮新增 `(A08,sq_forward)` 已有；`(A08,agu_addrmodes)` 仍未实测）。这些不改结论，但会让 formal 把"不可达"读成"0 次激活"。
9. **P2 — 并发/共享文件**：`lsq.cc`/`lsq_unit.cc`/`iew.cc` 是全部 LSU 家族共享，任何改动必须单 owner 串行 + 全家族回归（至少 T 单元一个 unaffected 样本 `exit: pass`、零 SIGSEGV）。
10. **P3 — 文档口径**：`coverage_matrix` 的 PASS 是节点级并集，不等于子模型落地；本轮所有 A07-a/c、A08-a/b 结论必须写进 `runid_map` 的 `spec_landed`/`impl_status`，避免再次"字符串存在冒充动态覆盖"。

---

## 附：本轮只读核验的关键命令/输出（摘录，均可复现）

```
$ sha256sum CHAOS/gem5/build/ARM/gem5.opt
37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f

$ addr2line -f -C -e CHAOS/gem5/build/ARM/gem5.opt 0x11b2ad8 0x110fa50 0x10f8b8c
gem5::CHAOSPropagation::fnv1a64(void const*, unsigned long) const
  …/CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:288 (discriminator 3)
gem5::o3::LSQUnit::completeDataAccess(gem5::Packet*)
  …/CHAOS/gem5/src/cpu/o3/lsq_unit.cc:250
gem5::o3::LSQ::SplitDataRequest::recvTimingResp(gem5::Packet*)
  …/CHAOS/gem5/src/cpu/o3/lsq.cc:1378

$ grep iew_memRef_AGU_ready runs/lsu/r6_a_segv2_A07-F0-W3_s2/A07-F0-W3/seed2/addrpath_injections.log
Tick: 10908590, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=7499,
  ready_tick=10908590, delayed_tick=10908975, delay_cycles=1, isLoad=1, isStore=0
Tick: 10908975, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay,
  dyn_inst_seq=7499, consumed=1, squashed=0

$ zcat runs/lsu/r6_a_spanfix_A04-F0-W3_s1/A04-F0-W3/seed1/prop_evt.txt.gz | grep chain_end
… kind=chain_end … detection_layer=L4 contained=1 outcome=detected_contained
  … containment_reason=store_discarded_not_retired …
# 而 chain_report 的 terminal 仍是 provable_to_L4_then_unknown（门禁正确拒绝）

$ zcat runs/lsu/r6_a_segv2_A07-F0-W5_s2/A07-F0-W5/seed2/prop_evt.txt.gz | grep squash_masked
… kind=squash_masked … detection_layer=L4 contained=1 outcome=masked
  … containment_reason=squash_replay
# 有真实检测事件 ⇒ terminal=detected_contained（QUALIFIED）
```

*（本文件是本 Lane 唯一写入；未触碰任何源码/配置/测试/证据。）*
