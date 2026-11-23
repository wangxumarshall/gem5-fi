# 0202c 观测埋点规格 (observation-only instrumentation spec)

Round 0202c · `gem5-fi-mmu-when5x3` · 2026-11-17/18
全部埋点为纯观测：不修改冻结 Where/Context/Timing，不改变任何故障注入语义。
原始 Fault Injection 逻辑与新增观测埋点完全分离。

## 新增事件类型

| 事件 kind | 触发条件 | 关联 ID | 含义 |
|---|---|---|---|
| `ifu_response` | `Fetch::processCacheCompletion` 收到属于错误取指行(fetchBufferTxnId!=0)的 icache 响应 | `translation_id`(取指事务), `va`, `pa` | 真实 IFU 响应（与合成 Execute `lsu_request` 区分） |
| `ifu_decode` | `Fetch::buildInst` 从错误取指行构建 DynInst | `translation_id` + 真实 `dyn_inst_seq` + `pc` | IFU 消费/译码：错误字节解码为动态指令 |
| `masked_reason` (字段) | `mmu_fault_summary` 输出 | — | 显式掩盖机制分类 |

`ifu_response`/`ifu_decode` 之后由既有 `mmuNoteCommit`/`mmuNoteSquash` 自动
fault-tag 取指指令的 `commit`/`squash`（因 `mmuRegisterFetchSeq` 把真实
DynInst seq 绑定到取指事务并插入 `mmu_traced_seqs`）。

## 关联 ID 生成与传播

1. **Execute-fetch translation_id（合成）**: `mmuNewSyntheticSeq(va)` 在
   `mmu.cc::getTE` 对 `!req->hasInstSeqNum() && mode==Execute` 铸造成
   `2^63 | counter` 命名空间 id；经 `mmuBeginTxn` 成为 `mmu_txn[tid]`。
2. **Request 对象身份桥**: `mmuNoteLsuRequest` 对 is_fetch 用真实
   `Request*` 登记 `mmu_req_txn[req.get()]=tid`（对象身份，非 VA/tick）。
3. **fetch 流水线传播**: `Fetch::finishTranslation` → `mmuTakeFetchTxn(mem_req)`
   → `fetchBufferTxnId[tid]` → `buildInst` → `mmuRegisterFetchSeq(tid, seq, pc)`
   → `mmu_seq_txn[seq]=tid` + `mmu_traced_seqs.insert(seq)`。
4. **M05 暖命中消费者**: `mmuNoteEntryInsert` 对 M05 把每个 fault-tagged
   完整 entry insert 登记 `mmuRegisterEntryFault(...,"M05")`；
   `tlb.cc::lookup` 暖命中 poisoned entry 时 `mmuEntryFaultPtag` 命中 →
   `mmuBeginConsumerTranslation(seq, va, ..., fault_ptag)` 建消费事务，
   受 `MMU_CONSUMER_REUSE_CAP=16` 界。

## 与原始 Fault Injection 的分离

- 原始注入点（M01–M08 的 `mmuFaultActivate` / `maybeCorrupt*` /
  `checkPermissions64` grant 反转等）**完全未改动**。
- 新增代码只在 `mmuTraceEnabled()` 时发射事件或登记关联 ID；trace off 时
  全部为 no-op，二进制行为与故障语义不变。
- 8 个 Control 复现冻结 N（M04 N=20005、M07-C02 N=6、其余 N=3）即为
  Where/When 语义冻结一致性证据。
