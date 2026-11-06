# LSU Trace Hook 设计 v3

## 1. 动态指令与故障身份
- DynamicInstSeqNum：DynInst::seqNum（fetch顺序，有squash空洞）。
- execution_attempt_id：同一指令不同执行尝试。
- replay_generation：0=首次，1..N=Replay代次。
- SampleRunID/FaultID/FaultModelID/InjectionEventID。

## 2. 传播关系
- EventID/ParentEventID；PropagationEdgeID/SourceEventID/DestinationEventID。
- ProducerInstSeqNum/ConsumerInstSeqNum。
- 支持一个Load从多个Store获取不同字节。

## 3. 访存关联
- request_id/response_id/fragment_id；VA/PA/ASID；LQEntryID/SQEntryID/entry_generation。
- commit_seq：全局提交顺序计数器，每条提交指令+1；与dyn_inst_seq不同。

## 4. 错误状态
OldValue/NewValue；InjectionStatus/ActivationStatus/CommitStatus/SquashStatus/TerminalState；TraceCompleteness独立。

## 5. Hook位置
- AGU：`lsq.cc:764-878` pushRequest（正式EA Hook）。
- LQ：`lsq_unit.cc:353-414,775-798,986-1020,1376-1727`。
- SQ：`lsq_unit.cc:416-438,1729-1756,811-835,1197-1255`。
- FWD：`lsq_unit.cc:1444-1686`；`CHAOSLSQFwd.cc:297-346`。
- MD：`lsq_unit.cc:550-636`；`mem_dep_unit.cc:192-612`。
- Replay：`lsq_unit.cc:1647-1684`；`iew.cc:563-573`；`inst_queue.cc:1323-1398`；`mem_dep_unit.cc:380-404`。
- Alignment：`lsq.cc:993-1060,1114-1149,1242-1266`。
- LP：`lsq_unit.cc:107-214,1135-1195`；`CHAOSL1DForward.cc:60-140`。
- SP：`lsq_unit.cc:847-977,1104-1133,1197-1255`。
- DTLB：`tlb.cc:155-176`（观察；SE不调用，标SE_DTLB_UNOBSERVABLE）。
- Cache：`mem/cache/base.cc`（观察）。
- Commit/Squash：`commit.cc:1291-1319`；`rob.cc:380`。

## 6. 完整性
TraceCompleteness=COMPLETE/INCOMPLETE/MISSING，与终态分开；INCOMPLETE不得判Masked；正常程序退出不等于无错误；无RAS/ECC证据时Detected-contained=NOT_IMPLEMENTED。


## v3.1 四维状态

- **RunStatus**：COMPLETED / NO_ELIGIBLE_EVENT / TIMEOUT / SIMULATOR_ERROR
- **FaultActivationStatus**：NOT_TRIGGERED / TRIGGERED / UNKNOWN
- **TerminalState**：MASKED / SQUASHED / DETECTED_CONTAINED / ARCH_STATE_CORRUPTION / SDC / CRASH / HANG
- **TraceCompleteness**：COMPLETE / INCOMPLETE

四者独立记录；Trace INCOMPLETE 不得判 MASKED；RunStatus=COMPLETED 不等于无错误。

